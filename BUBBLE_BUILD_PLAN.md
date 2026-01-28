# Sign Guy AI - Bubble Build Plan

## OVERVIEW

This document provides a step-by-step build plan for recreating Sign Guy AI in Bubble.io. Follow phases in order - each phase depends on the previous.

**Estimated Build Time:** 40-60 hours (experienced Bubble developer)

**Reference Documents:**
- `/app/BUBBLE_DATABASE_SCHEMA.md` - Data types and option sets
- `/app/BUBBLE_WORKFLOWS.md` - All workflow logic
- `/app/BUBBLE_PAGE_MAP.md` - Page structure and components
- `/app/BUBBLE_AI_TOOLS_CONFIG.md` - AI integration details
- `/app/BUBBLE_ROLES_PERMISSIONS.md` - Future permissions structure

---

## PHASE 0: Option Sets & Settings

**Duration:** 1-2 hours
**Dependencies:** None

### 0.1 Create Option Sets

Create in this order (no dependencies between them):

| Option Set | Values (in order) |
|------------|-------------------|
| CustomerStatus | lead, active, inactive |
| QuoteStatus | draft, sent, approved, declined |
| JobStatus | quoted, approved, in_production, installed, complete, archived |
| JobActivityType | created, status_changed, quote_converted, invoice_created, item_added, item_updated, item_deleted, note_added, completed, archived, unarchived |
| JobItemStatus | pending, in_production, done |
| JobItemType | banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other |
| InvoiceStatus | draft, sent, paid, overdue |
| PayrollTransactionType | earnings, advance, payment |
| ExpenseCategory | materials, labor, equipment, utilities, rent, other |
| TimeLogAction | start_work, break_start, break_end, end_work |
| WebstoreType | fundraiser, b2b |
| FundraiserStatus | active, paused, completed, cancelled |
| WebstoreOrderStatus | pending, processing, completed, cancelled |

**For each option set:**
1. Settings → Option sets → New option set
2. Add display value (capitalized, spaces)
3. Set attribute for stored value (lowercase, underscores)

### 0.2 App Settings

1. **General Settings**
   - App name: Sign Guy AI
   - Default page: index (Dashboard)

2. **API Settings**
   - Enable Data API (for future integrations)
   - Enable Workflow API

3. **Plugins to Install**
   - API Connector (for OpenAI)
   - Toolbox (for JavaScript expressions)
   - Calendar / Date picker (optional enhancement)

### 0.3 API Connector Setup (OpenAI)

1. Add API Connector plugin
2. Create new API: "OpenAI"
3. Authentication: Bearer Token (use environment variable)
4. Create call "ChatCompletion":
   ```
   POST https://api.openai.com/v1/chat/completions
   Headers:
     Authorization: Bearer [api_key]
     Content-Type: application/json
   Body (JSON):
     {
       "model": "gpt-4",
       "messages": [
         {"role": "system", "content": "<system_message>"},
         {"role": "user", "content": "<user_message>"}
       ],
       "temperature": 0.7
     }
   ```

---

## PHASE 1: Core Data Types

**Duration:** 3-4 hours
**Dependencies:** Phase 0 complete

### Build Order (Critical - Follow Exactly)

Data types must be created in dependency order. Types that reference other types must be created after their dependencies.

```
LAYER 1 (No dependencies):
├── Customer
├── Employee

LAYER 2 (Depends on Layer 1):
├── Quote (→ Customer)
├── Job (→ Customer)
├── TimeLog (→ Employee)
├── PayrollTransaction (→ Employee)
├── SalesEntry
├── ExpenseEntry
├── Task (→ Job, optional)
├── FundraiserCampaign
├── B2BStore

LAYER 3 (Depends on Layer 2):
├── QuoteLineItem (embedded in Quote)
├── JobItem (→ Job)
├── JobNote (→ Job)
├── JobActivity (→ Job)
├── Invoice (→ Customer, → Job)
├── WebstoreOrder (→ Job)
├── AIResponse (→ Job, → Customer)

LAYER 4 (Depends on Layer 3):
├── InvoiceLineItem (embedded in Invoice, → JobItem)
```

### 1.1 Layer 1: Independent Types

#### Customer
| Field | Type | Default |
|-------|------|---------|
| name | text | - |
| company | text | - |
| phone | text | - |
| email | text | - |
| status | CustomerStatus | lead |
| notes | text | - |

