# Sign Guy AI - Workflows Documentation

## CUSTOMER WORKFLOWS

---

### WF-CUST-01: Create Customer

**Trigger:** User submits new customer form

**Conditions:** None

**Actions:**
1. Generate new UUID for `id`
2. Set `created_at` = current timestamp (ISO 8601)
3. Set `updated_at` = current timestamp (ISO 8601)
4. Set `status` = "lead" (if not provided)
5. Set optional fields to empty/null if not provided: `company`, `phone`, `email`, `notes`

**Data Changes:**
```
INSERT INTO customers:
{
  id: generated UUID,
  name: input.name,
  company: input.company || null,
  phone: input.phone || null,
  email: input.email || null,
  status: input.status || "lead",
  notes: input.notes || null,
  created_at: NOW(),
  updated_at: NOW()
}
```

**Returns:** Created Customer object

---

### WF-CUST-02: Update Customer

**Trigger:** User submits customer edit form

**Conditions:** Customer with `customer_id` must exist

**Actions:**
1. Find customer by `id`
2. If not found → ERROR 404 "Customer not found"
3. Update only fields that are provided (non-null)
4. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE customers WHERE id = customer_id:
SET {
  ...only_provided_fields,
  updated_at: NOW()
}
```

**Returns:** Updated Customer object

---

### WF-CUST-03: Delete Customer

**Trigger:** User clicks delete customer

**Conditions:** Customer with `customer_id` must exist

**Actions:**
1. Delete customer record
2. If no record deleted → ERROR 404 "Customer not found"

**Data Changes:**
```
DELETE FROM customers WHERE id = customer_id
```

**Returns:** `{ message: "Customer deleted" }`

---

### WF-CUST-04: Search/Filter Customers

**Trigger:** User applies search or filter

**Conditions:** None

**Actions:**
1. Build query based on filters:
   - If `status` provided → filter by status
   - If `search` provided → search in name, company, email (case-insensitive)
2. Execute query

**Data Changes:** None (read-only)

**Returns:** List of matching Customer objects

---

## QUOTE WORKFLOWS

---

### WF-QUOTE-01: Create Quote

**Trigger:** User submits new quote form

**Conditions:** 
- `customer_id` must be provided
- Customer must exist

**Actions:**
1. Generate new UUID for `id`
2. Set `created_at` = current timestamp
3. Set `updated_at` = current timestamp
4. Set `status` = "draft" (if not provided)
5. Set `job_id` = null (not yet converted)
6. **FOR EACH line_item in input.line_items:**
   - Calculate `item.total` = `item.quantity` × `item.unit_price`
7. Calculate `total` = SUM of all `line_items[].total`

**Data Changes:**
```
INSERT INTO quotes:
{
  id: generated UUID,
  customer_id: input.customer_id,
  line_items: [
    {
      description: item.description,
      quantity: item.quantity,
      unit_price: item.unit_price,
      total: item.quantity × item.unit_price  // CALCULATED
    },
    ...
  ],
  notes: input.notes || null,
  status: input.status || "draft",
  total: SUM(line_items[].total),  // CALCULATED
  job_id: null,
  created_at: NOW(),
  updated_at: NOW()
}
```

**Returns:** Created Quote object with calculated totals

---

### WF-QUOTE-02: Update Quote

**Trigger:** User submits quote edit form

**Conditions:**
- Quote with `quote_id` must exist
- Quote must NOT have `job_id` set (not yet converted)

**Actions:**
1. Find quote by `id`
2. If not found → ERROR 404 "Quote not found"
3. If `job_id` exists → ERROR 400 "Cannot update quote that has been converted to job"
4. Update only fields that are provided
5. **IF `line_items` changed:**
   - FOR EACH line_item:
     - Recalculate `item.total` = `item.quantity` × `item.unit_price`
   - Recalculate `total` = SUM of all `line_items[].total`
6. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE quotes WHERE id = quote_id:
SET {
  line_items: [recalculated items],  // if provided
  total: recalculated_total,         // if line_items changed
  notes: input.notes,                // if provided
  status: input.status,              // if provided
  updated_at: NOW()
}
```

**Returns:** Updated Quote object

---

### WF-QUOTE-03: Quote Status Change

**Trigger:** User changes quote status dropdown

**Conditions:** Quote must exist and not be converted to job

**Actions:**
1. Validate new status is valid enum value: draft, sent, approved, declined
2. Update status field
3. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE quotes WHERE id = quote_id:
SET {
  status: new_status,
  updated_at: NOW()
}
```

**Returns:** Updated Quote object

**Status Flow:**
```
draft → sent → approved
              ↘ declined
```

---

### WF-QUOTE-04: Add Line Item to Quote

**Trigger:** User clicks "Add Line Item" on quote form

**Conditions:** Quote must exist and not be converted

**Actions:**
1. Create new line item object
2. Calculate `item.total` = `quantity` × `unit_price`
3. Append to `line_items` array
4. Recalculate quote `total`
5. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE quotes WHERE id = quote_id:
PUSH to line_items: {
  description: input.description,
  quantity: input.quantity,
  unit_price: input.unit_price,
  total: input.quantity × input.unit_price
}
SET total = SUM(line_items[].total)
SET updated_at = NOW()
```

**Returns:** Updated Quote object

---

### WF-QUOTE-05: Edit Line Item on Quote

**Trigger:** User edits existing line item

**Conditions:** Quote must exist and not be converted

