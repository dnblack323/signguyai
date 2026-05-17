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
    """Strip Mongo _id and attach coverage summary."""
    safe = {k: v for k, v in doc.items() if k != "_id"}
    safe["coverage_summary"] = _coverage_summary(safe.get("wrapped_areas") or [])
    return safe


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
    await db.wrap_data.update_one(
        {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id},
        {"$set": {"vehicle_info": payload.model_dump(), "updated_at": _now()}},
    )
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