#### Employee
| Field | Type | Default |
|-------|------|---------|
| name | text | - |
| hourly_rate | number | 0 |
| is_active | yes/no | yes |

### 1.2 Layer 2: Single Dependencies

#### Quote
| Field | Type | Default |
|-------|------|---------|
| customer | Customer | - |
| line_items | list of QuoteLineItems | - |
| notes | text | - |
| status | QuoteStatus | draft |
| total | number | 0 |
| job | Job | - |

#### Job
| Field | Type | Default |
|-------|------|---------|
| customer | Customer | - |
| name | text | - |
| description | text | - |
| status | JobStatus | quoted |
| due_date | date | - |
| quote | Quote | - |
| invoice | Invoice | - |
| subtotal | number | 0 |
| is_archived | yes/no | no |

#### TimeLog
| Field | Type | Default |
|-------|------|---------|
| employee | Employee | - |
| action | TimeLogAction | - |
| timestamp | date | Current date/time |

#### PayrollTransaction
| Field | Type | Default |
|-------|------|---------|
| employee | Employee | - |
| type | PayrollTransactionType | - |
| amount | number | - |
| description | text | - |
| date | date | Current date/time |

#### SalesEntry
| Field | Type | Default |
|-------|------|---------|
| date | date | - |
| amount | number | - |
| tax_amount | number | 0 |
| description | text | - |

#### ExpenseEntry
| Field | Type | Default |
|-------|------|---------|
| date | date | - |
| amount | number | - |
| category | ExpenseCategory | other |
| description | text | - |

#### Task
| Field | Type | Default |
|-------|------|---------|
| title | text | - |
| description | text | - |
| job | Job | - |
| due_date | date | - |
| is_complete | yes/no | no |

#### FundraiserCampaign
| Field | Type | Default |
|-------|------|---------|
| name | text | - |
| goal | number | 0 |
| start_date | date | - |
| end_date | date | - |
| organizer | text | - |
| payout_rules | text | - |
| total_raised | number | 0 |
| status | FundraiserStatus | active |

#### B2BStore
| Field | Type | Default |
|-------|------|---------|
| company_name | text | - |
| contact_email | text | - |
| login_password | text | - |
| discount_percent | number | 0 |
| is_active | yes/no | yes |

### 1.3 Layer 3: Multiple Dependencies

#### JobItem
| Field | Type | Default |
|-------|------|---------|
| job | Job | - |
| item_type | JobItemType | other |
| description | text | - |
| quantity | number | 1 |
| unit_price | number | 0 |
| line_total | number | 0 |
| status | JobItemStatus | pending |
| notes | text | - |

#### JobNote
| Field | Type | Default |
|-------|------|---------|
| job | Job | - |
| content | text | - |
| author | text | - |

#### JobActivity
| Field | Type | Default |
|-------|------|---------|
| job | Job | - |
| activity_type | JobActivityType | - |
| description | text | - |
| old_value | text | - |
| new_value | text | - |

#### Invoice
| Field | Type | Default |
|-------|------|---------|
| customer | Customer | - |
| job | Job | - |
| line_items | list of InvoiceLineItems | - |
| total | number | 0 |
| status | InvoiceStatus | draft |
| due_date | date | - |
| notes | text | - |
| amount_paid | number | 0 |
| paid_date | date | - |

#### WebstoreOrder
| Field | Type | Default |
|-------|------|---------|
| store_type | WebstoreType | - |
| store_id | text | - |
| items | text (JSON) | - |
| total | number | 0 |
| status | WebstoreOrderStatus | pending |
| job | Job | - |

#### AIResponse
| Field | Type | Default |
|-------|------|---------|
| tool | text | - |
| input_data | text (JSON) | - |
| output | text | - |
| job | Job | - |
| customer | Customer | - |

### 1.4 Embedded Types (Sub-types)

Create these as separate types but they'll be used as lists within parent types:

#### QuoteLineItem
| Field | Type | Default |
|-------|------|---------|
| description | text | - |
| quantity | number | 1 |
| unit_price | number | 0 |
| total | number | 0 |

#### InvoiceLineItem
| Field | Type | Default |
|-------|------|---------|
| description | text | - |
| quantity | number | 1 |
| unit_price | number | 0 |
| total | number | 0 |
| job_item | JobItem | - |

