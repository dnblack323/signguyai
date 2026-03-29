# Sign Guy AI - Bubble-Ready Database Schema

## OPTION SETS (ENUMS)

---

### CustomerStatus
| Display | Value | Order |
|---------|-------|-------|
| Lead | lead | 1 |
| Active | active | 2 |
| Inactive | inactive | 3 |

---

### QuoteStatus
| Display | Value | Order |
|---------|-------|-------|
| Draft | draft | 1 |
| Sent | sent | 2 |
| Approved | approved | 3 |
| Declined | declined | 4 |

---

### OrderStatus
| Display | Value | Order |
|---------|-------|-------|
| Quoted | quoted | 1 |
| Approved | approved | 2 |
| In Production | in_production | 3 |
| Installed | installed | 4 |
| Complete | complete | 5 |
| Archived | archived | 6 |

---

### OrderActivityType
| Display | Value | Order |
|---------|-------|-------|
| Created | created | 1 |
| Status Changed | status_changed | 2 |
| Quote Converted | quote_converted | 3 |
| Invoice Created | invoice_created | 4 |
| Item Added | item_added | 5 |
| Item Updated | item_updated | 6 |
| Item Deleted | item_deleted | 7 |
| Note Added | note_added | 8 |
| Completed | completed | 9 |
| Archived | archived | 10 |
| Unarchived | unarchived | 11 |

---

### JobTicketStatus
| Display | Value | Order |
|---------|-------|-------|
| Pending | pending | 1 |
| In Production | in_production | 2 |
| Done | done | 3 |

---

### JobTicketCategory
| Display | Value | Order |
|---------|-------|-------|
| Banner | banner | 1 |
| Yard Sign | yard_sign | 2 |
| Decal | decal | 3 |
| Wrap | wrap | 4 |
| Install | install | 5 |
| Design | design | 6 |
| Vehicle Graphics | vehicle_graphics | 7 |
| Window Graphics | window_graphics | 8 |
| Dimensional Letters | dimensional_letters | 9 |
| Monument Sign | monument_sign | 10 |
| Other | other | 11 |

---

### InvoiceStatus
| Display | Value | Order |
|---------|-------|-------|
| Draft | draft | 1 |
| Sent | sent | 2 |
| Paid | paid | 3 |
| Overdue | overdue | 4 |

---

### PayrollTransactionType
| Display | Value | Order |
|---------|-------|-------|
| Earnings | earnings | 1 |
| Advance | advance | 2 |
| Payment | payment | 3 |

---

### ExpenseCategory
| Display | Value | Order |
|---------|-------|-------|
| Materials | materials | 1 |
| Labor | labor | 2 |
| Equipment | equipment | 3 |
| Utilities | utilities | 4 |
| Rent | rent | 5 |
| Other | other | 6 |

---

### TimeLogAction
| Display | Value | Order |
|---------|-------|-------|
| Start Work | start_work | 1 |
| Break Start | break_start | 2 |
| Break End | break_end | 3 |
| End Work | end_work | 4 |

---

### WebstoreType
| Display | Value | Order |
|---------|-------|-------|
| Fundraiser | fundraiser | 1 |
| B2B | b2b | 2 |

---

### FundraiserStatus
| Display | Value | Order |
|---------|-------|-------|
| Active | active | 1 |
| Paused | paused | 2 |
| Completed | completed | 3 |
| Cancelled | cancelled | 4 |

---

### WebstoreOrderStatus
| Display | Value | Order |
|---------|-------|-------|
| Pending | pending | 1 |
| Processing | processing | 2 |
| Completed | completed | 3 |
| Cancelled | cancelled | 4 |

---

## DATA TYPES

---

### Customer

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| name | text | YES | NO | - | Customer's full name |
| company | text | NO | NO | empty | Company/business name |
| phone | text | NO | NO | empty | Phone number |
| email | text | NO | NO | empty | Email address |
| status | CustomerStatus (option set) | YES | NO | lead | Customer lifecycle status |
| notes | text | NO | NO | empty | Free-form notes |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |
| updated_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- Customer → Quote (1:many) - via Quote.customer_id
- Customer → Order (1:many) - vian Order.customer_id
- Customer → Invoice (1:many) - via Invoice.customer_id

