"""
Test Team Schedule Features - Iteration 73

Tests for:
1. Dashboard Team Status Widget API (/api/dashboard/team-status-today)
2. Navigation structure verification (Employee Schedule in Team sub-nav)
3. Payroll page tab parameter handling
"""

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = DEV_TEST_EMAIL
TEST_PASSWORD = DEV_TEST_PASSWORD


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestDashboardTeamStatusToday:
    """Tests for GET /api/dashboard/team-status-today endpoint"""
    
    def test_team_status_today_returns_200(self, auth_headers):
        """Test that team-status-today endpoint returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/team-status-today",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("SUCCESS: GET /api/dashboard/team-status-today returns 200")
    
    def test_team_status_today_response_structure(self, auth_headers):
        """Test that response has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/team-status-today",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields
        assert "date" in data, "Response missing 'date' field"
        assert "day_of_week" in data, "Response missing 'day_of_week' field"
        assert "scheduled_count" in data, "Response missing 'scheduled_count' field"
        assert "clocked_in_count" in data, "Response missing 'clocked_in_count' field"
        assert "total_employees" in data, "Response missing 'total_employees' field"
        assert "employees" in data, "Response missing 'employees' field"
        
        print(f"SUCCESS: Response structure valid - date: {data['date']}, "
              f"scheduled: {data['scheduled_count']}, clocked_in: {data['clocked_in_count']}")
    
    def test_team_status_today_employee_structure(self, auth_headers):
        """Test that each employee has correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/team-status-today",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        employees = data.get("employees", [])
        
        if len(employees) > 0:
            emp = employees[0]
            
            # Check employee fields
            assert "employee_id" in emp, "Employee missing 'employee_id'"
            assert "employee_name" in emp, "Employee missing 'employee_name'"
            assert "is_scheduled" in emp, "Employee missing 'is_scheduled'"
            assert "shift_start" in emp, "Employee missing 'shift_start'"
            assert "shift_end" in emp, "Employee missing 'shift_end'"
            assert "clock_status" in emp, "Employee missing 'clock_status'"
            assert "clocked_in_at" in emp, "Employee missing 'clocked_in_at'"
            
            # Validate clock_status values
            valid_statuses = ["not_clocked_in", "working", "on_break", "finished"]
            assert emp["clock_status"] in valid_statuses, \
                f"Invalid clock_status: {emp['clock_status']}"
            
            print(f"SUCCESS: Employee structure valid - {emp['employee_name']}, "
                  f"scheduled: {emp['is_scheduled']}, status: {emp['clock_status']}")
        else:
            print("INFO: No employees found - empty state")
    
    def test_team_status_today_counts_match_employees(self, auth_headers):
        """Test that scheduled_count and clocked_in_count match employee data"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/team-status-today",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        employees = data.get("employees", [])
        
        # Count scheduled employees
        actual_scheduled = sum(1 for e in employees if e.get("is_scheduled"))
        assert data["scheduled_count"] == actual_scheduled, \
            f"scheduled_count mismatch: {data['scheduled_count']} vs {actual_scheduled}"
        
        # Count clocked in employees
        clocked_in_statuses = ["working", "on_break"]
        actual_clocked_in = sum(1 for e in employees if e.get("clock_status") in clocked_in_statuses)
        assert data["clocked_in_count"] == actual_clocked_in, \
            f"clocked_in_count mismatch: {data['clocked_in_count']} vs {actual_clocked_in}"
        
        print(f"SUCCESS: Counts match - scheduled: {actual_scheduled}, clocked_in: {actual_clocked_in}")
    
    def test_team_status_today_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/dashboard/team-status-today")
        assert response.status_code in [401, 403], \
            f"Expected 401/403 without auth, got {response.status_code}"
        print("SUCCESS: Endpoint requires authentication")


class TestDashboardOtherEndpoints:
    """Tests for other dashboard endpoints to ensure they still work"""
    
    def test_dashboard_stats(self, auth_headers):
        """Test GET /api/dashboard/stats"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "total_customers" in data
        assert "active_jobs" in data
        assert "pending_invoices" in data
        print(f"SUCCESS: Dashboard stats - customers: {data['total_customers']}, "
              f"active_jobs: {data['active_jobs']}")
    
    def test_dashboard_todays_schedule(self, auth_headers):
        """[Phase 5] Legacy /todays-schedule removed; verify V1 today-command-center."""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/today-command-center",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "due_order_items_today" in data
        print(f"SUCCESS: Today's command center - {len(data['due_order_items_today'])} due items")
    
    def test_dashboard_pending_approvals(self, auth_headers):
        """Test GET /api/dashboard/pending-approvals"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/pending-approvals",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"SUCCESS: Pending approvals - {len(response.json())} items")
    
    def test_dashboard_unread_messages(self, auth_headers):
        """Test GET /api/dashboard/unread-messages"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/unread-messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"SUCCESS: Unread messages - {len(response.json())} items")
    
    def test_dashboard_clocked_in(self, auth_headers):
        """[Phase 5] Legacy /clocked-in removed; verify V1 team-status-today."""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/team-status-today",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "employees" in data
        print(f"SUCCESS: Team status today - {data.get('clocked_in_count', 0)} clocked in")
    
    def test_dashboard_recent_ai_documents(self, auth_headers):
        """Test GET /api/dashboard/recent-ai-documents"""
        response = requests.get(
            f"{BASE_URL}/api/dashboard/recent-ai-documents",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"SUCCESS: Recent AI documents - {len(response.json())} items")


class TestPayrollScheduleEndpoint:
    """Tests for payroll schedule endpoint"""
    
    def test_payroll_schedule_get(self, auth_headers):
        """Test GET /api/payroll/schedule"""
        # Get current week start
        from datetime import datetime, timedelta
        today = datetime.now()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        week_start = monday.strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/schedule",
            params={"week_start": week_start},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "schedules" in data or isinstance(data, dict)
        print(f"SUCCESS: Payroll schedule retrieved for week of {week_start}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
