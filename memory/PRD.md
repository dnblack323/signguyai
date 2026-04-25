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

## Architecture — Stripe Service Layer
As of 2026-04-25, all Stripe business logic is centralised in `backend/services/stripe_service.py`:
- Platform fee schedule, `get_stripe_mode()`, `get_tenant_tier()`
- Connect account checkout-status cache (`get_stripe_account_checkout_status`)
- DB helpers: `find_invoice_document`, `record_stripe_event`, `mark_invoice_paid`
- Webstore finalization: `finalize_webstore_stripe_checkout` (lazy-imports webstore types to avoid circular dep)

`routes/stripe_connect.py` and `routes/webstores.py` are thin consumers of this service.
Invoice Stripe payments (`POST /stripe-connect/invoice/{id}/pay`) are independently usable with no webstore dependency.

## Implemented (CHANGELOG)

### 2026-04-25 — Send Payment Link Enhancement
- New `POST /api/stripe-connect/invoice/{id}/send-payment-link` endpoint — generates a Stripe Checkout URL for any invoice and optionally emails it directly to the customer.
- Frontend modal on Invoices page: shows amount, read-only URL, Copy (with check animation), Open-in-new-tab, editable email input, and Send button.
- Customer email auto-filled from the customers DB; the customer needs no account to pay (Stripe-hosted checkout page).
- Extracted all Stripe business logic out of `routes/webstores.py` and `routes/stripe_connect.py` into `services/stripe_service.py`.
- `webstores.py`: 2205 → 2034 lines (-171 lines).
- `stripe_connect.py`: 1371 → 1190 lines (-181 lines).
- New `stripe_service.py`: 410 lines, single source of truth.
- All existing endpoints and webhook flows verified working after refactor.
- Both files use standalone Motor clients to avoid circular import through `server.py`.

## Implemented (CHANGELOG)

### 2026-04-24 — Webstore orders now auto-appear in main Orders list
- Added automatic bridge creation from webstore checkout orders into `orders` collection in `backend/routes/webstores.py`.
- New helper flow:
  - `_next_order_number_for_tenant(...)` to generate standard `ORD-####` numbering.
  - `_ensure_main_order_bridge(...)` to insert a main order record with marker fields (`is_webstore_order`, `webstore_order_id`, `webstore_id`, `webstore_name`, `webstore_job_id`).
- `create_webstore_order(...)` now creates/links `main_order_id` immediately after webstore order creation and updates job with `order_id` linkage.
- Updated `frontend/src/pages/OrdersPage.js` to visibly mark these rows with a **Webstore** badge.
- Verified with simulated paid checkout in `signguypa@gmail.com` tenant:
  - webstore order created,
  - corresponding main order created,
  - marker fields present,
  - UI shows `Webstore` badge and row remains clickable.

### 2026-04-24 — Webstore checkout enforced to Stripe-only paid flow
- Hardened backend `POST /api/webstores/v2/orders` (`backend/routes/webstores.py`) to **block unpaid/direct order creation**.
- Route now requires a real Stripe session-backed idempotency key (`stripe:{session_id}`) and validates against `payment_transactions` with matching `reference_id` + `status=paid`.
- This prevents legacy “customer info only” submissions from creating unpaid orders.
- Updated storefront payment return handling (`frontend/src/pages/Storefront.js`) to verify `session_id` via `/api/stripe-connect/payment-status/{session_id}` before showing success.
- Added short polling for payment verification and clearer checkout CTA text (`Continue to Secure Payment` / `Redirecting to Stripe…`).

### 2026-04-24 — Webstore banner visibility compatibility fix
- Fixed storefront banner/logo rendering compatibility for legacy store docs where media URLs may be stored on top-level keys (`banner_url`, `logo_url`, `*_image_data`) instead of nested `branding`.
- Backend: updated `sanitize_webstore_for_public(...)` and `_normalize_webstore_doc(...)` in `backend/routes/webstores.py` to map legacy media fields into `branding.banner_url` / `branding.logo_url`.
- Frontend: updated `frontend/src/pages/Storefront.js` to use robust fallback chain for banner/logo source selection.
- Verified banner asset rendering + no 404 + no layout regressions on desktop/mobile via frontend test agent.

### 2026-04-23 — Webstores create flow: "created but failed to refresh list"
- Fixed `frontend/src/pages/Webstores.js` list-refresh resilience after create:
  - Added `normalizeWebstoreList(...)` to handle variable response shapes safely.
  - Upgraded `loadData(...)` with one-shot retry for webstore fetch failures.
  - Added optional `suppressStoreErrorToast` mode for create flow to avoid false-negative UX.
  - Added optimistic insert of newly created store into local list so it appears immediately even if background refresh is flaky.
- Create flow now shows success and keeps the store visible immediately + after hard refresh.
- Verified with frontend automation using tenant owner credentials: create succeeds, no "failed to refresh list" toast, store count increments instantly, and persists after page reload.

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
