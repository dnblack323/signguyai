"""
Job Tickets API Routes

CRUD for Job Ticket records (Layer 2) — the operational source of truth.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone

from server import db, get_current_active_user
from models import UserInDB
from models.orders import (
    JobTicket, JobTicketCreate, JobTicketUpdate, JobTicketStatus, JobTicketSpecs
)
from services.workflow_engine import (
    generate_production_tasks, seed_default_templates,
    update_ticket_progress, update_order_progress, log_activity
)

router = APIRouter(prefix="/job-tickets", tags=["Job Tickets"])



@router.get("/schema/{category}")
async def get_category_field_schema(category: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Return dynamic field schema for a job ticket category.
    Options are derived from existing enums and pricing settings — not hardcoded here."""
    from server import get_pricing_defaults
    from models.enums import (
        VinylType, PrintMaterial, SubstrateType, ApparelType, TransferType,
        VehicleType, CoverageType, PromoProductType
    )

    defaults = await get_pricing_defaults(current_user.tenant_id)
    cat_config = defaults.get("category_defaults", {}).get(category, {})

    def enum_opts(e):
        return [{"value": m.value, "label": m.value.replace("_", " ").title()} for m in e]

    # Base fields every category gets
    base = [
        {"key": "width", "label": "Width", "type": "text", "placeholder": "e.g. 8ft or 96in", "group": "dimensions"},
        {"key": "height", "label": "Height", "type": "text", "placeholder": "e.g. 3ft or 36in", "group": "dimensions"},
    ]

    schemas = {
        "banners": base + [
            {"key": "material", "label": "Banner Material", "type": "select", "options": enum_opts(PrintMaterial), "group": "material"},
            {"key": "lamination", "label": "Lamination", "type": "text", "placeholder": "Gloss, Matte, None", "group": "finishing"},
            {"key": "hemming", "label": "Hemming", "type": "toggle", "default": True, "group": "finishing"},
            {"key": "grommets", "label": "Grommets", "type": "toggle", "default": True, "group": "finishing"},
            {"key": "double_sided", "label": "Double Sided", "type": "toggle", "group": "specs"},
            {"key": "finish", "label": "Finish", "type": "text", "placeholder": "Gloss, Matte, Satin", "group": "finishing"},
            {"key": "print_method", "label": "Print Method", "type": "text", "placeholder": "Solvent, Latex, UV", "group": "production"},
        ],
        "rigid_signs": base + [
            {"key": "substrate", "label": "Board Material", "type": "select", "options": enum_opts(SubstrateType), "group": "material"},
            {"key": "material", "label": "Print Material", "type": "text", "placeholder": "Vinyl, Direct Print", "group": "material"},
            {"key": "double_sided", "label": "Double Sided", "type": "toggle", "group": "specs"},
            {"key": "lamination", "label": "Lamination", "type": "text", "placeholder": "Gloss, Matte, None", "group": "finishing"},
            {"key": "mounting_type", "label": "Mounting / Hardware", "type": "text", "placeholder": "Stakes, Standoffs, Channel", "group": "finishing"},
            {"key": "cut_method", "label": "Cut Shape", "type": "text", "placeholder": "Square, Contour, Custom", "group": "production"},
            {"key": "install_required", "label": "Install Required", "type": "toggle", "group": "specs"},
        ],
        "cut_vinyl": base + [
            {"key": "material", "label": "Vinyl Type", "type": "select", "options": enum_opts(VinylType), "group": "material"},
            {"key": "color_specs", "label": "Vinyl Colors", "type": "text", "placeholder": "Red, White, Blue", "group": "specs"},
            {"key": "lamination", "label": "Lamination", "type": "text", "placeholder": "Gloss, Matte, None", "group": "finishing"},
            {"key": "cut_method", "label": "Cut Method", "type": "text", "placeholder": "Plotter, Flatbed", "group": "production"},
            {"key": "install_required", "label": "Install Required", "type": "toggle", "group": "specs"},
        ],
        "vehicle_wrap": base + [
            {"key": "material", "label": "Wrap Material", "type": "select", "options": enum_opts(VinylType), "group": "material"},
            {"key": "color_specs", "label": "Color / Design Notes", "type": "text", "group": "specs"},
            {"key": "lamination", "label": "Lamination", "type": "text", "placeholder": "Gloss, Matte, Satin", "group": "finishing"},
            {"key": "double_sided", "label": "Multi-Panel", "type": "toggle", "group": "specs"},
            {"key": "install_required", "label": "Install Required", "type": "toggle", "default": True, "group": "specs"},
            {"key": "print_method", "label": "Print Method", "type": "text", "placeholder": "Solvent, Latex, UV", "group": "production"},
            {"key": "mounting_type", "label": "Coverage Type", "type": "select", "options": enum_opts(CoverageType), "group": "specs"},
        ],
        "apparel": [
            {"key": "material", "label": "Garment Type", "type": "select", "options": enum_opts(ApparelType), "group": "material"},
            {"key": "substrate", "label": "Brand / Style", "type": "text", "placeholder": "Gildan 5000, Bella+Canvas 3001", "group": "material"},
            {"key": "color_specs", "label": "Garment Color", "type": "text", "placeholder": "Black, White, Navy", "group": "specs"},
            {"key": "size_description", "label": "Size Breakdown", "type": "text", "placeholder": "S(2) M(5) L(8) XL(5) 2XL(4)", "group": "specs"},
            {"key": "print_method", "label": "Decoration Method", "type": "select", "options": enum_opts(TransferType), "group": "production"},
            {"key": "finish", "label": "Print Locations", "type": "text", "placeholder": "Front, Back, Left Sleeve", "group": "production"},
            {"key": "width", "label": "Art Width", "type": "text", "placeholder": "12in", "group": "dimensions"},
            {"key": "height", "label": "Art Height", "type": "text", "placeholder": "14in", "group": "dimensions"},
        ],
        "promo_misc": [
            {"key": "material", "label": "Product Type", "type": "select", "options": enum_opts(PromoProductType), "group": "material"},
            {"key": "size_description", "label": "Size / Specs", "type": "text", "group": "specs"},
            {"key": "color_specs", "label": "Colors", "type": "text", "group": "specs"},
            {"key": "finish", "label": "Decoration Method", "type": "text", "placeholder": "Printed, Engraved, Embossed", "group": "finishing"},
            {"key": "width", "label": "Width", "type": "text", "group": "dimensions"},
            {"key": "height", "label": "Height", "type": "text", "group": "dimensions"},
        ],
        "custom": base + [
            {"key": "material", "label": "Material", "type": "text", "group": "material"},
            {"key": "substrate", "label": "Substrate", "type": "text", "group": "material"},
            {"key": "color_specs", "label": "Colors", "type": "text", "group": "specs"},
            {"key": "finish", "label": "Finish", "type": "text", "group": "finishing"},
            {"key": "lamination", "label": "Lamination", "type": "text", "group": "finishing"},
            {"key": "print_method", "label": "Print Method", "type": "text", "group": "production"},
            {"key": "cut_method", "label": "Cut Method", "type": "text", "group": "production"},
            {"key": "mounting_type", "label": "Mounting", "type": "text", "group": "finishing"},
            {"key": "install_required", "label": "Install Required", "type": "toggle", "group": "specs"},
            {"key": "double_sided", "label": "Double Sided", "type": "toggle", "group": "specs"},
        ],
    }

    fields = schemas.get(category, schemas["custom"])

    return {
        "category": category,
        "fields": fields,
        "pricing_config": {
            "minimum_charge": cat_config.get("minimum_charge", defaults.get("minimum_order", 0)),
            "default_markup": cat_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
            "target_margin": cat_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40)),
            "labor_rate": defaults.get("production_hourly_rate", 28),
            "design_rate": defaults.get("design_hourly_rate", 85),
        },
    }