**Actions:**
1. Find line item by index in array
2. Update line item fields
3. Recalculate `item.total` = `quantity` × `unit_price`
4. Recalculate quote `total`
5. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE quotes WHERE id = quote_id:
SET line_items[index] = {
  description: input.description,
  quantity: input.quantity,
  unit_price: input.unit_price,
  total: input.quantity × input.unit_price
}
SET total = SUM(line_items[].total)
SET updated_at = NOW()
```

**Returns:** Updated Quote object

---

### WF-QUOTE-06: Delete Line Item from Quote

**Trigger:** User clicks delete on line item

**Conditions:** Quote must exist and not be converted

**Actions:**
1. Remove line item from array by index
2. Recalculate quote `total`
3. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE quotes WHERE id = quote_id:
PULL from line_items at index
SET total = SUM(line_items[].total)
SET updated_at = NOW()
```

**Returns:** Updated Quote object

---

### WF-QUOTE-07: Convert Quote to Job

**Trigger:** User clicks "Convert to Job" button

**Conditions:**
- Quote with `quote_id` must exist
- Quote must NOT have `job_id` set (not already converted)

**Actions:**
1. Find quote by `id`
2. If not found → ERROR 404 "Quote not found"
3. If `job_id` exists → ERROR 400 "Quote already converted to job"
4. **CREATE NEW JOB:**
   - Generate new UUID for job `id`
   - Set `customer_id` = quote's `customer_id`
   - Set `name` = "Job from Quote #{quote_id first 8 chars}"
   - Set `description` = quote's `notes`
   - Set `status` = "approved"
   - Set `quote_id` = quote's `id`
   - Set `subtotal` = quote's `total`
   - Set `invoice_id` = null
   - Set `is_archived` = false
   - Set `created_at` = current timestamp
   - Set `updated_at` = current timestamp
5. **FOR EACH line_item in quote.line_items → CREATE JOB ITEM:**
   - Generate new UUID for job item `id`
   - Set `job_id` = new job's `id`
   - Set `item_type` = "other"
   - Set `description` = line_item's `description`
   - Set `quantity` = line_item's `quantity`
   - Set `unit_price` = line_item's `unit_price`
   - Set `line_total` = line_item's `total`
   - Set `status` = "pending"
   - Set `notes` = null
   - Set `created_at` = current timestamp
6. **UPDATE QUOTE:**
   - Set `job_id` = new job's `id`
   - Set `status` = "approved"
7. **LOG ACTIVITY:**
   - Create JobActivity record for "quote_converted"

**Data Changes:**
```
INSERT INTO jobs:
{
  id: generated UUID,
  customer_id: quote.customer_id,
  name: "Job from Quote #" + quote_id.substring(0,8),
  description: quote.notes,
  status: "approved",
  due_date: null,
  quote_id: quote.id,
  invoice_id: null,
  subtotal: quote.total,
  is_archived: false,
  created_at: NOW(),
  updated_at: NOW()
}

FOR EACH quote.line_items:
INSERT INTO job_items:
{
  id: generated UUID,
  job_id: new_job.id,
  item_type: "other",
  description: line_item.description,
  quantity: line_item.quantity,
  unit_price: line_item.unit_price,
  line_total: line_item.total,
  status: "pending",
  notes: null,
  created_at: NOW()
}

UPDATE quotes WHERE id = quote_id:
SET {
  job_id: new_job.id,
  status: "approved"
}

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: new_job.id,
  activity_type: "quote_converted",
  description: "Job created from Quote #" + quote_id.substring(0,8),
  old_value: null,
  new_value: quote_id,
  created_at: NOW()
}
```

**Returns:** Created Job object

---

## JOB WORKFLOWS

---

### WF-JOB-01: Create Job (Direct)

**Trigger:** User submits new job form (not from quote conversion)

**Conditions:** `customer_id` must be provided

**Actions:**
1. Generate new UUID for `id`
2. Set `created_at` = current timestamp
3. Set `updated_at` = current timestamp
4. Set `status` = "quoted" (if not provided)
5. Set `subtotal` = 0 (no items yet)
6. Set `quote_id` = input.quote_id (if provided, else null)
7. Set `invoice_id` = null
8. Set `is_archived` = false
9. **LOG ACTIVITY:** Create "created" activity record

**Data Changes:**
```
INSERT INTO jobs:
{
  id: generated UUID,
  customer_id: input.customer_id,
  name: input.name,
  description: input.description || null,
  status: input.status || "quoted",
  due_date: input.due_date || null,
  quote_id: input.quote_id || null,
  invoice_id: null,
  subtotal: 0,
  is_archived: false,
  created_at: NOW(),
  updated_at: NOW()
}

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: new_job.id,
  activity_type: "created",
  description: "Job '" + input.name + "' created",
  old_value: null,
  new_value: null,
  created_at: NOW()
}
```

**Returns:** Created Job object

---

### WF-JOB-02: Update Job

**Trigger:** User submits job edit form

**Conditions:** Job with `job_id` must exist

**Actions:**
1. Find job by `id`
2. If not found → ERROR 404 "Job not found"
3. Update only fields that are provided
4. **IF status changed:**
   - Log appropriate activity (status_changed, completed, or archived)
5. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE jobs WHERE id = job_id:
SET {
  name: input.name,           // if provided
  description: input.description,  // if provided
  status: input.status,       // if provided
  due_date: input.due_date,   // if provided
  updated_at: NOW()
}

IF status changed:
INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "status_changed" | "completed" | "archived",
  description: "Status changed from {old} to {new}",
  old_value: old_status,
  new_value: new_status,
  created_at: NOW()
}
```

**Returns:** Updated Job object

---

### WF-JOB-03: Job Status Change

**Trigger:** User changes job status

**Conditions:** Job must exist

**Actions:**
1. Find job by `id`
2. Determine activity type based on new status:
   - If new status = "complete" → activity_type = "completed"
   - If new status = "archived" → activity_type = "archived"
   - Otherwise → activity_type = "status_changed"
3. Update status
4. Log activity
5. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE jobs WHERE id = job_id:
SET {
  status: new_status,
  updated_at: NOW()
}

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: determined_type,
  description: based_on_type,
  old_value: old_status,
  new_value: new_status,
  created_at: NOW()
}
```

