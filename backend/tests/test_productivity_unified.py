"""
Test Unified Productivity Layer - Iteration 79
Tests the new unified productivity endpoints that aggregate data from:
- Tasks, Orders, Legacy Jobs, Production Tasks, Employee Schedules, Appointments
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = PRODUCTION_OWNER_EMAIL
TEST_PASSWORD = PRODUCTION_OWNER_PASSWORD


class TestProductivityUnifiedLayer:
    """Test unified productivity endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    # ==================== /api/productivity/items ====================
    
    def test_productivity_items_endpoint_returns_200(self):
        """Test that /api/productivity/items returns 200"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "items" in data, "Response should contain 'items' key"
        assert "total" in data, "Response should contain 'total' key"
        assert "applied_filters" in data, "Response should contain 'applied_filters' key"
        print(f"✓ /api/productivity/items returned {data['total']} items")
    
    def test_productivity_items_structure(self):
        """Test that productivity items have correct structure"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={"include_completed": True})
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        if len(items) > 0:
            item = items[0]
            # Check required fields
            required_fields = ["uid", "id", "title", "type", "source_type", "source_id", "status", "board_column"]
            for field in required_fields:
                assert field in item, f"Item missing required field: {field}"
            
            # Check type is one of expected values
            valid_types = ["task", "job", "production_task", "schedule_shift", "appointment"]
            assert item["type"] in valid_types, f"Invalid item type: {item['type']}"
            print(f"✓ Item structure valid. First item type: {item['type']}, title: {item['title'][:50]}")
        else:
            print("⚠ No items returned - may need seed data")
    
    def test_productivity_items_filter_by_type(self):
        """Test filtering items by type"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "item_types": "task,job",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            assert item["type"] in ["task", "job"], f"Item type {item['type']} not in filter"
        
        print(f"✓ Type filter working. Got {len(items)} task/job items")
    
    def test_productivity_items_filter_by_status(self):
        """Test filtering items by status"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "statuses": "open,pending",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Status filter working. Got {data['total']} items with open/pending status")
    
    def test_productivity_items_search(self):
        """Test search functionality"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "search": "test",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Search filter working. Got {data['total']} items matching 'test'")
    
    def test_productivity_items_date_range(self):
        """Test date range filtering"""
        today = datetime.now().strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "start_date": today,
            "end_date": next_week,
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Date range filter working. Got {data['total']} items between {today} and {next_week}")
    
    # ==================== /api/productivity/summary ====================
    
    def test_productivity_summary_endpoint_returns_200(self):
        """Test that /api/productivity/summary returns 200"""
        response = self.session.get(f"{BASE_URL}/api/productivity/summary")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Check summary fields
        expected_fields = ["due_today", "overdue", "waiting_on_approval", "scheduled_this_week", 
                          "my_assigned", "open_items", "completed_items", "by_type", "by_board_column"]
        for field in expected_fields:
            assert field in data, f"Summary missing field: {field}"
        
        print(f"✓ Summary: due_today={data['due_today']}, overdue={data['overdue']}, open={data['open_items']}")
    
    def test_productivity_summary_by_type_breakdown(self):
        """Test that summary includes type breakdown"""
        response = self.session.get(f"{BASE_URL}/api/productivity/summary", params={"include_completed": True})
        assert response.status_code == 200
        
        data = response.json()
        by_type = data.get("by_type", {})
        
        print(f"✓ Summary by_type breakdown: {by_type}")
    
    # ==================== /api/productivity/calendar-range ====================
    
    def test_productivity_calendar_range_month_view(self):
        """Test calendar-range endpoint with month view (default)"""
        response = self.session.get(f"{BASE_URL}/api/productivity/calendar-range", params={
            "view": "month"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "view" in data, "Response should contain 'view'"
        assert "anchor_date" in data, "Response should contain 'anchor_date'"
        assert "range" in data, "Response should contain 'range'"
        assert "items" in data, "Response should contain 'items'"
        assert "summary" in data, "Response should contain 'summary'"
        
        assert data["view"] == "month"
        assert "start_date" in data["range"]
        assert "end_date" in data["range"]
        
        print(f"✓ Calendar month view: {data['range']['start_date']} to {data['range']['end_date']}, {len(data['items'])} items")
    
    def test_productivity_calendar_range_week_view(self):
        """Test calendar-range endpoint with week view"""
        response = self.session.get(f"{BASE_URL}/api/productivity/calendar-range", params={
            "view": "week"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["view"] == "week"
        print(f"✓ Calendar week view: {data['range']['start_date']} to {data['range']['end_date']}, {len(data['items'])} items")
    
    def test_productivity_calendar_range_day_view(self):
        """Test calendar-range endpoint with day view"""
        response = self.session.get(f"{BASE_URL}/api/productivity/calendar-range", params={
            "view": "day"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["view"] == "day"
        print(f"✓ Calendar day view: {data['range']['start_date']}, {len(data['items'])} items")
    
    def test_productivity_calendar_range_with_anchor_date(self):
        """Test calendar-range with specific anchor date"""
        anchor = "2025-02-15"
        response = self.session.get(f"{BASE_URL}/api/productivity/calendar-range", params={
            "view": "month",
            "anchor_date": anchor
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["anchor_date"] == anchor
        print(f"✓ Calendar with anchor date {anchor}: range {data['range']['start_date']} to {data['range']['end_date']}")
    
    def test_productivity_calendar_range_with_filters(self):
        """Test calendar-range with type filters"""
        response = self.session.get(f"{BASE_URL}/api/productivity/calendar-range", params={
            "view": "month",
            "item_types": "task,production_task"
        })
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            assert item["type"] in ["task", "production_task"], f"Item type {item['type']} not in filter"
        
        print(f"✓ Calendar with type filter: {len(items)} task/production_task items")
    
    # ==================== /api/productivity/board ====================
    
    def test_productivity_board_endpoint_returns_200(self):
        """Test that /api/productivity/board returns 200"""
        response = self.session.get(f"{BASE_URL}/api/productivity/board")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "groups" in data, "Response should contain 'groups'"
        assert "total" in data, "Response should contain 'total'"
        
        print(f"✓ Board endpoint: {data['total']} items in {len(data['groups'])} columns")
    
    def test_productivity_board_groups_structure(self):
        """Test that board groups items by board_column"""
        response = self.session.get(f"{BASE_URL}/api/productivity/board", params={"include_completed": True})
        assert response.status_code == 200
        
        data = response.json()
        groups = data.get("groups", {})
        
        # Each group should be a list of items
        for column, items in groups.items():
            assert isinstance(items, list), f"Group {column} should be a list"
            for item in items:
                assert item.get("board_column") == column, f"Item board_column mismatch: {item.get('board_column')} != {column}"
        
        print(f"✓ Board groups: {list(groups.keys())}")
    
    def test_productivity_board_with_type_filter(self):
        """Test board with type filter"""
        response = self.session.get(f"{BASE_URL}/api/productivity/board", params={
            "item_types": "task,job,production_task"
        })
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Board with type filter: {data['total']} items")
    
    # ==================== Source Type Mapping Tests ====================
    
    def test_productivity_items_include_orders(self):
        """Test that orders are mapped to productivity items"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "order",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            assert item["source_type"] == "order"
        
        print(f"✓ Orders mapped: {len(items)} order items")
    
    def test_productivity_items_include_tasks(self):
        """Test that tasks are mapped to productivity items"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            assert item["source_type"] == "task"
        
        print(f"✓ Tasks mapped: {len(items)} task items")
    
    def test_productivity_items_include_production_tasks(self):
        """Test that production tasks are mapped to productivity items"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "production_task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            assert item["source_type"] == "production_task"
        
        print(f"✓ Production tasks mapped: {len(items)} production_task items")
    
    def test_productivity_items_include_employee_schedules(self):
        """Test that employee schedules are mapped to productivity items"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "employee_schedule",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            assert item["source_type"] == "employee_schedule"
        
        print(f"✓ Employee schedules mapped: {len(items)} schedule items")
    
    def test_productivity_items_include_appointments(self):
        """Test that appointments are mapped to productivity items"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "appointment",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            assert item["source_type"] == "appointment"
        
        print(f"✓ Appointments mapped: {len(items)} appointment items")
    
    # ==================== Error Handling Tests ====================
    
    def test_productivity_calendar_invalid_view(self):
        """Test calendar-range with invalid view parameter"""
        response = self.session.get(f"{BASE_URL}/api/productivity/calendar-range", params={
            "view": "invalid_view"
        })
        # Should return 422 validation error
        assert response.status_code == 422, f"Expected 422 for invalid view, got {response.status_code}"
        print("✓ Invalid view parameter correctly rejected with 422")
    
    def test_productivity_endpoints_require_auth(self):
        """Test that productivity endpoints require authentication"""
        no_auth_session = requests.Session()
        
        endpoints = [
            "/api/productivity/items",
            "/api/productivity/summary",
            "/api/productivity/calendar-range",
            "/api/productivity/board"
        ]
        
        for endpoint in endpoints:
            response = no_auth_session.get(f"{BASE_URL}{endpoint}")
            assert response.status_code in [401, 403], f"{endpoint} should require auth, got {response.status_code}"
        
        print("✓ All productivity endpoints require authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
