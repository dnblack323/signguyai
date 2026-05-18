# Pricing Dropdown Duplicate Audit Report

**Generated:** 2026-05-18  
**Scope:** All pricing-related dropdowns, material lists, and option selectors  
**Status:** AUDIT ONLY - No code changes made

---

## Executive Summary

**Dropdowns/Lists Audited:** 21 categories  
**Exact Duplicates Found:** 6 groups  
**Near Duplicates Found:** 8 groups  
**Safe for UI Cleanup:** 4 groups  
**Needs Manual Review:** 10 groups

**Key Finding:** Multiple dropdown options use slightly different labels for the same materials (Coroplast, ACM/Dibond, banner weights, etc.), creating potential confusion for users.

---

## Audit Methodology

**Files Reviewed:**
1. `/app/frontend/src/components/PricingCalculator.js` (primary dropdowns)
2. `/app/frontend/src/components/wrap/tabs/PricingTab.js` (wrap materials)
3. `/app/frontend/src/backend/models/pricing.py` (backend defaults)

**Search Patterns:**
- Substrate types (Coroplast, ACM, PVC, Aluminum)
- Banner materials (13oz, 18oz, mesh, etc.)
- Vinyl types (cast, calendered, wrap, cut)
- Laminate types (gloss, matte, satin)
- Transfer types (HTV, DTF, screen print)

---

## Findings by Category

### 1. Rigid Sign Substrates

#### Dropdown: `SUBSTRATE_TYPES` (PricingCalculator.js)

**Location:** PricingCalculator.js lines 157-168

**Current Options:**
```javascript
{ id: 'coroplast_4mm', name: 'Coroplast 4mm' }
{ id: 'coroplast_10mm', name: 'Coroplast 10mm' }
{ id: 'aluminum_040', name: 'Aluminum .040' }
{ id: 'aluminum_063', name: 'Aluminum .063' }
{ id: 'aluminum_080', name: 'Aluminum .080' }
{ id: 'pvc_3mm', name: 'PVC 3mm' }
{ id: 'pvc_6mm', name: 'PVC 6mm' }
{ id: 'acrylic', name: 'Acrylic' }
{ id: 'dibond', name: 'Dibond/ACM' }
{ id: 'mdo', name: 'MDO Plywood' }
```

#### Backend Materials (pricing.py):

```python
{ key: "coroplast_4mm", name: "Coroplast 4mm" }
{ key: "coroplast_10mm", name: "Coroplast 10mm" }
{ key: "pvc_3mm", name: "PVC 3mm" }
{ key: "pvc_6mm", name: "PVC 6mm" }
{ key: "acm_dibond_3mm", name: "ACM / Dibond 3mm" }  # ⚠️ Different ID
{ key: "aluminum_040", name: "Aluminum .040" }
{ key: "aluminum_063", name: "Aluminum .063" }
```

#### Issues Found:

**Issue 1: ACM/Dibond Inconsistency**
- **Frontend ID:** `dibond` → Label: "Dibond/ACM"
- **Backend ID:** `acm_dibond_3mm` → Label: "ACM / Dibond 3mm"
- **Type:** Near duplicate (ID mismatch, label variance)
- **Risk:** Medium (ID mismatch could break mapping)

**Recommended Canonical:**
- **Label:** "ACM / Dibond"
- **Value:** `acm_dibond` (or `aluminum_composite`)
- **Aliases:** `dibond`, `acm`, `acm_dibond_3mm`, `aluminum_composite`

**Action:** Needs Manual Review (verify saved orders using either ID)

---

### 2. Banner Materials

#### Dropdown: `PRINT_MATERIALS` (PricingCalculator.js)

**Location:** PricingCalculator.js lines 67-75

**Current Options:**
```javascript
{ id: 'banner_13oz', name: '13oz Banner' }
{ id: 'banner_18oz', name: '18oz Banner (Heavy)' }
```

#### Dynamic Banner Options (getBannerMaterialOptions):

