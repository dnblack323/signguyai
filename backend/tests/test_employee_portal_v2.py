"""
Employee Portal Backend Tests - V2 (Production Integration Focus)

Tests for Employee Portal + Production Tracking features:
- Employee authentication (email/PIN login)
- GET /api/employee-portal/jobs - assigned jobs
- GET /api/employee-portal/work-summary - work summary
- GET /api/employee-portal/jobs/{job_id} - job detail with timelines
- POST /api/employee-portal/jobs/{job_id}/timeline/{timeline_id}/stage/{stage_order} - stage actions (start/pause/complete)
- Job assignment via admin API
- Tenant scoping for employee data
- Production timeline stage assignment in admin UI
- No regression on time clock and pay/profile routes
"""

import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Admin credentials
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD

# Test employee credentials (seeded)
TEST_EMPLOYEE_EMAIL = "portal-stage@test.com"
TEST_EMPLOYEE_PIN = "2468"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed - skipping tests")


@pytest.fixture(scope="module")
def employee_data(admin_token):
    """Create test employee for portal testing"""
    # First check if employee already exists
    check_response = requests.post(
        f"{BASE_URL}/api/employee-portal/auth/login",
        json={"email": TEST_EMPLOYEE_EMAIL, "pin": TEST_EMPLOYEE_PIN}
    )
    
    if check_response.status_code == 200:
        data = check_response.json()
        return {"id": data["employee_id"], "name": data["employee_name"], "tenant_id": data["tenant_id"]}
    
    # Create the employee if doesn't exist
    employee_payload = {
        "name": "TEST_PortalStageWorker",
        "email": TEST_EMPLOYEE_EMAIL,
        "phone": "5555552468",
        "role": "production",
        "hourly_rate": 20.0,
        "pin": TEST_EMPLOYEE_PIN,
        "is_active": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/employees",
        json=employee_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        return {"id": data["id"], "name": data["name"], "tenant_id": data.get("tenant_id")}
    
    pytest.skip(f"Failed to create test employee: {response.text}")


@pytest.fixture(scope="module")
def employee_token(employee_data):
    """Get employee JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/employee-portal/auth/login",
        json={"email": TEST_EMPLOYEE_EMAIL, "pin": TEST_EMPLOYEE_PIN}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Employee authentication failed: {response.text}")


@pytest.fixture(scope="module")
def test_job_with_assignment(admin_token, employee_data):
    """Create a test job and assign the employee to it"""
    # Get existing jobs first
    jobs_response = requests.get(
        f"{BASE_URL}/api/jobs?filter_type=all",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    if jobs_response.status_code == 200:
        jobs = jobs_response.json()
        if len(jobs) > 0:
            # Use existing job
            job = jobs[0]
            job_id = job["id"]
            
            # Assign employee to job
            assign_response = requests.put(
                f"{BASE_URL}/api/jobs/{job_id}/assign-employees",
                json={"employee_ids": [employee_data["id"]]},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if assign_response.status_code == 200:
                return job_id
    
    pytest.skip("No jobs available for testing or failed to assign employee")


class TestEmployeePortalAuthentication:
    """Employee Portal authentication tests"""
    
    def test_employee_login_success(self):
        """Test successful employee login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": TEST_EMPLOYEE_EMAIL, "pin": TEST_EMPLOYEE_PIN}
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "employee_id" in data
        assert "employee_name" in data
        assert "tenant_id" in data
        
        # Verify data types
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        print(f"SUCCESS: Employee login - {data['employee_name']}")
    
    def test_employee_login_invalid_email(self):
        """Test login failure with invalid email"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": "nonexistent@invalid.com", "pin": TEST_EMPLOYEE_PIN}
        )
        
        assert response.status_code == 401
        print("SUCCESS: Invalid email correctly rejected")
    
    def test_employee_login_invalid_pin(self):
        """Test login failure with invalid PIN"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": TEST_EMPLOYEE_EMAIL, "pin": "0000"}
        )
        
        assert response.status_code == 401
        print("SUCCESS: Invalid PIN correctly rejected")