**Status Flow:**
```
quoted → approved → in_production → installed → complete → archived
                                              ↗
                            (can skip to complete from any active status)
```

**Returns:** Updated Job object

---

### WF-JOB-04: Mark Job Complete

**Trigger:** User clicks "Mark Complete" button

**Conditions:** Job must exist

**Actions:**
1. Find job by `id`
2. If not found → ERROR 404 "Job not found"
3. Set `status` = "complete"
4. Log "completed" activity
5. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE jobs WHERE id = job_id:
SET {
  status: "complete",
  updated_at: NOW()
}

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "completed",
  description: "Job marked as complete",
  old_value: previous_status,
  new_value: "complete",
  created_at: NOW()
}
```

**Returns:** `{ message: "Job marked as complete" }`

---

### WF-JOB-05: Archive Job

**Trigger:** User clicks "Archive" button

**Conditions:** Job must exist

**Actions:**
1. Find job by `id`
2. If not found → ERROR 404 "Job not found"
3. Set `status` = "archived"
4. Set `is_archived` = true
5. Log "archived" activity
6. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE jobs WHERE id = job_id:
SET {
  status: "archived",
  is_archived: true,
  updated_at: NOW()
}

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "archived",
  description: "Job archived",
  old_value: previous_status,
  new_value: "archived",
  created_at: NOW()
}
```

**Returns:** `{ message: "Job archived" }`

---

### WF-JOB-06: Unarchive Job

**Trigger:** User clicks "Unarchive" button

**Conditions:** Job must exist

**Actions:**
1. Find job by `id`
2. If not found → ERROR 404 "Job not found"
3. Set `status` = "complete"
4. Set `is_archived` = false
5. Log "unarchived" activity
6. Set `updated_at` = current timestamp

**Data Changes:**
```
UPDATE jobs WHERE id = job_id:
SET {
  status: "complete",
  is_archived: false,
  updated_at: NOW()
}

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "unarchived",
  description: "Job unarchived",
  old_value: "archived",
  new_value: "complete",
  created_at: NOW()
}
```

**Returns:** `{ message: "Job unarchived" }`

---

### WF-JOB-07: Delete Job

**Trigger:** User confirms job deletion

**Conditions:** Job must exist

**Actions:**
1. Delete all related job_items WHERE job_id = job_id
2. Delete all related job_notes WHERE job_id = job_id
3. Delete all related job_activities WHERE job_id = job_id
4. Delete job record
5. If no record deleted → ERROR 404 "Job not found"

**Data Changes:**
```
DELETE FROM job_items WHERE job_id = job_id
DELETE FROM job_notes WHERE job_id = job_id
DELETE FROM job_activities WHERE job_id = job_id
DELETE FROM jobs WHERE id = job_id
```

**Returns:** `{ message: "Job deleted" }`

---

### WF-JOB-08: Filter Jobs

**Trigger:** User applies job filter

**Conditions:** None

**Actions:**
1. Build query based on filter_type:
   - "active" → status NOT IN ["complete", "archived"] AND is_archived != true
   - "completed" → status = "complete" AND is_archived != true
   - "archived" → is_archived = true OR status = "archived"
   - specific status → status = provided_status
2. Optionally filter by customer_id
3. Sort by created_at descending

**Data Changes:** None (read-only)

**Returns:** List of matching Job objects

---

## JOB ITEM WORKFLOWS

---

### WF-JOBITEM-01: Add Job Item

**Trigger:** User submits "Add Item" form on job

**Conditions:** Job with `job_id` must exist

**Actions:**
1. Find job by `id`
2. If not found → ERROR 404 "Job not found"
3. Generate new UUID for job item `id`
4. **CALCULATE:** `line_total` = `quantity` × `unit_price`
5. Insert job item record
6. **RECALCULATE JOB SUBTOTAL:** (see WF-JOBITEM-RECALC)
7. **LOG ACTIVITY:** Create "item_added" activity
8. Set job item `created_at` = current timestamp

**Data Changes:**
```
INSERT INTO job_items:
{
  id: generated UUID,
  job_id: job_id,
  item_type: input.item_type || "other",
  description: input.description,
  quantity: input.quantity || 1,
  unit_price: input.unit_price || 0,
  line_total: input.quantity × input.unit_price,  // CALCULATED
  status: input.status || "pending",
  notes: input.notes || null,
  created_at: NOW()
}

// Then recalculate job subtotal (WF-JOBITEM-RECALC)

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "item_added",
  description: "Added item: " + input.description,
  old_value: null,
  new_value: null,
  created_at: NOW()
}
```

**Returns:** Created JobItem object

---

### WF-JOBITEM-02: Update Job Item

**Trigger:** User submits job item edit form

**Conditions:** JobItem with `item_id` must exist

**Actions:**
1. Find job item by `id`
2. If not found → ERROR 404 "Job item not found"
3. Update only fields that are provided
4. **RECALCULATE:** `line_total` = `quantity` × `unit_price`
   - Use new values if provided, else existing values
5. Update job item record
6. **RECALCULATE JOB SUBTOTAL:** (see WF-JOBITEM-RECALC)
7. **LOG ACTIVITY:** Create "item_updated" activity

