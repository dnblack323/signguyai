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
        # ===== Vehicle Wraps Materials =====
        {"id": "vw-calendared", "key": "wrap_standard_calendared", "name": "Standard Calendared Vinyl", "category": "vehicle_wrap_material", "cost_per_unit": 1.50, "cost_per_sqft": 1.50, "sell_rate_per_sqft": 9.0, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-premium-cast", "key": "wrap_premium_cast", "name": "Premium Cast Vinyl", "category": "vehicle_wrap_material", "cost_per_unit": 2.75, "cost_per_sqft": 2.75, "sell_rate_per_sqft": 14.0, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-cast-film", "key": "wrap_cast_film", "name": "Wrap Cast Film", "category": "vehicle_wrap_material", "cost_per_unit": 3.50, "cost_per_sqft": 3.50, "sell_rate_per_sqft": 18.0, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-reflective", "key": "wrap_reflective", "name": "Reflective Vinyl (Wrap)", "category": "vehicle_wrap_material", "cost_per_unit": 5.00, "cost_per_sqft": 5.00, "sell_rate_per_sqft": 24.0, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-etched-frost", "key": "wrap_etched_frost", "name": "Etched / Frost Film", "category": "vehicle_wrap_material", "cost_per_unit": 2.75, "cost_per_sqft": 2.75, "sell_rate_per_sqft": 14.0, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-specialty", "key": "wrap_specialty_media", "name": "Specialty / Custom Vehicle Media", "category": "vehicle_wrap_material", "cost_per_unit": 4.00, "cost_per_sqft": 4.00, "sell_rate_per_sqft": 20.0, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-laminate-gloss", "key": "wrap_laminate_gloss", "name": "Gloss Wrap Laminate", "category": "vehicle_wrap_laminate", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-laminate-matte", "key": "wrap_laminate_matte", "name": "Matte Wrap Laminate", "category": "vehicle_wrap_laminate", "cost_per_unit": 1.25, "cost_per_sqft": 1.25, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-laminate-satin", "key": "wrap_laminate_satin", "name": "Satin Wrap Laminate", "category": "vehicle_wrap_laminate", "cost_per_unit": 1.35, "cost_per_sqft": 1.35, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "vw-window-perf", "key": "wrap_window_perf", "name": "Window Perf Film", "category": "vehicle_wrap_perf", "cost_per_unit": 2.50, "cost_per_sqft": 2.50, "sell_rate_per_sqft": 18.0, "unit_type": "sqft", "compatible_categories": ["vehicle_wraps"], "is_active": True},
        {"id": "apparel-tshirt", "key": "tshirt", "name": "T-Shirt", "category": "apparel", "cost_per_unit": 4.5, "unit_type": "each", "is_active": True},
        {"id": "apparel-hoodie", "key": "hoodie", "name": "Hoodie", "category": "apparel", "cost_per_unit": 18.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-hat", "key": "hat", "name": "Hat/Cap", "category": "apparel", "cost_per_unit": 8.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-polo", "key": "polo", "name": "Polo Shirt", "category": "apparel", "cost_per_unit": 12.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-tank", "key": "tank", "name": "Tank Top", "category": "apparel", "cost_per_unit": 4.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-longsleeve", "key": "longsleeve", "name": "Long Sleeve", "category": "apparel", "cost_per_unit": 7.5, "unit_type": "each", "is_active": True},
        {"id": "apparel-jacket", "key": "jacket", "name": "Jacket", "category": "apparel", "cost_per_unit": 25.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-crewneck", "key": "crewneck", "name": "Crewneck Sweatshirt", "category": "apparel", "cost_per_unit": 15.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-safety-vest", "key": "safety_vest", "name": "Safety Vest", "category": "apparel", "cost_per_unit": 10.0, "unit_type": "each", "is_active": True},
        # ===== Apparel Blank Styles (seeded from uploaded shop pricing) =====
        {"id": "blank-ss-gildan-5000", "key": "blank_ss_gildan_5000", "name": "Short Sleeve Tee — Gildan 5000", "category": "apparel_blank", "subtype": "short_sleeve_tee", "brand": "Gildan 5000", "cost_per_unit": 3.25, "retail_base_no_print": 7.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-ss-bella-3001", "key": "blank_ss_bella_3001", "name": "Short Sleeve Tee — Bella+Canvas 3001", "category": "apparel_blank", "subtype": "short_sleeve_tee", "brand": "Bella+Canvas 3001", "cost_per_unit": 5.00, "retail_base_no_print": 9.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-ls-gildan-2400", "key": "blank_ls_gildan_2400", "name": "Long Sleeve Tee — Gildan 2400", "category": "apparel_blank", "subtype": "long_sleeve_tee", "brand": "Gildan 2400", "cost_per_unit": 6.00, "retail_base_no_print": 10.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-ls-bella-3501", "key": "blank_ls_bella_3501", "name": "Long Sleeve Tee — Bella+Canvas 3501", "category": "apparel_blank", "subtype": "long_sleeve_tee", "brand": "Bella+Canvas 3501", "cost_per_unit": 8.00, "retail_base_no_print": 12.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-cn-gildan-18000", "key": "blank_cn_gildan_18000", "name": "Crewneck — Gildan 18000", "category": "apparel_blank", "subtype": "crewneck", "brand": "Gildan 18000", "cost_per_unit": 9.00, "retail_base_no_print": 13.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-cn-bella-3901", "key": "blank_cn_bella_3901", "name": "Crewneck — Bella+Canvas 3901", "category": "apparel_blank", "subtype": "crewneck", "brand": "Bella+Canvas 3901", "cost_per_unit": 11.00, "retail_base_no_print": 15.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-hd-gildan-18500", "key": "blank_hd_gildan_18500", "name": "Hoodie — Gildan 18500", "category": "apparel_blank", "subtype": "hoodie", "brand": "Gildan 18500", "cost_per_unit": 13.00, "retail_base_no_print": 18.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-hd-bella-3719", "key": "blank_hd_bella_3719", "name": "Hoodie — Bella+Canvas 3719", "category": "apparel_blank", "subtype": "hoodie", "brand": "Bella+Canvas 3719", "cost_per_unit": 17.00, "retail_base_no_print": 22.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-po-gildan-8800", "key": "blank_po_gildan_8800", "name": "Polo — Gildan 8800", "category": "apparel_blank", "subtype": "polo", "brand": "Gildan 8800", "cost_per_unit": 6.00, "retail_base_no_print": 12.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-po-bella-3415", "key": "blank_po_bella_3415", "name": "Polo — Bella+Canvas 3415", "category": "apparel_blank", "subtype": "polo", "brand": "Bella+Canvas 3415", "cost_per_unit": 8.50, "retail_base_no_print": 14.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-hat-standard", "key": "blank_hat_standard", "name": "Hat — Standard Cap", "category": "apparel_blank", "subtype": "hat_standard", "brand": "Standard Cap", "cost_per_unit": 4.00, "retail_base_no_print": 10.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-hat-premium", "key": "blank_hat_premium", "name": "Hat — Premium Cap", "category": "apparel_blank", "subtype": "hat_premium", "brand": "Premium Cap", "cost_per_unit": 6.00, "retail_base_no_print": 13.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
        {"id": "blank-visor-standard", "key": "blank_visor_standard", "name": "Visor — Standard", "category": "apparel_blank", "subtype": "visor", "brand": "Visor", "cost_per_unit": 4.00, "retail_base_no_print": 10.00, "unit_type": "each", "compatible_categories": ["apparel"], "is_active": True},
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
            "production_minutes_basic": 20.0,
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
            "minimum_charge": 150.0,
            "default_material_keys": ["wrap_standard_calendered", "wrap_laminate_gloss"],
            "default_hardware_keys": [],
            "default_labor_types": ["installation", "design"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
            "lettering_setup_minutes": 60.0,
            # Materials foundation
            "default_wrap_material_key": "wrap_standard_calendered",
            "available_wrap_material_keys": [
                "wrap_standard_calendared",
                "wrap_premium_cast",
                "wrap_cast_film",
                "wrap_reflective",
                "wrap_etched_frost",
                "wrap_specialty_media",
            ],
            "default_wrap_laminate_key": "wrap_laminate_gloss",
            "available_wrap_laminate_keys": [
                "wrap_laminate_gloss",
                "wrap_laminate_matte",
                "wrap_laminate_satin",
            ],
            "window_perf_material_key": "wrap_window_perf",
            # Defaults
            "default_graphic_type": "spot",
            "default_coverage_type": "spot",
            "default_laminate_required_for_prints": True,
            "default_laminate_required_for_lettering": False,
            "default_install_included_by_subtype": {"spot": True, "partial": True, "half": True, "full": True, "custom": True},
            "default_minimum_sell_price": 150.0,
            # Waste by coverage
            "waste_percentage": 12.0,
            "waste_by_coverage": {"spot": 10.0, "partial": 12.0, "half": 12.0, "full": 15.0, "custom": 12.0},
            # Base production labor
            "production_labor_hours_per_sqft": 0.12,
            "min_production_labor_hours_per_item": 1.0,
            # Design/mockup by coverage
            "design_time_by_coverage_hours": {"spot": 0.75, "partial": 1.5, "half": 2.0, "full": 3.0, "custom": 1.5},
            "design_complexity_multipliers": {"simple": 1.0, "medium": 1.25, "complex": 1.5, "extreme": 2.0},
            # Surface prep / removal
            "surface_prep_hours": {"none": 0, "basic": 0.25, "moderate": 0.75, "heavy": 1.5},
            "removal_hours": {"none": 0, "small": 0.5, "partial": 2.0, "full": 4.0},
            "removal_consumables_allowance": 8.0,
            # Install rates
            "install_rate_per_hour": 75.0,
            "install_minimum": 125.0,
            "second_installer_rate_per_hour": 35.0,
            # Install hours by vehicle type + coverage
            "install_hours_by_vehicle_coverage": {
                "car_sedan": {"spot": 0.75, "partial": 3.0, "half": 6.0, "full": 12.0},
                "car_suv": {"spot": 1.0, "partial": 4.0, "half": 7.0, "full": 14.0},
                "pickup": {"spot": 1.0, "partial": 4.0, "half": 7.0, "full": 14.0},
                "van_mini": {"spot": 1.0, "partial": 4.0, "half": 7.0, "full": 14.0},
                "van_cargo": {"spot": 1.5, "partial": 5.0, "half": 9.0, "full": 18.0},
                "van_sprinter": {"spot": 1.5, "partial": 5.0, "half": 9.0, "full": 18.0},
                "box_truck_12ft": {"spot": 1.5, "partial": 6.0, "half": 10.0, "full": 20.0},
                "box_truck_16ft": {"spot": 2.0, "partial": 7.0, "half": 12.0, "full": 24.0},
                "box_truck_24ft": {"spot": 2.5, "partial": 8.5, "half": 14.0, "full": 28.0},
                "trailer": {"spot": 1.5, "partial": 6.0, "half": 10.0, "full": 20.0},
                "semi": {"spot": 3.0, "partial": 10.0, "half": 16.0, "full": 32.0},
                "other": {"spot": 1.0, "partial": 4.0, "half": 7.0, "full": 14.0},
            },
            # Complexity multipliers
            "install_difficulty_multipliers": {"easy": 1.0, "medium": 1.25, "difficult": 1.5, "extreme": 2.0},
            "seam_complexity_multipliers": {"basic": 1.0, "moderate": 1.15, "advanced": 1.3},
            # Package benchmark sell pricing (by vehicle type + coverage)
            "package_pricing_by_vehicle_coverage": {
                "car_sedan": {"spot": 150, "partial": 650, "half": 1400, "full": 2400},
                "car_suv": {"spot": 175, "partial": 750, "half": 1600, "full": 2800},
                "pickup": {"spot": 175, "partial": 750, "half": 1600, "full": 2800},
                "van_mini": {"spot": 175, "partial": 750, "half": 1600, "full": 2800},
                "van_cargo": {"spot": 225, "partial": 950, "half": 2000, "full": 3400},
                "van_sprinter": {"spot": 225, "partial": 950, "half": 2000, "full": 3400},
                "box_truck_12ft": {"spot": 250, "partial": 1100, "half": 2300, "full": 4000},
                "box_truck_16ft": {"spot": 300, "partial": 1300, "half": 2700, "full": 4600},
                "box_truck_24ft": {"spot": 350, "partial": 1500, "half": 3100, "full": 5200},
                "trailer": {"spot": 250, "partial": 1200, "half": 2400, "full": 4200},
                "semi": {"spot": 400, "partial": 1800, "half": 3600, "full": 6000},
                "other": {"spot": 175, "partial": 750, "half": 1600, "full": 2800},
            },
            # Window perf sell pricing
            "window_perf_sell_rate_rear_per_sqft": 18.0,
            "window_perf_sell_rate_side_per_sqft": 20.0,
            "window_perf_scope_area_sqft": {"rear": 18.0, "side": 14.0, "full": 40.0},
            # Rush
            "rush_increase_percent": 30.0,
            # Sell method
            "sell_method": "max_of_package_or_cost_plus",
            # UI/coverage options
            "available_vehicle_type_keys": [
                "car_sedan", "car_suv", "pickup", "van_mini", "van_cargo", "van_sprinter",
                "box_truck_12ft", "box_truck_16ft", "box_truck_24ft", "trailer", "semi", "other",
            ],
            "available_coverage_types": ["spot", "partial", "half", "full", "custom"],
            # Defaults for UI prefill
            "default_install_difficulty": "medium",
            "default_seam_complexity": "basic",
            "default_surface_prep": "none",
            "default_removal_scope": "none",
            "default_design_complexity": "medium",
            "default_second_installer_required": False,
            "default_window_perf_included": False,
            "default_window_perf_scope": "rear",
            "default_install_required": True,
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
            "production_minutes_basic": 20.0,
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
            "production_minutes_basic": 20.0,
            "yard_sign_setup_minutes": 10.0,
            "yard_sign_minutes_per_sign": 2.0,
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
            "production_minutes_basic": 30.0,
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
            "setup_minutes_per_order": 15.0,
            "production_minutes_per_item": 3.0,
            # ===== Decoration method architecture (structural support for all methods) =====
            "default_decoration_method": "htv",
            "available_decoration_methods": [
                "htv",
                "screen_print_transfer",
                "dtf_transfer",
                "direct_screen_print",
                "embroidery",
                "dtg",
                "patch_emblem",
                "sublimation",
                "specialty_custom",
            ],
            # Which methods use the table-based sell path NOW
            "methods_using_shop_table": ["htv", "screen_print_transfer", "dtf_transfer"],
            # Per-method structural config (pricing rules can be expanded later per method)
            "method_config": {
                "htv": {"label": "HTV", "uses_shop_table": True, "default_setup_fee": 10.0, "material_cost_per_color_per_piece": 0.50, "min_sell_per_piece": 0},
                "screen_print_transfer": {"label": "Screen Print Transfer", "uses_shop_table": True, "default_setup_fee": 15.0, "material_cost_per_color_per_piece": 0.35, "min_sell_per_piece": 0},
                "dtf_transfer": {"label": "DTF Transfer", "uses_shop_table": True, "default_setup_fee": 10.0, "material_cost_per_sqin": 0.03, "min_sell_per_piece": 0},
                "direct_screen_print": {"label": "Direct Screen Print", "uses_shop_table": False, "default_setup_fee_per_color": 30.0, "material_cost_per_color_per_piece": 0.25, "min_sell_per_piece": 5.0},
                "embroidery": {"label": "Embroidery", "uses_shop_table": False, "default_setup_fee": 25.0, "cost_per_1k_stitches": 0.75, "default_stitch_count": 6000, "min_sell_per_piece": 6.0},
                "dtg": {"label": "DTG", "uses_shop_table": False, "default_setup_fee": 5.0, "material_cost_per_piece": 2.50, "min_sell_per_piece": 8.0},
                "patch_emblem": {"label": "Patch / Emblem", "uses_shop_table": False, "default_setup_fee": 0.0, "material_cost_per_piece": 3.00, "min_sell_per_piece": 4.0},
                "sublimation": {"label": "Sublimation", "uses_shop_table": False, "default_setup_fee": 10.0, "material_cost_per_sqin": 0.04, "min_sell_per_piece": 5.0},
                "specialty_custom": {"label": "Specialty / Custom", "uses_shop_table": False, "default_setup_fee": 20.0, "material_cost_per_piece": 3.00, "min_sell_per_piece": 6.0},
            },
            # ===== Preloaded product types + brands =====
            "available_product_types": [
                {"key": "short_sleeve_tee", "label": "Short Sleeve Tee", "is_hat": False, "allowed_placement_set": "garment"},
                {"key": "long_sleeve_tee", "label": "Long Sleeve Tee", "is_hat": False, "allowed_placement_set": "garment"},
                {"key": "crewneck", "label": "Crewneck Sweatshirt", "is_hat": False, "allowed_placement_set": "garment"},
                {"key": "hoodie", "label": "Hoodie", "is_hat": False, "allowed_placement_set": "garment"},
                {"key": "polo", "label": "Polo", "is_hat": False, "allowed_placement_set": "garment"},
                {"key": "hat_standard", "label": "Standard Cap", "is_hat": True, "allowed_placement_set": "hat"},
                {"key": "hat_premium", "label": "Premium Cap", "is_hat": True, "allowed_placement_set": "hat"},
                {"key": "visor", "label": "Visor", "is_hat": True, "allowed_placement_set": "hat"},
            ],
            # Brand/style options per product type (for UI select; Foundation admin can add more)
            "available_brand_styles": {
                "short_sleeve_tee": [
                    {"key": "blank_ss_gildan_5000", "label": "Gildan 5000"},
                    {"key": "blank_ss_bella_3001", "label": "Bella+Canvas 3001"},
                ],
                "long_sleeve_tee": [
                    {"key": "blank_ls_gildan_2400", "label": "Gildan 2400"},
                    {"key": "blank_ls_bella_3501", "label": "Bella+Canvas 3501"},
                ],
                "crewneck": [
                    {"key": "blank_cn_gildan_18000", "label": "Gildan 18000"},
                    {"key": "blank_cn_bella_3901", "label": "Bella+Canvas 3901"},
                ],
                "hoodie": [
                    {"key": "blank_hd_gildan_18500", "label": "Gildan 18500"},
                    {"key": "blank_hd_bella_3719", "label": "Bella+Canvas 3719"},
                ],
                "polo": [
                    {"key": "blank_po_gildan_8800", "label": "Gildan 8800"},
                    {"key": "blank_po_bella_3415", "label": "Bella+Canvas 3415"},
                ],
                "hat_standard": [{"key": "blank_hat_standard", "label": "Standard Cap"}],
                "hat_premium": [{"key": "blank_hat_premium", "label": "Premium Cap"}],
                "visor": [{"key": "blank_visor_standard", "label": "Visor"}],
            },
            # ===== Placement sets =====
            "placement_sets": {
                "garment": [
                    {"key": "front", "label": "Front Small"},
                    {"key": "back", "label": "Back Large"},
                    {"key": "front_back", "label": "Front + Back"},
                ],
                "hat": [
                    {"key": "front", "label": "Front Only"},
                    {"key": "side_back", "label": "Side / Back Only"},
                    {"key": "front_side_back", "label": "Front + Side/Back"},
                ],
            },
            # ===== Quantity tier boundaries =====
            "quantity_tiers": [
                {"key": "1_4", "min_qty": 1, "max_qty": 4, "label": "1–4"},
                {"key": "5_24", "min_qty": 5, "max_qty": 24, "label": "5–24"},
                {"key": "25_49", "min_qty": 25, "max_qty": 49, "label": "25–49"},
                {"key": "50_99", "min_qty": 50, "max_qty": 99, "label": "50–99"},
                {"key": "100_plus", "min_qty": 100, "max_qty": None, "label": "100+"},
            ],
            # ===== Shop pricing table (suggested sell per piece by product × brand × tier × placement) =====
            "shop_pricing_table": {
                "blank_ss_gildan_5000": {
                    "1_4":    {"front": 12.00, "back": 13.50, "front_back": 17.00},
                    "5_24":   {"front": 10.50, "back": 12.00, "front_back": 15.00},
                    "25_49":  {"front":  9.00, "back": 10.50, "front_back": 14.00},
                    "50_99":  {"front":  8.25, "back":  9.50, "front_back": 13.00},
                    "100_plus": {"front": 7.75, "back":  9.00, "front_back": 12.50},
                },
                "blank_ss_bella_3001": {
                    "1_4":    {"front": 14.00, "back": 15.50, "front_back": 19.00},
                    "5_24":   {"front": 12.50, "back": 14.00, "front_back": 17.00},
                    "25_49":  {"front": 11.00, "back": 12.50, "front_back": 16.00},
                    "50_99":  {"front": 10.25, "back": 11.75, "front_back": 15.00},
                    "100_plus": {"front": 9.75, "back": 11.25, "front_back": 14.50},
                },
                "blank_ls_gildan_2400": {
                    "1_4":    {"front": 15.00, "back": 16.50, "front_back": 20.00},
                    "5_24":   {"front": 13.50, "back": 15.00, "front_back": 18.00},
                    "25_49":  {"front": 12.00, "back": 13.50, "front_back": 17.00},
                    "50_99":  {"front": 11.25, "back": 12.50, "front_back": 16.00},
                    "100_plus": {"front": 10.75, "back": 12.00, "front_back": 15.50},
                },
                "blank_ls_bella_3501": {
                    "1_4":    {"front": 17.00, "back": 18.50, "front_back": 22.00},
                    "5_24":   {"front": 15.50, "back": 17.00, "front_back": 20.00},
                    "25_49":  {"front": 14.00, "back": 15.50, "front_back": 19.00},
                    "50_99":  {"front": 13.25, "back": 14.75, "front_back": 18.00},
                    "100_plus": {"front": 12.75, "back": 14.25, "front_back": 17.50},
                },
                "blank_cn_gildan_18000": {
                    "1_4":    {"front": 18.00, "back": 19.50, "front_back": 23.00},
                    "5_24":   {"front": 16.50, "back": 18.00, "front_back": 21.00},
                    "25_49":  {"front": 15.00, "back": 16.50, "front_back": 20.00},
                    "50_99":  {"front": 14.25, "back": 15.50, "front_back": 19.00},
                    "100_plus": {"front": 13.75, "back": 15.00, "front_back": 18.50},
                },
                "blank_cn_bella_3901": {
                    "1_4":    {"front": 20.00, "back": 21.50, "front_back": 25.00},
                    "5_24":   {"front": 18.50, "back": 20.00, "front_back": 23.00},
                    "25_49":  {"front": 17.00, "back": 18.50, "front_back": 22.00},
                    "50_99":  {"front": 16.25, "back": 17.75, "front_back": 21.00},
                    "100_plus": {"front": 15.75, "back": 17.25, "front_back": 20.50},
                },
                "blank_hd_gildan_18500": {
                    "1_4":    {"front": 23.00, "back": 24.50, "front_back": 28.00},
                    "5_24":   {"front": 21.50, "back": 23.00, "front_back": 26.00},
                    "25_49":  {"front": 20.00, "back": 21.50, "front_back": 25.00},
                    "50_99":  {"front": 19.25, "back": 20.50, "front_back": 24.00},
                    "100_plus": {"front": 18.75, "back": 20.00, "front_back": 23.50},
                },
                "blank_hd_bella_3719": {
                    "1_4":    {"front": 25.00, "back": 26.50, "front_back": 30.00},
                    "5_24":   {"front": 23.50, "back": 25.00, "front_back": 28.00},
                    "25_49":  {"front": 22.00, "back": 23.50, "front_back": 27.00},
                    "50_99":  {"front": 21.25, "back": 22.75, "front_back": 26.00},
                    "100_plus": {"front": 20.75, "back": 22.25, "front_back": 25.50},
                },
                "blank_po_gildan_8800": {
                    "1_4":    {"front": 14.00, "back": 15.50, "front_back": 19.00},
                    "5_24":   {"front": 12.50, "back": 14.00, "front_back": 17.00},
                    "25_49":  {"front": 11.00, "back": 12.50, "front_back": 16.00},
                    "50_99":  {"front": 10.25, "back": 11.75, "front_back": 15.00},
                    "100_plus": {"front": 9.75, "back": 11.25, "front_back": 14.50},
                },
                "blank_po_bella_3415": {
                    "1_4":    {"front": 16.00, "back": 17.50, "front_back": 21.00},
                    "5_24":   {"front": 14.50, "back": 16.00, "front_back": 19.00},
                    "25_49":  {"front": 13.00, "back": 14.50, "front_back": 18.00},
                    "50_99":  {"front": 12.25, "back": 13.75, "front_back": 17.00},
                    "100_plus": {"front": 11.75, "back": 13.25, "front_back": 16.50},
                },
                "blank_hat_standard": {
                    "1_4":    {"front": 12.00, "side_back": 13.00, "front_side_back": 15.00},
                    "5_24":   {"front": 11.00, "side_back": 12.00, "front_side_back": 14.00},
                    "25_49":  {"front": 10.00, "side_back": 11.00, "front_side_back": 13.00},
                    "50_99":  {"front":  9.50, "side_back": 10.50, "front_side_back": 12.50},
                    "100_plus": {"front": 9.00, "side_back": 10.00, "front_side_back": 12.00},
                },
                "blank_hat_premium": {
                    "1_4":    {"front": 14.00, "side_back": 15.00, "front_side_back": 17.00},
                    "5_24":   {"front": 13.00, "side_back": 14.00, "front_side_back": 16.00},
                    "25_49":  {"front": 12.00, "side_back": 13.00, "front_side_back": 15.00},
                    "50_99":  {"front": 11.50, "side_back": 12.50, "front_side_back": 14.50},
                    "100_plus": {"front": 11.00, "side_back": 12.00, "front_side_back": 14.00},
                },
                "blank_visor_standard": {
                    "1_4":    {"front": 12.00, "side_back": 13.00, "front_side_back": 15.00},
                    "5_24":   {"front": 11.00, "side_back": 12.00, "front_side_back": 14.00},
                    "25_49":  {"front": 10.00, "side_back": 11.00, "front_side_back": 13.00},
                    "50_99":  {"front":  9.50, "side_back": 10.50, "front_side_back": 12.50},
                    "100_plus": {"front": 9.00, "side_back": 10.00, "front_side_back": 12.00},
                },
            },
            # ===== Add-ons =====
            "plus_size_upcharge_per_x": 2.00,
            "custom_name_number_garment": 4.00,
            "custom_name_number_hat": 3.00,
            "specialty_finish_garment": 2.00,
            "specialty_vinyl_hat": 1.50,
            "two_tone_hat_finish": 1.50,
            "leather_patch_hat": 2.50,
            "bag_and_fold_each": 1.00,
            "basic_setup_fee": 10.00,
            "complex_layout_fee_min": 20.00,
            "complex_layout_fee_max": 30.00,
            "rush_percent_min": 15.0,
            "rush_percent_max": 20.0,
            "default_rush_percent": 17.5,
            # ===== Defaults / fallbacks =====
            "default_artwork_ready": False,
            "default_artwork_needed": False,
            "default_design_complexity": "simple",
            "default_setup_fee": 10.0,
            "design_complexity_setup_fees": {"simple": 10.0, "medium": 20.0, "complex": 25.0, "extreme": 30.0},
            "default_minimum_sell_price": 10.0,
            "apparel_labor_minutes_per_piece": 1.5,
            "apparel_handling_labor_minutes_per_piece": 0.5,
        },
        "services": {
            "label": "Services",
            "default_markup_multiplier": 1.8,
            "target_profit_margin_percent": 35.0,
            "minimum_charge": 25.0,
            "default_material_keys": ["misc_material"],
            "default_hardware_keys": [],
            "default_labor_types": ["production"],
            "sell_rate_defaults": {},
            "ai_prefill_overrides": {},
            # ===== Service Type Library =====
            "default_service_type": "general_labor",
            "available_service_types": [
                {"key": "graphic_design", "label": "Graphic Design", "default_billing_unit": "hour", "default_labor_role": "design", "default_suggested_sell_per_hour": 95.0, "default_flat_fee": None, "default_minimum_charge": 25.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "artwork_setup", "label": "Artwork Setup", "default_billing_unit": "flat", "default_labor_role": "design", "default_suggested_sell_per_hour": 85.0, "default_flat_fee": 25.0, "default_minimum_charge": 25.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "file_cleanup", "label": "File Cleanup", "default_billing_unit": "flat", "default_labor_role": "design", "default_suggested_sell_per_hour": 85.0, "default_flat_fee": 25.0, "default_minimum_charge": 25.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "consultation", "label": "Consultation", "default_billing_unit": "hour", "default_labor_role": "project_management", "default_suggested_sell_per_hour": 95.0, "default_flat_fee": 50.0, "default_minimum_charge": 50.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "site_survey", "label": "Site Survey", "default_billing_unit": "flat", "default_labor_role": "installer", "default_suggested_sell_per_hour": 95.0, "default_flat_fee": 125.0, "default_minimum_charge": 125.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "measurement", "label": "Measurement", "default_billing_unit": "flat", "default_labor_role": "installer", "default_suggested_sell_per_hour": 85.0, "default_flat_fee": 75.0, "default_minimum_charge": 75.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "delivery", "label": "Delivery", "default_billing_unit": "trip", "default_labor_role": "helper", "default_suggested_sell_per_hour": 65.0, "default_flat_fee": 45.0, "default_minimum_charge": 45.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "installation", "label": "Installation", "default_billing_unit": "hour", "default_labor_role": "installer", "default_suggested_sell_per_hour": 95.0, "default_flat_fee": None, "default_minimum_charge": 125.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "removal", "label": "Removal", "default_billing_unit": "hour", "default_labor_role": "installer", "default_suggested_sell_per_hour": 85.0, "default_flat_fee": None, "default_minimum_charge": 100.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "maintenance", "label": "Maintenance / Repair", "default_billing_unit": "hour", "default_labor_role": "installer", "default_suggested_sell_per_hour": 95.0, "default_flat_fee": None, "default_minimum_charge": 95.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "vehicle_graphics_install", "label": "Vehicle Graphics Install Labor", "default_billing_unit": "hour", "default_labor_role": "installer", "default_suggested_sell_per_hour": 95.0, "default_flat_fee": None, "default_minimum_charge": 125.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "wrap_install", "label": "Wrap Install Labor", "default_billing_unit": "hour", "default_labor_role": "lead_installer", "default_suggested_sell_per_hour": 110.0, "default_flat_fee": None, "default_minimum_charge": 450.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "service_call", "label": "Service Call Labor", "default_billing_unit": "hour", "default_labor_role": "installer", "default_suggested_sell_per_hour": 110.0, "default_flat_fee": None, "default_minimum_charge": 150.0, "sell_method": "max_of_both", "requires_travel": True, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "project_management", "label": "Project Management", "default_billing_unit": "hour", "default_labor_role": "project_manager", "default_suggested_sell_per_hour": 95.0, "default_flat_fee": None, "default_minimum_charge": 50.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "permit_handling", "label": "Permit Handling", "default_billing_unit": "flat", "default_labor_role": "admin", "default_suggested_sell_per_hour": 85.0, "default_flat_fee": 175.0, "default_minimum_charge": 175.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "equipment_rental", "label": "Equipment / Lift Rental", "default_billing_unit": "day", "default_labor_role": "installer", "default_suggested_sell_per_hour": 0.0, "default_flat_fee": None, "default_minimum_charge": 0.0, "sell_method": "cost_plus", "requires_travel": False, "uses_equipment": True, "typically_subcontracted": False},
                {"key": "subcontracted", "label": "Subcontracted Service", "default_billing_unit": "flat", "default_labor_role": "outsourced", "default_suggested_sell_per_hour": 0.0, "default_flat_fee": None, "default_minimum_charge": 0.0, "sell_method": "pass_through_plus_markup", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": True},
                {"key": "general_labor", "label": "General Labor Service", "default_billing_unit": "hour", "default_labor_role": "production", "default_suggested_sell_per_hour": 75.0, "default_flat_fee": None, "default_minimum_charge": 25.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
                {"key": "specialty_custom", "label": "Specialty / Custom Service", "default_billing_unit": "hour", "default_labor_role": "specialty_technician", "default_suggested_sell_per_hour": 125.0, "default_flat_fee": None, "default_minimum_charge": 50.0, "sell_method": "max_of_both", "requires_travel": False, "uses_equipment": False, "typically_subcontracted": False},
            ],
            # ===== Billing units =====
            "available_billing_units": ["hour", "flat", "piece", "sqft", "linear_foot", "mile", "trip", "day", "custom"],
            # ===== Labor roles + cost rates =====
            "default_labor_role": "production",
            "labor_roles": {
                "design": {"label": "Design", "cost_per_hour": 45.0, "sell_per_hour": 95.0},
                "production": {"label": "Production", "cost_per_hour": 28.0, "sell_per_hour": 75.0},
                "installer": {"label": "Installer", "cost_per_hour": 35.0, "sell_per_hour": 95.0},
                "lead_installer": {"label": "Lead Installer", "cost_per_hour": 45.0, "sell_per_hour": 110.0},
                "helper": {"label": "Helper", "cost_per_hour": 22.0, "sell_per_hour": 55.0},
                "project_manager": {"label": "Project Manager", "cost_per_hour": 45.0, "sell_per_hour": 95.0},
                "admin": {"label": "Admin", "cost_per_hour": 30.0, "sell_per_hour": 75.0},
                "outsourced": {"label": "Outsourced / Subcontracted", "cost_per_hour": 0.0, "sell_per_hour": 0.0},
                "specialty_technician": {"label": "Specialty Technician", "cost_per_hour": 55.0, "sell_per_hour": 125.0},
            },
            # ===== Complexity =====
            "complexity_multipliers": {"easy": 1.0, "medium": 1.25, "difficult": 1.5, "extreme": 2.0},
            # ===== Travel =====
            "default_travel_enabled": False,
            "travel_cost_per_mile": 0.65,
            "travel_sell_rate_per_mile": 1.25,
            "trip_charge_default": 45.0,
            "trip_charge_cost": 0.0,  # cost side (cost of a trip; 0 means pure sell add)
            # ===== Equipment =====
            "default_equipment_enabled": False,
            "equipment_cost_per_day": 150.0,
            "equipment_sell_rate_per_day": 225.0,
            "equipment_library": [
                {"key": "scissor_lift", "label": "Scissor Lift", "cost_per_day": 225.0, "sell_per_day": 325.0, "cost_per_hour": 35.0, "sell_per_hour": 55.0},
                {"key": "boom_lift", "label": "Boom Lift", "cost_per_day": 325.0, "sell_per_day": 475.0, "cost_per_hour": 55.0, "sell_per_hour": 80.0},
                {"key": "ladder_rig", "label": "Ladder Rig", "cost_per_day": 50.0, "sell_per_day": 95.0, "cost_per_hour": 15.0, "sell_per_hour": 25.0},
                {"key": "generator", "label": "Generator", "cost_per_day": 80.0, "sell_per_day": 125.0, "cost_per_hour": 15.0, "sell_per_hour": 25.0},
                {"key": "utility_truck", "label": "Utility Truck", "cost_per_day": 120.0, "sell_per_day": 200.0, "cost_per_hour": 25.0, "sell_per_hour": 40.0},
                {"key": "custom", "label": "Custom Equipment", "cost_per_day": 150.0, "sell_per_day": 225.0, "cost_per_hour": 25.0, "sell_per_hour": 45.0},
            ],
            # ===== Subcontract =====
            "default_subcontract_enabled": False,
            "subcontract_markup_percent": 20.0,
            # ===== Rush =====
            "default_rush_enabled": False,
            "rush_percent": 25.0,
            # ===== Minimums =====
            "default_min_billable_quantity": 1.0,
            "default_minimum_sell_price": 25.0,
            "design_setup_minimum": 25.0,
            "service_call_minimum": 50.0,
            "install_minimum": 125.0,
            "minimum_trip_charge": 45.0,
            # ===== Sell method =====
            "default_sell_method": "max_of_both",
            # ===== AI =====
            "ai_prefill_enabled": True,
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
    
    # Labor configuration
    labor: Dict[str, Any] = Field(default_factory=lambda: {
        "shop_labor_rate": 75.0,
        "include_labor_in_price": True,
    })
    
    # Design configuration
    design: Dict[str, Any] = Field(default_factory=lambda: {
        "default_design_rate": 85.0,
        "charge_design_separately": "yes",
        "included_design_minutes": 30.0,
    })
    
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
# ============== PHASE 2: STANDARDIZED BREAKDOWN MODELS ==============

class CostLineItem(BaseModel):
    """Individual cost component for itemized breakdown (Phase 2)"""
    name: str
    quantity: float = 1.0
    unit: str = "each"
    unit_cost: float = 0.0
    total_cost: float = 0.0
    notes: Optional[str] = None


class PricingBreakdown(BaseModel):
    """Standardized breakdown structure (Phase 2)"""
    materials: List[CostLineItem] = Field(default_factory=list)
    labor: List[CostLineItem] = Field(default_factory=list)
    design: List[CostLineItem] = Field(default_factory=list)
    setup: List[CostLineItem] = Field(default_factory=list)
    finishing: List[CostLineItem] = Field(default_factory=list)
    hardware: List[CostLineItem] = Field(default_factory=list)
    install: List[CostLineItem] = Field(default_factory=list)
    outsourcing: List[CostLineItem] = Field(default_factory=list)
    overhead: List[CostLineItem] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PricingCalculation(BaseModel):
    """Detailed pricing breakdown for a job item (Phase 2: Standardized)"""
    
    # ========== ITEMIZED COSTS (Top-Level) ==========
    material_cost: float = 0
    labor_cost: float = 0              # Production labor only
    design_cost: float = 0             # NEW (Phase 2): Design/artwork labor
    setup_cost: float = 0
    finishing_cost: float = 0          # NEW (Phase 2): Laminates, finishes
    hardware_cost: float = 0           # NEW (Phase 2): Grommets, stakes, mounts
    install_cost: float = 0            # NEW (Phase 2): Installation labor
    outsourcing_cost: float = 0        # NEW (Phase 2): Subcontract, permits
    overhead_cost: float = 0
    
    # ========== LEGACY FIELD (Backward Compat) ==========
    additional_costs: float = 0        # Deprecated, kept for compatibility
    
    # ========== CALCULATED TOTALS ==========
    # Corrected cost structure:
    # base_cost = sum of all itemized costs (before overhead)
    # overhead_cost = overhead applied to base_cost
    # true_cost = base_cost + overhead_cost
    # production_cost = true_cost (alias)
    base_cost: float = 0               # NEW (Phase 2): Sum before overhead
    true_cost: float = 0               # NEW (Phase 2): base_cost + overhead
    production_cost: float = 0         # Alias for true_cost
    total_cost: float = 0              # Legacy alias
    suggested_price: float = 0
    selling_price: float = 0
    
    # ========== PROFIT METRICS ==========
    profit_amount: float = 0
    profit_margin_percent: float = 0
    markup_percent: float = 0
    
    # ========== METADATA ==========
    estimated_labor_minutes: float = 0
    minimum_charge_applied: bool = False   # NEW (Phase 2)
    pricing_method_used: str = "cost_plus" # NEW (Phase 2)
    
    # ========== STRUCTURED BREAKDOWN ==========
    breakdown: Dict[str, Any] = Field(default_factory=dict)  # Keep dict for backward compat


# ============== JOB ITEM PRICING DATA ==============
class JobItemPricingData(BaseModel):
    """Category-specific pricing inputs for a job item"""
    category: PricingCategory = PricingCategory.CUSTOM
    complexity: int = 1  # Default to 1 (simple), not 5
    
    # Setup fee control - ONE TIME per order, optional
    include_setup_fee: bool = False
    setup_fee: Optional[float] = None
    
    # --- DIMENSIONS (Phase 1: Canonical + Legacy Fields) ---
    # CANONICAL FIELDS (use these going forward):
    width_inches: Optional[float] = None    # Width in inches (canonical)
    height_inches: Optional[float] = None   # Height in inches (canonical, added Phase 1)
    area_sqft: Optional[float] = None       # Area in square feet (canonical, added Phase 1)
    
    # LEGACY FIELDS (kept for backward compatibility, normalized via _normalize_pricing_payload):
    length_inches: Optional[float] = None   # Legacy: maps to height_inches
    square_footage: Optional[float] = None  # Legacy: maps to area_sqft
    # Note: Frontend may also send "width" or "height" (normalized to width_inches/height_inches)
    
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

    # Services — Foundation-driven fields
    services_billing_unit: Optional[str] = None  # hour, flat, piece, sqft, linear_foot, mile, trip, day, custom
    services_labor_role: Optional[str] = None
    services_flat_fee: Optional[float] = None
    services_unit_rate_override: Optional[float] = None
    services_complexity: Optional[str] = None  # easy, medium, difficult, extreme
    services_minimum_applies: Optional[bool] = None
    services_travel_required: Optional[bool] = None
    services_travel_miles: Optional[float] = None
    services_trip_charge_applies: Optional[bool] = None
    services_trip_count: Optional[int] = None
    services_equipment_required: Optional[bool] = None
    services_equipment_type: Optional[str] = None
    services_equipment_days: Optional[float] = None
    services_equipment_hours: Optional[float] = None
    services_subcontracted: Optional[bool] = None
    services_subcontract_cost: Optional[float] = None
    services_subcontract_markup_applies: Optional[bool] = None
    services_permit_external_fee: Optional[float] = None
    services_manual_quote_override: Optional[float] = None
    services_minimum_override: Optional[float] = None
    # Field provenance hint — list of JobItemPricingData attribute names
    # whose values were injected by AI prefill. Used by calculate_services to
    # tag breakdown.field_sources for UI source labels.
    ai_prefilled_fields: Optional[List[str]] = None
    # HMAC signature over (tenant_id | user_id | sorted ai_prefilled_fields)
    # produced by /api/ai/services-prefill. If present and valid, the
    # calculator trusts the ai_prefilled_fields claim. Unsigned or forged
    # claims are ignored (silently downgraded to `user_entered`).
    ai_prefill_signature: Optional[str] = None
    
    # Apparel
    apparel_type: Optional[ApparelType] = None
    apparel_brand: Optional[str] = None
    transfer_type: Optional[TransferType] = None
    print_locations: List[str] = Field(default_factory=list)
    num_print_locations: int = 1
    ink_colors: List[str] = Field(default_factory=list)
    size_range: str = "S-XL"
    blank_cost_override: Optional[float] = None

    # Apparel — Foundation-driven fields
    apparel_product_type: Optional[str] = None  # short_sleeve_tee, long_sleeve_tee, crewneck, hoodie, polo, hat_standard, hat_premium, visor
    apparel_brand_style_key: Optional[str] = None  # e.g. blank_ss_gildan_5000
    apparel_garment_color: Optional[str] = None
    apparel_placement_set: Optional[str] = None  # front, back, front_back (garments) | front, side_back, front_side_back (hats)
    apparel_decoration_method: Optional[str] = None  # htv, screen_print_transfer, dtf_transfer, direct_screen_print, embroidery, dtg, patch_emblem, sublimation, specialty_custom
    apparel_decoration_subtype: Optional[str] = None
    apparel_plus_size_count: Optional[int] = None
    apparel_custom_name_number: Optional[bool] = None
    apparel_custom_name_number_count: Optional[int] = None
    apparel_specialty_finish: Optional[bool] = None
    apparel_two_tone_hat_finish: Optional[bool] = None
    apparel_leather_patch: Optional[bool] = None
    apparel_bag_and_fold: Optional[bool] = None
    apparel_num_colors: Optional[int] = None
    apparel_stitch_count: Optional[int] = None
    apparel_rush_percent: Optional[float] = None
    apparel_manual_quote_override: Optional[float] = None
    
    # Vehicle Graphics
    vehicle_type: Optional[VehicleType] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    coverage_type: Optional[CoverageType] = None
    custom_coverage_percent: Optional[float] = None
    estimated_vehicle_sqft: Optional[float] = None
    install_difficulty: int = 5
    include_design: bool = False
    rush_order: bool = False

    # Vehicle Wraps — foundation-driven fields
    wrap_material_key: Optional[str] = None
    wrap_laminate_required: Optional[bool] = None
    wrap_laminate_type_key: Optional[str] = None
    window_perf_included: Optional[bool] = None
    window_perf_scope: Optional[str] = None  # rear, side, full
    surface_prep_level: Optional[str] = None  # none, basic, moderate, heavy
    removal_scope: Optional[str] = None  # none, small, partial, full
    install_difficulty_level: Optional[str] = None  # easy, medium, difficult, extreme
    seam_complexity: Optional[str] = None  # basic, moderate, advanced
    second_installer_required: Optional[bool] = None
    
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


# ============== CATEGORY COPY REMAP MATRIX ==============
# Universal fields carried across ALL cross-category clones (when user has the carry-over toggle enabled)
UNIVERSAL_CARRY_KEYS = [
    "artwork_notes", "production_notes", "install_notes",
    "shared_reference_links", "design_complexity",
    "artwork_ready", "artwork_needed",
    "rush_order", "due_date",
]

# Per-category "safe" spec keys to carry when source category == target category
CATEGORY_SAFE_KEYS = {
    "apparel": [
        "apparel_product_type", "apparel_brand_style_key", "apparel_garment_color",
        "apparel_placement_set", "apparel_decoration_method", "apparel_decoration_subtype",
        "design_complexity", "artwork_ready", "artwork_needed",
    ],
    "banners": [
        "width", "height", "unit_of_measure", "banner_material_key", "print_sides",
        "hems", "grommets", "pole_pockets", "wind_slits", "reinforced_corners",
    ],
    "rigid_signs": [
        "width", "height", "unit_of_measure", "substrate_material_key", "double_sided",
        "mounting_type", "sides",
    ],
    "digital_print": [
        "width", "height", "unit_of_measure", "print_media_key", "use_type",
        "print_quality_mode", "laminate", "laminate_material_key",
    ],
    "vehicle_wraps": [
        "vehicle_type", "coverage_type", "wrap_material_key",
        "wrap_laminate_required", "wrap_laminate_type_key",
        "window_perf_included", "window_perf_scope",
    ],
    "cut_vinyl": [
        "width", "height", "unit_of_measure", "vinyl_type_key", "num_colors", "surface_type",
    ],
    "services": [
        "service_type", "services_billing_unit", "services_labor_role",
        "services_complexity", "location_address",
    ],
}

# Cross-category remap rules — explicit allow-lists; everything else is dropped
# Format: { source: { target: [keys_to_keep] } }
CATEGORY_COPY_REMAP = {
    "banners": {
        "rigid_signs": ["width", "height", "unit_of_measure", "double_sided", "mounting_type"],
        "digital_print": ["width", "height", "unit_of_measure"],
        "cut_vinyl": ["width", "height", "unit_of_measure"],
    },
    "rigid_signs": {
        "banners": ["width", "height", "unit_of_measure", "double_sided"],
        "digital_print": ["width", "height", "unit_of_measure"],
    },
    "digital_print": {
        "banners": ["width", "height", "unit_of_measure"],
        "rigid_signs": ["width", "height", "unit_of_measure"],
        "vehicle_wraps": ["design_complexity"],
        "cut_vinyl": ["width", "height", "unit_of_measure"],
    },
    "vehicle_wraps": {
        "digital_print": ["design_complexity"],
    },
    "cut_vinyl": {
        "digital_print": ["width", "height", "unit_of_measure"],
        "banners": ["width", "height", "unit_of_measure"],
    },
    "apparel": {},   # apparel → any non-apparel: drop all apparel_* fields
    "services": {},  # services → any non-services: drop all services_* fields
}


def remap_specs_for_category(source_category: str, target_category: str, source_specs: Dict[str, Any], carry_over: Dict[str, bool]) -> Dict[str, Any]:
    """Return a new specs dict containing only keys allowed for the target category.

    Universal keys flow through when their carry_over toggle is True.
    Same-category clones keep everything in CATEGORY_SAFE_KEYS[target].
    Cross-category clones keep only CATEGORY_COPY_REMAP[source][target].
    """
    carry_over = carry_over or {}
    # Normalize historical singular/plural divergence between route handlers
    # (which use `vehicle_wrap`) and CATEGORY_* maps (which use `vehicle_wraps`).
    _alias = {"vehicle_wrap": "vehicle_wraps"}
    source_category = _alias.get(source_category, source_category)
    target_category = _alias.get(target_category, target_category)
    result: Dict[str, Any] = {}

    # Universal keys
    if carry_over.get("artwork_notes", True):
        if source_specs.get("artwork_notes"):
            result["artwork_notes"] = source_specs.get("artwork_notes")
    if carry_over.get("production_notes", True) and source_specs.get("production_notes"):
        result["production_notes"] = source_specs.get("production_notes")
    if carry_over.get("install_location_notes", True) and source_specs.get("install_notes"):
        result["install_notes"] = source_specs.get("install_notes")
    if carry_over.get("design_setup", True):
        for k in ("design_complexity", "artwork_ready", "artwork_needed"):
            if k in source_specs:
                result[k] = source_specs[k]
    if carry_over.get("rush_setting", True) and "rush_order" in source_specs:
        result["rush_order"] = source_specs["rush_order"]
    if carry_over.get("quantity", False) and "quantity" in source_specs:
        result["quantity"] = source_specs["quantity"]
    if carry_over.get("size_breakdown", False):
        for sz in ("size_xs", "size_s", "size_m", "size_l", "size_xl", "size_2xl", "size_3xl", "size_4xl", "size_5xl", "apparel_plus_size_count"):
            if sz in source_specs:
                result[sz] = source_specs[sz]
    if carry_over.get("names_numbers", False):
        for k in ("apparel_custom_name_number", "apparel_custom_name_number_count"):
            if k in source_specs:
                result[k] = source_specs[k]

    # Same-category or cross-category spec keys
    if source_category == target_category:
        for k in CATEGORY_SAFE_KEYS.get(target_category, []):
            if k in source_specs:
                result[k] = source_specs[k]
    else:
        allow = (CATEGORY_COPY_REMAP.get(source_category, {}) or {}).get(target_category, [])
        for k in allow:
            if k in source_specs:
                result[k] = source_specs[k]

    return result
