# Pricing Calculator Dimension Field Audit

**Purpose**: Identify dimension field usage across all calculators before Phase 2D rollout  
**Goal**: Ensure all calculators use canonical Phase 1 fields (height_inches, width_inches)  
**Date**: Pre-Phase 2D Audit

---

## 📊 AUDIT SUMMARY TABLE

| Calculator | width Field | height Field | Area Calc | Bug Risk | Phase 2 Ready | Notes |
|------------|-------------|--------------|-----------|----------|---------------|-------|
| **rigid_signs** | ✅ width_inches | ✅ height_inches | ✅ Correct | ✅ FIXED | ✅ YES | Fixed in Phase 2 bug fix |
| **banners** | ✅ width_inches | ❌ length_inches | ⚠️ May fail | 🔴 HIGH | ⚠️ NEEDS FIX | Same bug as rigid_signs |
| **cut_vinyl** | ✅ width_inches | ❌ length_inches | ⚠️ May fail | 🔴 HIGH | ⚠️ NEEDS FIX | Same bug as rigid_signs |
| **digital_print** | ✅ width_inches | ❌ length_inches | ⚠️ May fail | 🔴 HIGH | ⚠️ NEEDS FIX | Same bug as rigid_signs |
| **vehicle_graphics** | N/A | N/A | ✅ Correct | ✅ NONE | ✅ YES | Uses vehicle_type + coverage, no dimensions |
| **services** | N/A | N/A | N/A | ✅ NONE | ✅ YES | Uses estimated_hours, no dimensions |
| **promotional** | N/A | N/A | N/A | ✅ NONE | ✅ YES | Uses unit_cost, no dimensions |
| **custom** | N/A | N/A | N/A | ✅ NONE | ✅ YES | Uses unit_cost + hours, no dimensions |
| **apparel** | N/A | N/A | N/A | ✅ NONE | ✅ YES | Uses quantity tiers, no dimensions |

---

## 🔍 DETAILED AUDIT RESULTS

### 1. ✅ rigid_signs (FIXED)

**Current Dimension Fields** (after bug fix):
```python
width = data.width_inches or 24
height = data.height_inches or data.length_inches or 24  # ✅ FIXED
```

**Supports height_inches**: ✅ YES (after fix)  
**Relies on length_inches only**: ❌ NO (has fallback)  
**Area Calculation**: ✅ CORRECT  
```python
area_per_piece = (width * height) / 144 if unit != "feet" else (width * height)
```

**Safe for Phase 2**: ✅ YES  
**Risk**: ✅ NONE - Already using standardized response  
**Special Logic**: None - straightforward dimension-based pricing

---

### 2. ⚠️ banners (NEEDS FIX)

**Current Dimension Fields**:
```python
width = float(data.width_inches or 0)
height = float(data.length_inches or 0)  # ❌ BUG
```

**Location**: Line 1491-1492

**Supports height_inches**: ❌ NO  
**Relies on length_inches only**: ✅ YES (BUG)  
**Area Calculation**: ⚠️ MAY FAIL  
```python
area_per_piece = (width * height) / 144 if unit != "feet" else (width * height)
```

**Safe for Phase 2**: ⚠️ NO - Must fix dimension bug first  

**Risk**: 🔴 **HIGH** - Same bug as rigid_signs  
- If user sends `height_inches: 96`, it will be ignored
- Will default to `height = 0` → incorrect area
- Material costs will be wrong

**Fix Required**:
```python
width = float(data.width_inches or 0)
height = float(data.height_inches or data.length_inches or 0)  # ✅ FIX
```

**Special Logic**:
- Supports both inches and feet units
- Complex finishing options (hems, grommets, pole pockets, wind slits)
- Hardware handling logic
- Perimeter-based calculations for hems

**Phase 2 Conversion Notes**:
- After fixing dimensions, safe to convert
- Need to separate finishing costs from material_cost
- Need to itemize hardware separately
- Keep complex hem/grommet logic in legacy breakdown

---

### 3. ⚠️ cut_vinyl (NEEDS FIX)

**Current Dimension Fields**:
```python
width = data.width_inches or 12
height = data.length_inches or 12  # ❌ BUG
```

