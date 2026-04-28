"""
E2E test for the Stripe webhook → Dunning Workflow integration.

Posts synthetic `invoice.payment_failed` and `invoice.payment_succeeded`
events to the real `/api/webhook/stripe` endpoint and asserts that the
dunning state machine fires correctly: counters increment, threshold
hits trigger auto-suspend, and a payment success auto-reactivates.

This test runs without the Stripe CLI by relying on the dev fallback
where the webhook handler accepts unsigned events when STRIPE_WEBHOOK_SECRET
is not configured (which is the case in this environment).

Usage:  cd /app/backend && python tests/test_dunning_webhook_e2e.py
"""

import asyncio
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

API_URL = os.environ.get("REACT_APP_BACKEND_URL") or os.environ.get("API_URL")
if not API_URL:
    # Fall back to the value in the frontend .env
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    API_URL = line.strip().split("=", 1)[1]
                    break
    except FileNotFoundError:
        pass

assert API_URL, "API_URL not found"

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_failed_event(stripe_subscription_id: str, stripe_invoice_id: str, amount_cents: int = 4900) -> dict:
    """Synthetic Stripe `invoice.payment_failed` event payload."""
    return {
        "id": f"evt_{uuid.uuid4().hex}",
        "object": "event",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": stripe_invoice_id,
                "object": "invoice",
                "subscription": stripe_subscription_id,
                "amount_due": amount_cents,
                "amount_paid": 0,
                "currency": "usd",
                "status": "open",
                "metadata": {},
            }
        },
    }


def make_succeeded_event(stripe_subscription_id: str, stripe_invoice_id: str, amount_cents: int = 4900) -> dict:
    """Synthetic Stripe `invoice.payment_succeeded` event payload."""
    return {
        "id": f"evt_{uuid.uuid4().hex}",
        "object": "event",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "id": stripe_invoice_id,
                "object": "invoice",
                "subscription": stripe_subscription_id,
                "amount_due": amount_cents,
                "amount_paid": amount_cents,
                "currency": "usd",
                "status": "paid",
                "metadata": {},
            }
        },
    }


