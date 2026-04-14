# Sign Guy AI - Workflows Documentation (Current)

> Last updated: Feb 2026. Reflects Admin Payroll Worksheet, Unified Productivity, Signatures/Drawings, and multi-tenant architecture.

---

## CUSTOMER WORKFLOWS

### WF-CUST-01: Create Customer
**Trigger:** Submit new customer form
**Data:** `INSERT INTO customers { id, tenant_id, name, company, phone, email, status: "lead", notes, created_at, updated_at }`
**Returns:** Customer object

### WF-CUST-02: Update Customer
**Trigger:** Submit edit form
**Validation:** Customer must exist in tenant
**Data:** `UPDATE customers SET { ...provided_fields, updated_at: NOW() }`

### WF-CUST-03: Delete Customer
**Trigger:** Confirm delete
**Data:** `DELETE FROM customers WHERE id AND tenant_id`

### WF-CUST-04: Search/Filter Customers
**Trigger:** Search input or status filter
**Query:** Filter by `status`, search across `name`, `company`, `email` (case-insensitive). Always scoped to `tenant_id`.

---

## QUOTE WORKFLOWS

### WF-QUOTE-01: Create Quote
**Trigger:** Submit new quote form
**Validation:** Customer must exist in tenant
**Actions:**
1. Calculate each `line_item.total = quantity * unit_price`
2. Calculate `total = SUM(line_items[].total)`
3. Insert with `status: "draft"`, `order_id: null`

### WF-QUOTE-02: Update Quote
**Validation:** Quote exists, `order_id` is null (not converted)
**Actions:** Recalculate totals if line_items changed, update fields

### WF-QUOTE-07: Convert Quote to Order
**Trigger:** Click "Convert to Order"
**Validation:** Quote not already converted (`order_id` is null)
**Actions:**
1. Create Order linked to customer, set `status: "approved"`
2. Create JobTicket for each QuoteLineItem
3. Log "quote_converted" OrderActivity
4. Update Quote: set `order_id`, `status: "approved"`
**Circular write-back:** Quote.order_id <-> Order.quote_id

---

## ORDER WORKFLOWS

### WF-JOB-01: Create Order (Direct)
**Trigger:** Submit new order form or `/orders/new` wizard
**Data:** Insert order with `status: "quote"`, `subtotal: 0`, `is_archived: false`
**Side effect:** Log "created" OrderActivity

### WF-JOB-02: Update Order
**Actions:** Update fields, log "status_changed" if status changed

### WF-JOB-03: Order Status Change
**Status flow:** `quote -> approved -> in_progress -> completed -> invoiced -> archived`
**Any active status can skip to `completed`.**

### WF-JOB-04: Mark Complete
Set `status: "completed"`, log activity

### WF-JOB-05/06: Archive/Unarchive
Toggle `is_archived` and `status`

### WF-JOB-07: Delete Order
Cascade delete: `job_tickets`, `job_notes`, `job_activities`, `order_drawings`, `signatures`, then order

---

## JOB TICKET WORKFLOWS

### WF-JOBITEM-01: Add Ticket
**Trigger:** Add item form on Order Detail or "Add Ticket to Order" page
**Actions:** Calculate `line_total = qty * unit_price`, insert, recalculate Order subtotal, log activity

### WF-JOBITEM-02: Update Ticket
Recalculate `line_total`, recalculate Order subtotal, log activity

### WF-JOBITEM-03: Delete Ticket
Delete ticket, recalculate Order subtotal, log activity

### WF-JOBITEM-RECALC: Recalculate Order Subtotal
`Order.subtotal = SUM(all job_tickets[].line_total WHERE order_id)`

---

## ORDER DRAWING WORKFLOWS

### WF-DRAW-01: Create Drawing
**Trigger:** Save from DrawingCanvasPad on Order Detail
**Validation:** Order exists in tenant. If `parent_type = "job_ticket"`, ticket must exist. If `parent_type = "uploaded_image"`, file must exist.
**Actions:**
1. Decode base64 image data
2. Upload PNG to Emergent Object Storage -> get `storage_key`
3. Insert `order_drawings` record with metadata + `storage_key`
**Returns:** Drawing record with presigned `storage_url`

### WF-DRAW-02: Update Drawing Metadata
Update `label`, `title`, `notes`, `status`, `tags`, `requires_attention`

### WF-DRAW-03: Delete Drawing
Delete drawing record (Object Storage blob persists for retention)

### WF-DRAW-04: Get Drawing Image
**Trigger:** `GET /api/order-drawings/file/:drawing_id`
**Actions:** Fetch from Object Storage using `storage_key`, return binary PNG

