# TIER_CONFIG.PY DEPRECATION - CHANGE PLAN

**Created:** December 2025  
**Status:** READY FOR EXECUTION  
**Decision:** `plan_configs.py` + `multi_product_gate.py` are authoritative. `tier_config.py` is LEGACY.

---

## 1. LEGACY USAGE INVENTORY

### Files with Direct tier_config.py Imports

| File | Line | Import/Usage |
|------|------|--------------|
| `services/feature_gate.py` | 15 | `from services.tier_config import get_tier_config, TIER_CONFIGS` |
| `routes/tiers.py` | 19 | `from services.tier_config import get_all_tiers, get_tier_config` |

### Files with models/tiers.py Imports (Used by tier_config.py)

| File | Line | Import/Usage |
|------|------|--------------|
| `services/tier_config.py` | 7-14 | `from models.tiers import TierLevel, TierConfig, TierFeatures, FeatureValue, FeatureStatus...` |
| `services/feature_gate.py` | 11-14 | `from models.tiers import TierLevel, FeatureStatus, FeatureValue, FeatureCheckResult, TenantUsage, UsageType` |
| `routes/tiers.py` | 15-17 | `from models.tiers import TierLevel, TierConfig, FeatureCheckResult, TenantUsage` |
| `models/__init__.py` | 54-61 | Re-exports `TierLevel, FeatureStatus, FeatureValue, TierFeatures, TierConfig...` |

### Usage of Legacy Objects at Runtime

| File | Function | Legacy Call | Line |
|------|----------|-------------|------|
| `services/feature_gate.py` | `get_feature_value()` | `get_tier_config(tier)` | 44 |
| `services/feature_gate.py` | `get_tenant_features()` | `get_tier_config(tier)` | 155 |
| `services/feature_gate.py` | `set_tenant_tier()` | `get_tier_config(tier)` | 258 |
| `routes/tiers.py` | `get_subscription_plans()` | `get_all_tiers()` | 74 |
| `routes/tiers.py` | `get_full_tier_config()` | `get_tier_config(tier_level)` | 230 |
| `routes/tiers.py` | `get_upgrade_prompt()` | `get_tier_config(tier_level)` | 297, 308 |

---

## 2. CHANGE PLAN

### Step 1: Update `services/feature_gate.py`

**Current:**
```python
from models.tiers import (
    TierLevel, FeatureStatus, FeatureValue, FeatureCheckResult,
    TenantUsage, UsageType
)
from services.tier_config import get_tier_config, TIER_CONFIGS
```

**Change To:**
```python
from models.product_tiers import (
    PlanType, FeatureStatus, FeatureValue, FeatureCheckResult,
    TenantUsage, TierLevel
)
from services.plan_configs import get_plan_config, legacy_tier_to_plan, PLAN_CONFIGS
```

**Function Changes:**
- `get_tenant_tier()` → `get_tenant_plan()` returning `PlanType`
- `get_tier_config(tier)` → `get_plan_config(plan_type)`
- `set_tenant_tier()` → `set_tenant_plan()`
- Update `_update_usage_limits()` to use new feature path structure

### Step 2: Update `routes/tiers.py`

**Current:**
```python
from models.tiers import (
    TierLevel, TierConfig, FeatureCheckResult, TenantUsage
)
from services.tier_config import get_all_tiers, get_tier_config
```

**Change To:**
```python
from models.product_tiers import (
    PlanType, PlanConfig, FeatureCheckResult, TenantUsage, TierLevel
)
from services.plan_configs import get_all_plans, get_plan_config, get_plans_by_product_line
```

**Function Changes:**
- `get_subscription_plans()`: Use `get_all_plans()` instead of `get_all_tiers()`
- `_get_tier_highlights()`: Update to use `PlanConfig` structure
- `get_full_tier_config()`: Map `tier` string to `PlanType`, use `get_plan_config()`
- `set_tenant_tier()`: Accept `plan_type` string, use `PlanType` enum
- `get_upgrade_prompt()`: Iterate `PlanType` values for OS plans

### Step 3: Update `models/__init__.py`

**Current (lines 54-61):**
```python
from .tiers import (
    TierLevel, FeatureStatus, FeatureValue, TierFeatures, TierConfig,
    UsageType, TenantUsage, FeatureCheckResult,
    ...
)
```

**Change To:**
```python
# Legacy tier models - DEPRECATED, use product_tiers
from .tiers import (
    TierLevel, FeatureStatus, FeatureValue, TierFeatures, TierConfig,
    UsageType, TenantUsage, FeatureCheckResult,
    ...
)

# Authoritative tier models
from .product_tiers import (
    ProductLine, PlanType, PlanConfig, PlanPricing, ProcessingFees,
    PlanFeatures, FeatureCheckResult as PlanFeatureCheckResult,
    TenantUsage as PlanTenantUsage, FounderStatus
)
```

### Step 4: Deprecate `services/tier_config.py`

