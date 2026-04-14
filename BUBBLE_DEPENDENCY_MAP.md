# Sign Guy AI - Dependency & Execution Order Map (Current)

> Last updated: Feb 2026. Reflects multi-tenant architecture, Object Storage, Unified Productivity, Payroll Worksheet, and Signature/Drawing subsystems.

---

## PART 1: DATA TYPE DEPENDENCIES

### Dependency Graph

```
LEVEL 0 (No Dependencies - Foundation)
┌──────────┐     ┌──────────┐
│  Tenant  │     │(External)│
│          │     │ Object   │
│          │     │ Storage  │
└────┬─────┘     └──────────┘
     │ owns all
     ▼
LEVEL 1 (Depend on Tenant only)
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Customer │  │   User   │  │ Employee │  │Workflow  │
│          │  │          │  │          │  │Template  │
└────┬─────┘  └──────────┘  └────┬─────┘  └──────────┘
     │                           │
     ▼                           ▼
LEVEL 2 (Single Parent)
┌──────┐ ┌──────┐ ┌────────┐  ┌────────────┐ ┌──────────┐ ┌──────────┐
│Quote │ │Order │ │Invoice │  │Timeclock   │ │Payroll   │ │Employee  │
│      │ │      │ │        │  │Shift       │ │Trans.    │ │Schedule  │
│->Cust│ │->Cust│ │->Cust  │  │->Employee  │ │->Employee│ │->Employee│
└──┬───┘ └──┬───┘ └────────┘  └────────────┘ └──────────┘ └──────────┘
   │        │
   ▼        ▼
LEVEL 3 (Nested Dependencies)
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│JobTicket│ │OrderNote│ │ Order   │ │ Order   │ │Signature │
│->Order │ │->Order │ │Activity │ │Drawing  │ │->Order   │
│        │ │        │ │->Order  │ │->Order  │ │->Record  │
└────────┘ └────────┘ └──────────┘ │+ObjStore│ │+ObjStore │
                                   └──────────┘ └──────────┘

LEVEL 4 (Cross-Entity / Calculated)
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Payroll Signoff│ │Payroll Hours │ │Production    │
│->Employee    │ │(Legacy)      │ │Task          │
│->Date Range  │ │->Employee    │ │->JobTicket   │
└──────────────┘ └──────────────┘ └──────────────┘

BIDIRECTIONAL REFERENCES
┌──────┐ ◄─── order_id / quote_id ───► ┌──────┐
│Quote │                                │Order │
└──────┘                                └──┬───┘
                                           │
┌──────┐ ◄─── invoice_id / order_id ──► ┌──┴───┐
│Order │                                │Invoice│
└──────┘                                └──────┘
```

### Dependency Matrix

| Data Type | Depends On | Depended By | Circular? |
|-----------|------------|-------------|-----------|
| Tenant | - | All collections | No |
| User | Tenant | - | No |
| Customer | Tenant | Quote, Order, Invoice, Conversation, Appointment | No |
| Employee | Tenant | TimeclockShift, TimeLog, PayrollTransaction, PayrollSignoff, PayrollHours, EmployeeSchedule, ProductionTask | No |
| Quote | Customer, Tenant | Order (via conversion) | Yes (Quote<->Order) |
| Order | Customer, Tenant | JobTicket, OrderNote, OrderActivity, OrderDrawing, Signature, Invoice, Task | Yes (Order<->Quote, Order<->Invoice) |
| JobTicket | Order | ProductionTask, InvoiceLineItem | No |
| OrderDrawing | Order, Object Storage | - | No |
| Signature | Order (opt), Object Storage | - | No |
| TimeclockShift | Employee, Tenant | Payroll Worksheet (read) | No |
| PayrollTransaction | Employee, Tenant | Payroll Worksheet (read) | No |
| PayrollSignoff | Employee, Tenant | Payroll Worksheet (lock) | No |
| PayrollHours | Employee, Tenant | Payroll Worksheet (legacy) | No |
| Invoice | Customer, Order (opt) | - | Yes (Invoice<->Order) |
| Task | Tenant, Order (opt), Employee (opt) | Productivity Layer (read) | No |
| ProductionTask | JobTicket, Employee (opt) | Productivity Layer (read) | No |
| WorkflowTemplate | Tenant | JobTicket (reference) | No |
| AIResponse | Tenant, Order (opt), Customer (opt) | - | No |
| FundraiserCampaign | Tenant | WebstoreOrder | No |
| B2BStore | Tenant | WebstoreOrder | No |
| WebstoreOrder | Order (auto-created), Store | - | No |

---

## PART 2: WORKFLOW DEPENDENCIES