---

### Quote

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| customer_id | Customer (thing) | YES | NO | - | Link to Customer |
| line_items | QuoteLineItem (thing) | NO | YES | empty list | Embedded line items |
| notes | text | NO | NO | empty | Quote notes/terms |
| status | QuoteStatus (option set) | YES | NO | draft | Quote lifecycle status |
| total | number | YES | NO | 0 | **CALCULATED** - see below |
| order_id | Order (thing) | NO | NO | empty | Link to converted Order (null until converted) |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |
| updated_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- Quote → Customer (many:1) - via customer_id
- Quote → Order (1:1) - via order_id (set when quote converts to job)
- Quote → QuoteLineItem (1:many) - embedded list

**Calculated Fields:**
- `total` = SUM of all line_items[].total

---

### QuoteLineItem

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| description | text | YES | NO | - | Line item description |
| quantity | number | YES | NO | 1 | Quantity of items |
| unit_price | number | YES | NO | - | Price per unit |
| total | number | YES | NO | 0 | **CALCULATED** - see below |

**Calculated Fields:**
- `total` = quantity × unit_price

---

### Order

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| customer_id | Customer (thing) | YES | NO | - | Link to Customer |
| name | text | YES | NO | - | Order/project name |
| description | text | NO | NO | empty | Order description |
| status | OrderStatus (option set) | YES | NO | quoted | Order lifecycle status |
| due_date | date | NO | NO | empty | Expected completion date |
| quote_id | Quote (thing) | NO | NO | empty | Link to originating Quote |
| invoice_id | Invoice (thing) | NO | NO | empty | Link to generated Invoice |
| subtotal | number | YES | NO | 0 | **CALCULATED** - see below |
| is_archived | yes/no | YES | NO | no | Soft delete/archive flag |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |
| updated_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- Order → Customer (many:1) - via customer_id
- Order → Quote (1:1) - via quote_id
- Order → Invoice (1:1) - via invoice_id
- Order → JobTicket (1:many) - vian OrderTicket.order_id
- Order → OrderNote (1:many) - via OrderNote.order_id
- Order → OrderActivity (1:many) - via OrderActivity.order_id
- Order → Task (1:many) - via Task.order_id

**Calculated Fields:**
- `subtotal` = SUM of all JobTickets where order_id = this Order's id → line_total

---

### JobTicket

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| order_id | Order (thing) | YES | NO | - | Link to parent Order |
| item_type | JobTicketCategory (option set) | YES | NO | other | Type of sign/product |
| description | text | YES | NO | - | Item description |
| quantity | number | YES | NO | 1 | Quantity |
| unit_price | number | YES | NO | 0 | Price per unit |
| line_total | number | YES | NO | 0 | **CALCULATED** - see below |
| status | JobTicketStatus (option set) | YES | NO | pending | Item production status |
| notes | text | NO | NO | empty | Item-specific notes |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- JobTicket → Order (many:1) - via order_id
- JobTicket → InvoiceLineItem (1:1) - via InvoiceLineItem.job_item_id

**Calculated Fields:**
- `line_total` = quantity × unit_price

---

### OrderNote

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| order_id | Order (thing) | YES | NO | - | Link to parent Order |
| content | text | YES | NO | - | Note content |
| author | text | NO | NO | empty | Person who added note |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- OrderNote → Order (many:1) - via order_id

---

### OrderActivity

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| order_id | Order (thing) | YES | NO | - | Link to parent Order |
| activity_type | OrderActivityType (option set) | YES | NO | - | Type of activity logged |
| description | text | YES | NO | - | Human-readable description |
| old_value | text | NO | NO | empty | Previous value (for changes) |
| new_value | text | NO | NO | empty | New value (for changes) |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- OrderActivity → Order (many:1) - via order_id

---

