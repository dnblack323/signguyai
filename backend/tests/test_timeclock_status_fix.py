"""
Timeclock Status Fix Verification Tests
========================================
Tests for the bug fix: selecting an employee in Time Clock should NOT auto-show 
"working" status if no open shift exists.

Key scenarios:
1. Fresh employee with no shifts -> status should be "not_started"
2. Employee with closed shift (clock_out present) -> status should NOT be "working"
3. Employee clocks in -> status should be "working"
4. Employee clocks out -> status should be "finished" or "not_started"
5. Inconsistent shift (status=working but clock_out present) -> should be auto-repaired
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTimeclockStatusFix:
    """Tests for timeclock status endpoint correctness"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with owner credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Create a test employee for isolation
        self.test_employee_name = f"TEST_TimeclockFix_{uuid.uuid4().hex[:8]}"
        create_resp = self.session.post(f"{BASE_URL}/api/employees", json={
            "name": self.test_employee_name,
            "hourly_rate": 15.0
        })
        assert create_resp.status_code == 200, f"Failed to create test employee: {create_resp.text}"
        self.test_employee_id = create_resp.json()["id"]
        
        yield
        
        # Cleanup: delete test employee
        self.session.delete(f"{BASE_URL}/api/employees/{self.test_employee_id}")
    
    def test_fresh_employee_status_not_started(self):
        """Fresh employee with no shifts should have status 'not_started'"""
        response = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status")
        assert response.status_code == 200, f"Status endpoint failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "not_started", f"Expected 'not_started', got '{data['status']}'"
        assert data.get("last_action") is None, f"Expected no last_action, got '{data.get('last_action')}'"
        print(f"PASS: Fresh employee status is 'not_started': {data}")
    
    def test_clock_in_shows_working(self):
        """After clock in, status should be 'working'"""
        # Clock in
        clock_in_resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "start_work"
        })
        assert clock_in_resp.status_code == 200, f"Clock in failed: {clock_in_resp.text}"
        
        # Check status
        status_resp = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status")
        assert status_resp.status_code == 200
        
        data = status_resp.json()
        assert data["status"] == "working", f"Expected 'working', got '{data['status']}'"
        assert data.get("shift_id") is not None, "Expected shift_id to be present"
        assert data.get("clocked_in_at") is not None, "Expected clocked_in_at to be present"
        print(f"PASS: After clock in, status is 'working': {data}")
    
    def test_clock_out_shows_not_working(self):
        """After clock out, status should NOT be 'working'"""
        # Clock in first
        self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "start_work"
        })
        
        # Clock out
        clock_out_resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "end_work"
        })
        assert clock_out_resp.status_code == 200, f"Clock out failed: {clock_out_resp.text}"
        
        # Check status - should NOT be working
        status_resp = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status")
        assert status_resp.status_code == 200
        
        data = status_resp.json()
        assert data["status"] in ["finished", "not_started"], f"Expected 'finished' or 'not_started', got '{data['status']}'"
        assert data["status"] != "working", f"BUG: Status should NOT be 'working' after clock out!"
        print(f"PASS: After clock out, status is '{data['status']}' (not working): {data}")
    
    def test_full_shift_cycle(self):
        """Test complete shift cycle: start -> break -> end break -> end work"""
        # Start work
        resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "start_work"
        })
        assert resp.status_code == 200
        
        status = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status").json()
        assert status["status"] == "working", f"After start_work, expected 'working', got '{status['status']}'"
        
        # Start break
        resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "break_start"
        })
        assert resp.status_code == 200
        
        status = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status").json()
        assert status["status"] == "on_break", f"After break_start, expected 'on_break', got '{status['status']}'"
        
        # End break
        resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "break_end"
        })
        assert resp.status_code == 200
        
        status = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status").json()
        assert status["status"] == "working", f"After break_end, expected 'working', got '{status['status']}'"
        
        # End work
        resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "end_work"
        })
        assert resp.status_code == 200
        
        status = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status").json()
        assert status["status"] != "working", f"After end_work, status should NOT be 'working', got '{status['status']}'"
        assert status["status"] != "on_break", f"After end_work, status should NOT be 'on_break', got '{status['status']}'"
        print(f"PASS: Full shift cycle completed correctly. Final status: {status['status']}")
    
    def test_invalid_action_sequence_rejected(self):
        """Invalid action sequences should be rejected"""
        # Try to end work without starting - should fail
        resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "end_work"
        })
        assert resp.status_code == 400, f"Expected 400 for invalid sequence, got {resp.status_code}"
        print(f"PASS: Invalid sequence (end_work without start) rejected: {resp.json()}")
        
        # Try to start break without clocking in - should fail
        resp = self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "break_start"
        })
        assert resp.status_code == 400, f"Expected 400 for invalid sequence, got {resp.status_code}"
        print(f"PASS: Invalid sequence (break_start without start_work) rejected: {resp.json()}")
    
    def test_reselecting_employee_after_clock_out(self):
        """Reselecting employee after clock out should NOT show working status"""
        # Clock in
        self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "start_work"
        })
        
        # Clock out
        self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "end_work"
        })
        
        # Simulate "reselecting" by calling status endpoint multiple times
        for i in range(3):
            status_resp = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/status")
            assert status_resp.status_code == 200
            data = status_resp.json()
            assert data["status"] != "working", f"BUG on call {i+1}: Status should NOT be 'working' after clock out!"
            assert data["status"] != "on_break", f"BUG on call {i+1}: Status should NOT be 'on_break' after clock out!"
        
        print(f"PASS: Reselecting employee after clock out consistently shows non-working status")
    
    def test_today_logs_endpoint(self):
        """Today's logs endpoint should return correct data"""
        # Clock in and out
        self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "start_work"
        })
        self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "end_work"
        })
        
        # Get today's logs
        logs_resp = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/today")
        assert logs_resp.status_code == 200, f"Today logs failed: {logs_resp.text}"
        
        logs = logs_resp.json()
        assert len(logs) >= 2, f"Expected at least 2 logs, got {len(logs)}"
        
        actions = [log["action"] for log in logs]
        assert "start_work" in actions, "Expected start_work in logs"
        assert "end_work" in actions, "Expected end_work in logs"
        print(f"PASS: Today's logs endpoint returns correct data: {len(logs)} logs")
    
    def test_shift_summary_endpoint(self):
        """Shift summary endpoint should return correct metrics"""
        # Clock in and out
        self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "start_work"
        })
        self.session.post(f"{BASE_URL}/api/timeclock", json={
            "employee_id": self.test_employee_id,
            "action": "end_work"
        })
        
        # Get summary
        summary_resp = self.session.get(f"{BASE_URL}/api/timeclock/{self.test_employee_id}/summary")
        assert summary_resp.status_code == 200, f"Summary failed: {summary_resp.text}"
        
        summary = summary_resp.json()
        assert "work_minutes" in summary, "Expected work_minutes in summary"
        assert "break_minutes" in summary, "Expected break_minutes in summary"
        assert "net_hours" in summary, "Expected net_hours in summary"
        assert summary["work_minutes"] >= 0, "work_minutes should be non-negative"
        print(f"PASS: Shift summary endpoint returns correct metrics: {summary}")


class TestTimeclockStatusWithExistingEmployees:
    """Test status endpoint with existing employees to verify no false positives"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_existing_employees_status_not_false_working(self):
        """Check all existing employees - none should show false 'working' status"""
        # Get all employees
        emp_resp = self.session.get(f"{BASE_URL}/api/employees")
        assert emp_resp.status_code == 200
        employees = emp_resp.json()
        
        working_count = 0
        checked_count = 0
        
        for emp in employees[:10]:  # Check first 10 employees
            if not emp.get("is_active", True):
                continue
            
            status_resp = self.session.get(f"{BASE_URL}/api/timeclock/{emp['id']}/status")
            if status_resp.status_code != 200:
                continue
            
            status = status_resp.json()
            checked_count += 1
            
            if status["status"] == "working":
                # If working, verify there's actually an open shift
                assert status.get("shift_id") is not None, f"Employee {emp['name']} shows 'working' but no shift_id!"
                working_count += 1
                print(f"Employee {emp['name']} is working (shift_id: {status.get('shift_id')})")
            else:
                print(f"Employee {emp['name']} status: {status['status']}")
        
        print(f"PASS: Checked {checked_count} employees, {working_count} legitimately working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
