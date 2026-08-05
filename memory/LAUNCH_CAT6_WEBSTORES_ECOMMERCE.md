# Category 6: Webstores And Ecommerce
**Objective:** Verify that every launch-visible webstore can be configured, published, purchased from, fulfilled, reported, and paid out accurately without exposing private data or creating unpaid, duplicate, or unrecoverable orders.

**Sections:** Webstores Management · Store Setup Wizard · Public Storefront · Webstore Products · Webstore Orders · Webstore Owner Onboarding · Owner Portal · Webstore Questionnaires · Webstore Analytics · Webstore Payouts

---

## Category Readiness Summary

Status: Webstores is a broad, substantially implemented ecommerce system with strong saved API-test evidence. It is not launch-ready until the production Stripe bypass, confirmed tenant scope gaps, public checkout, owner onboarding, transfers, and live end-to-end workflows are resolved and verified.

### Verified Strengths
- [x] Internal Webstores, public Storefront, owner onboarding, owner portal, and customer portal webstore routes exist.
- [x] Backend supports store CRUD, products, assignments, public storefronts, public checkout, webstore orders, main Orders synchronization, questionnaires, analytics, and payouts.
- [x] Public storefront endpoints require stores to be public and active.
- [x] Public storefront payloads use an explicit safe-field allowlist.
- [x] Public order creation requires a Stripe-derived idempotency key and verifies a paid checkout transaction.
- [x] Payout eligibility is deferred until an eligible order status.
- [x] Manual payout recording has permission, positive-amount, available-balance, and atomic-balance guards.
- [x] Owner quick-connect and owner-portal onboarding paths exist.
- [x] Saved reports show broad passing coverage for store CRUD, products, checkout gating, order flow, analytics, payouts, Stripe Connect, questionnaires, and Orders synchronization.

---

## Category-Wide Confirmed Launch Blockers

- [ ] Remove or production-gate `const DEV_BYPASS_STRIPE = true` in `frontend/src/pages/Webstores.js`.
- [ ] Prove production users cannot bypass the shop's required Stripe connection.
- [ ] Add tenant scope to confirmed unscoped webstore, webstore-order, questionnaire, customer-sync, and owner-status updates.
- [ ] Add missing action-specific permissions to authenticated webstore read, analytics, order, questionnaire, and owner-invite endpoints where appropriate.
- [ ] Verify paid Stripe checkout creates exactly one webstore order and one main Orders record.
- [ ] Verify webhook/finalization retries cannot duplicate orders, jobs, items, commissions, or transfers.
- [ ] Verify owner Stripe onboarding and real test-mode transfer behavior.
- [ ] Define the authoritative payout ledger and reconcile manual payouts with automatic Stripe transfers.
- [ ] Verify public storefront abuse protection, price integrity, privacy, tax, shipping, cancellation, refund, and failure behavior.
- [ ] Fix owner-facing mojibake and complete public/internal responsive clickthrough.

---

## Category-Wide Required End-To-End Ecommerce Flow

- [ ] Define supported launch store types.
- [ ] Define the required setup steps for each store type.
- [ ] Define who owns store settings, products, prices, fulfillment rules, and financial terms.
- [ ] Define which fields store owners may edit and which remain tenant-controlled.
- [ ] Define how a store moves through draft, setup, active, paused/private, completed, and archived states.
- [ ] Define the exact conditions required before a store can become active.
- [ ] Define the exact conditions required before checkout can become enabled.
- [ ] Define the source of truth for product prices, fees, taxes, shipping, donations, and owner profit.
- [ ] Define the flow from paid checkout to webstore order, main Order, production, completion, and payout.
- [ ] Define cancellation, refund, chargeback, failed-payment, and partial-fulfillment behavior.
- [ ] Confirm every visible action advances this flow and remove actions that do not.

---

## Section 1 — Webstores Management

### Verified Structure And Behavior
- [x] Internal route `/webstores` exists.
- [x] Backend supports webstore create, list, detail, update, and delete.
- [x] Create requires `WEBSTORES_CREATE`.
- [x] Update and delete require `WEBSTORES_MANAGE`.
- [x] Store list is tenant scoped.
- [x] Store detail is tenant scoped.
- [x] Store create rejects duplicate names within a tenant.
- [x] Store owner customer synchronization exists.
- [x] Store logo and banner upload endpoints exist.
- [x] Store status and public/private controls exist.
- [x] Internal page supports Stores and Orders views.
- [x] Selected-store detail dashboard exists.
- [x] Saved `webstores_results.xml` report has 13 passing tests.
- [x] Saved `webstores_phase2_results.xml` report has 18 passing tests.
- [x] Saved `webstores_v3_results.xml` report has 16 passing tests.