### Invoice

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| customer_id | Customer (thing) | YES | NO | - | Link to Customer |
| order_id | Order (thing) | NO | NO | empty | Link to source Order |
| line_items | InvoiceLineItem (thing) | NO | YES | empty list | Embedded line items |
| total | number | YES | NO | 0 | **CALCULATED** - see below |
| status | InvoiceStatus (option set) | YES | NO | draft | Invoice lifecycle status |
| due_date | date | NO | NO | empty | Payment due date |
| notes | text | NO | NO | empty | Invoice notes/terms |
| amount_paid | number | YES | NO | 0 | Total amount received |
| paid_date | date | NO | NO | empty | Date payment was received |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |
| updated_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- Invoice → Customer (many:1) - via customer_id
- Invoice → Order (1:1) - via order_id
- Invoice → InvoiceLineItem (1:many) - embedded list

**Calculated Fields:**
- `total` = SUM of all line_items[].total
- `balance_due` (not stored, calculate on display) = total - amount_paid

---

### InvoiceLineItem

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| description | text | YES | NO | - | Line item description |
| quantity | number | YES | NO | 1 | Quantity |
| unit_price | number | YES | NO | 0 | Price per unit |
| total | number | YES | NO | 0 | **CALCULATED** - see below |
| job_item_id | JobTicket (thing) | NO | NO | empty | Link to source JobTicket |

**Relationships:**
- InvoiceLineItem → JobTicket (many:1) - via job_item_id (tracks origin)

**Calculated Fields:**
- `total` = quantity × unit_price

---

### Employee

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| name | text | YES | NO | - | Employee full name |
| hourly_rate | number | YES | NO | - | Pay rate per hour |
| is_active | yes/no | YES | NO | yes | Employment status |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- Employee → TimeLog (1:many) - via TimeLog.employee_id
- Employee → PayrollTransaction (1:many) - via PayrollTransaction.employee_id

---

### TimeLog

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| employee_id | Employee (thing) | YES | NO | - | Link to Employee |
| action | TimeLogAction (option set) | YES | NO | - | Clock action type |
| timestamp | date | YES | NO | Current date/time | When action occurred |

**Relationships:**
- TimeLog → Employee (many:1) - via employee_id

**Action Sequence Rules:**
- From `null` (no logs today): Only `start_work` allowed
- From `start_work`: Only `break_start` or `end_work` allowed
- From `break_start`: Only `break_end` allowed
- From `break_end`: Only `break_start` or `end_work` allowed
- From `end_work`: Only `start_work` allowed

---

### PayrollTransaction

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| employee_id | Employee (thing) | YES | NO | - | Link to Employee |
| type | PayrollTransactionType (option set) | YES | NO | - | Transaction type |
| amount | number | YES | NO | - | Dollar amount |
| description | text | NO | NO | empty | Transaction description |
| date | date | YES | NO | Current date | Transaction date |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- PayrollTransaction → Employee (many:1) - via employee_id

**Payroll Balance Calculation (per employee):**
- `total_earnings` = SUM of amount WHERE type = "earnings"
- `total_advances` = SUM of amount WHERE type = "advance"
- `total_payments` = SUM of amount WHERE type = "payment"
- `balance` = total_earnings - total_advances - total_payments
  - Positive balance = employer owes employee
  - Negative balance = employee has received advance

---

### SalesEntry

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| date | date | YES | NO | - | Sale date |
| amount | number | YES | NO | - | Sale amount (pre-tax) |
| tax_amount | number | YES | NO | 0 | Tax collected |
| description | text | NO | NO | empty | Sale description |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

---

### ExpenseEntry

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| date | date | YES | NO | - | Expense date |
| amount | number | YES | NO | - | Expense amount |
| category | ExpenseCategory (option set) | YES | NO | other | Expense category |
| description | text | NO | NO | empty | Expense description |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Financial Summary Calculations (for date range):**
- `total_sales` = SUM of SalesEntry.amount for date range
- `total_tax` = SUM of SalesEntry.tax_amount for date range
- `total_expenses` = SUM of ExpenseEntry.amount for date range
- `net_income` = total_sales - total_expenses

---

### Task

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| title | text | YES | NO | - | Task title |
| description | text | NO | NO | empty | Task details |
| order_id | Order (thing) | NO | NO | empty | Link to related Order |
| due_date | date | NO | NO | empty | Task due date |
| is_complete | yes/no | YES | NO | no | Completion status |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- Task → Order (many:1) - via order_id (optional)

---

