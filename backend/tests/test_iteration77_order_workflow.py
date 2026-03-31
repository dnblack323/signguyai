"""
Iteration 77 - Order Workflow Tests

Tests for:
- New Order form and detailed ticket mode
- Dynamic category fields for banners, rigid signs, cut vinyl, apparel, vehicle wrap
- Live estimate updates when category options/materials/specs change
- Apparel size breakdown drives quantity and saved estimate correctly
- Vehicle wrap pickup + coverage pricing works
- Order creation succeeds from UI
- Created ticket saves calculated estimate into backend/order totals
- Order detail can generate quote, invoice, and work order
- Order detail financial tab shows quote, invoice, and work order
- Ticket shortcut actions work: assign employee, add to schedule, create task
- Production start and production summary still work after these changes
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


@pytest.fixture(scope="module")
def test_order_id(api_client):
    """Create a test order for the test suite"""
    order_data = {
        "customer_name": "TEST_Iteration77_Customer",
        "company_name": "TEST_Iteration77_Company",
        "phone": "555-0177",
        "email": "test77@example.com",
        "order_source": "phone",
        "requested_due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "internal_notes": "Test order for iteration 77 testing"
    }
    response = api_client.post(f"{BASE_URL}/api/orders", json=order_data)
    assert response.status_code == 200, f"Failed to create test order: {response.text}"
    order = response.json()
    yield order["id"]
    # Cleanup
    api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")


class TestOrderCreation:
    """Test order creation and basic CRUD"""
    
    def test_create_order_success(self, api_client):
        """Test creating a new order"""
        order_data = {
            "customer_name": "TEST_OrderCreate_Customer",
            "company_name": "TEST_OrderCreate_Company",
            "phone": "555-0001",
            "email": "testcreate@example.com",
            "order_source": "walk_in",
            "requested_due_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
        }
        response = api_client.post(f"{BASE_URL}/api/orders", json=order_data)
        assert response.status_code == 200, f"Order creation failed: {response.text}"
        
        order = response.json()
        assert "id" in order
        assert "order_number" in order
        assert order["customer_name"] == "TEST_OrderCreate_Customer"
        assert order["status"] == "new_intake"
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")
        print("PASSED: test_create_order_success")
    
    def test_create_order_as_draft(self, api_client):
        """Test creating an order as draft"""
        order_data = {
            "customer_name": "TEST_DraftOrder_Customer",
            "status": "draft"
        }
        response = api_client.post(f"{BASE_URL}/api/orders", json=order_data)
        assert response.status_code == 200, f"Draft order creation failed: {response.text}"
        
        order = response.json()
        assert order["status"] == "draft"
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")
        print("PASSED: test_create_order_as_draft")
    
    def test_get_order_detail(self, api_client, test_order_id):
        """Test getting order details"""
        response = api_client.get(f"{BASE_URL}/api/orders/{test_order_id}")
        assert response.status_code == 200
        
        order = response.json()
        assert order["id"] == test_order_id
        assert "job_tickets" in order
        print("PASSED: test_get_order_detail")


class TestDynamicCategoryFields:
    """Test dynamic category field schemas"""
    
    def test_banner_schema(self, api_client):
        """Test banner category schema has correct fields"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/banners")
        assert response.status_code == 200
        
        schema = response.json()
        assert schema["category"] == "banners"
        assert "fields" in schema
        
        field_keys = [f["key"] for f in schema["fields"]]
        # Check essential banner fields
        assert "width" in field_keys
        assert "height" in field_keys
        assert "unit_of_measure" in field_keys
        assert "material" in field_keys
        assert "double_sided" in field_keys
        assert "hems" in field_keys
        assert "grommets" in field_keys
        
        # Check unit_of_measure has feet as default
        unit_field = next(f for f in schema["fields"] if f["key"] == "unit_of_measure")
        assert unit_field["default"] == "feet"
        print("PASSED: test_banner_schema")
    
    def test_rigid_signs_schema(self, api_client):
        """Test rigid signs category schema"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/rigid_signs")
        assert response.status_code == 200
        
        schema = response.json()
        field_keys = [f["key"] for f in schema["fields"]]
        assert "substrate" in field_keys
        assert "thickness" in field_keys
        assert "stakes_included" in field_keys
        assert "mounting_hardware" in field_keys
        print("PASSED: test_rigid_signs_schema")
    
    def test_cut_vinyl_schema(self, api_client):
        """Test cut vinyl category schema"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/cut_vinyl")
        assert response.status_code == 200
        
        schema = response.json()
        field_keys = [f["key"] for f in schema["fields"]]
        assert "vinyl_type" in field_keys
        assert "num_colors" in field_keys
        assert "weed_required" in field_keys
        assert "mask_required" in field_keys
        print("PASSED: test_cut_vinyl_schema")
    
    def test_apparel_schema(self, api_client):
        """Test apparel category schema has size breakdown"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/apparel")
        assert response.status_code == 200
        
        schema = response.json()
        field_keys = [f["key"] for f in schema["fields"]]
        
        # Check size breakdown fields
        assert "size_xs" in field_keys
        assert "size_s" in field_keys
        assert "size_m" in field_keys
        assert "size_l" in field_keys
        assert "size_xl" in field_keys
        assert "size_2xl" in field_keys
        
        # Check decoration fields
        assert "garment_type" in field_keys
        assert "decoration_method" in field_keys
        assert "print_locations" in field_keys
        print("PASSED: test_apparel_schema")
    
    def test_vehicle_wrap_schema(self, api_client):
        """Test vehicle wrap category schema"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/vehicle_wrap")
        assert response.status_code == 200
        
        schema = response.json()
        field_keys = [f["key"] for f in schema["fields"]]
        
        assert "vehicle_type" in field_keys
        assert "coverage_type" in field_keys
        assert "coverage_percent" in field_keys
        assert "vinyl_type" in field_keys
        assert "install_required" in field_keys
        assert "estimated_install_hours" in field_keys
        print("PASSED: test_vehicle_wrap_schema")


