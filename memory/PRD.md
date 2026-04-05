# SignGuy AI - Product Requirements Document

> **Last Updated:** March 31, 2026
> **Version:** 6.1

---

## Original Problem Statement
Build a comprehensive multi-tenant SaaS operating system for sign shops, print shops, and custom graphics businesses. Replace spreadsheets, notebooks, and disconnected tools with a unified platform.

## Core Requirements
- Full-stack React + FastAPI + MongoDB application
- Multi-tenant isolation with role-based access control
- AI-powered tools for design, business, and marketing
- Stripe billing integration
- Customer and Employee portals

---

## What's Been Implemented

### Session: April 5, 2026 (Focused ProductionSettings Hook Cleanup)
- Completed targeted stale-closure / dependency cleanup for `src/pages/settings/ProductionSettings.js`
- Refactored the flagged hooks by:
  - using a ref for the imperatively-read selected template during async template loading
  - stabilizing template selection via `useCallback`
  - ensuring the page bootstrapping effect depends only on stable callbacks
- Verified:
  - loading settings
  - switching tabs/sections
  - saving workflow mode
  - template screen still rendering correctly after the cleanup

### Session: April 5, 2026 (Stable React Keys Pass)
- Replaced index-based keys in the priority dynamic and flagged user-facing React lists
- Interactive lists hardened:
  - Customers CSV header/preview mapping rows now use normalized stable ids
  - QuickToolbar separators now use stored separator objects with stable ids
  - FloatingAssistant messages/actions/quick actions now use stable ids
  - NewOrderForm local sketches/files now use stored stable ids
- Docs/marketing lists updated to use durable content-based keys rather than array indexes in the flagged pages
- Verified touched dynamic screens still load and interactive list behavior remains stable

### Session: April 5, 2026 (Hook Dependency / Stale Closure Fixes)
- Fixed the targeted stale-closure / dependency issues in:
  - `src/pages/settings/ProductionSettings.js`
  - `src/pages/Webstores.js`
  - `src/pages/TimeClock.js`
- Approach used:
  - `ProductionSettings`: stabilized template selection with `useCallback` and used a ref for the current selected template during async template loading
  - `Webstores`: moved unstable app-context fetchers into a ref so `loadData` and `checkStripeStatus` no longer depend on changing callback identities
  - `TimeClock`: moved timeclock app-context fetchers/actions into a ref and changed employee data loading to accept explicit employee IDs instead of relying on a captured stale closure
- Verified affected screens still load and operate without runtime regressions

### Session: April 5, 2026 (Object Storage Circular Import Fix)
- Fixed the circular dependency between `server.py` and `services/object_storage.py`
- Added shared module: `/app/backend/services/storage_config.py`
- Moved object storage configuration and initialization there so:
  - `server.py` no longer needs to import storage service logic for configuration
  - `object_storage.py` no longer imports `logger` from `server.py`
- Also fixed environment-loading timing so object storage reads `EMERGENT_LLM_KEY` after `.env` loading
- Verified storage flow end-to-end by creating and fetching an order drawing through the live API

### Session: April 1, 2026 (Business Assistant Rollout Planning)
- Added phased rollout plan for Business Assistant enhancements
- Saved to memory with strict release-gate rule:
  - do not begin the next phase until the previous phase is fully working and verified
- Added dedicated memory file: `/app/memory/business_assistant_rollout.md`

### Session: April 1, 2026 (Business Assistant Phase 0 Complete)
- **Business Assistant Phase 0 — Stabilization & Core Usability (DONE):**
  - Fixed broken assistant response rendering so responses return as plain text instead of object-style output
  - Improved voice transcription handling and recording setup in Floating Assistant
  - Added transcript confirmation flow after voice capture:
    - Send Now
    - Edit First
    - Discard
  - Added support for `create_order` assistant parsing and execution
  - Voice/business assistant now correctly handles phrasing like: `create an order for Sara Manning`
  - Added `create_order` to the documented assistant action types endpoint
- **Testing:**
  - Self-tested parse + execute action for order creation
  - Cleaned temporary assistant test orders/customers after validation
  - Testing agent iteration_89 passed backend 16/16 and frontend 100%

