# Category 4: Billing, Payments, And Financial Reporting
**Objective:** Ensure every money movement, subscription action, financial record, and billing surface is authorized, tenant-isolated, accurate, idempotent, and visually trustworthy before launch.

**Sections:** Invoices · Payments · Billing Management · Subscription Plans And Checkout · Billing Success And Cancellation · Financials · Daily Sales And Expenses · Profit And Margin Analytics · Reports · Webstore Payouts · Stripe Connect And Payment Settings

---

## Category Readiness Summary
**Status:** Strong financial backend and Stripe integration foundation, but **not launch-approved** until authorization, tenant isolation, invoice mutation safety, Financials contract fixes, webhook security, and full Stripe test-mode matrix are completed.

---

## Category-Wide Confirmed Launch Blockers

- [ ] Add backend permission enforcement to invoices, Financials, billing changes, and Stripe Connect management; authenticated tenant users can currently reach sensitive connect/disconnect/dashboard/reconcile actions without explicit financial/admin checks.
- [ ] Fix multiple invoice mutations that verify tenant ownership and then update or delete using unscoped filters.
- [ ] Fix invoice customer and quote lookups that omit tenant scope.
- [ ] Fix invoice payment-history query so it verifies invoice ownership and scopes payments by tenant.
- [ ] Validate manual payment amounts and prevent zero, negative, or overpayments unless explicitly supported.
- [ ] Fix Financials frontend/backend summary contract: frontend reads `total_tax` and `net_income`; backend returns neither `total_tax` nor `net_income` and instead returns `net_profit`.
- [ ] Fix duplicate JSX `className` attributes on Financials and Invoices access-denied headings.
- [ ] Persist expense receipt uploads or remove the visible receipt controls.
- [ ] Require signed Stripe webhooks in production; both billing and Stripe Connect webhooks currently allow unsigned fallback parsing when secrets are absent.
- [ ] Make webhook failures return an error status so Stripe retries instead of receiving a successful HTTP response containing an error payload.
- [ ] Fix or clarify the Founder Billing return flow because founder checkout returns to `/billing?checkout=...`, while Billing Management does not process those query parameters.
- [ ] Verify all plan/feature/fee claims against current launch-visible product behavior.
- [ ] Complete real Stripe test-mode clickthroughs before enabling live payments.

## Money-System Boundaries

- [ ] Document customer invoice payments as money paid to the sign shop.
- [ ] Document app subscription billing as money paid by the tenant to SignGuyAI.
- [ ] Document webstore checkout as customer money split between shop/platform/store-owner responsibilities.
- [ ] Document webstore-owner payouts separately from Stripe payouts to the tenant's bank.
- [ ] Confirm users cannot confuse subscription invoices with customer invoices.
- [ ] Confirm Financials reports do not mix gross Stripe transaction values, platform fees, taxes, payouts, and manual entries incorrectly.
- [ ] Confirm every amount has an authoritative source and reconciliation path.

---

## Section 1 — Invoices

### Verified Structure And Behavior
- [x] Route `/invoices` exists.
- [x] Frontend checks invoice view and create permissions. ✅ *(platform_creator permission fix applied 2026-06-07)*
- [x] Backend supports invoice create, list, detail, update, and delete.
- [x] Backend supports invoice creation from a job.
- [x] Backend supports canonical invoices and legacy invoice records.
- [x] Backend supports marking an invoice sent.
- [x] Backend supports sending invoices to the customer portal.
- [x] Backend supports manual payment recording.
- [x] Backend supports invoice payment history.
- [x] Backend supports invoice PDF generation.
- [x] Frontend supports search and status filtering.
- [x] Frontend supports invoice preview and payment-link creation.
- [x] Stored invoice reconciliation report shows 11 passing tests.
- [x] Stored payment-link report shows 11 passing tests.

### PO Authorization And Tenant-Isolation Fixes
- [ ] Enforce `INVOICES_VIEW` on invoice list, detail, PDF, and payment-history endpoints.
- [ ] Enforce invoice create/manage permissions on create, update, delete, send, send-to-portal, and record-payment endpoints.
- [ ] Add `tenant_id` when linking a newly created invoice to a job.
- [ ] Add `tenant_id` when unlinking a deleted invoice from a job.
- [ ] Add `tenant_id` to invoice delete filters.
- [ ] Add `tenant_id` to quote lookup during invoice-from-job fallback.
- [ ] Add `tenant_id` when updating a job with invoice ID after invoice-from-job creation.
- [ ] Add tenant-aware activity logging where job activity is created from invoice actions.
- [ ] Add `tenant_id` to the send-invoice update filter.
- [ ] Add `tenant_id` to customer lookup when sending an invoice to the portal.
- [ ] Update the correct canonical or legacy invoice collection when sending to portal.
- [ ] Add `tenant_id` to send-to-portal update filters.
- [ ] Add `tenant_id` to manual-payment invoice update filters.
- [ ] Verify invoice ownership before returning payment history.
- [ ] Scope invoice payment-history records by `tenant_id`.
- [ ] Add tests proving one tenant cannot read, update, send, delete, pay, or list payments for another tenant's invoice.
- [ ] Add tests proving employees without invoice permissions cannot mutate invoices through direct API calls.

