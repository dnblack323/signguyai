"""
Migration Script: Standardize Tier Names

This script migrates existing tenants and subscriptions to use the canonical tier names:
- tier_1 → starter
- tier_2 → pro
- tier_3 → business
- free → starter

Also fixes any subscription.tier fields that use the old naming.

Run this script once to standardize all tier references.

Usage:
    python scripts/migrate_tier_names.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Get MongoDB connection from environment
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "signguy_ai")

# Mapping of old tier names to new canonical names
TIER_MIGRATION_MAP = {
    "tier_1": "starter",
    "tier_2": "pro",
    "tier_3": "business",
    "Tier 1": "starter",
    "Tier 2": "pro",
    "Tier 3": "business",
    "free": "starter",
    "FREE": "starter",
}


async def migrate_tier_names():
    """Migrate all tier references to canonical names"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"Connected to database: {DB_NAME}")
    print("=" * 50)
    
    # 1. Migrate tenant.plan fields
    print("\n1. Migrating tenant plans...")
    tenant_migrations = 0
    
    for old_name, new_name in TIER_MIGRATION_MAP.items():
        result = await db.tenants.update_many(
            {"plan": old_name},
            {"$set": {"plan": new_name}}
        )
        if result.modified_count > 0:
            print(f"   '{old_name}' → '{new_name}': {result.modified_count} tenants updated")
            tenant_migrations += result.modified_count
    
    print(f"   Total tenant migrations: {tenant_migrations}")
    
    # 2. Migrate subscription.tier fields
    print("\n2. Migrating subscription tiers...")
    subscription_migrations = 0
    
    for old_name, new_name in TIER_MIGRATION_MAP.items():
        result = await db.subscriptions.update_many(
            {"tier": old_name},
            {"$set": {"tier": new_name}}
        )
        if result.modified_count > 0:
            print(f"   '{old_name}' → '{new_name}': {result.modified_count} subscriptions updated")
            subscription_migrations += result.modified_count
    
    print(f"   Total subscription migrations: {subscription_migrations}")
    
    # 3. Verify results
    print("\n3. Verification...")
    
    # Check for any remaining invalid tenant plans
    invalid_plans = await db.tenants.count_documents({
        "plan": {"$nin": ["starter", "pro", "business"]}
    })
    print(f"   Invalid tenant plans remaining: {invalid_plans}")
    
    # Check for any remaining invalid subscription tiers
    invalid_tiers = await db.subscriptions.count_documents({
        "tier": {"$nin": ["starter", "pro", "business", "ai_addon"]}
    })
    print(f"   Invalid subscription tiers remaining: {invalid_tiers}")
    
    # 4. Summary
    print("\n" + "=" * 50)
    print("Migration Summary:")
    print(f"  Tenant plans migrated: {tenant_migrations}")
    print(f"  Subscription tiers migrated: {subscription_migrations}")
    print(f"  Total records updated: {tenant_migrations + subscription_migrations}")
    
    if invalid_plans > 0 or invalid_tiers > 0:
        print("\n⚠️  Warning: Some records have invalid tier values!")
        if invalid_plans > 0:
            invalid_tenant_plans = await db.tenants.find(
                {"plan": {"$nin": ["starter", "pro", "business"]}},
                {"_id": 0, "id": 1, "plan": 1}
            ).to_list(10)
            print(f"     Sample invalid tenant plans: {invalid_tenant_plans}")
        if invalid_tiers > 0:
            invalid_sub_tiers = await db.subscriptions.find(
                {"tier": {"$nin": ["starter", "pro", "business", "ai_addon"]}},
                {"_id": 0, "id": 1, "tier": 1}
            ).to_list(10)
            print(f"     Sample invalid subscription tiers: {invalid_sub_tiers}")
    else:
        print("\n✅ All tier names are now standardized!")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(migrate_tier_names())
