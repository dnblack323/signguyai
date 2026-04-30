"""
Admin Audit Log Service

Records every privileged action performed by Platform Admins (and other
high-trust roles in the future) so that we have a permanent, queryable trail
of "who did what, to whom, when, and from where".

Collection: admin_audit_log

Document shape:
    {
        id, action, action_category,
        actor_user_id, actor_email, actor_role,
        target_type, target_id, target_label,
        tenant_id, tenant_name,
        summary, metadata, status,
        ip_address, user_agent,
        created_at
    }
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

logger = logging.getLogger(__name__)


def _extract_client_ip(request) -> Optional[str]:
    """Extract client IP, respecting X-Forwarded-For when behind a proxy."""
    if request is None:
        return None
    try:
        forwarded_for = request.headers.get("x-forwarded-for") if request.headers else None
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
    except Exception:
        return None
    return None


def _extract_user_agent(request) -> Optional[str]:
    if request is None:
        return None
    try:
        return request.headers.get("user-agent") if request.headers else None
    except Exception:
        return None


async def log_admin_action(
    db,
    *,
    request=None,
    actor=None,
    action: str,
    action_category: str = "other",
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    target_label: Optional[str] = None,
    tenant_id: Optional[str] = None,
    tenant_name: Optional[str] = None,
    summary: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    status: str = "success",
) -> str:
    """
    Persist a single audit-log entry.

    Returns the new entry id. Failures are swallowed so a logging issue
    never breaks the main privileged action.
    """
    try:
        entry_id = str(uuid.uuid4())
        actor_user_id = getattr(actor, "id", None) if actor else None
        actor_email = getattr(actor, "email", None) if actor else None
        actor_role = getattr(actor, "role", None) if actor else None
        # Role may be an Enum
        if actor_role is not None and hasattr(actor_role, "value"):
            actor_role = actor_role.value

        doc = {
            "id": entry_id,
            "action": action,
            "action_category": action_category,
            "actor_user_id": actor_user_id,
            "actor_email": actor_email,
            "actor_role": actor_role,
            "target_type": target_type,
            "target_id": target_id,
            "target_label": target_label,
            "tenant_id": tenant_id,
            "tenant_name": tenant_name,
            "summary": summary,
            "metadata": metadata or {},
            "status": status,
            "ip_address": _extract_client_ip(request),
            "user_agent": _extract_user_agent(request),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await db.admin_audit_log.insert_one(doc)
        return entry_id
    except Exception as audit_err:  # noqa: BLE001
        # Logging must never break the caller, but DO surface the failure
        # loudly to logs / Sentry so an ops engineer notices a missing audit
        # trail rather than an attacker silently exploiting the gap.
        logger.error(
            "AUDIT_LOG_WRITE_FAILED action=%s actor=%s target=%s err=%s",
            action,
            getattr(actor, "email", None),
            target_id,
            audit_err,
            exc_info=True,
        )
        return ""
