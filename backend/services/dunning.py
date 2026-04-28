"""
Dunning Service

Centralized state machine for "failed payment → grace → auto-suspend →
auto-reactivate" so that Stripe webhooks (and the manual mark-paid endpoint)
all converge on the same logic.

Tracked on the tenant document:
    payment_failed_count          int   number of consecutive failures
    first_payment_failure_at      iso   first failure in this streak
    last_payment_failure_at       iso   most recent failure
    auto_suspended_for_payment    bool  set true when this service triggered the suspension
    last_payment_succeeded_at     iso

Tracked in the audit log under category="billing":
    payment.failed
    dunning.auto_suspend
    payment.succeeded
    dunning.auto_reactivate
    payment.manual_mark_paid

Auto-suspend threshold: AUTO_SUSPEND_AFTER_FAILURES (default 3).
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os

from services.admin_audit import log_admin_action

AUTO_SUSPEND_AFTER_FAILURES = int(os.environ.get("DUNNING_AUTO_SUSPEND_AFTER", "3"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _get_owner_email(db, tenant: dict) -> Optional[str]:
    return tenant.get("owner_email")


async def record_payment_failure(
    db,
    *,
    tenant_id: str,
    amount: Optional[float] = None,
    currency: str = "usd",
    stripe_invoice_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record a failed payment for a tenant. Returns the post-state including:
    {
        "tenant_id", "payment_failed_count", "auto_suspended": bool,
        "email_sent": bool, "email_status": dict|None
    }
    """
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        return {"tenant_id": tenant_id, "found": False}

    now = _now_iso()
    new_count = int(tenant.get("payment_failed_count") or 0) + 1
    update_doc = {
        "payment_failed_count": new_count,
        "last_payment_failure_at": now,
        "updated_at": now,
    }
    if not tenant.get("first_payment_failure_at"):
        update_doc["first_payment_failure_at"] = now

    await db.tenants.update_one({"id": tenant_id}, {"$set": update_doc})

    # Audit log
    await log_admin_action(
        db,
        action="payment.failed",
        action_category="billing",
        target_type="tenant",
        target_id=tenant_id,
        target_label=tenant.get("name"),
        tenant_id=tenant_id,
        tenant_name=tenant.get("name"),
        summary=f"Payment failed (attempt {new_count}) for {tenant.get('name')}",
        metadata={
            "attempt": new_count,
            "amount": amount,
            "currency": currency,
            "stripe_invoice_id": stripe_invoice_id,
            "stripe_subscription_id": stripe_subscription_id,
        },
    )

    auto_suspended = False
    email_status = None

    # Auto-suspend if past threshold and not already suspended.
    if new_count >= AUTO_SUSPEND_AFTER_FAILURES and tenant.get("is_active") is not False:
        # Skip auto-suspend if tenant contains a platform_admin user (self-lockout protection)
        pa_count = await db.users.count_documents({
            "tenant_id": tenant_id,
            "role": "platform_admin",
        })
        if pa_count == 0:
            await db.tenants.update_one(
                {"id": tenant_id},
                {"$set": {
                    "is_active": False,
                    "suspension_reason": (
                        f"Non-payment: {new_count} consecutive failed payment attempts"
                    ),
                    "suspended_at": now,
                    "suspended_by": "system:dunning",
                    "suspended_by_email": "system@dunning",
                    "auto_suspended_for_payment": True,
                    "reactivated_at": None,
                    "reactivated_by": None,
                    "reactivated_by_email": None,
                    "updated_at": now,
                }},
            )
            auto_suspended = True
            await log_admin_action(
                db,
                action="dunning.auto_suspend",
                action_category="billing",
                target_type="tenant",
                target_id=tenant_id,
                target_label=tenant.get("name"),
                tenant_id=tenant_id,
                tenant_name=tenant.get("name"),
                summary=(
                    f"Auto-suspended {tenant.get('name')} after {new_count} "
                    "consecutive failed payments"
                ),
                metadata={"failure_count": new_count},
            )

    # Send email
    owner_email = await _get_owner_email(db, tenant)
    if owner_email:
        try:
            from services.email_service import email_service
            if auto_suspended:
                email_status = await email_service.send_dunning_suspended_email(
                    owner_email=owner_email,
                    tenant_name=tenant.get("name") or "your account",
                    tenant_id=tenant_id,
                )
            else:
                attempts_remaining = max(AUTO_SUSPEND_AFTER_FAILURES - new_count, 0)
                email_status = await email_service.send_payment_failed_email(
                    owner_email=owner_email,
                    tenant_name=tenant.get("name") or "your account",
                    tenant_id=tenant_id,
                    attempt=new_count,
                    attempts_remaining=attempts_remaining,
                    amount=amount,
                    currency=(currency or "usd").upper(),
                )
        except Exception as e:
            email_status = {"success": False, "error": str(e)}

    return {
        "tenant_id": tenant_id,
        "payment_failed_count": new_count,
        "auto_suspended": auto_suspended,
        "email_status": email_status,
    }


async def record_payment_success(
    db,
    *,
    tenant_id: str,
    auto_reactivate: bool = True,
    triggered_by: str = "system:dunning",
) -> Dict[str, Any]:
    """
    Reset the dunning counters on a successful payment, and (optionally)
    auto-reactivate the tenant if it was previously auto-suspended for payment.
    """
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    if not tenant:
        return {"tenant_id": tenant_id, "found": False}

    now = _now_iso()

    update_doc: Dict[str, Any] = {
        "payment_failed_count": 0,
        "first_payment_failure_at": None,
        "last_payment_succeeded_at": now,
        "updated_at": now,
    }

    auto_reactivated = False
    if (
        auto_reactivate
        and tenant.get("is_active") is False
        and tenant.get("auto_suspended_for_payment") is True
    ):
        update_doc.update({
            "is_active": True,
            "suspension_reason": None,
            "suspended_at": None,
            "suspended_by": None,
            "suspended_by_email": None,
            "auto_suspended_for_payment": False,
            "reactivated_at": now,
            "reactivated_by": triggered_by,
            "reactivated_by_email": "system@dunning",
        })
        auto_reactivated = True

    await db.tenants.update_one({"id": tenant_id}, {"$set": update_doc})

    # Audit log success
    await log_admin_action(
        db,
        action="payment.succeeded",
        action_category="billing",
        target_type="tenant",
        target_id=tenant_id,
        target_label=tenant.get("name"),
        tenant_id=tenant_id,
        tenant_name=tenant.get("name"),
        summary=f"Payment succeeded for {tenant.get('name')}; dunning counters reset",
        metadata={
            "previous_failure_count": tenant.get("payment_failed_count", 0),
        },
    )
    if auto_reactivated:
        await log_admin_action(
            db,
            action="dunning.auto_reactivate",
            action_category="billing",
            target_type="tenant",
            target_id=tenant_id,
            target_label=tenant.get("name"),
            tenant_id=tenant_id,
            tenant_name=tenant.get("name"),
            summary=f"Auto-reactivated {tenant.get('name')} after payment success",
            metadata={"trigger": triggered_by},
        )
        # Best-effort welcome-back email
        owner_email = await _get_owner_email(db, tenant)
        if owner_email:
            try:
                from services.email_service import email_service
                await email_service.send_tenant_reactivated_email(
                    owner_email=owner_email,
                    tenant_name=tenant.get("name") or "your account",
                    tenant_id=tenant_id,
                    note="Payment received — your account is active again.",
                )
            except Exception:
                pass

    return {
        "tenant_id": tenant_id,
        "payment_failed_count": 0,
        "auto_reactivated": auto_reactivated,
    }
