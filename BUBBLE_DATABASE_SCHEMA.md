# Sign Guy AI - Database Schema (Current)

> Last updated: Feb 2026. Reflects multi-tenant SaaS architecture with Unified Productivity, Payroll Worksheet, Signatures/Drawings, and Object Storage.

## MULTI-TENANCY

Every business-data collection includes a `tenant_id` field for data isolation. All queries MUST filter by `tenant_id`.

---

## OPTION SETS (ENUMS)

### CustomerStatus
| Display | Value |
|---------|-------|
| Lead | lead |
| Active | active |
| Inactive | inactive |

### QuoteStatus
| Display | Value |
|---------|-------|
| Draft | draft |
| Sent | sent |
| Approved | approved |
| Declined | declined |

### JobStatus
| Display | Value |
|---------|-------|
| Quote | quote |
| Approved | approved |
| In Progress | in_progress |
| Completed | completed |
| Invoiced | invoiced |
| Archived | archived |

### JobActivityType
| Display | Value |
|---------|-------|
| Created | created |
| Status Changed | status_changed |
| Quote Converted | quote_converted |
| Invoice Created | invoice_created |
| Item Added | item_added |
| Item Updated | item_updated |
| Item Deleted | item_deleted |
| Note Added | note_added |
| Completed | completed |
| Archived | archived |
| Unarchived | unarchived |

### JobItemStatus
| Display | Value |
|---------|-------|
| Pending | pending |
| In Production | in_production |
| Done | done |

### JobItemType
| Display | Value |
|---------|-------|
| Banner | banner |
| Yard Sign | yard_sign |
| Decal | decal |
| Wrap | wrap |
| Install | install |
| Design | design |
| Vehicle Graphics | vehicle_graphics |
| Window Graphics | window_graphics |
| Dimensional Letters | dimensional_letters |
| Monument Sign | monument_sign |
| Other | other |

### InvoiceStatus
| Display | Value |
|---------|-------|
| Draft | draft |
| Sent | sent |
| Paid | paid |
| Overdue | overdue |

### PayrollTransactionType
| Display | Value |
|---------|-------|
| Earnings | earnings |
| Advance | advance |
| Payment | payment |

### ExpenseCategory
| Display | Value |
|---------|-------|
| Materials | materials |
| Labor | labor |
| Equipment | equipment |
| Utilities | utilities |
| Rent | rent |
| Insurance | insurance |
| Cell Phone | cell_phone |
| Garbage | garbage |
| Printing Supplies | printing_supplies |
| Meals | meals |
| Entertainment | entertainment |
| Donations | donations |
| Office Supplies | office_supplies |
| Apparel | apparel |
| Vehicle | vehicle |
| Advertising | advertising |
| Legal | legal |
| Repairs | repairs |
| Taxes | taxes |
| Travel | travel |
| Other | other |

### UserRole
| Display | Value |
|---------|-------|
| Owner | owner |
| Admin | admin |
| Staff | staff |

### TenantPlan
| Display | Value |
|---------|-------|
| Starter | starter |
| Pro | pro |
| Business | business |
| Founders Edition | founders_edition |

### PaymentMethod
| Display | Value |
|---------|-------|
| Cash | cash |
| Check | check |
| Card | card |
| Bank Transfer | bank_transfer |
| Other | other |

### MessageType
| Display | Value |
|---------|-------|
| Text | text |
| Image | image |
| File | file |
| System | system |

### ProofStatus
| Display | Value |
|---------|-------|
| Pending | pending |
| Approved | approved |
| Revision Requested | revision_requested |
| Rejected | rejected |

### AppointmentType
| Display | Value |
|---------|-------|
| Consultation | consultation |
| Installation | installation |
| Pickup | pickup |
| Site Survey | site_survey |
| Other | other |

### AppointmentStatus
| Display | Value |
|---------|-------|
| Scheduled | scheduled |
| Confirmed | confirmed |
| In Progress | in_progress |
| Completed | completed |
| Cancelled | cancelled |
| No Show | no_show |

### WebstoreType
| Display | Value |
|---------|-------|
| B2B | b2b |
| Fundraiser | fundraiser |
| Creator | creator |

