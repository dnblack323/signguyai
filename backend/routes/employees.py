"""
Employee, Time Clock, and Payroll Routes

This module contains all routes related to:
- Employee CRUD operations
- Time clock (punch in/out, breaks)
- Payroll transactions and balance tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import uuid

# Import from server module
from server import db, logger, get_current_active_user

from models import UserInDB, PayrollTransactionType


# ============== LOCAL MODELS (to be moved to models/employees.py) ==============

class EmployeeBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    hourly_rate: float = 0
    role: str = "staff"
    is_active: bool = True
    tenant_id: Optional[str] = None
    pin: Optional[str] = None  # 4-6 digit PIN for employee portal login
    profile_image: Optional[str] = None  # URL to profile image

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    hourly_rate: Optional[float] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    pin: Optional[str] = None
    profile_image: Optional[str] = None

class Employee(EmployeeBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TimeLogCreate(BaseModel):
    employee_id: str
    action: str  # start_work, break_start, break_end, end_work

class TimeLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    action: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PayrollTransactionCreate(BaseModel):
    employee_id: str
    type: PayrollTransactionType
    amount: float
    description: Optional[str] = None
    date: Optional[str] = None

class PayrollTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    type: PayrollTransactionType
    amount: float
    description: Optional[str] = None
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PayrollBalance(BaseModel):
    employee_id: str
    employee_name: str
    total_earnings: float
    total_advances: float
    total_payments: float
    balance: float

class ManualHoursCreate(BaseModel):
    employee_id: str
    date: str  # YYYY-MM-DD
    hours: float
    description: Optional[str] = None
    job_id: Optional[str] = None
    task_type: str = "general"  # general, design, production, installation, admin

class ManualHoursUpdate(BaseModel):
    hours: Optional[float] = None
    description: Optional[str] = None
    task_type: Optional[str] = None
    date: Optional[str] = None

class ManualHoursEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    tenant_id: str
    date: str
    hours: float
    description: Optional[str] = None
    job_id: Optional[str] = None
    job_name: Optional[str] = None
    task_type: str = "general"
    hourly_rate: float = 0
    gross_pay: float = 0
    is_manual: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============== ROUTERS ==============

employees_router = APIRouter(prefix="/employees", tags=["Employees"])
timeclock_router = APIRouter(prefix="/timeclock", tags=["Time Clock"])
payroll_router = APIRouter(prefix="/payroll", tags=["Payroll"])


# ============== EMPLOYEE ROUTES ==============

@employees_router.post("", response_model=Employee)
async def create_employee(
    input: EmployeeCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new employee"""
    # Set tenant_id from current user
    employee_data = input.model_dump()
    employee_data["tenant_id"] = current_user.tenant_id
    
    # Set default PIN if not provided (last 4 of phone or 1234)
    if not employee_data.get("pin"):
        if employee_data.get("phone") and len(employee_data["phone"]) >= 4:
            employee_data["pin"] = employee_data["phone"][-4:]
        else:
            employee_data["pin"] = "1234"
    
    employee = Employee(**employee_data)
    doc = employee.model_dump()
    await db.employees.insert_one(doc)
    return employee


