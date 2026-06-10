"""Deterministic inventory math and ledger operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional
import uuid

from fastapi import HTTPException


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def convert_quantity(quantity: float, from_unit: str, to_unit: str, *, pack_size: float = 1) -> float:
    """Convert compatible inventory units. Dimensions are handled separately."""
    source = (from_unit or "each").lower()
    target = (to_unit or "each").lower()
    if source == target:
        return float(quantity)
    linear_inches = {"in", "inch", "inches", "linear_in", "linear_inches"}
    linear_feet = {"ft", "foot", "feet", "linear_ft", "linear_feet"}
    if source in linear_feet and target in linear_inches:
        return float(quantity) * 12
    if source in linear_inches and target in linear_feet:
        return float(quantity) / 12
    if source in {"pack", "case"} and target == "each":
        return float(quantity) * float(pack_size or 1)
    if source == "each" and target in {"pack", "case"}:
        return float(quantity) / float(pack_size or 1)
    raise ValueError(f"Cannot convert {from_unit} to {to_unit}")


def roll_area_sqft(width_inches: float, length_inches: float) -> float:
    return max(float(width_inches or 0), 0) * max(float(length_inches or 0), 0) / 144


def requirement_outstanding(requirement: Dict[str, Any]) -> float:
    """Quantity still needing a reservation after prior consumption."""
    return max(
        float(requirement.get("required_quantity", 0))
        - float(requirement.get("consumed_quantity", 0))
        - float(requirement.get("reserved_quantity", 0)),
        0,
    )


def allocatable_quantity(lot: Dict[str, Any], reserved_for_requirement: float = 0) -> float:
    """Stock a requirement may use without consuming another job's reservation."""
    return max(
        float(lot.get("quantity_on_hand", 0))
        - float(lot.get("reserved_quantity", 0))
        + float(reserved_for_requirement or 0),
        0,
    )


def piece_fits(
    lot: Dict[str, Any],
    required_width_inches: Optional[float],
    required_length_inches: Optional[float],
) -> bool:
    """Dimension-aware fit check, allowing a 90-degree rotation."""
    if not required_width_inches or not required_length_inches:
        return True
    width = lot.get("width_inches") or lot.get("sheet_width_inches") or 0
    length = lot.get("remaining_length_inches")
    if length is None:
        length = lot.get("length_inches") or lot.get("sheet_height_inches") or 0
    rw, rl = float(required_width_inches), float(required_length_inches)
    return (float(width) >= rw and float(length) >= rl) or (float(width) >= rl and float(length) >= rw)


async def write_ledger(
    db,
    *,
    tenant_id: str,
    transaction_type: str,
    item_id: str,
    quantity: float,
    unit: str,
    actor_id: str,
    actor_name: str = "",
    reason: str = "",
    lot_id: Optional[str] = None,
    location_id: Optional[str] = None,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    unit_cost: float = 0,
    metadata: Optional[dict] = None,
) -> dict:
    doc = {
        "id": new_id(), "tenant_id": tenant_id, "transaction_type": transaction_type,
        "item_id": item_id, "lot_id": lot_id, "location_id": location_id,
        "quantity": float(quantity), "unit": unit, "unit_cost": float(unit_cost or 0),
        "reason": reason, "source_type": source_type, "source_id": source_id,
        "actor_id": actor_id, "actor_name": actor_name, "metadata": metadata or {},
        "created_at": now_iso(),
    }
    await db.inventory_transactions.insert_one(doc)
    doc.pop("_id", None)
    return doc


async def item_balances(db, tenant_id: str, item_ids: Optional[Iterable[str]] = None) -> Dict[str, dict]:
    match: Dict[str, Any] = {"tenant_id": tenant_id, "is_active": {"$ne": False}}
    if item_ids is not None:
        match["item_id"] = {"$in": list(item_ids)}
    pipeline = [
        {"$match": match},
        {"$group": {
            "_id": "$item_id",
            "on_hand": {"$sum": "$quantity_on_hand"},
            "reserved": {"$sum": "$reserved_quantity"},
            "inventory_value": {"$sum": {"$multiply": ["$quantity_on_hand", "$unit_cost"]}},
        }},
    ]
    rows = await db.inventory_lots.aggregate(pipeline).to_list(10000)
    balances = {}
    for row in rows:
        balances[row["_id"]] = {
            "on_hand": round(row.get("on_hand", 0), 4),
            "reserved": round(row.get("reserved", 0), 4),
            "available": round(row.get("on_hand", 0) - row.get("reserved", 0), 4),
            "inventory_value": round(row.get("inventory_value", 0), 2),
        }
    return balances


