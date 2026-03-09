"""
Quote Management Routes

This module contains all routes related to:
- Quote CRUD operations
- Quote to Job conversion
- Soft delete and restore
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from models import (
    Quote, QuoteCreate, QuoteUpdate, QuoteLineItem, QuoteStatus,
    Job, JobStatus, JobItem, JobItemType, JobItemStatus,
    JobActivity, JobActivityType,
    UserInDB, Permission
)

# Import from server module
from server import (
    db, logger,
    get_current_active_user, has_permission
)
from services.soft_delete_service import SoftDeleteService, build_active_filter

router = APIRouter(prefix="/quotes", tags=["Quotes"])


@router.post("", response_model=Quote)
async def create_quote(
    input: QuoteCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new quote"""
    # Calculate totals for line items
    line_items = []
    total = 0
    for item in input.line_items:
        item_total = item.quantity * item.unit_price
        line_items.append(QuoteLineItem(
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total=item_total
        ))
        total += item_total
    
    quote = Quote(
        customer_id=input.customer_id,
        line_items=line_items,
        notes=input.notes,
        status=input.status,
        total=total,
        tenant_id=current_user.tenant_id
    )
    doc = quote.model_dump()
    await db.quotes.insert_one(doc)
    return quote


@router.get("", response_model=List[Quote])
async def get_quotes(
    customer_id: Optional[str] = None,
    status: Optional[QuoteStatus] = None,
    include_deleted: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all quotes with optional filtering. Excludes deleted by default."""
    query = build_active_filter(current_user.tenant_id, include_deleted)
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    quotes = await db.quotes.find(query, {"_id": 0}).to_list(1000)
    return quotes


@router.get("/{quote_id}", response_model=Quote)
async def get_quote(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific quote by ID (excludes deleted)"""
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id, "deleted_at": None}, 
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote


@router.put("/{quote_id}", response_model=Quote)
async def update_quote(
    quote_id: str, 
    input: QuoteUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a quote"""
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Cannot update quote that has been converted to job")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Recalculate total if line items changed
    if "line_items" in update_data:
        total = 0
        processed_items = []
        for item in update_data["line_items"]:
            item_dict = item.model_dump() if hasattr(item, 'model_dump') else item
            item_total = item_dict["quantity"] * item_dict["unit_price"]
            item_dict["total"] = item_total
            processed_items.append(item_dict)
            total += item_total
        update_data["line_items"] = processed_items
        update_data["total"] = total
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.quotes.update_one({"id": quote_id}, {"$set": update_data})
    updated_quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    return updated_quote


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: str,
    permanent: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Soft delete a quote. Use permanent=true for hard delete (admin only)."""
    soft_delete_service = SoftDeleteService(db)
    
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Cannot delete quote that has been converted to job")
    
    if permanent:
        # Hard delete - admin only
        success = await soft_delete_service.hard_delete(
            collection_name="quotes",
            record_id=quote_id,
            tenant_id=current_user.tenant_id,
            admin_confirmation=True
        )
        if not success:
            raise HTTPException(status_code=404, detail="Quote not found")
        return {"message": "Quote permanently deleted"}
    else:
        # Soft delete
        success = await soft_delete_service.soft_delete(
            collection_name="quotes",
            record_id=quote_id,
            deleted_by=current_user.id,
            tenant_id=current_user.tenant_id,
            reason="User requested deletion"
        )
        if not success:
            raise HTTPException(status_code=404, detail="Quote not found or already deleted")
        return {"message": "Quote deleted (can be restored)"}


@router.post("/{quote_id}/restore")
async def restore_quote(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Restore a soft-deleted quote"""
    soft_delete_service = SoftDeleteService(db)
    
    success = await soft_delete_service.restore(
        collection_name="quotes",
        record_id=quote_id,
        restored_by=current_user.id,
        tenant_id=current_user.tenant_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Quote not found or not deleted")
    
    # Return the restored quote
    quote = await db.quotes.find_one({"id": quote_id}, {"_id": 0})
    return {"message": "Quote restored", "quote": quote}


@router.get("/deleted/list")
async def get_deleted_quotes(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get list of soft-deleted quotes for admin review"""
    soft_delete_service = SoftDeleteService(db)
    
    deleted = await soft_delete_service.get_deleted_records(
        collection_name="quotes",
        tenant_id=current_user.tenant_id,
        limit=100
    )
    
    return {"deleted_quotes": deleted, "count": len(deleted)}


@router.post("/{quote_id}/convert-to-job", response_model=Job)
async def convert_quote_to_job(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Convert a quote to a job"""
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Quote already converted to job")
    
    # Create job from quote
    job = Job(
        customer_id=quote["customer_id"],
        name=f"Job from Quote #{quote_id[:8]}",
        description=quote.get("notes", ""),
        status=JobStatus.APPROVED,
        quote_id=quote_id,
        subtotal=quote.get("total", 0),
        tenant_id=current_user.tenant_id
    )
    job_doc = job.model_dump()
    await db.jobs.insert_one(job_doc)
    
    # Create JobItems from Quote line items
    for item in quote.get("line_items", []):
        job_item = JobItem(
            job_id=job.id,
            item_type=JobItemType.OTHER,
            description=item.get("description", ""),
            quantity=item.get("quantity", 1),
            unit_price=item.get("unit_price", 0),
            line_total=item.get("total", item.get("quantity", 1) * item.get("unit_price", 0)),
            status=JobItemStatus.PENDING
        )
        await db.job_items.insert_one(job_item.model_dump())
    
    # Update quote with job_id
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {"job_id": job.id, "status": QuoteStatus.APPROVED.value}}
    )
    
    # Log activity for quote conversion
    activity = JobActivity(
        job_id=job.id,
        activity_type=JobActivityType.QUOTE_CONVERTED,
        description=f"Job created from Quote #{quote_id[:8]}",
        new_value=quote_id
    )
    await db.job_activities.insert_one(activity.model_dump())
    
    return job


@router.post("/{quote_id}/send")
async def send_quote(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Mark quote as sent"""
    quote = await db.quotes.find_one(
        {"id": quote_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    await db.quotes.update_one(
        {"id": quote_id},
        {"$set": {
            "status": QuoteStatus.SENT.value,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Quote marked as sent"}
