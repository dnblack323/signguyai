"""
Document Library Routes

This module handles document management including:
- Uploading documents (PDFs, images, etc.)
- Organizing documents by category
- Linking documents to jobs/customers
- Document templates
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import uuid
import base64
from enum import Enum
from pathlib import Path

from server import db, logger, get_current_active_user
from models import UserInDB
from services.object_storage import get_object, put_object
from services.storage_config import APP_NAME


class DocumentCategory(str, Enum):
    CONTRACT = "contract"
    INVOICE_TEMPLATE = "invoice_template"
    WORK_ORDER = "work_order"
    ARTWORK = "artwork"
    PROOF = "proof"
    PERMIT = "permit"
    INSURANCE = "insurance"
    WARRANTY = "warranty"
    QUOTE_TEMPLATE = "quote_template"
    CUSTOMER_FORM = "customer_form"
    INTERNAL = "internal"
    # Marketing & branding outputs from AI tools (audit 2026-04)
    MARKETING_CONTENT = "marketing_content"
    SOCIAL_POST = "social_post"
    CONTENT_CALENDAR = "content_calendar"
    CAMPAIGN_PLAN = "campaign_plan"
    BLOG_ARTICLE = "blog_article"
    LOGO_CONCEPT = "logo_concept"
    BRAND_KIT = "brand_kit"
    TAGLINE = "tagline"
    OTHER = "other"


class DocumentStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: DocumentCategory = DocumentCategory.OTHER
    file_type: str  # e.g., "application/pdf", "image/png"
    file_size: int  # in bytes
    file_data: Optional[str] = None  # legacy base64 fallback
    storage_path: Optional[str] = None
    storage_backend: Optional[str] = None
    file_url: Optional[str] = None
    original_filename: str
    is_template: bool = False  # Can be used as a template for jobs
    tags: List[str] = []
    linked_jobs: List[str] = []  # List of job IDs
    linked_customers: List[str] = []  # List of customer IDs
    status: DocumentStatus = DocumentStatus.ACTIVE
    uploaded_by: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DocumentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: DocumentCategory = DocumentCategory.OTHER
    is_template: bool = False
    tags: List[str] = []


class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[DocumentCategory] = None
    is_template: Optional[bool] = None
    tags: Optional[List[str]] = None
    status: Optional[DocumentStatus] = None


class DocumentLink(BaseModel):
    job_id: Optional[str] = None
    customer_id: Optional[str] = None


router = APIRouter(prefix="/documents", tags=["Documents"])


# Allowed file types
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
    "image/gif",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
    "text/csv",
]

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def _build_document_storage_path(tenant_id: str, document_id: str, filename: str) -> str:
    extension = Path(filename or "document.bin").suffix or ".bin"
    return f"{APP_NAME}/documents/{tenant_id}/{document_id}/{uuid.uuid4()}{extension}"


async def _migrate_document_to_storage(doc: dict) -> Optional[str]:
    if doc.get("storage_path") or not doc.get("file_data"):
        return doc.get("storage_path")

    file_bytes = base64.b64decode(doc["file_data"])
    storage_path = _build_document_storage_path(doc["tenant_id"], doc["id"], doc.get("original_filename") or doc.get("name") or "document.bin")
    result = put_object(storage_path, file_bytes, doc.get("file_type") or "application/octet-stream")
    stored_path = result.get("path", storage_path)
    await db.documents.update_one(
        {"id": doc["id"], "tenant_id": doc["tenant_id"]},
        {"$set": {
            "storage_path": stored_path,
            "storage_backend": "emergent_object_storage",
            "file_url": f"/api/documents/{doc['id']}/download",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return stored_path


async def _get_document_bytes(doc: dict) -> tuple[bytes, str]:
    storage_path = doc.get("storage_path") or await _migrate_document_to_storage(doc)
    if storage_path:
        data, content_type = get_object(storage_path)
        return data, content_type or doc.get("file_type") or "application/octet-stream"

    if doc.get("file_data"):
        return base64.b64decode(doc["file_data"]), doc.get("file_type") or "application/octet-stream"

    raise HTTPException(status_code=404, detail="Document file contents are unavailable")


async def _get_document_base64(doc: dict) -> str:
    if doc.get("file_data"):
        await _migrate_document_to_storage(doc)
        return doc["file_data"]

    data, _content_type = await _get_document_bytes(doc)
    return base64.b64encode(data).decode('utf-8')


@router.post("", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form("other"),
    is_template: bool = Form(False),
    tags: str = Form(""),  # Comma-separated tags
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Upload a new document"""
    # Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Supported types: PDF, Images, Word, Excel, Text, CSV"
        )
    
    # Read file content
    contents = await file.read()
    
    # Check file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB"
        )
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    document_id = str(uuid.uuid4())
    storage_path = _build_document_storage_path(current_user.tenant_id, document_id, file.filename or "document.bin")
    result = put_object(storage_path, contents, file.content_type or "application/octet-stream")
    
    # Create document
    doc = Document(
        id=document_id,
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        category=DocumentCategory(category) if category in [e.value for e in DocumentCategory] else DocumentCategory.OTHER,
        file_type=file.content_type,
        file_size=len(contents),
        storage_path=result.get("path", storage_path),
        storage_backend="emergent_object_storage",
        file_url=f"/api/documents/{document_id}/download",
        original_filename=file.filename or "unknown",
        is_template=is_template,
        tags=tag_list,
        uploaded_by=current_user.id
    )
    
    await db.documents.insert_one(doc.model_dump())
    logger.info(f"Document '{name}' uploaded by user {current_user.id}")
    
    # Return without the full file_data to save bandwidth
    response = doc.model_dump()
    response["file_data"] = "[BASE64_DATA]"  # Placeholder
    return response


