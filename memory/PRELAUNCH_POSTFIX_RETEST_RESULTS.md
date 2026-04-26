# Prelaunch Post-Fix Retest Results — Running Log

This is the **single running retest file** for checks executed **after code fixes**.

Last updated: 2026-04-26

---

## Tier 2 Retests (2026-04-26)

### 2.1F Tax-Exempt Toggle fix retested
- ✅ **2.1F** Tax-exempt flag now correctly reflected in invoice tax calculation
  - Backend evidence: `default_tax_rate=6.0` persists on tenant (PUT `/api/tenant`)
  - Non-exempt customer ($100 order): `tax_amount=6.0`, `grand_total=106.0`, `tax_rate=6.0`, `is_tax_exempt=False`
  - Tax-exempt customer ($100 order): `tax_amount=0.0`, `grand_total=100.0`, `tax_rate=0.0`, `is_tax_exempt=True`
  - Frontend evidence: `data-testid="company-tax-rate-input"` present on `/settings`; value persists after save (tested 6.0 → 8.5 → confirmed via reload)
  - Test report: `/app/test_reports/iteration_127.json`

### 2.2E Assets Panel Upload/Thumbnail fix retested
- ✅ **2.2E** Assets panel now supports drag-and-drop and shows real thumbnails
  - Frontend evidence: `data-testid="asset-drop-zone"` found with "drag & drop here" text
  - Upload via button: file input triggers, file appears as `data-testid="asset-row-{id}"`
  - Thumbnail: `data-testid="asset-thumbnail-{id}"` renders actual image (red 1×1 PNG blob — not static icon)
  - Test report: `/app/test_reports/iteration_127.json`

---

## Tier 1 Retests

### 1.1 / 1.3 / 1.6 fixes retested
- ✅ **1.1B** Backup size threshold now passes (`55740 bytes`)
- ✅ **1.1C** Required legacy collection names now present (`missing=[]`)
- ✅ **1.3A** Subscription response now includes date field (`trial_end` populated)
- ✅ **1.6D** Empty import now returns validation error (`status=400`)
- ✅ **1.6K** Phone format search now returns results
- ✅ **1.6L** Phone format search now returns results
- ✅ **1.6M** Phone format search now returns results
- ✅ **1.6N** Phone format search now returns results
- ✅ **1.6O** Phone format search now returns results
- ✅ **1.6P** Invalid email row now skipped with explicit row error

Independent verification:
- ✅ Backend testing agent pass for targeted Section 1 fixes (`/app/test_reports/iteration_119.json`)

---

## Tier 2 Retests

### 2.3a Digital Print fixes retested
- ✅ **2.3aB** Lamination now increases sell price
  - API evidence: `no_lam sell=1048.5`, `yes_lam sell=1296.28`, `laminate_sell_addon=247.78`
  - UI evidence: `no_lam=$1000.00`, `lam_yes=$1247.78`

- ✅ **2.3aE** Design Complexity now appears when `Artwork Ready = No`
  - UI evidence: `design_visible_with_artwork_ready_false=true`

### 2.3b Cut Vinyl fix retested
- ✅ **2.3bF** Duplicate now resets quantity to 1 and preserves category
  - API evidence: source qty `5` -> dup qty `1`, dup category `cut_vinyl`, dup name `Copy of Vinyl Source`

### 2.3e / 2.3f UX schema fixes retested
- ✅ **2.3eD** Vehicle Make/Model autocomplete now supported in dynamic schema UI
  - UI evidence: datalist options rendered for make/model and model suggestions respond to selected make
- ✅ **2.3fA** Apparel product type now switches Brand/Style option list dynamically
  - UI evidence: product type toggle changes brand option set (e.g., short-sleeve vs hoodie lists)

### Hats field-visibility + sticky-zero UX fix retested
- ✅ **Hat irrelevant fields hidden** when Product Type is hat/cap
  - UI evidence: `size_count=0`, garment placement hidden, hat placement visible (`hat_place=1`)
- ✅ **Zero-sticky input behavior fixed** for size numeric fields
  - UI evidence: clearing `size_s` leaves blank value (`''`) instead of forcing `0`
  - Console artifact: `/root/.emergent/automation_output/20260423_102924/console_20260423_102924.log`

