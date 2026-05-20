# Banner Foundation Audit Report
**Phase 2A Step 1**: Banner source-of-truth cleanup  
**Date**: December 2025

---

## 🔍 AUDIT FINDINGS

### **Old Banner Fields Found**

#### A. Shop Defaults Tab (Global, Not Banner-Specific)
**File**: `/app/frontend/src/pages/PricingFoundation.js` lines 363-364

```javascript
<Row label="Grommet Price (ea)" field="banner_grommet_price_each" />
<Row label="Hemming Tape / Linear In" field="banner_hemming_tape_price_per_linear_inch" />
```

**Status**: ❌ **DUPLICATE** - These are global fields in Shop Defaults but grommets/hems are banner-specific.  
**Location conflict**: Same fields exist in Category Rules → Banners section (lines 1724-1726)  
**Action needed**: Hide from Shop Defaults tab, keep only in Banner category settings

---

#### B. Category Rules → Banners Section (Current Banner Settings)
**File**: `/app/frontend/src/pages/PricingFoundation.js` lines 1667-1730

**Banner-specific fields that ARE being used** (✅ Keep these):

**Material & Defaults**:
- `default_banner_material_key` (dropdown from Materials Library)
- `default_laminate_key` (dropdown from Materials Library)
- `default_laminate_required` (boolean)
- `default_install_included` (boolean)

**Minimums & Labor**:
- `default_minimum_billable_area` (sqft)
- `default_minimum_sell_price` (per item)
- `default_design_time_hours` (hrs)
- `waste_percentage` (%)
- `production_labor_hours_per_sqft` (hrs/sqft)
- `min_production_labor_hours_per_item` (hrs)
- `install_hours_per_sqft` (hrs/sqft)
- `install_base_hours` (hrs)

**Finishing Rates**:
- `standard_hem_rate_per_linear_foot` ($/lin ft)
- `reinforced_hem_rate_per_linear_foot` ($/lin ft)
- `pole_pocket_rate_per_linear_foot` ($/lin ft)
- `specialty_sewing_rate_per_linear_foot` ($/lin ft)
- `grommet_cost_each` (shop cost)
- `grommet_sell_each` (customer charge)
- `grommet_minimum_charge` (minimum)
- `reinforced_corners_charge` ($)
- `wind_slit_charge` ($)

**Status**: ✅ **ACTIVE** - These are in the right place (Category Rules → Banners)

---

#### C. PricingSetupQuiz Banner Questions
**File**: `/app/frontend/src/components/pricing/PricingSetupQuiz.js` lines 45-52, 490-507

**Quiz questions**:
- `banner_2x4` - 2ft × 4ft banner price
- `banner_3x6` - 3ft × 6ft banner price
- `banner_4x8` - 4ft × 8ft banner price
- `banner_finishing_included` - Hems/grommets included boolean
- `banner_production_minutes` - Basic production time

**Maps to**:
- Calculates average rate per sqft from 3 banner prices
- Saves to: `category_defaults.banners.sell_rate_defaults.base_rate`

**Status**: ✅ **ACTIVE** - This is the guided setup wizard, keep it  
**Issue**: Does NOT map to new Banner Wizard structure yet (will be addressed in Phase 2A Step 2)

---

#### D. Hardcoded Banner Materials (PricingCalculator.js)
**File**: `/app/frontend/src/components/PricingCalculator.js` lines 67-75

```javascript
const PRINT_MATERIALS = [
  { id: 'banner_13oz', name: '13 oz Banner' },
  { id: 'banner_18oz', name: '18 oz Banner' },
  { id: 'vinyl_adhesive', name: 'Adhesive Vinyl' },
  { id: 'poster_paper', name: 'Poster Paper' },
  { id: 'canvas', name: 'Canvas' },
  { id: 'backlit', name: 'Backlit Film' },
  { id: 'perforated', name: 'Perforated Window Film' },
];
```

**Status**: ❌ **HARDCODED ARRAY** - Should pull from Materials Library where `category='banner_material'`  
**Action needed**: Phase 2A Step 2 - Update calculator to use Materials Library

---

#### E. Backend Banner Pricing Logic
**File**: `/app/backend/server.py` lines 2126-2536

**calculate_banners() function** uses:
- `cfg.default_banner_material_key`
- `cfg.default_laminate_key`
- `cfg.default_double_sided`
- `cfg.default_hems`
- `cfg.default_grommets`
- `cfg.default_pole_pockets`
- `cfg.grommet_cost_each`, `grommet_sell_each`, `grommet_minimum_charge`
- `cfg.standard_hem_rate_per_linear_foot`
- `cfg.reinforced_hem_rate_per_linear_foot`
- `cfg.pole_pocket_rate_per_linear_foot`
- Pulls material costs from Materials Library via `find_material()`

**Status**: ✅ **ACTIVE** - Backend already uses Category Rules → Banners config correctly

---

### **Missing Banner Wizard Fields**

Based on user requirements, these fields should exist in Banner category settings but are NOT yet implemented:

1. ❌ `pricing_method` - User should select: Price/Sq Ft, Detailed Material+Labor, Compare Methods, etc.
2. ❌ `default_retail_rate_per_sqft` - Simple retail rate method (alternative to detailed cost)
3. ❌ `setup_minutes` - Time to set up banner job
4. ❌ `production_minutes_per_sqft` - Alternative to hours (convert to hours in backend)
5. ❌ `addon_defaults` - Default finishing options (hems, grommets, pockets)
6. ❌ `product_templates` - Common banner templates (2x4, 3x6, 4x8, etc.)
7. ❌ `use_global_rush_rules` - Whether to use global or category-specific rush fees
8. ❌ `use_global_rounding_rules` - Whether to use global or category-specific rounding

**Note**: Some of these concepts exist (e.g., labor hours, finishing rates) but are not structured as a clean "Banner Wizard" configuration.

---

## 📊 COMPETING BANNER FIELDS ANALYSIS

### **Grommet/Hemming Duplication**

**Location 1** (Shop Defaults tab - WRONG):
- `banner_grommet_price_each` - Line 363
- `banner_hemming_tape_price_per_linear_inch` - Line 364

**Location 2** (Category Rules → Banners - CORRECT):
- `grommet_cost_each` - Line 1724
- `grommet_sell_each` - Line 1725
- `grommet_minimum_charge` - Line 1726
- `standard_hem_rate_per_linear_foot` - Line 1720
- `reinforced_hem_rate_per_linear_foot` - Line 1721

**Problem**: Two different field names for the same concepts!

