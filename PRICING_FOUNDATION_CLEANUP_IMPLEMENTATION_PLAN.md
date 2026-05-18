# Pricing Foundation Cleanup Implementation Plan

**Created:** 2026-05-18  
**Status:** PLANNING - Not Yet Implemented  
**Estimated Total Effort:** 8-12 hours across 6 phases

---

## Executive Summary

This plan outlines a safe, staged cleanup of the Pricing Foundation to:
1. Hide 22 fields that don't affect pricing (Level 1 UI cleanup)
2. Add realistic labor/design questions and fields (minutes-based)
3. Update calculator to use realistic labor times
4. Audit and clean up duplicate dropdown options
5. Update verification reports

**Key Safety Principles:**
- ✅ No backend field deletion
- ✅ No database schema changes
- ✅ No saved pricing data modification
- ✅ Backward compatibility maintained
- ✅ Staged implementation with testing between phases

---

## Phase 1: Hide Level 1 UI Fields (22 Fields)

### Fields to Hide from Main Pricing Foundation UI

#### Category: Unused Labor Rates (4 fields)

| # | Field Name | Current Location | Backend? | Frontend? | Affects Price? | How to Hide |
|---|------------|------------------|----------|-----------|----------------|-------------|
| 1 | `admin_hourly_rate` | PricingFoundation.js line 191 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 2 | `removal_hourly_rate` | PricingFoundation.js line 189 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 3 | `travel_hourly_rate` | PricingFoundation.js line 190 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 4 | `project_handling_hourly_rate` | PricingFoundation.js line 192 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |

**Details:**
- All in "Labor Rates" card
- Lines 189-192 in ShopDefaultsTab
- Keep: `production_hourly_rate`, `design_hourly_rate`, `install_hourly_rate`
- Hide: The 4 unused rates above

#### Category: Minimum Charges Not Enforced (8 fields)

| # | Field Name | Current Location | Backend? | Frontend? | Affects Price? | How to Hide |
|---|------------|------------------|----------|-----------|----------------|-------------|
| 5 | `minimum_design_charge` | PricingFoundation.js line 221 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 6 | `minimum_install_charge` | PricingFoundation.js line 222 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 7 | `minimum_removal_charge` | PricingFoundation.js line 223 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 8 | `minimum_vinyl_charge` | PricingFoundation.js line 224 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 9 | `minimum_print_charge` | PricingFoundation.js line 225 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 10 | `minimum_sign_charge` | PricingFoundation.js line 226 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 11 | `minimum_service_charge` | PricingFoundation.js line 227 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 12 | `minimum_wrap_charge` | PricingFoundation.js line 228 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |

**Details:**
- All in "Minimum Charges" card
- Lines 221-228 in ShopDefaultsTab
- Keep: `minimum_order` (actively used)
- Hide: The 8 unused minimum charges above
- Note: These are stored but never enforced as price floors in calculator

#### Category: Setup Fees Not Used (6 fields)

| # | Field Name | Current Location | Backend? | Frontend? | Affects Price? | How to Hide |
|---|------------|------------------|----------|-----------|----------------|-------------|
| 13 | `setup_fee_vinyl` | PricingFoundation.js line 239 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 14 | `setup_fee_print` | PricingFoundation.js line 240 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 15 | `setup_fee_apparel_screen` | PricingFoundation.js line 241 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 16 | `setup_fee_apparel_dtf` | PricingFoundation.js line 242 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 17 | `setup_fee_default` | PricingFoundation.js line 237 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 18 | `file_cleanup_fee_default` | PricingFoundation.js line 238 | ✅ Yes | ✅ Yes | ❌ No | Conditional render |

**Details:**
- All in "Rush, Setup, Rounding & Deposit" card
- Lines 237-242 in ShopDefaultsTab
- Note: Setup fees are stored but not applied in pricing calculations

#### Category: AI Fallback Settings (2 fields)

| # | Field Name | Current Location | Backend? | Frontend? | Affects Price? | How to Hide |
|---|------------|------------------|----------|-----------|----------------|-------------|
| 19 | `ai_fallback_behavior` | PricingFoundation.js (AI Rules section) | ✅ Yes | ✅ Yes | ❌ No | Conditional render |
| 20 | `ai_fallback_warnings_enabled` | PricingFoundation.js (AI Rules section) | ✅ Yes | ✅ Yes | ❌ No | Conditional render |

