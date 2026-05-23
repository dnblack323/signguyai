"""
Test Dashboard API Endpoints
Tests the new dashboard widgets and stats API

Endpoints tested:
- GET /api/dashboard/stats - Dashboard statistics
- GET /api/dashboard/pending-approvals - Proofs awaiting approval
- GET /api/dashboard/unread-messages - Unread customer messages
- GET /api/dashboard/team-status-today - V1 team status (supersedes legacy clocked-in)
- GET /api/dashboard/today-command-center - V1 command center (supersedes legacy todays-schedule)
"""

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser123@test.com"
TEST_PASSWORD = COMMON_TEST_PASSWORD


class TestDashboardAPIs:
    """Test all dashboard API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.text}")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_dashboard_stats_endpoint(self):
        """Test /api/dashboard/stats returns valid structure"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/stats")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions - validate response structure
        data = response.json()
        assert "total_customers" in data, "Missing total_customers field"
        assert "active_jobs" in data, "Missing active_jobs field"
        assert "pending_invoices" in data, "Missing pending_invoices field"
        assert "today_revenue" in data, "Missing today_revenue field"
        assert "overdue_count" in data, "Missing overdue_count field"
        assert "overdue_total" in data, "Missing overdue_total field"
        
        # Type assertions
        assert isinstance(data["total_customers"], int), "total_customers should be int"
        assert isinstance(data["active_jobs"], int), "active_jobs should be int"
        assert isinstance(data["pending_invoices"], int), "pending_invoices should be int"
        assert isinstance(data["today_revenue"], (int, float)), "today_revenue should be numeric"
        assert isinstance(data["overdue_count"], int), "overdue_count should be int"
        assert isinstance(data["overdue_total"], (int, float)), "overdue_total should be numeric"
    
    def test_pending_approvals_endpoint(self):
        """Test /api/dashboard/pending-approvals returns valid structure"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/pending-approvals")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions - validate response is a list
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are approvals, validate structure
        if len(data) > 0:
            approval = data[0]
            assert "id" in approval, "Missing id field"
            assert "job_id" in approval, "Missing job_id field"
            assert "job_name" in approval, "Missing job_name field"
            assert "customer_name" in approval, "Missing customer_name field"
            assert "created_at" in approval, "Missing created_at field"
            assert "status" in approval, "Missing status field"
    
    def test_unread_messages_endpoint(self):
        """Test /api/dashboard/unread-messages returns valid structure"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/unread-messages")
        
        # Status assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions - validate response is a list
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are messages, validate structure
        if len(data) > 0:
            msg = data[0]
            assert "conversation_id" in msg, "Missing conversation_id field"
            assert "customer_id" in msg, "Missing customer_id field"
            assert "customer_name" in msg, "Missing customer_name field"
            assert "last_message" in msg, "Missing last_message field"
            assert "last_message_at" in msg, "Missing last_message_at field"
            assert "unread_count" in msg, "Missing unread_count field"
    
    def test_clocked_in_endpoint(self):
        """[Phase 5] Legacy /clocked-in removed; verify V1 team-status-today instead."""
        response = self.session.get(f"{BASE_URL}/api/dashboard/team-status-today")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        assert "employees" in data, "Missing employees list"
        assert "clocked_in_count" in data, "Missing clocked_in_count"
        assert "scheduled_count" in data, "Missing scheduled_count"

    def test_todays_schedule_endpoint(self):
        """[Phase 5] Legacy /todays-schedule removed; verify V1 today-command-center."""
        response = self.session.get(f"{BASE_URL}/api/dashboard/today-command-center")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, dict), "Response should be a dict"
        assert "due_order_items_today" in data, "Missing due_order_items_today list"
        assert "appointments_installs_today" in data, "Missing appointments_installs_today list"
        assert "team_status_today" in data, "Missing team_status_today"
    
    def test_dashboard_stats_requires_auth(self):
        """Test that dashboard/stats requires authentication"""
        unauthenticated_session = requests.Session()
        response = unauthenticated_session.get(f"{BASE_URL}/api/dashboard/stats")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_pending_approvals_requires_auth(self):
        """Test that dashboard/pending-approvals requires authentication"""
        unauthenticated_session = requests.Session()
        response = unauthenticated_session.get(f"{BASE_URL}/api/dashboard/pending-approvals")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_unread_messages_requires_auth(self):
        """Test that dashboard/unread-messages requires authentication"""
        unauthenticated_session = requests.Session()
        response = unauthenticated_session.get(f"{BASE_URL}/api/dashboard/unread-messages")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_clocked_in_requires_auth(self):
        """[Phase 5] V1 team-status-today (replacement) requires auth."""
        unauthenticated_session = requests.Session()
        response = unauthenticated_session.get(f"{BASE_URL}/api/dashboard/team-status-today")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"

    def test_todays_schedule_requires_auth(self):
        """[Phase 5] V1 today-command-center (replacement) requires auth."""
        unauthenticated_session = requests.Session()
        response = unauthenticated_session.get(f"{BASE_URL}/api/dashboard/today-command-center")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
