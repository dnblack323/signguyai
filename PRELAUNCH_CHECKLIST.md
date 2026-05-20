# SignGuy AI — Pre-Launch Test Checklist (Comprehensive Edition)

> **Instructions.** Work top-to-bottom. Tier 1 must pass before launch. Replace `[ ]` with `[x]` as you complete each item. Add notes inline after any item that fails (suggested format: `— FAIL: <what happened>`). Every sub-bullet is intentional; do not skip to the next section until everything above it is either checked or explicitly marked as “not applicable to this build”.
>
> **Test account:** `signguypa@gmail.com` / `Billnel323`
> **Stripe test cards:** `4242 4242 4242 4242` (success) · `4000 0000 0000 0002` (declined) · `4000 0025 0000 3155` (3DS required)
> **Business timezone:** America/New_York
> **Preview URL pattern:** `https://ai-signage-platform.preview.emergentagent.com` (read actual value from `REACT_APP_BACKEND_URL`)
>
> **Reference numbering.** Each section has a stable `X.Y` number. When we discuss an item, refer to it like **“2.3c”** or **“4.2 #5”** and we’ll both know exactly what you mean.

---

## 🔴 TIER 1 — LAUNCH BLOCKERS (Data Safety & Money)

### 1.1 Backup & Restore — **DO THIS FIRST**
_Why this is first: if anything else goes wrong, backup is the only thing that keeps you whole._

- [ ] Settings → Backup → **Export All Data** downloads a `.json` file
- [ ] Downloaded file size is **> 50 KB** (not an empty `{}`)
- [ ] Open the file in a text editor — confirm it contains all of: `customers`, `orders`, `order_items`, `employees`, `payroll_transactions`, `invoices`, `quotes`, `timeclock_shifts`
- [ ] On a clean test tenant, upload the backup → **Preview Restore** shows row counts (`"12 customers, 8 orders…"`) **without writing**
- [ ] On the test tenant, click **Restore** → toast confirms completion
- [ ] Log out → log back in → all data visible
- [ ] Refresh the Orders page → all orders render
- [ ] Open a restored Order → the attached artwork / drawing previews still resolve (Object Storage URLs valid)
- [ ] `GET /api/backup/status` returns a recent `last_backup_at` timestamp
- [ ] Scheduled digest scheduler still running post-restore (`tail -n 50 /var/log/supervisor/backend.err.log` shows `INFO: check_and_send_digests`)
- [ ] Backup file does **not** contain plaintext passwords (only bcrypt hashes — search for `$2b$` to confirm)
- [ ] **Take a live production backup NOW** before doing any of the tests below

### 1.2 Authentication & Multi-Tenant Isolation
- [ ] **Sign-up** with a brand-new email → verification email arrives within 60s
- [ ] Verification email link works → account activated
- [ ] **Login** with correct credentials lands on Dashboard
- [ ] **Login with wrong password 5 times** → user sees a sensible error (wrong password) but the account is **not permanently locked** inappropriately
- [ ] **Forgot Password** → reset email arrives → click link → set new password
- [ ] Old password **rejected** after reset; new password accepted
- [ ] **Logout** clears the session → visiting `/orders` redirects to `/login`
- [ ] **Tenant isolation (critical):**
  - [ ] Create a second tenant using a different email
  - [ ] Login as Tenant B → `GET /api/customers` via browser dev-tools / curl returns **empty array** (not Tenant A’s customers)
  - [ ] Try to fetch a Tenant A order ID directly: `GET /api/orders/<TENANT_A_ORDER_ID>` → returns 404 or 403, never the data
- [ ] **Role checks** (invite a second user with role=staff):
  - [ ] Staff cannot access `/payroll`, `/settings`, `/billing`, `/users`
  - [ ] Staff CAN access `/orders`, `/customers`, `/dashboard`
- [ ] **Session / JWT expiry:** leave a tab idle 25+ hours → next action re-prompts login
- [ ] **Email change** flow (if exposed) requires verification of the new email

### 1.3 Stripe Billing (Platform Subscriptions)
- [ ] Settings → Billing shows the current plan and next renewal date
- [ ] **Upgrade** via Stripe checkout (`4242 4242 4242 4242`, any future expiry, any CVC) → redirect returns to `/billing/success` → new plan displayed in UI and in Stripe dashboard
- [ ] **Declined card** (`4000 0000 0000 0002`) → graceful error page → plan **not** upgraded
- [ ] **3DS required card** (`4000 0025 0000 3155`) → 3DS prompt appears → after approval, plan upgrades
- [ ] **Credit top-up**: purchase the 100-credit pack → balance in navbar updates within 10s of Stripe webhook
- [ ] **Subscription cancel** at period end → Stripe dashboard shows `cancel_at_period_end=true` → user retains access until period end
- [ ] **Webhook replay**: from Stripe dashboard, resend a `checkout.session.completed` event → tenant record updated (check server logs for `✓ Stripe webhook processed`)
- [ ] **Promo code / coupon**: apply `FOUNDERS` (or the live coupon) at checkout → discount shows in Stripe session preview
- [ ] Stripe-generated invoice PDF downloads from Stripe portal and matches the charged amount

### 1.4 Stripe Connect (Merchant Payouts)
_Different from 1.3 — this is the merchant (you) receiving customer payments, not the SaaS subscription._

- [ ] Settings → Admin → **Payment Settings** → “Connect with Stripe” → completes Stripe onboarding (or Express onboarding)
- [ ] After onboarding, `GET /api/stripe-connect/status` returns `connected=true`, `charges_enabled=true`, `payouts_enabled=true`
- [ ] Open the **Stripe Express dashboard** link from the UI — it loads
- [ ] Customer pays a test invoice via Stripe Connect card (`4242 4242 4242 4242`) → funds route to **your** Stripe balance (not platform’s)
- [ ] Confirm in Stripe Connect dashboard: balance went up by the paid amount minus Stripe fees
- [ ] **Refund** from Stripe dashboard → invoice status auto-updates to `refunded` in SignGuy (via webhook)
- [ ] **Disconnect** → status flips to disconnected → future invoices fall back to platform payment flow
- [ ] Re-connect works without duplicate-account errors

### 1.5 Credits System (AI Metering)
- [ ] Navbar shows the current **credit balance**
- [ ] Buy the **100 / 300 / 1000** credit packs one at a time (test cards) → each balance update reflects after the Stripe webhook
- [ ] Every successful AI call **decrements** the balance by the published credit cost (hover the tool card to see the cost)
- [ ] **Exhaustion**: burn balance to 0 → next AI call returns **HTTP 402 Insufficient Credits** with a friendly upgrade prompt in the UI
- [ ] **Auto top-up** toggle (if enabled) triggers a recharge when balance dips below the threshold
- [ ] **Credit History** page shows every charge (+) and every consumption (−) with the action name (`ai_business_assistant`, `ai_services_prefill`, etc.)
- [ ] **Founders Edition monthly allotment** refills on the billing anniversary date
- [ ] Free-tier users cannot bypass credit gating (check Network tab — no orphaned `X-Skip-Credits` header)

### 1.6 CSV Customer Import
- [ ] **Minimal CSV** (`name,email,phone` header + 10 rows): Customers → Import → preview shows first 5 rows correctly → click Import → toast `✓ 10 customers imported` → all 10 appear in the Customers list
- [ ] **Full CSV** with all columns (`name,email,phone,address,city,state,zip,notes,tax_exempt,business_name`): every field lands in the correct place on each customer record
- [ ] **Duplicate detection**: re-upload the same CSV → either skips or flags duplicates. Document the actual behavior here: `______________________`
- [ ] **Malformed CSV** (headers only, no data rows) → clear error, nothing imported
- [ ] **Missing required column** (no `name`) → clear error message naming the missing column → nothing imported
- [ ] **Unicode names** — include these rows and verify they render perfectly (no garbling):
  - [ ] `José García`
  - [ ] `北京客户`
  - [ ] `O'Brien`
  - [ ] `Müller & Söhne`
- [ ] **Large CSV** with 500+ rows → completes in **< 30 seconds**, UI does not hang
- [ ] **Phone format variants** — all of these should be saved and searchable:
  - [ ] `(415) 555-1234`
  - [ ] `415.555.1234`
  - [ ] `415-555-1234`
  - [ ] `+1 415 555 1234`
  - [ ] `+14155551234`
- [ ] **Email validation**: row with invalid email (`not-an-email`) → that row skipped, rest imported, **error count** displayed at the end
- [ ] **Rollback**: if import fails mid-way, **no partial data** is left in the DB (search for any ghost records)
- [ ] **CSV export** of customers → download → re-import the export into a clean tenant → round-trip integrity: no duplicates, no data loss, all fields match original

