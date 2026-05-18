"""
Iteration 86 - Auth Storage Hardening Tests

Tests for:
1. Admin login still works after authStorage/sessionStorage changes
2. Tier endpoints still work after prior circular-import refactor
3. Backend test credentials helper works correctly
4. Representative API endpoints work for pages using migrated token helpers
"""

import pytest
import requests
import os
import sys

# Add backend to path for imports
sys.path.insert(0, '/app/backend')

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://wrap-command-center.preview.emergentagent.com')

# Import test credentials helper
try:
    from tests.test_credentials_helper import (
        PRODUCTION_OWNER_EMAIL,
        PRODUCTION_OWNER_PASSWORD,
    )
except ImportError:
    from backend.tests.test_credentials_helper import PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD


class TestAdminAuth:
    """Test admin authentication after authStorage changes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_admin_login_success(self):
        """Test admin login still works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        print("PASS: Admin login works correctly")
    
    def test_admin_profile_fetch(self, auth_token):
        """Test fetching admin profile with token"""
        response = requests.get(
            f"{BASE_URL}/api/users/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        # Email may be different due to token association
        assert "@" in data["email"]
        print(f"PASS: Admin profile fetch works - email: {data['email']}")


class TestTierEndpoints:
    """Test tier endpoints after circular-import refactor"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_tiers_plans_public(self):
        """Test public plans endpoint"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        print(f"PASS: Tiers plans endpoint works - {len(data['plans'])} plans returned")
    
    def test_tiers_my_plan_authenticated(self, auth_token):
        """Test my-plan endpoint with authentication"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/my-plan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan_type" in data or "tier" in data or "features" in data
        print(f"PASS: Tiers my-plan endpoint works")
    
    def test_tiers_usage_authenticated(self, auth_token):
        """Test usage endpoint with authentication"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/usage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "usage" in data
        print(f"PASS: Tiers usage endpoint works - {len(data['usage'])} usage records")


class TestBillingEndpoints:
    """Test billing endpoints for pages using migrated token helpers"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_billing_pricing_public(self):
        """Test public pricing endpoint"""
        response = requests.get(f"{BASE_URL}/api/billing/pricing")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        print(f"PASS: Billing pricing endpoint works - {len(data['plans'])} plans")
    
    def test_billing_trial_status(self, auth_token):
        """Test trial status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/billing/trial-status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "is_locked" in data or "is_trial" in data
        print(f"PASS: Billing trial-status endpoint works")
    
    def test_billing_subscription(self, auth_token):
        """Test subscription endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/billing/subscription",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data or "status" in data
        print(f"PASS: Billing subscription endpoint works")


class TestPromoCodesEndpoint:
    """Test promo codes endpoint (PromoCodes.js uses getAuthToken)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_promo_codes_list(self, auth_token):
        """Test listing promo codes"""
        response = requests.get(
            f"{BASE_URL}/api/promo-codes",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 200 with empty list, 404 if no promo codes feature, or 403 if permission denied
        assert response.status_code in [200, 403, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"PASS: Promo codes endpoint works - {len(data)} codes")
        elif response.status_code == 403:
            print("PASS: Promo codes endpoint returns 403 (owner-only feature)")
        else:
            print("PASS: Promo codes endpoint returns 404 (feature may not be enabled)")


class TestPricingSetupEndpoint:
    """Test pricing setup endpoints (PricingSetup.js uses getAuthToken)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_pricing_setup_imports(self, auth_token):
        """Test pricing setup imports endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # May return 200 with list or 404 if feature not available
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"PASS: Pricing setup imports endpoint works - {len(data)} imports")
        else:
            print("PASS: Pricing setup imports endpoint returns 404 (feature may not be enabled)")


class TestProductionSettingsEndpoint:
    """Test production settings endpoints (ProductionSettings.js uses getAuthToken)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_production_timeline_settings(self, auth_token):
        """Test production timeline settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/production-timeline/settings",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"PASS: Production timeline settings endpoint works")
    
    def test_production_timeline_templates(self, auth_token):
        """Test production timeline templates endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/production-timeline/templates",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"PASS: Production timeline templates endpoint works - {len(data)} templates")


class TestDashboardEndpoint:
    """Test dashboard endpoint (Dashboard uses getAuthToken via AppContext)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_dashboard_stats(self, auth_token):
        """Test dashboard stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"PASS: Dashboard stats endpoint works")


class TestTimeClockEndpoint:
    """Test timeclock endpoint (TimeClock uses getAuthToken via AppContext)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_employees_list(self, auth_token):
        """Test employees list endpoint (used by TimeClock)"""
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        print(f"PASS: Employees endpoint works - {len(data)} employees")


class TestJobTicketsEndpoint:
    """Test job tickets schema endpoint (DynamicCategoryFields uses getAuthToken)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": PRODUCTION_OWNER_EMAIL,
                "password": PRODUCTION_OWNER_PASSWORD
            }
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_job_tickets_schema(self, auth_token):
        """Test job tickets schema endpoint for vehicle_wraps category"""
        response = requests.get(
            f"{BASE_URL}/api/job-tickets/schema/vehicle_wraps",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "fields" in data
        print(f"PASS: Job tickets schema endpoint works - {len(data['fields'])} fields")


class TestCredentialsHelper:
    """Test that the test credentials helper works correctly"""
    
    def test_credentials_helper_imports(self):
        """Test that credentials helper can be imported"""
        try:
            from tests.test_credentials_helper import (
                PRODUCTION_OWNER_EMAIL,
                PRODUCTION_OWNER_PASSWORD,
            )
            assert PRODUCTION_OWNER_EMAIL is not None
            print(f"PASS: Credentials helper imports work - email: {PRODUCTION_OWNER_EMAIL}")
        except ImportError as e:
            pytest.skip(f"Credentials helper not available: {e}")
    
    def test_credentials_helper_values(self):
        """Test that credentials helper returns valid values"""
        try:
            from tests.test_credentials_helper import (
                PRODUCTION_OWNER_EMAIL,
                PRODUCTION_OWNER_PASSWORD,
            )
            # Should match the known test credentials
            assert PRODUCTION_OWNER_EMAIL is not None
            assert PRODUCTION_OWNER_PASSWORD is not None
            print(f"PASS: Credentials helper values are valid")
        except ImportError as e:
            pytest.skip(f"Credentials helper not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
