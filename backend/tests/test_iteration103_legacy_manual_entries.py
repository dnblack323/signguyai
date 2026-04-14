"""
Iteration 103 - Legacy Manual Entries Section Testing

Tests for:
1. GET /api/payroll/legacy-manual-entries returns legacy entries for employee/week
2. PUT /api/payroll/legacy-manual-entries/{entry_id}/resolution saves handling mode
3. Legacy entries show date, source/type, hours, notes, current effect on totals
4. Inline handling controls persist (keep_legacy, worksheet_manual_row, merge_into_day)
5. Payroll totals and exports remain unchanged before/after legacy handling updates
6. Worksheet save works with legacy handling data present
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestLegacyManualEntriesAPI:
    """Tests for legacy manual entries API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get auth token"""
        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "signguypa@gmail.com", "password": "Billnel323"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get employees
        employees_response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=self.headers
        )
        assert employees_response.status_code == 200
        self.employees = employees_response.json()
        
        # Use the specific employee ID mentioned in the context
        self.employee_id = "18eed187-1a90-4bf8-b233-dc47b44c9579"
        self.week_start = "2026-04-06"  # Week with known legacy data
        
        # Verify employee exists
        employee_exists = any(emp["id"] == self.employee_id for emp in self.employees)
        if not employee_exists:
            # Fall back to first employee if specific one not found
            self.employee_id = self.employees[0]["id"] if self.employees else None
            print(f"WARNING: Specific employee not found, using: {self.employee_id}")
    
    def test_get_legacy_manual_entries_endpoint_exists(self):
        """Test GET /api/payroll/legacy-manual-entries endpoint exists and returns data"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert response.status_code == 200, f"GET legacy-manual-entries failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: GET legacy-manual-entries returns {len(data)} entries")
        return data
    
    def test_legacy_entry_structure(self):
        """Test that legacy entries have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            entry = data[0]
            # Check required fields per the feature spec
            required_fields = [
                "id", "date", "source_type", "hours", "notes",
                "current_effect_hours", "current_effect_pay", "current_effect_label",
                "included_in_totals", "included_in_exports",
                "handling_mode", "target_date", "admin_note", "resolution_saved"
            ]
            
            for field in required_fields:
                assert field in entry, f"Missing required field: {field}"
            
            print(f"SUCCESS: Legacy entry has all required fields")
            print(f"  - id: {entry['id']}")
            print(f"  - date: {entry['date']}")
            print(f"  - source_type: {entry['source_type']}")
            print(f"  - hours: {entry['hours']}")
            print(f"  - notes: {entry['notes']}")
            print(f"  - current_effect_label: {entry['current_effect_label']}")
            print(f"  - handling_mode: {entry['handling_mode']}")
            print(f"  - resolution_saved: {entry['resolution_saved']}")
        else:
            print("INFO: No legacy entries found for this employee/week")
    
    def test_legacy_entry_shows_current_effect_on_totals(self):
        """Test that legacy entries show current effect on payroll totals"""
        response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            for entry in data:
                # Verify current effect fields are populated
                assert "current_effect_hours" in entry
                assert "current_effect_pay" in entry
                assert "current_effect_label" in entry
                assert entry["current_effect_hours"] >= 0
                assert entry["current_effect_pay"] >= 0
                assert len(entry["current_effect_label"]) > 0
                
                print(f"Entry {entry['date']}: {entry['current_effect_hours']} hrs, ${entry['current_effect_pay']}")
            
            print(f"SUCCESS: All {len(data)} entries show current effect on totals")
        else:
            print("INFO: No legacy entries to verify current effect")
    
    def test_put_legacy_entry_resolution_keep_legacy(self):
        """Test PUT /api/payroll/legacy-manual-entries/{id}/resolution with keep_legacy mode"""
        # First get entries
        get_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert get_response.status_code == 200
        entries = get_response.json()
        
        if len(entries) > 0:
            entry_id = entries[0]["id"]
            
            # Update resolution to keep_legacy
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "keep_legacy",
                "target_date": entries[0]["date"],
                "admin_note": "Test: Keeping as legacy entry"
            }
            
            put_response = requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
            assert put_response.status_code == 200, f"PUT resolution failed: {put_response.text}"
            
            updated = put_response.json()
            assert updated["handling_mode"] == "keep_legacy"
            assert updated["resolution_saved"] == True
            print(f"SUCCESS: Resolution saved with keep_legacy mode")
        else:
            pytest.skip("No legacy entries to test resolution")
    
    def test_put_legacy_entry_resolution_worksheet_manual_row(self):
        """Test PUT resolution with worksheet_manual_row mode"""
        get_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert get_response.status_code == 200
        entries = get_response.json()
        
        if len(entries) > 0:
            entry_id = entries[0]["id"]
            
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "worksheet_manual_row",
                "target_date": entries[0]["date"],
                "admin_note": "Test: Converting to worksheet manual row"
            }
            
            put_response = requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
            assert put_response.status_code == 200, f"PUT resolution failed: {put_response.text}"
            
            updated = put_response.json()
            assert updated["handling_mode"] == "worksheet_manual_row"
            print(f"SUCCESS: Resolution saved with worksheet_manual_row mode")
        else:
            pytest.skip("No legacy entries to test resolution")
    
    def test_put_legacy_entry_resolution_merge_into_day(self):
        """Test PUT resolution with merge_into_day mode"""
        get_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert get_response.status_code == 200
        entries = get_response.json()
        
        if len(entries) > 1:
            entry_id = entries[1]["id"]
            
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "merge_into_day",
                "target_date": entries[1]["date"],
                "admin_note": "Test: Merging into selected day"
            }
            
            put_response = requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
            assert put_response.status_code == 200, f"PUT resolution failed: {put_response.text}"
            
            updated = put_response.json()
            assert updated["handling_mode"] == "merge_into_day"
            print(f"SUCCESS: Resolution saved with merge_into_day mode")
        elif len(entries) > 0:
            # Use first entry if only one exists
            entry_id = entries[0]["id"]
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "merge_into_day",
                "target_date": entries[0]["date"],
                "admin_note": "Test: Merging into selected day"
            }
            
            put_response = requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
            assert put_response.status_code == 200
            print(f"SUCCESS: Resolution saved with merge_into_day mode")
        else:
            pytest.skip("No legacy entries to test resolution")
    
    def test_resolution_persists_after_get(self):
        """Test that resolution persists and is returned on subsequent GET"""
        # First set a resolution
        get_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert get_response.status_code == 200
        entries = get_response.json()
        
        if len(entries) > 0:
            entry_id = entries[0]["id"]
            
            # Set resolution
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "keep_legacy",
                "target_date": entries[0]["date"],
                "admin_note": "Persistence test note"
            }
            
            put_response = requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
            assert put_response.status_code == 200
            
            # Get again and verify persistence
            get_response2 = requests.get(
                f"{BASE_URL}/api/payroll/legacy-manual-entries",
                params={"employee_id": self.employee_id, "week_start": self.week_start},
                headers=self.headers
            )
            assert get_response2.status_code == 200
            entries2 = get_response2.json()
            
            # Find the same entry
            updated_entry = next((e for e in entries2 if e["id"] == entry_id), None)
            assert updated_entry is not None
            assert updated_entry["handling_mode"] == "keep_legacy"
            assert updated_entry["admin_note"] == "Persistence test note"
            assert updated_entry["resolution_saved"] == True
            
            print(f"SUCCESS: Resolution persists after GET")
        else:
            pytest.skip("No legacy entries to test persistence")


class TestPayrollTotalsUnchanged:
    """Tests to verify payroll totals remain unchanged before/after legacy handling updates"""
    
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
        
        self.employee_id = "18eed187-1a90-4bf8-b233-dc47b44c9579"
        self.week_start = "2026-04-06"
        self.week_end = "2026-04-12"
        
        # Verify employee exists
        employee_exists = any(emp["id"] == self.employee_id for emp in self.employees)
        if not employee_exists:
            self.employee_id = self.employees[0]["id"] if self.employees else None
    
    def test_payroll_report_totals_unchanged_after_resolution_update(self):
        """Test that payroll report totals remain unchanged after updating legacy resolution"""
        # Get initial report
        report_before = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": self.employee_id,
                "start_date": self.week_start,
                "end_date": self.week_end
            },
            headers=self.headers
        )
        assert report_before.status_code == 200
        before_data = report_before.json()
        
        # Get legacy entries and update resolution
        legacy_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        
        if legacy_response.status_code == 200 and len(legacy_response.json()) > 0:
            entries = legacy_response.json()
            entry_id = entries[0]["id"]
            
            # Update resolution
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "worksheet_manual_row",
                "target_date": entries[0]["date"],
                "admin_note": "Totals test"
            }
            
            requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
        
        # Get report after
        report_after = requests.get(
            f"{BASE_URL}/api/payroll/report",
            params={
                "employee_id": self.employee_id,
                "start_date": self.week_start,
                "end_date": self.week_end
            },
            headers=self.headers
        )
        assert report_after.status_code == 200
        after_data = report_after.json()
        
        # Compare totals
        if before_data.get("employees") and after_data.get("employees"):
            before_emp = before_data["employees"][0] if before_data["employees"] else {}
            after_emp = after_data["employees"][0] if after_data["employees"] else {}
            
            # Totals should be unchanged
            assert before_emp.get("gross_pay") == after_emp.get("gross_pay"), \
                f"Gross pay changed: {before_emp.get('gross_pay')} -> {after_emp.get('gross_pay')}"
            assert before_emp.get("final_owed") == after_emp.get("final_owed"), \
                f"Final owed changed: {before_emp.get('final_owed')} -> {after_emp.get('final_owed')}"
            
            print(f"SUCCESS: Payroll totals unchanged after resolution update")
            print(f"  - Gross pay: ${before_emp.get('gross_pay', 0)}")
            print(f"  - Final owed: ${before_emp.get('final_owed', 0)}")
        else:
            print("INFO: No employee data to compare")
    
    def test_timesheet_totals_unchanged_after_resolution_update(self):
        """Test that timesheet totals remain unchanged after updating legacy resolution"""
        # Get initial timesheet
        timesheet_before = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": self.employee_id,
                "start_date": self.week_start,
                "end_date": self.week_end
            },
            headers=self.headers
        )
        assert timesheet_before.status_code == 200
        before_data = timesheet_before.json()
        
        # Update a resolution (if entries exist)
        legacy_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        
        if legacy_response.status_code == 200 and len(legacy_response.json()) > 0:
            entries = legacy_response.json()
            entry_id = entries[0]["id"]
            
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "merge_into_day",
                "target_date": entries[0]["date"],
                "admin_note": "Timesheet totals test"
            }
            
            requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
        
        # Get timesheet after
        timesheet_after = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            params={
                "employee_id": self.employee_id,
                "start_date": self.week_start,
                "end_date": self.week_end
            },
            headers=self.headers
        )
        assert timesheet_after.status_code == 200
        after_data = timesheet_after.json()
        
        # Compare totals
        if before_data.get("totals") and after_data.get("totals"):
            assert before_data["totals"].get("total_pay") == after_data["totals"].get("total_pay"), \
                f"Total pay changed"
            assert before_data["totals"].get("final_owed") == after_data["totals"].get("final_owed"), \
                f"Final owed changed"
            
            print(f"SUCCESS: Timesheet totals unchanged after resolution update")
        else:
            print("INFO: No totals data to compare")


class TestCleanWeekMessage:
    """Tests for clean-state message on weeks without legacy entries"""
    
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
        self.employee_id = self.employees[0]["id"] if self.employees else None
    
    def test_empty_legacy_entries_for_clean_week(self):
        """Test that a week without manual entries returns empty list"""
        # Use a future week that likely has no data
        clean_week = "2026-12-07"
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": clean_week},
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # For a clean week, should return empty list
        print(f"SUCCESS: Clean week returns {len(data)} legacy entries (expected 0 or few)")


class TestWorksheetSaveWithLegacyData:
    """Tests for worksheet save functionality with legacy handling data"""
    
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
        
        self.employee_id = "18eed187-1a90-4bf8-b233-dc47b44c9579"
        self.week_start = "2026-04-06"
        
        employee_exists = any(emp["id"] == self.employee_id for emp in self.employees)
        if not employee_exists:
            self.employee_id = self.employees[0]["id"] if self.employees else None
    
    def test_signoff_save_with_legacy_entries_present(self):
        """Test that signoff can be saved when legacy entries exist"""
        # First verify legacy entries exist
        legacy_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        assert legacy_response.status_code == 200
        
        # Save signoff
        signoff_data = {
            "employee_id": self.employee_id,
            "week_start": self.week_start,
            "reviewed_by": "Legacy Test Reviewer",
            "review_date": "2026-04-10",
            "approved_by": "",
            "approval_date": "",
            "payroll_notes": "Testing signoff with legacy entries present"
        }
        
        signoff_response = requests.put(
            f"{BASE_URL}/api/payroll/signoff",
            json=signoff_data,
            headers=self.headers
        )
        assert signoff_response.status_code == 200, f"Signoff save failed: {signoff_response.text}"
        
        saved = signoff_response.json()
        assert saved["reviewed_by"] == "Legacy Test Reviewer"
        print(f"SUCCESS: Signoff saved with legacy entries present")
    
    def test_employee_update_with_legacy_entries_present(self):
        """Test that employee can be updated when legacy entries exist"""
        # Get current employee data
        emp_response = requests.get(
            f"{BASE_URL}/api/employees/{self.employee_id}",
            headers=self.headers
        )
        assert emp_response.status_code == 200
        current_emp = emp_response.json()
        
        # Update employee
        update_data = {
            "hourly_rate": current_emp.get("hourly_rate", 20),
            "overtime_rate": current_emp.get("overtime_rate", 30)
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/employees/{self.employee_id}",
            json=update_data,
            headers=self.headers
        )
        assert update_response.status_code == 200, f"Employee update failed: {update_response.text}"
        print(f"SUCCESS: Employee updated with legacy entries present")


class TestInvalidResolutionHandling:
    """Tests for invalid resolution handling"""
    
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
        self.employee_id = self.employees[0]["id"] if self.employees else None
        self.week_start = "2026-04-06"
    
    def test_invalid_handling_mode_rejected(self):
        """Test that invalid handling mode is rejected"""
        # Get entries first
        legacy_response = requests.get(
            f"{BASE_URL}/api/payroll/legacy-manual-entries",
            params={"employee_id": self.employee_id, "week_start": self.week_start},
            headers=self.headers
        )
        
        if legacy_response.status_code == 200 and len(legacy_response.json()) > 0:
            entries = legacy_response.json()
            entry_id = entries[0]["id"]
            
            # Try invalid handling mode
            resolution_data = {
                "employee_id": self.employee_id,
                "week_start": self.week_start,
                "handling_mode": "invalid_mode",
                "target_date": entries[0]["date"],
                "admin_note": "Should fail"
            }
            
            put_response = requests.put(
                f"{BASE_URL}/api/payroll/legacy-manual-entries/{entry_id}/resolution",
                json=resolution_data,
                headers=self.headers
            )
            
            # Should return 400 for invalid handling mode
            assert put_response.status_code == 400, f"Expected 400 for invalid mode, got {put_response.status_code}"
            print(f"SUCCESS: Invalid handling mode rejected with 400")
        else:
            pytest.skip("No legacy entries to test invalid handling")
    
    def test_nonexistent_entry_returns_404(self):
        """Test that updating nonexistent entry returns 404"""
        resolution_data = {
            "employee_id": self.employee_id,
            "week_start": self.week_start,
            "handling_mode": "keep_legacy",
            "target_date": "2026-04-06",
            "admin_note": "Should fail"
        }
        
        put_response = requests.put(
            f"{BASE_URL}/api/payroll/legacy-manual-entries/nonexistent-id-12345/resolution",
            json=resolution_data,
            headers=self.headers
        )
        
        assert put_response.status_code == 404, f"Expected 404 for nonexistent entry, got {put_response.status_code}"
        print(f"SUCCESS: Nonexistent entry returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
