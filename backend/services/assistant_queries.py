"""
Assistant Query Service (Phase 2 — Business Assistant Live Queries)

Typed, tenant-scoped, permission-aware query layer.

Each `query_*` function reads the same collections / status enums the rest of
the app uses, so the assistant's answers match what the user sees in the UI.

Uniform response shape:
{
  "query_type": "...",
  "summary": "...",
  "metrics": [{"label": "...", "value": ...}],
  "rows":    [{...}],
  "suggested_actions": [{"id", "label", "action", "target"}],
}
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone, date
from typing import Any, Dict, List, Optional, Tuple
import re


# ----------------------------------------------------------------------------
# Natural-date parsing
# ----------------------------------------------------------------------------

_WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}


def _today(now: Optional[datetime] = None) -> date:
    return (now or datetime.now(timezone.utc)).date()


def parse_date_phrase(phrase: Optional[str], now: Optional[datetime] = None) -> Tuple[Optional[date], Optional[date]]:
    """Return (start, end) inclusive dates for a natural-date phrase.

    Returns (None, None) if the phrase is unrecognized / empty.
    """
    if not phrase:
        return None, None
    p = phrase.strip().lower()
    today = _today(now)

    # Pure ISO date?
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", p)
    if m:
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        return d, d

    # "YYYY-MM-DD to YYYY-MM-DD"
    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\s+(?:to|through|\-)\s+(\d{4}-\d{2}-\d{2})", p)
    if m:
        return parse_date_phrase(m.group(1), now)[0], parse_date_phrase(m.group(2), now)[0]

    if p in ("today",):
        return today, today
    if p == "tomorrow":
        return today + timedelta(days=1), today + timedelta(days=1)
    if p == "yesterday":
        return today - timedelta(days=1), today - timedelta(days=1)

    if p in ("this week", "current week"):
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    if p == "last week":
        this_start = today - timedelta(days=today.weekday())
        last_start = this_start - timedelta(days=7)
        return last_start, last_start + timedelta(days=6)
    if p == "next week":
        this_start = today - timedelta(days=today.weekday())
        next_start = this_start + timedelta(days=7)
        return next_start, next_start + timedelta(days=6)

    if p in ("this month", "current month"):
        start = today.replace(day=1)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
        return start, end
    if p == "last month":
        first = today.replace(day=1)
        prev_end = first - timedelta(days=1)
        prev_start = prev_end.replace(day=1)
        return prev_start, prev_end

    if p in ("this quarter",):
        q_start_month = ((today.month - 1) // 3) * 3 + 1
        start = date(today.year, q_start_month, 1)
        end_month = q_start_month + 2
        next_q = date(today.year + (1 if end_month == 12 else 0), 1 if end_month == 12 else end_month + 1, 1)
        return start, next_q - timedelta(days=1)

    # Weekday names ("friday", "next friday")
    next_wd = p.startswith("next ")
    wd_name = p[5:] if next_wd else p
    if wd_name in _WEEKDAYS:
        target = _WEEKDAYS[wd_name]
        delta = (target - today.weekday()) % 7
        if delta == 0:
            delta = 7  # "friday" on a Friday → next Friday
        if next_wd:
            delta += 7  # "next friday" is always at least a week out
        d = today + timedelta(days=delta)
        return d, d

    return None, None


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _fmt_money(n: float) -> str:
    try:
        return f"${n:,.2f}"
    except Exception:
        return str(n)


def _sum(items: List[Dict], key: str) -> float:
    total = 0.0
    for item in items:
        try:
            total += float(item.get(key) or 0)
        except (TypeError, ValueError):
            continue
    return total


def _ok(**kwargs) -> Dict[str, Any]:
    """Default response skeleton."""
    return {
        "query_type": kwargs.get("query_type", "unknown"),
        "summary": kwargs.get("summary", ""),
        "metrics": kwargs.get("metrics", []),
        "rows": kwargs.get("rows", []),
        "suggested_actions": kwargs.get("suggested_actions", []),
        "filters_used": kwargs.get("filters_used", {}),
    }


def _forbidden(query_type: str, reason: str) -> Dict[str, Any]:
    return _ok(
        query_type=query_type,
        summary=f"You don't have permission to run this query. {reason}",
        metrics=[],
        rows=[],
        suggested_actions=[],
    )


# ----------------------------------------------------------------------------
# Live query implementations
# ----------------------------------------------------------------------------

async def query_overdue_invoices(db, tenant_id: str) -> Dict[str, Any]:
    """Invoices whose `due_date` has passed and are not fully paid.

    Uses the same logic the Invoices module exposes via status + amount_paid:
    an invoice is overdue if status is 'sent' or 'overdue' (or if due_date<today
    and amount_paid < grand_total), regardless of an automated status sweep.
    """
    today_iso = _today().isoformat()
    invoices = await db.invoices.find(
        {
            "tenant_id": tenant_id,
            "status": {"$nin": ["paid", "draft", "cancelled", "void"]},
        },
        {"_id": 0},
    ).to_list(500)

    overdue: List[Dict[str, Any]] = []
    total_outstanding = 0.0
    for inv in invoices:
        due = (inv.get("due_date") or "")[:10]
        if not due or due >= today_iso:
            continue
        grand_total = float(inv.get("grand_total") or inv.get("total") or 0)
        paid = float(inv.get("amount_paid") or 0)
        balance = round(grand_total - paid, 2)
        if balance <= 0:
            continue
        overdue.append({
            "invoice_id": inv.get("id"),
            "invoice_number": inv.get("invoice_number"),
            "customer_id": inv.get("customer_id"),
            "customer_name": inv.get("customer_name"),
            "due_date": due,
            "grand_total": round(grand_total, 2),
            "amount_paid": round(paid, 2),
            "balance_due": balance,
            "days_overdue": (date.fromisoformat(today_iso) - date.fromisoformat(due)).days,
        })
        total_outstanding += balance

    overdue.sort(key=lambda r: r["days_overdue"], reverse=True)

    if not overdue:
        return _ok(
            query_type="overdue_invoices",
            summary="You have no overdue invoices right now.",
            metrics=[{"label": "Overdue Invoices", "value": 0}],
        )

    return _ok(
        query_type="overdue_invoices",
        summary=f"You have {len(overdue)} overdue invoice{'s' if len(overdue) != 1 else ''} totaling {_fmt_money(total_outstanding)}.",
        metrics=[
            {"label": "Overdue Invoices", "value": len(overdue)},
            {"label": "Total Overdue", "value": round(total_outstanding, 2), "format": "currency"},
            {"label": "Oldest Days Overdue", "value": overdue[0]["days_overdue"]},
        ],
        rows=overdue[:25],
        suggested_actions=[
            {"id": "view_overdue_invoices", "label": "View Invoices", "action": "navigate", "target": "/invoices?status=overdue"},
            {"id": "send_reminders", "label": "Send Reminders", "action": "assistant_action", "target": "send_overdue_reminders"},
        ],
    )


async def query_ar_by_customer(db, tenant_id: str) -> Dict[str, Any]:
    """Accounts receivable aggregated by customer."""
    base = await query_overdue_invoices(db, tenant_id)
    by_customer: Dict[str, Dict[str, Any]] = {}
    for r in base.get("rows", []):
        cid = r.get("customer_id") or "_unknown"
        bucket = by_customer.setdefault(cid, {
            "customer_id": cid,
            "customer_name": r.get("customer_name") or "(unknown)",
            "open_invoices": 0,
            "balance_due": 0.0,
            "oldest_due_date": r.get("due_date"),
        })
        bucket["open_invoices"] += 1
        bucket["balance_due"] = round(bucket["balance_due"] + r.get("balance_due", 0), 2)
        if r.get("due_date") and (not bucket["oldest_due_date"] or r["due_date"] < bucket["oldest_due_date"]):
            bucket["oldest_due_date"] = r["due_date"]

    rows = sorted(by_customer.values(), key=lambda r: r["balance_due"], reverse=True)
    total = round(sum(r["balance_due"] for r in rows), 2)

    if not rows:
        return _ok(
            query_type="ar_by_customer",
            summary="No customers have outstanding balances right now.",
            metrics=[{"label": "Customers With Balances", "value": 0}],
        )

    top = rows[0]
    return _ok(
        query_type="ar_by_customer",
        summary=f"{len(rows)} customer{'s' if len(rows) != 1 else ''} owe {_fmt_money(total)}. Largest: {top['customer_name']} ({_fmt_money(top['balance_due'])}).",
        metrics=[
            {"label": "Customers", "value": len(rows)},
            {"label": "Total Outstanding", "value": total, "format": "currency"},
        ],
        rows=rows[:20],
        suggested_actions=[
            {"id": "view_invoices_overdue", "label": "View Invoices", "action": "navigate", "target": "/invoices?status=overdue"},
            {"id": "export_ar", "label": "Export Report", "action": "assistant_action", "target": "export_ar_report"},
        ],
    )


async def query_jobs_due(db, tenant_id: str, start: Optional[date], end: Optional[date]) -> Dict[str, Any]:
    """Orders whose `requested_due_date` falls in [start, end]."""
    if not start or not end:
        return _ok(
            query_type="jobs_due",
            summary="I need a date range. Did you mean today, tomorrow, this week, or a specific date?",
            suggested_actions=[],
        )
    start_iso, end_iso = start.isoformat(), end.isoformat()
    today_iso = _today().isoformat()
    orders = await db.orders.find(
        {
            "tenant_id": tenant_id,
            "requested_due_date": {"$gte": start_iso, "$lte": end_iso},
            "status": {"$nin": ["completed", "cancelled"]},
        },
        {"_id": 0},
    ).sort("requested_due_date", 1).to_list(200)

    rows = []
    for o in orders:
        due = (o.get("requested_due_date") or "")[:10]
        rows.append({
            "order_id": o.get("id"),
            "order_number": o.get("order_number"),
            "customer_name": o.get("customer_name"),
            "due_date": due,
            "status": o.get("status"),
            "order_total": float(o.get("order_total") or 0),
            "is_overdue": bool(due and due < today_iso),
        })

    overdue_count = sum(1 for r in rows if r["is_overdue"])
    if not rows:
        return _ok(
            query_type="jobs_due",
            summary=f"No open orders due between {start_iso} and {end_iso}.",
            metrics=[{"label": "Orders Due", "value": 0}],
            filters_used={"start": start_iso, "end": end_iso},
        )

    range_label = f"{start_iso}" if start == end else f"{start_iso} to {end_iso}"
    return _ok(
        query_type="jobs_due",
        summary=(
            f"{len(rows)} order{'s' if len(rows) != 1 else ''} due {range_label}"
            + (f" — {overdue_count} overdue." if overdue_count else ".")
        ),
        metrics=[
            {"label": "Orders Due", "value": len(rows)},
            {"label": "Overdue", "value": overdue_count},
            {"label": "Total Value", "value": round(sum(r["order_total"] for r in rows), 2), "format": "currency"},
        ],
        rows=rows,
        suggested_actions=[
            {"id": "open_schedule", "label": "Open Schedule", "action": "navigate", "target": "/schedule"},
            {"id": "open_orders", "label": "View Orders", "action": "navigate", "target": f"/orders?due_from={start_iso}&due_to={end_iso}"},
        ],
        filters_used={"start": start_iso, "end": end_iso},
    )


async def query_artwork_pending(db, tenant_id: str) -> Dict[str, Any]:
    """Job tickets whose status indicates they're waiting on artwork/proof/approval."""
    waiting_statuses = ["awaiting_proof", "awaiting_approval", "awaiting_info"]
    tickets = await db.job_tickets.find(
        {"tenant_id": tenant_id, "status": {"$in": waiting_statuses}},
        {"_id": 0},
    ).to_list(300)

    rows = []
    for t in tickets:
        rows.append({
            "ticket_id": t.get("id"),
            "ticket_number": t.get("ticket_number"),
            "order_id": t.get("order_id"),
            "item_name": t.get("item_name"),
            "status": t.get("status"),
            "customer_name": t.get("customer_name"),
            "updated_at": (t.get("updated_at") or "")[:19],
        })

    if not rows:
        return _ok(
            query_type="artwork_pending",
            summary="Nothing is waiting on artwork or approval right now.",
            metrics=[{"label": "Pending", "value": 0}],
        )

    by_status = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1

    return _ok(
        query_type="artwork_pending",
        summary=f"{len(rows)} item{'s' if len(rows) != 1 else ''} waiting on artwork or approval.",
        metrics=[
            {"label": "Awaiting Proof", "value": by_status.get("awaiting_proof", 0)},
            {"label": "Awaiting Approval", "value": by_status.get("awaiting_approval", 0)},
            {"label": "Awaiting Info", "value": by_status.get("awaiting_info", 0)},
        ],
        rows=rows[:25],
        suggested_actions=[
            {"id": "view_tickets_pending", "label": "View Tickets", "action": "navigate", "target": "/job-tickets?status=awaiting_proof"},
        ],
    )


