"""
Facebook Messages Routes

Staff-facing API for reviewing, processing, and acting on incoming Facebook
Messenger messages that have been received through the Meta webhook.

Routes prefix: /api/facebook
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient

from models import UserInDB
from core.auth_deps import get_current_active_user
from services.meta_service import log_audit_event

# ── Standalone DB connection ──────────────────────────────────────────────────
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "signguy_ai")
_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/facebook", tags=["Facebook Messages"])


# ── Pydantic models ───────────────────────────────────────────────────────────
class CreateLeadRequest(BaseModel):
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    product_interest: Optional[str] = None


class CreateDraftOrderRequest(BaseModel):
    customer_name: Optional[str] = None
    notes: Optional[str] = None
    product_type: Optional[str] = None


class MarkReviewedRequest(BaseModel):
    staff_notes: Optional[str] = None
    action_taken: Optional[str] = None


# ── List messages ─────────────────────────────────────────────────────────────
@router.get("/messages")
async def list_messages(
    status: Optional[str] = Query(None, description="Filter by review_status"),
    classification: Optional[str] = Query(None),
    page_id: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    skip: int = Query(0),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return paginated Facebook messages for the current tenant."""
    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id}
    if status:
        query["review_status"] = status
    if classification:
        query["classification"] = classification
    if page_id:
        query["page_id"] = page_id

    messages = await db.facebook_messages.find(
        query,
        {"_id": 0, "raw_payload": 0},
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    total = await db.facebook_messages.count_documents(query)

    return {
        "messages": messages,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ── Get single message ────────────────────────────────────────────────────────
@router.get("/messages/{message_id}")
async def get_message(
    message_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return full message detail (excluding raw payload) for one message."""
    msg = await db.facebook_messages.find_one(
        {"id": message_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "raw_payload": 0},
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return msg


# ── Manually trigger AI processing ───────────────────────────────────────────
@router.post("/messages/{message_id}/process")
async def process_message(
    message_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Manually (re)trigger AI classification + extraction for a message."""
    from services.facebook_ai import classify_message, extract_order_details

    msg = await db.facebook_messages.find_one(
        {"id": message_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    message_text = msg.get("message_text", "")
    if not message_text:
        raise HTTPException(status_code=400, detail="Message has no text to classify")

    classification_result = await classify_message(message_text)
    classification = classification_result.get("classification", "unknown")
    confidence = float(classification_result.get("confidence", 0.0))

    extracted = None
    if classification_result.get("should_create_draft"):
        extracted = await extract_order_details(message_text)
        if extracted:
            extracted["attachment_present"] = bool(msg.get("attachments"))

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.facebook_messages.update_one(
        {"id": message_id},
        {
            "$set": {
                "classification": classification,
                "confidence_score": confidence,
                "urgency": classification_result.get("urgency", "low"),
                "suggested_reply": classification_result.get("suggested_reply", ""),
                "missing_information": classification_result.get("missing_info", []),
                "extracted_fields": extracted,
                "processing_status": "processed",
                "processed_at": now_iso,
                "updated_at": now_iso,
            }
        },
    )

    await log_audit_event(
        tenant_id=current_user.tenant_id,
        event_type="manual_ai_process",
        details={"message_id": message_id, "classification": classification, "confidence": confidence},
        user_id=current_user.id,
    )

    return {
        "classification": classification,
        "confidence_score": confidence,
        "urgency": classification_result.get("urgency"),
        "suggested_reply": classification_result.get("suggested_reply"),
        "missing_information": classification_result.get("missing_info", []),
        "extracted_fields": extracted,
    }


# ── Generate / refresh suggested reply ───────────────────────────────────────
@router.post("/messages/{message_id}/suggest-reply")
async def suggest_reply(
    message_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Generate a fresh AI-suggested customer reply for a message."""
    from services.facebook_ai import classify_message

    msg = await db.facebook_messages.find_one(
        {"id": message_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "message_text": 1},
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    result = await classify_message(msg.get("message_text", ""))
    suggested_reply = result.get("suggested_reply", "")

    await db.facebook_messages.update_one(
        {"id": message_id},
        {"$set": {"suggested_reply": suggested_reply, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )

    return {"suggested_reply": suggested_reply}


# ── Create lead from message ──────────────────────────────────────────────────
@router.post("/messages/{message_id}/create-lead")
async def create_lead_from_message(
    message_id: str,
    body: CreateLeadRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Manually create a draft lead linked to a Facebook message."""
    msg = await db.facebook_messages.find_one(
        {"id": message_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    extracted = msg.get("extracted_fields") or {}
    customer_name = body.customer_name or extracted.get("customer_name") or f"Facebook Lead ({msg.get('sender_id', 'unknown')})"
    product_interest = body.product_interest or extracted.get("product_type") or "Unknown"

    notes = body.notes or (
        f"Source: Facebook Messenger\n"
        f"Page ID: {msg.get('page_id')}\n"
        f"Sender ID: {msg.get('sender_id')}\n"
        f"Original Message:\n{msg.get('message_text', '')}"
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    lead_id = str(uuid.uuid4())
    await db.leads.insert_one(
        {
            "id": lead_id,
            "tenant_id": current_user.tenant_id,
            "name": customer_name,
            "source": "Facebook Messenger",
            "status": "Facebook Lead - New",
            "review_status": "Needs Review",
            "product_interest": product_interest,
            "notes": notes,
            "facebook_message_id": message_id,
            "facebook_sender_id": msg.get("sender_id"),
            "facebook_page_id": msg.get("page_id"),
            "ai_confidence": msg.get("confidence_score"),
            "ai_classification": msg.get("classification"),
            "extracted_fields": extracted,
            "created_by": current_user.id,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
    )

    await db.facebook_messages.update_one(
        {"id": message_id},
        {"$set": {"linked_lead_id": lead_id, "review_status": "lead_created", "updated_at": now_iso}},
    )

    await log_audit_event(
        tenant_id=current_user.tenant_id,
        event_type="lead_created_manual",
        details={"lead_id": lead_id, "message_id": message_id},
        user_id=current_user.id,
    )

    return {"message": "Lead created", "lead_id": lead_id}


# ── Create draft order from message ──────────────────────────────────────────
@router.post("/messages/{message_id}/create-draft-order")
async def create_draft_order_from_message(
    message_id: str,
    body: CreateDraftOrderRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Manually create a draft order linked to a Facebook message."""
    msg = await db.facebook_messages.find_one(
        {"id": message_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    extracted = msg.get("extracted_fields") or {}
    customer_name = body.customer_name or extracted.get("customer_name") or f"Facebook Lead ({msg.get('sender_id', 'unknown')})"
    product_type = body.product_type or extracted.get("product_type") or "Unknown"
    notes = body.notes or (
        f"Source: Facebook Messenger\n"
        f"Page ID: {msg.get('page_id')}\n"
        f"Sender ID: {msg.get('sender_id')}\n"
        f"Original Message:\n{msg.get('message_text', '')}"
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    order_id = str(uuid.uuid4())
    await db.orders.insert_one(
        {
            "id": order_id,
            "tenant_id": current_user.tenant_id,
            "customer_name": customer_name,
            "source": "Facebook Messenger",
            "status": "draft",
            "review_status": "Needs Review",
            "product_type": product_type,
            "notes": notes,
            "facebook_message_id": message_id,
            "facebook_sender_id": msg.get("sender_id"),
            "facebook_page_id": msg.get("page_id"),
            "ai_confidence": msg.get("confidence_score"),
            "ai_classification": msg.get("classification"),
            "extracted_fields": extracted,
            "created_by": current_user.id,
            "created_at": now_iso,
            "updated_at": now_iso,
        }
    )

    await db.facebook_messages.update_one(
        {"id": message_id},
        {"$set": {"linked_order_id": order_id, "review_status": "order_created", "updated_at": now_iso}},
    )

    await log_audit_event(
        tenant_id=current_user.tenant_id,
        event_type="draft_order_created_manual",
        details={"order_id": order_id, "message_id": message_id},
        user_id=current_user.id,
    )

    return {"message": "Draft order created", "order_id": order_id}


# ── Mark reviewed ─────────────────────────────────────────────────────────────
@router.post("/messages/{message_id}/mark-reviewed")
async def mark_reviewed(
    message_id: str,
    body: MarkReviewedRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Mark a message as reviewed by staff."""
    result = await db.facebook_messages.update_one(
        {"id": message_id, "tenant_id": current_user.tenant_id},
        {
            "$set": {
                "review_status": "reviewed",
                "reviewed_by": current_user.id,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "staff_notes": body.staff_notes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Marked as reviewed"}


# ── Mark spam ─────────────────────────────────────────────────────────────────
@router.post("/messages/{message_id}/mark-spam")
async def mark_spam(
    message_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Mark a message as spam / unrelated."""
    result = await db.facebook_messages.update_one(
        {"id": message_id, "tenant_id": current_user.tenant_id},
        {
            "$set": {
                "review_status": "spam",
                "classification": "spam_or_unrelated",
                "reviewed_by": current_user.id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Marked as spam"}


# ── Summary stats ─────────────────────────────────────────────────────────────
@router.get("/messages/summary/stats")
async def get_message_stats(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return summary counts for the Facebook Leads inbox."""
    tenant_id = current_user.tenant_id
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$review_status", "count": {"$sum": 1}}},
    ]
    by_status = {doc["_id"]: doc["count"] async for doc in db.facebook_messages.aggregate(pipeline)}

    total = sum(by_status.values())
    new_count = by_status.get("new", 0)
    needs_review = sum(v for k, v in by_status.items() if k in ("new", "pending"))

    urgency_pipeline = [
        {"$match": {"tenant_id": tenant_id, "urgency": "high", "review_status": {"$in": ["new", "pending"]}}},
        {"$count": "count"},
    ]
    urgency_result = await db.facebook_messages.aggregate(urgency_pipeline).to_list(1)
    high_urgency = urgency_result[0]["count"] if urgency_result else 0

    return {
        "total": total,
        "new": new_count,
        "needs_review": needs_review,
        "high_urgency": high_urgency,
        "by_status": by_status,
    }