**Location**: Line 699-700

**Supports height_inches**: ❌ NO  
**Relies on length_inches only**: ✅ YES (BUG)  
**Area Calculation**: ⚠️ MAY FAIL  
```python
area_per_piece = (width * height) / 144 if unit != "feet" else (width * height)
```

**Safe for Phase 2**: ⚠️ NO - Must fix dimension bug first

**Risk**: 🔴 **HIGH** - Same bug as rigid_signs  

**Fix Required**:
```python
width = data.width_inches or 12
height = data.height_inches or data.length_inches or 12  # ✅ FIX
```

**Special Logic**:
- Masking/transfer tape logic
- Color count multipliers
- Weeding complexity multipliers
- Design complexity factors
- Install labor calculation

**Phase 2 Conversion Notes**:
- After fixing dimensions, safe to convert
- Transfer tape should be in `finishing_cost` (not material_cost)
- Install labor should be in `install_cost` (not labor_cost)
- Design hours should be in `design_cost` (not labor_cost)

---

### 4. ⚠️ digital_print (NEEDS FIX)

**Current Dimension Fields**:
```python
width = data.width_inches or 24
height = data.length_inches or 24  # ❌ BUG
```

**Location**: Line 866-867

**Supports height_inches**: ❌ NO  
**Relies on length_inches only**: ✅ YES (BUG)  
**Area Calculation**: ⚠️ MAY FAIL  
```python
area_per_piece = (width * height) / 144 if unit != "feet" else (width * height)
```

**Safe for Phase 2**: ⚠️ NO - Must fix dimension bug first

**Risk**: 🔴 **HIGH** - Same bug as rigid_signs

**Fix Required**:
```python
width = data.width_inches or 24
height = data.height_inches or data.length_inches or 24  # ✅ FIX
```

**Special Logic**:
- Media type selection
- Ink coverage calculations
- Laminate cost logic
- Install labor calculation
- Design hours calculation

**Phase 2 Conversion Notes**:
- After fixing dimensions, safe to convert
- Ink should stay in `material_cost` (consumable)
- Laminate should be in `finishing_cost`
- Install labor should be in `install_cost`
- Design hours should be in `design_cost`

---

### 5. ✅ vehicle_graphics (NO DIMENSIONS)

**Current Dimension Fields**: NONE - Uses vehicle type + coverage

**Dimension Logic**:
```python
vehicle_type = data.vehicle_type or "van_cargo"
coverage_raw = data.coverage_type or cfg.get("default_coverage_type", "spot")
vehicle_base_sqft = 160.0  # Looked up from materials library
estimated_area_per_vehicle = float(data.estimated_vehicle_sqft or (vehicle_base_sqft * coverage_factor))
```

**Supports height_inches**: N/A  
**Relies on length_inches only**: N/A  
**Area Calculation**: ✅ CORRECT (uses vehicle_base_sqft * coverage_factor)

**Safe for Phase 2**: ✅ YES

**Risk**: ✅ **NONE** - No dimension fields used

**Special Logic**:
- Vehicle type lookup (car, van, truck, etc.)
- Coverage type (spot, partial, half, full, custom %)
- Laminate logic
- Window perf logic
- Complexity multipliers (difficulty, number of colors, seams)
- Two-installer logic
- Surface prep and removal fees

**Phase 2 Conversion Notes**:
- Safe to convert immediately (no dimension bug)
- Need to separate:
  - Vinyl material → `material_cost`
  - Laminate → `finishing_cost`
  - Window perf → `finishing_cost` or separate category
  - Design hours → `design_cost`
  - Prep/removal → `labor_cost` or `outsourcing_cost`
  - Install → `install_cost`

---

### 6. ✅ services (NO DIMENSIONS)

**Current Dimension Fields**: NONE - Uses estimated_hours

**Dimension Logic**: N/A - Time-based pricing

**Calculation**:
```python
estimated_hours = float(data.estimated_hours or 0)
labor_cost = estimated_hours * labor_cost_rate
labor_sell_baseline = estimated_hours * labor_sell_rate
```

**Supports height_inches**: N/A  
**Relies on length_inches only**: N/A  
**Area Calculation**: N/A

