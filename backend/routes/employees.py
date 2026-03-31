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
from services.timeclock_service import (
    backfill_timeclock_shifts,
    calculate_shift_metrics,
    get_timeclock_shifts,
    get_timeclock_status as get_shared_timeclock_status,
    get_timeclock_summary_for_date,
    record_timeclock_action,
    update_timeclock_shift,
)


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


class PayrollTransactionUpdate(BaseModel):
    type: Optional[PayrollTransactionType] = None
    amount: Optional[float] = None
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


class TimeClockShiftUpdate(BaseModel):
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None
    break_minutes: Optional[float] = None
    notes: Optional[str] = None


# ============== ROUTERS ==============

employees_router = APIRouter(prefix="/employees", tags=["Employees"])
timeclock_router = APIRouter(prefix="/timeclock", tags=["Time Clock"])
payroll_router = APIRouter(prefix="/payroll", tags=["Payroll"])


def _require_payroll_edit_access(current_user: UserInDB):
    if current_user.role not in ["owner", "admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Only admin-level users can edit payroll data")


async def _get_employee_compensation_snapshot(tenant_id: str, employee: dict, start_date: Optional[str] = None, end_date: Optional[str] = None):
    emp_id = employee["id"]
    hourly_rate = employee.get("hourly_rate", 0)

    if start_date and end_date:
        await backfill_timeclock_shifts(db, tenant_id, emp_id, start_date, end_date)
    else:
        earliest_log = await db.timelogs.find_one({"employee_id": emp_id}, {"_id": 0, "timestamp": 1}, sort=[("timestamp", 1)])
        if earliest_log and earliest_log.get("timestamp"):
            await backfill_timeclock_shifts(db, tenant_id, emp_id, earliest_log["timestamp"][:10], datetime.now(timezone.utc).date().isoformat())

    job_query = {"employee_id": emp_id, "tenant_id": tenant_id}
    if start_date and end_date:
        job_query["start_time"] = {"$gte": f"{start_date}T00:00:00", "$lte": f"{end_date}T23:59:59"}
    job_entries = await db.job_time_entries.find(job_query, {"_id": 0}).to_list(5000)

    manual_query = {"employee_id": emp_id, "tenant_id": tenant_id}
    if start_date and end_date:
        manual_query["date"] = {"$gte": start_date, "$lte": end_date}
    manual_entries = await db.payroll_hours.find(manual_query, {"_id": 0}).to_list(5000)

    shifts = await get_timeclock_shifts(db, tenant_id, employee_id=emp_id, start_date=start_date, end_date=end_date)

    job_hours = sum((entry.get("duration_minutes", 0) / 60) for entry in job_entries)
    manual_hours = sum(entry.get("hours", 0) for entry in manual_entries)
    clock_hours = sum(shift.get("net_hours", 0) for shift in shifts)

    job_details = [{
        "id": entry.get("id"),
        "job_id": entry.get("job_id"),
        "job_name": entry.get("job_name", ""),
        "task_type": entry.get("task_type", "production"),
        "date": entry.get("start_time", "")[:10],
        "hours": round((entry.get("duration_minutes", 0) / 60), 2),
        "pay": round(entry.get("labor_cost", 0), 2),
        "source": "job_timer"
    } for entry in job_entries]

    manual_details = [{
        "id": entry.get("id"),
        "job_id": entry.get("job_id"),
        "job_name": entry.get("job_name", ""),
        "task_type": entry.get("task_type", "general"),
        "date": entry.get("date"),
        "hours": entry.get("hours", 0),
        "pay": entry.get("gross_pay", 0),
        "description": entry.get("description", ""),
        "source": "manual"
    } for entry in manual_entries]

    shift_details = [{
        "id": shift.get("id"),
        "job_id": None,
        "job_name": None,
        "task_type": "time_clock",
        "date": shift.get("date"),
        "hours": shift.get("net_hours", 0),
        "pay": round((shift.get("net_hours", 0) * hourly_rate), 2),
        "description": shift.get("notes", ""),
        "clock_in": shift.get("clock_in"),
        "clock_out": shift.get("clock_out"),
        "break_minutes": shift.get("break_minutes", 0),
        "source": "time_clock"
    } for shift in shifts]

    total_hours = round(job_hours + manual_hours + clock_hours, 2)
    return {
        "job_entries": job_entries,
        "manual_entries": manual_entries,
        "timeclock_shifts": shifts,
        "job_details": job_details,
        "manual_details": manual_details,
        "shift_details": shift_details,
        "job_hours": round(job_hours, 2),
        "manual_hours": round(manual_hours, 2),
        "clock_hours": round(clock_hours, 2),
        "total_hours": total_hours,
    }


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
async def clock_action(input: TimeLogCreate, current_user: UserInDB = Depends(get_current_active_user)):
    """Record a time clock action (start_work, break_start, break_end, end_work)"""
    employee = await db.employees.find_one({"id": input.employee_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    try:
        log = await record_timeclock_action(db, current_user.tenant_id, input.employee_id, input.action)
        return TimeLog(**log)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@timeclock_router.get("/{employee_id}/today")
async def get_today_logs(employee_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get today's time logs for an employee"""
    employee = await db.employees.find_one({"id": employee_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    today = datetime.now(timezone.utc).date().isoformat()
    logs = await db.timelogs.find({
        "employee_id": employee_id,
        "timestamp": {"$regex": f"^{today}"}
    }, {"_id": 0}).sort("timestamp", 1).to_list(100)
    return logs


@timeclock_router.get("/{employee_id}/summary")
async def get_shift_summary(employee_id: str, date: Optional[str] = None, current_user: UserInDB = Depends(get_current_active_user)):
    """Get work/break time summary for an employee on a specific date"""
    if not date:
        date = datetime.now(timezone.utc).date().isoformat()
    employee = await db.employees.find_one({"id": employee_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return await get_timeclock_summary_for_date(db, current_user.tenant_id, employee_id, date)


@timeclock_router.get("/{employee_id}/status")
async def get_clock_status(employee_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    """Get current clock status for an employee"""
    employee = await db.employees.find_one({"id": employee_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return await get_shared_timeclock_status(db, current_user.tenant_id, employee_id)


# ============== PAYROLL ROUTES ==============

@payroll_router.post("/transactions", response_model=PayrollTransaction)
async def create_payroll_transaction(input: PayrollTransactionCreate, current_user: UserInDB = Depends(get_current_active_user)):
    """Create a payroll transaction (earnings, advance, payment)"""
    _require_payroll_edit_access(current_user)
    # Filter out None values to allow defaults to work
    input_data = {k: v for k, v in input.model_dump().items() if v is not None}
    transaction = PayrollTransaction(**input_data)
    doc = transaction.model_dump()
    await db.payroll_transactions.insert_one(doc)
    return transaction


@payroll_router.put("/transactions/{transaction_id}", response_model=PayrollTransaction)
async def update_payroll_transaction(
    transaction_id: str,
    input: PayrollTransactionUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    result = await db.payroll_transactions.update_one(
        {"id": transaction_id, "employee_id": {"$in": [emp["id"] for emp in await db.employees.find({"tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1}).to_list(1000)]}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    updated = await db.payroll_transactions.find_one({"id": transaction_id}, {"_id": 0})
    return updated


@payroll_router.delete("/transactions/{transaction_id}")
async def delete_payroll_transaction(
    transaction_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    tenant_employee_ids = [emp["id"] for emp in await db.employees.find({"tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1}).to_list(1000)]
    result = await db.payroll_transactions.delete_one({"id": transaction_id, "employee_id": {"$in": tenant_employee_ids}})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}


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
    
    snapshot = await _get_employee_compensation_snapshot(current_user.tenant_id, employee)
    total_earnings = round(employee.get("hourly_rate", 0) * snapshot["total_hours"], 2)
    transactions = await db.payroll_transactions.find({"employee_id": employee_id}, {"_id": 0}).to_list(1000)
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
        snapshot = await _get_employee_compensation_snapshot(current_user.tenant_id, emp, start_date, end_date)
        earnings = round(emp.get("hourly_rate", 0) * snapshot["total_hours"], 2)
        transactions = await db.payroll_transactions.find({"employee_id": emp["id"], "date": {"$gte": start_date, "$lte": end_date}}, {"_id": 0}).to_list(1000)
        advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
        payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
        
        report.append({
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "hourly_rate": emp.get("hourly_rate", 0),
            "hours": snapshot["total_hours"],
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
    _require_payroll_edit_access(current_user)
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
    _require_payroll_edit_access(current_user)
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
    _require_payroll_edit_access(current_user)
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


@payroll_router.get("/timeclock-shifts")
async def get_saved_timeclock_shifts(
    employee_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    target_employee_ids = [employee_id] if employee_id else [emp["id"] for emp in await db.employees.find({"tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1}).to_list(1000)]
    if start_date and end_date:
        for emp_id in target_employee_ids:
            await backfill_timeclock_shifts(db, current_user.tenant_id, emp_id, start_date, end_date)
    shifts = await get_timeclock_shifts(db, current_user.tenant_id, employee_id=employee_id, start_date=start_date, end_date=end_date)
    return shifts


@payroll_router.put("/timeclock-shifts/{shift_id}")
async def edit_timeclock_shift(
    shift_id: str,
    input: TimeClockShiftUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    try:
        updated = await update_timeclock_shift(db, current_user.tenant_id, shift_id, {k: v for k, v in input.model_dump().items() if v is not None})
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
        hourly_rate = emp.get("hourly_rate", 0)
        snapshot = await _get_employee_compensation_snapshot(current_user.tenant_id, emp, start_date, end_date)
        total_hours = snapshot["total_hours"]
        # Overtime calc: anything over 40 hours/week is 1.5x
        regular_hours = min(total_hours, 40)
        overtime_hours = max(total_hours - 40, 0)
        overtime_pay = round(overtime_hours * hourly_rate * 0.5, 2)  # Extra 0.5x on top of regular
        
        timesheet.append({
            "employee_id": emp["id"],
            "employee_name": emp.get("name"),
            "hourly_rate": hourly_rate,
            "total_hours": total_hours,
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "regular_pay": round(regular_hours * hourly_rate, 2),
            "overtime_pay": overtime_pay,
            "total_pay": round((total_hours * hourly_rate) + overtime_pay, 2),
            "entries": sorted(snapshot["job_details"] + snapshot["manual_details"] + snapshot["shift_details"], key=lambda x: (x.get("date", ""), x.get("clock_in", "")), reverse=True)
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
        hourly_rate = emp.get("hourly_rate", 0)
        snapshot = await _get_employee_compensation_snapshot(current_user.tenant_id, emp, start_str, end_str)
        total_hours = snapshot["total_hours"]
        
        # Overtime threshold depends on period type
        ot_threshold = 80 if period_type == "biweekly" else 40
        regular_hours = min(total_hours, ot_threshold)
        overtime_hours = max(total_hours - ot_threshold, 0)
        
        regular_pay = round(regular_hours * hourly_rate, 2)
        overtime_pay = round(overtime_hours * hourly_rate * 1.5, 2)
        
        # Get transactions in this period
        transactions = await db.payroll_transactions.find({"employee_id": emp["id"], "date": {"$gte": start_str, "$lte": end_str}}, {"_id": 0}).to_list(1000)
        
        advances = sum(t["amount"] for t in transactions if t["type"] == "advance")
        payments = sum(t["amount"] for t in transactions if t["type"] == "payment")
        
        gross_pay = regular_pay + overtime_pay
        net_owed = gross_pay - advances - payments
        
        daily = {}
        for entry in snapshot["job_details"] + snapshot["manual_details"] + snapshot["shift_details"]:
            day = entry.get("date", "")
            if not day:
                continue
            daily.setdefault(day, 0)
            daily[day] += float(entry.get("hours", 0) or 0)
        
        summary.append({
            "employee_id": emp["id"],
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
    _require_payroll_edit_access(current_user)
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
