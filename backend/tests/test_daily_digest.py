"""
Daily Digest Feature Tests
Tests for the morning digest email feature:
- GET /api/digest/preview - Preview digest content
- POST /api/digest/send - Manually send digest
- GET /api/digest/settings - Get digest settings
- PUT /api/digest/settings - Update digest settings
- GET /api/digest/history - Get digest send history
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser@example.com"
TEST_PASSWORD = "TestPassword123!"


class TestDigestEndpoints:
    """Daily Digest API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.authenticated = True
        else:
            self.authenticated = False
            pytest.skip(f"Authentication failed: {login_response.status_code}")
    
    # ==================== GET /api/digest/preview ====================
    
    def test_digest_preview_returns_200(self):
        """GET /api/digest/preview returns 200"""
        response = self.session.get(f"{BASE_URL}/api/digest/preview")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/digest/preview returns 200")
    
    def test_digest_preview_has_all_sections(self):
        """GET /api/digest/preview returns all required sections"""
        response = self.session.get(f"{BASE_URL}/api/digest/preview")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check all required sections exist
        required_fields = [
            "date", "day_name", "company_name",
            "scheduled_employees", "scheduled_count", "total_employees",
            "overdue_invoices", "overdue_count", "overdue_total",
            "jobs_today", "jobs_today_count",
            "pending_approvals",
            "yesterday_revenue",
            "unread_messages"
        ]
        
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"PASS: Digest preview has all sections: {list(data.keys())}")
    
    def test_digest_preview_data_types(self):
        """GET /api/digest/preview returns correct data types"""
        response = self.session.get(f"{BASE_URL}/api/digest/preview")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify data types
        assert isinstance(data["scheduled_employees"], list), "scheduled_employees should be a list"
        assert isinstance(data["overdue_invoices"], list), "overdue_invoices should be a list"
        assert isinstance(data["jobs_today"], list), "jobs_today should be a list"
        assert isinstance(data["scheduled_count"], int), "scheduled_count should be int"
        assert isinstance(data["pending_approvals"], int), "pending_approvals should be int"
        assert isinstance(data["unread_messages"], int), "unread_messages should be int"
        assert isinstance(data["yesterday_revenue"], (int, float)), "yesterday_revenue should be numeric"
        
        print("PASS: Digest preview data types are correct")
    
    # ==================== GET /api/digest/settings ====================
    
    def test_digest_settings_returns_200(self):
        """GET /api/digest/settings returns 200"""
        response = self.session.get(f"{BASE_URL}/api/digest/settings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/digest/settings returns 200")
    
    def test_digest_settings_default_values(self):
        """GET /api/digest/settings returns default settings structure"""
        response = self.session.get(f"{BASE_URL}/api/digest/settings")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check required fields exist
        assert "enabled" in data, "Missing 'enabled' field"
        assert "schedule_time" in data, "Missing 'schedule_time' field"
        assert "recipients" in data, "Missing 'recipients' field"
        
        # Check data types
        assert isinstance(data["enabled"], bool), "enabled should be boolean"
        assert isinstance(data["schedule_time"], str), "schedule_time should be string"
        assert isinstance(data["recipients"], list), "recipients should be list"
        
        print(f"PASS: Digest settings structure correct: enabled={data['enabled']}, time={data['schedule_time']}, recipients={len(data['recipients'])}")
    
    # ==================== PUT /api/digest/settings ====================
    
    def test_digest_settings_update_enabled(self):
        """PUT /api/digest/settings can toggle enabled"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/digest/settings")
        current_enabled = get_response.json().get("enabled", False)
        
        # Toggle enabled
        new_enabled = not current_enabled
        update_response = self.session.put(f"{BASE_URL}/api/digest/settings", json={
            "enabled": new_enabled
        })
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        updated_data = update_response.json()
        assert updated_data["enabled"] == new_enabled, f"Expected enabled={new_enabled}, got {updated_data['enabled']}"
        
        # Revert back
        self.session.put(f"{BASE_URL}/api/digest/settings", json={"enabled": current_enabled})
        
        print(f"PASS: Digest settings enabled toggle works: {current_enabled} -> {new_enabled}")
    
    def test_digest_settings_update_schedule_time(self):
        """PUT /api/digest/settings can update schedule_time"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/digest/settings")
        current_time = get_response.json().get("schedule_time", "07:00")
        
        # Update time
        new_time = "08:30"
        update_response = self.session.put(f"{BASE_URL}/api/digest/settings", json={
            "schedule_time": new_time
        })
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        updated_data = update_response.json()
        assert updated_data["schedule_time"] == new_time, f"Expected time={new_time}, got {updated_data['schedule_time']}"
        
        # Revert back
        self.session.put(f"{BASE_URL}/api/digest/settings", json={"schedule_time": current_time})
        
        print(f"PASS: Digest settings schedule_time update works: {current_time} -> {new_time}")
    
    def test_digest_settings_update_recipients(self):
        """PUT /api/digest/settings can add/remove recipients"""
        # Get current settings
        get_response = self.session.get(f"{BASE_URL}/api/digest/settings")
        current_recipients = get_response.json().get("recipients", [])
        
        # Add a test recipient
        test_email = "test_digest_recipient@example.com"
        new_recipients = current_recipients + [test_email]
        
        update_response = self.session.put(f"{BASE_URL}/api/digest/settings", json={
            "recipients": new_recipients
        })
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        
        updated_data = update_response.json()
        assert test_email in updated_data["recipients"], f"Test email not in recipients"
        
        # Revert back
        self.session.put(f"{BASE_URL}/api/digest/settings", json={"recipients": current_recipients})
        
        print(f"PASS: Digest settings recipients update works")
    
    # ==================== GET /api/digest/history ====================
    
    def test_digest_history_returns_200(self):
        """GET /api/digest/history returns 200"""
        response = self.session.get(f"{BASE_URL}/api/digest/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("PASS: GET /api/digest/history returns 200")
    
    def test_digest_history_returns_list(self):
        """GET /api/digest/history returns a list"""
        response = self.session.get(f"{BASE_URL}/api/digest/history")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        
        print(f"PASS: Digest history returns list with {len(data)} entries")
    
    def test_digest_history_with_limit(self):
        """GET /api/digest/history respects limit parameter"""
        response = self.session.get(f"{BASE_URL}/api/digest/history?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        assert len(data) <= 5, f"Expected max 5 entries, got {len(data)}"
        
        print(f"PASS: Digest history respects limit parameter")
    
    # ==================== POST /api/digest/send ====================
    
    def test_digest_send_returns_200(self):
        """POST /api/digest/send returns 200 and sends digest"""
        response = self.session.post(f"{BASE_URL}/api/digest/send")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have 'message' field"
        assert "results" in data, "Response should have 'results' field"
        
        print(f"PASS: POST /api/digest/send returns 200: {data['message']}")
    
    def test_digest_send_creates_history_entry(self):
        """POST /api/digest/send creates a history entry"""
        # Get history count before
        history_before = self.session.get(f"{BASE_URL}/api/digest/history?limit=50").json()
        count_before = len(history_before)
        
        # Send digest
        send_response = self.session.post(f"{BASE_URL}/api/digest/send")
        assert send_response.status_code == 200
        
        # Get history count after
        history_after = self.session.get(f"{BASE_URL}/api/digest/history?limit=50").json()
        count_after = len(history_after)
        
        assert count_after >= count_before, "History should have new entry after send"
        
        # Check latest entry has correct structure
        if count_after > 0:
            latest = history_after[0]
            assert "sent_at" in latest, "History entry should have sent_at"
            assert "recipients" in latest, "History entry should have recipients"
            assert "type" in latest, "History entry should have type"
        
        print(f"PASS: Digest send creates history entry (before={count_before}, after={count_after})")
    
    # ==================== Auth Required Tests ====================
    
    def test_digest_preview_requires_auth(self):
        """GET /api/digest/preview requires authentication"""
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/digest/preview")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/digest/preview requires auth")
    
    def test_digest_settings_requires_auth(self):
        """GET /api/digest/settings requires authentication"""
        no_auth_session = requests.Session()
        response = no_auth_session.get(f"{BASE_URL}/api/digest/settings")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/digest/settings requires auth")
    
    def test_digest_send_requires_auth(self):
        """POST /api/digest/send requires authentication"""
        no_auth_session = requests.Session()
        response = no_auth_session.post(f"{BASE_URL}/api/digest/send")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/digest/send requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