**Details:**
- In AI/Automation settings section
- These control UI warnings, not pricing

#### Category: Promotional Minimums (2 fields)

| # | Field Name | Current Location | Backend? | Frontend? | Affects Price? | How to Hide |
|---|------------|------------------|----------|-----------|----------------|-------------|
| 21 | `category_defaults.promotional.minimum_setup_fee` | DynamicCategoryFields component | ✅ Yes | ✅ Yes | ❌ No | Skip rendering |
| 22 | `category_defaults.promotional.minimum_charge` | DynamicCategoryFields component | ✅ Yes | ✅ Yes | ❌ No | Skip rendering |

**Details:**
- In category-specific defaults
- Need to check DynamicCategoryFields.js component

### Implementation Approach for Phase 1

**Step 1:** Add constant array at top of PricingFoundation.js (✅ Already done):
```javascript
const HIDDEN_FIELDS_LEVEL_1 = [
  'admin_hourly_rate', 'removal_hourly_rate', 'travel_hourly_rate', 
  'project_handling_hourly_rate', 'minimum_design_charge', 
  'minimum_install_charge', 'minimum_removal_charge', 'minimum_vinyl_charge',
  'minimum_print_charge', 'minimum_sign_charge', 'minimum_service_charge',
  'minimum_wrap_charge', 'setup_fee_vinyl', 'setup_fee_print',
  'setup_fee_apparel_screen', 'setup_fee_apparel_dtf', 'setup_fee_default',
  'file_cleanup_fee_default', 'ai_fallback_behavior', 'ai_fallback_warnings_enabled',
];
```

**Step 2:** Wrap each field Row with conditional:
```javascript
{!isFieldHidden('admin_hourly_rate') && (
  <Row label="Admin Rate" field="admin_hourly_rate" suffix="/hr" hint="Admin / office labor" />
)}
```

**Step 3:** Test that:
- Hidden fields no longer appear in UI
- Hidden fields still save/load from backend
- No errors when loading existing pricing configs

**Files to Modify:**
1. `/app/frontend/src/pages/PricingFoundation.js` - Main UI (22 conditional wraps)
2. `/app/frontend/src/components/DynamicCategoryFields.js` - Category defaults (2 fields)

**Estimated Effort:** 2-3 hours

---

## Phase 2: Add Labor/Design Quiz Questions

### New Quiz Questions to Add

#### Global Labor/Design Questions (7 questions)

| # | Question | Input Type | Maps To | Default | Validation |
|---|----------|------------|---------|---------|------------|
| 1 | What is your normal shop labor rate per hour? | Number ($/hr) | `labor.shop_labor_rate` | 75 | 15-300 |
| 2 | What is your normal design/artwork rate per hour? | Number ($/hr) | `design.default_design_rate` | 85 | 15-300 |
| 3 | Do you charge separately for design/artwork? | Yes/No | `design.charge_design_separately` | Yes | — |
| 4 | How many minutes of basic design are included before extra design charges apply? | Number (mins) | `design.included_design_minutes` | 30 | 0-240 |
| 5 | What is your minimum design charge when design is billed separately? | Number ($) | `design.minimum_design_charge` | 75 | 0-500 |
| 6 | Do you charge installation separately from production? | Yes/No | `install.charge_install_separately` | Yes | — |
| 7 | What is your install labor rate per hour? | Number ($/hr) | `install.install_labor_rate` | 95 | 15-300 |

#### Category-Specific Labor Questions