### Independent Workflows (No Prerequisites)
```
- Customer CRUD (WF-CUST-*)
- Employee CRUD
- Sales/Expense Entry (WF-FIN-01, WF-FIN-02)
- Fundraiser/B2B Store CRUD
- Workflow Template CRUD
- Tenant Settings Update
```

### Level 1 (Require Foundation Data)
```
Customer exists ->
  ├── WF-QUOTE-01 (Create Quote)
  ├── WF-JOB-01 (Create Order)
  └── WF-INV-01 (Create Invoice)

Employee exists ->
  ├── WF-TIME-01 (Clock Action)
  ├── WF-PAY-01 (Create Payroll Transaction)
  └── Schedule CRUD
```

### Level 2 (Require Level 1 Data)
```
Quote exists ->
  ├── WF-QUOTE-02 (Update)
  └── WF-QUOTE-07 (Convert to Order)
       ├── Creates: Order
       ├── Creates: JobTickets[]
       ├── Creates: OrderActivity
       └── Updates: Quote.order_id (circular)

Order exists ->
  ├── WF-JOBITEM-01 (Add Ticket)
  ├── WF-JOBNOTE-01 (Add Note)
  ├── WF-DRAW-01 (Create Drawing) + Object Storage
  ├── WF-SIG-01 (Create Signature Requirement)
  ├── WF-INV-02 (Create Invoice from Order)
  └── WF-TASK-01 (Create Task, optional order link)
```

### Level 3 (Calculations & Aggregation)
```
JobTicket changed -> WF-JOBITEM-RECALC (Order.subtotal)
TimeclockShift exists -> WF-TIME-02 (Backfill), WF-PAY-WORKSHEET (Payroll load)
PayrollTransaction exists -> WF-PAY-03 (Balance calc)
Multiple source types -> WF-PROD-01 (Unified Productivity aggregation)
```

### Complex Workflows (Multiple Dependencies)

```
WF-PAY-WORKSHEET: Load Payroll Worksheet
├── Requires: Employee
├── Requires: Tenant.payroll_settings (cycle, start day)
├── Reads: timeclock_shifts (or backfills from timelogs)
├── Reads: payroll_transactions
├── Reads: payroll_hours (legacy)
├── Reads: payroll_signoffs
└── Frontend builds editable spreadsheet

WF-PAY-SAVE: Save Worksheet
├── Creates/Updates: timeclock_shifts (per modified day row)
├── Creates/Updates/Deletes: payroll_transactions (adjustments)
├── Frontend clears "unsaved changes" badge
└── Reads: refreshed data from server

WF-SIG-02: Request Signature via Email
├── Requires: Signature requirement (WF-SIG-01)
├── Creates: request_token with expiry
├── Sends: Email with public link
└── Public page: WF-SIG-04 (capture without auth)

WF-PROD-01: Unified Productivity
├── Reads: tasks (WF-TASK)
├── Reads: orders (order status as board items)
├── Reads: job_tickets (ticket status)
├── Reads: production_tasks
├── Reads: employee_schedules
├── Reads: appointments
├── Normalizes all into ProductivityItem[]
└── Serves: Dashboard, List, Calendar, Kanban views
```

---

## PART 3: EXECUTION ORDER

### Data Type Creation Order
```
Phase 1: Foundation
  1. Tenant
  2. All Enums/Option Sets

Phase 2: Core Entities
  3. User (needs Tenant)
  4. Customer (needs Tenant)
  5. Employee (needs Tenant)
  6. WorkflowTemplate (needs Tenant)

Phase 3: Business Objects
  7. Quote (needs Customer)
  8. Order (needs Customer)
  9. Task (optional Order/Employee)

Phase 4: Order Children
  10. JobTicket (needs Order)
  11. OrderNote (needs Order)
  12. OrderActivity (needs Order)
  13. OrderDrawing (needs Order + Object Storage)
  14. Signature (needs Order or record + Object Storage)

Phase 5: Time & Payroll
  15. TimeLog (needs Employee)
  16. TimeclockShift (needs Employee)
  17. PayrollTransaction (needs Employee)
  18. PayrollHours (needs Employee)
  19. PayrollSignoff (needs Employee)
  20. EmployeeSchedule (needs Employee)

Phase 6: Cross-References
  21. Invoice (needs Customer, optional Order)
  22. ProductionTask (needs JobTicket)
  23. WebstoreOrder (auto-creates Order)
  24. Quote.order_id <-> Order.quote_id (circular)
  25. Order.invoice_id <-> Invoice.order_id (circular)

Phase 7: Aggregation Layers
  26. Unified Productivity (reads all source types)
  27. Dashboard Stats (reads all counts)
  28. Payroll Worksheet (reads shifts + transactions + hours)
```

---

## PART 4: CIRCULAR DEPENDENCIES