---

## 🟠 TIER 2 — CORE COMMERCE

### 2.1 Customers CRUD (beyond import)
- [ ] **Create customer manually** → appears in list
- [ ] **Search** by name, email, phone — all three work independently
- [ ] **Edit** a customer (change email, add note) → changes persist after page refresh
- [ ] **Delete** customer → confirmation prompt → customer removed but any **associated orders still display the customer name** (historical integrity)
- [ ] **Customer detail page** shows: all their orders, all their invoices, total spent, portal-invite status
- [ ] **Tax-exempt toggle** → flip ON → create a new invoice for this customer → tax line is zero
- [ ] **Portal invite** from the customer detail page → invite email arrives, customer can set password and log in to portal (verified in 4.4)

### 2.2 Orders — Quick Entry
- [ ] `/orders/new` loads, customer autocomplete shows suggestions as you type
- [ ] Select a customer — their info populates the order header
- [ ] **Quick item mode**: click + Add Order Item → Quick Manual Item → enter item name + price → total updates
- [ ] **Shared context panel** renders (Production Notes, Color Notes, Location Notes, Artwork Notes) — all four fields save with the order
- [ ] **Attach artwork**: drag-and-drop a PNG onto the assets panel → appears in Order Assets list with thumbnail
- [ ] **Save as Draft** → order saved with status=draft → appears in Drafts filter on OrdersPage
- [ ] **Save Order** (non-draft) → order gets assigned an ORD-XXXX number
- [ ] Re-open the saved order → all fields round-trip correctly
- [ ] **Delete order** → confirmation → removed
- [ ] Verify no right-side duplicate “Live Estimate” sidebar exists (this was explicitly removed)
- [ ] **Add Order Item** dropdown exposes exactly these 5 options:
  - [ ] Quick Manual Item
  - [ ] Detailed Item From Scratch
  - [ ] Duplicate Existing Item (disabled when there are 0 items)
  - [ ] Create Variation From Existing (disabled when there are 0 items)
  - [ ] Add Item Using Shared Artwork

### 2.3 Orders — Detailed Item Per Category (the big one)
For **EACH** category below, follow this exact sequence:
1. Click **+ Add Order Item → Detailed Item From Scratch**
2. Select the category
3. Fill the fields listed
4. Confirm **Live Estimate** updates on the right as you type
5. Confirm **progressive disclosure** hides / shows fields per the toggles listed
6. Click **Add Item to Order** → row saved, price reflected
7. Open the saved item → edit → values round-trip correctly on reload

#### 2.3a Digital Print
- [ ] Set width × height + material + quantity → price reflects **sqft × rate × qty**
- [ ] Toggle **Lamination = Yes** → price jumps by the lamination rate
- [ ] Change quantity tier (50 → 250 → 500) → per-unit price drops at each tier
- [ ] Toggle **Rush Order = Yes** → rush % adder applied at the end
- [ ] **Artwork Ready = No** → Design Complexity field APPEARS (progressive disclosure)

#### 2.3b Cut Vinyl
- [ ] Pick vinyl type (intermediate / premium / reflective) → baseline rate changes
- [ ] Set size + color count → price updates
- [ ] **Install Required = No** → Install Complexity field is **HIDDEN**
- [ ] **Install Required = Yes** → Install Complexity APPEARS → price jumps
- [ ] **Artwork Ready = No** → Design Complexity APPEARS
- [ ] Duplicate this item → Quantity resets to 1, category stays Cut Vinyl

#### 2.3c Rigid Signs (most progressive-disclosure tests)
- [ ] Pick material (coroplast / aluminum / PVC / MDO) and thickness → price baseline changes
- [ ] **Sidedness = Single** → Double-Sided Art field is **HIDDEN**
- [ ] **Sidedness = Double** → Double-Sided Art APPEARS
- [ ] **Hardware Included = No** → Hardware Type AND Drill Prep Required are both **HIDDEN**
- [ ] **Hardware Included = Yes** → both fields APPEAR
- [ ] **Install Required = No** → Install Complexity **HIDDEN**
- [ ] **Install Required = Yes** → Install Complexity APPEARS
- [ ] **Protective Finish = No** → Finish Type **HIDDEN**
- [ ] **Protective Finish = Yes** → Finish Type APPEARS
- [ ] **Artwork Ready = No** → Design Complexity APPEARS

#### 2.3d Banners
- [ ] Pick banner type (indoor / outdoor / fabric / mesh / step-and-repeat) → baseline set
- [ ] **Grommets = None** → grommet sub-fields hidden
- [ ] **Grommets = Standard** → standard per-piece grommet charge added
- [ ] **Grommets = Custom** → Grommet Count field APPEARS → count × per-grommet charge
- [ ] **Pole Pockets = Yes** → per-side charge applied
- [ ] **Wind Slits = Yes** → per-slit charge applied
- [ ] **Install Required = Yes** → Install Complexity APPEARS

#### 2.3e Vehicle Graphics / Wraps
- [ ] Vehicle type (sedan / van / truck / trailer / motorcycle) → install hours baseline reflects
- [ ] Coverage (partial / half / full) → package baseline changes
- [ ] **Coverage = Custom** → Custom % input APPEARS → interpolates between partial and full
- [ ] Make + Model autocomplete works
- [ ] Change wrap material (calendered / cast / reflective / etched) → cost math updates
- [ ] **Lamination = Yes** → laminate type selector APPEARS → adds laminate cost
- [ ] **Window Perf = Yes** → scope selector APPEARS (rear only / sides only / both) → perf sqft × rate
- [ ] **Install Required = Yes** → Install Difficulty + Seam Complexity APPEAR
- [ ] **Second Installer = Yes** → helper labor added
- [ ] **Surface Prep = Yes** → prep hours added
- [ ] **Removal Required = Yes** → removal hours added
- [ ] Rush % applied at end if Rush = Yes

#### 2.3f Apparel
- [ ] Product Type (tee / hoodie / cap / visor / bag) switches the Brand Style list
- [ ] Brand Style + Blank Color + Quantity → shop-table sell-price per piece
- [ ] Decoration Method dropdown includes HTV, DTF, Screen Print Transfer, Direct Screen Print, Embroidery, DTG, Patch, Sublimation, Specialty
- [ ] **Shop-table methods** (HTV / Screen Print Transfer / DTF) pull exact per-piece sell from the shop_pricing_table
- [ ] **Cost-plus methods** (Direct Screen / Embroidery / DTG / Sublimation) use method_config rules
- [ ] **Size Breakdown** entry — enter S=5 M=5 L=10 XL=5 2XL=2 3XL=1 4XL=1 — quantity auto-sums to 29
- [ ] Plus-size upcharge auto-applied starting at 2XL (2XL = 1× adder, 3XL = 2× adder, 4XL = 3× adder, 5XL = 4× adder)
- [ ] **Custom Names/Numbers = Yes** → per-piece upcharge added
- [ ] **Two-tone Hat = Yes** (cap product only) → $1.50 adder per piece
- [ ] **Leather Patch = Yes** (cap only) → $2.50 adder per piece
- [ ] **Bag & Fold = Yes** → $1 adder per piece
- [ ] **Setup Fee** charged **once per order item**, not per piece
- [ ] Rush % applied at end if Rush = Yes

#### 2.3g Services (deepest — newest build)
Test **every** scenario; each one exercises a different calculation branch.

