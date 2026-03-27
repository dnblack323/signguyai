# Sign Guy AI - Dependency & Execution Order Map

## OVERVIEW

This document maps all dependencies between data types and workflows, identifies the required execution order, and flags circular or fragile dependencies that require special handling in Bubble.

---

## PART 1: DATA TYPE DEPENDENCIES

### Dependency Graph

```
LEVEL 0 (No Dependencies - Create First)
┌─────────────┐     ┌─────────────┐
│  Customer   │     │  Employee   │
└─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
LEVEL 1 (Single Parent Dependency)
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Quote    │     │    Job      │     │  TimeLog    │
│ →Customer   │     │ →Customer   │     │ →Employee   │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   
       │                   │           ┌─────────────┐
       │                   │           │  Payroll    │
       │                   │           │ Transaction │
       │                   │           │ →Employee   │
       │                   │           └─────────────┘
       ▼                   ▼
LEVEL 2 (Multiple/Nested Dependencies)
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ QuoteLine   │     │  JobItem    │     │  JobNote    │
│   Item      │     │ →Job        │     │ →Job        │
│ (embedded)  │     └─────────────┘     └─────────────┘
└─────────────┘            │
                           │           ┌─────────────┐
                           │           │ JobActivity │
                           │           │ →Job        │
                           │           └─────────────┘
                           ▼
LEVEL 3 (Cross-Entity Dependencies)
┌─────────────────────────────────────────────────────┐
│                      Invoice                         │
│  →Customer (required)                               │
│  →Job (optional)                                    │
│  →InvoiceLineItem.job_item →JobItem (optional)     │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│                  InvoiceLineItem                     │
│  (embedded in Invoice)                              │
│  →JobItem (optional back-reference)                 │
└─────────────────────────────────────────────────────┘

LEVEL 4 (Bidirectional/Circular References)
┌─────────────┐ ◄──────────────► ┌─────────────┐
│    Quote    │    order_id /      │    Job      │
│             │    quote_id      │             │
└─────────────┘                  └─────────────┘
       
┌─────────────┐ ◄──────────────► ┌─────────────┐
│    Job      │   invoice_id /   │  Invoice    │
│             │     order_id       │             │
└─────────────┘                  └─────────────┘
```

### Dependency Matrix

| Data Type | Depends On | Depended By | Circular? |
|-----------|------------|-------------|-----------|
| Customer | - | Quote, Job, Invoice, AIResponse | No |
| Employee | - | TimeLog, PayrollTransaction | No |
| Quote | Customer | Job (via conversion) | ⚠️ Yes (Quote↔Job) |
| QuoteLineItem | Quote (embedded) | JobItem (via conversion) | No |
| Order | Customer, Quote (optional) | JobItem, JobNote, JobActivity, Invoice, Task, WebstoreOrder | ⚠️ Yes (Job↔Quote, Job↔Invoice) |
| JobItem | Order | InvoiceLineItem | No |
| JobNote | Order | - | No |
| JobActivity | Order | - | No |
| Invoice | Customer, Job (optional) | - | ⚠️ Yes (Invoice↔Job) |
| InvoiceLineItem | Invoice (embedded), JobItem (optional) | - | No |
| TimeLog | Employee | - | No |
| PayrollTransaction | Employee | - | No |
| SalesEntry | - | - | No |
| ExpenseEntry | - | - | No |
| Task | Job (optional) | - | No |
| AIResponse | Job (optional), Customer (optional) | - | No |
| FundraiserCampaign | - | WebstoreOrder | No |
| B2BStore | - | WebstoreOrder | No |
| WebstoreOrder | Job (auto-created) | - | No |

---

## PART 2: WORKFLOW DEPENDENCIES

### Workflow Dependency Graph

