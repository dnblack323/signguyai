from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth_deps import get_current_active_user
from models import UserInDB
from server import db

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


class StepStatusUpdate(BaseModel):
    status: str  # completed | finish_later | incomplete


class OnboardingSessionUpdate(BaseModel):
    current_tier: str
    current_step_id: str


async def compute_step_statuses(tenant_id: str) -> Dict[str, str]:
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0}) or {}
    pricing_config = await db.pricing_configuration.find_one({"tenant_id": tenant_id}, {"_id": 0}) or {}
    workflow_settings = await db.production_workflow_settings.find_one({"tenant_id": tenant_id}, {"_id": 0}) or {}
    onboarding_progress = await db.onboarding_progress.find_one({"tenant_id": tenant_id}, {"_id": 0}) or {"step_statuses": {}}
    manual = onboarding_progress.get("step_statuses", {})

    employee_count = await db.employees.count_documents({"tenant_id": tenant_id})
    job_count = await db.jobs.count_documents({"tenant_id": tenant_id})
    proof_count = await db.artwork_proofs.count_documents({"tenant_id": tenant_id})
    portal_docs_count = await db.portal_documents.count_documents({"tenant_id": tenant_id})
    form_requests_count = await db.portal_form_requests.count_documents({"tenant_id": tenant_id})
    questionnaire_count = await db.questionnaires.count_documents({"tenant_id": tenant_id})
    pricing_import_count = await db.pricing_imports.count_documents({"tenant_id": tenant_id, "status": {"$in": ["analyzed", "reviewed"]}})
    workflow_template_count = await db.workflow_templates.count_documents({"tenant_id": tenant_id})
    pricing_template_count = await db.pricing_templates.count_documents({"tenant_id": tenant_id})
    community_post_count = await db.community_posts.count_documents({"tenant_id": tenant_id}) if "community_posts" in await db.list_collection_names() else 0
    proof_responses = await db.artwork_proofs.count_documents({"tenant_id": tenant_id, "status": {"$in": ["approved", "revision_requested", "rejected"]}})
    paid_invoices = await db.invoices.count_documents({"tenant_id": tenant_id, "status": "paid"})
    production_timelines = await db.production_timelines.count_documents({"tenant_id": tenant_id})
    dashboard_preferences = await db.profit_analytics_preferences.count_documents({"tenant_id": tenant_id})

    required_material_keys = {"vinyl", "banner_material", "coroplast"}
    material_keys = {material.get("key") for material in pricing_config.get("materials", [])}
    portal_settings = tenant.get("customer_portal_settings", {}) or {}

    derived = {
        "quick_company_profile": bool(tenant.get("name") and tenant.get("owner_email") and tenant.get("phone") and tenant.get("address") and tenant.get("logo_url")),
        "quick_stripe_connect": bool(tenant.get("stripe_connect_account_id")),
        "quick_production_workflow": bool(workflow_settings.get("workflow_mode")),
        "quick_first_employee": employee_count > 0,
        "quick_basic_pricing": required_material_keys.issubset(material_keys) and bool(pricing_config.get("production_hourly_rate")),
        "quick_customer_portal": any(portal_settings.values()),
        "quick_first_job": job_count > 0,
        "quick_portal_test": proof_count > 0 and portal_docs_count > 0,

        "standard_historical_invoices": pricing_import_count > 0,
        "standard_detailed_pricing": all(pricing_config.get(field) not in [None, 0, ""] for field in ["design_hourly_rate", "production_hourly_rate", "installer_hourly_rate", "overhead_percentage", "target_profit_margin_percent", "default_markup_multiplier"]),
        "standard_product_categories": bool(pricing_config.get("category_defaults")),
        "standard_category_workflows": bool(workflow_settings.get("category_template_map") or workflow_template_count > 0),
        "standard_document_types": bool(manual.get("standard_document_types") == "completed"),
        "standard_questionnaires": questionnaire_count > 0,
        "standard_notifications": bool(tenant.get("notification_preferences") or manual.get("standard_notifications") == "completed"),
        "standard_ai_access": bool(manual.get("standard_ai_access") == "completed"),
        "standard_job_templates": pricing_template_count > 0,
        "standard_portal_review": any(portal_settings.values()),
        "standard_full_test": proof_responses > 0 and form_requests_count > 0 and paid_invoices > 0,

        "full_production_analytics": production_timelines > 0,
        "full_labor_cost_integration": all(pricing_config.get(field) not in [None, 0, ""] for field in ["design_hourly_rate", "production_hourly_rate", "installer_hourly_rate"]),
        "full_profit_analytics": dashboard_preferences > 0,
        "full_workflow_automation": bool(manual.get("full_workflow_automation") == "completed"),
        "full_customer_experience": proof_responses > 0 and portal_docs_count > 0,
        "full_install_scheduling": bool(manual.get("full_install_scheduling") == "completed"),
        "full_advanced_pricing": pricing_import_count > 0 and dashboard_preferences > 0,
        "full_dashboard_customization": dashboard_preferences > 0,
        "full_security_review": bool(tenant.get("employee_portal_settings")),
        "full_backup_safety": bool(manual.get("full_backup_safety") == "completed"),
        "full_health_check": bool(manual.get("full_health_check") == "completed"),
        "full_community_post": community_post_count > 0,
    }

    status_map = {}
    for step_id, is_complete in derived.items():
        if is_complete:
            status_map[step_id] = "completed"
        else:
            status_map[step_id] = manual.get(step_id, "incomplete")

    return status_map


