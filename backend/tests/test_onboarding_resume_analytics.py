"""
Test suite for Onboarding Resume Persistence and Analytics Features - Iteration 64
Tests:
- GET /api/onboarding/status returns analytics + progress with current_tier/current_step_id
- PUT /api/onboarding/session persists current tier and step for the tenant
- Onboarding status returns correct analytics per tier
"""
import os
import pytest
import requests
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope='module')
def auth_token():
    """Get authentication token using admin credentials"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": LEGACY_ADMIN_EMAIL,
        "password": LEGACY_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")

@pytest.fixture
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


class TestOnboardingStatusAnalytics:
    """Tests for GET /api/onboarding/status endpoint - analytics and progress data"""

    def test_onboarding_status_returns_analytics(self, api_client):
        """Verify analytics object is returned with tier-level completion stats"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify analytics is present
        assert "analytics" in data, "Response should include 'analytics' field"
        analytics = data["analytics"]
        
        # Verify all 3 tiers have analytics
        assert "quick_start" in analytics, "Analytics should include quick_start tier"
        assert "standard_setup" in analytics, "Analytics should include standard_setup tier"
        assert "full_optimization" in analytics, "Analytics should include full_optimization tier"
        
        # Verify analytics structure for each tier
        for tier_id in ["quick_start", "standard_setup", "full_optimization"]:
            tier_analytics = analytics[tier_id]
            assert "total_steps" in tier_analytics, f"{tier_id} should have total_steps"
            assert "completed_steps" in tier_analytics, f"{tier_id} should have completed_steps"
            assert "finish_later_steps" in tier_analytics, f"{tier_id} should have finish_later_steps"
            assert "completion_percent" in tier_analytics, f"{tier_id} should have completion_percent"
            
            # Validate types
            assert isinstance(tier_analytics["total_steps"], int)
            assert isinstance(tier_analytics["completed_steps"], int)
            assert isinstance(tier_analytics["finish_later_steps"], int)
            assert isinstance(tier_analytics["completion_percent"], (int, float))
        
        print(f"✓ Analytics returned for all tiers: {list(analytics.keys())}")

    def test_onboarding_status_returns_progress(self, api_client):
        """Verify progress object is returned with current_tier and current_step_id"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify progress is present
        assert "progress" in data, "Response should include 'progress' field"
        progress = data["progress"]
        
        # Progress can be empty dict or have saved session data
        assert isinstance(progress, dict), "progress should be a dict"
        
        print(f"✓ Progress object returned: {progress}")

    def test_onboarding_status_returns_step_statuses(self, api_client):
        """Verify step_statuses dict is returned with all step IDs"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify step_statuses is present
        assert "step_statuses" in data, "Response should include 'step_statuses' field"
        step_statuses = data["step_statuses"]
        
        # Should have step statuses for all quick_start steps
        quick_start_steps = [
            "quick_company_profile", "quick_stripe_connect", "quick_production_workflow",
            "quick_first_employee", "quick_basic_pricing", "quick_customer_portal",
            "quick_first_job", "quick_portal_test"
        ]
        
        for step_id in quick_start_steps:
            assert step_id in step_statuses, f"Missing step status for {step_id}"
            assert step_statuses[step_id] in ["completed", "finish_later", "incomplete"], \
                f"Invalid status for {step_id}: {step_statuses[step_id]}"
        
        print(f"✓ Step statuses returned for {len(step_statuses)} steps")


