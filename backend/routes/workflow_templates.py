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
from models.orders import WorkflowTemplate
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
