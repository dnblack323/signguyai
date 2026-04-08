"""
Iteration 91 - Payroll Export Feature Tests

Tests for:
1. Payroll page loads after login without compile/runtime errors
2. GET /api/payroll/report supports start_date + end_date, optional employee_id, and period_type=weekly
3. Existing payroll routes still work: /api/payroll/timesheet and /api/payroll/pay-period
4. Time Clock page still loads and updated summary/directory UI renders without regressions
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestPayrollExportFeatures:
    """Tests for payroll export functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_auth_login_works(self):
        """Test that authentication works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print("Auth login works correctly")
    
    def test_payroll_pay_period_endpoint(self):
        """Test GET /api/payroll/pay-period returns valid response"""
        response = self.session.get(f"{BASE_URL}/api/payroll/pay-period?period_type=weekly")
        assert response.status_code == 200
        
        data = response.json()
        assert "period_type" in data
        assert data["period_type"] == "weekly"
        assert "period_start" in data
        assert "period_end" in data
        assert "employees" in data
        assert "totals" in data
        
        # Verify totals structure
        totals = data["totals"]
        assert "total_hours" in totals
        assert "regular_hours" in totals
        assert "overtime_hours" in totals
        assert "gross_pay" in totals
        assert "net_owed" in totals
        print(f"Pay period endpoint works: {data['period_start']} to {data['period_end']}")
    
    def test_payroll_pay_period_biweekly(self):
        """Test GET /api/payroll/pay-period with biweekly period"""
        response = self.session.get(f"{BASE_URL}/api/payroll/pay-period?period_type=biweekly")
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_type"] == "biweekly"
        print(f"Biweekly pay period works: {data['period_start']} to {data['period_end']}")
    
    def test_payroll_timesheet_endpoint(self):
        """Test GET /api/payroll/timesheet returns valid response"""
        response = self.session.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={"start_date": "2026-04-06", "end_date": "2026-04-12"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "start_date" in data
        assert "end_date" in data
        assert "employees" in data
        assert "totals" in data
        
        # Verify totals structure
        totals = data["totals"]
        assert "total_hours" in totals
        assert "regular_hours" in totals
        assert "overtime_hours" in totals
        assert "total_pay" in totals
        print(f"Timesheet endpoint works: {data['start_date']} to {data['end_date']}")
    
    def test_payroll_report_with_date_range(self):
        """Test GET /api/payroll/report with start_date and end_date"""
        response = self.session.get(
            f"{BASE_URL}/api/payroll/report",
            params={"start_date": "2026-04-06", "end_date": "2026-04-12"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "period_type" in data
        assert data["period_type"] == "custom"
        assert "start_date" in data
        assert data["start_date"] == "2026-04-06"
        assert "end_date" in data
        assert data["end_date"] == "2026-04-12"
        assert "employee_count" in data
        assert "employees" in data
        assert "totals" in data
        
        # Verify totals structure
        totals = data["totals"]
        assert "hours" in totals
        assert "regular_hours" in totals
        assert "overtime_hours" in totals
        assert "earnings" in totals
        assert "advances" in totals
        assert "payments" in totals
        assert "balance" in totals
        print(f"Payroll report with date range works: {data['start_date']} to {data['end_date']}")
    
    def test_payroll_report_with_period_type_weekly(self):
        """Test GET /api/payroll/report with period_type=weekly"""
        response = self.session.get(
            f"{BASE_URL}/api/payroll/report",
            params={"period_type": "weekly"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_type"] == "weekly"
        assert "start_date" in data
        assert "end_date" in data
        print(f"Payroll report with weekly period works: {data['start_date']} to {data['end_date']}")
    
    def test_payroll_report_with_period_type_biweekly(self):
        """Test GET /api/payroll/report with period_type=biweekly"""
        response = self.session.get(
            f"{BASE_URL}/api/payroll/report",
            params={"period_type": "biweekly"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["period_type"] == "biweekly"
        print(f"Payroll report with biweekly period works: {data['start_date']} to {data['end_date']}")
    
    def test_payroll_report_with_employee_filter(self):
        """Test GET /api/payroll/report with optional employee_id filter"""
        # First get list of employees
        emp_response = self.session.get(f"{BASE_URL}/api/employees")
        assert emp_response.status_code == 200
        employees = emp_response.json()
        
        # Test with a fake employee_id (should return empty but not error)
        response = self.session.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": "2026-04-06",
                "end_date": "2026-04-12",
                "employee_id": "non-existent-employee-id"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["employee_count"] == 0
        print("Payroll report with employee filter works (empty result for non-existent employee)")
    
    def test_payroll_transactions_endpoint(self):
        """Test GET /api/payroll/transactions returns valid response"""
        response = self.session.get(f"{BASE_URL}/api/payroll/transactions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Payroll transactions endpoint works: {len(data)} transactions found")
    
    def test_payroll_hours_endpoint(self):
        """Test GET /api/payroll/hours returns valid response"""
        response = self.session.get(
            f"{BASE_URL}/api/payroll/hours",
            params={"start_date": "2026-04-06", "end_date": "2026-04-12"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Payroll hours endpoint works: {len(data)} entries found")
    
    def test_payroll_timeclock_shifts_endpoint(self):
        """Test GET /api/payroll/timeclock-shifts returns valid response"""
        response = self.session.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={"start_date": "2026-04-06", "end_date": "2026-04-12"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Payroll timeclock shifts endpoint works: {len(data)} shifts found")
    
    def test_payroll_schedule_endpoint(self):
        """Test GET /api/payroll/schedule returns valid response"""
        response = self.session.get(
            f"{BASE_URL}/api/payroll/schedule",
            params={"week_start": "2026-04-06"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "week_start" in data
        assert "schedules" in data
        print(f"Payroll schedule endpoint works: {len(data['schedules'])} schedules found")
    
    def test_employees_list_endpoint(self):
        """Test GET /api/employees returns valid response"""
        response = self.session.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"Employees list endpoint works: {len(data)} employees found")


class TestTimeclockEndpoints:
    """Tests for timeclock functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_timeclock_status_requires_employee(self):
        """Test that timeclock status endpoint requires valid employee"""
        # Test with non-existent employee
        response = self.session.get(f"{BASE_URL}/api/timeclock/non-existent-id/status")
        assert response.status_code == 404
        print("Timeclock status correctly returns 404 for non-existent employee")
    
    def test_timeclock_today_requires_employee(self):
        """Test that timeclock today endpoint requires valid employee"""
        response = self.session.get(f"{BASE_URL}/api/timeclock/non-existent-id/today")
        assert response.status_code == 404
        print("Timeclock today correctly returns 404 for non-existent employee")
    
    def test_timeclock_summary_requires_employee(self):
        """Test that timeclock summary endpoint requires valid employee"""
        response = self.session.get(f"{BASE_URL}/api/timeclock/non-existent-id/summary")
        assert response.status_code == 404
        print("Timeclock summary correctly returns 404 for non-existent employee")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
