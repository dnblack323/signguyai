# SignGuy AI - Changelog

## February 15, 2026 (later — Item #3)
- **Failed-Payment / Dunning Workflow (NEW)** — top-5 prelaunch platform gap #3
  - New service `services/dunning.py` with `record_payment_failure()` and `record_payment_success()` — single source of truth for dunning state.
  - Tenant doc gains: `payment_failed_count`, `first_payment_failure_at`, `last_payment_failure_at`, `last_payment_succeeded_at`, `auto_suspended_for_payment`.
  - **Auto-suspend at 3 consecutive failures** (configurable via env `DUNNING_AUTO_SUSPEND_AFTER`). Self-lockout protection: never auto-suspends a tenant that contains a `platform_admin` user.
  - **Auto-reactivate on payment success** if the tenant was previously auto-suspended for payment (`auto_suspended_for_payment=true`). Manual suspensions are NOT auto-reactivated.
  - **Email orchestration:**
    - Failure 1 / 2 → `send_payment_failed_email` ("you have N attempts left").
    - Failure 3 → `send_dunning_suspended_email` ("account suspended").
    - Auto-reactivate → existing `send_tenant_reactivated_email`.
  - **Webhook wiring:** `multi_product_billing.handle_invoice_payment_failed` and `handle_invoice_payment_succeeded` now call into the dunning service.
  - **Manual override:** new `POST /api/platform-admin/tenants/{id}/mark-paid` for NET-60 invoices, wires, manually cleared chargebacks, etc. Resets counters + auto-reactivates if needed.
  - **Audit log integration:** every transition writes a row under `action_category="billing"`: `payment.failed`, `dunning.auto_suspend`, `payment.succeeded`, `dunning.auto_reactivate`, `payment.manual_mark_paid`.
  - **UI:** `PlatformAdminTenantDetail.js` now shows a "Billing & Dunning" card (failed-attempts counter, last failure/success timestamps, "Auto-suspended for non-payment" badge, "Mark as Paid" button + confirmation dialog). Card auto-hides if there's nothing to show (zero failures and no payment history).
  - `TenantDetail` Pydantic now exposes all five dunning fields.
  - **Verified end-to-end:** simulated 3 consecutive failures via `services.dunning` → tenant auto-suspended after #3 → payment success auto-reactivated → manual mark-paid via real HTTP also auto-reactivated → 9 distinct billing audit rows captured.

## February 15, 2026 (later — Email toggle)
- **"Welcome back" email toggle on Reactivation** — Suggestion from Item #2 finish-tool note.
  - New `EmailService.send_tenant_reactivated_email()` (renders an HTML "Welcome back" message with optional "note from our team").
  - `POST /api/platform-admin/tenants/{id}/reactivate` now accepts `notify_owner: bool` (default true) and returns `email_status` so the UI can confirm.
  - Reactivate dialog has a checkbox "Send the owner a 'Welcome back' email" (default ON).
  - Verified via curl: notify_owner=true returns `email_status.success=true, status_code=202` (real SendGrid send); notify_owner=false returns `email_status: null`.

## February 15, 2026 (Item #2)
- **Suspend / Reactivate Tenant (NEW)** — top-5 prelaunch platform gap #2

  - New endpoints: `POST /api/platform-admin/tenants/{id}/suspend` (body: `reason`), `POST /api/platform-admin/tenants/{id}/reactivate` (body: `note?`).
  - Tenant doc gains: `is_active`, `suspension_reason`, `suspended_at`, `suspended_by`, `suspended_by_email`, `reactivated_at`, `reactivated_by`, `reactivated_by_email`.
  - **Self-lockout protection:** cannot suspend a tenant that contains a `platform_admin` user.
  - **Idempotent:** re-suspend returns `already_suspended: true`; re-reactivate returns `already_active: true`.
  - **Login enforcement:** suspended tenants' users get HTTP 403 with structured detail `{code: "tenant_suspended", message, reason, suspended_at}` on login attempt.
  - **Active session enforcement:** every protected endpoint runs through `get_current_active_user`, which checks tenant `is_active` and rejects with the same 403 — existing sessions are killed on the next API call. Platform admins are exempt.
  - **Auto audit log:** suspend / reactivate actions write `tenant.suspend` / `tenant.reactivate` rows automatically via `log_admin_action`.
  - Frontend: `TenantListItem` and `TenantDetail` response models surface `is_active`, `suspension_reason`, `suspended_at`, `suspended_by_email`. `PlatformAdmin.js` shows red "Suspended" badge + reason inline. `PlatformAdminTenantDetail.js` shows red banner + "Suspend Tenant" / "Reactivate Tenant" buttons with reason / note dialogs.
  - **Account-suspended UX:** new `/account-suspended` page shows the user the reason + suspended_at + a "Contact Support" mailto. New `lib/suspensionGuard.js` helper saves the suspension info to sessionStorage and hard-redirects. AuthContext login + fetchUserProfile + AppContext axios response interceptor all detect 403/`tenant_suspended` and route the user to `/account-suspended`.
  - Verified end-to-end: created brand-new tenant → confirmed `/api/users/me` works → suspended → existing token blocked with 403 + structured payload → fresh login also blocked with same payload → reactivated → existing token works again. Audit trail captured 6 events.

