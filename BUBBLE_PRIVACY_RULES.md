# Sign Guy AI - Bubble Privacy Rules Implementation

## OVERVIEW

This document translates the roles and permissions matrix into Bubble-specific privacy rules, including exact constraint syntax, search patterns, and common pitfalls.

---

## PART 1: USER SETUP

### User Data Type Extension

Add these fields to Bubble's built-in **User** type:

```
User (built-in)
├── email (built-in)
├── role                → type: text
│                         values: "owner", "staff", "customer"
│                         default: "staff"
├── linked_employee     → type: Employee (optional)
│                         used for: staff time clock access
├── linked_customer     → type: Customer (optional)
│                         used for: customer portal access
├── is_active           → type: yes/no
│                         default: yes
└── created_at          → type: date
                          default: Current date/time
```

### Role Constants

Create an **Option Set** called `UserRole`:

| Display | Value | Attributes |
|---------|-------|------------|
| Owner | owner | access_level: 100 |
| Staff | staff | access_level: 50 |
| Customer | customer | access_level: 10 |

**Usage in privacy rules:** `Current User's role is "owner"`

---

## PART 2: PRIVACY RULE STRUCTURE

### Bubble Privacy Rule Anatomy

```
Data Type: [Type Name]
├── Privacy Rule 1: [Rule Name]
│   ├── When: [Condition that must be true]
│   ├── This type can be viewed: [yes/no/field-level]
│   ├── This type can be found in searches: [yes/no]
│   ├── This type can be modified: [yes/no]
│   └── This type can be deleted: [yes/no]
│
├── Privacy Rule 2: [Rule Name]
│   └── ...
│
└── Default (when no rules match):
    └── All operations DENIED
```

### Rule Evaluation Order

```
1. Bubble evaluates rules TOP TO BOTTOM
2. FIRST matching rule applies
3. If NO rules match → ALL ACCESS DENIED
4. More specific rules should be ABOVE general rules
```

---

## PART 3: PRIVACY RULES BY DATA TYPE

### Customer

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: Customer                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ ─────────────────────────────────────────────────────────────── │
│ When: Current User's role is "owner"                            │
│                                                                 │
│ ☑ View all fields                                               │
│ ☑ Find in searches                                              │
│ ☑ Modify all fields                                             │
│ ☑ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff Access"                                          │
│ ─────────────────────────────────────────────────────────────── │
│ When: Current User's role is "staff"                            │
│                                                                 │
│ ☑ View all fields                                               │
│ ☑ Find in searches                                              │
│ ☑ Modify all fields                                             │
│ ☐ Delete                          ← Staff cannot delete         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Customer Portal - Own Profile"                         │
│ ─────────────────────────────────────────────────────────────── │
│ When: Current User's role is "customer"                         │
│   AND Current User's linked_customer is This Customer           │
│                                                                 │
│ ☑ View: name, company, email, phone                             │
│ ☐ View: status, notes, created_at  ← Hide internal fields       │
│ ☑ Find in searches                                              │
│ ☑ Modify: company, email, phone    ← Limited edit               │
│ ☐ Modify: name, status, notes                                   │
│ ☐ Delete                                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Bubble Implementation:**

```
Privacy Tab → Customer

Rule 1: Owner Full Access
├── Define a new rule
├── When: Current User's role is "owner"
├── Everyone else (unchecked - this is for matching users)
├── View all fields: ✓
├── Find this in searches: ✓
├── Modify all fields: ✓
└── Delete: ✓

Rule 2: Staff Access
├── When: Current User's role is "staff"
├── View all fields: ✓
├── Find this in searches: ✓
├── Modify all fields: ✓
└── Delete: ✗

Rule 3: Customer Own Profile
├── When: Current User's role is "customer" 
│         AND Current User's linked_customer is This Customer
├── View fields: name ✓, company ✓, email ✓, phone ✓, 
│                status ✗, notes ✗, created_at ✗
├── Find this in searches: ✓
├── Modify fields: company ✓, email ✓, phone ✓,
│                  name ✗, status ✗, notes ✗
└── Delete: ✗
```

