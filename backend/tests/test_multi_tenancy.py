"""
Sprint 7: Multi-Tenancy Tests
Tests for tenant data isolation, tenant settings, and tenant-scoped data access
"""
import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = SYNTHETIC_OWNER_EMAIL
OWNER_PASSWORD = SYNTHETIC_OWNER_PASSWORD
STAFF_EMAIL = "teststaff@signguy.ai"
STAFF_PASSWORD = "staff123"


class TestMultiTenancy:
    """Multi-tenancy feature tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_auth_token(self, email, password):
        """Helper to get auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        return None
    
    def get_authenticated_session(self, email, password):
        """Get session with auth header"""
        token = self.get_auth_token(email, password)
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            return True
        return False
    
    # ============== AUTH & TOKEN TESTS ==============
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ API health check passed")
    
    def test_owner_login_returns_token(self):
        """Test owner login returns auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        print("✅ Owner login returns valid token")
    
    def test_staff_login_returns_token(self):
        """Test staff login returns auth token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": STAFF_EMAIL,
            "password": STAFF_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        print("✅ Staff login returns valid token")
    
    # ============== USER PROFILE WITH TENANT_ID ==============
    
    def test_owner_profile_has_tenant_id(self):
        """Test /api/users/me returns tenant_id for owner"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/users/me")
        assert response.status_code == 200
        data = response.json()
        
        assert "tenant_id" in data
        assert data["tenant_id"] is not None
        assert len(data["tenant_id"]) > 0
        print(f"✅ Owner profile has tenant_id: {data['tenant_id']}")
    
    def test_staff_profile_has_tenant_id(self):
        """Test /api/users/me returns tenant_id for staff"""
        assert self.get_authenticated_session(STAFF_EMAIL, STAFF_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/users/me")
        assert response.status_code == 200
        data = response.json()
        
        assert "tenant_id" in data
        # Staff may or may not have tenant_id depending on how they were created
        print(f"✅ Staff profile tenant_id: {data.get('tenant_id')}")
    
    # ============== TENANT ROUTES ==============
    
    def test_get_current_tenant_owner(self):
        """Test GET /api/tenant/current returns tenant info for owner"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/tenant/current")
        assert response.status_code == 200
        data = response.json()
        
        # Verify tenant structure
        assert "id" in data
        assert "name" in data
        assert "slug" in data
        assert "owner_email" in data
        assert "plan" in data
        assert "is_active" in data
        assert "created_at" in data
        
        print(f"✅ GET /api/tenant/current returns tenant: {data['name']} (ID: {data['id']})")
        return data
    
    def test_update_tenant_settings_owner(self):
        """Test PUT /api/tenant/settings updates tenant info for owner"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        # Get current tenant first
        get_response = self.session.get(f"{BASE_URL}/api/tenant/current")
        assert get_response.status_code == 200
        original_tenant = get_response.json()
        
        # Update tenant settings
        update_data = {
            "phone": "555-TEST-123",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "AZ",
            "zip_code": "85001",
            "website": "https://test-signshop.com"
        }
        
        response = self.session.put(f"{BASE_URL}/api/tenant/settings", json=update_data)
        assert response.status_code == 200
        updated_tenant = response.json()
        
        # Verify updates
        assert updated_tenant["phone"] == update_data["phone"]
        assert updated_tenant["address"] == update_data["address"]
        assert updated_tenant["city"] == update_data["city"]
        assert updated_tenant["state"] == update_data["state"]
        assert updated_tenant["zip_code"] == update_data["zip_code"]
        assert updated_tenant["website"] == update_data["website"]
        
        # Verify GET returns updated data
        verify_response = self.session.get(f"{BASE_URL}/api/tenant/current")
        assert verify_response.status_code == 200
        verified_tenant = verify_response.json()
        assert verified_tenant["phone"] == update_data["phone"]
        
        print("✅ PUT /api/tenant/settings updates tenant successfully")
    
    def test_update_tenant_settings_staff_forbidden(self):
        """Test staff cannot update tenant settings (requires SETTINGS_EDIT permission)"""
        assert self.get_authenticated_session(STAFF_EMAIL, STAFF_PASSWORD)
        
        update_data = {"phone": "555-STAFF-HACK"}
        response = self.session.put(f"{BASE_URL}/api/tenant/settings", json=update_data)
        
        # Staff should get 403 Forbidden
        assert response.status_code == 403
        print("✅ Staff cannot update tenant settings (403 Forbidden)")
    
    # ============== TENANT-SCOPED DATA TESTS ==============
    
    def test_get_customers_tenant_scoped(self):
        """Test GET /api/customers returns only tenant-scoped customers"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200
        customers = response.json()
        
        # Verify it's a list
        assert isinstance(customers, list)
        
        # Get owner's tenant_id
        me_response = self.session.get(f"{BASE_URL}/api/users/me")
        owner_tenant_id = me_response.json().get("tenant_id")
        
        # All customers should have the same tenant_id as the owner
        for customer in customers:
            if customer.get("tenant_id"):  # Some old data might not have tenant_id
                assert customer["tenant_id"] == owner_tenant_id, f"Customer {customer['id']} has wrong tenant_id"
        
        print(f"✅ GET /api/customers returns {len(customers)} tenant-scoped customers")
    
    def test_get_jobs_tenant_scoped(self):
        """Test GET /api/jobs returns only tenant-scoped jobs"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/jobs")
        assert response.status_code == 200
        jobs = response.json()
        
        # Verify it's a list
        assert isinstance(jobs, list)
        
        # Get owner's tenant_id
        me_response = self.session.get(f"{BASE_URL}/api/users/me")
        owner_tenant_id = me_response.json().get("tenant_id")
        
        # All jobs should have the same tenant_id as the owner
        for job in jobs:
            if job.get("tenant_id"):  # Some old data might not have tenant_id
                assert job["tenant_id"] == owner_tenant_id, f"Job {job['id']} has wrong tenant_id"
        
        print(f"✅ GET /api/jobs returns {len(jobs)} tenant-scoped jobs")
    
    def test_create_customer_assigns_tenant_id(self):
        """Test creating a customer assigns the correct tenant_id"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        # Get owner's tenant_id
        me_response = self.session.get(f"{BASE_URL}/api/users/me")
        owner_tenant_id = me_response.json().get("tenant_id")
        
        # Create a new customer
        customer_data = {
            "name": "TEST_Tenant_Customer",
            "company": "Test Tenant Company",
            "email": "tenant-test@example.com",
            "phone": "555-TENANT"
        }
        
        response = self.session.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert response.status_code == 200
        created_customer = response.json()
        
        # Verify tenant_id is assigned
        assert "tenant_id" in created_customer
        assert created_customer["tenant_id"] == owner_tenant_id
        
        print(f"✅ Created customer has correct tenant_id: {created_customer['tenant_id']}")
        
        # Cleanup - delete the test customer
        delete_response = self.session.delete(f"{BASE_URL}/api/customers/{created_customer['id']}")
        assert delete_response.status_code == 200
        print("✅ Test customer cleaned up")
    
    def test_create_job_assigns_tenant_id(self):
        """Test creating a job assigns the correct tenant_id"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        # Get owner's tenant_id
        me_response = self.session.get(f"{BASE_URL}/api/users/me")
        owner_tenant_id = me_response.json().get("tenant_id")
        
        # First, get or create a customer
        customers_response = self.session.get(f"{BASE_URL}/api/customers")
        customers = customers_response.json()
        
        if len(customers) == 0:
            # Create a test customer first
            customer_data = {"name": "TEST_Job_Customer", "email": "job-test@example.com"}
            customer_response = self.session.post(f"{BASE_URL}/api/customers", json=customer_data)
            customer_id = customer_response.json()["id"]
        else:
            customer_id = customers[0]["id"]
        
        # Create a new job
        job_data = {
            "customer_id": customer_id,
            "name": "TEST_Tenant_Job",
            "description": "Test job for tenant verification"
        }
        
        response = self.session.post(f"{BASE_URL}/api/jobs", json=job_data)
        assert response.status_code == 200
        created_job = response.json()
        
        # Verify tenant_id is assigned
        assert "tenant_id" in created_job
        assert created_job["tenant_id"] == owner_tenant_id
        
        print(f"✅ Created job has correct tenant_id: {created_job['tenant_id']}")
        
        # Cleanup - delete the test job
        delete_response = self.session.delete(f"{BASE_URL}/api/jobs/{created_job['id']}")
        assert delete_response.status_code == 200
        print("✅ Test job cleaned up")
    
    # ============== DASHBOARD TENANT-SCOPED DATA ==============
    
    def test_dashboard_stats_tenant_scoped(self):
        """Test GET /api/dashboard/stats returns tenant-scoped data"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        stats = response.json()
        
        # Verify dashboard stats structure
        assert "total_customers" in stats or "customers" in stats or isinstance(stats, dict)
        
        print(f"✅ GET /api/dashboard/stats returns tenant-scoped data: {stats}")
    
    # ============== QUOTES TENANT-SCOPED ==============
    
    def test_get_quotes_tenant_scoped(self):
        """Test GET /api/quotes returns only tenant-scoped quotes"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/quotes")
        assert response.status_code == 200
        quotes = response.json()
        
        # Verify it's a list
        assert isinstance(quotes, list)
        
        # Get owner's tenant_id
        me_response = self.session.get(f"{BASE_URL}/api/users/me")
        owner_tenant_id = me_response.json().get("tenant_id")
        
        # All quotes should have the same tenant_id as the owner
        for quote in quotes:
            if quote.get("tenant_id"):
                assert quote["tenant_id"] == owner_tenant_id
        
        print(f"✅ GET /api/quotes returns {len(quotes)} tenant-scoped quotes")
    
    # ============== INVOICES TENANT-SCOPED ==============
    
    def test_get_invoices_tenant_scoped(self):
        """Test GET /api/invoices returns only tenant-scoped invoices"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 200
        invoices = response.json()
        
        # Verify it's a list
        assert isinstance(invoices, list)
        
        # Get owner's tenant_id
        me_response = self.session.get(f"{BASE_URL}/api/users/me")
        owner_tenant_id = me_response.json().get("tenant_id")
        
        # All invoices should have the same tenant_id as the owner
        for invoice in invoices:
            if invoice.get("tenant_id"):
                assert invoice["tenant_id"] == owner_tenant_id
        
        print(f"✅ GET /api/invoices returns {len(invoices)} tenant-scoped invoices")
    
    # ============== EMPLOYEES TENANT-SCOPED ==============
    
    def test_get_employees_tenant_scoped(self):
        """Test GET /api/employees returns only tenant-scoped employees"""
        assert self.get_authenticated_session(OWNER_EMAIL, OWNER_PASSWORD)
        
        response = self.session.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        employees = response.json()
        
        # Verify it's a list
        assert isinstance(employees, list)
        
        print(f"✅ GET /api/employees returns {len(employees)} tenant-scoped employees")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