### 1.5 Update Cross-References

After all types created, go back and add:

1. **Quote** → Add field `job` (type: Job)
2. **Job** → Add field `quote` (type: Quote)
3. **Job** → Add field `invoice` (type: Invoice)

### 1.6 Privacy Rules

Set up basic privacy rules (expand in Phase 5):

For each data type:
1. Data → Privacy → [Type]
2. Default: "Everyone can view, create, modify, delete"
3. Note: Lock down in Phase 5 for Customer Portal

---

## PHASE 2: Core Pages

**Duration:** 12-16 hours
**Dependencies:** Phase 1 complete

### Build Order

Pages should be built in order of dependency and complexity:

```
FOUNDATION:
├── index (Dashboard) - establish layout pattern
├── Reusable: Header
├── Reusable: Sidebar

CRUD PAGES (simpler):
├── customers
├── employees (for time clock)

COMPLEX PAGES (build on patterns):
├── quotes
├── jobs (list)
├── job-details (separate page)
├── invoices

OPERATIONAL PAGES:
├── timeclock
├── payroll
├── productivity
├── financials

ADVANCED PAGES:
├── ai-tools
├── webstores
```

### 2.1 Reusable Elements

Create these first - used on all pages:

#### Reusable: Sidebar
- Width: 240px (collapsible to 60px)
- Contains:
  - Logo (top)
  - Navigation groups
  - Active state highlighting
- Links to all main pages

#### Reusable: Header
- Contains:
  - Page title (dynamic)
  - Action buttons slot
  - User menu (future)

#### Reusable: Status Badge
- Input: status text, color
- Displays styled badge
- Use for all status indicators

#### Reusable: Currency Display
- Input: number
- Output: formatted as $X,XXX.XX

#### Reusable: Data Table
- Consider building a flexible table component
- Or use Bubble's native repeating group

### 2.2 Dashboard (index)

**Layout:**
- Sidebar (left)
- Main content area
  - Stats row (4 cards)
  - Two-column layout below

**Elements:**
1. Stat Card: Total Customers
   - Data: `Search for Customers:count`
2. Stat Card: Active Jobs
   - Data: `Search for Jobs where status is not complete:count`
3. Stat Card: Pending Invoices
   - Data: `Search for Invoices where status = sent or overdue:count`
4. Stat Card: Today's Revenue
   - Data: `Search for SalesEntries where date = Current date:each item's amount:sum`
5. Overdue Alert (conditional)
   - Visible when: `Search for Invoices where status = overdue:count > 0`
6. Recent Activity list
7. Quick Action buttons

### 2.3 Customers Page

**Layout:**
- Header with "Add Customer" button
- Search input
- Status filter dropdown
- Repeating group table

**Popup: Customer Form**
- Fields: name, company, email, phone, status, notes
- Save workflow creates/updates Customer

**Workflows:**
- Button "Add Customer" → Show popup
- Row click → Show popup with data
- Delete icon → Delete Customer

### 2.4 Quotes Page

**Layout:**
- Header with "New Quote" button
- Status filter
- Repeating group table

**Popup: Quote Form**
- Customer dropdown
- Line items editor (repeating group)
- Add/remove line item buttons
- Total calculation (live)
- Notes textarea
- Status dropdown

**Workflows:**
- Create Quote with line items
- Update Quote
- Convert to Job button
- Delete Quote

**Key Logic:**
- Line item total = quantity × unit_price
- Quote total = sum of line item totals
- Convert creates Job + JobItems from line items

### 2.5 Jobs Page (List)

**Layout:**
- Header with "New Job" button
- Filter tabs: Active, Completed, Archived
- Repeating group list (card style)

**Each Job Row Shows:**
- Name (link to details)
- Status badge (clickable dropdown)
- Customer name
- Due date
- Subtotal
- Actions menu

**Workflows:**
- Create Job
- Quick status change
- Navigate to job details

### 2.6 Job Details Page

**This is the most complex page - build carefully**

**URL Parameter:** job_id

**Layout:**
- Back button
- Header card (job info, status, actions)
- Financial snapshot (5 stat cards)
- Tabs: Line Items, Notes, Activity

**Header Card Contains:**
- Job name
- Status dropdown (editable)
- Customer link
- Due date
- Edit button
- Quick actions: Create Invoice, Mark Complete, Archive

