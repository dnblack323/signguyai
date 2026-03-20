"""
Founders Edition - The ONLY active plan.

All other tiers (Starter, Pro, Business, multi-product plans) are archived
and will only be activated after the Founders timeline is complete.
"""
import os

# ============== PLAN DEFINITION ==============
FOUNDERS_PLAN = {
    "plan_name": "Founders Edition",
    "plan_id": "founders_edition",
    "price_monthly": 99,
    "price_annual": 594,
    "founder_lifetime_lock": True,
    "founder_limit": 100,
    "ai_credits_monthly": 150,
    "monthly_credit_rollover": False,
    "purchased_credit_rollover": True,
    "plan_active": True,
    "plan_public": True,
    "all_features_included": True,
}

# ============== CREDIT PACKS ==============
CREDIT_PACKS = {
    "pack_small": {"credits": 100, "price": 10, "label": "100 Credits", "description": "100 AI credits"},
    "pack_medium": {"credits": 300, "price": 25, "label": "300 Credits", "description": "300 AI credits - 17% savings"},
    "pack_large": {"credits": 1000, "price": 60, "label": "1000 Credits", "description": "1000 AI credits - 40% savings"},
}

# ============== FEES ==============
PLATFORM_PROCESSING_PERCENT = 2.2
PLATFORM_PROCESSING_FIXED = 0.20
WEBSTORE_ADDITIONAL_PERCENT = 2.0

# ============== PROMO ==============
FOUNDERS_PROMO_CODE = "FOUNDERS"
FOUNDERS_PROMO_DISCOUNT_PERCENT = 50

# ============== STRIPE PRICE IDS ==============
STRIPE_PRICE_FOUNDERS_MONTHLY = os.environ.get("STRIPE_PRICE_FOUNDERS_MONTHLY", "")
STRIPE_PRICE_FOUNDERS_ANNUAL = os.environ.get("STRIPE_PRICE_FOUNDERS_ANNUAL", "")
STRIPE_PRICE_CREDITS_100 = os.environ.get("STRIPE_PRICE_CREDITS_100", "")
STRIPE_PRICE_CREDITS_300 = os.environ.get("STRIPE_PRICE_CREDITS_300", "")
STRIPE_PRICE_CREDITS_1000 = os.environ.get("STRIPE_PRICE_CREDITS_1000", "")
STRIPE_COUPON_FOUNDERS = os.environ.get("STRIPE_COUPON_FOUNDERS", "")

CREDIT_PACK_STRIPE_MAP = {
    "pack_small": STRIPE_PRICE_CREDITS_100,
    "pack_medium": STRIPE_PRICE_CREDITS_300,
    "pack_large": STRIPE_PRICE_CREDITS_1000,
}


def get_founders_plan():
    """Return the complete Founders Edition plan definition."""
    return {**FOUNDERS_PLAN}


def get_credit_packs():
    """Return available credit packs."""
    return [
        {"pack_id": k, **v, "stripe_price_id": CREDIT_PACK_STRIPE_MAP.get(k, "")}
        for k, v in CREDIT_PACKS.items()
    ]


def get_processing_fees():
    """Return the processing fee structure for Founders Edition."""
    return {
        "platform_processing_percent": PLATFORM_PROCESSING_PERCENT,
        "platform_processing_fixed": PLATFORM_PROCESSING_FIXED,
        "webstore_additional_percent": WEBSTORE_ADDITIONAL_PERCENT,
        "note": "Stripe's standard processing fees (typically 2.9% + $0.30) apply in addition to platform fees.",
    }


def get_founders_spot_count(db_count: int) -> dict:
    """Return spots remaining info."""
    return {
        "total_spots": FOUNDERS_PLAN["founder_limit"],
        "spots_taken": db_count,
        "spots_remaining": max(0, FOUNDERS_PLAN["founder_limit"] - db_count),
        "is_available": db_count < FOUNDERS_PLAN["founder_limit"],
    }
