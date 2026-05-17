from datetime import datetime, timezone
from typing import Optional, List
import os
import uuid
import hmac
import hashlib
import base64
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from models import UserInDB
from server import db, get_current_active_user
from core_runtime import SECRET_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["Appointments"])

# Public router — no auth, used for tokenized customer Confirm/Reject links
# embedded in appointment notification emails. Lives at /api/public-appointments.
public_router = APIRouter(prefix="/public-appointments", tags=["Appointments"])


# ─────────── Phase: Email C/R quick-action token helpers ───────────
# Tokens are URL-safe base64 of "{appointment_id}.{action}.{hmac}" where the
# HMAC is computed over "{appointment_id}|{action}" with the server SECRET_KEY.
# This keeps the token short, stateless, and tamper-proof without any DB or
# schema changes. The customer never logs in to confirm/reject.
def _make_action_token(appointment_id: str, action: str) -> str:
    payload = f"{appointment_id}|{action}"
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    raw = f"{appointment_id}.{action}.{sig_b64}"
    return base64.urlsafe_b64encode(raw.encode()).rstrip(b"=").decode()


def _decode_action_token(token: str) -> Optional[dict]:
    try:
        padded = token + "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode(padded.encode()).decode()
        parts = raw.split(".")
        if len(parts) != 3:
            return None
        appointment_id, action, sig_b64 = parts
        if action not in {"confirm", "reject"}:
            return None
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            f"{appointment_id}|{action}".encode(),
            hashlib.sha256,
        ).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_sig).rstrip(b"=").decode()
        if not hmac.compare_digest(expected_b64, sig_b64):
            return None
        return {"appointment_id": appointment_id, "action": action}
    except Exception:  # noqa: BLE001
        return None


def _public_base_url(tenant: dict) -> str:
    """Resolve the public base URL for tokenized links.

    Priority: tenant.portal_url → APP_PUBLIC_URL env → REACT_APP_BACKEND_URL env.
    Falls back to "" if nothing is configured.
    """
    return (
        (tenant or {}).get("portal_url")
        or os.environ.get("APP_PUBLIC_URL")
        or os.environ.get("REACT_APP_BACKEND_URL")
        or ""
    ).rstrip("/")