async def reserve_requirement(db, requirement: dict, actor: dict) -> dict:
    """Reserve fitting lots atomically and create/update a shortage."""
    tenant_id = requirement["tenant_id"]
    needed = requirement_outstanding(requirement)
    if needed <= 0:
        return requirement
    lots = await db.inventory_lots.find(
        {"tenant_id": tenant_id, "item_id": requirement["inventory_item_id"], "is_active": {"$ne": False}},
        {"_id": 0},
    ).sort("created_at", 1).to_list(1000)
    for lot in lots:
        if needed <= 0:
            break
        if not piece_fits(lot, requirement.get("required_width_inches"), requirement.get("required_length_inches")):
            continue
        available = float(lot.get("quantity_on_hand", 0)) - float(lot.get("reserved_quantity", 0))
        take = min(available, needed)
        if take <= 0:
            continue
        result = await db.inventory_lots.update_one(
            {
                "id": lot["id"], "tenant_id": tenant_id,
                "$expr": {"$gte": [{"$subtract": ["$quantity_on_hand", "$reserved_quantity"]}, take]},
            },
            {"$inc": {"reserved_quantity": take}, "$set": {"updated_at": now_iso()}},
        )
        if result.modified_count != 1:
            continue
        allocation = {
            "id": new_id(), "lot_id": lot["id"], "quantity": take,
            "status": "reserved", "created_at": now_iso(),
        }
        requirement_result = await db.material_requirements.update_one(
            {
                "id": requirement["id"], "tenant_id": tenant_id,
                "$expr": {
                    "$gte": [
                        {
                            "$subtract": [
                                {
                                    "$subtract": [
                                        "$required_quantity",
                                        {"$ifNull": ["$consumed_quantity", 0]},
                                    ]
                                },
                                {"$ifNull": ["$reserved_quantity", 0]},
                            ]
                        },
                        take,
                    ]
                },
            },
            {"$push": {"allocations": allocation}, "$inc": {"reserved_quantity": take}, "$set": {"updated_at": now_iso()}},
        )
        if requirement_result.modified_count != 1:
            await db.inventory_lots.update_one(
                {"id": lot["id"], "tenant_id": tenant_id, "reserved_quantity": {"$gte": take}},
                {"$inc": {"reserved_quantity": -take}, "$set": {"updated_at": now_iso()}},
            )
            break
        await write_ledger(
            db, tenant_id=tenant_id, transaction_type="reservation",
            item_id=requirement["inventory_item_id"], lot_id=lot["id"], quantity=take,
            unit=requirement.get("unit", "each"), actor_id=actor["id"], actor_name=actor.get("name", ""),
            reason="Reserved for approved order", source_type="material_requirement", source_id=requirement["id"],
        )
        needed -= take

    updated = await db.material_requirements.find_one({"id": requirement["id"], "tenant_id": tenant_id}, {"_id": 0})
    short = requirement_outstanding(updated)
    status = "short" if short > 0 else "reserved"
    await db.material_requirements.update_one(
        {"id": requirement["id"], "tenant_id": tenant_id},
        {"$set": {"short_quantity": short, "status": status, "updated_at": now_iso()}},
    )
    if short > 0:
        shortage = {
            "tenant_id": tenant_id, "requirement_id": requirement["id"],
            "job_ticket_id": requirement["job_ticket_id"], "order_id": requirement["order_id"],
            "inventory_item_id": requirement["inventory_item_id"], "quantity": short,
            "unit": requirement.get("unit", "each"), "status": "open", "updated_at": now_iso(),
        }
        await db.inventory_shortages.update_one(
            {"tenant_id": tenant_id, "requirement_id": requirement["id"]},
            {"$set": shortage, "$setOnInsert": {"id": new_id(), "created_at": now_iso()}},
            upsert=True,
        )
    else:
        await db.inventory_shortages.update_many(
            {"tenant_id": tenant_id, "requirement_id": requirement["id"], "status": {"$in": ["open", "ordered"]}},
            {"$set": {"status": "resolved", "updated_at": now_iso()}},
        )
    return await db.material_requirements.find_one({"id": requirement["id"], "tenant_id": tenant_id}, {"_id": 0})


async def release_requirement(db, requirement: dict, actor: dict, reason: str) -> None:
    for allocation in requirement.get("allocations", []):
        if allocation.get("status") != "reserved":
            continue
        qty = float(allocation.get("quantity", 0))
        result = await db.inventory_lots.update_one(
            {
                "id": allocation["lot_id"], "tenant_id": requirement["tenant_id"],
                "reserved_quantity": {"$gte": qty},
            },
            {"$inc": {"reserved_quantity": -qty}, "$set": {"updated_at": now_iso()}},
        )
        if result.modified_count != 1:
            continue
        await write_ledger(
            db, tenant_id=requirement["tenant_id"], transaction_type="reservation_release",
            item_id=requirement["inventory_item_id"], lot_id=allocation["lot_id"], quantity=-qty,
            unit=requirement.get("unit", "each"), actor_id=actor["id"], actor_name=actor.get("name", ""),
            reason=reason, source_type="material_requirement", source_id=requirement["id"],
        )
    await db.material_requirements.update_one(
        {"id": requirement["id"], "tenant_id": requirement["tenant_id"]},
        {"$set": {"allocations": [], "reserved_quantity": 0, "short_quantity": 0, "status": "pending", "updated_at": now_iso()}},
    )
    await db.inventory_shortages.update_many(
        {
            "tenant_id": requirement["tenant_id"], "requirement_id": requirement["id"],
            "status": {"$in": ["open", "ordered"]},
        },
        {"$set": {"status": "cancelled", "updated_at": now_iso()}},
    )


async def reserve_order(db, tenant_id: str, order_id: str, actor: dict) -> None:
    requirements = await db.material_requirements.find(
        {"tenant_id": tenant_id, "order_id": order_id, "status": {"$in": ["pending", "short"]}},
        {"_id": 0},
    ).to_list(1000)
    for requirement in requirements:
        await reserve_requirement(db, requirement, actor)


async def release_order(db, tenant_id: str, order_id: str, actor: dict, reason: str) -> None:
    requirements = await db.material_requirements.find(
        {"tenant_id": tenant_id, "order_id": order_id},
        {"_id": 0},
    ).to_list(1000)
    for requirement in requirements:
        if requirement.get("reserved_quantity", 0) > 0:
            await release_requirement(db, requirement, actor, reason)
        else:
            await db.material_requirements.update_one(
                {"id": requirement["id"], "tenant_id": tenant_id},
                {"$set": {"short_quantity": 0, "status": "pending", "updated_at": now_iso()}},
            )
    await db.inventory_shortages.update_many(
        {"tenant_id": tenant_id, "order_id": order_id, "status": {"$in": ["open", "ordered"]}},
        {"$set": {"status": "cancelled", "updated_at": now_iso()}},
    )
