"""
Stripe Connect API Tests

Tests for:
- GET /api/stripe-connect/status - Get connection status and platform fee
- POST /api/stripe-connect/create-account - Create Stripe account and get onboarding URL
- POST /api/stripe-connect/refresh-link - Refresh onboarding link
- DELETE /api/stripe-connect/disconnect - Disconnect Stripe account
- POST /api/stripe-connect/invoice/{invoice_id}/pay - Create payment link for invoice
- POST /api/stripe-connect/webstore/{webstore_id}/checkout - Create checkout session
- GET /api/stripe-connect/payment-status/{session_id} - Check payment status
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "testpass123"


class TestStripeConnectAuth:
    """Test authentication and basic connectivity"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_health_check(self):
        """Test API is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ Health check passed")
    
    def test_stripe_status_requires_auth(self):
        """Test that Stripe status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/stripe-connect/status")
        assert response.status_code == 401
        print("✓ Stripe status endpoint requires authentication")


class TestStripeConnectStatus:
    """Test GET /api/stripe-connect/status"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_get_connect_status(self, auth_headers):
        """Test getting Stripe Connect status"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "connected" in data
        assert "platform_fee_percent" in data
        assert isinstance(data["connected"], bool)
        assert isinstance(data["platform_fee_percent"], (int, float))
        
        # For starter tier, should be 3%
        # Platform fee should be between 1% and 3%
        assert 1 <= data["platform_fee_percent"] <= 3
        
        print(f"✓ Connect status: connected={data['connected']}, fee={data['platform_fee_percent']}%")
        
    def test_status_response_fields(self, auth_headers):
        """Test that status response has all expected fields"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = [
            "connected",
            "account_id",
            "charges_enabled",
            "payouts_enabled",
            "onboarding_complete",
            "platform_fee_percent"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ All expected fields present in status response")


class TestStripeConnectCreateAccount:
    """Test POST /api/stripe-connect/create-account"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_create_account_requires_auth(self):
        """Test that create account requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/create-account",
            json={
                "return_url": "https://example.com/return",
                "refresh_url": "https://example.com/refresh"
            }
        )
        assert response.status_code == 401
        print("✓ Create account requires authentication")
    
    def test_create_account_returns_onboarding_url(self, auth_headers):
        """Test creating Stripe account returns onboarding URL"""
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/create-account",
            json={
                "return_url": "https://example.com/return",
                "refresh_url": "https://example.com/refresh"
            },
            headers=auth_headers
        )
        
        # Should succeed and return URL
        assert response.status_code == 200
        data = response.json()
        
        assert "url" in data
        assert "account_id" in data
        assert data["url"].startswith("https://connect.stripe.com")
        assert data["account_id"].startswith("acct_")
        
        print(f"✓ Create account returned onboarding URL: {data['url'][:50]}...")
        print(f"✓ Account ID: {data['account_id']}")
    
    def test_create_account_validates_request(self, auth_headers):
        """Test that create account validates request body"""
        # Missing required fields
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/create-account",
            json={},
            headers=auth_headers
        )
        # Should fail validation
        assert response.status_code == 422
        print("✓ Create account validates required fields")


class TestStripeConnectRefreshLink:
    """Test POST /api/stripe-connect/refresh-link"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_refresh_link_requires_auth(self):
        """Test that refresh link requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/refresh-link",
            json={
                "return_url": "https://example.com/return",
                "refresh_url": "https://example.com/refresh"
            }
        )
        assert response.status_code == 401
        print("✓ Refresh link requires authentication")
    
    def test_refresh_link_with_existing_account(self, auth_headers):
        """Test refreshing onboarding link for existing account"""
        # First check if account exists
        status_response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers
        )
        status = status_response.json()
        
        if not status.get("account_id"):
            # Create account first if it doesn't exist
            requests.post(
                f"{BASE_URL}/api/stripe-connect/create-account",
                json={
                    "return_url": "https://example.com/return",
                    "refresh_url": "https://example.com/refresh"
                },
                headers=auth_headers
            )
        
        # Now try to refresh
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/refresh-link",
            json={
                "return_url": "https://example.com/return",
                "refresh_url": "https://example.com/refresh"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
        assert "account_id" in data
        print(f"✓ Refresh link returned new onboarding URL")


class TestStripeConnectDisconnect:
    """Test DELETE /api/stripe-connect/disconnect"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_disconnect_requires_auth(self):
        """Test that disconnect requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/stripe-connect/disconnect")
        assert response.status_code == 401
        print("✓ Disconnect requires authentication")
    
    def test_disconnect_stripe_account(self, auth_headers):
        """Test disconnecting Stripe account"""
        # First ensure we have an account connected
        status_response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers
        )
        initial_status = status_response.json()
        
        if not initial_status.get("account_id"):
            # Create account first
            requests.post(
                f"{BASE_URL}/api/stripe-connect/create-account",
                json={
                    "return_url": "https://example.com/return",
                    "refresh_url": "https://example.com/refresh"
                },
                headers=auth_headers
            )
        
        # Now disconnect
        response = requests.delete(
            f"{BASE_URL}/api/stripe-connect/disconnect",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify disconnected
        verify_response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers
        )
        verify_status = verify_response.json()
        assert verify_status["connected"] == False
        assert verify_status.get("account_id") is None
        
        print("✓ Successfully disconnected Stripe account")


class TestStripeConnectInvoicePayment:
    """Test POST /api/stripe-connect/invoice/{invoice_id}/pay"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_invoice_pay_requires_auth(self):
        """Test that invoice payment requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/invoice/test-invoice-id/pay",
            params={"origin_url": "https://example.com"}
        )
        assert response.status_code == 401
        print("✓ Invoice payment requires authentication")
    
    def test_invoice_pay_not_found(self, auth_headers):
        """Test payment for non-existent invoice returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/invoice/nonexistent-invoice-id/pay",
            params={"origin_url": "https://example.com"},
            headers=auth_headers
        )
        # Should return 404 (invoice not found) or 400 (no stripe account)
        assert response.status_code in [400, 404]
        print(f"✓ Invoice not found returns expected error: {response.status_code}")
    
    def test_invoice_pay_without_stripe_connected(self, auth_headers):
        """Test invoice payment when Stripe is not connected"""
        # First disconnect Stripe if connected
        requests.delete(
            f"{BASE_URL}/api/stripe-connect/disconnect",
            headers=auth_headers
        )
        
        # Get an existing invoice
        invoices_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        
        if invoices_response.status_code == 200 and invoices_response.json():
            invoice_id = invoices_response.json()[0].get("id")
            if invoice_id:
                response = requests.post(
                    f"{BASE_URL}/api/stripe-connect/invoice/{invoice_id}/pay",
                    params={"origin_url": "https://example.com"},
                    headers=auth_headers
                )
                # Should fail because Stripe not connected
                assert response.status_code == 400
                assert "not connected" in response.json().get("detail", "").lower()
                print("✓ Invoice payment fails correctly when Stripe not connected")
            else:
                print("✓ No invoices found to test (expected)")
        else:
            print("✓ No invoices found to test (expected)")


