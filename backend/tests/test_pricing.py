# Note: Phase 1 normalization tests appended at end of file
# Pricing Calculator API Tests
# Tests for pricing calculation, templates, and defaults endpoints

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPricingAPIs:
    """Test Pricing Calculator API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get token"""
        # Login to get auth token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SYNTHETIC_OWNER_EMAIL,
            "password": COMMON_TEST_PASSWORD
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
        
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        print("✅ Logged in successfully, token obtained")
    
    # ============== PRICING DEFAULTS TESTS ==============
    
    def test_get_pricing_defaults(self):
        """Test GET /api/pricing/defaults returns pricing defaults"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.headers
        )
        
        print(f"GET /api/pricing/defaults: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify default fields exist
        assert "hourly_rate" in data, "Missing hourly_rate in defaults"
        assert "default_markup_percent" in data, "Missing default_markup_percent in defaults"
        print(f"✅ Pricing defaults retrieved: hourly_rate={data.get('hourly_rate')}, markup={data.get('default_markup_percent')}%")
    
    def test_update_pricing_defaults(self):
        """Test PUT /api/pricing/defaults updates settings"""
        # First get current defaults
        get_response = requests.get(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.headers
        )
        assert get_response.status_code == 200
        original_data = get_response.json()
        original_hourly_rate = original_data.get("hourly_rate", 75)
        
        # Update hourly rate
        new_hourly_rate = 85.50
        update_response = requests.put(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.headers,
            json={"hourly_rate": new_hourly_rate}
        )
        
        print(f"PUT /api/pricing/defaults: {update_response.status_code}")
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        updated_data = update_response.json()
        assert updated_data.get("hourly_rate") == new_hourly_rate, "Hourly rate not updated"
        print(f"✅ Pricing defaults updated: hourly_rate={new_hourly_rate}")
        
        # Verify persistence with GET
        verify_response = requests.get(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data.get("hourly_rate") == new_hourly_rate, "Update not persisted"
        print("✅ Update persisted correctly")
        
        # Restore original value
        requests.put(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.headers,
            json={"hourly_rate": original_hourly_rate}
        )
    
    # ============== PRICING CALCULATION TESTS ==============
    
    def test_calculate_rigid_signs(self):
        """Test POST /api/pricing/calculate for rigid signs category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "rigid_signs",
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 36,
                    "substrate_type": "coroplast_4mm",
                    "complexity": 5
                },
                "quantity": 1
            }
        )
        
        print(f"POST /api/pricing/calculate (rigid_signs): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify calculation results
        assert "production_cost" in data, "Missing production_cost"
        assert "suggested_price" in data, "Missing suggested_price"
        assert "profit_amount" in data, "Missing profit_amount"
        assert "profit_margin_percent" in data, "Missing profit_margin_percent"
        
        # Verify values are reasonable
        assert data["production_cost"] > 0, "Production cost should be positive"
        assert data["suggested_price"] > data["production_cost"], "Suggested price should be > production cost"
        assert data["profit_amount"] > 0, "Profit should be positive"
        
        print(f"✅ Rigid signs calculation: cost=${data['production_cost']:.2f}, price=${data['suggested_price']:.2f}, profit=${data['profit_amount']:.2f}, margin={data['profit_margin_percent']}%")
    
    def test_calculate_cut_vinyl(self):
        """Test POST /api/pricing/calculate for cut vinyl category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "cut_vinyl",
                "pricing_data": {
                    "width_inches": 12,
                    "length_inches": 24,
                    "vinyl_type": "oracal_651",
                    "num_colors": 2,
                    "complexity": 6
                },
                "quantity": 5
            }
        )
        
        print(f"POST /api/pricing/calculate (cut_vinyl): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "production_cost" in data
        assert "suggested_price" in data
        assert data["suggested_price"] > 0
        print(f"✅ Cut vinyl calculation: price=${data['suggested_price']:.2f}")
    
    def test_calculate_digital_print(self):
        """Test POST /api/pricing/calculate for digital print category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "digital_print",
                "pricing_data": {
                    "width_inches": 48,
                    "length_inches": 96,
                    "print_material": "banner_13oz",
                    "laminate": True,
                    "complexity": 4
                },
                "quantity": 2
            }
        )
        
        print(f"POST /api/pricing/calculate (digital_print): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["suggested_price"] > 0
        print(f"✅ Digital print calculation: price=${data['suggested_price']:.2f}")
    
    def test_calculate_services(self):
        """Test POST /api/pricing/calculate for services category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "services",
                "pricing_data": {
                    "service_type": "installation",
                    "estimated_hours": 3,
                    "num_workers": 2,
                    "distance_miles": 25,
                    "complexity": 7
                },
                "quantity": 1
            }
        )
        
        print(f"POST /api/pricing/calculate (services): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["suggested_price"] > 0
        print(f"✅ Services calculation: price=${data['suggested_price']:.2f}")
    
    def test_calculate_apparel(self):
        """Test POST /api/pricing/calculate for apparel category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "apparel",
                "pricing_data": {
                    "apparel_type": "tshirt",
                    "transfer_type": "htv",
                    "num_colors": 3,
                    "num_print_locations": 2,
                    "complexity": 5
                },
                "quantity": 24
            }
        )
        
        print(f"POST /api/pricing/calculate (apparel): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["suggested_price"] > 0
        print(f"✅ Apparel calculation: price=${data['suggested_price']:.2f} for 24 shirts")
    
    def test_calculate_vehicle_graphics(self):
        """Test POST /api/pricing/calculate for vehicle graphics category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "vehicle_graphics",
                "pricing_data": {
                    "vehicle_type": "van_cargo",
                    "coverage_type": "partial",
                    "install_difficulty": 6,
                    "complexity": 7
                },
                "quantity": 1
            }
        )
        
        print(f"POST /api/pricing/calculate (vehicle_graphics): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["suggested_price"] > 0
        print(f"✅ Vehicle graphics calculation: price=${data['suggested_price']:.2f}")
    
    def test_calculate_promotional(self):
        """Test POST /api/pricing/calculate for promotional items category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "promotional",
                "pricing_data": {
                    "promo_product_type": "yard_signs",
                    "unit_cost": 5.00,
                    "markup_percent": 100,
                    "setup_fee": 25,
                    "complexity": 3
                },
                "quantity": 50
            }
        )
        
        print(f"POST /api/pricing/calculate (promotional): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["suggested_price"] > 0
        print(f"✅ Promotional calculation: price=${data['suggested_price']:.2f} for 50 yard signs")
    
    def test_calculate_custom(self):
        """Test POST /api/pricing/calculate for custom category"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.headers,
            json={
                "category": "custom",
                "pricing_data": {
                    "unit_cost": 100.00,
                    "markup_percent": 75,
                    "complexity": 5
                },
                "quantity": 1
            }
        )
        
        print(f"POST /api/pricing/calculate (custom): {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["suggested_price"] > 0
        print(f"✅ Custom calculation: price=${data['suggested_price']:.2f}")
    
    # ============== PRICING TEMPLATES TESTS ==============
    
    def test_get_templates_empty(self):
        """Test GET /api/pricing/templates returns list (may be empty)"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers
        )
        
        print(f"GET /api/pricing/templates: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of templates"
        print(f"✅ Templates retrieved: {len(data)} templates")
    
    def test_create_template(self):
        """Test POST /api/pricing/templates creates a new template"""
        template_data = {
            "name": "TEST_Standard Yard Sign 18x24",
            "description": "Standard coroplast yard sign",
            "category": "rigid_signs",
            "pricing_data": {
                "width_inches": 18,
                "length_inches": 24,
                "substrate_type": "coroplast_4mm",
                "complexity": 3
            },
            "quantity": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers,
            json=template_data
        )
        
        print(f"POST /api/pricing/templates: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Missing template id"
        assert data["name"] == template_data["name"], "Name mismatch"
        assert data["category"] == template_data["category"], "Category mismatch"
        
        self.created_template_id = data["id"]
        print(f"✅ Template created: {data['name']} (id={data['id']})")
        
        # Verify template appears in list
        list_response = requests.get(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers
        )
        assert list_response.status_code == 200
        templates = list_response.json()
        template_ids = [t["id"] for t in templates]
        assert data["id"] in template_ids, "Created template not in list"
        print("✅ Template persisted and appears in list")
        
        return data["id"]
    
    def test_template_crud_flow(self):
        """Test full CRUD flow for templates: Create -> Read -> Update -> Delete"""
        # CREATE
        create_response = requests.post(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers,
            json={
                "name": "TEST_CRUD Template",
                "description": "Test template for CRUD",
                "category": "cut_vinyl",
                "pricing_data": {
                    "width_inches": 12,
                    "length_inches": 12,
                    "vinyl_type": "oracal_651",
                    "complexity": 5
                },
                "quantity": 10
            }
        )
        assert create_response.status_code == 200
        template = create_response.json()
        template_id = template["id"]
        print(f"✅ Created template: {template_id}")
        
        # READ (via list)
        list_response = requests.get(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers
        )
        assert list_response.status_code == 200
        templates = list_response.json()
        found = any(t["id"] == template_id for t in templates)
        assert found, "Template not found in list"
        print("✅ Template found in list")
        
        # UPDATE (toggle favorite)
        favorite_response = requests.put(
            f"{BASE_URL}/api/pricing/templates/{template_id}/favorite",
            headers=self.headers
        )
        assert favorite_response.status_code == 200
        fav_data = favorite_response.json()
        assert fav_data.get("is_favorite"), "Favorite not toggled"
        print("✅ Template favorited")
        
        # DELETE
        delete_response = requests.delete(
            f"{BASE_URL}/api/pricing/templates/{template_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        print("✅ Template deleted")
        
        # Verify deletion
        verify_response = requests.get(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers
        )
        templates = verify_response.json()
        found = any(t["id"] == template_id for t in templates)
        assert not found, "Template still exists after deletion"
        print("✅ Template deletion verified")
    
    def test_template_filter_by_category(self):
        """Test GET /api/pricing/templates with category filter"""
        # Create a template first
        create_response = requests.post(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers,
            json={
                "name": "TEST_Filter Template",
                "category": "digital_print",
                "pricing_data": {"width_inches": 24, "length_inches": 36},
                "quantity": 1
            }
        )
        assert create_response.status_code == 200
        template_id = create_response.json()["id"]
        
        # Filter by category
        filter_response = requests.get(
            f"{BASE_URL}/api/pricing/templates?category=digital_print",
            headers=self.headers
        )
        assert filter_response.status_code == 200
        templates = filter_response.json()
        
        # All returned templates should be digital_print
        for t in templates:
            assert t["category"] == "digital_print", f"Wrong category: {t['category']}"
        print(f"✅ Category filter works: {len(templates)} digital_print templates")
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/pricing/templates/{template_id}",
            headers=self.headers
        )
    
    # ============== MATERIALS API TEST ==============
    
    def test_get_materials(self):
        """Test GET /api/pricing/materials returns material options"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/materials",
            headers=self.headers
        )
        
        print(f"GET /api/pricing/materials: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify material categories exist
        assert "vinyl" in data, "Missing vinyl materials"
        assert "print_material" in data, "Missing print materials"
        assert "substrate" in data, "Missing substrate materials"
        assert "apparel" in data, "Missing apparel materials"
        
        # Verify vinyl has expected items
        vinyl_ids = [v["id"] for v in data["vinyl"]]
        assert "oracal_651" in vinyl_ids, "Missing oracal_651 vinyl"
        
        print(f"✅ Materials retrieved: {len(data['vinyl'])} vinyl, {len(data['substrate'])} substrates")
    
    def test_get_materials_by_category(self):
        """Test GET /api/pricing/materials with category filter"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/materials?category=substrate",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "substrate" in data, "Missing substrate in filtered response"
        assert len(data) == 1, "Should only return requested category"
        print(f"✅ Materials category filter works: {len(data['substrate'])} substrates")
    
    # ============== ERROR HANDLING TESTS ==============
    
    def test_calculate_requires_auth(self):
        """Test POST /api/pricing/calculate requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers={"Content-Type": "application/json"},  # No auth header
            json={
                "category": "rigid_signs",
                "pricing_data": {"width_inches": 24, "length_inches": 36},
                "quantity": 1
            }
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Calculate endpoint requires auth (401)")
    
    def test_templates_requires_auth(self):
        """Test GET /api/pricing/templates requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/templates",
            headers={"Content-Type": "application/json"}  # No auth header
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Templates endpoint requires auth (401)")
    
    def test_defaults_requires_auth(self):
        """Test GET /api/pricing/defaults requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/defaults",
            headers={"Content-Type": "application/json"}  # No auth header
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Defaults endpoint requires auth (401)")


# Cleanup function to remove test templates
def cleanup_test_templates():
    """Remove all TEST_ prefixed templates"""
    BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
    
    # Login
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": SYNTHETIC_OWNER_EMAIL,
        "password": COMMON_TEST_PASSWORD
    })
    
    if login_response.status_code != 200:
        return
    
    token = login_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all templates
    templates_response = requests.get(f"{BASE_URL}/api/pricing/templates", headers=headers)
    if templates_response.status_code == 200:
        templates = templates_response.json()
        for t in templates:
            if t.get("name", "").startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/pricing/templates/{t['id']}", headers=headers)
                print(f"Cleaned up template: {t['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


# ============== PHASE 1: NORMALIZATION TESTS ==============

class TestPhase1Normalization:
    """Test backward compatibility for dimension and category aliases (Phase 1)"""
    
    @pytest.mark.asyncio
    async def test_dimension_alias_width_to_width_inches(self):
        """Test that 'width' field is normalized to 'width_inches'"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "rigid_signs",
            "pricing_data": {
                "width": 24.0,        # Legacy field
                "height": 36.0,       # Legacy field
                "substrate_type_key": "coroplast_4mm"
            },
            "quantity": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] > 0
        # Verify calculation ran (no 500 error = normalization worked)
    
    @pytest.mark.asyncio
    async def test_dimension_alias_length_to_height(self):
        """Test that 'length_inches' field is normalized to 'height_inches'"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "cut_vinyl",
            "pricing_data": {
                "width_inches": 24.0,
                "length_inches": 36.0,  # Legacy field (should map to height_inches)
                "vinyl_type_key": "oracal_651"
            },
            "quantity": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_dimension_alias_square_footage_to_area_sqft(self):
        """Test that 'square_footage' field is normalized to 'area_sqft'"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "banners",
            "pricing_data": {
                "square_footage": 32.0,  # Legacy field (4x8 banner)
                "banner_material_key": "banner_13oz"
            },
            "quantity": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_category_alias_vehicle_wraps(self):
        """Test that 'vehicle_wraps' category is normalized to 'vehicle_graphics'"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "vehicle_wraps",  # Legacy category name
            "pricing_data": {
                "vehicle_type": "car_sedan",
                "coverage_type": "spot"
            },
            "quantity": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_category_alias_vehicle_wrap_singular(self):
        """Test that 'vehicle_wrap' category is normalized to 'vehicle_graphics'"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "vehicle_wrap",  # Legacy category name (singular)
            "pricing_data": {
                "vehicle_type": "pickup",
                "coverage_type": "partial"
            },
            "quantity": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_category_alias_promo_misc(self):
        """Test that 'promo_misc' category is normalized to 'promotional'"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "promo_misc",  # Legacy category name
            "pricing_data": {
                "promo_product_type": "magnets",
                "unit_cost": 2.50,
                "markup_percent": 100
            },
            "quantity": 100
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["selling_price"] > 0
    
    @pytest.mark.asyncio
    async def test_canonical_fields_still_work(self):
        """Test that canonical field names continue to work (no regression)"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "rigid_signs",  # Canonical category
            "pricing_data": {
                "width_inches": 24.0,   # Canonical field
                "height_inches": 36.0,  # Canonical field (NEW in Phase 1)
                "substrate_type_key": "coroplast_4mm"
            },
            "quantity": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] > 0
        assert data["total_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_mixed_legacy_and_canonical_fields(self):
        """Test that mixing legacy and canonical fields doesn't break"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "thesigntistslab@gmail.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        payload = {
            "category": "digital_print",
            "pricing_data": {
                "width": 48.0,              # Legacy field
                "height_inches": 96.0,      # Canonical field
                "print_media_key": "banner_13oz"
            },
            "quantity": 1
        }
        
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=headers)
        assert response.status_code == 200
        # If width is present, it should be normalized to width_inches
        # height_inches is already canonical, should work as-is


# ============== PHASE 2E: STANDARDIZED RESPONSE SHAPE TESTS ==============
# Verifies every pricing calculator returns the Phase 2 standardized response
# structure and that breakdown arrays sum to their matching top-level fields.

class TestPhase2EResponseShape:
    """Phase 2E — Confirm all 9 pricing calculators return the standardized
    Phase 2 response structure with consistent top-level cost fields, structured
    breakdown arrays whose sums match top-level costs, and an explainable
    overhead_basis under breakdown.metadata.
    """

    TOLERANCE = 0.02  # legacy tests use 0.02, we use 0.01 where strict

    # The full set of top-level cost fields every standardized response must expose.
    REQUIRED_TOP_FIELDS = [
        "material_cost", "labor_cost", "design_cost", "setup_cost",
        "finishing_cost", "hardware_cost", "install_cost", "outsourcing_cost",
        "overhead_cost",
        "base_cost", "true_cost", "production_cost", "total_cost",
        "suggested_price", "selling_price",
        "profit_amount", "profit_margin_percent", "markup_percent",
        "estimated_labor_minutes", "minimum_charge_applied",
        "pricing_method_used", "breakdown",
    ]

    REQUIRED_BREAKDOWN_KEYS = [
        "materials", "labor", "design", "setup", "finishing",
        "hardware", "install", "outsourcing", "overhead", "metadata",
    ]

    # Itemized cost buckets that have a corresponding breakdown array
    BUCKET_TO_FIELD = [
        ("materials", "material_cost"),
        ("labor", "labor_cost"),
        ("design", "design_cost"),
        ("setup", "setup_cost"),
        ("finishing", "finishing_cost"),
        ("hardware", "hardware_cost"),
        ("install", "install_cost"),
        ("outsourcing", "outsourcing_cost"),
    ]

    @pytest.fixture(autouse=True)
    def setup(self):
        """Authenticate against the live BASE_URL once per test."""
        login = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "thesigntistslab@gmail.com", "password": "password123"},
        )
        if login.status_code != 200:
            pytest.skip(f"Login failed: {login.status_code} - {login.text}")
        token = login.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # ---------------- helpers ----------------

    def _calc(self, category: str, pricing_data: dict, quantity: float = 1):
        payload = {"category": category, "pricing_data": pricing_data, "quantity": quantity}
        r = requests.post(f"{BASE_URL}/api/pricing/calculate", json=payload, headers=self.headers)
        assert r.status_code == 200, f"{category} failed: {r.status_code} {r.text}"
        return r.json()

    def _assert_shape(self, data: dict, label: str):
        """Validate top-level + breakdown structure of a standardized response."""
        # Top-level fields
        for field in self.REQUIRED_TOP_FIELDS:
            assert field in data, f"[{label}] missing top-level field: {field}"

        bd = data["breakdown"]
        assert isinstance(bd, dict), f"[{label}] breakdown must be a dict"
        for key in self.REQUIRED_BREAKDOWN_KEYS:
            assert key in bd, f"[{label}] breakdown missing key: {key}"

        # Arrays should be lists (overhead is also a list of 0..1 items)
        for key in [k for k in self.REQUIRED_BREAKDOWN_KEYS if k != "metadata"]:
            assert isinstance(bd[key], list), f"[{label}] breakdown.{key} must be a list"

        # Metadata + overhead_basis presence
        md = bd["metadata"]
        assert isinstance(md, dict), f"[{label}] breakdown.metadata must be a dict"
        assert "overhead_basis" in md, f"[{label}] breakdown.metadata.overhead_basis missing"

    def _assert_math(self, data: dict, label: str):
        """Validate the math invariants for a standardized response."""
        tol = self.TOLERANCE
        bd = data["breakdown"]

        # 1. Every breakdown bucket sums to its top-level field
        for bucket, field in self.BUCKET_TO_FIELD:
            arr_sum = round(sum(item.get("total_cost", 0) for item in bd[bucket]), 2)
            top = float(data[field])
            assert abs(arr_sum - top) <= tol, (
                f"[{label}] sum(breakdown.{bucket})={arr_sum} != {field}={top}"
            )

        # 2. Overhead breakdown sums to overhead_cost
        oh_sum = round(sum(item.get("total_cost", 0) for item in bd["overhead"]), 2)
        assert abs(oh_sum - float(data["overhead_cost"])) <= tol, (
            f"[{label}] sum(breakdown.overhead)={oh_sum} != overhead_cost={data['overhead_cost']}"
        )

        # 3. base_cost = sum of all 8 itemized buckets
        itemized_sum = sum(float(data[f]) for _, f in self.BUCKET_TO_FIELD)
        assert abs(itemized_sum - float(data["base_cost"])) <= tol, (
            f"[{label}] sum(itemized costs)={itemized_sum} != base_cost={data['base_cost']}"
        )

        # 4. true_cost = base_cost + overhead_cost
        expected_true = float(data["base_cost"]) + float(data["overhead_cost"])
        assert abs(expected_true - float(data["true_cost"])) <= tol, (
            f"[{label}] base+overhead={expected_true} != true_cost={data['true_cost']}"
        )

        # 5. production_cost = true_cost
        assert abs(float(data["production_cost"]) - float(data["true_cost"])) <= tol, (
            f"[{label}] production_cost != true_cost"
        )

        # 6. profit_amount = selling_price - true_cost
        expected_profit = float(data["selling_price"]) - float(data["true_cost"])
        assert abs(expected_profit - float(data["profit_amount"])) <= tol, (
            f"[{label}] selling-true={expected_profit} != profit_amount={data['profit_amount']}"
        )

        # 7. overhead_basis math equals overhead_cost
        ob = bd["metadata"]["overhead_basis"]
        # Some calculators may have empty overhead_basis if overhead is 0 — guard.
        if ob:
            basis = float(ob.get("basis_amount", 0) or 0)
            pct = float(ob.get("overhead_percentage", 0) or 0)
            hours = float(ob.get("labor_hours", 0) or 0)
            shop = float(ob.get("shop_overhead_per_hour", 0) or 0)
            expected_oh = round(basis * pct / 100.0 + hours * shop, 2)
            assert abs(expected_oh - float(data["overhead_cost"])) <= tol, (
                f"[{label}] overhead_basis math={expected_oh} != overhead_cost={data['overhead_cost']}"
            )

    def _assert_response(self, data: dict, label: str):
        self._assert_shape(data, label)
        self._assert_math(data, label)

    # ---------------- per-calculator tests ----------------

    def test_rigid_signs_shape_24x36(self):
        """rigid_signs 24in × 36in returns standardized response with consistent math."""
        data = self._calc("rigid_signs", {"width_inches": 24, "height_inches": 36}, quantity=1)
        self._assert_response(data, "rigid_signs:24x36")
        assert data["material_cost"] > 0
        # Materials breakdown should contain at least one line item
        assert len(data["breakdown"]["materials"]) >= 1

    def test_banners_shape_3ft_x_6ft_inches(self):
        """banners 3ft × 6ft specified in inches (36in × 72in). Banners default
        unit is 'feet' per category config, so we must pass unit_of_measure='inches'
        to be interpreted as inches. Expected area = 18 sqft.
        """
        data = self._calc(
            "banners",
            {"width_inches": 36, "height_inches": 72, "unit_of_measure": "inches"},
            quantity=1,
        )
        self._assert_response(data, "banners:36in_x_72in")
        assert data["material_cost"] > 0
        md = data["breakdown"]["metadata"]
        assert abs(md.get("area_sqft", 0) - 18.0) <= 0.5, (
            f"banners area_sqft mismatch: got {md.get('area_sqft')}"
        )

    def test_cut_vinyl_shape_24x36(self):
        """cut_vinyl 24in × 36in returns standardized response."""
        data = self._calc("cut_vinyl", {"width_inches": 24, "height_inches": 36}, quantity=1)
        self._assert_response(data, "cut_vinyl:24x36")
        assert data["material_cost"] > 0

    def test_digital_print_shape_24x36(self):
        """digital_print 24in × 36in returns standardized response."""
        data = self._calc("digital_print", {"width_inches": 24, "height_inches": 36}, quantity=1)
        self._assert_response(data, "digital_print:24x36")
        assert data["material_cost"] > 0
        md = data["breakdown"]["metadata"]
        assert abs(md.get("area_sqft", 0) - 6.0) <= 0.5

    def test_promotional_shape_with_setup_fee(self):
        """promotional with setup_fee=$25 keeps setup excluded from overhead basis."""
        data = self._calc(
            "promotional",
            {"unit_cost": 3.0, "include_setup_fee": True, "setup_fee": 25, "double_sided_art": "different"},
            quantity=100,
        )
        self._assert_response(data, "promotional:setup25")
        assert data["setup_cost"] == 25.0
        ob = data["breakdown"]["metadata"]["overhead_basis"]
        assert ob.get("overhead_excludes_setup_cost") is True
        # Overhead basis must NOT include setup
        basis = float(ob["basis_amount"])
        assert abs(basis - (data["material_cost"] + data["labor_cost"])) <= 0.02

    def test_custom_shape_manual_override(self):
        """custom manual price override: selling_price = override × qty; method tagged."""
        # cost-plus baseline
        baseline = self._calc(
            "custom",
            {"unit_cost": 15, "estimated_hours": 2, "hourly_rate_override": 80, "markup_percent": 150},
            quantity=3,
        )
        self._assert_response(baseline, "custom:cost_plus")
        assert baseline["pricing_method_used"] == "markup"

        # manual override
        override = self._calc(
            "custom",
            {
                "unit_cost": 15, "estimated_hours": 2, "hourly_rate_override": 80,
                "override_enabled": True, "price_override": 99.99,
            },
            quantity=3,
        )
        self._assert_response(override, "custom:override")
        assert override["pricing_method_used"] == "manual_override"
        # selling_price must equal override × qty
        assert abs(override["selling_price"] - (99.99 * 3)) <= 0.02
        # profit_amount still equals selling - true_cost (re-checked inside _assert_math)
        md = override["breakdown"]["metadata"]
        assert md.get("manual_override_used") is True
        assert md.get("override_unit_price") == 99.99

    def test_services_shape_with_travel_equipment_subcontract_permit(self):
        """services with travel + equipment + subcontract + permit add-ons all in outsourcing."""
        data = self._calc(
            "services",
            {
                "services_billing_unit": "hour", "estimated_hours": 4,
                "services_complexity": "medium", "num_workers": 2,
                "services_travel_required": True, "services_travel_miles": 30,
                "services_equipment_required": True, "services_equipment_days": 1,
                "services_equipment_type": "custom",
                "services_subcontracted": True, "services_subcontract_cost": 150,
                "services_permit_external_fee": 75,
            },
            quantity=1,
        )
        self._assert_response(data, "services:travel+eq+sub+permit")
        # All 4 pass-through costs must land in outsourcing
        assert data["outsourcing_cost"] > 0
        outs_names = {item["name"] for item in data["breakdown"]["outsourcing"]}
        # At least travel, equipment, subcontract, permit lines present
        assert any("Travel" in n for n in outs_names), f"missing travel: {outs_names}"
        assert any("Equipment" in n for n in outs_names), f"missing equipment: {outs_names}"
        assert any("Subcontract" in n for n in outs_names), f"missing subcontract: {outs_names}"
        assert any("Permit" in n for n in outs_names), f"missing permit: {outs_names}"
        # material_cost is 0 for services
        assert data["material_cost"] == 0

    def test_services_shape_basic_hourly(self):
        """services basic hourly: only labor populated."""
        data = self._calc(
            "services",
            {"services_billing_unit": "hour", "estimated_hours": 3, "services_complexity": "medium", "num_workers": 1},
            quantity=1,
        )
        self._assert_response(data, "services:basic_hourly")
        assert data["labor_cost"] > 0
        assert data["material_cost"] == 0
        assert data["outsourcing_cost"] == 0

    def test_vehicle_graphics_shape_full_wrap_with_install(self):
        """vehicle_graphics full wrap with install + laminate + 2nd installer."""
        data = self._calc(
            "vehicle_graphics",
            {
                "vehicle_type": "van_cargo", "coverage_type": "full",
                "install_required": True, "wrap_laminate_required": True,
                "second_installer_required": True,
                "install_difficulty_level": "medium", "seam_complexity": "basic",
            },
            quantity=1,
        )
        self._assert_response(data, "vehicle_graphics:full_wrap")
        # Material (wrap vinyl) + finishing (laminate) + install (vehicle install + helper)
        assert data["material_cost"] > 0
        assert data["finishing_cost"] > 0, "laminate should be in finishing"
        assert data["install_cost"] > 0, "install labor + helper should be in install"
        # Install breakdown should have 2 lines (Vehicle Install + Helper)
        assert len(data["breakdown"]["install"]) >= 2

    def test_vehicle_graphics_shape_spot(self):
        """vehicle_graphics spot graphics smoke test."""
        data = self._calc(
            "vehicle_graphics",
            {"vehicle_type": "van_cargo", "coverage_type": "spot", "wrap_laminate_required": False},
            quantity=1,
        )
        self._assert_response(data, "vehicle_graphics:spot")
        assert data["material_cost"] > 0

    def test_apparel_shape_basic(self):
        """apparel basic order: short_sleeve_tee qty 12, single placement HTV, 1 color."""
        data = self._calc(
            "apparel",
            {
                "apparel_product_type": "short_sleeve_tee",
                "apparel_placement_set": "front",
                "apparel_decoration_method": "htv",
                "apparel_num_colors": 1,
            },
            quantity=12,
        )
        self._assert_response(data, "apparel:basic")
        # Blanks in materials
        assert data["material_cost"] > 0
        # Decoration consumable in finishing
        assert data["finishing_cost"] > 0
        # Outsourcing 0 (apparel has no outsource concept)
        assert data["outsourcing_cost"] == 0

    def test_apparel_shape_complex_with_addons(self):
        """apparel complex: plus-size, custom name/number, specialty, bag&fold + setup + design."""
        data = self._calc(
            "apparel",
            {
                "apparel_product_type": "short_sleeve_tee",
                "apparel_placement_set": "front",
                "apparel_decoration_method": "htv",
                "apparel_num_colors": 2,
                "apparel_plus_size_count": 4,
                "apparel_custom_name_number": True,
                "apparel_custom_name_number_count": 24,
                "apparel_specialty_finish": True,
                "apparel_bag_and_fold": True,
                "artwork_needed": True,
                "design_complexity": "medium",
            },
            quantity=24,
        )
        self._assert_response(data, "apparel:complex")
        # All add-on upcharges land in finishing per Phase 2D mapping
        finishing_names = {item["name"] for item in data["breakdown"]["finishing"]}
        assert any("Decoration Consumable" in n for n in finishing_names)
        assert any("Plus-Size" in n for n in finishing_names)
        assert any("Custom Name/Number" in n for n in finishing_names)
        assert any("Specialty Finish" in n for n in finishing_names)
        assert any("Bag & Fold" in n for n in finishing_names)
        # Setup, design, labor populated
        assert data["setup_cost"] > 0
        assert data["design_cost"] > 0
        assert data["labor_cost"] > 0
        # Overhead basis must exclude setup + add-ons (only blanks + decoration + prod_labor + design)
        ob = data["breakdown"]["metadata"]["overhead_basis"]
        legacy_mat = data["breakdown"]["metadata"].get("legacy_material_cost_total", 0)
        legacy_lab = data["breakdown"]["metadata"].get("legacy_labor_cost_total", 0)
        assert abs(float(ob["basis_amount"]) - (legacy_mat + legacy_lab)) <= 0.02

    def test_all_calculators_have_pricing_method_used(self):
        """Every calculator should populate pricing_method_used with a non-empty string."""
        scenarios = [
            ("rigid_signs",      {"width_inches": 24, "height_inches": 36}),
            ("banners",          {"width_inches": 36, "height_inches": 72}),
            ("cut_vinyl",        {"width_inches": 12, "height_inches": 12}),
            ("digital_print",    {"width_inches": 24, "height_inches": 36}),
            ("promotional",      {"unit_cost": 2.5}),
            ("custom",           {"unit_cost": 15, "estimated_hours": 2}),
            ("services",         {"services_billing_unit": "hour", "estimated_hours": 2}),
            ("vehicle_graphics", {"vehicle_type": "van_cargo", "coverage_type": "spot"}),
            ("apparel",          {"apparel_product_type": "short_sleeve_tee",
                                  "apparel_placement_set": "front",
                                  "apparel_decoration_method": "htv"}),
        ]
        for cat, payload in scenarios:
            qty = 12 if cat == "apparel" else 1
            data = self._calc(cat, payload, quantity=qty)
            assert isinstance(data.get("pricing_method_used"), str) and data["pricing_method_used"], (
                f"{cat}: pricing_method_used missing or empty"
            )

    def test_all_calculators_have_overhead_basis(self):
        """Every calculator must expose breakdown.metadata.overhead_basis as a dict."""
        scenarios = [
            ("rigid_signs",      {"width_inches": 24, "height_inches": 36}),
            ("banners",          {"width_inches": 36, "height_inches": 72}),
            ("cut_vinyl",        {"width_inches": 12, "height_inches": 12}),
            ("digital_print",    {"width_inches": 24, "height_inches": 36}),
            ("promotional",      {"unit_cost": 2.5}),
            ("custom",           {"unit_cost": 15, "estimated_hours": 2}),
            ("services",         {"services_billing_unit": "hour", "estimated_hours": 2}),
            ("vehicle_graphics", {"vehicle_type": "van_cargo", "coverage_type": "spot"}),
            ("apparel",          {"apparel_product_type": "short_sleeve_tee",
                                  "apparel_placement_set": "front",
                                  "apparel_decoration_method": "htv"}),
        ]
        for cat, payload in scenarios:
            qty = 12 if cat == "apparel" else 1
            data = self._calc(cat, payload, quantity=qty)
            ob = data["breakdown"]["metadata"].get("overhead_basis")
            assert isinstance(ob, dict) and ob, f"{cat}: overhead_basis missing/empty"
            # Required keys inside overhead_basis
            for required in ("formula", "basis_amount", "basis_components",
                             "labor_hours", "overhead_percentage",
                             "shop_overhead_per_hour", "overhead_excludes_setup_cost"):
                assert required in ob, f"{cat}: overhead_basis missing key '{required}'"

