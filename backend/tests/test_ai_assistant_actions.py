"""
AI Assistant Structured Actions Tests

Tests for:
- All 9 action types
- Tenant scoping
- Permission checks
- Confirmation flow
- Audit logging
"""

import pytest
import asyncio
from datetime import datetime, timezone
import sys
import uuid

sys.path.insert(0, '/app/backend')

from services.ai_assistant_actions import (
    AIAssistantActions, ActionType, ActionStatus, ActionRequest,
    ACTION_PERMISSIONS, DESTRUCTIVE_ACTIONS
)
from models.auth import Permission, UserRole


class MockDB:
    """Mock database for testing"""
    def __init__(self):
        self.jobs = MockCollection()
        self.calendar_events = MockCollection()
        self.materials = MockCollection()
        self.material_cost_history = MockCollection()
        self.invoices = MockCollection()
        self.employees = MockCollection()
        self.job_assignments = MockCollection()
        self.time_entries = MockCollection()
        self.expenses = MockCollection()
        self.ai_action_audit = MockCollection()


class MockCollection:
    """Mock MongoDB collection"""
    def __init__(self):
        self.data = {}
    
    async def find_one(self, query, projection=None):
        for doc in self.data.values():
            match = all(doc.get(k) == v for k, v in query.items())
            if match:
                return {k: v for k, v in doc.items() if k != '_id'}
        return None
    
    async def insert_one(self, doc):
        doc_id = doc.get('id', str(uuid.uuid4()))
        self.data[doc_id] = doc
        return type('InsertResult', (), {'inserted_id': doc_id})()
    
    async def update_one(self, query, update, upsert=False):
        for doc in self.data.values():
            if all(doc.get(k) == v for k, v in query.items()):
                if '$set' in update:
                    doc.update(update['$set'])
                return type('UpdateResult', (), {'matched_count': 1})()
        return type('UpdateResult', (), {'matched_count': 0})()
    
    async def count_documents(self, query):
        return sum(1 for doc in self.data.values() 
                   if all(doc.get(k) == v for k, v in query.items()))
    
    def find(self, query, projection=None):
        return MockCursor([doc for doc in self.data.values() 
                          if all(doc.get(k) == v for k, v in query.items())])


class MockCursor:
    def __init__(self, data):
        self._data = data
    
    def sort(self, *args):
        return self
    
    def limit(self, n):
        self._data = self._data[:n]
        return self
    
    async def to_list(self, length):
        return self._data[:length]


class MockUser:
    """Mock user for testing"""
    def __init__(self, role=UserUserRole.ADMIN, tenant_id="test_tenant"):
        self.id = "test_user"
        self.tenant_id = tenant_id
        self.role = role


class TestActionPermissions:
    """Test permission checking"""
    
    def test_all_actions_have_permissions(self):
        """All action types should have permission mappings"""
        for action_type in ActionType:
            assert action_type in ACTION_PERMISSIONS, f"{action_type} missing permission mapping"
    
    def test_destructive_actions_defined(self):
        """Destructive actions should be defined"""
        assert ActionType.UPDATE_JOB_STATUS in DESTRUCTIVE_ACTIONS
        assert ActionType.UPDATE_MATERIAL_COST in DESTRUCTIVE_ACTIONS
        assert ActionType.CREATE_INVOICE in DESTRUCTIVE_ACTIONS
        assert ActionType.ASSIGN_EMPLOYEE in DESTRUCTIVE_ACTIONS
    
    def test_non_destructive_actions(self):
        """Some actions should not require confirmation"""
        assert ActionType.CREATE_JOB not in DESTRUCTIVE_ACTIONS
        assert ActionType.CREATE_CALENDAR_EVENT not in DESTRUCTIVE_ACTIONS
        assert ActionType.ADD_MATERIAL not in DESTRUCTIVE_ACTIONS
        assert ActionType.LOG_TIME_ENTRY not in DESTRUCTIVE_ACTIONS