**Safe for Phase 2**: ✅ YES

**Risk**: ✅ **NONE** - No dimension fields

**Special Logic**:
- Service type selection
- Billing unit (hour, day, job, sqft, linear_ft)
- Labor role selection
- Complexity multipliers
- Travel cost
- Equipment rental
- Subcontract cost
- Permit fees
- Multiple sell methods (cost_plus, pass_through_plus_markup, max_of_both)

**Phase 2 Conversion Notes**:
- Safe to convert immediately
- Already has most costs separated:
  - Labor → `labor_cost`
  - Travel → `outsourcing_cost` or separate
  - Equipment → `outsourcing_cost` or separate
  - Subcontract → `outsourcing_cost`
  - Permit → `outsourcing_cost` or separate
- Complex logic should stay in legacy breakdown

---

### 7. ✅ promotional (NO DIMENSIONS)

**Current Dimension Fields**: NONE - Uses unit_cost

**Dimension Logic**: N/A - Unit-based pricing

**Calculation**:
```python
base_cost = data.unit_cost or material_cost_map.get("misc_material", 0)
material_cost = base_cost * quantity
labor_hours = float(category_config.get("default_labor_hours_per_unit", 0.25) or 0.25) * quantity
```

**Supports height_inches**: N/A  
**Relies on length_inches only**: N/A  
**Area Calculation**: N/A

**Safe for Phase 2**: ✅ YES

**Risk**: ✅ **NONE** - No dimension fields

**Special Logic**:
- Product type selection
- Setup fee (optional, flat, not marked up)
- Markup percent override
- Double-sided art multipliers
- Quantity discounts

**Phase 2 Conversion Notes**:
- Safe to convert immediately
- Simple structure:
  - Material → `material_cost`
  - Labor → `labor_cost`
  - Setup → `setup_cost`
- Double-sided logic can stay in legacy breakdown

---

### 8. ✅ custom (NO DIMENSIONS)

**Current Dimension Fields**: NONE - Uses unit_cost + estimated_hours

**Dimension Logic**: N/A - Manual pricing

**Calculation**:
```python
material_cost = (data.unit_cost or material_cost_map.get("misc_material", 0)) * quantity
labor_hours = data.estimated_hours or (float(category_config.get("default_labor_hours_per_unit", 0.25) or 0.25) * quantity)
labor_cost = labor_hours * hourly_rate
```

**Supports height_inches**: N/A  
**Relies on length_inches only**: N/A  
**Area Calculation**: N/A

**Safe for Phase 2**: ✅ YES

**Risk**: ✅ **NONE** - No dimension fields

**Special Logic**:
- Fully manual inputs
- Hourly rate override
- Estimated hours override
- Markup percent override
- Price override (bypass all calculations)

**Phase 2 Conversion Notes**:
- Safe to convert immediately
- Very simple structure:
  - Material → `material_cost`
  - Labor → `labor_cost`
- Price override logic should be handled in helper

---

### 9. ✅ apparel (NO DIMENSIONS)

**Current Dimension Fields**: NONE - Uses quantity tiers + decoration method

**Dimension Logic**: N/A - Table-based pricing

**Calculation**:
```python
# Blank cost
blank_cost_per_piece = float((blank_material or {}).get("cost_per_unit", 0) or 0)
total_blank_cost = blank_cost_per_piece * qty

# Decoration (from shop table or cost-plus)
per_piece_sell = shop_table[brand_key][tier_key][placement_key]
# OR cost-plus using method config
```

**Supports height_inches**: N/A  
**Relies on length_inches only**: N/A  
**Area Calculation**: N/A

**Safe for Phase 2**: ✅ YES

**Risk**: ✅ **NONE** - No dimension fields

**Special Logic**:
- Product type (t-shirt, hoodie, hat, etc.)
- Brand/style selection
- Placement set (front, back, sleeve, etc.)
- Decoration method (HTV, screen print, embroidery, DTG)
- Shop pricing table lookup
- Quantity tiers
- Plus-size upcharges
- Custom names/numbers
- Specialty finishes
- Patch add-ons
- Bag and fold
- Setup/design fees based on artwork state