### PO Payment And Total Integrity
- [ ] Reject manual payment amounts less than or equal to zero.
- [ ] Decide whether manual overpayments are allowed.
- [ ] If overpayments are not allowed, reject amounts above remaining balance.
- [ ] If overpayments are allowed, track unapplied credit explicitly.
- [ ] Prevent a paid invoice from accepting another manual payment unless intentionally reopening it.
- [ ] Make manual payment recording and invoice balance update atomic.
- [ ] Add a unique/idempotency reference for manual payments.
- [ ] Confirm partial payments set `partial` status instead of leaving an unrelated status.
- [ ] Confirm full payment sets paid date and paid status consistently.
- [ ] Confirm invoice update recalculates subtotal, tax, grand total, balance due, and paid status correctly.
- [ ] Confirm invoice update cannot reduce total below amount already paid without a defined refund/credit process.
- [ ] Use `grand_total` consistently where tax is part of amount owed.
- [ ] Confirm line-item quantities and prices reject invalid negative values.

### Invoice Lifecycle
- [ ] Define allowed status transitions: draft → sent → partial → paid/overdue/void.
- [ ] Prevent invalid backwards transitions or require an audit reason.
- [ ] Decide whether deleting sent or paid invoices is allowed.
- [ ] Prefer voiding paid/sent invoices when accounting history must remain intact.
- [ ] Add audit records for create, edit, send, portal-send, payment, void, and delete.
- [ ] Confirm a job cannot accidentally receive multiple active invoices unless intended.
- [ ] Confirm cloned invoices have unique IDs/numbers and correct metadata.
- [ ] Fix the stored iteration 129 quote/invoice-related failure or prove it cannot affect invoice launch behavior.

### Invoice PDF And Portal Delivery
- [ ] Verify tenant company name, address, phone, branding, and tax details.
- [ ] Verify invoice number, date, due date, customer, items, subtotal, tax, total, paid status, notes, and terms.
- [ ] Verify long descriptions wrap without clipping.
- [ ] Verify multi-page invoices repeat readable table headers.
- [ ] Verify invoices with no line items display a useful summary instead of an empty broken table.
- [ ] Verify paid, partial, overdue, and void states render correctly.
- [ ] Verify portal-send works for both canonical and legacy invoices.
- [ ] Verify portal notification links to the correct route.
- [ ] Verify customers cannot see invoices from another customer or tenant.

### Live Clickthrough
- [ ] Open `/invoices` with authorized and unauthorized users.
- [ ] Create a manual invoice.
- [ ] Create an invoice from a job.
- [ ] Edit customer, job, items, totals, tax, notes, and due date.
- [ ] Search and filter every status.
- [ ] Preview the invoice.
- [ ] Download the PDF.
- [ ] Send the invoice.
- [ ] Send the invoice to the portal.
- [ ] Record a partial manual payment.
- [ ] Record a final manual payment.
- [ ] Attempt invalid, negative, duplicate, and overpayment values.
- [ ] Delete or void test invoices according to the selected policy.
- [ ] Click every button, link, modal action, filter, and empty-state action.

### Visual And Responsive QA
- [ ] Remove duplicate JSX `className` attribute from the access-denied heading.
- [ ] Confirm status badge colors have sufficient contrast.
- [ ] Confirm green, yellow, and red totals are readable on white backgrounds.
- [ ] Confirm tables use intentional internal scrolling on narrow screens.
- [ ] Confirm action buttons remain visible and tappable.
- [ ] Confirm invoice modal forms fit mobile screens.
- [ ] Confirm no page-level horizontal scrolling, overlap, black screen, dead link, or large unexplained empty space.

---

## Section 2 — Payments

### Verified Structure And Behavior
- [x] Manual invoice payments are recorded with zero platform fee.
- [x] Stripe invoice payment sessions create transaction-ledger records.
- [x] Stripe invoice checkout calculates platform fees.
- [x] Stripe payment status can reconcile invoice status.
- [x] Payment reconciliation is tenant scoped in its transaction query.
- [x] Customer portal invoice payment behavior has stored test coverage.
- [x] Failed, expired, pending, and paid Stripe transactions can appear in the tenant operations dashboard.

### PO Payment Safety
- [ ] Require appropriate backend permissions for creating payment links, viewing payment operations, reconciliation, and manual payments.
- [ ] Confirm every Stripe payment transaction has a unique session ID and cannot be applied twice.
- [ ] Confirm payment-status polling and webhook processing are idempotent when both arrive.
- [ ] Confirm invoice payment cannot mark another tenant's invoice paid.
- [ ] Confirm amount and currency from Stripe match the intended invoice transaction before marking paid.
- [ ] Confirm platform fee amounts use authoritative backend tier configuration.
- [ ] Confirm payment transaction status names are consistent across billing and Stripe Connect systems.
- [ ] Confirm duplicate callbacks do not duplicate paid amount, payment records, fees, or notifications.
- [ ] Confirm cancelled and expired checkout sessions never mark invoices paid.
- [ ] Confirm refunds, disputes, reversals, and chargebacks have a defined internal effect.
- [ ] Confirm failed payment information is visible without exposing sensitive Stripe data.