**Decision**: 
- ✅ Keep Category Rules → Banners fields (more complete: cost + sell + minimum)
- ❌ Hide Shop Defaults grommet/hemming fields (they're global, which is wrong for banner-specific items)

---

### **Banner Material Source of Truth**

**Current state**:
- Materials Library has `category='banner_material'` (✅ Good)
- Category Rules → Banners has `default_banner_material_key` dropdown (✅ Good)
- PricingCalculator.js has hardcoded `PRINT_MATERIALS` array (❌ Bad)
- Backend `calculate_banners()` uses Materials Library (✅ Good)

**Problem**: Calculator UI shows hardcoded list, but backend uses Materials Library.

**Decision**: Phase 2A Step 2 will make calculator pull from Materials Library dynamically.

---

## ✅ PROPOSED BANNER SETTINGS STRUCTURE

### **Source of Truth Location**:
`settings.category_defaults.banners` (already exists, will be enhanced)

### **Enhanced Banner Category Settings**:

```javascript
category_defaults.banners = {
  // Pricing Method (NEW - to be added)
  pricing_method: "compare_methods", // or "price_per_sqft", "detailed_material_labor", etc.
  
  // Retail Rate Method (NEW - simple pricing)
  default_retail_rate_per_sqft: 0, // Simple retail rate if using price/sqft method
  
  // Material Defaults (EXISTING - keep)
  default_banner_material_key: "banner_13oz",
  default_laminate_key: "banner_laminate_coating",
  default_laminate_required: false,
  default_install_included: false,
  
  // Minimums (EXISTING - keep)
  default_minimum_billable_area: 0,
  default_minimum_sell_price: 0,
  
  // Labor & Time (EXISTING - keep, may add minute alternatives)
  default_design_time_hours: 0,
  production_labor_hours_per_sqft: 0,
  min_production_labor_hours_per_item: 0,
  install_hours_per_sqft: 0,
  install_base_hours: 0,
  
  // Optional: Minute-based alternatives (NEW)
  setup_minutes: 0,
  production_minutes_per_sqft: 0, // Convert to hours in backend
  
  // Waste (EXISTING - keep)
  waste_percentage: 0,
  
  // Finishing Rates (EXISTING - keep)
  standard_hem_rate_per_linear_foot: 0,
  reinforced_hem_rate_per_linear_foot: 0,
  pole_pocket_rate_per_linear_foot: 0,
  specialty_sewing_rate_per_linear_foot: 0,
  
  // Grommet Rates (EXISTING - keep)
  grommet_cost_each: 0,
  grommet_sell_each: 0,
  grommet_minimum_charge: 0,
  
  // Other Finishing (EXISTING - keep)
  reinforced_corners_charge: 0,
  wind_slit_charge: 0,
  
  // Default Finishing Options (EXISTING in backend, may expose in UI)
  default_hems: "standard", // standard, reinforced, none
  default_grommets: "corners", // corners, 24_inch, 18_inch, custom, none
  default_pole_pockets: "none", // top, top_bottom, none
  default_double_sided: "no", // yes, no
  
  // Addon Defaults (NEW - structured)
  addon_defaults: {
    hems: { included: true, type: "standard" },
    grommets: { included: true, type: "corners" },
    pole_pockets: { included: false, type: "none" },
    laminate: { included: false },
    double_sided: false,
  },
  
  // Product Templates (NEW - common sizes)
  product_templates: [
    { name: "2x4 Banner", width: 2, height: 4, sqft: 8 },
    { name: "3x6 Banner", width: 3, height: 6, sqft: 18 },
    { name: "4x8 Banner", width: 4, height: 8, sqft: 32 },
    { name: "Custom Size", width: 0, height: 0, sqft: 0 },
  ],
  
  // Global Rules (NEW)
  use_global_rush_rules: true,
  use_global_rounding_rules: true,
  
  // Sell Rate Defaults (EXISTING - keep, used by quiz)
  sell_rate_defaults: {
    base_rate: 0, // $/sqft retail rate (calculated by quiz or manual entry)
  },
};
```

### **Category Pricing Methods (Already exists from Phase 1)**:
```javascript
category_pricing_methods.banners = "compare_methods"
category_setup_status.banners = "basic_setup"
```

---

## 🎯 CLEANUP ACTIONS REQUIRED

### **Step 1: Hide Duplicate Fields from Shop Defaults Tab**

**File**: `/app/frontend/src/pages/PricingFoundation.js`

**Action**: Move grommet/hemming fields from Shop Defaults tab to HIDDEN_FIELDS or remove from ShopDefaultsTab component display.

**Fields to hide**:
- `banner_grommet_price_each`
- `banner_hemming_tape_price_per_linear_inch`

**Rationale**: These are banner-specific, not global shop defaults. The correct place is Category Rules → Banners.

---

### **Step 2: Add Missing Banner Wizard Fields**

**File**: `/app/frontend/src/pages/PricingFoundation.js` - CategoryRulesTab, Banners section

**Fields to add** (as optional/hidden until Banner Wizard is built):
- `pricing_method` (will be set by Category Methods tab)
- `default_retail_rate_per_sqft` (simple pricing alternative)
- `setup_minutes` (optional)
- `production_minutes_per_sqft` (optional alternative to hours)
- `addon_defaults` (structured object)
- `product_templates` (array of common sizes)
- `use_global_rush_rules` (boolean)
- `use_global_rounding_rules` (boolean)

**Note**: Many of these can remain backend-only until Banner Wizard UI is built in Step 2.

---

### **Step 3: Update HIDDEN_FIELDS List**

Add deprecated/duplicate banner fields to HIDDEN_FIELDS_LEVEL_1:

```javascript
const HIDDEN_FIELDS_LEVEL_1 = [
  // ... existing hidden fields
  'banner_grommet_price_each',        // Moved to category_defaults.banners
  'banner_hemming_tape_price_per_linear_inch', // Moved to category_defaults.banners
];
```

---

### **Step 4: Document Banner Settings Source of Truth**

**Add help text in UI** (Category Rules → Banners section):
```
💡 Banner Pricing Source of Truth:
- Materials: Select from Materials Library (banner_material category)
- Retail Rates: Set in Category Methods or use quiz-calculated base_rate
- Finishing Rates: Hems, grommets, pockets configured below
- Labor: Hours or minutes per sqft + base hours
- Add-ons: Default finishing options apply to all banner quotes
```

---

## 📋 MIGRATION PLAN

### **Fields Already Correct** (No migration needed):
✅ Material dropdowns already pull from Materials Library  
✅ Backend already uses category_defaults.banners correctly  
✅ Category Rules → Banners has all necessary fields  
✅ Quiz already maps to category_defaults.banners.sell_rate_defaults.base_rate  

### **Fields to Migrate**:
❌ None - The duplicate fields in Shop Defaults are not being used by backend; they just clutter the UI.

### **Fields to Hide**:
1. `banner_grommet_price_each` (Shop Defaults)
2. `banner_hemming_tape_price_per_linear_inch` (Shop Defaults)

---

## 🔧 IMPLEMENTATION STEPS

### **Phase 2A Step 1 Scope** (This cleanup):
1. ✅ Audit complete
2. Hide grommet/hemming from Shop Defaults tab
3. Add missing banner wizard fields to data model (backend-compatible)
4. Update help text to clarify Banner settings location
5. Test that existing banner calculator still works
6. Document source of truth

### **Phase 2A Step 2 Scope** (Next, will NOT do now):
- Build Banner Setup Wizard UI
- Implement pricing method selection UI
- Update PricingCalculator.js to pull banner materials from Materials Library
- Replace hardcoded PRINT_MATERIALS array
- Add product templates UI
- Add addon defaults UI

---

## ✅ VALIDATION CHECKLIST

After Step 1 cleanup:
- [ ] Shop Defaults tab does NOT show banner_grommet_price_each
- [ ] Shop Defaults tab does NOT show banner_hemming_tape_price_per_linear_inch
- [ ] Category Rules → Banners shows all banner-specific fields
- [ ] Materials Library has banner_material category
- [ ] Backend calculate_banners() still works with existing config
- [ ] Quiz still maps banner prices correctly
- [ ] No duplicate competing fields visible to user
- [ ] Help text clarifies Banner settings location

---

**Next Step**: Implement cleanup (hide duplicate fields, update help text, test)
