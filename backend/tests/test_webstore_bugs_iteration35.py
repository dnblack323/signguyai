"""
Test Webstore Bugs - Iteration 35
Tests for:
1. Webstore Stripe Connect gate (should show error when Stripe not connected)
2. Product creation with image upload (base64 images)
3. Product update with images
4. Webstore checkout API endpoint error handling
"""

import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser123@test.com",
            "password": "Test123!"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser123@test.com",
            "password": "Test123!"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


class TestStripeConnectStatus:
    """Test Stripe Connect status and gating"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser123@test.com",
            "password": "Test123!"
        })
        return response.json()["access_token"]
    
    def test_stripe_connect_status_not_connected(self, auth_token):
        """Verify Stripe Connect is not connected for test user"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/stripe-connect/status", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Stripe is NOT connected
        assert data["connected"] == False, "Stripe should NOT be connected for test user"
        assert data["charges_enabled"] == False
        assert data["account_id"] is None


class TestProductCRUDWithImages:
    """Test product creation and updates with base64 images"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser123@test.com",
            "password": "Test123!"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def sample_base64_image(self):
        """Generate a small test base64 image (1x1 red PNG)"""
        # Minimal valid PNG (1x1 red pixel)
        png_bytes = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
            0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk  
            0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x05, 0x6D,
            0xB2, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
            0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        return f"data:image/png;base64,{base64.b64encode(png_bytes).decode('utf-8')}"
    
    def test_create_product_with_base64_image(self, auth_token, sample_base64_image):
        """Test creating a product with base64 encoded image"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        product_data = {
            "name": "TEST_Product_With_Image",
            "description": "Test product with base64 image",
            "category": "signs",
            "base_cost": 10.00,
            "retail_price": 25.00,
            "images": [sample_base64_image],
            "has_variants": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/products", 
            headers=headers, 
            json=product_data
        )
        
        assert response.status_code == 200, f"Create product failed: {response.text}"
        data = response.json()
        
        # Verify product was created with image
        assert data["name"] == "TEST_Product_With_Image"
        assert "images" in data
        assert len(data["images"]) >= 1, "Product should have at least one image"
        assert data["images"][0].startswith("data:image"), "Image should be base64 encoded"
        
        # Store product ID for later tests
        return data["id"]
    
    def test_create_product_with_multiple_images(self, auth_token, sample_base64_image):
        """Test creating a product with multiple base64 images"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        product_data = {
            "name": "TEST_Product_Multiple_Images",
            "description": "Test product with multiple images",
            "category": "apparel",
            "base_cost": 15.00,
            "retail_price": 35.00,
            "images": [sample_base64_image, sample_base64_image, sample_base64_image],
            "has_variants": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/products", 
            headers=headers, 
            json=product_data
        )
        
        assert response.status_code == 200, f"Create product failed: {response.text}"
        data = response.json()
        
        # Verify 3 images were saved
        assert len(data["images"]) == 3, "Product should have 3 images"
        
        return data["id"]
    
    def test_update_product_images(self, auth_token, sample_base64_image):
        """Test updating a product to add/change images"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a product without images
        create_data = {
            "name": "TEST_Product_Update_Images",
            "description": "Test product for image update",
            "category": "signs",
            "base_cost": 20.00,
            "retail_price": 50.00,
            "images": [],
            "has_variants": False
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/products", 
            headers=headers, 
            json=create_data
        )
        assert create_response.status_code == 200
        product_id = create_response.json()["id"]
        
        # Now update to add images
        update_data = {
            "images": [sample_base64_image, sample_base64_image]
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/products/{product_id}",
            headers=headers,
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Update product failed: {update_response.text}"
        updated_data = update_response.json()
        
        # Verify images were added
        assert "images" in updated_data
        assert len(updated_data["images"]) == 2, "Product should have 2 images after update"
        
        # Verify GET returns updated data
        get_response = requests.get(
            f"{BASE_URL}/api/products/{product_id}",
            headers=headers
        )
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert len(get_data["images"]) == 2, "GET should return product with 2 images"
        
        return product_id


class TestWebstoreCreation:
    """Test webstore creation and color picker"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser123@test.com",
            "password": "Test123!"
        })
        return response.json()["access_token"]
    
    def test_create_webstore_with_branding(self, auth_token):
        """Test creating a webstore with branding/color settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        webstore_data = {
            "name": "TEST_Webstore_Branding",
            "description": "Test webstore with custom branding",
            "store_type": "business",  # Correct field name
            "owner_name": "Test Owner",  # Required field
            "owner_email": "testowner@test.com",
            "branding": {
                "primary_color": "#FF5733",
                "logo_url": None
            },
            "is_public": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=headers,
            json=webstore_data
        )
        
        assert response.status_code == 200, f"Create webstore failed: {response.text}"
        data = response.json()
        
        # Verify webstore was created with branding
        assert data["name"] == "TEST_Webstore_Branding"
        assert "branding" in data
        assert data["branding"]["primary_color"] == "#FF5733", "Primary color should be saved"
    
    def test_update_webstore_color(self, auth_token):
        """Test updating webstore branding color"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a webstore
        create_data = {
            "name": "TEST_Webstore_Color_Update",
            "description": "Test webstore for color update",
            "store_type": "business",  # Correct field name
            "owner_name": "Test Owner 2",  # Required field
            "branding": {
                "primary_color": "#0D9488"
            }
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=headers,
            json=create_data
        )
        assert create_response.status_code == 200, f"Create webstore failed: {create_response.text}"
        webstore_id = create_response.json()["id"]
        
        # Update color
        update_data = {
            "branding": {
                "primary_color": "#E91E63"
            }
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/webstores/v2/{webstore_id}",
            headers=headers,
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Update webstore failed: {update_response.text}"
        updated_data = update_response.json()
        assert updated_data["branding"]["primary_color"] == "#E91E63", "Color should be updated"


class TestWebstoreCheckoutStripeGate:
    """Test webstore checkout API returns proper error when Stripe not connected"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser123@test.com",
            "password": "Test123!"
        })
        return response.json()["access_token"]
    
    def test_checkout_returns_error_when_stripe_not_connected(self, auth_token):
        """Test that checkout returns proper error when Stripe is not connected"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a webstore
        webstore_data = {
            "name": "TEST_Webstore_Checkout",
            "description": "Test webstore for checkout",
            "store_type": "business",  # Correct field name
            "owner_name": "Checkout Test Owner",  # Required field
            "is_public": True
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=headers,
            json=webstore_data
        )
        
        # Handle both success and possible error
        if create_response.status_code == 200:
            webstore_id = create_response.json()["id"]
        else:
            # Use a placeholder ID - the checkout endpoint should still return proper error
            pytest.skip("Could not create webstore for checkout test")
            return
        
        # Create a test product
        product_data = {
            "name": "TEST_Checkout_Product",
            "description": "Product for checkout test",
            "category": "signs",
            "base_cost": 10.00,
            "retail_price": 25.00,
            "has_variants": False
        }
        
        product_response = requests.post(
            f"{BASE_URL}/api/products",
            headers=headers,
            json=product_data
        )
        
        if product_response.status_code != 200:
            pytest.skip("Could not create product for checkout test")
            return
            
        product_id = product_response.json()["id"]
        
        # Now try checkout - should fail because Stripe is not connected
        checkout_data = {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 1,
                    "variant_id": None,
                    "variant_name": None
                }
            ],
            "customer_info": {
                "name": "Test Customer",
                "email": "testcustomer@test.com",
                "phone": "555-1234",
                "shipping_address": "123 Test St"
            }
        }
        
        checkout_response = requests.post(
            f"{BASE_URL}/api/stripe-connect/webstore/{webstore_id}/checkout?origin_url=https://example.com",
            json=checkout_data
        )
        
        # Should return error because Stripe is not connected
        assert checkout_response.status_code == 400, f"Expected 400 error, got {checkout_response.status_code}"
        error_data = checkout_response.json()
        
        # Check for expected error message
        assert "detail" in error_data
        assert error_data["detail"] in [
            "Store cannot accept payments at this time",
            "Store payment setup incomplete",
            "Payment system unavailable"
        ], f"Unexpected error message: {error_data['detail']}"


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testuser123@test.com",
            "password": "Test123!"
        })
        return response.json()["access_token"]
    
    def test_cleanup_test_products(self, auth_token):
        """Delete all TEST_ prefixed products"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get all products
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        if response.status_code != 200:
            return
        
        products = response.json()
        deleted_count = 0
        
        for product in products:
            if product.get("name", "").startswith("TEST_"):
                del_response = requests.delete(
                    f"{BASE_URL}/api/products/{product['id']}",
                    headers=headers
                )
                if del_response.status_code in [200, 204]:
                    deleted_count += 1
        
        print(f"Cleaned up {deleted_count} test products")
    
    def test_cleanup_test_webstores(self, auth_token):
        """Delete all TEST_ prefixed webstores"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get all webstores
        response = requests.get(f"{BASE_URL}/api/webstores/v2", headers=headers)
        if response.status_code != 200:
            return
        
        webstores = response.json()
        deleted_count = 0
        
        for store in webstores:
            if store.get("name", "").startswith("TEST_"):
                del_response = requests.delete(
                    f"{BASE_URL}/api/webstores/v2/{store['id']}",
                    headers=headers
                )
                if del_response.status_code in [200, 204]:
                    deleted_count += 1
        
        print(f"Cleaned up {deleted_count} test webstores")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