**Financial Snapshot:**
- Quote Total: `This Job's quote's total`
- Job Subtotal: `This Job's subtotal`
- Invoiced: `This Job's invoice's total`
- Paid: `This Job's invoice's amount_paid`
- Balance: `Invoiced - Paid`

**Tab: Line Items**
- Add Item button
- Table of JobItems
- Inline status dropdown
- Edit/Delete actions
- Subtotal row

**Tab: Notes**
- Add note input + button
- List of JobNotes
- Delete option

**Tab: Activity**
- List of JobActivities
- Icon per type
- Timestamp

**Workflows:**
- Update job (many triggers)
- Add/edit/delete job item
- Recalculate subtotal on item change
- Add/delete note
- Log activity on changes
- Create invoice from job

### 2.7 Invoices Page

**Layout:**
- Header with "New Invoice" button
- Summary cards (Total, Paid, Pending, Overdue)
- Status filter
- Repeating group table

**Popup: Invoice Form**
- Customer dropdown
- Job dropdown (filtered by customer)
- Line items editor
- Total, status, due date, notes

**Workflows:**
- Create Invoice
- Update Invoice
- Mark as Paid (set amount_paid = total, paid_date = now)

### 2.8 Time Clock Page

**Layout:**
- Header with "Add Employee" button
- Employee selector dropdown
- Status badge
- Clock action buttons (4)
- Today's summary card
- Today's activity list

**Button State Logic:**
```
Start Work: enabled when last_action is null OR end_work
Break Start: enabled when last_action is start_work OR break_end
Break End: enabled when last_action is break_start
End Work: enabled when last_action is start_work OR break_end
```

**Workflows:**
- Add Employee
- Clock Action (create TimeLog)
- Calculate summary on employee change

### 2.9 Payroll Page

**Layout:**
- Header with "Add Transaction" button
- Employee ledger card
  - Employee selector
  - Balance summary (4 stats)
  - Transaction table
- Balance explanation card
- Payroll report card
  - Date range inputs
  - Employee summary table

**Workflows:**
- Add Transaction
- Calculate balance per employee
- Generate report for date range

### 2.10 Productivity Page

**Layout:**
- Header with "New Task" button
- View tabs: Tasks, Calendar, Kanban

**Tab: Tasks**
- Two columns: To Do, Completed
- Checkbox to toggle
- Delete option

**Tab: Calendar**
- Calendar element
- Selected date's tasks

**Tab: Kanban**
- 5 columns by JobStatus
- Jobs displayed as cards
- (Future: drag-and-drop)

### 2.11 Financials Page

**Layout:**
- Header with Add Sale / Add Expense buttons
- Date range filter
- Summary cards (4)
- Tabs: Overview, Sales, Expenses

**Tab: Overview**
- Expense breakdown by category
- Recent activity

**Tab: Sales**
- Table of SalesEntries

**Tab: Expenses**
- Table of ExpenseEntries

### 2.12 AI Tools Page

**Layout:**
- Tool selector sidebar
- Tool interface area
  - Tool header
  - Dynamic input form
  - Generate button
  - Result display
  - History panel

**Key Challenge:** Dynamic form based on selected tool

**Approach:**
- Create 6 groups (one per tool), show/hide based on selection
- Or use custom states to build form dynamically

### 2.13 Webstores Page

**Layout:**
- Tabs: Fundraisers, B2B Stores, Orders

**Tab: Fundraisers**
- Table of campaigns
- Add Campaign popup

**Tab: B2B Stores**
- Table of stores
- Add Store popup

**Tab: Orders**
- Table of all orders

---

## PHASE 3: Workflows

**Duration:** 8-12 hours
**Dependencies:** Phase 2 complete

### Workflow Categories

Implement workflows in this order:

```
1. CRUD Basics (all types)
2. Calculated Fields
3. Status Changes with Side Effects
4. Cross-Type Operations
5. Time Clock Logic
6. Payroll Calculations
7. AI Integration
```

### 3.1 CRUD Workflows

For each data type, create:

1. **Create [Type]**
   - Trigger: Button click
   - Action: Create new [Type]
   - Set all fields from form inputs
   - Set defaults where needed
   - Reset form, close popup