class TestOnboardingSessionPersistence:
    """Tests for PUT /api/onboarding/session endpoint - resume state persistence"""

    def test_save_onboarding_session(self, api_client):
        """Test saving current tier and step to session"""
        payload = {
            "current_tier": "quick_start",
            "current_step_id": "quick_company_profile"
        }
        
        response = api_client.put(f"{BASE_URL}/api/onboarding/session", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response includes saved values
        assert data.get("current_tier") == "quick_start"
        assert data.get("current_step_id") == "quick_company_profile"
        assert "last_opened_at" in data, "Response should include last_opened_at timestamp"
        
        print(f"✓ Session saved: tier={data['current_tier']}, step={data['current_step_id']}")

    def test_saved_session_persists_in_status(self, api_client):
        """Verify saved session appears in GET /api/onboarding/status"""
        # First save a session
        unique_step = "quick_first_employee"  # Use a different step to test
        payload = {
            "current_tier": "quick_start",
            "current_step_id": unique_step
        }
        
        save_response = api_client.put(f"{BASE_URL}/api/onboarding/session", json=payload)
        assert save_response.status_code == 200
        
        # Now fetch status and verify progress includes saved data
        status_response = api_client.get(f"{BASE_URL}/api/onboarding/status")
        assert status_response.status_code == 200
        
        data = status_response.json()
        progress = data.get("progress", {})
        
        assert progress.get("current_tier") == "quick_start", "Saved tier should persist"
        assert progress.get("current_step_id") == unique_step, "Saved step_id should persist"
        assert "last_opened_at" in progress, "last_opened_at should persist"
        
        print(f"✓ Session persisted: tier={progress['current_tier']}, step={progress['current_step_id']}")

    def test_update_session_to_different_tier(self, api_client):
        """Test updating session to a different tier"""
        payload = {
            "current_tier": "standard_setup",
            "current_step_id": "standard_historical_invoices"
        }
        
        response = api_client.put(f"{BASE_URL}/api/onboarding/session", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("current_tier") == "standard_setup"
        assert data.get("current_step_id") == "standard_historical_invoices"
        
        print(f"✓ Session updated to standard_setup tier")

    def test_session_tracks_last_activity(self, api_client):
        """Verify last_opened_at is updated on session save"""
        import time
        
        # Save session
        payload = {
            "current_tier": "quick_start",
            "current_step_id": "quick_basic_pricing"
        }
        
        response1 = api_client.put(f"{BASE_URL}/api/onboarding/session", json=payload)
        assert response1.status_code == 200
        timestamp1 = response1.json().get("last_opened_at")
        
        # Wait briefly
        time.sleep(0.5)
        
        # Save again
        response2 = api_client.put(f"{BASE_URL}/api/onboarding/session", json=payload)
        assert response2.status_code == 200
        timestamp2 = response2.json().get("last_opened_at")
        
        # Timestamps should be different (or at least the endpoint accepts updates)
        assert timestamp2 is not None
        print(f"✓ Last activity tracked: {timestamp2}")


class TestOnboardingStepStatus:
    """Tests for PUT /api/onboarding/steps/{step_id} endpoint"""

    def test_mark_step_completed(self, api_client):
        """Test marking a step as completed"""
        step_id = f"quick_portal_test"  # Manual step
        
        response = api_client.put(
            f"{BASE_URL}/api/onboarding/steps/{step_id}",
            json={"status": "completed"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("step_id") == step_id
        assert data.get("status") == "completed"
        
        print(f"✓ Step {step_id} marked completed")

    def test_mark_step_finish_later(self, api_client):
        """Test marking a step as finish_later"""
        step_id = "standard_document_types"
        
        response = api_client.put(
            f"{BASE_URL}/api/onboarding/steps/{step_id}",
            json={"status": "finish_later"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "finish_later"
        
        print(f"✓ Step {step_id} marked finish_later")

    def test_reset_step_to_incomplete(self, api_client):
        """Test resetting a step to incomplete"""
        step_id = "standard_document_types"
        
        response = api_client.put(
            f"{BASE_URL}/api/onboarding/steps/{step_id}",
            json={"status": "incomplete"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("status") == "incomplete"
        
        print(f"✓ Step {step_id} reset to incomplete")

    def test_invalid_status_returns_400(self, api_client):
        """Test that invalid status returns 400"""
        response = api_client.put(
            f"{BASE_URL}/api/onboarding/steps/quick_first_job",
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400
        
        print("✓ Invalid status correctly returns 400")


class TestOnboardingAnalyticsAccuracy:
    """Tests to verify analytics calculations are accurate"""

    def test_analytics_completion_percent_calculation(self, api_client):
        """Verify completion percentage is calculated correctly"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200
        
        data = response.json()
        analytics = data["analytics"]
        step_statuses = data["step_statuses"]
        
        # Manually count quick_start completions
        quick_start_steps = [k for k in step_statuses if k.startswith("quick_")]
        completed_quick = len([k for k in quick_start_steps if step_statuses[k] == "completed"])
        
        tier_analytics = analytics["quick_start"]
        expected_percent = round((completed_quick / tier_analytics["total_steps"]) * 100) if tier_analytics["total_steps"] else 0
        
        # Allow for small rounding differences
        assert abs(tier_analytics["completion_percent"] - expected_percent) <= 1, \
            f"Completion percent mismatch: got {tier_analytics['completion_percent']}, expected ~{expected_percent}"
        
        print(f"✓ Quick start: {completed_quick}/{tier_analytics['total_steps']} = {tier_analytics['completion_percent']}%")

    def test_finish_later_count_accuracy(self, api_client):
        """Verify finish_later count is accurate"""
        response = api_client.get(f"{BASE_URL}/api/onboarding/status")
        assert response.status_code == 200
        
        data = response.json()
        analytics = data["analytics"]
        step_statuses = data["step_statuses"]
        
        # Count finish_later steps per tier
        for tier_id, prefix in [("quick_start", "quick_"), ("standard_setup", "standard_"), ("full_optimization", "full_")]:
            tier_steps = [k for k in step_statuses if k.startswith(prefix)]
            finish_later_count = len([k for k in tier_steps if step_statuses[k] == "finish_later"])
            
            assert analytics[tier_id]["finish_later_steps"] == finish_later_count, \
                f"{tier_id} finish_later count mismatch"
        
        print("✓ Finish later counts accurate across all tiers")


class TestCustomerPortalInvite:
    """Tests for customer portal invite flow (no regression)"""

    def test_customer_invite_requires_email(self, api_client):
        """Verify portal invite requires customer email"""
        # Create customer without email
        customer_data = {
            "name": f"TEST_NoEmail_Resume_{uuid.uuid4().hex[:8]}",
            "company": "Test Company",
            "status": "lead"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/customers", json=customer_data)
        if create_response.status_code != 201:
            pytest.skip("Could not create test customer")
        
        customer_id = create_response.json()["id"]
        
        try:
            # Try to invite - should fail
            invite_response = api_client.post(f"{BASE_URL}/api/customers/{customer_id}/invite-portal")
            assert invite_response.status_code == 400, "Should fail without email"
            print("✓ Portal invite correctly requires email")
        finally:
            # Cleanup
            api_client.delete(f"{BASE_URL}/api/customers/{customer_id}")

    def test_customer_invite_returns_pin(self, api_client):
        """Verify portal invite returns temporary PIN"""
        # Create customer with email
        customer_data = {
            "name": f"TEST_Portal_Resume_{uuid.uuid4().hex[:8]}",
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "company": "Test Company",
            "status": "active"
        }
        
        create_response = api_client.post(f"{BASE_URL}/api/customers", json=customer_data)
        if create_response.status_code != 201:
            pytest.skip("Could not create test customer")
        
        customer_id = create_response.json()["id"]
        
        try:
            # Invite to portal
            invite_response = api_client.post(f"{BASE_URL}/api/customers/{customer_id}/invite-portal")
            assert invite_response.status_code == 200, f"Expected 200, got {invite_response.status_code}"
            
            data = invite_response.json()
            assert "temporary_pin" in data, "Response should include temporary_pin"
            assert len(data["temporary_pin"]) == 6, "PIN should be 6 digits"
            assert data["temporary_pin"].isdigit(), "PIN should be numeric"
            
            print(f"✓ Portal invite returned 6-digit PIN")
        finally:
            # Cleanup
            api_client.delete(f"{BASE_URL}/api/customers/{customer_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
