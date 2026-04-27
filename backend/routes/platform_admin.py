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

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid

from models import UserRole, User
from server import (
    db, logger,
    get_current_user, create_access_token, UserInDB
)

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


class ImpersonateRequest(BaseModel):
    target_user_id: str


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
    """Dependency to ensure user is a platform admin"""
    if current_user.role != UserRole.PLATFORM_ADMIN:
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
            user_count=user_count
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
    
    return {
        "tenant": TenantDetail(**tenant),
        "users": valid_users,
        "invalid_users_count": len(invalid_users)
    }


@router.post("/impersonate")
async def start_impersonation(
    request: ImpersonateRequest,
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
    current_user: UserInDB = Depends(get_current_user)
):
    """
    Exit impersonation mode and return to platform admin account
    
    This endpoint is called by an impersonating user to end the session.
    The frontend should handle the token replacement.
    """
    
    # This endpoint is accessible to anyone, but we need to verify impersonation
    # The token should have impersonation metadata
    # For now, we just log the exit and return success
    # The frontend will handle removing the impersonation token
    
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
