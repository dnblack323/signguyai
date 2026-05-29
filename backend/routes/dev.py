"""
Dev/Admin API Routes

These endpoints are for testing and admin purposes only.
They allow switching subscription modes and setting credits for testing different states.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
import jwt
import os

router = APIRouter(prefix="/dev", tags=["dev"])

# Admin emails that can access dev endpoints
ADMIN_EMAILS = [
    "thesigntistslab@gmail.com",
]

security = HTTPBearer(auto_error=False)


class SetSubscriptionModeRequest(BaseModel):
    mode: str  # founders_edition, free_trial, trial_expired, os_pro, os_starter, webstores_only


class SetCreditsRequest(BaseModel):
    credits: int


async def get_db():
    """Get database connection"""
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGO_URL = os.environ.get("MONGO_URL")
    DB_NAME = os.environ.get("DB_NAME", "signguy_ai")
    client = AsyncIOMotorClient(MONGO_URL)
    return client[DB_NAME]


async def get_current_user_dev(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current user from token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")

    jwt_secret_key = os.environ.get("JWT_SECRET_KEY", "").strip()
    if not jwt_secret_key:
        raise HTTPException(
            status_code=500,
            detail="Dev routes misconfigured: JWT_SECRET_KEY is required",
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            request.app.state.secret_key,
            algorithms=[request.app.state.algorithm],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db = await get_db()
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def check_admin(user: dict):
    """Check if user is admin"""
    email = user.get("email", "").lower()
    if email not in [e.lower() for e in ADMIN_EMAILS]:
        if not user.get('is_admin', False) and not user.get('is_founder', False):
            raise HTTPException(status_code=403, detail="Admin access required")


@router.post("/set-subscription-mode")
async def set_subscription_mode(
    request: SetSubscriptionModeRequest,
    current_user: dict = Depends(get_current_user_dev)
):
    """Set the subscription mode for testing different states"""
    check_admin(current_user)
    
    db = await get_db()
    now = datetime.now(timezone.utc)
    update_data = {}
    
    if request.mode == "founders_edition":
        update_data = {
            "plan": "founders_edition",
            "plan_name": "Founders Edition",
            "is_trial": False,
            "founder_lifetime_lock": True,
            "subscription_status": "active",
            "trial_ends_at": None,
        }
    elif request.mode == "free_trial":
        # Set trial to end in 48 hours
        trial_end = now + timedelta(hours=48)
        update_data = {
            "plan": "free_trial",
            "plan_name": "48-Hour Free Trial",
            "is_trial": True,
            "founder_lifetime_lock": False,
            "subscription_status": "trialing",
            "trial_started_at": now.isoformat(),
            "trial_ends_at": trial_end.isoformat(),
        }
    elif request.mode == "trial_expired":
        # Set trial to have ended 1 hour ago
        trial_end = now - timedelta(hours=1)
        update_data = {
            "plan": "free_trial",
            "plan_name": "48-Hour Free Trial (Expired)",
            "is_trial": True,
            "founder_lifetime_lock": False,
            "subscription_status": "locked",
            "trial_started_at": (now - timedelta(hours=49)).isoformat(),
            "trial_ends_at": trial_end.isoformat(),
        }
    elif request.mode == "os_pro":
        update_data = {
            "plan": "os_pro",
            "plan_name": "OS Pro",
            "is_trial": False,
            "founder_lifetime_lock": False,
            "subscription_status": "active",
            "trial_ends_at": None,
        }
    elif request.mode == "os_starter":
        update_data = {
            "plan": "os_starter",
            "plan_name": "OS Starter",
            "is_trial": False,
            "founder_lifetime_lock": False,
            "subscription_status": "active",
            "trial_ends_at": None,
        }
    elif request.mode == "webstores_only":
        update_data = {
            "plan": "webstores_only",
            "plan_name": "Webstores Only",
            "is_trial": False,
            "founder_lifetime_lock": False,
            "subscription_status": "active",
            "trial_ends_at": None,
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {request.mode}")
    
    update_data["updated_at"] = now.isoformat()
    
    await db.tenants.update_one(
        {"id": current_user.get("tenant_id")},
        {"$set": update_data}
    )
    
    return {"success": True, "mode": request.mode, "updated": update_data}


@router.post("/set-credits")
async def set_credits(
    request: SetCreditsRequest,
    current_user: dict = Depends(get_current_user_dev)
):
    """Set the credit balance for testing"""
    check_admin(current_user)
    
    db = await get_db()
    now = datetime.now(timezone.utc)
    tenant_id = current_user.get("tenant_id")
    
    # Update or create credits record
    credits_doc = await db.user_credits.find_one({"tenant_id": tenant_id})
    
    if credits_doc:
        await db.user_credits.update_one(
            {"tenant_id": tenant_id},
            {"$set": {
                "monthly_credits": request.credits,
                "is_unlimited": request.credits >= 999999,
                "updated_at": now.isoformat(),
            }}
        )
    else:
        await db.user_credits.insert_one({
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "monthly_credits": request.credits,
            "purchased_credits": 0,
            "is_unlimited": request.credits >= 999999,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        })
    
    return {"success": True, "credits": request.credits}


@router.post("/reset-to-admin")
async def reset_to_admin(
    current_user: dict = Depends(get_current_user_dev)
):
    """Reset account to full admin defaults"""
    check_admin(current_user)
    
    db = await get_db()
    now = datetime.now(timezone.utc)
    tenant_id = current_user.get("tenant_id")
    user_id = current_user.get("id")
    
    # Reset tenant to Founders Edition admin
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {
            "plan": "founders_edition",
            "plan_name": "Founders Edition (Admin)",
            "is_trial": False,
            "founder_lifetime_lock": True,
            "is_admin": True,
            "is_founder": True,
            "subscription_status": "active",
            "trial_ends_at": None,
            "updated_at": now.isoformat(),
        }}
    )
    
    # Reset credits to unlimited
    await db.user_credits.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "monthly_credits": 999999,
            "purchased_credits": 999999,
            "is_unlimited": True,
            "updated_at": now.isoformat(),
        }}
    )
    
    # Update user flags
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_admin": True,
            "is_founder": True,
            "updated_at": now.isoformat(),
        }}
    )
    
    return {"success": True, "message": "Reset to admin defaults"}


@router.get("/status")
async def get_dev_status(
    current_user: dict = Depends(get_current_user_dev)
):
    """Get current dev/admin status"""
    check_admin(current_user)
    
    db = await get_db()
    tenant_id = current_user.get("tenant_id")
    
    tenant = await db.tenants.find_one(
        {"id": tenant_id},
        {"_id": 0}
    )
    
    credits = await db.user_credits.find_one(
        {"tenant_id": tenant_id},
        {"_id": 0}
    )
    
    return {
        "user": {
            "email": current_user.get("email"),
            "is_admin": current_user.get('is_admin', False),
            "is_founder": current_user.get('is_founder', False),
        },
        "tenant": {
            "plan": tenant.get("plan") if tenant else None,
            "plan_name": tenant.get("plan_name") if tenant else None,
            "is_trial": tenant.get("is_trial") if tenant else None,
            "subscription_status": tenant.get("subscription_status") if tenant else None,
        },
        "credits": {
            "monthly": credits.get("monthly_credits") if credits else 0,
            "purchased": credits.get("purchased_credits") if credits else 0,
            "is_unlimited": credits.get("is_unlimited") if credits else False,
        }
    }
