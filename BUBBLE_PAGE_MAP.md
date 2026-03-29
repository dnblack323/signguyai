# Sign Guy AI - Page/Route Map

## NAVIGATION STRUCTURE

### Main Layout Component
**File:** `/app/frontend/src/components/MainLayout.js`

**Structure:**
- Collapsible sidebar (desktop)
- Mobile drawer navigation
- Logo in header
- Active route highlighting

**Navigation Groups:**
1. **Core Operations**
   - Dashboard (`/`)
   - Customers (`/customers`)
   - Quotes (`/quotes`)
   - Orders (`/orders`)
   - Invoices (`/invoices`)

2. **Operations** (separator)
   - Time Clock (`/timeclock`)
   - Payroll (`/payroll`)
   - Productivity (`/productivity`)
   - Financials (`/financials`)

3. **Tools** (separator)
   - AI Tools (`/ai-tools`)
   - Webstores (`/webstores`)

---

## PAGE DETAILS

---

### PAGE: Dashboard
**Route:** `/`
**File:** `/app/frontend/src/pages/Dashboard.js`
**Purpose:** Central overview of business metrics, recent activity, and quick actions

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| StatCard (x4) | Card Grid | Total Customers, Active Orders, Pending Invoices, Today's Revenue |
| Overdue Alert | Alert Banner | Conditional - shows when overdue invoices exist |
| RecentActivity | Card with List | Recent orders and overdue invoices |
| QuickActions | Card with Buttons | New Customer, New Quote, New Order, Time Clock |

**Primary Data Sources:**
- `fetchDashboardStats()` → `/api/dashboard/stats`
- `fetchCustomers()` → `/api/customers`
- `fetchOrders()` → `/api/orders`
- `fetchInvoices()` → `/api/invoices`

**Key Actions/Workflows:**
- View overdue invoices → navigates to `/invoices?status=overdue`
- Quick action buttons → navigate to respective pages

**Data-testids:**
- `dashboard`
- `quick-add-customer`
- `quick-add-quote`
- `quick-add-job`
- `quick-clock-in`
- `view-overdue`

---

### PAGE: Customers
**Route:** `/customers`
**File:** `/app/frontend/src/pages/Customers.js`
**Purpose:** CRUD management for customer records

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, count, Add Customer button |
| Search Input | Input | Search by name, company, email |
| Status Filter | Select | Filter: All, Lead, Active, Inactive |
| Customer Table | Table | Columns: Customer (avatar, name, company), Contact (email, phone), Status, Created, Actions |
| Customer Dialog | Modal Form | Create/Edit customer form |

**Primary Data Sources:**
- `fetchCustomers(params)` → `/api/customers`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Create Customer | Submit dialog form | WF-CUST-01 |
| Edit Customer | Click edit icon | Opens dialog → WF-CUST-02 |
| Delete Customer | Click delete icon + confirm | WF-CUST-03 |
| Search | Type in search input | WF-CUST-04 (filter) |
| Filter by Status | Select status | WF-CUST-04 (filter) |

**Form Fields:**
- name* (text)
- company (text)
- email (email)
- phone (text)
- status (select: lead, active, inactive)
- notes (textarea)

**Data-testids:**
- `customers-page`
- `add-customer-btn`
- `customer-name-input`
- `customer-company-input`
- `customer-email-input`
- `customer-phone-input`
- `customer-status-select`
- `customer-notes-input`
- `customer-submit-btn`
- `customer-search-input`
- `customer-filter-status`
- `customer-row-{id}`
- `edit-customer-{id}`
- `delete-customer-{id}`

---

### PAGE: Quotes
**Route:** `/quotes`
**File:** `/app/frontend/src/pages/Quotes.js`
**Purpose:** Create and manage quotes with line items, convert approved quotes to orders

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, count, New Quote button |
| Status Filter | Select | Filter: All, Draft, Sent, Approved, Declined |
| Quotes Table | Table | Columns: Quote #, Customer, Items, Total, Status, Created, Actions |
| Quote Dialog | Modal Form | Create/Edit quote with line items |
| Line Items Editor | Dynamic Form | Add/edit/remove line items with live total |

