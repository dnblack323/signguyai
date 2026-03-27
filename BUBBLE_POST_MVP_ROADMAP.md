# Sign Guy AI - Post-MVP Re-Integration Roadmap

## DOCUMENT PURPOSE

This roadmap defines the **locked sequence** for adding features after MVP launch. Each phase is dependency-safe and builds on the previous phase. **Do not skip phases or reorder.**

---

## MVP BASELINE (DO NOT MODIFY)

### What Exists After MVP

**Data Types (8):**
- ✅ Customer
- ✅ Job
- ✅ JobItem
- ✅ Invoice (+ InvoiceLineItem embedded)
- ✅ Employee
- ✅ TimeLog
- ✅ PayrollTransaction
- ✅ ExpenseEntry

**Option Sets (7):**
- ✅ CustomerStatus (lead, active, inactive)
- ✅ OrderStatus (quoted, approved, in_production, complete)
- ✅ JobItemStatus (pending, in_production, done)
- ✅ JobItemType (banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other)
- ✅ InvoiceStatus (draft, sent, paid)
- ✅ PayrollTransactionType (earnings, payment)
- ✅ TimeLogAction (start_work, end_work)

**Pages (8):**
- ✅ Dashboard
- ✅ Customers
- ✅ Orders (list)
- ✅ Order Details
- ✅ Invoices
- ✅ Time Clock
- ✅ Payroll
- ✅ Financials (expenses only)

**Workflows (22):**
- ✅ Customer CRUD (3)
- ✅ Job CRUD + status (4)
- ✅ JobItem CRUD + recalc (4)
- ✅ Invoice CRUD + from job + paid (5)
- ✅ Time clock in/out + hours (3)
- ✅ Payroll transactions + balance (3)

---

## PHASE 1: Job Notes & Activity Logging

**Purpose:** Add internal notes and audit trail to orders
**Estimated Time:** 3-4 hours
**Risk Level:** 🟢 Low

### DO NOT START UNTIL

```
□ MVP is deployed and stable
□ All MVP workflows tested and working
□ Order Details page loads without errors
□ JobItem CRUD confirmed working
□ No pending bug fixes in Job module
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Job data type | Database | ✅ MVP |
| Order Details page | Pages | ✅ MVP |
| JobItem workflows | Workflows | ✅ MVP |

### Add: Option Sets (1)

| Option Set | Values | Notes |
|------------|--------|-------|
| JobActivityType | created, status_changed, item_added, item_updated, item_deleted, note_added, completed | For activity log entries |

### Add: Data Types (2)

| Type | Fields | Depends On |
|------|--------|------------|
| JobNote | id, job (→Job), content, author, created_at | Order |
| JobActivity | id, job (→Job), activity_type (→JobActivityType), description, old_value, new_value, created_at | Order |

### Add: Workflows (6)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Create OrderNote | Add note button | Job exists |
| Delete JobNote | Delete note button | JobNote exists |
| Create OrderActivity | Called by other workflows | Job exists |
| Log Item Added | After JobItem created | JobItem create workflow |
| Log Item Updated | After JobItem updated | JobItem update workflow |
| Log Status Changed | After Job status change | Job status workflow |

### Modify: Existing Workflows (4)

| Workflow | Modification |
|----------|--------------|
| Create Order | Add step: Create OrderActivity (type=created) |
| Update Order Status | Add step: Create OrderActivity (type=status_changed) |
| Create OrderItem | Add step: Create OrderActivity (type=item_added) |
| Update JobItem | Add step: Create OrderActivity (type=item_updated) |
| Delete JobItem | Add step: Create OrderActivity (type=item_deleted) |

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Order Details | Add Notes tab with note list and add form |
| Order Details | Add Activity tab with activity log |

### Verification Checklist

```
□ Can add note to job
□ Note appears in notes list
□ Activity logged when note added
□ Can delete note
□ Activity logged on order creation
□ Activity logged on status change
□ Activity logged on item add/edit/delete
□ Activity tab shows correct history
□ No errors in existing JobItem workflows
```

---

## PHASE 2: Break Tracking & Time Clock Enhancement

**Purpose:** Add break tracking to time clock
**Estimated Time:** 2-3 hours
**Risk Level:** 🟢 Low

### DO NOT START UNTIL

```
□ Phase 1 complete and verified
□ Time Clock page working correctly
□ Clock in/out creating TimeLogs
□ Daily hours calculating correctly
□ No pending payroll issues
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Employee data type | Database | ✅ MVP |
| TimeLog data type | Database | ✅ MVP |
| Time Clock page | Pages | ✅ MVP |
| Clock in/out workflows | Workflows | ✅ MVP |

