"""
Platform Admin Routes - Minimal MVP for Tenant Impersonation

This module provides:
1. Tenant list
2. Tenant detail with users
3. Impersonate tenant user
4. Exit impersonation
5. Impersonation logs
6. Onboarding checklist management
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import html as _html_lib
import uuid

from models import UserRole, User
from server import (
    db, logger,
    get_current_user, create_access_token, UserInDB
)
from services.admin_audit import log_admin_action

router = APIRouter(prefix="/platform-admin", tags=["Platform Admin"])


# ============== MODELS ==============

class ImpersonationLog(BaseModel):
    id: str
    platform_admin_user_id: str
    platform_admin_email: str
    target_user_id: str
    target_user_email: str
    tenant_id: str
    tenant_name: str
    started_at: str
    ended_at: Optional[str] = None
    duration_seconds: Optional[int] = None


class OnboardingChecklistItem(BaseModel):
    id: str
    tenant_id: str
    item_key: str
    label: str
    completed: bool = False
    note: Optional[str] = None
    updated_by: Optional[str] = None
    updated_by_email: Optional[str] = None
    updated_at: Optional[str] = None
    order: int


class UpdateChecklistItemRequest(BaseModel):
    completed: bool
    note: Optional[str] = None


class TenantListItem(BaseModel):
    id: str
    name: str
    owner_email: str
    plan: str
    created_at: str
    user_count: int
    is_active: bool = True
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None


class TenantDetail(BaseModel):
    id: str
    name: str
    slug: str
    owner_email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    plan: str
    is_active: bool = True
    created_at: str
    updated_at: str
    suspension_reason: Optional[str] = None
    suspended_at: Optional[str] = None
    suspended_by_email: Optional[str] = None
    reactivated_at: Optional[str] = None
    reactivated_by_email: Optional[str] = None
    # Dunning state
    payment_failed_count: int = 0
    first_payment_failure_at: Optional[str] = None
    last_payment_failure_at: Optional[str] = None
    last_payment_succeeded_at: Optional[str] = None
    auto_suspended_for_payment: bool = False
    grace_period_until: Optional[str] = None
    dunning_failure_threshold: Optional[int] = None
    is_founder: bool = False


class ImpersonateRequest(BaseModel):
    target_user_id: str


class SuspendTenantRequest(BaseModel):
    reason: str


class ReactivateTenantRequest(BaseModel):
    note: Optional[str] = None
    notify_owner: bool = True


class MarkPaidRequest(BaseModel):
    note: Optional[str] = None


class DunningThresholdRequest(BaseModel):
    threshold: Optional[int] = None  # None = use global default


async def _enrich_with_founder_flag(tenant: dict) -> dict:
    """Attach a computed `is_founder` flag based on the tenant's users."""
    if not tenant:
        return tenant
    has_founder = await db.users.count_documents(
        {"tenant_id": tenant["id"], "is_founder": True}
    )
    tenant["is_founder"] = has_founder > 0
    return tenant


# ============== CONSTANTS ==============

DEFAULT_CHECKLIST_ITEMS = [
    {"key": "business_info", "label": "Business info received", "order": 1},
    {"key": "logo_uploaded", "label": "Logo received/uploaded", "order": 2},
    {"key": "owner_created", "label": "Owner/admin user created", "order": 3},
    {"key": "users_invited", "label": "Employee/users invited", "order": 4},
    {"key": "product_categories", "label": "Product categories selected", "order": 5},
    {"key": "materials_entered", "label": "Materials entered", "order": 6},
    {"key": "labor_rates", "label": "Labor rates entered", "order": 7},
    {"key": "markups_minimums", "label": "Markups/minimums entered", "order": 8},
    {"key": "pricing_reviewed", "label": "Pricing foundation reviewed", "order": 9},
    {"key": "first_quote_tested", "label": "First quote/order tested", "order": 10},
    {"key": "customer_approval_tested", "label": "Customer approval workflow tested", "order": 11},
    {"key": "production_tested", "label": "Production workflow tested", "order": 12},
    {"key": "customer_portal_reviewed", "label": "Customer portal reviewed", "order": 13},
    {"key": "employee_portal_reviewed", "label": "Employee portal reviewed", "order": 14},
    {"key": "ai_tools_reviewed", "label": "AI tools reviewed", "order": 15},
    {"key": "training_scheduled", "label": "Training scheduled", "order": 16},
    {"key": "training_completed", "label": "Training completed", "order": 17},
    {"key": "customer_approved", "label": "Customer approved setup", "order": 18},
    {"key": "onboarding_complete", "label": "Onboarding complete", "order": 19},
]


# ============== HELPER FUNCTIONS ==============

