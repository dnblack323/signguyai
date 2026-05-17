"""
Wrap Command Center — Phase 2A backend.

Stores wrap-specific data (vehicle info + wrapped areas) for a single
order item (job_ticket). The job_ticket and its parent order remain the
source of truth for customer / pricing / payments / due dates. This file
ONLY persists wrap-workflow detail fields that don't belong on the
generic JobTicket.

Storage: MongoDB collection `wrap_data` — one document per (tenant_id, ticket_id).
"""
from datetime import datetime, timezone
from typing import Optional, List
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from models import UserInDB
from server import db, get_current_active_user
from services.workflow_engine import update_order_progress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wrap", tags=["Wrap Command Center"])

# Categories that are considered wrap-workflow eligible.
# Mirrored from frontend `components/wrap/constants.js`.
_WRAP_CATEGORIES = {
    "vehicle_wrap", "vehicle_wraps", "wraps", "vehicle_graphics",
    "fleet_graphics", "trailer_wraps", "box_truck_wraps", "commercial_wraps",
    "vehicle_wraps_graphics",
}


def _is_wrap_category(category: Optional[str]) -> bool:
    if not category:
        return False
    norm = str(category).lower().replace(" ", "_").replace("&", "_")
    return norm in _WRAP_CATEGORIES or "wrap" in norm


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ────────── Pydantic models ──────────
class VehicleInfo(BaseModel):
    year: Optional[str] = ""
    make: Optional[str] = ""
    model: Optional[str] = ""
    trim: Optional[str] = ""
    body_type: Optional[str] = ""
    roof_height: Optional[str] = ""
    wheelbase: Optional[str] = ""
    vehicle_color: Optional[str] = ""
    license_plate: Optional[str] = ""
    vin: Optional[str] = ""
    existing_graphics: Optional[bool] = False
    existing_wrap: Optional[bool] = False
    paint_condition: Optional[str] = ""
    body_condition: Optional[str] = ""
    vehicle_notes: Optional[str] = ""
    template_type: Optional[str] = ""
    customer_photo_placeholders: List[str] = Field(default_factory=list)


