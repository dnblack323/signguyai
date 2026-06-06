# SignGuy AI — Complete Session History
# ALL sessions from Day 1 to present, oldest → newest
# Generated: June 2026
# Sources: /app/memory/CHANGELOG.md + /app/memory/PRD.md

---

## HOW TO READ THIS FILE
- This is a single document covering every session since the project started.
- Ordered oldest → newest (scroll down for most recent work).
- Each entry shows: date, what was built, what was tested, and status.

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CHAPTER 1 — EARLY FOUNDATION (Feb–Mar 2026)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### February 12, 2026 — AI Assistant Pass 1: Personality Picker + Quick-Action Intents
- Killed "generic mode" disclaimer — Founders get full business data access unconditionally
- System prompt rewritten from rigid rules → tone-driven; removed brittle regex post-processor
- 4 personality presets: ops_partner (default), wise_mentor, cheerful_helper, no_bs_direct
- Quick action intent detection: "email <name>", "send invoice to <name>" → customer lookup + ProposedActionPill
- New endpoints: GET/PUT /api/ai/assistant/personality
- Frontend: ProposedActionPill component, AssistantSettings page at /settings/assistant
- 43/43 backend regression tests pass

### February 12, 2026 — AI Assistant Pass 2: Proactive Nudges + Send-Email Loop + Long-Term Memory
- GET /api/ai/assistant/nudges: scans tenant data, returns up to 6 proactive pills (stale quotes, overdue invoices, appointments)
- POST /api/ai/assistant/draft-email: GPT-4o-mini drafts 2-4 sentence email from context
- POST /api/ai/assistant/send-email: sends reviewed draft via SendGrid; logs to ai_assistant_logs
- Rolling long-term memory: compresses last ~10 messages into 2-4 bullets, stored on tenant; prepended to every system prompt
- Frontend: AssistantNudgesWidget on Dashboard (DraftEmailModal inline review-and-send)
- 43/43 regression tests pass

### February 12, 2026 — AI Assistant Pass 3: Real Tool Calling (Navigate / Create / Metric)
- Tool router runs BEFORE GPT call. Two layers:
  - Layer 1: deterministic keyword fast-path (20 metric + 10 navigation phrasings)
  - Layer 2: gpt-4o-mini classifier with strict JSON output
- 4 tools: navigate, create_task, create_appointment, query_shop_metric (10 metrics)
- Short-circuits full LLM call when tool fires (~80% cost saving for metric questions)
- New commit endpoints: POST /ai/assistant/commit-task, POST /ai/assistant/commit-appointment
- 6 ProposedActionPill variants: metric, navigate, create_task, create_appointment, draft_email, send_invoice
- 43/43 regression tests pass

### February 12, 2026 — AI Assistant Pass 4: Extracted + 2 New Tools (Reminder, Bulk Follow-Up)
- Extracted tool-calling subsystem from routes/ai.py → new routes/assistant_tools.py (681 lines)
- New tool: set_reminder ("remind me to call Donald in 3 days") → assistant_reminders collection
- New tool: send_quote_followup_bulk ("follow up on all stale quotes") → GPT-4o-mini + SendGrid bulk send
- New endpoints: POST /ai/assistant/commit-reminder, POST /ai/assistant/bulk-followup-quotes
- 43/43 regression tests pass

### February 12, 2026 — "Show Math" Debug Panel on Pricing Foundation
- ShowMathPanel on Review tab with 4 sub-tabs: Calculation Flow, All Variables, Source Map, Raw JSON
- Calculation Flow: numbered human-readable trail (Dimensions → Area → Material → Labor → Overhead → Final)
- Source Map: shows which Pricing Foundation tab/setting drives each breakdown key
- Verified: Digital Print 24"×24" qty 1 → $88.50 suggested with 12-step flow

### February 12, 2026 — Fee Fix + Founders-Only Flag + Webstore Owner Stripe Connect (Phases A/B/C)
- Phase A: PLATFORM_FEES reshaped to {percent, flat_cents}; WEBSTORE_SURCHARGE_PERCENT=0.020
- Phase B: REACT_APP_SHOW_FOUNDERS_ONLY=true — bypasses ALL tier/feature gating; TierContext short-circuits
- Phase C — Webstore Owner Stripe Connect (2 flows):
  - Backend: owner_stripe_account_id, owner_stripe_charges_enabled on Webstore; WEBSTORE_OWNER role
  - Routes: invite/quick, invite/portal, owner-status, owner-onboard (public token flow), owner-portal
  - Activation gate: cannot set status=active until owner_stripe_charges_enabled=true
  - Auto-transfer on order completion via _maybe_auto_transfer_owner_commission()
  - Frontend: WebstoreOwnerConnectCard (admin), WebstoreOwnerOnboard (public), OwnerPortal (/owner-portal)
  - Tests: 10 fee-math + 21 endpoint tests — all pass

### February 12, 2026 — New "Events" Webstore Product Category
- Added EVENTS="events" to ProductCategory enum
- Mapped to JobItemType.OTHER for order bridge
- Frontend: Events (CalendarDays icon, pink badge) in Products admin + webstore product picker

### February 12, 2026 — Questionnaire Bugs Fixed (Send via Email + Dark-BG Contrast)
- New POST /api/questionnaires/{id}/send-email: requires status=active, validates email, sends branded HTML
- Fixed handleSendEmail to call correct endpoint (was wrongly calling /documents/send-email)
- PublicQuestionnaire dark-bg contrast: replaced hardcoded dark text with text-slate-200/300/400
- 12/12 backend pytest pass (test_questionnaire_send_email.py)

### February 15, 2026 — Admin Audit Log (Prelaunch Gap #1)
- New collection: admin_audit_log (actor, target, tenant, IP, user-agent, summary, metadata, status, timestamp)
- New service: services/admin_audit.py::log_admin_action() (failure-tolerant)
- Wired: impersonation start/exit, onboarding-checklist updates
- New endpoints: GET /platform-admin/audit-log (filterable + paginated), /audit-log/actions, /audit-log/{id}
- New page /platform-admin/audit-log with filter bar, table, detail dialog

