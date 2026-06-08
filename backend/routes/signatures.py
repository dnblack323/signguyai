"""
Signature capture routes.

Structured signatures are stored against the exact record being signed,
while also carrying order/job context for parent-level visibility.
"""

import base64
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from server import db, get_current_active_user, logger
from models import UserInDB
from services.object_storage import get_object, put_object
from services.email_service import email_service

router = APIRouter(prefix="/signatures", tags=["Signatures"])

SUPPORTED_PARENT_TYPES = {
    "quote",
    "proof",
    "order",
    "change_order",
    "install_record",
    "pickup_record",
    "delivery_record",
    "invoice",
    "form",
    "document",
    "work_order",
}

SIGNATURE_TYPE_MAP = {
    "quote": "quote_acceptance",
    "proof": "artwork_approval",
    "order": "order_authorization",
    "change_order": "change_approval",
    "install_record": "install_completion",
    "pickup_record": "pickup_confirmation",
    "delivery_record": "delivery_confirmation",
    "invoice": "payment_authorization",
    "form": "terms_acknowledgment",
    "document": "terms_acknowledgment",
    "work_order": "order_authorization",
}


class SignatureRequirementPayload(BaseModel):
    parent_record_type: str
    parent_record_id: str
    order_id: Optional[str] = None
    job_ticket_id: Optional[str] = None
    signature_type: Optional[str] = None
    document_version: Optional[str] = None
    requires_signature: bool = True


class SignatureRequestPayload(SignatureRequirementPayload):
    request_email: str
    origin_url: str
    signer_name: Optional[str] = None
    signer_role: Optional[str] = None
    notes: Optional[str] = None
    expires_in_days: int = 7


class SignatureCapturePayload(SignatureRequirementPayload):
    signer_name: str
    signer_role: Optional[str] = None
    printed_name: Optional[str] = None
    notes: Optional[str] = None
    image_data: str


class PublicSignatureCapturePayload(BaseModel):
    signer_name: str
    signer_role: Optional[str] = None
    printed_name: Optional[str] = None
    notes: Optional[str] = None
    image_data: str


class PublicSignatureDeclinePayload(BaseModel):
    signer_name: Optional[str] = None
    notes: Optional[str] = None


def _normalize_signature_type(parent_record_type: str, signature_type: Optional[str]) -> str:
    if signature_type:
        return signature_type
    return SIGNATURE_TYPE_MAP.get(parent_record_type, "order_authorization")


def _normalize_parent_type(parent_record_type: str) -> str:
    normalized = (parent_record_type or "").strip().lower()
    if normalized not in SUPPORTED_PARENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported signature parent record type")
    return normalized


async def _get_tenant_signature_settings(tenant_id: str) -> dict:
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "signature_settings": 1})
    return (tenant or {}).get("signature_settings") or {}


async def _require_signature_feature_enabled(tenant_id: str):
    settings = await _get_tenant_signature_settings(tenant_id)
    if not settings.get("enabled", False):
        raise HTTPException(status_code=404, detail="Signature capture is disabled for this account")
    return settings


def _decode_signature_image(image_data: str) -> bytes:
    try:
        encoded = image_data.split(",", 1)[1] if "," in image_data else image_data
        return base64.b64decode(encoded)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid signature image data") from exc


def _signature_query(payload: SignatureRequirementPayload) -> dict:
    return {
        "parent_record_type": payload.parent_record_type,
        "parent_record_id": payload.parent_record_id,
        "signature_type": payload.signature_type,
        "document_version": payload.document_version or None,
    }


