# Team / Workforce Ribbon Rebuild Spec

Last updated: April 5, 2026

Status: **Saved for later implementation — not started**

Use this file as the source of truth when the Team / Workforce ribbon rebuild begins later.

---

## Purpose

Rebuild the entire **Team / Workforce** module so it behaves like a real desktop business application with a **Microsoft Office style ribbon** under the main **Team** navigation tab. The current system is confusing, duplicated, oversized, hard to scan, and mixes employee workflows with admin workflows in the wrong places.

This rebuild must create a clear, compact, dense, professional workforce system that covers:
- Overview
- Time
- Payroll
- Schedule
- Employees
- Exports
- Settings
- Employee Portal navigation related to time, pay, schedule, and hours

This is not a visual polish request only. It is a **layout, navigation, workflow, data clarity, and system logic cleanup**.

---

# 1. Overall navigation structure

## Main app level navigation
The overall app already has a top level navigation. Under that system, **Team** should remain one main top-level tab.

Examples of app-level tabs:
- Dashboard
- Orders
- Billing
- Customers
- Webstores
- Documents
- Team
- AI Tools
- Financials
- Productivity
- Reports
- Community
- Settings

## Team module structure
When the user clicks **Team**, show a second row of **Team sub-tabs** directly below the main app nav.

### Team sub-tabs
Use these sub-tabs in this exact order:
1. Overview
2. Time
3. Payroll
4. Schedule
5. Employees
6. Exports
7. Settings

## Ribbon behavior
Directly below the Team sub-tabs, show a true **ribbon toolbar**.
The ribbon must change depending on the active Team sub-tab.

### Required ribbon behavior
- Ribbon stays visible while inside the Team module
- Ribbon content changes when a Team sub-tab changes
- Ribbon groups are separated visually by vertical dividers
- Ribbon group labels appear at the bottom of each group
- Ribbon is compact and desktop-like, not giant cards
- Active Team sub-tab must be visually obvious
- Inactive Team sub-tabs must still look clickable
- Ribbon items should use icon + label
- Buttons should be compact and short enough to avoid unnecessary horizontal overflow
- Prefer tighter spacing and shorter labels where possible
- Do not make the ribbon look like a dashboard full of floating cards

## Design goal
The Team module should feel like:
- Microsoft Office ribbon behavior
- GraphiXCalc / older desktop business software structure
- compact professional admin software

It should **not** feel like:
- giant mobile cards
- a modern landing page
- floating widget panels
- hidden tabs that do not look clickable

---

# 2. Admin vs Employee separation

## Employee portal
The employee portal is where employees should:
- clock in
- start break
- end break
- clock out
- view pay
- view schedule
- view hours
- view tasks if enabled

Employee portal can be simpler and slightly larger.

## Admin Team module
The Team module under the admin side is where the admin should:
- review timecards
- review raw time entries
- fix missing punches
- manage payroll
- manage schedule
- manage employees
- export workforce reports
- configure workforce settings

The admin side must be:
- more compact
- more dense
- more table-driven
- less padded
- easier to scan quickly

Do not use giant time clock style buttons as the main admin workflow.

---

# 3. Team sub-tab definitions and ribbon contents

---

# 3A. OVERVIEW TAB

## Purpose
Overview is the control panel for the Team module. It should answer:
1. What is happening right now?
2. What needs attention first?
3. Where do I click next?

Overview must **not** become a vague summary dashboard with numbers that do nothing.

## Overview ribbon groups
Use these ribbon groups in this exact order:
1. Views
2. Alerts
3. Quick Actions
4. Filters
5. Open

## Overview ribbon items and exact behavior

### Group: Views
#### Summary
Show overall workforce summary.

**What it does:**
- Loads the default overview dashboard
- Shows current workforce status across time, payroll, and schedule

**What appears in main content:**
- Working Now
- On Break
- Today Hours
- Week Hours
- Pending Payroll Review
- Missing Punches
- Pending Edits
- Open schedule issues

#### Today
Show only today-focused workforce information.

**What it does:**
- Filters Overview to today only

**What appears in main content:**
- who is clocked in now
- who is late
- who is missing punches today
- today’s scheduled shifts
- today’s unresolved issues

#### Week
Show current week workforce summary.

**What it does:**
- Filters Overview to the current week

