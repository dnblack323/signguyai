# Sign Guy AI - Strict MVP Cut Line

## DECISION FRAMEWORK

**MVP Question:** Can the shop operate tomorrow without this feature?
- YES = Postpone
- NO = Include

**Business Reality:** A sign shop needs to:
1. Know who their customers are
2. Track what work needs to be done
3. Get paid for that work
4. Pay their employees

Everything else is optimization.

---

## MVP: INCLUDE (Must Have)

### Data Types (8 of 17)

| Type | Reason |
|------|--------|
| ✅ Customer | Can't do business without customers |
| ✅ Job | Core work tracking unit |
| ✅ JobItem | What's being produced |
| ✅ Invoice | Getting paid |
| ✅ Employee | Who works here |
| ✅ TimeLog | Clock in/out for payroll |
| ✅ PayrollTransaction | Pay employees |
| ✅ ExpenseEntry | Track costs (basic) |

### Option Sets (7 of 13)

| Option Set | Reason |
|------------|--------|
| ✅ CustomerStatus | lead, active, inactive |
| ✅ JobStatus | quoted, approved, in_production, complete |
| ✅ JobItemStatus | pending, in_production, done |
| ✅ JobItemType | Core product types only |
| ✅ InvoiceStatus | draft, sent, paid |
| ✅ PayrollTransactionType | earnings, payment |
| ✅ TimeLogAction | start_work, end_work |

### Pages (8 of 12)

| Page | Reason |
|------|--------|
| ✅ Dashboard | Daily overview |
| ✅ Customers | Customer list and details |
| ✅ Jobs | Job list with status |
| ✅ Job Details | Manage single job + items |
| ✅ Invoices | Create and track invoices |
| ✅ Time Clock | Employees clock in/out |
| ✅ Payroll | Pay employees |
| ✅ Financials | Basic expense tracking only |

### Workflows (22 of 34)

**Customer:**
- ✅ Create Customer
- ✅ Update Customer
- ✅ Delete Customer

**Job:**
- ✅ Create Job
- ✅ Update Job
- ✅ Change Job Status
- ✅ Mark Job Complete

**JobItem:**
- ✅ Add Job Item
- ✅ Update Job Item
- ✅ Delete Job Item
- ✅ Recalculate Job Subtotal

**Invoice:**
- ✅ Create Invoice
- ✅ Create Invoice from Job
- ✅ Update Invoice
- ✅ Mark Invoice Paid
- ✅ Recalculate Invoice Total

**Time Clock:**
- ✅ Clock In (start_work)
- ✅ Clock Out (end_work)
- ✅ Calculate Daily Hours

**Payroll:**
- ✅ Create Payroll Transaction
- ✅ Calculate Employee Balance
- ✅ View Payroll Summary

### Features

| Feature | Scope |
|---------|-------|
| ✅ Customer CRUD | Name, company, phone, email, status |
| ✅ Job Management | Create, status changes, complete |
| ✅ Job Items | Add items with qty, price, total |
| ✅ Job Subtotal | Auto-calculated from items |
| ✅ Basic Invoice | Create from job, mark paid |
| ✅ Simple Time Clock | Start work, end work only |
| ✅ Basic Payroll | Earnings and payments |
| ✅ Expense Tracking | Date, amount, description |

---

## MVP: EXCLUDE (Postpone)

### Data Types (9 of 17) - DEFER

| Type | Reason to Defer |
|------|-----------------|
| ❌ Quote | Can create Jobs directly |
| ❌ QuoteLineItem | No quotes = no line items |
| ❌ JobNote | Can use Job description field |
| ❌ JobActivity | Nice audit trail, not essential |
| ❌ SalesEntry | Use Invoice.paid for revenue |
| ❌ Task | Use paper/whiteboard for now |
| ❌ AIResponse | AI is enhancement, not core |
| ❌ FundraiserCampaign | Webstores are Phase 2 |
| ❌ B2BStore | Webstores are Phase 2 |
| ❌ WebstoreOrder | Webstores are Phase 2 |

### Option Sets (6 of 13) - DEFER

