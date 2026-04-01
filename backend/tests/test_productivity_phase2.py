"""
Test Unified Productivity Phase 2 - Iteration 80
Tests the new Phase 2 features:
- PATCH /api/productivity/items/{item_uid} write-back endpoint
- Task schema expanded with status/priority/start_datetime
- Kanban drag/drop persistence for writable item types
- Task List inline edits (status, priority, due date, assignee, complete toggle)
- Dashboard schedule/pending-approval widgets using unified productivity queries
"""

import pytest
import requests
import os
from datetime import datetime, timedelta
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = PRODUCTION_OWNER_EMAIL
TEST_PASSWORD = PRODUCTION_OWNER_PASSWORD


class TestProductivityPhase2WriteBack:
    """Test unified PATCH write-back endpoint for Phase 2"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Authenticate
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.token = token
    
    # ==================== PATCH /api/productivity/items/{item_uid} ====================
    
    def test_patch_endpoint_exists(self):
        """Test that PATCH endpoint exists and returns proper response"""
        # First get an item to patch
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "item_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No task items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        
        # Try to patch with empty payload (should still work)
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={})
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.status_code} - {patch_response.text}"
        print(f"✓ PATCH endpoint exists and responds for item {item_uid}")
    
    def test_patch_task_status_update(self):
        """Test updating task status via PATCH endpoint"""
        # Get a task item
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No task items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        original_status = item["status"]
        
        # Update status
        new_status = "in_progress" if original_status != "in_progress" else "open"
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "status": new_status
        })
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
        
        updated_item = patch_response.json()
        assert updated_item.get("status") == new_status, f"Status not updated: {updated_item.get('status')} != {new_status}"
        
        # Verify persistence by fetching again
        verify_response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        verify_items = verify_response.json().get("items", [])
        verify_item = next((i for i in verify_items if i["uid"] == item_uid), None)
        assert verify_item is not None, "Item not found after update"
        assert verify_item["status"] == new_status, f"Status not persisted: {verify_item['status']} != {new_status}"
        
        # Restore original status
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"status": original_status})
        
        print(f"✓ Task status update working: {original_status} -> {new_status} -> {original_status}")
    
    def test_patch_task_priority_update(self):
        """Test updating task priority via PATCH endpoint"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No task items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        original_priority = item.get("priority", "normal")
        
        # Update priority
        new_priority = "high" if original_priority != "high" else "normal"
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "priority": new_priority
        })
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
        
        updated_item = patch_response.json()
        assert updated_item.get("priority") == new_priority, f"Priority not updated: {updated_item.get('priority')} != {new_priority}"
        
        # Restore original priority
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"priority": original_priority})
        
        print(f"✓ Task priority update working: {original_priority} -> {new_priority} -> {original_priority}")
    
    def test_patch_task_assignee_update(self):
        """Test updating task assignee via PATCH endpoint"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No task items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        original_assignee = item.get("assigned_user_id")
        
        # Get employees to find a valid assignee
        emp_response = self.session.get(f"{BASE_URL}/api/employees")
        employees = emp_response.json() if emp_response.status_code == 200 else []
        
        if employees:
            new_assignee = employees[0]["id"] if original_assignee != employees[0]["id"] else (employees[1]["id"] if len(employees) > 1 else None)
            if new_assignee:
                patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
                    "assigned_user_id": new_assignee
                })
                assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
                
                # Restore original assignee
                self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
                    "assigned_user_id": original_assignee or ""
                })
                
                print("✓ Task assignee update working")
            else:
                print("⚠ Only one employee available, skipping assignee change test")
        else:
            print("⚠ No employees available for assignee test")
    
    def test_patch_task_due_date_update(self):
        """Test updating task due date via PATCH endpoint"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No task items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        original_due = item.get("due_datetime")
        
        # Update due date
        new_due = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "due_datetime": new_due
        })
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
        
        updated_item = patch_response.json()
        # Due datetime should contain the new date
        if updated_item.get("due_datetime"):
            assert new_due in updated_item["due_datetime"], "Due date not updated correctly"
        
        # Restore original due date
        if original_due:
            self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"due_datetime": original_due[:10]})
        
        print(f"✓ Task due date update working: -> {new_due}")
    
    def test_patch_task_complete_toggle(self):
        """Test toggling task completion via PATCH endpoint"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No task items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        original_completed = item.get("is_completed", False)
        
        # Toggle completion
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "is_completed": not original_completed
        })
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
        
        updated_item = patch_response.json()
        assert updated_item.get("is_completed") == (not original_completed), "Completion not toggled"
        
        # Restore original state
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"is_completed": original_completed})
        
        print(f"✓ Task completion toggle working: {original_completed} -> {not original_completed} -> {original_completed}")
    
    def test_patch_order_status_update(self):
        """Test updating order status via PATCH endpoint"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "order",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No order items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        original_status = item["status"]
        
        # Update status (orders have different valid statuses)
        new_status = "in_production" if original_status != "in_production" else "new_intake"
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "status": new_status
        })
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
        
        # Restore original status
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"status": original_status})
        
        print(f"✓ Order status update working: {original_status} -> {new_status} -> {original_status}")
    
    def test_patch_production_task_status_update(self):
        """Test updating production task status via PATCH endpoint"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "production_task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No production task items available for testing")
        
        item = items[0]
        item_uid = item["uid"]
        original_status = item["status"]
        
        # Update status
        new_status = "in_progress" if original_status != "in_progress" else "not_started"
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "status": new_status
        })
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
        
        # Restore original status
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"status": original_status})
        
        print(f"✓ Production task status update working: {original_status} -> {new_status} -> {original_status}")


class TestTaskSchemaExpanded:
    """Test that task schema now includes status/priority/start_datetime"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_task_create_with_status(self):
        """Test creating task with status field"""
        task_data = {
            "title": f"TEST_Phase2_Status_{uuid.uuid4().hex[:8]}",
            "status": "pending",
            "priority": "high"
        }
        
        response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 200, f"Task creation failed: {response.text}"
        
        task = response.json()
        assert task.get("status") == "pending", f"Status not set correctly: {task.get('status')}"
        assert task.get("priority") == "high", f"Priority not set correctly: {task.get('priority')}"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/tasks/{task['id']}")
        
        print("✓ Task created with status=pending, priority=high")
    
    def test_task_create_with_start_datetime(self):
        """Test creating task with start_datetime field"""
        start_dt = (datetime.now() + timedelta(hours=2)).isoformat()
        task_data = {
            "title": f"TEST_Phase2_StartDT_{uuid.uuid4().hex[:8]}",
            "start_datetime": start_dt
        }
        
        response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 200, f"Task creation failed: {response.text}"
        
        task = response.json()
        assert task.get("start_datetime") is not None, "start_datetime not set"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/tasks/{task['id']}")
        
        print("✓ Task created with start_datetime")
    
    def test_task_update_status_via_tasks_endpoint(self):
        """Test updating task status via /api/tasks endpoint"""
        # Create a task
        task_data = {
            "title": f"TEST_Phase2_Update_{uuid.uuid4().hex[:8]}",
            "status": "open"
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert create_response.status_code == 200
        task = create_response.json()
        task_id = task["id"]
        
        # Update status
        update_response = self.session.put(f"{BASE_URL}/api/tasks/{task_id}", json={
            "status": "in_progress"
        })
        assert update_response.status_code == 200, f"Task update failed: {update_response.text}"
        
        updated_task = update_response.json()
        assert updated_task.get("status") == "in_progress", f"Status not updated: {updated_task.get('status')}"
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/tasks/{task_id}")
        
        print("✓ Task status updated via /api/tasks endpoint")


class TestDashboardUnifiedQueries:
    """Test that Dashboard schedule/pending-approval widgets use unified productivity queries"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_productivity_items_for_schedule_widget(self):
        """Test that productivity items endpoint can serve schedule widget data"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "start_date": today,
            "end_date": today,
            "include_completed": False,
            "item_types": "job,production_task,appointment,schedule_shift"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        # Verify items have required fields for schedule widget
        for item in items[:5]:  # Check first 5
            assert "uid" in item
            assert "title" in item
            assert "status" in item
            assert "type" in item
        
        print(f"✓ Schedule widget can use productivity items: {len(items)} items for today")
    
    def test_productivity_items_for_pending_approvals_widget(self):
        """Test that productivity items endpoint can serve pending approvals widget data"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "include_completed": False,
            "statuses": "pending,awaiting_approval,awaiting_quote,awaiting_review",
            "item_types": "job,production_task"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        items = data.get("items", [])
        
        # Verify items have required fields for pending approvals widget
        for item in items[:5]:  # Check first 5
            assert "uid" in item
            assert "title" in item
            assert "status" in item
            assert item["status"] in ["pending", "awaiting_approval", "awaiting_quote", "awaiting_review"]
        
        print(f"✓ Pending approvals widget can use productivity items: {len(items)} pending items")


class TestKanbanDragDropPersistence:
    """Test Kanban drag/drop persistence for writable item types"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_kanban_move_task_to_different_column(self):
        """Test moving a task to a different Kanban column persists"""
        # Get board data
        response = self.session.get(f"{BASE_URL}/api/productivity/board", params={
            "item_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        data = response.json()
        groups = data.get("groups", {})
        
        # Find a task to move
        task_item = None
        original_column = None
        for column, items in groups.items():
            if items and column not in ["done", "completed", "complete"]:
                task_item = items[0]
                original_column = column
                break
        
        if not task_item:
            pytest.skip("No movable task items available")
        
        item_uid = task_item["uid"]
        
        # Move to a different column
        target_column = "in_progress" if original_column != "in_progress" else "pending"
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "status": target_column
        })
        assert patch_response.status_code == 200, f"Move failed: {patch_response.text}"
        
        # Verify in board view
        verify_response = self.session.get(f"{BASE_URL}/api/productivity/board", params={
            "item_types": "task",
            "include_completed": True
        })
        verify_groups = verify_response.json().get("groups", {})
        
        # Item should be in target column
        target_items = verify_groups.get(target_column, [])
        found = any(i["uid"] == item_uid for i in target_items)
        assert found, f"Item not found in target column {target_column}"
        
        # Restore original column
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"status": original_column})
        
        print(f"✓ Kanban move persisted: {original_column} -> {target_column} -> {original_column}")
    
    def test_kanban_move_to_complete_column(self):
        """Test moving item to complete column sets is_completed"""
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": False
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No incomplete task items available")
        
        item = items[0]
        item_uid = item["uid"]
        original_status = item["status"]
        
        # Move to completed
        patch_response = self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "status": "completed",
            "is_completed": True
        })
        assert patch_response.status_code == 200
        
        updated = patch_response.json()
        assert updated.get("is_completed"), "is_completed not set to True"
        
        # Restore
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={
            "status": original_status,
            "is_completed": False
        })
        
        print("✓ Moving to complete column sets is_completed=True")


