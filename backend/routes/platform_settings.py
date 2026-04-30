"""
Platform-wide settings: Announcement Banner + Maintenance Mode.

Stored in the `platform_settings` collection in a single document with id="global":
    {
      "id": "global",
      "announcement": {
        "message": str, "severity": "info"|"warning"|"critical",
        "dismissable": bool, "expires_at": iso|None,
        "updated_at": iso, "updated_by_email": str
      } | None,
      "maintenance": {
        "enabled": bool,
        "message": str | None,
        "started_at": iso | None,
        "started_by_email": str | None
      }
    }

Public read endpoints power the global banner on every page (login + app).
Admin write endpoints require `platform_admin`.

Maintenance enforcement: middleware (registered in server.py) returns 503
on mutation methods (POST/PUT/PATCH/DELETE) for non-platform-admin tokens,
unless the path is on the allowlist (auth, platform-admin, webhooks).
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from server import db, logger
from core_runtime import UserInDB
from routes.platform_admin import require_platform_admin
from services.admin_audit import log_admin_action


public_router = APIRouter(prefix="/platform", tags=["Platform Public Settings"])
admin_router = APIRouter(prefix="/platform-admin", tags=["Platform Admin - Settings"])


# ---------- Models ----------

class AnnouncementPayload(BaseModel):
    message: Optional[str] = None  # None / empty clears the banner
    severity: str = Field(default="info")  # info | warning | critical
    dismissable: bool = True
    expires_at: Optional[str] = None  # ISO datetime


class MaintenancePayload(BaseModel):
    enabled: bool
    message: Optional[str] = None


# ---------- Helpers ----------

SETTINGS_ID = "global"


async def _get_settings() -> dict:
    doc = await db.platform_settings.find_one({"id": SETTINGS_ID}, {"_id": 0})
    if not doc:
        doc = {"id": SETTINGS_ID, "announcement": None, "maintenance": {"enabled": False}}
        await db.platform_settings.insert_one(dict(doc))
    return doc


def _is_announcement_active(announcement: Optional[dict]) -> bool:
    if not announcement or not announcement.get("message"):
        return False
    expires_at = announcement.get("expires_at")
    if not expires_at:
        return True
    try:
        return datetime.fromisoformat(expires_at.replace("Z", "+00:00")) > datetime.now(timezone.utc)
    except Exception:
        return True


# ---------- Public read endpoints ----------

@public_router.get("/announcement")
async def get_announcement():
    """Public endpoint — used by every page to render the banner."""
    settings = await _get_settings()
    ann = settings.get("announcement")
    if not _is_announcement_active(ann):
        return {"announcement": None}
    return {"announcement": ann}


@public_router.get("/maintenance")
async def get_maintenance():
    """Public endpoint — used to render the maintenance banner."""
    settings = await _get_settings()
    return {"maintenance": settings.get("maintenance") or {"enabled": False}}


# ---------- Admin write endpoints ----------

@admin_router.put("/announcement")
async def set_announcement(
    payload: AnnouncementPayload,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin),
):
    """Create / update / clear the global announcement banner."""
    severity = (payload.severity or "info").lower()
    if severity not in {"info", "warning", "critical"}:
        raise HTTPException(status_code=400, detail="severity must be info | warning | critical")

    now_iso = datetime.now(timezone.utc).isoformat()
    if not payload.message or not payload.message.strip():
        # Clear the banner
        await db.platform_settings.update_one(
            {"id": SETTINGS_ID},
            {"$set": {"announcement": None, "updated_at": now_iso}},
            upsert=True,
        )
        await log_admin_action(
            db,
            request=http_request,
            actor=current_user,
            action="announcement.clear",
            action_category="platform",
            target_type="platform_settings",
            target_id=SETTINGS_ID,
            target_label="Announcement Banner",
            summary="Cleared the announcement banner",
        )
        return {"announcement": None}

    new_ann = {
        "message": payload.message.strip(),
        "severity": severity,
        "dismissable": bool(payload.dismissable),
        "expires_at": payload.expires_at,
        "updated_at": now_iso,
        "updated_by_email": current_user.email,
    }
    await db.platform_settings.update_one(
        {"id": SETTINGS_ID},
        {"$set": {"announcement": new_ann, "updated_at": now_iso}},
        upsert=True,
    )
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action="announcement.set",
        action_category="platform",
        target_type="platform_settings",
        target_id=SETTINGS_ID,
        target_label="Announcement Banner",
        summary=f"Set announcement: {new_ann['message'][:80]}",
        metadata={"severity": severity, "expires_at": payload.expires_at},
    )
    return {"announcement": new_ann}


@admin_router.put("/maintenance")
async def set_maintenance(
    payload: MaintenancePayload,
    http_request: Request,
    current_user: UserInDB = Depends(require_platform_admin),
):
    """Enable or disable maintenance mode."""
    now_iso = datetime.now(timezone.utc).isoformat()
    if payload.enabled:
        new_state = {
            "enabled": True,
            "message": (payload.message or "Scheduled maintenance in progress").strip(),
            "started_at": now_iso,
            "started_by_email": current_user.email,
        }
    else:
        new_state = {
            "enabled": False,
            "message": None,
            "started_at": None,
            "started_by_email": None,
        }
    await db.platform_settings.update_one(
        {"id": SETTINGS_ID},
        {"$set": {"maintenance": new_state, "updated_at": now_iso}},
        upsert=True,
    )
    await log_admin_action(
        db,
        request=http_request,
        actor=current_user,
        action=("maintenance.enable" if payload.enabled else "maintenance.disable"),
        action_category="platform",
        target_type="platform_settings",
        target_id=SETTINGS_ID,
        target_label="Maintenance Mode",
        summary=(
            f"Enabled maintenance mode: {new_state['message']}"
            if payload.enabled
            else "Disabled maintenance mode"
        ),
        metadata={"message": new_state.get("message")},
    )
    return {"maintenance": new_state}


@admin_router.get("/settings")
async def get_full_settings(
    current_user: UserInDB = Depends(require_platform_admin),
):
    """Admin view: returns both announcement and maintenance state in one shot."""
    settings = await _get_settings()
    return {
        "announcement": settings.get("announcement"),
        "maintenance": settings.get("maintenance") or {"enabled": False},
    }