### Modify: Option Sets (1)

| Option Set | Modification |
|------------|--------------|
| TimeLogAction | Add: break_start, break_end |

### Add: Data Types (0)

No new types - using existing TimeLog

### Add: Workflows (3)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Start Break | Break Start button | Active shift (clocked in) |
| End Break | Break End button | Active break |
| Calculate Shift Summary | On employee select | TimeLogs exist |

### Modify: Existing Workflows (1)

| Workflow | Modification |
|----------|--------------|
| Calculate Today's Hours | Update to subtract break time |

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Time Clock | Add Break Start / Break End buttons |
| Time Clock | Add break time to summary |
| Time Clock | Update button states for break sequence |

### Button State Logic (New)

```
Start Work: enabled when (no logs today) OR (last = end_work)
Break Start: enabled when (last = start_work) OR (last = break_end)
Break End: enabled when (last = break_start)
End Work: enabled when (last = start_work) OR (last = break_end)
```

### Verification Checklist

```
□ Can start break after clocking in
□ Break Start button disabled when not valid
□ Can end break
□ Break End button disabled when not on break
□ Can start multiple breaks in one shift
□ Can end work after break ends
□ Break time shows in summary
□ Net hours = work time - break time
□ Original clock in/out still works
```

---

## PHASE 3: Quotes & Estimates

**Purpose:** Add quote creation and quote-to-job conversion
**Estimated Time:** 5-6 hours
**Risk Level:** 🟡 Medium (circular dependency)

### DO NOT START UNTIL

```
□ Phase 2 complete and verified
□ Job creation workflow working
□ JobItem creation workflow working
□ Job Activity logging working (Phase 1)
□ Customer CRUD working
□ No pending Job module bugs
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Customer data type | Database | ✅ MVP |
| Job data type | Database | ✅ MVP |
| JobItem data type | Database | ✅ MVP |
| JobActivity workflows | Workflows | ✅ Phase 1 |

### Add: Option Sets (1)

| Option Set | Values | Notes |
|------------|--------|-------|
| QuoteStatus | draft, sent, approved, declined | Quote lifecycle |

### Add: Data Types (2)

| Type | Fields | Depends On |
|------|--------|------------|
| Quote | id, customer (→Customer), line_items (list of QuoteLineItem), notes, status (→QuoteStatus), total, job (→Job, **add after Job.quote exists**), created_at, updated_at | Customer |
| QuoteLineItem | description, quantity, unit_price, total | Embedded in Quote |

### Modify: Existing Data Types (1)

| Type | Modification |
|------|--------------|
| Order | Add field: quote (→Quote) |

### Add: Circular Reference

```
⚠️ CIRCULAR DEPENDENCY HANDLING:

Step 1: Create Quote type WITHOUT job field
Step 2: Add quote field to Job type
Step 3: Add job field to Quote type
Step 4: Test both directions work
```

### Add: Workflows (8)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Create Quote | Submit quote form | Customer exists |
| Update Quote | Submit quote edit | Quote exists, not converted |
| Delete Quote | Delete button | Quote exists, not converted |
| Add Quote Line Item | Add item button | Quote exists |
| Update Quote Line Item | Edit item | QuoteLineItem exists |
| Delete Quote Line Item | Delete item | QuoteLineItem exists |
| Recalculate Quote Total | After line item change | Quote exists |
| Convert Quote to Job | Convert button | Quote exists, not converted |

### Convert Quote to Job Workflow (Detailed)

```
Trigger: Convert button clicked
Condition: This Quote's job is empty

Step 1: Create Order
  - customer = Quote's customer
  - name = "Job from Quote #" + Quote's unique id:truncated to 8
  - description = Quote's notes
  - status = approved
  - quote = This Quote
  - subtotal = Quote's total

