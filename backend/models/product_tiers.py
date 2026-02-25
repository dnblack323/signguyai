"""
SignGuy AI - Multi-Product Tier Configuration

THREE PRODUCT LINES:
1. SignGuy AI OS (Shop Management) - Starter/Pro/Business
2. SignGuy Webstores (Commerce-Only) - Launch/Growth/Scale  
3. SignGuy AI Studio (AI-Only) - Basic/Pro/Max

Each product line has distinct feature access, pricing, and processing fees.
Founder pricing is ONLY available for OS plans (100 spots).
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime, timezone


# ============== PRODUCT LINES ==============

class ProductLine(str, Enum):
    """The three distinct product offerings"""
    OS = "os"              # SignGuy AI OS (Full Shop Management)
    WEBSTORES = "webstores"  # SignGuy Webstores (Commerce-Only)
    AI_STUDIO = "ai_studio"  # SignGuy AI Studio (AI-Only)


# ============== PLAN TYPES ==============

class PlanType(str, Enum):
    """All available subscription plans across product lines"""
    # OS Plans
    OS_STARTER = "os_starter"
    OS_PRO = "os_pro"
    OS_BUSINESS = "os_business"
    
    # Webstore Plans
    WS_LAUNCH = "ws_launch"
    WS_GROWTH = "ws_growth"
    WS_SCALE = "ws_scale"
    
    # AI Studio Plans
    AI_BASIC = "ai_basic"
    AI_PRO = "ai_pro"
    AI_MAX = "ai_max"


# ============== LEGACY TIER MAPPING ==============
# For backwards compatibility with existing code

class TierLevel(str, Enum):
    """Legacy tier levels - maps to OS plans"""
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"


def plan_to_legacy_tier(plan: PlanType) -> TierLevel:
    """Map new plan types to legacy tier levels for backwards compat"""
    mapping = {
        PlanType.OS_STARTER: TierLevel.STARTER,
        PlanType.OS_PRO: TierLevel.PRO,
        PlanType.OS_BUSINESS: TierLevel.BUSINESS,
        PlanType.WS_LAUNCH: TierLevel.STARTER,
        PlanType.WS_GROWTH: TierLevel.PRO,
        PlanType.WS_SCALE: TierLevel.BUSINESS,
        PlanType.AI_BASIC: TierLevel.STARTER,
        PlanType.AI_PRO: TierLevel.PRO,
        PlanType.AI_MAX: TierLevel.BUSINESS,
    }
    return mapping.get(plan, TierLevel.STARTER)


# ============== FEATURE STATUS ==============

class FeatureStatus(str, Enum):
    ON = "on"
    OFF = "off"
    LIMITED = "limited"


class FeatureValue(BaseModel):
    """Represents a feature's status and optional limit"""
    status: FeatureStatus = FeatureStatus.OFF
    limit: Optional[int] = None
    description: Optional[str] = None


# ============== PROCESSING FEES ==============

class ProcessingFees(BaseModel):
    """Platform processing fees by transaction type"""
    invoice_fee_percent: float = 0.0      # Fee on invoice payments
    webstore_fee_percent: float = 0.0     # Fee on webstore transactions
    stripe_connect_enabled: bool = False  # Whether Stripe Connect is available
    online_payments_enabled: bool = False # Whether online invoice payments work


# ============== PRICING ==============

class PlanPricing(BaseModel):
    """Pricing for a plan"""
    monthly: float
    annual: float
    founder_monthly: Optional[float] = None  # None = no founder pricing
    founder_annual: Optional[float] = None
    

# ============== FEATURE CATEGORIES ==============