### Payroll/timeclock + payroll controls retested (Iteration 123)
- ✅ Timeclock shift edit now accepts `lunch_start/lunch_end = null` and updates `break_minutes` correctly.
- ✅ Worksheet totals now deduct break time even when lunch fields are blank.
- ✅ Same-day multiple shifts are merged into worksheet totals (split lunch clock-out/in no longer disappears).
- ✅ New **Paid in Full** flow works per selected employee + selected pay period and is idempotent for same period.
- ✅ New payroll settings toggle (`show_payroll_adjustments`) persists and controls adjustments panel visibility.
- ✅ Admin editability remains intact after marking Paid in Full.
  - Evidence: `/app/test_reports/iteration_123.json`

### Tier 3 + Tier 4 — Production, Analytics, Employees, Portals (2026-04-26)
**52/55 passed. 3 missing features implemented and re-tested.**

**Tier 3:**
- ✅ **3.1** Production board API: board endpoint, stages config, category filter all return 200
- ✅ **3.2** Task CRUD: add, check-off (timestamp), assign to employee, delete
- ✅ **3.3** Timeline settings + templates: both endpoints return without error
- ✅ **3.4** Workflow templates: full CRUD + seed-defaults (all pass)
- ✅ **3.5** Approvals: send proof, list, stats, approve (status transition + timestamps), request changes, resend (after adding `status` + `admin_notes` to `ProofUpdate` and timestamp logic to PUT handler)
- ✅ **3.6** Appointments: full CRUD verified (after full rewrite of `routes/appointments.py` — was skeleton-only)
- ✅ **3.8** Productivity feed: returns 200 with combined feed
- ✅ **3.9** Profit analytics: dashboard (margin data), filter, CSV export
- ✅ **3.10** Financials: revenue/expense/profit, expense create, invoice aging buckets (added `GET /api/financials/invoice-aging` with 0-30/31-60/61-90/90+ bucketing)

**Tier 4:**
- ✅ **4.1** Employees: create, list, edit rate, deactivate, reset PIN
- ✅ **4.2** Payroll: worksheet with hours + gross, carryover override set/clear, manual time entry
- ✅ **4.3** TimeClock: clock in → start lunch → end lunch → clock out (full shift lifecycle)
- ✅ **4.4** Customer portal: auth, dashboard, orders, quotes, invoices
- ✅ **4.5** Employee portal: PIN login, clock status, pay summary, profile

**3 gaps filled:**
- `routes/appointments.py`: Full rewrite — was a 72-line skeleton with no CRUD. Now has create/list/get/update/delete with customer/employee name resolution, all field aliases, and date-range filters
- `routes/approvals.py ProofUpdate`: Added `status` + `admin_notes` fields; PUT handler now sets `approved_at`/`rejected_at` timestamps on status transitions
- `routes/profit_analytics.py`: Added `GET /api/financials/invoice-aging` endpoint with 5 aging buckets
- Test report: `/app/test_reports/iteration_131.json`

---
**37/37 tests passed (100%). 4 bugs found and immediately fixed.**

**2.6 Artwork, Files & Drawings (14/14 PASS):**
- ✅ PNG, JPG, PDF, SVG, AI/EPS all upload, store, and retrieve correctly
- ✅ File content endpoint returns correct bytes + Content-Type
- ✅ File list populated; promote-to-shared sets is_shared=true; file appears in shared pool
- ✅ File delete removes record; content endpoint returns 404 after delete
- ✅ Drawing create/retrieve/file download/delete all work; base64 PNG data URL preserved

**2.7 Webstores (5/5 PASS, 3 improvements applied):**
- ✅ Products CRUD (add/edit/delete) fully functional
- ✅ Apparel options endpoint returns non-empty brand/color list
- ✅ Storefront GET returns seo_title, seo_description, og_image fields (after model fix)
- ✅ Product fields round-trip: size_options, color_options, is_featured, in_stock all persist (after constructor fix)
- ✅ Webstore name uniqueness enforced → second POST with same name → 409 (after fix)

**2.8 Products (3/3 PASS):** CRUD verified (add, edit, delete with all new fields)

**2.9 Questionnaires (7/7 PASS):**
- ✅ Create with all field types, public access (no auth), submit, dashboard responses, required enforcement, email validation (after fix)

**2.10 Signatures (7/7 PASS):**
- ✅ Requirement create, public token loads, sign, token one-time-use enforcement (409), invalid token → 404, expired token → appropriate error

**4 bugs fixed:**
- `webstores.py Product model`: Added `size_options`, `color_options`, `is_featured`, `in_stock` to Product/ProductCreate/ProductUpdate models AND constructor call
- `webstores.py create_webstore`: Added 409 uniqueness check on `{tenant_id, name}`
- `webstores.py Webstore model`: Added `seo_title`, `seo_description`, `og_image` fields to model + Create + Update + PUBLIC_FIELDS
- `questionnaires.py`: Added per-field email/phone format validation on submit
- Test report: `/app/test_reports/iteration_130.json`

