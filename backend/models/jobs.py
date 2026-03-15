"""
Quote, Job, and Invoice related Pydantic models.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
import uuid

from .enums import (
    QuoteStatus, JobStatus, JobActivityType, JobItemStatus, JobItemType,
    InvoiceStatus, PaymentMethod
)


# ============== QUOTE MODELS ==============
class QuoteLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float
    total: float = 0
    pricing_category: Optional[str] = None
    pricing_data: Optional[Dict[str, Any]] = None
    cost_snapshot: Optional[Dict[str, Any]] = None

class QuoteBase(BaseModel):
    customer_id: str
    line_items: List[QuoteLineItem] = []
    notes: Optional[str] = None
    status: QuoteStatus = QuoteStatus.DRAFT

class QuoteCreate(QuoteBase):
    pass

class QuoteUpdate(BaseModel):
    line_items: Optional[List[QuoteLineItem]] = None
    notes: Optional[str] = None
    status: Optional[QuoteStatus] = None

class Quote(QuoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    total: float = 0
    job_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== JOB LINE ITEM (for quote stage) ==============
class JobLineItem(BaseModel):
    """Line item used in quote stage before conversion to JobItem"""
    description: str
    quantity: float = 1
    unit_price: float = 0
    total: float = 0
    pricing_category: Optional[str] = None
    pricing_data: Optional[Dict[str, Any]] = None
    cost_snapshot: Optional[Dict[str, Any]] = None


# ============== JOB MODELS ==============
class JobBase(BaseModel):
    customer_id: str
    name: str
    description: Optional[str] = None
    status: JobStatus = JobStatus.QUOTE
    due_date: Optional[str] = None
    # Quote-stage fields
    line_items: List[JobLineItem] = []  # Used in quote stage
    notes: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[JobStatus] = None
    due_date: Optional[str] = None
    line_items: Optional[List[JobLineItem]] = None
    notes: Optional[str] = None

class Job(JobBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    invoice_id: Optional[str] = None
    subtotal: float = 0
    total: float = 0  # For quote stage compatibility
    is_archived: bool = False
    sent_at: Optional[str] = None  # When quote was sent
    approved_at: Optional[str] = None  # When quote was approved
    # Legacy field for backward compatibility
    quote_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== JOB NOTE MODELS ==============
class JobNoteBase(BaseModel):
    job_id: str
    content: str
    author: Optional[str] = None

class JobNoteCreate(BaseModel):
    content: str
    author: Optional[str] = None

class JobNote(JobNoteBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== JOB ACTIVITY MODELS ==============
class JobActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    activity_type: JobActivityType
    description: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== JOB ITEM MODELS ==============
class JobItemBase(BaseModel):
    job_id: str
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    unit_price: float = 0
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None
    pricing_category: Optional[str] = None
    pricing_data: Optional[Dict[str, Any]] = None
    cost_snapshot: Optional[Dict[str, Any]] = None
    production_cost: float = 0
    profit_amount: float = 0
    profit_margin_percent: float = 0

class JobItemCreate(BaseModel):
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    unit_price: float = 0
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None
    pricing_category: Optional[str] = None
    pricing_data: Optional[Dict[str, Any]] = None
    cost_snapshot: Optional[Dict[str, Any]] = None
    production_cost: float = 0
    profit_amount: float = 0
    profit_margin_percent: float = 0

class JobItemUpdate(BaseModel):
    item_type: Optional[JobItemType] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    status: Optional[JobItemStatus] = None
    notes: Optional[str] = None
    pricing_category: Optional[str] = None
    pricing_data: Optional[Dict[str, Any]] = None
    cost_snapshot: Optional[Dict[str, Any]] = None
    production_cost: Optional[float] = None
    profit_amount: Optional[float] = None
    profit_margin_percent: Optional[float] = None

class JobItem(JobItemBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    line_total: float = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== JOB TIME TRACKING MODELS ==============
class JobTimeEntryBase(BaseModel):
    """Time entry for tracking work on a specific job"""
    job_id: str
    employee_id: str
    description: Optional[str] = None
    task_type: Optional[str] = None  # design, production, installation, admin

class JobTimeEntryCreate(BaseModel):
    description: Optional[str] = None
    task_type: Optional[str] = "production"

class JobTimeEntryUpdate(BaseModel):
    description: Optional[str] = None
    task_type: Optional[str] = None
    end_time: Optional[str] = None

class JobTimeEntry(JobTimeEntryBase):
    """Complete time entry with all fields"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    employee_name: Optional[str] = None
    start_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_time: Optional[str] = None
    duration_minutes: float = 0
    hourly_rate: float = 0
    labor_cost: float = 0
    is_active: bool = True  # True if currently working
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class JobTimeSummary(BaseModel):
    """Summary of time spent on a job"""
    job_id: str
    total_minutes: float = 0
    total_hours: float = 0
    total_labor_cost: float = 0
    entries_count: int = 0
    by_employee: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    by_task_type: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


# ============== INVOICE MODELS ==============
class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float = 0
    total: float = 0
    job_item_id: Optional[str] = None
    pricing_category: Optional[str] = None
    cost_snapshot: Optional[Dict[str, Any]] = None

class InvoiceBase(BaseModel):
    customer_id: str
    job_id: Optional[str] = None
    line_items: List[InvoiceLineItem] = []
    total: float = 0
    tax_amount: float = 0
    discount_amount: float = 0
    grand_total: float = 0
    amount_paid: float = 0
    status: InvoiceStatus = InvoiceStatus.DRAFT
    notes: Optional[str] = None
    due_date: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceUpdate(BaseModel):
    line_items: Optional[List[InvoiceLineItem]] = None
    total: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    amount_paid: Optional[float] = None
    status: Optional[InvoiceStatus] = None
    notes: Optional[str] = None
    due_date: Optional[str] = None

class Invoice(InvoiceBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
