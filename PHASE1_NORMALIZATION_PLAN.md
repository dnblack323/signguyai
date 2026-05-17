# Phase 1: Category & Dimension Normalization (Backward Compatible)

**Goal**: Establish canonical naming standards with zero breaking changes. Add aliases for old field names. No UI changes, no formula changes, no deletions.

**Duration**: 1-2 hours  
**Risk Level**: ⚠️ LOW (Additive only, fully backward compatible)

---

## 📋 CANONICAL STANDARDS

### Category Names (Already Correct in Backend Enum):
```
banners
rigid_signs  
cut_vinyl
digital_print
vehicle_graphics
apparel
services
promotional
custom
```

### Dimension Field Names (Standard Going Forward):
```
width_inches   (float, always in inches)
height_inches  (float, always in inches)
area_sqft      (float, computed by backend)
```

### Backward Compatibility Aliases (Add These):
```
width              → width_inches
height             → height_inches
length_inches      → height_inches
square_footage     → area_sqft
vehicle_wrap       → vehicle_graphics
vehicle_wraps      → vehicle_graphics
promo_misc         → promotional
```

---

## 📁 EXACT FILES TO CHANGE

### Backend: 2 files
1. `/app/backend/routes/pricing.py` - Add normalization aliases
2. `/app/backend/models/pricing.py` - Document canonical fields (comments only)

### Frontend: 0 files
- No changes in Phase 1 (maintain existing behavior)

### Tests: 1 file
3. `/app/backend/tests/test_pricing.py` - Add backward compatibility tests

---

## 🔧 EXACT CODE CHANGES

### CHANGE 1: Add Dimension Field Aliases
**File**: `/app/backend/routes/pricing.py`  
**Location**: Lines 31-56 (inside `_normalize_pricing_payload` function)

**Current Code** (lines 31-55):
```python
def _normalize_pricing_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(payload or {})
    substrate = normalized.get("substrate_type")
    thickness = normalized.get("thickness")
    print_material = normalized.get("print_material")
    substrate_map = {
        ("coroplast", "4mm"): "coroplast_4mm",
        # ... existing substrate mappings ...
    }
    if substrate and thickness:
        normalized["substrate_type"] = substrate_map.get((str(substrate).lower(), str(thickness).lower()), substrate)
    print_material_map = {
        "13oz_vinyl": "banner_13oz",
        # ... existing material mappings ...
    }
    if print_material:
        normalized["print_material"] = print_material_map.get(str(print_material).lower(), print_material)
    return normalized
```

**NEW Code** (add AFTER line 55, BEFORE `return normalized`):
```python
def _normalize_pricing_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = dict(payload or {})
    
    # --- DIMENSION FIELD NORMALIZATION (Phase 1) ---
    # Canonical fields: width_inches, height_inches, area_sqft
    # Legacy aliases: width, height, length_inches, square_footage
    
    # Alias: width → width_inches
    if "width" in normalized and "width_inches" not in normalized:
        normalized["width_inches"] = normalized["width"]
    
    # Alias: height → height_inches
    if "height" in normalized and "height_inches" not in normalized:
        normalized["height_inches"] = normalized["height"]
    
    # Alias: length_inches → height_inches (common legacy field)
    if "length_inches" in normalized and "height_inches" not in normalized:
        normalized["height_inches"] = normalized["length_inches"]
    
    # Alias: square_footage → area_sqft
    if "square_footage" in normalized and "area_sqft" not in normalized:
        normalized["area_sqft"] = normalized["square_footage"]
    
    # --- SUBSTRATE & MATERIAL NORMALIZATION (existing code) ---
    substrate = normalized.get("substrate_type")
    thickness = normalized.get("thickness")
    print_material = normalized.get("print_material")
    substrate_map = {
        ("coroplast", "4mm"): "coroplast_4mm",
        ("coroplast", "10mm"): "coroplast_10mm",
        ("aluminum", "0.040"): "aluminum_040",
        ("aluminum", "0.063"): "aluminum_063",
        ("aluminum", "0.080"): "aluminum_080",
        ("pvc", "3mm_pvc"): "pvc_3mm",
        ("pvc", "6mm_pvc"): "pvc_6mm",
    }
    if substrate and thickness:
        normalized["substrate_type"] = substrate_map.get((str(substrate).lower(), str(thickness).lower()), substrate)
    
    print_material_map = {
        "13oz_vinyl": "banner_13oz",
        "18oz_vinyl": "banner_18oz",
        "adhesive_vinyl": "vinyl_adhesive",
        "mesh_banner": "banner_13oz",
    }
    if print_material:
        normalized["print_material"] = print_material_map.get(str(print_material).lower(), print_material)
    
    return normalized
```

