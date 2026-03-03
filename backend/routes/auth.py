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


# ============== AUTH ROUTES ==============

@router.post("/register", response_model=Token)
async def register(input: UserCreate):
    """Register a new user and create their tenant/company with Founders Edition plan"""
    from services.founders_config import (
        FOUNDERS_EDITION_MAX_CUSTOMERS, 
        FOUNDERS_EDITION_MONTHLY_CREDITS,
        FOUNDERS_EDITION_PLAN
    )
    from datetime import timezone
    from dateutil.relativedelta import relativedelta
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": input.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check Founders Edition availability
    founders_count = await db.tenants.count_documents({"plan": "founders_edition"})
    if founders_count >= FOUNDERS_EDITION_MAX_CUSTOMERS:
        raise HTTPException(
            status_code=400, 
            detail="Founders Edition is sold out. Please check back for future plans."
        )
    
    # Self-registration always creates a new tenant (company) and the user becomes owner
    company_name = input.company_name or f"{input.full_name}'s Sign Shop"
    
    # Create tenant with Founders Edition plan
    tenant = Tenant(
        name=company_name,
        slug=generate_tenant_slug(company_name),
        owner_email=input.email.lower(),
    )
    tenant_doc = tenant.model_dump()
    
    # Add Founders Edition plan fields
    tenant_doc["plan"] = "founders_edition"
    tenant_doc["plan_name"] = FOUNDERS_EDITION_PLAN["plan_name"]
    tenant_doc["founder_lifetime_lock"] = True
    tenant_doc["plan_started_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.tenants.insert_one(tenant_doc)
    tenant_id = tenant.id
    logger.info(f"Created new Founders Edition tenant: {tenant.name} ({tenant.id})")
    
    # Initialize AI credits for this tenant
    now = datetime.now(timezone.utc)
    period_end = now + relativedelta(months=1)
    
    credits_doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "monthly_credits": FOUNDERS_EDITION_MONTHLY_CREDITS,
        "purchased_credits": 0,
        "monthly_credits_granted_at": now.isoformat(),
        "monthly_credits_period_start": now.isoformat(),
        "monthly_credits_period_end": period_end.isoformat(),
        "low_credits_threshold": 10,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    await db.user_credits.insert_one(credits_doc)
    
    # Record initial credit grant transaction
    from models.credits import CreditTransaction, CreditTransactionType
    transaction = CreditTransaction(
        tenant_id=tenant_id,
        transaction_type=CreditTransactionType.MONTHLY_GRANT,
        amount=FOUNDERS_EDITION_MONTHLY_CREDITS,
        balance_after=FOUNDERS_EDITION_MONTHLY_CREDITS,
        monthly_balance_after=FOUNDERS_EDITION_MONTHLY_CREDITS,
        purchased_balance_after=0,
        description=f"Welcome to Founders Edition! {FOUNDERS_EDITION_MONTHLY_CREDITS} monthly credits granted."
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
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Account is disabled")
    
    # Create access token - extended expiry if "remember me" is checked
    if input.remember_me:
        expires_delta = timedelta(days=30)
        expires_in = 30 * 24 * 60 * 60
    else:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    access_token = create_access_token(data={"sub": user["id"]}, expires_delta=expires_delta)
    
    return Token(access_token=access_token, expires_in=expires_in)


# ============== USER PROFILE ROUTES ==============

@users_router.get("/me", response_model=User)
async def get_current_user_profile(current_user: UserInDB = Depends(get_current_active_user)):
    """Get current user's profile"""
    return User(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        company_name=current_user.company_name,
        is_active=current_user.is_active,
        role=current_user.role,
        tenant_id=current_user.tenant_id,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        is_founder=getattr(current_user, 'is_founder', False)
    )


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
    
    users = await db.users.find({}, {"_id": 0, "hashed_password": 0}).to_list(1000)
    return [User(**u) for u in users]


@admin_router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: str,
    input: PasswordReset,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin resets a user's password - requires USERS_EDIT permission"""
    if not has_permission(current_user, Permission.USERS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot reset passwords")
    
    # Find target user
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
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
        {"id": user_id},
        {"$set": {"hashed_password": hashed_password, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Password reset successfully for {target_user['email']}"}


@admin_router.put("/users/{user_id}/status")
async def admin_toggle_user_status(
    user_id: str,
    is_active: bool,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin enables/disables a user account - requires USERS_EDIT permission"""
    if not has_permission(current_user, Permission.USERS_EDIT):
        raise HTTPException(status_code=403, detail="Permission denied: Cannot modify user status")
    
    # Prevent disabling own account
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own account status")
    
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only owner can disable another owner
    if target_user.get("role") == UserRole.OWNER.value and current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only owners can modify owner accounts")
    
    await db.users.update_one(
        {"id": user_id},
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
    
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update role
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": input.role.value, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Role updated to {input.role.value} for {target_user['email']}"}
