"""
Wrap Command Center — Phase 2F: Photos & Files.

Real upload/list/update/delete for wrap-specific files. Files are stored in
the existing object-storage backend and tracked in the ``wrap_files``
collection. Categories follow the Phase 2F spec.

This module deliberately does NOT touch the existing ``order_files`` pipeline.
Wrap files are scoped to a single ``job_ticket_id`` and persist independently
so the wrap workflow stays self-contained.
"""
from datetime import datetime, timezone
from typing import Optional, List
import uuid
import mimetypes
import base64

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from pydantic import BaseModel

from models import UserInDB
from server import db, get_current_active_user
from services.object_storage import get_object, put_object
from services.storage_config import APP_NAME

from .core import _load_ticket_or_404, _now

files_router = APIRouter(tags=["Wrap Command Center — Files"])

WRAP_FILE_CATEGORIES = {
    "Customer Uploads",
    "Logo Files",
    "Vehicle Photos",
    "Inspection Photos",
    "Damage Photos",
    "Mockups",
    "Proofs",
    "Print Files",
    "Before Photos",
    "During Photos",
    "After Photos",
    "Signed Documents",
    "Aftercare Documents",
    "Final Packets",
}

ALLOWED_MIME_PREFIXES = ("image/", "video/", "audio/")
ALLOWED_MIME_EXACT = {
    "application/pdf",
    "application/postscript",
    "application/illustrator",
    "application/x-photoshop",
    "application/vnd.adobe.photoshop",
    "application/zip",
    "application/x-zip-compressed",
    "application/octet-stream",
    "text/plain",
    "text/csv",
    "application/json",
    "application/xml",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
MAX_BYTES = 25 * 1024 * 1024  # 25MB cap per upload


def _build_wrap_file_storage_path(tenant_id: str, ticket_id: str, file_id: str, filename: str) -> str:
    guessed_extension = mimetypes.guess_extension(
        mimetypes.guess_type(filename or "")[0] or ""
    ) or ""
    if not guessed_extension and filename and "." in filename:
        guessed_extension = f".{filename.rsplit('.', 1)[-1]}"
    return f"{APP_NAME}/wrap/{tenant_id}/{ticket_id}/{file_id}{guessed_extension or '.bin'}"


def _safe_file_doc(doc: dict) -> dict:
    return {k: v for k, v in (doc or {}).items() if k != "_id"}


class WrapFileUpdate(BaseModel):
    category: Optional[str] = None
    notes: Optional[str] = None
    customer_visible: Optional[bool] = None
    marketing_allowed: Optional[bool] = None
    filename: Optional[str] = None  # display rename only


@files_router.get("/items/{ticket_id}/files")
async def list_wrap_files(
    ticket_id: str,
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    query = {"tenant_id": current_user.tenant_id, "ticket_id": ticket_id}
    if category:
        if category not in WRAP_FILE_CATEGORIES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Allowed: {sorted(WRAP_FILE_CATEGORIES)}",
            )
        query["category"] = category
    cursor = db.wrap_files.find(query, {"_id": 0}).sort("uploaded_at", -1)
    files = await cursor.to_list(500)
    counts: dict = {}
    for f in files:
        counts[f.get("category", "Customer Uploads")] = counts.get(
            f.get("category", "Customer Uploads"), 0
        ) + 1
    return {
        "files": files,
        "categories": sorted(WRAP_FILE_CATEGORIES),
        "counts_by_category": counts,
        "total": len(files),
    }


@files_router.post("/items/{ticket_id}/files")
async def upload_wrap_file(
    ticket_id: str,
    file: UploadFile = File(...),
    category: str = Form("Customer Uploads"),
    notes: str = Form(""),
    customer_visible: bool = Form(False),
    marketing_allowed: bool = Form(False),
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    if category not in WRAP_FILE_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Allowed: {sorted(WRAP_FILE_CATEGORIES)}",
        )
    ct = (file.content_type or "").lower()
    if not (any(ct.startswith(p) for p in ALLOWED_MIME_PREFIXES) or ct in ALLOWED_MIME_EXACT):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type or 'unknown'}")
    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 25MB)")

    file_id = str(uuid.uuid4())
    original_filename = file.filename or "attachment.bin"
    storage_path = _build_wrap_file_storage_path(
        current_user.tenant_id, ticket_id, file_id, original_filename
    )
    result = put_object(storage_path, contents, file.content_type or "application/octet-stream")

    doc = {
        "id": file_id,
        "ticket_id": ticket_id,
        "order_id": ticket.get("order_id", ""),
        "tenant_id": current_user.tenant_id,
        "category": category,
        "filename": original_filename,
        "original_filename": original_filename,
        "content_type": file.content_type or "application/octet-stream",
        "size": len(contents),
        "storage_path": result.get("path", storage_path),
        "storage_backend": "emergent_object_storage",
        "uploaded_by": getattr(current_user, "email", "") or current_user.id,
        "uploaded_at": _now(),
        "notes": notes or "",
        "customer_visible": bool(customer_visible),
        "marketing_allowed": bool(marketing_allowed),
        "source": "wrap_command_center",
    }
    await db.wrap_files.insert_one(doc.copy())
    return _safe_file_doc(doc)


