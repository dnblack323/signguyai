# Sign Guy AI - Roles & Permissions Matrix

## OVERVIEW

This document defines the intended roles and permissions structure for Sign Guy AI. **Note: Role-based access control is NOT currently implemented** - this is a specification for future development.

### Roles Summary

| Role | Description | Typical User |
|------|-------------|--------------|
| **Owner** | Full system access, all administrative functions | Business owner, manager |
| **Staff** | Day-to-day operations, limited admin | Designers, production staff, sales |
| **Customer Portal User** | Limited external access to their own data | End customers |

---

## PERMISSION LEVELS

| Symbol | Meaning |
|--------|---------|
| ✅ | Full access |
| 📖 | Read only |
| 🔒 | No access |
| ⚠️ | Conditional / Limited |
| 👤 | Own records only |

---

## DATA TYPE PERMISSIONS

### Customer

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **View Own** | ✅ | ✅ | 👤 (own profile) |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ✅ | 👤 (limited fields) |
| **Delete** | ✅ | 🔒 | 🔒 |
| **Change Status** | ✅ | ✅ | 🔒 |

**Field-Level Restrictions:**

| Field | Owner | Staff | Customer Portal |
|-------|-------|-------|-----------------|
| name | ✅ | ✅ | 📖 |
| company | ✅ | ✅ | 👤 Edit |
| email | ✅ | ✅ | 👤 Edit |
| phone | ✅ | ✅ | 👤 Edit |
| status | ✅ | ✅ | 🔒 |
| notes | ✅ | ✅ | 🔒 (internal) |
| created_at | 📖 | 📖 | 🔒 |

---

### Quote

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **View Own** | ✅ | ✅ | 👤 (quotes for their account) |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ✅ | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |
| **Change Status** | ✅ | ✅ | ⚠️ (approve/decline only) |
| **Convert to Job** | ✅ | ✅ | 🔒 |
| **Add Line Items** | ✅ | ✅ | 🔒 |

**Field-Level Restrictions:**

| Field | Owner | Staff | Customer Portal |
|-------|-------|-------|-----------------|
| customer_id | ✅ | ✅ | 🔒 |
| line_items | ✅ | ✅ | 📖 |
| notes | ✅ | ✅ | 📖 |
| status | ✅ | ✅ | ⚠️ (approve/decline) |
| total | 📖 | 📖 | 📖 |
| job_id | 📖 | 📖 | 🔒 |

**Customer Portal Quote Actions:**
- View quotes sent to them
- Approve quote (changes status to "approved")
- Decline quote (changes status to "declined")
- Cannot modify pricing or line items

---

### Job

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **View Own** | ✅ | ✅ | 👤 (jobs for their account) |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ✅ | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |
| **Change Status** | ✅ | ✅ | 🔒 |
| **Mark Complete** | ✅ | ✅ | 🔒 |
| **Archive** | ✅ | ✅ | 🔒 |
| **View Activity Log** | ✅ | ✅ | 📖 (limited) |

**Field-Level Restrictions:**

| Field | Owner | Staff | Customer Portal |
|-------|-------|-------|-----------------|
| name | ✅ | ✅ | 📖 |
| description | ✅ | ✅ | 📖 |
| status | ✅ | ✅ | 📖 |
| due_date | ✅ | ✅ | 📖 |
| subtotal | 📖 | 📖 | 📖 |
| is_archived | ✅ | ✅ | 🔒 |
| quote_id | 📖 | 📖 | 🔒 |
| invoice_id | 📖 | 📖 | 🔒 |

**Customer Portal Job View:**
- See job name, status, due date
- See line items and totals
- See status updates (activity log - sanitized)
- Cannot see internal notes or full activity details

---

### JobItem

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View** | ✅ | ✅ | 👤 (items on their jobs) |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ✅ | 🔒 |
| **Delete** | ✅ | ✅ | 🔒 |
| **Change Status** | ✅ | ✅ | 🔒 |

**Field-Level Restrictions:**

| Field | Owner | Staff | Customer Portal |
|-------|-------|-------|-----------------|
| item_type | ✅ | ✅ | 📖 |
| description | ✅ | ✅ | 📖 |
| quantity | ✅ | ✅ | 📖 |
| unit_price | ✅ | ✅ | 📖 |
| line_total | 📖 | 📖 | 📖 |
| status | ✅ | ✅ | 📖 |
| notes | ✅ | ✅ | 🔒 (internal) |

