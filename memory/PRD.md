# SignGuy AI - Product Requirements Document

> **Last Updated:** Feb, 2026
> **Version:** 7.4

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

### Session: Feb 2026 — Business Assistant Phase 1 (Dangerous Wiring & Safety)
- **Schema-mismatch write handlers rewritten** in `backend/services/ai_assistant_actions.py`:
  - `_handle_create_order` — now uses the canonical `Order` Pydantic model, runs the same `_next_order_number` logic as `routes/orders.py`, auto-creates leads when needed, writes to real `orders` + `order_activities` collections, validates `pickup_delivery_method` against the enum, and returns `navigate_to` path.
  - `_handle_create_job` — **deprecated as separate path**; now an alias to `_handle_create_order`. Eliminates orphan records in `db.jobs` that were invisible to the Orders / Production / Invoicing pipeline.
  - `_handle_create_invoice` — **now requires `order_id`**; pulls real `job_tickets`, builds `line_items` with `job_item_id` linkage, links invoice back to the order (`linked_invoice_ids`), writes `order_activities` log entry. Rejects fabricated no-order invoices with a clear error.
  - `_handle_create_calendar_event` — rewritten to write to the canonical `db.appointments` collection (used by `/api/appointments` + Schedule), with `AppointmentType` / `AppointmentStatus` enum validation and customer resolution.
- **Voice-safety rule**: new `WRITE_ACTIONS` set + `source` field on `ActionRequest` / `ExecuteActionRequest`. When `source == "voice"` ALL write actions require confirmation (not just the destructive subset). Prevents misheard voice commands from creating records silently.
- **Frontend regex intent detection removed** (`FloatingAssistant.js`). `detectAndExecuteAction` and 5 per-intent handlers deleted. Single classifier path: `/assistant/parse-action?action_type=auto` → LLM returns `{intent, parameters, needs_more_info, question}`. Frontend routes to confirmation UI or chat based on intent.
- **Auto-classify** added to `parse_action_intent` in `backend/routes/ai.py`. New branch handles `action_type == "auto"` with JSON-shaped output covering 6 intents.
- **Verified via curl**:
  - auto-classify extracts company_name/due_date from "create an order for Acme Corp due Friday"
  - AI-created orders land in `/api/orders`, use real `ORD-####` numbers, match canonical schema
  - `source="voice"` forces `pending_confirmation`, `source="text"` executes
  - `create_invoice` without `order_id` → clear 400-style error
  - `create_invoice` with real `order_id` + tickets → INV-##### at correct total, navigate_to populated

### Session: Feb 2026 (New Order Code Review — Full Sweep: C1–C3, H1–H5, M1/M2/M4/M6/M7, L1/L2/L9/L11/L12)
- Completed comprehensive code review of the New Order lifecycle (`NewOrderForm.js`, `AddOrderItemMenu.js`, `CloneItemDialog.js`, `SharedContextPanel.js`, `LivePricingPreview.js`, `DynamicCategoryFields.js`, `orders.py`, `job_tickets.py`, `workflow_engine.py`). Documented 3 Critical, 5 High, 7 Medium, 12 Low findings and fixed 18 of them.
- **Criticals:** C1 (shared-context fields added to `OrderCreate`), C2 (manual-price preservation on ticket update), C3 (category enum drift `promotional`→`promo_misc`), plus Jobs.js EOF syntax error.
- **Highs:** H1 (clone menu disabled pre-save), H2 (parallel save with `Promise.allSettled`), H3 (AlertDialog replaces `window.confirm`), H4 (upfront blank-name validation), H5 (status whitelist on create).
- **Mediums fixed:**
  - M1 — `LivePricingPreview` uses `onPriceChangeRef` to avoid effect re-runs on every parent render.
  - M2 — Removed redundant `formData.append('label', filename)` — backend already falls back to filename.
  - M4 — `SharedContextPanel.onChange` now emits patch *delta* only; `NewOrderForm` does functional-state merge. Prevents accidental full-state clobber in future refactors.
  - M6 — `_next_ticket_number` now probes for an unused ticket number with up to 50 offsets + UUID fallback, eliminating concurrent-creation race.
  - M7 — New `frontend/src/lib/jobCategories.js` module — single source of truth; `NewOrderForm` and `CloneItemDialog` both import from it.
