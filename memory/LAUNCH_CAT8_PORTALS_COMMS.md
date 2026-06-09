# Category 8: Portals, Communication, And Engagement
**Objective:** Make every launch-visible portal, form, message, and communication surface usable, secure, tenant-isolated, traceable, and recoverable.

**Sections:** Customer Portal · Employee Portal · Owner Portal · Admin Portal · Portal Messages · Portal Proofs · Portal Quotes · Portal Invoices And Payments · Portal Documents And Forms · Portal Appointments · Community Hub · Facebook Leads · Meta Integration · Email Templates · Daily Digest · Contact Support

---

## Category Readiness Summary

- [x] All 16 Category 8 sections have implemented source surfaces or clearly identified launch decisions.
- [x] Customer, employee, owner, and admin portal routes exist.
- [x] Customer portal routes cover orders, quotes, invoices, messages, proofs, forms, documents, appointments, profile, notifications, and assigned webstores.
- [x] Admin portal routes cover dashboard, conversations, documents, forms, artwork approval queue, customers, and jobs.
- [x] Facebook Leads and Meta integration have strong saved API coverage, including tenant-isolation tests.
- [x] Daily Digest has a scheduler implementation and a passing saved endpoint report.
- [x] Community Hub, email-template, portal, approvals, and appointment API behavior has partial saved test evidence.
- [ ] Do not consider Category 8 launch-ready until the confirmed security, privacy, external-service, and false-success risks below are resolved.
- [ ] Complete a role-based live clickthrough for every launch-visible portal and communication surface.
- [ ] Complete the shared visual, contrast, responsive-layout, dead-link, duplication, and workflow-order audits.

---

## Category-Wide Confirmed Launch Blockers

- [ ] Fix customer portal registration and login ambiguity: both find a customer by email only, so duplicate customer emails across tenants can select the wrong account.
- [ ] Add tenant identity or an invitation-bound registration flow to customer portal authentication.
- [ ] Add tenant ID to the customer portal JWT and verify the token tenant matches the loaded customer.
- [ ] Add tenant scope to customer portal queries and mutations that currently rely only on customer ID, conversation ID, proof ID, invoice ID, document ID, form-request ID, or notification ID.
- [ ] Fix employee portal shared/default PIN, token-scoping, pay-data, task, and job-access risks documented in Category 7.
- [ ] Verify Owner Portal identity, store ownership, and Stripe access end to end as documented in Category 6.
- [ ] Add action-specific permission checks to Admin Portal, Meta Integration, Facebook Leads, Email Templates, and Daily Digest routes; current source primarily requires only an active authenticated user.
- [ ] Fix Admin Portal enrichment and mutation queries that omit tenant scope.
- [ ] Fix public-signature and portal-file risks documented in Category 5.
- [ ] Fix Community moderation authorization and exposed user metadata before Community is launch-visible.
- [ ] Fix Daily Digest unread-message count mismatch: digest queries `shop_unread_count`, while portal/admin messaging writes and reads `unread_shop`.
- [ ] Escape or sanitize dynamic database/user content before placing it into appointment emails, Daily Digest HTML, and customized email-template output.
- [ ] Remove or redesign Meta page access-token exposure from the `/integrations/meta/pages` frontend response.
- [ ] Add expiration and cleanup for temporary Meta OAuth state/token records.
- [ ] Choose and verify one official support-email/domain convention; current source uses several different addresses and domains.

---

## Saved Test Evidence

- [x] `customer_portal_results.xml`: 28 tests, 0 failures, 0 errors, 0 skipped.
- [x] `iteration122_portal_regressions_results.xml`: 19 tests, 0 failures, 0 errors, 0 skipped.
- [x] `employee_portal_results.xml`: 17 tests, 0 failures, 0 errors, 0 skipped.
- [x] `employee_portal_v2_results.xml`: 23 tests, 0 failures, 0 errors, 0 skipped.
- [x] `admin_portal_results.xml`: 24 tests, 0 failures, 0 errors, 2 skipped.
- [x] `approvals_results.xml`: 27 tests, 0 failures, 0 errors, 0 skipped.
- [x] `portal_documents_ai_results.xml`: 11 tests, 0 failures, 0 errors, 0 skipped.
- [x] `iteration125_meta_facebook.xml`: 50 tests, 0 failures, 0 errors, 0 skipped.
- [x] `iteration126_meta_24points.xml`: 33 tests, 0 failures, 0 errors, 0 skipped.
- [x] `daily_digest_results.xml`: 16 tests, 0 failures, 0 errors, 0 skipped.
- [x] `iteration134_results.xml`: Community create/list/upvote/delete and digest settings/preview tests passed.
- [ ] Fix `onboarding_portal_invite_results.xml` failure: invited customer is missing `portal_invited_at`.
- [ ] Fix `tier7_signatures_drawings.xml` drawing update and delete failures.
- [ ] Replace the two skipped Admin Portal document-share tests with current passing fixture-backed tests.
- [ ] Replace skipped portal/signature/proof cases with current passing tests or explicitly defer those launch surfaces.

