"""
AI Credit System Models

Credit Types:
- Monthly credits: Included with Founders Edition, expire at month end
- Purchased credits: Bought via credit packs, never expire

Credit Packs:
- 100 credits for $10
- 300 credits for $25  
- 1000 credits for $60

Usage priority: Monthly credits used first, then purchased credits
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import uuid


class CreditPackType(str, Enum):
    """Available credit pack sizes"""
    PACK_100 = "pack_100"   # 100 credits for $10
    PACK_300 = "pack_300"   # 300 credits for $25
    PACK_1000 = "pack_1000" # 1000 credits for $60


# Credit pack definitions
CREDIT_PACKS = {
    CreditPackType.PACK_100: {
        "credits": 100,
        "price_cents": 1000,  # $10.00
        "display_name": "100 Credits",
        "description": "100 AI credits - never expire"
    },
    CreditPackType.PACK_300: {
        "credits": 300,
        "price_cents": 2500,  # $25.00
        "display_name": "300 Credits",
        "description": "300 AI credits - best value!"
    },
    CreditPackType.PACK_1000: {
        "credits": 1000,
        "price_cents": 6000,  # $60.00
        "display_name": "1000 Credits",
        "description": "1000 AI credits - power user pack"
    }
}


class CreditTransactionType(str, Enum):
    """Types of credit transactions"""
    MONTHLY_GRANT = "monthly_grant"       # Monthly credits added
    MONTHLY_EXPIRE = "monthly_expire"     # Monthly credits expired
    PACK_PURCHASE = "pack_purchase"       # Credit pack purchased
    AI_USAGE = "ai_usage"                 # Credits spent on AI action
    ADMIN_ADJUSTMENT = "admin_adjustment" # Manual adjustment by admin
    REFUND = "refund"                     # Credits refunded


class CreditTransaction(BaseModel):
    """Record of a credit transaction"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    transaction_type: CreditTransactionType
    amount: int  # Positive for additions, negative for deductions
    balance_after: int  # Total balance after transaction
    monthly_balance_after: int  # Monthly balance after transaction
    purchased_balance_after: int  # Purchased balance after transaction
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)  # e.g., ai_action_id, pack_type, stripe_payment_id
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserCredits(BaseModel):
    """User's credit balance and settings"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    
    # Credit balances
    monthly_credits: int = 0           # Expire at month end
    purchased_credits: int = 0         # Never expire
    
    # Monthly credit tracking
    monthly_credits_granted_at: Optional[str] = None  # When monthly credits were last granted
    monthly_credits_period_start: Optional[str] = None  # Start of current billing period
    monthly_credits_period_end: Optional[str] = None    # End of current billing period
    
    # Low credits warning threshold
    low_credits_threshold: int = 20
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    @property
    def total_credits(self) -> int:
        """Total available credits"""
        return self.monthly_credits + self.purchased_credits
    
    @property
    def is_low_credits(self) -> bool:
        """Check if credits are below warning threshold"""
        return self.total_credits <= self.low_credits_threshold


class CreditUsageRequest(BaseModel):
    """Request to use credits for an AI action"""
    action_type: str  # e.g., "image_generation", "text_generation", "ai_assistant"
    credits_required: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreditUsageResponse(BaseModel):
    """Response after using credits"""
    success: bool
    credits_used: int
    monthly_credits_used: int
    purchased_credits_used: int
    remaining_monthly: int
    remaining_purchased: int
    remaining_total: int
    is_low_credits: bool
    message: str


class CreditBalanceResponse(BaseModel):
    """Credit balance information for UI"""
    monthly_credits: int
    purchased_credits: int
    total_credits: int
    is_low_credits: bool
    low_credits_threshold: int
    monthly_credits_period_end: Optional[str] = None
    days_until_refill: Optional[int] = None


class PurchaseCreditPackRequest(BaseModel):
    """Request to purchase a credit pack"""
    pack_type: CreditPackType


class PurchaseCreditPackResponse(BaseModel):
    """Response after credit pack purchase intent"""
    checkout_url: str
    session_id: str


# ============== FOUNDERS EDITION PROMO CODES ==============

class PromoCode(BaseModel):
    """Promo code for Founders Edition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # e.g., "FOUNDERS"
    description: str
    discount_type: str = "annual_50_percent"  # Pay 6 months, get 12 months
    max_uses: int = 100  # Limited to 100 customers
    current_uses: int = 0
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None


class PromoCodeUsage(BaseModel):
    """Record of promo code use"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    promo_code_id: str
    tenant_id: str
    user_id: str
    discount_applied: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
