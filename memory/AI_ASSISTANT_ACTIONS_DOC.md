# AI Assistant Structured Actions

**Created:** December 2025  
**File:** `/app/backend/services/ai_assistant_actions.py`

---

## Overview

The AI Assistant now supports structured database actions that allow it to create, update, and manage data on behalf of users. All actions are:

- **Tenant scoped** - Actions only affect the user's tenant data
- **Permission checked** - User must have the required permission
- **Confirmation required** for destructive changes
- **Audit logged** - Every action is recorded in `ai_action_audit` collection

---

## Supported Actions

| Action | Description | Requires Confirmation |
|--------|-------------|----------------------|
| `create_job` | Create a new job | No |
| `update_job_status` | Change job status | **Yes** |
| `create_calendar_event` | Create calendar event | No |
| `add_material` | Add material to inventory | No |
| `update_material_cost` | Update material cost | **Yes** |
| `create_invoice` | Create new invoice | **Yes** |
| `assign_employee` | Assign employee to job | **Yes** |
| `log_time_entry` | Log time entry | No |
| `categorize_expense` | Categorize/update expense | No |

---

## API Endpoints

### Execute Action
```
POST /api/ai/assistant/action
```

**Request:**
```json
{
  "action_type": "create_job",
  "parameters": {
    "name": "Vehicle Wrap - Company Van",
    "customer_name": "ABC Corp",
    "category": "Vehicle Wrap",
    "total": 2500.00
  },
  "confirmed": false
}
```

**Response (Success):**
```json
{
  "action_id": "uuid",
  "action_type": "create_job",
  "status": "executed",
  "result": {
    "job_id": "uuid",
    "name": "Vehicle Wrap - Company Van",
    "message": "Job 'Vehicle Wrap - Company Van' created successfully"
  },
  "audit_id": "uuid"
}
```

**Response (Needs Confirmation):**
```json
{
  "action_id": "uuid",
  "action_type": "update_job_status",
  "status": "pending_confirmation",
  "confirmation_required": true,
  "confirmation_message": "Are you sure you want to change Test Job status to 'completed'?",
  "audit_id": "uuid"
}
```

### Confirm/Cancel Action
```
POST /api/ai/assistant/action/confirm
```

**Request:**
```json
{
  "action_id": "uuid",
  "confirm": true
}
```

### Get Audit Log
```
GET /api/ai/assistant/actions/audit?limit=50&action_type=create_job
```

### Get Pending Actions
```
GET /api/ai/assistant/actions/pending
```

### Get Available Action Types
```
GET /api/ai/assistant/actions/types
```

---

## Permission Matrix

| Action | Required Permission |
|--------|-------------------|
| create_job | `jobs:edit` |
| update_job_status | `jobs:edit` |
| create_calendar_event | `jobs:edit` |
| add_material | `settings:manage` |
| update_material_cost | `settings:manage` |
| create_invoice | `invoices:edit` |
| assign_employee | `employees:manage` |
| log_time_entry | `time_clock:manage` |
| categorize_expense | `financials:manage` |

**Role Requirements:**
- `OWNER` role has all permissions
- `ADMIN` role has most permissions except settings:manage and financials:manage
- `STAFF` role has limited permissions

---

## Audit Log Schema

Collection: `ai_action_audit`

```json
{
  "id": "uuid",
  "tenant_id": "string",
  "user_id": "string",
  "action_id": "uuid",
  "action_type": "create_job|update_job_status|...",
  "parameters": {...},
  "status": "pending_confirmation|confirmed|executed|cancelled|failed",
  "result": {...},
  "error": "string|null",
  "source": "ai_assistant",
  "created_at": "ISO datetime"
}
```

---

## Action Parameters

### create_job
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Job name |
| customer_id | string | No | Customer ID |
| customer_name | string | No | Customer name |
| category | string | No | Job category |
| description | string | No | Job description |
| due_date | string | No | Due date (ISO) |
| priority | string | No | normal/high/urgent |
| total | number | No | Estimated total |

### update_job_status
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | Job ID to update |
| status | string | Yes | pending/in_progress/production/completed/on_hold/cancelled |

### create_calendar_event
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| title | string | Yes | Event title |
| start_time | string | Yes | Start time (ISO) |
| end_time | string | No | End time (ISO) |
| all_day | boolean | No | Is all day event |
| event_type | string | No | Event type |
| location | string | No | Location |
| job_id | string | No | Related job ID |

### add_material
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Material name |
| category | string | No | Category |
| sku | string | No | SKU code |
| unit | string | No | Unit of measure |
| cost | number | No | Unit cost |
| price | number | No | Selling price |
| quantity | number | No | Initial quantity |
| supplier | string | No | Supplier name |

### update_material_cost
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| material_id | string | Yes | Material ID |
| cost | number | Yes | New cost |

### create_invoice
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| customer_id | string | No | Customer ID |
| customer_name | string | No | Customer name |
| job_id | string | No | Related job |
| line_items | array | No | Invoice line items |
| tax_rate | number | No | Tax rate % |
| due_date | string | No | Due date (ISO) |
| notes | string | No | Invoice notes |

### assign_employee
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | Job ID |
| employee_id | string | Yes | Employee ID |

### log_time_entry
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| employee_id | string | No | Employee ID |
| employee_name | string | No | Employee name |
| job_id | string | No | Job ID |
| job_name | string | No | Job name |
| date | string | No | Date (YYYY-MM-DD) |
| hours | number | Yes | Hours worked |
| description | string | No | Work description |
| billable | boolean | No | Is billable |

### categorize_expense
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| expense_id | string | Yes | Expense ID |
| category | string | Yes | New category |

---

## Test Results

All 17 tests passing:
- Permission mapping tests (3)
- Create job tests (2)
- Update job status tests (2)
- Tenant scoping tests (1)
- Audit logging tests (2)
- All action type tests (7)

Test file: `/app/backend/tests/test_ai_assistant_actions.py`

---

*Documentation generated December 2025*
