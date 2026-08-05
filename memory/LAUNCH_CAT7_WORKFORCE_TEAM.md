# Category 7: Workforce, Team, And Employee Operation
**Objective:** Verify that employee identities, permissions, schedules, time records, tasks, payroll, and self-service access are private, accurate, tenant isolated, auditable, and operationally reliable.

**Sections:** Team Overview · User Management · Roles And Permissions · Payroll · Timesheets · Time Clock · Employee Schedule · Employee Portal · Employee Pay View · Employee Tasks

---

## Category Readiness Summary

Status: workforce functionality is broad and heavily tested, but Category 7 is not launch-ready until employee authentication, payroll privacy, backend permissions, tenant scoping, destructive deletion, and payroll accuracy risks are resolved.

### Verified Strengths
- [x] Internal routes exist for Time Clock, Payroll, Timesheets, Employee Schedule, and Productivity.
- [x] Employee portal routes exist for login, dashboard, jobs, pay, tasks, and profile.
- [x] Backend supports employee records, time actions, payroll worksheets, transactions, signoff, schedules, portal settings, tasks, and assigned jobs.
- [x] Payroll backend distinguishes view and edit access.
- [x] Employee portal feature visibility can be controlled by tenant settings.
- [x] Saved test reports provide broad passing coverage for employees, time clock, payroll, schedule, productivity, and employee portal.

---

## Category-Wide Confirmed Launch Blockers

- [ ] Remove the employee portal shared/default PIN behavior; employees without a PIN can currently use `1234` or the last four phone digits.
- [ ] Implement the employee portal set-PIN endpoint; it currently returns success without changing anything.
- [ ] Verify employee portal tokens against both employee ID and token tenant ID.
- [ ] Add tenant scope to confirmed employee portal pay, task, customer, job-item, time-log, and mutation queries.
- [ ] Stop exposing hourly rate in employee profile unless explicitly approved and enabled.
- [ ] Add backend employee and time-clock permissions; several authenticated routes currently allow employee creation, viewing, editing, or punching without action-specific permission checks.
- [ ] Add backend task, productivity, and production-task permissions.
- [ ] Replace destructive employee deletion that removes payroll/time records with retained offboarding/deactivation.
- [ ] Fix confirmed unscoped employee, payroll-hour, production-task, and employee-portal updates.
- [ ] Resolve the saved payroll report containing two failures and replace meaningful skipped payroll/productivity coverage.
- [ ] Define payroll calculation, approval, payment, correction, retention, and legal/compliance requirements.
- [ ] Complete live clickthrough and responsive visual review.

---

## Category-Wide Required Workforce Lifecycle

- [ ] Define the difference between application user, employee record, employee portal identity, and assigned worker.
- [ ] Define who needs an employee record versus an internal application user.
- [ ] Define how employee and user accounts link and unlink.
- [ ] Define onboarding steps: identity, role, permissions, pay, schedule, portal invite, and assignments.
- [ ] Define employment-status states: invited, active, leave, inactive, terminated, and archived.
- [ ] Define offboarding steps that preserve payroll, time, task, and audit history.
- [ ] Define which employee data is sensitive and who may access it.
- [ ] Define authoritative sources for hours, rates, overtime, adjustments, payments, and balances.
- [ ] Define correction and approval workflows.
- [ ] Define retention and export requirements.

---

## Section 1 — Team Overview

### Verified Structure And Behavior
- [x] Employee records support name, contact information, title, manager, role, rates, PIN, active status, and portal linkage.
- [x] Time Clock includes an employee directory for admins/owners.
- [x] Payroll dashboard summarizes active employees and clocked-in employees.
- [x] Employee records link to internal users when email is present.
- [x] Employee activation and deactivation exist.
- [x] Saved `iteration83_employee_module_results.xml` report has 30 passing tests.

### P0 Employee Record Security And Lifecycle
- [ ] Enforce `EMPLOYEES_VIEW` on employee list and detail.
- [ ] Enforce `EMPLOYEES_MANAGE` on employee create, update, activate, deactivate, invite, PIN reset, and offboarding.
- [ ] Prevent staff with employee-view permission from seeing hourly rates, PINs, payroll notes, or other sensitive fields.
- [ ] Return role-appropriate employee response models.
- [ ] Remove PIN values from ordinary employee API responses.
- [ ] Validate unique employee email within the intended tenant/account model.
- [ ] Validate phone, role, rate, overtime rate, and status values.
- [ ] Prevent negative or impossible rates.
- [ ] Replace hard delete with deactivate/archive/offboard.
- [ ] Preserve time, payroll, schedule, task, production, and audit records after offboarding.
- [ ] Define reassignment behavior for active tasks, jobs, and production work.
- [ ] Add employee change history.

