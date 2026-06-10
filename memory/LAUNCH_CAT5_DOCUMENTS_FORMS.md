# Category 5: Documents, Forms, And Business Records
**Objective:** Make every launch-visible document, form, questionnaire, signature, and business record usable, secure, tenant-isolated, traceable, and recoverable.

**Sections:** Document Library · Document Upload And Download · Document Templates · AI-Created Documents · Questionnaires · Public Questionnaires · Customer Forms · Document Signatures · Record Retention And History

---

## Category Readiness Summary

- Source review: completed for all nine sections
- Stored test review: completed for available document, questionnaire, signature, and portal reports
- Authenticated live clickthrough: **not yet completed**
- Visual and responsive review: **not yet completed**

---

## Section 1 — Document Library

### Verified Structure And Behavior
- [x] Route `/documents` exists.
- [x] Documents page has a stable `documents-page` test identifier.
- [x] Documents page loads documents and document statistics.
- [x] Documents page supports search.
- [x] Documents page supports category filtering.
- [x] Documents page supports templates-only filtering.
- [x] Documents page has an Upload Document action.
- [x] Documents page has an AI Document Creator action.
- [x] Documents page has document detail.
- [x] Documents page supports download.
- [x] Documents page supports archive.
- [x] Documents page supports template toggling.
- [x] Documents page supports sending by email.
- [x] Documents page supports sending to a customer portal.
- [x] Documents can link to jobs and customers through backend endpoints.
- [x] Document activity records are created for email and portal sends.
- [x] Stored `portal_documents_ai_results.xml` report has 11 passing tests.

### P0 Authorization And Tenant Isolation
- [ ] Define document view, upload, edit, archive, link, send, and template-management permissions.
- [ ] Enforce document view permission on list, stats, detail, download, categories, and customer-document endpoints.
- [ ] Enforce document manage permission on upload, update, archive, link, unlink, send, AI-save, template population, seeding, and PDF generation.
- [ ] Add tenant scope to the final lookup after document update.
- [ ] Add tenant scope to document link update.
- [ ] Add tenant scope to document unlink update.
- [ ] Add tenant scope when linking a document after email delivery.
- [ ] Add tenant scope when linking a document after portal delivery.
- [ ] Verify customer, job, and document relationships cannot cross tenants.
- [ ] Add API tests proving one tenant cannot read, download, update, archive, link, unlink, send, or list another tenant's documents.
- [ ] Add API tests proving employees without document permissions cannot call management endpoints directly.

### P0 Functional And Data Integrity
- [ ] Confirm search includes exactly the intended fields: name, description, tags, customer, and linked job.
- [ ] Confirm category counts match active documents.
- [ ] Confirm storage-used statistics include object-storage and legacy documents correctly.
- [ ] Confirm linked customers and jobs are visible and manageable in the UI.
- [ ] Add an intentional restore flow for archived documents or clearly state that archive is not recoverable from the UI.
- [ ] Prevent repeated portal-send clicks from creating duplicate portal document entries unless duplicates are intentional.
- [ ] Record delivery outcome, recipient, sender, time, and failure details consistently.
- [ ] Confirm failed email or portal delivery does not display false success.
- [ ] Confirm document details never expose raw storage paths or internal-only metadata.

### Live Clickthrough
- [ ] Open `/documents` as an authorized owner.
- [ ] Open `/documents` as an employee with intended permissions.
- [ ] Confirm the page loads without a blank or black screen.
- [ ] Confirm loading, empty, populated, and error states are understandable.
- [ ] Search by document name.
- [ ] Search by description.
- [ ] Search by tag.
- [ ] Test every category filter.
- [ ] Test templates-only filter.

---

## Section 2 — Document Upload And Download

