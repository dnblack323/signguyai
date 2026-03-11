# Changes Made This Week - To Reinstate After Rollback

**Created:** March 11, 2026
**Purpose:** Reference for what to add back after rolling back to a previous GitHub version

---

## CRITICAL FIXES (Must Reinstate First)

### 1. bcrypt Version Fix (LOGIN BROKEN WITHOUT THIS)
**File:** `backend/requirements.txt`
**Change:** Pin bcrypt to 4.0.1
```
bcrypt==4.0.1
```
**Why:** bcrypt 4.1.x breaks passlib password verification, causing all logins to fail silently.

---

### 2. AI Tools Rate Limiter Fix (AI BROKEN WITHOUT THIS)
**File:** `backend/routes/ai.py`
**Lines:** ~979-1020 and ~1035-1080

**BROKEN code:**
```python
async def generate_ai_content(request_obj: Request, request: AIGenerateRequest, ...)
```

**FIXED code:**
```python
async def generate_ai_content(request: Request, data: AIGenerateRequest, ...)
```

Then change all references from `request.tool` to `data.tool`, `request.input_data` to `data.input_data`, etc.

Same fix needed for `generate_ai_images` endpoint.

---

## DATA SAFETY (Soft Delete Implementation)

### 3. Soft Delete Service
**NEW FILE:** `backend/services/soft_delete_service.py`
```python
"""
Soft Delete Service

Provides soft delete functionality for data safety.
Records are marked with deleted_at timestamp instead of permanent deletion.
"""

from datetime import datetime, timezone
from typing import Optional

class SoftDeleteService:
    def __init__(self, db):
        self.db = db
    
    async def soft_delete(
        self,
        collection_name: str,
        record_id: str,
        deleted_by: str,
        tenant_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Mark a record as deleted"""
        now = datetime.now(timezone.utc)
        result = await self.db[collection_name].update_one(
            {"id": record_id, "tenant_id": tenant_id, "deleted_at": None},
            {"$set": {
                "deleted_at": now.isoformat(),
                "deleted_by": deleted_by,
                "deletion_reason": reason
            }}
        )
        return result.modified_count > 0
    
    async def restore(
        self,
        collection_name: str,
        record_id: str,
        restored_by: str,
        tenant_id: str
    ) -> bool:
        """Restore a soft-deleted record"""
        now = datetime.now(timezone.utc)
        result = await self.db[collection_name].update_one(
            {"id": record_id, "tenant_id": tenant_id, "deleted_at": {"$ne": None}},
            {
                "$set": {
                    "restored_at": now.isoformat(),
                    "restored_by": restored_by
                },
                "$unset": {
                    "deleted_at": "",
                    "deleted_by": "",
                    "deletion_reason": ""
                }
            }
        )
        return result.modified_count > 0
    
    async def hard_delete(
        self,
        collection_name: str,
        record_id: str,
        tenant_id: str,
        admin_confirmation: bool = False
    ) -> bool:
        """Permanently delete a record (requires admin confirmation)"""
        if not admin_confirmation:
            return False
        result = await self.db[collection_name].delete_one(
            {"id": record_id, "tenant_id": tenant_id}
        )
        return result.deleted_count > 0
    
    async def get_deleted_records(
        self,
        collection_name: str,
        tenant_id: str,
        limit: int = 100
    ):
        """Get list of soft-deleted records"""
        cursor = self.db[collection_name].find(
            {"tenant_id": tenant_id, "deleted_at": {"$ne": None}},
            {"_id": 0}
        ).sort("deleted_at", -1).limit(limit)
        return await cursor.to_list(limit)


def build_active_filter(tenant_id: str, include_deleted: bool = False) -> dict:
    """Build query filter that excludes deleted records by default"""
    query = {"tenant_id": tenant_id}
    if not include_deleted:
        query["deleted_at"] = None
    return query
```

### 4. Update Routes for Soft Delete
**Files to update:**
- `backend/routes/invoices.py`
- `backend/routes/quotes.py`
- `backend/routes/webstores.py`
- `backend/routes/employees.py`

**Pattern for each route file:**

Add import at top:
```python
from services.soft_delete_service import SoftDeleteService, build_active_filter
```

Update GET list endpoint:
```python
@router.get("")
async def get_items(include_deleted: bool = False, current_user = Depends(...)):
    query = build_active_filter(current_user.tenant_id, include_deleted)
    # ... rest of query
```

Update GET single item endpoint:
```python
@router.get("/{id}")
async def get_item(id: str, current_user = Depends(...)):
    item = await db.collection.find_one(
        {"id": id, "tenant_id": current_user.tenant_id, "deleted_at": None},
        {"_id": 0}
    )
```

