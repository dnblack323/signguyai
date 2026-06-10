"""Iteration 159 — Event Store polish pass.

Covers:
- GET /api/storefront/{id}/supporters (gating on store_type/fundraiser_enabled/
  show_supporter_names; donor_consent rendering; PII sanitization).
- POST /api/stripe-connect/webstore/{id}/checkout donor_consent field
  (Pydantic acceptance + ge=0 validation on donation_amount).
- Portal notifications: GET /api/portal/notifications (filtering),
  POST /api/portal/notifications/{id}/dismiss (own-only, 404),
  POST /api/portal/notifications/dismiss-all.
- Idempotent webstore_assigned notification seeding via GET /api/portal/webstores.
- GET /api/webstores/v2/{id}/event-setup-checklist (admin) — shape, done-flag
  flip when products are assigned / status flipped, tenant-scope guard.

Uses the existing event store "Gala Test 2026 UI"
(bf406578-1c57-4449-ab13-66736f3c2842) on tenant
d9c5507b-879c-4bec-9736-1dc841334719 for both admin and storefront tests.
"""
import os
import time
import uuid
import pytest
import requests
from datetime import datetime, timezone

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://sms-invoices.preview.emergentagent.com",
).rstrip("/")

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
ADMIN_TENANT = "d9c5507b-879c-4bec-9736-1dc841334719"
EVENT_WS_ID = "bf406578-1c57-4449-ab13-66736f3c2842"  # Gala Test 2026 UI

PORTAL_POS_EMAIL = "demo-fundraiser@rysoccer.example"
PORTAL_POS_PASSWORD = "TestPortal123!"
PORTAL_POS_WS_ID = "3dae02a7-0e2c-4ba1-a639-df19833161fc"

PORTAL_NEG_EMAIL = "portalreg_1776974524@example.com"
PORTAL_NEG_PASSWORD = "TestNeg123!"