def require_platform_admin(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Dependency to ensure user is a platform admin or owner (owner = app developer/operator)"""
    allowed_roles = {UserRole.PLATFORM_ADMIN, "platform_admin", UserRole.OWNER, "owner"}
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Platform Admin privileges required"
        )
    return current_user


async def ensure_checklist_exists(tenant_id: str):
    """Ensure checklist items exist for a tenant, create if missing"""
    existing_count = await db.onboarding_checklist.count_documents({"tenant_id": tenant_id})
    
    if existing_count == 0:
        # Create default checklist items
        items = []
        for item in DEFAULT_CHECKLIST_ITEMS:
            items.append({
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "item_key": item["key"],
                "label": item["label"],
                "completed": False,
                "note": None,
                "updated_by": None,
                "updated_by_email": None,
                "updated_at": None,
                "order": item["order"]
            })
        
        if items:
            await db.onboarding_checklist.insert_many(items)
            logger.info(f"Created {len(items)} checklist items for tenant {tenant_id}")
    
    return True


# ============== ROUTES ==============

@router.get("/tenants", response_model=List[TenantListItem])
async def list_tenants(
    search: Optional[str] = None,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """List all tenants - Platform Admin only"""
    
    query = {}
    if search:
        query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"owner_email": {"$regex": search, "$options": "i"}},
            ]
        }
    
    tenants = await db.tenants.find(query, {"_id": 0}).to_list(1000)
    
    # Get user counts for each tenant
    result = []
    for tenant in tenants:
        user_count = await db.users.count_documents({"tenant_id": tenant["id"]})
        result.append(TenantListItem(
            id=tenant["id"],
            name=tenant["name"],
            owner_email=tenant.get("owner_email", ""),
            plan=tenant.get("plan", "starter"),
            created_at=tenant.get("created_at", ""),
            user_count=user_count,
            is_active=tenant.get("is_active", True),
            suspension_reason=tenant.get("suspension_reason"),
            suspended_at=tenant.get("suspended_at"),
        ))

    return result


@router.get("/tenants/{tenant_id}")
async def get_tenant_detail(
    tenant_id: str,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Get tenant details with user list - Platform Admin only"""
    
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get all users for this tenant - with error handling for invalid user data
    users_raw = await db.users.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "hashed_password": 0}
    ).to_list(1000)
    
    # Filter out users with invalid data and validate each one
    valid_users = []
    invalid_users = []
    
    for user_data in users_raw:
        try:
            # Try to create a User model - this will validate the data
            valid_user = User(**user_data)
            valid_users.append(valid_user)
        except Exception as e:
            # Log invalid user but continue processing
            logger.warning(
                f"Skipping invalid user in tenant {tenant_id}: "
                f"email={user_data.get('email')}, error={str(e)}"
            )
            invalid_users.append({
                "email": user_data.get("email", "unknown"),
                "error": str(e)
            })
    
    # Enrich tenant doc with computed `is_founder` (any founder user in the tenant)
    await _enrich_with_founder_flag(tenant)

    return {
        "tenant": TenantDetail(**tenant),
        "users": valid_users,
        "invalid_users_count": len(invalid_users)
    }


# ============== TENANT SUSPENSION ROUTES ==============