- **Mediums deferred (documented):** M3 already mitigated by H2; M5 (UTC auto-name) blocked on per-tenant timezone data.
- **Lows fixed:**
  - L1 — Removed 2 redundant "Add Item" entry points (per-ticket "Add Item to Order" button and post-list Quick/Detailed strip). Reduced from 6 → 4 entry points.
  - L2 — `seed_default_templates` now caches seeded tenant IDs in-process, skipping the DB roundtrip on subsequent calls.
  - L3/L8 — Rolled into M6 fix (same ticket-number logic).
  - L9 — `POST /api/orders/{id}/upload` now whitelists MIME types (image/*, video/*, audio/*, PDF, PS, PSD, zip, office, text). Unsupported types return HTTP 400.
  - L11 — Added `"undecided"` / "Undecided / TBD" option to `PickupDeliveryMethod` enum + dropdown.
  - L12 — `DynamicCategoryFields` schema-per-category now cached in a module-level `SCHEMA_CACHE` Map. Switching between tickets of the same category no longer refetches.
- **Lows deferred:** L4 (silent NaN→0 is safer UX), L5 ("Use as new customer" customer creation is a scope change), L6 (intentional, documented), L7 (out of review scope), L10 (`navigate` handles it).
- **Verified via curl:** M6 (5 parallel tickets → ORD-0012-T1..T5 unique), L9 (bad MIME 400 ✓, image/png 200 ✓), L11 (undecided pickup persisted ✓). Lint clean, webpack compiled successfully.

### Session: Apr 20, 2026 (Services Category — Pricing Foundation)
- Implemented full Services pricing category matching exact user spec; extended existing Pricing Foundation (no parallel system).
- **Backend:**
  - `models/enums.py`: `ServiceType` expanded to 21 values (graphic_design, artwork_setup, file_cleanup, consultation, site_survey, measurement, delivery, installation, removal, maintenance, vehicle_graphics_install, wrap_install, service_call, project_management, permit_handling, equipment_rental, subcontracted, general_labor, specialty_custom, travel, other_labor).
  - `models/pricing.py`: `services` category_defaults rebuilt with 19-entry service-type library (each with default_billing_unit, default_labor_role, default_sell_rate, default_flat_fee, default_minimum_charge, sell_method, travel/equipment/subcontract flags), 9 billing units, 9-role labor rate map (cost + sell per hour), 4-tier complexity multipliers (1.0/1.25/1.5/2.0), travel rates ($0.65 cost/$1.25 sell per mile, $45 trip), equipment library (scissor/boom lift, ladder rig, generator, utility truck, custom) with cost_per_day + sell_per_day + cost_per_hour + sell_per_hour, subcontract_markup_percent 20%, minimums (design $25, service call $50, install $125, global $25), rush 25%. Added 22 new `JobItemPricingData.services_*` fields.
  - `server.py`: `calculate_services` fully rewritten as service-type + billing-unit dispatcher. Supports hour/flat/piece/sqft/linear_foot/mile/trip/day/custom billing math. Sell methods: `cost_plus`, `pass_through_plus_markup`, `max_of_both`. Cost side tracks labor, travel, equipment, subcontract, permit separately; sell side uses per-service-type baseline + travel_sell + equipment_sell + subcontract_sell + permit_sell, then floored by per-service-type minimum or override, then rush.
  - `routes/job_tickets.py`: `_services_schema` rebuilt Foundation-driven (26 fields). `_build_ticket_pricing_payload` passes all `services_*` inputs.
- **Frontend:**
  - `PricingFoundation.js`: Services admin card (default service type, default labor role, minimums, rush %, labor role rates, travel rates, equipment library, subcontract markup).
  - `PricingCalculator.js`: Services case rewritten with full dynamic UI — service-type switch auto-sets billing unit + labor role + travel/equipment/subcontract flags; conditional flat-fee and unit-rate-override fields; 24+ `svc-*` test IDs.
- **Testing:** testing_agent_v3_fork iteration_114 = 100% pass (backend 29/29, frontend 100%, 0 issues, 0 action items). Backend curl matrix at `/app/test_reports/services_backend_tests.txt` (22 scenarios covering every billing unit + sell method + add-on).

### Session: Apr 20, 2026 (Apparel Category — Pricing Foundation)
- Implemented full Apparel pricing category matching exact user spec; extended existing Pricing Foundation (not a parallel system) and designed for multi-decoration-method expansion.
- **Backend:**
  - `models/pricing.py`: Added 13 new `apparel_blank` materials (Gildan 5000/2400/18000/18500/8800; Bella+Canvas 3001/3501/3901/3719/3415; Standard + Premium Cap; Visor) with cost_per_unit + retail_base_no_print. Rewrote `apparel` category_defaults with: `available_decoration_methods` (9 methods), `methods_using_shop_table` (htv/screen_print_transfer/dtf_transfer), `method_config` (per-method pricing rules with uses_shop_table flag), `available_product_types`, `available_brand_styles`, `placement_sets`, `quantity_tiers`, full `shop_pricing_table` (13 blank keys × 5 tiers × 3 placements), add-on rates (plus_size $2, custom_name_number $4/$3, specialty $2/$1.50, two_tone_hat $1.50, leather_patch $2.50, bag_and_fold $1), setup-by-complexity, rush range. Added 17 new JobItemPricingData apparel fields.
  - `server.py`: `calculate_apparel` fully rewritten as method-dispatcher. Shop-table methods pull exact per-piece sell; cost-plus methods use method_config (color/stitch/sqin rules + setup + labor + markup). Adds plus-size/names/specialty/two-tone/patch/bag-fold/setup × complexity. Enforces retail_base floor per piece. Supports rush % override and manual_quote_override.
  - `routes/job_tickets.py`: `_apparel_schema` rewritten (34 Foundation-driven fields). `_build_ticket_pricing_payload` passes all new apparel_* fields + auto-derives apparel_plus_size_count from size breakdown (2XL=1x, 3XL=2x, 4XL=3x, 5XL=4x per spec).
- **Frontend:**
  - `PricingFoundation.js`: Apparel admin card (default method, setup fee, min sell, rush %, all add-on rates, setup-by-complexity, apparel_blank list).
  - `PricingCalculator.js`: Apparel case rewritten with dynamic UI — product type switches brand list + placement options + hat-only add-ons; all 22 `ap-*` test IDs (product/brand/color/placement/method/colors/stitch/plus-size/manual/artwork/complexity/custom-nn/nn-count/specialty/two-tone/patch/bag-fold/rush/rush-percent/blank-override).
- **Methods fully priced now:** HTV, Screen Print Transfer, DTF Transfer (all using uploaded shop quantity table).
- **Methods structurally supported + cost-plus scaffolded:** Direct Screen Print (per-color amortized setup), Embroidery (per 1k stitches), DTG (flat per-piece), Patch/Emblem, Sublimation (per sq in), Specialty/Custom. Each method has its own `method_config` block; shop can later add per-method pricing tables without engine changes.
- **Testing:** testing_agent_v3_fork iteration_113 = 100% pass (0 backend issues, 0 frontend issues, 0 action items, retest_needed=false). Backend curl matrix at `/app/test_reports/apparel_backend_tests.txt` (20 scenarios).

### Session: Apr 20, 2026 (Vehicle Graphics / Wraps Category — Pricing Foundation)
- Implemented full Vehicle Graphics / Wraps pricing category following exact user spec, mirroring Banner/Rigid/Cut Vinyl/Digital Print robustness.
- **Backend:**
  - `models/pricing.py`: Added 10 new wrap materials (wrap_standard_calendared, wrap_premium_cast, wrap_cast_film, wrap_reflective, wrap_etched_frost, wrap_specialty_media, wrap_laminate_gloss/matte/satin, wrap_window_perf). Rewrote `vehicle_wraps` category_defaults with ~30 new spec fields: install_hours_by_vehicle_coverage, package_pricing_by_vehicle_coverage, install_difficulty_multipliers, seam_complexity_multipliers, surface_prep_hours, removal_hours, design_time_by_coverage_hours, waste_by_coverage, window_perf_sell_rates, etc. Added 11 new JobItemPricingData fields.
  - `models/enums.py`: Added `CoverageType.CUSTOM = "custom"`.
  - `server.py`: Rewrote `calculate_vehicle_graphics` with full spec: coverage resolution (with custom % interpolation), vehicle-type × coverage install hours, difficulty × seam multipliers, optional second installer helper labor, window perf area/sell, surface prep, removal + consumables, max-of-package-or-cost-plus pricing.
  - `routes/job_tickets.py`: Rewrote `_vehicle_wrap_schema` to dynamically pull vehicle types, wrap materials, laminates from Foundation. `_build_ticket_pricing_payload` passes all new wrap fields. `_normalize_vehicle_coverage` preserves `custom`.
- **Frontend:**
  - `PricingFoundation.js`: Added Vehicle Wraps admin card (default material/laminate, install rate, helper rate, rush %, waste % by coverage, design time by coverage, prep/removal hours, install difficulty multipliers, seam multipliers, window perf sell rates).
  - `PricingCalculator.js`: Rewrote vehicle_graphics UI with all 18 spec controls (vehicle type, coverage, custom %, make/model, wrap material, laminate toggle + type, window perf toggle + scope, artwork ready/needed, design complexity, surface prep, removal, install required, install difficulty, seam complexity, second installer, rush, sqft override). Added Switch import.
- **Testing:** backend 20/20 ✓, frontend 100% ✓ via testing_agent_v3_fork iteration_112. Pytest suite at `/app/backend/tests/test_vehicle_graphics.py`. All spec test scenarios pass: vehicle change, coverage change, custom % interpolation, material change, laminate on/off + type, window perf rear/side, design complexity, surface prep, removal, install on/off, difficulty, seam, second installer, rush, quantity, schema, foundation admin, calculator UI, live breakdown.

### Session: Apr 2026 (Banners Category — Pricing Foundation)

### Session: Apr 2026 (TimeClock Stale Shift Auto-Close — P0 Bugfix)
- Fixed TimeClock incorrectly showing employees as "Working" on selection, caused by orphaned open shifts in the DB
- Added `STALE_SHIFT_HOURS = 18` threshold in `/app/backend/services/timeclock_service.py`
- New helpers: `_auto_close_stale_shift()` and `_cleanup_stale_open_shifts()` — any shift open longer than 18h is auto-closed with `clock_out = clock_in + 8h` cap, `status=finished`, `auto_closed=true` flag, and recomputed metrics
- `get_timeclock_status()` and `record_timeclock_action()` both run the cleanup defensively before evaluating state
- Verified via `/app/backend/tests/test_timeclock_stale.py`: stale shifts auto-close and return `not_started`; fresh shifts (<18h) remain `working`

### Session: Feb 2026 (BUBBLE Documentation Update)
- Updated all four `BUBBLE_*.md` documentation files to reflect the current codebase state:
  - `BUBBLE_DATABASE_SCHEMA.md` (843 lines) — All collections including timeclock_shifts, payroll_signoffs, order_drawings, signatures, tenants with payroll_settings, Object Storage mapping
  - `BUBBLE_PAGE_MAP.md` (337 lines) — All current routes, Payroll Worksheet components, Unified Productivity views, Customer/Employee Portals, public pages
  - `BUBBLE_WORKFLOWS.md` (450 lines) — All workflows including Payroll Worksheet load/save/signoff/legacy, Drawing/Signature capture, Unified Productivity aggregation, Time Clock shifts
  - `BUBBLE_DEPENDENCY_MAP.md` (337 lines) — Updated dependency graph with Object Storage, Payroll Worksheet state, Productivity compound UIDs, external service dependencies

### Session: Feb 2026 (Terminology Migration: Job/Job Ticket -> Order/Order Item)
- Migrated all user-facing terminology from "Job"/"Job Ticket"/"Job Item" to "Order"/"Order Item" across the entire frontend
- 45+ files updated: pages, components, docs, marketing, portals, libs
- Zero user-facing instances of "Job Ticket", "Job Item", or standalone "Job" remain
- Backend routes/collections/field names unchanged (internal compatibility layer)
- Files changed: OrderDetail.js, NewOrderForm.js, AddTicketToOrder.js, OrdersPage.js, JobTicketDetail.js, Quotes.js, Jobs.js, Customers.js, Invoices.js, Approvals.js, Payroll pages, Productivity, AI Tools, Admin Portal, Webstores, all Docs pages, Marketing pages, Portal pages, Settings pages, components (Ribbon, FloatingAssistant, InvoicePreview, JobHistory, AIEmail, PricingCalculator, UpgradeModal, TrialLockout, DocsLayout, OrderCommandBar, ProductivityFiltersBar), libs (payrollExport, productivity)

### Session: Feb 2026 (Quick Camera Upload & Markup)
- Added Quick Photo capture/upload + immediate markup flow on Order Detail and Order Item Detail pages
- Enhanced DrawingCanvasPad with 4 annotation tools: Draw (freehand), Arrow, Circle, Text
- Order Detail: "Photo" dropdown button with "Take Photo" (camera) and "Choose from Gallery" options; per-item "Quick Photo" in dropdown menu
- Order Item Detail: "Quick Photo" and "Choose Photo" buttons in shortcut actions row
- Flow: capture/select image -> auto-upload to order files -> immediately open Drawing Modal with photo as background for markup
- Original photo saved in Files tab, marked-up version saved in Drawings tab
- Mobile-first: uses `capture="environment"` for native camera on mobile devices
- All built on existing infrastructure: order file upload route, order-drawings API, Object Storage, DrawingModal, DrawingCanvasPad
- Files changed: DrawingCanvasPad.js (enhanced tools), OrderDetail.js (Quick Photo flow), JobTicketDetail.js (Quick Photo flow)
- Testing: iteration_107 passed 100% (all tools, buttons, flow verified)

### Session: Feb 2026 (Pricing Foundation — Unified Admin Page)
- Created new `/pricing-foundation` page consolidating PricingSettings, MaterialsAdmin, and general shop defaults into one single source of truth
- **3 Tabs:**
  - **Shop Defaults** — Labor rates (production/design/install/admin), overhead %, waste %, markup multiplier, target margin, material markup, all 8 minimum charges, rush fee %, setup fees (6 types), rounding rule, deposit %, quantity break tiers, time estimates, travel rates
  - **Materials Library** — Enhanced material records with: key, name, category, subtype, brand, thickness, width/length, roll/sheet size, purchase unit/cost, cost per unit, cost per sqft, sell rate per sqft, waste factor, compatible categories, active/inactive, notes. Grouped by 8 categories with expandable cards.
  - **Category Rules** — 8 category tabs (Cut Vinyl, Banners, Rigid Signs, Vehicle Wraps, Apparel, Services, Custom, Digital Print) each with: labor hours, markup multiplier, target margin %, minimum charge, default materials, selling benchmarks
- Extended `PricingDefaults` model with: `admin_hourly_rate`, `waste_percentage`, `minimum_design_charge`, `minimum_install_charge`, `rush_fee_percentage`, `setup_fee_default`, `rounding_rule`, `deposit_percentage`
- Extended `MaterialConfig` model with: `subtype`, `brand`, `thickness`, `width_inches`, `length_inches`, `roll_sheet_size`, `purchase_unit`, `purchase_cost`, `cost_per_sqft`, `sell_rate_per_sqft`, `waste_factor`, `compatible_categories`, `notes`
- Added `apply_rounding()` utility to server.py
- Routes: `/pricing-calculator/settings` and `/materials` now redirect to `/pricing-foundation`
- Navigation updated: Ribbon and PrimaryNav point to Pricing Foundation
- Reads/writes via existing `GET/PUT /api/pricing/defaults` — no new backend routes
- Testing: iteration_108 passed 100% (all tabs, fields, save flow, redirects, API verified)

### Session: Apr 2026 (Timeclock Timezone Bug Fix)
- **Root cause**: `get_timeclock_status` and `record_timeclock_action` used `datetime.now(timezone.utc).date()` (UTC date regex) to find timelogs/shifts. After UTC midnight (8pm ET), clock-in from the same local day became invisible because the UTC date rolled over.
- **Fix**: Status now checks for ANY open shift record (`status in ["working","on_break"]`) across all dates — no date filter. Action sequence validation also uses open shift state. `get_today_logs` uses a 36h window instead of UTC date regex. Frontend `getShiftSummary` now passes local date.
- Files changed: `timeclock_service.py`, `routes/employees.py`, `context/AppContext.js`
- Testing: iteration_109 passed 100% (16/16 backend, full frontend flow verified)

### Session: Apr 2026 (Payroll Worksheet Save Fix)
- **Root cause 1**: When an employee is clocked in (active shift with no end time), the payroll worksheet validation blocked ALL saves with "Add both start and end time for {day}" — even if the user only wanted to save OTHER days or adjustments.
- **Root cause 2**: Legacy manual entries with dates outside the current pay period caused 400 errors on every save. The save loop re-submitted ALL legacy entries, and the backend rejected entries whose `target_date` fell outside `week_start..period_end` range. This was the primary "Failed to save payroll worksheet" error.
- **Fix 1**: Validation now detects active shifts (`shiftStatus === 'working'` or `'on_break'`) and skips them. Save loop also skips actively-working rows.
- **Fix 2**: Frontend now skips legacy entries whose target_date is outside the current pay period. Backend now clamps target_date to the range instead of rejecting with 400.
- Files changed: `Payroll.js` (validation + save loop + legacy entry filter), `payrollWorksheet.js` (shiftStatus), `routes/employees.py` (clamp instead of reject)
- Testing: verified via UI — saves work correctly, zero failed requests

### Session: Apr 2026 (Payroll Worksheet Architecture Rewrite)
- Replaced `useCallback`/`useEffect` dependency chain with ref-based load (apiRef, loadVersionRef, debounce)
- `hasShiftContent()` now excludes notes — notes alone don't require start/end times
- Legacy entries only saved when changed (baselineLegacyRef diff tracking)
- Save is now section-by-section: employee info, shifts, adjustments, legacy, signoff — each in own try/catch
- Testing: iteration_110 passed 100%

### Session: Apr 2026 (Bugs + Features Batch)
**Bugs fixed:**
- Productivity: removed duplicate in-page view nav (PrimaryNav handles it), fixed stale closure on loadCore/loadCalendar with refs, added toast on task creation from calendar
- Productivity: default itemTypes now includes `['job', 'task']` so tasks show by default
- Dashboard restored at `/dashboard` as standalone page (no longer redirects to productivity)

**Features added:**
- Customer: name OR company required (not both), new `display_name` field auto-generated from company name (no spaces)
- Order auto-naming: `DISPLAYNAME-MMDDYY` (caps) with letter suffix for same-day dupes
- Order item auto-naming: `displayname-category-mmddyy` (lowercase)
- Naming Conventions settings card in CompanySettings
- Expense receipt photo: "Take Photo" and "Choose File" buttons in expense dialog
- Testing: iteration_111 passed 100% (13/13 backend, all frontend verified)

### Session: April 13, 2026 (Consolidation Pass — Legacy Jobs Cleanup + Unified Dashboard Finalization)
- Completed the post-audit consolidation pass across routing, navigation, productivity, and source-detail flows.
- Legacy `/jobs` flow cleanup:
  - `/jobs` now redirects through `LegacyJobsRedirect` to the current surfaces:
    - `/jobs` → `/orders`
    - `/jobs?new=true` → `/orders/new`
    - `/jobs?filter=quotes` → `/quotes`
  - `/jobs/:id` now redirects to the dedicated legacy record route:
    - `/productivity/legacy-jobs/:jobId`
  - updated active navigation/actions so current UI no longer sends users into outdated job flows
  - updated customer detail modal links/actions to use `/orders/new` and `/productivity/legacy-jobs/:id`
- Dashboard consolidation:
  - retired the old active `/dashboard` page route and redirected `/dashboard` to `/productivity?view=dashboard`
  - unified dashboard is now the single primary dashboard experience after login and on direct `/dashboard` visits
- Direct source routing completion:
  - `legacy_job` productivity items now open `/productivity/legacy-jobs/{id}`
  - `appointment` productivity items now open `/productivity/appointments/{id}`
  - added backend appointment detail route `GET /api/appointments/{appointment_id}`
  - added dedicated frontend detail pages for legacy jobs and appointments
- Shared productivity dialog coverage completed:
  - appointments now expose editable status + scheduled start controls
  - schedule shifts now expose editable shift start + shift end controls
  - schedule shift updates carry the required `schedule_day_key` through the unified PATCH flow
- Regression verification completed:
  - smoke-tested login + `/dashboard` redirect into unified productivity dashboard
  - frontend testing agent passed consolidation verification
  - backend testing agent passed consolidation verification
  - testing agent iteration_99 passed with 100% backend and frontend success, no action items

### Session: April 13, 2026 (Post-Consolidation Verification Fixes — Signature + Schedule + Drawing)
- Fixed the order signature capture runtime regression:
  - root cause was unstable `onChange` / `onAutosave` callback identities in `DrawingCanvasPad` causing callback-driven state updates to loop when signature capture opened inside the order detail dialog flow
  - stabilized canvas callbacks using refs instead of effect dependencies so the signature modal opens without `Maximum update depth exceeded`
- Fixed unified schedule shift persistence:
  - `schedule_shift` productivity item UIDs use the compound format `schedule_shift:{schedule_id}:{day_key}`
  - backend PATCH parsing now correctly extracts the schedule document id and day key before updating stored shift times
- Verified drawing persistence end-to-end from the order detail screen:
  - created and saved a real order drawing (`QA Persisted Drawing 2309`)
  - confirmed saved thumbnail + preview modal + backend record persistence
- Verified signature persistence end-to-end from the order detail screen:
  - captured and saved a real signature (`QA Signature Final Test`)
  - confirmed preview/summary + backend record persistence
- Focused testing completed:
  - live browser verification for signature modal open/save, schedule shift save/reopen, and drawing save/reopen
  - testing agent iteration_100 passed all scoped checks
  - testing agent also fixed a small unrelated regression in `Payroll.js` by moving `formatTimeOfDay` to module scope for ScheduleTab runtime safety

### Session: April 14, 2026 (Admin Payroll Worksheet Replacement)
- Replaced the old bloated `/payroll` screen with a new desktop-first Admin Payroll Worksheet interface inspired by the uploaded worksheet reference.
- New worksheet layout:
  - narrow left Adjustments panel with inline Date / Notes / Amount rows and Total Adjustments footer
  - wide right payroll worksheet with inline editable Employee Name, Title, Manager Name, Week Of, Hourly Rate, Overtime Rate
  - 7-row weekly spreadsheet table (Date, Day, Start, Lunch Start, Lunch End, End, Regular Hours, Overtime Hours, Total Hours)
  - compact summary block showing Total Time, Regular Hours, Overtime Hours, Regular Pay, Overtime Pay, Gross Pay, Carryover Balance, Total Adjustments, and Final Total For Pay Period
- Preserved current payroll/backend wiring where possible:
  - still uses existing employee, payroll transaction, payroll report, payroll timesheet, and payroll balance endpoints
  - kept CSV export and printable report functionality wired through existing export helpers
  - preserved carryover/final owed backend calculations in footer + summary context
- Backend payroll enhancements added to support the worksheet cleanly:
  - employee schema now supports `title`, `manager_name`, and `overtime_rate`
  - payroll report/timesheet/pay-period style responses now expose overtime rate consistently
  - added `POST /api/payroll/timeclock-shifts` for creating worksheet time rows
  - existing timeclock shift update schema now supports `lunch_start` and `lunch_end`
- Practical worksheet behavior:
  - inline edits save without modals
  - hours and pay recalculate instantly on the page
  - left-side adjustments use signed amounts (positive adds pay, negative deducts)
  - a subtle warning appears when legacy off-grid/manual entries still affect exports or totals
- Verification completed:
  - manual smoke testing for layout, save/reload persistence, and backend payroll report synchronization
  - `auto_frontend_testing_agent` passed all 9 worksheet UI checks
  - `testing_agent` iteration_101 passed with backend 100% (19/19) and frontend 100%

### Session: April 14, 2026 (Payroll Worksheet Follow-up — Legacy Review + Read-only Locking + Sign-off)
- Added a compact worksheet-friendly payroll sign-off strip directly into `/payroll`:
  - reviewed by
  - review date
  - approved by
  - approval date
  - payroll notes
- Added backend sign-off persistence keyed per employee + week:
  - `GET /api/payroll/signoff`
  - `PUT /api/payroll/signoff`
- Strengthened visible read-only locking across the worksheet UI:
  - meta fields, time grid inputs, adjustment rows, and sign-off fields now show disabled visual state when payroll edit permission is absent
  - export/print remain available; worksheet save remains disabled
- Added compact legacy/manual entry review inside the worksheet:
  - clean-state message when the selected employee/week maps cleanly to worksheet rows
  - warning summary when off-grid manual/timer entries or extra same-day shifts still affect exports/totals
- Current real-data review results:
  - found legacy manual payroll hours on 2026-04-03, 2026-04-08, and 2026-04-09 for the production tenant test employee
  - week `2026-04-06` shows 2 off-grid manual entries totaling 13.75 hours
  - no extra same-day timeclock shift collisions were found in the current tenant data sample
- Verification completed:
  - live browser save/reload confirmed sign-off persistence works
  - live browser check confirmed clean-state review for week `2026-04-13`
  - live browser check confirmed migration-warning review for week `2026-04-06`
  - `auto_frontend_testing_agent` passed sign-off, legacy review, and no-clutter checks
  - testing subagent confirmed backend sign-off endpoints and legacy review logic are implemented correctly
  - remaining coverage note: there is currently no payroll-view-without-edit credential in the tenant, so the read-only visual lock path was implemented and code-reviewed but not exercised under a dedicated real user role in this pass

### Session: April 14, 2026 (Legacy Manual Payroll Entry Handling Path)
- Added a compact inline `Legacy Manual Entries` section inside the payroll worksheet when a selected week contains off-grid/manual payroll hours.
- Each legacy entry now shows:
  - date
  - source/type
  - hours
  - notes/reason
  - explicit current effect on payroll totals/export
  - inline handling mode
  - selected worksheet day target
  - admin note
  - reviewed/handled status
- Added backend handling persistence for legacy entries:
  - `GET /api/payroll/legacy-manual-entries`
  - `PUT /api/payroll/legacy-manual-entries/{entry_id}/resolution`
- Supported handling modes (compact, inline, no modals):
  - keep as manual legacy entry
  - convert to worksheet manual row
  - merge into selected day
  - document admin note for why it remains off-grid
  - exclude-from-totals intentionally remains unavailable during migration so payroll math/export never changes silently
- Preserved payroll math during migration:
  - verified payroll report payloads stay unchanged before/after handling-resolution saves
  - verified timesheet payloads stay unchanged before/after handling-resolution saves
  - current exports remain unchanged because export inputs still come from the same backend report/timesheet totals
- Known legacy entries handled in production-tenant test data:
  - `2026-04-03` · 8.00h · production · kept as manual legacy entry with note preserving original context
  - `2026-04-08` · 7.50h · production · converted to worksheet manual row with admin note
  - `2026-04-09` · 6.25h · design · merged into selected worksheet day with admin note
- Representation status:
  - all currently known legacy manual entries can now be represented clearly in the worksheet through the dedicated Legacy Manual Entries section/fallback handling path
  - they still remain off-grid relative to clock-in/lunch/end rows, but they are no longer hidden or ambiguous
- Verification completed:
  - manual UI save/reload check confirmed legacy handling changes persist from the worksheet
  - API comparison confirmed totals and exports stay unchanged before/after resolution updates
  - testing agent iteration_103 passed with backend 100% (14/14) and frontend 100%

### Session: April 14, 2026 (Payroll Worksheet Bug Fix + Flexible Date Ranges)
- Fixed reported payroll worksheet issues from user feedback:
  - save flow confirmed working end-to-end again
  - print flow rewritten to use an iframe print path instead of popup/new-window dependency
  - final total math now includes legacy manual pay in the worksheet summary so UI totals match backend payroll report values
- Expanded the worksheet from fixed weekly mode to flexible custom date ranges:
  - start date + end date are now first-class controls on `/payroll`
  - Weekly / Biweekly / Current Cycle are now convenience presets only
  - custom range remains the default interaction model
  - biweekly preset now expands the worksheet to 14 rows automatically
- Added company payroll preferences in main company settings:
  - default cycle (`weekly` / `biweekly`)
  - pay-week start day (`monday` ... `sunday`)
- Updated payroll math/settings behavior:
  - frontend worksheet summary groups overtime by configured pay-week start day
  - backend payroll report/timesheet/pay-period calculations now respect tenant `pay_week_start_day`
  - sign-off and legacy-manual-entry handling now support flexible date ranges (`period_end` / `start_date` / `end_date` support)
- Verified results:
  - live browser verification confirmed save works, print works, custom range works, biweekly 14-row worksheet works, and company payroll preferences persist
  - manual UI check confirmed final worksheet total now matches backend (`$1,103.50` in current-cycle test)
  - testing agent iteration_104 passed all requested features; only low-priority note was API naming inconsistency on `/api/payroll/pay-period` response fields

### Session: April 14, 2026 (Markup Notes Applied — Save Prompt + Expandable Adjustments)
- Reviewed uploaded `MARKUP.pdf` notes and implemented the relevant compact worksheet updates without expanding payroll into a new subsystem.
- Added explicit unsaved-change handling:
  - dirty-state detection for worksheet edits
  - visible `Unsaved changes` badge in the worksheet header strip
  - save-before-export prompt
  - save-before-print prompt
  - browser/tab close warning via `beforeunload`
- Added expandable adjustments handling:
  - new `Add Adjustment Row` button in the left adjustments panel
  - users are no longer limited to the initial fixed row count
- Preserved markup-intended layout behavior:
  - save / export / print buttons remain at the top
  - review/sign-off remains at the end of the worksheet
  - no extra modals or second workflow introduced
- Fixed the remaining total-math mismatch:
  - worksheet summary now includes legacy manual pay/hours in displayed totals so the on-screen final total matches backend payroll report math
- Verification completed:
  - manual live browser checks passed for save prompt, print prompt, add-row behavior, and final-total math
  - testing agent iteration_105 passed with backend 100% (17/17) and frontend 100%

### Session: April 11, 2026 (Signguypa Stripe Validation + Webstore Checkout Gating)
- Validated the tenant the user called out specifically:
  - `signguypa@gmail.com / Billnel323`
  - current Stripe Connect status in preview: `connected=false`, `stripe_mode=live`
- Implemented requested Webstore behavior:
  - browsing remains active
  - add-to-cart remains active
  - cart drawer remains active
  - checkout dialog can still open
  - final place-order button is disabled unless the tenant is connected/onboarded through Stripe Connect on the platform
- Public storefront API now exposes safe checkout gating fields:
  - `checkout_enabled`
  - `checkout_status`
  - `checkout_message`
- Storefront UI now shows a clear checkout-inactive banner and a disabled final checkout action with explanation instead of failing silently
- Maintained public-data safety:
  - public store/product APIs still avoid exposing tenant-sensitive payout/profit fields
- Preview webstore QA seed created for validation:
  - store_id: `fc0bad7e-9040-477e-93b9-a3f0b1a2df90`
  - product_id: `b3c51047-4bc9-4d6e-b3cb-9023bb6a2ee6`
- Testing:
  - testing agent iteration_98 passed backend 11/11 and frontend 100%

### Session: April 11, 2026 (Order Command Bar + Payroll Export/Carryover Overhaul)
- Added a reusable `OrderCommandBar` component and wired it into:
  - New Order
  - Add Ticket to Order
- Command bar now keeps key actions visible while building orders:
  - Pricing Analysis
  - Pricing Calculator
  - Sketch (New Order)
  - Add Ticket
  - Save Order
- Payroll/timesheet backend overhaul:
  - transactions now affect payroll balances correctly instead of being ignored in export/summary math
  - carryover rule implemented using prior unpaid payroll balance before the selected start date
  - `final_owed = carryover_balance + gross_pay + adjustments_total`
  - adjustments now treat:
    - earnings = positive
    - advances = negative
    - payments = negative
  - added daily payroll breakdown with:
    - day name
    - date
    - worked time as hours/minutes
    - break time label
    - daily pay
    - daily adjustments
    - daily final
  - added hours/minutes labels across payroll report, timesheet, and pay-period summary responses
  - entry details now include punch/break labels where available
- Payroll export/print overhaul:
  - CSV/printable exports now include carryover, daily breakdowns, transaction lines, totals by type, and final owed values
  - export formats now use hours/minutes labels instead of only decimal-hour values
- Payroll UI updates:
  - Timesheet summary strip now surfaces carryover and final owed
- Preview verification data created for testing:
  - employee `Preview Payroll QA`
  - seeded prior/current manual hours + transactions to verify carryover math end-to-end in preview
- Testing:
  - testing agent iteration_97 passed backend 17/17 and frontend 100%

### Session: April 11, 2026 (Batch C — Stripe Mode Clarity + Settings Cleanup)
- Investigated the tenant Stripe Connect confusion and added explicit live/test mode visibility
- Stripe Connect backend now returns:
  - `stripe_mode`
  - `account_mode`
  - `mode_mismatch`
- Stripe Connect account creation now detects an old connected account whose mode does not match the current platform key mode and will create the correct onboarding flow instead of blindly reusing the mismatched account
- Payment Settings UI now explains what Stripe test mode means in plain language and surfaces live/test mode clearly
- Added reconnect guidance for mode mismatches so a tenant can reconnect into the correct environment
- Settings cleanup:
  - `/workflow-templates` now redirects into `/settings/production`
  - duplicate Workflow Templates settings entry removed from desktop/mobile settings navigation
  - duplicate Backup card removed from Company Settings so Backup only lives in its own settings tab
- Testing:
  - testing agent iteration_96 passed backend 8/8 and frontend 100%

### Session: April 11, 2026 (Batch B — Drawing + Order Entry UX)
- Fixed drawing persistence/save behavior:
  - drawing canvas no longer rebuilds and wipes strokes when pen settings change
  - backend blank-drawing threshold relaxed so normal small sketches are no longer falsely rejected
- New Order UX improvements:
  - added sticky live estimate sidebar
  - added pricing analysis + pricing calculator quick links near the estimate
  - added bottom actions so staff can add another ticket or save without scrolling back to the top
- Add Ticket to Order UX improvements:
  - added sticky live estimate summary
  - added `Add to Order`, `Add Another Ticket`, and `Save Order` actions in the lower summary area
- Compatibility follow-up:
  - pricing calculator now accepts `banners` as a category alias and common banner material labels like `13oz_vinyl`
  - job ticket specs now accept numeric width/height values directly
- Testing:
  - testing agent iteration_95 passed backend 10/10 and frontend 100%

### Session: April 11, 2026 (Pricing + Billing Visibility Pass)
- Completed the first approved `A` batch from the user's next priority list: pricing + billing
- Pricing fixes:
  - rigid-sign thickness now changes pricing correctly (for example 4mm vs 10mm)
  - rush order now increases pricing across pricing categories
  - job-ticket / live preview payloads now forward more real pricing-affecting fields into the pricing engine
  - added compatibility normalization so generic substrate + thickness selections map correctly into backend pricing enums
- Billing / quote visibility fixes:
  - order-generated quotes now save into the standard `quotes` collection
  - order-generated invoices now save into the standard `invoices` collection
  - `/api/orders/{order_id}/financials` now merges standard quote/invoice docs with legacy `order_quotes` work-order records
  - legacy order-generated quotes/invoices stored in `order_quotes` are now also surfaced through the normal `/api/quotes` and `/api/invoices` flows
- Frontend billing visibility:
  - restored `/quotes` as a real page instead of redirecting away
  - rewired quote navigation so users can actually reach the dedicated Quotes screen again
  - stabilized the Quotes page fetch cycle to avoid repeated re-fetching loops
- Testing:
  - self-tested thickness/rush pricing behavior and order-generated quote/invoice visibility
  - testing agent iteration_94 passed backend 12/12 and frontend 100%
  - follow-up frontend verification passed for `/quotes` and `/invoices`

### Session: April 11, 2026 (P0 Workflow / Order / Nav Stabilization)
- Applied the first approved P0 batch from the user's latest shop-ops notes
- Production workflow defaults:
  - changed default workflow mode to `simple`
  - updated default simple stages to only:
    - `Design`
    - `Production`
    - `Waiting on Customer Input`
    - `On Hold`
    - `Ready`
  - added auto-migration behavior so legacy default detailed workflow settings fall back to simple unless a customer explicitly re-saves workflow preferences
- Productivity main calendar cleanup:
  - default calendar filters now load with jobs only
  - removed production sub-step / schedule sub-step filters from the main productivity filter bar so detailed shop-floor steps stay inside production workflows instead of the main shop calendar
- Reports tab fix:
  - changed the ribbon Reports nav to point to Financials
  - added `/reports -> /financials` redirect so the tab no longer feels like a logout or broken route
- Order file upload / review fixes:
  - fixed the order detail files-tab render crash after uploads
  - added visible image thumbnails for uploaded order files in order review
- Tenant branding isolation hardening:
  - AppContext now clears tenant state on logout and refreshes tenant branding on login/account change
  - shared tenant logo state is now used consistently in top/mobile navigation so stale branding is less likely between account switches
- Ticket scheduling UX:
  - improved the ticket schedule date field with explicit picker support and a calendar button
- Testing:
  - self-tested live preview for order files and reports routing
  - testing agent iteration_93 passed backend 13/13 and frontend 100%

### Session: April 9, 2026 (Production Login 500 Root Cause)
- Reproduced the production-only login failure on `https://signguy-ai.com/login`
- Browser console root cause:
  - production frontend was trying to call an old backend URL
  - `https://quote-to-invoice-3-r-1773003818.emergent.host/api/auth/login`
  - request failed with CORS, which surfaced as a generic frontend “Network error” on login
- Added `frontend/.env.production` with:
  - `REACT_APP_BACKEND_URL=https://signguy-ai.com`
- Verified the frontend still builds successfully for production after adding the production env file
- Preview auth remains healthy; both known shop accounts still log in successfully there

### Session: April 9, 2026 (Auth Verification Note)
- Verified browser login works for both known shop accounts:
  - `signguypa@gmail.com` / `Billnel323`
  - `thesigntistslab@gmail.com` / `password123`
- Updated `/app/memory/test_credentials.md` to add the missing legacy admin password so future auth debugging/tests use the correct saved credential

### Session: April 9, 2026 (Cloud Storage Migration for Uploads)
- Confirmed storage direction with user: Emergent Object Storage, migrate existing files where applicable, preserve current access behavior
- Migrated upload persistence away from local filesystem / inline-only storage for these active flows:
  - Historical invoice imports (`/api/pricing-setup/imports`)
  - Document uploads (`/api/documents`)
  - Order attachments (`/api/orders/{order_id}/upload`)
- Added pricing import migration endpoint: `POST /api/pricing-setup/imports/migrate-storage`
- Kept backward compatibility intact:
  - document download still returns `file_data` for the current frontend
  - order attachment content endpoint still returns raw bytes
  - pricing import preview / analysis still works after moving files to object storage
- Object storage path conventions now in active use:
  - `signguy-ai/pricing-imports/{tenant_id}/{import_id}/{file_id}{extension}`
  - `signguy-ai/documents/{tenant_id}/{document_id}/{uuid}{extension}`
  - `signguy-ai/orders/{tenant_id}/{order_id}/files/{file_id}{extension}`
- Testing:
  - self-tested document upload/download, pricing import upload/migration, and order attachment upload/content
  - testing agent iteration_92 passed backend 19/19
  - frontend sanity check passed for Pricing Setup and Documents pages
  - final backend spot-check passed

### Session: April 8, 2026 (Payroll Cleanup + Payroll Export Reports)
- Completed a focused cleanup pass on the existing Payroll workspace without changing the overall navigation structure
- Added a new export workflow inside `src/pages/Payroll.js`:
  - Weekly / biweekly / custom report range selector
  - One employee or all employees export scope
  - Refresh control
  - CSV export
  - Printable payroll report view
- Added frontend export helper module: `/app/frontend/src/lib/payrollExport.js`
- Enhanced backend payroll reporting in `/app/backend/routes/employees.py`:
  - `GET /api/payroll/report` now supports optional `employee_id`
  - supports `period_type=weekly|biweekly|custom`
  - keeps custom `start_date` / `end_date` support
  - returns richer summary totals for export/report use
- Applied a light readability pass to `src/pages/TimeClock.js` so the header, selector, summary cards, and employee directory are clearer and more consistent with Payroll
- Testing:
  - smoke-tested live preview login + payroll load
  - testing agent iteration_91 passed backend 16/16 and frontend 100%
  - follow-up frontend specialist check passed
  - follow-up backend deep verification passed

### Session: April 5, 2026 (Team / Workforce Ribbon Spec Saved)
- Saved the detailed Team / Workforce ribbon rebuild specification to memory for later implementation
- Added dedicated memory file: `/app/memory/team_workforce_ribbon_spec.md`
- This spec is saved only and is **not started yet**

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

### Session: April 20, 2026
- **Cut Vinyl Pricing Phase:** Implemented Cut Vinyl defaults, materials, AI prefill, and full calculation flow (materials, labor, overhead, suggested price, manual quote, profit/margin)
- **Total Production Cost Label:** Updated calculator output label to match required terminology
- **Rigid Signs Pricing Phase:** Implemented Rigid Signs defaults + calculator UI + backend calculation (substrates, thickness, finish, sidedness, shape complexity, hardware/drill)
- **New Order Form Schema Sync:** Job ticket schemas now pull options from Pricing Foundation (materials/laminates/hardware) with fallback only when missing; added base materials for apparel/decoration/vehicle types and a services schema definition
- **Pricing Engine Fix:** Added calculate_apparel placeholder to prevent pricing dispatcher failures
- **Testing:** Backend schema + rigid sign calc verified via API; frontend Rigid Signs + New Order Form dropdowns verified via Playwright/auto UI tests

### Session: April 19, 2026
- **Digital Print Pricing Phase:** Implemented Digital Print-specific defaults, media/laminate libraries, AI prefill logic, and full calculation flow (material, labor, overhead, suggested price, manual quote, profit/margin)
- **Pricing Foundation Phase:** Extended Pricing Foundation as the single source of truth (general defaults, materials, hardware/accessories, labor rates, category rule containers, AI rules, benchmarks, global calculation rules, review panel)
- **Compatibility Surfaces:** Pricing Settings + Materials Admin converted to compatibility pages linking to Pricing Foundation; Pricing Setup clarified as historical import/analysis only
- **Backend Pricing Defaults Expanded:** Added hardware/accessories, labor rates, AI/benchmark/global rule structures, expanded category containers (Digital Print, Cut Vinyl, Rigid Signs, Banners, Vehicle Wraps, Apparel, Services, Custom), and benchmark ranges
- **Pricing Calculator:** Displays Pricing Foundation default summary
- **Routing:** Added explicit routes for /pricing-settings and /materials-admin
- **Testing:** Manual API save/load via curl + UI verification via Playwright screenshots

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
- Remaining pricing-engine gaps
  - audit additional pricing-affecting options beyond the newly-fixed thickness / rush / rigid-sign modifiers to ensure all intended selections affect live estimates
- Stripe Connect follow-up
  - validate reconnect flow against a real tenant account that previously saw Stripe test-data messaging and confirm the mismatch path behaves correctly end-to-end
- Deployment readiness blockers
  - app still needs the deferred supervisor/deployment readiness cleanup from the previous fork

### P1 - High Priority
- Camera / intake workflow
  - quick photo capture from camera during order creation
  - markup-ready intake photo flow for customer vehicles / site conditions
- Customer communication
  - easier send-artwork-to-customer-portal flow
- Remaining high-complexity code review cleanup
  - `src/components/FloatingAssistant.js`
  - `src/components/PricingCalculator.js`
  - `backend/routes/ai.py`

### P2 - Medium Priority
- Business Assistant Phase 1+
  - action-oriented response layer
  - quick action buttons
  - smart navigation links
  - visual response blocks
- Business Assistant Phases 2-5
  - context awareness
  - cross-system commands
  - personalization
  - bulk workflows

### P3 - Future/Backlog
- Team / Workforce Ribbon rebuild from `/app/memory/team_workforce_ribbon_spec.md` (**paused by user — do not start until explicitly requested**)
- Broader mobile responsiveness pass
- Inventory / materials system return pass
- QuickBooks integration
- SMS notifications (Twilio)

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
- Current active test credentials are maintained in `/app/memory/test_credentials.md`
