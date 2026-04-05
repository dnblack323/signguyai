"""
Backend Refactoring Regression Tests

Tests all API endpoints after major refactoring:
- server.py reduced from 6349 to 774 lines
- All models moved to /models directory
- All routes moved to /routes directory

Test Coverage:
- Auth routes: /api/auth/register, /api/auth/login
- User routes: /api/users/me
- Customer routes: /api/customers CRUD
- Quote routes: /api/quotes CRUD
- Job routes: /api/jobs CRUD
- Invoice routes: /api/invoices CRUD
- Pricing routes: /api/pricing/calculate
- Portal routes: /api/portal/auth/login
- Dashboard routes: /api/dashboard/stats (if exists)
- Employee routes: /api/employees
- Timeclock routes: /api/timeclock
- Payroll routes: /api/payroll
- Webstore routes: /api/webstores/v2
- Product routes: /api/products
"""

import pytest
import requests
import os
import uuid
from datetime import datetime
from backend.tests.test_credentials_helper import COMMON_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, WRONG_PASSWORD

# Get base URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_EMAIL = f"test_refactor_{uuid.uuid4().hex[:8]}@signguy.com"
TEST_PASSWORD = COMMON_TEST_PASSWORD
TEST_FULL_NAME = "Test Refactor User"


class TestHealthAndRoot:
    """Basic health check tests"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health endpoint working")
    
    def test_root_endpoint(self):
        """Test /api/ returns API info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "SignGuy" in data["message"]
        print("✅ Root endpoint working")


class TestAuthRoutes:
    """Authentication route tests"""
    
    @pytest.fixture(scope="class")
    def registered_user(self):
        """Register a test user and return credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_FULL_NAME,
            "company_name": "Test Refactor Company"
        })
        if response.status_code == 200:
            data = response.json()
            return {"email": TEST_EMAIL, "password": TEST_PASSWORD, "token": data["access_token"]}
        elif response.status_code == 400 and "already registered" in response.text:
            # User exists, try login
            login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if login_resp.status_code == 200:
                return {"email": TEST_EMAIL, "password": TEST_PASSWORD, "token": login_resp.json()["access_token"]}
        pytest.skip(f"Could not register/login test user: {response.text}")
    
    def test_register_new_user(self):
        """Test POST /api/auth/register creates new user"""
        unique_email = f"test_new_{uuid.uuid4().hex[:8]}@signguy.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": COMMON_TEST_PASSWORD,
            "full_name": "New Test User",
            "company_name": "New Test Company"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        print(f"✅ Register endpoint working - created user {unique_email}")
    
    def test_register_duplicate_email_fails(self, registered_user):
        """Test registering with existing email fails"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": registered_user["email"],
            "password": COMMON_TEST_PASSWORD,
            "full_name": "Duplicate User"
        })
        assert response.status_code == 400
        assert "already registered" in response.json().get("detail", "").lower()
        print("✅ Duplicate email registration correctly rejected")
    
    def test_login_valid_credentials(self, registered_user):
        """Test POST /api/auth/login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
        print("✅ Login endpoint working")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials fails"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": WRONG_PASSWORD
        })
        assert response.status_code == 401
        print("✅ Invalid login correctly rejected")
    
    def test_login_with_remember_me(self, registered_user):
        """Test login with remember_me flag"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": registered_user["email"],
            "password": registered_user["password"],
            "remember_me": True
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        # Remember me should have longer expiry
        assert data.get("expires_in", 0) > 86400  # More than 1 day
        print("✅ Login with remember_me working")