class TestEmployeePortalAssignedJobs:
    """Tests for GET /api/employee-portal/jobs - assigned jobs list"""
    
    def test_get_assigned_jobs_success(self, employee_token, test_job_with_assignment):
        """Test getting list of jobs assigned to the employee"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/jobs",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200, f"Failed to get assigned jobs: {response.text}"
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        print(f"SUCCESS: Got {len(data)} assigned jobs")
        
        # If jobs assigned, verify structure
        if len(data) > 0:
            job = data[0]
            assert "id" in job
            assert "job_number" in job
            assert "job_name" in job
            assert "customer_name" in job
            assert "job_type" in job
            assert "priority" in job
            print(f"SUCCESS: Job structure verified - {job['job_name']}")
    
    def test_get_assigned_jobs_unauthorized(self):
        """Test assigned jobs access without token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/jobs")
        
        assert response.status_code == 401
        print("SUCCESS: Unauthorized access correctly rejected")


class TestEmployeePortalWorkSummary:
    """Tests for GET /api/employee-portal/work-summary"""
    
    def test_get_work_summary_success(self, employee_token):
        """Test getting employee work summary"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/work-summary",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200, f"Failed to get work summary: {response.text}"
        data = response.json()
        
        # Verify work summary structure
        assert "today_hours_worked" in data
        assert "week_hours_worked" in data
        assert "completed_stages_today" in data
        assert "assigned_jobs_count" in data
        
        # Verify data types
        assert isinstance(data["today_hours_worked"], (int, float))
        assert isinstance(data["week_hours_worked"], (int, float))
        assert isinstance(data["completed_stages_today"], int)
        assert isinstance(data["assigned_jobs_count"], int)
        
        print(f"SUCCESS: Work summary - Today: {data['today_hours_worked']}h, Week: {data['week_hours_worked']}h, Jobs: {data['assigned_jobs_count']}")
    
    def test_get_work_summary_unauthorized(self):
        """Test work summary access without token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/work-summary")
        
        assert response.status_code == 401
        print("SUCCESS: Unauthorized access correctly rejected")