### Confirmed Destructive Delete Risks
- [ ] Stop deleting time logs during employee deletion.
- [ ] Stop deleting time-clock shifts during employee deletion.
- [ ] Stop deleting payroll hours during employee deletion.
- [ ] Stop deleting payroll transactions during employee deletion.
- [ ] Stop deleting schedules without retained history.
- [ ] Decide how linked application user access is revoked without deleting required audit identity.
- [ ] Add confirmation that explains offboarding consequences.
- [ ] Add tests proving offboarding preserves historical records.

### Team Live Clickthrough
- [ ] Create an employee without portal access.
- [ ] Create an employee with linked internal user.
- [ ] Edit contact, title, manager, and rates.
- [ ] Change role and verify permissions.
- [ ] Deactivate and reactivate.
- [ ] Offboard a test employee.
- [ ] Confirm historical payroll/time remains.
- [ ] Reassign active work.
- [ ] Confirm every employee action works and serves a purpose.

### Team Visual And Flow QA
- [ ] Separate general team information from sensitive payroll data.
- [ ] Check employee cards, rates, statuses, and disabled states for contrast.
- [ ] Confirm directory actions fit without horizontal scrolling.
- [ ] Confirm long names, emails, titles, and phone numbers fit.
- [ ] Reduce duplicate employee-management entry points.
- [ ] Confirm workflow order is onboard, configure, assign, manage, and offboard.

---

## Section 2 — User Management

### Verified Structure And Behavior
- [x] Auth backend supports current-user profile and permissions.
- [x] Admin user list exists.
- [x] Admin user create exists.
- [x] Admin password reset exists.
- [x] Admin user status update exists.
- [x] Admin role update exists.
- [x] Admin user delete exists.
- [x] User-management endpoints check Users View or Users Manage permissions.
- [x] Employee creation can create or link a tenant user.

### P0 Identity And Account Integrity
- [ ] Define whether employee creation should automatically create an application user.
- [ ] Prevent employee PIN from being reused as an internal application password.
- [ ] Require secure initial password setup or invitation flow.
- [ ] Prevent duplicate identities across employee, user, owner-portal, and customer-portal records.
- [ ] Confirm changing employee email updates linked user safely.
- [ ] Confirm changing role updates linked user safely.
- [ ] Confirm deactivation revokes all relevant sessions and portal access.
- [ ] Confirm deleting a user does not delete the employee's required payroll/audit identity.
- [ ] Prevent users from changing their own role or deleting themselves in unsafe ways.
- [ ] Protect the final active owner/admin account.
- [ ] Record user create, role change, reset, deactivate, and delete events.
- [ ] Add invitation expiry, revoke, resend, and acceptance state.

### User Management Live Clickthrough
- [ ] List users as owner/admin.
- [ ] Confirm unauthorized roles cannot list or manage users.
- [ ] Create owner-approved admin and staff accounts.
- [ ] Send or perform initial credential setup.
- [ ] Reset password.
- [ ] Change role.
- [ ] Deactivate and reactivate.
- [ ] Delete or archive a safe test user.
- [ ] Confirm employee and user records stay synchronized as intended.
- [ ] Confirm active sessions are revoked when required.

### User Management Visual And Purpose QA
- [ ] Clearly distinguish Users from Employees.
- [ ] Explain whether a user can access the internal app, employee portal, or both.
- [ ] Hide sensitive authentication values.
- [ ] Check role/status badges and destructive actions for contrast.
- [ ] Confirm no duplicate user-management surfaces conflict.
- [ ] Confirm every action and link works without blank screens.

---

## Section 3 — Roles And Permissions

