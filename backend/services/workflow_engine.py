"""
Workflow Engine Service

Handles:
- Auto-generating production tasks from job ticket categories
- Status roll-up (tasks → tickets → orders)
- Default workflow templates
- Activity logging
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid

from models.orders import (
    ProductionTask, TaskStatus, JobTicketStatus, OrderStatus,
    WorkflowTemplate, OrderActivity
)


# ============== DEFAULT WORKFLOW TEMPLATES ==============

DEFAULT_TEMPLATES = [
    {
        "category": "rigid_signs",
        "template_name": "Rigid Signs",
        "stages": [
            {"name": "Intake Review", "department": "qc_review", "sequence": 1, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Design", "department": "design", "sequence": 2, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Sent", "department": "design", "sequence": 3, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Approved", "department": "design", "sequence": 4, "required": False, "qc_required": False, "depends_on_proof": True},
            {"name": "Print", "department": "print", "sequence": 5, "required": True, "qc_required": False, "depends_on_proof": True},
            {"name": "Laminate", "department": "lamination", "sequence": 6, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "Mount to Substrate", "department": "assembly", "sequence": 7, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Cut / Trim", "department": "cut_trim", "sequence": 8, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Add Hardware / Stakes", "department": "assembly", "sequence": 9, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "QC", "department": "qc_review", "sequence": 10, "required": True, "qc_required": True, "depends_on_proof": False},
            {"name": "Ready for Pickup / Delivery", "department": "packaging", "sequence": 11, "required": True, "qc_required": False, "depends_on_proof": False},
        ],
    },
    {
        "category": "banners",
        "template_name": "Banners",
        "stages": [
            {"name": "Intake Review", "department": "qc_review", "sequence": 1, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Design", "department": "design", "sequence": 2, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Sent", "department": "design", "sequence": 3, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Approved", "department": "design", "sequence": 4, "required": False, "qc_required": False, "depends_on_proof": True},
            {"name": "Print", "department": "print", "sequence": 5, "required": True, "qc_required": False, "depends_on_proof": True},
            {"name": "Laminate", "department": "lamination", "sequence": 6, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "Trim", "department": "cut_trim", "sequence": 7, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Hem", "department": "sewing_finishing", "sequence": 8, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Grommets", "department": "sewing_finishing", "sequence": 9, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "QC", "department": "qc_review", "sequence": 10, "required": True, "qc_required": True, "depends_on_proof": False},
            {"name": "Package", "department": "packaging", "sequence": 11, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Ready for Pickup / Delivery", "department": "delivery", "sequence": 12, "required": True, "qc_required": False, "depends_on_proof": False},
        ],
    },
    {
        "category": "cut_vinyl",
        "template_name": "Cut Vinyl / Lettering",
        "stages": [
            {"name": "Intake Review", "department": "qc_review", "sequence": 1, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Design Setup", "department": "design", "sequence": 2, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Cut", "department": "cut_trim", "sequence": 3, "required": True, "qc_required": False, "depends_on_proof": True},
            {"name": "Weed", "department": "weed_mask", "sequence": 4, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Mask", "department": "weed_mask", "sequence": 5, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "QC", "department": "qc_review", "sequence": 6, "required": True, "qc_required": True, "depends_on_proof": False},
            {"name": "Package", "department": "packaging", "sequence": 7, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Ready for Pickup / Delivery", "department": "delivery", "sequence": 8, "required": True, "qc_required": False, "depends_on_proof": False},
        ],
    },
    {
        "category": "vehicle_wrap",
        "template_name": "Vehicle Wrap / Lettering",
        "stages": [
            {"name": "Intake Review", "department": "qc_review", "sequence": 1, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Vehicle Photos / Measurements", "department": "design", "sequence": 2, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Design", "department": "design", "sequence": 3, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Sent", "department": "design", "sequence": 4, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Approved", "department": "design", "sequence": 5, "required": True, "qc_required": False, "depends_on_proof": True},
            {"name": "Print", "department": "print", "sequence": 6, "required": True, "qc_required": False, "depends_on_proof": True},
            {"name": "Laminate", "department": "lamination", "sequence": 7, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Panel / Trim", "department": "cut_trim", "sequence": 8, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Prep Materials", "department": "wrap_prep", "sequence": 9, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Install Scheduling", "department": "install", "sequence": 10, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Vehicle Prep", "department": "install", "sequence": 11, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Install", "department": "install", "sequence": 12, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Post-Install QC", "department": "qc_review", "sequence": 13, "required": True, "qc_required": True, "depends_on_proof": False},
            {"name": "Customer Pickup / Completion", "department": "delivery", "sequence": 14, "required": True, "qc_required": False, "depends_on_proof": False},
        ],
    },
    {
        "category": "apparel",
        "template_name": "Apparel",
        "stages": [
            {"name": "Intake Review", "department": "qc_review", "sequence": 1, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Artwork Setup", "department": "design", "sequence": 2, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Sent", "department": "design", "sequence": 3, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "Proof Approved", "department": "design", "sequence": 4, "required": False, "qc_required": False, "depends_on_proof": True},
            {"name": "Order Garments / Check Stock", "department": "apparel", "sequence": 5, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Receive Garments", "department": "apparel", "sequence": 6, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Print / Press", "department": "apparel", "sequence": 7, "required": True, "qc_required": False, "depends_on_proof": True},
            {"name": "Count / Sort", "department": "apparel", "sequence": 8, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "QC", "department": "qc_review", "sequence": 9, "required": True, "qc_required": True, "depends_on_proof": False},
            {"name": "Package", "department": "packaging", "sequence": 10, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Ready for Pickup / Delivery", "department": "delivery", "sequence": 11, "required": True, "qc_required": False, "depends_on_proof": False},
        ],
    },
    {
        "category": "promo_misc",
        "template_name": "Promotional / Miscellaneous",
        "stages": [
            {"name": "Intake Review", "department": "qc_review", "sequence": 1, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Order / Source Product", "department": "assembly", "sequence": 2, "required": True, "qc_required": False, "depends_on_proof": False},
            {"name": "Decoration / Personalization", "department": "print", "sequence": 3, "required": False, "qc_required": False, "depends_on_proof": False},
            {"name": "QC", "department": "qc_review", "sequence": 4, "required": True, "qc_required": True, "depends_on_proof": False},
            {"name": "Delivery / Pickup", "department": "delivery", "sequence": 5, "required": True, "qc_required": False, "depends_on_proof": False},
        ],
    },
]


async def seed_default_templates(db, tenant_id: str):
    """Seed default workflow templates for a tenant if none exist."""
    existing = await db.workflow_templates.count_documents({"tenant_id": tenant_id})
    if existing > 0:
        return

    for tmpl in DEFAULT_TEMPLATES:
        template = WorkflowTemplate(
            tenant_id=tenant_id,
            category=tmpl["category"],
            template_name=tmpl["template_name"],
            stages=tmpl["stages"],
            is_default=True,
        )
        await db.workflow_templates.insert_one(template.model_dump())


async def generate_production_tasks(db, job_ticket: dict, tenant_id: str) -> List[dict]:
    """Generate production tasks from a job ticket's category template."""
    category = job_ticket.get("item_category", "custom")

    template = await db.workflow_templates.find_one(
        {"tenant_id": tenant_id, "category": category, "is_active": True},
        {"_id": 0}
    )
    if not template:
        # Try system default
        template = await db.workflow_templates.find_one(
            {"tenant_id": None, "category": category, "is_active": True},
            {"_id": 0}
        )
    if not template:
        return []

    tasks = []
    prev_task_id = None
    for stage in sorted(template.get("stages", []), key=lambda s: s.get("sequence", 0)):
        task = ProductionTask(
            order_id=job_ticket.get("order_id", ""),
            job_ticket_id=job_ticket["id"],
            tenant_id=tenant_id,
            task_name=stage["name"],
            department=stage.get("department", ""),
            stage_sequence=stage.get("sequence", 0),
            status=TaskStatus.NOT_STARTED.value,
            qc_required=stage.get("qc_required", False),
            depends_on_proof=stage.get("depends_on_proof", False),
            dependency_task_id=prev_task_id,
            timestamp_history=[{
                "status": TaskStatus.NOT_STARTED.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": "",
            }],
        )
        task_doc = task.model_dump()
        await db.production_tasks.insert_one(task_doc)
        tasks.append(task_doc)
        prev_task_id = task.id

    return tasks