---

### Order

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: Order                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ ─────────────────────────────────────────────────────────────── │
│ When: Current User's role is "owner"                            │
│                                                                 │
│ ☑ View all fields                                               │
│ ☑ Find in searches                                              │
│ ☑ Modify all fields                                             │
│ ☑ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff Access"                                          │
│ ─────────────────────────────────────────────────────────────── │
│ When: Current User's role is "staff"                            │
│                                                                 │
│ ☑ View all fields                                               │
│ ☑ Find in searches                                              │
│ ☑ Modify all fields                                             │
│ ☐ Delete                          ← Only owners delete orders     │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Customer Portal - Own Orders"                            │
│ ─────────────────────────────────────────────────────────────── │
│ When: Current User's role is "customer"                         │
│   AND This Order's customer is Current User's linked_customer     │
│                                                                 │
│ ☑ View: name, status, due_date, subtotal                        │
│ ☐ View: description, is_archived, quote, invoice                │
│ ☑ Find in searches                                              │
│ ☐ Modify                          ← Customers can't edit orders   │
│ ☐ Delete                                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Constraint Expression:**

```
This Order's customer is Current User's linked_customer
```

This is a **relational constraint** - it follows the reference from Order → Customer and compares to User's linked_customer.

---

### JobTicket

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: JobTicket                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ When: Current User's role is "owner"                            │
│ All permissions: ✓                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff Full Access"                                     │
│ When: Current User's role is "staff"                            │
│ View: ✓  Find: ✓  Modify: ✓  Delete: ✓                         │
│ (Staff can manage job items fully)                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Customer Portal - Own Order Items"                       │
│ When: Current User's role is "customer"                         │
│   AND This OrderItem's job's customer                             │
│       is Current User's linked_customer                         │
│                                                                 │
│ ☑ View: item_type, description, quantity, unit_price,           │
│         line_total, status                                      │
│ ☐ View: notes                     ← Internal notes hidden       │
│ ☑ Find in searches                                              │
│ ☐ Modify                                                        │
│ ☐ Delete                                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Constraint Expression (Nested):**

```
This OrderItem's job's customer is Current User's linked_customer
```

⚠️ **Note:** This is a two-level traversal: JobTicket → Order → Customer

---

### Invoice

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: Invoice                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ When: Current User's role is "owner"                            │
│ All permissions: ✓                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff Access - Draft Invoices"                         │
│ When: Current User's role is "staff"                            │
│   AND This Invoice's status is "draft"                          │
│                                                                 │
│ View: ✓  Find: ✓  Modify: ✓  Delete: ✗                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Staff Access - Sent/Paid Invoices"                     │
│ When: Current User's role is "staff"                            │
│   AND This Invoice's status is not "draft"                      │
│                                                                 │
│ ☑ View all fields                                               │
│ ☑ Find in searches                                              │
│ ☑ Modify: status only            ← Can mark paid               │
│ ☐ Modify: total, line_items      ← Cannot change amounts       │
│ ☐ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 4: "Customer Portal - Own Invoices"                        │
│ When: Current User's role is "customer"                         │
│   AND This Invoice's customer is Current User's linked_customer │
│                                                                 │
│ ☑ View all fields                 ← Customers see full invoice  │
│ ☑ Find in searches                                              │
│ ☐ Modify                                                        │
│ ☐ Delete                                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Complex Constraint (Staff Invoice Edit):**

```
Current User's role is "staff" AND This Invoice's status is "draft"
```

This uses **AND** to combine role check with data state check.

---

