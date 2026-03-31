"""Shared productivity query and normalization layer."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from models.productivity import ProductivityItem, ProductivitySummary


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        if len(value) == 10:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _to_iso(value: Optional[datetime]) -> Optional[str]:
    return value.astimezone(timezone.utc).isoformat() if value else None


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _start_of_week(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _status_color(status: str, item_type: str, is_completed: bool) -> str:
    if is_completed:
        return "emerald"
    status = (status or "").lower()
    if "overdue" in status or status in {"blocked", "cancelled", "rework", "on_hold"}:
        return "red"
    if status in {"pending", "waiting", "awaiting_approval", "awaiting_quote", "awaiting_review"}:
        return "amber"
    if status in {"approved", "scheduled", "confirmed", "in_progress", "in_production"}:
        return "blue"
    if item_type in {"schedule_shift", "appointment"}:
        return "violet"
    return "slate"


def _build_item(**kwargs: Any) -> ProductivityItem:
    item = ProductivityItem(**kwargs)
    return item


async def _load_maps(db, tenant_id: str) -> Dict[str, Dict[str, Any]]:
    customers = await db.customers.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1, "company": 1}).to_list(5000)
    employees = await db.employees.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    orders = await db.orders.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(2000)
    jobs = await db.jobs.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(2000)
    tickets = await db.job_tickets.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1, "order_id": 1, "ticket_number": 1, "item_name": 1, "priority": 1, "due_date": 1, "assigned_user_id": 1}).to_list(5000)
    return {
        "customers": {customer["id"]: customer for customer in customers},
        "employees": {employee["id"]: employee for employee in employees},
        "orders": {order["id"]: order for order in orders},
        "jobs": {job["id"]: job for job in jobs},
        "tickets": {ticket["id"]: ticket for ticket in tickets},
    }


def _map_task(task: dict, maps: Dict[str, Dict[str, Any]]) -> ProductivityItem:
    job = maps["jobs"].get(task.get("job_id"), {})
    assigned_employee = maps["employees"].get(task.get("assigned_to"), {})
    due_dt = _parse_dt(task.get("due_date"))
    is_completed = bool(task.get("is_complete"))
    status = "completed" if is_completed else "open"
    return _build_item(
        uid=f"task:{task['id']}",
        id=task["id"],
        title=task.get("title") or "Task",
        type="task",
        source_type="task",
        source_id=task["id"],
        related_job_id=task.get("job_id"),
        related_customer_id=job.get("customer_id"),
        customer_name=(maps["customers"].get(job.get("customer_id"), {}) or {}).get("name"),
        assigned_user_id=task.get("assigned_to"),
        assigned_user_name=assigned_employee.get("name"),
        status=status,
        priority=task.get("priority", "normal") or "normal",
        due_datetime=_to_iso(due_dt),
        all_day=True,
        is_completed=is_completed,
        board_column="done" if is_completed else "to_do",
        notes=task.get("description") or "",
        category="task",
        color=_status_color(status, "task", is_completed),
        source_route="/productivity?view=tasks",
        source_reference=job.get("name") or task.get("job_id"),
        source_label="Task List",
        meta={"job_name": job.get("name")},
    )


def _map_order(order: dict, maps: Dict[str, Dict[str, Any]]) -> ProductivityItem:
    customer = maps["customers"].get(order.get("customer_id"), {})
    due_dt = _parse_dt(order.get("requested_due_date"))
    status = order.get("status", "new_intake")
    is_completed = status in {"completed", "ready_for_pickup"}
    return _build_item(
        uid=f"order:{order['id']}",
        id=order["id"],
        title=order.get("order_number") or order.get("customer_name") or "Order",
        type="job",
        source_type="order",
        source_id=order["id"],
        related_order_id=order["id"],
        related_customer_id=order.get("customer_id"),
        customer_name=customer.get("name") or order.get("customer_name"),
        status=status,
        priority="high" if status in {"awaiting_quote", "awaiting_review"} else "normal",
        due_datetime=_to_iso(due_dt),
        all_day=True,
        is_completed=is_completed,
        board_column=status,
        notes=order.get("internal_notes") or order.get("pickup_delivery_notes") or "",
        category="order",
        color=_status_color(status, "job", is_completed),
        source_route=f"/orders/{order['id']}",
        source_reference=order.get("order_number"),
        source_label="Order",
        meta={"payment_status": order.get("payment_status"), "approval_status": order.get("approval_status")},
    )


def _map_legacy_job(job: dict, maps: Dict[str, Dict[str, Any]]) -> ProductivityItem:
    customer = maps["customers"].get(job.get("customer_id"), {})
    due_dt = _parse_dt(job.get("due_date"))
    status = job.get("status", "quote")
    is_completed = status in {"completed", "archived"}
    assigned_employees = job.get("assigned_employees") or []
    assigned_employee = maps["employees"].get(assigned_employees[0], {}) if assigned_employees else {}
    return _build_item(
        uid=f"legacy_job:{job['id']}",
        id=job["id"],
        title=job.get("name") or "Legacy Job",
        type="job",
        source_type="legacy_job",
        source_id=job["id"],
        related_job_id=job["id"],
        related_customer_id=job.get("customer_id"),
        customer_name=customer.get("name"),
        assigned_user_id=assigned_employees[0] if assigned_employees else None,
        assigned_user_name=assigned_employee.get("name"),
        status=status,
        priority="normal",
        due_datetime=_to_iso(due_dt),
        all_day=True,
        is_completed=is_completed,
        board_column=status,
        notes=job.get("notes") or job.get("description") or "",
        category="legacy_job",
        color=_status_color(status, "job", is_completed),
        source_route=None,
        source_reference=job.get("name"),
        source_label="Legacy Job",
        meta={"archived": job.get("is_archived", False)},
    )


def _map_production_task(task: dict, maps: Dict[str, Dict[str, Any]]) -> ProductivityItem:
    ticket = maps["tickets"].get(task.get("job_ticket_id"), {})
    order = maps["orders"].get(task.get("order_id"), {})
    customer = maps["customers"].get(order.get("customer_id"), {})
    assigned_employee = maps["employees"].get(task.get("assigned_to"), {})
    due_dt = _parse_dt(ticket.get("due_date") or order.get("requested_due_date"))
    start_dt = _parse_dt(task.get("start_datetime"))
    status = task.get("status", "not_started")
    is_completed = status == "complete"
    priority = ticket.get("priority", "normal") or "normal"
    return _build_item(
        uid=f"production_task:{task['id']}",
        id=task["id"],
        title=task.get("task_name") or ticket.get("item_name") or "Production Task",
        type="production_task",
        source_type="production_task",
        source_id=task["id"],
        related_order_id=task.get("order_id"),
        related_job_ticket_id=task.get("job_ticket_id"),
        related_customer_id=order.get("customer_id"),
        customer_name=customer.get("name") or order.get("customer_name"),
        assigned_user_id=task.get("assigned_to") or ticket.get("assigned_user_id"),
        assigned_user_name=assigned_employee.get("name") or (maps["employees"].get(ticket.get("assigned_user_id"), {}) or {}).get("name"),
        status=status,
        priority=priority,
        start_datetime=_to_iso(start_dt),
        due_datetime=_to_iso(due_dt),
        all_day=start_dt is None,
        is_completed=is_completed,
        board_column=status,
        notes=task.get("notes") or "",
        category=task.get("department") or "production",
        color=_status_color(status, "production_task", is_completed),
        source_route=f"/job-tickets/{task.get('job_ticket_id')}?tab=production" if task.get("job_ticket_id") else "/production-board",
        source_reference=ticket.get("ticket_number"),
        source_label="Production Board",
        meta={"department": task.get("department"), "order_number": order.get("order_number"), "ticket_name": ticket.get("item_name")},
    )


def _expand_schedule_shift(schedule_doc: dict, day_key: str, shift: dict, day_date: date, maps: Dict[str, Dict[str, Any]]) -> ProductivityItem:
    employee = maps["employees"].get(schedule_doc.get("employee_id"), {})
    start_dt = None
    end_dt = None
    if shift.get("start"):
        start_dt = _parse_dt(f"{day_date.isoformat()}T{shift['start']}:00")
    if shift.get("end"):
        end_dt = _parse_dt(f"{day_date.isoformat()}T{shift['end']}:00")
    return _build_item(
        uid=f"schedule_shift:{schedule_doc['id']}:{day_key}",
        id=schedule_doc["id"],
        title=f"{employee.get('name', 'Employee')} Shift",
        type="schedule_shift",
        source_type="employee_schedule",
        source_id=schedule_doc["id"],
        assigned_user_id=schedule_doc.get("employee_id"),
        assigned_user_name=employee.get("name"),
        status="scheduled",
        priority="normal",
        start_datetime=_to_iso(start_dt),
        due_datetime=_to_iso(end_dt or start_dt),
        all_day=False,
        is_completed=False,
        board_column="scheduled",
        notes=shift.get("notes") or "",
        category="schedule",
        color="violet",
        source_route="/payroll?tab=schedule",
        source_reference=day_date.isoformat(),
        source_label="Employee Schedule",
        meta={"shift_start": shift.get("start"), "shift_end": shift.get("end")},
    )


def _map_appointment(appointment: dict, maps: Dict[str, Dict[str, Any]]) -> ProductivityItem:
    customer = maps["customers"].get(appointment.get("customer_id"), {})
    start_dt = _parse_dt(appointment.get("scheduled_at") or appointment.get("scheduled_date"))
    end_dt = start_dt + timedelta(minutes=int(appointment.get("duration_minutes", 60) or 60)) if start_dt else None
    status = appointment.get("status", "scheduled")
    is_completed = status in {"completed", "cancelled"}
    return _build_item(
        uid=f"appointment:{appointment['id']}",
        id=appointment["id"],
        title=appointment.get("title") or "Appointment",
        type="appointment",
        source_type="appointment",
        source_id=appointment["id"],
        related_job_id=appointment.get("job_id"),
        related_customer_id=appointment.get("customer_id"),
        customer_name=customer.get("name"),
        status=status,
        priority="normal",
        start_datetime=_to_iso(start_dt),
        due_datetime=_to_iso(end_dt or start_dt),
        all_day=False,
        is_completed=is_completed,
        board_column=status,
        notes=appointment.get("description") or appointment.get("notes") or "",
        category=appointment.get("appointment_type") or "appointment",
        color="teal",
        source_route=None,
        source_reference=appointment.get("title"),
        source_label="Appointment",
        meta={"location": appointment.get("location")},
    )


def _item_in_date_range(item: ProductivityItem, start_dt: Optional[datetime], end_dt: Optional[datetime]) -> bool:
    if not start_dt and not end_dt:
        return True
    item_start = _parse_dt(item.start_datetime) or _parse_dt(item.due_datetime)
    item_end = _parse_dt(item.due_datetime) or item_start
    if not item_start and not item_end:
        return False
    compare_start = item_start or item_end
    compare_end = item_end or item_start
    if start_dt and compare_end and compare_end < start_dt:
        return False
    if end_dt and compare_start and compare_start > end_dt:
        return False
    return True


def _filter_items(items: Iterable[ProductivityItem], filters: Dict[str, Any]) -> List[ProductivityItem]:
    item_types = set(_split_csv(filters.get("item_types")))
    statuses = set(_split_csv(filters.get("statuses")))
    priorities = set(_split_csv(filters.get("priorities")))
    assigned_user_ids = set(_split_csv(filters.get("assigned_user_ids")))
    customer_ids = set(_split_csv(filters.get("customer_ids")))
    source_types = set(_split_csv(filters.get("source_types")))
    search = (filters.get("search") or "").strip().lower()
    include_completed = filters.get("include_completed", False)
    start_dt = _parse_dt(filters.get("start_date"))
    end_dt = _parse_dt(filters.get("end_date"))

    filtered: List[ProductivityItem] = []
    for item in items:
        if not include_completed and item.is_completed:
            continue
        if item_types and item.type not in item_types:
            continue
        if statuses and item.status not in statuses and item.board_column not in statuses:
            continue
        if priorities and item.priority not in priorities:
            continue
        if assigned_user_ids and (item.assigned_user_id or "") not in assigned_user_ids:
            continue
        if customer_ids and (item.related_customer_id or "") not in customer_ids:
            continue
        if source_types and item.source_type not in source_types:
            continue
        if not _item_in_date_range(item, start_dt, end_dt):
            continue
        if search:
            haystack = " ".join([
                item.title,
                item.notes,
                item.customer_name or "",
                item.source_reference or "",
                item.assigned_user_name or "",
                item.status,
                item.type,
                item.category,
            ]).lower()
            if search not in haystack:
                continue
        filtered.append(item)
    return filtered


async def get_unified_productivity_items(db, tenant_id: str, filters: Optional[Dict[str, Any]] = None) -> List[ProductivityItem]:
    maps = await _load_maps(db, tenant_id)
    filters = filters or {}
    items: List[ProductivityItem] = []

    tasks = await db.tasks.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(5000)
    items.extend(_map_task(task, maps) for task in tasks)

    orders = await db.orders.find({"tenant_id": tenant_id, "is_archived": {"$ne": True}}, {"_id": 0}).to_list(2000)
    items.extend(_map_order(order, maps) for order in orders)

    legacy_jobs = await db.jobs.find({"tenant_id": tenant_id, "is_archived": {"$ne": True}}, {"_id": 0}).to_list(2000)
    items.extend(_map_legacy_job(job, maps) for job in legacy_jobs)

    production_tasks = await db.production_tasks.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(5000)
    items.extend(_map_production_task(task, maps) for task in production_tasks)

    schedules = await db.employee_schedules.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(1000)
    for schedule_doc in schedules:
        week_start = _parse_dt(schedule_doc.get("week_start"))
        if not week_start:
            continue
        for offset, day_key in enumerate(["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
            shift = (schedule_doc.get("shifts") or {}).get(day_key)
            if not shift or not (shift.get("start") or shift.get("end")):
                continue
            day_date = (week_start + timedelta(days=offset)).date()
            items.append(_expand_schedule_shift(schedule_doc, day_key, shift, day_date, maps))

    appointments = await db.appointments.find({"tenant_id": tenant_id}, {"_id": 0}).to_list(1000)
    items.extend(_map_appointment(appointment, maps) for appointment in appointments)

    filtered = _filter_items(items, filters)
    filtered.sort(key=lambda item: (_parse_dt(item.start_datetime) or _parse_dt(item.due_datetime) or datetime.max.replace(tzinfo=timezone.utc), item.title.lower()))
    return filtered


def build_productivity_summary(items: List[ProductivityItem], current_user_id: Optional[str] = None) -> ProductivitySummary:
    today = datetime.now(timezone.utc).date()
    week_end = _start_of_week(today) + timedelta(days=6)
    by_type = Counter(item.type for item in items)
    by_board_column = Counter(item.board_column for item in items)
    due_today = 0
    overdue = 0
    waiting_on_approval = 0
    scheduled_this_week = 0
    my_assigned = 0
    completed_items = 0
    open_items = 0

    for item in items:
        due_dt = _parse_dt(item.due_datetime)
        if item.is_completed:
            completed_items += 1
        else:
            open_items += 1
        if due_dt and due_dt.date() == today and not item.is_completed:
            due_today += 1
        if due_dt and due_dt.date() < today and not item.is_completed:
            overdue += 1
        if item.status in {"pending", "awaiting_approval", "awaiting_quote", "awaiting_review"}:
            waiting_on_approval += 1
        start_dt = _parse_dt(item.start_datetime) or due_dt
        if start_dt and today <= start_dt.date() <= week_end:
            scheduled_this_week += 1
        if current_user_id and item.assigned_user_id == current_user_id and not item.is_completed:
            my_assigned += 1

    return ProductivitySummary(
        due_today=due_today,
        overdue=overdue,
        waiting_on_approval=waiting_on_approval,
        scheduled_this_week=scheduled_this_week,
        my_assigned=my_assigned,
        open_items=open_items,
        completed_items=completed_items,
        by_type=dict(by_type),
        by_board_column=dict(by_board_column),
    )