class TestStripeConnectWebstoreCheckout:
    """Test POST /api/stripe-connect/webstore/{webstore_id}/checkout"""
    
    def test_webstore_checkout_with_invalid_store(self):
        """Test checkout with non-existent webstore"""
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/webstore/nonexistent-store/checkout",
            params={"origin_url": "https://example.com"},
            json={
                "items": [{"product_id": "test", "quantity": 1, "price": 10.00}],
                "customer_info": {"name": "Test", "email": "test@test.com"}
            }
        )
        assert response.status_code == 404
        print("✓ Webstore not found returns 404")
    
    def test_webstore_checkout_validates_items(self):
        """Test checkout validates items array"""
        # This is a public endpoint, so no auth required
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/webstore/some-store-id/checkout",
            params={"origin_url": "https://example.com"},
            json={
                "items": [],  # Empty items
                "customer_info": {"name": "Test", "email": "test@test.com"}
            }
        )
        # Should return 404 (store not found) or 400 (validation error)
        assert response.status_code in [400, 404, 422]
        print(f"✓ Webstore checkout validates request: {response.status_code}")


class TestStripeConnectPaymentStatus:
    """Test GET /api/stripe-connect/payment-status/{session_id}"""
    
    def test_payment_status_invalid_session(self):
        """Test payment status with invalid session ID"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/payment-status/invalid-session-id"
        )
        # Should return 400 with Stripe error
        assert response.status_code == 400
        print("✓ Invalid session ID returns 400 error")
    
    def test_payment_status_nonexistent_session(self):
        """Test payment status with non-existent session"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/payment-status/cs_test_nonexistent123"
        )
        # Should return 400 (Stripe error for invalid session)
        assert response.status_code == 400
        print("✓ Non-existent session returns appropriate error")


class TestStripeConnectDashboardLink:
    """Test GET /api/stripe-connect/dashboard-link"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_dashboard_link_requires_auth(self):
        """Test that dashboard link requires authentication"""
        response = requests.get(f"{BASE_URL}/api/stripe-connect/dashboard-link")
        assert response.status_code == 401
        print("✓ Dashboard link requires authentication")
    
    def test_dashboard_link_without_stripe_connected(self, auth_headers):
        """Test dashboard link when Stripe not connected"""
        # First disconnect Stripe if connected
        requests.delete(
            f"{BASE_URL}/api/stripe-connect/disconnect",
            headers=auth_headers
        )
        
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/dashboard-link",
            headers=auth_headers
        )
        # Should fail because no Stripe account connected
        assert response.status_code == 400
        print("✓ Dashboard link fails correctly when Stripe not connected")


class TestPlatformFeeByTier:
    """Test platform fee calculation by subscription tier"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code}")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_platform_fee_valid_range(self, auth_headers):
        """Test that platform fee is within valid range"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        fee = data["platform_fee_percent"]
        # Valid fees: 1% (Business), 2% (Pro/Growth), 3% (Starter)
        assert fee in [1, 2, 3], f"Unexpected fee: {fee}%"
        print(f"✓ Platform fee is valid: {fee}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
