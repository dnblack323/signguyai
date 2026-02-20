"""
Subscription & Billing Models - Updated Pricing Structure

Pricing Tiers:
- 24-Hour Free Trial (no payment)
- 14-Day Extended Trial ($19.99, credits to Tier 3)
- Founder Pricing (first 100 shops, lifetime lock-in):
  - Tier 1 Founder: $79/mo
  - Tier 2 Founder: $129/mo
  - Tier 3 Founder: $199/mo
  - AI Tools Add-On: $49/mo
- Standard Pricing (after 100 founders):
  - Shop Core: $129/mo
  - Growth Shop: $229/mo
  - Pro Shop: $379/mo
  - AI Tools Add-On: $89/mo
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime, timezone
import uuid


class SubscriptionPlan(str, Enum):
    """Available subscription plans"""
    FREE_TRIAL = "free_trial"           # 24-hour free trial
    EXTENDED_TRIAL = "extended_trial"   # 14-day trial ($19.99)
    TIER_1 = "tier_1"                   # Founder: $79/mo, Standard: $129/mo
    TIER_2 = "tier_2"                   # Founder: $129/mo, Standard: $229/mo
    TIER_3 = "tier_3"                   # Founder: $199/mo, Standard: $379/mo
    AI_ADDON = "ai_addon"               # Founder: $49/mo, Standard: $89/mo


class BillingInterval(str, Enum):
    """Billing intervals"""
    MONTHLY = "monthly"
    ANNUAL = "annual"


class SubscriptionStatus(str, Enum):
    """Subscription statuses"""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    LOCKED = "locked"


class PaymentStatus(str, Enum):
    """Payment transaction statuses"""
    PENDING = "pending"
    INITIATED = "initiated"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"


# ============== PRICING CONFIGURATION ==============

# Maximum founder accounts
MAX_FOUNDER_ACCOUNTS = 100

# Founder Pricing (First 100 shops - Lifetime lock-in)
FOUNDER_PRICING = {
    SubscriptionPlan.EXTENDED_TRIAL: {
        "name": "14-Day Extended Trial",
        "amount": 19.99,
        "amount_annual": 19.99,  # One-time, no annual
        "description": "Full platform access for 14 days. Credits toward Tier 3!",
        "trial_days": 14,
        "tier": "tier_3",  # Gets full Tier 3 access during trial
        "credits_to_tier3": True,
    },
    SubscriptionPlan.TIER_1: {
        "name": "Tier 1 – Founder",
        "display_name": "Starter Shop",
        "amount": 79.00,
        "amount_annual": 790.00,  # 10 months (save 2 months)
        "annual_savings": 158.00,  # 2 months saved
        "description": "Essential tools for small sign shops",
        "interval": "month",
        "tier": "starter",
        "standard_price": 129.00,
        "standard_price_annual": 1290.00,
        "onboarding_fee": 0,  # Founders never pay
    },
    SubscriptionPlan.TIER_2: {
        "name": "Tier 2 – Founder",
        "display_name": "Growth Shop",
        "amount": 129.00,
        "amount_annual": 1290.00,  # 10 months (save 2 months)
        "annual_savings": 258.00,
        "description": "Advanced features for growing businesses",
        "interval": "month",
        "tier": "pro",
        "standard_price": 229.00,
        "standard_price_annual": 2290.00,
        "onboarding_fee": 0,
    },
    SubscriptionPlan.TIER_3: {
        "name": "Tier 3 – Founder",
        "display_name": "Pro Shop",
        "amount": 199.00,
        "amount_annual": 1990.00,  # 10 months (save 2 months)
        "annual_savings": 398.00,
        "description": "Everything unlimited. Full power.",
        "interval": "month",
        "tier": "business",
        "standard_price": 379.00,
        "standard_price_annual": 3790.00,
        "onboarding_fee": 0,
    },
    SubscriptionPlan.AI_ADDON: {
        "name": "AI Tools Add-On – Founder",
        "display_name": "AI Tools Pack",
        "amount": 49.00,
        "amount_annual": 490.00,  # 10 months (save 2 months)
        "annual_savings": 98.00,
        "description": "All AI tools for shops using other systems",
        "interval": "month",
        "tier": "ai_addon",
        "standard_price": 89.00,
        "standard_price_annual": 890.00,
        "is_addon": True,
    },
}

# Standard Pricing (After 100 founders)
STANDARD_PRICING = {
    SubscriptionPlan.EXTENDED_TRIAL: {
        "name": "14-Day Extended Trial",
        "amount": 19.99,
        "description": "Full platform access for 14 days",
        "trial_days": 14,
        "tier": "tier_3",
    },
    SubscriptionPlan.TIER_1: {
        "name": "Shop Core",
        "display_name": "Shop Core",
        "amount": 129.00,
        "description": "Essential tools for small sign shops",
        "interval": "month",
        "tier": "starter",
        "onboarding_fee": 199.00,
    },
    SubscriptionPlan.TIER_2: {
        "name": "Growth Shop",
        "display_name": "Growth Shop",
        "amount": 229.00,
        "description": "Advanced features for growing businesses",
        "interval": "month",
        "tier": "pro",
        "onboarding_fee": 399.00,
    },
    SubscriptionPlan.TIER_3: {
        "name": "Pro Shop",
        "display_name": "Pro Shop",
        "amount": 379.00,
        "description": "Everything unlimited. Full power.",
        "interval": "month",
        "tier": "business",
        "onboarding_fee": 599.00,
    },
    SubscriptionPlan.AI_ADDON: {
        "name": "AI Tools Add-On",
        "display_name": "AI Tools Pack",
        "amount": 89.00,
        "description": "All AI tools for shops using other systems",
        "interval": "month",
        "tier": "ai_addon",
        "is_addon": True,
    },
}

# Tier feature mapping
TIER_NAMES = {
    "starter": "Tier 1",
    "pro": "Tier 2", 
    "business": "Tier 3",
}

# Features by tier for display
TIER_FEATURES = {
    "starter": [  # Tier 1
        "Customer Management",
        "Quotes & Jobs",
        "Basic Invoicing",
        "1 Webstore",
        "25 AI generations/month",
        "1 Team member",
        "100MB Storage",
        "Email Support",
    ],
    "pro": [  # Tier 2
        "Everything in Tier 1, plus:",
        "5 Webstores",
        "100 AI generations/month",
        "5 Team members",
        "1GB Storage",
        "Time Clock & Payroll",
        "Kanban & Calendar",
        "Advanced Analytics",
        "Priority Support",
    ],
    "business": [  # Tier 3
        "Everything in Tier 2, plus:",
        "Unlimited Webstores",
        "Unlimited AI generations",
        "Unlimited Team members",
        "5GB Storage",
        "B2B Features",
        "BNPL Payments",
        "Custom Reports",
        "SMS Notifications",
        "API Access",
        "Dedicated Support",
    ],
    "ai_addon": [
        "AI Design Tools",
        "AI Copywriter",
        "AI Social Media Content",
        "AI Branding Tools",
        "AI Business Document Generator",
        "Image Analysis",
        "AI Price Suggestions",
        "Works standalone or with any plan",
    ],
}

# Founder benefits for display
FOUNDER_BENEFITS = [
    "Lifetime locked-in pricing",
    "No onboarding fees (save up to $599)",
    "Early access to new features",
    "Direct input into product development",
    "Direct support contact with the developer",
]


# ============== DATABASE MODELS ==============

class Subscription(BaseModel):
    """Tenant subscription record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus = SubscriptionStatus.TRIALING
    tier: str = "starter"
    
    # Stripe IDs
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Founder status
    is_founder: bool = False
    founder_number: Optional[int] = None  # 1-100
    founder_locked_at: Optional[str] = None
    
    # AI Add-on
    has_ai_addon: bool = False
    
    # Trial info
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    trial_credits_applied: float = 0
    extended_trial_paid: bool = False
    
    # Billing
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FounderCounter(BaseModel):
    """Track founder account count"""
    id: str = "founder_counter"
    count: int = 0
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PaymentTransaction(BaseModel):
    """Payment transaction record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    
    # Stripe session
    stripe_session_id: str
    stripe_payment_intent_id: Optional[str] = None
    
    # Payment details
    amount: float
    currency: str = "usd"
    plan: SubscriptionPlan
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Founder tracking
    is_founder_purchase: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    paid_at: Optional[str] = None


# ============== API REQUEST/RESPONSE MODELS ==============

class CheckoutRequest(BaseModel):
    """Request to create checkout session"""
    plan: SubscriptionPlan
    include_ai_addon: bool = False
    origin_url: str


class CheckoutResponse(BaseModel):
    """Response with checkout session URL"""
    url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    """Current subscription info"""
    plan: str
    plan_name: str
    status: str
    tier: str
    is_founder: bool
    founder_number: Optional[int] = None
    has_ai_addon: bool = False
    trial_end: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    trial_credits: float = 0
    features: List[str] = []


class PricingPlan(BaseModel):
    """Pricing plan for display"""
    id: str
    name: str
    display_name: str
    amount: float
    standard_price: Optional[float] = None
    savings: Optional[float] = None
    description: str
    interval: Optional[str] = None
    tier: str
    features: List[str] = []
    is_addon: bool = False
    is_popular: bool = False
    onboarding_fee: float = 0


class PricingResponse(BaseModel):
    """Full pricing page response"""
    is_founder_pricing: bool
    founders_remaining: int
    founders_claimed: int
    plans: List[PricingPlan]
    addon: Optional[PricingPlan] = None
    trial: Optional[PricingPlan] = None
    founder_benefits: List[str] = []


class TrialStatus(BaseModel):
    """Trial status response"""
    is_trial: bool
    trial_type: Optional[str] = None
    hours_remaining: Optional[float] = None
    days_remaining: Optional[float] = None
    is_locked: bool = False
    can_upgrade: bool = True
    extended_trial_paid: bool = False
