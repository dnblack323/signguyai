# Category 2: Production And Work Management
**Objective:** Make scheduling, production execution, task management, appointments, workflow configuration, and cross-module handoffs reliable enough for daily shop operations.

**Sections:** Production Board · Production Settings · Workflow Templates And Production Timelines · Productivity Dashboard · Productivity Calendar · Productivity Kanban · Productivity Task List · Appointments · Job And Production Handoffs

---

## Category Readiness Summary
- Source review: completed for all nine sections
- Stored test review: completed for available production, productivity, scheduling, and workflow reports
- Authenticated live clickthrough: **not yet completed**
- Visual and responsive review: **not yet completed**
- Launch stance: read-only work views have strong foundations, but production movement, writeback, workflow configuration, and public appointment actions are not launch-ready until PO issues are resolved

---

## Category-Wide Confirmed Launch Blockers

- [x] Fix Production Board stage movement so it never shows a success toast after an API update fails. ✅ *Fixed 2026-06-08 — moveToStage checks return value from updateTask, only toasts on success*
- [ ] Enforce proof-approval dependencies before production tasks can start or complete; the backend currently checks and then intentionally allows the transition.
- [ ] Add tenant scoping to production-task mutations, ticket/order rollups, workflow-template updates, and appointment updates after initial validation.
- [ ] Decide and consolidate the overlapping production systems: Production Board stages, production-task workflow templates, and legacy production timelines.
- [ ] Resolve incompatible workflow-template schemas stored in the same `workflow_templates` collection.
- [ ] Prevent unsafe workflow-template reset/reseed actions from deleting or changing workflows used by active work.
- [x] Fix public appointment Confirm and Request Change actions so email scanners and simple GET requests cannot mutate appointment status. ✅ *Fixed 2026-06-08 — GET shows landing page/form, POST performs the mutation*
- [ ] Add expiry, tenant binding, and revocation behavior to public appointment action tokens.
- [x] Fix the dead appointment nudge route that navigates to `/appointments/{id}` instead of `/productivity/appointments/{id}`. ✅ *Fixed 2026-06-08 — corrected navigate path in AssistantNudgesWidget.js*
- [ ] Add visible error and Retry states across Production Board, Production Settings, Productivity, and Appointment Detail.
- [ ] Replace skipped Productivity writeback, drag/drop, and cross-view tests with seeded passing tests.
- [ ] Complete full cross-module handoff verification from approved order item through production completion.

## Category-Wide Required Workflow

- [ ] An approved order item can enter production only when required proofs and signatures are complete.
- [ ] The correct workflow template generates the correct production tasks exactly once.
- [ ] Production tasks appear consistently in Order Detail, Production Board, Productivity, employee-facing work views, Dashboard, and history.
- [ ] Assignments, priorities, dates, stages, statuses, and completion remain synchronized.
- [ ] Appointments and schedule items appear at the correct date/time for the correct customer and employee.
- [ ] Staff can recover safely from failed updates without duplicate tasks, timelines, or status changes.
- [ ] Completed work retains accurate timestamps, actor history, dependencies, and source links.

---

## Section 1 — Production Board

**Purpose:** Production Board must be the reliable shop-floor view of active production work. Moving or completing work must update the actual source records and never misrepresent success.

### Verified
- [x] `/production-board` route exists.
- [x] Desktop and mobile navigation expose Production Board.
- [x] Board loads from `GET /api/production-tasks/board?view=stage`.
- [x] Board supports configured stages, status filter, focus mode, and one-card-per-ticket rollup.
- [x] Board preferences persist in local storage.
- [x] Board supports drag/drop stage movement.
- [x] Board provides a non-drag Next action when rollup is disabled.
- [x] Board supports Start, Pause, and Done task actions.
- [x] Board links to `/settings/production`.
- [x] Backend board endpoint is tenant-scoped for production tasks.
- [x] Stored `production_timeline_results.xml` has 23 tests, 0 failures, 0 errors, and 0 skipped.
- [x] A dedicated Production checklist exists: `LAUNCH_READINESS_PRODUCTION_CHECKLIST.md`.

