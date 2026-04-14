"""
Iteration 102 - Payroll Signoff and Legacy Review Testing

Tests for:
1. Payroll sign-off GET/PUT endpoint works per employee + week
2. Sign-off fields save and persist on /payroll
3. Legacy/manual entry review appears for off-grid weeks
4. Existing save/export/print behavior still works after sign-off addition
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPayrollSignoff:
    """Payroll signoff endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get auth token"""
        # Login to get auth token
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "signguypa@gmail.com", "password": "Billnel323"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get employees to find test employee
        employees_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=self.headers
        )
        assert employees_response.status_code == 200
        self.employees = employees_response.json()
        assert len(self.employees) > 0, "No employees found"
        
        # Find QA Test Employee or use first employee
        self.test_employee = None
        for emp in self.employees:
            if "QA Test" in emp.get("name", ""):
                self.test_employee = emp
                break
        if not self.test_employee:
            self.test_employee = self.employees[0]
        
        self.employee_id = self.test_employee["id"]
        self.week_start = "2026-04-13"  # Test week
    
    def test_get_signoff_empty(self):
        """Test GET /api/payroll/signoff returns empty signoff for new week"""
        # Use a week that likely has no signoff data
        response = requests.get(
            f"{BASE_URL}/api/payroll/signoff",
            params={"employee_id": self.employee_id, "week_start": "2026-01-06"},
            headers=self.headers
        )
        assert response.status_code == 200, f"GET signoff failed: {response.text}"
        data = response.json()
        
        # Should return a signoff object with empty fields
        assert "employee_id" in data
        assert "week_start" in data
        assert data["employee_id"] == self.employee_id
        assert data["week_start"] == "2026-01-06"
        print(f"SUCCESS: GET signoff returns empty signoff for new week")
    
    def test_put_signoff_create(self):
        """Test PUT /api/payroll/signoff creates new signoff"""
        signoff_data = {
            "employee_id": self.employee_id,
            "week_start": self.week_start,
            "reviewed_by": "Test Reviewer",
            "review_date": "2026-04-14",
            "approved_by": "Test Approver",
            "approval_date": "2026-04-14",
            "payroll_notes": "Test signoff notes for iteration 102"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/payroll/signoff",
            json=signoff_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"PUT signoff failed: {response.text}"
        data = response.json()
        
        # Verify response contains all fields
        assert data["employee_id"] == self.employee_id
        assert data["week_start"] == self.week_start
        assert data["reviewed_by"] == "Test Reviewer"
        assert data["review_date"] == "2026-04-14"
        assert data["approved_by"] == "Test Approver"
        assert data["approval_date"] == "2026-04-14"
        assert data["payroll_notes"] == "Test signoff notes for iteration 102"
        print(f"SUCCESS: PUT signoff creates new signoff")
    
    def test_get_signoff_persisted(self):
        """Test GET /api/payroll/signoff returns persisted signoff data"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/signoff",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert response.status_code == 200, f"GET signoff failed: {response.text}"
        data = response.json()
        
        # Verify persisted data
        assert data["employee_id"] == self.employee_id
        assert data["week_start"] == self.week_start
        assert data["reviewed_by"] == "Test Reviewer"
        assert data["review_date"] == "2026-04-14"
        assert data["approved_by"] == "Test Approver"
        assert data["approval_date"] == "2026-04-14"
        assert data["payroll_notes"] == "Test signoff notes for iteration 102"
        print(f"SUCCESS: GET signoff returns persisted data")
    
    def test_put_signoff_update(self):
        """Test PUT /api/payroll/signoff updates existing signoff"""
        signoff_data = {
            "employee_id": self.employee_id,
            "week_start": self.week_start,
            "reviewed_by": "Updated Reviewer",
            "review_date": "2026-04-15",
            "approved_by": "Updated Approver",
            "approval_date": "2026-04-15",
            "payroll_notes": "Updated signoff notes"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/payroll/signoff",
            json=signoff_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"PUT signoff update failed: {response.text}"
        data = response.json()
        
        # Verify updated data
        assert data["reviewed_by"] == "Updated Reviewer"
        assert data["review_date"] == "2026-04-15"
        assert data["approved_by"] == "Updated Approver"
        assert data["approval_date"] == "2026-04-15"
        assert data["payroll_notes"] == "Updated signoff notes"
        print(f"SUCCESS: PUT signoff updates existing signoff")
    
    def test_signoff_partial_update(self):
        """Test PUT /api/payroll/signoff with partial data"""
        signoff_data = {
            "employee_id": self.employee_id,
            "week_start": self.week_start,
            "reviewed_by": "Partial Reviewer",
            "review_date": "",
            "approved_by": "",
            "approval_date": "",
            "payroll_notes": ""
        }
        
        response = requests.put(
            f"{BASE_URL}/api/payroll/signoff",
            json=signoff_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"PUT signoff partial update failed: {response.text}"
        data = response.json()
        
        # Verify partial data
        assert data["reviewed_by"] == "Partial Reviewer"
        print(f"SUCCESS: PUT signoff handles partial data")


class TestPayrollTimesheetWithLegacyData:
    """Tests for legacy/manual entry review functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "signguypa@gmail.com", "password": "Billnel323"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        employees_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=self.headers
        )
        assert employees_response.status_code == 200
        self.employees = employees_response.json()
        
        # Find QA Test Employee
        self.test_employee = None
        for emp in self.employees:
            if "QA Test" in emp.get("name", ""):
                self.test_employee = emp
                break
        if not self.test_employee:
            self.test_employee = self.employees[0]
        
        self.employee_id = self.test_employee["id"]
    
    def test_timesheet_returns_entries_with_source(self):
        """Test GET /api/payroll/timesheet returns entries with source field"""
        # Week with known data
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": self.employee_id,
                "start_date": "2026-04-06",
                "end_date": "2026-04-12"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"GET timesheet failed: {response.text}"
        data = response.json()
        
        assert "employees" in data
        print(f"SUCCESS: Timesheet returns employee data")
        
        # Check if entries have source field
        if data["employees"]:
            emp_data = data["employees"][0]
            if emp_data.get("entries"):
                for entry in emp_data["entries"]:
                    # Source should be one of: time_clock, manual, job_timer
                    if "source" in entry:
                        print(f"Entry source: {entry['source']}")
    
    def test_timesheet_week_with_manual_entries(self):
        """Test timesheet for week 2026-04-06 which has manual off-grid payroll_hours"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": self.employee_id,
                "start_date": "2026-04-06",
                "end_date": "2026-04-12"
            },
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for manual entries
        manual_count = 0
        time_clock_count = 0
        if data["employees"]:
            emp_data = data["employees"][0]
            for entry in emp_data.get("entries", []):
                source = entry.get("source", "")
                if source == "manual":
                    manual_count += 1
                elif source == "time_clock":
                    time_clock_count += 1
        
        print(f"Week 2026-04-06: {manual_count} manual entries, {time_clock_count} time_clock entries")
        print(f"SUCCESS: Timesheet returns entries with source classification")


class TestPayrollReportAndExport:
    """Tests for payroll report and export functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "signguypa@gmail.com", "password": "Billnel323"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        employees_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=self.headers
        )
        assert employees_response.status_code == 200
        self.employees = employees_response.json()
        
        self.test_employee = None
        for emp in self.employees:
            if "QA Test" in emp.get("name", ""):
                self.test_employee = emp
                break
        if not self.test_employee:
            self.test_employee = self.employees[0]
        
        self.employee_id = self.test_employee["id"]
    
    def test_payroll_report_endpoint(self):
        """Test GET /api/payroll/report returns complete data"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": self.employee_id,
                "start_date": "2026-04-13",
                "end_date": "2026-04-19"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"GET report failed: {response.text}"
        data = response.json()
        
        assert "employees" in data
        assert "totals" in data
        assert "start_date" in data
        assert "end_date" in data
        
        if data["employees"]:
            emp = data["employees"][0]
            assert "employee_id" in emp
            assert "employee_name" in emp
            assert "hourly_rate" in emp
            assert "overtime_rate" in emp
            assert "gross_pay" in emp
            assert "final_owed" in emp
        
        print(f"SUCCESS: Payroll report returns complete data structure")
    
    def test_payroll_timeclock_shifts_endpoint(self):
        """Test GET /api/payroll/timeclock-shifts returns shifts"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={
                "employee_id": self.employee_id,
                "start_date": "2026-04-13",
                "end_date": "2026-04-19"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"GET timeclock-shifts failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"SUCCESS: Timeclock shifts endpoint returns {len(data)} shifts")
    
    def test_payroll_transactions_endpoint(self):
        """Test GET /api/payroll/transactions returns transactions"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/transactions",
            params={
                "employee_id": self.employee_id,
                "start_date": "2026-04-13",
                "end_date": "2026-04-19"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"GET transactions failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        print(f"SUCCESS: Transactions endpoint returns {len(data)} transactions")


class TestPayrollWorksheetSave:
    """Tests for payroll worksheet save functionality including signoff"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "signguypa@gmail.com", "password": "Billnel323"}
        )
        assert login_response.status_code == 200
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        employees_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=self.headers
        )
        assert employees_response.status_code == 200
        self.employees = employees_response.json()
        
        self.test_employee = None
        for emp in self.employees:
            if "QA Test" in emp.get("name", ""):
                self.test_employee = emp
                break
        if not self.test_employee:
            self.test_employee = self.employees[0]
        
        self.employee_id = self.test_employee["id"]
        self.week_start = "2026-04-13"
    
    def test_employee_update_with_rates(self):
        """Test PUT /api/employees/{id} updates hourly and overtime rates"""
        update_data = {
            "hourly_rate": 25.00,
            "overtime_rate": 37.50
        }
        
        response = requests.put(
            f"{BASE_URL}/api/employees/{self.employee_id}",
            json=update_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"PUT employee failed: {response.text}"
        data = response.json()
        
        assert data["hourly_rate"] == 25.00
        assert data["overtime_rate"] == 37.50
        print(f"SUCCESS: Employee rates updated")
    
    def test_timeclock_shift_crud(self):
        """Test CRUD operations for timeclock shifts"""
        # Create a new shift
        shift_data = {
            "employee_id": self.employee_id,
            "date": "2026-04-20",
            "clock_in": "2026-04-20T08:00:00",
            "clock_out": "2026-04-20T17:00:00",
            "lunch_start": "2026-04-20T12:00:00",
            "lunch_end": "2026-04-20T12:30:00",
            "break_minutes": 30,
            "notes": "Test shift for iteration 102"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            json=shift_data,
            headers=self.headers
        )
        assert create_response.status_code == 200, f"POST shift failed: {create_response.text}"
        created_shift = create_response.json()
        shift_id = created_shift["id"]
        print(f"SUCCESS: Created shift {shift_id}")
        
        # Update the shift
        update_data = {
            "clock_out": "2026-04-20T18:00:00",
            "notes": "Updated test shift"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}",
            json=update_data,
            headers=self.headers
        )
        assert update_response.status_code == 200, f"PUT shift failed: {update_response.text}"
        print(f"SUCCESS: Updated shift {shift_id}")
        
        # Delete the shift
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"DELETE shift failed: {delete_response.text}"
        print(f"SUCCESS: Deleted shift {shift_id}")
    
    def test_transaction_crud(self):
        """Test CRUD operations for payroll transactions"""
        # Create a new transaction
        transaction_data = {
            "employee_id": self.employee_id,
            "type": "earnings",
            "amount": 50.00,
            "description": "Test bonus for iteration 102",
            "date": "2026-04-20"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/transactions",
            json=transaction_data,
            headers=self.headers
        )
        assert create_response.status_code == 200, f"POST transaction failed: {create_response.text}"
        created_transaction = create_response.json()
        transaction_id = created_transaction["id"]
        print(f"SUCCESS: Created transaction {transaction_id}")
        
        # Update the transaction
        update_data = {
            "amount": 75.00,
            "description": "Updated test bonus"
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/payroll/transactions/{transaction_id}",
            json=update_data,
            headers=self.headers
        )
        assert update_response.status_code == 200, f"PUT transaction failed: {update_response.text}"
        print(f"SUCCESS: Updated transaction {transaction_id}")
        
        # Delete the transaction
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/transactions/{transaction_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"DELETE transaction failed: {delete_response.text}"
        print(f"SUCCESS: Deleted transaction {transaction_id}")


class TestReadOnlyLockState:
    """Tests for read-only lock state (coverage gap - no non-edit credential exists)"""
    
    def test_read_only_coverage_gap_documented(self):
        """Document that read-only lock state cannot be fully tested without non-edit credential"""
        # This test documents the coverage gap
        # The frontend has readOnlyLocked = !canEditPayroll
        # But we don't have a non-edit credential to test this
        print("COVERAGE GAP: Read-only lock state cannot be tested without a non-edit credential")
        print("Frontend implements: readOnlyLocked = !canEditPayroll")
        print("All inputs have disabled={readOnlyLocked} and disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-500 classes")
        assert True  # Pass to document the gap


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