### P0 Stripe Gate And Authorization
- [ ] Replace the hardcoded Stripe bypass with a production-safe environment gate.
- [ ] Make the safe production default `false`.
- [ ] Add a build/test guard that fails if production bypass is enabled.
- [ ] Confirm disconnected Stripe state blocks Webstores as intended.
- [ ] Confirm connected Stripe state loads Webstores.
- [ ] Confirm backend-sensitive actions do not rely only on the frontend gate.
- [ ] Define Webstores view, create, manage, orders, analytics, owner-invite, and payout permissions.
- [ ] Enforce view permission on list, detail, products, orders, analytics, questionnaire status, and setup-checklist endpoints.
- [ ] Enforce manage permission on status, public/private, owner invite, questionnaire send/apply, and store configuration.
- [ ] Add unauthorized-role API tests.

### P0 Tenant Isolation And Data Integrity
- [ ] Add tenant scope to confirmed unscoped webstore updates after ownership checks.
- [ ] Add tenant scope to fresh lookups after updates.
- [ ] Add tenant scope to customer-sync updates and lookups.
- [ ] Add tenant scope to webstore-order status updates.
- [ ] Add tenant scope to job and main Order updates created from webstore actions.
- [ ] Add tenant scope to questionnaire and response updates.
- [ ] Add cross-tenant tests for store read, update, delete, assets, products, orders, questionnaires, analytics, owners, and payouts.
- [ ] Confirm store deletion cannot orphan paid orders, products, payouts, owners, or customer records.
- [ ] Replace destructive delete with archive when operational or financial records exist.

### Management Live Clickthrough
- [ ] Open it as each intended employee role.
- [ ] Confirm loading, empty, populated, permission-denied, and error states.
- [ ] Search and filter stores.
- [ ] Open every store row action.
- [ ] Copy and open public store link.
- [ ] Toggle active/inactive.
- [ ] Toggle public/private.
- [ ] Upload and replace logo and banner.
- [ ] Open selected-store detail.
- [ ] Delete or archive a safe test store.
- [ ] Confirm every action shows accurate success or failure.

### Visual, Layout, Purpose, And Flow
- [ ] Keep module-home actions focused on Stores, queue/blockers, owner actions, payments, and overflow.
- [ ] Keep product, questionnaire, approval, public-link, status, and archive actions in selected-store context.
- [ ] Reduce front-row actions if the ribbon or page feels crowded.
- [ ] Check every font, badge, toggle, and helper color for contrast.
- [ ] Confirm no page-level horizontal scrolling.
- [ ] Confirm store tables/cards and selected-store panels work on mobile, tablet, laptop, and wide desktop.
- [ ] Confirm long store and owner names do not overlap controls.

---

## Section 2 — Store Setup Wizard

### Verified Structure And Behavior
- [x] Store Setup Wizard component exists.
- [x] Wizard includes store type, basics, owner, branding, products/settings, questionnaire, and review concepts.
- [x] Wizard validates required store name and owner name.
- [x] Wizard validates owner email format when provided.
- [x] Wizard supports logo and banner selection.
- [x] Wizard explains questionnaire and Stripe onboarding follow-up.
- [x] Wizard distinguishes tenant-controlled locked financial settings.

### Setup Contract And Validation
- [ ] Define required fields for each store type.
- [ ] Hide irrelevant steps and fields based on store type.
- [ ] Validate names, email, phone, dates, URLs, percentages, currency, and quantities on frontend and backend.
- [ ] Prevent invalid or contradictory dates.
- [ ] Prevent negative prices, fees, costs, commissions, donations, or goals.
- [ ] Prevent owner profit plus fees from creating impossible economics.
- [ ] Validate uploaded branding file type, size, content, and dimensions.
- [ ] Preserve entered data when navigating backward.
- [ ] Warn before closing with unsaved work.
- [ ] Prevent duplicate creation on repeated Submit clicks.
- [ ] Show clear recovery behavior after partial creation.
- [ ] Confirm owner customer sync is idempotent.

### Setup Wizard Live Clickthrough
- [ ] Create a business store through the wizard.
- [ ] Create a fundraiser/event store through the wizard.
- [ ] Create every other launch-visible store type.
- [ ] Test Next and Back on every step.
- [ ] Test missing required fields.
- [ ] Test invalid owner contact details.
- [ ] Upload, replace, and clear branding.
- [ ] Add or defer products.
- [ ] Review every summary value before creation.
- [ ] Submit once and with rapid double-click.
- [ ] Confirm the created store matches every selected value.
- [ ] Confirm the next required action is obvious after creation.

