"""
Employee Portal Backend Tests

Tests for:
- Employee authentication (email/PIN login)
- Time clock operations (clock in/out, break start/end)
- Profile endpoint
- Pay summary endpoint
- Tasks endpoint
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Test credentials
TEST_EMPLOYEE_EMAIL = "john@signshop.com"
TEST_EMPLOYEE_PIN = "5678"


class TestEmployeePortalAuth:
    """Employee Portal authentication tests"""
    
    def test_employee_login_success(self):
        """Test successful employee login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": TEST_EMPLOYEE_EMAIL, "pin": TEST_EMPLOYEE_PIN}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "employee_id" in data
        assert "employee_name" in data
        assert "tenant_id" in data
        
        # Verify data types
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["employee_name"] == "John Worker"
    
    def test_employee_login_invalid_email(self):
        """Test login failure with invalid email"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": "wrong@email.com", "pin": TEST_EMPLOYEE_PIN}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
    
    def test_employee_login_invalid_pin(self):
        """Test login failure with invalid PIN"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": TEST_EMPLOYEE_EMAIL, "pin": "9999"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


@pytest.fixture
def employee_token():
    """Get valid employee JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/employee-portal/auth/login",
        json={"email": TEST_EMPLOYEE_EMAIL, "pin": TEST_EMPLOYEE_PIN}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Employee authentication failed - skipping authenticated tests")


class TestEmployeeProfile:
    """Employee profile endpoint tests"""
    
    def test_get_profile_success(self, employee_token):
        """Test getting employee profile with valid token"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/profile",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify profile structure
        assert "id" in data
        assert "name" in data
        assert "email" in data
        assert "role" in data
        assert "hourly_rate" in data
        assert "tenant_id" in data
        
        # Verify profile data
        assert data["email"] == TEST_EMPLOYEE_EMAIL
        assert data["name"] == "John Worker"
        assert isinstance(data["hourly_rate"], (int, float))
    
    def test_get_profile_unauthorized(self):
        """Test profile access without token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/profile")
        
        assert response.status_code == 401
    
    def test_get_profile_invalid_token(self):
        """Test profile access with invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/profile",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401


class TestTimeClock:
    """Time clock operations tests"""
    
    def test_get_time_clock_status(self, employee_token):
        """Test getting current time clock status"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/time-clock/status",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify status structure
        assert "is_clocked_in" in data
        assert "current_status" in data
        assert "clocked_in_at" in data
        assert "total_hours_today" in data
        assert "break_time_today" in data
        
        # Verify data types
        assert isinstance(data["is_clocked_in"], bool)
        assert isinstance(data["total_hours_today"], (int, float))
        assert isinstance(data["break_time_today"], (int, float))
    
    def test_punch_clock_in(self, employee_token):
        """Test clocking in (start_work)"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/time-clock/punch?action=start_work",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "log" in data
        assert data["log"]["action"] == "start_work"
        assert "timestamp" in data["log"]
    
    def test_punch_break_start(self, employee_token):
        """Test starting break (break_start)"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/time-clock/punch?action=break_start",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["log"]["action"] == "break_start"
    
    def test_punch_break_end(self, employee_token):
        """Test ending break (break_end)"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/time-clock/punch?action=break_end",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["log"]["action"] == "break_end"
    
    def test_punch_clock_out(self, employee_token):
        """Test clocking out (end_work)"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/time-clock/punch?action=end_work",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["log"]["action"] == "end_work"
    
    def test_punch_invalid_action(self, employee_token):
        """Test punching with invalid action"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/time-clock/punch?action=invalid_action",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 400
    
    def test_get_time_clock_history(self, employee_token):
        """Test getting time clock history"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/time-clock/history?days=7",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If entries exist, verify structure
        if len(data) > 0:
            entry = data[0]
            assert "id" in entry
            assert "action" in entry
            assert "timestamp" in entry


class TestPaySummary:
    """Pay summary endpoint tests"""
    
    def test_get_pay_summary(self, employee_token):
        """Test getting pay summary"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/pay/summary",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify pay summary structure
        assert "current_period_earnings" in data
        assert "current_period_hours" in data
        assert "ytd_earnings" in data
        assert "ytd_hours" in data
        assert "balance_owed" in data
        
        # Verify data types
        assert isinstance(data["current_period_earnings"], (int, float))
        assert isinstance(data["ytd_earnings"], (int, float))
        assert isinstance(data["balance_owed"], (int, float))
    
    def test_get_pay_summary_unauthorized(self):
        """Test pay summary access without token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/pay/summary")
        
        assert response.status_code == 401


class TestTasks:
    """Employee tasks endpoint tests"""
    
    def test_get_tasks(self, employee_token):
        """Test getting employee tasks"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/tasks",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If tasks exist, verify structure
        if len(data) > 0:
            task = data[0]
            assert "id" in task
            assert "title" in task
            assert "is_complete" in task
    
    def test_get_tasks_include_completed(self, employee_token):
        """Test getting tasks including completed ones"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/tasks?include_completed=true",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
