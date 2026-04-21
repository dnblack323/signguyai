# SignGuy AI — Pre-Launch Test Checklist

> **Instructions:** Work top-to-bottom. Tier 1 must pass before launch. Replace `[ ]` with `[x]` as you complete each item. Add notes inline after any item that fails.
>
> **Test account:** `signguypa@gmail.com` / `Billnel323`  
> **Stripe test card:** `4242 4242 4242 4242` (success) · `4000 0000 0000 0002` (fail)  
> **Timezone:** America/New_York

---

## 🔴 TIER 1 — BLOCKERS (Data Safety & Money)

### 1.1 Backup & Restore — DO THIS FIRST
- [ ] Full export downloads as `.json` > 50 KB
- [ ] Contains customers, orders, employees, payroll, invoices
- [ ] Preview restore shows correct row counts on a test tenant
- [ ] Execute restore → log out / back in → all data visible
- [ ] `GET /api/backup/status` returns a recent `last_backup_at`
- [ ] Restored artwork/drawings render (Object Storage links resolve)
- [ ] **Live production backup taken _before_ any other testing**

### 1.2 Authentication & Multi-Tenant Isolation
- [ ] Sign-up with new email → verification email arrives → link works
- [ ] Login with correct password lands on Dashboard
- [ ] 5× wrong password shows correct error (account not wrongly locked)
- [ ] Forgot-password email arrives → new password works, old rejected
- [ ] Logout redirects protected routes to `/login`
- [ ] Tenant B cannot see Tenant A's data (`GET /api/customers` with B's token returns empty)
- [ ] Staff role cannot access Payroll / Billing / Company Settings
- [ ] JWT expires after 24h, re-prompts login

### 1.3 Stripe Billing (Platform Subscriptions)
- [ ] View current plan at Settings → Billing
- [ ] Upgrade via `4242 4242 4242 4242` → `/billing/success` → plan updated
- [ ] Failed card `4000 0000 0000 0002` → graceful error, plan NOT upgraded
- [ ] Buy 100 AI credits → balance updates in navbar
- [ ] Cancel subscription → retains access until period end
- [ ] Re-send Stripe webhook `checkout.session.completed` → tenant updated in logs
- [ ] Apply coupon / promo → discount shows in checkout
- [ ] Stripe-generated invoice PDF downloads

### 1.4 Stripe Connect (Merchant Payouts)
- [ ] Settings → Admin → Payment Settings → Connect with Stripe succeeds
- [ ] `GET /api/stripe-connect/status` → `charges_enabled=true, payouts_enabled=true`
- [ ] Customer pays invoice → funds land in YOUR Stripe balance (not platform)
- [ ] Express dashboard link opens
- [ ] Disconnect works; future invoices revert to platform payment
- [ ] Refund via Stripe dashboard auto-updates invoice to `refunded`

### 1.5 Credits System (AI Metering)
- [ ] Navbar shows current credit balance
- [ ] Buying 100 / 300 / 1000 credits updates balance post-webhook
- [ ] AI action decrements credits by published cost
- [ ] At 0 credits, AI call returns 402 with friendly upgrade prompt
- [ ] Auto top-up (if enabled) triggers recharge below threshold
- [ ] Credit history page logs every charge + consumption
- [ ] Founders Edition monthly allotment refills on billing anniversary

### 1.6 CSV Customer Import
- [ ] Minimal CSV (`name,email,phone`): preview shows 5 rows, import succeeds
- [ ] Full CSV (all columns) imports all fields correctly
- [ ] Duplicate detection behavior documented (skip or flag)
- [ ] Malformed CSV (no data rows) → clear error, nothing imported
- [ ] Missing required column → rejected with explanation
- [ ] Unicode names (José, 北京) preserved
- [ ] 500+ rows complete in < 30s without UI hang
- [ ] Phone format variants all saved/searchable
- [ ] Invalid emails: bad rows skipped, error count shown, rest imported
- [ ] Mid-import failure → no partial data stuck
- [ ] CSV export → re-import round-trips cleanly

---

## 🟠 TIER 2 — CORE COMMERCE