### Session: April 1, 2026 (Security & Test-Credential Hardening Pass)
- **Auth / Token Storage Hardening (IN PROGRESS, major pieces DONE):**
  - Added shared frontend token helpers in `/app/frontend/src/lib/authStorage.js`
  - Admin auth token storage now prefers `sessionStorage` by default and only persists to `localStorage` when "Remember me" is enabled
  - Core auth/app contexts switched to the shared storage helper
  - High-priority auth-sensitive pages updated away from direct raw `localStorage` token reads:
    - Promo Codes
    - Pricing Setup
    - Portal Proofs
    - Employee Portal Login
    - Customer Portal Login
    - Production Settings
- **Backend Test Credential Cleanup (major pass DONE):**
  - Added `/app/backend/tests/test_credentials_helper.py` to centralize reusable test credentials/constants
  - Replaced a large set of hardcoded test credential literals across backend test files with shared helper constants
  - Fixed follow-up syntax issues created during that codemod and revalidated representative test files
- **Testing:**
  - Linted updated auth-storage files successfully
  - Revalidated key code-review regression pages/endpoints after hardening changes
  - Note: broader non-priority localStorage cleanup and full test-suite refactor still remain for a later hardening sweep if desired

### Session: April 1, 2026 (Continuing Hardening + Complexity Reduction)
- **Auth Storage Sweep Expanded (DONE for token-sensitive paths):**
  - Removed remaining direct raw `localStorage` token reads for admin auth, customer portal auth, and employee portal auth token flows across frontend pages/components
  - Fixed all batch-import regressions introduced during the sweep and revalidated frontend runtime
- **Test Secret Cleanup Expanded (DONE for targeted literals):**
  - Removed the remaining targeted hardcoded credential literals identified in the backend tests search pass
  - Replaced them with centralized helper constants or synthetic placeholders from `test_credentials_helper.py`
  - Cleaned a large amount of low-risk test lint noise (`f"literal"`, `== True/False`, bare excepts, and unused locals in touched tests)
- **Complexity Reduction (DONE for two top frontend offenders + AI helpers):**
  - Refactored `DynamicCategoryFields.js` into clearer helper-driven rendering sections while preserving behavior
  - Refactored `DrawingCanvasPad.js` by extracting repeated canvas/image helper logic
  - Reduced complexity in AI route helpers by extracting parsing helpers for product descriptions and data helpers inside shop context generation
- **Testing:**
  - Auth storage regression testing agent iteration_86 passed backend 17/17 and frontend 7/7 representative pages loaded
  - Self-tested login, dashboard load, and product description AI generation after refactors

### Session: April 1, 2026 (Memory Catalog + Remaining Issues Tracking)
- Added `/app/memory/feature_catalog.md` to keep the current implemented feature set in one place
- Added `/app/memory/remaining_code_issues.md` to track the remaining cleanup / hardening items after the major review pass

### Session: April 1, 2026 (Code Review Remediation Pass)
- **Critical Review Fixes (DONE):**
  - Removed the `server.py ↔ routes/tiers.py` circular-import dependency by moving tier route access to `request.app.state` instead of importing from `server`
  - Fixed real backend runtime/lint issues found in the review pass across:
    - `routes/billing.py`
    - `routes/webstores.py`
    - `services/multi_product_billing.py`
    - `routes/job_tickets.py`
  - Fixed mutable default argument in job ticket pricing endpoint
  - Replaced dynamic `__import__("uuid")` usage with static `uuid` imports in billing service
  - Replaced bare `except` blocks in touched backend files with explicit exception handling
- **React Reliability Fixes (DONE):**
  - Added targeted `useCallback` / dependency-array fixes for priority pages from the review:
    - Production Settings
    - Digest Settings
    - Webstores
    - TimeClock
    - Quotes
    - PricingPlansV2
    - BackupRestore
  - Replaced unstable array-index keys in the touched high-risk Production Settings / Digest Settings lists
  - Replaced empty catch blocks in touched React pages with explicit logging
- **Intentionally deferred to later hardening pass (per approved scope):**
  - broad localStorage security sweep
  - large test-secret cleanup across all test files
  - broad complexity decomposition outside touched files
- **Testing:**
  - Self-tested tier, billing, user, and page-load smoke paths
  - Testing agent iteration_85 passed backend 15/15 and frontend 7/7 pages loaded successfully

### Session: April 1, 2026 (Employee/User Bug Fixes + Portal Invite)
- **Timesheet Manual Entry Fixes (DONE):**
  - Fixed manual time-entry editing from the Time Sheets tab
  - Root cause: manual timesheet snapshot entries were missing `employee_id`, causing the edit form to fail validation and behave like employee selection was missing
  - Added delete controls to Time Sheets for:
    - manual entries
    - saved timeclock shifts
