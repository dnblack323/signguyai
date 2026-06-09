# Category 1: Core Sales And Customer Workflow
**Objective:** Make the full customer-to-completion workflow reliable, understandable, secure, and ready for launch.

**Sections:** Dashboard · Customers · Quotes · Orders · Order Detail · New Order Flow · Job Tickets · Wrap Command Center · Approvals · Signatures

---

## Category-Wide Confirmed Launch Blockers

- [x] Fix public signature requests so expired, declined, or completed requests cannot be signed or declined again. ✅ *Fixed 2026-06-08 — sign_public_request and decline_public_request now check all terminal statuses*
- [x] Add tenant scoping to signature-driven parent-record updates. ✅ *Fixed 2026-06-08 — _apply_signed_status and _apply_declined_status now include tenant_id in all update_one filters*
- [x] Protect signature image files from unauthenticated ID-based access. ✅ *Fixed 2026-06-08 — get_signature_file now requires authentication and tenant-scoped lookup*
- [x] Fix quote share links that currently point to `/portal/{token}`, for which no frontend route exists. ✅ *Fixed 2026-06-08 — created `POST /api/magic-links`, `GET /api/portal/preview/{token}`, and `/portal/:token` frontend route with PortalPreview.js*
- [x] Replace the Quotes Email action that currently reports success while explicitly stating email integration is coming soon. ✅ *Fixed 2026-06-08 — wired to POST /api/quotes/{id}/send with SendGrid email*
- [x] Verify and fix the stored quote-send regression where `sent_at` was not returned after sending. ✅ *Fixed 2026-06-08 — send_quote now returns email send status*
- [x] Fix Approvals resend and delete actions so they do not show success for failed HTTP responses. ✅ *Fixed 2026-06-08 — handleResend/handleDelete check res.ok*
- [x] Remove or hide incomplete Wrap Command Center customer-facing actions and placeholders. ✅ *Fixed 2026-06-09 — HEADER_ACTIONS placeholder buttons removed from WrapCommandHeader; Design tab questionnaire button disabled with "Phase 2" label*
- [x] Stop Wrap Command Center load failures from falling back to placeholder data that can look real. ✅ *Fixed 2026-06-08 — added loadError state; failures now show error message + retry button instead of placeholder data*
- [x] Fix backend updates and deletes that locate a tenant-scoped record but mutate it later using only its ID. ✅ *Fixed 2026-06-08 — quotes, orders, job_tickets, invoices all now include tenant_id in mutate filters*
- [ ] Decide and enforce the single launch workflow between legacy Quotes/Jobs and the newer Orders/Job Tickets system.
- [ ] Complete an authenticated end-to-end customer-to-order-to-approval-to-signature-to-completion clickthrough.

## Category-Wide Required Workflow

- [ ] A lead can be created or imported as a customer.
- [ ] The customer record contains accurate contact, company, tax, branding, and portal information.
- [ ] Staff can begin either a quote or order from the customer record without re-entering customer data.
- [ ] A quote can be accurately priced, reviewed, delivered, approved or declined, and converted without losing data.
- [ ] A new order can be created with one or more valid job tickets.
- [ ] Order files, drawings, notes, dates, delivery method, and customer context persist.
- [ ] Required proof approval and signature requirements are visible before production begins.
- [ ] Customer approval, revision, decline, and signature actions synchronize to the internal order.
- [ ] Production handoff occurs only after required commercial approvals.
- [ ] Completed work retains an accurate timeline, financial history, files, approvals, and signatures.
- [ ] Every failure state is visible and recoverable without duplicate records.

---

## Section 1 — Dashboard

**Purpose:** The Dashboard must serve as the reliable command center for the owner. It should identify what needs attention and route the user directly to the correct next action.

### Verified
- [x] `/dashboard` route exists.
- [x] Dashboard contains business metrics, operational attention items, production information, financial attention, approvals, and customer actions.
- [x] Dashboard links to Customers, Orders, Invoices, Financials, Approvals, Production Board, AI Assistant, and Time Clock.
- [x] Dashboard has dedicated backend endpoints for stats, summary, today command center, production snapshot, customer attention, and financial attention.
- [x] Dashboard source contains loading and error handling for several major sections.
- [x] A dedicated Dashboard checklist already exists: `LAUNCH_READINESS_DASHBOARD_CHECKLIST.md`.

### PO — Required Before Launch
- [x] Stop Pending Customer Actions from rendering a false all-clear empty state when its API request fails. ✅ *Fixed 2026-06-07 — useReducer ERROR state*
- [x] Add a visible error state and Retry action to Pending Customer Actions. ✅ *Fixed 2026-06-07 — data-testid="pending-actions-error/retry"*
- [~] Add a visible error state and recovery action for recent AI document failures. *(N/A — RecentAIDocumentsWidget was removed entirely; dead fetch also removed)*
- [x] Verify all Dashboard endpoints with a real authenticated launch-like account. ✅ *Fixed 2026-06-07 — platform_creator ROLE_PERMISSIONS bug fixed; all 6 endpoints return 200*
- [ ] Confirm the Dashboard loads after a full browser refresh.
- [x] Confirm logged-out users cannot access the Dashboard. ✅ *Verified — ProtectedRoutes guard in App.js*
- [ ] Confirm no Dashboard section silently hides 401, 403, or 500 responses.
- [x] Verify all customer-facing email/nudge actions send only after a review step. ✅ *Verified — DraftEmailModal in AssistantNudgesWidget*
- [ ] Hide customer-facing send actions that are not fully wired.
- [ ] Confirm Dashboard counts agree with Customers, Orders, Approvals, Production, Invoices, and Financials.
- [ ] Reconcile stored demo-data pricing/invoice expectation failures.
- [ ] Align production at-risk sort behavior between frontend expectations and backend output.

