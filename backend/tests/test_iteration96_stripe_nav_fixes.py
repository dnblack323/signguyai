"""
Iteration 96 - Stripe Connect Mode Fields, Navigation Cleanup, and Settings Fixes

Tests:
1. GET /api/stripe-connect/status returns stripe_mode, account_mode, mode_mismatch fields
2. Verify no runtime regressions on key endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestStripeConnectModeFields:
    """Test Stripe Connect status endpoint returns new mode fields"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_stripe_connect_status_returns_mode_fields(self):
        """Verify /api/stripe-connect/status returns stripe_mode, account_mode, mode_mismatch"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=self.headers
        )
        assert response.status_code == 200, f"Status endpoint failed: {response.text}"
        
        data = response.json()
        
        # Verify new fields exist
        assert "stripe_mode" in data, "Missing stripe_mode field"
        assert "account_mode" in data, "Missing account_mode field"
        assert "mode_mismatch" in data, "Missing mode_mismatch field"
        
        # Verify stripe_mode is either 'test' or 'live'
        assert data["stripe_mode"] in ["test", "live"], f"Invalid stripe_mode: {data['stripe_mode']}"
        
        # Verify mode_mismatch is boolean
        assert isinstance(data["mode_mismatch"], bool), "mode_mismatch should be boolean"
        
        # Verify existing fields still present
        assert "connected" in data
        assert "charges_enabled" in data
        assert "payouts_enabled" in data
        assert "onboarding_complete" in data
        assert "platform_fee_percent" in data
        
        print(f"✓ Stripe Connect status returns all mode fields")
        print(f"  stripe_mode: {data['stripe_mode']}")
        print(f"  account_mode: {data['account_mode']}")
        print(f"  mode_mismatch: {data['mode_mismatch']}")
    
    def test_stripe_mode_consistency(self):
        """Verify stripe_mode is consistent with platform configuration"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # If not connected, account_mode should be null and mode_mismatch should be false
        if not data["connected"]:
            assert data["account_mode"] is None, "account_mode should be null when not connected"
            assert data["mode_mismatch"] is False, "mode_mismatch should be false when not connected"
            print("✓ Unconnected account has correct mode values")
        else:
            # If connected, account_mode should be 'test' or 'live'
            assert data["account_mode"] in ["test", "live"], f"Invalid account_mode: {data['account_mode']}"
            # mode_mismatch should be true if stripe_mode != account_mode
            expected_mismatch = data["stripe_mode"] != data["account_mode"]
            assert data["mode_mismatch"] == expected_mismatch, "mode_mismatch calculation incorrect"
            print(f"✓ Connected account mode values correct (mismatch: {data['mode_mismatch']})")


class TestNoRuntimeRegressions:
    """Test that key endpoints still work after changes"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for tests"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_tenant_endpoint_works(self):
        """Verify tenant endpoint still works (used by settings pages)"""
        response = requests.get(
            f"{BASE_URL}/api/tenant",
            headers=self.headers
        )
        assert response.status_code == 200, f"Tenant endpoint failed: {response.text}"
        
        data = response.json()
        assert "id" in data or "name" in data, "Tenant data missing expected fields"
        print("✓ Tenant endpoint works correctly")
    
    def test_workflow_templates_endpoint_works(self):
        """Verify workflow templates endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/workflow-templates",
            headers=self.headers
        )
        # Should return 200 or 404 (if no templates), not 500
        assert response.status_code in [200, 404], f"Workflow templates endpoint error: {response.text}"
        print(f"✓ Workflow templates endpoint works (status: {response.status_code})")
    
    def test_production_settings_endpoint_works(self):
        """Verify production settings related endpoints work"""
        # Test materials endpoint (used by production settings)
        response = requests.get(
            f"{BASE_URL}/api/materials",
            headers=self.headers
        )
        assert response.status_code in [200, 404], f"Materials endpoint error: {response.text}"
        print(f"✓ Materials endpoint works (status: {response.status_code})")
    
    def test_backup_endpoint_works(self):
        """Verify backup endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/backup/status",
            headers=self.headers
        )
        # Should return 200 or 404, not 500
        assert response.status_code in [200, 404], f"Backup status endpoint error: {response.text}"
        print(f"✓ Backup status endpoint works (status: {response.status_code})")
    
    def test_invoices_endpoint_works(self):
        """Verify invoices endpoint works (billing section)"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=self.headers
        )
        assert response.status_code == 200, f"Invoices endpoint failed: {response.text}"
        print("✓ Invoices endpoint works correctly")
    
    def test_orders_endpoint_works(self):
        """Verify orders endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/orders",
            headers=self.headers
        )
        assert response.status_code == 200, f"Orders endpoint failed: {response.text}"
        print("✓ Orders endpoint works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