### 2.1 Customers CRUD
- [ ] Create customer manually
- [ ] Search by name / email / phone
- [ ] Edit customer — changes persist
- [ ] Delete customer — confirm prompt → order history retains `customer_name`
- [ ] Customer detail page: all orders, invoices, total spent
- [ ] Tax-exempt toggle removes tax on new invoices

### 2.2 Orders — Quick Entry
- [ ] `/orders/new` loads, customer autocomplete works
- [ ] Quick item mode adds a manual line item, total updates
- [ ] Shared context (production/artwork/location notes) saves on order
- [ ] Drag-and-drop artwork attaches
- [ ] Save as Draft → appears in Drafts filter
- [ ] Save Order → gets ORD-XXXX number
- [ ] Delete order → confirm prompt → removed

### 2.3 Orders — Detailed Item Per Category
For each category: select category → fill fields → confirm Live Estimate updates → confirm progressive disclosure → click "Add Item to Order" → reopen to verify round-trip.

**2.3a Digital Print**
- [ ] Width/height/material/qty → sqft pricing
- [ ] Lamination toggle bumps price
- [ ] Quantity tier drops per-unit price
- [ ] Rush order adds rush %

**2.3b Cut Vinyl**
- [ ] Vinyl type + size + color count pricing
- [ ] Install Required = No → Install Complexity HIDDEN
- [ ] Install Required = Yes → APPEARS, price jumps

**2.3c Rigid Signs**
- [ ] Material + thickness pricing
- [ ] Sidedness = Single → Double-Sided Art HIDDEN
- [ ] Sidedness = Double → APPEARS
- [ ] Hardware = No → Hardware Type + Drill Prep HIDDEN
- [ ] Hardware = Yes → APPEAR
- [ ] Install Required = No → Install Complexity HIDDEN
- [ ] Protective Finish = Yes → Finish Type APPEARS

**2.3d Banners**
- [ ] Banner type baseline
- [ ] Grommets adder; "custom" reveals Grommet Count
- [ ] Pole pockets per-side
- [ ] Wind slits per slit

**2.3e Vehicle Graphics / Wraps**
- [ ] Vehicle type shifts install hours
- [ ] Coverage (partial/half/full/custom); custom reveals % input
- [ ] Wrap material + laminate math
- [ ] Window perf toggle + scope (rear/sides)
- [ ] Second installer adds helper labor
- [ ] Install difficulty × seam multipliers reflected in breakdown

**2.3f Apparel**
- [ ] Product type switches brand list
- [ ] Blank brand/color/qty tier → shop-table per-piece price
- [ ] Decoration method routes to correct config
- [ ] Size breakdown applies 2XL+ upcharge automatically
- [ ] Custom names/numbers toggle adds upcharge
- [ ] Setup fee applied once, not per piece

**2.3g Services (deepest — newest)**
- [ ] Hourly Installation: 4h / lead_installer / 15mi / scissor_lift / rush → ≈ $1,100, margin > 40%
- [ ] Flat-Fee Design: flat $250 × medium = $312.50 (or min if higher)
- [ ] Consultation 0.25h → floors to $50 minimum
- [ ] Delivery per-mile: miles × rate
- [ ] Subcontracted Permit: $100 sub + 20% markup applied
- [ ] Equipment rental standalone (boom_lift × 2 days)
- [ ] AI Prefill: "Install 4 signs 15 miles, scissor lift" populates fields; Service Type badge = "AI"
- [ ] Manually change Labor Role → badge flips to "Edited"
- [ ] AI never overwrites: pre-set wrap_install stays wrap_install after prefill w/ "installation" description
- [ ] At least one "Default", one "AI", one "Edited" badge visible
- [ ] Foundation rush 17.5% → breakdown.rush_percent_source = "foundation"

**2.3h Promotional Items**
- [ ] Magnets / yard signs / stickers with qty-tier discounts

**2.3i Custom / Other**
- [ ] Manual price entry saved as-is

### 2.4 Order Item — Duplicate / Variant / Copy-to-Category
- [ ] Duplicate → "Copy of X", quick mode, qty reset
- [ ] Variation → "Variant — X", detailed mode
- [ ] Copy to different category (rigid → banners) → specs remapped, category-specific fields dropped
- [ ] Carry-over toggles (artwork off / notes off) respected

