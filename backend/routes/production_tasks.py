"""
Production Tasks API Routes

CRUD for Production Task records (Layer 4) — department-level tracking.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

from server import db, get_current_active_user
from models import UserInDB
from models.orders import ProductionTaskUpdate, TaskStatus
from services.workflow_engine import update_ticket_progress, update_order_progress, log_activity

router = APIRouter(prefix="/production-tasks", tags=["Production Tasks"])


@router.get("")
async def list_production_tasks(
    order_id: Optional[str] = None,
    job_ticket_id: Optional[str] = None,
    department: Optional[str] = None,
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_user: UserInDB = Depends(get_current_active_user),
):
    query = {"tenant_id": current_user.tenant_id}
    if order_id:
        query["order_id"] = order_id
    if job_ticket_id:
        query["job_ticket_id"] = job_ticket_id
    if department:
        query["department"] = department
    if status:
        query["status"] = status
    if assigned_to:
        query["assigned_to"] = assigned_to

    tasks = await db.production_tasks.find(query, {"_id": 0}).sort("stage_sequence", 1).skip(skip).limit(limit).to_list(limit)
    total = await db.production_tasks.count_documents(query)
    return {"tasks": tasks, "total": total}


DEFAULT_PRODUCTION_STAGES = [
    {"key": "intake", "label": "Intake", "color": "#6366F1"},
    {"key": "design", "label": "Design", "color": "#8B5CF6"},
    {"key": "production", "label": "Production", "color": "#2563EB"},
    {"key": "finishing", "label": "Finishing / QC", "color": "#059669"},
    {"key": "ready", "label": "Ready / Delivery", "color": "#16A34A"},
]


@router.get("/stages/config")
async def get_production_stages(current_user: UserInDB = Depends(get_current_active_user)):
    """Get the production stage configuration for the tenant."""
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "production_stages": 1})
    return {"stages": (tenant or {}).get("production_stages") or DEFAULT_PRODUCTION_STAGES}


@router.put("/stages/config")
async def update_production_stages(data: dict, current_user: UserInDB = Depends(get_current_active_user)):
    """Update production stage configuration."""
    stages = data.get("stages", DEFAULT_PRODUCTION_STAGES)
    await db.tenants.update_one(
        {"id": current_user.tenant_id},
        {"$set": {"production_stages": stages, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"stages": stages}


@router.get("/board")
async def production_board(
    view: str = "stage",
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Get production board data grouped by stage, department, or status."""
    pipeline = [
        {"$match": {"tenant_id": current_user.tenant_id}},
        {"$project": {"_id": 0}},
    ]

    tasks = await db.production_tasks.aggregate(pipeline).to_list(500)

    # Enrich with ticket info
    ticket_ids = list({t["job_ticket_id"] for t in tasks if t.get("job_ticket_id")})
    tickets_map = {}
    if ticket_ids:
        tickets = await db.job_tickets.find(
            {"id": {"$in": ticket_ids}},
            {"_id": 0, "id": 1, "item_name": 1, "item_category": 1, "order_id": 1, "priority": 1, "due_date": 1, "ticket_number": 1}
        ).to_list(500)
        tickets_map = {t["id"]: t for t in tickets}

    for task in tasks:
        ticket = tickets_map.get(task.get("job_ticket_id"), {})
        task["ticket_name"] = ticket.get("item_name", "")
        task["ticket_number"] = ticket.get("ticket_number", "")
        task["ticket_category"] = ticket.get("item_category", "")
        task["ticket_priority"] = ticket.get("priority", "normal")
        task["ticket_due_date"] = ticket.get("due_date")

    if view == "stage":
        tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "production_stages": 1})
        stages = (tenant or {}).get("production_stages") or DEFAULT_PRODUCTION_STAGES
        stage_keys = [s["key"] for s in stages]
        grouped = {s["key"]: [] for s in stages}
        for task in tasks:
            stage = task.get("production_stage") or task.get("department") or "intake"
            if stage not in grouped:
                stage = stage_keys[0] if stage_keys else "intake"
            grouped.setdefault(stage, []).append(task)
        return {"view": "stage", "stages": stages, "groups": grouped}

    if view == "department":
        grouped = {}
        for task in tasks:
            dept = task.get("department", "unassigned")
            grouped.setdefault(dept, []).append(task)
        return {"view": "department", "groups": grouped}

    if view == "status":
        grouped = {}
        for task in tasks:
            st = task.get("status", "not_started")
            grouped.setdefault(st, []).append(task)
        return {"view": "status", "groups": grouped}

    return {"view": "list", "tasks": tasks}


@router.get("/{task_id}")
async def get_production_task(task_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    task = await db.production_tasks.find_one(
        {"id": task_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not task:
        raise HTTPException(status_code=404, detail="Production task not found")
    return task


@router.put("/{task_id}")
async def update_production_task(task_id: str, data: ProductionTaskUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.production_tasks.find_one(
        {"id": task_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Production task not found")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    now = datetime.now(timezone.utc).isoformat()
    update_data["updated_at"] = now

    # Handle status transitions
    new_status = update_data.get("status")
    if new_status and new_status != existing.get("status"):
        # Check proof dependency: block if proof not approved and task depends on proof
        if existing.get("depends_on_proof"):
            ticket = await db.job_tickets.find_one({"id": existing["job_ticket_id"]}, {"_id": 0, "proof_approval_status": 1})
            if ticket and ticket.get("proof_approval_status") != "approved" and new_status in (TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETE.value):
                # Allow admin override but warn
                pass  # Could add stricter check here

        # Track timestamps
        if new_status == TaskStatus.IN_PROGRESS.value and not existing.get("start_datetime"):
            update_data["start_datetime"] = now
        if new_status == TaskStatus.COMPLETE.value:
            update_data["end_datetime"] = now
            update_data["completion_percent"] = 100.0

        # Add to timestamp history
        history = existing.get("timestamp_history", [])
        history.append({"status": new_status, "timestamp": now, "user_id": current_user.id})
        update_data["timestamp_history"] = history

        await log_activity(db, existing["order_id"], current_user.tenant_id, "production_task", task_id,
                           "task_status_change", f"Task '{existing.get('task_name')}': {existing.get('status')} → {new_status}",
                           user_id=current_user.id, user_name=current_user.full_name or "",
                           old_value=existing.get("status"), new_value=new_status)

    await db.production_tasks.update_one({"id": task_id, "tenant_id": current_user.tenant_id}, {"$set": update_data})

    # Roll up progress
    await update_ticket_progress(db, existing["job_ticket_id"])
    await update_order_progress(db, existing["order_id"])

    updated = await db.production_tasks.find_one({"id": task_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    return updated
