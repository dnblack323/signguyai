"""
Subscription & Billing Models

Defines models for:
- Subscription plans and pricing
- Payment transactions
- Founder member status
- Trial management
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime, timezone
import uuid


class SubscriptionPlan(str, Enum):
    """Available subscription plans"""
    FREE_TRIAL = "free_trial"      # 24-hour free trial
    PAID_TRIAL = "paid_trial"      # 14-day paid trial ($24.99)
    PRO_MONTHLY = "pro_monthly"    # Pro $49/mo
    PRO_YEARLY = "pro_yearly"      # Pro $399/yr
    BUSINESS_MONTHLY = "business_monthly"  # Business $149/mo
    BUSINESS_YEARLY = "business_yearly"    # Business $1,199/yr


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

# Founder Member Pricing (locked in for early adopters)
FOUNDER_PRICING = {
    SubscriptionPlan.PAID_TRIAL: {
        "name": "14-Day Pro Trial",
        "amount": 24.99,
        "description": "Full access to all Pro features for 14 days",
        "trial_days": 14,
        "tier": "pro",
        "regular_price": 49.99,
    },
    SubscriptionPlan.PRO_MONTHLY: {
        "name": "Pro Monthly",
        "amount": 49.00,
        "description": "Everything you need to run your sign shop",
        "interval": "month",
        "tier": "pro",
        "regular_price": 79.00,
    },
    SubscriptionPlan.PRO_YEARLY: {
        "name": "Pro Yearly",
        "amount": 399.00,
        "description": "Pro plan - Save $189 per year",
        "interval": "year",
        "tier": "pro",
        "monthly_equivalent": 33.25,
        "regular_price": 699.00,
        "savings": 189,
    },
    SubscriptionPlan.BUSINESS_MONTHLY: {
        "name": "Business Monthly",
        "amount": 149.00,
        "description": "Unlimited everything for established shops",
        "interval": "month",
        "tier": "business",
        "regular_price": 249.00,
    },
    SubscriptionPlan.BUSINESS_YEARLY: {
        "name": "Business Yearly",
        "amount": 1199.00,
        "description": "Business plan - Save $589 per year",
        "interval": "year",
        "tier": "business",
        "monthly_equivalent": 99.92,
        "regular_price": 1999.00,
        "savings": 589,
    },
}

# Features by tier for display
TIER_FEATURES = {
    "pro": [
        "5 Webstores",
        "100 AI generations/month",
        "5 Team members",
        "1GB Storage",
        "Time Clock & Payroll",
        "Kanban & Calendar",
        "Advanced Analytics",
        "Priority Support",
    ],
    "business": [
        "Unlimited Webstores",
        "Unlimited AI generations",
        "Unlimited Team members",
        "5GB Storage",
        "B2B Features",
        "BNPL Payments (Affirm/Klarna)",
        "Custom Reports",
        "SMS Notifications",
        "API Access",
        "Dedicated Support",
    ],
}


# ============== DATABASE MODELS ==============

class Subscription(BaseModel):
    """Tenant subscription record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus = SubscriptionStatus.TRIALING
    tier: str = "starter"  # starter, pro, business
    
    # Stripe IDs
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Founder status
    is_founder: bool = True  # All early adopters get founder pricing
    founder_locked_at: Optional[str] = None
    
    # Trial info
    trial_start: Optional[str] = None
    trial_end: Optional[str] = None
    trial_credits_applied: float = 0  # Trial payment credited to subscription
    
    # Billing
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


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
    origin_url: str  # Frontend origin for success/cancel URLs


class CheckoutResponse(BaseModel):
    """Response with checkout session URL"""
    url: str
    session_id: str


class SubscriptionResponse(BaseModel):
    """Current subscription info"""
    plan: str
    status: str
    tier: str
    is_founder: bool
    trial_end: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    trial_credits: float = 0
    features: List[str] = []


class PricingPlan(BaseModel):
    """Pricing plan for display"""
    id: str
    name: str
    amount: float
    regular_price: float
    savings: Optional[float] = None
    description: str
    interval: Optional[str] = None  # month, year, or None for one-time
    tier: str
    features: List[str] = []
    monthly_equivalent: Optional[float] = None
    is_popular: bool = False


class TrialStatus(BaseModel):
    """Trial status response"""
    is_trial: bool
    trial_type: Optional[str] = None  # free_trial, paid_trial
    hours_remaining: Optional[float] = None
    days_remaining: Optional[float] = None
    is_locked: bool = False
    can_upgrade: bool = True