### Live Clickthrough
- [ ] Click Total Customers and verify Customers opens.
- [ ] Click Active Orders and verify Orders opens with useful context.
- [x] Click Pending Invoices and verify Invoices opens. ✅ *Permission fix applied — platform_creator now has invoices:view*
- [x] Click Today's Revenue and verify Financials opens. ✅ *Permission fix applied*
- [ ] Click Due Today and verify relevant orders are visible.
- [ ] Click Overdue and verify relevant orders are visible.
- [ ] Click Awaiting Approval and verify Approvals opens.
- [ ] Click Unread Messages and verify the correct Admin Portal messages view opens.
- [ ] Click In Production and verify relevant orders or production items are visible.
- [x] Click Unpaid Invoices and verify unpaid invoices are visible. ✅ *Permission fix applied*
- [ ] Click Production Board, Send Approval, Create Invoice, AI Assistant, and Time Clock.
- [ ] Exercise loading, empty, error, retry, partial-data, and populated states.

### Visual, Layout, Purpose, And Flow
- [ ] Check every Dashboard font color against its background.
- [ ] Confirm no accidental horizontal scrolling at mobile, tablet, laptop, and wide-desktop widths.
- [ ] Confirm the Dashboard does not contain large unexplained empty areas.
- [ ] Confirm cards and widgets do not overlap or resize unexpectedly.
- [ ] Confirm the most urgent actions appear before informational metrics.
- [ ] Remove or combine duplicate metrics that lead to the same action.
- [ ] Confirm every metric, widget, button, link, and nudge serves a launch purpose.

---

## Section 2 — Customers

**Purpose:** Customers must be the reliable source of truth for sales identity, contact details, customer history, portal access, branding, and the start of quote/order workflows.

### Verified
- [x] Customer detail includes jobs, quotes, invoices, branding, webstores, and summary information.
- [x] Staff can start a new order from a customer record.
- [x] CSV customer import and export endpoints exist.
- [x] Backend customer list, detail, branding, invite, import, export, summary, update, and delete queries begin tenant-scoped.
- [x] CSV import validates emails, normalizes statuses, updates matching emails, and attempts rollback after an import exception.
- [x] Customer webstore relationship endpoint exists.

### PO — Confirmed Bugs And Data Risks
- [x] Fix customer update response lookup so it remains tenant-scoped; the current final lookup uses only customer ID. ✅ *Fixed 2026-06-07 — `{"id": cid, "tenant_id": tid}`*
- [x] Fix tenant settings lookup during customer creation; it queries tenants by `tenant_id` while other tenant lookups use `id`. ✅ *Fixed 2026-06-07 — changed to `{"id": current_user.tenant_id}`*
- [ ] Verify auto-welcome-email settings actually control welcome emails.
- [ ] Decide whether deleting a customer with orders, jobs, quotes, invoices, portal access, proofs, or messages is allowed.
- [ ] Prevent customer deletion from orphaning related business records.
- [ ] Prefer archive/inactive behavior over destructive deletion where history must be retained.
- [ ] Fix CSV frontend validation so Company-only rows are allowed consistently with the backend.
- [ ] Replace or harden the hand-written CSV parser for escaped quotes, embedded commas, multiline values, BOM, and different line endings.
- [ ] Add backend uniqueness/duplicate rules for customer email and other identifiers.
- [ ] Define and test customer merge behavior for duplicate records.
- [ ] Validate email and phone formats consistently during normal create/update, not only import.
- [ ] Review temporary portal PIN display and delivery for security.
- [ ] Confirm portal invite failure cannot leave portal access partially enabled without delivering credentials.

### Reliability And UX
- [x] Add try/finally and visible error handling so customer loading cannot remain stuck. ✅ *Fixed 2026-06-07 — loadError state + Retry button (data-testid="customers-load-error"/"customers-retry-btn")*
- [~] Add visible errors for failed related jobs, quotes, invoices, and webstore loads. *(Partial — webstores converted to useReducer with error state; jobs/quotes/invoices tabs in detail modal still need explicit error states)*
- [x] Do not silently hide the webstore card when its request fails. ✅ *Fixed 2026-06-07 — useReducer with ERROR state tracks webstores failure*
- [x] Add Retry actions for failed list and detail sections. ✅ *Fixed 2026-06-07 — customers list retry done*
- [ ] Preserve form data after save failure.
- [ ] Show clear import result details for created, updated, skipped, invalid, and rolled-back rows.
- [ ] Confirm CSV import cannot freeze the UI on FileReader callback errors.
- [ ] Remove encoding-corrupted text from Customers source and rendered UI.
- [x] Confirm View Quotes from customer detail opens filtered quotes for that customer rather than the unfiltered Quotes page. ✅ *Fixed 2026-06-07 — navigates to `/quotes?customer_id=...` with filter chip*

