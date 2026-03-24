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


def _rigid_sign_schema(defaults, substrate_opts):
    """Full Rigid Sign category schema."""
    thickness_opts = [
        {"value": "4mm", "label": "4mm"}, {"value": "6mm", "label": "6mm"},
        {"value": "10mm", "label": "10mm"}, {"value": "0.040", "label": "0.040\""},
        {"value": "0.063", "label": "0.063\""}, {"value": "0.080", "label": "0.080\""},
        {"value": "3mm_pvc", "label": "3mm PVC"}, {"value": "6mm_pvc", "label": "6mm PVC"},
    ]
    return [
        # Size & Material
        {"key": "width", "label": "Width", "type": "text", "placeholder": "e.g. 18 or 24", "group": "size_material", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "text", "placeholder": "e.g. 24 or 36", "group": "size_material", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [{"value": "inches", "label": "Inches"}, {"value": "feet", "label": "Feet"}], "default": "inches", "group": "size_material", "required": True, "pricing": True},
        {"key": "sq_footage", "label": "Square Footage", "type": "calculated", "group": "size_material", "pricing": True},
        {"key": "substrate", "label": "Board Material", "type": "select", "options": substrate_opts, "group": "size_material", "required": True, "pricing": True},
        {"key": "thickness", "label": "Thickness", "type": "select", "options": thickness_opts, "group": "size_material", "pricing": True},
        {"key": "double_sided", "label": "Sidedness", "type": "select", "options": [{"value": "single", "label": "Single-Sided"}, {"value": "double", "label": "Double-Sided"}], "default": "single", "group": "size_material", "pricing": True},
        # Finishing & Fabrication
        {"key": "lamination", "label": "Lamination", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "gloss", "label": "Gloss"}, {"value": "matte", "label": "Matte"}], "default": "none", "group": "finishing", "pricing": True},
        {"key": "rounded_corners", "label": "Rounded Corners", "type": "toggle", "default": False, "group": "finishing", "pricing": True},
        {"key": "drill_holes", "label": "Drill Holes", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "corners", "label": "Corner Holes"}, {"value": "custom", "label": "Custom Pattern"}], "default": "none", "group": "finishing", "pricing": True},
        {"key": "cut_shape", "label": "Cut Shape", "type": "select", "options": [{"value": "square", "label": "Square / Rectangle"}, {"value": "contour", "label": "Contour Cut"}, {"value": "custom", "label": "Custom Shape"}], "default": "square", "group": "finishing", "pricing": True},
        {"key": "edge_finishing", "label": "Edge Finishing", "type": "text", "placeholder": "Sanded, polished, raw", "group": "finishing"},
        # Mounting / Hardware
        {"key": "stakes_included", "label": "Stakes Included", "type": "toggle", "default": False, "group": "mounting", "pricing": True},
        {"key": "num_stakes", "label": "Number of Stakes", "type": "number", "default": 0, "group": "mounting", "pricing": True},
        {"key": "mounting_hardware", "label": "Mounting Hardware", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "screws", "label": "Screws"}, {"value": "brackets", "label": "Brackets"}, {"value": "posts", "label": "Posts"}, {"value": "standoffs", "label": "Standoffs"}], "default": "none", "group": "mounting", "pricing": True},
        {"key": "install_required", "label": "Installation Required", "type": "toggle", "default": False, "group": "mounting", "pricing": True},
        # Design
        {"key": "artwork_provided", "label": "Artwork Provided", "type": "toggle", "default": False, "group": "design"},
        {"key": "design_needed", "label": "Design Needed", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "proof_required", "label": "Proof Required", "type": "toggle", "default": True, "group": "design"},
        {"key": "artwork_notes", "label": "Notes", "type": "textarea", "group": "design"},
        # Production
        {"key": "rush_order", "label": "Rush Order", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "outsourced", "label": "Outsourced", "type": "toggle", "default": False, "group": "production"},
    ]


