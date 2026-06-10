"""Create indexes used by inventory, material reservations, and purchasing."""

import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def run():
    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]
    await db.inventory_items.create_index([("tenant_id", 1), ("sku", 1)], unique=True)
    await db.inventory_items.create_index([("tenant_id", 1), ("pricing_material_key", 1)])
    await db.inventory_lots.create_index([("tenant_id", 1), ("item_id", 1), ("is_active", 1)])
    await db.inventory_lots.create_index([("tenant_id", 1), ("location_id", 1)])
    await db.inventory_transactions.create_index([("tenant_id", 1), ("created_at", -1)])
    await db.material_requirements.create_index([("tenant_id", 1), ("job_ticket_id", 1)])
    await db.material_requirements.create_index([("tenant_id", 1), ("order_id", 1), ("status", 1)])
    await db.inventory_shortages.create_index([("tenant_id", 1), ("status", 1)])
    await db.purchase_orders.create_index([("tenant_id", 1), ("status", 1), ("created_at", -1)])
    await db.purchase_orders.create_index([("tenant_id", 1), ("po_number", 1)], unique=True)
    await db.inventory_vendors.create_index([("tenant_id", 1), ("name", 1)])
    await db.pricing_cost_suggestions.create_index([("tenant_id", 1), ("status", 1)])
    client.close()


if __name__ == "__main__":
    asyncio.run(run())