**What appears in main content:**
- week total hours
- week overtime buildup
- unresolved punch issues this week
- upcoming schedule gaps
- payroll review items for this week

### Group: Alerts
#### Missing Punches
Open missing punch / exception list.

**What it does:**
- Opens or filters the unresolved time problems list

**Show columns like:**
- Employee
- Date
- Issue Type
- Current Punches
- Suggested Fix
- Status
- Resolve

#### Late / Absent
Open attendance exceptions tied to schedule.

**What it does:**
- Shows employees who are late, absent, not clocked in, or otherwise not matching today’s schedule

**Show columns like:**
- Employee
- Scheduled Start
- Actual Clock In
- Status
- Minutes Late

#### Recent Edits
Open recent edits / pending edit review.

**What it does:**
- Shows recent manual changes to time or payroll-affecting data

**Show columns like:**
- Employee
- Date
- What Changed
- Edited By
- Time Changed
- Reason
- Review Status

### Group: Quick Actions
#### Manual Punch
Open add manual punch modal.

**Required fields:**
- Employee
- Date
- Time
- Punch Type
- Note / Reason

#### Transaction
Open quick payroll transaction modal.

**Supported types:**
- Advance
- Deduction
- Reimbursement
- Bonus
- Manual Correction

#### Approve
Approve selected reviewed time or payroll items.

**Behavior:**
- Only works on selected rows or filtered reviewed records
- Must not blindly approve everything on screen

### Group: Filters
#### Employee dropdown
Filter Overview by one employee, many employees, or all employees.

#### Status dropdown
Filter Overview by statuses such as:
- Working
- On Break
- Clocked Out
- Missing Punch
- Late
- Needs Review
- Approved
- Paid

#### Date Range dropdown
Choose actual date context such as:
- Today
- This Week
- Current Pay Period
- Custom Range

### Group: Open
These are jump shortcuts.

#### Time
Jump to Time tab.
Try to preserve filters/context if possible.

#### Payroll
Jump to Payroll tab.
Try to preserve period/context if possible.

#### Schedule
Jump to Schedule tab.
Try to preserve relevant date/context if possible.

## Overview main page layout

### Top summary row
Compact summary cards:
- Working Now
- On Break
- Today Hours
- Week Hours
- Pending Payroll
- Missing Punches

### Main content area
Use a 2-column or split layout:

#### Left/main column
- prioritized alerts list
- workforce status table
- open problems and pending actions

#### Right/sidebar column
- quick actions
- recent edits
- shortcuts into Time, Payroll, Schedule

## Overview must not include
- full payroll detail tables
- full schedule editor
- giant decorative cards
- duplicate versions of Time or Payroll

---

# 3B. TIME TAB

## Purpose
Time is the admin’s main time review area. It answers:
1. What time was worked?
2. What punch events were recorded?
3. What is broken?
4. What is ready for approval?

## Time ribbon groups
Use these ribbon groups in this exact order:
1. Time Views
2. Range
3. Actions
4. Filters
5. Export

## Time ribbon items and exact behavior

### Group: Time Views
#### Timecards
This opens the main calculated timecard view.

**This should be the default Time view.**

**Show one row per employee per day with columns like:**
- Date
- Employee
- Scheduled Shift
- Clock In
- Clock Out
- Break
- Worked Hours
- Regular Hours
- Overtime Hours
- Pay Rate
- Daily Pay
- Adjustments
- Status
- Edit

#### Time Entries
This opens raw punch entries.

**Show columns like:**
- Timestamp
- Employee
- Punch Type
- Source
- Notes
- Edited?
- Edited By
- Edit Reason

Make it clear that:
- Time Entries = raw punch log
- Timecards = calculated daily totals

#### Missing Punches
Open unresolved punch exception list.

**Show issues like:**
- clock in with no clock out
- break start with no break end
- invalid sequence
- long shift needing review

### Group: Range
#### Day
Show one selected day.

#### Week
Show one full week.
This should be one of the most important review ranges.

#### Pay Period
Show the full payroll period.
Important for payroll prep and exports.

#### Month
Show a monthly hours summary or wider time review.

### Group: Actions
#### Manual Punch
Open modal/drawer to add a manual punch.

#### Edit Entry
Edit selected time entry or selected timecard detail.
Every edit must store:
- who edited
- when edited
- why edited

#### Approve Time
Approve selected week or selected reviewed time data.

