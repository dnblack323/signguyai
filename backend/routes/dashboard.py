"""
Dashboard Routes

Phase 1 fixes (active contracts):
- GET /api/dashboard/stats: active_jobs/active_orders now from db.orders (not legacy db.jobs)
- GET /api/dashboard/stats: pending_invoices excludes "draft" (only sent/overdue = actionable)
- GET /api/dashboard/stats: today_revenue uses date-prefix regex for robust mixed-format handling

New V1 endpoints added in Phase 1:
- GET /api/dashboard/summary-v2
- GET /api/dashboard/today-command-center
- GET /api/dashboard/production-snapshot
- GET /api/dashboard/customer-attention
- GET /api/dashboard/financial-attention

Phase 5 cleanup (2026-05-23):
- Removed deprecated GET /api/dashboard/todays-schedule (legacy db.jobs source)
- Removed deprecated GET /api/dashboard/clocked-in (superseded by /dashboard/team-status-today)
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from server import db, get_current_active_user
from models import UserInDB


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# Active pipeline statuses for the new Order system
_ACTIVE_ORDER_STATUSES = [
    "new_intake", "awaiting_review", "awaiting_quote", "quote_sent",
    "awaiting_approval", "approved", "in_production", "partially_complete",
    "ready_for_pickup", "out_for_delivery", "on_hold",
]

# Active (non-terminal) job ticket statuses
_ACTIVE_TICKET_STATUSES = [
    "new", "awaiting_info", "awaiting_proof", "awaiting_approval",
    "approved", "queued", "in_production", "in_qc", "on_hold", "ready", "rework",
]

# Map ticket status → production stage label
_TICKET_STAGE_MAP: Dict[str, str] = {
    "new": "queued", "awaiting_info": "queued", "awaiting_proof": "queued",
    "awaiting_approval": "queued", "approved": "queued", "queued": "queued",
    "on_hold": "queued",
    "in_production": "printing",
    "in_qc": "finishing", "rework": "finishing",
    "ready": "install",
    "completed": "complete", "cancelled": "complete",
}

_ALL_STAGES = ["queued", "printing", "finishing", "install", "complete"]


def _severity(count: int, amber_at: int, red_at: int) -> str:
    """Return neutral/amber/red severity label."""
    if count == 0:
        return "neutral"
    if count < red_at:
        return "amber"
    return "red"


def _age_hours(ts: Optional[str]) -> float:
    """Return age in fractional hours from an ISO timestamp string."""
    if not ts:
        return 0.0
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600)
    except Exception:
        return 0.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _team_status_data(tenant_id: str) -> Dict[str, Any]:
    """Shared helper — returns the same payload as GET /dashboard/team-status-today."""
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()
    day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    day_key = day_keys[today.weekday()]
    days_since_monday = today.weekday()
    week_start = (today - timedelta(days=days_since_monday)).isoformat()

    employees = await db.employees.find(
        {"tenant_id": tenant_id, "is_active": True}, {"_id": 0}
    ).to_list(200)

    schedules = await db.employee_schedules.find(
        {"tenant_id": tenant_id, "week_start": week_start}, {"_id": 0}
    ).to_list(200)

    schedule_map: Dict[str, Dict] = {}
    for sched in schedules:
        emp_id = sched.get("employee_id")
        today_shift = (sched.get("shifts") or {}).get(day_key)
        if today_shift and (today_shift.get("start") or today_shift.get("end")):
            schedule_map[emp_id] = today_shift

    open_shifts_cursor = db.timeclock_shifts.find(
        {"tenant_id": tenant_id, "status": {"$in": ["working", "on_break"]}}, {"_id": 0}
    )
    open_shifts_by_emp = {s["employee_id"]: s async for s in open_shifts_cursor}

    team_status = []
    for emp in employees:
        emp_id = emp.get("id", "")
        is_scheduled = emp_id in schedule_map
        shift_info = schedule_map.get(emp_id, {})
        open_shift = open_shifts_by_emp.get(emp_id)
        clock_status = "not_clocked_in"
        clocked_in_at = None
        if open_shift:
            clock_status = "on_break" if open_shift.get("status") == "on_break" else "working"
            clocked_in_at = open_shift.get("clock_in")
        else:
            finished = await db.timeclock_shifts.find_one(
                {"tenant_id": tenant_id, "employee_id": emp_id, "status": "finished", "date": today_str},
                {"_id": 0, "clock_in": 1},
            )
            if finished:
                clock_status = "finished"
                clocked_in_at = finished.get("clock_in")

        team_status.append({
            "employee_id": emp_id,
            "employee_name": emp.get("name", "Unknown"),
            "is_scheduled": is_scheduled,
            "shift_start": shift_info.get("start", ""),
            "shift_end": shift_info.get("end", ""),
            "clock_status": clock_status,
            "clocked_in_at": clocked_in_at,
        })

    team_status.sort(key=lambda x: (not x["is_scheduled"], x["employee_name"]))
    scheduled_count = sum(1 for t in team_status if t["is_scheduled"])
    clocked_in_count = sum(1 for t in team_status if t["clock_status"] in ["working", "on_break"])
    return {
        "scheduled_count": scheduled_count,
        "clocked_in_count": clocked_in_count,
        "employees": team_status,
    }


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ============================================================
# Pydantic models — existing (keep for backward compat)
# ============================================================

class DashboardStats(BaseModel):
    total_customers: int = 0
    active_jobs: int = 0        # Backward-compat field — now populated from db.orders
    active_orders: int = 0      # Phase 1 addition — explicit Orders count
    pending_invoices: int = 0
    today_revenue: float = 0
    overdue_count: int = 0
    overdue_total: float = 0


class PendingApproval(BaseModel):
    id: str
    job_id: str
    job_name: str
    customer_name: str
    created_at: str
    status: str


class UnreadMessage(BaseModel):
    conversation_id: str
    customer_id: str
    customer_name: str
    last_message: str
    last_message_at: str
    unread_count: int


class OnboardingStatus(BaseModel):
    """Status of onboarding checklist items"""
    has_company_info: bool = False
    has_pricing_config: bool = False
    has_email_templates: bool = False
    has_customers: bool = False
    has_imported_customers: bool = False
    has_employees: bool = False
    has_quotes: bool = False
    has_webstores: bool = False
    has_documents: bool = False
    has_used_ai: bool = False


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: UserInDB = Depends(get_current_active_user)):
    """Get main dashboard statistics.

    Phase 1 fixes:
    - active_jobs/active_orders now from db.orders (not legacy db.jobs)
    - pending_invoices excludes 'draft' — only sent/overdue are actionable
    - today_revenue uses date-prefix regex for robust mixed ISO/date string handling
    """
    tenant_id = current_user.tenant_id

    # Total customers
    total_customers = await db.customers.count_documents({"tenant_id": tenant_id})

    # FIXED: Active orders from db.orders (new 4-layer system), not legacy db.jobs
    active_orders = await db.orders.count_documents({
        "tenant_id": tenant_id,
        "status": {"$in": _ACTIVE_ORDER_STATUSES},
        "is_archived": {"$ne": True},
    })

    # FIXED: Pending invoices — exclude draft; only actionable sent/overdue states
    pending_invoices = await db.invoices.count_documents({
        "tenant_id": tenant_id,
        "status": {"$in": ["sent", "overdue"]},
    })

    # FIXED: Today's revenue — regex prefix handles both "2026-02-20" and "2026-02-20T12:00:00Z"
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_invoices = await db.invoices.find(
        {"tenant_id": tenant_id, "status": "paid", "paid_date": {"$regex": f"^{today_str}"}},
        {"_id": 0, "total": 1},
    ).to_list(1000)
    today_revenue = sum(inv.get("total", 0) for inv in today_invoices)

    # Overdue invoices
    overdue_invoices = await db.invoices.find(
        {"tenant_id": tenant_id, "status": "overdue"},
        {"_id": 0, "total": 1},
    ).to_list(1000)
    overdue_count = len(overdue_invoices)
    overdue_total = sum(inv.get("total", 0) for inv in overdue_invoices)

    return DashboardStats(
        total_customers=total_customers,
        active_jobs=active_orders,       # backward-compat key, same value
        active_orders=active_orders,
        pending_invoices=pending_invoices,
        today_revenue=today_revenue,
        overdue_count=overdue_count,
        overdue_total=overdue_total,
    )


@router.get("/pending-approvals", response_model=List[PendingApproval])
async def get_pending_approvals(current_user: UserInDB = Depends(get_current_active_user)):
    """Get proofs awaiting customer approval"""
    tenant_id = current_user.tenant_id
    
    # Find proofs with pending status
    pending_proofs = await db.artwork_proofs.find({
        "tenant_id": tenant_id,
        "status": "pending"
    }, {"_id": 0}).sort("created_at", -1).to_list(20)
    
    approvals = []
    for proof in pending_proofs:
        # Get job info (tenant-filtered for extra safety)
        job = await db.jobs.find_one(
            {"id": proof.get("job_id"), "tenant_id": tenant_id}, 
            {"_id": 0, "name": 1, "customer_id": 1}
        )
        if not job:
            continue
            
        # Get customer name (tenant-filtered for extra safety)
        customer = await db.customers.find_one(
            {"id": job.get("customer_id"), "tenant_id": tenant_id}, 
            {"_id": 0, "name": 1}
        )
        customer_name = customer.get("name", "Unknown") if customer else "Unknown"
        
        approvals.append(PendingApproval(
            id=proof.get("id", ""),
            job_id=proof.get("job_id", ""),
            job_name=job.get("name", "Unknown Job"),
            customer_name=customer_name,
            created_at=proof.get("created_at", ""),
            status=proof.get("status", "pending")
        ))
    
    return approvals


@router.get("/unread-messages", response_model=List[UnreadMessage])
async def get_unread_messages(current_user: UserInDB = Depends(get_current_active_user)):
    """Get conversations with unread messages from customers"""
    tenant_id = current_user.tenant_id
    
    # Find conversations with unread messages (messages from customer not read by shop)
    conversations = await db.conversations.find({
        "tenant_id": tenant_id,
        "shop_unread_count": {"$gt": 0}
    }, {"_id": 0}).sort("last_message_at", -1).to_list(10)
    
    messages = []
    for conv in conversations:
        # Get customer name (tenant-filtered for extra safety)
        customer = await db.customers.find_one(
            {"id": conv.get("customer_id"), "tenant_id": tenant_id}, 
            {"_id": 0, "name": 1}
        )
        customer_name = customer.get("name", "Unknown") if customer else "Unknown"
        
        messages.append(UnreadMessage(
            conversation_id=conv.get("id", ""),
            customer_id=conv.get("customer_id", ""),
            customer_name=customer_name,
            last_message=conv.get("last_message", "")[:100],  # Truncate
            last_message_at=conv.get("last_message_at", ""),
            unread_count=conv.get("shop_unread_count", 0)
        ))
    
    return messages


@router.get("/onboarding-status", response_model=OnboardingStatus)
async def get_onboarding_status(current_user: UserInDB = Depends(get_current_active_user)):
    """Get the status of onboarding checklist items for the current tenant"""
    tenant_id = current_user.tenant_id
    
    # Check for customers
    customer_count = await db.customers.count_documents({"tenant_id": tenant_id})
    has_customers = customer_count > 0
    
    # Check if any customers were imported (look for imported_at field or bulk creation)
    imported_count = await db.customers.count_documents({
        "tenant_id": tenant_id,
        "$or": [
            {"imported_at": {"$exists": True}},
            {"source": "import"}
        ]
    })
    has_imported_customers = imported_count > 0
    
    # Check for employees
    employee_count = await db.employees.count_documents({"tenant_id": tenant_id})
    has_employees = employee_count > 0
    
    # Check for quotes
    quote_count = await db.quotes.count_documents({"tenant_id": tenant_id})
    has_quotes = quote_count > 0
    
    # Check company info - look for customized settings
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    has_company_info = False
    if tenant:
        # Check if company name has been customized (not default)
        company_name = tenant.get("company_name", "")
        default_names = ["My Sign Shop", "New Sign Shop", "", None]
        has_company_info = company_name not in default_names
    
    # Check pricing configuration
    pricing_config = await db.pricing_configuration.find_one({"tenant_id": tenant_id})
    has_pricing_config = pricing_config is not None
    
    # Check email templates - see if any have been customized
    custom_templates = await db.email_templates.count_documents({
        "tenant_id": tenant_id,
        "is_default": False
    })
    has_email_templates = custom_templates > 0
    
    # Check for webstores
    webstore_count = await db.webstores_v2.count_documents({"tenant_id": tenant_id})
    has_webstores = webstore_count > 0
    
    # Check for documents
    document_count = await db.documents.count_documents({"tenant_id": tenant_id})
    has_documents = document_count > 0
    
    # Check AI usage - look for AI-generated content or logs
    ai_usage = await db.ai_usage_logs.count_documents({"tenant_id": tenant_id})
    has_used_ai = ai_usage > 0
    
    return OnboardingStatus(
        has_company_info=has_company_info,
        has_pricing_config=has_pricing_config,
        has_email_templates=has_email_templates,
        has_customers=has_customers,
        has_imported_customers=has_imported_customers,
        has_employees=has_employees,
        has_quotes=has_quotes,
        has_webstores=has_webstores,
        has_documents=has_documents,
        has_used_ai=has_used_ai
    )



@router.get("/team-status-today")
async def get_team_status_today(current_user: UserInDB = Depends(get_current_active_user)):
    """Get combined team status: who is scheduled today and their clock-in status"""
    tenant_id = current_user.tenant_id
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()

    # Determine which day-of-week key to look up in shifts
    day_keys = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    day_key = day_keys[today.weekday()]

    # Get the week_start (Monday) for today
    days_since_monday = today.weekday()
    week_start = (today - timedelta(days=days_since_monday)).isoformat()

    # Fetch all active employees for this tenant
    employees = await db.employees.find(
        {"tenant_id": tenant_id, "is_active": True},
        {"_id": 0}
    ).to_list(200)

    # Fetch schedules for this week
    schedules = await db.employee_schedules.find(
        {"tenant_id": tenant_id, "week_start": week_start},
        {"_id": 0}
    ).to_list(200)

    # Build a map: employee_id -> shift for today
    schedule_map = {}
    for sched in schedules:
        emp_id = sched.get("employee_id")
        shifts = sched.get("shifts", {})
        today_shift = shifts.get(day_key)
        if today_shift and (today_shift.get("start") or today_shift.get("end")):
            schedule_map[emp_id] = today_shift

    # Check clock status for each employee.
    #
    # Previously this queried `timelogs` with a regex `^YYYY-MM-DD` against the
    # UTC timestamp. That silently dropped anyone whose shift crossed a UTC day
    # boundary (common for evening employees in US timezones) — so the Dashboard
    # widget would show "nobody clocked in" while the portal clearly showed them
    # working. We now use `timeclock_shifts` (the canonical store) and look for
    # ANY open shift (status ∈ working|on_break) regardless of date.
    open_shifts_cursor = db.timeclock_shifts.find(
        {"tenant_id": tenant_id, "status": {"$in": ["working", "on_break"]}},
        {"_id": 0}
    )
    open_shifts_by_emp = {s["employee_id"]: s async for s in open_shifts_cursor}

    team_status = []
    for emp in employees:
        emp_id = emp.get("id", "")
        is_scheduled = emp_id in schedule_map
        shift_info = schedule_map.get(emp_id, {})

        open_shift = open_shifts_by_emp.get(emp_id)
        clock_status = "not_clocked_in"
        clocked_in_at = None
        if open_shift:
            # Canonical: an open shift ⇒ currently working or on break.
            clock_status = "on_break" if open_shift.get("status") == "on_break" else "working"
            clocked_in_at = open_shift.get("clock_in")
        else:
            # Secondary: did they have a shift that finished today (local UTC)?
            finished_today = await db.timeclock_shifts.find_one(
                {
                    "tenant_id": tenant_id,
                    "employee_id": emp_id,
                    "status": "finished",
                    "date": today_str,
                },
                {"_id": 0, "clock_in": 1, "clock_out": 1},
            )
            if finished_today:
                clock_status = "finished"
                clocked_in_at = finished_today.get("clock_in")

        entry = {
            "employee_id": emp_id,
            "employee_name": emp.get("name", "Unknown"),
            "is_scheduled": is_scheduled,
            "shift_start": shift_info.get("start", ""),
            "shift_end": shift_info.get("end", ""),
            "clock_status": clock_status,
            "clocked_in_at": clocked_in_at,
        }
        team_status.append(entry)

    # Sort: scheduled first, then by name
    team_status.sort(key=lambda x: (not x["is_scheduled"], x["employee_name"]))

    scheduled_count = sum(1 for t in team_status if t["is_scheduled"])
    clocked_in_count = sum(1 for t in team_status if t["clock_status"] in ["working", "on_break"])

    return {
        "date": today_str,
        "day_of_week": day_key,
        "scheduled_count": scheduled_count,
        "clocked_in_count": clocked_in_count,
        "total_employees": len(team_status),
        "employees": team_status
    }


@router.get("/recent-ai-documents")
async def get_recent_ai_documents(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get the 5 most recent AI-generated documents"""
    # Find documents with ai-generated tag
    recent_docs = await db.documents.find(
        {
            "tenant_id": current_user.tenant_id,
            "tags": "ai-generated",
            "status": "active"
        },
        {"_id": 0, "file_data": 0}  # Exclude file_data for efficiency
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return recent_docs


# ============================================================
# Phase 1 V1 — New command-center endpoints
# ============================================================

@router.get("/summary-v2")
async def get_summary_v2(current_user: UserInDB = Depends(get_current_active_user)):
    """Aggregated severity metrics for the manager command-center header bar.

    Each metric includes a count and a severity label (neutral/amber/red)
    so the frontend can render urgency indicators without extra logic.
    """
    tenant_id = current_user.tenant_id
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # due_today — job tickets whose due_date == today (active only)
    due_today_count = await db.job_tickets.count_documents({
        "tenant_id": tenant_id,
        "due_date": today_str,
        "status": {"$in": _ACTIVE_TICKET_STATUSES},
    })

    # overdue — tickets past due date (not complete/cancelled)
    overdue_tickets = await db.job_tickets.count_documents({
        "tenant_id": tenant_id,
        "due_date": {"$lt": today_str},
        "status": {"$in": _ACTIVE_TICKET_STATUSES},
    })

    # awaiting_approval — pending proofs + pending signatures
    pending_proofs = await db.artwork_proofs.count_documents({
        "tenant_id": tenant_id, "status": "pending",
    })
    pending_sigs = await db.signatures.count_documents({
        "tenant_id": tenant_id, "status": "pending",
    })
    awaiting_approval_count = pending_proofs + pending_sigs

    # unread_messages — conversations with unread count > 0
    unread_msg_count = await db.conversations.count_documents({
        "tenant_id": tenant_id, "shop_unread_count": {"$gt": 0},
    })

    # in_production — tickets currently in in_production stage
    in_production_count = await db.job_tickets.count_documents({
        "tenant_id": tenant_id, "status": "in_production",
    })

    # unpaid_invoices — sent/overdue invoices (actionable)
    unpaid_count = await db.invoices.count_documents({
        "tenant_id": tenant_id, "status": {"$in": ["sent", "overdue"]},
    })

    return {
        "last_updated_at": _now_iso(),
        "metrics": {
            "due_today": {
                "count": due_today_count,
                "severity": _severity(due_today_count, amber_at=1, red_at=4),
            },
            "overdue": {
                "count": overdue_tickets,
                "severity": _severity(overdue_tickets, amber_at=1, red_at=3),
            },
            "awaiting_approval": {
                "count": awaiting_approval_count,
                "severity": _severity(awaiting_approval_count, amber_at=1, red_at=4),
            },
            "unread_messages": {
                "count": unread_msg_count,
                "severity": _severity(unread_msg_count, amber_at=1, red_at=5),
            },
            "in_production": {
                "count": in_production_count,
                "severity": _severity(in_production_count, amber_at=1, red_at=10),
            },
            "unpaid_invoices": {
                "count": unpaid_count,
                "severity": _severity(unpaid_count, amber_at=1, red_at=5),
            },
        },
    }


@router.get("/today-command-center")
async def get_today_command_center(current_user: UserInDB = Depends(get_current_active_user)):
    """Today's operational picture: due order items, appointments/installs, team status.

    Data sources:
    - due_order_items_today: db.job_tickets (due_date == today) + db.orders + db.customers
    - appointments_installs_today: db.appointments (scheduled_at starts today) + db.customers
    - team_status_today: db.employee_schedules + db.timeclock_shifts (reuses team-status-today logic)
    """
    tenant_id = current_user.tenant_id
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # --- batch load lookups ---
    customers_raw = await db.customers.find(
        {"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(5000)
    customer_map = {c["id"]: c["name"] for c in customers_raw}

    orders_raw = await db.orders.find(
        {"tenant_id": tenant_id}, {"_id": 0, "id": 1, "order_number": 1, "customer_id": 1, "customer_name": 1}
    ).to_list(2000)
    order_map = {o["id"]: o for o in orders_raw}

    # --- due order items today ---
    tickets_today = await db.job_tickets.find(
        {
            "tenant_id": tenant_id,
            "due_date": today_str,
            "status": {"$in": _ACTIVE_TICKET_STATUSES},
        },
        {"_id": 0, "id": 1, "order_id": 1, "item_name": 1, "due_date": 1, "status": 1, "priority": 1},
    ).sort("due_date", 1).to_list(100)

    due_items = []
    for t in tickets_today:
        order = order_map.get(t.get("order_id"), {})
        cust_name = (
            customer_map.get(order.get("customer_id", ""))
            or order.get("customer_name", "")
            or "Unknown"
        )
        due_items.append({
            "order_id": t.get("order_id", ""),
            "order_number": order.get("order_number", ""),
            "order_item_id": t.get("id", ""),
            "item_name": t.get("item_name", ""),
            "customer_name": cust_name,
            "due_at": f"{t.get('due_date', '')}T00:00:00Z" if t.get("due_date") else "",
            "stage": _TICKET_STAGE_MAP.get(t.get("status", ""), "queued"),
            "priority": t.get("priority", "normal"),
        })

    # --- appointments / installs today ---
    appts_raw = await db.appointments.find(
        {
            "tenant_id": tenant_id,
            "scheduled_at": {"$regex": f"^{today_str}"},
        },
        {"_id": 0},
    ).sort("scheduled_at", 1).to_list(50)

    appointments_today = []
    for a in appts_raw:
        cust_name = customer_map.get(a.get("customer_id", ""), a.get("customer_name", "Unknown"))
        appointments_today.append({
            "appointment_id": a.get("id", ""),
            "title": a.get("title", "Appointment"),
            "customer_name": cust_name,
            "start_at": a.get("scheduled_at", ""),
            "type": a.get("appointment_type", "appointment"),
            "status": a.get("status", "scheduled"),
            "order_id": a.get("order_id", "") or a.get("job_id", ""),
        })

    # --- team status today (reuse shared helper) ---
    team = await _team_status_data(tenant_id)

    return {
        "last_updated_at": _now_iso(),
        "due_order_items_today": due_items,
        "appointments_installs_today": appointments_today,
        "team_status_today": team,
    }


@router.get("/production-snapshot")
async def get_production_snapshot(current_user: UserInDB = Depends(get_current_active_user)):
    """Production pipeline snapshot: stage counts, bottlenecks, at-risk items.

    Data sources:
    - db.job_tickets — all active tickets for stage counting and at-risk detection
    - db.orders — order_number lookup
    """
    tenant_id = current_user.tenant_id
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_dt = datetime.now(timezone.utc)
    within_24h_str = (now_dt + timedelta(hours=24)).strftime("%Y-%m-%d")

    # Load all active tickets for this tenant
    tickets = await db.job_tickets.find(
        {
            "tenant_id": tenant_id,
            "status": {"$nin": ["completed", "cancelled"]},
        },
        {"_id": 0, "id": 1, "order_id": 1, "item_name": 1, "status": 1,
         "due_date": 1, "created_at": 1, "priority": 1},
    ).to_list(5000)

    # order_number lookup
    orders_raw = await db.orders.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "id": 1, "order_number": 1},
    ).to_list(2000)
    order_num_map = {o["id"]: o.get("order_number", "") for o in orders_raw}

    # --- Stage counts ---
    stage_counts: Dict[str, int] = {s: 0 for s in _ALL_STAGES}
    # Track items per stage for bottleneck analysis
    stage_items: Dict[str, List[dict]] = {s: [] for s in _ALL_STAGES}
    for t in tickets:
        stage = _TICKET_STAGE_MAP.get(t.get("status", ""), "queued")
        if stage != "complete":
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            stage_items[stage].append(t)
    # complete = separately counted
    complete_count = await db.job_tickets.count_documents({
        "tenant_id": tenant_id,
        "status": "completed",
    })
    stage_counts["complete"] = complete_count

    # --- Bottlenecks ---
    bottlenecks = []
    for stage in ["queued", "printing", "finishing"]:
        items_in_stage = stage_items.get(stage, [])
        if not items_in_stage:
            continue
        # Find oldest by created_at
        oldest_dt = None
        sample_ids = []
        for item in items_in_stage:
            ca = item.get("created_at")
            if ca:
                try:
                    dt = datetime.fromisoformat(ca.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if oldest_dt is None or dt < oldest_dt:
                        oldest_dt = dt
                except Exception:
                    pass
            sample_ids.append(item.get("id", ""))

        age_hours = (now_dt - oldest_dt).total_seconds() / 3600 if oldest_dt else 0
        bottlenecks.append({
            "stage": stage,
            "backlog_count": len(items_in_stage),
            "oldest_item_age_hours": round(age_hours, 1),
            "sample_order_item_ids": sample_ids[:3],
        })
    # Sort by backlog desc
    bottlenecks.sort(key=lambda b: b["backlog_count"], reverse=True)

    # --- At-risk items ---
    at_risk = []
    for t in tickets:
        due = t.get("due_date", "")
        status = t.get("status", "")
        reason = None
        if due and due < today_str:
            reason = "overdue"
        elif due and due <= within_24h_str and status in ["new", "awaiting_info", "queued", "approved"]:
            reason = "due_within_24h_not_started"
        elif status == "on_hold":
            reason = "blocked"

        if reason:
            at_risk.append({
                "order_id": t.get("order_id", ""),
                "order_number": order_num_map.get(t.get("order_id", ""), ""),
                "order_item_id": t.get("id", ""),
                "item_name": t.get("item_name", ""),
                "reason": reason,
                "due_at": f"{due}T00:00:00Z" if due else "",
            })

    # Sort: overdue first, then by due date
    _reason_priority = {"overdue": 0, "due_within_24h_not_started": 1, "blocked": 2}
    at_risk.sort(key=lambda x: (_reason_priority.get(x["reason"], 9), x["due_at"]))

    return {
        "last_updated_at": _now_iso(),
        "order_items_by_stage": stage_counts,
        "bottlenecks": bottlenecks,
        "at_risk": at_risk[:20],  # cap at 20 for performance
    }


@router.get("/customer-attention")
async def get_customer_attention(current_user: UserInDB = Depends(get_current_active_user)):
    """Customer-facing urgency items: unread messages, pending approvals/signatures, quote followups.

    Each list is sorted by urgency_score DESC then timestamp DESC.
    Data sources:
    - db.conversations (unread messages)
    - db.artwork_proofs + db.signatures (approvals/signatures pending)
    - db.quotes (quote followups: sent but not yet approved)
    """
    tenant_id = current_user.tenant_id

    # -- Customer name lookup --
    customers_raw = await db.customers.find(
        {"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(5000)
    customer_map = {c["id"]: c["name"] for c in customers_raw}

    # -- Order number lookup --
    orders_raw = await db.orders.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "id": 1, "order_number": 1, "customer_id": 1},
    ).to_list(2000)
    order_map = {o["id"]: o for o in orders_raw}

    # ---- Unread conversations ----
    convs = await db.conversations.find(
        {"tenant_id": tenant_id, "shop_unread_count": {"$gt": 0}},
        {"_id": 0, "id": 1, "customer_id": 1, "last_message": 1,
         "last_message_at": 1, "shop_unread_count": 1},
    ).to_list(50)

    unread_conversations = []
    for c in convs:
        age = _age_hours(c.get("last_message_at"))
        unread = c.get("shop_unread_count", 1)
        urgency = round(unread * min(age / 24.0, 5.0), 2)  # capped at 5-day multiplier
        unread_conversations.append({
            "conversation_id": c.get("id", ""),
            "customer_name": customer_map.get(c.get("customer_id", ""), "Unknown"),
            "unread_count": unread,
            "last_message_preview": (c.get("last_message") or "")[:100],
            "last_message_at": c.get("last_message_at", ""),
            "urgency_score": urgency,
        })
    unread_conversations.sort(key=lambda x: (-x["urgency_score"], x["last_message_at"]))

    # ---- Approvals + Signatures pending ----
    proofs = await db.artwork_proofs.find(
        {"tenant_id": tenant_id, "status": "pending"},
        {"_id": 0, "id": 1, "job_id": 1, "customer_id": 1, "created_at": 1},
    ).to_list(100)

    sigs = await db.signatures.find(
        {"tenant_id": tenant_id, "status": "pending"},
        {"_id": 0, "id": 1, "order_id": 1, "parent_record_id": 1,
         "customer_id": 1, "created_at": 1, "expires_at": 1},
    ).to_list(100)

    # Proof parent can be an order or legacy job — check orders first
    jobs_raw = await db.jobs.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "id": 1, "name": 1, "customer_id": 1},
    ).to_list(1000)
    legacy_job_map = {j["id"]: j for j in jobs_raw}

    approvals_sigs = []
    for p in proofs:
        age = _age_hours(p.get("created_at"))
        parent_id = p.get("job_id", "")
        order = order_map.get(parent_id)
        order_number = order.get("order_number", "") if order else ""
        if not order_number:
            lj = legacy_job_map.get(parent_id, {})
            order_number = lj.get("name", "")
        cust_id = p.get("customer_id") or (order or {}).get("customer_id", "")
        approvals_sigs.append({
            "record_id": p.get("id", ""),
            "type": "proof",
            "customer_name": customer_map.get(cust_id, "Unknown"),
            "order_number": order_number,
            "requested_at": p.get("created_at", ""),
            "age_hours": round(age, 1),
            "urgency_score": round(age, 2),
        })

    for s in sigs:
        age = _age_hours(s.get("created_at"))
        order_id = s.get("order_id") or s.get("parent_record_id", "")
        order = order_map.get(order_id, {})
        cust_id = s.get("customer_id") or order.get("customer_id", "")
        approvals_sigs.append({
            "record_id": s.get("id", ""),
            "type": "signature",
            "customer_name": customer_map.get(cust_id, "Unknown"),
            "order_number": order.get("order_number", ""),
            "requested_at": s.get("created_at", ""),
            "age_hours": round(age, 1),
            "urgency_score": round(age, 2),
        })

    approvals_sigs.sort(key=lambda x: (-x["urgency_score"], x["requested_at"]))

    # ---- Quote followups ----
    quotes_sent = await db.quotes.find(
        {"tenant_id": tenant_id, "status": "sent"},
        {"_id": 0, "id": 1, "customer_id": 1, "order_id": 1, "total": 1,
         "sent_at": 1, "customer_name": 1},
    ).to_list(100)

    quote_followups = []
    for q in quotes_sent:
        age_days = _age_hours(q.get("sent_at")) / 24
        total = q.get("total", 0) or 0
        urgency = round(total / 1000.0 + age_days * 10, 2)
        order_id = q.get("order_id", "")
        order = order_map.get(order_id, {})
        cust_id = q.get("customer_id") or order.get("customer_id", "")
        cust_name = (
            customer_map.get(cust_id)
            or q.get("customer_name", "")
            or "Unknown"
        )
        quote_followups.append({
            "quote_id": q.get("id", ""),
            "customer_name": cust_name,
            "order_number": order.get("order_number", ""),
            "quote_total": total,
            "last_sent_at": q.get("sent_at", ""),
            "age_days": round(age_days, 1),
            "urgency_score": urgency,
        })
    quote_followups.sort(key=lambda x: (-x["urgency_score"], x["last_sent_at"]))

    return {
        "last_updated_at": _now_iso(),
        "unread_conversations": unread_conversations,
        "approvals_signatures_pending": approvals_sigs,
        "quote_followups": quote_followups,
    }


