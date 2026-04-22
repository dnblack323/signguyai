"""
Employee Portal Routes

This module contains routes for the employee-facing portal:
- Employee authentication (login with email/PIN)
- Employee dashboard
- Time clock operations
- View pay/earnings
- View assigned tasks
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import jwt
import uuid
import os

from server import db, SECRET_KEY, ALGORITHM, pwd_context
from services.timeclock_service import backfill_timeclock_shifts, get_timeclock_shifts, get_timeclock_status as get_shared_timeclock_status, record_timeclock_action


router = APIRouter(prefix="/employee-portal", tags=["Employee Portal"])


# ============== MODELS ==============

class EmployeeLogin(BaseModel):
    email: str
    pin: str  # 4-6 digit PIN for quick login


class EmployeeLoginResponse(BaseModel):
    access_token: str
    employee_id: str
    employee_name: str
    tenant_id: str


class EmployeeProfile(BaseModel):
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    role: str
    hourly_rate: float
    tenant_id: str
    profile_image: Optional[str] = None


class TimeClockStatus(BaseModel):
    is_clocked_in: bool
    current_status: Optional[str]  # working, on_break
    clocked_in_at: Optional[str]
    total_hours_today: float
    break_time_today: float


class PaySummary(BaseModel):
    current_period_earnings: float
    current_period_hours: float
    ytd_earnings: float
    ytd_hours: float
    last_payment_date: Optional[str]
    last_payment_amount: Optional[float]
    balance_owed: float


class EmployeeTask(BaseModel):
    id: str
    title: str
    description: Optional[str]
    job_id: Optional[str]
    job_name: Optional[str]
    due_date: Optional[str]
    is_complete: bool
    created_at: str


class AssignedJobSummary(BaseModel):
    id: str
    job_number: str
    job_name: str
    customer_name: str
    job_type: str
    current_production_stage: Optional[str] = None
    priority: str = "normal"
    due_date: Optional[str] = None


class EmployeeWorkSummary(BaseModel):
    today_hours_worked: float
    week_hours_worked: float
    completed_stages_today: int
    assigned_jobs_count: int


class StageActionRequest(BaseModel):
    action: str  # start, pause, complete


class TimeLogEntry(BaseModel):
    id: str
    action: str
    timestamp: str


DEFAULT_PORTAL_SETTINGS = {
    "can_view_tasks": True,
    "can_view_schedule": True,
    "can_view_pay_stubs": True,
    "can_view_time_clock": True,
    "can_edit_profile": True,
    "can_see_job_details": False,
    "can_see_customer_info": False,
    "can_see_pricing": False,
}


# ============== HELPER FUNCTIONS ==============

def create_employee_token(employee_id: str, tenant_id: str) -> str:
    """Create JWT token for employee portal"""
    expire = datetime.now(timezone.utc) + timedelta(hours=12)
    to_encode = {
        "sub": employee_id,
        "tenant_id": tenant_id,
        "type": "employee",
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_employee(token: str) -> dict:
    """Decode and validate employee JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "employee":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        employee_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        
        if not employee_id or not tenant_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        employee = await db.employees.find_one({"id": employee_id}, {"_id": 0})
        if not employee:
            raise HTTPException(status_code=401, detail="Employee not found")
        
        if not employee.get("is_active", True):
            raise HTTPException(status_code=403, detail="Employee account is inactive")
        
        return employee
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def extract_token(authorization: str) -> str:
    """Extract token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    return authorization.replace("Bearer ", "")


async def get_assigned_job_ids(employee: dict) -> List[str]:
    tenant_id = employee.get("tenant_id")
    employee_id = employee.get("id")
    jobs = await db.jobs.find(
        {"tenant_id": tenant_id, "assigned_employees": employee_id},
        {"_id": 0, "id": 1}
    ).to_list(500)
    job_ids = {job["id"] for job in jobs}

    timeline_jobs = await db.production_timelines.find(
        {"tenant_id": tenant_id, "stages.assigned_user_id": employee_id},
        {"_id": 0, "job_id": 1}
    ).to_list(500)
    for timeline in timeline_jobs:
        if timeline.get("job_id"):
            job_ids.add(timeline["job_id"])
    return list(job_ids)


async def get_employee_portal_settings(tenant_id: str) -> dict:
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "employee_portal_settings": 1})
    return {**DEFAULT_PORTAL_SETTINGS, **((tenant or {}).get("employee_portal_settings") or {})}


async def require_portal_setting(tenant_id: str, setting_key: str):
    settings = await get_employee_portal_settings(tenant_id)
    if not settings.get(setting_key, False):
        raise HTTPException(status_code=403, detail="This section is disabled by your admin")
    return settings


# ============== AUTH ROUTES ==============

@router.post("/auth/login", response_model=EmployeeLoginResponse)
async def employee_login(data: EmployeeLogin):
    """Employee login with email and PIN"""
    # Find employee by email
    employee = await db.employees.find_one(
        {"email": data.email.lower()},
        {"_id": 0}
    )
    
    if not employee:
        raise HTTPException(status_code=401, detail="Invalid email or PIN")
    
    if not employee.get("is_active", True):
        raise HTTPException(status_code=403, detail="Employee account is inactive")
    
    # Verify PIN
    stored_pin = employee.get("pin")
    if not stored_pin:
        # If no PIN set, check if PIN matches last 4 digits of phone or default
        if data.pin != "1234" and data.pin != employee.get("phone", "")[-4:]:
            raise HTTPException(status_code=401, detail="Invalid email or PIN")
    elif stored_pin != data.pin:
        raise HTTPException(status_code=401, detail="Invalid email or PIN")
    
    # Get tenant_id from employee record or find from shop
    tenant_id = employee.get("tenant_id")
    if not tenant_id:
        # Try to find tenant - this shouldn't happen normally
        raise HTTPException(status_code=500, detail="Employee not associated with a shop")
    
    # Create token
    token = create_employee_token(employee["id"], tenant_id)
    
    return EmployeeLoginResponse(
        access_token=token,
        employee_id=employee["id"],
        employee_name=employee["name"],
        tenant_id=tenant_id
    )


@router.post("/auth/set-pin")
async def set_employee_pin(
    new_pin: str,
    authorization: str = Header(default="")
):
    """Set or update employee PIN"""
    # This would need proper auth in production
    # For now, simplified implementation
    return {"message": "PIN updated successfully"}


# ============== PROFILE ROUTES ==============

@router.get("/profile", response_model=EmployeeProfile)
async def get_employee_profile(authorization: str = Header(default="")):
    """Get current employee's profile"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    
    return EmployeeProfile(
        id=employee["id"],
        name=employee["name"],
        email=employee.get("email"),
        phone=employee.get("phone"),
        role=employee.get("role", "staff"),
        hourly_rate=employee.get("hourly_rate", 0),
        tenant_id=employee.get("tenant_id", ""),
        profile_image=employee.get("profile_image")
    )