### Verified Structure And Behavior
- [x] Backend has `POST /api/documents`.
- [x] Backend has `GET /api/documents/{document_id}/download`.
- [x] Frontend and backend enforce a 10MB upload limit.
- [x] Backend restricts uploads to a defined MIME-type allowlist.
- [x] Allowed types include PDF, common images, Word, Excel, plain text, and CSV.
- [x] New document files are stored in object storage.
- [x] Legacy base64 documents can migrate to object storage during access.
- [x] Object-storage paths include tenant and document identifiers.
- [x] Stored `iteration92_object_storage_results.xml` report has 19 passing tests.
- [x] Stored AI document workflow report verifies AI-created document download.

### P0 File Security And Reliability
- [ ] Verify file content matches the declared MIME type instead of trusting only the upload header.
- [ ] Decide whether to scan uploaded files for malware.
- [ ] Reject executable, scriptable, corrupt, and disguised files.
- [ ] Verify SVG, HTML, and other active content cannot execute in any preview surface.
- [ ] Normalize filenames and prevent unsafe path characters.
- [ ] Confirm object-storage keys cannot be manipulated by user input.
- [ ] Confirm object-storage credentials and raw paths never reach clients.
- [ ] Confirm one tenant cannot retrieve another tenant's object-storage file.
- [ ] Define encryption-at-rest and backup requirements.
- [ ] Define behavior when object storage succeeds but database insertion fails.
- [ ] Define behavior when database insertion succeeds but object storage fails.
- [ ] Define behavior when legacy-file migration fails.
- [ ] Log failed uploads and downloads without logging file contents or secrets.

### Live Upload And Download Matrix
- [ ] Upload a valid PDF.
- [ ] Upload valid PNG, JPG, WEBP, and GIF images.
- [ ] Upload valid DOC and DOCX files.
- [ ] Upload valid XLS, XLSX, TXT, and CSV files.
- [ ] Reject a disallowed file type.
- [ ] Reject a disguised file with an allowed extension.
- [ ] Reject a file larger than 10MB.
- [ ] Test a zero-byte file.
- [ ] Test a corrupt file.
- [ ] Test duplicate filenames.
- [ ] Test filenames with spaces and special characters.
- [ ] Download every supported type.
- [ ] Confirm every downloaded file opens and is not corrupted.
- [ ] Confirm the downloaded filename and MIME type are correct.
- [ ] Confirm download failure presents a clear recoverable error.
- [ ] Confirm users cannot download files after losing access.

### Customer Portal File Access
- [ ] Replace portal View and Download behavior that opens the internal `document.file_url` without attaching the portal token.
- [ ] Add or verify an authenticated portal document-content endpoint.
- [ ] Confirm portal users can retrieve only documents shared with their customer account.
- [ ] Confirm portal document links cannot be reused after access is revoked.
- [ ] Confirm portal View records `viewed_at` only after successful access.
- [ ] Confirm View and Download do not report success before the file actually opens.
- [ ] Confirm portal links never expose another customer's document ID or metadata.

---

## Section 3 — Document Templates

### Verified Structure And Behavior
- [x] Documents can be marked as templates.
- [x] Documents page can filter to templates only.
- [x] Backend supports template population.
- [x] Backend supports seeding default templates.
- [x] Template population can use tenant, customer, and job variables.
- [x] Seed logic checks for existing tenant templates before creating defaults.

### P0 Template Accuracy And Safety
- [ ] Inventory every default template intended for launch.
- [ ] Assign an owner to approve each template's wording and fields.
- [ ] Verify every variable resolves from the intended source.
- [ ] Handle missing customer, job, tenant, date, and pricing variables clearly.
- [ ] Prevent one tenant's data from populating another tenant's template.
- [ ] Confirm generated documents copy template content instead of sharing a mutable source unexpectedly.
- [ ] Confirm changes to a template do not alter already-created records.
- [ ] Add template version identifiers.
- [ ] Record which template version produced each generated document.
- [ ] Define whether generated documents remain editable.
- [ ] Define whether signed or sent generated documents become immutable.
- [ ] Verify repeated default-template seeding is idempotent.

