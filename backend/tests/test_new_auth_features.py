"""
New Authentication Features Tests for Sign Guy AI
Tests: Remember Me (30-day token), Admin User Management, Magic Links, Customer Portal
"""
import pytest
import requests
import os
import uuid
import jwt
from datetime import datetime, timezone
from backend.tests.test_credentials_helper import (
    ADMIN_TEST_PASSWORD,
    MAGIC_TEST_PASSWORD,
    PORTAL_CUSTOMER_EMAIL,
    PORTAL_TEST_USER_PASSWORD,
    REMEMBER_TEST_PASSWORD,
    TARGET_TEST_PASSWORD,
    TEST_CUSTOMER_EMAIL,
    UPDATED_TEST_PASSWORD,
)

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ============== REMEMBER ME FEATURE ==============
class TestRememberMe:
    """Test Remember Me checkbox extends token to 30 days"""
    
    @pytest.fixture(autouse=True)
    def setup_test_user(self):
        """Create a test user for login tests"""
        self.test_email = f"remember_test_{uuid.uuid4().hex[:8]}@example.com"
        self.test_password = REMEMBER_TEST_PASSWORD
        
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Remember Me Test User"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create test user: {response.text}")
    
    def test_login_without_remember_me(self):
        """Test login without remember_me returns standard token expiry"""
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "remember_me": False
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data
        # Standard expiry is 24 hours = 86400 seconds
        assert data["expires_in"] == 86400, f"Expected 86400, got {data['expires_in']}"
        print(f"✅ Login without remember_me returns 24-hour token (expires_in={data['expires_in']})")
    
    def test_login_with_remember_me(self):
        """Test login with remember_me=True returns 30-day token"""
        payload = {
            "email": self.test_email,
            "password": self.test_password,
            "remember_me": True
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "expires_in" in data
        # Remember me expiry is 30 days = 30 * 24 * 60 * 60 = 2592000 seconds
        expected_expiry = 30 * 24 * 60 * 60
        assert data["expires_in"] == expected_expiry, f"Expected {expected_expiry}, got {data['expires_in']}"
        print(f"✅ Login with remember_me returns 30-day token (expires_in={data['expires_in']})")


# ============== ADMIN USER MANAGEMENT ==============
class TestAdminUserManagement:
    """Test Admin User Management features"""
    
    @pytest.fixture(autouse=True)
    def setup_admin_and_target_user(self):
        """Create admin user and target user for tests"""
        # Create admin user
        self.admin_email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
        self.admin_password = ADMIN_TEST_PASSWORD
        
        admin_payload = {
            "email": self.admin_email,
            "password": self.admin_password,
            "full_name": "Admin User",
            "company_name": "Admin Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=admin_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create admin user: {response.text}")
        self.admin_token = response.json()["access_token"]
        
        # Get admin user ID
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        me_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        self.admin_user_id = me_response.json()["id"]
        
        # Create target user
        self.target_email = f"target_{uuid.uuid4().hex[:8]}@example.com"
        self.target_password = TARGET_TEST_PASSWORD
        
        target_payload = {
            "email": self.target_email,
            "password": self.target_password,
            "full_name": "Target User",
            "company_name": "Target Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=target_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create target user: {response.text}")
        self.target_token = response.json()["access_token"]
        
        # Get target user ID
        headers = {"Authorization": f"Bearer {self.target_token}"}
        me_response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        self.target_user_id = me_response.json()["id"]
    
    def test_list_all_users(self):
        """Test GET /api/admin/users returns list of users"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
        assert response.status_code == 200, f"List users failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 2, "Should have at least 2 users (admin and target)"
        
        # Verify user structure
        user = data[0]
        assert "id" in user
        assert "email" in user
        assert "full_name" in user
        assert "is_active" in user
        assert "hashed_password" not in user, "Should not expose hashed_password"
        print(f"✅ List users returns {len(data)} users")
    
    def test_list_users_requires_auth(self):
        """Test that listing users requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/users")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ List users requires authentication")
    
    def test_admin_reset_password(self):
        """Test admin can reset another user's password"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        new_password = UPDATED_TEST_PASSWORD
        payload = {"new_password": new_password}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{self.target_user_id}/reset-password",
            headers=headers,
            json=payload
        )
        assert response.status_code == 200, f"Reset password failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "reset" in data["message"].lower() or "success" in data["message"].lower()
        
        # Verify new password works
        login_payload = {
            "email": self.target_email,
            "password": new_password
        }
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert login_response.status_code == 200, "Login with new password failed"
        print("✅ Admin password reset works and new password is valid")
    
    def test_reset_password_short_password_fails(self):
        """Test that short passwords are rejected"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        payload = {"new_password": "12345"}  # Less than 6 characters
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{self.target_user_id}/reset-password",
            headers=headers,
            json=payload
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✅ Short password correctly rejected")
    
    def test_reset_password_nonexistent_user(self):
        """Test reset password for non-existent user fails"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        payload = {"new_password": UPDATED_TEST_PASSWORD}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/nonexistent-user-id/reset-password",
            headers=headers,
            json=payload
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Reset password for non-existent user correctly returns 404")
    
    def test_admin_disable_user(self):
        """Test admin can disable another user's account"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.target_user_id}/status?is_active=false",
            headers=headers
        )
        assert response.status_code == 200, f"Disable user failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "disabled" in data["message"].lower()
        
        # Verify user is disabled - login should fail
        login_payload = {
            "email": self.target_email,
            "password": self.target_password
        }
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert login_response.status_code == 400, f"Disabled user should not be able to login, got {login_response.status_code}"
        print("✅ Admin can disable user and disabled user cannot login")
    
    def test_admin_enable_user(self):
        """Test admin can enable a disabled user's account"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # First disable the user
        requests.put(
            f"{BASE_URL}/api/admin/users/{self.target_user_id}/status?is_active=false",
            headers=headers
        )
        
        # Then enable the user
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.target_user_id}/status?is_active=true",
            headers=headers
        )
        assert response.status_code == 200, f"Enable user failed: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "enabled" in data["message"].lower()
        
        # Verify user can login again
        login_payload = {
            "email": self.target_email,
            "password": self.target_password
        }
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        assert login_response.status_code == 200, "Enabled user should be able to login"
        print("✅ Admin can enable user and enabled user can login")
    
    def test_admin_cannot_disable_own_account(self):
        """Test admin cannot disable their own account"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/admin/users/{self.admin_user_id}/status?is_active=false",
            headers=headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        data = response.json()
        assert "detail" in data
        assert "own" in data["detail"].lower() or "cannot" in data["detail"].lower()
        print("✅ Admin cannot disable their own account")