async def query_employee_hours(
    db, tenant_id: str, start: Optional[date], end: Optional[date], employee_id: Optional[str] = None
) -> Dict[str, Any]:
    """Sum `hours` from `payroll_hours` per employee in range."""
    if not start or not end:
        return _ok(
            query_type="employee_hours",
            summary="Which date range should I use? (today, this week, last week, etc.)",
        )
    start_iso, end_iso = start.isoformat(), end.isoformat()

    # tenant-scope through employees list
    tenant_emp = await db.employees.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1, "first_name": 1, "last_name": 1}).to_list(500)
    tenant_emp_ids = [e["id"] for e in tenant_emp]
    name_by_id = {
        e["id"]: (e.get("name") or f"{e.get('first_name', '')} {e.get('last_name', '')}".strip() or e["id"])
        for e in tenant_emp
    }

    query = {
        "employee_id": {"$in": tenant_emp_ids},
        "date": {"$gte": start_iso, "$lte": end_iso},
    }
    if employee_id:
        query["employee_id"] = employee_id
    entries = await db.payroll_hours.find(query, {"_id": 0}).to_list(5000)

    totals: Dict[str, float] = {}
    entry_counts: Dict[str, int] = {}
    for e in entries:
        eid = e.get("employee_id")
        hrs = float(e.get("hours") or 0)
        totals[eid] = totals.get(eid, 0) + hrs
        entry_counts[eid] = entry_counts.get(eid, 0) + 1

    rows = sorted(
        [
            {
                "employee_id": eid,
                "employee_name": name_by_id.get(eid, eid),
                "total_hours": round(h, 2),
                "entries": entry_counts.get(eid, 0),
            }
            for eid, h in totals.items()
        ],
        key=lambda r: r["total_hours"],
        reverse=True,
    )

    if not rows:
        return _ok(
            query_type="employee_hours",
            summary=f"No time entries logged between {start_iso} and {end_iso}.",
            metrics=[{"label": "Hours Logged", "value": 0}],
            filters_used={"start": start_iso, "end": end_iso, "employee_id": employee_id},
        )

    total = round(sum(r["total_hours"] for r in rows), 2)
    top = rows[0]
    return _ok(
        query_type="employee_hours",
        summary=f"{total} hrs logged {start_iso}→{end_iso}. Top: {top['employee_name']} ({top['total_hours']} hrs).",
        metrics=[
            {"label": "Total Hours", "value": total},
            {"label": "Employees", "value": len(rows)},
        ],
        rows=rows,
        suggested_actions=[
            {"id": "open_payroll", "label": "Open Payroll", "action": "navigate", "target": "/payroll"},
            {"id": "open_timeclock", "label": "Time Clock", "action": "navigate", "target": "/time-clock"},
        ],
        filters_used={"start": start_iso, "end": end_iso, "employee_id": employee_id},
    )


