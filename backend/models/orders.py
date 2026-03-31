"""
Order System Data Models

4-layer architecture:
  Order → Job Tickets → Quotes/Invoices → Production Tasks
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


# ============== ENUMS ==============

class OrderStatus(str, Enum):
    DRAFT = "draft"  # Save as draft before submitting
    NEW_INTAKE = "new_intake"
    AWAITING_REVIEW = "awaiting_review"
    AWAITING_QUOTE = "awaiting_quote"
    QUOTE_SENT = "quote_sent"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    IN_PRODUCTION = "in_production"
    PARTIALLY_COMPLETE = "partially_complete"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class OrderSource(str, Enum):
    PHONE = "phone"
    WALK_IN = "walk_in"
    EMAIL = "email"
    WEBSITE = "website"
    REPEAT_ORDER = "repeat_order"
    SALES_REP = "sales_rep"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    DEPOSIT_PAID = "deposit_paid"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    REFUNDED = "refunded"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class PickupDeliveryMethod(str, Enum):
    PICKUP = "pickup"
    DELIVERY = "delivery"
    INSTALL = "install"
    SHIP = "ship"


class JobTicketStatus(str, Enum):
    NEW = "new"
    AWAITING_INFO = "awaiting_info"
    AWAITING_PROOF = "awaiting_proof"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    QUEUED = "queued"
    IN_PRODUCTION = "in_production"
    IN_QC = "in_qc"
    ON_HOLD = "on_hold"
    READY = "ready"
    COMPLETED = "completed"
    REWORK = "rework"
    CANCELLED = "cancelled"


class JobTicketCategory(str, Enum):
    RIGID_SIGNS = "rigid_signs"
    BANNERS = "banners"
    CUT_VINYL = "cut_vinyl"
    VEHICLE_WRAP = "vehicle_wrap"
    APPAREL = "apparel"
    PROMO_MISC = "promo_misc"
    CUSTOM = "custom"


class Priority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    RUSH = "rush"


class TaskStatus(str, Enum):
    NOT_STARTED = "not_started"
    WAITING = "waiting"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    ON_HOLD = "on_hold"
    NEEDS_REVIEW = "needs_review"
    COMPLETE = "complete"
    REWORK = "rework"


class Department(str, Enum):
    DESIGN = "design"
    PRINT = "print"
    CUT_TRIM = "cut_trim"
    LAMINATION = "lamination"
    WEED_MASK = "weed_mask"
    SEWING_FINISHING = "sewing_finishing"
    ASSEMBLY = "assembly"
    APPAREL = "apparel"
    WRAP_PREP = "wrap_prep"
    INSTALL = "install"
    QC_REVIEW = "qc_review"
    PACKAGING = "packaging"
    DELIVERY = "delivery"


class ArtworkStatus(str, Enum):
    NONE = "none"
    RECEIVED = "received"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class ProofApprovalStatus(str, Enum):
    NONE = "none"
    SENT = "sent"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    REJECTED = "rejected"


class QCStatus(str, Enum):
    NONE = "none"
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


# ============== LAYER 1: ORDER ==============

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = ""
    tenant_id: str = ""
    customer_id: str = ""
    customer_name: str = ""
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    company_name: str = ""
    order_source: str = OrderSource.PHONE.value
    date_created: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: str = ""
    requested_due_date: Optional[str] = None
    event_date: Optional[str] = None
    status: str = OrderStatus.NEW_INTAKE.value
    payment_status: str = PaymentStatus.UNPAID.value
    approval_status: str = ApprovalStatus.PENDING.value
    pickup_delivery_method: str = PickupDeliveryMethod.PICKUP.value
    pickup_delivery_notes: str = ""
    internal_notes: str = ""
    customer_notes: str = ""
    linked_quote_ids: List[str] = Field(default_factory=list)
    linked_invoice_ids: List[str] = Field(default_factory=list)
    job_ticket_count: int = 0
    overall_progress: float = 0.0
    final_completion_date: Optional[str] = None
    is_archived: bool = False
    is_active: bool = True
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OrderCreate(BaseModel):
    customer_id: str = ""
    customer_name: str = ""
    contact_name: str = ""
    phone: str = ""
    email: str = ""
    company_name: str = ""
    order_source: str = OrderSource.PHONE.value
    requested_due_date: Optional[str] = None
    event_date: Optional[str] = None
    status: Optional[str] = None  # Allow setting status on create (e.g., 'draft')
    pickup_delivery_method: str = PickupDeliveryMethod.PICKUP.value
    pickup_delivery_notes: str = ""
    internal_notes: str = ""
    customer_notes: str = ""


class OrderUpdate(BaseModel):
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    order_source: Optional[str] = None
    requested_due_date: Optional[str] = None
    event_date: Optional[str] = None
    status: Optional[str] = None
    payment_status: Optional[str] = None
    approval_status: Optional[str] = None
    pickup_delivery_method: Optional[str] = None
    pickup_delivery_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    is_archived: Optional[bool] = None


# ============== LAYER 2: JOB TICKET ==============

class JobTicketSpecs(BaseModel):
    width: str = ""
    height: str = ""
    size_description: str = ""
    material: str = ""
    substrate: str = ""
    color_specs: str = ""
    finish: str = ""
    lamination: str = ""
    grommets: str = ""  # Changed to str to accept "corners", "every_2ft", etc from schema
    hemming: str = ""  # Changed to str for consistency
    mounting_type: str = ""
    install_required: bool = False
    double_sided: str = ""  # Changed to str to accept "single"/"double" from frontend
    sides: int = 1
    print_method: str = ""
    cut_method: str = ""
    # Additional fields from dynamic schemas
    unit_of_measure: str = ""
    indoor_outdoor: str = ""
    hems: str = ""
    pole_pockets: str = ""
    wind_slits: bool = False
    reinforced_corners: bool = False
    sewn_edges: bool = False
    webbing: bool = False
    artwork_provided: bool = False
    proof_rounds: int = 0
    artwork_notes: str = ""
    rush_order: bool = False
    outsourced: bool = False
    hardware_included: bool = False
    packaging_notes: str = ""
    delivery_notes: str = ""
    vinyl_type: str = ""
    num_colors: int = 1

    class Config:
        extra = "allow"  # Allow additional fields from dynamic schemas


class JobTicket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = ""
    order_id: str = ""
    tenant_id: str = ""
    item_name: str = ""
    item_category: str = JobTicketCategory.CUSTOM.value
    item_subcategory: str = ""
    quantity: int = 1
    unit_type: str = "each"
    due_date: Optional[str] = None
    priority: str = Priority.NORMAL.value
    department_route: str = ""
    assigned_team: str = ""
    assigned_user_id: str = ""
    status: str = JobTicketStatus.NEW.value
    production_flow_enabled: bool = False
    specs: JobTicketSpecs = Field(default_factory=JobTicketSpecs)
    design_needed: bool = False
    customer_artwork: bool = False
    artwork_status: str = ArtworkStatus.NONE.value
    proof_required: bool = False
    proof_approval_status: str = ProofApprovalStatus.NONE.value
    revision_count: int = 0
    special_instructions: str = ""
    production_notes: str = ""
    install_notes: str = ""
    packaging_notes: str = ""
    artwork_files: List[str] = Field(default_factory=list)
    reference_images: List[str] = Field(default_factory=list)
    mockups: List[str] = Field(default_factory=list)
    proof_files: List[str] = Field(default_factory=list)
    production_output_files: List[str] = Field(default_factory=list)
    linked_pricing_profile: str = ""
    estimated_price: float = 0.0
    actual_cost: float = 0.0
    labor_estimate: float = 0.0
    material_estimate: float = 0.0
    started_date: Optional[str] = None
    finished_date: Optional[str] = None
    ready_for_qc: bool = False
    qc_status: str = QCStatus.NONE.value
    ready_for_pickup: bool = False
    rework_needed: bool = False
    rework_notes: str = ""
    progress: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JobTicketCreate(BaseModel):
    order_id: str
    item_name: str
    item_category: str = JobTicketCategory.CUSTOM.value
    item_subcategory: str = ""
    quantity: int = 1
    unit_type: str = "each"
    due_date: Optional[str] = None
    priority: str = Priority.NORMAL.value
    department_route: str = ""
    assigned_user_id: str = ""
    production_flow_enabled: bool = False
    specs: Optional[Dict[str, Any]] = None
    design_needed: bool = False
    customer_artwork: bool = False
    proof_required: bool = False
    special_instructions: str = ""
    production_notes: str = ""
    install_notes: str = ""
    packaging_notes: str = ""
    estimated_price: float = 0.0
    labor_estimate: float = 0.0
    material_estimate: float = 0.0


class JobTicketUpdate(BaseModel):
    item_name: Optional[str] = None
    item_category: Optional[str] = None
    item_subcategory: Optional[str] = None
    quantity: Optional[int] = None
    unit_type: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    department_route: Optional[str] = None
    assigned_user_id: Optional[str] = None
    status: Optional[str] = None
    production_flow_enabled: Optional[bool] = None
    specs: Optional[Dict[str, Any]] = None
    design_needed: Optional[bool] = None
    customer_artwork: Optional[bool] = None
    artwork_status: Optional[str] = None
    proof_required: Optional[bool] = None
    proof_approval_status: Optional[str] = None
    special_instructions: Optional[str] = None
    production_notes: Optional[str] = None
    install_notes: Optional[str] = None
    packaging_notes: Optional[str] = None
    estimated_price: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_estimate: Optional[float] = None
    material_estimate: Optional[float] = None
    ready_for_qc: Optional[bool] = None
    qc_status: Optional[str] = None
    ready_for_pickup: Optional[bool] = None
    rework_needed: Optional[bool] = None
    rework_notes: Optional[str] = None


# ============== LAYER 4: PRODUCTION TASK ==============

class TimestampEntry(BaseModel):
    status: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id: str = ""


class ProductionTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    job_ticket_id: str = ""
    tenant_id: str = ""
    task_name: str = ""
    department: str = ""
    stage_sequence: int = 0
    status: str = TaskStatus.NOT_STARTED.value
    assigned_to: str = ""
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    time_tracked_minutes: int = 0
    dependency_task_id: Optional[str] = None
    notes: str = ""
    hold_reason: str = ""
    rework_flag: bool = False
    qc_required: bool = False
    completion_percent: float = 0.0
    depends_on_proof: bool = False
    timestamp_history: List[Dict[str, str]] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProductionTaskUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    notes: Optional[str] = None
    hold_reason: Optional[str] = None
    rework_flag: Optional[bool] = None
    completion_percent: Optional[float] = None


# ============== WORKFLOW TEMPLATE ==============

class WorkflowStage(BaseModel):
    name: str
    department: str
    sequence: int
    required: bool = True
    qc_required: bool = False
    depends_on_proof: bool = False


class WorkflowTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    category: str
    template_name: str
    stages: List[Dict[str, Any]] = Field(default_factory=list)
    is_default: bool = False
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== ACTIVITY LOG ==============

class OrderActivity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    tenant_id: str
    entity_type: str = "order"
    entity_id: str = ""
    action: str = ""
    description: str = ""
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    user_id: str = ""
    user_name: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
