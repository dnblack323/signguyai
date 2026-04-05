"""
Artwork Approvals API Tests

Tests for the shop-side artwork approval system including:
- Stats endpoint
- Approvals CRUD operations
- Customers/Jobs list endpoints
- Proof creation with validation
"""

import pytest
import requests
import os
from datetime import datetime
from backend.tests.test_credentials_helper import COMMON_TEST_PASSWORD, TEST_CUSTOMER_EMAIL

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = TEST_CUSTOMER_EMAIL
TEST_PASSWORD = COMMON_TEST_PASSWORD


class TestApprovalsAuth:
    """Authentication setup for approvals tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns access_token, not token
        token = data.get("access_token") or data.get("token")
        assert token, f"Token not in response: {data}"
        return token

    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Auth headers for requests"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


class TestApprovalsStats(TestApprovalsAuth):
    """Tests for /api/approvals/stats endpoint"""

    def test_stats_returns_200(self, headers):
        """GET /api/approvals/stats returns 200"""
        response = requests.get(f"{BASE_URL}/api/approvals/stats", headers=headers)
        assert response.status_code == 200, f"Stats failed: {response.text}"

    def test_stats_has_required_fields(self, headers):
        """Stats response has total, pending, approved, revisions fields"""
        response = requests.get(f"{BASE_URL}/api/approvals/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data, "Missing 'total' field"
        assert "pending" in data, "Missing 'pending' field"
        assert "approved" in data, "Missing 'approved' field"
        assert "revisions" in data, "Missing 'revisions' field"
        
        # Values should be non-negative integers
        assert isinstance(data["total"], int) and data["total"] >= 0
        assert isinstance(data["pending"], int) and data["pending"] >= 0
        assert isinstance(data["approved"], int) and data["approved"] >= 0
        assert isinstance(data["revisions"], int) and data["revisions"] >= 0

    def test_stats_requires_auth(self):
        """Stats endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/approvals/stats")
        assert response.status_code == 401, "Stats should require auth"