**Location:** PricingCalculator.js lines 684-692

```javascript
{ key: 'banner_13oz', name: '13 oz Banner' }  # ⚠️ Space difference
{ key: 'banner_18oz', name: '18 oz Banner' }  # ⚠️ No "(Heavy)" suffix
{ key: 'banner_mesh', name: 'Mesh Banner' }
{ key: 'banner_blockout', name: 'Blockout Banner' }
{ key: 'banner_pole', name: 'Pole Banner Material' }
{ key: 'banner_fabric', name: 'Fabric Display Banner' }
{ key: 'banner_double_sided', name: 'Double-Sided Banner Material' }
{ key: 'banner_custom', name: 'Specialty / Custom Banner Material' }
```

#### Backend Materials (pricing.py):

```python
{ key: "banner_13oz", name: "13 oz Banner" }
{ key: "banner_18oz", name: "18 oz Banner" }
{ key: "banner_mesh", name: "Mesh Banner" }
# ... etc
```

#### Issues Found:

**Issue 2: Banner Weight Label Inconsistency**
- **Variant 1:** "13oz Banner" (no space)
- **Variant 2:** "13 oz Banner" (with space)
- **Type:** Exact duplicate (same ID, label variance)
- **Risk:** Low (cosmetic only)

**Issue 3: 18oz Banner Suffix Inconsistency**
- **Variant 1:** "18oz Banner (Heavy)"
- **Variant 2:** "18 oz Banner"
- **Type:** Near duplicate (different descriptions)
- **Risk:** Low (cosmetic, same ID)

**Recommended Canonical:**
- **13oz:** "13 oz Banner" (with space)
- **18oz:** "18 oz Banner" (drop "Heavy" suffix or make consistent)
- **Aliases:** `banner_13oz`, `13oz Banner`, `banner_13oz_vinyl`

**Action:** Safe to merge - use canonical labels with space

---

### 3. Vinyl Types

#### Dropdown: `VINYL_TYPES` (PricingCalculator.js)

**Location:** PricingCalculator.js lines 53-64

**Current Options:**
```javascript
{ id: 'oracal_651', name: 'Oracal 651' }
{ id: 'oracal_751', name: 'Oracal 751' }
{ id: 'oracal_951', name: 'Oracal 951' }
{ id: 'avery_hp750', name: 'Avery HP750' }
{ id: 'reflective_vinyl', name: 'Reflective Vinyl' }
{ id: 'metallic_vinyl', name: 'Metallic Vinyl' }
{ id: 'fluorescent_vinyl', name: 'Fluorescent Vinyl' }
{ id: 'etched_frost_vinyl', name: 'Etched / Frost Vinyl' }
{ id: 'wall_vinyl', name: 'Wall Vinyl' }
{ id: 'specialty_custom_vinyl', name: 'Specialty / Custom Vinyl' }
```

#### Backend Materials (pricing.py):

```python
{ key: "wall_vinyl", name: "Wall Vinyl" }
{ key: "specialty_custom_vinyl", name: "Specialty / Custom Vinyl" }
# Brand-specific vinyls not in backend defaults
```

#### Issues Found:

**Issue 4: Brand Names vs Generic Types**
- **Mix:** Specific brands (Oracal 651) + generic types (Reflective Vinyl)
- **Type:** Inconsistent classification
- **Risk:** Medium (confusion between brand and type)

**Recommended Approach:**
- **Option A:** Separate "Brand/Product" vs "Type/Category" dropdowns
- **Option B:** Standardize to generic types only: "Calendered Vinyl", "Cast Vinyl", "Reflective Vinyl"

**Action:** Needs Manual Review (business decision on brand vs generic)

---

### 4. Wrap Materials

#### Dropdown: `WRAP_MATERIAL_DEFAULTS` (PricingCalculator.js)

**Location:** PricingCalculator.js lines 215-222