- [ ] **Hourly Installation** — `service_type=installation, billing_unit=hour, estimated_hours=4, labor_role=lead_installer, travel=15mi, trip_charge=yes, trip_count=1, equipment=scissor_lift, equipment_days=1, rush=yes` → suggested price ≈ **$1,100**, profit > $500, margin > 40 %
- [ ] **Flat-Fee Graphic Design** — `service_type=graphic_design, billing_unit=flat, flat_fee=250, complexity=medium` → suggested price = **$250 × 1.25 = $312.50** (or minimum if higher)
- [ ] **Consultation Minimum Enforcement** — `service_type=consultation, billing_unit=hour, estimated_hours=0.25` → price floors at the **$50 consultation minimum** (not $12.50 labor)
- [ ] **Delivery Per Mile** — `service_type=delivery, billing_unit=mile, miles=25` → price = 25 × per-mile rate
- [ ] **Delivery Per Trip** — `service_type=delivery, billing_unit=trip, trip_count=2` → price = 2 × trip rate
- [ ] **Subcontracted Permit** — `service_type=permit_handling, flat_fee=150, subcontracted=yes, sub_cost=100, markup_applies=yes` → price = 150 + (100 × 1.20) = **$270** (20% markup on sub)
- [ ] **Equipment Rental Standalone** — `service_type=equipment_rental, equipment_type=boom_lift, equipment_days=2` → cost + sell pulled from equipment library
- [ ] **File Cleanup Flat Fee** — `service_type=file_cleanup, billing_unit=flat, flat_fee=35` → price = $35 (or shop minimum)
- [ ] **Site Survey With Travel** — `service_type=site_survey, billing_unit=flat, flat_fee=75, travel=12mi, trip_charge=yes` → price includes flat + travel_sell + trip charge
- [ ] **Wrap Install Labor with Complexity** — `service_type=wrap_install, billing_unit=hour, hours=6, complexity=difficult (×1.5)` → labor cost reflects the 1.5 multiplier
- [ ] **AI Prefill** — click ✨ Sparkles → type “Install 4 aluminum signs 15 miles away, needs a scissor lift” → fields populate; Service Type shows **“AI”** badge
- [ ] Manually change Labor Role after AI prefill → that field’s badge flips to **“Edited”**
- [ ] Other AI-populated fields retain the **“AI”** badge
- [ ] Un-touched default fields show the **“Default”** badge
- [ ] **AI never overwrites**: set Service Type = wrap_install FIRST, THEN click Prefill with a description mentioning “installation” → Service Type stays **wrap_install** (AI did not overwrite your input)
- [ ] **Rush from Pricing Foundation**: set Pricing Foundation → default_rush_percent = 17.5 → toggle Rush = Yes on the order item → breakdown.`rush_percent_source` = `foundation`, `rush_percent_applied` = `17.5`
- [ ] **Rush fallback**: clear default_rush_percent (null) → breakdown.`rush_percent_source` = `services_category`, `rush_percent_applied` = `25.0`
- [ ] **Explicit 0% foundation rush**: set default_rush_percent = 0 → honored (not silently overridden) → `rush_percent_applied` = `0`
- [ ] **Field provenance in breakdown** — open dev tools, inspect `/api/pricing/calculate` response → `breakdown.field_sources` is present and correctly tags each field (`shop_default` / `ai_estimated` / `user_entered`)
- [ ] **Spec-named totals in breakdown** — response includes: `total_labor_cost`, `total_travel_cost`, `total_equipment_cost`, `total_subcontract_cost`, `total_permit_cost`, `total_production_cost`

#### 2.3h Promotional Items
- [ ] Magnets / yard signs / stickers each have their own baseline pricing
- [ ] Quantity tier discounts kick in at the published thresholds (50 / 100 / 250 / 500 / 1000)
- [ ] Double-sided option adds the double-sided upcharge
- [ ] Rush = Yes → rush % at end

#### 2.3i Custom / Other
- [ ] Manual price entry saved as-is with no calculation override
- [ ] Description field is free-text
- [ ] No progressive-disclosure fields appear (Custom has none)

### 2.4 Order Item — Duplicate / Variant / Copy-to-Category
- [ ] On an existing order item, click the kebab menu → **Duplicate**
  - [ ] New item named **“Copy of X”**
  - [ ] Same category
  - [ ] Quantity reset to 1
  - [ ] Entry mode = **quick**
- [ ] Click **Create Variation**
  - [ ] New item named **“Variant — X”**
  - [ ] Same category
  - [ ] Entry mode = **detailed**
  - [ ] Quantity reset to 1
  - [ ] Carry-over toggles (artwork / notes / due date) work as set
- [ ] Click **Copy to Different Category** (e.g. rigid_signs → banners)
  - [ ] New item named **“Converted — X”**
  - [ ] `converted_from_category` = `rigid_signs` in the DB record
  - [ ] Universal fields preserved (artwork_ready, rush_order, quantity)
  - [ ] Category-specific fields **dropped** (e.g. `hardware_included`, `double_sided_art`) because they don’t apply to banners
- [ ] **Carry-over toggle test**: duplicate with Artwork = OFF → new item has no file links
- [ ] **Carry-over toggle test**: duplicate with Production Notes = OFF → all note fields cleared on new item
- [ ] **Carry-over toggle test**: duplicate with Due Date = OFF → due date reset to null

### 2.5 Quote → Order → Invoice → Payment (full commerce loop)
- [ ] Create a **Quote** for a customer → save
- [ ] Download the Quote PDF → logo, customer info, line items, tax line, totals all correct
- [ ] **Email the quote** to the customer → message arrives (check spam folder too)
- [ ] Customer opens the quote link → logs into portal → **Approves** → triggers signature capture
- [ ] Signature saved to the quote/order record with timestamp
- [ ] Convert approved quote → **Order** (one click) — all line items carry over
- [ ] Order → **Generate Invoice** → invoice has correct totals including tax
- [ ] Invoice PDF matches the UI totals **to the cent**
- [ ] Email the invoice → arrives with PDF attachment and a pay link
- [ ] Customer clicks pay link → Stripe checkout → pays with test card → invoice marked **paid** → order status updates
- [ ] **Partial payment**: customer pays less than full → invoice shows remaining balance
- [ ] **Second payment** closes out the invoice → status = paid
- [ ] **Refund** via Stripe dashboard → invoice auto-updates to `refunded`

### 2.6 Artwork, Files & Drawings
- [ ] Upload **PNG** to an order → thumbnail renders
- [ ] Upload **JPG** → thumbnail renders
- [ ] Upload **PDF** → preview renders (or at least opens in new tab)
- [ ] Upload **SVG** → accepted and stored (thumbnail may be fallback icon)
- [ ] Upload **AI / EPS** → accepted and stored (fallback icon)
- [ ] Upload file **> 10 MB** → uploads via chunked flow without timing out
- [ ] Upload file **> 100 MB** → either succeeds or shows a clear size-limit error (no silent fail)
- [ ] **Drawing Modal**: open on an order → draw something → save → attached as PNG to order
- [ ] Drawing modal: change color, thickness, clear, redo — all work
- [ ] **Shared Artwork**: mark an uploaded file as `is_shared=true` via the category dropdown → new order items can pick it via the Shared Artwork picker
- [ ] Delete a file → removed from Object Storage (not just DB) — the original signed URL should 404 after delete

### 2.7 Webstores / Public Storefront
_You specifically called this out as missed from V1 — test it thoroughly._

- [x] **Create a Webstore**: Webstores → + New → name, slug, logo, banner, tagline → saves
- [ ] Slug is **unique** per tenant (try creating two with same slug → second rejected)
- [x] **Add products** to the store (at least one from each category: apparel, print, rigid sign)
- [ ] For each product, confirm: title, description, price, images, size options, color options, stock on/off, featured flag
- [x] **Product image upload** — try a large PNG (8MB) → uploads, displays
- [x] **Public storefront URL** `/store/{slug}` loads **without login** (test in incognito mode)
- [x] Hero banner + logo + product grid render on **mobile** (375px width)
- [x] Hero banner + product grid render on **desktop** (1440px width)
- [x] Hero banner + product grid render on **tablet** (768px width)
- [x] Click a product → product detail page → variant selectors (size / color) present
- [x] Add to cart → cart icon updates with item count
- [x] Cart page shows correct subtotal, qty adjustable, remove works
- [ ] Checkout → enters email / shipping → Stripe Connect checkout session opens
- [ ] Pay with test card → lands on thank-you page → order confirmation email sent
- [x] Webstore order appears in **Webstores → Orders** with customer email, product, variant, amount
- [x] **Convert webstore order → internal Order/Job** (one click) → full order created with line items pre-filled
- [x] **Analytics**: Webstores → Analytics → shows views, conversions, revenue for a date range
- [ ] **Payouts page**: shows Stripe Connect payout history (synced from Stripe)
- [x] **Record payout manually** (for external settlements) → balance adjusts in the UI
- [ ] **SEO**: `view-source:/store/{slug}` has populated `<title>` and `<meta name="description">`
- [ ] **Open Graph** tags present for social sharing
- [x] **Multiple webstores**: create 2 different webstores → each has distinct URL, product set, branding, logo
- [x] **Delete webstore** → `/store/{slug}` now returns 404

### 2.8 Products Catalog (separate from Order line items)
- [x] Products page — list view with filters (by webstore, by type)
- [ ] **Add product** → title, description, price, images
- [ ] **Edit product** → changes persist
- [ ] **Delete product** → with confirm
- [x] Assign a single product to **multiple webstores** — it shows up on all of them
- [ ] `GET /api/products/defaults/apparel-options` returns the current brand/color list
- [ ] Image from Object Storage renders in thumbnail
- [x] Inventory / stock toggle affects whether it’s orderable on storefront

### 2.9 Questionnaires / Public Intake Forms
- [ ] Create a questionnaire (Questionnaires page)
- [ ] Add fields of each type:
  - [ ] Short text
  - [ ] Long text / textarea
  - [ ] Multiple choice (radio)
  - [ ] Checkbox list
  - [ ] File upload
  - [ ] Email (validated)
  - [ ] Phone (validated)
  - [ ] Dropdown / Select