### PO — Confirmed Bugs And Data Risks
- [ ] Make `updateTask` return or throw a failure result.
- [ ] Show "Moved to..." only after the production task update succeeds.
- [ ] Prevent drag/drop and Next from falsely reporting success after failed updates.
- [ ] Add tenant scoping when enriching board tasks from job tickets.
- [x] Add tenant scoping to production-task update and final lookup after tenant-scoped validation. ✅ *Fixed 2026-06-09 — update_one and final find_one now include tenant_id*
- [ ] Add tenant scoping to ticket and order progress rollups.
- [ ] Enforce `depends_on_proof` instead of silently allowing start/complete.
- [ ] Define an explicit authorized override workflow if proof-gate overrides are required.
- [ ] Enforce dependency-task completion before later tasks start or complete.
- [ ] Define whether completed tasks may be moved or reopened.
- [ ] Prevent duplicate rapid Start, Pause, Done, Next, and drag/drop actions.
- [ ] Remove encoding-corrupted task separators and history text.

### Reliability And Error States
- [ ] Add a persistent board load-error state.
- [ ] Add a Retry action.
- [ ] Distinguish a confirmed empty board from a failed board request.
- [ ] Preserve the last trustworthy board state during transient failures where appropriate.
- [ ] Show an update failure directly on the affected card.
- [ ] Confirm board reload failure after a successful update does not make the update appear lost.
- [ ] Confirm invalid task dates and missing ticket records do not crash the board.
- [ ] Confirm more than 500 production tasks are handled intentionally.

### Production Board Live Clickthrough
- [ ] Open the board with zero production tasks.
- [ ] Open the board with multiple tickets and stages.
- [ ] Toggle one-card-per-ticket on and off.
- [ ] Toggle focus mode on and off.
- [ ] Apply every status filter.
- [ ] Start, pause, restart, complete, and reopen a test task where allowed.
- [ ] Move a task with drag/drop.
- [ ] Move a task with Next.
- [ ] Attempt to start a task blocked by proof approval.
- [ ] Attempt to start a task blocked by an incomplete dependency.
- [ ] Refresh and verify persistence.
- [ ] Confirm the related ticket, order, Dashboard, Productivity, and employee work view agree.
- [ ] Force update and reload failures and verify no false success.
- [ ] Confirm unauthorized roles cannot perform restricted production actions.

### Visual, Layout, Purpose, And Accessibility
- [ ] Check every task, badge, priority dot, stage color, button, and metadata color for contrast.
- [ ] Confirm intentional board scrolling does not create page-level horizontal scrolling.
- [ ] Confirm header controls wrap at mobile, tablet, laptop, and desktop widths.
- [ ] Confirm long task names, ticket numbers, employees, and due dates do not overlap.
- [ ] Confirm drag targets have clear feedback.
- [ ] Confirm keyboard users can perform every drag action through buttons.

---

## Section 2 — Production Settings

**Purpose:** Production Settings must safely configure board columns, workflow behavior, templates, category assignments, and analytics without breaking active production.

### Verified
- [x] `/settings/production` route exists.
- [x] `/workflow-templates` redirects to `/settings/production`.
- [x] Production Settings includes Board Stages, Workflow Templates, and Analytics tabs.
- [x] Board stage editor supports add, remove, rename, recolor, reorder, and save.
- [x] Workflow mode supports simple, detailed, and custom values.
- [x] Workflow templates support list, create, edit, delete, reorder, copy-from, and category assignment in source.
- [x] Default timeline templates are read-only in the settings UI.
- [x] Production analytics and stage report endpoints exist.
- [x] Stored production timeline tests cover workflow settings, simple/detailed mode, timeline enable/disable, advance, edit, history, analytics, and templates.

### PO — Confirmed Configuration Risks
- [ ] Add a visible load-error state for board-stage configuration instead of silently using defaults.
- [ ] Add a visible load-error state for workflow settings and analytics.
- [ ] Add Retry actions for every failed settings section.
- [ ] Validate that stage configuration contains at least one valid stage.
- [ ] Reject duplicate stage keys.
- [ ] Reject malformed colors and invalid stage payloads.
- [ ] Prevent removing or renaming stages that contain active production tasks without migration.
- [ ] Define where tasks move when an active stage is removed.
- [ ] Confirm changing a stage label does not unintentionally change its stable key.
- [ ] Confirm stage order changes do not reorder active workflow dependencies incorrectly.
- [ ] Restrict production configuration to authorized roles.
- [ ] Add a clear confirmation and impact summary before destructive configuration changes.

