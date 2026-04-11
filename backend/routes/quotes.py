"""
Quote Management Routes

This module contains all routes related to:
- Quote CRUD operations
- Quote to Job conversion
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

router = APIRouter(prefix="/quotes", tags=["Quotes"])


async def _find_quote_document(quote_id: str, tenant_id: str):
    quote = await db.quotes.find_one({"id": quote_id, "tenant_id": tenant_id}, {"_id": 0})
    if quote:
        return quote, db.quotes
    legacy_quote = await db.order_quotes.find_one(
        {"id": quote_id, "tenant_id": tenant_id, "type": "quote"},
        {"_id": 0},
    )
    if legacy_quote:
        return legacy_quote, db.order_quotes
    return None, None


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
            total=item_total,
            pricing_category=getattr(item, "pricing_category", None),
            pricing_data=getattr(item, "pricing_data", None),
            cost_snapshot=getattr(item, "cost_snapshot", None),
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
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all quotes with optional filtering"""
    query = {"tenant_id": current_user.tenant_id}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    quotes = await db.quotes.find(query, {"_id": 0}).to_list(1000)
    legacy_query = {**query, "type": "quote"}
    legacy_quotes = await db.order_quotes.find(legacy_query, {"_id": 0}).to_list(1000)
    seen_ids = {quote["id"] for quote in quotes}
    quotes.extend(quote for quote in legacy_quotes if quote["id"] not in seen_ids)
    return sorted(quotes, key=lambda quote: quote.get("created_at", ""), reverse=True)


@router.get("/{quote_id}", response_model=Quote)
async def get_quote(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific quote by ID"""
    quote, _collection = await _find_quote_document(quote_id, current_user.tenant_id)
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
    quote, collection = await _find_quote_document(quote_id, current_user.tenant_id)
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
    await collection.update_one({"id": quote_id}, {"$set": update_data})
    updated_quote, _collection = await _find_quote_document(quote_id, current_user.tenant_id)
    return updated_quote


@router.delete("/{quote_id}")
async def delete_quote(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a quote"""
    quote, collection = await _find_quote_document(quote_id, current_user.tenant_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if quote.get("job_id"):
        raise HTTPException(status_code=400, detail="Cannot delete quote that has been converted to job")
    
    await collection.delete_one({"id": quote_id})
    return {"message": "Quote deleted"}


@router.post("/{quote_id}/convert-to-job", response_model=Job)
async def convert_quote_to_job(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Convert a quote to a job"""
    quote, collection = await _find_quote_document(quote_id, current_user.tenant_id)
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
            status=JobItemStatus.PENDING,
            pricing_category=item.get("pricing_category"),
            pricing_data=item.get("pricing_data"),
            cost_snapshot=item.get("cost_snapshot"),
            production_cost=(item.get("cost_snapshot") or {}).get("total_cost", 0),
            profit_amount=(item.get("cost_snapshot") or {}).get("profit_amount", 0),
            profit_margin_percent=(item.get("cost_snapshot") or {}).get("profit_margin_percent", 0),
        )
        await db.job_items.insert_one(job_item.model_dump())
    
    # Update quote with job_id
    await collection.update_one(
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
    quote, collection = await _find_quote_document(quote_id, current_user.tenant_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    await collection.update_one(
        {"id": quote_id},
        {"$set": {
            "status": QuoteStatus.SENT.value,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Quote marked as sent"}