- [ ] Copy the public link `/questionnaire/{id}` → open in incognito → fill out → submit
- [ ] Submission appears in dashboard with all fields + any uploaded files
- [ ] **Admin email notification** on new submission (check SendGrid logs)
- [ ] Required fields enforced — try submitting with a required field blank → blocked
- [ ] Email field validates format
- [ ] File upload respects max size
- [ ] **Portal Forms**: logged-in customers see their past submissions at `/customer-portal/forms`
- [ ] Customer can **continue an unfinished form** if saving drafts is supported

### 2.10 Public Customer Signature Page
- [ ] Create an approval or contract that requires a signature
- [ ] Copy the public signature link `/customer-sign/{token}`
- [ ] Open in incognito (no login) → page loads
- [ ] Customer signs with mouse on desktop → submit → signature stored on record
- [ ] Customer signs with finger on mobile → submit → signature stored
- [ ] **Token becomes invalid** for re-use after submit
- [ ] **Expired token** (manually mark old in DB, or wait past expiry) → friendly “This link has expired” page
- [ ] **Invalid / fabricated token** → friendly error page, no stack trace

---

## 🔵 TIER 3 — EXTENDED ORDER LIFECYCLE

### 3.1 Production Board (Kanban)
- [ ] `/production-board` loads without errors
- [ ] Columns are configured per your workflow (e.g. Queued / In Progress / Done)
- [ ] **Drag a card** between columns → status updates → **persists on refresh**
- [ ] Cards color-coded by status OR due date (confirm which)
- [ ] **Filters** work: by category, by assignee, by due date range
- [ ] Click a card → deep-links to `/orders/{id}` detail
- [ ] Overdue items visually highlighted (red border or similar)
- [ ] Real-time updates: change status in one browser tab → second tab reflects within 30s (if websocket supported) or after refresh

### 3.2 Production Tasks (Subtasks per Order Item)
- [ ] Open an order item → **Tasks** tab
- [ ] Add a task (e.g. “Laminate”, “Cut”, “Box”)
- [ ] Check off a task → marked complete with timestamp
- [ ] **Assign** a task to an employee → appears in that employee’s portal
- [ ] **Start / stop timer** on a task → time logged against the order → flows to payroll
- [ ] Reorder tasks via drag (if supported)
- [ ] Delete a task → with confirm
- [ ] All tasks completed → order item shows “Production Complete” status

### 3.3 Production Timeline / Gantt
- [ ] Timeline view shows all active orders plotted by **due date**
- [ ] **Overdue items** highlighted in red
- [ ] **Today** vertical line visible
- [ ] **Drag** a bar to reschedule (if supported) → due date updated
- [ ] Filter by employee, customer, category
- [ ] Weekly / monthly zoom toggle

### 3.4 Workflow Templates
- [ ] Settings → Production → create a template (e.g. “Standard Banner Flow”)
- [ ] Add ordered steps: Design → Print → Finish → QA → Package
- [ ] **Apply template** to a new order → tasks auto-created in order
- [ ] **Editing a template** does **NOT** retroactively change existing orders that used it
- [ ] Delete a template (not in use) → works; (in use) → warning / blocked
- [ ] Duplicate a template → new template with independent steps

### 3.5 Approvals Center
- [ ] `/approvals` lists: pending proof approvals, signature requests, payment authorizations
- [ ] Send a proof for approval → status = pending → customer portal shows it
- [ ] Customer approves proof → status updates to **approved** with timestamp + IP
- [ ] Customer can **request changes** with a comment → notification back to you via email + in-app
- [ ] **Reject** proof → order blocked from advancing to next production step
- [ ] Re-send the same proof → customer sees updated version
- [ ] Filter approvals by status, by customer, by date

### 3.6 Appointments / Scheduling
- [ ] Create an appointment (site survey, install visit, consultation)
- [ ] Associate with a customer + optionally an order
- [ ] Appointment appears on:
  - [ ] `/employee-schedule`
  - [ ] `/productivity`
  - [ ] Customer portal `/customer-portal/appointments`
  - [ ] Employee portal (if employee assigned)
- [ ] **Reminder email** sent **24h before** the appointment
- [ ] **Reschedule** from admin side → customer notified via email
- [ ] **Reschedule** from customer portal → admin notified
- [ ] **Cancel** from either side → status updates on both sides
- [ ] Calendar invite (.ics) attachment works if implemented

### 3.7 Employee Schedule
- [ ] Schedule page shows all employees across the week
- [ ] Assign an employee to a shift / appointment
- [ ] **Double-booking** conflicts flagged if employee is already booked in overlapping time
- [ ] Employee portal shows their upcoming shifts / appointments
- [ ] Print / export weekly schedule
- [ ] Week navigation (prev / next / today)
- [ ] Switch between week / day / month views (if available)

### 3.8 Productivity Dashboard
- [ ] `/productivity` shows a combined feed of orders, appointments, legacy jobs
- [ ] Filter by date range, assignee, customer, status
- [ ] Click through to each source entity (order / appointment / legacy job) — deep links work
- [ ] Legacy job detail page `/productivity/legacy-jobs/{jobId}` renders without errors
- [ ] Appointment detail page `/productivity/appointments/{appointmentId}` renders

### 3.9 Profit Margin Analytics
- [ ] `/reports/profit-margin` loads
- [ ] **Top 10 most profitable** orders listed with margin %
- [ ] **Top 10 least profitable** orders listed
- [ ] Filter by category (Digital Print, Banners, etc.), date range, customer
- [ ] **Drill-down**: click a bar → list of orders in that bucket
- [ ] **Export to CSV** works → opens in spreadsheet cleanly
- [ ] **Sanity reconciliation**: pick one specific order from the report, manually open it, compare profit_amount + margin to the report — **must match to the cent**

### 3.10 Financials Page
- [ ] `/financials` shows current-month revenue, expenses, profit
- [ ] Toggle year view → YTD numbers
- [ ] **Expense entry**: add a receipt with photo, vendor, amount, category, date → saved
- [ ] Expense photo preview renders
- [ ] **Invoice aging** buckets: 0-30 / 31-60 / 61-90 / 90+ days — counts correct
- [ ] **Unpaid invoices summary** → click through → Invoices page filtered to unpaid
- [ ] Charts / graphs render without errors on mobile + desktop

---

## 🟢 TIER 4 — PEOPLE & PORTALS

### 4.1 Employees CRUD
- [ ] Create employee → appears in roster immediately
- [ ] Assign a **4-6 digit PIN** → employee can log into Employee Portal with that PIN
- [ ] Set **hourly rate + overtime rate** → reflected in payroll calcs
- [ ] Set **title / manager / role**
- [ ] **Upload profile image** → shows on employee card
- [ ] **Link employee to user account** → employee can now access their own portal with that login
- [ ] Employee ↔ User link visible in admin UI
- [ ] **Deactivate employee** → `is_active = false` → no longer appears in payroll list for new periods but historic data preserved
- [ ] **Reset PIN** → old PIN invalidated, new PIN works

### 4.2 Payroll (your original carryover bug)
- [ ] Navigate to Team → **Timesheets** (at `/timesheets`, not `/payroll`)
- [ ] Select an employee (or click an employee row on `/payroll` dashboard — it deep-links with `?employee=<id>` pre-selected)
- [ ] Pick current pay period → worksheet loads
- [ ] **Carryover Edit** button appears next to the Carryover Balance row (pencil icon + the word “Edit”)
- [ ] Click Edit → numeric input appears with ✓ and ✗ buttons
- [ ] Type **0** → click ✓ → toast `Carryover balance updated` → value shows `$0.00`
- [ ] **Re-open the page** — carryover stays at $0
- [ ] Set override to **$500** → reflects; re-open page → still $500
- [ ] Set override to **null** via PUT `/api/employees/{id}` with `{"carryover_override": null}` → reverts to computed carryover from historical data
- [ ] **Final Total block** at the bottom of the worksheet is a big dark rectangle with 4xl font showing the sum
- [ ] **Manual time entry** row added → totals update
- [ ] **Adjustment** (bonus / deduction) → flows into Final Total
- [ ] Period sign-off → employee + admin signatures captured
- [ ] **Export payroll PDF** → totals match UI
- [ ] **Export payroll CSV** → imports cleanly into a spreadsheet app

