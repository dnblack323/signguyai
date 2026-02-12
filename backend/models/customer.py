"""
Customer and CRM related Pydantic models.
"""
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone
import uuid

from .enums import CustomerStatus, MessageType, ProofStatus, AppointmentType, AppointmentStatus


# ============== CUSTOMER MODELS ==============
class CustomerBase(BaseModel):
    name: str
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: CustomerStatus = CustomerStatus.LEAD
    notes: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_tax_exempt: bool = False
    tax_exempt_document_url: Optional[str] = None
    portal_password_hash: Optional[str] = None
    portal_enabled: bool = False
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "email_messages": True,
        "email_orders": True,
        "email_approvals": True,
        "email_payments": True
    })

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[CustomerStatus] = None
    notes: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_tax_exempt: Optional[bool] = None
    tax_exempt_document_url: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None

class Customer(CustomerBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== PORTAL MODELS ==============
class ConversationMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_type: str  # "customer" or "shop"
    sender_id: str
    sender_name: str
    message_type: MessageType = MessageType.TEXT
    content: str
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    is_read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Conversation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    customer_id: str
    subject: str
    related_job_id: Optional[str] = None
    related_quote_id: Optional[str] = None
    last_message_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_message_preview: str = ""
    unread_customer: int = 0
    unread_shop: int = 0
    is_closed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ArtworkProof(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    job_id: str
    customer_id: str
    version: int = 1
    file_url: str
    file_name: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    status: ProofStatus = ProofStatus.PENDING
    customer_comment: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class CustomerNotification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    customer_id: str
    notification_type: str
    title: str
    message: str
    link: Optional[str] = None
    related_id: Optional[str] = None
    is_read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class Appointment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None
    customer_id: str
    job_id: Optional[str] = None
    appointment_type: AppointmentType = AppointmentType.OTHER
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    title: str
    description: Optional[str] = None
    scheduled_at: str
    duration_minutes: int = 60
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== PORTAL AUTH MODELS ==============
class CustomerPortalLogin(BaseModel):
    email: str
    password: str

class CustomerPortalRegister(BaseModel):
    email: str
    password: str

class CustomerPortalToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    customer_id: str
    customer_name: str

class CustomerProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_tax_exempt: Optional[bool] = None
    tax_exempt_document_url: Optional[str] = None
    notification_preferences: Optional[Dict[str, bool]] = None

class ConversationCreate(BaseModel):
    subject: str
    message: str
    related_job_id: Optional[str] = None
    related_quote_id: Optional[str] = None

class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    message_type: MessageType = MessageType.TEXT

class ProofResponseCreate(BaseModel):
    status: ProofStatus
    comment: Optional[str] = None
