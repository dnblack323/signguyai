"""
Pricing Foundation API Tests - Iteration 108
Tests for the new unified Pricing Foundation page backend endpoints.
Tests GET/PUT /api/pricing/defaults with new fields (waste_percentage, admin_hourly_rate, 
rush_fee_percentage, rounding_rule, deposit_percentage).
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestPricingFoundationAPI:
    """Test Pricing Foundation API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_response.status_code} - {login_response.text}")
    
    def test_get_pricing_defaults(self):
        """Test GET /api/pricing/defaults returns data with all expected fields"""
        response = self.session.get(f"{BASE_URL}/api/pricing/defaults")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify core fields exist
        assert "production_hourly_rate" in data, "Missing production_hourly_rate"
        assert "design_hourly_rate" in data, "Missing design_hourly_rate"
        assert "install_hourly_rate" in data, "Missing install_hourly_rate"
        
        # Verify NEW fields from Pricing Foundation
        assert "admin_hourly_rate" in data, "Missing admin_hourly_rate (new field)"
        assert "waste_percentage" in data, "Missing waste_percentage (new field)"
        assert "rush_fee_percentage" in data, "Missing rush_fee_percentage (new field)"
        assert "rounding_rule" in data, "Missing rounding_rule (new field)"
        assert "deposit_percentage" in data, "Missing deposit_percentage (new field)"
        
        # Verify overhead fields
        assert "overhead_percentage" in data, "Missing overhead_percentage"
        assert "shop_overhead_per_hour" in data, "Missing shop_overhead_per_hour"
        
        # Verify minimum charges
        assert "minimum_order" in data, "Missing minimum_order"
        assert "minimum_design_charge" in data, "Missing minimum_design_charge"
        assert "minimum_install_charge" in data, "Missing minimum_install_charge"
        assert "minimum_vinyl_charge" in data, "Missing minimum_vinyl_charge"
        assert "minimum_print_charge" in data, "Missing minimum_print_charge"
        assert "minimum_sign_charge" in data, "Missing minimum_sign_charge"
        assert "minimum_service_charge" in data, "Missing minimum_service_charge"
        assert "minimum_wrap_charge" in data, "Missing minimum_wrap_charge"
        
        # Verify setup fees
        assert "setup_fee_default" in data, "Missing setup_fee_default"
        assert "setup_fee_vinyl" in data, "Missing setup_fee_vinyl"
        assert "setup_fee_print" in data, "Missing setup_fee_print"
        assert "setup_fee_apparel_screen" in data, "Missing setup_fee_apparel_screen"
        assert "setup_fee_apparel_dtf" in data, "Missing setup_fee_apparel_dtf"
        
        # Verify quantity breaks
        assert "quantity_breaks" in data, "Missing quantity_breaks"
        assert isinstance(data["quantity_breaks"], dict), "quantity_breaks should be a dict"
        
        # Verify materials array
        assert "materials" in data, "Missing materials"
        assert isinstance(data["materials"], list), "materials should be a list"
        
        # Verify category_defaults
        assert "category_defaults" in data, "Missing category_defaults"
        assert isinstance(data["category_defaults"], dict), "category_defaults should be a dict"
        
        # Verify selling_price_benchmarks
        assert "selling_price_benchmarks" in data, "Missing selling_price_benchmarks"
        assert isinstance(data["selling_price_benchmarks"], dict), "selling_price_benchmarks should be a dict"
        
        print(f"✓ GET /api/pricing/defaults returned all expected fields")
        print(f"  - admin_hourly_rate: {data.get('admin_hourly_rate')}")
        print(f"  - waste_percentage: {data.get('waste_percentage')}")
        print(f"  - rush_fee_percentage: {data.get('rush_fee_percentage')}")
        print(f"  - rounding_rule: {data.get('rounding_rule')}")
        print(f"  - deposit_percentage: {data.get('deposit_percentage')}")
        print(f"  - materials count: {len(data.get('materials', []))}")
        print(f"  - category_defaults keys: {list(data.get('category_defaults', {}).keys())}")
    
    def test_get_pricing_settings_alias(self):
        """Test GET /api/pricing/settings (alias endpoint) works"""
        response = self.session.get(f"{BASE_URL}/api/pricing/settings")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "production_hourly_rate" in data
        assert "materials" in data
        
        print(f"✓ GET /api/pricing/settings alias works correctly")
    
    def test_update_pricing_defaults(self):
        """Test PUT /api/pricing/defaults updates values correctly"""
        # First get current values
        get_response = self.session.get(f"{BASE_URL}/api/pricing/defaults")
        assert get_response.status_code == 200
        original_data = get_response.json()
        
        # Update with new values
        test_updates = {
            "production_hourly_rate": 30.0,
            "admin_hourly_rate": 40.0,
            "waste_percentage": 12.0,
            "rush_fee_percentage": 30.0,
            "rounding_rule": "nearest_5",
            "deposit_percentage": 55.0
        }
        
        put_response = self.session.put(
            f"{BASE_URL}/api/pricing/defaults",
            json=test_updates
        )
        
        assert put_response.status_code == 200, f"Expected 200, got {put_response.status_code}: {put_response.text}"
        
        updated_data = put_response.json()
        
        # Verify updates were applied
        assert updated_data.get("production_hourly_rate") == 30.0, "production_hourly_rate not updated"
        assert updated_data.get("admin_hourly_rate") == 40.0, "admin_hourly_rate not updated"
        assert updated_data.get("waste_percentage") == 12.0, "waste_percentage not updated"
        assert updated_data.get("rush_fee_percentage") == 30.0, "rush_fee_percentage not updated"
        assert updated_data.get("rounding_rule") == "nearest_5", "rounding_rule not updated"
        assert updated_data.get("deposit_percentage") == 55.0, "deposit_percentage not updated"
        
        print(f"✓ PUT /api/pricing/defaults updated values correctly")
        
        # Restore original values
        restore_updates = {
            "production_hourly_rate": original_data.get("production_hourly_rate", 28.0),
            "admin_hourly_rate": original_data.get("admin_hourly_rate", 35.0),
            "waste_percentage": original_data.get("waste_percentage", 10.0),
            "rush_fee_percentage": original_data.get("rush_fee_percentage", 25.0),
            "rounding_rule": original_data.get("rounding_rule", "nearest_dollar"),
            "deposit_percentage": original_data.get("deposit_percentage", 50.0)
        }
        
        restore_response = self.session.put(
            f"{BASE_URL}/api/pricing/defaults",
            json=restore_updates
        )
        assert restore_response.status_code == 200, "Failed to restore original values"
        print(f"✓ Original values restored")
    
    def test_update_category_defaults(self):
        """Test updating category_defaults nested object"""
        # Get current values
        get_response = self.session.get(f"{BASE_URL}/api/pricing/defaults")
        assert get_response.status_code == 200
        original_data = get_response.json()
        
        # Update category defaults
        test_updates = {
            "category_defaults": {
                "cut_vinyl": {
                    "default_labor_hours_per_sqft": 0.15,
                    "default_markup_multiplier": 2.5,
                    "minimum_charge": 30.0
                }
            }
        }
        
        put_response = self.session.put(
            f"{BASE_URL}/api/pricing/defaults",
            json=test_updates
        )
        
        assert put_response.status_code == 200, f"Expected 200, got {put_response.status_code}: {put_response.text}"
        
        updated_data = put_response.json()
        
        # Verify category_defaults was updated
        assert "category_defaults" in updated_data
        assert "cut_vinyl" in updated_data["category_defaults"]
        cut_vinyl = updated_data["category_defaults"]["cut_vinyl"]
        assert cut_vinyl.get("default_labor_hours_per_sqft") == 0.15
        assert cut_vinyl.get("default_markup_multiplier") == 2.5
        assert cut_vinyl.get("minimum_charge") == 30.0
        
        print(f"✓ PUT /api/pricing/defaults updated category_defaults correctly")
        
        # Restore original category defaults
        if "category_defaults" in original_data:
            restore_response = self.session.put(
                f"{BASE_URL}/api/pricing/defaults",
                json={"category_defaults": original_data["category_defaults"]}
            )
            assert restore_response.status_code == 200
            print(f"✓ Original category_defaults restored")
    
    def test_update_materials_array(self):
        """Test updating materials array"""
        # Get current values
        get_response = self.session.get(f"{BASE_URL}/api/pricing/defaults")
        assert get_response.status_code == 200
        original_data = get_response.json()
        original_materials = original_data.get("materials", [])
        
        # Add a test material
        test_material = {
            "id": "test-material-123",
            "key": "test_material",
            "name": "Test Material",
            "category": "vinyl",
            "cost_per_unit": 2.50,
            "unit_type": "sqft",
            "is_active": True
        }
        
        updated_materials = original_materials + [test_material]
        
        put_response = self.session.put(
            f"{BASE_URL}/api/pricing/defaults",
            json={"materials": updated_materials}
        )
        
        assert put_response.status_code == 200, f"Expected 200, got {put_response.status_code}: {put_response.text}"
        
        updated_data = put_response.json()
        
        # Verify material was added
        assert "materials" in updated_data
        material_keys = [m.get("key") for m in updated_data["materials"]]
        assert "test_material" in material_keys, "Test material not found in updated materials"
        
        print(f"✓ PUT /api/pricing/defaults updated materials array correctly")
        
        # Restore original materials
        restore_response = self.session.put(
            f"{BASE_URL}/api/pricing/defaults",
            json={"materials": original_materials}
        )
        assert restore_response.status_code == 200
        print(f"✓ Original materials restored")
    
    def test_update_selling_price_benchmarks(self):
        """Test updating selling_price_benchmarks"""
        # Get current values
        get_response = self.session.get(f"{BASE_URL}/api/pricing/defaults")
        assert get_response.status_code == 200
        original_data = get_response.json()
        
        # Update benchmarks
        test_updates = {
            "selling_price_benchmarks": {
                "cut_vinyl": {
                    "average_sell_price_per_sqft": 8.0,
                    "average_order_total": 150.0,
                    "minimum_charge": 35.0
                }
            }
        }
        
        put_response = self.session.put(
            f"{BASE_URL}/api/pricing/defaults",
            json=test_updates
        )
        
        assert put_response.status_code == 200, f"Expected 200, got {put_response.status_code}: {put_response.text}"
        
        updated_data = put_response.json()
        
        # Verify benchmarks were updated
        assert "selling_price_benchmarks" in updated_data
        assert "cut_vinyl" in updated_data["selling_price_benchmarks"]
        cut_vinyl_bench = updated_data["selling_price_benchmarks"]["cut_vinyl"]
        assert cut_vinyl_bench.get("average_sell_price_per_sqft") == 8.0
        
        print(f"✓ PUT /api/pricing/defaults updated selling_price_benchmarks correctly")
        
        # Restore original benchmarks
        if "selling_price_benchmarks" in original_data:
            restore_response = self.session.put(
                f"{BASE_URL}/api/pricing/defaults",
                json={"selling_price_benchmarks": original_data["selling_price_benchmarks"]}
            )
            assert restore_response.status_code == 200
            print(f"✓ Original selling_price_benchmarks restored")
    
    def test_get_pricing_materials(self):
        """Test GET /api/pricing/materials endpoint"""
        response = self.session.get(f"{BASE_URL}/api/pricing/materials")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, dict), "Materials response should be a dict"
        
        print(f"✓ GET /api/pricing/materials returned materials catalog")
        print(f"  - Categories: {list(data.keys())}")
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "healthy"
        
        print(f"✓ API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