### Template Live Clickthrough
- [ ] Seed default templates in a clean tenant.
- [ ] Seed defaults again and confirm no duplicates.
- [ ] Mark a normal document as a template.
- [ ] Remove template status.
- [ ] Generate from every launch template with a customer and job.
- [ ] Generate from every launch template without optional values.
- [ ] Confirm all variables render correctly.
- [ ] Confirm formatting is readable in generated output.
- [ ] Confirm generated output can be downloaded, sent, archived, and signed where intended.
- [ ] Confirm users can identify the source template and version.

---

## Section 4 — AI-Created Documents

### Verified Structure And Behavior
- [x] Documents page links to AI Document Creator.
- [x] Backend has `POST /api/documents/from-ai`.
- [x] Backend has document PDF generation.
- [x] AI-created text documents are stored in object storage.
- [x] Backend includes marketing and branding output categories.
- [x] Stored `ai_document_workflow_results.xml` report has 13 passing tests.
- [x] Saved tests cover PDF generation, saving, persistence, multiple categories, download, and portal send.

### Confirmed Category Contract Defect
- [ ] Add frontend category options for `marketing_content`.
- [ ] Add frontend category options for `social_post`.
- [ ] Add frontend category options for `content_calendar`.
- [ ] Add frontend category options for `campaign_plan`.
- [ ] Add frontend category options for `blog_article`.
- [ ] Add frontend category options for `logo_concept`.
- [ ] Add frontend category options for `brand_kit`.
- [ ] Add frontend category options for `tagline`.
- [ ] Confirm AI-created documents no longer display as Other when they have a specific category.
- [ ] Confirm users can filter every backend-supported category.

### AI Content Quality And Governance
- [ ] Clearly label AI-generated drafts before human approval.
- [ ] Require human review before sending legal, financial, customer-facing, or brand-sensitive AI documents.
- [ ] Define which AI document types are allowed at launch.
- [ ] Hide unfinished AI document types.
- [ ] Confirm generated content does not invent customer, job, price, legal, or policy facts.
- [ ] Confirm generated documents do not expose data from another tenant or unrelated record.
- [ ] Record generation time, generating user, source context, and model/tool where required.
- [ ] Define whether prompts and generated content are retained.
- [ ] Add a correction and regeneration workflow.
- [ ] Confirm AI failures show a useful error instead of creating blank documents.

### AI Document Live Clickthrough
- [ ] Open AI Document Creator from Documents.
- [ ] Generate every launch-visible document type.
- [ ] Save every launch-visible type to the library.
- [ ] Confirm category, filename, MIME type, and content are correct.
- [ ] Download and open generated output.
- [ ] Generate PDF output with headings, lists, long text, and special characters.
- [ ] Confirm no blank pages, clipped content, or mojibake.
- [ ] Send approved AI output by email and portal.
- [ ] Confirm users cannot accidentally send an unreviewed draft.

---

## Section 5 — Questionnaires

### Verified Structure And Behavior
- [x] Route `/questionnaires` exists.
- [x] Backend supports list, templates, create-from-template, create, detail, update, delete, and duplicate.
- [x] Backend supports draft, active, and archived statuses.
- [x] Backend supports response list, response detail, and response deletion.
- [x] Backend supports questionnaire email sending.
- [x] Email endpoint rejects draft questionnaires.
- [x] Email payload validates recipient email format.
- [x] Stored `questionnaires_results.xml` report has 24 passing tests.
- [x] Stored `questionnaire_send_email.xml` report has 12 passing tests.
- [x] Stored `iteration155_questionnaire_results.xml` report has 23 passing tests.