@router.get("/config")
async def get_employee_portal_config(authorization: str = Header(default="")):
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    settings = await get_employee_portal_settings(employee["tenant_id"])
    return settings


class ProfileImageUpdate(BaseModel):
    profile_image: str  # Base64 encoded image or URL


@router.put("/profile/image")
async def update_profile_image(
    data: ProfileImageUpdate,
    authorization: str = Header(default="")
):
    """Update employee's profile image"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_edit_profile")
    
    # Update the employee's profile image
    await db.employees.update_one(
        {"id": employee["id"]},
        {"$set": {"profile_image": data.profile_image}}
    )
    
    return {"message": "Profile image updated successfully", "profile_image": data.profile_image}


# ============== TIME CLOCK ROUTES ==============

@router.get("/time-clock/status", response_model=TimeClockStatus)
async def get_time_clock_status(authorization: str = Header(default="")):
    """Get current time clock status for employee"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_view_time_clock")
    
    today = datetime.now(timezone.utc).date().isoformat()
    status = await get_shared_timeclock_status(db, employee["tenant_id"], employee["id"])
    await backfill_timeclock_shifts(db, employee["tenant_id"], employee["id"], today, today)
    shifts = await get_timeclock_shifts(db, employee["tenant_id"], employee_id=employee["id"], start_date=today, end_date=today)
    total_hours = round(sum(shift.get("net_hours", 0) for shift in shifts), 2)
    break_hours = round(sum((shift.get("break_minutes", 0) or 0) / 60 for shift in shifts), 2)
    
    return TimeClockStatus(
        is_clocked_in=status.get("status") in {"working", "on_break"},
        current_status=status.get("status") if status.get("status") != "not_started" else None,
        # Canonical clock-in time (not updated_at — see timeclock_service fix).
        clocked_in_at=status.get("clocked_in_at") or status.get("last_timestamp"),
        total_hours_today=total_hours,
        break_time_today=break_hours,
    )


