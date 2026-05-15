"""Iteration 140 — End-to-end API contract tests for the Webstore Owner Connect flow.

Covers:
- /api/stripe-connect/fee-preview (invoice + webstore math)
- /api/webstore-owners/{id}/invite/quick + /invite/portal  (tenant auth)
- /api/webstore-owners/{id}/owner-status
- /api/owner-onboard/{token} + /start-stripe + /refresh + /login-link  (public)
- /api/owner-portal/signup + /me + /stores/{id}/transfers + /stores/{id}/stripe-login-link
- Webstore activation gate (PUT /api/webstores/v2/{id} status=active)
- Cross-tenant 404 + expired/unknown token 404/410
- Cleanup of all TEST_ data created
"""
import os
import uuid
import pytest
import requests
from datetime import datetime, timezone, timedelta
from pymongo import MongoClient

# Load env from backend/.env if not already set
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

BASE = (os.environ.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASS = "password123"

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "signguy_ai")

_sync_client = MongoClient(MONGO_URL)
_db = _sync_client[DB_NAME]


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
                      timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_tenant_id(admin_headers):
    r = requests.get(f"{BASE}/api/users/me", headers=admin_headers, timeout=15)
    assert r.status_code == 200, r.text
    return r.json().get("tenant_id")


@pytest.fixture(scope="module")
def test_webstore(admin_headers, admin_tenant_id):
    """Create a temporary webstore for the run; cleaned up at module teardown."""
    payload = {
        "name": f"TEST_OwnerConnect_{uuid.uuid4().hex[:6]}",
        "store_type": "fundraiser",
        "owner_name": "TEST Owner",
        "owner_email": f"TEST_owner_{uuid.uuid4().hex[:6]}@example.com",
    }
    r = requests.post(f"{BASE}/api/webstores/v2", json=payload, headers=admin_headers, timeout=30)
    assert r.status_code in (200, 201), f"create webstore failed: {r.status_code} {r.text}"
    ws = r.json()
    yield ws

    # teardown: hard-delete from mongo (tests created the data)
    _db.webstores_v2.delete_one({"id": ws["id"]})
    _db.webstore_owner_invites.delete_many({"webstore_id": ws["id"]})


# ── Fee preview ───────────────────────────────────────────────────────────────