### P0 Confirmed Page And Delivery Bugs
- [ ] Import or destructure `fetchCustomers` before calling it in `Questionnaires.js`.
- [ ] Import or destructure `customers` before rendering it in `Questionnaires.js`.
- [ ] Confirm `/questionnaires` no longer throws a runtime error or displays a black screen.
- [ ] Replace `POST /api/questionnaires/{id}/send-to-portal` with the implemented `POST /api/admin-portal/forms/send` contract, or remove the portal-send option.
- [ ] Map the Questionnaire send dialog fields to the implemented form-request fields.
- [ ] Decide whether the admin-portal form-send endpoint should support notification controls and messages.
- [ ] Implement `require_signature` end to end or remove the switch and all related success text.
- [ ] Remove unsupported `require_signature` from the questionnaire email payload until implemented.
- [ ] Fix mojibake in questionnaire UI and email plain text.

### P0 Authorization, Tenant Isolation, And Data Integrity
- [ ] Define questionnaire view, create, edit, publish, send, response-view, and response-delete permissions.
- [ ] Enforce those permissions on backend endpoints.
- [ ] Add tenant scope to questionnaire update.
- [ ] Add tenant scope to the post-update questionnaire lookup.
- [ ] Add tenant scope to questionnaire response-count increments and decrements.
- [ ] Add tenant scope to response deletion.
- [ ] Add tenant scope when loading questionnaire labels for a response.
- [ ] Scope response-list query by tenant as defense in depth.
- [ ] Prevent response count from becoming negative.
- [ ] Define behavior when a questionnaire is changed after responses exist.
- [ ] Preserve the exact question/version context used for each response.
- [ ] Add cross-tenant and unauthorized-role tests for all questionnaire mutations and responses.

### Builder And Management Clickthrough
- [ ] Open `/questionnaires`.
- [ ] Confirm loading, empty, populated, and error states.
- [ ] Create a questionnaire from scratch.
- [ ] Create from every launch template.
- [ ] Add every launch-supported question type.
- [ ] Add and remove options.
- [ ] Reorder questions and confirm order persists.
- [ ] Edit name, description, category, questions, and thank-you message.
- [ ] Duplicate a questionnaire.
- [ ] Activate, deactivate, and archive a questionnaire.
- [ ] Confirm only active questionnaires can be shared.
- [ ] Send an active questionnaire by email.
- [ ] Confirm a draft cannot be sent.
- [ ] View responses.
- [ ] Delete a response and confirm count remains accurate.
- [ ] Confirm every button and action works and serves a purpose.

### Builder Visual And Flow QA
- [ ] Confirm the builder is usable without horizontal scrolling.
- [ ] Confirm long questions and option text do not overlap controls.
- [ ] Confirm dialogs remain usable on mobile and tablet.
- [ ] Check badges, tabs, switches, inputs, helper text, and disabled states for contrast.
- [ ] Remove large empty spaces in templates, empty lists, and response dialogs.
- [ ] Confirm Create, Edit, Publish, Send, Responses, Duplicate, and Delete appear in a logical order.
- [ ] Confirm questionnaire actions do not duplicate Customer Forms actions confusingly.

---

## Section 6 — Public Questionnaires

### Verified Structure And Behavior
- [x] Public route `/questionnaire/:questionnaireId` exists.
- [x] Backend public view returns only active questionnaires.
- [x] Backend public response submission exists.
- [x] Required fields are validated.
- [x] Email and phone formats are validated.
- [x] Public responses record questionnaire, answers, optional customer/job/webstore context, submission time, and IP.
- [x] Public questionnaire saved tests cover active access, submission, required fields, and email validation.

### P0 Public Access And Abuse Protection
- [ ] Decide whether public questionnaire IDs are sufficiently unguessable or replace them with revocable share tokens.
- [ ] Add expiry, revoke, or close behavior where a public link should stop accepting responses.
- [ ] Add rate limiting.
- [ ] Add abuse, spam, and bot controls appropriate for launch exposure.
- [ ] Validate every answer against expected type, length, allowed options, and size.
- [ ] Reject answers for unknown question IDs when appropriate.
- [ ] Sanitize displayed answers and user-provided text.
- [ ] Implement file-upload questions end to end or hide them.
- [ ] Implement signature questions end to end or hide them.
- [ ] Confirm public response metadata cannot associate a response with another tenant's customer, job, or webstore.
- [ ] Define duplicate-submission behavior.
- [ ] Define consent and privacy notice requirements.