- **User Management Tenant Scope Fix (DONE):**
  - Fixed `/api/admin/users` to return only users for the current tenant
  - Scoped admin user actions (reset password, status toggle, role change) to the current tenant
  - Added tenant-scoped admin user creation route
  - Updated User Management copy to clarify tenant-only scope
- **Employee Portal Invite Flow (DONE):**
  - Added admin employee portal invite endpoint: `/api/employees/{employee_id}/invite-portal`
  - Time Clock employee directory now includes an **Invite Portal** action
  - Invite returns login URL + PIN metadata and sends email through the existing SendGrid email service when configured
  - If email service is unavailable, admin still receives manual invite info in the response/toast
- **Testing:**
  - Self-tested tenant-scoped users list, employee portal invite, timesheet edit/delete, and timeclock shift delete
  - Testing agent iteration_84 passed backend 17/17 and frontend 100%

### Session: April 1, 2026 (Employee Module Consistency Pass)
- **Employee Admin Lifecycle (DONE):**
  - Added admin lifecycle support for employee records:
    - edit employee details/rate/role
    - deactivate/reactivate employee
    - reset employee portal PIN
    - delete employee with related cleanup
  - Added these controls to the admin Time Clock page as an Employee Directory panel
- **Employee Portal Config & Permissions (DONE):**
  - Added `/api/employee-portal/config`
  - Employee portal now respects tenant `employee_portal_settings` for:
    - pay access
    - task access
    - timeclock/work summary access
    - job detail visibility
    - profile edit visibility
  - Frontend employee portal now stores config and hides disabled nav/sections cleanly
  - Direct access to disabled employee portal sections now shows blocked/hidden states instead of exposing data
- **Permission Consistency (DONE):**
  - Added frontend permission alias mapping so older permission checks resolve correctly to current backend permissions
  - Admin role now explicitly includes payroll view/manage access in backend role config
- **Employee UI Quality Fixes (DONE):**
  - Fixed sticky `0` behavior on employee hourly-rate input
  - Added missing dialog descriptions on Time Clock admin employee dialogs for accessibility
- **Testing:**
  - Self-tested employee create/update/deactivate/reset PIN/delete flows
  - Self-tested employee portal settings enforcement and permission-gated behavior
  - Testing agent iteration_83 passed backend 30/30 and frontend 100%

### Session: March 31, 2026 (AI Racing Tool + Timeclock / Payroll Integration Fixes)
- **Racing Number AI Tool (DONE):**
  - Fixed the apparent "black screen" on Race Number Designer generation
  - Root cause: AI credit confirmation modal stayed open during long-running image generation, leaving the page dimmed/blocked
  - Updated credit-confirmation flow to close the modal immediately before generation begins, while keeping generation progress visible inline
- **Timeclock / Payroll / Timesheet Data Sync (DONE):**
  - Added shared backend service: `/app/backend/services/timeclock_service.py`
  - Time clock punches now persist both raw `timelogs` and normalized `timeclock_shifts`
  - Added historical backfill from existing raw action logs into saved shift records so previous days are no longer lost from payroll views
  - Fixed payroll summaries to stop using nonexistent `clock_in` / `clock_out` fields on raw timelogs
  - Payroll now calculates from connected sources:
    - time clock shifts
    - manual payroll hours
    - job timer entries
    - payroll transactions (advances / payments)
- **Admin Editing Improvements (DONE):**
  - Added payroll endpoint for saved shift retrieval/editing: `/api/payroll/timeclock-shifts`
  - Admin can now edit saved timeclock shifts from Payroll Time Sheets and Time Entries views
  - Payroll Time Entries tab now shows combined entries from manual hours + time clock shifts
  - Added admin transaction edit/delete support for payroll advances, earnings, and payment records
  - Enforced payroll mutations as admin-only server-side
  - Switched admin-facing payroll schedule/time-entry displays to 12-hour AM/PM formatting
  - Fixed sticky numeric `0` behavior on employee hourly-rate input in Time Clock admin flow
- **Employee Portal Pay Sync (DONE):**
  - Employee pay summary now reflects connected hours/earnings/advances instead of isolated legacy data pulls