### WebstoreStatus
| Display | Value |
|---------|-------|
| Active | active |
| Paused | paused |
| Completed | completed |
| Archived | archived |

### WebstoreOrderStatus
| Display | Value |
|---------|-------|
| Pending | pending |
| Processing | processing |
| Ready | ready |
| Shipped | shipped |
| Delivered | delivered |
| Cancelled | cancelled |

### Pricing Enums
- **PricingCategory**: promotional, cut_vinyl, services, digital_print, rigid_signs, apparel, vehicle_graphics, custom
- **ServiceType**: design, installation, removal, site_survey, consultation, travel, other_labor
- **ApparelType**: tshirt, hoodie, hat, polo, tank, longsleeve, jacket, other
- **TransferType**: htv, screen_print, dtf, sublimation, embroidery
- **VinylType**: oracal_651, oracal_751, oracal_951, avery_hp750, reflective, specialty, custom
- **PrintMaterial**: banner_13oz, banner_18oz, vinyl_adhesive, poster_paper, canvas, backlit, perforated, custom
- **SubstrateType**: coroplast_4mm, coroplast_10mm, aluminum_040/063/080, pvc_3mm/6mm, acrylic, dibond, mdo, custom
- **VehicleType**: car_sedan, car_suv, pickup, van_mini, van_cargo, van_sprinter, box_truck_12ft/16ft/24ft, trailer, semi, other
- **CoverageType**: spot, partial, half, full
- **PromoProductType**: magnets, yard_signs, license_plates, stickers, branded_items, custom

---

## DATA TYPES

### Tenant
**Collection:** `tenants`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| name | text | YES | Business name |
| slug | text | YES | URL-safe identifier |
| owner_email | text | YES | Primary contact |
| phone, address, city, state, zip_code, country, website | text | NO | Business details |
| logo_url | text | NO | Uploaded logo |
| plan | TenantPlan | YES | Subscription tier |
| product_line | text | YES | "os", "webstores", or "ai_studio" |
| is_active | bool | YES | Account status |
| is_founder | bool | NO | Founders Edition flag |
| founder_number | int | NO | Sequential founder number |
| time_tracking_settings | object | NO | See sub-schema below |
| payroll_settings | object | NO | See sub-schema below |
| employee_portal_settings | object | NO | Portal feature toggles |
| signature_settings | object | NO | Signature feature config |
| subscription_status | text | NO | "active", "cancelled", etc. |
| subscription_ended_at | text | NO | ISO timestamp |
| created_at | text | YES | ISO 8601 |
| updated_at | text | YES | ISO 8601 |

**Sub-schema: `time_tracking_settings`**
```json
{
  "track_per_job": true,
  "track_per_line_item": false,
  "enable_employee_portal": false,
  "enable_kiosk_mode": false,
  "auto_suggest_on_status_change": true
}
```

**Sub-schema: `payroll_settings`**
```json
{
  "default_cycle": "weekly",        // "weekly" or "biweekly"
  "pay_week_start_day": "monday"    // Day name (lowercase)
}
```

---

### User
**Collection:** `users`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| email | text | YES | Login email (unique per tenant) |
| hashed_password | text | YES | bcrypt hash |
| full_name | text | YES | Display name |
| company_name | text | NO | |
| role | UserRole | YES | owner/admin/staff |
| tenant_id | text | YES | Tenant isolation |
| is_active | bool | YES | Can login |
| is_founder | bool | NO | |
| created_at | text | YES | ISO 8601 |

---

### Customer
**Collection:** `customers`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| name | text | YES | Customer full name |
| company | text | NO | Company/business name |
| phone | text | NO | Phone number |
| email | text | NO | Email address |
| status | CustomerStatus | YES | Default: "lead" |
| notes | text | NO | Free-form notes |
| portal_enabled | bool | NO | Customer portal access |
| portal_password_hash | text | NO | Portal login hash |
| created_at | text | YES | ISO 8601 |
| updated_at | text | YES | ISO 8601 |

**Relationships:** Customer -> Quote (1:many), Customer -> Order (1:many), Customer -> Invoice (1:many)

---