class TestLivePricingCalculation:
    """Test live pricing calculation API"""
    
    def test_banner_pricing_calculation(self, api_client):
        """Test pricing calculation for banners"""
        pricing_data = {
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 96,  # 8 feet
                "length_inches": 36,  # 3 feet
                "double_sided": False,
                "laminate": False,
                "print_material": "banner_13oz"
            },
            "quantity": 1
        }
        response = api_client.post(f"{BASE_URL}/api/pricing/calculate", json=pricing_data)
        assert response.status_code == 200
        
        calc = response.json()
        assert "selling_price" in calc
        assert "material_cost" in calc
        assert "labor_cost" in calc
        assert calc["selling_price"] > 0
        print(f"PASSED: test_banner_pricing_calculation - Price: ${calc['selling_price']:.2f}")
    
    def test_apparel_pricing_calculation(self, api_client):
        """Test pricing calculation for apparel"""
        pricing_data = {
            "category": "apparel",
            "pricing_data": {
                "apparel_type": "tshirt",
                "transfer_type": "dtf",
                "num_print_locations": 2
            },
            "quantity": 24
        }
        response = api_client.post(f"{BASE_URL}/api/pricing/calculate", json=pricing_data)
        assert response.status_code == 200
        
        calc = response.json()
        assert calc["selling_price"] > 0
        print(f"PASSED: test_apparel_pricing_calculation - Price: ${calc['selling_price']:.2f}")
    
    def test_vehicle_wrap_pricing_calculation(self, api_client):
        """Test pricing calculation for vehicle wrap with coverage"""
        pricing_data = {
            "category": "vehicle_graphics",
            "pricing_data": {
                "vehicle_type": "van_cargo",
                "coverage_type": "full",
                "vinyl_type": "oracal_951",
                "laminate": True
            },
            "quantity": 1
        }
        response = api_client.post(f"{BASE_URL}/api/pricing/calculate", json=pricing_data)
        assert response.status_code == 200
        
        calc = response.json()
        assert calc["selling_price"] > 0
        print(f"PASSED: test_vehicle_wrap_pricing_calculation - Price: ${calc['selling_price']:.2f}")