class WrappedArea(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    area_name: str = ""
    width: Optional[float] = None
    height: Optional[float] = None
    unit: str = "in"  # "in" or "ft"
    raw_sqft: Optional[float] = None
    waste_percent: Optional[float] = 15.0
    billable_sqft: Optional[float] = None
    material: Optional[str] = ""
    laminate: Optional[str] = ""
    complexity: Optional[str] = "medium"  # low | medium | high
    included: bool = True
    notes: Optional[str] = ""


class WrappedAreaCreate(BaseModel):
    area_name: str = ""
    width: Optional[float] = None
    height: Optional[float] = None
    unit: str = "in"
    waste_percent: Optional[float] = 15.0
    material: Optional[str] = ""
    laminate: Optional[str] = ""
    complexity: Optional[str] = "medium"
    included: bool = True
    notes: Optional[str] = ""


class WrappedAreaUpdate(BaseModel):
    area_name: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    unit: Optional[str] = None
    waste_percent: Optional[float] = None
    material: Optional[str] = None
    laminate: Optional[str] = None
    complexity: Optional[str] = None
    included: Optional[bool] = None
    notes: Optional[str] = None


# ────────── Phase 2B: Pricing & Materials models ──────────
class WrapMaterial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    material_name: str = ""
    brand: str = ""
    product_code: str = ""
    material_type: str = "printed_wrap_vinyl"  # see WRAP_MATERIAL_TYPES
    roll_width: Optional[str] = ""
    sqft_used: Optional[float] = None
    cost_per_sqft: Optional[float] = None
    total_material_cost: Optional[float] = None
    supplier: str = ""
    in_stock: bool = False
    ordered: bool = False
    notes: str = ""


class WrapMaterialCreate(BaseModel):
    material_name: str = ""
    brand: str = ""
    product_code: str = ""
    material_type: str = "printed_wrap_vinyl"
    roll_width: Optional[str] = ""
    sqft_used: Optional[float] = None
    cost_per_sqft: Optional[float] = None
    supplier: str = ""
    in_stock: bool = False
    ordered: bool = False
    notes: str = ""


class WrapMaterialUpdate(BaseModel):
    material_name: Optional[str] = None
    brand: Optional[str] = None
    product_code: Optional[str] = None
    material_type: Optional[str] = None
    roll_width: Optional[str] = None
    sqft_used: Optional[float] = None
    cost_per_sqft: Optional[float] = None
    supplier: Optional[str] = None
    in_stock: Optional[bool] = None
    ordered: Optional[bool] = None
    notes: Optional[str] = None


class WrapPricingConfig(BaseModel):
    pricing_method: str = "material_labor_markup"  # per_sqft | material_labor_markup | manual
    price_per_sqft: Optional[float] = 0.0
    design_hours: Optional[float] = 0.0
    production_hours: Optional[float] = 0.0
    install_hours: Optional[float] = 0.0
    labor_rate: Optional[float] = 75.0
    removal_fee: Optional[float] = 0.0
    prep_fee: Optional[float] = 0.0
    rush_fee: Optional[float] = 0.0
    travel_fee: Optional[float] = 0.0
    setup_design_fee: Optional[float] = 0.0
    misc_cost: Optional[float] = 0.0
    laminate_cost: Optional[float] = 0.0
    ink_consumables_cost: Optional[float] = 0.0
    markup_percent: Optional[float] = 30.0
    manual_quoted_price: Optional[float] = None


WRAP_MATERIAL_TYPES = [
    "printed_wrap_vinyl", "color_change_vinyl", "laminate", "window_perf",
    "transfer_tape", "knifeless_tape", "primer", "edge_sealer",
    "cleaning_prep_supply", "other",
]


# ────────── helpers ──────────

def _compute_area_sqft(width: Optional[float], height: Optional[float], unit: str, waste_percent: Optional[float]):
    """Return (raw_sqft, billable_sqft) or (None, None) when inputs incomplete."""
    if width is None or height is None or width <= 0 or height <= 0:
        return None, None
    if (unit or "in").lower() == "ft":
        raw = float(width) * float(height)
    else:
        raw = (float(width) * float(height)) / 144.0
    waste = float(waste_percent) if waste_percent is not None else 0.0
    billable = raw * (1.0 + waste / 100.0)
    return round(raw, 2), round(billable, 2)


def _apply_area_math(area: dict) -> dict:
    raw, billable = _compute_area_sqft(
        area.get("width"), area.get("height"), area.get("unit", "in"), area.get("waste_percent")
    )
    area["raw_sqft"] = raw
    area["billable_sqft"] = billable
    return area


def _empty_doc(tenant_id: str, ticket_id: str, order_id: str) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "ticket_id": ticket_id,
        "order_id": order_id,
        "vehicle_info": VehicleInfo().model_dump(),
        "wrapped_areas": [],
        "materials": [],
        "pricing": WrapPricingConfig().model_dump(),
        "pricing_snapshot": None,
        "created_at": _now(),
        "updated_at": _now(),
    }


def _coverage_summary(areas: List[dict]) -> dict:
    included = [a for a in areas if a.get("included")]
    excluded_count = len(areas) - len(included)
    total_raw = round(sum((a.get("raw_sqft") or 0.0) for a in included), 2)
    total_billable = round(sum((a.get("billable_sqft") or 0.0) for a in included), 2)
    waste_values = [a.get("waste_percent") for a in included if a.get("waste_percent") is not None]
    avg_waste = round(sum(waste_values) / len(waste_values), 2) if waste_values else 0.0
    return {
        "total_raw_sqft": total_raw,
        "total_billable_sqft": total_billable,
        "average_waste_percent": avg_waste,
        "included_count": len(included),
        "excluded_count": excluded_count,
    }


def _compute_material_total(material: dict) -> dict:
    sqft = material.get("sqft_used")
    cps = material.get("cost_per_sqft")
    if sqft is not None and cps is not None:
        material["total_material_cost"] = round(float(sqft) * float(cps), 2)
    else:
        material["total_material_cost"] = None
    return material


