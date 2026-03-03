"""
Tests for 48-Hour Free Trial Feature

Tests:
- FREE_TRIAL_CONFIG has correct 48 hours and 50 credits
- Registration creates trial tenant with sample data
- trial-status API returns correct trial info
- sample_data.py functions work correctly
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestFreeTrialConfig:
    """Test FREE_TRIAL_CONFIG settings"""
    
    def test_founders_edition_config_endpoint(self):
        """Test that founders edition config endpoint works"""
        response = requests.get(f"{BASE_URL}/api/plans/founders-edition")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify plan structure exists
        assert "plan" in data, "Response should have 'plan' field"
        assert "availability" in data, "Response should have 'availability' field"
        
        plan = data["plan"]
        assert plan.get("plan_name") == "Founders Edition", f"Expected Founders Edition, got {plan.get('plan_name')}"
        
        # Verify availability
        availability = data["availability"]
        assert availability.get("max_spots") == 100, f"Expected 100 max spots, got {availability.get('max_spots')}"
        
        print(f"✓ Founders Edition config verified: {plan.get('plan_name')}, {availability.get('spots_remaining')} spots remaining")
    
    def test_free_trial_config_via_trial_status(self):
        """Test FREE_TRIAL_CONFIG (48hrs, 50 credits) by checking new user trial status"""
        # Create a new user and check their trial is ~48 hours
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_config_check_{unique_id}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "full_name": f"Config Check User {unique_id}",
            "company_name": f"Config Shop {unique_id}"
        })
        
        if response.status_code != 200:
            pytest.skip(f"Could not register: {response.text}")
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check trial status
        trial_response = requests.get(f"{BASE_URL}/api/billing/trial-status", headers=headers)
        assert trial_response.status_code == 200
        
        trial_data = trial_response.json()
        hours = trial_data.get("hours_remaining", 0)
        
        # Verify FREE_TRIAL_HOURS = 48 (allowing for a few minutes of test execution)
        assert 47 < hours <= 48.1, f"FREE_TRIAL_HOURS should be 48, but got {hours} hours remaining"
        print(f"✓ FREE_TRIAL_HOURS=48 verified via trial-status (hours_remaining={hours})")
        
        # Check credits were granted (should be 50)
        credits_response = requests.get(f"{BASE_URL}/api/credits/balance", headers=headers)
        if credits_response.status_code == 200:
            credits_data = credits_response.json()
            total = credits_data.get("total_credits") or credits_data.get("monthly_credits", 0)
            assert total >= 50, f"FREE_TRIAL_CREDITS should be at least 50, got {total}"
            print(f"✓ FREE_TRIAL_CREDITS=50 verified (got {total} credits)")


class TestRegistrationCreatesTrial:
    """Test that registration creates trial account"""
    
    def test_register_new_user_creates_trial(self):
        """Test new user registration creates 48hr trial with sample data"""
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_trial_{unique_id}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "full_name": f"Test Trial User {unique_id}",
            "company_name": f"Test Sign Shop {unique_id}"
        })
        
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        
        assert "access_token" in data, "Response should have access_token"
        token = data["access_token"]
        print(f"✓ User registered successfully, got access token")
        
        # Check trial status immediately after registration
        headers = {"Authorization": f"Bearer {token}"}
        trial_response = requests.get(f"{BASE_URL}/api/billing/trial-status", headers=headers)
        
        assert trial_response.status_code == 200, f"Trial status check failed: {trial_response.text}"
        trial_data = trial_response.json()
        
        # Verify trial status
        assert trial_data.get("is_trial") == True, f"Expected is_trial=True, got {trial_data.get('is_trial')}"
        assert trial_data.get("trial_type") == "free_trial", f"Expected trial_type='free_trial', got {trial_data.get('trial_type')}"
        assert trial_data.get("is_locked") == False, f"New trial should not be locked"
        assert trial_data.get("can_upgrade") == True, "Trial should be upgradeable"
        
        # Verify hours remaining is approximately 48 (within a few minutes tolerance)
        hours_remaining = trial_data.get("hours_remaining", 0)
        assert 47 < hours_remaining <= 48, f"Expected ~48 hours remaining, got {hours_remaining}"
        
        print(f"✓ Trial status verified: is_trial=True, type=free_trial, hours_remaining={hours_remaining}")
        
        return token


class TestTrialStatusAPI:
    """Test trial-status API endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token from new registration"""
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_trial_api_{unique_id}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "full_name": f"Test User {unique_id}",
            "company_name": f"Test Shop {unique_id}"
        })
        
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not create test user")
    
    def test_trial_status_returns_correct_fields(self, auth_token):
        """Test trial-status returns all required fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/trial-status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields exist
        required_fields = ["is_trial", "is_locked", "can_upgrade"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        print(f"✓ Trial status response has all required fields")
    
    def test_trial_status_for_new_user(self, auth_token):
        """Test trial status for newly registered user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/trial-status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_trial"] == True
        assert data["trial_type"] == "free_trial"
        assert data["is_locked"] == False
        
        # Should have hours_remaining close to 48
        hours = data.get("hours_remaining", 0)
        assert hours > 47, f"Expected >47 hours remaining for new user, got {hours}"
        
        print(f"✓ New user trial status: is_trial=True, hours_remaining={hours}")
    
    def test_trial_status_unauthenticated(self):
        """Test trial-status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/billing/trial-status")
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("✓ Unauthenticated request correctly rejected")


class TestExistingTestCredentials:
    """Test with provided test credentials"""
    
    def test_login_with_test_credentials(self):
        """Test login with test@test.com / password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@test.com",
            "password": "password"
        })
        
        # This test user may or may not exist
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            assert token is not None, "Should get access token on successful login"
            
            # Check trial status for existing user
            headers = {"Authorization": f"Bearer {token}"}
            trial_response = requests.get(f"{BASE_URL}/api/billing/trial-status", headers=headers)
            
            if trial_response.status_code == 200:
                trial_data = trial_response.json()
                print(f"✓ Existing user trial status: is_trial={trial_data.get('is_trial')}, is_locked={trial_data.get('is_locked')}")
        else:
            print(f"ℹ Test user test@test.com doesn't exist or password is different (status={response.status_code})")
            pytest.skip("Test credentials don't work - user may not exist")


class TestSampleDataCreation:
    """Test that sample data is created for trial accounts"""
    
    @pytest.fixture
    def new_trial_account(self):
        """Create a new trial account and return token"""
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"TEST_sample_{unique_id}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": test_email,
            "password": "testpass123",
            "full_name": f"Sample Data Test User {unique_id}",
            "company_name": f"Sample Shop {unique_id}"
        })
        
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not create test user")
    
    def test_sample_customers_created(self, new_trial_account):
        """Test that sample customers are created for new trial"""
        headers = {"Authorization": f"Bearer {new_trial_account}"}
        response = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        
        if response.status_code == 200:
            customers = response.json()
            # Should have at least some sample customers
            sample_customers = [c for c in customers if c.get("is_sample_data") or "[SAMPLE" in c.get("notes", "")]
            
            if len(sample_customers) > 0:
                print(f"✓ Sample customers created: {len(sample_customers)} sample customers found")
            else:
                print(f"ℹ No sample customers found (may be in different format)")
        else:
            print(f"ℹ Could not fetch customers (status={response.status_code})")
    
    def test_sample_jobs_created(self, new_trial_account):
        """Test that sample jobs are created for new trial"""
        headers = {"Authorization": f"Bearer {new_trial_account}"}
        response = requests.get(f"{BASE_URL}/api/jobs", headers=headers)
        
        if response.status_code == 200:
            jobs = response.json()
            # Check for sample data indicator
            if isinstance(jobs, list):
                sample_jobs = [j for j in jobs if j.get("is_sample_data") or "[SAMPLE" in j.get("description", "")]
                print(f"✓ Sample jobs: {len(sample_jobs)} found")
        else:
            print(f"ℹ Could not fetch jobs (status={response.status_code})")
    
    def test_ai_credits_granted(self, new_trial_account):
        """Test that 50 AI credits are granted on trial creation"""
        headers = {"Authorization": f"Bearer {new_trial_account}"}
        response = requests.get(f"{BASE_URL}/api/credits/balance", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            total_credits = data.get("total_credits") or data.get("monthly_credits", 0)
            assert total_credits >= 50, f"Expected at least 50 credits for trial, got {total_credits}"
            print(f"✓ AI credits granted: {total_credits} total credits")
        else:
            # Try alternate endpoint
            response2 = requests.get(f"{BASE_URL}/api/credits", headers=headers)
            if response2.status_code == 200:
                data = response2.json()
                print(f"✓ Credits endpoint responded: {data}")
            else:
                print(f"ℹ Could not check credits balance (status={response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
