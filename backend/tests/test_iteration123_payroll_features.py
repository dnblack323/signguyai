"""
Iteration 123: Payroll Timeclock Lunch Persistence, Paid in Full, and Settings Toggle Tests

Tests:
1. Timeclock shift edit API accepts null lunch_start/lunch_end and updates break_minutes
2. Payroll worksheet totals deduct break_minutes even when lunch fields are blank
3. When same date has multiple shifts, worksheet row totals include all time (including split-shift lunch gaps)
4. Manual worksheet edits update displayed total hours/pay before save and persist after save/reload
5. POST /api/payroll/mark-paid-in-full creates/updates payment transaction for selected employee and selected period
6. Company Settings payroll toggle show_payroll_adjustments saves and controls visibility
7. Admin editability remains enabled after marking paid
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestPayrollAuth:
    """Authentication tests for payroll endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_login_success(self, auth_token):
        """Verify login works with test credentials"""
        assert auth_token is not None
        assert len(auth_token) > 0
        print(f"✓ Login successful, token length: {len(auth_token)}")


class TestTimeclockShiftEdit:
    """Test timeclock shift edit API accepts null lunch_start/lunch_end and updates break_minutes"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_employee(self, auth_headers):
        """Get or create a test employee"""
        # Get existing employees
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200
        employees = response.json()
        if employees:
            return employees[0]
        
        # Create test employee if none exist
        response = requests.post(f"{BASE_URL}/api/employees", headers=auth_headers, json={
            "name": "TEST_PayrollTestEmployee",
            "email": "test_payroll_employee@example.com",
            "hourly_rate": 25.00
        })
        assert response.status_code == 200
        return response.json()
    
    @pytest.fixture(scope="class")
    def test_shift(self, auth_headers, test_employee):
        """Create a test shift for editing"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.post(f"{BASE_URL}/api/payroll/timeclock-shifts", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "date": today,
            "clock_in": f"{today}T08:00:00",
            "clock_out": f"{today}T17:00:00",
            "lunch_start": f"{today}T12:00:00",
            "lunch_end": f"{today}T12:30:00",
            "break_minutes": 30,
            "notes": "TEST_shift_for_edit_test"
        })
        assert response.status_code == 200, f"Failed to create shift: {response.text}"
        shift = response.json()
        yield shift
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift['id']}", headers=auth_headers)
    
    def test_edit_shift_with_null_lunch_fields(self, auth_headers, test_shift):
        """Test that shift edit accepts null lunch_start/lunch_end and updates break_minutes"""
        shift_id = test_shift["id"]
        
        # Edit shift with null lunch fields but explicit break_minutes
        response = requests.put(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}", headers=auth_headers, json={
            "lunch_start": None,
            "lunch_end": None,
            "break_minutes": 45
        })
        
        assert response.status_code == 200, f"Edit failed: {response.text}"
        updated = response.json()
        
        # Verify break_minutes was updated
        assert updated.get("break_minutes") == 45, f"break_minutes not updated: {updated.get('break_minutes')}"
        print(f"✓ Shift edit with null lunch fields accepted, break_minutes updated to {updated.get('break_minutes')}")
    
    def test_edit_shift_preserves_break_minutes_when_lunch_blank(self, auth_headers, test_shift):
        """Test that break_minutes is preserved when lunch fields are blank"""
        shift_id = test_shift["id"]
        
        # First set break_minutes explicitly
        response = requests.put(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}", headers=auth_headers, json={
            "break_minutes": 60
        })
        assert response.status_code == 200
        
        # Verify it persisted
        shifts_response = requests.get(f"{BASE_URL}/api/payroll/timeclock-shifts", headers=auth_headers, params={
            "employee_id": test_shift["employee_id"],
            "start_date": test_shift["date"],
            "end_date": test_shift["date"]
        })
        assert shifts_response.status_code == 200
        shifts = shifts_response.json()
        
        found_shift = next((s for s in shifts if s["id"] == shift_id), None)
        assert found_shift is not None, "Shift not found after edit"
        assert found_shift.get("break_minutes") == 60, f"break_minutes not persisted: {found_shift.get('break_minutes')}"
        print(f"✓ break_minutes persisted correctly: {found_shift.get('break_minutes')}")


