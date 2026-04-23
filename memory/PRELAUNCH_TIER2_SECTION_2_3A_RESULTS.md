# Tier 2 — Section 2.3a Results (Digital Print)

Run timestamp: `2026-04-23T07:05:25Z`  
Environment: `REACT_APP_BACKEND_URL` (production preview URL)

Fix/retest timestamp: `2026-04-23T08:00:29Z`

---

- ✅ **2.3aA** Width/height/quantity scaling behavior validated for area-based pricing
  - Evidence: at qty=1, `60x60 -> $250.00`, `120x120 -> $1000.00` (4.00x for 4.00x area)

- ✅ **2.3aB** Lamination add-on now increases price
  - Retest evidence (API): `no_lam sell=1048.5`, `yes_lam sell=1296.28`, `laminate_sell_addon=247.78`
  - Retest evidence (UI): `no_lam=$1000.00`, `lam_yes=$1247.78`

- ✅ **2.3aC** Quantity tiers reduced effective per-unit price
  - Evidence (UI): totals `50=$45,000`, `250=$212,500`, `500=$425,000`
  - Per-unit: `50=$900.00`, `250=$850.00`, `500=$850.00` (decreasing / non-increasing)

- ✅ **2.3aD** Rush toggle applies end-of-calculation adder
  - Evidence: `rush=false -> $85,000.00`, `rush=true -> $106,250.00`

- ✅ **2.3aE** Progressive disclosure now matches checklist expectation
  - Retest evidence: with `Artwork Ready = No`, `Design Complexity` field is visible immediately (`true`)

---

Artifacts:
- UI automation console: `/root/.emergent/automation_output/20260423_070525/console_20260423_070525.log`
- Screenshot: `/tmp/tier2_section2_3a.jpg`
- Setup reference: `/app/memory/TIER2_SECTION_2_3A_SETUP.json`

Retest artifacts:
- UI automation console: `/root/.emergent/automation_output/20260423_080029/console_20260423_080029.log`
- Retest screenshot: `/tmp/tier2_2_3_fix_retest.jpg`
