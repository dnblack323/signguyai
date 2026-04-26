# SignGuy AI - Changelog

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