class TestFeePreview:
    def test_invoice_5_dollar(self, admin_headers):
        r = requests.get(f"{BASE}/api/stripe-connect/fee-preview",
                         params={"amount": 5, "is_webstore": False},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["platform_fee_cents"] == 31

    def test_invoice_100_dollar(self, admin_headers):
        r = requests.get(f"{BASE}/api/stripe-connect/fee-preview",
                         params={"amount": 100, "is_webstore": "false"},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["platform_fee_cents"] == 240

    def test_webstore_50_dollar(self, admin_headers):
        r = requests.get(f"{BASE}/api/stripe-connect/fee-preview",
                         params={"amount": 50, "is_webstore": "true"},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["platform_fee_cents"] == 230

    def test_webstore_500_dollar(self, admin_headers):
        r = requests.get(f"{BASE}/api/stripe-connect/fee-preview",
                         params={"amount": 500, "is_webstore": True},
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["platform_fee_cents"] == 2120
        # also sanity: tenant_receives < amount and includes a stripe estimate
        assert body.get("tenant_receives_cents") is not None
        assert body["tenant_receives_cents"] < 50000


# ── Invite endpoints (tenant auth) ────────────────────────────────────────────

class TestOwnerInvites:
    def test_quick_invite_creates_token(self, admin_headers, test_webstore):
        payload = {
            "email": f"TEST_quick_{uuid.uuid4().hex[:6]}@example.com",
            "name": "Quick Test",
            "public_url": "https://example.com",
        }
        r = requests.post(
            f"{BASE}/api/webstore-owners/{test_webstore['id']}/invite/quick",
            json=payload, headers=admin_headers, timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert "/webstore-owner/onboard/" in body["invite_url"]
        assert body["expires_at"]
        # store token for next tests
        pytest.QUICK_TOKEN = body["invite_url"].rsplit("/", 1)[-1]

    def test_portal_invite_creates_portal_token(self, admin_headers, test_webstore):
        payload = {
            "email": f"TEST_portal_{uuid.uuid4().hex[:6]}@example.com",
            "name": "Portal Test",
            "public_url": "https://example.com",
        }
        r = requests.post(
            f"{BASE}/api/webstore-owners/{test_webstore['id']}/invite/portal",
            json=payload, headers=admin_headers, timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "/owner-portal-signup/" in body["invite_url"]
        pytest.PORTAL_TOKEN = body["invite_url"].rsplit("/", 1)[-1]
        pytest.PORTAL_EMAIL = payload["email"]

    def test_cross_tenant_invite_returns_404(self, admin_headers):
        bogus_id = str(uuid.uuid4())
        r = requests.post(
            f"{BASE}/api/webstore-owners/{bogus_id}/invite/quick",
            json={"email": "x@y.com"}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 404

    def test_owner_status_endpoint(self, admin_headers, test_webstore):
        r = requests.get(
            f"{BASE}/api/webstore-owners/{test_webstore['id']}/owner-status",
            headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "ready_to_activate" in body
        assert body["ready_to_activate"] is False  # nothing connected yet
        assert body["charges_enabled"] is False


# ── Public token endpoints ────────────────────────────────────────────────────

class TestPublicOnboardEndpoints:
    def test_get_context_with_valid_token(self):
        token = getattr(pytest, "QUICK_TOKEN", None)
        if not token:
            pytest.skip("no quick token from prior test")
        r = requests.get(f"{BASE}/api/owner-onboard/{token}", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["webstore_id"]
        assert body["portal_invite"] is False
        assert body["charges_enabled"] is False

    def test_get_context_unknown_token_404(self):
        r = requests.get(f"{BASE}/api/owner-onboard/{uuid.uuid4().hex}", timeout=15)
        assert r.status_code == 404

    def test_portal_token_marks_portal_invite_true(self):
        token = getattr(pytest, "PORTAL_TOKEN", None)
        if not token:
            pytest.skip("no portal token")
        r = requests.get(f"{BASE}/api/owner-onboard/{token}", timeout=15)
        assert r.status_code == 200
        assert r.json()["portal_invite"] is True

    def test_login_link_before_stripe_connected_returns_400(self):
        token = getattr(pytest, "QUICK_TOKEN", None)
        if not token:
            pytest.skip()
        r = requests.post(f"{BASE}/api/owner-onboard/{token}/login-link", timeout=15)
        assert r.status_code == 400

    def test_expired_token_returns_410(self, admin_headers):
        # Insert a synthetic expired invite into mongo and confirm 410
        tok = uuid.uuid4().hex
        _db.webstore_owner_invites.insert_one({
            "token": tok,
            "webstore_id": "nonexistent",
            "tenant_id": "nonexistent",
            "owner_email": "TEST_expired@example.com",
            "owner_name": "Exp",
            "portal_invite": False,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        })
        try:
            r = requests.get(f"{BASE}/api/owner-onboard/{tok}", timeout=15)
            assert r.status_code == 410, f"Expected 410, got {r.status_code}: {r.text}"
        finally:
            _db.webstore_owner_invites.delete_one({"token": tok})


# ── Portal signup + authenticated endpoints ───────────────────────────────────

class TestPortalSignup:
    def test_signup_short_password_400(self):
        token = getattr(pytest, "PORTAL_TOKEN", None)
        if not token:
            pytest.skip()
        r = requests.post(f"{BASE}/api/owner-portal/signup",
                          json={"token": token, "password": "short", "full_name": "T"},
                          timeout=15)
        assert r.status_code == 400

    def test_signup_quick_token_rejected(self):
        token = getattr(pytest, "QUICK_TOKEN", None)
        if not token:
            pytest.skip()
        r = requests.post(f"{BASE}/api/owner-portal/signup",
                          json={"token": token, "password": "longenough123", "full_name": "T"},
                          timeout=15)
        assert r.status_code == 400  # quick-invite tokens cannot create portal account

    def test_signup_success_returns_jwt_and_me_works(self, test_webstore):
        token = getattr(pytest, "PORTAL_TOKEN", None)
        email = getattr(pytest, "PORTAL_EMAIL", None)
        if not token or not email:
            pytest.skip()
        r = requests.post(f"{BASE}/api/owner-portal/signup",
                          json={"token": token, "password": "ownerpass123", "full_name": "Owner Test"},
                          timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["access_token"]
        assert body["user_id"]
        pytest.OWNER_JWT = body["access_token"]
        pytest.OWNER_USER_ID = body["user_id"]

        # /me must list the linked store
        h = {"Authorization": f"Bearer {body['access_token']}"}
        rm = requests.get(f"{BASE}/api/owner-portal/me", headers=h, timeout=15)
        assert rm.status_code == 200, rm.text
        mb = rm.json()
        assert any(s["id"] == test_webstore["id"] for s in mb["stores"]), mb

    def test_admin_cannot_use_owner_portal(self, admin_headers):
        # Admin user has role != 'webstore_owner' — must be 403
        r = requests.get(f"{BASE}/api/owner-portal/me", headers=admin_headers, timeout=15)
        assert r.status_code == 403, r.text

    def test_transfers_endpoint(self, test_webstore):
        jwt = getattr(pytest, "OWNER_JWT", None)
        if not jwt:
            pytest.skip()
        h = {"Authorization": f"Bearer {jwt}"}
        r = requests.get(f"{BASE}/api/owner-portal/stores/{test_webstore['id']}/transfers",
                         headers=h, timeout=15)
        assert r.status_code == 200, r.text
        assert "transfers" in r.json()

    def test_stripe_login_link_blocked_when_not_connected(self, test_webstore):
        jwt = getattr(pytest, "OWNER_JWT", None)
        if not jwt:
            pytest.skip()
        h = {"Authorization": f"Bearer {jwt}"}
        r = requests.post(f"{BASE}/api/owner-portal/stores/{test_webstore['id']}/stripe-login-link",
                          headers=h, timeout=15)
        assert r.status_code == 400


# ── Webstore activation gate ──────────────────────────────────────────────────

class TestActivationGate:
    def test_cannot_activate_without_stripe_connected(self, admin_headers, test_webstore):
        r = requests.put(f"{BASE}/api/webstores/v2/{test_webstore['id']}",
                         json={"status": "active"}, headers=admin_headers, timeout=20)
        assert r.status_code == 400, r.text
        msg = (r.json().get("detail") or "").lower()
        assert "owner" in msg or "stripe" in msg or "onboard" in msg

    def test_activation_succeeds_after_seeding_connected_flags(self, admin_headers, test_webstore):
        # Seed connected flags directly via mongo to simulate completed Stripe onboarding
        _db.webstores_v2.update_one(
            {"id": test_webstore["id"]},
            {"$set": {
                "owner_stripe_account_id": "acct_test_seeded",
                "owner_stripe_charges_enabled": True,
                "owner_stripe_payouts_enabled": True,
                "owner_stripe_details_submitted": True,
            }},
        )

        r = requests.put(f"{BASE}/api/webstores/v2/{test_webstore['id']}",
                         json={"status": "active"}, headers=admin_headers, timeout=20)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "active"


# ── Module teardown for portal user we created ────────────────────────────────

def teardown_module(module):
    try:
        email = getattr(pytest, "PORTAL_EMAIL", None)
        if email:
            _db.users.delete_many({"email": email.lower()})
        _db.webstore_owner_invites.delete_many({"owner_email": {"$regex": "^TEST_"}})
    except Exception as exc:
        print(f"cleanup error: {exc}")