- **Testing:**
  - Self-tested admin timeclock flow, payroll summary rollup, timesheet rollup, shift editing, employee portal pay summary, and racing AI generation UX
  - Testing agent iteration_81 passed backend 24/24 and frontend 100%
  - Follow-up admin cleanup pass iteration_82 passed frontend 100% and backend 14/15 with the only skipped case due no saved shift existing in that agent-created fixture
  - Temporary payroll/timeclock test employees were cleaned back out of production data after verification

### Session: March 31, 2026 (Feature Catalog Refresh)
- Updated internal and public-facing feature catalog surfaces to reflect the current product state
- Refreshed marketing/pricing copy to include:
  - unified productivity system (Dashboard / Calendar / Kanban / Task List)
  - signatures, drawings, and image markup
  - current order/job workflow language
- Refreshed in-app Productivity documentation to match the unified Phase 1–2 implementation

### Session: March 31, 2026 (Unified Productivity Phase 2 — Write-Back + Interactive Views)
- **Kanban Drag/Drop Persistence (DONE):**
  - Added unified PATCH endpoint: `PATCH /api/productivity/items/{item_uid}`
  - Dragging cards between Kanban columns now writes status updates back to source records
  - Source-aware write-back implemented for:
    - `task`
    - `order` (current job workflow)
    - `legacy_job`
    - `production_task`
  - Updates now propagate back through unified layer and reflect across `/items`, `/board`, and `/calendar-range`
- **Task List Rich Interactions (DONE):**
  - Added inline quick actions in Task List for supported item types
  - Supported inline edits now include:
    - status
    - priority
    - due date
    - assigned user
    - complete / reopen toggle
  - Task schema extended to persist richer productivity fields:
    - `status`
    - `priority`
    - `start_datetime`
- **Unified Source Detail / Edit Flow (DONE):**
  - Clicking unified items now opens a source-aware detail/edit dialog
  - Writable item types expose edit controls directly in the dialog
  - Deep-link button still routes users to the original source screen when available
- **Dashboard Widget Consolidation (DONE):**
  - Main dashboard schedule/pending-approval widgets now pull from unified productivity queries rather than separate disconnected dashboard endpoints
  - Kept older dashboard endpoints in place for safe compatibility during transition
- **Legacy Screens intentionally kept for now:**
  - `/production-board` remains during safe consolidation
  - older task/order dashboards remain until unified replacements are proven stable in more workflows
  - no destructive removals performed in this phase
- **Testing:**
  - Self-tested write-back for task / order / production task sources
  - Screenshot smoke tests passed for Productivity Task List and navigation
  - Testing agent iteration_80 passed frontend 100%; backend 15/16 passed with 1 production-task case skipped only due no available seeded item during agent run

### Session: March 31, 2026 (Unified Productivity Layer + Calendar Phase 1)
- **Audit / Reuse Pass (DONE):**
  - Audited and reused existing productivity-related sources instead of creating another siloed system
  - Reused/mapped: `/api/tasks`, `orders`, legacy `jobs`, `production_tasks`, `employee_schedules`, `appointments`, and dashboard schedule concepts
  - Promoted Productivity to a top-level navigation area with submenu links for Dashboard / Calendar / Kanban Board / Task List
- **Shared Productivity Data Layer (DONE):**
  - Added backend model: `/app/backend/models/productivity.py`
  - Added shared normalization/query service: `/app/backend/services/productivity_query.py`
  - Added unified endpoints:
    - `GET /api/productivity/items`
    - `GET /api/productivity/summary`
    - `GET /api/productivity/calendar-range`
    - `GET /api/productivity/board`
  - All views now consume one shared record shape with unified filtering for:
    - date range
    - assigned employee
    - status
    - priority
    - item type/source type
    - completed/open
    - search
- **Calendar Phase 1 (DONE):**
  - Rebuilt Productivity page around unified layer
  - Month is now the default calendar view
  - Added large readable month cells with visible item pills and `+N more` behavior
  - Added Month / Week / Day view switching
  - Added Today / Previous / Next controls
  - Clicking a day opens a day detail dialog using unified records
  - Calendar now runs from the unified productivity API rather than isolated task-only data
- **Unified Productivity Views (Initial Connected Versions) (DONE):**
  - Dashboard view uses unified summary/widgets from shared layer
  - Task List view uses unified item records
  - Kanban Board view uses unified item records grouped by shared `board_column`
  - Shared item detail dialog added for cross-view inspection
