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




def _banner_schema(defaults):
    """Full Banner category schema per spec."""
    materials = defaults.get("materials", [])
    banner_mats = [m for m in materials if m.get("key") in ("banner_material", "ink", "laminate")]
    mat_options = [
        {"value": "banner_13oz", "label": "13oz Vinyl"},
        {"value": "banner_18oz", "label": "18oz Vinyl"},
        {"value": "mesh", "label": "Mesh Banner Material"},
        {"value": "blockout", "label": "Blockout Banner Material"},
        {"value": "retractable_film", "label": "Retractable Film"},
        {"value": "custom", "label": "Other / Custom"},
    ]
    return [
        # Size & Material
        {"key": "width", "label": "Width", "type": "text", "placeholder": "e.g. 8 or 96", "group": "size_material", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "text", "placeholder": "e.g. 3 or 36", "group": "size_material", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [{"value": "feet", "label": "Feet"}, {"value": "inches", "label": "Inches"}], "default": "feet", "group": "size_material", "required": True, "pricing": True},
        {"key": "sq_footage", "label": "Square Footage", "type": "calculated", "group": "size_material", "pricing": True},
        {"key": "material", "label": "Material", "type": "select", "options": mat_options, "group": "size_material", "required": True, "pricing": True},
        {"key": "indoor_outdoor", "label": "Indoor / Outdoor", "type": "select", "options": [{"value": "outdoor", "label": "Outdoor"}, {"value": "indoor", "label": "Indoor"}, {"value": "both", "label": "Both"}], "default": "outdoor", "group": "size_material"},
        {"key": "double_sided", "label": "Sidedness", "type": "select", "options": [{"value": "single", "label": "Single-Sided"}, {"value": "double", "label": "Double-Sided"}], "default": "single", "group": "size_material", "pricing": True},
        # Finishing
        {"key": "hems", "label": "Hems", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "all_sides", "label": "All Sides"}, {"value": "top_bottom", "label": "Top & Bottom"}, {"value": "custom", "label": "Custom"}], "default": "all_sides", "group": "finishing", "pricing": True},
        {"key": "grommets", "label": "Grommets", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "corners", "label": "Corners Only"}, {"value": "every_2ft", "label": "Every 2 ft"}, {"value": "every_3ft", "label": "Every 3 ft"}, {"value": "custom", "label": "Custom"}], "default": "corners", "group": "finishing", "pricing": True},
        {"key": "pole_pockets", "label": "Pole Pockets", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "top", "label": "Top"}, {"value": "bottom", "label": "Bottom"}, {"value": "both", "label": "Both"}, {"value": "custom", "label": "Custom"}], "default": "none", "group": "finishing", "pricing": True},
        {"key": "wind_slits", "label": "Wind Slits", "type": "toggle", "default": False, "group": "finishing", "pricing": True},
        {"key": "reinforced_corners", "label": "Reinforced Corners", "type": "toggle", "default": False, "group": "finishing", "pricing": True},
        {"key": "sewn_edges", "label": "Sewn Edges", "type": "toggle", "default": False, "group": "finishing", "pricing": True},
        {"key": "webbing", "label": "Webbing / Reinforcement", "type": "toggle", "default": False, "group": "finishing", "pricing": True},
        # Design / Artwork
        {"key": "artwork_provided", "label": "Artwork Provided", "type": "toggle", "default": False, "group": "design"},
        {"key": "design_needed", "label": "Design Needed", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "proof_required", "label": "Proof Required", "type": "toggle", "default": True, "group": "design"},
        {"key": "proof_rounds", "label": "Expected Proof Rounds", "type": "number", "placeholder": "1", "group": "design"},
        {"key": "artwork_notes", "label": "Artwork Notes", "type": "textarea", "group": "design"},
        # Production / Delivery
        {"key": "rush_order", "label": "Rush Order", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "outsourced", "label": "Outsourced", "type": "toggle", "default": False, "group": "production"},
        {"key": "hardware_included", "label": "Hardware Included", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "packaging_notes", "label": "Packaging / Rolling Notes", "type": "textarea", "group": "production"},
        {"key": "delivery_notes", "label": "Pickup / Delivery Notes", "type": "textarea", "group": "production"},
    ]