---

## Section 1 — Customer Portal

### Verified
- [x] Customer portal authentication, dashboard, profile, password-change, orders, quotes, invoices, conversations, proofs, appointments, documents, forms, notifications, and assigned-webstore routes exist.
- [x] Portal tokens require token type `portal`.
- [x] Disabled portal accounts are rejected after token authentication.
- [x] Order-detail lookup includes customer ownership and uses tenant filtering when tenant ID is available.
- [x] Appointment list includes tenant scope when the customer has a tenant ID.
- [x] Portal webstore assignment includes tenant matching and strips internal fields.

### Security And Correctness
- [ ] Replace email-only self-registration with a shop invitation, tenant slug, or other unambiguous tenant-bound flow.
- [ ] Define whether one email can access customer records in multiple shops and implement an explicit account selector if required.
- [ ] Add tenant ID to every portal token and reject customer/token tenant mismatches.
- [ ] Add tenant scope to profile reads and updates.
- [ ] Add stronger password rules than the current six-character minimum.
- [ ] Add password-reset and account-recovery flow or clearly document the support recovery process.
- [ ] Add brute-force protection and rate limiting to register, login, and password-change endpoints.
- [ ] Define portal token revocation behavior after password change or portal disable.
- [ ] Verify no portal profile response exposes internal pricing, notes, tags, audit fields, or other staff-only data.

### Live Clickthrough
- [ ] Invite a customer and verify the invitation timestamp and delivery.
- [ ] Register through the intended invitation/tenant flow.
- [ ] Log in with valid credentials and confirm the correct shop/customer account loads.
- [ ] Confirm invalid, expired, disabled, and revoked credentials show clear recovery paths.
- [ ] Open every customer portal navigation item and confirm there are no black screens or dead routes.
- [ ] Verify dashboard cards show accurate counts and link to the intended page.
- [ ] Verify profile changes persist and do not update forbidden internal fields.
- [ ] Verify password change works and prior sessions behave according to the approved revocation policy.
- [ ] Attempt cross-customer and cross-tenant access for every portal record type.

---

## Section 2 — Employee Portal

### Verified
- [x] Employee portal login, dashboard, jobs, pay, tasks, profile, and time-clock surfaces exist.
- [x] Two saved employee portal reports pass.
- [x] Portal navigation can hide pages based on employee-portal settings.

### Required Before Launch
- [ ] Remove the shared/default `1234` PIN behavior and last-four-phone fallback.
- [ ] Implement real employee PIN setup, hashing, reset, expiration, and lockout behavior.
- [ ] Make `/auth/set-pin` persist a secure PIN instead of acting as a no-op.
- [ ] Bind employee tokens to tenant ID and verify tenant on every request.
- [ ] Add tenant and employee ownership scope to pay, task, job, and mutation queries.
- [ ] Prevent employees from viewing another employee's payroll, profile, schedule, or time records.
- [ ] Prevent employees from opening or updating unassigned jobs and tasks.
- [ ] Prevent duplicate clock actions from rapid clicks or retries.
- [ ] Preserve historical payroll and time records when an employee is deactivated or deleted.
- [ ] Complete every Category 7 Employee Portal checklist item before exposing this portal.

### Live Clickthrough
- [ ] Test login, invalid PIN, lockout, reset, logout, token expiration, and disabled employee.
- [ ] Test clock in, break start, break end, clock out, refresh persistence, and duplicate-click behavior.
- [ ] Test every visible job, task, pay, profile, and schedule action with employee and nonemployee records.
- [ ] Verify mobile bottom navigation never overlaps content.