def _cut_vinyl_schema(defaults, vinyl_opts):
    """Full Cut Vinyl category schema."""
    return [
        # Size & Layout
        {"key": "width", "label": "Width", "type": "text", "placeholder": "e.g. 24 or 36", "group": "size_layout", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "text", "placeholder": "e.g. 36 or 48", "group": "size_layout", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [{"value": "inches", "label": "Inches"}, {"value": "feet", "label": "Feet"}], "default": "inches", "group": "size_layout", "pricing": True},
        {"key": "sq_footage", "label": "Coverage Area", "type": "calculated", "group": "size_layout", "pricing": True},
        {"key": "num_pieces", "label": "Number of Separate Pieces", "type": "number", "placeholder": "1", "group": "size_layout", "pricing": True},
        # Vinyl Details
        {"key": "vinyl_type", "label": "Vinyl Type", "type": "select", "options": vinyl_opts, "group": "vinyl_details", "required": True, "pricing": True},
        {"key": "color_specs", "label": "Color(s)", "type": "text", "placeholder": "Red, White, Blue", "group": "vinyl_details"},
        {"key": "num_colors", "label": "Number of Colors", "type": "number", "default": 1, "group": "vinyl_details", "pricing": True},
        {"key": "layered", "label": "Layered or Single Color", "type": "select", "options": [{"value": "single", "label": "Single Color"}, {"value": "layered", "label": "Layered / Multi-Color"}], "default": "single", "group": "vinyl_details", "pricing": True},
        {"key": "finish", "label": "Finish", "type": "select", "options": [{"value": "gloss", "label": "Gloss"}, {"value": "matte", "label": "Matte"}, {"value": "satin", "label": "Satin"}], "default": "gloss", "group": "vinyl_details"},
        # Production Options
        {"key": "weed_required", "label": "Weed Required", "type": "toggle", "default": True, "group": "vinyl_production", "pricing": True},
        {"key": "mask_required", "label": "Mask / Transfer Tape Required", "type": "toggle", "default": True, "group": "vinyl_production", "pricing": True},
        {"key": "transfer_tape_type", "label": "Transfer Tape Type", "type": "text", "placeholder": "Standard, high-tack", "group": "vinyl_production"},
        {"key": "reverse_cut", "label": "Reverse Cut", "type": "toggle", "default": False, "group": "vinyl_production"},
        {"key": "mount_type", "label": "Inside / Outside Mount", "type": "select", "options": [{"value": "outside", "label": "Outside Mount"}, {"value": "inside", "label": "Inside Mount"}, {"value": "na", "label": "N/A"}], "default": "outside", "group": "vinyl_production"},
        # Installation
        {"key": "install_required", "label": "Install Required", "type": "toggle", "default": False, "group": "installation", "pricing": True},
        {"key": "surface_type", "label": "Surface Type", "type": "text", "placeholder": "Glass, wall, vehicle", "group": "installation"},
        {"key": "location_notes", "label": "Location / Install Notes", "type": "textarea", "group": "installation"},
        # Design
        {"key": "artwork_provided", "label": "Artwork Provided", "type": "toggle", "default": False, "group": "design"},
        {"key": "design_needed", "label": "Design Needed", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "proof_required", "label": "Proof Required", "type": "toggle", "default": True, "group": "design"},
        # Production
        {"key": "rush_order", "label": "Rush Order", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "outsourced", "label": "Outsourced", "type": "toggle", "default": False, "group": "production"},
    ]


