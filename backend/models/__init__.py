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
    BrandingProfile, BrandingLogoConcept,
    ConversationMessage, Conversation, ArtworkProof,
    CustomerNotification, Appointment,
    CustomerPortalLogin, CustomerPortalRegister, CustomerPortalToken,
    CustomerProfileUpdate, ConversationCreate, MessageCreate, ProofResponseCreate
)

# Jobs, Quotes, Invoices models
from .jobs import (
    QuoteLineItem, QuoteBase, QuoteCreate, QuoteUpdate, Quote,
    JobLineItem, JobBase, JobCreate, JobUpdate, Job,
    JobNoteBase, JobNoteCreate, JobNote,
    JobActivity, JobItemBase, JobItemCreate, JobItemUpdate, JobItem,
    InvoiceLineItem, InvoiceBase, InvoiceCreate, InvoiceUpdate, Invoice,
    JobTimeEntry, JobTimeEntryCreate, JobTimeEntryUpdate, JobTimeSummary
)

# Auth & Tenant models
from .auth import (
    TenantBase, TenantCreate, TenantUpdate, Tenant, TimeTrackingSettings,
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

# Tier/SaaS models
from .tiers import (
    TierLevel, FeatureStatus, FeatureValue, TierFeatures, TierConfig,
    UsageType, TenantUsage, FeatureCheckResult,
    CustomerPortalFeatures, WebstoreFeatures, WebstorePaymentFeatures,
    B2BFeatures, CreatorAffiliateFeatures, OrderManagementFeatures,
    PricingFeatures, AnalyticsFeatures, AIToolsFeatures, AIBusinessAssistantFeatures,
    TeamFeatures, CoreModuleFeatures, CommunicationsFeatures, IntegrationsFeatures,
    DataFeatures
)

# Billing/Subscription models
from .billing import (
    SubscriptionPlan, SubscriptionStatus, PaymentStatus,
    FOUNDER_PRICING, TIER_FEATURES,
    Subscription, PaymentTransaction,
    CheckoutRequest, CheckoutResponse, SubscriptionResponse,
    PricingPlan, TrialStatus
)

# AI Credits models
from .credits import (
    CreditPackType, CREDIT_PACKS, CreditTransactionType,
    CreditTransaction, UserCredits,
    CreditUsageRequest, CreditUsageResponse,
    CreditBalanceResponse, PurchaseCreditPackRequest, PurchaseCreditPackResponse,
    PromoCode, PromoCodeUsage
)