@files_router.put("/items/{ticket_id}/files/{file_id}")
async def update_wrap_file(
    ticket_id: str,
    file_id: str,
    payload: WrapFileUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    updates = payload.model_dump(exclude_unset=True)
    if "category" in updates and updates["category"] not in WRAP_FILE_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Allowed: {sorted(WRAP_FILE_CATEGORIES)}",
        )
    updates["updated_at"] = _now()
    result = await db.wrap_files.update_one(
        {"id": file_id, "ticket_id": ticket_id, "tenant_id": current_user.tenant_id},
        {"$set": updates},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Wrap file not found")
    doc = await db.wrap_files.find_one(
        {"id": file_id, "ticket_id": ticket_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    return _safe_file_doc(doc)


@files_router.delete("/items/{ticket_id}/files/{file_id}")
async def delete_wrap_file(
    ticket_id: str,
    file_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    result = await db.wrap_files.delete_one(
        {"id": file_id, "ticket_id": ticket_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Wrap file not found")
    return {"deleted": True, "id": file_id}


@files_router.get("/items/{ticket_id}/files/{file_id}/content")
async def download_wrap_file(
    ticket_id: str,
    file_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    file_doc = await db.wrap_files.find_one(
        {"id": file_id, "ticket_id": ticket_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not file_doc:
        raise HTTPException(status_code=404, detail="Wrap file not found")
    media_type = (
        file_doc.get("content_type")
        or mimetypes.guess_type(file_doc.get("filename", ""))[0]
        or "application/octet-stream"
    )
    try:
        storage_path = file_doc.get("storage_path")
        if storage_path:
            content, content_type = get_object(storage_path)
            media_type = content_type or media_type
        else:
            content = base64.b64decode(file_doc.get("file_data", ""))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Failed to load wrap file") from exc
    return Response(content=content, media_type=media_type)


# Internal helper used by wrap/pdfs.py to record a generated PDF as a wrap_file.
async def _record_generated_pdf(
    *,
    tenant_id: str,
    ticket_id: str,
    order_id: str,
    pdf_bytes: bytes,
    filename: str,
    category: str,
    uploaded_by: str,
    notes: str = "",
    customer_visible: bool = False,
) -> dict:
    if category not in WRAP_FILE_CATEGORIES:
        category = "Signed Documents"
    file_id = str(uuid.uuid4())
    storage_path = _build_wrap_file_storage_path(tenant_id, ticket_id, file_id, filename)
    result = put_object(storage_path, pdf_bytes, "application/pdf")
    doc = {
        "id": file_id,
        "ticket_id": ticket_id,
        "order_id": order_id,
        "tenant_id": tenant_id,
        "category": category,
        "filename": filename,
        "original_filename": filename,
        "content_type": "application/pdf",
        "size": len(pdf_bytes),
        "storage_path": result.get("path", storage_path),
        "storage_backend": "emergent_object_storage",
        "uploaded_by": uploaded_by,
        "uploaded_at": _now(),
        "notes": notes,
        "customer_visible": bool(customer_visible),
        "marketing_allowed": False,
        "source": "wrap_command_center_pdf",
        "generated": True,
    }
    await db.wrap_files.insert_one(doc.copy())
    return _safe_file_doc(doc)
