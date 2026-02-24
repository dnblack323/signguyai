"""
Stripe Price Configuration

Maps subscription plans to Stripe Price IDs.
Create these prices in the Stripe Dashboard first.

For each plan, create:
- A Product (e.g., "Starter Plan")
- Recurring Prices (monthly and annual)
"""

import os
from typing import Optional, Dict
from enum import Enum


class StripePriceConfig:
    """Configuration for Stripe Price IDs"""
    
    # Environment variable names for each plan/interval
    PRICE_ENV_VARS = {
        # Founder pricing
        ("tier_1", "monthly", True): "STRIPE_PRICE_STARTER_MONTHLY",
        ("tier_2", "monthly", True): "STRIPE_PRICE_PRO_MONTHLY",
        ("tier_3", "monthly", True): "STRIPE_PRICE_BUSINESS_MONTHLY",
        ("ai_addon", "monthly", True): "STRIPE_PRICE_AI_ADDON_MONTHLY",
        ("tier_1", "annual", True): "STRIPE_PRICE_STARTER_ANNUAL",
        ("tier_2", "annual", True): "STRIPE_PRICE_PRO_ANNUAL",
        ("tier_3", "annual", True): "STRIPE_PRICE_BUSINESS_ANNUAL",
        ("ai_addon", "annual", True): "STRIPE_PRICE_AI_ADDON_ANNUAL",
        # Standard pricing
        ("tier_1", "monthly", False): "STRIPE_PRICE_STARTER_MONTHLY_STD",
        ("tier_2", "monthly", False): "STRIPE_PRICE_PRO_MONTHLY_STD",
        ("tier_3", "monthly", False): "STRIPE_PRICE_BUSINESS_MONTHLY_STD",
        ("ai_addon", "monthly", False): "STRIPE_PRICE_AI_ADDON_MONTHLY_STD",
        # Extended trial (one-time)
        ("extended_trial", "monthly", True): "STRIPE_PRICE_EXTENDED_TRIAL",
        ("extended_trial", "monthly", False): "STRIPE_PRICE_EXTENDED_TRIAL",
    }
    
    @classmethod
    def get_price_id(cls, plan: str, interval: str = "monthly", is_founder: bool = True) -> Optional[str]:
        """Get Stripe Price ID for a plan"""
        key = (plan, interval, is_founder)
        env_var = cls.PRICE_ENV_VARS.get(key)
        if env_var:
            return os.environ.get(env_var)
        return None
    
    @classmethod
    def has_stripe_prices_configured(cls) -> bool:
        """Check if Stripe price IDs are configured"""
        # Check for at least the basic monthly prices
        required_vars = [
            "STRIPE_PRICE_STARTER_MONTHLY",
            "STRIPE_PRICE_PRO_MONTHLY",
            "STRIPE_PRICE_BUSINESS_MONTHLY"
        ]
        return all(os.environ.get(var) for var in required_vars)
    
    @classmethod
    def get_all_configured_prices(cls) -> Dict[str, str]:
        """Get all configured Stripe price IDs"""
        prices = {}
        for key, env_var in cls.PRICE_ENV_VARS.items():
            price_id = os.environ.get(env_var)
            if price_id:
                prices[f"{key[0]}_{key[1]}_{'founder' if key[2] else 'std'}"] = price_id
        return prices


# Map plan names to tier keys
PLAN_TO_TIER = {
    "tier_1": "starter",
    "tier_2": "pro",
    "tier_3": "business",
    "ai_addon": "ai_addon",
    "extended_trial": "business",  # Extended trial gets business tier access
}

# Map product categories to JobItemType
CATEGORY_TO_JOB_TYPE = {
    "apparel": "apparel",
    "signs": "sign",
    "decals": "decal",
    "promotional": "promo",
    "other": "other",
}
