from datetime import datetime, timezone
from typing import Optional, List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models import UserInDB
from server import db, get_current_active_user

router = APIRouter(prefix="/appointments", tags=["Appointments"])


class AppointmentCreate(BaseModel):
    title: str = "Appointment"
    appointment_type: Optional[str] = None  # site_survey, install, consultation, pickup, dropoff, other
    customer_id: Optional[str] = None
    order_id: Optional[str] = None       # link to order
    employee_id: Optional[str] = None    # assigned employee
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    send_reminder: bool = True


class AppointmentUpdate(BaseModel):
    title: Optional[str] = None
    appointment_type: Optional[str] = None
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    employee_id: Optional[str] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None         # scheduled, confirmed, completed, cancelled, rescheduled
    send_reminder: Optional[bool] = None


class AppointmentResponse(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    title: str = "Appointment"
    status: str = "scheduled"
    appointment_type: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    order_id: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    # Legacy field aliases
    scheduled_at: Optional[str] = None
    scheduled_date: Optional[str] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    send_reminder: bool = True
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Kept for backwards compat with old code
class AppointmentDetailResponse(AppointmentResponse):
    related_job_id: Optional[str] = None


def _doc_to_response(doc: dict) -> AppointmentResponse:
    scheduled_start = doc.get("scheduled_start") or doc.get("scheduled_at")
    return AppointmentResponse(
        id=doc["id"],
        tenant_id=doc.get("tenant_id"),
        title=doc.get("title") or "Appointment",
        status=doc.get("status") or "scheduled",
        appointment_type=doc.get("appointment_type"),
        customer_id=doc.get("customer_id"),
        customer_name=doc.get("customer_name"),
        order_id=doc.get("order_id") or doc.get("job_id"),
        employee_id=doc.get("employee_id"),
        employee_name=doc.get("employee_name"),
        scheduled_start=scheduled_start,
        scheduled_end=doc.get("scheduled_end"),
        scheduled_at=scheduled_start,
        scheduled_date=doc.get("scheduled_date") or (scheduled_start[:10] if scheduled_start else None),
        duration_minutes=doc.get("duration_minutes"),
        location=doc.get("location"),
        description=doc.get("description"),
        notes=doc.get("notes"),
        send_reminder=doc.get("send_reminder", True),
        created_by=doc.get("created_by"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


@router.post("", response_model=AppointmentResponse)
async def create_appointment(
    input: AppointmentCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Create a new appointment (site survey, install, consultation, etc.)"""
    # Resolve customer name
    customer_name = None
    if input.customer_id:
        cust = await db.customers.find_one(
            {"id": input.customer_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1},
        )
        customer_name = (cust or {}).get("name")

    # Resolve employee name
    employee_name = None
    if input.employee_id:
        emp = await db.employees.find_one(
            {"id": input.employee_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1},
        )
        employee_name = (emp or {}).get("name")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "title": input.title,
        "status": "scheduled",
        "appointment_type": input.appointment_type,
        "customer_id": input.customer_id,
        "customer_name": customer_name,
        "order_id": input.order_id,
        "employee_id": input.employee_id,
        "employee_name": employee_name,
        "scheduled_start": input.scheduled_start,
        "scheduled_end": input.scheduled_end,
        "scheduled_at": input.scheduled_start,  # legacy alias
        "scheduled_date": input.scheduled_start[:10] if input.scheduled_start else None,
        "duration_minutes": input.duration_minutes,
        "location": input.location,
        "description": input.description,
        "notes": input.notes,
        "send_reminder": input.send_reminder,
        "created_by": current_user.id,
        "created_at": now,
        "updated_at": now,
    }
    await db.appointments.insert_one(doc)
    doc.pop("_id", None)
    return _doc_to_response(doc)


@router.get("", response_model=List[AppointmentResponse])
async def list_appointments(
    customer_id: Optional[str] = None,
    employee_id: Optional[str] = None,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    current_user: UserInDB = Depends(get_current_active_user),
):
    query: dict = {"tenant_id": current_user.tenant_id}
    if customer_id:
        query["customer_id"] = customer_id
    if employee_id:
        query["employee_id"] = employee_id
    if order_id:
        query["$or"] = [{"order_id": order_id}, {"job_id": order_id}]
    if status:
        query["status"] = status
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        query["scheduled_start"] = date_filter

    docs = await db.appointments.find(query, {"_id": 0}).sort("scheduled_start", 1).to_list(limit)
    return [_doc_to_response(d) for d in docs]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_detail(
    appointment_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    doc = await db.appointments.find_one(
        {"id": appointment_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Appointment not found")

    # Resolve customer name if missing
    if doc.get("customer_id") and not doc.get("customer_name"):
        cust = await db.customers.find_one(
            {"id": doc["customer_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1},
        )
        doc["customer_name"] = (cust or {}).get("name")

    return _doc_to_response(doc)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    input: AppointmentUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    doc = await db.appointments.find_one(
        {"id": appointment_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Appointment not found")

    updates = {k: v for k, v in input.model_dump(exclude_none=True).items()}

    if "scheduled_start" in updates:
        updates["scheduled_at"] = updates["scheduled_start"]
        s = updates["scheduled_start"]
        updates["scheduled_date"] = s[:10] if s else None

    if "customer_id" in updates and updates["customer_id"] != doc.get("customer_id"):
        cust = await db.customers.find_one(
            {"id": updates["customer_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1},
        )
        updates["customer_name"] = (cust or {}).get("name")

    if "employee_id" in updates and updates["employee_id"] != doc.get("employee_id"):
        emp = await db.employees.find_one(
            {"id": updates["employee_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1},
        )
        updates["employee_name"] = (emp or {}).get("name")

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.appointments.update_one({"id": appointment_id}, {"$set": updates})
    doc.update(updates)
    return _doc_to_response(doc)


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    result = await db.appointments.delete_one(
        {"id": appointment_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": "Appointment deleted"}