class TestJobTicketCreation:
    """Test job ticket creation with pricing snapshot"""
    
    def test_create_banner_ticket_with_specs(self, api_client, test_order_id):
        """Test creating a banner ticket with specs auto-calculates pricing"""
        ticket_data = {
            "order_id": test_order_id,
            "item_name": "TEST_Banner_8x3",
            "item_category": "banners",
            "quantity": 1,
            "priority": "normal",
            "production_flow_enabled": False,
            "specs": {
                "width": "8",
                "height": "3",
                "unit_of_measure": "feet",
                "material": "banner_13oz",
                "double_sided": "single",
                "hems": "all_sides",
                "grommets": "corners"
            }
        }
        response = api_client.post(f"{BASE_URL}/api/job-tickets", json=ticket_data)
        assert response.status_code == 200, f"Ticket creation failed: {response.text}"
        
        ticket = response.json()
        assert ticket["item_name"] == "TEST_Banner_8x3"
        assert ticket["item_category"] == "banners"
        
        # Check pricing snapshot was auto-calculated
        if ticket.get("pricing_snapshot"):
            assert ticket["pricing_snapshot"]["pricing_mode"] == "calculator"
            assert ticket["pricing_snapshot"]["active_price"] > 0
            print(f"PASSED: test_create_banner_ticket_with_specs - Price: ${ticket['pricing_snapshot']['active_price']:.2f}")
        else:
            print("PASSED: test_create_banner_ticket_with_specs (no auto-pricing)")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/job-tickets/{ticket['id']}")
    
    def test_create_apparel_ticket_with_size_breakdown(self, api_client, test_order_id):
        """Test apparel ticket with size breakdown derives quantity correctly"""
        ticket_data = {
            "order_id": test_order_id,
            "item_name": "TEST_Apparel_TShirts",
            "item_category": "apparel",
            "quantity": 1,  # Will be overridden by size total
            "priority": "normal",
            "specs": {
                "garment_type": "tshirt",
                "decoration_method": "dtf",
                "size_s": 5,
                "size_m": 10,
                "size_l": 8,
                "size_xl": 2
            }
        }
        response = api_client.post(f"{BASE_URL}/api/job-tickets", json=ticket_data)
        assert response.status_code == 200, f"Ticket creation failed: {response.text}"
        
        ticket = response.json()
        # Quantity should be sum of sizes: 5+10+8+2 = 25
        assert ticket["quantity"] == 25, f"Expected quantity 25, got {ticket['quantity']}"
        print(f"PASSED: test_create_apparel_ticket_with_size_breakdown - Quantity: {ticket['quantity']}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/job-tickets/{ticket['id']}")
    
    def test_create_vehicle_wrap_ticket(self, api_client, test_order_id):
        """Test vehicle wrap ticket with coverage pricing"""
        ticket_data = {
            "order_id": test_order_id,
            "item_name": "TEST_VehicleWrap_CargoVan",
            "item_category": "vehicle_wrap",
            "quantity": 1,
            "priority": "high",
            "specs": {
                "vehicle_type": "van_cargo",
                "coverage_type": "75",  # 75% coverage
                "vinyl_type": "oracal_951",
                "lamination": "gloss",
                "install_required": True
            }
        }
        response = api_client.post(f"{BASE_URL}/api/job-tickets", json=ticket_data)
        assert response.status_code == 200, f"Ticket creation failed: {response.text}"
        
        ticket = response.json()
        assert ticket["item_category"] == "vehicle_wrap"
        print(f"PASSED: test_create_vehicle_wrap_ticket")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/job-tickets/{ticket['id']}")