Suggested statuses:
- Draft
- Needs Review
- Approved
- Sent to Payroll

### Group: Filters
#### Employee dropdown
Show one employee, multiple employees, or all employees.

#### Status dropdown
Filter by:
- Working
- On Break
- Clocked Out
- Missing Punch
- Needs Review
- Approved
- Draft

#### Date Range dropdown
Choose exact date/week/pay period/month.

### Group: Export
#### Weekly Sheet
Export weekly time sheet.

#### Pay Period Export
Export pay period time sheet.

#### Print View
Print current time view.

## Time main page layout

### Main/default view
Timecards table should fill the main area.

### Secondary panel
Use right-side detail drawer or side panel for:
- exact punches
- notes
- edit history
- schedule for that day
- adjustments affecting that day

### Layout requirements
- use compact tables
- use dense rows
- reduce vertical padding
- keep more records above the fold
- avoid giant cards

---

# 3C. PAYROLL TAB

## Purpose
Payroll answers:
1. How much does each employee get paid?
2. Why is that amount what it is?
3. What still needs review, approval, or payment?

## Payroll ribbon groups
Use these ribbon groups in this exact order:
1. Views
2. Period
3. Actions
4. Filters
5. Export

## Payroll ribbon items and exact behavior

### Group: Views
#### Payroll Summary
Default payroll screen.

**Show one row per employee with columns like:**
- Employee
- Pay Rate
- Regular Hours
- Overtime Hours
- Gross Pay
- Advances
- Deductions
- Bonuses / Reimbursements
- Net Owed
- Payroll Status

#### Employee Detail
Open detailed payroll breakdown for selected employee.

**Show:**
- each day worked
- daily time data
- regular/overtime split
- daily pay
- advances
- deductions
- reimbursements
- final gross and net totals

#### Year to Date
Show YTD payroll summary.

### Group: Period
#### Current Period
Jump to current payroll period.

#### Previous Period
Jump to previous payroll period.

#### Custom Period
Choose custom payroll range.

### Group: Actions
#### Add Advance
Add payroll advance.

**Required fields:**
- Employee
- Date
- Amount
- Note
- Apply to current payroll yes/no

#### Add Deduction
Add deduction.

**Required fields:**
- Employee
- Date
- Amount
- Type
- Note
- Apply now yes/no

#### Mark Paid
Mark selected payroll row or batch as paid.

**Store:**
- payment date
- who marked it paid
- optional note or method

### Group: Filters
#### Employee dropdown
Filter payroll by selected employee(s).

#### Status dropdown
Use label **Status**, not State.

Status examples:
- Draft
- Needs Review
- Approved
- Paid
- Exception

#### Pay Period dropdown
Choose exact named pay period.

### Group: Export
#### Payroll Summary
Export payroll summary.

#### Payroll Detail
Export detailed payroll breakdown.

#### Print View
Print current payroll view.

## Payroll main page layout

### Main/default area
Payroll summary table in main column.

### Right-side detail panel
Show selected employee payroll detail including:
- regular hours
- overtime
- advance
- deductions
- net owed
- calculation breakdown

## Payroll requirements
- payroll totals must clearly tie back to time and transactions
- approval and paid should be separate ideas
- strongly recommend statuses:
  - Draft
  - Needs Review
  - Approved
  - Paid

---

# 3D. SCHEDULE TAB

## Purpose
Schedule answers:
1. Who is supposed to work and when?
2. What shifts are missing, conflicting, or unpublished?
3. How do I add, edit, copy, publish, and send schedules?

## Schedule ribbon groups
Use these ribbon groups in this exact order:
1. Views
2. Actions
3. Publish
4. Filters
5. Export

## Schedule ribbon items and exact behavior

### Group: Views
#### Day View
Show selected day schedule.

#### Week View
Show weekly schedule.
This should likely be the default schedule view.

#### Month View
Show broader monthly schedule.

### Group: Actions
#### Add Shift
Open shift creation modal/drawer.

**Required fields:**
- Employee
- Date
- Start Time
- End Time
- Break Expectation
- Role / Task
- Notes
- Open Shift or Assigned Shift

#### Edit Shift
Edit selected shift.

#### Copy Schedule
Copy:
- previous week to current week
- day to day
- employee pattern to another employee

### Group: Publish
#### Publish Schedule
Mark schedule as official/visible to employees.