```
INDEPENDENT WORKFLOWS (No Prerequisites)
════════════════════════════════════════════════════════════════
WF-CUST-01: Create Customer
WF-CUST-02: Update Customer
WF-CUST-03: Delete Customer
WF-CUST-04: Search Customers

WF-EMP-01: Create Employee
WF-EMP-02: Update Employee

WF-FIN-01: Create Sales Entry
WF-FIN-02: Create Expense Entry

WF-FUND-01: Create Fundraiser Campaign
WF-B2B-01: Create B2B Store
════════════════════════════════════════════════════════════════

LEVEL 1 WORKFLOWS (Require Level 0 Data)
════════════════════════════════════════════════════════════════
                    ┌─────────────────┐
                    │ Customer Exists │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ WF-QUOTE-01     │ │ WF-JOB-01       │ │ WF-INV-01       │
│ Create Quote    │ │ Create Order      │ │ Create Invoice  │
└─────────────────┘ └─────────────────┘ └─────────────────┘

                    ┌─────────────────┐
                    │ Employee Exists │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ WF-TIME-01      │ │ WF-TIME-02      │ │ WF-PAY-01       │
│ Clock Action    │ │ Get Today Logs  │ │ Create Payroll  │
└─────────────────┘ └─────────────────┘ │ Transaction     │
                                        └─────────────────┘
════════════════════════════════════════════════════════════════

LEVEL 2 WORKFLOWS (Require Level 1 Data)
════════════════════════════════════════════════════════════════
                    ┌─────────────────┐
                    │  Quote Exists   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ WF-QUOTE-02     │ │ WF-QUOTE-04     │ │ WF-QUOTE-07     │
│ Update Quote    │ │ Add Line Item   │ │ Convert to Job  │
└─────────────────┘ └─────────────────┘ └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Creates Job +   │
                                        │ JobItems        │
                                        │ + JobActivity   │
                                        └─────────────────┘

                    ┌─────────────────┐
                    │   Job Exists    │
                    └────────┬────────┘
                             │
    ┌────────────┬───────────┼───────────┬────────────┐
    ▼            ▼           ▼           ▼            ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│WF-JOB  │ │WF-JOBITEM│ │WF-JOBNOTE│ │WF-INV-02 │ │WF-TASK-01│
│-02,-03 │ │-01,-02   │ │-01       │ │Create Inv│ │Create    │
│Update  │ │Add/Edit  │ │Add Note  │ │from Job  │ │Task      │
│Status  │ │Item      │ │          │ │          │ │(opt job) │
└────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
    │            │           │           │
    ▼            ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────┐
│              ALL TRIGGER: WF-JOBACTIVITY                    │
│              (Auto-create activity log entry)               │
└─────────────────────────────────────────────────────────────┘
════════════════════════════════════════════════════════════════

LEVEL 3 WORKFLOWS (Require Level 2 Data + Calculations)
════════════════════════════════════════════════════════════════
┌─────────────────┐         ┌─────────────────┐
│ JobItem Changed │         │ QuoteLineItem   │
│                 │         │ Changed         │
└────────┬────────┘         └────────┬────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│ WF-JOBITEM-RECALC│        │ WF-QUOTE-RECALC │
│ Recalc Job      │         │ Recalc Quote    │
│ Subtotal        │         │ Total           │
└─────────────────┘         └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│ TimeLog Created │         │ PayrollTx       │
│                 │         │ Created         │
└────────┬────────┘         └────────┬────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌─────────────────┐
│ WF-TIME-04      │         │ WF-PAY-03       │
│ Calc Shift      │         │ Calc Employee   │
│ Summary         │         │ Balance         │
└─────────────────┘         └─────────────────┘
════════════════════════════════════════════════════════════════

COMPLEX WORKFLOWS (Multiple Dependencies)
════════════════════════════════════════════════════════════════

WF-QUOTE-07: Convert Quote to Job
├── Requires: Quote (with status ≠ converted)
├── Requires: Customer (from Quote)
├── Creates: Job
├── Creates: JobItem[] (from QuoteLineItems)
├── Creates: JobActivity
├── Updates: Quote.order_id (circular write-back)
└── Updates: Quote.status = approved

WF-INV-02: Create Invoice from Job
├── Requires: Job
├── Requires: Customer (from Job)
├── Requires: JobItem[] (optional, for line items)
├── Creates: Invoice
├── Creates: InvoiceLineItem[] (from JobItems)
├── Updates: Job.invoice_id (circular write-back)
└── Creates: JobActivity

WF-WEB-01: Create Webstore Order
├── Requires: FundraiserCampaign OR B2BStore
├── Creates: Customer (if not exists)
├── Creates: Job (auto-generated)
├── Creates: WebstoreOrder
├── Updates: FundraiserCampaign.total_raised (if fundraiser)
└── Links: WebstoreOrder.order_id

════════════════════════════════════════════════════════════════
```

