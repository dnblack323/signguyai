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


# ────────── Phase 2C: Design / Contract / Approvals models ──────────
class DesignBlock(BaseModel):
    questionnaire_status: str = "not_sent"  # not_sent | sent | completed | reviewed
    questionnaire_sent_at: Optional[str] = None
    questionnaire_completed_at: Optional[str] = None
    questionnaire_id: Optional[str] = None
    design_brief: str = ""
    style_direction: str = ""
    brand_colors: str = ""
    required_text: str = ""
    services_to_feature: str = ""
    design_notes: str = ""
    artwork_notes: str = ""
    mockup_status: str = "not_started"  # not_started | requested | generated | reviewed
    proof_status: str = "not_started"  # not_started | draft | sent | revision_requested | approved
    approved_proof_id: Optional[str] = None
    revision_notes: str = ""
    revision_count: int = 0
    proof_versions: List[dict] = Field(default_factory=list)


class DesignUpdate(BaseModel):
    design_brief: Optional[str] = None
    style_direction: Optional[str] = None
    brand_colors: Optional[str] = None
    required_text: Optional[str] = None
    services_to_feature: Optional[str] = None
    design_notes: Optional[str] = None
    artwork_notes: Optional[str] = None
    questionnaire_status: Optional[str] = None
    mockup_status: Optional[str] = None
    proof_status: Optional[str] = None
    revision_notes: Optional[str] = None


class ProofVersionCreate(BaseModel):
    label: str = ""
    notes: str = ""


class ProofVersionUpdate(BaseModel):
    label: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # draft | sent | revision_requested | approved


class ContractBlock(BaseModel):
    contract_status: str = "not_created"  # not_created | draft | sent | viewed | signed | stored
    contract_template: str = ""
    contract_id: Optional[str] = None
    contract_sent_at: Optional[str] = None
    contract_viewed_at: Optional[str] = None
    contract_signed_at: Optional[str] = None
    signed_by: str = ""
    signed_contract_url: str = ""
    terms_summary: str = ""
    accepted_terms: bool = False
    contract_notes: str = ""


class ContractUpdate(BaseModel):
    contract_template: Optional[str] = None
    terms_summary: Optional[str] = None
    contract_notes: Optional[str] = None
    signed_by: Optional[str] = None
    signed_contract_url: Optional[str] = None


CONTRACT_ACTIONS = {"generate_draft", "send", "mark_viewed", "mark_signed", "store_signed"}


class ContractAction(BaseModel):
    action: str
    signed_by: Optional[str] = None
    signed_contract_url: Optional[str] = None


APPROVAL_KEYS = [
    "quote_approved", "contract_signed", "deposit_paid", "proof_approved",
    "inspection_acknowledged", "final_signoff_completed", "aftercare_sent",
]


def _empty_approvals() -> dict:
    out = {}
    for k in APPROVAL_KEYS:
        out[k] = False
        out[f"{k}_at"] = None
    return out


class ApprovalsUpdate(BaseModel):
    # Each key is the approval name; value is bool (true/false).
    quote_approved: Optional[bool] = None
    contract_signed: Optional[bool] = None
    deposit_paid: Optional[bool] = None
    proof_approved: Optional[bool] = None
    inspection_acknowledged: Optional[bool] = None
    final_signoff_completed: Optional[bool] = None
    aftercare_sent: Optional[bool] = None


# ────────── Phase 2D: Production / Install models ──────────
PRODUCTION_CHECKLIST_KEYS = [
    "files_ready", "materials_pulled", "printed", "laminated", "outgassed",
    "trimmed", "panels_labeled", "install_kit_ready", "prep_complete", "ready_for_install",
]

PRODUCTION_STATUSES = {
    "not_started", "files_ready", "printing", "printed", "laminated",
    "trimming", "staged", "ready_for_install", "complete",
}

TASK_STATUSES = {"not_started", "in_progress", "blocked", "complete"}

DEFAULT_WRAP_TASKS = [
    "Review approved proof",
    "Prepare print files",
    "Check dimensions/panels",
    "Print wrap panels",
    "Laminate wrap panels",
    "Outgas if required",
    "Trim panels",
    "Label panels",
    "Pull install materials/tools",
    "Stage for install",
]


class ProductionTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    assigned_to: str = ""
    status: str = "not_started"
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    notes: str = ""
    completed_at: Optional[str] = None


class ProductionTaskCreate(BaseModel):
    task_name: str = ""
    assigned_to: str = ""
    status: str = "not_started"
    estimated_minutes: Optional[int] = None
    notes: str = ""


class ProductionTaskUpdate(BaseModel):
    task_name: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    notes: Optional[str] = None


def _empty_production() -> dict:
    out = {
        "production_status": "not_started",
        "assigned_to": "",
        "production_notes": "",
        "tasks": [],
    }
    for k in PRODUCTION_CHECKLIST_KEYS:
        out[k] = False
        out[f"{k}_at"] = None
    return out