class TestCreateJob:
    """Test create_job action"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.mark.asyncio
    async def test_create_job_success(self, mock_db):
        """Should create job successfully"""
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.CREATE_JOB,
            parameters={
                "name": "Test Job",
                "customer_name": "Test Customer",
                "category": "Signs"
            }
        )
        
        response = await actions.execute_action(user, request)
        
        assert response.status == ActionStatus.EXECUTED
        assert response.result is not None
        assert response.result["name"] == "Test Job"
        assert "job_id" in response.result
        assert response.audit_id is not None
    
    @pytest.mark.asyncio
    async def test_create_job_no_confirmation_needed(self, mock_db):
        """Create job should not require confirmation"""
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.CREATE_JOB,
            parameters={"name": "Test Job"}
        )
        
        response = await actions.execute_action(user, request, confirmed=False)
        
        assert response.status == ActionStatus.EXECUTED
        assert response.confirmation_required == False


class TestUpdateJobStatus:
    """Test update_job_status action"""
    
    @pytest.fixture
    def mock_db(self):
        db = MockDB()
        # Add a test job
        db.jobs.data["job1"] = {
            "id": "job1",
            "tenant_id": "test_tenant",
            "name": "Existing Job",
            "status": "pending"
        }
        return db
    
    @pytest.mark.asyncio
    async def test_update_status_requires_confirmation(self, mock_db):
        """Update status should require confirmation"""
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.UPDATE_JOB_STATUS,
            parameters={"job_id": "job1", "status": "completed"}
        )
        
        response = await actions.execute_action(user, request, confirmed=False)
        
        assert response.status == ActionStatus.PENDING_CONFIRMATION
        assert response.confirmation_required == True
        assert "completed" in response.confirmation_message
    
    @pytest.mark.asyncio
    async def test_update_status_with_confirmation(self, mock_db):
        """Update status should execute when confirmed"""
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.UPDATE_JOB_STATUS,
            parameters={"job_id": "job1", "status": "completed"}
        )
        
        response = await actions.execute_action(user, request, confirmed=True)
        
        assert response.status == ActionStatus.EXECUTED
        assert response.result["old_status"] == "pending"
        assert response.result["new_status"] == "completed"


class TestTenantScoping:
    """Test tenant isolation"""
    
    @pytest.fixture
    def mock_db(self):
        db = MockDB()
        # Add jobs for different tenants
        db.jobs.data["job_tenant_a"] = {
            "id": "job_tenant_a",
            "tenant_id": "tenant_a",
            "name": "Tenant A Job",
            "status": "pending"
        }
        db.jobs.data["job_tenant_b"] = {
            "id": "job_tenant_b",
            "tenant_id": "tenant_b",
            "name": "Tenant B Job",
            "status": "pending"
        }
        return db
    
    @pytest.mark.asyncio
    async def test_cannot_update_other_tenant_job(self, mock_db):
        """User should not be able to update another tenant's job"""
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN, tenant_id="tenant_a")
        
        request = ActionRequest(
            action_type=ActionType.UPDATE_JOB_STATUS,
            parameters={"job_id": "job_tenant_b", "status": "completed"}
        )
        
        response = await actions.execute_action(user, request, confirmed=True)
        
        assert response.status == ActionStatus.FAILED
        assert "not found" in response.error.lower()


