"""
Iteration 109 - Timeclock Timezone Bug Fix Tests

Tests the fix for the timezone bug where:
- Clock-in status vanished after UTC midnight for US timezone users
- Status now checks for any open shift (not UTC-today timelogs)
- Action validation uses open shift state
- Today's logs use 36h window

Key changes tested:
1. get_timeclock_status - checks for open shifts first (survives timezone boundary)
2. record_timeclock_action - finds open shifts without date filter
3. get_today_logs - uses 36h window instead of UTC date regex
"""

import pytest
import requests
import os
import time
from datetime import datetime, timezone

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
EMPLOYEE_ID = "18eed187-1a90-4bf8-b233-dc47b44c9579"  # QA Test Employee - Iteration 104


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "signguypa@gmail.com",
        "password": "Billnel323"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestTimeclockStatusFix:
    """Tests for the timezone-safe status checking"""

    def test_01_cleanup_existing_open_shift(self, api_client):
        """End any existing open shift before testing"""
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        
        if status.get("status") in ["working", "on_break"]:
            # End the break first if on break
            if status.get("status") == "on_break":
                break_end_resp = api_client.post(f"{BASE_URL}/api/timeclock", json={
                    "employee_id": EMPLOYEE_ID,
                    "action": "break_end"
                })
                assert break_end_resp.status_code == 200, f"Failed to end break: {break_end_resp.text}"
            
            # End the work
            end_resp = api_client.post(f"{BASE_URL}/api/timeclock", json={
                "employee_id": EMPLOYEE_ID,
                "action": "end_work"
            })
            assert end_resp.status_code == 200, f"Failed to end work: {end_resp.text}"
            
        # Verify status is now finished or not_started
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status.get("status") in ["finished", "not_started"], f"Unexpected status after cleanup: {status}"
        print(f"Cleanup complete. Status: {status}")

    def test_02_clock_in_creates_shift_with_working_status(self, api_client):
        """Clock in should create a timelog and shift with status=working"""
        response = api_client.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": EMPLOYEE_ID,
            "action": "start_work"
        })
        assert response.status_code == 200, f"Clock in failed: {response.text}"
        
        data = response.json()
        assert data.get("action") == "start_work"
        assert data.get("employee_id") == EMPLOYEE_ID
        assert "timestamp" in data
        assert "id" in data
        print(f"Clock in successful: {data}")

    def test_03_status_shows_working_after_clock_in(self, api_client):
        """Status should show 'working' after clock in"""
        response = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        assert response.status_code == 200
        
        status = response.json()
        assert status.get("status") == "working", f"Expected 'working', got: {status}"
        assert status.get("last_action") == "start_work"
        assert "last_timestamp" in status
        print(f"Status after clock in: {status}")

    def test_04_status_persists_after_multiple_checks(self, api_client):
        """Status should persist and not depend on UTC date"""
        # Check status multiple times
        for i in range(3):
            response = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
            assert response.status_code == 200
            status = response.json()
            assert status.get("status") == "working", f"Status check {i+1} failed: {status}"
            time.sleep(0.5)
        print("Status persists correctly across multiple checks")

    def test_05_break_start_changes_status_to_on_break(self, api_client):
        """Starting a break should change status to on_break"""
        response = api_client.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": EMPLOYEE_ID,
            "action": "break_start"
        })
        assert response.status_code == 200, f"Break start failed: {response.text}"
        
        # Verify status
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status.get("status") == "on_break", f"Expected 'on_break', got: {status}"
        print(f"Break started. Status: {status}")

    def test_06_break_end_returns_to_working(self, api_client):
        """Ending a break should return status to working"""
        response = api_client.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": EMPLOYEE_ID,
            "action": "break_end"
        })
        assert response.status_code == 200, f"Break end failed: {response.text}"
        
        # Verify status
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status.get("status") == "working", f"Expected 'working', got: {status}"
        print(f"Break ended. Status: {status}")

    def test_07_clock_out_changes_status_to_finished(self, api_client):
        """Clock out should change status to finished"""
        response = api_client.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": EMPLOYEE_ID,
            "action": "end_work"
        })
        assert response.status_code == 200, f"Clock out failed: {response.text}"
        
        # Verify status
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status.get("status") == "finished", f"Expected 'finished', got: {status}"
        print(f"Clock out successful. Status: {status}")

    def test_08_can_clock_in_again_after_clock_out(self, api_client):
        """Should be able to clock in again after clocking out"""
        response = api_client.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": EMPLOYEE_ID,
            "action": "start_work"
        })
        assert response.status_code == 200, f"Second clock in failed: {response.text}"
        
        # Verify status
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        assert status_resp.status_code == 200
        status = status_resp.json()
        assert status.get("status") == "working", f"Expected 'working', got: {status}"
        print(f"Second clock in successful. Status: {status}")