### Employee

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: Employee                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ When: Current User's role is "owner"                            │
│ All permissions: ✓                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff - View Own Profile"                              │
│ When: Current User's role is "staff"                            │
│   AND This Employee is Current User's linked_employee           │
│                                                                 │
│ ☑ View: name, is_active                                         │
│ ☐ View: hourly_rate              ← Can't see own rate          │
│ ☑ Find in searches                                              │
│ ☐ Modify                         ← Can't edit own profile      │
│ ☐ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Staff - View Other Employees (Names Only)"             │
│ When: Current User's role is "staff"                            │
│                                                                 │
│ ☑ View: name                      ← Only names visible         │
│ ☐ View: hourly_rate, is_active                                  │
│ ☑ Find in searches                                              │
│ ☐ Modify                                                        │
│ ☐ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 4: "Customer Portal - No Access"                           │
│ When: Current User's role is "customer"                         │
│                                                                 │
│ ☐ View                            ← Complete block              │
│ ☐ Find in searches                                              │
│ ☐ Modify                                                        │
│ ☐ Delete                                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Rule Order Critical Here:**
```
Rule 2 (own profile) MUST be above Rule 3 (all employees)
Otherwise Rule 3 matches first and blocks hourly_rate even for own profile
```

---

### TimeLog

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: TimeLog                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ When: Current User's role is "owner"                            │
│ All permissions: ✓                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff - Own Time Logs"                                 │
│ When: Current User's role is "staff"                            │
│   AND This TimeLog's employee is Current User's linked_employee │
│                                                                 │
│ ☑ View all fields                                               │
│ ☑ Find in searches                                              │
│ ☑ Create (via workflow)          ← Can clock in/out            │
│ ☐ Modify                         ← Can't edit past entries     │
│ ☐ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Staff - Other Time Logs (Block)"                       │
│ When: Current User's role is "staff"                            │
│   AND This TimeLog's employee is not Current User's linked_emp  │
│                                                                 │
│ ☐ All permissions                 ← Complete block              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### PayrollTransaction

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: PayrollTransaction                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ When: Current User's role is "owner"                            │
│ All permissions: ✓                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff - View Own Transactions"                         │
│ When: Current User's role is "staff"                            │
│   AND This PayrollTransaction's employee                        │
│       is Current User's linked_employee                         │
│                                                                 │
│ ☑ View all fields                 ← Can see own pay history    │
│ ☑ Find in searches                                              │
│ ☐ Modify                         ← Can't edit payroll          │
│ ☐ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Staff - Other Payroll (Block)"                         │
│ When: Current User's role is "staff"                            │
│                                                                 │
│ ☐ All permissions                 ← Can't see others' pay      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Quote (Post-MVP)

```
┌─────────────────────────────────────────────────────────────────┐
│ DATA TYPE: Quote                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ When: Current User's role is "owner"                            │
│ All permissions: ✓                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff Access"                                          │
│ When: Current User's role is "staff"                            │
│ View: ✓  Find: ✓  Modify: ✓  Delete: ✗                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 3: "Customer Portal - Own Quotes (Sent Status)"            │
│ When: Current User's role is "customer"                         │
│   AND This Quote's customer is Current User's linked_customer   │
│   AND This Quote's status is "sent"                             │
│                                                                 │
│ ☑ View all fields                                               │
│ ☑ Find in searches                                              │
│ ☑ Modify: status only            ← Can approve/decline         │
│ ☐ Delete                                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 4: "Customer Portal - Own Quotes (Other Status)"           │
│ When: Current User's role is "customer"                         │
│   AND This Quote's customer is Current User's linked_customer   │
│                                                                 │
│ ☑ View all fields                 ← Can see all their quotes   │
│ ☑ Find in searches                                              │
│ ☐ Modify                         ← Can't change approved/etc   │
│ ☐ Delete                                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Customer Quote Approval Constraint:**

```
When: Current User's role is "customer"
  AND This Quote's customer is Current User's linked_customer
  AND This Quote's status is "sent"
  
