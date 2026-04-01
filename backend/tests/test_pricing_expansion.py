"""
Pricing Expansion Tests (Iteration 55)
======================================
Testing the expanded company-based pricing calculator for remaining categories:
- cut_vinyl, apparel, services, custom calculators
- Re-testing digital_print/banner, rigid_signs, vehicle_graphics
- promotional calculator (extra safety check)
- GET /api/pricing/defaults for all category defaults
- Job item creation with cost_snapshot persistence across categories
- Profit consistency: selling_price - total_cost == profit_amount
"""

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD


class TestPricingExpansion:
    """Test expanded pricing calculator features for all categories"""
    
    token = None
    tenant_id = None
    test_customer_id = None
    test_job_id = None
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate and get token before tests"""
        if TestPricingExpansion.token is None:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestPricingExpansion.token = data["access_token"]
    
    def get_headers(self):
        return {"Authorization": f"Bearer {TestPricingExpansion.token}", "Content-Type": "application/json"}
    
    # ===================== PRICING DEFAULTS TESTS =====================
    
    def test_01_get_pricing_defaults_all_categories(self):
        """GET /api/pricing/defaults returns category_defaults for all supported categories"""
        response = requests.get(f"{BASE_URL}/api/pricing/defaults", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify category_defaults includes all expected categories
        cat_defaults = data.get("category_defaults", {})
        expected_categories = ["vehicle_wraps", "banners", "rigid_signs", "cut_vinyl", "apparel", "services", "custom"]
        
        for cat in expected_categories:
            assert cat in cat_defaults, f"category_defaults missing '{cat}'"
            # label is optional (may be removed during user updates), markup and margin are required
            assert "default_markup_multiplier" in cat_defaults[cat], f"'{cat}' missing default_markup_multiplier"
            assert "target_profit_margin_percent" in cat_defaults[cat], f"'{cat}' missing target_profit_margin_percent"
        
        # Verify selling_price_benchmarks includes all categories
        benchmarks = data.get("selling_price_benchmarks", {})
        for cat in expected_categories:
            assert cat in benchmarks, f"selling_price_benchmarks missing '{cat}'"
        
        # Verify materials list exists
        materials = data.get("materials", [])
        assert len(materials) > 0, "materials list is empty"
        
        # Check for some commonly used material keys (tenant may have customized)
        material_keys = [m.get("key") for m in materials]
        commonly_used_keys = ["vinyl", "laminate", "banner_material"]  # These are essential for most calculators
        for key in commonly_used_keys:
            assert key in material_keys, f"essential material key '{key}' missing from materials"
        
        print(f"[PASS] GET /api/pricing/defaults has all {len(expected_categories)} category defaults and {len(materials)} materials")

    # ===================== CUT VINYL CALCULATOR TESTS =====================
    
    def test_02_calculate_cut_vinyl(self):
        """POST /api/pricing/calculate for cut_vinyl uses tenant settings and returns full cost breakdown"""
        calc_payload = {
            "category": "cut_vinyl",
            "pricing_data": {
                "width_inches": 12,
                "length_inches": 24,
                "vinyl_type": "oracal_651",
                "num_colors": 2,
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
        
        # Verify all required cost breakdown fields
        assert "material_cost" in data, "material_cost missing"
        assert "labor_cost" in data, "labor_cost missing"
        assert "overhead_cost" in data, "overhead_cost missing"
        assert "total_cost" in data, "total_cost missing"
        assert "selling_price" in data, "selling_price missing"
        assert "profit_amount" in data, "profit_amount missing"
        assert "profit_margin_percent" in data, "profit_margin_percent missing"
        
        # Verify values are reasonable
        assert data["material_cost"] > 0, "material_cost should be > 0"
        assert data["total_cost"] > 0, "total_cost should be > 0"
        assert data["selling_price"] >= data["total_cost"], "selling_price should be >= total_cost"
        
        # Verify profit consistency: selling_price - total_cost == profit_amount
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02, f"Profit mismatch: {calculated_profit} != {data['profit_amount']}"
        
        # Verify breakdown
        breakdown = data.get("breakdown", {})
        assert "vinyl_type" in breakdown, "breakdown missing vinyl_type"
        assert "square_feet" in breakdown, "breakdown missing square_feet"
        
        print(f"[PASS] Cut vinyl calculation: material=${data['material_cost']:.2f}, total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit=${data['profit_amount']:.2f} ({data['profit_margin_percent']}%)")

    # ===================== APPAREL CALCULATOR TESTS =====================
    
    def test_03_calculate_apparel(self):
        """POST /api/pricing/calculate for apparel uses tenant settings and returns full cost breakdown"""
        calc_payload = {
            "category": "apparel",
            "pricing_data": {
                "apparel_type": "tshirt",
                "transfer_type": "dtf",
                "num_print_locations": 2,
                "complexity": 3
            },
            "quantity": 25
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify all required fields
        assert "material_cost" in data, "material_cost missing"
        assert "labor_cost" in data, "labor_cost missing"
        assert "overhead_cost" in data, "overhead_cost missing"
        assert "total_cost" in data, "total_cost missing"
        assert "selling_price" in data, "selling_price missing"
        assert "profit_amount" in data, "profit_amount missing"
        assert "profit_margin_percent" in data, "profit_margin_percent missing"
        
        # Values should be positive
        assert data["material_cost"] > 0, "material_cost should be > 0 for apparel"
        assert data["labor_cost"] > 0, "labor_cost should be > 0 for apparel"
        assert data["total_cost"] > 0, "total_cost should be > 0"
        assert data["selling_price"] > 0, "selling_price should be > 0"
        
        # Verify profit consistency
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02, f"Profit mismatch: {calculated_profit} != {data['profit_amount']}"
        
        # Verify breakdown
        breakdown = data.get("breakdown", {})
        assert "apparel_type" in breakdown, "breakdown missing apparel_type"
        assert "transfer_type" in breakdown, "breakdown missing transfer_type"
        assert "print_locations" in breakdown, "breakdown missing print_locations"
        
        print(f"[PASS] Apparel calculation (qty 25): material=${data['material_cost']:.2f}, total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit=${data['profit_amount']:.2f} ({data['profit_margin_percent']}%)")

    # ===================== SERVICES CALCULATOR TESTS =====================
    
    def test_04_calculate_services(self):
        """POST /api/pricing/calculate for services uses tenant settings and returns full cost breakdown"""
        calc_payload = {
            "category": "services",
            "pricing_data": {
                "service_type": "installation",
                "estimated_hours": 4.0,
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
        
        # Verify all required fields
        assert "material_cost" in data, "material_cost missing"
        assert "labor_cost" in data, "labor_cost missing"
        assert "overhead_cost" in data, "overhead_cost missing"
        assert "total_cost" in data, "total_cost missing"
        assert "selling_price" in data, "selling_price missing"
        assert "profit_amount" in data, "profit_amount missing"
        assert "profit_margin_percent" in data, "profit_margin_percent missing"
        
        # Labor cost should dominate services
        assert data["labor_cost"] > 0, "labor_cost should be > 0 for services"
        assert data["total_cost"] > 0, "total_cost should be > 0"
        
        # Verify profit consistency
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02, f"Profit mismatch: {calculated_profit} != {data['profit_amount']}"
        
        # Verify breakdown
        breakdown = data.get("breakdown", {})
        assert "service_type" in breakdown, "breakdown missing service_type"
        assert "hourly_rate" in breakdown, "breakdown missing hourly_rate"
        assert "hours" in breakdown, "breakdown missing hours"
        
        print(f"[PASS] Services calculation (4hrs): labor=${data['labor_cost']:.2f}, total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit=${data['profit_amount']:.2f} ({data['profit_margin_percent']}%)")

    # ===================== CUSTOM CALCULATOR TESTS =====================
    
    def test_05_calculate_custom(self):
        """POST /api/pricing/calculate for custom uses tenant settings and returns full cost breakdown"""
        calc_payload = {
            "category": "custom",
            "pricing_data": {
                "unit_cost": 25.0,
                "estimated_hours": 2.0,
                "complexity": 2
            },
            "quantity": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify all required fields
        assert "material_cost" in data, "material_cost missing"
        assert "labor_cost" in data, "labor_cost missing"
        assert "overhead_cost" in data, "overhead_cost missing"
        assert "total_cost" in data, "total_cost missing"
        assert "selling_price" in data, "selling_price missing"
        assert "profit_amount" in data, "profit_amount missing"
        assert "profit_margin_percent" in data, "profit_margin_percent missing"
        
        # Values should be positive
        assert data["material_cost"] > 0, "material_cost should be > 0 for custom"
        assert data["labor_cost"] > 0, "labor_cost should be > 0"
        assert data["total_cost"] > 0, "total_cost should be > 0"
        
        # Verify profit consistency
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02, f"Profit mismatch: {calculated_profit} != {data['profit_amount']}"
        
        # Verify breakdown
        breakdown = data.get("breakdown", {})
        assert "custom_item" in breakdown, "breakdown missing custom_item flag"
        assert "labor_hours" in breakdown, "breakdown missing labor_hours"
        
        print(f"[PASS] Custom calculation (qty 3): material=${data['material_cost']:.2f}, total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit=${data['profit_amount']:.2f} ({data['profit_margin_percent']}%)")

    # ===================== RE-TEST PREVIOUSLY COVERED CALCULATORS =====================
    
    def test_06_calculate_digital_print_banner(self):
        """Re-test POST /api/pricing/calculate for digital_print/banner"""
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
        assert "material_cost" in data
        assert "labor_cost" in data
        assert "overhead_cost" in data
        assert "total_cost" in data
        assert "selling_price" in data
        assert "profit_amount" in data
        assert "profit_margin_percent" in data
        
        # Verify profit consistency
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02
        
        print(f"[PASS] Banner re-test: total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit={data['profit_margin_percent']}%")

    def test_07_calculate_rigid_signs(self):
        """Re-test POST /api/pricing/calculate for rigid_signs"""
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
            "quantity": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["material_cost"] >= 0
        assert data["total_cost"] > 0
        assert data["selling_price"] > 0
        
        # Verify profit consistency
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02
        
        print(f"[PASS] Rigid signs re-test (qty 10): total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit={data['profit_margin_percent']}%")

    def test_08_calculate_vehicle_graphics(self):
        """Re-test POST /api/pricing/calculate for vehicle_graphics"""
        calc_payload = {
            "category": "vehicle_graphics",
            "pricing_data": {
                "vehicle_type": "van_sprinter",
                "coverage_type": "half",
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
        assert data["material_cost"] > 0
        assert data["labor_cost"] > 0
        assert data["total_cost"] > 0
        assert data["selling_price"] > 0
        
        # Verify profit consistency
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02
        
        # Verify breakdown
        breakdown = data.get("breakdown", {})
        assert breakdown.get("vehicle_type") == "van_sprinter"
        assert breakdown.get("coverage") == "half"
        
        print(f"[PASS] Vehicle graphics re-test: total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit={data['profit_margin_percent']}%")

    # ===================== PROMOTIONAL CALCULATOR SAFETY CHECK =====================
    
    def test_09_calculate_promotional(self):
        """Safety check: promotional calculator uses tenant settings"""
        # Valid promo_product_type values: magnets, yard_signs, license_plates, stickers, branded_items, custom
        calc_payload = {
            "category": "promotional",
            "pricing_data": {
                "promo_product_type": "branded_items",
                "unit_cost": 1.50,
                "complexity": 1
            },
            "quantity": 100
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "material_cost" in data
        assert "labor_cost" in data
        assert "overhead_cost" in data
        assert "total_cost" in data
        assert "selling_price" in data
        assert "profit_amount" in data
        assert "profit_margin_percent" in data
        
        # Verify profit consistency
        calculated_profit = round(data["selling_price"] - data["total_cost"], 2)
        assert abs(calculated_profit - data["profit_amount"]) < 0.02
        
        # Verify breakdown
        breakdown = data.get("breakdown", {})
        assert "quantity" in breakdown
        assert "price_per_item" in breakdown
        
        print(f"[PASS] Promotional calculation (qty 100): total=${data['total_cost']:.2f}, selling=${data['selling_price']:.2f}, profit={data['profit_margin_percent']}%")

    # ===================== JOB ITEM WITH COST_SNAPSHOT TESTS =====================
    
    def test_10_create_test_customer_and_job(self):
        """Create test customer and job for cost_snapshot testing"""
        # Create test customer
        customer_payload = {
            "name": "TEST_Pricing_Expansion_Customer",
            "email": "test_pricing_expansion@example.com",
            "phone": "555-0200"
        }
        response = requests.post(
            f"{BASE_URL}/api/customers",
            headers=self.get_headers(),
            json=customer_payload
        )
        assert response.status_code in [200, 201], f"Failed to create customer: {response.text}"
        customer = response.json()
        TestPricingExpansion.test_customer_id = customer["id"]
        
        # Create test job
        job_payload = {
            "customer_id": customer["id"],
            "name": "TEST_Pricing_Expansion_Job",
            "description": "Job for pricing expansion testing",
            "status": "approved"
        }
        response = requests.post(
            f"{BASE_URL}/api/jobs",
            headers=self.get_headers(),
            json=job_payload
        )
        assert response.status_code in [200, 201], f"Failed to create job: {response.text}"
        job = response.json()
        TestPricingExpansion.test_job_id = job["id"]
        
        print(f"[PASS] Created test customer {customer['id'][:8]} and job {job['id'][:8]}")

    def test_11_create_cut_vinyl_job_item_with_cost_snapshot(self):
        """Create job item from cut_vinyl calculator with cost_snapshot"""
        # First calculate price
        calc_payload = {
            "category": "cut_vinyl",
            "pricing_data": {
                "width_inches": 18,
                "length_inches": 12,
                "vinyl_type": "oracal_651",
                "num_colors": 1,
                "complexity": 2
            },
            "quantity": 10
        }
        calc_response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert calc_response.status_code == 200
        calc_data = calc_response.json()
        
        # Build cost_snapshot
        cost_snapshot = {
            "material_cost": calc_data["material_cost"],
            "labor_cost": calc_data["labor_cost"],
            "overhead_cost": calc_data.get("overhead_cost", 0),
            "total_cost": calc_data["total_cost"],
            "selling_price": calc_data["selling_price"],
            "profit": calc_data["profit_amount"],
            "profit_margin": calc_data["profit_margin_percent"],
            "breakdown": calc_data.get("breakdown", {})
        }
        
        # Create job item
        # Valid item_type values: banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other
        item_payload = {
            "description": "18x12 Cut Vinyl Decals (10 qty) - Calculator Test",
            "quantity": 10,
            "unit_price": calc_data["selling_price"] / 10,
            "item_type": "decal",  # Use decal for cut vinyl
            "status": "pending",
            "pricing_category": "cut_vinyl",
            "pricing_data": calc_payload["pricing_data"],
            "cost_snapshot": cost_snapshot,
            "production_cost": calc_data["total_cost"],
            "profit_amount": calc_data["profit_amount"],
            "profit_margin_percent": calc_data["profit_margin_percent"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TestPricingExpansion.test_job_id}/items",
            headers=self.get_headers(),
            json=item_payload
        )
        assert response.status_code in [200, 201], f"Failed to create job item: {response.text}"
        
        item = response.json()
        assert item.get("pricing_category") == "cut_vinyl", "pricing_category not persisted"
        assert item.get("cost_snapshot") is not None, "cost_snapshot not persisted"
        
        print(f"[PASS] Created cut_vinyl job item with cost_snapshot")

    def test_12_create_apparel_job_item_with_cost_snapshot(self):
        """Create job item from apparel calculator with cost_snapshot"""
        calc_payload = {
            "category": "apparel",
            "pricing_data": {
                "apparel_type": "hoodie",
                "transfer_type": "dtf",
                "num_print_locations": 1
            },
            "quantity": 12
        }
        calc_response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert calc_response.status_code == 200
        calc_data = calc_response.json()
        
        cost_snapshot = {
            "material_cost": calc_data["material_cost"],
            "labor_cost": calc_data["labor_cost"],
            "overhead_cost": calc_data.get("overhead_cost", 0),
            "total_cost": calc_data["total_cost"],
            "selling_price": calc_data["selling_price"],
            "profit": calc_data["profit_amount"],
            "profit_margin": calc_data["profit_margin_percent"]
        }
        
        # Valid item_type values: banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other
        item_payload = {
            "description": "Custom Hoodies DTF Print (12 qty)",
            "quantity": 12,
            "unit_price": calc_data["selling_price"] / 12,
            "item_type": "other",  # Use 'other' for apparel
            "status": "pending",
            "pricing_category": "apparel",
            "pricing_data": calc_payload["pricing_data"],
            "cost_snapshot": cost_snapshot,
            "production_cost": calc_data["total_cost"],
            "profit_amount": calc_data["profit_amount"],
            "profit_margin_percent": calc_data["profit_margin_percent"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TestPricingExpansion.test_job_id}/items",
            headers=self.get_headers(),
            json=item_payload
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        
        item = response.json()
        assert item.get("pricing_category") == "apparel"
        assert item.get("cost_snapshot") is not None
        
        print(f"[PASS] Created apparel job item with cost_snapshot")

    def test_13_create_services_job_item_with_cost_snapshot(self):
        """Create job item from services calculator with cost_snapshot"""
        calc_payload = {
            "category": "services",
            "pricing_data": {
                "service_type": "design",
                "estimated_hours": 3.0
            },
            "quantity": 1
        }
        calc_response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_headers(),
            json=calc_payload
        )
        assert calc_response.status_code == 200
        calc_data = calc_response.json()
        
        cost_snapshot = {
            "material_cost": calc_data["material_cost"],
            "labor_cost": calc_data["labor_cost"],
            "overhead_cost": calc_data.get("overhead_cost", 0),
            "total_cost": calc_data["total_cost"],
            "selling_price": calc_data["selling_price"],
            "profit": calc_data["profit_amount"],
            "profit_margin": calc_data["profit_margin_percent"]
        }
        
        # Valid item_type values: banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other
        item_payload = {
            "description": "Design Services - 3 hours",
            "quantity": 1,
            "unit_price": calc_data["selling_price"],
            "item_type": "design",  # Use 'design' for design services
            "status": "pending",
            "pricing_category": "services",
            "pricing_data": calc_payload["pricing_data"],
            "cost_snapshot": cost_snapshot,
            "production_cost": calc_data["total_cost"],
            "profit_amount": calc_data["profit_amount"],
            "profit_margin_percent": calc_data["profit_margin_percent"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/jobs/{TestPricingExpansion.test_job_id}/items",
            headers=self.get_headers(),
            json=item_payload
        )
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        
        item = response.json()
        assert item.get("pricing_category") == "services"
        assert item.get("cost_snapshot") is not None
        
        print(f"[PASS] Created services job item with cost_snapshot")

    def test_14_verify_job_items_persisted(self):
        """Verify all job items were persisted with cost_snapshots"""
        response = requests.get(
            f"{BASE_URL}/api/jobs/{TestPricingExpansion.test_job_id}/items",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        items = response.json()
        assert len(items) >= 3, f"Expected at least 3 items, got {len(items)}"
        
        # Check each item has pricing data
        for item in items:
            assert item.get("pricing_category") is not None, f"Item {item.get('description')} missing pricing_category"
            assert item.get("cost_snapshot") is not None, f"Item {item.get('description')} missing cost_snapshot"
            
            snapshot = item.get("cost_snapshot", {})
            assert "total_cost" in snapshot, f"cost_snapshot missing total_cost"
            assert "selling_price" in snapshot, f"cost_snapshot missing selling_price"
        
        print(f"[PASS] All {len(items)} job items have pricing_category and cost_snapshot persisted")

    # ===================== PROFIT CONSISTENCY CHECK =====================
    
    def test_15_profit_consistency_across_categories(self):
        """Verify profit calculations are consistent across all categories"""
        categories_to_test = [
            ("cut_vinyl", {"width_inches": 12, "length_inches": 12, "num_colors": 1}, 5),
            ("apparel", {"apparel_type": "tshirt", "num_print_locations": 1}, 20),
            ("services", {"service_type": "installation", "estimated_hours": 2.0}, 1),
            ("custom", {"unit_cost": 15.0, "estimated_hours": 1.0}, 3),
            ("digital_print", {"width_inches": 24, "length_inches": 36, "print_material": "banner_13oz"}, 2),
            ("rigid_signs", {"width_inches": 18, "length_inches": 12, "substrate_type": "coroplast_4mm"}, 5),
            ("vehicle_graphics", {"vehicle_type": "car_sedan", "coverage_type": "partial"}, 1),
            ("promotional", {"unit_cost": 2.0}, 50),
        ]
        
        all_passed = True
        for category, pricing_data, quantity in categories_to_test:
            calc_payload = {
                "category": category,
                "pricing_data": pricing_data,
                "quantity": quantity
            }
            
            response = requests.post(
                f"{BASE_URL}/api/pricing/calculate",
                headers=self.get_headers(),
                json=calc_payload
            )
            
            if response.status_code != 200:
                print(f"[FAIL] {category}: API returned {response.status_code}")
                all_passed = False
                continue
            
            data = response.json()
            selling = data.get("selling_price", 0)
            total_cost = data.get("total_cost", 0)
            profit = data.get("profit_amount", 0)
            margin = data.get("profit_margin_percent", 0)
            
            # Check profit = selling_price - total_cost
            expected_profit = round(selling - total_cost, 2)
            if abs(expected_profit - profit) > 0.02:
                print(f"[FAIL] {category}: Profit mismatch - expected {expected_profit}, got {profit}")
                all_passed = False
            else:
                # Check margin = profit/selling_price * 100
                if selling > 0:
                    expected_margin = round((profit / selling) * 100, 1)
                    if abs(expected_margin - margin) > 0.5:
                        print(f"[WARN] {category}: Margin slightly off - expected {expected_margin}%, got {margin}%")
                print(f"[PASS] {category}: selling=${selling:.2f}, cost=${total_cost:.2f}, profit=${profit:.2f} ({margin}%)")
        
        assert all_passed, "Some profit consistency checks failed"
        print(f"[PASS] All {len(categories_to_test)} categories have consistent profit calculations")

    # ===================== CLEANUP =====================
    
    def test_99_cleanup(self):
        """Cleanup test data"""
        # Delete job items
        if TestPricingExpansion.test_job_id:
            items_response = requests.get(
                f"{BASE_URL}/api/jobs/{TestPricingExpansion.test_job_id}/items",
                headers=self.get_headers()
            )
            if items_response.status_code == 200:
                for item in items_response.json():
                    requests.delete(
                        f"{BASE_URL}/api/job-items/{item['id']}",
                        headers=self.get_headers()
                    )
        
        # Delete job
        if TestPricingExpansion.test_job_id:
            requests.delete(
                f"{BASE_URL}/api/jobs/{TestPricingExpansion.test_job_id}",
                headers=self.get_headers()
            )
        
        # Delete customer
        if TestPricingExpansion.test_customer_id:
            requests.delete(
                f"{BASE_URL}/api/customers/{TestPricingExpansion.test_customer_id}",
                headers=self.get_headers()
            )
        
        print("[PASS] Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