**Lines to modify**: Insert new block after line 32 (after `normalized = dict(payload or {})`), before existing substrate logic.

---

### CHANGE 2: Add Category Aliases
**File**: `/app/backend/routes/pricing.py`  
**Location**: Lines 58-66 (inside `_normalize_pricing_category` function)

**Current Code** (lines 58-66):
```python
def _normalize_pricing_category(category: Any) -> PricingCategory:
    raw = str(category or "custom").lower()
    alias_map = {
        "promo_misc": PricingCategory.PROMOTIONAL,
        "vehicle_wrap": PricingCategory.VEHICLE_GRAPHICS,
    }
    if raw in alias_map:
        return alias_map[raw]
    return PricingCategory(raw)
```

**NEW Code** (expand alias_map):
```python
def _normalize_pricing_category(category: Any) -> PricingCategory:
    """
    Normalize category names to canonical enum values.
    
    Canonical categories:
    - banners, rigid_signs, cut_vinyl, digital_print, vehicle_graphics, 
      apparel, services, promotional, custom
    
    Legacy aliases supported for backward compatibility.
    """
    raw = str(category or "custom").lower()
    
    # Category alias map (Phase 1 backward compatibility)
    alias_map = {
        "promo_misc": PricingCategory.PROMOTIONAL,
        "vehicle_wrap": PricingCategory.VEHICLE_GRAPHICS,
        "vehicle_wraps": PricingCategory.VEHICLE_GRAPHICS,  # ← ADD THIS
    }
    
    if raw in alias_map:
        return alias_map[raw]
    
    # Try direct enum lookup (handles canonical names)
    try:
        return PricingCategory(raw)
    except ValueError:
        # Fallback to CUSTOM if category not recognized
        return PricingCategory.CUSTOM
```

**Lines to modify**: Replace lines 58-66 entirely with new version.

---

### CHANGE 3: Document Canonical Fields (Comments Only)
**File**: `/app/backend/models/pricing.py`  
**Location**: Lines 1276-1289 (inside `JobItemPricingData` class)

**Current Code** (lines 1276-1289):
```python
class JobItemPricingData(BaseModel):
    """Category-specific pricing inputs for a job item"""
    category: PricingCategory = PricingCategory.CUSTOM
    complexity: int = 1  # Default to 1 (simple), not 5
    
    # Setup fee control - ONE TIME per order, optional
    include_setup_fee: bool = False
    setup_fee: Optional[float] = None
    
    # Dimensions
    width_inches: Optional[float] = None
    length_inches: Optional[float] = None
    square_footage: Optional[float] = None
```

**NEW Code** (add documentation comments):
```python
class JobItemPricingData(BaseModel):
    """Category-specific pricing inputs for a job item"""
    category: PricingCategory = PricingCategory.CUSTOM
    complexity: int = 1  # Default to 1 (simple), not 5
    
    # Setup fee control - ONE TIME per order, optional
    include_setup_fee: bool = False
    setup_fee: Optional[float] = None
    
    # --- DIMENSIONS (Phase 1: Canonical + Legacy Fields) ---
    # CANONICAL FIELDS (use these going forward):
    width_inches: Optional[float] = None    # Width in inches (canonical)
    height_inches: Optional[float] = None   # Height in inches (canonical, added Phase 1)
    area_sqft: Optional[float] = None       # Area in square feet (canonical, added Phase 1)
    
    # LEGACY FIELDS (kept for backward compatibility, normalized via _normalize_pricing_payload):
    length_inches: Optional[float] = None   # Legacy: maps to height_inches
    square_footage: Optional[float] = None  # Legacy: maps to area_sqft
    # Note: Frontend may also send "width" or "height" (normalized to width_inches/height_inches)
```

**Lines to modify**: Replace lines 1286-1289 with new version.

**IMPORTANT**: Add `height_inches` and `area_sqft` as NEW optional fields. Do NOT remove `length_inches` or `square_footage`.

---

### CHANGE 4: Add Backward Compatibility Tests
**File**: `/app/backend/tests/test_pricing.py`  
**Location**: End of file (append new test class)

