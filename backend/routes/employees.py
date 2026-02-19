"""
Employee, Time Clock, and Payroll Routes

This module contains all routes related to:
- Employee CRUD operations
- Time clock (punch in/out, breaks)
- Payroll transactions and balance tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
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
