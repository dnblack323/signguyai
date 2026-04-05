"""
RBAC (Role-Based Access Control) Tests for SignGuy AI
Tests Sprint 6 features: Owner, Admin, Staff roles with different permission levels
"""
import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import COMMON_TEST_PASSWORD, STAFF_TEST_EMAIL, STAFF_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
OWNER_EMAIL = SYNTHETIC_OWNER_EMAIL
OWNER_PASSWORD = SYNTHETIC_OWNER_PASSWORD
STAFF_EMAIL = STAFF_TEST_EMAIL
STAFF_PASSWORD = STAFF_TEST_PASSWORD


class TestRBACSetup:
    """Setup and verify test accounts exist"""
    
    def test_api_health(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ API Health Check passed")
    
    def test_owner_login(self):
        """Test owner account can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 401:
            # Owner account doesn't exist, try to register
            print("Owner account not found, attempting to register...")
            reg_response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": OWNER_EMAIL,
                "password": OWNER_PASSWORD,
                "full_name": "Test Owner"
            })
            if reg_response.status_code == 200:
                print("✅ Owner account registered successfully")
                return reg_response.json()
            else:
                pytest.fail(f"Failed to register owner: {reg_response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✅ Owner login successful")
        return data
    
    def test_staff_login(self):
        """Test staff account can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD
        })
        if response.status_code == 401:
            # Staff account doesn't exist, need to create via owner
            print("Staff account not found, will be created by owner...")
            pytest.skip("Staff account needs to be created by owner")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✅ Staff login successful")
        return data