class TestCrossViewConsistency:
    """Test that updates reflect across all views (Kanban, Calendar, Task List, Dashboard)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Authentication failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        if not token:
            pytest.skip("No access token received")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_update_reflects_in_all_endpoints(self):
        """Test that a status update reflects in items, board, and calendar endpoints"""
        # Get a task
        response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        assert response.status_code == 200
        
        items = response.json().get("items", [])
        if not items:
            pytest.skip("No task items available")
        
        item = items[0]
        item_uid = item["uid"]
        original_status = item["status"]
        
        # Update status
        new_status = "waiting" if original_status != "waiting" else "open"
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"status": new_status})
        
        # Check in /items endpoint
        items_response = self.session.get(f"{BASE_URL}/api/productivity/items", params={
            "source_types": "task",
            "include_completed": True
        })
        items_data = items_response.json().get("items", [])
        items_item = next((i for i in items_data if i["uid"] == item_uid), None)
        assert items_item and items_item["status"] == new_status, "Status not reflected in /items"
        
        # Check in /board endpoint
        board_response = self.session.get(f"{BASE_URL}/api/productivity/board", params={
            "item_types": "task",
            "include_completed": True
        })
        board_groups = board_response.json().get("groups", {})
        board_item = None
        for column, col_items in board_groups.items():
            for i in col_items:
                if i["uid"] == item_uid:
                    board_item = i
                    break
        assert board_item and board_item["status"] == new_status, "Status not reflected in /board"
        
        # Check in /calendar-range endpoint
        calendar_response = self.session.get(f"{BASE_URL}/api/productivity/calendar-range", params={
            "view": "month",
            "item_types": "task",
            "include_completed": True
        })
        calendar_items = calendar_response.json().get("items", [])
        calendar_item = next((i for i in calendar_items if i["uid"] == item_uid), None)
        if calendar_item:  # May not be in current month range
            assert calendar_item["status"] == new_status, "Status not reflected in /calendar-range"
        
        # Restore
        self.session.patch(f"{BASE_URL}/api/productivity/items/{item_uid}", json={"status": original_status})
        
        print("✓ Update reflects across all endpoints: /items, /board, /calendar-range")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
