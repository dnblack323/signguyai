"""
Pricing Calculator related Pydantic models.
"""
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
import uuid

from .enums import (
    PricingCategory, ServiceType, ApparelType, TransferType,
    VinylType, PrintMaterial, SubstrateType, VehicleType,
    CoverageType, PromoProductType, JobItemType, JobItemStatus
)


# ============== MATERIAL CONFIGURATION ==============
class MaterialConfig(BaseModel):
    """Individual material/product configuration with costs"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str
    name: str
    category: str
    subtype: str = ""
    brand: str = ""
    vendor: str = ""
    thickness: str = ""
    width_inches: float = 0
    length_inches: float = 0
    roll_sheet_size: str = ""
    purchase_unit: str = ""
    purchase_cost: float = 0
    cost_per_unit: float = 0
    unit_type: str = "sqft"
    cost_per_sqft: float = 0
    cost_per_linear_foot: float = 0
    sell_rate_per_sqft: float = 0
    waste_factor: float = 0
    waste_override: float = 0
    compatible_categories: List[str] = Field(default_factory=list)
    is_active: bool = True
    notes: str = ""


class HardwareAccessoryConfig(BaseModel):
    """Hardware/accessory configuration with default cost + labor"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str = ""
    subcategory: str = ""
    unit_type: str = "each"
    purchase_cost: float = 0
    default_sell_price: float = 0
    default_labor_addon_minutes: float = 0
    compatible_categories: List[str] = Field(default_factory=list)
    is_active: bool = True
    notes: str = ""


class LaborRateRule(BaseModel):
    """Labor/service rate defaults for pricing calculations"""
    model_config = ConfigDict(extra="ignore")
    hourly_rate: float = 0
    minimum_charge: float = 0
    billing_increment_minutes: float = 15
    default_time_minutes: float = 0
    helper_addon_rate: float = 0
    after_hours_multiplier: float = 1.0
    weekend_multiplier: float = 1.0
    emergency_multiplier: float = 1.0


