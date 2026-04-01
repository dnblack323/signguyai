"""
Test Webstore Add Product API Fix - Iteration 31

Tests the fix for adding products to webstores:
1. Backend endpoint POST /api/webstores/v2/{id}/products now accepts JSON body
2. Frontend assignProductToWebstore sends proper JSON body instead of query params

Test flow:
1. Create a webstore
2. Create a product
3. Add product to webstore using JSON body
4. Verify product is assigned to webstore
"""
import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestWebstoreAddProduct:
    """Test webstore add product flow with JSON body"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": COMMON_TEST_EMAIL,
            "password": LEGACY_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authenticated headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    @pytest.fixture(scope="class")
    def test_webstore(self, auth_headers):
        """Create a test webstore"""
        webstore_data = {
            "name": "TEST_Webstore_Iteration31",
            "store_type": "business",
            "owner_name": "Test Owner",
            "owner_email": "testowner@test.com",
            "description": "Test webstore for iteration 31"
        }
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            json=webstore_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create webstore failed: {response.text}"
        webstore = response.json()
        yield webstore
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/webstores/v2/{webstore['id']}", headers=auth_headers)
    
    @pytest.fixture(scope="class")
    def test_product(self, auth_headers):
        """Create a test product"""
        product_data = {
            "name": "TEST_Product_Iteration31",
            "description": "Test product for iteration 31",
            "category": "signs",
            "base_cost": 25.00,
            "retail_price": 50.00
        }
        response = requests.post(
            f"{BASE_URL}/api/products",
            json=product_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Create product failed: {response.text}"
        product = response.json()
        yield product
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/products/{product['id']}", headers=auth_headers)
    
    def test_health_check(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("PASS: API is healthy")
    
    def test_add_product_to_webstore_with_json_body(self, auth_headers, test_webstore, test_product):
        """
        Test adding product to webstore using JSON body (the FIX)
        This is the core fix - the endpoint now accepts JSON body with product_id
        """
        webstore_id = test_webstore["id"]
        product_id = test_product["id"]
        
        # This is the FIX - sending JSON body with product_id instead of query params
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}/products",
            json={
                "product_id": product_id,
                "is_enabled": True,
                "price_override": 45.00
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Add product to webstore failed: {response.text}"
        result = response.json()
        assert "message" in result
        assert "added" in result["message"].lower() or "updated" in result["message"].lower()
        print(f"PASS: Product added to webstore successfully - {result}")
    
    def test_verify_product_in_webstore(self, auth_headers, test_webstore, test_product):
        """Verify the product is now in the webstore"""
        webstore_id = test_webstore["id"]
        product_id = test_product["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}/products",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get webstore products failed: {response.text}"
        products = response.json()
        
        # Check the product is in the webstore
        product_ids = [p["id"] for p in products]
        assert product_id in product_ids, f"Product {product_id} not found in webstore products"
        
        # Check price_override is set
        product_in_store = next((p for p in products if p["id"] == product_id), None)
        assert product_in_store is not None
        assert product_in_store.get("price_override") == 45.00 or product_in_store.get("effective_price") == 45.00
        print("PASS: Product verified in webstore with correct price")
    
    def test_update_existing_product_assignment(self, auth_headers, test_webstore, test_product):
        """Test updating an existing product assignment (re-adding updates price)"""
        webstore_id = test_webstore["id"]
        product_id = test_product["id"]
        
        # Update price_override to a different value
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}/products",
            json={
                "product_id": product_id,
                "is_enabled": True,
                "price_override": 55.00  # New price
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Update product assignment failed: {response.text}"
        result = response.json()
        assert "updated" in result["message"].lower()
        print(f"PASS: Product assignment updated - {result}")
    
    def test_verify_updated_price(self, auth_headers, test_webstore, test_product):
        """Verify the price was updated"""
        webstore_id = test_webstore["id"]
        product_id = test_product["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}/products",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        products = response.json()
        
        product_in_store = next((p for p in products if p["id"] == product_id), None)
        assert product_in_store is not None
        assert product_in_store.get("price_override") == 55.00 or product_in_store.get("effective_price") == 55.00
        print(f"PASS: Updated price verified - effective_price: {product_in_store.get('effective_price')}")
    
    def test_remove_product_from_webstore(self, auth_headers, test_webstore, test_product):
        """Test removing product from webstore"""
        webstore_id = test_webstore["id"]
        product_id = test_product["id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}/products/{product_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Remove product failed: {response.text}"
        print("PASS: Product removed from webstore")
    
    def test_verify_product_removed(self, auth_headers, test_webstore, test_product):
        """Verify product is no longer in webstore"""
        webstore_id = test_webstore["id"]
        product_id = test_product["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}/products",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        products = response.json()
        
        product_ids = [p["id"] for p in products]
        assert product_id not in product_ids, "Product should not be in webstore after removal"
        print("PASS: Product verified as removed from webstore")


class TestWebstoreAddProductErrorCases:
    """Test error handling for add product endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": COMMON_TEST_EMAIL,
            "password": LEGACY_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get authenticated headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_add_nonexistent_product(self, auth_headers):
        """Test adding a product that doesn't exist"""
        # First create a webstore
        webstore_response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            json={
                "name": "TEST_Webstore_ErrorCase",
                "store_type": "business",
                "owner_name": "Test Owner"
            },
            headers=auth_headers
        )
        webstore = webstore_response.json()
        
        try:
            # Try to add non-existent product
            response = requests.post(
                f"{BASE_URL}/api/webstores/v2/{webstore['id']}/products",
                json={"product_id": "nonexistent_product_id"},
                headers=auth_headers
            )
            
            assert response.status_code == 404, f"Expected 404 for non-existent product, got {response.status_code}"
            print("PASS: Correctly returns 404 for non-existent product")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/webstores/v2/{webstore['id']}", headers=auth_headers)
    
    def test_add_product_to_nonexistent_webstore(self, auth_headers):
        """Test adding product to a non-existent webstore"""
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/nonexistent_webstore_id/products",
            json={"product_id": "some_product_id"},
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent webstore, got {response.status_code}"
        print("PASS: Correctly returns 404 for non-existent webstore")
    
    def test_add_product_without_auth(self):
        """Test adding product without authentication"""
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/some_webstore_id/products",
            json={"product_id": "some_product_id"}
        )
        
        assert response.status_code == 401, f"Expected 401 for unauthenticated request, got {response.status_code}"
        print("PASS: Correctly returns 401 for unauthenticated request")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
