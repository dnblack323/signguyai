"""
Admin Portal Routes

This module contains routes for the admin-side communication hub:
- View all customer conversations across the tenant
- Send messages to customers
- Share documents with customers
- Manage artwork approvals
- Send artwork for customer approval
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid

from models import (
    UserInDB, Conversation, ConversationMessage, MessageType,
    CustomerNotification, ArtworkProof, ProofStatus
)


router = APIRouter(prefix="/admin-portal", tags=["Admin Portal"])

# Import db and auth after router definition to avoid circular imports
from core_runtime import db, get_current_active_user, logger


# ============== MODELS ==============

class AdminMessageCreate(BaseModel):
    customer_id: str
    subject: Optional[str] = None
    content: str
    conversation_id: Optional[str] = None  # If replying to existing conversation
    related_job_id: Optional[str] = None
    related_quote_id: Optional[str] = None


class DocumentShareCreate(BaseModel):
    customer_id: str
    document_id: str
    message: Optional[str] = None
    requires_acknowledgment: bool = False


class BulkDocumentShareCreate(BaseModel):
    customer_ids: List[str]
    document_id: str
    message: Optional[str] = None


class ArtworkSendCreate(BaseModel):
    job_id: str
    customer_id: str
    file_url: str
    file_name: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    watermarked_url: Optional[str] = None


class PortalFormSendCreate(BaseModel):
    customer_id: str
    questionnaire_id: str
    job_id: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[str] = None


# ============== DASHBOARD ==============

@router.get("/dashboard")
async def get_admin_portal_dashboard(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get admin portal dashboard stats.
    Returns counts for messages, pending approvals, shared documents.
    """
    tenant_id = current_user.tenant_id
    
    # Unread messages from customers (unread_shop > 0)
    unread_conversations = await db.conversations.count_documents({
        "tenant_id": tenant_id,
        "unread_shop": {"$gt": 0}
    })
    
    # Total active conversations
    total_conversations = await db.conversations.count_documents({
        "tenant_id": tenant_id,
        "is_closed": {"$ne": True}
    })
    
    # Pending artwork approvals
    pending_approvals = await db.artwork_proofs.count_documents({
        "tenant_id": tenant_id,
        "status": "pending"
    })
    
    # Revision requested approvals
    revision_requested = await db.artwork_proofs.count_documents({
        "tenant_id": tenant_id,
        "status": "revision_requested"
    })
    
    # Recently approved (last 7 days)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_approved = await db.artwork_proofs.count_documents({
        "tenant_id": tenant_id,
        "status": "approved",
        "approved_at": {"$gte": week_ago}
    })
    
    # Documents shared via portal
    shared_documents = await db.portal_documents.count_documents({
        "tenant_id": tenant_id
    })
    
    # Unviewed documents
    unviewed_documents = await db.portal_documents.count_documents({
        "tenant_id": tenant_id,
        "viewed_at": None
    })

    pending_forms = await db.portal_form_requests.count_documents({
        "tenant_id": tenant_id,
        "status": {"$in": ["pending", "in_progress", "overdue"]}
    })

    recent_form_submissions = await db.portal_form_requests.count_documents({
        "tenant_id": tenant_id,
        "status": "completed",
        "submitted_at": {"$gte": week_ago}
    })
    
    return {
        "messages": {
            "unread": unread_conversations,
            "total_active": total_conversations
        },
        "approvals": {
            "pending": pending_approvals,
            "revision_requested": revision_requested,
            "recent_approved": recent_approved
        },
        "documents": {
            "total_shared": shared_documents,
            "unviewed": unviewed_documents
        },
        "forms": {
            "pending": pending_forms,
            "recent_submissions": recent_form_submissions
        }
    }


# ============== CONVERSATIONS/MESSAGES ==============

