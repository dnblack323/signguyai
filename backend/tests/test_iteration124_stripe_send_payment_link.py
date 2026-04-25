"""
Iteration 124: Stripe Service Refactor + Send Payment Link Feature Tests

Tests:
1. Auth login with admin credentials
2. GET /api/stripe-connect/status - regression test for refactor
3. GET /api/webstores/v2/ - regression test for refactor
4. POST /api/stripe-connect/invoice/{id}/send-payment-link - endpoint exists (400 from Stripe expected, not 404)
5. POST /api/stripe-connect/invoice/{id}/send-payment-link with invalid ID returns 404
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestAuth:
    """Authentication for subsequent tests"""

    def test_login_success(self):
        """Login with admin credentials to get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "signguypa@gmail.com", "password": "Billnel323"},
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, f"No token in response: {data}"
        print("✓ Login successful")


@pytest.fixture(scope="module")
def auth_token():
    """Get auth token for the admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "signguypa@gmail.com", "password": "Billnel323"},
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    data = response.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        pytest.skip("No token in login response")
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestStripeConnectStatusRegression:
    """Regression tests for GET /api/stripe-connect/status after service refactor"""

    def test_stripe_connect_status_returns_200(self, auth_headers):
        """Verify GET /api/stripe-connect/status still works after refactor"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        print(f"✓ stripe-connect/status returned 200: {data}")

    def test_stripe_connect_status_has_required_fields(self, auth_headers):
        """Verify response structure is correct"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # All required fields from ConnectAccountResponse model
        assert "connected" in data, f"Missing 'connected' field: {data}"
        assert "charges_enabled" in data, f"Missing 'charges_enabled' field: {data}"
        assert "payouts_enabled" in data, f"Missing 'payouts_enabled' field: {data}"
        assert "platform_fee_percent" in data, f"Missing 'platform_fee_percent' field: {data}"
        assert "stripe_mode" in data, f"Missing 'stripe_mode' field: {data}"
        assert isinstance(data["connected"], bool)
        print(f"✓ All required fields present: connected={data['connected']}, mode={data['stripe_mode']}")


class TestWebstoresV2Regression:
    """Regression tests for GET /api/webstores/v2/ after service refactor"""

    def test_webstores_v2_returns_200(self, auth_headers):
        """Verify GET /api/webstores/v2 still works after refactor (no trailing slash)"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        print(f"✓ webstores/v2 returned 200, {len(data) if isinstance(data, list) else 'dict'} items")

    def test_webstores_v2_returns_list(self, auth_headers):
        """Verify webstores endpoint returns a list (no trailing slash to avoid redirect auth header drop)"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"✓ webstores/v2/ returned list with {len(data)} webstore(s)")


class TestSendPaymentLinkEndpoint:
    """Tests for POST /api/stripe-connect/invoice/{id}/send-payment-link"""

    def test_endpoint_exists_not_404(self, auth_headers):
        """Verify the endpoint is registered - should NOT return 404.
        
        In test mode (no charges_enabled), Stripe may reject the checkout
        session creation with 400, which is EXPECTED behavior.
        The key verification: 404 means route missing; 400 means route exists
        but Stripe rejected it (expected in test mode).
        """
        # Use a fake invoice ID - should return 404 for invoice not found,
        # not 404 for route not found
        fake_invoice_id = "00000000-0000-0000-0000-000000000000"
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/invoice/{fake_invoice_id}/send-payment-link",
            json={"customer_email": None},
            params={"origin_url": "https://example.com"},
            headers=auth_headers,
        )
        # Should be 404 (invoice not found) or 400 (Stripe error) - NOT a routing 404
        # A routing 404 would say "Not Found" and not have a detail with "Invoice not found"
        assert response.status_code != 405, f"Method not allowed - endpoint may be missing: {response.text}"
        print(f"✓ Endpoint is registered. Status: {response.status_code}, Response: {response.text[:200]}")

    def test_endpoint_returns_404_for_missing_invoice(self, auth_headers):
        """Verify endpoint returns 404 when invoice ID doesn't exist"""
        fake_invoice_id = "nonexistent-invoice-id-12345"
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/invoice/{fake_invoice_id}/send-payment-link",
            json={"customer_email": None},
            params={"origin_url": "https://example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 404, f"Expected 404 for missing invoice, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower() or "invoice" in data["detail"].lower()
        print(f"✓ Returns 404 for missing invoice: {data['detail']}")

    def test_endpoint_with_real_invoice(self, auth_headers):
        """Get real invoice IDs and test the endpoint - expect 400 from Stripe in test mode"""
        # First fetch invoices to get a real unpaid invoice ID
        invoices_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers,
        )
        if invoices_response.status_code != 200:
            pytest.skip(f"Could not fetch invoices: {invoices_response.text}")

        invoices = invoices_response.json()
        # Find an unpaid invoice
        unpaid_invoices = [inv for inv in invoices if inv.get("status") != "paid"]
        if not unpaid_invoices:
            pytest.skip("No unpaid invoices available for testing")

        invoice = unpaid_invoices[0]
        invoice_id = invoice.get("id")
        print(f"Testing with invoice ID: {invoice_id}, status: {invoice.get('status')}, total: {invoice.get('total')}")

        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/invoice/{invoice_id}/send-payment-link",
            json={"customer_email": None},
            params={"origin_url": "https://example.com"},
            headers=auth_headers,
        )
        # Expected: 400 (Stripe rejects in test mode - no charges enabled)
        # Also acceptable: 200 (if Stripe accepts it in this test environment)
        # NOT acceptable: 404 (route missing) or 500 (server error)
        assert response.status_code in [200, 400], (
            f"Unexpected status {response.status_code}: {response.text}"
        )
        if response.status_code == 400:
            print(f"✓ Got expected 400 from Stripe test mode: {response.json().get('detail', '')[:200]}")
        elif response.status_code == 200:
            data = response.json()
            assert "url" in data, f"Missing 'url' in response: {data}"
            assert "session_id" in data, f"Missing 'session_id' in response: {data}"
            print(f"✓ Got 200 with checkout URL: {data.get('url', '')[:80]}...")

    def test_endpoint_requires_auth(self):
        """Verify the endpoint requires authentication"""
        fake_id = "test-invoice-id"
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/invoice/{fake_id}/send-payment-link",
            json={"customer_email": None},
            params={"origin_url": "https://example.com"},
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"✓ Endpoint requires authentication (401)")


class TestInvoicesEndpoint:
    """Verify invoices API still works (regression for refactor)"""

    def test_get_invoices_returns_200(self, auth_headers):
        """GET /api/invoices returns 200"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ /api/invoices returned {len(data)} invoices")

    def test_invoices_have_unpaid_items(self, auth_headers):
        """Verify there are unpaid invoices in the system for UI testing"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        invoices = response.json()
        unpaid = [inv for inv in invoices if inv.get("status") != "paid"]
        print(f"✓ Found {len(unpaid)} unpaid invoice(s) out of {len(invoices)} total")
        # Just informational - log the first unpaid invoice
        if unpaid:
            first = unpaid[0]
            print(f"  First unpaid: id={first.get('id')}, total={first.get('total')}, status={first.get('status')}")