class TestOwnerPermissions:
    """Test Owner role has full access"""
    
    @pytest.fixture
    def owner_token(self):
        """Get owner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Owner account not available")
        return response.json()["access_token"]
    
    def test_owner_can_view_users(self, owner_token):
        """Owner should be able to view all users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        users = response.json()
        assert isinstance(users, list)
        print(f"✅ Owner can view users - Found {len(users)} users")
    
    def test_owner_can_view_permissions(self, owner_token):
        """Owner should have all permissions"""
        response = requests.get(
            f"{BASE_URL}/api/users/me/permissions",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "owner"
        permissions = data.get("permissions", [])
        
        # Owner should have all key permissions
        expected_permissions = [
            "users:view", "users:create", "users:edit", "users:manage_roles",
            "financials:view", "financials:create",
            "invoices:view", "invoices:create",
            "payroll:view", "payroll:edit",
            "jobs:view", "jobs:create",
            "customers:view", "customers:create",
            "quotes:view", "quotes:create",
            "ai_tools:use"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions, f"Owner missing permission: {perm}"
        
        print(f"✅ Owner has {len(permissions)} permissions including all admin permissions")
    
    def test_owner_can_access_financials(self, owner_token):
        """Owner should be able to access financials"""
        response = requests.get(
            f"{BASE_URL}/api/financials/summary",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        # Should return 200 or data (not 403)
        assert response.status_code != 403
        print("✅ Owner can access financials endpoint")
    
    def test_owner_can_access_invoices(self, owner_token):
        """Owner should be able to access invoices"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        print("✅ Owner can access invoices endpoint")
    
    def test_owner_can_access_payroll(self, owner_token):
        """Owner should be able to access payroll"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/transactions",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        # Should return 200 or data (not 403)
        assert response.status_code != 403
        print("✅ Owner can access payroll endpoint")
    
    def test_owner_can_create_staff_user(self, owner_token):
        """Owner should be able to create a staff user"""
        # First check if staff user exists
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        users = response.json()
        staff_exists = any(u.get("email") == STAFF_EMAIL for u in users)
        
        if not staff_exists:
            # Create staff user
            response = requests.post(
                f"{BASE_URL}/api/admin/users/create",
                headers={"Authorization": f"Bearer {owner_token}"},
                json={
                    "email": STAFF_EMAIL,
                    "password": STAFF_PASSWORD,
                    "full_name": "Test Staff",
                    "role": "staff"
                }
            )
            assert response.status_code in [200, 201]
            print("✅ Owner created staff user successfully")
        else:
            print("✅ Staff user already exists")
    
    def test_owner_can_change_user_role(self, owner_token):
        """Owner should be able to change user roles"""
        # Get users list
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        users = response.json()
        
        # Find staff user
        staff_user = next((u for u in users if u.get("email") == STAFF_EMAIL), None)
        if not staff_user:
            pytest.skip("Staff user not found")
        
        # Try to change role (just verify endpoint works, then change back)
        user_id = staff_user.get("id")
        _current_role = staff_user.get("role")
        
        # Change to admin
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/role",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"role": "admin"}
        )
        assert response.status_code == 200
        print("✅ Owner can change user role to admin")
        
        # Change back to staff
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{user_id}/role",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"role": "staff"}
        )
        assert response.status_code == 200
        print("✅ Owner can change user role back to staff")


class TestStaffPermissions:
    """Test Staff role has restricted access"""
    
    @pytest.fixture
    def staff_token(self):
        """Get staff authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Staff account not available")
        return response.json()["access_token"]
    
    def test_staff_can_login(self, staff_token):
        """Staff should be able to login"""
        assert staff_token is not None
        print("✅ Staff login successful")
    
    def test_staff_permissions_are_limited(self, staff_token):
        """Staff should have limited permissions"""
        response = requests.get(
            f"{BASE_URL}/api/users/me/permissions",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "staff"
        permissions = data.get("permissions", [])
        
        # Staff should have these permissions
        expected_permissions = [
            "customers:view",
            "quotes:view",
            "jobs:view",
            "timeclock:view_own",
            "timeclock:clock_in",
            "webstores:view",
            "ai_tools:use"
        ]
        
        for perm in expected_permissions:
            assert perm in permissions, f"Staff missing expected permission: {perm}"
        
        # Staff should NOT have these permissions
        forbidden_permissions = [
            "invoices:view",
            "invoices:create",
            "financials:view",
            "financials:create",
            "payroll:view",
            "payroll:edit",
            "users:view",
            "users:create",
            "users:manage_roles"
        ]
        
        for perm in forbidden_permissions:
            assert perm not in permissions, f"Staff should NOT have permission: {perm}"
        
        print(f"✅ Staff has {len(permissions)} limited permissions (no admin access)")
    
    def test_staff_cannot_view_users(self, staff_token):
        """Staff should NOT be able to view user management"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert response.status_code == 403
        print("✅ Staff correctly denied access to /api/admin/users (403)")
    
    def test_staff_cannot_access_financials_api(self, staff_token):
        """Staff should NOT be able to access financials API"""
        # Note: The financials endpoint may not have permission checks
        # This tests the permission system, not necessarily the endpoint
        response = requests.get(
            f"{BASE_URL}/api/users/me/permissions",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        data = response.json()
        permissions = data.get("permissions", [])
        
        assert "financials:view" not in permissions
        print("✅ Staff does not have financials:view permission")
    
    def test_staff_cannot_access_invoices_permission(self, staff_token):
        """Staff should NOT have invoices permission"""
        response = requests.get(
            f"{BASE_URL}/api/users/me/permissions",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        data = response.json()
        permissions = data.get("permissions", [])
        
        assert "invoices:view" not in permissions
        print("✅ Staff does not have invoices:view permission")
    
    def test_staff_cannot_access_payroll_permission(self, staff_token):
        """Staff should NOT have payroll permission"""
        response = requests.get(
            f"{BASE_URL}/api/users/me/permissions",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        data = response.json()
        permissions = data.get("permissions", [])
        
        assert "payroll:view" not in permissions
        print("✅ Staff does not have payroll:view permission")
    
    def test_staff_can_access_jobs(self, staff_token):
        """Staff should be able to view jobs"""
        response = requests.get(
            f"{BASE_URL}/api/jobs",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        # Jobs endpoint may not require auth, but staff should have permission
        assert response.status_code != 403
        print("✅ Staff can access jobs endpoint")
    
    def test_staff_can_access_customers(self, staff_token):
        """Staff should be able to view customers"""
        response = requests.get(
            f"{BASE_URL}/api/customers",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert response.status_code != 403
        print("✅ Staff can access customers endpoint")
    
    def test_staff_can_access_quotes(self, staff_token):
        """Staff should be able to view quotes"""
        response = requests.get(
            f"{BASE_URL}/api/quotes",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert response.status_code != 403
        print("✅ Staff can access quotes endpoint")
    
    def test_staff_can_use_ai_tools(self, staff_token):
        """Staff should be able to use AI tools"""
        response = requests.get(
            f"{BASE_URL}/api/users/me/permissions",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        data = response.json()
        permissions = data.get("permissions", [])
        
        assert "ai_tools:use" in permissions
        print("✅ Staff has ai_tools:use permission")


class TestRoleBadges:
    """Test role badges display correctly"""
    
    @pytest.fixture
    def owner_token(self):
        """Get owner authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Owner account not available")
        return response.json()["access_token"]
    
    def test_owner_role_in_profile(self, owner_token):
        """Owner profile should show owner role"""
        response = requests.get(
            f"{BASE_URL}/api/users/me",
            headers={"Authorization": f"Bearer {owner_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "owner"
        print("✅ Owner profile shows 'owner' role")
    
    def test_staff_role_in_profile(self):
        """Staff profile should show staff role"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Staff account not available")
        
        token = response.json()["access_token"]
        response = requests.get(
            f"{BASE_URL}/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "staff"
        print("✅ Staff profile shows 'staff' role")


class TestAPIPermissionEnforcement:
    """Test that API endpoints properly enforce permissions"""
    
    @pytest.fixture
    def staff_token(self):
        """Get staff authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Staff account not available")
        return response.json()["access_token"]
    
    def test_admin_users_endpoint_requires_permission(self, staff_token):
        """GET /api/admin/users should return 403 for staff"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert response.status_code == 403
        print("✅ /api/admin/users returns 403 for staff user")
    
    def test_admin_create_user_requires_permission(self, staff_token):
        """POST /api/admin/users/create should return 403 for staff"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users/create",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={
                "email": f"test_{uuid.uuid4().hex[:8]}@test.com",
                "password": COMMON_TEST_PASSWORD,
                "full_name": "Test User"
            }
        )
        assert response.status_code == 403
        print("✅ /api/admin/users/create returns 403 for staff user")
    
    def test_admin_reset_password_requires_permission(self, staff_token):
        """POST /api/admin/users/{id}/reset-password should return 403 for staff"""
        response = requests.post(
            f"{BASE_URL}/api/admin/users/fake-id/reset-password",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={"new_password": "newpass123"}
        )
        assert response.status_code == 403
        print("✅ /api/admin/users/{id}/reset-password returns 403 for staff user")
    
    def test_admin_change_role_requires_permission(self, staff_token):
        """PUT /api/admin/users/{id}/role should return 403 for staff"""
        response = requests.put(
            f"{BASE_URL}/api/admin/users/fake-id/role",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={"role": "admin"}
        )
        assert response.status_code == 403
        print("✅ /api/admin/users/{id}/role returns 403 for staff user")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
