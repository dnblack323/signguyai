"""
Job Tickets API Routes

CRUD for Job Ticket records (Layer 2) — the operational source of truth.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

from server import db, get_current_active_user
from models import UserInDB
from models.orders import (
    JobTicket, JobTicketCreate, JobTicketUpdate, JobTicketStatus, JobTicketSpecs
)
from services.workflow_engine import (
    generate_production_tasks, seed_default_templates,
    update_ticket_progress, update_order_progress, log_activity
)

router = APIRouter(prefix="/job-tickets", tags=["Job Tickets"])


async def _next_ticket_number(order_id: str, tenant_id: str) -> str:
    order = await db.orders.find_one({"id": order_id}, {"_id": 0, "order_number": 1})
    prefix = order.get("order_number", "ORD") if order else "ORD"
    count = await db.job_tickets.count_documents({"order_id": order_id, "tenant_id": tenant_id})
    return f"{prefix}-T{count + 1}"


@router.get("")
async def list_job_tickets(
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    assigned_user_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: UserInDB = Depends(get_current_active_user),
):
    query = {"tenant_id": current_user.tenant_id}
    if order_id:
        query["order_id"] = order_id
    if status:
        query["status"] = status
    if category:
        query["item_category"] = category
    if department:
        query["department_route"] = department
    if assigned_user_id:
        query["assigned_user_id"] = assigned_user_id

    tickets = await db.job_tickets.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.job_tickets.count_documents(query)
    return {"tickets": tickets, "total": total}


@router.get("/{ticket_id}")
async def get_job_ticket(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    ticket = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    # Include production tasks if workflow enabled
    if ticket.get("production_flow_enabled"):
        tasks = await db.production_tasks.find(
            {"job_ticket_id": ticket_id}, {"_id": 0}
        ).sort("stage_sequence", 1).to_list(50)
        ticket["production_tasks"] = tasks

    return ticket


@router.post("")
async def create_job_ticket(data: JobTicketCreate, current_user: UserInDB = Depends(get_current_active_user)):
    # Verify order exists
    order = await db.orders.find_one(
        {"id": data.order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    specs = JobTicketSpecs(**(data.specs or {}))
    ticket = JobTicket(
        tenant_id=current_user.tenant_id,
        order_id=data.order_id,
        item_name=data.item_name,
        item_category=data.item_category,
        item_subcategory=data.item_subcategory,
        quantity=data.quantity,
        unit_type=data.unit_type,
        due_date=data.due_date,
        priority=data.priority,
        department_route=data.department_route,
        assigned_user_id=data.assigned_user_id,
        production_flow_enabled=data.production_flow_enabled,
        specs=specs,
        design_needed=data.design_needed,
        customer_artwork=data.customer_artwork,
        proof_required=data.proof_required,
        special_instructions=data.special_instructions,
        production_notes=data.production_notes,
        install_notes=data.install_notes,
        packaging_notes=data.packaging_notes,
        estimated_price=data.estimated_price,
        labor_estimate=data.labor_estimate,
        material_estimate=data.material_estimate,
    )
    ticket.ticket_number = await _next_ticket_number(data.order_id, current_user.tenant_id)

    doc = ticket.model_dump()
    await db.job_tickets.insert_one(doc)

    # If production workflow enabled, auto-generate tasks
    tasks_created = 0
    if data.production_flow_enabled:
        await seed_default_templates(db, current_user.tenant_id)
        tasks = await generate_production_tasks(db, doc, current_user.tenant_id)
        tasks_created = len(tasks)

    # Update order counts
    await update_order_progress(db, data.order_id)

    await log_activity(db, data.order_id, current_user.tenant_id, "job_ticket", ticket.id,
                       "created", f"Job ticket '{data.item_name}' ({data.item_category}) created" +
                       (f" with {tasks_created} production tasks" if tasks_created else ""),
                       user_id=current_user.id, user_name=current_user.full_name or "")

    doc.pop("_id", None)
    return doc


@router.put("/{ticket_id}")
async def update_job_ticket(ticket_id: str, data: JobTicketUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if k == "specs":
                # Merge specs
                current_specs = existing.get("specs", {})
                current_specs.update(v)
                update_data["specs"] = current_specs
            else:
                update_data[k] = v

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Log status changes
    if "status" in update_data and update_data["status"] != existing.get("status"):
        await log_activity(db, existing["order_id"], current_user.tenant_id, "job_ticket", ticket_id,
                           "status_change", f"Ticket status: {existing.get('status')} → {update_data['status']}",
                           user_id=current_user.id, user_name=current_user.full_name or "",
                           old_value=existing.get("status"), new_value=update_data["status"])

    # Handle production flow toggle
    if "production_flow_enabled" in update_data and update_data["production_flow_enabled"] and not existing.get("production_flow_enabled"):
        existing_tasks = await db.production_tasks.count_documents({"job_ticket_id": ticket_id})
        if existing_tasks == 0:
            await seed_default_templates(db, current_user.tenant_id)
            merged = {**existing, **update_data}
            await generate_production_tasks(db, merged, current_user.tenant_id)

    await db.job_tickets.update_one({"id": ticket_id}, {"$set": update_data})

    # Update rollups
    await update_order_progress(db, existing["order_id"])

    updated = await db.job_tickets.find_one({"id": ticket_id}, {"_id": 0})
    return updated


@router.delete("/{ticket_id}")
async def delete_job_ticket(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "order_id": 1}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    await db.job_tickets.delete_one({"id": ticket_id})
    await db.production_tasks.delete_many({"job_ticket_id": ticket_id})
    await update_order_progress(db, existing["order_id"])
    return {"message": "Job ticket and tasks deleted"}
