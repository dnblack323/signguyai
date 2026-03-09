"""
Migration 003: Fix Tenant Isolation

This migration adds tenant_id to collections that are missing it,
backfilling from related records.

Collections affected:
- job_items (get tenant_id from jobs)
- job_activities (get tenant_id from jobs)
- job_notes (get tenant_id from jobs)
- conversation_messages (get tenant_id from conversations)
- timelogs (get tenant_id from employees)
- webstore_orders_v2 (get tenant_id from webstores_v2)
- webstore_products (get tenant_id from webstores_v2)

Run: python migrations/003_fix_tenant_isolation.py
"""

import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from migrations.migration_tracker import run_migration


async def migrate(db):
    """Add tenant_id to collections missing it"""
    
    # 1. job_items - get tenant_id from parent job
    print("Fixing job_items...")
    job_items = await db.job_items.find({"tenant_id": {"$exists": False}}).to_list(10000)
    for item in job_items:
        job = await db.jobs.find_one({"id": item.get("job_id")}, {"tenant_id": 1})
        if job and job.get("tenant_id"):
            await db.job_items.update_one(
                {"_id": item["_id"]},
                {"$set": {"tenant_id": job["tenant_id"]}}
            )
    print(f"✓ job_items: Updated {len(job_items)} documents")
    
    # 2. job_activities - get tenant_id from parent job
    print("Fixing job_activities...")
    activities = await db.job_activities.find({"tenant_id": {"$exists": False}}).to_list(10000)
    for activity in activities:
        job = await db.jobs.find_one({"id": activity.get("job_id")}, {"tenant_id": 1})
        if job and job.get("tenant_id"):
            await db.job_activities.update_one(
                {"_id": activity["_id"]},
                {"$set": {"tenant_id": job["tenant_id"]}}
            )
    print(f"✓ job_activities: Updated {len(activities)} documents")
    
    # 3. job_notes - get tenant_id from parent job
    print("Fixing job_notes...")
    notes = await db.job_notes.find({"tenant_id": {"$exists": False}}).to_list(10000)
    for note in notes:
        job = await db.jobs.find_one({"id": note.get("job_id")}, {"tenant_id": 1})
        if job and job.get("tenant_id"):
            await db.job_notes.update_one(
                {"_id": note["_id"]},
                {"$set": {"tenant_id": job["tenant_id"]}}
            )
    print(f"✓ job_notes: Updated {len(notes)} documents")
    
    # 4. conversation_messages - get tenant_id from parent conversation
    print("Fixing conversation_messages...")
    messages = await db.conversation_messages.find({"tenant_id": {"$exists": False}}).to_list(10000)
    for msg in messages:
        conv = await db.conversations.find_one({"id": msg.get("conversation_id")}, {"tenant_id": 1})
        if conv and conv.get("tenant_id"):
            await db.conversation_messages.update_one(
                {"_id": msg["_id"]},
                {"$set": {"tenant_id": conv["tenant_id"]}}
            )
    print(f"✓ conversation_messages: Updated {len(messages)} documents")
    
    # 5. timelogs - get tenant_id from employee
    print("Fixing timelogs...")
    timelogs = await db.timelogs.find({"tenant_id": {"$exists": False}}).to_list(10000)
    for log in timelogs:
        emp = await db.employees.find_one({"id": log.get("employee_id")}, {"tenant_id": 1})
        if emp and emp.get("tenant_id"):
            await db.timelogs.update_one(
                {"_id": log["_id"]},
                {"$set": {"tenant_id": emp["tenant_id"]}}
            )
    print(f"✓ timelogs: Updated {len(timelogs)} documents")
    
    # 6. webstore_orders_v2 - get tenant_id from webstore
    print("Fixing webstore_orders_v2...")
    orders = await db.webstore_orders_v2.find({"tenant_id": {"$exists": False}}).to_list(10000)
    for order in orders:
        store = await db.webstores_v2.find_one({"id": order.get("webstore_id")}, {"tenant_id": 1})
        if store and store.get("tenant_id"):
            await db.webstore_orders_v2.update_one(
                {"_id": order["_id"]},
                {"$set": {"tenant_id": store["tenant_id"]}}
            )
    print(f"✓ webstore_orders_v2: Updated {len(orders)} documents")
    
    # 7. webstore_products - get tenant_id from webstore
    print("Fixing webstore_products...")
    products = await db.webstore_products.find({"tenant_id": {"$exists": False}}).to_list(10000)
    for product in products:
        store = await db.webstores_v2.find_one({"id": product.get("webstore_id")}, {"tenant_id": 1})
        if store and store.get("tenant_id"):
            await db.webstore_products.update_one(
                {"_id": product["_id"]},
                {"$set": {"tenant_id": store["tenant_id"]}}
            )
    print(f"✓ webstore_products: Updated {len(products)} documents")
    
    # Create indexes for tenant_id on all fixed collections
    collections_to_index = [
        "job_items", "job_activities", "job_notes", 
        "conversation_messages", "timelogs",
        "webstore_orders_v2", "webstore_products"
    ]
    
    for coll_name in collections_to_index:
        await db[coll_name].create_index(
            [("tenant_id", 1)],
            name=f"idx_{coll_name}_tenant_id"
        )
        print(f"  - Created tenant_id index on {coll_name}")
    
    print("\n✅ Tenant isolation fixed for all collections")


async def main():
    """Run the migration"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                k, v = line.strip().split('=', 1)
                os.environ[k] = v.strip('"')
    
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    print("Starting Migration 003: Fix Tenant Isolation")
    print("=" * 50)
    
    success = await run_migration(
        db=db,
        version="003",
        name="fix_tenant_isolation",
        migrate_func=migrate,
        rollback_func=None  # No safe rollback for this
    )
    
    if success:
        print("\n✅ Migration 003 completed successfully!")
    else:
        print("\n❌ Migration 003 failed!")
        sys.exit(1)
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
