"""
Iteration 87 - Auth Storage Regression Tests
Tests for verifying auth flows and portal pages after authStorage helper expansion.
Focus: Admin login, customer portal, employee portal, tier/billing endpoints.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
ADMIN_EMAIL = "signguypa@gmail.com"
ADMIN_PASSWORD = "Billnel323"


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_admin_profile_fetch(self):
        """Test fetching admin profile with token"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Fetch profile
        response = requests.get(f"{BASE_URL}/api/users/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert "role" in data
    
    def test_admin_permissions_fetch(self):
        """Test fetching admin permissions"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/users/me/permissions", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "permissions" in data or isinstance(data, list)


class TestTierEndpoints:
    """Tier/plan endpoints tests"""
    
    def test_plans_public(self):
        """Test public plans endpoint"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) > 0
    
    def test_my_plan_authenticated(self):
        """Test my-plan endpoint with auth"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/tiers/my-plan", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "plan_id" in data or "tier" in data or "plan" in data
    
    def test_usage_authenticated(self):
        """Test usage endpoint with auth"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/tiers/usage", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200


class TestBillingEndpoints:
    """Billing endpoints tests"""
    
    def test_pricing_public(self):
        """Test public pricing endpoint"""
        response = requests.get(f"{BASE_URL}/api/billing/pricing")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
    
    def test_trial_status_authenticated(self):
        """Test trial status endpoint with auth"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/billing/trial-status", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200


class TestCustomerPortalAuth:
    """Customer portal authentication tests"""
    
    def test_portal_login_endpoint_exists(self):
        """Test portal login endpoint exists (even if no valid customer)"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        # Should return 401 or 404, not 500
        assert response.status_code in [401, 404, 403], f"Unexpected status: {response.status_code}"
    
    def test_portal_register_endpoint_exists(self):
        """Test portal register endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/register", json={
            "email": "test_register@test.com",
            "password": "testpassword123"
        })
        # Should return 400/404/409 (no matching customer), not 500
        assert response.status_code in [400, 404, 409, 422], f"Unexpected status: {response.status_code}"


class TestEmployeePortalAuth:
    """Employee portal authentication tests"""
    
    def test_employee_login_endpoint_exists(self):
        """Test employee portal login endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/auth/login", json={
            "email": "nonexistent@test.com",
            "pin": "1234"
        })
        # Should return 401 or 404, not 500
        assert response.status_code in [401, 404, 403], f"Unexpected status: {response.status_code}"


class TestPortalDashboardEndpoints:
    """Portal dashboard endpoints tests (require valid portal auth)"""
    
    def test_portal_dashboard_requires_auth(self):
        """Test portal dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/portal/dashboard")
        assert response.status_code in [401, 403, 422]
    
    def test_employee_portal_config_requires_auth(self):
        """Test employee portal config requires authentication"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/config")
        assert response.status_code in [401, 403, 422]
    
    def test_employee_portal_timeclock_requires_auth(self):
        """Test employee portal time clock requires authentication"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/time-clock/status")
        assert response.status_code in [401, 403, 422]


class TestBackendHealth:
    """Backend health and startup tests"""
    
    def test_backend_startup_healthy(self):
        """Test backend is running and responding"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        assert response.status_code == 200
    
    def test_tenant_endpoint(self):
        """Test tenant endpoint with auth"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/tenant", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data or "tenant_id" in data or "name" in data
    
    def test_credits_balance(self):
        """Test credits balance endpoint"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/credits/balance", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
    
    def test_orders_list(self):
        """Test orders list endpoint"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/orders?limit=50", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
    
    def test_customers_list(self):
        """Test customers list endpoint"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        response = requests.get(f"{BASE_URL}/api/customers?limit=200", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