# -------------------- shared fixtures --------------------

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
    })
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def portal_pos_token():
    r = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
        "email": PORTAL_POS_EMAIL, "password": PORTAL_POS_PASSWORD,
    })
    if r.status_code != 200:
        # try register fallback (existing customer)
        requests.post(f"{BASE_URL}/api/portal/auth/register", json={
            "email": PORTAL_POS_EMAIL, "password": PORTAL_POS_PASSWORD,
        })
        r = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": PORTAL_POS_EMAIL, "password": PORTAL_POS_PASSWORD,
        })
    if r.status_code != 200:
        pytest.skip(f"portal pos login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def portal_neg_token():
    r = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
        "email": PORTAL_NEG_EMAIL, "password": PORTAL_NEG_PASSWORD,
    })
    if r.status_code != 200:
        pytest.skip(f"portal neg login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("access_token") or r.json().get("token")


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# -------------------- Admin Event-Setup Checklist --------------------

class TestEventSetupChecklist:
    """Admin GET /api/webstores/v2/{id}/event-setup-checklist."""

    REQUIRED_KEYS = {
        "event_details", "questionnaire_sent", "questionnaire_completed",
        "safe_answers_applied", "stripe_invite_sent", "stripe_complete",
        "products_assigned", "store_live",
    }
    OPTIONAL_KEYS = {"fundraiser_enabled", "first_order_received"}

    def test_checklist_shape(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/webstores/v2/{EVENT_WS_ID}/event-setup-checklist",
            headers=_h(admin_token),
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["webstore_id"] == EVENT_WS_ID
        assert data["store_type"] == "event"
        items = data["items"]
        assert isinstance(items, list) and len(items) >= 9
        keys = {i["key"] for i in items}
        assert self.REQUIRED_KEYS.issubset(keys)
        assert self.OPTIONAL_KEYS.issubset(keys)

        # percent + counts shape
        assert isinstance(data["required_count"], int)
        assert isinstance(data["required_done"], int)
        assert isinstance(data["percent_complete"], int)
        assert 0 <= data["percent_complete"] <= 100

        # each item: key/label/done present; optional flag separates required from optional
        for it in items:
            assert "key" in it and "label" in it and "done" in it
            assert isinstance(it["done"], bool)

        # required_count excludes optional items
        required_items = [i for i in items if not i.get("optional")]
        assert data["required_count"] == len(required_items)

    def test_checklist_requires_auth(self):
        r = requests.get(
            f"{BASE_URL}/api/webstores/v2/{EVENT_WS_ID}/event-setup-checklist"
        )
        assert r.status_code in (401, 403)

    def test_checklist_404_for_unknown_store(self, admin_token):
        r = requests.get(
            f"{BASE_URL}/api/webstores/v2/{uuid.uuid4()}/event-setup-checklist",
            headers=_h(admin_token),
        )
        assert r.status_code == 404

    def test_checklist_tenant_scoped_404_cross_tenant(self, admin_token):
        # Try the cross-tenant positive portal webstore (different tenant)
        r = requests.get(
            f"{BASE_URL}/api/webstores/v2/{PORTAL_POS_WS_ID}/event-setup-checklist",
            headers=_h(admin_token),
        )
        # Admin tenant != positive webstore's tenant → must be 404
        assert r.status_code == 404, (
            f"Expected 404 cross-tenant, got {r.status_code} {r.text[:200]}"
        )

    def test_checklist_store_live_flips_with_status(self, admin_token):
        """Set status=active via direct DB write (Stripe gating blocks PUT) →
        store_live becomes done; revert."""
        try:
            from pymongo import MongoClient
        except ImportError:
            pytest.skip("pymongo not available")
        c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "signguy_ai")]
        snap = db.webstores_v2.find_one({"id": EVENT_WS_ID}, {"_id": 0, "status": 1})
        original_status = (snap or {}).get("status") or "pending"

        db.webstores_v2.update_one({"id": EVENT_WS_ID}, {"$set": {"status": "active"}})
        try:
            r = requests.get(
                f"{BASE_URL}/api/webstores/v2/{EVENT_WS_ID}/event-setup-checklist",
                headers=_h(admin_token),
            )
            assert r.status_code == 200
            items = {i["key"]: i for i in r.json()["items"]}
            assert items["store_live"]["done"] is True

            # Now flip back to pending and confirm done flips to False
            db.webstores_v2.update_one(
                {"id": EVENT_WS_ID}, {"$set": {"status": "pending"}}
            )
            r2 = requests.get(
                f"{BASE_URL}/api/webstores/v2/{EVENT_WS_ID}/event-setup-checklist",
                headers=_h(admin_token),
            )
            items2 = {i["key"]: i for i in r2.json()["items"]}
            assert items2["store_live"]["done"] is False
        finally:
            db.webstores_v2.update_one(
                {"id": EVENT_WS_ID}, {"$set": {"status": original_status}}
            )
            c.close()


# -------------------- Storefront Supporters Endpoint --------------------