### 2.5 Quote → Order → Invoice → Payment
- [ ] Create Quote → save → PDF downloads
- [ ] Email quote arrives in inbox
- [ ] Customer portal: approve quote → signature captured
- [ ] Convert to Order (one click)
- [ ] Generate Invoice with correct tax
- [ ] Invoice PDF matches UI totals to the cent
- [ ] Email invoice → pay link works
- [ ] Stripe payment marks invoice paid, order status updates
- [ ] Partial payment shows remaining balance

### 2.6 Artwork & Drawing
- [ ] PNG/JPG/PDF upload → thumbnail renders
- [ ] SVG/AI/EPS at least stored
- [ ] >10MB uploads via chunked flow
- [ ] Drawing modal → save → attaches as PNG to order
- [ ] Mark artwork as Shared → Shared Artwork Picker surfaces it on new items
- [ ] Delete file removes from Object Storage

### 2.7 Webstores / Public Storefront
- [ ] Create webstore (name, slug, logo, banner)
- [ ] Add ≥ 3 products (apparel, print, rigid)
- [ ] Product: title, description, price, images, size/color options, stock toggle
- [ ] `/store/{slug}` loads WITHOUT login (incognito test)
- [ ] Hero banner + grid render mobile + desktop
- [ ] Product detail → variant selector → add to cart
- [ ] Cart checkout via Stripe Connect → thank-you page
- [ ] Order appears in Webstores → Orders with customer + variant + amount
- [ ] Convert webstore order → internal Order/Job (one click)
- [ ] Analytics shows views / conversions / revenue
- [ ] Payouts page shows Stripe Connect payout history
- [ ] Manual payout recording works
- [ ] Large product images upload without error
- [ ] SEO: `<title>` / `<meta description>` populated per webstore
- [ ] Multiple webstores: distinct URLs, products, branding
- [ ] Delete webstore → URL 404s

### 2.8 Products Catalog
- [ ] Products page: add / edit / delete
- [ ] Product image from Object Storage renders
- [ ] Assign product to multiple webstores
- [ ] `GET /api/products/defaults/apparel-options` returns brand/color list

### 2.9 Questionnaires / Public Intake
- [ ] Create questionnaire with text / MCQ / file fields
- [ ] Public link `/questionnaire/{id}` opens without login
- [ ] Submit → appears in dashboard with attachments
- [ ] Admin email notification
- [ ] Required fields + email validation enforced
- [ ] Portal Forms shows customer's past submissions

### 2.10 Public Customer Signature
- [ ] Send `/customer-sign/{token}` link
- [ ] Loads without login, signature captured
- [ ] Token invalidated after use
- [ ] Expired token shows friendly message

---

## 🔵 TIER 3 — EXTENDED ORDER LIFECYCLE

### 3.1 Production Board (Kanban)
- [ ] `/production-board` loads with columns
- [ ] Drag card between columns persists
- [ ] Filters by category / assignee / due date
- [ ] Deep-link to order detail

### 3.2 Production Tasks
- [ ] Add task on order item, assign employee
- [ ] Check off completes
- [ ] Start/stop timer ties to payroll

### 3.3 Production Timeline / Gantt
- [ ] Timeline shows active orders by due date
- [ ] Overdue items highlighted
- [ ] Drag to reschedule (if supported)

### 3.4 Workflow Templates
- [ ] Create template in Settings → Production
- [ ] Apply to new order → tasks auto-created
- [ ] Editing template does NOT alter existing orders

### 3.5 Approvals Center
- [ ] `/approvals` lists pending proofs / signatures / auths
- [ ] Send proof → customer approves → status updates
- [ ] Customer can request changes → notifies admin
- [ ] Reject blocks order progression

### 3.6 Appointments
- [ ] Create, tied to customer + order
- [ ] Shows on `/employee-schedule` + `/productivity`
- [ ] Customer sees it in `/customer-portal/appointments`
- [ ] Reminder email sent 24h prior
- [ ] Reschedule / cancel from both sides

### 3.7 Employee Schedule
- [ ] Week grid across employees
- [ ] Double-book conflicts flagged
- [ ] Employee sees upcoming shifts in portal
- [ ] Export weekly schedule