Step 2: For each Quote's line_items → Schedule API workflow
  - Create OrderItem
  - job = Result of Step 1
  - item_type = other
  - description = line_item's description
  - quantity = line_item's quantity
  - unit_price = line_item's unit_price
  - line_total = line_item's total
  - status = pending

Step 3: Make changes to Quote
  - job = Result of Step 1
  - status = approved

Step 4: Create OrderActivity
  - job = Result of Step 1
  - activity_type = (add new value: quote_converted)
  - description = "Created from Quote"
```

### Modify: Option Sets (1)

| Option Set | Modification |
|------------|--------------|
| JobActivityType | Add: quote_converted |

### Add: Pages (1)

| Page | Components |
|------|------------|
| Quotes | Quote list with status filter |
| | Create/Edit quote popup with line items |
| | Convert to Job button |
| | Status change dropdown |

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Dashboard | Add quote count to stats (optional) |
| Order Details | Show linked quote info if exists |

### Verification Checklist

```
□ Can create quote for customer
□ Can add line items to quote
□ Quote total calculates correctly
□ Can edit quote (when not converted)
□ Can change quote status
□ Can convert quote to job
□ Job created with correct data
□ JobItems created from line items
□ Quote shows linked job after conversion
□ Job shows linked quote
□ Cannot convert same quote twice
□ Cannot edit converted quote
□ Activity log shows "quote_converted"
```

---

## PHASE 4: Invoice Enhancements

**Purpose:** Add due dates, overdue tracking, partial payments
**Estimated Time:** 3-4 hours
**Risk Level:** 🟢 Low

### DO NOT START UNTIL

```
□ Phase 3 complete and verified
□ Invoice CRUD working
□ Create Invoice from Job working
□ Mark as Paid working
□ Job→Invoice link working
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Invoice data type | Database | ✅ MVP |
| Invoice page | Pages | ✅ MVP |
| Invoice workflows | Workflows | ✅ MVP |

### Modify: Option Sets (1)

| Option Set | Modification |
|------------|--------------|
| InvoiceStatus | Add: overdue |

### Modify: Data Types (1)

| Type | Modification |
|------|--------------|
| Invoice | Ensure fields exist: due_date, amount_paid, notes |

### Add: Workflows (3)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Record Partial Payment | Payment form submit | Invoice exists |
| Check Overdue Invoices | Scheduled (daily) | Invoices exist |
| Send Reminder | Button click | Overdue invoice |

### Record Partial Payment Workflow

```
Trigger: Submit payment form
Input: payment_amount

Step 1: Make changes to Invoice
  - amount_paid = Invoice's amount_paid + payment_amount

Step 2: Only when Invoice's amount_paid ≥ Invoice's total
  - Make changes to Invoice
  - status = paid
  - paid_date = Current date/time
```

### Check Overdue Workflow (Scheduled)

```
Trigger: Scheduled - Every day at 6:00 AM

Step 1: Search for Invoices
  - status = sent
  - due_date < Current date/time

Step 2: Make changes to list
  - status = overdue
```

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Invoices | Add due_date to form |
| Invoices | Add overdue filter option |
| Invoices | Add partial payment button/form |
| Invoices | Show balance due (total - amount_paid) |
| Invoices | Color-code overdue invoices |

### Modify: Dashboard (1)

| Page | Modification |
|------|--------------|
| Dashboard | Add overdue alert banner |
| Dashboard | Show overdue count and total |

### Verification Checklist

```
□ Can set due date on invoice
□ Invoice becomes overdue after due date (via scheduled workflow)
□ Can record partial payment
□ Balance due calculates correctly
□ Invoice auto-marked paid when fully paid
□ Overdue invoices highlighted
□ Dashboard shows overdue alert
□ Can filter invoices by overdue status
```

---

## PHASE 5: Expense Categories & Financial Reports

**Purpose:** Categorize expenses, add financial summaries
**Estimated Time:** 3-4 hours
**Risk Level:** 🟢 Low

### DO NOT START UNTIL

