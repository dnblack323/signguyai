# SignGuy AI - Data Safety & Launch Readiness Documentation

## Document Version: 1.0
## Last Updated: March 2026

---

# 1. PERSISTENT USER DATA INVENTORY

## Critical Collections (Require Soft Delete + Tenant Isolation)

| Collection | Doc Count | Has tenant_id | Soft Delete Status | Priority |
|------------|-----------|---------------|-------------------|----------|
| customers | 133 | ✅ | IMPLEMENTING | P0 |
| jobs | 95 | ✅ | IMPLEMENTING | P0 |
| invoices | 52 | ✅ | IMPLEMENTING | P0 |
| quotes | 29 | ✅ | IMPLEMENTING | P0 |
| employees | 25 | ✅ | IMPLEMENTING | P0 |
| products | 51 | ✅ | IMPLEMENTING | P0 |
| documents | 17 | ✅ | IMPLEMENTING | P1 |
| users | 91 | ✅ | IMPLEMENTING | P0 |
| tenants | 40 | N/A (is root) | IMPLEMENTING | P0 |

## Supporting Collections (Require Tenant Isolation Fix)

| Collection | Doc Count | Has tenant_id | Action Needed |
|------------|-----------|---------------|---------------|
| job_items | 52 | ❌ | ADD tenant_id |
| job_activities | 104 | ❌ | ADD tenant_id |
| job_notes | 5 | ❌ | ADD tenant_id |
| webstores_v2 | 33 | ❌ | ADD tenant_id |
| webstore_orders_v2 | 16 | ❌ | ADD tenant_id |
| webstore_products | 44 | ❌ | ADD tenant_id |
| conversation_messages | 15 | ❌ | ADD tenant_id |
| timelogs | 39 | ❌ | ADD tenant_id |

## Reference/System Collections (Lower Priority)

| Collection | Notes |
|------------|-------|
| ai_history | Has tenant_id ✅ |
| ai_usage_logs | Has tenant_id ✅ |
| credit_transactions | Has tenant_id ✅ |
| payment_transactions | Has tenant_id ✅ |
| magic_links | Session data, can expire |
| subscriptions | Billing data |

---

# 2. DEPLOYMENT DATA PROTECTION

## Current Architecture

```
┌─────────────────────────────────────────────────────┐
│                  DEPLOYMENT                          │
├─────────────────────────────────────────────────────┤
│  Application Code (FastAPI + React)                  │
│  ├── /app/backend (Python code)                      │
│  ├── /app/frontend (React code)                      │
│  └── Deployed via Emergent Platform                  │
├─────────────────────────────────────────────────────┤
│  SEPARATED FROM                                      │
├─────────────────────────────────────────────────────┤
│  MongoDB Database (External)                         │
│  ├── Hosted on MongoDB Atlas                         │
│  ├── Connection via MONGO_URL env var               │
│  └── Data persists independently of deployments     │
└─────────────────────────────────────────────────────┘
```

## Deployment Safety Confirmation

✅ **Database is EXTERNAL** - MongoDB is not bundled with application
✅ **Connection via environment variable** - MONGO_URL points to Atlas
✅ **No database recreation on deploy** - Code never drops/recreates DB
✅ **Schema is flexible** - MongoDB doesn't require DROP TABLE migrations
✅ **File storage is external** - Images stored via URLs, not in app files

## What CANNOT Cause Data Loss

| Action | Data Safe? | Reason |
|--------|------------|--------|
| Code deployment | ✅ YES | DB is external |
| Server restart | ✅ YES | DB is external |
| New feature added | ✅ YES | Additive migrations only |
| Frontend rebuild | ✅ YES | No DB connection |
| requirements.txt update | ✅ YES | No DB impact |

## What COULD Cause Data Loss (Protected Against)

| Risk | Mitigation |
|------|------------|
| Unfiltered DELETE query | Rate limiting + tenant filter enforcement |
| DROP collection | Admin-only, logged |
| MONGO_URL changed | Env var protection |
| Atlas cluster deleted | Backups (see Section 4) |

---

# 3. MIGRATION VERSIONING STRATEGY

## Migration System Design

```
/app/backend/migrations/
├── __init__.py
├── migration_tracker.py      # Version tracking
├── 001_initial_schema.py     # Base schema
├── 002_add_soft_deletes.py   # Soft delete columns
├── 003_fix_tenant_isolation.py
└── ...
```

## Migration Tracking Collection

```json
{
  "collection": "schema_migrations",
  "document": {
    "version": "003",
    "name": "fix_tenant_isolation",
    "applied_at": "2026-03-09T...",
    "status": "completed",
    "rollback_available": true
  }
}
```

## Migration Rules

1. **NEVER** drop collections
2. **NEVER** remove fields (deprecate first)
3. **ALWAYS** add fields as optional with defaults
4. **ALWAYS** test in preview/staging first
5. **ALWAYS** backup before running migrations

---

# 4. BACKUP & RECOVERY SETUP

## MongoDB Atlas Backup Configuration

### Required Settings (Configure in Atlas Dashboard)

| Setting | Value | Location in Atlas |
|---------|-------|-------------------|
| Continuous Backup | ENABLED | Backup > Configure |
| Snapshot Frequency | Daily | Backup > Policy |
| Snapshot Retention | 7 days | Backup > Policy |
| Weekly Snapshot | ENABLED | Backup > Policy |
| Weekly Retention | 4 weeks | Backup > Policy |
| Monthly Snapshot | ENABLED | Backup > Policy |
| Monthly Retention | 6 months | Backup > Policy |
| Point-in-Time Recovery | ENABLED | Backup > Configure |
| PIT Window | 7 days | Backup > Configure |