#### Notify Employees
Send notice that schedule was published or changed.

#### Repeat Pattern
Apply repeating schedule pattern.

### Group: Filters
#### Employee dropdown
Filter one employee or all.

#### Location dropdown
Only show if multiple locations / work areas matter. Hide if not needed yet.

#### Date Range dropdown
Choose exact day/week/month/custom range.

### Group: Export
#### Export Schedule
Export current schedule.

#### Export PDF
Export printable PDF.

#### Print View
Print current schedule view.

## Schedule main page layout

### Main/default area
Weekly schedule grid or table.

### Main views required
- Day
- Week
- Month
- optional Employee View

### Schedule table/grid should show
- Employee
- Date
- Start
- End
- Role
- Status
- Notes if needed

## Schedule rules
- there must be one clear admin schedule area only
- do not duplicate schedule editors inside unrelated tabs
- schedule detail may appear in side drawers elsewhere as reference only

---

# 3E. EMPLOYEES TAB

## Purpose
Employees tab answers:
1. Who are my employees?
2. How do I manage access and pay setup?
3. How do I keep employee management out of Time and Payroll screens?

## Employees ribbon groups
Use these ribbon groups in this exact order:
1. Employee
2. Access
3. Pay
4. Filters

## Employees ribbon items and exact behavior

### Group: Employee
#### Add Employee
Create new employee record.

**Required fields:**
- First Name
- Last Name
- Display Name
- Email
- Phone
- Role
- Status
- Pay Rate
- Hire Date
- Portal Enabled yes/no

#### Edit Employee
Edit selected employee.

#### Deactivate
Use label **Deactivate**, not Off.
Deactivate employee without deleting history.

### Group: Access
#### Invite Portal
Send employee portal invitation.

#### Reset PIN
Reset or set employee kiosk/PIN access.

#### Reset Access / Password Reset
Reset portal password/access.

### Group: Pay
#### Pay Rate
Set pay rate with effective date.

#### OT Rule
Set employee-specific overtime rule if needed.

#### Start Setup / Opening Balance
Rename current vague label **Start** to a clearer term.
Use it for:
- opening payroll setup
- starting balance
- start date related payroll setup

### Group: Filters
#### Role dropdown
Filter employees by role.

#### Status dropdown
Filter employees by active/inactive/portal status.

#### Search
Search employee by name/email/role.

## Employees main page layout

### Main/default area
Compact employee directory table.

**Suggested columns:**
- Name
- Role
- Email
- Phone
- Pay Rate
- Status
- Portal Status
- Last Active
- Edit

## Employees rules
All employee management actions should live here, not scattered through time and payroll screens.

---

# 3F. EXPORTS TAB

## Purpose
Exports answers:
1. What report do I need?
2. What file format do I need?
3. Who or what date range should it cover?

## Exports ribbon groups
Use these ribbon groups in this exact order:
1. Time
2. Payroll
3. Format
4. Scope

## Exports ribbon items and exact behavior

### Group: Time
#### Weekly Sheet
Export weekly time sheet.

#### Pay Period
Export pay period time report.

#### Monthly Hours
Export monthly hours summary.

### Group: Payroll
#### Payroll Summary
Export payroll summary.

#### Payroll Detail
Export detailed payroll report.

#### Transactions
Rename current Txn label to **Transactions** or **Payroll Txns**.
Export payroll-affecting transactions.

### Group: Format
#### PDF
Export printable PDF.

#### Excel
Export structured spreadsheet.

#### CSV
Export raw structured data.

### Group: Scope
#### One Employee
Export selected employee only.

#### All Employees
Export everyone in current scope.

#### Date Range
Custom range export.

## Export flow requirement
After choosing export type + format + scope, show a small export settings panel/modal with fields like:
- employee selector if needed
- date range / pay period
- include pay rate yes/no
- include notes yes/no
- final Export button

## Exports main page layout
Use a central exports table/list showing:
- export type
- formats available
- what it includes

## Export headers must include where relevant
- company name
- report title
- selected employee or all employees
- selected date range
- generated date
- page numbers for PDF if applicable

---

# 3G. SETTINGS TAB

## Purpose
Settings controls the rules of the Team module.
It answers:
1. How is time grouped?
2. How is overtime calculated?
3. How does payroll approval work?
4. What should employees be allowed to see?
5. How compact should the workforce screens be?

