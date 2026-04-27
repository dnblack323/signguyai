"""
Employee, Time Clock, and Payroll Routes

This module contains all routes related to:
- Employee CRUD operations
- Time clock (punch in/out, breaks)
- Payroll transactions and balance tracking
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request
from typing import List, Optional, Dict, Any
from collections import defaultdict
from datetime import datetime, timezone, timedelta, date as date_type
from pydantic import BaseModel, Field
import uuid
import random

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
from services.email_service import email_service


# ============== LOCAL MODELS (to be moved to models/employees.py) ==============

class EmployeeBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    hourly_rate: float = 0
    overtime_rate: Optional[float] = None
    title: Optional[str] = None
    manager_name: Optional[str] = None
    role: str = "staff"
    is_active: bool = True
    tenant_id: Optional[str] = None
    pin: Optional[str] = None  # 4-6 digit PIN for employee portal login
    profile_image: Optional[str] = None  # URL to profile image
    linked_user_id: Optional[str] = None
    # Admin override: when set, bypasses the computed historical carryover balance
    # and uses this value directly. Set to 0.0 to zero out legacy carryover.
    carryover_override: Optional[float] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    hourly_rate: Optional[float] = None
    overtime_rate: Optional[float] = None
    title: Optional[str] = None
    manager_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    pin: Optional[str] = None
    profile_image: Optional[str] = None
    carryover_override: Optional[float] = None


class EmployeePinReset(BaseModel):
    pin: str


class EmployeePortalInviteRequest(BaseModel):
    origin_url: Optional[str] = None

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
    amount: float = Field(gt=0, description="Must be a positive magnitude. Sign is implied by `type`.")
    description: Optional[str] = Field(default=None, max_length=500)
    date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class PayrollTransactionUpdate(BaseModel):
    type: Optional[PayrollTransactionType] = None
    amount: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = Field(default=None, max_length=500)
    date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class PayrollTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: Optional[str] = None  # Optional for historical docs; set on all new writes.
    employee_id: str
    type: PayrollTransactionType
    amount: float
    description: Optional[str] = None
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PayrollPaidInFullRequest(BaseModel):
    employee_id: str
    period_start: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    period_end: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    paid_amount: float = Field(gt=0)
    paid_date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    notes: Optional[str] = Field(default=None, max_length=500)


class PayrollSignoff(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    week_start: str
    period_end: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_date: Optional[str] = None
    approved_by: Optional[str] = None
    approval_date: Optional[str] = None
    payroll_notes: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PayrollSignoffUpdate(BaseModel):
    employee_id: str
    week_start: str
    period_end: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_date: Optional[str] = None
    approved_by: Optional[str] = None
    approval_date: Optional[str] = None
    payroll_notes: Optional[str] = None


class LegacyManualEntryResolution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entry_id: str
    employee_id: str
    week_start: str
    period_end: Optional[str] = None
    handling_mode: str = "keep_legacy"
    target_date: Optional[str] = None
    admin_note: Optional[str] = None
    included_in_totals: bool = True
    reviewed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LegacyManualEntryResolutionUpdate(BaseModel):
    employee_id: str
    week_start: str
    period_end: Optional[str] = None
    handling_mode: str = "keep_legacy"
    target_date: Optional[str] = None
    admin_note: Optional[str] = None


class LegacyManualEntryResponse(BaseModel):
    id: str
    date: str
    source_type: str
    hours: float
    notes: Optional[str] = None
    current_effect_hours: float
    current_effect_pay: float
    current_effect_label: str
    included_in_totals: bool
    included_in_exports: bool
    handling_mode: str
    target_date: Optional[str] = None
    admin_note: Optional[str] = None
    resolution_saved: bool = False
    can_exclude: bool = False

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
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    notes: Optional[str] = None


class TimeClockShiftCreate(BaseModel):
    employee_id: str
    date: str
    clock_in: Optional[str] = None
    clock_out: Optional[str] = None
    break_minutes: Optional[float] = None
    lunch_start: Optional[str] = None
    lunch_end: Optional[str] = None
    notes: Optional[str] = None


# ============== ROUTERS ==============

employees_router = APIRouter(prefix="/employees", tags=["Employees"])
timeclock_router = APIRouter(prefix="/timeclock", tags=["Time Clock"])
payroll_router = APIRouter(prefix="/payroll", tags=["Payroll"])


def _require_payroll_edit_access(current_user: UserInDB):
    if current_user.role not in ["owner", "admin", "superadmin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="Only admin-level users can edit payroll data")


def _require_payroll_view_access(current_user: UserInDB):
    """Owner/admin can read payroll. Staff role is denied (no PAYROLL_VIEW)."""
    if current_user.role not in ["owner", "admin", "superadmin", "platform_admin"]:
        raise HTTPException(status_code=403, detail="You do not have permission to view payroll data")


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
        "employee_id": emp_id,
        "job_id": entry.get("job_id"),
        "job_name": entry.get("job_name", ""),
        "task_type": entry.get("task_type", "production"),
        "date": entry.get("start_time", "")[:10],
        "hours": round((entry.get("duration_minutes", 0) / 60), 2),
        "minutes": int(round(entry.get("duration_minutes", 0) or 0)),
        "pay": round(entry.get("labor_cost", 0), 2),
        "source": "job_timer"
    } for entry in job_entries]

    manual_details = [{
        "id": entry.get("id"),
        "employee_id": emp_id,
        "job_id": entry.get("job_id"),
        "job_name": entry.get("job_name", ""),
        "task_type": entry.get("task_type", "general"),
        "date": entry.get("date"),
        "hours": entry.get("hours", 0),
        "minutes": int(round((entry.get("hours", 0) or 0) * 60)),
        "pay": entry.get("gross_pay", 0),
        "description": entry.get("description", ""),
        "source": "manual"
    } for entry in manual_entries]

    shift_details = [{
        "id": shift.get("id"),
        "employee_id": emp_id,
        "job_id": None,
        "job_name": None,
        "task_type": "time_clock",
        "date": shift.get("date"),
        "hours": shift.get("net_hours", 0),
        # Prefer the precise integer `net_minutes` field over `net_hours * 60`
        # (which is already 2-decimal rounded, causing minute-level drift in
        # long payroll ranges).
        "minutes": int(shift.get("net_minutes") or round((shift.get("net_hours", 0) or 0) * 60)),
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


def _get_period_bounds(period_type: str, reference_date: Optional[str] = None, pay_week_start_day: str = "monday") -> tuple[str, str]:
    ref = date_type.fromisoformat(reference_date) if reference_date else datetime.now(timezone.utc).date()
    period_start = _get_pay_week_start(ref, pay_week_start_day)
    if period_type == "biweekly":
        period_start = period_start - timedelta(days=7)
        period_end = period_start + timedelta(days=13)
    else:
        period_end = period_start + timedelta(days=6)
    return period_start.isoformat(), period_end.isoformat()


def _resolve_report_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    period_type: str,
    reference_date: Optional[str],
    pay_week_start_day: str = "monday",
) -> tuple[str, str]:
    if period_type in {"weekly", "biweekly"}:
        return _get_period_bounds(period_type, reference_date, pay_week_start_day)

    if not start_date or not end_date:
        raise HTTPException(status_code=400, detail="start_date and end_date are required for custom reports")
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be before start_date")
    return start_date, end_date


def _get_overtime_threshold(start_date: str, end_date: str, period_type: str = "custom") -> int:
    if period_type == "weekly":
        return 40
    if period_type == "biweekly":
        return 80

    start = date_type.fromisoformat(start_date)
    end = date_type.fromisoformat(end_date)
    total_days = max((end - start).days + 1, 1)
    total_weeks = max((total_days + 6) // 7, 1)
    return total_weeks * 40


def _format_minutes_label(total_minutes: int) -> str:
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"


def _format_break_label(total_minutes: int) -> str:
    return _format_minutes_label(int(round(total_minutes or 0))) if total_minutes else "0h 0m"


def _entry_minutes(entry: dict) -> int:
    if entry.get("minutes") is not None:
        return int(round(entry.get("minutes") or 0))
    return int(round((entry.get("hours") or 0) * 60))


def _transaction_signed_amount(transaction: dict) -> float:
    txn_type = transaction.get("type")
    amount = float(transaction.get("amount") or 0)
    if txn_type == "earnings":
        return amount
    if txn_type in {"advance", "payment"}:
        return -amount
    return amount


def _get_week_end(week_start: str) -> str:
    return (date_type.fromisoformat(week_start) + timedelta(days=6)).isoformat()


DAY_NAME_TO_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


async def _get_tenant_payroll_settings(tenant_id: str) -> dict:
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "payroll_settings": 1})
    settings = (tenant or {}).get("payroll_settings") or {}
    return {
        "default_cycle": settings.get("default_cycle") or "weekly",
        "pay_week_start_day": settings.get("pay_week_start_day") or "monday",
        "show_payroll_adjustments": bool(settings.get("show_payroll_adjustments", False)),
    }


def _get_pay_week_start(date_value: date_type, pay_week_start_day: str) -> date_type:
    desired_weekday = DAY_NAME_TO_WEEKDAY.get((pay_week_start_day or "monday").lower(), 0)
    delta = (date_value.weekday() - desired_weekday) % 7
    return date_value - timedelta(days=delta)


def _serialize_legacy_manual_entry(entry: dict, resolution: Optional[dict], hourly_rate: float, week_start: str) -> LegacyManualEntryResponse:
    hours = float(entry.get("hours") or 0)
    pay = round(float(entry.get("gross_pay") or (hours * hourly_rate)), 2)
    handling_mode = (resolution or {}).get("handling_mode") or "keep_legacy"
    target_date = (resolution or {}).get("target_date") or entry.get("date")
    return LegacyManualEntryResponse(
        id=entry["id"],
        date=entry.get("date"),
        source_type=entry.get("task_type") or "manual legacy",
        hours=hours,
        notes=entry.get("description") or "",
        current_effect_hours=round(hours, 2),
        current_effect_pay=pay,
        current_effect_label=f"Included in current totals/export · {hours:.2f} hrs · ${pay:.2f}",
        included_in_totals=True,
        included_in_exports=True,
        handling_mode=handling_mode,
        target_date=target_date,
        admin_note=(resolution or {}).get("admin_note") or "",
        resolution_saved=bool(resolution),
        can_exclude=False,
    )


async def _get_employee_transactions(
    employee_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> list[dict]:
    """Read payroll transactions for an employee. Tenant-scoped by default;
    if `tenant_id` is provided, enforces it along with the legacy-doc fallback."""
    query: Dict[str, Any] = {"employee_id": employee_id}
    if tenant_id is not None:
        query["$or"] = [
            {"tenant_id": tenant_id},
            {"tenant_id": {"$exists": False}},  # legacy docs w/o tenant_id
        ]
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}

    transactions = await db.payroll_transactions.find(query, {"_id": 0}).sort("date", 1).to_list(5000)
    return transactions


def _summarize_transactions(transactions: list[dict]) -> dict:
    totals_by_type: dict[str, float] = defaultdict(float)
    serialized = []
    for transaction in transactions:
        amount = round(float(transaction.get("amount") or 0), 2)
        txn_type = transaction.get("type") or "other"
        totals_by_type[txn_type] += amount
        serialized.append({
            **transaction,
            "signed_amount": round(_transaction_signed_amount(transaction), 2),
        })

    earnings = round(totals_by_type.get("earnings", 0), 2)
    advances = round(totals_by_type.get("advance", 0), 2)
    payments = round(totals_by_type.get("payment", 0), 2)
    adjustments_total = round(earnings - advances - payments, 2)
    return {
        "transactions": serialized,
        "totals_by_type": {key: round(value, 2) for key, value in totals_by_type.items()},
        "earnings": earnings,
        "advances": advances,
        "payments": payments,
        "adjustments_total": adjustments_total,
    }


def _summarize_entry_pay(entries: list[dict], hourly_rate: float, overtime_rate: Optional[float] = None, pay_week_start_day: str = "monday") -> dict:
    weekly_minutes: dict[str, int] = defaultdict(int)
    total_minutes = 0
    base_pay = 0.0
    for entry in entries:
        minutes = _entry_minutes(entry)
        total_minutes += minutes
        base_pay += float(entry.get("pay") or 0)
        entry_date = entry.get("date")
        if entry_date:
            date_value = date_type.fromisoformat(entry_date)
            week_start = _get_pay_week_start(date_value, pay_week_start_day).isoformat()
            weekly_minutes[week_start] += minutes

    overtime_minutes = 0
    for minutes in weekly_minutes.values():
        overtime_minutes += max(minutes - (40 * 60), 0)

    regular_minutes = max(total_minutes - overtime_minutes, 0)
    effective_overtime_rate = float(overtime_rate) if overtime_rate is not None else round(float(hourly_rate or 0) * 1.5, 2)
    overtime_premium = round((overtime_minutes / 60) * max(effective_overtime_rate - float(hourly_rate or 0), 0), 2)
    gross_pay = round(base_pay + overtime_premium, 2)
    return {
        "total_minutes": total_minutes,
        "regular_minutes": regular_minutes,
        "overtime_minutes": overtime_minutes,
        "base_pay": round(base_pay, 2),
        "overtime_premium": overtime_premium,
        "overtime_rate": effective_overtime_rate,
        "gross_pay": gross_pay,
    }


def _build_daily_breakdown(entries: list[dict], transactions: list[dict]) -> list[dict]:
    grouped_entries: dict[str, list[dict]] = defaultdict(list)
    grouped_transactions: dict[str, list[dict]] = defaultdict(list)

    for entry in entries:
        grouped_entries[entry.get("date") or "unknown"].append(entry)
    for transaction in transactions:
        grouped_transactions[transaction.get("date") or "unknown"].append({
            **transaction,
            "signed_amount": round(_transaction_signed_amount(transaction), 2),
        })

    breakdown = []
    for date_key in sorted(set(grouped_entries.keys()) | set(grouped_transactions.keys())):
        day_entries = sorted(grouped_entries.get(date_key, []), key=lambda entry: entry.get("clock_in") or entry.get("date") or "")
        day_transactions = grouped_transactions.get(date_key, [])
        total_minutes = sum(_entry_minutes(entry) for entry in day_entries)
        break_minutes = sum(int(round(entry.get("break_minutes") or 0)) for entry in day_entries if entry.get("source") == "time_clock")
        base_pay = round(sum(float(entry.get("pay") or 0) for entry in day_entries), 2)
        day_adjustments = round(sum(transaction["signed_amount"] for transaction in day_transactions), 2)
        day_name = "—"
        if date_key and date_key != "unknown":
            day_name = date_type.fromisoformat(date_key).strftime("%A")

        breakdown.append({
            "date": date_key,
            "day_name": day_name,
            "total_minutes": total_minutes,
            "total_hours_label": _format_minutes_label(total_minutes),
            "break_minutes": break_minutes,
            "break_label": _format_break_label(break_minutes),
            "daily_pay": base_pay,
            "daily_adjustments": day_adjustments,
            "daily_final": round(base_pay + day_adjustments, 2),
            "entries": [
                {
                    **entry,
                    "hours_minutes_label": _format_minutes_label(_entry_minutes(entry)),
                    "break_label": _format_break_label(int(round(entry.get("break_minutes") or 0))),
                }
                for entry in day_entries
            ],
            "transactions": day_transactions,
        })

    return breakdown


async def _build_employee_payroll_snapshot(tenant_id: str, employee: dict, start_date: str, end_date: str, pay_week_start_day: str = "monday") -> dict:
    hourly_rate = float(employee.get("hourly_rate") or 0)
    overtime_rate = employee.get("overtime_rate")
    current_snapshot = await _get_employee_compensation_snapshot(tenant_id, employee, start_date, end_date)
    current_entries = sorted(
        current_snapshot["job_details"] + current_snapshot["manual_details"] + current_snapshot["shift_details"],
        key=lambda entry: (entry.get("date") or "", entry.get("clock_in") or ""),
    )
    current_pay = _summarize_entry_pay(current_entries, hourly_rate, overtime_rate, pay_week_start_day)
    current_transactions = await _get_employee_transactions(employee["id"], start_date, end_date, tenant_id=tenant_id)
    current_transaction_summary = _summarize_transactions(current_transactions)

    previous_end_date = date_type.fromisoformat(start_date) - timedelta(days=1)
    carryover_balance = 0.0
    previous_transaction_summary = _summarize_transactions([])
    carryover_override = employee.get("carryover_override")
    if carryover_override is not None:
        # Admin has explicitly set the carryover — use it verbatim and skip history calc.
        carryover_balance = round(float(carryover_override), 2)
    elif previous_end_date.isoformat() >= "2000-01-01":
        previous_snapshot = await _get_employee_compensation_snapshot(tenant_id, employee, "2000-01-01", previous_end_date.isoformat())
        previous_entries = previous_snapshot["job_details"] + previous_snapshot["manual_details"] + previous_snapshot["shift_details"]
        previous_pay = _summarize_entry_pay(previous_entries, hourly_rate, overtime_rate, pay_week_start_day)
        previous_transactions = await _get_employee_transactions(employee["id"], end_date=previous_end_date.isoformat(), tenant_id=tenant_id)
        previous_transaction_summary = _summarize_transactions(previous_transactions)
        carryover_balance = round(previous_pay["gross_pay"] + previous_transaction_summary["adjustments_total"], 2)

    final_owed = round(carryover_balance + current_pay["gross_pay"] + current_transaction_summary["adjustments_total"], 2)
    daily_breakdown = _build_daily_breakdown(current_entries, current_transaction_summary["transactions"])

    return {
        "entries": current_entries,
        "current_snapshot": current_snapshot,
        "current_pay": current_pay,
        "current_transaction_summary": current_transaction_summary,
        "previous_transaction_summary": previous_transaction_summary,
        "carryover_balance": carryover_balance,
        "daily_breakdown": daily_breakdown,
        "final_owed": final_owed,
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

    linked_user_id = None
    if employee_data.get("email"):
        existing_user = await db.users.find_one({"email": employee_data["email"].lower(), "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
        if existing_user:
            linked_user_id = existing_user["id"]
        else:
            from routes.auth import get_password_hash
            user_doc = UserInDB(
                email=employee_data["email"].lower(),
                full_name=employee_data.get("name", "Employee"),
                company_name=current_user.company_name,
                role="admin" if employee_data.get("role") == "admin" else "staff",
                tenant_id=current_user.tenant_id,
                hashed_password=get_password_hash(employee_data.get("pin") or "temporary-password"),
                is_active=employee_data.get("is_active", True),
            ).model_dump()
            linked_user_id = user_doc["id"]
            await db.users.insert_one(user_doc)
    employee_data["linked_user_id"] = linked_user_id
    
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
    raw = input.model_dump(exclude_unset=True)
    update_data = {k: v for k, v in raw.items() if v is not None}
    # Allow explicit null for carryover_override to clear the admin override
    # and fall back to computed carryover from historical entries.
    unset_fields = {}
    if "carryover_override" in raw and raw["carryover_override"] is None:
        unset_fields["carryover_override"] = ""
    mongo_update = {}
    if update_data:
        mongo_update["$set"] = update_data
    if unset_fields:
        mongo_update["$unset"] = unset_fields
    if not mongo_update:
        mongo_update = {"$set": {}}
    result = await db.employees.update_one({
        "id": employee_id,
        "tenant_id": current_user.tenant_id
    }, mongo_update)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    employee = await db.employees.find_one(
        {"id": employee_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    linked_user_id = employee.get("linked_user_id")
    if employee.get("email") and not linked_user_id:
        existing_user = await db.users.find_one({"email": employee["email"].lower(), "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
        if existing_user:
            linked_user_id = existing_user["id"]
        else:
            from routes.auth import get_password_hash
            user_doc = UserInDB(
                email=employee["email"].lower(),
                full_name=employee.get("name", "Employee"),
                company_name=current_user.company_name,
                role="admin" if employee.get("role") == "admin" else "staff",
                tenant_id=current_user.tenant_id,
                hashed_password=get_password_hash(employee.get("pin") or "temporary-password"),
                is_active=employee.get("is_active", True),
            ).model_dump()
            linked_user_id = user_doc["id"]
            await db.users.insert_one(user_doc)
        await db.employees.update_one({"id": employee_id}, {"$set": {"linked_user_id": linked_user_id}})
        employee["linked_user_id"] = linked_user_id

    if linked_user_id:
        await db.users.update_one(
            {"id": linked_user_id, "tenant_id": current_user.tenant_id},
            {"$set": {
                "email": employee.get("email", "").lower() if employee.get("email") else None,
                "full_name": employee.get("name", "Employee"),
                "role": "admin" if employee.get("role") == "admin" else "staff",
                "is_active": employee.get("is_active", True),
            }}
        )
    return employee


@employees_router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    employee = await db.employees.find_one({"id": employee_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.get("linked_user_id"):
        await db.users.delete_one({"id": employee["linked_user_id"], "tenant_id": current_user.tenant_id})

    await db.timelogs.delete_many({"employee_id": employee_id})
    await db.timeclock_shifts.delete_many({"employee_id": employee_id, "tenant_id": current_user.tenant_id})
    await db.payroll_hours.delete_many({"employee_id": employee_id, "tenant_id": current_user.tenant_id})
    await db.payroll_transactions.delete_many({"employee_id": employee_id})
    await db.employee_schedules.delete_many({"employee_id": employee_id, "tenant_id": current_user.tenant_id})
    await db.production_tasks.update_many({"assigned_to": employee_id, "tenant_id": current_user.tenant_id}, {"$set": {"assigned_to": None}})
    await db.job_tickets.update_many({"assigned_user_id": employee_id, "tenant_id": current_user.tenant_id}, {"$set": {"assigned_user_id": None}})
    await db.tasks.update_many({"assigned_to": employee_id, "tenant_id": current_user.tenant_id}, {"$set": {"assigned_to": None}})
    await db.employees.delete_one({"id": employee_id, "tenant_id": current_user.tenant_id})
    return {"message": "Employee deleted"}


@employees_router.post("/{employee_id}/reset-pin")
async def reset_employee_pin(
    employee_id: str,
    input: EmployeePinReset,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    if not input.pin or len(input.pin) < 4 or len(input.pin) > 6 or not input.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be 4-6 digits")
    result = await db.employees.update_one(
        {"id": employee_id, "tenant_id": current_user.tenant_id},
        {"$set": {"pin": input.pin}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "PIN updated"}


@employees_router.post("/{employee_id}/invite-portal")
async def invite_employee_to_portal(
    employee_id: str,
    input: EmployeePortalInviteRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    employee = await db.employees.find_one({"id": employee_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if not employee.get("email"):
        raise HTTPException(status_code=400, detail="Employee must have an email address before they can be invited")

    pin = employee.get("pin") or str(random.randint(1000, 9999))
    if not employee.get("pin"):
        await db.employees.update_one({"id": employee_id}, {"$set": {"pin": pin}})

    login_url = f"{(input.origin_url or '').rstrip('/')}/employee-portal/login" if input.origin_url else "/employee-portal/login"
    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "name": 1})
    company_name = (tenant or {}).get("name") or current_user.company_name or "Your Sign Shop"
    subject = f"{company_name} Employee Portal Access"
    html_content = f"""
      <div style='font-family:Arial,sans-serif;max-width:640px;margin:0 auto;padding:24px;'>
        <h2 style='color:#0f172a;'>You're invited to the employee portal</h2>
        <p>Hello {employee.get('name')},</p>
        <p>{current_user.full_name} invited you to the employee portal for <strong>{company_name}</strong>.</p>
        <div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin:16px 0;'>
          <p><strong>Login URL:</strong> <a href='{login_url}'>{login_url}</a></p>
          <p><strong>Email:</strong> {employee.get('email')}</p>
          <p><strong>PIN:</strong> {pin}</p>
        </div>
        <p>Use your email address and PIN to log in. Your admin can reset the PIN any time.</p>
      </div>
    """

    email_result = await email_service.send_email(
        to_email=employee["email"],
        subject=subject,
        html_content=html_content,
        tenant_id=current_user.tenant_id,
    )
    return {
        "message": "Employee portal invitation processed",
        "employee_id": employee_id,
        "employee_email": employee["email"],
        "temporary_pin": pin,
        "email_sent": bool(email_result.get("success")),
        "login_url": login_url,
        "email_error": email_result.get("error") if not email_result.get("success") else None,
    }


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
    """Get today's time logs for an employee (covers last 24h for timezone safety)"""
    employee = await db.employees.find_one({"id": employee_id, "tenant_id": current_user.tenant_id}, {"_id": 0, "id": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    # Use a 36h window to cover all timezone offsets from UTC
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=36)).isoformat()
    logs = await db.timelogs.find({
        "tenant_id": current_user.tenant_id,
        "employee_id": employee_id,
        "timestamp": {"$gte": cutoff}
    }, {"_id": 0}).sort("timestamp", 1).to_list(200)
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
    # Verify the employee belongs to this tenant before writing.
    employee = await db.employees.find_one(
        {"id": input.employee_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1},
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    input_data = {k: v for k, v in input.model_dump().items() if v is not None}
    transaction = PayrollTransaction(**input_data, tenant_id=current_user.tenant_id)
    doc = transaction.model_dump()
    await db.payroll_transactions.insert_one(doc)
    return transaction


@payroll_router.post("/mark-paid-in-full")
async def mark_payroll_paid_in_full(
    payload: PayrollPaidInFullRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create or update a period-specific payroll payment transaction."""
    _require_payroll_edit_access(current_user)
    if payload.period_end < payload.period_start:
        raise HTTPException(status_code=400, detail="period_end cannot be before period_start")

    employee = await db.employees.find_one(
        {"id": payload.employee_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1, "name": 1},
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    now = datetime.now(timezone.utc).isoformat()
    paid_date = payload.paid_date or payload.period_end
    description = (payload.notes or "").strip() or f"Paid in full for {payload.period_start} to {payload.period_end}"

    existing = await db.payroll_transactions.find_one(
        {
            "tenant_id": current_user.tenant_id,
            "employee_id": payload.employee_id,
            "type": "payment",
            "paid_in_full": True,
            "period_start": payload.period_start,
            "period_end": payload.period_end,
        },
        {"_id": 0, "id": 1},
    )

    if existing:
        transaction_id = existing["id"]
        await db.payroll_transactions.update_one(
            {"id": transaction_id, "tenant_id": current_user.tenant_id},
            {"$set": {
                "amount": round(float(payload.paid_amount), 2),
                "date": paid_date,
                "description": description,
                "updated_at": now,
            }},
        )
    else:
        transaction = PayrollTransaction(
            employee_id=payload.employee_id,
            tenant_id=current_user.tenant_id,
            type=PayrollTransactionType.PAYMENT,
            amount=round(float(payload.paid_amount), 2),
            description=description,
            date=paid_date,
        )
        transaction_doc = transaction.model_dump()
        transaction_doc.update({
            "period_start": payload.period_start,
            "period_end": payload.period_end,
            "paid_in_full": True,
            "updated_at": now,
        })
        await db.payroll_transactions.insert_one(transaction_doc)
        transaction_id = transaction_doc["id"]

    return {
        "message": "Payroll marked paid in full",
        "employee_id": payload.employee_id,
        "employee_name": employee.get("name", ""),
        "period_start": payload.period_start,
        "period_end": payload.period_end,
        "payment_transaction_id": transaction_id,
        "paid_amount": round(float(payload.paid_amount), 2),
        "paid_date": paid_date,
    }


@payroll_router.post("/timeclock-shifts")
async def create_timeclock_shift(
    input: TimeClockShiftCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a payroll worksheet time clock shift for a specific day."""
    _require_payroll_edit_access(current_user)
    employee = await db.employees.find_one({
        "id": input.employee_id,
        "tenant_id": current_user.tenant_id,
    }, {"_id": 0, "id": 1})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    shift = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "employee_id": input.employee_id,
        "date": input.date,
        "clock_in": input.clock_in,
        "clock_out": input.clock_out,
        "break_minutes": float(input.break_minutes or 0),
        "lunch_start": input.lunch_start,
        "lunch_end": input.lunch_end,
        "notes": input.notes or "",
        "source": "worksheet",
        "status": "finished" if input.clock_in and input.clock_out else "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    shift.update(calculate_shift_metrics(shift))
    await db.timeclock_shifts.insert_one(shift)
    shift.pop("_id", None)
    return shift


# ---------- Payroll transaction helpers ----------
async def _tenant_employee_ids(tenant_id: str) -> List[str]:
    """List of employee ids for this tenant — kept only for legacy
    payroll_transactions docs written before the model carried tenant_id.
    New code should filter by tenant_id directly."""
    docs = await db.employees.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1}).to_list(1000)
    return [e["id"] for e in docs]


