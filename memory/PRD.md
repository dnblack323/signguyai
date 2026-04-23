# SignGuy AI - Product Requirements Document

## Original Problem Statement
Full-stack business management app for sign/graphics shops: customer management, quoting, invoicing, job tracking, production workflow, employee time tracking, payroll, webstores with Stripe-powered checkout, and AI-driven business assistance.

## Core Modules
- **CRM / Quotes / Invoices / Jobs** — standard business workflow.
- **Production Workflow** — job tickets, production tasks, drawings, signatures.
- **Employee Portal + Timeclock + Payroll** — punch tracking, shift state, payroll worksheets.
- **Webstores** — per-tenant storefronts, products, Stripe Checkout via Connect, orders → jobs.
- **AI Business Assistant** — Phase 5 (saved commands, routines, modes, bulk action previews).
- **Stripe Connect (platform-owned) + Stripe Connect (tenant onboarding)** — platform billing + tenant payouts.

## Implemented (CHANGELOG)

### 2026-04-23 — Payroll/timeclock stabilization + payroll controls
- Fixed recurring payroll worksheet break-loss behavior by merging same-day shifts in `frontend/src/lib/payrollWorksheet.js` and preserving break deductions even when lunch fields are blank.
- Added lunch field persistence for timeclock break actions in `backend/services/timeclock_service.py` (`lunch_start` on break start, `lunch_end` on break end).
- Fixed payroll shift edit API to accept explicit null lunch values (`exclude_unset=True`) so admins can clear/edit breaks reliably.
- Added `POST /api/payroll/mark-paid-in-full` in `backend/routes/employees.py` to create/update period-scoped payment transactions with official paid amount.
- Added top-toolbar "Paid in Full" amount input + action button in `frontend/src/components/payroll/PayrollWorksheetToolbar.js` and wired flow in `frontend/src/pages/Payroll.js`.
- Added tenant payroll setting `show_payroll_adjustments` (default `false`) in `backend/models/auth.py` and `frontend/src/pages/CompanySettings.js`, with conditional panel rendering in payroll page.
- Verified by testing agent: `/app/test_reports/iteration_123.json` (backend 14/14 pass, frontend checks pass).

### 2026-04-22 — Stripe Connect mode-safety hardening
- Added `_scrub_stale_connect_account()` + `_is_wrong_mode_error()` helpers in `routes/stripe_connect.py`.
- `/stripe-connect/status` auto-scrubs test-mode Connect accounts lingering on a live platform and records audit trail (`stripe_connect_scrubbed_at/_reason/_account_id`).
- `/stripe-connect/create-account` refuses to save test-mode accounts on a live platform (defense in depth).
- `/stripe-connect/refresh-link` returns 409 with friendly copy when account is stale/wrong-mode, instead of a broken onboarding URL.
- `account_mode` detection now distinguishes `livemode=None` (unactivated live) from `livemode=False` (actual test) — fixes false `mode_mismatch` on fresh live accounts.
- Frontend `PaymentSettings.js` auto-refreshes status on 409 so UI recovers cleanly.
- Verified end-to-end: ghost `acct_1TP6Je0f4QWGY8c6` successfully scrubbed; live `acct_1TP6XF1JC1SdQUDo` recognized correctly.

### Earlier this session
- AI Business Assistant Phase 5 frontend integration.
- Webstore backend hardening (W1–W17): cross-tenant leaks, permission gaps, payout inflation, idempotency, Stripe caching, base64 image migration to object storage.
- Prelaunch checklist: 24 items tested and checked off.
- Timeclock display bug: canonical `clock_in` instead of `updated_at`.
- Dashboard clocked-in widget: removed UTC date regex (was dropping cross-midnight workers).
- Payroll print CSS: outline font stack fixed.
- `PayrollTransaction`: tenant_id scoping + Pydantic validation.
- Webstore frontend empty-state/filter-trap fix.
- Stripe Checkout Flow B rewrite — unified order recording into `webstore_orders_v2`, secure webhook handling, 9 bugs fixed.

## Roadmap (P0 → P3)

### P2 — Upcoming
- Easy Artwork sharing to Customer Portal from order details.
- AI receipt analysis for uploaded expense photos.
- Tax-exempt toggle behavior validation/fix (`2.1F`).
- Assets-panel artwork attach + thumbnail path fix (`2.2E`).

### P2 — Backlog
- Deduplicate payroll compensation snapshot hours (`_get_employee_compensation_snapshot` sums job+manual+clock without dedupe; needs product decision).

### P3 — Future
- Team / Workforce Ribbon rebuild (on hold).
- Optional: UI banner before Connect click reminding tenants to close old Stripe tabs.

## Key Files
- `backend/routes/stripe_connect.py` — Connect onboarding, webhooks, checkout.
- `backend/routes/webstores.py` — webstore CRUD, unified order creation.
- `backend/routes/employees.py` — payroll transactions, snapshots.
- `backend/services/timeclock_service.py` — punch handling, shift state.
- `frontend/src/lib/payrollWorksheet.js` — worksheet row merge + break calculations.
- `frontend/src/pages/Payroll.js` — worksheet save logic + paid-in-full flow.
- `frontend/src/components/payroll/PayrollWorksheetToolbar.js` — top-area payroll actions.
- `frontend/src/pages/CompanySettings.js` — payroll settings toggles.
- `frontend/src/pages/Admin/PaymentSettings.js` — Connect UI.
- `frontend/src/pages/Webstores.js` — admin dashboard.
- `frontend/src/pages/Storefront.js` — public storefront + checkout.

## Integrations
- **Stripe** — Live keys (`sk_live_…`). Platform account activated with Connect.
- **Emergent LLM Key** — OpenAI / Gemini / Claude via `emergentintegrations`.

## Test Credentials
See `/app/memory/test_credentials.md`.