class ProductionUpdate(BaseModel):
    production_status: Optional[str] = None
    assigned_to: Optional[str] = None
    production_notes: Optional[str] = None
    # checklist booleans
    files_ready: Optional[bool] = None
    materials_pulled: Optional[bool] = None
    printed: Optional[bool] = None
    laminated: Optional[bool] = None
    outgassed: Optional[bool] = None
    trimmed: Optional[bool] = None
    panels_labeled: Optional[bool] = None
    install_kit_ready: Optional[bool] = None
    prep_complete: Optional[bool] = None
    ready_for_install: Optional[bool] = None


# Install
INSTALL_STATUSES = {
    "not_scheduled", "scheduled", "vehicle_received", "in_progress",
    "installed", "customer_picked_up", "complete",
}

INSTALL_CHECKLIST_KEYS = [
    "vehicle_received", "vehicle_inspected", "surface_cleaned",
    "old_graphics_removed", "panels_staged", "install_started",
    "install_completed", "post_heated", "final_inspection_complete",
    "customer_walkthrough_complete",
]

ISSUE_TYPES = {
    "Misprint", "Wrong size panel", "Color issue", "Bad file",
    "Installer mistake", "Vehicle issue", "Paint failure", "Adhesion issue",
    "Weather issue", "Customer delay", "Material defect", "Other",
}


class InstallIssue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issue_type: str = "Other"
    area: str = ""
    description: str = ""
    photo_placeholder: str = ""
    resolved: bool = False
    resolution_notes: str = ""
    created_at: str = Field(default_factory=_now)
    resolved_at: Optional[str] = None


class InstallIssueCreate(BaseModel):
    issue_type: str = "Other"
    area: str = ""
    description: str = ""
    photo_placeholder: str = ""


class InstallIssueUpdate(BaseModel):
    issue_type: Optional[str] = None
    area: Optional[str] = None
    description: Optional[str] = None
    photo_placeholder: Optional[str] = None
    resolved: Optional[bool] = None
    resolution_notes: Optional[str] = None


def _empty_install_checklist() -> dict:
    return {k: False for k in INSTALL_CHECKLIST_KEYS}


def _empty_install() -> dict:
    return {
        "install_status": "not_scheduled",
        "install_date": None,
        "install_start_time": "",
        "install_end_time": "",
        "installer_name": "",
        "helper_name": "",
        "install_location": "",
        "bay_needed": False,
        "customer_dropoff_time": "",
        "customer_pickup_time": "",
        "hours_estimated": None,
        "hours_actual": None,
        "install_notes": "",
        "completion_notes": "",
        "customer_signoff": False,
        "customer_signoff_at": None,
        "issues": [],
        "checklist": _empty_install_checklist(),
    }


class InstallUpdate(BaseModel):
    install_status: Optional[str] = None
    install_date: Optional[str] = None
    install_start_time: Optional[str] = None
    install_end_time: Optional[str] = None
    installer_name: Optional[str] = None
    helper_name: Optional[str] = None
    install_location: Optional[str] = None
    bay_needed: Optional[bool] = None
    customer_dropoff_time: Optional[str] = None
    customer_pickup_time: Optional[str] = None
    hours_estimated: Optional[float] = None
    hours_actual: Optional[float] = None
    install_notes: Optional[str] = None
    completion_notes: Optional[str] = None
    customer_signoff: Optional[bool] = None
    checklist: Optional[dict] = None  # partial map of keys to bool


# ────────── Phase 2E: Inspection / Aftercare models ──────────
INSPECTION_STATUSES = {"not_started", "in_progress", "completed", "acknowledged"}
DAMAGE_TYPES = {
    "Dent", "Scratch", "Rust", "Paint Chip", "Clear Coat Failure",
    "Loose Trim", "Cracked Part", "Previous Wrap", "Adhesive Residue", "Other Concern",
}
SEVERITIES = {"Low", "Medium", "High", "Severe"}

VEHICLE_DIAGRAM_TYPES = [
    "Generic Van", "Generic Pickup", "Generic Box Truck", "Generic Trailer",
    "Generic SUV", "Generic Sedan", "Generic Ambulance", "Generic Bus",
    "Generic Race Car", "Custom / Other",
]


class DamageMarker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    area: str = ""
    damage_type: str = "Other Concern"
    severity: str = "Low"
    photo_placeholder: str = ""
    notes: str = ""
    x_percent: Optional[float] = None
    y_percent: Optional[float] = None
    marker_label: Optional[str] = ""
    created_at: str = Field(default_factory=_now)
    created_by: str = ""


class DamageMarkerCreate(BaseModel):
    area: str = ""
    damage_type: str = "Other Concern"
    severity: str = "Low"
    photo_placeholder: str = ""
    notes: str = ""
    x_percent: Optional[float] = None
    y_percent: Optional[float] = None
    marker_label: Optional[str] = ""


class DamageMarkerUpdate(BaseModel):
    area: Optional[str] = None
    damage_type: Optional[str] = None
    severity: Optional[str] = None
    photo_placeholder: Optional[str] = None
    notes: Optional[str] = None
    x_percent: Optional[float] = None
    y_percent: Optional[float] = None
    marker_label: Optional[str] = None


