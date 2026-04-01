"""
Webstore Module Tests - Testing branding customization, storefront, and order functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test store ID from the test data
TEST_STORE_ID = "98c18232-a12c-4272-99fb-ab87e3b38a65"


class TestWebstoreAPI:
    """Test Webstore CRUD operations"""
    
    def test_get_webstores(self):
        """Test getting all webstores"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Found {len(data)} webstores")
    
    def test_get_webstore_by_id(self):
        """Test getting a specific webstore"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TEST_STORE_ID
        assert data["name"] == "Lincoln High School Spring Fundraiser"
        assert data["store_type"] == "fundraiser"
        print(f"✅ Got webstore: {data['name']}")
    
    def test_webstore_branding_fields(self):
        """Test that webstore has branding fields"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # Check branding object exists
        assert "branding" in data
        branding = data["branding"]
        
        # Check branding fields
        assert "logo_url" in branding
        assert "primary_color" in branding
        
        # Verify custom branding values
        assert branding["primary_color"] == "#E91E63"
        assert "placeholder" in branding["logo_url"]
        print(f"✅ Branding: logo_url={branding['logo_url'][:50]}..., primary_color={branding['primary_color']}")
    
    def test_create_webstore_with_branding(self):
        """Test creating a webstore with branding"""
        test_store = {
            "name": f"TEST_Store_{uuid.uuid4().hex[:8]}",
            "store_type": "business",
            "owner_name": "Test Owner",
            "owner_email": "test@example.com",
            "description": "Test store with branding",
            "is_public": True,
            "branding": {
                "logo_url": "https://example.com/test-logo.png",
                "primary_color": "#FF5733"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/webstores/v2", json=test_store)
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == test_store["name"]
        assert data["branding"]["logo_url"] == "https://example.com/test-logo.png"
        assert data["branding"]["primary_color"] == "#FF5733"
        
        # Cleanup
        store_id = data["id"]
        requests.delete(f"{BASE_URL}/api/webstores/v2/{store_id}")
        print("✅ Created and deleted test store with branding")
    
    def test_update_webstore_branding(self):
        """Test updating webstore branding"""
        # Create a test store first
        test_store = {
            "name": f"TEST_Branding_{uuid.uuid4().hex[:8]}",
            "store_type": "business",
            "owner_name": "Test Owner",
            "branding": {"primary_color": "#000000"}
        }
        
        create_response = requests.post(f"{BASE_URL}/api/webstores/v2", json=test_store)
        assert create_response.status_code == 200
        store_id = create_response.json()["id"]
        
        # Update branding
        update_data = {
            "branding": {
                "logo_url": "https://example.com/new-logo.png",
                "primary_color": "#00FF00"
            }
        }
        
        update_response = requests.put(f"{BASE_URL}/api/webstores/v2/{store_id}", json=update_data)
        assert update_response.status_code == 200
        updated_data = update_response.json()
        
        assert updated_data["branding"]["logo_url"] == "https://example.com/new-logo.png"
        assert updated_data["branding"]["primary_color"] == "#00FF00"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/webstores/v2/{store_id}")
        print("✅ Updated webstore branding successfully")


class TestWebstoreProducts:
    """Test webstore product assignments"""
    
    def test_get_webstore_products(self):
        """Test getting products assigned to a webstore"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            product = data[0]
            assert "product_id" in product
            assert "product" in product
            assert "effective_price" in product
            print(f"✅ Found {len(data)} products assigned to store")
        else:
            print("⚠️ No products assigned to test store")
    
    def test_product_has_details(self):
        """Test that product assignment includes product details"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}/products")
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            product = data[0]
            product_details = product["product"]
            
            assert "name" in product_details
            assert "retail_price" in product_details
            assert "variants" in product_details
            
            print(f"✅ Product: {product_details['name']} - ${product_details['retail_price']}")
        else:
            pytest.skip("No products to test")


class TestWebstoreOrders:
    """Test webstore order functionality"""
    
    def test_get_webstore_orders(self):
        """Test getting orders for a webstore"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/orders?webstore_id={TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Found {len(data)} orders for test store")
    
    def test_create_order(self):
        """Test creating an order via API"""
        # Get products first
        products_response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}/products")
        products = products_response.json()
        
        if len(products) == 0:
            pytest.skip("No products available for order test")
        
        product = products[0]
        variant = product["product"]["variants"][0] if product["product"].get("variants") else None
        
        order_data = {
            "webstore_id": TEST_STORE_ID,
            "customer_name": "TEST_API_Customer",
            "customer_email": "api_test@example.com",
            "customer_phone": "555-999-8888",
            "shipping_address": "456 API Test Ave, Test City, TS 99999",
            "items": [
                {
                    "product_id": product["product_id"],
                    "variant_id": variant["id"] if variant else None,
                    "quantity": 2
                }
            ],
            "tax": 0,
            "shipping": 0,
            "notes": "API test order"
        }
        
        response = requests.post(f"{BASE_URL}/api/webstores/v2/orders", json=order_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["customer_name"] == "TEST_API_Customer"
        assert data["customer_email"] == "api_test@example.com"
        assert data["webstore_id"] == TEST_STORE_ID
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2
        
        print(f"✅ Created order: {data['id'][:8]}... Total: ${data['total']}")
    
    def test_order_profit_calculation(self):
        """Test that order profit is calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/orders?webstore_id={TEST_STORE_ID}")
        orders = response.json()
        
        if len(orders) == 0:
            pytest.skip("No orders to test")
        
        order = orders[0]
        
        # Check profit fields exist
        assert "total_profit" in order
        assert "shop_profit" in order
        assert "payout_amount" in order
        
        # For fundraiser, payout should be calculated
        if order["store_type"] == "fundraiser":
            assert order["payout_amount"] >= 0
            print(f"✅ Order profit: total=${order['total_profit']}, shop=${order['shop_profit']}, payout=${order['payout_amount']}")


class TestStorefrontPublicAccess:
    """Test public storefront access"""
    
    def test_public_store_accessible(self):
        """Test that public store is accessible"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["is_public"]
        print(f"✅ Store is public: {data['name']}")
    
    def test_store_products_accessible(self):
        """Test that store products are accessible"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}/products")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Store products accessible: {len(data)} products")


class TestWebstorePayouts:
    """Test webstore payout functionality"""
    
    def test_get_payouts(self):
        """Test getting payouts for a webstore"""
        response = requests.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}/payouts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Found {len(data)} payouts for test store")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
