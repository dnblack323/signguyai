# Phase 1 Implementation Plan - Pricing Foundation Framework

**Status**: IN PROGRESS
**Created Components**: 2/10
**Estimated Completion**: 60% planning, 20% implementation

---

## ✅ COMPLETED

### 1. Shop Rate Quiz Component (`/app/frontend/src/components/pricing/ShopRateQuiz.js`)
- ✅ Multi-path setup (Quick Estimate, Detailed Business Numbers, I Already Know My Rate)
- ✅ Monthly overhead calculation with presets
- ✅ Billable hours calculation
- ✅ Labor cost & payroll burden (Average Wage or Total Payroll method)
- ✅ Profit/safety buffer with presets
- ✅ Rounding rules
- ✅ Result breakdown with warnings
- ✅ Calculates: overhead per hour, loaded labor cost, suggested shop rate
- ✅ Clear explanations and help text throughout

### 2. Category Pricing Method Setup Component (`/app/frontend/src/components/pricing/CategoryPricingMethodSetup.js`)
- ✅ 11 category cards (Banners, Yard Signs, Rigid Signs, Printed Vinyl, Cut Vinyl, Vehicle Lettering, Vehicle Wraps, Apparel, Design, Installation, Custom/Promotional)
- ✅ Method selection per category (Flat Price, Price Per Sq Ft, Quantity Tier, Detailed Material+Labor, Compare Methods, Manual Quote, Hourly, Package)
- ✅ Status tracking (Not Started, Basic Setup, Detailed Setup, Compare Ready, Needs Review)
- ✅ Setup and Test buttons for each category
- ✅ Suggested methods per category

---

## 🚧 REMAINING WORK

### 3. Materials Library Cleanup (PRIORITY 1)

**Current Issues**:
- Vague field labels (Cost, Rate, Price)
- No support for roll/sheet material calculations
- No clear distinction between shop cost and suggested charge
- Material categories need consolidation

**Required Changes**:

#### A. Update Material Data Model
File: Backend model or PricingFoundation.js material schema

```javascript
// New material purchase types
purchase_type: 'roll' | 'sheet' | 'each' | 'linear_ft' | 'sqft' | 'yard' | 'custom'

// For roll materials
roll_width: number
roll_width_unit: 'inches' | 'feet'
roll_length: number
roll_length_unit: 'feet' | 'yards'
roll_cost: number

// For sheet materials
sheet_width: number
sheet_height: number
sheet_cost: number

// Calculated fields
shop_cost_per_sqft: number (calculated)
waste_adjusted_cost_per_sqft: number (calculated)
markup_percent: number (optional)
suggested_material_charge_per_sqft: number (calculated if markup entered)
manual_material_charge_per_sqft: number (optional override)
```

#### B. Update Material UI Labels
File: `/app/frontend/src/pages/PricingFoundation.js` MaterialRow component

**Replace**:
- "Cost / Sq Ft" → "Shop Cost Per Sq Ft"
- "Cost / Unit" → "Shop Cost Each"
- "Sell Rate / Sq Ft" → "Suggested Material Charge Per Sq Ft" or "Manual Material Charge Per Sq Ft"
- Add calculated fields display
- Add roll/sheet input forms

#### C. Consolidate Material Categories
Update MATERIAL_CATEGORIES constant:

```javascript
const MATERIAL_CATEGORIES = [
  { value: 'banner_material', label: 'Banner Material' },
  { value: 'printable_vinyl', label: 'Printable Vinyl' },
  { value: 'laminate', label: 'Laminate' },
  { value: 'cut_vinyl', label: 'Cut Vinyl' },
  { value: 'transfer_tape', label: 'Transfer Tape' },
  { value: 'wrap_film', label: 'Wrap Film' },
  { value: 'coroplast', label: 'Coroplast' },
  { value: 'acm', label: 'ACM' },
  { value: 'pvc', label: 'PVC' },
  { value: 'acrylic', label: 'Acrylic' },
  { value: 'apparel_blank', label: 'Apparel Blank' },
  { value: 'hardware', label: 'Hardware' },
  { value: 'other', label: 'Other' },
];
```

#### D. Add Material Calculation Logic
```javascript
// Roll material calculation
const rollWidthFeet = roll_width_unit === 'inches' ? roll_width / 12 : roll_width;
const rollLengthFeet = roll_length_unit === 'yards' ? roll_length * 3 : roll_length;
const totalSqFt = rollWidthFeet * rollLengthFeet;
const shop_cost_per_sqft = roll_cost / totalSqFt;
const waste_adjusted_cost_per_sqft = shop_cost_per_sqft * (1 + waste_percent / 100);
const suggested_material_charge_per_sqft = markup_percent 
  ? waste_adjusted_cost_per_sqft * (1 + markup_percent / 100)
  : 0;
```

### 4. Complexity Multipliers UI (PRIORITY 2)

File: Create new tab in PricingFoundation.js or add to Global Rules

```javascript
const COMPLEXITY_MULTIPLIERS = {
  simple: 1.0,
  moderate: 1.25,
  complex: 1.5,
  nightmare: 2.0,
};
```

