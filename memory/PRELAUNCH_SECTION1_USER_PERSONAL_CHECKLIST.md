# Prelaunch — User Personal Checklist (Section 1 + Personal-Only Tier 2)

This file contains only the Section 1 items that require **your personal verification** (email inbox, Stripe dashboard actions, long-duration checks, or clean-tenant/live-production actions).

Numbering format is preserved as requested: `Tier.SectionLetter` (example: `1.1A`, `1.1B`).

---

## Tier 1 → Section 1.1 Backup & Restore

- [ ] **1.1D** On a clean test tenant, upload backup and verify **Preview Restore** shows row counts without writing
- [ ] **1.1E** On test tenant, click **Restore** and confirm completion toast
- [ ] **1.1F** Log out/in after restore and confirm all expected data is visible
- [ ] **1.1G** Refresh Orders page and confirm all orders render
- [ ] **1.1H** Open restored order and verify artwork/drawing previews still resolve
- [ ] **1.1L** Take a live production backup before wider launch testing

## Tier 1 → Section 1.2 Authentication & Multi-Tenant Isolation

- [ ] **1.2A** Sign up with a brand-new email and confirm verification email arrives within 60s
- [ ] **1.2B** Open verification link and confirm account activation
- [ ] **1.2E** Forgot Password email arrives, reset link works, and reset completes
- [ ] **1.2F** Old password is rejected and new password is accepted after reset
- [ ] **1.2H** Create a second tenant with different email
- [ ] **1.2I** Tenant B `GET /api/customers` returns empty array (not Tenant A data)
- [ ] **1.2J** Tenant B direct fetch of Tenant A order returns 403/404 (never data)
- [ ] **1.2K** Staff cannot access `/payroll`, `/settings`, `/billing`, `/users`
- [ ] **1.2L** Staff can access `/orders`, `/customers`, `/dashboard`
- [ ] **1.2M** JWT/session expiry check after 25+ hours idle
- [ ] **1.2N** Email-change flow requires new-email verification

## Tier 1 → Section 1.3 Stripe Billing (Platform Subscriptions)

- [ ] **1.3A** Billing UI shows current plan and renewal date correctly
- [ ] **1.3B** Upgrade with Stripe checkout and verify success path
- [ ] **1.3C** Declined card path shows graceful error and no plan upgrade
- [ ] **1.3D** 3DS-required card flow completes and upgrades plan after approval
- [ ] **1.3E** Credit top-up purchase updates navbar balance after webhook
- [ ] **1.3F** Cancel at period end is correctly reflected in Stripe and app access behavior
- [ ] **1.3G** Webhook replay from Stripe dashboard is processed correctly
- [ ] **1.3H** Promo code/coupon applies correctly in checkout
- [ ] **1.3I** Stripe invoice PDF download matches charged amount

## Tier 1 → Section 1.4 Stripe Connect (Merchant Payouts)

- [ ] **1.4A** Complete Stripe Connect onboarding from Payment Settings
- [ ] **1.4B** Confirm status has `connected=true`, `charges_enabled=true`, `payouts_enabled=true`
- [ ] **1.4C** Stripe Express dashboard link opens and works
- [ ] **1.4D** Customer payment routes to connected merchant balance
- [ ] **1.4E** Stripe Connect balance reflects payment minus fees
- [ ] **1.4F** Stripe dashboard refund syncs invoice to `refunded` in SignGuy
- [ ] **1.4G** Disconnect path works and fallback payment behavior is correct
- [ ] **1.4H** Reconnect works cleanly without duplicate-account errors

## Tier 1 → Section 1.5 Credits System

- [ ] **1.5A** Navbar visibly shows current credit balance in your normal UI usage
- [ ] **1.5B** Buy 100/300/1000 packs and confirm webhook-driven balance updates
- [ ] **1.5D** Drive balance to 0 and verify HTTP 402 + friendly UI upgrade prompt
- [ ] **1.5E** Auto top-up triggers when below threshold
- [ ] **1.5G** Founders monthly allotment refills on billing anniversary
- [ ] **1.5H** Free-tier users cannot bypass credit gating in network flow

## Tier 1 → Section 1.6 CSV Customer Import

- [ ] **1.6R** Export customers CSV, re-import into a clean tenant, and confirm round-trip integrity (no duplicates/data loss)

---