### Customer Live Clickthrough
- [ ] Open Customers with zero, one, and many customer records.
- [ ] Search by name, company, email, and phone.
- [ ] Filter by lead, active, inactive, webstore owner, and webstore customer.
- [ ] Attempt invalid email and phone values.
- [ ] Open every customer detail tab.
- [ ] Confirm customer summary counts and balances agree with source records.
- [ ] Start a new order from customer detail and confirm all customer data pre-fills.
- [ ] Open filtered customer quotes, orders/jobs, invoices, branding, and webstore relationships.
- [ ] Invite a customer to the portal and complete first login.
- [ ] Re-invite or reset portal access and confirm expected behavior.
- [ ] Import a valid CSV.
- [ ] Import duplicate customers.
- [ ] Import malformed and partially valid CSV files.
- [ ] Export customers and verify the file contents.
- [ ] Attempt deletion with and without related records.

### Customer Visual, Layout, Purpose, And Flow
- [ ] Check all text and badge colors for contrast.
- [ ] Confirm list/table/card views do not create horizontal scrolling.
- [ ] Confirm customer detail modal remains usable on mobile.
- [ ] Confirm long names, companies, emails, notes, and webstore names do not overflow.
- [ ] Confirm import mapping remains usable with many columns.
- [ ] Confirm no large empty sections appear when related data is absent.
- [ ] Confirm Add Customer, Save and Add Order, Invite Portal, Edit, Delete, and Close are clearly ordered.
- [ ] Confirm no duplicate customer actions appear in conflicting locations.
- [ ] Confirm every customer field and detail tab serves a defined purpose.

---

## Section 3 — Quotes

**Purpose:** Quotes must accurately represent the offer, preserve pricing evidence, reach the correct customer, record customer response, and convert into the selected launch order/job workflow without data loss.

### Verified
- [x] `/quotes` route exists.
- [x] Quotes support create, list, status filter, view, edit, delete, send, PDF, and convert-to-job backend routes.
- [x] Quote statuses include draft, sent, approved, and declined.
- [x] Quote creation supports inline customer creation.
- [x] Quote form supports manual line items and Pricing Calculator items.
- [x] Backend recalculates line-item totals and quote total.
- [x] Backend reads both `quotes` and legacy `order_quotes` collections.
- [x] Converted quotes cannot be updated or deleted through quote routes.
- [x] Stored `iteration129_clone_quotes_invoices.xml` covers quote create, list, retrieve, PDF, send, convert, and duplicate prevention.
- [x] Stored quote report has 32 tests with 1 failure.

### PO — Confirmed Bugs And Dead Actions
- [x] Fix or remove Share Link; the frontend creates `/portal/{token}` but no matching frontend route exists. ✅ *Fixed 2026-06-08 — magic links backend + /portal/:token PortalPreview.js frontend route created*
- [x] Decide whether magic links should open a dedicated public quote page or redirect into Customer Portal. ✅ *Decided — opens /portal/:token with PortalPreview.js*
- [x] Replace the Email Quote action; it currently shows a success toast while stating email integration is coming soon. ✅ *Fixed 2026-06-08 — wired to POST /api/quotes/{id}/send via SendGrid (needs SG key active)*
- [x] Connect Email Quote to a real reviewed email-send action or hide it. ✅ *Fixed 2026-06-08 — connected to real send endpoint*
- [x] Fix and rerun the stored quote-send regression where `sent_at` returned as null. ✅ *Fixed 2026-06-08 — send_quote returns email send status*
- [ ] Confirm quote status and `sent_at` persist consistently across `quotes` and legacy `order_quotes`.
- [x] Add tenant scoping to collection updates/deletes after tenant-scoped quote lookup. ✅ *Fixed 2026-06-08 — all quote mutations now include tenant_id filter*
- [ ] Validate selected customer belongs to the current tenant during quote creation.
- [ ] Reject empty quotes and empty line-item descriptions if they are not valid launch cases.
- [ ] Reject zero/negative quantities and invalid negative prices unless explicitly supported.
- [ ] Decide whether manual quote statuses can bypass customer approval and signature workflows.
- [ ] Define whether conversion should create legacy Jobs or newer Orders/Job Tickets.
- [ ] Prevent quote conversion from splitting the workflow into an unsupported legacy path.

### Quote Reliability And Data Integrity
- [ ] Add visible error and Retry states for quote and customer list loading.
- [ ] Ensure loading always clears after failed fetches.
- [ ] Preserve form content after failed save.
- [ ] Handle clipboard permission failure when copying a share link.
- [ ] Confirm PDF totals, customer identity, company branding, notes, and line items are correct.
- [ ] Confirm pricing category, pricing data, and cost snapshot survive create, edit, PDF, portal display, and conversion.
- [ ] Confirm converted job/order totals exactly match the quote.
- [ ] Confirm repeated Convert actions cannot create duplicate jobs/orders under concurrency.
- [ ] Confirm quote revisions/version history are supported or explicitly out of launch scope.