### Wizard Visual And Accessibility QA
- [ ] Confirm step labels fit on narrow screens.
- [ ] Confirm no horizontal scrolling.
- [ ] Confirm long hints and validation messages wrap.
- [ ] Confirm buttons remain reachable.
- [ ] Confirm selected, completed, optional, and error steps are distinguishable.
- [ ] Check all text and disabled controls for contrast.
- [ ] Confirm keyboard navigation and visible focus.
- [ ] Remove unnecessary fields, explanations, and large empty areas.

---

## Section 3 — Public Storefront

### Verified Structure And Behavior
- [x] Public route `/store/:storeId` exists.
- [x] Public store detail endpoint exists.
- [x] Public store products endpoint exists.
- [x] Public asset endpoints exist.
- [x] Public supporter endpoint exists for eligible fundraiser stores.
- [x] Private stores are rejected.
- [x] Inactive stores are rejected.
- [x] Public payload removes tenant ID, payout fields, and other private fields.
- [x] Public checkout readiness status and message are exposed.
- [x] Storefront supports cart, variants, quantities, customer information, shipping, notes, donations, and checkout.
- [x] Saved `billing_webstore_refactor_results.xml` report has 14 passing tests.
- [x] Saved `iteration98_checkout_gating_results.xml` report has 11 passing tests.

### P0 Public Security And Price Integrity
- [ ] Add rate limiting and abuse controls to public storefront and checkout endpoints.
- [ ] Confirm clients cannot override product price, fees, commission, tax, shipping, donation, or totals.
- [ ] Confirm backend recalculates every amount from authoritative values.
- [ ] Confirm disabled or unassigned products cannot be purchased.
- [ ] Confirm private or inactive stores cannot be ordered from through direct API calls.
- [ ] Validate quantity maximums and prevent abusive order sizes.
- [ ] Validate variants and options belong to the selected product.
- [ ] Sanitize all customer, note, donor, and supporter text.
- [ ] Protect customer contact and shipping data.
- [ ] Confirm public assets cannot expose arbitrary object-storage files.
- [ ] Define bot, fraud, and card-testing protections.
- [ ] Define privacy notice, terms, refund policy, and contact information.

### P0 Checkout And Failure Behavior
- [ ] Verify checkout is disabled when tenant Stripe is not ready.
- [ ] Verify checkout is disabled when store or required owner payout setup is not ready.
- [ ] Verify successful Stripe payment returns to the intended store.
- [ ] Verify cancelled checkout returns without creating an order.
- [ ] Verify failed and unpaid sessions do not create orders.
- [ ] Verify delayed payment methods and asynchronous finalization behavior.
- [ ] Verify duplicate return visits do not create duplicate orders.
- [ ] Verify checkout session expiry behavior.
- [ ] Define tax and shipping calculation responsibility.
- [ ] Define inventory/availability behavior during concurrent purchases.
- [ ] Display useful recoverable errors for Stripe and API failures.

### Public Storefront Live Clickthrough
- [ ] Open each launch store type logged out.
- [ ] Confirm private, inactive, missing, and checkout-disabled states.
- [ ] Confirm logo, banner, products, images, variants, descriptions, and prices.
- [ ] Add, update, and remove cart items.
- [ ] Test minimum and maximum quantities.
- [ ] Test shipping and customer fields.
- [ ] Test fundraiser donation options.
- [ ] Complete a Stripe test-mode purchase.
- [ ] Confirm confirmation state and order details are accurate.
- [ ] Confirm every public link and button works.

### Public Visual And Accessibility QA
- [ ] Check all text, buttons, price labels, badges, errors, and disabled states for contrast.
- [ ] Confirm mobile storefront has no horizontal scrolling.
- [ ] Confirm product images are visible, correctly framed, and not distorted.
- [ ] Confirm long product names, descriptions, variants, and prices fit.
- [ ] Confirm cart and checkout dialogs fit all viewports.
- [ ] Confirm keyboard navigation and visible focus.

---

## Section 4 — Webstore Products

### Verified Structure And Behavior
- [x] Product create, list, detail, update, and delete endpoints exist.
- [x] Product create and manage permissions exist.
- [x] Product operations are tenant scoped.
- [x] Product assignment to webstores exists.
- [x] Assigned products can have store-specific status and pricing.
- [x] Product removal from a store exists.
- [x] Public product listing checks store public/active state.
- [x] Public product listing sanitizes product data.
- [x] Saved `WEBSTORE_add_product_results.xml` report has 10 passing tests.

