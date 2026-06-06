"""
Authentication and User Management Routes

This module contains all routes related to:
- User registration and login
- User profile management
- Admin user management
- Password reset
- Role management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import jwt
import re
import os
import hashlib
import secrets
from pydantic import BaseModel, Field

from models import (
    User, UserCreate, UserLogin, UserInDB, UserRoleUpdate,
    Token, TokenData, PasswordReset,
    Tenant, TenantCreate, TenantUpdate,
    UserRole, Permission, ROLE_PERMISSIONS,
    get_user_permissions, user_has_permission
)
import uuid

# These will be imported from the main server module
# In the future, they should be moved to core/auth.py
from server import (
    db, logger, security,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    pwd_context, get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_active_user,
    has_permission, generate_tenant_slug
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/users", tags=["Users"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminCreateUserInput(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: Optional[str] = None
    role: UserRole = UserRole.STAFF


# ============== AUTH ROUTES ==============

@router.post("/register", response_model=Token)
async def register(input: UserCreate):
    """Register a new user with 48-hour free trial and sample data"""
    from services.founders_config import (
        FOUNDERS_EDITION_MAX_CUSTOMERS, 
        FREE_TRIAL_CREDITS,
        FREE_TRIAL_HOURS,
        FOUNDERS_EDITION_PLAN
    )
    from services.sample_data import create_sample_data_for_tenant
    from datetime import timezone
    from dateutil.relativedelta import relativedelta
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": input.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check Founders Edition availability (for after trial)
    founders_count = await db.tenants.count_documents({"plan": "founders_edition"})
    founders_spots_remaining = FOUNDERS_EDITION_MAX_CUSTOMERS - founders_count
    
    # Self-registration always creates a new tenant (company) and the user becomes owner
    company_name = input.company_name or f"{input.full_name}'s Sign Shop"
    
    # Create tenant with FREE TRIAL (not Founders Edition yet)
    tenant = Tenant(
        name=company_name,
        slug=generate_tenant_slug(company_name),
        owner_email=input.email.lower(),
    )
    tenant_doc = tenant.model_dump()
    
    # Set up 48-hour free trial
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(hours=FREE_TRIAL_HOURS)
    
    tenant_doc["plan"] = "free_trial"
    tenant_doc["plan_name"] = "48-Hour Free Trial"
    tenant_doc["trial_started_at"] = now.isoformat()
    tenant_doc["trial_ends_at"] = trial_end.isoformat()
    tenant_doc["is_trial"] = True
    tenant_doc["founders_spots_remaining"] = founders_spots_remaining
    
    await db.tenants.insert_one(tenant_doc)
    tenant_id = tenant.id
    logger.info(f"Created new trial tenant: {tenant.name} ({tenant.id}) - 48hr trial until {trial_end.isoformat()}")
    
    # Initialize trial AI credits (50 credits, one-time)
    credits_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "monthly_credits": FREE_TRIAL_CREDITS,  # 50 trial credits
        "purchased_credits": 0,
        "monthly_credits_granted_at": now.isoformat(),
        "monthly_credits_period_start": now.isoformat(),
        "monthly_credits_period_end": trial_end.isoformat(),  # Credits expire with trial
        "low_credits_threshold": 10,
        "is_trial_credits": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.user_credits.insert_one(credits_doc)
    
    # Record trial credit grant transaction
    from models.credits import CreditTransaction, CreditTransactionType
    transaction = CreditTransaction(
        tenant_id=tenant_id,
        transaction_type=CreditTransactionType.MONTHLY_GRANT,
        amount=FREE_TRIAL_CREDITS,
        balance_after=FREE_TRIAL_CREDITS,
        monthly_balance_after=FREE_TRIAL_CREDITS,
        purchased_balance_after=0,
        description=f"Welcome! {FREE_TRIAL_CREDITS} AI credits for your 48-hour free trial."
    )
    await db.credit_transactions.insert_one(transaction.model_dump())
    
    # Self-registering user is always the owner of their tenant
    role = UserRole.OWNER
    
    # Create new user
    hashed_password = get_password_hash(input.password)
    user = UserInDB(
        email=input.email.lower(),
        full_name=input.full_name,
        company_name=input.company_name,
        role=role,
        tenant_id=tenant_id,
        hashed_password=hashed_password
    )
    doc = user.model_dump()
    await db.users.insert_one(doc)
    
    # Create sample data for the trial account
    try:
        await create_sample_data_for_tenant(db, tenant_id, input.full_name)
        logger.info(f"Created sample data for trial tenant: {tenant_id}")
    except Exception as e:
        logger.warning(f"Failed to create sample data for tenant {tenant_id}: {e}")
        # Don't fail registration if sample data creation fails
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token)


@router.post("/login", response_model=Token)
async def login(input: UserLogin):
    """Authenticate user and return access token"""
    # Find user by email
    user = await db.users.find_one({"email": input.email.lower()}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(input.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Re-hash password on successful login to ensure hash is in current bcrypt format
    current_hash = user["hashed_password"]
    fresh_hash = get_password_hash(input.password)
    if current_hash != fresh_hash:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"hashed_password": fresh_hash}}
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is disabled")

    # Block login for suspended tenants (skip platform admins).
    user_role = user.get("role")
    if user_role != "platform_admin" and user.get("tenant_id"):
        tenant = await db.tenants.find_one(
            {"id": user["tenant_id"]},
            {"_id": 0, "is_active": 1, "suspension_reason": 1, "suspended_at": 1},
        )
        if tenant and tenant.get("is_active") is False:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "tenant_suspended",
                    "message": "This account is suspended. Please contact support.",
                    "reason": tenant.get("suspension_reason"),
                    "suspended_at": tenant.get("suspended_at"),
                },
            )

    # Create access token - extended expiry if "remember me" is checked
    if input.remember_me:
        expires_delta = timedelta(days=30)
        expires_in = 30 * 24 * 60 * 60
    else:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    access_token = create_access_token(data={"sub": user["id"]}, expires_delta=expires_delta)
    
    return Token(access_token=access_token, expires_in=expires_in)


class ForgotPasswordRequest(BaseModel):
    """Request a password-reset link by email (no auth)."""
    email: str
    origin: Optional[str] = None  # frontend origin for building the reset link


class ResetPasswordRequest(BaseModel):
    """Complete a password reset using a single-use token."""
    token: str
    new_password: str = Field(min_length=6)


# Reset tokens live in their own collection and are stored as SHA-256 hashes,
# never in plaintext. Tokens are single-use and expire after this window.
_RESET_TOKEN_TTL_MINUTES = 60


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _build_reset_link(origin: Optional[str], raw_token: str) -> str:
    base = (
        (origin or "").rstrip("/")
        or os.environ.get("APP_URL", "").rstrip("/")
        or os.environ.get("META_PUBLIC_URL", "").rstrip("/")
    )
    return f"{base}/reset-password?token={raw_token}"


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Begin a secure password reset. Generates a single-use, time-limited token,
    stores only its hash, and emails the reset link to the account owner.

    Always returns a generic success response so the endpoint cannot be used to
    enumerate which emails have accounts.
    """
    generic_response = {
        "message": "If an account exists for that email, a password reset link has been sent."
    }

    email_lower = request.email.lower().strip()
    if not email_lower:
        return generic_response

    user = await db.users.find_one({"email": email_lower}, {"_id": 0})
    # Silently no-op for unknown or disabled accounts (no enumeration).
    if not user or not user.get("is_active", True):
        return generic_response

    raw_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=_RESET_TOKEN_TTL_MINUTES)

    # Invalidate any prior outstanding tokens for this user, then store the new one.
    await db.password_reset_tokens.update_many(
        {"user_id": user["id"], "used": False},
        {"$set": {"used": True, "invalidated_at": now.isoformat()}},
    )
    await db.password_reset_tokens.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "email": email_lower,
        "token_hash": _hash_reset_token(raw_token),
        "expires_at": expires_at.isoformat(),
        "used": False,
        "created_at": now.isoformat(),
    })

    reset_link = _build_reset_link(request.origin, raw_token)
    try:
        from services.email_service import email_service
        await email_service.send_password_reset_email(
            to_email=email_lower,
            reset_link=reset_link,
            user_name=user.get("full_name"),
            expires_minutes=_RESET_TOKEN_TTL_MINUTES,
        )
    except Exception as e:  # never leak delivery state to the caller
        logger.warning(f"Password reset email dispatch failed for {email_lower}: {e}")

    return generic_response


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Complete a password reset. Verifies the single-use token (hash match, not
    expired, not used), updates the password with a fresh bcrypt hash, and burns
    the token.
    """
    token_hash = _hash_reset_token(request.token.strip())
    record = await db.password_reset_tokens.find_one({"token_hash": token_hash}, {"_id": 0})

    if not record or record.get("used"):
        raise HTTPException(status_code=400, detail="This reset link is invalid or has already been used.")

    try:
        expired = datetime.fromisoformat(record["expires_at"]) < datetime.now(timezone.utc)
    except (KeyError, ValueError):
        expired = True
    if expired:
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    user = await db.users.find_one({"id": record["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=400, detail="This reset link is invalid.")

    hashed_password = get_password_hash(request.new_password)
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {
            "hashed_password": hashed_password,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    # Burn the token so it cannot be replayed.
    await db.password_reset_tokens.update_one(
        {"id": record["id"]},
        {"$set": {"used": True, "used_at": datetime.now(timezone.utc).isoformat()}},
    )

    return {"message": "Your password has been reset. You can now log in with your new password."}


@router.post("/setup-admin")
async def setup_admin_account(request_body: dict):
    """
    One-time production bootstrap: reset admin password and seed promo codes.

    SECURITY: This endpoint is DISABLED by default and only mounted when the
    environment flag ENABLE_SETUP_ADMIN=true is set. Even when enabled it
    additionally requires the shared setup_key to equal JWT_SECRET_KEY. Keep it
    off in normal deployments and only flip it on for a controlled bootstrap.
    """
    import uuid as uuid_mod

    if os.environ.get("ENABLE_SETUP_ADMIN", "").strip().lower() != "true":
        # Behave as if the route does not exist when disabled.
        raise HTTPException(status_code=404, detail="Not Found")

    setup_key = request_body.get("setup_key", "")
    expected_key = os.environ.get("JWT_SECRET_KEY", "")

    if not expected_key or not setup_key or not secrets.compare_digest(setup_key, expected_key):
        raise HTTPException(status_code=403, detail="Invalid setup key")

    results = []
    
    # 1. Reset admin password and/or promote role if email provided
    email = request_body.get("email", "").lower().strip()
    new_password = request_body.get("new_password", "")
    promote_to_platform_admin = request_body.get("promote_to_platform_admin", False)
    if email:
        user = await db.users.find_one({"email": email}, {"_id": 0})
        if user:
            updates = {}
            if new_password:
                updates["hashed_password"] = get_password_hash(new_password)
                results.append(f"Password reset for {email}")
            if promote_to_platform_admin:
                updates["role"] = "platform_admin"
                results.append(f"Role promoted to platform_admin for {email}")
            if updates:
                await db.users.update_one({"email": email}, {"$set": updates})
            
            # Ensure tenant has owner_email and is_platform_owner
            if user.get("role") in ("owner", "platform_admin") and user.get("tenant_id"):
                await db.tenants.update_one(
                    {"id": user["tenant_id"]},
                    {"$set": {
                        "owner_email": email,
                        "is_platform_owner": True,
                        "is_founder": True,
                        "subscription_status": "active",
                        "trial_ends_at": None,
                    }}
                )
                results.append("Tenant updated: platform_owner=true, founder=true, active")
        else:
            results.append(f"User {email} not found")
    
    # 2. Seed promo codes if provided
    promo_codes = request_body.get("promo_codes", [])
    for pc in promo_codes:
        code = pc.get("code", "").upper().strip()
        if not code:
            continue
        existing = await db.promo_codes.find_one({"code": code})
        if existing:
            # Reset usage if requested
            if pc.get("reset_usage"):
                await db.promo_codes.update_one(
                    {"code": code},
                    {"$set": {
                        "times_used": 0,
                        "max_uses": pc.get("max_uses", existing.get("max_uses")),
                        "is_active": True,
                    }}
                )
                results.append(f"Promo {code}: usage reset")
            else:
                results.append(f"Promo {code}: already exists")
        else:
            promo_doc = {
                "id": str(uuid_mod.uuid4()),
                "tenant_id": pc.get("tenant_id", ""),
                "code": code,
                "description": pc.get("description", ""),
                "discount_type": pc.get("discount_type", "free_trial"),
                "discount_value": pc.get("discount_value", 0),
                "trial_days": pc.get("trial_days", 14),
                "max_uses": pc.get("max_uses"),
                "times_used": 0,
                "expires_at": pc.get("expires_at"),
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.promo_codes.insert_one(promo_doc)
            results.append(f"Promo {code}: created")
    
    return {"results": results}



# ============== USER PROFILE ROUTES ==============

@users_router.get("/me")
async def get_current_user_profile(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user's profile - includes impersonation metadata if present"""
    user_data = {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "is_active": current_user.is_active,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at,
        "is_founder": getattr(current_user, 'is_founder', False)
    }
    
    # Add impersonation metadata if present (from JWT token)
    impersonation = getattr(current_user, 'impersonation', None)
    if impersonation:
        user_data['impersonation'] = impersonation

    # Always include the tenant name — used by the impersonation banner so
    # the platform admin sees exactly which tenant they're inside.
    if current_user.tenant_id:
        tenant_doc = await db.tenants.find_one(
            {"id": current_user.tenant_id}, {"_id": 0, "name": 1}
        )
        if tenant_doc and tenant_doc.get("name"):
            user_data['tenant_name'] = tenant_doc["name"]

    return user_data


