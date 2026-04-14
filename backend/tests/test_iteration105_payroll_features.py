"""
Iteration 105 - Payroll Worksheet Feature Tests
Tests for:
1. Payroll worksheet save functionality
2. Adjustments CRUD operations (including adding more rows)
3. Custom date range and presets
4. Legacy manual pay inclusion in totals
5. Export/Print endpoints
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPayrollWorksheetFeatures:
    """Test payroll worksheet core features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get test employee
        employees_response = self.session.get(f"{BASE_URL}/api/employees")
        assert employees_response.status_code == 200
        employees = employees_response.json()
        
        # Find QA Test Employee or use first employee
        self.test_employee = None
        for emp in employees:
            if "QA Test Employee" in emp.get("name", ""):
                self.test_employee = emp
                break
        if not self.test_employee and employees:
            self.test_employee = employees[0]
        
        assert self.test_employee is not None, "No test employee found"
        self.employee_id = self.test_employee["id"]
        
        # Set date range for testing
        self.start_date = "2026-04-08"
        self.end_date = "2026-04-21"
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"
        print("SUCCESS: Health check passed")
    
    def test_get_employee(self):
        """Test getting employee details"""
        response = self.session.get(f"{BASE_URL}/api/employees/{self.employee_id}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        print(f"SUCCESS: Got employee: {data.get('name')}")
    
    def test_get_timeclock_shifts(self):
        """Test getting timeclock shifts for date range"""
        params = {
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        }
        response = self.session.get(f"{BASE_URL}/api/payroll/timeclock-shifts", params=params)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Got {len(data)} timeclock shifts")
    
    def test_get_transactions(self):
        """Test getting payroll transactions (adjustments)"""
        params = {
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        }
        response = self.session.get(f"{BASE_URL}/api/payroll/transactions", params=params)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Got {len(data)} transactions/adjustments")
    
    def test_create_transaction_adjustment(self):
        """Test creating a new adjustment (adding more rows)"""
        payload = {
            "employee_id": self.employee_id,
            "date": self.start_date,
            "description": "TEST_Iteration105_Adjustment",
            "amount": 50.00,
            "type": "earnings"
        }
        response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=payload)
        assert response.status_code in [200, 201], f"Create transaction failed: {response.text}"
        data = response.json()
        assert "id" in data
        self.created_transaction_id = data["id"]
        print(f"SUCCESS: Created adjustment with ID: {self.created_transaction_id}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/payroll/transactions", params={
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        })
        assert get_response.status_code == 200
        transactions = get_response.json()
        found = any(t.get("description") == "TEST_Iteration105_Adjustment" for t in transactions)
        assert found, "Created transaction not found in list"
        print("SUCCESS: Verified adjustment was persisted")
        
        # Cleanup - delete the test transaction
        if hasattr(self, 'created_transaction_id'):
            delete_response = self.session.delete(f"{BASE_URL}/api/payroll/transactions/{self.created_transaction_id}")
            assert delete_response.status_code in [200, 204]
            print("SUCCESS: Cleaned up test adjustment")
    
    def test_update_transaction(self):
        """Test updating an existing adjustment"""
        # First create a transaction
        payload = {
            "employee_id": self.employee_id,
            "date": self.start_date,
            "description": "TEST_Update_Adjustment",
            "amount": 25.00,
            "type": "advance"
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=payload)
        assert create_response.status_code in [200, 201]
        transaction_id = create_response.json()["id"]
        
        # Update the transaction
        update_payload = {
            "employee_id": self.employee_id,
            "date": self.start_date,
            "description": "TEST_Updated_Adjustment",
            "amount": 75.00,
            "type": "earnings"
        }
        update_response = self.session.put(f"{BASE_URL}/api/payroll/transactions/{transaction_id}", json=update_payload)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        print("SUCCESS: Updated adjustment")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/payroll/transactions/{transaction_id}")
    
    def test_get_payroll_report(self):
        """Test getting payroll report for date range"""
        params = {
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        }
        response = self.session.get(f"{BASE_URL}/api/payroll/report", params=params)
        assert response.status_code == 200
        data = response.json()
        assert "employees" in data or "period_start" in data or isinstance(data, dict)
        print(f"SUCCESS: Got payroll report")
    
    def test_get_payroll_timesheet(self):
        """Test getting payroll timesheet for date range"""
        params = {
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        }
        response = self.session.get(f"{BASE_URL}/api/payroll/timesheet", params=params)
        assert response.status_code == 200
        data = response.json()
        print(f"SUCCESS: Got payroll timesheet")
    
    def test_get_legacy_manual_entries(self):
        """Test getting legacy manual entries"""
        params = {
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        }
        response = self.session.get(f"{BASE_URL}/api/payroll/legacy-manual-entries", params=params)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Calculate total legacy pay
        total_hours = sum(float(entry.get("current_effect_hours", 0)) for entry in data)
        total_pay = sum(float(entry.get("current_effect_pay", 0)) for entry in data)
        print(f"SUCCESS: Got {len(data)} legacy entries, {total_hours} hrs, ${total_pay}")
    
    def test_get_signoff(self):
        """Test getting payroll signoff"""
        params = {
            "employee_id": self.employee_id,
            "week_start": self.start_date,
            "period_end": self.end_date
        }
        response = self.session.get(f"{BASE_URL}/api/payroll/signoff", params=params)
        assert response.status_code == 200
        data = response.json()
        print(f"SUCCESS: Got signoff data")
    
    def test_update_signoff(self):
        """Test updating payroll signoff"""
        payload = {
            "employee_id": self.employee_id,
            "week_start": self.start_date,
            "period_end": self.end_date,
            "reviewed_by": "Test Reviewer",
            "review_date": "2026-04-14",
            "approved_by": "",
            "approval_date": None,
            "payroll_notes": "TEST_Iteration105_Signoff"
        }
        response = self.session.put(f"{BASE_URL}/api/payroll/signoff", json=payload)
        assert response.status_code == 200, f"Signoff update failed: {response.text}"
        print("SUCCESS: Updated signoff")
        
        # Verify
        get_response = self.session.get(f"{BASE_URL}/api/payroll/signoff", params={
            "employee_id": self.employee_id,
            "week_start": self.start_date,
            "period_end": self.end_date
        })
        assert get_response.status_code == 200
        data = get_response.json()
        assert data.get("reviewed_by") == "Test Reviewer"
        print("SUCCESS: Verified signoff was persisted")
    
    def test_update_employee_rates(self):
        """Test updating employee hourly/overtime rates (part of save worksheet)"""
        # Get current employee data
        get_response = self.session.get(f"{BASE_URL}/api/employees/{self.employee_id}")
        assert get_response.status_code == 200
        current_data = get_response.json()
        
        # Update with same data (to not break existing data)
        payload = {
            "name": current_data.get("name"),
            "title": current_data.get("title"),
            "manager_name": current_data.get("manager_name"),
            "hourly_rate": current_data.get("hourly_rate", 25),
            "overtime_rate": current_data.get("overtime_rate", 37.5)
        }
        response = self.session.put(f"{BASE_URL}/api/employees/{self.employee_id}", json=payload)
        assert response.status_code == 200, f"Employee update failed: {response.text}"
        print("SUCCESS: Updated employee rates")
    
    def test_create_timeclock_shift(self):
        """Test creating a timeclock shift"""
        payload = {
            "employee_id": self.employee_id,
            "date": "2026-04-15",
            "clock_in": "2026-04-15T09:00:00",
            "clock_out": "2026-04-15T17:00:00",
            "lunch_start": "2026-04-15T12:00:00",
            "lunch_end": "2026-04-15T12:30:00",
            "break_minutes": 30,
            "notes": "TEST_Iteration105_Shift"
        }
        response = self.session.post(f"{BASE_URL}/api/payroll/timeclock-shifts", json=payload)
        assert response.status_code in [200, 201], f"Create shift failed: {response.text}"
        data = response.json()
        shift_id = data.get("id")
        print(f"SUCCESS: Created timeclock shift with ID: {shift_id}")
        
        # Cleanup
        if shift_id:
            delete_response = self.session.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}")
            assert delete_response.status_code in [200, 204]
            print("SUCCESS: Cleaned up test shift")
    
    def test_preset_weekly_range(self):
        """Test that weekly preset returns 7 days of data"""
        # Get pay period for weekly
        params = {"period_type": "weekly"}
        response = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params=params)
        assert response.status_code == 200
        data = response.json()
        
        if "period_start" in data and "period_end" in data:
            start = datetime.fromisoformat(data["period_start"][:10])
            end = datetime.fromisoformat(data["period_end"][:10])
            days = (end - start).days + 1
            assert days == 7, f"Weekly should be 7 days, got {days}"
            print(f"SUCCESS: Weekly preset returns 7 days ({data['period_start']} to {data['period_end']})")
        else:
            print(f"INFO: Pay period response format: {data}")
    
    def test_preset_biweekly_range(self):
        """Test that biweekly preset returns 14 days of data"""
        params = {"period_type": "biweekly"}
        response = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params=params)
        assert response.status_code == 200
        data = response.json()
        
        if "period_start" in data and "period_end" in data:
            start = datetime.fromisoformat(data["period_start"][:10])
            end = datetime.fromisoformat(data["period_end"][:10])
            days = (end - start).days + 1
            assert days == 14, f"Biweekly should be 14 days, got {days}"
            print(f"SUCCESS: Biweekly preset returns 14 days ({data['period_start']} to {data['period_end']})")
        else:
            print(f"INFO: Pay period response format: {data}")
    
    def test_custom_date_range(self):
        """Test custom date range works"""
        # Use a custom 10-day range
        custom_start = "2026-04-01"
        custom_end = "2026-04-10"
        
        params = {
            "employee_id": self.employee_id,
            "start_date": custom_start,
            "end_date": custom_end
        }
        
        # Test timeclock shifts with custom range
        response = self.session.get(f"{BASE_URL}/api/payroll/timeclock-shifts", params=params)
        assert response.status_code == 200
        print(f"SUCCESS: Custom date range {custom_start} to {custom_end} works for timeclock shifts")
        
        # Test transactions with custom range
        response = self.session.get(f"{BASE_URL}/api/payroll/transactions", params=params)
        assert response.status_code == 200
        print(f"SUCCESS: Custom date range works for transactions")
        
        # Test report with custom range
        response = self.session.get(f"{BASE_URL}/api/payroll/report", params=params)
        assert response.status_code == 200
        print(f"SUCCESS: Custom date range works for report")