```
□ Phase 4 complete and verified
□ ExpenseEntry CRUD working
□ Financials page displaying expenses
□ Invoice paid tracking working
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| ExpenseEntry data type | Database | ✅ MVP |
| Invoice (for revenue) | Database | ✅ MVP |
| Financials page | Pages | ✅ MVP |

### Add: Option Sets (1)

| Option Set | Values | Notes |
|------------|--------|-------|
| ExpenseCategory | materials, labor, equipment, utilities, rent, other | Expense classification |

### Modify: Data Types (1)

| Type | Modification |
|------|--------------|
| ExpenseEntry | Add field: category (→ExpenseCategory) |

### Add: Data Types (1)

| Type | Fields | Depends On |
|------|--------|------------|
| SalesEntry | id, date, amount, tax_amount, description, created_at | None (independent) |

### Add: Workflows (3)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Create Sales Entry | Submit sales form | None |
| Calculate Financial Summary | Date range change | Entries exist |
| Generate Financial Report | Report button | Entries exist |

### Financial Summary Calculation

```
Inputs: start_date, end_date

Revenue (Option A - from Sales Entries):
  total_sales = Search SalesEntries (date in range):sum amount
  total_tax = Search SalesEntries (date in range):sum tax_amount

Revenue (Option B - from Paid Invoices):
  total_revenue = Search Invoices (status=paid, paid_date in range):sum total

Expenses:
  total_expenses = Search ExpenseEntries (date in range):sum amount
  expenses_by_category = Group by category, sum amount

Net Income:
  net = total_sales - total_expenses (or total_revenue - total_expenses)
```

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Financials | Add category dropdown to expense form |
| Financials | Add Sales tab with sales entry form |
| Financials | Add Summary tab with date range filter |
| Financials | Add expense breakdown by category chart |
| Financials | Add revenue vs expenses comparison |

### Verification Checklist

```
□ Can select category when adding expense
□ Can add sales entry
□ Summary calculates for date range
□ Expense breakdown by category correct
□ Revenue total matches expectations
□ Net income calculation correct
□ Chart displays properly
```

---

## PHASE 6: Payroll Advances & Reports

**Purpose:** Add advance type and period reports
**Estimated Time:** 2-3 hours
**Risk Level:** 🟢 Low

### DO NOT START UNTIL

```
□ Phase 5 complete and verified
□ Payroll transactions working
□ Employee balance calculating correctly
□ Break tracking working (Phase 2)
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| PayrollTransaction | Database | ✅ MVP |
| Employee | Database | ✅ MVP |
| Payroll page | Pages | ✅ MVP |
| TimeLog with breaks | Database | ✅ Phase 2 |

### Modify: Option Sets (1)

| Option Set | Modification |
|------------|--------------|
| PayrollTransactionType | Add: advance |

### Add: Workflows (2)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Generate Payroll Report | Date range submit | Transactions exist |
| Calculate Earnings from Hours | Button click | TimeLogs exist |

### Updated Balance Calculation

```
Previous (MVP):
  balance = earnings - payments

Updated (Phase 6):
  balance = earnings - advances - payments

Interpretation:
  Positive = employer owes employee
  Negative = employee has advance balance
```

### Calculate Earnings from Hours Workflow

```
Trigger: "Generate Earnings" button for employee + date

Step 1: Get shift summary (use Phase 2 calculation)
  - net_hours = work_hours - break_hours

Step 2: Calculate earnings
  - amount = net_hours × Employee's hourly_rate

Step 3: Create PayrollTransaction
  - employee = This Employee
  - type = earnings
  - amount = calculated amount
  - description = "Earnings for [date] ([hours] hrs)"
  - date = selected date
```

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Payroll | Add advance transaction type option |
| Payroll | Add period report section with date range |
| Payroll | Add "Generate Earnings from Hours" button |
| Payroll | Update balance display for advances |

### Verification Checklist

```
□ Can create advance transaction
□ Balance calculation includes advances
□ Period report shows correct totals
□ Can generate earnings from time logs
□ Earnings amount matches hours × rate
□ Report filters by date range correctly
```

---

## PHASE 7: Task Management

**Purpose:** Add task tracking with job linking
**Estimated Time:** 3-4 hours
**Risk Level:** 🟢 Low

### DO NOT START UNTIL