### 3.8 Productivity Dashboard
- [ ] Shows orders + appointments + legacy jobs
- [ ] Filters by date / assignee / customer
- [ ] Legacy job detail page (`/productivity/legacy-jobs/{id}`) renders

### 3.9 Profit Margin Analytics
- [ ] `/reports/profit-margin` loads
- [ ] Top / bottom lists correct
- [ ] Drill-down to orders
- [ ] CSV export
- [ ] Spot-verify one order manually

### 3.10 Financials Page
- [ ] `/financials` month/year revenue, expenses, profit
- [ ] Receipt entry with photo upload
- [ ] Invoice aging 0-30 / 31-60 / 61-90 / 90+
- [ ] Unpaid invoices summary links to Invoices page

---

## 🟢 TIER 4 — PEOPLE & PORTALS

### 4.1 Employees CRUD
- [ ] Create employee
- [ ] Assign PIN → PIN login works
- [ ] Set hourly + overtime rates
- [ ] Upload profile image
- [ ] Link employee to user account
- [ ] Deactivate removes from new-period payroll

### 4.2 Payroll
- [ ] Select employee + current period → worksheet loads
- [ ] **Carryover override**: pencil → set $0 → verify $5,015.65 gone (your original bug)
- [ ] Re-open: carryover stays $0
- [ ] Set override $500 → reflects
- [ ] Set override null → reverts to computed
- [ ] Manual time entry flows into totals
- [ ] Adjustments (bonus / deduction) roll up
- [ ] Period sign-off: employee + admin signatures
- [ ] Export payroll PDF matches UI totals
- [ ] CSV export imports cleanly

### 4.3 TimeClock (10pm→2pm bug fix)
- [ ] Clock IN → status Working
- [ ] Refresh → clock-in time shows in **New York local time**
- [ ] Start lunch → On Lunch
- [ ] End lunch → Working, lunch logged
- [ ] Clock OUT → total hours correct minus lunch
- [ ] Stale shift > 18h auto-closes
- [ ] Payroll worksheet shifts display in local time
- [ ] Editing a shift time round-trips local ↔ UTC

### 4.4 Customer Portal — Full Coverage
- [ ] Invite customer → email → password set → login
- [ ] Sees own quotes / orders / invoices only
- [ ] Download artwork / PDFs
- [ ] Sign approval
- [ ] Pay invoice via Stripe Connect
- [ ] Messaging: send → admin receives in Approvals inbox
- [ ] `/customer-portal/orders` list + detail
- [ ] `/customer-portal/quotes` approve / reject
- [ ] `/customer-portal/invoices` pay
- [ ] `/customer-portal/documents` downloads
- [ ] `/customer-portal/proofs` approve / request change
- [ ] `/customer-portal/messages` + threaded conversation
- [ ] `/customer-portal/forms` + fill new form
- [ ] `/customer-portal/pages` static tenant-configured content
- [ ] `/customer-portal/profile` customer edits info
- [ ] `/customer-portal/appointments` view / cancel / reschedule
- [ ] Portal password reset email works
- [ ] Portal shows MY brand, not SignGuy branding

### 4.5 Employee Portal — Full Coverage
- [ ] PIN login
- [ ] Clock IN / lunch / OUT from phone
- [ ] Dashboard: today's tasks, clock status
- [ ] `/employee-portal/jobs/:id` full detail + attachments
- [ ] `/employee-portal/tasks` all assigned tasks
- [ ] `/employee-portal/pay` pay preview
- [ ] `/employee-portal/profile` edit photo/PIN
- [ ] PIN recovery flow
- [ ] Manual time corrections queue for admin approval

---

## 🔶 TIER 5 — ADMIN / TEAM / SETTINGS

### 5.1 User Management
- [ ] Invite team member by email
- [ ] Invitee sets password, lands in tenant with correct role
- [ ] Change role (owner/admin/staff) — permissions update immediately
- [ ] Remove user — their created data remains
- [ ] Last owner cannot remove self (guardrail)

### 5.2 Admin Portal (Super Admin)
- [ ] `/admin-portal` visible only to super-admins
- [ ] Lists tenants, subs, credits
- [ ] Impersonate support (if available)
- [ ] `/admin/payments` configures platform Stripe keys