**Data Changes:**
```
// Get current values for calculation
current_quantity = input.quantity ?? job_item.quantity
current_unit_price = input.unit_price ?? job_item.unit_price

UPDATE job_items WHERE id = item_id:
SET {
  item_type: input.item_type,      // if provided
  description: input.description,  // if provided
  quantity: input.quantity,        // if provided
  unit_price: input.unit_price,    // if provided
  line_total: current_quantity × current_unit_price,  // ALWAYS RECALCULATE
  status: input.status,            // if provided
  notes: input.notes               // if provided
}

// Then recalculate job subtotal (WF-JOBITEM-RECALC)

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_item.job_id,
  activity_type: "item_updated",
  description: "Updated item: " + job_item.description,
  old_value: null,
  new_value: null,
  created_at: NOW()
}
```

**Returns:** Updated JobItem object

---

### WF-JOBITEM-03: Delete Job Item

**Trigger:** User clicks delete on job item

**Conditions:** JobItem with `item_id` must exist

**Actions:**
1. Find job item by `id`
2. If not found → ERROR 404 "Job item not found"
3. Store `job_id` for subtotal recalculation
4. Delete job item record
5. **RECALCULATE JOB SUBTOTAL:** (see WF-JOBITEM-RECALC)
6. **LOG ACTIVITY:** Create "item_deleted" activity

**Data Changes:**
```
// Store job_id before deletion
job_id = job_item.job_id
item_description = job_item.description

DELETE FROM job_items WHERE id = item_id

// Then recalculate job subtotal (WF-JOBITEM-RECALC)

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "item_deleted",
  description: "Deleted item: " + item_description,
  old_value: null,
  new_value: null,
  created_at: NOW()
}
```

**Returns:** `{ message: "Job item deleted" }`

---

### WF-JOBITEM-RECALC: Recalculate Job Subtotal

**Trigger:** Called after any job item add/update/delete

**Conditions:** Job must exist

**Actions:**
1. Query all job_items WHERE job_id = job_id
2. Calculate `subtotal` = SUM of all `job_items[].line_total`
3. Update job with new subtotal
4. Set job `updated_at` = current timestamp

**Data Changes:**
```
// Calculate
all_items = SELECT * FROM job_items WHERE job_id = job_id
subtotal = SUM(item.line_total for item in all_items)

UPDATE jobs WHERE id = job_id:
SET {
  subtotal: calculated_subtotal,
  updated_at: NOW()
}
```

**Returns:** Calculated subtotal value

---

## JOB NOTE WORKFLOWS

---

### WF-JOBNOTE-01: Add Note to Job

**Trigger:** User submits note form on job details

**Conditions:** Job with `job_id` must exist

**Actions:**
1. Find job by `id`
2. If not found → ERROR 404 "Job not found"
3. Generate new UUID for note `id`
4. Insert note record
5. **LOG ACTIVITY:** Create "note_added" activity
6. Set `created_at` = current timestamp

**Data Changes:**
```
INSERT INTO job_notes:
{
  id: generated UUID,
  job_id: job_id,
  content: input.content,
  author: input.author || null,
  created_at: NOW()
}

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "note_added",
  description: "Note added" + (input.author ? " by " + input.author : ""),
  old_value: null,
  new_value: null,
  created_at: NOW()
}
```

**Returns:** Created JobNote object

---

### WF-JOBNOTE-02: Delete Note

**Trigger:** User clicks delete on note

**Conditions:** Note with `note_id` must exist

**Actions:**
1. Delete note record
2. If no record deleted → ERROR 404 "Note not found"

**Data Changes:**
```
DELETE FROM job_notes WHERE id = note_id
```

**Returns:** `{ message: "Note deleted" }`

---

## INVOICE WORKFLOWS

---

### WF-INV-01: Create Invoice (Direct)

**Trigger:** User submits new invoice form

**Conditions:** `customer_id` must be provided

**Actions:**
1. Generate new UUID for `id`
2. Set `created_at` = current timestamp
3. Set `updated_at` = current timestamp
4. Set `status` = "draft" (if not provided)
5. Set `amount_paid` = 0
6. Set `paid_date` = null
7. Calculate totals (same as quote line items)
8. If `job_id` provided → update job with `invoice_id`

**Data Changes:**
```
// Calculate line item totals
line_items = []
total = 0
FOR EACH input.line_items:
  item_total = item.quantity × item.unit_price
  line_items.push({
    description: item.description,
    quantity: item.quantity,
    unit_price: item.unit_price,
    total: item_total,
    job_item_id: item.job_item_id || null
  })
  total += item_total

INSERT INTO invoices:
{
  id: generated UUID,
  customer_id: input.customer_id,
  job_id: input.job_id || null,
  line_items: line_items,
  total: total,  // CALCULATED
  status: input.status || "draft",
  due_date: input.due_date || null,
  notes: input.notes || null,
  amount_paid: 0,
  paid_date: null,
  created_at: NOW(),
  updated_at: NOW()
}

IF input.job_id:
UPDATE jobs WHERE id = input.job_id:
SET invoice_id = new_invoice.id
```

**Returns:** Created Invoice object

---

### WF-INV-02: Create Invoice from Job

**Trigger:** User clicks "Create Invoice" on job details

**Conditions:** Job with `job_id` must exist

**Actions:**
1. Find job by `id`
2. If not found → ERROR 404 "Job not found"
3. Query all job_items WHERE job_id = job_id
4. **IF job has items:**
   - Create invoice line items from job items
   - Calculate total from job items
5. **ELSE (no items):**
   - Use job.subtotal as total
   - If subtotal = 0 and job has quote_id → use quote.total
6. Generate new UUID for invoice
7. Insert invoice record
8. Update job with `invoice_id`
9. **LOG ACTIVITY:** Create "invoice_created" activity

