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

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import jwt

from models import (
    Conversation, ConversationMessage, MessageType,
    ArtworkProof, ProofStatus,
    CustomerNotification,
    CustomerPortalLogin, CustomerPortalRegister, CustomerPortalToken,
    CustomerProfileUpdate, ConversationCreate, MessageCreate, ProofResponseCreate
)

# Import from server module
from server import (
    db, logger, security,
    SECRET_KEY, ALGORITHM,
    get_password_hash, verify_password, create_access_token
)

router = APIRouter(prefix="/portal", tags=["Customer Portal"])


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
    
    # Get counts
    total_quotes = await db.quotes.count_documents({"customer_id": customer_id})
    active_jobs = await db.jobs.count_documents({"customer_id": customer_id, "status": {"$nin": ["complete", "archived"]}})
    pending_invoices = await db.invoices.count_documents({"customer_id": customer_id, "status": {"$in": ["sent", "draft"]}})
    pending_proofs = await db.artwork_proofs.count_documents({"customer_id": customer_id, "status": "pending"})
    
    # Get unread message count
    conversations = await db.conversations.find({"customer_id": customer_id}, {"_id": 0}).to_list(100)
    unread_messages = sum(c.get("unread_customer", 0) for c in conversations)
    
    # Get unread notifications
    unread_notifications = await db.customer_notifications.count_documents({"customer_id": customer_id, "is_read": False})
    
    # Get upcoming appointments
    today = datetime.now(timezone.utc).date().isoformat()
    upcoming_appointments = await db.appointments.find(
        {"customer_id": customer_id, "scheduled_date": {"$gte": today}, "status": {"$in": ["scheduled", "confirmed"]}},
        {"_id": 0}
    ).sort("scheduled_date", 1).limit(5).to_list(5)
    
    # Get recent jobs
    recent_jobs = await db.jobs.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Get recent invoices
    recent_invoices = await db.invoices.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "stats": {
            "total_quotes": total_quotes,
            "active_jobs": active_jobs,
            "pending_invoices": pending_invoices,
            "pending_proofs": pending_proofs,
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications
        },
        "upcoming_appointments": upcoming_appointments,
        "recent_jobs": recent_jobs,
        "recent_invoices": recent_invoices
    }


# ============== PORTAL ORDERS/JOBS ==============

@router.get("/orders")
async def get_portal_orders(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's orders (jobs)"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Enrich with items
    for job in jobs:
        items = await db.job_items.find({"job_id": job["id"]}, {"_id": 0}).to_list(50)
        job["items"] = items
    
    return jobs


@router.get("/orders/{job_id}")
async def get_portal_order_detail(
    job_id: str,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get single order detail"""
    job = await db.jobs.find_one({"id": job_id, "customer_id": customer["id"]}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get items
    items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(50)
    job["items"] = items
    
    # Get associated quote if any
    if job.get("quote_id"):
        quote = await db.quotes.find_one({"id": job["quote_id"]}, {"_id": 0})
        job["quote"] = quote
    
    # Get associated invoice if any
    if job.get("invoice_id"):
        invoice = await db.invoices.find_one({"id": job["invoice_id"]}, {"_id": 0})
        job["invoice"] = invoice
    
    # Get artwork proofs
    proofs = await db.artwork_proofs.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(20)
    job["proofs"] = proofs
    
    return job


# ============== PORTAL QUOTES ==============

@router.get("/quotes")
async def get_portal_quotes(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's quotes"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    quotes = await db.quotes.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return quotes


# ============== PORTAL INVOICES ==============

@router.get("/invoices")
async def get_portal_invoices(
    status: Optional[str] = None,
    customer: dict = Depends(get_current_portal_customer)
):
    """Get customer's invoices"""
    query = {"customer_id": customer["id"]}
    if status:
        query["status"] = status
    
    invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return invoices


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
    
    # Create message
    message = ConversationMessage(
        conversation_id=conversation_id,
        sender_type="customer",
        sender_id=customer["id"],
        sender_name=customer["name"],
        content=input.content,
        message_type=MessageType.TEXT
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    # Update conversation
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {
            "last_message_at": datetime.now(timezone.utc).isoformat(),
            "last_message_preview": input.content[:100]
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
    proof["job"] = job
    
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
