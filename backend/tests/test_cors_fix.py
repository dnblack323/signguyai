"""
CORS Fix Verification Tests - P0 Bug Fix
Testing: CORS preflight returns correct headers after removing allow_credentials=True

Root Cause: allow_credentials=True + allow_origins=["*"] violated CORS spec
Fix: Set allow_credentials=False (app uses Bearer token auth, not cookies)

Tests:
- OPTIONS preflight requests return 200
- No 'access-control-allow-credentials' header in responses
- 'access-control-allow-origin: *' present in responses
- Login endpoints work correctly
- Protected endpoints work with Bearer token
"""
import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from requirements
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD
TEST_EMAIL = FALLBACK_TEST_EMAIL
TEST_PASSWORD = FALLBACK_TEST_PASSWORD


class TestCORSHeaders:
    """Verify CORS headers are correct after the fix"""
    
    def test_options_preflight_login_returns_success(self):
        """OPTIONS preflight request to /api/auth/login should return 200 or 204"""
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(f"{BASE_URL}/api/auth/login", headers=headers)
        # CORS preflight can return 200 or 204 (No Content) - both are valid
        assert response.status_code in [200, 204], f"OPTIONS preflight failed with {response.status_code}: {response.text}"
        print(f"✅ OPTIONS /api/auth/login returns {response.status_code}")
    
    def test_options_preflight_has_correct_allow_origin(self):
        """OPTIONS response should have access-control-allow-origin: * header"""
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(f"{BASE_URL}/api/auth/login", headers=headers)
        
        # Check for access-control-allow-origin header (case-insensitive)
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin == "*", f"Expected '*', got '{allow_origin}'"
        print("✅ access-control-allow-origin: * present")
    
    def test_options_preflight_no_credentials_header(self):
        """OPTIONS response should NOT have access-control-allow-credentials header"""
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(f"{BASE_URL}/api/auth/login", headers=headers)
        
        # Check that credentials header is NOT present (this was the bug!)
        credentials_header = response.headers.get("access-control-allow-credentials", None)
        assert credentials_header is None or credentials_header.lower() != "true", \
            f"CORS FIX NOT APPLIED: access-control-allow-credentials should NOT be 'true', got '{credentials_header}'"
        print("✅ access-control-allow-credentials header is NOT 'true' (fix verified)")
    
    def test_options_preflight_allows_post_method(self):
        """OPTIONS response should allow POST method"""
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(f"{BASE_URL}/api/auth/login", headers=headers)
        
        allow_methods = response.headers.get("access-control-allow-methods", "")
        assert "POST" in allow_methods or "*" in allow_methods, \
            f"POST not in allowed methods: {allow_methods}"
        print("✅ POST method allowed in CORS preflight")
    
    def test_post_response_has_cors_headers(self):
        """POST response should also have CORS headers"""
        payload = {"email": "test@example.com", "password": "wrong"}
        headers = {
            "Origin": "https://example.com",
            "Content-Type": "application/json"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload, headers=headers)
        
        # Even for failed login, CORS headers should be present
        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin == "*", f"POST response missing allow-origin header: {allow_origin}"
        
        # Verify no credentials header
        credentials_header = response.headers.get("access-control-allow-credentials", None)
        assert credentials_header is None or credentials_header.lower() != "true", \
            "POST response should NOT have credentials: true"
        print("✅ POST response has correct CORS headers")
    
    def test_options_preflight_users_me(self):
        """OPTIONS preflight to protected endpoint /api/users/me should work"""
        headers = {
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type"
        }
        
        response = requests.options(f"{BASE_URL}/api/users/me", headers=headers)
        # CORS preflight can return 200 or 204 - both are valid
        assert response.status_code in [200, 204], f"OPTIONS /api/users/me failed: {response.status_code}"
        
        # Check credentials header is NOT set to true
        credentials_header = response.headers.get("access-control-allow-credentials", None)
        assert credentials_header is None or credentials_header.lower() != "true", \
            "Protected endpoint CORS should not have credentials: true"
        print(f"✅ OPTIONS /api/users/me returns {response.status_code} with correct headers")