**Data Changes:**
```
// Get job items
job_items = SELECT * FROM job_items WHERE job_id = job_id

IF job_items.length > 0:
  invoice_line_items = []
  total = 0
  FOR EACH job_item:
    invoice_line_items.push({
      description: job_item.description,
      quantity: job_item.quantity,
      unit_price: job_item.unit_price,
      total: job_item.line_total,
      job_item_id: job_item.id
    })
    total += job_item.line_total
ELSE:
  invoice_line_items = []
  total = job.subtotal
  IF total == 0 AND job.quote_id:
    quote = SELECT * FROM quotes WHERE id = job.quote_id
    total = quote.total

INSERT INTO invoices:
{
  id: generated UUID,
  customer_id: job.customer_id,
  job_id: job_id,
  line_items: invoice_line_items,
  total: total,
  status: "draft",
  due_date: null,
  notes: null,
  amount_paid: 0,
  paid_date: null,
  created_at: NOW(),
  updated_at: NOW()
}

UPDATE jobs WHERE id = job_id:
SET invoice_id = new_invoice.id

INSERT INTO job_activities:
{
  id: generated UUID,
  job_id: job_id,
  activity_type: "invoice_created",
  description: "Invoice created for " + total,
  old_value: null,
  new_value: new_invoice.id,
  created_at: NOW()
}
```

**Returns:** Created Invoice object

---

### WF-INV-03: Update Invoice

**Trigger:** User submits invoice edit form

**Conditions:** Invoice with `invoice_id` must exist

**Actions:**
1. Find invoice by `id`
2. If not found → ERROR 404 "Invoice not found"
3. Update only fields that are provided
4. **IF `line_items` changed:**
   - Recalculate each item.total = quantity × unit_price
   - Recalculate invoice total = SUM of all item.total
5. **IF status changed to "paid":**
   - Set `paid_date` = current timestamp
6. Set `updated_at` = current timestamp

**Data Changes:**
```
IF input.line_items provided:
  processed_items = []
  total = 0
  FOR EACH input.line_items:
    item_total = item.quantity × item.unit_price
    processed_items.push({
      ...item,
      total: item_total
    })
    total += item_total

UPDATE invoices WHERE id = invoice_id:
SET {
  line_items: processed_items,  // if provided
  total: recalculated_total,    // if line_items changed
  status: input.status,         // if provided
  due_date: input.due_date,     // if provided
  notes: input.notes,           // if provided
  paid_date: NOW() if status == "paid" else unchanged,
  updated_at: NOW()
}
```

**Returns:** Updated Invoice object

---

### WF-INV-04: Invoice Status Changes

**Trigger:** User changes invoice status

**Conditions:** Invoice must exist

**Status Flow:**
```
draft → sent → paid
             ↘ overdue (manual or automatic based on due_date)
```

**Actions by Status:**

#### Mark as Sent:
```
UPDATE invoices WHERE id = invoice_id:
SET {
  status: "sent",
  updated_at: NOW()
}
```

#### Mark as Paid:
```
UPDATE invoices WHERE id = invoice_id:
SET {
  status: "paid",
  amount_paid: invoice.total,  // Full payment
  paid_date: NOW(),
  updated_at: NOW()
}
```

#### Mark as Overdue:
```
UPDATE invoices WHERE id = invoice_id:
SET {
  status: "overdue",
  updated_at: NOW()
}
```

**Balance Due Calculation (on read):**
```
balance_due = invoice.total - invoice.amount_paid
```

---

### WF-INV-05: Record Partial Payment

**Trigger:** User records payment amount

**Conditions:** Invoice must exist

**Actions:**
1. Add payment amount to `amount_paid`
2. Check if `amount_paid` >= `total`
   - If yes → set status = "paid", set paid_date = NOW()
3. Set `updated_at` = current timestamp

**Data Changes:**
```
new_amount_paid = invoice.amount_paid + input.payment_amount

UPDATE invoices WHERE id = invoice_id:
SET {
  amount_paid: new_amount_paid,
  status: "paid" if new_amount_paid >= invoice.total else invoice.status,
  paid_date: NOW() if new_amount_paid >= invoice.total else invoice.paid_date,
  updated_at: NOW()
}
```

---

## TIME CLOCK WORKFLOWS

---

### WF-TIME-01: Clock Action (Start Work / Break Start / Break End / End Work)

**Trigger:** Employee clicks clock button

**Conditions:**
- `employee_id` must be provided
- `action` must be valid: "start_work", "break_start", "break_end", "end_work"
- Action must follow valid sequence (see below)

**Sequence Validation Rules:**
| Last Action | Valid Next Actions |
|-------------|-------------------|
| null (no logs today) | start_work |
| start_work | break_start, end_work |
| break_start | break_end |
| break_end | break_start, end_work |
| end_work | start_work |

**Actions:**
1. Validate action is in allowed list
2. Query today's logs for employee (filter by date prefix in timestamp)
3. Get last action from today's logs
4. Check if requested action is valid based on last action
   - If invalid → ERROR 400 with valid options
5. Generate new UUID for time log
6. Insert time log record

**Data Changes:**
```
// Validation
today = TODAY() in ISO format (YYYY-MM-DD)
today_logs = SELECT * FROM timelogs 
             WHERE employee_id = employee_id 
             AND timestamp STARTS WITH today
             ORDER BY timestamp ASC

last_action = today_logs.length > 0 ? today_logs[last].action : null

valid_sequences = {
  null: ["start_work"],
  "start_work": ["break_start", "end_work"],
  "break_start": ["break_end"],
  "break_end": ["break_start", "end_work"],
  "end_work": ["start_work"]
}

IF input.action NOT IN valid_sequences[last_action]:
  ERROR 400: "Invalid sequence. After '{last_action}', valid actions are: {valid_sequences[last_action]}"

// Insert
INSERT INTO timelogs:
{
  id: generated UUID,
  employee_id: input.employee_id,
  action: input.action,
  timestamp: NOW()
}
```

