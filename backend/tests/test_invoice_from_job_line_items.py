"""
Test invoice creation from job with line items
Verifies that invoice line_items are properly copied from job.line_items
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestInvoiceFromJobLineItems:
    """Test invoice line items copied from job.line_items"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and create test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Create test customer
        test_suffix = str(uuid.uuid4())[:8]
        self.customer_name = f"TEST_Customer_{test_suffix}"
        cust_response = self.session.post(f"{BASE_URL}/api/customers", json={
            "name": self.customer_name,
            "email": f"test_{test_suffix}@example.com",
            "status": "active"
        })
        assert cust_response.status_code == 200 or cust_response.status_code == 201, f"Customer creation failed: {cust_response.text}"
        self.customer_id = cust_response.json()["id"]
        
        yield
        
        # Cleanup - delete test data
        try:
            if hasattr(self, 'invoice_id') and self.invoice_id:
                self.session.delete(f"{BASE_URL}/api/invoices/{self.invoice_id}")
            if hasattr(self, 'job_id') and self.job_id:
                self.session.delete(f"{BASE_URL}/api/jobs/{self.job_id}")
            if hasattr(self, 'customer_id') and self.customer_id:
                self.session.delete(f"{BASE_URL}/api/customers/{self.customer_id}")
        except:
            pass
    
    def test_create_job_with_line_items(self):
        """Create a job with line_items"""
        self.job_id = None
        self.invoice_id = None
        
        # Create job with line_items
        job_data = {
            "customer_id": self.customer_id,
            "name": "TEST_Job_With_Line_Items",
            "description": "Test job for invoice line items",
            "status": "approved",
            "line_items": [
                {"description": "Banner 4x8 ft", "quantity": 2, "unit_price": 150.00},
                {"description": "Installation Fee", "quantity": 1, "unit_price": 75.00},
                {"description": "Design Work", "quantity": 3, "unit_price": 50.00}
            ]
        }
        
        response = self.session.post(f"{BASE_URL}/api/jobs", json=job_data)
        assert response.status_code in [200, 201], f"Job creation failed: {response.text}"
        
        job = response.json()
        self.job_id = job["id"]
        print(f"✅ Job created: {self.job_id}")
        print(f"   Job line_items: {job.get('line_items', [])}")
        
        # Verify job has line_items stored
        assert "line_items" in job, "Job should have line_items"
        assert len(job["line_items"]) == 3, f"Job should have 3 line_items, got {len(job['line_items'])}"
        
    def test_create_invoice_from_job_copies_line_items(self):
        """Create invoice from job and verify line_items are copied"""
        self.job_id = None
        self.invoice_id = None
        
        # First create job with line_items
        job_data = {
            "customer_id": self.customer_id,
            "name": "TEST_Job_Invoice_Line_Items",
            "description": "Test job for invoice line items copy",
            "status": "approved",
            "line_items": [
                {"description": "Vinyl Banner Large", "quantity": 1, "unit_price": 200.00},
                {"description": "Rush Fee", "quantity": 1, "unit_price": 50.00}
            ]
        }
        
        job_response = self.session.post(f"{BASE_URL}/api/jobs", json=job_data)
        assert job_response.status_code in [200, 201], f"Job creation failed: {job_response.text}"
        
        job = job_response.json()
        self.job_id = job["id"]
        print(f"✅ Job created with {len(job.get('line_items', []))} line items")
        
        # Create invoice from job
        invoice_response = self.session.post(f"{BASE_URL}/api/invoices/from-job/{self.job_id}")
        assert invoice_response.status_code in [200, 201], f"Invoice from job failed: {invoice_response.text}"
        
        invoice = invoice_response.json()
        self.invoice_id = invoice["id"]
        print(f"✅ Invoice created: {self.invoice_id}")
        print(f"   Invoice line_items: {invoice.get('line_items', [])}")
        print(f"   Invoice total: {invoice.get('total', 0)}")
        
        # CRITICAL CHECK: Verify invoice has line_items
        assert "line_items" in invoice, "Invoice should have line_items field"
        assert len(invoice.get("line_items", [])) > 0, "Invoice should have at least one line item"
        
        # Verify line items match original job
        invoice_items = invoice.get("line_items", [])
        assert len(invoice_items) == 2, f"Invoice should have 2 line items, got {len(invoice_items)}"
        
        # Check descriptions are preserved
        descriptions = [item.get("description") for item in invoice_items]
        assert "Vinyl Banner Large" in descriptions, "Should have 'Vinyl Banner Large' item"
        assert "Rush Fee" in descriptions, "Should have 'Rush Fee' item"
        
        # Check total is calculated correctly (200 + 50 = 250)
        assert invoice.get("total") == 250.0, f"Invoice total should be 250.00, got {invoice.get('total')}"
        
        print("✅ PASS: Invoice line_items correctly copied from job.line_items")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
