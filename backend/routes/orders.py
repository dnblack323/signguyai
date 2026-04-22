"""
Orders API Routes

CRUD for the master Order record (Layer 1).
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Response
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
import base64
import mimetypes

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
        "tax_amount": 0,
        "discount_amount": 0,
        "grand_total": subtotal,
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