# ============== PRICING DEFAULTS ==============
class PricingDefaults(BaseModel):
    """Default pricing rates and multipliers for a tenant"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str

    # Company-specific cost settings foundation
    materials: List[Dict[str, Any]] = Field(default_factory=lambda: [
        {"id": "vinyl-cost", "key": "vinyl", "name": "Vinyl Cost Per Sq Ft", "category": "material", "cost_per_unit": 1.25, "unit_type": "sqft", "is_active": True},
        {"id": "laminate-cost", "key": "laminate", "name": "Laminate Cost Per Sq Ft", "category": "material", "cost_per_unit": 0.65, "unit_type": "sqft", "is_active": True},
        {"id": "banner-material-cost", "key": "banner_material", "name": "Banner Material Cost Per Sq Ft", "category": "material", "cost_per_unit": 0.9, "unit_type": "sqft", "is_active": True},
        {"id": "coroplast-cost", "key": "coroplast", "name": "Coroplast Cost Per Sq Ft", "category": "material", "cost_per_unit": 1.35, "unit_type": "sqft", "is_active": True},
        {"id": "aluminum-composite-cost", "key": "aluminum_composite", "name": "Aluminum Composite Cost Per Sq Ft", "category": "material", "cost_per_unit": 3.75, "unit_type": "sqft", "is_active": True},
        {"id": "foam-board-cost", "key": "foam_board", "name": "Foam Board Cost Per Sq Ft", "category": "material", "cost_per_unit": 2.15, "unit_type": "sqft", "is_active": True},
        {"id": "ink-cost", "key": "ink", "name": "Ink Cost Per Sq Ft", "category": "optional", "cost_per_unit": 0.35, "unit_type": "sqft", "is_active": True},
        {"id": "transfer-tape-cost", "key": "transfer_tape", "name": "Transfer Tape Cost Per Sq Ft", "category": "transfer_tape", "cost_per_unit": 0.35, "cost_per_sqft": 0.35, "unit_type": "sqft", "is_active": True},
        {"id": "apparel-blank-cost", "key": "apparel_blank", "name": "Apparel Blank Cost Per Item", "category": "material", "cost_per_unit": 5.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-decoration-cost", "key": "apparel_decoration", "name": "Apparel Decoration Cost Per Print", "category": "material", "cost_per_unit": 2.5, "unit_type": "each", "is_active": True},
        {"id": "misc-material-cost", "key": "misc_material", "name": "Custom / Misc Material Cost Per Item", "category": "material", "cost_per_unit": 10.0, "unit_type": "each", "is_active": True},
        {"id": "acrylic-sheet-cost", "key": "acrylic_sheet", "name": "Acrylic Sheet Cost Per Sq Ft", "category": "material", "cost_per_unit": 5.5, "unit_type": "sqft", "is_active": True},
        {"id": "rigid-sign-board-cost", "key": "rigid_sign_board", "name": "Rigid Sign Board Cost Per Sq Ft", "category": "material", "cost_per_unit": 2.85, "unit_type": "sqft", "is_active": True},
        {"id": "dp-printable-adhesive-vinyl", "key": "printable_adhesive_vinyl", "name": "Printable Adhesive Vinyl", "category": "print_media", "cost_per_unit": 1.5, "cost_per_sqft": 1.5, "sell_rate_per_sqft": 10.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-poster-paper", "key": "poster_paper", "name": "Poster Paper", "category": "print_media", "cost_per_unit": 0.6, "cost_per_sqft": 0.6, "sell_rate_per_sqft": 6.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-canvas", "key": "canvas", "name": "Canvas", "category": "print_media", "cost_per_unit": 2.25, "cost_per_sqft": 2.25, "sell_rate_per_sqft": 15.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-backlit-film", "key": "backlit_film", "name": "Backlit Film", "category": "print_media", "cost_per_unit": 2.5, "cost_per_sqft": 2.5, "sell_rate_per_sqft": 16.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-perforated-window-film", "key": "perforated_window_film", "name": "Perforated Window Film", "category": "print_media", "cost_per_unit": 2.75, "cost_per_sqft": 2.75, "sell_rate_per_sqft": 18.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-wall-graphic-media", "key": "wall_graphic_media", "name": "Wall Graphic Media", "category": "print_media", "cost_per_unit": 2.25, "cost_per_sqft": 2.25, "sell_rate_per_sqft": 14.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-floor-graphic-media", "key": "floor_graphic_media", "name": "Floor Graphic Media", "category": "print_media", "cost_per_unit": 3.0, "cost_per_sqft": 3.0, "sell_rate_per_sqft": 20.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-removable-adhesive", "key": "removable_adhesive_print_media", "name": "Removable Adhesive Print Media", "category": "print_media", "cost_per_unit": 1.5, "cost_per_sqft": 1.5, "sell_rate_per_sqft": 10.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-photo-paper", "key": "photo_paper", "name": "Photo Paper", "category": "print_media", "cost_per_unit": 0.75, "cost_per_sqft": 0.75, "sell_rate_per_sqft": 8.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-specialty-media", "key": "specialty_print_media", "name": "Specialty / Custom Print Media", "category": "print_media", "cost_per_unit": 2.0, "cost_per_sqft": 2.0, "sell_rate_per_sqft": 12.0, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-ink-cost", "key": "digital_print_ink", "name": "Digital Print Ink (100% coverage)", "category": "consumable", "cost_per_unit": 0.75, "cost_per_sqft": 0.75, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-laminate-gloss", "key": "laminate_gloss", "name": "Gloss Laminate", "category": "laminate", "cost_per_unit": 0.85, "cost_per_sqft": 0.85, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-laminate-matte", "key": "laminate_matte", "name": "Matte Laminate", "category": "laminate", "cost_per_unit": 0.85, "cost_per_sqft": 0.85, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-laminate-heavy", "key": "laminate_heavy_duty", "name": "Heavy-Duty Laminate", "category": "laminate", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-laminate-floor", "key": "laminate_floor", "name": "Floor Laminate", "category": "laminate", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-laminate-uv", "key": "laminate_uv", "name": "UV Laminate", "category": "laminate", "cost_per_unit": 0.85, "cost_per_sqft": 0.85, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "dp-laminate-specialty", "key": "laminate_specialty", "name": "Specialty / Custom Laminate", "category": "laminate", "cost_per_unit": 0.85, "cost_per_sqft": 0.85, "unit_type": "sqft", "compatible_categories": ["digital_print"], "is_active": True},
        {"id": "cv-oracal-651", "key": "oracal_651", "name": "Oracal 651", "category": "cut_vinyl", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "sell_rate_per_sqft": 12.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-oracal-751", "key": "oracal_751", "name": "Oracal 751", "category": "cut_vinyl", "cost_per_unit": 2.5, "cost_per_sqft": 2.5, "sell_rate_per_sqft": 15.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-oracal-951", "key": "oracal_951", "name": "Oracal 951", "category": "cut_vinyl", "cost_per_unit": 2.5, "cost_per_sqft": 2.5, "sell_rate_per_sqft": 15.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-avery-hp750", "key": "avery_hp750", "name": "Avery HP750", "category": "cut_vinyl", "cost_per_unit": 2.5, "cost_per_sqft": 2.5, "sell_rate_per_sqft": 15.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-reflective", "key": "reflective_vinyl", "name": "Reflective Vinyl", "category": "cut_vinyl", "cost_per_unit": 4.5, "cost_per_sqft": 4.5, "sell_rate_per_sqft": 22.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-metallic", "key": "metallic_vinyl", "name": "Metallic Vinyl", "category": "cut_vinyl", "cost_per_unit": 4.5, "cost_per_sqft": 4.5, "sell_rate_per_sqft": 22.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-fluorescent", "key": "fluorescent_vinyl", "name": "Fluorescent Vinyl", "category": "cut_vinyl", "cost_per_unit": 4.5, "cost_per_sqft": 4.5, "sell_rate_per_sqft": 22.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-etched", "key": "etched_frost_vinyl", "name": "Etched / Frost Vinyl", "category": "cut_vinyl", "cost_per_unit": 4.5, "cost_per_sqft": 4.5, "sell_rate_per_sqft": 20.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-wall", "key": "wall_vinyl", "name": "Wall Vinyl", "category": "cut_vinyl", "cost_per_unit": 2.5, "cost_per_sqft": 2.5, "sell_rate_per_sqft": 15.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "cv-specialty", "key": "specialty_custom_vinyl", "name": "Specialty / Custom Vinyl", "category": "cut_vinyl", "cost_per_unit": 4.5, "cost_per_sqft": 4.5, "sell_rate_per_sqft": 24.0, "unit_type": "sqft", "compatible_categories": ["cut_vinyl"], "is_active": True},
        {"id": "rs-coroplast-4mm", "key": "coroplast_4mm", "name": "Coroplast 4mm", "category": "substrate", "cost_per_unit": 0.9, "cost_per_sqft": 0.9, "sell_rate_per_sqft": 10.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-coroplast-10mm", "key": "coroplast_10mm", "name": "Coroplast 10mm", "category": "substrate", "cost_per_unit": 1.6, "cost_per_sqft": 1.6, "sell_rate_per_sqft": 14.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-pvc-3mm", "key": "pvc_3mm", "name": "PVC 3mm", "category": "substrate", "cost_per_unit": 2.25, "cost_per_sqft": 2.25, "sell_rate_per_sqft": 16.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-pvc-6mm", "key": "pvc_6mm", "name": "PVC 6mm", "category": "substrate", "cost_per_unit": 3.5, "cost_per_sqft": 3.5, "sell_rate_per_sqft": 22.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-acm-dibond", "key": "acm_dibond_3mm", "name": "ACM / Dibond 3mm", "category": "substrate", "cost_per_unit": 4.25, "cost_per_sqft": 4.25, "sell_rate_per_sqft": 24.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-aluminum-040", "key": "aluminum_040", "name": "Aluminum .040", "category": "substrate", "cost_per_unit": 3.25, "cost_per_sqft": 3.25, "sell_rate_per_sqft": 18.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-aluminum-063", "key": "aluminum_063", "name": "Aluminum .063", "category": "substrate", "cost_per_unit": 4.25, "cost_per_sqft": 4.25, "sell_rate_per_sqft": 22.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-aluminum-080", "key": "aluminum_080", "name": "Aluminum .080", "category": "substrate", "cost_per_unit": 5.25, "cost_per_sqft": 5.25, "sell_rate_per_sqft": 26.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-acrylic-1-8", "key": "acrylic_1_8", "name": "Acrylic 1/8\"", "category": "substrate", "cost_per_unit": 4.5, "cost_per_sqft": 4.5, "sell_rate_per_sqft": 24.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-acrylic-1-4", "key": "acrylic_1_4", "name": "Acrylic 1/4\"", "category": "substrate", "cost_per_unit": 6.5, "cost_per_sqft": 6.5, "sell_rate_per_sqft": 32.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-foamboard", "key": "foamboard_3_16", "name": "Foamboard 3/16\"", "category": "substrate", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "sell_rate_per_sqft": 12.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-mdo", "key": "mdo_1_2", "name": "MDO 1/2\"", "category": "substrate", "cost_per_unit": 3.75, "cost_per_sqft": 3.75, "sell_rate_per_sqft": 20.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-custom-substrate", "key": "custom_other_substrate", "name": "Custom Other Substrate", "category": "substrate", "cost_per_unit": 4.0, "cost_per_sqft": 4.0, "sell_rate_per_sqft": 20.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-mounted-print", "key": "mounted_print_graphic", "name": "Mounted Print Graphic", "category": "rigid_graphic", "cost_per_unit": 2.0, "cost_per_sqft": 2.0, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-direct-print", "key": "direct_print_consumable", "name": "Direct Print Consumable", "category": "rigid_graphic", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "rs-finish-standard", "key": "rigid_finish_standard", "name": "Standard Protective Finish", "category": "rigid_finish", "cost_per_unit": 0.75, "cost_per_sqft": 0.75, "unit_type": "sqft", "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "bn-13oz", "key": "banner_13oz", "name": "13 oz Banner", "category": "banner_material", "cost_per_unit": 0.85, "cost_per_sqft": 0.85, "sell_rate_per_sqft": 8.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-18oz", "key": "banner_18oz", "name": "18 oz Banner", "category": "banner_material", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "sell_rate_per_sqft": 10.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-mesh", "key": "banner_mesh", "name": "Mesh Banner", "category": "banner_material", "cost_per_unit": 1.40, "cost_per_sqft": 1.40, "sell_rate_per_sqft": 11.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-blockout", "key": "banner_blockout", "name": "Blockout Banner", "category": "banner_material", "cost_per_unit": 1.65, "cost_per_sqft": 1.65, "sell_rate_per_sqft": 12.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-pole", "key": "banner_pole", "name": "Pole Banner Material", "category": "banner_material", "cost_per_unit": 2.25, "cost_per_sqft": 2.25, "sell_rate_per_sqft": 14.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-fabric", "key": "banner_fabric", "name": "Fabric Display Banner", "category": "banner_material", "cost_per_unit": 2.75, "cost_per_sqft": 2.75, "sell_rate_per_sqft": 16.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-double-sided", "key": "banner_double_sided", "name": "Double-Sided Banner Material", "category": "banner_material", "cost_per_unit": 1.95, "cost_per_sqft": 1.95, "sell_rate_per_sqft": 13.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-custom", "key": "banner_custom", "name": "Specialty / Custom Banner Material", "category": "banner_material", "cost_per_unit": 2.00, "cost_per_sqft": 2.00, "sell_rate_per_sqft": 12.0, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-print-consumable", "key": "banner_print_consumable", "name": "Banner Print Consumable (ink/wear)", "category": "banner_consumable", "cost_per_unit": 0.75, "cost_per_sqft": 0.75, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "bn-laminate-coating", "key": "banner_laminate_coating", "name": "Optional Laminate / Coating", "category": "banner_coating", "cost_per_unit": 0.60, "cost_per_sqft": 0.60, "unit_type": "sqft", "compatible_categories": ["banners"], "is_active": True},
        {"id": "apparel-tshirt", "key": "tshirt", "name": "T-Shirt", "category": "apparel", "cost_per_unit": 4.5, "unit_type": "each", "is_active": True},
        {"id": "apparel-hoodie", "key": "hoodie", "name": "Hoodie", "category": "apparel", "cost_per_unit": 18.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-hat", "key": "hat", "name": "Hat/Cap", "category": "apparel", "cost_per_unit": 8.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-polo", "key": "polo", "name": "Polo Shirt", "category": "apparel", "cost_per_unit": 12.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-tank", "key": "tank", "name": "Tank Top", "category": "apparel", "cost_per_unit": 4.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-longsleeve", "key": "longsleeve", "name": "Long Sleeve", "category": "apparel", "cost_per_unit": 7.5, "unit_type": "each", "is_active": True},
        {"id": "apparel-jacket", "key": "jacket", "name": "Jacket", "category": "apparel", "cost_per_unit": 25.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-crewneck", "key": "crewneck", "name": "Crewneck Sweatshirt", "category": "apparel", "cost_per_unit": 15.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-safety-vest", "key": "safety_vest", "name": "Safety Vest", "category": "apparel", "cost_per_unit": 10.0, "unit_type": "each", "is_active": True},
        {"id": "decor-htv", "key": "htv", "name": "HTV (Heat Transfer Vinyl)", "category": "decoration", "cost_per_unit": 0.5, "unit_type": "per_color", "is_active": True},
        {"id": "decor-screen-print", "key": "screen_print", "name": "Screen Print Transfer", "category": "decoration", "cost_per_unit": 0.35, "unit_type": "per_color", "is_active": True},
        {"id": "decor-dtf", "key": "dtf", "name": "DTF / Printed Transfer", "category": "decoration", "cost_per_unit": 0.03, "unit_type": "per_sqin", "is_active": True},
        {"id": "decor-sublimation", "key": "sublimation", "name": "Sublimation", "category": "decoration", "cost_per_unit": 0.04, "unit_type": "per_sqin", "is_active": True},
        {"id": "decor-embroidery", "key": "embroidery", "name": "Embroidery", "category": "decoration", "cost_per_unit": 0.01, "unit_type": "per_stitch", "is_active": True},
        {"id": "decor-patch", "key": "patch", "name": "Patch / Emblem", "category": "decoration", "cost_per_unit": 3.0, "unit_type": "each", "is_active": True},
        {"id": "vehicle-car-sedan", "key": "car_sedan", "name": "Car (Sedan)", "category": "vehicle_type", "base_sqft": 150, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-car-suv", "key": "car_suv", "name": "Car (SUV)", "category": "vehicle_type", "base_sqft": 200, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-pickup", "key": "pickup", "name": "Pickup Truck", "category": "vehicle_type", "base_sqft": 175, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-van-cargo", "key": "van_cargo", "name": "Cargo Van", "category": "vehicle_type", "base_sqft": 250, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-van-sprinter", "key": "van_sprinter", "name": "Sprinter Van", "category": "vehicle_type", "base_sqft": 350, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-box-truck-12ft", "key": "box_truck_12ft", "name": "Box Truck (12ft)", "category": "vehicle_type", "base_sqft": 400, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-box-truck-16ft", "key": "box_truck_16ft", "name": "Box Truck (16ft)", "category": "vehicle_type", "base_sqft": 500, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-box-truck-24ft", "key": "box_truck_24ft", "name": "Box Truck (24ft)", "category": "vehicle_type", "base_sqft": 650, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-trailer", "key": "trailer", "name": "Trailer", "category": "vehicle_type", "base_sqft": 450, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-semi", "key": "semi", "name": "Semi Truck", "category": "vehicle_type", "base_sqft": 800, "unit_type": "sqft", "is_active": True},
        {"id": "vehicle-other", "key": "other", "name": "Other Vehicle", "category": "vehicle_type", "base_sqft": 160, "unit_type": "sqft", "is_active": True},
    ])
    hardware_accessories: List[Dict[str, Any]] = Field(default_factory=lambda: [
        {"id": "hw-h-stake", "name": "Standard H-Stake", "category": "stakes", "subcategory": "standard", "unit_type": "each", "purchase_cost": 1.5, "default_sell_price": 3.5, "default_labor_addon_minutes": 0, "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "hw-heavy-stake", "name": "Heavy-Duty Stake", "category": "stakes", "subcategory": "heavy", "unit_type": "each", "purchase_cost": 2.5, "default_sell_price": 5.0, "default_labor_addon_minutes": 0, "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "hw-screws", "name": "Screws / Basic Mounting Set", "category": "mounting", "subcategory": "screws", "unit_type": "set", "purchase_cost": 1.0, "default_sell_price": 3.0, "default_labor_addon_minutes": 0, "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "hw-standoff", "name": "Stand-Off Set", "category": "mounting", "subcategory": "standoff", "unit_type": "set", "purchase_cost": 3.0, "default_sell_price": 7.0, "default_labor_addon_minutes": 0, "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "hw-easel", "name": "Easel Back", "category": "display", "subcategory": "easel", "unit_type": "each", "purchase_cost": 2.0, "default_sell_price": 5.0, "default_labor_addon_minutes": 0, "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "hw-hanging", "name": "Hanging Hardware", "category": "mounting", "subcategory": "hanging", "unit_type": "set", "purchase_cost": 1.5, "default_sell_price": 4.0, "default_labor_addon_minutes": 0, "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "hw-custom", "name": "Custom Other Hardware", "category": "custom", "subcategory": "other", "unit_type": "each", "purchase_cost": 2.0, "default_sell_price": 5.0, "default_labor_addon_minutes": 0, "compatible_categories": ["rigid_signs"], "is_active": True},
        {"id": "hw-banner-grommet", "name": "Banner Grommet", "category": "banner_hardware", "subcategory": "grommet", "unit_type": "each", "purchase_cost": 0.20, "default_sell_price": 0.75, "default_labor_addon_minutes": 0.5, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-pole-rod", "name": "Pole Pocket Rod", "category": "banner_hardware", "subcategory": "pole_rod", "unit_type": "each", "purchase_cost": 3.50, "default_sell_price": 12.0, "default_labor_addon_minutes": 2, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-bungee", "name": "Bungee Cord Set", "category": "banner_hardware", "subcategory": "tie_down", "unit_type": "set", "purchase_cost": 1.50, "default_sell_price": 4.0, "default_labor_addon_minutes": 0, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-rope", "name": "Rope / Tie Set", "category": "banner_hardware", "subcategory": "tie_down", "unit_type": "set", "purchase_cost": 1.25, "default_sell_price": 3.5, "default_labor_addon_minutes": 0, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-zipties", "name": "Zip Tie Set", "category": "banner_hardware", "subcategory": "tie_down", "unit_type": "set", "purchase_cost": 0.50, "default_sell_price": 2.0, "default_labor_addon_minutes": 0, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-retractable-stand", "name": "Retractable Stand Base", "category": "banner_hardware", "subcategory": "stand", "unit_type": "each", "purchase_cost": 40.0, "default_sell_price": 95.0, "default_labor_addon_minutes": 5, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-x-stand", "name": "X-Banner Stand", "category": "banner_hardware", "subcategory": "stand", "unit_type": "each", "purchase_cost": 18.0, "default_sell_price": 45.0, "default_labor_addon_minutes": 3, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-sandbag", "name": "Sandbag", "category": "banner_hardware", "subcategory": "weight", "unit_type": "each", "purchase_cost": 8.0, "default_sell_price": 20.0, "default_labor_addon_minutes": 0, "compatible_categories": ["banners"], "is_active": True},
        {"id": "hw-banner-custom", "name": "Custom Other Banner Hardware", "category": "banner_hardware", "subcategory": "other", "unit_type": "each", "purchase_cost": 2.0, "default_sell_price": 5.0, "default_labor_addon_minutes": 0, "compatible_categories": ["banners"], "is_active": True},
    ])
    labor_rates: Dict[str, Any] = Field(default_factory=lambda: {
        "design": {
            "hourly_rate": 85.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 15,
            "default_time_minutes": 60,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "production": {
            "hourly_rate": 28.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 15,
            "default_time_minutes": 60,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "finishing": {
            "hourly_rate": 28.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 15,
            "default_time_minutes": 30,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "installation": {
            "hourly_rate": 95.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 30,
            "default_time_minutes": 90,
            "helper_addon_rate": 45.0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "removal": {
            "hourly_rate": 65.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 30,
            "default_time_minutes": 60,
            "helper_addon_rate": 35.0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "travel": {
            "hourly_rate": 45.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 30,
            "default_time_minutes": 30,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "admin_project_handling": {
            "hourly_rate": 35.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 15,
            "default_time_minutes": 30,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "consultation": {
            "hourly_rate": 110.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 30,
            "default_time_minutes": 60,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "site_survey": {
            "hourly_rate": 95.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 30,
            "default_time_minutes": 60,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
        "other_labor": {
            "hourly_rate": 65.0,
            "minimum_charge": 0,
            "billing_increment_minutes": 15,
            "default_time_minutes": 30,
            "helper_addon_rate": 0,
            "after_hours_multiplier": 1.0,
            "weekend_multiplier": 1.0,
            "emergency_multiplier": 1.0,
        },
    })
    production_hourly_rate: float = 28.0
    installer_hourly_rate: float = 40.0
    overhead_percentage: float = 15.0
    shop_overhead_per_hour: float = 0.0
    apply_overhead_to_jobs: bool = True
    target_profit_margin_percent: float = 40.0
    default_markup_multiplier: float = 2.5
    category_defaults: Dict[str, Any] = Field(default_factory=lambda: {
        "digital_print": {
            "label": "Digital Print",
            "default_labor_hours_per_sqft": 0.08,
            "default_markup_multiplier": 2.3,
            "target_profit_margin_percent": 40.0,
            "minimum_charge": 40.0,
            "default_material_keys": ["printable_adhesive_vinyl", "digital_print_ink"],
            "default_hardware_keys": [],
            "default_labor_types": ["production"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
            "default_print_media_key": "printable_adhesive_vinyl",
            "default_ink_material_key": "digital_print_ink",
            "available_print_media_keys": [
                "printable_adhesive_vinyl",
                "poster_paper",
                "canvas",
                "backlit_film",
                "perforated_window_film",
                "wall_graphic_media",
                "floor_graphic_media",
                "removable_adhesive_print_media",
                "photo_paper",
                "specialty_print_media",
            ],
            "default_laminate_required": False,
            "default_laminate_key": "laminate_gloss",
            "default_install_included": False,
            "default_minimum_billable_area": 1.0,
            "default_minimum_sell_price": 20.0,
            "default_file_prep_fee": 20.0,
            "default_design_time_hours": 0.5,
            "default_print_quality_mode": "standard",
            "default_ink_coverage_percent": 35.0,
            "waste_percentage": 10.0,
            "base_ink_cost_per_sqft": 0.75,
            "sell_method": "max_of_rate_or_minimum",
            "production_labor_hours_per_sqft": 0.08,
            "min_production_labor_hours_per_item": 0.2,
            "mounting_labor_hours_per_sqft": 0.08,
            "piece_separation_hours_per_piece": 0.02,
            "install_hours_per_sqft": 0.08,
            "quality_multipliers": {
                "draft": 0.9,
                "standard": 1.0,
                "high": 1.15,
                "photo": 1.3,
            },
            "contour_cut_multipliers": {
                "none": 1.0,
                "simple": 1.2,
                "complex": 1.5,
                "kiss": 1.15,
            },
            "trim_premium_addon": 3.0,
            "quantity_discounts": [
                {"min_qty": 1, "max_qty": 4, "discount_percent": 0},
                {"min_qty": 5, "max_qty": 24, "discount_percent": 5},
                {"min_qty": 25, "max_qty": 99, "discount_percent": 10},
                {"min_qty": 100, "max_qty": None, "discount_percent": 15},
            ],
            "default_use_type": "indoor",
            "default_unit_of_measure": "inches",
            "default_contour_cut_type": "none",
            "default_trim_finish_type": "standard",
            "default_design_complexity": "simple",
            "default_install_complexity": "easy",
        },
        "vehicle_wraps": {
            "label": "Vehicle Graphics / Wraps",
            "default_labor_hours_per_sqft": 0.12,
            "default_markup_multiplier": 2.4,
            "target_profit_margin_percent": 42.0,
            "minimum_charge": 850.0,
            "default_material_keys": ["vinyl", "laminate", "ink"],
            "default_hardware_keys": [],
            "default_labor_types": ["installation", "design"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
        },
        "banners": {
            "label": "Banners",
            "default_labor_hours_per_sqft": 0.10,
            "default_markup_multiplier": 2.35,
            "target_profit_margin_percent": 40.0,
            "minimum_charge": 35.0,
            "default_material_keys": ["banner_13oz", "banner_print_consumable"],
            "default_hardware_keys": [],
            "default_labor_types": ["production"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
            "default_banner_material_key": "banner_13oz",
            "available_banner_material_keys": [
                "banner_13oz",
                "banner_18oz",
                "banner_mesh",
                "banner_blockout",
                "banner_pole",
                "banner_fabric",
                "banner_double_sided",
                "banner_custom",
            ],
            "banner_print_consumable_key": "banner_print_consumable",
            "banner_laminate_key": "banner_laminate_coating",
            "default_laminate_required": False,
            "default_laminate_key": "banner_laminate_coating",
            "default_install_included": False,
            "default_minimum_billable_area": 4.0,
            "default_minimum_sell_price": 35.0,
            "default_design_time_hours": 0.5,
            "waste_percentage": 8.0,
            "production_labor_hours_per_sqft": 0.10,
            "min_production_labor_hours_per_item": 0.20,
            "standard_hem_rate_per_linear_foot": 0.75,
            "reinforced_hem_rate_per_linear_foot": 1.25,
            "pole_pocket_rate_per_linear_foot": 3.50,
            "specialty_sewing_rate_per_linear_foot": 2.00,
            "grommet_cost_each": 0.20,
            "grommet_sell_each": 0.75,
            "grommet_minimum_charge": 4.0,
            "grommet_default_corner_count": 4,
            "grommet_spacing_feet": {"every_2ft": 2.0, "every_3ft": 3.0},
            "reinforced_corners_charge": 6.0,
            "wind_slit_charge": 2.0,
            "install_hours_per_sqft": 0.04,
            "install_base_hours": 0.5,
            "sidedness_multipliers": {
                "single": 1.0,
                "double_same": 1.75,
                "double_diff": 2.0,
            },
            "event_premium_multiplier": 1.20,
            "pole_banner_premium_multiplier": 1.30,
            "design_complexity_multipliers": {
                "simple": 1.0,
                "medium": 1.25,
                "complex": 1.5,
                "extreme": 2.0,
            },
            "install_complexity_multipliers": {
                "easy": 1.0,
                "medium": 1.25,
                "difficult": 1.5,
                "high_access": 2.0,
            },
            "quantity_discounts": [
                {"min_qty": 1, "max_qty": 2, "discount_percent": 0},
                {"min_qty": 3, "max_qty": 9, "discount_percent": 5},
                {"min_qty": 10, "max_qty": 24, "discount_percent": 10},
                {"min_qty": 25, "max_qty": None, "discount_percent": 15},
            ],
            "sell_method": "max_of_rate_or_minimum",
            "default_unit_of_measure": "feet",
            "default_use_type": "outdoor",
            "default_hems": "standard",
            "default_grommets": "corners",
            "default_pole_pockets": "none",
            "default_double_sided": "no",
            "default_reinforced_corners": False,
            "default_wind_slits": False,
            "default_specialty_sewing": False,
            "default_event_premium": False,
            "default_install_complexity": "easy",
            "default_design_complexity": "simple",
        },
        "rigid_signs": {
            "label": "Rigid Signs",
            "default_labor_hours_per_sqft": 0.15,
            "default_markup_multiplier": 2.45,
            "target_profit_margin_percent": 41.0,
            "minimum_charge": 25.0,
            "default_material_keys": ["coroplast_4mm", "direct_print_consumable"],
            "default_hardware_keys": ["hw-h-stake"],
            "default_labor_types": ["production", "installation"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
            "default_substrate_key": "coroplast_4mm",
            "available_substrate_keys": [
                "coroplast_4mm",
                "coroplast_10mm",
                "pvc_3mm",
                "pvc_6mm",
                "acm_dibond_3mm",
                "aluminum_040",
                "aluminum_063",
                "aluminum_080",
                "acrylic_1_8",
                "acrylic_1_4",
                "foamboard_3_16",
                "mdo_1_2",
                "custom_other_substrate",
            ],
            "default_finish_required": False,
            "default_finish_key": "rigid_finish_standard",
            "default_install_included": False,
            "default_minimum_billable_area": 1.0,
            "default_minimum_sell_price": 25.0,
            "default_design_time_hours": 0.5,
            "default_mounting_labor_hours_per_sqft": 0.08,
            "waste_percentage": 5.0,
            "production_labor_hours_per_sqft": 0.15,
            "min_production_labor_hours_per_item": 0.2,
            "install_hours_per_sqft": 0.08,
            "direct_print_consumable_key": "direct_print_consumable",
            "mounted_print_graphic_key": "mounted_print_graphic",
            "cut_vinyl_material_key": "oracal_651",
            "hardware_handling_labor_cost": 5.0,
            "drill_prep_fee": 3.0,
            "thickness_multipliers": {
                "thin_basic": 1.0,
                "medium": 1.1,
                "thick_heavy": 1.2,
            },
            "sidedness_multipliers": {
                "single": 1.0,
                "double_same": 1.75,
                "double_diff": 2.0,
            },
            "shape_multipliers": {
                "rectangle": 1.0,
                "rounded_corners": 1.1,
                "simple_contour": 1.25,
                "complex_contour": 1.5,
                "specialty_routed": 2.0,
            },
            "finish_quality_multipliers": {
                "standard": 1.0,
                "premium": 1.15,
                "presentation": 1.3,
                "architectural": 1.5,
            },
            "install_complexity_multipliers": {
                "easy": 1.0,
                "medium": 1.25,
                "difficult": 1.5,
                "high_risk": 2.0,
            },
            "quantity_discounts": [
                {"min_qty": 1, "max_qty": 4, "discount_percent": 0},
                {"min_qty": 5, "max_qty": 24, "discount_percent": 5},
                {"min_qty": 25, "max_qty": 99, "discount_percent": 10},
                {"min_qty": 100, "max_qty": None, "discount_percent": 15},
            ],
            "sell_method": "max_of_rate_or_minimum",
            "default_unit_of_measure": "inches",
            "default_graphic_method": "direct_print",
            "default_protective_finish": False,
            "default_sidedness": "single",
            "default_double_sided_art": "same",
            "default_shape_type": "rectangle",
            "default_finish_quality": "standard",
        },
        "cut_vinyl": {
            "label": "Cut Vinyl",
            "default_labor_hours_per_sqft": 0.2,
            "default_markup_multiplier": 2.3,
            "target_profit_margin_percent": 40.0,
            "minimum_charge": 20.0,
            "default_material_keys": ["oracal_651", "transfer_tape"],
            "default_hardware_keys": [],
            "default_labor_types": ["production"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
            "default_vinyl_type_key": "oracal_651",
            "available_vinyl_type_keys": [
                "oracal_651",
                "oracal_751",
                "oracal_951",
                "avery_hp750",
                "reflective_vinyl",
                "metallic_vinyl",
                "fluorescent_vinyl",
                "etched_frost_vinyl",
                "wall_vinyl",
                "specialty_custom_vinyl",
            ],
            "sell_method": "max_of_rate_or_minimum",
            "default_masking_required": True,
            "default_install_included": False,
            "default_minimum_billable_area": 0.5,
            "default_minimum_sell_price": 20.0,
            "default_cleanup_fee": 20.0,
            "default_design_time_hours": 0.5,
            "default_use_type": "indoor",
            "default_unit_of_measure": "inches",
            "default_weeding_complexity": "simple",
            "default_design_complexity": "simple",
            "default_install_complexity": "easy",
            "default_surface_type": "flat_smooth",
            "default_number_of_colors": 1,
            "waste_percentage": 10.0,
            "production_labor_hours_per_sqft": 0.2,
            "min_production_labor_hours_per_item": 0.25,
            "install_hours_per_sqft": 0.06,
            "transfer_tape_key": "transfer_tape",
            "color_multipliers": {
                "1": 1.0,
                "2": 1.5,
                "3": 2.0,
                "4_plus": 2.5,
            },
            "weeding_multipliers": {
                "simple": 1.0,
                "medium": 1.25,
                "complex": 1.5,
                "extreme": 2.0,
            },
            "install_complexity_multipliers": {
                "easy": 1.0,
                "medium": 1.25,
                "difficult": 1.5,
                "extreme": 2.0,
            },
            "surface_multipliers": {
                "flat_smooth": 1.0,
                "glass_window": 1.1,
                "vehicle": 1.25,
                "textured_rough": 1.5,
                "curved_awkward": 1.75,
            },
            "use_type_multipliers": {
                "indoor": 1.0,
                "outdoor": 1.05,
                "wall": 1.05,
                "glass_window": 1.1,
                "vehicle": 1.15,
                "specialty": 1.1,
            },
            "quantity_discounts": [
                {"min_qty": 1, "max_qty": 5, "discount_percent": 0},
                {"min_qty": 6, "max_qty": 24, "discount_percent": 5},
                {"min_qty": 25, "max_qty": 99, "discount_percent": 10},
                {"min_qty": 100, "max_qty": None, "discount_percent": 15},
            ],
        },
        "apparel": {
            "label": "Apparel",
            "default_labor_hours_per_unit": 0.08,
            "default_markup_multiplier": 2.15,
            "target_profit_margin_percent": 38.0,
            "minimum_charge": 60.0,
            "default_material_keys": ["apparel_blank", "apparel_decoration"],
            "default_hardware_keys": [],
            "default_labor_types": ["production"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
        },
        "services": {
            "label": "Services",
            "default_labor_hours": 1.0,
            "default_markup_multiplier": 1.8,
            "target_profit_margin_percent": 35.0,
            "minimum_charge": 75.0,
            "default_material_keys": ["misc_material"],
            "default_hardware_keys": [],
            "default_labor_types": ["consultation"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
        },
        "custom": {
            "label": "Custom / Miscellaneous",
            "default_labor_hours_per_unit": 0.25,
            "default_markup_multiplier": 2.25,
            "target_profit_margin_percent": 38.0,
            "minimum_charge": 50.0,
            "default_material_keys": ["misc_material"],
            "default_hardware_keys": [],
            "default_labor_types": ["production"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
        },
    })
    selling_price_benchmarks: Dict[str, Any] = Field(default_factory=lambda: {
        "digital_print": {
            "label": "Digital Print",
            "average_sell_price_per_sqft": 9.5,
            "average_order_total": 280.0,
            "minimum_charge": 45.0,
            "low_price": 7.0,
            "typical_price": 9.5,
            "premium_price": 13.0,
        },
        "vehicle_wraps": {
            "label": "Vehicle Wraps",
            "average_sell_price_per_sqft": 18.75,
            "average_order_total": 2850.0,
            "minimum_charge": 950.0,
            "low_price": 15.0,
            "typical_price": 18.75,
            "premium_price": 24.0,
        },
        "banners": {
            "label": "Banners",
            "average_sell_price_per_sqft": 8.25,
            "average_order_total": 245.0,
            "minimum_charge": 45.0,
            "low_price": 6.5,
            "typical_price": 8.25,
            "premium_price": 11.0,
        },
        "rigid_signs": {
            "label": "Rigid Signs",
            "average_sell_price_per_sqft": 12.4,
            "average_order_total": 310.0,
            "minimum_charge": 65.0,
            "low_price": 9.5,
            "typical_price": 12.4,
            "premium_price": 16.0,
        },
        "cut_vinyl": {
            "label": "Cut Vinyl",
            "average_sell_price_per_sqft": 7.5,
            "average_order_total": 125.0,
            "minimum_charge": 30.0,
            "low_price": 5.5,
            "typical_price": 7.5,
            "premium_price": 10.0,
        },
        "apparel": {
            "label": "Apparel",
            "average_sell_price_per_unit": 24.0,
            "average_order_total": 420.0,
            "minimum_charge": 75.0,
            "low_price": 18.0,
            "typical_price": 24.0,
            "premium_price": 32.0,
        },
        "services": {
            "label": "Services",
            "average_sell_price_per_hour": 110.0,
            "average_order_total": 240.0,
            "minimum_charge": 85.0,
            "low_price": 85.0,
            "typical_price": 110.0,
            "premium_price": 145.0,
        },
        "custom": {
            "label": "Custom / Miscellaneous",
            "average_sell_price_per_unit": 75.0,
            "average_order_total": 280.0,
            "minimum_charge": 60.0,
            "low_price": 55.0,
            "typical_price": 75.0,
            "premium_price": 100.0,
        },
    })
    
    # Labor rates
    hourly_rate: float = 75.0
    design_hourly_rate: float = 85.0
    install_hourly_rate: float = 95.0
    removal_hourly_rate: float = 65.0
    travel_hourly_rate: float = 45.0
    admin_hourly_rate: float = 35.0
    project_handling_hourly_rate: float = 35.0
    
    # Default markups
    default_markup_percent: float = 100.0
    material_markup_percent: float = 50.0
    
    # Waste and overhead
    waste_percentage: float = 10.0
    
    # Minimum charges
    minimum_order: float = 50.0
    minimum_design_charge: float = 75.0
    minimum_install_charge: float = 150.0
    minimum_removal_charge: float = 120.0
    minimum_vinyl_charge: float = 25.0
    minimum_print_charge: float = 35.0
    minimum_sign_charge: float = 50.0
    minimum_service_charge: float = 75.0
    minimum_wrap_charge: float = 500.0
    banner_grommet_price_each: float = 1.0
    banner_hemming_tape_price_per_linear_inch: float = 0.03
    
    # Rush and fees
    rush_fee_percentage: float = 25.0
    rush_fee_flat: float = 0.0
    setup_fee_default: float = 20.0
    file_cleanup_fee_default: float = 15.0
    
    # Rounding and display
    rounding_rule: str = "nearest_dollar"
    deposit_percentage: float = 50.0
    ai_fallback_behavior: str = "warn"
    ai_fallback_warnings_enabled: bool = True
    
    # Complexity multipliers
    complexity_multiplier_base: float = 1.0
    complexity_multiplier_max: float = 2.0
    install_complexity_multiplier_base: float = 1.0
    install_complexity_multiplier_max: float = 2.0
    
    # Setup fees by category
    setup_fee_vinyl: float = 15.0
    setup_fee_print: float = 25.0
    setup_fee_apparel_screen: float = 35.0
    setup_fee_apparel_dtf: float = 20.0
    
    # Quantity break thresholds and discounts
    quantity_breaks: Dict[str, Any] = Field(default_factory=lambda: {
        "break_1": {"min_qty": 10, "discount_percent": 5},
        "break_2": {"min_qty": 25, "discount_percent": 10},
        "break_3": {"min_qty": 50, "discount_percent": 15},
        "break_4": {"min_qty": 100, "discount_percent": 20}
    })
    
    # Per-category time estimates (minutes)
    weeding_time_per_sqft: float = 5.0
    application_time_per_sqft: float = 3.0
    print_time_per_sqft: float = 1.0
    laminate_time_per_sqft: float = 1.5
    
    # Travel
    mileage_rate: float = 0.67
    minimum_travel_charge: float = 50.0

    ai_estimation_rules: Dict[str, Any] = Field(default_factory=lambda: {
        "fill_missing_only": True,
        "never_override_user_values": True,
        "allow_prefill_category_defaults": True,
        "suggest_material_type": True,
        "suggest_complexity": True,
        "suggest_install": True,
        "suggest_design": True,
        "value_source_labels_enabled": True,
    })
    benchmark_rules: Dict[str, Any] = Field(default_factory=lambda: {
        "enabled": True,
        "historical_influence": 0.6,
        "outlier_handling": "exclude_high_low",
        "confidence_handling": "warn_low_confidence",
    })
    global_calc_rules: Dict[str, Any] = Field(default_factory=lambda: {
        "pricing_method_hierarchy": "max_of_margin_or_markup",
        "overhead_application": "material_and_labor",
        "waste_application": "material_only",
        "rush_application": "multiply_total",
        "minimum_billable_area": 1.0,
        "minimum_price_floor": 0.0,
        "category_override_rules": "",
        "fallback_warning_behavior": "warn",
    })

    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== PRICING CALCULATION ==============
class PricingCalculation(BaseModel):
    """Detailed pricing breakdown for a job item"""
    material_cost: float = 0
    labor_cost: float = 0
    setup_cost: float = 0
    additional_costs: float = 0
    overhead_cost: float = 0
    
    production_cost: float = 0
    total_cost: float = 0
    suggested_price: float = 0
    selling_price: float = 0
    
    markup_percent: float = 0
    profit_margin_percent: float = 0
    profit_amount: float = 0
    
    estimated_labor_minutes: float = 0
    
    breakdown: Dict[str, Any] = Field(default_factory=dict)


# ============== JOB ITEM PRICING DATA ==============
class JobItemPricingData(BaseModel):
    """Category-specific pricing inputs for a job item"""
    category: PricingCategory = PricingCategory.CUSTOM
    complexity: int = 1  # Default to 1 (simple), not 5
    
    # Setup fee control - ONE TIME per order, optional
    include_setup_fee: bool = False
    setup_fee: Optional[float] = None
    
    # Dimensions
    width_inches: Optional[float] = None
    length_inches: Optional[float] = None
    square_footage: Optional[float] = None
    
    # Promotional Items
    promo_product_type: Optional[PromoProductType] = None
    unit_cost: Optional[float] = None
    markup_percent: Optional[float] = None
    
    # Cut Vinyl
    vinyl_type: Optional[VinylType] = None
    vinyl_type_key: Optional[str] = None
    vinyl_colors: List[str] = Field(default_factory=list)
    num_colors: int = 1
    weeding_complexity: Optional[str] = None
    masking_required: Optional[bool] = None
    surface_type: Optional[str] = None
    
    # Digital Print
    print_media_key: Optional[str] = None
    print_material: Optional[PrintMaterial] = None
    unit_of_measure: Optional[str] = None
    use_type: Optional[str] = None
    print_quality_mode: Optional[str] = None
    ink_coverage_percent: Optional[float] = None
    laminate: bool = False
    laminate_type: Optional[str] = None
    laminate_material_key: Optional[str] = None
    contour_cut_type: Optional[str] = None
    trim_finish_type: Optional[str] = None
    piece_separation_required: bool = False
    separated_piece_count: int = 0
    artwork_ready: Optional[bool] = None
    artwork_needed: Optional[bool] = None
    design_complexity: Optional[str] = None
    file_cleanup_needed: bool = False
    mounted_to_substrate: bool = False
    substrate_material_key: Optional[str] = None
    install_complexity: Optional[str] = None
    grommets: Optional[str] = None
    hemming: Optional[str] = None
    
    # Rigid Signs
    substrate_type: Optional[SubstrateType] = None
    substrate_type_key: Optional[str] = None
    thickness: Optional[str] = None
    graphic_method: Optional[str] = None
    protective_finish: bool = False
    protective_finish_type: Optional[str] = None
    sidedness: Optional[str] = None
    double_sided_art: Optional[str] = None
    shape_type: Optional[str] = None
    finish_quality: Optional[str] = None
    hardware_included: bool = False
    hardware_type: Optional[str] = None
    drill_prep_required: bool = False
    install_required: bool = False

    # Banners
    banner_material_key: Optional[str] = None
    banner_use_type: Optional[str] = None  # indoor, outdoor, event_display, fence, pole_banner, backwall_step_repeat, custom
    banner_laminate: Optional[bool] = None
    banner_laminate_type_key: Optional[str] = None
    banner_hems: Optional[str] = None  # none, standard, reinforced
    banner_grommets: Optional[str] = None  # none, corners, every_2ft, every_3ft, custom
    banner_grommet_count: Optional[int] = None
    banner_pole_pockets: Optional[str] = None  # none, top, top_and_bottom, side_pockets
    banner_reinforced_corners: Optional[bool] = None
    banner_wind_slits: Optional[bool] = None
    banner_specialty_sewing: Optional[bool] = None
    banner_double_sided: Optional[str] = None  # no, same, different
    banner_event_premium: Optional[bool] = None
    banner_hardware_keys: List[str] = Field(default_factory=list)
    
    # Services
    service_type: Optional[ServiceType] = None
    estimated_hours: Optional[float] = None
    hourly_rate_override: Optional[float] = None
    num_workers: int = 1
    location_address: Optional[str] = None
    distance_miles: Optional[float] = None
    equipment_required: List[str] = Field(default_factory=list)
    
    # Apparel
    apparel_type: Optional[ApparelType] = None
    apparel_brand: Optional[str] = None
    transfer_type: Optional[TransferType] = None
    print_locations: List[str] = Field(default_factory=list)
    num_print_locations: int = 1
    ink_colors: List[str] = Field(default_factory=list)
    size_range: str = "S-XL"
    blank_cost_override: Optional[float] = None
    
    # Vehicle Graphics
    vehicle_type: Optional[VehicleType] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    coverage_type: Optional[CoverageType] = None
    estimated_vehicle_sqft: Optional[float] = None
    install_difficulty: int = 5
    include_design: bool = False
    rush_order: bool = False
    
    # Price override
    price_override: Optional[float] = None
    override_enabled: bool = False


# ============== ENHANCED JOB ITEM ==============
class JobItemEnhanced(BaseModel):
    """Enhanced Job Item with full pricing calculator support"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None
    
    pricing_category: PricingCategory = PricingCategory.CUSTOM
    pricing_data: Optional[JobItemPricingData] = None
    pricing_calculation: Optional[PricingCalculation] = None
    
    unit_price: float = 0
    line_total: float = 0
    production_cost: float = 0
    
    artwork_url: Optional[str] = None
    proof_url: Optional[str] = None
    proof_approved: bool = False
    
    is_taxable: bool = True
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class JobItemEnhancedCreate(BaseModel):
    """Create input for enhanced job item"""
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None
    pricing_category: PricingCategory = PricingCategory.CUSTOM
    pricing_data: Optional[JobItemPricingData] = None
    unit_price: Optional[float] = None
    artwork_url: Optional[str] = None
    proof_url: Optional[str] = None
    proof_approved: bool = False
    is_taxable: bool = True

class JobItemEnhancedUpdate(BaseModel):
    """Update input for enhanced job item"""
    item_type: Optional[JobItemType] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    status: Optional[JobItemStatus] = None
    notes: Optional[str] = None
    pricing_category: Optional[PricingCategory] = None
    pricing_data: Optional[JobItemPricingData] = None
    unit_price: Optional[float] = None
    artwork_url: Optional[str] = None
    proof_url: Optional[str] = None
    proof_approved: Optional[bool] = None
    is_taxable: Optional[bool] = None


# ============== PRICING TEMPLATES ==============
class PricingTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    category: PricingCategory
    pricing_data: Dict[str, Any]
    quantity: int = 1
    is_favorite: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PricingTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: PricingCategory
    pricing_data: Dict[str, Any]
    quantity: int = 1


# ============== PRICING API MODELS ==============
class PriceCalculateRequest(BaseModel):
    category: PricingCategory
    pricing_data: Dict[str, Any]
    quantity: int = 1
