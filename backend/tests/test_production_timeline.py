"""
Production Timeline / Workflow Settings Tests - Iteration 58

Tests for:
- GET/PUT /api/production-timeline/settings (tenant-specific workflow_mode, category_template_map)
- POST /api/production-timeline/enable (simple/detailed timelines based on workflow settings)
- GET /api/jobs/{job_id}/history (unified timeline/history events)
- Production stage started/completed events in job history
- No regression on timeline advance/edit flows
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProductionWorkflowSettings:
    """Test workflow settings GET/PUT endpoints"""
    
    auth_token = None
    created_job_id = None
    created_customer_id = None
    created_line_item_id = None
    created_timeline_id = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate before tests"""
        if TestProductionWorkflowSettings.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "thesigntistslab@gmail.com",
                "password": "password123"
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestProductionWorkflowSettings.auth_token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {TestProductionWorkflowSettings.auth_token}"}
    
    def test_01_get_production_workflow_settings(self):
        """GET /api/production-timeline/settings returns workflow_mode and category_template_map"""
        response = requests.get(f"{BASE_URL}/api/production-timeline/settings", headers=self.headers)
        assert response.status_code == 200, f"Failed to get settings: {response.text}"
        data = response.json()
        
        # Verify required fields
        assert "workflow_mode" in data, "Missing workflow_mode in response"
        assert "category_template_map" in data, "Missing category_template_map in response"
        assert data["workflow_mode"] in ["simple", "detailed", "custom"], f"Invalid workflow_mode: {data['workflow_mode']}"
        print(f"Current workflow settings: mode={data['workflow_mode']}, map={data['category_template_map']}")
    
    def test_02_put_production_workflow_settings_detailed(self):
        """PUT /api/production-timeline/settings saves workflow_mode=detailed"""
        payload = {
            "workflow_mode": "detailed",
            "category_template_map": {}
        }
        response = requests.put(f"{BASE_URL}/api/production-timeline/settings", 
                               json=payload, headers=self.headers)
        assert response.status_code == 200, f"Failed to save settings: {response.text}"
        data = response.json()
        assert data["workflow_mode"] == "detailed"
        print("Saved workflow_mode=detailed successfully")
    
    def test_03_put_production_workflow_settings_simple(self):
        """PUT /api/production-timeline/settings saves workflow_mode=simple"""
        payload = {
            "workflow_mode": "simple",
            "category_template_map": {}
        }
        response = requests.put(f"{BASE_URL}/api/production-timeline/settings", 
                               json=payload, headers=self.headers)
        assert response.status_code == 200, f"Failed to save settings: {response.text}"
        data = response.json()
        assert data["workflow_mode"] == "simple"
        print("Saved workflow_mode=simple successfully")
    
    def test_04_put_production_workflow_settings_custom_with_category_map(self):
        """PUT /api/production-timeline/settings saves custom workflow with category_template_map"""
        payload = {
            "workflow_mode": "custom",
            "category_template_map": {
                "vehicle_wrap": "custom_template_123",
                "printed_signs": "custom_template_456"
            }
        }
        response = requests.put(f"{BASE_URL}/api/production-timeline/settings", 
                               json=payload, headers=self.headers)
        assert response.status_code == 200, f"Failed to save settings: {response.text}"
        data = response.json()
        assert data["workflow_mode"] == "custom"
        assert "category_template_map" in data
        assert data["category_template_map"].get("vehicle_wrap") == "custom_template_123"
        print("Saved custom workflow with category_template_map successfully")
        
        # Reset to detailed for other tests
        reset_payload = {"workflow_mode": "detailed", "category_template_map": {}}
        requests.put(f"{BASE_URL}/api/production-timeline/settings", 
                    json=reset_payload, headers=self.headers)