---

## PART 3: EXECUTION ORDER REQUIREMENTS

### Data Type Creation Order

**Must create in this exact sequence:**

```
PHASE 1: Foundation (No dependencies)
══════════════════════════════════════
1. All Option Sets (see Phase 0 in Build Plan)
2. Customer
3. Employee
4. SalesEntry
5. ExpenseEntry
6. FundraiserCampaign
7. B2BStore

PHASE 2: First-Level Dependents
══════════════════════════════════════
8. Quote (needs Customer)
9. QuoteLineItem (embedded in Quote)
10. Job (needs Customer) 
    ⚠️ Initially WITHOUT quote field - add later
11. TimeLog (needs Employee)
12. PayrollTransaction (needs Employee)
13. Task (job field optional)

PHASE 3: Second-Level Dependents
══════════════════════════════════════
14. JobItem (needs Job)
15. JobNote (needs Job)
16. JobActivity (needs Job)
17. AIResponse (job/customer optional)

PHASE 4: Cross-References (Circular)
══════════════════════════════════════
18. Invoice (needs Customer, optional Job)
19. InvoiceLineItem (embedded, optional JobItem ref)
20. WebstoreOrder (needs Job for auto-creation)

PHASE 5: Add Circular References
══════════════════════════════════════
21. Add Quote.job field (reference to Job)
22. Add Job.quote field (reference to Quote)
23. Add Job.invoice field (reference to Invoice)
```

### Workflow Implementation Order

```
STAGE 1: Basic CRUD (Independent)
═══════════════════════════════════════════════════════════════
Order │ Workflow              │ Reason
──────┼───────────────────────┼─────────────────────────────────
  1   │ Customer CRUD         │ Foundation - no dependencies
  2   │ Employee CRUD         │ Foundation - no dependencies
  3   │ SalesEntry CRUD       │ Independent financial tracking
  4   │ ExpenseEntry CRUD     │ Independent financial tracking
  5   │ FundraiserCampaign    │ Independent webstore setup
  6   │ B2BStore CRUD         │ Independent webstore setup

STAGE 2: Dependent CRUD
═══════════════════════════════════════════════════════════════
Order │ Workflow              │ Dependencies
──────┼───────────────────────┼─────────────────────────────────
  7   │ Quote Create          │ Customer must exist
  8   │ Quote Line Items      │ Quote must exist
  9   │ Quote Total Calc      │ Line items must exist
 10   │ Job Create (basic)    │ Customer must exist
 11   │ Task CRUD             │ Job optional
 12   │ TimeLog Create        │ Employee must exist
 13   │ PayrollTransaction    │ Employee must exist

STAGE 3: Job Sub-entities
═══════════════════════════════════════════════════════════════
Order │ Workflow              │ Dependencies
──────┼───────────────────────┼─────────────────────────────────
 14   │ JobItem CRUD          │ Job must exist
 15   │ JobItem Total Calc    │ JobItem must exist
 16   │ Job Subtotal Recalc   │ JobItems must be calculable
 17   │ JobNote CRUD          │ Job must exist
 18   │ JobActivity Create    │ Job must exist

STAGE 4: Status & Activity Logging
═══════════════════════════════════════════════════════════════
Order │ Workflow              │ Dependencies
──────┼───────────────────────┼─────────────────────────────────
 19   │ Order Status Change     │ Job + JobActivity workflows
 20   │ Job Complete/Archive  │ Status change workflow
 21   │ Quote Status Change   │ Quote workflow

STAGE 5: Cross-Entity Operations (⚠️ Careful Order)
═══════════════════════════════════════════════════════════════
Order │ Workflow              │ Dependencies
──────┼───────────────────────┼─────────────────────────────────
 22   │ Quote→Job Conversion  │ Quote, Job, JobItem, JobActivity
      │                       │ all must work first
 23   │ Invoice Create        │ Customer must exist
 24   │ Invoice from Job      │ Job, JobItem, Invoice all ready
 25   │ Invoice Totals        │ InvoiceLineItems must work
 26   │ Invoice Status/Paid   │ Invoice workflows complete

STAGE 6: Time & Payroll Calculations
═══════════════════════════════════════════════════════════════
Order │ Workflow              │ Dependencies
──────┼───────────────────────┼─────────────────────────────────
 27   │ Clock Sequence Valid  │ TimeLog must work
 28   │ Shift Summary Calc    │ TimeLog query must work
 29   │ Payroll Balance Calc  │ PayrollTransaction must work
 30   │ Payroll Report        │ All payroll workflows

STAGE 7: Complex/Integration
═══════════════════════════════════════════════════════════════
Order │ Workflow              │ Dependencies
──────┼───────────────────────┼─────────────────────────────────
 31   │ Webstore Order        │ Customer, Job auto-creation
 32   │ AI Generation         │ API connector configured
 33   │ Financial Summaries   │ Sales/Expense entries work
 34   │ Dashboard Stats       │ All queries must work
```

