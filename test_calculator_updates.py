#!/usr/bin/env python3
"""
Quick test script to verify the updated pricing calculator functions work correctly.
Tests that the new minute-based labor and design charge logic integrates properly.
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from server import calculate_cut_vinyl, calculate_rigid_signs, calculate_vehicle_graphics, calculate_apparel, calculate_digital_print
from models.pricing import JobItemPricingData

async def test_calculators():
    """Test each updated calculator function with basic data"""
    
    # Mock defaults with new quiz fields
    defaults = {
        "labor": {
            "shop_labor_rate": 75.0,
            "include_labor_in_price": True
        },
        "design": {
            "charge_design_separately": "yes",
            "default_design_rate": 85.0,
            "included_design_minutes": 30.0
        },
        "category_defaults": {
            "cut_vinyl": {
                "production_minutes_basic": 45.0
            },
            "rigid_signs": {
                "production_minutes_basic": 30.0
            },
            "vehicle_wraps": {
                "production_minutes_basic": 120.0
            },
            "apparel": {
                "setup_minutes_per_order": 15.0,
                "production_minutes_per_item": 3.0
            },
            "digital_print": {
                "production_minutes_basic": 25.0
            }
        },
        "materials": [],
        "labor_rates": {
            "production": {"hourly_rate": 75.0},
            "design": {"hourly_rate": 85.0},
            "installation": {"hourly_rate": 95.0}
        }
    }
    
    # Test 1: Cut Vinyl
    print("Testing calculate_cut_vinyl...")
    try:
        data = JobItemPricingData(
            width_inches=12,
            height_inches=12,
            artwork_ready=False,
            artwork_needed=True,
            design_complexity="simple"
        )
        result = await calculate_cut_vinyl(data, 1, defaults)
        print(f"✓ Cut Vinyl - Success! Design cost: ${result.design_cost:.2f}, Labor cost: ${result.labor_cost:.2f}")
    except Exception as e:
        print(f"✗ Cut Vinyl - Error: {e}")
        return False
    
    # Test 2: Rigid Signs
    print("\nTesting calculate_rigid_signs...")
    try:
        data = JobItemPricingData(
            width_inches=24,
            height_inches=24,
            artwork_ready=False,
            artwork_needed=True,
            design_complexity="medium"
        )
        result = await calculate_rigid_signs(data, 1, defaults)
        print(f"✓ Rigid Signs - Success! Design cost: ${result.design_cost:.2f}, Labor cost: ${result.labor_cost:.2f}")
    except Exception as e:
        print(f"✗ Rigid Signs - Error: {e}")
        return False
    
    # Test 3: Vehicle Graphics
    print("\nTesting calculate_vehicle_graphics...")
    try:
        data = JobItemPricingData(
            vehicle_type="van_cargo",
            coverage_type="partial",
            artwork_ready=False,
            artwork_needed=True,
            design_complexity="complex"
        )
        result = await calculate_vehicle_graphics(data, 1, defaults)
        print(f"✓ Vehicle Graphics - Success! Design cost: ${result.design_cost:.2f}, Labor cost: ${result.labor_cost:.2f}")
    except Exception as e:
        print(f"✗ Vehicle Graphics - Error: {e}")
        return False
    
    # Test 4: Apparel
    print("\nTesting calculate_apparel...")
    try:
        data = JobItemPricingData(
            apparel_product_type="short_sleeve_tee",
            artwork_ready=False,
            artwork_needed=True,
            design_complexity="simple"
        )
        result = await calculate_apparel(data, 10, defaults)
        print(f"✓ Apparel - Success! Design cost: ${result.design_cost:.2f}, Labor cost: ${result.labor_cost:.2f}")
    except Exception as e:
        print(f"✗ Apparel - Error: {e}")
        return False
    
    # Test 5: Digital Print
    print("\nTesting calculate_digital_print...")
    try:
        data = JobItemPricingData(
            width_inches=24,
            height_inches=36,
            artwork_ready=False,
            artwork_needed=True,
            design_complexity="medium"
        )
        result = await calculate_digital_print(data, 1, defaults)
        print(f"✓ Digital Print - Success! Design cost: ${result.design_cost:.2f}, Labor cost: ${result.labor_cost:.2f}")
    except Exception as e:
        print(f"✗ Digital Print - Error: {e}")
        return False
    
    # Test 6: Design charge = "no" (should result in $0 design cost)
    print("\nTesting design_charge='no' logic...")
    try:
        defaults_no_charge = {**defaults}
        defaults_no_charge["design"]["charge_design_separately"] = "no"
        data = JobItemPricingData(
            width_inches=12,
            height_inches=12,
            artwork_ready=False,
            artwork_needed=True,
            design_complexity="complex"
        )
        result = await calculate_cut_vinyl(data, 1, defaults_no_charge)
        if result.design_cost == 0:
            print(f"✓ Design charge='no' - Success! Design cost correctly set to $0")
        else:
            print(f"✗ Design charge='no' - Failed! Expected $0, got ${result.design_cost:.2f}")
            return False
    except Exception as e:
        print(f"✗ Design charge='no' - Error: {e}")
        return False
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_calculators())
    sys.exit(0 if success else 1)