async def query_production_load(db, tenant_id: str, start: Optional[date], end: Optional[date]) -> Dict[str, Any]:
    """Active production workload for a day or range."""
    if not start:
        start = _today()
    if not end:
        end = start
    start_iso, end_iso = start.isoformat(), end.isoformat()

    # Active tickets with a due_date in range OR already in production
    tickets = await db.job_tickets.find(
        {
            "tenant_id": tenant_id,
            "status": {"$nin": ["completed", "cancelled"]},
            "$or": [
                {"due_date": {"$gte": start_iso, "$lte": end_iso}},
                {"status": "in_production"},
            ],
        },
        {"_id": 0},
    ).to_list(500)

    rows = []
    by_stage: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    unassigned = 0
    for t in tickets:
        stage = t.get("status") or "unknown"
        cat = t.get("item_category") or "custom"
        by_stage[stage] = by_stage.get(stage, 0) + 1
        by_category[cat] = by_category.get(cat, 0) + 1
        if not t.get("assigned_to"):
            unassigned += 1
        rows.append({
            "ticket_id": t.get("id"),
            "ticket_number": t.get("ticket_number"),
            "order_id": t.get("order_id"),
            "item_name": t.get("item_name"),
            "category": cat,
            "status": stage,
            "due_date": (t.get("due_date") or "")[:10],
            "assigned_to": t.get("assigned_to"),
            "quantity": t.get("quantity", 1),
        })

    range_label = start_iso if start == end else f"{start_iso} → {end_iso}"
    if not rows:
        return _ok(
            query_type="production_load",
            summary=f"Production queue is clear for {range_label}.",
            metrics=[{"label": "Active Items", "value": 0}],
        )
    return _ok(
        query_type="production_load",
        summary=f"{len(rows)} active production item{'s' if len(rows) != 1 else ''} for {range_label}.",
        metrics=[
            {"label": "Total Items", "value": len(rows)},
            {"label": "Unassigned", "value": unassigned},
            {"label": "In Production", "value": by_stage.get("in_production", 0)},
        ],
        rows=rows[:50],
        suggested_actions=[
            {"id": "open_production", "label": "Open Production Board", "action": "navigate", "target": "/production"},
            {"id": "open_schedule", "label": "Open Schedule", "action": "navigate", "target": "/schedule"},
        ],
        filters_used={"start": start_iso, "end": end_iso, "by_stage": by_stage, "by_category": by_category},
    )