2. **Update [Type]**
   - Trigger: Button click
   - Action: Make changes to [Type]
   - Only update non-empty fields

3. **Delete [Type]**
   - Trigger: Button click (with confirmation)
   - Action: Delete [Type]
   - Handle cascade deletes where needed

### 3.2 Calculated Field Workflows

#### Quote Total Calculation
```
When: QuoteLineItem created/changed/deleted
Action: Make changes to Parent Quote
  - total = This Quote's line_items:each item's total:sum
```

#### Job Subtotal Calculation
```
When: JobItem created/changed/deleted
Action: Make changes to Parent Job
  - subtotal = Search for JobItems where job = This Job:each item's line_total:sum
```

#### JobItem Line Total
```
When: JobItem created/changed
Action: Make changes to This JobItem
  - line_total = This JobItem's quantity × This JobItem's unit_price
```

#### Invoice Total Calculation
```
When: InvoiceLineItem created/changed/deleted
Action: Make changes to Parent Invoice
  - total = This Invoice's line_items:each item's total:sum
```

### 3.3 Status Change Workflows

#### Job Status Change with Activity Log
```
When: Job's status is changed
Actions:
1. Create JobActivity
   - job = This Job
   - activity_type = status_changed (or completed/archived)
   - description = "Status changed from [old] to [new]"
   - old_value = This Job's status before change
   - new_value = This Job's status
```

#### Invoice Paid Status
```
When: Invoice status changed to paid
Actions:
1. Make changes to Invoice
   - paid_date = Current date/time
   - amount_paid = This Invoice's total (if not already set)
```

### 3.4 Cross-Type Operations

#### Convert Quote to Job
```
When: Button "Convert to Job" clicked
Conditions: Quote's job is empty
Actions:
1. Create new Job
   - customer = Quote's customer
   - name = "Job from Quote #" + Quote's unique id (first 8 chars)
   - description = Quote's notes
   - status = approved
   - quote = This Quote
   - subtotal = Quote's total

2. For each Quote's line_items:
   Create JobItem
   - job = Job created in step 1
   - item_type = other
   - description = line_item's description
   - quantity = line_item's quantity
   - unit_price = line_item's unit_price
   - line_total = line_item's total
   - status = pending

3. Make changes to Quote
   - job = Job created in step 1
   - status = approved

4. Create JobActivity
   - job = Job created in step 1
   - activity_type = quote_converted
   - description = "Job created from Quote"
```

#### Create Invoice from Job
```
When: Button "Create Invoice" clicked on Job Details
Conditions: Job's invoice is empty
Actions:
1. Create Invoice
   - customer = Job's customer
   - job = This Job
   - status = draft

2. For each JobItem where job = This Job:
   Create InvoiceLineItem (add to Invoice's line_items)
   - description = JobItem's description
   - quantity = JobItem's quantity
   - unit_price = JobItem's unit_price
   - total = JobItem's line_total
   - job_item = This JobItem

3. Make changes to Invoice
   - total = sum of line_items totals

4. Make changes to Job
   - invoice = Invoice created in step 1

5. Create JobActivity
   - activity_type = invoice_created
```

### 3.5 Time Clock Workflows

#### Clock Action
```
When: Clock button clicked
Conditions: Validate sequence (see below)
Actions:
1. Create TimeLog
   - employee = Selected Employee
   - action = Button's action type
   - timestamp = Current date/time
2. Refresh displays
```

**Sequence Validation (run before action):**
```
Custom state: last_action = 
  Search for TimeLogs where employee = Selected AND 
  timestamp > Today's date:first item's action

Allowed actions based on last_action:
- null/empty → start_work only
- start_work → break_start, end_work
- break_start → break_end only
- break_end → break_start, end_work
- end_work → start_work only
```

#### Calculate Shift Summary
```
When: Employee selected OR TimeLog created
Actions (using Toolbox plugin for calculation):
1. Get today's logs for employee
2. Calculate work_minutes:
   - Sum time between start_work and end_work pairs
3. Calculate break_minutes:
   - Sum time between break_start and break_end pairs
4. net_minutes = work_minutes - break_minutes
5. net_hours = net_minutes / 60
6. Store in custom states for display
```

### 3.6 Payroll Calculations