---

### JobNote

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View** | ✅ | ✅ | 🔒 (internal notes) |
| **Create** | ✅ | ✅ | 🔒 |
| **Delete** | ✅ | ✅ | 🔒 |

**Notes:** Job notes are internal-only. Customer communication should be handled separately (future: messaging feature).

---

### JobActivity

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **View Sanitized** | ✅ | ✅ | 👤 (status changes only) |

**Customer Portal Activity View:**
- Can see: created, status_changed, completed
- Cannot see: note_added, item pricing changes, internal activities

---

### Invoice

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **View Own** | ✅ | ✅ | 👤 (invoices for their account) |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ⚠️ (not after sent) | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |
| **Change Status** | ✅ | ✅ | 🔒 |
| **Mark Paid** | ✅ | ✅ | 🔒 |
| **Record Payment** | ✅ | ✅ | 🔒 |
| **Download PDF** | ✅ | ✅ | 👤 |

**Field-Level Restrictions:**

| Field | Owner | Staff | Customer Portal |
|-------|-------|-------|-----------------|
| customer_id | ✅ | ✅ | 🔒 |
| job_id | ✅ | ✅ | 🔒 |
| line_items | ✅ | ⚠️ | 📖 |
| total | 📖 | 📖 | 📖 |
| status | ✅ | ✅ | 📖 |
| due_date | ✅ | ✅ | 📖 |
| notes | ✅ | ✅ | 📖 |
| amount_paid | ✅ | ✅ | 📖 |
| paid_date | 📖 | 📖 | 📖 |

**Staff Invoice Edit Restrictions:**
- Cannot edit invoices with status "sent" or "paid" without Owner approval
- Can edit draft invoices freely

---

### Employee

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ⚠️ (names only) | 🔒 |
| **View Own** | ✅ | 👤 | 🔒 |
| **Create** | ✅ | 🔒 | 🔒 |
| **Edit** | ✅ | 👤 (limited) | 🔒 |
| **Delete/Deactivate** | ✅ | 🔒 | 🔒 |

**Field-Level Restrictions:**

| Field | Owner | Staff | Customer Portal |
|-------|-------|-------|-----------------|
| name | ✅ | 📖 | 🔒 |
| hourly_rate | ✅ | 🔒 | 🔒 |
| is_active | ✅ | 🔒 | 🔒 |

**Notes:** Staff cannot see other employees' pay rates. Only Owner has full employee management.

---

### TimeLog

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | 🔒 | 🔒 |
| **View Own** | ✅ | 👤 | 🔒 |
| **Create (Clock Action)** | ✅ | 👤 | 🔒 |
| **Edit** | ✅ | 🔒 | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |

**Staff Time Clock Access:**
- Can only clock in/out for themselves
- Cannot modify past entries
- Cannot view other employees' time logs

---

### PayrollTransaction

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | 🔒 | 🔒 |
| **View Own** | ✅ | 👤 | 🔒 |
| **Create** | ✅ | 🔒 | 🔒 |
| **Edit** | ✅ | 🔒 | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |
| **View Reports** | ✅ | 🔒 | 🔒 |

**Notes:** Only Owner can manage payroll. Staff can view their own balance and transaction history.

---

### SalesEntry / ExpenseEntry

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View** | ✅ | 📖 | 🔒 |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ⚠️ (own entries, same day) | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |
| **View Summary** | ✅ | 📖 | 🔒 |

**Staff Financial Entry Restrictions:**
- Can add sales and expenses
- Can edit only their own entries from the current day
- Cannot delete entries
- Can view summary reports (read-only)

---

### Task

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ✅ | 🔒 |
| **Delete** | ✅ | ✅ | 🔒 |
| **Toggle Complete** | ✅ | ✅ | 🔒 |

**Notes:** Tasks are internal workflow items, not visible to customers.

---

### AIResponse

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **Generate** | ✅ | ✅ | 🔒 |
| **View History** | ✅ | ✅ | 🔒 |

**Notes:** AI tools are internal productivity features.

---

### FundraiserCampaign

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ✅ | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |
| **View Public Store** | ✅ | ✅ | ✅ (public) |

