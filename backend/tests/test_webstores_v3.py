"""
Test Webstores V3 - Comprehensive testing of:
- Product creation with up to 3 images
- Product variants (apparel tiers: economy, standard, premium with sizes)
- Webstore creation (business type)
- Adding products to webstore
- Public storefront access without authentication
- Order creation from public storefront
- Auto-create job when order is placed
- Job appears in jobs list
- Webstore manager shows stats
- Orders tab shows orders with customer info
"""
import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "testuser@test.com"
TEST_PASSWORD = COMMON_TEST_PASSWORD

# Known webstore ID from context
EXISTING_STORE_ID = "1028e604-0468-4cdf-8944-849e75408b28"


class TestPublicStorefrontNoAuth:
    """Test public storefront endpoints - NO authentication required"""
    
    def test_public_store_endpoint(self):
        """Test /api/storefront/{id} returns store info without auth"""
        response = requests.get(f"{BASE_URL}/api/storefront/{EXISTING_STORE_ID}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["id"] == EXISTING_STORE_ID
        assert data["is_public"] == True
        assert data["status"] == "active"
        assert "name" in data
        assert "owner_name" in data
        assert "branding" in data
        print(f"✅ Public store accessible: {data['name']}")
    
    def test_public_store_products_endpoint(self):
        """Test /api/storefront/{id}/products returns products without auth"""
        response = requests.get(f"{BASE_URL}/api/storefront/{EXISTING_STORE_ID}/products")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) > 0, "Store should have products"
        
        # Verify product structure
        product = data[0]
        assert "product_id" in product
        assert "product" in product
        assert "effective_price" in product
        
        # Verify product details
        product_details = product["product"]
        assert "name" in product_details
        assert "retail_price" in product_details
        assert "description" in product_details
        assert "images" in product_details or "image_url" in product_details
        print(f"✅ Public store has {len(data)} products")
    
    def test_public_store_nonexistent(self):
        """Test nonexistent store returns 404"""
        response = requests.get(f"{BASE_URL}/api/storefront/nonexistent-id-12345")
        assert response.status_code == 404


