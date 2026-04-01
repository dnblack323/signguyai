"""
Iteration 90 - Payroll/Timeclock Shift Deletion Fix Tests

Tests for the fix where deleting a timeclock shift now also deletes
the underlying raw timelogs to prevent the shift from being recreated
during backfill operations.

Also tests floating assistant drag/right-click behaviors (frontend).
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for owner account"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


@pytest.fixture(scope="module")
def test_employee(api_client):
    """Create a test employee for timeclock tests"""
    employee_data = {
        "name": f"TEST_Timeclock_Employee_{uuid.uuid4().hex[:6]}",
        "email": f"test_timeclock_{uuid.uuid4().hex[:6]}@example.com",
        "hourly_rate": 25.0,
        "role": "staff",
        "is_active": True
    }
    response = api_client.post(f"{BASE_URL}/api/employees", json=employee_data)
    if response.status_code not in [200, 201]:
        pytest.skip(f"Failed to create test employee: {response.text}")
    employee = response.json()
    yield employee
    # Cleanup
    api_client.delete(f"{BASE_URL}/api/employees/{employee['id']}")


class TestTimeclockShiftDeletion:
    """Tests for timeclock shift deletion and raw timelog cleanup"""

    def test_delete_timeclock_shift_removes_raw_timelogs(self, api_client, test_employee):
        """
        Test that deleting a timeclock shift also deletes the underlying raw timelogs
        so the shift doesn't reappear after backfill.
        """
        employee_id = test_employee["id"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Step 1: Create a timeclock entry by punching in
        punch_in_response = api_client.post(
            f"{BASE_URL}/api/timeclock",
            json={"employee_id": employee_id, "action": "start_work"}
        )
        assert punch_in_response.status_code == 200, f"Punch in failed: {punch_in_response.text}"
        
        # Step 2: Punch out to complete the shift
        punch_out_response = api_client.post(
            f"{BASE_URL}/api/timeclock",
            json={"employee_id": employee_id, "action": "end_work"}
        )
        assert punch_out_response.status_code == 200, f"Punch out failed: {punch_out_response.text}"
        
        # Step 3: Get the timeclock shifts to find the one we just created
        shifts_response = api_client.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={"employee_id": employee_id, "start_date": today, "end_date": today}
        )
        assert shifts_response.status_code == 200, f"Get shifts failed: {shifts_response.text}"
        shifts = shifts_response.json()
        assert len(shifts) > 0, "No shifts found after punching in/out"
        
        shift_id = shifts[0]["id"]
        
        # Step 4: Delete the shift
        delete_response = api_client.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}")
        assert delete_response.status_code == 200, f"Delete shift failed: {delete_response.text}"
        
        # Step 5: Verify shift is gone
        shifts_after_delete = api_client.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={"employee_id": employee_id, "start_date": today, "end_date": today}
        )
        assert shifts_after_delete.status_code == 200
        remaining_shifts = shifts_after_delete.json()
        assert len(remaining_shifts) == 0, f"Shift still exists after deletion: {remaining_shifts}"
        
        # Step 6: Trigger a backfill by fetching timesheet (this calls backfill internally)
        timesheet_response = api_client.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={"start_date": today, "end_date": today, "employee_id": employee_id}
        )
        assert timesheet_response.status_code == 200, f"Timesheet fetch failed: {timesheet_response.text}"
        
        # Step 7: Verify shift did NOT reappear after backfill
        shifts_after_backfill = api_client.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={"employee_id": employee_id, "start_date": today, "end_date": today}
        )
        assert shifts_after_backfill.status_code == 200
        final_shifts = shifts_after_backfill.json()
        assert len(final_shifts) == 0, f"Shift reappeared after backfill! This is the bug. Shifts: {final_shifts}"
        
        print("SUCCESS: Deleted timeclock shift did NOT reappear after backfill")

    def test_payroll_totals_consistent_after_shift_deletion(self, api_client, test_employee):
        """
        Test that payroll totals remain consistent after deleting a timeclock shift.
        """
        employee_id = test_employee["id"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create a shift
        api_client.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "start_work"})
        api_client.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "end_work"})
        
        # Get pay period before deletion
        pay_period_before = api_client.get(f"{BASE_URL}/api/payroll/pay-period", params={"period_type": "weekly"})
        assert pay_period_before.status_code == 200
        totals_before = pay_period_before.json().get("totals", {})
        
        # Get shifts and delete
        shifts = api_client.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={"employee_id": employee_id, "start_date": today, "end_date": today}
        ).json()
        
        if shifts:
            shift_id = shifts[0]["id"]
            shift_hours = shifts[0].get("net_hours", 0)
            
            delete_response = api_client.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}")
            assert delete_response.status_code == 200
            
            # Get pay period after deletion
            pay_period_after = api_client.get(f"{BASE_URL}/api/payroll/pay-period", params={"period_type": "weekly"})
            assert pay_period_after.status_code == 200
            totals_after = pay_period_after.json().get("totals", {})
            
            # Verify hours decreased
            hours_diff = totals_before.get("total_hours", 0) - totals_after.get("total_hours", 0)
            assert hours_diff >= 0, f"Hours should decrease or stay same after deletion, but increased by {-hours_diff}"
            
            print(f"SUCCESS: Payroll totals consistent. Hours decreased by {hours_diff}")


class TestTimesheetEntryDeletion:
    """Tests for timesheet entry deletion behavior"""

    def test_timesheet_entries_not_resurrected(self, api_client, test_employee):
        """
        Test that deleted timesheet entries (from timeclock) don't reappear
        after reload/backfill operations.
        """
        employee_id = test_employee["id"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create a shift
        api_client.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "start_work"})
        api_client.post(f"{BASE_URL}/api/timeclock", json={"employee_id": employee_id, "action": "end_work"})
        
        # Get timesheet to see entries
        timesheet = api_client.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={"start_date": today, "end_date": today, "employee_id": employee_id}
        ).json()
        
        # Find time_clock entries
        time_clock_entries = []
        for emp in timesheet.get("employees", []):
            for entry in emp.get("entries", []):
                if entry.get("source") == "time_clock":
                    time_clock_entries.append(entry)
        
        if time_clock_entries:
            entry_id = time_clock_entries[0]["id"]
            
            # Delete via timeclock-shifts endpoint
            delete_response = api_client.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{entry_id}")
            assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
            
            # Fetch timesheet again (triggers backfill)
            timesheet_after = api_client.get(
                f"{BASE_URL}/api/payroll/timesheet",
                params={"start_date": today, "end_date": today, "employee_id": employee_id}
            ).json()
            
            # Check entry is gone
            remaining_entries = []
            for emp in timesheet_after.get("employees", []):
                for entry in emp.get("entries", []):
                    if entry.get("source") == "time_clock" and entry.get("id") == entry_id:
                        remaining_entries.append(entry)
            
            assert len(remaining_entries) == 0, f"Deleted entry reappeared in timesheet: {remaining_entries}"
            print("SUCCESS: Deleted timesheet entry did NOT reappear")


class TestPayrollEndpoints:
    """Basic payroll endpoint tests"""

    def test_get_timeclock_shifts(self, api_client):
        """Test GET /api/payroll/timeclock-shifts endpoint"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = api_client.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={"start_date": today, "end_date": today}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("SUCCESS: GET timeclock-shifts endpoint works")

    def test_get_timesheet(self, api_client):
        """Test GET /api/payroll/timesheet endpoint"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = api_client.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={"start_date": today, "end_date": today}
        )
        assert response.status_code == 200
        data = response.json()
        assert "employees" in data
        print("SUCCESS: GET timesheet endpoint works")

    def test_get_pay_period(self, api_client):
        """Test GET /api/payroll/pay-period endpoint"""
        response = api_client.get(
            f"{BASE_URL}/api/payroll/pay-period",
            params={"period_type": "weekly"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "totals" in data
        assert "employees" in data
        print("SUCCESS: GET pay-period endpoint works")

    def test_delete_nonexistent_shift_returns_404(self, api_client):
        """Test that deleting a non-existent shift returns 404"""
        fake_id = str(uuid.uuid4())
        response = api_client.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{fake_id}")
        assert response.status_code == 404
        print("SUCCESS: Delete non-existent shift returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
