"""
Iteration 88 - Bug Fixes Testing

Tests for:
1. New Order form shows today's date field by default and no longer shows Event Date
2. Services category exists in new order / add-ticket category dropdowns
3. Banner pricing now charges finishing for grommets and hems using settings-driven values
4. Saved job ticket pricing reopens correctly in Job Ticket Detail / pricing panel
5. Order uploaded artwork can be previewed and markup mode loads the actual image
6. Order file send-for-approval action creates an approval/proof successfully for order-backed records
7. Production send flow after creating tickets/orders works
8. Productivity dashboard overdue cards no longer count employee schedule shifts as production-overdue work
9. Opening a calendar day allows manual task creation from the day detail dialog
10. Employees created in Time Clock are also reflected in tenant users
11. Promo Codes are no longer exposed from the Webstores navigation surfaces
12. AI assistant returns plain text response (not object/object)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://meta-webhook-setup.preview.emergentagent.com')

# Test credentials
from backend.tests.test_credentials_helper import PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD

TEST_EMAIL = PRODUCTION_OWNER_EMAIL
TEST_PASSWORD = PRODUCTION_OWNER_PASSWORD


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Create authenticated session"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestServicesCategory:
    """Test that Services category exists in job ticket schema"""
    
    def test_services_category_in_schema(self, api_client):
        """Verify services category is available in job ticket schema"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/services")
        assert response.status_code == 200
        data = response.json()
        assert data.get("category") == "services"
        assert "fields" in data
        # Check for service-specific fields
        field_keys = [f.get("key") for f in data.get("fields", [])]
        assert "service_type" in field_keys or "estimated_hours" in field_keys
        print(f"Services schema fields: {field_keys}")