class CoreModuleFeatures(BaseModel):
    """Core shop management modules"""
    customers: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    jobs: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    invoices: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    online_invoice_payments: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    dashboard: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    employees: FeatureValue = FeatureValue(status=FeatureStatus.OFF, limit=0)
    time_clock: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    time_clock_advanced: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    tasks: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    productivity: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    productivity_advanced: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    payroll: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    financials: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    financials_advanced: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    company_settings: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    email_templates: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class CustomerPortalFeatures(BaseModel):
    """Customer-facing portal features"""
    portal_access: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    messaging: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    artwork_approvals: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    documents: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    document_storage_mb: FeatureValue = FeatureValue(status=FeatureStatus.OFF, limit=0)


class WebstoreFeatures(BaseModel):
    """Webstore/commerce features"""
    webstore_access: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    num_stores: FeatureValue = FeatureValue(status=FeatureStatus.OFF, limit=0)
    store_type_b2b: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    store_type_fundraiser: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    store_type_creator: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    stripe_connect: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    order_to_job_automation: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    commission_tracking: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    payout_tracking: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    advanced_branding: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    price_overrides: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    bulk_order_tools: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    store_analytics: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    store_analytics_advanced: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    fundraiser_goals: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class AIToolsFeatures(BaseModel):
    """AI generation tools"""
    ai_access: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    text_generation: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    image_generation: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    monthly_generations: FeatureValue = FeatureValue(status=FeatureStatus.OFF, limit=0)
    branding_kit_generator: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    campaign_builder: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    pricing_intelligence: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    content_calendar: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class AIAssistantFeatures(BaseModel):
    """AI business assistant"""
    assistant_access: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    monthly_queries: FeatureValue = FeatureValue(status=FeatureStatus.OFF, limit=0)
    business_data_aware: FeatureValue = FeatureValue(status=FeatureStatus.OFF)  # Can query actual business data
    business_data_limited: FeatureValue = FeatureValue(status=FeatureStatus.OFF)  # Limited data access


class CRMFeatures(BaseModel):
    """Advanced CRM features"""
    customer_specific_pricing: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    advanced_tagging: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    portal_document_sharing: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


# ============== COMBINED FEATURES ==============

class PlanFeatures(BaseModel):
    """All features for a plan"""
    core: CoreModuleFeatures = CoreModuleFeatures()
    customer_portal: CustomerPortalFeatures = CustomerPortalFeatures()
    webstores: WebstoreFeatures = WebstoreFeatures()
    ai_tools: AIToolsFeatures = AIToolsFeatures()
    ai_assistant: AIAssistantFeatures = AIAssistantFeatures()
    crm: CRMFeatures = CRMFeatures()


# ============== PLAN CONFIGURATION ==============

class PlanConfig(BaseModel):
    """Complete configuration for a subscription plan"""
    plan_type: PlanType
    product_line: ProductLine
    display_name: str
    description: str
    pricing: PlanPricing
    processing_fees: ProcessingFees
    features: PlanFeatures
    founder_eligible: bool = False  # Can use founder pricing
    
    # UI Visibility Controls
    show_jobs_ui: bool = True
    show_payroll_ui: bool = True
    show_time_clock_ui: bool = True
    show_financials_ui: bool = True
    show_ai_assistant_ui: bool = True


# ============== FOUNDER TRACKING ==============

FOUNDER_SPOTS_TOTAL = 100

class FounderStatus(BaseModel):
    """Founder status for a tenant"""
    is_founder: bool = False
    founder_number: Optional[int] = None
    founder_locked_at: Optional[str] = None


# ============== FEATURE CHECK RESULT ==============

class FeatureCheckResult(BaseModel):
    """Result of checking feature access"""
    allowed: bool
    feature: str
    status: FeatureStatus
    limit: Optional[int] = None
    current_usage: Optional[int] = None
    remaining: Optional[int] = None
    message: Optional[str] = None


# ============== TENANT USAGE TRACKING ==============

class TenantUsage(BaseModel):
    """Track usage for limited features"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    usage_type: str  # e.g., "ai_tools.monthly_generations"
    current_usage: int = 0
    limit: int = 0
    period_start: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    period_end: Optional[str] = None
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


import uuid