**Returns:** Created TimeLog object

---

### WF-TIME-02: Get Today's Logs

**Trigger:** Load time clock page for employee

**Conditions:** `employee_id` must be provided

**Actions:**
1. Get today's date in ISO format
2. Query all time logs for employee where timestamp starts with today
3. Sort by timestamp ascending

**Data Changes:** None (read-only)

```
today = TODAY() in ISO format
logs = SELECT * FROM timelogs 
       WHERE employee_id = employee_id 
       AND timestamp STARTS WITH today
       ORDER BY timestamp ASC
```

**Returns:** List of TimeLog objects

---

### WF-TIME-03: Get Clock Status

**Trigger:** Check current clock status for employee

**Conditions:** `employee_id` must be provided

**Actions:**
1. Get today's date
2. Query most recent log for employee today
3. Map last action to status

**Status Mapping:**
| Last Action | Status |
|-------------|--------|
| null | not_started |
| start_work | working |
| break_start | on_break |
| break_end | working |
| end_work | finished |

**Data Changes:** None (read-only)

```
today = TODAY() in ISO format
last_log = SELECT * FROM timelogs 
           WHERE employee_id = employee_id 
           AND timestamp STARTS WITH today
           ORDER BY timestamp DESC
           LIMIT 1

IF last_log is null:
  RETURN { status: "not_started", last_action: null }

status_map = {
  "start_work": "working",
  "break_start": "on_break",
  "break_end": "working",
  "end_work": "finished"
}

RETURN {
  status: status_map[last_log.action],
  last_action: last_log.action,
  last_timestamp: last_log.timestamp
}
```

**Returns:** Status object

---

### WF-TIME-04: Calculate Shift Summary

**Trigger:** View shift summary for employee on date

**Conditions:** 
- `employee_id` must be provided
- `date` optional (defaults to today)

**Actions:**
1. Query all time logs for employee on specified date
2. Sort by timestamp ascending
3. Calculate work minutes and break minutes
4. Calculate net minutes

**Calculation Algorithm:**
```
work_minutes = 0
break_minutes = 0
work_start = null
break_start = null

FOR EACH log IN logs (sorted by timestamp ASC):
  timestamp = PARSE(log.timestamp)
  
  IF log.action == "start_work":
    work_start = timestamp
    
  ELSE IF log.action == "break_start" AND work_start != null:
    break_start = timestamp
    
  ELSE IF log.action == "break_end" AND break_start != null:
    break_minutes += (timestamp - break_start) / 60  // in minutes
    break_start = null
    
  ELSE IF log.action == "end_work" AND work_start != null:
    work_minutes += (timestamp - work_start) / 60  // in minutes
    work_start = null

net_minutes = work_minutes - break_minutes
net_hours = net_minutes / 60
```

**Data Changes:** None (read-only)

**Returns:**
```
{
  employee_id: employee_id,
  date: date,
  work_minutes: ROUND(work_minutes, 2),
  break_minutes: ROUND(break_minutes, 2),
  net_minutes: ROUND(net_minutes, 2),
  net_hours: ROUND(net_hours, 2)
}
```

---

## PAYROLL WORKFLOWS

---

### WF-PAY-01: Create Payroll Transaction

**Trigger:** Admin submits payroll transaction form

**Conditions:**
- `employee_id` must be provided
- `type` must be valid: "earnings", "advance", "payment"
- `amount` must be provided

**Actions:**
1. Generate new UUID for `id`
2. Set `date` = input.date or current date
3. Set `created_at` = current timestamp
4. Insert transaction record

**Data Changes:**
```
INSERT INTO payroll_transactions:
{
  id: generated UUID,
  employee_id: input.employee_id,
  type: input.type,  // "earnings" | "advance" | "payment"
  amount: input.amount,
  description: input.description || null,
  date: input.date || TODAY(),
  created_at: NOW()
}
```

**Returns:** Created PayrollTransaction object

---

### WF-PAY-02: Get Payroll Transactions

**Trigger:** View payroll transactions (with filters)

**Conditions:** None

**Actions:**
1. Build query based on filters:
   - `employee_id` → filter by employee
   - `start_date` and/or `end_date` → filter by date range
2. Execute query

**Data Changes:** None (read-only)

```
query = {}
IF employee_id: query.employee_id = employee_id
IF start_date AND end_date: query.date = { $gte: start_date, $lte: end_date }
ELSE IF start_date: query.date = { $gte: start_date }
ELSE IF end_date: query.date = { $lte: end_date }

transactions = SELECT * FROM payroll_transactions WHERE query
```

**Returns:** List of PayrollTransaction objects

---

### WF-PAY-03: Calculate Payroll Balance (Per Employee)

**Trigger:** View employee payroll balance

**Conditions:** Employee with `employee_id` must exist

**Actions:**
1. Find employee by `id`
2. If not found → ERROR 404 "Employee not found"
3. Query all transactions for employee
4. Calculate totals by type
5. Calculate balance

**Calculation:**
```
employee = SELECT * FROM employees WHERE id = employee_id
IF employee is null: ERROR 404

transactions = SELECT * FROM payroll_transactions WHERE employee_id = employee_id

total_earnings = SUM(t.amount for t in transactions WHERE t.type == "earnings")
total_advances = SUM(t.amount for t in transactions WHERE t.type == "advance")
total_payments = SUM(t.amount for t in transactions WHERE t.type == "payment")

// Balance formula:
// Earnings = money owed TO employee
// Advances = money given to employee early (reduces what's owed)
// Payments = money paid to employee (reduces what's owed)
balance = total_earnings - total_advances - total_payments

// Interpretation:
// Positive balance = employer owes employee this amount
// Negative balance = employee received advance (employer is ahead)
```