### Production Settings Live Clickthrough
- [ ] Load each settings tab.
- [ ] Add, rename, recolor, reorder, and remove a test board stage.
- [ ] Save and confirm Production Board updates correctly.
- [ ] Attempt malformed, empty, duplicate, and destructive stage configurations.
- [ ] Switch simple, detailed, and custom workflow modes.
- [ ] Create, copy, edit, assign, and delete a custom template.
- [ ] Confirm default templates remain protected.
- [ ] Confirm assigned category template affects newly generated work.
- [ ] Confirm existing active work is not silently changed.
- [ ] Verify analytics with zero, normal, and large datasets.
- [ ] Force each settings request to fail and verify recovery.

### Visual, Layout, Purpose, And Flow
- [ ] Check heading and subtitle colors against the actual settings background.
- [ ] Check all stage colors and analytics colors for contrast.
- [ ] Confirm long stage/template names do not overflow.
- [ ] Confirm settings tabs and editors fit mobile and tablet widths.
- [ ] Confirm destructive buttons are clearly separated.
- [ ] Confirm Board Stages and Workflow Templates have clearly different purposes.
- [ ] Confirm Analytics does not show large empty areas when no data exists.
- [ ] Confirm every visible setting has a measurable launch effect.

---

## Section 3 — Workflow Templates And Production Timelines

**Purpose:** Workflow templates must define one consistent production sequence. Applying a template must generate the expected tasks or timeline once, preserve dependencies, and remain compatible with active work.

### Verified
- [x] Backend has `/api/workflow-templates` CRUD, reseed, apply, and duplicate routes.
- [x] Backend has `/api/production-timeline` settings, templates, enable, disable, advance, stage update, analytics, and history routes.
- [x] Production task generation uses category-based templates.
- [x] Template application can target an order or specific job ticket.
- [x] Template application can replace existing tasks when explicitly requested.
- [x] Generated production tasks carry order, ticket, tenant, sequence, department, QC, proof dependency, and dependency-task data.
- [x] Stored production timeline report has 23 passing tests.

### PO — Confirmed Overlap And Schema Risks
- [ ] Choose one canonical launch workflow engine: production tasks, production timelines, or a documented coordinated design.
- [ ] Consolidate the two template APIs that both use `workflow_templates`.
- [ ] Resolve incompatible template fields such as `template_name` versus `name`, `sequence` versus `order`, and task dependencies versus timeline triggers.
- [ ] Prevent one template editor from corrupting templates expected by the other engine.
- [ ] Remove or archive the unreachable standalone `WorkflowTemplateManager` if it is obsolete.
- [ ] Confirm `/workflow-templates` redirect does not hide necessary standalone functionality.
- [ ] Add tenant scoping to workflow-template update and final lookup.
- [ ] Add tenant scoping to production-timeline template update.
- [ ] Add tenant scoping to job-item/timeline mutations after validation.
- [ ] Fix process-level default-template seed caching so a deleted/recreated tenant state can reseed correctly.
- [ ] Ensure custom templates do not cause all default templates to disappear from the timeline template list unintentionally.
- [ ] Prevent reset/reseed from deleting defaults required by active work.
- [ ] Prevent template apply with `replace_existing=true` from destroying completed task history without confirmation/archive.
- [ ] Make template apply transactional or recoverable after partial task creation.
- [ ] Validate stages, sequence/order uniqueness, required final stage, dependencies, and supported departments.

### Workflow And Timeline Live Clickthrough
- [ ] Generate production tasks from every launch item category.
- [ ] Confirm the expected category template is selected.
- [ ] Apply a template to one ticket.
- [ ] Apply a template to all tickets on an order.
- [ ] Attempt repeated apply without replacement.
- [ ] Apply with replacement and inspect history/cleanup.
- [ ] Duplicate and edit a template.
- [ ] Enable, advance, edit, and disable a production timeline.
- [ ] Confirm task workflow and timeline workflow do not contradict each other.
- [ ] Confirm history records every stage transition and actor.
- [ ] Confirm active work remains understandable after template edits.
- [ ] Force partial apply and verify rollback/recovery.