---
**31/32 tests passed; 2 model bugs found and immediately fixed**

**2.4 Order Item Clone:**
- ✅ **2.4-A** Duplicate: `name='Copy of Source Sign'`, `category=rigid_signs`, `qty=1`, `entry_mode=quick`
- ✅ **2.4-B** Variation: `name='Variant — Source Sign'`, `entry_mode=detailed`, `qty=1`
- ✅ **2.4-C** Copy-to-category (rigid_signs→banners): `name='Converted — Source Sign'`, `item_category=banners`, `converted_from_category=rigid_signs`, universal fields preserved
- ✅ **2.4-D** Category-specific field dropping: `hardware_included`, `protective_finish`, `double_sided_art` absent after copy; `width/height/unit_of_measure` preserved
- ✅ **2.4-E** Artwork carry-over OFF: `linked_order_file_ids=[]`, `item_artwork_file_ids=[]`
- ✅ **2.4-F** Production notes carry-over OFF: `production_notes=''` ✓; install_notes requires separate `install_location_notes=false` key (documented)
- ✅ **2.4-G** Due date carry-over OFF: `due_date=None`
- ✅ Legacy `/duplicate` endpoint also functional

**2.5 Quote → Invoice:**
- ✅ **2.5-A** Quote create: `total=320.0` (2×85+1×150), `status=draft`
- ✅ **2.5-B** List/retrieve round-trips correctly
- ⚠️ **2.5-C** Quote PDF: `GET /api/quotes/{id}/pdf` → 404 — **NOT IMPLEMENTED**
- ✅ **2.5-D** Quote send: `status=sent`, `sent_at` now returned (after model fix)
- ✅ **2.5-E** Convert-to-job: `job_id` set, `quote.status=approved`, double-convert → 400
- ✅ **2.5-F** Invoice from order: `tax_amount=21.0`, `grand_total=371.0`, `tax_rate=6.0` (re-confirmed)
- ✅ **2.5-G** Invoice structure: all required fields present; `tax_rate`/`is_tax_exempt` now returned (after model fix)
- ✅ **2.5-H** Invoice send: `status=sent`
- ✅ **2.5-I** Partial payment: `amount_paid=185.5`, balance tracked
- ✅ **2.5-J** Mark paid: `status=paid`

**2 bugs fixed immediately:**
- `models/jobs.py Quote`: Added `sent_at`, `approved_at` fields (were written to DB but stripped by response model)
- `models/jobs.py Invoice`: Added `grand_total`, `tax_rate`, `is_tax_exempt` fields (were written to DB but stripped by response model)
- Test report: `/app/test_reports/iteration_129.json`

---
**23/25 tests passed (2 bugs found and immediately fixed)**

**2.3g Services pricing:**
- ✅ **2.3g-1** Hourly installation with travel + equipment + rush → sell > $200, profit/margin > 0
- ✅ **2.3g-2** Flat-fee graphic design → `sell=$250.00` (after fixing ServiceType enum: `GRAPHIC_DESIGN='graphic_design'` added to `enums.py`)
- ✅ **2.3g-3** Consultation minimum enforcement → `sell >= $50` (0.25h floored to minimum)
- ✅ **2.3g-4** Delivery per mile → `sell >= $31.25` for 25 miles
- ✅ **2.3g-5** Delivery per trip → `sell >= $45` for 2 trips
- ✅ **2.3g-6** Subcontracted permit → `sell ≈ $270` ($150 flat + $100 sub × 1.20)
- ✅ **2.3g-7** Equipment rental (boom_lift, 2 days) → `equipment_sell=$950`
- ✅ **2.3g-8** File cleanup flat fee → `sell >= $35`
- ✅ **2.3g-9** Site survey with travel → `sell > $75` + `travel_sell > 0`
- ✅ **2.3g-10** Wrap install with difficulty multiplier → `difficult/medium ≈ 1.2 ratio`
- ✅ **2.3g-11** Rush from Pricing Foundation (`17.5%`) → `rush_source=foundation`, `rush_applied=17.5`
- ✅ **2.3g-12** Rush fallback (null foundation) → `rush_source=services_category`, `pct≈25.0`
- ✅ **2.3g-13** Explicit 0% rush → `rush_applied=0` (not overridden)
- ✅ **2.3g-14** Breakdown spec fields → `total_labor_cost`, `total_travel_cost`, `total_equipment_cost`, `total_subcontract_cost`, `rush_percent_source` all present