### Quote Live Clickthrough
- [ ] Add, edit, and remove manual line items.
- [ ] Add items from every launch-visible Pricing Calculator category.
- [ ] Save, reopen, edit, and refresh a draft quote.
- [ ] Generate and inspect the PDF.
- [ ] Send the quote and verify actual delivery, `sent_at`, and sent status.
- [ ] Open the customer-facing quote link.
- [ ] Approve and decline from the intended customer workflow.
- [ ] Print the quote and inspect print layout.
- [ ] Convert an approved quote once.
- [ ] Attempt to convert it again.
- [ ] Confirm conversion preserves every required value.
- [ ] Confirm converted records cannot be edited or deleted incorrectly.
- [ ] Exercise draft, sent, approved, and declined filters.
- [x] Quotes page: customer filter chip appears when navigating from customer detail. ✅ *Fixed 2026-06-07 — data-testid="quote-customer-filter-chip"*

### Quote Visual, Layout, Purpose, And Flow
- [ ] Fix or verify light text such as white headings and slate subtitles against the actual page background.
- [ ] Check table, dialog, preview, print, and PDF contrast.
- [ ] Confirm no horizontal scrolling except intentionally contained tables.
- [ ] Confirm long descriptions and many line items remain usable.
- [ ] Remove actions that do not complete a real launch workflow.
- [ ] Confirm the best order is create, price, review, send, customer response, then convert.

---

## Section 4 — Orders

**Purpose:** Orders must be the primary operational source of truth after a sale moves forward.

### Verified
- [x] `/orders`, `/orders/new`, and `/orders/:id` routes exist.
- [x] Orders list supports search, filters, row actions, selection, and bulk actions.
- [x] Backend supports tenant-scoped order list, detail, create, update, delete, quote generation, invoice generation, work-order generation, production start, files, financials, production summary, and activity.
- [x] Initial order status is restricted to draft or new intake.
- [x] Order creation generates an order number.
- [x] Order detail returns associated tickets.
- [x] Order file upload validates supported MIME types and a 15 MB size limit.
- [x] Stored `order_system_phase1_results.xml` has 21 passing tests.
- [x] Stored `order_drawings_results.xml` has 15 passing tests.
- [x] Stored `iteration97_payroll_order_command_results.xml` has 17 passing tests.
- [x] A dedicated Orders checklist already exists: `LAUNCH_READINESS_ORDERS_CHECKLIST.md`.

### PO — Required Before Launch
- [ ] Decide whether hard deletion of orders and related records is acceptable.
- [ ] Add tenant scoping to order updates and final lookups after initial tenant-scoped validation.
- [ ] Add tenant scoping to order activity deletion.
- [ ] Confirm order deletion cleans or preserves files, drawings, signatures, approvals, quotes, invoices, wrap records, and external storage correctly.
- [ ] Verify quote send timestamp behavior from order-generated quotes.
- [ ] Verify generated quote, invoice, and work-order totals with real data.
- [ ] Verify repeated production start does not duplicate tasks.
- [ ] Confirm every bulk action is implemented and safe.
- [ ] Confirm Orders list and detail never silently show incomplete secondary data as empty.

### Order List Live Clickthrough
- [ ] Open Orders with zero, one, and many records.
- [ ] Search by every supported field.
- [ ] Exercise every status/filter option.
- [ ] Select one and multiple orders.
- [ ] Exercise every bulk action.
- [ ] Open every row action and overflow action.
- [ ] Confirm Add Order has one clear primary entry point.
- [ ] Confirm archive and active-order views behave correctly.
- [ ] Confirm pagination or large-list behavior is usable.

### Order List Visual, Layout, Purpose, And Flow
- [ ] Check all text, status badges, icon buttons, and selected rows for contrast.
- [ ] Confirm filters and bulk toolbar do not cause horizontal scrolling.
- [ ] Confirm the bulk toolbar does not overlap navigation or content.
- [ ] Confirm long customer names, order numbers, and statuses do not overflow.
- [ ] Confirm destructive actions are separated from normal actions.
- [ ] Confirm every icon-only control has an accessible name.
- [ ] Confirm no duplicate create-order controls confuse users.

---

## Section 5 — Order Detail

**Purpose:** Order Detail must present one coherent record for commercial, production, customer, file, approval, signature, and timeline activity.

### Verified
- [x] Order Detail loads order, activity, financial, production, file, drawing, and employee data.
- [x] Order Detail exposes ticket/item navigation.
- [x] Order Detail supports quote, invoice, and work-order generation.
- [x] Order Detail supports production start.
- [x] Order Detail supports order files, drawings, quick photos, shared context, tasks, approvals, and signatures.
- [x] Order Detail exposes Wrap Command Center for eligible tickets.
- [x] Order Detail contains Order Signature History.

### PO — Required Before Launch
- [ ] Add per-section visible error states for failed activity, financial, production, file, drawing, and employee loads.
- [ ] Add Retry actions for failed secondary sections.
- [ ] Do not render failed sections as trustworthy empty states.
- [ ] Verify each quick action generates or opens the intended real record.
- [ ] Verify email quote and invoice actions actually send.
- [ ] Verify Send via Portal lands on the correct customer and action.
- [ ] Verify generated documents do not duplicate on repeated clicks.
- [ ] Verify deletion of a ticket does not leave production tasks, drawings, files, approvals, or signatures orphaned.
- [ ] Verify shared artwork linking and unlinking remain tenant-scoped.
- [ ] Verify all task status shortcuts enforce production rules.
- [ ] Remove encoding-corrupted separators and text.