### Verified Structure And Behavior
- [x] Backend defines platform admin, owner, admin, staff, and webstore-owner roles.
- [x] Backend defines permissions for customers, quotes, jobs, invoices, time, payroll, employees, financials, users, settings, webstores, and products.
- [x] Owner and platform admin receive all permissions.
- [x] Admin and staff receive fixed permission sets.
- [x] Frontend retrieves current-user permissions.
- [x] Frontend includes aliases for several frontend/backend permission-name differences.
- [x] Employee portal uses separate tenant-config feature flags.

### P0 Permission Contract Defects
- [ ] Create an app-wide route/action permission matrix.
- [ ] Align frontend permission names directly with backend names.
- [ ] Remove reliance on aliases as the long-term contract.
- [ ] Enforce backend permissions on every Category 7 endpoint.
- [ ] Enforce `EMPLOYEES_VIEW` and `EMPLOYEES_MANAGE`.
- [ ] Enforce Time Clock Own, View All, and Manage distinctions.
- [ ] Enforce Payroll View and Manage distinctions.
- [ ] Define and enforce Task and Productivity permissions.
- [ ] Define and enforce Schedule permissions separately from payroll if appropriate.
- [ ] Confirm staff cannot view all employees' rates or payroll.
- [ ] Confirm admins have only intended payroll/settings/user capabilities.
- [ ] Confirm employee portal JWTs cannot access internal application APIs.
- [ ] Confirm webstore-owner and customer-portal identities cannot access workforce APIs.

### Role Design Decisions
- [ ] Decide whether fixed roles are sufficient for launch.
- [ ] If custom roles are required, implement them before claiming granular permissions.
- [ ] Define who may promote a staff user to admin.
- [ ] Define who may view compensation.
- [ ] Define who may edit time records.
- [ ] Define who may approve and mark payroll paid.
- [ ] Define who may invite/reset employee portal credentials.
- [ ] Define who may change employee portal feature visibility.
- [ ] Define emergency access and audit requirements.

### Permission Verification
- [ ] Test every workforce route as owner.
- [ ] Test every workforce route as admin.
- [ ] Test every workforce route as staff.
- [ ] Test employee portal token against internal APIs.
- [ ] Test inactive and terminated identities.
- [ ] Test cross-tenant employee IDs.
- [ ] Confirm UI hides unavailable actions.
- [ ] Confirm direct API calls are still rejected.
- [ ] Confirm permission-denied states are useful and not blank.

---

## Section 4 — Payroll

### Verified Structure And Behavior
- [x] Routes `/payroll` and `/timesheets` exist.
- [x] Payroll dashboard and detailed worksheet exist.
- [x] Payroll backend checks Payroll View and edit/admin access.
- [x] Payroll supports reports, transactions, payment, signoff, adjustments, manual hours, time-clock shifts, timesheets, pay periods, schedule, export, and legacy resolution.
- [x] Payroll worksheet warns about unsaved changes.
- [x] Payroll worksheet supports CSV and printable output.
- [x] Saved payroll reports show broad passing coverage.
- [x] Saved `iteration104_payroll_worksheet_extended_results.xml` contains 29 tests with 2 failures.
- [x] Saved `iteration82_payroll_admin_results.xml` contains 15 tests with 1 skipped.
- [x] Saved `payroll_enhancement_results.xml` contains 20 tests with 9 skipped.

### P0 Payroll Accuracy And Compliance
- [ ] Define whether this module is payroll calculation, payroll tracking, or an actual payroll system.
- [ ] Do not imply taxes, withholding, benefits, garnishments, or compliance are handled unless implemented.
- [ ] Define authoritative pay period and week-start rules.
- [ ] Define regular-time and overtime rules for launch jurisdictions.
- [ ] Define rounding rules.
- [ ] Define how time clock, job time, manual hours, legacy hours, adjustments, advances, and payments combine.
- [ ] Prevent duplicate hours across sources.
- [ ] Prevent negative or impossible hours, rates, and payment values.
- [ ] Validate mark-paid-in-full amount against the approved period balance.
- [ ] Prevent duplicate period payment transactions.
- [ ] Define correction/reversal behavior after payment.
- [ ] Define approval and signoff requirements.
- [ ] Add immutable approved-period snapshot.
- [ ] Obtain payroll/legal/accounting review.