@users_router.get("/me/permissions")
async def get_current_user_permissions(current_user: UserInDB = Depends(get_current_active_user)):
    """Get all permissions for the current user"""
    permissions = ROLE_PERMISSIONS.get(current_user.role, [])
    return {
        "role": current_user.role.value,
        "permissions": [p.value for p in permissions]
    }


@users_router.put("/me", response_model=User)
async def update_current_user_profile(
    full_name: Optional[str] = None,
    company_name: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update current user's profile"""
    update_data = {}
    if full_name is not None:
        update_data["full_name"] = full_name
    if company_name is not None:
        update_data["company_name"] = company_name
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.users.update_one({"id": current_user.id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    return User(**{k: v for k, v in updated_user.items() if k != "hashed_password"})


# ============== ADMIN USER MANAGEMENT ==============

@admin_router.get("/users", response_model=List[User])
async def list_all_users(current_user: UserInDB = Depends(get_current_active_user)):
    """List all users - requires USERS_VIEW permission"""
    if not has_permission(current_user, Permission.USERS_VIEW):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot view users")
    
    users = await db.users.find({"tenant_id": current_user.tenant_id}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    return [User(**u) for u in users]


@admin_router.post("/users/create", response_model=User)
async def admin_create_user(
    input: AdminCreateUserInput,
    current_user: UserInDB = Depends(get_current_active_user)
):
    if not has_permission(current_user, Permission.USERS_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot create users")

    if input.role == UserRole.OWNER and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can create another owner")

    existing = await db.users.find_one({"email": input.email.lower()}, {"_id": 0, "id": 1})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(input.password)
    user = UserInDB(
        email=input.email.lower(),
        full_name=input.full_name,
        company_name=input.company_name or current_user.company_name,
        role=input.role,
        tenant_id=current_user.tenant_id,
        hashed_password=hashed_password,
    )
    await db.users.insert_one(user.model_dump())
    return User(**{k: v for k, v in user.model_dump().items() if k != "hashed_password"})


@admin_router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    input: PasswordReset,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin resets a user's password - requires USERS_MANAGE permission"""
    if not has_permission(current_user, Permission.USERS_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot reset passwords")
    
    # Find target user
    target_user = await db.users.find_one({"id": user_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only owner can reset another owner's password
    if target_user.get("role") == UserRole.OWNER.value and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can reset owner passwords")
    
    # Validate new password
    if len(input.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Hash and update password
    hashed_password = get_password_hash(input.new_password)
    await db.users.update_one(
        {"id": user_id, "tenant_id": current_user.tenant_id},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Password reset successfully for {target_user['email']}"}


@admin_router.put("/users/{user_id}/status")
async def admin_toggle_user_status(
    user_id: str,
    is_active: bool,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin enables/disables a user account - requires USERS_MANAGE permission"""
    if not has_permission(current_user, Permission.USERS_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot modify user status")
    
    # Prevent disabling own account
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account status")
    
    target_user = await db.users.find_one({"id": user_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only owner can disable another owner
    if target_user.get("role") == UserRole.OWNER.value and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can modify owner accounts")
    
    await db.users.update_one(
        {"id": user_id, "tenant_id": current_user.tenant_id},
        {"$set": {"is_active": is_active, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    status_text = "enabled" if is_active else "disabled"
    return {"message": f"User {target_user['email']} has been {status_text}"}


@admin_router.put("/users/{user_id}/role")
async def admin_update_user_role(
    user_id: str,
    input: UserRoleUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a user's role - requires USERS_MANAGE permission (Owner only)"""
    if not has_permission(current_user, Permission.USERS_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied: Only owners can manage roles")
    
    # Prevent changing own role
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own role")
    
    target_user = await db.users.find_one({"id": user_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update role
    await db.users.update_one(
        {"id": user_id, "tenant_id": current_user.tenant_id},
        {"$set": {"role": input.role.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Role updated to {input.role.value} for {target_user['email']}"}


@admin_router.delete("/users/{user_id}")
async def admin_delete_user(
    user_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin deletes a user - requires USERS_MANAGE permission (Owner only).
    Guardrails:
      - Cannot delete yourself
      - Cannot delete the last owner of the tenant"""
    if not has_permission(current_user, Permission.USERS_MANAGE):
        raise HTTPException(status_code=403, detail="Permission denied: Only owners can remove users")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove your own account")

    target_user = await db.users.find_one(
        {"id": user_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Last-owner guard
    if target_user.get("role") == UserRole.OWNER.value:
        owner_count = await db.users.count_documents({
            "tenant_id": current_user.tenant_id,
            "role": UserRole.OWNER.value,
            "is_active": True,
        })
        if owner_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the last owner of this tenant. Promote another user to owner first."
            )

    result = await db.users.delete_one(
        {"id": user_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": f"User {target_user.get('email')} removed"}