### Public Questionnaire Live Clickthrough
- [ ] Copy an active public share link.
- [ ] Open it in a logged-out browser.
- [ ] Confirm draft and archived questionnaires are unavailable.
- [ ] Submit every supported field type.
- [ ] Confirm required fields are enforced.
- [ ] Confirm invalid email and phone values are rejected.
- [ ] Test very long values and unexpected input.
- [ ] Confirm thank-you message displays correctly.
- [ ] Confirm the internal response appears once and is accurate.
- [ ] Confirm browser refresh does not accidentally duplicate a response.
- [ ] Confirm invalid, revoked, or unavailable links show a useful page.

### Public Visual And Accessibility QA
- [ ] Check all font, field, helper, error, and button colors for contrast.
- [ ] Confirm keyboard navigation and visible focus.
- [ ] Confirm labels and required states are accessible.
- [ ] Confirm error messages identify the affected fields.
- [ ] Confirm mobile layout has no horizontal scrolling.
- [ ] Confirm long questionnaires remain navigable and do not create unusable empty space.
- [ ] Confirm submission controls remain reachable.

---

## Section 7 — Customer Forms

### Verified Structure And Behavior
- [x] Customer portal route `/customer-portal/forms` exists.
- [x] Customer portal route `/customer-portal/forms/:requestId` exists.
- [x] Admin endpoint lists tenant portal form requests.
- [x] Admin endpoint `POST /api/admin-portal/forms/send` creates a portal form request.
- [x] Admin send verifies customer, questionnaire, and optional job tenant ownership.
- [x] Admin send creates a customer notification.
- [x] Portal form list supports status filtering.
- [x] Portal form detail loads the request, questionnaire, and existing response.
- [x] Completed forms become read-only in the portal UI.
- [x] Portal supports text, textarea, number, select, radio, checkbox, and multi-select inputs.
- [x] Stored `customer_portal_forms_results.xml` report has 19 tests with 18 passing and 1 skipped.

### P0 Confirmed Integration And Data Defects
- [ ] Connect the internal Questionnaire send dialog to the implemented admin form-send endpoint.
- [ ] Add tenant scope to customer and job enrichment queries in the admin form-request list.
- [ ] Verify all portal form list, detail, and submission queries scope by the authenticated portal customer's tenant and customer ID.
- [ ] Verify a portal customer cannot open another customer's form request by changing the URL ID.
- [ ] Verify submitted answers cannot be modified after completion unless reopening is explicit.
- [ ] Validate required questions and allowed answer values on portal submission.
- [ ] Confirm portal form submission cannot create duplicate responses during retries.
- [ ] Confirm portal form submission's related generated document is accurate and linked correctly.
- [ ] Decide and implement overdue-status calculation.
- [ ] Decide and implement cancellation, reminder, resend, reopen, and correction behavior.
- [ ] Replace the skipped portal proof fixture before treating the broader report as complete.

### Customer Form Live Clickthrough
- [ ] Send a form request from the internal app.
- [ ] Confirm the intended customer receives a portal notification.
- [ ] Confirm the request appears under Pending.
- [ ] Confirm due date and instructions display correctly.
- [ ] Open the request from the notification and Forms list.
- [ ] Complete every supported field type.
- [ ] Submit the form.
- [ ] Confirm the request moves to Completed.
- [ ] Confirm the completed response is read-only and accurate.
- [ ] Confirm internal staff can find and review the completed response.
- [ ] Test expired, overdue, cancelled, duplicate, and already-completed requests.
- [ ] Confirm errors do not silently redirect customers away from recoverable work.