---

### B2BStore

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **Create** | ✅ | ✅ | 🔒 |
| **Edit** | ✅ | ✅ | 🔒 |
| **Delete** | ✅ | 🔒 | 🔒 |
| **Access Own Store** | ✅ | ✅ | 👤 (B2B customers) |

---

### WebstoreOrder

| Action | Owner | Staff | Customer Portal |
|--------|-------|-------|-----------------|
| **View All** | ✅ | ✅ | 🔒 |
| **View Own** | ✅ | ✅ | 👤 |
| **Create** | ✅ | ✅ | 👤 (via store) |
| **Edit Status** | ✅ | ✅ | 🔒 |

---

## PAGE/ROUTE ACCESS

### Owner Access (All Routes)

| Route | Access | Notes |
|-------|--------|-------|
| `/` (Dashboard) | ✅ | Full dashboard |
| `/customers` | ✅ | Full CRUD |
| `/quotes` | ✅ | Full CRUD |
| `/jobs` | ✅ | Full CRUD |
| `/jobs/:id` | ✅ | Full access |
| `/invoices` | ✅ | Full CRUD |
| `/timeclock` | ✅ | All employees |
| `/payroll` | ✅ | Full access |
| `/productivity` | ✅ | Full access |
| `/financials` | ✅ | Full access |
| `/ai-tools` | ✅ | Full access |
| `/webstores` | ✅ | Full access |
| `/settings` | ✅ | All settings |
| `/users` | ✅ | User management |

---

### Staff Access

| Route | Access | Notes |
|-------|--------|-------|
| `/` (Dashboard) | ✅ | Limited metrics (no financial totals) |
| `/customers` | ✅ | No delete |
| `/quotes` | ✅ | No delete |
| `/jobs` | ✅ | No delete |
| `/jobs/:id` | ✅ | Full access except delete |
| `/invoices` | ⚠️ | Cannot edit sent/paid invoices |
| `/timeclock` | ⚠️ | Own time only |
| `/payroll` | ⚠️ | Own balance only |
| `/productivity` | ✅ | Full access |
| `/financials` | 📖 | Read-only summaries, can add entries |
| `/ai-tools` | ✅ | Full access |
| `/webstores` | ✅ | No delete |
| `/settings` | ⚠️ | Own profile only |
| `/users` | 🔒 | No access |

**Staff Dashboard Modifications:**
- Hide "Today's Revenue" card
- Hide "Overdue Total" amounts
- Show job counts and task counts only

---

### Customer Portal Access

| Route | Access | Notes |
|-------|--------|-------|
| `/portal` (Dashboard) | ✅ | Customer-specific dashboard |
| `/portal/profile` | ✅ | Edit own profile |
| `/portal/quotes` | 📖 | View and approve/decline |
| `/portal/jobs` | 📖 | View status only |
| `/portal/invoices` | 📖 | View and pay |
| `/portal/orders` | 👤 | B2B/Fundraiser orders |
| `/store/:id` | ✅ | B2B store access (if authorized) |

**Customer Portal Dashboard Shows:**
- Active quotes pending approval
- Current job statuses
- Outstanding invoices
- Order history

**Routes NOT accessible to Customer Portal:**
- `/customers` (internal)
- `/timeclock` (internal)
- `/payroll` (internal)
- `/productivity` (internal)
- `/financials` (internal)
- `/ai-tools` (internal)
- `/webstores` (admin)
- `/settings` (admin)
- `/users` (admin)

---

## PERMISSIONS MATRIX SUMMARY

### By Data Type

| Data Type | Owner | Staff | Customer Portal |
|-----------|-------|-------|-----------------|
| Customer | CRUD | CRU | R (own) |
| Quote | CRUD | CRU | R (own) + Approve |
| Job | CRUD | CRU | R (own) |
| JobItem | CRUD | CRUD | R (own) |
| JobNote | CRUD | CRUD | 🔒 |
| JobActivity | R | R | R (sanitized) |
| Invoice | CRUD | CRU* | R (own) |
| Employee | CRUD | R (own) | 🔒 |
| TimeLog | CRUD | C (own) R (own) | 🔒 |
| PayrollTransaction | CRUD | R (own) | 🔒 |
| SalesEntry | CRUD | CR | 🔒 |
| ExpenseEntry | CRUD | CR | 🔒 |
| Task | CRUD | CRUD | 🔒 |
| AIResponse | CR | CR | 🔒 |
| FundraiserCampaign | CRUD | CRU | 🔒 |
| B2BStore | CRUD | CRU | R (own store) |
| WebstoreOrder | CRUD | CRU | CR (own) |