def _compute_pricing_snapshot(pricing: dict, materials: List[dict], coverage: dict) -> dict:
    """Pure pricing math. Returns the snapshot block stored on the wrap doc.

    Formulas (per phase-2B spec):
      total_labor_cost   = (design + production + install) * labor_rate
      material_total     = sum(total_material_cost) + laminate_cost + ink_consumables_cost
      base_cost          = material_total + total_labor_cost + removal + prep + travel + misc
      markup_amount      = base_cost * markup_percent/100
      suggested_price    = base_cost + markup_amount + setup_design_fee + rush_fee
      per_sqft_price     = total_billable_sqft * price_per_sqft + setup_design_fee + rush_fee + travel + prep + removal + misc
      quoted_price       = manual_quoted_price if method == manual else per_sqft_price/suggested_price
      estimated_profit   = quoted_price - base_cost
      estimated_margin_% = profit / quoted_price * 100 if quoted_price else 0
    """
    p = pricing or {}
    def n(v):
        try:
            return float(v) if v is not None else 0.0
        except (TypeError, ValueError):
            return 0.0

    total_billable = n((coverage or {}).get("total_billable_sqft"))
    design_h = n(p.get("design_hours"))
    prod_h = n(p.get("production_hours"))
    install_h = n(p.get("install_hours"))
    labor_rate = n(p.get("labor_rate"))
    total_labor_cost = round((design_h + prod_h + install_h) * labor_rate, 2)

    materials_sum = sum(n(m.get("total_material_cost")) for m in (materials or []))
    material_total = round(materials_sum + n(p.get("laminate_cost")) + n(p.get("ink_consumables_cost")), 2)

    removal = n(p.get("removal_fee"))
    prep = n(p.get("prep_fee"))
    travel = n(p.get("travel_fee"))
    misc = n(p.get("misc_cost"))
    setup_design = n(p.get("setup_design_fee"))
    rush = n(p.get("rush_fee"))

    base_cost = round(material_total + total_labor_cost + removal + prep + travel + misc, 2)
    markup_percent = n(p.get("markup_percent"))
    markup_amount = round(base_cost * markup_percent / 100.0, 2)
    suggested_price_mlm = round(base_cost + markup_amount + setup_design + rush, 2)

    price_per_sqft = n(p.get("price_per_sqft"))
    per_sqft_price = round(
        total_billable * price_per_sqft + setup_design + rush + travel + prep + removal + misc, 2
    )

    method = (p.get("pricing_method") or "material_labor_markup").lower()
    manual = p.get("manual_quoted_price")
    manual_n = n(manual) if manual not in (None, "") else None

    if method == "manual" and manual_n is not None:
        quoted_price = round(manual_n, 2)
        suggested_price = quoted_price
    elif method == "per_sqft":
        suggested_price = per_sqft_price
        quoted_price = round(manual_n, 2) if manual_n is not None else per_sqft_price
    else:
        method = "material_labor_markup"
        suggested_price = suggested_price_mlm
        quoted_price = round(manual_n, 2) if manual_n is not None else suggested_price_mlm

    estimated_profit = round(quoted_price - base_cost, 2)
    estimated_margin_percent = round((estimated_profit / quoted_price) * 100.0, 2) if quoted_price else 0.0

    return {
        "pricing_method": method,
        "total_billable_sqft": round(total_billable, 2),
        "total_labor_cost": total_labor_cost,
        "material_total": material_total,
        "base_cost": base_cost,
        "markup_percent": markup_percent,
        "markup_amount": markup_amount,
        "suggested_price": round(suggested_price, 2),
        "per_sqft_price": per_sqft_price,
        "manual_quoted_price": round(manual_n, 2) if manual_n is not None else None,
        "quoted_price": quoted_price,
        "estimated_profit": estimated_profit,
        "estimated_margin_percent": estimated_margin_percent,
        "computed_at": _now(),
    }


async def _load_ticket_or_404(ticket_id: str, tenant_id: str) -> dict:
    ticket = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Job ticket not found")
    if not _is_wrap_category(ticket.get("item_category")):
        raise HTTPException(status_code=400, detail="Job ticket is not a wrap category")
    return ticket


async def _get_or_create_doc(tenant_id: str, ticket: dict) -> dict:
    existing = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket["id"]}, {"_id": 0}
    )
    if existing:
        return existing
    doc = _empty_doc(tenant_id, ticket["id"], ticket.get("order_id", ""))
    await db.wrap_data.insert_one(doc.copy())
    # remove _id that motor may add to original dict on insert
    return {k: v for k, v in doc.items() if k != "_id"}