## Settings ribbon groups
Use these ribbon groups in this exact order:
1. Time Rules
2. Payroll
3. Display

## Settings ribbon items and exact behavior

### Group: Time Rules
#### Week Start
Choose start day of week.

#### OT Rule
Set default overtime rule.

#### Break Rules
Set break behavior.

Possible options:
- manual break tracking
- required break start/end
- auto lunch deduction
- paid vs unpaid break
- missing break warnings

### Group: Payroll
#### Pay Period
Set payroll grouping:
- Weekly
- Bi-Weekly
- Semi-Monthly
- Monthly

#### Transaction Types
Control allowed payroll adjustment types.

#### Approval Flow
Configure:
- require approval before paid
- lock after approval yes/no
- allow edit after approval yes/no
- require edit reason after approval yes/no

### Group: Display
#### Compact Mode
Toggle compact vs comfortable workforce layout.
Compact mode should reduce:
- row height
- padding
- ribbon spacing
- dead space

#### Status Colors
Control colors for statuses like:
- working
- on break
- clocked out
- approved
- paid
- missing punch

#### Portal Options
Control employee portal visibility:
- enable clock
- enable pay
- enable schedule
- enable hours
- enable tasks
- hide unpublished schedule
- allow portal clocking in/out

## Settings main page layout
Use grouped settings sections:

### Time Tracking Defaults
- week start
- overtime rule
- break rule type
- auto lunch
- missing punch behavior

### Payroll Defaults
- pay period type
- transaction types
- approval flow
- lock after approval
- allow edits after approval

### Display Preferences
- compact mode
- table density
- colors
- visual cleanup

### Employee Portal Settings
- enable time clock
- enable pay view
- enable schedule view
- enable hours view
- enable tasks view

---

# 4. Main content layout rules for the Team module

## General layout
Every Team sub-tab page should use this basic structure:

### Row 1
Main app navigation (already existing app-level row)

### Row 2
Team sub-tab row:
- Overview
- Time
- Payroll
- Schedule
- Employees
- Exports
- Settings

### Row 3
Contextual ribbon for the active Team sub-tab

### Row 4 and below
Actual page content

## Content layout rules
- use compact tables where possible
- reduce card height
- reduce white space
- do not over-stack giant sections
- use side drawers or side panels for detail instead of giant repeated cards
- keep admin pages scan-friendly
- preserve filters when jumping between related tabs if possible

## Recommended detail pattern
Use this pattern repeatedly:
- main table/grid on left or center
- detail drawer or side panel on right

That should be used in:
- Time
- Payroll
- Schedule where relevant

---

# 5. Employee portal requirements

## Employee portal navigation
The employee portal must always have a clear way to move between:
- Clock
- Pay
- Schedule
- Hours
- Tasks if enabled

Use a persistent top nav or mini ribbon for the employee portal.

## Employee portal pages

### Clock
Show:
- current status
- current time/date
- clocked in since
- today’s worked time
- today’s break time
- Clock In / Start Break / End Break / Clock Out
- today’s punches
- this week’s total hours
- today’s shift if scheduled

### Pay
Show:
- current pay period earnings
- current pay period hours
- pending amount
- year-to-date earnings
- year-to-date hours
- last payment
- payment history

### Schedule
Show:
- published schedule only unless settings allow otherwise
- day/week view of assigned shifts

### Hours
Show:
- recent worked hours
- weekly totals
- prior timecard summaries if allowed

## Employee portal requirement
There must always be an obvious route back to Clock after opening Pay or another page.

---

# 6. Data and logic requirements that must support this UI

This rebuild must not be visual only. The UI must map to a clean logical structure.

## Core workforce data structures
Use or normalize around:
- Employees
- Time Punches
- Daily Timecards
- Weekly Timecards
- Payroll Periods
- Payroll Transactions
- Schedule Shifts

## Time Punch fields
Each punch must store:
- employee id
- timestamp
- punch type
- source
- edited flag
- edited by
- edit reason

Punch types:
- clock_in
- break_start
- break_end
- clock_out

## Daily time calculations must derive:
- first clock in
- last clock out
- break total
- worked hours
- regular hours
- overtime hours
- daily pay if shown

## Payroll transactions must support:
- advance
- deduction
- reimbursement
- bonus
- manual correction

Each transaction should store:
- employee
- date
- amount
- type
- note
- apply to payroll now yes/no