**Banners (5 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Basic banner setup/print minutes | `category_defaults.banners.labor.setup_minutes` | 15 | minutes |
| 2 | Banner trim/finish minutes | `category_defaults.banners.labor.finishing_minutes` | 10 | minutes |
| 3 | Grommet/hemming minutes (if needed) | `category_defaults.banners.labor.grommet_hemming_minutes` | 5 | minutes per item |
| 4 | Included banner design minutes | `category_defaults.banners.design.included_minutes` | 20 | minutes |
| 5 | Charge extra for banner design? | `category_defaults.banners.design.charge_separately` | No | boolean |

**Rigid Signs (5 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Basic rigid sign setup/production minutes | `category_defaults.rigid_signs.labor.setup_minutes` | 20 | minutes |
| 2 | Vinyl application/print prep minutes | `category_defaults.rigid_signs.labor.vinyl_app_minutes` | 15 | minutes |
| 3 | Cutting/drilling/special finishing minutes | `category_defaults.rigid_signs.labor.special_finishing_minutes` | 10 | minutes |
| 4 | Included design minutes | `category_defaults.rigid_signs.design.included_minutes` | 20 | minutes |
| 5 | Charge extra for rigid sign design? | `category_defaults.rigid_signs.design.charge_separately` | No | boolean |

**Yard Signs (5 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Batch setup minutes (one-time per order) | `category_defaults.rigid_signs.labor.yard_sign_batch_setup_minutes` | 15 | minutes |
| 2 | Production minutes per yard sign | `category_defaults.rigid_signs.labor.yard_sign_minutes_per_unit` | 3 | minutes per sign |
| 3 | Stakes included? | `category_defaults.rigid_signs.yard_sign_stakes_included` | No | boolean |
| 4 | Included design minutes | `category_defaults.rigid_signs.design.yard_sign_included_minutes` | 15 | minutes |
| 5 | Charge extra for yard sign design? | `category_defaults.rigid_signs.design.yard_sign_charge_separately` | No | boolean |

**Cut Vinyl (5 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Basic setup/weeding minutes | `category_defaults.cut_vinyl.labor.setup_weeding_minutes` | 20 | minutes |
| 2 | Extra minutes for complex weeding | `category_defaults.cut_vinyl.labor.complex_weeding_addon_minutes` | 15 | minutes |
| 3 | Extra minutes for multi-color layering | `category_defaults.cut_vinyl.labor.multi_color_addon_minutes` | 10 | minutes per color |
| 4 | Included design minutes | `category_defaults.cut_vinyl.design.included_minutes` | 20 | minutes |
| 5 | Charge extra for cut vinyl design? | `category_defaults.cut_vinyl.design.charge_separately` | No | boolean |

**Digital Print (5 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Basic setup/printing minutes | `category_defaults.digital_print.labor.setup_print_minutes` | 15 | minutes |
| 2 | Laminating/cutting minutes | `category_defaults.digital_print.labor.laminate_cut_minutes` | 10 | minutes |
| 3 | Extra contour cut minutes | `category_defaults.digital_print.labor.contour_cut_addon_minutes` | 5 | minutes |
| 4 | Included design minutes | `category_defaults.digital_print.design.included_minutes` | 20 | minutes |
| 5 | Charge extra for decal design? | `category_defaults.digital_print.design.charge_separately` | No | boolean |

**Vehicle Graphics / Wraps (6 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Vehicle lettering setup minutes | `category_defaults.vehicle_graphics.labor.lettering_setup_minutes` | 30 | minutes |
| 2 | Partial wrap setup/prep minutes | `category_defaults.vehicle_graphics.labor.partial_wrap_setup_minutes` | 120 | minutes |
| 3 | Full wrap setup/prep minutes | `category_defaults.vehicle_graphics.labor.full_wrap_setup_minutes` | 240 | minutes |
| 4 | Install minutes per square foot | `category_defaults.vehicle_graphics.labor.install_minutes_per_sqft` | 3 | minutes per sqft |
| 5 | Charge wrap design separately? | `category_defaults.vehicle_graphics.design.charge_separately` | Yes | boolean |
| 6 | Included wrap design minutes | `category_defaults.vehicle_graphics.design.included_minutes` | 60 | minutes |

**Apparel (5 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Setup minutes per apparel order | `category_defaults.apparel.labor.setup_minutes_per_order` | 30 | minutes |
| 2 | Production minutes per item (one side) | `category_defaults.apparel.labor.minutes_per_item_one_side` | 2 | minutes per item |
| 3 | Extra minutes for second side | `category_defaults.apparel.labor.second_side_addon_minutes` | 1 | minutes per item |
| 4 | Extra minutes for names/numbers/personalization | `category_defaults.apparel.labor.personalization_addon_minutes` | 3 | minutes per item |
| 5 | Charge apparel artwork/setup separately? | `category_defaults.apparel.design.charge_separately` | Yes | boolean |

**Promotional Items (2 questions):**

| # | Question | Maps To | Default | Unit |
|---|----------|---------|---------|------|
| 1 | Setup/admin minutes per promotional order | `category_defaults.promotional.labor.setup_admin_minutes` | 45 | minutes |
| 2 | Charge artwork/setup separately? | `category_defaults.promotional.design.charge_separately` | Yes | boolean |

**Total New Quiz Questions:** 7 global + 43 category-specific = **50 new questions**

### Quiz Implementation Details

**File to Modify:** `/app/frontend/src/components/pricing/PricingSetupQuiz.js`

**New Section to Add:** "Labor & Design Times"

**Structure:**
```javascript
{
  key: 'labor_design',
  title: 'Labor & Design Times',
  questions: [
    { key: 'shop_labor_rate', label: 'Shop labor rate', prefix: '$', suffix: '/hr', default: 75 },
    { key: 'default_design_rate', label: 'Design/artwork rate', prefix: '$', suffix: '/hr', default: 85 },
    { key: 'charge_design_separately', label: 'Charge design separately?', type: 'bool', default: true },
    // ... rest of questions
  ],
},
```

**buildSuggestions Update:**
Need to add mapping logic for all 50 new questions.

**Estimated Effort:** 4-6 hours

---

## Phase 3: Update Calculator Logic

### Design Charge Logic Changes

**File:** `/app/backend/routes/pricing.py` or calculation handler

**Current Behavior:** Design is lumped into production labor

**New Behavior:**

```python
def calculate_design_charge(
    design_minutes: float,
    included_design_minutes: float,
    design_rate_per_hour: float,
    minimum_design_charge: float,
    charge_design_separately: bool
) -> float:
    """
    Calculate design charge based on new rules.
    
    Returns:
        Design charge to add to customer price (0 if not charging separately)
    """
    if not charge_design_separately:
        return 0.0  # Track internally but don't charge customer
    
    # Only charge after included minutes
    billable_minutes = max(0, design_minutes - included_design_minutes)
    
    if billable_minutes == 0:
        return 0.0
    
    calculated_charge = (billable_minutes / 60) * design_rate_per_hour
    
    # Apply minimum if configured
    if minimum_design_charge > 0:
        return max(minimum_design_charge, calculated_charge)
    
    return calculated_charge
```

### Labor Charge Logic Changes

**File:** `/app/backend/routes/pricing.py` or calculation handler

**Current Behavior:** Uses hours-based estimates (often unrealistic)

**New Behavior:**

```python
def calculate_labor_charge(
    category: str,
    quantity: int,
    sqft: float,
    pricing_config: dict,
    track_labor_only: bool = False
) -> dict:
    """
    Calculate labor charge based on category-specific minutes.
    
    Returns:
        {
            'labor_minutes': float,
            'labor_cost': float,  # Internal cost
            'labor_charge': float,  # Customer charge (0 if track_labor_only)
        }
    """
    category_labor = pricing_config.get('category_defaults', {}).get(category, {}).get('labor', {})
    shop_labor_rate = pricing_config.get('labor', {}).get('shop_labor_rate', 75)
    
    # Get category-specific minutes
    if category == 'banners':
        minutes = (
            category_labor.get('setup_minutes', 15) +
            category_labor.get('finishing_minutes', 10)
        )
    elif category == 'rigid_signs':
        # Check if yard sign
        is_yard_sign = pricing_config.get('is_yard_sign', False)
        if is_yard_sign:
            minutes = (
                category_labor.get('yard_sign_batch_setup_minutes', 15) +
                (quantity * category_labor.get('yard_sign_minutes_per_unit', 3))
            )
        else:
            minutes = (
                category_labor.get('setup_minutes', 20) +
                category_labor.get('vinyl_app_minutes', 15) +
                category_labor.get('special_finishing_minutes', 0)
            )
    # ... other categories
    
    labor_cost = (minutes / 60) * shop_labor_rate
    labor_charge = 0 if track_labor_only else labor_cost
    
    return {
        'labor_minutes': minutes,
        'labor_cost': labor_cost,
        'labor_charge': labor_charge,
    }
```

### Backend Model Changes

**File:** `/app/backend/models/pricing.py`

**Add New Fields to PricingDefaults:**

```python
# Labor configuration
labor: Dict[str, Any] = Field(default_factory=lambda: {
    "shop_labor_rate": 75.0,
    "track_labor_only": False,  # If true, labor doesn't add to customer price
})

# Design configuration
design: Dict[str, Any] = Field(default_factory=lambda: {
    "default_design_rate": 85.0,
    "charge_design_separately": True,
    "included_design_minutes": 30.0,
    "minimum_design_charge": 75.0,
})

# Install configuration
install: Dict[str, Any] = Field(default_factory=lambda: {
    "charge_install_separately": True,
    "install_labor_rate": 95.0,
})
```

**Add Labor/Design to Category Defaults:**

```python
# Example for banners
"banners": {
    "labor": {
        "setup_minutes": 15.0,
        "finishing_minutes": 10.0,
        "grommet_hemming_minutes": 5.0,
    },
    "design": {
        "included_minutes": 20.0,
        "charge_separately": False,
    },
    # ... existing sell_rate_defaults, etc.
}
```

**Estimated Effort:** 3-4 hours

---

## Phase 4: Dropdown Duplicate Audit

### Dropdowns to Audit

| # | Component/Location | Dropdown Field | Purpose |
|---|--------------------|----------------|---------|
| 1 | Order item form | Substrate type | Rigid sign substrates |
| 2 | Order item form | Print material | Banner materials |
| 3 | Order item form | Vinyl type | Cut vinyl types |
| 4 | Order item form | Laminate type | Lamination options |
| 5 | Order item form | Wrap material | Vehicle wrap materials |
| 6 | Pricing calculator | Substrate selector | Material selection |
| 7 | Pricing calculator | Vinyl selector | Vinyl selection |
| 8 | Pricing Foundation | Material category filter | Material management |
| 9 | Wrap Command Center | Wrap material dropdown | Wrap project materials |
| 10 | DynamicCategoryFields | Install complexity | Complexity levels |
| 11 | DynamicCategoryFields | Design complexity | Design difficulty |
| 12 | Order form | Item category | Job type selection |

### Known Duplicates to Check

**Substrate Types:**
- "Coroplast" vs "Corrugated Plastic" vs "Coro"
- "ACM" vs "Aluminum Composite" vs "Alumapanel" vs "Dibond"
- "PVC" vs "Sintra" vs "Expanded PVC"
- "Foam Board" vs "Foam Core" vs "Gator Board"

**Banner Materials:**
- "13oz Banner" vs "13 oz Banner Vinyl" vs "Banner Vinyl 13oz"
- "18oz Banner" vs "18 oz Banner Vinyl" vs "Heavy Banner"
- "Mesh Banner" vs "Mesh Vinyl" vs "Perforated Banner"

**Vinyl Types:**
- "Cast Vinyl" vs "Cast Wrap Vinyl" vs "Wrap Vinyl"
- "Calendered Vinyl" vs "Calendared Vinyl" vs "Standard Vinyl"
- "Reflective Vinyl" vs "Reflective Sheeting"

**Laminate Types:**
- "Gloss Laminate" vs "Cast Gloss Laminate" vs "Wrap Laminate Gloss"
- "Matte Laminate" vs "Matte Finish" vs "Non-Glare Laminate"
- "Luster Laminate" vs "Satin Laminate" vs "Semi-Gloss"

### Audit Approach

**Step 1:** Extract all unique dropdown options from code

```javascript
// Search for SelectItem components
grep -r "SelectItem" /app/frontend/src --include="*.js" --include="*.jsx"

// Extract material type options
grep -r "substrate\|vinyl\|laminate\|banner" /app/frontend/src/components
```

**Step 2:** Create mapping of canonical → aliases

```javascript
const CANONICAL_MATERIAL_NAMES = {
  // Substrates
  'Coroplast': ['Corrugated Plastic', 'Coro', 'Coroplast'],
  'ACM / Aluminum Composite': ['ACM', 'Aluminum Composite', 'Alumapanel', 'Dibond'],
  'PVC': ['PVC', 'Sintra', 'Expanded PVC'],
  'Foam Board': ['Foam Board', 'Foam Core', 'Gator Board'],
  
  // Banner
  '13 oz Banner': ['13oz Banner', '13 oz Banner Vinyl', 'Banner Vinyl 13oz'],
  '18 oz Banner': ['18oz Banner', '18 oz Banner Vinyl', 'Heavy Banner'],
  
  // Vinyl
  'Cast Vinyl': ['Cast Vinyl', 'Cast Wrap Vinyl', 'Wrap Vinyl'],
  'Calendered Vinyl': ['Calendered Vinyl', 'Calendared Vinyl', 'Standard Vinyl'],
  
  // Laminate
  'Gloss Laminate': ['Gloss Laminate', 'Cast Gloss Laminate', 'Wrap Laminate Gloss'],
  'Matte Laminate': ['Matte Laminate', 'Matte Finish', 'Non-Glare Laminate'],
};
```

**Step 3:** Generate duplicate audit report

**Output:**
- `/app/DROPDOWN_DUPLICATE_AUDIT_REPORT.md`
- List of exact duplicates
- List of near duplicates (need review)
- Recommended canonical names
- Alias mapping for backward compatibility

**Estimated Effort:** 2-3 hours

---

## Phase 5: Safe Dropdown Cleanup

### Cleanup Strategy

**Only remove EXACT duplicates:**
- Same meaning, different capitalization
- Same meaning, different punctuation
- Obvious typos

**Leave for manual review:**
- Different brands (ACM vs Dibond)
- Different quality tiers
- Different sizes/thicknesses

### Implementation Approach

**Step 1:** Update dropdown constants to use canonical names

```javascript
// Before
const SUBSTRATE_TYPES = [
  { value: 'coroplast', label: 'Coroplast' },
  { value: 'coro', label: 'Coro' },  // DUPLICATE
  { value: 'corrugated_plastic', label: 'Corrugated Plastic' },  // DUPLICATE
];

// After
const SUBSTRATE_TYPES = [
  { value: 'coroplast', label: 'Coroplast' },
  // Removed duplicates
];
```

**Step 2:** Add alias resolver for saved records

```javascript
const MATERIAL_ALIAS_MAP = {
  'coro': 'coroplast',
  'corrugated_plastic': 'coroplast',
  'acm': 'aluminum_composite',
  'dibond': 'aluminum_composite',
  'sintra': 'pvc',
  // ... etc
};

function resolveMaterialAlias(value) {
  return MATERIAL_ALIAS_MAP[value] || value;
}
```

**Step 3:** Update display logic to show canonical name

```javascript
function getMaterialDisplayName(savedValue) {
  const canonical = resolveMaterialAlias(savedValue);
  return CANONICAL_NAMES[canonical] || savedValue;
}
```

**Files to Update:**
1. Order form components (material selectors)
2. Pricing calculator (material dropdowns)
3. Pricing Foundation (material list)
4. Wrap Command Center (wrap materials)

**Safety Checks:**
- ✅ Alias resolver handles old values
- ✅ Saved orders still display correctly
- ✅ No data migration required
- ✅ Backend remains unchanged

**Estimated Effort:** 2-3 hours

---

## Phase 6: Update Verification Reports

### Quiz Mapping Verification Update

**File:** `/app/backend/quiz_mapping_verification.py`

**Changes Needed:**
1. Add 50 new quiz questions to QUIZ_SECTIONS
2. Add 50 new mappings to ANSWER_TO_FOUNDATION_MAP
3. Add new fields to ACTIVELY_USED_FIELDS
4. Update field paths for labor/design

**Run Updated Verification:**
```bash
cd /app/backend && python quiz_mapping_verification.py
```

**Expected Results:**
- 98 total questions (48 old + 50 new)
- 95+ successfully mapped
- 3 intentionally unmapped (booleans)
- 0 unknown fields

### Field Usage Audit Update

**File:** `/app/backend/pricing_foundation_field_usage_audit.py`

**Changes Needed:**
1. Add new labor/design fields to schema
2. Mark 22 hidden fields as "Hidden from UI"
3. Update classification logic
4. Add "affects_customer_price" flag

**Run Updated Audit:**
```bash
cd /app/backend && python pricing_foundation_field_usage_audit.py
```

**Expected Results:**
- Total fields: 150+ (103 old + 50+ new)
- Actively used: 70+
- Hidden from UI: 22
- Stored/Display: 25

**Estimated Effort:** 2 hours

---

## Implementation Order & Timeline

### Recommended Sequence

| Phase | Task | Effort | Risk | Dependencies |
|-------|------|--------|------|--------------|
| **1** | Hide 22 Level 1 fields from UI | 2-3h | 🟢 Low | None |
| **2** | Add 50 labor/design quiz questions | 4-6h | 🟡 Medium | Phase 1 |
| **3** | Update calculator labor/design logic | 3-4h | 🟡 Medium | Phase 2 |
| **4** | Audit dropdown duplicates | 2-3h | 🟢 Low | None (parallel) |
| **5** | Clean up exact duplicate dropdowns | 2-3h | 🟢 Low | Phase 4 |
| **6** | Update verification reports | 2h | 🟢 Low | Phases 1-3 |

**Total Estimated Time:** 15-21 hours

**Risk Legend:**
- 🟢 Low Risk: No calculator changes, UI only
- 🟡 Medium Risk: Calculator logic changes, needs thorough testing
- 🔴 High Risk: Database changes (none in this plan)

---

## Testing Checklist

### Phase 1 Testing (Hide Fields)

- [ ] Pricing Foundation page loads without errors
- [ ] 22 hidden fields no longer appear in main UI
- [ ] Remaining visible fields still work
- [ ] Can save and load pricing configuration
- [ ] Hidden field values still saved to backend
- [ ] No console errors
- [ ] Quiz still loads
- [ ] Existing orders still load

### Phase 2 Testing (New Quiz Questions)

- [ ] Quiz displays new "Labor & Design Times" section
- [ ] All 50 new questions render correctly
- [ ] Default values populate
- [ ] Validation works (min/max ranges)
- [ ] Boolean toggles work
- [ ] Quiz submission doesn't error
- [ ] buildSuggestions creates correct mappings
- [ ] Preview shows suggested values

### Phase 3 Testing (Calculator Logic)

**Design Charge Tests:**
- [ ] Design charge = 0 when charge_design_separately = false
- [ ] Design charge only applies after included minutes
- [ ] Minimum design charge enforced when configured
- [ ] Design tracked internally even when not charged

**Labor Charge Tests:**
- [ ] Simple banner uses minutes (not hours)
- [ ] Yard sign uses quantity-based minutes
- [ ] Rigid sign uses setup + finishing minutes
- [ ] Labor = 0 when track_labor_only = true
- [ ] Labor minutes tracked for reporting

**Before/After Pricing:**
- [ ] 4×8 banner: Old (4 hrs = $300 labor) → New (25 mins = $31 labor)
- [ ] Basic rigid sign: Old (3 hrs = $225) → New (45 mins = $56)
- [ ] 25 yard signs: Old (75 hrs = $1875) → New (90 mins = $113)

### Phase 4 Testing (Dropdown Audit)

- [ ] Audit script runs without errors
- [ ] Report generated with duplicate findings
- [ ] Exact duplicates identified correctly
- [ ] Near duplicates flagged for review
- [ ] Canonical names recommended

### Phase 5 Testing (Dropdown Cleanup)

- [ ] Dropdown options show canonical names only
- [ ] No exact duplicates remain
- [ ] Alias resolver works for old values
- [ ] Saved orders still display correctly
- [ ] New orders use canonical values
- [ ] Wrap Command Center materials work
- [ ] Pricing calculator materials work

### Phase 6 Testing (Verification)

- [ ] Quiz verification passes
- [ ] Field usage audit completes
- [ ] New fields classified correctly
- [ ] Hidden fields marked correctly
- [ ] Reports generate without errors

---

## Risks & Decisions Needed

### Decision Points

**1. Design Charging Default**
- ❓ Should `charge_design_separately` default to `true` or `false`?
- 🤔 Recommendation: Default to `true` (most shops charge separately)
- Impact: Affects all categories

**2. Included Design Minutes**
- ❓ What should default included minutes be per category?
- 🤔 Recommendation: 15-30 minutes depending on complexity
- Impact: Affects when design charges apply

**3. Track Labor Only Mode**
- ❓ Should there be a global "track but don't charge labor" toggle?
- 🤔 Recommendation: Yes, useful for shops with flat pricing
- Impact: Labor tracked but not added to customer price

**4. Dropdown Cleanup Aggressiveness**
- ❓ Should we clean up near-duplicates or only exact matches?
- 🤔 Recommendation: Only exact matches in Phase 5, leave near-duplicates
- Impact: Safety vs. thoroughness tradeoff

**5. Quiz Question Organization**
- ❓ Should labor/design questions be in one section or split by category?
- 🤔 Recommendation: Split into Global + per-category subsections
- Impact: Quiz length and user experience

### Known Risks

**Risk 1: Calculator Behavior Change**
- **What:** Labor calculations will produce different results
- **Impact:** 🟡 Medium - Quotes may be lower (more realistic)
- **Mitigation:** Test with real-world examples, document changes
- **Rollback:** Revert calculator logic, keep new fields dormant

**Risk 2: Quiz Too Long**
- **What:** 50 new questions makes quiz very long
- **Impact:** 🟡 Medium - User fatigue
- **Mitigation:** Make most questions optional, use good defaults
- **Alternative:** Split into "Quick Setup" vs "Advanced Setup"

**Risk 3: Backward Compatibility**
- **What:** Old pricing configs missing new labor/design fields
- **Impact:** 🟢 Low - Defaults will be used
- **Mitigation:** Provide sensible defaults in backend model
- **Rollback:** Not needed (additive changes only)

**Risk 4: Dropdown Aliases Not Comprehensive**
- **What:** Some old material values not mapped to canonical names
- **Impact:** 🟢 Low - Will display old value as-is
- **Mitigation:** Comprehensive alias mapping, fallback to original
- **Rollback:** Not needed (only affects display)

---

## Smallest Safe Next Step

### Recommended: Phase 1 Only

**What:** Hide 22 Level 1 fields from Pricing Foundation UI

**Why:**
- ✅ Lowest risk (UI changes only)
- ✅ Immediate benefit (cleaner UI)
- ✅ No calculator changes
- ✅ No backend changes
- ✅ Easy to test
- ✅ Easy to rollback (remove conditional)

**Estimated Time:** 2-3 hours

**Files Changed:** 2 files
1. `/app/frontend/src/pages/PricingFoundation.js` (~25 lines)
2. `/app/frontend/src/components/DynamicCategoryFields.js` (~5 lines)

**Testing Required:**
- Load Pricing Foundation page
- Verify 22 fields hidden
- Verify visible fields still work
- Save and reload configuration
- Check no console errors

**Rollback Plan:**
- Remove conditional rendering
- All fields visible again
- No data loss

**Approval Needed:**
1. ✅ Confirm list of 22 fields to hide
2. ✅ Confirm they should remain in backend
3. ✅ Confirm no Level 2/3 yet

---

## Files That Will Be Modified (All Phases)

### Phase 1 (2 files)
- `/app/frontend/src/pages/PricingFoundation.js`
- `/app/frontend/src/components/DynamicCategoryFields.js`

### Phase 2 (1 file)
- `/app/frontend/src/components/pricing/PricingSetupQuiz.js`

### Phase 3 (3 files)
- `/app/backend/routes/pricing.py`
- `/app/backend/models/pricing.py`
- `/app/backend/routes/job_tickets.py` (if calculator logic there)

### Phase 4 (1 new file)
- `/app/backend/dropdown_duplicate_audit.py` (new script)

### Phase 5 (5-8 files)
- Order form components (material selectors)
- Pricing calculator components
- Wrap Command Center components
- Constant/config files with dropdown options

### Phase 6 (2 files)
- `/app/backend/quiz_mapping_verification.py`
- `/app/backend/pricing_foundation_field_usage_audit.py`

**Total Files Across All Phases:** 14-17 files

**Phase 1 Only:** 2 files

---

## Summary & Recommendation

**Plan Status:** ✅ Complete and ready for review

**Total Scope:**
- 22 fields to hide
- 50 new quiz questions
- 50+ new pricing foundation fields
- Calculator labor/design logic updates
- Dropdown duplicate cleanup
- Verification report updates

**Recommended Approach:**
1. ✅ Review and approve this plan
2. ✅ Start with Phase 1 only (smallest safe step)
3. ✅ Test Phase 1 thoroughly
4. ✅ Get user feedback on hidden fields
5. ✅ Proceed to Phase 2 if Phase 1 successful

**Next Action:**
Await your approval to proceed with **Phase 1 only** (hide 22 fields from UI).

---

## Approval Checklist

Before proceeding with implementation, confirm:

- [ ] Agree with list of 22 fields to hide
- [ ] Agree they should remain in backend for compatibility
- [ ] Agree with Phase 1 implementation approach
- [ ] Agree to defer Phases 2-6 until Phase 1 is tested
- [ ] Approve 2-3 hour time estimate for Phase 1
- [ ] Ready to proceed with Phase 1 implementation

---

**Plan Created:** 2026-05-18  
**Status:** Awaiting Approval  
**Next Step:** Implement Phase 1 (hide 22 fields) upon approval