### Customer Form Visual, Layout, Purpose, And Flow
- [ ] Fix mojibake in portal form sent/due separator text.
- [ ] Check all status badges and alerts for contrast.
- [ ] Confirm form cards and action buttons do not overlap on narrow screens.
- [ ] Confirm long instructions and question text wrap cleanly.
- [ ] Confirm no page-level horizontal scrolling.
- [ ] Confirm loading, empty, completed, and error states do not look like blank or broken pages.
- [ ] Confirm Forms and Questionnaires naming is consistent for staff and customers.
- [ ] Confirm Customer Forms is not a confusing duplicate of public questionnaires.
- [ ] Confirm the intended flow is request, notify, complete, review, retain.

---

## Section 8 — Document Signatures

### Verified Structure And Behavior
- [x] Public route `/customer-sign/:token` exists.
- [x] Signature UI is integrated with orders, approvals, and documents.
- [x] Tenant settings can enable or disable signature features.
- [x] Signature requirements can be created.
- [x] Email requests create unique request tokens.
- [x] Request expiry is clamped to 1-30 days.
- [x] Internal and public capture record signer data, image, timestamp, and client IP.
- [x] Signature images are stored in object storage.
- [x] Blank-looking images below a minimum size are rejected.
- [x] Public GET marks expired requests expired and rejects them.
- [x] Authenticated signature list omits request tokens.
- [x] Stored `signature_drawing_results.xml` report has 27 tests with 22 passing and 5 skipped.
- [x] Stored `iteration130_artwork_products_questionnaires_signatures.xml` report has 37 passing tests.
- [x] Stored `tier7_signatures_drawings.xml` report has 24 tests with 22 passing and 2 drawing failures.

### P0 Confirmed Public-State And File Security Defects
- [ ] Reject public signing when a request is expired.
- [ ] Reject public signing when a request is declined or otherwise not pending.
- [ ] Reject public decline when a request is signed, declined, expired, or otherwise not pending.
- [ ] Enforce state and expiry conditions atomically in database updates.
- [ ] Prevent simultaneous sign and decline calls from producing contradictory outcomes.
- [ ] Protect `/api/signatures/file/{signature_id}` with authenticated tenant access or a secure time-limited token.
- [ ] Prevent signature image retrieval by guessed or leaked signature ID.
- [ ] Invalidate or rotate public access after completion where appropriate.
- [ ] Add terminal-state, race-condition, and file-authorization tests.

### P0 Tenant Scope, Delivery, And Parent Synchronization
- [ ] Add tenant scope to every parent-record update after sign or decline.
- [ ] Add tenant scope to signature updates after tenant-scoped lookup.
- [ ] Add tenant scope to requirement and request upserts.
- [ ] Validate `origin_url` against trusted application origins.
- [ ] Escape company, customer, record, message, and link values inserted into signature email HTML.
- [ ] Remove or invalidate pending requests when email delivery fails.
- [ ] Make signature update and parent-record status update transactional or safely recoverable.
- [ ] Define behavior when image storage succeeds but signature update fails.
- [ ] Define behavior when signature update succeeds but parent update fails.
- [ ] Verify each launch-visible parent type has correct signed and declined behavior.
- [ ] Ensure a signature for one document version cannot authorize a changed version silently.

### Legal, Consent, And Audit Requirements
- [ ] Obtain legal review of electronic-signature consent and intended use.
- [ ] Display clear consent language before signing.
- [ ] Record the consent text/version accepted.
- [ ] Record exact reviewed snapshot/version.
- [ ] Record request time, access time, signature time, IP, and user agent if required.
- [ ] Define signer identity verification requirements.
- [ ] Define whether customers receive a completion receipt and signed copy.
- [ ] Define whether staff receive completion and decline notifications.
- [ ] Define whether a signed certificate or audit package is required.
- [ ] Define signature retention and deletion restrictions.