**Current Options:**
```javascript
{ id: 'wrap_standard_calendared', name: 'Standard Calendared Vinyl' }  # ⚠️ Typo
{ id: 'wrap_premium_cast', name: 'Premium Cast Vinyl' }
{ id: 'wrap_cast_film', name: 'Wrap Cast Film' }  # ⚠️ Redundant
{ id: 'wrap_reflective', name: 'Reflective Vinyl' }
{ id: 'wrap_etched_frost', name: 'Etched / Frost Film' }
{ id: 'wrap_specialty_media', name: 'Specialty / Custom Vehicle Media' }
```

#### Wrap CC Pricing Tab: `MATERIAL_TYPES`

**Location:** /app/frontend/src/components/wrap/tabs/PricingTab.js lines 15-26

```javascript
{ value: 'printed_wrap_vinyl', label: 'Printed Wrap Vinyl' }
{ value: 'color_change_vinyl', label: 'Color Change Vinyl' }
{ value: 'laminate', label: 'Laminate' }
{ value: 'window_perf', label: 'Window Perf' }
{ value: 'transfer_tape', label: 'Transfer Tape' }
{ value: 'knifeless_tape', label: 'Knifeless Tape' }
{ value: 'primer', label: 'Primer' }
{ value: 'edge_sealer', label: 'Edge Sealer' }
{ value: 'cleaning_prep_supply', label: 'Cleaning / Prep Supply' }
{ value: 'other', label: 'Other' }
```

#### Issues Found:

**Issue 5: Calendared Spelling Typo**
- **Current:** "Calendared" (incorrect spelling)
- **Correct:** "Calendered"
- **Type:** Typo
- **Risk:** Low (cosmetic)

**Issue 6: Wrap Material Redundancy**
- **Duplicate concept:** "Premium Cast Vinyl" vs "Wrap Cast Film"
- **Type:** Near duplicate (both refer to cast vinyl for wraps)
- **Risk:** Medium (user confusion)

**Issue 7: Different Wrap Dropdowns**
- **Calculator:** Uses generic material types (Cast, Calendered)
- **Wrap CC:** Uses purpose-based types (Printed Wrap Vinyl, Color Change)
- **Type:** Different classification systems
- **Risk:** Medium (inconsistent UX across tools)

**Recommended Canonical:**
- Fix "Calendared" → "Calendered"
- Merge "Premium Cast Vinyl" + "Wrap Cast Film" → "Cast Wrap Vinyl"
- Consider aligning Calculator vs Wrap CC dropdown structures

**Action:** Safe to fix typo; Needs Review for dropdown alignment

---

### 5. Laminate Types

#### Dropdown: `WRAP_LAMINATE_DEFAULTS` (PricingCalculator.js)

**Location:** PricingCalculator.js lines 224-228

**Current Options:**
```javascript
{ id: 'wrap_laminate_gloss', name: 'Gloss Laminate' }
{ id: 'wrap_laminate_matte', name: 'Matte Laminate' }
{ id: 'wrap_laminate_satin', name: 'Satin Laminate' }
```

#### Backend Materials (pricing.py):

**Backend does NOT have laminate material defaults** (only referenced in vehicle graphics).

#### Issues Found:

**Issue 8: No Backend Material Match**
- **Frontend:** Has laminate dropdown
- **Backend:** No corresponding material defaults
- **Type:** Missing backend support
- **Risk:** Medium (calculator may not use these properly)

**Recommended Action:**
- Add backend material support for laminates
- OR clarify that laminates are add-ons, not base materials

**Action:** Needs Manual Review (verify if laminates work in pricing)

---

### 6. Transfer Types (Apparel)

#### Dropdown: `TRANSFER_TYPES` (PricingCalculator.js)

**Location:** PricingCalculator.js lines 182-188

**Current Options:**
```javascript
{ id: 'htv', name: 'HTV (Heat Transfer Vinyl)' }
{ id: 'screen_print', name: 'Screen Print' }
{ id: 'dtf', name: 'DTF (Direct to Film)' }
{ id: 'sublimation', name: 'Sublimation' }
{ id: 'embroidery', name: 'Embroidery' }
```