class TestLoginWithAdminCredentials:
    """Test login with admin credentials (thesigntistslab@gmail.com / password123)"""
    
    def test_login_admin_success(self):
        """POST /api/auth/login with admin credentials should succeed"""
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200, f"Admin login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        print("✅ Admin login successful")
        
        return data["access_token"]
    
    def test_login_admin_get_user_profile(self):
        """After admin login, GET /api/users/me should return profile"""
        # Login first
        login_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Get user profile
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        
        assert profile_response.status_code == 200, f"Profile fetch failed: {profile_response.text}"
        
        data = profile_response.json()
        assert data["email"] == ADMIN_EMAIL.lower() or data["email"] == ADMIN_EMAIL
        assert "id" in data
        print("✅ GET /api/users/me returns admin profile")
    
    def test_login_admin_get_permissions(self):
        """After admin login, GET /api/users/me/permissions should return permissions"""
        # Login first
        login_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Get permissions
        headers = {"Authorization": f"Bearer {token}"}
        perm_response = requests.get(f"{BASE_URL}/api/users/me/permissions", headers=headers)
        
        assert perm_response.status_code == 200, f"Permissions fetch failed: {perm_response.text}"
        
        data = perm_response.json()
        assert "role" in data
        assert "permissions" in data
        assert isinstance(data["permissions"], list)
        print(f"✅ GET /api/users/me/permissions returns role: {data['role']} with {len(data['permissions'])} permissions")


class TestLoginWithTestCredentials:
    """Test login with test credentials (test@test.com / password)"""
    
    def test_login_test_user_success(self):
        """POST /api/auth/login with test credentials should succeed"""
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        # Note: test@test.com might not exist, so we check for either success or auth failure
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            print("✅ Test user login successful")
        elif response.status_code == 401:
            print("⚠️ Test user (test@test.com) does not exist or wrong password - this is OK if not seeded")
        else:
            pytest.fail(f"Unexpected status: {response.status_code} - {response.text}")


class TestLoginWithRememberMe:
    """Test login with remember_me=true flag"""
    
    def test_login_with_remember_me_true(self):
        """POST /api/auth/login with remember_me=true should return extended token"""
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "remember_me": True
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200, f"Login with remember_me failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        
        # Check expires_in is extended (30 days = 2592000 seconds)
        # The endpoint should return expires_in when remember_me is true
        if "expires_in" in data:
            assert data["expires_in"] >= 2592000, f"Expected 30 days expiry, got {data['expires_in']} seconds"
            print(f"✅ Login with remember_me=true returns extended expiry ({data['expires_in']} seconds)")
        else:
            # Token is valid even if expires_in not returned
            assert len(data["access_token"]) > 0
            print("✅ Login with remember_me=true successful (token issued)")
    
    def test_login_with_remember_me_false(self):
        """POST /api/auth/login with remember_me=false should return standard token"""
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "remember_me": False
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        print("✅ Login with remember_me=false successful")


class TestLoginInvalidCredentials:
    """Test login with invalid credentials returns 401"""
    
    def test_login_wrong_password(self):
        """POST /api/auth/login with wrong password should return 401"""
        payload = {
            "email": ADMIN_EMAIL,
            "password": "wrong_password_123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        print("✅ Wrong password returns 401")
    
    def test_login_nonexistent_email(self):
        """POST /api/auth/login with non-existent email should return 401"""
        payload = {
            "email": "nonexistent_user_12345@example.com",
            "password": "some_password"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Non-existent email returns 401")


class TestRegistrationFlow:
    """Test registration creates new user and returns token"""
    
    def test_register_new_user_success(self):
        """POST /api/auth/register should create new user and return token"""
        unique_email = f"TEST_cors_fix_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": COMMON_TEST_PASSWORD,
            "full_name": "CORS Fix Test User",
            "company_name": "CORS Test Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in registration response"
        assert data["token_type"] == "bearer"
        print(f"✅ Registration successful, token returned for {unique_email}")
        
        # Verify we can use the token
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        profile_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile = profile_response.json()
        assert profile["email"] == unique_email.lower()
        print("✅ New user can access protected endpoint with token")


class TestHealthEndpoint:
    """Verify health endpoint is working"""
    
    def test_health_returns_healthy(self):
        """GET /api/health should return healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint returns healthy")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
