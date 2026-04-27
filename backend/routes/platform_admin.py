"""
Platform Admin Routes - Minimal MVP for Tenant Impersonation

This module provides:
1. Tenant list
2. Tenant detail with users
3. Impersonate tenant user
4. Exit impersonation
5. Impersonation logs
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
    is_active: bool
    created_at: str
    updated_at: str


class ImpersonateRequest(BaseModel):
    target_user_id: str


# ============== HELPER FUNCTIONS ==============

def require_platform_admin(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Dependency to ensure user is a platform admin"""
    if current_user.role != UserRole.PLATFORM_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Platform Admin privileges required"
        )
    return current_user


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
    
    # Get all users for this tenant
    users = await db.users.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "hashed_password": 0}
    ).to_list(1000)
    
    return {
        "tenant": TenantDetail(**tenant),
        "users": [User(**u) for u in users]
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
