# User Data Safety Specification - SignGuy AI

## Overview
This document captures the data safety requirements specified by the user for the SignGuy AI application launch. These requirements are **non-negotiable** for production deployment.

---

## 1. Soft Delete Requirements ✅ IMPLEMENTED

### Requirement
All user-facing data must use soft delete instead of permanent deletion.

### Implementation
- **Added `deleted_at` field** to all major collections
- **DELETE endpoints** now set `deleted_at` timestamp instead of removing documents
- **GET endpoints** automatically filter out soft-deleted records
- **Restore capability** available via dedicated restore endpoints

### Collections with Soft Delete
| Collection | Soft Delete | Restore | Filter Active |
|------------|-------------|---------|---------------|
| customers | ✅ | ✅ | ✅ |
| jobs | ✅ | ✅ | ✅ |
| job_items | ✅ | ✅ | ✅ |
| job_notes | ✅ | ✅ | ✅ |
| invoices | ✅ | ✅ | ✅ |
| quotes | ✅ | ✅ | ✅ |
| products | ✅ | ✅ | ✅ |
| webstores_v2 | ✅ | ✅ | ✅ |
| employees | ✅ | ✅ | ✅ |

### API Patterns
```
# Soft delete (default)
DELETE /api/{model}/{id}

# Permanent delete (admin only)
DELETE /api/{model}/{id}?permanent=true

# Restore soft-deleted item
POST /api/{model}/{id}/restore

# List deleted items (admin)
GET /api/{model}/deleted/list

# Include deleted in list
GET /api/{model}?include_deleted=true
```

---

## 2. Database Migration System ✅ IMPLEMENTED

### Requirement
Track database schema changes with versioned migrations.

### Implementation
- **Migration runner script**: `backend/scripts/run_migrations.py`
- **Migrations collection**: Tracks applied migrations by version number
- **Migration files**: Stored in `backend/migrations/` directory

### Running Migrations
```bash
cd /app/backend
python scripts/run_migrations.py
```

### Migration File Format
```python
# backend/migrations/NNNN_description.py
MIGRATION_VERSION = 1
MIGRATION_NAME = "soft_delete_fields"

async def up(db):
    """Apply migration"""
    # Add fields, create indexes, etc.

async def down(db):
    """Rollback migration (optional)"""
    pass
```

---

## 3. Tenant Data Isolation ✅ VERIFIED

### Requirement
Complete data isolation between tenants. No tenant should ever be able to access another tenant's data.

### Implementation
- All database queries include `tenant_id` filter
- Security audit completed with 28 tests passing
- Cross-tenant access tests verified for all API domains

### Test Coverage
- Customers API
- Employees API
- Jobs API
- Tasks API
- Job Items API
- Quotes API
- Invoices API
- Webstores API
- Products API
- Dashboard API
- Payroll API

---

## 4. MongoDB Atlas Backup Strategy (PENDING DOCUMENTATION)

### Requirement
Automated daily backups with tested restore procedure.

### Recommended Configuration
1. **Enable Continuous Backup** in MongoDB Atlas
2. **Point-in-time recovery** retention: 7 days minimum
3. **Daily snapshots** retained for 30 days
4. **Monthly snapshots** retained for 12 months

### Restore Procedure (To Document)
1. Access MongoDB Atlas console
2. Navigate to Backup → Restore
3. Select snapshot or point-in-time
4. Choose target cluster (use staging for testing)
5. Verify data integrity post-restore

---

## 5. Schema Fields for Soft Delete

### Base Soft Delete Fields
```json
{
  "deleted_at": "2026-03-09T15:30:00.000Z",  // null if not deleted
  "deleted_by": "user_id_123",               // who deleted
  "deletion_reason": "User requested"        // optional reason
}
```

### Restore Fields (added on restore)
```json
{
  "restored_at": "2026-03-10T10:00:00.000Z",
  "restored_by": "admin_user_id"
}
```

---

## 6. Data Retention Policy

### Soft-Deleted Records
- **Retained**: 90 days from deletion date
- **After 90 days**: Eligible for permanent deletion by admin
- **Admin Review**: Required before permanent deletion

### Audit Trail
- All deletions logged with timestamp, user, and reason
- Restoration events logged similarly

---

## Change Log

| Date | Change | Status |
|------|--------|--------|
| Mar 2026 | Initial soft delete implementation | ✅ Complete |
| Mar 2026 | Migration system created | ✅ Complete |
| Mar 2026 | Tenant isolation verified | ✅ Complete |
| Mar 2026 | Backup/restore documentation | 🔄 Pending |

---

## Next Steps

1. **Document backup procedure** with MongoDB Atlas screenshots
2. **Test restore process** in staging environment
3. **Create admin UI** for viewing/restoring deleted records
4. **Implement 90-day cleanup job** for permanently deleting old soft-deleted records

---

*Last Updated: March 2026*
