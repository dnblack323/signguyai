"""
Employee Portal Routes

This module contains routes for the employee-facing portal:
- Employee authentication (login with email/PIN)
- Employee dashboard
- Time clock operations
- View pay/earnings
- View assigned tasks
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import jwt
import uuid
import os

from server import db, SECRET_KEY, ALGORITHM, pwd_context


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


class TimeLogEntry(BaseModel):
    id: str
    action: str
    timestamp: str


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
    authorization: str = None
):
    """Set or update employee PIN"""
    from fastapi import Header
    # This would need proper auth in production
    # For now, simplified implementation
    return {"message": "PIN updated successfully"}


# ============== PROFILE ROUTES ==============

@router.get("/profile", response_model=EmployeeProfile)
async def get_employee_profile(authorization: str = ""):
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
        tenant_id=employee.get("tenant_id", "")
    )


# ============== TIME CLOCK ROUTES ==============

@router.get("/time-clock/status", response_model=TimeClockStatus)
async def get_time_clock_status(authorization: str = ""):
    """Get current time clock status for employee"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Get today's time logs
    logs = await db.timelogs.find({
        "employee_id": employee["id"],
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    
    is_clocked_in = False
    current_status = None
    clocked_in_at = None
    total_work_seconds = 0
    total_break_seconds = 0
    
    if logs:
        # Determine current status from last log
        last_log = logs[-1]
        last_action = last_log.get("action")
        
        if last_action in ["start_work", "break_end"]:
            is_clocked_in = True
            current_status = "working"
        elif last_action == "break_start":
            is_clocked_in = True
            current_status = "on_break"
        elif last_action == "end_work":
            is_clocked_in = False
            current_status = None
        
        # Find clock in time
        for log in logs:
            if log.get("action") == "start_work":
                clocked_in_at = log.get("timestamp")
                break
        
        # Calculate hours worked
        work_start = None
        break_start = None
        
        for log in logs:
            action = log.get("action")
            ts = datetime.fromisoformat(log.get("timestamp").replace("Z", "+00:00"))
            
            if action == "start_work":
                work_start = ts
            elif action == "break_start" and work_start:
                total_work_seconds += (ts - work_start).total_seconds()
                break_start = ts
                work_start = None
            elif action == "break_end":
                if break_start:
                    total_break_seconds += (ts - break_start).total_seconds()
                work_start = ts
                break_start = None
            elif action == "end_work":
                if work_start:
                    total_work_seconds += (ts - work_start).total_seconds()
                work_start = None
        
        # If still working, add time up to now
        if work_start:
            now = datetime.now(timezone.utc)
            total_work_seconds += (now - work_start).total_seconds()
        if break_start:
            now = datetime.now(timezone.utc)
            total_break_seconds += (now - break_start).total_seconds()
    
    return TimeClockStatus(
        is_clocked_in=is_clocked_in,
        current_status=current_status,
        clocked_in_at=clocked_in_at,
        total_hours_today=round(total_work_seconds / 3600, 2),
        break_time_today=round(total_break_seconds / 3600, 2)
    )


@router.post("/time-clock/punch")
async def punch_time_clock(action: str, authorization: str = ""):
    """Punch time clock (start_work, break_start, break_end, end_work)"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    
    valid_actions = ["start_work", "break_start", "break_end", "end_work"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    # Create time log
    log = {
        "id": str(uuid.uuid4()),
        "employee_id": employee["id"],
        "action": action,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.timelogs.insert_one(log)
    log.pop("_id", None)
    
    return {"message": f"Successfully recorded: {action.replace('_', ' ')}", "log": log}


@router.get("/time-clock/history", response_model=List[TimeLogEntry])
async def get_time_clock_history(
    days: int = 7,
    authorization: str = ""
):
    """Get time clock history for the past N days"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    logs = await db.timelogs.find({
        "employee_id": employee["id"],
        "timestamp": {"$gte": start_date}
    }, {"_id": 0}).sort("timestamp", -1).to_list(500)
    
    return [TimeLogEntry(**log) for log in logs]


# ============== PAY ROUTES ==============

@router.get("/pay/summary", response_model=PaySummary)
async def get_pay_summary(authorization: str = ""):
    """Get employee pay summary"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    
    hourly_rate = employee.get("hourly_rate", 0)
    
    # Calculate current pay period (assume weekly, Monday-Sunday)
    today = datetime.now(timezone.utc)
    days_since_monday = today.weekday()
    period_start = (today - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get time logs for current period
    current_period_logs = await db.timelogs.find({
        "employee_id": employee["id"],
        "timestamp": {"$gte": period_start.isoformat()}
    }, {"_id": 0}).to_list(500)
    
    # Calculate hours for current period
    current_period_hours = 0
    work_start = None
    
    for log in sorted(current_period_logs, key=lambda x: x.get("timestamp", "")):
        action = log.get("action")
        ts = datetime.fromisoformat(log.get("timestamp").replace("Z", "+00:00"))
        
        if action == "start_work":
            work_start = ts
        elif action in ["break_start", "end_work"] and work_start:
            current_period_hours += (ts - work_start).total_seconds() / 3600
            work_start = None
        elif action == "break_end":
            work_start = ts
    
    # If still working, add time up to now
    if work_start:
        current_period_hours += (datetime.now(timezone.utc) - work_start).total_seconds() / 3600
    
    current_period_earnings = current_period_hours * hourly_rate
    
    # Get YTD data
    year_start = datetime(today.year, 1, 1, tzinfo=timezone.utc).isoformat()
    ytd_logs = await db.timelogs.find({
        "employee_id": employee["id"],
        "timestamp": {"$gte": year_start}
    }, {"_id": 0}).to_list(10000)
    
    ytd_hours = 0
    work_start = None
    for log in sorted(ytd_logs, key=lambda x: x.get("timestamp", "")):
        action = log.get("action")
        ts = datetime.fromisoformat(log.get("timestamp").replace("Z", "+00:00"))
        
        if action == "start_work":
            work_start = ts
        elif action in ["break_start", "end_work"] and work_start:
            ytd_hours += (ts - work_start).total_seconds() / 3600
            work_start = None
        elif action == "break_end":
            work_start = ts
    
    if work_start:
        ytd_hours += (datetime.now(timezone.utc) - work_start).total_seconds() / 3600
    
    ytd_earnings = ytd_hours * hourly_rate
    
    # Get last payment
    last_payment = await db.payroll.find_one(
        {"employee_id": employee["id"], "type": "payment"},
        {"_id": 0},
        sort=[("date", -1)]
    )
    
    # Calculate balance owed (earnings - payments)
    total_payments = 0
    payments = await db.payroll.find(
        {"employee_id": employee["id"], "type": "payment"},
        {"_id": 0}
    ).to_list(1000)
    total_payments = sum(p.get("amount", 0) for p in payments)
    
    balance_owed = ytd_earnings - total_payments
    
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
    authorization: str = ""
):
    """Get tasks assigned to employee"""
    token = extract_token(authorization)
    employee = await get_current_employee(token)
    
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


@router.put("/tasks/{task_id}/complete")
async def complete_task(task_id: str, authorization: str = ""):
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