async def query_jobs_in_production(db, tenant_id: str) -> Dict[str, Any]:
    """What's actively being produced right now (status == in_production)."""
    tickets = await db.job_tickets.find(
        {"tenant_id": tenant_id, "status": "in_production"},
        {"_id": 0},
    ).to_list(300)
    rows = [
        {
            "ticket_id": t.get("id"),
            "ticket_number": t.get("ticket_number"),
            "order_id": t.get("order_id"),
            "item_name": t.get("item_name"),
            "category": t.get("item_category"),
            "due_date": (t.get("due_date") or "")[:10],
            "assigned_to": t.get("assigned_to"),
        }
        for t in tickets
    ]
    if not rows:
        return _ok(
            query_type="jobs_in_production",
            summary="Nothing is actively in production right now.",
            metrics=[{"label": "In Production", "value": 0}],
        )
    return _ok(
        query_type="jobs_in_production",
        summary=f"{len(rows)} item{'s' if len(rows) != 1 else ''} in production.",
        metrics=[{"label": "In Production", "value": len(rows)}],
        rows=rows[:50],
        suggested_actions=[
            {"id": "open_production", "label": "Open Production Board", "action": "navigate", "target": "/production"},
        ],
    )


async def _revenue_for_range(db, tenant_id: str, start: date, end: date) -> Tuple[float, int, Dict[str, float]]:
    """Revenue for a date range = paid invoice `amount_paid` where invoice is
    within range. Returns (total, invoice_count, by_source)."""
    start_iso, end_iso = start.isoformat(), end.isoformat()
    # We key on created_at for simplicity; matches dashboard revenue logic.
    invoices = await db.invoices.find(
        {
            "tenant_id": tenant_id,
            "status": "paid",
            "created_at": {"$gte": start_iso, "$lte": end_iso + "T23:59:59Z"},
        },
        {"_id": 0, "grand_total": 1, "total": 1, "amount_paid": 1, "source": 1},
    ).to_list(2000)

    total = 0.0
    by_source: Dict[str, float] = {}
    for inv in invoices:
        amt = float(inv.get("amount_paid") or inv.get("grand_total") or inv.get("total") or 0)
        total += amt
        src = (inv.get("source") or "invoice").lower()
        by_source[src] = by_source.get(src, 0) + amt
    return round(total, 2), len(invoices), {k: round(v, 2) for k, v in by_source.items()}


