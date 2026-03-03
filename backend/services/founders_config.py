"""
Founders Edition Plan Configuration

The ONLY active pricing plan for new signups:
- Price: $99/month
- Annual: $594 for 12 months with promo code FOUNDERS
- Limited to 100 customers (lifetime lock)
- 150 AI credits per month (rollover enabled for purchased credits)
- All features included, no restrictions

Processing Fees:
- Platform processing: 2.2% + $0.20 on all transactions
- Webstore fee: 2.0% on all webstore sales
"""

# =============================================================================
# FOUNDERS EDITION PLAN FIELDS
# =============================================================================

FOUNDERS_EDITION_PLAN = {
    "plan_name": "Founders Edition",
    "plan_id": "founders_edition",
    "price_monthly": 99.0,
    "price_annual": 594.0,  # 6 months price for 12 months access
    "founder_lifetime_lock": True,
    "founder_limit": 100,
    "founder_spots_used": 0,  # Tracked in database
    "ai_credits_monthly": 150,
    "credit_rollover": True,  # Purchased credits roll over (monthly don't)
    "plan_active": True,
    "plan_public": True,
}

# =============================================================================
# FEE CONFIGURATION
# =============================================================================

PLATFORM_FEES = {
    "platform_processing_percent": 2.2,  # 2.2% of transaction
    "platform_processing_fixed": 0.20,   # + $0.20 fixed fee
    "webstore_fee_percent": 2.0,         # 2% on webstore sales
}

# =============================================================================
# CREDIT PACK DEFINITIONS
# =============================================================================

CREDIT_PACKS = {
    "credit_pack_small": {
        "pack_id": "pack_100",
        "credits": 100,
        "price": 10.00,
        "price_cents": 1000,
        "price_display": "$10",
        "per_credit": "$0.10",
        "display_name": "100 Credits",
        "description": "100 AI credits - never expire"
    },
    "credit_pack_medium": {
        "pack_id": "pack_300",
        "credits": 300,
        "price": 25.00,
        "price_cents": 2500,
        "price_display": "$25",
        "per_credit": "$0.083",
        "display_name": "300 Credits",
        "description": "300 AI credits - 17% savings"
    },
    "credit_pack_large": {
        "pack_id": "pack_1000",
        "credits": 1000,
        "price": 60.00,
        "price_cents": 6000,
        "price_display": "$60",
        "per_credit": "$0.06",
        "display_name": "1000 Credits",
        "description": "1000 AI credits - 40% savings"
    }
}

# Shorthand for API compatibility
FOUNDERS_EDITION_MONTHLY_PRICE = FOUNDERS_EDITION_PLAN["price_monthly"]
FOUNDERS_EDITION_ANNUAL_PRICE = FOUNDERS_EDITION_PLAN["price_annual"]
FOUNDERS_EDITION_MONTHLY_CREDITS = FOUNDERS_EDITION_PLAN["ai_credits_monthly"]
FOUNDERS_EDITION_MAX_CUSTOMERS = FOUNDERS_EDITION_PLAN["founder_limit"]
FOUNDERS_PROMO_CODE = "FOUNDERS"

# =============================================================================
# AI CREDIT COSTS BY CATEGORY
# =============================================================================

# 1-Credit Tools: Short text, simple queries, non-destructive actions
ONE_CREDIT_TOOLS = [
    # Short text tools
    "text_generation",
    "short_text",
    "tagline_generator",
    "headline_generator",
    
    # Email replies
    "email_reply",
    "quick_response",
    
    # Product descriptions
    "product_description",
    "product_description_generator",
    
    # Simple assistant queries
    "ai_assistant_query",
    "simple_query",
    "quick_lookup",
    
    # Non-destructive structured actions
    "view_action",
    "list_action",
    "search_action",
]

# 2-Credit Tools: Blog, SEO, proposals, medium complexity
TWO_CREDIT_TOOLS = [
    # Blog creator
    "blog_creator",
    "blog_post",
    "article_writer",
    
    # SEO content
    "seo_content",
    "seo_optimizer",
    "meta_description",
    
    # Proposals
    "proposal_generator",
    "quote_letter",
    
    # Content calendar
    "content_calendar",
    "social_calendar",
    
    # Pricing advisor
    "pricing_advisor",
    "cost_estimator",
    
    # Simple image generation
    "simple_image",
    "icon_generation",
    
    # Medium assistant queries
    "ai_assistant_data_query",
    "data_analysis",
    "report_generation",
    
    # Structured actions requiring confirmation
    "create_action",
    "update_action",
    "schedule_action",
]

# 3-Credit Tools: Image generation, mockups, heavy processing
THREE_CREDIT_TOOLS = [
    # All image generation
    "image_generation",
    "logo_generation",
    "banner_generation",
    "social_image",
    
    # Mockups
    "mockup_generation",
    "product_mockup",
    "sign_mockup",
    
    # Vehicle wrap mockups
    "vehicle_wrap_mockup",
    "vehicle_wrap",
    "wrap_preview",
    
    # Generative fill
    "generative_fill",
    "image_edit",
    "background_removal",
    
    # Pricing intelligence
    "pricing_intelligence",
    "market_analysis",
    "competitor_analysis",
    
    # Heavy assistant queries
    "complex_query",
    "multi_step_analysis",
    
    # Multi-step structured actions
    "bulk_action",
    "workflow_action",
    "automation_action",
    
    # Branding kit
    "branding_kit",
    "brand_generator",
    
    # Campaign builder
    "campaign_builder",
    "marketing_campaign",
]