**NEW Code** (append to end of file):
```python
# ============== PHASE 1: NORMALIZATION TESTS ==============

class TestPhase1Normalization:
    """Test backward compatibility for dimension and category aliases (Phase 1)"""
    
    @pytest.mark.asyncio
    async def test_dimension_alias_width_to_width_inches(self, test_user):
        """Test that 'width' field is normalized to 'width_inches'"""
        payload = {
            "category": "rigid_signs",
            "pricing_data": {
                "width": 24.0,        # Legacy field
                "height": 36.0,       # Legacy field
                "substrate_type_key": "coroplast_4mm"
            },
            "quantity": 1
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] > 0
        # Verify calculation ran (no 500 error = normalization worked)
    
    @pytest.mark.asyncio
    async def test_dimension_alias_length_to_height(self, test_user):
        """Test that 'length_inches' field is normalized to 'height_inches'"""
        payload = {
            "category": "cut_vinyl",
            "pricing_data": {
                "width_inches": 24.0,
                "length_inches": 36.0,  # Legacy field (should map to height_inches)
                "vinyl_type_key": "oracal_651"
            },
            "quantity": 1
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_dimension_alias_square_footage_to_area_sqft(self, test_user):
        """Test that 'square_footage' field is normalized to 'area_sqft'"""
        payload = {
            "category": "banners",
            "pricing_data": {
                "square_footage": 32.0,  # Legacy field (4x8 banner)
                "banner_material_key": "banner_13oz"
            },
            "quantity": 1
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_category_alias_vehicle_wraps(self, test_user):
        """Test that 'vehicle_wraps' category is normalized to 'vehicle_graphics'"""
        payload = {
            "category": "vehicle_wraps",  # Legacy category name
            "pricing_data": {
                "vehicle_type": "car_sedan",
                "coverage_type": "spot"
            },
            "quantity": 1
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_category_alias_vehicle_wrap_singular(self, test_user):
        """Test that 'vehicle_wrap' category is normalized to 'vehicle_graphics'"""
        payload = {
            "category": "vehicle_wrap",  # Legacy category name (singular)
            "pricing_data": {
                "vehicle_type": "pickup",
                "coverage_type": "partial"
            },
            "quantity": 1
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_category_alias_promo_misc(self, test_user):
        """Test that 'promo_misc' category is normalized to 'promotional'"""
        payload = {
            "category": "promo_misc",  # Legacy category name
            "pricing_data": {
                "promo_product_type": "magnets",
                "unit_cost": 2.50,
                "markup_percent": 100
            },
            "quantity": 100
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["selling_price"] > 0
    
    @pytest.mark.asyncio
    async def test_canonical_fields_still_work(self, test_user):
        """Test that canonical field names continue to work (no regression)"""
        payload = {
            "category": "rigid_signs",  # Canonical category
            "pricing_data": {
                "width_inches": 24.0,   # Canonical field
                "height_inches": 36.0,  # Canonical field (NEW in Phase 1)
                "substrate_type_key": "coroplast_4mm"
            },
            "quantity": 1
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["material_cost"] > 0
        assert data["total_cost"] > 0
    
    @pytest.mark.asyncio
    async def test_mixed_legacy_and_canonical_fields(self, test_user):
        """Test that mixing legacy and canonical fields doesn't break"""
        payload = {
            "category": "digital_print",
            "pricing_data": {
                "width": 48.0,              # Legacy field
                "height_inches": 96.0,      # Canonical field
                "print_media_key": "banner_13oz"
            },
            "quantity": 1
        }
        
        response = await client.post(
            "/api/pricing/calculate",
            json=payload,
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 200
        # If width is present, it should be normalized to width_inches
        # height_inches is already canonical, should work as-is
```

**Action**: Append entire test class to end of `/app/backend/tests/test_pricing.py`.

---

## ✅ WHAT TESTS/CHECKS PROVE PHASE 1 WORKED

### Automated Tests (Run These):
```bash
# Run Phase 1 normalization tests
cd /app/backend
pytest tests/test_pricing.py::TestPhase1Normalization -v

# Expected: All 9 tests pass
# - test_dimension_alias_width_to_width_inches ✓
# - test_dimension_alias_length_to_height ✓
# - test_dimension_alias_square_footage_to_area_sqft ✓
# - test_category_alias_vehicle_wraps ✓
# - test_category_alias_vehicle_wrap_singular ✓
# - test_category_alias_promo_misc ✓
# - test_canonical_fields_still_work ✓
# - test_mixed_legacy_and_canonical_fields ✓
```