**Primary Data Sources:**
- `fetchQuotes(params)` → `/api/quotes`
- `fetchCustomers()` → `/api/customers`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Create Quote | Submit dialog form | WF-QUOTE-01 |
| Edit Quote | Click edit icon | Opens dialog → WF-QUOTE-02 |
| Add Line Item | Click "Add Item" | WF-QUOTE-04 |
| Remove Line Item | Click trash on item | WF-QUOTE-06 |
| Convert to Order | Click "To Order" button | WF-QUOTE-07 |

**Form Fields:**
- customer_id* (select)
- status (select: draft, sent, approved, declined)
- line_items[] (dynamic list)
  - description (text)
  - quantity (number)
  - unit_price (number)
- notes (textarea)

**Calculated Display:**
- Total = SUM(line_items[].quantity × unit_price)

**Data-testids:**
- `quotes-page`
- `add-quote-btn`
- `quote-customer-select`
- `quote-status-select`
- `line-item-desc-{idx}`
- `line-item-qty-{idx}`
- `line-item-price-{idx}`
- `quote-notes-input`
- `quote-submit-btn`
- `quote-filter-status`
- `quote-row-{id}`
- `convert-quote-{id}`
- `edit-quote-{id}`

---

### PAGE: Orders (List View)
**Route:** `/orders`
**File:** `/app/frontend/src/pages/OrdersPage.js`
**Purpose:** View and manage all orders with filter tabs

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, count, New Order button |
| Filter Tabs | Tab Buttons | Active, Completed, Archived (with counts) |
| Orders List | Card List | Each job shows: name, status badge (dropdown), customer, due date, subtotal |
| Order Row Actions | Dropdown + Button | View, Mark Complete, Archive, Delete |
| New Order Dialog | Modal Form | Create new job |

**Primary Data Sources:**
- `fetchOrders({ filter_type })` → `/api/orders?filter_type=active|completed|archived`
- `fetchCustomers()` → `/api/customers`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Create Order | Submit dialog form | WF-JOB-01 |
| Change Status | Click status badge dropdown | WF-JOB-03 |
| View Details | Click "View" or job name | Navigate to `/orders/{id}` |
| Mark Complete | Dropdown → Mark Complete | WF-JOB-04 |
| Archive | Dropdown → Archive | WF-JOB-05 |
| Delete | Dropdown → Delete + confirm | WF-JOB-07 |

**Form Fields (New Order):**
- customer_id* (select)
- name* (text)
- description (textarea)
- status (select: quoted, approved, in_production, installed)
- due_date (date)

**Data-testids:**
- `orders-page`
- `add-job-btn`
- `job-customer-select`
- `job-name-input`
- `job-submit-btn`
- `filter-active`
- `filter-completed`
- `filter-archived`
- `job-row-{id}`
- `view-job-{id}`

---

### PAGE: Order Details
**Route:** `/orders/:id`
**File:** `/app/frontend/src/pages/OrderDetail.js`
**Purpose:** Comprehensive order management with line items, notes, activity, and financial snapshot

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Back Button | Button | Returns to Orders list |
| Header Card | Card | Order name, status dropdown, customer link, due date, edit button, quick actions |
| Quick Actions | Button Group | Create Invoice, Mark Complete, Archive/Unarchive |
| Financial Snapshot | Card Grid (5) | Quote Total, Order Subtotal, Invoiced, Paid, Balance Due |
| Tabs | Tab Container | Line Items, Notes, Activity |
| Line Items Table | Table in Tab | Type, Description, Qty, Unit Price, Total, Status dropdown, Actions |
| Notes List | List in Tab | Add note input + note cards with delete |
| Activity Log | Scrollable List | Activity icons, descriptions, timestamps |
| Edit Order Dialog | Modal Form | Edit name, status, due date, description |
| Add/Edit Item Dialog | Modal Form | Item form with type, description, qty, price, status, notes |

**Primary Data Sources:**
- `getJobDetails(id)` → `/api/orders/{id}/details`
- Returns: job, customer, quote, invoice, job_items, notes, activities, financial_snapshot

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Edit Order | Edit button → submit | WF-JOB-02 |
| Change Status | Status dropdown | WF-JOB-03 |
| Mark Complete | Quick action button | WF-JOB-04 |
| Archive/Unarchive | Quick action button | WF-JOB-05 / WF-JOB-06 |
| Create Invoice | Quick action button | WF-INV-02 |
| Add Item | Add Item button → submit | WF-JOBITEM-01 |
| Edit Item | Edit icon → submit | WF-JOBITEM-02 |
| Delete Item | Delete icon + confirm | WF-JOBITEM-03 |
| Change Item Status | Status dropdown in row | WF-JOBITEM-02 |
| Add Note | Type + send button | WF-JOBNOTE-01 |
| Delete Note | Delete icon on note | WF-JOBNOTE-02 |

