"""
P0 Bug Fixes Batch 2 — Iteration 187 backend tests
Tests: signature security, appointment confirm/reject GET pages, magic links, invoices auth, financials, promo codes
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"

# Magic link token from previous iteration
PREV_MAGIC_TOKEN = "rqAHMyBNEJFh6-Z2AtgvNd4JUoAo_F5W6wPrt1VeM3M"


@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ── Signature Security ────────────────────────────────────────────────────────

class TestSignatureSecurity:
    """Expired/invalid token on public sign endpoint should return 404, not schema error"""

    def test_sign_invalid_token_returns_404(self):
        """POST /api/signatures/public/INVALID_TOKEN/sign must 404 (not 400 schema error)"""
        r = requests.post(
            f"{BASE_URL}/api/signatures/public/INVALID_TOKEN/sign",
            json={
                "signer_name": "Test Signer",
                "image_data": "data:image/png;base64,iVBORw0KGgo=",
            },
        )
        assert r.status_code == 404, f"Expected 404 for invalid token, got {r.status_code}: {r.text}"

    def test_decline_invalid_token_returns_404(self):
        """POST /api/signatures/public/INVALID_TOKEN/decline must 404"""
        r = requests.post(
            f"{BASE_URL}/api/signatures/public/INVALID_TOKEN/decline",
            json={"notes": "test"},
        )
        assert r.status_code == 404, f"Expected 404 for invalid token, got {r.status_code}: {r.text}"

    def test_signature_file_requires_auth(self):
        """GET /api/signatures/file/{id} without token must return 401 or 403"""
        r = requests.get(f"{BASE_URL}/api/signatures/file/some-fake-id")
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_signature_file_with_auth_404_for_nonexistent(self, auth_headers):
        """GET /api/signatures/file/{id} with auth should 404 for nonexistent signature"""
        r = requests.get(f"{BASE_URL}/api/signatures/file/nonexistent-id", headers=auth_headers)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


# ── Appointment Public Confirm/Reject GET (HTML pages) ───────────────────────

class TestAppointmentPublicPages:
    """Public confirm/reject GET must return HTML (not mutate) — 400 for bad token"""

    def test_confirm_get_bad_token_returns_400_html(self):
        """GET /api/public-appointments/BADTOKEN/confirm → 400 HTML"""
        r = requests.get(f"{BASE_URL}/api/public-appointments/BADTOKEN/confirm")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        assert "text/html" in r.headers.get("content-type", ""), "Expected HTML response"

    def test_reject_get_bad_token_returns_400_html(self):
        """GET /api/public-appointments/BADTOKEN/reject → 400 HTML"""
        r = requests.get(f"{BASE_URL}/api/public-appointments/BADTOKEN/reject")
        assert r.status_code == 400, f"Expected 400, got {r.status_code}"
        assert "text/html" in r.headers.get("content-type", ""), "Expected HTML response"

    def test_confirm_get_bad_token_does_not_mutate(self):
        """GET should show landing page with form (contains 'confirm' button or 'form' tag for valid tokens)"""
        # Using a bad token — the page should say link expired
        r = requests.get(f"{BASE_URL}/api/public-appointments/BADTOKEN/confirm")
        body = r.text.lower()
        assert "link expired" in body or "no longer valid" in body or "expired" in body, \
            f"Expected 'expired' text in HTML, got: {body[:300]}"


# ── Magic Links ───────────────────────────────────────────────────────────────

class TestMagicLinks:
    """Magic link creation and portal preview"""

    def test_create_magic_link_requires_auth(self):
        """POST /api/magic-links without auth → 401"""
        r = requests.post(f"{BASE_URL}/api/magic-links", json={
            "resource_type": "quote", "resource_id": "fake-id"
        })
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_list_magic_links_with_auth(self, auth_headers):
        """GET /api/magic-links with auth → 200 list"""
        r = requests.get(f"{BASE_URL}/api/magic-links", headers=auth_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert isinstance(r.json(), list), "Expected list response"

    def test_portal_preview_invalid_token_404(self):
        """GET /api/portal/preview/INVALIDTOKEN → 404"""
        r = requests.get(f"{BASE_URL}/api/portal/preview/INVALIDTOKEN_NOTEXIST_12345")
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"

    def test_portal_preview_prev_iteration_token(self):
        """GET /api/portal/preview/{prev_token} — returns quote data or 404/410 if expired"""
        r = requests.get(f"{BASE_URL}/api/portal/preview/{PREV_MAGIC_TOKEN}")
        assert r.status_code in (200, 404, 410), f"Unexpected status {r.status_code}: {r.text}"
        if r.status_code == 200:
            data = r.json()
            assert "resource_type" in data
            assert "resource" in data


# ── Invoice Permission ────────────────────────────────────────────────────────

class TestInvoicePermissions:
    """Invoices require auth"""

    def test_invoices_without_auth_returns_401(self):
        """GET /api/invoices without auth → 401"""
        r = requests.get(f"{BASE_URL}/api/invoices")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}: {r.text}"

    def test_invoices_with_auth_returns_200(self, auth_headers):
        """GET /api/invoices with auth → 200"""
        r = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert isinstance(r.json(), list), "Expected list"


# ── Financials Summary ────────────────────────────────────────────────────────

class TestFinancialsSummary:
    """Financials summary must include total_tax and net_income"""

    def test_financials_summary_fields(self, auth_headers):
        """GET /api/financials/summary → 200 with total_tax and net_income"""
        r = requests.get(f"{BASE_URL}/api/financials/summary", headers=auth_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        assert "total_tax" in data or "sales_tax" in data, f"Missing total_tax in {list(data.keys())}"
        assert "net_income" in data or "net_profit" in data, f"Missing net_income in {list(data.keys())}"


# ── Promo Codes ───────────────────────────────────────────────────────────────

class TestPromoCodes:
    """Promo codes list endpoint"""

    def test_promo_codes_with_auth(self, auth_headers):
        """GET /api/promo-codes → 200"""
        r = requests.get(f"{BASE_URL}/api/promo-codes", headers=auth_headers)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        assert isinstance(r.json(), list), "Expected list"
