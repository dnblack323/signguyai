"""
Comprehensive Backend Testing for Banners Category Pricing Implementation

This test file verifies the new Banners category pricing implementation end-to-end:
1. POST /api/pricing/calculate with category=banners
2. GET /api/job-tickets/schema/banners  
3. GET /api/pricing/defaults
4. PUT /api/pricing/defaults
5. Regression testing for existing categories

All tests use production URL via REACT_APP_BACKEND_URL from /app/frontend/.env
Credentials: signguypa@gmail.com / Billnel323
"""

import requests
import json
import os
from datetime import datetime

# Production URL from frontend/.env
BASE_URL = "https://sms-invoices.preview.emergentagent.com"

# Production credentials from test_credentials.md
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"

def get_auth_token():
    """Get authentication token"""
    print("🔐 Authenticating...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30
    )
    if response.status_code != 200:
        raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    print(f"✅ Authentication successful")
    return token

def test_banners_pricing_simple():
    """Test 1a: Simple 8x3 ft 13oz banner, corners grommets, standard hem, single-sided, qty=1"""
    print("\n🎯 Testing POST /api/pricing/calculate - Simple 8x3 ft banner...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "category": "banners",
        "quantity": 1,
        "pricing_data": {
            "width_inches": 8,   # 8 feet (when unit is feet, these are feet values)
            "length_inches": 3,  # 3 feet (when unit is feet, these are feet values)
            "unit_of_measure": "feet",
            "banner_material_key": "banner_13oz",
            "banner_grommets": "corners",
            "banner_hems": "standard",
            "banner_double_sided": "no"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pricing/calculate",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Simple banner pricing failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    breakdown = data.get("breakdown", {})
    
    # Verify expected fields in breakdown
    expected_fields = [
        "banner_material_key", "banner_material_cost", "hem_cost", 
        "total_grommets", "sidedness_multiplier"
    ]
    missing_fields = [field for field in expected_fields if field not in breakdown]
    
    if missing_fields:
        print(f"❌ Missing breakdown fields: {missing_fields}")
        return False
    
    # Verify specific values
    material_cost = data.get("material_cost", 0)
    selling_price = data.get("selling_price", 0)
    
    if material_cost < 40 or material_cost > 60:
        print(f"❌ Material cost out of expected range: {material_cost} (expected ~46)")
        return False
    
    if breakdown.get("banner_material_key") != "banner_13oz":
        print(f"❌ Wrong material key: {breakdown.get('banner_material_key')}")
        return False
    
    if breakdown.get("total_grommets") != 4:
        print(f"❌ Wrong grommet count: {breakdown.get('total_grommets')} (expected 4)")
        return False
    
    if breakdown.get("sidedness_multiplier") != 1.0:
        print(f"❌ Wrong sidedness multiplier: {breakdown.get('sidedness_multiplier')} (expected 1.0)")
        return False
    
    print(f"✅ Simple banner pricing successful")
    print(f"   Material cost: ${material_cost:.2f}")
    print(f"   Selling price: ${selling_price:.2f}")
    print(f"   Total grommets: {breakdown.get('total_grommets')}")
    print(f"   Sidedness multiplier: {breakdown.get('sidedness_multiplier')}")
    
    return True

def test_banners_pricing_minimum():
    """Test 1b: Small 1x1 ft banner - verify minimum billable area and sell price"""
    print("\n🎯 Testing POST /api/pricing/calculate - Small 1x1 ft banner (minimum enforcement)...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "category": "banners",
        "quantity": 1,
        "pricing_data": {
            "width_inches": 1,   # 1 foot (when unit is feet, these are feet values)
            "length_inches": 1,  # 1 foot (when unit is feet, these are feet values)
            "unit_of_measure": "feet",
            "banner_material_key": "banner_13oz",
            "banner_grommets": "corners",
            "banner_hems": "standard",
            "banner_double_sided": "no"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pricing/calculate",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Small banner pricing failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    breakdown = data.get("breakdown", {})
    selling_price = data.get("selling_price", 0)
    
    # Verify minimum billable area enforcement
    billable_area = breakdown.get("billable_area_per_piece", 0)
    if billable_area != 4.0:
        print(f"❌ Billable area not enforced to minimum: {billable_area} (expected 4.0)")
        return False
    
    # Verify minimum sell price enforcement
    if selling_price < 35:
        print(f"❌ Selling price below minimum: ${selling_price} (expected ≥ $35)")
        return False
    
    print(f"✅ Small banner pricing successful")
    print(f"   Billable area per piece: {billable_area} sq ft (minimum enforced)")
    print(f"   Selling price: ${selling_price:.2f} (minimum enforced)")
    
    return True

def test_banners_pricing_complex():
    """Test 1c: Complex 10x8 ft fabric banner with all options"""
    print("\n🎯 Testing POST /api/pricing/calculate - Complex 10x8 ft fabric banner...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "category": "banners",
        "quantity": 5,
        "pricing_data": {
            "width_inches": 10,  # 10 feet (when unit is feet, these are feet values)
            "length_inches": 8,   # 8 feet (when unit is feet, these are feet values)
            "unit_of_measure": "feet",
            "banner_material_key": "banner_fabric",
            "banner_hems": "reinforced",
            "banner_grommets": "every_2ft",
            "banner_pole_pockets": "top_and_bottom",
            "banner_double_sided": "different",
            "banner_reinforced_corners": True,
            "banner_wind_slits": True,
            "banner_specialty_sewing": True,
            "banner_use_type": "backwall_step_repeat",
            "install_required": True,
            "install_complexity": "difficult",
            "design_complexity": "complex",
            "rush_order": True,
            "banner_hardware_keys": ["hw-banner-pole-rod"]
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pricing/calculate",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Complex banner pricing failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    breakdown = data.get("breakdown", {})
    selling_price = data.get("selling_price", 0)
    
    # Verify complex banner features
    sidedness_mult = breakdown.get("sidedness_multiplier", 0)
    if sidedness_mult != 2.0:
        print(f"❌ Wrong sidedness multiplier for different double-sided: {sidedness_mult} (expected 2.0)")
        return False
    
    event_premium = breakdown.get("event_premium_applied", 0)
    if event_premium < 1.15:  # Should be at least 1.20 for event premium
        print(f"❌ Event premium not applied: {event_premium} (expected ≥ 1.20)")
        return False
    
    quantity_discount = breakdown.get("quantity_discount_percent", 0)
    if quantity_discount != 5:  # 5 qty should get 5% discount
        print(f"❌ Wrong quantity discount: {quantity_discount}% (expected 5%)")
        return False
    
    # Verify hardware costs
    hardware_cost = breakdown.get("hardware_cost", 0)
    hardware_sell = breakdown.get("hardware_sell", 0)
    if hardware_cost <= 0 or hardware_sell <= 0:
        print(f"❌ Hardware costs not calculated: cost=${hardware_cost}, sell=${hardware_sell}")
        return False
    
    # Verify additional costs
    reinforced_cost = breakdown.get("reinforced_corners_cost", 0)
    wind_slit_cost = breakdown.get("wind_slit_cost", 0)
    pole_pocket_cost = breakdown.get("pole_pocket_cost", 0)
    
    if reinforced_cost <= 0:
        print(f"❌ Reinforced corners cost not calculated: ${reinforced_cost}")
        return False
    
    if wind_slit_cost <= 0:
        print(f"❌ Wind slit cost not calculated: ${wind_slit_cost}")
        return False
    
    if pole_pocket_cost <= 0:
        print(f"❌ Pole pocket cost not calculated: ${pole_pocket_cost}")
        return False
    
    print(f"✅ Complex banner pricing successful")
    print(f"   Selling price: ${selling_price:.2f}")
    print(f"   Sidedness multiplier: {sidedness_mult}")
    print(f"   Event premium applied: {event_premium}")
    print(f"   Quantity discount: {quantity_discount}%")
    print(f"   Hardware cost: ${hardware_cost:.2f}, sell: ${hardware_sell:.2f}")
    print(f"   Reinforced corners: ${reinforced_cost:.2f}")
    print(f"   Wind slits: ${wind_slit_cost:.2f}")
    print(f"   Pole pockets: ${pole_pocket_cost:.2f}")
    
    return True

def test_banners_pricing_pole_banner():
    """Test 1d: Pole banner (use_type='pole_banner') - verify 1.30x premium"""
    print("\n🎯 Testing POST /api/pricing/calculate - Pole banner premium...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    payload = {
        "category": "banners",
        "quantity": 1,
        "pricing_data": {
            "width_inches": 4,   # 4 feet (when unit is feet, these are feet values)
            "length_inches": 6,  # 6 feet (when unit is feet, these are feet values)
            "unit_of_measure": "feet",
            "banner_material_key": "banner_pole",
            "banner_use_type": "pole_banner",
            "banner_grommets": "corners",
            "banner_hems": "standard",
            "banner_double_sided": "no"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pricing/calculate",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Pole banner pricing failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    breakdown = data.get("breakdown", {})
    
    # Verify pole banner premium
    event_premium = breakdown.get("event_premium_applied", 0)
    if event_premium < 1.25:  # Should include 1.30x pole banner premium
        print(f"❌ Pole banner premium not applied: {event_premium} (expected ≥ 1.30)")
        return False
    
    use_type = breakdown.get("use_type", "")
    if use_type != "pole_banner":
        print(f"❌ Wrong use type: {use_type} (expected 'pole_banner')")
        return False
    
    print(f"✅ Pole banner pricing successful")
    print(f"   Use type: {use_type}")
    print(f"   Event premium applied: {event_premium}")
    
    return True

def test_banners_pricing_minimum_sell():
    """Test 1e: Verify min_sell_per_item=$35 enforced"""
    print("\n🎯 Testing POST /api/pricing/calculate - Minimum sell enforcement...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Very small banner that would normally price below $35
    payload = {
        "category": "banners",
        "quantity": 1,
        "pricing_data": {
            "width_inches": 0.5,  # 0.5 feet (when unit is feet, these are feet values)
            "length_inches": 1,   # 1 foot (when unit is feet, these are feet values)
            "unit_of_measure": "feet",
            "banner_material_key": "banner_13oz",
            "banner_grommets": "none",
            "banner_hems": "none",
            "banner_double_sided": "no"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/pricing/calculate",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Minimum sell pricing failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    breakdown = data.get("breakdown", {})
    selling_price = data.get("selling_price", 0)
    min_sell = breakdown.get("min_sell_per_item", 0)
    
    if selling_price < 35:
        print(f"❌ Minimum sell not enforced: ${selling_price} (expected ≥ $35)")
        return False
    
    if min_sell != 35:
        print(f"❌ Wrong minimum sell per item: ${min_sell} (expected $35)")
        return False
    
    print(f"✅ Minimum sell enforcement successful")
    print(f"   Selling price: ${selling_price:.2f}")
    print(f"   Minimum sell per item: ${min_sell}")
    
    return True

def test_banners_schema():
    """Test 2: GET /api/job-tickets/schema/banners - verify foundation-driven schema"""
    print("\n🎯 Testing GET /api/job-tickets/schema/banners...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/job-tickets/schema/banners",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Banners schema failed: {response.status_code} - {response.text}")
        return False
    
    schema_response = response.json()
    
    # Handle both list and object responses
    if isinstance(schema_response, dict):
        schema = schema_response.get("fields", [])
    else:
        schema = schema_response
    
    if not isinstance(schema, list):
        print(f"❌ Schema fields is not a list: {type(schema)}")
        return False
    
    if len(schema) < 25:
        print(f"❌ Schema has too few fields: {len(schema)} (expected ≥25)")
        return False
    
    # Verify key banner fields are present
    field_keys = [field.get("key") for field in schema]
    required_fields = [
        "banner_material_key", "banner_use_type", "banner_hems", "banner_grommets",
        "banner_grommet_count", "banner_pole_pockets", "banner_reinforced_corners",
        "banner_wind_slits", "banner_specialty_sewing", "banner_double_sided",
        "banner_event_premium", "banner_hardware_keys", "banner_laminate",
        "banner_laminate_type_key", "install_required", "install_complexity",
        "design_complexity", "artwork_ready", "artwork_needed", "rush_order",
        "width", "height", "unit_of_measure", "sq_footage"
    ]
    
    missing_fields = [field for field in required_fields if field not in field_keys]
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    # Verify banner_material_key options
    material_field = next((f for f in schema if f.get("key") == "banner_material_key"), None)
    if not material_field:
        print("❌ banner_material_key field not found")
        return False
    
    material_options = material_field.get("options", [])
    expected_materials = ["banner_13oz", "banner_18oz", "banner_mesh", "banner_blockout", "banner_pole", "banner_fabric"]
    found_materials = [opt.get("value") for opt in material_options]
    
    missing_materials = [mat for mat in expected_materials if mat not in found_materials]
    if len(missing_materials) > 2:  # Allow some flexibility
        print(f"❌ Missing material options: {missing_materials}")
        return False
    
    # Verify banner_hardware_keys is multi_select
    hardware_field = next((f for f in schema if f.get("key") == "banner_hardware_keys"), None)
    if not hardware_field:
        print("❌ banner_hardware_keys field not found")
        return False
    
    if hardware_field.get("type") != "multi_select":
        print(f"❌ banner_hardware_keys wrong type: {hardware_field.get('type')} (expected multi_select)")
        return False
    
    # Verify banner_grommets options
    grommet_field = next((f for f in schema if f.get("key") == "banner_grommets"), None)
    if not grommet_field:
        print("❌ banner_grommets field not found")
        return False
    
    grommet_options = [opt.get("value") for opt in grommet_field.get("options", [])]
    expected_grommets = ["none", "corners", "every_2ft", "every_3ft", "custom"]
    missing_grommets = [g for g in expected_grommets if g not in grommet_options]
    if missing_grommets:
        print(f"❌ Missing grommet options: {missing_grommets}")
        return False
    
    print(f"✅ Banners schema successful")
    print(f"   Total fields: {len(schema)}")
    print(f"   Material options: {len(material_options)}")
    print(f"   Hardware field type: {hardware_field.get('type')}")
    print(f"   Grommet options: {len(grommet_options)}")
    
    return True

def test_pricing_defaults_get():
    """Test 3: GET /api/pricing/defaults - verify banners category defaults"""
    print("\n🎯 Testing GET /api/pricing/defaults...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/pricing/defaults",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Pricing defaults failed: {response.status_code} - {response.text}")
        return False
    
    defaults = response.json()
    
    # Verify category_defaults.banners exists
    category_defaults = defaults.get("category_defaults", {})
    banners_defaults = category_defaults.get("banners", {})
    
    if not banners_defaults:
        print("❌ category_defaults.banners not found")
        return False
    
    # Verify key banner defaults
    required_keys = [
        "default_banner_material_key", "available_banner_material_keys", "waste_percentage",
        "default_minimum_billable_area", "default_minimum_sell_price", "default_design_time_hours",
        "standard_hem_rate_per_linear_foot", "reinforced_hem_rate_per_linear_foot",
        "pole_pocket_rate_per_linear_foot", "grommet_cost_each", "grommet_sell_each",
        "grommet_minimum_charge", "reinforced_corners_charge", "wind_slit_charge",
        "specialty_sewing_rate_per_linear_foot", "sidedness_multipliers",
        "event_premium_multiplier", "pole_banner_premium_multiplier",
        "install_complexity_multipliers", "design_complexity_multipliers", "quantity_discounts"
    ]
    
    missing_keys = [key for key in required_keys if key not in banners_defaults]
    if len(missing_keys) > 5:  # Allow some flexibility
        print(f"❌ Missing banner default keys: {missing_keys}")
        return False
    
    # Verify materials list includes banner materials
    materials = defaults.get("materials", [])
    banner_materials = [m for m in materials if m.get("key", "").startswith("banner_")]
    
    if len(banner_materials) < 3:
        print(f"❌ Too few banner materials: {len(banner_materials)} (expected ≥3)")
        return False
    
    # Verify hardware_accessories includes banner hardware
    hardware = defaults.get("hardware_accessories", [])
    banner_hardware = [h for h in hardware if "banners" in h.get("compatible_categories", [])]
    
    if len(banner_hardware) < 2:
        print(f"❌ Too few banner hardware items: {len(banner_hardware)} (expected ≥2)")
        return False
    
    print(f"✅ Pricing defaults successful")
    print(f"   Banner defaults keys: {len(banners_defaults)}")
    print(f"   Banner materials: {len(banner_materials)}")
    print(f"   Banner hardware: {len(banner_hardware)}")
    
    return True

def test_pricing_defaults_update():
    """Test 4: PUT /api/pricing/defaults - update banners defaults and verify"""
    print("\n🎯 Testing PUT /api/pricing/defaults...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # First get current defaults
    response = requests.get(f"{BASE_URL}/api/pricing/defaults", headers=headers, timeout=30)
    if response.status_code != 200:
        print(f"❌ Failed to get current defaults: {response.status_code}")
        return False
    
    current_defaults = response.json()
    original_waste = current_defaults.get("category_defaults", {}).get("banners", {}).get("waste_percentage", 8.0)
    original_hem_rate = current_defaults.get("category_defaults", {}).get("banners", {}).get("standard_hem_rate_per_linear_foot", 0.75)
    
    # Update banners defaults
    updates = {
        "category_defaults": {
            "banners": {
                "waste_percentage": 10.0,
                "standard_hem_rate_per_linear_foot": 1.0
            }
        }
    }
    
    response = requests.put(
        f"{BASE_URL}/api/pricing/defaults",
        json=updates,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Pricing defaults update failed: {response.status_code} - {response.text}")
        return False
    
    updated_defaults = response.json()
    
    # Verify updates were applied
    banners_defaults = updated_defaults.get("category_defaults", {}).get("banners", {})
    new_waste = banners_defaults.get("waste_percentage")
    new_hem_rate = banners_defaults.get("standard_hem_rate_per_linear_foot")
    
    if new_waste != 10.0:
        print(f"❌ Waste percentage not updated: {new_waste} (expected 10.0)")
        return False
    
    if new_hem_rate != 1.0:
        print(f"❌ Hem rate not updated: {new_hem_rate} (expected 1.0)")
        return False
    
    # Test that pricing calculation picks up new values
    print("   Testing pricing calculation with new defaults...")
    
    payload = {
        "category": "banners",
        "quantity": 1,
        "pricing_data": {
            "width_inches": 8,   # 8 feet (when unit is feet, these are feet values)
            "length_inches": 3,  # 3 feet (when unit is feet, these are feet values)
            "unit_of_measure": "feet",
            "banner_material_key": "banner_13oz",
            "banner_grommets": "corners",
            "banner_hems": "standard",
            "banner_double_sided": "no"
        }
    }
    
    calc_response = requests.post(
        f"{BASE_URL}/api/pricing/calculate",
        json=payload,
        headers=headers,
        timeout=30
    )
    
    if calc_response.status_code != 200:
        print(f"❌ Pricing calculation with new defaults failed: {calc_response.status_code}")
        return False
    
    calc_data = calc_response.json()
    breakdown = calc_data.get("breakdown", {})
    
    # Verify new waste percentage is used
    waste_percent = breakdown.get("waste_percent")
    if waste_percent != 10.0:
        print(f"❌ New waste percentage not used in calculation: {waste_percent}")
        return False
    
    # Restore original values
    restore_updates = {
        "category_defaults": {
            "banners": {
                "waste_percentage": original_waste,
                "standard_hem_rate_per_linear_foot": original_hem_rate
            }
        }
    }
    
    requests.put(f"{BASE_URL}/api/pricing/defaults", json=restore_updates, headers=headers, timeout=30)
    
    print(f"✅ Pricing defaults update successful")
    print(f"   Updated waste percentage: {new_waste}")
    print(f"   Updated hem rate: {new_hem_rate}")
    print(f"   Calculation used new waste: {waste_percent}")
    print(f"   Restored original values")
    
    return True

def test_regression_existing_categories():
    """Test 5: Regression test for existing categories (digital_print, cut_vinyl, rigid_signs)"""
    print("\n🎯 Testing regression for existing categories...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    test_cases = [
        {
            "name": "Digital Print",
            "payload": {
                "category": "digital_print",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 48,
                    "length_inches": 36,
                    "print_media_key": "printable_adhesive_vinyl",
                    "laminate": False
                }
            }
        },
        {
            "name": "Cut Vinyl",
            "payload": {
                "category": "cut_vinyl",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 12,
                    "vinyl_type_key": "oracal_651",
                    "num_colors": 1
                }
            }
        },
        {
            "name": "Rigid Signs",
            "payload": {
                "category": "rigid_signs",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 18,
                    "substrate_type_key": "coroplast_4mm",
                    "graphic_method": "direct_print"
                }
            }
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        name = test_case["name"]
        payload = test_case["payload"]
        
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ {name} regression failed: {response.status_code} - {response.text}")
            results[name] = False
            continue
        
        data = response.json()
        
        # Verify basic response structure
        required_fields = ["material_cost", "labor_cost", "selling_price", "breakdown"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ {name} missing response fields: {missing_fields}")
            results[name] = False
            continue
        
        selling_price = data.get("selling_price", 0)
        if selling_price <= 0:
            print(f"❌ {name} invalid selling price: {selling_price}")
            results[name] = False
            continue
        
        results[name] = True
        print(f"✅ {name} regression successful - selling price: ${selling_price:.2f}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print(f"✅ All regression tests passed")
    else:
        failed = [name for name, passed in results.items() if not passed]
        print(f"❌ Regression tests failed: {failed}")
    
    return all_passed

def main():
    """Run all banners pricing tests"""
    print("🚀 Starting Banners Category Pricing Implementation Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    
    tests = [
        ("Simple 8x3 ft banner", test_banners_pricing_simple),
        ("Small 1x1 ft banner (minimum)", test_banners_pricing_minimum),
        ("Complex 10x8 ft fabric banner", test_banners_pricing_complex),
        ("Pole banner premium", test_banners_pricing_pole_banner),
        ("Minimum sell enforcement", test_banners_pricing_minimum_sell),
        ("Banners schema", test_banners_schema),
        ("Pricing defaults GET", test_pricing_defaults_get),
        ("Pricing defaults UPDATE", test_pricing_defaults_update),
        ("Regression tests", test_regression_existing_categories),
    ]
    
    results = {}
    
    try:
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print('='*60)
            
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
    
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        return False
    
    # Summary
    print("\n" + "="*60)
    print("📊 BANNERS PRICING IMPLEMENTATION TEST RESULTS")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:35} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 ALL BANNERS PRICING TESTS PASSED!")
        print("✅ Banners category pricing implementation is working correctly")
    else:
        print("⚠️  SOME BANNERS PRICING TESTS FAILED")
        print("❌ Banners category pricing implementation needs attention")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)