### Backup Verification Checklist

- [ ] Daily automated backups enabled
- [ ] Retention policy configured (7d/4w/6m)
- [ ] Point-in-time recovery enabled
- [ ] Test restore performed
- [ ] Restore procedure documented
- [ ] Alert on backup failure configured

## Restore Procedure

### Option 1: Point-in-Time Recovery
```
1. Go to Atlas > Backup > Restore
2. Select "Point in Time"
3. Choose timestamp before incident
4. Restore to new cluster (don't overwrite production)
5. Verify data integrity
6. Update MONGO_URL to new cluster
```

### Option 2: Snapshot Restore
```
1. Go to Atlas > Backup > Snapshots
2. Select snapshot date
3. Click "Restore"
4. Choose target cluster
5. Verify data integrity
```

### Emergency Recovery Contacts
- MongoDB Atlas Support: support.mongodb.com
- Emergent Platform Support: [your contact]

---

# 5. TENANT DATA ISOLATION AUDIT

## Query Patterns That MUST Include tenant_id

```python
# CORRECT ✅
await db.customers.find({"tenant_id": current_user.tenant_id})
await db.jobs.find_one({"id": job_id, "tenant_id": current_user.tenant_id})
await db.invoices.count_documents({"tenant_id": tenant_id, "status": "paid"})

# INCORRECT ❌ - NEVER DO THIS
await db.customers.find({})  # Returns ALL tenants' data!
await db.jobs.find_one({"id": job_id})  # Could return another tenant's job!
```

## Collections Requiring tenant_id Enforcement

| Collection | Current Status | Fix Required |
|------------|----------------|--------------|
| customers | ✅ Enforced | None |
| jobs | ✅ Enforced | None |
| invoices | ✅ Enforced | None |
| quotes | ✅ Enforced | None |
| job_items | ⚠️ Missing | Add to all docs + queries |
| job_activities | ⚠️ Missing | Add to all docs + queries |
| webstores_v2 | ⚠️ Missing | Add to all docs + queries |
| webstore_orders_v2 | ⚠️ Missing | Add to all docs + queries |

---

# 6. STAGING/PREVIEW DEPLOYMENT WORKFLOW

## Current Setup

| Environment | Purpose | URL |
|-------------|---------|-----|
| Preview | Staging/Testing | *.preview.emergentagent.com |
| Production | Live customers | [production domain] |

## Deployment Workflow

```
1. Developer makes changes
         │
         ▼
2. Deploy to PREVIEW environment
         │
         ▼
3. Run automated tests
         │
         ▼
4. Run migration tests (if schema changes)
         │
         ▼
5. Manual QA verification
         │
         ▼
6. Backup production database
         │
         ▼
7. Deploy to PRODUCTION
         │
         ▼
8. Run production migrations
         │
         ▼
9. Verify production health
```

## Pre-Production Checklist

- [ ] All tests pass in preview
- [ ] Migration tested in preview
- [ ] No breaking schema changes
- [ ] Production backup confirmed
- [ ] Rollback plan documented

---

# 7. SOFT DELETE IMPLEMENTATION

## Schema Addition

All soft-deletable collections will have:

```json
{
  "deleted_at": null,          // null = active, timestamp = deleted
  "deleted_by": null,          // user_id who deleted
  "deletion_reason": null      // optional reason
}
```

## Query Modifications

```python
# Default query (excludes deleted)
await db.customers.find({
    "tenant_id": tenant_id,
    "deleted_at": None
})

# Admin view (includes deleted)
await db.customers.find({
    "tenant_id": tenant_id,
    "include_deleted": True  # Special admin flag
})

# Restore deleted record
await db.customers.update_one(
    {"id": customer_id},
    {"$set": {"deleted_at": None, "deleted_by": None}}
)
```

## Collections Getting Soft Delete

1. customers
2. jobs
3. invoices
4. quotes
5. employees
6. products
7. documents
8. users
9. tenants
10. webstores_v2

---

# 8. LAUNCH READINESS CHECKLIST

## Data Persistence ✅
- [x] Database is external (MongoDB Atlas)
- [x] No code deploys can delete data
- [x] MONGO_URL is environment variable
- [ ] Verified: Test deployment doesn't affect data

## Database Migrations ✅
- [x] Migration scripts exist
- [ ] Migration version tracking implemented
- [ ] All migrations tested in preview
- [ ] Rollback procedures documented

## Backups 🔄
- [ ] Atlas backups enabled
- [ ] Daily/weekly/monthly retention set
- [ ] Point-in-time recovery enabled
- [ ] Test restore performed
- [ ] Restore procedure documented

## Soft Deletes 🔄
- [ ] deleted_at added to all key collections
- [ ] All list queries exclude deleted
- [ ] All count queries exclude deleted
- [ ] Admin restore functionality added
- [ ] Admin "view deleted" functionality added

## Tenant Isolation 🔄
- [ ] All collections have tenant_id
- [ ] All queries filter by tenant_id
- [ ] Cross-tenant access tested (should fail)
- [ ] Audit of all database queries complete

## Deployment Workflow ✅
- [x] Preview environment available
- [ ] Preview used as staging gate
- [ ] Production deploy requires preview approval
- [ ] Rollback procedure documented

---

## Document Status: DRAFT
## Next Review: Before Production Launch