**Data-testids:**
- `order-details-page`
- `back-to-orders`
- `job-status-dropdown`
- `create-invoice-btn`
- `add-line-item-btn`
- `new-note-input`
- `add-note-btn`

---

### PAGE: Invoices
**Route:** `/invoices`
**File:** `/app/frontend/src/pages/Invoices.js`
**Purpose:** Create and manage invoices, track payments

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, count, New Invoice button |
| Summary Cards (4) | Card Grid | Total, Paid, Pending, Overdue |
| Status Filter | Select | Filter: All, Draft, Sent, Paid, Overdue |
| Invoices Table | Table | Columns: Invoice #, Customer, Order, Total, Status, Due Date, Actions |
| Invoice Dialog | Modal Form | Create/Edit invoice |

**Primary Data Sources:**
- `fetchInvoices(params)` → `/api/invoices`
- `fetchCustomers()` → `/api/customers`
- `fetchOrders()` → `/api/orders`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Create Invoice | Submit dialog form | WF-INV-01 |
| Edit Invoice | Click edit icon | Opens dialog → WF-INV-03 |
| Mark as Paid | Click "Mark Paid" button | WF-INV-04 (status=paid) |

**Form Fields:**
- customer_id* (select)
- order_id (select, filtered by customer)
- total* (number)
- status (select: draft, sent, paid, overdue)
- due_date (date)
- notes (textarea)

**Calculated Display:**
- Summary totals calculated from invoice list

**Data-testids:**
- `invoices-page`
- `add-invoice-btn`
- `invoice-customer-select`
- `invoice-job-select`
- `invoice-total-input`
- `invoice-status-select`
- `invoice-due-date-input`
- `invoice-notes-input`
- `invoice-submit-btn`
- `invoice-filter-status`
- `invoice-row-{id}`
- `mark-paid-{id}`
- `edit-invoice-{id}`

---

### PAGE: Time Clock
**Route:** `/timeclock`
**File:** `/app/frontend/src/pages/TimeClock.js`
**Purpose:** Employee clock in/out with break tracking

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, Add Employee button |
| Employee Selector | Card with Select | Choose employee + status badge |
| Clock Actions | Card with Buttons | Start Work, Start Break, End Break, End Work (enabled/disabled based on sequence) |
| Today's Summary | Card with Stats | Work Time, Break Time, Net Hours |
| Today's Activity | Card with List | Log of today's clock actions with timestamps |
| Add Employee Dialog | Modal Form | Create new employee |

**Primary Data Sources:**
- `fetchEmployees()` → `/api/employees`
- `getClockStatus(employee_id)` → `/api/timeclock/{employee_id}/status`
- `getTodayLogs(employee_id)` → `/api/timeclock/{employee_id}/today`
- `getShiftSummary(employee_id)` → `/api/timeclock/{employee_id}/summary`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Create Employee | Submit dialog form | Creates employee |
| Clock Action | Click action button | WF-TIME-01 |
| Select Employee | Change select | Loads status, logs, summary |

**Clock Buttons State Logic:**
- `start_work`: enabled when status = not_started or finished
- `break_start`: enabled when status = working
- `break_end`: enabled when status = on_break
- `end_work`: enabled when status = working

**Data-testids:**
- `timeclock-page`
- `add-employee-btn`
- `employee-name-input`
- `employee-rate-input`
- `employee-submit-btn`
- `employee-select`
- `clock-start_work`
- `clock-break_start`
- `clock-break_end`
- `clock-end_work`
- `log-{id}`
- `empty-add-employee`

---

### PAGE: Payroll
**Route:** `/payroll`
**File:** `/app/frontend/src/pages/Payroll.js`
**Purpose:** Manage employee earnings, advances, and payments with balance tracking

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, Add Transaction button |
| Employee Ledger | Card | Employee selector, balance summary (4 stats), transaction table |
| Balance Info | Card | Explanation of Earnings, Advances, Payments, Balance formula |
| Payroll Report | Card | Date range inputs, employee period summary table |
| Add Transaction Dialog | Modal Form | Record earnings/advance/payment |