### Payment Methods And Reconciliation
- [ ] Define supported manual payment methods.
- [ ] Confirm cash/check/external payments remain fee-free.
- [ ] Confirm card payments processed outside SignGuyAI are recorded as manual/external, not Stripe-processed.
- [ ] Reconcile Stripe ledger totals against invoice paid totals.
- [ ] Reconcile manual payment totals against invoice paid totals.
- [ ] Add missing-payment and mismatched-amount alerts.
- [ ] Add a safe process to correct or reverse an incorrectly recorded manual payment.
- [ ] Confirm payment records cannot be deleted without audit history.
- [ ] Confirm Financials does not double count invoice payments and manually entered daily sales.

### Live Clickthrough
- [ ] Generate an invoice Stripe payment link.
- [ ] Copy and open the payment link.
- [ ] Send the payment link by email.
- [ ] Verify fallback messaging when email is unavailable.
- [ ] Complete a Stripe test payment.
- [ ] Cancel a Stripe test payment.
- [ ] Let a Stripe test checkout expire.
- [ ] Simulate failed payment and dispute events.
- [ ] Confirm invoice, payment ledger, tenant dashboard, and customer portal all agree.
- [ ] Confirm every payment action works and no flow ends in a dead or blank screen.

---

## Section 3 — Billing Management

### Verified Structure And Behavior
- [x] Route `/billing` exists.
- [x] Billing Management redirects unauthenticated users to login.
- [x] Billing Management loads founder-plan data.
- [x] Billing Management loads tenant payment history.
- [x] Billing Management can start monthly and annual founder checkout.
- [x] Billing Management can start credit-pack purchase checkout.
- [x] Billing Management can open Stripe customer portal.
- [x] Current plan, fee, founder spot, tenant status, credit balance, credit packs, and payment history data are displayed.

### Must Fix Or Decide
- [ ] Restrict billing-management actions to owner/admin or an approved billing role.
- [ ] Confirm employees cannot subscribe, purchase credits, or open the tenant's Stripe billing portal.
- [ ] Add a persistent visible error state when plan data fails to load; current page can return blank when `planData` is absent.
- [ ] Show a visible payment-history load error instead of silently swallowing it.
- [ ] Process `/billing?checkout=success`, `/billing?checkout=cancel`, `/billing?credits=success`, and `/billing?credits=cancel`.
- [ ] Confirm returned checkout session status before showing purchase success.
- [ ] Refresh plan, credits, and payment history after successful checkout.
- [ ] Confirm loading state cannot become stuck after navigation errors.
- [ ] Confirm Manage in Stripe opens the correct customer portal for the current tenant.
- [ ] Confirm cancellation, upgrade, downgrade, payment-method update, and invoice-history behaviors.

### Claims And Pricing Accuracy
- [ ] Verify displayed monthly and annual prices against Stripe price configuration.
- [ ] Verify founder discount and lifetime-lock claims.
- [ ] Verify founder spot count and sold-out behavior.
- [ ] Verify AI-credit allowance and credit-pack prices.
- [ ] Verify processing-fee claims against backend fee configuration.
- [ ] Verify "Full Shop Management" claim against launch-visible modules.
- [ ] Verify "All AI Tools" and voice claim; remove claims for incomplete or hidden features.
- [ ] Verify unlimited Webstores claim against current entitlements.
- [ ] Verify customer/employee portal, payroll, and support claims.
- [ ] Confirm Billing Management and public Pricing pages show consistent prices and plan claims.

### Live Clickthrough And Visual QA
- [ ] Open Billing Management as owner/admin and unauthorized employee.
- [ ] Start monthly checkout and cancel.
- [ ] Start annual checkout and cancel.
- [ ] Complete a Stripe test subscription.
- [ ] Purchase each credit-pack type in test mode.
- [ ] Cancel each checkout.
- [ ] Test failed card.
- [ ] Test recurring payment success.
- [ ] Test recurring payment failure.
- [ ] Test subscription cancellation.
- [ ] Test upgrade and downgrade.
- [ ] Test customer portal payment-method update.
- [ ] Confirm each event produces correct transaction, subscription, tenant, and entitlement records.

---

## Section 4 — Subscription Plans And Checkout

### Verified Structure And Behavior
- [x] Legacy and multi-product checkout endpoints exist.
- [x] Multi-product checkout supports OS, Webstores, and AI Studio plan types.
- [x] Subscription status endpoints exist.
- [x] Payment history endpoint is tenant scoped.
- [x] Checkout status endpoint exists.
- [x] Stripe customer portal endpoint exists.
- [x] Founder checkout and credit-pack checkout endpoints exist.
- [x] Stored multi-product billing report shows 39 passing tests.
- [x] Stored billing feature and founder billing reports show 47 passing tests.