class TestEmployeePortalJobDetail:
    """Tests for GET /api/employee-portal/jobs/{job_id}"""
    
    def test_get_job_detail_success(self, employee_token, test_job_with_assignment):
        """Test getting assigned job detail"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/jobs/{test_job_with_assignment}",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200, f"Failed to get job detail: {response.text}"
        data = response.json()
        
        # Verify job detail structure
        assert "job" in data
        assert "customer_name" in data
        assert "job_items" in data
        assert "timelines" in data
        
        # Verify job data
        assert data["job"]["id"] == test_job_with_assignment
        print(f"SUCCESS: Job detail retrieved - {data['job'].get('name', 'Unknown')}")
        print(f"  - Customer: {data['customer_name']}")
        print(f"  - Items: {len(data['job_items'])}")
        print(f"  - Timelines: {len(data['timelines'])}")
    
    def test_get_unassigned_job_returns_404(self, employee_token):
        """Test that unassigned job returns 404 - tenant scoping"""
        fake_job_id = str(uuid.uuid4())
        
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/jobs/{fake_job_id}",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 404
        print("SUCCESS: Unassigned job correctly returns 404")
    
    def test_get_job_detail_unauthorized(self, test_job_with_assignment):
        """Test job detail access without token"""
        response = requests.get(f"{BASE_URL}/api/employee-portal/jobs/{test_job_with_assignment}")
        
        assert response.status_code == 401
        print("SUCCESS: Unauthorized access correctly rejected")


class TestEmployeePortalStageActions:
    """Tests for POST /api/employee-portal/jobs/{job_id}/timeline/{timeline_id}/stage/{stage_order}"""
    
    @pytest.fixture
    def job_with_timeline(self, admin_token, employee_token, test_job_with_assignment):
        """Get job detail with timelines for stage action tests"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/jobs/{test_job_with_assignment}",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["timelines"]:
                return {
                    "job_id": test_job_with_assignment,
                    "timeline_id": data["timelines"][0]["id"],
                    "stages": data["timelines"][0].get("stages", [])
                }
        
        # If no timeline, we can still test the API - it should return 404 for timeline
        return {
            "job_id": test_job_with_assignment,
            "timeline_id": None,
            "stages": []
        }
    
    def test_stage_start_action(self, employee_token, job_with_timeline):
        """Test starting a stage"""
        if not job_with_timeline["timeline_id"]:
            pytest.skip("No timeline available for stage action test")
        
        # Find a pending stage
        pending_stage = None
        for stage in job_with_timeline["stages"]:
            if stage.get("status") in ["pending", "paused"]:
                pending_stage = stage
                break
        
        if not pending_stage:
            pytest.skip("No pending stage available for test")
        
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/jobs/{job_with_timeline['job_id']}/timeline/{job_with_timeline['timeline_id']}/stage/{pending_stage['stage_order']}",
            json={"action": "start"},
            headers={"Authorization": f"Bearer {employee_token}", "Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Failed to start stage: {response.text}"
        data = response.json()
        
        assert "message" in data
        assert "Stage started" in data["message"]
        print(f"SUCCESS: Stage {pending_stage['stage_order']} started")
    
    def test_stage_pause_action(self, employee_token, job_with_timeline):
        """Test pausing a stage"""
        if not job_with_timeline["timeline_id"]:
            pytest.skip("No timeline available for stage action test")
        
        # Find an in_progress stage
        active_stage = None
        for stage in job_with_timeline["stages"]:
            if stage.get("status") == "in_progress":
                active_stage = stage
                break
        
        if not active_stage:
            # Start a stage first
            pending_stage = next((s for s in job_with_timeline["stages"] if s.get("status") in ["pending", "paused"]), None)
            if pending_stage:
                # Start it
                requests.post(
                    f"{BASE_URL}/api/employee-portal/jobs/{job_with_timeline['job_id']}/timeline/{job_with_timeline['timeline_id']}/stage/{pending_stage['stage_order']}",
                    json={"action": "start"},
                    headers={"Authorization": f"Bearer {employee_token}", "Content-Type": "application/json"}
                )
                active_stage = pending_stage
            else:
                pytest.skip("No stage available for pause test")
        
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/jobs/{job_with_timeline['job_id']}/timeline/{job_with_timeline['timeline_id']}/stage/{active_stage['stage_order']}",
            json={"action": "pause"},
            headers={"Authorization": f"Bearer {employee_token}", "Content-Type": "application/json"}
        )
        
        assert response.status_code == 200, f"Failed to pause stage: {response.text}"
        data = response.json()
        
        assert "message" in data
        assert "Stage paused" in data["message"]
        print(f"SUCCESS: Stage {active_stage['stage_order']} paused")
    
    def test_stage_invalid_action(self, employee_token, job_with_timeline):
        """Test invalid stage action"""
        if not job_with_timeline["timeline_id"]:
            pytest.skip("No timeline available for stage action test")
        
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/jobs/{job_with_timeline['job_id']}/timeline/{job_with_timeline['timeline_id']}/stage/1",
            json={"action": "invalid_action"},
            headers={"Authorization": f"Bearer {employee_token}", "Content-Type": "application/json"}
        )
        
        assert response.status_code == 400
        print("SUCCESS: Invalid action correctly rejected")
    
    def test_stage_action_unauthorized(self, job_with_timeline):
        """Test stage action without token"""
        if not job_with_timeline["timeline_id"]:
            pytest.skip("No timeline available")
        
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/jobs/{job_with_timeline['job_id']}/timeline/{job_with_timeline['timeline_id']}/stage/1",
            json={"action": "start"}
        )
        
        assert response.status_code == 401
        print("SUCCESS: Unauthorized access correctly rejected")