@router.get("")
async def list_documents(
    category: Optional[str] = None,
    is_template: Optional[bool] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    job_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all documents for the tenant"""
    query = {"tenant_id": current_user.tenant_id}
    
    if category:
        query["category"] = category
    if is_template is not None:
        query["is_template"] = is_template
    if status:
        query["status"] = status
    else:
        query["status"] = "active"  # Default to active documents
    if job_id:
        query["linked_jobs"] = job_id
    if customer_id:
        query["linked_customers"] = customer_id
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$regex": search, "$options": "i"}}
        ]
    
    # Don't return file_data in list view
    documents = await db.documents.find(
        query,
        {"_id": 0, "file_data": 0}
    ).sort("created_at", -1).to_list(500)
    
    return documents


@router.get("/stats")
async def get_document_stats(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get document statistics"""
    query = {"tenant_id": current_user.tenant_id, "status": "active"}
    
    total = await db.documents.count_documents(query)
    templates = await db.documents.count_documents({**query, "is_template": True})
    
    # Count by category
    pipeline = [
        {"$match": query},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_counts = await db.documents.aggregate(pipeline).to_list(20)
    categories = {item["_id"]: item["count"] for item in category_counts}
    
    # Calculate total storage used
    pipeline = [
        {"$match": query},
        {"$group": {"_id": None, "total_size": {"$sum": "$file_size"}}}
    ]
    size_result = await db.documents.aggregate(pipeline).to_list(1)
    total_size = size_result[0]["total_size"] if size_result else 0
    
    return {
        "total_documents": total,
        "templates": templates,
        "by_category": categories,
        "storage_used_bytes": total_size,
        "storage_used_mb": round(total_size / (1024 * 1024), 2)
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    include_data: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific document"""
    projection = {"_id": 0}
    if not include_data:
        projection["file_data"] = 0
    
    doc = await db.documents.find_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        projection
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get document with file data for download"""
    doc = await db.documents.find_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": doc["id"],
        "name": doc["name"],
        "file_type": doc["file_type"],
        "original_filename": doc["original_filename"],
        "file_data": await _get_document_base64(doc)
    }


@router.put("/{document_id}")
async def update_document(
    document_id: str,
    input: DocumentUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update document metadata"""
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.documents.update_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = await db.documents.find_one(
        {"id": document_id},
        {"_id": 0, "file_data": 0}
    )
    return doc


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a document (or archive it)"""
    # Soft delete by archiving
    result = await db.documents.update_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        {"$set": {"status": "archived", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document archived"}


@router.post("/{document_id}/link")
async def link_document(
    document_id: str,
    link: DocumentLink,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Link a document to a job or customer"""
    doc = await db.documents.find_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_ops = {}
    
    if link.job_id:
        # Verify job exists
        job = await db.jobs.find_one({"id": link.job_id, "tenant_id": current_user.tenant_id})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        update_ops["$addToSet"] = {"linked_jobs": link.job_id}
    
    if link.customer_id:
        # Verify customer exists
        customer = await db.customers.find_one({"id": link.customer_id, "tenant_id": current_user.tenant_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        if "$addToSet" not in update_ops:
            update_ops["$addToSet"] = {}
        update_ops["$addToSet"]["linked_customers"] = link.customer_id
    
    if update_ops:
        update_ops["$set"] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        await db.documents.update_one({"id": document_id}, update_ops)
    
    return {"message": "Document linked successfully"}


@router.delete("/{document_id}/link")
async def unlink_document(
    document_id: str,
    job_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Unlink a document from a job or customer"""
    doc = await db.documents.find_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_ops = {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    
    if job_id:
        update_ops["$pull"] = {"linked_jobs": job_id}
    
    if customer_id:
        if "$pull" not in update_ops:
            update_ops["$pull"] = {}
        update_ops["$pull"]["linked_customers"] = customer_id
    
    await db.documents.update_one({"id": document_id}, update_ops)
    
    return {"message": "Document unlinked successfully"}


@router.get("/categories/list")
async def get_categories():
    """Get list of available document categories"""
    return [
        {"value": "contract", "label": "Contract"},
        {"value": "invoice_template", "label": "Invoice Template"},
        {"value": "work_order", "label": "Work Order"},
        {"value": "artwork", "label": "Artwork"},
        {"value": "proof", "label": "Proof"},
        {"value": "permit", "label": "Permit"},
        {"value": "insurance", "label": "Insurance"},
        {"value": "warranty", "label": "Warranty"},
        {"value": "quote_template", "label": "Quote Template"},
        {"value": "customer_form", "label": "Customer Form"},
        {"value": "internal", "label": "Internal"},
        # Marketing & branding outputs from AI tools (audit 2026-04)
        {"value": "marketing_content", "label": "Marketing Content"},
        {"value": "social_post", "label": "Social Post"},
        {"value": "content_calendar", "label": "Content Calendar"},
        {"value": "campaign_plan", "label": "Campaign Plan"},
        {"value": "blog_article", "label": "Blog Article"},
        {"value": "logo_concept", "label": "Logo Concept"},
        {"value": "brand_kit", "label": "Brand Kit"},
        {"value": "tagline", "label": "Tagline"},
        {"value": "other", "label": "Other"},
    ]


# ============== DOCUMENT DELIVERY ==============

class SendDocumentEmail(BaseModel):
    customer_id: str
    subject: Optional[str] = None
    message: Optional[str] = None
    include_attachment: bool = True


class SendToPortal(BaseModel):
    customer_id: str
    notify_customer: bool = True
    message: Optional[str] = None


@router.post("/{document_id}/send-email")
async def send_document_via_email(
    document_id: str,
    input: SendDocumentEmail,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Send a document to a customer via email"""
    from services.email_service import email_service
    
    # Get the document
    doc = await db.documents.find_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get the customer
    customer = await db.customers.find_one(
        {"id": input.customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    if not customer.get("email"):
        raise HTTPException(status_code=400, detail="Customer does not have an email address")
    
    # Get tenant info for company name
    tenant = await db.tenants.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0})
    company_name = tenant.get("company_name", "SignGuy AI") if tenant else "SignGuy AI"
    
    # Prepare attachment if requested
    attachment = None
    if input.include_attachment:
        attachment = {
            "filename": doc.get("original_filename", f"{doc['name']}.pdf"),
            "content": await _get_document_base64(doc),
            "type": doc.get("file_type", "application/octet-stream")
        }
    
    # Send the email
    result = await email_service.send_document_to_customer(
        customer_email=customer["email"],
        customer_name=customer.get("name", customer.get("contact_name", "Valued Customer")),
        document_name=doc["name"],
        document_content=input.message or doc.get("description", "Please review the attached document."),
        document_attachment=attachment,
        tenant_id=current_user.tenant_id,
        company_name=company_name
    )
    
    if result["success"]:
        # Link document to customer if not already linked
        await db.documents.update_one(
            {"id": document_id},
            {
                "$addToSet": {"linked_customers": input.customer_id},
                "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
            }
        )
        
        # Log the send activity
        activity = {
            "id": str(uuid.uuid4()),
            "tenant_id": current_user.tenant_id,
            "document_id": document_id,
            "customer_id": input.customer_id,
            "action": "emailed",
            "performed_by": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.document_activities.insert_one(activity)
        
        return {"message": "Document sent via email successfully", "email": customer["email"]}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {result.get('error', 'Unknown error')}")


@router.post("/{document_id}/send-to-portal")
async def send_document_to_portal(
    document_id: str,
    input: SendToPortal,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Send a document to a customer's portal and optionally notify them"""
    from services.email_service import email_service
    
    # Get the document
    doc = await db.documents.find_one(
        {"id": document_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get the customer
    customer = await db.customers.find_one(
        {"id": input.customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if customer has portal access
    if not customer.get("portal_enabled"):
        raise HTTPException(status_code=400, detail="Customer does not have portal access enabled")
    
    # Get tenant info
    tenant = await db.tenants.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0})
    company_name = tenant.get("company_name", "SignGuy AI") if tenant else "SignGuy AI"
    
    # Create a portal document entry
    portal_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "customer_id": input.customer_id,
        "document_id": document_id,
        "document_name": doc["name"],
        "document_category": doc.get("category", "other"),
        "message": input.message,
        "status": "unread",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.id
    }
    await db.portal_documents.insert_one(portal_doc)
    
    # Link document to customer
    await db.documents.update_one(
        {"id": document_id},
        {
            "$addToSet": {"linked_customers": input.customer_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    # Create notification for customer
    notification = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "customer_id": input.customer_id,
        "notification_type": "document_ready",
        "title": f"New Document: {doc['name']}",
        "message": input.message or f"A new document '{doc['name']}' has been shared with you.",
        "link": f"/portal/documents/{portal_doc['id']}",
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.customer_notifications.insert_one(notification)
    
    # Send email notification if requested
    email_sent = False
    if input.notify_customer and customer.get("email"):
        portal_url = tenant.get("portal_url", "https://signguy.ai/customer-portal") if tenant else "https://signguy.ai/customer-portal"
        
        result = await email_service.send_portal_notification(
            customer_email=customer["email"],
            customer_name=customer.get("name", customer.get("contact_name", "Valued Customer")),
            notification_type="document_ready",
            notification_title=f"New Document: {doc['name']}",
            notification_message=input.message or "A new document has been shared with you. Please log in to your portal to view it.",
            portal_link=f"{portal_url}/documents",
            tenant_id=current_user.tenant_id,
            company_name=company_name
        )
        email_sent = result.get("success", False)
    
    # Log the activity
    activity = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "document_id": document_id,
        "customer_id": input.customer_id,
        "action": "sent_to_portal",
        "email_notification_sent": email_sent,
        "performed_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.document_activities.insert_one(activity)
    
    return {
        "message": "Document sent to customer portal",
        "portal_document_id": portal_doc["id"],
        "notification_sent": email_sent
    }


@router.get("/portal/{customer_id}")
async def get_customer_portal_documents(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all documents shared with a customer via portal"""
    # Verify customer belongs to tenant
    customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    portal_docs = await db.portal_documents.find(
        {"customer_id": customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return portal_docs



# ============== AI DOCUMENT GENERATION ==============

class AIDocumentCreate(BaseModel):
    """Create a document from AI-generated content"""
    content: str
    name: str
    tool_id: Optional[str] = None
    category: str = "other"
    input_data: Optional[dict] = None


class PDFGenerateRequest(BaseModel):
    """Request to generate a PDF from content"""
    content: str
    title: str
    tool_id: Optional[str] = None


@router.post("/from-ai")
async def create_document_from_ai(
    input: AIDocumentCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a document from AI-generated content (text becomes a text file)"""
    import io
    
    # Create a simple text file from the content
    content_bytes = input.content.encode('utf-8')
    document_id = str(uuid.uuid4())
    original_filename = f"{input.name.replace(' ', '_')}.txt"
    storage_path = _build_document_storage_path(current_user.tenant_id, document_id, original_filename)
    result = put_object(storage_path, content_bytes, "text/plain")
    
    doc = Document(
        id=document_id,
        tenant_id=current_user.tenant_id,
        name=input.name,
        description=f"Generated by AI tool: {input.tool_id or 'unknown'}",
        category=DocumentCategory(input.category) if input.category in [e.value for e in DocumentCategory] else DocumentCategory.OTHER,
        file_type="text/plain",
        file_size=len(content_bytes),
        storage_path=result.get("path", storage_path),
        storage_backend="emergent_object_storage",
        file_url=f"/api/documents/{document_id}/download",
        original_filename=original_filename,
        uploaded_by=current_user.id,
        tags=["ai-generated", input.tool_id] if input.tool_id else ["ai-generated"]
    )
    
    await db.documents.insert_one(doc.model_dump())
    
    # Return document without file_data for efficiency
    result = doc.model_dump()
    if 'file_data' in result:
        del result['file_data']
    
    return result


async def get_template_variables(tenant_id: str, customer_id: Optional[str] = None, job_id: Optional[str] = None) -> dict:
    """Get all available template variables for replacement"""
    from datetime import datetime
    
    variables = {
        "today_date": datetime.now().strftime("%B %d, %Y"),
        "today_short": datetime.now().strftime("%m/%d/%Y"),
        "current_year": str(datetime.now().year),
    }
    
    # Get tenant info
    tenant = await db.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0})
    if tenant:
        variables.update({
            "company_name": tenant.get("company_name", ""),
            "company_address": tenant.get("address", ""),
            "company_city": tenant.get("city", ""),
            "company_state": tenant.get("state", ""),
            "company_zip": tenant.get("zip_code", ""),
            "company_phone": tenant.get("phone", ""),
            "company_email": tenant.get("email", ""),
            "company_website": tenant.get("website", ""),
            "logo_url": tenant.get("logo_url", ""),
        })
    
    # Get customer info
    if customer_id:
        customer = await db.customers.find_one({"id": customer_id, "tenant_id": tenant_id}, {"_id": 0})
        if customer:
            variables.update({
                "customer_name": customer.get("name", customer.get("contact_name", "")),
                "customer_email": customer.get("email", ""),
                "customer_phone": customer.get("phone", ""),
                "customer_company": customer.get("company", ""),
                "customer_address": customer.get("address", ""),
                "customer_city": customer.get("city", ""),
                "customer_state": customer.get("state", ""),
                "customer_zip": customer.get("zip_code", ""),
            })
    
    # Get order/job info
    if job_id:
        job = await db.orders.find_one({"id": job_id, "tenant_id": tenant_id}, {"_id": 0})
        if job:
            variables.update({
                "order_id": job.get("order_id", job.get("id", "")),
                "order_date": job.get("created_at", "")[:10] if job.get("created_at") else "",
                "order_status": job.get("status", ""),
                "order_total": f"${job.get('total', 0):.2f}" if job.get("total") else "$0.00",
                "order_subtotal": f"${job.get('subtotal', 0):.2f}" if job.get("subtotal") else "$0.00",
                "order_tax": f"${job.get('tax', 0):.2f}" if job.get("tax") else "$0.00",
                "due_date": job.get("due_date", "")[:10] if job.get("due_date") else "",
            })
    
    return variables


def replace_template_variables(content: str, variables: dict) -> str:
    """Replace {{variable_name}} placeholders in content with actual values"""
    import re
    
    # Find all {{variable}} patterns
    pattern = r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}'
    
    def replacer(match):
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))  # Keep placeholder if variable not found
    
    return re.sub(pattern, replacer, content)


@router.post("/{document_id}/populate-from-template")
async def populate_document_from_template(
    document_id: str,
    customer_id: Optional[str] = None,
    job_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a populated copy of a template document with real data"""
    
    # Get the template document
    template = await db.documents.find_one(
        {"id": document_id, "tenant_id": current_user.tenant_id, "is_template": True},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Get template variables
    variables = await get_template_variables(current_user.tenant_id, customer_id, job_id)
    
    # Replace variables in name and description
    new_name = replace_template_variables(template["name"], variables)
    new_description = replace_template_variables(template.get("description", ""), variables) if template.get("description") else None
    
    # Create a new document (copy of template with populated data)
    new_doc = Document(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        name=new_name,
        description=new_description,
        category=template["category"],
        file_type=template["file_type"],
        file_size=template["file_size"],
        file_data=template.get("file_data"),
        storage_path=template.get("storage_path"),
        storage_backend=template.get("storage_backend"),
        file_url=template.get("file_url"),
        original_filename=replace_template_variables(template["original_filename"], variables),
        is_template=False,  # This is an instance, not a template
        tags=template.get("tags", []),
        linked_jobs=[job_id] if job_id else [],
        linked_customers=[customer_id] if customer_id else [],
        uploaded_by=current_user.id,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat()
    )
    
    # Insert new document
    await db.documents.insert_one(new_doc.model_dump())
    
    return {
        "message": "Document created from template with populated data",
        "document": new_doc.model_dump(),
        "variables_used": list(variables.keys())
    }


@router.post("/generate-pdf")
async def generate_pdf_from_content(
    input: PDFGenerateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate a PDF from text content"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        import io
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        # Build story (content)
        story = []
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
        )
        
        # Body style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            spaceAfter=12,
        )
        
        # Add title
        story.append(Paragraph(input.title, title_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Process content - split by newlines and create paragraphs
        lines = input.content.split('\n')
        for line in lines:
            if line.strip():
                # Handle markdown-style headers
                if line.startswith('# '):
                    story.append(Paragraph(line[2:], styles['Heading1']))
                elif line.startswith('## '):
                    story.append(Paragraph(line[3:], styles['Heading2']))
                elif line.startswith('### '):
                    story.append(Paragraph(line[4:], styles['Heading3']))
                elif line.startswith('- '):
                    story.append(Paragraph(f"• {line[2:]}", body_style))
                elif line.startswith('* '):
                    story.append(Paragraph(f"• {line[2:]}", body_style))
                else:
                    # Escape special characters for reportlab
                    safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    story.append(Paragraph(safe_line, body_style))
            else:
                story.append(Spacer(1, 0.1 * inch))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Encode to base64
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        # Generate filename
        safe_title = "".join(c for c in input.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title.replace(' ', '_')}.pdf"
        
        return {
            "pdf_data": pdf_base64,
            "filename": filename,
            "file_size": len(pdf_data)
        }
        
    except ImportError:
        raise HTTPException(
            status_code=500, 
            detail="PDF generation library not installed. Please install reportlab."
        )
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