**Primary Data Sources:**
- `fetchEmployees()` → `/api/employees`
- `getPayrollTransactions({ employee_id })` → `/api/payroll/transactions`
- `getPayrollBalance(employee_id)` → `/api/payroll/balance/{employee_id}`
- `getPayrollReport(start_date, end_date)` → `/api/payroll/report`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Add Transaction | Submit dialog form | WF-PAY-01 |
| View Employee Ledger | Select employee | WF-PAY-02, WF-PAY-03 |
| View Period Report | Change date range | WF-PAY-04 |

**Form Fields:**
- employee_id* (select)
- type* (select: earnings, advance, payment)
- amount* (number)
- date (date)
- description (text)

**Data-testids:**
- `payroll-page`
- `add-transaction-btn`
- `payroll-employee-select`
- `payroll-type-select`
- `payroll-amount-input`
- `payroll-date-input`
- `payroll-description-input`
- `payroll-submit-btn`
- `ledger-employee-select`
- `report-start-date`
- `report-end-date`

---

### PAGE: Productivity
**Route:** `/productivity`
**File:** `/app/frontend/src/pages/Productivity.js`
**Purpose:** Task management with list, calendar, and Kanban views

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, New Task button |
| View Tabs | Tab List | Tasks (list), Calendar, Order Kanban |
| Tasks List View | Two-column layout | To Do (incomplete), Completed |
| Task Item | Checkbox + Card | Title, description, due date badge, job badge |
| Calendar View | Calendar + Day panel | Calendar with task indicators, selected day's tasks |
| Kanban View | 5-column board | Orders grouped by status (quoted → complete) |
| Add Task Dialog | Modal Form | Create new task |

**Primary Data Sources:**
- `fetchTasks()` → `/api/tasks`
- `fetchOrders()` → `/api/orders`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Create Task | Submit dialog form | WF-TASK-01 |
| Toggle Complete | Click checkbox | WF-TASK-03 |
| Delete Task | Click delete icon | WF-TASK-04 |
| Select Calendar Date | Click date | Shows tasks for that date |

**Form Fields:**
- title* (text)
- description (text)
- order_id (select)
- due_date (date)

**Kanban Columns:**
- Quoted
- Approved
- In Production
- Installed
- Complete

**Data-testids:**
- `productivity-page`
- `add-task-btn`
- `task-title-input`
- `task-description-input`
- `task-job-select`
- `task-due-date-input`
- `task-submit-btn`
- `productivity-list-view`
- `productivity-calendar-view`
- `productivity-kanban-view`
- `task-{id}`
- `task-checkbox-{id}`
- `delete-task-{id}`

---

### PAGE: Financials
**Route:** `/financials`
**File:** `/app/frontend/src/pages/Financials.js`
**Purpose:** Track daily sales, expenses, and view financial summaries

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title, Add Sale button, Add Expense button |
| Date Range Filter | Card with Inputs | Start date, end date |
| Summary Cards (4) | Card Grid | Total Sales, Sales Tax, Expenses, Net Income |
| Tabs | Tab List | Overview, Sales, Expenses |
| Overview Tab | Two cards | Expense Breakdown by category, Recent Activity |
| Sales Tab | Table | Date, Description, Amount, Tax |
| Expenses Tab | Table | Date, Category, Description, Amount |
| Add Sale Dialog | Modal Form | Record sale |
| Add Expense Dialog | Modal Form | Record expense |

**Primary Data Sources:**
- `getSalesEntries({ start_date, end_date })` → `/api/financials/sales`
- `getExpenseEntries({ start_date, end_date })` → `/api/financials/expenses`
- `getFinancialSummary(start_date, end_date)` → `/api/financials/summary`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Add Sale | Submit sale dialog | WF-FIN-01 |
| Add Expense | Submit expense dialog | WF-FIN-02 |
| Change Date Range | Change date inputs | Reloads data for range |

**Sale Form Fields:**
- date (date)
- amount* (number)
- tax_amount (number)
- description (text)

**Expense Form Fields:**
- date (date)
- category (select: materials, labor, equipment, utilities, rent, other)
- amount* (number)
- description (text)