---

## PART 4: CIRCULAR DEPENDENCIES

### Identified Circular Dependencies

#### 1. Quote ↔ Job (Bidirectional Reference)

```
┌─────────────────────────────────────────────────────────────┐
│                    CIRCULAR DEPENDENCY #1                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Quote                              Job                   │
│    ┌─────────┐                    ┌─────────┐              │
│    │         │                    │         │              │
│    │ job ────┼───────────────────►│   id    │              │
│    │         │                    │         │              │
│    │   id    │◄───────────────────┼── quote │              │
│    │         │                    │         │              │
│    └─────────┘                    └─────────┘              │
│                                                             │
│    Created when: Quote converted to Job                     │
│    Risk: Data inconsistency if one side updated without    │
│          the other                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Bubble Handling:**
```
WF-QUOTE-07: Convert Quote to Job
Step 1: Create Order (quote field = This Quote)
Step 2: Make changes to Quote (job field = Result of Step 1)
        ⚠️ Must use "Result of Step 1" not a search
```

**Fragility:**
- If Step 2 fails, Job exists without Quote back-reference
- No automatic rollback in Bubble
- Solution: Use API workflow with error handling, or accept eventual consistency

---

#### 2. Job ↔ Invoice (Bidirectional Reference)

```
┌─────────────────────────────────────────────────────────────┐
│                    CIRCULAR DEPENDENCY #2                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Job                                Invoice               │
│    ┌─────────┐                    ┌─────────┐              │
│    │         │                    │         │              │
│    │invoice ─┼───────────────────►│   id    │              │
│    │         │                    │         │              │
│    │   id    │◄───────────────────┼── job   │              │
│    │         │                    │         │              │
│    └─────────┘                    └─────────┘              │
│                                                             │
│    Created when: Invoice created from Job                   │
│    Risk: Same as Quote↔Job                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Bubble Handling:**
```
WF-INV-02: Create Invoice from Job
Step 1: Create Invoice (job field = This Job)
Step 2: Make changes to Job (invoice field = Result of Step 1)
```

---

#### 3. JobItem → Order.subtotal (Calculated Dependency)

```
┌─────────────────────────────────────────────────────────────┐
│                    CALCULATED DEPENDENCY                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    JobItem                            Job                   │
│    ┌─────────┐                    ┌─────────┐              │
│    │         │                    │         │              │
│    │ job ────┼───────────────────►│   id    │              │
│    │         │                    │         │              │
│    │line_total│                   │subtotal │◄─ SUM of     │
│    │         │                    │         │  all items   │
│    └─────────┘                    └─────────┘              │
│                                                             │
│    Trigger: Any JobItem create/update/delete               │
│    Risk: Subtotal out of sync if trigger fails             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Bubble Handling:**
```
Option A: Database Trigger (Recommended)
- Use "Do when condition is true" on page with job context
- Recalculate on any item change

