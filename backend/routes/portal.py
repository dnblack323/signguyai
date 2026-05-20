"""
Customer Portal Routes

This module contains all routes for the customer-facing portal:
- Portal authentication (register, login, password change)
- Customer profile management
- Dashboard with stats
- Orders (jobs) viewing
- Quotes viewing
- Invoices viewing
- Messaging/conversations
- Artwork proof approval
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import jwt
import uuid
import base64
import os
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from services.object_storage import get_object

from models import (
    Conversation, ConversationMessage, MessageType,
    ArtworkProof, ProofStatus,
    CustomerNotification,
    CustomerPortalLogin, CustomerPortalRegister, CustomerPortalToken,
    CustomerProfileUpdate, ConversationCreate, MessageCreate, ProofResponseCreate
)
from models.questionnaires import QuestionnaireResponse

# Import from server module
from server import (
    db, logger, security,
    SECRET_KEY, ALGORITHM,
    get_password_hash, verify_password, create_access_token
)

router = APIRouter(prefix="/portal", tags=["Customer Portal"])


def _normalize_order_status(raw_status: Optional[str]) -> str:
    if not raw_status:
        return "pending"
    status = str(raw_status).lower()
    mapping = {
        "new_intake": "pending",
        "awaiting_review": "pending",
        "awaiting_quote": "quoted",
        "quote_sent": "quoted",
        "awaiting_approval": "approved",
        "approved": "approved",
        "ready_for_pickup": "installed",
        "out_for_delivery": "installed",
        "completed": "complete",
        "cancelled": "archived",
    }
    return mapping.get(status, status)


def _normalize_order_document(doc: Dict[str, Any], source: str) -> Dict[str, Any]:
    normalized_status = _normalize_order_status(doc.get("status"))
    created_at = doc.get("created_at") or doc.get("date_created")
    due_date = doc.get("due_date") or doc.get("requested_due_date")
    subtotal = doc.get("subtotal")
    if subtotal is None:
        subtotal = doc.get("total", 0)

    return {
        **doc,
        "status": normalized_status,
        "created_at": created_at,
        "due_date": due_date,
        "subtotal": subtotal,
        "source_type": source,
    }


def _order_matches_filter(doc: Dict[str, Any], status: Optional[str]) -> bool:
    if not status:
        return True

    normalized = _normalize_order_status(doc.get("status"))
    if status == "active":
        return normalized not in ["complete", "archived"]
    if status == "awaiting_approval":
        return normalized in ["approved", "quoted", "awaiting_approval"]
    if status == "completed":
        return normalized == "complete"
    if status == "archived":
        return normalized == "archived" or bool(doc.get("is_archived"))

    return normalized == status


async def _fetch_portal_orders_combined(customer: Dict[str, Any], status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    customer_id = customer["id"]
    tenant_id = customer.get("tenant_id")

    orders_query: Dict[str, Any] = {"customer_id": customer_id}
    jobs_query: Dict[str, Any] = {"customer_id": customer_id}
    if tenant_id:
        orders_query["tenant_id"] = tenant_id
        jobs_query["tenant_id"] = tenant_id

    order_rows = await db.orders.find(orders_query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    job_rows = await db.jobs.find(jobs_query, {"_id": 0}).sort("created_at", -1).to_list(limit)

    merged: Dict[str, Dict[str, Any]] = {}
    for row in order_rows:
        normalized = _normalize_order_document(row, "orders")
        if _order_matches_filter(normalized, status):
            merged[normalized["id"]] = normalized

    for row in job_rows:
        normalized = _normalize_order_document(row, "jobs")
        if _order_matches_filter(normalized, status) and normalized["id"] not in merged:
            merged[normalized["id"]] = normalized

    return sorted(
        merged.values(),
        key=lambda row: row.get("created_at") or "",
        reverse=True,
    )[:limit]


def _normalize_quote_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **doc,
        "status": (doc.get("status") or "draft").lower(),
        "total": doc.get("total", 0),
        "created_at": doc.get("created_at") or doc.get("updated_at"),
    }


async def _fetch_portal_quotes_combined(customer: Dict[str, Any], status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    customer_id = customer["id"]
    tenant_id = customer.get("tenant_id")

    q1: Dict[str, Any] = {"customer_id": customer_id}
    q2: Dict[str, Any] = {"customer_id": customer_id, "type": "quote"}
    if tenant_id:
        q1["tenant_id"] = tenant_id
        q2["tenant_id"] = tenant_id

    quotes = await db.quotes.find(q1, {"_id": 0}).sort("created_at", -1).to_list(limit)
    legacy_quotes = await db.order_quotes.find(q2, {"_id": 0}).sort("created_at", -1).to_list(limit)

    merged: Dict[str, Dict[str, Any]] = {}
    for row in quotes + legacy_quotes:
        normalized = _normalize_quote_document(row)
        if status and normalized.get("status") != status:
            continue
        merged[normalized["id"]] = normalized

    return sorted(
        merged.values(),
        key=lambda row: row.get("created_at") or "",
        reverse=True,
    )[:limit]


def _normalize_invoice_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    total = float(doc.get("grand_total", doc.get("total", 0)) or 0)
    amount_paid = float(doc.get("amount_paid", 0) or 0)
    status = (doc.get("status") or "draft").lower()

    if amount_paid >= total and total > 0:
        status = "paid"

    return {
        **doc,
        "status": status,
        "total": total,
        "amount_paid": amount_paid,
        "created_at": doc.get("created_at") or doc.get("updated_at"),
    }


async def _fetch_portal_invoices_combined(customer: Dict[str, Any], status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    customer_id = customer["id"]
    tenant_id = customer.get("tenant_id")

    q1: Dict[str, Any] = {"customer_id": customer_id}
    q2: Dict[str, Any] = {"customer_id": customer_id, "type": "invoice"}
    if tenant_id:
        q1["tenant_id"] = tenant_id
        q2["tenant_id"] = tenant_id

    invoices = await db.invoices.find(q1, {"_id": 0}).sort("created_at", -1).to_list(limit)
    legacy_invoices = await db.order_quotes.find(q2, {"_id": 0}).sort("created_at", -1).to_list(limit)

    merged: Dict[str, Dict[str, Any]] = {}
    for row in invoices + legacy_invoices:
        normalized = _normalize_invoice_document(row)
        if status and normalized.get("status") != status:
            continue
        merged[normalized["id"]] = normalized

    return sorted(
        merged.values(),
        key=lambda row: row.get("created_at") or "",
        reverse=True,
    )[:limit]


async def _find_portal_invoice_document(invoice_id: str, tenant_id: Optional[str]) -> Optional[Dict[str, Any]]:
    query: Dict[str, Any] = {"id": invoice_id}
    if tenant_id:
        query["tenant_id"] = tenant_id

    invoice = await db.invoices.find_one(query, {"_id": 0})
    if invoice:
        return _normalize_invoice_document(invoice)

    legacy_query = {**query, "type": "invoice"}
    legacy = await db.order_quotes.find_one(legacy_query, {"_id": 0})
    if legacy:
        return _normalize_invoice_document(legacy)

    return None


def build_customer_status_timeline(job: dict, proofs: List[dict], form_requests: List[dict], invoice: Optional[dict]) -> List[dict]:
    timeline = []
    timeline.append({"label": "Quote Approved" if job.get("status") != "quoted" else "Quote Sent", "status": "complete" if job.get("status") != "quoted" else "current"})
    timeline.append({"label": "Design In Progress", "status": "complete" if proofs else ("current" if job.get("status") in ["approved", "design"] else "upcoming")})
    proof_pending = any(proof.get("status") == "pending" for proof in proofs)
    proof_approved = any(proof.get("status") == "approved" for proof in proofs)
    timeline.append({"label": "Awaiting Artwork Approval", "status": "complete" if proof_approved else ("current" if proof_pending else "upcoming")})
    form_pending = any(request.get("status") in ["pending", "in_progress", "overdue"] for request in form_requests)
    if form_requests:
        timeline.append({"label": "Forms / Questionnaire", "status": "complete" if not form_pending else "current"})
    timeline.append({"label": "In Production", "status": "complete" if job.get("status") in ["installed", "complete"] else ("current" if job.get("status") in ["in_production", "production"] else "upcoming")})
    timeline.append({"label": "Scheduled for Pickup / Install", "status": "complete" if job.get("status") in ["installed", "complete"] else ("current" if job.get("status") in ["scheduled", "install_scheduled"] else "upcoming")})
    timeline.append({"label": "Completed", "status": "complete" if job.get("status") == "complete" else "upcoming"})
    if invoice:
        timeline.append({"label": "Invoice Paid" if invoice.get("status") == "paid" else "Invoice Unpaid", "status": "complete" if invoice.get("status") == "paid" else "current"})
    return timeline


def format_form_response_document(questionnaire: dict, answers: Dict[str, Any], customer_name: str, submitted_at: str) -> str:
    question_map = {question.get("id"): question for question in questionnaire.get("questions", [])}
    lines = [
        f"Questionnaire Submission: {questionnaire.get('name')}",
        f"Submitted by: {customer_name}",
        f"Submitted at: {submitted_at}",
        "",
    ]
    for question_id, answer in answers.items():
        label = question_map.get(question_id, {}).get("label", question_id)
        rendered_answer = ", ".join(answer) if isinstance(answer, list) else str(answer)
        lines.append(f"{label}: {rendered_answer}")
    return "\n".join(lines)


# ============== PORTAL AUTH HELPER ==============

async def get_current_portal_customer(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get customer from portal JWT token"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate portal credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if credentials is None:
        raise credentials_exception
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        customer_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        if customer_id is None or token_type != "portal":
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Portal token has expired")
    except jwt.PyJWTError:
        raise credentials_exception
    
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    if customer is None:
        raise credentials_exception
    
    if not customer.get("portal_enabled", False):
        raise HTTPException(status_code=403, detail="Portal access is disabled for this account")
    
    return customer


# ============== PORTAL AUTH ROUTES ==============

@router.post("/auth/register", response_model=CustomerPortalToken)
async def portal_register(input: CustomerPortalRegister):
    """Register/enable portal access for an existing customer"""
    # Find customer by email
    customer = await db.customers.find_one({"email": input.email.lower()}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="No customer account found with this email. Please contact the sign shop.")
    
    if customer.get("portal_enabled") and customer.get("portal_password_hash"):
        raise HTTPException(status_code=400, detail="Portal access already enabled. Please login instead.")
    
    # Hash password and enable portal
    hashed_password = get_password_hash(input.password)
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$set": {
            "portal_password_hash": hashed_password,
            "portal_enabled": True,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Create portal token
    access_token = create_access_token(
        data={"sub": customer["id"], "type": "portal"},
        expires_delta=timedelta(days=30)
    )
    
    return CustomerPortalToken(
        access_token=access_token,
        customer_id=customer["id"],
        customer_name=customer["name"]
    )


@router.post("/auth/login", response_model=CustomerPortalToken)
async def portal_login(input: CustomerPortalLogin):
    """Login to customer portal"""
    customer = await db.customers.find_one({"email": input.email.lower()}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not customer.get("portal_enabled"):
        raise HTTPException(status_code=403, detail="Portal access is not enabled for this account")
    
    if not customer.get("portal_password_hash"):
        raise HTTPException(status_code=400, detail="Portal password not set. Please register first.")
    
    if not verify_password(input.password, customer["portal_password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create portal token
    access_token = create_access_token(
        data={"sub": customer["id"], "type": "portal"},
        expires_delta=timedelta(days=30)
    )
    
    return CustomerPortalToken(
        access_token=access_token,
        customer_id=customer["id"],
        customer_name=customer["name"]
    )


# ============== PORTAL PROFILE ==============

@router.get("/profile")
async def get_portal_profile(customer: dict = Depends(get_current_portal_customer)):
    """Get current customer's profile"""
    # Remove sensitive fields
    safe_customer = {k: v for k, v in customer.items() if k != "portal_password_hash"}
    return safe_customer


