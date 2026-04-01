"""
Bug Fixes Testing - Iteration 22
Testing:
1. User can access Payroll page (tier upgraded to Business)
2. User can access Financials page (tier upgraded to Business) 
3. Pricing calculator complexity slider affects price
4. Setup fee is charged once per order (not multiplied by quantity)
5. AI Tools API endpoints work
"""

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = SYNTHETIC_OWNER_EMAIL
TEST_PASSWORD = "test123456"


class TestAuthentication:
    """Test login and get auth token"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Test that login works"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✅ Login successful, got token")
    
    def test_get_user_profile(self, auth_token):
        """Test getting user profile"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/users/me", headers=headers)
        assert response.status_code == 200
        user = response.json()
        assert user["email"] == TEST_EMAIL
        print(f"✅ User profile: {user['full_name']} ({user['role']})")
        return user


class TestTierUpgrade:
    """Test that user's tier is Business"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_tenant_tier_is_business(self, auth_token):
        """Check that tenant tier is business"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/tiers/current", headers=headers)
        assert response.status_code == 200
        tier_data = response.json()
        print(f"✅ Current tier: {tier_data}")
        # Check tier is business
        tier = tier_data.get("tier") or tier_data.get("plan")
        assert tier in ["business", "Business"], f"Expected business tier, got: {tier}"
        print(f"✅ Tenant has Business tier: {tier}")


class TestPayrollAccess:
    """Test Payroll page access (requires Business tier)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_payroll_employees_endpoint(self, auth_token):
        """Test employees endpoint for payroll"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/employees", headers=headers)
        # Should be accessible with Business tier
        assert response.status_code == 200, f"Employees endpoint failed: {response.status_code} - {response.text}"
        print(f"✅ Employees endpoint accessible: {len(response.json())} employees")
    
    def test_payroll_transactions_endpoint(self, auth_token):
        """Test payroll transactions endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/transactions", headers=headers)
        assert response.status_code == 200, f"Payroll transactions failed: {response.status_code} - {response.text}"
        print(f"✅ Payroll transactions accessible")
    
    def test_payroll_report_endpoint(self, auth_token):
        """Test payroll report endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/report?start_date=2025-01-01&end_date=2025-12-31", headers=headers)
        assert response.status_code == 200, f"Payroll report failed: {response.status_code} - {response.text}"
        print(f"✅ Payroll report accessible")


class TestFinancialsAccess:
    """Test Financials page access (requires Business tier)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_sales_entries_endpoint(self, auth_token):
        """Test sales entries endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/financials/sales", headers=headers)
        assert response.status_code == 200, f"Sales entries failed: {response.status_code} - {response.text}"
        print(f"✅ Sales entries accessible")
    
    def test_expense_entries_endpoint(self, auth_token):
        """Test expense entries endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/financials/expenses", headers=headers)
        assert response.status_code == 200, f"Expense entries failed: {response.status_code} - {response.text}"
        print(f"✅ Expense entries accessible")
    
    def test_financial_summary_endpoint(self, auth_token):
        """Test financial summary endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/financials/summary?start_date=2025-01-01&end_date=2025-12-31", headers=headers)
        assert response.status_code == 200, f"Financial summary failed: {response.status_code} - {response.text}"
        print(f"✅ Financial summary accessible")