class TestInvalidSequenceRejection:
    """Tests for invalid action sequence rejection"""

    def test_09_break_end_before_break_start_rejected(self, api_client):
        """break_end should be rejected if not on break"""
        # First ensure we're in working state (not on break)
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        status = status_resp.json()
        
        if status.get("status") == "on_break":
            # End the break first
            api_client.post(f"{BASE_URL}/api/timeclock", json={
                "employee_id": EMPLOYEE_ID,
                "action": "break_end"
            })
        
        # Now try break_end when not on break - should fail
        response = api_client.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": EMPLOYEE_ID,
            "action": "break_end"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"Invalid sequence correctly rejected: {response.json()}")

    def test_10_double_clock_in_rejected(self, api_client):
        """Double clock in should be rejected"""
        # Ensure we're clocked in
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        status = status_resp.json()
        
        if status.get("status") not in ["working", "on_break"]:
            api_client.post(f"{BASE_URL}/api/timeclock", json={
                "employee_id": EMPLOYEE_ID,
                "action": "start_work"
            })
        
        # Try to clock in again - should fail
        response = api_client.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": EMPLOYEE_ID,
            "action": "start_work"
        })
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"Double clock in correctly rejected: {response.json()}")


class TestTodayLogsEndpoint:
    """Tests for the today's logs endpoint (36h window)"""

    def test_11_today_logs_returns_recent_logs(self, api_client):
        """Today's logs should return logs from the 36h window"""
        response = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/today")
        assert response.status_code == 200
        
        logs = response.json()
        assert isinstance(logs, list), f"Expected list, got: {type(logs)}"
        assert len(logs) > 0, "Expected at least one log entry"
        
        # Verify log structure
        for log in logs:
            assert "id" in log
            assert "employee_id" in log
            assert "action" in log
            assert "timestamp" in log
            assert log["employee_id"] == EMPLOYEE_ID
        
        print(f"Today's logs returned {len(logs)} entries")


class TestShiftSummary:
    """Tests for shift summary endpoint"""

    def test_12_shift_summary_returns_correct_data(self, api_client):
        """Shift summary should return work_minutes and net_hours"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        response = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/summary", params={"date": today})
        assert response.status_code == 200
        
        summary = response.json()
        assert "employee_id" in summary
        assert "date" in summary
        assert "work_minutes" in summary
        assert "net_hours" in summary
        assert summary["employee_id"] == EMPLOYEE_ID
        print(f"Shift summary: {summary}")


class TestPayrollIntegration:
    """Tests for payroll-related timeclock features"""

    def test_13_payroll_report_loads_for_date_range(self, api_client):
        """Payroll report should load correctly for a date range"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        response = api_client.get(f"{BASE_URL}/api/payroll/report", params={
            "start_date": today,
            "end_date": today
        })
        assert response.status_code == 200
        
        report = response.json()
        assert "employees" in report
        assert "start_date" in report
        assert "end_date" in report
        print(f"Payroll report loaded with {len(report.get('employees', []))} employees")

    def test_14_payroll_transaction_create_works(self, api_client):
        """Payroll transaction create should work"""
        response = api_client.post(f"{BASE_URL}/api/payroll/transactions", json={
            "employee_id": EMPLOYEE_ID,
            "type": "earnings",
            "amount": 100.00,
            "description": "Test transaction for iteration 109"
        })
        assert response.status_code == 200, f"Transaction create failed: {response.text}"
        
        transaction = response.json()
        assert transaction.get("employee_id") == EMPLOYEE_ID
        assert transaction.get("type") == "earnings"
        assert transaction.get("amount") == 100.00
        print(f"Transaction created: {transaction.get('id')}")

    def test_15_payroll_timeclock_shifts_endpoint(self, api_client):
        """Payroll timeclock shifts endpoint should work"""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        response = api_client.get(f"{BASE_URL}/api/payroll/timeclock-shifts", params={
            "employee_id": EMPLOYEE_ID,
            "start_date": today,
            "end_date": today
        })
        assert response.status_code == 200
        
        shifts = response.json()
        assert isinstance(shifts, list)
        print(f"Timeclock shifts returned {len(shifts)} entries")


class TestCleanup:
    """Cleanup after tests"""

    def test_99_cleanup_end_shift(self, api_client):
        """End any open shift after tests"""
        status_resp = api_client.get(f"{BASE_URL}/api/timeclock/{EMPLOYEE_ID}/status")
        status = status_resp.json()
        
        if status.get("status") == "on_break":
            api_client.post(f"{BASE_URL}/api/timeclock", json={
                "employee_id": EMPLOYEE_ID,
                "action": "break_end"
            })
        
        if status.get("status") in ["working", "on_break"]:
            response = api_client.post(f"{BASE_URL}/api/timeclock", json={
                "employee_id": EMPLOYEE_ID,
                "action": "end_work"
            })
            assert response.status_code == 200
        
        print("Cleanup complete")
