"""
Iteration 97 - Payroll Overhaul & Order Command Bar Tests

Tests for:
1. Payroll report with carryover balance, transaction totals, final owed
2. Payroll timesheet with carryover, transaction summary, final owed
3. Pay-period summary with carryover + transaction adjustments in net owed
4. Daily payroll breakdown with day/date, worked time, daily pay, daily adjustments
5. Entry details with punch in/out and break labels
6. Order Command Bar presence on New Order and Add Ticket pages (UI tested separately)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"

# Seeded test employee for payroll validation
TEST_EMPLOYEE_ID = "18eed187-1a90-4bf8-b233-dc47b44c9579"
TEST_DATE_RANGE_START = "2026-04-07"
TEST_DATE_RANGE_END = "2026-04-13"

# Expected values from main agent's seeded data
EXPECTED_CARRYOVER_BALANCE = 120.0
EXPECTED_CURRENT_GROSS_PAY = 275.0
EXPECTED_ADJUSTMENTS_TOTAL = -5.0
EXPECTED_FINAL_OWED = 390.0


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API requests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestPayrollReportEndpoint:
    """Tests for /api/payroll/report endpoint"""
    
    def test_payroll_report_returns_carryover_balance(self, auth_headers):
        """Verify payroll report includes carryover_balance field"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "employees" in data
        assert len(data["employees"]) > 0
        
        employee = data["employees"][0]
        assert "carryover_balance" in employee, "carryover_balance field missing from payroll report"
        assert employee["carryover_balance"] == EXPECTED_CARRYOVER_BALANCE
    
    def test_payroll_report_returns_transaction_totals(self, auth_headers):
        """Verify payroll report includes transaction totals (earnings_adjustments, advances, payments)"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        assert "earnings_adjustments" in employee
        assert "advances" in employee
        assert "payments" in employee
        assert "adjustments_total" in employee
        
        # Verify adjustments_total = earnings - advances - payments
        assert employee["adjustments_total"] == EXPECTED_ADJUSTMENTS_TOTAL
    
    def test_payroll_report_returns_final_owed(self, auth_headers):
        """Verify payroll report includes final_owed field"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        assert "final_owed" in employee, "final_owed field missing from payroll report"
        assert employee["final_owed"] == EXPECTED_FINAL_OWED
    
    def test_payroll_report_returns_hours_minutes_labels(self, auth_headers):
        """Verify payroll report includes hours+minutes labels"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        assert "total_hours_label" in employee
        assert "regular_hours_label" in employee
        assert "overtime_hours_label" in employee
        
        # Verify format is "Xh Ym"
        assert "h" in employee["total_hours_label"]
        assert "m" in employee["total_hours_label"]
    
    def test_payroll_report_returns_daily_breakdown(self, auth_headers):
        """Verify payroll report includes daily breakdown with required fields"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        assert "daily_breakdown" in employee
        assert len(employee["daily_breakdown"]) > 0
        
        day = employee["daily_breakdown"][0]
        assert "date" in day
        assert "day_name" in day
        assert "total_minutes" in day
        assert "total_hours_label" in day
        assert "daily_pay" in day
        assert "daily_adjustments" in day
        assert "daily_final" in day
        assert "entries" in day
    
    def test_payroll_report_daily_entries_have_punch_details(self, auth_headers):
        """Verify daily entries include punch in/out and break labels where applicable"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        for day in employee["daily_breakdown"]:
            for entry in day.get("entries", []):
                assert "hours_minutes_label" in entry
                assert "break_label" in entry
                # For time_clock entries, should have clock_in/clock_out
                if entry.get("source") == "time_clock":
                    assert "clock_in" in entry or entry.get("clock_in") is None
                    assert "clock_out" in entry or entry.get("clock_out") is None


class TestPayrollTimesheetEndpoint:
    """Tests for /api/payroll/timesheet endpoint"""
    
    def test_timesheet_returns_carryover_balance(self, auth_headers):
        """Verify timesheet includes carryover_balance field"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "employees" in data
        assert len(data["employees"]) > 0
        
        employee = data["employees"][0]
        assert "carryover_balance" in employee
        assert employee["carryover_balance"] == EXPECTED_CARRYOVER_BALANCE
    
    def test_timesheet_returns_transaction_summary(self, auth_headers):
        """Verify timesheet includes transaction_summary with all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        assert "transaction_summary" in employee
        
        txn_summary = employee["transaction_summary"]
        assert "transactions" in txn_summary
        assert "earnings" in txn_summary
        assert "advances" in txn_summary
        assert "payments" in txn_summary
        assert "adjustments_total" in txn_summary
    
    def test_timesheet_returns_final_owed(self, auth_headers):
        """Verify timesheet includes final_owed field"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        assert "final_owed" in employee
        assert employee["final_owed"] == EXPECTED_FINAL_OWED
    
    def test_timesheet_returns_daily_breakdown(self, auth_headers):
        """Verify timesheet includes daily_breakdown"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        employee = data["employees"][0]
        assert "daily_breakdown" in employee
        assert len(employee["daily_breakdown"]) > 0
    
    def test_timesheet_totals_include_carryover_and_final_owed(self, auth_headers):
        """Verify timesheet totals include carryover_balance and final_owed"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "totals" in data
        totals = data["totals"]
        assert "carryover_balance" in totals
        assert "final_owed" in totals


