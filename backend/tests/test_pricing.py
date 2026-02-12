# Pricing Calculator API Tests
# Tests for pricing calculation, templates, and defaults endpoints

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPricingAPIs:
    """Test Pricing Calculator API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get token"""
        # Login to get auth token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testowner@signguy.com",
            "password": "Test123!"
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
        
        self.token = login_response.json().get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        print(f"✅ Logged in successfully, token obtained")
    
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
        assert updated_data.get("hourly_rate") == new_hourly_rate, f"Hourly rate not updated"
        print(f"✅ Pricing defaults updated: hourly_rate={new_hourly_rate}")
        
        # Verify persistence with GET
        verify_response = requests.get(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.headers
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data.get("hourly_rate") == new_hourly_rate, "Update not persisted"
        print(f"✅ Update persisted correctly")
        
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
        print(f"✅ Template persisted and appears in list")
        
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
        print(f"✅ Template found in list")
        
        # UPDATE (toggle favorite)
        favorite_response = requests.put(
            f"{BASE_URL}/api/pricing/templates/{template_id}/favorite",
            headers=self.headers
        )
        assert favorite_response.status_code == 200
        fav_data = favorite_response.json()
        assert fav_data.get("is_favorite") == True, "Favorite not toggled"
        print(f"✅ Template favorited")
        
        # DELETE
        delete_response = requests.delete(
            f"{BASE_URL}/api/pricing/templates/{template_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        print(f"✅ Template deleted")
        
        # Verify deletion
        verify_response = requests.get(
            f"{BASE_URL}/api/pricing/templates",
            headers=self.headers
        )
        templates = verify_response.json()
        found = any(t["id"] == template_id for t in templates)
        assert not found, "Template still exists after deletion"
        print(f"✅ Template deletion verified")
    
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
        print(f"✅ Calculate endpoint requires auth (401)")
    
    def test_templates_requires_auth(self):
        """Test GET /api/pricing/templates requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/templates",
            headers={"Content-Type": "application/json"}  # No auth header
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Templates endpoint requires auth (401)")
    
    def test_defaults_requires_auth(self):
        """Test GET /api/pricing/defaults requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/pricing/defaults",
            headers={"Content-Type": "application/json"}  # No auth header
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ Defaults endpoint requires auth (401)")


# Cleanup function to remove test templates
def cleanup_test_templates():
    """Remove all TEST_ prefixed templates"""
    BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
    
    # Login
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "testowner@signguy.com",
        "password": "Test123!"
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