### WF-DRAW-05: List Drawings
**Filters:** By `order_id`, `parent_type`, `drawing_type`, `status`
All scoped to `tenant_id`

---

## SIGNATURE WORKFLOWS

### WF-SIG-01: Create Signature Requirement
**Trigger:** Admin marks a record as requiring signature
**Data:** Insert `signatures` record with `status: "pending"`, `requires_signature: true`
**Auto-mapping:** `parent_record_type` -> `signature_type` (e.g., "quote" -> "quote_acceptance")

### WF-SIG-02: Request Signature via Email
**Trigger:** Admin clicks "Request Signature"
**Actions:**
1. Generate unique `request_token` with expiry
2. Store email, origin URL
3. Send email with link to `/customer-sign/:token`
4. Status remains "pending"

### WF-SIG-03: Capture Signature (Authenticated)
**Trigger:** Admin captures signature in-app via SignatureCaptureModal
**Actions:**
1. Decode base64 signature image
2. Upload to Object Storage -> `storage_key`
3. Update signature record: `status: "signed"`, `signed_at`, signer details

### WF-SIG-04: Public Signature Capture
**Trigger:** Customer opens email link `/customer-sign/:token`
**Validation:** Token valid, not expired, signature pending
**Actions:** Same as WF-SIG-03 but via public page (no auth required)

### WF-SIG-05: Decline Signature
**Trigger:** Customer declines via public link
**Data:** Set `status: "declined"`, record reason

### WF-SIG-06: Get Signature Image
**Trigger:** `GET /api/signatures/file/:signature_id`
**Actions:** Fetch from Object Storage, return binary PNG

---

## TIME CLOCK WORKFLOWS

### WF-TIME-01: Clock Action
**Trigger:** Employee clicks clock button (Start Work / Break Start / Break End / End Work)
**Sequence validation:**
| Last Action | Valid Next |
|-------------|-----------|
| null | start_work |
| start_work | break_start, end_work |
| break_start | break_end |
| break_end | break_start, end_work |
| end_work | start_work |

**Actions:**
1. Insert raw `timelogs` record
2. Create or update `timeclock_shifts` record:
   - `start_work`: Create new shift with `clock_in`, status "working"
   - `break_start`: Update shift status "on_break", set `current_break_start`
   - `break_end`: Calculate break_minutes, clear `current_break_start`, status "working"
   - `end_work`: Set `clock_out`, calculate `total_hours`, `regular_hours`, `overtime_hours`, status "completed"

### WF-TIME-02: Backfill Shifts
**Trigger:** Opening payroll report for a date range
**Purpose:** Convert older raw `timelogs` into `timeclock_shifts` records for employees who clocked before the shift system existed
**Actions:** Query `timelogs` by date range, group into work sessions, create `timeclock_shifts`

### WF-TIME-03: Admin Edit Shift (Inline)
**Trigger:** Edit cells in Payroll Worksheet's day row
**Actions:** Update `timeclock_shifts` record: `clock_in`, `clock_out`, `lunch_start`, `lunch_end`, `break_minutes`. Recalculate `total_hours`, `regular_hours`, `overtime_hours`.

### WF-TIME-04: Admin Create Manual Shift
**Trigger:** Admin adds shift via payroll worksheet for a date with no existing shift
**Actions:** Insert `timeclock_shifts` with `is_manual: true`

---

## PAYROLL WORKSHEET WORKFLOWS

### WF-PAY-WORKSHEET: Load Payroll Worksheet
**Trigger:** Select employee + date range on Payroll page
**Steps:**
1. Read tenant `payroll_settings` for default cycle/start day
2. Call `GET /api/payroll/report?employee_id=&start_date=&end_date=`
3. Backend builds compensation snapshot:
   - Fetch employee details (hourly_rate, overtime_rate)
   - Backfill `timeclock_shifts` if needed
   - Fetch `payroll_transactions` in range (adjustments)
   - Fetch `payroll_hours` (legacy manual entries)
   - Return: `{ employee, timeclock_shifts[], transactions[], manual_entries[], signoff }`
4. Frontend `buildWorksheetRows()` creates one row per day with editable fields
5. Frontend `buildAdjustmentRows()` maps transactions to editable rows
6. Frontend `summarizeWorksheet()` calculates totals

### WF-PAY-SAVE: Save Worksheet Changes
**Trigger:** Admin clicks Save (only enabled when "unsaved changes" badge visible)
**Actions:**
1. For each modified shift row: `PUT /api/payroll/timeclock-shifts/:id` or `POST /api/payroll/timeclock-shifts` (new)
2. For each adjustment row: `POST/PUT/DELETE /api/payroll/transactions`
3. Refresh worksheet from server
4. Clear "unsaved changes" badge