---

## Section 3 — Owner Portal

### Verified
- [x] Owner Portal signup-token and login/dashboard routes exist.
- [x] Assigned webstores can be exposed to an owner through portal surfaces.
- [x] Stripe onboarding, refresh, and dashboard-link actions exist.

### Required Before Launch
- [ ] Complete the Category 6 Owner Portal and payout checklist.
- [ ] Verify signup tokens are single-use, expiring, securely generated, and store-owner bound.
- [ ] Verify an owner can access only assigned stores and their permitted payout/analytics data.
- [ ] Verify internal tenant data, costs, margins, locked settings, and staff actions never leak to owners.
- [ ] Verify Stripe onboarding, refresh, account readiness, login-link, and disconnected states with a real connected account.
- [ ] Disable or hide Stripe actions when configuration or account readiness is incomplete.
- [ ] Define owner support and account-recovery process.

### Live Clickthrough
- [ ] Complete owner invitation/signup from a fresh token.
- [ ] Test invalid, expired, reused, and wrong-store tokens.
- [ ] Test owner login, logout, dashboard, empty state, multiple-store state, Stripe actions, and payout history.
- [ ] Attempt cross-owner and cross-tenant access.

---

## Section 4 — Admin Portal

### Verified
- [x] Admin Portal dashboard counts are tenant scoped.
- [x] Primary conversation, document, form, artwork, customer, and job lists begin with tenant-scoped queries.
- [x] Customer, document, questionnaire, and job records are tenant-validated before create/share/send actions.
- [x] Conversation close and reopen mutations include tenant scope.
- [x] A saved Admin Portal report has 22 passing and 2 skipped cases.

### Confirmed Risks And Fixes
- [ ] Add named permissions for viewing messages, sending messages, sharing documents, sending forms, and managing proofs.
- [ ] Do not allow every active authenticated employee to use all Admin Portal actions.
- [ ] Add tenant scope to conversation customer/job enrichment queries.
- [ ] Add tenant scope to shared-document document/customer enrichment queries.
- [ ] Add tenant scope to form-request customer/job enrichment queries.
- [ ] Add tenant scope to artwork-queue customer/job enrichment queries.
- [ ] Add tenant scope to conversation-message list/read mutations and conversation unread-count mutations.
- [ ] Verify a supplied `conversation_id` belongs to the supplied `customer_id` before replying through the create-conversation endpoint.
- [ ] Add tenant scope to all mutation filters even after a tenant-scoped parent lookup succeeds.
- [ ] Add audit logs for message sends, document shares, form sends, artwork sends, closes, and reopens.
- [ ] Replace skipped document-share tests with working fixtures.

### Live Clickthrough
- [ ] Open `/admin-portal` as owner, permitted employee, and unpermitted employee.
- [ ] Test every dashboard count and tab.
- [ ] Create/reply/close/reopen conversations and verify both customer and admin states.
- [ ] Share one document and bulk-share a document.
- [ ] Send a form, receive a submission, and inspect the generated record.
- [ ] Send artwork, receive approval/revision, and verify queue/status synchronization.
- [ ] Force API failures and verify no action displays false success.

---

## Section 5 — Portal Messages

### Verified
- [x] Customer can list conversations, create a conversation, list messages, and send a nonempty message.
- [x] Closed conversations reject new customer messages.
- [x] Admin can create conversations, reply, close, and reopen.
- [x] Customer and admin unread counters are updated in source.

### Required Before Launch
- [ ] Add tenant scope to customer conversation lists, detail checks, message lists, and unread mutations.
- [ ] Add tenant scope to admin conversation-message lists and unread mutations.
- [ ] Reconcile `unread_shop` and `shop_unread_count` across Portal, Admin Portal, Dashboard, and Daily Digest.
- [ ] Validate subject/content maximum lengths and supported attachment types.
- [ ] Sanitize displayed message content and filenames.
- [ ] Add file-access authorization for message attachments.
- [ ] Define message retention, deletion, and audit-history behavior.
- [ ] Define whether closed conversations can be reopened by customers.
- [ ] Add visible Retry and durable error states.