# ============== MAGIC LINKS ==============
class TestMagicLinks:
    """Test Magic Link generation and customer portal access"""
    
    @pytest.fixture(autouse=True)
    def setup_user_and_quote(self):
        """Create user, customer, and quote for magic link tests"""
        # Create user
        self.user_email = f"magic_test_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = MAGIC_TEST_PASSWORD
        
        user_payload = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Magic Link Test User"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create user: {response.text}")
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create customer
        customer_payload = {
            "name": "Test Customer",
            "email": TEST_CUSTOMER_EMAIL,
            "phone": "555-1234",
            "company": "Test Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create customer: {response.text}")
        self.customer_id = response.json()["id"]
        
        # Create quote
        quote_payload = {
            "customer_id": self.customer_id,
            "line_items": [
                {"description": "Test Sign", "quantity": 2, "unit_price": 100.00}
            ],
            "notes": "Test quote for magic link",
            "status": "draft"
        }
        
        response = requests.post(f"{BASE_URL}/api/quotes", json=quote_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create quote: {response.text}")
        self.quote_id = response.json()["id"]
    
    def test_create_magic_link_for_quote(self):
        """Test creating a magic link for a quote"""
        payload = {
            "resource_type": "quote",
            "resource_id": self.quote_id,
            "customer_email": TEST_CUSTOMER_EMAIL,
            "expires_in_days": 7
        }
        
        response = requests.post(
            f"{BASE_URL}/api/magic-links",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 200, f"Create magic link failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "token" in data
        assert data["resource_type"] == "quote"
        assert data["resource_id"] == self.quote_id
        assert "expires_at" in data
        assert len(data["token"]) > 20, "Token should be a secure random string"
        
        self.magic_link_token = data["token"]
        print(f"✅ Magic link created with token: {data['token'][:20]}...")
        return data
    
    def test_create_magic_link_requires_auth(self):
        """Test that creating magic links requires authentication"""
        payload = {
            "resource_type": "quote",
            "resource_id": self.quote_id,
            "expires_in_days": 7
        }
        
        response = requests.post(f"{BASE_URL}/api/magic-links", json=payload)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Creating magic links requires authentication")
    
    def test_create_magic_link_invalid_resource(self):
        """Test creating magic link for non-existent resource fails"""
        payload = {
            "resource_type": "quote",
            "resource_id": "nonexistent-quote-id",
            "expires_in_days": 7
        }
        
        response = requests.post(
            f"{BASE_URL}/api/magic-links",
            headers=self.headers,
            json=payload
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Magic link for non-existent resource correctly returns 404")
    
    def test_access_portal_via_magic_link(self):
        """Test accessing customer portal via magic link (public endpoint)"""
        # First create a magic link
        create_payload = {
            "resource_type": "quote",
            "resource_id": self.quote_id,
            "expires_in_days": 7
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/magic-links",
            headers=self.headers,
            json=create_payload
        )
        assert create_response.status_code == 200
        magic_token = create_response.json()["token"]
        
        # Access portal without authentication (public endpoint)
        response = requests.get(f"{BASE_URL}/api/portal/{magic_token}")
        assert response.status_code == 200, f"Portal access failed: {response.text}"
        
        data = response.json()
        assert data["resource_type"] == "quote"
        assert "resource" in data
        assert "customer" in data
        assert "link_expires_at" in data
        
        # Verify quote data
        assert data["resource"]["id"] == self.quote_id
        assert len(data["resource"]["line_items"]) > 0
        print("✅ Customer portal accessible via magic link without authentication")
    
    def test_portal_invalid_token(self):
        """Test accessing portal with invalid token fails"""
        response = requests.get(f"{BASE_URL}/api/portal/invalid-token-here")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✅ Invalid magic link token correctly returns 404")
    
    def test_list_magic_links(self):
        """Test listing magic links"""
        # Create a magic link first
        create_payload = {
            "resource_type": "quote",
            "resource_id": self.quote_id,
            "expires_in_days": 7
        }
        requests.post(f"{BASE_URL}/api/magic-links", headers=self.headers, json=create_payload)
        
        # List magic links
        response = requests.get(f"{BASE_URL}/api/magic-links", headers=self.headers)
        assert response.status_code == 200, f"List magic links failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"✅ List magic links returns {len(data)} links")
    
    def test_list_magic_links_filtered(self):
        """Test listing magic links with filters"""
        # Create a magic link first
        create_payload = {
            "resource_type": "quote",
            "resource_id": self.quote_id,
            "expires_in_days": 7
        }
        requests.post(f"{BASE_URL}/api/magic-links", headers=self.headers, json=create_payload)
        
        # List with filter
        response = requests.get(
            f"{BASE_URL}/api/magic-links?resource_type=quote&resource_id={self.quote_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        
        data = response.json()
        for link in data:
            assert link["resource_type"] == "quote"
            assert link["resource_id"] == self.quote_id
        print("✅ Magic links filtering works")
    
    def test_revoke_magic_link(self):
        """Test revoking/deleting a magic link"""
        # Create a magic link
        create_payload = {
            "resource_type": "quote",
            "resource_id": self.quote_id,
            "expires_in_days": 7
        }
        create_response = requests.post(
            f"{BASE_URL}/api/magic-links",
            headers=self.headers,
            json=create_payload
        )
        link_id = create_response.json()["id"]
        magic_token = create_response.json()["token"]
        
        # Revoke the link
        response = requests.delete(
            f"{BASE_URL}/api/magic-links/{link_id}",
            headers=self.headers
        )
        assert response.status_code == 200, f"Revoke magic link failed: {response.text}"
        
        # Verify link no longer works
        portal_response = requests.get(f"{BASE_URL}/api/portal/{magic_token}")
        assert portal_response.status_code == 404, "Revoked link should not work"
        print("✅ Magic link revocation works")


# ============== CUSTOMER PORTAL ==============
class TestCustomerPortal:
    """Test Customer Portal page functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_resources(self):
        """Create user, customer, quote, job, and invoice for portal tests"""
        # Create user
        self.user_email = f"portal_test_{uuid.uuid4().hex[:8]}@example.com"
        self.user_password = PORTAL_TEST_USER_PASSWORD
        
        user_payload = {
            "email": self.user_email,
            "password": self.user_password,
            "full_name": "Portal Test User"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create user: {response.text}")
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create customer
        customer_payload = {
            "name": "Portal Customer",
            "email": PORTAL_CUSTOMER_EMAIL,
            "phone": "555-5678",
            "company": "Portal Company"
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create customer: {response.text}")
        self.customer_id = response.json()["id"]
        
        # Create quote
        quote_payload = {
            "customer_id": self.customer_id,
            "line_items": [
                {"description": "Banner Sign", "quantity": 1, "unit_price": 250.00},
                {"description": "Installation", "quantity": 1, "unit_price": 75.00}
            ],
            "notes": "Portal test quote",
            "status": "sent"
        }
        
        response = requests.post(f"{BASE_URL}/api/quotes", json=quote_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create quote: {response.text}")
        self.quote_id = response.json()["id"]
        
        # Create job
        job_payload = {
            "customer_id": self.customer_id,
            "name": "Portal Test Job",
            "description": "Test job for portal",
            "status": "in_production"
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create job: {response.text}")
        self.job_id = response.json()["id"]
        
        # Create invoice
        invoice_payload = {
            "customer_id": self.customer_id,
            "job_id": self.job_id,
            "line_items": [
                {"description": "Banner Sign", "quantity": 1, "unit_price": 250.00, "total": 250.00}
            ],
            "total": 250.00,
            "status": "sent"
        }
        
        response = requests.post(f"{BASE_URL}/api/invoices", json=invoice_payload)
        if response.status_code != 200:
            pytest.skip(f"Could not create invoice: {response.text}")
        self.invoice_id = response.json()["id"]
    
    def test_portal_shows_quote_details(self):
        """Test portal shows quote details correctly"""
        # Create magic link for quote
        create_payload = {
            "resource_type": "quote",
            "resource_id": self.quote_id,
            "expires_in_days": 7
        }
        create_response = requests.post(
            f"{BASE_URL}/api/magic-links",
            headers=self.headers,
            json=create_payload
        )
        magic_token = create_response.json()["token"]
        
        # Access portal
        response = requests.get(f"{BASE_URL}/api/portal/{magic_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["resource_type"] == "quote"
        assert data["resource"]["id"] == self.quote_id
        assert len(data["resource"]["line_items"]) == 2
        assert data["resource"]["total"] == 325.00  # 250 + 75
        assert data["customer"]["name"] == "Portal Customer"
        print("✅ Portal shows quote details correctly")
    
    def test_portal_shows_job_details(self):
        """Test portal shows job details correctly"""
        # Create magic link for job
        create_payload = {
            "resource_type": "job",
            "resource_id": self.job_id,
            "expires_in_days": 7
        }
        create_response = requests.post(
            f"{BASE_URL}/api/magic-links",
            headers=self.headers,
            json=create_payload
        )
        magic_token = create_response.json()["token"]
        
        # Access portal
        response = requests.get(f"{BASE_URL}/api/portal/{magic_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["resource_type"] == "job"
        assert data["resource"]["id"] == self.job_id
        assert data["resource"]["name"] == "Portal Test Job"
        assert data["customer"]["name"] == "Portal Customer"
        print("✅ Portal shows job details correctly")
    
    def test_portal_shows_invoice_details(self):
        """Test portal shows invoice details correctly"""
        # Create magic link for invoice
        create_payload = {
            "resource_type": "invoice",
            "resource_id": self.invoice_id,
            "expires_in_days": 7
        }
        create_response = requests.post(
            f"{BASE_URL}/api/magic-links",
            headers=self.headers,
            json=create_payload
        )
        magic_token = create_response.json()["token"]
        
        # Access portal
        response = requests.get(f"{BASE_URL}/api/portal/{magic_token}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["resource_type"] == "invoice"
        assert data["resource"]["id"] == self.invoice_id
        assert data["resource"]["total"] == 250.00
        assert data["customer"]["name"] == "Portal Customer"
        print("✅ Portal shows invoice details correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