### Quote
**Collection:** `quotes`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| customer_id | text | YES | Link to Customer |
| line_items | array | NO | Embedded QuoteLineItem[] |
| notes | text | NO | |
| status | QuoteStatus | YES | Default: "draft" |
| total | number | YES | CALCULATED from line_items |
| order_id | text | NO | Set when converted to Order |
| created_at | text | YES | ISO 8601 |
| updated_at | text | YES | ISO 8601 |

---

### Order
**Collection:** `orders`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| customer_id | text | YES | Link to Customer |
| name | text | YES | Order/project name |
| description | text | NO | |
| status | JobStatus | YES | Default: "quote" |
| due_date | text | NO | ISO date |
| quote_id | text | NO | Originating Quote |
| invoice_id | text | NO | Generated Invoice |
| subtotal | number | YES | CALCULATED from job tickets |
| is_archived | bool | YES | Soft delete flag |
| created_at | text | YES | ISO 8601 |
| updated_at | text | YES | ISO 8601 |

---

### JobTicket
**Collection:** `job_tickets`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| order_id | text | YES | Parent Order |
| ticket_number | text | NO | Human-readable ticket number |
| item_type | JobItemType | YES | Default: "other" |
| item_name | text | NO | Display name |
| description | text | YES | |
| quantity | number | YES | Default: 1 |
| unit_price | number | YES | Default: 0 |
| line_total | number | YES | CALCULATED: qty x unit_price |
| status | JobItemStatus | YES | Default: "pending" |
| priority | text | NO | |
| assigned_user_id | text | NO | Assigned employee |
| due_date | text | NO | |
| notes | text | NO | |
| workflow_template_id | text | NO | Links to workflow template |
| created_at | text | YES | ISO 8601 |

---

### Invoice
**Collection:** `invoices`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| customer_id | text | YES | Link to Customer |
| order_id | text | NO | Source Order |
| line_items | array | NO | Embedded InvoiceLineItem[] |
| total | number | YES | CALCULATED |
| status | InvoiceStatus | YES | Default: "draft" |
| due_date | text | NO | |
| notes | text | NO | |
| amount_paid | number | YES | Default: 0 |
| paid_date | text | NO | |
| platform_fee_percent | number | NO | Stripe Connect fee |
| created_at | text | YES | ISO 8601 |
| updated_at | text | YES | ISO 8601 |

---

### Employee
**Collection:** `employees`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| name | text | YES | Full name |
| email | text | NO | |
| phone | text | NO | |
| hourly_rate | number | YES | Default: 0 |
| overtime_rate | number | NO | Defaults to 1.5x hourly |
| title | text | NO | Job title |
| manager_name | text | NO | |
| role | text | YES | Default: "staff" |
| is_active | bool | YES | Default: true |
| pin | text | NO | 4-6 digit portal PIN |
| profile_image | text | NO | URL |
| linked_user_id | text | NO | Links to User for portal access |
| created_at | text | YES | ISO 8601 |

---

### TimeclockShift (Primary time record)
**Collection:** `timeclock_shifts`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| employee_id | text | YES | Link to Employee |
| date | text | YES | YYYY-MM-DD |
| clock_in | text | NO | ISO timestamp |
| clock_out | text | NO | ISO timestamp |
| lunch_start | text | NO | ISO timestamp |
| lunch_end | text | NO | ISO timestamp |
| break_minutes | number | NO | Total break/lunch minutes |
| total_hours | number | NO | CALCULATED net hours |
| regular_hours | number | NO | Hours up to 8 (or OT threshold) |
| overtime_hours | number | NO | Hours beyond threshold |
| status | text | NO | "working", "on_break", "completed" |
| current_break_start | text | NO | Active break timestamp |
| notes | text | NO | |
| is_manual | bool | NO | Admin-created shift |
| created_at | text | YES | ISO 8601 |
| updated_at | text | NO | ISO 8601 |

**Key concept:** `timeclock_shifts` is the primary time record. Raw `timelogs` (start_work/break_start/etc.) are backfilled into shift records for the payroll worksheet.

---

### TimeLog (Raw clock actions)
**Collection:** `timelogs`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| employee_id | text | YES | Link to Employee |
| action | text | YES | start_work/break_start/break_end/end_work |
| timestamp | text | YES | ISO 8601 |

---