async def _load_signature_parent(parent_record_type: str, parent_record_id: str, tenant_id: str) -> dict:
    if parent_record_type == "order":
        order = await db.orders.find_one({"id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        tickets = await db.job_tickets.find({"order_id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1, "item_name": 1, "quantity": 1, "item_category": 1}).to_list(100)
        return {
            "tenant_id": tenant_id,
            "order_id": order["id"],
            "parent": order,
            "review_snapshot": {
                "label": order.get("order_number") or order["id"],
                "customer_name": order.get("customer_name"),
                "order_number": order.get("order_number"),
                "company_name": order.get("company_name"),
                "requested_due_date": order.get("requested_due_date"),
                "signature_type_label": "Order Authorization",
                "items": tickets,
                "notes": order.get("internal_notes"),
            },
        }

    if parent_record_type in {"change_order", "install_record", "pickup_record", "delivery_record"}:
        order = await db.orders.find_one({"id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        tickets = await db.job_tickets.find({"order_id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1, "item_name": 1, "quantity": 1, "item_category": 1}).to_list(100)
        return {
            "tenant_id": tenant_id,
            "order_id": order["id"],
            "parent": order,
            "review_snapshot": {
                "label": f"{parent_record_type.replace('_', ' ').title()} — {order.get('order_number') or order['id']}",
                "customer_name": order.get("customer_name"),
                "order_number": order.get("order_number"),
                "company_name": order.get("company_name"),
                "requested_due_date": order.get("requested_due_date"),
                "signature_type_label": SIGNATURE_TYPE_MAP.get(parent_record_type, "Signature").replace("_", " ").title(),
                "items": tickets,
                "notes": order.get("pickup_delivery_notes") or order.get("internal_notes"),
            },
        }

    if parent_record_type in {"quote", "invoice", "work_order"}:
        doc = await db.order_quotes.find_one({"id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0})
        if not doc and parent_record_type == "quote":
            doc = await db.quotes.find_one({"id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0})
        if not doc and parent_record_type == "invoice":
            doc = await db.invoices.find_one({"id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Signature document not found")
        order_id = doc.get("order_id")
        order = await db.orders.find_one({"id": order_id, "tenant_id": tenant_id}, {"_id": 0, "order_number": 1}) if order_id else None
        return {
            "tenant_id": tenant_id,
            "order_id": order_id,
            "parent": doc,
            "review_snapshot": {
                "label": (doc.get("type") or parent_record_type).replace("_", " ").title(),
                "customer_name": doc.get("customer_name"),
                "order_number": (order or {}).get("order_number"),
                "signature_type_label": SIGNATURE_TYPE_MAP.get(parent_record_type, "Signature").replace("_", " ").title(),
                "line_items": doc.get("line_items") or doc.get("tickets") or [],
                "total": doc.get("total"),
                "document_version": doc.get("version") or doc.get("updated_at") or doc.get("created_at"),
                "notes": doc.get("notes") or doc.get("internal_notes"),
            },
        }

    if parent_record_type == "proof":
        proof = await db.artwork_proofs.find_one({"id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0})
        if not proof:
            raise HTTPException(status_code=404, detail="Proof not found")
        job = await db.jobs.find_one({"id": proof.get("job_id"), "tenant_id": tenant_id}, {"_id": 0, "name": 1})
        return {
            "tenant_id": tenant_id,
            "order_id": None,
            "parent": proof,
            "review_snapshot": {
                "label": proof.get("file_name") or f"Proof v{proof.get('version', 1)}",
                "customer_name": proof.get("customer_name"),
                "job_name": (job or {}).get("name"),
                "signature_type_label": "Artwork Approval",
                "document_version": proof.get("version"),
                "file_url": proof.get("file_url"),
                "notes": proof.get("description"),
            },
        }

    if parent_record_type in {"document", "form"}:
        doc = await db.documents.find_one({"id": parent_record_id, "tenant_id": tenant_id}, {"_id": 0, "file_data": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            "tenant_id": tenant_id,
            "order_id": (doc.get("linked_jobs") or [None])[0],
            "parent": doc,
            "review_snapshot": {
                "label": doc.get("name"),
                "signature_type_label": "Terms Acknowledgment",
                "document_version": doc.get("updated_at") or doc.get("created_at"),
                "notes": doc.get("description"),
                "file_name": doc.get("original_filename"),
                "category": doc.get("category"),
            },
        }

    raise HTTPException(status_code=400, detail="This record type is not yet wired for signature review")


async def _store_signature_image(signature_id: str, order_id: Optional[str], image_data: str) -> tuple[str, str]:
    image_bytes = _decode_signature_image(image_data)
    if len(image_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Signature appears blank")
    folder = order_id or "global"
    storage_path = f"signguy-ai/signatures/{folder}/{signature_id}.png"
    put_object(storage_path, image_bytes, "image/png")
    return storage_path, f"/api/signatures/file/{signature_id}"


async def _apply_signed_status(signature: dict):
    parent_type = signature.get("parent_record_type")
    parent_id = signature.get("parent_record_id")
    tenant_id = signature.get("tenant_id")
    now = datetime.now(timezone.utc).isoformat()

    base_filter = {"id": parent_id}
    if tenant_id:
        base_filter["tenant_id"] = tenant_id

    if parent_type == "order":
        await db.orders.update_one(base_filter, {"$set": {"approval_status": "approved", "updated_at": now}})
    elif parent_type == "proof":
        await db.artwork_proofs.update_one(base_filter, {"$set": {"status": "approved", "approved_at": now}})
    elif parent_type == "quote":
        await db.order_quotes.update_one(base_filter, {"$set": {"status": "approved", "updated_at": now}})
        await db.quotes.update_one(base_filter, {"$set": {"status": "approved", "updated_at": now}})
    elif parent_type == "invoice":
        await db.order_quotes.update_one(base_filter, {"$set": {"payment_authorized_at": now, "updated_at": now}})
        await db.invoices.update_one(base_filter, {"$set": {"payment_authorized_at": now, "updated_at": now}})


async def _apply_declined_status(signature: dict, notes: Optional[str]):
    parent_type = signature.get("parent_record_type")
    parent_id = signature.get("parent_record_id")
    tenant_id = signature.get("tenant_id")
    now = datetime.now(timezone.utc).isoformat()

    base_filter = {"id": parent_id}
    if tenant_id:
        base_filter["tenant_id"] = tenant_id

    if parent_type == "order":
        await db.orders.update_one(base_filter, {"$set": {"approval_status": "rejected", "updated_at": now}})
    elif parent_type == "proof":
        await db.artwork_proofs.update_one(base_filter, {"$set": {"status": "revision_requested", "customer_comment": notes, "updated_at": now}})
    elif parent_type == "quote":
        await db.order_quotes.update_one(base_filter, {"$set": {"status": "declined", "updated_at": now}})
        await db.quotes.update_one(base_filter, {"$set": {"status": "declined", "updated_at": now}})


@router.get("")
async def list_signatures(
    parent_record_type: Optional[str] = None,
    parent_record_id: Optional[str] = None,
    order_id: Optional[str] = None,
    job_ticket_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _require_signature_feature_enabled(current_user.tenant_id)
    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id}
    if parent_record_type:
        query["parent_record_type"] = parent_record_type
    if parent_record_id:
        query["parent_record_id"] = parent_record_id
    if order_id:
        query["order_id"] = order_id
    if job_ticket_id:
        query["job_ticket_id"] = job_ticket_id
    signatures = await db.signatures.find(query, {"_id": 0, "request_token": 0}).sort("created_at", -1).to_list(200)
    return signatures


@router.post("/requirement")
async def upsert_signature_requirement(
    payload: SignatureRequirementPayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    settings = await _require_signature_feature_enabled(current_user.tenant_id)
    payload.parent_record_type = _normalize_parent_type(payload.parent_record_type)
    payload.signature_type = _normalize_signature_type(payload.parent_record_type, payload.signature_type)
    parent = await _load_signature_parent(payload.parent_record_type, payload.parent_record_id, current_user.tenant_id)

    existing = await db.signatures.find_one({
        **_signature_query(payload),
        "tenant_id": current_user.tenant_id,
        "status": {"$in": ["pending", "expired"]},
    }, {"_id": 0})

    now = datetime.now(timezone.utc).isoformat()
    expiry_days = int(settings.get("link_expiry_days", 7) or 7)
    base_update = {
        "requires_signature": payload.requires_signature,
        "signature_acquired": False,
        "order_id": payload.order_id or parent.get("order_id"),
        "job_ticket_id": payload.job_ticket_id,
        "review_snapshot": parent["review_snapshot"],
        "updated_at": now,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=expiry_days)).isoformat(),
    }

    if existing:
        await db.signatures.update_one({"id": existing["id"]}, {"$set": base_update})
        updated = await db.signatures.find_one({"id": existing["id"]}, {"_id": 0, "request_token": 0})
        return updated

    signature = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "parent_record_type": payload.parent_record_type,
        "parent_record_id": payload.parent_record_id,
        "order_id": payload.order_id or parent.get("order_id"),
        "job_ticket_id": payload.job_ticket_id,
        "signature_type": payload.signature_type,
        "signer_name": "",
        "signer_role": "",
        "printed_name": "",
        "signature_image": None,
        "signed_at": None,
        "notes": "",
        "document_version": payload.document_version,
        "status": "pending",
        "requires_signature": payload.requires_signature,
        "signature_acquired": False,
        "request_email": None,
        "request_token": str(uuid.uuid4()),
        "expires_at": base_update["expires_at"],
        "review_snapshot": parent["review_snapshot"],
        "created_at": now,
        "updated_at": now,
    }
    await db.signatures.insert_one(signature)
    signature.pop("_id", None)
    signature.pop("request_token", None)
    return signature


@router.post("/request")
async def request_signature(
    payload: SignatureRequestPayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _require_signature_feature_enabled(current_user.tenant_id)
    payload.parent_record_type = _normalize_parent_type(payload.parent_record_type)
    payload.signature_type = _normalize_signature_type(payload.parent_record_type, payload.signature_type)
    parent = await _load_signature_parent(payload.parent_record_type, payload.parent_record_id, current_user.tenant_id)
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "name": 1})
    company_name = (tenant or {}).get("name") or "SignGuy AI"

    existing = await db.signatures.find_one({
        **_signature_query(payload),
        "tenant_id": current_user.tenant_id,
        "status": {"$in": ["pending", "expired"]},
    }, {"_id": 0})

    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=max(1, min(payload.expires_in_days, 30)))
    signature_id = existing["id"] if existing else str(uuid.uuid4())
    link = f"{payload.origin_url.rstrip('/')}/customer-sign/{token}" if payload.origin_url else None

    signature_doc = {
        "id": signature_id,
        "tenant_id": current_user.tenant_id,
        "parent_record_type": payload.parent_record_type,
        "parent_record_id": payload.parent_record_id,
        "order_id": payload.order_id or parent.get("order_id"),
        "job_ticket_id": payload.job_ticket_id,
        "signature_type": payload.signature_type,
        "signer_name": payload.signer_name or "",
        "signer_role": payload.signer_role or "",
        "printed_name": "",
        "signature_image": existing.get("signature_image") if existing else None,
        "signed_at": None,
        "notes": payload.notes or "",
        "document_version": payload.document_version,
        "status": "pending",
        "requires_signature": True,
        "signature_acquired": False,
        "request_email": payload.request_email,
        "request_message": payload.notes or "",
        "request_token": token,
        "expires_at": expires_at.isoformat(),
        "review_snapshot": parent["review_snapshot"],
        "created_at": existing.get("created_at", now.isoformat()) if existing else now.isoformat(),
        "updated_at": now.isoformat(),
    }

    await db.signatures.update_one({"id": signature_id}, {"$set": signature_doc}, upsert=True)

    if not link:
        raise HTTPException(status_code=500, detail="Public signature URL is not configured")

    review = parent["review_snapshot"]
    html_content = f"""
    <div style='font-family:Arial,sans-serif;max-width:640px;margin:0 auto;padding:24px;'>
      <h2 style='margin-bottom:12px;color:#0f172a;'>{company_name} Signature Request</h2>
      <p>Please review and sign the requested record.</p>
      <div style='border:1px solid #e2e8f0;border-radius:12px;padding:16px;background:#f8fafc;margin:16px 0;'>
        <p><strong>Record:</strong> {review.get('label') or payload.parent_record_type.title()}</p>
        <p><strong>Signature Type:</strong> {payload.signature_type.replace('_', ' ').title()}</p>
        <p><strong>Customer:</strong> {review.get('customer_name') or payload.signer_name or 'Customer'}</p>
        {f"<p><strong>Order / Job:</strong> {review.get('order_number') or review.get('job_name')}</p>" if review.get('order_number') or review.get('job_name') else ''}
        {f"<p><strong>Version:</strong> {review.get('document_version')}</p>" if review.get('document_version') else ''}
      </div>
      <a href='{link}' style='display:inline-block;background:#0f766e;color:#fff;text-decoration:none;padding:12px 18px;border-radius:999px;'>Review & Sign</a>
      <p style='font-size:12px;color:#64748b;margin-top:16px;'>This secure link expires on {expires_at.strftime('%b %d, %Y %I:%M %p UTC')}.</p>
    </div>
    """
    email_result = await email_service.send_email(
        to_email=payload.request_email,
        subject=f"Review & Sign: {review.get('label') or payload.parent_record_type.replace('_', ' ').title()}",
        html_content=html_content,
        tenant_id=current_user.tenant_id,
    )
    if not email_result.get("success"):
        raise HTTPException(status_code=500, detail=email_result.get("error") or "Failed to send signature request")

    return {"message": "Signature request sent", "signature_id": signature_id, "expires_at": expires_at.isoformat()}


@router.post("/capture")
async def capture_signature_internal(
    payload: SignatureCapturePayload,
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _require_signature_feature_enabled(current_user.tenant_id)
    payload.parent_record_type = _normalize_parent_type(payload.parent_record_type)
    payload.signature_type = _normalize_signature_type(payload.parent_record_type, payload.signature_type)
    parent = await _load_signature_parent(payload.parent_record_type, payload.parent_record_id, current_user.tenant_id)
    existing = await db.signatures.find_one({
        **_signature_query(payload),
        "tenant_id": current_user.tenant_id,
        "status": {"$in": ["pending", "expired"]},
    }, {"_id": 0})

    # Extract client IP address
    client_ip = None
    if request.client:
        client_ip = request.client.host
    # Check for forwarded IP (behind proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    signature_id = existing["id"] if existing else str(uuid.uuid4())
    storage_path, image_url = await _store_signature_image(signature_id, payload.order_id or parent.get("order_id"), payload.image_data)
    signed_at = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": signature_id,
        "tenant_id": current_user.tenant_id,
        "parent_record_type": payload.parent_record_type,
        "parent_record_id": payload.parent_record_id,
        "order_id": payload.order_id or parent.get("order_id"),
        "job_ticket_id": payload.job_ticket_id,
        "signature_type": payload.signature_type,
        "signer_name": payload.signer_name,
        "signer_role": payload.signer_role or current_user.role,
        "printed_name": payload.printed_name or payload.signer_name,
        "signature_image": image_url,
        "signature_storage_path": storage_path,
        "signed_at": signed_at,
        "client_ip": client_ip,
        "notes": payload.notes or "",
        "document_version": payload.document_version,
        "status": "signed",
        "requires_signature": True,
        "signature_acquired": True,
        "request_email": existing.get("request_email") if existing else None,
        "request_token": existing.get("request_token") if existing else None,
        "expires_at": existing.get("expires_at") if existing else None,
        "review_snapshot": parent["review_snapshot"],
        "created_at": existing.get("created_at", signed_at) if existing else signed_at,
        "updated_at": signed_at,
    }
    await db.signatures.update_one({"id": signature_id}, {"$set": doc}, upsert=True)
    await _apply_signed_status(doc)
    safe_doc = {**doc}
    safe_doc.pop("request_token", None)
    return safe_doc


@router.get("/public/{token}")
async def get_public_signature_request(token: str):
    signature = await db.signatures.find_one({"request_token": token}, {"_id": 0})
    if not signature:
        raise HTTPException(status_code=404, detail="Signature request not found")
    await _require_signature_feature_enabled(signature["tenant_id"])
    if signature.get("status") == "expired":
        raise HTTPException(status_code=410, detail="Signature request has expired")
    if signature.get("expires_at") and datetime.fromisoformat(signature["expires_at"].replace("Z", "+00:00")) < datetime.now(timezone.utc):
        await db.signatures.update_one({"id": signature["id"]}, {"$set": {"status": "expired", "updated_at": datetime.now(timezone.utc).isoformat()}})
        raise HTTPException(status_code=410, detail="Signature request has expired")
    return {
        "id": signature["id"],
        "parent_record_type": signature["parent_record_type"],
        "parent_record_id": signature["parent_record_id"],
        "order_id": signature.get("order_id"),
        "job_ticket_id": signature.get("job_ticket_id"),
        "signature_type": signature["signature_type"],
        "status": signature["status"],
        "requires_signature": signature.get("requires_signature", True),
        "signature_acquired": signature.get("signature_acquired", False),
        "document_version": signature.get("document_version"),
        "review_snapshot": signature.get("review_snapshot") or {},
        "signature_image": signature.get("signature_image"),
        "signed_at": signature.get("signed_at"),
        "expires_at": signature.get("expires_at"),
    }


@router.post("/public/{token}/sign")
async def sign_public_request(token: str, payload: PublicSignatureCapturePayload, request: Request):
    signature = await db.signatures.find_one({"request_token": token}, {"_id": 0})
    if not signature:
        raise HTTPException(status_code=404, detail="Signature request not found")
    await _require_signature_feature_enabled(signature["tenant_id"])

    # Block re-signing or signing a declined/expired/completed request
    sig_status = signature.get("status")
    if sig_status == "signed":
        raise HTTPException(status_code=400, detail="Signature has already been completed")
    if sig_status == "declined":
        raise HTTPException(status_code=400, detail="This request was already declined and cannot be signed")
    if sig_status == "expired":
        raise HTTPException(status_code=410, detail="Signature request has expired")
    # Also check expiry timestamp
    if signature.get("expires_at"):
        try:
            expires = datetime.fromisoformat(signature["expires_at"].replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expires:
                await db.signatures.update_one({"id": signature["id"]}, {"$set": {"status": "expired", "updated_at": datetime.now(timezone.utc).isoformat()}})
                raise HTTPException(status_code=410, detail="Signature request has expired")
        except HTTPException:
            raise
        except Exception:
            pass

    # Extract client IP address
    client_ip = None
    if request.client:
        client_ip = request.client.host
    # Check for forwarded IP (behind proxy)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    storage_path, image_url = await _store_signature_image(signature["id"], signature.get("order_id"), payload.image_data)
    signed_at = datetime.now(timezone.utc).isoformat()
    update_doc = {
        "signer_name": payload.signer_name,
        "signer_role": payload.signer_role or signature.get("signer_role") or "customer",
        "printed_name": payload.printed_name or payload.signer_name,
        "signature_image": image_url,
        "signature_storage_path": storage_path,
        "signed_at": signed_at,
        "client_ip": client_ip,
        "notes": payload.notes or signature.get("notes") or "",
        "status": "signed",
        "signature_acquired": True,
        "updated_at": signed_at,
    }
    await db.signatures.update_one({"id": signature["id"]}, {"$set": update_doc})
    signed_signature = {**signature, **update_doc}
    await _apply_signed_status(signed_signature)
    return {"message": "Signature captured", "signed_at": signed_at}


@router.post("/public/{token}/decline")
async def decline_public_request(token: str, payload: PublicSignatureDeclinePayload):
    signature = await db.signatures.find_one({"request_token": token}, {"_id": 0})
    if not signature:
        raise HTTPException(status_code=404, detail="Signature request not found")
    await _require_signature_feature_enabled(signature["tenant_id"])

    sig_status = signature.get("status")
    if sig_status == "declined":
        raise HTTPException(status_code=400, detail="This request has already been declined")
    if sig_status == "signed":
        raise HTTPException(status_code=400, detail="This request has already been signed and cannot be declined")
    if sig_status == "expired":
        raise HTTPException(status_code=410, detail="Signature request has expired")

    now = datetime.now(timezone.utc).isoformat()
    await db.signatures.update_one({"id": signature["id"]}, {"$set": {
        "status": "declined",
        "updated_at": now,
        "notes": payload.notes or signature.get("notes") or "",
        "signer_name": payload.signer_name or signature.get("signer_name") or "",
    }})
    await _apply_declined_status(signature, payload.notes)
    return {"message": "Signature request declined"}


@router.get("/file/{signature_id}")
async def get_signature_file(signature_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Download a signature image — authenticated, tenant-scoped."""
    signature = await db.signatures.find_one(
        {"id": signature_id, "tenant_id": current_user.tenant_id, "signature_storage_path": {"$exists": True}},
        {"_id": 0, "signature_storage_path": 1}
    )
    if not signature:
        raise HTTPException(status_code=404, detail="Signature image not found")
    data, _content_type = get_object(signature["signature_storage_path"])
    return Response(content=data, media_type="image/png")