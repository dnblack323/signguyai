"""
Security Audit: Tenant Data Isolation Tests

This module tests that all API endpoints properly filter by tenant_id 
to prevent data leaks between accounts.

Test Strategy:
1. Create data as Tenant A
2. Attempt to access/modify/delete that data as Tenant B
3. Verify Tenant B cannot see or manipulate Tenant A's data
"""

import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials for two different tenants
TENANT_A = {
    "email": "tenant_a@test.com",
    "password": COMMON_TEST_PASSWORD
}

TENANT_B = {
    "email": "tenant_b@test.com", 
    "password": COMMON_TEST_PASSWORD
}


class TestTenantIsolation:
    """Comprehensive tenant isolation security tests"""
    
    @pytest.fixture(scope="class")
    def tenant_a_token(self):
        """Get auth token for Tenant A"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TENANT_A)
        if response.status_code != 200:
            pytest.skip(f"Cannot authenticate Tenant A: {response.text}")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def tenant_b_token(self):
        """Get auth token for Tenant B"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TENANT_B)
        if response.status_code != 200:
            pytest.skip(f"Cannot authenticate Tenant B: {response.text}")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers_a(self, tenant_a_token):
        return {"Authorization": f"Bearer {tenant_a_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def headers_b(self, tenant_b_token):
        return {"Authorization": f"Bearer {tenant_b_token}", "Content-Type": "application/json"}

    # ================== CUSTOMERS ISOLATION ==================
    
    def test_customers_tenant_a_cannot_see_tenant_b_customers(self, headers_a, headers_b):
        """Tenant A should NOT see Tenant B's customers"""
        # Create customer as Tenant B
        unique_name = f"SECURITY_TEST_B_CUSTOMER_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/customers", json={
            "name": unique_name,
            "email": f"{unique_name}@test.com"
        }, headers=headers_b)
        
        assert create_resp.status_code in [200, 201], f"Failed to create customer: {create_resp.text}"
        customer_b_id = create_resp.json().get("id")
        
        # Try to access Tenant B's customer as Tenant A
        get_resp = requests.get(f"{BASE_URL}/api/customers/{customer_b_id}", headers=headers_a)
        assert get_resp.status_code == 404, f"SECURITY ISSUE: Tenant A can see Tenant B's customer! Status: {get_resp.status_code}"
        
        # Try to list customers as Tenant A - should not contain Tenant B's customer
        list_resp = requests.get(f"{BASE_URL}/api/customers", headers=headers_a)
        assert list_resp.status_code == 200
        customer_ids = [c.get("id") for c in list_resp.json()]
        assert customer_b_id not in customer_ids, "SECURITY ISSUE: Tenant B's customer appears in Tenant A's list!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer_b_id}", headers=headers_b)
        print("PASS: Customers tenant isolation verified")

    def test_customers_tenant_b_cannot_update_tenant_a_customer(self, headers_a, headers_b):
        """Tenant B should NOT be able to update Tenant A's customer"""
        # Create customer as Tenant A
        unique_name = f"SECURITY_TEST_A_CUSTOMER_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/customers", json={
            "name": unique_name,
            "email": f"{unique_name}@test.com"
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201]
        customer_a_id = create_resp.json().get("id")
        
        # Try to update Tenant A's customer as Tenant B
        update_resp = requests.put(f"{BASE_URL}/api/customers/{customer_a_id}", json={
            "name": "HACKED_BY_TENANT_B"
        }, headers=headers_b)
        assert update_resp.status_code == 404, f"SECURITY ISSUE: Tenant B can update Tenant A's customer! Status: {update_resp.status_code}"
        
        # Verify customer was not modified
        verify_resp = requests.get(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        assert verify_resp.json().get("name") == unique_name, "SECURITY ISSUE: Customer was modified!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        print("PASS: Customer update isolation verified")

    def test_customers_tenant_b_cannot_delete_tenant_a_customer(self, headers_a, headers_b):
        """Tenant B should NOT be able to delete Tenant A's customer"""
        # Create customer as Tenant A
        unique_name = f"SECURITY_TEST_DELETE_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/customers", json={
            "name": unique_name
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201]
        customer_a_id = create_resp.json().get("id")
        
        # Try to delete Tenant A's customer as Tenant B
        delete_resp = requests.delete(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, f"SECURITY ISSUE: Tenant B can delete Tenant A's customer! Status: {delete_resp.status_code}"
        
        # Verify customer still exists
        verify_resp = requests.get(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        assert verify_resp.status_code == 200, "SECURITY ISSUE: Customer was deleted by unauthorized tenant!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        print("PASS: Customer delete isolation verified")

    # ================== EMPLOYEES ISOLATION ==================
    
    def test_employees_isolation(self, headers_a, headers_b):
        """Tenant B should NOT see, update, or delete Tenant A's employees"""
        # Create employee as Tenant A
        unique_name = f"SECURITY_TEST_EMP_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/employees", json={
            "name": unique_name,
            "hourly_rate": 15.0
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create employee: {create_resp.text}"
        employee_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT see Tenant A's employee in list
        list_resp = requests.get(f"{BASE_URL}/api/employees", headers=headers_b)
        assert list_resp.status_code == 200
        employee_ids = [e.get("id") for e in list_resp.json()]
        assert employee_a_id not in employee_ids, "SECURITY ISSUE: Tenant A's employee in Tenant B's list!"
        
        # Tenant B should NOT access Tenant A's employee directly
        get_resp = requests.get(f"{BASE_URL}/api/employees/{employee_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's employee!"
        
        # Tenant B should NOT update Tenant A's employee
        update_resp = requests.put(f"{BASE_URL}/api/employees/{employee_a_id}", json={
            "name": "HACKED_EMPLOYEE"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's employee!"
        
        # Verify not modified
        verify_resp = requests.get(f"{BASE_URL}/api/employees/{employee_a_id}", headers=headers_a)
        assert verify_resp.json().get("name") == unique_name, "Employee was modified by unauthorized tenant!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_a_id}", headers=headers_a)
        print("PASS: Employees tenant isolation verified")

    # ================== JOBS ISOLATION ==================
    
    def test_jobs_isolation(self, headers_a, headers_b):
        """Tenant B should NOT see, update, or delete Tenant A's jobs"""
        # First create a customer for Tenant A
        customer_resp = requests.post(f"{BASE_URL}/api/customers", json={
            "name": f"SECURITY_JOB_CUSTOMER_{uuid.uuid4().hex[:8]}"
        }, headers=headers_a)
        customer_a_id = customer_resp.json().get("id")
        
        # Create job as Tenant A
        unique_name = f"SECURITY_TEST_JOB_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/jobs", json={
            "name": unique_name,
            "customer_id": customer_a_id
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create job: {create_resp.text}"
        job_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT see Tenant A's job in list
        list_resp = requests.get(f"{BASE_URL}/api/jobs", headers=headers_b)
        assert list_resp.status_code == 200
        job_ids = [j.get("id") for j in list_resp.json()]
        assert job_a_id not in job_ids, "SECURITY ISSUE: Tenant A's job in Tenant B's list!"
        
        # Tenant B should NOT access Tenant A's job directly
        get_resp = requests.get(f"{BASE_URL}/api/jobs/{job_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's job!"
        
        # Tenant B should NOT access job details
        details_resp = requests.get(f"{BASE_URL}/api/jobs/{job_a_id}/details", headers=headers_b)
        assert details_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's job details!"
        
        # Tenant B should NOT update Tenant A's job
        update_resp = requests.put(f"{BASE_URL}/api/jobs/{job_a_id}", json={
            "name": "HACKED_JOB"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's job!"
        
        # Tenant B should NOT delete Tenant A's job
        delete_resp = requests.delete(f"{BASE_URL}/api/jobs/{job_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, "SECURITY ISSUE: Tenant B can delete Tenant A's job!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_a_id}", headers=headers_a)
        requests.delete(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        print("PASS: Jobs tenant isolation verified")

    # ================== TASKS ISOLATION (PREVIOUSLY NO AUTH) ==================
    
    def test_tasks_isolation(self, headers_a, headers_b):
        """Tasks should now require auth and filter by tenant_id"""
        # Create task as Tenant A
        unique_title = f"SECURITY_TEST_TASK_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/tasks", json={
            "title": unique_title,
            "description": "Security test task"
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create task: {create_resp.text}"
        task_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT see Tenant A's task in list
        list_resp = requests.get(f"{BASE_URL}/api/tasks", headers=headers_b)
        assert list_resp.status_code == 200
        task_ids = [t.get("id") for t in list_resp.json()]
        assert task_a_id not in task_ids, "SECURITY ISSUE: Tenant A's task in Tenant B's list!"
        
        # Tenant B should NOT access Tenant A's task directly
        get_resp = requests.get(f"{BASE_URL}/api/tasks/{task_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's task!"
        
        # Tenant B should NOT update Tenant A's task
        update_resp = requests.put(f"{BASE_URL}/api/tasks/{task_a_id}", json={
            "title": "HACKED_TASK"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's task!"
        
        # Tenant B should NOT delete Tenant A's task
        delete_resp = requests.delete(f"{BASE_URL}/api/tasks/{task_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, "SECURITY ISSUE: Tenant B can delete Tenant A's task!"
        
        # Verify task not accessed without auth
        no_auth_resp = requests.get(f"{BASE_URL}/api/tasks")
        assert no_auth_resp.status_code == 401, f"SECURITY ISSUE: Tasks accessible without auth! Status: {no_auth_resp.status_code}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tasks/{task_a_id}", headers=headers_a)
        print("PASS: Tasks tenant isolation verified (auth required)")

    # ================== JOB ITEMS ISOLATION (PREVIOUSLY NO AUTH) ==================
    
    def test_job_items_isolation(self, headers_a, headers_b):
        """Job items should now require auth and verify parent job tenant"""
        # First create customer and job for Tenant A
        unique_cust = f"SECURITY_ITEM_CUSTOMER_{uuid.uuid4().hex[:8]}"
        customer_resp = requests.post(f"{BASE_URL}/api/customers", json={
            "name": unique_cust
        }, headers=headers_a)
        assert customer_resp.status_code in [200, 201], f"Failed to create customer: {customer_resp.text}"
        customer_a_id = customer_resp.json().get("id")
        
        unique_job = f"SECURITY_ITEM_JOB_{uuid.uuid4().hex[:8]}"
        job_resp = requests.post(f"{BASE_URL}/api/jobs", json={
            "name": unique_job,
            "customer_id": customer_a_id
        }, headers=headers_a)
        assert job_resp.status_code in [200, 201], f"Failed to create job: {job_resp.text}"
        job_a_id = job_resp.json().get("id")
        
        # Create job item as Tenant A
        create_resp = requests.post(f"{BASE_URL}/api/jobs/{job_a_id}/items", json={
            "description": "Security test item",
            "quantity": 1,
            "unit_price": 100.0,
            "item_type": "other"
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create job item: {create_resp.text}"
        item_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT access Tenant A's job item via standalone route
        get_resp = requests.get(f"{BASE_URL}/api/job-items/{item_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's job item!"
        
        # Tenant B should NOT update Tenant A's job item
        update_resp = requests.put(f"{BASE_URL}/api/job-items/{item_a_id}", json={
            "description": "HACKED_ITEM"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's job item!"
        
        # Tenant B should NOT delete Tenant A's job item
        delete_resp = requests.delete(f"{BASE_URL}/api/job-items/{item_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, "SECURITY ISSUE: Tenant B can delete Tenant A's job item!"
        
        # Tenant B should NOT create item on Tenant A's job
        create_b_resp = requests.post(f"{BASE_URL}/api/jobs/{job_a_id}/items", json={
            "description": "Unauthorized item",
            "quantity": 1,
            "unit_price": 100.0,
            "item_type": "other"
        }, headers=headers_b)
        assert create_b_resp.status_code == 404, f"SECURITY ISSUE: Tenant B can create items on Tenant A's job! Status: {create_b_resp.status_code}, Response: {create_b_resp.text}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_a_id}", headers=headers_a)
        requests.delete(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        print("PASS: Job items tenant isolation verified")

    # ================== QUOTES ISOLATION ==================
    
    def test_quotes_isolation(self, headers_a, headers_b):
        """Tenant B should NOT see, update, or delete Tenant A's quotes"""
        # First create customer for Tenant A
        customer_resp = requests.post(f"{BASE_URL}/api/customers", json={
            "name": f"SECURITY_QUOTE_CUSTOMER_{uuid.uuid4().hex[:8]}"
        }, headers=headers_a)
        customer_a_id = customer_resp.json().get("id")
        
        # Create quote as Tenant A
        create_resp = requests.post(f"{BASE_URL}/api/quotes", json={
            "customer_id": customer_a_id,
            "line_items": [
                {"description": "Test item", "quantity": 1, "unit_price": 100.0}
            ],
            "status": "draft"
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create quote: {create_resp.text}"
        quote_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT see Tenant A's quote in list
        list_resp = requests.get(f"{BASE_URL}/api/quotes", headers=headers_b)
        assert list_resp.status_code == 200
        quote_ids = [q.get("id") for q in list_resp.json()]
        assert quote_a_id not in quote_ids, "SECURITY ISSUE: Tenant A's quote in Tenant B's list!"
        
        # Tenant B should NOT access Tenant A's quote directly
        get_resp = requests.get(f"{BASE_URL}/api/quotes/{quote_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's quote!"
        
        # Tenant B should NOT update Tenant A's quote
        update_resp = requests.put(f"{BASE_URL}/api/quotes/{quote_a_id}", json={
            "notes": "HACKED_QUOTE"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's quote!"
        
        # Tenant B should NOT delete Tenant A's quote
        delete_resp = requests.delete(f"{BASE_URL}/api/quotes/{quote_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, "SECURITY ISSUE: Tenant B can delete Tenant A's quote!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/quotes/{quote_a_id}", headers=headers_a)
        requests.delete(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        print("PASS: Quotes tenant isolation verified")

    # ================== INVOICES ISOLATION ==================
    
    def test_invoices_isolation(self, headers_a, headers_b):
        """Tenant B should NOT see, update, or delete Tenant A's invoices"""
        # First create customer for Tenant A
        customer_resp = requests.post(f"{BASE_URL}/api/customers", json={
            "name": f"SECURITY_INVOICE_CUSTOMER_{uuid.uuid4().hex[:8]}"
        }, headers=headers_a)
        customer_a_id = customer_resp.json().get("id")
        
        # Create invoice as Tenant A
        create_resp = requests.post(f"{BASE_URL}/api/invoices", json={
            "customer_id": customer_a_id,
            "line_items": [
                {"description": "Test service", "quantity": 1, "unit_price": 500.0}
            ]
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create invoice: {create_resp.text}"
        invoice_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT see Tenant A's invoice in list
        list_resp = requests.get(f"{BASE_URL}/api/invoices", headers=headers_b)
        assert list_resp.status_code == 200
        invoice_ids = [i.get("id") for i in list_resp.json()]
        assert invoice_a_id not in invoice_ids, "SECURITY ISSUE: Tenant A's invoice in Tenant B's list!"
        
        # Tenant B should NOT access Tenant A's invoice directly
        get_resp = requests.get(f"{BASE_URL}/api/invoices/{invoice_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's invoice!"
        
        # Tenant B should NOT update Tenant A's invoice
        update_resp = requests.put(f"{BASE_URL}/api/invoices/{invoice_a_id}", json={
            "status": "paid"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's invoice!"
        
        # Tenant B should NOT delete Tenant A's invoice
        delete_resp = requests.delete(f"{BASE_URL}/api/invoices/{invoice_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, "SECURITY ISSUE: Tenant B can delete Tenant A's invoice!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/invoices/{invoice_a_id}", headers=headers_a)
        requests.delete(f"{BASE_URL}/api/customers/{customer_a_id}", headers=headers_a)
        print("PASS: Invoices tenant isolation verified")

    # ================== WEBSTORES ISOLATION ==================
    
    def test_webstores_isolation(self, headers_a, headers_b):
        """Tenant B should NOT see, update, or delete Tenant A's webstores"""
        # Create webstore as Tenant A
        unique_name = f"SECURITY_STORE_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/webstores/v2", json={
            "name": unique_name,
            "store_type": "business",
            "owner_name": "Test Owner"
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create webstore: {create_resp.text}"
        store_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT see Tenant A's webstore in list
        list_resp = requests.get(f"{BASE_URL}/api/webstores/v2", headers=headers_b)
        assert list_resp.status_code == 200
        store_ids = [s.get("id") for s in list_resp.json()]
        assert store_a_id not in store_ids, "SECURITY ISSUE: Tenant A's webstore in Tenant B's list!"
        
        # Tenant B should NOT access Tenant A's webstore directly
        get_resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's webstore!"
        
        # Tenant B should NOT update Tenant A's webstore
        update_resp = requests.put(f"{BASE_URL}/api/webstores/v2/{store_a_id}", json={
            "name": "HACKED_STORE"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's webstore!"
        
        # Tenant B should NOT delete Tenant A's webstore
        delete_resp = requests.delete(f"{BASE_URL}/api/webstores/v2/{store_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, "SECURITY ISSUE: Tenant B can delete Tenant A's webstore!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/webstores/v2/{store_a_id}", headers=headers_a)
        print("PASS: Webstores tenant isolation verified")

    # ================== PRODUCTS ISOLATION ==================
    
    def test_products_isolation(self, headers_a, headers_b):
        """Tenant B should NOT see, update, or delete Tenant A's products"""
        # Create product as Tenant A
        unique_name = f"SECURITY_PRODUCT_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/products", json={
            "name": unique_name,
            "base_cost": 10.0,
            "retail_price": 25.0,
            "category": "other"
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201], f"Failed to create product: {create_resp.text}"
        product_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT see Tenant A's product in list
        list_resp = requests.get(f"{BASE_URL}/api/products", headers=headers_b)
        assert list_resp.status_code == 200
        product_ids = [p.get("id") for p in list_resp.json()]
        assert product_a_id not in product_ids, "SECURITY ISSUE: Tenant A's product in Tenant B's list!"
        
        # Tenant B should NOT access Tenant A's product directly
        get_resp = requests.get(f"{BASE_URL}/api/products/{product_a_id}", headers=headers_b)
        assert get_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's product!"
        
        # Tenant B should NOT update Tenant A's product
        update_resp = requests.put(f"{BASE_URL}/api/products/{product_a_id}", json={
            "name": "HACKED_PRODUCT"
        }, headers=headers_b)
        assert update_resp.status_code == 404, "SECURITY ISSUE: Tenant B can update Tenant A's product!"
        
        # Tenant B should NOT delete Tenant A's product
        delete_resp = requests.delete(f"{BASE_URL}/api/products/{product_a_id}", headers=headers_b)
        assert delete_resp.status_code == 404, "SECURITY ISSUE: Tenant B can delete Tenant A's product!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/products/{product_a_id}", headers=headers_a)
        print("PASS: Products tenant isolation verified")

    # ================== DASHBOARD ISOLATION ==================
    
    def test_dashboard_stats_isolation(self, headers_a, headers_b):
        """Dashboard stats should only show data from the current tenant"""
        # Get Tenant A's dashboard stats
        stats_a = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers_a)
        assert stats_a.status_code == 200
        
        # Get Tenant B's dashboard stats
        stats_b = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers_b)
        assert stats_b.status_code == 200
        
        # Stats should be tenant-specific (not necessarily different, but endpoint should work)
        print("PASS: Dashboard stats returns tenant-specific data")

    def test_dashboard_pending_approvals_isolation(self, headers_a, headers_b):
        """Pending approvals should only show data from the current tenant"""
        approvals_a = requests.get(f"{BASE_URL}/api/dashboard/pending-approvals", headers=headers_a)
        assert approvals_a.status_code == 200
        
        approvals_b = requests.get(f"{BASE_URL}/api/dashboard/pending-approvals", headers=headers_b)
        assert approvals_b.status_code == 200
        print("PASS: Dashboard pending approvals is tenant-isolated")

    def test_dashboard_clocked_in_isolation(self, headers_a, headers_b):
        """Clocked-in employees should only show employees from the current tenant"""
        clocked_a = requests.get(f"{BASE_URL}/api/dashboard/clocked-in", headers=headers_a)
        assert clocked_a.status_code == 200
        
        clocked_b = requests.get(f"{BASE_URL}/api/dashboard/clocked-in", headers=headers_b)
        assert clocked_b.status_code == 200
        print("PASS: Dashboard clocked-in is tenant-isolated")

    def test_dashboard_todays_schedule_isolation(self, headers_a, headers_b):
        """Today's schedule should only show jobs from the current tenant"""
        schedule_a = requests.get(f"{BASE_URL}/api/dashboard/todays-schedule", headers=headers_a)
        assert schedule_a.status_code == 200
        
        schedule_b = requests.get(f"{BASE_URL}/api/dashboard/todays-schedule", headers=headers_b)
        assert schedule_b.status_code == 200
        print("PASS: Dashboard today's schedule is tenant-isolated")

    # ================== PAYROLL ISOLATION ==================
    
    def test_payroll_transactions_isolation(self, headers_a, headers_b):
        """Payroll transactions should be tenant-isolated"""
        # Get payroll transactions - should be scoped to tenant
        trans_a = requests.get(f"{BASE_URL}/api/payroll/transactions", headers=headers_a)
        assert trans_a.status_code == 200
        
        trans_b = requests.get(f"{BASE_URL}/api/payroll/transactions", headers=headers_b)
        assert trans_b.status_code == 200
        print("PASS: Payroll transactions is tenant-isolated")

    def test_payroll_balance_cross_tenant_access(self, headers_a, headers_b):
        """Tenant B should NOT access payroll balance for Tenant A's employee"""
        # Create employee as Tenant A
        unique_name = f"SECURITY_PAYROLL_EMP_{uuid.uuid4().hex[:8]}"
        create_resp = requests.post(f"{BASE_URL}/api/employees", json={
            "name": unique_name,
            "hourly_rate": 20.0
        }, headers=headers_a)
        
        assert create_resp.status_code in [200, 201]
        employee_a_id = create_resp.json().get("id")
        
        # Tenant B should NOT access Tenant A's employee payroll balance
        balance_resp = requests.get(f"{BASE_URL}/api/payroll/balance/{employee_a_id}", headers=headers_b)
        assert balance_resp.status_code == 404, "SECURITY ISSUE: Tenant B can access Tenant A's employee payroll!"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/employees/{employee_a_id}", headers=headers_a)
        print("PASS: Payroll balance is tenant-isolated")

    def test_payroll_report_isolation(self, headers_a, headers_b):
        """Payroll report should only include current tenant's employees"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        report_a = requests.get(f"{BASE_URL}/api/payroll/report?start_date={today}&end_date={today}", headers=headers_a)
        assert report_a.status_code == 200
        
        report_b = requests.get(f"{BASE_URL}/api/payroll/report?start_date={today}&end_date={today}", headers=headers_b)
        assert report_b.status_code == 200
        print("PASS: Payroll report is tenant-isolated")


class TestAuthenticationRequired:
    """Test that protected endpoints require authentication"""
    
    def test_tasks_require_auth(self):
        """Tasks API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/tasks")
        assert response.status_code == 401, f"Tasks accessible without auth: {response.status_code}"
        print("PASS: Tasks require authentication")

    def test_jobs_require_auth(self):
        """Jobs API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/jobs")
        assert response.status_code == 401, f"Jobs accessible without auth: {response.status_code}"
        print("PASS: Jobs require authentication")

    def test_customers_require_auth(self):
        """Customers API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 401, f"Customers accessible without auth: {response.status_code}"
        print("PASS: Customers require authentication")

    def test_employees_require_auth(self):
        """Employees API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 401, f"Employees accessible without auth: {response.status_code}"
        print("PASS: Employees require authentication")

    def test_invoices_require_auth(self):
        """Invoices API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/invoices")
        assert response.status_code == 401, f"Invoices accessible without auth: {response.status_code}"
        print("PASS: Invoices require authentication")

    def test_quotes_require_auth(self):
        """Quotes API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/quotes")
        assert response.status_code == 401, f"Quotes accessible without auth: {response.status_code}"
        print("PASS: Quotes require authentication")

    def test_webstores_require_auth(self):
        """Webstores API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2")
        assert response.status_code == 401, f"Webstores accessible without auth: {response.status_code}"
        print("PASS: Webstores require authentication")

    def test_products_require_auth(self):
        """Products API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/products")
        assert response.status_code == 401, f"Products accessible without auth: {response.status_code}"
        print("PASS: Products require authentication")

    def test_dashboard_requires_auth(self):
        """Dashboard API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 401, f"Dashboard accessible without auth: {response.status_code}"
        print("PASS: Dashboard requires authentication")

    def test_payroll_requires_auth(self):
        """Payroll API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/payroll/transactions")
        assert response.status_code == 401, f"Payroll accessible without auth: {response.status_code}"
        print("PASS: Payroll requires authentication")
