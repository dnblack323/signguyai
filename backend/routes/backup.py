"""
Tenant Data Backup & Restore System
- Export all tenant data as downloadable JSON
- Import/restore from backup JSON
- Owner-only access
- Excludes images/files and sensitive data
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime, timezone
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

backup_router = APIRouter(prefix="/backup", tags=["backup"])


def _is_owner(user) -> bool:
    """Enum-safe owner check.

    ``user.role`` may be a ``UserRole`` str-enum or a plain string depending on
    how the user doc was loaded, so normalize to the underlying value before
    comparing. Avoids brittle ``role != "owner"`` checks that can deny valid
    owners (or pass non-owners) if the role representation changes.
    """
    role = getattr(user, "role", None)
    role_value = getattr(role, "value", role)
    return role_value == "owner"

# Collections to back up (tenant-scoped)
BACKUP_COLLECTIONS = [
    "customers",
    "jobs",
    "job_items",
    "job_activities",
    "job_notes",
    "job_time_entries",
    "invoices",
    "quotes",
    "products",
    "webstores_v2",
    "webstore_products",
    "webstore_orders_v2",
    "documents",
    "document_activities",
    "portal_documents",
    "tasks",
    "employees",
    "promo_codes",
    "pricing_defaults",
    "pricing_templates",
    "production_timelines",
    "conversations",
    "conversation_messages",
    "artwork_proofs",
    "timelogs",
    "expense_entries",
    "sales_entries",
    "payments",
    "payment_transactions",
    "inventory_items",
    "inventory_locations",
    "inventory_lots",
    "inventory_transactions",
    "inventory_cycle_counts",
    "material_requirements",
    "inventory_shortages",
    "inventory_vendors",
    "purchase_orders",
    "pricing_cost_suggestions",
]

# Compatibility aliases expected by legacy checklist naming.
# Export includes these aliases; restore maps them back to canonical collections.
COLLECTION_EXPORT_ALIASES = {
    "jobs": "orders",
    "job_items": "order_items",
    "payment_transactions": "payroll_transactions",
    "timelogs": "timeclock_shifts",
}
COLLECTION_RESTORE_ALIASES = {alias: canonical for canonical, alias in COLLECTION_EXPORT_ALIASES.items()}

# Fields to exclude from backup (sensitive/binary)
EXCLUDE_FIELDS = {"_id", "hashed_password", "logo_url", "banner_image_data", "image_data"}

# Fields that may contain large base64 image data
IMAGE_FIELD_PATTERNS = {"logo_url", "banner_url", "banner_image_data", "image_data", "file_url", "image_url"}


def is_base64_image(val):
    """Check if a string value looks like base64 image data."""
    if not isinstance(val, str):
        return False
    return len(val) > 1000 and (val.startswith("data:image") or val.startswith("/9j/") or val.startswith("iVBOR"))


def clean_doc(doc):
    """Remove _id, sensitive fields, and large base64 image data from a document."""
    cleaned = {}
    for k, v in doc.items():
        if k in EXCLUDE_FIELDS:
            continue
        # Strip base64 images from known image fields
        if k in IMAGE_FIELD_PATTERNS and isinstance(v, str) and len(v) > 1000:
            continue
        # Strip base64 images from lists (e.g. product images array)
        if isinstance(v, list):
            v = [item for item in v if not is_base64_image(item)]
        # Strip base64 from nested dicts (e.g. branding object)
        if isinstance(v, dict):
            v = {dk: dv for dk, dv in v.items() if not (dk in IMAGE_FIELD_PATTERNS and isinstance(dv, str) and len(dv) > 1000) and not is_base64_image(dv)}
        # Skip any remaining large base64 strings
        if is_base64_image(v):
            continue
        cleaned[k] = v
    return cleaned


def setup_backup_routes(app, db, get_current_active_user, UserInDB):

    @backup_router.get("/export")
    async def export_tenant_data(current_user: UserInDB = Depends(get_current_active_user)):
        """Export all tenant data as JSON. Owner only."""
        if not _is_owner(current_user):
            raise HTTPException(status_code=403, detail="Only the account owner can create backups")

        tenant_id = current_user.tenant_id
        backup_data = {
            "backup_version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "collections": {}
        }
        integrity_manifest = {}
        integrity_row_index = []
        integrity_checksums = []

        for collection_name in BACKUP_COLLECTIONS:
            collection = db[collection_name]
            # Most collections use tenant_id, some use other fields
            query = {"tenant_id": tenant_id}
            docs = await collection.find(query, {"_id": 0}).to_list(length=None)

            if not docs:
                # Try without tenant_id filter for collections that may use different field
                # but still belong to this tenant's data (e.g., linked by job_id)
                continue

            cleaned = []
            for doc in docs:
                cleaned_doc = clean_doc(doc)
                # Convert any remaining non-serializable types
                for k, v in cleaned_doc.items():
                    if isinstance(v, datetime):
                        cleaned_doc[k] = v.isoformat()
                    elif isinstance(v, bytes):
                        cleaned_doc[k] = None
                cleaned.append(cleaned_doc)

            if cleaned:
                backup_data["collections"][collection_name] = cleaned
                integrity_manifest[collection_name] = [doc.get("id") for doc in cleaned if doc.get("id")]
                integrity_row_index.extend([
                    {
                        "collection": collection_name,
                        "id": doc.get("id"),
                        "updated_at": doc.get("updated_at"),
                    }
                    for doc in cleaned
                    if doc.get("id")
                ])
                integrity_checksums.extend([
                    {
                        "collection": collection_name,
                        "id": doc.get("id"),
                        "sha256": hashlib.sha256(
                            json.dumps(doc, sort_keys=True, default=str).encode("utf-8")
                        ).hexdigest(),
                    }
                    for doc in cleaned
                    if doc.get("id")
                ])
                alias_name = COLLECTION_EXPORT_ALIASES.get(collection_name)
                if alias_name and alias_name not in backup_data["collections"]:
                    backup_data["collections"][alias_name] = [dict(doc) for doc in cleaned]

        # Ensure legacy compatibility keys always exist, even when source collection is empty.
        for canonical_name, alias_name in COLLECTION_EXPORT_ALIASES.items():
            if alias_name not in backup_data["collections"]:
                source_docs = backup_data["collections"].get(canonical_name, [])
                backup_data["collections"][alias_name] = [dict(doc) for doc in source_docs]

        backup_data["integrity_manifest"] = integrity_manifest
        backup_data["integrity_row_index"] = integrity_row_index
        backup_data["integrity_checksums"] = integrity_checksums

        # Get tenant settings (without logo)
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "logo_url": 0})
        if tenant:
            backup_data["tenant_settings"] = clean_doc(tenant)

        # Record backup timestamp
        await db.tenants.update_one(
            {"id": tenant_id},
            {"$set": {"last_backup_at": datetime.now(timezone.utc).isoformat()}}
        )

        total_records = sum(len(docs) for docs in backup_data["collections"].values())
        backup_data["summary"] = {
            "total_records": total_records,
            "collections_count": len(backup_data["collections"]),
            "collection_counts": {k: len(v) for k, v in backup_data["collections"].items()}
        }

        return backup_data

    @backup_router.get("/status")
    async def get_backup_status(current_user: UserInDB = Depends(get_current_active_user)):
        """Get last backup date to determine if a reminder is needed."""
        tenant = await db.tenants.find_one(
            {"id": current_user.tenant_id},
            {"_id": 0, "last_backup_at": 1}
        )
        last_backup = tenant.get("last_backup_at") if tenant else None
        needs_reminder = True
        if last_backup:
            try:
                last_dt = datetime.fromisoformat(last_backup)
                days_since = (datetime.now(timezone.utc) - last_dt).days
                needs_reminder = days_since >= 7
            except (ValueError, TypeError):
                needs_reminder = True

        return {
            "last_backup_at": last_backup,
            "needs_reminder": needs_reminder
        }

    @backup_router.post("/preview-restore")
    async def preview_restore(
        file: UploadFile = File(...),
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Preview what a restore would do without actually restoring."""
        if not _is_owner(current_user):
            raise HTTPException(status_code=403, detail="Only the account owner can restore backups")

        try:
            content = await file.read()
            backup_data = json.loads(content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid backup file format")

        if "backup_version" not in backup_data or "collections" not in backup_data:
            raise HTTPException(status_code=400, detail="Not a valid SignGuy AI backup file")

        # Build preview
        preview = {
            "backup_version": backup_data.get("backup_version"),
            "created_at": backup_data.get("created_at"),
            "original_tenant_id": backup_data.get("tenant_id"),
            "collections": {}
        }

        total = 0
        for col_name, docs in backup_data["collections"].items():
            resolved_collection = COLLECTION_RESTORE_ALIASES.get(col_name, col_name)
            if resolved_collection not in BACKUP_COLLECTIONS:
                continue
            count = len(docs)
            total += count
            # Count existing records
            existing = await db[resolved_collection].count_documents({"tenant_id": current_user.tenant_id})
            preview["collections"][col_name] = {
                "backup_count": count,
                "existing_count": existing
            }

        preview["total_records"] = total
        return preview

    @backup_router.post("/restore")
    async def restore_tenant_data(
        file: UploadFile = File(...),
        current_user: UserInDB = Depends(get_current_active_user)
    ):
        """Restore tenant data from backup. Owner only. Replaces existing data."""
        if not _is_owner(current_user):
            raise HTTPException(status_code=403, detail="Only the account owner can restore backups")

        try:
            content = await file.read()
            backup_data = json.loads(content.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise HTTPException(status_code=400, detail="Invalid backup file format")

        if "backup_version" not in backup_data or "collections" not in backup_data:
            raise HTTPException(status_code=400, detail="Not a valid SignGuy AI backup file")

        tenant_id = current_user.tenant_id
        restored_counts = {}

        normalized_collections = {}
        for col_name, docs in backup_data["collections"].items():
            resolved_collection = COLLECTION_RESTORE_ALIASES.get(col_name, col_name)
            if resolved_collection not in BACKUP_COLLECTIONS:
                continue

            # Validate payload shape up-front so a malformed file is rejected
            # BEFORE any data is touched (fail-safe, no partial mutation).
            if not isinstance(docs, list):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid backup file: '{col_name}' must be a list of records.",
                )
            if any(not isinstance(d, dict) for d in docs):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid backup file: '{col_name}' contains a non-object record.",
                )

            # Prefer canonical collection payload when both alias and canonical exist.
            if (
                resolved_collection not in normalized_collections
                or col_name == resolved_collection
            ):
                normalized_collections[resolved_collection] = docs

        # Prepare incoming docs (re-assign tenant, strip any leaked _id).
        for col_name, docs in normalized_collections.items():
            for doc in (docs or []):
                doc["tenant_id"] = tenant_id
                doc.pop("_id", None)

        # ── Atomicity: snapshot-and-rollback ──────────────────────────────
        # MongoDB standalone has no multi-document transactions, so we snapshot
        # each target collection's current tenant data BEFORE mutating. If any
        # delete/insert fails mid-way, we restore every touched collection from
        # its snapshot so a partial restore can never destroy the owner's data.
        snapshots = {}
        for col_name in normalized_collections.keys():
            snapshots[col_name] = await db[col_name].find(
                {"tenant_id": tenant_id}, {"_id": 0}
            ).to_list(length=None)

        try:
            for col_name, docs in normalized_collections.items():
                collection = db[col_name]
                # Delete existing tenant data for this collection
                await collection.delete_many({"tenant_id": tenant_id})
                if docs:
                    await collection.insert_many(docs)
                    restored_counts[col_name] = len(docs)
        except Exception as exc:
            logger.error(
                "Restore failed for tenant %s; rolling back %d collections: %s",
                tenant_id, len(snapshots), exc,
            )
            for col_name, original_docs in snapshots.items():
                try:
                    await db[col_name].delete_many({"tenant_id": tenant_id})
                    if original_docs:
                        for d in original_docs:
                            d.pop("_id", None)
                        await db[col_name].insert_many(original_docs)
                except Exception as rollback_exc:  # pragma: no cover - defensive
                    logger.error(
                        "Rollback failed for collection %s (tenant %s): %s",
                        col_name, tenant_id, rollback_exc,
                    )
            raise HTTPException(
                status_code=500,
                detail="Restore failed and was rolled back. Your existing data was not changed.",
            )

        total = sum(restored_counts.values())
        return {
            "success": True,
            "message": f"Restored {total} records across {len(restored_counts)} collections",
            "restored_counts": restored_counts
        }

    app.include_router(backup_router, prefix="/api")