### 4.3 TimeClock (10pm → 2pm bug fix + naive/UTC dual format)
- [ ] Clock IN from `/timeclock` → status = **Working**
- [ ] Refresh → still Working, clock-in time shows in **America/New_York** local time (NOT UTC)
- [ ] **Start lunch** → status = On Lunch; lunch_start saved
- [ ] **End lunch** → status = Working; lunch duration logged
- [ ] Clock OUT → shift closes; total hours correct (accounts for lunch)
- [ ] **Stale shift cleanup**: leave a shift open > 18 hours → next clock action auto-closes the stale shift at `clock_in + 8h`
- [ ] Payroll worksheet shows shifts in **local time** (clock_in 10:00 PM displays as `22:00`, not `14:00` or `02:00`)
- [ ] **Manually edit a shift time** in the worksheet (type `22:00` / `10:00 PM`) → save → re-open → still shows `22:00` (round-trip without drift)
- [ ] **Dual storage format** verified: real-time PIN punches store UTC with `+00:00`; manual worksheet entries store naive (no TZ) — both display correctly
- [ ] Change `/settings` timezone to a different TZ → clock displays shift in new TZ
- [ ] Hours calculations unchanged regardless of TZ (subtraction is TZ-agnostic)

### 4.4 Customer Portal — Full Coverage
- [ ] Send portal invite to a customer → email arrives
- [ ] Customer sets password → logs in at `/customer-portal/login`
- [ ] Dashboard `/customer-portal` loads with their activity summary
- [ ] **Orders** `/customer-portal/orders` — lists all their orders with status, total, due date
- [ ] **Order Detail** `/customer-portal/orders/:orderId` — line items, artwork previews, payment status visible
- [ ] **Forms** `/customer-portal/forms` — lists past questionnaire submissions
- [ ] **Form Detail** `/customer-portal/forms/:requestId` — full submission + attachments
- [ ] **Quotes** `/customer-portal/quotes` — approve / reject → triggers workflow
- [ ] **Invoices** `/customer-portal/invoices` — pay online via Stripe Connect
- [ ] **Documents** `/customer-portal/documents` — download contracts, receipts, artwork proofs
- [ ] **Messages** `/customer-portal/messages` — two-way chat inbox
- [ ] **Conversation** `/customer-portal/messages/:conversationId` — threaded view; send a message → merchant receives in Approvals inbox
- [ ] **Proofs** `/customer-portal/proofs` — artwork proofs with approve / request-change buttons
- [ ] **Proof Detail** `/customer-portal/proofs/:proofId` — large preview + comment box
- [ ] **Appointments** `/customer-portal/appointments` — view + cancel + reschedule
- [ ] **Profile** `/customer-portal/profile` — customer updates their own info
- [ ] **Portal Pages** `/customer-portal` static tenant-configured pages (About / Services) render if configured
- [ ] **Password reset from portal** — email arrives → flow works
- [ ] **Portal branding**: customer sees YOUR logo + colors, NOT the SignGuy AI branding
- [ ] **Tenant isolation**: customer of Tenant A cannot see anything from Tenant B even by URL manipulation

### 4.5 Employee Portal — Full Coverage
- [ ] PIN login at `/employee-portal/login` works
- [ ] **Dashboard** `/employee-portal` — today’s tasks, clock status, quick links
- [ ] **Clock IN / lunch / OUT** from phone, buttons big enough to tap
- [ ] **Jobs** — individual job detail `/employee-portal/jobs/:jobId` loads with attachments
- [ ] **Tasks** `/employee-portal/tasks` — all assigned tasks across all jobs
- [ ] Mark task complete → reflects in admin UI immediately
- [ ] **Pay** `/employee-portal/pay` — current pay period preview (hours, gross)
- [ ] Employee can see their adjustments (bonuses / deductions) if tenant allows
- [ ] Employee can NOT edit their own pay period unless the tenant explicitly enables manual corrections → then corrections go into admin approval queue
- [ ] **Profile** `/employee-portal/profile` — upload new profile photo, change PIN, update personal info
- [ ] **PIN recovery** flow (forgot PIN → admin resets → new PIN emailed)
- [ ] Log out clears PIN session

---

## 🔶 TIER 5 — ADMIN / TEAM / SETTINGS

### 5.1 User Management (Team Invites)
- [ ] Settings → Users → **Invite** a new user by email
- [ ] Invite email arrives with link
- [ ] Invitee clicks link → sets password → lands in your tenant with the role you assigned
- [ ] **Change role** (owner / admin / staff) on an existing user → permissions update immediately (they lose or gain access without re-login)
- [ ] **Remove user** → they lose access → their created data (orders, time entries) remains intact
- [ ] **Last owner cannot remove themselves** (guardrail)
- [ ] **Resend invite** to an unaccepted invite works
- [ ] **Revoke invite** before acceptance works

### 5.2 Admin Portal (Super-Admin / Tenant Management)
- [ ] `/admin-portal` — visible **only to super-admins**
- [ ] Lists all tenants, their active subscriptions, credit balances
- [ ] **Impersonate** a tenant (if supported) for support — view as them without password
- [ ] View platform-wide metrics (MRR, active users, etc.)
- [ ] **Payment Settings** `/admin/payments` — configure platform-side Stripe keys (super-admin only)

### 5.3 Onboarding Flow
- [ ] Brand-new account → `/onboarding` hub shows checklist with items like:
  - [ ] Add your first customer
  - [ ] Create your first order
  - [ ] Generate your first invoice
  - [ ] Connect Stripe
  - [ ] Add your first employee
- [ ] Items auto-mark done as user completes them
- [ ] **Skip** / **Complete** buttons work
- [ ] Checklist hides once 100% complete or user dismisses
- [ ] Public `/setup` route for **ProductionSetup** wizard works
- [ ] **OnboardingChecklist** component in the app ribbon / sidebar reflects status

### 5.4 Digest / Daily Email Settings
- [ ] `/settings/digest` → toggle daily / weekly digest
- [ ] Set time of day + timezone (e.g. 8:00 AM America/New_York)
- [ ] Choose what’s included (new orders, overdue invoices, upcoming appointments, time-clock summary)
- [ ] **Send test digest** → arrives immediately with real data
- [ ] **Scheduled digest actually fires** at the configured time (verify via `tail -n 200 /var/log/supervisor/backend.err.log` for `INFO: check_and_send_digests executed successfully`)

### 5.5 Founders Edition / Pricing Plans
- [ ] Public `/pricing` → Founders Edition page loads
- [ ] Select plan (Starter / Pro / Business) → Stripe checkout → subscription activated
- [ ] **Monthly vs Annual** toggle → correct price shown + charged
- [ ] **Founders coupon** auto-applied (if user qualifies)
- [ ] **Plan change — upgrade mid-month** → prorated charge on next invoice
- [ ] **Plan change — downgrade** → takes effect at period end, not immediately
- [ ] **Trial countdown** banner in app shows days remaining
- [ ] **Trial expired** → `TrialLockout` screen locks the tenant until they subscribe
- [ ] **UpgradeModal** triggers automatically on feature limits (e.g. try to add an 11th employee on a 10-employee plan)
- [ ] **UpgradePrompt** banner at top of page for approaching limits — dismissible, reappears after 7 days

### 5.6 Tiers Configuration (Feature Flags per Plan)
- [ ] Per-tier feature matrix enforced (e.g. Starter can’t access AI Tools)
- [ ] UI hides or **disables** locked features with upsell prompt
- [ ] API-level enforcement: on Starter, calling a Pro-only endpoint returns 403 with upgrade hint
- [ ] Add a beta flag to a tier → test user sees the beta feature

### 5.7 Promo Codes
- [ ] Create code with **% discount**
- [ ] Create code with **$ discount**
- [ ] Create code with **max redemptions** → enforced after N uses
- [ ] Create code with **expiry date** → rejected after date
- [ ] Assign code to **specific plan(s)** — rejected if applied to wrong plan
- [ ] Customer applies code at checkout → Stripe session has discount applied
- [ ] **Redemption count** increments in the admin view
- [ ] **Exhausted code** rejected with “No longer valid”
- [ ] **Expired code** rejected with clear message
- [ ] Delete a code → no longer usable

### 5.8 Community Hub
- [ ] `/community` loads — list of posts with likes + comment counts
- [ ] **Create a post** → add title, body, optional image
- [ ] **Edit your own post** works
- [ ] **Comment** on a post → comment appears with your name + timestamp
- [ ] **Like / unlike** a post — count updates
- [ ] **Moderation**: admin can delete any post / comment
- [ ] **Report** a post → goes to admin moderation queue
- [ ] Infinite-scroll or pagination works without duplicate entries

### 5.9 Materials Admin / Pricing Setup
- [ ] `/materials-admin` — legacy materials list, edit costs
- [ ] `/settings/pricing-setup` — pricing foundation wizard (may overlap with `/pricing-foundation`)
- [ ] `/pricing-settings` redirect to `/pricing-foundation` works
- [ ] `/materials` redirect to `/pricing-foundation` works
- [ ] No console errors on any of these routes