Replace DELETE endpoint:
```python
@router.delete("/{id}")
async def delete_item(id: str, permanent: bool = False, current_user = Depends(...)):
    soft_delete_service = SoftDeleteService(db)
    
    if permanent:
        success = await soft_delete_service.hard_delete(...)
        return {"message": "Permanently deleted"}
    else:
        success = await soft_delete_service.soft_delete(...)
        return {"message": "Deleted (can be restored)"}
```

Add restore endpoint:
```python
@router.post("/{id}/restore")
async def restore_item(id: str, current_user = Depends(...)):
    soft_delete_service = SoftDeleteService(db)
    success = await soft_delete_service.restore(...)
    return {"message": "Restored"}
```

Add deleted list endpoint:
```python
@router.get("/deleted/list")
async def get_deleted_items(current_user = Depends(...)):
    soft_delete_service = SoftDeleteService(db)
    deleted = await soft_delete_service.get_deleted_records(...)
    return {"deleted_items": deleted, "count": len(deleted)}
```

---

## PROMO CODE UPDATES

### 5. Trial Lockout Promo Code Input
**File:** `frontend/src/components/TrialLockout.js`

Add to imports:
```javascript
import { Input } from './ui/input';
import { Tag, Loader2 } from 'lucide-react';
```

Add state:
```javascript
const [promoCode, setPromoCode] = useState('');
const [promoLoading, setPromoLoading] = useState(false);
```

Add promo code handler:
```javascript
const handleApplyPromoCode = async () => {
  if (!promoCode.trim()) {
    toast.error('Please enter a promo code');
    return;
  }
  setPromoLoading(true);
  try {
    const response = await axios.post(
      `${API_URL}/api/billing/apply-promo`,
      { promo_code: promoCode.trim() },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (response.data.success) {
      toast.success(response.data.message);
      window.location.reload();
    }
  } catch (error) {
    toast.error(error.response?.data?.detail || 'Failed to apply promo code');
  } finally {
    setPromoLoading(false);
  }
};
```

Add UI section before CTA buttons:
```jsx
{/* Promo Code Section */}
<div className="mb-6 p-4 rounded-xl bg-[var(--card-bg)] border border-[var(--border-color)]">
  <div className="flex items-center gap-2 mb-3">
    <Tag className="w-4 h-4 text-amber-500" />
    <span className="text-sm font-medium">Have a promo code?</span>
  </div>
  <div className="flex gap-2">
    <Input
      type="text"
      placeholder="Enter promo code"
      value={promoCode}
      onChange={(e) => setPromoCode(e.target.value.toUpperCase())}
      className="flex-1"
    />
    <Button onClick={handleApplyPromoCode} disabled={promoLoading} variant="outline">
      {promoLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Apply'}
    </Button>
  </div>
</div>
```

### 6. Backend Promo Code Endpoints
**File:** `backend/routes/billing.py`

Add at end of file:
```python
class ApplyPromoRequest(BaseModel):
    promo_code: str

@router.post("/apply-promo")
async def apply_promo_code(
    request: Request,
    data: ApplyPromoRequest,
    current_user = Depends(get_current_user_billing)
):
    """Apply a promo code for free access"""
    promo_code = data.promo_code.upper().strip()
    now = datetime.now(timezone.utc)
    
    promo = await db.promo_codes.find_one({
        "code": promo_code,
        "is_active": True
    }, {"_id": 0})
    
    if not promo:
        raise HTTPException(status_code=400, detail="Invalid or expired promo code")
    
    # Check if free_days type
    if promo.get("discount_type") == "free_days" and promo.get("trial_days", 0) > 0:
        trial_days = promo["trial_days"]
        trial_end = now + timedelta(days=trial_days)
        
        await db.tenants.update_one(
            {"id": current_user.tenant_id},
            {"$set": {
                "is_trial": True,
                "plan": "founders_edition",
                "trial_ends_at": trial_end.isoformat(),
                "promo_code_used": promo_code
            }}
        )
        
        await db.promo_codes.update_one(
            {"code": promo_code},
            {"$inc": {"times_used": 1}}
        )
        
        return {"success": True, "message": f"Success! You have {trial_days} days of free access."}
    
    raise HTTPException(status_code=400, detail="This promo code type requires checkout.")
```

### 7. Promo Codes Page - Free Days Type
**File:** `frontend/src/pages/PromoCodes.js`

Add to discount type select options:
```jsx
<SelectItem value="free_days">Free Access (No Payment)</SelectItem>
```

