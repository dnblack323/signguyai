# SignGuy AI — Full Feature Map by Category
> Organized by complexity and wow factor within each category.
> Use this to decide what goes in each release stage.
>
> **Tiers within each section:**
> - 🟢 **Foundation** — table-stakes, expected, simple CRUD
> - 🟡 **Operational** — daily workflow features, moderate complexity
> - 🔴 **Power / Wow** — differentiating, high complexity, impressive to demo

---

## 1. DASHBOARD

### 🟢 Foundation
- KPI strip — today's revenue, active orders, open quotes, AR balance
- Quick action buttons (New Order, New Customer, New Invoice)
- Recent orders list (last 5–10)
- Welcome / shop name header

### 🟡 Operational
- 12-button command ribbon (Create / Customer / Workflow groups)
- Action Required card — proofs pending, approvals, overdue invoices, low stock
- Production Snapshot — jobs by stage, bottleneck count
- Billing Snapshot — outstanding AR, paid this week, overdue count
- Shop Health card — on-time rate, avg production days, conversion rate
- Team Today card — who's clocked in, shift status
- Guided Onboarding checklist (collapsible, disappears when complete)
- Single API digest call — all dashboard data in one request, no waterfall

### 🔴 Power / Wow
- AI-generated Suggestions / Nudges — "You have 3 quotes over 7 days old, consider following up"
- Staleness indicator — "Data may be stale" warning if digest is >10 min old
- Live unread message badge from Meta Messenger
- Urgency-sorted action items (blocked > overdue > due today)
- Low stock alert count from inventory ledger
- Inventory shortage count (jobs blocked by missing materials)

---

## 2. ORDERS & JOB MANAGEMENT

### 🟢 Foundation
- Create order (customer, due date, notes)
- Order list with search, filter by status
- Order status management (quote → confirmed → in production → ready → delivered)
- Order detail view
- Attach files to order
- Delete / cancel order
- Order number auto-generation (ORD-0001, tenant-scoped)

### 🟡 Operational
- Line items on each order (multiple products per order)
- Per-line-item dimensions, quantity, material, turnaround
- Job ticket auto-created from each line item
- Production task auto-created from each ticket
- Order source tracking (walk-in, phone, email, webstore, quote converted)
- Filter orders by source, date range, status, customer
- Webstore badge on bridged webstore orders
- Webstore filter — show only webstore orders, filter by specific store
- Bulk status update
- Deposit tracking (deposit amount vs balance due)

### 🔴 Power / Wow
- 4-layer hierarchy: Order → Line Items → Job Ticket → Production Tasks (all linked, all visible)
- Webstore orders automatically bridge into the main orders list (zero manual entry)
- Quote-to-order conversion (all line items + tickets created instantly)
- Order timeline / activity log (every state change recorded with who + when)
- Deep-link from dashboard action items directly into relevant order

---

## 3. JOB TICKETS (PRODUCTION UNIT)

### 🟢 Foundation
- Ticket list with status, priority, assignee, due date
- Ticket detail view
- Ticket status (not started / in progress / complete / blocked)
- Priority levels (low / normal / high / rush)
- Assign ticket to staff member
- Due date
- Production notes, special instructions, install notes, packaging notes

### 🟡 Operational
- Tabs: Overview · Artwork · Proofs · Materials · Notes · Activity
- Production stage (linked to kanban board)
- Multiple production tasks per ticket (Print, Cut, Laminate, Install)
- Task-level status, assignee, estimated time
- Artwork file uploads (AI, EPS, PDF, PNG)
- Activity log — every change recorded (who, what, when)
- Ticket number (TKT-0001, tenant-scoped)
- Link to order and customer
- Rework notes field

### 🔴 Power / Wow
- Materials tab — pull inventory requirements directly from the ticket
- Material requirement reservation (holds stock while ticket is open)
- Shortage detection — surfaces immediately when stock is insufficient
- Proof send / approval workflow directly from the ticket (see Proofs section)
- "Materials" button on production board cards deep-links to this tab
- Job ticket linked to Pricing Foundation — material cost pre-populated from configured rates
- Drawing mode — freehand annotation on artwork files

---

## 4. CUSTOMERS (CRM)

### 🟢 Foundation
- Create / edit / delete customer
- Customer list with search
- Customer detail (name, company, email, phone, address)
- Customer type (individual / business / nonprofit)
- Notes field
- Active / inactive toggle