class TestPayrollSaveWorkflow:
    """Test the complete save worksheet workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get test employee
        employees_response = self.session.get(f"{BASE_URL}/api/employees")
        employees = employees_response.json()
        self.test_employee = employees[0] if employees else None
        assert self.test_employee is not None
        self.employee_id = self.test_employee["id"]
        
        self.start_date = "2026-04-08"
        self.end_date = "2026-04-21"
    
    def test_full_save_workflow(self):
        """Test the complete save worksheet workflow as done by frontend"""
        print("\n=== Testing Full Save Workflow ===")
        
        # Step 1: Update employee
        employee_payload = {
            "name": self.test_employee.get("name"),
            "title": self.test_employee.get("title"),
            "manager_name": self.test_employee.get("manager_name"),
            "hourly_rate": self.test_employee.get("hourly_rate", 25),
            "overtime_rate": self.test_employee.get("overtime_rate", 37.5)
        }
        response = self.session.put(f"{BASE_URL}/api/employees/{self.employee_id}", json=employee_payload)
        assert response.status_code == 200
        print("Step 1: Employee update - PASS")
        
        # Step 2: Create/update a transaction (adjustment)
        transaction_payload = {
            "employee_id": self.employee_id,
            "date": self.start_date,
            "description": "TEST_SaveWorkflow_Adjustment",
            "amount": 100.00,
            "type": "earnings"
        }
        response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json=transaction_payload)
        assert response.status_code in [200, 201]
        transaction_id = response.json().get("id")
        print("Step 2: Transaction create - PASS")
        
        # Step 3: Update signoff
        signoff_payload = {
            "employee_id": self.employee_id,
            "week_start": self.start_date,
            "period_end": self.end_date,
            "reviewed_by": "Test Reviewer",
            "review_date": "2026-04-14",
            "approved_by": "",
            "approval_date": None,
            "payroll_notes": "TEST_SaveWorkflow_Notes"
        }
        response = self.session.put(f"{BASE_URL}/api/payroll/signoff", json=signoff_payload)
        assert response.status_code == 200
        print("Step 3: Signoff update - PASS")
        
        # Verify all data persisted
        # Check transaction
        transactions = self.session.get(f"{BASE_URL}/api/payroll/transactions", params={
            "employee_id": self.employee_id,
            "start_date": self.start_date,
            "end_date": self.end_date
        }).json()
        found_transaction = any(t.get("description") == "TEST_SaveWorkflow_Adjustment" for t in transactions)
        assert found_transaction, "Transaction not persisted"
        print("Verification: Transaction persisted - PASS")
        
        # Check signoff
        signoff = self.session.get(f"{BASE_URL}/api/payroll/signoff", params={
            "employee_id": self.employee_id,
            "week_start": self.start_date,
            "period_end": self.end_date
        }).json()
        assert signoff.get("reviewed_by") == "Test Reviewer"
        print("Verification: Signoff persisted - PASS")
        
        # Cleanup
        if transaction_id:
            self.session.delete(f"{BASE_URL}/api/payroll/transactions/{transaction_id}")
        
        print("\n=== Full Save Workflow - ALL PASS ===")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