class TestAdminJobAssignment:
    """Tests for admin job assignment persistence"""
    
    def test_assign_employees_to_job(self, admin_token, employee_data):
        """Test assigning employees to a job via admin API"""
        # Get a job to assign
        jobs_response = requests.get(
            f"{BASE_URL}/api/jobs?filter_type=all",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert jobs_response.status_code == 200
        jobs = jobs_response.json()
        
        if len(jobs) == 0:
            pytest.skip("No jobs available for assignment test")
        
        job_id = jobs[0]["id"]
        
        # Assign employee
        response = requests.put(
            f"{BASE_URL}/api/jobs/{job_id}/assign-employees",
            json={"employee_ids": [employee_data["id"]]},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Failed to assign employees: {response.text}"
        data = response.json()
        
        assert "assigned_employees" in data
        assert len(data["assigned_employees"]) > 0
        
        # Verify assignment persists
        details_response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert details_response.status_code == 200
        details = details_response.json()
        
        assigned_ids = [e["id"] for e in details.get("assigned_employee_details", [])]
        assert employee_data["id"] in assigned_ids
        
        print("SUCCESS: Employee assigned to job and persisted")
    
    def test_job_details_includes_assigned_employees(self, admin_token, employee_data, test_job_with_assignment):
        """Test that job details includes assigned_employee_details"""
        response = requests.get(
            f"{BASE_URL}/api/jobs/{test_job_with_assignment}/details",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Failed to get job details: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "job" in data
        assert "assigned_employee_details" in data
        
        # Verify assigned employees
        assigned_ids = [e["id"] for e in data["assigned_employee_details"]]
        assert employee_data["id"] in assigned_ids
        
        print(f"SUCCESS: Job details includes {len(data['assigned_employee_details'])} assigned employees")


class TestNoRegressionTimeClock:
    """No regression tests for existing time clock functionality"""
    
    def test_time_clock_status(self, employee_token):
        """Test time clock status endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/time-clock/status",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "is_clocked_in" in data
        assert "total_hours_today" in data
        print(f"SUCCESS: Time clock status - clocked_in: {data['is_clocked_in']}, hours: {data['total_hours_today']}")
    
    def test_time_clock_punch(self, employee_token):
        """Test time clock punch endpoint still works"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/time-clock/punch?action=start_work",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "log" in data
        print(f"SUCCESS: Time clock punch - {data['log']['action']}")
    
    def test_time_clock_history(self, employee_token):
        """Test time clock history endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/time-clock/history?days=7",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"SUCCESS: Time clock history - {len(data)} entries")


class TestNoRegressionPayProfile:
    """No regression tests for pay and profile endpoints"""
    
    def test_employee_profile(self, employee_token):
        """Test employee profile endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/profile",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "name" in data
        assert "email" in data
        assert "hourly_rate" in data
        print(f"SUCCESS: Profile - {data['name']} (rate: ${data['hourly_rate']}/hr)")
    
    def test_pay_summary(self, employee_token):
        """Test pay summary endpoint still works"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/pay/summary",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "current_period_earnings" in data
        assert "ytd_earnings" in data
        assert "balance_owed" in data
        print(f"SUCCESS: Pay summary - YTD: ${data['ytd_earnings']}, Balance: ${data['balance_owed']}")


class TestProductionTimelineSettings:
    """Tests for production timeline settings endpoint - regression check"""
    
    def test_get_production_timeline_settings(self, admin_token):
        """Test production timeline settings endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/production-timeline/settings",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "workflow_mode" in data
        print(f"SUCCESS: Production timeline settings - workflow_mode: {data['workflow_mode']}")
    
    def test_get_production_timeline_templates(self, admin_token):
        """Test production timeline templates endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/production-timeline/templates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        print(f"SUCCESS: Production timeline templates - {len(data)} templates")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
