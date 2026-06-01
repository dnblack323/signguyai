"""
Dev / Admin Testing Routes.

These endpoints exist for developer testing and admin self-service so an
operator can flip a tenant into different subscription / credit states
without leaving the app. They mutate billing and credit state, so the
blast radius if they leak into a real production environment is high.

Two safeguards layered on top of role checks:

1. ``ENABLE_DEV_PANEL`` env flag — the router is only included in
   ``server.py`` when this is ``"true"``. The flag is left ON in the
   preview/dev environment and OFF in production deployments.
2. Canonical JWT verifier — the auth dependency is the same
   ``get_current_active_user`` every other route uses. The previous
   bespoke ``jwt.decode(... SECRET_KEY ...)`` with a fallback default
   secret has been removed so a missing env var can no longer silently
   accept tokens minted against the wrong key.
"""

import os
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

# Canonical singletons — same db + secret + user resolver every other
# route uses. No bespoke jwt.decode, no fallback secret.
from core_runtime import db, get_current_active_user
from models import UserInDB


router = APIRouter(prefix="/dev", tags=["dev"])

# Admin emails that can access dev endpoints
ADMIN_EMAILS = [
    "thesigntistslab@gmail.com",
]


def is_dev_panel_enabled() -> bool:
    """Single source of truth for dev-panel availability."""
    return os.environ.get("ENABLE_DEV_PANEL", "").strip().lower() == "true"


def _check_dev_panel_enabled():
    if not is_dev_panel_enabled():
        raise HTTPException(
            status_code=404,
            detail="Not found",
        )


def _check_admin(user: UserInDB):
    """Belt-and-braces admin gate on top of the env flag."""
    email = (getattr(user, "email", "") or "").lower()
    if email in [e.lower() for e in ADMIN_EMAILS]:
        return
    if getattr(user, "is_admin", False) or getattr(user, "is_founder", False):
        return
    raise HTTPException(status_code=403, detail="Admin access required")


def _dev_dependency(user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
    """All dev mutations route through this gate.

    Two layers: env flag must be on (else 404), and the calling user must
    be an admin (else 403). Returns the resolved canonical user object so
    handlers can reference ``user.tenant_id`` directly.
    """
    _check_dev_panel_enabled()
    _check_admin(user)
    return user


class SetSubscriptionModeRequest(BaseModel):
    mode: str  # founders_edition, free_trial, trial_expired, os_pro, os_starter, webstores_only


class SetCreditsRequest(BaseModel):
    credits: int


@router.get("/enabled")
async def get_dev_panel_enabled():
    """Public probe — lets the frontend hide the Dev Panel widget in prod."""
    return {"enabled": is_dev_panel_enabled()}


@router.post("/set-subscription-mode")
async def set_subscription_mode(
    request: SetSubscriptionModeRequest,
    current_user: UserInDB = Depends(_dev_dependency),
):
    """Set the subscription mode for testing different states."""
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
        {"id": current_user.tenant_id},
        {"$set": update_data},
    )
    return {"success": True, "mode": request.mode, "updated": update_data}


@router.post("/set-credits")
async def set_credits(
    request: SetCreditsRequest,
    current_user: UserInDB = Depends(_dev_dependency),
):
    """Set the credit balance for testing."""
    now = datetime.now(timezone.utc)
    tenant_id = current_user.tenant_id

    credits_doc = await db.user_credits.find_one({"tenant_id": tenant_id})
    if credits_doc:
        await db.user_credits.update_one(
            {"tenant_id": tenant_id},
            {"$set": {
                "monthly_credits": request.credits,
                "is_unlimited": request.credits >= 999999,
                "updated_at": now.isoformat(),
            }},
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
    current_user: UserInDB = Depends(_dev_dependency),
):
    """Reset account to full admin defaults."""
    now = datetime.now(timezone.utc)
    tenant_id = current_user.tenant_id
    user_id = current_user.id

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
        }},
    )
    await db.user_credits.update_one(
        {"tenant_id": tenant_id},
        {"$set": {
            "monthly_credits": 999999,
            "purchased_credits": 999999,
            "is_unlimited": True,
            "updated_at": now.isoformat(),
        }},
    )
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "is_admin": True,
            "is_founder": True,
            "updated_at": now.isoformat(),
        }},
    )
    return {"success": True, "message": "Reset to admin defaults"}


@router.get("/status")
async def get_dev_status(
    current_user: UserInDB = Depends(_dev_dependency),
):
    """Get current dev/admin status."""
    tenant_id = current_user.tenant_id
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    credits = await db.user_credits.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return {
        "user": {
            "email": current_user.email,
            "is_admin": getattr(current_user, "is_admin", False),
            "is_founder": getattr(current_user, "is_founder", False),
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
        },
    }
