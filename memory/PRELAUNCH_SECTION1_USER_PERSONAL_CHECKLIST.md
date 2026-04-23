# Prelaunch — User Personal Checklist (Section 1 Only)

This file contains only the Section 1 items that require **your personal verification** (email inbox, Stripe dashboard actions, long-duration checks, or clean-tenant/live-production actions).

Numbering format is preserved as requested: `Tier.SectionLetter` (example: `1.1A`, `1.1B`).

---

## Tier 1 → Section 1.1 Backup & Restore

- [ ] **1.1D** On a clean test tenant, upload backup and verify **Preview Restore** shows row counts without writing
- [ ] **1.1E** On test tenant, click **Restore** and confirm completion toast
- [ ] **1.1F** Log out/in after restore and confirm all expected data is visible
- [ ] **1.1G** Refresh Orders page and confirm all orders render
- [ ] **1.1H** Open restored order and verify artwork/drawing previews still resolve
- [ ] **1.1L** Take a live production backup before wider launch testing

## Tier 1 → Section 1.2 Authentication & Multi-Tenant Isolation

- [ ] **1.2A** Sign up with a brand-new email and confirm verification email arrives within 60s
- [ ] **1.2B** Open verification link and confirm account activation
- [ ] **1.2E** Forgot Password email arrives, reset link works, and reset completes
- [ ] **1.2F** Old password is rejected and new password is accepted after reset
- [ ] **1.2H** Create a second tenant with different email
- [ ] **1.2I** Tenant B `GET /api/customers` returns empty array (not Tenant A data)
- [ ] **1.2J** Tenant B direct fetch of Tenant A order returns 403/404 (never data)
- [ ] **1.2K** Staff cannot access `/payroll`, `/settings`, `/billing`, `/users`
- [ ] **1.2L** Staff can access `/orders`, `/customers`, `/dashboard`
- [ ] **1.2M** JWT/session expiry check after 25+ hours idle
- [ ] **1.2N** Email-change flow requires new-email verification

## Tier 1 → Section 1.3 Stripe Billing (Platform Subscriptions)

- [ ] **1.3A** Billing UI shows current plan and renewal date correctly
- [ ] **1.3B** Upgrade with Stripe checkout and verify success path
- [ ] **1.3C** Declined card path shows graceful error and no plan upgrade
- [ ] **1.3D** 3DS-required card flow completes and upgrades plan after approval
- [ ] **1.3E** Credit top-up purchase updates navbar balance after webhook
- [ ] **1.3F** Cancel at period end is correctly reflected in Stripe and app access behavior
- [ ] **1.3G** Webhook replay from Stripe dashboard is processed correctly
- [ ] **1.3H** Promo code/coupon applies correctly in checkout
- [ ] **1.3I** Stripe invoice PDF download matches charged amount

## Tier 1 → Section 1.4 Stripe Connect (Merchant Payouts)

- [ ] **1.4A** Complete Stripe Connect onboarding from Payment Settings
- [ ] **1.4B** Confirm status has `connected=true`, `charges_enabled=true`, `payouts_enabled=true`
- [ ] **1.4C** Stripe Express dashboard link opens and works
- [ ] **1.4D** Customer payment routes to connected merchant balance
- [ ] **1.4E** Stripe Connect balance reflects payment minus fees
- [ ] **1.4F** Stripe dashboard refund syncs invoice to `refunded` in SignGuy
- [ ] **1.4G** Disconnect path works and fallback payment behavior is correct
- [ ] **1.4H** Reconnect works cleanly without duplicate-account errors

## Tier 1 → Section 1.5 Credits System

- [ ] **1.5A** Navbar visibly shows current credit balance in your normal UI usage
- [ ] **1.5B** Buy 100/300/1000 packs and confirm webhook-driven balance updates
- [ ] **1.5D** Drive balance to 0 and verify HTTP 402 + friendly UI upgrade prompt
- [ ] **1.5E** Auto top-up triggers when below threshold
- [ ] **1.5G** Founders monthly allotment refills on billing anniversary
- [ ] **1.5H** Free-tier users cannot bypass credit gating in network flow

## Tier 1 → Section 1.6 CSV Customer Import

- [ ] **1.6R** Export customers CSV, re-import into a clean tenant, and confirm round-trip integrity (no duplicates/data loss)