### Live Clickthrough
- [ ] Send messages in both directions and verify unread/read transitions.
- [ ] Test empty, oversized, attachment, closed, network-failure, and duplicate-submit cases.
- [ ] Verify notifications link to the correct conversation.
- [ ] Verify message lists remain usable with long histories.

---

## Section 6 — Portal Proofs

### Verified
- [x] Portal proof list, detail, version history, approve/reject/revision response, and duplicate-response prevention exist.
- [x] Admin proof queue and send-for-approval routes exist.
- [x] Saved approvals report has 27 passing cases.

### Required Before Launch
- [ ] Add tenant scope to proof lists, detail, history, job/order enrichment, and response mutation.
- [ ] Fix status-language mismatch between `changes_requested` and `revision_requested`.
- [ ] Fix Approvals frontend reminder/delete false-success behavior by checking HTTP responses.
- [ ] Enforce the advertised upload-size limit after decoding.
- [ ] Validate proof file content and format, not only supplied metadata.
- [ ] Move large proof images out of base64 database storage.
- [ ] Verify approval updates the correct parent order/job state.
- [ ] Verify notifications reach the correct customer and staff recipients.

### Live Clickthrough
- [ ] Send a first proof and a later version.
- [ ] Approve one proof and request revision on another.
- [ ] Verify status, version history, comments, notifications, and parent-record state.
- [ ] Test invalid files, oversized files, duplicate clicks, and failed network requests.

---

## Section 7 — Portal Quotes

### Verified
- [x] Customer portal quote list route exists and combines current/legacy quote sources.
- [x] Quote-related IDs can be attached to portal conversations.

### Required Before Launch
- [ ] Add a dedicated portal quote-detail flow or confirm the intended order-detail/signature path.
- [ ] Add tenant scope to all quote lookups and related enrichment.
- [ ] Verify only customer-facing quote fields are returned.
- [ ] Verify quote totals, taxes, discounts, expiration, revision, acceptance, and signature state match internal records.
- [ ] Resolve skipped quote-signature test coverage.
- [ ] Define expired, superseded, declined, and converted quote states.
- [ ] Prevent duplicate acceptance/signature actions.

### Live Clickthrough
- [ ] Open all quote states from a customer account.
- [ ] Verify quote detail, download, signature, acceptance, decline, revision, and conversion links.
- [ ] Attempt cross-customer and cross-tenant quote access.
- [ ] Verify mobile line-item tables do not overflow.

---

## Section 8 — Portal Invoices And Payments

### Verified
- [x] Portal invoice list, viewed marker, PDF download, and Stripe Checkout creation routes exist.
- [x] Payment creation verifies that the invoice belongs to the portal customer.
- [x] Stripe Checkout metadata includes invoice, tenant, customer, and fee information.
- [x] Paid invoices reject another payment-session creation.

### Required Before Launch
- [ ] Add tenant scope to invoice reads, viewed mutation, payment creation, and PDF download.
- [ ] Validate `origin_url` against an approved frontend-origin allowlist before constructing Stripe return URLs.
- [ ] Use decimal-safe amount conversion and define rounding rules before converting dollars to cents.
- [ ] Do not return raw Stripe exception details to portal customers.
- [ ] Verify webhook/payment-status logic marks the correct invoice paid exactly once.
- [ ] Verify refunds, disputes, partial payments, duplicate sessions, abandoned sessions, and expired sessions.
- [ ] Verify invoice PDF totals and line items match the authoritative invoice.
- [ ] Verify disconnected or incomplete Stripe accounts show a customer-safe message.

### Live Clickthrough
- [ ] View and download an invoice.
- [ ] Complete a real test-mode payment through a connected account.
- [ ] Cancel a payment and confirm the invoice remains unpaid.
- [ ] Refresh after payment and confirm the correct status.
- [ ] Attempt cross-customer and cross-tenant invoice access.

---

## Section 9 — Portal Documents And Forms

### Verified
- [x] Portal document list/detail and form list/detail/submit routes exist.
- [x] Required questionnaire fields are validated before portal submission.
- [x] Form submission creates a response, text document, portal document, request completion state, and notification.
- [x] Admin Portal can send forms and share documents.