class TestProductMultipleImages:
    """Test product creation with up to 3 images"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_product_with_three_images(self):
        """Test creating a product with up to 3 images"""
        product_data = {
            "name": f"TEST_MultiImage_Product_{uuid.uuid4().hex[:8]}",
            "description": "Test product with multiple images",
            "category": "apparel",
            "base_cost": 10.0,
            "retail_price": 25.0,
            "images": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg",
                "https://example.com/image3.jpg"
            ],
            "has_variants": False,
            "variants": []
        }
        
        response = self.session.post(f"{BASE_URL}/api/products", json=product_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["name"] == product_data["name"]
        assert "images" in data
        assert len(data["images"]) == 3
        assert data["images"][0] == "https://example.com/image1.jpg"
        
        # Legacy image_url should be set to first image
        assert data.get("image_url") == "https://example.com/image1.jpg"
        
        print(f"✅ Created product with 3 images: {data['name']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/products/{data['id']}")
    
    def test_create_product_images_limit_to_three(self):
        """Test that images are limited to 3"""
        product_data = {
            "name": f"TEST_ImageLimit_Product_{uuid.uuid4().hex[:8]}",
            "description": "Test product",
            "category": "signs",
            "base_cost": 15.0,
            "retail_price": 35.0,
            "images": [
                "https://example.com/image1.jpg",
                "https://example.com/image2.jpg",
                "https://example.com/image3.jpg",
                "https://example.com/image4.jpg",  # Should be ignored
                "https://example.com/image5.jpg"   # Should be ignored
            ],
            "has_variants": False,
            "variants": []
        }
        
        response = self.session.post(f"{BASE_URL}/api/products", json=product_data)
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["images"]) <= 3, "Images should be limited to 3"
        print(f"✅ Images correctly limited to 3")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/products/{data['id']}")


class TestProductApparelVariants:
    """Test product variants with apparel tiers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_apparel_defaults_endpoint(self):
        """Test endpoint that returns apparel tier defaults"""
        response = self.session.get(f"{BASE_URL}/api/products/defaults/apparel-options")
        assert response.status_code == 200
        data = response.json()
        
        # Check tiers exist
        assert "tiers" in data
        tiers = data["tiers"]
        assert "economy" in tiers
        assert "standard" in tiers
        assert "premium" in tiers
        
        # Check price modifiers
        assert tiers["economy"]["price_modifier"] == 0
        assert tiers["standard"]["price_modifier"] == 5
        assert tiers["premium"]["price_modifier"] == 12
        
        # Check sizes
        assert "apparel_sizes" in data
        assert "S" in data["apparel_sizes"]
        assert "M" in data["apparel_sizes"]
        assert "L" in data["apparel_sizes"]
        
        print(f"✅ Apparel defaults: {len(data['tiers'])} tiers, {len(data['apparel_sizes'])} sizes")
    
    def test_create_product_with_apparel_variants(self):
        """Test creating an apparel product with tier variants"""
        variants = []
        tiers = ["economy", "standard", "premium"]
        tier_costs = {"economy": 0, "standard": 5, "premium": 12}
        sizes = ["S", "M", "L", "XL"]
        
        for tier in tiers:
            for size in sizes:
                variants.append({
                    "name": f"{tier.title()} - {size}",
                    "size": size,
                    "tier": tier,
                    "additional_cost": tier_costs[tier]
                })
        
        product_data = {
            "name": f"TEST_Apparel_Product_{uuid.uuid4().hex[:8]}",
            "description": "Custom t-shirt with tier variants",
            "category": "apparel",
            "base_cost": 8.0,
            "retail_price": 20.0,
            "images": ["https://example.com/shirt.jpg"],
            "has_variants": True,
            "variants": variants
        }
        
        response = self.session.post(f"{BASE_URL}/api/products", json=product_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["has_variants"] == True
        assert len(data["variants"]) == 12  # 3 tiers * 4 sizes
        
        # Verify tier info is saved
        economy_variant = next(v for v in data["variants"] if v["tier"] == "economy")
        assert economy_variant["additional_cost"] == 0
        
        premium_variant = next(v for v in data["variants"] if v["tier"] == "premium")
        assert premium_variant["additional_cost"] == 12
        
        print(f"✅ Created apparel product with {len(data['variants'])} variants")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/products/{data['id']}")
    
    def test_existing_product_has_apparel_variants(self):
        """Verify existing Custom T-Shirt product has proper variants"""
        products_response = self.session.get(f"{BASE_URL}/api/products")
        assert products_response.status_code == 200
        products = products_response.json()
        
        tshirt = next((p for p in products if "Custom T-Shirt" in p.get("name", "")), None)
        if not tshirt:
            pytest.skip("Custom T-Shirt product not found")
        
        assert tshirt["has_variants"] == True
        assert len(tshirt["variants"]) >= 9  # At least 3 tiers * 3 sizes
        
        # Check tiers exist
        tiers_found = set(v.get("tier") for v in tshirt["variants"] if v.get("tier"))
        assert "economy" in tiers_found
        assert "standard" in tiers_found
        assert "premium" in tiers_found
        
        print(f"✅ Custom T-Shirt has {len(tshirt['variants'])} variants with tiers: {tiers_found}")


class TestWebstoreCreationAndProducts:
    """Test webstore creation and product assignment"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_business_webstore(self):
        """Test creating a business type webstore"""
        store_data = {
            "name": f"TEST_Business_Store_{uuid.uuid4().hex[:8]}",
            "store_type": "business",
            "owner_name": "Test Business Owner",
            "owner_email": "owner@test.com",
            "description": "Test business store",
            "is_public": True,
            "branding": {
                "primary_color": "#0066FF",
                "logo_url": "https://example.com/logo.png"
            }
        }
        
        response = self.session.post(f"{BASE_URL}/api/webstores/v2", json=store_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["name"] == store_data["name"]
        assert data["store_type"] == "business"
        assert data["is_public"] == True
        assert data["status"] == "active"
        assert data["branding"]["primary_color"] == "#0066FF"
        
        print(f"✅ Created business webstore: {data['name']}")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/webstores/v2/{data['id']}")
    
    def test_add_product_to_webstore(self):
        """Test adding a product to a webstore"""
        # Get existing products
        products_response = self.session.get(f"{BASE_URL}/api/products")
        products = products_response.json()
        
        if len(products) == 0:
            pytest.skip("No products available")
        
        product = products[0]
        
        # Add product to existing webstore
        response = self.session.post(
            f"{BASE_URL}/api/webstores/v2/{EXISTING_STORE_ID}/products",
            params={"product_id": product["id"]}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify product is in store
        store_products = self.session.get(f"{BASE_URL}/api/webstores/v2/{EXISTING_STORE_ID}/products")
        assert store_products.status_code == 200
        prods = store_products.json()
        
        product_ids = [p["id"] for p in prods]
        assert product["id"] in product_ids or any(p.get("product_id") == product["id"] for p in prods)
        
        print(f"✅ Product added to webstore")
    
    def test_webstore_shows_sales_stats(self):
        """Test that webstore has sales/profit stats"""
        response = self.session.get(f"{BASE_URL}/api/webstores/v2/{EXISTING_STORE_ID}")
        assert response.status_code == 200
        data = response.json()
        
        # Webstore should have stats fields
        assert "total_sales" in data
        assert "total_orders" in data
        assert "total_profit" in data
        
        # Test Company Store should have some data
        print(f"✅ Webstore stats - Sales: ${data['total_sales']}, Orders: {data['total_orders']}, Profit: ${data['total_profit']}")


class TestOrderCreationAndJobAutoCreate:
    """Test order creation and automatic job creation"""
    
    def test_create_order_creates_job(self):
        """Test that creating an order automatically creates a job"""
        # Get products from storefront (public endpoint)
        products_response = requests.get(f"{BASE_URL}/api/storefront/{EXISTING_STORE_ID}/products")
        assert products_response.status_code == 200
        products = products_response.json()
        
        if len(products) == 0:
            pytest.skip("No products in store")
        
        product = products[0]
        variant = product["product"]["variants"][0] if product["product"].get("variants") else None
        
        order_data = {
            "webstore_id": EXISTING_STORE_ID,
            "customer_name": f"TEST_Customer_{uuid.uuid4().hex[:6]}",
            "customer_email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "customer_phone": "555-123-4567",
            "items": [
                {
                    "product_id": product["product_id"],
                    "variant_id": variant["id"] if variant else None,
                    "quantity": 2
                }
            ],
            "notes": "Test order for auto-job creation"
        }
        
        # Create order (public endpoint)
        response = requests.post(f"{BASE_URL}/api/webstores/v2/orders", json=order_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        order = response.json()
        
        # Verify order was created
        assert order["customer_name"] == order_data["customer_name"]
        assert order["webstore_id"] == EXISTING_STORE_ID
        assert len(order["items"]) == 1
        assert order["items"][0]["quantity"] == 2
        
        # Verify job was auto-created
        assert "job_id" in order, "Order should have auto-created job_id"
        assert order["job_id"] is not None, "job_id should not be None"
        assert order["status"] == "processing", "Status should be 'processing' after job creation"
        
        print(f"✅ Order {order['id'][:8]}... created with auto-created job {order['job_id'][:8]}...")
        
        return order
    
    def test_job_appears_in_jobs_list(self):
        """Test that auto-created job appears in jobs list"""
        # Login to check jobs
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get jobs
        jobs_response = session.get(f"{BASE_URL}/api/jobs")
        assert jobs_response.status_code == 200
        jobs = jobs_response.json()
        
        # Find webstore orders
        webstore_jobs = [j for j in jobs if "Webstore Order" in j.get("name", "")]
        assert len(webstore_jobs) > 0, "Should have at least one webstore order job"
        
        print(f"✅ Found {len(webstore_jobs)} webstore order jobs")
    
    def test_order_has_correct_customer_info(self):
        """Test that orders have correct customer info"""
        # Login to check orders
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get orders
        orders_response = session.get(f"{BASE_URL}/api/webstores/v2/orders")
        assert orders_response.status_code == 200
        orders = orders_response.json()
        
        if len(orders) == 0:
            pytest.skip("No orders to test")
        
        order = orders[0]
        
        # Verify customer info fields
        assert "customer_name" in order
        assert "customer_email" in order
        assert "items" in order
        assert "subtotal" in order
        assert "job_id" in order
        
        print(f"✅ Order has customer info: {order['customer_name']} ({order['customer_email']})")


class TestDecalSizeVariants:
    """Test decal size variants"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_create_decal_with_size_variants(self):
        """Test creating a decal product with size variants"""
        sizes = [
            {"name": "Small (3\")", "size": "Small (3\")", "additional_cost": 0},
            {"name": "Medium (6\")", "size": "Medium (6\")", "additional_cost": 5},
            {"name": "Large (12\")", "size": "Large (12\")", "additional_cost": 15},
            {"name": "XL (18\")", "size": "XL (18\")", "additional_cost": 30},
        ]
        
        product_data = {
            "name": f"TEST_Decal_Product_{uuid.uuid4().hex[:8]}",
            "description": "Custom vinyl decal",
            "category": "decals",
            "base_cost": 3.0,
            "retail_price": 10.0,
            "images": ["https://example.com/decal.jpg"],
            "has_variants": True,
            "variants": sizes
        }
        
        response = self.session.post(f"{BASE_URL}/api/products", json=product_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["category"] == "decals"
        assert data["has_variants"] == True
        assert len(data["variants"]) == 4
        
        # Verify size pricing
        large = next(v for v in data["variants"] if "Large" in v["name"])
        assert large["additional_cost"] == 15
        
        print(f"✅ Created decal product with {len(data['variants'])} size variants")
        
        # Cleanup
        self.session.delete(f"{BASE_URL}/api/products/{data['id']}")


class TestWebstoreIntegration:
    """End-to-end integration tests"""
    
    def test_complete_flow(self):
        """Test complete flow: create product → add to store → order → job created"""
        # Login
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # 1. Create a product
        product_data = {
            "name": f"TEST_Flow_Product_{uuid.uuid4().hex[:8]}",
            "description": "Integration test product",
            "category": "apparel",
            "base_cost": 10.0,
            "retail_price": 25.0,
            "images": ["https://example.com/test1.jpg", "https://example.com/test2.jpg"],
            "has_variants": True,
            "variants": [
                {"name": "Economy - M", "size": "M", "tier": "economy", "additional_cost": 0},
                {"name": "Standard - M", "size": "M", "tier": "standard", "additional_cost": 5},
                {"name": "Premium - M", "size": "M", "tier": "premium", "additional_cost": 12}
            ]
        }
        
        product_response = session.post(f"{BASE_URL}/api/products", json=product_data)
        assert product_response.status_code == 200
        product = product_response.json()
        print(f"1. ✅ Created product: {product['name']}")
        
        # 2. Create a webstore
        store_data = {
            "name": f"TEST_Flow_Store_{uuid.uuid4().hex[:8]}",
            "store_type": "business",
            "owner_name": "Integration Test",
            "is_public": True
        }
        
        store_response = session.post(f"{BASE_URL}/api/webstores/v2", json=store_data)
        assert store_response.status_code == 200
        store = store_response.json()
        print(f"2. ✅ Created webstore: {store['name']}")
        
        # 3. Add product to store
        assign_response = session.post(
            f"{BASE_URL}/api/webstores/v2/{store['id']}/products",
            params={"product_id": product["id"]}
        )
        assert assign_response.status_code == 200
        print(f"3. ✅ Added product to webstore")
        
        # 4. Verify public access
        public_response = requests.get(f"{BASE_URL}/api/storefront/{store['id']}")
        assert public_response.status_code == 200
        print(f"4. ✅ Public storefront accessible")
        
        # 5. Get products from public endpoint
        public_products = requests.get(f"{BASE_URL}/api/storefront/{store['id']}/products")
        assert public_products.status_code == 200
        products_list = public_products.json()
        assert len(products_list) > 0
        print(f"5. ✅ Public products endpoint returns {len(products_list)} products")
        
        # 6. Create order (public)
        variant = product["variants"][1]  # Standard variant
        order_data = {
            "webstore_id": store["id"],
            "customer_name": "Integration Test Customer",
            "customer_email": f"integration_{uuid.uuid4().hex[:6]}@test.com",
            "items": [
                {
                    "product_id": product["id"],
                    "variant_id": variant["id"],
                    "quantity": 1
                }
            ]
        }
        
        order_response = requests.post(f"{BASE_URL}/api/webstores/v2/orders", json=order_data)
        assert order_response.status_code == 200
        order = order_response.json()
        assert order["job_id"] is not None
        print(f"6. ✅ Order created with auto job: {order['job_id'][:8]}...")
        
        # 7. Verify job exists
        job_response = session.get(f"{BASE_URL}/api/jobs/{order['job_id']}")
        assert job_response.status_code == 200
        job = job_response.json()
        assert "Webstore Order" in job["name"]
        print(f"7. ✅ Job exists: {job['name']}")
        
        # Cleanup
        session.delete(f"{BASE_URL}/api/webstores/v2/{store['id']}")
        session.delete(f"{BASE_URL}/api/products/{product['id']}")
        
        print("✅ Complete flow test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