# Build the credit costs dictionary
AI_CREDIT_COSTS = {}

for tool in ONE_CREDIT_TOOLS:
    AI_CREDIT_COSTS[tool] = 1

for tool in TWO_CREDIT_TOOLS:
    AI_CREDIT_COSTS[tool] = 2

for tool in THREE_CREDIT_TOOLS:
    AI_CREDIT_COSTS[tool] = 3

# Default cost for unknown tools
AI_CREDIT_COSTS["default"] = 1

# Low credits threshold for modal trigger
LOW_CREDITS_THRESHOLD = 10


def get_ai_credit_cost(action_type: str) -> int:
    """Get the credit cost for an AI action (1, 2, or 3 credits)"""
    return AI_CREDIT_COSTS.get(action_type, AI_CREDIT_COSTS["default"])


def calculate_platform_fee(amount_cents: int) -> int:
    """
    Calculate platform processing fee: 2.2% + $0.20
    Returns fee in cents
    """
    percent_fee = amount_cents * (PLATFORM_FEES["platform_processing_percent"] / 100)
    fixed_fee = PLATFORM_FEES["platform_processing_fixed"] * 100  # Convert to cents
    return int(percent_fee + fixed_fee)


def calculate_webstore_fee(amount_cents: int) -> int:
    """
    Calculate webstore fee: 2.0%
    Returns fee in cents
    """
    return int(amount_cents * (PLATFORM_FEES["webstore_fee_percent"] / 100))


def get_founders_edition_config() -> dict:
    """
    Get the complete Founders Edition plan configuration.
    This is the ONLY active plan for new signups.
    """
    return {
        "plan_id": "founders_edition",
        "plan_name": FOUNDERS_EDITION_PLAN["plan_name"],
        "plan_type": "founders_edition",
        "product_line": "founders",
        "display_name": "Founders Edition",
        "tagline": "Only 100 Spots Available",
        "description": "Early adopter exclusive - all features, unlimited access, 150 AI credits/month",
        
        # Pricing
        "pricing": {
            "monthly": FOUNDERS_EDITION_MONTHLY_PRICE,
            "annual": FOUNDERS_EDITION_ANNUAL_PRICE,
            "annual_months": 12,  # Pay for 6, get 12
            "annual_savings": "Get 6 months FREE with annual plan",
            "promo_code": FOUNDERS_PROMO_CODE,
            "promo_description": "Use code FOUNDERS for annual billing discount",
        },
        
        # Fees
        "fees": {
            "platform_processing_percent": PLATFORM_FEES["platform_processing_percent"],
            "platform_processing_fixed": PLATFORM_FEES["platform_processing_fixed"],
            "webstore_fee_percent": PLATFORM_FEES["webstore_fee_percent"],
            "fee_display": "2.2% + $0.20 processing • 2% webstore fee",
        },
        
        # AI Credits
        "ai_credits": {
            "monthly_allowance": FOUNDERS_EDITION_MONTHLY_CREDITS,
            "monthly_credits_expire": True,
            "purchased_credits_expire": False,
            "credit_rollover": True,  # Purchased credits roll over
            "low_credits_threshold": LOW_CREDITS_THRESHOLD,
        },
        
        # Availability
        "availability": {
            "max_customers": FOUNDERS_EDITION_MAX_CUSTOMERS,
            "founder_lifetime_lock": True,
        },
        
        # Status
        "is_active": True,
        "is_default": True,
        "is_public": True,
        
        # Stripe
        "stripe": {
            "connect_enabled": True,
            "online_payments_enabled": True,
        },
        
        # All features ON - no restrictions
        "features": {
            "core": {
                "customers": "on",
                "jobs": "on",
                "invoices": "on",
                "online_invoice_payments": "on",
                "dashboard": "on",
                "employees": "unlimited",
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
        
        # UI visibility - all enabled
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


def get_credit_packs_for_api() -> list:
    """Get credit packs formatted for API response"""
    return [
        {
            "pack_type": pack["pack_id"],
            "credits": pack["credits"],
            "price": pack["price"],
            "price_cents": pack["price_cents"],
            "price_display": pack["price_display"],
            "per_credit": pack["per_credit"],
            "display_name": pack["display_name"],
            "description": pack["description"],
        }
        for pack in CREDIT_PACKS.values()
    ]


def get_fee_breakdown(transaction_amount_cents: int, is_webstore: bool = False) -> dict:
    """
    Get detailed fee breakdown for a transaction
    """
    platform_fee = calculate_platform_fee(transaction_amount_cents)
    webstore_fee = calculate_webstore_fee(transaction_amount_cents) if is_webstore else 0
    total_fees = platform_fee + webstore_fee
    net_amount = transaction_amount_cents - total_fees
    
    return {
        "transaction_amount": transaction_amount_cents / 100,
        "platform_fee": platform_fee / 100,
        "platform_fee_display": f"{PLATFORM_FEES['platform_processing_percent']}% + ${PLATFORM_FEES['platform_processing_fixed']:.2f}",
        "webstore_fee": webstore_fee / 100 if is_webstore else 0,
        "webstore_fee_display": f"{PLATFORM_FEES['webstore_fee_percent']}%" if is_webstore else None,
        "total_fees": total_fees / 100,
        "net_amount": net_amount / 100,
    }
