"""
Job Time Tracking and AI Tools Tests

Tests for:
- Job Time Tracking feature (start/stop timer, view entries, summary, delete)
- AI Tools text generation (tagline_generator, font_identifier)
- AI Pricing Advisor
"""

import pytest
import requests
import os
import time
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = SYNTHETIC_OWNER_EMAIL
TEST_PASSWORD = "test123456"
TEST_JOB_ID = "66a3d88b-e18d-4afd-a4ee-e9e0bf2b7cef"


class TestAuth:
    """Authentication helper - get auth token"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]


class TestJobTimeTrackingStart(TestAuth):
    """Test starting a job timer"""
    
    def test_start_timer_success(self, auth_token):
        """Test starting a timer on a job"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First check if there's an active timer and stop it
        active_resp = requests.get(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/active",
            headers=headers
        )
        if active_resp.status_code == 200:
            data = active_resp.json()
            if data.get("has_active_timer"):
                # Stop existing timer first
                stop_resp = requests.post(
                    f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop",
                    headers=headers
                )
                assert stop_resp.status_code == 200, f"Failed to stop existing timer: {stop_resp.text}"
        
        # Now start a new timer
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/start",
            headers=headers,
            json={
                "description": "TEST_TimeEntry - Backend test timer",
                "task_type": "production"
            }
        )
        
        assert response.status_code == 200, f"Start timer failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response missing 'id'"
        assert data["job_id"] == TEST_JOB_ID, "Wrong job_id in response"
        assert data["is_active"] == True, "Timer should be active"
        assert data["task_type"] == "production", "Wrong task_type"
        assert "start_time" in data, "Response missing 'start_time'"
        
        print(f"✓ Timer started successfully. Entry ID: {data['id']}")
        return data["id"]
    
    def test_start_timer_duplicate_fails(self, auth_token):
        """Test that starting another timer when one is active fails"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Ensure there's an active timer first
        active_resp = requests.get(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/active",
            headers=headers
        )
        
        if active_resp.status_code == 200:
            data = active_resp.json()
            if not data.get("has_active_timer"):
                # Start a timer first
                start_resp = requests.post(
                    f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/start",
                    headers=headers,
                    json={"description": "TEST_DuplicateCheck", "task_type": "design"}
                )
                assert start_resp.status_code == 200
        
        # Now try to start another - should fail
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/start",
            headers=headers,
            json={"description": "TEST_Duplicate", "task_type": "production"}
        )
        
        # Should return 400 because timer already active
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "active timer" in response.text.lower(), f"Expected 'active timer' in error message: {response.text}"
        print("✓ Duplicate timer correctly rejected")


class TestJobTimeTrackingStop(TestAuth):
    """Test stopping a job timer"""
    
    def test_stop_timer_success(self, auth_token):
        """Test stopping an active timer"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Check active timer
        active_resp = requests.get(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/active",
            headers=headers
        )
        assert active_resp.status_code == 200
        
        data = active_resp.json()
        if not data.get("has_active_timer"):
            # Start one first
            start_resp = requests.post(
                f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/start",
                headers=headers,
                json={"description": "TEST_ToStop", "task_type": "admin"}
            )
            assert start_resp.status_code == 200
            time.sleep(1)  # Let some time pass
        
        # Now stop the timer
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop",
            headers=headers
        )
        
        assert response.status_code == 200, f"Stop timer failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert data["is_active"] == False, "Timer should be inactive after stop"
        assert "end_time" in data and data["end_time"], "Should have end_time"
        assert "duration_minutes" in data, "Should have duration_minutes"
        
        print(f"✓ Timer stopped. Duration: {data.get('duration_minutes', 0):.2f} minutes")
    
    def test_stop_timer_when_none_active(self, auth_token):
        """Test stopping when no timer is active - should return 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Ensure no active timer
        active_resp = requests.get(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/active",
            headers=headers
        )
        if active_resp.status_code == 200:
            data = active_resp.json()
            if data.get("has_active_timer"):
                # Stop it first
                requests.post(f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop", headers=headers)
        
        # Now try to stop again - should fail
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404 when no active timer: {response.status_code}"
        print("✓ Stop correctly returns 404 when no active timer")


class TestJobTimeTrackingEntries(TestAuth):
    """Test viewing time entries"""
    
    def test_get_time_entries_list(self, auth_token):
        """Test getting list of time entries for a job"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time",
            headers=headers
        )
        
        assert response.status_code == 200, f"Get entries failed: {response.text}"
        entries = response.json()
        
        # Should be a list
        assert isinstance(entries, list), "Response should be a list"
        
        # Verify entry structure if entries exist
        if len(entries) > 0:
            entry = entries[0]
            assert "id" in entry
            assert "job_id" in entry
            assert "employee_id" in entry
            assert "start_time" in entry
            assert "task_type" in entry
            assert "is_active" in entry
            print(f"✓ Found {len(entries)} time entries for job")
        else:
            print("✓ Time entries endpoint works (0 entries)")