### PayrollTransaction (Adjustments)
**Collection:** `payroll_transactions`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| employee_id | text | YES | Link to Employee |
| type | PayrollTransactionType | YES | earnings/advance/payment |
| amount | number | YES | Dollar amount |
| description | text | NO | |
| date | text | YES | YYYY-MM-DD |
| created_at | text | YES | ISO 8601 |

---

### PayrollSignoff
**Collection:** `payroll_signoffs`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| employee_id | text | YES | Link to Employee |
| week_start | text | YES | YYYY-MM-DD |
| period_end | text | NO | For biweekly periods |
| reviewed_by | text | NO | Reviewer name |
| review_date | text | NO | ISO timestamp |
| approved_by | text | NO | Approver name |
| approval_date | text | NO | ISO timestamp |
| payroll_notes | text | NO | |
| updated_at | text | YES | ISO 8601 |

---

### PayrollHours (Manual/Legacy hours)
**Collection:** `payroll_hours`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| employee_id | text | YES | Link to Employee |
| date | text | YES | YYYY-MM-DD |
| hours | number | YES | Manual hours logged |
| description | text | NO | |
| job_id | text | NO | Optional job link |
| job_name | text | NO | Cached job name |
| task_type | text | YES | general/design/production/installation/admin |
| hourly_rate | number | YES | Rate at time of entry |
| gross_pay | number | YES | CALCULATED |
| is_manual | bool | YES | Always true |
| created_at | text | YES | ISO 8601 |

**Legacy handling:** Older `payroll_hours` entries that fall outside the current pay period are surfaced in the Payroll Worksheet as "legacy manual entries" with resolution options (keep, convert, exclude).

---

### EmployeeSchedule
**Collection:** `employee_schedules`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | |
| employee_id | text | YES | |
| day_of_week | text | YES | monday-sunday |
| date | text | NO | Specific date override |
| start_time | text | NO | HH:MM |
| end_time | text | NO | HH:MM |
| is_off | bool | NO | Day off flag |
| notes | text | NO | |

---

### OrderDrawing
**Collection:** `order_drawings`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| order_id | text | YES | Parent Order |
| parent_type | text | YES | "order", "job_ticket", "uploaded_image" |
| parent_id | text | NO | ID of the parent record |
| job_ticket_id | text | NO | Specific ticket link |
| uploaded_image_id | text | NO | For image markups |
| drawing_type | text | YES | sketch/markup/measurement_note/install_note/layout_note/signature/other |
| label | text | NO | |
| title | text | NO | |
| notes | text | NO | |
| storage_key | text | YES | Object storage key for image data |
| storage_url | text | NO | Presigned URL (cached) |
| status | text | YES | draft/saved/finalized |
| tags | array | NO | String tags |
| requires_attention | bool | NO | |
| created_by | text | NO | User ID |
| created_at | text | YES | ISO 8601 |
| updated_at | text | NO | ISO 8601 |

**Storage:** Drawing image data (PNG) is stored in Emergent Object Storage. The `storage_key` references the object; a presigned URL is generated on read.

---

### Signature
**Collection:** `signatures`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | Tenant isolation |
| parent_record_type | text | YES | quote/proof/order/change_order/install_record/pickup_record/delivery_record/invoice/form/document/work_order |
| parent_record_id | text | YES | ID of signed record |
| order_id | text | NO | Order context |
| job_ticket_id | text | NO | Ticket context |
| signature_type | text | YES | Auto-derived from parent_record_type |
| document_version | text | NO | |
| requires_signature | bool | YES | |
| signer_name | text | NO | |
| signer_role | text | NO | |
| printed_name | text | NO | |
| notes | text | NO | |
| storage_key | text | NO | Object storage key for signature image |
| storage_url | text | NO | Presigned URL |
| status | text | YES | pending/signed/declined/expired |
| signed_at | text | NO | ISO timestamp |
| request_token | text | NO | For public email signature links |
| request_email | text | NO | |
| request_expires_at | text | NO | |
| created_by | text | NO | |
| created_at | text | YES | ISO 8601 |
| updated_at | text | NO | ISO 8601 |

