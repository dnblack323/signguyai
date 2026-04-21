"""
Job Tickets API Routes

CRUD for Job Ticket records (Layer 2) — the operational source of truth.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from copy import deepcopy

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

SETTINGS_CATEGORY_KEYS = {
    "vehicle_wrap": "vehicle_wraps",
    "promo_misc": "custom",
    "digital_print": "digital_print",
}

FALLBACK_MATERIALS_CATALOG = {
    "vinyl": [
        {"id": "oracal_651", "name": "Oracal 651", "cost_per_sqft": 1.25},
        {"id": "oracal_751", "name": "Oracal 751", "cost_per_sqft": 2.50},
        {"id": "oracal_951", "name": "Oracal 951", "cost_per_sqft": 2.50},
        {"id": "avery_hp750", "name": "Avery HP750", "cost_per_sqft": 2.50},
        {"id": "reflective_vinyl", "name": "Reflective Vinyl", "cost_per_sqft": 4.50},
        {"id": "metallic_vinyl", "name": "Metallic Vinyl", "cost_per_sqft": 4.50},
        {"id": "fluorescent_vinyl", "name": "Fluorescent Vinyl", "cost_per_sqft": 4.50},
        {"id": "etched_frost_vinyl", "name": "Etched / Frost Vinyl", "cost_per_sqft": 4.50},
        {"id": "wall_vinyl", "name": "Wall Vinyl", "cost_per_sqft": 2.50},
        {"id": "specialty_custom_vinyl", "name": "Specialty / Custom Vinyl", "cost_per_sqft": 4.50},
    ],
    "print_material": [
        {"id": "printable_adhesive_vinyl", "name": "Printable Adhesive Vinyl", "cost_per_sqft": 1.50},
        {"id": "poster_paper", "name": "Poster Paper", "cost_per_sqft": 0.60},
        {"id": "canvas", "name": "Canvas", "cost_per_sqft": 2.25},
        {"id": "backlit_film", "name": "Backlit Film", "cost_per_sqft": 2.50},
        {"id": "perforated_window_film", "name": "Perforated Window Film", "cost_per_sqft": 2.75},
        {"id": "wall_graphic_media", "name": "Wall Graphic Media", "cost_per_sqft": 2.25},
        {"id": "floor_graphic_media", "name": "Floor Graphic Media", "cost_per_sqft": 3.00},
        {"id": "removable_adhesive_print_media", "name": "Removable Adhesive Print Media", "cost_per_sqft": 1.50},
        {"id": "photo_paper", "name": "Photo Paper", "cost_per_sqft": 0.75},
        {"id": "specialty_print_media", "name": "Specialty / Custom Print Media", "cost_per_sqft": 2.00},
    ],
    "substrate": [
        {"id": "coroplast_4mm", "name": "Coroplast 4mm", "cost_per_sqft": 0.90},
        {"id": "coroplast_10mm", "name": "Coroplast 10mm", "cost_per_sqft": 1.60},
        {"id": "pvc_3mm", "name": "PVC 3mm", "cost_per_sqft": 2.25},
        {"id": "pvc_6mm", "name": "PVC 6mm", "cost_per_sqft": 3.50},
        {"id": "acm_dibond_3mm", "name": "ACM / Dibond 3mm", "cost_per_sqft": 4.25},
        {"id": "aluminum_040", "name": "Aluminum .040", "cost_per_sqft": 3.25},
        {"id": "aluminum_063", "name": "Aluminum .063", "cost_per_sqft": 4.25},
        {"id": "aluminum_080", "name": "Aluminum .080", "cost_per_sqft": 5.25},
        {"id": "acrylic_1_8", "name": "Acrylic 1/8\"", "cost_per_sqft": 4.50},
        {"id": "acrylic_1_4", "name": "Acrylic 1/4\"", "cost_per_sqft": 6.50},
        {"id": "foamboard_3_16", "name": "Foamboard 3/16\"", "cost_per_sqft": 1.25},
        {"id": "mdo_1_2", "name": "MDO 1/2\"", "cost_per_sqft": 3.75},
        {"id": "custom_other_substrate", "name": "Custom Other Substrate", "cost_per_sqft": 4.00},
    ],
    "finish": [
        {"id": "rigid_finish_standard", "name": "Standard Protective Finish", "cost_per_sqft": 0.75},
    ],
    "laminate": [
        {"id": "laminate_gloss", "name": "Gloss Laminate", "cost_per_sqft": 0.85},
        {"id": "laminate_matte", "name": "Matte Laminate", "cost_per_sqft": 0.85},
        {"id": "laminate_heavy_duty", "name": "Heavy-Duty Laminate", "cost_per_sqft": 1.25},
        {"id": "laminate_floor", "name": "Floor Laminate", "cost_per_sqft": 1.25},
        {"id": "laminate_uv", "name": "UV Laminate", "cost_per_sqft": 0.85},
        {"id": "laminate_specialty", "name": "Specialty / Custom Laminate", "cost_per_sqft": 0.85},
    ],
    "hardware": [
        {"id": "hw-h-stake", "name": "Standard H-Stake", "cost_each": 1.50},
        {"id": "hw-heavy-stake", "name": "Heavy-Duty Stake", "cost_each": 2.50},
        {"id": "hw-screws", "name": "Screws / Basic Mounting Set", "cost_each": 1.00},
        {"id": "hw-standoff", "name": "Stand-Off Set", "cost_each": 3.00},
        {"id": "hw-easel", "name": "Easel Back", "cost_each": 2.00},
        {"id": "hw-hanging", "name": "Hanging Hardware", "cost_each": 1.50},
        {"id": "hw-custom", "name": "Custom Other Hardware", "cost_each": 2.00},
    ],
    "apparel": [
        {"id": "tshirt", "name": "T-Shirt", "cost_each": 4.50},
        {"id": "hoodie", "name": "Hoodie", "cost_each": 18.00},
        {"id": "hat", "name": "Hat/Cap", "cost_each": 8.00},
        {"id": "polo", "name": "Polo Shirt", "cost_each": 12.00},
        {"id": "tank", "name": "Tank Top", "cost_each": 4.00},
        {"id": "longsleeve", "name": "Long Sleeve", "cost_each": 7.50},
        {"id": "jacket", "name": "Jacket", "cost_each": 25.00},
        {"id": "crewneck", "name": "Crewneck Sweatshirt", "cost_each": 15.00},
        {"id": "safety_vest", "name": "Safety Vest", "cost_each": 10.00},
    ],
    "decoration": [
        {"id": "htv", "name": "HTV (Heat Transfer Vinyl)", "cost_per_color": 0.50},
        {"id": "screen_print", "name": "Screen Print Transfer", "cost_per_color": 0.35},
        {"id": "dtf", "name": "DTF / Printed Transfer", "cost_per_sqin": 0.03},
        {"id": "sublimation", "name": "Sublimation", "cost_per_sqin": 0.04},
        {"id": "embroidery", "name": "Embroidery", "cost_per_stitch": 0.01},
        {"id": "patch", "name": "Patch / Emblem", "cost_each": 3.00},
    ],
    "vehicle_type": [
        {"id": "car_sedan", "name": "Car (Sedan)", "base_sqft": 150},
        {"id": "car_suv", "name": "Car (SUV)", "base_sqft": 200},
        {"id": "pickup", "name": "Pickup Truck", "base_sqft": 175},
        {"id": "van_cargo", "name": "Cargo Van", "base_sqft": 250},
        {"id": "van_sprinter", "name": "Sprinter Van", "base_sqft": 350},
        {"id": "box_truck_12ft", "name": "Box Truck (12ft)", "base_sqft": 400},
        {"id": "box_truck_16ft", "name": "Box Truck (16ft)", "base_sqft": 500},
        {"id": "box_truck_24ft", "name": "Box Truck (24ft)", "base_sqft": 650},
        {"id": "trailer", "name": "Trailer", "base_sqft": 450},
        {"id": "semi", "name": "Semi Truck", "base_sqft": 800},
        {"id": "other", "name": "Other Vehicle", "base_sqft": 160},
    ],
}


def _settings_category_key(category: str) -> str:
    return SETTINGS_CATEGORY_KEYS.get(category, category)


def _sum_apparel_sizes(specs: dict) -> int:
    if not isinstance(specs, dict):
        return 0
    size_keys = [
        "size_xs", "size_s", "size_m", "size_l", "size_xl",
        "size_2xl", "size_3xl", "size_4xl", "size_5xl",
    ]
    return sum(int(specs.get(key, 0) or 0) for key in size_keys)


def _derive_ticket_quantity(category: str, quantity: int, specs: dict) -> int:
    if category == "apparel":
        size_total = _sum_apparel_sizes(specs or {})
        if size_total > 0:
            return size_total
    return max(int(quantity or 1), 1)


def _normalize_vehicle_coverage(coverage_type: Optional[str], coverage_percent: Optional[float] = None) -> Optional[str]:
    raw = str(coverage_type or "").strip().lower()
    mapping = {
        "25": "spot",
        "50": "half",
        "75": "partial",
        "100": "full",
        "spot_graphics": "spot",
        "partial_50": "half",
        "partial_75": "partial",
        "full_wrap": "full",
    }
    if raw in mapping:
        return mapping[raw]
    if raw == "custom":
        # Preserve custom — the calculator handles custom_coverage_percent directly
        return "custom"
    return raw or None


def _normalize_substrate_type(substrate: Optional[str], thickness: Optional[str]) -> Optional[str]:
    substrate_map = {
        ("coroplast", "4mm"): "coroplast_4mm",
        ("coroplast", "10mm"): "coroplast_10mm",
        ("aluminum", "0.040"): "aluminum_040",
        ("aluminum", "0.063"): "aluminum_063",
        ("aluminum", "0.080"): "aluminum_080",
        ("pvc", "3mm_pvc"): "pvc_3mm",
        ("pvc", "6mm_pvc"): "pvc_6mm",
    }
    if not substrate:
        return None
    return substrate_map.get((str(substrate).lower(), str(thickness or "").lower()), substrate)


def _infer_material_bucket(material: dict) -> Optional[str]:
    category = str(material.get("category") or "").lower()
    key = str(material.get("key") or material.get("id") or "").lower()
    if category in {"print_material", "media", "banner", "print_media"}:
        return "print_material"
    if category in {"vinyl", "cut_vinyl"}:
        return "vinyl"
    if category in {"substrate", "board"}:
        return "substrate"
    if category == "laminate":
        return "laminate"
    if category in {"rigid_finish", "protective_finish", "finish"}:
        return "finish"
    if category == "apparel":
        return "apparel"
    if category in {"decoration", "transfer_type"}:
        return "decoration"
    if category == "vehicle_type":
        return "vehicle_type"
    if key.startswith("banner_") or key in {"mesh", "vinyl_adhesive", "poster_paper", "canvas", "backlit", "perforated", "blockout", "retractable_film", "static_cling", "floor_graphic", "printable_adhesive_vinyl", "backlit_film", "perforated_window_film", "wall_graphic_media", "floor_graphic_media", "removable_adhesive_print_media", "photo_paper", "specialty_print_media"}:
        return "print_material"
    if key.startswith("laminate_") or key in {"laminate_gloss", "laminate_matte", "laminate_heavy_duty", "laminate_floor", "laminate_uv", "laminate_specialty"}:
        return "laminate"
    if key in {"rigid_finish_standard"}:
        return "finish"
    if key in {"oracal_651", "oracal_751", "oracal_951", "avery_hp750", "reflective", "specialty", "vinyl", "reflective_vinyl", "metallic_vinyl", "fluorescent_vinyl", "etched_frost_vinyl", "wall_vinyl", "specialty_custom_vinyl"}:
        return "vinyl"
    if key.startswith("coroplast") or key.startswith("aluminum") or key.startswith("pvc") or key in {"acrylic", "dibond", "mdo", "foam_board", "rigid_sign_board", "acrylic_sheet", "acm_dibond_3mm", "acrylic_1_8", "acrylic_1_4", "foamboard_3_16", "mdo_1_2", "custom_other_substrate"}:
        return "substrate"
    if key in {"tshirt", "hoodie", "hat", "polo", "tank", "longsleeve", "jacket", "crewneck", "safety_vest", "apparel_blank"}:
        return "apparel"
    if key in {"htv", "screen_print", "dtf", "sublimation", "embroidery", "patch", "apparel_decoration"}:
        return "decoration"
    if key in {"car_sedan", "car_suv", "pickup", "van_mini", "van_cargo", "van_sprinter", "box_truck_12ft", "box_truck_16ft", "box_truck_24ft", "trailer", "semi", "other"}:
        return "vehicle_type"
    return None


def _build_materials_catalog(defaults: dict) -> dict:
    catalog = {key: [] for key in FALLBACK_MATERIALS_CATALOG.keys()}
    active_materials = [m for m in defaults.get("materials", []) if m.get("is_active", True)]
    for material in active_materials:
        bucket = _infer_material_bucket(material)
        if not bucket or bucket not in catalog:
            continue
        key = material.get("key") or material.get("id")
        if not key:
            continue
        entry = {"id": key, "name": material.get("name") or key.replace("_", " ").title()}
        cost = float(material.get("cost_per_sqft", material.get("cost_per_unit", 0)) or 0)
        unit_type = material.get("unit_type")
        if bucket == "apparel":
            entry["cost_each"] = cost
        elif bucket == "decoration":
            if unit_type == "per_stitch":
                entry["cost_per_stitch"] = cost
            elif unit_type == "per_sqin":
                entry["cost_per_sqin"] = cost
            elif unit_type == "per_color":
                entry["cost_per_color"] = cost
            else:
                entry["cost_each"] = cost
        elif bucket == "vehicle_type":
            entry["base_sqft"] = float(material.get("base_sqft", 0) or 0)
        else:
            entry["cost_per_sqft"] = cost

        existing_idx = next((idx for idx, item in enumerate(catalog[bucket]) if item.get("id") == key), None)
        if existing_idx is None:
            catalog[bucket].append(entry)
        else:
            catalog[bucket][existing_idx] = {**catalog[bucket][existing_idx], **entry}

    for hardware in defaults.get("hardware_accessories", []) or []:
        if not hardware.get("is_active", True):
            continue
        key = hardware.get("id") or hardware.get("name")
        if not key:
            continue
        entry = {
            "id": key,
            "name": hardware.get("name") or key.replace("_", " ").title(),
            "cost_each": float(hardware.get("purchase_cost", 0) or 0),
            "sell_each": float(hardware.get("default_sell_price", 0) or 0),
        }
        existing_idx = next((idx for idx, item in enumerate(catalog["hardware"]) if item.get("id") == key), None)
        if existing_idx is None:
            catalog["hardware"].append(entry)
        else:
            catalog["hardware"][existing_idx] = {**catalog["hardware"][existing_idx], **entry}

    for key, fallback_items in FALLBACK_MATERIALS_CATALOG.items():
        if not catalog.get(key):
            catalog[key] = deepcopy(fallback_items)
    return catalog


def _build_ticket_pricing_payload(ticket: dict, pricing_input: Optional[dict] = None):
    specs = ticket.get("specs", {}) or {}
    incoming = pricing_input or {}
    unit = str(specs.get("unit_of_measure") or "inches").lower()
    width_raw = _parse_dimension(specs.get("width") or incoming.get("width_inches"))
    height_raw = _parse_dimension(specs.get("height") or incoming.get("length_inches"))
    width_inches = (width_raw * 12) if unit == "feet" and width_raw else width_raw
    height_inches = (height_raw * 12) if unit == "feet" and height_raw else height_raw
    category_map = {
        "banners": "banners",
        "rigid_signs": "rigid_signs",
        "cut_vinyl": "cut_vinyl",
        "digital_print": "digital_print",
        "vehicle_wrap": "vehicle_graphics",
        "apparel": "apparel",
        "services": "services",
        "promo_misc": "promotional",
        "custom": "custom",
    }
    is_vinyl_category = ticket.get("item_category") in {"cut_vinyl", "vehicle_wrap"}
    coverage_percent = float(specs.get("coverage_percent", 0) or 0)
    coverage_type = _normalize_vehicle_coverage(specs.get("coverage_type"), coverage_percent)
    merged_input = {
        "category": category_map.get(ticket.get("item_category"), "custom"),
        "complexity": int(incoming.get("complexity", 1) or 1),
        "width_inches": width_inches,
        "length_inches": height_inches,
        "unit_of_measure": specs.get("unit_of_measure") or incoming.get("unit_of_measure") or "inches",
        "print_media_key": specs.get("print_media_key") or specs.get("media_type") or specs.get("material"),
        "use_type": specs.get("use_type") or specs.get("application_type"),
        "print_quality_mode": specs.get("print_quality_mode"),
        "ink_coverage_percent": specs.get("ink_coverage_percent"),
        "laminate": bool(specs.get("laminate") or (specs.get("lamination") not in ("none", "", None, False))),
        "laminate_material_key": specs.get("laminate_material_key") or specs.get("laminate_type") or (specs.get("lamination") if specs.get("lamination") not in ("none", "") else None),
        "contour_cut_type": specs.get("contour_cut_type"),
        "trim_finish_type": specs.get("trim_finish_type"),
        "piece_separation_required": bool(specs.get("piece_separation_required")),
        "separated_piece_count": int(specs.get("separated_piece_count", 0) or 0),
        "mounted_to_substrate": bool(specs.get("mounted_to_substrate")),
        "substrate_material_key": specs.get("substrate_material_key"),
        "vinyl_type_key": specs.get("vinyl_type_key") or (specs.get("vinyl_type") if is_vinyl_category else None),
        "vinyl_type": specs.get("vinyl_type") if is_vinyl_category else None,
        "num_colors": int(specs.get("num_colors", 1) or 1),
        "weeding_complexity": specs.get("weeding_complexity"),
        "masking_required": specs.get("masking_required"),
        "surface_type": specs.get("surface_type"),
        "substrate_type_key": specs.get("substrate_type_key") or _normalize_substrate_type(specs.get("substrate"), specs.get("thickness")),
        "substrate_type": _normalize_substrate_type(specs.get("substrate"), specs.get("thickness")),
        "thickness": specs.get("thickness"),
        "graphic_method": specs.get("graphic_method"),
        "protective_finish": bool(specs.get("protective_finish")),
        "protective_finish_type": specs.get("protective_finish_type"),
        "sidedness": specs.get("sidedness"),
        "double_sided_art": specs.get("double_sided_art"),
        "shape_type": specs.get("shape_type"),
        "finish_quality": specs.get("finish_quality"),
        "hardware_included": bool(specs.get("hardware_included")),
        "hardware_type": specs.get("hardware_type"),
        "drill_prep_required": bool(specs.get("drill_prep_required")),
        "artwork_ready": bool(specs.get("artwork_ready") or specs.get("artwork_provided")),
        "artwork_needed": bool(specs.get("artwork_needed") or specs.get("design_needed") or ticket.get("design_needed")),
        "design_complexity": specs.get("design_complexity"),
        "file_cleanup_needed": bool(specs.get("file_cleanup_needed")),
        "install_required": bool(specs.get("install_required")),
        "install_complexity": specs.get("install_complexity"),
        "apparel_type": specs.get("garment_type") or specs.get("subtype"),
        "transfer_type": specs.get("decoration_method") or specs.get("print_method"),
        "num_print_locations": len(specs.get("print_locations", [])) or 1,
        # Apparel — Foundation-driven inputs
        "apparel_product_type": specs.get("apparel_product_type") or specs.get("garment_type"),
        "apparel_brand_style_key": specs.get("apparel_brand_style_key") or specs.get("brand_style"),
        "apparel_garment_color": specs.get("apparel_garment_color") or specs.get("garment_color"),
        "apparel_placement_set": specs.get("apparel_placement_set") or specs.get("apparel_placement_set_hat"),
        "apparel_decoration_method": specs.get("apparel_decoration_method") or specs.get("decoration_method"),
        "apparel_decoration_subtype": specs.get("apparel_decoration_subtype"),
        "apparel_plus_size_count": (
            int((specs.get("size_2xl", 0) or 0) + (specs.get("size_3xl", 0) or 0) * 2
                + (specs.get("size_4xl", 0) or 0) * 3 + (specs.get("size_5xl", 0) or 0) * 4)
            if any(specs.get(k) for k in ("size_2xl", "size_3xl", "size_4xl", "size_5xl"))
            else (int(specs.get("apparel_plus_size_count", 0) or 0) or None)
        ),
        "apparel_custom_name_number": bool(specs.get("apparel_custom_name_number")) if specs.get("apparel_custom_name_number") is not None else None,
        "apparel_custom_name_number_count": int(specs.get("apparel_custom_name_number_count", 0) or 0) or None,
        "apparel_specialty_finish": bool(specs.get("apparel_specialty_finish")) if specs.get("apparel_specialty_finish") is not None else None,
        "apparel_two_tone_hat_finish": bool(specs.get("apparel_two_tone_hat_finish")) if specs.get("apparel_two_tone_hat_finish") is not None else None,
        "apparel_leather_patch": bool(specs.get("apparel_leather_patch")) if specs.get("apparel_leather_patch") is not None else None,
        "apparel_bag_and_fold": bool(specs.get("apparel_bag_and_fold") or specs.get("folding_bagging")) if (specs.get("apparel_bag_and_fold") is not None or specs.get("folding_bagging") is not None) else None,
        "apparel_num_colors": int(specs.get("apparel_num_colors", specs.get("num_colors", 0)) or 0) or None,
        "apparel_stitch_count": int(specs.get("apparel_stitch_count", 0) or 0) or None,
        "apparel_rush_percent": float(specs.get("apparel_rush_percent", 0) or 0) or None,
        "apparel_manual_quote_override": float(specs.get("apparel_manual_quote_override", 0) or 0) or None,
        # Banner-specific pricing inputs (must match JobItemPricingData keys)
        "banner_material_key": specs.get("banner_material_key") or specs.get("material"),
        "banner_use_type": specs.get("banner_use_type") or specs.get("use_type"),
        "banner_laminate": bool(specs.get("banner_laminate")) if specs.get("banner_laminate") is not None else None,
        "banner_laminate_type_key": specs.get("banner_laminate_type_key"),
        "banner_hems": specs.get("banner_hems") or specs.get("hems"),
        "banner_grommets": specs.get("banner_grommets") or specs.get("grommets"),
        "banner_grommet_count": int(specs.get("banner_grommet_count", 0) or 0) or None,
        "banner_pole_pockets": specs.get("banner_pole_pockets") or specs.get("pole_pockets"),
        "banner_reinforced_corners": bool(specs.get("banner_reinforced_corners")) if specs.get("banner_reinforced_corners") is not None else None,
        "banner_wind_slits": bool(specs.get("banner_wind_slits")) if specs.get("banner_wind_slits") is not None else (bool(specs.get("wind_slits")) if specs.get("wind_slits") is not None else None),
        "banner_specialty_sewing": bool(specs.get("banner_specialty_sewing")) if specs.get("banner_specialty_sewing") is not None else None,
        "banner_double_sided": specs.get("banner_double_sided"),
        "banner_event_premium": bool(specs.get("banner_event_premium")) if specs.get("banner_event_premium") is not None else None,
        "banner_hardware_keys": specs.get("banner_hardware_keys") or [],
        "service_type": specs.get("service_type") or specs.get("subtype"),
        # Services — Foundation-driven inputs
        "services_billing_unit": specs.get("services_billing_unit"),
        "services_labor_role": specs.get("services_labor_role"),
        "services_flat_fee": float(specs.get("services_flat_fee", 0) or 0) or None,
        "services_unit_rate_override": float(specs.get("services_unit_rate_override", 0) or 0) or None,
        "services_complexity": specs.get("services_complexity"),
        "services_minimum_applies": bool(specs.get("services_minimum_applies")) if specs.get("services_minimum_applies") is not None else None,
        "services_travel_required": bool(specs.get("services_travel_required")) if specs.get("services_travel_required") is not None else None,
        "services_travel_miles": float(specs.get("services_travel_miles", 0) or 0) or None,
        "services_trip_charge_applies": bool(specs.get("services_trip_charge_applies")) if specs.get("services_trip_charge_applies") is not None else None,
        "services_trip_count": int(specs.get("services_trip_count", 0) or 0) or None,
        "services_equipment_required": bool(specs.get("services_equipment_required")) if specs.get("services_equipment_required") is not None else None,
        "services_equipment_type": specs.get("services_equipment_type"),
        "services_equipment_days": float(specs.get("services_equipment_days", 0) or 0) or None,
        "services_equipment_hours": float(specs.get("services_equipment_hours", 0) or 0) or None,
        "services_subcontracted": bool(specs.get("services_subcontracted")) if specs.get("services_subcontracted") is not None else None,
        "services_subcontract_cost": float(specs.get("services_subcontract_cost", 0) or 0) or None,
        "services_subcontract_markup_applies": bool(specs.get("services_subcontract_markup_applies")) if specs.get("services_subcontract_markup_applies") is not None else None,
        "services_permit_external_fee": float(specs.get("services_permit_external_fee", 0) or 0) or None,
        "services_manual_quote_override": float(specs.get("services_manual_quote_override", 0) or 0) or None,
        "services_minimum_override": float(specs.get("services_minimum_override", 0) or 0) or None,
        "hourly_rate_override": float(specs.get("hourly_rate_override", 0) or 0) or None,
        "vehicle_type": specs.get("vehicle_type"),
        "coverage_type": coverage_type,
        "custom_coverage_percent": float(specs.get("custom_coverage_percent", specs.get("coverage_percent", 0)) or 0) or None,
        "estimated_vehicle_sqft": float(specs.get("estimated_vehicle_sqft", 0) or 0) or None,
        "wrap_material_key": specs.get("wrap_material_key") or specs.get("vinyl_type"),
        "wrap_laminate_required": bool(specs.get("wrap_laminate_required")) if specs.get("wrap_laminate_required") is not None else None,
        "wrap_laminate_type_key": specs.get("wrap_laminate_type_key") or specs.get("lamination"),
        "window_perf_included": bool(specs.get("window_perf_included")) if specs.get("window_perf_included") is not None else None,
        "window_perf_scope": specs.get("window_perf_scope"),
        "surface_prep_level": specs.get("surface_prep_level") or ("basic" if specs.get("surface_prep") else None),
        "removal_scope": specs.get("removal_scope") or ("partial" if specs.get("removal_required") else None),
        "install_difficulty_level": specs.get("install_difficulty_level") or specs.get("install_difficulty"),
        "seam_complexity": specs.get("seam_complexity"),
        "second_installer_required": bool(specs.get("second_installer_required")) if specs.get("second_installer_required") is not None else None,
        "estimated_hours": float(specs.get("estimated_hours", 0) or specs.get("estimated_install_hours", 0) or 0) or None,
        "rush_order": bool(specs.get("rush_order")),
        **{k: v for k, v in incoming.items() if v is not None and k not in {"complexity"}},
    }
    sanitized = {}
    for key, value in merged_input.items():
        if key == "category":
            sanitized[key] = value
        elif isinstance(value, str) and value.strip() == "":
            sanitized[key] = None
        else:
            sanitized[key] = value
    return sanitized["category"], sanitized


async def _calculate_ticket_snapshot(ticket: dict, tenant_id: str):
    from server import calculate_pricing
    from models.enums import PricingCategory
    from models.pricing import JobItemPricingData

    pricing_category, pricing_input = _build_ticket_pricing_payload(ticket)
    quantity = _derive_ticket_quantity(ticket.get("item_category", "custom"), ticket.get("quantity", 1), ticket.get("specs", {}))
    try:
        category_enum = PricingCategory(pricing_category)
        pricing_data = JobItemPricingData(**pricing_input)
        calculation = await calculate_pricing(category_enum, pricing_data, quantity, tenant_id)
        calculation_data = calculation.model_dump()
        return {
            "estimated_price": calculation.selling_price,
            "pricing_snapshot": {
                "pricing_mode": "calculator",
                "calculated_price": calculation.selling_price,
                "manual_price": 0,
                "active_price": calculation.selling_price,
                "calculation_breakdown": calculation_data,
                "saved_at": datetime.now(timezone.utc).isoformat(),
            },
        }
    except Exception:
        return None




def _banner_schema(defaults, material_opts=None):
    """Full Banner category schema — all options sourced from Pricing Foundation defaults."""
    cat_defaults = (defaults.get("category_defaults", {}) or {}).get("banners", {}) or {}
    materials = defaults.get("materials", []) or []
    hardware_list = defaults.get("hardware_accessories", []) or []

    available_keys = cat_defaults.get("available_banner_material_keys") or []
    def _material_by_key(k):
        return next((m for m in materials if (m.get("key") == k or m.get("id") == k) and m.get("is_active", True)), None)
    banner_material_options = []
    for k in available_keys:
        m = _material_by_key(k)
        if m:
            banner_material_options.append({"value": m.get("key") or m.get("id"), "label": m.get("name") or k})
    if not banner_material_options:
        banner_material_options = [
            {"value": "banner_13oz", "label": "13 oz Banner"},
            {"value": "banner_18oz", "label": "18 oz Banner"},
            {"value": "banner_mesh", "label": "Mesh Banner"},
            {"value": "banner_blockout", "label": "Blockout Banner"},
            {"value": "banner_pole", "label": "Pole Banner Material"},
            {"value": "banner_fabric", "label": "Fabric Display Banner"},
            {"value": "banner_double_sided", "label": "Double-Sided Banner Material"},
            {"value": "banner_custom", "label": "Specialty / Custom Banner Material"},
        ]

    # Optional laminate/coating options (any material compatible with banners + category banner_coating or laminate)
    laminate_options = [
        {"value": m.get("key") or m.get("id"), "label": m.get("name")}
        for m in materials
        if m.get("is_active", True)
        and (
            str(m.get("category", "")).lower() in {"banner_coating", "laminate"}
            and ("banners" in (m.get("compatible_categories") or []) or str(m.get("category", "")).lower() == "banner_coating")
        )
    ]
    if not laminate_options:
        laminate_options = [{"value": "banner_laminate_coating", "label": "Optional Laminate / Coating"}]

    # Banner hardware (multi-select) filtered to compat ["banners"]
    banner_hardware_options = [
        {"value": h.get("id") or h.get("key"), "label": h.get("name")}
        for h in hardware_list
        if h.get("is_active", True) and "banners" in (h.get("compatible_categories") or [])
    ]

    default_material = cat_defaults.get("default_banner_material_key", "banner_13oz")
    default_uom = cat_defaults.get("default_unit_of_measure", "feet")
    default_use_type = cat_defaults.get("default_use_type", "outdoor")
    default_hems = cat_defaults.get("default_hems", "standard")
    default_grommets = cat_defaults.get("default_grommets", "corners")
    default_pole_pockets = cat_defaults.get("default_pole_pockets", "none")
    default_double_sided = cat_defaults.get("default_double_sided", "no")
    default_reinforced = bool(cat_defaults.get("default_reinforced_corners", False))
    default_wind_slits = bool(cat_defaults.get("default_wind_slits", False))
    default_specialty_sewing = bool(cat_defaults.get("default_specialty_sewing", False))
    default_event = bool(cat_defaults.get("default_event_premium", False))
    default_install_complexity = cat_defaults.get("default_install_complexity", "easy")
    default_design_complexity = cat_defaults.get("default_design_complexity", "simple")
    default_laminate_required = bool(cat_defaults.get("default_laminate_required", False))
    default_laminate_key = cat_defaults.get("default_laminate_key", "banner_laminate_coating")
    default_install_included = bool(cat_defaults.get("default_install_included", False))

    return [
        # Size & Material
        {"key": "width", "label": "Width", "type": "text", "placeholder": "e.g. 8 or 96", "group": "size_material", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "text", "placeholder": "e.g. 3 or 36", "group": "size_material", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [{"value": "feet", "label": "Feet"}, {"value": "inches", "label": "Inches"}], "default": default_uom, "group": "size_material", "required": True, "pricing": True},
        {"key": "sq_footage", "label": "Square Footage", "type": "calculated", "group": "size_material", "pricing": True},
        {"key": "banner_material_key", "label": "Banner Material Type", "type": "select", "options": banner_material_options, "default": default_material, "group": "size_material", "required": True, "pricing": True},
        {"key": "banner_use_type", "label": "Use Type", "type": "select", "options": [
            {"value": "indoor", "label": "Indoor"},
            {"value": "outdoor", "label": "Outdoor"},
            {"value": "event_display", "label": "Event / Display"},
            {"value": "fence", "label": "Fence"},
            {"value": "pole_banner", "label": "Pole Banner"},
            {"value": "backwall_step_repeat", "label": "Backwall / Step-and-Repeat"},
            {"value": "custom", "label": "Custom"},
        ], "default": default_use_type, "group": "size_material", "pricing": True},
        {"key": "banner_double_sided", "label": "Double-Sided?", "type": "select", "options": [
            {"value": "no", "label": "No"},
            {"value": "same", "label": "Same art both sides"},
            {"value": "different", "label": "Different art both sides"},
        ], "default": default_double_sided, "group": "size_material", "pricing": True},
        # Laminate / Coating
        {"key": "banner_laminate", "label": "Laminate / Coating?", "type": "toggle", "default": default_laminate_required, "group": "finishing", "pricing": True},
        {"key": "banner_laminate_type_key", "label": "Laminate / Coating Type", "type": "select", "options": laminate_options, "default": default_laminate_key, "group": "finishing", "pricing": True},
        # Finishing
        {"key": "banner_hems", "label": "Hems", "type": "select", "options": [
            {"value": "none", "label": "None"},
            {"value": "standard", "label": "Standard Hem"},
            {"value": "reinforced", "label": "Reinforced Hem"},
        ], "default": default_hems, "group": "finishing", "pricing": True},
        {"key": "banner_grommets", "label": "Grommets", "type": "select", "options": [
            {"value": "none", "label": "None"},
            {"value": "corners", "label": "Corners Only"},
            {"value": "every_2ft", "label": "Every 2 ft"},
            {"value": "every_3ft", "label": "Every 3 ft"},
            {"value": "custom", "label": "Custom Count"},
        ], "default": default_grommets, "group": "finishing", "pricing": True},
        {"key": "banner_grommet_count", "label": "Grommet Count (if custom)", "type": "number", "default": 0, "group": "finishing", "pricing": True},
        {"key": "banner_pole_pockets", "label": "Pole Pockets", "type": "select", "options": [
            {"value": "none", "label": "None"},
            {"value": "top", "label": "Top Only"},
            {"value": "top_and_bottom", "label": "Top and Bottom"},
            {"value": "side_pockets", "label": "Side Pockets"},
        ], "default": default_pole_pockets, "group": "finishing", "pricing": True},
        {"key": "banner_reinforced_corners", "label": "Reinforced Corners?", "type": "toggle", "default": default_reinforced, "group": "finishing", "pricing": True},
        {"key": "banner_wind_slits", "label": "Wind Slits?", "type": "toggle", "default": default_wind_slits, "group": "finishing", "pricing": True},
        {"key": "banner_specialty_sewing", "label": "Specialty Sewing?", "type": "toggle", "default": default_specialty_sewing, "group": "finishing", "pricing": True},
        # Design
        {"key": "artwork_ready", "label": "Artwork Ready?", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "artwork_needed", "label": "Artwork Needed?", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "design_complexity", "label": "Design Complexity", "type": "select", "options": [
            {"value": "simple", "label": "Simple"},
            {"value": "medium", "label": "Medium"},
            {"value": "complex", "label": "Complex"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": default_design_complexity, "group": "design", "pricing": True},
        # Install
        {"key": "install_required", "label": "Install Required?", "type": "toggle", "default": default_install_included, "group": "install", "pricing": True},
        {"key": "install_complexity", "label": "Install Complexity", "type": "select", "options": [
            {"value": "easy", "label": "Easy"},
            {"value": "medium", "label": "Medium"},
            {"value": "difficult", "label": "Difficult"},
            {"value": "high_access", "label": "High-Access"},
        ], "default": default_install_complexity, "group": "install", "pricing": True},
        # Hardware / Production
        {"key": "banner_hardware_keys", "label": "Hardware / Accessories", "type": "multi_select", "options": banner_hardware_options, "default": [], "group": "production", "pricing": True},
        {"key": "banner_event_premium", "label": "Step-and-Repeat / Event Premium?", "type": "toggle", "default": default_event, "group": "production", "pricing": True},
        {"key": "rush_order", "label": "Rush?", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "packaging_notes", "label": "Packaging / Rolling Notes", "type": "textarea", "group": "production"},
        {"key": "delivery_notes", "label": "Pickup / Delivery Notes", "type": "textarea", "group": "production"},
    ]


def _apparel_schema(defaults, garment_opts, decoration_opts):
    """Full Apparel category schema — all options sourced from Pricing Foundation defaults."""
    cat = (defaults.get("category_defaults", {}) or {}).get("apparel", {}) or {}
    product_types = cat.get("available_product_types", []) or []
    brand_styles_map = cat.get("available_brand_styles", {}) or {}
    method_cfg = cat.get("method_config", {}) or {}
    avail_methods = cat.get("available_decoration_methods", []) or []

    product_type_options = [{"value": p["key"], "label": p["label"]} for p in product_types]
    # For initial schema we return brand options for the first product type; UI will filter by selected product type.
    default_product = cat.get("default_product_type") or (product_types[0]["key"] if product_types else "short_sleeve_tee")
    default_brand_styles = brand_styles_map.get(default_product, [])
    brand_style_options = [{"value": b["key"], "label": b["label"]} for b in default_brand_styles]

    # Placement set options (garment + hat) — UI switches based on product type
    garment_placement = [{"value": "front", "label": "Front Small"}, {"value": "back", "label": "Back Large"}, {"value": "front_back", "label": "Front + Back"}]
    hat_placement = [{"value": "front", "label": "Front Only"}, {"value": "side_back", "label": "Side / Back Only"}, {"value": "front_side_back", "label": "Front + Side/Back"}]

    decoration_method_options = [
        {"value": m, "label": (method_cfg.get(m, {}) or {}).get("label", m.replace("_", " ").title())}
        for m in avail_methods
    ]
    if not decoration_method_options:
        decoration_method_options = [
            {"value": "htv", "label": "HTV"},
            {"value": "screen_print_transfer", "label": "Screen Print Transfer"},
            {"value": "dtf_transfer", "label": "DTF Transfer"},
            {"value": "direct_screen_print", "label": "Direct Screen Print"},
            {"value": "embroidery", "label": "Embroidery"},
            {"value": "dtg", "label": "DTG"},
            {"value": "patch_emblem", "label": "Patch / Emblem"},
            {"value": "sublimation", "label": "Sublimation"},
            {"value": "specialty_custom", "label": "Specialty / Custom"},
        ]

    default_method = cat.get("default_decoration_method", "htv")
    default_complexity = cat.get("default_design_complexity", "simple")

    return [
        # Product / Brand / Color
        {"key": "apparel_product_type", "label": "Product Type", "type": "select", "options": product_type_options, "default": default_product, "group": "garment_info", "required": True, "pricing": True},
        {"key": "apparel_brand_style_key", "label": "Brand / Style", "type": "select", "options": brand_style_options, "group": "garment_info", "required": True, "pricing": True},
        {"key": "apparel_garment_color", "label": "Garment / Hat Color", "type": "text", "placeholder": "Black, White, Navy", "group": "garment_info"},
        {"key": "customer_supplied", "label": "Customer Supplied Garments", "type": "toggle", "default": False, "group": "garment_info", "pricing": True},
        # Size breakdown (existing — quantity derives from sum; plus-size count for upcharge)
        {"key": "size_xs", "label": "XS", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_s", "label": "S", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_m", "label": "M", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_l", "label": "L", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_xl", "label": "XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_2xl", "label": "2XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_3xl", "label": "3XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_4xl", "label": "4XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "size_5xl", "label": "5XL", "type": "number", "default": 0, "group": "size_breakdown", "pricing": True},
        {"key": "apparel_plus_size_count", "label": "Plus Size Count (2XL–5XL, auto)", "type": "calculated", "group": "size_breakdown", "pricing": True},
        # Placement (garment options shown by default; UI switches to hat placements when product_type is a hat)
        {"key": "apparel_placement_set", "label": "Placement Set (Garment)", "type": "select", "options": garment_placement, "default": "front", "group": "placement", "required": True, "pricing": True, "visible_when_garment": True},
        {"key": "apparel_placement_set_hat", "label": "Placement Set (Hat)", "type": "select", "options": hat_placement, "default": "front", "group": "placement", "required": True, "pricing": True, "visible_when_hat": True},
        # Decoration
        {"key": "apparel_decoration_method", "label": "Decoration Method", "type": "select", "options": decoration_method_options, "default": default_method, "group": "decoration", "required": True, "pricing": True},
        {"key": "apparel_decoration_subtype", "label": "Method Detail / Subtype", "type": "text", "placeholder": "e.g. Siser EasyWeed, Plastisol", "group": "decoration"},
        {"key": "apparel_num_colors", "label": "Number of Colors", "type": "number", "default": 1, "group": "decoration", "pricing": True},
        {"key": "apparel_stitch_count", "label": "Stitch Count (embroidery)", "type": "number", "default": 0, "group": "decoration", "pricing": True},
        # Design / Artwork
        {"key": "artwork_ready", "label": "Artwork Ready?", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "artwork_needed", "label": "Artwork Needed?", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "design_complexity", "label": "Design Complexity", "type": "select", "options": [
            {"value": "simple", "label": "Simple"},
            {"value": "medium", "label": "Medium"},
            {"value": "complex", "label": "Complex"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": default_complexity, "group": "design", "pricing": True},
        # Add-ons
        {"key": "apparel_custom_name_number", "label": "Custom Name/Number?", "type": "toggle", "default": False, "group": "addons", "pricing": True},
        {"key": "apparel_custom_name_number_count", "label": "Custom Name/Number Count", "type": "number", "default": 0, "group": "addons", "pricing": True},
        {"key": "apparel_specialty_finish", "label": "Specialty Finish / Specialty Vinyl?", "type": "toggle", "default": False, "group": "addons", "pricing": True},
        {"key": "apparel_two_tone_hat_finish", "label": "Two-Tone / Specialty Hat Finish? (hats)", "type": "toggle", "default": False, "group": "addons", "pricing": True},
        {"key": "apparel_leather_patch", "label": "Leather / Faux Patch? (hats)", "type": "toggle", "default": False, "group": "addons", "pricing": True},
        {"key": "apparel_bag_and_fold", "label": "Bag & Fold?", "type": "toggle", "default": False, "group": "addons", "pricing": True},
        # Production
        {"key": "rush_order", "label": "Rush?", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "apparel_rush_percent", "label": "Rush % (override)", "type": "number", "default": cat.get("default_rush_percent", 17.5), "group": "production", "pricing": True},
        {"key": "apparel_manual_quote_override", "label": "Manual Quote Override ($)", "type": "number", "default": 0, "group": "production", "pricing": True},
        {"key": "folding_bagging", "label": "Folding / Bagging Needed", "type": "toggle", "default": False, "group": "production"},
        {"key": "tagging_notes", "label": "Tagging / Sorting Notes", "type": "textarea", "group": "production"},
    ]


def _services_schema(defaults):
    cat = defaults.get("category_defaults", {}).get("services", {}) or {}
    service_types = cat.get("available_service_types", []) or []
    billing_units = cat.get("available_billing_units", ["hour", "flat", "piece", "sqft", "linear_foot", "mile", "trip", "day", "custom"])
    labor_roles_map = cat.get("labor_roles", {}) or {}
    equipment_library = cat.get("equipment_library", []) or []

    st_options = [{"value": s["key"], "label": s["label"]} for s in service_types]
    bu_options = [{"value": u, "label": {"hour": "Hour", "flat": "Flat Fee", "piece": "Piece", "sqft": "Sq Ft", "linear_foot": "Linear Ft", "mile": "Mile", "trip": "Trip", "day": "Day", "custom": "Custom Unit"}.get(u, u.title())} for u in billing_units]
    role_options = [{"value": k, "label": v.get("label", k)} for k, v in labor_roles_map.items()]
    equipment_options = [{"value": e["key"], "label": e["label"]} for e in equipment_library]

    complexity_opts = [
        {"value": "easy", "label": "Easy"},
        {"value": "medium", "label": "Medium"},
        {"value": "difficult", "label": "Difficult"},
        {"value": "extreme", "label": "Extreme"},
    ]

    default_st = cat.get("default_service_type", "general_labor")
    default_role = cat.get("default_labor_role", "production")
    default_bu = "hour"

    return [
        {"key": "service_type", "label": "Service Type", "type": "select", "options": st_options, "default": default_st, "group": "service_info", "required": True, "pricing": True},
        {"key": "services_billing_unit", "label": "Billing Unit", "type": "select", "options": bu_options, "default": default_bu, "group": "service_info", "required": True, "pricing": True},
        {"key": "services_labor_role", "label": "Labor Role", "type": "select", "options": role_options, "default": default_role, "group": "service_info", "pricing": True},
        {"key": "services_complexity", "label": "Complexity", "type": "select", "options": complexity_opts, "default": "medium", "group": "service_info", "pricing": True},

        {"key": "estimated_hours", "label": "Estimated Hours", "type": "number", "default": 1, "group": "labor", "pricing": True},
        {"key": "num_workers", "label": "Number of Workers", "type": "number", "default": 1, "group": "labor", "pricing": True},
        {"key": "services_flat_fee", "label": "Flat Fee ($, if billing_unit=flat)", "type": "number", "group": "labor", "pricing": True},
        {"key": "services_unit_rate_override", "label": "Unit Rate Override ($)", "type": "number", "group": "labor", "pricing": True},
        {"key": "hourly_rate_override", "label": "Hourly Rate Override ($)", "type": "number", "group": "labor", "pricing": True},

        {"key": "services_minimum_applies", "label": "Apply Minimum Charge?", "type": "toggle", "default": True, "group": "minimums", "pricing": True},
        {"key": "services_minimum_override", "label": "Minimum Charge Override ($)", "type": "number", "group": "minimums", "pricing": True},

        {"key": "services_travel_required", "label": "Travel Required?", "type": "toggle", "default": False, "group": "travel", "pricing": True},
        {"key": "services_travel_miles", "label": "Travel Miles", "type": "number", "default": 0, "group": "travel", "pricing": True},
        {"key": "services_trip_charge_applies", "label": "Trip Charge Applies?", "type": "toggle", "default": False, "group": "travel", "pricing": True},
        {"key": "services_trip_count", "label": "Trip Count", "type": "number", "default": 1, "group": "travel", "pricing": True},

        {"key": "services_equipment_required", "label": "Equipment Required?", "type": "toggle", "default": False, "group": "equipment", "pricing": True},
        {"key": "services_equipment_type", "label": "Equipment Type", "type": "select", "options": equipment_options, "group": "equipment", "pricing": True},
        {"key": "services_equipment_days", "label": "Equipment Days", "type": "number", "default": 0, "group": "equipment", "pricing": True},
        {"key": "services_equipment_hours", "label": "Equipment Hours", "type": "number", "default": 0, "group": "equipment", "pricing": True},

        {"key": "services_subcontracted", "label": "Subcontracted / Outsourced?", "type": "toggle", "default": False, "group": "subcontract", "pricing": True},
        {"key": "services_subcontract_cost", "label": "Subcontract Cost ($)", "type": "number", "default": 0, "group": "subcontract", "pricing": True},
        {"key": "services_subcontract_markup_applies", "label": "Apply Markup to Subcontract?", "type": "toggle", "default": True, "group": "subcontract", "pricing": True},

        {"key": "services_permit_external_fee", "label": "Permit / External Fee ($)", "type": "number", "default": 0, "group": "passthrough", "pricing": True},

        {"key": "rush_order", "label": "Rush?", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "services_manual_quote_override", "label": "Manual Quote Override ($)", "type": "number", "default": 0, "group": "production", "pricing": True},
        {"key": "service_notes", "label": "Service Notes", "type": "textarea", "group": "production"},
    ]


def _rigid_sign_schema(defaults, substrate_opts, finish_opts, hardware_opts):
    cat_config = defaults.get("category_defaults", {}).get("rigid_signs", {})
    return [
        {"key": "width", "label": "Width", "type": "number", "unit": "in", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "number", "unit": "in", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [
            {"value": "inches", "label": "Inches"},
            {"value": "feet", "label": "Feet"},
        ], "default": cat_config.get("default_unit_of_measure", "inches"), "pricing": True},
        {"key": "substrate_type_key", "label": "Substrate Type", "type": "select", "options": substrate_opts, "default": cat_config.get("default_substrate_key", "coroplast_4mm"), "pricing": True},
        {"key": "thickness", "label": "Thickness", "type": "select", "options": [
            {"value": "4mm", "label": "4mm"},
            {"value": "10mm", "label": "10mm"},
            {"value": "3mm", "label": "3mm"},
            {"value": "6mm", "label": "6mm"},
            {"value": "0.040", "label": ".040"},
            {"value": "0.063", "label": ".063"},
            {"value": "0.080", "label": ".080"},
            {"value": "1/8", "label": "1/8"},
            {"value": "1/4", "label": "1/4"},
            {"value": "3/16", "label": "3/16"},
            {"value": "1/2", "label": "1/2"},
            {"value": "custom", "label": "Custom"},
        ], "default": "4mm", "pricing": True},
        {"key": "graphic_method", "label": "Graphic Method", "type": "select", "options": [
            {"value": "direct_print", "label": "Direct Print"},
            {"value": "mounted_print", "label": "Mounted Print"},
            {"value": "cut_vinyl_applied", "label": "Cut Vinyl Applied"},
        ], "default": cat_config.get("default_graphic_method", "direct_print"), "pricing": True},
        {"key": "protective_finish", "label": "Protective Finish / Laminate", "type": "toggle", "default": cat_config.get("default_finish_required", False), "pricing": True},
        {"key": "protective_finish_type", "label": "Protective Finish Type", "type": "select", "options": finish_opts, "default": cat_config.get("default_finish_key", "rigid_finish_standard"), "pricing": True},
        {"key": "sidedness", "label": "Single or Double Sided", "type": "select", "options": [
            {"value": "single", "label": "Single-Sided"},
            {"value": "double", "label": "Double-Sided"},
        ], "default": cat_config.get("default_sidedness", "single"), "pricing": True},
        {"key": "double_sided_art", "label": "Double-Sided Art", "type": "select", "options": [
            {"value": "same", "label": "Same Art"},
            {"value": "different", "label": "Different Art"},
        ], "default": cat_config.get("default_double_sided_art", "same"), "pricing": True},
        {"key": "shape_type", "label": "Shape Type", "type": "select", "options": [
            {"value": "rectangle", "label": "Rectangle"},
            {"value": "rounded_corners", "label": "Rounded Corners"},
            {"value": "simple_contour", "label": "Simple Contour"},
            {"value": "complex_contour", "label": "Complex Contour"},
            {"value": "specialty_routed", "label": "Specialty Routed"},
        ], "default": cat_config.get("default_shape_type", "rectangle"), "pricing": True},
        {"key": "finish_quality", "label": "Finish Quality Tier", "type": "select", "options": [
            {"value": "standard", "label": "Standard"},
            {"value": "premium", "label": "Premium"},
            {"value": "presentation", "label": "Presentation"},
            {"value": "architectural", "label": "Architectural"},
        ], "default": cat_config.get("default_finish_quality", "standard"), "pricing": True},
        {"key": "hardware_included", "label": "Hardware Included", "type": "toggle", "default": False, "pricing": True},
        {"key": "hardware_type", "label": "Hardware Type", "type": "select", "options": hardware_opts, "pricing": True},
        {"key": "drill_prep_required", "label": "Drill / Prep Required", "type": "toggle", "default": False, "pricing": True},
        {"key": "artwork_ready", "label": "Artwork Ready", "type": "toggle", "default": False, "pricing": True},
        {"key": "artwork_needed", "label": "Artwork Needed", "type": "toggle", "default": False, "pricing": True},
        {"key": "design_complexity", "label": "Design Complexity", "type": "select", "options": [
            {"value": "simple", "label": "Simple"},
            {"value": "medium", "label": "Medium"},
            {"value": "complex", "label": "Complex"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": cat_config.get("default_design_complexity", "simple"), "pricing": True},
        {"key": "install_required", "label": "Install Required", "type": "toggle", "default": cat_config.get("default_install_included", False), "pricing": True},
        {"key": "install_complexity", "label": "Install Complexity", "type": "select", "options": [
            {"value": "easy", "label": "Easy"},
            {"value": "medium", "label": "Medium"},
            {"value": "difficult", "label": "Difficult"},
            {"value": "high_risk", "label": "High-Risk"},
        ], "default": cat_config.get("default_install_complexity", "easy"), "pricing": True},
        {"key": "rush_order", "label": "Rush", "type": "toggle", "default": False, "pricing": True},
    ]


def _cut_vinyl_schema(defaults, vinyl_opts):
    cat_config = defaults.get("category_defaults", {}).get("cut_vinyl", {})
    return [
        {"key": "width", "label": "Width", "type": "number", "unit": "in", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "number", "unit": "in", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [
            {"value": "inches", "label": "Inches"},
            {"value": "feet", "label": "Feet"},
        ], "default": cat_config.get("default_unit_of_measure", "inches"), "pricing": True},
        {"key": "vinyl_type_key", "label": "Vinyl Type", "type": "select", "options": vinyl_opts, "default": cat_config.get("default_vinyl_type_key", "oracal_651"), "pricing": True},
        {"key": "num_colors", "label": "Number of Colors", "type": "select", "options": [
            {"value": 1, "label": "1"},
            {"value": 2, "label": "2"},
            {"value": 3, "label": "3"},
            {"value": 4, "label": "4+"},
        ], "default": cat_config.get("default_number_of_colors", 1), "pricing": True},
        {"key": "weeding_complexity", "label": "Weeding Complexity", "type": "select", "options": [
            {"value": "simple", "label": "Simple"},
            {"value": "medium", "label": "Medium"},
            {"value": "complex", "label": "Complex"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": cat_config.get("default_weeding_complexity", "simple"), "pricing": True},
        {"key": "masking_required", "label": "Masking Required", "type": "toggle", "default": cat_config.get("default_masking_required", True), "pricing": True},
        {"key": "use_type", "label": "Application / Use Type", "type": "select", "options": [
            {"value": "indoor", "label": "Indoor"},
            {"value": "outdoor", "label": "Outdoor"},
            {"value": "wall", "label": "Wall"},
            {"value": "glass_window", "label": "Glass / Window"},
            {"value": "vehicle", "label": "Vehicle"},
            {"value": "specialty", "label": "Specialty"},
        ], "default": cat_config.get("default_use_type", "indoor"), "pricing": True},
        {"key": "artwork_ready", "label": "Artwork Ready", "type": "toggle", "default": False, "pricing": True},
        {"key": "artwork_needed", "label": "Artwork Needed", "type": "toggle", "default": False, "pricing": True},
        {"key": "design_complexity", "label": "Design Complexity", "type": "select", "options": [
            {"value": "simple", "label": "Simple"},
            {"value": "medium", "label": "Medium"},
            {"value": "complex", "label": "Complex"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": cat_config.get("default_design_complexity", "simple"), "pricing": True},
        {"key": "file_cleanup_needed", "label": "File Cleanup Needed", "type": "toggle", "default": False, "pricing": True},
        {"key": "install_required", "label": "Install Required", "type": "toggle", "default": cat_config.get("default_install_included", False), "pricing": True},
        {"key": "install_complexity", "label": "Install Complexity", "type": "select", "options": [
            {"value": "easy", "label": "Easy"},
            {"value": "medium", "label": "Medium"},
            {"value": "difficult", "label": "Difficult"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": cat_config.get("default_install_complexity", "easy"), "pricing": True},
        {"key": "surface_type", "label": "Surface Type", "type": "select", "options": [
            {"value": "flat_smooth", "label": "Flat Smooth"},
            {"value": "glass_window", "label": "Glass / Window"},
            {"value": "vehicle", "label": "Vehicle"},
            {"value": "textured_rough", "label": "Textured / Rough"},
            {"value": "curved_awkward", "label": "Curved / Awkward"},
        ], "default": cat_config.get("default_surface_type", "flat_smooth"), "pricing": True},
        {"key": "rush_order", "label": "Rush", "type": "toggle", "default": False, "pricing": True},
    ]


def _digital_print_schema(defaults, media_opts, laminate_opts, substrate_opts):
    cat_config = defaults.get("category_defaults", {}).get("digital_print", {})
    return [
        {"key": "width", "label": "Width", "type": "number", "unit": "in", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "number", "unit": "in", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [
            {"value": "inches", "label": "Inches"},
            {"value": "feet", "label": "Feet"},
        ], "default": cat_config.get("default_unit_of_measure", "inches"), "pricing": True},
        {"key": "print_media_key", "label": "Print Media Type", "type": "select", "options": media_opts, "default": cat_config.get("default_print_media_key", "printable_adhesive_vinyl"), "pricing": True},
        {"key": "use_type", "label": "Application / Use Type", "type": "select", "options": [
            {"value": "indoor", "label": "Indoor"},
            {"value": "outdoor", "label": "Outdoor"},
            {"value": "display", "label": "Display"},
            {"value": "floor", "label": "Floor"},
            {"value": "window", "label": "Window"},
            {"value": "wall", "label": "Wall"},
            {"value": "backlit", "label": "Backlit"},
        ], "default": cat_config.get("default_use_type", "indoor"), "pricing": True},
        {"key": "print_quality_mode", "label": "Print Quality Mode", "type": "select", "options": [
            {"value": "draft", "label": "Draft"},
            {"value": "standard", "label": "Standard"},
            {"value": "high", "label": "High"},
            {"value": "photo", "label": "Photo"},
        ], "default": cat_config.get("default_print_quality_mode", "standard"), "pricing": True},
        {"key": "ink_coverage_percent", "label": "Ink Coverage %", "type": "number", "default": cat_config.get("default_ink_coverage_percent", 35), "pricing": True},
        {"key": "laminate", "label": "Laminate Required", "type": "toggle", "default": cat_config.get("default_laminate_required", False), "pricing": True},
        {"key": "laminate_material_key", "label": "Laminate Type", "type": "select", "options": laminate_opts, "default": cat_config.get("default_laminate_key", "laminate_gloss"), "pricing": True},
        {"key": "contour_cut_type", "label": "Contour Cut Type", "type": "select", "options": [
            {"value": "none", "label": "None"},
            {"value": "simple", "label": "Simple Contour"},
            {"value": "complex", "label": "Complex Contour"},
            {"value": "kiss", "label": "Kiss Cut / Sheet Cut"},
        ], "default": cat_config.get("default_contour_cut_type", "none"), "pricing": True},
        {"key": "trim_finish_type", "label": "Trim Finish Type", "type": "select", "options": [
            {"value": "standard", "label": "Standard Trim"},
            {"value": "premium", "label": "Premium Trim"},
        ], "default": cat_config.get("default_trim_finish_type", "standard"), "pricing": True},
        {"key": "piece_separation_required", "label": "Piece Separation Required", "type": "toggle", "default": False, "pricing": True},
        {"key": "separated_piece_count", "label": "Separated Piece Count", "type": "number", "default": 0, "pricing": True},
        {"key": "artwork_ready", "label": "Artwork Ready", "type": "toggle", "default": False, "pricing": True},
        {"key": "artwork_needed", "label": "Artwork Needed", "type": "toggle", "default": False, "pricing": True},
        {"key": "design_complexity", "label": "Design Complexity", "type": "select", "options": [
            {"value": "simple", "label": "Simple"},
            {"value": "medium", "label": "Medium"},
            {"value": "complex", "label": "Complex"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": cat_config.get("default_design_complexity", "simple"), "pricing": True},
        {"key": "file_cleanup_needed", "label": "File Cleanup Needed", "type": "toggle", "default": False, "pricing": True},
        {"key": "mounted_to_substrate", "label": "Mounted to Substrate", "type": "toggle", "default": False, "pricing": True},
        {"key": "substrate_material_key", "label": "Substrate Type", "type": "select", "options": substrate_opts, "pricing": True},
        {"key": "install_required", "label": "Install Required", "type": "toggle", "default": cat_config.get("default_install_included", False), "pricing": True},
        {"key": "install_complexity", "label": "Install Complexity", "type": "select", "options": [
            {"value": "easy", "label": "Easy"},
            {"value": "medium", "label": "Medium"},
            {"value": "difficult", "label": "Difficult"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": cat_config.get("default_install_complexity", "easy"), "pricing": True},
        {"key": "rush_order", "label": "Rush", "type": "toggle", "default": False, "pricing": True},
    ]


def _vehicle_wrap_schema(defaults, vinyl_opts, vehicle_type_opts):
    """Full Vehicle Graphics / Wraps category schema — all options sourced from Pricing Foundation defaults."""
    cat = (defaults.get("category_defaults", {}) or {}).get("vehicle_wraps", {}) or {}
    materials = defaults.get("materials", []) or []

    # Build foundation-backed vehicle type options
    available_vehicle_keys = cat.get("available_vehicle_type_keys") or []
    vehicle_options = []
    vehicle_lookup = {m.get("key") or m.get("id"): m for m in materials if m.get("category") == "vehicle_type"}
    for vk in available_vehicle_keys:
        m = vehicle_lookup.get(vk)
        if m:
            vehicle_options.append({"value": m.get("key") or m.get("id"), "label": m.get("name") or vk})
    if not vehicle_options:
        vehicle_options = vehicle_type_opts or [
            {"value": "car_sedan", "label": "Sedan"},
            {"value": "car_suv", "label": "SUV"},
            {"value": "pickup", "label": "Pickup"},
            {"value": "van_mini", "label": "Mini Van"},
            {"value": "van_cargo", "label": "Cargo Van"},
            {"value": "van_sprinter", "label": "Sprinter Van"},
            {"value": "box_truck_12ft", "label": "12 ft Box Truck"},
            {"value": "box_truck_16ft", "label": "16 ft Box Truck"},
            {"value": "box_truck_24ft", "label": "24 ft Box Truck"},
            {"value": "trailer", "label": "Trailer"},
            {"value": "semi", "label": "Semi"},
            {"value": "other", "label": "Custom / Other"},
        ]

    # Wrap material options from Foundation
    available_wrap_keys = cat.get("available_wrap_material_keys") or []
    def _material_by_key(k):
        return next((m for m in materials if (m.get("key") == k or m.get("id") == k) and m.get("is_active", True)), None)
    wrap_material_options = []
    for k in available_wrap_keys:
        m = _material_by_key(k)
        if m:
            wrap_material_options.append({"value": m.get("key") or m.get("id"), "label": m.get("name") or k})
    if not wrap_material_options:
        wrap_material_options = [
            {"value": "wrap_standard_calendared", "label": "Standard Calendared Vinyl"},
            {"value": "wrap_premium_cast", "label": "Premium Cast Vinyl"},
            {"value": "wrap_cast_film", "label": "Wrap Cast Film"},
            {"value": "wrap_reflective", "label": "Reflective Vinyl"},
            {"value": "wrap_etched_frost", "label": "Etched / Frost Film"},
            {"value": "wrap_specialty_media", "label": "Specialty / Custom Vehicle Media"},
        ]

    # Laminate options from Foundation (vehicle_wrap_laminate)
    available_lam_keys = cat.get("available_wrap_laminate_keys") or []
    laminate_options = []
    for k in available_lam_keys:
        m = _material_by_key(k)
        if m:
            laminate_options.append({"value": m.get("key") or m.get("id"), "label": m.get("name") or k})
    if not laminate_options:
        laminate_options = [
            {"value": "wrap_laminate_gloss", "label": "Gloss Wrap Laminate"},
            {"value": "wrap_laminate_matte", "label": "Matte Wrap Laminate"},
            {"value": "wrap_laminate_satin", "label": "Satin Wrap Laminate"},
        ]

    coverage_opts = [
        {"value": "spot", "label": "Spot Graphics"},
        {"value": "partial", "label": "Partial Wrap"},
        {"value": "half", "label": "Half Wrap"},
        {"value": "full", "label": "Full Wrap"},
        {"value": "custom", "label": "Custom %"},
    ]

    default_vehicle = vehicle_options[0]["value"] if vehicle_options else "van_cargo"
    default_coverage = cat.get("default_coverage_type", "spot")
    default_material = cat.get("default_wrap_material_key", "wrap_standard_calendared")
    default_laminate_required = bool(cat.get("default_laminate_required_for_prints", True))
    default_laminate_key = cat.get("default_wrap_laminate_key", "wrap_laminate_gloss")
    default_install_difficulty = cat.get("default_install_difficulty", "medium")
    default_seam = cat.get("default_seam_complexity", "basic")
    default_surface_prep = cat.get("default_surface_prep", "none")
    default_removal = cat.get("default_removal_scope", "none")
    default_design_complexity = cat.get("default_design_complexity", "medium")
    default_second_installer = bool(cat.get("default_second_installer_required", False))
    default_perf_included = bool(cat.get("default_window_perf_included", False))
    default_perf_scope = cat.get("default_window_perf_scope", "rear")
    default_install_required = bool(cat.get("default_install_required", True))

    return [
        # Vehicle Info
        {"key": "vehicle_type", "label": "Vehicle Type", "type": "select", "options": vehicle_options, "default": default_vehicle, "group": "vehicle_info", "required": True, "pricing": True},
        {"key": "vehicle_year", "label": "Year", "type": "text", "placeholder": "2024", "group": "vehicle_info"},
        {"key": "vehicle_make", "label": "Make", "type": "text", "placeholder": "Ford, Chevy, Ram", "group": "vehicle_info"},
        {"key": "vehicle_model", "label": "Model", "type": "text", "placeholder": "Transit, Silverado", "group": "vehicle_info"},
        # Coverage
        {"key": "coverage_type", "label": "Coverage Type", "type": "select", "options": coverage_opts, "default": default_coverage, "group": "coverage", "required": True, "pricing": True},
        {"key": "custom_coverage_percent", "label": "Custom Coverage % (if custom)", "type": "number", "placeholder": "e.g. 65", "group": "coverage", "pricing": True},
        {"key": "estimated_vehicle_sqft", "label": "Override Estimated Sq Ft", "type": "number", "placeholder": "Auto from vehicle type", "group": "coverage", "pricing": True},
        # Material
        {"key": "wrap_material_key", "label": "Wrap Material", "type": "select", "options": wrap_material_options, "default": default_material, "group": "material", "required": True, "pricing": True},
        {"key": "wrap_laminate_required", "label": "Laminate Required?", "type": "toggle", "default": default_laminate_required, "group": "material", "pricing": True},
        {"key": "wrap_laminate_type_key", "label": "Laminate Type", "type": "select", "options": laminate_options, "default": default_laminate_key, "group": "material", "pricing": True},
        # Window Perf
        {"key": "window_perf_included", "label": "Window Perf Included?", "type": "toggle", "default": default_perf_included, "group": "window_perf", "pricing": True},
        {"key": "window_perf_scope", "label": "Window Perf Scope", "type": "select", "options": [
            {"value": "rear", "label": "Rear Only"},
            {"value": "side", "label": "Side Windows"},
            {"value": "full", "label": "Full Window Package"},
        ], "default": default_perf_scope, "group": "window_perf", "pricing": True},
        # Design
        {"key": "artwork_ready", "label": "Artwork Ready?", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "artwork_needed", "label": "Artwork Needed?", "type": "toggle", "default": True, "group": "design", "pricing": True},
        {"key": "design_complexity", "label": "Design Complexity", "type": "select", "options": [
            {"value": "simple", "label": "Simple"},
            {"value": "medium", "label": "Medium"},
            {"value": "complex", "label": "Complex"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": default_design_complexity, "group": "design", "pricing": True},
        # Prep / Removal
        {"key": "surface_prep_level", "label": "Surface Prep Required", "type": "select", "options": [
            {"value": "none", "label": "None"},
            {"value": "basic", "label": "Basic"},
            {"value": "moderate", "label": "Moderate"},
            {"value": "heavy", "label": "Heavy"},
        ], "default": default_surface_prep, "group": "prep_removal", "pricing": True},
        {"key": "removal_scope", "label": "Removal Required", "type": "select", "options": [
            {"value": "none", "label": "None"},
            {"value": "small", "label": "Small"},
            {"value": "partial", "label": "Partial"},
            {"value": "full", "label": "Full"},
        ], "default": default_removal, "group": "prep_removal", "pricing": True},
        # Install
        {"key": "install_required", "label": "Install Required?", "type": "toggle", "default": default_install_required, "group": "install", "pricing": True},
        {"key": "install_difficulty_level", "label": "Install Difficulty", "type": "select", "options": [
            {"value": "easy", "label": "Easy"},
            {"value": "medium", "label": "Medium"},
            {"value": "difficult", "label": "Difficult"},
            {"value": "extreme", "label": "Extreme"},
        ], "default": default_install_difficulty, "group": "install", "pricing": True},
        {"key": "seam_complexity", "label": "Panel / Seam Alignment", "type": "select", "options": [
            {"value": "basic", "label": "Basic"},
            {"value": "moderate", "label": "Moderate"},
            {"value": "advanced", "label": "Advanced"},
        ], "default": default_seam, "group": "install", "pricing": True},
        {"key": "second_installer_required", "label": "Second Installer?", "type": "toggle", "default": default_second_installer, "group": "install", "pricing": True},
        # Production
        {"key": "rush_order", "label": "Rush?", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "vehicle_notes", "label": "Existing Damage / Notes", "type": "textarea", "group": "production"},
    ]



# ===== Progressive disclosure rules =====
# Marks which field keys are "core" (always visible after category selected) and
# applies visible_when rules so follow-up fields only render when their trigger is met.
_CORE_BY_CATEGORY = {
    "banners": {"width", "height", "unit_of_measure", "banner_material_key", "print_sides", "artwork_ready", "artwork_needed"},
    "apparel": {"apparel_product_type", "apparel_brand_style_key", "apparel_garment_color", "apparel_decoration_method", "apparel_placement_set", "apparel_placement_set_hat", "artwork_ready", "artwork_needed"},
    "rigid_signs": {"width", "height", "unit_of_measure", "substrate_material_key", "print_method", "double_sided", "artwork_ready", "artwork_needed"},
    "cut_vinyl": {"width", "height", "unit_of_measure", "vinyl_type_key", "num_colors", "surface_type", "artwork_ready", "artwork_needed"},
    "vehicle_wrap": {"vehicle_type", "coverage_type", "wrap_material_key", "artwork_ready", "artwork_needed"},
    "digital_print": {"width", "height", "unit_of_measure", "print_media_key", "use_type", "print_quality_mode", "artwork_ready", "artwork_needed"},
    "services": {"service_type", "services_billing_unit", "services_labor_role", "estimated_hours", "services_flat_fee"},
}

_VISIBLE_WHEN_RULES = {
    "banners": {
        "banner_grommet_count": {"banner_grommets": "custom"},
        "install_complexity": {"install_required": True},
        "design_complexity": {"artwork_needed": True},
    },
    "apparel": {
        "apparel_custom_name_number_count": {"apparel_custom_name_number": True},
        "apparel_two_tone_hat_finish": {"apparel_product_type": {"in": ["hat_standard", "hat_premium", "visor"]}},
        "apparel_leather_patch": {"apparel_product_type": {"in": ["hat_standard", "hat_premium", "visor"]}},
        "apparel_stitch_count": {"apparel_decoration_method": "embroidery"},
        "size_xs": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_s": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_m": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_l": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_xl": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_2xl": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_3xl": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_4xl": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "size_5xl": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "apparel_plus_size_count": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "apparel_placement_set": {"apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}},
        "apparel_placement_set_hat": {"apparel_product_type": {"in": ["hat_standard", "hat_premium", "visor"]}},
        "design_complexity": {"artwork_needed": True},
        "apparel_rush_percent": {"rush_order": True},
    },
    "services": {
        "services_flat_fee": {"services_billing_unit": "flat"},
        "services_unit_rate_override": {"services_billing_unit": {"in": ["piece", "sqft", "linear_foot", "mile", "trip", "day", "custom"]}},
        "estimated_hours": {"services_billing_unit": {"in": ["hour", "flat", "piece", "sqft", "linear_foot", "custom"]}},
        "services_travel_miles": {"services_travel_required": True},
        "services_trip_charge_applies": {"services_travel_required": True},
        "services_trip_count": {"services_trip_charge_applies": True},
        "services_equipment_type": {"services_equipment_required": True},
        "services_equipment_days": {"services_equipment_required": True},
        "services_equipment_hours": {"services_equipment_required": True},
        "services_subcontract_cost": {"services_subcontracted": True},
        "services_subcontract_markup_applies": {"services_subcontracted": True},
    },
    "vehicle_wrap": {
        "custom_coverage_percent": {"coverage_type": "custom"},
        "wrap_laminate_type_key": {"wrap_laminate_required": True},
        "window_perf_scope": {"window_perf_included": True},
        "design_complexity": {"artwork_needed": True},
        "install_difficulty_level": {"install_required": True},
        "seam_complexity": {"install_required": True},
        "second_installer_required": {"install_required": True},
    },
    "digital_print": {
        "laminate_material_key": {"laminate": True},
        "design_complexity": {"artwork_needed": True},
    },
    "rigid_signs": {
        "design_complexity": {"artwork_needed": True},
        "install_complexity": {"install_required": True},
        "hardware_type": {"hardware_included": True},
        "drill_prep_required": {"hardware_included": True},
        "double_sided_art": {"sidedness": "double"},
        "protective_finish_type": {"protective_finish": True},
    },
    "cut_vinyl": {
        "design_complexity": {"artwork_needed": True},
        "install_complexity": {"install_required": True},
    },
}


def _apply_progressive_disclosure(category: str, fields):
    """Tag each field with `core` and `visible_when` based on category rules."""
    core_keys = _CORE_BY_CATEGORY.get(category, set())
    rules = _VISIBLE_WHEN_RULES.get(category, {})
    out = []
    for f in fields:
        # clone-safe shallow copy
        nf = dict(f)
        nf["core"] = nf.get("core") or (f.get("key") in core_keys)
        if f.get("key") in rules:
            nf["visible_when"] = rules[f["key"]]
            nf["depends_on"] = list(rules[f["key"]].keys()) if isinstance(rules[f["key"]], dict) else []
        # default group if missing
        if "group" not in nf:
            nf["group"] = "production"
        out.append(nf)
    return out


@router.get("/schema/{category}")
async def get_category_field_schema(category: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Return dynamic field schema for a job ticket category.
    All options pulled from pricing settings + materials catalog — nothing hardcoded."""
    from server import get_pricing_defaults
    from models.enums import PromoProductType

    defaults = await get_pricing_defaults(current_user.tenant_id)
    settings_category = _settings_category_key(category)
    cat_config = defaults.get("category_defaults", {}).get(settings_category, {})
    materials_catalog = _build_materials_catalog(defaults)

    def cat_opts(catalog_key):
        return [{"value": m["id"], "label": m["name"]} for m in materials_catalog.get(catalog_key, [])]

    # Base fields
    base = [
        {"key": "width", "label": "Width", "type": "text", "placeholder": "e.g. 8ft or 96in", "group": "dimensions"},
        {"key": "height", "label": "Height", "type": "text", "placeholder": "e.g. 3ft or 36in", "group": "dimensions"},
    ]

    schemas = {
        "banners": _banner_schema(defaults, cat_opts("print_material")),
        "apparel": _apparel_schema(defaults, cat_opts("apparel"), cat_opts("decoration")),
        "rigid_signs": _rigid_sign_schema(defaults, cat_opts("substrate"), cat_opts("finish"), cat_opts("hardware")),
        "cut_vinyl": _cut_vinyl_schema(defaults, cat_opts("vinyl")),
        "vehicle_wrap": _vehicle_wrap_schema(defaults, cat_opts("vinyl"), cat_opts("vehicle_type")),
        "digital_print": _digital_print_schema(defaults, cat_opts("print_material"), cat_opts("laminate"), cat_opts("substrate")),
        "services": _services_schema(defaults),
        "promo_misc": [
            {"key": "material", "label": "Product Type", "type": "select", "options": [{"value": m.value, "label": m.value.replace("_"," ").title()} for m in PromoProductType], "group": "material"},
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
            {"key": "install_required", "label": "Install Required", "type": "toggle", "group": "specs"},
            {"key": "double_sided", "label": "Double Sided", "type": "toggle", "group": "specs"},
        ],
    }

    fields = schemas.get(category, schemas["custom"])
    fields = _apply_progressive_disclosure(category, fields)

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
        "digital_print": [
            {"value": "poster", "label": "Poster / Paper Print"},
            {"value": "photo", "label": "Photo Print"},
            {"value": "sticker_sheet", "label": "Sticker / Label Sheet"},
            {"value": "window_perf", "label": "Window Perf"},
            {"value": "wall_graphic", "label": "Wall Graphic"},
            {"value": "floor_graphic", "label": "Floor Graphic"},
            {"value": "backlit", "label": "Backlit Film"},
            {"value": "static_cling", "label": "Static Cling"},
            {"value": "decal_sheet", "label": "Decal Sheet (Printed)"},
            {"value": "mounted", "label": "Mounted Print"},
            {"value": "laminated", "label": "Laminated Print"},
            {"value": "custom", "label": "Custom Digital Print"},
        ],
    }

    return {
        "category": category,
        "subtypes": subtypes.get(category, []),
        "fields": fields,
        "materials_catalog": materials_catalog,
        "pricing_config": {
            "minimum_charge": cat_config.get("minimum_charge", defaults.get("minimum_order", 0)),
            "default_markup": cat_config.get("default_markup_multiplier", defaults.get("default_markup_multiplier", 2.5)),
            "target_margin": cat_config.get("target_profit_margin_percent", defaults.get("target_profit_margin_percent", 40)),
            "labor_rate": defaults.get("production_hourly_rate", 28),
            "design_rate": defaults.get("design_hourly_rate", 85),
            "install_rate": defaults.get("installer_hourly_rate", 40),
            "overhead_pct": defaults.get("overhead_percentage", 15),
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

    normalized_quantity = _derive_ticket_quantity(data.item_category, data.quantity, data.specs or {})
    specs = JobTicketSpecs(**(data.specs or {}))
    ticket = JobTicket(
        tenant_id=current_user.tenant_id,
        order_id=data.order_id,
        item_name=data.item_name,
        item_category=data.item_category,
        item_subcategory=data.item_subcategory,
        quantity=normalized_quantity,
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

    # Auto-generate item_name if not provided
    if not ticket.item_name or ticket.item_name.strip() == '':
        order_full = await db.orders.find_one(
            {"id": data.order_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "customer_id": 1}
        )
        customer = None
        if order_full and order_full.get("customer_id"):
            customer = await db.customers.find_one(
                {"id": order_full["customer_id"], "tenant_id": current_user.tenant_id},
                {"_id": 0, "display_name": 1, "company": 1, "name": 1}
            )
        display = (customer or {}).get("display_name") or (customer or {}).get("company") or (customer or {}).get("name") or "item"
        display_clean = display.replace(" ", "").lower()
        cat_label = (ticket.item_category or "item").replace("_", "").lower()
        today = datetime.now(timezone.utc).strftime("%m%d%y")
        ticket.item_name = f"{display_clean}-{cat_label}-{today}"

    doc = ticket.model_dump()
    if doc.get("estimated_price", 0) <= 0:
        snapshot = await _calculate_ticket_snapshot(doc, current_user.tenant_id)
        if snapshot:
            doc.update(snapshot)
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

    next_category = update_data.get("item_category", existing.get("item_category"))
    next_specs = update_data.get("specs", existing.get("specs", {}))
    next_quantity = _derive_ticket_quantity(next_category, update_data.get("quantity", existing.get("quantity", 1)), next_specs)
    update_data["quantity"] = next_quantity

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

    pricing_mode = (existing.get("pricing_snapshot") or {}).get("pricing_mode")
    should_refresh_pricing = any(field in update_data for field in {"specs", "item_category", "quantity"}) and pricing_mode != "manual"
    if should_refresh_pricing:
        merged = {**existing, **update_data}
        if update_data.get("estimated_price", merged.get("estimated_price", 0)) <= 0 or pricing_mode != "manual":
            snapshot = await _calculate_ticket_snapshot(merged, current_user.tenant_id)
            if snapshot:
                update_data.update(snapshot)

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


@router.post("/{ticket_id}/clone")
async def clone_job_ticket(ticket_id: str, payload: Dict[str, Any], current_user: UserInDB = Depends(get_current_active_user)):
    """Clone a job ticket with one of three modes: duplicate | variation | copy_to_category.

    Request body:
      {
        "mode": "duplicate" | "variation" | "copy_to_category",
        "target_category": "rigid_signs",  # only for copy_to_category
        "carry_over": { "artwork": true, "artwork_notes": true, ... }
      }
    """
    import uuid as uuid_mod
    from models.pricing import remap_specs_for_category

    mode = (payload.get("mode") or "duplicate").lower()
    target_category = payload.get("target_category")
    carry_over = payload.get("carry_over") or {}

    existing = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Order Item not found")

    source_category = existing.get("item_category") or "custom"
    final_category = target_category if mode == "copy_to_category" and target_category else source_category

    new_id = str(uuid_mod.uuid4())
    new_number = await _next_ticket_number(existing["order_id"], current_user.tenant_id)
    now = datetime.now(timezone.utc).isoformat()

    # Remap specs using the matrix
    source_specs = dict(existing.get("specs") or {})
    new_specs = remap_specs_for_category(source_category, final_category, source_specs, carry_over)

    # Start from blank template, merge carry-over scalar fields
    new_item: Dict[str, Any] = {
        "id": new_id,
        "ticket_number": new_number,
        "order_id": existing["order_id"],
        "tenant_id": current_user.tenant_id,
        "item_name": ("Copy of " if mode == "duplicate" else ("Variant — " if mode == "variation" else "Converted — ")) + (existing.get("item_name") or "Item"),
        "item_category": final_category,
        "item_subcategory": existing.get("item_subcategory", "") if source_category == final_category else "",
        "quantity": existing.get("quantity", 1) if carry_over.get("quantity", False) else 1,
        "unit_type": existing.get("unit_type", "each"),
        "due_date": existing.get("due_date") if carry_over.get("due_date", True) else None,
        "priority": existing.get("priority", "normal"),
        "department_route": "",
        "assigned_team": "",
        "assigned_user_id": "",
        "status": "new",
        "production_flow_enabled": False,
        "specs": new_specs,
        "design_needed": False,
        "customer_artwork": False,
        "artwork_status": "none",
        "proof_required": False,
        "proof_approval_status": "none",
        "revision_count": 0,
        "special_instructions": existing.get("special_instructions", "") if carry_over.get("production_notes", True) else "",
        "production_notes": existing.get("production_notes", "") if carry_over.get("production_notes", True) else "",
        "install_notes": existing.get("install_notes", "") if carry_over.get("install_location_notes", True) else "",
        "packaging_notes": "",
        "artwork_files": [],
        "reference_images": [],
        "mockups": [],
        "proof_files": [],
        "production_output_files": [],
        "linked_pricing_profile": existing.get("linked_pricing_profile", ""),
        "estimated_price": 0.0,
        "actual_cost": 0.0,
        "labor_estimate": 0.0,
        "material_estimate": 0.0,
        "started_date": None,
        "finished_date": None,
        "ready_for_qc": False,
        "qc_status": "none",
        "ready_for_pickup": False,
        "rework_needed": False,
        "rework_notes": "",
        "progress": 0.0,
        # Intake extensions
        "entry_mode": "detailed" if mode in ("variation", "copy_to_category") else existing.get("entry_mode", "quick"),
        "description": existing.get("description", "") if carry_over.get("production_notes", True) else "",
        "manual_quote_override": None,
        "pricing_snapshot": None,
        "linked_order_file_ids": list(existing.get("linked_order_file_ids") or []) if carry_over.get("artwork", True) else [],
        "item_artwork_file_ids": list(existing.get("item_artwork_file_ids") or []) if carry_over.get("artwork", True) else [],
        "artwork_use_mode": existing.get("artwork_use_mode", "shared_only"),
        # Clone lineage
        "source_item_id": ticket_id,
        "clone_mode": mode,
        "converted_from_category": source_category if mode == "copy_to_category" else None,
        "created_at": now,
        "updated_at": now,
    }

    await db.job_tickets.insert_one(new_item)
    # Reverse-link shared files → new item
    if new_item["linked_order_file_ids"]:
        await db.order_files.update_many(
            {"id": {"$in": new_item["linked_order_file_ids"]}, "order_id": existing["order_id"]},
            {"$addToSet": {"linked_item_ids": new_id}},
        )
    await update_order_progress(db, existing["order_id"])
    await log_activity(db, existing["order_id"], current_user.tenant_id, "job_ticket", new_id,
                       "cloned", f"{mode.replace('_', ' ').title()} of {existing.get('ticket_number', '')}",
                       user_id=current_user.id, user_name=current_user.full_name or "")

    new_item.pop("_id", None)
    return new_item


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
async def calculate_ticket_pricing(ticket_id: str, pricing_input: Optional[dict] = None, current_user: UserInDB = Depends(get_current_active_user)):
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

    pricing_cat, merged_input = _build_ticket_pricing_payload(ticket, pricing_input or {})

    try:
        category_enum = PricingCategory(pricing_cat)
        pricing_data = JobItemPricingData(**merged_input)
        quantity = _derive_ticket_quantity(ticket.get("item_category", "custom"), ticket.get("quantity", 1), ticket.get("specs", {}))

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