**2.3h Promotional Items pricing:**
- ✅ **2.3h-1** Magnets qty=50 → `sell=$1934.49 > 0`
- ✅ **2.3h-2** Yard signs qty=100 → `sell > 0`
- ✅ **2.3h-3** Stickers qty=250 → `sell > 0`
- ✅ **2.3h-4** Quantity tier discounts → per-unit price decreases at qty 50→100→250→500
- ✅ **2.3h-5** Double-sided upcharge → `double_sided=different: $2503.46 > none: $1934.49` (after fixing `calculate_promotional()` to apply 1.5× multiplier)
- ✅ **2.3h-6** Rush upcharge → promotional rush=true > rush=false

**2.3i Custom/Other:**
- ✅ **2.3i-1** Manual price override → `sell=$150.00` exactly (no override)
- ✅ **2.3i-2** Description persists → `'Custom laser-cut acrylic award'` saved (after adding `description=data.description` to `JobTicket()` constructor in `job_tickets.py`)
- ✅ **2.3i-3** No progressive disclosure fields → `custom` and `custom_other` schemas return 0 `visible_when` fields

**Bugs fixed in this session:**
- `models/enums.py`: Added `GRAPHIC_DESIGN = 'graphic_design'` to `ServiceType` enum
- `routes/job_tickets.py`: Added `description`, `entry_mode`, `manual_quote_override`, `pricing_snapshot`, `linked_order_file_ids`, `item_artwork_file_ids`, `artwork_use_mode` to `JobTicket()` constructor
- `server.py` (`calculate_promotional`): Added double-sided upcharge (1.5× for `different`, 1.2× for `same`)
- Test report: `/app/test_reports/iteration_128.json`

---
- `/app/memory/SECTION1_FIX_RETEST_RESULTS.json`
- `/app/test_reports/iteration_119.json`
- `/app/test_reports/iteration_123.json`
- `/root/.emergent/automation_output/20260423_080029/console_20260423_080029.log`

---

## Tier 1+3+4 Final Mop-Up Retests (2026-04-26)

### Iteration 132 follow-up — 4 missing endpoints + 1 security bug

- ✅ **T1-ISO-E** Payroll READ security: Staff role now returns `403 "You do not have permission to view payroll data"` on `GET /api/payroll/{report,balance,transactions,hours,signoff,timesheet,pay-period,timeclock-shifts,legacy-manual-entries,schedule}`
  - Fix: Added `_require_payroll_view_access()` helper to `routes/employees.py` and wired into all GET payroll routes
  - Verified: Admin (owner) still gets `200`, Staff returns `403` for `/report`, `/transactions`, `/hours`
- ✅ **T1-CSV** Customer CSV export: `GET /api/customers/export` returns `200 text/csv` with header `name,email,phone,company,status,notes,created_at`
- ✅ **T3-WF-A** Workflow template apply: `POST /api/workflow-templates/{id}/apply` creates production tasks per stage; supports `replace_existing=true`. Bonus: `POST /{id}/duplicate`.
- ✅ **T4-PORTAL-C** Customer portal appointments: `GET /api/portal/appointments` returns appointment list filtered by current customer
- ✅ **T4-PAYROLL-A** Payroll CSV export: `GET /api/payroll/report?format=csv` streams CSV with employee-level columns
- ✅ **T4-EMP-PORTAL-A** `/api/employee-portal/dashboard` alias added (returns same payload as `/work-summary`)

**Test verification:** 29/29 pytest tests passed (`/app/test_reports/iteration_133.json`)

---

## Tier 5 Backend Audit + Customer Request Appointment Feature (2026-04-26)

### Customer Request Appointment Flow (NEW FEATURE)

- ✅ **POST /api/portal/appointments/request** — customer creates appointment with `status="requested"`, `requested_by_customer=true`; default duration 60min; customer notification row created
- ✅ **GET /api/portal/appointments?upcoming_only=true** — `requested` status entries now included in upcoming filter
- ✅ **GET /api/appointments?status=requested** (admin) — admin sees all customer requests scoped to tenant
- ✅ **PUT /api/appointments/{id}/confirm** — flips status to `confirmed`; supports overriding `scheduled_start`, `scheduled_end`, `employee_id`, `notes`
- ✅ **PUT /api/appointments/{id}/reject** — flips status to `cancelled`, appends reason to notes
- ✅ **Frontend `/customer-portal/appointments`** — Request Appointment dialog with type, date, time, location, description fields. "Pending Confirmation" badge for `status="requested"`. Toast on submit. Verified via testing agent (iteration_134).
- Test report: `/app/test_reports/iteration_134.json`

