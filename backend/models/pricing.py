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
    cost_per_unit: float = 0
    unit_type: str = "sqft"
    is_active: bool = True


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
        {"id": "transfer-tape-cost", "key": "transfer_tape", "name": "Transfer Tape Cost Per Sq Ft", "category": "optional", "cost_per_unit": 0.2, "unit_type": "sqft", "is_active": True},
        {"id": "apparel-blank-cost", "key": "apparel_blank", "name": "Apparel Blank Cost Per Item", "category": "material", "cost_per_unit": 5.0, "unit_type": "each", "is_active": True},
        {"id": "apparel-decoration-cost", "key": "apparel_decoration", "name": "Apparel Decoration Cost Per Print", "category": "material", "cost_per_unit": 2.5, "unit_type": "each", "is_active": True},
        {"id": "misc-material-cost", "key": "misc_material", "name": "Custom / Misc Material Cost Per Item", "category": "material", "cost_per_unit": 10.0, "unit_type": "each", "is_active": True},
        {"id": "acrylic-sheet-cost", "key": "acrylic_sheet", "name": "Acrylic Sheet Cost Per Sq Ft", "category": "material", "cost_per_unit": 5.5, "unit_type": "sqft", "is_active": True},
        {"id": "rigid-sign-board-cost", "key": "rigid_sign_board", "name": "Rigid Sign Board Cost Per Sq Ft", "category": "material", "cost_per_unit": 2.85, "unit_type": "sqft", "is_active": True},
    ])
    production_hourly_rate: float = 28.0
    installer_hourly_rate: float = 40.0
    overhead_percentage: float = 15.0
    shop_overhead_per_hour: float = 0.0
    apply_overhead_to_jobs: bool = True
    target_profit_margin_percent: float = 40.0
    default_markup_multiplier: float = 2.5
    category_defaults: Dict[str, Any] = Field(default_factory=lambda: {
        "vehicle_wraps": {
            "label": "Vehicle Wraps",
            "default_labor_hours_per_sqft": 0.12,
            "default_markup_multiplier": 2.4,
            "target_profit_margin_percent": 42.0,
            "minimum_charge": 850.0,
            "default_material_keys": ["vinyl", "laminate", "ink"],
        },
        "banners": {
            "label": "Banners",
            "default_labor_hours_per_sqft": 0.06,
            "default_markup_multiplier": 2.35,
            "target_profit_margin_percent": 40.0,
            "minimum_charge": 35.0,
            "default_material_keys": ["banner_material", "ink"],
        },
        "rigid_signs": {
            "label": "Rigid Signs",
            "default_labor_hours_per_sqft": 0.08,
            "default_markup_multiplier": 2.45,
            "target_profit_margin_percent": 41.0,
            "minimum_charge": 55.0,
            "default_material_keys": ["coroplast", "aluminum_composite", "foam_board", "ink"],
        },
        "cut_vinyl": {
            "label": "Cut Vinyl",
            "default_labor_hours_per_sqft": 0.1,
            "default_markup_multiplier": 2.3,
            "target_profit_margin_percent": 40.0,
            "minimum_charge": 25.0,
            "default_material_keys": ["vinyl", "transfer_tape"],
        },
        "apparel": {
            "label": "Apparel",
            "default_labor_hours_per_unit": 0.08,
            "default_markup_multiplier": 2.15,
            "target_profit_margin_percent": 38.0,
            "minimum_charge": 60.0,
            "default_material_keys": ["apparel_blank", "apparel_decoration"],
        },
        "services": {
            "label": "Services",
            "default_labor_hours": 1.0,
            "default_markup_multiplier": 1.8,
            "target_profit_margin_percent": 35.0,
            "minimum_charge": 75.0,
            "default_material_keys": ["misc_material"],
        },
        "custom": {
            "label": "Custom / Miscellaneous",
            "default_labor_hours_per_unit": 0.25,
            "default_markup_multiplier": 2.25,
            "target_profit_margin_percent": 38.0,
            "minimum_charge": 50.0,
            "default_material_keys": ["misc_material"],
        },
    })
    selling_price_benchmarks: Dict[str, Any] = Field(default_factory=lambda: {
        "vehicle_wraps": {"label": "Vehicle Wraps", "average_sell_price_per_sqft": 18.75, "average_order_total": 2850.0, "minimum_charge": 950.0},
        "banners": {"label": "Banners", "average_sell_price_per_sqft": 8.25, "average_order_total": 245.0, "minimum_charge": 45.0},
        "rigid_signs": {"label": "Rigid Signs", "average_sell_price_per_sqft": 12.4, "average_order_total": 310.0, "minimum_charge": 65.0},
        "cut_vinyl": {"label": "Cut Vinyl", "average_sell_price_per_sqft": 7.5, "average_order_total": 125.0, "minimum_charge": 30.0},
        "apparel": {"label": "Apparel", "average_sell_price_per_unit": 24.0, "average_order_total": 420.0, "minimum_charge": 75.0},
        "services": {"label": "Services", "average_sell_price_per_hour": 110.0, "average_order_total": 240.0, "minimum_charge": 85.0},
        "custom": {"label": "Custom / Miscellaneous", "average_sell_price_per_unit": 75.0, "average_order_total": 280.0, "minimum_charge": 60.0},
    })
    
    # Labor rates
    hourly_rate: float = 75.0
    design_hourly_rate: float = 85.0
    install_hourly_rate: float = 95.0
    
    # Default markups
    default_markup_percent: float = 100.0
    material_markup_percent: float = 50.0
    
    # Minimum charges
    minimum_order: float = 50.0
    minimum_vinyl_charge: float = 25.0
    minimum_print_charge: float = 35.0
    minimum_sign_charge: float = 50.0
    minimum_service_charge: float = 75.0
    minimum_wrap_charge: float = 500.0
    
    # Complexity multipliers
    complexity_multiplier_base: float = 1.0
    complexity_multiplier_max: float = 2.0
    
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
    vinyl_colors: List[str] = Field(default_factory=list)
    num_colors: int = 1
    
    # Digital Print
    print_material: Optional[PrintMaterial] = None
    laminate: bool = False
    laminate_type: Optional[str] = None
    
    # Rigid Signs
    substrate_type: Optional[SubstrateType] = None
    double_sided: bool = False
    
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
