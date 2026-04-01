"""
Authentication System Tests for Sign Guy AI
Tests: Registration, Login, JWT Token, Protected Routes, Error Handling
"""
import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")


class TestUserRegistration:
    """User registration flow tests"""
    
    def test_register_new_user_success(self):
        """Test successful user registration with all fields"""
        unique_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": COMMON_TEST_PASSWORD,
            "full_name": "Test User",
            "company_name": "Test Sign Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        print(f"✅ User registration successful for {unique_email}")
        
        # Return token for cleanup or further tests
        return data["access_token"]
    
    def test_register_without_company_name(self):
        """Test registration without optional company name"""
        unique_email = f"test_nocompany_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": COMMON_TEST_PASSWORD,
            "full_name": "No Company User"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        print("✅ Registration without company name successful")
    
    def test_register_duplicate_email_fails(self):
        """Test that duplicate email registration fails"""
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@example.com"
        payload = {
            "email": unique_email,
            "password": COMMON_TEST_PASSWORD,
            "full_name": "First User"
        }
        
        # First registration should succeed
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response1.status_code == 200
        
        # Second registration with same email should fail
        payload["full_name"] = "Second User"
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response2.status_code == 400, f"Expected 400, got {response2.status_code}"
        
        data = response2.json()
        assert "detail" in data
        assert "already registered" in data["detail"].lower() or "email" in data["detail"].lower()
        print("✅ Duplicate email registration correctly rejected")
    
    def test_register_invalid_email_format(self):
        """Test registration with invalid email format"""
        payload = {
            "email": "not-an-email",
            "password": COMMON_TEST_PASSWORD,
            "full_name": "Invalid Email User"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"
        print("✅ Invalid email format correctly rejected")
    
    def test_register_missing_required_fields(self):
        """Test registration with missing required fields"""
        # Missing password
        payload = {
            "email": "test@example.com",
            "full_name": "Missing Password"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 422
        
        # Missing full_name
        payload = {
            "email": "test@example.com",
            "password": COMMON_TEST_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 422
        print("✅ Missing required fields correctly rejected")


class TestUserLogin:
    """User login flow tests"""
    
    @pytest.fixture(autouse=True)
    def setup_test_user(self):
        """Create a test user for login tests"""
        self.test_email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "LoginTest123!"
        
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Login Test User",
            "company_name": "Login Test Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            self.registration_token = response.json()["access_token"]
        else:
            pytest.skip(f"Could not create test user: {response.text}")
    
    def test_login_success(self):
        """Test successful login with valid credentials"""
        payload = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        print(f"✅ Login successful for {self.test_email}")
    
    def test_login_wrong_password(self):
        """Test login with wrong password"""
        payload = {
            "email": self.test_email,
            "password": "WrongPassword123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or FALLBACK_TEST_PASSWORD in data["detail"].lower()
        print("✅ Wrong password correctly rejected")
    
    def test_login_nonexistent_email(self):
        """Test login with non-existent email"""
        payload = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        print("✅ Non-existent email correctly rejected")
    
    def test_login_case_insensitive_email(self):
        """Test that email login is case-insensitive"""
        # Login with uppercase email
        payload = {
            "email": self.test_email.upper(),
            "password": self.test_password
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200, f"Case-insensitive login failed: {response.text}"
        print("✅ Case-insensitive email login works")


class TestJWTTokenValidation:
    """JWT token generation and validation tests"""
    
    @pytest.fixture(autouse=True)
    def setup_authenticated_user(self):
        """Create and login a test user"""
        self.test_email = f"jwt_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "JWTTest123!"
        
        # Register
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "JWT Test User",
            "company_name": "JWT Test Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            pytest.skip(f"Could not create test user: {response.text}")
    
    def test_get_current_user_with_valid_token(self):
        """Test /users/me endpoint with valid token"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.status_code == 200, f"Get user failed: {response.text}"
        
        data = response.json()
        assert data["email"] == self.test_email.lower()
        assert data["full_name"] == "JWT Test User"
        assert data["company_name"] == "JWT Test Company"
        assert data["is_active"]
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data  # Should not expose password
        print("✅ Get current user with valid token works")
    
    def test_get_current_user_without_token(self):
        """Test /users/me endpoint without token"""
        response = requests.get(f"{BASE_URL}/api/users/me")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Unauthorized access correctly rejected")
    
    def test_get_current_user_with_invalid_token(self):
        """Test /users/me endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token_here"}
        
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Invalid token correctly rejected")
    
    def test_get_current_user_with_malformed_header(self):
        """Test /users/me endpoint with malformed auth header"""
        headers = {"Authorization": "NotBearer sometoken"}
        
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Malformed auth header correctly rejected")


class TestProtectedRoutes:
    """Test that protected routes require authentication"""
    
    @pytest.fixture(autouse=True)
    def setup_authenticated_user(self):
        """Create and login a test user"""
        self.test_email = f"protected_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "ProtectedTest123!"
        
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Protected Test User"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            pytest.skip(f"Could not create test user: {response.text}")
    
    def test_users_me_requires_auth(self):
        """Test that /users/me requires authentication"""
        # Without token
        response = requests.get(f"{BASE_URL}/api/users/me")
        assert response.status_code == 401
        
        # With token
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.status_code == 200
        print("✅ /users/me correctly requires authentication")
    
    def test_update_profile_requires_auth(self):
        """Test that PUT /users/me requires authentication"""
        # Without token
        response = requests.put(f"{BASE_URL}/api/users/me?full_name=Updated")
        assert response.status_code == 401
        
        # With token
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.put(f"{BASE_URL}/api/users/me?full_name=Updated", headers=headers)
        assert response.status_code == 200
        print("✅ PUT /users/me correctly requires authentication")


class TestUserProfileUpdate:
    """Test user profile update functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_authenticated_user(self):
        """Create and login a test user"""
        self.test_email = f"update_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = "UpdateTest123!"
        
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Original Name",
            "company_name": "Original Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            pytest.skip(f"Could not create test user: {response.text}")
    
    def test_update_full_name(self):
        """Test updating user's full name"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/users/me?full_name=Updated Name",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "Updated Name"
        
        # Verify persistence with GET
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.json()["full_name"] == "Updated Name"
        print("✅ Full name update works and persists")
    
    def test_update_company_name(self):
        """Test updating user's company name"""
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/users/me?company_name=New Company",
            headers=headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["company_name"] == "New Company"
        print("✅ Company name update works")


class TestPublicEndpoints:
    """Test that public endpoints don't require authentication"""
    
    def test_health_is_public(self):
        """Test that health endpoint is public"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✅ Health endpoint is public")
    
    def test_root_is_public(self):
        """Test that root API endpoint is public"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "Sign Guy AI" in data.get("message", "")
        print("✅ Root API endpoint is public")
    
    def test_register_is_public(self):
        """Test that register endpoint is public (no auth required)"""
        # Just check it doesn't return 401
        response = requests.post(f"{BASE_URL}/api/auth/register", json={})
        assert response.status_code != 401  # Should be 422 for validation error
        print("✅ Register endpoint is public")
    
    def test_login_is_public(self):
        """Test that login endpoint is public (no auth required)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={})
        assert response.status_code != 401  # Should be 422 for validation error
        print("✅ Login endpoint is public")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