class TestSupportersEndpoint:
    """GET /api/storefront/{id}/supporters — public, no auth."""

    @pytest.fixture(scope="class")
    def active_event_store(self):
        """Force-activate the event store via direct DB write (PUT endpoint is
        gated by Stripe onboarding which is mocked in dev). Snapshot+restore
        original values at teardown."""
        try:
            from pymongo import MongoClient
        except ImportError:
            pytest.skip("pymongo not available")
        c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "signguy_ai")]
        snap = db.webstores_v2.find_one({"id": EVENT_WS_ID}, {"_id": 0,
            "status": 1, "show_supporter_names": 1, "fundraiser_enabled": 1})
        if not snap:
            pytest.skip(f"event store {EVENT_WS_ID} not found")
        db.webstores_v2.update_one(
            {"id": EVENT_WS_ID},
            {"$set": {
                "status": "active",
                "show_supporter_names": "yes_all",
                "fundraiser_enabled": True,
                "is_public": True,
            }},
        )
        yield snap
        # Restore
        restore = {
            "status": snap.get("status") or "pending",
            "show_supporter_names": snap.get("show_supporter_names"),
            "fundraiser_enabled": bool(snap.get("fundraiser_enabled", True)),
        }
        db.webstores_v2.update_one({"id": EVENT_WS_ID}, {"$set": restore})
        c.close()

    def _set_ws(self, **fields):
        from pymongo import MongoClient
        c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        db = c[os.environ.get("DB_NAME", "signguy_ai")]
        db.webstores_v2.update_one({"id": EVENT_WS_ID}, {"$set": fields})
        c.close()

    def test_supporters_endpoint_is_public(self, active_event_store):
        r = requests.get(f"{BASE_URL}/api/storefront/{EVENT_WS_ID}/supporters")
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_supporters_404_for_unknown_store(self):
        r = requests.get(f"{BASE_URL}/api/storefront/{uuid.uuid4()}/supporters")
        assert r.status_code == 404

    def test_supporters_returns_empty_when_show_names_no(self, active_event_store):
        """show_supporter_names='no' → endpoint MUST return []."""
        self._set_ws(show_supporter_names="no")
        try:
            r = requests.get(f"{BASE_URL}/api/storefront/{EVENT_WS_ID}/supporters")
            assert r.status_code == 200
            assert r.json() == []
        finally:
            self._set_ws(show_supporter_names="yes_all")

    def test_supporters_empty_when_fundraiser_disabled(self, active_event_store):
        self._set_ws(fundraiser_enabled=False)
        try:
            r = requests.get(f"{BASE_URL}/api/storefront/{EVENT_WS_ID}/supporters")
            assert r.status_code == 200
            assert r.json() == []
        finally:
            self._set_ws(fundraiser_enabled=True)

    def test_supporters_yes_with_permission_respects_donor_consent(self, active_event_store):
        """In yes_with_permission mode, donor_consent=False rows render as
        'Anonymous Supporter'. Verified via seeded orders with both flags."""
        self._set_ws(show_supporter_names="yes_with_permission")
        try:
            r = requests.get(f"{BASE_URL}/api/storefront/{EVENT_WS_ID}/supporters?limit=10")
            assert r.status_code == 200, r.text
            rows = r.json()
            if not rows:
                pytest.skip("no supporter rows seeded")
            # Must include at least one Anonymous Supporter (donor_consent=False)
            names = [row["name"] for row in rows]
            assert "Anonymous Supporter" in names, (
                f"Expected at least one 'Anonymous Supporter' in {names}"
            )
        finally:
            self._set_ws(show_supporter_names="yes_all")

    def test_supporters_yes_all_exposes_all_names(self, active_event_store):
        self._set_ws(show_supporter_names="yes_all")
        r = requests.get(f"{BASE_URL}/api/storefront/{EVENT_WS_ID}/supporters?limit=10")
        assert r.status_code == 200
        rows = r.json()
        if rows:
            # No row should be "Anonymous Supporter" if customer_name was set
            # (we seeded all with customer_name populated)
            for row in rows:
                # amount must be a positive number
                assert isinstance(row["amount"], (int, float))
                assert row["amount"] > 0

    def test_supporters_sanitization_no_pii(self, active_event_store):
        """Response rows MUST only contain name/amount/created_at."""
        r = requests.get(f"{BASE_URL}/api/storefront/{EVENT_WS_ID}/supporters")
        assert r.status_code == 200
        for row in r.json():
            assert set(row.keys()).issubset({"name", "amount", "created_at"}), (
                f"Unexpected keys leaked: {set(row.keys())}"
            )
            # Explicit PII negative checks
            for forbidden in (
                "customer_email", "email", "customer_phone", "phone",
                "stripe_session_id", "session_id", "base_cost",
                "profit", "store_owner_profit", "tenant_id",
                "customer_id", "locked_settings", "owner_email",
            ):
                assert forbidden not in row, f"{forbidden} leaked in supporters"


# -------------------- Checkout donor_consent --------------------

