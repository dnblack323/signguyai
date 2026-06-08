"""
Quote Management Routes

This module contains all routes related to:
- Quote CRUD operations
- Quote to Job conversion
- Quote PDF download (admin)
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
from services.email_service import EmailService

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
    await collection.update_one({"id": quote_id, "tenant_id": current_user.tenant_id}, {"$set": update_data})
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
    
    await collection.delete_one({"id": quote_id, "tenant_id": current_user.tenant_id})
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
    """Mark quote as sent and email the customer"""
    quote, collection = await _find_quote_document(quote_id, current_user.tenant_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    
    now = datetime.now(timezone.utc).isoformat()
    await collection.update_one(
        {"id": quote_id},
        {"$set": {
            "status": QuoteStatus.SENT.value,
            "sent_at": now,
            "updated_at": now
        }}
    )

    # Attempt to email the customer
    email_result = {"sent": False, "reason": "No customer email"}
    customer_id = quote.get("customer_id")
    if customer_id:
        customer = await db.customers.find_one(
            {"id": customer_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "email": 1, "name": 1, "company_name": 1}
        )
        if customer and customer.get("email"):
            quote_number = quote.get("quote_number") or quote.get("id", "")[:8].upper()
            total = quote.get("total", 0)
            customer_name = customer.get("name") or customer.get("company_name") or "Valued Customer"
            line_items_html = "".join(
                f"<tr><td style='padding:6px 12px;border-bottom:1px solid #eee'>{item.get('description','')}</td>"
                f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right'>{item.get('quantity',1)}</td>"
                f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right'>${item.get('unit_price',0):.2f}</td>"
                f"<td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:right'>${item.get('total',0):.2f}</td></tr>"
                for item in (quote.get("line_items") or [])
            )
            html_content = f"""
<div style="font-family:Arial,sans-serif;max-width:640px;margin:0 auto;color:#333">
  <h2 style="color:#1a1a2e">Quote #{quote_number}</h2>
  <p>Hi {customer_name},</p>
  <p>Please find your quote details below. Feel free to reply with any questions.</p>
  <table style="width:100%;border-collapse:collapse;margin:16px 0">
    <thead>
      <tr style="background:#f5f5f5">
        <th style="padding:8px 12px;text-align:left">Description</th>
        <th style="padding:8px 12px;text-align:right">Qty</th>
        <th style="padding:8px 12px;text-align:right">Unit Price</th>
        <th style="padding:8px 12px;text-align:right">Total</th>
      </tr>
    </thead>
    <tbody>{line_items_html}</tbody>
    <tfoot>
      <tr>
        <td colspan="3" style="padding:10px 12px;font-weight:bold;text-align:right">Total</td>
        <td style="padding:10px 12px;font-weight:bold;text-align:right">${total:.2f}</td>
      </tr>
    </tfoot>
  </table>
  {f'<p style="color:#555"><em>Notes: {quote.get("notes")}</em></p>' if quote.get("notes") else ""}
  <p style="margin-top:24px;color:#888;font-size:12px">
    This quote is valid for 30 days. Thank you for your business!
  </p>
</div>
"""
            email_svc = EmailService()
            result = await email_svc.send_email(
                to_email=customer["email"],
                subject=f"Your Quote #{quote_number} is Ready",
                html_content=html_content,
                tenant_id=current_user.tenant_id,
            )
            email_result = {"sent": result.get("success", False), "reason": result.get("error")}

    return {"message": "Quote marked as sent", "email": email_result}


@router.get("/{quote_id}/pdf")
async def download_quote_pdf(
    quote_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Download quote PDF (admin-side)."""
    quote, _collection = await _find_quote_document(quote_id, current_user.tenant_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    customer = None
    if quote.get("customer_id"):
        customer = await db.customers.find_one(
            {"id": quote["customer_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0}
        )

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    company_name = (tenant or {}).get("name") or "Sign Shop"
    elements.append(Paragraph(f"<b>{company_name}</b>", styles['Title']))
    if tenant:
        addr_parts = [tenant.get(k) for k in ("address", "city", "state", "zip_code") if tenant.get(k)]
        if addr_parts:
            elements.append(Paragraph(" • ".join(addr_parts), styles['BodyText']))
        if tenant.get("phone"):
            elements.append(Paragraph(f"Phone: {tenant['phone']}", styles['BodyText']))
    elements.append(Spacer(1, 16))

    # Quote header
    quote_number = quote.get("quote_number") or quote_id[:8].upper()
    status = (quote.get("status") or "draft").upper()
    elements.append(Paragraph(f"<b>QUOTE #{quote_number}</b>  <font color='#0D9488'>[{status}]</font>", styles['Heading2']))
    elements.append(Paragraph(f"Date: {(quote.get('created_at') or '')[:10]}", styles['BodyText']))
    if quote.get("expiration_date"):
        elements.append(Paragraph(f"Valid until: {quote['expiration_date']}", styles['BodyText']))
    elements.append(Spacer(1, 12))

    # For
    if customer:
        elements.append(Paragraph("<b>For:</b>", styles['BodyText']))
        elements.append(Paragraph(customer.get("name") or "", styles['BodyText']))
        if customer.get("company"):
            elements.append(Paragraph(customer["company"], styles['BodyText']))
        if customer.get("email"):
            elements.append(Paragraph(customer["email"], styles['BodyText']))
        elements.append(Spacer(1, 12))

    # Line items
    table_data = [["Description", "Qty", "Unit Price", "Total"]]
    for item in quote.get("line_items", []):
        table_data.append([
            item.get("description", "Item"),
            str(item.get("quantity", 1)),
            f"${item.get('unit_price', 0):.2f}",
            f"${item.get('total', 0):.2f}",
        ])
    subtotal = float(quote.get("subtotal", 0) or 0)
    tax_amount = float(quote.get("tax_amount", 0) or 0)
    grand_total = float(quote.get("grand_total", quote.get("total", 0)) or 0)
    table_data.append(["", "", "Subtotal", f"${subtotal:.2f}"])
    if tax_amount:
        table_data.append(["", "", f"Tax ({quote.get('tax_rate', 0):.2f}%)", f"${tax_amount:.2f}"])
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

    if quote.get("notes"):
        elements.append(Paragraph(f"<b>Notes:</b> {quote['notes']}", styles['BodyText']))
    if quote.get("terms"):
        elements.append(Paragraph(f"<b>Terms:</b> {quote['terms']}", styles['BodyText']))

    doc.build(elements)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=quote_{quote_number}.pdf"}
    )
