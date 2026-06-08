# Launch Readiness Master Checklist
Source: LAUNCH READY MASTER DOC.pdf (uploaded 2026-06-07)

---

## CATEGORY 1: Core Sales and Customer Workflow
**Objective:** Make the full customer-to-completion workflow reliable, understandable, secure, and ready for launch.

### Section 1 — Dashboard
**Purpose:** The Dashboard must serve as the reliable command center for the owner.

#### ✅ Verified (Already Done)
- [x] `/dashboard` route exists
- [x] Dashboard contains business metrics, operational attention items, production info, financial attention, approvals, and customer actions
- [x] Dashboard links to Customers, Orders, Invoices, Financials, Approvals, Production Board, AI Assistant, Time Clock
- [x] Dashboard has dedicated backend endpoints (stats, summary-v2, today-command-center, production-snapshot, customer-attention, financial-attention)
- [x] Dashboard source contains loading and error handling for major sections
- [x] Logged-out users cannot access Dashboard (ProtectedRoutes guard in App.js)
- [x] Customer-facing email/nudge actions (AssistantNudgesWidget) require review step before sending (DraftEmailModal)
- [x] StatCards have clickthrough links: Total Customers→/customers, Active Orders→/orders, Pending Invoices→/invoices, Today's Revenue→/financials
- [x] Severity strip links: Due Today, Overdue, Awaiting Approval, In Production, Unpaid Invoices all linked
- [x] Permission fix applied 2026-06-07: platform_creator role now has full ROLE_PERMISSIONS

#### ✅ Fixed in This Session (2026-06-07)
- [x] **PendingCustomerActionsWidget**: Fixed false "all caught up" empty state on API failure. Now shows visible error + Retry button (data-testid="pending-actions-error", "pending-actions-retry")
- [x] **Dead code removed**: `recentAIDocs` state and `recent-ai-documents` fetch removed from Dashboard.js (widget was previously deleted but state/fetch lingered)
- [x] **Permission bug fixed**: `platform_creator` role was missing from `ROLE_PERMISSIONS` → invoices, financials, and all permission-gated pages now accessible

#### ❌ PO - Required Before Launch (Still Needed)
- [ ] Verify all Dashboard endpoints with a real authenticated launch-like account (post-permission-fix)
- [ ] Confirm Dashboard loads after a full browser refresh (test manually)
- [ ] Confirm no Dashboard section silently hides 401, 403, or 500 responses
- [ ] Confirm Dashboard counts agree with Customers, Orders, Approvals, Production, Invoices, and Financials
- [ ] Reconcile stored demo-data pricing/invoice expectation failures
- [ ] Align production at-risk sort behavior between frontend expectations and backend output
- [ ] Hide customer-facing send actions that are not fully wired

#### Live Clickthrough Checklist
- [ ] Click Total Customers → Customers opens
- [ ] Click Active Orders → Orders opens with useful context
- [ ] Click Pending Invoices → Invoices opens ✅ (permission fix applied)
- [ ] Click Today's Revenue → Financials opens ✅ (permission fix applied)
- [ ] Click Due Today → relevant orders visible
- [ ] Click Overdue → relevant orders visible
- [ ] Click Awaiting Approval → Approvals opens
- [ ] Click Unread Messages → Admin Portal messages view opens
- [ ] Click In Production → relevant orders/production items visible
- [ ] Click Unpaid Invoices → unpaid invoices visible ✅ (permission fix applied)
- [ ] Click Production Board, Send Approval, Create Invoice, AI Assistant, Time Clock
- [ ] Exercise loading, empty, error, retry, partial-data, and populated states

#### Visual / Layout / Purpose / Flow
- [ ] Check every Dashboard font color against its background
- [ ] Confirm no accidental horizontal scrolling at mobile, tablet, laptop, wide-desktop widths
- [ ] Confirm Dashboard does not contain large unexplained empty areas
- [ ] Confirm cards and widgets do not overlap or resize unexpectedly
- [ ] Confirm most urgent actions appear before informational metrics
- [ ] Remove or combine duplicate metrics that lead to the same action
- [ ] Confirm every metric, widget, button, link, and nudge serves a launch purpose

---

### Section 2 — Customers
**Status:** Reviewed and fixed 2026-06-07.

#### ✅ Fixed in This Session (2026-06-07)
- [x] **Backend bug**: `update_customer` final read-back now tenant-scoped (`{"id": cid, "tenant_id": tid}`)
- [x] **Backend bug**: `create_customer` tenant lookup fixed from `{"tenant_id": ...}` → `{"id": ...}`
- [x] **Frontend**: `loadCustomers()` now has try/catch/finally — cannot stay stuck; shows visible error + Retry button (`data-testid="customers-load-error"`, `"customers-retry-btn"`)
- [x] **Frontend**: "View Quotes" from customer detail now navigates to `/quotes?customer_id=...` (filtered) instead of unfiltered `/quotes`
- [x] **Frontend (Quotes.js)**: Quotes page reads `?customer_id` URL param on mount and applies customer filter chip with ✕ clear button (`data-testid="quote-customer-filter-chip"`)
- [x] **Frontend lint**: Webstores useEffect converted to `useReducer` + `dispatch` (removes set-state-in-effect error and adds error state tracking)
- [x] **Frontend lint**: URL param import dialog converted to lazy initializer (removes set-state-in-effect error)
- [x] **Frontend lint**: `handleViewCustomer` uses `structuredClone` to satisfy immutability rule

