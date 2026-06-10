"""
Seed starter sign-shop inventory items for a tenant.
Run: python seed_inventory.py
Reads MONGO_URL / DB_NAME from backend/.env
"""
import asyncio, os, uuid
from datetime import datetime, timezone
from pathlib import Path

# Load .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            # Strip surrounding quotes
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k.strip(), v)

import motor.motor_asyncio

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME   = os.environ["DB_NAME"]

def _id():   return str(uuid.uuid4())
def _now():  return datetime.now(timezone.utc).isoformat()


# ── Seed catalogue ────────────────────────────────────────────────────────────
ITEMS = [
    # ── VINYL ROLLS ────────────────────────────────────────────────────────────
    dict(
        sku="VNL-CAST-54", name="Cast Vinyl Roll 54\"", category="vinyl",
        tracking_method="roll", base_unit="roll",
        manufacturer="3M", manufacturer_part_number="IJ180mC-10",
        reorder_point=2, preferred_stock_level=5,
        notes="Premium cast vinyl for vehicle wraps and long-term outdoor graphics",
        lot=dict(quantity_on_hand=3, unit_cost=220.00, width_inches=54, remaining_length_inches=1500),
    ),
    dict(
        sku="VNL-CAST-60", name="Cast Vinyl Roll 60\"", category="vinyl",
        tracking_method="roll", base_unit="roll",
        manufacturer="3M", manufacturer_part_number="IJ180mC-10",
        reorder_point=1, preferred_stock_level=3,
        notes="60-inch wide cast vinyl for oversized vehicle wraps",
        lot=dict(quantity_on_hand=2, unit_cost=240.00, width_inches=60, remaining_length_inches=1500),
    ),
    dict(
        sku="VNL-CAL-54", name="Calendered Vinyl Roll 54\"", category="vinyl",
        tracking_method="roll", base_unit="roll",
        manufacturer="Avery", manufacturer_part_number="MPI 1005",
        reorder_point=3, preferred_stock_level=6,
        notes="Economical calendered vinyl for flat surfaces and short-term outdoor use",
        lot=dict(quantity_on_hand=5, unit_cost=95.00, width_inches=54, remaining_length_inches=1500),
    ),
    dict(
        sku="VNL-WHT-PERF", name="Perforated Window Vinyl 54\"", category="vinyl",
        tracking_method="roll", base_unit="roll",
        manufacturer="Avery", manufacturer_part_number="MPI 3300",
        reorder_point=1, preferred_stock_level=2,
        notes="50/50 perforated vinyl for see-through window graphics",
        lot=dict(quantity_on_hand=2, unit_cost=185.00, width_inches=54, remaining_length_inches=150),
    ),
    dict(
        sku="VNL-REFL-3M", name="3M Reflective Vinyl 30\"", category="vinyl",
        tracking_method="roll", base_unit="roll",
        manufacturer="3M", manufacturer_part_number="3930",
        reorder_point=1, preferred_stock_level=2,
        notes="Engineer-grade reflective vinyl for regulatory and safety signage",
        lot=dict(quantity_on_hand=2, unit_cost=310.00, width_inches=30, remaining_length_inches=150),
    ),

    # ── LAMINATES ─────────────────────────────────────────────────────────────
    dict(
        sku="LAM-GLO-54", name="Gloss Overlaminate 54\"", category="laminate",
        tracking_method="roll", base_unit="roll",
        manufacturer="Avery", manufacturer_part_number="DOL 1360",
        reorder_point=2, preferred_stock_level=4,
        notes="High-gloss overlaminate for vehicle wraps and outdoor graphics",
        lot=dict(quantity_on_hand=3, unit_cost=120.00, width_inches=54, remaining_length_inches=500),
    ),
    dict(
        sku="LAM-MAT-54", name="Matte Overlaminate 54\"", category="laminate",
        tracking_method="roll", base_unit="roll",
        manufacturer="Avery", manufacturer_part_number="DOL 1460",
        reorder_point=2, preferred_stock_level=4,
        notes="Satin-matte finish overlaminate",
        lot=dict(quantity_on_hand=3, unit_cost=125.00, width_inches=54, remaining_length_inches=500),
    ),

    # ── SUBSTRATES ────────────────────────────────────────────────────────────
    dict(
        sku="SUB-CORO-4MM-4X8", name="Coroplast 4mm 4x8 Sheet", category="substrate",
        tracking_method="sheet", base_unit="sheet",
        manufacturer="Coroplast", manufacturer_part_number="",
        reorder_point=20, preferred_stock_level=50,
        notes="4mm corrugated plastic - yard signs, real estate, event signage",
        lot=dict(quantity_on_hand=100, unit_cost=3.75, sheet_width_inches=48, sheet_height_inches=96),
    ),
    dict(
        sku="SUB-CORO-4MM-2X3", name="Coroplast 4mm 2x3 Sheet", category="substrate",
        tracking_method="sheet", base_unit="sheet",
        manufacturer="Coroplast", manufacturer_part_number="",
        reorder_point=30, preferred_stock_level=75,
        notes="4mm corrugated plastic pre-cut 24x36 yard sign blanks",
        lot=dict(quantity_on_hand=200, unit_cost=1.10, sheet_width_inches=24, sheet_height_inches=36),
    ),
    dict(
        sku="SUB-ACM-3MM-4X8", name="ACM Panel 3mm 4x8", category="substrate",
        tracking_method="sheet", base_unit="sheet",
        manufacturer="Alucobond", manufacturer_part_number="",
        reorder_point=10, preferred_stock_level=25,
        notes="Aluminum composite material for flat cut letters and rigid exterior signs",
        lot=dict(quantity_on_hand=25, unit_cost=38.00, sheet_width_inches=48, sheet_height_inches=96),
    ),
    dict(
        sku="SUB-SINTRA-3MM-4X8", name="Sintra PVC 3mm 4x8", category="substrate",
        tracking_method="sheet", base_unit="sheet",
        manufacturer="Kömmerling", manufacturer_part_number="Sintra",
        reorder_point=10, preferred_stock_level=20,
        notes="Expanded PVC foam board for indoor signs, displays, and point-of-purchase",
        lot=dict(quantity_on_hand=20, unit_cost=18.50, sheet_width_inches=48, sheet_height_inches=96),
    ),
    dict(
        sku="SUB-SINTRA-6MM-4X8", name="Sintra PVC 6mm 4x8", category="substrate",
        tracking_method="sheet", base_unit="sheet",
        manufacturer="Kömmerling", manufacturer_part_number="Sintra",
        reorder_point=5, preferred_stock_level=15,
        notes="6mm expanded PVC foam board - heavier-duty indoor applications",
        lot=dict(quantity_on_hand=15, unit_cost=32.00, sheet_width_inches=48, sheet_height_inches=96),
    ),
    dict(
        sku="SUB-FOAM-3-16-4X8", name="Foam Board 3/16\" 4x8", category="substrate",
        tracking_method="sheet", base_unit="sheet",
        manufacturer="Elmer's",
        reorder_point=10, preferred_stock_level=25,
        notes="Lightweight foam core for indoor displays and event graphics",
        lot=dict(quantity_on_hand=50, unit_cost=4.25, sheet_width_inches=48, sheet_height_inches=96),
    ),
    dict(
        sku="SUB-BANNER-13OZ-54", name="13oz Banner Material 54\"", category="substrate",
        tracking_method="roll", base_unit="roll",
        reorder_point=2, preferred_stock_level=4,
        notes="13oz scrim vinyl banner material for outdoor banners",
        lot=dict(quantity_on_hand=3, unit_cost=0.65, width_inches=54, remaining_length_inches=1500),
    ),

    # ── APPLICATION TAPE ──────────────────────────────────────────────────────
    dict(
        sku="APP-TAPE-MED-6IN", name="Application Tape 6\" Medium Tack", category="application_tape",
        tracking_method="roll", base_unit="roll",
        manufacturer="R-Tape", manufacturer_part_number="4075",
        reorder_point=2, preferred_stock_level=5,
        notes="Paper-based medium tack transfer tape for cut vinyl lettering",
        lot=dict(quantity_on_hand=6, unit_cost=14.00, width_inches=6, remaining_length_inches=3600),
    ),
    dict(
        sku="APP-TAPE-CLR-12IN", name="Clear App Tape 12\" High Tack", category="application_tape",
        tracking_method="roll", base_unit="roll",
        manufacturer="RTape", manufacturer_part_number="ConformX 4761",
        reorder_point=1, preferred_stock_level=3,
        notes="Clear high-tack application tape for premium vinyl placement",
        lot=dict(quantity_on_hand=3, unit_cost=28.00, width_inches=12, remaining_length_inches=1500),
    ),

    # ── HARDWARE ──────────────────────────────────────────────────────────────
    dict(
        sku="HW-HSTAKE-9G", name="H-Stake 9-Gauge Wire", category="hardware",
        tracking_method="quantity", base_unit="each",
        reorder_point=50, preferred_stock_level=200,
        notes="9-gauge galvanized H-stakes for yard signs and corrugated lawn signs",
        lot=dict(quantity_on_hand=500, unit_cost=0.42),
    ),
    dict(
        sku="HW-GROMMET-BRS", name="Brass Grommet #2", category="hardware",
        tracking_method="pack", base_unit="pack",
        reorder_point=5, preferred_stock_level=10,
        notes="Brass #2 grommets for banner finishing — packs of 100",
        lot=dict(quantity_on_hand=20, unit_cost=8.50, pack_size=100),
    ),
    dict(
        sku="HW-BANNER-TAPE", name="Banner Hemming Tape 1\" Roll", category="hardware",
        tracking_method="quantity", base_unit="roll",
        reorder_point=5, preferred_stock_level=10,
        notes="Heat-activated banner hemming tape for professional banner finishing",
        lot=dict(quantity_on_hand=12, unit_cost=9.50),
    ),
    dict(
        sku="HW-STANDOFF-1IN", name="Sign Standoff 1\" Chrome", category="hardware",
        tracking_method="quantity", base_unit="each",
        reorder_point=20, preferred_stock_level=50,
        notes="1-inch chrome standoff cap screws for lobby and office signs",
        lot=dict(quantity_on_hand=100, unit_cost=1.85),
    ),
    dict(
        sku="HW-FOAM-TAPE-3M", name="3M VHB Foam Tape 1\" Roll", category="hardware",
        tracking_method="quantity", base_unit="roll",
        reorder_point=3, preferred_stock_level=8,
        notes="3M VHB double-sided foam tape for mounting signs on surfaces",
        lot=dict(quantity_on_hand=10, unit_cost=22.00),
    ),
]