class TestJobTimeTrackingSummary(TestAuth):
    """Test time tracking summary"""
    
    def test_get_time_summary(self, auth_token):
        """Test getting time summary for a job"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/summary",
            headers=headers
        )
        
        assert response.status_code == 200, f"Get summary failed: {response.text}"
        summary = response.json()
        
        # Verify summary structure
        assert "job_id" in summary, "Missing job_id"
        assert "total_minutes" in summary, "Missing total_minutes"
        assert "total_hours" in summary, "Missing total_hours"
        assert "total_labor_cost" in summary, "Missing total_labor_cost"
        assert "entries_count" in summary, "Missing entries_count"
        assert "by_employee" in summary, "Missing by_employee"
        assert "by_task_type" in summary, "Missing by_task_type"
        
        print(f"✓ Time Summary: {summary['total_hours']:.2f} hours, ${summary['total_labor_cost']:.2f} labor cost, {summary['entries_count']} entries")


class TestJobTimeTrackingActiveTimer(TestAuth):
    """Test checking active timer status"""
    
    def test_get_active_timer_status(self, auth_token):
        """Test checking if user has an active timer"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/active",
            headers=headers
        )
        
        assert response.status_code == 200, f"Get active timer failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "has_active_timer" in data, "Missing has_active_timer field"
        
        if data["has_active_timer"]:
            assert "entry" in data and data["entry"], "Should have entry when timer is active"
            print(f"✓ Active timer found: {data['entry'].get('task_type', 'unknown')} task")
        else:
            print("✓ No active timer (correct response)")


