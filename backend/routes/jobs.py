"""
Job Management Routes

This module contains all routes related to:
- Job CRUD operations
- Job items (line items)
- Job notes
- Job activities (audit log)
- Job status management (archive, complete, etc.)
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from models import (
    Job, JobCreate, JobUpdate, JobStatus,
    JobItem, JobItemCreate, JobItemUpdate, JobItemStatus, JobItemType,
    JobNote, JobNoteCreate,
    JobActivity, JobActivityType,
    UserInDB, Permission
)

# Import from server module
from server import (
    db, logger,
    get_current_active_user, has_permission
)

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
    """Create a new job"""
    job = Job(**input.model_dump())
    job.tenant_id = current_user.tenant_id
    doc = job.model_dump()
    await db.jobs.insert_one(doc)
    
    # Log creation
    await log_job_activity(job.id, JobActivityType.CREATED, f"Job '{job.name}' created")
    
    return job


@router.get("", response_model=List[Job])
async def get_jobs(
    customer_id: Optional[str] = None,
    status: Optional[JobStatus] = None,
    filter_type: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all jobs with optional filtering"""
    query = {"tenant_id": current_user.tenant_id}
    if customer_id:
        query["customer_id"] = customer_id
    
    # Handle filter types
    if filter_type == "active":
        query["status"] = {"$nin": [JobStatus.COMPLETE.value, JobStatus.ARCHIVED.value]}
        query["is_archived"] = {"$ne": True}
    elif filter_type == "completed":
        query["status"] = JobStatus.COMPLETE.value
        query["is_archived"] = {"$ne": True}
    elif filter_type == "archived":
        query["$or"] = [{"is_archived": True}, {"status": JobStatus.ARCHIVED.value}]
    elif status:
        query["status"] = status.value
    
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
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
    """Update a job"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Log status change
    if input.status and input.status.value != job.get("status"):
        old_status = job.get("status")
        new_status = input.status.value
        
        if new_status == JobStatus.COMPLETE.value:
            await log_job_activity(job_id, JobActivityType.COMPLETED, f"Job marked as complete", old_status, new_status)
        elif new_status == JobStatus.ARCHIVED.value:
            await log_job_activity(job_id, JobActivityType.ARCHIVED, f"Job archived", old_status, new_status)
        else:
            await log_job_activity(job_id, JobActivityType.STATUS_CHANGED, f"Status changed from {old_status} to {new_status}", old_status, new_status)
    
    await db.jobs.update_one({"id": job_id}, {"$set": update_data})
    updated_job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
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
async def get_job_item(item_id: str):
    """Get a specific job item"""
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
        raise HTTPException(status_code=404, detail="Job item not found")
    return job_item


@job_items_router.put("/{item_id}", response_model=JobItem)
async def update_job_item(item_id: str, input: JobItemUpdate):
    """Update a job item"""
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
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
async def delete_job_item(item_id: str):
    """Delete a job item"""
    job_item = await db.job_items.find_one({"id": item_id}, {"_id": 0})
    if not job_item:
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