**Data-testids:**
- `financials-page`
- `add-sales-btn`
- `add-expense-btn`
- `sales-date-input`
- `sales-amount-input`
- `sales-tax-input`
- `sales-description-input`
- `sales-submit-btn`
- `expense-date-input`
- `expense-category-select`
- `expense-amount-input`
- `expense-description-input`
- `expense-submit-btn`
- `financials-start-date`
- `financials-end-date`

---

### PAGE: AI Tools
**Route:** `/ai-tools`
**File:** `/app/frontend/src/pages/AITools.js`
**Purpose:** AI-powered assistants for design, branding, and business tasks

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title |
| Tool Selector | Card Sidebar | List of 6 AI tools with icons |
| Tool Header | Card | Selected tool name, description, History button |
| Input Form | Card | Dynamic fields based on selected tool |
| Generate Button | Button | Triggers AI generation |
| Result | Card | AI output with copy button |
| History Panel | Card (conditional) | Past generations for selected tool |

**Available Tools:**
| Tool ID | Name | Category | Purpose |
|---------|------|----------|---------|
| layout_generator | Layout Generator | Design | Create layout concepts |
| print_checklist | Print-Ready Checklist | Design | Check for print issues |
| brand_kit | Brand Kit Generator | Branding | Colors, fonts, taglines |
| document_creator | Document Creator | Business | Proposals, scope docs |
| overdue_assistant | Overdue Payment Assistant | Business | Collection messages |
| design_intake | Design Intake Chat | Customer | Extract project requirements |

**Primary Data Sources:**
- `generateAIContent(tool, input_data)` → `/api/ai/generate`
- `fetchAIHistory({ tool })` → `/api/ai/history`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Select Tool | Click tool in sidebar | Loads tool form |
| Generate | Click Generate button | Sends to AI, displays result |
| Copy Result | Click copy button | Copies to clipboard |
| View History | Click History button | Shows past generations |
| Load from History | Click history item | Loads result into view |

**Data-testids:**
- `ai-tools-page`
- `tool-{tool_id}`
- `input-{field_name}`
- `generate-btn`
- `copy-result-btn`
- `view-history-btn`

---

### PAGE: Webstores
**Route:** `/webstores`
**File:** `/app/frontend/src/pages/Webstores.js`
**Purpose:** Manage fundraiser campaigns and B2B customer stores

**Main UI Components:**
| Component | Type | Description |
|-----------|------|-------------|
| Header | Section | Title |
| Tabs | Tab List | Fundraisers, B2B Stores, Orders |
| Fundraiser Tab | Card + Table | New Campaign button, campaigns table |
| B2B Tab | Card + Table | New B2B Store button, stores table |
| Orders Tab | Table | All webstore orders with type, items, total, status, linked job |
| Fundraiser Dialog | Modal Form | Create fundraiser campaign |
| B2B Dialog | Modal Form | Create B2B store |

**Primary Data Sources:**
- `getFundraisers()` → `/api/webstores/fundraiser`
- `getB2BStores()` → `/api/webstores/b2b`
- `getWebstoreOrders()` → `/api/webstores/orders`

**Key Actions/Workflows:**
| Action | Trigger | Workflow |
|--------|---------|----------|
| Create Fundraiser | Submit dialog form | Creates campaign |
| Create B2B Store | Submit dialog form | Creates store |
| (Orders auto-created via external API) | External | WF-WEB-01 |

**Fundraiser Form Fields:**
- name* (text)
- goal (number)
- start_date (date)
- end_date (date)
- organizer* (text)
- payout_rules (textarea)

**B2B Form Fields:**
- company_name* (text)
- contact_email* (email)
- login_password* (password)
- discount_percent (number)

**Data-testids:**
- `webstores-page`
- `tab-fundraiser`
- `tab-b2b`
- `tab-orders`
- `add-fundraiser-btn`
- `fundraiser-name-input`
- `fundraiser-goal-input`
- `fundraiser-organizer-input`
- `fundraiser-start-input`
- `fundraiser-end-input`
- `fundraiser-payout-input`
- `fundraiser-submit-btn`
- `fundraiser-row-{id}`
- `add-b2b-btn`
- `b2b-company-input`
- `b2b-email-input`
- `b2b-password-input`
- `b2b-discount-input`
- `b2b-submit-btn`
- `b2b-row-{id}`