### AIResponse

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| tool | text | YES | NO | - | AI tool name used |
| input_data | text | YES | NO | - | JSON string of input parameters |
| output | text | YES | NO | - | AI-generated response |
| order_id | Order (thing) | NO | NO | empty | Link to related Order |
| customer_id | Customer (thing) | NO | NO | empty | Link to related Customer |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**AI Tool Types:**
- layout_generator
- print_checklist
- brand_kit
- document_creator
- overdue_assistant
- design_intake

**Relationships:**
- AIResponse → Order (many:1) - via order_id (optional)
- AIResponse → Customer (many:1) - via customer_id (optional)

---

### FundraiserCampaign

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| name | text | YES | NO | - | Campaign name |
| goal | number | YES | NO | - | Fundraising goal amount |
| start_date | date | YES | NO | - | Campaign start date |
| end_date | date | YES | NO | - | Campaign end date |
| organizer | text | YES | NO | - | Organizer name/contact |
| payout_rules | text | NO | NO | empty | Payout terms/rules |
| products | text | NO | YES | empty list | List of allowed product IDs |
| total_raised | number | YES | NO | 0 | **CALCULATED** - see below |
| status | FundraiserStatus (option set) | YES | NO | active | Campaign status |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- FundraiserCampaign → WebstoreOrder (1:many) - via WebstoreOrder.store_id WHERE store_type = "fundraiser"

**Calculated Fields:**
- `total_raised` = SUM of WebstoreOrder.total WHERE store_id = this campaign's id AND store_type = "fundraiser"
- (Alternatively: incremented on each order creation)

---

### B2BStore

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| company_name | text | YES | NO | - | B2B customer company |
| contact_email | text | YES | NO | - | Login/contact email |
| login_password | text | YES | NO | - | Store access password |
| allowed_products | text | NO | YES | empty list | List of allowed product IDs |
| discount_percent | number | YES | NO | 0 | Percentage discount for this customer |
| is_active | yes/no | YES | NO | yes | Store active status |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- B2BStore → WebstoreOrder (1:many) - via WebstoreOrder.store_id WHERE store_type = "b2b"

---

### WebstoreOrder

| Field Name | Bubble Field Type | Required | List | Default Value | Notes |
|------------|-------------------|----------|------|---------------|-------|
| id | text | YES | NO | Auto-generated UUID | Primary key |
| store_type | WebstoreType (option set) | YES | NO | - | "fundraiser" or "b2b" |
| store_id | text | YES | NO | - | ID of FundraiserCampaign or B2BStore |
| items | text | YES | YES | empty list | JSON array of order items |
| total | number | YES | NO | 0 | Order total amount |
| status | WebstoreOrderStatus (option set) | YES | NO | pending | Order status |
| order_id | Order (thing) | NO | NO | empty | Auto-created Order for this order |
| created_at | date | YES | NO | Current date/time | ISO 8601 timestamp |

**Relationships:**
- WebstoreOrder → Order (1:1) - via order_id (auto-created)
- WebstoreOrder → FundraiserCampaign (many:1) - via store_id WHERE store_type = "fundraiser"
- WebstoreOrder → B2BStore (many:1) - via store_id WHERE store_type = "b2b"

**Note:** `items` field contains JSON array with structure:
```json
[
  {
    "product_id": "string",
    "product_name": "string",
    "quantity": number,
    "unit_price": number,
    "total": number
  }
]
```

---

## CALCULATED TOTALS SUMMARY

### Quote Total
```
Quote.total = SUM(QuoteLineItem.total for all line_items)
QuoteLineItem.total = QuoteLineItem.quantity × QuoteLineItem.unit_price
```

### Order Subtotal
```
Order.subtotal = SUM(JobTicket.line_total for all JobTickets where JobTicket.order_id = Order.id)
JobTicket.line_total = JobTicket.quantity × JobTicket.unit_price
```
**Trigger:** Recalculate when JobTicket is added, updated, or deleted.

### Invoice Total
```
Invoice.total = SUM(InvoiceLineItem.total for all line_items)
InvoiceLineItem.total = InvoiceLineItem.quantity × InvoiceLineItem.unit_price
Invoice.balance_due = Invoice.total - Invoice.amount_paid
```

