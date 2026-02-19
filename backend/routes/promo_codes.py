"""
Promo Codes Routes

Admin-only routes for managing promotional codes for SignGuy AI subscriptions.
- Create, update, delete promo codes
- Validate promo codes during checkout
- Track usage statistics
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
import uuid

from server import db, get_current_active_user
from models import UserInDB


router = APIRouter(prefix="/promo-codes", tags=["Promo Codes"])


# Pydantic Models
class PromoCodeCreate(BaseModel):
    code: str  # e.g., "FRIEND2024", "BETATESTER"
    description: Optional[str] = None
    discount_type: str  # "percent", "fixed", "free_trial"
    discount_value: float = 0  # percent off or fixed amount
    trial_days: int = 0  # for free_trial type, number of days
    max_uses: Optional[int] = None  # None = unlimited
    expires_at: Optional[str] = None  # ISO date string
    is_active: bool = True


class PromoCodeUpdate(BaseModel):
    description: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    trial_days: Optional[int] = None
    max_uses: Optional[int] = None
    expires_at: Optional[str] = None
    is_active: Optional[bool] = None


class PromoCodeResponse(BaseModel):
    id: str
    code: str
    description: Optional[str]
    discount_type: str
    discount_value: float
    trial_days: int
    max_uses: Optional[int]
    times_used: int
    expires_at: Optional[str]
    is_active: bool
    created_at: str


class PromoCodeValidation(BaseModel):
    code: str


class PromoCodeValidationResponse(BaseModel):
    valid: bool
    message: str
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    trial_days: Optional[int] = None


# Helper to check if user is admin/owner
def require_admin(user: UserInDB):
    if user.role not in ['owner', 'admin']:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("", response_model=List[PromoCodeResponse])
async def list_promo_codes(current_user: UserInDB = Depends(get_current_active_user)):
    """List all promo codes (admin only)"""
    require_admin(current_user)
    
    codes = await db.promo_codes.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return codes


@router.post("", response_model=PromoCodeResponse)
async def create_promo_code(
    data: PromoCodeCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new promo code (admin only)"""
    require_admin(current_user)
    
    # Check if code already exists
    existing = await db.promo_codes.find_one({
        "code": data.code.upper(),
        "tenant_id": current_user.tenant_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Promo code already exists")
    
    # Validate discount type
    if data.discount_type not in ['percent', 'fixed', 'free_trial']:
        raise HTTPException(status_code=400, detail="Invalid discount type")
    
    promo_code = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "code": data.code.upper(),
        "description": data.description,
        "discount_type": data.discount_type,
        "discount_value": data.discount_value,
        "trial_days": data.trial_days if data.discount_type == 'free_trial' else 0,
        "max_uses": data.max_uses,
        "times_used": 0,
        "expires_at": data.expires_at,
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    await db.promo_codes.insert_one(promo_code)
    del promo_code["_id"]
    
    return promo_code


@router.put("/{code_id}", response_model=PromoCodeResponse)
async def update_promo_code(
    code_id: str,
    data: PromoCodeUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a promo code (admin only)"""
    require_admin(current_user)
    
    # Find existing code
    existing = await db.promo_codes.find_one({
        "id": code_id,
        "tenant_id": current_user.tenant_id
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    # Build update
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    
    if update_data:
        await db.promo_codes.update_one(
            {"id": code_id},
            {"$set": update_data}
        )
    
    # Return updated code
    updated = await db.promo_codes.find_one({"id": code_id}, {"_id": 0})
    return updated


@router.delete("/{code_id}")
async def delete_promo_code(
    code_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a promo code (admin only)"""
    require_admin(current_user)
    
    result = await db.promo_codes.delete_one({
        "id": code_id,
        "tenant_id": current_user.tenant_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    return {"message": "Promo code deleted"}


@router.post("/validate", response_model=PromoCodeValidationResponse)
async def validate_promo_code(data: PromoCodeValidation):
    """
    Validate a promo code (public endpoint for checkout).
    Does not require authentication so users can validate during signup.
    """
    code = data.code.upper().strip()
    
    # Find the promo code (across all tenants for now - could be scoped)
    promo = await db.promo_codes.find_one({
        "code": code,
        "is_active": True
    }, {"_id": 0})
    
    if not promo:
        return PromoCodeValidationResponse(
            valid=False,
            message="Invalid promo code"
        )
    
    # Check expiration
    if promo.get("expires_at"):
        expires = datetime.fromisoformat(promo["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            return PromoCodeValidationResponse(
                valid=False,
                message="This promo code has expired"
            )
    
    # Check max uses
    if promo.get("max_uses") is not None:
        if promo.get("times_used", 0) >= promo["max_uses"]:
            return PromoCodeValidationResponse(
                valid=False,
                message="This promo code has reached its usage limit"
            )
    
    # Valid!
    return PromoCodeValidationResponse(
        valid=True,
        message="Promo code applied!",
        discount_type=promo["discount_type"],
        discount_value=promo.get("discount_value", 0),
        trial_days=promo.get("trial_days", 0)
    )


@router.post("/redeem/{code}")
async def redeem_promo_code(
    code: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Redeem a promo code (increment usage counter).
    Called after successful checkout/signup.
    """
    code = code.upper().strip()
    
    result = await db.promo_codes.update_one(
        {"code": code, "is_active": True},
        {"$inc": {"times_used": 1}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Promo code not found")
    
    return {"message": "Promo code redeemed"}