Allowed status changes: "sent" → "approved" OR "sent" → "declined"
```

---

### Internal-Only Data Types

These types should **BLOCK** all customer portal access:

```
┌─────────────────────────────────────────────────────────────────┐
│ INTERNAL-ONLY TYPES (Same Pattern)                              │
│ • OrderNote                                                       │
│ • OrderActivity                                                   │
│ • Task                                                          │
│ • SalesEntry                                                    │
│ • ExpenseEntry                                                  │
│ • AIResponse                                                    │
│ • FundraiserCampaign (admin)                                    │
│ • B2BStore (admin)                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 1: "Owner Full Access"                                     │
│ When: Current User's role is "owner"                            │
│ All permissions: ✓                                              │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ RULE 2: "Staff Access"                                          │
│ When: Current User's role is "staff"                            │
│ View: ✓  Find: ✓  Modify: ✓  Delete: varies                    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ NO RULE FOR CUSTOMERS = BLOCKED BY DEFAULT                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## PART 4: SEARCH BEHAVIOR WITH PRIVACY RULES

### How Privacy Affects Searches

```
IMPORTANT: Privacy rules filter search results automatically

Search for Orders → Only returns Orders the current user can "Find in searches"

If user is "customer":
  - Only Orders where customer = their linked_customer
  - Other orders are invisible (not just hidden, truly not returned)
```

### Search Examples

**Owner Search:**
```
Do a search for: Orders
Constraint: status is not "archived"
Result: ALL orders that aren't archived (privacy rule allows all)
```

**Staff Search:**
```
Do a search for: Orders
Constraint: status is not "archived"
Result: ALL orders that aren't archived (same as owner for Orders)
```

**Customer Portal Search:**
```
Do a search for: Orders
Constraint: status is not "archived"
Result: ONLY their orders that aren't archived
        (privacy rule auto-filters to their customer)
```

### Search + Privacy Rule Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│ SEARCH CONSTRAINT vs PRIVACY RULE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Search: Do a search for Orders                                    │
│         where status = "in_production"                          │
│                                                                 │
│ Privacy Rule: Customer can only see Orders where                  │
│               customer = their linked_customer                  │
│                                                                 │
│ RESULT: Orders where                                              │
│         status = "in_production"                                │
│         AND customer = Current User's linked_customer           │
│                                                                 │
│ Privacy rule is applied AUTOMATICALLY after search constraint   │
│ You don't need to add customer filter in the search             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Counting with Privacy

```
Visible count = Search for Orders:count
This count ALREADY respects privacy rules

Owner sees: 50 orders
Staff sees: 50 orders (same access for Orders)
Customer sees: 3 orders (only their orders)
```

---

## PART 5: COMMON MISTAKES TO AVOID

### Mistake #1: Rule Order Wrong

```
❌ WRONG ORDER:
Rule 1: Staff Access (matches all staff)
Rule 2: Staff Own Profile (never reached)

✓ CORRECT ORDER:
Rule 1: Staff Own Profile (more specific, checked first)
Rule 2: Staff General Access (fallback for other cases)
```

**Why it matters:** Bubble evaluates top-to-bottom, first match wins.

---

### Mistake #2: Forgetting "Find in Searches"

```
❌ WRONG:
Rule: Customer can view Orders
      ☑ View all fields
      ☐ Find in searches    ← UNCHECKED

Result: Customer can see Order if they somehow get to it,
        but "Search for Orders" returns EMPTY

✓ CORRECT:
Rule: Customer can view Orders
      ☑ View all fields
      ☑ Find in searches    ← MUST BE CHECKED
```

**Why it matters:** "Find in searches" controls search/repeating group visibility.

---

### Mistake #3: Using "is" vs "is not" Incorrectly

```
❌ WRONG:
When: Current User's role is not "customer"
      (Matches both owner AND staff - too broad)

✓ CORRECT:
When: Current User's role is "staff"
      (Matches exactly staff)
```

**Why it matters:** "is not X" matches everything except X, which may be more than intended.

---

### Mistake #4: Missing the "Everyone Else" Case