def _empty_inspection() -> dict:
    return {
        "inspection_status": "not_started",
        "vehicle_diagram_type": "",
        "inspected_by": "",
        "inspection_date": None,
        "customer_acknowledged": False,
        "customer_acknowledged_at": None,
        "customer_visible": False,
        "inspection_notes": "",
        "damage_markers": [],
    }


class InspectionUpdate(BaseModel):
    inspection_status: Optional[str] = None
    vehicle_diagram_type: Optional[str] = None
    inspected_by: Optional[str] = None
    inspection_date: Optional[str] = None
    customer_acknowledged: Optional[bool] = None
    customer_visible: Optional[bool] = None
    inspection_notes: Optional[str] = None


AFTERCARE_STATUSES = {
    "not_sent", "generated", "sent", "viewed",
    "acknowledged", "followup_active", "complete",
}

AFTERCARE_FOLLOWUP_KEYS = ["followup_24h", "followup_7d", "followup_30d"]


def _empty_aftercare() -> dict:
    out = {
        "aftercare_status": "not_sent",
        "aftercare_template": "",
        "aftercare_sent": False,
        "aftercare_sent_at": None,
        "sent_by": "",
        "customer_viewed": False,
        "customer_viewed_at": None,
        "customer_acknowledged": False,
        "customer_acknowledged_at": None,
        "aftercare_notes": "",
    }
    for k in AFTERCARE_FOLLOWUP_KEYS:
        out[k] = False
        out[f"{k}_at"] = None
    return out


class AftercareUpdate(BaseModel):
    aftercare_status: Optional[str] = None
    aftercare_template: Optional[str] = None
    sent_by: Optional[str] = None
    aftercare_sent: Optional[bool] = None
    customer_viewed: Optional[bool] = None
    customer_acknowledged: Optional[bool] = None
    followup_24h: Optional[bool] = None
    followup_7d: Optional[bool] = None
    followup_30d: Optional[bool] = None
    aftercare_notes: Optional[str] = None


# Phase 2E: Production Board stage mapping
WRAP_PRODUCTION_TO_PB_STAGE = {
    "not_started": "intake",
    "files_ready": "intake",
    "printing": "production",
    "printed": "production",
    "laminated": "finishing",
    "trimming": "finishing",
    "staged": "finishing",
    "ready_for_install": "ready",
    "complete": "ready",
}


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
        "design": DesignBlock().model_dump(),
        "contract": ContractBlock().model_dump(),
        "approvals": _empty_approvals(),
        "production": _empty_production(),
        "install": _empty_install(),
        "inspection": _empty_inspection(),
        "aftercare": _empty_aftercare(),
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


def _pipeline_state(doc: dict) -> dict:
    """Light derivation of which Phase 1 pipeline chips are 'complete' or 'active'.
    Frontend reads this to color the WrapStatusBar without a full workflow engine.
    """
    out = {}
    areas = doc.get("wrapped_areas") or []
    snapshot = doc.get("pricing_snapshot")
    approvals = doc.get("approvals") or {}
    contract = doc.get("contract") or {}
    design = doc.get("design") or {}
    production = doc.get("production") or {}
    install = doc.get("install") or {}
    inspection = doc.get("inspection") or {}
    aftercare = doc.get("aftercare") or {}

    out["measurements_complete"] = any(a.get("included") for a in areas)
    out["estimate_complete"] = bool(snapshot and snapshot.get("quoted_price"))
    out["quote_sent"] = bool(approvals.get("quote_approved"))  # rough heuristic
    out["contract_sent"] = (contract.get("contract_status") or "") in {"sent", "viewed"}
    out["contract_signed"] = (contract.get("contract_status") or "") in {"signed", "stored"} or bool(approvals.get("contract_signed"))
    out["deposit_paid"] = bool(approvals.get("deposit_paid"))
    out["proof_sent"] = (design.get("proof_status") or "") in {"sent", "revision_requested"}
    out["proof_approved"] = (design.get("proof_status") or "") == "approved" or bool(approvals.get("proof_approved"))
    out["production_complete"] = (production.get("production_status") or "") in {"complete", "ready_for_install"}
    install_status = install.get("install_status") or ""
    out["install_active"] = install_status in {"scheduled", "vehicle_received", "in_progress", "installed", "customer_picked_up"}
    out["install_complete"] = install_status == "complete"
    insp_status = inspection.get("inspection_status") or ""
    out["inspection_active"] = insp_status in {"in_progress", "completed"}
    out["inspection_complete"] = insp_status == "acknowledged" or bool(approvals.get("inspection_acknowledged"))
    after_status = aftercare.get("aftercare_status") or ""
    out["aftercare_active"] = after_status in {"generated", "sent", "viewed", "followup_active"}
    out["aftercare_complete"] = bool(aftercare.get("aftercare_sent")) or bool(approvals.get("aftercare_sent"))
    out["complete"] = bool(approvals.get("final_signoff_completed"))
    out["workflow_complete"] = out["install_complete"] and out["complete"] and out["aftercare_complete"]
    return out