### February 15, 2026 — Suspend / Reactivate Tenant (Prelaunch Gap #2)
- New endpoints: POST /platform-admin/tenants/{id}/suspend, POST .../reactivate
- Tenant doc gains: is_active, suspension_reason, suspended_at/by, reactivated_at/by
- Self-lockout protection: cannot suspend tenant containing a platform_admin user
- Login enforcement: suspended tenants get 403 {code: "tenant_suspended"} on login
- Session kill: every protected endpoint checks is_active; existing sessions die on next API call
- Frontend: red "Suspended" badge, Suspend/Reactivate buttons with reason dialogs
- /account-suspended page + suspensionGuard.js + AuthContext interceptor
- E2E verified: suspend → blocked → reactivate → unblocked; 6 audit events captured

### February 15, 2026 — Reactivation "Welcome Back" Email Toggle
- New EmailService.send_tenant_reactivated_email() with optional "note from our team"
- POST /platform-admin/tenants/{id}/reactivate accepts notify_owner: bool (default true)
- Reactivate dialog: "Send 'Welcome back' email" checkbox (default ON)

### February 15, 2026 — Failed-Payment / Dunning Workflow (Prelaunch Gap #3)
- New service: services/dunning.py with record_payment_failure() and record_payment_success()
- Auto-suspend at 3 consecutive failures (DUNNING_AUTO_SUSPEND_AFTER env)
- Auto-reactivate on success (if auto-suspended for payment only)
- Email orchestration: failure 1/2 → "N attempts left"; failure 3 → "account suspended"; reactivate → welcome back
- Webhook wiring: handle_invoice_payment_failed/succeeded call into dunning service
- Manual override: POST /platform-admin/tenants/{id}/mark-paid
- Audit log: payment.failed, dunning.auto_suspend, payment.succeeded, dunning.auto_reactivate, payment.manual_mark_paid
- Frontend: "Billing & Dunning" card on TenantDetail (counters, badges, Mark as Paid button)
- E2E verified: 3 failures → auto-suspend, success → auto-reactivate; 9 audit rows captured

### February 15, 2026 — Dunning Refinements + Email Deliverability Dashboard (Items #3+ and #4)
- Founder 24-hour grace period (DUNNING_FOUNDER_GRACE_HOURS env, default 24)
- Per-tenant failure threshold override: PUT /platform-admin/tenants/{id}/dunning-threshold
- is_founder surfaced on TenantDetail via _enrich_with_founder_flag
- Stripe webhook E2E test (test_dunning_webhook_e2e.py) — 4 phases pass
- Email Deliverability: SendGrid Event Webhook at POST /api/webhook/sendgrid
- email_logs schema: delivery_status, sg_message_id, events[]
- Platform Admin endpoints: GET /platform-admin/email-logs (filterable), /email-logs/summary
- New page /platform-admin/email-logs with summary tiles, filter, table, detail dialog
- E2E verified: sent real email → got sg_message_id → synthetic bounce → delivery_status flipped

### February 15, 2026 — System-wide Announcement Banner + Maintenance Mode (Prelaunch Gap #5)
- New collection platform_settings (id="global") for both announcement + maintenance state
- Public reads (no auth): GET /api/platform/announcement, GET /api/platform/maintenance
- Admin writes (platform_admin only): PUT /platform-admin/announcement, PUT .../maintenance
- Announcement: message, severity, dismissable, optional expires_at; per-user dismiss in localStorage
- Maintenance Mode: ASGI middleware blocks POST/PUT/PATCH/DELETE for non-admins with 503
- Allowlist: /api/auth/, /api/users/me, /api/platform/, /api/platform-admin/, /api/webhook/
- Audit log: announcement.set/clear, maintenance.enable/disable
- Frontend: GlobalBanner (polls every 60s, sticky top), /platform-admin/site-settings page
- E2E verified: maintenance on → user writes 503 → admin writes 200 → off → user writes 200

### February 17, 2026 — Pricing System Refactor (Phases 1–6 Complete)
- Phase 1: /api/pricing/calculate accepts canonical dimensions + aliases; legacy payloads still work
- Phase 2: create_standardized_pricing_result() — 8 cost buckets + breakdown arrays
- Phase 2D: All 9 calculators migrated to standardized response (pricing math unchanged)
- Phase 2E: 14 backend regression tests pinning response shape + math invariants — all passing
- Phase 3: New StandardizedPricingBreakdown frontend component (summary, cost buckets, margin banner)
- Phase 4: Removed ~110 lines of redundant legacy display blocks from PricingCalculator.js
- Phase 5: Simple/Advanced/Audit mode switch; mode persisted to localStorage
- Phase 6: PricingSetupQuiz wizard — 10 sections, converts real-world price answers to suggested defaults

### March 20, 2026 — Stage 1 Critical Fixes + Deployment
- AI rate limiter, promo code system, invoice line items
- Deployment fix: requirements.txt cleaned from 137 → 24 packages
- SendGrid email configured
- Production setup endpoint and page (/setup)

### March 22, 2026 — Complete 4-Layer Order System
- Built: Orders, Job Tickets, Production Tasks, Workflow Templates backend
- Built: Frontend pages (OrdersPage, OrderDetail, NewOrderForm, JobTicketDetail, ProductionBoard, WorkflowTemplateManager)
- 6 default workflow templates, activity logging, status roll-up
- Terms of Service and Privacy Policy pages
- Color scheme: amber/gold → violet/purple across Founders pages
- Founder grace period (14 days read-only after subscription lapse)

### March 23, 2026 — Full Category Schemas
- Built: Banner (24 fields), Apparel (27 fields, size grid), Rigid Signs, Cut Vinyl, Digital Print, Vehicle Wrap (22-30 fields each)
- All material options from centralized catalog; calculator wiring
- Quick Entry / Detailed Entry modes for job tickets
- Legacy Jobs → Orders redirect; dark shell / light content theme global (20+ pages)

### March 24, 2026 — File Upload + Schedule + Materials + Pricing Admin
- Built: File upload system for orders (upload, list, delete)
- Built: Live pricing preview on new order form (real-time pricing API)
- Built: Employee schedule system (weekly grid, shift dialog, save to DB)
- Built: Materials & Pricing admin page (global rates, material CRUD)
- 30 database indexes for production performance

