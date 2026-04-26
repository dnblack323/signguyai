"""
Iteration 98 - Webstore Checkout Gating Tests

Tests for the checkout gating feature that:
- Allows browsing and add-to-cart when checkout is inactive
- Disables final checkout button when Stripe Connect is not connected/onboarded
- Shows clear inactive-checkout message
- Exposes checkout gating state cleanly via public storefront API
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"

# Seeded test data from main agent
TEST_STORE_ID = "fc0bad7e-9040-477e-93b9-a3f0b1a2df90"
TEST_PRODUCT_ID = "b3c51047-4bc9-4d6e-b3cb-9023bb6a2ee6"


class TestStripeConnectStatus:
    """Test Stripe Connect status for tenant"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    def test_stripe_connect_status_returns_connected_false(self, auth_token):
        """Verify Stripe Connect status shows connected=false for test tenant"""
        response = requests.get(
            f"{BASE_URL}/api/stripe-connect/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "connected" in data
        assert "charges_enabled" in data
        assert "stripe_mode" in data
        
        # For this test tenant, connected should be false
        assert data["connected"] == False, f"Expected connected=false, got {data['connected']}"
        assert data["charges_enabled"] == False
        print(f"✅ Stripe Connect status: connected={data['connected']}, stripe_mode={data['stripe_mode']}")


class TestPublicStorefrontCheckoutGating:
    """Test public storefront API exposes checkout gating state"""
    
    def test_storefront_returns_checkout_gating_fields(self):
        """Verify public storefront API returns checkout_enabled, checkout_status, checkout_message"""
        response = requests.get(f"{BASE_URL}/api/storefront/{TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify checkout gating fields are present
        assert "checkout_enabled" in data, "Missing checkout_enabled field"
        assert "checkout_status" in data, "Missing checkout_status field"
        assert "checkout_message" in data, "Missing checkout_message field"
        
        print(f"✅ Checkout gating fields present: checkout_enabled={data['checkout_enabled']}, checkout_status={data['checkout_status']}")
    
    def test_storefront_checkout_disabled_when_stripe_not_connected(self):
        """Verify checkout is disabled when tenant has no Stripe Connect"""
        response = requests.get(f"{BASE_URL}/api/storefront/{TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # Checkout should be disabled
        assert data["checkout_enabled"] == False, f"Expected checkout_enabled=false, got {data['checkout_enabled']}"
        assert data["checkout_status"] in ["inactive", "setup_incomplete", "unavailable"], \
            f"Unexpected checkout_status: {data['checkout_status']}"
        assert data["checkout_message"], "checkout_message should not be empty"
        
        print(f"✅ Checkout correctly disabled: status={data['checkout_status']}, message={data['checkout_message']}")
    
    def test_storefront_returns_store_details(self):
        """Verify storefront returns expected store details"""
        response = requests.get(f"{BASE_URL}/api/storefront/{TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify basic store fields
        assert data["id"] == TEST_STORE_ID
        assert "name" in data
        assert "store_type" in data
        assert "status" in data
        assert data["status"] == "active"
        
        print(f"✅ Store details: name={data['name']}, type={data['store_type']}")
    
    def test_storefront_does_not_expose_sensitive_fields(self):
        """Verify storefront does not expose tenant_id, payout info, etc."""
        response = requests.get(f"{BASE_URL}/api/storefront/{TEST_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # These fields should NOT be exposed publicly
        sensitive_fields = ["tenant_id", "payout_owed", "payout_paid", "total_profit"]
        for field in sensitive_fields:
            assert field not in data, f"Sensitive field '{field}' should not be exposed"
        
        print("✅ Sensitive fields correctly hidden from public API")


class TestStorefrontProducts:
    """Test storefront products endpoint"""
    
    def test_storefront_products_returns_list(self):
        """Verify storefront products endpoint returns product list"""
        response = requests.get(f"{BASE_URL}/api/storefront/{TEST_STORE_ID}/products")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list), "Expected list of products"
        assert len(data) > 0, "Expected at least one product"
        
        print(f"✅ Storefront products: {len(data)} products found")
    
    def test_storefront_products_contain_expected_fields(self):
        """Verify product data contains expected fields for storefront display"""
        response = requests.get(f"{BASE_URL}/api/storefront/{TEST_STORE_ID}/products")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) > 0, "Expected at least one product"
        product = data[0]
        
        # Verify expected fields
        assert "product_id" in product
        assert "product" in product
        assert "effective_price" in product
        
        # Verify nested product fields
        product_details = product["product"]
        assert "id" in product_details
        assert "name" in product_details
        assert "retail_price" in product_details
        
        print(f"✅ Product fields verified: {product_details['name']} at ${product['effective_price']}")
    
    def test_storefront_products_do_not_expose_base_cost(self):
        """Verify product data does not expose base_cost (profit margin info)"""
        response = requests.get(f"{BASE_URL}/api/storefront/{TEST_STORE_ID}/products")
        assert response.status_code == 200
        data = response.json()
        
        for product in data:
            product_details = product.get("product", {})
            assert "base_cost" not in product_details, "base_cost should not be exposed publicly"
        
        print("✅ base_cost correctly hidden from public product data")


class TestCheckoutGatingBehavior:
    """Test checkout gating behavior - cart works but checkout blocked"""
    
    def test_webstore_checkout_fails_when_stripe_not_connected(self):
        """Verify checkout endpoint returns error when Stripe not connected"""
        checkout_payload = {
            "items": [{
                "product_id": TEST_PRODUCT_ID,
                "variant_id": None,
                "variant_name": None,
                "quantity": 1,
                "price": 20.0
            }],
            "customer_info": {
                "name": "Test Customer",
                "email": "test@example.com",
                "phone": "555-1234",
                "shipping_address": "123 Test St",
                "notes": "Test order"
            }
        }
        
        origin_url = "https://meta-webhook-setup.preview.emergentagent.com"
        response = requests.post(
            f"{BASE_URL}/api/stripe-connect/webstore/{TEST_STORE_ID}/checkout?origin_url={origin_url}",
            json=checkout_payload
        )
        
        # Should fail because Stripe is not connected
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        assert "cannot accept payments" in data["detail"].lower() or "payment" in data["detail"].lower()
        
        print(f"✅ Checkout correctly blocked: {data['detail']}")
    
    def test_storefront_404_for_nonexistent_store(self):
        """Verify 404 for non-existent store"""
        response = requests.get(f"{BASE_URL}/api/storefront/nonexistent-store-id")
        assert response.status_code == 404
        print("✅ 404 returned for non-existent store")


class TestStorefrontEdgeCases:
    """Test edge cases for storefront"""
    
    def test_storefront_products_empty_for_nonexistent_store(self):
        """Verify products endpoint returns 404 for non-existent store"""
        response = requests.get(f"{BASE_URL}/api/storefront/nonexistent-store-id/products")
        assert response.status_code == 404
        print("✅ Products endpoint returns 404 for non-existent store")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