### Workflow Purpose And Governance
- [ ] Define which categories use which templates.
- [ ] Define who may create, assign, edit, reset, apply, and delete templates.
- [ ] Define whether templates are copied into active work or referenced dynamically.
- [ ] Define migration behavior when a template changes.
- [ ] Define required proof, QC, assignment, and dependency gates.
- [ ] Confirm each workflow has one clear completion state.

---

## Section 4 — Productivity Dashboard

**Purpose:** Productivity Dashboard must summarize unified work accurately without changing source records unexpectedly or hiding missing data.

### Verified
- [x] `/productivity?view=dashboard` is supported.
- [x] Productivity has unified items and summary endpoints.
- [x] Dashboard can summarize due today, overdue, waiting approval, scheduled this week, assigned work, open items, completed items, source types, and board columns.
- [x] Filters support search, assignee, status, completed items, and item types.
- [x] Stored `productivity_unified_results.xml` has 23 tests with no failures, errors, or skips.
- [x] Stored unified tests cover items, filters, search, date range, summary, calendar modes, board grouping, source types, invalid view, and authentication.
- [x] A dedicated Productivity checklist exists: `LAUNCH_READINESS_PRODUCTIVITY_CHECKLIST.md`.

### PO — Navigation And Reliability
- [ ] Add a visible view selector inside Productivity or explicitly rely on stable external navigation.
- [ ] Use or remove the currently unused `VIEW_OPTIONS`.
- [ ] Sync active view when the URL `?view=` changes while Productivity remains mounted.
- [ ] Validate invalid view values and fall back to a valid view.
- [ ] Prevent invalid views from rendering mostly blank pages.
- [ ] Add persistent errors and Retry actions for items and summary loads.
- [ ] Distinguish failed data from legitimate zero-value summaries.
- [ ] Confirm summary source types and include-completed behavior match the visible item list.

### Dashboard Live Clickthrough
- [ ] Open Productivity Dashboard from desktop and mobile navigation.
- [ ] Refresh and confirm the view remains selected.
- [ ] Compare every summary number to filtered visible/source data.
- [ ] Apply every filter individually and in combination.
- [ ] Open items from every summary/list surface.
- [ ] Confirm empty and error states are trustworthy.

### Dashboard Visual, Purpose, And Flow
- [ ] Check header white/slate text against the actual background.
- [ ] Check metric and badge contrast.
- [ ] Confirm summary content does not leave excessive blank space.
- [ ] Confirm the most actionable work appears first.
- [ ] Remove duplicate metrics that already exist on the main Dashboard without a clear work-management purpose.

---

## Section 5 — Productivity Calendar

**Purpose:** Productivity Calendar must show tasks, orders/jobs, production tasks, appointments, and schedule items on the correct dates and allow safe daily planning.

### Verified
- [x] Productivity Calendar supports month, week, and day modes.
- [x] Calendar supports Today, Previous, and Next actions.
- [x] Calendar range endpoint exists.
- [x] Calendar supports opening unified items.
- [x] Day detail dialog displays items for a selected day.
- [x] Day detail supports creating a task for the selected day.
- [x] Calendar view, mode, and anchor date are written to URL parameters.

### PO — Required Before Launch
- [ ] Add persistent calendar load-error state and Retry action.
- [ ] Catch calendar-load errors so they do not become unhandled promise rejections.
- [ ] Verify calendar view/date URL changes synchronize while the page remains mounted.
- [ ] Confirm date-only values never shift by one day across timezones.
- [ ] Confirm appointment and schedule-shift times display in the intended tenant/user timezone.
- [ ] Confirm invalid dates do not crash the calendar.
- [ ] Confirm creating a day task refreshes Calendar, Dashboard, Kanban, and Task List.
- [ ] Preserve typed day-task data after creation failure.
- [ ] Confirm large numbers of items remain performant and readable.