### Required Before Launch
- [ ] Add tenant scope to portal-document, underlying-document, form-request, questionnaire, response, and update queries.
- [ ] Do not return internal/private document fields or inaccessible internal file URLs to portal customers.
- [ ] Add an authorized download/preview endpoint for every portal document type.
- [ ] Prevent duplicate form submissions after completion unless resubmission is explicitly allowed.
- [ ] Validate all answer types, lengths, file uploads, and changed questionnaire schemas.
- [ ] Escape/sanitize user answers before generated documents or staff display.
- [ ] Define document acknowledgment behavior and expose it consistently.
- [ ] Complete Category 5 document, form, signature, file-security, and retention items.

### Live Clickthrough
- [ ] Share, view, download, acknowledge, and revoke a document.
- [ ] Send and complete every launch-used question type.
- [ ] Verify completed forms become read-only or clearly support approved resubmission.
- [ ] Attempt cross-customer and cross-tenant document/form access.

---

## Section 10 — Portal Appointments

### Verified
- [x] Portal appointment list and request routes exist.
- [x] Appointment list can include requested appointments in upcoming results.
- [x] Saved appointment request/confirm/reject flow tests passed in `iteration134_results.xml`.
- [x] Appointment requests notify the shop in-app and attempt an owner email.

### Required Before Launch
- [ ] Validate preferred date and time formats instead of constructing timestamps from unchecked strings.
- [ ] Reject past dates, invalid times, invalid/negative durations, and excessive durations.
- [ ] Verify a supplied `order_id` belongs to the portal customer and tenant.
- [ ] Escape customer name, email, location, and description before adding them to appointment email HTML.
- [ ] Replace blank or incorrect appointment-dashboard URLs with a verified production URL.
- [ ] Define timezone behavior for customer, tenant, email, and staff calendar.
- [ ] Define cancellation, reschedule, confirmation, rejection, and reminder behavior.
- [ ] Show the customer a visible warning if the request saves but owner email delivery fails only when appropriate.

### Live Clickthrough
- [ ] Request each appointment type and verify staff receives it.
- [ ] Confirm, reject, reschedule, cancel, and remind from the staff side.
- [ ] Verify customer-facing status and times after each action.
- [ ] Test mobile date/time controls and invalid input.

---

## Section 11 — Community Hub

### Verified
- [x] Community list/detail, create, reply, upvote, search, filters, stats, moderation fields, and support link exist.
- [x] Four Community API lifecycle actions passed in saved evidence.
- [x] Post authors and owners can delete through the API.

### Confirmed Security And Privacy Defects
- [ ] Restrict status and `is_answered` changes to an explicit moderator/platform-admin permission.
- [ ] Remove the hard-coded owner email used to identify official replies.
- [ ] Remove `author_email`, `author_tenant_id`, and complete `upvoted_by` arrays from normal reader responses.
- [ ] Return a per-user `has_upvoted` value instead of exposing voter IDs.
- [ ] Decide and document whether Community is app-wide or tenant-scoped.
- [ ] Add privacy and moderation-authorization tests for the approved model.

### Reliability, Purpose, And Live Clickthrough
- [ ] Add visible load/action errors and Retry actions.
- [ ] Add pagination/load-more beyond the current 50-post limit.
- [ ] Add backend length limits, whitespace rejection, sanitization, rate limits, spam handling, and reporting.
- [ ] Clarify the difference between Community, private portal messages, and Contact Support.
- [ ] Clarify Answered, Resolved, and Closed so they do not overlap.
- [ ] Test every category, filter, search, reply, upvote, delete, moderation, and support action.

---

## Section 12 — Facebook Leads

### Verified
- [x] Facebook message list, detail, stats, process, suggest-reply, create-lead, create-draft-order, mark-reviewed, and mark-spam routes exist.
- [x] Main list/detail/action queries include tenant scope.
- [x] Saved Meta/Facebook reports contain 83 passing tests.
- [x] Saved tests cover message tenant isolation, cross-tenant create-lead rejection, webhook routing, AI processing, lead creation, draft-order creation, and review actions.

### Required Before Launch
- [ ] Add named permissions for viewing messages, running AI, creating leads/orders, marking reviewed, and marking spam.
- [ ] Add tenant scope to internal update filters that currently update by message ID only.
- [ ] Prevent duplicate lead or draft-order creation from repeated clicks/retries.
- [ ] Clearly label AI classification, extracted values, and suggested replies as unverified until staff review.
- [ ] Define handling for attachments, unsupported messages, deleted messages, and Meta API failures.
- [ ] Verify created leads/orders enter the correct workflow without bypassing required data.
- [ ] Define retention and privacy policy for raw Meta payloads, message text, sender IDs, and attachments.