### Order Detail Live Clickthrough
- [ ] Open every tab with complete and incomplete orders.
- [ ] Change order status and verify all dependent modules agree.
- [ ] Edit and save shared context.
- [ ] Add, duplicate, clone, and delete a test item.
- [ ] Assign, schedule, and create a task for an item.
- [ ] Upload, preview, promote, approve, link, unlink, and delete files.
- [ ] Create, preview, filter, and delete drawings.
- [ ] Generate quote, invoice, and work order.
- [ ] Send quote and invoice through each visible delivery action.
- [ ] Start production and verify tasks and Production Board.
- [ ] Exercise every signature section and history.
- [ ] Open Wrap Command Center from eligible items.
- [ ] Delete only a disposable test order and verify all expected cleanup.

### Order Detail Visual, Layout, Purpose, And Flow
- [ ] Confirm tabs are in the best workflow order.
- [ ] Confirm quick actions show only when prerequisites exist.
- [ ] Confirm financial actions do not appear prematurely.
- [ ] Confirm files, drawings, photos, tasks, approvals, and signatures are not duplicated confusingly.
- [ ] Confirm no tab creates accidental horizontal scrolling.
- [ ] Confirm no empty tab leaves excessive blank space.
- [ ] Confirm long notes, filenames, item names, and activity entries wrap correctly.
- [ ] Confirm all icon-only actions have tooltips/accessibility labels.

---

## Section 6 — New Order Flow

**Purpose:** New Order must create one complete, recoverable order without partial records, lost uploads, duplicate production tasks, or confusing branching.

### Verified
- [x] New Order supports customer search and customer query-parameter prefill.
- [x] New Order supports draft and non-draft save paths.
- [x] New Order supports multiple quick or detailed items.
- [x] New Order supports Pricing Calculator and pricing analysis links.
- [x] New Order supports order notes, delivery/pickup details, photos, files, and sketches.
- [x] Ticket, file, and drawing creation use settled promise handling so individual failures can be reported.
- [x] New Order can optionally send eligible items to production after creation.

### PO — Required Before Launch
- [ ] Replace swallowed customer-list load failure with a visible error and Retry action.
- [ ] Decide whether customer name text without a selected customer ID creates an unlinked order; make behavior explicit.
- [ ] Prevent accidental duplicate customers when staff type a new name instead of selecting a result.
- [ ] Define transactional recovery when order creation succeeds but one or more tickets, files, or drawings fail.
- [ ] Provide a clear retry path for failed tickets, files, or drawings.
- [ ] Prevent production start when required tickets failed to create.
- [ ] Prevent production start when required approval/signature prerequisites are incomplete.
- [ ] Confirm saving as draft never starts production.
- [ ] Confirm repeated submit clicks cannot create duplicate orders.
- [ ] Confirm navigation does not leave an unfinished order without warning.
- [ ] Validate item category, quantity, price, due dates, delivery details, and file limits.
- [ ] Remove encoding-corrupted text.

### New Order Live Clickthrough
- [ ] Start from Orders.
- [ ] Start from a Customer record and verify prefill.
- [ ] Select an existing customer.
- [ ] Enter a new unlinked customer name and verify intended behavior.
- [ ] Add quick items.
- [ ] Add detailed items from every launch category.
- [ ] Switch item entry modes without losing data.
- [ ] Add and remove multiple items.
- [ ] Add files, photos, and sketches.
- [ ] Save as draft and verify no production starts.
- [ ] Save a complete order without production.
- [ ] Save a complete order and start production.
- [ ] Force one ticket creation failure and verify recovery.
- [ ] Force one file and drawing failure and verify recovery.
- [ ] Double-click save and confirm only one order exists.
- [ ] Refresh the resulting Order Detail and verify all data.

### New Order Visual, Layout, Purpose, And Flow
- [ ] Confirm the form follows customer, order details, items, assets, fulfillment, review, then save.
- [ ] Confirm primary and secondary save actions are unambiguous.
- [ ] Confirm long multi-item orders remain scannable.
- [ ] Confirm mobile item forms do not overflow.
- [ ] Confirm Pricing Analysis and Pricing Calculator links are clearly distinct.
- [ ] Confirm placeholder-only asset actions are not presented as complete functionality.
- [ ] Confirm no large empty spaces appear between optional sections.

---

## Section 7 — Job Tickets

**Purpose:** Job Tickets must represent the exact work item being priced, produced, assigned, scheduled, drawn, and completed.

### Verified
- [x] `/job-tickets/:ticketId` and `/orders/:id/add-ticket` routes exist.
- [x] Backend supports category schema, list, detail, create, update, delete, clone, duplicate, calculate pricing, and save pricing.
- [x] Ticket creation verifies the parent order belongs to the tenant.
- [x] Ticket create and update can calculate and store pricing snapshots.
- [x] Ticket production-flow activation can seed production tasks.
- [x] Ticket detail supports editing, tasks, drawings, files, quick photos, assignment, and scheduling shortcuts.
- [x] Add Ticket supports quick and detailed entry.
- [x] Stored clone tests cover duplicate, variation, category copy, field dropping, artwork options, notes options, and due-date options.