---

## REUSABLE COMPONENTS

### From `/app/frontend/src/components/ui/`

| Component | Usage Across Pages |
|-----------|-------------------|
| Button | All pages |
| Card, CardContent, CardHeader, CardTitle | All pages |
| Input | All forms |
| Label | All forms |
| Textarea | Customers, Quotes, Orders, Invoices, Financials, Webstores |
| Select, SelectTrigger, SelectContent, SelectItem, SelectValue | All pages with dropdowns |
| Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger | All create/edit forms |
| Table, TableHeader, TableBody, TableRow, TableHead, TableCell | Customers, Quotes, Orders, Invoices, Payroll, Financials, Webstores |
| Badge | All pages (status indicators) |
| Tabs, TabsList, TabsTrigger, TabsContent | Orders Details, Productivity, Financials, Webstores |
| Checkbox | Productivity (tasks) |
| Calendar | Productivity |
| ScrollArea | AI Tools, Orders (activity) |
| Separator | Orders |
| DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator | Orders |

### From `/app/frontend/src/lib/utils.js`

| Utility | Description |
|---------|-------------|
| `cn()` | Classname merger (clsx + tailwind-merge) |
| `formatCurrency(amount)` | Format number as $X,XXX.XX |
| `formatDate(dateStr)` | Format ISO date as readable |
| `formatDateTime(dateStr)` | Format with time |
| `formatTime(dateStr)` | Format time only |
| `getStatusColor(status)` | Return Tailwind classes for status badges |
| `getInitials(name)` | Extract initials for avatars |

---

## PAGE SUMMARY TABLE

| Route | Page | File | Key Features |
|-------|------|------|--------------|
| `/` | Dashboard | Dashboard.js | Stats, alerts, quick actions |
| `/customers` | Customers | Customers.js | CRUD table, search, filter |
| `/quotes` | Quotes | Quotes.js | Line items, convert to job |
| `/orders` | Orders List | Orders.js | Filter tabs, status dropdown |
| `/orders/:id` | Order Details | Orders.js | Items, notes, activity, financials |
| `/invoices` | Invoices | Invoices.js | Summaries, mark paid |
| `/timeclock` | Time Clock | TimeClock.js | Clock actions, daily summary |
| `/payroll` | Payroll | Payroll.js | Ledger, balance, reports |
| `/productivity` | Productivity | Productivity.js | Tasks, calendar, Kanban |
| `/financials` | Financials | Financials.js | Sales, expenses, summaries |
| `/ai-tools` | AI Tools | AITools.js | 6 AI assistants |
| `/webstores` | Webstores | Webstores.js | Fundraisers, B2B, orders |

---

## CONTEXT PROVIDER

**File:** `/app/frontend/src/context/AppContext.js`

All pages consume the `AppContext` via `useApp()` hook which provides:

**State:**
- customers, orders, quotes, invoices, employees, tasks
- dashboardStats

**API Methods (examples):**
- `fetchCustomers()`, `createCustomer()`, `updateCustomer()`, `deleteCustomer()`
- `fetchOrders()`, `createJob()`, `updateJob()`, `deleteJob()`, `completeJob()`, `archiveJob()`
- `fetchQuotes()`, `createQuote()`, `updateQuote()`, `convertQuoteToJob()`
- `fetchInvoices()`, `createInvoice()`, `updateInvoice()`, `createInvoiceFromJob()`
- `getJobDetails()`, `createJobItem()`, `updateJobItem()`, `deleteJobItem()`
- `createJobNote()`, `deleteJobNote()`
- `fetchEmployees()`, `createEmployee()`
- `clockAction()`, `getClockStatus()`, `getTodayLogs()`, `getShiftSummary()`
- `createPayrollTransaction()`, `getPayrollTransactions()`, `getPayrollBalance()`, `getPayrollReport()`
- `createSalesEntry()`, `getSalesEntries()`, `createExpenseEntry()`, `getExpenseEntries()`, `getFinancialSummary()`
- `fetchTasks()`, `createTask()`, `updateTask()`, `deleteTask()`
- `generateAIContent()`, `fetchAIHistory()`
- `createFundraiser()`, `getFundraisers()`, `createB2BStore()`, `getB2BStores()`, `getWebstoreOrders()`
- `fetchDashboardStats()`