## February 15, 2026
- **Admin Audit Log (NEW)** — top-5 prelaunch platform gap #1
  - New collection `admin_audit_log` capturing every privileged Platform Admin action with actor, target, tenant, IP, user-agent, summary, structured metadata, status, timestamp.
  - New service `services/admin_audit.py::log_admin_action()` (failure-tolerant — never blocks the calling action).
  - Wired into existing privileged endpoints: impersonation start, impersonation exit, manual end of impersonation log, and onboarding-checklist updates.
  - New endpoints: `GET /api/platform-admin/audit-log` (filterable by action, category, actor_email, target_id, tenant_id, since/until; paginated), `GET /api/platform-admin/audit-log/actions` (distinct actions/categories), `GET /api/platform-admin/audit-log/{id}` (single entry).
  - New page `/platform-admin/audit-log` with filter bar, table, and detail dialog. Reachable from "View Audit Log" button on the Platform Admin home page.
  - Verified end-to-end: impersonation start writes audit row with action `impersonation.start`, captured IP `34.170.12.145`, actor `thesigntistslab@gmail.com`, target user, tenant, metadata `{impersonation_log_id, target_role}`.

## April 28, 2026
- AI Tool Audits complete (read-only): Racing, Business, Marketing, Design, Branding categories documented in `/app/memory/*_TOOLS_AUDIT.md`.

## April 26, 2026 (Tier 6 sweep)
- **Customer Appointment Request → Owner Email Notification (NEW)**
  - When a customer submits an appointment request via portal, tenant owner now receives an HTML email immediately (verified by `email_logs` rows with status='sent', response_code=202).
  - Try/except wrapper means SendGrid failure does NOT block appointment creation.
- **Admin PDF Endpoints (NEW)**
  - `GET /api/quotes/{id}/pdf` — admin can download quote PDF (no portal login required).
  - `GET /api/invoices/{id}/pdf` — admin can download invoice PDF with PAID/UNPAID status badge.
- **Tier 6 Backend Audit (20/20 PASS)** — AI assistant multi-turn, email composer, voice transcribe, image-gen route, SendGrid wiring, customer portal invoice PDF all verified.
- **Backlog tracked (NOT_IMPLEMENTED, deferred):** `GET /api/ai/tools` list, `POST /api/ai/extract-invoice`, server-side clear-chat, payroll PDF, work-ticket PDF.
- **Trackers updated:** PRELAUNCH_CHECKLIST.md Tier 6 sections + Section 17 added to user personal checklist (31 items: AI UI, mail-client rendering, PDF visual quality, SPF/DKIM/DMARC).