### 1. Quote <-> Order
**Created when:** Quote converted to Order
**Handling:** Two-step workflow - create Order first, then update Quote.order_id
**Risk:** Medium. If step 2 fails, Order exists without Quote back-reference.

### 2. Order <-> Invoice
**Created when:** Invoice created from Order
**Handling:** Two-step - create Invoice, then update Order.invoice_id
**Risk:** Medium.

### 3. JobTicket -> Order.subtotal (Calculated)
**Trigger:** Any JobTicket add/update/delete
**Handling:** Same-workflow recalculation (never separate the operations)
**Risk:** High if triggers fail silently.

---

## PART 5: KEY FRAGILE DEPENDENCIES

### 1. Time Clock Sequence
**Rule:** `start_work -> [break_start -> break_end]* -> end_work`
**Protection:** UI disables invalid buttons + backend validation
**Risk:** Medium. Debounce prevents double-click.

### 2. Payroll Worksheet State
**Rule:** All changes are local until Save. Export/Print blocked while unsaved.
**Protection:** "Unsaved changes" badge tracks dirty state via JSON snapshot comparison
**Risk:** Low. Explicit save-before-export enforcement.

### 3. Object Storage for Drawings/Signatures
**Rule:** Binary data stored externally, MongoDB holds only `storage_key`
**Protection:** Presigned URLs generated on read, cached in `storage_url`
**Risk:** Low. Storage service availability.

### 4. Legacy Manual Entries
**Rule:** Older `payroll_hours` entries outside current period surfaced with resolution UI
**Protection:** Admin explicitly chooses: keep/exclude/convert. Default is "keep_legacy" (non-destructive).
**Risk:** Low. No automatic data deletion.

### 5. Unified Productivity Compound UIDs
**Rule:** `uid = "{source_type}:{id}"` or `"{source_type}:{id}:{day}"` for schedule shifts
**Protection:** Backend parser handles both formats
**Risk:** Medium. Malformed UIDs rejected with 400 error.

---

## PART 6: EXTERNAL SERVICE DEPENDENCIES

| Service | Used For | Collections Affected |
|---------|----------|---------------------|
| Emergent Object Storage | Drawings, Signatures, Files, Logos | order_drawings, signatures, order_files, tenants, employees |
| OpenAI GPT-5.2 (Emergent LLM Key) | AI Tools, AI Assistant | ai_responses |
| OpenAI Whisper (Emergent LLM Key) | Speech-to-Text | ai_responses |
| OpenAI TTS (Emergent LLM Key) | Text-to-Speech | - |
| Stripe | Subscription billing, Connect payouts | tenants, invoices |
| Email Service | Signature requests, Portal invites, Digests | signatures, employees |

---

## PART 7: VALIDATION CHECKLIST

### Data Integrity
```
[ ] All records have tenant_id (except timelogs - legacy)
[ ] Quote.order_id <-> Order.quote_id consistency
[ ] Order.invoice_id <-> Invoice.order_id consistency
[ ] All JobTickets reference valid Order
[ ] All OrderDrawings reference valid Order
[ ] All Signatures have valid parent_record_type
[ ] Employee.linked_user_id references valid User (if set)
```

### Calculated Fields
```
[ ] Quote.total = SUM(line_items[].total)
[ ] Order.subtotal = SUM(job_tickets[].line_total)
[ ] Invoice.total = SUM(line_items[].total)
[ ] TimeclockShift.total_hours matches clock_in/clock_out minus break_minutes
[ ] PayrollBalance = earnings - advances - payments
```

### Object Storage
```
[ ] All order_drawings with storage_key are retrievable
[ ] All signatures with storage_key are retrievable
[ ] Presigned URLs regenerate on expiry
```

---

## SUMMARY: CRITICAL DEPENDENCIES

### Must Implement Carefully
| Dependency | Risk | Recommendation |
|------------|------|----------------|
| Quote -> Order conversion | High | Two-phase commit + lock |
| Order -> Invoice creation | High | Two-phase commit + lock |
| JobTicket -> Order.subtotal | High | Same-workflow recalc |
| Payroll Worksheet save | Medium | Atomic batch per employee |
| Object Storage upload | Medium | Upload before DB insert |
| Productivity UID parsing | Medium | Strict format validation |

### Safe to Implement Simply
| Dependency | Risk | Notes |
|------------|------|-------|
| Customer -> Quote/Order/Invoice | Low | Standard parent-child |
| Employee -> TimeclockShift/PayrollTxn | Low | Standard parent-child |
| Order -> OrderNote/Activity | Low | One-way reference |
| Task -> Order (optional) | Low | Optional reference |
| Tenant -> All collections | Low | Filter in every query |