async def query_revenue(
    db, tenant_id: str, start: Optional[date], end: Optional[date], comparison: Optional[str] = None
) -> Dict[str, Any]:
    """Total paid revenue for a date range, optionally compared to a prior period."""
    if not start or not end:
        return _ok(
            query_type="revenue",
            summary="Which period should I measure? (this week / last month / a specific date range)",
        )
    total, count, _by_source = await _revenue_for_range(db, tenant_id, start, end)

    metrics = [
        {"label": "Revenue", "value": total, "format": "currency"},
        {"label": "Paid Invoices", "value": count},
    ]
    summary = f"Revenue from {start.isoformat()} to {end.isoformat()}: {_fmt_money(total)} across {count} paid invoice{'s' if count != 1 else ''}."

    # Optional comparison vs prior equivalent period.
    if comparison:
        days = (end - start).days + 1
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - timedelta(days=days - 1)
        comp_total, comp_count, _ = await _revenue_for_range(db, tenant_id, comp_start, comp_end)
        diff = total - comp_total
        pct = (diff / comp_total * 100) if comp_total > 0 else None
        metrics.append({"label": f"Prev {days}d", "value": comp_total, "format": "currency"})
        if pct is not None:
            metrics.append({"label": "Change", "value": round(pct, 1), "format": "percent"})
        summary += f" vs {_fmt_money(comp_total)} in the prior {days} days"
        if pct is not None:
            summary += f" ({'+' if pct >= 0 else ''}{round(pct, 1)}%)."
        else:
            summary += "."

    return _ok(
        query_type="revenue",
        summary=summary,
        metrics=metrics,
        suggested_actions=[
            {"id": "open_financials", "label": "Open Financials", "action": "navigate", "target": "/financials"},
        ],
        filters_used={"start": start.isoformat(), "end": end.isoformat(), "comparison": comparison},
    )