## April 26, 2026 (later)
- **Customer Request Appointment Feature (NEW) + Tier 5 Backend Sweep**
- New: `POST /api/portal/appointments/request` — customer-initiated appointment requests with `status="requested"`. Notification row auto-created for shop staff.
- New: `PUT /api/appointments/{id}/confirm` — admin confirms request, supports time/employee override. Flips status to `confirmed`.
- New: `PUT /api/appointments/{id}/reject` — admin rejects, sets status to `cancelled` and appends reason to notes.
- New UI: Portal Appointments page now has "Request Appointment" button + dialog (type / date / time / location / notes). New "Pending Confirmation" amber badge for `requested` status. Toast feedback on submit.
- New: `DELETE /api/admin/users/{id}` with three guardrails (self / staff-perm / last-owner-of-tenant).
- Bug fix: `routes/auth.py` had broken references to `Permission.USERS_EDIT` (enum doesn't exist). Fixed to `USERS_MANAGE` — would have caused `AttributeError` on first call to admin reset-password / status routes.
- Tier 5 backend audit: 28/29 PASS via testing agent (iteration_134). Sections 5.1, 5.4, 5.7, 5.8, 5.10, 5.11, 5.12 verified working. Manual UI/Stripe/email items migrated to Section 16 of personal checklist.
- Trackers updated: PRELAUNCH_CHECKLIST.md, OPEN_ITEMS_TRACKER.md, POSTFIX_RETEST_RESULTS.md, SECTION1_USER_PERSONAL_CHECKLIST.md (Section 16 added with 25 items).

## April 26, 2026
- **Prelaunch Tier 1–4 Final Mop-Up Complete (iteration_132 follow-up)**
- Security fix: Added `_require_payroll_view_access()` guard to all GET payroll endpoints (`/report`, `/balance`, `/transactions`, `/hours`, `/signoff`, `/timesheet`, `/pay-period`, `/timeclock-shifts`, `/legacy-manual-entries`, `/schedule`) — staff role now correctly receives `403`.
- New endpoint: `GET /api/customers/export` — CSV export of customers (name, email, phone, company, status, notes, created_at).
- New endpoint: `POST /api/workflow-templates/{id}/apply` — applies a template to an order, creates production tasks per stage for each ticket; supports `replace_existing=true`.
- New endpoint: `POST /api/workflow-templates/{id}/duplicate` — copies a template into a tenant-owned "(Copy)" version.
- New endpoint: `GET /api/portal/appointments` — customer portal list of scheduled appointments.
- New endpoint: `GET /api/employee-portal/dashboard` — alias of `/work-summary` (matches frontend spec).
- Enhanced: `GET /api/payroll/report` now accepts `format=csv` query param, returns streaming CSV.
- Updated trackers: `PRELAUNCH_CHECKLIST.md`, `PRELAUNCH_OPEN_ITEMS_TRACKER.md`, `PRELAUNCH_POSTFIX_RETEST_RESULTS.md`, `PRELAUNCH_SECTION1_USER_PERSONAL_CHECKLIST.md` (Section 15 added).

## March 27, 2026
- Updated all documentation (Feature Catalog, Build Roadmap, Docs pages) to reflect Order/Job Ticket system
- Removed all references to old "Jobs" module from docs and navigation
- Updated DocsQuotesJobs → DocsOrdersTickets (Orders & Job Tickets documentation)
- Updated DocsEmployees with schedule feature documentation
- Updated GettingStarted guide with order workflow
- Updated DocsOverview with 4-layer architecture description

## March 26, 2026
- Fixed: Sales and expense recording (created /api/financials/sales and /api/financials/expenses endpoints)
- Fixed: Schedule dialog not opening (removed conditional wrapper)
- Fixed: Owner permissions (hasPermission now grants all permissions to owner role)
- Fixed: Contact Support now emails donnell@signguy-ai.com
- Navigation: Financials moved to top-level, Reports = shortcuts page
- Theme: Applied light theme to PricingSetup, CompanySettings, PaymentSettings
- Workflow Templates: Removed duplicate QC toggle, kept only Required
- New Order Form: Added ticket buttons near Save, fixed zero placeholder, better error handling
- Square footage: Default changed to inches (18x24 = 3 sqft, not 432)
- LivePricingPreview: Added all finishing options, fixed apparel trigger
- Production Board: Shows ticket name first, task name secondary

## March 25, 2026
- Fixed: Setup fee markup bug — $25 fee was causing $67 increase, now adds exactly $25 (flat, not marked up)
- Fixed across ALL 6 calculator functions
- Added: Generate Work Order on order detail
- Added: Apparel quantity discounts (5-25% based on qty tiers)
- Improved: Stripe Connect error messaging

## March 24, 2026
- Built: File upload system for orders (upload, list, delete)
- Built: Live pricing preview on new order form (calls pricing API in real-time)
- Built: Employee schedule system (weekly grid, shift dialog, save to DB)
- Built: Materials & Pricing admin page (global rates, material CRUD)
- Added: Files tab on Order Detail page
- Added: Order action buttons (Generate Quote/Invoice/Work Order, Email, Status, Portal)
- Created: 30 database indexes for production performance

## March 23, 2026
- Built: Full Banner category schema (24 fields, 7 subtypes)
- Built: Full Apparel category schema (27 fields, 8 subtypes, size grid, print locations with per-location details)
- Built: Rigid Signs, Cut Vinyl, Digital Print, Vehicle Wrap schemas (22-30 fields each)
- All material options now from centralized catalog (not hardcoded)
- Calculator wiring: all dynamic fields map to pricing engine
- Quick Entry / Detailed Entry modes for job tickets
- Legacy Jobs removed from navigation, redirects to Orders
- Dashboard quick actions updated (New Job → New Order)
- Dark shell / light content theme applied globally (20+ pages)
- Container widened to 1600px

## March 22, 2026
- Built: Complete 4-layer Order system backend (Orders, Job Tickets, Production Tasks, Workflow Templates)
- Built: Frontend pages (OrdersPage, OrderDetail, NewOrderForm, JobTicketDetail, ProductionBoard, WorkflowTemplateManager)
- 6 default workflow templates, activity logging, status roll-up
- Terms of Service and Privacy Policy pages
- Color scheme: amber/gold → violet/purple across all Founders-branded pages
- Founder grace period (14 days read-only after subscription lapse)
- Multiple production bug fixes (login, promo codes, onboarding, mobile nav)

## March 20, 2026
- Stage 1 Critical Fixes: AI rate limiter, promo code system, invoice line items
- Deployment fix: requirements.txt cleaned from 137 → 24 packages
- SendGrid email configured
- Production setup endpoint and page (/setup)