### P0 Payroll Tenant Isolation And Mutation Safety
- [ ] Add tenant scope to confirmed unscoped payroll-hours updates and post-update lookups.
- [ ] Add tenant scope to employee-linked updates made from payroll worksheet.
- [ ] Add tenant scope to legacy payroll/time queries where missing.
- [ ] Migrate all legacy payroll transactions to explicit tenant IDs.
- [ ] Remove broad legacy fallback after migration.
- [ ] Make multi-row worksheet save transactional or safely recoverable.
- [ ] Define behavior when some shift/transaction/signoff changes save and others fail.
- [ ] Record before/after audit history for payroll mutations.
- [ ] Add cross-tenant payroll tests for every endpoint.

### Payroll Live Clickthrough
- [ ] Open payroll dashboard and worksheet as authorized viewer.
- [ ] Confirm unauthorized user cannot view payroll.
- [ ] Select every employee and pay-period preset.
- [ ] Add, edit, and remove time-clock rows.
- [ ] Add, edit, and remove adjustments/transactions.
- [ ] Resolve legacy entries.
- [ ] Change rates with explicit effective-date behavior.
- [ ] Review and approve/sign off.
- [ ] Mark paid in full.
- [ ] Export CSV and print.
- [ ] Refresh and confirm exact persistence.
- [ ] Reconcile worksheet, timesheet, employee pay view, and transactions.

### Payroll Visual And Privacy QA
- [ ] Ensure payroll values are never visible in general team views without permission.
- [ ] Check tables, totals, warnings, locked fields, and disabled controls for contrast.
- [ ] Confirm wide worksheet scrolling is intentional and usable.
- [ ] Confirm no page-level horizontal scrolling outside the worksheet.
- [ ] Confirm large values and long notes fit.

---

## Section 5 — Timesheets

### Verified Structure And Behavior
- [x] Timesheet route uses the payroll worksheet.
- [x] Backend timesheet endpoint exists.
- [x] Timesheet combines time, pay, carryover, transactions, and daily breakdown.
- [x] Backend time-clock shift list, create, update, and delete exist.
- [x] Manual payroll hours endpoints exist.
- [x] Job time tracking saved report has 14 passing tests.
- [x] Timeclock/payroll saved report has 24 passing tests.

### Timesheet Source And Correction Rules
- [ ] Define which time source wins when records overlap.
- [ ] Show source for every row.
- [ ] Detect duplicate or overlapping shifts.
- [ ] Detect missing clock-out and invalid break combinations.
- [ ] Detect shifts crossing midnight.
- [ ] Define timezone used for every row.
- [ ] Define manager correction and employee dispute workflow.
- [ ] Require correction reason.
- [ ] Preserve original and corrected values.
- [ ] Prevent edits to approved/paid periods without reopening.
- [ ] Confirm job-time entries and time-clock shifts are not double counted.
- [ ] Add overlap, overnight, timezone, correction, and locked-period tests.

### Timesheet Live Clickthrough
- [ ] View one employee and all employees.
- [ ] Test current, prior, custom, and cross-month periods.
- [ ] Create normal, overnight, and split shifts.
- [ ] Add breaks and lunch.
- [ ] Correct a missed punch.
- [ ] Delete a safe draft shift.
- [ ] Confirm totals and overtime.
- [ ] Confirm source labels.
- [ ] Approve, pay, and attempt correction.
- [ ] Export and compare to visible totals.

### Timesheet Visual QA
- [ ] Check dense table readability and contrast.
- [ ] Keep dates, times, sources, totals, and actions aligned.
- [ ] Confirm narrow-screen behavior is intentional.
- [ ] Confirm invalid and overlapping rows are visibly flagged.
- [ ] Confirm empty periods do not look broken.
- [ ] Confirm every edit/delete action has confirmation and purpose.

---

## Section 6 — Time Clock

### Verified Structure And Behavior
- [x] Internal route `/timeclock` exists.
- [x] Internal Time Clock supports start work, start break, end break, and end work.
- [x] Time Clock shows status, work minutes, break minutes, and net hours.
- [x] Shared time-clock service validates action sequence.
- [x] Internal time-clock endpoints verify employee tenant ownership.
- [x] Employee portal uses the shared time-clock service.
- [x] Saved timezone, stale-status, status-x, and payroll integration reports pass.