async def compute_ticket_progress(db, ticket_id: str) -> float:
    """Compute job ticket progress from its production tasks."""
    tasks = await db.production_tasks.find(
        {"job_ticket_id": ticket_id},
        {"_id": 0, "status": 1, "required": 1}
    ).to_list(100)

    if not tasks:
        return 0.0

    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == TaskStatus.COMPLETE.value)
    return round((completed / total) * 100, 1)


async def update_ticket_progress(db, ticket_id: str):
    """Recompute and save job ticket progress."""
    progress = await compute_ticket_progress(db, ticket_id)

    # Determine status based on tasks
    tasks = await db.production_tasks.find(
        {"job_ticket_id": ticket_id},
        {"_id": 0, "status": 1}
    ).to_list(100)

    update_fields = {"progress": progress, "updated_at": datetime.now(timezone.utc).isoformat()}

    if tasks:
        statuses = [t["status"] for t in tasks]
        if all(s == TaskStatus.COMPLETE.value for s in statuses):
            update_fields["status"] = JobTicketStatus.COMPLETED.value
            update_fields["finished_date"] = datetime.now(timezone.utc).isoformat()
        elif any(s == TaskStatus.ON_HOLD.value for s in statuses):
            update_fields["status"] = JobTicketStatus.ON_HOLD.value
        elif any(s == TaskStatus.REWORK.value for s in statuses):
            update_fields["status"] = JobTicketStatus.REWORK.value
        elif any(s in (TaskStatus.IN_PROGRESS.value, TaskStatus.PAUSED.value, TaskStatus.NEEDS_REVIEW.value, TaskStatus.COMPLETE.value) for s in statuses) and not all(s == TaskStatus.NOT_STARTED.value for s in statuses):
            update_fields["status"] = JobTicketStatus.IN_PRODUCTION.value
            if not await db.job_tickets.find_one({"id": ticket_id, "started_date": {"$ne": None}}, {"_id": 0, "id": 1}):
                update_fields["started_date"] = datetime.now(timezone.utc).isoformat()

    await db.job_tickets.update_one({"id": ticket_id}, {"$set": update_fields})