### 🟡 Operational
- Billing and shipping address (separate)
- Tax exempt flag + tax ID
- Preferred contact method
- Tags (VIP, wholesale, net30, etc.)
- Customer detail tabs: Overview · Orders · Invoices · Quotes · Files · Activity
- Lifetime value — sum of all paid invoices (computed)
- Order history inline on customer
- Invoice history inline on customer
- Webstore buyer / webstore owner badges
- Filter customers by tag, type, active status

### 🔴 Power / Wow
- Webstore Connections card — shows which webstores they own and which they've bought from
- Auto-tagged when webstore checkout happens (webstore_customer or webstore_owner)
- Customer portal — self-service login to view orders, approve proofs, pay invoices, access their webstore
- Stripe customer ID linked at creation (enables saved payment methods)
- Communication log — every email sent, Meta message, proof interaction recorded on the customer

---

## 5. QUOTES

### 🟢 Foundation
- Create quote with line items
- Quote list with status filter
- Quote detail view
- Quote number (QUO-0001)
- Quote expiry date
- Notes / terms on quote

### 🟡 Operational
- Quote status flow (draft → sent → viewed → accepted → declined → expired → converted)
- Send quote via email (PDF or link)
- Customer view + accept/decline via email link (unauthenticated)
- Pricing snapshot — quote price locked at time of creation
- Follow-up tracking — "sent 7 days ago, no response"
- Convert accepted quote → order (all line items + tickets created instantly)
- Quote PDF export with branding

### 🔴 Power / Wow
- Pricing Calculator integration — build a quote from the calculator output
- AI-generated quote copy (professional description of work)
- Dashboard urgency — aging quotes surfaced in Customer Attention card
- Pricing snapshot freezes config — price won't change even if foundation rates are updated later

---

## 6. INVOICES & BILLING

### 🟢 Foundation
- Create invoice (manual or from order)
- Invoice list with status filter
- Invoice detail view
- Invoice number (INV-0001)
- Line items, subtotal, tax, total
- Invoice status (draft / sent / paid / overdue / void)
- PDF export
- Mark as paid (manual)

### 🟡 Operational
- Send invoice via email with payment link
- Customer pays via secure payment link (unauthenticated flow)
- Partial payments (multiple payments per invoice, tracked separately)
- Balance due always computed (total minus all payments)
- Tax rate configuration per invoice
- Overdue detection (scheduled daily check, emails reminder)
- Invoice branding (logo, accent color, footer, payment terms)
- Payment terms on invoice (Net 15, Net 30, Due on Receipt)
- Void / write off invoice
- Duplicate invoice

### 🔴 Power / Wow
- Stripe online payment — customer clicks link, pays with card
- Stripe payment intent linked to invoice — enables refunds
- Full payment history per invoice (who paid, how much, when)
- Branding live preview — see how invoice looks as you configure it
- Dashboard AR aging — overdue invoices surfaced immediately in dashboard
- Automated overdue email sequence

---

## 7. PRICING FOUNDATION & CALCULATOR

### 🟢 Foundation
- Pricing Foundation settings page (admin-only)
- Material cost entry per category
- Labor rate per hour
- Markup percentage
- Minimum price per category

### 🟡 Operational
- Six sign categories: Yard Signs · Rigid Signs · Digital Print · Cut Vinyl · Vehicle Graphics · Banners
- Per-category size presets (18×24, 24×36, etc.)
- Per-category materials list with cost per sqft
- Overhead percentage
- Waste percentage
- Setup fee per category
- Quantity break pricing (price drops at 10, 25, 50, 100 units)
- Pricing Calculator — live price calculation using Foundation config
- Calculator usable standalone (phone quote tool) or embedded in New Quote

### 🔴 Power / Wow
- Different formula per category:
  - Sqft-based for flat signs (width × height ÷ 144 × rates)
  - Roll-based for vinyl (linear feet consumed)
  - Per-vehicle-panel for wraps
- Cost breakdown shown to staff (material cost / labor / overhead / markup / final)
- Pricing linked to Inventory — material cost auto-updated when PO is received
- Pricing snapshot on quotes — prices frozen at time of quote creation
- Foundation config exports/imports for multiple shops (platform admin feature)

---

## 8. WEBSTORES

### 🟢 Foundation
- Create webstore (name, type, owner info)
- Three store types: B2B · Fundraiser · Creator
- Store list with status badges
- Basic storefront (product grid, cart, checkout)
- Product creation (name, price, variants, image)
- Store status management (pending / active / closed)

