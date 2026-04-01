"""
Iteration 85 - Code Review Fixes Testing

Tests for:
- Tiers endpoints after circular import refactor: /api/tiers/plans, /api/tiers/my-plan, /api/tiers/usage
- Billing/webstores/job-tickets backend smoke after undefined-var and mutable-default fixes
- Admin users endpoint still works and remains tenant-scoped
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "signguypa@gmail.com"
ADMIN_PASSWORD = "Billnel323"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestTiersEndpoints:
    """Test tiers endpoints after circular import refactor"""
    
    def test_tiers_plans_public(self):
        """Test /api/tiers/plans - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plans" in data
        assert len(data["plans"]) > 0
        
        # Verify plan structure
        plan = data["plans"][0]
        assert "id" in plan
        assert "name" in plan
        assert "product_line" in plan
        print(f"✓ /api/tiers/plans returned {len(data['plans'])} plans")
    
    def test_tiers_my_plan_authenticated(self, auth_headers):
        """Test /api/tiers/my-plan - requires auth"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/my-plan",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should return tenant features
        assert isinstance(data, dict)
        print(f"✓ /api/tiers/my-plan returned tenant features")
    
    def test_tiers_usage_authenticated(self, auth_headers):
        """Test /api/tiers/usage - requires auth"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/usage",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "usage" in data
        print(f"✓ /api/tiers/usage returned usage data")


class TestBillingEndpoints:
    """Test billing endpoints after undefined-var fixes"""
    
    def test_billing_pricing_public(self):
        """Test /api/billing/pricing - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/billing/pricing")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plans" in data
        print(f"✓ /api/billing/pricing returned pricing data")
    
    def test_billing_founder_status_public(self):
        """Test /api/billing/founder-status - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/billing/founder-status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "founders_claimed" in data
        assert "founders_remaining" in data
        print(f"✓ /api/billing/founder-status returned founder status")
    
    def test_billing_trial_status_authenticated(self, auth_headers):
        """Test /api/billing/trial-status - requires auth"""
        response = requests.get(
            f"{BASE_URL}/api/billing/trial-status",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "is_trial" in data or "is_locked" in data
        print(f"✓ /api/billing/trial-status returned trial status")
    
    def test_billing_subscription_authenticated(self, auth_headers):
        """Test /api/billing/subscription - requires auth"""
        response = requests.get(
            f"{BASE_URL}/api/billing/subscription",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plan" in data or "status" in data
        print(f"✓ /api/billing/subscription returned subscription data")


class TestWebstoresEndpoints:
    """Test webstores endpoints after fixes"""
    
    def test_webstores_list_authenticated(self, auth_headers):
        """Test /api/webstores/v2 - list webstores"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ /api/webstores/v2 returned {len(data)} webstores")
    
    def test_products_list_authenticated(self, auth_headers):
        """Test /api/products - list products"""
        response = requests.get(
            f"{BASE_URL}/api/products",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ /api/products returned {len(data)} products")


class TestJobTicketsEndpoints:
    """Test job tickets endpoints after mutable-default fixes"""
    
    def test_job_tickets_list_authenticated(self, auth_headers):
        """Test /api/job-tickets - list job tickets"""
        response = requests.get(
            f"{BASE_URL}/api/job-tickets",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        print(f"✓ /api/job-tickets returned {data['total']} tickets")
    
    def test_job_tickets_schema_authenticated(self, auth_headers):
        """Test /api/job-tickets/schema/{category} - get schema"""
        categories = ["banners", "apparel", "rigid_signs", "cut_vinyl", "vehicle_wrap"]
        
        for category in categories:
            response = requests.get(
                f"{BASE_URL}/api/job-tickets/schema/{category}",
                headers=auth_headers
            )
            assert response.status_code == 200, f"Expected 200 for {category}, got {response.status_code}: {response.text}"
            
            data = response.json()
            assert "category" in data
            assert "fields" in data
        
        print(f"✓ /api/job-tickets/schema returned schemas for {len(categories)} categories")


class TestAdminUsersEndpoint:
    """Test admin users endpoint remains tenant-scoped"""
    
    def test_admin_users_list_authenticated(self, auth_headers):
        """Test /api/admin/users - list users (tenant-scoped)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        
        # Verify all users belong to same tenant (tenant_id should be consistent)
        if len(data) > 0:
            tenant_ids = set(user.get("tenant_id") for user in data if user.get("tenant_id"))
            # All users should have the same tenant_id (tenant-scoped)
            assert len(tenant_ids) <= 1, f"Users from multiple tenants returned: {tenant_ids}"
        
        print(f"✓ /api/admin/users returned {len(data)} tenant-scoped users")


class TestFoundersEndpoints:
    """Test founders billing endpoints"""
    
    def test_founders_plan_authenticated(self, auth_headers):
        """Test /api/billing/founders/plan - get founders plan info"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/plan",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plan" in data
        print(f"✓ /api/billing/founders/plan returned founders plan info")
    
    def test_founders_spots_public(self):
        """Test /api/billing/founders/spots - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/billing/founders/spots")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "total" in data or "remaining" in data or "is_available" in data
        print(f"✓ /api/billing/founders/spots returned spots info")


class TestMultiProductBilling:
    """Test multi-product billing endpoints"""
    
    def test_subscription_v2_authenticated(self, auth_headers):
        """Test /api/billing/subscription/v2 - get v2 subscription"""
        response = requests.get(
            f"{BASE_URL}/api/billing/subscription/v2",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plan_type" in data
        assert "product_line" in data
        print(f"✓ /api/billing/subscription/v2 returned v2 subscription data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
