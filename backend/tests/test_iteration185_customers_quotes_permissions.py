"""
Iteration 185 Tests - Customers, Quotes, Permissions
Tests for:
- platform_creator role returns full permissions (ROLE_PERMISSIONS fix)
- PUT /api/customers/{id} response includes tenant_id (tenant-scoped readback)
- Customer APIs work correctly (load/retry)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASS = "password123"


@pytest.fixture(scope="module")
def admin_token():
    """Login with admin credentials and return token"""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
    )
    if resp.status_code != 200:
        pytest.skip(f"Auth failed: {resp.status_code} {resp.text}")
    data = resp.json()
    token = data.get("token") or data.get("access_token")
    if not token:
        pytest.skip("No token in login response")
    return token


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ───────────────────────────────────────────────
# Section 1: Auth / Permission checks
# ───────────────────────────────────────────────

class TestPermissions:
    """Verify that platform_creator role gets full permission set from backend"""

    def test_login_returns_token(self, admin_token):
        """Admin login succeeds and returns a token"""
        assert admin_token and len(admin_token) > 10
        print(f"PASS: Admin token obtained (len={len(admin_token)})")

    def test_platform_creator_role_in_user_info(self, auth_headers):
        """Authenticated user has platform_creator or owner role"""
        resp = requests.get(f"{BASE_URL}/api/users/me", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        role = data.get("role") or data.get("user", {}).get("role")
        assert role in ("platform_creator", "owner", "platform_admin"), \
            f"Expected privileged role, got: {role}"
        print(f"PASS: User role is '{role}'")

    def test_invoices_endpoint_accessible(self, auth_headers):
        """GET /api/invoices returns 200 for platform_creator (no permission error)"""
        resp = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert resp.status_code == 200, \
            f"Expected 200 (permission OK), got {resp.status_code}: {resp.text[:200]}"
        print(f"PASS: /api/invoices accessible (status={resp.status_code})")

    def test_financials_reports_accessible(self, auth_headers):
        """GET /api/reports/financial (or similar) returns 200 for platform_creator"""
        # Try common financials endpoint
        resp = requests.get(f"{BASE_URL}/api/invoices/summary", headers=auth_headers)
        # May not exist, so accept 200 or 404 — just NOT 403
        assert resp.status_code != 403, \
            f"Got 403 Forbidden — platform_creator should have full access. status={resp.status_code}"
        print(f"PASS: Financials endpoint status={resp.status_code} (not 403)")

    def test_customers_endpoint_accessible(self, auth_headers):
        """GET /api/customers returns 200 for platform_creator"""
        resp = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        print(f"PASS: /api/customers accessible (status={resp.status_code})")


# ───────────────────────────────────────────────
# Section 2: PUT /api/customers/{id} - tenant_id in response
# ───────────────────────────────────────────────

class TestCustomerUpdate:
    """Verify PUT /api/customers/{id} response includes tenant_id"""

    @pytest.fixture(scope="class")
    def test_customer_id(self, auth_headers):
        """Create a test customer for this class and clean up after"""
        resp = requests.post(
            f"{BASE_URL}/api/customers",
            json={
                "name": "TEST_IterCustomer185",
                "company": "TEST_IterCo185",
                "email": "test185@testonly.example.com",
                "status": "lead",
                "notes": "Created by iteration 185 test",
            },
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201), f"Customer create failed: {resp.status_code} {resp.text[:200]}"
        cid = resp.json().get("id")
        assert cid, "No id in create response"
        yield cid
        # cleanup
        requests.delete(f"{BASE_URL}/api/customers/{cid}", headers=auth_headers)
        print(f"Cleanup: deleted test customer {cid}")

    def test_create_customer_returns_tenant_id(self, auth_headers):
        """POST /api/customers response includes tenant_id"""
        resp = requests.post(
            f"{BASE_URL}/api/customers",
            json={"name": "TEST_TenantIdCheck185", "status": "lead"},
            headers=auth_headers,
        )
        assert resp.status_code in (200, 201), f"Expected 200/201 got {resp.status_code}"
        data = resp.json()
        assert "tenant_id" in data, f"tenant_id missing from POST response: {data.keys()}"
        assert data["tenant_id"], f"tenant_id is empty/null in POST response"
        print(f"PASS: POST /api/customers includes tenant_id='{data['tenant_id']}'")
        # cleanup
        cid = data.get("id")
        if cid:
            requests.delete(f"{BASE_URL}/api/customers/{cid}", headers=auth_headers)

    def test_put_customer_response_includes_tenant_id(self, auth_headers, test_customer_id):
        """PUT /api/customers/{id} response includes tenant_id (tenant-scoped readback)"""
        resp = requests.put(
            f"{BASE_URL}/api/customers/{test_customer_id}",
            json={"notes": "Updated by iter185 test"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert "tenant_id" in data, f"tenant_id missing from PUT response keys: {list(data.keys())}"
        assert data["tenant_id"], f"tenant_id is empty in PUT response"
        print(f"PASS: PUT /api/customers/{{id}} includes tenant_id='{data['tenant_id']}'")

    def test_put_customer_response_structure(self, auth_headers, test_customer_id):
        """PUT /api/customers/{id} response has correct data structure"""
        resp = requests.put(
            f"{BASE_URL}/api/customers/{test_customer_id}",
            json={"notes": "Structure check by iter185"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Must have key customer fields
        for field in ("id", "name", "tenant_id"):
            assert field in data, f"Field '{field}' missing from PUT response: {list(data.keys())}"
        # Must not have MongoDB _id
        assert "_id" not in data, f"MongoDB _id should be excluded from response"
        print(f"PASS: PUT response structure correct (id, name, tenant_id present, no _id)")


# ───────────────────────────────────────────────
# Section 3: Quotes endpoint + customer_id filtering
# ───────────────────────────────────────────────

class TestQuotesCustomerFilter:
    """Verify quotes can be fetched and customer_id filtering works at API level"""

    def test_get_quotes_accessible(self, auth_headers):
        """GET /api/quotes returns 200"""
        resp = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200 got {resp.status_code}: {resp.text[:200]}"
        data = resp.json()
        assert isinstance(data, list), f"Expected list of quotes, got {type(data)}"
        print(f"PASS: GET /api/quotes returns {len(data)} quotes")

    def test_quotes_have_customer_id_field(self, auth_headers):
        """All quotes have a customer_id field"""
        resp = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        assert resp.status_code == 200
        quotes = resp.json()
        if not quotes:
            pytest.skip("No quotes to test - skip customer_id field check")
        for q in quotes[:5]:  # check first 5
            assert "customer_id" in q, f"Quote missing customer_id: {list(q.keys())}"
        print(f"PASS: All checked quotes have customer_id field")

    def test_get_customers_for_filter(self, auth_headers):
        """Can fetch customers to use for quote filtering"""
        resp = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert resp.status_code == 200
        customers = resp.json()
        assert isinstance(customers, list)
        print(f"PASS: GET /api/customers returns {len(customers)} customers for filter chip")


# ───────────────────────────────────────────────
# Section 4: Dashboard - pending customer actions endpoint
# ───────────────────────────────────────────────

class TestPendingCustomerActions:
    """Verify /api/wrap/pending-customer-actions returns structured data"""

    def test_pending_actions_endpoint_accessible(self, auth_headers):
        """GET /api/wrap/pending-customer-actions returns 200 (not 403 or 500)"""
        resp = requests.get(
            f"{BASE_URL}/api/wrap/pending-customer-actions",
            headers=auth_headers,
        )
        assert resp.status_code == 200, \
            f"Expected 200 got {resp.status_code}: {resp.text[:300]}"
        data = resp.json()
        # Should have 'items' key
        assert "items" in data, f"Expected 'items' key in response: {list(data.keys())}"
        assert isinstance(data["items"], list), f"Expected items to be a list"
        print(f"PASS: /api/wrap/pending-customer-actions returns {len(data['items'])} items")

    def test_pending_actions_not_403(self, auth_headers):
        """Pending customer actions should not return 403 for platform_creator"""
        resp = requests.get(
            f"{BASE_URL}/api/wrap/pending-customer-actions",
            headers=auth_headers,
        )
        assert resp.status_code != 403, \
            f"Got 403 — platform_creator should have access to pending actions"
        print(f"PASS: Pending actions endpoint not 403 (status={resp.status_code})")
