"""Inventory, job materials, and manual purchasing API."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from core_runtime import db, get_current_active_user, has_permission
from models import (
    CycleCountInput, InventoryAdjustmentInput, InventoryItem, InventoryItemInput,
    InventoryLocation, InventoryLocationInput, InventoryLot, InventoryLotInput,
    InventoryTransferInput, MaterialPullInput, MaterialRequirementInput, Permission, PurchaseOrderInput,
    PurchaseOrderReceiveInput, UserInDB, VendorInput,
)
from services.inventory_service import (
    allocatable_quantity, convert_quantity, item_balances, new_id, now_iso, piece_fits,
    release_requirement, requirement_outstanding, reserve_requirement, roll_area_sqft,
    write_ledger,
)

router = APIRouter(tags=["Inventory and Purchasing"])


def _actor(user: UserInDB) -> dict:
    return {"id": user.id, "name": user.full_name or ""}


def _require(user: UserInDB, permission: Permission) -> None:
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail="You do not have permission for this inventory action")


async def _item_or_404(tenant_id: str, item_id: str) -> dict:
    item = await db.inventory_items.find_one({"id": item_id, "tenant_id": tenant_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item


async def _lot_or_404(tenant_id: str, lot_id: str) -> dict:
    lot = await db.inventory_lots.find_one({"id": lot_id, "tenant_id": tenant_id}, {"_id": 0})
    if not lot:
        raise HTTPException(status_code=404, detail="Inventory lot not found")
    return lot


async def _location_or_404(tenant_id: str, location_id: str) -> dict:
    location = await db.inventory_locations.find_one({"id": location_id, "tenant_id": tenant_id}, {"_id": 0})
    if not location:
        raise HTTPException(status_code=404, detail="Inventory location not found")
    return location


def _normalize_requirement(data: MaterialRequirementInput, item: dict) -> dict:
    payload = data.model_dump()
    base_unit = item.get("base_unit") or "each"
    if payload["unit"] != base_unit:
        pack_size = next((float(alias.get("pack_quantity", 1) or 1) for alias in item.get("aliases", []) if alias.get("pack_quantity")), 1)
        try:
            payload["required_quantity"] = convert_quantity(payload["required_quantity"], payload["unit"], base_unit, pack_size=pack_size)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        payload["unit"] = base_unit
    return payload


def _alias_pack_size(item: dict, vendor_id: Optional[str] = None, supplier_sku: str = "") -> float:
    aliases = item.get("aliases", [])
    alias = next(
        (
            candidate for candidate in aliases
            if (not vendor_id or candidate.get("vendor_id") == vendor_id)
            and (not supplier_sku or candidate.get("supplier_sku") == supplier_sku)
        ),
        None,
    )
    return float((alias or {}).get("pack_quantity", 1) or 1)


def _to_base_quantity(quantity: float, unit: str, item: dict, pack_size: float) -> float:
    try:
        return convert_quantity(quantity, unit, item.get("base_unit", "each"), pack_size=pack_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/inventory/summary")
async def inventory_summary(current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_VIEW)
    tid = current_user.tenant_id
    items = await db.inventory_items.find({"tenant_id": tid, "is_active": {"$ne": False}}, {"_id": 0}).to_list(10000)
    balances = await item_balances(db, tid)
    incoming_rows = await db.purchase_orders.aggregate([
        {"$match": {"tenant_id": tid, "status": {"$in": ["approved", "sent", "partially_received"]}}},
        {"$unwind": "$lines"},
        {"$group": {
            "_id": "$lines.inventory_item_id",
            "incoming": {"$sum": {"$subtract": [
                {"$ifNull": ["$lines.base_ordered_quantity", "$lines.ordered_quantity"]},
                {"$ifNull": ["$lines.base_received_quantity", "$lines.received_quantity"]},
            ]}},
        }},
    ]).to_list(10000)
    incoming = {row["_id"]: row["incoming"] for row in incoming_rows}
    shortage_rows = await db.inventory_shortages.aggregate([
        {"$match": {"tenant_id": tid, "status": "open"}},
        {"$group": {"_id": "$inventory_item_id", "short": {"$sum": "$quantity"}}},
    ]).to_list(10000)
    shortages = {row["_id"]: row["short"] for row in shortage_rows}
    enriched = []
    for item in items:
        balance = balances.get(item["id"], {"on_hand": 0, "reserved": 0, "available": 0, "inventory_value": 0})
        enriched.append({**item, **balance, "incoming": incoming.get(item["id"], 0), "short": shortages.get(item["id"], 0)})
    low_stock = [x for x in enriched if x["available"] <= float(x.get("reorder_point", 0)) and float(x.get("reorder_point", 0)) > 0]
    return {
        "items": enriched, "item_count": len(enriched), "low_stock_count": len(low_stock),
        "shortage_count": await db.inventory_shortages.count_documents({"tenant_id": tid, "status": "open"}),
        "inventory_value": round(sum(x["inventory_value"] for x in enriched), 2),
    }


@router.get("/inventory/items")
async def list_inventory_items(
    search: str = "", category: str = "", current_user: UserInDB = Depends(get_current_active_user)
):
    _require(current_user, Permission.INVENTORY_VIEW)
    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id}
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"aliases.nickname": {"$regex": search, "$options": "i"}},
            {"aliases.supplier_sku": {"$regex": search, "$options": "i"}},
            {"aliases.supplier_name": {"$regex": search, "$options": "i"}},
            {"aliases.supplier_product_name": {"$regex": search, "$options": "i"}},
            {"aliases.manufacturer_sku": {"$regex": search, "$options": "i"}},
        ]
    items = await db.inventory_items.find(query, {"_id": 0}).sort("name", 1).to_list(10000)
    balances = await item_balances(db, current_user.tenant_id, [x["id"] for x in items])
    return [{**item, **balances.get(item["id"], {"on_hand": 0, "reserved": 0, "available": 0, "inventory_value": 0})} for item in items]


@router.post("/inventory/items")
async def create_inventory_item(data: InventoryItemInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    duplicate = await db.inventory_items.find_one({"tenant_id": current_user.tenant_id, "sku": data.sku})
    if duplicate:
        raise HTTPException(status_code=409, detail="Inventory SKU already exists")
    item = InventoryItem(tenant_id=current_user.tenant_id, **data.model_dump())
    doc = item.model_dump(mode="json")
    await db.inventory_items.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/inventory/import-pricing-materials")
async def import_pricing_materials(current_user: UserInDB = Depends(get_current_active_user)):
    """Create inactive-stock inventory catalog records linked to Pricing Foundation."""
    _require(current_user, Permission.INVENTORY_ADJUST)
    from server import get_pricing_defaults
    defaults = await get_pricing_defaults(current_user.tenant_id)
    created = 0
    skipped = 0
    for material in defaults.get("materials", []):
        key = material.get("key") or material.get("id")
        if not key:
            continue
        exists = await db.inventory_items.find_one(
            {"tenant_id": current_user.tenant_id, "$or": [{"pricing_material_key": key}, {"sku": key}]},
            {"_id": 0, "id": 1},
        )
        if exists:
            skipped += 1
            continue
        unit = material.get("unit_type") or ("sqft" if material.get("cost_per_sqft") is not None else "each")
        item = InventoryItem(
            tenant_id=current_user.tenant_id, sku=key, name=material.get("name") or key,
            category=material.get("category") or "other", tracking_method="quantity",
            manufacturer=material.get("brand", ""), base_unit=unit, pricing_material_key=key,
            aliases=[], notes="Imported from Pricing Foundation; receive or adjust stock to begin tracking.",
        ).model_dump(mode="json")
        await db.inventory_items.insert_one(item)
        created += 1
    return {"created": created, "skipped": skipped}


@router.put("/inventory/items/{item_id}")
async def update_inventory_item(item_id: str, data: InventoryItemInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    await _item_or_404(current_user.tenant_id, item_id)
    duplicate = await db.inventory_items.find_one(
        {"tenant_id": current_user.tenant_id, "sku": data.sku, "id": {"$ne": item_id}},
        {"_id": 0, "id": 1},
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Inventory SKU already exists")
    updates = data.model_dump(mode="json")
    updates["updated_at"] = now_iso()
    await db.inventory_items.update_one({"id": item_id, "tenant_id": current_user.tenant_id}, {"$set": updates})
    return await db.inventory_items.find_one({"id": item_id, "tenant_id": current_user.tenant_id}, {"_id": 0})


@router.delete("/inventory/items/{item_id}")
async def deactivate_inventory_item(item_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    result = await db.inventory_items.update_one(
        {"id": item_id, "tenant_id": current_user.tenant_id},
        {"$set": {"is_active": False, "updated_at": now_iso()}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return {"message": "Inventory item deactivated"}


@router.get("/inventory/locations")
async def list_locations(current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_VIEW)
    return await db.inventory_locations.find({"tenant_id": current_user.tenant_id}, {"_id": 0}).sort("name", 1).to_list(1000)


@router.post("/inventory/locations")
async def create_location(data: InventoryLocationInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    if data.parent_id:
        await _location_or_404(current_user.tenant_id, data.parent_id)
    location = InventoryLocation(tenant_id=current_user.tenant_id, **data.model_dump())
    doc = location.model_dump(mode="json")
    await db.inventory_locations.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/inventory/locations/{location_id}")
async def update_location(location_id: str, data: InventoryLocationInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    if data.parent_id:
        if data.parent_id == location_id:
            raise HTTPException(status_code=400, detail="A location cannot be its own parent")
        await _location_or_404(current_user.tenant_id, data.parent_id)
    result = await db.inventory_locations.update_one(
        {"id": location_id, "tenant_id": current_user.tenant_id},
        {"$set": {**data.model_dump(), "updated_at": now_iso()}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Inventory location not found")
    return await db.inventory_locations.find_one({"id": location_id, "tenant_id": current_user.tenant_id}, {"_id": 0})


@router.get("/inventory/lots")
async def list_lots(
    item_id: str = "", location_id: str = "", current_user: UserInDB = Depends(get_current_active_user)
):
    _require(current_user, Permission.INVENTORY_VIEW)
    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id, "is_active": {"$ne": False}}
    if item_id:
        query["item_id"] = item_id
    if location_id:
        query["location_id"] = location_id
    lots = await db.inventory_lots.find(query, {"_id": 0}).sort("created_at", 1).to_list(10000)
    for lot in lots:
        lot["available_quantity"] = float(lot.get("quantity_on_hand", 0)) - float(lot.get("reserved_quantity", 0))
        if lot.get("width_inches") and lot.get("remaining_length_inches") is not None:
            lot["remaining_area_sqft"] = round(roll_area_sqft(lot["width_inches"], lot["remaining_length_inches"]), 4)
    return lots


@router.post("/inventory/lots")
async def create_lot(data: InventoryLotInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    item = await _item_or_404(current_user.tenant_id, data.item_id)
    if data.location_id:
        await _location_or_404(current_user.tenant_id, data.location_id)
    if data.reserved_quantity:
        raise HTTPException(status_code=400, detail="New lots cannot begin with reserved stock")
    lot = InventoryLot(tenant_id=current_user.tenant_id, **data.model_dump())
    doc = lot.model_dump(mode="json")
    await db.inventory_lots.insert_one(doc)
    await write_ledger(
        db, tenant_id=current_user.tenant_id, transaction_type="receipt", item_id=data.item_id,
        lot_id=lot.id, location_id=data.location_id, quantity=data.quantity_on_hand, unit=item["base_unit"],
        actor_id=current_user.id, actor_name=current_user.full_name or "", reason="Initial lot receipt",
        unit_cost=data.unit_cost, source_type="inventory_lot", source_id=lot.id,
    )
    doc.pop("_id", None)
    return doc


@router.post("/inventory/adjustments")
async def adjust_inventory(data: InventoryAdjustmentInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    if not data.reason.strip():
        raise HTTPException(status_code=400, detail="Adjustment reason is required")
    item = await _item_or_404(current_user.tenant_id, data.item_id)
    if data.location_id:
        await _location_or_404(current_user.tenant_id, data.location_id)
    lot = await _lot_or_404(current_user.tenant_id, data.lot_id) if data.lot_id else None
    if lot and lot["item_id"] != data.item_id:
        raise HTTPException(status_code=400, detail="Selected lot does not belong to the inventory item")
    if lot and data.location_id and data.location_id != lot.get("location_id"):
        raise HTTPException(status_code=400, detail="Use a stock transfer to change an existing lot's location")
    pack_size = float((lot or {}).get("pack_size", _alias_pack_size(item)) or 1)
    quantity_delta = float(data.quantity_delta)
    if data.unit and data.unit != item["base_unit"]:
        try:
            quantity_delta = convert_quantity(quantity_delta, data.unit, item["base_unit"], pack_size=pack_size)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not lot:
        lot = InventoryLot(
            tenant_id=current_user.tenant_id, item_id=data.item_id, location_id=data.location_id,
            quantity_on_hand=0, unit_cost=float(data.unit_cost or 0), notes="Created by manual adjustment",
        ).model_dump(mode="json")
        await db.inventory_lots.insert_one(lot)
        lot.pop("_id", None)
    new_quantity = float(lot.get("quantity_on_hand", 0)) + quantity_delta
    if new_quantity < float(lot.get("reserved_quantity", 0)) or new_quantity < 0:
        raise HTTPException(status_code=409, detail="Adjustment would reduce stock below reserved or zero quantity")
    updates: Dict[str, Any] = {"quantity_on_hand": new_quantity, "updated_at": now_iso()}
    if data.unit_cost is not None:
        updates["unit_cost"] = data.unit_cost
    await db.inventory_lots.update_one({"id": lot["id"], "tenant_id": current_user.tenant_id}, {"$set": updates})
    return await write_ledger(
        db, tenant_id=current_user.tenant_id, transaction_type="manual_adjustment", item_id=data.item_id,
        lot_id=lot["id"], location_id=data.location_id or lot.get("location_id"), quantity=quantity_delta,
        unit=item["base_unit"], actor_id=current_user.id, actor_name=current_user.full_name or "",
        reason=data.reason, unit_cost=float(data.unit_cost if data.unit_cost is not None else lot.get("unit_cost", 0)),
    )


@router.post("/inventory/transfers")
async def transfer_inventory(data: InventoryTransferInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    if not data.reason.strip():
        raise HTTPException(status_code=400, detail="Transfer reason is required")
    lot = await _lot_or_404(current_user.tenant_id, data.lot_id)
    item = await _item_or_404(current_user.tenant_id, lot["item_id"])
    await _location_or_404(current_user.tenant_id, data.destination_location_id)
    if lot.get("location_id") == data.destination_location_id:
        raise HTTPException(status_code=400, detail="Source and destination locations must be different")
    quantity = float(data.quantity)
    on_hand = float(lot.get("quantity_on_hand", 0))
    if item.get("tracking_method") in {"roll", "sheet", "remnant"} and abs(quantity - on_hand) > 0.0001:
        raise HTTPException(status_code=400, detail="Dimension-tracked lots must be transferred in full")
    result = await db.inventory_lots.update_one(
        {
            "id": lot["id"], "tenant_id": current_user.tenant_id,
            "$expr": {"$gte": [{"$subtract": ["$quantity_on_hand", "$reserved_quantity"]}, quantity]},
        },
        {
            "$inc": {"quantity_on_hand": -quantity},
            "$set": {"updated_at": now_iso(), **({"is_active": False} if abs(quantity - on_hand) <= 0.0001 else {})},
        },
    )
    if result.modified_count != 1:
        raise HTTPException(status_code=409, detail="Not enough unreserved stock to transfer")
    dimension_fields = {
        key: lot.get(key) for key in (
            "width_inches", "length_inches", "remaining_length_inches",
            "sheet_width_inches", "sheet_height_inches", "thickness",
        ) if lot.get(key) is not None
    } if abs(quantity - on_hand) <= 0.0001 else {}
    destination = InventoryLot(
        tenant_id=current_user.tenant_id, item_id=item["id"], location_id=data.destination_location_id,
        parent_lot_id=lot["id"], lot_number=lot.get("lot_number", ""), quantity_on_hand=quantity,
        unit_cost=lot.get("unit_cost", 0), pack_size=lot.get("pack_size", 1),
        notes=f"Transferred from {lot.get('location_id') or 'unlocated'}: {data.reason}", **dimension_fields,
    ).model_dump(mode="json")
    await db.inventory_lots.insert_one(destination)
    common = {
        "db": db, "tenant_id": current_user.tenant_id, "transaction_type": "transfer",
        "item_id": item["id"], "unit": item["base_unit"], "actor_id": current_user.id,
        "actor_name": current_user.full_name or "", "reason": data.reason,
        "source_type": "inventory_transfer", "source_id": destination["id"], "unit_cost": lot.get("unit_cost", 0),
    }
    await write_ledger(
        lot_id=lot["id"], location_id=lot.get("location_id"), quantity=-quantity,
        metadata={"destination_lot_id": destination["id"], "destination_location_id": data.destination_location_id},
        **common,
    )
    await write_ledger(
        lot_id=destination["id"], location_id=data.destination_location_id, quantity=quantity,
        metadata={"source_lot_id": lot["id"], "source_location_id": lot.get("location_id")},
        **common,
    )
    destination.pop("_id", None)
    return destination


@router.get("/inventory/transactions")
async def list_transactions(
    item_id: str = "", limit: int = 200, current_user: UserInDB = Depends(get_current_active_user)
):
    _require(current_user, Permission.INVENTORY_VIEW)
    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id}
    if item_id:
        query["item_id"] = item_id
    return await db.inventory_transactions.find(query, {"_id": 0}).sort("created_at", -1).limit(min(limit, 1000)).to_list(min(limit, 1000))


@router.get("/inventory/cost-suggestions")
async def list_cost_suggestions(current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_VIEW)
    return await db.pricing_cost_suggestions.find(
        {"tenant_id": current_user.tenant_id, "status": "pending"}, {"_id": 0}
    ).sort("created_at", -1).to_list(1000)


@router.post("/inventory/cycle-counts")
async def complete_cycle_count(data: CycleCountInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    report = {
        "id": new_id(), "tenant_id": current_user.tenant_id, "name": data.name or f"Count {now_iso()[:10]}",
        "status": "completed", "lines": [], "completed_by": current_user.id, "created_at": now_iso(), "completed_at": now_iso(),
    }
    for line in data.lines:
        item = await _item_or_404(current_user.tenant_id, line.item_id)
        lot = await _lot_or_404(current_user.tenant_id, line.lot_id) if line.lot_id else None
        if not lot:
            raise HTTPException(status_code=400, detail="Cycle count lines require a lot")
        if lot["item_id"] != line.item_id:
            raise HTTPException(status_code=400, detail="Cycle count lot does not belong to the inventory item")
        expected = float(lot.get("quantity_on_hand", 0))
        delta = line.actual_quantity - expected
        if delta and not (line.reason or "").strip():
            raise HTTPException(status_code=400, detail="A discrepancy reason is required")
        if line.actual_quantity < float(lot.get("reserved_quantity", 0)):
            raise HTTPException(status_code=409, detail="Count cannot be below reserved quantity")
        await db.inventory_lots.update_one(
            {"id": lot["id"], "tenant_id": current_user.tenant_id},
            {"$set": {"quantity_on_hand": line.actual_quantity, "updated_at": now_iso()}},
        )
        if delta:
            await write_ledger(
                db, tenant_id=current_user.tenant_id, transaction_type="cycle_count_adjustment",
                item_id=line.item_id, lot_id=lot["id"], location_id=line.location_id or lot.get("location_id"),
                quantity=delta, unit=item["base_unit"], actor_id=current_user.id, actor_name=current_user.full_name or "",
                reason=line.reason or "", unit_cost=lot.get("unit_cost", 0), source_type="cycle_count", source_id=report["id"],
            )
        report["lines"].append({**line.model_dump(), "expected_quantity": expected, "difference": delta})
    await db.inventory_cycle_counts.insert_one(report)
    report.pop("_id", None)
    return report


@router.get("/inventory/cycle-counts")
async def list_cycle_counts(current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_VIEW)
    return await db.inventory_cycle_counts.find({"tenant_id": current_user.tenant_id}, {"_id": 0}).sort("completed_at", -1).to_list(500)


@router.get("/job-tickets/{ticket_id}/material-requirements")
async def list_requirements(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_VIEW)
    return await db.material_requirements.find(
        {"tenant_id": current_user.tenant_id, "job_ticket_id": ticket_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(1000)


@router.post("/job-tickets/{ticket_id}/material-requirements")
async def create_requirement(ticket_id: str, data: MaterialRequirementInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    ticket = await db.job_tickets.find_one({"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Job ticket not found")
    item = await _item_or_404(current_user.tenant_id, data.inventory_item_id)
    normalized = _normalize_requirement(data, item)
    doc = {
        "id": new_id(), "tenant_id": current_user.tenant_id, "job_ticket_id": ticket_id, "order_id": ticket["order_id"],
        **normalized, "reserved_quantity": 0, "consumed_quantity": 0, "short_quantity": 0,
        "status": "pending", "allocations": [], "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.material_requirements.insert_one(doc)
    doc.pop("_id", None)
    order = await db.orders.find_one({"id": ticket["order_id"], "tenant_id": current_user.tenant_id}, {"_id": 0, "status": 1, "approval_status": 1})
    if order and (order.get("approval_status") == "approved" or order.get("status") == "approved"):
        doc = await reserve_requirement(db, doc, _actor(current_user))
    return doc


@router.post("/job-tickets/{ticket_id}/material-requirements/generate")
async def generate_requirement(ticket_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    ticket = await db.job_tickets.find_one({"id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Job ticket not found")
    specs = ticket.get("specs") or {}
    candidates = [
        specs.get("material"), specs.get("substrate"), specs.get("vinyl_type"),
        specs.get("print_material"), specs.get("apparel_blank_key"),
    ]
    key = next((x for x in candidates if x), None)
    item = await db.inventory_items.find_one(
        {"tenant_id": current_user.tenant_id, "$or": [{"pricing_material_key": key}, {"sku": key}]}, {"_id": 0}
    ) if key else None
    if not item:
        raise HTTPException(status_code=400, detail="No linked inventory item found. Add a requirement manually or link a Pricing Foundation material.")
    width = float(specs.get("width", 0) or 0)
    height = float(specs.get("height", 0) or 0)
    unit = str(specs.get("unit_of_measure") or "inches").lower()
    if unit == "feet":
        width, height = width * 12, height * 12
    qty = float(ticket.get("quantity", 1) or 1)
    required = qty
    if item.get("base_unit") == "sqft" and width and height:
        required = (width * height / 144) * qty
    payload = MaterialRequirementInput(
        inventory_item_id=item["id"], required_quantity=round(required, 4), unit=item.get("base_unit", "each"),
        required_width_inches=width or None, required_length_inches=height or None, source="generated",
    )
    return await create_requirement(ticket_id, payload, current_user)


@router.put("/material-requirements/{requirement_id}")
async def update_requirement(requirement_id: str, data: MaterialRequirementInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    requirement = await db.material_requirements.find_one({"id": requirement_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not requirement:
        raise HTTPException(status_code=404, detail="Material requirement not found")
    if requirement.get("reserved_quantity", 0) > 0:
        await release_requirement(db, requirement, _actor(current_user), "Requirement edited")
    item = await _item_or_404(current_user.tenant_id, data.inventory_item_id)
    normalized = _normalize_requirement(data, item)
    await db.material_requirements.update_one(
        {"id": requirement_id, "tenant_id": current_user.tenant_id},
        {"$set": {**normalized, "updated_at": now_iso()}},
    )
    updated = await db.material_requirements.find_one({"id": requirement_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    order = await db.orders.find_one({"id": requirement["order_id"], "tenant_id": current_user.tenant_id}, {"_id": 0, "status": 1, "approval_status": 1})
    if order and (order.get("approval_status") == "approved" or order.get("status") == "approved"):
        updated = await reserve_requirement(db, updated, _actor(current_user))
    return updated


@router.post("/material-requirements/{requirement_id}/reserve")
async def reserve_one_requirement(requirement_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_ADJUST)
    requirement = await db.material_requirements.find_one({"id": requirement_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not requirement:
        raise HTTPException(status_code=404, detail="Material requirement not found")
    return await reserve_requirement(db, requirement, _actor(current_user))


@router.post("/job-tickets/{ticket_id}/pull-materials")
async def pull_material(ticket_id: str, data: MaterialPullInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_PULL)
    requirement = await db.material_requirements.find_one(
        {"id": data.requirement_id, "job_ticket_id": ticket_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not requirement:
        raise HTTPException(status_code=404, detail="Material requirement not found")
    lot = await _lot_or_404(current_user.tenant_id, data.lot_id)
    if lot["item_id"] != requirement["inventory_item_id"]:
        raise HTTPException(status_code=400, detail="Selected lot does not match the required inventory item")
    if not piece_fits(lot, requirement.get("required_width_inches"), requirement.get("required_length_inches")):
        raise HTTPException(status_code=409, detail="Selected roll, sheet, or remnant does not fit the required dimensions")
    used = float(data.consumed_quantity) + float(data.waste_quantity)
    if used < 0 or data.pulled_quantity < used:
        raise HTTPException(status_code=400, detail="Pulled quantity must cover consumed and wasted quantities")
    if data.waste_quantity and not data.waste_reason.strip():
        raise HTTPException(status_code=400, detail="Waste reason is required")
    if abs(float(data.pulled_quantity) - used - float(data.returned_quantity)) > 0.0001:
        raise HTTPException(status_code=400, detail="Pulled quantity must equal consumed, waste, and returned quantities")
    item = await _item_or_404(current_user.tenant_id, requirement["inventory_item_id"])
    if float(requirement.get("consumed_quantity", 0)) + float(data.consumed_quantity) > float(requirement["required_quantity"]) + 0.0001:
        raise HTTPException(status_code=400, detail="Consumed quantity cannot exceed the material requirement")
    remnant_quantity = 0.0
    if data.create_remnant:
        if not data.remnant_width_inches or not data.remnant_length_inches:
            raise HTTPException(status_code=400, detail="Remnant dimensions are required")
        if item.get("base_unit") == "sqft":
            remnant_quantity = roll_area_sqft(data.remnant_width_inches, data.remnant_length_inches)
        elif item.get("base_unit") in {"linear_ft", "feet", "ft"}:
            remnant_quantity = float(data.remnant_length_inches) / 12
        elif item.get("base_unit") in {"linear_in", "linear_inches", "inches", "in"}:
            remnant_quantity = float(data.remnant_length_inches)
        else:
            remnant_quantity = data.returned_quantity
        if abs(float(remnant_quantity) - float(data.returned_quantity)) > 0.01:
            raise HTTPException(status_code=400, detail="Returned quantity must match the remnant dimensions")
    reserved_for_lot = sum(
        float(a.get("quantity", 0)) for a in requirement.get("allocations", [])
        if a.get("lot_id") == lot["id"] and a.get("status") == "reserved"
    )
    reserved_reduction = min(reserved_for_lot, float(data.pulled_quantity))
    quantity_reduction = used + (float(data.returned_quantity) if data.create_remnant else 0)
    if allocatable_quantity(lot, reserved_for_lot) < quantity_reduction:
        raise HTTPException(status_code=409, detail="Not enough unreserved stock in selected lot")
    lot_updates: Dict[str, Any] = {"updated_at": now_iso()}
    if lot.get("remaining_length_inches") is not None and lot.get("width_inches"):
        if item.get("base_unit") == "sqft":
            length_reduction = quantity_reduction * 144 / float(lot["width_inches"])
        elif item.get("base_unit") in {"linear_ft", "feet", "ft"}:
            length_reduction = quantity_reduction * 12
        else:
            length_reduction = quantity_reduction
        next_length = float(lot.get("remaining_length_inches", 0)) - length_reduction
        if next_length < -0.0001:
            raise HTTPException(status_code=409, detail="Material pull exceeds remaining roll length")
        lot_updates["remaining_length_inches"] = max(next_length, 0)
    result = await db.inventory_lots.update_one(
        {
            "id": lot["id"], "tenant_id": current_user.tenant_id,
            "quantity_on_hand": {"$gte": quantity_reduction},
            "reserved_quantity": {"$gte": reserved_reduction},
            "$expr": {
                "$gte": [
                    {"$subtract": ["$quantity_on_hand", "$reserved_quantity"]},
                    quantity_reduction - reserved_reduction,
                ]
            },
        },
        {"$inc": {"quantity_on_hand": -quantity_reduction, "reserved_quantity": -reserved_reduction}, "$set": lot_updates},
    )
    if result.modified_count != 1:
        raise HTTPException(status_code=409, detail="Stock changed while materials were being pulled; refresh and try again")
    allocations = requirement.get("allocations", [])
    remaining_to_consume = reserved_reduction
    for allocation in allocations:
        if allocation.get("lot_id") != lot["id"] or allocation.get("status") != "reserved" or remaining_to_consume <= 0:
            continue
        take = min(float(allocation.get("quantity", 0)), remaining_to_consume)
        allocation["quantity"] = float(allocation.get("quantity", 0)) - take
        remaining_to_consume -= take
        if allocation["quantity"] <= 0:
            allocation["status"] = "consumed"
    total_consumed = float(requirement.get("consumed_quantity", 0)) + float(data.consumed_quantity)
    next_status = "consumed" if total_consumed >= float(requirement.get("required_quantity", 0)) else "pending"
    await db.material_requirements.update_one(
        {"id": requirement["id"], "tenant_id": current_user.tenant_id},
        {"$set": {"allocations": allocations, "status": next_status, "updated_at": now_iso()}, "$inc": {"reserved_quantity": -reserved_reduction, "consumed_quantity": data.consumed_quantity}},
    )
    common = dict(
        db=db, tenant_id=current_user.tenant_id, item_id=item["id"], lot_id=lot["id"],
        location_id=lot.get("location_id"), unit=requirement.get("unit", item.get("base_unit", "each")),
        actor_id=current_user.id, actor_name=current_user.full_name or "",
        source_type="material_requirement", source_id=requirement["id"], unit_cost=lot.get("unit_cost", 0),
    )
    await write_ledger(
        transaction_type="material_pull", quantity=0, reason=data.notes or "Pulled for production",
        metadata={"pulled_quantity": data.pulled_quantity}, **common,
    )
    if data.consumed_quantity:
        await write_ledger(transaction_type="consumption", quantity=-data.consumed_quantity, reason="Consumed in production", **common)
    if data.waste_quantity:
        await write_ledger(transaction_type="waste", quantity=-data.waste_quantity, reason=data.waste_reason, **common)
    if data.returned_quantity:
        await write_ledger(
            transaction_type="return", quantity=0, reason="Unused pulled material returned",
            metadata={"returned_quantity": data.returned_quantity}, **common,
        )
    if data.create_remnant:
        remnant = InventoryLot(
            tenant_id=current_user.tenant_id, item_id=item["id"], location_id=data.remnant_location_id or lot.get("location_id"),
            parent_lot_id=lot["id"], quantity_on_hand=remnant_quantity,
            unit_cost=lot.get("unit_cost", 0), width_inches=data.remnant_width_inches,
            remaining_length_inches=data.remnant_length_inches, notes=f"Remnant from ticket {ticket_id}",
        ).model_dump(mode="json")
        await db.inventory_lots.insert_one(remnant)
        await write_ledger(
            transaction_type="transfer", quantity=-remnant_quantity, reason="Transferred into reusable remnant",
            metadata={"destination_lot_id": remnant["id"]}, **common,
        )
        await write_ledger(
            db, tenant_id=current_user.tenant_id, transaction_type="transfer", item_id=item["id"],
            lot_id=remnant["id"], location_id=remnant.get("location_id"), quantity=remnant_quantity,
            unit=requirement.get("unit", item.get("base_unit", "each")), actor_id=current_user.id,
            actor_name=current_user.full_name or "", reason="Reusable remnant created",
            source_type="material_requirement", source_id=requirement["id"], unit_cost=lot.get("unit_cost", 0),
            metadata={"source_lot_id": lot["id"]},
        )
    updated_requirement = await db.material_requirements.find_one(
        {"id": requirement["id"], "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if requirement_outstanding(updated_requirement) <= 0:
        await db.material_requirements.update_one(
            {"id": requirement["id"], "tenant_id": current_user.tenant_id},
            {"$set": {"short_quantity": 0, "status": "consumed", "updated_at": now_iso()}},
        )
        await db.inventory_shortages.update_many(
            {
                "tenant_id": current_user.tenant_id, "requirement_id": requirement["id"],
                "status": {"$in": ["open", "ordered"]},
            },
            {"$set": {"status": "resolved", "updated_at": now_iso()}},
        )
    else:
        await reserve_requirement(db, updated_requirement, _actor(current_user))
    actual_cost = used * float(lot.get("unit_cost", 0))
    await db.job_tickets.update_one(
        {"id": ticket_id, "tenant_id": current_user.tenant_id},
        {"$inc": {"actual_cost": actual_cost}, "$set": {"updated_at": now_iso()}},
    )
    return {"message": "Materials pulled", "used_quantity": used, "actual_cost": round(actual_cost, 2)}


@router.get("/inventory/shortages")
async def list_shortages(current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.INVENTORY_VIEW)
    return await db.inventory_shortages.find({"tenant_id": current_user.tenant_id, "status": "open"}, {"_id": 0}).sort("created_at", 1).to_list(10000)


@router.get("/vendors")
async def list_vendors(current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    return await db.inventory_vendors.find({"tenant_id": current_user.tenant_id}, {"_id": 0}).sort("name", 1).to_list(1000)


@router.post("/vendors")
async def create_vendor(data: VendorInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.VENDORS_MANAGE)
    doc = {"id": new_id(), "tenant_id": current_user.tenant_id, **data.model_dump(), "created_at": now_iso(), "updated_at": now_iso()}
    await db.inventory_vendors.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/vendors/{vendor_id}")
async def update_vendor(vendor_id: str, data: VendorInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.VENDORS_MANAGE)
    result = await db.inventory_vendors.update_one(
        {"id": vendor_id, "tenant_id": current_user.tenant_id}, {"$set": {**data.model_dump(), "updated_at": now_iso()}}
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return await db.inventory_vendors.find_one({"id": vendor_id, "tenant_id": current_user.tenant_id}, {"_id": 0})


@router.get("/purchase-orders")
async def list_purchase_orders(status: str = "", current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id}
    if status:
        query["status"] = status
    return await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(5000)


@router.post("/purchase-orders")
async def create_purchase_order(data: PurchaseOrderInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    vendor = await db.inventory_vendors.find_one({"id": data.vendor_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    number = f"PO-{datetime.now(timezone.utc).strftime('%y%m%d')}-{new_id()[:8].upper()}"
    lines = []
    for line in data.lines:
        item = await _item_or_404(current_user.tenant_id, line.inventory_item_id)
        pack_size = _alias_pack_size(item, data.vendor_id, line.supplier_sku)
        line_doc = line.model_dump()
        line_doc.update({
            "id": new_id(), "received_quantity": 0, "base_received_quantity": 0,
            "base_ordered_quantity": _to_base_quantity(line.ordered_quantity, line.unit, item, pack_size),
            "base_unit": item.get("base_unit", "each"), "pack_size": pack_size,
            "damaged_quantity": 0, "missing_quantity": 0, "backordered_quantity": 0, "substituted_quantity": 0,
        })
        lines.append(line_doc)
    doc = {
        "id": new_id(), "tenant_id": current_user.tenant_id, "po_number": number,
        "vendor_id": data.vendor_id, "vendor_name": vendor["name"], "lines": lines, "status": "draft",
        "notes": data.notes, "expected_delivery_date": data.expected_delivery_date,
        "created_by": current_user.id, "created_at": now_iso(), "updated_at": now_iso(),
    }
    await db.purchase_orders.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/purchase-orders/from-shortages")
async def create_po_from_shortages(payload: Dict[str, Any], current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    shortage_ids = payload.get("shortage_ids") or []
    vendor_id = payload.get("vendor_id")
    shortages = await db.inventory_shortages.find(
        {"id": {"$in": shortage_ids}, "tenant_id": current_user.tenant_id, "status": "open"}, {"_id": 0}
    ).to_list(1000)
    if not shortages:
        raise HTTPException(status_code=400, detail="Select at least one open shortage")
    lines = []
    for shortage in shortages:
        item = await _item_or_404(current_user.tenant_id, shortage["inventory_item_id"])
        alias = next((a for a in item.get("aliases", []) if a.get("vendor_id") == vendor_id), {})
        lines.append({
            "inventory_item_id": item["id"], "supplier_sku": alias.get("supplier_sku", ""),
            "description": item["name"], "ordered_quantity": shortage["quantity"], "unit": shortage["unit"],
            "unit_cost": alias.get("last_known_cost", 0), "shortage_ids": [shortage["id"]],
        })
    return await create_purchase_order(PurchaseOrderInput(vendor_id=vendor_id, lines=lines), current_user)


@router.put("/purchase-orders/{po_id}")
async def update_purchase_order(po_id: str, payload: Dict[str, Any], current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    po = await db.purchase_orders.find_one(
        {"id": po_id, "tenant_id": current_user.tenant_id, "status": "draft"}, {"_id": 0}
    )
    if not po:
        raise HTTPException(status_code=409, detail="Only draft purchase orders can be edited")
    updates = {key: value for key, value in payload.items() if key in {"notes", "expected_delivery_date"}}
    if "lines" in payload:
        existing_lines = {line["id"]: line for line in po.get("lines", [])}
        lines = []
        for incoming in payload["lines"]:
            line = existing_lines.get(incoming.get("id"))
            if not line:
                raise HTTPException(status_code=400, detail="Purchase-order line not found")
            for key in ("supplier_sku", "description", "ordered_quantity", "unit", "unit_cost"):
                if key in incoming:
                    line[key] = incoming[key]
            if float(line.get("ordered_quantity", 0)) <= 0 or float(line.get("unit_cost", 0)) < 0:
                raise HTTPException(status_code=400, detail="PO quantities must be positive and costs cannot be negative")
            item = await _item_or_404(current_user.tenant_id, line["inventory_item_id"])
            pack_size = _alias_pack_size(item, po.get("vendor_id"), line.get("supplier_sku", ""))
            line["base_ordered_quantity"] = _to_base_quantity(
                float(line["ordered_quantity"]), line.get("unit", "each"), item, pack_size
            )
            line["base_unit"] = item.get("base_unit", "each")
            line["pack_size"] = pack_size
            lines.append(line)
        updates["lines"] = lines
    updates["updated_at"] = now_iso()
    await db.purchase_orders.update_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"$set": updates})
    return await db.purchase_orders.find_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"_id": 0})


@router.post("/purchase-orders/{po_id}/approve")
async def approve_purchase_order(po_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_APPROVE)
    result = await db.purchase_orders.update_one(
        {"id": po_id, "tenant_id": current_user.tenant_id, "status": "draft"},
        {"$set": {"status": "approved", "approved_by": current_user.id, "approved_at": now_iso(), "updated_at": now_iso()}},
    )
    if not result.modified_count:
        raise HTTPException(status_code=409, detail="Only draft purchase orders can be approved")
    po = await db.purchase_orders.find_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    shortage_ids = [shortage_id for line in po.get("lines", []) for shortage_id in line.get("shortage_ids", [])]
    if shortage_ids:
        await db.inventory_shortages.update_many(
            {"id": {"$in": shortage_ids}, "tenant_id": current_user.tenant_id, "status": "open"},
            {"$set": {"status": "ordered", "purchase_order_id": po_id, "updated_at": now_iso()}},
        )
    return po


@router.post("/purchase-orders/{po_id}/mark-sent")
async def mark_purchase_order_sent(po_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    result = await db.purchase_orders.update_one(
        {"id": po_id, "tenant_id": current_user.tenant_id, "status": "approved"},
        {"$set": {"status": "sent", "sent_at": now_iso(), "updated_at": now_iso()}},
    )
    if not result.modified_count:
        raise HTTPException(status_code=409, detail="Only approved purchase orders can be marked sent")
    return await db.purchase_orders.find_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"_id": 0})


@router.post("/purchase-orders/{po_id}/close")
async def close_purchase_order(po_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    result = await db.purchase_orders.update_one(
        {"id": po_id, "tenant_id": current_user.tenant_id, "status": {"$in": ["received", "partially_received"]}},
        {"$set": {"status": "closed", "closed_by": current_user.id, "closed_at": now_iso(), "updated_at": now_iso()}},
    )
    if not result.modified_count:
        raise HTTPException(status_code=409, detail="Only received or partially received purchase orders can be closed")
    return await db.purchase_orders.find_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"_id": 0})


@router.post("/purchase-orders/{po_id}/cancel")
async def cancel_purchase_order(po_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    po = await db.purchase_orders.find_one(
        {"id": po_id, "tenant_id": current_user.tenant_id, "status": {"$in": ["draft", "approved", "sent"]}},
        {"_id": 0},
    )
    if not po:
        raise HTTPException(status_code=409, detail="This purchase order cannot be cancelled")
    await db.purchase_orders.update_one(
        {"id": po_id, "tenant_id": current_user.tenant_id},
        {"$set": {"status": "cancelled", "cancelled_by": current_user.id, "cancelled_at": now_iso(), "updated_at": now_iso()}},
    )
    shortage_ids = [shortage_id for line in po.get("lines", []) for shortage_id in line.get("shortage_ids", [])]
    if shortage_ids:
        await db.inventory_shortages.update_many(
            {"id": {"$in": shortage_ids}, "tenant_id": current_user.tenant_id, "status": "ordered"},
            {"$set": {"status": "open", "updated_at": now_iso()}, "$unset": {"purchase_order_id": ""}},
        )
    return await db.purchase_orders.find_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"_id": 0})


@router.post("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(po_id: str, data: PurchaseOrderReceiveInput, current_user: UserInDB = Depends(get_current_active_user)):
    _require(current_user, Permission.PURCHASING_MANAGE)
    po = await db.purchase_orders.find_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    if po.get("status") not in {"approved", "sent", "partially_received"}:
        raise HTTPException(status_code=409, detail="Purchase order is not receivable")
    lines = po.get("lines", [])
    by_id = {line["id"]: line for line in lines}
    for received in data.lines:
        line = by_id.get(received.line_id)
        if not line:
            raise HTTPException(status_code=400, detail="Purchase-order line not found")
        remaining = float(line["ordered_quantity"]) - float(line.get("received_quantity", 0))
        if received.received_quantity < 0 or received.received_quantity > remaining:
            raise HTTPException(status_code=400, detail="Received quantity exceeds outstanding quantity")
        next_received = float(line.get("received_quantity", 0)) + float(received.received_quantity)
        classified = (
            next_received + float(received.damaged_quantity)
            + float(received.missing_quantity) + float(received.backordered_quantity)
            + float(received.substituted_quantity)
        )
        if classified > float(line["ordered_quantity"]):
            raise HTTPException(status_code=400, detail="Received and exception quantities exceed ordered quantity")
        line["received_quantity"] = next_received
        for field in ("damaged_quantity", "missing_quantity", "backordered_quantity", "substituted_quantity"):
            line[field] = float(getattr(received, field))
        if received.actual_unit_cost is not None:
            line["actual_unit_cost"] = received.actual_unit_cost
        if received.received_quantity:
            if received.location_id:
                await _location_or_404(current_user.tenant_id, received.location_id)
            item = await _item_or_404(current_user.tenant_id, line["inventory_item_id"])
            details = received.lot_details or {}
            pack_size = float(details.get("pack_size", line.get("pack_size", 1)) or 1)
            inventory_quantity = _to_base_quantity(
                float(received.received_quantity), line.get("unit", "each"), item, pack_size
            )
            order_unit_cost = float(
                received.actual_unit_cost if received.actual_unit_cost is not None else line.get("unit_cost", 0)
            )
            inventory_unit_cost = (
                float(received.received_quantity) * order_unit_cost / inventory_quantity if inventory_quantity else 0
            )
            line["base_received_quantity"] = float(line.get("base_received_quantity", 0)) + inventory_quantity
            lot = InventoryLot(
                tenant_id=current_user.tenant_id, item_id=item["id"], location_id=received.location_id,
                quantity_on_hand=inventory_quantity, unit_cost=inventory_unit_cost,
                source_purchase_order_id=po_id, lot_number=details.get("lot_number", ""),
                width_inches=details.get("width_inches"), length_inches=details.get("length_inches"),
                remaining_length_inches=details.get("remaining_length_inches"), sheet_width_inches=details.get("sheet_width_inches"),
                sheet_height_inches=details.get("sheet_height_inches"), thickness=details.get("thickness", ""),
                pack_size=pack_size, notes=received.notes,
            ).model_dump(mode="json")
            await db.inventory_lots.insert_one(lot)
            await write_ledger(
                db, tenant_id=current_user.tenant_id, transaction_type="receipt", item_id=item["id"], lot_id=lot["id"],
                location_id=received.location_id, quantity=inventory_quantity, unit=item["base_unit"],
                actor_id=current_user.id, actor_name=current_user.full_name or "", reason=f"Received {po['po_number']}",
                unit_cost=lot["unit_cost"], source_type="purchase_order", source_id=po_id,
            )
            if item.get("pricing_material_key"):
                pricing = await db.pricing_configuration.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0, "materials": 1})
                if not pricing:
                    pricing = await db.pricing_defaults.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0, "materials": 1})
                material = next(
                    (m for m in (pricing or {}).get("materials", []) if (m.get("key") or m.get("id")) == item["pricing_material_key"]),
                    None,
                )
                current_cost = float((material or {}).get("cost_per_sqft", (material or {}).get("cost_per_unit", 0)) or 0)
                if abs(current_cost - float(lot["unit_cost"])) > 0.01:
                    suggestion = {
                        "tenant_id": current_user.tenant_id, "inventory_item_id": item["id"],
                        "pricing_material_key": item["pricing_material_key"], "current_cost": current_cost,
                        "suggested_cost": float(lot["unit_cost"]), "source_purchase_order_id": po_id,
                        "status": "pending", "updated_at": now_iso(),
                    }
                    await db.pricing_cost_suggestions.update_one(
                        {"tenant_id": current_user.tenant_id, "inventory_item_id": item["id"], "status": "pending"},
                        {"$set": suggestion, "$setOnInsert": {"id": new_id(), "created_at": now_iso()}},
                        upsert=True,
                    )
            for shortage_id in line.get("shortage_ids", []):
                shortage = await db.inventory_shortages.find_one(
                    {"id": shortage_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
                )
                if shortage:
                    requirement = await db.material_requirements.find_one(
                        {"id": shortage["requirement_id"], "tenant_id": current_user.tenant_id}, {"_id": 0}
                    )
                    if requirement:
                        await reserve_requirement(db, requirement, _actor(current_user))
    complete = all(float(line.get("received_quantity", 0)) >= float(line.get("ordered_quantity", 0)) for line in lines)
    status = "received" if complete else "partially_received"
    await db.purchase_orders.update_one(
        {"id": po_id, "tenant_id": current_user.tenant_id},
        {"$set": {"lines": lines, "status": status, "receiving_notes": data.notes, "updated_at": now_iso()}},
    )
    return await db.purchase_orders.find_one({"id": po_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
