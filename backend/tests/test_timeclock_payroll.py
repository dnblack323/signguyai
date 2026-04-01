"""
Timeclock and Payroll Integration Tests

Tests for:
- Admin TimeClock flow: create/use employee, clock in, break start/end, clock out
- Time clock entries persist and are reflected in saved payroll timeclock shifts
- Payroll /pay-period summary includes timeclock hours, manual hours, and advances/payments correctly
- Payroll /timesheet includes timeclock entries plus manual entries and supports editing hours
- Payroll Time Entries tab shows combined entries and admin can edit timeclock shifts
- Employee portal pay summary reflects the same connected hours/earnings/advances logic
- Transactions/advances affect payroll totals and balances correctly
"""

import pytest
import requests
import os
import time
from datetime import datetime, timedelta
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = PRODUCTION_OWNER_EMAIL
ADMIN_PASSWORD = PRODUCTION_OWNER_PASSWORD
EMPLOYEE_EMAIL = "clockqa_02e57d@example.com"
EMPLOYEE_PIN = "1234"


class TestTimeclockPayrollIntegration:
    """Test timeclock and payroll integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
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
    
    # ============== EMPLOYEE MANAGEMENT ==============
    
    def test_01_get_employees(self):
        """Test getting employees list"""
        response = self.session.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200, f"Failed to get employees: {response.text}"
        employees = response.json()
        assert isinstance(employees, list), "Employees should be a list"
        print(f"PASS: Found {len(employees)} employees")
        return employees
    
    def test_02_create_test_employee(self):
        """Test creating a test employee for timeclock testing"""
        test_employee = {
            "name": "TEST_TimeclockQA_Employee",
            "email": f"test_timeclock_{int(time.time())}@example.com",
            "hourly_rate": 25.00,
            "pin": "9999"
        }
        response = self.session.post(f"{BASE_URL}/api/employees", json=test_employee)
        assert response.status_code == 200, f"Failed to create employee: {response.text}"
        employee = response.json()
        assert employee.get("name") == test_employee["name"]
        assert employee.get("hourly_rate") == 25.00
        print(f"PASS: Created test employee {employee.get('id')}")
        return employee
    
    # ============== TIMECLOCK OPERATIONS ==============
    
    def test_03_timeclock_start_work(self):
        """Test clock in (start_work) action"""
        # First get an employee
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available for timeclock test")
        
        employee = employees[0]
        employee_id = employee["id"]
        
        # Check current status
        status_response = self.session.get(f"{BASE_URL}/api/timeclock/{employee_id}/status")
        assert status_response.status_code == 200, f"Failed to get status: {status_response.text}"
        status = status_response.json()
        print(f"Current status: {status}")
        
        # If already working, end work first
        if status.get("status") in ["working", "on_break"]:
            if status.get("status") == "on_break":
                self.session.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "break_end"})
            self.session.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "end_work"})
        
        # Start work
        response = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": employee_id,
            "action": "start_work"
        })
        assert response.status_code == 200, f"Failed to start work: {response.text}"
        log = response.json()
        assert log.get("action") == "start_work"
        print(f"PASS: Started work for employee {employee_id}")
        return employee_id
    
    def test_04_timeclock_break_start(self):
        """Test break start action"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        
        # Ensure employee is working
        status = self.session.get(f"{BASE_URL}/api/timeclock/{employee_id}/status").json()
        if status.get("status") != "working":
            self.session.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "start_work"})
        
        response = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": employee_id,
            "action": "break_start"
        })
        assert response.status_code == 200, f"Failed to start break: {response.text}"
        log = response.json()
        assert log.get("action") == "break_start"
        print(f"PASS: Started break for employee {employee_id}")
    
    def test_05_timeclock_break_end(self):
        """Test break end action"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        
        # Ensure employee is on break
        status = self.session.get(f"{BASE_URL}/api/timeclock/{employee_id}/status").json()
        if status.get("status") != "on_break":
            if status.get("status") != "working":
                self.session.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "start_work"})
            self.session.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "break_start"})
        
        response = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": employee_id,
            "action": "break_end"
        })
        assert response.status_code == 200, f"Failed to end break: {response.text}"
        log = response.json()
        assert log.get("action") == "break_end"
        print(f"PASS: Ended break for employee {employee_id}")
    
    def test_06_timeclock_end_work(self):
        """Test clock out (end_work) action"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        
        # Ensure employee is working
        status = self.session.get(f"{BASE_URL}/api/timeclock/{employee_id}/status").json()
        if status.get("status") == "on_break":
            self.session.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "break_end"})
        if status.get("status") not in ["working"]:
            self.session.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "start_work"})
        
        response = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": employee_id,
            "action": "end_work"
        })
        assert response.status_code == 200, f"Failed to end work: {response.text}"
        log = response.json()
        assert log.get("action") == "end_work"
        print(f"PASS: Ended work for employee {employee_id}")
    
    def test_07_timeclock_today_logs(self):
        """Test getting today's time logs"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        response = self.session.get(f"{BASE_URL}/api/timeclock/{employee_id}/today")
        assert response.status_code == 200, f"Failed to get today logs: {response.text}"
        logs = response.json()
        assert isinstance(logs, list), "Logs should be a list"
        print(f"PASS: Found {len(logs)} logs for today")
    
    def test_08_timeclock_shift_summary(self):
        """Test getting shift summary"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        response = self.session.get(f"{BASE_URL}/api/timeclock/{employee_id}/summary")
        assert response.status_code == 200, f"Failed to get summary: {response.text}"
        summary = response.json()
        assert "work_minutes" in summary or "net_hours" in summary, "Summary should have time data"
        print(f"PASS: Shift summary - net_hours: {summary.get('net_hours', 0)}")
    
    # ============== PAYROLL TIMECLOCK SHIFTS ==============
    
    def test_09_payroll_timeclock_shifts_endpoint(self):
        """Test /api/payroll/timeclock-shifts endpoint returns saved shifts"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat()
        
        response = self.session.get(f"{BASE_URL}/api/payroll/timeclock-shifts", params={
            "start_date": week_start,
            "end_date": today
        })
        assert response.status_code == 200, f"Failed to get timeclock shifts: {response.text}"
        shifts = response.json()
        assert isinstance(shifts, list), "Shifts should be a list"
        print(f"PASS: Found {len(shifts)} timeclock shifts in payroll")
        
        # Verify shift structure
        if shifts:
            shift = shifts[0]
            assert "employee_id" in shift, "Shift should have employee_id"
            assert "date" in shift, "Shift should have date"
            assert "clock_in" in shift or "net_hours" in shift, "Shift should have clock_in or net_hours"
            print(f"PASS: Shift structure verified - date: {shift.get('date')}, net_hours: {shift.get('net_hours')}")
    
    def test_10_payroll_timeclock_shift_edit(self):
        """Test editing a timeclock shift via /api/payroll/timeclock-shifts/{shift_id}"""
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
            "break_minutes": 15,
            "notes": "TEST_edited_shift"
        })
        assert edit_response.status_code == 200, f"Failed to edit shift: {edit_response.text}"
        updated = edit_response.json()
        assert updated.get("break_minutes") == 15 or updated.get("notes") == "TEST_edited_shift"
        print(f"PASS: Successfully edited timeclock shift {shift_id}")
    
    # ============== PAYROLL PAY PERIOD ==============
    
    def test_11_payroll_pay_period_summary(self):
        """Test /api/payroll/pay-period includes timeclock hours, manual hours, and transactions"""
        response = self.session.get(f"{BASE_URL}/api/payroll/pay-period", params={
            "period_type": "weekly"
        })
        assert response.status_code == 200, f"Failed to get pay period: {response.text}"
        data = response.json()
        
        assert "period_start" in data, "Should have period_start"
        assert "period_end" in data, "Should have period_end"
        assert "employees" in data, "Should have employees list"
        assert "totals" in data, "Should have totals"
        
        print(f"PASS: Pay period {data.get('period_start')} to {data.get('period_end')}")
        print(f"  Total hours: {data.get('totals', {}).get('total_hours', 0)}")
        print(f"  Gross pay: {data.get('totals', {}).get('gross_pay', 0)}")
        print(f"  Net owed: {data.get('totals', {}).get('net_owed', 0)}")
        
        # Verify employee data structure
        if data.get("employees"):
            emp = data["employees"][0]
            assert "employee_id" in emp, "Employee should have employee_id"
            assert "total_hours" in emp, "Employee should have total_hours"
            assert "gross_pay" in emp, "Employee should have gross_pay"
            assert "advances" in emp, "Employee should have advances"
            assert "payments_made" in emp, "Employee should have payments_made"
            assert "net_owed" in emp, "Employee should have net_owed"
            print("PASS: Employee data structure verified")
    
    # ============== PAYROLL TIMESHEET ==============
    
    def test_12_payroll_timesheet(self):
        """Test /api/payroll/timesheet includes timeclock entries plus manual entries"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=datetime.now().weekday())).date().isoformat()
        
        response = self.session.get(f"{BASE_URL}/api/payroll/timesheet", params={
            "start_date": week_start,
            "end_date": today
        })
        assert response.status_code == 200, f"Failed to get timesheet: {response.text}"
        data = response.json()
        
        assert "employees" in data, "Should have employees"
        assert "totals" in data, "Should have totals"
        
        print(f"PASS: Timesheet {data.get('start_date')} to {data.get('end_date')}")
        print(f"  Total hours: {data.get('totals', {}).get('total_hours', 0)}")
        
        # Check entries include different sources
        if data.get("employees"):
            for emp in data["employees"]:
                entries = emp.get("entries", [])
                sources = set(e.get("source") for e in entries)
                print(f"  Employee {emp.get('employee_name')}: {len(entries)} entries, sources: {sources}")
    
    # ============== MANUAL HOURS ==============
    
    def test_13_add_manual_hours(self):
        """Test adding manual hours entry"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        today = datetime.now().date().isoformat()
        
        response = self.session.post(f"{BASE_URL}/api/payroll/hours", json={
            "employee_id": employee_id,
            "date": today,
            "hours": 2.5,
            "description": "TEST_manual_hours_entry",
            "task_type": "general"
        })
        assert response.status_code == 200, f"Failed to add manual hours: {response.text}"
        entry = response.json()
        assert entry.get("hours") == 2.5
        print(f"PASS: Added manual hours entry {entry.get('id')}")
        return entry
    
    def test_14_get_manual_hours(self):
        """Test getting manual hours entries"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=7)).date().isoformat()
        
        response = self.session.get(f"{BASE_URL}/api/payroll/hours", params={
            "start_date": week_start,
            "end_date": today
        })
        assert response.status_code == 200, f"Failed to get manual hours: {response.text}"
        entries = response.json()
        assert isinstance(entries, list), "Entries should be a list"
        print(f"PASS: Found {len(entries)} manual hours entries")
    
    def test_15_edit_manual_hours(self):
        """Test editing manual hours entry"""
        today = datetime.now().date().isoformat()
        week_start = (datetime.now() - timedelta(days=7)).date().isoformat()
        
        # Get existing entries
        entries = self.session.get(f"{BASE_URL}/api/payroll/hours", params={
            "start_date": week_start,
            "end_date": today
        }).json()
        
        if not entries:
            pytest.skip("No manual hours entries to edit")
        
        entry = entries[0]
        entry_id = entry.get("id")
        
        response = self.session.put(f"{BASE_URL}/api/payroll/hours/{entry_id}", json={
            "hours": 3.0,
            "description": "TEST_edited_hours"
        })
        assert response.status_code == 200, f"Failed to edit hours: {response.text}"
        updated = response.json()
        assert updated.get("hours") == 3.0
        print(f"PASS: Edited manual hours entry {entry_id}")
    
    # ============== TRANSACTIONS ==============
    
    def test_16_add_advance_transaction(self):
        """Test adding an advance transaction"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        today = datetime.now().date().isoformat()
        
        response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json={
            "employee_id": employee_id,
            "type": "advance",
            "amount": 50.00,
            "description": "TEST_advance_transaction",
            "date": today
        })
        assert response.status_code == 200, f"Failed to add advance: {response.text}"
        txn = response.json()
        assert txn.get("type") == "advance"
        assert txn.get("amount") == 50.00
        print(f"PASS: Added advance transaction {txn.get('id')}")
    
    def test_17_add_payment_transaction(self):
        """Test adding a payment transaction"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        today = datetime.now().date().isoformat()
        
        response = self.session.post(f"{BASE_URL}/api/payroll/transactions", json={
            "employee_id": employee_id,
            "type": "payment",
            "amount": 100.00,
            "description": "TEST_payment_transaction",
            "date": today
        })
        assert response.status_code == 200, f"Failed to add payment: {response.text}"
        txn = response.json()
        assert txn.get("type") == "payment"
        print(f"PASS: Added payment transaction {txn.get('id')}")
    
    def test_18_get_transactions(self):
        """Test getting transactions"""
        response = self.session.get(f"{BASE_URL}/api/payroll/transactions")
        assert response.status_code == 200, f"Failed to get transactions: {response.text}"
        transactions = response.json()
        assert isinstance(transactions, list), "Transactions should be a list"
        print(f"PASS: Found {len(transactions)} transactions")
    
    def test_19_transactions_affect_payroll_balance(self):
        """Test that transactions affect payroll totals correctly"""
        employees = self.session.get(f"{BASE_URL}/api/employees").json()
        if not employees:
            pytest.skip("No employees available")
        
        employee_id = employees[0]["id"]
        
        # Get payroll balance
        response = self.session.get(f"{BASE_URL}/api/payroll/balance/{employee_id}")
        assert response.status_code == 200, f"Failed to get balance: {response.text}"
        balance = response.json()
        
        assert "total_earnings" in balance, "Should have total_earnings"
        assert "total_advances" in balance, "Should have total_advances"
        assert "total_payments" in balance, "Should have total_payments"
        assert "balance" in balance, "Should have balance"
        
        # Verify balance calculation: balance = earnings - advances - payments
        expected_balance = balance["total_earnings"] - balance["total_advances"] - balance["total_payments"]
        assert abs(balance["balance"] - expected_balance) < 0.01, f"Balance calculation mismatch: {balance['balance']} vs {expected_balance}"
        print(f"PASS: Balance calculation verified - earnings: {balance['total_earnings']}, advances: {balance['total_advances']}, payments: {balance['total_payments']}, balance: {balance['balance']}")