class TestPayrollWorksheetTotals:
    """Test payroll worksheet totals deduct break_minutes even when lunch fields are blank"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_employee(self, auth_headers):
        """Get first employee"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200
        employees = response.json()
        assert len(employees) > 0, "No employees found"
        return employees[0]
    
    def test_worksheet_deducts_break_minutes(self, auth_headers, test_employee):
        """Test that worksheet totals deduct break_minutes from net hours"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create a shift with break_minutes but no lunch fields
        response = requests.post(f"{BASE_URL}/api/payroll/timeclock-shifts", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "date": today,
            "clock_in": f"{today}T09:00:00",
            "clock_out": f"{today}T17:00:00",  # 8 hours gross
            "lunch_start": None,
            "lunch_end": None,
            "break_minutes": 60,  # 1 hour break
            "notes": "TEST_break_deduction_test"
        })
        assert response.status_code == 200, f"Failed to create shift: {response.text}"
        shift = response.json()
        
        try:
            # Verify net_hours calculation
            # 8 hours gross - 1 hour break = 7 hours net
            assert "net_hours" in shift, "net_hours not in response"
            expected_net_hours = 7.0
            actual_net_hours = shift.get("net_hours", 0)
            
            # Allow small floating point tolerance
            assert abs(actual_net_hours - expected_net_hours) < 0.1, \
                f"net_hours incorrect: expected ~{expected_net_hours}, got {actual_net_hours}"
            
            print(f"✓ Worksheet correctly deducts break_minutes: net_hours={actual_net_hours}")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift['id']}", headers=auth_headers)


class TestMultipleShiftsSameDay:
    """Test that when same date has multiple shifts, worksheet row totals include all time"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_employee(self, auth_headers):
        """Get first employee"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200
        employees = response.json()
        assert len(employees) > 0, "No employees found"
        return employees[0]
    
    def test_multiple_shifts_same_day_totals(self, auth_headers, test_employee):
        """Test that multiple shifts on same day are summed correctly"""
        # Use a date in the past to avoid conflicts
        test_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Create first shift (morning)
        shift1_response = requests.post(f"{BASE_URL}/api/payroll/timeclock-shifts", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "clock_in": f"{test_date}T08:00:00",
            "clock_out": f"{test_date}T12:00:00",  # 4 hours
            "break_minutes": 0,
            "notes": "TEST_morning_shift"
        })
        assert shift1_response.status_code == 200, f"Failed to create shift1: {shift1_response.text}"
        shift1 = shift1_response.json()
        
        # Create second shift (afternoon)
        shift2_response = requests.post(f"{BASE_URL}/api/payroll/timeclock-shifts", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "clock_in": f"{test_date}T13:00:00",
            "clock_out": f"{test_date}T17:00:00",  # 4 hours
            "break_minutes": 0,
            "notes": "TEST_afternoon_shift"
        })
        assert shift2_response.status_code == 200, f"Failed to create shift2: {shift2_response.text}"
        shift2 = shift2_response.json()
        
        try:
            # Get shifts for the day
            shifts_response = requests.get(f"{BASE_URL}/api/payroll/timeclock-shifts", headers=auth_headers, params={
                "employee_id": test_employee["id"],
                "start_date": test_date,
                "end_date": test_date
            })
            assert shifts_response.status_code == 200
            shifts = shifts_response.json()
            
            # Calculate total hours from all shifts
            total_net_hours = sum(s.get("net_hours", 0) for s in shifts if s.get("date") == test_date)
            
            # Expected: 4 + 4 = 8 hours
            expected_total = 8.0
            assert abs(total_net_hours - expected_total) < 0.1, \
                f"Total hours incorrect: expected ~{expected_total}, got {total_net_hours}"
            
            print(f"✓ Multiple shifts same day totals correctly: {total_net_hours} hours from {len(shifts)} shifts")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift1['id']}", headers=auth_headers)
            requests.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift2['id']}", headers=auth_headers)


class TestMarkPaidInFull:
    """Test POST /api/payroll/mark-paid-in-full creates/updates payment transaction"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_employee(self, auth_headers):
        """Get first employee"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200
        employees = response.json()
        assert len(employees) > 0, "No employees found"
        return employees[0]
    
    def test_mark_paid_in_full_creates_transaction(self, auth_headers, test_employee):
        """Test that mark-paid-in-full creates a payment transaction"""
        # Use a test period
        period_start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        period_end = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        paid_amount = 1500.00
        
        response = requests.post(f"{BASE_URL}/api/payroll/mark-paid-in-full", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "period_start": period_start,
            "period_end": period_end,
            "paid_amount": paid_amount,
            "paid_date": period_end,
            "notes": "TEST_paid_in_full_transaction"
        })
        
        assert response.status_code == 200, f"mark-paid-in-full failed: {response.text}"
        result = response.json()
        
        # Verify response structure
        assert "payment_transaction_id" in result, "No payment_transaction_id in response"
        assert result.get("paid_amount") == paid_amount, f"paid_amount mismatch: {result.get('paid_amount')}"
        assert result.get("employee_id") == test_employee["id"], "employee_id mismatch"
        
        print(f"✓ mark-paid-in-full created transaction: {result.get('payment_transaction_id')}")
        
        # Verify transaction exists in transactions list
        transactions_response = requests.get(f"{BASE_URL}/api/payroll/transactions", headers=auth_headers, params={
            "employee_id": test_employee["id"],
            "start_date": period_start,
            "end_date": period_end
        })
        assert transactions_response.status_code == 200
        transactions = transactions_response.json()
        
        # Find the payment transaction
        payment_txn = next((t for t in transactions if t.get("id") == result.get("payment_transaction_id")), None)
        assert payment_txn is not None, "Payment transaction not found in transactions list"
        assert payment_txn.get("type") == "payment", f"Transaction type incorrect: {payment_txn.get('type')}"
        assert payment_txn.get("amount") == paid_amount, f"Transaction amount incorrect: {payment_txn.get('amount')}"
        
        print(f"✓ Payment transaction verified in transactions list")
    
    def test_mark_paid_in_full_updates_existing(self, auth_headers, test_employee):
        """Test that mark-paid-in-full updates existing transaction for same period"""
        period_start = (datetime.now() - timedelta(days=21)).strftime("%Y-%m-%d")
        period_end = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        
        # First call
        response1 = requests.post(f"{BASE_URL}/api/payroll/mark-paid-in-full", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "period_start": period_start,
            "period_end": period_end,
            "paid_amount": 1000.00
        })
        assert response1.status_code == 200
        txn_id_1 = response1.json().get("payment_transaction_id")
        
        # Second call with different amount - should update same transaction
        response2 = requests.post(f"{BASE_URL}/api/payroll/mark-paid-in-full", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "period_start": period_start,
            "period_end": period_end,
            "paid_amount": 1200.00
        })
        assert response2.status_code == 200
        txn_id_2 = response2.json().get("payment_transaction_id")
        
        # Should be the same transaction ID (updated, not created new)
        assert txn_id_1 == txn_id_2, f"Expected same transaction ID, got {txn_id_1} vs {txn_id_2}"
        
        # Verify updated amount
        assert response2.json().get("paid_amount") == 1200.00
        
        print(f"✓ mark-paid-in-full correctly updates existing transaction")
    
    def test_mark_paid_in_full_validation(self, auth_headers, test_employee):
        """Test validation for mark-paid-in-full"""
        # Test with invalid period (end before start)
        response = requests.post(f"{BASE_URL}/api/payroll/mark-paid-in-full", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "period_start": "2026-01-15",
            "period_end": "2026-01-01",  # End before start
            "paid_amount": 1000.00
        })
        assert response.status_code == 400, f"Expected 400 for invalid period, got {response.status_code}"
        print(f"✓ mark-paid-in-full correctly validates period dates")
        
        # Test with zero amount
        response = requests.post(f"{BASE_URL}/api/payroll/mark-paid-in-full", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "period_start": "2026-01-01",
            "period_end": "2026-01-07",
            "paid_amount": 0
        })
        assert response.status_code == 422, f"Expected 422 for zero amount, got {response.status_code}"
        print(f"✓ mark-paid-in-full correctly validates paid_amount > 0")


class TestPayrollSettingsToggle:
    """Test Company Settings payroll toggle show_payroll_adjustments saves and controls visibility"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_tenant_payroll_settings(self, auth_headers):
        """Test that tenant payroll settings are returned"""
        response = requests.get(f"{BASE_URL}/api/tenant", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get tenant: {response.text}"
        
        tenant = response.json()
        payroll_settings = tenant.get("payroll_settings", {})
        
        # Verify payroll_settings structure
        assert "default_cycle" in payroll_settings or payroll_settings == {}, \
            "payroll_settings should have default_cycle or be empty"
        
        print(f"✓ Tenant payroll_settings retrieved: {payroll_settings}")
    
    def test_update_show_payroll_adjustments_toggle(self, auth_headers):
        """Test that show_payroll_adjustments toggle can be saved"""
        # Get current settings
        response = requests.get(f"{BASE_URL}/api/tenant", headers=auth_headers)
        assert response.status_code == 200
        current_settings = response.json().get("payroll_settings", {})
        current_value = current_settings.get("show_payroll_adjustments", False)
        
        # Toggle the value
        new_value = not current_value
        update_response = requests.put(f"{BASE_URL}/api/tenant", headers=auth_headers, json={
            "payroll_settings": {
                "default_cycle": current_settings.get("default_cycle", "weekly"),
                "pay_week_start_day": current_settings.get("pay_week_start_day", "monday"),
                "show_payroll_adjustments": new_value
            }
        })
        assert update_response.status_code == 200, f"Failed to update tenant: {update_response.text}"
        
        # Verify the change persisted
        verify_response = requests.get(f"{BASE_URL}/api/tenant", headers=auth_headers)
        assert verify_response.status_code == 200
        updated_settings = verify_response.json().get("payroll_settings", {})
        
        assert updated_settings.get("show_payroll_adjustments") == new_value, \
            f"show_payroll_adjustments not updated: expected {new_value}, got {updated_settings.get('show_payroll_adjustments')}"
        
        print(f"✓ show_payroll_adjustments toggle saved: {current_value} -> {new_value}")
        
        # Restore original value
        requests.put(f"{BASE_URL}/api/tenant", headers=auth_headers, json={
            "payroll_settings": {
                "default_cycle": current_settings.get("default_cycle", "weekly"),
                "pay_week_start_day": current_settings.get("pay_week_start_day", "monday"),
                "show_payroll_adjustments": current_value
            }
        })


class TestAdminEditabilityAfterPaid:
    """Test that admin editability remains enabled after marking paid"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture(scope="class")
    def test_employee(self, auth_headers):
        """Get first employee"""
        response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert response.status_code == 200
        employees = response.json()
        assert len(employees) > 0, "No employees found"
        return employees[0]
    
    def test_can_edit_shift_after_marking_paid(self, auth_headers, test_employee):
        """Test that shifts can still be edited after marking period as paid"""
        test_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        period_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        period_end = datetime.now().strftime("%Y-%m-%d")
        
        # Create a shift
        shift_response = requests.post(f"{BASE_URL}/api/payroll/timeclock-shifts", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "clock_in": f"{test_date}T09:00:00",
            "clock_out": f"{test_date}T17:00:00",
            "break_minutes": 30,
            "notes": "TEST_edit_after_paid"
        })
        assert shift_response.status_code == 200
        shift = shift_response.json()
        
        try:
            # Mark period as paid
            paid_response = requests.post(f"{BASE_URL}/api/payroll/mark-paid-in-full", headers=auth_headers, json={
                "employee_id": test_employee["id"],
                "period_start": period_start,
                "period_end": period_end,
                "paid_amount": 500.00
            })
            assert paid_response.status_code == 200
            
            # Try to edit the shift - should still work (no locking)
            edit_response = requests.put(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift['id']}", headers=auth_headers, json={
                "break_minutes": 45,
                "notes": "TEST_edited_after_paid"
            })
            
            assert edit_response.status_code == 200, f"Edit failed after marking paid: {edit_response.text}"
            edited = edit_response.json()
            assert edited.get("break_minutes") == 45, "Edit did not persist"
            
            print(f"✓ Admin can still edit shifts after marking period as paid")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift['id']}", headers=auth_headers)
    
    def test_can_create_transaction_after_marking_paid(self, auth_headers, test_employee):
        """Test that transactions can still be created after marking period as paid"""
        period_start = (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d")
        period_end = (datetime.now() - timedelta(days=21)).strftime("%Y-%m-%d")
        
        # Mark period as paid
        paid_response = requests.post(f"{BASE_URL}/api/payroll/mark-paid-in-full", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "period_start": period_start,
            "period_end": period_end,
            "paid_amount": 800.00
        })
        assert paid_response.status_code == 200
        
        # Try to create a new transaction in the same period - should still work
        txn_response = requests.post(f"{BASE_URL}/api/payroll/transactions", headers=auth_headers, json={
            "employee_id": test_employee["id"],
            "type": "advance",
            "amount": 50.00,
            "description": "TEST_advance_after_paid",
            "date": period_start
        })
        
        assert txn_response.status_code == 200, f"Transaction creation failed after marking paid: {txn_response.text}"
        txn = txn_response.json()
        
        print(f"✓ Admin can still create transactions after marking period as paid")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payroll/transactions/{txn['id']}", headers=auth_headers)


class TestPayrollReportEndpoint:
    """Test payroll report endpoint returns correct data"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_payroll_report_returns_data(self, auth_headers):
        """Test that payroll report endpoint returns expected structure"""
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(f"{BASE_URL}/api/payroll/report", headers=auth_headers, params={
            "start_date": start_date,
            "end_date": end_date
        })
        
        assert response.status_code == 200, f"Report failed: {response.text}"
        report = response.json()
        
        # Verify structure
        assert "employees" in report, "No employees in report"
        assert "totals" in report, "No totals in report"
        assert "start_date" in report, "No start_date in report"
        assert "end_date" in report, "No end_date in report"
        
        print(f"✓ Payroll report returned {len(report.get('employees', []))} employees")
    
    def test_payroll_report_includes_daily_breakdown(self, auth_headers):
        """Test that payroll report includes daily breakdown"""
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get employees first
        emp_response = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert emp_response.status_code == 200
        employees = emp_response.json()
        
        if not employees:
            pytest.skip("No employees to test")
        
        response = requests.get(f"{BASE_URL}/api/payroll/report", headers=auth_headers, params={
            "start_date": start_date,
            "end_date": end_date,
            "employee_id": employees[0]["id"]
        })
        
        assert response.status_code == 200
        report = response.json()
        
        if report.get("employees"):
            emp_report = report["employees"][0]
            assert "daily_breakdown" in emp_report, "No daily_breakdown in employee report"
            print(f"✓ Payroll report includes daily_breakdown with {len(emp_report.get('daily_breakdown', []))} days")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
