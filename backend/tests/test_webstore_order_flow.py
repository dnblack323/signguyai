"""
Webstore Order Flow Tests
Tests the complete webstore flow:
1. User login and authentication
2. Create a new webstore (Business type)
3. Create a product
4. Assign product to webstore
5. Public storefront loads correctly
6. Customer places an order (auto-creates job)
7. Order appears in orders list
8. Job was auto-created with matching items
"""

import pytest
import requests
import os
import time
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "thesigntistslab@gmail.com"
TEST_PASSWORD = "password123"


class TestWebstoreOrderFlow:
    """Complete webstore order flow tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_webstore(self, auth_headers):
        """Create a test webstore for the flow"""
        timestamp = int(time.time())
        webstore_data = {
            "name": f"TEST_Store_{timestamp}",
            "store_type": "business",
            "owner_name": f"TEST_Owner_{timestamp}",
            "owner_email": "test@example.com",
            "owner_phone": "555-1234",
            "description": "Test business store for automated testing",
            "is_public": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers,
            json=webstore_data
        )
        assert response.status_code == 200, f"Failed to create webstore: {response.text}"
        webstore = response.json()
        assert "id" in webstore, "Webstore missing id"
        assert webstore["name"] == webstore_data["name"]
        assert webstore["store_type"] == "business"
        assert webstore["status"] == "active"
        
        yield webstore
        
        # Cleanup: Delete the webstore after tests
        try:
            requests.delete(f"{BASE_URL}/api/webstores/v2/{webstore['id']}", headers=auth_headers)
        except:
            pass
    
    @pytest.fixture(scope="class")
    def test_product(self, auth_headers):
        """Create a test product for the flow"""
        timestamp = int(time.time())
        product_data = {
            "name": f"TEST_Product_{timestamp}",
            "description": "Test product for automated testing",
            "category": "signs",
            "base_cost": 15.00,
            "retail_price": 25.00
        }
        
        response = requests.post(
            f"{BASE_URL}/api/products",
            headers=auth_headers,
            json=product_data
        )
        assert response.status_code == 200, f"Failed to create product: {response.text}"
        product = response.json()
        assert "id" in product, "Product missing id"
        assert product["name"] == product_data["name"]
        assert product["retail_price"] == 25.00
        
        yield product
        
        # Cleanup: Delete the product after tests
        try:
            requests.delete(f"{BASE_URL}/api/products/{product['id']}", headers=auth_headers)
        except:
            pass
    
    # ============== Test 1: User Login ==============
    def test_user_login(self, auth_token):
        """Test 1: User login and authentication works"""
        assert auth_token is not None, "Auth token should not be None"
        assert len(auth_token) > 0, "Auth token should not be empty"
        print(f"✓ Login successful, received auth token")
    
    # ============== Test 2: Create Webstore ==============
    def test_create_webstore(self, test_webstore):
        """Test 2: Create a new webstore (Business type)"""
        assert test_webstore["store_type"] == "business"
        assert test_webstore["status"] == "active"
        assert test_webstore["is_public"] == True
        assert "owner_name" in test_webstore
        print(f"✓ Created webstore: {test_webstore['name']} (ID: {test_webstore['id']})")
    
    # ============== Test 3: Create Product ==============
    def test_create_product(self, test_product):
        """Test 3: Create a product in the catalog"""
        assert test_product["category"] == "signs"
        assert test_product["base_cost"] == 15.00
        assert test_product["retail_price"] == 25.00
        assert test_product["is_active"] == True
        print(f"✓ Created product: {test_product['name']} (ID: {test_product['id']})")
    
    # ============== Test 4: Assign Product to Webstore ==============
    def test_assign_product_to_webstore(self, auth_headers, test_webstore, test_product):
        """Test 4: Assign product to webstore"""
        assign_data = {
            "product_id": test_product["id"],
            "is_enabled": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{test_webstore['id']}/products",
            headers=auth_headers,
            json=assign_data
        )
        assert response.status_code == 200, f"Failed to assign product: {response.text}"
        result = response.json()
        assert "message" in result
        print(f"✓ Assigned product {test_product['id']} to webstore {test_webstore['id']}")
    
    # ============== Test 5: Verify Public Storefront ==============
    def test_public_storefront_loads(self, test_webstore, test_product):
        """Test 5: Public storefront loads correctly with products"""
        # Get store info (public endpoint - no auth)
        store_response = requests.get(f"{BASE_URL}/api/storefront/{test_webstore['id']}")
        assert store_response.status_code == 200, f"Storefront not accessible: {store_response.text}"
        
        store_data = store_response.json()
        assert store_data["id"] == test_webstore["id"]
        assert store_data["name"] == test_webstore["name"]
        assert store_data["status"] == "active"
        print(f"✓ Storefront loads: {store_data['name']}")
        
        # Get products (public endpoint - no auth)
        products_response = requests.get(f"{BASE_URL}/api/storefront/{test_webstore['id']}/products")
        assert products_response.status_code == 200, f"Products not accessible: {products_response.text}"
        
        products = products_response.json()
        assert len(products) >= 1, "No products in storefront"
        
        # Verify our test product is in the list
        product_ids = [p["product_id"] for p in products]
        assert test_product["id"] in product_ids, "Test product not found in storefront"
        print(f"✓ Storefront shows {len(products)} products, including test product")
    
    # ============== Test 6: Place Order (Public) ==============
    def test_place_order(self, test_webstore, test_product):
        """Test 6: Customer places an order from storefront (auto-creates job)"""
        timestamp = int(time.time())
        order_data = {
            "webstore_id": test_webstore["id"],
            "customer_name": f"TEST_Customer_{timestamp}",
            "customer_email": f"test_customer_{timestamp}@example.com",
            "customer_phone": "555-9999",
            "items": [
                {
                    "product_id": test_product["id"],
                    "quantity": 2
                }
            ],
            "notes": "Test order for automated testing"
        }
        
        # Public order endpoint - no auth required
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Failed to place order: {response.text}"
        
        order = response.json()
        assert "id" in order, "Order missing id"
        assert order["webstore_id"] == test_webstore["id"]
        assert order["customer_name"] == order_data["customer_name"]
        assert order["customer_email"] == order_data["customer_email"]
        assert len(order["items"]) == 1
        assert order["items"][0]["product_id"] == test_product["id"]
        assert order["items"][0]["quantity"] == 2
        
        # Verify pricing
        expected_total = test_product["retail_price"] * 2  # 25.00 * 2 = 50.00
        assert order["subtotal"] == expected_total, f"Expected subtotal {expected_total}, got {order['subtotal']}"
        
        # Verify job was auto-created
        assert "job_id" in order and order["job_id"], "Order should have auto-created job_id"
        
        # Store for subsequent tests
        self.__class__.created_order = order
        print(f"✓ Order placed: {order['id'][:8]}... (Total: ${order['subtotal']:.2f})")
        print(f"✓ Auto-created job: {order['job_id'][:8]}...")
    
    # ============== Test 7: Verify Order in Orders List ==============
    def test_order_in_orders_list(self, auth_headers):
        """Test 7: Verify order appears in webstore orders list"""
        # Get orders for tenant
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/orders",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get orders: {response.text}"
        
        orders = response.json()
        assert len(orders) >= 1, "No orders found"
        
        # Find our created order
        created_order = getattr(self.__class__, 'created_order', None)
        assert created_order is not None, "No order created in previous test"
        
        order_ids = [o["id"] for o in orders]
        assert created_order["id"] in order_ids, "Created order not found in orders list"
        
        # Verify order details
        matching_order = next((o for o in orders if o["id"] == created_order["id"]), None)
        assert matching_order is not None
        assert matching_order["customer_name"] == created_order["customer_name"]
        assert matching_order["job_id"] == created_order["job_id"]
        
        print(f"✓ Order {created_order['id'][:8]}... found in orders list")
    
    # ============== Test 8: Verify Job Was Auto-Created ==============
    def test_job_auto_created(self, auth_headers):
        """Test 8: Verify job was auto-created from order with matching items"""
        created_order = getattr(self.__class__, 'created_order', None)
        assert created_order is not None, "No order created in previous test"
        assert created_order.get("job_id"), "Order should have job_id"
        
        # Get jobs list
        response = requests.get(
            f"{BASE_URL}/api/jobs",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get jobs: {response.text}"
        
        jobs = response.json()
        job_ids = [j["id"] for j in jobs]
        assert created_order["job_id"] in job_ids, f"Job {created_order['job_id']} not found in jobs list"
        
        # Verify job details
        matching_job = next((j for j in jobs if j["id"] == created_order["job_id"]), None)
        assert matching_job is not None, "Matching job not found"
        assert matching_job["status"] == "approved", f"Job status should be 'approved', got '{matching_job['status']}'"
        
        print(f"✓ Job {created_order['job_id'][:8]}... found and verified")
        print(f"  - Status: {matching_job['status']}")
    
    # ============== Test 9: Verify Job Items Match Order ==============
    def test_job_items_match_order(self, auth_headers):
        """Test 9: Verify job items match order items"""
        created_order = getattr(self.__class__, 'created_order', None)
        assert created_order is not None, "No order created in previous test"
        
        job_id = created_order["job_id"]
        
        # Get job items
        response = requests.get(
            f"{BASE_URL}/api/jobs/{job_id}/items",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get job items: {response.text}"
        
        job_items = response.json()
        assert len(job_items) >= 1, "Job should have at least one item"
        
        # Verify item count matches order items count
        order_items_count = len(created_order["items"])
        assert len(job_items) >= order_items_count, f"Expected at least {order_items_count} job items, got {len(job_items)}"
        
        # Verify item details
        order_item = created_order["items"][0]
        job_item = job_items[0]
        
        assert job_item["quantity"] == order_item["quantity"], "Quantity mismatch"
        assert job_item["unit_price"] == order_item["unit_price"], "Unit price mismatch"
        
        print(f"✓ Job items verified: {len(job_items)} items matching order")
        print(f"  - Item: {job_item.get('description', 'N/A')}")
        print(f"  - Quantity: {job_item['quantity']}")
        print(f"  - Unit Price: ${job_item['unit_price']:.2f}")


class TestWebstoreListAndNavigation:
    """Tests for webstore listing and navigation"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    def test_list_webstores(self, auth_headers):
        """Test listing all webstores"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list webstores: {response.text}"
        
        webstores = response.json()
        assert isinstance(webstores, list), "Response should be a list"
        print(f"✓ Listed {len(webstores)} webstores")
    
    def test_list_products(self, auth_headers):
        """Test listing all products"""
        response = requests.get(
            f"{BASE_URL}/api/products",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list products: {response.text}"
        
        products = response.json()
        assert isinstance(products, list), "Response should be a list"
        print(f"✓ Listed {len(products)} products")
    
    def test_list_orders(self, auth_headers):
        """Test listing all webstore orders"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/orders",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list orders: {response.text}"
        
        orders = response.json()
        assert isinstance(orders, list), "Response should be a list"
        print(f"✓ Listed {len(orders)} orders")
    
    def test_list_jobs(self, auth_headers):
        """Test listing all jobs"""
        response = requests.get(
            f"{BASE_URL}/api/jobs",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list jobs: {response.text}"
        
        jobs = response.json()
        assert isinstance(jobs, list), "Response should be a list"
        print(f"✓ Listed {len(jobs)} jobs")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