async def query_revenue_by_source(db, tenant_id: str, start: Optional[date], end: Optional[date]) -> Dict[str, Any]:
    """Break revenue out by `invoice.source` (webstore, invoice, stripe, etc.)."""
    if not start or not end:
        return _ok(
            query_type="revenue_by_source",
            summary="Which period should I analyze?",
        )
    total, _count, by_source = await _revenue_for_range(db, tenant_id, start, end)
    rows = sorted(
        [{"source": k, "amount": v, "pct": round((v / total * 100), 1) if total else 0} for k, v in by_source.items()],
        key=lambda r: r["amount"],
        reverse=True,
    )
    if not rows:
        return _ok(
            query_type="revenue_by_source",
            summary=f"No paid revenue between {start.isoformat()} and {end.isoformat()}.",
            metrics=[{"label": "Revenue", "value": 0, "format": "currency"}],
            filters_used={"start": start.isoformat(), "end": end.isoformat(), "note": "Source = invoice.source field (webstore/invoice/stripe)"},
        )
    top = rows[0]
    return _ok(
        query_type="revenue_by_source",
        summary=f"{_fmt_money(total)} paid. Biggest source: {top['source']} ({_fmt_money(top['amount'])}, {top['pct']}%).",
        metrics=[
            {"label": "Total Revenue", "value": total, "format": "currency"},
            {"label": "Sources", "value": len(rows)},
        ],
        rows=rows,
        suggested_actions=[
            {"id": "open_financials", "label": "Open Financials", "action": "navigate", "target": "/financials"},
            {"id": "open_webstores", "label": "Open Webstores", "action": "navigate", "target": "/webstores"},
        ],
        filters_used={"start": start.isoformat(), "end": end.isoformat(), "note": "Source = invoice.source field"},
    )