#### Calculate Employee Balance
```
When: Employee selected for ledger view
Data source expressions:
- total_earnings = Search for PayrollTransactions where 
    employee = This Employee AND type = earnings:each item's amount:sum
- total_advances = Search for PayrollTransactions where 
    employee = This Employee AND type = advance:each item's amount:sum
- total_payments = Search for PayrollTransactions where 
    employee = This Employee AND type = payment:each item's amount:sum
- balance = total_earnings - total_advances - total_payments
```

#### Payroll Report
```
When: Date range changed
For each Employee:
- Filter transactions by date range
- Calculate period totals using same formula
- Display in repeating group
```

### 3.7 Financial Summary

```
When: Date range changed
Data source expressions:
- total_sales = Search for SalesEntries where date ≥ start AND date ≤ end:
    each item's amount:sum
- total_tax = Search for SalesEntries where date ≥ start AND date ≤ end:
    each item's tax_amount:sum
- total_expenses = Search for ExpenseEntries where date ≥ start AND date ≤ end:
    each item's amount:sum
- net_income = total_sales - total_expenses
```

---

## PHASE 4: AI Tools Integration

**Duration:** 4-6 hours
**Dependencies:** Phase 3 complete, API Connector configured

### 4.1 API Connector Calls

Create API call for each tool (or one dynamic call):

**Option A: Single Dynamic Call**
```
API Call: GenerateAI
Method: POST
URL: https://api.openai.com/v1/chat/completions
Headers:
  Authorization: Bearer [api_key from App settings]
  Content-Type: application/json
Body:
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "<system_message>"},
    {"role": "user", "content": "<user_prompt>"}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

### 4.2 Tool Prompts (Store in Option Set or Database)

Create an Option Set "AIToolType" or a data type "AIToolConfig":

| Tool | System Message | Prompt Template |
|------|----------------|-----------------|
| layout_generator | "You are a helpful AI assistant for Sign Guy AI, a sign shop management system." | [Full prompt from AI config doc] |
| print_checklist | Same | [Full prompt] |
| brand_kit | Same | [Full prompt] |
| document_creator | Same | [Full prompt] |
| overdue_assistant | Same | [Full prompt] |
| design_intake | Same | [Full prompt] |

### 4.3 AI Generation Workflow

```
When: Generate button clicked
Actions:
1. Show loading state
2. Build prompt:
   - Get template for selected tool
   - Replace {input} with form data (formatted as text)
   - Replace any specific placeholders

3. Call API: GenerateAI
   - system_message = tool's system message
   - user_prompt = built prompt

4. Create AIResponse
   - tool = selected tool
   - input_data = form data (as JSON text)
   - output = API response's choices[0].message.content
   - job = (if provided in form)
   - customer = (if provided in form)

5. Display result
6. Hide loading state
```

### 4.4 AI History Workflow

```
When: History button clicked
Data source: Search for AIResponses where tool = selected tool
             sorted by Created Date descending
             limit 100
Display in repeating group
Click to load into result display
```

---

## PHASE 5: Customer Portal (Future)

**Duration:** 10-15 hours
**Dependencies:** All previous phases, User authentication

### 5.1 Authentication Setup

1. Enable Bubble's built-in User type
2. Add fields to User:
   - role (text or Option Set: owner, staff, customer)
   - linked_customer (Customer type) - for portal users
   - linked_employee (Employee type) - for staff

3. Create signup/login pages
4. Set up email verification

### 5.2 Portal Pages

Create separate page group for portal:

| Page | Purpose |
|------|---------|
| /portal | Customer dashboard |
| /portal/profile | Edit profile |
| /portal/quotes | View/approve quotes |
| /portal/jobs | View job status |
| /portal/invoices | View/pay invoices |
| /portal/orders | Order history |

### 5.3 Privacy Rules

Update each data type's privacy:

**Customer**
```
When: Current User's linked_customer is This Customer
Can view: yes
Can modify: yes (limited fields via API workflow)
```

**Quote**
```
When: Current User's linked_customer is This Quote's customer
Can view: yes
Can modify: no (except via approve/decline workflow)
```

**Job**
```
When: Current User's linked_customer is This Job's customer
Can view: yes (limited fields)
Can modify: no
```

**Invoice**
```
When: Current User's linked_customer is This Invoice's customer
Can view: yes
Can modify: no
```

**All Internal Types (Employee, TimeLog, PayrollTransaction, etc.)**
```
When: Current User's role is not customer
Can view: yes
Otherwise: no
```

### 5.4 Portal Workflows

#### Approve Quote
```
When: Approve button clicked
Conditions: 
  - Current User's role = customer
  - Quote's customer = Current User's linked_customer
  - Quote's status = sent