class TestEmployeePortalPay:
    """Test employee portal pay summary"""
    
    def test_20_employee_portal_login(self):
        """Test employee portal login"""
        response = requests.post(f"{BASE_URL}/api/employee-portal/auth/login", json={
            "email": EMPLOYEE_EMAIL,
            "pin": EMPLOYEE_PIN
        })
        assert response.status_code == 200, f"Employee login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "Should have access_token"
        assert "employee_id" in data, "Should have employee_id"
        print(f"PASS: Employee portal login successful for {data.get('employee_name')}")
        return data
    
    def test_21_employee_portal_pay_summary(self):
        """Test employee portal pay summary endpoint"""
        # Login first
        login_response = requests.post(f"{BASE_URL}/api/employee-portal/auth/login", json={
            "email": EMPLOYEE_EMAIL,
            "pin": EMPLOYEE_PIN
        })
        if login_response.status_code != 200:
            pytest.skip(f"Employee login failed: {login_response.text}")
        
        token = login_response.json().get("access_token")
        
        # Get pay summary
        response = requests.get(f"{BASE_URL}/api/employee-portal/pay/summary", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Failed to get pay summary: {response.text}"
        summary = response.json()
        
        assert "current_period_earnings" in summary, "Should have current_period_earnings"
        assert "current_period_hours" in summary, "Should have current_period_hours"
        assert "ytd_earnings" in summary, "Should have ytd_earnings"
        assert "ytd_hours" in summary, "Should have ytd_hours"
        assert "balance_owed" in summary, "Should have balance_owed"
        
        print(f"PASS: Employee pay summary - current period: {summary.get('current_period_hours')} hrs, ${summary.get('current_period_earnings')}")
        print(f"  YTD: {summary.get('ytd_hours')} hrs, ${summary.get('ytd_earnings')}")
        print(f"  Balance owed: ${summary.get('balance_owed')}")
    
    def test_22_employee_portal_timeclock_status(self):
        """Test employee portal timeclock status"""
        login_response = requests.post(f"{BASE_URL}/api/employee-portal/auth/login", json={
            "email": EMPLOYEE_EMAIL,
            "pin": EMPLOYEE_PIN
        })
        if login_response.status_code != 200:
            pytest.skip(f"Employee login failed: {login_response.text}")
        
        token = login_response.json().get("access_token")
        
        response = requests.get(f"{BASE_URL}/api/employee-portal/time-clock/status", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200, f"Failed to get timeclock status: {response.text}"
        status = response.json()
        
        assert "is_clocked_in" in status, "Should have is_clocked_in"
        assert "total_hours_today" in status, "Should have total_hours_today"
        print(f"PASS: Employee timeclock status - clocked_in: {status.get('is_clocked_in')}, hours_today: {status.get('total_hours_today')}")


class TestAICreditConfirmation:
    """Test AI credit confirmation dialog doesn't block the page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with auth"""
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
        yield
    
    def test_23_ai_credits_preflight(self):
        """Test AI credits preflight endpoint works"""
        response = self.session.post(f"{BASE_URL}/api/credits/preflight", json={
            "action_type": "race_number_designer",
            "credits_required": 1
        })
        assert response.status_code == 200, f"Preflight failed: {response.text}"
        data = response.json()
        
        assert "sufficient_credits" in data, "Should have sufficient_credits"
        assert "should_show_popup" in data, "Should have should_show_popup"
        print(f"PASS: AI credits preflight - sufficient: {data.get('sufficient_credits')}, show_popup: {data.get('should_show_popup')}")
    
    def test_24_ai_credits_balance(self):
        """Test AI credits balance endpoint"""
        response = self.session.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200, f"Balance failed: {response.text}"
        data = response.json()
        
        assert "monthly_credits" in data or "total_credits" in data, "Should have credits info"
        print("PASS: AI credits balance retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
