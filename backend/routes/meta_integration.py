"""
Meta / Facebook Integration Routes

Handles:
- OAuth connect flow (start, callback, page listing, connect/disconnect)
- Webhook verification (GET) and event reception (POST)
- Integration status per tenant

Routes prefix: /api/integrations/meta
"""

import os
import uuid
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

from models import UserInDB
from core.auth_deps import get_current_active_user
from services.meta_service import (
    META_VERIFY_TOKEN,
    encrypt_token,
    decrypt_token,
    get_oauth_url,
    exchange_code_for_token,
    get_user_pages,
    subscribe_page_to_webhook,
    unsubscribe_page_from_webhook,
    verify_webhook_signature,
    log_audit_event,
)

# ── Standalone DB connection ──────────────────────────────────────────────────
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "signguy_ai")
_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations/meta", tags=["Meta Integration"])


# ── Pydantic models ───────────────────────────────────────────────────────────
class ConnectPageRequest(BaseModel):
    page_id: str
    page_name: str
    page_access_token: str
    category: Optional[str] = None
    ai_enabled: bool = True
    create_mode: str = "lead"  # lead | draft_order | message_only


class UpdatePageSettingsRequest(BaseModel):
    ai_enabled: Optional[bool] = None
    create_mode: Optional[str] = None
    default_assignee_id: Optional[str] = None
    min_confidence_threshold: Optional[float] = None


# ── Status endpoint ───────────────────────────────────────────────────────────
@router.get("/status")
async def get_meta_status(current_user: UserInDB = Depends(get_current_active_user)):
    """Return all connected Meta Pages for the current tenant."""
    pages = await db.meta_integrations.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0, "page_access_token_encrypted": 0},
    ).to_list(50)

    app_id = os.environ.get("META_APP_ID", "")
    configured = bool(app_id and os.environ.get("META_APP_SECRET"))

    return {
        "configured": configured,
        "app_configured": configured,
        "pages": pages,
        "total_connected": len([p for p in pages if p.get("status") == "active"]),
    }