@payroll_router.put("/transactions/{transaction_id}", response_model=PayrollTransaction)
async def update_payroll_transaction(
    transaction_id: str,
    input: PayrollTransactionUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    # Direct tenant_id filter — replaces the previous `$in` over all employees.
    # Falls back to the legacy employee-list match for pre-migration docs that
    # don't yet carry tenant_id.
    tenant_filter = {
        "$or": [
            {"tenant_id": current_user.tenant_id},
            {
                "tenant_id": {"$exists": False},
                "employee_id": {"$in": await _tenant_employee_ids(current_user.tenant_id)},
            },
        ],
    }
    result = await db.payroll_transactions.update_one(
        {"id": transaction_id, **tenant_filter},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    updated = await db.payroll_transactions.find_one(
        {"id": transaction_id, **tenant_filter}, {"_id": 0}
    )
    return updated


@payroll_router.delete("/transactions/{transaction_id}")
async def delete_payroll_transaction(
    transaction_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    tenant_filter = {
        "$or": [
            {"tenant_id": current_user.tenant_id},
            {
                "tenant_id": {"$exists": False},
                "employee_id": {"$in": await _tenant_employee_ids(current_user.tenant_id)},
            },
        ],
    }
    result = await db.payroll_transactions.delete_one(
        {"id": transaction_id, **tenant_filter}
    )
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
    _require_payroll_view_access(current_user)
    # Direct tenant_id filter + OR legacy employee-list match for pre-migration docs.
    legacy_ids = await _tenant_employee_ids(current_user.tenant_id)
    query: Dict[str, Any] = {
        "$or": [
            {"tenant_id": current_user.tenant_id},
            {"tenant_id": {"$exists": False}, "employee_id": {"$in": legacy_ids}},
        ]
    }
    if employee_id:
        if employee_id not in legacy_ids:
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


@payroll_router.get("/signoff", response_model=PayrollSignoff)
async def get_payroll_signoff(
    employee_id: str,
    week_start: str,
    period_end: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_view_access(current_user)
    signoff = await db.payroll_signoffs.find_one(
        {"tenant_id": current_user.tenant_id, "employee_id": employee_id, "week_start": week_start, "period_end": period_end},
        {"_id": 0},
    )
    if not signoff and period_end is None:
        signoff = await db.payroll_signoffs.find_one(
            {"tenant_id": current_user.tenant_id, "employee_id": employee_id, "week_start": week_start},
            {"_id": 0},
        )
    if signoff:
        return PayrollSignoff(**signoff)

    return PayrollSignoff(employee_id=employee_id, week_start=week_start, period_end=period_end)


@payroll_router.put("/signoff", response_model=PayrollSignoff)
async def upsert_payroll_signoff(
    payload: PayrollSignoffUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    now = datetime.now(timezone.utc).isoformat()
    existing = await db.payroll_signoffs.find_one(
        {"tenant_id": current_user.tenant_id, "employee_id": payload.employee_id, "week_start": payload.week_start, "period_end": payload.period_end},
        {"_id": 0, "id": 1, "created_at": 1},
    )
    next_doc = {
        "id": existing.get("id") if existing else str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "employee_id": payload.employee_id,
        "week_start": payload.week_start,
        "period_end": payload.period_end,
        "reviewed_by": payload.reviewed_by or "",
        "review_date": payload.review_date or None,
        "approved_by": payload.approved_by or "",
        "approval_date": payload.approval_date or None,
        "payroll_notes": payload.payroll_notes or "",
        "created_at": existing.get("created_at") if existing else now,
        "updated_at": now,
    }
    await db.payroll_signoffs.update_one(
        {"tenant_id": current_user.tenant_id, "employee_id": payload.employee_id, "week_start": payload.week_start, "period_end": payload.period_end},
        {"$set": next_doc},
        upsert=True,
    )
    saved = await db.payroll_signoffs.find_one(
        {"tenant_id": current_user.tenant_id, "employee_id": payload.employee_id, "week_start": payload.week_start, "period_end": payload.period_end},
        {"_id": 0},
    )
    return PayrollSignoff(**saved)


@payroll_router.get("/legacy-manual-entries", response_model=List[LegacyManualEntryResponse])
async def get_legacy_manual_entries(
    employee_id: str,
    week_start: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_view_access(current_user)
    period_start = start_date or week_start
    period_end = end_date or (_get_week_end(week_start) if week_start else None)
    if not period_start or not period_end:
        raise HTTPException(status_code=400, detail="start_date and end_date are required")
    employee = await db.employees.find_one(
        {"id": employee_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "hourly_rate": 1},
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    entries = await db.payroll_hours.find(
        {"tenant_id": current_user.tenant_id, "employee_id": employee_id, "date": {"$gte": period_start, "$lte": period_end}},
        {"_id": 0},
    ).sort("date", 1).to_list(500)
    if not entries:
        return []

    resolutions = await db.payroll_manual_entry_resolutions.find(
        {"tenant_id": current_user.tenant_id, "entry_id": {"$in": [entry["id"] for entry in entries]}},
        {"_id": 0},
    ).to_list(500)
    resolution_map = {resolution["entry_id"]: resolution for resolution in resolutions}
    hourly_rate = float(employee.get("hourly_rate") or 0)
    return [_serialize_legacy_manual_entry(entry, resolution_map.get(entry["id"]), hourly_rate, period_start) for entry in entries]


@payroll_router.put("/legacy-manual-entries/{entry_id}/resolution", response_model=LegacyManualEntryResponse)
async def upsert_legacy_manual_entry_resolution(
    entry_id: str,
    payload: LegacyManualEntryResolutionUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    entry = await db.payroll_hours.find_one(
        {"id": entry_id, "tenant_id": current_user.tenant_id, "employee_id": payload.employee_id},
        {"_id": 0},
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Legacy manual entry not found")

    period_end = payload.period_end or _get_week_end(payload.week_start)
    target_date = payload.target_date or entry.get("date")
    # Clamp target_date to the selected range (legacy entries may predate the period)
    if target_date < payload.week_start:
        target_date = payload.week_start
    if target_date > period_end:
        target_date = period_end

    if payload.handling_mode not in {"keep_legacy", "worksheet_manual_row", "merge_into_day"}:
        raise HTTPException(status_code=400, detail="Unsupported handling mode")

    existing = await db.payroll_manual_entry_resolutions.find_one(
        {"tenant_id": current_user.tenant_id, "entry_id": entry_id},
        {"_id": 0, "id": 1},
    )
    now = datetime.now(timezone.utc).isoformat()
    next_doc = LegacyManualEntryResolution(
        id=existing.get("id") if existing else str(uuid.uuid4()),
        entry_id=entry_id,
        employee_id=payload.employee_id,
        week_start=payload.week_start,
        period_end=payload.period_end,
        handling_mode=payload.handling_mode,
        target_date=target_date,
        admin_note=payload.admin_note or "",
        included_in_totals=True,
        reviewed_at=existing.get("reviewed_at") if existing and existing.get("reviewed_at") else now,
        updated_at=now,
    ).model_dump()
    next_doc["tenant_id"] = current_user.tenant_id

    await db.payroll_manual_entry_resolutions.update_one(
        {"tenant_id": current_user.tenant_id, "entry_id": entry_id},
        {"$set": next_doc},
        upsert=True,
    )

    employee = await db.employees.find_one(
        {"id": payload.employee_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "hourly_rate": 1},
    )
    return _serialize_legacy_manual_entry(entry, next_doc, float(employee.get("hourly_rate") or 0), payload.week_start)


@payroll_router.get("/balance/{employee_id}", response_model=PayrollBalance)
async def get_payroll_balance(
    employee_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get payroll balance for an employee (tenant-scoped)"""
    _require_payroll_view_access(current_user)
    employee = await db.employees.find_one({
        "id": employee_id,
        "tenant_id": current_user.tenant_id
    }, {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    snapshot = await _get_employee_compensation_snapshot(current_user.tenant_id, employee)
    entries = snapshot["job_details"] + snapshot["manual_details"] + snapshot["shift_details"]
    payroll_settings = await _get_tenant_payroll_settings(current_user.tenant_id)
    pay_summary = _summarize_entry_pay(entries, float(employee.get("hourly_rate") or 0), employee.get("overtime_rate"), payroll_settings["pay_week_start_day"])
    transaction_summary = _summarize_transactions(await _get_employee_transactions(employee_id, tenant_id=current_user.tenant_id))
    total_earnings = round(pay_summary["gross_pay"] + transaction_summary["earnings"], 2)
    total_advances = transaction_summary["advances"]
    total_payments = transaction_summary["payments"]
    balance = round(pay_summary["gross_pay"] + transaction_summary["adjustments_total"], 2)
    
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
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    employee_id: Optional[str] = None,
    period_type: str = Query("custom", pattern="^(custom|weekly|biweekly)$"),
    reference_date: Optional[str] = None,
    format: str = Query("json", pattern="^(json|csv)$"),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get payroll report for all employees in a date range (tenant-scoped)"""
    _require_payroll_view_access(current_user)
    payroll_settings = await _get_tenant_payroll_settings(current_user.tenant_id)
    start_date, end_date = _resolve_report_date_range(start_date, end_date, period_type, reference_date, payroll_settings["pay_week_start_day"])

    employee_query = {"tenant_id": current_user.tenant_id}
    if employee_id:
        employee_query["id"] = employee_id

    employees = await db.employees.find(employee_query, {"_id": 0}).to_list(1000)
    report = []
    
    for emp in employees:
        hourly_rate = float(emp.get("hourly_rate") or 0)
        payroll_snapshot = await _build_employee_payroll_snapshot(current_user.tenant_id, emp, start_date, end_date, payroll_settings["pay_week_start_day"])
        pay_summary = payroll_snapshot["current_pay"]
        transaction_summary = payroll_snapshot["current_transaction_summary"]
        
        report.append({
            "employee_id": emp["id"],
            "employee_name": emp["name"],
            "hourly_rate": hourly_rate,
            "overtime_rate": emp.get("overtime_rate") or round(hourly_rate * 1.5, 2),
            "hours": round(pay_summary["total_minutes"] / 60, 2),
            "total_minutes": pay_summary["total_minutes"],
            "total_hours_label": _format_minutes_label(pay_summary["total_minutes"]),
            "regular_hours": round(pay_summary["regular_minutes"] / 60, 2),
            "regular_minutes": pay_summary["regular_minutes"],
            "regular_hours_label": _format_minutes_label(pay_summary["regular_minutes"]),
            "overtime_hours": round(pay_summary["overtime_minutes"] / 60, 2),
            "overtime_minutes": pay_summary["overtime_minutes"],
            "overtime_hours_label": _format_minutes_label(pay_summary["overtime_minutes"]),
            "earnings": pay_summary["gross_pay"],
            "gross_pay": pay_summary["gross_pay"],
            "base_pay": pay_summary["base_pay"],
            "overtime_premium": pay_summary["overtime_premium"],
            "carryover_balance": payroll_snapshot["carryover_balance"],
            "earnings_adjustments": transaction_summary["earnings"],
            "advances": transaction_summary["advances"],
            "payments": transaction_summary["payments"],
            "adjustments_total": transaction_summary["adjustments_total"],
            "final_owed": payroll_snapshot["final_owed"],
            "balance": payroll_snapshot["final_owed"],
            "transactions": transaction_summary["transactions"],
            "transaction_totals": transaction_summary["totals_by_type"],
            "daily_breakdown": payroll_snapshot["daily_breakdown"],
        })
    
    result = {
        "period_type": period_type,
        "start_date": start_date,
        "end_date": end_date,
        "employee_count": len(report),
        "employees": report,
        "totals": {
            "hours": round(sum(r["hours"] for r in report), 2),
            "total_minutes": sum(r["total_minutes"] for r in report),
            "total_hours_label": _format_minutes_label(sum(r["total_minutes"] for r in report)),
            "regular_hours": round(sum(r["regular_hours"] for r in report), 2),
            "regular_minutes": sum(r["regular_minutes"] for r in report),
            "regular_hours_label": _format_minutes_label(sum(r["regular_minutes"] for r in report)),
            "overtime_hours": round(sum(r["overtime_hours"] for r in report), 2),
            "overtime_minutes": sum(r["overtime_minutes"] for r in report),
            "overtime_hours_label": _format_minutes_label(sum(r["overtime_minutes"] for r in report)),
            "earnings": sum(r["earnings"] for r in report),
            "carryover_balance": sum(r["carryover_balance"] for r in report),
            "earnings_adjustments": sum(r["earnings_adjustments"] for r in report),
            "advances": sum(r["advances"] for r in report),
            "payments": sum(r["payments"] for r in report),
            "adjustments_total": sum(r["adjustments_total"] for r in report),
            "balance": sum(r["balance"] for r in report),
            "final_owed": sum(r["final_owed"] for r in report),
        }
    }

    if format == "csv":
        import csv
        from io import StringIO
        from fastapi.responses import StreamingResponse

        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "Employee ID", "Employee Name", "Hourly Rate", "Overtime Rate",
            "Total Hours", "Regular Hours", "Overtime Hours",
            "Gross Pay", "Carryover Balance", "Earnings Adjustments",
            "Advances", "Payments", "Adjustments Total", "Final Owed"
        ])
        for r in report:
            writer.writerow([
                r["employee_id"], r["employee_name"], r["hourly_rate"], r["overtime_rate"],
                r["hours"], r["regular_hours"], r["overtime_hours"],
                r["gross_pay"], r["carryover_balance"], r["earnings_adjustments"],
                r["advances"], r["payments"], r["adjustments_total"], r["final_owed"]
            ])
        buffer.seek(0)
        filename = f"payroll_report_{start_date}_to_{end_date}.csv"
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    return result


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
    _require_payroll_view_access(current_user)
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
    _require_payroll_view_access(current_user)
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
        updates = input.model_dump(exclude_unset=True)
        updated = await update_timeclock_shift(db, current_user.tenant_id, shift_id, updates)
        return updated
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@payroll_router.delete("/timeclock-shifts/{shift_id}")
async def delete_timeclock_shift(
    shift_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    _require_payroll_edit_access(current_user)
    shift = await db.timeclock_shifts.find_one({"id": shift_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not shift:
        raise HTTPException(status_code=404, detail="Time clock shift not found")

    # Delete matching raw timelogs too, otherwise the shift will be auto-backfilled again.
    if shift.get("employee_id") and shift.get("date"):
        log_query = {
            "employee_id": shift["employee_id"],
            "tenant_id": current_user.tenant_id,
            "timestamp": {"$regex": f"^{shift['date']}"},
        }
        if shift.get("clock_in") and shift.get("clock_out"):
            log_query["timestamp"] = {"$gte": shift["clock_in"], "$lte": shift["clock_out"]}
        await db.timelogs.delete_many(log_query)

    result = await db.timeclock_shifts.delete_one({"id": shift_id, "tenant_id": current_user.tenant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Time clock shift not found")
    return {"message": "Time clock shift deleted"}


# ============== TIMESHEET & PAY PERIOD ROUTES ==============

@payroll_router.get("/timesheet")
async def get_timesheet(
    start_date: str,
    end_date: str,
    employee_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get consolidated timesheet - combines job time entries + manual hours"""
    _require_payroll_view_access(current_user)
    payroll_settings = await _get_tenant_payroll_settings(current_user.tenant_id)
    emp_query = {"tenant_id": current_user.tenant_id}
    if employee_id:
        emp_query["id"] = employee_id
    employees = await db.employees.find(emp_query, {"_id": 0}).to_list(1000)
    
    timesheet = []
    for emp in employees:
        hourly_rate = float(emp.get("hourly_rate") or 0)
        payroll_snapshot = await _build_employee_payroll_snapshot(current_user.tenant_id, emp, start_date, end_date, payroll_settings["pay_week_start_day"])
        pay_summary = payroll_snapshot["current_pay"]
        
        timesheet.append({
            "employee_id": emp["id"],
            "employee_name": emp.get("name"),
            "hourly_rate": hourly_rate,
            "overtime_rate": emp.get("overtime_rate") or round(hourly_rate * 1.5, 2),
            "total_hours": round(pay_summary["total_minutes"] / 60, 2),
            "total_minutes": pay_summary["total_minutes"],
            "total_hours_label": _format_minutes_label(pay_summary["total_minutes"]),
            "regular_hours": round(pay_summary["regular_minutes"] / 60, 2),
            "regular_minutes": pay_summary["regular_minutes"],
            "regular_hours_label": _format_minutes_label(pay_summary["regular_minutes"]),
            "overtime_hours": round(pay_summary["overtime_minutes"] / 60, 2),
            "overtime_minutes": pay_summary["overtime_minutes"],
            "overtime_hours_label": _format_minutes_label(pay_summary["overtime_minutes"]),
            "regular_pay": pay_summary["base_pay"],
            "overtime_pay": pay_summary["overtime_premium"],
            "total_pay": pay_summary["gross_pay"],
            "carryover_balance": payroll_snapshot["carryover_balance"],
            "transaction_summary": payroll_snapshot["current_transaction_summary"],
            "final_owed": payroll_snapshot["final_owed"],
            "daily_breakdown": payroll_snapshot["daily_breakdown"],
            "entries": list(reversed([
                {
                    **entry,
                    "hours_minutes_label": _format_minutes_label(_entry_minutes(entry)),
                    "break_label": _format_break_label(int(round(entry.get("break_minutes") or 0))),
                }
                for entry in payroll_snapshot["entries"]
            ]))
        })
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "employees": timesheet,
        "totals": {
            "total_hours": round(sum(e["total_hours"] for e in timesheet), 2),
            "total_minutes": sum(e["total_minutes"] for e in timesheet),
            "total_hours_label": _format_minutes_label(sum(e["total_minutes"] for e in timesheet)),
            "regular_hours": round(sum(e["regular_hours"] for e in timesheet), 2),
            "regular_minutes": sum(e["regular_minutes"] for e in timesheet),
            "regular_hours_label": _format_minutes_label(sum(e["regular_minutes"] for e in timesheet)),
            "overtime_hours": round(sum(e["overtime_hours"] for e in timesheet), 2),
            "overtime_minutes": sum(e["overtime_minutes"] for e in timesheet),
            "overtime_hours_label": _format_minutes_label(sum(e["overtime_minutes"] for e in timesheet)),
            "total_pay": round(sum(e["total_pay"] for e in timesheet), 2),
            "carryover_balance": round(sum(e["carryover_balance"] for e in timesheet), 2),
            "adjustments_total": round(sum(e["transaction_summary"]["adjustments_total"] for e in timesheet), 2),
            "final_owed": round(sum(e["final_owed"] for e in timesheet), 2),
        }
    }


@payroll_router.get("/pay-period")
async def get_pay_period_summary(
    period_type: str = "weekly",  # weekly or biweekly
    reference_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get pay period summary with overtime calculations"""
    _require_payroll_view_access(current_user)
    payroll_settings = await _get_tenant_payroll_settings(current_user.tenant_id)
    start_str, end_str = _get_period_bounds(period_type, reference_date, payroll_settings["pay_week_start_day"])
    
    employees = await db.employees.find({
        "tenant_id": current_user.tenant_id
    }, {"_id": 0}).to_list(1000)
    
    summary = []
    for emp in employees:
        payroll_snapshot = await _build_employee_payroll_snapshot(current_user.tenant_id, emp, start_str, end_str, payroll_settings["pay_week_start_day"])
        pay_summary = payroll_snapshot["current_pay"]
        transaction_summary = payroll_snapshot["current_transaction_summary"]
        daily = {
            day["date"]: {
                "hours": round(day["total_minutes"] / 60, 2),
                "hours_label": day["total_hours_label"],
                "pay": day["daily_pay"],
                "day_name": day["day_name"],
            }
            for day in payroll_snapshot["daily_breakdown"]
        }
        
        summary.append({
            "employee_id": emp["id"],
            "employee_name": emp.get("name"),
            "hourly_rate": emp.get("hourly_rate", 0),
            "overtime_rate": emp.get("overtime_rate") or round(float(emp.get("hourly_rate") or 0) * 1.5, 2),
            "total_hours": round(pay_summary["total_minutes"] / 60, 2),
            "total_minutes": pay_summary["total_minutes"],
            "total_hours_label": _format_minutes_label(pay_summary["total_minutes"]),
            "regular_hours": round(pay_summary["regular_minutes"] / 60, 2),
            "overtime_hours": round(pay_summary["overtime_minutes"] / 60, 2),
            "regular_pay": pay_summary["base_pay"],
            "overtime_pay": pay_summary["overtime_premium"],
            "gross_pay": pay_summary["gross_pay"],
            "carryover_balance": payroll_snapshot["carryover_balance"],
            "advances": transaction_summary["advances"],
            "payments_made": transaction_summary["payments"],
            "earnings_adjustments": transaction_summary["earnings"],
            "adjustments_total": transaction_summary["adjustments_total"],
            "net_owed": round(payroll_snapshot["final_owed"], 2),
            "daily_breakdown": payroll_snapshot["daily_breakdown"],
            "daily_hours": {key: value["hours"] for key, value in sorted(daily.items())},
            "daily": daily,
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
            "carryover_balance": round(sum(e["carryover_balance"] for e in summary), 2),
            "earnings_adjustments": round(sum(e["earnings_adjustments"] for e in summary), 2),
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
    _require_payroll_view_access(current_user)
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
