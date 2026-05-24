"""
Orders API Routes

CRUD for the master Order record (Layer 1).
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from io import BytesIO
import uuid
import base64
import mimetypes

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether

from server import db, get_current_active_user
from models import UserInDB
from models.orders import (
    Order, OrderCreate, OrderUpdate, OrderStatus, PaymentStatus
)
from services.workflow_engine import update_order_progress, log_activity
from services.object_storage import get_object, put_object
from services.storage_config import APP_NAME

router = APIRouter(prefix="/orders", tags=["Orders"])


def _build_order_file_storage_path(tenant_id: str, order_id: str, file_id: str, filename: str) -> str:
    guessed_extension = mimetypes.guess_extension(mimetypes.guess_type(filename or "")[0] or "") or ""
    if not guessed_extension and filename and "." in filename:
        guessed_extension = f".{filename.rsplit('.', 1)[-1]}"
    return f"{APP_NAME}/orders/{tenant_id}/{order_id}/files/{file_id}{guessed_extension or '.bin'}"


async def _migrate_order_file_to_storage(file_doc: dict) -> str | None:
    if file_doc.get("storage_path") or not file_doc.get("file_data"):
        return file_doc.get("storage_path")

    content = base64.b64decode(file_doc["file_data"])
    storage_path = _build_order_file_storage_path(
        file_doc["tenant_id"],
        file_doc["order_id"],
        file_doc["id"],
        file_doc.get("filename") or "attachment.bin",
    )
    result = put_object(storage_path, content, file_doc.get("content_type") or "application/octet-stream")
    stored_path = result.get("path", storage_path)
    await db.order_files.update_one(
        {"id": file_doc["id"], "order_id": file_doc["order_id"], "tenant_id": file_doc["tenant_id"]},
        {"$set": {
            "storage_path": stored_path,
            "storage_backend": "emergent_object_storage",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return stored_path


async def _next_order_number(tenant_id: str) -> str:
    last = await db.orders.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "order_number": 1}
    ).sort("date_created", -1).limit(1).to_list(1)
    if last and last[0].get("order_number"):
        try:
            num = int(last[0]["order_number"].split("-")[-1])
            return f"ORD-{num + 1:04d}"
        except (ValueError, IndexError):
            pass
    count = await db.orders.count_documents({"tenant_id": tenant_id})
    return f"ORD-{count + 1:04d}"


@router.get("")
async def list_orders(
    status: Optional[str] = None,
    is_archived: bool = False,
    limit: int = 50,
    skip: int = 0,
    search: Optional[str] = None,
    source: Optional[str] = None,
    webstore_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
):
    query = {"tenant_id": current_user.tenant_id, "is_archived": is_archived}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"order_number": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
        ]
    # Phase 4 — optional safe filter hooks for webstore-sourced orders.
    # `source=webstore` mirrors the new explicit marker on the order document,
    # while also matching legacy rows where only `is_webstore_order=true` was set.
    if source:
        if source.lower() == "webstore":
            query["$and"] = query.get("$and", []) + [{
                "$or": [{"source": "webstore"}, {"is_webstore_order": True}],
            }]
        else:
            query["source"] = source
    if webstore_id:
        query["webstore_id"] = webstore_id

    orders = await db.orders.find(query, {"_id": 0}).sort("date_created", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.orders.count_documents(query)
    return {"orders": orders, "total": total}


@router.get("/{order_id}")
async def get_order(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    order = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Enrich with job tickets summary
    tickets = await db.job_tickets.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).to_list(100)

    order["job_tickets"] = tickets
    return order


@router.post("")
async def create_order(data: OrderCreate, current_user: UserInDB = Depends(get_current_active_user)):
    payload = data.model_dump(exclude_none=True)
    # H5: Restrict client-settable initial status to safe values only.
    if payload.get("status") and payload["status"] not in {OrderStatus.DRAFT.value, OrderStatus.NEW_INTAKE.value}:
        raise HTTPException(status_code=400, detail="Invalid initial status — only 'draft' or 'new_intake' allowed")
    order = Order(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **payload
    )
    order.order_number = await _next_order_number(current_user.tenant_id)

    # Auto-generate order name if not provided
    if not order.name or order.name.strip() == '':
        customer = await db.customers.find_one(
            {"id": order.customer_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "display_name": 1, "company": 1, "name": 1}
        ) if order.customer_id else None
        display = (customer or {}).get("display_name") or (customer or {}).get("company") or (customer or {}).get("name") or "ORDER"
        display_clean = display.replace(" ", "").upper()
        today = datetime.now(timezone.utc).strftime("%m%d%y")
        base_name = f"{display_clean}-{today}"
        # Check for same-day duplicates and add suffix letter
        existing_count = await db.orders.count_documents({
            "tenant_id": current_user.tenant_id,
            "name": {"$regex": f"^{base_name}"}
        })
        if existing_count > 0:
            suffix = chr(ord('a') + existing_count)
            order.name = f"{base_name}{suffix}"
        else:
            order.name = base_name

    doc = order.model_dump()
    await db.orders.insert_one(doc)

    await log_activity(db, order.id, current_user.tenant_id, "order", order.id,
                       "created", f"Order {order.order_number} created",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    doc.pop("_id", None)
    return doc


@router.put("/{order_id}")
async def update_order(order_id: str, data: OrderUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Log status changes
    if "status" in update_data and update_data["status"] != existing.get("status"):
        await log_activity(db, order_id, current_user.tenant_id, "order", order_id,
                           "status_change", f"Status changed from {existing.get('status')} to {update_data['status']}",
                           user_id=current_user.id, user_name=current_user.full_name or "",
                           old_value=existing.get("status"), new_value=update_data["status"])

    if "status" in update_data and update_data["status"] == OrderStatus.COMPLETED.value:
        update_data["final_completion_date"] = datetime.now(timezone.utc).isoformat()

    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    updated = await db.orders.find_one({"id": order_id}, {"_id": 0})
    return updated


@router.delete("/{order_id}")
async def delete_order(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Order not found")

    await db.orders.delete_one({"id": order_id})
    await db.job_tickets.delete_many({"order_id": order_id, "tenant_id": current_user.tenant_id})
    await db.production_tasks.delete_many({"order_id": order_id, "tenant_id": current_user.tenant_id})
    await db.order_activities.delete_many({"order_id": order_id})
    return {"message": "Order and related records deleted"}


@router.post("/{order_id}/generate-quote")
async def generate_quote_from_order(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Generate a quote/invoice from job tickets attached to this order."""
    order = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tickets = await db.job_tickets.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).to_list(100)

    if not tickets:
        raise HTTPException(status_code=400, detail="No job tickets to generate quote from")

    line_items = []
    subtotal = 0.0
    for t in tickets:
        snapshot = t.get("pricing_snapshot") or {}
        price = snapshot.get("active_price") or t.get("estimated_price", 0)
        line_items.append({
            "description": f"{t.get('item_name', 'Item')} — {t.get('item_category', '')} (Qty: {t.get('quantity', 1)})",
            "quantity": t.get("quantity", 1),
            "unit_price": price / max(t.get("quantity", 1), 1),
            "total": price,
            "job_ticket_id": t["id"],
        })
        subtotal += price

    quote_id = str(uuid.uuid4())
    quote_doc = {
        "id": quote_id,
        "tenant_id": current_user.tenant_id,
        "order_id": order_id,
        "customer_id": order.get("customer_id", ""),
        "customer_name": order.get("customer_name", ""),
        "status": "draft",
        "line_items": line_items,
        "total": subtotal,
        "notes": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "order",
    }
    await db.quotes.insert_one(quote_doc)

    # Link to order
    await db.orders.update_one(
        {"id": order_id},
        {"$push": {"linked_quote_ids": quote_id}, "$set": {"status": OrderStatus.AWAITING_QUOTE.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    await log_activity(db, order_id, current_user.tenant_id, "quote", quote_id,
                       "created", f"Quote generated from {len(tickets)} job ticket(s), total ${subtotal:.2f}",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    quote_doc.pop("_id", None)
    return quote_doc


@router.post("/{order_id}/start-production")
async def start_production(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Activate production for all workflow-enabled job tickets in this order."""
    order = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    from services.workflow_engine import generate_production_tasks, seed_default_templates

    await seed_default_templates(db, current_user.tenant_id)

    tickets = await db.job_tickets.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id, "production_flow_enabled": True},
        {"_id": 0}
    ).to_list(100)

    tasks_created = 0
    for ticket in tickets:
        existing_tasks = await db.production_tasks.count_documents({"job_ticket_id": ticket["id"]})
        if existing_tasks == 0:
            tasks = await generate_production_tasks(db, ticket, current_user.tenant_id)
            tasks_created += len(tasks)
            if tasks:
                await db.job_tickets.update_one(
                    {"id": ticket["id"]},
                    {"$set": {"status": "queued", "updated_at": datetime.now(timezone.utc).isoformat()}}
                )

    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": OrderStatus.IN_PRODUCTION.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    await log_activity(db, order_id, current_user.tenant_id, "order", order_id,
                       "production_started", f"Production started: {tasks_created} tasks created for {len(tickets)} ticket(s)",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    return {"message": "Production started", "tickets_activated": len(tickets), "tasks_created": tasks_created}


@router.get("/{order_id}/activity")
async def get_order_activity(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    activities = await db.order_activities.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return activities


@router.post("/{order_id}/generate-invoice")
async def generate_invoice_from_order(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Generate an invoice from job tickets attached to this order."""
    order = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tickets = await db.job_tickets.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).to_list(100)

    if not tickets:
        raise HTTPException(status_code=400, detail="No job tickets to generate invoice from")

    line_items = []
    subtotal = 0.0
    for t in tickets:
        snapshot = t.get("pricing_snapshot") or {}
        price = snapshot.get("active_price") or t.get("estimated_price", 0)
        line_items.append({
            "description": f"{t.get('item_name', 'Item')} — {t.get('item_category', '')} (Qty: {t.get('quantity', 1)})",
            "quantity": t.get("quantity", 1),
            "unit_price": price / max(t.get("quantity", 1), 1),
            "total": price,
            "job_ticket_id": t["id"],
        })
        subtotal += price

    # Fetch tenant default tax rate and customer tax-exempt status
    tenant_doc = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "default_tax_rate": 1})
    default_tax_rate = float(tenant_doc.get("default_tax_rate") or 0) if tenant_doc else 0.0
    customer_doc = await db.customers.find_one({"id": order.get("customer_id", ""), "tenant_id": current_user.tenant_id}, {"_id": 0, "is_tax_exempt": 1})
    is_tax_exempt = bool((customer_doc or {}).get("is_tax_exempt", False))
    tax_rate_applied = 0.0 if is_tax_exempt else default_tax_rate
    tax_amount = round(subtotal * (tax_rate_applied / 100), 2)
    grand_total = round(subtotal + tax_amount, 2)

    invoice_id = str(uuid.uuid4())
    invoice_doc = {
        "id": invoice_id,
        "tenant_id": current_user.tenant_id,
        "order_id": order_id,
        "customer_id": order.get("customer_id", ""),
        "customer_name": order.get("customer_name", ""),
        "status": "draft",
        "total": subtotal,
        "line_items": [
            {
                **item,
                "job_item_id": item.get("job_ticket_id"),
            }
            for item in line_items
        ],
        "tax_amount": tax_amount,
        "tax_rate": tax_rate_applied,
        "is_tax_exempt": is_tax_exempt,
        "discount_amount": 0,
        "grand_total": grand_total,
        "amount_paid": 0,
        "notes": "",
        "due_date": order.get("requested_due_date"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": "order",
    }
    await db.invoices.insert_one(invoice_doc)

    await db.orders.update_one(
        {"id": order_id},
        {"$push": {"linked_invoice_ids": invoice_id}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    )

    await log_activity(db, order_id, current_user.tenant_id, "invoice", invoice_id,
                       "created", f"Invoice generated from {len(tickets)} job ticket(s), total ${subtotal:.2f}",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    invoice_doc.pop("_id", None)
    return invoice_doc



@router.post("/{order_id}/generate-work_order")
async def generate_work_order(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Generate a production work order from job tickets — includes full specs and production details."""
    order = await db.orders.find_one({"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tickets = await db.job_tickets.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    ).to_list(100)

    if not tickets:
        raise HTTPException(status_code=400, detail="No job tickets to generate work order from")

    work_order_id = str(uuid.uuid4())
    ticket_details = []
    for t in tickets:
        specs = t.get("specs", {})
        detail = {
            "ticket_number": t.get("ticket_number", ""),
            "item_name": t.get("item_name", ""),
            "category": t.get("item_category", ""),
            "quantity": t.get("quantity", 1),
            "priority": t.get("priority", "normal"),
            "specs": specs,
            "special_instructions": t.get("special_instructions", ""),
            "production_notes": t.get("production_notes", ""),
            "install_notes": t.get("install_notes", ""),
            "design_needed": t.get("design_needed", False),
            "proof_required": t.get("proof_required", False),
            "production_flow_enabled": t.get("production_flow_enabled", False),
        }
        ticket_details.append(detail)

    work_order_doc = {
        "id": work_order_id,
        "tenant_id": current_user.tenant_id,
        "order_id": order_id,
        "order_number": order.get("order_number", ""),
        "customer_name": order.get("customer_name", ""),
        "company_name": order.get("company_name", ""),
        "type": "work_order",
        "status": "draft",
        "requested_due_date": order.get("requested_due_date"),
        "pickup_delivery_method": order.get("pickup_delivery_method", "pickup"),
        "internal_notes": order.get("internal_notes", ""),
        "tickets": ticket_details,
        "total_tickets": len(ticket_details),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.order_quotes.insert_one(work_order_doc)

    await log_activity(db, order_id, current_user.tenant_id, "work_order", work_order_id,
                       "created", f"Work order generated with {len(ticket_details)} ticket(s)",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    work_order_doc.pop("_id", None)
    return work_order_doc


@router.get("/{order_id}/financials")
async def get_order_financials(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get all quotes, invoices, and work orders linked to this order."""
    order = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    legacy_docs = await db.order_quotes.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    quotes = await db.quotes.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    invoices = await db.invoices.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    work_orders = [d for d in legacy_docs if d.get("type") == "work_order"]

    legacy_quotes = [d for d in legacy_docs if d.get("type") == "quote"]
    legacy_invoices = [d for d in legacy_docs if d.get("type") == "invoice"]
    quote_ids = {doc["id"] for doc in quotes}
    invoice_ids = {doc["id"] for doc in invoices}
    quotes.extend(doc for doc in legacy_quotes if doc["id"] not in quote_ids)
    invoices.extend(doc for doc in legacy_invoices if doc["id"] not in invoice_ids)
    docs = quotes + invoices + work_orders

    return {
        "quotes": quotes,
        "invoices": invoices,
        "work_orders": work_orders,
        "total_documents": len(docs),
    }


@router.get("/{order_id}/production-summary")
async def get_order_production_summary(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get all production tasks across all tickets for this order."""
    tasks = await db.production_tasks.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("stage_sequence", 1).to_list(500)

    tickets = await db.job_tickets.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1, "item_name": 1, "ticket_number": 1, "status": 1, "progress": 1, "item_category": 1}
    ).to_list(100)

    # Group tasks by ticket
    by_ticket = {}
    for task in tasks:
        tid = task.get("job_ticket_id", "")
        by_ticket.setdefault(tid, []).append(task)

    # Group by department
    by_dept = {}
    for task in tasks:
        dept = task.get("department", "unassigned")
        by_dept.setdefault(dept, []).append(task)

    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "complete")
    on_hold = sum(1 for t in tasks if t.get("status") in ("on_hold", "rework"))

    return {
        "tasks": tasks,
        "by_ticket": by_ticket,
        "by_department": by_dept,
        "tickets": tickets,
        "summary": {
            "total_tasks": total,
            "completed": completed,
            "on_hold": on_hold,
            "progress": round((completed / total) * 100, 1) if total > 0 else 0,
        }
    }



@router.post("/{order_id}/upload")
async def upload_order_file(
    order_id: str,
    file: UploadFile = File(...),
    label: str = Form(""),
    category: str = Form("artwork"),
    tags: str = Form(""),
    is_shared: bool = Form(True),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Upload a file attachment to an order (artwork, logo, reference, production_note, proof, other)."""
    order = await db.orders.find_one({"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # L9: whitelist content types to prevent hostile uploads.
    ALLOWED_MIME_PREFIXES = ("image/", "video/", "audio/")
    ALLOWED_MIME_EXACT = {
        "application/pdf", "application/postscript", "application/illustrator",
        "application/x-photoshop", "application/vnd.adobe.photoshop",
        "application/zip", "application/x-zip-compressed",
        "application/octet-stream",  # generic binary (fonts, design files)
        "text/plain", "text/csv",
        "application/json", "application/xml",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    ct = (file.content_type or "").lower()
    if not (any(ct.startswith(p) for p in ALLOWED_MIME_PREFIXES) or ct in ALLOWED_MIME_EXACT):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type or 'unknown'}")

    contents = await file.read()
    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 15MB)")

    valid_categories = {"artwork", "logo", "reference", "production_note", "proof", "other"}
    if category not in valid_categories:
        category = "artwork"
    tag_list = [t.strip() for t in (tags or "").split(",") if t.strip()]

    file_id = str(uuid.uuid4())
    storage_path = _build_order_file_storage_path(current_user.tenant_id, order_id, file_id, file.filename or "attachment.bin")
    result = put_object(storage_path, contents, file.content_type or "application/octet-stream")
    file_doc = {
        "id": file_id,
        "order_id": order_id,
        "tenant_id": current_user.tenant_id,
        "filename": file.filename or "unknown",
        "label": label or file.filename or "Attachment",
        "content_type": file.content_type,
        "file_size": len(contents),
        "storage_path": result.get("path", storage_path),
        "storage_backend": "emergent_object_storage",
        "uploaded_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "tags": tag_list,
        "is_shared": bool(is_shared),
        "linked_item_ids": [],
        "uploaded_scope": "order" if is_shared else "item",
        "original_item_id": None,
    }
    await db.order_files.insert_one(file_doc)

    await log_activity(db, order_id, current_user.tenant_id, "file", file_id,
                       "uploaded", f"File uploaded: {file.filename}",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    return {"id": file_id, "filename": file.filename, "label": file_doc["label"], "file_size": len(contents), "content_type": file.content_type, "category": category, "tags": tag_list, "is_shared": is_shared}


@router.get("/{order_id}/files")
async def list_order_files(order_id: str, category: Optional[str] = None, current_user: UserInDB = Depends(get_current_active_user)):
    """List all file attachments for an order. Optional category filter."""
    query = {"order_id": order_id, "tenant_id": current_user.tenant_id}
    if category:
        query["category"] = category
    files = await db.order_files.find(
        query,
        {"_id": 0, "file_data": 0}
    ).sort("created_at", -1).to_list(200)
    return files


@router.post("/{order_id}/items/{item_id}/link-artwork")
async def link_artwork_to_item(
    order_id: str,
    item_id: str,
    payload: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Link shared order-level artwork files to an Order Item (reference-only, no file duplication)."""
    file_ids = [str(fid) for fid in (payload.get("file_ids") or [])]
    item = await db.job_tickets.find_one({"id": item_id, "order_id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "linked_order_file_ids": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Order Item not found")
    existing = list(item.get("linked_order_file_ids") or [])
    merged = list(dict.fromkeys([*existing, *file_ids]))
    await db.job_tickets.update_one({"id": item_id}, {"$set": {"linked_order_file_ids": merged, "updated_at": datetime.now(timezone.utc).isoformat()}})
    # Also record the reverse link on each file doc
    for fid in file_ids:
        await db.order_files.update_one({"id": fid, "order_id": order_id}, {"$addToSet": {"linked_item_ids": item_id}})
    return {"linked_order_file_ids": merged}


@router.post("/{order_id}/items/{item_id}/unlink-artwork")
async def unlink_artwork_from_item(
    order_id: str,
    item_id: str,
    payload: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user),
):
    file_ids = set(str(fid) for fid in (payload.get("file_ids") or []))
    item = await db.job_tickets.find_one({"id": item_id, "order_id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "linked_order_file_ids": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Order Item not found")
    remaining = [fid for fid in (item.get("linked_order_file_ids") or []) if fid not in file_ids]
    await db.job_tickets.update_one({"id": item_id}, {"$set": {"linked_order_file_ids": remaining, "updated_at": datetime.now(timezone.utc).isoformat()}})
    for fid in file_ids:
        await db.order_files.update_one({"id": fid, "order_id": order_id}, {"$pull": {"linked_item_ids": item_id}})
    return {"linked_order_file_ids": remaining}


@router.get("/{order_id}/items/{item_id}/artwork")
async def get_item_artwork(order_id: str, item_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Merged artwork view for an Order Item: shared + item-specific file metadata."""
    item = await db.job_tickets.find_one({"id": item_id, "order_id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "linked_order_file_ids": 1, "item_artwork_file_ids": 1})
    if not item:
        raise HTTPException(status_code=404, detail="Order Item not found")
    shared_ids = list(item.get("linked_order_file_ids") or [])
    item_ids = list(item.get("item_artwork_file_ids") or [])
    all_ids = list({*shared_ids, *item_ids})
    docs = await db.order_files.find({"id": {"$in": all_ids}, "order_id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "file_data": 0}).to_list(200)
    by_id = {d["id"]: d for d in docs}
    return {
        "shared_files": [by_id[fid] for fid in shared_ids if fid in by_id],
        "item_files": [by_id[fid] for fid in item_ids if fid in by_id],
    }


@router.post("/{order_id}/files/{file_id}/promote-to-shared")
async def promote_file_to_shared(order_id: str, file_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    result = await db.order_files.update_one(
        {"id": file_id, "order_id": order_id, "tenant_id": current_user.tenant_id},
        {"$set": {"is_shared": True, "uploaded_scope": "order"}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    return {"ok": True}


@router.delete("/{order_id}/files/{file_id}")
async def delete_order_file(order_id: str, file_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    result = await db.order_files.delete_one({"id": file_id, "order_id": order_id, "tenant_id": current_user.tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted"}


@router.get("/{order_id}/files/{file_id}/content")
async def get_order_file_content(order_id: str, file_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    file_doc = await db.order_files.find_one(
        {"id": file_id, "order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found")

    media_type = file_doc.get("content_type") or mimetypes.guess_type(file_doc.get("filename", ""))[0] or "application/octet-stream"
    try:
        storage_path = file_doc.get("storage_path") or await _migrate_order_file_to_storage(file_doc)
        if storage_path:
            content, content_type = get_object(storage_path)
            media_type = content_type or media_type
        else:
            content = base64.b64decode(file_doc.get("file_data", ""))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Failed to load file") from exc
    return Response(content=content, media_type=media_type)


# ───────────────────────────────────────────────────────────────────────────
# Work-Ticket PDF (internal production document)
# ───────────────────────────────────────────────────────────────────────────


def _render_work_ticket_pdf(
    order: dict,
    tenant: dict,
    customer: Optional[dict],
    tickets: List[dict],
    include_pricing: bool,
    assignees: Dict[str, str],
) -> BytesIO:
    """Render the internal production work-ticket PDF.

    The work ticket is meant for shop staff. Pricing is hidden by default and
    only included when include_pricing=True so production crews don't see
    margins on the shop floor.
    """
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=letter,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    h1 = styles['Heading1']
    h3 = styles['Heading3']
    body = styles['BodyText']
    small = ParagraphStyle('small', parent=body, fontSize=8, leading=10, textColor=colors.HexColor('#475569'))
    label_style = ParagraphStyle('label', parent=body, fontSize=8, leading=10, textColor=colors.HexColor('#64748B'), spaceAfter=0)
    value_style = ParagraphStyle('value', parent=body, fontSize=10, leading=12, textColor=colors.HexColor('#0F172A'))
    section_title = ParagraphStyle('section_title', parent=h3, fontSize=11, leading=14, textColor=colors.HexColor('#7C3AED'), spaceBefore=8, spaceAfter=4)

    elements: List[Any] = []

    # Header — tenant branding (text-only; image asset support could be added later)
    company_name = (tenant or {}).get("name") or "Sign Shop"
    elements.append(Paragraph(f"<b>{company_name}</b>", h1))
    header_bits = []
    if tenant:
        for k in ("address", "city", "state", "zip_code", "phone", "email"):
            v = tenant.get(k)
            if v:
                header_bits.append(str(v))
    if header_bits:
        elements.append(Paragraph(" · ".join(header_bits), small))

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<b>INTERNAL WORK TICKET</b>", h3))
    elements.append(Spacer(1, 6))

    # Order header table — order#, dates, status, customer
    order_number = order.get("order_number") or (order.get("id") or "")[:8].upper()
    order_name = order.get("name") or ""
    order_date = (order.get("date_created") or "")[:10] or "—"
    due_date = order.get("requested_due_date") or order.get("event_date") or "—"
    status = (order.get("status") or "").upper() or "—"
    approval = (order.get("approval_status") or "").upper() or "—"
    payment = (order.get("payment_status") or "").upper() or "—"

    cust_lines: List[str] = []
    cust_name = (
        (customer or {}).get("display_name")
        or (customer or {}).get("name")
        or order.get("customer_name")
        or "—"
    )
    cust_lines.append(f"<b>{cust_name}</b>")
    if (customer or {}).get("company") or order.get("company_name"):
        cust_lines.append((customer or {}).get("company") or order.get("company_name") or "")
    contact = (customer or {}).get("phone") or order.get("phone")
    if contact:
        cust_lines.append(f"📞 {contact}")
    email = (customer or {}).get("email") or order.get("email")
    if email:
        cust_lines.append(f"✉  {email}")

    header_rows = [
        [
            Paragraph("ORDER #", label_style),
            Paragraph(f"<b>{order_number}</b>", value_style),
            Paragraph("CUSTOMER", label_style),
            Paragraph("<br/>".join(cust_lines), value_style),
        ],
        [
            Paragraph("ORDER NAME", label_style),
            Paragraph(order_name or "—", value_style),
            Paragraph("ORDER DATE", label_style),
            Paragraph(order_date, value_style),
        ],
        [
            Paragraph("STATUS", label_style),
            Paragraph(status, value_style),
            Paragraph("DUE DATE", label_style),
            Paragraph(due_date, value_style),
        ],
        [
            Paragraph("APPROVAL", label_style),
            Paragraph(approval, value_style),
            Paragraph("PAYMENT", label_style),
            Paragraph(payment, value_style),
        ],
    ]
    header_table = Table(header_rows, colWidths=[70, 200, 70, 200])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # Shared order-level context (always useful to production)
    shared_blocks = []
    for label, key in [
        ("Shared Production Notes", "shared_production_notes"),
        ("Shared Design Notes", "shared_design_notes"),
        ("Shared Install Notes", "shared_install_notes"),
        ("Color / Brand Notes", "shared_color_brand_notes"),
    ]:
        val = order.get(key) or ""
        if val:
            shared_blocks.append(f"<b>{label}:</b> {val}")
    if order.get("pickup_delivery_method"):
        shared_blocks.append(f"<b>Fulfillment:</b> {order['pickup_delivery_method']}")
        if order.get("pickup_delivery_notes"):
            shared_blocks.append(f"<b>Fulfillment Notes:</b> {order['pickup_delivery_notes']}")
    if shared_blocks:
        elements.append(Paragraph("Shared Order Context", section_title))
        for b in shared_blocks:
            elements.append(Paragraph(b, body))
        elements.append(Spacer(1, 6))

    # ── Items (Job Tickets) ──
    elements.append(Paragraph("Order Items", section_title))
    if not tickets:
        elements.append(Paragraph("<i>No job tickets attached to this order yet.</i>", small))
    for idx, t in enumerate(tickets, start=1):
        specs = t.get("specs") or {}
        item_name = t.get("item_name") or t.get("description") or "Untitled Item"
        category = t.get("item_category") or ""
        sub = t.get("item_subcategory") or ""
        qty = t.get("quantity", 1)
        unit = t.get("unit_type") or "each"
        ticket_due = t.get("due_date") or "—"
        ticket_status = (t.get("status") or "").upper() or "—"
        artwork_status = (t.get("artwork_status") or "").upper() or "—"
        proof_status = (t.get("proof_approval_status") or "").upper() or "—"
        assignee = assignees.get(t.get("assigned_user_id") or "", "") or t.get("assigned_team") or ""

        width = specs.get("width", "")
        height = specs.get("height", "")
        uom = specs.get("unit_of_measure") or "in"
        size_desc = specs.get("size_description") or (
            f"{width} × {height} {uom}" if width and height else "—"
        )
        material = specs.get("material") or ""
        substrate = specs.get("substrate") or ""
        finish = specs.get("finish") or specs.get("lamination") or ""

        item_rows = [
            [
                Paragraph(f"<b>Item {idx}</b>", value_style),
                Paragraph(f"<b>{item_name}</b>", value_style),
            ],
            [Paragraph("Category", label_style),
             Paragraph(f"{category}{(' / ' + sub) if sub else ''}", value_style)],
            [Paragraph("Quantity", label_style), Paragraph(f"{qty} {unit}", value_style)],
            [Paragraph("Dimensions", label_style), Paragraph(size_desc, value_style)],
            [Paragraph("Material / Substrate", label_style),
             Paragraph(" / ".join([x for x in (material, substrate) if x]) or "—", value_style)],
        ]
        if finish:
            item_rows.append([Paragraph("Finish", label_style), Paragraph(finish, value_style)])
        item_rows.extend([
            [Paragraph("Due Date", label_style), Paragraph(ticket_due, value_style)],
            [Paragraph("Production Status", label_style), Paragraph(ticket_status, value_style)],
            [Paragraph("Approval Status", label_style),
             Paragraph(f"Artwork: {artwork_status} · Proof: {proof_status}", value_style)],
        ])
        if assignee:
            item_rows.append([Paragraph("Assigned", label_style), Paragraph(assignee, value_style)])

        # Notes blocks
        note_rows = []
        for label, key in [
            ("Production Notes", "production_notes"),
            ("Special Instructions", "special_instructions"),
            ("Install Notes", "install_notes"),
            ("Packaging Notes", "packaging_notes"),
        ]:
            v = t.get(key) or ""
            if v:
                note_rows.append([Paragraph(label, label_style), Paragraph(v, value_style)])
        # Design / finishing notes pulled from specs
        for label, key in [
            ("Design / Artwork Notes", "artwork_notes"),
            ("Finishing Notes", "finishing"),
        ]:
            v = (specs.get(key) or "") if isinstance(specs, dict) else ""
            if v:
                note_rows.append([Paragraph(label, label_style), Paragraph(v, value_style)])
        item_rows.extend(note_rows)

        # Optional pricing rows (gated)
        if include_pricing:
            selling = float(t.get("estimated_price") or 0)
            cost = float(t.get("actual_cost") or t.get("material_estimate") or 0) + float(t.get("labor_estimate") or 0)
            profit = selling - cost
            margin = (profit / selling * 100.0) if selling > 0 else 0.0
            item_rows.append([
                Paragraph("Selling Price", label_style),
                Paragraph(f"${selling:.2f}", value_style),
            ])
            item_rows.append([
                Paragraph("Production Cost", label_style),
                Paragraph(f"${cost:.2f}", value_style),
            ])
            item_rows.append([
                Paragraph("Profit / Margin", label_style),
                Paragraph(f"${profit:.2f} ({margin:.1f}%)", value_style),
            ])

        tbl = Table(item_rows, colWidths=[120, 420])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EDE9FE')),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8FAFC')),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#CBD5E1')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elements.append(KeepTogether([tbl, Spacer(1, 8)]))

    # ── Production Checklist ──
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Production Checklist", section_title))
    checklist = [
        "Artwork ready",
        "Customer approved",
        "Deposit paid",
        "Materials ordered",
        "Printed",
        "Laminated",
        "Cut / trimmed",
        "Installed / picked up",
        "Final payment collected",
    ]
    # Two columns of checkboxes for compact layout
    rows = []
    for i in range(0, len(checklist), 2):
        left = checklist[i]
        right = checklist[i + 1] if i + 1 < len(checklist) else ""
        rows.append([
            Paragraph(f"☐ &nbsp; {left}", value_style),
            Paragraph(f"☐ &nbsp; {right}" if right else "", value_style),
        ])
    chk = Table(rows, colWidths=[270, 270])
    chk.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(chk)

    # ── Notes (blank lines for shop staff) ──
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Shop Notes", section_title))
    lines = []
    for _ in range(6):
        lines.append([Paragraph("", value_style)])
    notes_tbl = Table(lines, colWidths=[540], rowHeights=[18] * 6)
    notes_tbl.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(notes_tbl)

    # Footer
    elements.append(Spacer(1, 12))
    pricing_visibility = "shown" if include_pricing else "hidden"
    elements.append(Paragraph(
        f"<font color='#64748B'>Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        f"Pricing: {pricing_visibility} · Internal — not for customer distribution.</font>",
        small,
    ))

    doc.build(elements)
    output.seek(0)
    return output


@router.get("/{order_id}/work-ticket/pdf")
async def download_order_work_ticket_pdf(
    order_id: str,
    include_pricing: bool = False,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Generate a printable internal production work-ticket PDF.

    Query params:
      include_pricing — when true, the PDF includes per-item selling price,
                        production cost, and profit/margin. Defaults to false
                        so production staff don't see margins by default.
    """
    order = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    tickets = await db.job_tickets.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    ).sort("ticket_number", 1).to_list(500)

    tenant = await db.tenants.find_one(
        {"id": current_user.tenant_id},
        {"_id": 0},
    ) or {}

    customer = None
    if order.get("customer_id"):
        customer = await db.customers.find_one(
            {"id": order["customer_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0},
        )

    # Resolve assigned user names so the ticket can show "Assigned: Jane Doe"
    assignee_ids = list({t.get("assigned_user_id") for t in tickets if t.get("assigned_user_id")})
    assignees: Dict[str, str] = {}
    if assignee_ids:
        async for user in db.users.find(
            {"id": {"$in": assignee_ids}, "tenant_id": current_user.tenant_id},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1},
        ):
            assignees[user["id"]] = user.get("full_name") or user.get("email") or ""

    pdf = _render_work_ticket_pdf(order, tenant, customer, tickets, include_pricing, assignees)
    order_number = order.get("order_number") or order_id[:8].upper()
    safe_number = "".join(c for c in str(order_number) if c.isalnum() or c in ("-", "_")) or "order"
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename=work_ticket_{safe_number}.pdf"},
    )