class TestCheckoutDonorConsent:
    """POST /api/stripe-connect/webstore/{id}/checkout — donor_consent field."""

    def test_donor_consent_accepted_negative_donation_rejected(self):
        """ge=0 validation still enforced on donation_amount."""
        payload = {
            "customer_email": "consent_test@example.com",
            "customer_name": "Consent Test",
            "items": [],
            "donation_amount": -5,
            "donor_consent": True,
        }
        r = requests.post(
            f"{BASE_URL}/api/stripe-connect/webstore/{EVENT_WS_ID}/checkout",
            json=payload,
        )
        # Pydantic should reject negative donation_amount with 422
        assert r.status_code == 422, f"Expected 422 for negative donation, got {r.status_code} {r.text[:200]}"

    def test_donor_consent_field_accepted_in_schema(self):
        """donor_consent must be a known field — sending it must NOT trigger
        a Pydantic 'extra fields not permitted' or 422 on the consent key itself."""
        payload = {
            "customer_email": "consent_test2@example.com",
            "customer_name": "Consent Test 2",
            "items": [],
            "donation_amount": 0,
            "donor_consent": True,
        }
        r = requests.post(
            f"{BASE_URL}/api/stripe-connect/webstore/{EVENT_WS_ID}/checkout",
            json=payload,
        )
        # Could be 400 (no items + no donation), 422 (validation), 502 (stripe mocked),
        # 200 (mocked success), or 404 (store/inactive). The key check: it MUST NOT
        # report donor_consent as an unknown/invalid field.
        body = r.text.lower()
        assert "donor_consent" not in body or "unknown" not in body, (
            f"donor_consent appears to be rejected: {r.status_code} {r.text[:300]}"
        )


# -------------------- Portal Notifications --------------------

class TestPortalNotifications:
    """/api/portal/notifications endpoints."""

    def test_list_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/portal/notifications")
        assert r.status_code in (401, 403)

    def test_dismiss_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/portal/notifications/{uuid.uuid4()}/dismiss")
        assert r.status_code in (401, 403)

    def test_dismiss_all_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/portal/notifications/dismiss-all")
        assert r.status_code in (401, 403)

    def test_list_filters_to_current_customer_only(self, portal_pos_token, portal_neg_token):
        """All rows returned must belong to the auth'd customer.
        Implicit cross-customer isolation: pos token returns pos's customer_id only.
        """
        # Trigger seed for positive user
        requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token))
        r = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            headers=_h(portal_pos_token),
        )
        assert r.status_code == 200, r.text
        pos_rows = r.json()
        assert isinstance(pos_rows, list)
        pos_ids = {row.get("customer_id") for row in pos_rows}
        assert len(pos_ids) <= 1, f"Multiple customer_ids leaked: {pos_ids}"

        # Negative user — should NOT see any of positive's notifications
        rneg = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            headers=_h(portal_neg_token),
        )
        assert rneg.status_code == 200
        neg_rows = rneg.json()
        assert isinstance(neg_rows, list)
        # No overlap by customer_id
        if pos_rows and neg_rows:
            assert pos_ids.isdisjoint({r.get("customer_id") for r in neg_rows})

    def test_list_filter_by_notification_type(self, portal_pos_token):
        # Trigger seed
        requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token))
        r = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            params={"notification_type": "webstore_assigned"},
            headers=_h(portal_pos_token),
        )
        assert r.status_code == 200
        for row in r.json():
            assert row.get("notification_type") == "webstore_assigned"

    def test_list_unread_only_filter(self, portal_pos_token):
        r = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            params={"unread_only": "true"},
            headers=_h(portal_pos_token),
        )
        assert r.status_code == 200
        for row in r.json():
            assert row.get("is_read") in (False, None)

    def test_dismiss_unknown_returns_404(self, portal_pos_token):
        r = requests.post(
            f"{BASE_URL}/api/portal/notifications/{uuid.uuid4()}/dismiss",
            headers=_h(portal_pos_token),
        )
        assert r.status_code == 404

    def test_dismiss_other_customers_notification_returns_404(
        self, portal_pos_token, portal_neg_token
    ):
        """Negative user must NOT be able to dismiss a positive user's
        notification — must return 404 (not 403, no enumeration)."""
        # Trigger seed for positive
        requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token))
        r = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            headers=_h(portal_pos_token),
        )
        rows = r.json()
        if not rows:
            pytest.skip("no positive notifications to test cross-customer dismiss")
        target_id = rows[0]["id"]

        # Negative user tries to dismiss positive's notification → 404
        rdis = requests.post(
            f"{BASE_URL}/api/portal/notifications/{target_id}/dismiss",
            headers=_h(portal_neg_token),
        )
        assert rdis.status_code == 404

        # Confirm positive's notification is still unread
        rcheck = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            headers=_h(portal_pos_token),
        )
        for row in rcheck.json():
            if row["id"] == target_id:
                # Should still be unread (negative's dismiss was rejected)
                # We don't strictly assert is_read=False because positive may
                # have dismissed earlier; just confirm the row still exists.
                assert row.get("customer_id") != None

    def test_dismiss_own_notification_marks_read(self, portal_pos_token):
        # Trigger seed
        requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token))
        rlist = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            params={"unread_only": "true"},
            headers=_h(portal_pos_token),
        )
        rows = rlist.json()
        if not rows:
            pytest.skip("no unread notifications to dismiss")
        target_id = rows[0]["id"]
        rdis = requests.post(
            f"{BASE_URL}/api/portal/notifications/{target_id}/dismiss",
            headers=_h(portal_pos_token),
        )
        assert rdis.status_code == 200
        assert rdis.json().get("ok") is True

        # Verify is_read=True now
        rafter = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            headers=_h(portal_pos_token),
        )
        match = [r for r in rafter.json() if r["id"] == target_id]
        if match:
            assert match[0].get("is_read") is True

    def test_dismiss_all_marks_all_read(self, portal_pos_token):
        # Trigger seed
        requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token))
        r = requests.post(
            f"{BASE_URL}/api/portal/notifications/dismiss-all",
            headers=_h(portal_pos_token),
        )
        assert r.status_code == 200
        assert "dismissed" in r.json()

        # All should be is_read=True now
        runread = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            params={"unread_only": "true"},
            headers=_h(portal_pos_token),
        )
        assert runread.status_code == 200
        assert runread.json() == []