### 🟡 Operational
- 11-step guided setup flow (Store Created → Questionnaire → Branding → Products → Fulfillment → Stripe Onboarding → Preview → Owner Approval → Open)
- Setup questionnaire sent to store owner via email (one per store type)
- Staff review + "Apply Safe Answers" — questionnaire answers auto-populate store settings
- Branding tab (logo, banner, accent color)
- Custom domain support
- Shipping & handling fee configuration (bundle or separate)
- B2B: approved buyers list, spending limits, payment terms, order approval workflow
- Fundraiser: goal amount, deadline, profit split, progress bar
- Creator: commission percentage, Stripe Connect payout
- Webstore orders auto-bridge to main Orders list (zero manual entry)
- Filter orders by webstore in Orders page
- Store analytics (revenue, orders, avg order value, items sold, sales trend chart)
- Product categories with grouping on storefront
- Store snapshot (printable PDF with QR code and KPIs)

### 🔴 Power / Wow
- Stripe Connect marketplace — platform collects, distributes to store owner minus fee
- Owner Portal — store owner logs in to see their store progress, payouts, and financial summary
- Owner Stripe Express onboarding from inside the portal
- Fundraiser donations at checkout (preset amounts + custom, donor consent)
- Fundraiser supporters strip (public leaderboard, privacy-respecting)
- Share fundraiser button (Web Share API + clipboard fallback)
- Store lifecycle audit trail (every status change logged with timestamp)
- Admin preview mode — staff views store as it looks to customers before going live
- Coming Soon / Closed / Unavailable branded status screens (not 404s)
- Customer auto-tagged on checkout (webstore_buyer, webstore_owner)
- Customer ↔ Webstore connections view in CRM
- Per-store setup checklist (10-item, shows percent complete)
- Owner Portal financial transparency — gross sales, profit allocation, payout owed vs paid, formula explainer
- Webstores command ribbon (10-group Microsoft Office-style)

---

## 9. PRODUCTION BOARD

### 🟢 Foundation
- Kanban board view
- Production stages as columns
- Task cards with name, status, assignee
- Move task to next stage

### 🟡 Operational
- Tenant-configurable stages (key, label, color, order) — set in Settings
- Drag-and-drop between stages
- Task status (not started / in progress / paused / complete / blocked)
- Priority dot on each card (low / normal / high / rush)
- Assignee name on card
- Due date on card
- Start / Done / Pause quick-action buttons on card
- Ticket number and order reference on card
- Filter by assignee, priority
- Badge showing task count per column

### 🔴 Power / Wow
- Rollup view mode — all tasks for one job ticket collapsed into a single card
- Rollup progress indicator — "Step 2 of 4" on the collapsed card
- Drag advances the rollup ticket stage, not individual tasks
- "Materials" button on each card — deep-links to job ticket Materials tab
- Settings → Production stage editor — add/reorder/recolor stages without code
- Production snapshot on dashboard — stage counts, bottlenecks, at-risk jobs

---

## 10. ARTWORK & PROOFS

### 🟢 Foundation
- Upload artwork files to job ticket
- View uploaded files
- Download files
- Track artwork status (not received / received / approved)

### 🟡 Operational
- Proof PDF generation (combine artwork + order details into a proof document)
- Send proof to customer via email
- Customer approval link in email (no login required)
- Customer approves or requests revision
- Ticket status + activity log updated on response
- Shop notified when customer responds
- Proof version tracking (v1, v2, v3...)
- Proof status (draft / sent / approved / revision requested / expired)
- Proof expiry (auto-expires after X days)

### 🔴 Power / Wow
- Unauthenticated approval flow — customer clicks link, approves in browser, no account needed
- Revision request includes customer notes (customer types why they need changes)
- Dashboard "Proofs Pending" card — all outstanding approvals with urgency scoring
- Customer portal — customer views all their proofs in one place, approves from portal
- Drawing/annotation mode — freehand markup directly on the artwork file
- Digital signatures on job sign-off documents
- Proof history — view all previous versions of a proof side-by-side

---

## 11. INVENTORY & MATERIALS

### 🟢 Foundation
- Inventory item catalog (SKU, name, category, unit)
- Add/edit/deactivate items
- Tracking methods (quantity, roll, sheet, pack, remnant)
- Item list with search and filter by category
- On-hand quantity view