# ── OAuth start ───────────────────────────────────────────────────────────────
@router.post("/connect/start")
async def start_oauth(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Generate the Meta OAuth authorization URL and return it to the frontend."""
    if not os.environ.get("META_APP_ID") or not os.environ.get("META_APP_SECRET"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Meta App is not configured. Add META_APP_ID and META_APP_SECRET "
                "to your .env file and restart the server."
            ),
        )

    # State encodes tenant_id and user_id for validation in the callback
    state = f"{current_user.tenant_id}:{current_user.id}:{uuid.uuid4().hex}"

    # Store state temporarily so callback can verify it
    await db.meta_oauth_states.insert_one(
        {
            "state": state,
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    # Build redirect URI — same origin as the backend API
    origin = str(request.base_url).rstrip("/")
    redirect_uri = f"{origin}/api/integrations/meta/oauth/callback"

    return {
        "auth_url": get_oauth_url(redirect_uri=redirect_uri, state=state),
        "state": state,
    }


# ── OAuth callback ────────────────────────────────────────────────────────────
@router.get("/oauth/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None),
):
    """Handle the OAuth redirect from Meta and exchange code for a user token.

    Returns a redirect to the frontend integrations page with a result param.
    """
    from fastapi.responses import RedirectResponse

    frontend_origin = os.environ.get("REACT_APP_FRONTEND_URL", "")
    # Fallback: strip /api from base URL
    if not frontend_origin:
        # We'll resolve at runtime from the stored state
        frontend_origin = ""

    if error:
        logger.warning(f"Meta OAuth error: {error} — {error_description}")
        return RedirectResponse(
            url=f"{frontend_origin}/settings/meta-integration?error={error}&error_desc={error_description or ''}"
        )

    # Validate state
    state_doc = await db.meta_oauth_states.find_one_and_delete({"state": state})
    if not state_doc:
        return RedirectResponse(
            url=f"{frontend_origin}/settings/meta-integration?error=invalid_state"
        )

    tenant_id = state_doc["tenant_id"]
    user_id = state_doc["user_id"]

    # Build same redirect URI used in start_oauth
    # We reconstruct from the stored state since this is a GET redirect
    # The request.base_url approach fails for GET redirects; use env fallback
    api_base = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
    redirect_uri = f"{api_base}/api/integrations/meta/oauth/callback"

    try:
        token_data = await exchange_code_for_token(code=code, redirect_uri=redirect_uri)
        user_access_token = token_data.get("access_token")
        if not user_access_token:
            raise ValueError("No access_token in response")
    except Exception as exc:
        logger.error(f"Meta token exchange failed: {exc}")
        await log_audit_event(
            tenant_id=tenant_id,
            event_type="oauth_token_exchange_failed",
            details={"error": str(exc)},
            user_id=user_id,
        )
        return RedirectResponse(
            url=f"{frontend_origin}/settings/meta-integration?error=token_exchange_failed"
        )

    # Temporarily store the user token so the frontend can fetch pages
    temp_id = uuid.uuid4().hex
    await db.meta_oauth_tokens.insert_one(
        {
            "id": temp_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "user_access_token_encrypted": encrypt_token(user_access_token),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    await log_audit_event(
        tenant_id=tenant_id,
        event_type="oauth_completed",
        details={"temp_id": temp_id},
        user_id=user_id,
    )

    return RedirectResponse(
        url=f"{frontend_origin}/settings/meta-integration?oauth_success=1&tmp={temp_id}"
    )


# ── List available pages after OAuth ─────────────────────────────────────────
@router.get("/pages")
async def list_available_pages(
    tmp: str = Query(..., description="Temp token ID from OAuth callback"),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return the Facebook Pages this user manages using the OAuth user token."""
    token_doc = await db.meta_oauth_tokens.find_one(
        {"id": tmp, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not token_doc:
        raise HTTPException(status_code=404, detail="OAuth session expired. Please reconnect.")

    try:
        user_token = decrypt_token(token_doc["user_access_token_encrypted"])
        pages = await get_user_pages(user_token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to fetch pages: {exc}")

    # Remove raw tokens from response — never expose them to frontend
    safe_pages = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "category": p.get("category"),
            "fan_count": p.get("fan_count"),
            "access_token": p.get("access_token"),  # Temporarily included so connect can use it
        }
        for p in pages
    ]
    return {"pages": safe_pages, "tmp": tmp}


# ── Connect a page ────────────────────────────────────────────────────────────
@router.post("/pages/connect")
async def connect_page(
    body: ConnectPageRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Store a Page connection for the current tenant."""
    # Check for duplicate
    existing = await db.meta_integrations.find_one(
        {"tenant_id": current_user.tenant_id, "page_id": body.page_id},
        {"_id": 0, "id": 1, "status": 1},
    )

    encrypted_token = encrypt_token(body.page_access_token)
    now_iso = datetime.now(timezone.utc).isoformat()

    # Subscribe the page to our webhook
    webhook_subscribed = False
    try:
        webhook_subscribed = await subscribe_page_to_webhook(
            body.page_id, body.page_access_token
        )
    except Exception as exc:
        logger.warning(f"Webhook subscription failed for page {body.page_id}: {exc}")

    if existing:
        # Re-activating an existing connection
        await db.meta_integrations.update_one(
            {"tenant_id": current_user.tenant_id, "page_id": body.page_id},
            {
                "$set": {
                    "page_name": body.page_name,
                    "page_access_token_encrypted": encrypted_token,
                    "status": "active",
                    "ai_enabled": body.ai_enabled,
                    "create_mode": body.create_mode,
                    "webhook_subscribed": webhook_subscribed,
                    "updated_at": now_iso,
                    "disconnected_at": None,
                }
            },
        )
        integration_id = existing["id"]
    else:
        integration_id = str(uuid.uuid4())
        await db.meta_integrations.insert_one(
            {
                "id": integration_id,
                "tenant_id": current_user.tenant_id,
                "connected_by_user_id": current_user.id,
                "provider": "facebook",
                "page_id": body.page_id,
                "page_name": body.page_name,
                "category": body.category,
                "page_access_token_encrypted": encrypted_token,
                "token_expires_at": None,
                "status": "active",
                "ai_enabled": body.ai_enabled,
                "create_mode": body.create_mode,
                "default_assignee_id": None,
                "min_confidence_threshold": 0.65,
                "webhook_subscribed": webhook_subscribed,
                "last_webhook_at": None,
                "message_count": 0,
                "created_at": now_iso,
                "updated_at": now_iso,
                "disconnected_at": None,
            }
        )

    await log_audit_event(
        tenant_id=current_user.tenant_id,
        event_type="page_connected",
        details={
            "page_id": body.page_id,
            "page_name": body.page_name,
            "webhook_subscribed": webhook_subscribed,
        },
        user_id=current_user.id,
        page_id=body.page_id,
    )

    return {
        "message": f"Page '{body.page_name}' connected successfully",
        "integration_id": integration_id,
        "webhook_subscribed": webhook_subscribed,
    }


# ── Disconnect a page ─────────────────────────────────────────────────────────
@router.delete("/pages/{page_id}")
async def disconnect_page(
    page_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Disconnect a Facebook Page for the current tenant."""
    integration = await db.meta_integrations.find_one(
        {"tenant_id": current_user.tenant_id, "page_id": page_id},
        {"_id": 0},
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Page integration not found")

    # Try to unsubscribe from webhook
    try:
        token = decrypt_token(integration["page_access_token_encrypted"])
        await unsubscribe_page_from_webhook(page_id, token)
    except Exception as exc:
        logger.warning(f"Could not unsubscribe page {page_id} from webhook: {exc}")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.meta_integrations.update_one(
        {"tenant_id": current_user.tenant_id, "page_id": page_id},
        {"$set": {"status": "disconnected", "disconnected_at": now_iso, "updated_at": now_iso}},
    )

    await log_audit_event(
        tenant_id=current_user.tenant_id,
        event_type="page_disconnected",
        details={"page_id": page_id},
        user_id=current_user.id,
        page_id=page_id,
    )

    return {"message": "Page disconnected successfully"}


# ── Update page settings ──────────────────────────────────────────────────────
@router.patch("/pages/{page_id}/settings")
async def update_page_settings(
    page_id: str,
    body: UpdatePageSettingsRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Update AI settings for a connected Page."""
    integration = await db.meta_integrations.find_one(
        {"tenant_id": current_user.tenant_id, "page_id": page_id},
        {"_id": 0, "id": 1},
    )
    if not integration:
        raise HTTPException(status_code=404, detail="Page integration not found")

    update = {k: v for k, v in body.model_dump().items() if v is not None}
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.meta_integrations.update_one(
        {"tenant_id": current_user.tenant_id, "page_id": page_id},
        {"$set": update},
    )
    return {"message": "Settings updated"}


# ── Webhook verification (GET) ────────────────────────────────────────────────
@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Meta webhook verification challenge.

    Meta sends a GET with hub.mode='subscribe', hub.verify_token, and
    hub.challenge. We must return hub.challenge if the token matches.
    """
    if hub_mode == "subscribe" and hub_verify_token == META_VERIFY_TOKEN:
        logger.info("Meta webhook verified successfully")
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Webhook verification failed")


# ── Webhook event receiver (POST) ─────────────────────────────────────────────
@router.post("/webhook")
async def receive_webhook(request: Request):
    """Receive and process incoming Meta Messenger webhook events.

    Responds 200 immediately (Meta retries on non-200). Heavy processing
    runs as a background task.
    """
    from fastapi.responses import JSONResponse
    from fastapi import BackgroundTasks

    # Validate signature
    body_bytes = await request.body()
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    if not verify_webhook_signature(body_bytes, sig_header):
        logger.warning("Meta webhook signature validation failed")
        return JSONResponse(content={"status": "invalid_signature"}, status_code=200)

    try:
        payload = json.loads(body_bytes)
    except json.JSONDecodeError:
        logger.warning("Meta webhook received invalid JSON")
        return JSONResponse(content={"status": "bad_payload"}, status_code=200)

    # Process asynchronously so we return 200 instantly
    asyncio.create_task(_process_webhook_payload(payload))
    return JSONResponse(content={"status": "ok"}, status_code=200)


async def _process_webhook_payload(payload: Dict[str, Any]) -> None:
    """Background task: route each messaging event to the correct tenant."""
    if payload.get("object") != "page":
        return

    for entry in payload.get("entry", []):
        page_id = entry.get("id")
        if not page_id:
            continue

        # Resolve tenant by Page ID (cross-tenant safe — each page_id is unique)
        integration = await db.meta_integrations.find_one(
            {"page_id": page_id, "status": "active"},
            {"_id": 0, "tenant_id": 1, "id": 1, "ai_enabled": 1, "create_mode": 1, "min_confidence_threshold": 1},
        )
        if not integration:
            logger.debug(f"No active integration found for page_id={page_id}")
            continue

        tenant_id = integration["tenant_id"]
        await db.meta_integrations.update_one(
            {"page_id": page_id},
            {"$set": {"last_webhook_at": datetime.now(timezone.utc).isoformat()}},
        )

        for messaging in entry.get("messaging", []):
            await _handle_messaging_event(
                messaging=messaging,
                page_id=page_id,
                tenant_id=tenant_id,
                integration=integration,
                raw_entry=entry,
            )

        await log_audit_event(
            tenant_id=tenant_id,
            event_type="webhook_received",
            details={"page_id": page_id, "entry_count": len(payload.get("entry", []))},
            page_id=page_id,
        )


async def _handle_messaging_event(
    messaging: Dict,
    page_id: str,
    tenant_id: str,
    integration: Dict,
    raw_entry: Dict,
) -> None:
    """Store a single messaging event and queue it for AI processing."""
    msg_data = messaging.get("message", {})
    message_id = msg_data.get("mid") or messaging.get("delivery", {}).get("mids", [None])[0]

    # Ignore delivery receipts, reads, echo messages
    if not msg_data or msg_data.get("is_echo"):
        return
    if not message_id:
        return

    # Idempotency — skip if we already stored this message
    existing = await db.facebook_messages.find_one(
        {"message_id": message_id, "tenant_id": tenant_id},
        {"_id": 0, "id": 1},
    )
    if existing:
        return

    sender_id = (messaging.get("sender") or {}).get("id")
    recipient_id = (messaging.get("recipient") or {}).get("id")
    message_text = msg_data.get("text", "")
    attachments = msg_data.get("attachments", [])
    timestamp_ms = messaging.get("timestamp", 0)
    received_at = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat() if timestamp_ms else datetime.now(timezone.utc).isoformat()

    doc_id = str(uuid.uuid4())
    doc = {
        "id": doc_id,
        "tenant_id": tenant_id,
        "page_id": page_id,
        "sender_id": sender_id,
        "recipient_id": recipient_id,
        "message_id": message_id,
        "thread_id": sender_id,  # In Messenger, thread = sender PSID
        "message_text": message_text,
        "attachments": [
            {"type": a.get("type"), "url": a.get("payload", {}).get("url")}
            for a in attachments
        ],
        "raw_payload": messaging,
        "received_at": received_at,
        "processing_status": "pending",
        "classification": None,
        "confidence_score": None,
        "extracted_fields": None,
        "missing_information": [],
        "suggested_reply": None,
        "linked_lead_id": None,
        "linked_order_id": None,
        "review_status": "new",
        "urgency": "low",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.facebook_messages.insert_one(doc)
    await db.meta_integrations.update_one(
        {"page_id": page_id},
        {"$inc": {"message_count": 1}},
    )

    # Trigger AI processing if enabled
    if integration.get("ai_enabled") and message_text:
        asyncio.create_task(
            _process_message_ai(
                doc_id=doc_id,
                tenant_id=tenant_id,
                message_text=message_text,
                has_attachments=bool(attachments),
                integration=integration,
            )
        )


async def _process_message_ai(
    doc_id: str,
    tenant_id: str,
    message_text: str,
    has_attachments: bool,
    integration: Dict,
) -> None:
    """Run AI classification + extraction and update the message document."""
    from services.facebook_ai import classify_message, extract_order_details

    try:
        classification_result = await classify_message(message_text)
        classification = classification_result.get("classification", "unknown")
        confidence = float(classification_result.get("confidence", 0.0))
        urgency = classification_result.get("urgency", "low")
        suggested_reply = classification_result.get("suggested_reply", "")
        missing_info = classification_result.get("missing_info", [])

        extracted = None
        should_create = classification_result.get("should_create_draft", False)
        if should_create:
            extracted = await extract_order_details(message_text)
            if extracted:
                extracted["attachment_present"] = has_attachments

        min_conf = float(integration.get("min_confidence_threshold", 0.65))
        create_mode = integration.get("create_mode", "lead")

        now_iso = datetime.now(timezone.utc).isoformat()
        await db.facebook_messages.update_one(
            {"id": doc_id},
            {
                "$set": {
                    "classification": classification,
                    "confidence_score": confidence,
                    "urgency": urgency,
                    "suggested_reply": suggested_reply,
                    "missing_information": missing_info,
                    "extracted_fields": extracted,
                    "processing_status": "processed",
                    "processed_at": now_iso,
                    "updated_at": now_iso,
                }
            },
        )

        await log_audit_event(
            tenant_id=tenant_id,
            event_type="ai_processed",
            details={
                "message_id": doc_id,
                "classification": classification,
                "confidence": confidence,
            },
        )

        # Auto-create draft if confidence is high enough and tenant settings allow
        if should_create and confidence >= min_conf and create_mode in ("lead", "draft_order"):
            await _auto_create_draft(
                doc_id=doc_id,
                tenant_id=tenant_id,
                create_mode=create_mode,
                classification_result=classification_result,
                extracted=extracted,
                integration=integration,
            )

    except Exception as exc:
        logger.error(f"AI processing failed for message {doc_id}: {exc}")
        await db.facebook_messages.update_one(
            {"id": doc_id},
            {"$set": {"processing_status": "failed", "updated_at": datetime.now(timezone.utc).isoformat()}},
        )


async def _auto_create_draft(
    doc_id: str,
    tenant_id: str,
    create_mode: str,
    classification_result: Dict,
    extracted: Optional[Dict],
    integration: Dict,
) -> None:
    """Automatically create a draft lead or draft order from AI extraction."""
    message_doc = await db.facebook_messages.find_one({"id": doc_id}, {"_id": 0})
    if not message_doc:
        return

    customer_name = (extracted or {}).get("customer_name") or f"Facebook Lead ({message_doc.get('sender_id', 'unknown')})"
    product_type = (extracted or {}).get("product_type") or "Unknown"
    notes_parts = [
        "Source: Facebook Messenger",
        f"Page ID: {message_doc.get('page_id')}",
        f"Sender ID: {message_doc.get('sender_id')}",
        f"Original Message:\n{message_doc.get('message_text', '')}",
        f"\nAI Classification: {classification_result.get('classification')} (confidence: {classification_result.get('confidence', 0):.0%})",
        f"Suggested Action: {classification_result.get('suggested_action', '')}",
    ]
    if extracted and extracted.get("missing_information"):
        notes_parts.append(f"Missing Info: {', '.join(extracted['missing_information'])}")

    notes = "\n".join(notes_parts)
    now_iso = datetime.now(timezone.utc).isoformat()
    draft_id = str(uuid.uuid4())

    if create_mode == "lead":
        lead_doc = {
            "id": draft_id,
            "tenant_id": tenant_id,
            "name": customer_name,
            "source": "Facebook Messenger",
            "status": "Facebook Lead - New",
            "review_status": "Needs Review",
            "product_interest": product_type,
            "notes": notes,
            "facebook_message_id": doc_id,
            "facebook_sender_id": message_doc.get("sender_id"),
            "facebook_page_id": message_doc.get("page_id"),
            "ai_confidence": classification_result.get("confidence"),
            "ai_classification": classification_result.get("classification"),
            "extracted_fields": extracted,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        await db.leads.insert_one(lead_doc)
        await db.facebook_messages.update_one(
            {"id": doc_id},
            {"$set": {"linked_lead_id": draft_id, "review_status": "draft_created", "updated_at": now_iso}},
        )
        await log_audit_event(
            tenant_id=tenant_id,
            event_type="draft_lead_created",
            details={"lead_id": draft_id, "message_id": doc_id},
            page_id=message_doc.get("page_id"),
        )
    elif create_mode == "draft_order":
        order_doc = {
            "id": draft_id,
            "tenant_id": tenant_id,
            "customer_name": customer_name,
            "source": "Facebook Messenger",
            "status": "draft",
            "review_status": "Needs Review",
            "product_type": product_type,
            "notes": notes,
            "facebook_message_id": doc_id,
            "facebook_sender_id": message_doc.get("sender_id"),
            "facebook_page_id": message_doc.get("page_id"),
            "ai_confidence": classification_result.get("confidence"),
            "ai_classification": classification_result.get("classification"),
            "extracted_fields": extracted,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        await db.orders.insert_one(order_doc)
        await db.facebook_messages.update_one(
            {"id": doc_id},
            {"$set": {"linked_order_id": draft_id, "review_status": "draft_created", "updated_at": now_iso}},
        )
        await log_audit_event(
            tenant_id=tenant_id,
            event_type="draft_order_created",
            details={"order_id": draft_id, "message_id": doc_id},
            page_id=message_doc.get("page_id"),
        )