### P0 Permission And Punch Integrity
- [ ] Enforce Time Clock Own for a linked user's own punches.
- [ ] Enforce Time Clock View All for viewing other employees.
- [ ] Enforce Time Clock Manage for punching or editing another employee.
- [ ] Prevent ordinary staff from creating or editing employee records through Time Clock.
- [ ] Confirm internal user-to-employee linking before allowing own punch.
- [ ] Prevent punches for inactive/offboarded employees.
- [ ] Add idempotency or duplicate-punch protection.
- [ ] Define offline, retry, and delayed-punch behavior.
- [ ] Define location/device verification if required.
- [ ] Record actor separately when a manager punches/corrects for an employee.
- [ ] Add permission, duplicate, inactive, retry, and manager-action tests.

### Time Clock Live Clickthrough
- [ ] Clock in.
- [ ] Attempt duplicate clock in.
- [ ] Start and end break.
- [ ] Attempt invalid sequence.
- [ ] Clock out.
- [ ] Refresh after every action.
- [ ] Test overnight shift.
- [ ] Test timezone boundary.
- [ ] Test manager punch for another employee.
- [ ] Test inactive employee.
- [ ] Confirm Time Clock, Timesheet, Payroll, and Employee Portal agree.

### Time Clock Visual And Floor-Use QA
- [ ] Confirm punch buttons are large and usable on shop-floor devices.
- [ ] Check status badge colors for contrast.
- [ ] Confirm current status is unmistakable.
- [ ] Confirm accidental double-click cannot create duplicate punches.
- [ ] Confirm action buttons do not shift unexpectedly.
- [ ] Confirm mobile has no horizontal scrolling.
- [ ] Confirm errors remain visible long enough to understand.
- [ ] Remove employee-management actions from staff-facing Time Clock.

---

## Section 7 — Employee Schedule

### Verified Structure And Behavior
- [x] Route `/employee-schedule` exists.
- [x] Schedule backend list and save endpoints exist.
- [x] Schedule is tenant and employee scoped.
- [x] Frontend checks payroll view for visibility.
- [x] Frontend restricts editing to admin/owner.
- [x] Schedule supports week navigation, off days, start/end times, notes, and weekly total.
- [x] Saved `team_schedule_features_results.xml` report has 12 passing tests.

### Schedule Rules And Permissions
- [ ] Decide whether schedule deserves separate permissions from payroll.
- [ ] Enforce schedule view/edit permissions in backend.
- [ ] Validate employee belongs to tenant.
- [ ] Validate start/end time and overnight shifts.
- [ ] Validate duplicate/overlapping schedule entries.
- [ ] Define timezone.
- [ ] Define schedule publish/draft behavior.
- [ ] Define employee notification behavior.
- [ ] Preserve schedule change history.
- [ ] Define recurring versus one-week schedules.
- [ ] Confirm schedule does not imply time worked.

### Schedule Live Clickthrough
- [ ] Select every active employee.
- [ ] Navigate previous/current/next weeks.
- [ ] Set normal, off, and overnight days.
- [ ] Add notes.
- [ ] Save and refresh.
- [ ] Confirm weekly total.
- [ ] Test unauthorized viewer/editor.
- [ ] Confirm employee can view intended schedule if launch-visible.
- [ ] Test overlapping/invalid values.

### Schedule Visual QA
- [ ] Confirm schedule table fits or scrolls intentionally.
- [ ] Confirm mobile controls stack without overlap.
- [ ] Check off-day, weekend, disabled, and error-state contrast.
- [ ] Confirm long notes fit.
- [ ] Remove large empty weeks and confusing duplicate controls.
- [ ] Confirm every control works and serves a purpose.

---

## Section 8 — Employee Portal

### Verified Structure And Behavior
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

## Section 9 — Employee Pay View

### Verified Structure And Behavior
- [x] Employee pay route exists.
- [x] Employee pay summary endpoint checks portal pay-view setting.
- [x] Pay summary includes current-period hours/earnings, year-to-date hours/earnings, last payment, and balance owed.
- [x] Pay summary uses shifts, manual hours, job-time entries, and payroll transactions.
- [x] Employee Pay page hides itself when pay view is disabled.

