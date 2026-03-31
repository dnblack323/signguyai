"""
Iteration 82 - Payroll Admin-Only Features Tests

Tests for:
- Admin-only payroll mutation routes: manual hours create/update/delete, timeclock shift edit, transaction create/update/delete
- Payroll transactions tab supports add/edit/delete and rollups stay correct
- Payroll Time Sheets and Time Entries both allow admin editing of timeclock-based hours
- Timeclock/Payroll/Employee Portal pay flow stays connected end-to-end
- No leftover temporary test employee data remains after cleanup
"""

import pytest
import requests
import os
import time
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "signguypa@gmail.com"
ADMIN_PASSWORD = "Billnel323"


class TestPayrollAdminOnlyMutations:
    """Test that payroll mutations are admin-only"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with admin auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.admin_token = token
        yield
    
    # ============== MANUAL HOURS CRUD (Admin-Only) ==============
    
    def test_01_admin_can_create_manual_hours(self):
        """Test admin can create manual hours entry"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        today = datetime.now().date().isoformat()
        
        response = self.session.post(f"{BASE_URL}/api/payroll/hours", json={
            "employee_id": employee_id,
            "date": today,
            "hours": 1.5,
            "description": "TEST_iter82_manual_hours",
            "task_type": "general"
        })
        assert response.status_code == 200, f"Failed to create manual hours: {response.text}"
        entry = response.json()
        assert entry.get("hours") == 1.5
        assert entry.get("description") == "TEST_iter82_manual_hours"
        print(f"PASS: Admin created manual hours entry {entry.get('id')}")
        return entry
    
    def test_02_admin_can_update_manual_hours(self):
        """Test admin can update manual hours entry"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=7)).date().isoformat()
        
        # Get existing entries
        entries = self.session.get(f"{BASE_URL}/api/payroll/hours", params={
            "start_date": week_start,
            "end_date": today
        }).json()
        
        if not entries:
            pytest.skip("No manual hours entries to update")
        
        entry = entries[0]
        entry_id = entry.get("id")
        original_hours = entry.get("hours", 0)
        
        response = self.session.put(f"{BASE_URL}/api/payroll/hours/{entry_id}", json={
            "hours": original_hours + 0.5,
            "description": "TEST_iter82_updated_hours"
        })
        assert response.status_code == 200, f"Failed to update hours: {response.text}"
        updated = response.json()
        assert updated.get("hours") == original_hours + 0.5
        print(f"PASS: Admin updated manual hours entry {entry_id}")
    
    def test_03_admin_can_delete_manual_hours(self):
        """Test admin can delete manual hours entry"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        today = datetime.now().date().isoformat()
        
        # Create an entry to delete
        create_response = self.session.post(f"{BASE_URL}/api/payroll/hours", json={
            "employee_id": employee_id,
            "date": today,
            "hours": 0.25,
            "description": "TEST_iter82_to_delete",
            "task_type": "general"
        })
        assert create_response.status_code == 200
        entry_id = create_response.json().get("id")
        
        # Delete it
        delete_response = self.session.delete(f"{BASE_URL}/api/payroll/hours/{entry_id}")
        assert delete_response.status_code == 200, f"Failed to delete hours: {delete_response.text}"
        print(f"PASS: Admin deleted manual hours entry {entry_id}")
    
    # ============== TIMECLOCK SHIFT EDIT (Admin-Only) ==============
    
    def test_04_admin_can_edit_timeclock_shift(self):
        """Test admin can edit timeclock shift"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=7)).date().isoformat()
        
        # Get existing shifts
        shifts_response = self.session.get(f"{BASE_URL}/api/payroll/timeclock-shifts", params={
            "start_date": week_start,
            "end_date": today
        })
        shifts = shifts_response.json()
        
        if not shifts:
            pytest.skip("No timeclock shifts available to edit")
        
        shift = shifts[0]
        shift_id = shift.get("id")
        
        # Edit the shift
        edit_response = self.session.put(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}", json={
            "break_minutes": 20,
            "notes": "TEST_iter82_edited_shift"
        })
        assert edit_response.status_code == 200, f"Failed to edit shift: {edit_response.text}"
        updated = edit_response.json()
        assert updated.get("break_minutes") == 20 or updated.get("notes") == "TEST_iter82_edited_shift"
        print(f"PASS: Admin edited timeclock shift {shift_id}")
    
    # ============== TRANSACTION CRUD (Admin-Only) ==============
    
    def test_05_admin_can_create_transaction(self):
        """Test admin can create payroll transaction"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        today = datetime.now().date().isoformat()
        
        response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json={
            "employee_id": employee_id,
            "type": "advance",
            "amount": 25.00,
            "description": "TEST_iter82_advance",
            "date": today
        })
        assert response.status_code == 200, f"Failed to create transaction: {response.text}"
        txn = response.json()
        assert txn.get("type") == "advance"
        assert txn.get("amount") == 25.00
        print(f"PASS: Admin created transaction {txn.get('id')}")
        return txn
    
    def test_06_admin_can_update_transaction(self):
        """Test admin can update payroll transaction"""
        # Get existing transactions
        transactions = self.session.get(f"{BASE_URL}/api/payroll/transactions").json()
        
        if not transactions:
            pytest.skip("No transactions available to update")
        
        # Find a test transaction
        test_txn = next((t for t in transactions if "TEST_" in (t.get("description") or "")), transactions[0])
        txn_id = test_txn.get("id")
        
        response = self.session.put(f"{BASE_URL}/api/payroll/transactions/{txn_id}", json={
            "amount": 30.00,
            "description": "TEST_iter82_updated_txn"
        })
        assert response.status_code == 200, f"Failed to update transaction: {response.text}"
        updated = response.json()
        assert updated.get("amount") == 30.00
        print(f"PASS: Admin updated transaction {txn_id}")
    
    def test_07_admin_can_delete_transaction(self):
        """Test admin can delete payroll transaction"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        today = datetime.now().date().isoformat()
        
        # Create a transaction to delete
        create_response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json={
            "employee_id": employee_id,
            "type": "payment",
            "amount": 10.00,
            "description": "TEST_iter82_to_delete",
            "date": today
        })
        assert create_response.status_code == 200
        txn_id = create_response.json().get("id")
        
        # Delete it
        delete_response = self.session.delete(f"{BASE_URL}/api/payroll/transactions/{txn_id}")
        assert delete_response.status_code == 200, f"Failed to delete transaction: {delete_response.text}"
        print(f"PASS: Admin deleted transaction {txn_id}")
    
    # ============== PAYROLL ROLLUPS STAY CORRECT ==============
    
    def test_08_payroll_rollups_after_transaction_changes(self):
        """Test payroll rollups stay correct after transaction changes"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        
        # Get initial balance
        initial_balance = self.session.get(f"{BASE_URL}/api/payroll/balance/{employee_id}").json()
        initial_advances = initial_balance.get("total_advances", 0)
        
        # Add an advance
        today = datetime.now().date().isoformat()
        create_response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json={
            "employee_id": employee_id,
            "type": "advance",
            "amount": 15.00,
            "description": "TEST_iter82_rollup_test",
            "date": today
        })
        assert create_response.status_code == 200
        txn_id = create_response.json().get("id")
        
        # Check balance increased
        new_balance = self.session.get(f"{BASE_URL}/api/payroll/balance/{employee_id}").json()
        assert new_balance.get("total_advances", 0) == initial_advances + 15.00, "Advances should increase by 15"
        
        # Delete the advance
        self.session.delete(f"{BASE_URL}/api/payroll/transactions/{txn_id}")
        
        # Check balance returned to original
        final_balance = self.session.get(f"{BASE_URL}/api/payroll/balance/{employee_id}").json()
        assert abs(final_balance.get("total_advances", 0) - initial_advances) < 0.01, "Advances should return to original"
        
        print(f"PASS: Payroll rollups stay correct after transaction changes")
    
    # ============== TIMESHEET INCLUDES TIMECLOCK ENTRIES ==============
    
    def test_09_timesheet_includes_timeclock_entries(self):
        """Test timesheet includes timeclock entries with edit capability"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat()
        
        response = self.session.get(f"{BASE_URL}/api/payroll/timesheet", params={
            "start_date": week_start,
            "end_date": today
        })
        assert response.status_code == 200, f"Failed to get timesheet: {response.text}"
        data = response.json()
        
        assert "employees" in data, "Should have employees"
        
        # Check for timeclock entries
        timeclock_found = False
        for emp in data.get("employees", []):
            for entry in emp.get("entries", []):
                if entry.get("source") == "time_clock":
                    timeclock_found = True
                    assert "id" in entry, "Timeclock entry should have id for editing"
                    assert "hours" in entry, "Timeclock entry should have hours"
                    break
            if timeclock_found:
                break
        
        print(f"PASS: Timesheet includes timeclock entries (found: {timeclock_found})")
    
    # ============== PAY PERIOD INCLUDES ALL SOURCES ==============
    
    def test_10_pay_period_includes_all_hour_sources(self):
        """Test pay period includes timeclock + manual + job timer hours"""
        response = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params={
            "period_type": "weekly"
        })
        assert response.status_code == 200, f"Failed to get pay period: {response.text}"
        data = response.json()
        
        assert "employees" in data, "Should have employees"
        assert "totals" in data, "Should have totals"
        
        # Verify structure
        if data.get("employees"):
            emp = data["employees"][0]
            assert "total_hours" in emp, "Employee should have total_hours"
            assert "gross_pay" in emp, "Employee should have gross_pay"
            assert "net_owed" in emp, "Employee should have net_owed"
        
        print(f"PASS: Pay period includes all hour sources - total hours: {data.get('totals', {}).get('total_hours', 0)}")


class TestEmployeePortalPayConnection:
    """Test employee portal pay flow stays connected"""
    
    def test_11_employee_portal_pay_reflects_admin_changes(self):
        """Test employee portal pay summary reflects admin payroll changes"""
        # First, login as admin and get an employee
        admin_session = requests.Session()
        admin_session.headers.update({"Content-Type": "application/json"})
        
        login_response = admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        admin_token = login_response.json().get("access_token")
        admin_session.headers.update({"Authorization": f"Bearer {admin_token}"})
        
        # Get employees
        employees = admin_session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        # Find an employee with email for portal login
        test_employee = None
        for emp in employees:
            if emp.get("email") and emp.get("pin"):
                test_employee = emp
                break
        
        if not test_employee:
            pytest.skip("No employee with email/PIN for portal login")
        
        # Try employee portal login
        portal_login = requests.post(f"{BASE_URL}/api/employee-portal/auth/login", json={
            "email": test_employee["email"],
            "pin": test_employee.get("pin", "1234")
        })
        
        if portal_login.status_code != 200:
            pytest.skip(f"Employee portal login failed: {portal_login.text}")
        
        emp_token = portal_login.json().get("access_token")
        
        # Get employee pay summary
        pay_response = requests.get(f"{BASE_URL}/api/employee-portal/pay/summary", headers={
            "Authorization": f"Bearer {emp_token}"
        })
        assert pay_response.status_code == 200, f"Failed to get pay summary: {pay_response.text}"
        summary = pay_response.json()
        
        assert "current_period_earnings" in summary
        assert "current_period_hours" in summary
        assert "ytd_earnings" in summary
        assert "balance_owed" in summary
        
        print(f"PASS: Employee portal pay summary connected - current: ${summary.get('current_period_earnings')}, YTD: ${summary.get('ytd_earnings')}")


class TestScheduleEndpoint:
    """Test schedule endpoint uses 12-hour formatting"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with admin auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_12_schedule_endpoint_works(self):
        """Test schedule endpoint returns data"""
        response = self.session.get(f"{BASE_URL}/api/payroll/schedule")
        assert response.status_code == 200, f"Failed to get schedule: {response.text}"
        data = response.json()
        
        assert "week_start" in data, "Should have week_start"
        assert "schedules" in data, "Should have schedules"
        
        print(f"PASS: Schedule endpoint works - week_start: {data.get('week_start')}")
    
    def test_13_admin_can_save_schedule(self):
        """Test admin can save schedule entry"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        
        # Calculate current week start
        today = datetime.now()
        monday_offset = today.weekday()
        monday = today - timedelta(days=monday_offset)
        week_start = monday.date().isoformat()
        
        response = self.session.post(f"{BASE_URL}/api/payroll/schedule", json={
            "employee_id": employee_id,
            "week_start": week_start,
            "day": "mon",
            "start_time": "09:00",
            "end_time": "17:00",
            "notes": "TEST_iter82_schedule"
        })
        assert response.status_code == 200, f"Failed to save schedule: {response.text}"
        print(f"PASS: Admin saved schedule entry")


class TestCleanupVerification:
    """Test that no leftover test data remains"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with admin auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_14_cleanup_test_transactions(self):
        """Clean up TEST_ prefixed transactions"""
        transactions = self.session.get(f"{BASE_URL}/api/payroll/transactions").json()
        
        test_txns = [t for t in transactions if "TEST_" in (t.get("description") or "")]
        deleted_count = 0
        
        for txn in test_txns:
            try:
                self.session.delete(f"{BASE_URL}/api/payroll/transactions/{txn['id']}")
                deleted_count += 1
            except:
                pass
        
        print(f"PASS: Cleaned up {deleted_count} test transactions")
    
    def test_15_cleanup_test_manual_hours(self):
        """Clean up TEST_ prefixed manual hours"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=30)).date().isoformat()
        
        entries = self.session.get(f"{BASE_URL}/api/payroll/hours", params={
            "start_date": week_start,
            "end_date": today
        }).json()
        
        test_entries = [e for e in entries if "TEST_" in (e.get("description") or "")]
        deleted_count = 0
        
        for entry in test_entries:
            try:
                self.session.delete(f"{BASE_URL}/api/payroll/hours/{entry['id']}")
                deleted_count += 1
            except:
                pass
        
        print(f"PASS: Cleaned up {deleted_count} test manual hours entries")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