Add header comment:
```python
"""
=============================================================================
LEGACY - DO NOT USE
=============================================================================
This module has been replaced by:
  - services/plan_configs.py (plan definitions)
  - services/multi_product_gate.py (feature gating logic)
  - models/product_tiers.py (data models)

All new code MUST use the above modules.
This file is retained ONLY for backwards compatibility during migration.
=============================================================================
"""
```

---

## 3. MIGRATION MAPPING

### Enum Mapping
| Legacy (tier_config) | New (plan_configs) |
|---------------------|-------------------|
| `TierLevel.STARTER` | `PlanType.OS_STARTER` |
| `TierLevel.PRO` | `PlanType.OS_PRO` |
| `TierLevel.BUSINESS` | `PlanType.OS_BUSINESS` |

### Function Mapping
| Legacy Function | New Function |
|----------------|--------------|
| `get_tier_config(tier: TierLevel)` | `get_plan_config(plan: PlanType)` |
| `get_all_tiers()` | `get_all_plans()` |
| `TIER_CONFIGS` dict | `PLAN_CONFIGS` dict |

### Feature Path Mapping
| Legacy Path | New Path |
|-------------|----------|
| `config.features.ai_tools.monthly_generations` | `config.features.ai_tools.monthly_generations` |
| `config.features.ai_assistant.natural_language` | `config.features.ai_assistant.monthly_queries` |
| `config.features.team.team_members` | `config.features.core.employees` |
| `config.features.webstores.num_stores` | `config.features.webstores.num_stores` |
| `config.features.webstores.product_images` | N/A (removed) |
| `config.features.data.storage_mb` | `config.features.customer_portal.document_storage_mb` |
| `config.features.data.retention_years` | N/A (removed) |

---

## 4. FILES TOUCHED

### Will Be Modified
1. `/app/backend/services/feature_gate.py` - Migrate to plan_configs
2. `/app/backend/routes/tiers.py` - Migrate to plan_configs
3. `/app/backend/models/__init__.py` - Add product_tiers exports
4. `/app/backend/services/tier_config.py` - Add deprecation header

### Intentionally NOT Modified
1. `/app/backend/models/tiers.py` - Kept for backwards compat, no runtime change
2. `/app/backend/services/plan_configs.py` - Already authoritative, no change
3. `/app/backend/services/multi_product_gate.py` - Already authoritative, no change
4. `/app/backend/models/product_tiers.py` - Already authoritative, no change
5. All frontend files - No backend tier changes affect frontend
6. All other route files - They don't import tier_config directly

---

## 5. REGRESSION CHECKLIST

### Plan Selection / Tenant Plan Read
- [ ] `GET /api/tiers/my-plan` returns correct plan info
- [ ] `GET /api/tiers/plans` returns all 9 plans (not just 3 legacy)
- [ ] Legacy tier names (`starter`, `pro`, `business`) still map correctly
- [ ] New plan names (`os_starter`, `ws_launch`, `ai_basic`) work correctly

### Feature Gates ON/OFF/LIMITED
- [ ] `GET /api/tiers/check/{category}/{feature}` returns correct status
- [ ] OS_STARTER users cannot access `payroll` (OFF)
- [ ] OS_PRO users can access `time_clock` (ON)
- [ ] AI_BASIC users cannot access `image_generation` (OFF)
- [ ] LIMITED features return correct limit values

### Usage Tracking Limits Updates on Plan Change
- [ ] `PUT /api/tiers/admin/tenant/{id}/tier` updates plan
- [ ] Usage limits update when plan changes (e.g., ai_tools.monthly_generations)
- [ ] Usage counters preserved on upgrade (not reset)
- [ ] `POST /api/tiers/admin/tenant/{id}/reset-usage` still works

### UI Visibility Flags
- [ ] `show_jobs_ui` correct per plan
- [ ] `show_payroll_ui` correct per plan
- [ ] `show_time_clock_ui` correct per plan
- [ ] `show_financials_ui` correct per plan
- [ ] `show_ai_assistant_ui` correct per plan

### Processing Fees Calculation
- [ ] Invoice fee % correct per plan
- [ ] Webstore fee % correct per plan
- [ ] Founder annual discount applied for OS_BUSINESS

### Upgrade Prompts
- [ ] `GET /api/tiers/upgrade-prompt/{category}/{feature}` returns valid upgrade path
- [ ] Upgrade prompt shows correct target plan price

---

## 6. EXECUTION ORDER

1. Add deprecation header to `tier_config.py` (no runtime impact)
2. Update `models/__init__.py` to export product_tiers models
3. Update `services/feature_gate.py` to use plan_configs
4. Update `routes/tiers.py` to use plan_configs
5. Run regression tests
6. Verify all endpoints work

---

## 7. ROLLBACK PLAN

If issues occur:
1. Revert changes to `feature_gate.py` and `routes/tiers.py`
2. Remove product_tiers exports from `models/__init__.py`
3. Keep deprecation header in `tier_config.py` (informational only)

---

*Document created per user request. Ready for execution approval.*