Option B: Backend Workflow
- Schedule API workflow after item operations
- More reliable but adds latency

Option C: Real-time Calculation
- Don't store subtotal, calculate on display
- :each item's line_total:sum
- Performance impact on large item lists
```

---

### Circular Dependency Risk Matrix

| Dependency | Severity | Frequency | Mitigation |
|------------|----------|-----------|------------|
| Quote↔Job | Medium | Low (once per quote) | Two-step workflow, log failures |
| Job↔Invoice | Medium | Low (once per job) | Two-step workflow, log failures |
| JobItem→Order.subtotal | High | High (every item edit) | Real-time calc or reliable trigger |
| QuoteLineItem→Quote.total | High | High (every item edit) | Same as above |
| InvoiceLineItem→Invoice.total | High | High (every item edit) | Same as above |

---

## PART 5: FRAGILE DEPENDENCIES

### Fragile Dependency #1: Time Clock Sequence

```
┌─────────────────────────────────────────────────────────────┐
│              FRAGILE: TIME CLOCK SEQUENCE                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Sequence must be: start → [break_start → break_end]* → end
│                                                             │
│    Problem: No built-in state machine in Bubble             │
│                                                             │
│    Failure modes:                                           │
│    • Double start_work (data corruption)                    │
│    • end_work without start_work (negative hours)           │
│    • break_end without break_start (calculation error)      │
│                                                             │
│    Current protection: Query-based validation               │
│    Risk: Race condition if user double-clicks               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Mitigation Strategies:**

```
1. DISABLE BUTTONS (Frontend)
   - Query last action on page load
   - Conditionally show/enable only valid buttons
   - Re-query after each action

2. BACKEND VALIDATION (Workflow)
   - "Only when" condition on workflow
   - Search for last action, compare to valid transitions
   - Show alert if invalid

3. DEBOUNCE (Frontend)
   - Disable button immediately on click
   - Re-enable after workflow completes
   - Prevents double-click issues

4. AUDIT LOG (Recovery)
   - Store all attempts (valid and invalid)
   - Allow admin to fix corrupted data
```

---

### Fragile Dependency #2: Quote Conversion (One-Time Operation)

```
┌─────────────────────────────────────────────────────────────┐
│           FRAGILE: QUOTE → JOB CONVERSION                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Rule: Quote can only be converted ONCE                   │
│                                                             │
│    Problem: No transaction support in Bubble                │
│                                                             │
│    Failure modes:                                           │
│    • Job created but Quote not updated                      │
│    • JobItems partially created (some fail)                 │
│    • User clicks again → duplicate Job                      │
│                                                             │
│    Data state after partial failure:                        │
│    Quote: order_id = null (looks unconverted)                 │
│    Job: exists, orphaned                                    │
│    JobItems: partial set                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Mitigation Strategies:**

```
1. PRE-CHECK (Before Conversion)
   - Verify Quote.order_id is empty
   - If not empty, show "Already converted" message

2. IMMEDIATE UPDATE (During Conversion)
   - Step 1: Set Quote.status = "converting" (lock)
   - Step 2: Create Order
   - Step 3: Create OrderItems
   - Step 4: Set Quote.order_id
   - Step 5: Set Quote.status = "approved"

3. CLEANUP JOB (Scheduled)
   - Backend workflow runs hourly
   - Find Orders where quote.order_id ≠ this Job
   - Flag for admin review or auto-delete

4. UI PROTECTION
   - Hide convert button when Quote.order_id exists
   - Disable button during conversion
   - Show loading state