### March 25, 2026 — Pricing + Order Fixes
- Fixed: Setup fee markup bug ($25 was causing $67 increase, now adds exactly $25 flat)
- Fixed across all 6 calculator functions
- Added: Generate Work Order on order detail
- Added: Apparel quantity discounts (5-25% based on qty tiers)
- Improved: Stripe Connect error messaging

### March 26, 2026 — Navigation + UX Fixes
- Fixed: Sales and expense recording (/api/financials/sales + /api/financials/expenses)
- Fixed: Schedule dialog not opening (removed conditional wrapper)
- Fixed: Owner permissions (hasPermission grants all to owner role)
- Fixed: Contact Support now emails donnell@signguy-ai.com
- Navigation: Financials → top-level; Reports = shortcuts page
- Theme: Light theme applied to PricingSetup, CompanySettings, PaymentSettings
- New Order Form: ticket buttons near Save, zero placeholder, better error handling
- Square footage: Default changed to inches (18x24 = 3 sqft)
- Production Board: Shows ticket name first, task name secondary

### March 27, 2026 — Documentation Updates
- Updated all docs (Feature Catalog, Build Roadmap, Docs pages) to reflect Order/Job Ticket system
- Removed all references to old "Jobs" module
- DocsQuotesJobs → DocsOrdersTickets; updated DocsEmployees, GettingStarted, DocsOverview

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CHAPTER 2 — PLATFORM HARDENING + WEBSTORE V2 (Apr 2026)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### April 22, 2026 — Stripe Connect Mode-Safety Hardening
- _scrub_stale_connect_account(): auto-scrubs test-mode accounts on live platform
- /stripe-connect/status: auto-scrubs on load; records audit trail
- /stripe-connect/create-account: refuses test-mode accounts on live platform
- /stripe-connect/refresh-link: returns 409 for stale/wrong-mode instead of broken URL
- account_mode detection: distinguishes livemode=None (unactivated live) from livemode=False (test)
- E2E: ghost test account scrubbed; live account recognized correctly

### April 22–23, 2026 — Payroll / Timeclock Stabilization + Controls
- Fixed recurring break-loss in payroll worksheet (merge same-day shifts, preserve break deductions)
- Added lunch field persistence for timeclock break actions
- Fixed payroll shift edit API to accept explicit null lunch values
- Added POST /api/payroll/mark-paid-in-full (creates/updates period-scoped payment transactions)
- Added "Paid in Full" amount input + action button in PayrollWorksheetToolbar
- Added tenant payroll setting show_payroll_adjustments (default false)
- 14/14 backend + frontend checks pass

### April 23, 2026 — Marketing Site: Features Page + Screenshots
- Replaced all feature screenshots with live preview tenant data (17 real screenshots)
- Added click-to-enlarge lightbox (click to open, close button, click-outside)
- Updated Features page content: removed outdated bullets, aligned to active calculator categories
- Added admin/team/Stripe/reporting coverage highlights
- Verified: category filters, new cards, screenshots, responsive layout

### April 24, 2026 — Webstore Checkout Hardened + Bridge to Main Orders
- POST /api/webstores/v2/orders: blocked unpaid/direct creation; requires real Stripe session idempotency key
- Storefront: verifies session_id via /api/stripe-connect/payment-status/{session_id} before success
- Auto-bridge: webstore checkout orders auto-appear in main Orders list with "Webstore" badge
- _next_order_number_for_tenant() + _ensure_main_order_bridge() helpers
- Banner/logo compatibility fix: maps legacy media fields into branding.banner_url / branding.logo_url
- Webstore list-refresh resilience: normalizeWebstoreList(), one-shot retry, optimistic insert

### April 25, 2026 — Meta OAuth Redirect_uri Fix + Public Data-Deletion Page
- Fixed routes/meta_integration.py to use META_PUBLIC_URL env var instead of request.base_url
- Added META_PUBLIC_URL=https://signguy-ai.com to backend .env
- OAuth flow now reaches Facebook's authorization page successfully
- Created /app/frontend/public/data-deletion.html (raw HTML for Meta crawler compliance)
- Wrapped mailto links in <!--email_off--> to prevent Cloudflare email obfuscation
- Verified: https://signguy-ai.com/data-deletion returns 200 with full content

### April 25, 2026 — Meta/Facebook Messenger Integration (Phase 1)
- Backend: services/meta_service.py (Fernet token encryption, Meta Graph API helpers, audit)
- Backend: services/facebook_ai.py (Claude Sonnet classification + order extraction, 12 labels, 30+ fields)
- Backend: routes/meta_integration.py (OAuth flow, webhook GET/POST, page connect/disconnect)
- Backend: routes/facebook_messages.py (inbox, AI processing, lead/order creation, review)
- Frontend: MetaIntegration.js (Settings > Meta/Facebook page, OAuth connect, page management)
- Frontend: FacebookLeads.js (leads inbox, stats, AI review modal)
- 50/50 backend tests pass
- Status: OAuth works but "No Pages Found" — blocked on user adding 4 Messenger permissions in Meta App

### April 25, 2026 — Stripe Service Layer Extraction
- Extracted all Stripe business logic from routes/webstores.py and routes/stripe_connect.py → services/stripe_service.py
- webstores.py: 2205 → 2034 lines; stripe_connect.py: 1371 → 1190 lines
- New stripe_service.py: 410 lines, single source of truth
- New POST /api/stripe-connect/invoice/{id}/send-payment-link endpoint + frontend modal

### April 26, 2026 — Prelaunch Tier 1–4 Final Mop-Up (Tiers 1-4 all verified)
- Security: Added _require_payroll_view_access() guard to all GET payroll routes (staff → 403)
- New: GET /api/customers/export (CSV stream)
- New: POST /api/workflow-templates/{id}/apply (creates production tasks from template)
- New: POST /api/workflow-templates/{id}/duplicate
- New: GET /api/portal/appointments (customer portal)
- New: GET /api/employee-portal/dashboard (alias of /work-summary)
- Enhanced: GET /api/payroll/report accepts format=csv
- All 6 fixes verified via curl with admin/staff/portal/employee tokens