### Product Contract And Accuracy
- [ ] Define the product catalog source of truth.
- [ ] Define which fields are global and which may be overridden per store.
- [ ] Confirm price precedence is clear and consistent.
- [ ] Confirm base cost, production cost, retail price, owner profit, fees, and margin reconcile.
- [ ] Prevent negative or invalid costs and prices.
- [ ] Prevent disabled products from appearing or being purchased.
- [ ] Prevent deleted products from breaking historical orders.
- [ ] Define variant and option availability behavior.
- [ ] Define inventory, made-to-order, and out-of-stock behavior.
- [ ] Define image requirements and fallback behavior.
- [ ] Confirm product assignments cannot cross tenants.
- [ ] Confirm product edits do not silently alter historical order values.

### Product Live Clickthrough
- [ ] Create each launch-visible product type.
- [ ] Add images and variants.
- [ ] Assign products to multiple stores.
- [ ] Apply store-specific pricing.
- [ ] Disable and re-enable an assigned product.
- [ ] Remove product assignment.
- [ ] Edit the catalog product and verify intended store impact.
- [ ] Delete a safe unused product.
- [ ] Confirm storefront price and options match admin configuration.
- [ ] Confirm ordered line-item snapshots remain unchanged after product edits.

### Product Visual And Flow QA
- [ ] Confirm product creation/editing belongs in a clear catalog or selected-store context.
- [ ] Remove duplicate product actions.
- [ ] Check price, margin, warning, and disabled-state contrast.
- [ ] Confirm image controls and variant tables work without horizontal page scrolling.
- [ ] Confirm long names and option values do not overlap.
- [ ] Confirm all product actions work and serve a purpose.

---

## Section 5 — Webstore Orders

### Verified Structure And Behavior
- [x] Public order creation endpoint exists.
- [x] Public order creation requires `stripe:` idempotency key format.
- [x] Backend verifies payment transaction and paid status.
- [x] Backend verifies store active/public state.
- [x] Backend validates product and assignment relationships.
- [x] Backend uses idempotency lookup before order creation.
- [x] Webstore orders synchronize into main Orders with `source=webstore`.
- [x] Main Orders support webstore filtering.
- [x] Create-job action is idempotent when a job already exists.
- [x] Saved `WEBSTORE_order_flow_results.xml` report has 13 passing tests.
- [x] Saved `iteration168.xml` report has 13 passing tests.

### P0 Order Integrity And Idempotency
- [ ] Add tenant scope to confirmed unscoped webstore-order lookups and updates.
- [ ] Make paid-session verification and order creation atomic or safely idempotent.
- [ ] Add a database uniqueness constraint for Stripe session/idempotency key.
- [ ] Ensure duplicate webhook, return-page, and manual-finalize calls return the same order.
- [ ] Prevent duplicate main Orders, jobs, job items, commissions, and notifications.
- [ ] Snapshot product name, options, price, fees, taxes, shipping, donation, and totals.
- [ ] Confirm all money uses integer cents or approved decimal handling.
- [ ] Confirm line totals and grand total reconcile exactly.
- [ ] Define behavior when main Order synchronization fails after webstore order creation.
- [ ] Define behavior when job creation fails.
- [ ] Define cancellation, refund, partial refund, chargeback, and dispute state synchronization.
- [ ] Confirm order status transitions cannot credit payout more than once.

### Order Workflow Clickthrough
- [ ] Complete one paid order for every launch store type.
- [ ] Confirm exactly one webstore order is created.
- [ ] Confirm exactly one main Order is created.
- [ ] Confirm customer, line items, totals, source, store, and payment data match.
- [ ] Confirm the order appears in Webstores and Orders.
- [ ] Confirm production workflow can fulfill it.
- [ ] Move through every supported status.
- [ ] Confirm payout eligibility occurs once at the intended status.
- [ ] Retry finalization and status changes.
- [ ] Cancel and refund a test order.
- [ ] Confirm customer and staff notifications.
- [ ] Confirm reporting totals update correctly.

### Order Visual And Cross-Module QA
- [ ] Confirm Webstores Orders view and main Orders view have clear distinct purposes.
- [ ] Confirm users can navigate between store, webstore order, main Order, customer, and payment.
- [ ] Confirm no duplicated actions cause contradictory status changes.
- [ ] Confirm long order IDs, customer names, and item details fit.
- [ ] Confirm mobile order views avoid page-level horizontal scrolling.
- [ ] Confirm loading, empty, error, and sync-failure states are useful.

