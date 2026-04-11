"""Generic order drawing routes for order-level, item-level, and image markups."""

import base64
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from server import db, logger, get_current_active_user
from models import UserInDB
from services.object_storage import get_object, put_object

router = APIRouter(prefix="/order-drawings", tags=["Order Drawings"])

ALLOWED_TYPES = {"sketch", "markup", "measurement_note", "install_note", "layout_note", "other", "signature"}
ALLOWED_PARENT_TYPES = {"order", "job_ticket", "uploaded_image"}
ALLOWED_STATUS = {"draft", "saved", "finalized"}


class DrawingCreate(BaseModel):
    id: Optional[str] = None
    order_id: str
    parent_type: str = "order"
    parent_id: Optional[str] = None
    job_ticket_id: Optional[str] = None
    uploaded_image_id: Optional[str] = None
    drawing_type: str = "sketch"
    type: Optional[str] = None
    label: str = ""
    title: Optional[str] = None
    notes: Optional[str] = ""
    image_data: str
    status: str = "saved"
    tags: List[str] = Field(default_factory=list)
    requires_attention: bool = False


class DrawingUpdate(BaseModel):
    label: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    requires_attention: Optional[bool] = None


async def _validate_context(input: DrawingCreate, tenant_id: str):
    order = await db.orders.find_one({"id": input.order_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if input.parent_type == "job_ticket":
        target_id = input.job_ticket_id or input.parent_id
        ticket = await db.job_tickets.find_one({"id": target_id, "order_id": input.order_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1})
        if not ticket:
            raise HTTPException(status_code=404, detail="Job ticket not found for this order")
        input.job_ticket_id = target_id
        input.parent_id = target_id
    elif input.parent_type == "uploaded_image":
        target_id = input.uploaded_image_id or input.parent_id
        file_doc = await db.order_files.find_one({"id": target_id, "order_id": input.order_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1})
        if not file_doc:
            raise HTTPException(status_code=404, detail="Uploaded image not found for this order")
        input.uploaded_image_id = target_id
        input.parent_id = target_id
    else:
        input.parent_id = input.order_id
    return order


def _decode_image(image_data: str) -> bytes:
    try:
        encoded = image_data.split(",", 1)[1] if "," in image_data else image_data
        return base64.b64decode(encoded)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid image data") from exc


def _serialize_drawing(drawing: dict) -> dict:
    payload = {**drawing}
    payload.pop("_id", None)
    payload["label"] = payload.get("title") or payload.get("label")
    payload["type"] = payload.get("drawing_type")
    return payload


@router.get("")
async def query_drawings(
    order_id: Optional[str] = None,
    job_ticket_id: Optional[str] = None,
    uploaded_image_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
):
    query = {"tenant_id": current_user.tenant_id, "visibility_status": {"$ne": "deleted"}}
    if order_id:
        query["order_id"] = order_id
    if job_ticket_id:
        query["job_ticket_id"] = job_ticket_id
    if uploaded_image_id:
        query["uploaded_image_id"] = uploaded_image_id
    if status:
        query["status"] = status
    drawings = await db.order_drawings.find(query, {"_id": 0}).sort("updated_at", -1).to_list(200)
    return [_serialize_drawing(drawing) for drawing in drawings]


@router.get("/{order_id}")
async def list_drawings(order_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    drawings = await db.order_drawings.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id, "visibility_status": {"$ne": "deleted"}},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(200)
    return [_serialize_drawing(drawing) for drawing in drawings]


@router.post("/")
async def create_drawing(input: DrawingCreate, current_user: UserInDB = Depends(get_current_active_user)):
    tenant_id = current_user.tenant_id
    input.parent_type = (input.parent_type or "order").lower()
    input.drawing_type = (input.type or input.drawing_type or "sketch").lower()
    input.status = (input.status or "saved").lower()

    if input.parent_type not in ALLOWED_PARENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid drawing context")
    if input.drawing_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid drawing type")
    if input.status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="Invalid drawing status")

    await _validate_context(input, tenant_id)
    img_bytes = _decode_image(input.image_data)
    if len(img_bytes) < 150:
        raise HTTPException(status_code=400, detail="Drawing appears to be blank. Please draw something before saving.")
    if len(img_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Drawing is too large. Please simplify and try again.")

    drawing_id = input.id or str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    storage_path = f"signguy-ai/orders/{input.order_id}/drawings/{drawing_id}-{timestamp}.png"
    try:
        result = put_object(storage_path, img_bytes, "image/png")
        stored_path = result.get("path", storage_path)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Object storage upload failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to upload drawing. Please try again.") from exc

    existing = await db.order_drawings.find_one({"id": drawing_id, "tenant_id": tenant_id}, {"_id": 0})
    now = datetime.now(timezone.utc).isoformat()
    drawing = {
        "id": drawing_id,
        "order_id": input.order_id,
        "parent_type": input.parent_type,
        "parent_id": input.parent_id,
        "job_ticket_id": input.job_ticket_id,
        "uploaded_image_id": input.uploaded_image_id,
        "tenant_id": tenant_id,
        "drawing_type": input.drawing_type,
        "title": (input.title or input.label or input.drawing_type.replace("_", " ").title()).strip(),
        "label": (input.title or input.label or input.drawing_type.replace("_", " ").title()).strip(),
        "notes": input.notes or "",
        "storage_path": stored_path,
        "image_url": f"/api/order-drawings/file/{drawing_id}",
        "thumbnail_url": f"/api/order-drawings/file/{drawing_id}",
        "file_size": len(img_bytes),
        "created_by": existing.get("created_by") if existing else (current_user.full_name or current_user.email),
        "created_by_id": existing.get("created_by_id") if existing else current_user.id,
        "created_at": existing.get("created_at", now) if existing else now,
        "updated_at": now,
        "tags": input.tags,
        "requires_attention": input.requires_attention,
        "status": input.status,
        "visibility_status": existing.get("visibility_status", "active") if existing else "active",
    }

    await db.order_drawings.update_one({"id": drawing_id}, {"$set": drawing}, upsert=True)
    return _serialize_drawing(drawing)


@router.get("/file/{drawing_id}")
async def get_drawing_file(drawing_id: str):
    drawing = await db.order_drawings.find_one({"id": drawing_id, "visibility_status": {"$ne": "deleted"}}, {"_id": 0, "storage_path": 1})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    try:
        data, content_type = get_object(drawing["storage_path"])
        return Response(content=data, media_type=content_type or "image/png")
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to retrieve drawing file: {exc}")
        raise HTTPException(status_code=500, detail="Failed to load drawing") from exc


@router.put("/{drawing_id}")
async def update_drawing(drawing_id: str, input: DrawingUpdate, current_user: UserInDB = Depends(get_current_active_user)):
    drawing = await db.order_drawings.find_one({"id": drawing_id, "tenant_id": current_user.tenant_id, "visibility_status": {"$ne": "deleted"}}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    updates = {key: value for key, value in input.model_dump().items() if value is not None}
    if updates.get("title") and "label" not in updates:
        updates["label"] = updates["title"]
    if updates.get("status") and updates["status"] not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="Invalid drawing status")
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.order_drawings.update_one({"id": drawing_id}, {"$set": updates})
    updated = await db.order_drawings.find_one({"id": drawing_id}, {"_id": 0})
    return _serialize_drawing(updated)


@router.delete("/{drawing_id}")
async def delete_drawing(drawing_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    if current_user.role not in ("owner", "admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Only admins can delete drawings")
    drawing = await db.order_drawings.find_one({"id": drawing_id, "tenant_id": current_user.tenant_id, "visibility_status": {"$ne": "deleted"}}, {"_id": 0, "id": 1})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    await db.order_drawings.update_one({"id": drawing_id}, {"$set": {"visibility_status": "deleted", "deleted_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Drawing deleted"}