**Signature types (auto-mapped from parent):**
- quote -> quote_acceptance
- proof -> artwork_approval
- order -> order_authorization
- change_order -> change_approval
- install_record -> install_completion
- pickup_record -> pickup_confirmation
- delivery_record -> delivery_confirmation
- invoice -> payment_authorization
- form/document -> terms_acknowledgment

---

### ProductionTask
**Collection:** `production_tasks`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | |
| job_ticket_id | text | YES | Parent ticket |
| order_id | text | NO | |
| title | text | YES | |
| status | text | YES | |
| assigned_to | text | NO | Employee ID |
| priority | text | NO | |
| due_date | text | NO | |
| created_at | text | YES | ISO 8601 |

---

### Task (General)
**Collection:** `tasks`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID primary key |
| tenant_id | text | YES | |
| title | text | YES | |
| description | text | NO | |
| job_id | text | NO | Legacy job link |
| order_id | text | NO | Order link |
| assigned_to | text | NO | Employee ID |
| due_date | text | NO | |
| status | text | NO | |
| priority | text | NO | |
| is_complete | bool | YES | Default: false |
| created_at | text | YES | ISO 8601 |

---

### WorkflowTemplate
**Collection:** `workflow_templates`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID |
| tenant_id | text | YES | |
| name | text | YES | |
| steps | array | YES | Ordered step definitions |
| category | text | NO | |
| is_active | bool | YES | |
| created_at | text | YES | ISO 8601 |

---

### SalesEntry & ExpenseEntry
**Collections:** `sales_entries`, `expense_entries`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID |
| tenant_id | text | YES | |
| date | text | YES | YYYY-MM-DD |
| amount | number | YES | |
| tax_amount (sales only) | number | NO | |
| category (expense only) | ExpenseCategory | YES | |
| description | text | NO | |
| created_at | text | YES | ISO 8601 |

---

### AIResponse
**Collection:** `ai_responses`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | text | YES | UUID |
| tenant_id | text | YES | |
| tool | text | YES | AI tool name |
| input_data | text | YES | JSON string |
| output | text | YES | AI response |
| order_id | text | NO | |
| customer_id | text | NO | |
| credit_cost | number | NO | AI credits consumed |
| created_at | text | YES | ISO 8601 |

---

### Webstore Collections

**`fundraiser_campaigns`**, **`b2b_stores`**, **`webstore_orders`**, **`webstore_products`**

These follow the same pattern as before with added `tenant_id` and Object Storage for product images.

---

### Other Collections

| Collection | Purpose |
|-----------|---------|
| `job_notes` | Notes on orders |
| `job_activities` | Order activity log |
| `job_time_entries` | Per-job time tracking entries |
| `order_files` | Uploaded files/images for orders |
| `conversations` | Customer portal messaging |
| `artwork_proofs` | Proof approval workflow |
| `appointments` | Customer appointments |
| `questionnaires` | Dynamic form builder |
| `questionnaire_responses` | Form submissions |
| `documents` | Document library |
| `email_templates` | Customizable email templates |
| `promo_codes` | Discount codes |
| `backups` | Tenant data backups |
| `digest_settings` | Daily digest email config |

---

## CALCULATED TOTALS

### Quote Total
```
Quote.total = SUM(line_items[].quantity * line_items[].unit_price)
```

### Order Subtotal
```
Order.subtotal = SUM(JobTicket.line_total WHERE order_id = Order.id)
JobTicket.line_total = quantity * unit_price
```

### Invoice Total
```
Invoice.total = SUM(line_items[].quantity * line_items[].unit_price)
Invoice.balance_due = total - amount_paid
```

### Payroll Worksheet (Per Employee Per Period)
```
For each day in date range:
  shift = timeclock_shifts WHERE employee_id AND date
  reg_hours = shift.regular_hours
  ot_hours = shift.overtime_hours
  day_pay = (reg_hours * hourly_rate) + (ot_hours * overtime_rate)

period_shift_pay = SUM(day_pay for all days)
period_adjustments = SUM(payroll_transactions in date range)
  signed_total = earnings - advances - payments
period_legacy = SUM(payroll_hours entries if included_in_totals)
FINAL_PAY = period_shift_pay + signed_total_adjustments + legacy_hours_pay
```