def _digital_print_schema(defaults):
    """Full Digital Print category schema."""
    media_opts = [
        {"value": "gloss_paper", "label": "Gloss Paper"},
        {"value": "matte_paper", "label": "Matte Paper"},
        {"value": "vinyl_adhesive", "label": "Vinyl (Printable Adhesive)"},
        {"value": "window_perf", "label": "Window Perf"},
        {"value": "backlit_film", "label": "Backlit Film"},
        {"value": "static_cling", "label": "Static Cling"},
        {"value": "canvas", "label": "Canvas"},
        {"value": "fabric", "label": "Fabric / Textile"},
        {"value": "floor_graphic", "label": "Floor Graphic Media"},
        {"value": "custom", "label": "Other / Custom"},
    ]
    return [
        # Size & Media
        {"key": "width", "label": "Width", "type": "text", "placeholder": "e.g. 24 or 48", "group": "size_media", "required": True, "pricing": True},
        {"key": "height", "label": "Height", "type": "text", "placeholder": "e.g. 36 or 96", "group": "size_media", "required": True, "pricing": True},
        {"key": "unit_of_measure", "label": "Unit of Measure", "type": "select", "options": [{"value": "inches", "label": "Inches"}, {"value": "feet", "label": "Feet"}], "default": "inches", "group": "size_media", "pricing": True},
        {"key": "sq_footage", "label": "Square Footage", "type": "calculated", "group": "size_media", "pricing": True},
        {"key": "media_type", "label": "Media Type", "type": "select", "options": media_opts, "group": "size_media", "required": True, "pricing": True},
        {"key": "roll_or_sheet", "label": "Roll vs Sheet", "type": "select", "options": [{"value": "roll", "label": "Roll"}, {"value": "sheet", "label": "Sheet"}], "default": "roll", "group": "size_media", "pricing": True},
        {"key": "num_copies", "label": "Number of Copies / Sets", "type": "number", "placeholder": "1", "group": "size_media"},
        # Print Options
        {"key": "print_quality", "label": "Print Quality", "type": "select", "options": [{"value": "draft", "label": "Draft"}, {"value": "standard", "label": "Standard"}, {"value": "high", "label": "High Quality"}], "default": "standard", "group": "print_options", "pricing": True},
        {"key": "bleed_required", "label": "Bleed Required", "type": "toggle", "default": True, "group": "print_options"},
        # Finishing
        {"key": "lamination", "label": "Lamination", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "gloss", "label": "Gloss"}, {"value": "matte", "label": "Matte"}, {"value": "dry_erase", "label": "Dry Erase"}, {"value": "anti_slip", "label": "Anti-Slip (Floor)"}], "default": "none", "group": "finishing", "pricing": True},
        {"key": "mounting", "label": "Mounting", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "foam_board", "label": "Foam Board"}, {"value": "pvc", "label": "PVC"}, {"value": "acm", "label": "ACM"}], "default": "none", "group": "finishing", "pricing": True},
        {"key": "contour_cut", "label": "Contour Cut", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "simple", "label": "Simple Cut"}, {"value": "complex", "label": "Complex / Detailed"}], "default": "none", "group": "finishing", "pricing": True},
        {"key": "trim", "label": "Trim", "type": "select", "options": [{"value": "none", "label": "None"}, {"value": "standard", "label": "Standard Trim"}, {"value": "custom", "label": "Custom Trim"}], "default": "standard", "group": "finishing"},
        {"key": "corner_rounding", "label": "Corner Rounding", "type": "toggle", "default": False, "group": "finishing", "pricing": True},
        # Installation
        {"key": "install_required", "label": "Install Required", "type": "toggle", "default": False, "group": "installation", "pricing": True},
        {"key": "surface_type", "label": "Surface Type", "type": "select", "options": [{"value": "glass", "label": "Glass"}, {"value": "wall", "label": "Wall"}, {"value": "floor", "label": "Floor"}, {"value": "vehicle", "label": "Vehicle"}, {"value": "other", "label": "Other"}], "group": "installation"},
        {"key": "interior_exterior", "label": "Interior / Exterior", "type": "select", "options": [{"value": "interior", "label": "Interior"}, {"value": "exterior", "label": "Exterior"}, {"value": "both", "label": "Both"}], "default": "interior", "group": "installation"},
        {"key": "install_notes", "label": "Install Notes", "type": "textarea", "group": "installation"},
        # Design
        {"key": "artwork_provided", "label": "Artwork Provided", "type": "toggle", "default": False, "group": "design"},
        {"key": "design_needed", "label": "Design Needed", "type": "toggle", "default": False, "group": "design", "pricing": True},
        {"key": "proof_required", "label": "Proof Required", "type": "toggle", "default": True, "group": "design"},
        {"key": "artwork_notes", "label": "Notes", "type": "textarea", "group": "design"},
        # Production
        {"key": "rush_order", "label": "Rush Order", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "outsourced", "label": "Outsourced", "type": "toggle", "default": False, "group": "production"},
    ]


