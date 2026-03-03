"""
Founders Edition Plan Configuration

The Founders Edition is the only active pricing plan:
- Price: $99/month
- Annual: Pay for 6 months ($594), get 12 months with promo code FOUNDERS
- Limited to 100 customers
- 150 AI credits per month
- All features included, no restrictions
"""

from models.product_tiers import (
    PlanConfig, PlanPricing, ProcessingFees, PlanFeatures,
    CoreModuleFeatures, CustomerPortalFeatures, WebstoreFeatures,
    AIToolsFeatures, AIAssistantFeatures, CRMFeatures,
    FeatureValue, FeatureStatus, ProductLine, PlanType
)

# Founders Edition constants
FOUNDERS_EDITION_MONTHLY_PRICE = 99.0
FOUNDERS_EDITION_ANNUAL_PRICE = 594.0  # 6 months = $594, but gets 12 months
FOUNDERS_EDITION_MONTHLY_CREDITS = 150
FOUNDERS_EDITION_MAX_CUSTOMERS = 100
FOUNDERS_PROMO_CODE = "FOUNDERS"

# AI Action credit costs (to be configured by user)
# Default costs - user will update these
AI_CREDIT_COSTS = {
    # Text Generation
    "text_generation": 1,
    "blog_creator": 2,
    "social_media_post": 1,
    "email_template": 1,
    "product_description": 1,
    
    # Image Generation
    "image_generation": 3,
    "logo_generation": 3,
    "mockup_generation": 3,
    
    # AI Assistant
    "ai_assistant_query": 1,
    "ai_assistant_data_query": 2,
    
    # Other AI Tools
    "branding_kit": 3,
    "campaign_builder": 2,
    "pricing_intelligence": 1,
    "content_calendar": 2,
    
    # Default for unknown actions
    "default": 1
}


def get_ai_credit_cost(action_type: str) -> int:
    """Get the credit cost for an AI action"""
    return AI_CREDIT_COSTS.get(action_type, AI_CREDIT_COSTS["default"])


def get_founders_edition_config() -> dict:
    """
    Get the Founders Edition plan configuration.
    All features ON, no restrictions.
    """
    return {
        "plan_id": "founders_edition",
        "plan_type": "founders_edition",
        "product_line": "founders",
        "display_name": "Founders Edition",
        "description": "Early adopter exclusive - all features, unlimited access, 150 AI credits/month",
        "pricing": {
            "monthly": FOUNDERS_EDITION_MONTHLY_PRICE,
            "annual": FOUNDERS_EDITION_ANNUAL_PRICE,
            "annual_months": 12,  # Pay for 6, get 12
            "promo_code": FOUNDERS_PROMO_CODE,
        },
        "processing_fees": {
            "invoice_fee_percent": 0.0,  # No platform fees for Founders
            "webstore_fee_percent": 0.0,
            "stripe_connect_enabled": True,
            "online_payments_enabled": True,
        },
        "ai_credits": {
            "monthly_allowance": FOUNDERS_EDITION_MONTHLY_CREDITS,
            "credits_expire": True,  # Monthly credits expire
        },
        "max_customers": FOUNDERS_EDITION_MAX_CUSTOMERS,
        "is_active": True,
        "is_default": True,
        # All features ON
        "features": {
            "core": {
                "customers": "on",
                "jobs": "on",
                "invoices": "on",
                "online_invoice_payments": "on",
                "dashboard": "on",
                "employees": "on",
                "time_clock": "on",
                "time_clock_advanced": "on",
                "tasks": "on",
                "productivity": "on",
                "productivity_advanced": "on",
                "payroll": "on",
                "financials": "on",
                "financials_advanced": "on",
                "company_settings": "on",
                "email_templates": "on",
            },
            "customer_portal": {
                "portal_access": "on",
                "messaging": "on",
                "artwork_approvals": "on",
                "documents": "on",
                "document_storage_mb": "unlimited",
            },
            "webstores": {
                "webstore_access": "on",
                "num_stores": "unlimited",
                "store_type_b2b": "on",
                "store_type_fundraiser": "on",
                "store_type_creator": "on",
                "stripe_connect": "on",
                "order_to_job_automation": "on",
                "commission_tracking": "on",
                "payout_tracking": "on",
                "advanced_branding": "on",
                "price_overrides": "on",
                "bulk_order_tools": "on",
                "store_analytics": "on",
                "store_analytics_advanced": "on",
                "fundraiser_goals": "on",
            },
            "ai_tools": {
                "ai_access": "on",
                "text_generation": "on",
                "image_generation": "on",
                "monthly_generations": "unlimited",
                "branding_kit_generator": "on",
                "campaign_builder": "on",
                "pricing_intelligence": "on",
                "content_calendar": "on",
            },
            "ai_assistant": {
                "assistant_access": "on",
                "monthly_queries": "unlimited",
                "business_data_aware": "on",
                "business_data_limited": "on",
            },
            "crm": {
                "customer_specific_pricing": "on",
                "advanced_tagging": "on",
                "portal_document_sharing": "on",
            },
        },
        "ui_visibility": {
            "show_jobs_ui": True,
            "show_payroll_ui": True,
            "show_time_clock_ui": True,
            "show_financials_ui": True,
            "show_ai_assistant_ui": True,
            "show_webstores_ui": True,
            "show_customer_portal_ui": True,
        }
    }


def is_founders_edition_available() -> dict:
    """
    Check if Founders Edition spots are still available.
    Returns availability status and remaining spots.
    """
    # This will be called with actual database count
    return {
        "is_available": True,  # Will be computed from DB
        "max_spots": FOUNDERS_EDITION_MAX_CUSTOMERS,
        "spots_remaining": FOUNDERS_EDITION_MAX_CUSTOMERS,  # Will be computed from DB
        "spots_claimed": 0  # Will be computed from DB
    }


# Credit pack pricing
CREDIT_PACKS = {
    "pack_100": {
        "credits": 100,
        "price_cents": 1000,  # $10.00
        "price_display": "$10",
        "per_credit": "$0.10",
        "display_name": "Starter Pack",
        "description": "100 AI credits"
    },
    "pack_300": {
        "credits": 300,
        "price_cents": 2500,  # $25.00
        "price_display": "$25",
        "per_credit": "$0.083",
        "display_name": "Value Pack",
        "description": "300 AI credits - 17% savings"
    },
    "pack_1000": {
        "credits": 1000,
        "price_cents": 6000,  # $60.00
        "price_display": "$60",
        "per_credit": "$0.06",
        "display_name": "Power Pack",
        "description": "1000 AI credits - 40% savings"
    }
}