### PO Checkout And Subscription Safety
- [ ] Require owner/admin billing permission for tenant subscription changes.
- [ ] Require configured Stripe API keys and price IDs in production.
- [ ] Require signed billing webhook verification in production.
- [ ] Remove unsigned webhook fallback from production execution.
- [ ] Make webhook event processing idempotent by Stripe event ID.
- [ ] Record every processed webhook event and outcome.
- [ ] Return non-2xx on processing failure so Stripe retries.
- [ ] Confirm checkout-status fallback cannot activate another tenant's subscription.
- [ ] Confirm session metadata, transaction tenant, Stripe customer, and subscription all match before activation.
- [ ] Confirm a tenant cannot hold conflicting active subscriptions unless the product model intentionally permits it.
- [ ] Confirm failed recurring payment changes entitlements correctly.
- [ ] Confirm cancellation and subscription deletion change entitlements correctly.
- [ ] Confirm upgrade/downgrade proration and timing.
- [ ] Confirm payment retries and past-due grace period.
- [ ] Confirm one-time credit purchases are idempotent and credited exactly once.

### Plan And Entitlement Contract
- [ ] Define the authoritative plan catalog.
- [ ] Remove or redirect old checkout paths that are no longer sold.
- [ ] Confirm public Pricing, Founder Pricing, Billing Management, backend plan config, and Stripe price IDs agree.
- [ ] Confirm each plan grants exactly the displayed features.
- [ ] Confirm hidden/incomplete features are not advertised as plan benefits.
- [ ] Confirm processing fees by plan and transaction type.
- [ ] Confirm trial duration, expiration, lockout, and conversion behavior.
- [ ] Confirm founder pricing eligibility and spot limits cannot be bypassed.
- [ ] Confirm promo-code behavior is consistent with Category 3 fixes.
- [ ] Confirm subscription cancellation does not destroy tenant data unexpectedly.

### Live Stripe Test Matrix
- [ ] Complete new monthly subscription checkout.
- [ ] Complete new annual subscription checkout where allowed.
- [ ] Complete founder checkout.
- [ ] Complete each multi-product plan checkout intended for launch.
- [ ] Complete credit-pack purchase.
- [ ] Cancel each checkout.
- [ ] Test failed card.
- [ ] Test recurring payment success.
- [ ] Test recurring payment failure.
- [ ] Test subscription cancellation.
- [ ] Test upgrade and downgrade.
- [ ] Test customer portal payment-method update.
- [ ] Confirm each event produces correct transaction, subscription, tenant, and entitlement records.

---

## Section 5 — Billing Success And Cancellation

### Verified Structure And Behavior
- [x] Routes `/billing/success` and `/billing/cancel` exist.
- [x] Billing Success polls checkout status and refreshes tier data after paid status.
- [x] Billing Success has checking, success, and error states.
- [x] Billing Cancel provides routes back to pricing and dashboard.
- [x] General billing checkout uses the dedicated success and cancel routes.

### Must Fix Or Decide
- [ ] Decide whether Founder Billing and credit purchases should use the dedicated success/cancel pages.
- [ ] If Founder Billing returns to `/billing`, add query-parameter handling there.
- [ ] If dedicated pages are authoritative, update founder and credit checkout URLs.
- [ ] Ensure success page messaging matches the purchased product; it currently always welcomes a Founder.
- [ ] Ensure success page does not claim full access for a credit-pack-only purchase.
- [ ] Replace or remove malformed emoji/encoding text.
- [ ] Confirm error state provides a real support route.
- [ ] Confirm retry route points to the currently sold pricing page.
- [ ] Confirm cancellation page does not guarantee no charge when payment state is uncertain.
- [ ] Clear or safely preserve checkout query parameters after processing.
- [ ] Confirm refresh/revisit behavior does not duplicate activation.

### Live Clickthrough And Visual QA
- [ ] Open success route without session ID.
- [ ] Open success route with invalid session ID.
- [ ] Open success route with pending, paid, expired, and cancelled sessions.
- [ ] Complete subscription and credit-pack return flows.
- [ ] Open cancel route from each checkout type.
- [ ] Verify every button route.
- [ ] Confirm desktop/mobile contrast, layout, and no horizontal scrolling.
- [ ] Confirm no blank, black, misleading, or product-inaccurate state.

---

## Section 6 — Financials

### Verified Structure And Behavior
- [x] Route `/financials` exists.
- [x] Frontend checks financial view and create permissions. ✅ *(platform_creator permission fix applied 2026-06-07)*
- [x] Frontend loads sales, expenses, and summary by date range.
- [x] Backend supports sales list/create, expense list/create, summary, and invoice aging.
- [x] Financial records are stored with tenant IDs.
- [x] Sales and expense list queries are tenant scoped.

### PO Contract And Authorization Fixes
- [ ] Enforce `FINANCIALS_VIEW` on backend sales, expense, summary, and aging reads.
- [ ] Enforce `FINANCIALS_CREATE` or manage permission on sales and expense creates.
- [ ] Validate financial request payloads with typed models instead of unvalidated request JSON.
- [ ] Reject zero, negative, NaN, infinite, malformed, or excessively large amounts.
- [ ] Validate date, payment method, expense category, tax amount, vendor, and description.
- [ ] Fix backend summary to return `total_tax` if the UI displays it.
- [ ] Fix frontend/backend naming to use one of `net_profit` or `net_income`.
- [ ] Add a contract test asserting every rendered summary field exists.
- [ ] Remove duplicate JSX `className` attribute from access-denied heading.
- [ ] Add a visible persistent load-error state.
- [ ] Confirm date ranges reject start dates after end dates.