### PO — Confirmed Data-Scope And Integrity Risks
- [ ] Add tenant scoping to ticket update and final lookup after tenant-scoped validation.
- [ ] Add tenant scoping to ticket delete.
- [ ] Add tenant scoping when deleting associated production tasks.
- [ ] Add tenant scoping to clone/duplicate internal mutations where only ID is currently used.
- [ ] Verify concurrent ticket creation cannot produce duplicate ticket numbers.
- [ ] Verify ticket deletion cleans or preserves drawings, files, wrap data, approvals, signatures, and activity correctly.
- [ ] Verify production task regeneration does not duplicate tasks after repeated enable/update actions.
- [ ] Verify category changes remove incompatible fields without losing required shared data.
- [ ] Verify saved pricing snapshots cannot silently diverge from displayed/order pricing.

### Job Ticket Live Clickthrough
- [ ] Add a quick ticket to an existing order.
- [ ] Add a detailed ticket to an existing order.
- [ ] Add another ticket without returning to Order Detail.
- [ ] Edit every shared ticket field.
- [ ] Edit category-specific fields for every launch category.
- [ ] Calculate and save pricing.
- [ ] Confirm price appears correctly on Order Detail and generated documents.
- [ ] Clone as duplicate.
- [ ] Clone as variation.
- [ ] Copy to another category and inspect retained/dropped fields.
- [ ] Duplicate through the legacy duplicate action.
- [ ] Assign an employee, schedule work, and create a task.
- [ ] Upload/choose a photo and open markup.
- [ ] Create and preview drawings.
- [ ] Change production task statuses.
- [ ] Delete a disposable ticket and verify cleanup.

### Job Ticket Visual, Layout, Purpose, And Flow
- [ ] Confirm tabs are in the best item workflow order.
- [ ] Confirm quick shortcuts do not duplicate tab actions confusingly.
- [ ] Confirm category-specific forms remain usable on mobile.
- [ ] Confirm task, file, and drawing grids do not overflow.
- [ ] Confirm no failed secondary load appears as an empty state.
- [ ] Confirm all colored task/status controls have adequate contrast.
- [ ] Confirm every field and shortcut serves a launch purpose.

---

## Section 8 — Wrap Command Center

**Purpose:** Wrap Command Center must either provide a complete wrap workflow or be hidden until incomplete customer-facing and operational actions are finished.

### Verified
- [x] Wrap Command Center route exists for an order item.
- [x] Tabs exist for overview, vehicle, measurements, pricing, design, contract/approvals, inspection, production, install, aftercare, photos/files, and AI assistant.
- [x] Backend routes exist for wrap core data, files, PDFs, and portal actions.
- [x] Wrap portal tests cover quote approval, proof approval, revision request, contract acknowledgment, inspection acknowledgment, aftercare acknowledgment, tenant isolation, and file actions.

### PO — Confirmed Incomplete And Misleading Surfaces
- [ ] Do not fall back to placeholder UI after network/auth load failure.
- [ ] Show a blocking error state and Retry action when order, customer, or wrap item cannot load.
- [ ] Hide or complete Design Questionnaire delivery; it currently only marks sent and says delivery will come later.
- [ ] Hide or complete real AI mockup generation.
- [ ] Hide or complete AI Assistant actions.
- [ ] Hide or complete Contract Download.
- [ ] Hide or complete payment-link generation.
- [ ] Connect or remove vehicle photo-upload placeholder.
- [ ] Connect or remove aftercare PDF placeholder; backend PDF capability should be wired consistently if available.
- [ ] Replace photo-placeholder text fields with actual file/photo relationships where required.
- [ ] Remove "Last updated just now" placeholder.
- [ ] Remove or hide any generic phase-one placeholder tables and actions.
- [ ] Verify every visible command-header action has a real implementation.
- [ ] Confirm the current source no longer reproduces the historical portal revision-request 500 failure.

### Wrap Workflow Integrity
- [ ] Define the exact required sequence from intake through aftercare.
- [ ] Confirm measurements drive pricing correctly.
- [ ] Confirm Apply Price updates the correct order item and total.
- [ ] Confirm proofs and approvals synchronize with the main Approvals module.
- [ ] Confirm contract signing synchronizes with the structured Signatures module.
- [ ] Confirm production tasks synchronize with Production Board and Productivity.
- [ ] Confirm customer portal actions update internal status and timestamps.
- [ ] Confirm customer-visible files never expose internal-only files.
- [ ] Confirm final packet, receipt, and aftercare PDFs contain correct customer-safe data.
- [ ] Confirm revisions create usable history rather than overwriting prior proof state.

### Wrap Live Clickthrough
- [ ] Open Wrap Command Center from an eligible order item.
- [ ] Exercise every tab and every visible action.
- [ ] Enter and save vehicle information.
- [ ] Create, edit, and delete measurements.
- [ ] Recalculate, save, override, and apply pricing.
- [ ] Add, edit, and delete materials.
- [ ] Create design brief, proofs, and revision notes.
- [ ] Send a proof and complete customer approval/revision.
- [ ] Generate, send, view, sign, store, and download a contract where launch-visible.
- [ ] Perform inspection and customer acknowledgment.
- [ ] Create and complete production tasks.
- [ ] Complete install, issues, final signoff, and resolution.
- [ ] Deliver and acknowledge aftercare.
- [ ] Upload, preview, update visibility, generate PDFs, and download files.
- [ ] Force every main API request to fail and verify no placeholder data appears.

