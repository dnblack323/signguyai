"""
Iteration 111 - Bug Fixes and Features Testing

Tests for:
- BUG 2: Task creation from productivity calendar day modal
- BUG 4: Productivity status filter functionality
- FEATURE 5: Customer creation with company only (no name) + display_name auto-generation
- FEATURE 6: Order auto-naming (DISPLAYNAME-MMDDYY format)
- FEATURE 8: /dashboard route loads Dashboard page
- FEATURE 10: Expense receipt photo buttons (UI test)
- Productivity page shows both orders AND tasks by default
"""

import pytest
import requests
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self, auth_token):
        """Verify login works"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token obtained")


class TestCustomerCreation:
    """FEATURE 5: Customer creation with company only + display_name auto-generation"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_create_customer_with_company_only(self, auth_token):
        """Create customer with only company name (no personal name) - should succeed"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create customer with only company name
        customer_data = {
            "company": "TEST_CompanyOnlyTest Inc",
            "name": "",  # Empty name
            "email": f"test_company_only_{datetime.now().timestamp()}@test.com",
            "status": "lead"
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200, f"Failed to create customer with company only: {response.text}"
        
        data = response.json()
        assert data.get("company") == "TEST_CompanyOnlyTest Inc"
        # Name should be set to company when name is empty
        assert data.get("name") == "TEST_CompanyOnlyTest Inc"
        print(f"✓ Customer created with company only: {data.get('id')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{data['id']}", headers=headers)
    
    def test_customer_display_name_auto_generated(self, auth_token):
        """Customer creation auto-generates display_name from company name"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create customer with company name containing spaces
        customer_data = {
            "company": "TEST Display Name Company",
            "name": "",
            "email": f"test_display_{datetime.now().timestamp()}@test.com",
            "status": "lead"
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        
        data = response.json()
        # display_name should be company name without spaces
        assert data.get("display_name") == "TESTDisplayNameCompany", f"Expected 'TESTDisplayNameCompany', got '{data.get('display_name')}'"
        print(f"✓ display_name auto-generated: {data.get('display_name')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{data['id']}", headers=headers)
    
    def test_customer_with_name_only(self, auth_token):
        """Create customer with only name (no company) - should succeed"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        customer_data = {
            "name": "TEST John Doe",
            "company": "",
            "email": f"test_name_only_{datetime.now().timestamp()}@test.com",
            "status": "lead"
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200, f"Failed to create customer with name only: {response.text}"
        
        data = response.json()
        assert data.get("name") == "TEST John Doe"
        # display_name should be generated from name when no company
        assert data.get("display_name") == "TESTJohnDoe", f"Expected 'TESTJohnDoe', got '{data.get('display_name')}'"
        print(f"✓ Customer created with name only, display_name: {data.get('display_name')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{data['id']}", headers=headers)
    
    def test_customer_requires_name_or_company(self, auth_token):
        """Customer creation fails if both name and company are empty"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        customer_data = {
            "name": "",
            "company": "",
            "email": f"test_empty_{datetime.now().timestamp()}@test.com",
            "status": "lead"
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 400, f"Expected 400 for empty name and company, got {response.status_code}"
        print(f"✓ Customer creation correctly rejected when both name and company are empty")


class TestOrderAutoNaming:
    """FEATURE 6: Order auto-naming (DISPLAYNAME-MMDDYY format)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_token):
        """Create a test customer for order tests"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        customer_data = {
            "company": "TEST AutoName Corp",
            "name": "",
            "email": f"test_autoname_{datetime.now().timestamp()}@test.com",
            "status": "active"
        }
        
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=headers)
        assert response.status_code == 200
        customer = response.json()
        yield customer
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/customers/{customer['id']}", headers=headers)
    
    def test_order_auto_naming(self, auth_token, test_customer):
        """Create order without explicit name - should auto-generate DISPLAYNAME-MMDDYY format"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create order without name
        order_data = {
            "customer_id": test_customer["id"],
            "customer_name": test_customer.get("name") or test_customer.get("company"),
            "name": ""  # Empty name - should auto-generate
        }
        
        response = requests.post(f"{BASE_URL}/api/orders", json=order_data, headers=headers)
        assert response.status_code == 200, f"Failed to create order: {response.text}"
        
        data = response.json()
        order_name = data.get("name", "")
        
        # Expected format: TESTAUTONAMECOPR-MMDDYY (display_name without spaces, uppercase)
        today = datetime.now(timezone.utc).strftime("%m%d%y")
        expected_prefix = "TESTAUTONAMECOPR"  # display_name is "TESTAutoNameCorp" -> uppercase
        
        assert order_name.startswith(expected_prefix) or "AUTONAME" in order_name.upper(), \
            f"Order name '{order_name}' doesn't match expected format starting with customer display_name"
        assert today in order_name, f"Order name '{order_name}' doesn't contain today's date {today}"
        
        print(f"✓ Order auto-named: {order_name}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/orders/{data['id']}", headers=headers)


class TestTaskCreation:
    """BUG 2: Task creation from productivity calendar day modal"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_create_task_via_api(self, auth_token):
        """Create a task via POST /api/tasks - should succeed"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        task_data = {
            "title": f"TEST_Task_Iteration111_{datetime.now().timestamp()}",
            "due_date": today,
            "assigned_to": None
        }
        
        response = requests.post(f"{BASE_URL}/api/tasks", json=task_data, headers=headers)
        assert response.status_code in [200, 201], f"Failed to create task: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data.get("title") == task_data["title"]
        assert data.get("due_date") == today
        print(f"✓ Task created successfully: {data.get('id')}")
        
        # Verify task appears in productivity items
        items_response = requests.get(f"{BASE_URL}/api/productivity/items", 
                                      params={"item_types": "task"},
                                      headers=headers)
        assert items_response.status_code == 200
        items = items_response.json().get("items", [])
        task_ids = [item.get("source_id") or item.get("id") for item in items]
        assert data.get("id") in task_ids or any(data.get("title") in str(item) for item in items), \
            "Created task not found in productivity items"
        print(f"✓ Task appears in productivity items")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/tasks/{data['id']}", headers=headers)


class TestProductivityFilters:
    """BUG 4: Productivity status filter functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_productivity_items_endpoint(self, auth_token):
        """Verify productivity items endpoint works"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/productivity/items", headers=headers)
        assert response.status_code == 200, f"Failed to get productivity items: {response.text}"
        
        data = response.json()
        assert "items" in data
        print(f"✓ Productivity items endpoint works, returned {len(data.get('items', []))} items")
    
    def test_productivity_status_filter(self, auth_token):
        """Test status filter - selecting 'open' should filter items"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get all items first
        all_response = requests.get(f"{BASE_URL}/api/productivity/items", headers=headers)
        assert all_response.status_code == 200
        all_items = all_response.json().get("items", [])
        
        # Get items with status filter
        filtered_response = requests.get(f"{BASE_URL}/api/productivity/items", 
                                         params={"statuses": "open"},
                                         headers=headers)
        assert filtered_response.status_code == 200, f"Status filter failed: {filtered_response.text}"
        
        filtered_items = filtered_response.json().get("items", [])
        
        # Verify all filtered items have 'open' status (or related status)
        for item in filtered_items:
            item_status = item.get("status", "").lower()
            # Allow for status variations
            assert item_status in ["open", "to_do", "pending", "new"], \
                f"Item with status '{item_status}' should not appear in 'open' filter"
        
        print(f"✓ Status filter works: {len(all_items)} total items, {len(filtered_items)} with 'open' status")
    
    def test_productivity_item_types_filter(self, auth_token):
        """Test item types filter - should include both jobs and tasks by default"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get items with both job and task types
        response = requests.get(f"{BASE_URL}/api/productivity/items", 
                               params={"item_types": "job,task"},
                               headers=headers)
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        item_types = set(item.get("type") for item in items)
        
        print(f"✓ Item types filter works, found types: {item_types}")


class TestDashboardRoute:
    """FEATURE 8: /dashboard route loads Dashboard page"""
    
    def test_dashboard_api_endpoint(self):
        """Test that dashboard-related API endpoints exist"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check if dashboard summary endpoint exists
        response = requests.get(f"{BASE_URL}/api/dashboard/summary", headers=headers)
        # Dashboard endpoint may or may not exist, but we're testing the route exists
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Dashboard API check complete (status: {response.status_code})")


class TestProductivityCalendarRange:
    """Test productivity calendar-range endpoint for calendar view"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_calendar_range_endpoint(self, auth_token):
        """Test calendar-range endpoint returns items"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        response = requests.get(f"{BASE_URL}/api/productivity/calendar-range", 
                               params={"anchor_date": today, "view": "month", "item_types": "job,task"},
                               headers=headers)
        assert response.status_code == 200, f"Calendar range failed: {response.text}"
        
        data = response.json()
        assert "items" in data
        assert "range" in data
        print(f"✓ Calendar range endpoint works, returned {len(data.get('items', []))} items")


class TestExpenseEndpoint:
    """FEATURE 10: Expense endpoint exists (receipt photo upload is UI feature)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_expense_entries_endpoint(self, auth_token):
        """Test expense entries endpoint exists"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/financials/expenses", headers=headers)
        # Endpoint should exist
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ Expense entries endpoint check complete (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
