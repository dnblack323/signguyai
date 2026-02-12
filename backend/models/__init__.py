"""
SignGuy AI Backend Models

This module exports all Pydantic models and enums used throughout the application.
"""

# Enums
from .enums import (
    CustomerStatus, QuoteStatus, JobStatus, JobActivityType,
    JobItemStatus, JobItemType, InvoiceStatus,
    PricingCategory, ServiceType, ApparelType, TransferType,
    VinylType, PrintMaterial, SubstrateType, VehicleType,
    CoverageType, PromoProductType, PayrollTransactionType, ExpenseCategory,
    UserRole, TenantPlan, PaymentMethod,
    MessageType, ProofStatus, AppointmentType, AppointmentStatus,
    WebstoreType, WebstoreStatus, OrderStatus
)

# Customer & Portal models
from .customer import (
    CustomerBase, CustomerCreate, CustomerUpdate, Customer,
    ConversationMessage, Conversation, ArtworkProof,
    CustomerNotification, Appointment,
    CustomerPortalLogin, CustomerPortalRegister, CustomerPortalToken,
    CustomerProfileUpdate, ConversationCreate, MessageCreate, ProofResponseCreate
)

# Jobs, Quotes, Invoices models
from .jobs import (
    QuoteLineItem, QuoteBase, QuoteCreate, QuoteUpdate, Quote,
    JobBase, JobCreate, JobUpdate, Job,
    JobNoteBase, JobNoteCreate, JobNote,
    JobActivity, JobItemBase, JobItemCreate, JobItemUpdate, JobItem,
    InvoiceLineItem, InvoiceBase, InvoiceCreate, InvoiceUpdate, Invoice
)

# Auth & Tenant models
from .auth import (
    TenantBase, TenantCreate, TenantUpdate, Tenant,
    UserBase, UserCreate, UserLogin, User, UserInDB, UserRoleUpdate,
    Token, TokenData, PasswordReset,
    Permission, ROLE_PERMISSIONS, get_user_permissions, user_has_permission
)

# Pricing models
from .pricing import (
    MaterialConfig, PricingDefaults, PricingCalculation,
    JobItemPricingData, JobItemEnhanced, JobItemEnhancedCreate, JobItemEnhancedUpdate,
    PricingTemplate, PricingTemplateCreate, PriceCalculateRequest
)
