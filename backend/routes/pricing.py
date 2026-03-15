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
        category = PricingCategory(request.get("category", "custom"))
        pricing_data = JobItemPricingData(**request.get("pricing_data", {}))
        quantity = request.get("quantity", 1)
        
        calculation = await calculate_pricing(
            category,
            pricing_data,
            quantity,
            current_user.tenant_id
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
    if current_user.role not in ["owner", "admin"]:
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
    materials = {
        "vinyl": [
            {"id": "oracal_651", "name": "Oracal 651 (Intermediate)", "cost_per_sqft": 0.50},
            {"id": "oracal_751", "name": "Oracal 751 (High Performance)", "cost_per_sqft": 0.75},
            {"id": "oracal_951", "name": "Oracal 951 (Premium Cast)", "cost_per_sqft": 1.25},
            {"id": "avery_hp750", "name": "Avery HP750", "cost_per_sqft": 0.90},
            {"id": "reflective", "name": "Reflective Vinyl", "cost_per_sqft": 2.50},
            {"id": "specialty", "name": "Specialty Vinyl", "cost_per_sqft": 1.50},
        ],
        "print_material": [
            {"id": "banner_13oz", "name": "13oz Banner", "cost_per_sqft": 0.75},
            {"id": "banner_18oz", "name": "18oz Banner (Heavy)", "cost_per_sqft": 1.10},
            {"id": "vinyl_adhesive", "name": "Adhesive Vinyl", "cost_per_sqft": 1.25},
            {"id": "poster_paper", "name": "Poster Paper", "cost_per_sqft": 0.35},
            {"id": "canvas", "name": "Canvas", "cost_per_sqft": 2.50},
            {"id": "backlit", "name": "Backlit Film", "cost_per_sqft": 2.00},
            {"id": "perforated", "name": "Perforated Window Film", "cost_per_sqft": 1.75},
        ],
        "substrate": [
            {"id": "coroplast_4mm", "name": "Coroplast 4mm", "cost_per_sqft": 0.45},
            {"id": "coroplast_10mm", "name": "Coroplast 10mm", "cost_per_sqft": 0.65},
            {"id": "aluminum_040", "name": "Aluminum .040", "cost_per_sqft": 1.50},
            {"id": "aluminum_063", "name": "Aluminum .063", "cost_per_sqft": 2.25},
            {"id": "aluminum_080", "name": "Aluminum .080", "cost_per_sqft": 3.00},
            {"id": "pvc_3mm", "name": "PVC 3mm", "cost_per_sqft": 1.00},
            {"id": "pvc_6mm", "name": "PVC 6mm", "cost_per_sqft": 1.50},
            {"id": "acrylic", "name": "Acrylic", "cost_per_sqft": 4.00},
            {"id": "dibond", "name": "Dibond/ACM", "cost_per_sqft": 3.50},
            {"id": "mdo", "name": "MDO Plywood", "cost_per_sqft": 2.00},
        ],
        "apparel": [
            {"id": "tshirt", "name": "T-Shirt", "cost_each": 4.50},
            {"id": "hoodie", "name": "Hoodie", "cost_each": 18.00},
            {"id": "hat", "name": "Hat/Cap", "cost_each": 8.00},
            {"id": "polo", "name": "Polo Shirt", "cost_each": 12.00},
            {"id": "tank", "name": "Tank Top", "cost_each": 4.00},
            {"id": "longsleeve", "name": "Long Sleeve", "cost_each": 7.50},
            {"id": "jacket", "name": "Jacket", "cost_each": 25.00},
        ],
        "transfer_type": [
            {"id": "htv", "name": "HTV (Heat Transfer Vinyl)", "cost_per_color": 0.50},
            {"id": "screen_print", "name": "Screen Print", "cost_per_color": 0.35},
            {"id": "dtf", "name": "DTF (Direct to Film)", "cost_per_color": 0.75},
            {"id": "sublimation", "name": "Sublimation", "cost_per_color": 1.00},
            {"id": "embroidery", "name": "Embroidery", "cost_per_stitch": 0.01},
        ],
        "vehicle_type": [
            {"id": "car_sedan", "name": "Car (Sedan)", "base_sqft": 150},
            {"id": "car_suv", "name": "Car (SUV)", "base_sqft": 200},
            {"id": "van_mini", "name": "Minivan", "base_sqft": 180},
            {"id": "van_cargo", "name": "Cargo Van", "base_sqft": 250},
            {"id": "van_sprinter", "name": "Sprinter Van", "base_sqft": 350},
            {"id": "box_truck_12ft", "name": "Box Truck (12ft)", "base_sqft": 400},
            {"id": "box_truck_16ft", "name": "Box Truck (16ft)", "base_sqft": 500},
            {"id": "box_truck_24ft", "name": "Box Truck (24ft)", "base_sqft": 650},
            {"id": "trailer", "name": "Trailer", "base_sqft": 450},
            {"id": "semi", "name": "Semi Truck", "base_sqft": 800},
        ]
    }
    
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