---

## Section 6 — Webstore Owner Onboarding

### Verified Structure And Behavior
- [x] Public owner onboarding route `/webstore-owner/onboard/:token` exists.
- [x] Owner portal signup route `/owner-portal-signup/:token` exists.
- [x] Backend supports Quick Connect and Portal Account invites.
- [x] Invite tokens use secure random URL-safe values.
- [x] Invite resolution checks expiry and status.
- [x] Public onboarding can create or resume a Stripe Express account.
- [x] Public onboarding can refresh Stripe status.
- [x] Public onboarding can open Stripe login link after connection.
- [x] Portal signup requires a password of at least eight characters.
- [x] Owner status endpoint exists for internal staff.

### P0 Token, Identity, And Update Security
- [ ] Add tenant scope to owner Stripe-status updates.
- [ ] Add tenant scope to owner-account/store-link updates.
- [ ] Confirm invite tokens are single-purpose, expiring, revocable, and non-reusable after completion.
- [ ] Decide whether consumed quick-connect links may still open Stripe login links.
- [ ] Prevent one invite from linking the wrong store or owner.
- [ ] Verify owner email ownership before granting persistent portal access.
- [ ] Prevent an existing unrelated user account from being silently converted into a webstore owner.
- [ ] Define secure account recovery and password reset for owners.
- [ ] Rate limit invite resolution, signup, login, refresh, and Stripe-link creation.
- [ ] Validate return and refresh URLs against trusted origins.
- [ ] Avoid exposing unnecessary store, tenant, owner, or Stripe identifiers publicly.
- [ ] Add token replay, expiry, revocation, cross-store, and account-takeover tests.

### Owner Onboarding Live Clickthrough
- [ ] Send a Quick Connect invite.
- [ ] Open and complete Quick Connect onboarding.
- [ ] Send an Owner Portal invite.
- [ ] Create an owner account.
- [ ] Complete Stripe test onboarding.
- [ ] Return from Stripe and confirm status refresh.
- [ ] Resume incomplete onboarding.
- [ ] Open Stripe Express dashboard.
- [ ] Test expired, revoked, consumed, malformed, and wrong-store tokens.
- [ ] Resend invites and confirm intended token behavior.
- [ ] Confirm internal owner status updates correctly.
- [ ] Confirm failures provide clear recovery.

### Onboarding Visual And Content QA
- [ ] Fix mojibake in owner onboarding and signup pages.
- [ ] Check dark-theme text and controls for contrast.
- [ ] Confirm mobile forms fit without horizontal scrolling.
- [ ] Confirm invalid and expired invite pages are useful.
- [ ] Confirm Stripe handoff and return messaging is clear.
- [ ] Confirm Quick Connect versus Owner Portal account choices are understandable.
- [ ] Confirm every button/link works and serves a purpose.

---

## Section 7 — Owner Portal

### Verified Structure And Behavior
- [x] Public route `/owner-portal` exists.
- [x] Owner Portal includes login and logout.
- [x] Owner Portal lists stores linked by `owner_user_id`.
- [x] Owner Portal displays orders, sales, paid, and pending values.
- [x] Owner Portal displays lifecycle progress and required actions.
- [x] Owner Portal exposes transfer history.
- [x] Owner Portal creates Stripe Express login links only for owned stores.
- [x] Customer portal also has a separate assigned-webstores experience.

### P0 Privacy, Authorization, And Financial Accuracy
- [ ] Confirm only `WEBSTORE_OWNER` role can use owner portal endpoints.
- [ ] Confirm owner JWT cannot access tenant employee/admin endpoints.
- [ ] Confirm owners can view only stores linked to their user ID.
- [ ] Add tenant/store scope to progress queries as defense in depth.
- [ ] Scope questionnaire, order, and payout-history queries through the owned store.
- [ ] Confirm owner portal never exposes tenant-only margins, locked financial settings, customer private data, or unrelated orders.
- [ ] Confirm orders, sales, paid, owed, donations, and progress calculations use authoritative values.
- [ ] Remove fallback calculations that can disagree with the payout ledger.
- [ ] Define owner access after a store is archived or ownership changes.
- [ ] Add owner privacy and cross-owner tests.

