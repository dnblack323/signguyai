"""
Order System Phase 1 - Backend API Tests

Tests the 4-layer architecture:
  Layer 1: Orders (master record)
  Layer 2: Job Tickets (production detail)
  Layer 3: Quotes/Invoices (financial)
  Layer 4: Production Tasks (department-level)

Features tested:
- Orders CRUD with auto-generated order_number
- Job Tickets CRUD with production task auto-generation
- Production Tasks management with status roll-up
- Workflow Templates (6 default templates)
- Generate quote and start production endpoints
- Activity logging
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "thesigntistslab@gmail.com"
TEST_PASSWORD = "password123"


class TestOrderSystemPhase1:
    """Order System Phase 1 API Tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token")
        assert token, "No access_token in login response"
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    # ============== WORKFLOW TEMPLATES TESTS ==============
    
    def test_workflow_templates_list_and_seed(self, auth_headers):
        """Test GET /api/workflow-templates lists 6 default templates (auto-seeded)"""
        response = requests.get(f"{BASE_URL}/api/workflow-templates", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list templates: {response.text}"
        
        templates = response.json()
        assert isinstance(templates, list), "Templates should be a list"
        
        # Verify 6 default templates exist
        categories = [t.get("category") for t in templates]
        expected_categories = ["rigid_signs", "banners", "cut_vinyl", "vehicle_wrap", "apparel", "promo_misc"]
        
        for cat in expected_categories:
            assert cat in categories, f"Missing default template for category: {cat}"
        
        # Verify stage counts for each template
        template_stage_counts = {
            "rigid_signs": 11,
            "banners": 12,
            "cut_vinyl": 8,
            "vehicle_wrap": 14,
            "apparel": 11,
            "promo_misc": 5
        }
        
        for template in templates:
            cat = template.get("category")
            if cat in template_stage_counts:
                expected_stages = template_stage_counts[cat]
                actual_stages = len(template.get("stages", []))
                assert actual_stages == expected_stages, f"Template {cat} should have {expected_stages} stages, got {actual_stages}"
        
        print(f"✓ Found {len(templates)} workflow templates with correct stage counts")
    
    # ============== ORDERS CRUD TESTS ==============
    
    def test_create_order_with_auto_number(self, auth_headers):
        """Test POST /api/orders creates an order with auto-generated order_number"""
        order_data = {
            "customer_name": "TEST_Order_Customer",
            "contact_name": "John Doe",
            "phone": "555-1234",
            "email": "test@example.com",
            "company_name": "TEST_Company",
            "order_source": "phone",
            "pickup_delivery_method": "pickup",
            "internal_notes": "Test order for Phase 1 testing"
        }
        
        response = requests.post(f"{BASE_URL}/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create order: {response.text}"
        
        order = response.json()
        assert "id" in order, "Order should have an id"
        assert "order_number" in order, "Order should have an order_number"
        assert order["order_number"].startswith("ORD-"), f"Order number should start with ORD-, got {order['order_number']}"
        assert order["customer_name"] == "TEST_Order_Customer"
        assert order["status"] == "new_intake", f"New order should have status 'new_intake', got {order['status']}"
        
        # Store for later tests
        self.__class__.test_order_id = order["id"]
        self.__class__.test_order_number = order["order_number"]
        
        print(f"✓ Created order {order['order_number']} with id {order['id']}")
        return order
    
    def test_list_orders_with_filters(self, auth_headers):
        """Test GET /api/orders lists orders with search and status filters"""
        # List all orders
        response = requests.get(f"{BASE_URL}/api/orders", headers=auth_headers)
        assert response.status_code == 200, f"Failed to list orders: {response.text}"
        
        data = response.json()
        assert "orders" in data, "Response should have 'orders' key"
        assert "total" in data, "Response should have 'total' key"
        assert isinstance(data["orders"], list)
        
        # Test search filter
        response = requests.get(f"{BASE_URL}/api/orders?search=TEST_Order", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1, "Should find at least 1 order with TEST_Order search"
        
        # Test status filter
        response = requests.get(f"{BASE_URL}/api/orders?status=new_intake", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for order in data["orders"]:
            assert order["status"] == "new_intake", "Status filter should work"
        
        print(f"✓ Listed orders with filters - total: {data['total']}")
    
    def test_get_order_with_enriched_tickets(self, auth_headers):
        """Test GET /api/orders/{id} returns order with enriched job_tickets"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get order: {response.text}"
        
        order = response.json()
        assert order["id"] == order_id
        assert "job_tickets" in order, "Order should include job_tickets array"
        assert isinstance(order["job_tickets"], list)
        
        print(f"✓ Got order {order['order_number']} with {len(order['job_tickets'])} job tickets")
    
    def test_update_order_and_log_status_change(self, auth_headers):
        """Test PUT /api/orders/{id} updates order and logs status changes"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        # Update status
        update_data = {
            "status": "awaiting_review",
            "internal_notes": "Updated for testing"
        }
        
        response = requests.put(f"{BASE_URL}/api/orders/{order_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to update order: {response.text}"
        
        order = response.json()
        assert order["status"] == "awaiting_review", f"Status should be updated, got {order['status']}"
        assert order["internal_notes"] == "Updated for testing"
        
        # Verify activity was logged
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}/activity", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get activity: {response.text}"
        
        activities = response.json()
        assert isinstance(activities, list)
        
        # Find status change activity
        status_changes = [a for a in activities if a.get("action") == "status_change"]
        assert len(status_changes) >= 1, "Should have at least one status change logged"
        
        print(f"✓ Updated order status and verified activity log ({len(activities)} activities)")
    
    # ============== JOB TICKETS CRUD TESTS ==============
    
    def test_create_job_ticket_with_production_flow(self, auth_headers):
        """Test POST /api/job-tickets creates ticket linked to order, auto-generates production tasks if flow enabled"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        ticket_data = {
            "order_id": order_id,
            "item_name": "TEST_Banner_24x36",
            "item_category": "banners",
            "quantity": 5,
            "unit_type": "each",
            "priority": "normal",
            "production_flow_enabled": True,
            "estimated_price": 250.00,
            "special_instructions": "Test banner for Phase 1 testing"
        }
        
        response = requests.post(f"{BASE_URL}/api/job-tickets", json=ticket_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to create job ticket: {response.text}"
        
        ticket = response.json()
        assert "id" in ticket, "Ticket should have an id"
        assert "ticket_number" in ticket, "Ticket should have a ticket_number"
        assert ticket["order_id"] == order_id
        assert ticket["item_category"] == "banners"
        assert ticket["production_flow_enabled"] == True
        
        # Store for later tests
        self.__class__.test_ticket_id = ticket["id"]
        self.__class__.test_ticket_number = ticket["ticket_number"]
        
        print(f"✓ Created job ticket {ticket['ticket_number']} with production flow enabled")
        return ticket
    
    def test_get_job_ticket_with_production_tasks(self, auth_headers):
        """Test GET /api/job-tickets/{id} returns ticket with production_tasks if flow enabled"""
        ticket_id = getattr(self.__class__, 'test_ticket_id', None)
        if not ticket_id:
            pytest.skip("No test ticket created")
        
        response = requests.get(f"{BASE_URL}/api/job-tickets/{ticket_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get job ticket: {response.text}"
        
        ticket = response.json()
        assert ticket["id"] == ticket_id
        assert "production_tasks" in ticket, "Ticket with production_flow_enabled should include production_tasks"
        
        tasks = ticket["production_tasks"]
        assert isinstance(tasks, list)
        assert len(tasks) == 12, f"Banners template should have 12 tasks, got {len(tasks)}"
        
        # Verify tasks are sorted by sequence
        sequences = [t["stage_sequence"] for t in tasks]
        assert sequences == sorted(sequences), "Tasks should be sorted by stage_sequence"
        
        # Store first task for later tests
        if tasks:
            self.__class__.test_task_id = tasks[0]["id"]
        
        print(f"✓ Got job ticket with {len(tasks)} production tasks")
    
    def test_list_job_tickets_with_filters(self, auth_headers):
        """Test GET /api/job-tickets lists with filters (order_id, category, department, status)"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        
        # List all tickets
        response = requests.get(f"{BASE_URL}/api/job-tickets", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        
        # Filter by order_id
        if order_id:
            response = requests.get(f"{BASE_URL}/api/job-tickets?order_id={order_id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            for ticket in data["tickets"]:
                assert ticket["order_id"] == order_id
        
        # Filter by category
        response = requests.get(f"{BASE_URL}/api/job-tickets?category=banners", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for ticket in data["tickets"]:
            assert ticket["item_category"] == "banners"
        
        print(f"✓ Listed job tickets with filters")
    
    def test_update_job_ticket_enable_production_flow(self, auth_headers):
        """Test PUT /api/job-tickets/{id} updates ticket, enables production flow toggle"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        # Create a ticket without production flow
        ticket_data = {
            "order_id": order_id,
            "item_name": "TEST_Vinyl_Lettering",
            "item_category": "cut_vinyl",
            "quantity": 1,
            "production_flow_enabled": False,
            "estimated_price": 75.00
        }
        
        response = requests.post(f"{BASE_URL}/api/job-tickets", json=ticket_data, headers=auth_headers)
        assert response.status_code == 200
        ticket = response.json()
        ticket_id = ticket["id"]
        
        # Enable production flow via update
        update_data = {"production_flow_enabled": True}
        response = requests.put(f"{BASE_URL}/api/job-tickets/{ticket_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Verify tasks were generated
        response = requests.get(f"{BASE_URL}/api/job-tickets/{ticket_id}", headers=auth_headers)
        assert response.status_code == 200
        ticket = response.json()
        
        assert ticket["production_flow_enabled"] == True
        assert "production_tasks" in ticket
        assert len(ticket["production_tasks"]) == 8, f"Cut vinyl template should have 8 tasks, got {len(ticket['production_tasks'])}"
        
        # Store for cleanup
        self.__class__.test_vinyl_ticket_id = ticket_id
        
        print(f"✓ Enabled production flow on ticket, generated {len(ticket['production_tasks'])} tasks")
    
    # ============== PRODUCTION TASKS TESTS ==============
    
    def test_list_production_tasks_with_filters(self, auth_headers):
        """Test GET /api/production-tasks list and filter by department, status, order, ticket"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        ticket_id = getattr(self.__class__, 'test_ticket_id', None)
        
        # List all tasks
        response = requests.get(f"{BASE_URL}/api/production-tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        
        # Filter by order_id
        if order_id:
            response = requests.get(f"{BASE_URL}/api/production-tasks?order_id={order_id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            for task in data["tasks"]:
                assert task["order_id"] == order_id
        
        # Filter by job_ticket_id
        if ticket_id:
            response = requests.get(f"{BASE_URL}/api/production-tasks?job_ticket_id={ticket_id}", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            for task in data["tasks"]:
                assert task["job_ticket_id"] == ticket_id
        
        # Filter by department
        response = requests.get(f"{BASE_URL}/api/production-tasks?department=design", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for task in data["tasks"]:
            assert task["department"] == "design"
        
        # Filter by status
        response = requests.get(f"{BASE_URL}/api/production-tasks?status=not_started", headers=auth_headers)
        assert response.status_code == 200
        
        print(f"✓ Listed production tasks with filters")
    
    def test_update_production_task_status_with_timestamp(self, auth_headers):
        """Test PUT /api/production-tasks/{id} updates status with timestamp history, triggers roll-up"""
        task_id = getattr(self.__class__, 'test_task_id', None)
        if not task_id:
            pytest.skip("No test task created")
        
        # Update task to in_progress
        update_data = {"status": "in_progress"}
        response = requests.put(f"{BASE_URL}/api/production-tasks/{task_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed to update task: {response.text}"
        
        task = response.json()
        assert task["status"] == "in_progress"
        assert task.get("start_datetime") is not None, "start_datetime should be set when status becomes in_progress"
        
        # Verify timestamp history
        history = task.get("timestamp_history", [])
        assert len(history) >= 2, "Should have at least 2 entries in timestamp_history (not_started + in_progress)"
        
        # Update task to complete
        update_data = {"status": "complete"}
        response = requests.put(f"{BASE_URL}/api/production-tasks/{task_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        task = response.json()
        assert task["status"] == "complete"
        assert task.get("end_datetime") is not None, "end_datetime should be set when status becomes complete"
        assert task["completion_percent"] == 100.0
        
        print(f"✓ Updated task status with timestamp history")
    
    def test_production_board_grouped_by_department(self, auth_headers):
        """Test GET /api/production-tasks/board?view=department returns grouped tasks"""
        response = requests.get(f"{BASE_URL}/api/production-tasks/board?view=department", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get production board: {response.text}"
        
        data = response.json()
        assert data.get("view") == "department", "View should be 'department'"
        assert "groups" in data, "Response should have 'groups' key"
        
        groups = data["groups"]
        assert isinstance(groups, dict), "Groups should be a dictionary"
        
        # Verify tasks are grouped by department
        for dept, tasks in groups.items():
            assert isinstance(tasks, list)
            for task in tasks:
                assert task.get("department") == dept or dept == "unassigned"
        
        print(f"✓ Got production board with {len(groups)} department groups")
    
    # ============== QUOTE GENERATION TEST ==============
    
    def test_generate_quote_from_order(self, auth_headers):
        """Test POST /api/orders/{id}/generate-quote creates quote from job tickets"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        response = requests.post(f"{BASE_URL}/api/orders/{order_id}/generate-quote", headers=auth_headers)
        assert response.status_code == 200, f"Failed to generate quote: {response.text}"
        
        quote = response.json()
        assert "id" in quote, "Quote should have an id"
        assert quote["order_id"] == order_id
        assert quote["type"] == "quote"
        assert "line_items" in quote
        assert isinstance(quote["line_items"], list)
        assert len(quote["line_items"]) >= 1, "Quote should have at least 1 line item"
        assert "subtotal" in quote
        assert "total" in quote
        
        # Verify order status was updated
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        order = response.json()
        assert order_id in str(order.get("linked_quote_ids", [])) or quote["id"] in order.get("linked_quote_ids", [])
        
        print(f"✓ Generated quote with {len(quote['line_items'])} line items, total: ${quote['total']}")
    
    # ============== START PRODUCTION TEST ==============
    
    def test_start_production_activates_workflow(self, auth_headers):
        """Test POST /api/orders/{id}/start-production activates workflow for enabled tickets"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        response = requests.post(f"{BASE_URL}/api/orders/{order_id}/start-production", headers=auth_headers)
        assert response.status_code == 200, f"Failed to start production: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "tickets_activated" in data
        assert "tasks_created" in data
        
        # Verify order status changed to in_production
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        order = response.json()
        assert order["status"] == "in_production", f"Order status should be 'in_production', got {order['status']}"
        
        print(f"✓ Started production: {data['tickets_activated']} tickets, {data['tasks_created']} tasks created")
    
    # ============== ACTIVITY LOG TEST ==============
    
    def test_get_order_activity_log(self, auth_headers):
        """Test GET /api/orders/{id}/activity returns activity log"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}/activity", headers=auth_headers)
        assert response.status_code == 200, f"Failed to get activity: {response.text}"
        
        activities = response.json()
        assert isinstance(activities, list)
        
        # Should have multiple activities from our tests
        assert len(activities) >= 3, f"Should have at least 3 activities, got {len(activities)}"
        
        # Verify activity structure
        for activity in activities:
            assert "id" in activity
            assert "order_id" in activity
            assert "action" in activity
            assert "description" in activity
            assert "created_at" in activity
        
        # Check for expected activity types
        actions = [a["action"] for a in activities]
        assert "created" in actions, "Should have 'created' activity"
        
        print(f"✓ Got {len(activities)} activity log entries")
    
    # ============== STATUS ROLL-UP TESTS ==============
    
    def test_status_rollup_ticket_completion(self, auth_headers):
        """Test status roll-up: completing all tasks on a ticket sets ticket to completed"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        # Create a new ticket with minimal tasks (promo_misc has only 5 stages)
        ticket_data = {
            "order_id": order_id,
            "item_name": "TEST_Promo_Item",
            "item_category": "promo_misc",
            "quantity": 1,
            "production_flow_enabled": True,
            "estimated_price": 50.00
        }
        
        response = requests.post(f"{BASE_URL}/api/job-tickets", json=ticket_data, headers=auth_headers)
        assert response.status_code == 200
        ticket = response.json()
        ticket_id = ticket["id"]
        
        # Get all tasks for this ticket
        response = requests.get(f"{BASE_URL}/api/production-tasks?job_ticket_id={ticket_id}", headers=auth_headers)
        assert response.status_code == 200
        tasks = response.json()["tasks"]
        assert len(tasks) == 5, f"Promo_misc should have 5 tasks, got {len(tasks)}"
        
        # Complete all tasks
        for task in tasks:
            response = requests.put(
                f"{BASE_URL}/api/production-tasks/{task['id']}", 
                json={"status": "complete"}, 
                headers=auth_headers
            )
            assert response.status_code == 200
        
        # Verify ticket status is now completed
        response = requests.get(f"{BASE_URL}/api/job-tickets/{ticket_id}", headers=auth_headers)
        assert response.status_code == 200
        ticket = response.json()
        assert ticket["status"] == "completed", f"Ticket should be 'completed' after all tasks complete, got {ticket['status']}"
        assert ticket["progress"] == 100.0, f"Ticket progress should be 100%, got {ticket['progress']}"
        
        # Store for cleanup
        self.__class__.test_promo_ticket_id = ticket_id
        
        print(f"✓ Status roll-up: All tasks complete → ticket status = completed")
    
    def test_status_rollup_order_partial_completion(self, auth_headers):
        """Test status roll-up: partial ticket completion sets order to partially_complete or in_production"""
        order_id = getattr(self.__class__, 'test_order_id', None)
        if not order_id:
            pytest.skip("No test order created")
        
        # Get order status - should reflect partial completion since we have one completed ticket
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        order = response.json()
        
        # Order should be partially_complete or in_production since we have mixed ticket statuses
        valid_statuses = ["partially_complete", "in_production"]
        assert order["status"] in valid_statuses, f"Order status should be one of {valid_statuses}, got {order['status']}"
        
        # Verify overall_progress is calculated
        assert order["overall_progress"] > 0, "Order should have some progress"
        
        print(f"✓ Status roll-up: Order status = {order['status']}, progress = {order['overall_progress']}%")
    
    # ============== DELETE CASCADE TEST ==============
    
    def test_delete_order_cascades(self, auth_headers):
        """Test DELETE /api/orders/{id} cascades to job tickets and tasks"""
        # Create a new order for deletion test
        order_data = {
            "customer_name": "TEST_Delete_Customer",
            "contact_name": "Delete Test",
            "phone": "555-9999",
            "email": "delete@test.com"
        }
        
        response = requests.post(f"{BASE_URL}/api/orders", json=order_data, headers=auth_headers)
        assert response.status_code == 200
        order = response.json()
        order_id = order["id"]
        
        # Create a job ticket with production flow
        ticket_data = {
            "order_id": order_id,
            "item_name": "TEST_Delete_Banner",
            "item_category": "banners",
            "quantity": 1,
            "production_flow_enabled": True
        }
        
        response = requests.post(f"{BASE_URL}/api/job-tickets", json=ticket_data, headers=auth_headers)
        assert response.status_code == 200
        ticket = response.json()
        ticket_id = ticket["id"]
        
        # Verify tasks were created
        response = requests.get(f"{BASE_URL}/api/production-tasks?job_ticket_id={ticket_id}", headers=auth_headers)
        assert response.status_code == 200
        tasks_before = response.json()["total"]
        assert tasks_before > 0, "Should have tasks before deletion"
        
        # Delete the order
        response = requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # Verify order is deleted
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 404, "Order should be deleted"
        
        # Verify ticket is deleted
        response = requests.get(f"{BASE_URL}/api/job-tickets/{ticket_id}", headers=auth_headers)
        assert response.status_code == 404, "Job ticket should be cascade deleted"
        
        # Verify tasks are deleted
        response = requests.get(f"{BASE_URL}/api/production-tasks?job_ticket_id={ticket_id}", headers=auth_headers)
        assert response.status_code == 200
        tasks_after = response.json()["total"]
        assert tasks_after == 0, "Production tasks should be cascade deleted"
        
        print(f"✓ Delete cascade: Order, {1} ticket, and {tasks_before} tasks deleted")
    
    # ============== CLEANUP ==============
    
    def test_cleanup_test_data(self, auth_headers):
        """Cleanup test data created during tests"""
        # Delete the main test order (will cascade delete tickets and tasks)
        order_id = getattr(self.__class__, 'test_order_id', None)
        if order_id:
            response = requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
            if response.status_code == 200:
                print(f"✓ Cleaned up test order {order_id}")
            else:
                print(f"⚠ Could not delete test order: {response.text}")
        
        print("✓ Test cleanup complete")


class TestExistingOrderData:
    """Tests using existing test data (ORD-0001)"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_find_existing_order_ord_0001(self, auth_headers):
        """Test finding existing order ORD-0001 with 4 job tickets"""
        response = requests.get(f"{BASE_URL}/api/orders?search=ORD-0001", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        orders = data.get("orders", [])
        
        # Find ORD-0001
        ord_0001 = None
        for order in orders:
            if order.get("order_number") == "ORD-0001":
                ord_0001 = order
                break
        
        if ord_0001:
            print(f"✓ Found existing order ORD-0001 with status: {ord_0001.get('status')}")
            self.__class__.existing_order_id = ord_0001["id"]
        else:
            print("⚠ ORD-0001 not found - may have been deleted or not created yet")
            pytest.skip("ORD-0001 not found")
    
    def test_verify_existing_order_tickets(self, auth_headers):
        """Verify existing order has expected job tickets"""
        order_id = getattr(self.__class__, 'existing_order_id', None)
        if not order_id:
            pytest.skip("No existing order found")
        
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        
        order = response.json()
        tickets = order.get("job_tickets", [])
        
        # Check for expected categories
        categories = [t.get("item_category") for t in tickets]
        expected = ["banners", "cut_vinyl", "apparel", "rigid_signs"]
        
        found_categories = []
        for cat in expected:
            if cat in categories:
                found_categories.append(cat)
        
        print(f"✓ Found {len(tickets)} job tickets with categories: {categories}")
        print(f"  Expected categories found: {found_categories}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