async def query_top_categories(db, tenant_id: str, start: Optional[date], end: Optional[date]) -> Dict[str, Any]:
    """Top-selling job-ticket categories in a period (by ticket count + estimated revenue)."""
    if not start or not end:
        return _ok(query_type="top_categories", summary="Which period should I analyze?")
    start_iso, end_iso = start.isoformat(), end.isoformat()
    tickets = await db.job_tickets.find(
        {
            "tenant_id": tenant_id,
            "created_at": {"$gte": start_iso, "$lte": end_iso + "T23:59:59Z"},
        },
        {"_id": 0, "item_category": 1, "estimated_price": 1, "quantity": 1},
    ).to_list(5000)

    by_cat: Dict[str, Dict[str, float]] = {}
    for t in tickets:
        cat = t.get("item_category") or "uncategorized"
        bucket = by_cat.setdefault(cat, {"category": cat, "count": 0, "revenue": 0.0})
        bucket["count"] += 1
        bucket["revenue"] += float(t.get("estimated_price") or 0)

    rows = sorted(by_cat.values(), key=lambda r: r["revenue"], reverse=True)
    for r in rows:
        r["revenue"] = round(r["revenue"], 2)

    if not rows:
        return _ok(
            query_type="top_categories",
            summary=f"No items created between {start.isoformat()} and {end.isoformat()}.",
            metrics=[{"label": "Categories", "value": 0}],
        )
    top = rows[0]
    return _ok(
        query_type="top_categories",
        summary=f"Top category in {start.isoformat()}→{end.isoformat()}: {top['category']} ({top['count']} items, {_fmt_money(top['revenue'])}).",
        metrics=[
            {"label": "Categories", "value": len(rows)},
            {"label": "Total Items", "value": sum(r["count"] for r in rows)},
            {"label": "Total Estimated Revenue", "value": round(sum(r["revenue"] for r in rows), 2), "format": "currency"},
        ],
        rows=rows[:10],
        suggested_actions=[
            {"id": "open_reports", "label": "Open Reports", "action": "navigate", "target": "/reports"},
        ],
        filters_used={"start": start.isoformat(), "end": end.isoformat()},
    )


# ----------------------------------------------------------------------------
# Dispatcher — maps a QueryRequest to the right backend call.
# Callers should enforce permission checks BEFORE invoking this dispatcher.
# ----------------------------------------------------------------------------

async def run_query(db, tenant_id: str, query_type: str, filters: Dict[str, Any]) -> Dict[str, Any]:
    f = filters or {}
    date_phrase = f.get("date_phrase") or f.get("range")
    start, end = parse_date_phrase(date_phrase) if date_phrase else (None, None)
    if f.get("start_date"):
        start, _ = parse_date_phrase(f["start_date"])
    if f.get("end_date"):
        end, _ = parse_date_phrase(f["end_date"])
    if start and not end:
        end = start

    if query_type == "overdue_invoices":
        return await query_overdue_invoices(db, tenant_id)
    if query_type == "ar_by_customer":
        return await query_ar_by_customer(db, tenant_id)
    if query_type == "jobs_due":
        return await query_jobs_due(db, tenant_id, start, end)
    if query_type == "artwork_pending":
        return await query_artwork_pending(db, tenant_id)
    if query_type == "employee_hours":
        return await query_employee_hours(db, tenant_id, start, end, employee_id=f.get("employee_id"))
    if query_type == "production_load":
        return await query_production_load(db, tenant_id, start, end)
    if query_type == "revenue":
        return await query_revenue(db, tenant_id, start, end, comparison=f.get("comparison"))
    if query_type == "revenue_by_source":
        return await query_revenue_by_source(db, tenant_id, start, end)
    if query_type == "top_categories":
        return await query_top_categories(db, tenant_id, start, end)
    if query_type == "jobs_in_production":
        return await query_jobs_in_production(db, tenant_id)

    return _ok(
        query_type=query_type,
        summary=f"I don't have a live-data query for '{query_type}' yet.",
    )


# Permission map: query_type → Permission required to run it
from models.auth import Permission  # noqa: E402

QUERY_PERMISSIONS: Dict[str, Permission] = {
    "overdue_invoices": Permission.INVOICES_VIEW,
    "ar_by_customer": Permission.INVOICES_VIEW,
    "jobs_due": Permission.JOBS_VIEW,
    "artwork_pending": Permission.JOBS_VIEW,
    "employee_hours": Permission.TIME_CLOCK_VIEW_ALL,
    "production_load": Permission.JOBS_VIEW,
    "jobs_in_production": Permission.JOBS_VIEW,
    "revenue": Permission.FINANCIALS_VIEW,
    "revenue_by_source": Permission.FINANCIALS_VIEW,
    "top_categories": Permission.FINANCIALS_VIEW,
}