### 2.3g Services (agent can test pricing math; these require AI credits or Stripe)
- [ ] **2.3g-AI** AI Prefill — click ✨ Sparkles → paste "Install 4 aluminum signs 15 miles away, needs a scissor lift" → verify fields populate and badge shows "AI"
- [ ] **2.3g-CreditGate** Burn credits to 0 → try AI Prefill → verify HTTP 402 + friendly upgrade prompt appears

### 2.4 Order Item Duplicate / Variant / Copy
- [ ] **2.4-CarryArtwork** Duplicate with Artwork carry-over = OFF → new item has no file links
- [ ] **2.4-CarryNotes** Duplicate with Production Notes = OFF → note fields cleared
- [ ] **2.4-CarryDueDate** Duplicate with Due Date = OFF → due date reset to null

### 2.5 Quote → Order → Invoice → Payment
- [ ] **2.5C** Quote email **arrives in inbox** (check spam too)
- [ ] **2.5-QuotePDF** Quote PDF download — **not yet implemented** in backend; endpoint `GET /api/quotes/{id}/pdf` returns 404. This needs to be built before launch if you want customers to download quotes directly.
- [ ] **2.5I** Invoice email arrives with **PDF attachment** and a pay link
- [ ] **2.5J** Customer clicks pay link → Stripe checkout → pays with test card `4242 4242 4242 4242` → invoice marked **paid** → order status updates
- [ ] **2.5K** Partial payment: customer pays less than full → invoice shows remaining balance
- [ ] **2.5L** Second payment closes invoice → status = paid
- [ ] **2.5M** **Refund** via Stripe dashboard → invoice auto-updates to `refunded`

### 2.7 Webstores
- [ ] **2.7N** Checkout with Stripe test card → confirmation email delivered to inbox
- [ ] **2.7R** Payouts page shows Stripe Connect payout history (requires live Stripe payout data)

### 2.9 Questionnaires
- [ ] **2.9L** Admin email notification fires on new submission (verify in SendGrid logs or inbox)

### 2.10 Customer Signature Page
- [ ] **2.10E** Signature with **finger on real mobile device** → submit → stored correctly

---

## Section 3 — Marketing / Landing Pages (manual browser check)