@employees_router.get("", response_model=List[Employee])
async def get_employees(
    is_active: Optional[bool] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all employees for current tenant"""
    query = {"tenant_id": current_user.tenant_id}
    if is_active is not None:
        query["is_active"] = is_active
    employees = await db.employees.find(query, {"_id": 0}).to_list(1000)
    return employees


@employees_router.get("/{employee_id}", response_model=Employee)
async def get_employee(
    employee_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific employee (must belong to current tenant)"""
    employee = await db.employees.find_one({
        "id": employee_id,
        "tenant_id": current_user.tenant_id
    }, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@employees_router.put("/{employee_id}", response_model=Employee)
async def update_employee(
    employee_id: str, 
    input: EmployeeUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update an employee (must belong to current tenant)"""
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    result = await db.employees.update_one({
        "id": employee_id,
        "tenant_id": current_user.tenant_id
    }, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee = await db.employees.find_one(
        {"id": employee_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    return employee


# ============== TIME CLOCK ROUTES ==============

@timeclock_router.post("", response_model=TimeLog)
async def clock_action(input: TimeLogCreate):
    """Record a time clock action (start_work, break_start, break_end, end_work)"""
    valid_actions = ["start_work", "break_start", "break_end", "end_work"]
    if input.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
    
    # Get today's logs for this employee
    today = datetime.now(timezone.utc).date().isoformat()
    today_logs = await db.timelogs.find({
        "employee_id": input.employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    
    # Validate sequence
    last_action = today_logs[-1]["action"] if today_logs else None
    
    valid_sequences = {
        None: ["start_work"],
        "start_work": ["break_start", "end_work"],
        "break_start": ["break_end"],
        "break_end": ["break_start", "end_work"],
        "end_work": ["start_work"]
    }
    
    if input.action not in valid_sequences.get(last_action, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid sequence. After '{last_action}', valid actions are: {valid_sequences.get(last_action, [])}"
        )
    
    time_log = TimeLog(
        employee_id=input.employee_id,
        action=input.action,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    doc = time_log.model_dump()
    await db.timelogs.insert_one(doc)
    return time_log


@timeclock_router.get("/{employee_id}/today")
async def get_today_logs(employee_id: str):
    """Get today's time logs for an employee"""
    today = datetime.now(timezone.utc).date().isoformat()
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return logs


@timeclock_router.get("/{employee_id}/summary")
async def get_shift_summary(employee_id: str, date: Optional[str] = None):
    """Get work/break time summary for an employee on a specific date"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()
    
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{date}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    
    work_minutes = 0
    break_minutes = 0
    work_start = None
    break_start = None
    
    for log in logs:
        ts = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
        action = log["action"]
        
        if action == "start_work":
            work_start = ts
        elif action == "break_start" and work_start:
            break_start = ts
        elif action == "break_end" and break_start:
            break_minutes += (ts - break_start).total_seconds() / 60
            break_start = None
        elif action == "end_work" and work_start:
            work_minutes += (ts - work_start).total_seconds() / 60
            work_start = None
    
    return {
        "employee_id": employee_id,
        "date": date,
        "work_minutes": round(work_minutes, 2),
        "break_minutes": round(break_minutes, 2),
        "net_minutes": round(work_minutes - break_minutes, 2),
        "net_hours": round((work_minutes - break_minutes) / 60, 2)
    }


@timeclock_router.get("/{employee_id}/status")
async def get_clock_status(employee_id: str):
    """Get current clock status for an employee"""
    today = datetime.now(timezone.utc).date().isoformat()
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", -1).to_list(1)
    
    if not logs:
        return {"status": "not_started", "last_action": None}
    
    last_log = logs[0]
    status_map = {
        "start_work": "working",
        "break_start": "on_break",
        "break_end": "working",
        "end_work": "finished"
    }
    
    return {
        "status": status_map.get(last_log["action"], "unknown"),
        "last_action": last_log["action"],
        "last_timestamp": last_log["timestamp"]
    }


# ============== PAYROLL ROUTES ==============

@payroll_router.post("/transactions", response_model=PayrollTransaction)
async def create_payroll_transaction(input: PayrollTransactionCreate):
    """Create a payroll transaction (earnings, advance, payment)"""
    # Filter out None values to allow defaults to work
    input_data = {k: v for k, v in input.model_dump().items() if v is not None}
    transaction = PayrollTransaction(**input_data)
    doc = transaction.model_dump()
    await db.payroll_transactions.insert_one(doc)
    return transaction


@payroll_router.get("/transactions", response_model=List[PayrollTransaction])
async def get_payroll_transactions(
    employee_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List payroll transactions with optional filtering (tenant-scoped)"""
    # First get employee IDs for this tenant
    tenant_employees = await db.employees.find(
        {"tenant_id": current_user.tenant_id}, 
        {"id": 1, "_id": 0}
    ).to_list(1000)
    tenant_employee_ids = [e["id"] for e in tenant_employees]
    
    query = {"employee_id": {"$in": tenant_employee_ids}}
    if employee_id:
        if employee_id not in tenant_employee_ids:
            return []
        query["employee_id"] = employee_id
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    transactions = await db.payroll_transactions.find(query, {"_id": 0}).to_list(1000)
    return transactions


@payroll_router.get("/balance/{employee_id}", response_model=PayrollBalance)
async def get_payroll_balance(
    employee_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get payroll balance for an employee (tenant-scoped)"""
    employee = await db.employees.find_one({
        "id": employee_id,
        "tenant_id": current_user.tenant_id
    }, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    transactions = await db.payroll_transactions.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
    
    total_earnings = sum(t["amount"] for t in transactions if t["type"] == "earnings")
    total_advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
    total_payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
    
    # Balance = Earnings - Advances - Payments
    balance = total_earnings - total_advances - total_payments
    
    return PayrollBalance(
        employee_id=employee_id,
        employee_name=employee["name"],
        total_earnings=total_earnings,
        total_advances=total_advances,
        total_payments=total_payments,
        balance=balance
    )


@payroll_router.get("/report")
async def get_payroll_report(
    start_date: str, 
    end_date: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get payroll report for all employees in a date range (tenant-scoped)"""
    employees = await db.employees.find({
        "tenant_id": current_user.tenant_id
    }, {"_id": 0}).to_list(1000)
    report = []
    
    for emp in employees:
        transactions = await db.payroll_transactions.find({
            "employee_id": emp["id"],
            "date": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}).to_list(1000)
        
        earnings = sum(t["amount"] for t in transactions if t["type"] == "earnings")
        advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
        payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
        
        report.append({
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "hourly_rate": emp.get("hourly_rate", 0),
            "earnings": earnings,
            "advances": advances,
            "payments": payments,
            "balance": earnings - advances - payments
        })
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "employees": report,
        "totals": {
            "earnings": sum(r["earnings"] for r in report),
            "advances": sum(r["advances"] for r in report),
            "payments": sum(r["payments"] for r in report),
            "balance": sum(r["balance"] for r in report)
        }
    }


# ============== MANUAL HOURS ROUTES ==============

@payroll_router.post("/hours")
async def add_manual_hours(
    input: ManualHoursCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Add manual hours entry for an employee"""
    employee = await db.employees.find_one({
        "id": input.employee_id,
        "tenant_id": current_user.tenant_id
    }, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    hourly_rate = employee.get("hourly_rate", 0)
    job_name = None
    if input.job_id:
        job = await db.jobs.find_one({"id": input.job_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "name": 1})
        if job:
            job_name = job.get("name")
    
    entry = ManualHoursEntry(
        employee_id=input.employee_id,
        tenant_id=current_user.tenant_id,
        date=input.date,
        hours=input.hours,
        description=input.description,
        job_id=input.job_id,
        job_name=job_name,
        task_type=input.task_type,
        hourly_rate=hourly_rate,
        gross_pay=round(input.hours * hourly_rate, 2)
    )
    doc = entry.model_dump()
    await db.payroll_hours.insert_one(doc)
    doc.pop("_id", None)
    return doc


@payroll_router.put("/hours/{entry_id}")
async def update_manual_hours(
    entry_id: str,
    input: ManualHoursUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a manual hours entry"""
    entry = await db.payroll_hours.find_one({
        "id": entry_id,
        "tenant_id": current_user.tenant_id
    })
    if not entry:
        raise HTTPException(status_code=404, detail="Hours entry not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    # Recalculate gross_pay if hours changed
    if "hours" in update_data:
        hourly_rate = entry.get("hourly_rate", 0)
        update_data["gross_pay"] = round(update_data["hours"] * hourly_rate, 2)
    
    if update_data:
        await db.payroll_hours.update_one({"id": entry_id}, {"$set": update_data})
    
    updated = await db.payroll_hours.find_one({"id": entry_id}, {"_id": 0})
    return updated


@payroll_router.delete("/hours/{entry_id}")
async def delete_manual_hours(
    entry_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a manual hours entry"""
    result = await db.payroll_hours.delete_one({
        "id": entry_id,
        "tenant_id": current_user.tenant_id
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Hours entry not found")
    return {"message": "Hours entry deleted"}


@payroll_router.get("/hours")
async def get_manual_hours(
    employee_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get manual hours entries"""
    query = {"tenant_id": current_user.tenant_id}
    if employee_id:
        query["employee_id"] = employee_id
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    
    entries = await db.payroll_hours.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return entries


# ============== TIMESHEET & PAY PERIOD ROUTES ==============

@payroll_router.get("/timesheet")
async def get_timesheet(
    start_date: str,
    end_date: str,
    employee_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get consolidated timesheet - combines job time entries + manual hours"""
    emp_query = {"tenant_id": current_user.tenant_id}
    if employee_id:
        emp_query["id"] = employee_id
    employees = await db.employees.find(emp_query, {"_id": 0}).to_list(1000)
    
    timesheet = []
    for emp in employees:
        emp_id = emp["id"]
        hourly_rate = emp.get("hourly_rate", 0)
        
        # Get job time entries for this employee in range
        job_entries = await db.job_time_entries.find({
            "employee_id": emp_id,
            "tenant_id": current_user.tenant_id,
            "start_time": {"$gte": f"{start_date}T00:00:00", "$lte": f"{end_date}T23:59:59"}
        }, {"_id": 0}).to_list(1000)
        
        # Get manual hours entries
        manual_entries = await db.payroll_hours.find({
            "employee_id": emp_id,
            "tenant_id": current_user.tenant_id,
            "date": {"$gte": start_date, "$lte": end_date}
        }, {"_id": 0}).to_list(1000)
        
        # Calculate totals from job time entries
        job_hours = 0
        job_pay = 0
        job_details = []
        for je in job_entries:
            minutes = je.get("duration_minutes", 0)
            if minutes:
                hours = minutes / 60
                job_hours += hours
                cost = je.get("labor_cost", 0)
                job_pay += cost
                job_details.append({
                    "id": je.get("id"),
                    "job_id": je.get("job_id"),
                    "job_name": je.get("job_name", ""),
                    "task_type": je.get("task_type", "production"),
                    "date": je.get("start_time", "")[:10],
                    "hours": round(hours, 2),
                    "pay": round(cost, 2),
                    "source": "job_timer"
                })
        
        # Calculate totals from manual entries
        manual_hours = sum(m.get("hours", 0) for m in manual_entries)
        manual_pay = sum(m.get("gross_pay", 0) for m in manual_entries)
        manual_details = [{
            "id": m.get("id"),
            "job_id": m.get("job_id"),
            "job_name": m.get("job_name", ""),
            "task_type": m.get("task_type", "general"),
            "date": m.get("date"),
            "hours": m.get("hours", 0),
            "pay": m.get("gross_pay", 0),
            "description": m.get("description", ""),
            "source": "manual"
        } for m in manual_entries]
        
        total_hours = round(job_hours + manual_hours, 2)
        total_pay = round(job_pay + manual_pay, 2)
        
        # Overtime calc: anything over 40 hours/week is 1.5x
        regular_hours = min(total_hours, 40)
        overtime_hours = max(total_hours - 40, 0)
        overtime_pay = round(overtime_hours * hourly_rate * 0.5, 2)  # Extra 0.5x on top of regular
        
        timesheet.append({
            "employee_id": emp_id,
            "employee_name": emp.get("name"),
            "hourly_rate": hourly_rate,
            "total_hours": total_hours,
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "regular_pay": round(regular_hours * hourly_rate, 2),
            "overtime_pay": overtime_pay,
            "total_pay": round(total_pay + overtime_pay, 2),
            "entries": sorted(job_details + manual_details, key=lambda x: x.get("date", ""), reverse=True)
        })
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "employees": timesheet,
        "totals": {
            "total_hours": round(sum(e["total_hours"] for e in timesheet), 2),
            "regular_hours": round(sum(e["regular_hours"] for e in timesheet), 2),
            "overtime_hours": round(sum(e["overtime_hours"] for e in timesheet), 2),
            "total_pay": round(sum(e["total_pay"] for e in timesheet), 2),
        }
    }


@payroll_router.get("/pay-period")
async def get_pay_period_summary(
    period_type: str = "weekly",  # weekly or biweekly
    reference_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get pay period summary with overtime calculations"""
    from datetime import date as date_type
    
    if reference_date:
        ref = date_type.fromisoformat(reference_date)
    else:
        ref = datetime.now(timezone.utc).date()
    
    # Calculate period start/end
    # Weekly: Monday to Sunday
    days_since_monday = ref.weekday()
    period_start = ref - timedelta(days=days_since_monday)
    
    if period_type == "biweekly":
        # Go back an extra week
        period_start = period_start - timedelta(days=7)
        period_end = period_start + timedelta(days=13)
    else:
        period_end = period_start + timedelta(days=6)
    
    start_str = period_start.isoformat()
    end_str = period_end.isoformat()
    
    employees = await db.employees.find({
        "tenant_id": current_user.tenant_id
    }, {"_id": 0}).to_list(1000)
    
    summary = []
    for emp in employees:
        emp_id = emp["id"]
        hourly_rate = emp.get("hourly_rate", 0)
        
        # Get all hours from both sources
        job_entries = await db.job_time_entries.find({
            "employee_id": emp_id,
            "tenant_id": current_user.tenant_id,
            "start_time": {"$gte": f"{start_str}T00:00:00", "$lte": f"{end_str}T23:59:59"}
        }, {"_id": 0}).to_list(1000)
        
        manual_entries = await db.payroll_hours.find({
            "employee_id": emp_id,
            "tenant_id": current_user.tenant_id,
            "date": {"$gte": start_str, "$lte": end_str}
        }, {"_id": 0}).to_list(1000)
        
        job_hours = sum((e.get("duration_minutes", 0) / 60) for e in job_entries)
        manual_hours_total = sum(m.get("hours", 0) for m in manual_entries)
        total_hours = round(job_hours + manual_hours_total, 2)
        
        # Overtime threshold depends on period type
        ot_threshold = 80 if period_type == "biweekly" else 40
        regular_hours = min(total_hours, ot_threshold)
        overtime_hours = max(total_hours - ot_threshold, 0)
        
        regular_pay = round(regular_hours * hourly_rate, 2)
        overtime_pay = round(overtime_hours * hourly_rate * 1.5, 2)
        
        # Get transactions in this period
        transactions = await db.payroll_transactions.find({
            "employee_id": emp_id,
            "date": {"$gte": start_str, "$lte": end_str}
        }, {"_id": 0}).to_list(1000)
        
        advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
        payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
        
        gross_pay = regular_pay + overtime_pay
        net_owed = gross_pay - advances - payments
        
        # Build daily breakdown
        daily = {}
        for je in job_entries:
            day = je.get("start_time", "")[:10]
            if day not in daily:
                daily[day] = 0
            daily[day] += je.get("duration_minutes", 0) / 60
        for me in manual_entries:
            day = me.get("date", "")
            if day not in daily:
                daily[day] = 0
            daily[day] += me.get("hours", 0)
        
        summary.append({
            "employee_id": emp_id,
            "employee_name": emp.get("name"),
            "hourly_rate": hourly_rate,
            "total_hours": total_hours,
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "regular_pay": regular_pay,
            "overtime_pay": overtime_pay,
            "gross_pay": gross_pay,
            "advances": advances,
            "payments_made": payments,
            "net_owed": round(net_owed, 2),
            "daily_hours": {k: round(v, 2) for k, v in sorted(daily.items())}
        })
    
    return {
        "period_type": period_type,
        "period_start": start_str,
        "period_end": end_str,
        "employees": summary,
        "totals": {
            "total_hours": round(sum(e["total_hours"] for e in summary), 2),
            "regular_hours": round(sum(e["regular_hours"] for e in summary), 2),
            "overtime_hours": round(sum(e["overtime_hours"] for e in summary), 2),
            "gross_pay": round(sum(e["gross_pay"] for e in summary), 2),
            "net_owed": round(sum(e["net_owed"] for e in summary), 2)
        }
    }



# ==================== SCHEDULE ENDPOINTS ====================

@payroll_router.get("/schedule")
async def get_schedule(
    week_start: str = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get employee schedule for a week."""
    if not week_start:
        from datetime import date
        today = date.today()
        week_start = (today - timedelta(days=today.weekday())).isoformat()

    schedules = await db.employee_schedules.find(
        {"tenant_id": current_user.tenant_id, "week_start": week_start},
        {"_id": 0}
    ).to_list(100)

    return {"week_start": week_start, "schedules": schedules}


@payroll_router.post("/schedule")
async def save_schedule(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Save or update a schedule entry for an employee on a specific day."""
    body = await request.json()
    employee_id = body.get("employee_id")
    week_start = body.get("week_start")
    day = body.get("day")  # mon, tue, wed, thu, fri, sat, sun
    start_time = body.get("start_time", "")
    end_time = body.get("end_time", "")
    notes = body.get("notes", "")

    if not employee_id or not week_start or not day:
        raise HTTPException(status_code=400, detail="employee_id, week_start, and day are required")

    existing = await db.employee_schedules.find_one(
        {"tenant_id": current_user.tenant_id, "employee_id": employee_id, "week_start": week_start},
        {"_id": 0}
    )

    if existing:
        shifts = existing.get("shifts", {})
        shifts[day] = {"start": start_time, "end": end_time, "notes": notes}
        await db.employee_schedules.update_one(
            {"id": existing["id"]},
            {"$set": {"shifts": shifts, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        schedule_doc = {
            "id": str(uuid.uuid4()),
            "tenant_id": current_user.tenant_id,
            "employee_id": employee_id,
            "week_start": week_start,
            "shifts": {day: {"start": start_time, "end": end_time, "notes": notes}},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.employee_schedules.insert_one(schedule_doc)

    return {"message": "Schedule saved", "employee_id": employee_id, "day": day}