### Live Clickthrough
- [ ] Receive a real sandbox/test-page message through Meta webhook.
- [ ] Review message, rerun processing, suggest reply, create lead, and create draft order.
- [ ] Mark reviewed/spam and verify list/stats updates.
- [ ] Test failure, duplicate-click, low-confidence, and attachment-only cases.

---

## Section 13 — Meta Integration

### Verified
- [x] Meta status, OAuth start/callback, page list/connect/disconnect/settings, webhook verification, and webhook receiver routes exist.
- [x] OAuth state is stored and consumed during callback.
- [x] Stored page access tokens are encrypted.
- [x] Status responses exclude encrypted page tokens.
- [x] Webhook signatures are verified and duplicate messages are ignored.
- [x] Saved tests cover tenant isolation and core connection/webhook behavior.

### Required Before Launch
- [ ] Add an explicit integration-management permission to connect, disconnect, and change page settings.
- [ ] Stop returning raw page access tokens to the browser from the available-pages endpoint; exchange/connect server-side.
- [ ] Add expiration timestamps and cleanup for `meta_oauth_states` and `meta_oauth_tokens`.
- [ ] Validate `create_mode`, confidence threshold range, and default assignee tenant membership.
- [ ] Enforce global uniqueness or deterministic conflict handling for a Facebook page connected to multiple tenants.
- [ ] Add tenant scope to internal page/message update filters even when page ID is expected to be unique.
- [ ] Define token refresh, token expiration, revoked permissions, disconnected pages, and webhook-subscription failure behavior.
- [ ] Verify required production environment variables, redirect URLs, webhook URL, app review permissions, and encryption key.
- [ ] Decide whether invalid webhook signatures should return 200 or an error, and document the monitoring/retry tradeoff.

### Live External-Service Verification
- [ ] Complete OAuth with the production Meta app and a test page.
- [ ] Connect, configure, disconnect, and reconnect the page.
- [ ] Receive signed webhook events and verify correct-tenant routing.
- [ ] Revoke access in Meta and verify the app shows a recoverable disconnected state.
- [ ] Confirm no token appears in browser logs, URLs, analytics, or normal API responses.
- [ ] Hide Meta/Facebook launch navigation until this full external-service flow passes.

---

## Section 14 — Email Templates

### Verified
- [x] Tenant-scoped list, get, update, reset, and preview routes exist.
- [x] Default templates and tenant customizations are merged.
- [x] Saved email-template list/get/update/preview cases passed in `iteration134_results.xml`.

### Required Before Launch
- [ ] Add an explicit permission for viewing and editing customer-facing email templates.
- [ ] Fix preview tenant lookup, which queries `tenants` by `tenant_id` while other source uses tenant `id`.
- [ ] Sanitize or constrain editable HTML before sending or previewing it.
- [ ] Escape variable values before inserting user/customer data into HTML templates.
- [ ] Define allowed tags, attributes, links, images, styles, and variables.
- [ ] Validate subject and HTML size limits.
- [ ] Verify reset confirmation, update errors, and preview errors cannot show false success.
- [ ] Send every launch-used template through the production email provider and inspect major email clients.
- [ ] Verify links, branding, logo, colors, attachments, conditional blocks, and missing-variable fallback.

### Live And Visual QA
- [ ] Preview each default and customized template.
- [ ] Test missing, long, malicious, and unexpected variable values.
- [ ] Test Gmail, Outlook, desktop, mobile, dark mode, and images-disabled rendering.
- [ ] Verify editor and preview fit without horizontal scrolling or overlapping controls.
- [ ] Verify all buttons, links, resets, and navigation actions work.

---

## Section 15 — Daily Digest

### Verified
- [x] Preview, manual send, settings, and history routes exist.
- [x] A background scheduler checks enabled digest settings every minute.
- [x] Digest data is tenant scoped for employees, schedules, invoices, jobs, approvals, revenue, messages, settings, and history.
- [x] Saved Daily Digest report has 16 passing tests.

