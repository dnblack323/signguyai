"""
Job Management Routes (Unified with Quotes)

This module contains all routes related to:
- Job CRUD operations (including quote stage)
- Job items (line items)
- Job notes
- Job activities (audit log)
- Job status management (archive, complete, etc.)

IMPORTANT: Quotes are now jobs with status="quote"
- Creating a "quote" = creating a job with status="quote"
- Approving a quote = updating job status to "approved"
- No separate quote storage or collection
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone

from models import (
    Job, JobCreate, JobUpdate, JobStatus, JobLineItem,
    JobItem, JobItemCreate, JobItemUpdate, JobItemStatus, JobItemType,
    JobNote, JobNoteCreate,
    JobActivity, JobActivityType,
    UserInDB, Permission
)

# Import from server module - using late import to avoid circular dependency
from core.auth_deps import get_current_active_user

# Lazy imports to avoid circular dependency
_db = None
_logger = None
_has_permission = None

def _get_db():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db

def _get_logger():
    global _logger
    if _logger is None:
        from server import logger
        _logger = logger
    return _logger

def _get_has_permission():
    global _has_permission
    if _has_permission is None:
        from server import has_permission
        _has_permission = has_permission
    return _has_permission

# Create property-like accessors
class LazyDB:
    def __getattr__(self, name):
        return getattr(_get_db(), name)

db = LazyDB()

router = APIRouter(prefix="/jobs", tags=["Jobs"])


# ============== HELPER FUNCTIONS ==============

async def log_job_activity(
    job_id: str, 
    activity_type: JobActivityType, 
    description: str, 
    old_value: str = None, 
    new_value: str = None
):
    """Log an activity for a job"""
    activity = JobActivity(
        job_id=job_id,
        activity_type=activity_type,
        description=description,
        old_value=old_value,
        new_value=new_value
    )
    await db.job_activities.insert_one(activity.model_dump())


async def recalculate_job_subtotal(job_id: str) -> float:
    """Recalculate and update job subtotal from items"""
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    subtotal = sum(item.get("line_total", 0) for item in job_items)
    await db.jobs.update_one(
        {"id": job_id}, 
        {"$set": {"subtotal": subtotal, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return subtotal


# ============== JOB CRUD ==============

@router.post("", response_model=Job)
async def create_job(
    input: JobCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Create a new job.
    
    - If status="quote": Creates a job in quote stage (not yet approved)
    - If status="approved": Creates a job ready for production
    - Default status is "quote" (pipeline stage)
    """
    # Calculate total from line items if present
    total = 0
    line_items_with_totals = []
    if input.line_items:
        for item in input.line_items:
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else item
            item_total = item_dict.get('quantity', 1) * item_dict.get('unit_price', 0)
            item_dict['total'] = item_total
            line_items_with_totals.append(item_dict)
            total += item_total
    
    job_data = input.model_dump()
    job_data['line_items'] = line_items_with_totals
    job_data['total'] = total
    job_data['subtotal'] = total
    
    job = Job(**job_data)
    job.tenant_id = current_user.tenant_id
    doc = job.model_dump()
    await db.jobs.insert_one(doc)
    
    # Log creation
    activity_desc = f"Quote '{job.name}' created" if job.status == JobStatus.QUOTE else f"Job '{job.name}' created"
    await log_job_activity(job.id, JobActivityType.CREATED, activity_desc)
    
    return job