```
❌ WRONG:
Rule 1: Owner full access
Rule 2: Staff limited access
(No rule for customer = complete block, even for their own data)

✓ CORRECT:
Rule 1: Owner full access
Rule 2: Staff limited access  
Rule 3: Customer own data access
(Explicit rule for each role that needs access)
```

**Why it matters:** No matching rule = access denied by default.

---

### Mistake #5: Field-Level Privacy in Searches

```
❌ WRONG ASSUMPTION:
"If I hide hourly_rate field, searches won't expose it"

ACTUALLY:
Hidden fields return null/empty in search results
But the RECORD is still found
User just sees blank where that field would be

✓ CORRECT APPROACH:
If field is truly sensitive, block "Find in searches" entirely
Or accept that record is visible but field is null
```

---

### Mistake #6: Nested Reference Privacy Gaps

```
❌ WRONG:
Order privacy: Customer sees only their orders ✓
JobTicket privacy: No customer rule defined ✗

Result: Customer can't see JobTickets even for their own orders
        because JobTicket has no rule granting access

✓ CORRECT:
Order privacy: Customer sees their orders
JobTicket privacy: Customer sees items where 
                 This OrderItem's job's customer = their linked_customer
```

**Why it matters:** Each type needs its own privacy rules; they don't inherit from parent.

---

### Mistake #7: Modify vs Delete Confusion

```
❌ WRONG:
Staff Rule:
  ☑ Modify all fields
  ☐ Delete

Expectation: Staff can't delete
Reality: Staff CAN'T delete via UI, 
         but they CAN make changes to record
         (Including setting a "deleted" flag if you have one)

✓ CORRECT UNDERSTANDING:
- "Delete" = permanent database delete
- "Modify" = change any/all fields
- Soft delete (is_deleted flag) requires blocking Modify
  OR blocking that specific field
```

---

### Mistake #8: Privacy Rules Don't Block Workflows

```
❌ WRONG ASSUMPTION:
"Privacy rules will stop unauthorized workflow actions"

ACTUALLY:
Privacy rules affect:
  - Page data display
  - Search results
  - Direct data modifications

Privacy rules DON'T affect:
  - Backend workflows
  - API workflows
  - Scheduled workflows

✓ CORRECT APPROACH:
Add "Only when" conditions to workflows:
  Only when: Current User's role is "owner"
```

---

### Mistake #9: Relying Only on Privacy Rules for Security

```
❌ WRONG:
- Set privacy rules
- Assume all security is handled

ACTUALLY NEEDED:
- Privacy rules (data access)
- Page access conditions (who sees pages)
- Workflow conditions (who triggers actions)
- Element conditions (who sees buttons)

✓ CORRECT - LAYERED SECURITY:

Layer 1: Page Level
  Page is visible when: Current User's role is not "customer"

Layer 2: Element Level
  Delete button visible when: Current User's role is "owner"

Layer 3: Workflow Level
  Only when: Current User's role is "owner"

Layer 4: Privacy Rule
  Delete permission: only for owner role
```

---

### Mistake #10: Not Testing with Actual Users

```
❌ WRONG:
- Build privacy rules
- Test only in preview (you're logged in as admin/owner)
- Deploy

✓ CORRECT:
- Create test users for each role:
  - test-owner@example.com (role: owner)
  - test-staff@example.com (role: staff)
  - test-customer@example.com (role: customer, linked to test customer)
- Log in as each user type
- Verify:
  - Correct data visible in searches
  - Correct fields visible/hidden
  - Correct actions allowed/blocked
  - Counts match expectations
```

---

## PART 6: IMPLEMENTATION CHECKLIST

### Setup Checklist

```
□ Add role field to User type
□ Add linked_employee field to User type
□ Add linked_customer field to User type
□ Create UserRole option set
□ Create test users (one per role)
□ Link test-staff user to an Employee
□ Link test-customer user to a Customer
```

### Per-Data-Type Checklist

