"""
Magic Links — Create shareable short-lived tokens for quotes (and future resources).

POST /api/magic-links          — create a magic link (authenticated)
GET  /api/magic-links          — list tenant's magic links (authenticated)
GET  /api/portal/preview/{tok} — public resource viewer
"""

import uuid
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from server import db, logger, get_current_active_user
from models import UserInDB

router = APIRouter(prefix="/magic-links", tags=["Magic Links"])
preview_router = APIRouter(prefix="/portal", tags=["Portal Preview"])

SUPPORTED_TYPES = {"quote"}


class MagicLinkCreate(BaseModel):
    resource_type: str
    resource_id: str
    customer_email: Optional[str] = None
    expires_in_days: int = 7


# ── helpers ──────────────────────────────────────────────────────────────────

async def _find_quote(resource_id: str, tenant_id: str):
    doc = await db.quotes.find_one(
        {"id": resource_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if doc:
        return doc
    return await db.order_quotes.find_one(
        {"id": resource_id, "tenant_id": tenant_id, "type": "quote"}, {"_id": 0}
    )


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("")
async def create_magic_link(
    data: MagicLinkCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    if data.resource_type not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported resource type: {data.resource_type}")

    # Verify resource exists and belongs to this tenant
    if data.resource_type == "quote":
        resource = await _find_quote(data.resource_id, current_user.tenant_id)
        if not resource:
            raise HTTPException(status_code=404, detail="Quote not found")

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)).isoformat()

    link = {
        "id": str(uuid.uuid4()),
        "token": token,
        "resource_type": data.resource_type,
        "resource_id": data.resource_id,
        "tenant_id": current_user.tenant_id,
        "customer_email": data.customer_email,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.id,
    }
    await db.magic_links.insert_one(link)

    return {
        "id": link["id"],
        "token": token,
        "resource_type": data.resource_type,
        "resource_id": data.resource_id,
        "expires_at": expires_at,
    }


@router.get("")
async def list_magic_links(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    current_user: UserInDB = Depends(get_current_active_user),
):
    query: dict = {"tenant_id": current_user.tenant_id}
    if resource_type:
        query["resource_type"] = resource_type
    if resource_id:
        query["resource_id"] = resource_id
    links = await db.magic_links.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return links


# ── public viewer ─────────────────────────────────────────────────────────────

@preview_router.get("/preview/{token}")
async def view_via_magic_link(token: str):
    """Public endpoint — return quote data for a valid magic link token."""
    link = await db.magic_links.find_one({"token": token}, {"_id": 0})
    if not link:
        raise HTTPException(status_code=404, detail="Link not found or expired")

    # Check expiry
    try:
        expires = datetime.fromisoformat(link["expires_at"].replace("Z", "+00:00"))
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=410, detail="This link has expired")
    except HTTPException:
        raise
    except Exception:
        pass

    resource = None
    if link["resource_type"] == "quote":
        resource = await db.quotes.find_one({"id": link["resource_id"]}, {"_id": 0})
        if not resource:
            resource = await db.order_quotes.find_one(
                {"id": link["resource_id"], "type": "quote"}, {"_id": 0}
            )

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    customer = None
    if resource.get("customer_id"):
        customer = await db.customers.find_one(
            {"id": resource["customer_id"]}, {"_id": 0, "name": 1, "email": 1, "company_name": 1}
        )

    tenant = None
    if link.get("tenant_id"):
        tenant = await db.tenants.find_one(
            {"id": link["tenant_id"]}, {"_id": 0, "name": 1, "phone": 1, "email": 1}
        )

    return {
        "resource_type": link["resource_type"],
        "resource": resource,
        "customer": customer,
        "tenant": tenant,
        "link_expires_at": link["expires_at"],
    }