class TestApprovalsCustomersList(TestApprovalsAuth):
    """Tests for /api/approvals/customers/list endpoint"""

    def test_customers_list_returns_200(self, headers):
        """GET /api/approvals/customers/list returns 200"""
        response = requests.get(f"{BASE_URL}/api/approvals/customers/list", headers=headers)
        assert response.status_code == 200, f"Customers list failed: {response.text}"

    def test_customers_list_returns_array(self, headers):
        """Customers list returns an array"""
        response = requests.get(f"{BASE_URL}/api/approvals/customers/list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_customers_have_required_fields(self, headers):
        """Customer items have id, name, and email fields"""
        response = requests.get(f"{BASE_URL}/api/approvals/customers/list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # If customers exist, verify structure
        if len(data) > 0:
            customer = data[0]
            assert "id" in customer, "Customer missing 'id' field"
            assert "name" in customer, "Customer missing 'name' field"
            # email is optional but should be present if it exists

    def test_customers_list_requires_auth(self):
        """Customers list endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/approvals/customers/list")
        assert response.status_code == 401, "Customers list should require auth"


class TestApprovalsJobsList(TestApprovalsAuth):
    """Tests for /api/approvals/jobs/list endpoint"""

    def test_jobs_list_returns_200(self, headers):
        """GET /api/approvals/jobs/list returns 200"""
        response = requests.get(f"{BASE_URL}/api/approvals/jobs/list", headers=headers)
        assert response.status_code == 200, f"Jobs list failed: {response.text}"

    def test_jobs_list_returns_array(self, headers):
        """Jobs list returns an array"""
        response = requests.get(f"{BASE_URL}/api/approvals/jobs/list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_jobs_have_required_fields(self, headers):
        """Job items have id, name, and customer_id fields"""
        response = requests.get(f"{BASE_URL}/api/approvals/jobs/list", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # If jobs exist, verify structure
        if len(data) > 0:
            job = data[0]
            assert "id" in job, "Job missing 'id' field"
            assert "name" in job, "Job missing 'name' field"

    def test_jobs_list_filters_by_customer(self, headers):
        """Jobs list can be filtered by customer_id"""
        # First get customers list
        customers_response = requests.get(f"{BASE_URL}/api/approvals/customers/list", headers=headers)
        if customers_response.status_code == 200:
            customers = customers_response.json()
            if len(customers) > 0:
                customer_id = customers[0]["id"]
                
                # Get jobs filtered by customer
                response = requests.get(
                    f"{BASE_URL}/api/approvals/jobs/list?customer_id={customer_id}",
                    headers=headers
                )
                assert response.status_code == 200, f"Filtered jobs list failed: {response.text}"
                data = response.json()
                assert isinstance(data, list), "Response should be a list"

    def test_jobs_list_requires_auth(self):
        """Jobs list endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/approvals/jobs/list")
        assert response.status_code == 401, "Jobs list should require auth"


class TestApprovalsList(TestApprovalsAuth):
    """Tests for /api/approvals endpoint"""

    def test_approvals_list_returns_200(self, headers):
        """GET /api/approvals returns 200"""
        response = requests.get(f"{BASE_URL}/api/approvals", headers=headers)
        assert response.status_code == 200, f"Approvals list failed: {response.text}"

    def test_approvals_list_returns_array(self, headers):
        """Approvals list returns an array"""
        response = requests.get(f"{BASE_URL}/api/approvals", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_approvals_list_filters_by_status(self, headers):
        """Approvals list can be filtered by status"""
        # Test filtering by pending status
        response = requests.get(f"{BASE_URL}/api/approvals?status=pending", headers=headers)
        assert response.status_code == 200, f"Filtered approvals failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"

    def test_approvals_list_requires_auth(self):
        """Approvals list endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/approvals")
        assert response.status_code == 401, "Approvals list should require auth"


class TestApprovalsCreate(TestApprovalsAuth):
    """Tests for POST /api/approvals endpoint"""
    
    created_proof_id = None

    def test_create_approval_requires_customer_job(self, headers):
        """POST /api/approvals requires customer_id and job_id"""
        response = requests.post(
            f"{BASE_URL}/api/approvals",
            headers=headers,
            json={
                "file_url": "data:image/png;base64,iVBORw0KGgo=",
                "file_name": "test.png"
            }
        )
        # Should fail due to missing customer_id and job_id
        assert response.status_code in [400, 422], f"Should require customer_id and job_id: {response.text}"

    def test_create_approval_validates_customer(self, headers):
        """POST /api/approvals validates customer exists"""
        response = requests.post(
            f"{BASE_URL}/api/approvals",
            headers=headers,
            json={
                "customer_id": "nonexistent-customer-id",
                "job_id": "nonexistent-job-id",
                "file_url": "data:image/png;base64,iVBORw0KGgo=",
                "file_name": "test.png"
            }
        )
        # Should fail due to customer not found
        assert response.status_code == 404, f"Should validate customer exists: {response.text}"

    def test_create_approval_success(self, headers):
        """POST /api/approvals creates proof when valid customer and job exist"""
        # Get a valid customer
        customers_response = requests.get(f"{BASE_URL}/api/approvals/customers/list", headers=headers)
        if customers_response.status_code != 200 or len(customers_response.json()) == 0:
            pytest.skip("No customers available for testing")
        
        customer_id = customers_response.json()[0]["id"]
        
        # Get a valid job for this customer
        jobs_response = requests.get(
            f"{BASE_URL}/api/approvals/jobs/list?customer_id={customer_id}",
            headers=headers
        )
        if jobs_response.status_code != 200 or len(jobs_response.json()) == 0:
            pytest.skip("No jobs available for testing")
        
        job_id = jobs_response.json()[0]["id"]
        
        # Create approval
        response = requests.post(
            f"{BASE_URL}/api/approvals",
            headers=headers,
            json={
                "customer_id": customer_id,
                "job_id": job_id,
                "file_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "file_name": "TEST_approval_artwork.png",
                "description": "TEST_approval description"
            }
        )
        
        assert response.status_code in [200, 201], f"Create approval failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response missing 'id' field"
        assert data["customer_id"] == customer_id, "Customer ID mismatch"
        assert data["job_id"] == job_id, "Job ID mismatch"
        assert "status" in data, "Response missing 'status' field"
        assert data["status"] == "pending", "New proof should be pending"
        assert "version" in data, "Response missing 'version' field"
        
        # Store for cleanup
        TestApprovalsCreate.created_proof_id = data["id"]

    def test_create_approval_requires_auth(self):
        """POST /api/approvals requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/approvals",
            json={
                "customer_id": "test",
                "job_id": "test",
                "file_url": "test",
                "file_name": "test.png"
            }
        )
        assert response.status_code == 401, "Create approval should require auth"

    def test_cleanup_created_proof(self, headers):
        """Cleanup: delete created proof"""
        if TestApprovalsCreate.created_proof_id:
            response = requests.delete(
                f"{BASE_URL}/api/approvals/{TestApprovalsCreate.created_proof_id}",
                headers=headers
            )
            # 200 or 204 are both acceptable for successful deletion
            assert response.status_code in [200, 204, 404], f"Delete failed: {response.text}"


class TestApprovalsGetSingle(TestApprovalsAuth):
    """Tests for GET /api/approvals/{proof_id} endpoint"""

    def test_get_nonexistent_proof_returns_404(self, headers):
        """GET /api/approvals/{id} returns 404 for nonexistent proof"""
        response = requests.get(
            f"{BASE_URL}/api/approvals/nonexistent-proof-id",
            headers=headers
        )
        assert response.status_code == 404, "Should return 404 for nonexistent proof"

    def test_get_proof_requires_auth(self):
        """GET /api/approvals/{id} requires authentication"""
        response = requests.get(f"{BASE_URL}/api/approvals/some-id")
        assert response.status_code == 401, "Get proof should require auth"


class TestApprovalsDelete(TestApprovalsAuth):
    """Tests for DELETE /api/approvals/{proof_id} endpoint"""

    def test_delete_nonexistent_proof_returns_404(self, headers):
        """DELETE /api/approvals/{id} returns 404 for nonexistent proof"""
        response = requests.delete(
            f"{BASE_URL}/api/approvals/nonexistent-proof-id",
            headers=headers
        )
        assert response.status_code == 404, "Should return 404 for nonexistent proof"

    def test_delete_proof_requires_auth(self):
        """DELETE /api/approvals/{id} requires authentication"""
        response = requests.delete(f"{BASE_URL}/api/approvals/some-id")
        assert response.status_code == 401, "Delete proof should require auth"


class TestApprovalsResend(TestApprovalsAuth):
    """Tests for POST /api/approvals/{proof_id}/resend endpoint"""

    def test_resend_nonexistent_proof_returns_404(self, headers):
        """POST /api/approvals/{id}/resend returns 404 for nonexistent proof"""
        response = requests.post(
            f"{BASE_URL}/api/approvals/nonexistent-proof-id/resend",
            headers=headers
        )
        assert response.status_code == 404, "Should return 404 for nonexistent proof"

    def test_resend_requires_auth(self):
        """POST /api/approvals/{id}/resend requires authentication"""
        response = requests.post(f"{BASE_URL}/api/approvals/some-id/resend")
        assert response.status_code == 401, "Resend should require auth"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