- **Still intentionally left for later merge/polish:**
  - Replace older standalone Dashboard widgets with unified productivity queries
  - Deeper write-back/edit actions from unified views (drag/drop persistence, inline edits)
  - Full add-item flow for reminders/follow-ups/appointments from Productivity UI
  - Final consolidation of older standalone production board/task-specific screens
- **Testing:**
  - Self-tested unified endpoints and new Productivity UI
  - Screenshot smoke test passed with top-level Productivity nav + calendar layout
  - Testing agent iteration_79 passed (backend 23/23, frontend 100%)

### Session: March 31, 2026 (Signature & Drawing System)
- **Signature System (DONE):**
  - Added tenant-level `signature_settings` feature toggle in Company Settings
  - Signature UI now hides completely when disabled on tested surfaces
  - New structured `/api/signatures/*` flow with:
    - per-record signature requirements
    - email signature request links
    - public review + sign page (`/customer-sign/:token`)
    - internal signature capture modal
  - Signatures store context: parent record, order/job context, type, signer info, signed timestamp, version reference, and image
  - Order Detail now exposes signatures for:
    - Order authorization
    - Change approval
    - Pickup / delivery / install confirmation
    - Quote / invoice / work order cards
  - Added proof signature controls in Approvals preview and document signature controls in Document Library details
  - Parent order signature history view added
- **Drawing / Sketch / Markup System (DONE):**
  - Upgraded drawing pad with undo, pen size selector, color picker, and improved touch support
  - Added autosave draft behavior for persisted order/item/image drawings
  - Extended drawing storage to structured contexts:
    - order-level
    - job-ticket/item-level
    - uploaded-image markup
  - Order Detail Drawings tab now supports combined filtered views: All / Order / Item / Image
  - Job Ticket Detail now has item-level drawings tab with enable/reveal behavior and image markup actions
  - Added secure image content endpoint for markup-on-uploaded-image flow
- **Testing:**
  - Self-tested: signature capture, email request creation, public signing flow, order/item drawings, image markup API paths
  - Screenshot smoke test passed for signature UI on Order Detail
  - Testing agent iteration_78 passed (backend 22/22, frontend 100%; skipped cases only due missing seed data)

### Session: March 31, 2026 (Order Workflow Hardening & Verification)
- **Order Workflow Verification Pass (DONE):**
  - Verified full order flow: order creation → job tickets → quote/invoice/work order generation → production start
  - Added ticket-level workflow shortcuts from Order Detail + Job Ticket Detail:
    - Assign employee
    - Add to employee schedule
    - Create productivity task
- **Live Estimate + Saved Price Sync (DONE):**
  - New Order and Add Ticket forms now auto-sync live pricing into `estimated_price`
  - Banner, apparel, and vehicle-wrap tickets now save calculator-backed pricing snapshots during ticket creation
  - Quotes and invoices now use active pricing snapshot values when available
- **Category / Pricing Reliability Fixes (DONE):**
  - Dynamic category schema now pulls pricing config and material options from tenant pricing settings with fallback catalog merge
  - Vehicle Wrap category now correctly maps to `vehicle_wraps` settings defaults
  - Vehicle coverage values (`25/50/75/custom`) now normalize correctly for pricing engine
  - Added `pickup` vehicle support to pricing enums/calculator
  - Apparel size breakdown now drives ticket quantity automatically
- **Document Visibility Fix (DONE):**
  - Generated work orders now appear in the Order Detail Financial tab alongside quotes and invoices
- **Testing:**
  - Self-tested backend pricing + workflow APIs with live tenant auth
  - Screenshot smoke test passed on `/orders/new`
  - Testing agent iteration_77 passed: backend 23 passed / 1 skipped, frontend 100%

### Session: March 30, 2026 (Dashboard Team Status & Navigation)
- **Dashboard Team Status Widget (DONE):**
  - Replaced basic ClockedInWidget with enhanced TeamStatusWidget
  - New backend endpoint: GET /api/dashboard/team-status-today
  - Combines employee schedule data with real-time clock-in status
  - Shows "Scheduled Today" section with clock status badges (Clocked In / Not In / On Break / Finished)
  - Shows "Clocked In (Unscheduled)" section for walk-ins
  - Empty state with "Set Up Schedule" button linking to /payroll?tab=schedule
  - Count badges: "X in" and "X scheduled" in header