### Accounting And Reporting Decisions
- [ ] Define whether Daily Sales represents deposits, invoice payments, or all revenue.
- [ ] Prevent invoice/Stripe revenue from being double counted as manual Daily Sales.
- [ ] Track sales tax separately from revenue.
- [ ] Decide whether platform fees and Stripe processing fees appear as expenses.
- [ ] Define cash versus accrual reporting expectations.
- [ ] Define treatment for refunds, chargebacks, discounts, tips/donations, and owner payouts.
- [ ] Confirm currency and rounding behavior.
- [ ] Confirm Financials is operational reporting, not represented as formal accounting software unless supported.
- [ ] Add correction/void workflows with audit trails for incorrect entries.

### Live Clickthrough
- [ ] Open Financials with authorized and unauthorized users.
- [ ] Create sales entry for each payment method.
- [ ] Create expense entry for each launch category.
- [ ] Attempt invalid values and dates.
- [ ] Change date range.
- [ ] Verify total sales, tax, expenses, and net profit.
- [ ] Compare totals against source entries.
- [ ] Confirm empty, loading, error, and permission-denied states.
- [ ] Click every visible action and tab.

### Visual And Responsive QA
- [ ] Confirm header text remains readable in every theme.
- [ ] Confirm summary values never show blank, `$NaN`, or misleading zero.
- [ ] Confirm date controls wrap cleanly.
- [ ] Confirm tables fit desktop, tablet, and mobile.
- [ ] Confirm green, amber, red, and violet values have sufficient contrast.
- [ ] Confirm no horizontal page scrolling, overlap, dead link, black screen, or large empty area.

---

## Section 7 — Daily Sales And Expenses

### Verified Structure And Behavior
- [x] Daily sales supports date, amount, tax, payment method, and description.
- [x] Expense entry supports date, amount, category, description, vendor backend field, and visible receipt selector.
- [x] Sales and expense records include creator and created-at metadata.
- [x] Date-range filtering exists.

### PO Receipt And Entry Integrity
- [ ] Persist receipt images through a secure upload endpoint or remove receipt buttons.
- [ ] Add receipt file type, size, malware, access, and retention rules.
- [ ] Confirm receipt access is tenant scoped.
- [ ] Add vendor field to UI if backend/reporting needs it.
- [ ] Add edit, void, or correction flow for sales entries.
- [ ] Add edit, void, or correction flow for expense entries.
- [ ] Record audit metadata for corrections.
- [ ] Prevent duplicate submission from repeated clicks.
- [ ] Confirm taxes cannot exceed gross sales without explicit warning.
- [ ] Confirm payment method and categories use consistent controlled values.

### Daily Entry Accuracy Scenarios
- [ ] Enter cash sales with tax.
- [ ] Enter card sales with tax.
- [ ] Enter check sales without tax.
- [ ] Enter other-method sales.
- [ ] Enter material, labor, rent, utility, tax, vehicle, and other expenses.
- [ ] Verify date-range inclusion boundaries.
- [ ] Verify totals after corrections/voids.
- [ ] Verify entries from another tenant never appear.
- [ ] Compare entry totals to Financials summary.

### Visual And Flow QA
- [ ] Confirm sales and expense dialogs fit mobile screens.
- [ ] Confirm receipt selection does not imply successful persistence when none exists.
- [ ] Confirm payment method buttons are readable and keyboard accessible.
- [ ] Confirm category names fit without clipping.
- [ ] Confirm workflow is enter → review → record → verify summary.

---

## Section 8 — Profit And Margin Analytics

### Verified Structure And Behavior
- [x] Route `/reports/profit-margin` exists.
- [x] Frontend and backend enforce financial-view or owner/admin access.
- [x] Dashboard supports date ranges and category filtering.
- [x] Dashboard derives revenue, cost, profit, margin, customer, category, trend, and low-margin data.
- [x] Dashboard preferences are tenant scoped.
- [x] Widget order, visibility, and simple mode exist.
- [x] CSV, XLSX, and PDF exports exist.
- [x] Stored `profit_analytics_results.xml` shows 23 passing tests.

### Accuracy And Data-Source Verification
- [ ] Document the source of revenue for each job row.
- [ ] Document the source of costs and which cost snapshot fields are included.
- [ ] Confirm labor, materials, overhead, subcontracting, fees, refunds, and discounts are included correctly.
- [ ] Confirm jobs without cost snapshots are flagged instead of treated as zero-cost profit.
- [ ] Confirm partially paid and unpaid invoices do not incorrectly count as collected revenue if the report claims cash profit.
- [ ] Confirm cancelled, voided, refunded, and test jobs are excluded or labeled.
- [ ] Confirm benchmark-margin and underpriced thresholds are configurable and understandable.
- [ ] Verify aggregate totals equal the sum of underlying rows.
- [ ] Verify customer and category totals equal job totals.
- [ ] Verify date boundaries and time zones.
- [ ] Verify exports exactly match filtered dashboard data.
- [ ] Add regression fixtures with known revenue, cost, profit, and margin.

