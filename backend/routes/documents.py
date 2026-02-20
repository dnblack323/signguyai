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

from server import db, logger, get_current_active_user
from models import UserInDB


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
    file_data: str  # base64 encoded file
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
            detail=f"File type not allowed. Supported types: PDF, Images, Word, Excel, Text, CSV"
        )
    
    # Read file content
    contents = await file.read()
    
    # Check file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB"
        )
    
    # Convert to base64
    file_data = base64.b64encode(contents).decode('utf-8')
    
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    
    # Create document
    doc = Document(
        tenant_id=current_user.tenant_id,
        name=name,
        description=description,
        category=DocumentCategory(category) if category in [e.value for e in DocumentCategory] else DocumentCategory.OTHER,
        file_type=file.content_type,
        file_size=len(contents),
        file_data=file_data,
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
        "file_data": doc["file_data"]
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
        {"value": "other", "label": "Other"},
    ]