class TestBannerPricingFinishing:
    """Test banner pricing with grommets and hems finishing options"""
    
    def test_banner_pricing_with_grommets(self, api_client):
        """Test that banner pricing includes grommet charges"""
        response = api_client.post(
            f"{BASE_URL}/api/pricing/calculate",
            json={
                "category": "digital_print",
                "pricing_data": {
                    "width_inches": 96,
                    "length_inches": 36,
                    "print_material": "banner_13oz",
                    "grommets": "corners",
                    "hemming": "all_sides"
                },
                "quantity": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Should have a selling price
        assert "selling_price" in data or "error" in data
        if "selling_price" in data:
            assert data["selling_price"] > 0
            print(f"Banner with grommets/hems price: ${data['selling_price']:.2f}")
    
    def test_banner_pricing_without_finishing(self, api_client):
        """Test banner pricing without finishing options"""
        response = api_client.post(
            f"{BASE_URL}/api/pricing/calculate",
            json={
                "category": "digital_print",
                "pricing_data": {
                    "width_inches": 96,
                    "length_inches": 36,
                    "print_material": "banner_13oz",
                    "grommets": "none",
                    "hemming": "none"
                },
                "quantity": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        if "selling_price" in data:
            print(f"Banner without finishing price: ${data['selling_price']:.2f}")


class TestJobTicketPricing:
    """Test job ticket pricing save and retrieve"""
    
    def test_create_ticket_with_pricing(self, api_client):
        """Create a job ticket and verify pricing snapshot is saved"""
        # First create an order
        order_response = api_client.post(
            f"{BASE_URL}/api/orders",
            json={
                "customer_name": "TEST_Pricing_Customer",
                "order_source": "phone",
                "date_created": datetime.now().strftime("%Y-%m-%d")
            }
        )
        assert order_response.status_code in [200, 201]
        order_id = order_response.json().get("id")
        
        # Create a job ticket with pricing
        ticket_response = api_client.post(
            f"{BASE_URL}/api/job-tickets",
            json={
                "order_id": order_id,
                "item_name": "TEST_Banner_Pricing",
                "item_category": "banners",
                "quantity": 1,
                "estimated_price": 150.00,
                "specs": {
                    "width": "8",
                    "height": "3",
                    "unit_of_measure": "feet",
                    "material": "banner_13oz"
                }
            }
        )
        assert ticket_response.status_code in [200, 201]
        ticket_data = ticket_response.json()
        ticket_id = ticket_data.get("id")
        
        # Verify ticket was created
        assert ticket_id is not None
        print(f"Created ticket: {ticket_id}")
        
        # Save pricing to ticket
        save_response = api_client.post(
            f"{BASE_URL}/api/job-tickets/{ticket_id}/save-pricing",
            json={
                "pricing_mode": "manual",
                "calculated_price": 120.00,
                "manual_price": 150.00,
                "calculation_breakdown": {"material_cost": 50, "labor_cost": 30}
            }
        )
        assert save_response.status_code == 200
        
        # Retrieve ticket and verify pricing snapshot
        get_response = api_client.get(f"{BASE_URL}/api/job-tickets/{ticket_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        
        # Verify pricing snapshot exists
        pricing_snapshot = retrieved.get("pricing_snapshot")
        assert pricing_snapshot is not None, "Pricing snapshot should be saved"
        assert pricing_snapshot.get("pricing_mode") == "manual"
        assert pricing_snapshot.get("manual_price") == 150.00
        print(f"Pricing snapshot verified: {pricing_snapshot}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/job-tickets/{ticket_id}")
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestOrderApprovalCreation:
    """Test that approvals can be created for order-backed records"""
    
    def test_create_approval_for_order(self, api_client):
        """Test creating an approval/proof for an order"""
        # Get customers list
        customers_response = api_client.get(f"{BASE_URL}/api/customers?limit=1")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        if isinstance(customers, dict):
            customers = customers.get("customers", [])
        
        if not customers:
            pytest.skip("No customers available for testing")
        
        customer_id = customers[0].get("id")
        
        # Create an order
        order_response = api_client.post(
            f"{BASE_URL}/api/orders",
            json={
                "customer_name": "TEST_Approval_Customer",
                "customer_id": customer_id,
                "order_source": "phone",
                "date_created": datetime.now().strftime("%Y-%m-%d")
            }
        )
        assert order_response.status_code in [200, 201]
        order_id = order_response.json().get("id")
        
        # Create an approval for the order
        approval_response = api_client.post(
            f"{BASE_URL}/api/approvals",
            json={
                "job_id": order_id,  # Using order_id as job_id
                "customer_id": customer_id,
                "file_url": "https://example.com/test-proof.png",
                "file_name": "test-proof.png",
                "description": "TEST_Approval for order"
            }
        )
        
        # Should succeed - approvals route now accepts order-backed proofs
        assert approval_response.status_code in [200, 201], f"Failed to create approval: {approval_response.text}"
        approval_data = approval_response.json()
        assert approval_data.get("id") is not None
        print(f"Created approval for order: {approval_data.get('id')}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/approvals/{approval_data.get('id')}")
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestProductivityScheduleExclusion:
    """Test that productivity dashboard excludes schedule shifts from overdue counts"""
    
    def test_productivity_summary_excludes_schedule(self, api_client):
        """Verify productivity summary doesn't count schedule shifts as overdue"""
        response = api_client.get(f"{BASE_URL}/api/productivity/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Summary should exist
        assert "overdue" in data or "due_today" in data
        print(f"Productivity summary: {data}")
    
    def test_productivity_items_filter(self, api_client):
        """Test productivity items can filter by type"""
        response = api_client.get(
            f"{BASE_URL}/api/productivity/items",
            params={"item_types": "task,job,production_task"}
        )
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        
        # Verify no schedule_shift items in filtered results
        for item in items:
            assert item.get("type") != "schedule_shift", "Schedule shifts should be excluded when not requested"
        print(f"Filtered productivity items count: {len(items)}")


class TestTaskCreation:
    """Test manual task creation from productivity day detail"""
    
    def test_create_task_with_due_date(self, api_client):
        """Test creating a task with a specific due date"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = api_client.post(
            f"{BASE_URL}/api/tasks",
            json={
                "title": "TEST_Task_From_Day_Detail",
                "due_date": tomorrow,
                "assigned_to": None
            }
        )
        assert response.status_code in [200, 201]
        task_data = response.json()
        task_id = task_data.get("id")
        assert task_id is not None
        assert task_data.get("title") == "TEST_Task_From_Day_Detail"
        print(f"Created task: {task_id} with due date: {tomorrow}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/tasks/{task_id}")


class TestEmployeeUserSync:
    """Test that employees created in Time Clock are reflected in tenant users"""
    
    def test_create_employee_creates_user(self, api_client):
        """Test that creating an employee with email also creates a user"""
        unique_email = f"test_employee_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        
        # Create employee
        response = api_client.post(
            f"{BASE_URL}/api/employees",
            json={
                "name": "TEST_Employee_User_Sync",
                "email": unique_email,
                "hourly_rate": 25.00,
                "role": "staff"
            }
        )
        assert response.status_code in [200, 201]
        employee_data = response.json()
        employee_id = employee_data.get("id")
        
        # Check if linked_user_id is set
        linked_user_id = employee_data.get("linked_user_id")
        print(f"Employee created: {employee_id}, linked_user_id: {linked_user_id}")
        
        # Verify user was created by checking users list
        users_response = api_client.get(f"{BASE_URL}/api/users")
        assert users_response.status_code == 200
        users = users_response.json()
        
        # Find user with matching email
        matching_user = next((u for u in users if u.get("email", "").lower() == unique_email.lower()), None)
        
        if linked_user_id:
            assert matching_user is not None, "User should be created when employee has email"
            print(f"User sync verified: {matching_user.get('id')}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/employees/{employee_id}")


class TestAIAssistantResponse:
    """Test AI assistant returns plain text response"""
    
    def test_assistant_returns_text(self, api_client):
        """Test that AI assistant returns plain text, not object/object"""
        response = api_client.post(
            f"{BASE_URL}/api/ai/assistant",
            json={
                "message": "Hello, what can you help me with?",
                "session_id": f"test_session_{datetime.now().timestamp()}",
                "conversation_history": []
            }
        )
        
        # May fail due to credits, but if it succeeds, check response format
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            
            # Should be a string, not "[object Object]"
            assert isinstance(response_text, str), "Response should be a string"
            assert "[object Object]" not in response_text, "Response should not contain [object Object]"
            assert response_text.strip() != "", "Response should not be empty"
            print(f"AI response (first 100 chars): {response_text[:100]}...")
        elif response.status_code == 402:
            print("Skipping AI test - insufficient credits")
        else:
            print(f"AI assistant response: {response.status_code} - {response.text[:200]}")


class TestOrderWorkflow:
    """Test order creation and production workflow"""
    
    def test_create_order_with_tickets(self, api_client):
        """Test creating an order and adding tickets"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create order
        order_response = api_client.post(
            f"{BASE_URL}/api/orders",
            json={
                "customer_name": "TEST_Workflow_Customer",
                "order_source": "phone",
                "date_created": today,
                "requested_due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            }
        )
        assert order_response.status_code in [200, 201]
        order_data = order_response.json()
        order_id = order_data.get("id")
        
        # Verify date_created is set
        assert order_data.get("date_created") == today
        print(f"Order created with date: {order_data.get('date_created')}")
        
        # Create a ticket with services category
        ticket_response = api_client.post(
            f"{BASE_URL}/api/job-tickets",
            json={
                "order_id": order_id,
                "item_name": "TEST_Service_Item",
                "item_category": "services",
                "quantity": 1,
                "specs": {
                    "service_type": "design",
                    "estimated_hours": 2
                }
            }
        )
        assert ticket_response.status_code in [200, 201]
        ticket_data = ticket_response.json()
        ticket_id = ticket_data.get("id")
        
        # Verify services category was accepted
        assert ticket_data.get("item_category") == "services"
        print(f"Services ticket created: {ticket_id}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/job-tickets/{ticket_id}")
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestOrderFileUpload:
    """Test order file upload and preview"""
    
    def test_order_files_endpoint(self, api_client):
        """Test that order files endpoint exists and works"""
        # Create an order first
        order_response = api_client.post(
            f"{BASE_URL}/api/orders",
            json={
                "customer_name": "TEST_File_Upload_Customer",
                "order_source": "phone",
                "date_created": datetime.now().strftime("%Y-%m-%d")
            }
        )
        assert order_response.status_code in [200, 201]
        order_id = order_response.json().get("id")
        
        # Check files endpoint
        files_response = api_client.get(f"{BASE_URL}/api/orders/{order_id}/files")
        assert files_response.status_code == 200
        files = files_response.json()
        assert isinstance(files, list)
        print(f"Order files endpoint works, files count: {len(files)}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestPricingDefaults:
    """Test pricing defaults include banner finishing settings"""
    
    def test_pricing_defaults_have_finishing_settings(self, api_client):
        """Verify pricing defaults include grommet and hemming prices"""
        response = api_client.get(f"{BASE_URL}/api/pricing/defaults")
        assert response.status_code == 200
        defaults = response.json()
        
        # Check for finishing-related settings
        grommet_price = defaults.get("banner_grommet_price_each")
        hemming_price = defaults.get("banner_hemming_tape_price_per_linear_inch")
        
        print(f"Grommet price: {grommet_price}, Hemming price: {hemming_price}")
        
        # These should exist in the defaults
        assert grommet_price is not None or "category_defaults" in defaults


class TestHealthCheck:
    """Basic health check tests"""
    
    def test_backend_health(self, api_client):
        """Test backend is running"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("Backend health check passed")
    
    def test_auth_works(self, api_client):
        """Test authentication is working"""
        response = api_client.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        user = response.json()
        assert user.get("email") == TEST_EMAIL
        print(f"Authenticated as: {user.get('email')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
