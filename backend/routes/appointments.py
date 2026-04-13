from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from models import UserInDB
from server import db, get_current_active_user

router = APIRouter(prefix="/appointments", tags=["Appointments"])


class AppointmentDetailResponse(BaseModel):
    id: str
    title: str = "Appointment"
    status: str = "scheduled"
    scheduled_at: Optional[str] = None
    scheduled_date: Optional[str] = None
    duration_minutes: Optional[int] = None
    appointment_type: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    related_job_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/{appointment_id}", response_model=AppointmentDetailResponse)
async def get_appointment_detail(
    appointment_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    appointment = await db.appointments.find_one(
        {"id": appointment_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    customer_name = appointment.get("customer_name")
    customer_id = appointment.get("customer_id")
    if customer_id and not customer_name:
        customer = await db.customers.find_one(
            {"id": customer_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1},
        )
        customer_name = (customer or {}).get("name")

    scheduled_at = appointment.get("scheduled_at")
    scheduled_date = appointment.get("scheduled_date")
    updated_at = appointment.get("updated_at") or datetime.now(timezone.utc).isoformat()

    return AppointmentDetailResponse(
        id=appointment["id"],
        title=appointment.get("title") or "Appointment",
        status=appointment.get("status") or "scheduled",
        scheduled_at=scheduled_at,
        scheduled_date=scheduled_date,
        duration_minutes=appointment.get("duration_minutes"),
        appointment_type=appointment.get("appointment_type"),
        location=appointment.get("location"),
        description=appointment.get("description"),
        notes=appointment.get("notes"),
        customer_id=customer_id,
        customer_name=customer_name,
        related_job_id=appointment.get("job_id"),
        created_at=appointment.get("created_at"),
        updated_at=updated_at,
    )