@router.post("/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    payload: SuspendTenantRequest,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """
    Suspend a tenant.

    Sets is_active=False and stores reason/audit metadata. Active sessions are
    blocked on their next API call (via get_current_active_user). Login is
    blocked with the same reason. Platform-admin tenants cannot be suspended.
    """
    if not payload.reason or not payload.reason.strip():
        raise HTTPException(status_code=400, detail="A reason is required")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Don't allow suspending a tenant that owns a platform_admin user (self-lockout protection)
    pa_count = await db.users.count_documents({
        "tenant_id": tenant_id,
        "role": "platform_admin",
    })
    if pa_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot suspend a tenant that contains a platform_admin user",
        )

    if tenant.get("is_active") is False:
        return {
            "message": "Tenant already suspended",
            "tenant_id": tenant_id,
            "already_suspended": True,
            "suspension_reason": tenant.get("suspension_reason"),
            "suspended_at": tenant.get("suspended_at"),
        }

    now_iso = datetime.now(timezone.utc).isoformat()
    update_doc = {
        "is_active": False,
        "suspension_reason": payload.reason.strip(),
        "suspended_at": now_iso,
        "suspended_by": current_user.id,
        "suspended_by_email": current_user.email,
        "reactivated_at": None,
        "reactivated_by": None,
        "reactivated_by_email": None,
        "updated_at": now_iso,
    }
    await db.tenants.update_one({"id": tenant_id}, {"$set": update_doc})

    # Audit log
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="tenant.suspend",
        action_category="tenant",
        target_type="tenant",
        target_id=tenant_id,
        target_label=tenant.get("name"),
        tenant_id=tenant_id,
        tenant_name=tenant.get("name"),
        summary=f"Suspended tenant {tenant.get('name')} (reason: {payload.reason.strip()})",
        metadata={"reason": payload.reason.strip()},
    )

    logger.warning(
        f"Tenant {tenant_id} ({tenant.get('name')}) suspended by "
        f"{current_user.email}: {payload.reason.strip()}"
    )

    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    await _enrich_with_founder_flag(updated)
    return {
        "message": "Tenant suspended",
        "tenant": TenantDetail(**updated),
    }


@router.post("/tenants/{tenant_id}/reactivate")
async def reactivate_tenant(
    tenant_id: str,
    payload: ReactivateTenantRequest,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """
    Reactivate a previously suspended tenant.

    Sets is_active=True and clears suspension fields, while preserving
    a reactivated_at / reactivated_by_email pointer for the audit trail.
    """
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.get("is_active") is True:
        return {
            "message": "Tenant is already active",
            "tenant_id": tenant_id,
            "already_active": True,
        }

    now_iso = datetime.now(timezone.utc).isoformat()
    update_doc = {
        "is_active": True,
        "suspension_reason": None,
        "suspended_at": None,
        "suspended_by": None,
        "suspended_by_email": None,
        "reactivated_at": now_iso,
        "reactivated_by": current_user.id,
        "reactivated_by_email": current_user.email,
        "updated_at": now_iso,
    }
    await db.tenants.update_one({"id": tenant_id}, {"$set": update_doc})

    # Audit log
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="tenant.reactivate",
        action_category="tenant",
        target_type="tenant",
        target_id=tenant_id,
        target_label=tenant.get("name"),
        tenant_id=tenant_id,
        tenant_name=tenant.get("name"),
        summary=f"Reactivated tenant {tenant.get('name')}",
        metadata={
            "previous_reason": tenant.get("suspension_reason"),
            "note": (payload.note or "").strip() or None,
            "notify_owner": payload.notify_owner,
        },
    )

    logger.info(
        f"Tenant {tenant_id} ({tenant.get('name')}) reactivated by {current_user.email}"
    )

    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    await _enrich_with_founder_flag(updated)

    # Optional: send "You're back" email to the owner.
    email_status: Optional[Dict[str, Any]] = None
    if payload.notify_owner:
        owner_email = (updated or {}).get("owner_email") or tenant.get("owner_email")
        if owner_email:
            try:
                from services.email_service import email_service
                email_status = await email_service.send_tenant_reactivated_email(
                    owner_email=owner_email,
                    tenant_name=(updated or {}).get("name") or tenant.get("name") or "your account",
                    tenant_id=tenant_id,
                    note=(payload.note or "").strip() or None,
                )
                logger.info(
                    f"Reactivation email sent to {owner_email} (status={email_status})"
                )
            except Exception as e:
                logger.error(f"Failed to send reactivation email: {e}")
                email_status = {"success": False, "error": str(e)}
        else:
            email_status = {"success": False, "error": "No owner_email on tenant"}

    return {
        "message": "Tenant reactivated",
        "tenant": TenantDetail(**updated),
        "email_status": email_status,
    }


@router.post("/tenants/{tenant_id}/mark-paid")
async def mark_tenant_paid(
    tenant_id: str,
    payload: MarkPaidRequest,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """
    Manual override: mark a tenant as having paid.

    Resets dunning counters and, if the tenant was auto-suspended for non-payment,
    reactivates the account. Used for NET-60 invoices, wire transfers, manually
    cleared chargebacks, or any case where Stripe can't tell us about the payment.
    """
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    from services.dunning import record_payment_success
    result = await record_payment_success(
        db,
        tenant_id=tenant_id,
        triggered_by="manual:platform_admin",
    )

    # Audit the manual override (record_payment_success only records "system" entries)
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="payment.manual_mark_paid",
        action_category="billing",
        target_type="tenant",
        target_id=tenant_id,
        target_label=tenant.get("name"),
        tenant_id=tenant_id,
        tenant_name=tenant.get("name"),
        summary=f"Manually marked {tenant.get('name')} as paid",
        metadata={
            "note": (payload.note or "").strip() or None,
            "auto_reactivated": result.get("auto_reactivated"),
        },
    )

    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    await _enrich_with_founder_flag(updated)
    return {
        "message": "Tenant marked as paid",
        "tenant": TenantDetail(**updated),
        "auto_reactivated": result.get("auto_reactivated", False),
    }


@router.put("/tenants/{tenant_id}/dunning-threshold")
async def set_dunning_threshold(
    tenant_id: str,
    payload: DunningThresholdRequest,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """
    Set or clear a per-tenant override for the dunning failure threshold.
    Pass `threshold=null` to clear the override and use the global default
    (env: DUNNING_AUTO_SUSPEND_AFTER, default 3).
    """
    if payload.threshold is not None and payload.threshold < 1:
        raise HTTPException(status_code=400, detail="threshold must be >= 1 (or null to clear)")

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    now_iso = datetime.now(timezone.utc).isoformat()
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {
            "dunning_failure_threshold": payload.threshold,
            "updated_at": now_iso,
        }},
    )

    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="dunning.threshold_set",
        action_category="billing",
        target_type="tenant",
        target_id=tenant_id,
        target_label=tenant.get("name"),
        tenant_id=tenant_id,
        tenant_name=tenant.get("name"),
        summary=(
            f"Set dunning threshold to {payload.threshold} for {tenant.get('name')}"
            if payload.threshold is not None
            else f"Cleared dunning threshold override for {tenant.get('name')}"
        ),
        metadata={
            "previous": tenant.get("dunning_failure_threshold"),
            "new": payload.threshold,
        },
    )

    updated = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    await _enrich_with_founder_flag(updated)
    return {
        "message": "Dunning threshold updated",
        "tenant": TenantDetail(**updated),
    }


@router.post("/impersonate")
async def start_impersonation(
    request: ImpersonateRequest,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """
    Start impersonating a tenant user
    
    Creates a new JWT token with impersonation metadata.
    Platform Admin can act as the target user to help troubleshoot.
    """
    
    # Find target user
    target_user = await db.users.find_one({"id": request.target_user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")
    
    # Get tenant info
    tenant = await db.tenants.find_one({"id": target_user["tenant_id"]}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Create impersonation log
    log_id = str(uuid.uuid4())
    log_doc = {
        "id": log_id,
        "platform_admin_user_id": current_user.id,
        "platform_admin_email": current_user.email,
        "target_user_id": target_user["id"],
        "target_user_email": target_user["email"],
        "tenant_id": target_user["tenant_id"],
        "tenant_name": tenant["name"],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ended_at": None,
        "duration_seconds": None,
    }
    await db.impersonation_logs.insert_one(log_doc)

    # Audit log entry
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="impersonation.start",
        action_category="impersonation",
        target_type="user",
        target_id=target_user["id"],
        target_label=target_user.get("email"),
        tenant_id=target_user["tenant_id"],
        tenant_name=tenant.get("name"),
        summary=f"Started impersonating {target_user.get('email')} in tenant {tenant.get('name')}",
        metadata={
            "impersonation_log_id": log_id,
            "target_role": target_user.get("role"),
        },
    )

    logger.info(
        f"Platform Admin {current_user.email} started impersonating "
        f"{target_user['email']} (Tenant: {tenant['name']})"
    )
    
    # Create new JWT token for the target user with impersonation metadata
    token_data = {
        "sub": target_user["id"],
        "impersonating": True,
        "impersonation_log_id": log_id,
        "platform_admin_id": current_user.id,
        "platform_admin_email": current_user.email,
    }
    access_token = create_access_token(data=token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "impersonation_log_id": log_id,
        "target_user": {
            "id": target_user["id"],
            "email": target_user["email"],
            "full_name": target_user["full_name"],
            "role": target_user["role"],
            "tenant_id": target_user["tenant_id"],
        },
        "tenant": {
            "id": tenant["id"],
            "name": tenant["name"],
        },
        "platform_admin": {
            "id": current_user.id,
            "email": current_user.email,
        }
    }


@router.post("/exit-impersonation")
async def exit_impersonation(
    http_request: Request,
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Exit impersonation mode and return to platform admin account
    
    This endpoint is called by an impersonating user to end the session.
    The frontend should handle the token replacement.
    """

    # Try to capture audit context from token (impersonation metadata is in JWT)
    # Best-effort logging - no failure should block the exit.
    try:
        await log_admin_action(
            db,
            request=http_request,
            actor=current_user,
            action="impersonation.exit",
            action_category="impersonation",
            target_type="user",
            target_id=current_user.id,
            target_label=current_user.email,
            tenant_id=current_user.tenant_id,
            summary=f"Exited impersonation as {current_user.email}",
        )
    except Exception:
        pass

    return {
        "message": "Impersonation session ended. Please refresh or re-login as platform admin.",
        "action": "logout_required"
    }


@router.get("/impersonation-logs", response_model=List[ImpersonationLog])
async def get_impersonation_logs(
    limit: int = 100,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Get recent impersonation logs - Platform Admin only"""
    
    logs = await db.impersonation_logs.find(
        {},
        {"_id": 0}
    ).sort("started_at", -1).limit(limit).to_list(limit)
    
    return [ImpersonationLog(**log) for log in logs]


@router.post("/impersonation-logs/{log_id}/end")
async def end_impersonation_log(
    log_id: str,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Manually end an impersonation log entry"""
    
    log = await db.impersonation_logs.find_one({"id": log_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    if log.get("ended_at"):
        return {"message": "Log already ended"}
    
    # Calculate duration
    started = datetime.fromisoformat(log["started_at"].replace("Z", "+00:00"))
    ended = datetime.now(timezone.utc)
    duration = int((ended - started).total_seconds())
    
    await db.impersonation_logs.update_one(
        {"id": log_id},
        {"$set": {
            "ended_at": ended.isoformat(),
            "duration_seconds": duration
        }}
    )
    
    logger.info(f"Impersonation log {log_id} ended (duration: {duration}s)")

    # Audit log entry
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="impersonation.manual_end",
        action_category="impersonation",
        target_type="impersonation_log",
        target_id=log_id,
        target_label=log.get("target_user_email"),
        tenant_id=log.get("tenant_id"),
        tenant_name=log.get("tenant_name"),
        summary=f"Manually ended impersonation log for {log.get('target_user_email')}",
        metadata={"duration_seconds": duration},
    )

    return {"message": "Impersonation log ended", "duration_seconds": duration}


# ============== ONBOARDING CHECKLIST ROUTES ==============

@router.get("/tenants/{tenant_id}/checklist", response_model=List[OnboardingChecklistItem])
async def get_tenant_checklist(
    tenant_id: str,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Get onboarding checklist for a tenant - Platform Admin only"""
    
    # Verify tenant exists
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Ensure checklist exists
    await ensure_checklist_exists(tenant_id)
    
    # Get checklist items
    items = await db.onboarding_checklist.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).sort("order", 1).to_list(100)
    
    return [OnboardingChecklistItem(**item) for item in items]


@router.patch("/tenants/{tenant_id}/checklist/{item_id}")
async def update_checklist_item(
    tenant_id: str,
    item_id: str,
    request: UpdateChecklistItemRequest,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Update a checklist item - Platform Admin only"""
    
    # Verify item exists
    item = await db.onboarding_checklist.find_one(
        {"id": item_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    # Update item
    update_data = {
        "completed": request.completed,
        "note": request.note,
        "updated_by": current_user.id,
        "updated_by_email": current_user.email,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.onboarding_checklist.update_one(
        {"id": item_id},
        {"$set": update_data}
    )
    
    logger.info(
        f"Platform Admin {current_user.email} updated checklist item "
        f"{item['label']} for tenant {tenant_id} (completed: {request.completed})"
    )

    # Audit log entry
    tenant_doc = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "name": 1})
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="checklist.update",
        action_category="onboarding",
        target_type="onboarding_checklist_item",
        target_id=item_id,
        target_label=item.get("label"),
        tenant_id=tenant_id,
        tenant_name=(tenant_doc or {}).get("name"),
        summary=(
            f"Marked '{item.get('label')}' as "
            f"{'completed' if request.completed else 'incomplete'}"
        ),
        metadata={
            "completed": request.completed,
            "previous_completed": item.get("completed", False),
            "note": request.note,
        },
    )
    
    # Get updated item
    updated_item = await db.onboarding_checklist.find_one(
        {"id": item_id},
        {"_id": 0}
    )
    
    return OnboardingChecklistItem(**updated_item)


@router.get("/tenants/{tenant_id}/checklist/progress")
async def get_checklist_progress(
    tenant_id: str,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Get checklist completion progress - Platform Admin only"""
    
    # Ensure checklist exists
    await ensure_checklist_exists(tenant_id)
    
    # Get all items
    items = await db.onboarding_checklist.find(
        {"tenant_id": tenant_id},
        {"_id": 0}
    ).to_list(100)
    
    total = len(items)
    completed = sum(1 for item in items if item.get("completed", False))
    percentage = int((completed / total) * 100) if total > 0 else 0
    
    return {
        "total": total,
        "completed": completed,
        "remaining": total - completed,
        "percentage": percentage
    }



# ============== ADMIN AUDIT LOG ROUTES ==============

@router.get("/audit-log")
async def list_audit_log(
    action: Optional[str] = None,
    action_category: Optional[str] = None,
    actor_email: Optional[str] = None,
    target_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 200,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """
    List Admin Audit Log entries (Platform Admin only).

    Filters: action, action_category, actor_email, target_id, tenant_id,
    since (ISO datetime), until (ISO datetime).
    Default 200 entries, max 1000.
    """
    limit = max(1, min(limit, 1000))

    query: dict = {}
    if action:
        query["action"] = action
    if action_category:
        query["action_category"] = action_category
    if actor_email:
        query["actor_email"] = {"$regex": actor_email, "$options": "i"}
    if target_id:
        query["target_id"] = target_id
    if tenant_id:
        query["tenant_id"] = tenant_id
    if since or until:
        created_filter: dict = {}
        if since:
            created_filter["$gte"] = since
        if until:
            created_filter["$lte"] = until
        query["created_at"] = created_filter

    entries = await db.admin_audit_log.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)

    return {
        "total_returned": len(entries),
        "limit": limit,
        "entries": entries,
    }


@router.get("/audit-log/actions")
async def list_audit_actions(
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Return distinct action types and categories present in the audit log."""
    actions = await db.admin_audit_log.distinct("action")
    categories = await db.admin_audit_log.distinct("action_category")
    return {
        "actions": sorted([a for a in actions if a]),
        "categories": sorted([c for c in categories if c]),
    }


@router.get("/audit-log/{entry_id}")
async def get_audit_entry(
    entry_id: str,
    current_user: UserInDB = Depends(require_platform_admin)
):
    """Get a single audit-log entry by id."""
    entry = await db.admin_audit_log.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")
    return entry



@router.post("/users/{user_id}/promote-to-tenant")
async def promote_user_to_tenant(
    user_id: str,
    payload: dict,
    request: Request,
    current_user: UserInDB = Depends(require_platform_admin),
):
    """Promote an existing user out of their current tenant into a brand-new
    tenant where they become the owner.

    Used when someone signed up via a team-invite link by mistake but should
    actually have been their own tenant.

    Important: this ONLY moves the user record. No orders, customers,
    invoices, or other tenant-scoped data is touched. The new tenant starts
    empty. The original tenant keeps any data the user created while inside.

    Disabled by default. Set env var ENABLE_PROMOTE_TO_TENANT=1 to enable.
    """
    # Feature flag — keep this destructive tool OFF until explicitly turned
    # on. Even with platform_admin auth we don't want this clickable in prod
    # by accident.
    import os as _os
    if (_os.environ.get("ENABLE_PROMOTE_TO_TENANT") or "").strip() not in ("1", "true", "yes", "on"):
        raise HTTPException(
            status_code=403,
            detail="Promote-to-tenant is disabled. Set ENABLE_PROMOTE_TO_TENANT=1 to enable.",
        )

    new_tenant_name = (payload or {}).get("new_tenant_name", "").strip()
    if not new_tenant_name:
        raise HTTPException(status_code=400, detail="new_tenant_name is required")
    if len(new_tenant_name) > 120:
        raise HTTPException(status_code=400, detail="Tenant name too long (max 120 chars)")

    # Look up the user being promoted
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Don't allow promoting platform admins (they shouldn't be inside a tenant in the
    # ordinary sense — and we already protect against losing the only platform admin
    # via the suspend self-lockout guard).
    if user.get("role") == "platform_admin":
        raise HTTPException(status_code=400, detail="Cannot promote a platform_admin user")

    # Don't double-promote: if the user is already the owner of their current
    # tenant, there's nothing to do.
    current_tenant = await db.tenants.find_one(
        {"id": user.get("tenant_id")},
        {"_id": 0, "id": 1, "name": 1, "owner_email": 1},
    )
    if current_tenant and current_tenant.get("owner_email", "").lower() == (user.get("email") or "").lower():
        raise HTTPException(
            status_code=409,
            detail="User is already the owner of their current tenant — nothing to promote.",
        )

    # Create the new tenant
    new_tenant_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    new_tenant_doc = {
        "id": new_tenant_id,
        "name": new_tenant_name,
        "owner_email": user.get("email"),
        "plan": "free_trial",
        "is_active": True,
        "created_at": now_iso,
        "updated_at": now_iso,
        # Make it discoverable that this tenant was split off so we have a
        # paper trail beyond the audit row.
        "promoted_from_tenant_id": user.get("tenant_id"),
        "promoted_from_user_id": user["id"],
        "promoted_at": now_iso,
        "promoted_by_platform_admin": current_user.email,
    }
    await db.tenants.insert_one(new_tenant_doc)

    # Move the user. Role flips to "owner" of the new tenant.
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "tenant_id": new_tenant_id,
            "role": "owner",
            "promoted_from_tenant_id": user.get("tenant_id"),
            "promoted_at": now_iso,
            "updated_at": now_iso,
        }},
    )

    # Audit log on both tenants for full traceability.
    try:
        await log_admin_action(
            db=db,
            request=request,
            actor=current_user,
            action="user.promote_to_tenant",
            action_category="platform",
            target_type="user",
            target_id=user_id,
            target_label=user.get("email"),
            tenant_id=new_tenant_id,
            tenant_name=new_tenant_name,
            summary=f"Promoted {user.get('email')} out of '{(current_tenant or {}).get('name')}' into new tenant '{new_tenant_name}'",
            metadata={
                "old_tenant_id": user.get("tenant_id"),
                "old_tenant_name": (current_tenant or {}).get("name"),
                "new_tenant_id": new_tenant_id,
                "new_tenant_name": new_tenant_name,
                "user_email": user.get("email"),
            },
            status="success",
        )
    except Exception as audit_err:  # noqa: BLE001
        logger.error(f"Audit log failed for user.promote_to_tenant: {audit_err}")

    # Strip the _id key (Mongo populated it on insert) before returning.
    new_tenant_doc.pop("_id", None)
    return {
        "ok": True,
        "tenant": new_tenant_doc,
        "user_email": user.get("email"),
        "moved_from_tenant_id": user.get("tenant_id"),
    }


# ============== BROADCAST EMAIL TO TENANT OWNERS ==============
#
# Lets a Platform Admin send a one-off email to one or more tenant owners.
# Audience can be filtered (all / active / suspended / founders) or limited to a
# specific list of tenant_ids. Always supports a "test mode" so the admin can
# preview the rendered email by sending only to a single address first.

class BroadcastEmailRequest(BaseModel):
    # Subject capped at 200 chars (well above any reasonable email subject).
    subject: str = Field(..., max_length=200)
    # html_body capped at 50 KB. Beyond that you're either embedding images
    # (don't — use linked CDN URLs) or about to trigger SendGrid abuse flags.
    html_body: str = Field(..., max_length=50_000)
    # Audience selector. Mutually exclusive with `tenant_ids`.
    target: Optional[str] = "all_owners"  # all_owners | active_only | suspended_only | founders_only
    # Optional explicit override (takes precedence over `target` when set).
    tenant_ids: Optional[List[str]] = Field(default=None, max_length=1000)
    # When set, the email is only sent to this single address. Nothing goes out
    # to tenants. Use this to preview the rendered email first.
    test_to: Optional[str] = None


# ---------- Rate limiting ----------
# We don't have slowapi installed. Use an audit-log-driven cap instead: count
# successful broadcast sends by this actor in the last 60 minutes. This is
# self-healing (no extra collection) and survives restarts.
BROADCAST_HOURLY_CAP_TENANTS = 10        # full-audience sends per hour
BROADCAST_HOURLY_CAP_TESTS = 30          # test_to sends per hour


async def _enforce_broadcast_rate_limit(actor_id: str, is_test: bool):
    """Block runaway / compromised admin accounts from spam-blasting customers.

    Counts past-hour `broadcast_email.send` audit rows by this actor split by
    test vs broadcast. Raises 429 if over the cap.
    """
    since_iso = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    query: Dict[str, Any] = {
        "actor_user_id": actor_id,
        "action": "broadcast_email.send",
        "created_at": {"$gte": since_iso},
    }
    # We track test vs broadcast in metadata — count both separately.
    rows = await db.admin_audit_log.find(query, {"_id": 0, "metadata": 1}).to_list(500)
    test_count = sum(1 for r in rows if (r.get("metadata") or {}).get("test_to"))
    broadcast_count = sum(1 for r in rows if not (r.get("metadata") or {}).get("test_to"))

    if is_test and test_count >= BROADCAST_HOURLY_CAP_TESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Broadcast test rate limit reached ({BROADCAST_HOURLY_CAP_TESTS}/hour). Try again later.",
        )
    if (not is_test) and broadcast_count >= BROADCAST_HOURLY_CAP_TENANTS:
        raise HTTPException(
            status_code=429,
            detail=f"Broadcast send rate limit reached ({BROADCAST_HOURLY_CAP_TENANTS}/hour). Try again later.",
        )


# ---------- Personalization helpers ----------
# Supported placeholders in subject + html_body. Missing values render empty
# rather than blowing up.
_BROADCAST_PLACEHOLDERS = (
    "tenant_name",
    "owner_email",
    "owner_first_name",
)


def _derive_owner_first_name(tenant: Dict[str, Any]) -> str:
    """Best-effort first name from explicit owner_name or fallback to email local-part."""
    name = (tenant.get("owner_name") or "").strip()
    if name:
        return name.split()[0]
    email = (tenant.get("owner_email") or "").strip()
    if email and "@" in email:
        local = email.split("@", 1)[0]
        # turn "first.last" / "first_last" / "first-last" into "First"
        local = local.replace(".", " ").replace("_", " ").replace("-", " ")
        first = local.split()[0] if local.split() else local
        return first.capitalize()
    return "there"


def _render_broadcast_template(text: str, ctx: Dict[str, str]) -> str:
    """Tiny mustache-ish renderer for `{{placeholder}}` tokens.

    HTML-escapes every substituted value so a tenant whose name is
    `<script>alert(1)</script>` cannot inject scripts into the rendered email.
    Unknown tokens are left as-is so the admin notices typos at preview time.
    """
    out = text
    for key in _BROADCAST_PLACEHOLDERS:
        token = "{{" + key + "}}"
        raw_value = str(ctx.get(key, "") or "")
        safe_value = _html_lib.escape(raw_value, quote=True)
        out = out.replace(token, safe_value)
    return out


@router.post("/broadcast-email")
async def broadcast_email(
    payload: BroadcastEmailRequest,
    request: Request,
    current_user: UserInDB = Depends(require_platform_admin),
):
    """Send a one-off email to one or many tenant owners.

    Modes:
    - test_to set → sends to that one address only (no audience resolution).
    - tenant_ids set → resolves owner_email for each id, sends to those.
    - target set → filters tenants by `target` and sends to each owner_email.

    Always writes a single audit-log row with summary counts.
    """
    from services.email_service import email_service

    if not payload.subject.strip():
        raise HTTPException(status_code=400, detail="Subject is required")
    if not payload.html_body.strip():
        raise HTTPException(status_code=400, detail="Email body is required")

    # Fail fast if SendGrid is not configured — otherwise a broadcast would
    # silently report success with 0 emails actually sent.
    if not email_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Email service is not configured. Set SENDGRID_API_KEY and try again.",
        )

    # Rate limit (per actor, last hour). Test sends and full broadcasts are
    # capped separately — a runaway broadcast loop is the bigger risk.
    await _enforce_broadcast_rate_limit(
        actor_id=current_user.id,
        is_test=bool(payload.test_to),
    )

    # 1) Resolve recipient list (now also captures the tenant doc so we can
    # personalize per-recipient at render time).
    recipients: List[Dict[str, Any]] = []  # [{tenant_id, email, tenant}]

    if payload.test_to:
        # Test mode → preview using the admin's own tenant (or stub values if
        # the admin isn't tied to a tenant). This way the rendered placeholders
        # match what real recipients will see.
        admin_tenant = None
        if current_user.tenant_id:
            admin_tenant = await db.tenants.find_one(
                {"id": current_user.tenant_id},
                {"_id": 0, "id": 1, "name": 1, "owner_email": 1, "owner_name": 1},
            )
        recipients.append({
            "tenant_id": admin_tenant.get("id") if admin_tenant else None,
            "email": payload.test_to.strip(),
            "tenant": admin_tenant or {
                "name": "Example Tenant LLC",
                "owner_email": payload.test_to.strip(),
            },
        })
    elif payload.tenant_ids:
        tenants = await db.tenants.find(
            {"id": {"$in": payload.tenant_ids}},
            {"_id": 0, "id": 1, "name": 1, "owner_email": 1, "owner_name": 1},
        ).to_list(len(payload.tenant_ids))
        for t in tenants:
            if t.get("owner_email"):
                recipients.append({"tenant_id": t["id"], "email": t["owner_email"], "tenant": t})
    else:
        target = (payload.target or "all_owners").lower()
        query: Dict[str, Any] = {}
        if target == "active_only":
            query["is_active"] = {"$ne": False}
        elif target == "suspended_only":
            query["is_active"] = False
        elif target == "founders_only":
            # `is_founder` is a per-user flag, not persisted on the tenant doc
            # (see _enrich_with_founder_flag). Resolve via users collection so
            # this filter actually returns rows.
            founder_tenant_ids = await db.users.distinct("tenant_id", {"is_founder": True})
            query["id"] = {"$in": [t for t in founder_tenant_ids if t]}
        # all_owners → no filter

        tenants = await db.tenants.find(
            query,
            {"_id": 0, "id": 1, "name": 1, "owner_email": 1, "owner_name": 1, "is_founder": 1, "is_active": 1},
        ).to_list(10000)
        for t in tenants:
            if t.get("owner_email"):
                recipients.append({"tenant_id": t["id"], "email": t["owner_email"], "tenant": t})

    # Dedupe by email (a single human can own multiple tenants — we only email them once)
    seen_emails = set()
    unique_recipients: List[Dict[str, Any]] = []
    for r in recipients:
        em = (r["email"] or "").strip().lower()
        if not em or em in seen_emails:
            continue
        seen_emails.add(em)
        unique_recipients.append(r)

    if not unique_recipients:
        raise HTTPException(status_code=400, detail="No recipients matched the given audience")

    # 2) Send (sequential, per-recipient personalization).
    sent: List[str] = []
    failed: List[Dict[str, str]] = []
    for r in unique_recipients:
        tenant = r.get("tenant") or {}
        ctx = {
            "tenant_name": tenant.get("name") or "",
            "owner_email": tenant.get("owner_email") or r["email"],
            "owner_first_name": _derive_owner_first_name(tenant),
        }
        rendered_subject = _render_broadcast_template(payload.subject, ctx)
        rendered_body = _render_broadcast_template(payload.html_body, ctx)
        try:
            res = await email_service.send_email(
                to_email=r["email"],
                subject=rendered_subject,
                html_content=rendered_body,
                tenant_id=r.get("tenant_id"),
            )
            if res and res.get("success"):
                sent.append(r["email"])
            else:
                failed.append({"email": r["email"], "error": (res or {}).get("error", "unknown")})
        except Exception as e:  # noqa: BLE001
            logger.error(f"Broadcast email failed for {r['email']}: {e}")
            failed.append({"email": r["email"], "error": str(e)})

    # 3) Audit log (single row summarizing the blast)
    try:
        await log_admin_action(
            db=db,
            request=request,
            actor=current_user,
            action="broadcast_email.send",
            action_category="platform",
            target_type="tenants",
            summary=f"Broadcast email sent: {payload.subject}",
            metadata={
                "subject": payload.subject,
                "target": payload.target,
                "tenant_ids": payload.tenant_ids,
                "test_to": payload.test_to,
                "sent_count": len(sent),
                "failed_count": len(failed),
            },
            status="success" if not failed else "partial",
        )
    except Exception as audit_err:  # noqa: BLE001
        logger.error(f"Failed to write broadcast_email audit row: {audit_err}")

    return {
        "mode": "test" if payload.test_to else "broadcast",
        "matched_recipients": len(unique_recipients),
        "sent_count": len(sent),
        "failed_count": len(failed),
        "failed": failed[:25],  # cap response size
    }


@router.get("/broadcast-email/audience-counts")
async def broadcast_email_audience_counts(
    current_user: UserInDB = Depends(require_platform_admin),
):
    """Return live recipient counts for each audience filter so the UI can
    show 'Send to 47 active tenants' before the admin commits."""
    base_q = {"owner_email": {"$exists": True, "$ne": ""}}
    all_owners = await db.tenants.count_documents(base_q)
    active = await db.tenants.count_documents({**base_q, "is_active": {"$ne": False}})
    suspended = await db.tenants.count_documents({**base_q, "is_active": False})
    # founder_tenant_ids resolved via users collection (is_founder is per-user).
    founder_tenant_ids = await db.users.distinct("tenant_id", {"is_founder": True})
    founder_tenant_ids = [t for t in founder_tenant_ids if t]
    founders = await db.tenants.count_documents(
        {**base_q, "id": {"$in": founder_tenant_ids}}
    ) if founder_tenant_ids else 0
    return {
        "all_owners": all_owners,
        "active_only": active,
        "suspended_only": suspended,
        "founders_only": founders,
    }