**Data Changes:** None (read-only)

**Returns:**
```
{
  employee_id: employee_id,
  employee_name: employee.name,
  total_earnings: total_earnings,
  total_advances: total_advances,
  total_payments: total_payments,
  balance: balance
}
```

---

### WF-PAY-04: Generate Payroll Report (Date Range)

**Trigger:** Admin requests payroll report

**Conditions:**
- `start_date` must be provided
- `end_date` must be provided

**Actions:**
1. Query all employees
2. For each employee, query transactions in date range
3. Calculate period totals for each employee
4. Return consolidated report

**Calculation:**
```
employees = SELECT * FROM employees
report = []

FOR EACH employee IN employees:
  transactions = SELECT * FROM payroll_transactions 
                 WHERE employee_id = employee.id
                 AND date >= start_date
                 AND date <= end_date
  
  period_earnings = SUM(t.amount for t in transactions WHERE t.type == "earnings")
  period_advances = SUM(t.amount for t in transactions WHERE t.type == "advance")
  period_payments = SUM(t.amount for t in transactions WHERE t.type == "payment")
  period_balance = period_earnings - period_advances - period_payments
  
  report.push({
    employee_id: employee.id,
    employee_name: employee.name,
    period_earnings: period_earnings,
    period_advances: period_advances,
    period_payments: period_payments,
    period_balance: period_balance
  })

RETURN report
```

**Data Changes:** None (read-only)

**Returns:** List of employee period summaries

---

### WF-PAY-05: Calculate Earnings from Time Logs

**Trigger:** Generate earnings transaction from worked hours

**Conditions:**
- Employee must exist
- Employee must have `hourly_rate` set

**Actions:**
1. Get shift summary for date range (WF-TIME-04)
2. Calculate earnings = net_hours × employee.hourly_rate
3. Create earnings transaction (WF-PAY-01)

**Calculation:**
```
shift_summary = GET_SHIFT_SUMMARY(employee_id, date)
employee = SELECT * FROM employees WHERE id = employee_id

earnings_amount = shift_summary.net_hours × employee.hourly_rate

// Then create transaction via WF-PAY-01
CREATE_PAYROLL_TRANSACTION({
  employee_id: employee_id,
  type: "earnings",
  amount: earnings_amount,
  description: "Earnings for " + date + " (" + shift_summary.net_hours + " hours)",
  date: date
})
```

---

## FINANCIAL WORKFLOWS

---

### WF-FIN-01: Create Sales Entry

**Trigger:** User submits sales entry form

**Conditions:** 
- `date` must be provided
- `amount` must be provided

**Actions:**
1. Generate new UUID for `id`
2. Set `created_at` = current timestamp
3. Insert sales entry record

**Data Changes:**
```
INSERT INTO sales_entries:
{
  id: generated UUID,
  date: input.date,
  amount: input.amount,
  tax_amount: input.tax_amount || 0,
  description: input.description || null,
  created_at: NOW()
}
```

**Returns:** Created SalesEntry object

---

### WF-FIN-02: Create Expense Entry

**Trigger:** User submits expense entry form

**Conditions:**
- `date` must be provided
- `amount` must be provided

**Actions:**
1. Generate new UUID for `id`
2. Set `created_at` = current timestamp
3. Insert expense entry record

**Data Changes:**
```
INSERT INTO expense_entries:
{
  id: generated UUID,
  date: input.date,
  amount: input.amount,
  category: input.category || "other",
  description: input.description || null,
  created_at: NOW()
}
```

**Returns:** Created ExpenseEntry object

---

### WF-FIN-03: Calculate Financial Summary

**Trigger:** View financial summary for date range

**Conditions:**
- `start_date` must be provided
- `end_date` must be provided

**Actions:**
1. Query all sales entries in date range
2. Query all expense entries in date range
3. Calculate totals

**Calculation:**
```
sales = SELECT * FROM sales_entries 
        WHERE date >= start_date AND date <= end_date

expenses = SELECT * FROM expense_entries 
           WHERE date >= start_date AND date <= end_date

total_sales = SUM(s.amount for s in sales)
total_tax = SUM(s.tax_amount for s in sales)
total_expenses = SUM(e.amount for e in expenses)
net_income = total_sales - total_expenses
```

**Data Changes:** None (read-only)

**Returns:**
```
{
  total_sales: total_sales,
  total_tax: total_tax,
  total_expenses: total_expenses,
  net_income: net_income
}
```

---

## TASK WORKFLOWS

---

### WF-TASK-01: Create Task

**Trigger:** User submits task form

**Conditions:** None

**Actions:**
1. Generate new UUID for `id`
2. Set `created_at` = current timestamp
3. Set `is_complete` = false (default)
4. Insert task record

**Data Changes:**
```
INSERT INTO tasks:
{
  id: generated UUID,
  title: input.title,
  description: input.description || null,
  job_id: input.job_id || null,
  due_date: input.due_date || null,
  is_complete: false,
  created_at: NOW()
}
```

**Returns:** Created Task object

---

### WF-TASK-02: Update Task

**Trigger:** User submits task edit form

**Conditions:** Task must exist

**Actions:**
1. Find task by `id`
2. If not found → ERROR 404 "Task not found"
3. Update only fields that are provided

**Data Changes:**
```
UPDATE tasks WHERE id = task_id:
SET {
  title: input.title,           // if provided
  description: input.description,  // if provided
  job_id: input.job_id,         // if provided
  due_date: input.due_date,     // if provided
  is_complete: input.is_complete  // if provided
}
```

**Returns:** Updated Task object

---

### WF-TASK-03: Toggle Task Complete

**Trigger:** User clicks task checkbox