UI to show/edit these multipliers with explanation:
- "Complexity affects labor time, not material costs"
- "Used for: Cut vinyl weeding, install difficulty, vehicle graphics, design cleanup"

### 5. Global Rules UI (PRIORITY 2)

File: Update GlobalCalculationRulesTab in PricingFoundation.js

Add/clean up:
- **Minimum Order**: Already exists, keep
- **Rush Fees**: Add rush fee options (Standard 0%, Same Week, 48hr, 24hr, Same Day) with % or flat fee
- **Rounding Rules**: Already exists, keep (nearest $1, $5, $10, $25)
- **Deposit Percentage**: Already exists, keep

### 6. Category Setup Wizard Shell (PRIORITY 3)

File: Create `/app/frontend/src/components/pricing/CategorySetupWizard.js`

Reusable wizard component that takes `categoryId` prop and renders:
1. Pricing method selection
2. Default retail rate or pricing style inputs (placeholder for now)
3. Material selection (placeholder)
4. Labor time inputs (placeholder)
5. Minimum charge
6. Compare methods toggle
7. Complexity toggle

**For Phase 1**: Just create the shell structure, save method and status. Full implementation comes later per category.

### 7. Test/Compare Calculator Shell (PRIORITY 3)

File: Update ReviewTestingPanel in PricingFoundation.js or create new component

Add:
- Category selector dropdown
- Sample dimension/quantity inputs
- "Calculate" button
- Placeholder results display showing:
  - Selected pricing method
  - "Category not fully configured" warning if needed
  - Placeholder price breakdown structure

### 8. Integration into PricingFoundation.js (PRIORITY 1)

**Add new tabs**:
```javascript
const TAB_MODE_MAP = {
  // ... existing tabs
  shop_rate: { simple: true, advanced: true, audit: false },
  category_methods: { simple: true, advanced: true, audit: false },
  complexity: { simple: false, advanced: true, audit: false },
  // ... existing tabs
};
```

**Import new components**:
```javascript
import ShopRateQuiz from '../components/pricing/ShopRateQuiz';
import CategoryPricingMethodSetup from '../components/pricing/CategoryPricingMethodSetup';
```

**Add tab triggers and content**:
```javascript
<TabsTrigger value="shop_rate">Shop Rate</TabsTrigger>
<TabsTrigger value="category_methods">Category Methods</TabsTrigger>

<TabsContent value="shop_rate">
  <ShopRateQuiz
    open={shopRateQuizOpen}
    onClose={() => setShopRateQuizOpen(false)}
    onApply={(result) => {
      handleSettingsChange({ ...settings, ...result });
      setShopRateQuizOpen(false);
    }}
  />
  <div className="space-y-4">
    {settings?.shop_rate_quiz_completed && (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Current Shop Rate</CardTitle>
          <CardDescription>Calculated from your overhead, labor cost, and profit buffer</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <Label className="text-xs text-gray-500">Default Shop Rate</Label>
            <div className="text-lg font-semibold">${settings.default_shop_rate}/hr</div>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Production Rate</Label>
            <div className="text-lg font-semibold">${settings.production_hourly_rate}/hr</div>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Design Rate</Label>
            <div className="text-lg font-semibold">${settings.design_hourly_rate}/hr</div>
          </div>
          <div>
            <Label className="text-xs text-gray-500">Install Rate</Label>
            <div className="text-lg font-semibold">${settings.install_hourly_rate}/hr</div>
          </div>
        </CardContent>
      </Card>
    )}
    <Button onClick={() => setShopRateQuizOpen(true)}>
      {settings?.shop_rate_quiz_completed ? 'Recalculate' : 'Calculate'} Shop Rate
    </Button>
  </div>
</TabsContent>

<TabsContent value="category_methods">
  <CategoryPricingMethodSetup
    settings={settings}
    onChange={handleSettingsChange}
    onSetupCategory={(catId) => {
      // TODO: Open category setup wizard
      toast.info(`Setup wizard for ${catId} coming in next phase`);
    }}
    onTestCategory={(catId) => {
      // TODO: Open test calculator
      toast.info(`Test calculator for ${catId} coming in next phase`);
    }}
  />
</TabsContent>
```

### 9. Backend Data Storage (PRIORITY 1)

File: `/app/backend/server.py` or pricing models

Ensure backend can save/load:
```python
{
  "shop_rate_quiz_completed": bool,
  "shop_rate_quiz_method": str,  # "quick", "detailed", "known"
  "default_shop_rate": float,
  "production_hourly_rate": float,
  "design_hourly_rate": float,
  "install_hourly_rate": float,
  "monthly_overhead_total": float,
  "monthly_billable_hours": float,
  "overhead_per_billable_hour": float,
  "payroll_burden_percent": float,
  "labor_profit_buffer_per_hour": float,
  "loaded_labor_cost": float,
  
  "category_pricing_methods": {
    "banners": str,  # method name
    "yard_signs": str,
    # ... other categories
  },
  "category_setup_status": {
    "banners": str,  # status
    # ... other categories
  },
  
  "complexity_multipliers": {
    "simple": float,
    "moderate": float,
    "complex": float,
    "nightmare": float,
  },
  
  "rush_fee_options": {
    "same_week": {"type": "percent", "value": 10},
    "48_hour": {"type": "percent", "value": 20},
    "24_hour": {"type": "percent", "value": 35},
    "same_day": {"type": "flat", "value": 150},
  },
}
```