| Option Set | Reason to Defer |
|------------|-----------------|
| ❌ QuoteStatus | No quotes in MVP |
| ❌ JobActivityType | No activity logging |
| ❌ ExpenseCategory | Simple expenses, no categories |
| ❌ WebstoreType | No webstores |
| ❌ FundraiserStatus | No webstores |
| ❌ WebstoreOrderStatus | No webstores |

### Pages (4 of 12) - DEFER

| Page | Reason to Defer |
|------|-----------------|
| ❌ Quotes | Create Jobs directly |
| ❌ Productivity | Use physical Kanban board |
| ❌ AI Tools | Enhancement, not essential |
| ❌ Webstores | Separate product, Phase 2 |

### Workflows (12 of 34) - DEFER

| Workflow | Reason to Defer |
|----------|-----------------|
| ❌ All Quote workflows | No quotes |
| ❌ Quote → Job conversion | No quotes |
| ❌ Job Archive/Unarchive | Just mark complete |
| ❌ JobNote CRUD | Use description |
| ❌ JobActivity logging | Not essential |
| ❌ Break tracking | Start/end only for MVP |
| ❌ Shift summary calc | Simple hours only |
| ❌ Payroll report | Basic balance only |
| ❌ Sales entry | Use paid invoices |
| ❌ Financial summary | Basic expense list |
| ❌ AI generation | Phase 2 |
| ❌ Webstore order | Phase 2 |

### Features - DEFER

| Feature | Why Defer |
|---------|-----------|
| ❌ Quotes/Estimates | Jobs can start without formal quote |
| ❌ Quote → Job conversion | No quotes |
| ❌ Job Notes | Use description or paper |
| ❌ Activity Logging | Nice to have, not essential |
| ❌ Break Tracking | Calculate breaks manually |
| ❌ Overtime Calculation | Handle in spreadsheet initially |
| ❌ Advances | Simple earnings/payments only |
| ❌ Sales Entry | Paid invoices = revenue |
| ❌ Expense Categories | All expenses equal for now |
| ❌ Financial Reports | Export to spreadsheet |
| ❌ Task Management | Physical board or paper |
| ❌ Calendar View | Use Google Calendar |
| ❌ Kanban Board | Physical board |
| ❌ AI Tools | Manual processes work |
| ❌ Webstores | Separate business line |
| ❌ Customer Portal | Email/phone communication |
| ❌ Proof Approval | Email attachments |
| ❌ File Attachments | Local file storage |
| ❌ Stripe Integration | Cash/check/manual card |

---

## MVP SCOPE SUMMARY

### What MVP Delivers

```
CUSTOMER → JOB → INVOICE → PAID
     ↓
  JOB ITEMS (with pricing)
     ↓
  SUBTOTAL (calculated)

EMPLOYEE → CLOCK IN → CLOCK OUT
     ↓
  HOURS WORKED
     ↓
  PAYROLL (earnings + payments)

EXPENSES → SIMPLE LIST
```

### Numbers

| Category | MVP | Total | Cut |
|----------|-----|-------|-----|
| Data Types | 8 | 17 | 53% |
| Option Sets | 7 | 13 | 46% |
| Pages | 8 | 12 | 33% |
| Workflows | 22 | 34 | 35% |

### Build Time Estimate

| Phase | Hours |
|-------|-------|
| MVP | 15-20 hours |
| Full App | 40-60 hours |
| **Savings** | **50-65%** |

---

## MVP PAGE SPECIFICATIONS

### Dashboard (Simplified)

**Show only:**
- Total Customers (count)
- Active Jobs (count)
- Unpaid Invoices (count + total)
- Quick actions: New Customer, New Job

**Remove:**
- Revenue metrics
- Recent activity
- Overdue alerts

### Customers (Keep as-is)

Full CRUD, no changes needed.

### Jobs (Simplified)

**Keep:**
- Job list with status filter
- Create job form
- Status change dropdown

**Remove:**
- Archive/unarchive
- Filter tabs (just one list)

### Job Details (Simplified)

**Keep:**
- Job header with status
- Job items table
- Subtotal display
- Create Invoice button