```
□ Phase 6 complete and verified
□ Job module fully working
□ Order Details page stable
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Job data type | Database | ✅ MVP |
| Job list page | Pages | ✅ MVP |

### Add: Data Types (1)

| Type | Fields | Depends On |
|------|--------|------------|
| Task | id, title, description, job (→Job, optional), due_date, is_complete, created_at | Job (optional) |

### Add: Workflows (4)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Create Task | Submit task form | None |
| Update Task | Submit edit form | Task exists |
| Toggle Task Complete | Checkbox click | Task exists |
| Delete Task | Delete button | Task exists |

### Add: Pages (1)

| Page | Components |
|------|------------|
| Productivity | Task list view (To Do / Completed columns) |
| | Create task popup |
| | Task card with checkbox, title, due date, job link |
| | Filter by job (optional) |

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Order Details | Add "Related Tasks" section (optional) |
| Dashboard | Add task count or overdue tasks (optional) |

### Verification Checklist

```
□ Can create task without job
□ Can create task linked to job
□ Can mark task complete
□ Can unmark task (toggle)
□ Can edit task
□ Can delete task
□ Tasks appear in correct column
□ Due date displays correctly
□ Job link works when set
```

---

## PHASE 8: Productivity Views (Calendar & Kanban)

**Purpose:** Add calendar and kanban visualizations
**Estimated Time:** 4-5 hours
**Risk Level:** 🟡 Medium (UI complexity)

### DO NOT START UNTIL

```
□ Phase 7 complete and verified
□ Task CRUD working
□ Job status changes working
□ Productivity page exists with task list
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Task data type | Database | ✅ Phase 7 |
| Job data type | Database | ✅ MVP |
| Productivity page | Pages | ✅ Phase 7 |

### Add: Data Types (0)

No new types

### Add: Workflows (2)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Move Job (Kanban) | Drag-drop or button | Job exists |
| Get Tasks for Date | Calendar date click | Tasks exist |

### Modify: Pages (1)

| Page | Modification |
|------|--------------|
| Productivity | Add tab navigation (List / Calendar / Kanban) |
| Productivity | Add Calendar view with task dots |
| Productivity | Add Kanban view with job cards by status |

### Calendar View Specification

```
Components:
- Calendar element (month view)
- Tasks shown as dots on dates with tasks
- Click date → show tasks for that date in side panel

Data:
- Tasks filtered by due_date matching selected date
- Group tasks by date for dot indicators
```

### Kanban View Specification

```
Columns (from OrderStatus):
- Quoted
- Approved
- In Production
- Installed
- Complete

Each column:
- Shows orders with that status
- Count and total value header
- Job cards with name, customer, due date

Interaction:
- Click job → navigate to Order Details
- (Future: drag-drop to change status)
```

### Verification Checklist

```
□ Tab navigation works
□ Calendar displays current month
□ Tasks with due dates show indicator
□ Click date shows tasks for that date
□ Kanban shows correct orders per column
□ Order counts match filters
□ Click job navigates to details
□ All three views work without errors
```

---

## PHASE 9: AI Tools Suite

**Purpose:** Add AI-powered design and business tools
**Estimated Time:** 6-8 hours
**Risk Level:** 🟡 Medium (API integration)

### DO NOT START UNTIL

```
□ Phase 8 complete and verified
□ API Connector plugin installed
□ OpenAI API key configured
□ Job and Customer modules stable
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Job data type | Database | ✅ MVP |
| Customer data type | Database | ✅ MVP |
| API Connector | Plugins | Required |
| OpenAI API Key | Settings | Required |

### Add: Data Types (1)

| Type | Fields | Depends On |
|------|--------|------------|
| AIResponse | id, tool, input_data (text/JSON), output (text), job (→Job, optional), customer (→Customer, optional), created_at | Job, Customer (optional) |

### Add: API Connector Calls (1)

```
API: OpenAI
Call: ChatCompletion
Method: POST
URL: https://api.openai.com/v1/chat/completions
Headers:
  Authorization: Bearer [key]
  Content-Type: application/json
