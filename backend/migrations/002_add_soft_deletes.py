"""
Migration 002: Add Soft Deletes to Key Collections

This migration adds deleted_at, deleted_by, and deletion_reason fields
to all primary user data collections.

Collections affected:
- customers
- jobs
- invoices
- quotes
- employees
- products
- documents
- users
- tenants
- webstores_v2

Run: python migrations/002_add_soft_deletes.py
"""

import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations.migration_tracker import run_migration, MigrationTracker

# Collections that need soft delete fields
SOFT_DELETE_COLLECTIONS = [
    "customers",
    "jobs",
    "invoices",
    "quotes",
    "employees",
    "products",
    "documents",
    "users",
    "tenants",
    "webstores_v2",
    "webstore_orders_v2",
    "webstore_products",
    "tasks",
    "artwork_proofs",
    "conversations",
]


async def migrate(db):
    """Add soft delete fields to all collections"""
    
    for collection_name in SOFT_DELETE_COLLECTIONS:
        collection = db[collection_name]
        
        # Add deleted_at = None to all documents that don't have it
        result = await collection.update_many(
            {"deleted_at": {"$exists": False}},
            {"$set": {
                "deleted_at": None,
                "deleted_by": None,
                "deletion_reason": None
            }}
        )
        
        print(f"✓ {collection_name}: Updated {result.modified_count} documents")
        
        # Create index on deleted_at for efficient queries
        await collection.create_index(
            [("deleted_at", 1)],
            name=f"idx_{collection_name}_deleted_at",
            sparse=True
        )
        print(f"  - Created deleted_at index")
    
    print("\n✅ Soft delete fields added to all collections")


async def rollback(db):
    """Remove soft delete fields (CAUTION: This removes deletion history)"""
    
    for collection_name in SOFT_DELETE_COLLECTIONS:
        collection = db[collection_name]
        
        # Remove soft delete fields
        await collection.update_many(
            {},
            {"$unset": {
                "deleted_at": "",
                "deleted_by": "",
                "deletion_reason": ""
            }}
        )
        
        # Drop index
        try:
            await collection.drop_index(f"idx_{collection_name}_deleted_at")
        except:
            pass
        
        print(f"✓ {collection_name}: Removed soft delete fields")


async def main():
    """Run the migration"""
    # Load environment
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip('"')
    
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    print("Starting Migration 002: Add Soft Deletes")
    print("=" * 50)
    
    success = await run_migration(
        db=db,
        version="002",
        name="add_soft_deletes",
        migrate_func=migrate,
        rollback_func=rollback
    )
    
    if success:
        print("\n✅ Migration 002 completed successfully!")
    else:
        print("\n❌ Migration 002 failed!")
        sys.exit(1)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
