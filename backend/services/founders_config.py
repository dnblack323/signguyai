"""
Founders Edition Plan Configuration

The ONLY active pricing plan for new signups:
- Price: $99/month
- Annual: $594 for 12 months with promo code FOUNDERS
- Limited to 100 customers (lifetime lock)
- 150 AI credits per month (rollover enabled for purchased credits)
- All features included, no restrictions

48-Hour Free Trial:
- No credit card required
- All features available
- 50 AI credits (one-time, non-refilling)
- Sample data provided to explore the platform
- Webstores: Can create stores/products but cannot make them "live"
- After 48 hours: Full lockout until subscription

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
# 48-HOUR FREE TRIAL CONFIGURATION
# =============================================================================

FREE_TRIAL_CONFIG = {
    "trial_hours": 48,
    "trial_credits": 50,  # One-time credits for trial
    "require_card": False,
    "all_features_enabled": True,
    "webstores_can_go_live": False,  # Can create, cannot publish
    "sample_data_enabled": True,
}

FREE_TRIAL_HOURS = FREE_TRIAL_CONFIG["trial_hours"]
FREE_TRIAL_CREDITS = FREE_TRIAL_CONFIG["trial_credits"]

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

# Exact application tool/action mappings from the live codebase
AI_CREDIT_COSTS.update({
    # Design/image generation tools (HIGH = 3)
    "logo_refresher": 3,
    "generative_fill": 3,
    "text_to_image": 3,
    "ai_sign_designer": 3,
    "ai_banner_designer": 3,
    "mockup_creator": 3,
    "vehicle_wrap_mockup": 3,
    "logo_creator": 3,
    "race_number_designer": 3,
    "driver_name_plate": 3,
    "race_team_branding": 3,
    "historical_invoice_analysis": 3,

    # Medium tools (2)
    "permit_research": 2,
    "photo_enhancer": 2,
    "image_vectorizer": 2,
    "font_identifier": 2,
    "branding_kit_generator": 2,
    "business_copywriter": 2,
    "document_composer": 2,
    "pricing_intelligence": 2,
    "blog_creator": 2,
    "completed_job_post": 2,
    "social_pack_generator": 2,
    "content_calendar": 2,
    "campaign_builder": 2,
    "wrap_cost_calculator": 2,
    "product_description": 2,
    "ai_business_assistant": 2,
    "assistant_chat": 2,

    # Low tools (1)
    "idea_brainstormer": 1,
    "social_job_post": 1,
    "pricing_advisor": 1,
    "tagline_generator": 1,
    "brand_color_advisor": 1,
    "brand_voice_guide": 1,
    "review_responder": 1,
    "assistant_parse_action": 1,
    "voice_transcription": 1,
    "voice_tts": 1,
    "invoice_send": 1,
    "invoice_reminder": 1,
    "invoice_overdue": 1,
    "quote_send": 1,
    "quote_followup": 1,
    "approval_request": 1,
    "job_update": 1,
    "job_complete": 1,
    "thank_you": 1,

    # Hidden but callable backend-only tools
    "proposal_writer": 2,
    "email_templates": 2,
    "seo_content": 2,
    "showcase_post": 2,

    # Internal AI pipeline actions
    "historical_invoice_pdf_extract": 3,
    "historical_invoice_benchmark_synthesis": 2,
    # Services AI prefill — low cost, structured JSON output
    "ai_services_prefill": 1,
})

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
        "description": "Early adopter exclusive - all features, unified productivity, signatures/drawings, and 150 AI credits/month",
        
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


def get_fee_explanation() -> dict:
    """
    Get detailed explanations of what the fees cover and why they exist.
    Use this for FAQ sections and anywhere fees are displayed.
    """
    return {
        "platform_fee": {
            "rate": f"{PLATFORM_FEES['platform_processing_percent']}% + ${PLATFORM_FEES['platform_processing_fixed']:.2f}",
            "short_description": "Platform Processing Fee",
            "explanation": (
                "This fee covers secure payment processing through Stripe, fraud protection and chargeback defense, "
                "encrypted data storage, platform infrastructure and uptime, and continuous feature development. "
                "For comparison, Stripe alone charges 2.9% + $0.30 — our bundled rate gives you more value at a lower cost."
            ),
            "what_it_covers": [
                "Secure payment processing via Stripe",
                "Fraud protection & chargeback defense",
                "Encrypted data storage & backups",
                "Platform infrastructure & 99.9% uptime",
                "Continuous feature updates & improvements",
            ],
        },
        "webstore_fee": {
            "rate": f"{PLATFORM_FEES['webstore_fee_percent']}%",
            "short_description": "Webstore Sales Fee",
            "explanation": (
                "This fee only applies when you make sales through your webstores. It covers hosted storefront infrastructure, "
                "CDN delivery for fast loading, order management and fulfillment tracking, customer checkout experience, "
                "and inventory sync across stores. You only pay this when your webstores generate revenue."
            ),
            "what_it_covers": [
                "Hosted storefront infrastructure",
                "CDN delivery for fast global loading",
                "Order management & fulfillment tracking",
                "Secure customer checkout experience",
                "Inventory sync across multiple stores",
            ],
            "when_charged": "Only charged when you make sales through your webstores",
        },
        "comparison": {
            "stripe_standard": "2.9% + $0.30",
            "our_platform": f"{PLATFORM_FEES['platform_processing_percent']}% + ${PLATFORM_FEES['platform_processing_fixed']:.2f}",
            "savings_note": "You save money while getting more features bundled in",
        },
        "summary": (
            "Our fees are designed to be transparent and competitive. The platform fee covers everything "
            "from payment processing to feature development, while the webstore fee only kicks in when "
            "you're actually making sales. No hidden costs, no surprises."
        ),
    }