### Signature Live Clickthrough
- [ ] Enable and disable signatures and verify visible workflows update.
- [ ] Toggle Requires Signature for each launch-visible record type.
- [ ] Send a request to a real test inbox.
- [ ] Confirm email content, company, record, recipient, link, and expiry.
- [ ] Open and sign each launch-visible record type.
- [ ] Open and decline each launch-visible record type.
- [ ] Capture an internal signature for each launch-visible record type.
- [ ] Confirm signature history and parent status update correctly.
- [ ] Reopen signed, declined, expired, and invalid links.
- [ ] Attempt sign and decline simultaneously.
- [ ] Attempt invalid, tiny, blank, and corrupt signature images.
- [ ] Force email, storage, database, and parent-update failures.

### Signature Visual, Layout, Purpose, And Flow
- [ ] Check all font colors, badges, disabled controls, and alerts for contrast.
- [ ] Confirm public and internal signature layouts have no horizontal scrolling.
- [ ] Confirm signature canvas works on phone, tablet, and desktop.
- [ ] Confirm long record names, line items, notes, emails, and filenames do not overflow.
- [ ] Confirm proof and signature images fit without distortion.
- [ ] Confirm invalid and expired pages are useful rather than blank.
- [ ] Add explicit confirmation before Decline.
- [ ] Confirm signature actions do not duplicate approvals without a clear distinction.
- [ ] Hide unsupported signature types and parent-record flows.

---

## Section 9 — Record Retention And History

### Verified Existing Record Metadata
- [x] Documents store created and updated timestamps.
- [x] Documents support archived status instead of immediate hard deletion.
- [x] Document email and portal sends create activity records.
- [x] Portal documents store created and viewed timestamps.
- [x] Questionnaires and responses store creation, update, and submission timestamps.
- [x] Signatures store created, updated, signed, expiry, signer, version, and IP metadata.
- [x] Artwork proofs have explicit versioning outside the document library.

### P0 Governance Decisions
- [ ] Inventory every business-record collection in Category 5.
- [ ] Classify records as draft, operational, financial, legal, customer-provided, signed, or system audit.
- [ ] Define the authoritative record for each category.
- [ ] Define retention period for each category.
- [ ] Define deletion eligibility for each category.
- [ ] Define legal-hold behavior.
- [ ] Define customer data export and deletion handling.
- [ ] Define tenant closure and offboarding export/deletion behavior.
- [ ] Define backup frequency, restore objectives, and restore testing.
- [ ] Define who can access archived and deleted records.
- [ ] Define whether signed and customer-submitted records are immutable.
- [ ] Define how corrected records preserve previous versions.
- [ ] Obtain legal and privacy review before enabling destructive deletion.

### P0 History And Audit Implementation
- [ ] Add a unified event model for create, view, download, edit, send, share, sign, decline, archive, restore, export, and delete.
- [ ] Record actor, tenant, record, action, timestamp, source, and outcome.
- [ ] Record before/after values for sensitive metadata changes where required.
- [ ] Prevent ordinary users from editing audit events.
- [ ] Add document version history where records can change after delivery.
- [ ] Add questionnaire version snapshots to responses.
- [ ] Add signed-record snapshots and consent versions.
- [ ] Add delivery history visible to authorized staff.
- [ ] Add portal view/download history where required.
- [ ] Add archive search and restore workflow.
- [ ] Add permanent-delete workflow with elevated permission and confirmation.
- [ ] Add export workflow for a customer, order, or tenant record package.
- [ ] Verify audit and retention records are tenant isolated.

### Retention And Recovery Verification
- [ ] Archive and restore each supported record type.
- [ ] Verify archived records remain excluded from normal active lists.
- [ ] Verify archived records remain available to authorized history views.
- [ ] Verify signed and submitted records cannot be silently changed.
- [ ] Verify correction creates a traceable new version.
- [ ] Restore records from backup in a non-production exercise.
- [ ] Confirm object-storage files and database metadata restore together.
- [ ] Confirm deleted or revoked portal access stops customer access.
- [ ] Confirm retention jobs do not delete records under legal hold.
- [ ] Confirm exports contain complete, readable, correctly linked records.
