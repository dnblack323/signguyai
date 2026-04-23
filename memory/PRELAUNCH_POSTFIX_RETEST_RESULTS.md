# Prelaunch Post-Fix Retest Results — Running Log

This is the **single running retest file** for checks executed **after code fixes**.

Last updated: 2026-04-23

---

## Tier 1 Retests

### 1.1 / 1.3 / 1.6 fixes retested
- ✅ **1.1B** Backup size threshold now passes (`55740 bytes`)
- ✅ **1.1C** Required legacy collection names now present (`missing=[]`)
- ✅ **1.3A** Subscription response now includes date field (`trial_end` populated)
- ✅ **1.6D** Empty import now returns validation error (`status=400`)
- ✅ **1.6K** Phone format search now returns results
- ✅ **1.6L** Phone format search now returns results
- ✅ **1.6M** Phone format search now returns results
- ✅ **1.6N** Phone format search now returns results
- ✅ **1.6O** Phone format search now returns results
- ✅ **1.6P** Invalid email row now skipped with explicit row error

Independent verification:
- ✅ Backend testing agent pass for targeted Section 1 fixes (`/app/test_reports/iteration_119.json`)

---

## Tier 2 Retests

### 2.3a Digital Print fixes retested
- ✅ **2.3aB** Lamination now increases sell price
  - API evidence: `no_lam sell=1048.5`, `yes_lam sell=1296.28`, `laminate_sell_addon=247.78`
  - UI evidence: `no_lam=$1000.00`, `lam_yes=$1247.78`

- ✅ **2.3aE** Design Complexity now appears when `Artwork Ready = No`
  - UI evidence: `design_visible_with_artwork_ready_false=true`

---

## Source artifacts
- `/app/memory/SECTION1_FIX_RETEST_RESULTS.json`
- `/app/test_reports/iteration_119.json`
- `/root/.emergent/automation_output/20260423_080029/console_20260423_080029.log`
