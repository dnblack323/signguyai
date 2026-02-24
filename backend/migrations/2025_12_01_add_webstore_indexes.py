"""
Migration: Add MongoDB indexes for Webstore performance
Date: December 1, 2025

Indexes added:
- products: (tenant_id, category, is_active)
- webstores_v2: (tenant_id, store_type, status)
- webstore_products: (webstore_id, product_id) unique
- webstore_orders_v2: (webstore_id, created_at)
- customers: (tenant_id, email) unique (optional - handles conflicts)
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def run_migration():
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("Starting index migration...")
    
    # 1. Products index: (tenant_id, category, is_active)
    try:
        await db.products.create_index(
            [("tenant_id", 1), ("category", 1), ("is_active", 1)],
            name="idx_products_tenant_category_active"
        )
        print("✓ Created index: products (tenant_id, category, is_active)")
    except Exception as e:
        print(f"⚠ Products index: {e}")
    
    # 2. Webstores index: (tenant_id, store_type, status)
    try:
        await db.webstores_v2.create_index(
            [("tenant_id", 1), ("store_type", 1), ("status", 1)],
            name="idx_webstores_tenant_type_status"
        )
        print("✓ Created index: webstores_v2 (tenant_id, store_type, status)")
    except Exception as e:
        print(f"⚠ Webstores index: {e}")
    
    # 3. Webstore products index: (webstore_id, product_id) unique
    try:
        await db.webstore_products.create_index(
            [("webstore_id", 1), ("product_id", 1)],
            name="idx_webstore_products_unique",
            unique=True
        )
        print("✓ Created index: webstore_products (webstore_id, product_id) UNIQUE")
    except Exception as e:
        print(f"⚠ Webstore products index: {e}")
    
    # 4. Webstore orders index: (webstore_id, created_at)
    try:
        await db.webstore_orders_v2.create_index(
            [("webstore_id", 1), ("created_at", -1)],
            name="idx_webstore_orders_webstore_created"
        )
        print("✓ Created index: webstore_orders_v2 (webstore_id, created_at)")
    except Exception as e:
        print(f"⚠ Webstore orders index: {e}")
    
    # 5. Customers index: (tenant_id, email) - unique per tenant
    # Note: This may fail if there are duplicate emails within a tenant
    try:
        await db.customers.create_index(
            [("tenant_id", 1), ("email", 1)],
            name="idx_customers_tenant_email_unique",
            unique=True,
            sparse=True  # Allow null emails
        )
        print("✓ Created index: customers (tenant_id, email) UNIQUE")
    except Exception as e:
        print(f"⚠ Customers index (may have duplicates): {e}")
    
    # 6. Subscriptions index: (stripe_subscription_id) for webhook lookups
    try:
        await db.subscriptions.create_index(
            [("stripe_subscription_id", 1)],
            name="idx_subscriptions_stripe_sub_id",
            sparse=True
        )
        print("✓ Created index: subscriptions (stripe_subscription_id)")
    except Exception as e:
        print(f"⚠ Subscriptions index: {e}")
    
    # 7. Subscriptions index: (tenant_id)
    try:
        await db.subscriptions.create_index(
            [("tenant_id", 1)],
            name="idx_subscriptions_tenant",
            unique=True
        )
        print("✓ Created index: subscriptions (tenant_id) UNIQUE")
    except Exception as e:
        print(f"⚠ Subscriptions tenant index: {e}")
    
    print("\nMigration completed!")
    
    # List all indexes for verification
    print("\n=== Current Indexes ===")
    for collection_name in ["products", "webstores_v2", "webstore_products", "webstore_orders_v2", "customers", "subscriptions"]:
        try:
            indexes = await db[collection_name].index_information()
            print(f"\n{collection_name}:")
            for idx_name, idx_info in indexes.items():
                print(f"  - {idx_name}: {idx_info.get('key')}")
        except Exception as e:
            print(f"  Error listing indexes: {e}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