**Conditions:** Task must exist

**Actions:**
1. Find task by `id`
2. Toggle `is_complete` value

**Data Changes:**
```
UPDATE tasks WHERE id = task_id:
SET is_complete = NOT current_is_complete
```

**Returns:** Updated Task object

---

### WF-TASK-04: Delete Task

**Trigger:** User clicks delete task

**Conditions:** Task must exist

**Actions:**
1. Delete task record
2. If no record deleted → ERROR 404 "Task not found"

**Data Changes:**
```
DELETE FROM tasks WHERE id = task_id
```

**Returns:** `{ message: "Task deleted" }`

---

## WEBSTORE WORKFLOWS

---

### WF-WEB-01: Create Webstore Order

**Trigger:** Customer places order on webstore

**Conditions:**
- `store_type` must be "fundraiser" or "b2b"
- `store_id` must be provided
- `items` must be provided
- `total` must be provided

**Actions:**
1. Generate new UUID for order `id`
2. Set `status` = "pending"
3. **AUTO-CREATE CUSTOMER** (if not exists):
   - Find customer with company = "Webstore {TYPE} Customer"
   - If not found → create new customer
4. **AUTO-CREATE JOB:**
   - Create job linked to customer
   - Set name = "Webstore Order #{order_id first 8 chars}"
   - Set status = "approved"
5. Link order to job
6. Insert order record
7. **IF store_type = "fundraiser":**
   - Increment campaign's `total_raised` by order total

**Data Changes:**
```
// Find or create customer
customer_name = "Webstore " + UPPERCASE(store_type) + " Customer"
customer = SELECT * FROM customers WHERE company = customer_name

IF customer is null:
  INSERT INTO customers:
  {
    id: generated UUID,
    name: customer_name,
    company: customer_name,
    status: "active",
    created_at: NOW(),
    updated_at: NOW()
  }
  customer_id = new_customer.id
ELSE:
  customer_id = customer.id

// Create job
INSERT INTO jobs:
{
  id: generated UUID,
  customer_id: customer_id,
  name: "Webstore Order #" + order_id.substring(0,8),
  description: "Order from " + store_type + " store " + store_id,
  status: "approved",
  subtotal: 0,
  is_archived: false,
  created_at: NOW(),
  updated_at: NOW()
}

// Create order
INSERT INTO webstore_orders:
{
  id: generated UUID,
  store_type: input.store_type,
  store_id: input.store_id,
  items: input.items,  // JSON array
  total: input.total,
  status: "pending",
  job_id: new_job.id,
  created_at: NOW()
}

// Update fundraiser total if applicable
IF store_type == "fundraiser":
  UPDATE fundraiser_campaigns WHERE id = store_id:
  INCREMENT total_raised BY input.total
```

**Returns:** Created WebstoreOrder object

---

## DASHBOARD WORKFLOWS

---

### WF-DASH-01: Get Dashboard Stats

**Trigger:** Load dashboard page

**Conditions:** None

**Actions:**
1. Count total customers
2. Count active jobs (status not in ["complete"])
3. Count pending invoices (status in ["sent", "overdue"])
4. Sum today's sales
5. Sum overdue invoice totals

**Calculation:**
```
today = TODAY() in ISO format

total_customers = COUNT(customers)
active_jobs = COUNT(jobs WHERE status NOT IN ["complete"])
pending_invoices = COUNT(invoices WHERE status IN ["sent", "overdue"])

today_sales = SELECT * FROM sales_entries WHERE date = today
today_revenue = SUM(s.amount for s in today_sales)

overdue_invoices = SELECT * FROM invoices WHERE status = "overdue"
overdue_total = SUM(i.total for i in overdue_invoices)
overdue_count = COUNT(overdue_invoices)
```

**Data Changes:** None (read-only)

**Returns:**
```
{
  total_customers: total_customers,
  active_jobs: active_jobs,
  pending_invoices: pending_invoices,
  today_revenue: today_revenue,
  overdue_total: overdue_total,
  overdue_count: overdue_count
}
```

---

## WORKFLOW SUMMARY BY MODULE

| Module | Create | Read | Update | Delete | Special |
|--------|--------|------|--------|--------|---------|
| Customer | WF-CUST-01 | WF-CUST-04 | WF-CUST-02 | WF-CUST-03 | - |
| Quote | WF-QUOTE-01 | - | WF-QUOTE-02,03 | - | WF-QUOTE-04,05,06 (line items), WF-QUOTE-07 (convert) |
| Job | WF-JOB-01 | WF-JOB-08 | WF-JOB-02,03 | WF-JOB-07 | WF-JOB-04 (complete), WF-JOB-05,06 (archive) |
| JobItem | WF-JOBITEM-01 | - | WF-JOBITEM-02 | WF-JOBITEM-03 | WF-JOBITEM-RECALC (subtotal) |
| JobNote | WF-JOBNOTE-01 | - | - | WF-JOBNOTE-02 | - |
| Invoice | WF-INV-01 | - | WF-INV-03 | - | WF-INV-02 (from job), WF-INV-04,05 (status/payment) |
| TimeClock | WF-TIME-01 | WF-TIME-02,03 | - | - | WF-TIME-04 (summary) |
| Payroll | WF-PAY-01 | WF-PAY-02 | - | - | WF-PAY-03 (balance), WF-PAY-04 (report), WF-PAY-05 (from hours) |
| Financial | WF-FIN-01,02 | WF-FIN-03 | - | - | - |
| Task | WF-TASK-01 | - | WF-TASK-02 | WF-TASK-04 | WF-TASK-03 (toggle) |
| Webstore | WF-WEB-01 | - | - | - | Auto-creates customer and job |
| Dashboard | - | WF-DASH-01 | - | - | - |
