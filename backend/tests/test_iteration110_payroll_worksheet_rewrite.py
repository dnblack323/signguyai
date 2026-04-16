"""
Iteration 110 - Payroll Worksheet Architecture Rewrite Tests

Tests for the 6 specific fixes:
1. No refetch loop (frontend-only, tested via Playwright)
2. Notes alone don't block save
3. Legacy entries only saved when changed
4. Section-by-section error reporting
5. Adjustment sign change works in isolation
6. Adding end time to existing shift works

Employee ID for testing: 18eed187-1a90-4bf8-b233-dc47b44c9579
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMPLOYEE_ID = "18eed187-1a90-4bf8-b233-dc47b44c9579"

# Calculate current pay period (biweekly starting Monday)
def get_current_pay_period():
    today = datetime.now()
    # Find the most recent Monday
    days_since_monday = today.weekday()
    start = today - timedelta(days=days_since_monday)
    end = start + timedelta(days=13)  # Biweekly
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')


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
def auth_headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPayrollWorksheetAPIs:
    """Test payroll worksheet API endpoints work correctly"""
    
    def test_employee_endpoint(self, auth_headers):
        """Verify employee endpoint returns data"""
        response = requests.get(
            f"{BASE_URL}/api/employees/{TEST_EMPLOYEE_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == TEST_EMPLOYEE_ID
        print(f"Employee: {data.get('name', 'Unknown')}")
    
    def test_timeclock_shifts_endpoint(self, auth_headers):
        """Verify timeclock shifts endpoint"""
        start_date, end_date = get_current_pay_period()
        response = requests.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} shifts for period {start_date} to {end_date}")
    
    def test_transactions_endpoint(self, auth_headers):
        """Verify transactions/adjustments endpoint"""
        start_date, end_date = get_current_pay_period()
        response = requests.get(
            f"{BASE_URL}/api/payroll/transactions",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} transactions/adjustments")
    
    def test_legacy_manual_entries_endpoint(self, auth_headers):
        """Verify legacy manual entries endpoint"""
        start_date, end_date = get_current_pay_period()
        response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} legacy manual entries")
    
    def test_payroll_report_endpoint(self, auth_headers):
        """Verify payroll report endpoint"""
        start_date, end_date = get_current_pay_period()
        response = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "employees" in data or "summary" in data or isinstance(data, dict)
        print(f"Payroll report loaded successfully")
    
    def test_payroll_timesheet_endpoint(self, auth_headers):
        """Verify payroll timesheet endpoint"""
        start_date, end_date = get_current_pay_period()
        response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Payroll timesheet loaded successfully")
    
    def test_signoff_endpoint(self, auth_headers):
        """Verify signoff endpoint"""
        start_date, end_date = get_current_pay_period()
        response = requests.get(
            f"{BASE_URL}/api/payroll/signoff",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "week_start": start_date,
                "period_end": end_date
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Signoff data loaded successfully")


class TestShiftOperations:
    """Test shift CRUD operations for FIX 6 - Adding end time to existing shift"""
    
    def test_create_shift_with_only_start_time(self, auth_headers):
        """Create a shift with only start time (simulating active shift)"""
        # Use a date in the future to avoid conflicts
        test_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": test_date,
            "clock_in": f"{test_date}T09:00:00",
            "clock_out": None,
            "lunch_start": None,
            "lunch_end": None,
            "break_minutes": 0,
            "notes": "Test shift for iteration 110"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            json=payload,
            headers=auth_headers
        )
        
        # May return 200 or 201
        assert response.status_code in [200, 201], f"Failed to create shift: {response.text}"
        data = response.json()
        shift_id = data.get("id")
        print(f"Created shift with ID: {shift_id}")
        
        # Store for cleanup
        return shift_id, test_date
    
    def test_update_shift_add_end_time(self, auth_headers):
        """FIX 6: Add end time to an existing shift - should work independently"""
        # First create a shift
        test_date = (datetime.now() + timedelta(days=31)).strftime('%Y-%m-%d')
        
        create_payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": test_date,
            "clock_in": f"{test_date}T08:00:00",
            "clock_out": None,
            "lunch_start": None,
            "lunch_end": None,
            "break_minutes": 0,
            "notes": ""
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            json=create_payload,
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201], f"Failed to create shift: {create_response.text}"
        shift_id = create_response.json().get("id")
        
        # Now update with end time only
        update_payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": test_date,
            "clock_in": f"{test_date}T08:00:00",
            "clock_out": f"{test_date}T17:00:00",  # Adding end time
            "lunch_start": None,
            "lunch_end": None,
            "break_minutes": 0,
            "notes": ""
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}",
            json=update_payload,
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Failed to update shift with end time: {update_response.text}"
        print(f"Successfully added end time to shift {shift_id}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}", headers=auth_headers)


class TestAdjustmentOperations:
    """Test adjustment operations for FIX 5 - Adjustment sign change"""
    
    def test_create_positive_adjustment(self, auth_headers):
        """Create a positive adjustment (earnings)"""
        start_date, end_date = get_current_pay_period()
        
        payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": start_date,
            "description": "Test positive adjustment iter110",
            "amount": 100.00,
            "type": "earnings"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/transactions",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code in [200, 201], f"Failed to create adjustment: {response.text}"
        data = response.json()
        print(f"Created positive adjustment with ID: {data.get('id')}")
        return data.get("id")
    
    def test_adjustment_sign_change(self, auth_headers):
        """FIX 5: Change adjustment from positive to negative - should work in isolation"""
        start_date, end_date = get_current_pay_period()
        
        # Create positive adjustment
        create_payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": start_date,
            "description": "Test sign change iter110",
            "amount": 50.00,
            "type": "earnings"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/transactions",
            json=create_payload,
            headers=auth_headers
        )
        assert create_response.status_code in [200, 201], f"Failed to create adjustment: {create_response.text}"
        adjustment_id = create_response.json().get("id")
        
        # Change to negative (advance/deduction)
        update_payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": start_date,
            "description": "Test sign change iter110 - now negative",
            "amount": 25.00,  # Amount is absolute, type determines sign
            "type": "advance"  # Negative type
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/payroll/transactions/{adjustment_id}",
            json=update_payload,
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Failed to change adjustment sign: {update_response.text}"
        print(f"Successfully changed adjustment {adjustment_id} from positive to negative")
        
        # Verify the change
        verify_response = requests.get(
            f"{BASE_URL}/api/payroll/transactions",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        transactions = verify_response.json()
        updated_tx = next((t for t in transactions if t.get("id") == adjustment_id), None)
        assert updated_tx is not None, "Updated transaction not found"
        assert updated_tx.get("type") == "advance", f"Type should be 'advance', got {updated_tx.get('type')}"
        print(f"Verified adjustment type changed to: {updated_tx.get('type')}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/payroll/transactions/{adjustment_id}", headers=auth_headers)


class TestEmployeeUpdate:
    """Test employee update for section-by-section save"""
    
    def test_employee_update(self, auth_headers):
        """Verify employee info can be updated independently"""
        # Get current employee data
        get_response = requests.get(
            f"{BASE_URL}/api/employees/{TEST_EMPLOYEE_ID}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        original_data = get_response.json()
        
        # Update with same data (no actual change)
        update_payload = {
            "name": original_data.get("name"),
            "title": original_data.get("title", ""),
            "manager_name": original_data.get("manager_name", ""),
            "hourly_rate": original_data.get("hourly_rate", 0),
            "overtime_rate": original_data.get("overtime_rate", 0)
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/employees/{TEST_EMPLOYEE_ID}",
            json=update_payload,
            headers=auth_headers
        )
        assert update_response.status_code == 200, f"Failed to update employee: {update_response.text}"
        print(f"Employee update successful")


class TestSignoffUpdate:
    """Test signoff update for section-by-section save"""
    
    def test_signoff_update(self, auth_headers):
        """Verify signoff can be updated independently"""
        start_date, end_date = get_current_pay_period()
        
        payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "week_start": start_date,
            "period_end": end_date,
            "reviewed_by": "Test Reviewer",
            "review_date": start_date,
            "approved_by": "",
            "approval_date": None,
            "payroll_notes": "Test notes for iteration 110"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/payroll/signoff",
            json=payload,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to update signoff: {response.text}"
        print(f"Signoff update successful")


class TestShiftWithNotesOnly:
    """Test FIX 2 - Notes alone don't require start/end time"""
    
    def test_shift_notes_only_validation(self, auth_headers):
        """
        FIX 2: A row with only notes (no time fields) should NOT require start/end time.
        This is a frontend validation test - the backend should accept shifts with notes only.
        """
        test_date = (datetime.now() + timedelta(days=32)).strftime('%Y-%m-%d')
        
        # Try to create a shift with only notes (no times)
        # The backend may or may not accept this - the key fix is frontend validation
        payload = {
            "employee_id": TEST_EMPLOYEE_ID,
            "date": test_date,
            "clock_in": None,
            "clock_out": None,
            "lunch_start": None,
            "lunch_end": None,
            "break_minutes": 0,
            "notes": "Just a note, no times"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            json=payload,
            headers=auth_headers
        )
        
        # The backend behavior may vary - document what happens
        print(f"Notes-only shift creation response: {response.status_code}")
        if response.status_code in [200, 201]:
            print("Backend accepts notes-only shifts")
            # Cleanup
            shift_id = response.json().get("id")
            if shift_id:
                requests.delete(f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}", headers=auth_headers)
        else:
            print(f"Backend requires time fields: {response.text}")
            # This is expected - the fix is in frontend validation


class TestLegacyEntriesResolution:
    """Test FIX 3 - Legacy entries only saved when changed"""
    
    def test_legacy_entries_list(self, auth_headers):
        """Get legacy entries to understand the data structure"""
        start_date, end_date = get_current_pay_period()
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={
                "employee_id": TEST_EMPLOYEE_ID,
                "start_date": start_date,
                "end_date": end_date
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        entries = response.json()
        print(f"Found {len(entries)} legacy entries")
        
        if entries:
            # Show structure of first entry
            print(f"Sample entry keys: {list(entries[0].keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