```
For each data type:
□ Owner rule (full access)
□ Staff rule (appropriate access)
□ Customer rule (if applicable)
□ Verify rule order (specific before general)
□ Verify "Find in searches" is set correctly
□ Test with each user role
□ Verify field-level restrictions work
```

### Testing Checklist

```
As Owner:
□ Can see all records
□ Can modify all records
□ Can delete records
□ Counts are complete

As Staff:
□ Can see appropriate records
□ Can modify appropriate records
□ Cannot delete (where restricted)
□ Cannot see restricted fields (e.g., hourly_rate)
□ Can only clock own time

As Customer:
□ Can only see own data
□ Cannot see internal types (Tasks, Notes, etc.)
□ Can see but not modify orders
□ Can see and approve quotes (when sent)
□ Can see invoices
□ Cannot see employee data
```

---

## PART 7: QUICK REFERENCE

### Privacy Rule Syntax Patterns

**Role Check:**
```
Current User's role is "owner"
Current User's role is "staff"
Current User's role is "customer"
```

**Self-Reference (Employee/Customer):**
```
This Employee is Current User's linked_employee
This Customer is Current User's linked_customer
```

**Parent Reference:**
```
This Order's customer is Current User's linked_customer
This Invoice's customer is Current User's linked_customer
```

**Nested Reference:**
```
This OrderItem's job's customer is Current User's linked_customer
This TimeLog's employee is Current User's linked_employee
```

**Status-Based:**
```
This Invoice's status is "draft"
This Quote's status is "sent"
```

**Compound:**
```
Current User's role is "staff" AND This Invoice's status is "draft"
Current User's role is "customer" AND This Quote's status is "sent"
```

### Permission Matrix Quick Reference

| Type | Owner | Staff | Customer |
|------|-------|-------|----------|
| Customer | CRUD | CRU | R (own) |
| Order | CRUD | CRU | R (own) |
| JobTicket | CRUD | CRUD | R (own) |
| Invoice | CRUD | CRU* | R (own) |
| Employee | CRUD | R (own) | - |
| TimeLog | CRUD | CR (own) | - |
| PayrollTx | CRUD | R (own) | - |
| Quote | CRUD | CRU | R (own) + approve |
| Task | CRUD | CRUD | - |
| Internal | CRUD | varies | - |

*Staff Invoice: Full edit only when draft, status-only when sent/paid

---

## PART 8: DEBUGGING PRIVACY ISSUES

### Symptom: Empty Repeating Group

```
Possible causes:
1. "Find in searches" is unchecked
2. No privacy rule matches current user
3. Constraint on search conflicts with privacy rule

Debug steps:
1. Check privacy rules for "Find in searches"
2. Verify current user's role value
3. Test same search as owner (should work)
4. Add each constraint one at a time to isolate issue
```

### Symptom: Field Shows Empty

```
Possible causes:
1. Field is hidden at privacy level
2. Field value is actually null
3. Wrong field referenced in element

Debug steps:
1. Check privacy rule field-level permissions
2. View record in database as admin
3. Test as owner (field should show)
```

### Symptom: Can't Modify Record

```
Possible causes:
1. Modify permission not granted
2. Specific field not allowed for modify
3. Workflow has "Only when" blocking

Debug steps:
1. Check "Modify" checkbox in privacy rule
2. Check field-level modify permissions
3. Check workflow conditions
4. Test as owner (should work)
```

### Symptom: Can Still Delete When Shouldn't

```
Possible causes:
1. Multiple rules, one grants delete
2. Workflow doesn't check role
3. Element visible but should be hidden

Debug steps:
1. Review ALL privacy rules for the type
2. Check workflow "Only when" conditions
3. Add conditional to hide delete button
4. Test with actual role user, not preview
```

### Debug Mode Approach

```
Temporary debug changes:
1. Add text element showing: Current User's role
2. Add text element showing: Search for X:count
3. Add text element showing: This Thing's [field]
4. Test each role and compare values
5. Remove debug elements when fixed
```