### Live Clickthrough
- [ ] Open with authorized and unauthorized users.
- [ ] Test every date range.
- [ ] Test custom dates.
- [ ] Test every category filter.
- [ ] Toggle simple mode.
- [ ] Enable, disable, and reorder every widget.
- [ ] Save and reload preferences.
- [ ] Export CSV, XLSX, and PDF.
- [ ] Open each exported file and verify values.
- [ ] Verify low-margin jobs against source orders.
- [ ] Click every button and control.

### Visual And Responsive QA
- [ ] Confirm charts remain meaningful with negative and zero profit.
- [ ] Confirm bars and trends do not overflow.
- [ ] Confirm low-margin text and badges have sufficient contrast.
- [ ] Confirm long job/customer/category names fit.
- [ ] Confirm tables have intentional responsive behavior.
- [ ] Confirm no horizontal page scrolling, overlap, blank state, or large empty space.

---

## Section 9 — Reports

### Verified Structure And Behavior
- [x] Route `/reports` redirects to `/financials`.
- [x] Profit And Margin Analytics has its own report route.
- [x] Navigation includes Financials and Reports entry points.
- [x] Report exports exist for Profit And Margin Analytics.

### Purpose And Duplication Audit
- [ ] Decide whether Reports should remain a separate navigation group.
- [ ] Decide whether `/reports` should open a report hub instead of redirecting to Financials.
- [ ] Remove duplicate Profit, Revenue, Costs, Margins, Sales Analytics, and Financials actions that lead to the same page without explanation.
- [ ] Define which reports are launch-visible.
- [ ] Define each report's authoritative data source and business meaning.
- [ ] Ensure users can distinguish operational Financials from profit analytics.
- [ ] Add direct links only when they open a meaningful distinct view.
- [ ] Hide empty/unimplemented report categories.
- [ ] Confirm report names match exported content.
- [ ] Confirm documentation matches actual report behavior.

### Launch Report Set
- [ ] Daily sales report.
- [ ] Expense report.
- [ ] Tax collected report.
- [ ] Invoice aging report.
- [ ] Payment-method breakdown.
- [ ] Invoice/payment reconciliation report.
- [ ] Profit and margin report.
- [ ] Webstore revenue and payout report.
- [ ] Subscription/payment history report for tenant billing.
- [ ] Decide which reports require CSV, XLSX, and PDF.

### Live And Visual QA
- [ ] Click every Reports navigation and ribbon action.
- [ ] Confirm no redirect loop, dead link, or misleading duplicate.
- [ ] Verify every visible report with known test data.
- [ ] Verify exports open and match filters.
- [ ] Confirm report layouts do not horizontally overflow.
- [ ] Confirm empty reports explain why no data exists.

---

## Section 10 — Webstore Payouts

### Verified Structure And Behavior
- [x] Webstore payout history endpoint exists.
- [x] Payout recording requires financial-manage or webstore-manage permission.
- [x] Webstore ownership is tenant verified before payout.
- [x] Payout amount uses an atomic owed-balance guard.
- [x] Payout records include tenant ID, amount, notes, recorder, and creation time.
- [x] Stored webstore analytics/payout report shows 20 passing tests.
- [x] Stripe tenant dashboard can show actual Stripe payouts to the tenant bank.

### PO Payout Integrity
- [ ] Scope payout-history query by `tenant_id` in addition to webstore ID.
- [ ] Reject zero, negative, NaN, infinite, malformed, and excessive payout amounts.
- [ ] Confirm `RecordPayoutRequest` validation enforces positive amounts.
- [ ] Make owed-balance update and payout-record insert transactional or add recovery for partial failure.
- [ ] Add idempotency key/reference for payout recording.
- [ ] Confirm concurrent payout attempts cannot overpay.
- [ ] Confirm payout owed is credited exactly once per eligible order.
- [ ] Confirm cancelled, refunded, disputed, or reversed orders adjust payout owed correctly.
- [ ] Define whether recorded payout represents actual money transfer or an external/manual record.
- [ ] Clearly distinguish webstore-owner payouts from Stripe payouts to the tenant bank.
- [ ] Confirm payout records cannot be deleted or changed without audit history.

### Live Payout Verification
- [ ] Create and complete a test webstore order.
- [ ] Confirm payout owed increases exactly once.
- [ ] Record a partial payout.
- [ ] Record the remaining payout.
- [ ] Attempt zero, negative, excess, duplicate, and concurrent payouts.
- [ ] Confirm payout history and analytics agree.
- [ ] Test refund/dispute adjustment.
- [ ] Verify owner portal payout visibility if launch-visible.
- [ ] Verify actual Stripe transfer behavior separately if automatic transfers are enabled.

### Visual And Flow QA
- [ ] Confirm amount owed, amount paid, payout history, Stripe payout, and owner share labels are unambiguous.
- [ ] Confirm money-moving actions require confirmation.
- [ ] Confirm payout forms fit mobile screens.
- [ ] Confirm every payout action works without blank or dead states.
- [ ] Confirm no duplicate payout concepts are shown without explanation.