### 10. Clean Up Existing UI (PRIORITY 2)

File: `/app/frontend/src/pages/PricingFoundation.js`

**Hide/Remove from normal UI**:
- Already hidden fields in HIDDEN_FIELDS_LEVEL_1 ✅
- Additional confusing fields:
  - Duplicate markup fields (keep only one clear one)
  - Unused time estimate fields that don't affect calculations
  - Display-only material metadata unless in "Advanced" mode

**Add help text**:
- Explain shop cost vs suggested charge
- Explain when overhead is included (in shop rate) vs not double-counted
- Explain waste precedence

---

## IMPLEMENTATION SEQUENCE

### Phase 1A (Do First - Essential Framework):
1. ✅ Shop Rate Quiz component (DONE)
2. ✅ Category Pricing Method Setup component (DONE)
3. 🚧 Materials Library cleanup (labels, roll/sheet support, calculations)
4. 🚧 Integrate components into PricingFoundation.js
5. 🚧 Backend data model updates
6. 🚧 Test basic save/load

### Phase 1B (Do Next - Polish & Complete):
7. 🚧 Complexity Multipliers UI
8. 🚧 Global Rules cleanup (rush fees)
9. 🚧 Category Setup Wizard shell
10. 🚧 Test/Compare Calculator shell
11. 🚧 UI cleanup and help text
12. 🚧 Comprehensive testing

### Phase 2 (After Phase 1 Complete):
- Individual category implementations starting with Banners
- Detailed material + labor calculations per category
- Compare methods logic
- Calculator dropdown integration with Materials Library

---

## FILES TO MODIFY

### Created:
- ✅ `/app/frontend/src/components/pricing/ShopRateQuiz.js`
- ✅ `/app/frontend/src/components/pricing/CategoryPricingMethodSetup.js`

### To Create:
- `/app/frontend/src/components/pricing/CategorySetupWizard.js`
- `/app/frontend/src/components/pricing/ComplexityMultipliersSetup.js`
- `/app/frontend/src/components/pricing/TestCompareCalculator.js`

### To Modify:
- `/app/frontend/src/pages/PricingFoundation.js` (integrate new components, update tabs, add shop rate display)
- `/app/backend/server.py` or pricing model (add new fields to pricing_defaults)

---

## NEXT IMMEDIATE STEPS

1. **Materials Library Cleanup** - Most impactful change
   - Update material schema to support roll/sheet with calculations
   - Update UI labels (Shop Cost, Suggested Charge, Manual Charge)
   - Add roll and sheet input forms
   - Test material calculations

2. **Integration** - Make new components usable
   - Add Shop Rate tab to PricingFoundation
   - Add Category Methods tab to PricingFoundation
   - Wire up save/load from backend
   - Test end-to-end save

3. **Polish** - Complete the framework
   - Add Complexity Multipliers
   - Clean up Global Rules
   - Add wizard and calculator shells
   - Final testing

---

## USER TESTING CHECKLIST (from original requirements)

After completing Phase 1A + 1B, test:

1. ✅ Shop Rate Quiz opens
2. ✅ Shop Rate Quiz explains confusing terms clearly
3. ✅ Shop Rate Quiz offers presets
4. ✅ Shop Rate Quiz calculates overhead per billable hour
5. ✅ Shop Rate Quiz calculates suggested shop rate
6. ⏳ User can save shop rate
7. ⏳ Saved shop rate appears in Pricing Foundation
8. ⏳ Roll material calculates shop cost per sq ft
9. ⏳ Roll material calculates waste-adjusted cost
10. ⏳ Roll material calculates suggested charge if markup entered
11. ⏳ Sheet material calculations work
12. ⏳ Unit material calculations work
13. ⏳ Materials clearly show shop cost vs suggested charge
14. ⏳ Materials not mislabeled as "default retail sell price"
15. ✅ Category Pricing Method Setup shows category cards
16. ✅ User can choose pricing method per category
17. ⏳ Category setup status saves correctly
18. ⏳ Complexity multipliers save correctly
19. ⏳ Global rules save correctly
20. ⏳ Existing calculator page still loads
21. ⏳ No unrelated app modules changed

---

**Status Summary**: 
- ✅ 2 major components complete (Shop Rate Quiz, Category Method Setup)
- 🚧 8 remaining tasks for Phase 1 completion
- Estimated 60-70% of Phase 1 framework planning complete
- Need ~4-6 hours focused implementation time to complete Phase 1A
- Need additional 3-4 hours for Phase 1B polish

**Recommendation**: Focus next on Materials Library cleanup and integration, as those provide immediate user value and unblock category implementations.
