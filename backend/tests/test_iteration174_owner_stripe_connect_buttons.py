"""Iteration 174 — Webstore Owner Stripe Connect Buttons

Tests the two backend endpoints consumed by WebstoreOwnerConnectCard.js:
  GET  /api/webstore-owners/{id}/owner-status  → returns owner Stripe status dict
  POST /api/webstore-owners/{id}/invite/quick  → sends invite (or 502 if email fails)

Uses the known test store: fc0bad7e-9040-477e-93b9-a3f0b1a2df90 (Preview Storefront QA)
which has no Stripe account connected.
"""
import os
import pytest
import requests

from dotenv import load_dotenv
load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

BASE = (os.environ.get("REACT_APP_BACKEND_URL") or "").rstrip("/")

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASS = "password123"

# Known test store with no Stripe account
TEST_STORE_ID = "fc0bad7e-9040-477e-93b9-a3f0b1a2df90"


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(
        f"{BASE}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=30,
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text}")
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ── owner-status endpoint ──────────────────────────────────────────────────────

class TestOwnerStatus:
    """GET /api/webstore-owners/{id}/owner-status"""

    def test_owner_status_returns_200(self, admin_headers):
        """Endpoint must return 200 for a valid webstore owned by the tenant."""
        r = requests.get(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/owner-status",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_owner_status_response_has_required_fields(self, admin_headers):
        """Response must contain all fields expected by the frontend component."""
        r = requests.get(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/owner-status",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        # These are the exact fields read by WebstoreOwnerConnectCard.js
        for field in ["owner_stripe_account_id", "charges_enabled", "payouts_enabled",
                      "details_submitted", "portal_enabled", "ready_to_activate"]:
            assert field in body, f"Missing field '{field}' in response: {body}"

    def test_owner_status_not_connected_for_test_store(self, admin_headers):
        """Test store has no Stripe account — charges_enabled should be False."""
        r = requests.get(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/owner-status",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        # Test store has no Stripe → these must be False/None
        assert body["charges_enabled"] is False, \
            f"Expected charges_enabled=False for unconnected store, got: {body}"
        assert body["ready_to_activate"] is False, \
            f"Expected ready_to_activate=False, got: {body}"
        # owner_stripe_account_id should be None or empty string
        assert not body["owner_stripe_account_id"], \
            f"Expected no stripe account id, got: {body['owner_stripe_account_id']}"

    def test_owner_status_bool_types(self, admin_headers):
        """All flag fields must be proper booleans (not None or missing)."""
        r = requests.get(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/owner-status",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        for bool_field in ["charges_enabled", "payouts_enabled", "details_submitted",
                           "portal_enabled", "ready_to_activate"]:
            assert isinstance(body[bool_field], bool), \
                f"Field '{bool_field}' is {type(body[bool_field])}, expected bool"

    def test_owner_status_unauthenticated_returns_401(self):
        """No auth header → 401 or 403."""
        r = requests.get(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/owner-status",
            timeout=15,
        )
        assert r.status_code in (401, 403), \
            f"Expected 401/403 without auth, got {r.status_code}"

    def test_owner_status_unknown_store_returns_404(self, admin_headers):
        """Non-existent webstore_id → 404."""
        r = requests.get(
            f"{BASE}/api/webstore-owners/nonexistent-store-000/owner-status",
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 404, \
            f"Expected 404 for unknown store, got {r.status_code}: {r.text}"


# ── invite/quick endpoint ──────────────────────────────────────────────────────

class TestOwnerInviteQuick:
    """POST /api/webstore-owners/{id}/invite/quick"""

    def test_invite_unauthenticated_returns_401(self):
        """No auth header → 401 or 403."""
        r = requests.post(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/invite/quick",
            json={"email": "owner@example.com"},
            timeout=15,
        )
        assert r.status_code in (401, 403), \
            f"Expected 401/403 without auth, got {r.status_code}"

    def test_invite_invalid_email_returns_422(self, admin_headers):
        """Malformed email → Pydantic validation error → 422."""
        r = requests.post(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/invite/quick",
            json={"email": "not-an-email"},
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 422, \
            f"Expected 422 for invalid email, got {r.status_code}: {r.text}"

    def test_invite_unknown_store_returns_404(self, admin_headers):
        """Non-existent webstore → 404."""
        r = requests.post(
            f"{BASE}/api/webstore-owners/nonexistent-store-000/invite/quick",
            json={"email": "owner@example.com"},
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 404, \
            f"Expected 404 for unknown store, got {r.status_code}: {r.text}"

    def test_invite_response_shape_or_clear_error(self, admin_headers):
        """
        When invite is sent, the backend should either:
        a) Return 200 with {success, invite_url, expires_at, message}  (SendGrid configured)
        b) Return 502 with {detail: "..."} when email delivery fails (SendGrid misconfigured)

        Either way — NOT a silent 200 with empty body, NOT a 500 crash.
        This validates the frontend can show either success toast or clear error toast.
        """
        r = requests.post(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/invite/quick",
            json={
                "email": "TEST_owner_invite@example.com",
                "public_url": "https://sign-shop-checkout.preview.emergentagent.com",
            },
            headers=admin_headers,
            timeout=30,
        )
        # Must be 200 (success) or 502 (email failed) — never 500 crash
        assert r.status_code in (200, 502), \
            f"Expected 200 or 502, got {r.status_code}: {r.text}"

        if r.status_code == 200:
            body = r.json()
            assert body.get("success") is True
            assert "invite_url" in body
            assert "expires_at" in body
            assert "message" in body
            print(f"✅ Invite succeeded — invite_url: {body['invite_url']}")
        else:
            # 502 = email delivery failed (SendGrid not configured)
            body = r.json()
            assert "detail" in body, f"502 response missing 'detail': {body}"
            assert body["detail"], "detail must not be empty"
            print(f"✅ Expected 502 (SendGrid not configured) — detail: {body['detail']}")

    def test_invite_missing_email_returns_422(self, admin_headers):
        """Entirely missing email field → 422."""
        r = requests.post(
            f"{BASE}/api/webstore-owners/{TEST_STORE_ID}/invite/quick",
            json={"name": "Test Owner"},  # email missing
            headers=admin_headers,
            timeout=15,
        )
        assert r.status_code == 422, \
            f"Expected 422 for missing email, got {r.status_code}: {r.text}"
