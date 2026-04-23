# Prelaunch Pretesting Results — Master Running Log

This is the **single running pretesting file** (before fixes).  
Going forward, new pretesting will be appended here in checklist order.

Last updated: 2026-04-23

---

## Tier 1

### 1.1 Backup & Restore (pre-fix first pass)
- ✅ **1.1A** Export JSON endpoint returned 200
- ❌ **1.1B** Backup size below threshold on first pass (`32944 bytes`)
- ❌ **1.1C** Missing expected legacy collection names on first pass (`orders`, `order_items`, `payroll_transactions`, `timeclock_shifts`)
- ✅ **1.1I** Backup status returned recent `last_backup_at`
- ✅ **1.1J** Scheduler activity observed (`check_and_send_digests`)
- ✅ **1.1K** No plaintext passwords detected

### 1.2 Authentication & Isolation (tested subset)
- ✅ **1.2C** Login success
- ✅ **1.2D** Wrong-password attempts handled; valid login still works
- ✅ **1.2G** Logout redirects protected route access to `/login`

### 1.3 Stripe Billing (tested subset)
- ❌ **1.3A** First pass lacked renewal/trial date response fields (`current_period_end=None`, `trial_end=None`)

### 1.4 Stripe Connect (tested subset)
- ❌ **1.4B** Status not fully enabled (`charges_enabled=false`, `payouts_enabled=false`, `onboarding_complete=false`)

### 1.5 Credits (tested subset)
- ✅ **1.5A** Balance endpoint healthy
- ✅ **1.5C** Credit decrement verified after API usage
- ✅ **1.5F** Credit history entries present with action names

### 1.6 CSV Import (pre-fix first pass)
- ✅ **1.6A** Minimal import
- ✅ **1.6B** Full-field import
- ✅ **1.6C** Duplicate re-import behavior
- ❌ **1.6D** Empty payload did not error on first pass
- ✅ **1.6E** Missing-name row rejected
- ✅ **1.6F** Unicode: José García
- ✅ **1.6G** Unicode: 北京客户
- ✅ **1.6H** Unicode: O'Brien
- ✅ **1.6I** Unicode: Müller & Söhne
- ✅ **1.6J** 500+ import performance passed
- ❌ **1.6K** Phone search format `(415) 555-1234` failed on first pass
- ❌ **1.6L** Phone search format `415.555.1234` failed on first pass
- ❌ **1.6M** Phone search format `415-555-1234` failed on first pass
- ❌ **1.6N** Phone search format `+1 415 555 1234` failed on first pass
- ❌ **1.6O** Phone search format `+14155551234` failed on first pass
- ❌ **1.6P** Invalid email row was not rejected on first pass
- ❌ **1.6Q** Mid-batch validation failure left partial inserts

---

## Tier 2

### 2.1 Customers CRUD (first pass)
- ✅ **2.1A** Create customer
- ✅ **2.1B** Search by name/email/phone
- ✅ **2.1C** Edit persistence
- ✅ **2.1D** Delete customer preserves historical order customer name
- ✅ **2.1E** Summary/detail data paths
- ❌ **2.1F** Tax-exempt behavior not observable (non-exempt and exempt paths both tax=0)
- ⛔ **2.1G** Requires inbox + end-user portal verification

### 2.2 Orders Quick Entry (first pass)
- ✅ **2.2A** New order page + autocomplete
- ✅ **2.2B** Customer populate
- ✅ **2.2C** Quick-item estimate updates
- ✅ **2.2D** Shared context persistence
- ❌ **2.2E** Assets-panel upload/thumbnail path failed in run
- ✅ **2.2F** Draft save + draft filter
- ✅ **2.2G** Non-draft ORD number assignment
- ✅ **2.2H** Reopen/reload round-trip
- ✅ **2.2I** Delete order flow
- ✅ **2.2J** No duplicate live estimate panel
- ✅ **2.2K** Add-item menu options/disabled states