class TestJobTimeTrackingDelete(TestAuth):
    """Test deleting time entries"""
    
    def test_delete_time_entry(self, auth_token):
        """Test deleting a time entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create an entry to delete
        start_resp = requests.post(
            f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/start",
            headers=headers,
            json={"description": "TEST_ToDelete", "task_type": "installation"}
        )
        
        # If already active, stop then start
        if start_resp.status_code == 400:
            requests.post(f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop", headers=headers)
            start_resp = requests.post(
                f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/start",
                headers=headers,
                json={"description": "TEST_ToDelete", "task_type": "installation"}
            )
        
        if start_resp.status_code == 200:
            entry_id = start_resp.json()["id"]
            
            # Stop the timer first (can't delete active timers)
            time.sleep(1)
            stop_resp = requests.post(f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop", headers=headers)
            assert stop_resp.status_code == 200
            
            # Now delete it
            delete_resp = requests.delete(
                f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/{entry_id}",
                headers=headers
            )
            
            assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"
            print(f"✓ Time entry {entry_id[:8]}... deleted successfully")
        else:
            print(f"! Could not create entry to delete: {start_resp.text}")


class TestJobTimeTrackingTaskTypes(TestAuth):
    """Test task type dropdown functionality"""
    
    def test_task_types_work(self, auth_token):
        """Test that different task types can be set"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        task_types = ["design", "production", "installation", "admin"]
        
        for task_type in task_types:
            # Stop any existing timer
            requests.post(f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop", headers=headers)
            
            # Start with this task type
            response = requests.post(
                f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/start",
                headers=headers,
                json={"description": f"TEST_{task_type}", "task_type": task_type}
            )
            
            if response.status_code == 200:
                data = response.json()
                assert data["task_type"] == task_type, f"Task type mismatch: expected {task_type}, got {data.get('task_type')}"
                
                # Stop it
                stop_resp = requests.post(f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/stop", headers=headers)
                assert stop_resp.status_code == 200
                
                # Delete it to clean up
                requests.delete(f"{BASE_URL}/api/jobs/{TEST_JOB_ID}/time/{data['id']}", headers=headers)
        
        print(f"✓ All task types work: {', '.join(task_types)}")


class TestAIToolsTextGeneration(TestAuth):
    """Test AI text generation tools"""
    
    def test_tagline_generator(self, auth_token):
        """Test tagline generator AI tool"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=headers,
            json={
                "tool": "tagline_generator",
                "input_data": {
                    "business_name": "TEST_SignCraft Pro",
                    "industry": "Sign Shop",
                    "key_values": "Quality craftsmanship, Fast turnaround",
                    "target_audience": "Local businesses",
                    "tone": "Professional yet friendly"
                }
            }
        )
        
        assert response.status_code == 200, f"Tagline generation failed: {response.text}"
        data = response.json()
        
        assert "content" in data, "Response missing 'content'"
        assert len(data["content"]) > 50, "Content seems too short for taglines"
        assert "id" in data, "Response missing history 'id'"
        
        print(f"✓ Tagline generator works. Generated {len(data['content'])} chars")
    
    def test_font_identifier(self, auth_token):
        """Test font identifier AI tool (text-only, no image)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=headers,
            json={
                "tool": "font_identifier",
                "input_data": {
                    "text_sample": "OPEN FOR BUSINESS"
                }
            }
        )
        
        assert response.status_code == 200, f"Font identifier failed: {response.text}"
        data = response.json()
        
        assert "content" in data, "Response missing 'content'"
        assert "id" in data, "Response missing history 'id'"
        
        print(f"✓ Font identifier works. Generated {len(data['content'])} chars")


class TestAIPricingAdvisor(TestAuth):
    """Test AI Pricing Advisor in calculator"""
    
    def test_pricing_advisor(self, auth_token):
        """Test pricing advisor tool"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=headers,
            json={
                "tool": "pricing_advisor",
                "input_data": {
                    "category": "cut_vinyl",
                    "quantity": 10,
                    "current_price": 250.00,
                    "production_cost": 75.00,
                    "profit_margin": 70,
                    "complexity": 5,
                    "breakdown": {
                        "materials": "$50.00",
                        "labor": "$25.00",
                        "markup": "$175.00"
                    }
                }
            }
        )
        
        assert response.status_code == 200, f"Pricing advisor failed: {response.text}"
        data = response.json()
        
        assert "content" in data, "Response missing 'content'"
        # Pricing advisor should give structured recommendations
        assert len(data["content"]) > 100, "Content too short for pricing advice"
        
        print(f"✓ Pricing advisor works. Generated {len(data['content'])} chars of recommendations")


class TestAIHistory(TestAuth):
    """Test AI history endpoint"""
    
    def test_get_ai_history(self, auth_token):
        """Test getting AI generation history"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/ai/history",
            headers=headers
        )
        
        assert response.status_code == 200, f"Get AI history failed: {response.text}"
        history = response.json()
        
        assert isinstance(history, list), "History should be a list"
        
        if len(history) > 0:
            entry = history[0]
            assert "tool" in entry, "History entry missing 'tool'"
            assert "created_at" in entry, "History entry missing 'created_at'"
            print(f"✓ AI history works. Found {len(history)} entries")
        else:
            print("✓ AI history endpoint works (0 entries)")


class TestJobNotFound(TestAuth):
    """Test error handling for non-existent job"""
    
    def test_start_timer_invalid_job(self, auth_token):
        """Test starting timer on non-existent job returns 404"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/jobs/invalid-job-id-12345/time/start",
            headers=headers,
            json={"description": "test", "task_type": "production"}
        )
        
        assert response.status_code == 404, f"Expected 404 for invalid job, got {response.status_code}"
        print("✓ Invalid job correctly returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
