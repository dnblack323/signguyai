"""
Workflow Templates API Routes

Admin CRUD for category-based workflow templates.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from server import db, get_current_active_user
from models import UserInDB
from models.orders import WorkflowTemplate, ProductionTask, TaskStatus
from services.workflow_engine import seed_default_templates

router = APIRouter(prefix="/workflow-templates", tags=["Workflow Templates"])


class TemplateCreate(BaseModel):
    category: str
    template_name: str
    stages: List[Dict[str, Any]]


class TemplateUpdate(BaseModel):
    template_name: Optional[str] = None
    stages: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None


@router.get("")
async def list_templates(current_user: UserInDB = Depends(get_current_active_user)):
    """List all workflow templates for the tenant. Seeds defaults if none exist."""
    await seed_default_templates(db, current_user.tenant_id)

    templates = await db.workflow_templates.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("category", 1).to_list(50)
    return templates


@router.get("/{template_id}")
async def get_template(template_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    template = await db.workflow_templates.find_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("")
async def create_template(data: TemplateCreate, current_user: UserInDB = Depends(get_current_active_user)):
    template = WorkflowTemplate(
        tenant_id=current_user.tenant_id,
        category=data.category,
        template_name=data.template_name,
        stages=data.stages,
    )
    doc = template.model_dump()
    await db.workflow_templates.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/{template_id}")
async def update_template(template_id: str, data: TemplateUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.workflow_templates.find_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["is_default"] = False  # No longer default if edited

    await db.workflow_templates.update_one({"id": template_id}, {"$set": update_data})
    updated = await db.workflow_templates.find_one({"id": template_id}, {"_id": 0})
    return updated


@router.delete("/{template_id}")
async def delete_template(template_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    result = await db.workflow_templates.delete_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}


@router.post("/seed-defaults")
async def reseed_defaults(current_user: UserInDB = Depends(get_current_active_user)):
    """Force re-seed default templates (deletes existing defaults first)."""
    await db.workflow_templates.delete_many({"tenant_id": current_user.tenant_id, "is_default": True})
    await seed_default_templates(db, current_user.tenant_id)
    templates = await db.workflow_templates.find(
        {"tenant_id": current_user.tenant_id}, {"_id": 0}
    ).to_list(50)
    return {"message": "Default templates re-seeded", "count": len(templates)}


class ApplyTemplateRequest(BaseModel):
    order_id: str
    job_ticket_id: Optional[str] = None
    replace_existing: bool = False


@router.post("/{template_id}/apply")
async def apply_template_to_order(
    template_id: str,
    payload: ApplyTemplateRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Apply a workflow template to an order (or specific job ticket on the order).

    Generates ProductionTask records from the template's stages for each
    targeted job ticket. If replace_existing=true, deletes the ticket's
    existing production tasks first.
    """
    template = await db.workflow_templates.find_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    order = await db.orders.find_one(
        {"id": payload.order_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    ticket_query: Dict[str, Any] = {"order_id": payload.order_id, "tenant_id": current_user.tenant_id}
    if payload.job_ticket_id:
        ticket_query["id"] = payload.job_ticket_id

    tickets = await db.job_tickets.find(ticket_query, {"_id": 0}).to_list(200)
    if not tickets:
        raise HTTPException(status_code=404, detail="No job tickets found for this order")

    created_total = 0
    affected_tickets: List[str] = []
    now = datetime.now(timezone.utc).isoformat()

    for ticket in tickets:
        ticket_id = ticket["id"]
        if payload.replace_existing:
            await db.production_tasks.delete_many({
                "job_ticket_id": ticket_id,
                "tenant_id": current_user.tenant_id,
            })

        prev_task_id = None
        for stage in sorted(template.get("stages", []), key=lambda s: s.get("sequence", 0)):
            task = ProductionTask(
                order_id=payload.order_id,
                job_ticket_id=ticket_id,
                tenant_id=current_user.tenant_id,
                task_name=stage.get("name", "Stage"),
                department=stage.get("department", ""),
                stage_sequence=stage.get("sequence", 0),
                status=TaskStatus.NOT_STARTED.value,
                qc_required=stage.get("qc_required", False),
                depends_on_proof=stage.get("depends_on_proof", False),
                dependency_task_id=prev_task_id,
                timestamp_history=[{
                    "status": TaskStatus.NOT_STARTED.value,
                    "timestamp": now,
                    "user_id": current_user.id,
                }],
            )
            await db.production_tasks.insert_one(task.model_dump())
            prev_task_id = task.id
            created_total += 1
        affected_tickets.append(ticket_id)

    return {
        "message": "Template applied successfully",
        "template_id": template_id,
        "template_name": template.get("template_name"),
        "order_id": payload.order_id,
        "tickets_updated": affected_tickets,
        "tasks_created": created_total,
    }


@router.post("/{template_id}/duplicate")
async def duplicate_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Duplicate an existing template into a new copy (tenant-scoped)."""
    source = await db.workflow_templates.find_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not source:
        raise HTTPException(status_code=404, detail="Template not found")

    new_template = WorkflowTemplate(
        tenant_id=current_user.tenant_id,
        category=source.get("category"),
        template_name=f"{source.get('template_name', 'Template')} (Copy)",
        stages=source.get("stages", []),
        is_default=False,
    )
    doc = new_template.model_dump()
    await db.workflow_templates.insert_one(doc)
    doc.pop("_id", None)
    return doc