### April 26, 2026 — Customer Request Appointment + Tier 5 Backend Sweep (28/29 PASS)
- New: POST /api/portal/appointments/request (customer-initiated, status="requested")
- New: PUT /api/appointments/{id}/confirm (admin, supports time/employee override)
- New: PUT /api/appointments/{id}/reject (admin, reason appended)
- Portal UI: "Request Appointment" button + dialog, "Pending Confirmation" amber badge
- Bug fix: DELETE /api/admin/users/{id} with 3 guardrails (self/permission/last-owner)
- Bug fix: Fixed broken Permission.USERS_EDIT references → USERS_MANAGE in routes/auth.py

### April 26, 2026 — Tier 6 Sweep: Admin PDFs + Appointment Email Notification
- Customer appointment request → owner receives HTML email immediately (202 from SendGrid verified)
- GET /api/quotes/{id}/pdf: returns valid PDF with company header, customer, line items, totals
- GET /api/invoices/{id}/pdf: includes PAID/UNPAID watermark, line items, totals
- Tier 6 backend sweep: 20/20 PASS (AI Tools, Floating Assistant, Emails/SendGrid, PDFs)
- Deferred to backlog: GET /api/ai/tools list, POST /api/ai/extract-invoice, payroll PDF, work-ticket PDF

### April 27, 2026 — Tier 7/8: Signatures, Drawings, Docs, Marketing (22/24 + 17/17 PASS)
- Bug fix: DELETE /api/order-drawings/{id} — added platform_admin to allowed roles
- Bug fix: PUT /api/order-drawings/{id} — fixed label↔title mirror sync
- Bug fix: Signature capture — added client_ip field to both internal and public sign routes
- RBAC audit: fixed 5 locations missing platform_admin (employees.py, credits.py, pricing.py x2)
- Tier 8 Docs: all 15 docs pages return 200; 9 marketing pages load correctly
- Docs content updates: Signatures section, Appointment Requests, Invoice Aging, FAQ Billing category

