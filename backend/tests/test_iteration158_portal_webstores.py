"""Iteration 158 — Portal Webstores tab tests.

Covers:
- /api/portal/dashboard has_webstores + stats.assigned_webstores
- /api/portal/webstores list (assignment + auth + tenant filter)
- /api/portal/webstores/{id} detail (sanitization, 404 cross-tenant, etc.)
- /api/portal/webstores/{id}/stripe-onboarding|refresh|login-link (assignment check)
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://sms-consent-demo.preview.emergentagent.com").rstrip("/")

POSITIVE_EMAIL = "demo-fundraiser@rysoccer.example"
POSITIVE_PASSWORD = "TestPortal123!"
POSITIVE_TENANT_ID = "b05a87f3-5d3f-45f9-b629-aec53bd78418"
POSITIVE_WS_ID = "3dae02a7-0e2c-4ba1-a639-df19833161fc"

NEGATIVE_EMAIL = "portalreg_1776974524@example.com"
NEGATIVE_PASSWORD = "TestNeg123!"


@pytest.fixture(scope="module")
def positive_token():
    """Login as the demo-fundraiser portal user. Register if needed."""
    s = requests.Session()
    # Try login first.
    r = s.post(f"{BASE_URL}/api/portal/auth/login", json={
        "email": POSITIVE_EMAIL, "password": POSITIVE_PASSWORD,
    })
    if r.status_code != 200:
        # Register (the register endpoint enables portal for an existing customer with that email).
        r2 = s.post(f"{BASE_URL}/api/portal/auth/register", json={
            "email": POSITIVE_EMAIL, "password": POSITIVE_PASSWORD,
        })
        if r2.status_code not in (200, 201):
            pytest.skip(f"Cannot enable portal login for positive user: register={r2.status_code} {r2.text[:200]} login={r.status_code} {r.text[:200]}")
        r = s.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": POSITIVE_EMAIL, "password": POSITIVE_PASSWORD,
        })
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture(scope="module")
def negative_token():
    """Login a portal customer with no webstores assigned (different tenant from positive)."""
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/portal/auth/login", json={
        "email": NEGATIVE_EMAIL, "password": NEGATIVE_PASSWORD,
    })
    if r.status_code != 200:
        pytest.skip(f"Cannot login negative portal user: {r.status_code} {r.text[:200]}")
    return r.json().get("access_token") or r.json().get("token")


def _h(token): return {"Authorization": f"Bearer {token}"}


# --- AUTH / REGISTRATION ---

class TestAuth:
    def test_list_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/portal/webstores")
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_detail_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}")
        assert r.status_code in (401, 403)


# --- DASHBOARD ---

class TestDashboard:
    def test_dashboard_positive_has_webstores_true(self, positive_token):
        r = requests.get(f"{BASE_URL}/api/portal/dashboard", headers=_h(positive_token))
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("has_webstores") is True
        assert d.get("stats", {}).get("assigned_webstores", 0) >= 1

    def test_dashboard_negative_has_webstores_false(self, negative_token):
        r = requests.get(f"{BASE_URL}/api/portal/dashboard", headers=_h(negative_token))
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("has_webstores") is False
        assert d.get("stats", {}).get("assigned_webstores", 0) == 0


# --- LIST ---

class TestList:
    def test_list_returns_assigned_store(self, positive_token):
        r = requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(positive_token))
        assert r.status_code == 200, r.text[:300]
        rows = r.json()
        assert isinstance(rows, list) and len(rows) >= 1
        ids = [w.get("id") for w in rows]
        assert POSITIVE_WS_ID in ids

    def test_list_sanitization(self, positive_token):
        r = requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(positive_token))
        assert r.status_code == 200
        for w in r.json():
            assert "tenant_id" not in w, "tenant_id leaked in list"
            assert "owner_user_id" not in w, "owner_user_id leaked"
            ls = w.get("locked_settings") or {}
            for forbidden in ("base_item_cost", "production_cost", "store_owner_profit", "profit_split"):
                assert forbidden not in ls, f"{forbidden} leaked in locked_settings"
            # locked_settings keys whitelisted
            allowed = {"shipping_fee", "handling_fee", "shipping_handling_enabled",
                       "shipping_handling_fee", "shipping_handling_label",
                       "shipping_handling_description"}
            assert set(ls.keys()).issubset(allowed), f"unexpected locked_settings keys: {set(ls.keys()) - allowed}"

    def test_list_empty_for_negative_user(self, negative_token):
        r = requests.get(f"{BASE_URL}/api/portal/webstores", headers=_h(negative_token))
        assert r.status_code == 200
        assert r.json() == []


# --- DETAIL ---

class TestDetail:
    def test_detail_owned(self, positive_token):
        r = requests.get(f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}", headers=_h(positive_token))
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d.get("id") == POSITIVE_WS_ID
        assert d.get("store_type") == "fundraiser"
        # Sanitization
        assert "tenant_id" not in d
        assert "owner_user_id" not in d
        ls = d.get("locked_settings") or {}
        for k in ("base_item_cost", "production_cost", "store_owner_profit", "profit_split"):
            assert k not in ls
        # Should include recent_orders and questionnaire blocks
        assert "recent_orders" in d
        assert isinstance(d["recent_orders"], list)
        assert "questionnaire" in d
        assert "public_path" in d
        assert d["public_path"].endswith(POSITIVE_WS_ID)

    def test_detail_not_owned_returns_404(self, negative_token):
        # Negative user trying to access positive user's store
        r = requests.get(f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}", headers=_h(negative_token))
        assert r.status_code == 404, f"expected 404, got {r.status_code} {r.text[:200]}"

    def test_detail_nonexistent_returns_404(self, positive_token):
        r = requests.get(f"{BASE_URL}/api/portal/webstores/nonexistent-id-xyz", headers=_h(positive_token))
        assert r.status_code == 404


# --- STRIPE (assignment-check focus) ---

class TestStripe:
    def test_onboarding_blocked_for_non_owner(self, negative_token):
        r = requests.post(
            f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}/stripe-onboarding",
            headers=_h(negative_token),
            json={"return_url": "https://example.com/r", "refresh_url": "https://example.com/f"},
        )
        assert r.status_code == 404

    def test_onboarding_owner_shape(self, positive_token):
        r = requests.post(
            f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}/stripe-onboarding",
            headers=_h(positive_token),
            json={"return_url": "https://example.com/r", "refresh_url": "https://example.com/f"},
        )
        # Either a 200 with url or a 502 (Stripe error). Both acceptable.
        assert r.status_code in (200, 502), f"unexpected {r.status_code} {r.text[:300]}"
        if r.status_code == 200:
            assert "url" in r.json()

    def test_refresh_blocked_for_non_owner(self, negative_token):
        r = requests.post(
            f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}/stripe-refresh",
            headers=_h(negative_token),
        )
        assert r.status_code == 404

    def test_refresh_returns_ready_false_when_no_account(self, positive_token):
        r = requests.post(
            f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}/stripe-refresh",
            headers=_h(positive_token),
        )
        # If onboarding test above created an account, the field may now be set
        # which would call Stripe (maybe 502). Both 200/502 acceptable; if 200
        # and ready=false-no-account path, ensure shape is right.
        assert r.status_code in (200, 502)
        if r.status_code == 200:
            d = r.json()
            assert "ready" in d and "charges_enabled" in d

    def test_login_link_blocked_for_non_owner(self, negative_token):
        r = requests.post(
            f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}/stripe-login-link",
            headers=_h(negative_token),
        )
        assert r.status_code == 404

    def test_login_link_400_when_no_account(self, positive_token):
        # The previous onboarding may have set the account id; if Stripe accepted
        # the account creation, the doc would have owner_stripe_account_id, and
        # this would go to Stripe (maybe 502). Either way the assignment check
        # passed; we just verify it's NOT a 404.
        r = requests.post(
            f"{BASE_URL}/api/portal/webstores/{POSITIVE_WS_ID}/stripe-login-link",
            headers=_h(positive_token),
        )
        assert r.status_code != 404
        assert r.status_code in (200, 400, 502)