- [ ] **3.1** `/why-founder`, `/about`, `/contact`, `/terms`, `/privacy` all load without errors
- [ ] **3.2** `/contact` form submits → email arrives at admin inbox
- [ ] **3.3** Missing redirects: `/platform`, `/ai-studio`, `/starter`, `/pro`, `/business`, `/pricing-plans-old`, `/ai-basic`, `/ai-pro`, `/ai-max` → all redirect to `/pricing-plans`
- [ ] **3.4** Mobile landing at **375px** — no broken layout, no horizontal scroll
- [ ] **3.5** **Lighthouse** on landing page → Performance > 85, Accessibility > 90 (run in Chrome DevTools → Lighthouse)
- [ ] **3.6** **Favicon** appears in browser tab
- [ ] **3.7** **Open Graph image** — paste URL into [opengraph.xyz](https://www.opengraph.xyz) or Slack → card preview renders with image
- [ ] **3.8** View page source on each public page → `<meta name="description">` present and unique per page
- [ ] **3.9** `robots.txt` (`/robots.txt`) and `sitemap.xml` (`/sitemap.xml`) serve correctly

---

## Section 5 — Email Delivery (all require your inbox)

- [ ] **5.1** **Quote email** arrives
- [ ] **5.2** **Invoice email** arrives with PDF attachment
- [ ] **5.3** **Approval request email** arrives with portal link
- [ ] **5.4** **Password reset email** arrives within 60s
- [ ] **5.5** **Welcome email** fires on new user signup
- [ ] **5.6** **Digest email** fires at your configured time (verify `tail -n 200 /var/log/supervisor/backend.err.log` shows `check_and_send_digests executed successfully`)
- [ ] **5.7** Send a test email to each: **Gmail, Outlook, Yahoo, ProtonMail, iCloud, Fastmail** → ALL land in inbox, not spam
- [ ] **5.8** From address shows your company name (`SENDGRID_FROM_NAME`), NOT generic "SignGuy"
- [ ] **5.9** Reply-to goes to your business inbox
- [ ] **5.10** **Unsubscribe link** on marketing emails works and persists in SendGrid suppressions

---

## Section 6 — PDFs (physical print verification)

- [ ] **6.1** Quote PDF: logo, customer info, line items, tax line, totals, terms, expiration date all look correct
- [ ] **6.2** Invoice PDF: same as quote + PAID/UNPAID watermark, invoice number, due date, remit-to address
- [ ] **6.3** Payroll worksheet PDF: all shifts, hours totals, pay totals, signatures
- [ ] **6.4** Order work ticket PDF: materials, specs, artwork thumbnails, due date, assigned employee
- [ ] **6.5** Print a PDF on **physical paper** → page breaks sensible, nothing cut off
- [ ] **6.6** Non-ASCII names in PDF render correctly (no `??` or tofu squares)

---

## Section 7 — Mobile & Responsive (real device required)

Test each on **iPhone** (Safari) and **Android** (Chrome):
- [ ] **7.1** Login page
- [ ] **7.2** Dashboard
- [ ] **7.3** Orders list
- [ ] **7.4** Order detail page
- [ ] **7.5** TimeClock (`/timeclock`) — buttons big enough to tap with thumb
- [ ] **7.6** Customer portal
- [ ] **7.7** Employee portal
- [ ] **7.8** Public storefront checkout
- [ ] **7.9** No horizontal scroll on any of the above
- [ ] **7.10** Modals readable, close button reachable
- [ ] **7.11** Bottom-sheet / sticky actions don't cover important content

---

## Section 8 — Browser Compatibility (test on real browsers)

- [ ] **8.1** Chrome latest (Mac)
- [ ] **8.2** Chrome latest (Windows)
- [ ] **8.3** Chrome latest (Android)
- [ ] **8.4** Safari latest (Mac)
- [ ] **8.5** Safari latest (iPhone)
- [ ] **8.6** Safari latest (iPad)
- [ ] **8.7** Firefox latest
- [ ] **8.8** Edge latest
- [ ] **8.9** No console errors in any of the above (open DevTools → Console tab)

---

## Section 9 — Error Handling & Accessibility (manual)

- [ ] **9.1** Kill internet mid-save → toast "Connection lost — retry" (no data lost)
- [ ] **9.2** Slow network (throttle to 3G in DevTools) → loading states visible, no blank screens
- [ ] **9.3** 500 server error on form submit → user-friendly message, option to retry
- [ ] **9.4** **WCAG AA color contrast** on key pages (install [axe DevTools](https://chrome.google.com/webstore/detail/axe-devtools/lhdoppojpmngadmnindnejefpokejbdd) → run audit)
- [ ] **9.5** Tab key navigates through the Order form in logical order
- [ ] **9.6** Screen-reader labels present on icon-only buttons (inspect: `aria-label` on Edit pencil, Delete icon, etc.)
- [ ] **9.7** Modal **focus trap** — Tab doesn't escape the modal
- [ ] **9.8** Escape key closes modals
- [ ] **9.9** Can complete a full order creation using **only keyboard** (no mouse)
- [ ] **9.10** Injection test: enter `'; DROP TABLE orders;` and `{"$ne": null}` as a customer name → safely saved as plain text
- [ ] **9.11** XSS test: enter `<script>alert(1)</script>` as a note → renders as plain text, no alert fires

---

## Section 10 — Performance (real Lighthouse run)

- [ ] **10.1** Lighthouse on Dashboard → Performance > 85 (Chrome DevTools → Lighthouse)
- [ ] **10.2** Large customer list (500+) → paginates without lag
- [ ] **10.3** Large order list (500+) → paginates without lag
- [ ] **10.4** Upload a 20MB PDF → UI doesn't freeze
- [ ] **10.5** Leave the tab open for 1 hour → RAM stays stable (no memory leak; watch Task Manager)

---

## Section 11 — Security (production environment)

- [ ] **11.1** **HTTPS only** — production URL redirects HTTP → HTTPS
- [ ] **11.2** **HSTS header** present (`Strict-Transport-Security`) — check with `curl -I https://yourdomain.com`
- [ ] **11.3** **CORS** — no wildcard `*` on production (verify with `curl -H "Origin: https://evil.com" -I https://yourdomain.com/api/customers`)
- [ ] **11.4** Rate-limit auth endpoint: `for i in {1..10}; do curl -s -o /dev/null -w "%{http_code}\n" -X POST https://yourdomain.com/api/auth/login -d '{"email":"x","password":"y"}'; done` → eventually returns 429
- [ ] **11.5** File upload size cap: try uploading a 500MB file → rejected with clear error, not a 500

---

## Section 12 — Legal & Compliance

- [ ] **12.1** **Cookie banner** (if serving EU users) appears on first visit, accept/decline works, choice stored
- [ ] **12.2** **GDPR data export** — user can download their own data (`/account/export` or similar)
- [ ] **12.3** **GDPR data deletion** — user can delete their account + data
- [ ] **12.4** Footer has **correct year** (2026)
- [ ] **12.5** Terms of Service and Privacy Policy are current and accurate

---

## Section 13 — DNS & Domain (production)

- [ ] **13.1** Both `yourdomain.com` and `www.yourdomain.com` resolve and redirect consistently (pick canonical)
- [ ] **13.2** SSL certificate valid → **no mixed-content warnings** in browser console
- [ ] **13.3** Email MX records set correctly (`dig MX yourdomain.com`)
- [ ] **13.4** **SPF** valid (`dig TXT yourdomain.com` should show `v=spf1`)
- [ ] **13.5** **DKIM** enabled in SendGrid and published in DNS
- [ ] **13.6** **DMARC** policy at least `p=none` with `rua=` address (`dig TXT _dmarc.yourdomain.com`)
- [ ] **13.7** Certificate auto-renewal configured (Let's Encrypt or similar)

---

## Section 14 — Monitoring & Ops (production)

- [ ] **14.1** **Sentry** (or equivalent) — generate a test error → verify it appears in Sentry dashboard
- [ ] **14.2** **Stripe webhook monitoring** — check Stripe Dashboard → Developers → Webhooks → 0 failed deliveries
- [ ] **14.3** **Uptime monitoring** — set up StatusCake / UptimeRobot / Pingdom → pings every minute → alert if down > 5 min
- [ ] **14.4** Backup job failures trigger email to admin
- [ ] **14.5** SendGrid dashboard: bounce rate < 2%, zero spam complaints

---

## Section 4.5 — E2E Golden Path (requires email + Stripe)

- [ ] **E2E-1** Customer submits a public Questionnaire → appears in dashboard
- [ ] **E2E-2** Create Quote from submission → customer receives quote email
- [ ] **E2E-3** Customer logs into portal → approves quote → signature captured
- [ ] **E2E-4** Convert approved quote → Order (all line items carry over)
- [ ] **E2E-5** Generate invoice → email customer → customer pays via Stripe Connect test card
- [ ] **E2E-6** Invoice marked paid → order closed
- [ ] **E2E-7** Profit Margin Analytics reflects correct revenue + margin
- [ ] **E2E-8** Tonight's digest email mentions the completed job
- [ ] **E2E-9** Payroll worksheet shows employee time clocked against the order
- [ ] **E2E-10** Customer sees completed order + invoice in their portal

---

## Section 15 — Iteration 132 Mop-Up Manual Verifications (added 2026-04-26)

These items had backend endpoints implemented + verified, but UI / round-trip checks remain personal:

- [ ] **15.1 Customer CSV round-trip** — Hit `/api/customers/export` (or UI download), open CSV in Excel/Numbers, then re-import via Customers → Import on a clean tenant. Confirm zero duplicates, all rows present, special chars (é, ñ, &) survive UTF-8 roundtrip.
- [ ] **15.2 Payroll CSV in spreadsheet** — Download `/api/payroll/report?format=csv&start_date=...&end_date=...`, open in Excel/Numbers/Google Sheets. Confirm columns align, decimals preserved (e.g. `25.00` not `25`), no broken cells.
- [ ] **15.3 Portal appointments UI** — Customer logs into `/customer-portal/appointments`, sees scheduled appointments. Confirm cancel button works, reschedule (if implemented in UI) propagates back to admin schedule.
- [ ] **15.4 Employee portal dashboard UI** — Employee logs into `/employee-portal`, sees today's hours / week's hours / assigned jobs count. Confirm clock-in/out badges + tappable buttons render on mobile.
- [ ] **15.5 Workflow template apply UX** — From an order, click "Apply Workflow Template" → select template → confirm tasks appear in production Kanban under the order.
- [ ] **15.6 Staff-role UI guards** — Login as staff user (e.g. `staff_payroll_test@test.com / StaffTest123!`); confirm Payroll/Settings/Billing/Users nav links are hidden or guarded with friendly toast (not raw 403).
- [ ] **15.7 Tenant isolation UI walkthrough** — Login as Tenant B user, attempt URL manipulation to reach Tenant A's `/orders/<id>` → confirm friendly 404 page (not raw API JSON).