Add UI for free_days input:
```jsx
{formData.discount_type === 'free_days' && (
  <div>
    <Label>Free Access Days</Label>
    <Input
      type="number"
      value={formData.trial_days}
      onChange={(e) => setFormData({ ...formData, trial_days: parseInt(e.target.value) || 30 })}
    />
    <p className="text-xs text-muted">Grants full access - no payment required.</p>
  </div>
)}
```

### 8. Backend Promo Codes - Free Days Type
**File:** `backend/routes/promo_codes.py`

Update validation:
```python
if data.discount_type not in ['percent', 'fixed', 'free_trial', 'free_days']:
    raise HTTPException(status_code=400, detail="Invalid discount type")
```

Update trial_days assignment:
```python
"trial_days": data.trial_days if data.discount_type in ['free_trial', 'free_days'] else 0,
```

---

## MATERIALS & INVENTORY SYSTEM

### 9. Materials Settings Page
**NEW FILE:** `frontend/src/pages/MaterialsSettings.js`
(Full file is ~500 lines - see current codebase for complete implementation)

Key features:
- CRUD for custom materials
- Categories: vinyl, print_media, laminate, substrate, hardware, supplies
- Cost per unit, markup percentage, sell price calculation
- "Load Sign Shop Defaults" button

### 10. Materials Backend Endpoints
**File:** `backend/routes/pricing.py`

Add at end:
```python
@router.get("/materials/catalog")
async def get_materials_catalog(current_user = Depends(...)):
    query = {"tenant_id": current_user.tenant_id}
    return await db.materials.find(query, {"_id": 0}).to_list(500)

@router.post("/materials")
async def create_material(data: MaterialCreate, current_user = Depends(...)):
    # Create material with id, tenant_id, cost, markup, etc.

@router.put("/materials/{id}")
async def update_material(id: str, data: MaterialUpdate, current_user = Depends(...)):
    # Update material

@router.delete("/materials/{id}")
async def delete_material(id: str, current_user = Depends(...)):
    # Delete material

@router.post("/materials/seed-defaults")
async def seed_default_materials(current_user = Depends(...)):
    # Insert 32 default sign shop materials
```

### 11. App.js Route
**File:** `frontend/src/App.js`

Add import:
```javascript
import MaterialsSettings from "./pages/MaterialsSettings";
```

Add route:
```jsx
<Route path="/pricing-calculator/materials" element={<MaterialsSettings />} />
```

### 12. Pricing Calculator - Use Custom Materials
**File:** `frontend/src/components/PricingCalculator.js`

Add state and fetch:
```javascript
const [customMaterials, setCustomMaterials] = useState({...});

const fetchCustomMaterials = useCallback(async () => {
  const response = await fetch(`${API_URL}/api/pricing/materials/catalog`, {...});
  // Group by category and set state
}, []);

useEffect(() => {
  fetchCustomMaterials();
}, []);
```

Replace hardcoded VINYL_TYPES, PRINT_MATERIALS, SUBSTRATE_TYPES with functions that return custom materials or fallback to defaults.

---

## NAVIGATION UPDATES

### 13. Action Toolbar Links
**File:** `frontend/src/components/ribbon/ActionToolbar.js`

Add to ai-tools group:
```javascript
{ type: 'button', icon: FileDown, label: 'Documents', route: '/documents' },
```

Add to settings group:
```javascript
{ type: 'button', icon: UserCheck, label: 'Admin Portal', route: '/admin-portal' },
```

### 14. Settings Page - Pricing Link
**File:** `frontend/src/pages/CompanySettings.js`

Add Card section linking to pricing settings and materials.

---

## CORS Configuration (Keep Simple)

**File:** `backend/server.py`
```python
cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
cors_origins = [origin.strip().strip('"').strip("'") for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**File:** `backend/.env`
```
CORS_ORIGINS=https://signguy-ai.com,https://www.signguy-ai.com,http://localhost:3000
```

---

## REINSTATEMENT ORDER

1. **bcrypt==4.0.1** in requirements.txt (CRITICAL - login broken without)
2. **AI routes fix** - parameter naming (CRITICAL - AI broken without)
3. **CORS config** - simple version with your domains
4. **Soft delete** - for data safety
5. **Promo code updates** - for free access grants
6. **Materials system** - nice to have
7. **Navigation links** - nice to have

---

## QUICK TEST AFTER REINSTATEMENT

```bash
# Test login works
curl -X POST "https://YOUR_DOMAIN/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"thesigntistslab@gmail.com","password":"password123"}'

# Test AI works
curl -X POST "https://YOUR_DOMAIN/api/ai/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool":"pricing_advisor","input_data":{"test":"test"}}'
```