### Required Before Launch
- [ ] Fix unread-message count to use the same canonical field as Portal/Admin Portal.
- [ ] Escape employee, job, customer, company, and other dynamic values before rendering digest HTML.
- [ ] Add explicit permission checks for preview, send, settings, and history.
- [ ] Validate schedule-time format and recipient email addresses in the backend.
- [ ] Prevent duplicate scheduled sends when multiple application instances run the scheduler.
- [ ] Add a per-tenant/date idempotency key and verify retry behavior.
- [ ] Define tenant timezone instead of requiring users to reason only in UTC.
- [ ] Verify scheduler starts in production and is monitored.
- [ ] Verify disabled settings, no-recipient settings, partial send failures, and provider outages.
- [ ] Verify digest totals against authoritative dashboard/report totals.

### Live Clickthrough
- [ ] Preview with empty, normal, and large datasets.
- [ ] Add/remove recipients and validate bad addresses.
- [ ] Send manually and verify history/results.
- [ ] Schedule a near-future send and confirm exactly one delivery.
- [ ] Inspect the email on mobile and desktop clients for overflow, contrast, and broken layout.

---

## Section 16 — Contact Support

### Verified
- [x] Community Hub includes a Contact Support mailto link.
- [x] Navigation includes a Contact Support mailto action.
- [x] Account Suspended, documentation, legal, privacy, data-deletion, and contact pages contain support/contact links.

### Confirmed Consistency Risks And Required Work
- [ ] Choose one official support address and one official domain convention.
- [ ] Reconcile current variants including `thesigntistslab@gmail.com`, `donnell@signguy-ai.com`, `support@signguy.ai`, `support@signguyai.com`, and privacy-specific addresses.
- [ ] Verify every visible support address exists, is monitored, and has an owner/SLA.
- [ ] Decide when users should use private portal messages, Community, public Contact, or email support.
- [ ] Add a non-mailto fallback for users without a configured mail client.
- [ ] Include useful account/tenant context without exposing sensitive data.
- [ ] Verify suspended users and unauthenticated users can reach support.
- [ ] Remove dead `/contact-support` path assumptions if the action is only a mailto link.

### Live Clickthrough
- [ ] Click every support/contact link from every role and public page.
- [ ] Verify recipient, subject, body, and fallback behavior.
- [ ] Send a test request and confirm receipt, routing, and response ownership.

---

## Shared Visual, Layout, Accessibility, And Purpose Audit

Complete for every Category 8 page, dialog, email, empty state, error state, and role.

- [ ] Check every font color against its background; remove light-on-light and low-contrast text.
- [ ] Verify badges, muted text, placeholders, disabled controls, links, and focus indicators meet contrast requirements.
- [ ] Test mobile, tablet, laptop, desktop, and wide-desktop widths.
- [ ] Remove accidental horizontal scrolling.
- [ ] Verify intentional horizontal navigation has visible affordance and does not hide critical actions.
- [ ] Remove large empty spaces caused by missing data, failed requests, fixed heights, or uneven columns.
- [ ] Verify long names, subjects, emails, filenames, URLs, messages, and table values wrap without overlap.
- [ ] Verify bottom navigation, sticky headers, dialogs, toasts, and keyboards do not cover content.
- [ ] Verify loading, empty, error, forbidden, expired, disconnected, and completed states are useful and never black screens.
- [ ] Verify every button and link works, has a clear result, and serves a launch purpose.
- [ ] Remove, hide, or disable actions that are incomplete, unavailable, duplicated, or permission-forbidden.
- [ ] Verify external links open safely and mailto links have a fallback.
- [ ] Verify destructive actions require confirmation and cannot be triggered twice.
- [ ] Verify forms preserve typed input after recoverable failures.
- [ ] Check keyboard navigation, focus order, labels, announcements, and touch-target sizes.

---

## Duplicate, Overlap, And Workflow Audit

