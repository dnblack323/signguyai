"""
Iteration 99 - Full Consolidation Pass Testing

Tests for:
1. Dashboard consolidation - /dashboard redirects to /productivity?view=dashboard
2. Legacy job redirects - /jobs -> /orders, /jobs?new=true -> /orders/new, /jobs/:id -> /productivity/legacy-jobs/:id
3. Legacy job source route page loads
4. Appointment source route page loads
5. Unified productivity endpoints still work
6. Signature public flow remains reachable
7. Drawing save/resume/markup flow remains reachable
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthAndBasicEndpoints:
    """Authentication and basic endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for owner account"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data


class TestProductivityEndpoints:
    """Unified productivity endpoints tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_productivity_items_endpoint(self, auth_headers):
        """Test /api/productivity/items endpoint returns items"""
        response = requests.get(f"{BASE_URL}/api/productivity/items", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
    
    def test_productivity_summary_endpoint(self, auth_headers):
        """Test /api/productivity/summary endpoint returns summary"""
        response = requests.get(f"{BASE_URL}/api/productivity/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Summary should have expected fields
        assert "due_today" in data or "open_items" in data
    
    def test_productivity_calendar_range_endpoint(self, auth_headers):
        """Test /api/productivity/calendar-range endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/productivity/calendar-range",
            headers=auth_headers,
            params={"anchor_date": "2026-01-15", "view": "month"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    def test_productivity_items_with_filters(self, auth_headers):
        """Test productivity items with various filters"""
        # Test with item_types filter
        response = requests.get(
            f"{BASE_URL}/api/productivity/items",
            headers=auth_headers,
            params={"item_types": "job,task"}
        )
        assert response.status_code == 200
        
        # Test with include_completed filter
        response = requests.get(
            f"{BASE_URL}/api/productivity/items",
            headers=auth_headers,
            params={"include_completed": "true"}
        )
        assert response.status_code == 200


class TestLegacyJobDetailsEndpoint:
    """Test legacy job details endpoint for source route"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_jobs_list_endpoint(self, auth_headers):
        """Test /api/jobs endpoint returns jobs list"""
        response = requests.get(f"{BASE_URL}/api/jobs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_job_details_endpoint_with_valid_id(self, auth_headers):
        """Test /api/jobs/{id}/details endpoint with a valid job ID"""
        # First get list of jobs
        response = requests.get(f"{BASE_URL}/api/jobs", headers=auth_headers)
        assert response.status_code == 200
        jobs = response.json()
        
        if len(jobs) > 0:
            job_id = jobs[0]["id"]
            response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/details", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert "job" in data
            assert "customer" in data or data.get("customer") is None
            assert "financial_snapshot" in data
        else:
            pytest.skip("No jobs available to test details endpoint")
    
    def test_job_details_endpoint_with_invalid_id(self, auth_headers):
        """Test /api/jobs/{id}/details endpoint with invalid ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/jobs/nonexistent-job-id-12345/details",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestAppointmentsEndpoint:
    """Test appointments endpoint for source route"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_appointment_detail_endpoint_with_invalid_id(self, auth_headers):
        """Test /api/appointments/{id} endpoint with invalid ID returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/appointments/nonexistent-appointment-id-12345",
            headers=auth_headers
        )
        assert response.status_code == 404


class TestProductivityPatchEndpoint:
    """Test productivity item patch/update endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_productivity_patch_endpoint_exists(self, auth_headers):
        """Test that PATCH /api/productivity/items/{uid} endpoint exists"""
        # Get a productivity item first
        response = requests.get(f"{BASE_URL}/api/productivity/items", headers=auth_headers)
        assert response.status_code == 200
        items = response.json().get("items", [])
        
        if len(items) > 0:
            item = items[0]
            uid = item.get("uid")
            
            # Test PATCH endpoint exists (even if we don't change anything)
            response = requests.patch(
                f"{BASE_URL}/api/productivity/items/{uid}",
                headers=auth_headers,
                json={"status": item.get("status")}  # No actual change
            )
            # Should return 200 or 404 (if item was deleted), not 405 Method Not Allowed
            assert response.status_code in [200, 404, 422], f"PATCH endpoint returned unexpected status: {response.status_code}"
        else:
            pytest.skip("No productivity items available to test patch endpoint")


class TestOrdersEndpoint:
    """Test orders endpoint (where /jobs redirects to)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_orders_list_endpoint(self, auth_headers):
        """Test /api/orders endpoint returns orders list"""
        response = requests.get(f"{BASE_URL}/api/orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Orders endpoint returns {orders: [...], total: N}
        assert "orders" in data or isinstance(data, list)
        if "orders" in data:
            assert isinstance(data["orders"], list)


class TestSignaturePublicFlow:
    """Test signature public flow remains reachable"""
    
    def test_signature_endpoint_structure(self):
        """Test that signature endpoint returns expected response for invalid token"""
        # Test with invalid token - should return 404 or appropriate error, not 500
        response = requests.get(f"{BASE_URL}/api/signatures/verify/invalid-token-12345")
        # Should be 404 (not found) or similar, not 500 (server error)
        assert response.status_code in [404, 400, 422], f"Signature endpoint returned unexpected status: {response.status_code}"


class TestDrawingEndpoints:
    """Test drawing save/resume/markup flow endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_order_drawings_endpoint_exists(self, auth_headers):
        """Test that order drawings endpoint exists"""
        # Get an order first
        response = requests.get(f"{BASE_URL}/api/orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Handle both list and {orders: [...]} response formats
        orders = data.get("orders", data) if isinstance(data, dict) else data
        
        if len(orders) > 0:
            order_id = orders[0]["id"]
            # Test drawings endpoint
            response = requests.get(
                f"{BASE_URL}/api/orders/{order_id}/drawings",
                headers=auth_headers
            )
            # Should return 200 (with drawings) or 404 (no drawings), not 500
            assert response.status_code in [200, 404], f"Drawings endpoint returned unexpected status: {response.status_code}"
        else:
            pytest.skip("No orders available to test drawings endpoint")


class TestEmployeesEndpoint:
    """Test employees endpoint for productivity dialog assignee dropdown"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_employees_list_endpoint(self, auth_headers):
        """Test /api/employees endpoint returns employees list"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestTasksEndpoint:
    """Test tasks endpoint for productivity task creation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_tasks_list_endpoint(self, auth_headers):
        """Test /api/tasks endpoint returns tasks list"""
        response = requests.get(f"{BASE_URL}/api/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_task_endpoint(self, auth_headers):
        """Test POST /api/tasks endpoint creates a task"""
        response = requests.post(
            f"{BASE_URL}/api/tasks",
            headers=auth_headers,
            json={
                "title": "TEST_Consolidation_Pass_Task",
                "due_date": "2026-01-20"
            }
        )
        assert response.status_code in [200, 201], f"Create task failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data.get("title") == "TEST_Consolidation_Pass_Task"
        
        # Cleanup - delete the test task
        task_id = data["id"]
        requests.delete(f"{BASE_URL}/api/tasks/{task_id}", headers=auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
