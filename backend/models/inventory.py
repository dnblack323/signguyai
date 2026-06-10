"""Inventory, material-requirement, and manual-purchasing models."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field, model_validator


def _id() -> str:
    return str(uuid.uuid4())


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TrackingMethod(str, Enum):
    QUANTITY = "quantity"
    ROLL = "roll"
    SHEET = "sheet"
    REMNANT = "remnant"
    PACK = "pack"


class InventoryTransactionType(str, Enum):
    RECEIPT = "receipt"
    RESERVATION = "reservation"
    RESERVATION_RELEASE = "reservation_release"
    MATERIAL_PULL = "material_pull"
    CONSUMPTION = "consumption"
    WASTE = "waste"
    RETURN = "return"
    TRANSFER = "transfer"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    CYCLE_COUNT_ADJUSTMENT = "cycle_count_adjustment"


class InventoryAlias(BaseModel):
    id: str = Field(default_factory=_id)
    vendor_id: Optional[str] = None
    supplier_name: str = ""
    supplier_sku: str = ""
    supplier_product_name: str = ""
    manufacturer_sku: str = ""
    nickname: str = ""
    pack_quantity: float = Field(default=1, gt=0)
    last_known_cost: float = Field(default=0, ge=0)
    last_updated_at: Optional[str] = None


class InventoryItemInput(BaseModel):
    sku: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = "other"
    tracking_method: TrackingMethod = TrackingMethod.QUANTITY
    manufacturer: str = ""
    manufacturer_part_number: str = ""
    base_unit: str = "each"
    reorder_point: float = Field(default=0, ge=0)
    preferred_stock_level: float = Field(default=0, ge=0)
    pricing_material_key: Optional[str] = None
    aliases: List[InventoryAlias] = Field(default_factory=list)
    is_active: bool = True
    notes: str = ""


class InventoryItem(InventoryItemInput):
    id: str = Field(default_factory=_id)
    tenant_id: str
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class InventoryLocationInput(BaseModel):
    name: str = Field(min_length=1)
    code: str = ""
    location_type: str = "bin"
    parent_id: Optional[str] = None
    is_active: bool = True
    notes: str = ""


class InventoryLocation(InventoryLocationInput):
    id: str = Field(default_factory=_id)
    tenant_id: str
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class InventoryLotInput(BaseModel):
    item_id: str
    location_id: Optional[str] = None
    lot_number: str = ""
    quantity_on_hand: float = 0
    reserved_quantity: float = 0
    unit_cost: float = Field(default=0, ge=0)
    width_inches: Optional[float] = Field(default=None, ge=0)
    length_inches: Optional[float] = Field(default=None, ge=0)
    remaining_length_inches: Optional[float] = Field(default=None, ge=0)
    sheet_width_inches: Optional[float] = Field(default=None, ge=0)
    sheet_height_inches: Optional[float] = Field(default=None, ge=0)
    thickness: str = ""
    pack_size: float = Field(default=1, gt=0)
    source_purchase_order_id: Optional[str] = None
    parent_lot_id: Optional[str] = None
    is_active: bool = True
    notes: str = ""

    @model_validator(mode="after")
    def validate_quantities(self):
        if self.quantity_on_hand < 0 or self.reserved_quantity < 0:
            raise ValueError("Lot quantities cannot be negative")
        if self.reserved_quantity > self.quantity_on_hand:
            raise ValueError("Reserved quantity cannot exceed on-hand quantity")
        return self


class InventoryLot(InventoryLotInput):
    id: str = Field(default_factory=_id)
    tenant_id: str
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)


class MaterialRequirementInput(BaseModel):
    inventory_item_id: str
    required_quantity: float = Field(gt=0)
    unit: str = "each"
    expected_waste_percent: float = Field(default=0, ge=0)
    required_width_inches: Optional[float] = None
    required_length_inches: Optional[float] = None
    preferred_lot_id: Optional[str] = None
    source: str = "manual"
    notes: str = ""


class InventoryAdjustmentInput(BaseModel):
    item_id: str
    lot_id: Optional[str] = None
    location_id: Optional[str] = None
    quantity_delta: float
    unit: Optional[str] = None
    reason: str
    unit_cost: Optional[float] = None


class InventoryTransferInput(BaseModel):
    lot_id: str
    destination_location_id: str
    quantity: float = Field(gt=0)
    reason: str


class CycleCountLine(BaseModel):
    item_id: str
    lot_id: Optional[str] = None
    location_id: Optional[str] = None
    actual_quantity: float = Field(ge=0)
    reason: Optional[str] = None


class CycleCountInput(BaseModel):
    name: str = ""
    lines: List[CycleCountLine] = Field(min_length=1)


class MaterialPullInput(BaseModel):
    requirement_id: str
    lot_id: str
    pulled_quantity: float = Field(ge=0)
    consumed_quantity: float = Field(ge=0)
    waste_quantity: float = Field(default=0, ge=0)
    returned_quantity: float = Field(default=0, ge=0)
    waste_reason: str = ""
    create_remnant: bool = False
    remnant_width_inches: Optional[float] = None
    remnant_length_inches: Optional[float] = None
    remnant_location_id: Optional[str] = None
    notes: str = ""


class VendorInput(BaseModel):
    name: str = Field(min_length=1)
    website: str = ""
    account_number: str = ""
    default_shipping_notes: str = ""
    contact_name: str = ""
    email: str = ""
    phone: str = ""
    is_active: bool = True
    notes: str = ""


class PurchaseOrderLineInput(BaseModel):
    inventory_item_id: str
    supplier_sku: str = ""
    description: str = ""
    ordered_quantity: float = Field(gt=0)
    unit: str = "each"
    unit_cost: float = Field(default=0, ge=0)
    shortage_ids: List[str] = Field(default_factory=list)


class PurchaseOrderInput(BaseModel):
    vendor_id: str
    lines: List[PurchaseOrderLineInput] = Field(min_length=1)
    notes: str = ""
    expected_delivery_date: Optional[str] = None


class PurchaseOrderReceiveLine(BaseModel):
    line_id: str
    received_quantity: float = Field(default=0, ge=0)
    damaged_quantity: float = Field(default=0, ge=0)
    missing_quantity: float = Field(default=0, ge=0)
    backordered_quantity: float = Field(default=0, ge=0)
    substituted_quantity: float = Field(default=0, ge=0)
    actual_unit_cost: Optional[float] = Field(default=None, ge=0)
    location_id: Optional[str] = None
    lot_details: Dict[str, Any] = Field(default_factory=dict)
    notes: str = ""


class PurchaseOrderReceiveInput(BaseModel):
    lines: List[PurchaseOrderReceiveLine] = Field(min_length=1)
    notes: str = ""