```

---

### Fragile Dependency #3: Calculated Totals Sync

```
┌─────────────────────────────────────────────────────────────┐
│           FRAGILE: CALCULATED TOTALS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Affected fields:                                         │
│    • Quote.total (from QuoteLineItems)                      │
│    • Order.subtotal (from JobItems)                           │
│    • Invoice.total (from InvoiceLineItems)                  │
│    • JobItem.line_total (qty × price)                       │
│                                                             │
│    Problem: Triggers can fail silently                      │
│                                                             │
│    Failure modes:                                           │
│    • Item added but parent not recalculated                 │
│    • Item deleted but total not decreased                   │
│    • Price changed but line_total not updated               │
│                                                             │
│    Result: Displayed totals don't match sum of items        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Mitigation Strategies:**

```
1. COMPUTE ON DISPLAY (No Storage)
   - Don't store totals, always calculate
   - Order.subtotal = Search JobItems where job = This:sum line_total
   - Pro: Always accurate
   - Con: Performance on lists

2. COMPUTE + CACHE (Hybrid)
   - Store calculated value for list views
   - Recalculate on detail view
   - Periodic reconciliation job

3. MULTI-STEP WORKFLOW (Reliable)
   - Item create → recalc total (same workflow)
   - Item update → recalc total (same workflow)
   - Item delete → recalc total (same workflow)
   - Never separate the operations

4. RECONCILIATION REPORT
   - Admin report showing mismatches
   - Stored total vs calculated total
   - One-click fix button
```

---

### Fragile Dependency #4: Invoice from Job (Data Copy)

```
┌─────────────────────────────────────────────────────────────┐
│           FRAGILE: INVOICE FROM JOB                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Operation: Copy JobItems → InvoiceLineItems              │
│                                                             │
│    Problem: Data is COPIED, not referenced                  │
│                                                             │
│    Failure modes:                                           │
│    • JobItem changed after invoice created                  │
│    • JobItem deleted after invoice created                  │
│    • Invoice line items now incorrect                       │
│                                                             │
│    Business question: Should invoice auto-update?           │
│    Usually NO - invoice is a point-in-time snapshot         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Design Decision:**

```
OPTION A: Snapshot (Recommended for Invoicing)
- Copy data at creation time
- Invoice is immutable record
- JobItem.job_item_id kept for reference only
- Changes to Job don't affect sent invoices

OPTION B: Live Reference
- InvoiceLineItem just references JobItem
- Invoice always shows current Job state
- Problematic for accounting/auditing

IMPLEMENTATION:
- Once invoice status = "sent", block JobItem edits
- Or: Allow edits but show warning "Invoice already created"
- Or: Create new invoice version on Job changes
```

---

### Fragile Dependency #5: Webstore Auto-Creation

```
┌─────────────────────────────────────────────────────────────┐
│           FRAGILE: WEBSTORE ORDER → AUTO JOB                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    Operation: WebstoreOrder creates Customer + Job          │
│                                                             │
│    Problem: Three things created in one workflow            │
│                                                             │
│    Failure modes:                                           │
│    • Customer created, Job fails                            │
│    • Job created, Order fails                               │
│    • Order created, no link to Job                          │
│                                                             │
│    Result: Orphaned records, missing orders                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Mitigation:**

```
1. ATOMIC WORKFLOW (API Workflow)
   - Use backend API workflow
   - All steps in one server-side operation
   - Better error handling

2. FIND-OR-CREATE PATTERN
   - Step 1: Search for Customer with webstore marker
   - Step 2: If empty, create; else use existing
   - Step 3: Create Order
   - Step 4: Create Order with Job reference

3. STATUS TRACKING
   - Order has status: pending_customer, pending_job, complete
   - Retry failed steps based on status
   - Admin dashboard for stuck orders
```

---

## PART 6: RECOMMENDED SAFEGUARDS

### Safeguard Patterns for Bubble

#### 1. Two-Phase Commit Pattern

```
For circular references (Quote↔Job):

Phase 1: Create child, reference parent
- Create Order with quote = This Quote
- Job now exists and references Quote

Phase 2: Update parent with child reference  
- Make changes to Quote: job = Result of Step 1
- Use "Result of Step X" to avoid race conditions
```

