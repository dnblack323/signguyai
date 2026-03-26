"""
Orders API Routes

CRUD for the master Order record (Layer 1).
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import base64

from server import db, get_current_active_user
from models import UserInDB
from models.orders import (
    Order, OrderCreate, OrderUpdate, OrderStatus, PaymentStatus
)
from services.workflow_engine import update_order_progress, log_activity

router = APIRouter(prefix="/orders", tags=["Orders"])


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
    order = Order(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **data.model_dump()
    )
    order.order_number = await _next_order_number(current_user.tenant_id)

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
        price = t.get("estimated_price", 0)
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
        "type": "quote",
        "status": "draft",
        "line_items": line_items,
        "subtotal": subtotal,
        "tax": 0,
        "discount": 0,
        "total": subtotal,
        "notes": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.order_quotes.insert_one(quote_doc)

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

    return {"message": f"Production started", "tickets_activated": len(tickets), "tasks_created": tasks_created}


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
        price = t.get("estimated_price", 0)
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
        "type": "invoice",
        "status": "draft",
        "line_items": line_items,
        "subtotal": subtotal,
        "tax": 0,
        "discount": 0,
        "total": subtotal,
        "notes": "",
        "due_date": order.get("requested_due_date"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.order_quotes.insert_one(invoice_doc)

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
    """Get all quotes and invoices linked to this order."""
    order = await db.orders.find_one(
        {"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    docs = await db.order_quotes.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)

    quotes = [d for d in docs if d.get("type") == "quote"]
    invoices = [d for d in docs if d.get("type") == "invoice"]

    return {"quotes": quotes, "invoices": invoices, "total_documents": len(docs)}


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
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Upload a file attachment to an order (artwork, drawings, notes, photos)."""
    order = await db.orders.find_one({"id": order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    contents = await file.read()
    if len(contents) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 15MB)")

    file_id = str(uuid.uuid4())
    file_doc = {
        "id": file_id,
        "order_id": order_id,
        "tenant_id": current_user.tenant_id,
        "filename": file.filename or "unknown",
        "label": label or file.filename or "Attachment",
        "content_type": file.content_type,
        "file_size": len(contents),
        "file_data": base64.b64encode(contents).decode("utf-8"),
        "uploaded_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.order_files.insert_one(file_doc)

    await log_activity(db, order_id, current_user.tenant_id, "file", file_id,
                       "uploaded", f"File uploaded: {file.filename}",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    return {"id": file_id, "filename": file.filename, "label": file_doc["label"], "file_size": len(contents), "content_type": file.content_type}


@router.get("/{order_id}/files")
async def list_order_files(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """List all file attachments for an order."""
    files = await db.order_files.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "file_data": 0}
    ).sort("created_at", -1).to_list(50)
    return files


@router.delete("/{order_id}/files/{file_id}")
async def delete_order_file(order_id: str, file_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    result = await db.order_files.delete_one({"id": file_id, "order_id": order_id, "tenant_id": current_user.tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    return {"message": "File deleted"}