class TimeClockPunchRequest(BaseModel):
    """Body for POST /time-clock/punch — replaces the query-string action."""
    action: str = Field(pattern="^(start_work|break_start|break_end|end_work)$")


@router.post("/time-clock/punch")
async def punch_time_clock(
    data: TimeClockPunchRequest,
    authorization: str = Header(default=""),
):
    """Punch time clock (start_work, break_start, break_end, end_work)."""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_view_time_clock")

    try:
        log = await record_timeclock_action(db, employee["tenant_id"], employee["id"], data.action)
        return {"message": f"Successfully recorded: {data.action.replace('_', ' ')}", "log": log}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/time-clock/history", response_model=List[TimeLogEntry])
async def get_time_clock_history(
    days: int = 7,
    authorization: str = Header(default="")
):
    """Get time clock history for the past N days"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_view_time_clock")
    
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    logs = await db.timelogs.find({
        "employee_id": employee["id"],
        "timestamp": {"$gte": start_date}
    }, {"_id": 0}).sort("timestamp", -1).to_list(500)
    
    return [TimeLogEntry(**log) for log in logs]


# ============== PAY ROUTES ==============

@router.get("/pay/summary", response_model=PaySummary)
async def get_pay_summary(authorization: str = Header(default="")):
    """Get employee pay summary"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_view_pay_stubs")
    
    hourly_rate = employee.get("hourly_rate", 0)
    today = datetime.now(timezone.utc)
    current_period_start = (today - timedelta(days=today.weekday())).date().isoformat()
    current_period_end = today.date().isoformat()
    year_start = datetime(today.year, 1, 1, tzinfo=timezone.utc).date().isoformat()

    await backfill_timeclock_shifts(db, employee["tenant_id"], employee["id"], year_start, current_period_end)
    current_shifts = await get_timeclock_shifts(db, employee["tenant_id"], employee_id=employee["id"], start_date=current_period_start, end_date=current_period_end)
    ytd_shifts = await get_timeclock_shifts(db, employee["tenant_id"], employee_id=employee["id"], start_date=year_start, end_date=current_period_end)

    current_manual = await db.payroll_hours.find({"employee_id": employee["id"], "tenant_id": employee["tenant_id"], "date": {"$gte": current_period_start, "$lte": current_period_end}}, {"_id": 0}).to_list(1000)
    ytd_manual = await db.payroll_hours.find({"employee_id": employee["id"], "tenant_id": employee["tenant_id"], "date": {"$gte": year_start, "$lte": current_period_end}}, {"_id": 0}).to_list(5000)
    current_job_entries = await db.job_time_entries.find({"employee_id": employee["id"], "tenant_id": employee["tenant_id"], "start_time": {"$gte": f"{current_period_start}T00:00:00", "$lte": f"{current_period_end}T23:59:59"}}, {"_id": 0}).to_list(1000)
    ytd_job_entries = await db.job_time_entries.find({"employee_id": employee["id"], "tenant_id": employee["tenant_id"], "start_time": {"$gte": f"{year_start}T00:00:00", "$lte": f"{current_period_end}T23:59:59"}}, {"_id": 0}).to_list(5000)

    current_period_hours = round(sum(shift.get("net_hours", 0) for shift in current_shifts) + sum(entry.get("hours", 0) for entry in current_manual) + sum((entry.get("duration_minutes", 0) / 60) for entry in current_job_entries), 2)
    ytd_hours = round(sum(shift.get("net_hours", 0) for shift in ytd_shifts) + sum(entry.get("hours", 0) for entry in ytd_manual) + sum((entry.get("duration_minutes", 0) / 60) for entry in ytd_job_entries), 2)

    current_period_earnings = current_period_hours * hourly_rate
    ytd_earnings = ytd_hours * hourly_rate

    last_payment = await db.payroll_transactions.find_one(
        {"employee_id": employee["id"], "type": "payment"},
        {"_id": 0},
        sort=[("date", -1)]
    )
    transactions = await db.payroll_transactions.find({"employee_id": employee["id"]}, {"_id": 0}).to_list(5000)
    total_advances = sum(item.get("amount", 0) for item in transactions if item.get("type") == "advance")
    total_payments = sum(item.get("amount", 0) for item in transactions if item.get("type") == "payment")
    balance_owed = ytd_earnings - total_advances - total_payments
    
    return PaySummary(
        current_period_earnings=round(current_period_earnings, 2),
        current_period_hours=round(current_period_hours, 2),
        ytd_earnings=round(ytd_earnings, 2),
        ytd_hours=round(ytd_hours, 2),
        last_payment_date=last_payment.get("date") if last_payment else None,
        last_payment_amount=last_payment.get("amount") if last_payment else None,
        balance_owed=round(max(0, balance_owed), 2)
    )