@router.get("/status")
async def get_onboarding_program_status(current_user: UserInDB = Depends(get_current_active_user)):
    tenant_id = current_user.tenant_id
    progress = await db.onboarding_progress.find_one({"tenant_id": tenant_id}, {"_id": 0}) or {"step_statuses": {}}
    step_statuses = await compute_step_statuses(tenant_id)

    tier_map = {
        "quick_start": [key for key in step_statuses if key.startswith("quick_")],
        "standard_setup": [key for key in step_statuses if key.startswith("standard_")],
        "full_optimization": [key for key in step_statuses if key.startswith("full_")],
    }
    analytics = {}
    for tier_id, step_ids in tier_map.items():
        completed = len([step_id for step_id in step_ids if step_statuses.get(step_id) == "completed"])
        finish_later = len([step_id for step_id in step_ids if step_statuses.get(step_id) == "finish_later"])
        analytics[tier_id] = {
            "total_steps": len(step_ids),
            "completed_steps": completed,
            "finish_later_steps": finish_later,
            "completion_percent": round((completed / len(step_ids)) * 100) if step_ids else 0,
        }

    return {
        "step_statuses": step_statuses,
        "progress": progress,
        "analytics": analytics,
    }


@router.put("/steps/{step_id}")
async def update_onboarding_step(
    step_id: str,
    payload: StepStatusUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if payload.status not in ["completed", "finish_later", "incomplete"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    progress = await db.onboarding_progress.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0}) or {
        "tenant_id": current_user.tenant_id,
        "step_statuses": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    step_statuses = progress.get("step_statuses", {})
    if payload.status == "incomplete":
        step_statuses.pop(step_id, None)
    else:
        step_statuses[step_id] = payload.status

    progress["step_statuses"] = step_statuses
    progress["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.onboarding_progress.update_one(
        {"tenant_id": current_user.tenant_id},
        {"$set": progress},
        upsert=True,
    )
    return {"step_id": step_id, "status": payload.status}


@router.put("/session")
async def update_onboarding_session(
    payload: OnboardingSessionUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    progress = await db.onboarding_progress.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0}) or {
        "tenant_id": current_user.tenant_id,
        "step_statuses": {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    progress["current_tier"] = payload.current_tier
    progress["current_step_id"] = payload.current_step_id
    progress["last_opened_at"] = datetime.now(timezone.utc).isoformat()
    progress["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.onboarding_progress.update_one(
        {"tenant_id": current_user.tenant_id},
        {"$set": progress},
        upsert=True,
    )
    return {
        "current_tier": payload.current_tier,
        "current_step_id": payload.current_step_id,
        "last_opened_at": progress["last_opened_at"],
    }