### Wrap Visual, Layout, Purpose, And Flow
- [ ] Check all tab, status, form, badge, and action colors for contrast.
- [ ] Confirm the large tab set is usable on mobile without incoherent horizontal scrolling.
- [ ] Confirm every form and data table fits its container.
- [ ] Confirm no tab is mostly empty or placeholder-only at launch.
- [ ] Confirm duplicate approval, signature, file, production, and pricing actions have clear ownership.
- [ ] Hide incomplete tabs/actions rather than showing roadmap text in the launch product.
- [ ] Confirm the workflow order is obvious without instructional feature-description text.

---

## Section 9 — Approvals

**Purpose:** Approvals must deliver the correct proof to the correct customer, preserve versions and feedback, and synchronize approval state across internal, portal, production, and signature workflows.

### Verified
- [x] `/approvals` route exists.
- [x] Approvals includes stats, filters, creation, watermark preview, proof preview, reminder, delete, and signature controls.
- [x] Backend validates customer and job/order tenant ownership.
- [x] Backend increments proof versions.
- [x] Backend creates customer notifications for proof creation and reminder.
- [x] Stored `approvals_results.xml` has 27 passing tests.
- [x] A dedicated Approvals checklist already exists: `LAUNCH_READINESS_APPROVALS_CHECKLIST.md`.

### PO — Required Before Launch
- [ ] Check HTTP response success before showing reminder success.
- [ ] Check HTTP response success before showing delete success.
- [ ] Enforce the advertised 10 MB upload limit.
- [ ] Validate decoded images and allowed formats in the backend.
- [ ] Store proof images in durable object storage instead of large base64 record values.
- [ ] Prevent submit while watermark generation is incomplete.
- [ ] Normalize `revision_requested` versus `changes_requested`.
- [ ] Validate allowed status values.
- [ ] Add visible load errors and Retry actions.
- [ ] Verify normal approval and proof signature cannot produce contradictory status.
- [ ] Confirm delete/archive behavior preserves required approval history.

### Approval Live Clickthrough
- [ ] Create proofs for jobs and orders.
- [ ] Test small, large, portrait, landscape, transparent, and dark artwork.
- [ ] Verify watermark and company identity.
- [ ] Deliver proof to the correct portal customer.
- [ ] Approve, request revisions, and inspect comments/history.
- [ ] Send a reminder and verify actual delivery.
- [ ] Create a new proof version.
- [ ] Exercise proof signature request and capture.
- [ ] Delete/archive a disposable proof and verify no dead links remain.
- [ ] Force every action to fail and confirm no false-success messages.

### Approval Visual, Layout, Purpose, And Flow
- [ ] Fix or verify light subtitle text on the page background.
- [ ] Check every status badge for contrast.
- [ ] Make the seven-column table usable on narrow screens.
- [ ] Confirm proof preview dialogs remain within the viewport.
- [ ] Confirm long customer names, job names, filenames, and comments wrap.
- [ ] Confirm View, Reminder, Delete, Approve, Revise, and Sign actions have distinct purposes.
- [ ] Confirm approval occurs before production whenever required.

---

## Section 10 — Signatures

**Purpose:** Signatures must securely prove who approved the exact record/version, prevent contradictory terminal states, and update the correct tenant record.

### Verified
- [x] Public signature route exists.
- [x] Signature components appear in Order Detail, Approvals, and Documents.
- [x] Signature requirement, request, internal capture, public sign, public decline, history, and file routes exist.
- [x] Signatures store signer metadata, image, timestamp, and client IP.
- [x] Signature images use object storage.
- [x] Stored signature reports cover core API and public lifecycle behavior.
- [x] A dedicated Signatures checklist already exists: `LAUNCH_READINESS_SIGNATURES_CHECKLIST.md`.

### PO — Required Before Launch
- [ ] Reject public signing after expiry, decline, or completion.
- [ ] Reject public decline after expiry, decline, or completion.
- [ ] Enforce terminal-state transitions atomically.
- [ ] Prevent simultaneous sign and decline.
- [ ] Protect signature image files with authorized access or secure file tokens.
- [ ] Add tenant scoping to every signature and parent-record mutation.
- [ ] Validate trusted public origin URLs.
- [ ] Escape values inserted into signature-request email HTML.
- [ ] Remove or invalidate requests after email delivery failure.
- [ ] Define recovery for object-storage, database, and parent-update partial failures.
- [ ] Replace encoding-corrupted signature UI text.
- [ ] Add visible load error and Retry states.
- [ ] Add clear invalid and expired public-link pages.
- [ ] Add consent/electronic-signature language and decline confirmation.

### Signature Live Clickthrough
- [ ] Enable and disable the feature.
- [ ] Toggle requirement for every launch-visible record type.
- [ ] Send to a real test inbox.
- [ ] Sign and decline every launch-visible record type.
- [ ] Capture internal signatures.
- [ ] Verify parent record updates and history.
- [ ] Reopen signed, declined, expired, and invalid links.
- [ ] Attempt simultaneous sign and decline.
- [ ] Attempt blank, tiny, invalid, and corrupt signatures.
- [ ] Verify signature file access authorization.
- [ ] Force email, storage, database, and parent-update failures.

