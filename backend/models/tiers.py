"""
SaaS Tier Configuration Models

Defines the feature access rules for each subscription tier:
- Tier 1 (Starter/Free): Basic features for small shops
- Tier 2 (Pro): Full features for growing businesses  
- Tier 3 (Business): Everything unlimited
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from enum import Enum
from datetime import datetime, timezone
import uuid


class TierLevel(str, Enum):
    STARTER = "starter"  # Tier 1 - Free
    PRO = "pro"          # Tier 2
    BUSINESS = "business" # Tier 3


class FeatureStatus(str, Enum):
    ON = "on"
    OFF = "off"
    LIMITED = "limited"


class FeatureValue(BaseModel):
    """Represents a feature's status and optional limit"""
    status: FeatureStatus = FeatureStatus.OFF
    limit: Optional[int] = None  # For LIMITED features
    description: Optional[str] = None


# ============== FEATURE CATEGORIES ==============

class CustomerPortalFeatures(BaseModel):
    portal_access: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    dashboard: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    view_orders: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    view_quotes: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    view_invoices: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    messaging: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    artwork_approvals: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    appointments: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    profile_management: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    tax_exempt_status: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    notification_preferences: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    payment_history: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    online_payments: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    bnpl_options: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class WebstoreFeatures(BaseModel):
    webstore_access: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    num_stores: FeatureValue = FeatureValue(status=FeatureStatus.LIMITED, limit=1)
    business_stores: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    fundraiser_stores: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    creator_stores: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    event_stores: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    branding_basic: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    branding_logo: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    branding_colors: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    branding_banner: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    custom_domain: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    product_variants: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    product_images: FeatureValue = FeatureValue(status=FeatureStatus.LIMITED, limit=3)
    price_overrides: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    personalization_fields: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    product_bundles: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    minimum_order_qty: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    bulk_import: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    discount_codes: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    tax_calculation: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    shipping_basic: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    calculated_shipping: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    free_shipping_threshold: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    guest_checkout: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    customer_accounts: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    order_notes: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    confirmation_email: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    analytics_basic: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    analytics_advanced: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    external_dashboard: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    payout_tracking: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    social_sharing: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    countdown_timer: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    progress_bar: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    leaderboard: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class WebstorePaymentFeatures(BaseModel):
    cash_check: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    stripe: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    paypal: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    affirm: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    klarna: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    store_credit: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class B2BFeatures(BaseModel):
    b2b_access: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    volume_discounts: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    net_terms: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    budget_limits: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    purchase_orders: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    approval_workflows: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class CreatorAffiliateFeatures(BaseModel):
    creator_access: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    commission_tracking: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    affiliate_links: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    payout_management: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class OrderManagementFeatures(BaseModel):
    order_list: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    filters: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    detail_view: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    status_updates: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    convert_to_job: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    packing_slips: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    bulk_updates: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    search: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    internal_notes: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    refund: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    partial_fulfillment: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    tracking_entry: FeatureValue = FeatureValue(status=FeatureStatus.ON)


class PricingFeatures(BaseModel):
    basic_pricing: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    pricing_calculator: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    cost_tracking: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    profit_margin_display: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    price_templates: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    ai_price_suggestions: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    local_market_analysis: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    profit_optimization: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    historical_trends: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    quote_templates: FeatureValue = FeatureValue(status=FeatureStatus.ON)


class AnalyticsFeatures(BaseModel):
    basic_summary: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    category_breakdown: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    monthly_reports: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    profit_analysis: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    customer_insights: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    trend_analysis: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    export_reports: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    custom_reports: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    scheduled_reports: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    cash_flow_projections: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class AIToolsFeatures(BaseModel):
    ai_access: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    monthly_generations: FeatureValue = FeatureValue(status=FeatureStatus.LIMITED, limit=25)
    text_tools: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    image_generation: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    image_analysis: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    ai_history: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    save_to_job: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class AIBusinessAssistantFeatures(BaseModel):
    chat: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    revenue_queries: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    customer_queries: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    job_queries: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    product_queries: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    trend_queries: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    comparison_queries: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    natural_language: FeatureValue = FeatureValue(status=FeatureStatus.LIMITED, limit=10)
    export_insights: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class TeamFeatures(BaseModel):
    team_members: FeatureValue = FeatureValue(status=FeatureStatus.LIMITED, limit=1)
    role_management: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    custom_roles: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    activity_logs: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    permissions: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class CoreModuleFeatures(BaseModel):
    customers: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    quotes: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    jobs: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    active_jobs: FeatureValue = FeatureValue(status=FeatureStatus.ON)  # unlimited for all tiers
    line_items: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    kanban: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    job_log: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    invoices: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    time_clock: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    payroll: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    tasks: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    calendar: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    financial_tracking: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class CommunicationsFeatures(BaseModel):
    email_notifications: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    new_order_alerts: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    order_status_emails: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    proof_alerts: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    payment_alerts: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    low_stock_alerts: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    abandoned_cart: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    marketing_emails: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    sms: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    in_app_notifications: FeatureValue = FeatureValue(status=FeatureStatus.ON)