### Calendar Live Clickthrough
- [ ] Open month, week, and day modes.
- [ ] Use Today, Previous, and Next in every mode.
- [ ] Refresh and confirm mode/date persist.
- [ ] Open tasks, jobs/orders, production tasks, appointments, and schedule items.
- [ ] Create a day task with and without an assignee.
- [ ] Move/edit dates through the supported source workflow and verify calendar updates.
- [ ] Test daylight-saving transitions and timezone boundaries.
- [ ] Test days with zero, one, and many items.

### Calendar Visual, Layout, Purpose, And Accessibility
- [ ] Confirm calendar cells and labels remain readable on mobile.
- [ ] Confirm crowded dates do not overflow or hide work.
- [ ] Confirm item types are distinguishable without relying only on color.
- [ ] Confirm the day detail dialog fits and scrolls.
- [ ] Confirm keyboard users can navigate dates and open items.
- [ ] Confirm no duplicate calendar competes with Employee Schedule without a clear purpose.

---

## Section 6 — Productivity Kanban

**Purpose:** Productivity Kanban must provide a safe unified status view without bypassing the business rules of Orders, Production, Tasks, or Appointments.

### Verified
- [x] Kanban view exists.
- [x] Kanban includes task, job, and production-task item types.
- [x] Backend board endpoint exists.
- [x] Source supports drag/drop status updates.
- [x] Production-task completion maps generic completed/done columns to `complete`.
- [x] Non-production completion maps the complete column to `completed`.

### PO — Confirmed Writeback Risks
- [ ] Await and catch `handleUpdateItem` inside `handleKanbanMove`.
- [ ] Show visible move failure instead of an unhandled promise rejection.
- [ ] Revert optimistic UI state if future optimistic updates are added.
- [ ] Confirm generic Kanban status changes cannot bypass order, appointment, or production business rules.
- [ ] Route production-task status changes through production-task transition logic rather than directly updating the database.
- [ ] Ensure Production Board, ticket progress, order progress, history, proof dependencies, and timestamps update after Productivity moves.
- [ ] Replace skipped Kanban persistence tests with seeded fixtures.
- [ ] Define valid columns/statuses per source type.
- [ ] Reject unsupported cross-status moves.

### Kanban Live Clickthrough
- [ ] Move normal tasks between every allowed column.
- [ ] Complete and reopen tasks.
- [ ] Move a production task and confirm Production Board and Order Detail agree.
- [ ] Move a job/order and confirm Orders agrees.
- [ ] Attempt invalid and gated production moves.
- [ ] Refresh after every move.
- [ ] Force move failures and verify visible recovery.
- [ ] Test rapid and concurrent moves.

### Kanban Visual, Layout, Purpose, And Accessibility
- [ ] Confirm horizontal scrolling is intentional and contained.
- [ ] Confirm empty columns do not create excessive blank space.
- [ ] Confirm long cards fit without overlap.
- [ ] Confirm drag feedback and drop targets are visible.
- [ ] Provide keyboard/button alternatives for every drag action.
- [ ] Confirm Kanban does not duplicate Production Board without a clear unified-work purpose.

---

## Section 7 — Productivity Task List

**Purpose:** Task List must provide fast, accurate work updates while clearly identifying the source record that will be changed.

### Verified
- [x] Task List view exists.
- [x] Task List supports inline status, priority, due date, assignment, complete, and reopen actions for supported source types.
- [x] Productivity item dialog supports source-specific editing.
- [x] Source records can be opened from item dialog when a source route exists.
- [x] Productivity writeback endpoint exists.
- [x] Stored `productivity_phase2_results.xml` has 16 tests and 0 failures.

### PO — Confirmed Writeback And Error Gaps
- [ ] Replace the 10 skipped Phase 2 tests with seeded fixtures.
- [ ] Catch and display every inline update failure.
- [ ] Prevent unsupported updates from silently doing nothing.
- [ ] Make the backend return a clear error when the source item is missing instead of `{ message: "Updated" }`.
- [ ] Validate allowed fields and statuses per source type.
- [ ] Confirm direct production-task writeback performs progress rollups and history logging.
- [ ] Confirm direct appointment writeback updates all canonical date aliases.
- [ ] Confirm direct schedule-shift writeback preserves all shift data and prevents invalid end-before-start windows.
- [ ] Confirm direct order/job writeback cannot bypass required workflow transitions.
- [ ] Confirm Open Source uses client-side navigation and always points to a real route.