---

## Section 11 — Stripe Connect And Payment Settings

### Verified Structure And Behavior
- [x] Route `/admin/payments` exists.
- [x] Payment Settings can load Stripe connection status.
- [x] Payment Settings displays platform mode and connected-account mode.
- [x] Mode mismatch detection and reconnect behavior exist.
- [x] Stripe onboarding, refresh, disconnect, dashboard link, and tenant operations dashboard endpoints exist.
- [x] Invoice and webstore Stripe checkout endpoints exist.
- [x] Stripe Connect webhook and payment-status fallback exist.
- [x] Tenant operations dashboard is tenant scoped for internal transaction records.
- [x] Stored Stripe Connect report shows 22 passing tests.

### PO Authorization And Configuration
- [ ] Require owner/admin or financial-manage permission for Stripe create-account, refresh-link, disconnect, dashboard-link, tenant-dashboard, and reconciliation.
- [ ] Require invoice payment permission for invoice payment-link actions.
- [ ] Confirm public webstore checkout remains public but validates store, product, assignment, pricing, and Stripe readiness.
- [ ] Require signed Stripe Connect webhook verification in production.
- [ ] Remove unsigned webhook fallback from production execution.
- [ ] Fail deployment/startup when live Stripe mode lacks required webhook secrets.
- [ ] Verify test/live key, account, price, webhook, and Connect mode alignment.
- [ ] Prevent a test-mode connected account from being used in live mode.
- [ ] Confirm disconnect cannot occur while active payment flows require the account without a strong warning.
- [ ] Confirm disconnect does not lose reconciliation history.

### Fees, Ledger, And Operations Dashboard
- [ ] Remove hardcoded Payment Settings fee text or load it from backend authoritative fee configuration.
- [ ] Confirm displayed platform fee matches the tenant plan and transaction type.
- [ ] Confirm Stripe processing estimates are labeled estimates.
- [ ] Confirm invoice and webstore platform fees are calculated differently only when intended.
- [ ] Reconcile internal transaction ledger against Stripe sessions, charges, balances, payouts, disputes, and fees.
- [ ] Confirm tenant dashboard does not expose another connected account's data.
- [ ] Confirm dispute queries reliably filter to the connected tenant account.
- [ ] Confirm dashboard handles Stripe API outages without a blank screen.
- [ ] Confirm recent payment, payout, dispute, event, and failure lists use stable pagination/limits.
- [ ] Confirm operations dashboard values clearly distinguish gross, fees, available, pending, and paid out.

### Live Stripe Connect Verification
- [ ] Connect a test Stripe Express account.
- [ ] Complete onboarding.
- [ ] Verify charges and payouts enabled status.
- [ ] Verify platform/account mode match.
- [ ] Open Stripe dashboard.
- [ ] Create and pay a test invoice.
- [ ] Create and pay a test webstore checkout.
- [ ] Verify webhook and payment-status fallback each work idempotently.
- [ ] Verify reconciliation repairs a deliberately stale invoice.
- [ ] Verify failed, expired, disputed, and refunded transaction states.
- [ ] Verify Stripe payout appears.
- [ ] Disconnect and reconnect safely.
- [ ] Repeat critical test in live-mode configuration without moving real money until approved.

### Visual And Responsive QA
- [ ] Confirm fee, mode, status, and warning text has sufficient contrast.
- [ ] Confirm actions wrap cleanly on tablet/mobile.
- [ ] Confirm operations tables have intentional internal scrolling.
- [ ] Confirm long Stripe IDs and error messages do not overflow.
- [ ] Confirm every button/link works and serves a clear purpose.
- [ ] Confirm no dead links, blank screens, black screens, overlapping controls, or large empty spaces.

---

## Cross-Section Data Contract Checklist

- [ ] Define authoritative invoice total fields.
- [ ] Define authoritative invoice paid/balance fields.
- [ ] Define authoritative payment transaction statuses.
- [ ] Define authoritative subscription statuses and entitlements.
- [ ] Define authoritative Financials revenue and expense sources.
- [ ] Define authoritative profit/margin revenue and cost sources.
- [ ] Define authoritative webstore payout owed/paid fields.
- [ ] Define authoritative Stripe fee configuration.
- [ ] Confirm all money values use consistent cents/decimal conversion and rounding.
- [ ] Confirm all currencies are explicit and supported.
- [ ] Confirm all financial records are tenant scoped.
- [ ] Confirm all money mutations have backend permission enforcement.
- [ ] Confirm all money mutations are idempotent or safely repeatable.
- [ ] Confirm refunds, disputes, chargebacks, voids, reversals, and corrections propagate consistently.

---

## Full Category Live Clickthrough

- [ ] Start with owner/admin and restricted employee accounts.
- [ ] Verify every financial permission boundary in the UI and direct API.
- [ ] Create job → invoice → send → portal → pay → reconcile → report.
- [ ] Record manual payment and verify fee-free behavior.
- [ ] Create daily sales and expenses and verify summary.
- [ ] Verify profit/margin analytics and exports.
- [ ] Complete subscription and credit checkout in Stripe test mode.
- [ ] Connect Stripe and verify operations dashboard.
- [ ] Complete webstore checkout and payout flow.
- [ ] Test failures, cancellations, expirations, refunds, disputes, and retries.
- [ ] Click every visible button, link, filter, tab, menu, modal action, and empty-state action.
- [ ] Confirm no dead links, black screens, blank screens, unhandled errors, duplicate money records, or misleading success messages.