@router.put("/profile")
async def update_portal_profile(
    input: CustomerProfileUpdate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Update customer profile"""
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$set": update_data}
    )
    
    updated = await db.customers.find_one({"id": customer["id"]}, {"_id": 0, "portal_password_hash": 0})
    return updated


@router.put("/change-password")
async def change_portal_password(
    current_password: str,
    new_password: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Change portal password"""
    if not verify_password(current_password, customer.get("portal_password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    hashed = get_password_hash(new_password)
    await db.customers.update_one(
        {"id": customer["id"]},
        {"$set": {"portal_password_hash": hashed, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Password changed successfully"}


# ============== PORTAL DASHBOARD ==============

@router.get("/dashboard")
async def get_portal_dashboard(customer: dict = Depends(get_current_portal_customer)):
    """Get customer portal dashboard data"""
    customer_id = customer["id"]

    # Unified data sources (orders/jobs + quotes + invoices + legacy order_quotes)
    combined_orders = await _fetch_portal_orders_combined(customer, limit=300)
    combined_quotes = await _fetch_portal_quotes_combined(customer, limit=300)
    combined_invoices = await _fetch_portal_invoices_combined(customer, limit=300)

    total_quotes = len(combined_quotes)
    active_jobs = len([row for row in combined_orders if row.get("status") not in ["complete", "archived"]])
    pending_invoices = len([
        row for row in combined_invoices
        if row.get("status") in ["sent", "draft", "pending", "unpaid", "partially_paid", "deposit_paid"]
    ])
    pending_proofs = await db.artwork_proofs.count_documents({"customer_id": customer_id, "status": "pending"})
    
    # Get unread message count
    conversations = await db.conversations.find({"customer_id": customer_id}, {"_id": 0}).to_list(100)
    unread_messages = sum(c.get("unread_customer", 0) for c in conversations)
    
    # Get unread notifications
    unread_notifications = await db.customer_notifications.count_documents({"customer_id": customer_id, "is_read": False})

    pending_forms = await db.portal_form_requests.count_documents({
        "customer_id": customer_id,
        "status": {"$in": ["pending", "in_progress", "overdue"]}
    })

    unread_docs = await db.portal_documents.count_documents({
        "customer_id": customer_id,
        "viewed_at": None
    })
    
    # Get upcoming appointments
    today = datetime.now(timezone.utc).date().isoformat()
    upcoming_appointments = await db.appointments.find(
        {"customer_id": customer_id, "scheduled_date": {"$gte": today}, "status": {"$in": ["scheduled", "confirmed"]}},
        {"_id": 0}
    ).sort("scheduled_date", 1).limit(5).to_list(5)
    
    recent_jobs = combined_orders[:5]
    recent_invoices = combined_invoices[:5]

    recent_documents = await db.portal_documents.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)

    pending_form_requests = await db.portal_form_requests.find(
        {"customer_id": customer_id, "status": {"$in": ["pending", "in_progress", "overdue"]}},
        {"_id": 0}
    ).sort("due_date", 1).limit(5).to_list(5)

    awaiting_approval = await db.artwork_proofs.find(
        {"customer_id": customer_id, "status": "pending"},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)

    # Count webstores assigned to this portal user (by owner_email).
    # Used by the portal nav to conditionally render the Webstores tab.
    # Case-insensitive match — mirrors the list/detail endpoints below so the
    # nav-tab visibility and the page contents never disagree.
    assigned_webstore_count = 0
    customer_email = (customer.get("email") or "").strip().lower()
    if customer_email:
        import re as _re_email
        ws_query: Dict[str, Any] = {
            "owner_email": {"$regex": f"^{_re_email.escape(customer_email)}$", "$options": "i"},
        }
        if customer.get("tenant_id"):
            ws_query["tenant_id"] = customer["tenant_id"]
        assigned_webstore_count = await db.webstores_v2.count_documents(ws_query)

    return {
        "stats": {
            "total_quotes": total_quotes,
            "active_jobs": active_jobs,
            "pending_invoices": pending_invoices,
            "pending_proofs": pending_proofs,
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications,
            "pending_forms": pending_forms,
            "recent_documents": unread_docs,
            "overdue_invoices": len([inv for inv in combined_invoices if inv.get("status") == "overdue"]),
            "paid_invoices": len([inv for inv in combined_invoices if inv.get("status") == "paid"]),
            "assigned_webstores": assigned_webstore_count,
        },
        "has_webstores": assigned_webstore_count > 0,
        "upcoming_appointments": upcoming_appointments,
        "recent_jobs": recent_jobs,
        "recent_invoices": recent_invoices,
        "recent_documents": recent_documents,
        "pending_forms": pending_form_requests,
        "awaiting_approval": awaiting_approval
    }


# ============== PORTAL ORDERS/JOBS ==============

@router.get("/orders")
async def get_portal_orders(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's orders (jobs)"""
    orders = await _fetch_portal_orders_combined(customer, status=status, limit=120)

    # Enrich with item/proof/invoice snapshots used by portal UI cards
    for order in orders:
        order_id = order["id"]
        if order.get("source_type") == "orders":
            items = await db.job_tickets.find({"order_id": order_id}, {"_id": 0}).to_list(80)
        else:
            items = await db.job_items.find({"job_id": order_id}, {"_id": 0}).to_list(80)
        order["items"] = items

        proofs = await db.artwork_proofs.find(
            {"customer_id": customer["id"], "$or": [{"job_id": order_id}, {"order_id": order_id}]},
            {"_id": 0},
        ).to_list(25)
        order["approval_status"] = "awaiting_approval" if any(proof.get("status") == "pending" for proof in proofs) else "approved"

        linked_invoice_ids = order.get("linked_invoice_ids") or []
        invoice_id = linked_invoice_ids[0] if linked_invoice_ids else order.get("invoice_id")
        invoice_doc = None
        if invoice_id:
            invoice_doc = await _find_portal_invoice_document(invoice_id, customer.get("tenant_id"))
        order["invoice_status"] = (invoice_doc or {}).get("status")

    return orders


@router.get("/orders/{job_id}")
async def get_portal_order_detail(
    job_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get single order detail"""
    tenant_filter = {"tenant_id": customer.get("tenant_id")} if customer.get("tenant_id") else {}
    order = await db.orders.find_one({"id": job_id, "customer_id": customer["id"], **tenant_filter}, {"_id": 0})
    source_type = "orders"
    if order:
        job = _normalize_order_document(order, "orders")
    else:
        job = await db.jobs.find_one({"id": job_id, "customer_id": customer["id"], **tenant_filter}, {"_id": 0})
        source_type = "jobs"

    if not job:
        raise HTTPException(status_code=404, detail="Order not found")

    if source_type == "orders":
        items = await db.job_tickets.find({"order_id": job_id}, {"_id": 0}).to_list(120)
    else:
        items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(120)
    job["items"] = items

    # Get associated quote if any
    quote = None
    quote_id = (job.get("linked_quote_ids") or [None])[0] or job.get("quote_id")
    if quote_id:
        quote = await db.quotes.find_one({"id": quote_id, **tenant_filter}, {"_id": 0})
        if not quote:
            quote = await db.order_quotes.find({"id": quote_id, "type": "quote", **tenant_filter}, {"_id": 0}).to_list(1)
            quote = quote[0] if quote else None
    if quote:
        job["quote"] = quote
    
    # Get associated invoice if any
    invoice_id = (job.get("linked_invoice_ids") or [None])[0] or job.get("invoice_id")
    if invoice_id:
        invoice = await _find_portal_invoice_document(invoice_id, customer.get("tenant_id"))
        job["invoice"] = invoice
    
    # Get artwork proofs
    proofs = await db.artwork_proofs.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(20)
    job["proofs"] = proofs

    portal_docs = await db.portal_documents.find(
        {"customer_id": customer["id"], "$or": [{"job_id": job_id}, {"related_job_id": job_id}]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    job["documents"] = portal_docs

    form_requests = await db.portal_form_requests.find(
        {"customer_id": customer["id"], "job_id": job_id},
        {"_id": 0}
    ).sort("sent_at", -1).to_list(50)
    job["forms"] = form_requests

    conversations = await db.conversations.find(
        {"customer_id": customer["id"], "related_job_id": job_id},
        {"_id": 0}
    ).sort("last_message_at", -1).to_list(50)
    job["conversations"] = conversations

    job["customer_status_timeline"] = build_customer_status_timeline(job, proofs, form_requests, job.get("invoice"))

    # ─────── Phase 2F: Vehicle Wrap Project section ───────
    # If any line-item on this order is a wrap category, attach the
    # customer-facing wrap summary so the portal can render its own
    # "Vehicle Wrap Project" card. NO separate portal — this is part of the
    # existing customer portal order detail response.
    try:
        from routes.wrap.core import _is_wrap_category  # local import to avoid circulars
        from routes.wrap.portal import build_customer_facing_summary

        wrap_items: List[Dict[str, Any]] = []
        for ticket in items:
            if _is_wrap_category(ticket.get("item_category")):
                summary = await build_customer_facing_summary(
                    tenant_id=customer.get("tenant_id"),
                    ticket_id=ticket.get("id"),
                    ticket=ticket,
                )
                wrap_items.append(summary)
        if wrap_items:
            job["wrap_items"] = wrap_items
    except Exception as exc:  # noqa: BLE001 — wrap section is non-blocking
        logger.warning(f"portal: failed to attach wrap_items for order {job_id}: {exc}")

    return job


# ============== PORTAL QUOTES ==============

@router.get("/quotes")
async def get_portal_quotes(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's quotes"""
    return await _fetch_portal_quotes_combined(customer, status=status, limit=150)


# ============== PORTAL INVOICES ==============

@router.get("/invoices")
async def get_portal_invoices(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's invoices"""
    return await _fetch_portal_invoices_combined(customer, status=status, limit=150)


# ============== PORTAL MESSAGING ==============

@router.get("/conversations")
async def get_portal_conversations(customer: dict = Depends(get_current_portal_customer)):
    """Get all conversations for the customer"""
    conversations = await db.conversations.find(
        {"customer_id": customer["id"]},
        {"_id": 0}
    ).sort("last_message_at", -1).to_list(100)
    return conversations


@router.post("/conversations")
async def create_portal_conversation(
    input: ConversationCreate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Start a new conversation"""
    conversation = Conversation(
        customer_id=customer["id"],
        tenant_id=customer.get("tenant_id"),
        subject=input.subject,
        related_job_id=input.related_job_id,
        related_quote_id=input.related_quote_id,
        last_message_preview=input.message[:100],
        unread_shop=1
    )
    
    await db.conversations.insert_one(conversation.model_dump())
    
    # Create first message
    message = ConversationMessage(
        conversation_id=conversation.id,
        sender_type="customer",
        sender_id=customer["id"],
        sender_name=customer["name"],
        content=input.message
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    return conversation.model_dump()


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get messages in a conversation"""
    # Verify conversation belongs to customer
    conv = await db.conversations.find_one({"id": conversation_id, "customer_id": customer["id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    messages = await db.conversation_messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Mark as read
    await db.conversation_messages.update_many(
        {"conversation_id": conversation_id, "sender_type": "shop", "is_read": False},
        {"$set": {"is_read": True}}
    )
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"unread_customer": 0}}
    )
    
    return {"conversation": conv, "messages": messages}


@router.post("/conversations/{conversation_id}/messages")
async def send_portal_message(
    conversation_id: str,
    input: MessageCreate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Send a message in a conversation"""
    # Verify conversation belongs to customer
    conv = await db.conversations.find_one({"id": conversation_id, "customer_id": customer["id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if conv.get("is_closed"):
        raise HTTPException(status_code=400, detail="This conversation is closed")
    
    content = (input.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")

    # Create message
    message = ConversationMessage(
        conversation_id=conversation_id,
        sender_type="customer",
        sender_id=customer["id"],
        sender_name=customer["name"],
        content=content,
        message_type=input.message_type or MessageType.TEXT
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    # Update conversation
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "last_message_preview": content[:100]
        }, "$inc": {"unread_shop": 1}}
    )
    
    return message.model_dump()


# ============== PORTAL ARTWORK PROOFS ==============

@router.get("/proofs")
async def get_portal_proofs(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get all artwork proofs for the customer"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    proofs = await db.artwork_proofs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with job info
    for proof in proofs:
        job = await db.jobs.find_one({"id": proof["job_id"]}, {"_id": 0, "id": 1, "name": 1})
        if not job:
            order = await db.orders.find_one({"id": proof["job_id"]}, {"_id": 0, "id": 1, "order_number": 1})
            job = {"id": order["id"], "name": order.get("order_number", "Order")} if order else None
        proof["job"] = job
    
    return proofs


@router.get("/proofs/{proof_id}")
async def get_portal_proof_detail(
    proof_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get single proof detail"""
    proof = await db.artwork_proofs.find_one({"id": proof_id, "customer_id": customer["id"]}, {"_id": 0})
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    # Get job info
    job = await db.jobs.find_one({"id": proof["job_id"]}, {"_id": 0})
    if not job:
        order = await db.orders.find_one({"id": proof["job_id"]}, {"_id": 0, "id": 1, "order_number": 1})
        job = {"id": order["id"], "name": order.get("order_number", "Order")} if order else None
    proof["job"] = job

    history = await db.artwork_proofs.find(
        {"job_id": proof["job_id"], "customer_id": customer["id"]},
        {"_id": 0, "id": 1, "version": 1, "status": 1, "created_at": 1, "customer_comment": 1, "description": 1}
    ).sort("version", -1).to_list(20)
    proof["version_history"] = history
    
    return proof


@router.post("/proofs/{proof_id}/respond")
async def respond_to_proof(
    proof_id: str,
    input: ProofResponseCreate,
    customer: dict = Depends(get_current_portal_customer)
):
    """Approve, reject, or request revision on a proof"""
    proof = await db.artwork_proofs.find_one({"id": proof_id, "customer_id": customer["id"]}, {"_id": 0})
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    if proof.get("status") != "pending":
        raise HTTPException(status_code=400, detail="This proof has already been responded to")
    
    update_data = {
        "status": input.status.value,
        "customer_comment": input.comment
    }
    
    if input.status == ProofStatus.APPROVED:
        update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
    elif input.status == ProofStatus.REJECTED:
        update_data["rejected_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.artwork_proofs.update_one({"id": proof_id}, {"$set": update_data})
    
    # Create notification for shop
    status_text = "approved" if input.status == ProofStatus.APPROVED else "rejected" if input.status == ProofStatus.REJECTED else "requested revisions on"
    notification = CustomerNotification(
        tenant_id=customer.get("tenant_id"),
        customer_id=customer["id"],
        notification_type="proof_response",
        title=f"Proof {status_text}",
        message=f"{customer['name']} has {status_text} proof for job {proof.get('job_id', '')[:8]}",
        related_id=proof_id
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    return {"message": f"Proof {status_text}", "status": input.status.value}


@router.post("/invoices/{invoice_id}/viewed")
async def mark_invoice_viewed(
    invoice_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    invoice = await db.invoices.find_one({"id": invoice_id, "customer_id": customer["id"]}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.invoices.update_one({"id": invoice_id}, {"$set": {"portal_viewed_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Invoice view recorded"}


@router.post("/invoices/{invoice_id}/pay")
async def create_portal_invoice_payment(
    invoice_id: str,
    payload: Dict[str, Any] = Body(...),
    customer: dict = Depends(get_current_portal_customer)
):
    invoice = await db.invoices.find_one({"id": invoice_id, "customer_id": customer["id"]}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.get("status") == "paid":
        raise HTTPException(status_code=400, detail="Invoice already paid")

    tenant = await db.tenants.find_one({"id": customer.get("tenant_id")}, {"_id": 0})
    if not tenant or not tenant.get("stripe_connect_account_id"):
        raise HTTPException(status_code=400, detail="Online payments are not set up yet. Go to Settings > Payment Settings to connect your Stripe account.")

    from routes.stripe_connect import stripe, get_tenant_tier, get_platform_fee_percent

    origin_url = payload.get("origin_url")
    if not origin_url:
        raise HTTPException(status_code=400, detail="origin_url is required")

    account_id = tenant["stripe_connect_account_id"]
    tier = await get_tenant_tier(customer.get("tenant_id"))
    fee_percent = get_platform_fee_percent(tier)
    amount = float(invoice.get("total", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid invoice amount")

    amount_cents = int(amount * 100)
    platform_fee_cents = int(amount_cents * fee_percent)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {
                        "name": f"Invoice #{invoice.get('invoice_number', invoice_id[:8])}",
                        "description": "Portal invoice payment"
                    }
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=f"{origin_url}/customer-portal/invoices?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin_url}/customer-portal/invoices?payment=cancelled",
            customer_email=customer.get("email"),
            payment_intent_data={
                "application_fee_amount": platform_fee_cents,
                "transfer_data": {"destination": account_id}
            },
            metadata={
                "type": "invoice",
                "invoice_id": invoice_id,
                "tenant_id": customer.get("tenant_id"),
                "portal_customer_id": customer.get("id"),
                "platform_fee_percent": str(fee_percent * 100)
            }
        )

        await db.payment_transactions.insert_one({
            "id": session.id,
            "tenant_id": customer.get("tenant_id"),
            "type": "invoice",
            "reference_id": invoice_id,
            "amount": amount,
            "platform_fee": platform_fee_cents / 100,
            "currency": "usd",
            "status": "pending",
            "stripe_session_id": session.id,
            "connected_account_id": account_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })

        return {"url": session.url, "session_id": session.id}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ============== PORTAL APPOINTMENTS ==============

@router.get("/appointments")
async def get_portal_appointments(
    status: Optional[str] = None,
    upcoming_only: bool = False,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get the customer's appointments (scheduled site surveys, installs, etc.)."""
    query: Dict[str, Any] = {"customer_id": customer["id"]}
    if customer.get("tenant_id"):
        query["tenant_id"] = customer["tenant_id"]
    if status:
        query["status"] = status
    if upcoming_only:
        today = datetime.now(timezone.utc).date().isoformat()
        query["scheduled_date"] = {"$gte": today}
        query.setdefault("status", {"$in": ["scheduled", "confirmed", "requested"]} if not status else status)

    appointments = await db.appointments.find(query, {"_id": 0}).sort("scheduled_start", 1).to_list(200)
    return appointments


class PortalAppointmentRequest(BaseModel):
    appointment_type: Optional[str] = None  # consultation, site_survey, pickup, install, other
    preferred_date: str  # ISO date YYYY-MM-DD
    preferred_time: Optional[str] = None  # e.g., "14:00" or "any"
    duration_minutes: Optional[int] = 60
    location: Optional[str] = None
    description: Optional[str] = None
    order_id: Optional[str] = None


@router.post("/appointments/request")
async def request_portal_appointment(
    payload: PortalAppointmentRequest,
    customer: dict = Depends(get_current_portal_customer)
):
    """Customer-initiated appointment request. Creates appointment with status='requested';
    admin must confirm via PUT /api/appointments/{id}/confirm to mark as scheduled."""
    if not payload.preferred_date:
        raise HTTPException(status_code=400, detail="preferred_date is required")

    now = datetime.now(timezone.utc).isoformat()
    scheduled_start = f"{payload.preferred_date}T{payload.preferred_time}:00" if payload.preferred_time and payload.preferred_time != "any" else f"{payload.preferred_date}T09:00:00"
    type_label_map = {
        "consultation": "Consultation",
        "site_survey": "Site Survey",
        "pickup": "Pickup",
        "install": "Installation",
        "installation": "Installation",
        "other": "Appointment",
    }
    title = f"{type_label_map.get(payload.appointment_type or 'other', 'Appointment')} Request"

    doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": customer.get("tenant_id"),
        "title": title,
        "status": "requested",
        "appointment_type": payload.appointment_type,
        "customer_id": customer["id"],
        "customer_name": customer.get("name"),
        "order_id": payload.order_id,
        "employee_id": None,
        "employee_name": None,
        "scheduled_start": scheduled_start,
        "scheduled_end": None,
        "scheduled_at": scheduled_start,
        "scheduled_date": payload.preferred_date,
        "duration_minutes": payload.duration_minutes or 60,
        "location": payload.location,
        "description": payload.description,
        "notes": "Customer-requested via portal",
        "send_reminder": True,
        "requested_by_customer": True,
        "created_by": customer["id"],
        "created_at": now,
        "updated_at": now,
    }
    await db.appointments.insert_one(doc)
    doc.pop("_id", None)

    # Notify shop staff (in-app)
    notification = CustomerNotification(
        tenant_id=customer.get("tenant_id"),
        customer_id=customer["id"],
        notification_type="appointment_requested",
        title="New appointment request",
        message=f"{customer.get('name', 'Customer')} requested a {payload.appointment_type or 'meeting'} on {payload.preferred_date}",
        related_id=doc["id"],
    )
    await db.customer_notifications.insert_one(notification.model_dump())

    # Email the shop owner so they don't miss the request
    try:
        from services.email_service import email_service
        tenant = await db.tenants.find_one({"id": customer.get("tenant_id")}, {"_id": 0})
        owner_email = (tenant or {}).get("owner_email")
        if owner_email and email_service.is_configured():
            type_pretty = (payload.appointment_type or "Appointment").replace("_", " ").title()
            customer_name = customer.get("name", "A customer")
            customer_email = customer.get("email", "")
            location_block = f"<p><strong>Location:</strong> {payload.location}</p>" if payload.location else ""
            description_block = f"<p><strong>Notes from customer:</strong><br/>{payload.description}</p>" if payload.description else ""
            html = f"""
            <h2>New Appointment Request</h2>
            <p><strong>{customer_name}</strong> just submitted a request through your customer portal.</p>
            <table style="margin: 16px 0; border-collapse: collapse;">
              <tr><td style="padding: 4px 12px;"><strong>Type</strong></td><td style="padding: 4px 12px;">{type_pretty}</td></tr>
              <tr><td style="padding: 4px 12px;"><strong>Preferred Date</strong></td><td style="padding: 4px 12px;">{payload.preferred_date}</td></tr>
              <tr><td style="padding: 4px 12px;"><strong>Preferred Time</strong></td><td style="padding: 4px 12px;">{payload.preferred_time or 'Any'}</td></tr>
              <tr><td style="padding: 4px 12px;"><strong>Duration</strong></td><td style="padding: 4px 12px;">{payload.duration_minutes or 60} minutes</td></tr>
              <tr><td style="padding: 4px 12px;"><strong>Customer Email</strong></td><td style="padding: 4px 12px;">{customer_email}</td></tr>
            </table>
            {location_block}
            {description_block}
            <p style="margin-top: 24px;">
              Confirm or reschedule from your <a href="{(tenant or {}).get('portal_url', '')}/appointments">Appointments dashboard</a>.
            </p>
            """
            await email_service.send_email(
                to_email=owner_email,
                subject=f"New appointment request from {customer_name}",
                html_content=html,
                tenant_id=customer.get("tenant_id"),
            )
    except Exception as exc:
        # Don't fail the request if email send fails
        logger.warning(f"Failed to send appointment-request email to shop owner: {exc}")

    return doc


# ============== PORTAL DOCUMENTS ==============

@router.get("/documents")
async def get_portal_documents(
    customer: dict = Depends(get_current_portal_customer)
):
    """Get all documents shared with the customer via portal"""
    portal_docs = await db.portal_documents.find(
        {"customer_id": customer["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with document info
    for portal_doc in portal_docs:
        doc = await db.documents.find_one(
            {"id": portal_doc.get("document_id")},
            {"_id": 0, "id": 1, "name": 1, "file_type": 1, "file_size": 1, "file_url": 1, "category": 1}
        )
        if doc:
            portal_doc["document"] = doc
    
    return portal_docs


@router.get("/documents/{document_id}")
async def get_portal_document_detail(
    document_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get a specific document shared with the customer"""
    portal_doc = await db.portal_documents.find_one(
        {"id": document_id, "customer_id": customer["id"]},
        {"_id": 0}
    )
    if not portal_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get full document info
    doc = await db.documents.find_one(
        {"id": portal_doc.get("document_id")},
        {"_id": 0}
    )
    if doc:
        portal_doc["document"] = doc
    
    # Mark as viewed
    if not portal_doc.get("viewed_at"):
        await db.portal_documents.update_one(
            {"id": document_id},
            {"$set": {"viewed_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return portal_doc


# ============== PORTAL FORMS / QUESTIONNAIRES ==============

@router.get("/forms")
async def get_portal_forms(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    requests = await db.portal_form_requests.find(query, {"_id": 0}).sort("sent_at", -1).to_list(200)
    return requests


@router.get("/forms/{request_id}")
async def get_portal_form_detail(
    request_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    form_request = await db.portal_form_requests.find_one({"id": request_id, "customer_id": customer["id"]}, {"_id": 0})
    if not form_request:
        raise HTTPException(status_code=404, detail="Form request not found")

    questionnaire = await db.questionnaires.find_one(
        {"id": form_request.get("questionnaire_id")},
        {"_id": 0, "tenant_id": 0, "created_by": 0}
    )
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")

    if not form_request.get("opened_at"):
        await db.portal_form_requests.update_one(
            {"id": request_id},
            {"$set": {"opened_at": datetime.now(timezone.utc).isoformat(), "status": "in_progress"}}
        )
        form_request["opened_at"] = datetime.now(timezone.utc).isoformat()
        form_request["status"] = "in_progress"

    existing_response = None
    if form_request.get("response_id"):
        existing_response = await db.questionnaire_responses.find_one({"id": form_request.get("response_id")}, {"_id": 0})

    return {
        "request": form_request,
        "questionnaire": questionnaire,
        "existing_response": existing_response,
    }


@router.post("/forms/{request_id}/submit")
async def submit_portal_form(
    request_id: str,
    payload: Dict[str, Any] = Body(...),
    customer: dict = Depends(get_current_portal_customer)
):
    form_request = await db.portal_form_requests.find_one({"id": request_id, "customer_id": customer["id"]}, {"_id": 0})
    if not form_request:
        raise HTTPException(status_code=404, detail="Form request not found")

    questionnaire = await db.questionnaires.find_one({"id": form_request.get("questionnaire_id")}, {"_id": 0})
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")

    answers = payload.get("answers", {})
    for question in questionnaire.get("questions", []):
        if question.get("required") and question.get("type") not in ["heading", "paragraph"]:
            question_id = question.get("id")
            answer = answers.get(question_id)
            if not answer or (isinstance(answer, list) and len(answer) == 0):
                raise HTTPException(status_code=400, detail=f"Required field missing: {question.get('label')}")

    now = datetime.now(timezone.utc).isoformat()
    response = QuestionnaireResponse(
        tenant_id=questionnaire["tenant_id"],
        questionnaire_id=questionnaire["id"],
        questionnaire_name=questionnaire["name"],
        answers=answers,
        job_id=form_request.get("job_id"),
        customer_id=customer["id"],
        customer_name=customer.get("name"),
        customer_email=customer.get("email"),
        submitted_at=now,
    )
    await db.questionnaire_responses.insert_one(response.model_dump())
    await db.questionnaires.update_one({"id": questionnaire["id"]}, {"$inc": {"response_count": 1}})

    rendered_text = format_form_response_document(questionnaire, answers, customer.get("name", "Customer"), now)
    document_id = str(uuid.uuid4())
    encoded_data = base64.b64encode(rendered_text.encode("utf-8")).decode("utf-8")
    document = {
        "id": document_id,
        "tenant_id": customer.get("tenant_id"),
        "name": f"{questionnaire.get('name')} Submission",
        "description": f"Portal form submission for {customer.get('name')}",
        "category": "customer_form",
        "file_type": "text/plain",
        "file_size": len(rendered_text.encode("utf-8")),
        "file_data": encoded_data,
        "original_filename": f"{questionnaire.get('name', 'form').replace(' ', '_').lower()}_submission.txt",
        "is_template": False,
        "tags": ["portal-form", "questionnaire-submission"],
        "linked_jobs": [form_request.get("job_id")] if form_request.get("job_id") else [],
        "linked_customers": [customer["id"]],
        "status": "active",
        "uploaded_by": customer["id"],
        "created_at": now,
        "updated_at": now,
    }
    await db.documents.insert_one(document)

    portal_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": customer.get("tenant_id"),
        "customer_id": customer["id"],
        "document_id": document_id,
        "document_name": document["name"],
        "document_category": "customer_form",
        "message": "Completed form submission",
        "status": "unread",
        "job_id": form_request.get("job_id"),
        "related_job_id": form_request.get("job_id"),
        "created_at": now,
        "created_by": customer["id"],
    }
    await db.portal_documents.insert_one(portal_doc)

    await db.portal_form_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "completed", "submitted_at": now, "response_id": response.id, "document_id": document_id}}
    )

    notification = CustomerNotification(
        tenant_id=customer.get("tenant_id"),
        customer_id=customer["id"],
        notification_type="form_submitted",
        title="Form submitted",
        message=f"{customer.get('name')} submitted {questionnaire.get('name')}",
        related_id=response.id,
    )
    await db.customer_notifications.insert_one(notification.model_dump())

    return {"message": questionnaire.get("thank_you_message", "Thank you for your submission!"), "response_id": response.id, "document_id": document_id}


@router.get("/invoices/{invoice_id}/download")
async def download_portal_invoice_pdf(
    invoice_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    invoice = await db.invoices.find_one({"id": invoice_id, "customer_id": customer["id"]}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Invoice #{invoice['id'][:8].upper()}", styles['Title']), Spacer(1, 12)]
    elements.append(Paragraph(f"Customer: {customer.get('name', 'Customer')}", styles['BodyText']))
    elements.append(Paragraph(f"Date: {invoice.get('created_at', '')[:10]}", styles['BodyText']))
    elements.append(Paragraph(f"Due: {invoice.get('due_date', 'N/A')}", styles['BodyText']))
    elements.append(Spacer(1, 12))
    table_data = [["Description", "Qty", "Unit Price", "Total"]]
    for item in invoice.get("line_items", []):
        table_data.append([item.get("description", "Item"), item.get("quantity", 1), f"${item.get('unit_price', 0):.2f}", f"${item.get('total', 0):.2f}"])
    table_data.append(["", "", "Total", f"${invoice.get('total', 0):.2f}"])
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)

    signature = await db.signatures.find_one(
        {
            "tenant_id": customer.get("tenant_id"),
            "parent_record_type": "invoice",
            "parent_record_id": invoice_id,
            "status": "signed",
            "signature_storage_path": {"$exists": True},
        },
        {"_id": 0}
    )
    if signature:
        try:
            image_bytes, _content_type = get_object(signature["signature_storage_path"])
            elements.append(Spacer(1, 18))
            elements.append(Paragraph("Authorized Signature", styles['Heading3']))
            elements.append(Spacer(1, 6))
            elements.append(ReportLabImage(BytesIO(image_bytes), width=180, height=72))
            elements.append(Spacer(1, 4))
            elements.append(Paragraph(f"Signed by: {signature.get('printed_name') or signature.get('signer_name')}", styles['BodyText']))
            elements.append(Paragraph(f"Type: {signature.get('signature_type', '').replace('_', ' ').title()}", styles['BodyText']))
            elements.append(Paragraph(f"Signed at: {signature.get('signed_at', '')}", styles['BodyText']))
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to render invoice signature block: {exc}")
    doc.build(elements)
    output.seek(0)
    return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=invoice_{invoice['id'][:8].upper()}.pdf"})



# ═══════════════════════════════════════════════════════════════════════════
# Phase 2F — Vehicle Wrap Project: customer actions
# ═══════════════════════════════════════════════════════════════════════════
#
# These endpoints let the customer-portal-authenticated customer act on a wrap
# job ticket inside their own order: approve artwork, request revision,
# acknowledge the contract, approve the quote, acknowledge the inspection
# report, and acknowledge aftercare. They reuse the existing portal JWT auth
# (`get_current_portal_customer`) and verify that the wrap ticket belongs to
# an order owned by the authenticated customer. NO new portal, NO new tokens.


async def _portal_load_wrap_ticket(customer: dict, job_id: str, ticket_id: str) -> dict:
    """Look up a wrap-category job_ticket and verify it belongs to an order
    owned by the customer. Raises 404/400 on failures.
    """
    from routes.wrap.core import _is_wrap_category  # local import

    tenant_id = customer.get("tenant_id")
    tenant_filter = {"tenant_id": tenant_id} if tenant_id else {}

    # Verify the order exists and belongs to this customer
    order = await db.orders.find_one(
        {"id": job_id, "customer_id": customer["id"], **tenant_filter},
        {"_id": 0, "id": 1},
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    ticket = await db.job_tickets.find_one(
        {"id": ticket_id, "order_id": job_id, **tenant_filter},
        {"_id": 0},
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Wrap item not found on this order")
    if not _is_wrap_category(ticket.get("item_category")):
        raise HTTPException(status_code=400, detail="This item is not a wrap")
    return ticket


def _customer_display_name(customer: dict) -> str:
    name = (customer.get("name") or "").strip()
    if name:
        return name
    bits = [customer.get("first_name"), customer.get("last_name")]
    full = " ".join(b for b in bits if b).strip()
    return full or customer.get("email") or "Customer"


async def _portal_set_wrap_approval(tenant_id: str, ticket_id: str, key: str, value: bool):
    """Mirror of wrap.core._set_approval but local to this module so we
    don't fight a circular import at module load time.
    """
    from routes.wrap.core import APPROVAL_KEYS  # local import
    if key not in APPROVAL_KEYS:
        return
    ts_key = f"{key}_at"
    updates: Dict[str, Any] = {f"approvals.{key}": bool(value)}
    now_iso = datetime.now(timezone.utc).isoformat()
    if value:
        # Idempotent: keep original timestamp if already true
        doc = await db.wrap_data.find_one(
            {"tenant_id": tenant_id, "ticket_id": ticket_id},
            {"_id": 0, "approvals": 1},
        ) or {}
        existing_ts = ((doc.get("approvals") or {}).get(ts_key))
        existing_val = bool(((doc.get("approvals") or {}).get(key)))
        if not (existing_val and existing_ts):
            updates[f"approvals.{ts_key}"] = now_iso
    else:
        updates[f"approvals.{ts_key}"] = None
    updates["updated_at"] = now_iso
    await db.wrap_data.update_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"$set": updates},
    )


class _PortalRevisionPayload(BaseModel):
    notes: Optional[str] = ""


class _PortalAckPayload(BaseModel):
    accepted_terms: Optional[bool] = True
    signed_by: Optional[str] = None


@router.post("/orders/{job_id}/wrap/{ticket_id}/approve-proof")
async def portal_wrap_approve_proof(
    job_id: str,
    ticket_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    ticket = await _portal_load_wrap_ticket(customer, job_id, ticket_id)
    tenant_id = customer.get("tenant_id")
    # Idempotency guard: only notify on the first transition to approved
    pre = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"_id": 0, "approvals.proof_approved": 1},
    ) or {}
    was_approved = bool(((pre.get("approvals") or {}).get("proof_approved")))

    now_iso = datetime.now(timezone.utc).isoformat()
    display_name = _customer_display_name(customer)
    await db.wrap_data.update_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"$set": {
            "design.proof_status": "approved",
            "design.proof_approved_at": now_iso,
            "design.proof_approved_by": display_name,
            "updated_at": now_iso,
        }},
    )
    await _portal_set_wrap_approval(tenant_id, ticket_id, "proof_approved", True)

    if not was_approved:
        from services.wrap_notifications import send_wrap_portal_action_notification
        await send_wrap_portal_action_notification(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            action_key="proof_approved",
            extra={"Approved by": display_name},
        )

    from routes.wrap.portal import build_customer_facing_summary
    return await build_customer_facing_summary(tenant_id, ticket_id, ticket)


@router.post("/orders/{job_id}/wrap/{ticket_id}/request-revision")
async def portal_wrap_request_revision(
    job_id: str,
    ticket_id: str,
    payload: _PortalRevisionPayload,
    customer: dict = Depends(get_current_portal_customer),
):
    ticket = await _portal_load_wrap_ticket(customer, job_id, ticket_id)
    tenant_id = customer.get("tenant_id")
    now_iso = datetime.now(timezone.utc).isoformat()
    display_name = _customer_display_name(customer)
    revision_note = {
        "id": str(uuid.uuid4()),
        "notes": (payload.notes or "").strip(),
        "requested_by": display_name,
        "requested_at": now_iso,
        "source": "customer_portal",
    }
    # Pipeline update normalises legacy design.revision_notes (some old docs
    # stored it as a string) into an array, then appends the revision note —
    # all in a single round trip.
    await db.wrap_data.update_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        [
            {
                "$set": {
                    "design.revision_notes": {
                        "$cond": [
                            {"$isArray": "$design.revision_notes"},
                            "$design.revision_notes",
                            [],
                        ]
                    }
                }
            },
            {
                "$set": {
                    "design.proof_status": "revision_requested",
                    "design.last_revision_requested_at": now_iso,
                    "design.last_revision_requested_by": display_name,
                    "design.revision_count": {
                        "$add": [{"$ifNull": ["$design.revision_count", 0]}, 1]
                    },
                    "design.revision_notes": {
                        "$concatArrays": ["$design.revision_notes", [revision_note]]
                    },
                    "updated_at": now_iso,
                }
            },
        ],
    )
    # Make sure proof_approved is cleared (idempotent)
    await _portal_set_wrap_approval(tenant_id, ticket_id, "proof_approved", False)

    # Revisions are intentionally NOT de-duped — every request has unique notes
    # and the shop should see each one.
    from services.wrap_notifications import send_wrap_portal_action_notification
    await send_wrap_portal_action_notification(
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        action_key="revision_requested",
        extra={
            "Requested by": display_name,
            "Notes": (payload.notes or "").strip()[:500] or "(no notes)",
        },
    )

    from routes.wrap.portal import build_customer_facing_summary
    return await build_customer_facing_summary(tenant_id, ticket_id, ticket)


@router.post("/orders/{job_id}/wrap/{ticket_id}/acknowledge-contract")
async def portal_wrap_acknowledge_contract(
    job_id: str,
    ticket_id: str,
    payload: _PortalAckPayload,
    customer: dict = Depends(get_current_portal_customer),
):
    ticket = await _portal_load_wrap_ticket(customer, job_id, ticket_id)
    tenant_id = customer.get("tenant_id")
    # Idempotency guard
    pre = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"_id": 0, "approvals.contract_signed": 1},
    ) or {}
    was_signed = bool(((pre.get("approvals") or {}).get("contract_signed")))

    now_iso = datetime.now(timezone.utc).isoformat()
    display_name = (payload.signed_by or "").strip() or _customer_display_name(customer)
    await db.wrap_data.update_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"$set": {
            "contract.contract_status": "signed",
            "contract.signed_at": now_iso,
            "contract.signed_by": display_name,
            "contract.accepted_terms": bool(payload.accepted_terms),
            "contract.signed_via": "customer_portal",
            "updated_at": now_iso,
        }},
    )
    await _portal_set_wrap_approval(tenant_id, ticket_id, "contract_signed", True)

    if not was_signed:
        from services.wrap_notifications import send_wrap_portal_action_notification
        await send_wrap_portal_action_notification(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            action_key="contract_signed",
            extra={"Signed by": display_name, "Accepted terms": "Yes" if payload.accepted_terms else "No"},
        )

    from routes.wrap.portal import build_customer_facing_summary
    return await build_customer_facing_summary(tenant_id, ticket_id, ticket)


@router.post("/orders/{job_id}/wrap/{ticket_id}/approve-quote")
async def portal_wrap_approve_quote(
    job_id: str,
    ticket_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    ticket = await _portal_load_wrap_ticket(customer, job_id, ticket_id)
    tenant_id = customer.get("tenant_id")
    pre = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"_id": 0, "approvals.quote_approved": 1},
    ) or {}
    was_approved = bool(((pre.get("approvals") or {}).get("quote_approved")))

    await _portal_set_wrap_approval(tenant_id, ticket_id, "quote_approved", True)

    if not was_approved:
        from services.wrap_notifications import send_wrap_portal_action_notification
        await send_wrap_portal_action_notification(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            action_key="quote_approved",
            extra={"Approved by": _customer_display_name(customer)},
        )

    from routes.wrap.portal import build_customer_facing_summary
    return await build_customer_facing_summary(tenant_id, ticket_id, ticket)


@router.post("/orders/{job_id}/wrap/{ticket_id}/acknowledge-inspection")
async def portal_wrap_acknowledge_inspection(
    job_id: str,
    ticket_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    ticket = await _portal_load_wrap_ticket(customer, job_id, ticket_id)
    tenant_id = customer.get("tenant_id")
    # Inspection ack is only allowed when the report has been marked
    # customer-visible by the shop. Otherwise reject — we don't want to
    # silently expose data the shop hasn't released.
    wrap_doc = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"_id": 0, "inspection": 1},
    ) or {}
    insp = wrap_doc.get("inspection") or {}
    if not insp.get("customer_visible"):
        raise HTTPException(
            status_code=400,
            detail="Inspection report has not been shared with you yet.",
        )
    was_acked = bool(insp.get("customer_acknowledged"))
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.wrap_data.update_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"$set": {
            "inspection.customer_acknowledged": True,
            "inspection.customer_acknowledged_at": now_iso,
            "inspection.inspection_status": "acknowledged",
            "updated_at": now_iso,
        }},
    )
    await _portal_set_wrap_approval(tenant_id, ticket_id, "inspection_acknowledged", True)

    if not was_acked:
        from services.wrap_notifications import send_wrap_portal_action_notification
        await send_wrap_portal_action_notification(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            action_key="inspection_acknowledged",
            extra={"Acknowledged by": _customer_display_name(customer)},
        )

    from routes.wrap.portal import build_customer_facing_summary
    return await build_customer_facing_summary(tenant_id, ticket_id, ticket)


@router.post("/orders/{job_id}/wrap/{ticket_id}/acknowledge-aftercare")
async def portal_wrap_acknowledge_aftercare(
    job_id: str,
    ticket_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    ticket = await _portal_load_wrap_ticket(customer, job_id, ticket_id)
    tenant_id = customer.get("tenant_id")
    now_iso = datetime.now(timezone.utc).isoformat()
    # Idempotent: do not overwrite an existing customer_acknowledged_at
    existing = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"_id": 0, "aftercare": 1},
    ) or {}
    was_acked = bool(((existing.get("aftercare") or {}).get("customer_acknowledged")))
    existing_ts = ((existing.get("aftercare") or {}).get("customer_acknowledged_at"))
    set_updates: Dict[str, Any] = {
        "aftercare.customer_acknowledged": True,
        "aftercare.customer_viewed": True,
        "updated_at": now_iso,
    }
    if not existing_ts:
        set_updates["aftercare.customer_acknowledged_at"] = now_iso
    existing_viewed_ts = ((existing.get("aftercare") or {}).get("customer_viewed_at"))
    if not existing_viewed_ts:
        set_updates["aftercare.customer_viewed_at"] = now_iso
    # Move aftercare status forward when it makes sense
    cur_status = ((existing.get("aftercare") or {}).get("aftercare_status")) or ""
    if cur_status in {"sent", "viewed", ""}:
        set_updates["aftercare.aftercare_status"] = "acknowledged"
    await db.wrap_data.update_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"$set": set_updates},
    )

    if not was_acked:
        from services.wrap_notifications import send_wrap_portal_action_notification
        await send_wrap_portal_action_notification(
            tenant_id=tenant_id,
            ticket_id=ticket_id,
            action_key="aftercare_acknowledged",
            extra={"Acknowledged by": _customer_display_name(customer)},
        )

    from routes.wrap.portal import build_customer_facing_summary
    return await build_customer_facing_summary(tenant_id, ticket_id, ticket)


@router.get("/orders/{job_id}/wrap/{ticket_id}/files/{file_id}/content")
async def portal_wrap_download_file(
    job_id: str,
    ticket_id: str,
    file_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    """Download a single customer_visible wrap file. Enforces order
    ownership + customer_visible flag."""
    import mimetypes as _mimetypes  # local to avoid touching top-level imports
    from fastapi.responses import Response as FastAPIResponse

    await _portal_load_wrap_ticket(customer, job_id, ticket_id)
    file_doc = await db.wrap_files.find_one(
        {
            "id": file_id,
            "ticket_id": ticket_id,
            "tenant_id": customer.get("tenant_id"),
            "customer_visible": True,
        },
        {"_id": 0},
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not available")
    media_type = (
        file_doc.get("content_type")
        or _mimetypes.guess_type(file_doc.get("filename", ""))[0]
        or "application/octet-stream"
    )
    storage_path = file_doc.get("storage_path")
    if not storage_path:
        raise HTTPException(status_code=404, detail="File not available")
    try:
        content, content_type = get_object(storage_path)
        media_type = content_type or media_type
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Failed to load file") from exc
    return FastAPIResponse(content=content, media_type=media_type)


# ═══════════════════════════════════════════════════════════════════════════
# Customer Portal — Webstores tab
# ═══════════════════════════════════════════════════════════════════════════
#
# Lets customer-portal users (db.customers) who are also assigned as the
# owner of one or more webstores see their stores from inside the existing
# customer portal. NO new portal, NO new auth — reuses the portal JWT and
# the existing webstore_owners.py Stripe onboarding flow.
#
# Assignment rule: a webstore is considered owned by the customer when
#   webstore.owner_email (case-insensitive) == customer.email
# AND webstore.tenant_id == customer.tenant_id.
#
# Sanitization: never expose tenant_id, raw locked_settings cost/profit, or
# any field the store owner is not allowed to edit. Shipping/handling is
# safe to surface read-only (it's already public on the storefront).


def _sanitize_webstore_for_portal_owner(ws: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce a webstore doc to what the customer-portal Webstores tab can show.

    - Includes safe summary + fundraiser totals + event fields + Stripe state.
    - Excludes tenant_id, raw locked_settings cost/profit, owner_user_id, and
      anything that would let the store owner bypass tenant admin controls.
    """
    if not isinstance(ws, dict):
        return {}

    locked = ws.get("locked_settings") or {}
    # Only the shipping/handling subset is exposed read-only.
    locked_public = {
        "shipping_fee": locked.get("shipping_fee"),
        "handling_fee": locked.get("handling_fee"),
        "shipping_handling_enabled": bool(locked.get("shipping_handling_enabled")),
        "shipping_handling_fee": locked.get("shipping_handling_fee"),
        "shipping_handling_label": locked.get("shipping_handling_label"),
        "shipping_handling_description": locked.get("shipping_handling_description"),
    }

    branding_raw = ws.get("branding") if isinstance(ws.get("branding"), dict) else {}
    branding = {
        "logo_url": branding_raw.get("logo_url") or ws.get("logo_url"),
        "primary_color": branding_raw.get("primary_color") or "#0D9488",
        "banner_url": branding_raw.get("banner_url") or ws.get("banner_url"),
    }

    return {
        # Identity / display
        "id": ws.get("id"),
        "name": ws.get("name"),
        "store_type": ws.get("store_type"),
        "status": ws.get("status"),
        "store_slug": ws.get("store_slug"),
        "description": ws.get("description"),
        "owner_name": ws.get("owner_name"),
        "owner_email": ws.get("owner_email"),
        "branding": branding,
        "is_public": bool(ws.get("is_public", True)),
        # Event-store fields (safe — already public on the storefront)
        "event_name": ws.get("event_name"),
        "event_type": ws.get("event_type"),
        "event_start_date": ws.get("event_start_date"),
        "event_end_date": ws.get("event_end_date"),
        "event_location": ws.get("event_location"),
        "order_deadline": ws.get("order_deadline"),
        "pickup_delivery_date": ws.get("pickup_delivery_date"),
        "pickup_delivery_instructions": ws.get("pickup_delivery_instructions"),
        "auto_close_after_deadline": bool(ws.get("auto_close_after_deadline")),
        "allow_late_orders": bool(ws.get("allow_late_orders")),
        # Fundraiser config (read-only on the portal — tenant controls these)
        "fundraiser_enabled": bool(ws.get("fundraiser_enabled")),
        "fundraiser_name": ws.get("fundraiser_name"),
        "fundraiser_description": ws.get("fundraiser_description"),
        "fundraiser_goal_amount": ws.get("fundraiser_goal_amount"),
        "show_progress_bar": bool(ws.get("show_progress_bar")),
        "allow_checkout_donations": bool(ws.get("allow_checkout_donations")),
        "allow_custom_donation": bool(ws.get("allow_custom_donation")),
        "donation_amount_options": ws.get("donation_amount_options"),
        # Fundraiser running totals (the whole point of the portal tab)
        "total_donations": float(ws.get("total_donations") or 0),
        "total_profit_allocated": float(ws.get("total_profit_allocated") or 0),
        "total_raised": float(ws.get("total_raised") or 0),
        "manual_adjustments": float(ws.get("manual_adjustments") or 0),
        # Sales summary — basic, owner-safe
        "total_sales": float(ws.get("total_sales") or 0),
        "total_orders": int(ws.get("total_orders") or 0),
        "payout_owed": float(ws.get("payout_owed") or 0),
        "payout_paid": float(ws.get("payout_paid") or 0),
        # Stripe Express onboarding (owner-side)
        "owner_stripe_account_id": ws.get("owner_stripe_account_id"),
        "owner_stripe_charges_enabled": bool(ws.get("owner_stripe_charges_enabled")),
        "owner_stripe_payouts_enabled": bool(ws.get("owner_stripe_payouts_enabled")),
        "owner_stripe_details_submitted": bool(ws.get("owner_stripe_details_submitted")),
        # Read-only locked subset (shipping/handling only)
        "locked_settings": locked_public,
        # Timestamps
        "created_at": ws.get("created_at"),
        "updated_at": ws.get("updated_at"),
    }


async def _portal_load_assigned_webstore(customer: Dict[str, Any], webstore_id: str) -> Dict[str, Any]:
    """Fetch a webstore doc only if the customer is assigned to it.

    Assignment: webstore.owner_email (case-insensitive) matches the
    customer's email AND tenant_id matches. Raises 404 otherwise so we
    never leak existence of stores the customer doesn't own.
    """
    email = (customer.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=404, detail="Webstore not found")
    query: Dict[str, Any] = {"id": webstore_id, "owner_email": email}
    if customer.get("tenant_id"):
        query["tenant_id"] = customer["tenant_id"]
    ws = await db.webstores_v2.find_one(query, {"_id": 0})
    if not ws:
        # Try a case-insensitive match if the stored email isn't normalized.
        import re as _re
        ws = await db.webstores_v2.find_one(
            {
                "id": webstore_id,
                "owner_email": {"$regex": f"^{_re.escape(email)}$", "$options": "i"},
                **({"tenant_id": customer["tenant_id"]} if customer.get("tenant_id") else {}),
            },
            {"_id": 0},
        )
    if not ws:
        raise HTTPException(status_code=404, detail="Webstore not found")
    return ws


async def _portal_list_assigned_webstores(customer: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return all webstores assigned to this customer-portal user."""
    email = (customer.get("email") or "").strip().lower()
    if not email:
        return []
    import re as _re
    query: Dict[str, Any] = {
        "owner_email": {"$regex": f"^{_re.escape(email)}$", "$options": "i"},
    }
    if customer.get("tenant_id"):
        query["tenant_id"] = customer["tenant_id"]
    rows = await db.webstores_v2.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return rows


@router.get("/webstores")
async def list_portal_webstores(customer: dict = Depends(get_current_portal_customer)):
    """List webstores assigned to the current customer-portal user."""
    rows = await _portal_list_assigned_webstores(customer)
    # Polish: one-time notification per assignment, dismissible.
    # Idempotent — duplicate calls only insert when the row is missing.
    await _ensure_webstore_assignment_notifications(customer, rows)
    return [_sanitize_webstore_for_portal_owner(r) for r in rows]


async def _ensure_webstore_assignment_notifications(
    customer: Dict[str, Any],
    webstores: List[Dict[str, Any]],
) -> None:
    """For each assigned webstore, ensure a one-time `webstore_assigned`
    notification exists for this customer. Idempotent — uses
    (customer_id, notification_type, related_id) as the dedup key.
    """
    if not customer or not customer.get("id") or not webstores:
        return
    customer_id = customer["id"]
    for ws in webstores:
        ws_id = ws.get("id")
        if not ws_id:
            continue
        # Skip if a notification already exists for this assignment.
        existing = await db.customer_notifications.find_one(
            {
                "customer_id": customer_id,
                "notification_type": "webstore_assigned",
                "related_id": ws_id,
            },
            {"_id": 0, "id": 1},
        )
        if existing:
            continue
        store_name = ws.get("name") or "your store"
        cta_link = "/customer-portal/webstores"
        stripe_ready = bool(ws.get("owner_stripe_charges_enabled"))
        message = (
            f"You've been assigned as the owner of {store_name}. "
            + ("Visit the Webstores tab to manage your store."
               if stripe_ready
               else "Complete Stripe onboarding to start receiving payouts.")
        )
        notification = CustomerNotification(
            tenant_id=customer.get("tenant_id") or ws.get("tenant_id"),
            customer_id=customer_id,
            notification_type="webstore_assigned",
            title="New webstore assignment",
            message=message,
            link=cta_link,
            related_id=ws_id,
        )
        try:
            await db.customer_notifications.insert_one(notification.model_dump())
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Failed to seed webstore_assigned notification: {exc}")


@router.get("/notifications")
async def list_portal_notifications(
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer),
):
    """List portal notifications for the current customer.

    Filters:
      - unread_only=true → only is_read=false rows
      - notification_type → exact match (e.g., "webstore_assigned")
    """
    query: Dict[str, Any] = {"customer_id": customer["id"]}
    if unread_only:
        query["is_read"] = False
    if notification_type:
        query["notification_type"] = notification_type
    rows = await db.customer_notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return rows


@router.post("/notifications/{notification_id}/dismiss")
async def dismiss_portal_notification(
    notification_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    """Mark a single notification as read (dismissible by the customer).

    Returns 404 (not 403) if the notification doesn't belong to the
    customer — keeps notification existence private.
    """
    res = await db.customer_notifications.update_one(
        {"id": notification_id, "customer_id": customer["id"]},
        {"$set": {"is_read": True, "dismissed_at": datetime.now(timezone.utc).isoformat()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"ok": True, "id": notification_id}


@router.post("/notifications/dismiss-all")
async def dismiss_all_portal_notifications(
    notification_type: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer),
):
    """Bulk-dismiss notifications (optionally filtered by type)."""
    q: Dict[str, Any] = {"customer_id": customer["id"], "is_read": False}
    if notification_type:
        q["notification_type"] = notification_type
    res = await db.customer_notifications.update_many(
        q,
        {"$set": {"is_read": True, "dismissed_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"ok": True, "dismissed": res.modified_count}


@router.get("/webstores/{webstore_id}")
async def get_portal_webstore_detail(
    webstore_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    """Full sanitized detail for one assigned webstore, plus recent orders
    and questionnaire status (Event Stores)."""
    ws = await _portal_load_assigned_webstore(customer, webstore_id)
    sanitized = _sanitize_webstore_for_portal_owner(ws)

    # Public storefront URL (frontend builds the full link).
    sanitized["public_path"] = f"/store/{ws['id']}"

    # Recent orders for this webstore (basic count + last 10 entries).
    recent_orders_cursor = db.webstore_orders_v2.find(
        {"webstore_id": webstore_id},
        {
            "_id": 0,
            "id": 1, "customer_name": 1, "customer_email": 1,
            "subtotal": 1, "donation_amount": 1, "profit_allocation_amount": 1,
            "shipping_handling_amount": 1, "grand_total": 1, "commission_amount": 1,
            "status": 1, "created_at": 1, "stripe_session_id": 1,
        },
    ).sort("created_at", -1).limit(10)
    recent_orders = await recent_orders_cursor.to_list(10)
    sanitized["recent_orders"] = recent_orders

    # Questionnaire status (Event Stores only, but cheap to include).
    questionnaire = await db.questionnaires.find_one(
        {"webstore_id": webstore_id},
        {"_id": 0, "id": 1, "name": 1, "status": 1, "response_count": 1,
         "last_sent_at": 1, "updated_at": 1},
    )
    latest_response = None
    if questionnaire:
        latest_response = await db.questionnaire_responses.find_one(
            {"questionnaire_id": questionnaire["id"]},
            {"_id": 0, "id": 1, "submitted_at": 1, "customer_name": 1,
             "applied_to_webstore": 1},
            sort=[("submitted_at", -1)],
        )
    sanitized["questionnaire"] = {
        "linked": bool(questionnaire),
        "questionnaire": questionnaire,
        "latest_response": latest_response,
    }

    return sanitized


class _PortalStripeOnboardRequest(BaseModel):
    return_url: str
    refresh_url: str


@router.post("/webstores/{webstore_id}/stripe-onboarding")
async def start_portal_webstore_stripe_onboarding(
    webstore_id: str,
    body: _PortalStripeOnboardRequest,
    customer: dict = Depends(get_current_portal_customer),
):
    """Reuse the webstore_owners Stripe Express onboarding flow from inside
    the customer portal. Creates an Express account if needed and returns
    a fresh AccountLink URL the owner can use to complete onboarding.
    """
    ws = await _portal_load_assigned_webstore(customer, webstore_id)

    # Lazy import — avoids circular deps and reuses the canonical Stripe code.
    import stripe as _stripe
    _stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY")

    account_id = ws.get("owner_stripe_account_id")
    try:
        if not account_id:
            account = _stripe.Account.create(
                type="express",
                email=ws.get("owner_email") or customer.get("email"),
                capabilities={
                    "transfers": {"requested": True},
                    "card_payments": {"requested": True},
                },
                metadata={
                    "signguy_webstore_id": ws["id"],
                    "signguy_tenant_id": ws.get("tenant_id") or "",
                    "signguy_source": "customer_portal",
                },
            )
            account_id = account.id
            await db.webstores_v2.update_one(
                {"id": ws["id"]},
                {"$set": {
                    "owner_stripe_account_id": account_id,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }},
            )

        link = _stripe.AccountLink.create(
            account=account_id,
            return_url=body.return_url,
            refresh_url=body.refresh_url,
            type="account_onboarding",
        )
        return {"url": link.url, "account_id": account_id}
    except _stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/webstores/{webstore_id}/stripe-refresh")
async def refresh_portal_webstore_stripe_status(
    webstore_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    """Pull the latest charges_enabled/payouts_enabled/details_submitted from
    Stripe and update the webstore doc. Returns the refreshed flags."""
    ws = await _portal_load_assigned_webstore(customer, webstore_id)
    account_id = ws.get("owner_stripe_account_id")
    if not account_id:
        return {
            "ready": False,
            "charges_enabled": False,
            "payouts_enabled": False,
            "details_submitted": False,
        }

    import stripe as _stripe
    _stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY")
    try:
        account = _stripe.Account.retrieve(account_id)
    except _stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    flags = {
        "owner_stripe_account_id": account_id,
        "owner_stripe_charges_enabled": bool(account.charges_enabled),
        "owner_stripe_payouts_enabled": bool(account.payouts_enabled),
        "owner_stripe_details_submitted": bool(account.details_submitted),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.webstores_v2.update_one({"id": ws["id"]}, {"$set": flags})
    return {
        "ready": flags["owner_stripe_charges_enabled"],
        "charges_enabled": flags["owner_stripe_charges_enabled"],
        "payouts_enabled": flags["owner_stripe_payouts_enabled"],
        "details_submitted": flags["owner_stripe_details_submitted"],
    }


@router.post("/webstores/{webstore_id}/stripe-login-link")
async def portal_webstore_stripe_login_link(
    webstore_id: str,
    customer: dict = Depends(get_current_portal_customer),
):
    """One-time Stripe Express dashboard link for the assigned store owner."""
    ws = await _portal_load_assigned_webstore(customer, webstore_id)
    if not ws.get("owner_stripe_account_id"):
        raise HTTPException(status_code=400, detail="Stripe onboarding not started yet")
    import stripe as _stripe
    _stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY")
    try:
        link = _stripe.Account.create_login_link(ws["owner_stripe_account_id"])
        return {"url": link.url}
    except _stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