class IntegrationsFeatures(BaseModel):
    sendgrid: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    stripe: FeatureValue = FeatureValue(status=FeatureStatus.ON)
    paypal: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    affirm: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    klarna: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    twilio: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    quickbooks: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    google_analytics: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    facebook_pixel: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    zapier: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    mailchimp: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


class DataFeatures(BaseModel):
    storage_mb: FeatureValue = FeatureValue(status=FeatureStatus.LIMITED, limit=100)
    data_export: FeatureValue = FeatureValue(status=FeatureStatus.OFF)
    retention_years: FeatureValue = FeatureValue(status=FeatureStatus.LIMITED, limit=1)
    backup: FeatureValue = FeatureValue(status=FeatureStatus.OFF)


# ============== COMPLETE TIER CONFIGURATION ==============

class TierFeatures(BaseModel):
    """Complete feature configuration for a tier"""
    customer_portal: CustomerPortalFeatures = Field(default_factory=CustomerPortalFeatures)
    webstores: WebstoreFeatures = Field(default_factory=WebstoreFeatures)
    webstore_payments: WebstorePaymentFeatures = Field(default_factory=WebstorePaymentFeatures)
    b2b: B2BFeatures = Field(default_factory=B2BFeatures)
    creator_affiliate: CreatorAffiliateFeatures = Field(default_factory=CreatorAffiliateFeatures)
    order_management: OrderManagementFeatures = Field(default_factory=OrderManagementFeatures)
    pricing: PricingFeatures = Field(default_factory=PricingFeatures)
    analytics: AnalyticsFeatures = Field(default_factory=AnalyticsFeatures)
    ai_tools: AIToolsFeatures = Field(default_factory=AIToolsFeatures)
    ai_assistant: AIBusinessAssistantFeatures = Field(default_factory=AIBusinessAssistantFeatures)
    team: TeamFeatures = Field(default_factory=TeamFeatures)
    core_modules: CoreModuleFeatures = Field(default_factory=CoreModuleFeatures)
    communications: CommunicationsFeatures = Field(default_factory=CommunicationsFeatures)
    integrations: IntegrationsFeatures = Field(default_factory=IntegrationsFeatures)
    data: DataFeatures = Field(default_factory=DataFeatures)


class TierConfig(BaseModel):
    """Configuration for a subscription tier"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    level: TierLevel
    display_name: str
    description: str
    price_monthly: float = 0
    price_yearly: float = 0
    features: TierFeatures = Field(default_factory=TierFeatures)
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== USAGE TRACKING ==============

class UsageType(str, Enum):
    AI_GENERATIONS = "ai_generations"
    STORAGE_MB = "storage_mb"
    TEAM_MEMBERS = "team_members"
    WEBSTORES = "webstores"
    PRODUCT_IMAGES = "product_images"
    NL_QUERIES = "nl_queries"


class TenantUsage(BaseModel):
    """Track usage for limited features"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    usage_type: UsageType
    current_usage: int = 0
    limit: int = 0
    period_start: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    period_end: Optional[str] = None  # None = no reset (lifetime limit)
    last_updated: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class FeatureCheckResult(BaseModel):
    """Result of checking feature access"""
    allowed: bool
    feature: str
    status: FeatureStatus
    limit: Optional[int] = None
    current_usage: Optional[int] = None
    remaining: Optional[int] = None
    message: Optional[str] = None