### April 28, 2026 — AI Tool Audits (Read-Only Docs)
- Racing, Business, Marketing, Design, Branding categories audited
- Documents saved to /app/memory/*_TOOLS_AUDIT.md (5 audit files created)

### April 30, 2026 — Design Tools + Racing Tools Cleanup
- Design: Hidden logo_refresher and generative_fill (misleading — uploads not actually sent to AI)
- Design: Renamed text_to_image → "AI Image Concept Creator" with concept-only description
- Design: AI Sign/Banner Designer now emit concise design brief alongside images
- Racing: Hidden Vehicle Wrap Cost Calculator (general tool, not racing-specific)
- Racing: Softened wording on remaining 3 racing tools; Race Team Branding Kit emits written brief

### April 30, 2026 — Customer Branding Profile UI + Marketing Tools Cleanup
- Wired CustomerBrandingTab into customer detail drawer as 5th tab
- AITools deep-link: ?customer={id} auto-fetches branding profile and pre-fills form
- Merged: Completed Order Post Creator + Social Media Job Post Creator (post_mode selector)
- Added conditional required/showWhen field engine in AITools.js
- Improved Social Media Pack Generator and Content Calendar Creator
- 8 new Document Library categories with AI-tool auto-tagging

### April 30, 2026 — Broadcast Email + Platform Admin Runbook
- New POST /api/platform-admin/broadcast-email (audience filters: all/active/suspended/founders)
- Companion: GET /platform-admin/broadcast-email/audience-counts (live recipient preview)
- Sequential delivery, dedupes by email, single audit row per blast
- New page /platform-admin/broadcast-email with subject/body/audience/test-mode UI
- Created /app/PLATFORM_ADMIN_RUNBOOK.md (comprehensive step-by-step walkthrough of every admin feature)

### April 30, 2026 — Broadcast Email Security Hardening
- Body cap: html_body ≤ 50KB, subject ≤ 200 chars, tenant_ids ≤ 1000
- HTML-escape all placeholder values (XSS prevention)
- Rate limit: 10 full broadcasts/hour, 30 test sends/hour per admin (429 over cap)
- Fail-closed if SendGrid not configured (503 instead of silent "0 sent")
- founders_only filter fix: now queries users.distinct("tenant_id", {"is_founder": True})
- Loud audit-log failures: AUDIT_LOG_WRITE_FAILED logged at error level

### April 30, 2026 — Assistant Memory Fix (Options A + B)
- Persistent conversation per (tenant_id, user_id) in assistant_conversations (up to 60 messages)
- New: GET /api/ai/assistant/history, DELETE /api/ai/assistant/history
- Frontend slice bumped: last 10 → last 30 messages; backend context: last 6 → last 20
- Both full-page /ai-assistant and floating assistant hydrate saved history on mount
- Floating assistant: trash-icon "New Chat" button (with confirm dialog) calls DELETE server-side

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CHAPTER 3 — AI PASS 5 + WRAP COMMAND CENTER (May 2026)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### May 15, 2026 — AI Assistant Pass 5: CRM Tools + Actionable Reminders
- New tools: find_customer, attach_note_to_customer in tool router
- New endpoints: POST /ai/assistant/commit-note-to-customer, POST /ai/assistant/dismiss-reminder
- Reminders from set_reminder now surface in Dashboard Nudges widget as "Mark done" pills
- New ProposedActionPill variants: find_customer (sky theme), attach_note (indigo theme)
- 10/10 fees/owner_connect regression + 12/12 new pass-5 tests pass (test_iteration141_assistant_pass5.py)

### May 17, 2026 — Wrap Command Center Phase 1 (Frontend, Modular)
- New page: /app/frontend/src/pages/WrapCommandCenterPage.js
- 23 reusable wrap components under /app/frontend/src/components/wrap/
- Route: /orders/:orderId/items/:itemId/wrap-command-center
- OrderDetail.js: violet "Wrap Workflow" badge + "Open Wrap Command Center" button for wrap categories
- 11/11 acceptance criteria pass (iteration_142.json)

### May 17, 2026 — Wrap Command Center Phase 2A: Vehicle Info + Measurements Persistence
- Wrap data persisted to wrap_data.vehicle_info + measurements; 13/13 backend + 100% frontend pass (iteration_143.json)

### May 17, 2026 — Wrap Command Center Phase 2B: Pricing & Materials + Vehicle Sync
- Materials CRUD + 3 pricing methods
- apply-price-to-order rolls up order_total via workflow_engine.update_order_progress
- Vehicle sync into job_tickets.specs
- 21/21 backend + 100% frontend pass (iteration_144.json)

### May 17, 2026 — Wrap Command Center Phase 2C: Design + Contract + Approvals + Quote Draft + Pipeline
- 10 endpoints: design/contract/approvals/draft-quote/pipeline_state derivation
- QuoteDraftModal; status pipeline chips wired
- 21/21 backend + 100% frontend pass (iteration_145.json)

### May 18, 2026 — Wrap Command Center Phase 2D: Production + Install Workflow
- 8 new endpoints: PUT /production, POST/PUT/DELETE /production/tasks, load-defaults, PUT /install, install issues
- Production: 10 checklist booleans + timestamps, 9 production statuses, default-task seeding
- Install: 14 schedule fields, customer_signoff, issue log CRUD (12 issue types)
- Auto-flip approvals.final_signoff_completed when install_complete AND customer_signoff
- WrapStatusBar lights Production/Install/Complete chips from real state
- New: ProductionTab.js, InstallTab.js
- 25/25 backend + 100% frontend pass (iteration_146.json)

### May 18, 2026 — Wrap Command Center Phase 2E: Inspection + Aftercare + Overview + AI Shell
- 5 new endpoints: PUT /inspection, PUT /aftercare, damage-markers CRUD
- Inspection: customer_acknowledged, damage_markers[], INSPECTION_STATUSES
- Aftercare: 7 AFTERCARE_STATUSES, followup schedule, idempotent timestamps
- Mirror + auto-flip rules between inspection/aftercare and approvals
- Production Board light mirror: _sync_wrap_to_production_board (single row per ticket, never duplicates)
- New: InspectionTab.js, AftercareTab.js, OverviewTab.js, AIAssistantTab.js (rule-based, zero LLM dispatch)
- 24/24 backend + 100% frontend pass (iteration_147.json)

### May 18, 2026 — Wrap Command Center Phase 2F: Polish + Customer Portal Integration
- Backend refactor: routes/wrap.py → routes/wrap/ package (core.py + files.py + portal.py + pdfs.py)
- Visual damage diagram: WrapVehicleDiagram SVG (10 vehicle outlines), click-to-add markers
- Real Photos & Files: 14 categories, 25MB cap, MIME whitelist, per-file customer_visible flag; uses object storage
- PDF generators (reportlab): customer-receipt, aftercare, final-packet → stored as wrap_files
- Customer portal integration: GET /api/portal/orders/{id} now attaches wrap_items[]
- 6 customer portal action endpoints: approve-proof, request-revision, acknowledge-contract/inspection/aftercare, approve-quote
- PortalWrapProjectCard in PortalOrderDetail
- 34/34 backend + 100% frontend pass (iteration_148/149.json)

### May 18, 2026 — Wrap Command Center: Shop Email Notifications
- New services/wrap_notifications.py: send_wrap_portal_action_notification()
- 6 actions wired in routes/portal.py: approve-proof, acknowledge-contract/inspection/aftercare, approve-quote, request-revision
- Idempotency guards (false→true transition only); request-revision fires every time
- Recipient resolution: tenant.notification_email > business_email > email > owner_email
- Failure isolation: customer action still returns 200 on SendGrid/Mongo failure
- 53/53 backend pass (iteration_150.json)

### May 18, 2026 — Wrap Command Center: Launch Polish + Hardening
- Email deep links: 3 inline buttons in every shop notification (Open Order, Open Wrap CC, Respond in Admin Portal)
- Wrap CC respond row: 3 link buttons in WrapCommandHeader (Order, Conversation, Customer)
- Pending Customer Actions Dashboard widget: GET /api/wrap/pending-customer-actions + PendingCustomerActionsWidget
- AI placeholder cleanup: WrapAIHelperCard disabled=true (grey style, "Coming soon" chip); AI helper removed from 6 tabs
- XSS fix: html.escape(..., quote=True) on all hrefs in _render_html
- 66/66 backend pass (iteration_151.json)

### May 20, 2026 — Banner Calculator Phase 2A/2B + Compare Methods
- Backend: Auto-injects 4 starter banner materials (13oz, 18oz, Standard Mesh, Standard Fabric) on first save
- Frontend: BANNER_TEMPLATES constants; Quick Templates (Small Pole Banner, Large Pole Banner); 8 add-ons section
- Compare Methods panel: Price Per SqFt vs Detailed M+L comparison, recommended price (higher of two)
- Use/Use Recommended buttons set overrideEnabled+overridePrice; manual override + clear button
- Expandable detailed breakdown showing all formula inputs
- Math: Small Pole Banner = $60.00 recommended; Large Pole = $95.00 recommended
- 15/15 (iteration_152.json) + 20/20 (iteration_153.json) pass

### May 20, 2026 — Event Store Foundation + Tenant-Controlled Locked Settings
- Added EVENT="event" to WebstoreType enum (4th type)
- New LockedSettings Pydantic model (tenant-controlled cost/profit fields)
- Event-specific fields: event_name, event_type, dates, location, order_deadline, pickup info, auto_close
- store_slug field with _generate_unique_slug() async helper
- WEBSTORE_PUBLIC_FIELDS updated; locked_settings excluded (security)
- Frontend: Event Store as 4th storeType (CalendarDays, orange badge); Event Settings card; Financial Settings card
- 16/16 backend + 100% frontend pass (iteration_154.json)

### May 20, 2026 — Event Store Part 3: Questionnaire Integration
- Added 18 fundraiser questions to event_web_store_setup template (87 questions total)
- GET /{webstore_id}/questionnaire — returns questionnaire status
- POST /{webstore_id}/questionnaire/send — idempotent, prefills + locks fields, sends email
- POST /{webstore_id}/questionnaire/apply-answers — maps safe answers to event store fields
- PublicQuestionnaire: applies prefill_answers on load, renders locked_answer_ids as read-only
- Frontend: Questionnaire status card in Event Store settings; Send dialog with lock notice; Apply Safe Answers button
- 23/23 backend + 17/17 frontend pass (iteration_155.json)

### May 20, 2026 — Fundraiser Field Structure Fix
- Fixed SAFE_MAP in apply_questionnaire_answers_to_event_store (fundraiser_name, goal, etc.)
- Added 17 dedicated fundraiser fields to Webstore model (fundraiser_enabled, goal, progress bar, donations, profit allocation, etc.)
- Fixed missing WebstoreUpdate class declaration
- Updated WEBSTORE_PUBLIC_FIELDS to include fundraiser public fields
- Frontend: Added fundraiserEdits state, Fundraiser Settings card in Event Store settings
- 27/27 backend + 100% frontend pass (iteration_156.json)

### May 21, 2026 — Event Store Part 4: Fundraiser Money Logic + Checkout Donations
- Backend: WebstoreCheckoutRequest accepts donation_amount
- Server-side validates donations (rejects if allow_checkout_donations=false)
- Server-computes profit_allocation_amount (never trusts frontend)
- Stores donation/profit_allocation/shipping_handling in Stripe metadata + payment_transactions
- New Webstore order fields: donation_amount, profit_allocation_amount, grand_total, fundraiser_totals_applied
- _apply_fundraiser_totals: idempotent flag-guarded increment (no double-counting)
- Frontend: Donation block (presets + custom), fundraiser progress bar, S&H line item, grand total
- 6/6 backend + 100% frontend pass (iteration_157.json)

### May 21, 2026 — Event Store P0 Bug Fixes
- Removed product-level pricing fields from store create form (base_item_cost, production_cost, etc.)
- Fixed black screen on Event Store create (sanitize Optional[float] and Optional[date] to null)
- Fixed questionnaire tab black screen (showSendDialog now resets on detail dialog close)
- Fixed WebstoreOwnerConnectCard (rewritten with light-mode CSS variables)
- 14/14 pass (iteration_161.json)

### May 21, 2026 — Customer Portal: Webstores Tab for Assigned Owners
- Backend: GET /api/portal/webstores, GET .../webstores/{id}, Stripe onboarding/refresh/login-link endpoints
- Assignment rule: webstore.owner_email == customer.email (case-insensitive) + tenant_id match
- _sanitize_webstore_for_portal_owner: whitelist-only, strips tenant_id + cost/profit fields
- Dashboard: stats.assigned_webstores + has_webstores; nav tab conditionally inserted
- Frontend: PortalWebstores.js at /customer-portal/webstores with QR, Stripe buttons, Financial Summary, Recent Orders
- 16/16 backend + 100% frontend pass (iteration_158.json)

### May 22, 2026 — Event Store Polish: Supporters Strip + Notifications + Admin Checklist
- GET /api/storefront/{id}/supporters: public Top Donors / Recent Supporters, gated by show_supporter_names
- Donor consent plumbed: WebstoreCheckoutRequest → Stripe metadata → webstore_orders_v2
- One-time assignment notification: _ensure_webstore_assignment_notifications (idempotent)
- Portal notifications: GET/POST /api/portal/notifications (unread_only filter, dismiss, dismiss-all)
- Owner Checklist in PortalWebstores.js (6 items: assigned, questionnaire, stripe, live, first_order, fundraiser)
- Admin Event Store Setup Checklist: 10-item structured checklist with percent_complete
- 26/27 backend + 100% frontend pass (iteration_159.json)

### May 22, 2026 — Storefront "Share this Fundraiser" Button
- Frontend-only, gated by store_type==='event' && fundraiser_enabled
- Uses navigator.share when available; clipboard fallback; AbortError silently ignored
- Share message variants: with goal+raised when goal>0; generic fallback otherwise
- data-testid="fundraiser-share-button"
- Verified via screenshot: present on event+fundraiser store; absent on business store

### May 23, 2026 — Dashboard Phase 1: Backend Contracts + Truth Fixes
- Fix 1: active_jobs/active_orders count from orders collection (not legacy jobs)
- Fix 2: pending_invoices excludes draft; only sent/overdue counted
- Fix 3: today_revenue uses regex prefix match for robust ISO string handling
- New: GET /api/dashboard/summary-v2 (6-metric severity strip with last_updated_at)
- New: GET /api/dashboard/today-command-center (due order items, appointments, team status)
- New: GET /api/dashboard/production-snapshot (stage counts, bottlenecks, at-risk)
- New: GET /api/dashboard/customer-attention (unread conversations, approvals, quote followups)
- New: GET /api/dashboard/financial-attention (unpaid/overdue/due-this-week/recent payments)
- 49/49 backend tests pass (test_phase1_dashboard.py)

### May 23, 2026 — Dashboard Phase 2: Frontend Wiring to V1 Endpoints
- Rewrote Dashboard.js to consume all 5 V1 endpoints
- Row 1: Severity Strip (6 metric badges, neutral/amber/red)
- Row 2: Today Command Center (Due Order Items, Appointments, Team Status)
- Row 3: Production Snapshot (stage counts + At Risk + Bottlenecks)
- Row 4: Customer Attention (Messages, Approvals, Quote Follow-Ups)
- Row 5: Financial Attention (Unpaid/Overdue/Due This Week/Recent Payments)
- Row 6: Quick Actions (9 buttons)
- All .catch(() => {}) replaced with console.warn + per-section error states + retry hooks
- 18/18 frontend tests pass (iteration_162.json)

### May 23, 2026 — Dashboard Phase 3: Correctness + Urgency + Error/Trust States
- ErrorState hardened: data-testid=section-error, visible "Couldn't load" + "Please retry" + Retry button
- Staleness/trust: getFreshness() — "Data may be stale" if >10 min; "Last updated unavailable" if missing
- At Risk sorting: sortAtRisk() with blocked:0, overdue:1, due_within_24h:2 priority
- Customer Attention sorting: sortByUrgency() — urgency_score desc, then timestamp desc
- CTA routing fixes: "Production Board" → /production-board; "Create Invoice" → /invoices
- 19/19 frontend tests pass (iteration_163.json)

### May 23, 2026 — Dashboard Phase 4: Tests + Hardening (46/46 Playwright pass)
- Full Playwright E2E suite at /app/tests/test_dashboard_phase4.py
- Coverage: smoke, empty states, error states, retry, staleness, CTA routing, ordering, guardrails, DOM links
- UI fix: SeverityStripWidget renders ErrorState when summary-v2 fails
- UI fix: Today's Command Center shows "Last updated unavailable." when timestamp absent

### May 23, 2026 — Dashboard Phase 5: Cleanup + Deprecation Removal
- Removed GET /api/dashboard/todays-schedule and GET /api/dashboard/clocked-in
- Removed unused Pydantic models (ClockedInEmployee, ScheduleItem)
- Realigned 4 test files to V1 contracts; all 47/47 Phase 1 backend + 46/46 Phase 4 Playwright pass

### May 24, 2026 — Webstore Phases 1–4: Ribbon + Wizard + Questionnaires + Customer Sync

#### Phase 1: Webstore Crash & Trust-State Hardening
- handleViewStore: opens dialog BEFORE any awaits (fire-and-forget IIFEs for data fetching)
- WebstoreDetailDashboard.js: Promise.allSettled, visible error card + Retry button
- PortalWebstores.js: surfaces non-OK responses via setError/portal-webstores-error Alert
- Defensive guard on eventChecklist.items in Webstores.js
- 3/3 retargeted checks PASS (iteration_165.json)

#### Phase 2: Navigation Consolidation + Office-Style Ribbon
- New WebstoresRibbon.js: 10-group Microsoft Office-style command ribbon
- MainLayout.js: conditionally swaps ActionToolbar for WebstoresRibbon on /webstores routes
- 9/9 frontend checks PASS (iteration_166.json)

#### Phase 3: Store Setup Wizard
- New StoreSetupWizard.js: 9-step wizard (Store Type → Basics → Owner → Branding → Dates → Fulfillment → Questionnaire → Payments → Review)
- wizard-recommended-warnings data-testid for missing recommended items
- 9/10 PASS (iteration_167.json); remaining issue fixed post-report

#### Phase 4: Store-Type Questionnaire Coverage + Customer/Order Sync
- Added 3 new questionnaire templates: fundraiser_web_store_setup, team_school_web_store_setup, business_web_store_setup
- _template_key_for_store_type() dispatcher; aliases for all store type variants
- Customer tags: webstore_owner (on create/invite), webstore_customer (on checkout/job-from-order)
- Orders: source="webstore" stamp + webstore_id query params on GET /api/orders
- 13/13 backend tests PASS (iteration_168.json)

### May 24, 2026 — Webstore Phase 5: Owner Portal Progress + Financial Transparency
- Phase 4 enhancement: GET /api/customers/{id}/webstores → customer-webstore join
- Phase 5 backend: GET /api/owner-portal/stores/{webstore_id}/progress (15 lifecycle stages, 6 required actions, live finance block)
- Finance values computed LIVE from webstore_orders_v2 (matches analytics endpoint — no source-of-truth drift)
- Privacy guard: strips cost/margin/supplier/staff notes from response
- Frontend: OwnerStoreProgressPanel.js (lifecycle progress, required actions, financial summary)
- HIGH finding fixed: finance source-of-truth drift; both endpoints now return $40 / 2 orders for test store
- (iteration_169.json)

### May 29 / June 1, 2026 — Webstore Phase 6: Admin Workflow Polish + Orders/Customers Filters
- Backend: GET/PATCH /api/webstores/v2/{id}/admin-progress (tenant-scoped, stage stamps)
- Bug fix: Added COMPLETED + CLOSED to WebstoreStatus enum (GET no longer 500s after mark_completed)
- _build_store_progress_payload now returns stage_stamps dict (raw timestamps)
- Frontend: AdminStoreProgressCard.js (lifecycle bar + 15-stage pills + 3 stamp buttons + money summary)
- OrdersPage.js: orders-source-filter + orders-webstore-filter selects; deep-link ?webstore_id=
- Customers.js: tag-chip row (all/webstore_owner/webstore_customer); inline role badges
- All 3 HIGH/MEDIUM findings fixed (iteration_170.json)

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## CHAPTER 4 — STOREFRONT POLISH + SETUP FLOW OVERHAUL (Jun 2026)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### June 5, 2026 — Webstore Phase 7: Public Storefront Polish + Hardening
- Status-aware screens: Coming Soon (pending), Store Closed (completed/closed), Unavailable (disabled)
- Pickup/delivery info band on active storefronts
- Admin preview mode: GET /api/storefront/{id}/preview (admin JWT); ?admin_preview=1 URL param + yellow banner
- Product category grouping by category with section headers and counts
- Better image fallbacks: styled gradient placeholder (category color + icon)
- webstore_stage_events audit trail: auto-logs status_changed, stage_stamped, admin_preview_accessed
- 21/21 backend + all 7 Phase 7 UI features verified (iteration_171.json)

### June 5, 2026 — Webstore Setup Flow Simplification
- StoreSetupWizard.js: 9-step → 3-step minimal flow (Store Type → Basics → Owner Info)
- After creation: CreationResult screen with "Send Setup Questionnaire" card (email pre-filled)
- If email fails: amber warning + copyable questionnaire link fallback
- 12/12 acceptance criteria PASS (iteration_172.json)

### June 5, 2026 — Questionnaire Support for All Store Types
- All 4 store types (event, fundraiser, creator/team, business) now show questionnaire card
- getQuestionnaireLabel helper with store-type-specific labels
- getQStatusPhase + Q_PHASE_CONFIG for 5 visible states (Not Sent/Sent/Awaiting Review/Applied/Draft)
- 12/12 PASS (iteration_173.json)

### June 5, 2026 — Webstore Owner Stripe Connect Buttons Fixed
- AppContext.js: Added getWebstoreOwnerStatus + sendWebstoreOwnerInvite with correct response field mapping
- WebstoreOwnerConnectCard.js: Fixed charges_enabled, owner_stripe_account_id, success field names
- 502-from-SendGrid now shows friendly error message instead of raw error
- 10/10 + 11/11 pytest PASS (iteration_174.json)

### June 5–6, 2026 — Consolidated Webstore Setup Flow + 6-Tab Structure
- WebstoreSetupFlow.js: Completely rewritten from 8 to 11 sequential steps (Store Created → Questionnaire → Review → Branding → Products → Fulfillment → Stripe → Preview → Approval → Open Store)
- Webstores.js: Tab structure → 6 tabs (Store Setup / Products / Branding / Payments / Orders / Analytics)
- Store Setup is now the default tab; settings distributed to correct tabs
- Added questionnaire_reviewed, questionnaire_submitted_at, questionnaire_reviewed_at to Webstore Pydantic model
- P0 Fix: IndentationError at line 3700 in webstores.py (backend was completely DOWN)
- P1 Fix: review-details endpoint fixed for dict-style answers AND flat questionnaire questions
- StaffReviewPanel renders with all testids; launch button unblocked after questionnaire review
- 3/3 pytest + 14/14 frontend requirements verified (iteration_177.json)

### June 6, 2026 — Security Code-Review Remediation (Part 1)
- Removed recover_owner_password (credentials in query params)
- Secure token-based password reset: POST /auth/forgot-password + POST /auth/reset-password (SHA-256 hash, 60-min expiry, single-use)
- setup-admin gated behind ENABLE_SETUP_ADMIN=true env flag (default OFF → 404)
- CORS: allow_origin_regex=".*" replaces literal "*" (browser-rejected with credentials)
- Frontend: forgot-password flow + new ResetPassword.js page at /reset-password?token=…

### June 6, 2026 — Security Code-Review Remediation (Part 2)
- Workflow template update scoped by tenant_id (prevents cross-tenant update)
- Tenant lookup key standardized from {"tenant_id": ...} to {"id": ...} across 8 files (was always None → fell back to default "SignGuy AI" branding)
- Backup owner-role check: enum-safe _is_owner() helper
- Backup restore atomicity: snapshot-and-rollback (partial failure no longer causes data loss)
- 3/3 pytest (test_backup_security.py)

### June 6, 2026 — Questionnaire Submit Validation Hardening
- iter_questionnaire_questions(): walks top-level AND nested sections[*].questions
- _answer_is_empty(): None/blank/empty-list aware; numeric 0 counts as answered
- _question_is_visible(): mirrors storefront conditional logic (equals/not_equals/contains/greater_than/less_than)
- Rewrote submit validator: skips non-input, locked fields, hidden-by-condition; enforces required+format on visible only
- 9/9 unit tests (test_questionnaire_nested_validation.py)

### June 6, 2026 — Branding & Templates Settings (Invoice / Email / Document)
- New BrandingSettings model in backend/models/auth.py (invoice/email/document sub-sections)
- Settings UI in CompanySettings.js: Branding & Templates card
- Invoice preview: real tenant name/address, branded logo, accent color, payment terms, custom footer
- Email: send_email wraps HTML in branded shell (logo header, header color, signature), from-name override
- Document PDFs: embeds tenant logo, header text, footer text
- New BrandingPreview.js: live side-by-side Invoice/Email/Document mini-previews (updates in real time)

### June 6, 2026 — Branding Tab Cleanup + Launch Gate Verification
- Removed duplicate "Store Link / QR Code" section from top of Branding tab
- Launch gate verified: backend blocks activation with 0 products; frontend shows disabled button
- 100% tested (iteration_176.json)

### June 6, 2026 — Store Snapshot Feature
- New StoreSnapshotModal.js: branded, printable snapshot with QR code
- Accessed via "Store Snapshot" button in Analytics tab
- Includes: accent-color header, QR code, store URL, 4 KPI tiles, fundraiser progress (if applicable), top products list, footer
- "Print / Save as PDF" opens new window with inline-styled print-ready HTML (QR code via QRCodeCanvas → data URL)
- data-testid="store-snapshot-btn" and data-testid="snapshot-print-btn"

### June 6, 2026 — Admin Analytics Dashboard (Platform Admin Only)
- New route: /platform-admin/analytics (platform_admin role only)
- Backend: /app/backend/routes/admin_analytics.py — 8 endpoints (overview, activity-chart, users, routes, sessions, referrers, errors, suspicious)
- Frontend: /app/frontend/src/pages/PlatformAdminAnalytics.js — 8-tab dashboard
- Tracker: /app/frontend/src/utils/analytics.js — lightweight event tracker (visitor_id/session_id, auto page views, global error capture)
- Collection: analytics_events (indexed on timestamp, event_type, session_id, user_id, route, ip_address)
- PageTracker component + error init in App.js for automatic tracking
- "Analytics" button added to /platform-admin nav
- 38/38 backend + 100% frontend pass (iteration_178.json)

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## UPCOMING WORK (As of June 6, 2026)
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### P1 — Next Up
- Yard Signs Pricing Setup and Calculator Integration
- Rigid Signs, Digital Print, Cut Vinyl, Vehicle Graphics Category Integrations

### P3 — Future
- Platform Admin Phase 2 Extensions (Internal Notes, User invite flow)
- Admin Portal communication template system
- Meta Messenger Phase 2 (dashboard widgets, auto-replies, notification system)

---

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## QUICK REFERENCE
## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Test Credentials
See /app/memory/test_credentials.md

### Key Files
- Backend routes: /app/backend/routes/
- Frontend pages: /app/frontend/src/pages/
- Frontend components: /app/frontend/src/components/
- Services: /app/backend/services/
- Test reports: /app/test_reports/iteration_*.json

### Architecture
- Frontend: React + Shadcn UI + Tailwind CSS
- Backend: FastAPI + Motor (async MongoDB)
- Database: MongoDB (Motor async driver)
- Auth: JWT (admin), custom portal JWT (customer/employee/owner)
- Payments: Stripe Connect (platform account + tenant onboarding)
- Email: SendGrid via EmailService
- AI: OpenAI (via Emergent LLM Key), Claude Sonnet (via Emergent LLM Key)