### Payroll Balance (per Employee)
```
total_earnings = SUM(PayrollTransaction.amount WHERE type = "earnings" AND employee_id = Employee.id)
total_advances = SUM(PayrollTransaction.amount WHERE type = "advance" AND employee_id = Employee.id)
total_payments = SUM(PayrollTransaction.amount WHERE type = "payment" AND employee_id = Employee.id)
balance = total_earnings - total_advances - total_payments
```
- Positive: Employer owes employee
- Negative: Employee has advance balance

### Daily Shift Summary (per Employee per Date)
```
work_minutes = SUM(time between start_work and end_work pairs)
break_minutes = SUM(time between break_start and break_end pairs)
net_minutes = work_minutes - break_minutes
net_hours = net_minutes / 60
```

### Financial Summary (for date range)
```
total_sales = SUM(SalesEntry.amount for date range)
total_tax = SUM(SalesEntry.tax_amount for date range)
total_expenses = SUM(ExpenseEntry.amount for date range)
net_income = total_sales - total_expenses
```

### Fundraiser Total Raised
```
FundraiserCampaign.total_raised = SUM(WebstoreOrder.total WHERE store_type = "fundraiser" AND store_id = FundraiserCampaign.id)
```
**Trigger:** Increment when new order is placed.

---

## RELATIONSHIP DIAGRAM

```
┌─────────────┐
│  Customer   │
└─────┬───────┘
      │ 1:many
      ├───────────────┐─────────────────┐
      ▼               ▼                 ▼
┌─────────────┐ ┌─────────────┐   ┌─────────────┐
│   Quote     │ │    Order      │   │  Invoice    │
└─────┬───────┘ └──────┬──────┘   └─────────────┘
      │                │                 ▲
      │ 1:1            │ 1:many          │ 1:1
      │ (converts to)  │                 │
      └────────────────┼─────────────────┘
                       │
      ┌────────────────┼────────────────┬────────────────┐
      ▼                ▼                ▼                ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  JobTicket    │ │  OrderNote    │ │ OrderActivity │ │    Task     │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘


┌─────────────┐
│  Employee   │
└─────┬───────┘
      │ 1:many
      ├───────────────────────┐
      ▼                       ▼
┌─────────────┐       ┌──────────────────┐
│  TimeLog    │       │PayrollTransaction│
└─────────────┘       └──────────────────┘


┌───────────────────┐     ┌─────────────┐
│FundraiserCampaign │     │  B2BStore   │
└─────────┬─────────┘     └──────┬──────┘
          │ 1:many                │ 1:many
          └───────────┬──────────┘
                      ▼
              ┌───────────────┐
              │WebstoreOrder  │───1:1───▶ Order (auto-created)
              └───────────────┘
```

---

## CORE WORKFLOW: Customer → Quote → Order → Invoice

1. **Customer** is created with status `lead`
2. **Quote** is created linked to Customer
   - Add QuoteLineItems with quantity × unit_price
   - Quote.total is calculated
   - Status: draft → sent → approved/declined
3. **Order** is created from Quote (via convert action)
   - JobTickets are auto-created from QuoteLineItems
   - Order.subtotal is calculated
   - Status flows: quoted → approved → in_production → installed → complete → archived
4. **Invoice** is created from Order
   - InvoiceLineItems are auto-created from JobTickets
   - Invoice.total is calculated
   - Links back to Order (order_id) and Customer (customer_id)
   - Status: draft → sent → paid/overdue

---

## MONGODB COLLECTIONS MAPPING

| Bubble Data Type | MongoDB Collection |
|------------------|-------------------|
| Customer | customers |
| Quote | quotes |
| Order | orders |
| JobTicket | job_items |
| OrderNote | job_notes |
| OrderActivity | job_activities |
| Invoice | invoices |
| Employee | employees |
| TimeLog | timelogs |
| PayrollTransaction | payroll_transactions |
| SalesEntry | sales_entries |
| ExpenseEntry | expense_entries |
| Task | tasks |
| AIResponse | ai_responses |
| FundraiserCampaign | fundraiser_campaigns |
| B2BStore | b2b_stores |
| WebstoreOrder | webstore_orders |