def _serialize(doc: dict) -> dict:
    """Strip Mongo _id, ensure new fields exist on older docs, attach coverage summary + pipeline state."""
    safe = {k: v for k, v in doc.items() if k != "_id"}
    safe.setdefault("materials", [])
    safe.setdefault("pricing", WrapPricingConfig().model_dump())
    safe.setdefault("pricing_snapshot", None)
    safe.setdefault("design", DesignBlock().model_dump())
    safe.setdefault("contract", ContractBlock().model_dump())
    safe.setdefault("approvals", _empty_approvals())
    safe.setdefault("production", _empty_production())
    safe.setdefault("install", _empty_install())
    safe.setdefault("inspection", _empty_inspection())
    safe.setdefault("aftercare", _empty_aftercare())
    for k in APPROVAL_KEYS:
        safe["approvals"].setdefault(k, False)
        safe["approvals"].setdefault(f"{k}_at", None)
    for k in PRODUCTION_CHECKLIST_KEYS:
        safe["production"].setdefault(k, False)
        safe["production"].setdefault(f"{k}_at", None)
    safe["production"].setdefault("tasks", [])
    install_block = safe["install"]
    install_block.setdefault("issues", [])
    install_block.setdefault("checklist", {})
    for k in INSTALL_CHECKLIST_KEYS:
        install_block["checklist"].setdefault(k, False)
    safe["inspection"].setdefault("damage_markers", [])
    safe["inspection"].setdefault("customer_visible", False)
    for k in AFTERCARE_FOLLOWUP_KEYS:
        safe["aftercare"].setdefault(k, False)
        safe["aftercare"].setdefault(f"{k}_at", None)
    safe["coverage_summary"] = _coverage_summary(safe.get("wrapped_areas") or [])
    safe["pipeline_state"] = _pipeline_state(safe)
    return safe


async def _sync_wrap_to_production_board(tenant_id: str, ticket_id: str, ticket: dict, production: dict):
    """Phase 2E quick-win: mirror a single production_tasks doc per wrap ticket
    so the existing Production Board can show wrap items on the right stage.

    Idempotent: uses (tenant_id, job_ticket_id, source='wrap_command_center')
    as the upsert key. Never duplicates and never touches non-wrap PB tasks.
    """
    status = (production or {}).get("production_status") or "not_started"
    stage = WRAP_PRODUCTION_TO_PB_STAGE.get(status, "intake")
    pb_status = "complete" if status == "complete" else (
        "in_progress" if status in {"printing", "printed", "laminated", "trimming", "staged"}
        else "not_started"
    )
    payload = {
        "tenant_id": tenant_id,
        "job_ticket_id": ticket_id,
        "order_id": ticket.get("order_id", ""),
        "source": "wrap_command_center",
        "task_name": ticket.get("item_name") or "Wrap Item",
        "department": "wrap",
        "production_stage": stage,
        "status": pb_status,
        "assigned_to": (production or {}).get("assigned_to") or "",
        "updated_at": _now(),
    }
    try:
        existing = await db.production_tasks.find_one(
            {"tenant_id": tenant_id, "job_ticket_id": ticket_id, "source": "wrap_command_center"},
            {"_id": 0, "id": 1, "created_at": 1},
        )
        if existing:
            await db.production_tasks.update_one(
                {"tenant_id": tenant_id, "job_ticket_id": ticket_id, "source": "wrap_command_center"},
                {"$set": payload},
            )
        else:
            payload["id"] = str(uuid.uuid4())
            payload["created_at"] = _now()
            payload["stage_sequence"] = 0
            await db.production_tasks.insert_one(payload.copy())
    except Exception as e:  # noqa: BLE001
        logger.warning("Wrap→PB sync failed for ticket %s: %s", ticket_id, e)



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


# ────────── Phase 2C: Design ──────────
async def _refresh_doc(tenant_id: str, ticket_id: str):
    return await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )


async def _set_approval(tenant_id: str, ticket_id: str, key: str, value: bool):
    """Helper to flip a single approval flag with automatic timestamp handling."""
    if key not in APPROVAL_KEYS:
        return
    ts_key = f"{key}_at"
    updates = {f"approvals.{key}": bool(value)}
    if value:
        doc = await db.wrap_data.find_one(
            {"tenant_id": tenant_id, "ticket_id": ticket_id},
            {"_id": 0, "approvals": 1},
        )
        existing_ts = ((doc or {}).get("approvals") or {}).get(ts_key)
        if not existing_ts:
            updates[f"approvals.{ts_key}"] = _now()
    else:
        updates[f"approvals.{ts_key}"] = None
    updates["updated_at"] = _now()
    await db.wrap_data.update_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id},
        {"$set": updates},
    )