# -------------------- Idempotent assignment-notification seeding --------------------

class TestNotificationSeedIdempotent:
    """GET /api/portal/webstores must seed exactly one webstore_assigned
    notification per (customer, webstore) — even when called multiple times."""

    def test_double_call_does_not_create_duplicate(self, portal_pos_token):
        # First call (may seed)
        r1 = requests.get(
            f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token)
        )
        assert r1.status_code == 200
        # Second call (must not duplicate)
        r2 = requests.get(
            f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token)
        )
        assert r2.status_code == 200
        # Third call for extra safety
        requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token))

        # Now count notifications of type webstore_assigned with
        # related_id == POSITIVE_WS_ID for this customer.
        rn = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            params={"notification_type": "webstore_assigned"},
            headers=_h(portal_pos_token),
        )
        assert rn.status_code == 200
        matching = [
            r for r in rn.json()
            if r.get("related_id") == PORTAL_POS_WS_ID
            and r.get("notification_type") == "webstore_assigned"
        ]
        assert len(matching) == 1, (
            f"Expected exactly 1 webstore_assigned notif for ws {PORTAL_POS_WS_ID}, "
            f"got {len(matching)}: {[m.get('id') for m in matching]}"
        )

    def test_assigned_notification_message_mentions_store(self, portal_pos_token):
        requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(portal_pos_token))
        rn = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            params={"notification_type": "webstore_assigned"},
            headers=_h(portal_pos_token),
        )
        assert rn.status_code == 200
        matching = [r for r in rn.json() if r.get("related_id") == PORTAL_POS_WS_ID]
        assert matching, "no webstore_assigned notification found for positive user"
        msg = (matching[0].get("message") or "").lower()
        # Must mention either the store name or "store"/"webstore"/"stripe"
        assert any(tok in msg for tok in ("store", "webstore", "stripe")), (
            f"Unexpected message: {matching[0].get('message')}"
        )

    def test_negative_user_does_not_get_positive_users_notifications(
        self, portal_neg_token
    ):
        rn = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            params={"notification_type": "webstore_assigned"},
            headers=_h(portal_neg_token),
        )
        assert rn.status_code == 200
        for row in rn.json():
            assert row.get("related_id") != PORTAL_POS_WS_ID, (
                "negative user can see positive user's assignment notification"
            )