Body: {
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": <system_message>},
    {"role": "user", "content": <user_message>}
  ]
}
```

### Add: Workflows (3)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Generate AI Response | Generate button | API configured |
| Save AI Response | After generation | AIResponse type |
| Load AI History | History button | AIResponse exists |

### AI Tools Configuration

| Tool ID | Name | System Prompt Summary |
|---------|------|----------------------|
| layout_generator | Layout Generator | Sign design layout expert |
| print_checklist | Print-Ready Checklist | Print production expert |
| brand_kit | Brand Kit Generator | Branding expert |
| document_creator | Document Creator | Business document specialist |
| overdue_assistant | Overdue Payment Assistant | Collections specialist |
| design_intake | Design Intake Chat | Design intake specialist |

### Add: Pages (1)

| Page | Components |
|------|------------|
| AI Tools | Tool selector sidebar (6 tools) |
| | Dynamic input form per tool |
| | Generate button |
| | Result display with copy |
| | History panel |

### Verification Checklist

```
□ API Connector configured correctly
□ Test API call works
□ Can select each tool
□ Input form shows correct fields per tool
□ Generate button triggers API call
□ Result displays correctly
□ Response saved to database
□ History shows past generations
□ Can link response to job/customer
□ Error handling for API failures
```

---

## PHASE 10: Webstores (Fundraiser & B2B)

**Purpose:** Add webstore functionality for fundraisers and B2B customers
**Estimated Time:** 8-10 hours
**Risk Level:** 🔴 High (complex auto-creation)

### DO NOT START UNTIL

```
□ Phase 9 complete and verified
□ All core modules stable
□ Customer creation working
□ Job creation working
□ No pending critical bugs
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Customer data type | Database | ✅ MVP |
| Job data type | Database | ✅ MVP |
| Invoice data type | Database | ✅ MVP |

### Add: Option Sets (3)

| Option Set | Values | Notes |
|------------|--------|-------|
| WebstoreType | fundraiser, b2b | Store classification |
| FundraiserStatus | active, paused, completed, cancelled | Campaign lifecycle |
| WebstoreOrderStatus | pending, processing, completed, cancelled | Order lifecycle |

### Add: Data Types (3)

| Type | Fields | Depends On |
|------|--------|------------|
| FundraiserCampaign | id, name, goal, start_date, end_date, organizer, payout_rules, total_raised, status, created_at | None |
| B2BStore | id, company_name, contact_email, login_password, discount_percent, is_active, created_at | None |
| WebstoreOrder | id, store_type, store_id, items (JSON), total, status, job (→Job), created_at | Order |

### Add: Workflows (6)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Create Fundraiser | Submit form | None |
| Create B2B Store | Submit form | None |
| Create Webstore Order | Order placed | Store exists |
| Auto-Create Customer | Part of order | Customer type |
| Auto-Create Order | Part of order | Job type |
| Update Fundraiser Total | After order | Campaign exists |

### Webstore Order Workflow (Complex)

```
Trigger: Order submitted (API or form)

Step 1: Find or Create Customer
  - Search Customers where company = "Webstore [TYPE] Customer"
  - If empty → Create Customer with default values

Step 2: Create Order
  - customer = Customer from Step 1
  - name = "Webstore Order #" + unique id
  - status = approved
  - description = Order details

Step 3: Create WebstoreOrder
  - store_type = input type
  - store_id = input store id
  - items = input items JSON
  - total = input total
  - status = pending
  - job = Job from Step 2

Step 4: (If fundraiser) Update Campaign
  - Make changes to FundraiserCampaign
  - total_raised = total_raised + order total
```

### Add: Pages (1)

| Page | Components |
|------|------------|
| Webstores | Tab navigation (Fundraisers / B2B / Orders) |
| | Fundraiser list and create form |
| | B2B store list and create form |
| | Orders list with status and linked job |

### Verification Checklist

```
□ Can create fundraiser campaign
□ Can create B2B store
□ Order creation triggers customer find/create
□ Order creation triggers order creation
□ Order linked to job correctly
□ Fundraiser total_raised updates
□ Orders list shows all orders
□ Can filter by store type
□ Job shows webstore origin
```

---

## PHASE 11: Customer Portal

**Purpose:** Add customer-facing portal for quotes, orders, invoices
**Estimated Time:** 10-12 hours
**Risk Level:** 🔴 High (authentication, privacy rules)

### DO NOT START UNTIL

```
□ Phase 10 complete and verified
□ All data modules stable
□ Quote module working (Phase 3)
□ Invoice module working (Phase 4)
□ Privacy rules designed
```

### Prerequisites (Must Exist)

