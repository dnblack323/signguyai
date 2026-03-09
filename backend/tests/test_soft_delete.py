"""
Soft Delete Feature Tests

This module tests soft delete and restore functionality across all models:
- Invoices: DELETE /api/invoices/{id}, POST /api/invoices/{id}/restore
- Quotes: DELETE /api/quotes/{id}, POST /api/quotes/{id}/restore
- Products: DELETE /api/products/{id}, POST /api/products/{id}/restore
- Webstores: DELETE /api/webstores/v2/{id}, POST /api/webstores/v2/{id}/restore
- Employees: DELETE /api/employees/{id}, POST /api/employees/{id}/restore

Test scenarios:
1. Soft delete sets deleted_at (not permanent removal)
2. GET list excludes soft-deleted records by default
3. GET deleted/list returns soft-deleted records
4. Restore brings back soft-deleted records
5. Permanent delete (permanent=true) removes record entirely
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
TEST_EMAIL = "thesigntistslab@gmail.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Auth failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ============== INVOICES SOFT DELETE TESTS ==============

class TestInvoicesSoftDelete:
    """Tests for invoices soft delete and restore"""
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_headers):
        """Create a test customer for invoice testing"""
        customer_data = {
            "name": f"TEST_SoftDelete_Customer_{uuid.uuid4().hex[:8]}",
            "email": f"test_sd_{uuid.uuid4().hex[:8]}@example.com",
            "phone": "555-0199"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=customer_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        return response.json()
    
    @pytest.fixture(scope="class")
    def test_invoice(self, auth_headers, test_customer):
        """Create a test invoice for soft delete testing"""
        invoice_data = {
            "customer_id": test_customer["id"],
            "line_items": [
                {"description": "Test Item", "quantity": 1, "unit_price": 100}
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/invoices",
            json=invoice_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create invoice: {response.text}"
        return response.json()
    
    def test_soft_delete_invoice(self, auth_headers, test_invoice):
        """Test that DELETE sets deleted_at instead of removing"""
        invoice_id = test_invoice["id"]
        
        # Soft delete
        response = requests.delete(
            f"{BASE_URL}/api/invoices/{invoice_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Soft delete failed: {response.text}"
        assert "can be restored" in response.json()["message"]
    
    def test_invoice_hidden_from_list_after_soft_delete(self, auth_headers, test_invoice):
        """Test that soft-deleted invoice is not in regular list"""
        invoice_id = test_invoice["id"]
        
        # Get regular list
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        invoice_ids = [inv["id"] for inv in response.json()]
        assert invoice_id not in invoice_ids, "Soft-deleted invoice should not appear in list"
    
    def test_invoice_in_deleted_list(self, auth_headers, test_invoice):
        """Test that soft-deleted invoice appears in deleted/list"""
        invoice_id = test_invoice["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/invoices/deleted/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        deleted = response.json()
        assert "deleted_invoices" in deleted
        deleted_ids = [inv["id"] for inv in deleted["deleted_invoices"]]
        assert invoice_id in deleted_ids, "Soft-deleted invoice should appear in deleted list"
    
    def test_restore_invoice(self, auth_headers, test_invoice):
        """Test restoring a soft-deleted invoice"""
        invoice_id = test_invoice["id"]
        
        # Restore
        response = requests.post(
            f"{BASE_URL}/api/invoices/{invoice_id}/restore",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Restore failed: {response.text}"
        assert "restored" in response.json()["message"].lower()
        
        # Verify back in list
        list_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        invoice_ids = [inv["id"] for inv in list_response.json()]
        assert invoice_id in invoice_ids, "Restored invoice should appear in list"
    
    def test_permanent_delete_invoice(self, auth_headers, test_customer):
        """Test permanent delete with permanent=true"""
        # Create a new invoice for permanent delete
        invoice_data = {
            "customer_id": test_customer["id"],
            "line_items": [
                {"description": "Temp Item", "quantity": 1, "unit_price": 50}
            ]
        }
        create_response = requests.post(
            f"{BASE_URL}/api/invoices",
            json=invoice_data,
            headers=auth_headers
        )
        invoice_id = create_response.json()["id"]
        
        # Permanent delete
        response = requests.delete(
            f"{BASE_URL}/api/invoices/{invoice_id}?permanent=true",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Permanent delete failed: {response.text}"
        assert "permanently" in response.json()["message"].lower()
        
        # Verify not in deleted list either
        deleted_response = requests.get(
            f"{BASE_URL}/api/invoices/deleted/list",
            headers=auth_headers
        )
        deleted_ids = [inv["id"] for inv in deleted_response.json().get("deleted_invoices", [])]
        assert invoice_id not in deleted_ids, "Permanently deleted invoice should not be in deleted list"


# ============== QUOTES SOFT DELETE TESTS ==============

class TestQuotesSoftDelete:
    """Tests for quotes soft delete and restore"""
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_headers):
        """Create a test customer for quote testing"""
        customer_data = {
            "name": f"TEST_Quote_Customer_{uuid.uuid4().hex[:8]}",
            "email": f"test_quote_{uuid.uuid4().hex[:8]}@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers",
            json=customer_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        return response.json()
    
    @pytest.fixture(scope="class")
    def test_quote(self, auth_headers, test_customer):
        """Create a test quote for soft delete testing"""
        quote_data = {
            "customer_id": test_customer["id"],
            "line_items": [
                {"description": "Quote Item", "quantity": 2, "unit_price": 75}
            ],
            "status": "draft"
        }
        response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=quote_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create quote: {response.text}"
        return response.json()
    
    def test_soft_delete_quote(self, auth_headers, test_quote):
        """Test that DELETE sets deleted_at"""
        quote_id = test_quote["id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/quotes/{quote_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Soft delete failed: {response.text}"
        assert "can be restored" in response.json()["message"]
    
    def test_quote_hidden_from_list(self, auth_headers, test_quote):
        """Test soft-deleted quote hidden from list"""
        quote_id = test_quote["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/quotes",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        quote_ids = [q["id"] for q in response.json()]
        assert quote_id not in quote_ids
    
    def test_quote_in_deleted_list(self, auth_headers, test_quote):
        """Test soft-deleted quote in deleted/list"""
        quote_id = test_quote["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/quotes/deleted/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        deleted_ids = [q["id"] for q in response.json().get("deleted_quotes", [])]
        assert quote_id in deleted_ids
    
    def test_restore_quote(self, auth_headers, test_quote):
        """Test restoring soft-deleted quote"""
        quote_id = test_quote["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/quotes/{quote_id}/restore",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify back in list
        list_response = requests.get(
            f"{BASE_URL}/api/quotes",
            headers=auth_headers
        )
        quote_ids = [q["id"] for q in list_response.json()]
        assert quote_id in quote_ids
    
    def test_permanent_delete_quote(self, auth_headers, test_customer):
        """Test permanent delete for quote"""
        # Create new quote
        quote_data = {
            "customer_id": test_customer["id"],
            "line_items": [{"description": "Temp", "quantity": 1, "unit_price": 25}]
        }
        create_response = requests.post(
            f"{BASE_URL}/api/quotes",
            json=quote_data,
            headers=auth_headers
        )
        quote_id = create_response.json()["id"]
        
        # Permanent delete
        response = requests.delete(
            f"{BASE_URL}/api/quotes/{quote_id}?permanent=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "permanently" in response.json()["message"].lower()


# ============== PRODUCTS SOFT DELETE TESTS ==============

class TestProductsSoftDelete:
    """Tests for products soft delete and restore"""
    
    @pytest.fixture(scope="class")
    def test_product(self, auth_headers):
        """Create a test product for soft delete testing"""
        product_data = {
            "name": f"TEST_Product_{uuid.uuid4().hex[:8]}",
            "description": "Test product for soft delete",
            "category": "other",
            "base_cost": 50,
            "retail_price": 100
        }
        response = requests.post(
            f"{BASE_URL}/api/products",
            json=product_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create product: {response.text}"
        return response.json()
    
    def test_soft_delete_product(self, auth_headers, test_product):
        """Test that DELETE sets deleted_at"""
        product_id = test_product["id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/products/{product_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Soft delete failed: {response.text}"
        assert "can be restored" in response.json()["message"]
    
    def test_product_hidden_from_list(self, auth_headers, test_product):
        """Test soft-deleted product hidden from list"""
        product_id = test_product["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/products",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        product_ids = [p["id"] for p in response.json()]
        assert product_id not in product_ids
    
    def test_product_in_deleted_list(self, auth_headers, test_product):
        """Test soft-deleted product in deleted/list"""
        product_id = test_product["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/products/deleted/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        deleted_ids = [p["id"] for p in response.json().get("deleted_products", [])]
        assert product_id in deleted_ids
    
    def test_restore_product(self, auth_headers, test_product):
        """Test restoring soft-deleted product"""
        product_id = test_product["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/products/{product_id}/restore",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify back in list
        list_response = requests.get(
            f"{BASE_URL}/api/products",
            headers=auth_headers
        )
        product_ids = [p["id"] for p in list_response.json()]
        assert product_id in product_ids
    
    def test_permanent_delete_product(self, auth_headers):
        """Test permanent delete for product"""
        # Create new product
        product_data = {
            "name": f"TEST_TempProduct_{uuid.uuid4().hex[:8]}",
            "base_cost": 10,
            "retail_price": 20
        }
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            json=product_data,
            headers=auth_headers
        )
        product_id = create_response.json()["id"]
        
        # Permanent delete
        response = requests.delete(
            f"{BASE_URL}/api/products/{product_id}?permanent=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "permanently" in response.json()["message"].lower()


# ============== WEBSTORES SOFT DELETE TESTS ==============

class TestWebstoresSoftDelete:
    """Tests for webstores soft delete and restore"""
    
    @pytest.fixture(scope="class")
    def test_webstore(self, auth_headers):
        """Create a test webstore for soft delete testing"""
        webstore_data = {
            "name": f"TEST_Webstore_{uuid.uuid4().hex[:8]}",
            "store_type": "business",
            "owner_name": "Test Owner",
            "owner_email": "test@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            json=webstore_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create webstore: {response.text}"
        return response.json()
    
    def test_soft_delete_webstore(self, auth_headers, test_webstore):
        """Test that DELETE sets deleted_at"""
        webstore_id = test_webstore["id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Soft delete failed: {response.text}"
        assert "can be restored" in response.json()["message"]
    
    def test_webstore_hidden_from_list(self, auth_headers, test_webstore):
        """Test soft-deleted webstore hidden from list"""
        webstore_id = test_webstore["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        webstore_ids = [w["id"] for w in response.json()]
        assert webstore_id not in webstore_ids
    
    def test_webstore_in_deleted_list(self, auth_headers, test_webstore):
        """Test soft-deleted webstore in deleted/list"""
        webstore_id = test_webstore["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/deleted/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        deleted_ids = [w["id"] for w in response.json().get("deleted_webstores", [])]
        assert webstore_id in deleted_ids
    
    def test_restore_webstore(self, auth_headers, test_webstore):
        """Test restoring soft-deleted webstore"""
        webstore_id = test_webstore["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}/restore",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify back in list
        list_response = requests.get(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers
        )
        webstore_ids = [w["id"] for w in list_response.json()]
        assert webstore_id in webstore_ids
    
    def test_permanent_delete_webstore(self, auth_headers):
        """Test permanent delete for webstore"""
        # Create new webstore
        webstore_data = {
            "name": f"TEST_TempWebstore_{uuid.uuid4().hex[:8]}",
            "store_type": "fundraiser",
            "owner_name": "Temp Owner"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            json=webstore_data,
            headers=auth_headers
        )
        webstore_id = create_response.json()["id"]
        
        # Permanent delete
        response = requests.delete(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}?permanent=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "permanently" in response.json()["message"].lower()


# ============== EMPLOYEES SOFT DELETE TESTS ==============

class TestEmployeesSoftDelete:
    """Tests for employees soft delete and restore"""
    
    @pytest.fixture(scope="class")
    def test_employee(self, auth_headers):
        """Create a test employee for soft delete testing"""
        employee_data = {
            "name": f"TEST_Employee_{uuid.uuid4().hex[:8]}",
            "email": f"test_emp_{uuid.uuid4().hex[:8]}@example.com",
            "hourly_rate": 25,
            "role": "staff"
        }
        response = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create employee: {response.text}"
        return response.json()
    
    def test_soft_delete_employee(self, auth_headers, test_employee):
        """Test that DELETE sets deleted_at"""
        employee_id = test_employee["id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Soft delete failed: {response.text}"
        assert "can be restored" in response.json()["message"]
    
    def test_employee_hidden_from_list(self, auth_headers, test_employee):
        """Test soft-deleted employee hidden from list"""
        employee_id = test_employee["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        employee_ids = [e["id"] for e in response.json()]
        assert employee_id not in employee_ids
    
    def test_employee_in_deleted_list(self, auth_headers, test_employee):
        """Test soft-deleted employee in deleted/list"""
        employee_id = test_employee["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/employees/deleted/list",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        deleted_ids = [e["id"] for e in response.json().get("deleted_employees", [])]
        assert employee_id in deleted_ids
    
    def test_restore_employee(self, auth_headers, test_employee):
        """Test restoring soft-deleted employee"""
        employee_id = test_employee["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/employees/{employee_id}/restore",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        # Verify back in list
        list_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=auth_headers
        )
        employee_ids = [e["id"] for e in list_response.json()]
        assert employee_id in employee_ids
    
    def test_permanent_delete_employee(self, auth_headers):
        """Test permanent delete for employee"""
        # Create new employee
        employee_data = {
            "name": f"TEST_TempEmployee_{uuid.uuid4().hex[:8]}",
            "hourly_rate": 15
        }
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        employee_id = create_response.json()["id"]
        
        # Permanent delete
        response = requests.delete(
            f"{BASE_URL}/api/employees/{employee_id}?permanent=true",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "permanently" in response.json()["message"].lower()


# ============== EDGE CASE TESTS ==============

class TestSoftDeleteEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_restore_non_deleted_record_fails(self, auth_headers):
        """Test that restoring a non-deleted record fails appropriately"""
        # Create a fresh product (not deleted)
        product_data = {
            "name": f"TEST_NotDeleted_{uuid.uuid4().hex[:8]}",
            "base_cost": 10,
            "retail_price": 20
        }
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            json=product_data,
            headers=auth_headers
        )
        product_id = create_response.json()["id"]
        
        # Try to restore (should fail - not deleted)
        response = requests.post(
            f"{BASE_URL}/api/products/{product_id}/restore",
            headers=auth_headers
        )
        assert response.status_code == 404, "Should fail to restore non-deleted record"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/products/{product_id}?permanent=true",
            headers=auth_headers
        )
    
    def test_double_soft_delete_fails(self, auth_headers):
        """Test that double soft delete fails appropriately"""
        # Create and soft delete a product
        product_data = {
            "name": f"TEST_DoubleDelete_{uuid.uuid4().hex[:8]}",
            "base_cost": 10,
            "retail_price": 20
        }
        create_response = requests.post(
            f"{BASE_URL}/api/products",
            json=product_data,
            headers=auth_headers
        )
        product_id = create_response.json()["id"]
        
        # First soft delete (should succeed)
        first_delete = requests.delete(
            f"{BASE_URL}/api/products/{product_id}",
            headers=auth_headers
        )
        assert first_delete.status_code == 200
        
        # Second soft delete (should fail - already deleted)
        second_delete = requests.delete(
            f"{BASE_URL}/api/products/{product_id}",
            headers=auth_headers
        )
        assert second_delete.status_code == 404, "Should fail to soft delete already deleted record"
        
        # Cleanup - permanently delete
        requests.delete(
            f"{BASE_URL}/api/products/{product_id}?permanent=true",
            headers=auth_headers
        )
    
    def test_get_single_record_excludes_deleted(self, auth_headers):
        """Test that GET single record returns 404 for soft-deleted"""
        # Create and soft delete an employee
        employee_data = {
            "name": f"TEST_SingleGet_{uuid.uuid4().hex[:8]}",
            "hourly_rate": 20
        }
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            json=employee_data,
            headers=auth_headers
        )
        employee_id = create_response.json()["id"]
        
        # Soft delete
        requests.delete(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers=auth_headers
        )
        
        # GET single should return 404
        get_response = requests.get(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404, "GET single should return 404 for soft-deleted"
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{employee_id}?permanent=true",
            headers=auth_headers
        )