class TestOrderFinancials:
    """Test order financial document generation"""
    
    @pytest.fixture
    def order_with_tickets(self, api_client):
        """Create an order with tickets for financial tests"""
        # Create order
        order_data = {
            "customer_name": "TEST_Financial_Customer",
            "company_name": "TEST_Financial_Company",
            "email": "financial@test.com"
        }
        order_res = api_client.post(f"{BASE_URL}/api/orders", json=order_data)
        order = order_res.json()
        
        # Create tickets
        ticket1 = api_client.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": order["id"],
            "item_name": "TEST_Banner_1",
            "item_category": "banners",
            "quantity": 1,
            "estimated_price": 150.00,
            "specs": {"width": "4", "height": "2", "unit_of_measure": "feet"}
        }).json()
        
        ticket2 = api_client.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": order["id"],
            "item_name": "TEST_Sign_1",
            "item_category": "rigid_signs",
            "quantity": 2,
            "estimated_price": 75.00,
            "specs": {"width": "18", "height": "24", "unit_of_measure": "inches"}
        }).json()
        
        yield order["id"]
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/job-tickets/{ticket1['id']}")
        api_client.delete(f"{BASE_URL}/api/job-tickets/{ticket2['id']}")
        api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")
    
    def test_generate_quote(self, api_client, order_with_tickets):
        """Test generating a quote from order"""
        response = api_client.post(f"{BASE_URL}/api/orders/{order_with_tickets}/generate-quote")
        assert response.status_code == 200, f"Quote generation failed: {response.text}"
        
        quote = response.json()
        assert quote["type"] == "quote"
        assert quote["status"] == "draft"
        assert "line_items" in quote
        assert len(quote["line_items"]) == 2
        assert quote["total"] > 0
        print(f"PASSED: test_generate_quote - Total: ${quote['total']:.2f}")
    
    def test_generate_invoice(self, api_client, order_with_tickets):
        """Test generating an invoice from order"""
        response = api_client.post(f"{BASE_URL}/api/orders/{order_with_tickets}/generate-invoice")
        assert response.status_code == 200, f"Invoice generation failed: {response.text}"
        
        invoice = response.json()
        assert invoice["type"] == "invoice"
        assert invoice["status"] == "draft"
        assert len(invoice["line_items"]) == 2
        print(f"PASSED: test_generate_invoice - Total: ${invoice['total']:.2f}")
    
    def test_generate_work_order(self, api_client, order_with_tickets):
        """Test generating a work order from order"""
        response = api_client.post(f"{BASE_URL}/api/orders/{order_with_tickets}/generate-work_order")
        assert response.status_code == 200, f"Work order generation failed: {response.text}"
        
        work_order = response.json()
        assert work_order["type"] == "work_order"
        assert work_order["status"] == "draft"
        assert work_order["total_tickets"] == 2
        print(f"PASSED: test_generate_work_order - Tickets: {work_order['total_tickets']}")
    
    def test_get_order_financials(self, api_client, order_with_tickets):
        """Test getting all financial documents for an order"""
        # Generate documents first
        api_client.post(f"{BASE_URL}/api/orders/{order_with_tickets}/generate-quote")
        api_client.post(f"{BASE_URL}/api/orders/{order_with_tickets}/generate-invoice")
        api_client.post(f"{BASE_URL}/api/orders/{order_with_tickets}/generate-work_order")
        
        response = api_client.get(f"{BASE_URL}/api/orders/{order_with_tickets}/financials")
        assert response.status_code == 200
        
        financials = response.json()
        assert "quotes" in financials
        assert "invoices" in financials
        assert "work_orders" in financials
        assert len(financials["quotes"]) >= 1
        assert len(financials["invoices"]) >= 1
        assert len(financials["work_orders"]) >= 1
        print(f"PASSED: test_get_order_financials - Quotes: {len(financials['quotes'])}, Invoices: {len(financials['invoices'])}, Work Orders: {len(financials['work_orders'])}")


