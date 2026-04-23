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
