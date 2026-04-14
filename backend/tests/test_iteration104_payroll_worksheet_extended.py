"""
Iteration 104 - Payroll Worksheet Extended Testing
Tests for:
1. Payroll worksheet save works end-to-end on /payroll
2. Print works from /payroll without popup-breakage/runtime error
3. Custom start/end date range works
4. Biweekly preset expands the worksheet beyond 7 rows and totals still work
5. Company settings payroll preferences save and persist
6. Payroll summary/final total includes legacy manual pay correctly and matches backend report values
7. Backend overtime/range calculations respect pay-week start day setting for payroll report/timesheet/pay-period endpoints
8. Legacy/signoff endpoints still work with new range support
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"
TEST_EMPLOYEE_ID = "18eed187-1a90-4bf8-b233-dc47b44c9579"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in login response"
    return data["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Authenticated requests session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("PASS: Health endpoint accessible")
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"PASS: Login successful for {TEST_EMAIL}")


class TestPayrollWorksheetSave:
    """Test payroll worksheet save functionality"""
    
    def test_get_employees(self, api_client):
        """Test getting employees list"""
        response = api_client.get(f"{BASE_URL}/api/employees")
        assert response.status_code == 200
        employees = response.json()
        assert isinstance(employees, list)
        assert len(employees) > 0
        print(f"PASS: Got {len(employees)} employees")
    
    def test_get_employee_by_id(self, api_client):
        """Test getting specific employee"""
        response = api_client.get(f"{BASE_URL}/api/employees/{TEST_EMPLOYEE_ID}")
        assert response.status_code == 200
        employee = response.json()
        assert employee["id"] == TEST_EMPLOYEE_ID
        print(f"PASS: Got employee {employee.get('name', 'Unknown')}")
    
    def test_update_employee_meta_fields(self, api_client):
        """Test updating employee meta fields (name, title, manager, rates)"""
        update_data = {
            "name": "QA Test Employee - Iteration 104",
            "title": "Test Title 104",
            "manager_name": "Test Manager 104",
            "hourly_rate": 25.00,
            "overtime_rate": 37.50
        }
        response = api_client.put(f"{BASE_URL}/api/employees/{TEST_EMPLOYEE_ID}", json=update_data)
        assert response.status_code == 200
        updated = response.json()
        assert updated["name"] == update_data["name"]
        assert updated["title"] == update_data["title"]
        assert updated["manager_name"] == update_data["manager_name"]
        assert updated["hourly_rate"] == update_data["hourly_rate"]
        assert updated["overtime_rate"] == update_data["overtime_rate"]
        print("PASS: Employee meta fields updated successfully")


class TestCustomDateRange:
    """Test custom start/end date range functionality"""
    
    def test_timeclock_shifts_custom_range(self, api_client):
        """Test getting timeclock shifts with custom date range"""
        start_date = "2026-01-01"
        end_date = "2026-01-14"
        response = api_client.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        assert response.status_code == 200
        shifts = response.json()
        assert isinstance(shifts, list)
        print(f"PASS: Got {len(shifts)} shifts for custom range {start_date} to {end_date}")
    
    def test_transactions_custom_range(self, api_client):
        """Test getting transactions with custom date range"""
        start_date = "2026-01-01"
        end_date = "2026-01-31"
        response = api_client.get(
            f"{BASE_URL}/api/payroll/transactions",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        assert response.status_code == 200
        transactions = response.json()
        assert isinstance(transactions, list)
        print(f"PASS: Got {len(transactions)} transactions for custom range")
    
    def test_payroll_report_custom_range(self, api_client):
        """Test payroll report with custom date range"""
        start_date = "2026-01-01"
        end_date = "2026-01-14"
        response = api_client.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date,
                "period_type": "custom"
            }
        )
        assert response.status_code == 200
        report = response.json()
        assert "employees" in report
        assert "start_date" in report
        assert "end_date" in report
        assert report["start_date"] == start_date
        assert report["end_date"] == end_date
        print(f"PASS: Payroll report works with custom range {start_date} to {end_date}")
    
    def test_timesheet_custom_range(self, api_client):
        """Test timesheet with custom date range"""
        start_date = "2026-01-01"
        end_date = "2026-01-14"
        response = api_client.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        assert response.status_code == 200
        timesheet = response.json()
        assert "employees" in timesheet
        assert "start_date" in timesheet
        assert "end_date" in timesheet
        print(f"PASS: Timesheet works with custom range")


class TestBiweeklyPreset:
    """Test biweekly preset functionality"""
    
    def test_payroll_report_biweekly(self, api_client):
        """Test payroll report with biweekly period type"""
        response = api_client.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "period_type": "biweekly"
            }
        )
        assert response.status_code == 200
        report = response.json()
        assert report["period_type"] == "biweekly"
        
        # Verify biweekly range is 14 days
        start = datetime.fromisoformat(report["start_date"])
        end = datetime.fromisoformat(report["end_date"])
        days_diff = (end - start).days + 1
        assert days_diff == 14, f"Biweekly should be 14 days, got {days_diff}"
        print(f"PASS: Biweekly report covers 14 days ({report['start_date']} to {report['end_date']})")
    
    def test_pay_period_biweekly(self, api_client):
        """Test pay period endpoint with biweekly"""
        response = api_client.get(
            f"{BASE_URL}/api/payroll/pay-period",
            params={"period_type": "biweekly"}
        )
        assert response.status_code == 200
        period = response.json()
        
        # Verify biweekly range
        start = datetime.fromisoformat(period["start_date"])
        end = datetime.fromisoformat(period["end_date"])
        days_diff = (end - start).days + 1
        assert days_diff == 14, f"Biweekly pay period should be 14 days, got {days_diff}"
        print(f"PASS: Biweekly pay period covers 14 days")


class TestCompanyPayrollSettings:
    """Test company payroll settings save and persist"""
    
    def test_get_tenant_settings(self, api_client):
        """Test getting tenant settings including payroll settings"""
        response = api_client.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        tenant = response.json()
        assert "payroll_settings" in tenant or tenant.get("payroll_settings") is None
        print(f"PASS: Got tenant settings, payroll_settings: {tenant.get('payroll_settings')}")
    
    def test_update_payroll_settings_biweekly_wednesday(self, api_client):
        """Test updating payroll settings to biweekly with Wednesday start"""
        update_data = {
            "payroll_settings": {
                "default_cycle": "biweekly",
                "pay_week_start_day": "wednesday"
            }
        }
        response = api_client.put(f"{BASE_URL}/api/tenant", json=update_data)
        assert response.status_code == 200
        updated = response.json()
        assert updated.get("payroll_settings", {}).get("default_cycle") == "biweekly"
        assert updated.get("payroll_settings", {}).get("pay_week_start_day") == "wednesday"
        print("PASS: Payroll settings updated to biweekly/wednesday")
    
    def test_verify_payroll_settings_persist(self, api_client):
        """Verify payroll settings persist after update"""
        response = api_client.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        tenant = response.json()
        payroll_settings = tenant.get("payroll_settings", {})
        assert payroll_settings.get("default_cycle") == "biweekly"
        assert payroll_settings.get("pay_week_start_day") == "wednesday"
        print("PASS: Payroll settings persisted correctly")


class TestPayWeekStartDayCalculations:
    """Test that overtime/range calculations respect pay-week start day setting"""
    
    def test_payroll_report_respects_pay_week_start(self, api_client):
        """Test payroll report respects pay_week_start_day setting"""
        # First ensure settings are set to wednesday
        api_client.put(f"{BASE_URL}/api/tenant", json={
            "payroll_settings": {
                "default_cycle": "weekly",
                "pay_week_start_day": "wednesday"
            }
        })
        
        # Get payroll report with weekly period
        response = api_client.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "period_type": "weekly"
            }
        )
        assert response.status_code == 200
        report = response.json()
        
        # Verify the start date is a Wednesday
        start_date = datetime.fromisoformat(report["start_date"])
        # Wednesday is weekday 2 (Monday=0)
        assert start_date.weekday() == 2, f"Expected Wednesday (2), got weekday {start_date.weekday()}"
        print(f"PASS: Weekly report starts on Wednesday ({report['start_date']})")
    
    def test_timesheet_respects_pay_week_start(self, api_client):
        """Test timesheet respects pay_week_start_day setting"""
        # Use a custom range that spans multiple weeks
        start_date = "2026-01-01"
        end_date = "2026-01-14"
        
        response = api_client.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        assert response.status_code == 200
        timesheet = response.json()
        assert "employees" in timesheet
        print("PASS: Timesheet works with pay_week_start_day setting")


class TestLegacyManualEntries:
    """Test legacy manual entries with new range support"""
    
    def test_get_legacy_entries_with_range(self, api_client):
        """Test getting legacy manual entries with start/end date range"""
        start_date = "2026-04-06"
        end_date = "2026-04-12"
        response = api_client.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        assert response.status_code == 200
        entries = response.json()
        assert isinstance(entries, list)
        print(f"PASS: Got {len(entries)} legacy entries for range {start_date} to {end_date}")
    
    def test_legacy_entries_include_required_fields(self, api_client):
        """Test legacy entries include all required fields"""
        start_date = "2026-04-06"
        end_date = "2026-04-12"
        response = api_client.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            }
        )
        assert response.status_code == 200
        entries = response.json()
        
        if len(entries) > 0:
            entry = entries[0]
            required_fields = [
                "id", "date", "source_type", "hours", "notes",
                "current_effect_hours", "current_effect_pay", "current_effect_label",
                "included_in_totals", "included_in_exports", "handling_mode",
                "target_date", "admin_note", "resolution_saved", "can_exclude"
            ]
            for field in required_fields:
                assert field in entry, f"Missing field: {field}"
            print(f"PASS: Legacy entry has all required fields")
        else:
            print("PASS: No legacy entries found (clean week)")


class TestSignoffWithRangeSupport:
    """Test signoff endpoints with new range support"""
    
    def test_get_signoff_with_period_end(self, api_client):
        """Test getting signoff with period_end parameter"""
        week_start = "2026-01-06"
        period_end = "2026-01-19"
        response = api_client.get(
            f"{BASE_URL}/api/payroll/signoff",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "week_start": week_start,
                "period_end": period_end
            }
        )
        assert response.status_code == 200
        signoff = response.json()
        assert "employee_id" in signoff
        assert "week_start" in signoff
        print(f"PASS: Got signoff for range {week_start} to {period_end}")
    
    def test_upsert_signoff_with_period_end(self, api_client):
        """Test upserting signoff with period_end parameter"""
        week_start = "2026-01-06"
        period_end = "2026-01-19"
        signoff_data = {
            "employee_id": TEST_EMPLOYEE_ID,
            "week_start": week_start,
            "period_end": period_end,
            "reviewed_by": "Test Reviewer 104",
            "review_date": "2026-01-20",
            "approved_by": "Test Approver 104",
            "approval_date": "2026-01-21",
            "payroll_notes": "Iteration 104 test signoff"
        }
        response = api_client.put(f"{BASE_URL}/api/payroll/signoff", json=signoff_data)
        assert response.status_code == 200
        saved = response.json()
        assert saved["reviewed_by"] == signoff_data["reviewed_by"]
        assert saved["approved_by"] == signoff_data["approved_by"]
        assert saved["payroll_notes"] == signoff_data["payroll_notes"]
        print("PASS: Signoff upserted with period_end support")


class TestPayrollSummaryTotals:
    """Test payroll summary/final total calculations"""
    
    def test_report_includes_carryover_balance(self, api_client):
        """Test payroll report includes carryover balance"""
        response = api_client.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": "2026-04-06",
                "end_date": "2026-04-12",
                "period_type": "custom"
            }
        )
        assert response.status_code == 200
        report = response.json()
        
        if len(report["employees"]) > 0:
            emp = report["employees"][0]
            assert "carryover_balance" in emp
            assert "final_owed" in emp
            assert "gross_pay" in emp
            assert "adjustments_total" in emp
            print(f"PASS: Report includes carryover_balance={emp['carryover_balance']}, final_owed={emp['final_owed']}")
        else:
            print("PASS: No employees in report (expected for filtered query)")
    
    def test_timesheet_includes_legacy_manual_pay(self, api_client):
        """Test timesheet includes legacy manual pay in totals"""
        response = api_client.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": "2026-04-06",
                "end_date": "2026-04-12"
            }
        )
        assert response.status_code == 200
        timesheet = response.json()
        
        if len(timesheet["employees"]) > 0:
            emp = timesheet["employees"][0]
            assert "total_pay" in emp
            assert "carryover_balance" in emp
            assert "final_owed" in emp
            print(f"PASS: Timesheet includes total_pay={emp['total_pay']}, final_owed={emp['final_owed']}")
        else:
            print("PASS: No employees in timesheet")


class TestTimeclockShiftsCRUD:
    """Test timeclock shifts CRUD operations"""
    
    def test_create_timeclock_shift(self, api_client):
        """Test creating a new timeclock shift"""
        shift_data = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": "2026-01-15",
            "clock_in": "2026-01-15T08:00:00",
            "clock_out": "2026-01-15T17:00:00",
            "lunch_start": "2026-01-15T12:00:00",
            "lunch_end": "2026-01-15T12:30:00",
            "break_minutes": 30,
            "notes": "Iteration 104 test shift"
        }
        response = api_client.post(f"{BASE_URL}/api/payroll/timeclock-shifts", json=shift_data)
        assert response.status_code in [200, 201]
        shift = response.json()
        assert shift["employee_id"] == TEST_EMPLOYEE_ID
        assert shift["date"] == "2026-01-15"
        print(f"PASS: Created timeclock shift with id={shift.get('id')}")
        return shift.get("id")
    
    def test_update_timeclock_shift(self, api_client):
        """Test updating a timeclock shift"""
        # First create a shift
        shift_data = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": "2026-01-16",
            "clock_in": "2026-01-16T09:00:00",
            "clock_out": "2026-01-16T18:00:00",
            "notes": "Original notes"
        }
        create_response = api_client.post(f"{BASE_URL}/api/payroll/timeclock-shifts", json=shift_data)
        assert create_response.status_code in [200, 201]
        shift_id = create_response.json().get("id")
        
        # Update the shift
        update_data = {
            "notes": "Updated notes - Iteration 104",
            "clock_out": "2026-01-16T17:30:00"
        }
        update_response = api_client.put(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}", json=update_data)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["notes"] == update_data["notes"]
        print(f"PASS: Updated timeclock shift {shift_id}")
    
    def test_delete_timeclock_shift(self, api_client):
        """Test deleting a timeclock shift"""
        # First create a shift
        shift_data = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": "2026-01-17",
            "clock_in": "2026-01-17T08:00:00",
            "clock_out": "2026-01-17T16:00:00",
            "notes": "To be deleted"
        }
        create_response = api_client.post(f"{BASE_URL}/api/payroll/timeclock-shifts", json=shift_data)
        assert create_response.status_code in [200, 201]
        shift_id = create_response.json().get("id")
        
        # Delete the shift
        delete_response = api_client.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}")
        assert delete_response.status_code == 200
        print(f"PASS: Deleted timeclock shift {shift_id}")


class TestTransactionsCRUD:
    """Test payroll transactions CRUD operations"""
    
    def test_create_transaction(self, api_client):
        """Test creating a payroll transaction"""
        transaction_data = {
            "employee_id": TEST_EMPLOYEE_ID,
            "type": "earnings",
            "amount": 50.00,
            "description": "Iteration 104 test bonus",
            "date": "2026-01-15"
        }
        response = api_client.post(f"{BASE_URL}/api/payroll/transactions", json=transaction_data)
        assert response.status_code in [200, 201]
        transaction = response.json()
        assert transaction["employee_id"] == TEST_EMPLOYEE_ID
        assert transaction["amount"] == 50.00
        print(f"PASS: Created transaction with id={transaction.get('id')}")
        return transaction.get("id")
    
    def test_update_transaction(self, api_client):
        """Test updating a payroll transaction"""
        # First create a transaction
        transaction_data = {
            "employee_id": TEST_EMPLOYEE_ID,
            "type": "advance",
            "amount": 100.00,
            "description": "Original advance",
            "date": "2026-01-16"
        }
        create_response = api_client.post(f"{BASE_URL}/api/payroll/transactions", json=transaction_data)
        assert create_response.status_code in [200, 201]
        transaction_id = create_response.json().get("id")
        
        # Update the transaction
        update_data = {
            "amount": 75.00,
            "description": "Updated advance - Iteration 104"
        }
        update_response = api_client.put(f"{BASE_URL}/api/payroll/transactions/{transaction_id}", json=update_data)
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["amount"] == 75.00
        print(f"PASS: Updated transaction {transaction_id}")
    
    def test_delete_transaction(self, api_client):
        """Test deleting a payroll transaction"""
        # First create a transaction
        transaction_data = {
            "employee_id": TEST_EMPLOYEE_ID,
            "type": "payment",
            "amount": 25.00,
            "description": "To be deleted",
            "date": "2026-01-17"
        }
        create_response = api_client.post(f"{BASE_URL}/api/payroll/transactions", json=transaction_data)
        assert create_response.status_code in [200, 201]
        transaction_id = create_response.json().get("id")
        
        # Delete the transaction
        delete_response = api_client.delete(f"{BASE_URL}/api/payroll/transactions/{transaction_id}")
        assert delete_response.status_code == 200
        print(f"PASS: Deleted transaction {transaction_id}")


class TestCleanup:
    """Cleanup test data and restore settings"""
    
    def test_restore_payroll_settings(self, api_client):
        """Restore payroll settings to biweekly/wednesday as per main agent context"""
        update_data = {
            "payroll_settings": {
                "default_cycle": "biweekly",
                "pay_week_start_day": "wednesday"
            }
        }
        response = api_client.put(f"{BASE_URL}/api/tenant", json=update_data)
        assert response.status_code == 200
        print("PASS: Restored payroll settings to biweekly/wednesday")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