## Status concepts to support
At minimum:
- Draft
- Needs Review
- Approved
- Paid

## Schedule logic
Need support for:
- assigned shift
- open/unfilled shift
- draft schedule
- published schedule

---

# 7. Styling and spacing requirements

## Admin side visual requirements
- compact desktop-style interface
- tighter spacing
- smaller ribbon buttons
- smaller icons
- smaller summary cards than current version
- more rows visible without scrolling
- clearer active states
- stronger clickability cues

## Do not do these things
- do not use giant pill cards for ribbon groups
- do not make every screen tall and airy
- do not mix employee management buttons into time review pages
- do not duplicate schedule sections across unrelated screens
- do not bury raw entries behind weak tabs
- do not let Time Sheets and Time Entries feel disconnected

## Color requirements
Use consistent, professional status colors:
- working = green
- on break = amber
- clocked out = neutral gray
- missing/problem = red or amber
- approved = green
- paid = darker success/accent

Ensure strong text contrast everywhere.

---

# 8. Label corrections for the real UI

Use these clearer labels instead of overly short mockup labels.

## Overview
- Missing → Missing Punches
- Late → Late / Absent
- Txn → Transaction
- Sched → Schedule

## Time
- Cards → Timecards
- Entries → Time Entries
- Missing → Missing Punches
- Period → Pay Period
- Punch → Manual Punch
- Edit → Edit Entry
- Approve → Approve Time
- Emp ▼ → Employee ▼
- Date ▼ → Date Range ▼
- Weekly → Weekly Sheet
- Period → Pay Period Export

## Payroll
- Summary → Payroll Summary
- Detail → Employee Detail
- YTD → Year to Date
- Current → Current Period
- Prev → Previous Period
- Advance → Add Advance
- Deduct → Add Deduction
- Paid → Mark Paid
- State ▼ → Status ▼
- Period ▼ → Pay Period ▼

## Schedule
- Shift → Add Shift
- Edit → Edit Shift
- Copy → Copy Schedule
- Publish → Publish Schedule
- Notify → Notify Employees
- Repeat → Repeat Pattern
- Loc ▼ → Location ▼
- Range ▼ → Date Range ▼
- Sched → Export Schedule

## Employees
- Off → Deactivate
- Invite → Invite Portal
- PIN → Reset PIN
- Reset → Reset Access or Password Reset
- Rate → Pay Rate
- OT → OT Rule
- Start → Start Setup or Opening Balance

## Exports
- Period → Pay Period
- Month → Monthly Hours
- Txn → Transactions
- One → One Employee
- All → All Employees
- Range → Date Range

## Settings
- Week → Week Start
- OT → OT Rule
- Period → Pay Period
- Types → Transaction Types
- Approval → Approval Flow
- Compact → Compact Mode
- Colors → Status Colors
- Portal → Portal Options

---

# 9. Acceptance criteria

This Team module rebuild is not complete unless all of the following are true:

1. Team has sub-tabs for Overview, Time, Payroll, Schedule, Employees, Exports, Settings
2. Each sub-tab has its own contextual ribbon
3. Ribbon groups are compact, clear, and feel like desktop software
4. Timecards and Time Entries are clearly separated but connected logically
5. Payroll clearly explains totals and supports advances/deductions/paid state
6. Schedule exists in one clear admin location only
7. Employees tab contains employee management and access tools
8. Exports tab can export weekly, pay period, payroll, and monthly workforce reports
9. Settings tab controls real workforce rules, not fake placeholder toggles
10. Employee portal has persistent navigation back to Clock, Pay, Schedule, Hours
11. The admin Team module is compact and easier to scan than the current version
12. Tabs look clickable and obvious without guessing
13. Data does not disappear when switching related views
14. The system feels like one organized workforce module, not disconnected pages

---

# 10. Build order

Implement in this order:

1. Team navigation structure and ribbon framework
2. Time tab and timecard/raw entry clarity
3. Payroll tab and payroll calculation display
4. Schedule tab and schedule cleanup
5. Employees tab and employee management relocation
6. Exports tab and export workflows
7. Settings tab and workforce rule controls
8. Employee portal navigation cleanup
9. compact styling and density polish across all Team pages

After each phase, report:
- files changed
- screens changed
- logic changed
- what was tested
- what remains

Do not mark a phase complete unless it works end-to-end.