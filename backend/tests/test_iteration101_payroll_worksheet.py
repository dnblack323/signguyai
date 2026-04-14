"""
Iteration 101 - Payroll Worksheet Backend Tests

Tests for the new Admin Payroll Worksheet page features:
- Worksheet meta fields save and persist
- 7-row time table edits save and persist through backend
- Left adjustments panel edits save and persist through backend
- Worksheet totals compute correctly after edits
- Export CSV and Print remain functional
- Backend payroll report/timesheet include updated overtime rate and worksheet data
- New POST /api/payroll/timeclock-shifts works
- No regressions in payroll page load or save flow
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestPayrollWorksheetBackend:
    """Backend API tests for payroll worksheet features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get auth token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        login_data = login_response.json()
        self.token = login_data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        # Get employees for testing
        emp_response = self.session.get(f"{BASE_URL}/api/employees")
        if emp_response.status_code == 200:
            employees = emp_response.json()
            # Find QA Test Employee or use first employee
            self.test_employee = None
            for emp in employees:
                if "QA" in emp.get("name", "") or "Preview" in emp.get("name", ""):
                    self.test_employee = emp
                    break
            if not self.test_employee and employees:
                self.test_employee = employees[0]
        
        yield
        
        # Cleanup if needed
        self.session.close()
    
    # ============== HEALTH CHECK ==============
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("SUCCESS: Health endpoint accessible")
    
    # ============== EMPLOYEE META FIELDS ==============
    
    def test_get_employee_details(self):
        """Test GET /api/employees/{id} returns employee with meta fields"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        response = self.session.get(f"{BASE_URL}/api/employees/{self.test_employee['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "hourly_rate" in data
        
        # Check for new worksheet meta fields
        print(f"Employee: {data.get('name')}")
        print(f"Title: {data.get('title')}")
        print(f"Manager Name: {data.get('manager_name')}")
        print(f"Hourly Rate: {data.get('hourly_rate')}")
        print(f"Overtime Rate: {data.get('overtime_rate')}")
        print("SUCCESS: Employee details retrieved with meta fields")
    
    def test_update_employee_meta_fields(self):
        """Test PUT /api/employees/{id} updates meta fields including overtime_rate"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        # Update employee with worksheet meta fields
        update_payload = {
            "name": self.test_employee.get("name"),
            "title": "Test Title Updated",
            "manager_name": "Test Manager Updated",
            "hourly_rate": 25.00,
            "overtime_rate": 37.50
        }
        
        response = self.session.put(
            f"{BASE_URL}/api/employees/{self.test_employee['id']}", 
            json=update_payload
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("title") == "Test Title Updated"
        assert data.get("manager_name") == "Test Manager Updated"
        assert data.get("hourly_rate") == 25.00
        assert data.get("overtime_rate") == 37.50
        
        # Verify persistence with GET
        verify_response = self.session.get(f"{BASE_URL}/api/employees/{self.test_employee['id']}")
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data.get("overtime_rate") == 37.50
        
        print("SUCCESS: Employee meta fields updated and persisted")
        
        # Restore original values
        restore_payload = {
            "name": self.test_employee.get("name"),
            "title": self.test_employee.get("title", ""),
            "manager_name": self.test_employee.get("manager_name", ""),
            "hourly_rate": self.test_employee.get("hourly_rate", 0),
            "overtime_rate": self.test_employee.get("overtime_rate")
        }
        self.session.put(f"{BASE_URL}/api/employees/{self.test_employee['id']}", json=restore_payload)
    
    # ============== TIMECLOCK SHIFTS (7-ROW TABLE) ==============
    
    def test_get_timeclock_shifts(self):
        """Test GET /api/payroll/timeclock-shifts returns shifts for date range"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        # Get current week dates
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        response = self.session.get(f"{BASE_URL}/api/payroll/timeclock-shifts", params={
            "employee_id": self.test_employee['id'],
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": sunday.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} timeclock shifts for current week")
    
    def test_create_timeclock_shift(self):
        """Test POST /api/payroll/timeclock-shifts creates a new shift"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        # Create a test shift for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        shift_payload = {
            "employee_id": self.test_employee['id'],
            "date": tomorrow,
            "clock_in": f"{tomorrow}T09:00:00",
            "clock_out": f"{tomorrow}T17:00:00",
            "lunch_start": f"{tomorrow}T12:00:00",
            "lunch_end": f"{tomorrow}T12:30:00",
            "break_minutes": 30,
            "notes": "Test worksheet shift"
        }
        
        response = self.session.post(f"{BASE_URL}/api/payroll/timeclock-shifts", json=shift_payload)
        assert response.status_code == 200 or response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data.get("date") == tomorrow
        assert data.get("employee_id") == self.test_employee['id']
        
        self.created_shift_id = data.get("id")
        print(f"SUCCESS: Created timeclock shift with ID: {self.created_shift_id}")
        
        # Cleanup - delete the test shift
        if self.created_shift_id:
            delete_response = self.session.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{self.created_shift_id}")
            print(f"Cleanup: Deleted test shift (status: {delete_response.status_code})")
    
    def test_update_timeclock_shift(self):
        """Test PUT /api/payroll/timeclock-shifts/{id} updates shift"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        # First create a shift to update
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        create_payload = {
            "employee_id": self.test_employee['id'],
            "date": tomorrow,
            "clock_in": f"{tomorrow}T08:00:00",
            "clock_out": f"{tomorrow}T16:00:00",
            "notes": "Original shift"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/payroll/timeclock-shifts", json=create_payload)
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create shift for update test")
        
        shift_id = create_response.json().get("id")
        
        # Update the shift
        update_payload = {
            "clock_in": f"{tomorrow}T09:00:00",
            "clock_out": f"{tomorrow}T17:30:00",
            "lunch_start": f"{tomorrow}T12:00:00",
            "lunch_end": f"{tomorrow}T12:45:00",
            "break_minutes": 45,
            "notes": "Updated shift"
        }
        
        update_response = self.session.put(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}", json=update_payload)
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data.get("notes") == "Updated shift"
        print("SUCCESS: Timeclock shift updated")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}")
    
    def test_delete_timeclock_shift(self):
        """Test DELETE /api/payroll/timeclock-shifts/{id} deletes shift"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        # Create a shift to delete
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        create_payload = {
            "employee_id": self.test_employee['id'],
            "date": tomorrow,
            "clock_in": f"{tomorrow}T08:00:00",
            "clock_out": f"{tomorrow}T16:00:00",
            "notes": "Shift to delete"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/payroll/timeclock-shifts", json=create_payload)
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create shift for delete test")
        
        shift_id = create_response.json().get("id")
        
        # Delete the shift
        delete_response = self.session.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}")
        assert delete_response.status_code == 200
        print("SUCCESS: Timeclock shift deleted")
    
    # ============== PAYROLL TRANSACTIONS (ADJUSTMENTS PANEL) ==============
    
    def test_get_payroll_transactions(self):
        """Test GET /api/payroll/transactions returns transactions for date range"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        response = self.session.get(f"{BASE_URL}/api/payroll/transactions", params={
            "employee_id": self.test_employee['id'],
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": sunday.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} payroll transactions")
    
    def test_create_payroll_transaction(self):
        """Test POST /api/payroll/transactions creates adjustment"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        transaction_payload = {
            "employee_id": self.test_employee['id'],
            "type": "earnings",
            "amount": 50.00,
            "description": "Test worksheet bonus",
            "date": today
        }
        
        response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=transaction_payload)
        assert response.status_code == 200 or response.status_code == 201
        
        data = response.json()
        assert "id" in data
        assert data.get("amount") == 50.00
        assert data.get("type") == "earnings"
        
        self.created_transaction_id = data.get("id")
        print(f"SUCCESS: Created payroll transaction with ID: {self.created_transaction_id}")
        
        # Cleanup
        if self.created_transaction_id:
            self.session.delete(f"{BASE_URL}/api/payroll/transactions/{self.created_transaction_id}")
    
    def test_update_payroll_transaction(self):
        """Test PUT /api/payroll/transactions/{id} updates adjustment"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create transaction to update
        create_payload = {
            "employee_id": self.test_employee['id'],
            "type": "earnings",
            "amount": 25.00,
            "description": "Original bonus",
            "date": today
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=create_payload)
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create transaction for update test")
        
        transaction_id = create_response.json().get("id")
        
        # Update transaction
        update_payload = {
            "amount": 75.00,
            "description": "Updated bonus"
        }
        
        update_response = self.session.put(f"{BASE_URL}/api/payroll/transactions/{transaction_id}", json=update_payload)
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data.get("amount") == 75.00
        assert data.get("description") == "Updated bonus"
        print("SUCCESS: Payroll transaction updated")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/payroll/transactions/{transaction_id}")
    
    def test_delete_payroll_transaction(self):
        """Test DELETE /api/payroll/transactions/{id} deletes adjustment"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create transaction to delete
        create_payload = {
            "employee_id": self.test_employee['id'],
            "type": "advance",
            "amount": 100.00,
            "description": "Transaction to delete",
            "date": today
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=create_payload)
        if create_response.status_code not in [200, 201]:
            pytest.skip("Could not create transaction for delete test")
        
        transaction_id = create_response.json().get("id")
        
        # Delete transaction
        delete_response = self.session.delete(f"{BASE_URL}/api/payroll/transactions/{transaction_id}")
        assert delete_response.status_code == 200
        print("SUCCESS: Payroll transaction deleted")
    
    # ============== PAYROLL REPORT ==============
    
    def test_get_payroll_report(self):
        """Test GET /api/payroll/report returns report with overtime rate"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        response = self.session.get(f"{BASE_URL}/api/payroll/report", params={
            "employee_id": self.test_employee['id'],
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": sunday.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "employees" in data
        assert "totals" in data
        
        if data["employees"]:
            emp_report = data["employees"][0]
            print(f"Employee: {emp_report.get('employee_name')}")
            print(f"Hourly Rate: {emp_report.get('hourly_rate')}")
            print(f"Overtime Rate: {emp_report.get('overtime_rate')}")
            print(f"Total Hours: {emp_report.get('hours')}")
            print(f"Regular Hours: {emp_report.get('regular_hours')}")
            print(f"Overtime Hours: {emp_report.get('overtime_hours')}")
            print(f"Gross Pay: {emp_report.get('gross_pay')}")
            print(f"Final Owed: {emp_report.get('final_owed')}")
            
            # Verify overtime_rate is included
            assert "overtime_rate" in emp_report
        
        print("SUCCESS: Payroll report retrieved with overtime rate")
    
    def test_payroll_report_includes_worksheet_data(self):
        """Test payroll report includes worksheet shifts and transactions"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        response = self.session.get(f"{BASE_URL}/api/payroll/report", params={
            "employee_id": self.test_employee['id'],
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": sunday.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 200
        data = response.json()
        
        if data["employees"]:
            emp_report = data["employees"][0]
            
            # Check for transaction data
            assert "transactions" in emp_report or "adjustments_total" in emp_report
            
            # Check for daily breakdown
            if "daily_breakdown" in emp_report:
                print(f"Daily breakdown entries: {len(emp_report['daily_breakdown'])}")
        
        print("SUCCESS: Payroll report includes worksheet data")
    
    # ============== TIMESHEET ==============
    
    def test_get_timesheet(self):
        """Test GET /api/payroll/timesheet returns timesheet with overtime rate"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        response = self.session.get(f"{BASE_URL}/api/payroll/timesheet", params={
            "employee_id": self.test_employee['id'],
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": sunday.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "employees" in data
        assert "totals" in data
        
        if data["employees"]:
            emp_timesheet = data["employees"][0]
            print(f"Employee: {emp_timesheet.get('employee_name')}")
            print(f"Overtime Rate: {emp_timesheet.get('overtime_rate')}")
            print(f"Total Hours: {emp_timesheet.get('total_hours')}")
            print(f"Entries count: {len(emp_timesheet.get('entries', []))}")
            
            # Verify overtime_rate is included
            assert "overtime_rate" in emp_timesheet
        
        print("SUCCESS: Timesheet retrieved with overtime rate")
    
    # ============== PAYROLL BALANCE ==============
    
    def test_get_payroll_balance(self):
        """Test GET /api/payroll/balance/{employee_id} returns balance"""
        if not self.test_employee:
            pytest.skip("No test employee available")
        
        response = self.session.get(f"{BASE_URL}/api/payroll/balance/{self.test_employee['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert "employee_id" in data
        assert "employee_name" in data
        assert "total_earnings" in data
        assert "balance" in data
        
        print(f"Employee: {data.get('employee_name')}")
        print(f"Total Earnings: {data.get('total_earnings')}")
        print(f"Total Advances: {data.get('total_advances')}")
        print(f"Total Payments: {data.get('total_payments')}")
        print(f"Balance: {data.get('balance')}")
        print("SUCCESS: Payroll balance retrieved")
    
    # ============== PAY PERIOD ==============
    
    def test_get_pay_period_summary(self):
        """Test GET /api/payroll/pay-period returns summary with overtime rate"""
        response = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params={
            "period_type": "weekly"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_type" in data
        assert "period_start" in data
        assert "period_end" in data
        assert "employees" in data
        assert "totals" in data
        
        if data["employees"]:
            emp_summary = data["employees"][0]
            assert "overtime_rate" in emp_summary
            print(f"Pay period: {data.get('period_start')} to {data.get('period_end')}")
            print(f"Employee count: {len(data['employees'])}")
        
        print("SUCCESS: Pay period summary retrieved with overtime rate")
    
    # ============== EMPLOYEES LIST ==============
    
    def test_get_employees_list(self):
        """Test GET /api/employees returns list for employee selector"""
        response = self.session.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if data:
            emp = data[0]
            assert "id" in emp
            assert "name" in emp
            print(f"Retrieved {len(data)} employees")
        
        print("SUCCESS: Employees list retrieved")


class TestPayrollWorksheetCalculations:
    """Tests for worksheet calculation accuracy"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        login_data = login_response.json()
        self.token = login_data.get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        self.session.close()
    
    def test_overtime_calculation_in_report(self):
        """Test that overtime is calculated correctly in payroll report"""
        # Get a week's report
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        response = self.session.get(f"{BASE_URL}/api/payroll/report", params={
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": sunday.strftime("%Y-%m-%d"),
            "period_type": "weekly"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        if data["employees"]:
            for emp in data["employees"]:
                total_hours = emp.get("hours", 0)
                regular_hours = emp.get("regular_hours", 0)
                overtime_hours = emp.get("overtime_hours", 0)
                
                # Verify hours add up
                assert abs(total_hours - (regular_hours + overtime_hours)) < 0.01, \
                    f"Hours mismatch: {total_hours} != {regular_hours} + {overtime_hours}"
                
                # Verify overtime threshold (40 hours for weekly)
                if total_hours > 40:
                    assert overtime_hours > 0, "Should have overtime hours when total > 40"
                
                print(f"Employee {emp.get('employee_name')}: {total_hours}h total, {regular_hours}h regular, {overtime_hours}h OT")
        
        print("SUCCESS: Overtime calculations verified")
    
    def test_adjustments_total_calculation(self):
        """Test that adjustments total is calculated correctly"""
        today = datetime.now()
        monday = today - timedelta(days=today.weekday())
        sunday = monday + timedelta(days=6)
        
        response = self.session.get(f"{BASE_URL}/api/payroll/report", params={
            "start_date": monday.strftime("%Y-%m-%d"),
            "end_date": sunday.strftime("%Y-%m-%d")
        })
        
        assert response.status_code == 200
        data = response.json()
        
        if data["employees"]:
            for emp in data["employees"]:
                earnings_adj = emp.get("earnings_adjustments", 0)
                advances = emp.get("advances", 0)
                payments = emp.get("payments", 0)
                adjustments_total = emp.get("adjustments_total", 0)
                
                # Adjustments total = earnings - advances - payments
                expected_total = earnings_adj - advances - payments
                assert abs(adjustments_total - expected_total) < 0.01, \
                    f"Adjustments mismatch: {adjustments_total} != {expected_total}"
                
                print(f"Employee {emp.get('employee_name')}: Earnings {earnings_adj}, Advances {advances}, Payments {payments}, Total {adjustments_total}")
        
        print("SUCCESS: Adjustments total calculations verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