### WF-PAY-SIGNOFF: Review & Sign-Off
**Trigger:** Admin clicks Review/Approve on sign-off strip
**Actions:**
1. `PUT /api/payroll/signoff` with `reviewed_by`, `review_date` (or `approved_by`, `approval_date`)
2. Once approved, worksheet becomes read-only for non-admin users

### WF-PAY-LEGACY: Resolve Legacy Manual Entry
**Trigger:** Admin uses resolution UI on legacy entry
**Modes:**
- `keep_legacy`: Keep entry as-is, include in totals
- `exclude`: Remove from totals (set `included_in_totals: false`)
- `convert`: Move hours to a specific date as a new shift
**Data:** `PUT /api/payroll/legacy-manual-entries/:id/resolution`

### WF-PAY-EXPORT: Export/Print Worksheet
**Trigger:** Admin clicks Export CSV or Print
**Precondition:** No unsaved changes
**Actions:**
1. `buildPayrollCsv()` or `buildPayrollPrintHtml()` from current worksheet state
2. Download file or open print dialog

### WF-PAY-01: Create Payroll Transaction (Adjustment)
**Trigger:** Add row in Adjustments Panel
**Types:** `earnings` (bonus/commission), `advance` (pay advance), `payment` (recorded payment)
**Data:** `INSERT INTO payroll_transactions { id, tenant_id, employee_id, type, amount, description, date }`

### WF-PAY-02: Get Transactions
**Filters:** `employee_id`, `start_date`, `end_date`

### WF-PAY-03: Calculate Balance (All-Time)
```
balance = SUM(earnings) - SUM(advances) - SUM(payments)
Positive = employer owes employee
Negative = employee has advance balance
```

---

## PAYROLL SETTINGS WORKFLOW

### WF-PAY-SETTINGS: Configure Pay Period
**Trigger:** Company Settings -> Payroll Settings panel
**Actions:**
1. `PATCH /api/auth/tenant` with `payroll_settings: { default_cycle, pay_week_start_day }`
2. Next time Payroll Worksheet loads, `getCurrentCycleRange()` uses these settings to compute default date range

---

## UNIFIED PRODUCTIVITY WORKFLOWS

### WF-PROD-01: Get Unified Items
**Trigger:** Load Productivity page (any view)
**Backend aggregation** (`productivity_query.py`):
1. Load all tasks, orders, job_tickets, production_tasks, employee_schedules, appointments for tenant
2. Normalize each into `ProductivityItem` with common fields:
   - `uid` (compound: `{source_type}:{id}` or `{source_type}:{id}:{day}` for schedules)
   - `type`, `source_type`, `status`, `priority`, `due_datetime`
   - `board_column` (open/in_progress/blocked/done)
   - `color` (status-derived)
3. Apply filters (type, status, priority, assigned user, customer, date range, search)
4. Return unified list

### WF-PROD-02: Update Productivity Item
**Trigger:** Toggle complete, change status, drag on Kanban
**Endpoint:** `PATCH /api/productivity/items/:uid`
**Actions:**
1. Parse `uid` to determine `source_type` and `source_id`
2. For `schedule_shift` UIDs, parse compound `schedule_shift:{id}:{day}` format
3. Route update to the correct collection (`tasks`, `orders`, `job_tickets`, `production_tasks`, `employee_schedules`)
4. Return updated item

### WF-PROD-03: Get Summary
**Trigger:** Dashboard view
**Returns:** Counts for due_today, overdue, waiting_on_approval, scheduled_this_week, my_assigned, open/completed, by_type, by_board_column

---

## INVOICE WORKFLOWS

### WF-INV-01: Create Invoice (Direct)
Insert with calculated line item totals, `amount_paid: 0`, `status: "draft"`

### WF-INV-02: Create Invoice from Order
Copy JobTickets -> InvoiceLineItems (snapshot), link Order.invoice_id, log activity

### WF-INV-03: Update Invoice
Recalculate totals if line_items changed. If status -> "paid", set `paid_date`.

### WF-INV-04: Status Changes
`draft -> sent -> paid/overdue`
Mark Paid: set `amount_paid = total`, `paid_date = NOW()`

### WF-INV-05: Partial Payment
Add to `amount_paid`. If `amount_paid >= total`, auto-mark as paid.

---

## FINANCIAL WORKFLOWS

### WF-FIN-01: Create Sales Entry
Insert `{ date, amount, tax_amount, description }`

### WF-FIN-02: Create Expense Entry
Insert `{ date, amount, category, description }`