### 5.10 Pricing Foundation (edit propagates live to calculator)
For **each** category tab: edit one value, open `/pricing-calculator`, verify change reflected.

- [ ] **Digital Print**: change material cost → calculator reflects
- [ ] **Cut Vinyl**: change labor rate → reflects
- [ ] **Rigid Signs**: change per-material cost → reflects
- [ ] **Banners**: change grommet rate → reflects
- [ ] **Vehicle Wraps**: change install rate per hour → reflects
- [ ] **Apparel**: change shop_pricing_table entry → reflects
- [ ] **Services**: change labor role cost per hour → reflects
- [ ] **Promotional**: change per-tier rate → reflects
- [ ] **Global defaults**: change `default_rush_percent` → reflects in all categories (where rush source is foundation-sourced)
- [ ] **Reset to defaults** button works
- [ ] **Two-tab concurrency**: change in Tab A, refresh Tab B → sees change (no stale cache bug)

### 5.11 Company Settings
- [ ] Update company name / address / phone → reflected on quotes and invoices (regenerate to verify)
- [ ] **Upload company logo** → appears on:
  - [ ] PDFs (quote, invoice, payroll worksheet)
  - [ ] Transactional emails (quote email, invoice email)
  - [ ] Customer portal header
- [ ] Change tax rate → new orders use new rate; **old orders unchanged**
- [ ] Set business hours → reflected on customer portal
- [ ] **Change timezone** → redo TimeClock test from 4.3 → local display updates
- [ ] Upload a favicon → browser tab shows it

### 5.12 Email Templates
- [ ] `/settings/email-templates` lists all system emails (quote, invoice, approval, welcome, password-reset, digest)
- [ ] Edit a template → preview on the right updates live
- [ ] **Send test email** → rendered template arrives at your inbox
- [ ] Template variables render correctly (`{{customer_name}}`, `{{order_number}}`, `{{total}}`, etc.)
- [ ] Malformed template (mismatched `{{`) → error before save
- [ ] **Reset to default** reverts a customized template

---

## 🟣 TIER 6 — AI & AUTOMATIONS

### 6.1 AI Tools Page
- [ ] `/ai-tools` loads and lists every AI feature with its credit cost
- [ ] Each tool card has a **Try it** CTA that works
- [ ] **AI Email Composer** (`AIEmailComposer`) generates a draft email → **Copy** works → **Insert** into an email template works
- [ ] **AI Image Generation (Nano Banana)** → generates image → attaches to order assets
- [ ] **AI Business Assistant** `/ai-assistant` — multi-turn conversational, session persists across messages
- [ ] **AI Services Prefill** — already covered in 2.3g; also test the **402 path** by burning credits to zero first → graceful upgrade prompt
- [ ] **Voice transcription (Whisper)** — record a short voice note on an order → transcribed text appears in the notes field
- [ ] **Historical invoice PDF extract** — upload a past vendor invoice PDF → fields extracted (date, vendor, total, line items)
- [ ] **Profile → Universal Key balance** link → take the user to credit top-up if low
- [ ] Check that EVERY AI action correctly logs to `ai_usage` collection with metadata

### 6.2 Floating Assistant (Ribbon AI)
- [ ] Purple/violet bubble present in corner on every logged-in page
- [ ] Click → slideout AI chat opens
- [ ] Chat **remembers context** across page navigation within the session
- [ ] When on `/orders/<id>`, assistant can reference the current order
- [ ] When on `/customers/<id>`, assistant can reference the current customer
- [ ] Close / reopen chat → conversation history preserved
- [ ] Clear-chat button works
- [ ] Keyboard shortcut (if exposed) opens chat

### 6.3 Emails / SendGrid
- [ ] **Quote email** arrives
- [ ] **Invoice email** arrives with PDF attachment
- [ ] **Approval request email** arrives with portal link
- [ ] **Password reset email** arrives within 60s
- [ ] **Welcome email** on new user signup
- [ ] **Digest email** fires on schedule (see 5.4)
- [ ] All emails render correctly in:
  - [ ] Gmail web
  - [ ] Gmail mobile (iOS)
  - [ ] Gmail mobile (Android)
  - [ ] Outlook web
  - [ ] Outlook desktop
  - [ ] Apple Mail (Mac)
  - [ ] Apple Mail (iPhone)
  - [ ] Yahoo Mail
  - [ ] ProtonMail
  - [ ] iCloud Mail
- [ ] From address shows your company name (`SENDGRID_FROM_NAME`), not generic SignGuy
- [ ] Reply-to goes to your business inbox
- [ ] **SPF / DKIM / DMARC** records set on your sending domain — verify with `dig TXT yourdomain.com` or a tool like MXToolbox
- [ ] **Unsubscribe link** works on marketing emails (not transactional)
- [ ] Bounce rate in SendGrid dashboard < 2%
- [ ] Zero spam complaints

### 6.4 PDF / Document Generation
- [ ] **Quote PDF**: logo, customer info, line items, tax line, totals, terms, expiration date
- [ ] **Invoice PDF**: same as quote + PAID/UNPAID watermark, invoice number, due date, remit-to address
- [ ] **Payroll worksheet PDF**: all shifts visible, hours totals, pay totals, signatures if signed
- [ ] **Order work ticket PDF**: production-floor-ready — materials, specs, artwork thumbnails, due date, assigned employee
- [ ] PDFs render correctly when printed on physical paper (page breaks sensible)
- [ ] Non-ASCII characters in customer name / notes render correctly in PDF (no `??` or tofu squares)
- [ ] PDF file size reasonable (< 2 MB for typical order)

---

## ⚫ TIER 7 — SIGNATURES & DRAWINGS

### 7.1 In-App Signature Capture
- [ ] `SignatureCaptureModal` opens on an order → admin captures customer’s signature on tablet → saved to order with timestamp
- [ ] Signature also saves the signer’s name + IP address
- [ ] `SignatureActivityList` on an order shows **all historical signatures** with timestamps + ability to re-view
- [ ] **Clear / redo** works mid-signature (doesn’t save until you click Confirm)
- [ ] Signature renders correctly on invoice PDF after capture
- [ ] Signature works on tablet, desktop, phone (touch + mouse)

### 7.2 Order Drawings (Whiteboard)
- [ ] `DrawingModal` opens from an order → draw with mouse / finger
- [ ] **Tools**: pen, text, colors, thickness — all work
- [ ] `DrawingCanvasPad` saves on each stroke (debounced)
- [ ] `DrawingPreviewModal` shows the finished drawing
- [ ] Attached to order as a PNG in Order Assets → renders as thumbnail
- [ ] **Editable after save** → opens pad with existing drawing pre-loaded
- [ ] Clear / undo works
- [ ] Multiple drawings on a single order → all listed
- [ ] Works on mobile with finger input
- [ ] Large drawings (many strokes) save without performance lag

---

## 🟤 TIER 8 — DOCS & MARKETING

### 8.1 Docs / Help Center — each page loads with real content
- [ ] `/docs/getting-started`
- [ ] `/docs/customers`
- [ ] `/docs/document-library`
- [ ] `/docs/quotes-jobs`
- [ ] `/docs/invoicing`
- [ ] `/docs/pricing-calculator`
- [ ] `/docs/ai-tools`
- [ ] `/docs/time-tracking`
- [ ] `/docs/employees`
- [x] `/docs/webstores`
- [ ] `/docs/customer-portal`
- [ ] `/docs/financials`
- [ ] `/docs/productivity`
- [ ] `/docs/faq`
- [ ] Search across docs returns relevant results
- [ ] Table of Contents visible on each page
- [ ] Code snippets (if any) render with syntax highlighting
- [ ] Screenshots in docs match current UI (not outdated)
- [ ] Internal doc links (doc → doc) work
- [ ] Docs readable on mobile