# ============== TASKS ROUTES ==============

@router.get("/tasks", response_model=List[EmployeeTask])
async def get_employee_tasks(
    include_completed: bool = False,
    authorization: str = Header(default="")
):
    """Get tasks assigned to employee"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_view_tasks")
    
    query = {"assigned_to": employee["id"]}
    if not include_completed:
        query["is_complete"] = False
    
    tasks = await db.tasks.find(query, {"_id": 0}).sort("due_date", 1).to_list(100)
    
    result = []
    for task in tasks:
        job_name = None
        if task.get("job_id"):
            job = await db.jobs.find_one({"id": task["job_id"]}, {"_id": 0, "name": 1})
            job_name = job.get("name") if job else None
        
        result.append(EmployeeTask(
            id=task.get("id", ""),
            title=task.get("title", ""),
            description=task.get("description"),
            job_id=task.get("job_id"),
            job_name=job_name,
            due_date=task.get("due_date"),
            is_complete=task.get("is_complete", False),
            created_at=task.get("created_at", "")
        ))
    
    return result


@router.get("/jobs", response_model=List[AssignedJobSummary])
async def get_assigned_jobs(authorization: str = Header(default="")):
    """Get jobs assigned to the current employee."""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    settings = await get_employee_portal_settings(employee["tenant_id"])
    if not settings.get("can_view_tasks", True) and not settings.get("can_see_job_details", False):
        raise HTTPException(status_code=403, detail="Assigned jobs are hidden by your admin")
    job_ids = await get_assigned_job_ids(employee)

    jobs = await db.jobs.find(
        {"tenant_id": employee["tenant_id"], "id": {"$in": job_ids}},
        {"_id": 0}
    ).sort("due_date", 1).to_list(200)

    result = []
    for job in jobs:
        customer = await db.customers.find_one({"id": job.get("customer_id")}, {"_id": 0, "name": 1})
        timelines = await db.production_timelines.find(
            {"job_id": job["id"], "tenant_id": employee["tenant_id"]},
            {"_id": 0, "current_stage_order": 1, "stages": 1}
        ).to_list(20)
        current_stage = None
        if timelines:
            for timeline in timelines:
                match = next((stage for stage in timeline.get("stages", []) if stage.get("stage_order") == timeline.get("current_stage_order")), None)
                if match:
                    current_stage = match.get("stage_name")
                    break

        result.append(AssignedJobSummary(
            id=job["id"],
            job_number=job["id"][:8].upper(),
            job_name=job.get("name", "Untitled Job"),
            customer_name=(customer.get("name", "Unknown") if customer else "Unknown") if settings.get("can_see_customer_info", False) else "Assigned Customer",
            job_type=job.get("status", "job"),
            current_production_stage=current_stage,
            priority="urgent" if job.get("due_date") and job.get("due_date") <= datetime.now(timezone.utc).date().isoformat() else "normal",
            due_date=job.get("due_date"),
        ))
    return result


@router.get("/jobs/{job_id}")
async def get_employee_job_detail(job_id: str, authorization: str = Header(default="")):
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    settings = await require_portal_setting(employee["tenant_id"], "can_see_job_details")
    job_ids = await get_assigned_job_ids(employee)
    if job_id not in job_ids:
        raise HTTPException(status_code=404, detail="Assigned job not found")

    job = await db.jobs.find_one({"id": job_id, "tenant_id": employee["tenant_id"]}, {"_id": 0})
    customer = await db.customers.find_one({"id": job.get("customer_id")}, {"_id": 0, "name": 1}) if job else None
    job_items = await db.job_items.find({"job_id": job_id}, {"_id": 0}).to_list(200)
    timelines = await db.production_timelines.find({"job_id": job_id, "tenant_id": employee["tenant_id"]}, {"_id": 0}).to_list(200)
    return {
        "job": job,
        "customer_name": (customer.get("name", "Unknown") if customer else "Unknown") if settings.get("can_see_customer_info", False) else "Assigned Customer",
        "job_items": job_items,
        "timelines": timelines,
    }


@router.get("/work-summary", response_model=EmployeeWorkSummary)
async def get_employee_work_summary(authorization: str = Header(default="")):
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_view_time_clock")
    job_ids = await get_assigned_job_ids(employee)
    today = datetime.now(timezone.utc).date().isoformat()
    week_start = (datetime.now(timezone.utc) - timedelta(days=datetime.now(timezone.utc).weekday())).date().isoformat()

    status = await get_time_clock_status(authorization)
    today_hours = status.total_hours_today

    await backfill_timeclock_shifts(db, employee["tenant_id"], employee["id"], week_start, today)
    week_shifts = await get_timeclock_shifts(db, employee["tenant_id"], employee_id=employee["id"], start_date=week_start, end_date=today)
    week_hours = sum(shift.get("net_hours", 0) for shift in week_shifts)

    completed_stages_today = await db.production_timelines.count_documents({
        "tenant_id": employee["tenant_id"],
        "stages": {"$elemMatch": {"assigned_user_id": employee["id"], "completed_at": {"$regex": f"^{today}"}}}
    })

    return EmployeeWorkSummary(
        today_hours_worked=round(today_hours, 2),
        week_hours_worked=round(week_hours, 2),
        completed_stages_today=completed_stages_today,
        assigned_jobs_count=len(job_ids),
    )


@router.post("/jobs/{job_id}/timeline/{timeline_id}/stage/{stage_order}")
async def act_on_stage(
    job_id: str,
    timeline_id: str,
    stage_order: int,
    request: StageActionRequest,
    authorization: str = Header(default="")
):
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    await require_portal_setting(employee["tenant_id"], "can_see_job_details")
    job_ids = await get_assigned_job_ids(employee)
    if job_id not in job_ids:
        raise HTTPException(status_code=404, detail="Assigned job not found")

    timeline = await db.production_timelines.find_one(
        {"id": timeline_id, "job_id": job_id, "tenant_id": employee["tenant_id"]},
        {"_id": 0}
    )
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")

    stages = timeline.get("stages", [])
    now = datetime.now(timezone.utc).isoformat()
    action = request.action
    if action not in ["start", "pause", "complete"]:
        raise HTTPException(status_code=400, detail="Invalid stage action")

    for stage in stages:
        if stage.get("stage_order") == stage_order:
            stage["assigned_user_id"] = employee["id"]
            stage["assigned_user_name"] = employee.get("name")
            if action == "start":
                stage["status"] = "in_progress"
                stage["started_at"] = stage.get("started_at") or now
            elif action == "pause":
                stage["status"] = "paused"
            elif action == "complete":
                stage["status"] = "completed"
                stage["started_at"] = stage.get("started_at") or now
                stage["completed_at"] = now
                start = datetime.fromisoformat(stage["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(now.replace("Z", "+00:00"))
                stage["duration_minutes"] = int((end - start).total_seconds() / 60)
                if timeline.get("current_stage_order") == stage_order:
                    timeline["current_stage_order"] = stage_order + 1
            break

    if all(stage.get("status") == "completed" for stage in stages):
        timeline["completed_at"] = now

    await db.production_timelines.update_one(
        {"id": timeline_id},
        {"$set": {"stages": stages, "current_stage_order": timeline.get("current_stage_order", stage_order), "updated_at": now, "completed_at": timeline.get("completed_at")}}
    )

    action_messages = {"start": "started", "pause": "paused", "complete": "completed"}
    return {"message": f"Stage {action_messages.get(action, action + 'ed')}", "timeline_id": timeline_id, "stage_order": stage_order}


@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str, authorization: str = Header(default="")):
    """Mark a task as complete"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    
    result = await db.tasks.update_one(
        {"id": task_id, "assigned_to": employee["id"]},
        {"$set": {"is_complete": True, "completed_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found or not assigned to you")
    
    return {"message": "Task marked as complete"}