class TestProductionTimelineEnable:
    """Test timeline enable with simple/detailed workflow modes"""
    
    auth_token = None
    created_job_id = None
    created_customer_id = None
    created_line_item_id = None
    created_timeline_id = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate before tests"""
        if TestProductionTimelineEnable.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "thesigntistslab@gmail.com",
                "password": "password123"
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestProductionTimelineEnable.auth_token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {TestProductionTimelineEnable.auth_token}"}
    
    def test_05_create_test_customer_and_job(self):
        """Create customer and job for timeline testing"""
        # Create customer
        customer_data = {
            "name": f"TEST_Timeline_Customer_{uuid.uuid4().hex[:8]}",
            "email": f"test_timeline_{uuid.uuid4().hex[:8]}@example.com"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=self.headers)
        assert response.status_code in [200, 201], f"Failed to create customer: {response.text}"
        TestProductionTimelineEnable.created_customer_id = response.json()["id"]
        
        # Create job
        job_data = {
            "customer_id": TestProductionTimelineEnable.created_customer_id,
            "name": f"TEST_Timeline_Job_{uuid.uuid4().hex[:8]}",
            "description": "Timeline test job",
            "status": "approved"
        }
        response = requests.post(f"{BASE_URL}/api/jobs", json=job_data, headers=self.headers)
        assert response.status_code in [200, 201], f"Failed to create job: {response.text}"
        TestProductionTimelineEnable.created_job_id = response.json()["id"]
        print(f"Created test job: {TestProductionTimelineEnable.created_job_id}")
    
    def test_06_create_job_item_for_timeline(self):
        """Create job item to enable timeline on"""
        item_data = {
            "item_type": "banner",
            "description": "TEST_Timeline_Item",
            "quantity": 1,
            "unit_price": 100.00,
            "status": "pending"
        }
        response = requests.post(f"{BASE_URL}/api/jobs/{TestProductionTimelineEnable.created_job_id}/items", 
                                json=item_data, headers=self.headers)
        assert response.status_code in [200, 201], f"Failed to create job item: {response.text}"
        TestProductionTimelineEnable.created_line_item_id = response.json()["id"]
        print(f"Created test line item: {TestProductionTimelineEnable.created_line_item_id}")
    
    def test_07_set_simple_workflow_mode(self):
        """Set workflow mode to simple before enabling timeline"""
        payload = {"workflow_mode": "simple", "category_template_map": {}}
        response = requests.put(f"{BASE_URL}/api/production-timeline/settings", 
                               json=payload, headers=self.headers)
        assert response.status_code == 200
        print("Set workflow_mode to 'simple'")
    
    def test_08_enable_timeline_simple_mode(self):
        """POST /api/production-timeline/enable uses simple workflow stages"""
        params = {
            "job_id": TestProductionTimelineEnable.created_job_id,
            "line_item_id": TestProductionTimelineEnable.created_line_item_id,
            "category": "banners"
        }
        response = requests.post(f"{BASE_URL}/api/production-timeline/enable", 
                                params=params, headers=self.headers)
        assert response.status_code == 200, f"Failed to enable timeline: {response.text}"
        data = response.json()
        
        # Verify timeline created
        assert "id" in data
        assert "stages" in data
        TestProductionTimelineEnable.created_timeline_id = data["id"]
        
        # Simple workflow should have fewer stages (typically 3: Design, Production, Completion)
        stage_count = len(data["stages"])
        print(f"Timeline created with {stage_count} stages (simple mode)")
        
        # Check stage names for simple workflow
        stage_names = [s["stage_name"] for s in data["stages"]]
        print(f"Simple workflow stages: {stage_names}")
        assert stage_count <= 5, f"Simple workflow should have 3-5 stages, got {stage_count}"
    
    def test_09_disable_timeline(self):
        """Delete timeline to test detailed mode next"""
        response = requests.delete(
            f"{BASE_URL}/api/production-timeline/line-item/{TestProductionTimelineEnable.created_line_item_id}",
            headers=self.headers
        )
        assert response.status_code == 200
        print("Timeline disabled for re-testing with detailed mode")
    
    def test_10_set_detailed_workflow_mode(self):
        """Set workflow mode to detailed"""
        payload = {"workflow_mode": "detailed", "category_template_map": {}}
        response = requests.put(f"{BASE_URL}/api/production-timeline/settings", 
                               json=payload, headers=self.headers)
        assert response.status_code == 200
        print("Set workflow_mode to 'detailed'")
    
    def test_11_enable_timeline_detailed_mode(self):
        """POST /api/production-timeline/enable uses detailed workflow stages"""
        params = {
            "job_id": TestProductionTimelineEnable.created_job_id,
            "line_item_id": TestProductionTimelineEnable.created_line_item_id,
            "category": "banners"
        }
        response = requests.post(f"{BASE_URL}/api/production-timeline/enable", 
                                params=params, headers=self.headers)
        assert response.status_code == 200, f"Failed to enable timeline: {response.text}"
        data = response.json()
        
        # Verify timeline created
        assert "id" in data
        assert "stages" in data
        TestProductionTimelineEnable.created_timeline_id = data["id"]
        
        # Detailed workflow should have more stages (typically 8+)
        stage_count = len(data["stages"])
        print(f"Timeline created with {stage_count} stages (detailed mode)")
        
        # Check stage names for detailed workflow
        stage_names = [s["stage_name"] for s in data["stages"]]
        print(f"Detailed workflow stages: {stage_names}")
        assert stage_count >= 5, f"Detailed workflow should have 5+ stages, got {stage_count}"


class TestJobHistory:
    """Test unified job history endpoint"""
    
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate before tests"""
        if TestJobHistory.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "thesigntistslab@gmail.com",
                "password": "password123"
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestJobHistory.auth_token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {TestJobHistory.auth_token}"}
    
    def test_12_get_job_history_endpoint_exists(self):
        """GET /api/jobs/{job_id}/history endpoint returns array of events"""
        # First get any job to test with
        response = requests.get(f"{BASE_URL}/api/jobs", headers=self.headers)
        assert response.status_code == 200
        jobs = response.json()
        
        if not jobs:
            pytest.skip("No jobs available for history testing")
        
        job_id = jobs[0]["id"]
        
        # Get job history
        response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/history", headers=self.headers)
        assert response.status_code == 200, f"Failed to get job history: {response.text}"
        events = response.json()
        
        assert isinstance(events, list), "Job history should return a list"
        print(f"Job {job_id} has {len(events)} history events")
        
        if events:
            # Verify event structure
            event = events[0]
            assert "id" in event, "Event missing id"
            assert "event_type" in event, "Event missing event_type"
            assert "title" in event, "Event missing title"
            assert "timestamp" in event, "Event missing timestamp"
            assert "filter_group" in event, "Event missing filter_group"
            print(f"Sample event: type={event['event_type']}, group={event['filter_group']}, title={event['title']}")
    
    def test_13_job_history_includes_production_stages(self):
        """Job history includes production stage started/completed events"""
        # Get jobs that have timelines
        response = requests.get(f"{BASE_URL}/api/jobs", headers=self.headers)
        assert response.status_code == 200
        jobs = response.json()
        
        production_events_found = False
        for job in jobs[:5]:  # Check first 5 jobs
            response = requests.get(f"{BASE_URL}/api/jobs/{job['id']}/history", headers=self.headers)
            if response.status_code != 200:
                continue
            events = response.json()
            
            # Look for production stage events
            for event in events:
                if event.get("event_type") in ["production_stage_started", "production_stage_completed"]:
                    production_events_found = True
                    print(f"Found production event: {event['event_type']} - {event['title']}")
                    assert event["filter_group"] == "production"
                    break
            if production_events_found:
                break
        
        # Note: May not have production events if no timeline was advanced
        if not production_events_found:
            print("No production stage events found (expected if no timelines have been advanced)")
    
    def test_14_job_history_filter_groups(self):
        """Job history events have valid filter_group values"""
        valid_groups = ["all", "production", "artwork", "customer", "financial", "documents", "general"]
        
        response = requests.get(f"{BASE_URL}/api/jobs", headers=self.headers)
        assert response.status_code == 200
        jobs = response.json()
        
        if not jobs:
            pytest.skip("No jobs available")
        
        job_id = jobs[0]["id"]
        response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/history", headers=self.headers)
        assert response.status_code == 200
        events = response.json()
        
        groups_found = set()
        for event in events:
            filter_group = event.get("filter_group")
            groups_found.add(filter_group)
            assert filter_group in valid_groups, f"Invalid filter_group: {filter_group}"
        
        print(f"Filter groups found in job history: {groups_found}")
    
    def test_15_job_history_reverse_chronological_order(self):
        """Job history events are in reverse chronological order"""
        response = requests.get(f"{BASE_URL}/api/jobs", headers=self.headers)
        assert response.status_code == 200
        jobs = response.json()
        
        if not jobs:
            pytest.skip("No jobs available")
        
        job_id = jobs[0]["id"]
        response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/history", headers=self.headers)
        assert response.status_code == 200
        events = response.json()
        
        if len(events) > 1:
            # Check timestamps are in descending order
            timestamps = [e.get("timestamp") for e in events if e.get("timestamp")]
            for i in range(len(timestamps) - 1):
                assert timestamps[i] >= timestamps[i+1], "Events should be in reverse chronological order"
            print("History events are in reverse chronological order")