async def _next_ticket_number(order_id: str, tenant_id: str) -> str:
    order = await db.orders.find_one({"id": order_id}, {"_id": 0, "order_number": 1})
    prefix = order.get("order_number", "ORD") if order else "ORD"
    count = await db.job_tickets.count_documents({"order_id": order_id, "tenant_id": tenant_id})
    return f"{prefix}-T{count + 1}"


@router.get("")
async def list_job_tickets(
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    assigned_user_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: UserInDB = Depends(get_current_active_user),
):
    query = {"tenant_id": current_user.tenant_id}
    if order_id:
        query["order_id"] = order_id
    if status:
        query["status"] = status
    if category:
        query["item_category"] = category
    if department:
        query["department_route"] = department
    if assigned_user_id:
        query["assigned_user_id"] = assigned_user_id

    tickets = await db.job_tickets.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.job_tickets.count_documents(query)
    return {"tickets": tickets, "total": total}


@router.get("/{ticket_id}")
async def get_job_ticket(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    ticket = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    # Include production tasks if workflow enabled
    if ticket.get("production_flow_enabled"):
        tasks = await db.production_tasks.find(
            {"job_ticket_id": ticket_id}, {"_id": 0}
        ).sort("stage_sequence", 1).to_list(50)
        ticket["production_tasks"] = tasks

    return ticket


@router.post("")
async def create_job_ticket(data: JobTicketCreate, current_user: UserInDB = Depends(get_current_active_user)):
    # Verify order exists
    order = await db.orders.find_one(
        {"id": data.order_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    specs = JobTicketSpecs(**(data.specs or {}))
    ticket = JobTicket(
        tenant_id=current_user.tenant_id,
        order_id=data.order_id,
        item_name=data.item_name,
        item_category=data.item_category,
        item_subcategory=data.item_subcategory,
        quantity=data.quantity,
        unit_type=data.unit_type,
        due_date=data.due_date,
        priority=data.priority,
        department_route=data.department_route,
        assigned_user_id=data.assigned_user_id,
        production_flow_enabled=data.production_flow_enabled,
        specs=specs,
        design_needed=data.design_needed,
        customer_artwork=data.customer_artwork,
        proof_required=data.proof_required,
        special_instructions=data.special_instructions,
        production_notes=data.production_notes,
        install_notes=data.install_notes,
        packaging_notes=data.packaging_notes,
        estimated_price=data.estimated_price,
        labor_estimate=data.labor_estimate,
        material_estimate=data.material_estimate,
    )
    ticket.ticket_number = await _next_ticket_number(data.order_id, current_user.tenant_id)

    doc = ticket.model_dump()
    await db.job_tickets.insert_one(doc)

    # If production workflow enabled, auto-generate tasks
    tasks_created = 0
    if data.production_flow_enabled:
        await seed_default_templates(db, current_user.tenant_id)
        tasks = await generate_production_tasks(db, doc, current_user.tenant_id)
        tasks_created = len(tasks)

    # Update order counts
    await update_order_progress(db, data.order_id)

    await log_activity(db, data.order_id, current_user.tenant_id, "job_ticket", ticket.id,
                       "created", f"Job ticket '{data.item_name}' ({data.item_category}) created" +
                       (f" with {tasks_created} production tasks" if tasks_created else ""),
                       user_id=current_user.id, user_name=current_user.full_name or "")

    doc.pop("_id", None)
    return doc


@router.put("/{ticket_id}")
async def update_job_ticket(ticket_id: str, data: JobTicketUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if k == "specs":
                # Merge specs
                current_specs = existing.get("specs", {})
                current_specs.update(v)
                update_data["specs"] = current_specs
            else:
                update_data[k] = v

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Log status changes
    if "status" in update_data and update_data["status"] != existing.get("status"):
        await log_activity(db, existing["order_id"], current_user.tenant_id, "job_ticket", ticket_id,
                           "status_change", f"Ticket status: {existing.get('status')} → {update_data['status']}",
                           user_id=current_user.id, user_name=current_user.full_name or "",
                           old_value=existing.get("status"), new_value=update_data["status"])

    # Handle production flow toggle
    if "production_flow_enabled" in update_data and update_data["production_flow_enabled"] and not existing.get("production_flow_enabled"):
        existing_tasks = await db.production_tasks.count_documents({"job_ticket_id": ticket_id})
        if existing_tasks == 0:
            await seed_default_templates(db, current_user.tenant_id)
            merged = {**existing, **update_data}
            await generate_production_tasks(db, merged, current_user.tenant_id)

    await db.job_tickets.update_one({"id": ticket_id}, {"$set": update_data})

    # Update rollups
    await update_order_progress(db, existing["order_id"])

    updated = await db.job_tickets.find_one({"id": ticket_id}, {"_id": 0})
    return updated


@router.delete("/{ticket_id}")
async def delete_job_ticket(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    existing = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "order_id": 1}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    await db.job_tickets.delete_one({"id": ticket_id})
    await db.production_tasks.delete_many({"job_ticket_id": ticket_id})
    await update_order_progress(db, existing["order_id"])
    return {"message": "Job ticket and tasks deleted"}


@router.post("/{ticket_id}/duplicate")
async def duplicate_job_ticket(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Duplicate a job ticket within the same order."""
    import uuid as uuid_mod
    existing = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    new_id = str(uuid_mod.uuid4())
    new_number = await _next_ticket_number(existing["order_id"], current_user.tenant_id)

    dup = {**existing}
    dup["id"] = new_id
    dup["ticket_number"] = new_number
    dup["status"] = "new"
    dup["progress"] = 0.0
    dup["started_date"] = None
    dup["finished_date"] = None
    dup["ready_for_qc"] = False
    dup["ready_for_pickup"] = False
    dup["rework_needed"] = False
    dup["rework_notes"] = ""
    dup["pricing_snapshot"] = None
    dup["created_at"] = datetime.now(timezone.utc).isoformat()
    dup["updated_at"] = datetime.now(timezone.utc).isoformat()
    dup.pop("_id", None)
    dup.pop("production_tasks", None)

    await db.job_tickets.insert_one(dup)

    # Generate tasks if workflow enabled
    if dup.get("production_flow_enabled"):
        await seed_default_templates(db, current_user.tenant_id)
        from services.workflow_engine import generate_production_tasks
        await generate_production_tasks(db, dup, current_user.tenant_id)

    await update_order_progress(db, existing["order_id"])
    await log_activity(db, existing["order_id"], current_user.tenant_id, "job_ticket", new_id,
                       "duplicated", f"Duplicated from {existing.get('ticket_number', '')} → {new_number}",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    dup.pop("_id", None)
    return dup



@router.post("/{ticket_id}/calculate-pricing")
async def calculate_ticket_pricing(ticket_id: str, pricing_input: dict = {}, current_user: UserInDB = Depends(get_current_active_user)):
    """Calculate pricing for a job ticket using the existing pricing engine.
    Reads pricing settings from tenant config. Can be called with partial input for live updates."""
    from server import calculate_pricing, get_pricing_defaults
    from models.enums import PricingCategory
    from models.pricing import JobItemPricingData

    ticket = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    # Map job ticket category to pricing category
    CATEGORY_MAP = {
        "banners": "digital_print",
        "rigid_signs": "rigid_signs",
        "cut_vinyl": "cut_vinyl",
        "vehicle_wrap": "vehicle_graphics",
        "apparel": "apparel",
        "promo_misc": "promotional",
        "custom": "custom",
    }
    pricing_cat = CATEGORY_MAP.get(ticket.get("item_category"), "custom")

    # Build pricing data from ticket specs + explicit overrides
    specs = ticket.get("specs", {})
    merged_input = {
        "category": pricing_cat,
        "complexity": pricing_input.get("complexity", 1),
        "width_inches": _parse_dimension(specs.get("width") or pricing_input.get("width_inches")),
        "length_inches": _parse_dimension(specs.get("height") or pricing_input.get("length_inches")),
        "double_sided": specs.get("double_sided", False),
        "laminate": bool(specs.get("lamination")),
        "include_setup_fee": pricing_input.get("include_setup_fee", False),
        **{k: v for k, v in pricing_input.items() if v is not None and k not in ("complexity",)},
    }

    try:
        category_enum = PricingCategory(pricing_cat)
        pricing_data = JobItemPricingData(**merged_input)
        quantity = ticket.get("quantity", 1)

        result = await calculate_pricing(category_enum, pricing_data, quantity, current_user.tenant_id)
        return {
            "calculation": result.model_dump(),
            "pricing_category": pricing_cat,
            "quantity": quantity,
            "active_price": result.selling_price,
        }
    except Exception as e:
        return {"calculation": None, "error": str(e), "pricing_category": pricing_cat}


@router.post("/{ticket_id}/save-pricing")
async def save_ticket_pricing(ticket_id: str, body: dict, current_user: UserInDB = Depends(get_current_active_user)):
    """Save pricing snapshot to a job ticket. Supports calculator and manual modes."""
    ticket = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Job ticket not found")

    pricing_mode = body.get("pricing_mode", "calculator")  # "calculator" or "manual"
    calculated_price = body.get("calculated_price", 0)
    manual_price = body.get("manual_price", 0)
    calculation_breakdown = body.get("calculation_breakdown", {})

    active_price = manual_price if pricing_mode == "manual" else calculated_price

    update = {
        "estimated_price": active_price,
        "pricing_snapshot": {
            "pricing_mode": pricing_mode,
            "calculated_price": calculated_price,
            "manual_price": manual_price,
            "active_price": active_price,
            "calculation_breakdown": calculation_breakdown,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.job_tickets.update_one({"id": ticket_id}, {"$set": update})

    # Update order totals
    from services.workflow_engine import update_order_progress
    await update_order_progress(db, ticket["order_id"])

    return {"message": "Pricing saved", "active_price": active_price, "pricing_mode": pricing_mode}


def _parse_dimension(val):
    """Parse dimension string like '8ft' or '36in' to inches."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().lower()
    try:
        if 'ft' in s:
            return float(s.replace('ft', '').strip()) * 12
        if 'in' in s:
            return float(s.replace('in', '').replace('"', '').strip())
        if "'" in s:
            return float(s.replace("'", '').strip()) * 12
        return float(s)
    except (ValueError, TypeError):
        return None
