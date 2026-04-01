"""
Pricing Foundation Tests
========================
Testing the new company-based pricing calculator foundation:
- GET/PUT /api/pricing/defaults (tenant-specific pricing settings)
- POST /api/pricing/calculate for digital_print (banners), rigid_signs, vehicle_graphics
- Job item creation with cost_snapshot persistence
- Settings page data-testid and routing validation
"""

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD


class TestPricingFoundation:
    """Test pricing foundation features"""
    
    token = None
    tenant_id = None
    test_customer_id = None
    test_job_id = None
    test_job_item_id = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate and get token before tests"""
        if TestPricingFoundation.token is None:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestPricingFoundation.token = data["access_token"]
    
    def get_headers(self):
        return {"Authorization": f"Bearer {TestPricingFoundation.token}", "Content-Type": "application/json"}
    
    # ===================== PRICING DEFAULTS TESTS =====================
    
    def test_01_get_pricing_defaults(self):
        """GET /api/pricing/defaults returns tenant-specific pricing settings"""
        response = requests.get(f"{BASE_URL}/api/pricing/defaults", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify expected fields exist
        assert "materials" in data, "materials field missing"
        assert "production_hourly_rate" in data, "production_hourly_rate missing"
        assert "overhead_percentage" in data, "overhead_percentage missing"
        assert "target_profit_margin_percent" in data, "target_profit_margin_percent missing"
        assert "default_markup_multiplier" in data, "default_markup_multiplier missing"
        assert "category_defaults" in data, "category_defaults missing"
        assert "selling_price_benchmarks" in data, "selling_price_benchmarks missing"
        
        # Verify category defaults structure
        cat_defaults = data["category_defaults"]
        assert "vehicle_wraps" in cat_defaults, "vehicle_wraps category missing"
        assert "banners" in cat_defaults, "banners category missing"
        assert "rigid_signs" in cat_defaults, "rigid_signs category missing"
        
        # Verify selling benchmarks structure
        benchmarks = data["selling_price_benchmarks"]
        assert "vehicle_wraps" in benchmarks, "vehicle_wraps benchmark missing"
        assert "banners" in benchmarks, "banners benchmark missing"
        assert "rigid_signs" in benchmarks, "rigid_signs benchmark missing"
        
        print(f"[PASS] GET /api/pricing/defaults returned {len(data.get('materials', []))} materials")
    
    def test_02_update_pricing_defaults(self):
        """PUT /api/pricing/defaults saves tenant-specific pricing settings"""
        # Update some settings
        update_payload = {
            "production_hourly_rate": 30.0,
            "overhead_percentage": 18.0,
            "target_profit_margin_percent": 42.0,
            "category_defaults": {
                "banners": {
                    "default_labor_hours_per_sqft": 0.07,
                    "default_markup_multiplier": 2.4,
                    "target_profit_margin_percent": 41.0,
                    "minimum_charge": 40.0
                }
            },
            "selling_price_benchmarks": {
                "banners": {
                    "average_sell_price_per_sqft": 9.0,
                    "average_order_total": 260.0,
                    "minimum_charge": 50.0
                }
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.get_headers(),
            json=update_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify updates were applied
        assert data["production_hourly_rate"] == 30.0, "production_hourly_rate not updated"
        assert data["overhead_percentage"] == 18.0, "overhead_percentage not updated"
        
        # Verify category defaults were merged
        banner_defaults = data["category_defaults"].get("banners", {})
        assert banner_defaults.get("default_labor_hours_per_sqft") == 0.07, "banner labor hours not updated"
        
        # Verify benchmarks were merged
        banner_benchmarks = data["selling_price_benchmarks"].get("banners", {})
        assert banner_benchmarks.get("average_sell_price_per_sqft") == 9.0, "banner benchmark not updated"
        
        print("[PASS] PUT /api/pricing/defaults saved settings correctly")
    
    # ===================== CALCULATE ENDPOINT TESTS =====================
    
    def test_03_calculate_digital_print_banner(self):
        """POST /api/pricing/calculate for digital_print (banner) returns full cost breakdown"""
        calc_payload = {
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 48,
                "length_inches": 96,
                "print_material": "banner_13oz",
                "laminate": False,
                "grommets": True,
                "hemming": True,
                "complexity": 3
            },
            "quantity": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify all required cost breakdown fields
        assert "material_cost" in data, "material_cost missing"
        assert "labor_cost" in data, "labor_cost missing"
        assert "overhead_cost" in data, "overhead_cost missing"
        assert "total_cost" in data, "total_cost missing"
        assert "selling_price" in data, "selling_price missing"
        assert "profit_amount" in data, "profit_amount missing"
        assert "profit_margin_percent" in data, "profit_margin_percent missing"
        
        # Verify reasonable values
        assert data["material_cost"] > 0, "material_cost should be > 0"
        assert data["total_cost"] > 0, "total_cost should be > 0"
        assert data["selling_price"] >= data["total_cost"], "selling_price should be >= total_cost"
        assert data["profit_amount"] >= 0, "profit_amount should be >= 0"
        
        # Verify breakdown details
        assert "breakdown" in data, "breakdown missing"
        breakdown = data["breakdown"]
        assert "square_feet" in breakdown, "breakdown missing square_feet"
        # grommets and hemming are optional fields in breakdown
        assert "grommets" in breakdown, "grommets key missing from breakdown"
        assert "hemming" in breakdown, "hemming key missing from breakdown"
        
        print(f"[PASS] Banner calculation: material=${data['material_cost']:.2f}, total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit=${data['profit_amount']:.2f} ({data['profit_margin_percent']}%)")
    
    def test_04_calculate_rigid_signs(self):
        """POST /api/pricing/calculate for rigid_signs returns full cost breakdown"""
        calc_payload = {
            "category": "rigid_signs",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 18,
                "substrate_type": "coroplast_4mm",
                "double_sided": False,
                "laminate": True,
                "complexity": 2
            },
            "quantity": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify all required fields
        assert data["material_cost"] >= 0, "material_cost should be >= 0"
        assert data["labor_cost"] >= 0, "labor_cost should be >= 0"
        assert data["overhead_cost"] >= 0, "overhead_cost should be >= 0"
        assert data["total_cost"] > 0, "total_cost should be > 0"
        assert data["selling_price"] > 0, "selling_price should be > 0"
        assert data["profit_amount"] >= 0, "profit_amount should be >= 0"
        assert "profit_margin_percent" in data
        
        # Verify breakdown
        breakdown = data.get("breakdown", {})
        assert "substrate" in breakdown, "substrate missing from breakdown"
        
        print(f"[PASS] Rigid signs calculation (qty 5): total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit={data['profit_margin_percent']}%")
    
    def test_05_calculate_vehicle_graphics(self):
        """POST /api/pricing/calculate for vehicle_graphics returns full cost breakdown"""
        calc_payload = {
            "category": "vehicle_graphics",
            "pricing_data": {
                "vehicle_type": "van_cargo",
                "coverage_type": "partial",
                "complexity": 4,
                "include_design": True
            },
            "quantity": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Verify all required fields
        assert data["material_cost"] > 0, "material_cost should be > 0 for vehicle wrap"
        assert data["labor_cost"] > 0, "labor_cost should be > 0 for vehicle wrap"
        assert data["overhead_cost"] >= 0, "overhead_cost should be >= 0"
        assert data["total_cost"] > 0, "total_cost should be > 0"
        assert data["selling_price"] > 0, "selling_price should be > 0"
        assert data["profit_amount"] >= 0, "profit_amount should be >= 0"
        
        # Verify breakdown has vehicle info
        breakdown = data.get("breakdown", {})
        assert breakdown.get("vehicle_type") == "van_cargo", "vehicle_type mismatch"
        assert breakdown.get("coverage") == "partial", "coverage mismatch"
        assert "actual_sqft" in breakdown, "actual_sqft missing"
        
        print(f"[PASS] Vehicle graphics calculation: total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit={data['profit_margin_percent']}%")
    
    # ===================== JOB ITEM WITH COST_SNAPSHOT TESTS =====================
    
    def test_06_create_test_customer_and_job(self):
        """Create a test customer and job for item creation tests"""
        # Create test customer
        customer_payload = {
            "name": "TEST_Pricing_Customer",
            "email": "test_pricing@example.com",
            "phone": "555-0100"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers=self.get_headers(),
            json=customer_payload
        )
        assert response.status_code in [200, 201], f"Failed to create customer: {response.text}"
        customer = response.json()
        TestPricingFoundation.test_customer_id = customer["id"]
        
        # Create test job
        job_payload = {
            "customer_id": customer["id"],
            "name": "TEST_Pricing_Job",
            "description": "Job for pricing foundation testing",
            "status": "approved"
        }
        response = requests.post(
            f"{BASE_URL}/api/jobs",
            headers=self.get_headers(),
            json=job_payload
        )
        assert response.status_code in [200, 201], f"Failed to create job: {response.text}"
        job = response.json()
        TestPricingFoundation.test_job_id = job["id"]
        
        print(f"[PASS] Created test customer {customer['id'][:8]} and job {job['id'][:8]}")
    
    def test_07_create_job_item_with_cost_snapshot(self):
        """POST /api/jobs/{id}/items preserves pricing_category and cost_snapshot"""
        # First calculate a price
        calc_payload = {
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 36,
                "length_inches": 48,
                "print_material": "banner_13oz",
                "complexity": 2
            },
            "quantity": 2
        }
        calc_response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert calc_response.status_code == 200
        calc_data = calc_response.json()
        
        # Build cost_snapshot from calculation
        cost_snapshot = {
            "material_cost": calc_data["material_cost"],
            "labor_cost": calc_data["labor_cost"],
            "overhead_cost": calc_data.get("overhead_cost", 0),
            "total_cost": calc_data["total_cost"],
            "selling_price": calc_data["selling_price"],
            "profit_amount": calc_data["profit_amount"],
            "profit_margin_percent": calc_data["profit_margin_percent"],
            "breakdown": calc_data.get("breakdown", {})
        }
        
        # Create job item with calculator data
        item_payload = {
            "description": "36x48 Banner (2 qty) - Calculator Test",
            "quantity": 2,
            "unit_price": calc_data["selling_price"] / 2,  # per unit
            "item_type": "banner",
            "status": "pending",
            "pricing_category": "digital_print",
            "pricing_data": calc_payload["pricing_data"],
            "cost_snapshot": cost_snapshot,
            "production_cost": calc_data["total_cost"],
            "profit_amount": calc_data["profit_amount"],
            "profit_margin_percent": calc_data["profit_margin_percent"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TestPricingFoundation.test_job_id}/items",
            headers=self.get_headers(),
            json=item_payload
        )
        assert response.status_code in [200, 201], f"Failed to create job item: {response.text}"
        
        item = response.json()
        TestPricingFoundation.test_job_item_id = item["id"]
        
        # Verify cost_snapshot persisted
        assert item.get("pricing_category") == "digital_print", "pricing_category not persisted"
        assert item.get("cost_snapshot") is not None, "cost_snapshot not persisted"
        assert item.get("production_cost") == calc_data["total_cost"], "production_cost not persisted"
        assert item.get("profit_amount") == calc_data["profit_amount"], "profit_amount not persisted"
        
        # Verify cost_snapshot contents
        saved_snapshot = item.get("cost_snapshot", {})
        assert saved_snapshot.get("material_cost") == cost_snapshot["material_cost"], "cost_snapshot material_cost mismatch"
        assert saved_snapshot.get("selling_price") == cost_snapshot["selling_price"], "cost_snapshot selling_price mismatch"
        
        print(f"[PASS] Created job item {item['id'][:8]} with cost_snapshot preserved")
    
    def test_08_get_job_item_verifies_cost_snapshot(self):
        """GET job item verifies cost_snapshot was persisted in database"""
        response = requests.get(
            f"{BASE_URL}/api/job-items/{TestPricingFoundation.test_job_item_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        item = response.json()
        # Verify all pricing fields persisted
        assert item.get("pricing_category") == "digital_print", "pricing_category not in GET response"
        assert item.get("cost_snapshot") is not None, "cost_snapshot not in GET response"
        assert item.get("production_cost", 0) > 0, "production_cost not in GET response"
        assert item.get("profit_amount", 0) >= 0, "profit_amount not in GET response"
        assert "profit_margin_percent" in item, "profit_margin_percent not in GET response"
        
        print("[PASS] GET job item confirms cost_snapshot persisted correctly")
    
    # ===================== CLEANUP =====================
    
    def test_99_cleanup(self):
        """Cleanup test data"""
        # Delete job item
        if TestPricingFoundation.test_job_item_id:
            requests.delete(
                f"{BASE_URL}/api/job-items/{TestPricingFoundation.test_job_item_id}",
                headers=self.get_headers()
            )
        
        # Delete job
        if TestPricingFoundation.test_job_id:
            requests.delete(
                f"{BASE_URL}/api/jobs/{TestPricingFoundation.test_job_id}",
                headers=self.get_headers()
            )
        
        # Delete customer
        if TestPricingFoundation.test_customer_id:
            requests.delete(
                f"{BASE_URL}/api/customers/{TestPricingFoundation.test_customer_id}",
                headers=self.get_headers()
            )
        
        print("[PASS] Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