### 2.3a Digital Print (first pass before fixes)
- ✅ **2.3aA** Area-based scaling behavior
- ❌ **2.3aB** Lamination had no price effect in first pass
- ✅ **2.3aC** Quantity tier per-unit behavior
- ✅ **2.3aD** Rush adder behavior
- ❌ **2.3aE** Design complexity visibility condition differed from checklist on first pass

### 2.3b Cut Vinyl (first pass)
- ✅ **2.3bA** Vinyl type changes baseline pricing
  - Evidence (API): `oracal_651=24.0`, `oracal_751=30.0`, `reflective_vinyl=44.0`
- ✅ **2.3bB** Size + color count increases price
  - Evidence (API): `24x12,1color=24.0` → `48x24,1color=96.0` → `48x24,3color=192.0`
- ✅ **2.3bC** `Install Required = No` hides Install Complexity
  - Evidence (UI): `install_complexity_visible_count=0`
- ✅ **2.3bD** `Install Required = Yes` shows Install Complexity and increases sell
  - Evidence (UI): `before=96.0`, `after=246.0`, `install_complexity_visible_count=1`
- ✅ **2.3bE** `Artwork Ready = No` shows Design Complexity
  - Evidence (UI): `design_complexity_visible_count=1`
- ❌ **2.3bF** Duplicate item behavior mismatch
  - Evidence (API `/job-tickets/{id}/duplicate`): source qty `5` duplicated as qty `5` (expected reset to `1`); duplicate name unchanged (expected `Copy of ...`)

### 2.3c Rigid Signs (first pass)
- ✅ **2.3cA** Material + thickness changes baseline pricing
  - Evidence (API): `coroplast_4mm=128.5`, `acm_dibond_3mm_4mm=240.5`, `acm_dibond_3mm_1/2=278.9`
- ✅ **2.3cB** Sidedness single hides double-sided art field
- ✅ **2.3cC** Sidedness double shows double-sided art field
- ✅ **2.3cD** Hardware off hides Hardware Type + Drill Prep fields
- ✅ **2.3cE** Hardware on shows both fields
- ✅ **2.3cF** Install off hides Install Complexity
- ✅ **2.3cG** Install on shows Install Complexity
- ✅ **2.3cH** Protective finish off hides Finish Type
- ✅ **2.3cI** Protective finish on shows Finish Type
- ✅ **2.3cJ** Artwork Ready = No shows Design Complexity

### 2.3d Banners (first pass)
- ✅ **2.3dA** Banner material selection changes baseline pricing
  - Evidence (API): `banner_13oz=257.0`, `banner_18oz=305.0`
- ✅ **2.3dB** Grommets=None hides custom grommet count field
- ✅ **2.3dC** Grommet standard option adds grommet charge
  - Evidence (API): `none=257.0`, `corners=261.0`
- ✅ **2.3dD** Custom grommet count scales pricing
  - Evidence (API): `custom4=261.0`, `custom20=272.0`
- ✅ **2.3dE** Pole pockets option adds charge
  - Evidence (API): `none=257.0`, `top_and_bottom=313.0`
- ✅ **2.3dF** Wind slits option adds charge
  - Evidence (API): `wind_no=257.0`, `wind_yes=259.0`
- ✅ **2.3dG** Install required shows Install Complexity and increases price
  - Evidence (UI/API): install complexity visible + `install_no=257.0`, `install_yes=395.7`

---

## Source artifacts
- `/app/memory/SECTION1_AGENT_EXECUTION_RESULTS.json`
- `/app/memory/PRELAUNCH_TIER2_SECTION_2_1_RESULTS.md`
- `/app/memory/PRELAUNCH_TIER2_SECTION_2_2_RESULTS.md`
- `/app/memory/PRELAUNCH_TIER2_SECTION_2_3A_RESULTS.md`
- `/app/memory/TIER2_SECTION_2_3B_API_RESULTS.json`
- `/app/memory/TIER2_SECTION_2_3B_DUPLICATE_RESULTS.json`
- `/root/.emergent/automation_output/20260423_092005/console_20260423_092005.log`
- `/app/memory/TIER2_SECTION_2_3CD_API_RESULTS.json`
- `/root/.emergent/automation_output/20260423_094031/console_20260423_094031.log`