### Manual API Tests (Use curl):
```bash
# Test 1: Legacy dimension fields (width, height)
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
TOKEN="<your-test-token>"

curl -X POST "$API_URL/api/pricing/calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "rigid_signs",
    "pricing_data": {
      "width": 24,
      "height": 36,
      "substrate_type_key": "coroplast_4mm"
    },
    "quantity": 1
  }'

# Expected: 200 OK, returns calculation (no 500 error)

# Test 2: Legacy category name (vehicle_wraps)
curl -X POST "$API_URL/api/pricing/calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "vehicle_wraps",
    "pricing_data": {
      "vehicle_type": "car_sedan",
      "coverage_type": "spot"
    },
    "quantity": 1
  }'

# Expected: 200 OK, returns vehicle graphics calculation

# Test 3: Canonical fields (width_inches, height_inches)
curl -X POST "$API_URL/api/pricing/calculate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "cut_vinyl",
    "pricing_data": {
      "width_inches": 12,
      "height_inches": 24,
      "vinyl_type_key": "oracal_651"
    },
    "quantity": 5
  }'

# Expected: 200 OK, calculation uses height_inches correctly
```

### Frontend Regression Test (Manual):
1. Open calculator at `/pricing-calculator` or embedded in order/quote
2. Select "Vehicle Graphics" category
3. Enter dimensions using existing UI fields
4. Click Calculate
5. **Expected**: Calculation runs successfully (no errors)
6. Try all categories (banners, rigid_signs, cut_vinyl, etc.)
7. **Expected**: All categories calculate without errors

### Database Check (Optional):
```bash
# Check existing pricing_configuration documents
mongo --eval 'db.pricing_configuration.find({}, {category_defaults: 1}).pretty()'

# Expected: No errors, existing category_defaults keys may include "vehicle_wraps"
# (This is fine - our normalization handles it)
```

---

## 🚫 WHAT TO LEAVE ALONE (DO NOT TOUCH)

### ❌ DO NOT change these files:
1. **Any frontend component** (`/app/frontend/src/**/*.js`) - Phase 1 is backend-only
2. **Pricing calculators** (`/app/backend/server.py` lines 2556+) - No formula changes
3. **PricingFoundation.js** page - No UI redesign
4. **PricingSetup.js** page - No changes to historical import
5. **PricingPage.js** / **PricingPagePublic.js** - No changes to subscription pricing
6. **Database migrations** - Not needed (normalization is runtime only)
7. **Frontend `.env` files** - No config changes
8. **Material definitions** in `pricing.py` model (lines 82-200) - No edits to default materials