async def update_order_progress(db, order_id: str):
    """Recompute and save order progress from all its job tickets."""
    tickets = await db.job_tickets.find(
        {"order_id": order_id},
        {"_id": 0, "status": 1, "progress": 1}
    ).to_list(200)

    if not tickets:
        await db.orders.update_one({"id": order_id}, {"$set": {
            "overall_progress": 0.0,
            "job_ticket_count": 0,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }})
        return

    total_progress = sum(t.get("progress", 0) for t in tickets)
    avg_progress = round(total_progress / len(tickets), 1) if tickets else 0.0

    statuses = [t["status"] for t in tickets]
    update_fields = {
        "overall_progress": avg_progress,
        "job_ticket_count": len(tickets),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Roll-up status
    if all(s == JobTicketStatus.COMPLETED.value for s in statuses):
        update_fields["status"] = OrderStatus.READY_FOR_PICKUP.value
    elif any(s == JobTicketStatus.ON_HOLD.value for s in statuses):
        update_fields["status"] = OrderStatus.ON_HOLD.value
    elif any(s == JobTicketStatus.COMPLETED.value for s in statuses) and not all(s == JobTicketStatus.COMPLETED.value for s in statuses):
        update_fields["status"] = OrderStatus.PARTIALLY_COMPLETE.value
    elif any(s in (JobTicketStatus.IN_PRODUCTION.value, JobTicketStatus.IN_QC.value, JobTicketStatus.REWORK.value) for s in statuses):
        update_fields["status"] = OrderStatus.IN_PRODUCTION.value

    await db.orders.update_one({"id": order_id}, {"$set": update_fields})


async def log_activity(db, order_id: str, tenant_id: str, entity_type: str, entity_id: str, action: str, description: str, user_id: str = "", user_name: str = "", old_value: str = None, new_value: str = None):
    """Log an activity entry for an order."""
    entry = OrderActivity(
        order_id=order_id,
        tenant_id=tenant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        description=description,
        user_id=user_id,
        user_name=user_name,
        old_value=old_value,
        new_value=new_value,
    )
    await db.order_activities.insert_one(entry.model_dump())