### Owner Portal Live Clickthrough
- [ ] Log in as a valid owner.
- [ ] Log in with invalid credentials.
- [ ] Test logout and token expiration.
- [ ] Review every linked store.
- [ ] Confirm progress stages and required actions.
- [ ] Confirm financial totals match admin analytics and ledger.
- [ ] Load transfer history.
- [ ] Open Stripe dashboard.
- [ ] Confirm an owner cannot access another owner's store URL/API.
- [ ] Confirm archived and completed store behavior.
- [ ] Confirm empty and error states.

### Owner Portal Visual And Flow QA
- [ ] Fix mojibake in store type/status and lifecycle text.
- [ ] Check dark-theme text, badges, stats, and disabled controls for contrast.
- [ ] Confirm cards and financial stats fit mobile and tablet.
- [ ] Confirm long store names and amounts fit.
- [ ] Confirm no horizontal scrolling or excessive empty space.
- [ ] Confirm the next required action is prominent.
- [ ] Confirm Owner Portal and customer Portal Webstores do not confuse users or duplicate purpose.

---

## Section 8 — Webstore Questionnaires

### Verified Structure And Behavior
- [x] Store-type questionnaire template dispatch exists.
- [x] Questionnaire send endpoint exists.
- [x] Questionnaire send reuses an existing linked questionnaire.
- [x] Questionnaire status endpoint exists.
- [x] Questionnaire apply-answers endpoint exists.
- [x] Event setup checklist includes questionnaire state.
- [x] Locked answer IDs protect tenant-controlled financial settings conceptually.
- [x] Saved questionnaire/webstore synchronization tests pass.

### P0 Questionnaire Data Integrity
- [ ] Add tenant scope to questionnaire updates during resend.
- [ ] Add tenant scope to webstore updates when applying answers.
- [ ] Add tenant scope to questionnaire-response updates after applying answers.
- [ ] Confirm locked fields cannot be changed through crafted public submissions.
- [ ] Confirm apply-answers maps only approved labels/fields.
- [ ] Confirm unknown, duplicated, malformed, and stale answers are ignored or rejected safely.
- [ ] Snapshot the questionnaire version used for each response.
- [ ] Define whether reapplying answers overwrites admin edits.
- [ ] Define review/approval before applying owner answers.
- [ ] Confirm email failure returns a usable link without false success.
- [ ] Confirm resend behavior does not create duplicate questionnaires.
- [ ] Add cross-tenant, locked-field, stale-response, and reapply tests.

### Questionnaire Live Clickthrough
- [ ] Create each store type with questionnaire support.
- [ ] Send questionnaire to owner.
- [ ] Open the link logged out.
- [ ] Confirm prefilled values.
- [ ] Confirm locked values cannot be edited.
- [ ] Submit valid and invalid responses.
- [ ] Confirm status changes to completed.
- [ ] Review response internally.
- [ ] Apply approved answers.
- [ ] Confirm intended store fields change and locked values do not.
- [ ] Resend and reapply safely.
- [ ] Force email failure and use returned link.

### Questionnaire Flow And Duplication QA
- [ ] Confirm questionnaire action appears in the selected-store workflow.
- [ ] Confirm it does not duplicate general Questionnaires confusingly.
- [ ] Confirm staff understand send, complete, review, and apply states.
- [ ] Confirm every action and status serves a purpose.
- [ ] Confirm mobile/public questionnaire layout and contrast pass Category 5 requirements.

---

## Section 9 — Webstore Analytics

### Verified Structure And Behavior
- [x] Store analytics endpoint exists.
- [x] Selected-store dashboard loads analytics, orders, and payouts independently.
- [x] Dashboard provides an analytics Retry state.
- [x] Analytics includes summary, daily sales, top products, payout information, and optional fundraiser metrics.
- [x] Saved `webstore_analytics_payouts_results.xml` report has 20 passing tests.

### P0 Metric Definitions And Accuracy
- [ ] Define gross sales, net sales, donations, fees, refunds, owner profit, owed, paid, and pending.
- [ ] Define which order statuses count toward every metric.
- [ ] Exclude unpaid, cancelled, refunded, and duplicate orders correctly.
- [ ] Handle partial refunds and chargebacks.
- [ ] Confirm timezone and date-boundary behavior.
- [ ] Confirm daily sales sum to the selected summary period.
- [ ] Confirm top-product totals match order line snapshots.
- [ ] Confirm fundraiser totals and public raised amounts use approved definitions.
- [ ] Confirm analytics and owner portal financial values reconcile.
- [ ] Confirm analytics and Financials reports reconcile.
- [ ] Add fixture-based calculation and reconciliation tests.