### Task List Live Clickthrough
- [ ] Update status for every writable source type.
- [ ] Update priority for tasks and production tasks.
- [ ] Update due dates.
- [ ] Assign and unassign tasks and production tasks.
- [ ] Complete and reopen work.
- [ ] Edit appointment start.
- [ ] Edit schedule-shift start and end.
- [ ] Open the source record for every source type.
- [ ] Refresh and verify persistence.
- [ ] Confirm every update appears in all relevant modules.
- [ ] Force every update to fail and verify recovery.

### Task List Visual, Layout, Purpose, And Accessibility
- [ ] Confirm inline controls fit mobile and tablet widths.
- [ ] Confirm long titles, customers, and source labels do not overlap.
- [ ] Confirm status and priority controls have sufficient contrast.
- [ ] Confirm compact controls have accessible labels.
- [ ] Confirm source type and impacted record are obvious before editing.
- [ ] Confirm Task List does not duplicate source-module editing without a productivity benefit.

---

## Section 8 — Appointments

**Purpose:** Appointments must safely coordinate customer requests, internal scheduling, confirmations, rescheduling, assignment, reminders, and calendar visibility.

### Verified
- [x] Authenticated appointment create, list, detail, update, delete, confirm, and reject routes exist.
- [x] Appointment queries begin tenant-scoped.
- [x] Appointments can link to customers, orders, and employees.
- [x] Appointments appear in Productivity and Customer Portal.
- [x] `/productivity/appointments/:appointmentId` route exists.
- [x] Appointment Detail displays status, scheduled time, customer, location, type, duration, and notes.
- [x] Customer appointment emails include tokenized Confirm and Request Change links.
- [x] Stored appointment-request coverage exists inside broader saved reports.

### PO — Confirmed Security, Routing, And State Defects
- [ ] Replace public Confirm and Request Change GET mutations with confirmation pages followed by POST actions.
- [ ] Prevent email-security scanners and link previews from changing appointment state.
- [ ] Add expiry to public appointment action tokens.
- [ ] Bind public tokens to tenant and appointment version/state.
- [ ] Add token revocation after cancellation, reschedule, deletion, or replacement email.
- [ ] Decide whether a customer may re-confirm an admin-cancelled appointment; current source allows it.
- [ ] Prevent contradictory confirm/reschedule actions under concurrency.
- [ ] Escape appointment/customer/tenant values inserted into public HTML and email HTML.
- [ ] Fix Assistant Nudges appointment navigation from `/appointments/{id}` to the real route `/productivity/appointments/{id}`.
- [ ] Add tenant scoping to authenticated appointment update/confirm/reject mutations after lookup.
- [ ] Review public appointment mutations that use only appointment ID.
- [ ] Remove encoding-corrupted public appointment and detail text.

### Appointment Reliability And UX
- [ ] Add loading, not-found, error, and Retry states to Appointment Detail.
- [ ] Prevent Appointment Detail from displaying Loading forever after a failed request.
- [ ] Show whether an appointment notification email was actually delivered or skipped.
- [ ] Define reminder scheduling behavior; `send_reminder` currently triggers creation email behavior but does not prove timed reminders.
- [ ] Validate customer, employee, and order references exist and belong to the tenant.
- [ ] Validate start/end times, duration, timezone, and end-after-start.
- [ ] Prevent employee double-booking where required.
- [ ] Prevent customer double-booking where required.
- [ ] Define statuses and transitions: requested, scheduled, confirmed, needs reschedule, cancelled, completed, and no-show.
- [ ] Notify the correct parties after confirmation, rejection, reschedule, cancellation, and reassignment.

### Appointment Live Clickthrough
- [ ] Create an internal appointment.
- [ ] Create a customer-linked, order-linked, and employee-assigned appointment.
- [ ] Request an appointment through Customer Portal.
- [ ] Confirm and reject/reschedule as staff.
- [ ] Confirm and request change through customer email links.
- [ ] Verify a link preview does not mutate state.
- [ ] Reschedule and confirm old links no longer act.
- [ ] Edit appointment time through Productivity.
- [ ] Open Appointment Detail from Calendar, source links, Dashboard, and nudges.
- [ ] Confirm Calendar, Customer Portal, Dashboard, and detail agree.
- [ ] Delete/cancel a disposable appointment.
- [ ] Test invalid, expired, reused, and concurrent public actions.

