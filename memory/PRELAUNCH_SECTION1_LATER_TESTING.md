# Prelaunch — Section 1 Failed Items (Later Testing Queue)

Only items that **failed during agent execution** are listed here.
Numbering preserves original Tier/Section/Letter format.

---

## Tier 1 → Section 1.1 Backup & Restore

- [ ] **1.1B** Backup file size threshold failed (`32944 bytes`, expected > 50KB)
  - Evidence: export payload size check
  - Next test focus: confirm data volume expectation vs threshold policy

- [ ] **1.1C** Required collection names mismatch (`orders/order_items/payroll_transactions/timeclock_shifts` not present)
  - Evidence: export `collections` key set differs from checklist naming
  - Next test focus: schema mapping decision (`jobs` vs `orders`, etc.)

## Tier 1 → Section 1.3 Stripe Billing (Platform Subscriptions)

- [ ] **1.3A** Plan/renewal date check failed (`plan=free_trial`, no period/trial date returned)
  - Evidence: `GET /api/billing/subscription`
  - Next test focus: subscription response contract for free-trial tenants

## Tier 1 → Section 1.4 Stripe Connect (Merchant Payouts)

- [ ] **1.4B** Connect status not fully enabled (`charges_enabled=false`, `payouts_enabled=false`, `onboarding_complete=false`)
  - Evidence: `GET /api/stripe-connect/status`
  - Next test focus: finish onboarding, then re-check flags

## Tier 1 → Section 1.6 CSV Customer Import

- [ ] **1.6D** Empty import payload did not return clear error (`200`, created=0)
  - Evidence: `/api/customers/import` with empty list
  - Next test focus: enforce explicit validation error for no-data imports

- [ ] **1.6K** Phone search failed for `(415) 555-1234`
- [ ] **1.6L** Phone search failed for `415.555.1234`
- [ ] **1.6M** Phone search failed for `415-555-1234`
- [ ] **1.6N** Phone search failed for `+1 415 555 1234`
- [ ] **1.6O** Phone search failed for `+14155551234`
  - Evidence: `/api/customers?search=<phone>` returned no matches
  - Next test focus: include phone in backend search query (or document expected behavior)

- [ ] **1.6P** Invalid email row not skipped (imported as valid)
  - Evidence: `created=2`, `errors=[]` for one invalid + one valid row
  - Next test focus: add email format validation in import flow

- [ ] **1.6Q** Mid-batch failure leaves partial data (no atomic rollback)
  - Evidence: rows created despite one invalid row in middle
  - Next test focus: transaction-like behavior or staged validation before insert