@router.put("/items/{ticket_id}/design")
async def update_design(
    ticket_id: str,
    payload: DesignUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        set_doc = {f"design.{k}": v for k, v in updates.items()}
        set_doc["updated_at"] = _now()
        await db.wrap_data.update_one(
            {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
            {"$set": set_doc},
        )
        if updates.get("proof_status") == "approved":
            await _set_approval(current_user.tenant_id, ticket_id, "proof_approved", True)
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.post("/items/{ticket_id}/design/send-questionnaire")
async def send_design_questionnaire(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {
            "design.questionnaire_status": "sent",
            "design.questionnaire_sent_at": _now(),
            "updated_at": _now(),
        }},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.post("/items/{ticket_id}/design/proofs")
async def add_proof_version(
    ticket_id: str,
    payload: ProofVersionCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    proof = {
        "id": str(uuid.uuid4()),
        "label": payload.label or "Untitled Proof",
        "notes": payload.notes or "",
        "status": "draft",
        "created_at": _now(),
        "approved_at": None,
    }
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$push": {"design.proof_versions": proof}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.put("/items/{ticket_id}/design/proofs/{proof_id}")
async def update_proof_version(
    ticket_id: str,
    proof_id: str,
    payload: ProofVersionUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    if not doc:
        await _get_or_create_doc(current_user.tenant_id, ticket)
        doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    proofs = (doc.get("design") or {}).get("proof_versions") or []
    updates = payload.model_dump(exclude_unset=True)
    found = None
    for p in proofs:
        if p.get("id") == proof_id:
            p.update(updates)
            if updates.get("status") == "approved" and not p.get("approved_at"):
                p["approved_at"] = _now()
            found = p
            break
    if not found:
        raise HTTPException(status_code=404, detail="Proof not found")
    design_updates = {"design.proof_versions": proofs, "updated_at": _now()}
    if updates.get("status") == "approved":
        design_updates["design.proof_status"] = "approved"
        design_updates["design.approved_proof_id"] = proof_id
    elif updates.get("status") in {"sent", "draft", "revision_requested"}:
        design_updates["design.proof_status"] = updates["status"]
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": design_updates},
    )
    if updates.get("status") == "approved":
        await _set_approval(current_user.tenant_id, ticket_id, "proof_approved", True)
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.delete("/items/{ticket_id}/design/proofs/{proof_id}")
async def delete_proof_version(
    ticket_id: str,
    proof_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$pull": {"design.proof_versions": {"id": proof_id}}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


# ────────── Phase 2C: Contract ──────────
DEFAULT_TERMS_SUMMARY = (
    "1. Customer approves design proof prior to production.\n"
    "2. 50% deposit due before production begins; remaining balance due before final pickup/install.\n"
    "3. Customer is responsible for ensuring vehicle is clean, dry, and indoors at install time.\n"
    "4. Workmanship warranty as described in the customer-facing wrap care guide.\n"
    "5. Any change to scope requires written approval and may revise the price."
)


@router.put("/items/{ticket_id}/contract")
async def update_contract(
    ticket_id: str,
    payload: ContractUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    updates = payload.model_dump(exclude_unset=True)
    if updates:
        set_doc = {f"contract.{k}": v for k, v in updates.items()}
        set_doc["updated_at"] = _now()
        await db.wrap_data.update_one(
            {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
            {"$set": set_doc},
        )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.post("/items/{ticket_id}/contract/action")
async def contract_action(
    ticket_id: str,
    payload: ContractAction,
    current_user: UserInDB = Depends(get_current_active_user),
):
    if payload.action not in CONTRACT_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Invalid action. Allowed: {sorted(CONTRACT_ACTIONS)}")
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    contract = (doc or {}).get("contract") or {}

    updates: dict = {"updated_at": _now()}
    action = payload.action
    if action == "generate_draft":
        updates["contract.contract_status"] = "draft"
        if not contract.get("terms_summary"):
            updates["contract.terms_summary"] = DEFAULT_TERMS_SUMMARY
    elif action == "send":
        updates["contract.contract_status"] = "sent"
        updates["contract.contract_sent_at"] = contract.get("contract_sent_at") or _now()
    elif action == "mark_viewed":
        updates["contract.contract_status"] = "viewed"
        updates["contract.contract_viewed_at"] = contract.get("contract_viewed_at") or _now()
    elif action == "mark_signed":
        updates["contract.contract_status"] = "signed"
        updates["contract.contract_signed_at"] = contract.get("contract_signed_at") or _now()
        updates["contract.accepted_terms"] = True
        if payload.signed_by is not None:
            updates["contract.signed_by"] = payload.signed_by
    elif action == "store_signed":
        updates["contract.contract_status"] = "stored"
        if payload.signed_contract_url is not None:
            updates["contract.signed_contract_url"] = payload.signed_contract_url

    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": updates},
    )
    if action == "mark_signed":
        await _set_approval(current_user.tenant_id, ticket_id, "contract_signed", True)
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


# ────────── Phase 2C: Approvals ──────────
@router.put("/items/{ticket_id}/approvals")
async def update_approvals(
    ticket_id: str,
    payload: ApprovalsUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is None:
            continue
        await _set_approval(current_user.tenant_id, ticket_id, key, bool(value))
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


# ────────── Phase 2C: Updated quote draft ──────────
def _money(n) -> str:
    try:
        return f"${float(n):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


@router.post("/items/{ticket_id}/draft-updated-quote-message")
async def draft_updated_quote_message(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    if not doc:
        await _get_or_create_doc(current_user.tenant_id, ticket)
        doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    vehicle = doc.get("vehicle_info") or {}
    pricing_snapshot = doc.get("pricing_snapshot") or {}
    quote_amount = float(pricing_snapshot.get("quoted_price") or ticket.get("estimated_price") or 0.0)
    deposit_amount = round(quote_amount / 2.0, 2) if quote_amount else 0.0
    balance_amount = round(quote_amount - deposit_amount, 2) if quote_amount else 0.0

    order = await db.orders.find_one(
        {"id": ticket.get("order_id"), "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    customer = None
    if order and order.get("customer_id"):
        customer = await db.customers.find_one(
            {"id": order["customer_id"], "tenant_id": current_user.tenant_id}, {"_id": 0}
        )

    customer_name = (customer or {}).get("name") or (order or {}).get("customer_name") or "there"
    first_name = customer_name.split(" ")[0] if customer_name else "there"
    customer_email = (customer or {}).get("email") or (order or {}).get("email") or ""
    order_number = (order or {}).get("order_number") or ""

    vehicle_line = " ".join([v for v in [vehicle.get("year"), vehicle.get("make"), vehicle.get("model")] if v]).strip()
    wrap_type = (ticket.get("item_category") or "").replace("_", " ").title() or "wrap"

    subject = f"Updated Wrap Quote for Order #{order_number}" if order_number else "Updated Wrap Quote"

    body_lines = [
        f"Hi {first_name},",
        "",
        "We updated the wrap quote for your "
        + (vehicle_line + " " if vehicle_line else "")
        + "based on the confirmed measurements, coverage areas, and material selections.",
        "",
        f"Updated wrap quote: {_money(quote_amount)}",
    ]
    if quote_amount:
        body_lines.append(f"Required deposit: {_money(deposit_amount)}")
        body_lines.append(f"Estimated balance due: {_money(balance_amount)}")
    body_lines += [
        "",
        "Once approved, we can move forward with the design/proof stage.",
        "",
        "Payment link:",
        "Payment link will be connected in a later phase.",
        "",
        "Thank you,",
        "The SignGuy Team",
    ]
    body = "\n".join(body_lines)

    return {
        "to": customer_email,
        "subject": subject,
        "body": body,
        "quote_amount": round(quote_amount, 2),
        "deposit_amount": deposit_amount,
        "balance_amount": balance_amount,
        "order_number": order_number,
        "vehicle_summary": vehicle_line,
        "wrap_type": wrap_type,
        "customer_name": customer_name,
    }



# ────────── Phase 2D: Production ──────────
@router.put("/items/{ticket_id}/production")
async def update_production(
    ticket_id: str,
    payload: ProductionUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("production_status") and updates["production_status"] not in PRODUCTION_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid production_status. Allowed: {sorted(PRODUCTION_STATUSES)}")

    # Load current state for timestamp idempotency on checklist flips
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    current_prod = (doc or {}).get("production") or {}
    set_doc: dict = {"updated_at": _now()}
    for k, v in updates.items():
        if k in PRODUCTION_CHECKLIST_KEYS:
            set_doc[f"production.{k}"] = bool(v)
            ts_key = f"production.{k}_at"
            if v:
                existing_ts = current_prod.get(f"{k}_at")
                if not existing_ts:
                    set_doc[ts_key] = _now()
            else:
                set_doc[ts_key] = None
        else:
            set_doc[f"production.{k}"] = v
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": set_doc},
    )
    # Phase 2E quick-win: mirror to existing Production Board
    refreshed_for_pb = await _refresh_doc(current_user.tenant_id, ticket_id)
    await _sync_wrap_to_production_board(
        current_user.tenant_id, ticket_id, ticket, (refreshed_for_pb or {}).get("production") or {}
    )
    return _serialize(refreshed_for_pb)


@router.post("/items/{ticket_id}/production/tasks")
async def add_production_task(
    ticket_id: str,
    payload: ProductionTaskCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    if payload.status and payload.status not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(TASK_STATUSES)}")
    task = ProductionTask(**payload.model_dump()).model_dump()
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$push": {"production.tasks": task}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.post("/items/{ticket_id}/production/tasks/load-defaults")
async def load_default_production_tasks(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Append the 10 default wrap production tasks only when the task list is empty.
    Safe to click multiple times — never duplicates."""
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    if (doc.get("production") or {}).get("tasks"):
        # Idempotent — do not duplicate
        return _serialize(doc)
    tasks = [ProductionTask(task_name=name).model_dump() for name in DEFAULT_WRAP_TASKS]
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"production.tasks": tasks, "updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.put("/items/{ticket_id}/production/tasks/{task_id}")
async def update_production_task(
    ticket_id: str,
    task_id: str,
    payload: ProductionTaskUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    if not doc:
        await _get_or_create_doc(current_user.tenant_id, ticket)
        doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    tasks = ((doc.get("production") or {}).get("tasks")) or []
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("status") and updates["status"] not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {sorted(TASK_STATUSES)}")
    found = False
    for t in tasks:
        if t.get("id") == task_id:
            t.update(updates)
            if updates.get("status") == "complete" and not t.get("completed_at"):
                t["completed_at"] = _now()
            elif updates.get("status") and updates["status"] != "complete":
                t["completed_at"] = None
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"production.tasks": tasks, "updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.delete("/items/{ticket_id}/production/tasks/{task_id}")
async def delete_production_task(
    ticket_id: str,
    task_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$pull": {"production.tasks": {"id": task_id}}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


# ────────── Phase 2D: Install ──────────
@router.put("/items/{ticket_id}/install")
async def update_install(
    ticket_id: str,
    payload: InstallUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("install_status") and updates["install_status"] not in INSTALL_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid install_status. Allowed: {sorted(INSTALL_STATUSES)}")
    if "checklist" in updates and updates["checklist"] is not None:
        bad = [k for k in updates["checklist"].keys() if k not in INSTALL_CHECKLIST_KEYS]
        if bad:
            raise HTTPException(status_code=400, detail=f"Unknown checklist keys: {bad}")

    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    current_install = (doc or {}).get("install") or {}
    set_doc: dict = {"updated_at": _now()}
    # customer_signoff timestamp idempotency
    if "customer_signoff" in updates:
        v = bool(updates["customer_signoff"])
        set_doc["install.customer_signoff"] = v
        if v and not current_install.get("customer_signoff_at"):
            set_doc["install.customer_signoff_at"] = _now()
        elif not v:
            set_doc["install.customer_signoff_at"] = None
        del updates["customer_signoff"]
    # Checklist partial merge
    if "checklist" in updates:
        cl = current_install.get("checklist") or {}
        for k, v in (updates["checklist"] or {}).items():
            cl[k] = bool(v)
        set_doc["install.checklist"] = cl
        del updates["checklist"]
    for k, v in updates.items():
        set_doc[f"install.{k}"] = v

    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": set_doc},
    )

    # Mirror into approvals.final_signoff_completed when install completes
    refreshed = await _refresh_doc(current_user.tenant_id, ticket_id)
    install_block = (refreshed or {}).get("install") or {}
    if install_block.get("customer_signoff") and install_block.get("install_status") == "complete":
        await _set_approval(current_user.tenant_id, ticket_id, "final_signoff_completed", True)
        refreshed = await _refresh_doc(current_user.tenant_id, ticket_id)
    return _serialize(refreshed)


@router.post("/items/{ticket_id}/install/issues")
async def add_install_issue(
    ticket_id: str,
    payload: InstallIssueCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    if payload.issue_type and payload.issue_type not in ISSUE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid issue_type. Allowed: {sorted(ISSUE_TYPES)}")
    issue = InstallIssue(**payload.model_dump()).model_dump()
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$push": {"install.issues": issue}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.put("/items/{ticket_id}/install/issues/{issue_id}")
async def update_install_issue(
    ticket_id: str,
    issue_id: str,
    payload: InstallIssueUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    if not doc:
        await _get_or_create_doc(current_user.tenant_id, ticket)
        doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    issues = ((doc.get("install") or {}).get("issues")) or []
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("issue_type") and updates["issue_type"] not in ISSUE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid issue_type. Allowed: {sorted(ISSUE_TYPES)}")
    found = False
    for i in issues:
        if i.get("id") == issue_id:
            i.update(updates)
            if "resolved" in updates:
                if updates["resolved"] and not i.get("resolved_at"):
                    i["resolved_at"] = _now()
                elif not updates["resolved"]:
                    i["resolved_at"] = None
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Issue not found")
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"install.issues": issues, "updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.delete("/items/{ticket_id}/install/issues/{issue_id}")
async def delete_install_issue(
    ticket_id: str,
    issue_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$pull": {"install.issues": {"id": issue_id}}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))



# ────────── Phase 2E: Inspection ──────────
@router.put("/items/{ticket_id}/inspection")
async def update_inspection(
    ticket_id: str,
    payload: InspectionUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("inspection_status") and updates["inspection_status"] not in INSPECTION_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid inspection_status. Allowed: {sorted(INSPECTION_STATUSES)}")

    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    current = (doc or {}).get("inspection") or {}
    set_doc: dict = {"updated_at": _now()}
    customer_ack_change = None  # True/False/None
    if "customer_acknowledged" in updates:
        v = bool(updates["customer_acknowledged"])
        set_doc["inspection.customer_acknowledged"] = v
        if v:
            if not current.get("customer_acknowledged_at"):
                set_doc["inspection.customer_acknowledged_at"] = _now()
            set_doc["inspection.inspection_status"] = "acknowledged"
        else:
            set_doc["inspection.customer_acknowledged_at"] = None
        customer_ack_change = v
        del updates["customer_acknowledged"]
    for k, v in updates.items():
        set_doc[f"inspection.{k}"] = v
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": set_doc},
    )
    # Mirror approvals.inspection_acknowledged
    if customer_ack_change is True:
        await _set_approval(current_user.tenant_id, ticket_id, "inspection_acknowledged", True)
    elif customer_ack_change is False:
        await _set_approval(current_user.tenant_id, ticket_id, "inspection_acknowledged", False)
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.post("/items/{ticket_id}/inspection/damage-markers")
async def add_damage_marker(
    ticket_id: str,
    payload: DamageMarkerCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    if payload.damage_type and payload.damage_type not in DAMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid damage_type. Allowed: {sorted(DAMAGE_TYPES)}")
    if payload.severity and payload.severity not in SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Allowed: {sorted(SEVERITIES)}")
    marker = DamageMarker(
        **payload.model_dump(),
        created_by=current_user.email if hasattr(current_user, "email") else "",
    ).model_dump()
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$push": {"inspection.damage_markers": marker}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.put("/items/{ticket_id}/inspection/damage-markers/{marker_id}")
async def update_damage_marker(
    ticket_id: str,
    marker_id: str,
    payload: DamageMarkerUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    if not doc:
        await _get_or_create_doc(current_user.tenant_id, ticket)
        doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    markers = ((doc.get("inspection") or {}).get("damage_markers")) or []
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("damage_type") and updates["damage_type"] not in DAMAGE_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid damage_type. Allowed: {sorted(DAMAGE_TYPES)}")
    if updates.get("severity") and updates["severity"] not in SEVERITIES:
        raise HTTPException(status_code=400, detail=f"Invalid severity. Allowed: {sorted(SEVERITIES)}")
    found = False
    for m in markers:
        if m.get("id") == marker_id:
            m.update(updates)
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Damage marker not found")
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"inspection.damage_markers": markers, "updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


@router.delete("/items/{ticket_id}/inspection/damage-markers/{marker_id}")
async def delete_damage_marker(
    ticket_id: str,
    marker_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$pull": {"inspection.damage_markers": {"id": marker_id}}, "$set": {"updated_at": _now()}},
    )
    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))


# ────────── Phase 2E: Aftercare ──────────
@router.put("/items/{ticket_id}/aftercare")
async def update_aftercare(
    ticket_id: str,
    payload: AftercareUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("aftercare_status") and updates["aftercare_status"] not in AFTERCARE_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid aftercare_status. Allowed: {sorted(AFTERCARE_STATUSES)}")

    doc = await _refresh_doc(current_user.tenant_id, ticket_id)
    current = (doc or {}).get("aftercare") or {}
    set_doc: dict = {"updated_at": _now()}
    aftercare_sent_change = None

    # aftercare_sent — special handling
    if "aftercare_sent" in updates:
        v = bool(updates["aftercare_sent"])
        set_doc["aftercare.aftercare_sent"] = v
        if v:
            if not current.get("aftercare_sent_at"):
                set_doc["aftercare.aftercare_sent_at"] = _now()
            if (current.get("aftercare_status") or "not_sent") in {"not_sent", "generated"}:
                set_doc["aftercare.aftercare_status"] = "sent"
        else:
            set_doc["aftercare.aftercare_sent_at"] = None
        aftercare_sent_change = v
        del updates["aftercare_sent"]

    # customer_viewed
    if "customer_viewed" in updates:
        v = bool(updates["customer_viewed"])
        set_doc["aftercare.customer_viewed"] = v
        if v:
            if not current.get("customer_viewed_at"):
                set_doc["aftercare.customer_viewed_at"] = _now()
            if (current.get("aftercare_status") or "") in {"sent", "not_sent", "generated"}:
                set_doc["aftercare.aftercare_status"] = "viewed"
        else:
            set_doc["aftercare.customer_viewed_at"] = None
        del updates["customer_viewed"]

    # customer_acknowledged
    if "customer_acknowledged" in updates:
        v = bool(updates["customer_acknowledged"])
        set_doc["aftercare.customer_acknowledged"] = v
        if v:
            if not current.get("customer_acknowledged_at"):
                set_doc["aftercare.customer_acknowledged_at"] = _now()
            if (current.get("aftercare_status") or "") not in {"complete", "followup_active"}:
                set_doc["aftercare.aftercare_status"] = "acknowledged"
        else:
            set_doc["aftercare.customer_acknowledged_at"] = None
        del updates["customer_acknowledged"]

    # follow-up toggles
    for fk in AFTERCARE_FOLLOWUP_KEYS:
        if fk in updates:
            v = bool(updates[fk])
            set_doc[f"aftercare.{fk}"] = v
            if v:
                if not current.get(f"{fk}_at"):
                    set_doc[f"aftercare.{fk}_at"] = _now()
            else:
                set_doc[f"aftercare.{fk}_at"] = None
            del updates[fk]

    # remaining plain fields
    for k, v in updates.items():
        set_doc[f"aftercare.{k}"] = v

    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": set_doc},
    )

    # Mirror approvals.aftercare_sent
    if aftercare_sent_change is True:
        await _set_approval(current_user.tenant_id, ticket_id, "aftercare_sent", True)
    elif aftercare_sent_change is False:
        await _set_approval(current_user.tenant_id, ticket_id, "aftercare_sent", False)

    return _serialize(await _refresh_doc(current_user.tenant_id, ticket_id))