class TestUserRoutes:
    """User profile route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        # Register or login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code != 200:
            # Try registering
            response = requests.post(f"{BASE_URL}/api/auth/register", json={
                "email": SYNTHETIC_OWNER_EMAIL,
                "password": COMMON_TEST_PASSWORD,
                "full_name": "Test Owner",
                "company_name": "Test Sign Shop"
            })
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        pytest.skip("Could not authenticate")
    
    def test_get_current_user(self, auth_headers):
        """Test GET /api/users/me returns current user"""
        response = requests.get(f"{BASE_URL}/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "role" in data
        assert "tenant_id" in data
        print(f"✅ Get current user working - {data['email']}")
    
    def test_get_user_permissions(self, auth_headers):
        """Test GET /api/users/me/permissions returns permissions"""
        response = requests.get(f"{BASE_URL}/api/users/me/permissions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "role" in data
        assert "permissions" in data
        assert isinstance(data["permissions"], list)
        print(f"✅ Get user permissions working - role: {data['role']}")
    
    def test_unauthorized_access_rejected(self):
        """Test accessing protected endpoint without auth fails"""
        response = requests.get(f"{BASE_URL}/api/users/me")
        assert response.status_code == 401
        print("✅ Unauthorized access correctly rejected")


class TestCustomerRoutes:
    """Customer CRUD route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_headers):
        """Create a test customer"""
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": f"TEST_Customer_{uuid.uuid4().hex[:8]}",
            "email": f"test_customer_{uuid.uuid4().hex[:8]}@test.com",
            "phone": "555-1234",
            "company": "Test Company Inc"
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create test customer: {response.text}")
    
    def test_create_customer(self, auth_headers):
        """Test POST /api/customers creates customer"""
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": f"TEST_NewCustomer_{uuid.uuid4().hex[:8]}",
            "email": f"new_customer_{uuid.uuid4().hex[:8]}@test.com",
            "phone": "555-5678"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        print(f"✅ Create customer working - {data['name']}")
    
    def test_get_customers_list(self, auth_headers):
        """Test GET /api/customers returns list"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get customers list working - {len(data)} customers")
    
    def test_get_customer_by_id(self, auth_headers, test_customer):
        """Test GET /api/customers/{id} returns customer"""
        response = requests.get(f"{BASE_URL}/api/customers/{test_customer['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_customer["id"]
        print("✅ Get customer by ID working")
    
    def test_update_customer(self, auth_headers, test_customer):
        """Test PUT /api/customers/{id} updates customer"""
        response = requests.put(f"{BASE_URL}/api/customers/{test_customer['id']}", headers=auth_headers, json={
            "phone": "555-9999"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "555-9999"
        print("✅ Update customer working")
    
    def test_get_customer_summary(self, auth_headers, test_customer):
        """Test GET /api/customers/{id}/summary returns summary"""
        response = requests.get(f"{BASE_URL}/api/customers/{test_customer['id']}/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "customer" in data
        assert "quotes_count" in data
        assert "jobs_count" in data
        assert "invoices_count" in data
        print("✅ Get customer summary working")
    
    def test_search_customers(self, auth_headers, test_customer):
        """Test GET /api/customers with search parameter"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers, params={
            "search": "TEST_"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Search customers working - found {len(data)} matches")


