# Prelaunch Open Items Tracker — Failures & Cannot-Fully-Test Items

This is the **single running unresolved-items file**.

Use categories:
- ❌ Failed and still open
- ⛔ Cannot fully test without user/external actions

Last updated: 2026-04-23

---

## ❌ Failed and still open

### Tier 1

#### 1.4 Stripe Connect
- **1.4B** Connect status not fully enabled (`charges_enabled=false`, `payouts_enabled=false`, `onboarding_complete=false`)
  - Next: complete Stripe Connect onboarding and re-check status endpoint

#### 1.6 CSV Import
- **1.6Q** Mid-batch validation failure still leaves partial inserts by design (runtime exceptions rollback; row-validation remains partial-skip)
  - Next: product decision required (strict atomic import vs row-level partial import)

### Tier 2

#### 2.1 Customers CRUD
- **2.1F** Tax-exempt toggle not reflected in tested invoice tax behavior
  - Evidence: non-exempt and exempt paths both produced tax=0 in tested flow
  - Next: implement or document customer-aware tax policy

#### 2.2 Orders Quick Entry
- **2.2E** Assets-panel upload/thumbnail path failed in tested run
  - Evidence: `asset_row_count=0`, `thumbnail_images=0`
  - Next: verify assets panel upload + listing wiring

#### 2.3b Cut Vinyl
- **2.3bF** Duplicate item should reset quantity to 1 and keep category as Cut Vinyl
  - Evidence: current `/api/job-tickets/{id}/duplicate` preserves original quantity and name
  - Next: align duplicate flow to checklist contract (qty reset=1 + `Copy of ...` naming), or update checklist contract to current behavior

---

## ⛔ Cannot fully test without user/external actions

### Tier 1 (personal verification / inbox / clean-tenant / Stripe dashboard)
- **1.1D, 1.1E, 1.1F, 1.1G, 1.1H, 1.1L** (restore on clean tenant + live backup action)
- **1.2A, 1.2B, 1.2E, 1.2F, 1.2H, 1.2I, 1.2J, 1.2K, 1.2L, 1.2M, 1.2N**
- **1.3B, 1.3C, 1.3D, 1.3E, 1.3F, 1.3G, 1.3H, 1.3I**
- **1.4A, 1.4C, 1.4D, 1.4E, 1.4F, 1.4G, 1.4H**
- **1.5B, 1.5D, 1.5E, 1.5G, 1.5H**
- **1.6R**

### Tier 2 (external/email/mobile/manual dependency)
- **2.1G** (portal invite email + end-user login)
- **2.5C, 2.5I, 2.5J, 2.5K, 2.5L, 2.5M**
- **2.7N, 2.7R**
- **2.9L**
- **2.10E**

---

## Source references
- `/app/memory/PRELAUNCH_SECTION1_USER_PERSONAL_CHECKLIST.md`
- `/app/memory/PRELAUNCH_SECTION1_LATER_TESTING.md`