| Requirement | Location | Status |
|-------------|----------|--------|
| Customer data type | Database | ✅ MVP |
| Quote data type | Database | ✅ Phase 3 |
| Job data type | Database | ✅ MVP |
| Invoice data type | Database | ✅ MVP |
| User authentication | Built-in | Required |

### Modify: User Type

| Field | Type | Notes |
|-------|------|-------|
| role | text | Add "customer" option |
| linked_customer | Customer | Link portal user to customer |

### Add: Privacy Rules (All Types)

See `/app/BUBBLE_PRIVACY_RULES.md` for complete specifications.

Key rules:
- Customer users see only their own data
- Customer users cannot modify most fields
- Customer users can approve/decline quotes

### Add: Workflows (4)

| Workflow | Trigger | Depends On |
|----------|---------|------------|
| Customer Login | Login form | User exists |
| Approve Quote | Approve button | Quote status = sent |
| Decline Quote | Decline button | Quote status = sent |
| View Invoice | Page load | Invoice exists |

### Add: Pages (5)

| Page | Components | Access |
|------|------------|--------|
| /portal | Customer dashboard | Customer only |
| /portal/profile | Edit profile | Customer only |
| /portal/quotes | Quote list, approve/decline | Customer only |
| /portal/orders | Job list (read-only status) | Customer only |
| /portal/invoices | Invoice list, payment (future) | Customer only |

### Add: Signup/Login Flow

```
Customer Portal Access:
1. Admin creates Customer record
2. Admin creates User with role="customer"
3. Admin links User.linked_customer = Customer
4. Customer receives login credentials
5. Customer logs in → redirected to /portal
```

### Verification Checklist

```
□ Customer can log in
□ Customer redirected to portal
□ Customer sees only their quotes
□ Customer can approve sent quote
□ Customer can decline sent quote
□ Customer sees only their orders
□ Customer cannot edit orders
□ Customer sees only their invoices
□ Staff/Owner cannot access /portal pages
□ Customer cannot access admin pages
□ Privacy rules enforced in searches
```

---

## PHASE SUMMARY

| Phase | Name | Data Types | Workflows | Hours | Risk |
|-------|------|------------|-----------|-------|------|
| MVP | Baseline | 8 | 22 | 15-20 | - |
| 1 | Notes & Activity | +2 | +6 | 3-4 | 🟢 |
| 2 | Break Tracking | 0 | +3 | 2-3 | 🟢 |
| 3 | Quotes | +2 | +8 | 5-6 | 🟡 |
| 4 | Invoice Enhance | 0 | +3 | 3-4 | 🟢 |
| 5 | Financial Reports | +1 | +3 | 3-4 | 🟢 |
| 6 | Payroll Advances | 0 | +2 | 2-3 | 🟢 |
| 7 | Tasks | +1 | +4 | 3-4 | 🟢 |
| 8 | Calendar/Kanban | 0 | +2 | 4-5 | 🟡 |
| 9 | AI Tools | +1 | +3 | 6-8 | 🟡 |
| 10 | Webstores | +3 | +6 | 8-10 | 🔴 |
| 11 | Customer Portal | 0 | +4 | 10-12 | 🔴 |
| **TOTAL** | | **17** | **66** | **60-83** | |

---

## ROLLBACK PROCEDURES

### If Phase Fails

```
Phase 1-2: 
  - Low risk, isolated features
  - Can disable without affecting MVP

Phase 3 (Quotes):
  - If conversion breaks: revert Job.quote field
  - Orders can still be created directly

Phase 4-6:
  - Additive features
  - Can revert option set additions
  - Core workflows unaffected

Phase 7-8:
  - New page, can be hidden
  - No impact on core modules

Phase 9 (AI):
  - Disable page, remove API calls
  - No data dependencies

Phase 10 (Webstores):
  - Complex, has job auto-creation
  - Disable order intake
  - Manual cleanup of test orders

Phase 11 (Portal):
  - Disable login for customer role
  - Revert privacy rules to staff-only
  - Remove portal pages
```

---

## FINAL CHECKLIST BEFORE EACH PHASE

```
□ Previous phase verified and stable
□ All "DO NOT START UNTIL" items checked
□ Backup/snapshot taken
□ Test users ready for new role (if applicable)
□ Rollback procedure understood
□ Time allocated for testing
□ Stakeholder notified of changes
```