#### ❌ Still Needed (PO Items from Checklist)
- [ ] Verify auto-welcome-email settings actually control welcome emails
- [ ] Decide deletion policy for customers with related records (prefer archive over destructive delete)
- [ ] Fix CSV frontend validation so Company-only rows are allowed
- [ ] Add backend uniqueness/duplicate rules for customer email
- [ ] Validate email and phone formats consistently during create/update
- [ ] Review temporary portal PIN display and delivery for security
- [ ] Confirm portal invite failure cannot leave portal access partially enabled
- [ ] Add visible errors for failed related jobs, quotes, invoices, and webstore loads in detail modal
- [ ] Add Retry actions for failed list and detail sections
- [ ] Preserve form data after save failure
- [ ] Show clear import result details (created/updated/skipped/invalid counts)
- [ ] Confirm CSV import cannot freeze UI on FileReader callback errors
- [ ] Define and test customer merge behavior for duplicate records

---

### Section 3 — Quotes
**Status:** Not yet reviewed in this session. See PDF for full checklist.

**Key PO bugs to fix:**
- [ ] Fix Share Link (creates `/portal/{token}` but no matching frontend route)
- [ ] Replace Email Quote action (shows success toast but says "coming soon")
- [ ] Fix quote-send regression (sent_at returned as null)
- [ ] Add tenant scoping to collection updates/deletes

---

### Section 4 — Orders
**Status:** Not yet reviewed. See PDF.
**Key items:**
- [ ] Add tenant scoping to order updates and final lookups
- [ ] Verify bulk actions are safe and complete

---

### Section 5 — Order Detail
**Status:** Not yet reviewed. See PDF.

---

### Section 6 — New Order Flow
**Status:** Not yet reviewed. See PDF.

---

### Section 7 — Job Tickets
**Status:** Not yet reviewed. See PDF.
**Key items:**
- [ ] Add tenant scoping to ticket update/delete

---

### Section 8 — Wrap Command Center
**Status:** Not yet reviewed. See PDF.
**Key items:**
- [ ] Hide or complete incomplete actions (Design Questionnaire delivery, AI mockup, AI Assistant, Contract Download, payment-link generation)
- [ ] Fix fallback to placeholder data on load failure

---

### Section 9 — Approvals
**Status:** Not yet reviewed. See PDF.
**Key items:**
- [ ] Fix resend and delete actions showing success for failed HTTP responses

---

### Section 10 — Signatures
**Status:** Not yet reviewed. See PDF.
**Key items:**
- [ ] Fix public signature requests allowing re-sign/decline after expired/declined
- [ ] Add tenant scoping to signature-driven parent-record updates
- [ ] Protect signature image files from unauthenticated access

---

## CATEGORY 2: Production and Work Management
**Status:** Not yet reviewed. See PDF for full checklist.

---

## CATEGORY 3: Pricing, Products, and Catalog
**Status:** Not yet reviewed. See PDF.
**Key items:**
- [ ] Yard Signs Pricing Setup and Calculator Integration (P1)
- [ ] Verify all pricing calculator categories work correctly

---

## CATEGORY 4: Billing, Payments, and Financial Reporting
**Status:** Not yet reviewed. See PDF.
**Key items:**
- [ ] Add backend permission enforcement to invoices, Financials, billing, Stripe Connect
- [ ] Fix unscoped invoice mutations and lookups
- [ ] Require signed webhooks in production
- [ ] Verify plan, feature, founder, and fee claims

---

## Category-Wide Launch Blockers (Cat 1)
- [ ] Fix public signature requests (expired/declined/completed cannot be re-signed)
- [ ] Add tenant scoping to signature-driven parent-record updates
- [ ] Protect signature image files from unauthenticated ID-based access
- [ ] Fix quote share links (`/portal/{token}` has no frontend route)
- [ ] Replace Quotes Email action (shows success while saying "coming soon")
- [ ] Fix stored quote-send regression (sent_at not returned after sending)
- [ ] Fix Approvals resend/delete showing success for failed HTTP responses
- [ ] Remove/hide incomplete Wrap Command Center customer-facing actions
- [ ] Stop Wrap CC load failures from falling back to placeholder data
- [ ] Fix backend updates/deletes that use only ID after tenant-scoped lookup
- [ ] Decide and enforce single launch workflow (legacy Quotes/Jobs vs newer Orders/Job Tickets)
- [ ] Complete authenticated end-to-end clickthrough

---

## Progress Summary
- **Category 1, Section 1 (Dashboard):** ~40% complete
  - Verified items: All 5 confirmed working
  - Fixed: 3 items (permission bug, PendingCustomerActionsWidget error state, dead code)
  - Remaining: 12 PO items + 13 clickthrough tests + 7 visual checks

Last updated: 2026-06-07