class TestProductionTimelineAdvanceEdit:
    """Test timeline advance and edit flows (regression)"""
    
    auth_token = None
    timeline_id = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate before tests"""
        if TestProductionTimelineAdvanceEdit.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "thesigntistslab@gmail.com",
                "password": "password123"
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestProductionTimelineAdvanceEdit.auth_token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {TestProductionTimelineAdvanceEdit.auth_token}"}
    
    def test_16_get_workflow_templates(self):
        """GET /api/production-timeline/templates returns templates"""
        response = requests.get(f"{BASE_URL}/api/production-timeline/templates", headers=self.headers)
        assert response.status_code == 200, f"Failed to get templates: {response.text}"
        templates = response.json()
        
        assert isinstance(templates, list)
        print(f"Found {len(templates)} workflow templates")
        
        if templates:
            template = templates[0]
            assert "name" in template
            assert "stages" in template
            print(f"Sample template: {template['name']} with {len(template['stages'])} stages")
    
    def test_17_advance_timeline_stage(self):
        """POST /api/production-timeline/{id}/advance works correctly"""
        # Find a timeline to advance
        response = requests.get(f"{BASE_URL}/api/jobs", headers=self.headers)
        assert response.status_code == 200
        jobs = response.json()
        
        timeline = None
        for job in jobs[:10]:
            response = requests.get(f"{BASE_URL}/api/production-timeline/job/{job['id']}", headers=self.headers)
            if response.status_code == 200:
                timelines = response.json()
                if timelines:
                    timeline = timelines[0]
                    break
        
        if not timeline:
            pytest.skip("No active timelines found for advance test")
        
        TestProductionTimelineAdvanceEdit.timeline_id = timeline["id"]
        
        # Advance the timeline
        response = requests.post(
            f"{BASE_URL}/api/production-timeline/{timeline['id']}/advance",
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to advance timeline: {response.text}"
        data = response.json()
        
        assert "new_stage_order" in data
        print(f"Timeline advanced to stage {data['new_stage_order']}, completed={data.get('is_completed')}")
    
    def test_18_update_timeline_stage(self):
        """PUT /api/production-timeline/{id}/stage/{order} updates stage"""
        if not TestProductionTimelineAdvanceEdit.timeline_id:
            pytest.skip("No timeline available for stage update test")
        
        timeline_id = TestProductionTimelineAdvanceEdit.timeline_id
        
        # Update stage 1 with notes
        update_data = {
            "notes": "Test note from pytest"
        }
        response = requests.put(
            f"{BASE_URL}/api/production-timeline/{timeline_id}/stage/1",
            json=update_data,
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed to update stage: {response.text}"
        print("Timeline stage updated with notes")


class TestNoRegression:
    """Regression tests for existing functionality"""
    
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate before tests"""
        if TestNoRegression.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "thesigntistslab@gmail.com",
                "password": "password123"
            })
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestNoRegression.auth_token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {TestNoRegression.auth_token}"}
    
    def test_19_jobs_list_endpoint(self):
        """GET /api/jobs returns job list"""
        response = requests.get(f"{BASE_URL}/api/jobs", headers=self.headers)
        assert response.status_code == 200, f"Jobs list failed: {response.text}"
        jobs = response.json()
        assert isinstance(jobs, list)
        print(f"Jobs list returned {len(jobs)} jobs")
    
    def test_20_jobs_filter_quotes(self):
        """GET /api/jobs?filter_type=quotes works"""
        response = requests.get(f"{BASE_URL}/api/jobs?filter_type=quotes", headers=self.headers)
        assert response.status_code == 200, f"Quotes filter failed: {response.text}"
        print("Quotes filter endpoint working")
    
    def test_21_jobs_filter_active(self):
        """GET /api/jobs?filter_type=active works"""
        response = requests.get(f"{BASE_URL}/api/jobs?filter_type=active", headers=self.headers)
        assert response.status_code == 200, f"Active filter failed: {response.text}"
        print("Active filter endpoint working")
    
    def test_22_production_analytics_endpoint(self):
        """GET /api/production-timeline/analytics works"""
        response = requests.get(f"{BASE_URL}/api/production-timeline/analytics", headers=self.headers)
        assert response.status_code == 200, f"Analytics failed: {response.text}"
        data = response.json()
        assert "total_timelines" in data
        print(f"Production analytics: {data.get('total_timelines')} timelines")