### WF-FIN-03: Financial Summary
```
total_sales = SUM(sales_entries.amount)
total_tax = SUM(sales_entries.tax_amount)
total_expenses = SUM(expense_entries.amount)
net_income = total_sales - total_expenses
```

---

## TASK WORKFLOWS

### WF-TASK-01: Create Task
Insert `{ title, description, order_id (opt), assigned_to (opt), due_date, is_complete: false }`

### WF-TASK-02: Update Task
Update provided fields

### WF-TASK-03: Toggle Complete
Toggle `is_complete`

### WF-TASK-04: Delete Task
Delete record

---

## WEBSTORE WORKFLOWS

### WF-WEB-01: Create Webstore Order
1. Auto-create Customer if not exists (by webstore type marker)
2. Auto-create Order linked to customer
3. Insert WebstoreOrder linked to Order
4. If fundraiser, increment `total_raised`

---

## EMPLOYEE PORTAL WORKFLOWS

### WF-EMPPORTAL-01: PIN Login
**Trigger:** Employee enters PIN on `/employee-portal/login`
**Validation:** Find employee by PIN in tenant, check `is_active`
**Returns:** JWT token scoped to employee

### WF-EMPPORTAL-02: View Assigned Tasks
Query `production_tasks` + `tasks` where `assigned_to = employee_id`

### WF-EMPPORTAL-03: View Pay Stubs
Query `payroll_transactions` and `timeclock_shifts` for employee

---

## CUSTOMER PORTAL WORKFLOWS

### WF-CUSTPORTAL-01: Customer Login
Email + password authentication against `customers` collection

### WF-CUSTPORTAL-02: View Orders
Filtered by `customer_id`, read-only

### WF-CUSTPORTAL-03: Proof Approval
Customer reviews artwork proof, approves/requests revision/rejects

### WF-CUSTPORTAL-04: Messaging
Threaded conversations between customer and shop

---

## AI WORKFLOWS

### WF-AI-01: Generate Content
**Trigger:** Submit AI tool form
**Actions:**
1. Validate AI credits available
2. Call OpenAI GPT-5.2 via Emergent LLM Key
3. Deduct credits
4. Store `ai_responses` record
5. Return generated content

### WF-AI-02: AI Assistant Chat
Conversational interface with action layer (can create tasks, look up orders, etc.)

---

## DOCUMENT & EMAIL WORKFLOWS

### WF-DOC-01: Upload Document
Upload to Object Storage, store metadata in `documents`

### WF-EMAIL-01: Send from Template
Merge template variables, send via email service

---

## DASHBOARD WORKFLOW

### WF-DASH-01: Get Dashboard Stats
Now served via Unified Productivity summary endpoint:
```
total_customers, active_orders, pending_invoices,
today_revenue, overdue_total, overdue_count,
due_today, my_assigned, open_items
```

---

## WORKFLOW SUMMARY BY MODULE

| Module | Create | Read | Update | Delete | Special |
|--------|--------|------|--------|--------|---------|
| Customer | WF-CUST-01 | WF-CUST-04 | WF-CUST-02 | WF-CUST-03 | Portal toggle |
| Quote | WF-QUOTE-01 | - | WF-QUOTE-02 | - | WF-QUOTE-07 (convert) |
| Order | WF-JOB-01 | WF-JOB-08 | WF-JOB-02,03 | WF-JOB-07 | Complete, Archive |
| JobTicket | WF-JOBITEM-01 | - | WF-JOBITEM-02 | WF-JOBITEM-03 | Subtotal recalc |
| Drawing | WF-DRAW-01 | WF-DRAW-05 | WF-DRAW-02 | WF-DRAW-03 | Object Storage |
| Signature | WF-SIG-01 | - | WF-SIG-03 | - | Email request, Public capture |
| Invoice | WF-INV-01 | - | WF-INV-03 | - | From Order, Payment |
| TimeClock | WF-TIME-01 | - | WF-TIME-03 | - | Backfill, Manual shift |
| Payroll Worksheet | WF-PAY-WORKSHEET | - | WF-PAY-SAVE | - | Signoff, Legacy, Export |
| Payroll Txn | WF-PAY-01 | WF-PAY-02 | - | - | Balance calc |
| Productivity | WF-PROD-01 | WF-PROD-03 | WF-PROD-02 | - | Unified aggregation |
| Financial | WF-FIN-01,02 | WF-FIN-03 | - | - | Summary |
| Task | WF-TASK-01 | - | WF-TASK-02 | WF-TASK-04 | Toggle complete |
| Webstore | WF-WEB-01 | - | - | - | Auto-create |
| AI | WF-AI-01 | - | - | - | Credits, Assistant |