- **Employee Schedule Navigation Link (DONE):**
  - Added "Employee Schedule" to Team sub-nav in PrimaryNav.js
  - Added "Employee Schedule" to Team children in MobileNav.js
  - Links to /payroll?tab=schedule which pre-selects the Schedule tab
  - Payroll.js now reads ?tab query parameter to initialize active tab
- **Daily Notification Digest (DONE):**
  - Full backend: /api/digest/* endpoints (preview, send, settings, history)
  - Compiles: scheduled employees, jobs due today, overdue invoices, pending approvals, yesterday's revenue, unread messages
  - Rich HTML email template rendered server-side with inline CSS
  - SendGrid email delivery (configured in .env)
  - APScheduler background scheduler checks every minute for scheduled sends
  - Settings page at /settings/digest with enable toggle, time picker (UTC), and recipient management
  - "Send Digest" quick action button on Dashboard
  - "Daily Digest" link in Settings sub-nav (desktop + mobile)
  - Send history tracking in MongoDB digest_logs collection
- **Order Drawing Pad — Phase 1 (DONE):**
  - New `order_drawings` collection with full CRUD API: `/api/order-drawings/*`
  - Canvas-based drawing: mouse, touch, stylus support with high-DPI rendering
  - PNG upload to Emergent Object Storage (`signguy-ai/orders/{id}/drawings/...`)
  - Blank drawing prevention (< 1000 bytes rejected)
  - "Drawings & Signatures" tab in Order Detail page with thumbnail grid
  - Full-size preview modal with label, type badge, date, creator, notes
  - Admin-only delete (soft-delete)
  - `touch-none` CSS prevents page scroll while drawing on tablet/mobile
  - Drawing types: signature, sketch, markup
  - Object storage service: `/app/backend/services/object_storage.py`

### Session: March 31, 2026 (Bug Fixes & Drawing Phase 2)
- **Unit of Measure Bug Fix (DONE):**
  - Root cause: Schema defaults not applied to specs on category load
  - DynamicCategoryFields now auto-sets defaults from schema fields
  - Case-insensitive unit comparison in sqFootage and LivePricingPreview
  - Banner: Width=2, Height=8, Feet now correctly shows 16.00 sq ft
- **New Order Form Reorder (DONE):**
  - Customer section: search, name, company, phone, email only
  - Order Information: source, due date (moved here), event date, internal notes
  - Job Tickets section
  - Sketches & Notes: new section with "Add Sketch" drawing pad
  - Pickup / Delivery: moved to end with method + delivery notes
  - Attachments / Artwork: moved to end
  - Save as Draft + Save Order buttons
- **Order Drafts Feature (DONE):**
  - "Save as Draft" button creates order with status='draft'
  - Draft status added to OrderStatus enum and OrderCreate model
  - Drafts filter in Orders page status dropdown
  - Draft status badge styling (gray)
- **Material Price Zero Placeholder Fix (DONE):**
  - Changed initial cost_per_unit from 0 to '' (empty string)
  - Clean numeric input without leading zeros
- **Invoice History Preview Colors Fix (DONE):**
  - Changed dark slate backgrounds to white/gray-100
  - All text now dark (gray-900/gray-700) for readability
  - Preview table has alternating row colors
  - Suggestion cards and stat cards on white backgrounds
- **Logo Upload Update Fix (DONE):**
  - File input reset forces re-mount after upload
  - Can now upload and then update logo reliably
- **Category Schema Fetch Reliability (DONE):**
  - Added retry logic (up to 2 retries with 500ms delay) for schema endpoint
- **Drawing Pad on New Order Form (DONE):**
  - DrawingModal supports onLocalSave for pre-order sketches
  - Sketches stored in-memory until order is saved, then uploaded as order_drawings

### Session: March 27, 2026 (Bug Fixes & UI Improvements)
- **Task List Display Bug (FIXED):**
  - Updated AppContext.js to use local state updates instead of refetching
  - `createTask`, `updateTask`, `deleteTask` now immediately update local state
  - Tasks appear instantly in the UI after creation
- **Job Ticket Customer Data Bug (FIXED):**
  - Created new `AddTicketToOrder.js` page for adding tickets to existing orders
  - Updated App.js routing to use dedicated component instead of reusing NewOrderForm
  - Order summary card shows customer info while adding tickets
- **Orders List Icons (DONE):**
  - Added View icon (blue eye) for quick view
  - Added dropdown menu with View Details, Add Ticket, Delete Order options
  - Added bulk actions toolbar with checkboxes for multi-select
  - Bulk status change and bulk delete functionality
- **Users List Icons (DONE):**
  - Added View icon (blue eye) for quick user info
  - Consolidated Role/Reset/Enable actions into dropdown menu
- **Financials Page Color Fix (DONE):**
  - Fixed page header to use white text on dark background
  - Updated summary cards to use -600 color variants for better visibility on white
  - Fixed expense breakdown and recent activity text colors
  - Changed table cell text to text-gray-900 for readability
- **Documentation Theme Fixes (DONE):**
  - DocsEmployees.js - Fixed text colors for dark theme
  - DocsQuotesJobs.js - Fixed text colors for dark theme with cyan accents
  - Updated bg-gray-50 to bg-gray-800/50 for proper dark theme cards
- **Documentation Content Updates (DONE):**
  - Created new DocsDocumentLibrary.js page with full guide
  - Enhanced DocsProductivity.js with Task List, Calendar, and Kanban details
  - Enhanced DocsCustomerPortal.js with Portal Invite Flow, Proofs, Forms sections
  - Enhanced DocsWebstores.js with creating stores, products, checkout details
  - Enhanced DocsAITools.js with tool descriptions and credit system explanation
  - Added Document Library to DocsLayout sidebar navigation
  - Added Document Library to DocsOverview primary links
- **Documentation Screenshots (DONE):**
  - Added screenshot to DocsCustomers.js with feature_customers.jpeg
  - Added screenshot to DocsAITools.js with feature_ai_tools.jpeg
  - Added screenshot to DocsWebstores.js with feature_webstores.jpeg
  - Added screenshot to DocsInvoicing.js with feature_invoices.jpeg
  - Added screenshot to DocsPricingCalculator.js with pricing.png
  - Added screenshot to DocsTimeTracking.js with feature_time_clock.jpeg
  - Screenshots use existing /screenshots/ assets with proper captions

### Session: March 22-27, 2026 (Previous Sessions)
- **NEW 4-Layer Workflow System (DONE - Backend):**
  - Layer 1: Orders (master record with auto-numbering ORD-XXXX)
  - Layer 2: Job Tickets (production detail per item, category-based)
  - Layer 3: Quotes generated from job tickets (financial layer)
  - Layer 4: Production Tasks (auto-generated from category workflow templates)
  - 6 Default Workflow Templates: Rigid Signs (11), Banners (12), Cut Vinyl (8), Vehicle Wrap (14), Apparel (11), Promo/Misc (5)
  - Status roll-up: tasks→tickets→orders with partial completion logic
  - Activity logging for all status changes
  - Production board grouped by department/status
  - Admin workflow template CRUD
- **Testing:** 21/21 backend tests passed (iteration_72)
- **New Files:** models/orders.py, services/workflow_engine.py, routes/orders.py, routes/job_tickets.py, routes/production_tasks.py, routes/workflow_templates.py
- **New Collections:** orders, job_tickets, production_tasks, workflow_templates, order_quotes, order_activities

### Session: March 22, 2026 (Stage 2 + Fixes)
- **Stage 2 Legal & Color Scheme (DONE):**
  - Terms of Service page (`/terms`) — 13 sections covering agreement, billing, AI credits, GDPR
  - Privacy Policy page (`/privacy`) — 12 sections GDPR-compliant with third-party sharing disclosure
  - Footer links updated from `<a href="#">` to React Router `<Link>` components
  - Color scheme changed from amber/gold → violet/purple across 7 files (Landing, Pricing, Billing, Founders, WhyFounder, TrialLockout, PublicNav)
- **Testing:** 11/11 frontend tests passed (iteration_71)
- **Deployment Fix:** Cleaned requirements.txt from 137 → 24 packages, removed server_backup.py

### Session: March 20, 2026
- **Stage 1 Critical Fixes (ALL DONE):**
  - AI Rate Limiter Fix: All 9 AI endpoints in `ai.py` now use `request: Request, data: PydanticModel` pattern
  - Promo Code Backend: Added `POST /api/billing/apply-promo` endpoint with full validation
  - Promo Code `free_days` type: Backend and frontend support added
  - TrialLockout promo input: Users on lockout screen can now enter promo codes
  - AI Credit Audit: Verified all 28+ tools have credit costs assigned (1-3 credits)
  - AI Credit Confirmation Popup: Verified preflight, "don't show again", low balance warnings
  - Invoice Line Items: Verified fallback chain (job_items → line_items → subtotal → quote.total)
- **Testing:** 14/14 backend tests passed, 100% frontend verification (iteration_70)

### Session: March 18, 2026
- **Founders Edition Only Billing:** Simplified entire billing system from multi-tier (9 plans, 3 product lines) to Founders-only ($99/mo, $594/yr). All other tiers archived.
- **Founders Plan Config:** Created `/app/backend/config/founders_plan.py` as single source of truth
- **New Billing Endpoints:** `/api/billing/founders/*` (plan, checkout, purchase-credits, credits, fees, spots)
- **Processing Fees Fixed:** 2.2% + $0.20 platform, 2% webstore additional
- **Credit Rollover Logic:** Monthly (150) don't roll over, purchased DO roll over
- **Stripe Founders Price IDs:** Added STRIPE_PRICE_FOUNDERS_MONTHLY, ANNUAL, CREDITS_100/300/1000, COUPON
- **Route Redirects:** All old tier pages (/starter, /pro, /business, /platform, /ai-studio) redirect to /pricing-plans
- **Feature Gate Bypass:** Founders get all features enabled regardless of plan config
- **Voice I/O on Floating Assistant:** Added mic button + "Read aloud" to the persistent chat widget
- **Voice Transcription Bug Fix:** Fixed 500 error on /api/ai/voice/transcribe (file handling)
- **Password Recovery:** Added "Forgot Password?" flow for owner accounts
- **Login Error Handling:** Improved to show "Invalid email or password" instead of generic "Network error"
- **bcrypt Fix:** Replaced passlib with direct bcrypt + pinned bcrypt==4.0.1
- **Feature Catalog Updated:** Added voice features, floating assistant, password recovery

### Previous Sessions (Jan-Mar 2026)
- CRM, Orders/Job Tickets, Invoicing, Time Clock, Payroll
- 28+ AI Tools, AI Business Assistant
- Webstores (3 types), Stripe Connect
- Customer Portal, Employee Portal
- Multi-tenant isolation (28 security tests, 100% pass)
- Pricing Calculator (8 categories), Production Workflow
- AI Credit System, Tiered Onboarding
- Community Hub, Documentation Site
- Marketing Website, Promo Codes
- Office-Style Ribbon Navigation

---

## Active Plan: Founders Edition Only

| Field | Value |
|-------|-------|
| Plan Name | Founders Edition |
| Monthly Price | $99 |
| Annual Price | $594 |
| Founder Limit | 100 spots |
| AI Credits | 150/month (no rollover) |
| Purchased Credits | Roll over while active |
| Processing Fee | 2.2% + $0.20 |
| Webstore Fee | 2% additional |
| Promo Code | FOUNDERS (50% off) |
| Features | All included |

---

## Prioritized Backlog

### P0 - Critical
- ~~AI Tools rate limiter parameter fix~~ DONE
- ~~Promo code apply-promo endpoint~~ DONE
- ~~free_days promo type~~ DONE

### P1 - High Priority (from user notes)
- Update documentation pages to Founders-only model
- Update Feature Catalog (remove tier references)
- "New Job" button in customer info popup
- UI Overhaul ("Dark Shell / Light Workspace")

### P2 - Medium Priority (from user notes)
- Reinstate: Materials & Inventory system
- Reinstate: Bulk actions on Orders page
- Reinstate: Search on Orders/Invoices/Webstores pages
- Reinstate: Database indexes migration
- Reinstate: Code cleanup (console.log removal, print→logger)
- Reinstate: Navigation updates (ActionToolbar, Settings links)

### P3 - Future/Backlog
- Rate limiting (slowapi)
- Cookie consent banner
- Error boundary implementation
- GDPR data export/deletion tools
- Mobile responsiveness pass
- Learning Calculator
- Vehicle Wrap AI Tool (Full Spec)
- Master Product List
- Custom Domain Support for webstores
- SMS Notifications (Twilio)
- QuickBooks Integration

---

## Architecture

```
Tech Stack: React 18 + FastAPI + MongoDB + OpenAI + Stripe
Frontend: 87 pages, 81 components, 98 routes, 50,414 LOC
Backend: 33 route files, 289 endpoints, 29,169 LOC
Database: 58 MongoDB collections
Total: ~80,000 lines of code
```

---

## Credentials
- Admin: thesigntistslab@gmail.com / password123
- Test: test@test.com / password
