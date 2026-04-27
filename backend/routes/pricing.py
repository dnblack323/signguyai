"""
Pricing Calculator Routes

This module contains all routes related to:
- Price calculation for various product categories
- Pricing defaults management
- Pricing templates (saved configurations)
- Materials catalog
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from models import (
    UserInDB, PricingCategory,
    PricingDefaults, PricingCalculation, JobItemPricingData,
    PricingTemplate, PricingTemplateCreate
)

# Import from server module
from server import (
    db, logger,
    get_current_active_user,
    get_pricing_defaults, calculate_pricing
)

router = APIRouter(prefix="/pricing", tags=["Pricing"])


def _normalize_pricing_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(payload or {})
    substrate = normalized.get("substrate_type")
    thickness = normalized.get("thickness")
    print_material = normalized.get("print_material")
    substrate_map = {
        ("coroplast", "4mm"): "coroplast_4mm",
        ("coroplast", "10mm"): "coroplast_10mm",
        ("aluminum", "0.040"): "aluminum_040",
        ("aluminum", "0.063"): "aluminum_063",
        ("aluminum", "0.080"): "aluminum_080",
        ("pvc", "3mm_pvc"): "pvc_3mm",
        ("pvc", "6mm_pvc"): "pvc_6mm",
    }
    if substrate and thickness:
        normalized["substrate_type"] = substrate_map.get((str(substrate).lower(), str(thickness).lower()), substrate)
    print_material_map = {
        "13oz_vinyl": "banner_13oz",
        "18oz_vinyl": "banner_18oz",
        "adhesive_vinyl": "vinyl_adhesive",
        "mesh_banner": "banner_13oz",
    }
    if print_material:
        normalized["print_material"] = print_material_map.get(str(print_material).lower(), print_material)
    return normalized


def _normalize_pricing_category(category: Any) -> PricingCategory:
    raw = str(category or "custom").lower()
    alias_map = {
        "promo_misc": PricingCategory.PROMOTIONAL,
        "vehicle_wrap": PricingCategory.VEHICLE_GRAPHICS,
    }
    if raw in alias_map:
        return alias_map[raw]
    return PricingCategory(raw)


# ============== PRICING CALCULATION ==============

class PriceCalculateRequest:
    """Request model for price calculation"""
    def __init__(
        self,
        category: PricingCategory,
        pricing_data: Dict[str, Any],
        quantity: float = 1
    ):
        self.category = category
        self.pricing_data = pricing_data
        self.quantity = quantity


@router.post("/calculate")
async def calculate_price(
    request: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Calculate pricing for an item (real-time preview)"""
    try:
        category = _normalize_pricing_category(request.get("category", "custom"))
        pricing_data = JobItemPricingData(**_normalize_pricing_payload(request.get("pricing_data", {})))
        quantity = request.get("quantity", 1)
        
        calculation = await calculate_pricing(
            category,
            pricing_data,
            quantity,
            current_user.tenant_id,
            user_id=current_user.id,
        )
        return calculation.model_dump()
    except Exception as e:
        logger.error(f"Pricing calculation error: {e}")
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


# ============== PRICING DEFAULTS ==============

@router.get("/defaults")
async def get_my_pricing_defaults(current_user: UserInDB = Depends(get_current_active_user)):
    """Get pricing defaults for current tenant"""
    defaults = await get_pricing_defaults(current_user.tenant_id)
    return defaults


@router.get("/settings")
async def get_my_pricing_settings(current_user: UserInDB = Depends(get_current_active_user)):
    """Alias for pricing defaults/settings."""
    return await get_pricing_defaults(current_user.tenant_id)


@router.put("/defaults")
async def update_pricing_defaults(
    updates: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update pricing defaults for current tenant"""
    if current_user.role not in ["owner", "admin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can update pricing settings")

    tenant_id = current_user.tenant_id

    current_defaults = await get_pricing_defaults(tenant_id)
    merged = {**current_defaults, **updates}
    if "category_defaults" in updates:
        merged["category_defaults"] = {
            **current_defaults.get("category_defaults", {}),
            **updates.get("category_defaults", {}),
        }
    if "selling_price_benchmarks" in updates:
        merged["selling_price_benchmarks"] = {
            **current_defaults.get("selling_price_benchmarks", {}),
            **updates.get("selling_price_benchmarks", {}),
        }
    if "labor_rates" in updates:
        merged["labor_rates"] = {
            **current_defaults.get("labor_rates", {}),
            **updates.get("labor_rates", {}),
        }
    if "ai_estimation_rules" in updates:
        merged["ai_estimation_rules"] = {
            **current_defaults.get("ai_estimation_rules", {}),
            **updates.get("ai_estimation_rules", {}),
        }
    if "benchmark_rules" in updates:
        merged["benchmark_rules"] = {
            **current_defaults.get("benchmark_rules", {}),
            **updates.get("benchmark_rules", {}),
        }
    if "global_calc_rules" in updates:
        merged["global_calc_rules"] = {
            **current_defaults.get("global_calc_rules", {}),
            **updates.get("global_calc_rules", {}),
        }

    merged["tenant_id"] = tenant_id
    merged["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.pricing_configuration.update_one(
        {"tenant_id": tenant_id},
        {"$set": merged},
        upsert=True,
    )

    return await get_pricing_defaults(tenant_id)


@router.put("/settings")
async def update_pricing_settings(
    updates: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Alias for updating pricing settings."""
    return await update_pricing_defaults(updates, current_user)


# ============== MATERIALS CATALOG ==============

@router.get("/materials")
async def get_materials(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get available materials (for dropdowns)"""
    from routes.job_tickets import _build_materials_catalog

    defaults = await get_pricing_defaults(current_user.tenant_id)
    materials = _build_materials_catalog(defaults)
    if "decoration" in materials and "transfer_type" not in materials:
        materials["transfer_type"] = materials["decoration"]
    
    if category:
        return {category: materials.get(category, [])}
    return materials


# ============== PRICING TEMPLATES ==============

@router.get("/templates")
async def get_pricing_templates(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all pricing templates for the current tenant"""
    query = {"tenant_id": current_user.tenant_id}
    if category:
        query["category"] = category
    
    templates = await db.pricing_templates.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    return templates


@router.post("/templates")
async def create_pricing_template(
    input: PricingTemplateCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Save a new pricing template"""
    template = PricingTemplate(
        tenant_id=current_user.tenant_id,
        name=input.name,
        description=input.description,
        category=input.category,
        pricing_data=input.pricing_data,
        quantity=input.quantity
    )
    await db.pricing_templates.insert_one(template.model_dump())
    return template.model_dump()


@router.put("/templates/{template_id}")
async def update_pricing_template(
    template_id: str,
    updates: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a pricing template"""
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.pricing_templates.update_one(
        {"id": template_id, "tenant_id": current_user.tenant_id},
        {"$set": updates}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = await db.pricing_templates.find_one({"id": template_id}, {"_id": 0})
    return template


@router.delete("/templates/{template_id}")
async def delete_pricing_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a pricing template"""
    result = await db.pricing_templates.delete_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"message": "Template deleted"}


@router.put("/templates/{template_id}/favorite")
async def toggle_template_favorite(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Toggle favorite status of a template"""
    template = await db.pricing_templates.find_one(
        {"id": template_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    new_status = not template.get("is_favorite", False)
    await db.pricing_templates.update_one(
        {"id": template_id},
        {"$set": {"is_favorite": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"is_favorite": new_status}