#### 2. Optimistic Locking Pattern

```
For one-time operations (Quote conversion):

Before operation:
- Check Quote.order_id is empty
- Check Quote.status ≠ "converting"

During operation:
- Set Quote.status = "converting" (lock)
- Perform multi-step operation
- Set Quote.status = "approved" (unlock)

If user retries:
- Status = "converting" blocks retry
- Or: order_id exists blocks retry
```

#### 3. Computed Field Pattern

```
For calculated totals:

Option A: Always Compute
- Never store totals
- Calculate in expressions: :sum, :count
- Accept performance cost

Option B: Compute + Store  
- Calculate in workflow
- Store result
- Recalculate on every related change
- Validate periodically

Option C: Lazy Compute
- Store stale value with timestamp
- Recalculate if accessed and stale > X minutes
- Background reconciliation
```

#### 4. Idempotent Workflow Pattern

```
For operations that might retry (network issues):

Before creating:
- Search for existing record with same unique key
- If found, return existing (don't duplicate)

Example for Clock Action:
- Search TimeLogs: employee + action + timestamp within 1 minute
- If found, return existing
- If not, create new
```

---

## PART 7: DEPENDENCY VALIDATION CHECKLIST

### Pre-Launch Validation

```
DATA INTEGRITY CHECKS
═══════════════════════════════════════════════════════════════
□ All Quotes with order_id have corresponding Job with quote_id
□ All Orders with invoice_id have corresponding Invoice with order_id
□ All JobItems have valid job reference
□ All InvoiceLineItems with job_item_id have valid JobItem
□ No orphaned JobNotes or JobActivities (job exists)

CALCULATED FIELD CHECKS
═══════════════════════════════════════════════════════════════
□ Quote.total = SUM(QuoteLineItems.total) for all Quotes
□ Order.subtotal = SUM(JobItems.line_total) for all Orders
□ Invoice.total = SUM(InvoiceLineItems.total) for all Invoices
□ JobItem.line_total = quantity × unit_price for all items

SEQUENCE CHECKS
═══════════════════════════════════════════════════════════════
□ No Quote with status="approved" and empty order_id
□ No Job with quote_id pointing to Quote with different order_id
□ TimeLogs follow valid sequence per employee per day

REFERENTIAL INTEGRITY
═══════════════════════════════════════════════════════════════
□ All customer_id references point to existing Customer
□ All employee_id references point to existing Employee
□ All order_id references point to existing Job
```

### Monitoring Queries (Run Daily)

```
ORPHAN DETECTION
════════════════
Orders without valid Customer:
  Search Orders where customer is empty

Quotes without valid Customer:
  Search Quotes where customer is empty

JobItems without valid Job:
  Search JobItems where job is empty

MISMATCH DETECTION
══════════════════
Quote-Job mismatch:
  Search Quotes where job's quote ≠ This Quote

Job-Invoice mismatch:
  Search Orders where invoice's job ≠ This Job

CALCULATION MISMATCH
════════════════════
Orders with wrong subtotal:
  (Requires custom logic to compare stored vs calculated)
```

---

## SUMMARY: CRITICAL DEPENDENCIES

### Must Implement Carefully

| Dependency | Risk Level | Recommendation |
|------------|------------|----------------|
| Quote → Job conversion | 🔴 High | Two-phase commit + lock |
| Job → Invoice creation | 🔴 High | Two-phase commit + lock |
| JobItem → Order.subtotal | 🔴 High | Same-workflow recalc |
| Time clock sequence | 🟡 Medium | UI disable + backend validate |
| Webstore auto-creation | 🟡 Medium | API workflow + retry logic |

### Safe to Implement Simply

| Dependency | Risk Level | Notes |
|------------|------------|-------|
| Customer → Quote/Job/Invoice | 🟢 Low | Standard parent-child |
| Employee → TimeLog/Payroll | 🟢 Low | Standard parent-child |
| Job → JobNote/JobActivity | 🟢 Low | One-way reference |
| Task → Job (optional) | 🟢 Low | Optional reference |
