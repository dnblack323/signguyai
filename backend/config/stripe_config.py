"""
Stripe Price Configuration - Founders Edition v1

CONFIGURATION: founder_pricing_v1
STATUS: ACTIVE

This configuration implements the simplified Founders Edition pricing:
- Single plan: $99/month or $1188/year ($594 with FOUNDERS promo)
- Credit packs: $10 (100), $25 (300), $60 (1000)
- All features unlocked, no tiers

Create these in Stripe Dashboard:
1. Product: "Founders Edition" 
   - Monthly Price: $99/month (recurring)
   - Annual Price: $1188/year (recurring)
2. Product: "AI Credits - 100 Pack" - $10 (one-time)
3. Product: "AI Credits - 300 Pack" - $25 (one-time)
4. Product: "AI Credits - 1000 Pack" - $60 (one-time)
5. Coupon: "FOUNDERS" - 50% off, first payment only, limit 100 uses
"""

import os
from typing import Optional, Dict


class FounderPricingConfig:
    """Founders Edition Pricing Configuration - v1"""
    
    # Environment variable mappings
    ENV_VARS = {
        # Subscription prices
        "founders_monthly": "STRIPE_PRICE_FOUNDERS_MONTHLY",
        "founders_annual": "STRIPE_PRICE_FOUNDERS_ANNUAL",
        
        # Credit pack prices (one-time)
        "credits_100": "STRIPE_PRICE_CREDITS_100",
        "credits_300": "STRIPE_PRICE_CREDITS_300",
        "credits_1000": "STRIPE_PRICE_CREDITS_1000",
        
        # Promo code
        "founders_coupon": "STRIPE_COUPON_FOUNDERS",
    }
    
    # Pricing details
    PRICING = {
        "monthly": 99.00,
        "annual": 1188.00,
        "annual_with_promo": 594.00,
        "credits_100": 10.00,
        "credits_300": 25.00,
        "credits_1000": 60.00,
    }
    
    # Founder promo rules
    FOUNDER_PROMO = {
        "code": "FOUNDERS",
        "discount_percent": 50,
        "applies_to": "annual",
        "max_uses": 100,
        "first_payment_only": True,
    }
    
    @classmethod
    def get_subscription_price_id(cls, interval: str = "monthly") -> Optional[str]:
        """Get Stripe Price ID for subscription"""
        key = f"founders_{interval}"
        env_var = cls.ENV_VARS.get(key)
        if env_var:
            return os.environ.get(env_var)
        return None
    
    @classmethod
    def get_credit_pack_price_id(cls, credits: int) -> Optional[str]:
        """Get Stripe Price ID for credit pack"""
        key = f"credits_{credits}"
        env_var = cls.ENV_VARS.get(key)
        if env_var:
            return os.environ.get(env_var)
        return None
    
    @classmethod
    def get_founders_coupon_id(cls) -> Optional[str]:
        """Get Stripe Coupon ID for FOUNDERS promo"""
        env_var = cls.ENV_VARS.get("founders_coupon")
        if env_var:
            return os.environ.get(env_var)
        return None
    
    @classmethod
    def has_stripe_configured(cls) -> bool:
        """Check if required Stripe IDs are configured"""
        required = ["founders_monthly"]
        return all(os.environ.get(cls.ENV_VARS.get(k)) for k in required)
    
    @classmethod
    def get_all_configured(cls) -> Dict[str, str]:
        """Get all configured Stripe IDs"""
        configured = {}
        for key, env_var in cls.ENV_VARS.items():
            value = os.environ.get(env_var)
            if value:
                configured[key] = value
        return configured


# Legacy compatibility - map old tier system to founders
class StripePriceConfig:
    """Legacy compatibility layer - redirects to FounderPricingConfig"""
    
    @classmethod
    def get_price_id(cls, plan: str, interval: str = "monthly", is_founder: bool = True) -> Optional[str]:
        """Get Stripe Price ID - all plans map to Founders Edition"""
        return FounderPricingConfig.get_subscription_price_id(interval)
    
    @classmethod
    def has_stripe_prices_configured(cls) -> bool:
        """Check if Stripe is configured"""
        return FounderPricingConfig.has_stripe_configured()
    
    @classmethod
    def get_all_configured_prices(cls) -> Dict[str, str]:
        """Get all configured prices"""
        return FounderPricingConfig.get_all_configured()


# Credit pack mapping
CREDIT_PACK_MAPPING = {
    100: {"price": 10.00, "env_var": "STRIPE_PRICE_CREDITS_100"},
    300: {"price": 25.00, "env_var": "STRIPE_PRICE_CREDITS_300"},
    1000: {"price": 60.00, "env_var": "STRIPE_PRICE_CREDITS_1000"},
}

# AI Credit cost rules
AI_CREDIT_COSTS = {
    "light": 1,      # Small text responses, assistant replies, light formatting
    "moderate": 2,   # Content generation, image edits
    "heavy": 3,      # Complex design actions, heavier processing
    "premium": 5,    # Future high-compute actions
}