class TestPricingCalculator:
    """Test pricing calculator - complexity slider and setup fee"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_complexity_affects_price_digital_print(self, auth_token):
        """Test that complexity slider affects digital print pricing"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Calculate with complexity 1
        response_low = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 36,
                "print_material": "banner_13oz",
                "complexity": 1
            },
            "quantity": 1
        })
        assert response_low.status_code == 200, f"Pricing calc failed: {response_low.text}"
        price_low = response_low.json()["suggested_price"]
        
        # Calculate with complexity 5
        response_high = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 36,
                "print_material": "banner_13oz",
                "complexity": 5
            },
            "quantity": 1
        })
        assert response_high.status_code == 200
        price_high = response_high.json()["suggested_price"]
        
        print(f"Price with complexity 1: ${price_low}")
        print(f"Price with complexity 5: ${price_high}")
        
        # Higher complexity should result in higher price
        assert price_high > price_low, f"Complexity should affect price! Low: {price_low}, High: {price_high}"
        print(f"✅ Complexity affects price: ${price_low} (complexity 1) vs ${price_high} (complexity 5)")
    
    def test_complexity_affects_price_rigid_signs(self, auth_token):
        """Test that complexity slider affects rigid signs pricing"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        # Calculate with complexity 1
        response_low = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "category": "rigid_signs",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 18,
                "substrate_type": "coroplast_4mm",
                "complexity": 1
            },
            "quantity": 1
        })
        assert response_low.status_code == 200
        price_low = response_low.json()["suggested_price"]
        
        # Calculate with complexity 5
        response_high = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "category": "rigid_signs",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 18,
                "substrate_type": "coroplast_4mm",
                "complexity": 5
            },
            "quantity": 1
        })
        assert response_high.status_code == 200
        price_high = response_high.json()["suggested_price"]
        
        print(f"Rigid sign price with complexity 1: ${price_low}")
        print(f"Rigid sign price with complexity 5: ${price_high}")
        
        assert price_high > price_low, f"Complexity should affect rigid sign price!"
        print(f"✅ Rigid signs complexity works: ${price_low} vs ${price_high}")
    
    def test_setup_fee_not_multiplied_by_quantity(self, auth_token):
        """Test that setup fee is charged once per order, not multiplied by quantity"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        
        setup_fee = 25.0
        
        # Calculate with quantity 1
        response_qty1 = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 36,
                "print_material": "banner_13oz",
                "setup_fee": setup_fee,
                "complexity": 1
            },
            "quantity": 1
        })
        assert response_qty1.status_code == 200
        data_qty1 = response_qty1.json()
        setup_cost_qty1 = data_qty1.get("setup_cost", 0)
        
        # Calculate with quantity 10
        response_qty10 = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=headers, json={
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 36,
                "print_material": "banner_13oz",
                "setup_fee": setup_fee,
                "complexity": 1
            },
            "quantity": 10
        })
        assert response_qty10.status_code == 200
        data_qty10 = response_qty10.json()
        setup_cost_qty10 = data_qty10.get("setup_cost", 0)
        
        print(f"Setup cost with qty 1: ${setup_cost_qty1}")
        print(f"Setup cost with qty 10: ${setup_cost_qty10}")
        
        # Setup fee should be the same regardless of quantity (once per order)
        assert setup_cost_qty1 == setup_cost_qty10, f"Setup fee should not multiply! Qty 1: {setup_cost_qty1}, Qty 10: {setup_cost_qty10}"
        assert setup_cost_qty1 == setup_fee, f"Setup cost should equal setup fee: {setup_cost_qty1} != {setup_fee}"
        print(f"✅ Setup fee charged once: ${setup_cost_qty1} for qty 1, ${setup_cost_qty10} for qty 10")


class TestAITools:
    """Test AI Tools endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_ai_history_endpoint(self, auth_token):
        """Test AI history endpoint is accessible"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/ai/history", headers=headers)
        assert response.status_code == 200, f"AI history failed: {response.status_code} - {response.text}"
        print(f"✅ AI history endpoint accessible")
    
    def test_ai_generate_tagline(self, auth_token):
        """Test AI tagline generation (text tool)"""
        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/api/ai/generate", headers=headers, json={
            "tool": "tagline_generator",
            "input_data": {
                "business_name": "Test Shop",
                "industry": "Signs",
                "key_values": "Quality, Fast, Reliable",
                "target_audience": "Small businesses",
                "tone": "professional"
            }
        }, timeout=60)  # AI calls can take time
        
        # If AI service is configured, should return 200
        # If not configured, might return 500 with "AI service not configured"
        if response.status_code == 500 and "not configured" in response.text.lower():
            print(f"⚠️ AI service not configured (expected if no API key)")
            pytest.skip("AI service not configured")
        
        assert response.status_code == 200, f"AI generate failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "content" in data, "Response should have content"
        print(f"✅ AI tagline generation works, content length: {len(data.get('content', ''))}")


class TestJobsEndpoints:
    """Test Jobs endpoints for row click functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_jobs_list_endpoint(self, auth_token):
        """Test jobs list endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/jobs", headers=headers)
        assert response.status_code == 200, f"Jobs list failed: {response.status_code}"
        jobs = response.json()
        print(f"✅ Jobs list accessible: {len(jobs)} jobs")
        return jobs
    
    def test_job_details_endpoint(self, auth_token):
        """Test that job details endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        # First get list of jobs
        response = requests.get(f"{BASE_URL}/api/jobs", headers=headers)
        assert response.status_code == 200
        jobs = response.json()
        
        if len(jobs) > 0:
            job_id = jobs[0]["id"]
            # Get job details
            response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=headers)
            assert response.status_code == 200, f"Job details failed: {response.status_code}"
            details = response.json()
            assert "job" in details
            print(f"✅ Job details accessible: {details['job']['name']}")
        else:
            print("⚠️ No jobs to test details endpoint")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