def _serialize(doc: dict) -> dict:
    """Strip Mongo _id, ensure new fields exist on older docs, attach coverage summary."""
    safe = {k: v for k, v in doc.items() if k != "_id"}
    safe.setdefault("materials", [])
    safe.setdefault("pricing", WrapPricingConfig().model_dump())
    safe.setdefault("pricing_snapshot", None)
    safe["coverage_summary"] = _coverage_summary(safe.get("wrapped_areas") or [])
    return safe


async def _sync_vehicle_to_ticket(tenant_id: str, ticket_id: str, vehicle: dict):
    """Mirror basic vehicle fields into JobTicket.specs so the standard
    order item card and Work-Ticket PDF can show vehicle info without
    duplicate entry. Uses `$set` on dotted keys so we don't overwrite
    unrelated spec fields. JobTicketSpecs has `extra=allow` so these
    additional keys persist safely.
    """
    if not vehicle:
        return
    field_map = {
        "year": "vehicle_year",
        "make": "vehicle_make",
        "model": "vehicle_model",
        "trim": "vehicle_trim",
        "body_type": "vehicle_body_type",
        "vehicle_color": "vehicle_color",
    }
    updates = {}
    for src, dst in field_map.items():
        val = vehicle.get(src)
        if val is not None:
            updates[f"specs.{dst}"] = val
    if not updates:
        return
    try:
        await db.job_tickets.update_one(
            {"id": ticket_id, "tenant_id": tenant_id},
            {"$set": updates},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("Vehicle sync to ticket %s failed: %s", ticket_id, e)


# ────────── routes ──────────
@router.get("/items/{ticket_id}")
async def get_wrap_data(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await _get_or_create_doc(current_user.tenant_id, ticket)
    return _serialize(doc)


@router.put("/items/{ticket_id}/vehicle")
async def update_vehicle_info(
    ticket_id: str,
    payload: VehicleInfo,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    vehicle = payload.model_dump()
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"vehicle_info": vehicle, "updated_at": _now()}},
    )
    # Phase 2B: mirror basic vehicle fields into JobTicket.specs so the
    # standard OrderDetail card and Work-Ticket PDF see them too.
    await _sync_vehicle_to_ticket(current_user.tenant_id, ticket_id, vehicle)
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(doc)


@router.post("/items/{ticket_id}/areas")
async def add_wrapped_area(
    ticket_id: str,
    payload: WrappedAreaCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)

    area = WrappedArea(**payload.model_dump()).model_dump()
    area = _apply_area_math(area)

    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$push": {"wrapped_areas": area}, "$set": {"updated_at": _now()}},
    )
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(doc)


@router.put("/items/{ticket_id}/areas/{area_id}")
async def update_wrapped_area(
    ticket_id: str,
    area_id: str,
    payload: WrappedAreaUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    if not doc:
        # Ticket exists & is wrap, but no wrap_data doc yet — create empty so we can update
        await _get_or_create_doc(current_user.tenant_id, ticket)
        doc = await db.wrap_data.find_one(
            {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
        )
    areas = doc.get("wrapped_areas") or []
    found = False
    updates = payload.model_dump(exclude_unset=True)
    for a in areas:
        if a.get("id") == area_id:
            a.update(updates)
            _apply_area_math(a)
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Area not found")
    _ = ticket  # auth side-effect only
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"wrapped_areas": areas, "updated_at": _now()}},
    )
    refreshed = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(refreshed)


@router.delete("/items/{ticket_id}/areas/{area_id}")
async def delete_wrapped_area(
    ticket_id: str,
    area_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    res = await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$pull": {"wrapped_areas": {"id": area_id}}, "$set": {"updated_at": _now()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Wrap data not found")
    refreshed = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(refreshed)



# ────────── Phase 2B: Materials CRUD ──────────
@router.post("/items/{ticket_id}/materials")
async def add_material(
    ticket_id: str,
    payload: WrapMaterialCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    material = WrapMaterial(**payload.model_dump()).model_dump()
    _compute_material_total(material)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$push": {"materials": material}, "$set": {"updated_at": _now()}},
    )
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(doc)