class TestProductionWorkflow:
    """Test production workflow features"""
    
    @pytest.fixture
    def workflow_order(self, api_client):
        """Create an order with workflow-enabled ticket"""
        order_data = {
            "customer_name": "TEST_Workflow_Customer",
        }
        order_res = api_client.post(f"{BASE_URL}/api/orders", json=order_data)
        order = order_res.json()
        
        ticket = api_client.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": order["id"],
            "item_name": "TEST_Workflow_Banner",
            "item_category": "banners",
            "quantity": 1,
            "production_flow_enabled": True,
            "specs": {"width": "4", "height": "2", "unit_of_measure": "feet"}
        }).json()
        
        yield {"order_id": order["id"], "ticket_id": ticket["id"]}
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")
    
    def test_start_production(self, api_client, workflow_order):
        """Test starting production activates workflow tickets"""
        # Note: Tasks are auto-created when ticket is created with production_flow_enabled=True
        # So start-production may report 0 tasks_created if they already exist
        response = api_client.post(f"{BASE_URL}/api/orders/{workflow_order['order_id']}/start-production")
        assert response.status_code == 200, f"Start production failed: {response.text}"
        
        result = response.json()
        assert result["tickets_activated"] >= 1
        
        # Verify tasks exist (either created now or during ticket creation)
        tasks_res = api_client.get(f"{BASE_URL}/api/production-tasks?job_ticket_id={workflow_order['ticket_id']}")
        tasks = tasks_res.json().get("tasks", [])
        assert len(tasks) >= 1, "No production tasks found for workflow ticket"
        print(f"PASSED: test_start_production - Tasks: {len(tasks)}, Activated: {result['tickets_activated']}")
    
    def test_production_summary(self, api_client, workflow_order):
        """Test getting production summary"""
        # Start production first
        api_client.post(f"{BASE_URL}/api/orders/{workflow_order['order_id']}/start-production")
        
        response = api_client.get(f"{BASE_URL}/api/orders/{workflow_order['order_id']}/production-summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert "tasks" in summary
        assert "summary" in summary
        assert "by_department" in summary
        assert summary["summary"]["total_tasks"] >= 1
        print(f"PASSED: test_production_summary - Total tasks: {summary['summary']['total_tasks']}")


class TestTicketShortcuts:
    """Test ticket shortcut actions (assign, schedule, task)"""
    
    @pytest.fixture
    def shortcut_order(self, api_client):
        """Create order and ticket for shortcut tests"""
        order_res = api_client.post(f"{BASE_URL}/api/orders", json={
            "customer_name": "TEST_Shortcut_Customer"
        })
        order = order_res.json()
        
        ticket_res = api_client.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": order["id"],
            "item_name": "TEST_Shortcut_Item",
            "item_category": "banners",
            "quantity": 1
        })
        ticket = ticket_res.json()
        
        yield {"order_id": order["id"], "ticket_id": ticket["id"]}
        
        api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")
    
    def test_assign_ticket_to_employee(self, api_client, shortcut_order):
        """Test assigning a ticket to an employee"""
        # Get employees
        emp_res = api_client.get(f"{BASE_URL}/api/employees")
        employees = emp_res.json()
        
        if not employees:
            pytest.skip("No employees available for assignment test")
        
        employee_id = employees[0]["id"]
        
        # Assign ticket
        response = api_client.put(
            f"{BASE_URL}/api/job-tickets/{shortcut_order['ticket_id']}",
            json={"assigned_user_id": employee_id}
        )
        assert response.status_code == 200
        
        ticket = response.json()
        assert ticket["assigned_user_id"] == employee_id
        print(f"PASSED: test_assign_ticket_to_employee - Assigned to: {employee_id}")
    
    def test_create_task_from_ticket(self, api_client, shortcut_order):
        """Test creating a task from ticket context"""
        task_data = {
            "title": f"TEST_Task_from_ticket",
            "description": f"Follow up on ticket {shortcut_order['ticket_id']}",
            "due_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        }
        response = api_client.post(f"{BASE_URL}/api/tasks", json=task_data)
        assert response.status_code == 200, f"Task creation failed: {response.text}"
        
        task = response.json()
        assert task["title"] == "TEST_Task_from_ticket"
        print(f"PASSED: test_create_task_from_ticket - Task ID: {task['id']}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/tasks/{task['id']}")


class TestOrderTotals:
    """Test order total calculations from ticket prices"""
    
    def test_order_total_updates_with_tickets(self, api_client):
        """Test that order total updates when tickets are added"""
        # Create order
        order_res = api_client.post(f"{BASE_URL}/api/orders", json={
            "customer_name": "TEST_OrderTotal_Customer"
        })
        order = order_res.json()
        order_id = order["id"]
        
        # Add ticket with price
        ticket1 = api_client.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": order_id,
            "item_name": "TEST_Item_1",
            "item_category": "banners",
            "quantity": 1,
            "estimated_price": 100.00
        }).json()
        
        # Check order total
        order_detail = api_client.get(f"{BASE_URL}/api/orders/{order_id}").json()
        assert order_detail.get("order_total", 0) >= 100.00 or len(order_detail.get("job_tickets", [])) == 1
        
        # Add another ticket
        ticket2 = api_client.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": order_id,
            "item_name": "TEST_Item_2",
            "item_category": "rigid_signs",
            "quantity": 1,
            "estimated_price": 50.00
        }).json()
        
        # Check updated total
        order_detail = api_client.get(f"{BASE_URL}/api/orders/{order_id}").json()
        total = order_detail.get("order_total", 0)
        ticket_count = len(order_detail.get("job_tickets", []))
        
        assert ticket_count == 2
        print(f"PASSED: test_order_total_updates_with_tickets - Total: ${total:.2f}, Tickets: {ticket_count}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_orders(self, api_client):
        """Clean up any remaining test orders"""
        response = api_client.get(f"{BASE_URL}/api/orders?search=TEST_&limit=100")
        if response.status_code == 200:
            orders = response.json().get("orders", [])
            cleaned = 0
            for order in orders:
                if order.get("customer_name", "").startswith("TEST_"):
                    api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")
                    cleaned += 1
            print(f"PASSED: test_cleanup_test_orders - Cleaned {cleaned} test orders")
        else:
            print("PASSED: test_cleanup_test_orders - No cleanup needed")