@router.get("", response_model=List[Job])
async def get_jobs(
    customer_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    filter_type: Optional[str] = Query(None, description="Filter: all, quotes, active, completed, invoiced, archived"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    List all jobs with optional filtering.
    
    Filter types:
    - all: All jobs (excludes archived by default)
    - quotes: Only jobs in quote stage (status=quote)
    - active: Jobs in production (approved, in_progress)
    - completed: Completed jobs
    - invoiced: Invoiced jobs
    - archived: Archived jobs only
    """
    query = {"tenant_id": current_user.tenant_id}
    if customer_id:
        query["customer_id"] = customer_id
    
    # Handle filter types
    if filter_type == "quotes":
        query["status"] = JobStatus.QUOTE.value
        query["is_archived"] = {"$ne": True}
    elif filter_type == "active":
        # Active = approved or in_progress (production stage)
        query["status"] = {"$in": [JobStatus.APPROVED.value, JobStatus.IN_PROGRESS.value]}
        query["is_archived"] = {"$ne": True}
    elif filter_type == "completed":
        query["status"] = JobStatus.COMPLETED.value
        query["is_archived"] = {"$ne": True}
    elif filter_type == "invoiced":
        query["status"] = JobStatus.INVOICED.value
        query["is_archived"] = {"$ne": True}
    elif filter_type == "archived":
        query["$or"] = [{"is_archived": True}, {"status": JobStatus.ARCHIVED.value}]
    elif filter_type == "all" or filter_type is None:
        # Show all non-archived jobs by default
        query["is_archived"] = {"$ne": True}
        query["status"] = {"$ne": JobStatus.ARCHIVED.value}
    elif status:
        # Direct status filter
        query["status"] = status.value
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return jobs
    return jobs


@router.get("/{job_id}", response_model=Job)
async def get_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific job by ID"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/details")
async def get_job_details(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get comprehensive job details including related data"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get customer
    customer = await db.customers.find_one({"id": job["customer_id"]}, {"_id": 0})
    
    # Get quote if exists
    quote = None
    if job.get("quote_id"):
        quote = await db.quotes.find_one({"id": job["quote_id"]}, {"_id": 0})
    
    # Get invoice if exists
    invoice = None
    if job.get("invoice_id"):
        invoice = await db.invoices.find_one({"id": job["invoice_id"]}, {"_id": 0})
    
    # Get job items
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    
    # Get job notes
    notes = await db.job_notes.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Get activity log
    activities = await db.job_activities.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Calculate financial snapshot
    quote_total = quote.get("total", 0) if quote else 0
    invoice_total = invoice.get("total", 0) if invoice else 0
    amount_paid = invoice.get("amount_paid", 0) if invoice else 0
    balance_due = invoice_total - amount_paid if invoice else 0
    
    return {
        "job": job,
        "customer": customer,
        "quote": quote,
        "invoice": invoice,
        "job_items": job_items,
        "notes": notes,
        "activities": activities,
        "financial_snapshot": {
            "quote_total": quote_total,
            "invoice_total": invoice_total,
            "invoice_status": invoice.get("status") if invoice else None,
            "amount_paid": amount_paid,
            "balance_due": balance_due
        }
    }


@router.put("/{job_id}", response_model=Job)
async def update_job(
    job_id: str, 
    input: JobUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Update a job.
    
    Status transitions:
    - quote -> approved: Quote approved, ready for production
    - approved -> in_progress: Production started
    - in_progress -> completed: Job finished
    - completed -> invoiced: Invoice created
    - Any -> archived: Job archived
    """
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Handle line_items update - recalculate total
    if "line_items" in update_data and update_data["line_items"]:
        total = 0
        processed_items = []
        for item in update_data["line_items"]:
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else item
            item_total = item_dict.get("quantity", 1) * item_dict.get("unit_price", 0)
            item_dict["total"] = item_total
            processed_items.append(item_dict)
            total += item_total
        update_data["line_items"] = processed_items
        update_data["total"] = total
        update_data["subtotal"] = total
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Log status change with proper descriptions
    if input.status and input.status.value != job.get("status"):
        old_status = job.get("status")
        new_status = input.status.value
        
        # Set approved_at timestamp when moving from quote to approved
        if old_status == JobStatus.QUOTE.value and new_status == JobStatus.APPROVED.value:
            update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
            await log_job_activity(job_id, JobActivityType.STATUS_CHANGED, "Quote approved - ready for production", old_status, new_status)
        elif new_status == JobStatus.COMPLETED.value:
            await log_job_activity(job_id, JobActivityType.COMPLETED, "Job marked as complete", old_status, new_status)
        elif new_status == JobStatus.INVOICED.value:
            await log_job_activity(job_id, JobActivityType.STATUS_CHANGED, "Job invoiced", old_status, new_status)
        elif new_status == JobStatus.ARCHIVED.value:
            await log_job_activity(job_id, JobActivityType.ARCHIVED, "Job archived", old_status, new_status)
        else:
            await log_job_activity(job_id, JobActivityType.STATUS_CHANGED, f"Status changed from {old_status} to {new_status}", old_status, new_status)
    
    await db.jobs.update_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    updated_job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    return updated_job


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a job and all related data"""
    # Also delete related job items, notes, and activities
    await db.job_items.delete_many({"job_id": job_id})
    await db.job_notes.delete_many({"job_id": job_id})
    await db.job_activities.delete_many({"job_id": job_id})
    result = await db.jobs.delete_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted"}


# ============== JOB STATUS ACTIONS ==============

@router.post("/{job_id}/archive")
async def archive_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Archive a job"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.jobs.update_one(
        {"id": job_id}, 
        {"$set": {
            "is_archived": True, 
            "status": JobStatus.ARCHIVED.value, 
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    await log_job_activity(job_id, JobActivityType.ARCHIVED, "Job archived", job.get("status"), JobStatus.ARCHIVED.value)
    
    return {"message": "Job archived"}


@router.post("/{job_id}/unarchive")
async def unarchive_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Unarchive a job"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    await db.jobs.update_one(
        {"id": job_id}, 
        {"$set": {
            "is_archived": False, 
            "status": JobStatus.COMPLETE.value, 
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    await log_job_activity(job_id, JobActivityType.UNARCHIVED, "Job unarchived", JobStatus.ARCHIVED.value, JobStatus.COMPLETE.value)
    
    return {"message": "Job unarchived"}


@router.post("/{job_id}/complete")
async def complete_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Mark a job as complete"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    old_status = job.get("status")
    await db.jobs.update_one(
        {"id": job_id}, 
        {"$set": {
            "status": JobStatus.COMPLETE.value, 
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    await log_job_activity(job_id, JobActivityType.COMPLETED, "Job marked as complete", old_status, JobStatus.COMPLETE.value)
    
    return {"message": "Job marked as complete"}


# ============== JOB NOTES ==============

@router.post("/{job_id}/notes", response_model=JobNote)
async def create_job_note(
    job_id: str, 
    input: JobNoteCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Add a note to a job"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    note = JobNote(
        job_id=job_id,
        content=input.content,
        author=input.author or current_user.full_name
    )
    await db.job_notes.insert_one(note.model_dump())
    await log_job_activity(job_id, JobActivityType.NOTE_ADDED, f"Note added by {note.author}")
    
    return note


@router.get("/{job_id}/notes", response_model=List[JobNote])
async def get_job_notes(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all notes for a job"""
    notes = await db.job_notes.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return notes


# ============== JOB ACTIVITIES ==============

@router.get("/{job_id}/activities", response_model=List[JobActivity])
async def get_job_activities(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get activity log for a job"""
    activities = await db.job_activities.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return activities


# ============== JOB ITEMS ==============

@router.post("/{job_id}/items", response_model=JobItem)
async def create_job_item(
    job_id: str, 
    input: JobItemCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Add an item to a job"""
    # Verify job exists
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate line total
    line_total = input.quantity * input.unit_price
    
    job_item = JobItem(
        job_id=job_id,
        item_type=input.item_type,
        description=input.description,
        quantity=input.quantity,
        unit_price=input.unit_price,
        line_total=line_total,
        status=input.status,
        notes=input.notes
    )
    doc = job_item.model_dump()
    await db.job_items.insert_one(doc)
    
    # Recalculate job subtotal
    await recalculate_job_subtotal(job_id)
    
    # Log activity
    await log_job_activity(job_id, JobActivityType.ITEM_ADDED, f"Added item: {input.description}")
    
    return job_item


@router.get("/{job_id}/items", response_model=List[JobItem])
async def get_job_items(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all items for a job"""
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    return job_items


# ============== JOB ITEMS (standalone routes) ==============
# These are also available at /job-items/{item_id} for direct access

job_items_router = APIRouter(prefix="/job-items", tags=["Job Items"])


@job_items_router.get("/{item_id}", response_model=JobItem)
async def get_job_item(
    item_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific job item (tenant-scoped)"""
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    # Verify the parent job belongs to this tenant
    job = await db.jobs.find_one(
        {"id": job_item["job_id"], "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    return job_item


@job_items_router.put("/{item_id}", response_model=JobItem)
async def update_job_item(
    item_id: str, 
    input: JobItemUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a job item (tenant-scoped)"""
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    # Verify the parent job belongs to this tenant
    job = await db.jobs.find_one(
        {"id": job_item["job_id"], "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Recalculate line total if quantity or unit_price changed
    quantity = update_data.get("quantity", job_item.get("quantity", 1))
    unit_price = update_data.get("unit_price", job_item.get("unit_price", 0))
    update_data["line_total"] = quantity * unit_price
    
    await db.job_items.update_one({"id": item_id}, {"$set": update_data})
    
    # Recalculate job subtotal
    await recalculate_job_subtotal(job_item["job_id"])
    
    # Log activity
    await log_job_activity(job_item["job_id"], JobActivityType.ITEM_UPDATED, f"Updated item: {job_item.get('description', 'Unknown')}")
    
    updated_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    return updated_item


@job_items_router.delete("/{item_id}")
async def delete_job_item(
    item_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a job item (tenant-scoped)"""
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    # Verify the parent job belongs to this tenant
    job = await db.jobs.find_one(
        {"id": job_item["job_id"], "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job item not found")
    
    job_id = job_item["job_id"]
    result = await db.job_items.delete_one({"id": item_id})
    
    # Recalculate job subtotal
    await recalculate_job_subtotal(job_id)
    
    # Log activity
    await log_job_activity(job_id, JobActivityType.ITEM_DELETED, f"Deleted item: {job_item.get('description', 'Unknown')}")
    
    return {"message": "Job item deleted"}


# Job notes standalone route
job_notes_router = APIRouter(prefix="/job-notes", tags=["Job Notes"])


@job_notes_router.delete("/{note_id}")
async def delete_job_note(note_id: str):
    """Delete a job note"""
    result = await db.job_notes.delete_one({"id": note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted"}
