"""
Invoice Management Routes

This module contains all routes related to:
- Invoice CRUD operations
- Invoice from Job creation
- Payment recording
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone

from models import (
    Invoice, InvoiceCreate, InvoiceUpdate, InvoiceLineItem, InvoiceStatus,
    JobActivityType,
    UserInDB, Permission
)

# Import from server module
from server import (
    db, logger,
    get_current_active_user, has_permission, log_job_activity
)

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("", response_model=Invoice)
async def create_invoice(
    input: InvoiceCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new invoice"""
    invoice = Invoice(**input.model_dump())
    invoice.tenant_id = current_user.tenant_id
    doc = invoice.model_dump()
    await db.invoices.insert_one(doc)
    
    # Link invoice to job if job_id provided
    if input.job_id:
        await db.jobs.update_one({"id": input.job_id}, {"$set": {"invoice_id": invoice.id}})
    
    return invoice


@router.get("", response_model=List[Invoice])
async def get_invoices(
    customer_id: Optional[str] = None,
    status: Optional[InvoiceStatus] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all invoices with optional filtering"""
    query = {"tenant_id": current_user.tenant_id}
    if customer_id:
        query["customer_id"] = customer_id
    if status:
        query["status"] = status.value
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific invoice by ID"""
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(
    invoice_id: str, 
    input: InvoiceUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update an invoice"""
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Recalculate total if line items changed
    if "line_items" in update_data:
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
    
    # If marking as paid, set paid_date
    if input.status == InvoiceStatus.PAID:
        update_data["paid_date"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.invoices.update_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    return invoice


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete an invoice"""
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Unlink from job if linked
    if invoice.get("job_id"):
        await db.jobs.update_one(
            {"id": invoice["job_id"]},
            {"$unset": {"invoice_id": ""}}
        )
    
    result = await db.invoices.delete_one({"id": invoice_id})
    return {"message": "Invoice deleted"}


@router.post("/from-job/{job_id}", response_model=Invoice)
async def create_invoice_from_job(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create an invoice from a job"""
    job = await db.jobs.find_one(
        {"id": job_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get job items from job_items collection
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    
    invoice_line_items = []
    total = 0
    
    if job_items:
        # Create line items from job_items collection
        for item in job_items:
            line_item = InvoiceLineItem(
                description=item.get("description", ""),
                quantity=item.get("quantity", 1),
                unit_price=item.get("unit_price", 0),
                total=item.get("line_total", 0),
                job_item_id=item.get("id")
            )
            invoice_line_items.append(line_item)
            total += item.get("line_total", 0)
    elif job.get("line_items") and len(job.get("line_items", [])) > 0:
        # Fallback to line_items stored directly in job document (from quote/job creation)
        for item in job.get("line_items", []):
            qty = float(item.get("quantity", 1))
            unit_price = float(item.get("unit_price", 0))
            line_total = qty * unit_price
            line_item = InvoiceLineItem(
                description=item.get("description", ""),
                quantity=qty,
                unit_price=unit_price,
                total=line_total
            )
            invoice_line_items.append(line_item)
            total += line_total
    else:
        # Final fallback to job subtotal or quote total
        total = job.get("subtotal", 0)
        if total == 0 and job.get("quote_id"):
            quote = await db.quotes.find_one({"id": job["quote_id"]}, {"_id": 0})
            if quote:
                total = quote.get("total", 0)
    
    invoice = Invoice(
        customer_id=job["customer_id"],
        job_id=job_id,
        line_items=invoice_line_items,
        total=total,
        tenant_id=current_user.tenant_id,
        status=InvoiceStatus.DRAFT
    )
    doc = invoice.model_dump()
    await db.invoices.insert_one(doc)
    
    # Update job with invoice_id
    await db.jobs.update_one({"id": job_id}, {"$set": {"invoice_id": invoice.id}})
    
    # Log activity
    await log_job_activity(job_id, JobActivityType.INVOICE_CREATED, f"Invoice created for ${total:.2f}", new_value=invoice.id)
    
    return invoice


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Mark invoice as sent"""
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "status": InvoiceStatus.SENT.value,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Invoice marked as sent"}


@router.post("/{invoice_id}/send-to-portal")
async def send_invoice_to_portal(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Send invoice to customer portal.
    Makes the invoice visible in the customer's portal and creates a notification.
    """
    from models import CustomerNotification
    
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get customer info for notification
    customer = await db.customers.find_one(
        {"id": invoice["customer_id"]},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if customer has portal enabled
    if not customer.get("portal_enabled"):
        raise HTTPException(
            status_code=400, 
            detail="Customer does not have portal access enabled. Enable portal access for this customer first."
        )
    
    # Update invoice to mark as portal visible and set status to sent
    update_data = {
        "portal_visible": True,
        "portal_sent_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Also update status to sent if it's still draft
    if invoice.get("status") == "draft":
        update_data["status"] = InvoiceStatus.SENT.value
        update_data["sent_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": update_data}
    )
    
    # Create notification for customer
    notification = CustomerNotification(
        tenant_id=current_user.tenant_id,
        customer_id=invoice["customer_id"],
        notification_type="invoice",
        title="New Invoice Available",
        message=f"Invoice #{invoice_id[:8].upper()} for ${invoice.get('total', 0):.2f} is now available in your portal.",
        related_id=invoice_id
    )
    await db.customer_notifications.insert_one(notification.model_dump())
    
    logger.info(f"Invoice {invoice_id} sent to portal for customer {invoice['customer_id']}")
    
    return {
        "message": "Invoice sent to customer portal",
        "portal_url": f"/portal/invoices",
        "customer_name": customer.get("name"),
        "customer_email": customer.get("email")
    }


@router.post("/{invoice_id}/record-payment")
async def record_payment(
    invoice_id: str,
    amount: float,
    payment_method: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Record a manual payment on an invoice.
    
    BUSINESS RULE: Manual payments have NO platform fee.
    Platform fees apply ONLY when the platform processes the payment (Stripe).
    Manual payments (cash/check/external) bypass platform processing.
    """
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    new_amount_paid = invoice.get("amount_paid", 0) + amount
    grand_total = invoice.get("grand_total", invoice.get("total", 0))
    
    # Update status based on payment
    if new_amount_paid >= grand_total:
        new_status = InvoiceStatus.PAID.value
    else:
        new_status = invoice.get("status", InvoiceStatus.SENT.value)
    
    await db.invoices.update_one(
        {"id": invoice_id},
        {"$set": {
            "amount_paid": new_amount_paid,
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Record payment in payments collection
    # Manual payments intentionally have platform_fee = 0.00
    # Fees only apply to platform-processed (Stripe) payments
    payment_record = {
        "invoice_id": invoice_id,
        "tenant_id": current_user.tenant_id,
        "amount": amount,
        "platform_fee": 0.00,
        "platform_fee_percent": 0.0,
        "platform_fee_reason": "manual_payment_no_platform_processing",
        "payment_method": payment_method or "manual",
        "payment_type": "manual",
        "notes": notes,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payments.insert_one(payment_record)
    
    return {
        "message": f"Payment of ${amount:.2f} recorded",
        "new_balance": grand_total - new_amount_paid,
        "status": new_status,
        "platform_fee": 0.00
    }


@router.get("/{invoice_id}/payments")
async def get_invoice_payments(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all payments for an invoice"""
    payments = await db.payments.find({"invoice_id": invoice_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payments