async def main() -> int:
    print(f"[setup] API_URL={API_URL}")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # 1. Find or create a test tenant + subscription
    test_tenant = await db.tenants.find_one(
        {"name": {"$regex": "^TEST_TenantB"}}, {"_id": 0}
    )
    if not test_tenant:
        print("[setup] No TEST_TenantB tenant; aborting (this test relies on existing seed data)")
        client.close()
        return 1

    tenant_id = test_tenant["id"]
    sub_id = f"sub_e2e_{uuid.uuid4().hex[:12]}"
    print(f"[setup] tenant_id={tenant_id}  subscription_id={sub_id}")

    # Reset dunning state on the tenant + ensure NOT a founder for this run
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {
            "is_active": True,
            "payment_failed_count": 0,
            "first_payment_failure_at": None,
            "last_payment_failure_at": None,
            "last_payment_succeeded_at": None,
            "auto_suspended_for_payment": False,
            "suspension_reason": None,
            "suspended_at": None,
            "grace_period_until": None,
            "is_founder": False,
            "dunning_failure_threshold": None,
        }},
    )
    # Ensure no founder users in this tenant for the basic flow test
    await db.users.update_many({"tenant_id": tenant_id}, {"$set": {"is_founder": False}})

    # Create or upsert a subscription record so the webhook can find it
    await db.subscriptions.update_one(
        {"stripe_subscription_id": sub_id},
        {"$set": {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "stripe_subscription_id": sub_id,
            "status": "active",
            "plan": "test",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }},
        upsert=True,
    )

    webhook_url = f"{API_URL.rstrip('/')}/api/webhook/stripe"
    failures_to_send = 3  # default threshold

    async with httpx.AsyncClient(timeout=30.0) as http:
        # ----- Phase 1: send 3 failed events; the last one should auto-suspend -----
        for i in range(1, failures_to_send + 1):
            payload = make_failed_event(sub_id, f"in_e2e_{i}_{uuid.uuid4().hex[:6]}")
            r = await http.post(webhook_url, json=payload)
            print(f"[failure {i}] webhook status={r.status_code}  body={r.text[:120]}")
            assert r.status_code == 200, f"Webhook returned {r.status_code}"
            # Give async db writes a beat
            await asyncio.sleep(0.4)

        t = await db.tenants.find_one(
            {"id": tenant_id},
            {"_id": 0, "is_active": 1, "payment_failed_count": 1, "auto_suspended_for_payment": 1, "suspension_reason": 1, "suspended_by": 1},
        )
        print(f"[after 3 failures] {t}")
        assert t["payment_failed_count"] == 3, f"expected 3, got {t['payment_failed_count']}"
        assert t["is_active"] is False, "tenant should be auto-suspended"
        assert t["auto_suspended_for_payment"] is True
        assert t["suspended_by"] == "system:dunning"
        print("[phase 1] PASS — auto-suspended after 3 webhook-driven failures")

        # ----- Phase 2: send a payment success → auto-reactivate -----
        payload = make_succeeded_event(sub_id, f"in_e2e_pay_{uuid.uuid4().hex[:6]}")
        r = await http.post(webhook_url, json=payload)
        print(f"[success]  webhook status={r.status_code}  body={r.text[:120]}")
        assert r.status_code == 200
        await asyncio.sleep(0.5)

        t = await db.tenants.find_one(
            {"id": tenant_id},
            {"_id": 0, "is_active": 1, "payment_failed_count": 1, "auto_suspended_for_payment": 1, "last_payment_succeeded_at": 1, "reactivated_by_email": 1},
        )
        print(f"[after success] {t}")
        assert t["is_active"] is True, "tenant should be auto-reactivated"
        assert t["payment_failed_count"] == 0
        assert t["auto_suspended_for_payment"] is False
        assert t["last_payment_succeeded_at"]
        print("[phase 2] PASS — auto-reactivated on payment success")

        # ----- Phase 3: founder grace period -----
        # Mark a user in this tenant as a founder, reset state, send 3 more failures.
        # The 3rd failure should NOT auto-suspend; it should start the grace window.
        await db.users.update_one(
            {"tenant_id": tenant_id},
            {"$set": {"is_founder": True}},
        )
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {
                "payment_failed_count": 0,
                "first_payment_failure_at": None,
                "last_payment_failure_at": None,
                "grace_period_until": None,
                "is_active": True,
                "auto_suspended_for_payment": False,
                "suspension_reason": None,
            }},
        )
        for i in range(1, failures_to_send + 1):
            payload = make_failed_event(sub_id, f"in_grace_{i}_{uuid.uuid4().hex[:6]}")
            r = await http.post(webhook_url, json=payload)
            assert r.status_code == 200
            await asyncio.sleep(0.4)
        t = await db.tenants.find_one(
            {"id": tenant_id},
            {"_id": 0, "is_active": 1, "payment_failed_count": 1, "grace_period_until": 1, "auto_suspended_for_payment": 1},
        )
        print(f"[founder grace] {t}")
        assert t["payment_failed_count"] == 3
        assert t["is_active"] is True, "founder should be in grace, not suspended"
        assert t["grace_period_until"] is not None, "grace period should be set"
        assert t["auto_suspended_for_payment"] is False
        print("[phase 3] PASS — founder grace window started instead of immediate suspend")

        # ----- Phase 4: per-tenant threshold override -----
        # Reset state, set threshold=5, send 3 more failures → should NOT trigger anything
        await db.users.update_many({"tenant_id": tenant_id}, {"$set": {"is_founder": False}})
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {
                "payment_failed_count": 0,
                "first_payment_failure_at": None,
                "grace_period_until": None,
                "dunning_failure_threshold": 5,
                "is_active": True,
                "auto_suspended_for_payment": False,
                "suspension_reason": None,
            }},
        )
        for i in range(1, 4):  # only 3 failures
            payload = make_failed_event(sub_id, f"in_thr_{i}_{uuid.uuid4().hex[:6]}")
            r = await http.post(webhook_url, json=payload)
            assert r.status_code == 200
            await asyncio.sleep(0.3)
        t = await db.tenants.find_one(
            {"id": tenant_id},
            {"_id": 0, "is_active": 1, "payment_failed_count": 1, "auto_suspended_for_payment": 1},
        )
        print(f"[per-tenant threshold (5) after 3 failures] {t}")
        assert t["payment_failed_count"] == 3
        assert t["is_active"] is True, "should not suspend below per-tenant threshold of 5"
        # Now send 2 more → should suspend at attempt 5
        for i in range(4, 6):
            payload = make_failed_event(sub_id, f"in_thr_{i}_{uuid.uuid4().hex[:6]}")
            r = await http.post(webhook_url, json=payload)
            assert r.status_code == 200
            await asyncio.sleep(0.4)
        t = await db.tenants.find_one(
            {"id": tenant_id},
            {"_id": 0, "is_active": 1, "payment_failed_count": 1, "auto_suspended_for_payment": 1},
        )
        print(f"[per-tenant threshold (5) after 5 failures] {t}")
        assert t["payment_failed_count"] == 5
        assert t["is_active"] is False
        assert t["auto_suspended_for_payment"] is True
        print("[phase 4] PASS — per-tenant threshold override respected")

    # Final cleanup: reset the test tenant
    await db.tenants.update_one(
        {"id": tenant_id},
        {"$set": {
            "is_active": True,
            "payment_failed_count": 0,
            "first_payment_failure_at": None,
            "last_payment_failure_at": None,
            "auto_suspended_for_payment": False,
            "suspension_reason": None,
            "suspended_at": None,
            "grace_period_until": None,
            "dunning_failure_threshold": None,
        }},
    )
    await db.subscriptions.delete_many({"stripe_subscription_id": sub_id})
    client.close()
    print("\n[ALL PHASES PASSED]")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