### 🟡 Operational
- Lot-based tracking — each physical batch has its own lot record
- Roll tracking (width + remaining length in inches)
- Sheet tracking (sheet dimensions + quantity)
- Opening balance entry
- Manual adjustment (add/remove stock with reason)
- Inventory transactions ledger — every change recorded (never edited)
- Balance calculation: on_hand / reserved / available / inventory_value
- Reorder point — triggers low-stock alert in dashboard
- Preferred stock level
- Vendor aliases per item (supplier SKU, nickname, pack quantity, last known cost)
- Cycle count — physical count reconciliation with automatic adjustment transaction
- Location management (bins, shelves, rooms)
- Transfer stock between locations

### 🔴 Power / Wow
- Material requirement system — job tickets create reservations against inventory lots
- Reservation model — stock reserved when requirement created, released when job complete
- Shortage detection — if available < required, creates a shortage record
- Shortage → PO flow — convert shortage to purchase order line item
- Remnant creation — when partial roll consumed, auto-create remnant lot with remaining dimensions
- `pricing_material_key` link — item's unit cost automatically flows into Pricing Foundation
- Inventory value tracking — total stock value computed from lots × unit costs
- Dashboard low-stock count from live ledger
- Dashboard inventory shortage count (jobs blocked)

---

## 12. PURCHASING (POs & VENDORS)

### 🟢 Foundation
- Vendor list (name, contact, website, account number)
- Create / edit / deactivate vendor
- Purchase order list
- PO number (PO-0001)
- Create PO (vendor, line items, expected delivery)
- PO status (draft / sent / received)

### 🟡 Operational
- PO line items (item, supplier SKU, quantity, unit cost)
- Send PO via email to vendor
- PO receipt — record what actually arrived (quantity, damage, backorder)
- Receipt auto-creates inventory lot + transaction
- Receipt updates PO line received quantity
- Partial receipt — some lines received, PO stays "partial"
- PO status auto-advances to "received" when all lines done
- Per-vendor item aliases (supplier SKUs stored on inventory item)

### 🔴 Power / Wow
- Shortage → PO conversion — add inventory shortage directly to a new PO line
- Shortage marked "resolved" when PO is received
- Receipt creates lot with full detail (cost, dimensions, location)
- Unit cost from received PO flows back to pricing suggestions
- Vendor history — all POs for a vendor in one view

---

## 13. TEAM & HR

### 🟢 Foundation
- Staff list (name, role, email, phone)
- Add / edit / deactivate staff
- Role assignment (owner / admin / staff)
- Employee ID (EMP-001)

### 🟡 Operational
- Department assignment
- Hourly rate / salary flag
- Hire date
- Permission system — granular 60+ permissions per role
- Custom role permissions (assign specific permissions beyond the role defaults)
- Staff visible in assignment dropdowns (job tickets, tasks)
- Active / inactive toggle (soft delete, history preserved)