### P0 Pay Privacy And Accuracy
- [ ] Decide whether employee portal should show estimated earnings or approved pay stubs.
- [ ] Label estimates clearly.
- [ ] Scope all payroll transactions by tenant.
- [ ] Use approved payroll calculation rules including overtime where intended.
- [ ] Prevent double-counting time sources.
- [ ] Ensure advances, payments, adjustments, and carryover use the same payroll contract.
- [ ] Confirm year-to-date values use the correct calendar/payroll year.
- [ ] Confirm last payment belongs to the same tenant and employee.
- [ ] Define visibility for rate, overtime, adjustments, notes, and payment history.
- [ ] Hide pay completely when disabled.
- [ ] Add employee-pay versus payroll reconciliation tests.
- [ ] Obtain privacy/payroll approval.

### Employee Pay Live Clickthrough
- [ ] View pay as enabled employee.
- [ ] Confirm disabled employee cannot access direct endpoint.
- [ ] Compare current hours and earnings to approved payroll.
- [ ] Compare year-to-date totals.
- [ ] Compare last payment and balance.
- [ ] Test after adjustment, payment, rate change, correction, and period approval.
- [ ] Confirm another employee's pay is inaccessible.
- [ ] Confirm error and empty states.

### Pay View Visual QA
- [ ] Check money values, labels, warnings, and disabled states for contrast.
- [ ] Clearly distinguish estimated, approved, paid, and owed amounts.
- [ ] Confirm amounts and dates fit on mobile.
- [ ] Avoid showing unexplained or misleading balances.
- [ ] Confirm no sensitive pay data appears in screenshots/navigation previews unnecessarily.

---

## Section 10 — Employee Tasks

### Verified Structure And Behavior
- [x] Internal task CRUD endpoints exist.
- [x] Tasks are tenant scoped in standard internal endpoints.
- [x] Productivity unifies tasks with jobs, appointments, schedules, and production tasks.
- [x] Productivity supports dashboard, calendar, kanban, and task-list views.
- [x] Employee portal lists assigned tasks.
- [x] Employee portal can complete assigned tasks.
- [x] Saved `productivity_unified_results.xml` report has 23 passing tests.
- [x] Saved `productivity_phase2_results.xml` report has 16 tests with 10 skipped.

### P0 Task Permissions And Cross-Module Integrity
- [ ] Define task view, create, edit, assign, complete, reopen, and delete permissions.
- [ ] Enforce backend permissions on Tasks and Productivity.
- [ ] Enforce backend permissions on production-task stage configuration and updates.
- [ ] Validate assignee belongs to tenant.
- [ ] Add tenant scope to employee portal task list and completion.
- [ ] Add tenant scope to production-task ticket lookup, update, and post-update lookup.
- [ ] Confirm employee can complete only assigned task.
- [ ] Define whether employee can reopen or edit task.
- [ ] Confirm Productivity edits do not bypass source-module rules.
- [ ] Replace skipped writeback, drag/drop, and cross-view tests with seeded fixtures.
- [ ] Add cross-tenant and unauthorized-role task tests.

### Employee Task Live Clickthrough
- [ ] Create and assign a task.
- [ ] Confirm it appears internally and in employee portal.
- [ ] Complete it in employee portal.
- [ ] Confirm all internal views update.
- [ ] Edit priority, due date, and assignee.
- [ ] Drag through Kanban if launch-visible.
- [ ] Reopen and reassign.
- [ ] Delete/archive a safe task.
- [ ] Test production task and assigned job stage behavior.
- [ ] Confirm every task action works and serves a purpose.

### Task Visual And Flow QA
- [ ] Confirm Tasks, Productivity, Production Tasks, and assigned job stages have distinct purposes.
- [ ] Remove duplicate or conflicting task actions.
- [ ] Check status, priority, due-date, and assignment colors for contrast.
- [ ] Confirm Task List and Kanban narrow-screen behavior.
- [ ] Confirm long titles and customer/job names fit.
- [ ] Confirm drag/drop has keyboard-accessible alternatives.
- [ ] Confirm no dead links, blank views, or false success.

---

## Category-Wide Audit, Retention, And Compliance

- [ ] Define retention for employee, user, schedule, time, payroll, task, and portal-auth records.
- [ ] Define access logging for sensitive compensation data.
- [ ] Record actor and before/after values for rate, hours, adjustments, payment, role, PIN reset, and offboarding changes.
- [ ] Prevent ordinary users from altering audit history.
- [ ] Define employee data export and deletion handling.
- [ ] Define legal hold and payroll-record retention.
- [ ] Define backup and restore verification.
- [ ] Confirm offboarding preserves required records while revoking access.