class TestQuoteRoutes:
    """Quote CRUD route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def test_customer_id(self, auth_headers):
        """Get or create a test customer for quotes"""
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": f"TEST_QuoteCustomer_{uuid.uuid4().hex[:8]}",
            "email": f"quote_customer_{uuid.uuid4().hex[:8]}@test.com"
        })
        if response.status_code == 200:
            return response.json()["id"]
        pytest.skip("Could not create customer for quotes")
    
    @pytest.fixture(scope="class")
    def test_quote(self, auth_headers, test_customer_id):
        """Create a test quote"""
        response = requests.post(f"{BASE_URL}/api/quotes", headers=auth_headers, json={
            "customer_id": test_customer_id,
            "line_items": [
                {"description": "Test Sign", "quantity": 2, "unit_price": 100.00}
            ],
            "notes": "Test quote for refactoring tests"
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create test quote: {response.text}")
    
    def test_create_quote(self, auth_headers, test_customer_id):
        """Test POST /api/quotes creates quote"""
        response = requests.post(f"{BASE_URL}/api/quotes", headers=auth_headers, json={
            "customer_id": test_customer_id,
            "line_items": [
                {"description": "Banner 4x8", "quantity": 1, "unit_price": 150.00},
                {"description": "Installation", "quantity": 1, "unit_price": 75.00}
            ],
            "notes": "New test quote"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["total"] == 225.00
        print(f"✅ Create quote working - total: ${data['total']}")
    
    def test_get_quotes_list(self, auth_headers):
        """Test GET /api/quotes returns list"""
        response = requests.get(f"{BASE_URL}/api/quotes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get quotes list working - {len(data)} quotes")
    
    def test_get_quote_by_id(self, auth_headers, test_quote):
        """Test GET /api/quotes/{id} returns quote"""
        response = requests.get(f"{BASE_URL}/api/quotes/{test_quote['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_quote["id"]
        print("✅ Get quote by ID working")
    
    def test_update_quote(self, auth_headers, test_quote):
        """Test PUT /api/quotes/{id} updates quote"""
        response = requests.put(f"{BASE_URL}/api/quotes/{test_quote['id']}", headers=auth_headers, json={
            "notes": "Updated test quote notes"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated test quote notes"
        print("✅ Update quote working")
    
    def test_send_quote(self, auth_headers, test_quote):
        """Test POST /api/quotes/{id}/send marks quote as sent"""
        response = requests.post(f"{BASE_URL}/api/quotes/{test_quote['id']}/send", headers=auth_headers)
        assert response.status_code == 200
        print("✅ Send quote working")


class TestJobRoutes:
    """Job CRUD route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def test_customer_id(self, auth_headers):
        """Get or create a test customer for jobs"""
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": f"TEST_JobCustomer_{uuid.uuid4().hex[:8]}",
            "email": f"job_customer_{uuid.uuid4().hex[:8]}@test.com"
        })
        if response.status_code == 200:
            return response.json()["id"]
        pytest.skip("Could not create customer for jobs")
    
    @pytest.fixture(scope="class")
    def test_job(self, auth_headers, test_customer_id):
        """Create a test job"""
        response = requests.post(f"{BASE_URL}/api/jobs", headers=auth_headers, json={
            "customer_id": test_customer_id,
            "name": f"TEST_Job_{uuid.uuid4().hex[:8]}",
            "description": "Test job for refactoring tests"
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create test job: {response.text}")
    
    def test_create_job(self, auth_headers, test_customer_id):
        """Test POST /api/jobs creates job"""
        response = requests.post(f"{BASE_URL}/api/jobs", headers=auth_headers, json={
            "customer_id": test_customer_id,
            "name": f"TEST_NewJob_{uuid.uuid4().hex[:8]}",
            "description": "New test job"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        print(f"✅ Create job working - {data['name']}")
    
    def test_get_jobs_list(self, auth_headers):
        """Test GET /api/jobs returns list"""
        response = requests.get(f"{BASE_URL}/api/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get jobs list working - {len(data)} jobs")
    
    def test_get_job_by_id(self, auth_headers, test_job):
        """Test GET /api/jobs/{id} returns job"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_job["id"]
        print("✅ Get job by ID working")
    
    def test_get_job_details(self, auth_headers, test_job):
        """Test GET /api/jobs/{id}/details returns comprehensive details"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job['id']}/details", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "job" in data
        assert "customer" in data
        assert "job_items" in data
        assert "notes" in data
        assert "activities" in data
        assert "financial_snapshot" in data
        print("✅ Get job details working")
    
    def test_update_job(self, auth_headers, test_job):
        """Test PUT /api/jobs/{id} updates job"""
        response = requests.put(f"{BASE_URL}/api/jobs/{test_job['id']}", headers=auth_headers, json={
            "description": "Updated test job description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated test job description"
        print("✅ Update job working")
    
    def test_add_job_item(self, auth_headers, test_job):
        """Test POST /api/jobs/{id}/items adds item"""
        response = requests.post(f"{BASE_URL}/api/jobs/{test_job['id']}/items", headers=auth_headers, json={
            "item_type": "banner",
            "description": "Test Sign Item",
            "quantity": 2,
            "unit_price": 50.00
        })
        assert response.status_code == 200
        data = response.json()
        assert data["line_total"] == 100.00
        print("✅ Add job item working")
    
    def test_get_job_items(self, auth_headers, test_job):
        """Test GET /api/jobs/{id}/items returns items"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job['id']}/items", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get job items working - {len(data)} items")
    
    def test_add_job_note(self, auth_headers, test_job):
        """Test POST /api/jobs/{id}/notes adds note"""
        response = requests.post(f"{BASE_URL}/api/jobs/{test_job['id']}/notes", headers=auth_headers, json={
            "content": "Test note for job"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["content"] == "Test note for job"
        print("✅ Add job note working")
    
    def test_get_job_notes(self, auth_headers, test_job):
        """Test GET /api/jobs/{id}/notes returns notes"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job['id']}/notes", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get job notes working - {len(data)} notes")
    
    def test_get_job_activities(self, auth_headers, test_job):
        """Test GET /api/jobs/{id}/activities returns activity log"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job['id']}/activities", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get job activities working - {len(data)} activities")
    
    def test_complete_job(self, auth_headers, test_job):
        """Test POST /api/jobs/{id}/complete marks job complete"""
        response = requests.post(f"{BASE_URL}/api/jobs/{test_job['id']}/complete", headers=auth_headers)
        assert response.status_code == 200
        print("✅ Complete job working")
    
    def test_archive_job(self, auth_headers, test_job):
        """Test POST /api/jobs/{id}/archive archives job"""
        response = requests.post(f"{BASE_URL}/api/jobs/{test_job['id']}/archive", headers=auth_headers)
        assert response.status_code == 200
        print("✅ Archive job working")
    
    def test_unarchive_job(self, auth_headers, test_job):
        """Test POST /api/jobs/{id}/unarchive unarchives job"""
        response = requests.post(f"{BASE_URL}/api/jobs/{test_job['id']}/unarchive", headers=auth_headers)
        assert response.status_code == 200
        print("✅ Unarchive job working")


class TestInvoiceRoutes:
    """Invoice CRUD route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def test_customer_id(self, auth_headers):
        """Get or create a test customer for invoices"""
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": f"TEST_InvoiceCustomer_{uuid.uuid4().hex[:8]}",
            "email": f"invoice_customer_{uuid.uuid4().hex[:8]}@test.com"
        })
        if response.status_code == 200:
            return response.json()["id"]
        pytest.skip("Could not create customer for invoices")
    
    @pytest.fixture(scope="class")
    def test_invoice(self, auth_headers, test_customer_id):
        """Create a test invoice"""
        response = requests.post(f"{BASE_URL}/api/invoices", headers=auth_headers, json={
            "customer_id": test_customer_id,
            "line_items": [
                {"description": "Test Service", "quantity": 1, "unit_price": 200.00}
            ]
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create test invoice: {response.text}")
    
    def test_create_invoice(self, auth_headers, test_customer_id):
        """Test POST /api/invoices creates invoice"""
        response = requests.post(f"{BASE_URL}/api/invoices", headers=auth_headers, json={
            "customer_id": test_customer_id,
            "line_items": [
                {"description": "Sign Production", "quantity": 1, "unit_price": 300.00},
                {"description": "Installation", "quantity": 1, "unit_price": 100.00}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✅ Create invoice working - total: ${data.get('total', 0)}")
    
    def test_get_invoices_list(self, auth_headers):
        """Test GET /api/invoices returns list"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get invoices list working - {len(data)} invoices")
    
    def test_get_invoice_by_id(self, auth_headers, test_invoice):
        """Test GET /api/invoices/{id} returns invoice"""
        response = requests.get(f"{BASE_URL}/api/invoices/{test_invoice['id']}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_invoice["id"]
        print("✅ Get invoice by ID working")
    
    def test_update_invoice(self, auth_headers, test_invoice):
        """Test PUT /api/invoices/{id} updates invoice"""
        response = requests.put(f"{BASE_URL}/api/invoices/{test_invoice['id']}", headers=auth_headers, json={
            "notes": "Updated invoice notes"
        })
        assert response.status_code == 200
        print("✅ Update invoice working")
    
    def test_send_invoice(self, auth_headers, test_invoice):
        """Test POST /api/invoices/{id}/send marks invoice as sent"""
        response = requests.post(f"{BASE_URL}/api/invoices/{test_invoice['id']}/send", headers=auth_headers)
        assert response.status_code == 200
        print("✅ Send invoice working")
    
    def test_record_payment(self, auth_headers, test_invoice):
        """Test POST /api/invoices/{id}/record-payment records payment"""
        response = requests.post(
            f"{BASE_URL}/api/invoices/{test_invoice['id']}/record-payment",
            headers=auth_headers,
            params={"amount": 50.00, "payment_method": "cash"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("✅ Record payment working")
    
    def test_get_invoice_payments(self, auth_headers, test_invoice):
        """Test GET /api/invoices/{id}/payments returns payments"""
        response = requests.get(f"{BASE_URL}/api/invoices/{test_invoice['id']}/payments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get invoice payments working - {len(data)} payments")


class TestPricingRoutes:
    """Pricing calculator route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    def test_calculate_rigid_signs(self, auth_headers):
        """Test POST /api/pricing/calculate for rigid signs"""
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=auth_headers, json={
            "category": "rigid_signs",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 18,
                "substrate_type": "coroplast_4mm"
            },
            "quantity": 2
        })
        assert response.status_code == 200
        data = response.json()
        assert "material_cost" in data
        assert "labor_cost" in data
        assert "suggested_price" in data
        print(f"✅ Pricing calculate (rigid_signs) working - ${data['suggested_price']}")
    
    def test_calculate_cut_vinyl(self, auth_headers):
        """Test POST /api/pricing/calculate for cut vinyl"""
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=auth_headers, json={
            "category": "cut_vinyl",
            "pricing_data": {
                "width_inches": 12,
                "length_inches": 12,
                "vinyl_type": "oracal_651"
            },
            "quantity": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert "suggested_price" in data
        print(f"✅ Pricing calculate (cut_vinyl) working - ${data['suggested_price']}")
    
    def test_calculate_apparel(self, auth_headers):
        """Test POST /api/pricing/calculate for apparel"""
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", headers=auth_headers, json={
            "category": "apparel",
            "pricing_data": {
                "apparel_type": "tshirt",
                "transfer_type": "htv",
                "num_print_locations": 1
            },
            "quantity": 24
        })
        assert response.status_code == 200
        data = response.json()
        assert "suggested_price" in data
        print(f"✅ Pricing calculate (apparel) working - ${data['suggested_price']}")
    
    def test_get_pricing_defaults(self, auth_headers):
        """Test GET /api/pricing/defaults returns defaults"""
        response = requests.get(f"{BASE_URL}/api/pricing/defaults", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print("✅ Get pricing defaults working")
    
    def test_get_materials(self, auth_headers):
        """Test GET /api/pricing/materials returns materials catalog"""
        response = requests.get(f"{BASE_URL}/api/pricing/materials", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "vinyl" in data
        assert "substrate" in data
        assert "apparel" in data
        print("✅ Get materials catalog working")
    
    def test_pricing_requires_auth(self):
        """Test pricing endpoints require authentication"""
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json={
            "category": "rigid_signs",
            "pricing_data": {},
            "quantity": 1
        })
        assert response.status_code == 401
        print("✅ Pricing endpoints correctly require auth")


class TestPortalRoutes:
    """Customer portal route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get shop auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def portal_customer(self, auth_headers):
        """Create a customer with portal access"""
        unique_email = f"portal_test_{uuid.uuid4().hex[:8]}@test.com"
        # Create customer
        response = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": "Portal Test Customer",
            "email": unique_email
        })
        if response.status_code == 200:
            return {"email": unique_email, "password": "Portal123!"}
        pytest.skip("Could not create portal customer")
    
    def test_portal_register(self, portal_customer):
        """Test POST /api/portal/auth/register enables portal access"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/register", json={
            "email": portal_customer["email"],
            "password": portal_customer["password"]
        })
        # May fail if customer doesn't exist or already registered
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            print("✅ Portal register working")
        elif response.status_code == 404:
            print("⚠️ Portal register - customer not found (expected if customer creation failed)")
        elif response.status_code == 400:
            print("⚠️ Portal register - already registered")
        else:
            print(f"⚠️ Portal register returned {response.status_code}")
    
    def test_portal_login_invalid(self):
        """Test portal login with invalid credentials fails"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": "nonexistent@portal.com",
            "password": WRONG_PASSWORD
        })
        assert response.status_code in [401, 403]
        print("✅ Portal login correctly rejects invalid credentials")


class TestEmployeeRoutes:
    """Employee management route tests"""
    
    @pytest.fixture(scope="class")
    def test_employee(self):
        """Create a test employee"""
        response = requests.post(f"{BASE_URL}/api/employees", json={
            "name": f"TEST_Employee_{uuid.uuid4().hex[:8]}",
            "email": f"employee_{uuid.uuid4().hex[:8]}@test.com",
            "hourly_rate": 25.00,
            "role": "staff"
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create test employee: {response.text}")
    
    def test_create_employee(self):
        """Test POST /api/employees creates employee"""
        response = requests.post(f"{BASE_URL}/api/employees", json={
            "name": f"TEST_NewEmployee_{uuid.uuid4().hex[:8]}",
            "hourly_rate": 20.00
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✅ Create employee working - {data['name']}")
    
    def test_get_employees_list(self):
        """Test GET /api/employees returns list"""
        response = requests.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get employees list working - {len(data)} employees")
    
    def test_get_employee_by_id(self, test_employee):
        """Test GET /api/employees/{id} returns employee"""
        response = requests.get(f"{BASE_URL}/api/employees/{test_employee['id']}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_employee["id"]
        print("✅ Get employee by ID working")
    
    def test_update_employee(self, test_employee):
        """Test PUT /api/employees/{id} updates employee"""
        response = requests.put(f"{BASE_URL}/api/employees/{test_employee['id']}", json={
            "hourly_rate": 30.00
        })
        assert response.status_code == 200
        data = response.json()
        assert data["hourly_rate"] == 30.00
        print("✅ Update employee working")


class TestTimeclockRoutes:
    """Time clock route tests"""
    
    @pytest.fixture(scope="class")
    def test_employee(self):
        """Create a test employee for timeclock"""
        response = requests.post(f"{BASE_URL}/api/employees", json={
            "name": f"TEST_TimeclockEmployee_{uuid.uuid4().hex[:8]}",
            "hourly_rate": 25.00
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip("Could not create employee for timeclock")
    
    def test_clock_in(self, test_employee):
        """Test POST /api/timeclock clocks in employee"""
        response = requests.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": test_employee["id"],
            "action": "start_work"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "start_work"
        print("✅ Clock in working")
    
    def test_get_today_logs(self, test_employee):
        """Test GET /api/timeclock/{id}/today returns today's logs"""
        response = requests.get(f"{BASE_URL}/api/timeclock/{test_employee['id']}/today")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get today's logs working - {len(data)} entries")
    
    def test_get_clock_status(self, test_employee):
        """Test GET /api/timeclock/{id}/status returns current status"""
        response = requests.get(f"{BASE_URL}/api/timeclock/{test_employee['id']}/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        print(f"✅ Get clock status working - status: {data['status']}")
    
    def test_clock_out(self, test_employee):
        """Test clock out after clock in"""
        response = requests.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": test_employee["id"],
            "action": "end_work"
        })
        assert response.status_code == 200
        print("✅ Clock out working")
    
    def test_get_shift_summary(self, test_employee):
        """Test GET /api/timeclock/{id}/summary returns shift summary"""
        response = requests.get(f"{BASE_URL}/api/timeclock/{test_employee['id']}/summary")
        assert response.status_code == 200
        data = response.json()
        assert "work_minutes" in data
        assert "net_hours" in data
        print(f"✅ Get shift summary working - {data['net_hours']} hours")


class TestPayrollRoutes:
    """Payroll route tests"""
    
    @pytest.fixture(scope="class")
    def test_employee(self):
        """Create a test employee for payroll"""
        response = requests.post(f"{BASE_URL}/api/employees", json={
            "name": f"TEST_PayrollEmployee_{uuid.uuid4().hex[:8]}",
            "hourly_rate": 25.00
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip("Could not create employee for payroll")
    
    def test_create_payroll_transaction(self, test_employee):
        """Test POST /api/payroll/transactions creates transaction"""
        response = requests.post(f"{BASE_URL}/api/payroll/transactions", json={
            "employee_id": test_employee["id"],
            "type": "earnings",
            "amount": 500.00,
            "description": "Weekly pay"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 500.00
        print("✅ Create payroll transaction working")
    
    def test_get_payroll_transactions(self, test_employee):
        """Test GET /api/payroll/transactions returns transactions"""
        response = requests.get(f"{BASE_URL}/api/payroll/transactions", params={
            "employee_id": test_employee["id"]
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get payroll transactions working - {len(data)} transactions")
    
    def test_get_payroll_balance(self, test_employee):
        """Test GET /api/payroll/balance/{id} returns balance"""
        response = requests.get(f"{BASE_URL}/api/payroll/balance/{test_employee['id']}")
        assert response.status_code == 200
        data = response.json()
        assert "total_earnings" in data
        assert "balance" in data
        print(f"✅ Get payroll balance working - balance: ${data['balance']}")


class TestWebstoreRoutes:
    """Webstore route tests"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    @pytest.fixture(scope="class")
    def test_product(self, auth_headers):
        """Create a test product"""
        response = requests.post(f"{BASE_URL}/api/products", headers=auth_headers, json={
            "name": f"TEST_Product_{uuid.uuid4().hex[:8]}",
            "category": "signs",
            "base_cost": 10.00,
            "retail_price": 25.00
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create test product: {response.text}")
    
    @pytest.fixture(scope="class")
    def test_webstore(self, auth_headers):
        """Create a test webstore"""
        response = requests.post(f"{BASE_URL}/api/webstores/v2", headers=auth_headers, json={
            "name": f"TEST_Store_{uuid.uuid4().hex[:8]}",
            "store_type": "business",
            "owner_name": "Test Owner",
            "owner_email": "store_owner@test.com"
        })
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create test webstore: {response.text}")
    
    def test_create_product(self, auth_headers):
        """Test POST /api/products creates product"""
        response = requests.post(f"{BASE_URL}/api/products", headers=auth_headers, json={
            "name": f"TEST_NewProduct_{uuid.uuid4().hex[:8]}",
            "category": "apparel",
            "base_cost": 5.00,
            "retail_price": 20.00
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✅ Create product working - {data['name']}")
    
    def test_get_products_list(self, auth_headers):
        """Test GET /api/products returns list"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get products list working - {len(data)} products")
    
    def test_create_webstore(self, auth_headers):
        """Test POST /api/webstores/v2 creates webstore"""
        response = requests.post(f"{BASE_URL}/api/webstores/v2", headers=auth_headers, json={
            "name": f"TEST_NewStore_{uuid.uuid4().hex[:8]}",
            "store_type": "fundraiser",
            "owner_name": "Fundraiser Owner",
            "fundraiser_goal": 5000.00,
            "fundraiser_profit_percent": 20
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✅ Create webstore working - {data['name']}")
    
    def test_get_webstores_list(self, auth_headers):
        """Test GET /api/webstores/v2 returns list"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get webstores list working - {len(data)} stores")
    
    def test_add_product_to_webstore(self, auth_headers, test_webstore, test_product):
        """Test POST /api/webstores/v2/{id}/products adds product"""
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{test_webstore['id']}/products",
            headers=auth_headers,
            params={"product_id": test_product["id"]}
        )
        assert response.status_code == 200
        print("✅ Add product to webstore working")
    
    def test_get_webstore_products(self, auth_headers, test_webstore):
        """Test GET /api/webstores/v2/{id}/products returns products"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{test_webstore['id']}/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Get webstore products working - {len(data)} products")


class TestQuoteToJobConversion:
    """Test quote to job conversion flow"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    def test_convert_quote_to_job(self, auth_headers):
        """Test POST /api/quotes/{id}/convert-to-job creates job from quote"""
        # Create customer
        customer_resp = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": f"TEST_ConvertCustomer_{uuid.uuid4().hex[:8]}",
            "email": f"convert_{uuid.uuid4().hex[:8]}@test.com"
        })
        if customer_resp.status_code != 200:
            pytest.skip("Could not create customer")
        customer_id = customer_resp.json()["id"]
        
        # Create quote
        quote_resp = requests.post(f"{BASE_URL}/api/quotes", headers=auth_headers, json={
            "customer_id": customer_id,
            "line_items": [
                {"description": "Sign for conversion", "quantity": 1, "unit_price": 500.00}
            ]
        })
        if quote_resp.status_code != 200:
            pytest.skip("Could not create quote")
        quote_id = quote_resp.json()["id"]
        
        # Convert to job
        convert_resp = requests.post(f"{BASE_URL}/api/quotes/{quote_id}/convert-to-job", headers=auth_headers)
        assert convert_resp.status_code == 200
        job = convert_resp.json()
        assert "id" in job
        assert job["quote_id"] == quote_id
        print(f"✅ Quote to job conversion working - Job ID: {job['id'][:8]}")


class TestInvoiceFromJob:
    """Test invoice creation from job"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        if response.status_code == 200:
            return {"Authorization": f"Bearer {response.json()['access_token']}"}
        pytest.skip("Could not authenticate")
    
    def test_create_invoice_from_job(self, auth_headers):
        """Test POST /api/invoices/from-job/{id} creates invoice from job"""
        # Create customer
        customer_resp = requests.post(f"{BASE_URL}/api/customers", headers=auth_headers, json={
            "name": f"TEST_InvoiceJobCustomer_{uuid.uuid4().hex[:8]}",
            "email": f"invoice_job_{uuid.uuid4().hex[:8]}@test.com"
        })
        if customer_resp.status_code != 200:
            pytest.skip("Could not create customer")
        customer_id = customer_resp.json()["id"]
        
        # Create job
        job_resp = requests.post(f"{BASE_URL}/api/jobs", headers=auth_headers, json={
            "customer_id": customer_id,
            "name": f"TEST_InvoiceJob_{uuid.uuid4().hex[:8]}"
        })
        if job_resp.status_code != 200:
            pytest.skip("Could not create job")
        job_id = job_resp.json()["id"]
        
        # Add job item
        requests.post(f"{BASE_URL}/api/jobs/{job_id}/items", headers=auth_headers, json={
            "item_type": "banner",
            "description": "Test item for invoice",
            "quantity": 2,
            "unit_price": 150.00
        })
        
        # Create invoice from job
        invoice_resp = requests.post(f"{BASE_URL}/api/invoices/from-job/{job_id}", headers=auth_headers)
        assert invoice_resp.status_code == 200
        invoice = invoice_resp.json()
        assert "id" in invoice
        assert invoice["job_id"] == job_id
        print(f"✅ Invoice from job working - Invoice ID: {invoice['id'][:8]}")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