### Appointment Visual, Layout, Purpose, And Accessibility
- [ ] Check Appointment Detail heading/subtitle colors.
- [ ] Check public appointment result pages for correct encoding, branding, and contrast.
- [ ] Confirm public pages are usable on mobile.
- [ ] Confirm dates/times are human-readable and timezone-aware.
- [ ] Confirm reason forms fit without horizontal scrolling.

---

## Section 9 — Job And Production Handoffs

**Purpose:** Handoffs must move work safely from approved order item to production, assignments, scheduling, completion, and downstream fulfillment without duplication or bypassed gates.

### Verified
- [x] Order and ticket records contain production-flow controls.
- [x] Starting production can generate tasks for workflow-enabled tickets.
- [x] Ticket creation/update can generate production tasks.
- [x] Production-task changes can roll up ticket and order progress.
- [x] Production items appear in Production Board and Productivity.
- [x] Order Detail exposes production actions and task status.
- [x] Employee-facing production/task surfaces exist.

### PO — Confirmed Handoff Risks
- [ ] Enforce proof approval, signature, deposit, material, scheduling, or other required gates before production.
- [ ] Define which gates are mandatory by item category.
- [ ] Prevent repeated Start Production from generating duplicate tasks.
- [ ] Prevent ticket enable/update and order Start Production from generating duplicate workflows.
- [ ] Make task generation transactional or recoverable after partial creation.
- [ ] Ensure task generation uses the canonical active workflow template.
- [ ] Ensure assignments and dates propagate to the correct employee/calendar views.
- [ ] Ensure direct Productivity updates execute the same transition rules and history as Production Board.
- [ ] Ensure completion cannot occur while required QC/dependencies remain incomplete.
- [ ] Define rework, pause, hold, cancellation, and reopening behavior.
- [ ] Preserve complete history when workflows or templates change.

### Handoff Live Clickthrough
- [ ] Create an approved standard order item.
- [ ] Enable its production workflow.
- [ ] Start production from Order Detail.
- [ ] Confirm tasks are generated exactly once.
- [ ] Confirm tasks appear in Production Board, Productivity, Order Detail, and employee work views.
- [ ] Assign and schedule production work.
- [ ] Complete each dependency in order.
- [ ] Attempt to bypass proof and dependency gates.
- [ ] Pause, hold, resume, rework, and complete work.
- [ ] Confirm ticket/order progress, Dashboard, and history update.
- [ ] Repeat for every launch item category.
- [ ] Repeat after workflow-template changes.
- [ ] Force partial handoff failures and verify recovery.

### Handoff Purpose And Flow Audit
- [ ] Define the single production start action and remove duplicate/confusing alternatives.
- [ ] Define ownership of production stage versus task status.
- [ ] Define ownership of assignment and scheduling.
- [ ] Define ownership of due dates and priorities.
- [ ] Confirm Production Board and Productivity Kanban do not compete as equal sources of truth.
- [ ] Confirm order, ticket, production task, timeline, appointment, and schedule statuses use consistent language.
- [ ] Confirm every handoff creates the minimum necessary records and no duplicates.

---

## Cross-Section Data Contract Checklist

- [ ] Use one canonical workflow-template schema.
- [ ] Use one canonical production-stage vocabulary.
- [ ] Use one canonical status vocabulary per source type with explicit mappings.
- [ ] Use tenant ID in every read, update, delete, rollup, enrichment, and public-token mutation.
- [ ] Preserve source IDs across tasks, tickets, orders, appointments, schedules, and timelines.
- [ ] Record actor, timestamp, old value, new value, and reason for every important transition.
- [ ] Store dates/times with explicit timezone rules.
- [ ] Validate all assignments reference active tenant employees.
- [ ] Validate all customer/order/ticket references belong to the tenant.
- [ ] Prevent duplicate records under retries and concurrent requests.
- [ ] Define archive/history behavior instead of destructive loss.
- [ ] Define how active work behaves after configuration changes.

---

*Last updated: 2026-06-07 | No fixes applied yet — full clickthrough and visual QA pending*
