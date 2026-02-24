"""
Test Suite for Unified Jobs System (Iteration 36)

Tests the major refactor where Quotes and Jobs are unified into a single Job system.
A quote is now a job with status='quote'.

Key features tested:
- Job creation with status='quote' (via New Quote option)
- Job creation with status='approved' (via New Job option)
- Job status filtering - All Jobs, Quotes (Pipeline), Active (Production), Completed, Invoiced, Archived
- Job approve action - POST /api/jobs/{id}/approve should change status from 'quote' to 'approved'
- Dashboard stats - Active Jobs should NOT include jobs with status='quote'
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://checkout-flow-v2-1.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "testuser123@test.com"
TEST_PASSWORD = "Test123!"

# Test data prefix for cleanup
TEST_PREFIX = "TEST_JOB_UNIFIED_"


class TestJobsUnifiedSystem:
    """Test the unified Jobs system where quotes are jobs with status=quote"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token_data = login_response.json()
        assert "access_token" in token_data, "No access_token in response"
        
        self.token = token_data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get or create a test customer
        self.customer_id = self._get_or_create_test_customer()
        
        yield
        
        # Cleanup: Delete test jobs
        self._cleanup_test_jobs()
    
    def _get_or_create_test_customer(self):
        """Get existing customer or create one for testing"""
        customers_response = self.session.get(f"{BASE_URL}/api/customers")
        if customers_response.status_code == 200:
            customers = customers_response.json()
            if customers:
                return customers[0]["id"]
        
        # Create a test customer
        customer_data = {
            "name": f"{TEST_PREFIX}Customer_{uuid.uuid4().hex[:6]}",
            "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "555-0100"
        }
        create_response = self.session.post(f"{BASE_URL}/api/customers", json=customer_data)
        assert create_response.status_code == 200 or create_response.status_code == 201
        return create_response.json()["id"]
    
    def _cleanup_test_jobs(self):
        """Cleanup test jobs created during testing"""
        try:
            jobs_response = self.session.get(f"{BASE_URL}/api/jobs?filter_type=all")
            if jobs_response.status_code == 200:
                jobs = jobs_response.json()
                for job in jobs:
                    if job.get("name", "").startswith(TEST_PREFIX):
                        self.session.delete(f"{BASE_URL}/api/jobs/{job['id']}")
        except:
            pass
    
    # ============== TEST: Create Job with status='quote' ==============
    def test_create_job_as_quote(self):
        """Test creating a job with status='quote' (New Quote flow)"""
        job_data = {
            "customer_id": self.customer_id,
            "name": f"{TEST_PREFIX}Quote_{uuid.uuid4().hex[:6]}",
            "description": "Test quote job",
            "status": "quote",
            "line_items": [
                {"description": "Banner 4x8", "quantity": 2, "unit_price": 150.00},
                {"description": "Installation", "quantity": 1, "unit_price": 75.00}
            ]
        }
        
        response = self.session.post(f"{BASE_URL}/api/jobs", json=job_data)
        print(f"Create quote response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200 or response.status_code == 201
        
        created_job = response.json()
        assert created_job["status"] == "quote", "Job should have status='quote'"
        assert created_job["name"] == job_data["name"]
        assert created_job["customer_id"] == self.customer_id
        assert len(created_job.get("line_items", [])) == 2
        
        # Verify total calculation
        expected_total = (2 * 150.00) + (1 * 75.00)  # 375.00
        assert created_job.get("total", 0) == expected_total, f"Expected total {expected_total}, got {created_job.get('total')}"
        
        return created_job["id"]
    
    # ============== TEST: Create Job with status='approved' ==============
    def test_create_job_as_approved(self):
        """Test creating a job with status='approved' (New Job flow - ready for production)"""
        job_data = {
            "customer_id": self.customer_id,
            "name": f"{TEST_PREFIX}Job_{uuid.uuid4().hex[:6]}",
            "description": "Test approved job",
            "status": "approved",
            "line_items": [
                {"description": "Vinyl Decal", "quantity": 5, "unit_price": 25.00}
            ]
        }
        
        response = self.session.post(f"{BASE_URL}/api/jobs", json=job_data)
        print(f"Create approved job response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200 or response.status_code == 201
        
        created_job = response.json()
        assert created_job["status"] == "approved", "Job should have status='approved'"
        assert created_job["name"] == job_data["name"]
        
        return created_job["id"]
    
    # ============== TEST: Job Status Filters ==============
    def test_filter_quotes_only(self):
        """Test filtering jobs to show only quotes (status=quote)"""
        # First create a quote job
        quote_job_id = self.test_create_job_as_quote()
        
        # Now filter for quotes only
        response = self.session.get(f"{BASE_URL}/api/jobs", params={"filter_type": "quotes"})
        print(f"Filter quotes response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200
        
        jobs = response.json()
        # All returned jobs should have status='quote'
        for job in jobs:
            assert job["status"] == "quote", f"Job {job['id']} has status '{job['status']}' but filter was 'quotes'"
        
        # Our test job should be in the list
        job_ids = [j["id"] for j in jobs]
        assert quote_job_id in job_ids, "Created quote job should appear in quotes filter"
    
    def test_filter_active_only(self):
        """Test filtering jobs to show only active (approved/in_progress)"""
        # First create an approved job
        approved_job_id = self.test_create_job_as_approved()
        
        # Now filter for active only
        response = self.session.get(f"{BASE_URL}/api/jobs", params={"filter_type": "active"})
        print(f"Filter active response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200
        
        jobs = response.json()
        # All returned jobs should have status='approved' or 'in_progress'
        for job in jobs:
            assert job["status"] in ["approved", "in_progress"], f"Job {job['id']} has status '{job['status']}' but filter was 'active'"
        
        # Our test job should be in the list
        job_ids = [j["id"] for j in jobs]
        assert approved_job_id in job_ids, "Created approved job should appear in active filter"
    
    def test_filter_all_jobs(self):
        """Test filtering all jobs (excludes archived)"""
        response = self.session.get(f"{BASE_URL}/api/jobs", params={"filter_type": "all"})
        print(f"Filter all response: {response.status_code} - {response.text[:500]}")
        
        assert response.status_code == 200
        
        jobs = response.json()
        # Should not include archived jobs
        for job in jobs:
            assert job["status"] != "archived", f"Job {job['id']} is archived but filter was 'all'"
            assert not job.get("is_archived", False), f"Job {job['id']} is archived but filter was 'all'"
    
    # ============== TEST: Approve Job (Quote -> Approved) ==============
    def test_approve_job_endpoint(self):
        """Test POST /api/jobs/{id}/approve - changes status from 'quote' to 'approved'"""
        # Create a quote first
        quote_job_id = self.test_create_job_as_quote()
        
        # Get the job to verify it's a quote
        get_response = self.session.get(f"{BASE_URL}/api/jobs/{quote_job_id}")
        assert get_response.status_code == 200
        job_before = get_response.json()
        assert job_before["status"] == "quote", "Job should start as 'quote'"
        
        # Approve the job
        approve_response = self.session.post(f"{BASE_URL}/api/jobs/{quote_job_id}/approve")
        print(f"Approve job response: {approve_response.status_code} - {approve_response.text[:500]}")
        
        assert approve_response.status_code == 200, f"Approve failed: {approve_response.text}"
        
        # Verify the job is now approved
        get_response = self.session.get(f"{BASE_URL}/api/jobs/{quote_job_id}")
        assert get_response.status_code == 200
        job_after = get_response.json()
        
        assert job_after["status"] == "approved", f"Job status should be 'approved' after approval, got '{job_after['status']}'"
        assert job_after.get("approved_at") is not None, "approved_at should be set after approval"
        
        # CRITICAL: Verify the same ID - no record duplication
        assert job_after["id"] == quote_job_id, "Job ID should remain the same after approval (no duplication)"
        
        print(f"✅ Job approved successfully: status changed from 'quote' to 'approved'")
        print(f"✅ Same job ID: {quote_job_id} - No record duplication")
    
    def test_approve_already_approved_fails(self):
        """Test that approving an already approved job fails"""
        # Create an approved job
        approved_job_id = self.test_create_job_as_approved()
        
        # Try to approve it again
        approve_response = self.session.post(f"{BASE_URL}/api/jobs/{approved_job_id}/approve")
        print(f"Approve already approved response: {approve_response.status_code} - {approve_response.text[:500]}")
        
        # Should fail with 400
        assert approve_response.status_code == 400, "Should not be able to approve an already approved job"
    
    # ============== TEST: Dashboard Stats ==============
    def test_dashboard_active_jobs_excludes_quotes(self):
        """Test that dashboard 'active_jobs' count does NOT include quotes"""
        # Create a quote and an approved job
        quote_id = self.test_create_job_as_quote()
        approved_id = self.test_create_job_as_approved()
        
        # Get dashboard stats
        stats_response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        print(f"Dashboard stats response: {stats_response.status_code} - {stats_response.text[:500]}")
        
        assert stats_response.status_code == 200
        
        stats = stats_response.json()
        active_jobs_count = stats.get("active_jobs", 0)
        
        # Get actual active jobs (approved + in_progress)
        active_response = self.session.get(f"{BASE_URL}/api/jobs", params={"filter_type": "active"})
        actual_active = len(active_response.json())
        
        # Get quotes count
        quotes_response = self.session.get(f"{BASE_URL}/api/jobs", params={"filter_type": "quotes"})
        quotes_count = len(quotes_response.json())
        
        print(f"Dashboard active_jobs: {active_jobs_count}")
        print(f"Actual active jobs (approved/in_progress): {actual_active}")
        print(f"Quotes count: {quotes_count}")
        
        # The dashboard active_jobs should NOT include quotes
        assert active_jobs_count <= actual_active, "Dashboard active_jobs should only count approved/in_progress jobs"
        
        # Verify our approved job is counted
        assert active_jobs_count >= 1, "At least our test approved job should be counted"
    
    # ============== TEST: Send Quote ==============
    def test_send_quote(self):
        """Test POST /api/jobs/{id}/send - marks quote as sent"""
        # Create a quote
        quote_id = self.test_create_job_as_quote()
        
        # Send the quote
        send_response = self.session.post(f"{BASE_URL}/api/jobs/{quote_id}/send")
        print(f"Send quote response: {send_response.status_code} - {send_response.text[:500]}")
        
        assert send_response.status_code == 200
        
        # Verify sent_at is set
        get_response = self.session.get(f"{BASE_URL}/api/jobs/{quote_id}")
        job = get_response.json()
        assert job.get("sent_at") is not None, "sent_at should be set after sending quote"
    
    # ============== TEST: Update Job Line Items ==============
    def test_update_job_line_items(self):
        """Test updating job line items and total recalculation"""
        # Create a quote
        quote_id = self.test_create_job_as_quote()
        
        # Update with new line items
        update_data = {
            "line_items": [
                {"description": "Large Banner 8x10", "quantity": 1, "unit_price": 500.00},
                {"description": "Stand", "quantity": 2, "unit_price": 50.00}
            ]
        }
        
        update_response = self.session.put(f"{BASE_URL}/api/jobs/{quote_id}", json=update_data)
        print(f"Update line items response: {update_response.status_code} - {update_response.text[:500]}")
        
        assert update_response.status_code == 200
        
        updated_job = update_response.json()
        expected_total = (1 * 500.00) + (2 * 50.00)  # 600.00
        assert updated_job.get("total") == expected_total, f"Expected total {expected_total}, got {updated_job.get('total')}"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