**Remove:**
- Financial snapshot (just show subtotal)
- Notes tab
- Activity tab
- Quick actions (archive, etc.)

### Invoices (Simplified)

**Keep:**
- Invoice list
- Create invoice (manual)
- Create from job
- Mark as paid

**Remove:**
- Summary cards
- Partial payments
- Overdue tracking

### Time Clock (Simplified)

**Keep:**
- Employee selector
- Clock In button
- Clock Out button
- Today's hours display

**Remove:**
- Break tracking
- Detailed activity log
- Shift summary calculations

### Payroll (Simplified)

**Keep:**
- Employee list with balances
- Add earnings transaction
- Add payment transaction
- Current balance display

**Remove:**
- Advances
- Date range reports
- Detailed ledger view

### Financials (Simplified)

**Keep:**
- Add expense form
- Expense list (date, amount, description)

**Remove:**
- Sales entries (use invoices)
- Categories
- Summary cards
- Date range filtering
- Charts

---

## MVP DATA MODELS

### Customer (No changes)
```
- id
- name
- company
- phone
- email
- status (lead, active, inactive)
- created_at
```

### Job (Simplified)
```
- id
- customer (reference)
- name
- description
- status (quoted, approved, in_production, complete)
- due_date
- subtotal (calculated)
- created_at

REMOVED:
- quote (reference) → no quotes
- invoice (reference) → query instead
- is_archived → just use status
```

### JobItem (Simplified)
```
- id
- job (reference)
- item_type
- description
- quantity
- unit_price
- line_total (calculated)
- status (pending, in_production, done)
- created_at

REMOVED:
- notes → use description
```

### Invoice (Simplified)
```
- id
- customer (reference)
- job (reference, optional)
- line_items (embedded)
- total (calculated)
- status (draft, sent, paid)
- created_at
- paid_date

REMOVED:
- due_date → not tracking overdue
- notes → not needed
- amount_paid → full payment only
```

### Employee (No changes)
```
- id
- name
- hourly_rate
- is_active
- created_at
```

### TimeLog (Simplified)
```
- id
- employee (reference)
- action (start_work, end_work)
- timestamp

REMOVED:
- break_start, break_end actions
```

### PayrollTransaction (Simplified)
```
- id
- employee (reference)
- type (earnings, payment)
- amount
- date
- created_at

REMOVED:
- advance type
- description
```

### ExpenseEntry (Simplified)
```
- id
- date
- amount
- description
- created_at

REMOVED:
- category
```

---

## MVP WORKFLOWS (Detailed)

### Customer Workflows (3)
```
1. Create Customer
   Trigger: Submit form
   Action: Create Customer with form data

2. Update Customer
   Trigger: Submit edit form
   Action: Make changes to Customer

3. Delete Customer
   Trigger: Confirm delete
   Condition: No Jobs reference this Customer
   Action: Delete Customer
```

### Job Workflows (4)
```
1. Create Job
   Trigger: Submit form
   Action: Create Job with customer, name, status=quoted

2. Update Job
   Trigger: Submit edit form
   Action: Make changes to Job

3. Change Job Status
   Trigger: Status dropdown change
   Action: Make changes to Job (status)

4. Mark Job Complete
   Trigger: Complete button
   Action: Make changes to Job (status=complete)
```

### JobItem Workflows (4)
```
1. Add Job Item
   Trigger: Submit item form
   Actions:
   - Create JobItem
   - Calculate line_total = qty × price
   - Recalculate parent Job subtotal

2. Update Job Item
   Trigger: Submit item edit
   Actions:
   - Make changes to JobItem
   - Recalculate line_total
   - Recalculate parent Job subtotal

3. Delete Job Item
   Trigger: Confirm delete
   Actions:
   - Delete JobItem
   - Recalculate parent Job subtotal

4. Recalculate Job Subtotal
   (Called by above workflows)
   Action: Make changes to Job
   - subtotal = Search JobItems (job=This):sum line_total
```