@router.put("/items/{ticket_id}/materials/{material_id}")
async def update_material(
    ticket_id: str,
    material_id: str,
    payload: WrapMaterialUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    if not doc:
        await _get_or_create_doc(current_user.tenant_id, ticket)
        doc = await db.wrap_data.find_one(
            {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
        )
    materials = doc.get("materials") or []
    updates = payload.model_dump(exclude_unset=True)
    found = False
    for m in materials:
        if m.get("id") == material_id:
            m.update(updates)
            _compute_material_total(m)
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Material not found")
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"materials": materials, "updated_at": _now()}},
    )
    refreshed = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(refreshed)


@router.delete("/items/{ticket_id}/materials/{material_id}")
async def delete_material(
    ticket_id: str,
    material_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    res = await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$pull": {"materials": {"id": material_id}}, "$set": {"updated_at": _now()}},
    )
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Wrap data not found")
    refreshed = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(refreshed)


# ────────── Phase 2B: Pricing config + snapshot ──────────
@router.put("/items/{ticket_id}/pricing")
async def update_pricing(
    ticket_id: str,
    payload: WrapPricingConfig,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    pricing = payload.model_dump()
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    coverage = _coverage_summary(doc.get("wrapped_areas") or [])
    snapshot = _compute_pricing_snapshot(pricing, doc.get("materials") or [], coverage)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"pricing": pricing, "pricing_snapshot": snapshot, "updated_at": _now()}},
    )
    refreshed = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(refreshed)


@router.post("/items/{ticket_id}/recalculate")
async def recalculate_pricing(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Recompute the snapshot from the current stored pricing+materials+coverage
    without overwriting the pricing config. Returns the refreshed doc."""
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    pricing = doc.get("pricing") or WrapPricingConfig().model_dump()
    coverage = _coverage_summary(doc.get("wrapped_areas") or [])
    snapshot = _compute_pricing_snapshot(pricing, doc.get("materials") or [], coverage)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"pricing_snapshot": snapshot, "updated_at": _now()}},
    )
    refreshed = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    return _serialize(refreshed)


@router.post("/items/{ticket_id}/apply-price-to-order")
async def apply_price_to_order(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Push the wrap quoted_price into the JobTicket's estimated_price and
    update a small pricing_snapshot block on the ticket. The parent Order's
    aggregate `order_total` will pick this up automatically the next time
    the order is fetched (it sums ticket.estimated_price)."""
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Wrap data not found")
    snap = doc.get("pricing_snapshot")
    if not snap:
        # Compute on the fly if user clicks Apply before Save
        pricing = doc.get("pricing") or WrapPricingConfig().model_dump()
        coverage = _coverage_summary(doc.get("wrapped_areas") or [])
        snap = _compute_pricing_snapshot(pricing, doc.get("materials") or [], coverage)
        await db.wrap_data.update_one(
            {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
            {"$set": {"pricing_snapshot": snap, "updated_at": _now()}},
        )
    quoted = float(snap.get("quoted_price") or 0.0)
    ticket_snapshot = {
        "pricing_mode": "wrap",
        "active_price": quoted,
        "source": "wrap_command_center",
        "wrap_snapshot": snap,
        "computed_at": snap.get("computed_at"),
    }
    await db.job_tickets.update_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id},
        {"$set": {
            "estimated_price": quoted,
            "pricing_snapshot": ticket_snapshot,
            "updated_at": _now(),
        }},
    )
    # Touch the parent order's updated_at so the Orders Dashboard refresh
    # picks up the new total. Recompute aggregate via the shared workflow engine
    # (this updates order.order_total/overall_progress/etc.).
    order_id = ticket.get("order_id")
    if order_id:
        try:
            await update_order_progress(db, order_id)
        except Exception as e:  # noqa: BLE001
            logger.warning("update_order_progress failed for %s: %s", order_id, e)
    refreshed = await db.wrap_data.find_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    result = _serialize(refreshed)
    result["applied_to_ticket"] = {"ticket_id": ticket_id, "estimated_price": quoted}
    return result