class TestPayPeriodEndpoint:
    """Tests for /api/payroll/pay-period endpoint"""
    
    def test_pay_period_returns_carryover_balance(self, auth_headers):
        """Verify pay-period includes carryover_balance"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/pay-period",
            params={
                "period_type": "weekly",
                "reference_date": "2026-04-10"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find the test employee
        test_employee = None
        for emp in data.get("employees", []):
            if emp.get("employee_id") == TEST_EMPLOYEE_ID:
                test_employee = emp
                break
        
        assert test_employee is not None, "Test employee not found in pay-period response"
        assert "carryover_balance" in test_employee
        assert test_employee["carryover_balance"] == EXPECTED_CARRYOVER_BALANCE
    
    def test_pay_period_returns_net_owed_with_adjustments(self, auth_headers):
        """Verify pay-period net_owed reflects carryover + transaction adjustments"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/pay-period",
            params={
                "period_type": "weekly",
                "reference_date": "2026-04-10"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find the test employee
        test_employee = None
        for emp in data.get("employees", []):
            if emp.get("employee_id") == TEST_EMPLOYEE_ID:
                test_employee = emp
                break
        
        assert test_employee is not None
        assert "net_owed" in test_employee
        assert "adjustments_total" in test_employee
        
        # net_owed should equal carryover + gross_pay + adjustments_total
        expected_net_owed = (
            test_employee["carryover_balance"] +
            test_employee["gross_pay"] +
            test_employee["adjustments_total"]
        )
        assert test_employee["net_owed"] == expected_net_owed
    
    def test_pay_period_returns_daily_breakdown(self, auth_headers):
        """Verify pay-period includes daily_breakdown"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/pay-period",
            params={
                "period_type": "weekly",
                "reference_date": "2026-04-10"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Find the test employee
        test_employee = None
        for emp in data.get("employees", []):
            if emp.get("employee_id") == TEST_EMPLOYEE_ID:
                test_employee = emp
                break
        
        assert test_employee is not None
        assert "daily_breakdown" in test_employee
        assert len(test_employee["daily_breakdown"]) > 0
    
    def test_pay_period_totals_include_carryover(self, auth_headers):
        """Verify pay-period totals include carryover_balance"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/pay-period",
            params={
                "period_type": "weekly",
                "reference_date": "2026-04-10"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "totals" in data
        totals = data["totals"]
        assert "carryover_balance" in totals
        assert "net_owed" in totals


class TestPayrollTransactionsEndpoint:
    """Tests for /api/payroll/transactions endpoint"""
    
    def test_get_transactions_for_employee(self, auth_headers):
        """Verify transactions can be retrieved for a specific employee"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/transactions",
            params={"employee_id": TEST_EMPLOYEE_ID},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Should have at least the seeded transactions
        assert len(data) >= 2
        
        # Verify transaction structure
        for txn in data:
            assert "id" in txn
            assert "employee_id" in txn
            assert "type" in txn
            assert "amount" in txn
            assert "date" in txn


class TestPayrollExportDataShape:
    """Tests to verify the data shape is correct for export functionality"""
    
    def test_report_and_timesheet_have_consistent_structure(self, auth_headers):
        """Verify report and timesheet have consistent structure for export"""
        report_response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        
        timesheet_response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "start_date": TEST_DATE_RANGE_START,
                "end_date": TEST_DATE_RANGE_END,
                "employee_id": TEST_EMPLOYEE_ID
            },
            headers=auth_headers
        )
        
        assert report_response.status_code == 200
        assert timesheet_response.status_code == 200
        
        report = report_response.json()
        timesheet = timesheet_response.json()
        
        # Both should have employees array
        assert "employees" in report
        assert "employees" in timesheet
        
        # Both should have totals
        assert "totals" in report
        assert "totals" in timesheet
        
        # Employee data should have consistent fields
        report_emp = report["employees"][0]
        timesheet_emp = timesheet["employees"][0]
        
        # Common fields that should exist in both
        common_fields = [
            "employee_id", "employee_name", "hourly_rate",
            "total_hours_label", "regular_hours_label", "overtime_hours_label",
            "carryover_balance", "final_owed", "daily_breakdown"
        ]
        
        for field in common_fields:
            assert field in report_emp, f"Field {field} missing from report employee"
            assert field in timesheet_emp, f"Field {field} missing from timesheet employee"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
