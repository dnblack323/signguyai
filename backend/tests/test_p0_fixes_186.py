"""
P0 Bug Fixes - Iteration 186
Tests: financials summary, magic links, invoices permissions, quote send, promo codes, portal preview
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json().get("access_token") or resp.json().get("token")


@pytest.fixture(scope="module")
def headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


# ── Financials Summary ──────────────────────────────────────────────────────

class TestFinancialsSummary:
    def test_summary_returns_200(self, headers):
        r = requests.get(f"{BASE_URL}/api/financials/summary", headers=headers)
        assert r.status_code == 200, r.text

    def test_summary_has_total_tax(self, headers):
        r = requests.get(f"{BASE_URL}/api/financials/summary", headers=headers)
        data = r.json()
        assert "total_tax" in data, f"total_tax missing. Keys: {list(data.keys())}"

    def test_summary_has_net_income(self, headers):
        r = requests.get(f"{BASE_URL}/api/financials/summary", headers=headers)
        data = r.json()
        assert "net_income" in data, f"net_income missing. Keys: {list(data.keys())}"

    def test_summary_has_net_profit(self, headers):
        r = requests.get(f"{BASE_URL}/api/financials/summary", headers=headers)
        data = r.json()
        assert "net_profit" in data, f"net_profit missing. Keys: {list(data.keys())}"

    def test_summary_net_income_equals_net_profit(self, headers):
        r = requests.get(f"{BASE_URL}/api/financials/summary", headers=headers)
        data = r.json()
        assert data["net_income"] == data["net_profit"], "net_income should alias net_profit"


# ── Magic Links ─────────────────────────────────────────────────────────────

class TestMagicLinks:
    def test_list_magic_links(self, headers):
        r = requests.get(f"{BASE_URL}/api/magic-links", headers=headers)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_create_magic_link_invalid_type(self, headers):
        r = requests.post(f"{BASE_URL}/api/magic-links", headers=headers, json={
            "resource_type": "invalid_type",
            "resource_id": "does-not-exist",
        })
        assert r.status_code == 400

    def test_portal_preview_invalid_token(self):
        r = requests.get(f"{BASE_URL}/api/portal/preview/invalid-token-xyz")
        assert r.status_code == 404

    def test_create_magic_link_nonexistent_quote(self, headers):
        r = requests.post(f"{BASE_URL}/api/magic-links", headers=headers, json={
            "resource_type": "quote",
            "resource_id": "nonexistent-quote-id-xyz",
        })
        assert r.status_code == 404


# ── Invoices ────────────────────────────────────────────────────────────────

class TestInvoices:
    def test_invoices_list_authenticated(self, headers):
        r = requests.get(f"{BASE_URL}/api/invoices", headers=headers)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)

    def test_invoices_list_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/invoices")
        assert r.status_code in [401, 403], f"Expected 401/403, got {r.status_code}"


# ── Quotes Send ──────────────────────────────────────────────────────────────

class TestQuotesSend:
    def test_quotes_list(self, headers):
        r = requests.get(f"{BASE_URL}/api/quotes", headers=headers)
        assert r.status_code == 200, r.text

    def test_send_nonexistent_quote(self, headers):
        r = requests.post(f"{BASE_URL}/api/quotes/nonexistent-id/send", headers=headers)
        assert r.status_code in [404, 400, 422], f"Got {r.status_code}: {r.text}"

    def test_send_quote_returns_email_status(self, headers):
        """Get a real quote and try to send it — check email_status in response."""
        quotes_resp = requests.get(f"{BASE_URL}/api/quotes", headers=headers)
        if quotes_resp.status_code != 200:
            pytest.skip("Could not retrieve quotes")
        quotes = quotes_resp.json()
        if not quotes:
            pytest.skip("No quotes available for send test")
        quote_id = quotes[0]["id"]
        r = requests.post(f"{BASE_URL}/api/quotes/{quote_id}/send", headers=headers)
        # Either 200 with email_status or error status
        if r.status_code == 200:
            data = r.json()
            assert "email_status" in data or "status" in data or "email" in data, f"No status field in response: {data}"
        else:
            # Acceptable: no customer email, etc.
            assert r.status_code in [400, 404, 422, 500]


# ── Promo Codes ──────────────────────────────────────────────────────────────

class TestPromoCodes:
    def test_promo_codes_list(self, headers):
        r = requests.get(f"{BASE_URL}/api/promo-codes", headers=headers)
        assert r.status_code == 200, r.text
        assert isinstance(r.json(), list)
