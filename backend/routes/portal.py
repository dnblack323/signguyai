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
import jwt
import uuid
import base64
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
            "paid_invoices": len([inv for inv in combined_invoices if inv.get("status") == "paid"])
        },
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