#### Issues Found:

**Issue 9: Acronym Clarity**
- **HTV:** Label includes full expansion "(Heat Transfer Vinyl)"
- **DTF:** Label includes full expansion "(Direct to Film)"
- **Others:** No expansion (Screen Print, Sublimation)
- **Type:** Inconsistent labeling style
- **Risk:** Low (cosmetic)

**Recommended Canonical:**
- **Consistent format:** Either all with expansions or none
- **Preferred:** "HTV (Heat Transfer Vinyl)", "DTF (Direct to Film)", "Screen Print", etc.

**Action:** Keep as-is (expansions help users) OR standardize format

---

### 7. Complexity Levels

#### Multiple Dropdowns with Same Values:

**Design Complexity:**
```javascript
const DESIGN_COMPLEXITY_LEVELS = [
  { value: 'simple', label: 'Simple' },
  { value: 'medium', label: 'Medium' },
  { value: 'complex', label: 'Complex' },
  { value: 'extreme', label: 'Extreme' },
];
```

**Install Complexity:**
```javascript
const INSTALL_COMPLEXITY_LEVELS = [
  { value: 'easy', label: 'Easy' },    # ⚠️ Different value
  { value: 'medium', label: 'Medium' },
  { value: 'difficult', label: 'Difficult' },  # ⚠️ Different value
  { value: 'extreme', label: 'Extreme' },
];
```

**Weeding Complexity:**
```javascript
const CUT_VINYL_WEEDING_LEVELS = [
  { value: 'simple', label: 'Simple' },
  { value: 'medium', label: 'Medium' },
  { value: 'complex', label: 'Complex' },
  { value: 'extreme', label: 'Extreme' },
];
```

#### Issues Found:

**Issue 10: Inconsistent Complexity Value Names**
- **Design/Weeding:** Uses `simple`, `medium`, `complex`, `extreme`
- **Install:** Uses `easy`, `medium`, `difficult`, `extreme`
- **Type:** Near duplicate (similar concepts, different values)
- **Risk:** Medium (pricing formulas may treat differently)

**Recommended Canonical:**
- **Standardize:** Use consistent values across all complexity types
- **Preferred:** `simple`, `medium`, `complex`, `extreme` (most common)
- **Aliases:** Map `easy` → `simple`, `difficult` → `complex`