@router.get("/conversations")
async def get_all_conversations(
    customer_id: Optional[str] = None,
    unread_only: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get all conversations across all customers for the tenant.
    Admin can see everything and respond to any customer.
    """
    tenant_id = current_user.tenant_id
    query = {"tenant_id": tenant_id}
    
    if customer_id:
        query["customer_id"] = customer_id
    if unread_only:
        query["unread_shop"] = {"$gt": 0}
    
    conversations = await db.conversations.find(
        query, {"_id": 0}
    ).sort("last_message_at", -1).to_list(500)
    
    # Enrich with customer info
    for conv in conversations:
        customer = await db.customers.find_one(
            {"id": conv.get("customer_id")},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1}
        )
        conv["customer"] = customer
        
        # Get related job/quote names if any
        if conv.get("related_job_id"):
            job = await db.jobs.find_one(
                {"id": conv["related_job_id"]},
                {"_id": 0, "name": 1}
            )
            conv["related_job_name"] = job.get("name") if job else None
    
    return conversations


@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific conversation with all messages."""
    tenant_id = current_user.tenant_id
    
    conv = await db.conversations.find_one(
        {"id": conversation_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get customer info
    customer = await db.customers.find_one(
        {"id": conv.get("customer_id")},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1, "phone": 1}
    )
    conv["customer"] = customer
    
    # Get all messages
    messages = await db.conversation_messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(1000)
    
    # Mark shop's unread as read
    await db.conversation_messages.update_many(
        {"conversation_id": conversation_id, "sender_type": "customer", "is_read": False},
        {"$set": {"is_read": True}}
    )
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": {"unread_shop": 0}}
    )
    
    return {
        "conversation": conv,
        "messages": messages
    }


@router.post("/conversations")
async def create_conversation_to_customer(
    input: AdminMessageCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Start a new conversation with a customer or reply to existing.
    This is the shop initiating contact.
    """
    tenant_id = current_user.tenant_id
    
    # Verify customer exists
    customer = await db.customers.find_one(
        {"id": input.customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # If conversation_id provided, add to existing conversation
    if input.conversation_id:
        conv = await db.conversations.find_one(
            {"id": input.conversation_id, "tenant_id": tenant_id},
            {"_id": 0}
        )
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Create message
        message = ConversationMessage(
            conversation_id=input.conversation_id,
            sender_type="shop",
            sender_id=current_user.id,
            sender_name=current_user.full_name or current_user.email,
            content=input.content,
            message_type=MessageType.TEXT
        )
        await db.conversation_messages.insert_one(message.model_dump())
        
        # Update conversation
        await db.conversations.update_one(
            {"id": input.conversation_id},
            {
                "$set": {
                    "last_message_at": datetime.now(timezone.utc).isoformat(),
                    "last_message_preview": input.content[:100]
                },
                "$inc": {"unread_customer": 1}
            }
        )
        
        return {"message": "Message sent", "conversation_id": input.conversation_id, "message_id": message.id}
    
    # Create new conversation
    subject = input.subject or f"Message from {current_user.full_name or 'Sign Shop'}"
    
    conversation = Conversation(
        customer_id=input.customer_id,
        tenant_id=tenant_id,
        subject=subject,
        related_job_id=input.related_job_id,
        related_quote_id=input.related_quote_id,
        last_message_preview=input.content[:100],
        unread_customer=1,
        unread_shop=0
    )
    await db.conversations.insert_one(conversation.model_dump())
    
    # Create first message
    message = ConversationMessage(
        conversation_id=conversation.id,
        sender_type="shop",
        sender_id=current_user.id,
        sender_name=current_user.full_name or current_user.email,
        content=input.content,
        message_type=MessageType.TEXT
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    # Create notification for customer
    notification = CustomerNotification(
        tenant_id=tenant_id,
        customer_id=input.customer_id,
        notification_type="message",
        title="New Message",
        message=f"You have a new message: {subject}",
        related_id=conversation.id
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    logger.info(f"Admin {current_user.email} started conversation with customer {input.customer_id}")
    
    return {
        "message": "Conversation started",
        "conversation_id": conversation.id,
        "message_id": message.id
    }


@router.post("/conversations/{conversation_id}/messages")
async def send_message_in_conversation(
    conversation_id: str,
    content: str,
    file_url: Optional[str] = None,
    file_name: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Send a message in an existing conversation."""
    tenant_id = current_user.tenant_id
    
    conv = await db.conversations.find_one(
        {"id": conversation_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Determine message type
    msg_type = MessageType.FILE if file_url else MessageType.TEXT
    
    message = ConversationMessage(
        conversation_id=conversation_id,
        sender_type="shop",
        sender_id=current_user.id,
        sender_name=current_user.full_name or current_user.email,
        content=content,
        message_type=msg_type,
        file_url=file_url,
        file_name=file_name
    )
    await db.conversation_messages.insert_one(message.model_dump())
    
    # Update conversation
    preview = f"[File] {file_name}" if file_url else content[:100]
    await db.conversations.update_one(
        {"id": conversation_id},
        {
            "$set": {
                "last_message_at": datetime.now(timezone.utc).isoformat(),
                "last_message_preview": preview
            },
            "$inc": {"unread_customer": 1}
        }
    )
    
    return message.model_dump()


@router.put("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Close a conversation."""
    result = await db.conversations.update_one(
        {"id": conversation_id, "tenant_id": current_user.tenant_id},
        {"$set": {"is_closed": True, "closed_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation closed"}


@router.put("/conversations/{conversation_id}/reopen")
async def reopen_conversation(
    conversation_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Reopen a closed conversation."""
    result = await db.conversations.update_one(
        {"id": conversation_id, "tenant_id": current_user.tenant_id},
        {"$set": {"is_closed": False}, "$unset": {"closed_at": ""}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation reopened"}


# ============== DOCUMENT SHARING ==============

@router.get("/documents")
async def get_all_shared_documents(
    customer_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all documents shared via portal."""
    tenant_id = current_user.tenant_id
    query = {"tenant_id": tenant_id}
    
    if customer_id:
        query["customer_id"] = customer_id
    
    portal_docs = await db.portal_documents.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    # Enrich with document and customer info
    for pdoc in portal_docs:
        doc = await db.documents.find_one(
            {"id": pdoc.get("document_id")},
            {"_id": 0, "id": 1, "name": 1, "file_type": 1, "file_url": 1, "category": 1}
        )
        pdoc["document"] = doc
        
        customer = await db.customers.find_one(
            {"id": pdoc.get("customer_id")},
            {"_id": 0, "id": 1, "name": 1}
        )
        pdoc["customer"] = customer
    
    return portal_docs


@router.post("/documents/share")
async def share_document_with_customer(
    input: DocumentShareCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Share a document with a customer via the portal."""
    tenant_id = current_user.tenant_id
    
    # Verify customer
    customer = await db.customers.find_one(
        {"id": input.customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify document
    document = await db.documents.find_one(
        {"id": input.document_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Create portal document entry
    portal_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "customer_id": input.customer_id,
        "document_id": input.document_id,
        "shared_by": current_user.id,
        "shared_by_name": current_user.full_name or current_user.email,
        "message": input.message,
        "requires_acknowledgment": input.requires_acknowledgment,
        "acknowledged_at": None,
        "viewed_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.portal_documents.insert_one(portal_doc)
    
    # Create notification for customer
    notification = CustomerNotification(
        tenant_id=tenant_id,
        customer_id=input.customer_id,
        notification_type="document",
        title="New Document Shared",
        message=f"A new document '{document.get('name')}' has been shared with you.",
        related_id=portal_doc["id"]
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    logger.info(f"Document {input.document_id} shared with customer {input.customer_id}")
    
    return {"message": "Document shared", "portal_document_id": portal_doc["id"]}


@router.post("/documents/share-bulk")
async def share_document_with_multiple_customers(
    input: BulkDocumentShareCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Share a document with multiple customers."""
    tenant_id = current_user.tenant_id
    
    # Verify document
    document = await db.documents.find_one(
        {"id": input.document_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    shared_count = 0
    for customer_id in input.customer_ids:
        # Verify customer
        customer = await db.customers.find_one(
            {"id": customer_id, "tenant_id": tenant_id},
            {"_id": 0}
        )
        if not customer:
            continue
        
        # Create portal document entry
        portal_doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "document_id": input.document_id,
            "shared_by": current_user.id,
            "shared_by_name": current_user.full_name or current_user.email,
            "message": input.message,
            "requires_acknowledgment": False,
            "acknowledged_at": None,
            "viewed_at": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.portal_documents.insert_one(portal_doc)
        
        # Create notification
        notification = CustomerNotification(
            tenant_id=tenant_id,
            customer_id=customer_id,
            notification_type="document",
            title="New Document Shared",
            message=f"A new document '{document.get('name')}' has been shared with you.",
            related_id=portal_doc["id"]
        )
        await db.customer_notifications.insert_one(notification.model_dump())
        shared_count += 1
    
    return {"message": f"Document shared with {shared_count} customers"}


# ============== FORMS / QUESTIONNAIRE MANAGEMENT ==============

@router.get("/forms")
async def get_form_requests(
    customer_id: Optional[str] = None,
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    query = {"tenant_id": current_user.tenant_id}
    if customer_id:
        query["customer_id"] = customer_id
    if job_id:
        query["job_id"] = job_id
    if status:
        query["status"] = status

    requests = await db.portal_form_requests.find(query, {"_id": 0}).sort("sent_at", -1).to_list(500)
    for request in requests:
        request["customer"] = await db.customers.find_one({"id": request.get("customer_id")}, {"_id": 0, "id": 1, "name": 1, "email": 1})
        if request.get("job_id"):
            request["job"] = await db.jobs.find_one({"id": request.get("job_id")}, {"_id": 0, "id": 1, "name": 1})
    return requests


@router.post("/forms/send")
async def send_form_request(
    input: PortalFormSendCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    customer = await db.customers.find_one({"id": input.customer_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    questionnaire = await db.questionnaires.find_one({"id": input.questionnaire_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not questionnaire:
        raise HTTPException(status_code=404, detail="Questionnaire not found")

    if input.job_id:
        job = await db.jobs.find_one({"id": input.job_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

    now = datetime.now(timezone.utc).isoformat()
    request = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "customer_id": input.customer_id,
        "job_id": input.job_id,
        "questionnaire_id": input.questionnaire_id,
        "questionnaire_name": questionnaire.get("name"),
        "instructions": input.instructions,
        "due_date": input.due_date,
        "status": "pending",
        "sent_at": now,
        "created_at": now,
        "created_by": current_user.id,
    }
    await db.portal_form_requests.insert_one(request)

    notification = CustomerNotification(
        tenant_id=current_user.tenant_id,
        customer_id=input.customer_id,
        notification_type="form_request",
        title="New Form Request",
        message=f"Please complete {questionnaire.get('name')}",
        link=f"/customer-portal/forms/{request['id']}",
        related_id=request["id"],
    )
    await db.customer_notifications.insert_one(notification.model_dump())

    # Remove MongoDB _id before returning
    request.pop("_id", None)
    return request


# ============== ARTWORK APPROVALS ==============

@router.get("/artwork-queue")
async def get_artwork_approval_queue(
    status: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get all artwork proofs with their status.
    This is the approval queue for the admin to manage.
    """
    tenant_id = current_user.tenant_id
    query = {"tenant_id": tenant_id}
    
    if status:
        query["status"] = status
    
    proofs = await db.artwork_proofs.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    # Enrich with customer and job info
    for proof in proofs:
        customer = await db.customers.find_one(
            {"id": proof.get("customer_id")},
            {"_id": 0, "id": 1, "name": 1, "email": 1}
        )
        proof["customer"] = customer
        
        job = await db.jobs.find_one(
            {"id": proof.get("job_id")},
            {"_id": 0, "id": 1, "name": 1}
        )
        proof["job"] = job
    
    return proofs


@router.post("/artwork/send")
async def send_artwork_for_approval(
    input: ArtworkSendCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Send artwork to customer for approval.
    Creates an artwork proof and notifies the customer.
    """
    tenant_id = current_user.tenant_id
    
    # Verify customer
    customer = await db.customers.find_one(
        {"id": input.customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify job
    job = await db.jobs.find_one(
        {"id": input.job_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get next version number
    latest = await db.artwork_proofs.find_one(
        {"job_id": input.job_id, "tenant_id": tenant_id},
        {"_id": 0},
        sort=[("version", -1)]
    )
    version = (latest["version"] + 1) if latest else 1
    
    # Create artwork proof
    proof = ArtworkProof(
        tenant_id=tenant_id,
        job_id=input.job_id,
        customer_id=input.customer_id,
        version=version,
        file_url=input.watermarked_url or input.file_url,
        file_name=input.file_name,
        thumbnail_url=input.thumbnail_url,
        description=input.description,
        status=ProofStatus.PENDING
    )
    await db.artwork_proofs.insert_one(proof.model_dump())
    
    # Create notification for customer
    notification = CustomerNotification(
        tenant_id=tenant_id,
        customer_id=input.customer_id,
        notification_type="proof_ready",
        title="Artwork Ready for Approval",
        message=f"Version {version} of your artwork for '{job.get('name', 'your order')}' is ready for review.",
        related_id=proof.id
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    logger.info(f"Artwork proof {proof.id} sent to customer {input.customer_id} for job {input.job_id}")
    
    return {
        "message": "Artwork sent for approval",
        "proof_id": proof.id,
        "version": version
    }


@router.get("/customers")
async def get_customers_for_admin_portal(
    search: Optional[str] = None,
    portal_enabled_only: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get customers list for the admin portal dropdowns."""
    tenant_id = current_user.tenant_id
    query = {"tenant_id": tenant_id}
    
    if portal_enabled_only:
        query["portal_enabled"] = True
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}}
        ]
    
    customers = await db.customers.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1, "portal_enabled": 1}
    ).sort("name", 1).to_list(500)
    
    return customers


@router.get("/jobs")
async def get_jobs_for_admin_portal(
    customer_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get active jobs for the admin portal dropdowns."""
    tenant_id = current_user.tenant_id
    query = {
        "tenant_id": tenant_id,
        "status": {"$nin": ["complete", "delivered", "cancelled", "archived"]}
    }
    
    if customer_id:
        query["customer_id"] = customer_id
    
    jobs = await db.jobs.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "customer_id": 1, "status": 1}
    ).sort("created_at", -1).to_list(500)
    
    # Enrich with customer name
    for job in jobs:
        customer = await db.customers.find_one(
            {"id": job.get("customer_id")},
            {"_id": 0, "name": 1}
        )
        job["customer_name"] = customer.get("name") if customer else "Unknown"
    
    return jobs
