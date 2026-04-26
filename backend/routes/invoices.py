"""
Invoice Management Routes

This module contains all routes related to:
- Invoice CRUD operations
- Invoice from Job creation
- Payment recording
- Invoice PDF download (admin)
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timezone
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

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
from routes.jobs import sync_job_items_from_embedded_line_items

router = APIRouter(prefix="/invoices", tags=["Invoices"])


async def _find_invoice_document(invoice_id: str, tenant_id: str):
    invoice = await db.invoices.find_one({"id": invoice_id, "tenant_id": tenant_id}, {"_id": 0})
    if invoice:
        return invoice, db.invoices
    legacy_invoice = await db.order_quotes.find_one(
        {"id": invoice_id, "tenant_id": tenant_id, "type": "invoice"},
        {"_id": 0},
    )
    if legacy_invoice:
        return legacy_invoice, db.order_quotes
    return None, None


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
    legacy_query = {**query, "type": "invoice"}
    legacy_invoices = await db.order_quotes.find(legacy_query, {"_id": 0}).to_list(1000)
    seen_ids = {invoice["id"] for invoice in invoices}
    invoices.extend(invoice for invoice in legacy_invoices if invoice["id"] not in seen_ids)
    return sorted(invoices, key=lambda invoice: invoice.get("created_at", ""), reverse=True)


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific invoice by ID"""
    invoice, _collection = await _find_invoice_document(invoice_id, current_user.tenant_id)
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
    
    _invoice, collection = await _find_invoice_document(invoice_id, current_user.tenant_id)
    if not _invoice or collection is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    result = await collection.update_one(
        {"id": invoice_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice, _collection = await _find_invoice_document(invoice_id, current_user.tenant_id)
    return invoice


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete an invoice"""
    invoice, collection = await _find_invoice_document(invoice_id, current_user.tenant_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Unlink from job if linked
    if invoice.get("job_id"):
        await db.jobs.update_one(
            {"id": invoice["job_id"]},
            {"$unset": {"invoice_id": ""}}
        )
    
    await collection.delete_one({"id": invoice_id})
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
    
    # Get job items and create invoice line items
    job_items = await sync_job_items_from_embedded_line_items(job)
    
    invoice_line_items = []
    total = 0
    
    if job_items:
        # Create line items from job items
        for item in job_items:
            line_item = InvoiceLineItem(
                description=item.get("description", ""),
                quantity=item.get("quantity", 1),
                unit_price=item.get("unit_price", 0),
                total=item.get("line_total", 0),
                job_item_id=item.get("id"),
                pricing_category=item.get("pricing_category"),
                cost_snapshot=item.get("cost_snapshot"),
            )
            invoice_line_items.append(line_item)
            total += item.get("line_total", 0)
    else:
        # Fallback to job subtotal or quote total
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
    invoice, collection = await _find_invoice_document(invoice_id, current_user.tenant_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    await collection.update_one(
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
    
    invoice, _collection = await _find_invoice_document(invoice_id, current_user.tenant_id)
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
        "portal_url": "/portal/invoices",
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


def _render_invoice_pdf(invoice: dict, tenant: dict, customer: Optional[dict]) -> BytesIO:
    """Render invoice as a PDF document. Shared helper for admin + portal."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # Header — company + invoice meta
    company_name = (tenant or {}).get("name") or "Sign Shop"
    elements.append(Paragraph(f"<b>{company_name}</b>", styles['Title']))
    if tenant:
        addr_parts = [tenant.get(k) for k in ("address", "city", "state", "zip_code") if tenant.get(k)]
        if addr_parts:
            elements.append(Paragraph(" • ".join(addr_parts), styles['BodyText']))
        if tenant.get("phone"):
            elements.append(Paragraph(f"Phone: {tenant['phone']}", styles['BodyText']))
    elements.append(Spacer(1, 16))

    # Invoice header
    invoice_number = invoice.get("invoice_number") or invoice.get("id", "")[:8].upper()
    status = (invoice.get("status") or "draft").upper()
    watermark = "PAID" if status == "PAID" else "UNPAID"
    elements.append(Paragraph(f"<b>INVOICE #{invoice_number}</b>  <font color='{ '#10B981' if watermark == 'PAID' else '#EF4444'}'>[{watermark}]</font>", styles['Heading2']))
    elements.append(Paragraph(f"Date: {(invoice.get('created_at') or '')[:10]}", styles['BodyText']))
    if invoice.get("due_date"):
        elements.append(Paragraph(f"Due: {invoice['due_date']}", styles['BodyText']))
    elements.append(Spacer(1, 12))

    # Bill-to
    if customer:
        elements.append(Paragraph("<b>Bill To:</b>", styles['BodyText']))
        elements.append(Paragraph(customer.get("name") or "", styles['BodyText']))
        if customer.get("company"):
            elements.append(Paragraph(customer["company"], styles['BodyText']))
        if customer.get("email"):
            elements.append(Paragraph(customer["email"], styles['BodyText']))
        elements.append(Spacer(1, 12))

    # Line items
    table_data = [["Description", "Qty", "Unit Price", "Total"]]
    for item in invoice.get("line_items", []):
        table_data.append([
            item.get("description", "Item"),
            str(item.get("quantity", 1)),
            f"${item.get('unit_price', 0):.2f}",
            f"${item.get('total', 0):.2f}",
        ])
    subtotal = float(invoice.get("subtotal", 0) or 0)
    tax_amount = float(invoice.get("tax_amount", 0) or 0)
    grand_total = float(invoice.get("grand_total", invoice.get("total", 0)) or 0)
    table_data.append(["", "", "Subtotal", f"${subtotal:.2f}"])
    if tax_amount:
        table_data.append(["", "", f"Tax ({invoice.get('tax_rate', 0):.2f}%)", f"${tax_amount:.2f}"])
    table_data.append(["", "", "Total", f"${grand_total:.2f}"])

    table = Table(table_data, colWidths=[280, 50, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 18))

    if invoice.get("notes"):
        elements.append(Paragraph(f"<b>Notes:</b> {invoice['notes']}", styles['BodyText']))
    if invoice.get("terms"):
        elements.append(Paragraph(f"<b>Terms:</b> {invoice['terms']}", styles['BodyText']))

    doc.build(elements)
    output.seek(0)
    return output


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Download invoice PDF (admin-side, no portal login required)."""
    invoice, _collection = await _find_invoice_document(invoice_id, current_user.tenant_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    customer = None
    if invoice.get("customer_id"):
        customer = await db.customers.find_one(
            {"id": invoice["customer_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0}
        )

    pdf = _render_invoice_pdf(invoice, tenant or {}, customer)
    invoice_number = invoice.get("invoice_number") or invoice_id[:8].upper()
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_number}.pdf"}
    )