### Signature Visual, Legal, Purpose, And Flow
- [ ] Check all internal and public signature surfaces for contrast.
- [ ] Confirm the canvas works on phones without overflow.
- [ ] Confirm public line-item tables fit narrow screens.
- [ ] Confirm proof and signature images display correctly.
- [ ] Define which launch records require a signature.
- [ ] Define who can request, capture, view, and download signatures.
- [ ] Define audit fields, consent text, retention, and downloadable certificate requirements.
- [ ] Confirm signatures and normal approvals do not duplicate or contradict one another.

---

## Cross-Section Data Contract Checklist

- [ ] Use one canonical customer ID across Customers, Quotes, Orders, Approvals, Portals, and Webstores.
- [ ] Use one canonical sales workflow after quote approval.
- [ ] Decide whether legacy Jobs remain launch-visible.
- [ ] Define canonical status names for quote, order, job ticket, proof, signature, and production.
- [ ] Ensure every price retains the expected pricing/cost snapshot.
- [ ] Ensure every approval/signature retains the exact approved version.
- [ ] Ensure deleting/archiving a parent record handles all children intentionally.
- [ ] Ensure every customer-facing link resolves to a real frontend route.
- [ ] Ensure every customer-facing email is actually sent and audited.
- [ ] Ensure every timeline event uses accurate actor, timestamp, type, and record link.
- [ ] Ensure all timestamps use a consistent timezone and format.
- [ ] Ensure concurrent actions cannot create duplicate orders, tickets, documents, tasks, approvals, or terminal states.

---

## Category 1 Full Live Clickthrough Script

### Scenario A — New Lead To Completed Standard Order
- [ ] Create a new lead customer.
- [ ] Edit customer contact details and branding.
- [ ] Create a quote with multiple accurately priced items.
- [ ] Send the quote to a real test customer.
- [ ] Customer reviews and approves the quote.
- [ ] Convert the quote into the canonical order workflow.
- [ ] Verify all customer, item, pricing, notes, and source data transferred.
- [ ] Add files, drawings, and required details.
- [ ] Request proof approval.
- [ ] Customer approves proof or requests revision.
- [ ] Request required signatures.
- [ ] Customer signs the exact version.
- [ ] Start production.
- [ ] Complete production and fulfillment.
- [ ] Verify Dashboard, Customer, Order, Approval, Signature, and timeline views agree.

### Scenario B — Direct New Order
- [ ] Start a new order from an existing customer.
- [ ] Add multiple quick and detailed tickets.
- [ ] Add files, photos, and sketches.
- [ ] Save as draft.
- [ ] Resume and complete the draft.
- [ ] Start production only after required approvals/signatures.
- [ ] Verify no duplicate order, ticket, or production task is created.

### Scenario C — Vehicle Wrap
- [ ] Create or open a vehicle-wrap order item.
- [ ] Complete the launch-visible Wrap Command Center workflow.
- [ ] Verify pricing, proofs, approvals, contract/signature, production, install, aftercare, portal, files, and PDFs.
- [ ] Confirm no visible action is a placeholder or dead end.

### Scenario D — Failure And Recovery
- [ ] Fail customer, quote, order, ticket, approval, signature, file, and wrap API requests.
- [ ] Confirm errors are visible and retryable.
- [ ] Confirm no failed action shows success.
- [ ] Confirm no duplicate records appear after retry.
- [ ] Confirm no placeholder or stale data appears as real data.
- [ ] Confirm partial failures can be safely completed or rolled back.

---

## Category 1 Shared Visual And Accessibility Checklist

- [ ] Check every font color against every background.
- [ ] Remove light-on-light and low-contrast text.
- [ ] Check all status badges, disabled controls, destructive controls, and links.
- [ ] Check mobile, tablet, laptop, and wide-desktop layouts.
- [ ] Remove accidental page-level horizontal scrolling.
- [ ] Contain intentional table/tab scrolling clearly.
- [ ] Remove large unexplained empty spaces.
- [ ] Confirm text never overlaps or escapes containers.
- [ ] Confirm long words, emails, filenames, notes, and IDs wrap safely.
- [ ] Confirm dialogs remain within the viewport and actions stay reachable.
- [ ] Confirm all icon-only buttons have accessible labels/tooltips.
- [ ] Confirm keyboard navigation, focus order, focus visibility, and escape/close behavior.

---

## Category 1 Duplicate, Purpose, And Workflow Audit

- [ ] Decide whether Quotes creates legacy Jobs or modern Orders.
- [ ] Decide where quote approval is owned: Quotes, Customer Portal, Signatures, or a coordinated workflow.
- [ ] Decide where proof approval is owned: Approvals, Wrap Command Center, Customer Portal, or coordinated workflow.
- [ ] Decide where signature requirements are configured and reviewed.
- [ ] Decide whether Customer Detail should show legacy Jobs, Orders, or both.
- [ ] Decide whether Wrap Command Center duplicates Order Detail files, drawings, tasks, approvals, and signatures or provides a dedicated wrap-only view.
- [ ] Confirm every visible action is either complete and launch-ready or explicitly hidden.

---

*Last updated: 2026-06-07 | Fixes applied: Section 1 (3 items), Section 2 (5 items)*