## Shared Visual, Layout, And Accessibility Checklist

- [ ] Check all text, labels, placeholders, badges, totals, warnings, errors, and disabled states for sufficient contrast.
- [ ] Remove light-on-light and dark-on-dark combinations.
- [ ] Check desktop, tablet, and mobile widths.
- [ ] Remove accidental page-level horizontal scrolling.
- [ ] Remove unexplained large empty spaces.
- [ ] Confirm money values never clip, wrap confusingly, or display `$NaN`.
- [ ] Confirm tables use intentional internal scrolling.
- [ ] Confirm icon-only buttons have accessible names and tooltips.
- [ ] Confirm forms have visible labels and understandable validation.
- [ ] Confirm keyboard focus follows workflow order.
- [ ] Confirm dialogs trap and restore focus.
- [ ] Confirm financial states are understandable without color alone.
- [ ] Confirm loading, empty, error, permission-denied, pending, paid, failed, cancelled, expired, refunded, and disputed states all exist.

## Automated Test Work

- [ ] Add invoice endpoint permission tests.
- [ ] Add invoice mutation tenant-isolation tests.
- [ ] Add manual payment amount, overpayment, concurrency, and idempotency tests.
- [ ] Add invoice payment-history tenant-isolation tests.
- [ ] Add Financials permission and request-validation tests.
- [ ] Add Financials summary frontend/backend contract test.
- [ ] Add expense receipt persistence tests or remove the UI.
- [ ] Add production webhook-secret configuration tests.
- [ ] Add billing webhook event-id idempotency tests.
- [ ] Add webhook failure/retry tests.
- [ ] Add billing return-flow browser tests.
- [ ] Add subscription owner/admin permission tests.
- [ ] Add Stripe Connect management permission tests.
- [ ] Add Stripe mode/key/account mismatch tests.
- [ ] Add webstore payout validation, transaction/recovery, and idempotency tests.
- [ ] Add report-data reconciliation fixtures.
- [ ] Rerun invoice reconciliation and payment-link suites.
- [ ] Rerun billing, founder billing, and multi-product billing suites.
- [ ] Rerun Stripe Connect suite.
- [ ] Rerun profit analytics suite.
- [ ] Rerun webstore analytics/payout suite.
- [ ] Run frontend build after duplicate JSX fixes.

## Launch Decision Gates

**Category 4 can ship when:**
- [ ] Every financial and payment endpoint has correct backend permissions.
- [ ] Every financial and payment read/write is tenant scoped.
- [ ] Invoice mutations and payment history are fixed.
- [ ] Manual and Stripe payments cannot duplicate, overpay, or corrupt balances.
- [ ] Financials summary fields and calculations match the UI.
- [ ] Expense receipt UI is real or removed.
- [ ] Production billing and Connect webhooks require signature verification.
- [ ] Subscription and credit checkout return flows are accurate.
- [ ] Plan, feature, fee, and founder claims are verified.
- [ ] Stripe test-mode invoice, subscription, credit, webstore, reconciliation, and payout flows pass.
- [ ] Reports reconcile to source records.
- [ ] Every visible button and link has been clicked.
- [ ] Contrast, responsive layout, dead-link, duplicate-feature, and workflow-order audits pass.

**Hide or simplify a surface before launch when:**
- [ ] Its backend authorization or tenant isolation is not fixed.
- [ ] A payment flow cannot be verified end to end.
- [ ] A report cannot be reconciled to known source data.
- [ ] A visible receipt, payout, refund, dispute, or billing action is incomplete.
- [ ] A plan or fee claim is not accurate.
- [ ] A page produces misleading totals, blank states, or duplicate financial concepts.

**Exact Work Order:**
1. Add backend permission enforcement to invoices, Financials, billing changes, and Stripe Connect management.
2. Fix all unscoped invoice mutations, lookups, and payment-history reads.
3. Validate and make manual payments atomic/idempotent.
4. Fix Financials summary contract and duplicate JSX attributes.
5. Persist expense receipts or remove receipt controls.
6. Require signed webhooks in production and make failures retryable.
7. Fix Founder Billing and credit-purchase return flows.
8. Verify plan, feature, founder, and fee claims.
9. Harden webstore payout validation, idempotency, and failure recovery.
10. Build known-data reconciliation fixtures for Financials and profit reports.
11. Run complete Stripe test-mode invoice, subscription, credit, webstore, dispute, refund, reconciliation, and payout matrix.
12. Complete live clickthrough, contrast, responsive layout, duplicate-feature, and workflow-order audits.
13. Rerun automated tests and make the final Category 4 launch decision.

---

*Last updated: 2026-06-07 | Applied: platform_creator permission fix (invoices/financials now accessible). Full backend permission enforcement, tenant scoping fixes, and Stripe test matrix pending.*