### 8.2 Marketing / Public Pages (SEO-critical)
- [ ] `/` LandingPage — renders with CTA to signup
- [ ] `/features` — all feature cards + screenshots load
- [ ] `/pricing` — Founders Edition pricing displays correctly
- [ ] `/pricing-legacy` — old pricing page still accessible (if needed)
- [ ] `/founders` → FoundersEditionPricing
- [ ] `/why-founder` loads
- [ ] `/about` loads with team / mission content
- [ ] `/contact` — form submits → email to admin
- [ ] `/terms` — Terms of Service content present, contact email accurate
- [ ] `/privacy` — Privacy Policy content present
- [ ] `/platform` redirects to `/pricing-plans`
- [x] `/webstores-overview` redirects to `/pricing-plans`
- [ ] `/ai-studio` redirects to `/pricing-plans`
- [ ] `/starter`, `/pro`, `/business` redirect to `/pricing-plans`
- [x] `/webstore-launch`, `/webstore-growth`, `/webstore-scale` redirect to `/pricing-plans`
- [ ] `/ai-basic`, `/ai-pro`, `/ai-max` redirect to `/pricing-plans`
- [ ] `/pricing-plans-old` redirects to `/pricing-plans`
- [ ] **Mobile** landing page not broken at 375px
- [ ] **Lighthouse**: performance > 85, accessibility > 90 on landing page
- [ ] **Favicon** set
- [ ] **Open Graph image** set (test: paste URL into Slack / Facebook / Twitter preview)
- [ ] **meta description** on each public page
- [ ] **robots.txt** and **sitemap.xml** serve correctly

---

## 🟢 TIER 9 — NAVIGATION / SHELL / QUALITY

### 9.1 Main Layout & Ribbon
- [ ] `MainLayout` sidebar shows the correct items per role:
  - [x] Owner sees: Dashboard, Orders, Billing, Customers, Webstores, Documents, Team, AI Tools, Financials, Productivity, Reports, Community, Settings
  - [ ] Admin sees: same minus Billing/Settings high-risk areas (verify per your RBAC matrix)
  - [ ] Staff sees: limited subset