class TestAuditLogging:
    """Test audit log functionality"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.mark.asyncio
    async def test_successful_action_logged(self, mock_db):
        """Successful actions should be audit logged"""
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN, tenant_id="test_tenant")
        
        request = ActionRequest(
            action_type=ActionType.CREATE_JOB,
            parameters={"name": "Audit Test Job"}
        )
        
        response = await actions.execute_action(user, request)
        
        assert response.audit_id is not None
        
        # Check audit entry was created
        audit_entries = await actions.get_action_audit_log("test_tenant")
        assert len(audit_entries) == 1
        assert audit_entries[0]["action_type"] == "create_job"
        assert audit_entries[0]["status"] == "executed"
    
    @pytest.mark.asyncio
    async def test_failed_action_logged(self, mock_db):
        """Failed actions should be audit logged with error"""
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN, tenant_id="test_tenant")
        
        request = ActionRequest(
            action_type=ActionType.UPDATE_JOB_STATUS,
            parameters={"job_id": "nonexistent", "status": "completed"}
        )
        
        response = await actions.execute_action(user, request, confirmed=True)
        
        assert response.status == ActionStatus.FAILED
        assert response.audit_id is not None
        
        audit_entries = await actions.get_action_audit_log("test_tenant")
        failed_entry = next((e for e in audit_entries if e["status"] == "failed"), None)
        assert failed_entry is not None
        assert failed_entry["error"] is not None


class TestAllActionTypes:
    """Test all 9 action types work"""
    
    @pytest.fixture
    def mock_db(self):
        db = MockDB()
        # Setup required data
        db.jobs.data["test_job"] = {
            "id": "test_job", "tenant_id": "test_tenant",
            "name": "Test Job", "status": "pending", "assigned_employees": []
        }
        db.employees.data["test_emp"] = {
            "id": "test_emp", "tenant_id": "test_tenant", "name": "Test Employee"
        }
        db.materials.data["test_mat"] = {
            "id": "test_mat", "tenant_id": "test_tenant", 
            "name": "Test Material", "cost": 10.00
        }
        db.expenses.data["test_exp"] = {
            "id": "test_exp", "tenant_id": "test_tenant",
            "description": "Test Expense", "amount": 50.00, "category": "Uncategorized"
        }
        return db
    
    @pytest.mark.asyncio
    async def test_create_calendar_event(self, mock_db):
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.CREATE_CALENDAR_EVENT,
            parameters={
                "title": "Test Event",
                "start_time": "2025-01-15T10:00:00Z",
                "end_time": "2025-01-15T11:00:00Z"
            }
        )
        response = await actions.execute_action(user, request)
        assert response.status == ActionStatus.EXECUTED
    
    @pytest.mark.asyncio
    async def test_add_material(self, mock_db):
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.ADD_MATERIAL,
            parameters={
                "name": "New Vinyl",
                "cost": 25.00,
                "quantity": 100
            }
        )
        response = await actions.execute_action(user, request)
        assert response.status == ActionStatus.EXECUTED
    
    @pytest.mark.asyncio
    async def test_update_material_cost(self, mock_db):
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.UPDATE_MATERIAL_COST,
            parameters={"material_id": "test_mat", "cost": 15.00}
        )
        response = await actions.execute_action(user, request, confirmed=True)
        assert response.status == ActionStatus.EXECUTED
        assert response.result["old_cost"] == 10.00
        assert response.result["new_cost"] == 15.00
    
    @pytest.mark.asyncio
    async def test_create_invoice(self, mock_db):
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.CREATE_INVOICE,
            parameters={
                "customer_name": "Test Customer",
                "line_items": [{"description": "Sign", "total": 100.00}]
            }
        )
        response = await actions.execute_action(user, request, confirmed=True)
        assert response.status == ActionStatus.EXECUTED
        assert "invoice_number" in response.result
    
    @pytest.mark.asyncio
    async def test_assign_employee(self, mock_db):
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.ASSIGN_EMPLOYEE,
            parameters={"job_id": "test_job", "employee_id": "test_emp"}
        )
        response = await actions.execute_action(user, request, confirmed=True)
        assert response.status == ActionStatus.EXECUTED
    
    @pytest.mark.asyncio
    async def test_log_time_entry(self, mock_db):
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.LOG_TIME_ENTRY,
            parameters={
                "employee_id": "test_emp",
                "employee_name": "Test Employee",
                "hours": 2.5,
                "description": "Production work"
            }
        )
        response = await actions.execute_action(user, request)
        assert response.status == ActionStatus.EXECUTED
    
    @pytest.mark.asyncio
    async def test_categorize_expense(self, mock_db):
        actions = AIAssistantActions(mock_db)
        user = MockUser(role=UserRole.ADMIN)
        
        request = ActionRequest(
            action_type=ActionType.CATEGORIZE_EXPENSE,
            parameters={"expense_id": "test_exp", "category": "Materials"}
        )
        response = await actions.execute_action(user, request)
        assert response.status == ActionStatus.EXECUTED
        assert response.result["new_category"] == "Materials"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