### Analytics Live Clickthrough
- [ ] Open analytics for empty, active, completed, and archived stores.
- [ ] Confirm values before and after paid orders.
- [ ] Confirm values after status changes.
- [ ] Confirm values after refund/cancellation.
- [ ] Confirm daily sales and top products.
- [ ] Confirm fundraiser metrics.
- [ ] Confirm error and Retry behavior.
- [ ] Compare analytics, owner portal, payout ledger, Stripe, and Financials.

### Analytics Visual And Purpose QA
- [ ] Check chart, metric, warning, and payout colors for contrast.
- [ ] Confirm analytics does not dominate setup blockers before launch.
- [ ] Confirm labels explain each metric without ambiguity.
- [ ] Confirm large amounts and long product names fit.
- [ ] Confirm charts and tables avoid page-level horizontal scrolling.
- [ ] Remove duplicate metrics and large empty chart areas.

---

## Section 10 — Webstore Payouts

### Verified Structure And Behavior
- [x] Payout history endpoint exists.
- [x] Manual payout recording endpoint exists.
- [x] Manual payout requires Financials Manage or Webstores Manage permission.
- [x] Manual payout rejects zero and negative amounts.
- [x] Manual payout rejects amounts above available owed balance.
- [x] Manual payout uses an atomic available-balance guard.
- [x] Payout records include tenant, store, amount, notes, and actor.
- [x] Order status transitions can credit payout owed idempotently.
- [x] Automatic Stripe transfer path exists.
- [x] Automatic transfer uses a Stripe idempotency key and records transfer ID.

### P0 Ledger, Transfer, And Reconciliation Integrity
- [ ] Define one authoritative payout ledger.
- [ ] Reconcile `payout_owed`, `payout_paid`, payout records, order commissions, and Stripe transfer records.
- [ ] Prevent manual payout from recording money not actually sent.
- [ ] Clearly distinguish Record Payout from Send Payout.
- [ ] Define whether manual payout requires external reference/proof.
- [ ] Prevent automatic transfer and manual payout from paying the same commission.
- [ ] Make payout credit and order status transition atomic or safely recoverable.
- [ ] Make transfer success and ledger update atomic or safely recoverable.
- [ ] Handle Stripe transfer failure, retry, reversal, and dispute.
- [ ] Prevent negative owed balances.
- [ ] Confirm commission is credited once when orders move in and out of eligible statuses.
- [ ] Define payout timing, minimum, hold, approval, and tax-reporting requirements.
- [ ] Add transfer/manual-payout collision and reconciliation tests.

### Payout Live Verification
- [ ] Complete owner Stripe onboarding in test mode.
- [ ] Complete an eligible paid order.
- [ ] Confirm commission calculation.
- [ ] Confirm owed balance increases once.
- [ ] Confirm automatic transfer occurs once when enabled.
- [ ] Confirm transfer appears in Stripe and Owner Portal.
- [ ] Test manual payout below, equal to, and above owed balance.
- [ ] Confirm invalid amounts are rejected.
- [ ] Retry status transition and payout calls.
- [ ] Simulate transfer failure and retry.
- [ ] Simulate reversal/refund after payout.
- [ ] Reconcile admin dashboard, owner portal, payout ledger, order, and Stripe.

### Payout Visual, Permissions, And Purpose QA
- [ ] Restrict payout controls to authorized users.
- [ ] Require explicit confirmation before recording or sending payout.
- [ ] Display available balance and resulting balance clearly.
- [ ] Label manual records versus Stripe transfers.
- [ ] Display reference, date, status, actor, and notes.
- [ ] Check amount and warning colors for contrast.
- [ ] Confirm payout tables work without page-level horizontal scrolling.
- [ ] Confirm no payout action implies money was sent when it was only recorded.

---

## Category-Wide External Service And Failure Review
- [ ] Verify current Stripe API keys, modes, account ownership, and webhook secrets.
- [ ] Require signed production webhooks.
- [ ] Return failure statuses that allow appropriate Stripe retries.
- [ ] Verify webhook event idempotency.
- [ ] Verify email provider configuration and sender identity.
- [ ] Verify public application origins and redirect URLs.
- [ ] Define monitoring and alerts for failed checkout, synchronization, owner onboarding, and transfers.
- [ ] Define support recovery steps for each external-service failure.
- [ ] Confirm logs contain useful IDs without secrets or full private data.