### Invoice Workflows (4)
```
1. Create Invoice
   Trigger: Submit form
   Action: Create Invoice with line items, calculate total

2. Create Invoice from Job
   Trigger: Button on Job Details
   Actions:
   - Create Invoice (customer=Job's customer, job=This Job)
   - Copy JobItems to InvoiceLineItems
   - Calculate total

3. Update Invoice
   Trigger: Submit edit form
   Condition: Status = draft
   Action: Make changes to Invoice

4. Mark Invoice Paid
   Trigger: Mark Paid button
   Action: Make changes to Invoice
   - status = paid
   - paid_date = Current date/time
```

### Time Clock Workflows (3)
```
1. Clock In
   Trigger: Clock In button
   Condition: No start_work today without end_work
   Action: Create TimeLog (action=start_work)

2. Clock Out
   Trigger: Clock Out button
   Condition: Has start_work today without end_work
   Action: Create TimeLog (action=end_work)

3. Calculate Today's Hours
   (Display only, not stored)
   Expression: 
   - Find today's start_work timestamp
   - Find today's end_work timestamp (or now)
   - Calculate difference in hours
```

### Payroll Workflows (3)
```
1. Add Earnings
   Trigger: Submit earnings form
   Action: Create PayrollTransaction (type=earnings)

2. Add Payment
   Trigger: Submit payment form
   Action: Create PayrollTransaction (type=payment)

3. Calculate Balance
   (Display only)
   Expression:
   - SUM(amount where type=earnings) - SUM(amount where type=payment)
```

### Expense Workflow (1)
```
1. Add Expense
   Trigger: Submit expense form
   Action: Create ExpenseEntry
```

**Total MVP Workflows: 22**

---

## POST-MVP PHASES

### Phase 2: Quotes & Polish (Week 2-3)
- Quote data type and workflows
- Quote → Job conversion
- Job notes
- Activity logging
- Break tracking in time clock
- Expense categories
- Invoice due dates and overdue status

### Phase 3: Productivity (Week 4)
- Task management
- Kanban board view
- Calendar view
- Advances in payroll
- Financial reports

### Phase 4: AI & Automation (Week 5-6)
- AI Tools suite
- Document generation
- Smart suggestions

### Phase 5: Customer Portal (Week 7-8)
- Customer login
- Quote approval
- Job status viewing
- Invoice viewing/payment

### Phase 6: Webstores (Week 9-10)
- Fundraiser campaigns
- B2B stores
- Order → Job automation

### Phase 7: Integrations (Week 11-12)
- Stripe payments
- File attachments
- Proof approval system

---

## MVP LAUNCH CHECKLIST

### Must Work Before Launch

```
□ Can create a customer
□ Can create a job for that customer
□ Can add items to the job
□ Job subtotal calculates correctly
□ Can create invoice from job
□ Can mark invoice as paid
□ Can add an employee
□ Employee can clock in
□ Employee can clock out
□ Hours display correctly
□ Can add earnings for employee
□ Can add payment for employee
□ Balance calculates correctly
□ Can add an expense
```

### Can Ship Without

```
□ Quotes
□ Job notes
□ Activity log
□ Break tracking
□ Overtime
□ Advances
□ Expense categories
□ Financial reports
□ Tasks
□ Calendar
□ Kanban
□ AI tools
□ Webstores
□ Customer portal
□ Stripe
```

---

## COMMUNICATION TEMPLATE

### For Stakeholders

> **MVP Scope:**
> 
> The MVP includes everything needed to run daily operations:
> - Customer management
> - Job tracking with line items
> - Basic invoicing
> - Time clock (in/out)
> - Payroll (earnings/payments)
> - Expense tracking
> 
> **Not in MVP (coming in future updates):**
> - Formal quotes/estimates
> - AI-powered tools
> - Customer portal
> - Online payments
> - Webstores
> 
> **Timeline:** MVP in ~20 hours, full feature set in ~60 hours

### For Users

> **What you can do now:**
> - Add customers and track their info
> - Create jobs and add what you're making
> - See job totals automatically calculated
> - Create invoices and mark them paid
> - Clock employees in and out
> - Track what you owe employees
> - Log expenses
> 
> **Coming soon:**
> - Quotes that convert to jobs
> - Break tracking
> - AI design helpers
> - Customer login portal
> - Online payments