@router.get("/financial-attention")
async def get_financial_attention(current_user: UserInDB = Depends(get_current_active_user)):
    """Financial urgency dashboard: unpaid, overdue, due-this-week, recent payments.

    Each section returns a count, total_amount, and top_records (max 3).
    Data source: db.invoices exclusively.
    """
    tenant_id = current_user.tenant_id
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    week_end_str = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d")

    # Customer name lookup
    customers_raw = await db.customers.find(
        {"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(5000)
    customer_map = {c["id"]: c["name"] for c in customers_raw}

    def _top3(invoices: List[dict]) -> List[dict]:
        """Return top 3 invoice records as output dicts, sorted by amount desc."""
        sorted_inv = sorted(invoices, key=lambda i: i.get("total", 0), reverse=True)
        return [
            {
                "invoice_id": inv.get("id", ""),
                "invoice_number": inv.get("invoice_number", ""),
                "customer_name": customer_map.get(inv.get("customer_id", ""), inv.get("customer_name", "Unknown")),
                "amount": inv.get("total", 0),
                "status": inv.get("status", ""),
                "due_date": inv.get("due_date", ""),
                "paid_date": inv.get("paid_date", ""),
            }
            for inv in sorted_inv[:3]
        ]

    # ---- Unpaid (sent only — not overdue) ----
    unpaid_invoices = await db.invoices.find(
        {"tenant_id": tenant_id, "status": "sent"},
        {"_id": 0, "id": 1, "invoice_number": 1, "customer_id": 1,
         "customer_name": 1, "total": 1, "status": 1, "due_date": 1, "paid_date": 1},
    ).to_list(500)
    unpaid_total = sum(i.get("total", 0) for i in unpaid_invoices)

    # ---- Overdue ----
    overdue_invoices = await db.invoices.find(
        {"tenant_id": tenant_id, "status": "overdue"},
        {"_id": 0, "id": 1, "invoice_number": 1, "customer_id": 1,
         "customer_name": 1, "total": 1, "status": 1, "due_date": 1, "paid_date": 1},
    ).to_list(500)
    overdue_total = sum(i.get("total", 0) for i in overdue_invoices)

    # ---- Due this week (sent/overdue with due_date in next 7 days) ----
    due_week_invoices = await db.invoices.find(
        {
            "tenant_id": tenant_id,
            "status": {"$in": ["sent", "overdue"]},
            "due_date": {"$gte": today_str, "$lte": week_end_str},
        },
        {"_id": 0, "id": 1, "invoice_number": 1, "customer_id": 1,
         "customer_name": 1, "total": 1, "status": 1, "due_date": 1, "paid_date": 1},
    ).to_list(200)
    due_week_total = sum(i.get("total", 0) for i in due_week_invoices)

    # ---- Recent payments (last 10 paid, desc by paid_date) ----
    recent_paid = await db.invoices.find(
        {"tenant_id": tenant_id, "status": "paid", "paid_date": {"$exists": True}},
        {"_id": 0, "id": 1, "invoice_number": 1, "customer_id": 1,
         "customer_name": 1, "total": 1, "status": 1, "due_date": 1, "paid_date": 1},
    ).sort("paid_date", -1).to_list(10)
    recent_paid_total = sum(i.get("total", 0) for i in recent_paid)

    return {
        "last_updated_at": _now_iso(),
        "unpaid": {
            "count": len(unpaid_invoices),
            "total_amount": round(unpaid_total, 2),
            "top_records": _top3(unpaid_invoices),
        },
        "overdue": {
            "count": len(overdue_invoices),
            "total_amount": round(overdue_total, 2),
            "top_records": _top3(overdue_invoices),
        },
        "due_this_week": {
            "count": len(due_week_invoices),
            "total_amount": round(due_week_total, 2),
            "top_records": _top3(due_week_invoices),
        },
        "recent_payments": {
            "count": len(recent_paid),
            "total_amount": round(recent_paid_total, 2),
            "top_records": _top3(recent_paid),
        },
    }
