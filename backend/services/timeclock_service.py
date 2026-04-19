"""Shared timeclock + payroll helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
import uuid


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_bounds(day_str: str) -> tuple[str, str]:
    return f"{day_str}T00:00:00", f"{day_str}T23:59:59"


STALE_SHIFT_HOURS = 18


async def _auto_close_stale_shift(db, shift: dict) -> bool:
    """If a shift has been open longer than STALE_SHIFT_HOURS, auto-close it.
    Returns True if the shift was closed (i.e., was stale)."""
    if not shift:
        return False
    clock_in = _parse_iso(shift.get("clock_in"))
    if not clock_in:
        return False
    age = datetime.now(timezone.utc) - clock_in
    if age <= timedelta(hours=STALE_SHIFT_HOURS):
        return False
    # Cap clock_out at clock_in + 8h to avoid absurd totals from orphaned shifts
    synthetic_clock_out = (clock_in + timedelta(hours=8)).isoformat()
    updated_shift = {
        **shift,
        "clock_out": synthetic_clock_out,
        "status": "finished",
        "current_break_start": None,
        "updated_at": _now_iso(),
        "auto_closed": True,
    }
    updated_shift.update(calculate_shift_metrics(updated_shift))
    await db.timeclock_shifts.update_one({"id": shift["id"]}, {"$set": updated_shift})
    return True


async def _cleanup_stale_open_shifts(db, tenant_id: str, employee_id: str) -> None:
    """Auto-close all stale open shifts for this employee."""
    cursor = db.timeclock_shifts.find(
        {"tenant_id": tenant_id, "employee_id": employee_id, "status": {"$in": ["working", "on_break"]}},
        {"_id": 0}
    )
    async for shift in cursor:
        await _auto_close_stale_shift(db, shift)


def calculate_shift_metrics(shift: dict) -> dict:
    clock_in = _parse_iso(shift.get("clock_in"))
    clock_out = _parse_iso(shift.get("clock_out")) or datetime.now(timezone.utc)
    break_minutes = float(shift.get("break_minutes", 0) or 0)
    if not clock_in or not clock_out:
      return {"work_minutes": 0.0, "net_minutes": 0.0, "net_hours": 0.0}
    work_minutes = max((clock_out - clock_in).total_seconds() / 60, 0)
    net_minutes = max(work_minutes - break_minutes, 0)
    return {
        "work_minutes": round(work_minutes, 2),
        "net_minutes": round(net_minutes, 2),
        "net_hours": round(net_minutes / 60, 2),
    }


async def backfill_timeclock_shifts(db, tenant_id: str, employee_id: str, start_date: str, end_date: str):
    existing = await db.timeclock_shifts.find(
        {"tenant_id": tenant_id, "employee_id": employee_id, "date": {"$gte": start_date, "$lte": end_date}},
        {"_id": 0, "date": 1}
    ).to_list(500)
    existing_dates = {shift["date"] for shift in existing}

    logs = await db.timelogs.find(
        {"employee_id": employee_id, "timestamp": {"$gte": f"{start_date}T00:00:00", "$lte": f"{end_date}T23:59:59"}},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(5000)

    grouped: Dict[str, List[dict]] = {}
    for log in logs:
        day = (log.get("timestamp") or "")[:10]
        if not day or day in existing_dates:
            continue
        grouped.setdefault(day, []).append(log)

    for day, day_logs in grouped.items():
        current_shift = None
        current_break_start = None
        shifts_to_insert = []

        for log in day_logs:
            action = log.get("action")
            timestamp = log.get("timestamp")
            if action == "start_work":
                if current_shift and not current_shift.get("clock_out"):
                    current_shift["clock_out"] = timestamp
                    current_shift.update(calculate_shift_metrics(current_shift))
                    current_shift["status"] = "finished"
                    shifts_to_insert.append(current_shift)
                current_shift = {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "employee_id": employee_id,
                    "date": day,
                    "clock_in": timestamp,
                    "clock_out": None,
                    "break_minutes": 0.0,
                    "status": "working",
                    "notes": "",
                    "source": "time_clock",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                }
                current_break_start = None
            elif action == "break_start" and current_shift:
                current_break_start = timestamp
                current_shift["status"] = "on_break"
            elif action == "break_end" and current_shift and current_break_start:
                break_start = _parse_iso(current_break_start)
                break_end = _parse_iso(timestamp)
                if break_start and break_end:
                    current_shift["break_minutes"] = float(current_shift.get("break_minutes", 0)) + max((break_end - break_start).total_seconds() / 60, 0)
                current_break_start = None
                current_shift["status"] = "working"
            elif action == "end_work" and current_shift:
                current_shift["clock_out"] = timestamp
                current_shift.update(calculate_shift_metrics(current_shift))
                current_shift["status"] = "finished"
                current_shift["updated_at"] = timestamp
                shifts_to_insert.append(current_shift)
                current_shift = None
                current_break_start = None

        if current_shift:
            current_shift.update(calculate_shift_metrics(current_shift))
            current_shift["updated_at"] = current_shift.get("clock_out") or current_shift.get("clock_in")
            shifts_to_insert.append(current_shift)

        if shifts_to_insert:
            await db.timeclock_shifts.insert_many(shifts_to_insert)


async def get_timeclock_shifts(db, tenant_id: str, employee_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[dict]:
    query = {"tenant_id": tenant_id}
    if employee_id:
        query["employee_id"] = employee_id
    if start_date and end_date:
        query["date"] = {"$gte": start_date, "$lte": end_date}
    elif start_date:
        query["date"] = {"$gte": start_date}
    elif end_date:
        query["date"] = {"$lte": end_date}
    shifts = await db.timeclock_shifts.find(query, {"_id": 0}).sort([("date", -1), ("clock_in", -1)]).to_list(5000)
    enriched = []
    for shift in shifts:
        metrics = calculate_shift_metrics(shift)
        enriched.append({**shift, **metrics})
    return enriched


async def record_timeclock_action(db, tenant_id: str, employee_id: str, action: str) -> dict:
    valid_actions = ["start_work", "break_start", "break_end", "end_work"]
    if action not in valid_actions:
        raise ValueError(f"Invalid action: {action}")

    # Defensive: auto-close any stale open shifts from prior days before evaluating state
    await _cleanup_stale_open_shifts(db, tenant_id, employee_id)

    # Find any open shift for this employee (regardless of date) to handle timezone boundary
    open_shift = await db.timeclock_shifts.find_one(
        {"tenant_id": tenant_id, "employee_id": employee_id, "status": {"$in": ["working", "on_break"]}},
        {"_id": 0},
        sort=[("clock_in", -1)]
    )

    # Determine current effective status from the open shift
    current_status = None
    if open_shift:
        current_status = "start_work" if open_shift["status"] == "working" else "break_start"
    else:
        # Fallback: check recent timelogs (last 48h window) for sequence validation
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        recent_logs = await db.timelogs.find(
            {"employee_id": employee_id, "timestamp": {"$gte": cutoff}},
            {"_id": 0}
        ).sort("timestamp", -1).to_list(1)
        if recent_logs:
            last = recent_logs[0]["action"]
            current_status = last if last == "end_work" else None

    valid_sequences = {
        None: ["start_work"],
        "start_work": ["break_start", "end_work"],
        "break_start": ["break_end"],
        "break_end": ["break_start", "end_work"],
        "end_work": ["start_work"],
    }
    if action not in valid_sequences.get(current_status, []):
        raise ValueError(f"Invalid sequence. After '{current_status}', valid actions are: {valid_sequences.get(current_status, [])}")

    timestamp = _now_iso()
    today = timestamp[:10]
    log = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "employee_id": employee_id,
        "action": action,
        "timestamp": timestamp,
    }
    await db.timelogs.insert_one(log)

    if action == "start_work":
        # Close any stale open shift first
        if open_shift:
            stale_update = {**open_shift, "clock_out": timestamp, "status": "finished", "updated_at": timestamp, "current_break_start": None}
            stale_update.update(calculate_shift_metrics(stale_update))
            await db.timeclock_shifts.update_one({"id": open_shift["id"]}, {"$set": stale_update})
        shift = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "employee_id": employee_id,
            "date": today,
            "clock_in": timestamp,
            "clock_out": None,
            "break_minutes": 0.0,
            "status": "working",
            "notes": "",
            "source": "time_clock",
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        await db.timeclock_shifts.insert_one(shift)
    elif action == "break_start" and open_shift:
        await db.timeclock_shifts.update_one({"id": open_shift["id"]}, {"$set": {"status": "on_break", "current_break_start": timestamp, "updated_at": timestamp}})
    elif action == "break_end" and open_shift:
        break_start = _parse_iso(open_shift.get("current_break_start"))
        break_end = _parse_iso(timestamp)
        break_minutes = float(open_shift.get("break_minutes", 0) or 0)
        if break_start and break_end:
            break_minutes += max((break_end - break_start).total_seconds() / 60, 0)
        await db.timeclock_shifts.update_one({"id": open_shift["id"]}, {"$set": {"status": "working", "current_break_start": None, "break_minutes": round(break_minutes, 2), "updated_at": timestamp}})
    elif action == "end_work" and open_shift:
        updated_shift = {**open_shift, "clock_out": timestamp, "status": "finished", "updated_at": timestamp, "current_break_start": None}
        metrics = calculate_shift_metrics(updated_shift)
        await db.timeclock_shifts.update_one({"id": open_shift["id"]}, {"$set": {**updated_shift, **metrics}})

    log.pop("_id", None)
    return log


async def get_timeclock_status(db, tenant_id: str, employee_id: str) -> dict:
    # Defensive: auto-close any stale open shifts from prior days
    await _cleanup_stale_open_shifts(db, tenant_id, employee_id)

    # Primary: check for any open shift (survives timezone boundary)
    open_shift = await db.timeclock_shifts.find_one(
        {"tenant_id": tenant_id, "employee_id": employee_id, "status": {"$in": ["working", "on_break"]}},
        {"_id": 0},
        sort=[("clock_in", -1)]
    )
    if open_shift:
        status = "working" if open_shift["status"] == "working" else "on_break"
        return {
            "status": status,
            "last_action": "start_work" if status == "working" else "break_start",
            "last_timestamp": open_shift.get("updated_at") or open_shift.get("clock_in"),
        }

    # Fallback: check recent timelogs (48h window covers timezone edge cases)
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    logs = await db.timelogs.find(
        {"employee_id": employee_id, "timestamp": {"$gte": cutoff}},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(1)
    if not logs:
        return {"status": "not_started", "last_action": None}

    last_log = logs[0]
    status_map = {
        "start_work": "working",
        "break_start": "on_break",
        "break_end": "working",
        "end_work": "finished",
    }
    return {
        "status": status_map.get(last_log["action"], "unknown"),
        "last_action": last_log["action"],
        "last_timestamp": last_log["timestamp"],
    }


async def get_timeclock_summary_for_date(db, tenant_id: str, employee_id: str, date_str: str) -> dict:
    await backfill_timeclock_shifts(db, tenant_id, employee_id, date_str, date_str)
    shifts = await get_timeclock_shifts(db, tenant_id, employee_id=employee_id, start_date=date_str, end_date=date_str)
    work_minutes = round(sum(shift.get("work_minutes", 0) for shift in shifts), 2)
    break_minutes = round(sum(float(shift.get("break_minutes", 0) or 0) for shift in shifts), 2)
    net_minutes = round(sum(shift.get("net_minutes", 0) for shift in shifts), 2)
    return {
        "employee_id": employee_id,
        "date": date_str,
        "work_minutes": work_minutes,
        "break_minutes": break_minutes,
        "net_minutes": net_minutes,
        "net_hours": round(net_minutes / 60, 2),
    }


async def update_timeclock_shift(db, tenant_id: str, shift_id: str, updates: dict) -> dict:
    shift = await db.timeclock_shifts.find_one({"id": shift_id, "tenant_id": tenant_id}, {"_id": 0})
    if not shift:
        raise ValueError("Time clock shift not found")
    next_shift = {**shift, **updates, "updated_at": _now_iso()}
    if next_shift.get("clock_in"):
        next_shift["date"] = str(next_shift["clock_in"])[:10]
    next_shift.update(calculate_shift_metrics(next_shift))
    await db.timeclock_shifts.update_one({"id": shift_id}, {"$set": next_shift})
    return next_shift