**Phase 2 Conversion Notes**:
- Safe to convert immediately
- Complex structure:
  - Blanks → `material_cost`
  - Decoration materials → `material_cost`
  - Setup/design → `setup_cost` or `design_cost`
  - Plus-size, custom names, specialty → can stay itemized or in finishing
- Shop table logic should stay in legacy breakdown

---

## 🔴 CRITICAL FINDINGS

### Dimension Bug Found in 3 Calculators:

1. **banners** (line 1492) - Uses `length_inches` only
2. **cut_vinyl** (line 700) - Uses `length_inches` only  
3. **digital_print** (line 867) - Uses `length_inches` only

**All three have the same bug as rigid_signs had before the fix.**

### Impact:
- If frontend sends `height_inches: 36`, these calculators will ignore it
- Will default to fallback value (0 for banners, 12 for cut_vinyl/digital_print)
- Incorrect area calculations
- Incorrect material costs
- Incorrect labor costs

### Must Fix Before Phase 2D Rollout:
```python
# BEFORE (Bug):
height = data.length_inches or default_value

# AFTER (Fixed):
height = data.height_inches or data.length_inches or default_value
```

---

## ✅ SAFE CALCULATORS (5 total)

These calculators do NOT use dimension fields and can be converted to Phase 2 immediately:

1. ✅ **vehicle_graphics** - Uses vehicle type + coverage factor
2. ✅ **services** - Uses estimated_hours
3. ✅ **promotional** - Uses unit_cost
4. ✅ **custom** - Uses unit_cost + estimated_hours
5. ✅ **apparel** - Uses quantity tiers + shop table

---

## 📋 RECOMMENDED PHASE 2D ROLLOUT SEQUENCE

### Step 1: Fix Dimension Bugs (REQUIRED FIRST)
1. Fix **banners** (line 1492)
2. Fix **cut_vinyl** (line 700)
3. Fix **digital_print** (line 867)
4. Test each with `width_inches: 24, height_inches: 36`
5. Verify area = 6.0, not default values

### Step 2: Convert Safe Calculators (NO BUGS)
6. Convert **vehicle_graphics** (complex but no dimension bug)
7. Convert **services** (complex pricing methods)
8. Convert **promotional** (simple)
9. Convert **custom** (simple)
10. Convert **apparel** (most complex - shop table logic)

### Step 3: Convert Fixed Dimension Calculators
11. Convert **banners** (after dimension fix)
12. Convert **cut_vinyl** (after dimension fix)
13. Convert **digital_print** (after dimension fix)

---

## ⚠️ SPECIAL CONSIDERATIONS

### Complex Logic to Preserve:

1. **banners**: Hem calculations (perimeter-based), grommet spacing, pole pockets
2. **cut_vinyl**: Color multipliers, weeding complexity, masking logic
3. **digital_print**: Ink coverage calculations, laminate logic
4. **vehicle_graphics**: Coverage factors, complexity multipliers, two-installer logic
5. **services**: Multiple billing units, sell method selection
6. **apparel**: Shop table lookup, quantity tiers, decoration methods

**All complex logic should be preserved in `legacy_breakdown.metadata`**

---

## 🎯 NEXT ACTIONS

### Before Phase 2D:
1. ✅ Fix dimension bug in banners (line 1492)
2. ✅ Fix dimension bug in cut_vinyl (line 700)
3. ✅ Fix dimension bug in digital_print (line 867)
4. ✅ Test all 3 fixes with `height_inches: 36`
5. ✅ Verify area calculations correct

### Phase 2D Rollout:
6. Convert vehicle_graphics (safe, no bugs)
7. Convert services (safe, no bugs)
8. Convert promotional (safe, no bugs)
9. Convert custom (safe, no bugs)
10. Convert apparel (safe, no bugs)
11. Convert banners (after fix)
12. Convert cut_vinyl (after fix)
13. Convert digital_print (after fix)

### Testing Strategy:
- Test each calculator with both `height_inches` and `length_inches`
- Verify backward compatibility (legacy field still works)
- Verify area calculations (6.0 sqft for 24×36)
- Verify material costs scale correctly
- Verify all breakdown arrays populated

---

**End of Audit**