### 5.3 Onboarding Flow
- [ ] Fresh account → `/onboarding` checklist loads
- [ ] Items auto-mark done as you complete them
- [ ] Skip / complete buttons work
- [ ] Hides at 100%
- [ ] `/setup` public wizard works

### 5.4 Digest / Daily Email Settings
- [ ] `/settings/digest` daily / weekly toggle
- [ ] Time-of-day + TZ
- [ ] Content toggles (new orders / overdue / appts)
- [ ] Test digest arrives immediately
- [ ] Scheduled digest fires (check `apscheduler` log)

### 5.5 Pricing Plans / Founders Edition
- [ ] `/pricing` loads
- [ ] Select plan → Stripe checkout → subscription active
- [ ] Monthly vs Annual toggle correct
- [ ] Founders coupon auto-applies
- [ ] Upgrade mid-cycle prorates
- [ ] Downgrade takes effect at period end
- [ ] Trial countdown banner accurate
- [ ] Trial expired → `TrialLockout` screen locks tenant
- [ ] `UpgradeModal` triggers at feature limits

### 5.6 Tiers Configuration
- [ ] Feature matrix enforced per tier (Starter can't reach AI tools etc.)
- [ ] Locked features show upsell prompt

### 5.7 Promo Codes
- [ ] Create % discount code
- [ ] Create $ discount code
- [ ] Max redemptions enforced
- [ ] Expiry date enforced
- [ ] Plan restriction enforced
- [ ] Exhausted code rejected
- [ ] Redemption count increments

### 5.8 Community Hub
- [ ] `/community` posts + comments + likes
- [ ] Create post with image
- [ ] Comment / like / unlike
- [ ] Admin can moderate / delete

### 5.9 Materials Admin / Pricing Setup
- [ ] `/materials-admin` legacy list editable
- [ ] `/settings/pricing-setup` wizard loads
- [ ] `/pricing-settings` and `/pricing-foundation` both error-free

### 5.10 Pricing Foundation (edit propagates live)
- [ ] Digital Print: material cost change reflects in calculator
- [ ] Cut Vinyl: labor rate change
- [ ] Rigid Signs, Banners, Vehicle Wraps, Apparel, Services, Promotional: each one edited + verified
- [ ] Reset to defaults button works
- [ ] Change in one tab visible in other tab after refresh

### 5.11 Company Settings
- [ ] Company name / address / phone on quotes/invoices
- [ ] Logo on PDFs + emails
- [ ] Tax rate applies to new orders (old unchanged)
- [ ] Business hours shown on portal
- [ ] Timezone change updates TimeClock display

### 5.12 Email Templates
- [ ] Edit template → preview updates
- [ ] Send test → rendered email arrives

---

## 🟣 TIER 6 — AI & AUTOMATIONS

### 6.1 AI Tools
- [ ] `/ai-tools` lists every tool with credit cost
- [ ] Each "Try it" CTA works
- [ ] AI Email Composer drafts → Copy/Insert
- [ ] AI Image Generation (Nano Banana) → attaches to order
- [ ] AI Business Assistant multi-turn session persists
- [ ] AI Services Prefill (covered in 2.3g)
- [ ] Voice transcribe (Whisper) → text on order
- [ ] Historical invoice PDF extract

### 6.2 Floating Assistant
- [ ] Bubble in corner on every page
- [ ] Opens chat with page context
- [ ] Remembers conversation across page navigation

### 6.3 Emails / SendGrid
- [ ] Quote, invoice, approval, password reset all arrive < 60s
- [ ] Digest fires on schedule
- [ ] Renders correctly in Gmail, Outlook, Apple Mail, mobile Gmail
- [ ] From name = your company (`SENDGRID_FROM_NAME`)
- [ ] SPF / DKIM / DMARC set on sending domain
- [ ] Unsubscribe works for marketing emails

### 6.4 PDF / Document Generation
- [ ] Quote PDF: logo, totals, line items, tax
- [ ] Invoice PDF: + paid/unpaid watermark
- [ ] Payroll worksheet PDF: all shifts visible
- [ ] Order work ticket PDF: production-ready

---

## ⚫ TIER 7 — SIGNATURES & DRAWINGS

### 7.1 In-App Signature Capture
- [ ] `SignatureCaptureModal` tablet capture → saves to order
- [ ] `SignatureActivityList` lists all signatures with timestamps
- [ ] Clear / redo works mid-signature

### 7.2 Order Drawings (Whiteboard)
- [ ] `DrawingModal` — draw, text, color, thickness
- [ ] `DrawingCanvasPad` debounced save
- [ ] `DrawingPreviewModal` shows finished drawing
- [ ] Saved as PNG in Order Assets
- [ ] Editable after save (pad pre-loads)

---

## 🟤 TIER 8 — DOCS & MARKETING

### 8.1 Docs / Help Center
- [ ] `/docs/getting-started`
- [ ] `/docs/customers`
- [ ] `/docs/document-library`
- [ ] `/docs/quotes-jobs`
- [ ] `/docs/invoicing`
- [ ] `/docs/pricing-calculator`
- [ ] `/docs/ai-tools`
- [ ] `/docs/time-tracking`
- [ ] `/docs/employees`
- [ ] `/docs/webstores`
- [ ] `/docs/customer-portal`
- [ ] `/docs/financials`
- [ ] `/docs/productivity`
- [ ] `/docs/faq`
- [ ] ToC / search works across docs

### 8.2 Marketing / Public Pages
- [ ] `/` LandingPage + CTA
- [ ] `/features` all cards + screenshots
- [ ] `/pricing` plans link to signup
- [ ] `/about` `/contact` `/why-founder` load
- [ ] `/platform` `/webstores-overview` `/ai-studio` redirect to `/pricing-plans`
- [ ] `/terms` `/privacy` present, contact email accurate
- [ ] Contact form → admin email
- [ ] Mobile landing not broken
- [ ] Lighthouse load < 2.5s
- [ ] Favicon + OG image set

---

## 🟢 TIER 9 — SHELL / NAVIGATION / QUALITY

### 9.1 Main Layout & Ribbon
- [ ] Sidebar items correct per role
- [ ] Ribbon pin/unpin favorites
- [ ] QuickToolbar keyboard shortcuts (if any)
- [ ] ScrollToTop resets scroll on route change
- [ ] Breadcrumbs accurate

### 9.2 Trial / Upgrade UX
- [ ] `TrialLockout` screen locks expired trials (Billing link only)
- [ ] `UpgradeModal` at plan limits
- [ ] `UpgradePrompt` banner dismissible, reappears after 7 days
- [ ] Founders banner appears for founding members

### 9.3 Dashboard
- [ ] Widgets show today's revenue / pending / overdue
- [ ] Refresh on tab switch
- [ ] Click-through to source page
- [ ] Friendly empty states

### 9.4 Dev Panel
- [ ] Hidden from regular users in production

### 9.5 Mobile / Responsive
- [ ] Phone: login, dashboard, orders list/detail, add item — no horizontal scroll
- [ ] Tablet: same
- [ ] iPad Pro: same
- [ ] TimeClock one-hand usable on phone

### 9.6 Browsers
- [ ] Chrome latest
- [ ] Safari (Mac + iPhone)
- [ ] Firefox latest
- [ ] Edge latest

### 9.7 Error States
- [ ] `/orders/does-not-exist` → friendly not-found
- [ ] Random route → 404 with dashboard link
- [ ] Mid-save disconnect → toast "Connection lost, retry" (no data lost)
- [ ] Disabled button states clear

### 9.8 Accessibility
- [ ] Tab navigation through order form
- [ ] Screen-reader labels on interactive testid elements
- [ ] WCAG AA color contrast on key pages

### 9.9 Performance
- [ ] Dashboard < 2.5s on 4G throttle
- [ ] 500+ customer list paginates smoothly
- [ ] 500+ order list paginates smoothly
- [ ] 20MB PDF upload doesn't freeze UI

### 9.10 Security
- [ ] Backup contains only password hashes (no plaintext)
- [ ] JWT expiry enforced
- [ ] No secrets in client bundle (`curl /static/js/main.*.js | grep "sk_live"` empty)
- [ ] HTTPS only in production
- [ ] `Authorization` header required on all `/api/*`

### 9.11 Legal
- [ ] ToS page loads
- [ ] Privacy Policy loads
- [ ] Cookie banner (if EU traffic)
- [ ] Footer year correct

---

## 🔺 TIER 10 — REGRESSION / DATA INTEGRITY

### 10.1 Legacy Redirects
- [ ] `/jobs` → `/productivity` (or similar)
- [ ] `/jobs/:id` → legacy redirect
- [ ] `/workflow-templates` → `/settings/production`
- [ ] `/materials` → `/pricing-foundation`
- [ ] `/reports` → `/financials`
- [ ] `/pricing-calculator/settings` → `/pricing-foundation`

### 10.2 Terminology Consistency (Job → Order migration)
- [ ] No "Job Ticket", "Job Item", standalone "Job" in user-facing text
- [ ] Email templates updated
- [ ] PDFs (quote/invoice/worksheet) use "Order / Order Item"
- [ ] Docs pages updated
- [ ] Marketing pages updated

### 10.3 Full End-to-End Scenario
- [ ] Customer submits public **Questionnaire** (wrap + sign job)
- [ ] You create Quote from submission
- [ ] Customer approves quote via portal; signature captured via public link
- [ ] Quote → Order with 2 items (vehicle wrap + rigid sign)
- [ ] AI Prefill populates Services install line
- [ ] Upload artwork → customer approves via portal Proofs
- [ ] Production tasks auto-created from workflow template
- [ ] Employees clock time against the order
- [ ] Job moves across Production Board
- [ ] Invoice sent → customer pays via Stripe Connect
- [ ] Profit Margin Analytics reflects the revenue/margin correctly
- [ ] Tonight's digest email mentions the completed job
- [ ] If product published to webstore, storefront shows it correctly

### 10.4 Data Export / Migration
- [ ] Customers CSV export → re-import to fresh tenant matches
- [ ] Orders export (if endpoint exists)
- [ ] Payroll transactions export
- [ ] Webstore orders export

---

## ⚪ TIER 11 — OPERATIONAL READINESS

### 11.1 Health Checks
- [ ] `GET /api/` returns 200
- [ ] Backend startup ≠ hanging (deployment fix verified)
- [ ] `tail -n 100 /var/log/supervisor/backend.err.log` clean

### 11.2 Email Deliverability
- [ ] Low SendGrid bounce rate, zero spam complaints
- [ ] Tests land in INBOX for Gmail, Outlook, Yahoo, ProtonMail, iCloud
- [ ] SPF / DKIM / DMARC valid
- [ ] Unsubscribe link works

### 11.3 Monitoring & Alerts
- [ ] Error tracking (Sentry or equivalent) wired up
- [ ] Stripe webhook delivery monitored
- [ ] Backup failure triggers admin email

### 11.4 Rate Limiting / Abuse
- [ ] Rapid login attempts → temporary block
- [ ] Public questionnaire spam-protected
- [ ] File upload cap enforced (500MB rejected)

### 11.5 DNS / Domain
- [ ] Custom domain resolves
- [ ] SSL valid, no mixed-content
- [ ] `www` and apex both resolve consistently

---

## 📋 Launch-Day Execution Order

1. Back up everything (1.1)
2. Deploy fresh → verify health (11.1)
3. Smoke-test revenue loop: customer → quote → order → invoice → payment → payout
4. Spot-check one item from every tier header
5. Invite 3–5 beta users to run Tiers 2–4 over 48 hours
6. Monitor logs 24h post-launch
7. Work through Tiers 5–11 in week one

---

## 📝 Open Questions / Integrations To Verify
_If any of these are wired in your build, add their tests to the plan:_

- [ ] Telegram
- [ ] Twilio SMS
- [ ] Slack notifications
- [ ] Google Calendar sync
- [ ] Gmail integration
- [ ] Discord webhooks
- [ ] Barcode / QR scanning on production floor
- [ ] Print stylesheets for work tickets
- [ ] Dark mode on key pages
- [ ] PWA / offline mode

---

**Last updated:** {{fill in on launch day}}  
**Signed off by:** {{your name}}  
**Launched on:** {{date}}