### Tier 5 Backend Sweep (28/29 PASS)

**5.1 User Management:**
- ✅ POST `/api/admin/users/create` (field: `full_name`)
- ✅ PUT `/api/admin/users/{id}/role`
- ✅ PUT `/api/admin/users/{id}/status` (RBAC permission fixed: `USERS_MANAGE` instead of broken `USERS_EDIT`)
- ✅ POST `/api/admin/users/{id}/reset-password` (RBAC permission fixed)
- ✅ **NEW** DELETE `/api/admin/users/{id}` — implemented 2026-04-26 with last-owner guard
  - Cannot delete self → 400
  - Staff cannot delete → 403
  - Last-owner-of-tenant guard → 400 "Cannot remove the last owner..."
  - Idempotent on missing user → 404
- ⛔ Email-link invite/accept flow not implemented (user-only Section 16.1)

**5.4 Digest:** ✅ GET/PUT `/api/digest/settings`, GET `/api/digest/preview` — all PASS

**5.7 Promo Codes:** ✅ Full CRUD — note: `discount_type` valid values are `percent` / `fixed` / `free_trial` / `free_days`

**5.8 Community Hub:** ✅ Create post (field `body` not `content`; categories: `bug_report`/`feature_request`/`question`/`feedback`), list, upvote, delete; owner-role moderation works

**5.10 Pricing Foundation:** ✅ GET/PUT `/api/pricing/defaults` (NOT `/pricing-foundation` — checklist wording corrected)

**5.11 Company Settings:** ✅ GET/PUT `/api/tenant` — phone update round-trip verified

**5.12 Email Templates:** ✅ GET (list + single), PUT, POST `/preview` — all PASS

### Bugs uncovered + fixed in this run

- 🔧 `routes/auth.py`: Fixed `Permission.USERS_EDIT` references (enum doesn't exist) → changed to `Permission.USERS_MANAGE`. This would have caused `AttributeError` on first call to admin reset-password / status routes.
- 🔧 `routes/auth.py`: Added `DELETE /api/admin/users/{id}` with three guardrails (self / staff-perm / last-owner).

### Iteration 132 follow-up — 4 missing endpoints + 1 security bug

- ✅ **T1-ISO-E** Payroll READ security: Staff role now returns `403 "You do not have permission to view payroll data"` on `GET /api/payroll/{report,balance,transactions,hours,signoff,timesheet,pay-period,timeclock-shifts,legacy-manual-entries,schedule}`
  - Fix: Added `_require_payroll_view_access()` helper to `routes/employees.py` and wired into all GET payroll routes
  - Verified: Admin (owner) still gets `200`, Staff returns `403` for `/report`, `/transactions`, `/hours`
- ✅ **T1-CSV** Customer CSV export: `GET /api/customers/export` returns `200 text/csv` with header `name,email,phone,company,status,notes,created_at`
  - Fix: New endpoint added to `routes/customers.py`
- ✅ **T3-WF-A** Workflow template apply: `POST /api/workflow-templates/{id}/apply` creates production tasks per stage for each ticket on the order; supports `replace_existing=true`
  - Verified: Applied "Apparel" template (11 stages) to order with 2 tickets → `tasks_created: 22`, `tickets_updated: [..2 ids..]`
  - Bonus: Added `POST /api/workflow-templates/{id}/duplicate` for explicit copy
  - Fix: New endpoints in `routes/workflow_templates.py`
- ✅ **T4-PORTAL-C** Customer portal appointments: `GET /api/portal/appointments?upcoming_only=&status=` returns appointment list filtered by current customer
  - Fix: New endpoint in `routes/portal.py`
- ✅ **T4-PAYROLL-A** Payroll CSV export: `GET /api/payroll/report?format=csv&start_date=...&end_date=...` streams CSV with employee-level columns
  - Fix: Added `format` query param to existing `/payroll/report` route
- ✅ **T4-EMP-PORTAL-A** `/api/employee-portal/dashboard` alias added (returns same payload as `/work-summary`)
  - Fix: Alias route added to `routes/employee_portal.py`

**Test verification:**
- ✅ All 6 endpoints tested via curl with admin + staff + portal + employee tokens
- ✅ Existing endpoints unaffected (regression spot-check: appointments, invoice-aging, quotes, workflow-templates list — all `200`)
- Test report: `/app/test_reports/iteration_132.json` (action items resolved)