def _apparel_schema(defaults):
    """Full Apparel category schema per spec."""
    garment_types = [
        {"value": "tshirt", "label": "T-Shirt"},
        {"value": "hoodie", "label": "Hoodie"},
        {"value": "crewneck", "label": "Crewneck"},
        {"value": "polo", "label": "Polo"},
        {"value": "hat", "label": "Hat"},
        {"value": "jacket", "label": "Jacket"},
        {"value": "safety_vest", "label": "Safety Vest"},
        {"value": "tank", "label": "Tank Top"},
        {"value": "longsleeve", "label": "Long Sleeve"},
        {"value": "other", "label": "Other Apparel"},
    ]
    decoration_methods = [
        {"value": "htv", "label": "HTV (Heat Transfer Vinyl)"},
        {"value": "dtf", "label": "DTF / Printed Transfer"},
        {"value": "screen_print", "label": "Screen Print Transfer"},
        {"value": "sublimation", "label": "Sublimation"},
        {"value": "embroidery", "label": "Embroidery"},
        {"value": "patch", "label": "Patch / Emblem"},
        {"value": "other", "label": "Other"},
    ]
    print_locations = [
        {"value": "front_center", "label": "Front Center"},
        {"value": "left_chest", "label": "Left Chest"},
        {"value": "right_chest", "label": "Right Chest"},
        {"value": "full_back", "label": "Full Back"},
        {"value": "upper_back", "label": "Upper Back"},
        {"value": "left_sleeve", "label": "Left Sleeve"},
        {"value": "right_sleeve", "label": "Right Sleeve"},
        {"value": "hood", "label": "Hood"},
        {"value": "hat_front", "label": "Hat Front"},
        {"value": "hat_side", "label": "Hat Side"},
        {"value": "hat_back", "label": "Hat Back"},
        {"value": "other", "label": "Other Custom Location"},
    ]
    brand_options = [
        {"value": "gildan_5000", "label": "Gildan 5000"},
        {"value": "gildan_softstyle", "label": "Gildan Softstyle"},
        {"value": "bella_canvas_3001", "label": "Bella+Canvas 3001"},
        {"value": "next_level_3600", "label": "Next Level 3600"},
        {"value": "comfort_colors", "label": "Comfort Colors"},
        {"value": "jerzees", "label": "Jerzees"},
        {"value": "hanes", "label": "Hanes"},
        {"value": "richardson", "label": "Richardson (Hats)"},
        {"value": "port_authority", "label": "Port Authority"},
        {"value": "custom", "label": "Custom / Manual Entry"},
    ]
    return [
        # Garment Information
        {"key": "garment_type", "label": "Garment Type", "type": "select", "options": garment_types, "group": "garment_info", "required": True, "pricing": True},
        {"key": "brand_style", "label": "Brand / Style", "type": "select_or_text", "options": brand_options, "placeholder": "Select or type custom", "group": "garment_info", "pricing": True},
        {"key": "garment_color", "label": "Garment Color", "type": "text", "placeholder": "Black, White, Navy", "group": "garment_info"},
        {"key": "garment_material", "label": "Material / Fabric", "type": "text", "placeholder": "Cotton, Polyester, Blend", "group": "garment_info"},
        {"key": "customer_supplied", "label": "Customer Supplied Garments", "type": "toggle", "default": False, "group": "garment_info", "pricing": True},
        # Size Breakdown
        {"key": "size_xs", "label": "XS", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_s", "label": "S", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_m", "label": "M", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_l", "label": "L", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_xl", "label": "XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_2xl", "label": "2XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_3xl", "label": "3XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_4xl", "label": "4XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_5xl", "label": "5XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        # Decoration
        {"key": "decoration_method", "label": "Decoration Method", "type": "select", "options": decoration_methods, "group": "decoration", "required": True, "pricing": True},
        {"key": "num_colors", "label": "Number of Colors", "type": "number", "placeholder": "1", "group": "decoration", "pricing": True},
        {"key": "specialty_finish", "label": "Specialty Finish", "type": "text", "placeholder": "Metallic, Puff, Glitter", "group": "decoration", "pricing": True},
        {"key": "setup_required", "label": "Setup Required", "type": "toggle", "default": True, "group": "decoration", "pricing": True},
        {"key": "artwork_provided", "label": "Artwork Provided", "type": "toggle", "default": False, "group": "decoration"},
        # Print Locations
        {"key": "print_locations", "label": "Print Locations", "type": "location_picker", "options": print_locations, "group": "print_locations", "pricing": True},
        # Per-location details are handled dynamically in frontend based on selected locations
        # Design / Proof
        {"key": "design_needed", "label": "Design Needed", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "proof_required", "label": "Proof Required", "type": "toggle", "default": True, "group": "design"},
        {"key": "artwork_notes", "label": "Notes", "type": "textarea", "group": "design"},
        # Production
        {"key": "rush_order", "label": "Rush Order", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "outsourced", "label": "Outsourced", "type": "toggle", "default": False, "group": "production"},
        {"key": "folding_bagging", "label": "Folding / Bagging Needed", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "tagging_notes", "label": "Tagging / Sorting Notes", "type": "textarea", "group": "production"},
    ]


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
        "banners": _banner_schema(defaults),
        "apparel": _apparel_schema(defaults),
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
        "apparel": _apparel_schema(defaults),
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

    # Subtypes per category (from settings or defaults)
    subtypes = {
        "banners": [
            {"value": "standard", "label": "Standard Banner"},
            {"value": "mesh", "label": "Mesh Banner"},
            {"value": "pole", "label": "Pole Banner"},
            {"value": "retractable", "label": "Retractable Banner"},
            {"value": "double_sided", "label": "Double-Sided Banner"},
            {"value": "grommets", "label": "Vinyl Banner with Grommets"},
            {"value": "custom", "label": "Custom Banner"},
        ],
        "apparel": [
            {"value": "tshirt", "label": "T-Shirt"},
            {"value": "hoodie", "label": "Hoodie"},
            {"value": "crewneck", "label": "Crewneck"},
            {"value": "polo", "label": "Polo"},
            {"value": "hat", "label": "Hat"},
            {"value": "jacket", "label": "Jacket"},
            {"value": "safety_vest", "label": "Safety Vest"},
            {"value": "other", "label": "Other Apparel"},
        ],
        "rigid_signs": [
            {"value": "yard_sign", "label": "Yard Sign"},
            {"value": "aluminum", "label": "Aluminum Sign"},
            {"value": "acm", "label": "ACM (Aluminum Composite)"},
            {"value": "pvc", "label": "PVC Sign"},
            {"value": "foam_board", "label": "Foam Board"},
            {"value": "coroplast", "label": "Corrugated Plastic"},
            {"value": "custom", "label": "Custom Rigid Sign"},
        ],
        "cut_vinyl": [
            {"value": "decals", "label": "Decals"},
            {"value": "lettering", "label": "Lettering"},
            {"value": "window", "label": "Window Graphics"},
            {"value": "wall", "label": "Wall Graphics"},
            {"value": "vehicle", "label": "Vehicle Graphics"},
            {"value": "layered", "label": "Layered Vinyl"},
            {"value": "single_color", "label": "Single Color Vinyl"},
            {"value": "custom", "label": "Custom Vinyl"},
        ],
        "vehicle_wrap": [
            {"value": "full_wrap", "label": "Full Wrap"},
            {"value": "partial_50", "label": "Partial Wrap (50%)"},
            {"value": "partial_75", "label": "Partial Wrap (75%)"},
            {"value": "spot_graphics", "label": "Spot Graphics"},
            {"value": "fleet", "label": "Fleet Graphics"},
            {"value": "trailer", "label": "Trailer Wrap"},
            {"value": "box_truck", "label": "Box Truck Wrap"},
            {"value": "van", "label": "Van Wrap"},
            {"value": "car", "label": "Car Wrap"},
            {"value": "custom", "label": "Custom Vehicle Graphics"},
        ],
    }

    return {
        "category": category,
        "subtypes": subtypes.get(category, []),
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