def _result_html(title: str, message: str, success: bool = True) -> str:
    """Tiny standalone HTML response page for the customer after they click
    Confirm or Reject. No JS, no external assets — works in any email client
    preview / mobile browser.
    """
    color = "#0EA5E9" if success else "#DC2626"
    icon = "✓" if success else "ℹ"
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
 body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#F8FAFC;color:#0F172A;margin:0;padding:24px;}}
 .card{{max-width:480px;margin:48px auto;background:#fff;border-radius:12px;box-shadow:0 8px 32px rgba(15,23,42,0.08);padding:28px;text-align:center;}}
 .icon{{width:56px;height:56px;line-height:56px;border-radius:50%;background:{color};color:#fff;font-size:28px;margin:0 auto 16px;}}
 h1{{font-size:22px;margin:0 0 8px;color:{color};}}
 p{{color:#475569;line-height:1.55;margin:8px 0;}}
</style></head><body>
<div class="card"><div class="icon">{icon}</div>
<h1>{title}</h1><p>{message}</p></div></body></html>"""


async def _send_customer_appointment_email(appointment: dict, tenant: dict) -> None:
    """Send the customer an appointment notification with Confirm / Reject
    quick-action buttons. Safe-no-op if the customer has no email or if the
    email service isn't configured.
    """
    try:
        # Resolve customer email
        customer_email = None
        if appointment.get("customer_id"):
            cust = await db.customers.find_one(
                {"id": appointment["customer_id"], "tenant_id": appointment.get("tenant_id")},
                {"_id": 0, "email": 1, "name": 1},
            )
            customer_email = (cust or {}).get("email")
        if not customer_email:
            return  # nothing to email

        from services.email_service import email_service
        if not email_service.is_configured():
            logger.info("Email service not configured; skipping appointment email")
            return

        base = _public_base_url(tenant)
        confirm_url = f"{base}/api/public-appointments/{_make_action_token(appointment['id'], 'confirm')}/confirm"
        reject_url = f"{base}/api/public-appointments/{_make_action_token(appointment['id'], 'reject')}/reject"

        title = appointment.get("title") or "Appointment"
        when = (
            appointment.get("scheduled_start")
            or appointment.get("scheduled_at")
            or appointment.get("scheduled_date")
            or "TBD"
        )
        location = appointment.get("location") or ""
        shop_name = (tenant or {}).get("name") or "Your Sign Shop"
        appt_type = (appointment.get("appointment_type") or "").replace("_", " ").title() or "Appointment"

        html = f"""
        <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;max-width:560px;margin:0 auto;color:#0F172A;">
          <h2 style="color:#0F172A;margin:0 0 12px;">{title}</h2>
          <p style="color:#475569;line-height:1.5;">{shop_name} has scheduled <strong>{appt_type}</strong> with you.</p>
          <table style="margin:16px 0;border-collapse:collapse;width:100%;">
            <tr><td style="padding:6px 0;color:#64748B;width:120px;">When</td><td style="padding:6px 0;"><strong>{when}</strong></td></tr>
            {f'<tr><td style="padding:6px 0;color:#64748B;">Location</td><td style="padding:6px 0;">{location}</td></tr>' if location else ''}
          </table>
          <p style="color:#475569;line-height:1.5;">Please confirm this time works for you, or let us know if you need a change.</p>
          <div style="margin:24px 0;text-align:center;">
            <a href="{confirm_url}"
               style="display:inline-block;background:#0EA5E9;color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;margin:0 6px;">
              ✓ Confirm Appointment
            </a>
            <a href="{reject_url}"
               style="display:inline-block;background:#fff;color:#0F172A;border:1px solid #CBD5E1;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;margin:0 6px;">
              Request Change
            </a>
          </div>
          <p style="color:#94A3B8;font-size:12px;line-height:1.4;margin-top:32px;">
            If neither button works, reply to this email and we'll help you reschedule.
          </p>
        </div>
        """
        await email_service.send_email(
            to_email=customer_email,
            subject=f"{shop_name}: Please confirm your appointment",
            html_content=html,
            tenant_id=appointment.get("tenant_id"),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Appointment notification email failed: {exc}")


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

    # Send appointment email with Confirm/Reject quick actions to the customer
    if doc.get("customer_id") and doc.get("send_reminder", True):
        tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0}) or {}
        await _send_customer_appointment_email(doc, tenant)

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


class ConfirmRequest(BaseModel):
    scheduled_start: Optional[str] = None  # admin can override the proposed time
    scheduled_end: Optional[str] = None
    employee_id: Optional[str] = None
    notes: Optional[str] = None


@router.put("/{appointment_id}/confirm", response_model=AppointmentResponse)
async def confirm_appointment(
    appointment_id: str,
    payload: ConfirmRequest = ConfirmRequest(),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Admin confirms a customer-requested appointment.
    Flips status from 'requested' (or any state) to 'confirmed'.
    Admin can override proposed time and assign an employee."""
    doc = await db.appointments.find_one(
        {"id": appointment_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Appointment not found")

    updates: dict = {
        "status": "confirmed",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if payload.scheduled_start:
        updates["scheduled_start"] = payload.scheduled_start
        updates["scheduled_at"] = payload.scheduled_start
        updates["scheduled_date"] = payload.scheduled_start[:10]
    if payload.scheduled_end:
        updates["scheduled_end"] = payload.scheduled_end
    if payload.notes:
        updates["notes"] = payload.notes
    if payload.employee_id:
        emp = await db.employees.find_one(
            {"id": payload.employee_id, "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1},
        )
        updates["employee_id"] = payload.employee_id
        updates["employee_name"] = (emp or {}).get("name")

    await db.appointments.update_one({"id": appointment_id}, {"$set": updates})
    doc.update(updates)
    return _doc_to_response(doc)


class RejectRequest(BaseModel):
    reason: Optional[str] = None


@router.put("/{appointment_id}/reject", response_model=AppointmentResponse)
async def reject_appointment(
    appointment_id: str,
    payload: RejectRequest = RejectRequest(),
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Admin rejects a customer-requested appointment. Sets status='cancelled'
    and stores the reason in notes."""
    doc = await db.appointments.find_one(
        {"id": appointment_id, "tenant_id": current_user.tenant_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Appointment not found")

    updates: dict = {
        "status": "cancelled",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if payload.reason:
        prev_notes = doc.get("notes") or ""
        updates["notes"] = (prev_notes + f"\nRejected: {payload.reason}").strip()
    await db.appointments.update_one({"id": appointment_id}, {"$set": updates})
    doc.update(updates)
    return _doc_to_response(doc)


# ───────────────────────────────────────────────────────────────────────────
# Public (customer-facing) Confirm / Reject quick-action endpoints
# ───────────────────────────────────────────────────────────────────────────


@public_router.get("/{token}/confirm", response_class=HTMLResponse)
async def public_confirm_appointment(token: str):
    """Tokenized customer confirmation endpoint — no auth required.

    Linked from the appointment notification email's "Confirm Appointment"
    button. Marks the appointment as `confirmed` and returns a friendly
    standalone HTML page. Idempotent — duplicate clicks return success.
    """
    decoded = _decode_action_token(token)
    if not decoded or decoded["action"] != "confirm":
        return HTMLResponse(
            _result_html(
                "Link expired",
                "This confirmation link is no longer valid. Please reply to the appointment email to confirm directly.",
                success=False,
            ),
            status_code=400,
        )

    appointment_id = decoded["appointment_id"]
    appt = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appt:
        return HTMLResponse(
            _result_html(
                "Appointment not found",
                "We couldn't find this appointment. It may have been removed.",
                success=False,
            ),
            status_code=404,
        )

    # Already confirmed → idempotent success page (no duplicate update)
    if appt.get("status") == "confirmed":
        return HTMLResponse(_result_html(
            "Already confirmed",
            "Thanks — we already have your confirmation on file. See you soon!",
            success=True,
        ))

    # If previously rejected/cancelled, still allow re-confirmation (customer
    # changed their mind). Append an audit note.
    now = datetime.now(timezone.utc).isoformat()
    prev_status = appt.get("status") or "scheduled"
    updates = {
        "status": "confirmed",
        "confirmation_status": "confirmed_by_customer",
        "confirmed_at": now,
        "updated_at": now,
    }
    if prev_status in {"cancelled", "rejected"}:
        prev_notes = appt.get("notes") or ""
        updates["notes"] = (prev_notes + f"\n[Customer re-confirmed via email on {now}]").strip()
    await db.appointments.update_one({"id": appointment_id}, {"$set": updates})

    return HTMLResponse(_result_html(
        "Appointment confirmed",
        f"Thanks! Your appointment is confirmed for <strong>{appt.get('scheduled_start') or 'the scheduled time'}</strong>. "
        f"We'll see you then.",
        success=True,
    ))


class _RejectReasonForm(BaseModel):
    reason: Optional[str] = None


@public_router.get("/{token}/reject", response_class=HTMLResponse)
async def public_reject_appointment(token: str, reason: Optional[str] = Query(None)):
    """Tokenized customer reject / request-change endpoint — no auth required.

    Marks the appointment as `needs_reschedule` (preferred) and optionally
    appends a customer-supplied reason. Returns a friendly standalone HTML
    page that lets the customer add a short message and resubmit.
    Idempotent — duplicate clicks return the same friendly page.
    """
    decoded = _decode_action_token(token)
    if not decoded or decoded["action"] != "reject":
        return HTMLResponse(
            _result_html(
                "Link expired",
                "This link is no longer valid. Please reply to the appointment email and we'll help reschedule.",
                success=False,
            ),
            status_code=400,
        )

    appointment_id = decoded["appointment_id"]
    appt = await db.appointments.find_one({"id": appointment_id}, {"_id": 0})
    if not appt:
        return HTMLResponse(
            _result_html(
                "Appointment not found",
                "We couldn't find this appointment. It may have been removed.",
                success=False,
            ),
            status_code=404,
        )

    now = datetime.now(timezone.utc).isoformat()
    # If a reason was supplied (e.g. via the reason form on the reject page),
    # record it and mark as needs_reschedule. Otherwise show the reason form.
    if reason:
        prev_notes = appt.get("notes") or ""
        updates = {
            "status": "needs_reschedule",
            "confirmation_status": "rejected_by_customer",
            "rejected_at": now,
            "notes": (prev_notes + f"\n[Customer requested change on {now}]: {reason}").strip(),
            "updated_at": now,
        }
        await db.appointments.update_one({"id": appointment_id}, {"$set": updates})
        return HTMLResponse(_result_html(
            "Thanks — we got your message",
            "We've let the shop know you need a different time. They'll reach out shortly with new options.",
            success=True,
        ))

    # Already rejected — idempotent
    if appt.get("status") in {"needs_reschedule", "rejected", "cancelled"}:
        return HTMLResponse(_result_html(
            "Already received",
            "Thanks — we already received your request to reschedule. The shop will be in touch.",
            success=True,
        ))

    # Mark needs_reschedule immediately, then show form to optionally add a reason.
    await db.appointments.update_one(
        {"id": appointment_id},
        {"$set": {
            "status": "needs_reschedule",
            "confirmation_status": "rejected_by_customer",
            "rejected_at": now,
            "updated_at": now,
        }},
    )

    # Friendly page with optional reason form — submit reposts to this same URL
    # with ?reason=...
    form_html = f"""<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Request a change</title>
<style>
 body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;background:#F8FAFC;color:#0F172A;margin:0;padding:24px;}}
 .card{{max-width:520px;margin:48px auto;background:#fff;border-radius:12px;box-shadow:0 8px 32px rgba(15,23,42,0.08);padding:28px;}}
 h1{{font-size:20px;margin:0 0 12px;color:#0F172A;}}
 p{{color:#475569;line-height:1.55;}}
 textarea{{width:100%;min-height:96px;padding:10px;border:1px solid #CBD5E1;border-radius:8px;font:inherit;box-sizing:border-box;}}
 button{{background:#0EA5E9;color:#fff;border:0;padding:11px 20px;border-radius:8px;font-weight:600;cursor:pointer;}}
</style></head><body>
<div class="card">
  <h1>Request a different time</h1>
  <p>Thanks for letting us know. Add a quick note (optional) and we'll reach out with new options.</p>
  <form method="get" action="/api/public-appointments/{token}/reject">
    <textarea name="reason" placeholder="Optional: what time works better for you?"></textarea>
    <div style="margin-top:12px;text-align:right;">
      <button type="submit">Send message</button>
    </div>
  </form>
  <p style="color:#94A3B8;font-size:12px;margin-top:24px;">
    Your appointment has already been marked as needing a new time. Adding a note just helps us pick the right slot.
  </p>
</div></body></html>"""
    return HTMLResponse(form_html)
