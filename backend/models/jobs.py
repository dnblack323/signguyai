"""
Quote, Job, and Invoice related Pydantic models.
"""
from typing import Optional, List
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


# ============== JOB MODELS ==============
class JobBase(BaseModel):
    customer_id: str
    name: str
    description: Optional[str] = None
    status: JobStatus = JobStatus.QUOTED
    due_date: Optional[str] = None

class JobCreate(JobBase):
    quote_id: Optional[str] = None

class JobUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[JobStatus] = None
    due_date: Optional[str] = None

class Job(JobBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    quote_id: Optional[str] = None
    invoice_id: Optional[str] = None
    subtotal: float = 0
    is_archived: bool = False
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

class JobItemCreate(BaseModel):
    item_type: JobItemType = JobItemType.OTHER
    description: str
    quantity: float = 1
    unit_price: float = 0
    status: JobItemStatus = JobItemStatus.PENDING
    notes: Optional[str] = None

class JobItemUpdate(BaseModel):
    item_type: Optional[JobItemType] = None
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    status: Optional[JobItemStatus] = None
    notes: Optional[str] = None

class JobItem(JobItemBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    line_total: float = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== INVOICE MODELS ==============
class InvoiceLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float = 0
    total: float = 0
    job_item_id: Optional[str] = None

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