## Category-Wide Button, Link, Duplication, And Flow Review
- [ ] Click every button, link, icon action, tab, switch, filter, menu, and public CTA.
- [ ] Confirm every action produces the intended result or a clear error.
- [ ] Remove dead links, dead controls, and false-success messages.
- [ ] Remove or hide incomplete actions.
- [ ] Confirm no action opens a blank page or black screen.
- [ ] Confirm browser back, refresh, direct links, Stripe return, and expired links.
- [ ] Identify duplicate Store, Product, Order, Owner, Questionnaire, Analytics, and Payout actions.
- [ ] Consolidate duplicates or give each a clear distinct purpose.
- [ ] Confirm internal, public, owner, and customer terminology is consistent.
- [ ] Confirm workflow order is setup, owner, products, preview, activate, sell, fulfill, analyze, and pay.

## Category-Wide Visual And Accessibility Review
- [ ] Check all launch-visible surfaces at mobile, tablet, laptop, and wide-desktop widths.
- [ ] Check every font color against its background; remove light-on-light and dark-on-dark combinations.
- [ ] Check badges, helper text, disabled controls, alerts, links, and focus states for contrast.
- [ ] Confirm no accidental page-level horizontal scrolling.
- [ ] Confirm tables, charts, carts, dialogs, wizards, and forms have intentional narrow-screen behavior.
- [ ] Confirm long store, owner, product, order, variant, questionnaire, and payout values do not overlap.
- [ ] Remove large empty spaces and redundant cards.
- [ ] Confirm loading, empty, error, unavailable, permission-denied, and external-service failure states never look blank or broken.
- [ ] Confirm keyboard navigation, visible focus, labels, and field errors.
- [ ] Fix all mojibake and encoding defects.

## Automated Test Completion
- [ ] Re-run all Category 6 tests against the current branch and environment.
- [ ] Distinguish fixture-based tests from external smoke tests before treating them as certification.
- [ ] Add production-bypass guard test.
- [ ] Add backend permission and cross-tenant tests.
- [ ] Add paid-checkout end-to-end idempotency test.
- [ ] Add duplicate webhook/return/finalize tests.
- [ ] Add main Order/job synchronization partial-failure tests.
- [ ] Add public price-tampering and abuse tests.
- [ ] Add owner invite replay, expiry, revocation, and account-takeover tests.
- [ ] Add owner portal privacy and cross-owner tests.
- [ ] Add questionnaire locked-field and reapply tests.
- [ ] Add analytics fixture and reconciliation tests.
- [ ] Add payout transfer/manual collision, retry, reversal, and reconciliation tests.
- [ ] Add responsive visual tests for admin, public storefront, onboarding, and owner portal.

## Exact Recommended Work Order
- [ ] 1. Remove or production-gate `DEV_BYPASS_STRIPE`.
- [ ] 2. Fix confirmed unscoped tenant updates and missing permissions.
- [ ] 3. Define authoritative price, order, commission, analytics, and payout contracts.
- [ ] 4. Add missing idempotency constraints and partial-failure recovery.
- [ ] 5. Protect and verify owner invite, account, and portal flows.
- [ ] 6. Complete Stripe test-mode paid checkout and duplicate-finalization verification.
- [ ] 7. Complete main Orders, job, production, refund, and reporting synchronization verification.
- [ ] 8. Complete owner onboarding and transfer verification.
- [ ] 9. Complete questionnaire send, submit, review, and apply verification.
- [ ] 10. Reconcile analytics and payouts across all sources.
- [ ] 11. Fix mojibake, workflow overload, duplicate actions, and responsive issues.
- [ ] 12. Re-run automated tests and complete every internal/public/owner live clickthrough.
- [ ] 13. Hide any remaining incomplete or weakly verified surface before launch.

## Launch Decision Gates
- [ ] Production Stripe gating cannot be bypassed.
- [ ] Every visible store, setup, product, order, owner, questionnaire, analytics, and payout action works and serves a purpose.
- [ ] Public checkout creates exactly one paid webstore order and one main Order.
- [ ] Failed, unpaid, cancelled, duplicate, and retried checkout paths are safe.
- [ ] Store, order, questionnaire, owner, analytics, and payout data are tenant isolated and permission protected.
- [ ] Public storefront exposes no private or tenant-only data.
- [ ] Owner onboarding and portal access are secure and verified.
- [ ] Analytics, commissions, owed balances, payouts, and Stripe transfers reconcile.
- [ ] Refund, dispute, cancellation, and failure behavior is defined and tested.
- [ ] All automated tests and live clickthroughs pass.
- [ ] Contrast, responsive layout, overflow, empty-space, accessibility, and workflow-order review passes.
- [ ] Product owner, security reviewer, finance owner, and payments/compliance reviewer approve launch-visible Category 6 scope.