### Payroll Balance (All-Time Per Employee)
```
total_earnings = SUM(PayrollTransaction.amount WHERE type = "earnings")
total_advances = SUM(PayrollTransaction.amount WHERE type = "advance")
total_payments = SUM(PayrollTransaction.amount WHERE type = "payment")
balance = total_earnings - total_advances - total_payments
```

---

## MONGODB COLLECTIONS MAPPING

| Data Type | Collection |
|-----------|-----------|
| Tenant | tenants |
| User | users |
| Customer | customers |
| Quote | quotes |
| Order | orders |
| JobTicket | job_tickets |
| OrderNote | job_notes |
| OrderActivity | job_activities |
| Invoice | invoices |
| Employee | employees |
| TimeclockShift | timeclock_shifts |
| TimeLog | timelogs |
| PayrollTransaction | payroll_transactions |
| PayrollSignoff | payroll_signoffs |
| PayrollHours | payroll_hours |
| EmployeeSchedule | employee_schedules |
| OrderDrawing | order_drawings |
| Signature | signatures |
| ProductionTask | production_tasks |
| Task | tasks |
| WorkflowTemplate | workflow_templates |
| SalesEntry | sales_entries |
| ExpenseEntry | expense_entries |
| AIResponse | ai_responses |
| FundraiserCampaign | fundraiser_campaigns |
| B2BStore | b2b_stores |
| WebstoreOrder | webstore_orders |
| WebstoreProduct | webstore_products |
| OrderFile | order_files |
| JobTimeEntry | job_time_entries |
| Conversation | conversations |
| ArtworkProof | artwork_proofs |
| Appointment | appointments |
| Questionnaire | questionnaires |
| Document | documents |
| EmailTemplate | email_templates |

---

## RELATIONSHIP DIAGRAM

```
                        ┌──────────┐
                        │  Tenant  │
                        └────┬─────┘
                             │ owns all data
         ┌───────────────────┼───────────────────────────────────┐
         ▼                   ▼                                   ▼
   ┌──────────┐        ┌──────────┐                        ┌──────────┐
   │ Customer │        │   User   │                        │ Employee │
   └────┬─────┘        └──────────┘                        └────┬─────┘
        │ 1:many                                                │ 1:many
   ┌────┼──────┬───────────┐                    ┌───────────────┼────────────────┐
   ▼    ▼      ▼           ▼                    ▼               ▼                ▼
┌──────┐┌─────┐┌────────┐┌────────────┐  ┌──────────┐   ┌────────────┐  ┌───────────┐
│Quote ││Order││Invoice ││Appointments│  │Timeclock │   │  Payroll   │  │ Employee  │
│      ││     ││        ││            │  │  Shifts  │   │Transactions│  │ Schedules │
└──┬───┘└──┬──┘└────────┘└────────────┘  └──────────┘   └────────────┘  └───────────┘
   │       │                                                │
   │       │ 1:many                                  ┌──────┼──────┐
   │  ┌────┼─────┬──────────┬──────────┐             ▼      ▼      ▼
   │  ▼    ▼     ▼          ▼          ▼        ┌────────┐┌──────┐┌───────┐
   │┌────┐┌────┐┌──────┐┌──────────┐┌────────┐ │Payroll ││Payrl ││Legacy │
   ││Job ││Note││Activ-││ Order    ││Signa-  │ │Signoff ││Hours ││Resol- │
   ││Tick││    ││ity   ││Drawings  ││tures   │ │        ││      ││utions │
   ││ets ││    ││      ││(+ Object ││(+ Obj  │ └────────┘└──────┘└───────┘
   │└────┘└────┘└──────┘│ Storage) ││Storage)│
   │                    └──────────┘└────────┘
   │ converts to
   └───────────► Order
```

---

## OBJECT STORAGE

Emergent Object Storage is used for:
- **Order Drawings** (`order_drawings.storage_key`)
- **Signatures** (`signatures.storage_key`)
- **Order Files/Uploads** (`order_files.storage_key`)
- **Tenant Logos** (`tenants.logo_url`)
- **Employee Profile Images** (`employees.profile_image`)
- **Webstore Product Images**

All binary image data is stored externally; MongoDB documents only hold the `storage_key` and optionally a cached `storage_url`.