- [ ] **Ribbon** (`/components/ribbon`) — user can pin / unpin favorite actions
- [ ] Pinned items persist across sessions (stored per-user)
- [ ] **QuickToolbar** keyboard shortcuts work (if exposed — e.g. `Cmd+K` to search)
- [ ] **ScrollToTop** — clicking a nav link resets scroll to top of new page
- [ ] **Breadcrumbs** accurate (Dashboard → Orders → Order #ORD-1234)
- [ ] **Active route** highlighted in sidebar
- [ ] **Collapsible sidebar** state persists

### 9.2 Trial / Upgrade UX
- [ ] `TrialLockout` screen renders when trial has ended — only Billing link clickable (all other routes locked)
- [ ] `UpgradeModal` pops when hitting a plan limit (e.g. >10 employees on Starter)
- [ ] `UpgradePrompt` banner appears for approaching limits — dismissible, reappears after 7 days
- [ ] **Founders banner** (`/components/founders`) appears if user has founding-member badge
- [ ] Upgrade buttons in modal actually deep-link to the right Stripe checkout

### 9.3 Dashboard
- [ ] Dashboard shows key widgets: today’s revenue, pending orders, overdue invoices, upcoming appointments
- [ ] Widgets **refresh** when you switch tabs (via focus event) OR every N minutes
- [ ] Click a widget → drills into corresponding page with appropriate filters pre-applied
- [ ] **Empty states** friendly (“No orders yet — [Create your first]”)
- [ ] Charts / graphs render without console errors
- [ ] Mobile dashboard legible (widgets stack, not squashed)

### 9.4 Dev Panel
- [ ] `/components/DevPanel` hidden from regular users in production
- [ ] Only admins / developers can see it
- [ ] Dev panel features (feature flags, DB stats) all behave correctly

### 9.5 Mobile / Responsive
Test each critical page at these widths: **375px (iPhone SE), 390px (iPhone 14), 768px (iPad portrait), 1024px (iPad landscape / laptop)**:

- [ ] Login
- [ ] Dashboard
- [ ] Orders list
- [ ] Order detail
- [ ] Add Order Item flow (the detailed entry)
- [ ] Timesheets / Payroll
- [ ] TimeClock (critical — must be one-hand usable on phone)
- [ ] Customer portal
- [ ] Employee portal
- [ ] Checkout flow
- [ ] Public storefront
- [ ] No horizontal scroll on any of the above
- [ ] Modals readable, close button reachable
- [ ] Bottom-sheet / sticky actions don’t cover important content

### 9.6 Browsers
Run the critical flow (login → create order → add detailed item → save):

- [ ] Chrome latest (Mac)
- [ ] Chrome latest (Windows)
- [ ] Chrome latest (Android)
- [ ] Safari latest (Mac)
- [ ] Safari latest (iPhone)
- [ ] Safari latest (iPad)
- [ ] Firefox latest
- [ ] Edge latest
- [ ] No console errors in any of the above

### 9.7 Error States
- [ ] Visit `/orders/does-not-exist` → friendly “Order not found” (not stack trace)
- [ ] Visit `/random-route-nothing-here` → 404 page with link back to dashboard
- [ ] Kill internet mid-save → toast “Connection lost — retry” (no data lost, form state preserved)
- [ ] Slow network (throttle to 3G) → loading states visible, no blank screens
- [ ] **Disabled buttons** show clearly (opacity, cursor)
- [ ] 500 server error on a form submit → user-friendly message, option to retry
- [ ] Session expired mid-session → redirected to login with “Please sign in again” notice
- [ ] Rate-limited action → clear “Too many attempts, wait X minutes”

### 9.8 Accessibility
- [ ] Tab key navigates through the Order form in logical order
- [ ] Every interactive element has a visible **focus state**
- [ ] Screen-reader labels present on icon-only buttons (e.g. the Edit pencil in 4.2 has `aria-label`)
- [ ] Color contrast passes **WCAG AA** on key pages (use axe-DevTools browser extension)
- [ ] Form errors announced to screen readers (`aria-live`)
- [ ] Modal focus trap — Tab doesn’t escape the modal
- [ ] Escape key closes modals
- [ ] Alt text present on all customer-uploaded images (auto-generated or user-provided)
- [ ] Can complete a whole order creation using **only keyboard**

### 9.9 Performance
- [ ] Dashboard loads in **< 2.5s** on a 4G throttled connection (Chrome DevTools → Network → Fast 3G)
- [ ] Large customer list (500+) paginates without lag
- [ ] Large order list (500+) paginates without lag
- [ ] Uploading a 20MB PDF doesn’t freeze the UI
- [ ] Live Estimate preview recalculates within 100ms of user input
- [ ] Lighthouse Performance > 85 on dashboard
- [ ] No memory leaks on long session (leave tab open 1hr — RAM stays stable)

### 9.10 Security Sanity
- [ ] Backup file does **not** contain plaintext passwords (only bcrypt `$2b$` hashes)
- [ ] JWT expiry enforced (verify: decoded JWT has `exp` claim)
- [ ] No secrets in client bundle:
  - `curl https://<your-site>/static/js/main.*.js | grep -i "sk_live"` → **empty**
  - Same for `sk_test`, `rk_live`, `AKIA` (AWS), `EMERGENT_LLM_KEY`
- [ ] **HTTPS only** on production URL (HTTP redirects to HTTPS)
- [ ] **Strict Transport Security (HSTS)** header present
- [x] `Authorization: Bearer <token>` header required on ALL `/api/*` endpoints (except genuinely public ones like `/storefront/*`, `/questionnaire/*`, `/customer-sign/*`)
- [ ] SQL / NoSQL injection attempts on search inputs → safely escaped (try `'; DROP TABLE orders;` and `{"$ne": null}` as customer name)
- [ ] XSS attempts rendered as plain text (try `<script>alert(1)</script>` as a note)
- [ ] Rate limiting on auth endpoints (see 11.4)
- [ ] No CORS wildcard `*` on production (set to your actual origins)

### 9.11 Legal / Compliance Copy
- [ ] Terms of Service page loads and is current
- [ ] Privacy Policy page loads and is current
- [ ] Cookie banner (if EU traffic) — appears, accept/decline works, choice stored
- [ ] Footer has **correct year** (auto-updated or manually set to current)
- [ ] GDPR data-export request flow (if serving EU) — user can download their own data
- [ ] GDPR data-deletion request flow — user can delete their account + data
- [ ] CCPA data-sale opt-out if serving CA users

---

## 🔺 TIER 10 — REGRESSION / DATA INTEGRITY

### 10.1 Legacy Redirects
- [ ] `/jobs` → redirects to `/productivity` (or wherever the current jobs view lives)
- [ ] `/jobs/:id` → `LegacyJobRedirect` handles old bookmarks, lands on correct entity
- [ ] `/workflow-templates` → `/settings/production`
- [ ] `/materials` → `/pricing-foundation`
- [ ] `/reports` → `/financials`
- [ ] `/pricing-calculator/settings` → `/pricing-foundation`
- [ ] `/register` → `/login?register=true`
- [ ] Old public marketing URLs all redirect to `/pricing-plans` (see 8.2)
- [ ] Pasting any old bookmark URL in the address bar doesn’t dump the user on a 404

### 10.2 Terminology Consistency (Job → Order migration)
- [ ] No page shows the old words **“Job Ticket”**, **“Job Item”**, or standalone **“Job”** in user-facing text
- [ ] Email templates updated with new terminology
- [ ] PDF documents (quotes, invoices, worksheets) use **“Order / Order Item”**
- [ ] Docs pages use new terminology
- [ ] Marketing pages use new terminology (highly public-facing)
- [ ] Customer portal uses new terminology
- [ ] Employee portal uses new terminology
- [ ] System emails use new terminology
- [ ] Search for old terms: `grep -ri "job ticket\|job item" /app/frontend/src/pages /app/frontend/src/components` should return nothing user-facing
- [ ] Backend routes / collections / field names unchanged (internal compatibility layer — verify no breakage)

### 10.3 Full End-to-End Scenario (realistic 1-hour test)
- [ ] Customer submits a public **Questionnaire** describing a wrap + rigid sign job
- [ ] You create a **Quote** from the submission (2 line items + services install)
- [ ] Customer receives quote email → logs into portal
- [ ] Customer **approves the quote** → public signature link captures signature
- [ ] Quote → Order (one click) with all 2 items + services line
- [ ] Open the Services item → **AI Prefill** fills out the installation details based on the original questionnaire description
- [ ] **Upload artwork** to the order → customer approves via portal **Proofs** flow
- [ ] **Production tasks** auto-created from the workflow template
- [ ] Employees **clock time** against the order tasks
- [ ] Order moves across the **Production Board** (Queued → In Progress → Done)
- [ ] Generate invoice → email to customer → customer pays via **Stripe Connect**
- [ ] Invoice marked paid → order closed
- [ ] **Profit Margin Analytics** reflects the revenue and margin correctly for this order
- [ ] **Tonight’s digest email** mentions the completed job
- [ ] **Payroll worksheet** for the employees shows the time they clocked against this order
- [ ] **Customer receives thank-you follow-up** (if automation configured)
- [ ] Order shows up in the customer portal as completed with invoice link

### 10.4 Data Export / Migration
- [ ] Export customers to CSV → reimport into a fresh test tenant → data matches exactly
- [ ] Export orders (if endpoint exists) → re-import round-trip
- [ ] Export payroll transactions
- [ ] Export webstore orders
- [ ] Export employees
- [ ] Export all time entries
- [ ] Each exported CSV has UTF-8 BOM so Excel opens it correctly with non-ASCII names

---

## ⚪ TIER 11 — OPERATIONAL READINESS

### 11.1 Health Checks & Logs
- [ ] `GET https://your-domain/` returns 200
- [ ] `GET https://your-domain/api/` returns 200 JSON (not HTML)
- [ ] `tail -n 100 /var/log/supervisor/backend.err.log` clean (no ERROR or CRITICAL)
- [ ] `tail -n 100 /var/log/supervisor/backend.out.log` shows `Application startup complete.` right after object storage init (no hanging — the deployment fix)
- [ ] `tail -n 100 /var/log/supervisor/frontend.err.log` clean
- [ ] Supervisor status: `sudo supervisorctl status` — all services RUNNING
- [ ] MongoDB connection healthy (backend logs show successful queries)
- [ ] Object Storage reachable (test file upload works)

### 11.2 Email Deliverability
- [ ] SendGrid dashboard: bounce rate < 2%, zero spam complaints in last 7 days
- [ ] Test emails sent to each of: Gmail, Outlook, Yahoo, ProtonMail, iCloud, Fastmail → ALL land in **inbox**, not spam
- [ ] SPF valid (check with `dig TXT yourdomain.com`)
- [ ] DKIM valid (check SendGrid settings)
- [ ] DMARC policy = at least `p=none` with `rua=` reporting address
- [ ] **Unsubscribe** link on marketing emails works and persists
- [ ] **List-Unsubscribe** header present (one-click unsubscribe in Gmail)

### 11.3 Monitoring & Alerts
- [ ] Sentry (or equivalent) error tracking hooked up — generate a test error and verify it appears
- [ ] Stripe webhook endpoint monitored — failed deliveries trigger an alert
- [ ] Backup job failures trigger email to admin
- [ ] Backend CPU / memory monitored (at least basic uptime)
- [ ] MongoDB slow-query alerting (if configured)
- [ ] Uptime monitoring (StatusCake / UptimeRobot / Pingdom) pings every minute
- [ ] Admin gets paged if `/api/` returns non-200 for > 5 minutes

### 11.4 Rate Limiting / Abuse
- [ ] Rapid-fire the login endpoint (10+ attempts in 10s) → temporarily blocked (429 or similar)
- [ ] Public `questionnaire` endpoint — can’t be spammed by a bot (rate limit or captcha)
- [ ] Public storefront checkout can’t be DDoS’d (Stripe’s anti-fraud helps but verify no bare endpoints)
- [ ] File upload size cap enforced (try 500MB → rejected with clear error, not 500)
- [ ] Max request body size enforced
- [ ] AI endpoints rate-limited per user (beyond credits — prevent cost explosion)

### 11.5 DNS / Domain
- [ ] Production URL resolves (apex + `www`)
- [ ] SSL certificate valid, **no mixed-content warnings** in browser console
- [ ] `www.yourdomain.com` and `yourdomain.com` both resolve and redirect consistently (decide which is canonical)
- [ ] Email domain (MX records) correctly set
- [ ] Nameservers stable (not flapping)
- [ ] Certificate auto-renewal configured (Let’s Encrypt or similar)
- [ ] Redirects from old domains (if any) work

---

## 📋 Launch-Day Execution Order

1. **Back up everything** (1.1) — ALWAYS first
2. **Deploy** and verify health (11.1)
3. **Smoke-test revenue loop**: new customer → quote → order → invoice → payment → payout (this proves money works end-to-end)
4. **Spot-check one item** from every tier header
5. **Invite 3-5 beta users** to run Tiers 2-4 over 48 hours
6. **Monitor logs continuously** for the first 24h post-launch: `tail -f /var/log/supervisor/backend.err.log`
7. Work through Tiers 5-11 in week one
8. Re-run Tier 1 **weekly** for the first month

---

## 📝 Open Questions / Integrations to Verify
_If any of these are wired up in your build, expand them into their own sections:_

- [ ] **Telegram** integration (notifications, bots)
- [ ] **Twilio SMS** (order status texts, appointment reminders)
- [ ] **Slack** notifications (new order → #sales channel)
- [ ] **Google Calendar** sync (appointments)
- [ ] **Gmail** integration (send quotes from Gmail, log replies)
- [ ] **Discord** webhooks
- [ ] **Barcode / QR scanning** on production floor (scan work ticket → pull up order)
- [ ] **Print stylesheets** for work tickets (browser Print → shop-floor-friendly layout)
- [ ] **Dark mode** on key pages
- [ ] **PWA / offline mode** (service worker, installable)
- [ ] **Multi-language / i18n** (Spanish? French?)
- [ ] **Native mobile app** (iOS / Android)
- [ ] **Native push notifications** (web push API)
- [ ] **Zapier / Make** integrations
- [ ] **QuickBooks / Xero** accounting sync
- [ ] **Shipping integrations** (USPS, UPS, FedEx label printing)
- [ ] **Payment methods beyond Stripe** (Square, PayPal, ACH via Plaid)
- [ ] **Subscription boxes** (recurring orders)

---

## 🎯 Critical Pre-Launch Gates (one-page cheat sheet)

**DO NOT launch until all of these are green:**

1. ✅ Tier 1.1 — Backup works end-to-end
2. ✅ Tier 1.2 — Auth + tenant isolation rock solid
3. ✅ Tier 1.3 — Stripe billing processes test cards
4. ✅ Tier 1.4 — Stripe Connect receives customer payments to YOUR balance
5. ✅ Tier 1.5 — Credits system enforces limits
6. ✅ Tier 1.6 — CSV import handles real customer data
7. ✅ Tier 2.5 — Quote → Order → Invoice → Payment loop works
8. ✅ Tier 2.7 — Public storefront takes a real order
9. ✅ Tier 4.2 — Payroll carryover edit works
10. ✅ Tier 4.3 — TimeClock displays local time correctly
11. ✅ Tier 6.3 — Emails land in inbox on all major providers
12. ✅ Tier 9.10 — No secrets leaked in client bundle
13. ✅ Tier 11.1 — Backend starts within 30s, no hanging
14. ✅ Tier 11.2 — Deliverability clean (SPF/DKIM/DMARC)
15. ✅ Tier 11.5 — HTTPS, valid SSL, both apex + www resolve

---

**Last updated:** {{fill in on launch day}}
**Signed off by:** {{your name}}
**Launched on:** {{date}}
**Rollback contact:** {{name / phone}}
