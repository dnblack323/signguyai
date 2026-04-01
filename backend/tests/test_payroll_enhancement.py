"""
Test Payroll Enhancement Features
Tests for: Manual Hours CRUD, Timesheet, Pay Period Summary, Transactions
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPayrollEnhancement:
    """Test suite for enhanced Admin Payroll features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": LEGACY_ADMIN_EMAIL,
            "password": LEGACY_ADMIN_PASSWORD
        })
        
        if login_res.status_code != 200:
            pytest.skip("Auth failed - skipping payroll tests")
        
        token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
        
        # Get an employee ID for testing
        emp_res = self.session.get(f"{BASE_URL}/api/employees")
        self.employees = emp_res.json() if emp_res.status_code == 200 else []
        self.test_employee_id = self.employees[0]["id"] if self.employees else None
        
        yield
        
        # Cleanup - delete TEST_ prefixed hours entries
        if hasattr(self, 'created_hours_ids'):
            for entry_id in self.created_hours_ids:
                try:
                    self.session.delete(f"{BASE_URL}/api/payroll/hours/{entry_id}")
                except Exception:
                    pass

    # =================== MANUAL HOURS CRUD ===================
    
    def test_get_manual_hours_empty(self):
        """GET /api/payroll/hours - returns list (possibly empty)"""
        res = self.session.get(f"{BASE_URL}/api/payroll/hours")
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, list), "Expected list response"
        print(f"PASS: GET /api/payroll/hours returns {len(data)} entries")
    
    def test_get_manual_hours_with_date_filter(self):
        """GET /api/payroll/hours with date range filter"""
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        
        res = self.session.get(f"{BASE_URL}/api/payroll/hours", params={
            "start_date": week_ago,
            "end_date": today
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        print("PASS: GET /api/payroll/hours with date filter works")
    
    def test_create_manual_hours(self):
        """POST /api/payroll/hours - creates manual hours entry"""
        if not self.test_employee_id:
            pytest.skip("No employee available for test")
        
        self.created_hours_ids = []
        today = datetime.now().date().isoformat()
        
        payload = {
            "employee_id": self.test_employee_id,
            "date": today,
            "hours": 4.5,
            "description": "TEST_manual_hours_entry",
            "task_type": "production"
        }
        
        res = self.session.post(f"{BASE_URL}/api/payroll/hours", json=payload)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert "id" in data, "Response should have id"
        assert data["hours"] == 4.5, "Hours should match"
        assert data["employee_id"] == self.test_employee_id, "Employee ID should match"
        assert data["task_type"] == "production", "Task type should match"
        assert "gross_pay" in data, "Should calculate gross_pay"
        
        self.created_hours_ids.append(data["id"])
        print(f"PASS: POST /api/payroll/hours - created entry {data['id']} with gross_pay ${data['gross_pay']}")
        
        # Store for subsequent tests
        self.__class__.test_hours_entry_id = data["id"]
    
    def test_update_manual_hours(self):
        """PUT /api/payroll/hours/{id} - updates hours entry"""
        if not hasattr(self.__class__, 'test_hours_entry_id'):
            # Create one first
            if not self.test_employee_id:
                pytest.skip("No employee available")
            
            create_res = self.session.post(f"{BASE_URL}/api/payroll/hours", json={
                "employee_id": self.test_employee_id,
                "date": datetime.now().date().isoformat(),
                "hours": 2.0,
                "description": "TEST_update_entry",
                "task_type": "general"
            })
            if create_res.status_code != 200:
                pytest.skip("Could not create test entry")
            entry_id = create_res.json()["id"]
        else:
            entry_id = self.__class__.test_hours_entry_id
        
        # Update the entry
        update_payload = {
            "hours": 6.0,
            "description": "TEST_updated_description",
            "task_type": "design"
        }
        
        res = self.session.put(f"{BASE_URL}/api/payroll/hours/{entry_id}", json=update_payload)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data["hours"] == 6.0, "Hours should be updated to 6.0"
        assert data["task_type"] == "design", "Task type should be updated"
        print(f"PASS: PUT /api/payroll/hours/{entry_id} - updated successfully")
    
    def test_delete_manual_hours(self):
        """DELETE /api/payroll/hours/{id} - deletes hours entry"""
        if not self.test_employee_id:
            pytest.skip("No employee available")
        
        # Create entry to delete
        create_res = self.session.post(f"{BASE_URL}/api/payroll/hours", json={
            "employee_id": self.test_employee_id,
            "date": datetime.now().date().isoformat(),
            "hours": 1.0,
            "description": "TEST_to_delete",
            "task_type": "admin"
        })
        if create_res.status_code != 200:
            pytest.skip("Could not create test entry")
        
        entry_id = create_res.json()["id"]
        
        # Delete it
        res = self.session.delete(f"{BASE_URL}/api/payroll/hours/{entry_id}")
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "message" in data, "Should have success message"
        
        # Verify it's gone
        get_res = self.session.get(f"{BASE_URL}/api/payroll/hours")
        hours_list = get_res.json()
        entry_ids = [h.get("id") for h in hours_list]
        assert entry_id not in entry_ids, "Deleted entry should not exist"
        
        print(f"PASS: DELETE /api/payroll/hours/{entry_id} - deleted successfully")
    
    def test_delete_nonexistent_hours_returns_404(self):
        """DELETE /api/payroll/hours/{id} - returns 404 for nonexistent"""
        fake_id = "nonexistent-uuid-12345"
        res = self.session.delete(f"{BASE_URL}/api/payroll/hours/{fake_id}")
        
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("PASS: DELETE nonexistent hours entry returns 404")

    # =================== TIMESHEET ===================
    
    def test_get_timesheet(self):
        """GET /api/payroll/timesheet - returns consolidated timesheet data"""
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        
        res = self.session.get(f"{BASE_URL}/api/payroll/timesheet", params={
            "start_date": week_ago,
            "end_date": today
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert "start_date" in data, "Should have start_date"
        assert "end_date" in data, "Should have end_date"
        assert "employees" in data, "Should have employees array"
        assert "totals" in data, "Should have totals"
        
        # Check totals structure
        totals = data["totals"]
        assert "total_hours" in totals, "Totals should have total_hours"
        assert "regular_hours" in totals, "Totals should have regular_hours"
        assert "overtime_hours" in totals, "Totals should have overtime_hours"
        assert "total_pay" in totals, "Totals should have total_pay"
        
        # Check employee structure if any exist
        if data["employees"]:
            emp = data["employees"][0]
            assert "employee_id" in emp, "Employee should have employee_id"
            assert "employee_name" in emp, "Employee should have employee_name"
            assert "hourly_rate" in emp, "Employee should have hourly_rate"
            assert "total_hours" in emp, "Employee should have total_hours"
            assert "regular_hours" in emp, "Employee should have regular_hours"
            assert "overtime_hours" in emp, "Employee should have overtime_hours"
            assert "entries" in emp, "Employee should have entries array"
        
        print(f"PASS: GET /api/payroll/timesheet returns data with {len(data['employees'])} employees")
    
    def test_get_timesheet_with_employee_filter(self):
        """GET /api/payroll/timesheet with employee_id filter"""
        if not self.test_employee_id:
            pytest.skip("No employee available")
        
        today = datetime.now().date().isoformat()
        week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
        
        res = self.session.get(f"{BASE_URL}/api/payroll/timesheet", params={
            "start_date": week_ago,
            "end_date": today,
            "employee_id": self.test_employee_id
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        # Should only contain the filtered employee (or empty if no hours)
        if data["employees"]:
            assert len(data["employees"]) == 1, "Should only have one employee"
            assert data["employees"][0]["employee_id"] == self.test_employee_id
        
        print("PASS: GET /api/payroll/timesheet with employee filter works")

    # =================== PAY PERIOD SUMMARY ===================
    
    def test_get_pay_period_weekly(self):
        """GET /api/payroll/pay-period - returns weekly pay period summary"""
        res = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params={
            "period_type": "weekly"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data["period_type"] == "weekly", "Period type should be weekly"
        assert "period_start" in data, "Should have period_start"
        assert "period_end" in data, "Should have period_end"
        assert "employees" in data, "Should have employees"
        assert "totals" in data, "Should have totals"
        
        # Verify period is 7 days
        start = datetime.fromisoformat(data["period_start"])
        end = datetime.fromisoformat(data["period_end"])
        days = (end - start).days + 1
        assert days == 7, f"Weekly period should be 7 days, got {days}"
        
        # Check employee structure
        if data["employees"]:
            emp = data["employees"][0]
            required_fields = ["employee_id", "employee_name", "hourly_rate", 
                             "total_hours", "regular_hours", "overtime_hours",
                             "regular_pay", "overtime_pay", "gross_pay",
                             "advances", "payments_made", "net_owed", "daily_hours"]
            for field in required_fields:
                assert field in emp, f"Employee should have {field}"
        
        print(f"PASS: GET /api/payroll/pay-period (weekly) - period: {data['period_start']} to {data['period_end']}")
    
    def test_get_pay_period_biweekly(self):
        """GET /api/payroll/pay-period - returns biweekly pay period summary"""
        res = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params={
            "period_type": "biweekly"
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data["period_type"] == "biweekly", "Period type should be biweekly"
        
        # Verify period is 14 days
        start = datetime.fromisoformat(data["period_start"])
        end = datetime.fromisoformat(data["period_end"])
        days = (end - start).days + 1
        assert days == 14, f"Biweekly period should be 14 days, got {days}"
        
        print(f"PASS: GET /api/payroll/pay-period (biweekly) - period: {data['period_start']} to {data['period_end']}")
    
    def test_get_pay_period_with_reference_date(self):
        """GET /api/payroll/pay-period with reference_date parameter"""
        # Use a specific date to test
        ref_date = "2025-01-15"
        
        res = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params={
            "period_type": "weekly",
            "reference_date": ref_date
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        # The period should be the week containing Jan 15
        assert data["period_start"] <= ref_date <= data["period_end"], \
            f"Reference date {ref_date} should be within period {data['period_start']} to {data['period_end']}"
        
        print("PASS: GET /api/payroll/pay-period with reference_date works")

    # =================== PAYROLL TRANSACTIONS ===================
    
    def test_get_payroll_transactions(self):
        """GET /api/payroll/transactions - returns list of transactions"""
        res = self.session.get(f"{BASE_URL}/api/payroll/transactions")
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, list), "Expected list response"
        print(f"PASS: GET /api/payroll/transactions returns {len(data)} transactions")
    
    def test_create_payroll_transaction_earnings(self):
        """POST /api/payroll/transactions - create earnings transaction"""
        if not self.test_employee_id:
            pytest.skip("No employee available")
        
        payload = {
            "employee_id": self.test_employee_id,
            "type": "earnings",
            "amount": 150.00,
            "description": "TEST_earnings_bonus"
        }
        
        res = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=payload)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data["type"] == "earnings", "Type should be earnings"
        assert data["amount"] == 150.00, "Amount should match"
        assert "id" in data, "Should have id"
        
        print(f"PASS: POST /api/payroll/transactions (earnings) - created {data['id']}")
    
    def test_create_payroll_transaction_advance(self):
        """POST /api/payroll/transactions - create advance transaction"""
        if not self.test_employee_id:
            pytest.skip("No employee available")
        
        payload = {
            "employee_id": self.test_employee_id,
            "type": "advance",
            "amount": 50.00,
            "description": "TEST_advance_requested"
        }
        
        res = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=payload)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data["type"] == "advance", "Type should be advance"
        print(f"PASS: POST /api/payroll/transactions (advance) - created {data['id']}")
    
    def test_create_payroll_transaction_payment(self):
        """POST /api/payroll/transactions - create payment transaction"""
        if not self.test_employee_id:
            pytest.skip("No employee available")
        
        payload = {
            "employee_id": self.test_employee_id,
            "type": "payment",
            "amount": 200.00,
            "description": "TEST_payment_issued"
        }
        
        res = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=payload)
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data["type"] == "payment", "Type should be payment"
        print(f"PASS: POST /api/payroll/transactions (payment) - created {data['id']}")
    
    def test_get_transactions_with_employee_filter(self):
        """GET /api/payroll/transactions with employee_id filter"""
        if not self.test_employee_id:
            pytest.skip("No employee available")
        
        res = self.session.get(f"{BASE_URL}/api/payroll/transactions", params={
            "employee_id": self.test_employee_id
        })
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        
        # All transactions should be for this employee
        for txn in data:
            assert txn["employee_id"] == self.test_employee_id
        
        print(f"PASS: GET /api/payroll/transactions with filter returns {len(data)} transactions")

    # =================== PAYROLL BALANCE ===================
    
    def test_get_payroll_balance(self):
        """GET /api/payroll/balance/{employee_id} - returns balance summary"""
        if not self.test_employee_id:
            pytest.skip("No employee available")
        
        res = self.session.get(f"{BASE_URL}/api/payroll/balance/{self.test_employee_id}")
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data["employee_id"] == self.test_employee_id
        assert "employee_name" in data
        assert "total_earnings" in data
        assert "total_advances" in data
        assert "total_payments" in data
        assert "balance" in data
        
        # Balance formula: earnings - advances - payments
        expected_balance = data["total_earnings"] - data["total_advances"] - data["total_payments"]
        assert abs(data["balance"] - expected_balance) < 0.01, "Balance calculation should be correct"
        
        print(f"PASS: GET /api/payroll/balance/{self.test_employee_id} - balance ${data['balance']}")

    # =================== EMPLOYEES ENDPOINT ===================
    
    def test_get_employees(self):
        """GET /api/employees - required for payroll dropdowns"""
        res = self.session.get(f"{BASE_URL}/api/employees")
        
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert isinstance(data, list), "Expected list"
        
        if data:
            emp = data[0]
            assert "id" in emp
            assert "name" in emp
            assert "hourly_rate" in emp
        
        print(f"PASS: GET /api/employees returns {len(data)} employees")


class TestPayrollHoursValidation:
    """Test validation for manual hours"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_res = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": LEGACY_ADMIN_EMAIL,
            "password": LEGACY_ADMIN_PASSWORD
        })
        
        if login_res.status_code != 200:
            pytest.skip("Auth failed")
        
        token = login_res.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_hours_invalid_employee_returns_404(self):
        """POST /api/payroll/hours with invalid employee_id returns 404"""
        payload = {
            "employee_id": "nonexistent-employee-id",
            "date": datetime.now().date().isoformat(),
            "hours": 8.0,
            "task_type": "general"
        }
        
        res = self.session.post(f"{BASE_URL}/api/payroll/hours", json=payload)
        
        assert res.status_code == 404, f"Expected 404 for invalid employee, got {res.status_code}"
        print("PASS: Create hours with invalid employee returns 404")
    
    def test_update_hours_invalid_entry_returns_404(self):
        """PUT /api/payroll/hours/{id} with invalid id returns 404"""
        res = self.session.put(f"{BASE_URL}/api/payroll/hours/nonexistent-id", json={
            "hours": 5.0
        })
        
        assert res.status_code == 404, f"Expected 404, got {res.status_code}"
        print("PASS: Update nonexistent hours entry returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