*Staff Invoice restrictions: Cannot edit after "sent" status

---

## FUTURE EXPANSION NOTES

### Additional Roles (Future)

| Role | Description |
|------|-------------|
| **Admin** | Like Owner but cannot delete business data |
| **Designer** | Staff + additional access to design tools |
| **Production** | Staff focused on job items and status |
| **Sales** | Staff + full customer and quote access |
| **Accountant** | Staff + full financial access, limited operations |

### Feature-Specific Permissions (Future)

| Feature | Permission Type |
|---------|-----------------|
| **Proof Approval** | Customer can approve/reject proofs |
| **File Uploads** | Staff can upload, Customer can view |
| **Messaging** | Bidirectional communication |
| **Scheduling** | Staff can view/edit assigned jobs |
| **Reporting** | Role-based report access |
| **API Access** | Token-based for integrations |

### Implementation Recommendations

1. **Authentication**
   - JWT-based authentication
   - Session management
   - Password policies
   - Two-factor authentication (Owner accounts)

2. **Authorization**
   - Role stored in User record
   - Middleware checks on each route
   - Field-level filtering in API responses
   - Audit logging for sensitive actions

3. **Customer Portal**
   - Separate authentication flow
   - Magic link or password-based
   - Linked to Customer record via email
   - Limited API surface

4. **Multi-Tenancy (Future)**
   - Organization-level isolation
   - Cross-organization Owner access
   - Franchise support

---

## DATA ISOLATION RULES

### Customer Portal Data Isolation

Customer Portal users can ONLY access data where:

```
Customer.id = LoggedInUser.customer_id
```

This applies to:
- Quotes: `quote.customer_id = user.customer_id`
- Jobs: `job.customer_id = user.customer_id`
- Invoices: `invoice.customer_id = user.customer_id`
- WebstoreOrders: `order.store_id` in user's authorized stores

### Staff Data Isolation

Staff can access all customer data but:
- TimeLog: `timelog.employee_id = user.employee_id`
- PayrollTransaction: `transaction.employee_id = user.employee_id`
- Cannot see other staff's pay rates or payroll

### Owner Data Isolation

None - full access to all data within the organization.

---

## AUDIT REQUIREMENTS

### Actions Requiring Audit Log

| Action | Logged Fields |
|--------|---------------|
| User Login | user_id, timestamp, IP, success/fail |
| User Logout | user_id, timestamp |
| Password Change | user_id, timestamp |
| Role Change | user_id, old_role, new_role, changed_by |
| Customer Delete | customer_id, deleted_by, timestamp |
| Invoice Status Change | invoice_id, old_status, new_status, changed_by |
| Payment Recorded | invoice_id, amount, recorded_by |
| Payroll Transaction | transaction_id, employee_id, amount, created_by |
| Employee Deactivation | employee_id, deactivated_by |
| Quote Approval (Customer) | quote_id, customer_user_id |

### Retention

- Audit logs: 7 years (financial compliance)
- User activity: 1 year
- Failed logins: 90 days

---

## IMPLEMENTATION CHECKLIST

### Phase 1: Basic Auth
- [ ] User model with role field
- [ ] Login/logout endpoints
- [ ] JWT token generation
- [ ] Auth middleware
- [ ] Password hashing

### Phase 2: Role-Based Access
- [ ] Route-level guards
- [ ] Role checking middleware
- [ ] Staff restrictions
- [ ] Owner full access

### Phase 3: Customer Portal
- [ ] Separate user type
- [ ] Customer-user linking
- [ ] Portal routes
- [ ] Data isolation queries

### Phase 4: Fine-Grained Permissions
- [ ] Field-level filtering
- [ ] Status-based restrictions
- [ ] Audit logging
- [ ] Time-based restrictions

### Phase 5: Advanced Features
- [ ] Two-factor auth
- [ ] API tokens
- [ ] SSO integration
- [ ] Multi-tenancy