def _vehicle_wrap_schema(defaults, vinyl_opts, coverage_opts, vehicle_type_opts):
    """Full Vehicle Wrap category schema."""
    difficulty_opts = [
        {"value": "easy", "label": "Easy"}, {"value": "moderate", "label": "Moderate"}, {"value": "complex", "label": "Complex"},
    ]
    lam_opts = [
        {"value": "gloss", "label": "Gloss"}, {"value": "matte", "label": "Matte"}, {"value": "satin", "label": "Satin"},
    ]
    coverage_full = [
        {"value": "full", "label": "Full Wrap (100%)"},
        {"value": "75", "label": "Partial Wrap (75%)"},
        {"value": "50", "label": "Partial Wrap (50%)"},
        {"value": "25", "label": "Spot Graphics (25%)"},
        {"value": "custom", "label": "Custom %"},
    ]
    area_opts = [
        {"value": "hood", "label": "Hood"}, {"value": "roof", "label": "Roof"},
        {"value": "driver_side", "label": "Driver Side"}, {"value": "passenger_side", "label": "Passenger Side"},
        {"value": "rear", "label": "Rear"}, {"value": "windows_perf", "label": "Windows (Perf)"},
        {"value": "tailgate", "label": "Tailgate"}, {"value": "bumper", "label": "Bumper"},
    ]
    return [
        # Vehicle Information
        {"key": "vehicle_type", "label": "Vehicle Type", "type": "select", "options": vehicle_type_opts, "group": "vehicle_info", "required": True, "pricing": True},
        {"key": "vehicle_year", "label": "Year", "type": "text", "placeholder": "2024", "group": "vehicle_info"},
        {"key": "vehicle_make", "label": "Make", "type": "text", "placeholder": "Ford, Chevy, Ram", "group": "vehicle_info"},
        {"key": "vehicle_model", "label": "Model", "type": "text", "placeholder": "Transit, Silverado", "group": "vehicle_info"},
        {"key": "vehicle_notes", "label": "Existing Damage / Notes", "type": "textarea", "group": "vehicle_info"},
        # Coverage
        {"key": "coverage_type", "label": "Coverage Level", "type": "select", "options": coverage_full, "group": "coverage", "required": True, "pricing": True},
        {"key": "coverage_percent", "label": "Coverage % (if custom)", "type": "number", "placeholder": "100", "group": "coverage", "pricing": True},
        {"key": "areas_covered", "label": "Areas Covered", "type": "location_picker", "options": area_opts, "group": "coverage", "pricing": True},
        # Material & Print
        {"key": "vinyl_type", "label": "Vinyl Type", "type": "select", "options": vinyl_opts, "group": "material_print", "required": True, "pricing": True},
        {"key": "lamination", "label": "Lamination", "type": "select", "options": lam_opts, "group": "material_print", "pricing": True},
        {"key": "print_quality", "label": "Print Quality", "type": "select", "options": [{"value": "standard", "label": "Standard"}, {"value": "high", "label": "High Quality"}], "default": "standard", "group": "material_print"},
        {"key": "color_notes", "label": "Color / Design Notes", "type": "textarea", "group": "material_print"},
        # Paneling & Production
        {"key": "paneling_method", "label": "Paneling Method", "type": "select", "options": [{"value": "auto", "label": "Auto Paneling"}, {"value": "manual", "label": "Manual Paneling"}], "default": "auto", "group": "paneling"},
        {"key": "num_panels", "label": "Number of Panels", "type": "number", "placeholder": "Auto", "group": "paneling"},
        {"key": "contour_cuts", "label": "Contour Cuts Required", "type": "toggle", "default": False, "group": "paneling", "pricing": True},
        # Installation
        {"key": "install_required", "label": "Install Required", "type": "toggle", "default": True, "group": "installation", "pricing": True},
        {"key": "install_location", "label": "Install Location", "type": "select", "options": [{"value": "in_house", "label": "In-House"}, {"value": "on_site", "label": "On-Site"}], "default": "in_house", "group": "installation"},
        {"key": "install_difficulty", "label": "Install Difficulty", "type": "select", "options": difficulty_opts, "default": "moderate", "group": "installation", "pricing": True},
        {"key": "estimated_install_hours", "label": "Estimated Install Hours", "type": "number", "placeholder": "Auto", "group": "installation", "pricing": True},
        {"key": "removal_required", "label": "Removal Required", "type": "toggle", "default": False, "group": "installation", "pricing": True},
        {"key": "surface_prep", "label": "Surface Prep Required", "type": "toggle", "default": False, "group": "installation", "pricing": True},
        # Design & Complexity
        {"key": "artwork_provided", "label": "Artwork Provided", "type": "toggle", "default": False, "group": "design"},
        {"key": "design_needed", "label": "Design Needed", "type": "toggle", "default": True, "group": "design", "pricing": True},
        {"key": "design_complexity", "label": "Design Complexity", "type": "select", "options": [{"value": "simple", "label": "Simple"}, {"value": "moderate", "label": "Moderate"}, {"value": "complex", "label": "Complex"}], "default": "moderate", "group": "design", "pricing": True},
        {"key": "num_revisions", "label": "Expected Revisions", "type": "number", "placeholder": "2", "group": "design"},
        {"key": "mockups_required", "label": "Mockups Required", "type": "toggle", "default": True, "group": "design", "pricing": True},
        {"key": "proof_required", "label": "Proof Required", "type": "toggle", "default": True, "group": "design"},
        # Production
        {"key": "rush_order", "label": "Rush Order", "type": "toggle", "default": False, "group": "production", "pricing": True},
        {"key": "outsourced_print", "label": "Outsourced Print", "type": "toggle", "default": False, "group": "production"},
        {"key": "outsourced_install", "label": "Outsourced Install", "type": "toggle", "default": False, "group": "production"},
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
        "rigid_signs": _rigid_sign_schema(defaults, enum_opts(SubstrateType)),
        "cut_vinyl": _cut_vinyl_schema(defaults, enum_opts(VinylType)),
        "vehicle_wrap": _vehicle_wrap_schema(defaults, enum_opts(VinylType), enum_opts(CoverageType), enum_opts(VehicleType)),
        "digital_print": _digital_print_schema(defaults),
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