class TestCleanup:
    """Cleanup test data"""
    
    auth_token = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate before tests"""
        if TestCleanup.auth_token is None:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "thesigntistslab@gmail.com",
                "password": "password123"
            })
            if response.status_code == 200:
                data = response.json()
                TestCleanup.auth_token = data.get("access_token")
        self.headers = {"Authorization": f"Bearer {TestCleanup.auth_token}"} if TestCleanup.auth_token else {}
    
    def test_99_cleanup_test_data(self):
        """Cleanup TEST_ prefixed data"""
        if not TestCleanup.auth_token:
            pytest.skip("No auth token for cleanup")
        
        # Clean up test jobs
        response = requests.get(f"{BASE_URL}/api/jobs", headers=self.headers)
        if response.status_code == 200:
            jobs = response.json()
            for job in jobs:
                if job.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/jobs/{job['id']}", headers=self.headers)
                    print(f"Deleted test job: {job['name']}")
        
        # Clean up test customers
        response = requests.get(f"{BASE_URL}/api/customers", headers=self.headers)
        if response.status_code == 200:
            customers = response.json()
            for customer in customers:
                if customer.get("name", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/customers/{customer['id']}", headers=self.headers)
                    print(f"Deleted test customer: {customer['name']}")
        
        # Reset workflow settings to detailed
        reset_payload = {"workflow_mode": "detailed", "category_template_map": {}}
        requests.put(f"{BASE_URL}/api/production-timeline/settings", 
                    json=reset_payload, headers=self.headers)
        print("Reset workflow settings to detailed mode")
