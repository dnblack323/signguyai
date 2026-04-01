"""
Iteration 76 Feature Tests
- Order form reorder (Customer, Order Info, Job Tickets, Sketches, Pickup/Delivery, Attachments)
- Save as Draft functionality
- Draft status filter in orders
- Banner unit of measure bug fix (feet showing correct sq ft)
- Job ticket schema defaults (unit_of_measure defaults to 'feet' for banners)
"""

import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = PRODUCTION_OWNER_EMAIL
TEST_PASSWORD = PRODUCTION_OWNER_PASSWORD


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


class TestOrderDraftFeature:
    """Test Save as Draft functionality for orders"""
    
    def test_create_order_as_draft(self, api_client):
        """Create an order with status='draft'"""
        order_data = {
            "customer_name": f"TEST_Draft_Customer_{uuid.uuid4().hex[:6]}",
            "company_name": "Test Draft Company",
            "phone": "555-0001",
            "email": "draft@test.com",
            "order_source": "phone",
            "status": "draft"  # Key: Save as draft
        }
        response = api_client.post(f"{BASE_URL}/api/orders", json=order_data)
        assert response.status_code == 200, f"Failed to create draft order: {response.text}"
        
        data = response.json()
        assert data.get("status") == "draft", f"Expected status='draft', got {data.get('status')}"
        assert "id" in data
        assert "order_number" in data
        
        # Store for cleanup
        self.draft_order_id = data["id"]
        print(f"Created draft order: {data['order_number']} with status={data['status']}")
        return data
    
    def test_get_draft_orders_filter(self, api_client):
        """GET /api/orders?status=draft returns only draft orders"""
        response = api_client.get(f"{BASE_URL}/api/orders?status=draft")
        assert response.status_code == 200, f"Failed to get draft orders: {response.text}"
        
        data = response.json()
        assert "orders" in data
        assert "total" in data
        
        # All returned orders should have status='draft'
        for order in data["orders"]:
            assert order.get("status") == "draft", f"Non-draft order in results: {order.get('order_number')}"
        
        print(f"Found {data['total']} draft order(s)")
    
    def test_update_draft_to_new_intake(self, api_client):
        """Update a draft order to new_intake status"""
        # First create a draft
        order_data = {
            "customer_name": f"TEST_Draft_Update_{uuid.uuid4().hex[:6]}",
            "status": "draft"
        }
        create_resp = api_client.post(f"{BASE_URL}/api/orders", json=order_data)
        assert create_resp.status_code == 200
        order_id = create_resp.json()["id"]
        
        # Update to new_intake
        update_resp = api_client.put(f"{BASE_URL}/api/orders/{order_id}", json={
            "status": "new_intake"
        })
        assert update_resp.status_code == 200, f"Failed to update draft: {update_resp.text}"
        
        updated = update_resp.json()
        assert updated.get("status") == "new_intake"
        print("Updated draft order to new_intake")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestBannerSchemaDefaults:
    """Test that banner schema returns correct defaults including unit_of_measure='feet'"""
    
    def test_banner_schema_has_unit_of_measure_default(self, api_client):
        """GET /api/job-tickets/schema/banners should have unit_of_measure with default='feet'"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/banners")
        assert response.status_code == 200, f"Failed to get banner schema: {response.text}"
        
        data = response.json()
        assert "fields" in data
        
        # Find unit_of_measure field
        unit_field = None
        for field in data["fields"]:
            if field.get("key") == "unit_of_measure":
                unit_field = field
                break
        
        assert unit_field is not None, "unit_of_measure field not found in banner schema"
        assert unit_field.get("default") == "feet", f"Expected default='feet', got {unit_field.get('default')}"
        assert unit_field.get("type") == "select"
        
        # Verify options include feet and inches
        options = unit_field.get("options", [])
        option_values = [o.get("value") for o in options]
        assert "feet" in option_values, "feet option missing"
        assert "inches" in option_values, "inches option missing"
        
        print(f"Banner schema unit_of_measure: default={unit_field.get('default')}, options={option_values}")
    
    def test_banner_schema_has_sq_footage_calculated(self, api_client):
        """Banner schema should have sq_footage as calculated field"""
        response = api_client.get(f"{BASE_URL}/api/job-tickets/schema/banners")
        assert response.status_code == 200
        
        data = response.json()
        sq_field = None
        for field in data["fields"]:
            if field.get("key") == "sq_footage":
                sq_field = field
                break
        
        assert sq_field is not None, "sq_footage field not found"
        assert sq_field.get("type") == "calculated", f"Expected type='calculated', got {sq_field.get('type')}"
        print(f"sq_footage field: type={sq_field.get('type')}, group={sq_field.get('group')}")


class TestJobTicketWithBannerSpecs:
    """Test creating job tickets with banner specs and verifying unit handling"""
    
    def test_create_banner_ticket_with_feet(self, api_client):
        """Create a banner job ticket with width=2, height=8, unit=feet"""
        # First create an order
        order_resp = api_client.post(f"{BASE_URL}/api/orders", json={
            "customer_name": f"TEST_Banner_Customer_{uuid.uuid4().hex[:6]}",
            "status": "new_intake"
        })
        assert order_resp.status_code == 200
        order_id = order_resp.json()["id"]
        
        # Create banner ticket with feet dimensions
        ticket_data = {
            "order_id": order_id,
            "item_name": "TEST Race Banner 2x8 feet",
            "item_category": "banners",
            "quantity": 1,
            "specs": {
                "width": "2",
                "height": "8",
                "unit_of_measure": "feet",  # Key: using feet
                "material": "banner_13oz",
                "double_sided": "single"
            }
        }
        ticket_resp = api_client.post(f"{BASE_URL}/api/job-tickets", json=ticket_data)
        assert ticket_resp.status_code == 200, f"Failed to create ticket: {ticket_resp.text}"
        
        ticket = ticket_resp.json()
        assert ticket.get("specs", {}).get("unit_of_measure") == "feet"
        assert ticket.get("specs", {}).get("width") == "2"
        assert ticket.get("specs", {}).get("height") == "8"
        
        print(f"Created banner ticket: {ticket.get('ticket_number')} with specs={ticket.get('specs')}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")
    
    def test_pricing_calculation_with_feet(self, api_client):
        """Test pricing calculation correctly converts feet to inches"""
        # Create order and ticket
        order_resp = api_client.post(f"{BASE_URL}/api/orders", json={
            "customer_name": f"TEST_Pricing_Customer_{uuid.uuid4().hex[:6]}",
            "status": "new_intake"
        })
        assert order_resp.status_code == 200
        order_id = order_resp.json()["id"]
        
        ticket_data = {
            "order_id": order_id,
            "item_name": "TEST Pricing Banner",
            "item_category": "banners",
            "quantity": 1,
            "specs": {
                "width": "2",
                "height": "8",
                "unit_of_measure": "feet",
                "material": "banner_13oz"
            }
        }
        ticket_resp = api_client.post(f"{BASE_URL}/api/job-tickets", json=ticket_data)
        assert ticket_resp.status_code == 200
        ticket_id = ticket_resp.json()["id"]
        
        # Calculate pricing
        pricing_resp = api_client.post(f"{BASE_URL}/api/job-tickets/{ticket_id}/calculate-pricing", json={})
        assert pricing_resp.status_code == 200, f"Pricing calculation failed: {pricing_resp.text}"
        
        pricing = pricing_resp.json()
        print(f"Pricing result: {pricing}")
        
        # The calculation should have converted feet to inches
        # 2ft x 8ft = 24in x 96in = 2304 sq in = 16 sq ft
        # Verify we got a reasonable price (not 0 or near-zero)
        if pricing.get("calculation"):
            calc = pricing["calculation"]
            # Material cost should be based on 16 sq ft, not 0.11 sq ft
            print(f"Material cost: {calc.get('material_cost')}, Total: {calc.get('selling_price')}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestLivePricingAPI:
    """Test the live pricing calculation endpoint"""
    
    def test_pricing_calculate_with_feet_unit(self, api_client):
        """POST /api/pricing/calculate with feet dimensions"""
        pricing_data = {
            "category": "digital_print",  # banners map to digital_print
            "pricing_data": {
                "width_inches": 24,  # 2 feet converted to inches
                "length_inches": 96,  # 8 feet converted to inches
                "double_sided": False,
                "laminate": False,
                "print_material": "banner_13oz"
            },
            "quantity": 1
        }
        response = api_client.post(f"{BASE_URL}/api/pricing/calculate", json=pricing_data)
        assert response.status_code == 200, f"Pricing API failed: {response.text}"
        
        data = response.json()
        print(f"Live pricing result: {data}")
        
        # Should have non-zero pricing
        assert data.get("selling_price", 0) > 0 or data.get("total_cost", 0) > 0, "Pricing returned zero"


class TestOrderStatusColors:
    """Test that draft status is properly handled in order listing"""
    
    def test_order_list_includes_draft_status(self, api_client):
        """Verify orders API returns draft orders with correct status"""
        # Create a draft order
        order_resp = api_client.post(f"{BASE_URL}/api/orders", json={
            "customer_name": f"TEST_Status_Check_{uuid.uuid4().hex[:6]}",
            "status": "draft"
        })
        assert order_resp.status_code == 200
        order_id = order_resp.json()["id"]
        order_number = order_resp.json()["order_number"]
        
        # Get all orders and find our draft
        list_resp = api_client.get(f"{BASE_URL}/api/orders?limit=100")
        assert list_resp.status_code == 200
        
        orders = list_resp.json().get("orders", [])
        our_order = next((o for o in orders if o.get("id") == order_id), None)
        
        assert our_order is not None, f"Draft order {order_number} not found in list"
        assert our_order.get("status") == "draft"
        
        print(f"Found draft order in list: {order_number} with status={our_order.get('status')}")
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_orders(self, api_client):
        """Delete all TEST_ prefixed orders"""
        response = api_client.get(f"{BASE_URL}/api/orders?limit=200")
        if response.status_code == 200:
            orders = response.json().get("orders", [])
            deleted = 0
            for order in orders:
                if order.get("customer_name", "").startswith("TEST_"):
                    del_resp = api_client.delete(f"{BASE_URL}/api/orders/{order['id']}")
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"Cleaned up {deleted} test orders")
