# Prelaunch — Section 1 Failed Items (Later Testing Queue)

Only items that are still **open after fixes/retests** are listed here.
Numbering preserves original Tier/Section/Letter format.

---

## Tier 1 → Section 1.4 Stripe Connect (Merchant Payouts)

- [ ] **1.4B** Connect status not fully enabled (`charges_enabled=false`, `payouts_enabled=false`, `onboarding_complete=false`)
  - Evidence: `GET /api/stripe-connect/status`
  - Next test focus: finish onboarding, then re-check flags

## Tier 1 → Section 1.6 CSV Customer Import

- [ ] **1.6Q** Mid-batch failure leaves partial data (no atomic rollback)
  - Current state: runtime-exception rollback is implemented; validation-row errors still use skip-and-continue behavior
  - Next test focus: decide desired product behavior between strict all-or-nothing vs partial import with row errors

## Tier 2 → Section 2.1 Customers CRUD

- [ ] **2.1F** Tax-exempt toggle should affect invoice tax calculation
  - Evidence: non-exempt and exempt invoice-generation paths both produced `tax_amount=0`
  - Next test focus: implement customer-aware tax calculation (or document global zero-tax policy)

## Tier 2 → Section 2.2 Orders — Quick Entry

- [ ] **2.2E** Attach artwork drag-and-drop/assets-panel thumbnail path
  - Evidence: Section 2.2 automation run returned `asset_row_count=0`, `thumbnail_images=0` for assets-panel upload check
  - Next test focus: verify assets panel upload wiring (and/or implement explicit drag-and-drop + thumbnail rendering in this panel)

## Tier 2 → Section 2.3a Digital Print

- [ ] **2.3aB** Lamination should increase Digital Print price
  - Evidence: `laminate=false` and `laminate=true` returned identical selling prices in UI and `/api/pricing/calculate`
  - Next test focus: wire laminate material cost into digital_print pricing calculation (`laminate` + `laminate_material_key`)

- [ ] **2.3aE** Design Complexity progressive disclosure condition
  - Evidence: field appeared only when `artwork_needed=true`, not simply when `artwork_ready=false`
  - Next test focus: decide expected UX rule (checklist says Artwork Ready=No should reveal; current schema uses Artwork Needed=Yes)