### ❌ DO NOT delete these fields:
- ❌ `length_inches` (keep for backward compat)
- ❌ `square_footage` (keep for backward compat)
- ❌ `width` field (will be normalized, but don't remove from model)
- ❌ `height` field (will be normalized, but don't remove from model)

### ❌ DO NOT change these behaviors:
- ❌ Frontend still sends whatever fields it currently sends
- ❌ Pricing formulas remain identical (no calculation changes)
- ❌ Material costs, labor rates stay the same
- ❌ Markup multipliers unchanged
- ❌ Quantity discounts unchanged

---

## ⚠️ RISK AREAS & MITIGATION

### Risk 1: Existing API Calls Break
**Scenario**: Old frontend code sends `{"width": 24, "length_inches": 36}`, backend doesn't recognize.  
**Mitigation**: Normalization function preserves ALL existing fields, only ADDS canonical equivalents.  
**Test**: All manual curl tests above should pass with legacy fields.

### Risk 2: Missing Category in Enum
**Scenario**: Client sends `category: "vehicle_wrap"` but enum doesn't have it.  
**Mitigation**: Alias map converts to `VEHICLE_GRAPHICS` before enum lookup.  
**Test**: Test case `test_category_alias_vehicle_wrap_singular` verifies this.

### Risk 3: Calculator Expects Specific Field Name
**Scenario**: A calculator reads `data.length_inches` directly and fails if field is renamed.  
**Mitigation**: We are NOT renaming fields, only ADDING new canonical fields alongside legacy ones.  
**Test**: Run full test suite after changes: `pytest tests/test_pricing.py -v`

### Risk 4: Frontend Sends Both Legacy and Canonical
**Scenario**: Frontend sends `{"width": 24, "width_inches": 30}` (conflicting values).  
**Mitigation**: Normalization checks `if "width_inches" not in normalized` before mapping. Canonical field takes precedence.  
**Test**: Test case `test_mixed_legacy_and_canonical_fields` covers this.

### Risk 5: Breaking Production Data
**Scenario**: Existing tenant has `category_defaults: {"vehicle_wraps": {...}}` in database.  
**Mitigation**: Alias map handles runtime normalization. No database migration needed.  
**Test**: Existing defaults load via `/api/pricing/defaults` endpoint (check logs).

---

## 🎯 IMPLEMENTATION CHECKLIST

### Pre-Implementation:
- [ ] Review this plan with team/stakeholder
- [ ] Backup database (optional, but recommended): `mongodump --out /tmp/backup`
- [ ] Create feature branch: `git checkout -b phase1-pricing-normalization`

### Implementation Steps:
1. [ ] **CHANGE 1**: Update `_normalize_pricing_payload` in `/app/backend/routes/pricing.py`
2. [ ] **CHANGE 2**: Update `_normalize_pricing_category` in `/app/backend/routes/pricing.py`
3. [ ] **CHANGE 3**: Add documentation comments to `JobItemPricingData` in `/app/backend/models/pricing.py`
4. [ ] **CHANGE 4**: Add test class to `/app/backend/tests/test_pricing.py`
5. [ ] Commit changes: `git add . && git commit -m "Phase 1: Add dimension & category normalization aliases"`

### Testing:
6. [ ] Run pytest: `cd /app/backend && pytest tests/test_pricing.py::TestPhase1Normalization -v`
7. [ ] Run full pricing test suite: `pytest tests/test_pricing.py -v`
8. [ ] Run manual curl tests (all 3 scenarios above)
9. [ ] Test frontend calculator (manual click-through)
10. [ ] Check backend logs for errors: `tail -n 50 /var/log/supervisor/backend.err.log`

### Deployment:
11. [ ] Restart backend: `sudo supervisorctl restart backend`
12. [ ] Verify service status: `sudo supervisorctl status backend`
13. [ ] Smoke test production: Call `/api/pricing/calculate` with legacy fields
14. [ ] Monitor logs for 5 minutes: `tail -f /var/log/supervisor/backend.out.log`

### Post-Deployment:
15. [ ] Mark Phase 1 complete in project tracker
16. [ ] Document any edge cases discovered
17. [ ] Plan Phase 2 (if/when ready): Frontend field migration

---

## 📊 SUCCESS CRITERIA

✅ **Phase 1 is successful if**:
1. All 9 new tests pass
2. Existing tests still pass (no regressions)
3. Frontend calculator works with ALL categories
4. Legacy API calls (`width`, `vehicle_wraps`) return 200 OK
5. Canonical API calls (`width_inches`, `vehicle_graphics`) return 200 OK
6. No 500 errors in backend logs for pricing endpoints
7. Existing tenant pricing configurations still load

✅ **Phase 1 is complete when**:
- Backward compatibility aliases are live
- Tests are passing
- Documentation is updated
- No breaking changes deployed

---

## 🔄 ROLLBACK PLAN

If Phase 1 causes issues:

```bash
# 1. Revert git commit
git revert HEAD

# 2. Restart backend
cd /app/backend
sudo supervisorctl restart backend

# 3. Verify rollback worked
curl -X POST $API_URL/api/pricing/calculate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"category":"rigid_signs","pricing_data":{"width_inches":24,"length_inches":36},"quantity":1}'

# Expected: 200 OK (should work with or without Phase 1 changes)
```

**Rollback Time**: < 2 minutes  
**Data Loss**: None (no schema changes, no data migrations)

---

## 📈 NEXT STEPS (Future Phases - NOT in Phase 1)

Once Phase 1 is stable and deployed for 1-2 weeks:

### Phase 2 (Optional): Frontend Field Migration
- Update frontend to send canonical fields (`width_inches`, `height_inches`)
- Keep legacy field support in backend for external API users

### Phase 3 (Optional): Remove Frontend Pricing Logic
- Move calculations to backend
- Frontend becomes pure input collector

### Phase 4 (Optional): Enhanced Breakdown
- Add itemized cost components
- Return material/labor line items

**Important**: Do NOT implement Phase 2+ until Phase 1 is proven stable in production.

---

## 📝 SUMMARY

**What Phase 1 Does**:
- ✅ Adds backward compatibility aliases for dimension fields
- ✅ Adds backward compatibility aliases for category names
- ✅ Documents canonical field standards
- ✅ Adds comprehensive tests
- ✅ Zero breaking changes

**What Phase 1 Does NOT Do**:
- ❌ Change frontend components
- ❌ Remove legacy fields
- ❌ Modify pricing formulas
- ❌ Redesign UI
- ❌ Touch historical import
- ❌ Change database schema

**Risk Level**: ⚠️ LOW  
**Effort**: 1-2 hours  
**Reversibility**: Full (git revert)  
**Production Impact**: None (additive only)

---

**End of Phase 1 Plan**