async def seed(tenant_id: str):
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    existing = await db.inventory_items.find({"tenant_id": tenant_id}, {"sku": 1}).to_list(1000)
    existing_skus = {e["sku"] for e in existing}

    created, skipped = 0, 0
    for spec in ITEMS:
        lot_spec = spec.pop("lot", {})
        if spec["sku"] in existing_skus:
            skipped += 1
            continue

        item_id = _id()
        now = _now()
        item = {
            "id": item_id, "tenant_id": tenant_id, "is_active": True,
            "created_at": now, "updated_at": now, "aliases": [],
            "manufacturer_part_number": spec.get("manufacturer_part_number", ""),
            "manufacturer": spec.get("manufacturer", ""),
            **spec,
        }
        await db.inventory_items.insert_one(item)

        # Opening lot
        lot_id = _id()
        qoh = float(lot_spec.get("quantity_on_hand", 0))
        lot = {
            "id": lot_id, "tenant_id": tenant_id,
            "item_id": item_id,
            "lot_number": f"OPEN-{item['sku']}",
            "quantity_on_hand": qoh,
            "reserved_quantity": 0,
            "unit_cost": float(lot_spec.get("unit_cost", 0)),
            "width_inches": lot_spec.get("width_inches"),
            "length_inches": lot_spec.get("length_inches"),
            "remaining_length_inches": lot_spec.get("remaining_length_inches"),
            "sheet_width_inches": lot_spec.get("sheet_width_inches"),
            "sheet_height_inches": lot_spec.get("sheet_height_inches"),
            "pack_size": float(lot_spec.get("pack_size", 1)),
            "thickness": "", "source_purchase_order_id": None,
            "parent_lot_id": None, "is_active": True, "notes": "Opening stock balance",
            "created_at": now, "updated_at": now,
        }
        await db.inventory_lots.insert_one(lot)

        # Opening transaction
        tx = {
            "id": _id(), "tenant_id": tenant_id,
            "transaction_type": "receipt",
            "item_id": item_id, "lot_id": lot_id,
            "quantity": qoh, "unit": item["base_unit"],
            "unit_cost": lot["unit_cost"],
            "reason": "Opening stock balance",
            "performed_by_user_id": "seed_script",
            "performed_by_name": "System Seed",
            "created_at": now,
        }
        await db.inventory_transactions.insert_one(tx)
        created += 1
        print(f"  + {item['sku']}: {item['name']} (qty {qoh})")

    client.close()
    print(f"\nDone: {created} created, {skipped} skipped (already existed)")
    return created, skipped


async def main():
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    # Find first active tenant (non-platform admin)
    user = await db.users.find_one({"role": "owner", "is_active": True}, {"tenant_id": 1, "email": 1})
    client.close()

    if not user:
        print("No owner user found — cannot determine tenant_id")
        return

    tid = user["tenant_id"]
    print(f"Seeding inventory for tenant: {tid} (owner: {user['email']})")
    await seed(tid)


asyncio.run(main())