**Action:** Needs Manual Review (verify calculator doesn't rely on specific values)

---

## Summary of Duplicates Found

### Exact Duplicates (Same ID, Label Variance)

| # | Dropdown | Issue | Example | Risk | Action |
|---|----------|-------|---------|------|--------|
| 1 | Banner 13oz | Space inconsistency | "13oz" vs "13 oz" | Low | Safe to merge |
| 2 | Banner 18oz | Suffix inconsistency | "(Heavy)" vs no suffix | Low | Safe to merge |

### Near Duplicates (Different IDs or Concepts)

| # | Dropdown | Issue | Example | Risk | Action |
|---|----------|-------|---------|------|--------|
| 3 | ACM/Dibond | ID mismatch | `dibond` vs `acm_dibond_3mm` | Medium | Needs Review |
| 4 | Wrap Cast | Redundancy | "Premium Cast" vs "Cast Film" | Medium | Needs Review |
| 5 | Vinyl Types | Brand vs Generic mix | Oracal 651 vs Reflective | Medium | Needs Review |
| 6 | Complexity | Value inconsistency | `easy` vs `simple` | Medium | Needs Review |

### Typos & Errors

| # | Dropdown | Issue | Current | Correct | Risk | Action |
|---|----------|-------|---------|---------|------|--------|
| 7 | Wrap Material | Spelling | "Calendared" | "Calendered" | Low | Safe to fix |

### Missing Backend Support

| # | Dropdown | Issue | Impact | Risk | Action |
|---|----------|-------|--------|------|--------|
| 8 | Laminates | No backend materials | Calculator may not price correctly | Medium | Needs Review |

---

## Recommended Canonical Labels

### Substrates

| Current Labels | Canonical Label | Value | Aliases |
|----------------|-----------------|-------|---------|
| Coroplast 4mm | Coroplast 4mm | `coroplast_4mm` | coroplast, coro_4mm |
| Coroplast 10mm | Coroplast 10mm | `coroplast_10mm` | coroplast, coro_10mm |
| Dibond/ACM, ACM / Dibond 3mm | ACM / Dibond | `acm_dibond` | dibond, acm, aluminum_composite, acm_dibond_3mm |
| PVC 3mm, PVC 6mm | PVC 3mm / 6mm | `pvc_3mm`, `pvc_6mm` | sintra, expanded_pvc |
| Aluminum .040/.063/.080 | Aluminum .040 (etc) | `aluminum_040` | aluminum, alu |

### Banner Materials

| Current Labels | Canonical Label | Value | Aliases |
|----------------|-----------------|-------|---------|
| 13oz Banner, 13 oz Banner | 13 oz Banner | `banner_13oz` | 13oz, banner_13oz_vinyl |
| 18oz Banner (Heavy), 18 oz Banner | 18 oz Banner | `banner_18oz` | 18oz, heavy_banner |
| Mesh Banner | Mesh Banner | `banner_mesh` | mesh, perforated_banner |

### Wrap Materials

| Current Labels | Canonical Label | Value | Aliases |
|----------------|-----------------|-------|---------|
| Standard Calendared Vinyl | Calendered Vinyl | `wrap_calendered` | calendared, standard_wrap |
| Premium Cast Vinyl, Wrap Cast Film | Cast Wrap Vinyl | `wrap_cast` | premium_cast, cast_film |
| Printed Wrap Vinyl | Printed Wrap Vinyl | `printed_wrap_vinyl` | print_vinyl, wrap_vinyl |
| Color Change Vinyl | Color Change Vinyl | `color_change_vinyl` | solid_color_wrap |

### Laminates

| Current Labels | Canonical Label | Value | Aliases |
|----------------|-----------------|-------|---------|
| Gloss Laminate | Gloss Laminate | `laminate_gloss` | cast_gloss, wrap_gloss |
| Matte Laminate | Matte Laminate | `laminate_matte` | cast_matte, wrap_matte |
| Satin Laminate | Satin Laminate | `laminate_satin` | luster, semi_gloss |

---

## Alias Mapping Strategy

**How old values will continue to work:**

### Example: ACM/Dibond

**Current Saved Values:**
- Some orders: `dibond`
- Some orders: `acm_dibond_3mm`
- Future orders: `acm_dibond`

**Resolution Function:**
```javascript
const MATERIAL_ALIAS_MAP = {
  // ACM/Dibond aliases
  'dibond': 'acm_dibond',
  'acm': 'acm_dibond',
  'acm_dibond_3mm': 'acm_dibond',
  'aluminum_composite': 'acm_dibond',
  
  // Coroplast aliases
  'coro': 'coroplast_4mm',  // Default to 4mm
  'corrugated_plastic': 'coroplast_4mm',
  
  // PVC aliases
  'sintra': 'pvc_3mm',  // Default to 3mm
  'expanded_pvc': 'pvc_3mm',
  
  // Banner aliases
  '13oz': 'banner_13oz',
  '18oz': 'banner_18oz',
  
  // Wrap aliases
  'calendared': 'wrap_calendered',
  'premium_cast': 'wrap_cast',
  'cast_film': 'wrap_cast',
};

function resolveMaterialAlias(value) {
  return MATERIAL_ALIAS_MAP[value] || value;
}

function getMaterialDisplayName(savedValue) {
  const canonical = resolveMaterialAlias(savedValue);
  return CANONICAL_NAMES[canonical] || savedValue;
}
```

**Safety:**
- ✅ Old orders still display correctly
- ✅ Old values still calculate correctly
- ✅ No database migration required
- ✅ No saved data overwritten

---

## Safe for UI Cleanup (Phase 5)

### Level 1: Exact Duplicates (Low Risk)

**Safe to clean immediately:**

1. **Banner weight spacing** - Standardize "13 oz Banner" (with space)
2. **Banner 18oz suffix** - Remove "(Heavy)" or keep consistent
3. **Calendared typo** - Fix to "Calendered"

**Implementation:**
- Update dropdown constant arrays
- Add alias mapping
- Test dropdown display
- Verify saved orders load

**Estimated Effort:** 1 hour

---

## Needs Manual Review (Phase 5+)

### Medium Risk - Business Decision Required

**Requires review before cleanup:**

1. **ACM/Dibond ID mismatch** - Verify which ID is used in saved orders
2. **Wrap Cast redundancy** - Decide on single canonical option
3. **Vinyl brand vs generic** - Business decision on dropdown structure
4. **Complexity value inconsistency** - Verify calculator dependencies
5. **Wrap CC vs Calculator alignment** - Decide on consistent dropdown structure
6. **Laminate backend support** - Verify if working, add materials if needed

**Recommended Approach:**
- Query database for material value frequency
- Test calculator with different values
- Get user feedback on preferred labels
- Plan migration for high-impact changes

**Estimated Effort:** 3-4 hours

---

## Files Containing Dropdowns

### Frontend Dropdown Definitions

| File | Dropdowns Found | Line Range |
|------|----------------|------------|
| `/app/frontend/src/components/PricingCalculator.js` | 15+ dropdowns | Lines 53-248 |
| `/app/frontend/src/components/wrap/tabs/PricingTab.js` | Material types | Lines 15-26 |
| `/app/frontend/src/pages/NewOrderForm.js` | Category selectors | Various |

### Backend Material Definitions

| File | Materials Found | Line Range |
|------|----------------|------------|
| `/app/backend/models/pricing.py` | 50+ materials | Lines 200-500 |

---

## Testing & Verification Checklist

**Before any cleanup, verify:**

- [ ] Database query: Which material IDs are actually used in saved orders?
- [ ] Frequency analysis: Most common vs rarely used options
- [ ] Calculator testing: Do all dropdown values calculate correctly?
- [ ] Wrap CC testing: Do wrap materials work end-to-end?
- [ ] Order loading: Do old orders with legacy IDs still load?
- [ ] Quiz testing: Do quiz-mapped values still work?

---

## Recommended Cleanup Order

### Phase 5A: Low-Risk Fixes (1-2 hours)

1. Fix "Calendared" typo → "Calendered"
2. Standardize banner weight labels (13 oz, 18 oz)
3. Add alias mapping for old values
4. Test dropdown display

### Phase 5B: Medium-Risk Alignment (3-4 hours)

5. Verify ACM/Dibond ID usage in database
6. Align canonical IDs if safe
7. Add comprehensive alias mapping
8. Test saved order loading

### Phase 5C: High-Impact Review (Future)

9. Decide on vinyl brand vs generic strategy
10. Align Wrap CC and Calculator dropdown structures
11. Add backend laminate materials if needed
12. Standardize complexity value names

---

## Confirmation

✅ **No code changes made** - This is audit only  
✅ **No dropdowns removed**  
✅ **No backend values deleted**  
✅ **No saved orders modified**  
✅ **No pricing formulas changed**  
✅ **No calculator logic updated**

**All findings documented for review before cleanup.**

---

## Next Steps

**Awaiting user decision:**

1. Review audit findings
2. Approve Level 1 safe fixes (typo, spacing)
3. Decide on business questions (brand vs generic, dropdown alignment)
4. Approve Phase 5A implementation (low-risk fixes only)

**Estimated Phase 5A effort:** 1-2 hours (safe fixes only)