### 🔴 Power / Wow
- Payroll-ready fields — hourly rate stored as a snapshot in payroll runs (rate changes don't alter history)
- Staff performance — tickets completed, on-time rate, hours logged
- Employee portal — staff clock in/out, view assigned tickets, view their payslips

---

## 14. TIMECLOCK

### 🟢 Foundation
- Clock in / clock out
- Today's shift status per employee
- Total hours for a shift
- View timeclock log

### 🟡 Operational
- Break tracking (break start / end)
- Break minutes deducted from total hours
- Edit a timeclock entry (manager override)
- Filter by employee, date range
- Daily / weekly hours totals
- Currently clocked-in view (dashboard)

### 🔴 Power / Wow
- Append-only log — entries are never edited, corrections are new records with `edited_by` flag
- Overtime detection — hours over 40/week flagged automatically
- Dashboard "Team Today" card — who's clocked in right now, shift duration
- Payroll integration — timeclock entries are the source of truth for payroll calculation
- Shift anomaly detection — missed punch-out, unusually long shift

---

## 15. PAYROLL

### 🟢 Foundation
- Pay period configuration (weekly / biweekly / semi-monthly)
- Payroll run list
- Create payroll run for a period

### 🟡 Operational
- Auto-calculate from timeclock entries for the period
- Regular hours vs overtime hours (1.5×)
- Per-employee gross pay line item
- Rate snapshot — hourly rate at time of run is frozen (future rate changes don't alter history)
- Draft → finalize workflow
- Payroll summary (total payroll cost, headcount)
- Export payroll run to CSV / PDF

### 🔴 Power / Wow
- Payroll run is immutable once finalized — no edits, only a new corrective run
- Historical payroll browsable per employee across all runs
- Deductions support (health insurance, garnishments)
- Payroll integration readiness (export in format compatible with QuickBooks / Gusto)

---

## 16. AI TOOLS

### 🟢 Foundation
- Document Composer — long-form document generation from a prompt
- Business Copywriter — marketing copy for the shop
- AI tool list / catalogue page

### 🟡 Operational
- Blog Creator — full blog post from topic + keywords
- Email Template Creator — professional email drafts
- Job Post Creator — hiring announcement from job title
- Social Media Creator — platform-specific post variants (Facebook, Instagram, LinkedIn)
- All tools save output to a Documents library
- Documents tagged by tool, searchable, browsable
- Document download (PDF or DOCX)
- Document preview in app
- AI credit balance shown in UI

### 🔴 Power / Wow
- Credit system — each generation deducts credits, balance tracked per tenant
- Automatic credit balance check before each call (fail fast with clear error)
- Document linked to order / customer / quote (attach AI doc to any entity)
- Streaming responses — text appears as it's generated, not after a long wait
- "Generate from order" — AI writes a proof cover letter or job description auto-populated from order data
- Branding-aware templates — AI tools use shop name, tone, and industry context

---

## 17. COMMUNICATIONS & MESSAGING

### 🟢 Foundation
- Send email manually from order / customer
- Email log on customer record
- Transactional emails (proof ready, invoice sent, order confirmed)

### 🟡 Operational
- 8+ email templates (proof ready, invoice sent/overdue, payment received, order confirmed/ready, quote sent/accepted)
- Per-template on/off toggle in settings
- Branded email wrapper (logo, header color, from name, signature)
- Email log on both customer AND order
- Meta Messenger inbox — view and reply to Facebook messages
- Conversation list with unread badge
- Link conversation to customer record

### 🔴 Power / Wow
- Unread count drives dashboard badge and digest API count
- Messaging from inside the app — reply to Meta Messenger without leaving SignGuy AI
- Customer matched to conversation by email/phone automatically
- Real-time unread count on dashboard ("3 unread messages")
- Automatic proof-ready email triggered on proof creation
- Automatic overdue reminder sequence (daily check, escalating emails)
- SendGrid bounce / delivery status tracking

---

## 18. REPORTS & ANALYTICS

### 🟢 Foundation
- Revenue this month / last month
- Order count by status
- Invoice aging summary
- Top customers by revenue

### 🟡 Operational
- Daily / weekly / monthly revenue chart (trend line)
- Pipeline value (confirmed orders not yet invoiced)
- Outstanding AR by age bucket (current, 30, 60, 90+ days)
- Quote conversion rate (accepted / total sent)
- Average order value
- Top products / categories by order frequency
- New customers vs returning customers
- Production: average days from order to delivery
- On-time delivery rate

### 🔴 Power / Wow
- Cross-period comparison (this month vs same period last year)
- Per-staff productivity (tickets completed, on-time rate, hours billed)
- Webstore analytics per store (revenue, orders, avg order, items sold, top products, donor totals for fundraisers)
- Sales by day chart on webstore dashboard
- Platform admin cross-tenant analytics (total ARR, new signups, churn, MAU per feature)
- Nightly aggregation job — pre-computed snapshots for fast dashboard loading
- Timezone-aware date ranges (tenant's local timezone, not UTC)

---

## 19. SETTINGS

### 🟢 Foundation
- Shop name, address, phone, email, website
- Timezone
- Shop logo upload
- Default tax rate

### 🟡 Operational
- Production stage editor — add, reorder, recolor kanban stages
- Pricing Foundation — material costs, labor rates, markup, waste per category
- Invoice settings (prefix, due days, payment terms, default notes)
- Notification toggles (which email triggers are on/off)
- Stripe Connect — connect shop's Stripe account
- SendGrid API key setup
- Meta / Facebook app configuration
- Pay period configuration (weekly / biweekly / semi-monthly)
- Overtime rules (configurable threshold and multiplier)

### 🔴 Power / Wow
- Branding & Templates — configure invoice appearance, email wrapper, document header/footer
- Branding live preview — side-by-side invoice / email / document previews update in real-time as you type
- Data backup — export full tenant data as JSON
- Data restore — import backup (with rollback on failure)
- Feature flags — enable/disable specific modules per tenant
- Tier gating — features locked by plan, upgrade prompts

---

## 20. PLATFORM ADMIN (SaaS Layer)

### 🟢 Foundation
- All tenants list (shop name, plan, status, created date)
- Tenant detail view
- Total tenant count, ARR overview
- Onboarding checklist per tenant

### 🟡 Operational
- Search / filter tenants
- Tenant user list (all users under a tenant)
- Feature flag toggles per tenant
- Impersonate tenant — "Act as this shop" without logging out
- Delete test tenant (cascades all associated data)
- Platform admin role for support staff (separate from platform_creator)

### 🔴 Power / Wow
- Cross-tenant analytics — revenue, signups, churn, MAU, feature usage
- 8-tab analytics dashboard (overview, activity chart, users, routes, sessions, referrers, errors, suspicious activity)
- Lightweight event tracker — automatic page views, global error capture, session tracking
- Suspicious activity detection — failed logins, unusual patterns
- Per-tenant usage metrics — which features they've used, last active date
- Platform creator role secured by environment variable (cannot be granted via UI — only tied to a specific email at startup)
- Impersonation request logging (audit trail of who impersonated what)

---

## 21. CUSTOMER PORTAL

### 🟢 Foundation
- Customer login (separate from shop staff login)
- View their orders
- View their invoices
- Basic profile

### 🟡 Operational
- Pay invoice online (Stripe payment link, no login required OR portal payment)
- View proof sent for approval
- Approve or request revision on proof
- View appointments / installs
- Download invoice PDFs
- View their quote and accept/decline

### 🔴 Power / Wow
- Webstore owner view — see their store progress, financial summary, payout history
- Stripe Express onboarding from inside the portal (no separate redirect needed)
- Per-store setup checklist with actionable items
- Financial transparency card (gross sales / profit allocation / net pending — formula shown)
- Notification system — one-time assignment notification when portal user is assigned a webstore
- Dismiss notifications
- Deep-link from email → portal to specific order or proof

---

## 22. AUTH & SECURITY

### 🟢 Foundation
- Email + password login
- JWT auth
- Protected routes (redirect to login if not authenticated)
- Logout

### 🟡 Operational
- Role-based access (owner / admin / staff)
- Granular permissions (60+) per role
- Password reset via email (secure token flow, 60-min expiry)
- Single-use reset token (burned on use)
- Email enumeration protection (generic response on forgot-password)

### 🔴 Power / Wow
- platform_creator role — secured by env var at startup, cannot be granted via UI
- Impersonation — platform admin acts as any tenant
- Tenant isolation enforced on every query (tenant_id compound index everywhere)
- Backup restore with rollback — if restore fails midway, original data is restored atomically
- CORS configured correctly for credentials + wildcard origin handling
- Setup admin endpoint gated by ENABLE_SETUP_ADMIN env flag (off by default)
- Rate limiting on auth endpoints
- Suspicious login detection in platform analytics

---

## FEATURE COUNT SUMMARY

| Category | Foundation | Operational | Power/Wow | Total |
|---|---|---|---|---|
| Dashboard | 4 | 8 | 7 | 19 |
| Orders | 7 | 10 | 4 | 21 |
| Job Tickets | 7 | 9 | 6 | 22 |
| Customers | 6 | 10 | 5 | 21 |
| Quotes | 5 | 7 | 4 | 16 |
| Invoices | 8 | 11 | 6 | 25 |
| Pricing | 4 | 10 | 5 | 19 |
| Webstores | 6 | 13 | 14 | 33 |
| Production Board | 4 | 10 | 6 | 20 |
| Artwork & Proofs | 4 | 9 | 7 | 20 |
| Inventory | 5 | 13 | 9 | 27 |
| Purchasing | 6 | 8 | 5 | 19 |
| Team & HR | 4 | 7 | 3 | 14 |
| Timeclock | 4 | 7 | 5 | 16 |
| Payroll | 3 | 7 | 4 | 14 |
| AI Tools | 2 | 9 | 6 | 17 |
| Communications | 3 | 8 | 7 | 18 |
| Reports | 4 | 9 | 7 | 20 |
| Settings | 4 | 9 | 6 | 19 |
| Platform Admin | 4 | 6 | 7 | 17 |
| Customer Portal | 4 | 7 | 7 | 18 |
| Auth & Security | 4 | 5 | 8 | 17 |
| **TOTAL** | **112** | **195** | **152** | **459** |

---

*Generated: 2026-06-10 | SignGuy AI Full Feature Map*
*Use alongside REBUILD_SPEC.md for the full rebuild brief*
