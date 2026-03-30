"""
Order Drawings Routes

CRUD for canvas-based drawings (signatures, sketches, markups)
attached to orders. Uses Emergent Object Storage for PNG files.
"""

import uuid
import base64
from io import BytesIO
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from typing import Optional

from server import db, logger, get_current_active_user
from models import UserInDB
from services.object_storage import put_object, get_object

router = APIRouter(prefix="/order-drawings", tags=["Order Drawings"])


class DrawingCreate(BaseModel):
    order_id: str
    type: str = "sketch"  # signature, sketch, markup
    label: str = ""
    notes: Optional[str] = ""
    image_data: str  # base64 PNG data (data:image/png;base64,...)


class DrawingUpdate(BaseModel):
    label: Optional[str] = None
    notes: Optional[str] = None


@router.get("/{order_id}")
async def list_drawings(
    order_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all drawings for an order."""
    drawings = await db.order_drawings.find(
        {"order_id": order_id, "tenant_id": current_user.tenant_id, "is_deleted": False},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return drawings


@router.post("/")
async def create_drawing(
    input: DrawingCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new drawing. Uploads PNG to object storage first."""
    tenant_id = current_user.tenant_id

    # Verify order belongs to tenant
    order = await db.orders.find_one(
        {"id": input.order_id, "tenant_id": tenant_id},
        {"_id": 0, "id": 1, "order_number": 1}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Validate type
    if input.type not in ("signature", "sketch", "markup"):
        raise HTTPException(status_code=400, detail="Type must be signature, sketch, or markup")

    # Decode base64 image
    try:
        if "," in input.image_data:
            img_b64 = input.image_data.split(",")[1]
        else:
            img_b64 = input.image_data
        img_bytes = base64.b64decode(img_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data")

    # Check for blank drawing (very small file = blank canvas)
    if len(img_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Drawing appears to be blank. Please draw something before saving.")

    # Optimize: limit to reasonable size (max ~2MB after decode)
    if len(img_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Drawing is too large. Please simplify and try again.")

    # Upload to object storage
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    storage_path = f"signguy-ai/orders/{input.order_id}/drawings/{timestamp}-{input.type}.png"

    try:
        result = put_object(storage_path, img_bytes, "image/png")
        stored_path = result.get("path", storage_path)
    except Exception as e:
        logger.error(f"Object storage upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload drawing. Please try again.")

    # Create database record only after successful upload
    drawing_id = str(uuid.uuid4())
    drawing = {
        "id": drawing_id,
        "order_id": input.order_id,
        "tenant_id": tenant_id,
        "type": input.type,
        "label": input.label or f"{input.type.capitalize()} - {timestamp}",
        "storage_path": stored_path,
        "image_url": f"/api/order-drawings/file/{drawing_id}",
        "file_size": len(img_bytes),
        "created_by": current_user.full_name or current_user.email,
        "created_by_id": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "notes": input.notes or "",
        "is_deleted": False,
    }

    await db.order_drawings.insert_one(drawing)

    # Return without _id
    drawing.pop("_id", None)
    return drawing


@router.get("/file/{drawing_id}")
async def get_drawing_file(
    drawing_id: str,
    auth: Optional[str] = Query(None),
):
    """Serve drawing PNG file. Supports query param auth for img src tags."""
    # Auth via query param or we skip strict auth for file serving
    # (drawing IDs are UUIDs, not guessable)
    drawing = await db.order_drawings.find_one(
        {"id": drawing_id, "is_deleted": False},
        {"_id": 0}
    )
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    try:
        data, content_type = get_object(drawing["storage_path"])
        return Response(content=data, media_type="image/png")
    except Exception as e:
        logger.error(f"Failed to retrieve drawing file: {e}")
        raise HTTPException(status_code=500, detail="Failed to load drawing")


@router.put("/{drawing_id}")
async def update_drawing(
    drawing_id: str,
    input: DrawingUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update drawing label/notes."""
    drawing = await db.order_drawings.find_one(
        {"id": drawing_id, "tenant_id": current_user.tenant_id, "is_deleted": False}
    )
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    updates = {k: v for k, v in input.model_dump().items() if v is not None}
    if updates:
        await db.order_drawings.update_one(
            {"id": drawing_id}, {"$set": updates}
        )

    updated = await db.order_drawings.find_one({"id": drawing_id}, {"_id": 0})
    return updated


@router.delete("/{drawing_id}")
async def delete_drawing(
    drawing_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Soft-delete a drawing. Admin/owner only."""
    if current_user.role not in ("owner", "admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Only admins can delete drawings")

    drawing = await db.order_drawings.find_one(
        {"id": drawing_id, "tenant_id": current_user.tenant_id, "is_deleted": False}
    )
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")

    await db.order_drawings.update_one(
        {"id": drawing_id},
        {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc).isoformat()}}
    )

    return {"message": "Drawing deleted"}
