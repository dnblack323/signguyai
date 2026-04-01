"""
Job Line Items Sync Tests - Iteration 66
Tests for the fix where job line_items weren't showing on Job Details

Verifies:
1. Creating job with manually typed line_items persists and shows on Job Details
2. Creating job via Save & Add Job path persists line_items
3. Pricing calculator items persist and show on Job Details
4. GET /api/jobs/{job_id}/details returns job_items for embedded line_items
5. GET /api/jobs/{job_id}/items returns synced items
6. POST /api/invoices/from-job/{job_id} includes restored job items
7. No duplicate line items on repeated reads
8. No regression on editing/deleting line items after sync
"""
import pytest
import requests
import os
import time
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return auth headers for API calls"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_customer(auth_headers):
    """Get or create a test customer for job creation"""
    # Try to get existing customers
    response = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
    if response.status_code == 200 and len(response.json()) > 0:
        return response.json()[0]
    
    # Create a new customer if none exist
    customer_data = {
        "name": "TEST_LineItemSync_Customer",
        "email": "test_lineitems@example.com",
        "phone": "555-0123"
    }
    response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=auth_headers)
    if response.status_code in [200, 201]:
        return response.json()
    pytest.skip(f"Failed to create test customer: {response.status_code}")


class TestJobCreationWithLineItems:
    """Tests for job creation with manually typed line items"""
    
    def test_create_job_with_manual_line_items_from_jobs_page(self, auth_headers, test_customer):
        """Test: Creating a new job with manually typed line_items from Jobs page persists items"""
        # Create job with manual line items (simulating Jobs page creation)
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_ManualLineItems_Job",
            "description": "Test job for manual line items",
            "status": "approved",
            "line_items": [
                {"description": "Banner 3x6", "quantity": 2, "unit_price": 150.00},
                {"description": "Yard Sign 18x24", "quantity": 10, "unit_price": 25.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        assert response.status_code in [200, 201], f"Failed to create job: {response.text}"
        
        job = response.json()
        job_id = job["id"]
        
        # Verify line_items were embedded in job
        assert "line_items" in job, "line_items not in job response"
        assert len(job["line_items"]) == 2, f"Expected 2 line items, got {len(job['line_items'])}"
        
        # Verify totals calculated
        expected_total = (2 * 150) + (10 * 25)  # 300 + 250 = 550
        assert job.get("subtotal") == expected_total or job.get("total") == expected_total, \
            f"Total mismatch: expected {expected_total}, got subtotal={job.get('subtotal')}, total={job.get('total')}"
        
        # Now verify GET /api/jobs/{job_id}/details returns job_items
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        assert details_response.status_code == 200, f"Failed to get job details: {details_response.text}"
        
        details = details_response.json()
        assert "job_items" in details, "job_items not in details response"
        assert len(details["job_items"]) == 2, f"Expected 2 job_items, got {len(details['job_items'])}"
        
        # Verify item descriptions match
        item_descriptions = [item["description"] for item in details["job_items"]]
        assert "Banner 3x6" in item_descriptions, "Banner item not found"
        assert "Yard Sign 18x24" in item_descriptions, "Yard Sign item not found"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)
        
    def test_create_job_via_save_and_add_path(self, auth_headers, test_customer):
        """Test: Creating job via Save & Add Job path from Customers page persists line_items"""
        # This simulates Route B - Save & Add Job after creating/editing a customer
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_SaveAndAddJob_Route",
            "description": "Test job via save and add path",
            "status": "approved",  # Direct job creation (not quote)
            "line_items": [
                {"description": "Vehicle Wrap - Full", "quantity": 1, "unit_price": 2500.00},
                {"description": "Installation Labor", "quantity": 4, "unit_price": 75.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        assert response.status_code in [200, 201], f"Failed to create job: {response.text}"
        
        job = response.json()
        job_id = job["id"]
        
        # Verify job_items via /details endpoint
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        assert details_response.status_code == 200
        
        details = details_response.json()
        assert len(details["job_items"]) == 2, f"Expected 2 items, got {len(details['job_items'])}"
        
        # Verify individual item values
        wrap_item = next((i for i in details["job_items"] if "Wrap" in i["description"]), None)
        assert wrap_item is not None, "Vehicle Wrap item not found"
        assert wrap_item["quantity"] == 1
        assert wrap_item["unit_price"] == 2500.00
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)
    
    def test_create_quote_with_line_items_then_approve(self, auth_headers, test_customer):
        """Test: Creating a quote with line_items, then approving shows items on Job Details"""
        # Create as quote first
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_QuoteToJob_LineItems",
            "status": "quote",
            "line_items": [
                {"description": "Window Graphics", "quantity": 5, "unit_price": 120.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        job = response.json()
        job_id = job["id"]
        assert job["status"] == "quote"
        
        # Approve the quote
        approve_response = requests.post(f"{BASE_URL}/api/jobs/{job_id}/approve", headers=auth_headers)
        assert approve_response.status_code == 200, f"Failed to approve: {approve_response.text}"
        
        # Verify items still accessible after approval
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        assert details_response.status_code == 200
        
        details = details_response.json()
        assert details["job"]["status"] == "approved"
        assert len(details["job_items"]) == 1
        assert details["job_items"][0]["description"] == "Window Graphics"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)


class TestGetJobItemsEndpoint:
    """Tests for GET /api/jobs/{job_id}/items endpoint"""
    
    def test_get_job_items_returns_synced_items(self, auth_headers, test_customer):
        """Test: GET /api/jobs/{job_id}/items returns synced items for jobs with embedded line_items"""
        # Create job with embedded line_items
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_GetItems_Sync",
            "status": "approved",
            "line_items": [
                {"description": "Decal Set", "quantity": 20, "unit_price": 5.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        job = response.json()
        job_id = job["id"]
        
        # Test the /items endpoint directly
        items_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/items", headers=auth_headers)
        assert items_response.status_code == 200
        
        items = items_response.json()
        assert len(items) == 1, f"Expected 1 item, got {len(items)}"
        assert items[0]["description"] == "Decal Set"
        assert items[0]["quantity"] == 20
        assert items[0]["unit_price"] == 5.00
        assert items[0]["line_total"] == 100.00  # 20 * 5
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)


class TestNoDuplicateItems:
    """Tests to verify no duplicate line items are created on repeated reads"""
    
    def test_no_duplicates_on_repeated_details_calls(self, auth_headers, test_customer):
        """Test: No duplicate line items created on repeated GET /details calls"""
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_NoDuplicates_Job",
            "status": "approved",
            "line_items": [
                {"description": "Test Item Alpha", "quantity": 1, "unit_price": 100.00},
                {"description": "Test Item Beta", "quantity": 2, "unit_price": 50.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        job = response.json()
        job_id = job["id"]
        
        # Call /details multiple times
        for i in range(3):
            details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
            assert details_response.status_code == 200
            details = details_response.json()
            
            # Should always be exactly 2 items, no duplicates
            assert len(details["job_items"]) == 2, \
                f"Call {i+1}: Expected 2 items, got {len(details['job_items'])} - possible duplicates!"
        
        # Also test /items endpoint
        for i in range(3):
            items_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/items", headers=auth_headers)
            items = items_response.json()
            assert len(items) == 2, f"Items call {i+1}: Expected 2, got {len(items)}"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)


class TestInvoiceFromJobWithLineItems:
    """Tests for invoice creation from jobs with line items"""
    
    def test_invoice_from_job_includes_line_items(self, auth_headers, test_customer):
        """Test: POST /api/invoices/from-job/{job_id} includes restored job items in invoice"""
        # Create job with line items
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_InvoiceFromJob_LineItems",
            "status": "approved",
            "line_items": [
                {"description": "Invoice Test Item 1", "quantity": 3, "unit_price": 200.00},
                {"description": "Invoice Test Item 2", "quantity": 1, "unit_price": 150.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        job = response.json()
        job_id = job["id"]
        
        # Create invoice from job
        invoice_response = requests.post(f"{BASE_URL}/api/invoices/from-job/{job_id}", headers=auth_headers)
        assert invoice_response.status_code in [200, 201], f"Failed to create invoice: {invoice_response.text}"
        
        invoice = invoice_response.json()
        
        # Verify invoice has line_items
        assert "line_items" in invoice, "line_items not in invoice"
        assert len(invoice["line_items"]) == 2, f"Expected 2 invoice line items, got {len(invoice['line_items'])}"
        
        # Verify total
        expected_total = (3 * 200) + (1 * 150)  # 600 + 150 = 750
        assert invoice["total"] == expected_total, f"Total mismatch: expected {expected_total}, got {invoice['total']}"
        
        # Verify individual items
        item_descriptions = [item["description"] for item in invoice["line_items"]]
        assert "Invoice Test Item 1" in item_descriptions
        assert "Invoice Test Item 2" in item_descriptions
        
        # Cleanup - delete invoice first, then job
        requests.delete(f"{BASE_URL}/api/invoices/{invoice['id']}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)


class TestEditDeleteJobItemsAfterSync:
    """Tests for editing and deleting job items after sync"""
    
    def test_edit_job_item_after_sync(self, auth_headers, test_customer):
        """Test: Editing a synced job item works correctly"""
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_EditItem_AfterSync",
            "status": "approved",
            "line_items": [
                {"description": "Editable Item", "quantity": 1, "unit_price": 100.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        job = response.json()
        job_id = job["id"]
        
        # Get the synced items
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        details = details_response.json()
        assert len(details["job_items"]) == 1
        
        item_id = details["job_items"][0]["id"]
        
        # Edit the item
        update_data = {
            "description": "Updated Editable Item",
            "quantity": 5,
            "unit_price": 120.00
        }
        
        edit_response = requests.put(f"{BASE_URL}/api/job-items/{item_id}", json=update_data, headers=auth_headers)
        assert edit_response.status_code == 200, f"Failed to edit item: {edit_response.text}"
        
        updated_item = edit_response.json()
        assert updated_item["description"] == "Updated Editable Item"
        assert updated_item["quantity"] == 5
        assert updated_item["unit_price"] == 120.00
        assert updated_item["line_total"] == 600.00  # 5 * 120
        
        # Verify via details endpoint
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        details = details_response.json()
        assert details["job_items"][0]["description"] == "Updated Editable Item"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)
    
    def test_delete_job_item_after_sync(self, auth_headers, test_customer):
        """Test: Deleting a synced job item works correctly"""
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_DeleteItem_AfterSync",
            "status": "approved",
            "line_items": [
                {"description": "Keep This Item", "quantity": 1, "unit_price": 50.00},
                {"description": "Delete This Item", "quantity": 1, "unit_price": 75.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        job = response.json()
        job_id = job["id"]
        
        # Get items
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        details = details_response.json()
        assert len(details["job_items"]) == 2
        
        # Find the item to delete
        item_to_delete = next((i for i in details["job_items"] if "Delete" in i["description"]), None)
        assert item_to_delete is not None
        
        # Delete the item
        delete_response = requests.delete(f"{BASE_URL}/api/job-items/{item_to_delete['id']}", headers=auth_headers)
        assert delete_response.status_code == 200, f"Failed to delete item: {delete_response.text}"
        
        # Verify only one item remains
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        details = details_response.json()
        assert len(details["job_items"]) == 1
        assert details["job_items"][0]["description"] == "Keep This Item"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)


class TestPricingCalculatorItems:
    """Tests for items added via pricing calculator"""
    
    def test_pricing_calculator_items_persist(self, auth_headers, test_customer):
        """Test: Pricing calculator-added line items persist and show on Job Details"""
        # Pricing calculator items typically have additional fields like pricing_category, cost_snapshot
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_PricingCalc_Items",
            "status": "approved",
            "line_items": [
                {
                    "description": "Digital Print Banner 4x8",
                    "quantity": 2,
                    "unit_price": 180.00,
                    "pricing_category": "digital_print",
                    "pricing_data": {
                        "width": 4,
                        "height": 8,
                        "material": "vinyl"
                    },
                    "cost_snapshot": {
                        "total_cost": 95.00,
                        "profit_amount": 265.00,
                        "profit_margin_percent": 73.6
                    }
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        assert response.status_code in [200, 201]
        
        job = response.json()
        job_id = job["id"]
        
        # Verify via details
        details_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
        details = details_response.json()
        
        assert len(details["job_items"]) == 1
        item = details["job_items"][0]
        
        assert item["description"] == "Digital Print Banner 4x8"
        assert item["quantity"] == 2
        assert item["unit_price"] == 180.00
        assert item["line_total"] == 360.00
        
        # Verify pricing metadata persisted
        assert item.get("pricing_category") == "digital_print"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)


class TestJobUpdateWithLineItems:
    """Tests for updating jobs with line items"""
    
    def test_update_job_line_items_resyncs(self, auth_headers, test_customer):
        """Test: Updating job line_items triggers resync"""
        # Create initial job
        job_data = {
            "customer_id": test_customer["id"],
            "name": "TEST_UpdateLineItems_Resync",
            "status": "approved",
            "line_items": [
                {"description": "Original Item", "quantity": 1, "unit_price": 100.00}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=auth_headers)
        job = response.json()
        job_id = job["id"]
        
        # Verify initial state
        details = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers).json()
        assert len(details["job_items"]) == 1
        
        # Update job with new line items
        update_data = {
            "line_items": [
                {"description": "Updated Item A", "quantity": 2, "unit_price": 150.00},
                {"description": "Updated Item B", "quantity": 3, "unit_price": 50.00}
            ]
        }
        
        update_response = requests.put(f"{BASE_URL}/api/jobs/{job_id}", json=update_data, headers=auth_headers)
        assert update_response.status_code == 200
        
        # Verify new items synced
        details = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers).json()
        assert len(details["job_items"]) == 2, f"Expected 2 items after update, got {len(details['job_items'])}"
        
        item_descriptions = [i["description"] for i in details["job_items"]]
        assert "Updated Item A" in item_descriptions
        assert "Updated Item B" in item_descriptions
        assert "Original Item" not in item_descriptions  # Old item should be replaced
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)
