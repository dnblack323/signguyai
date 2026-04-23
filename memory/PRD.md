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

### 2026-04-23 — Features page screenshot lightbox
- Added click-to-enlarge behavior for feature screenshots on `/features` in `frontend/src/pages/FeaturesPage.js`.
- Each screenshot card now shows a "Click to enlarge" hint and opens a full-screen modal with enlarged image + feature title.
- Lightbox supports both close button and click-outside-to-close interactions.
- Verified desktop + mobile behavior via frontend test agent; no layout regressions.

### 2026-04-23 — Default feature screenshots made taller/readable
- Recaptured all `frontend/public/screenshots/feature_*.jpeg` marketing assets at **1920x1200 (16:10)** instead of short wide-strip framing.
- This increases default on-page screenshot height and improves text readability before opening lightbox.
- Re-verified: all feature images load successfully, lightbox still works, and no desktop/mobile overflow regressions.

### 2026-04-23 — Features page screenshot refresh with real data states
- Replaced/recaptured marketing feature screenshots using live preview tenant data for core admin modules (dashboard, customers, orders, pricing, invoices, payroll, payments, reporting, settings, productivity, webstores, AI tools, intake forms).
- Added dedicated portal screenshots with real account states:
  - `feature_customer_portal.jpeg` from active customer portal dashboard (orders/invoices visible)
  - `feature_employee_portal.jpeg` from active employee portal dashboard (clock/pay/tasks visible)
- Updated `frontend/src/pages/FeaturesPage.js` image mapping to use new context-specific assets (`feature_payments`, `feature_payroll`, `feature_customer_portal`, `feature_employee_portal`, `feature_productivity`, `feature_reporting`, `feature_intake_forms`).
- Verified by frontend test agent: all 17 cards render real images (no placeholders), no broken links, removed legacy terms absent, and responsive layout passes desktop/mobile.

### 2026-04-23 — Marketing Features page coverage refresh
- Updated `frontend/src/pages/FeaturesPage.js` content while preserving existing layout and flow (hero, filters, alternating feature cards, CTA).
- Removed outdated pricing bullets (`Channel letter calculator`, `Monument sign calculator`) and aligned pricing coverage to active categories (digital print, cut vinyl, rigid signs, banners, vehicle graphics, apparel, services, promotional, custom).
- Expanded high-level feature coverage with concise, non-overwhelming additions: Stripe billing/connect, intake forms, reporting/productivity analytics, admin/team/onboarding controls.
- Added compact “Coverage Highlights” cards to represent broader platform capability without excessive detail.
- Reused existing screenshots and mapped them across all added/updated cards to avoid placeholder-heavy sections.
- Verified via UI automation: category filters, new cards, removed terms, screenshot presence, desktop/mobile layout integrity all passing.

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