Actions:
  - Make changes to Quote: status = approved
```

#### Decline Quote
```
When: Decline button clicked
Conditions: Same as above
Actions:
  - Make changes to Quote: status = declined
```

### 5.5 Staff Restrictions

Implement via conditional workflows:

```
When: Delete button clicked
Conditions: Current User's role = owner
Actions: Delete thing
(Staff cannot delete)
```

```
When: Invoice edit saved
Conditions: 
  - Current User's role = staff
  - This Invoice's status is sent or paid
Actions: Show alert "Cannot edit sent/paid invoices"
(Block the edit)
```

---

## BUILD CHECKLIST

### Phase 0: Option Sets ⬜
- [ ] CustomerStatus
- [ ] QuoteStatus
- [ ] JobStatus
- [ ] JobActivityType
- [ ] JobItemStatus
- [ ] JobItemType
- [ ] InvoiceStatus
- [ ] PayrollTransactionType
- [ ] ExpenseCategory
- [ ] TimeLogAction
- [ ] WebstoreType
- [ ] FundraiserStatus
- [ ] WebstoreOrderStatus
- [ ] API Connector (OpenAI)

### Phase 1: Data Types ⬜
- [ ] Customer
- [ ] Employee
- [ ] Quote + QuoteLineItem
- [ ] Job
- [ ] JobItem
- [ ] JobNote
- [ ] JobActivity
- [ ] Invoice + InvoiceLineItem
- [ ] TimeLog
- [ ] PayrollTransaction
- [ ] SalesEntry
- [ ] ExpenseEntry
- [ ] Task
- [ ] AIResponse
- [ ] FundraiserCampaign
- [ ] B2BStore
- [ ] WebstoreOrder

### Phase 2: Pages ⬜
- [ ] Reusable: Sidebar
- [ ] Reusable: Header
- [ ] Dashboard (index)
- [ ] Customers
- [ ] Quotes
- [ ] Jobs (list)
- [ ] Job Details
- [ ] Invoices
- [ ] Time Clock
- [ ] Payroll
- [ ] Productivity
- [ ] Financials
- [ ] AI Tools
- [ ] Webstores

### Phase 3: Workflows ⬜
- [ ] All CRUD operations
- [ ] Calculated totals (Quote, Job, Invoice)
- [ ] Status change logging
- [ ] Convert Quote to Job
- [ ] Create Invoice from Job
- [ ] Time Clock sequence validation
- [ ] Payroll calculations
- [ ] Financial summaries

### Phase 4: AI Tools ⬜
- [ ] API Connector calls
- [ ] Prompt templates
- [ ] Generate workflow
- [ ] History display
- [ ] Result display

### Phase 5: Customer Portal ⬜
- [ ] User authentication
- [ ] Role-based access
- [ ] Portal pages
- [ ] Privacy rules
- [ ] Approval workflows

---

## TESTING CHECKLIST

### Core Flows
- [ ] Create customer → Create quote → Convert to job → Create invoice → Mark paid
- [ ] Add job items, verify subtotal calculation
- [ ] Add notes, verify activity log
- [ ] Status changes log correctly
- [ ] Delete cascade works (Job → Items, Notes, Activities)

### Time Clock
- [ ] Clock sequence enforced
- [ ] Summary calculates correctly
- [ ] Multiple break periods work

### Payroll
- [ ] Balance formula correct
- [ ] Report filters by date
- [ ] Transaction types affect balance correctly

### AI Tools
- [ ] Each tool generates response
- [ ] Responses save to database
- [ ] History loads correctly

---

## PERFORMANCE NOTES

1. **Add indexes** on frequently searched fields:
   - Customer: status, name
   - Job: status, customer, is_archived
   - Invoice: status, customer
   - TimeLog: employee, timestamp

2. **Limit search results** where possible (use :items until # or pagination)

3. **Use "Do a search for" efficiently** - avoid nested searches in repeating groups

4. **Consider Backend Workflows** for heavy calculations (shift summaries, reports)

5. **Cache AI responses** - check for identical recent requests before calling API