- [ ] Define the purpose and owner of Customer Portal messages, Admin Portal messages, Community, Contact Support, and public Contact.
- [ ] Define the purpose and owner of Admin Portal approvals versus the standalone Approvals page.
- [ ] Define the purpose and owner of portal documents/forms versus Document Library sharing/forms.
- [ ] Define the purpose and owner of Portal Appointments versus internal Appointments.
- [ ] Define the purpose and owner of Facebook Leads versus normal Leads/Customers/Orders.
- [ ] Confirm Owner Portal and Customer Portal webstore-owner views do not duplicate or contradict each other.
- [ ] Confirm quote, proof, signature, invoice, and payment actions appear in the best customer workflow order.
- [ ] Confirm notifications take each role directly to the correct action, not only a general dashboard.
- [ ] Remove duplicate status names and contradictory state transitions.
- [ ] Confirm each workflow has a clear start, next action, completion state, and recovery path.

---

## Required Automated-Test Completion

- [ ] Add customer portal duplicate-email/multi-tenant authentication tests.
- [ ] Add customer portal token-tenant mismatch and endpoint-by-endpoint cross-tenant tests.
- [ ] Add employee portal PIN, token, pay, task, job, and mutation isolation tests.
- [ ] Add Owner Portal token, ownership, and Stripe state tests.
- [ ] Add Admin Portal permission and tenant-scoped enrichment/mutation tests.
- [ ] Add portal-message unread-field consistency and attachment authorization tests.
- [ ] Add proof status synchronization and file-validation tests.
- [ ] Add quote detail/signature/state tests.
- [ ] Add invoice origin allowlist, rounding, webhook idempotency, and cross-tenant tests.
- [ ] Add portal document/form duplicate-submit, schema-change, and secure-download tests.
- [ ] Add portal appointment validation, order ownership, timezone, and email escaping tests.
- [ ] Add Community moderation, privacy, input, pagination, and abuse tests.
- [ ] Add Facebook Leads duplicate-action, permission, and raw-data privacy tests.
- [ ] Add Meta OAuth temp-token expiration, permission, validation, and production-contract tests.
- [ ] Add email-template permission, HTML safety, variable escaping, and delivery tests.
- [ ] Add Daily Digest canonical unread count, HTML escaping, scheduler idempotency, timezone, and provider-failure tests.
- [ ] Add support-link route/address consistency tests.
- [ ] Add responsive visual tests and role-based browser clickthrough tests for every launch-visible section.

---

## Exact Category 8 Work Order

- [ ] 1. Fix customer and employee portal identity, tenant binding, and cross-record authorization.
- [ ] 2. Fix public signature/file access and portal document/form tenant scope.
- [ ] 3. Add Admin Portal and communication-management permissions.
- [ ] 4. Fix Admin Portal and customer portal unscoped enrichment/mutation queries.
- [ ] 5. Fix Community moderation authorization and response privacy.
- [ ] 6. Fix invoice/payment origin, amount, webhook, and cross-tenant behavior.
- [ ] 7. Fix Meta token exposure/temp-token lifecycle and complete production Meta verification.
- [ ] 8. Fix Daily Digest unread field, escaping, scheduler idempotency, and timezone behavior.
- [ ] 9. Sanitize/escape appointment emails and email-template content/variables.
- [ ] 10. Standardize support addresses, channels, and fallback behavior.
- [ ] 11. Complete missing automated tests and replace failed/skipped reports.
- [ ] 12. Complete role-based live clickthrough for all portals and communication actions.
- [ ] 13. Complete visual, responsive, accessibility, dead-link, duplicate, and workflow-order audits.
- [ ] 14. Hide any external-service or portal surface that has not passed its launch gate.

---

## Category 8 Launch Gates

- [ ] No portal or communication endpoint can access another tenant's records.
- [ ] Every portal identity type has secure setup, recovery, expiration, revocation, and role boundaries.
- [ ] Every staff communication/admin action has an approved permission.
- [ ] Public tokens and files expose only the intended record and expire appropriately.
- [ ] Community moderation and privacy model is approved and tested.
- [ ] Meta, Stripe, email provider, and scheduled digest flows pass production-like external-service verification.
- [ ] All failed and skipped Category 8 test evidence is resolved or the affected surface is hidden.
- [ ] Every launch-visible button, link, form, dialog, and workflow passes live clickthrough.
- [ ] No dead links, black screens, false-success messages, low-contrast text, horizontal overflow, or excessive empty spaces remain.
- [ ] Duplicate/overlapping surfaces have clear purposes and workflows appear in the best logical order.
- [ ] Product owner approves the final Category 8 launch scope and accepted risks.
