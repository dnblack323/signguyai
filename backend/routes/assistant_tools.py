"""
Assistant tool-calling subsystem.

Extracted from ``routes/ai.py`` (Feb 2026) as the tool-router architecture
hit ~700 lines and was actively growing every pass. Kept as its own module
so new tools can be added in one place without bloating the legacy AI route
file.

Public API:
    - TOOL_SCHEMAS                : LLM-facing schema list
    - route_with_tools(msg, tid)  : two-layer router (kw fast-path + classifier)
    - execute_metric_query(...)   : direct metric helper (also used by nudges)
    - safe_parse_datetime_phrase  : natural-language → ISO UTC

FastAPI sub-router exposed via ``router`` for the commit endpoints (task /
appointment / reminder / quote follow-up bulk).
"""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient

from core.auth_deps import get_current_active_user
from models import UserInDB

logger = logging.getLogger(__name__)

# DB handle — share the same connection ai.py uses
_mongo_client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
db = _mongo_client[os.environ.get("DB_NAME", "signguy")]

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

router = APIRouter(prefix="/ai/assistant", tags=["AI Assistant Tools"])


# ────────── Tool schemas ──────────

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "navigate",
        "description": "Open a specific page inside the SignGuy AI app.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "enum": [
                        "dashboard", "orders", "billing", "invoices", "quotes",
                        "customers", "webstores", "documents", "questionnaires",
                        "team", "schedule", "appointments", "calendar", "tasks",
                        "ai_tools", "financials", "productivity", "reports",
                        "settings", "pricing_foundation",
                    ],
                },
                "spoken_label": {"type": "string"},
            },
            "required": ["destination"],
        },
    },
    {
        "name": "create_task",
        "description": "Add a task to the user's task list.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "due_date_phrase": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
            },
            "required": ["title"],
        },
    },
    {
        "name": "create_appointment",
        "description": "Schedule an appointment / job on the calendar.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "customer_query": {"type": "string"},
                "start_phrase": {"type": "string"},
                "duration_minutes": {"type": "integer"},
            },
            "required": ["title", "start_phrase"],
        },
    },
    {
        "name": "set_reminder",
        "description": "Set a one-shot reminder. Use for 'remind me to check on the order in 3 days', 'remind me on Friday to follow up with Donald'.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "What to be reminded about"},
                "when_phrase": {"type": "string", "description": "When the reminder should fire (e.g. 'tomorrow 9am', 'friday', 'in 3 days')"},
            },
            "required": ["text", "when_phrase"],
        },
    },
    {
        "name": "send_quote_followup_bulk",
        "description": "Bulk-send follow-up emails to ALL stale quotes at once. Use only when user clearly asks for bulk (e.g. 'follow up on all my stale quotes', 'email everyone who hasn't responded').",
        "parameters": {
            "type": "object",
            "properties": {
                "max_count": {"type": "integer", "description": "Optional cap, defaults to 10"},
            },
        },
    },
    {
        "name": "query_shop_metric",
        "description": "Answer a number question about the shop.",
        "parameters": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "enum": [
                        "revenue_today", "revenue_week", "revenue_month",
                        "open_orders", "open_invoices_total", "overdue_invoices_count",
                        "customers_total", "customers_new_30d",
                        "top_customer_30d", "stale_quotes_count",
                    ],
                },
            },
            "required": ["metric"],
        },
    },
]


# ────────── Helpers ──────────

def safe_parse_datetime_phrase(phrase: str) -> Optional[str]:
    """Best-effort natural-language → ISO UTC datetime."""
    if not phrase:
        return None
    p = phrase.strip().lower()
    now = datetime.now(timezone.utc)

    try:
        return datetime.fromisoformat(p.replace("z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    # "in N days"
    m = re.search(r"in\s+(\d+)\s+days?", p)
    if m:
        days = int(m.group(1))
        return (now + timedelta(days=days)).replace(hour=9, minute=0, second=0, microsecond=0).isoformat()

    weekday_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    base = None
    if "today" in p:
        base = now.replace(hour=9, minute=0, second=0, microsecond=0)
    elif "tomorrow" in p:
        base = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    elif "next week" in p:
        base = (now + timedelta(days=7)).replace(hour=9, minute=0, second=0, microsecond=0)
    else:
        for name, idx in weekday_map.items():
            if name in p:
                days_ahead = (idx - now.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                base = (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)
                break
    if base is None:
        return None

    tm = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", p)
    if tm:
        hr = int(tm.group(1))
        mn = int(tm.group(2) or 0)
        ampm = tm.group(3)
        if ampm == "pm" and hr < 12:
            hr += 12
        if ampm == "am" and hr == 12:
            hr = 0
        if 0 <= hr <= 23 and 0 <= mn <= 59:
            base = base.replace(hour=hr, minute=mn)
    return base.isoformat()


async def _lookup_customer(tenant_id: str, name: str) -> Optional[Dict[str, Any]]:
    """Case-insensitive customer name lookup."""
    if not name:
        return None
    return await db.customers.find_one(
        {"tenant_id": tenant_id, "name": {"$regex": f"^{re.escape(name)}", "$options": "i"}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1},
    )


# ────────── Two-layer router ──────────

METRIC_KEYWORDS = [
    (("how much", "today"), "revenue_today"),
    (("how much", "made today"), "revenue_today"),
    (("revenue", "today"), "revenue_today"),
    (("money", "today"), "revenue_today"),
    (("how much", "week"), "revenue_week"),
    (("how much", "this week"), "revenue_week"),
    (("revenue", "week"), "revenue_week"),
    (("how much", "month"), "revenue_month"),
    (("how much", "this month"), "revenue_month"),
    (("revenue", "month"), "revenue_month"),
    (("how many", "open order"), "open_orders"),
    (("how many", "open jobs"), "open_orders"),
    (("open orders",), "open_orders"),
    (("how much", "outstanding"), "open_invoices_total"),
    (("how much", "unpaid"), "open_invoices_total"),
    (("how many", "overdue invoice"), "overdue_invoices_count"),
    (("how many", "customers"), "customers_total"),
    (("new customers",), "customers_new_30d"),
    (("top customer",), "top_customer_30d"),
    (("stale quotes",), "stale_quotes_count"),
    (("how many", "stale"), "stale_quotes_count"),
]

NAV_KEYWORDS = [
    ("open the schedule", "schedule"), ("open my schedule", "schedule"),
    ("show me the schedule", "schedule"), ("open calendar", "calendar"),
    ("show me my orders", "orders"), ("open orders", "orders"),
    ("show me customers", "customers"), ("open customers", "customers"),
    ("show me invoices", "invoices"), ("open invoices", "invoices"),
    ("show me tasks", "tasks"), ("open tasks", "tasks"),
    ("open ai tools", "ai_tools"), ("show me reports", "reports"),
    ("open dashboard", "dashboard"),
]


async def route_with_tools(message: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    """Two-layer router. Returns {tool, args, executed} or None."""
    if not message or len(message) > 600:
        return None
    lower = message.lower().strip().rstrip("?!.")

    # Priority deterministic check: bulk follow-up verb beats metric matchers.
    # ("follow up on all my stale quotes" should SEND emails, not just count.)
    if ("follow up" in lower or "follow-up" in lower) and ("all" in lower or "every" in lower) and ("stale" in lower or "quote" in lower or "unrespond" in lower):
        executed = await _execute_tool("send_quote_followup_bulk", {}, tenant_id)
        return {"tool": "send_quote_followup_bulk", "args": {}, "executed": executed}

    # Fast path: keyword metric matches
    for keywords, metric in METRIC_KEYWORDS:
        if all(k in lower for k in keywords):
            executed = await execute_metric_query(metric, tenant_id)
            return {"tool": "query_shop_metric", "args": {"metric": metric}, "executed": executed}

    # Fast path: keyword navigation
    for phrase, dest in NAV_KEYWORDS:
        if phrase in lower:
            executed = await _execute_tool("navigate", {"destination": dest}, tenant_id)
            return {"tool": "navigate", "args": {"destination": dest}, "executed": executed}

    # LLM classifier fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
    except Exception:
        return None

    tool_descriptions = "\n".join(f"- {t['name']}: {t['description']}" for t in TOOL_SCHEMAS)
    schema_json = json.dumps(TOOL_SCHEMAS, indent=2)
    classifier_prompt = (
        "You are an intent router for a sign-shop SaaS app. Decide if the user's "
        "message maps to one of these tools, OR is just a chat question.\n\n"
        f"Available tools:\n{tool_descriptions}\n\n"
        f"Full JSON schemas:\n{schema_json}\n\n"
        "Rules:\n"
        "1. 'how much/how many/total/revenue/made/open/overdue/top' number questions → query_shop_metric.\n"
        "2. DO verbs (open, show me, take me to, navigate) for a page → navigate.\n"
        "3. 'add a task' / 'remember to do X' → create_task.\n"
        "4. 'remind me to X (at/on/in Y)' → set_reminder.\n"
        "5. 'schedule', 'book', 'set up an appointment/meeting/install' with date/time → create_appointment.\n"
        "6. 'follow up on all stale quotes' / 'email everyone unresponded' → send_quote_followup_bulk.\n"
        "7. Advice / opinion / strategy / how-to → tool: null.\n\n"
        "Output STRICT JSON only (no markdown fence):\n"
        '  { "tool": "<name>", "args": { ... } } OR { "tool": null }\n\n'
        f"User message: {message}"
    )
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"router_{uuid.uuid4()}",
            system_message="You output strict JSON only.",
        ).with_model("openai", "gpt-4o-mini")
        raw = await chat.send_message(UserMessage(text=classifier_prompt))
        text = raw if isinstance(raw, str) else (getattr(raw, "text", None) or str(raw))
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
        parsed = json.loads(text)
    except Exception as exc:
        logger.warning("tool router classifier failed: %s", exc)
        return None

    tool_name = parsed.get("tool")
    args = parsed.get("args") or {}
    if not tool_name:
        return None
    try:
        executed = await _execute_tool(tool_name, args, tenant_id)
    except Exception as exc:
        logger.exception("tool execution failed for %s: %s", tool_name, exc)
        return None
    return {"tool": tool_name, "args": args, "executed": executed}


# ────────── Tool executors ──────────

async def _execute_tool(tool_name: str, args: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
    if tool_name == "navigate":
        dest = (args.get("destination") or "").lower()
        route_map = {
            "dashboard": "/dashboard", "orders": "/jobs", "billing": "/billing",
            "invoices": "/billing/invoices", "quotes": "/billing/quotes",
            "customers": "/customers", "webstores": "/webstores",
            "documents": "/documents", "questionnaires": "/questionnaires",
            "team": "/team", "schedule": "/calendar", "appointments": "/calendar",
            "calendar": "/calendar", "tasks": "/tasks", "ai_tools": "/ai-tools",
            "financials": "/financials", "productivity": "/productivity",
            "reports": "/reports", "settings": "/settings",
            "pricing_foundation": "/pricing-foundation",
        }
        nice = {
            "dashboard": "Dashboard", "orders": "Orders", "billing": "Billing",
            "invoices": "Invoices", "quotes": "Quotes", "customers": "Customers",
            "webstores": "Webstores", "documents": "Documents",
            "questionnaires": "Questionnaires", "team": "Team",
            "schedule": "Schedule", "appointments": "Schedule",
            "calendar": "Schedule", "tasks": "Tasks", "ai_tools": "AI Tools",
            "financials": "Financials", "productivity": "Productivity",
            "reports": "Reports", "settings": "Settings",
            "pricing_foundation": "Pricing Foundation",
        }
        return {
            "action_type": "navigate",
            "status": "ready",
            "path": route_map.get(dest, "/dashboard"),
            "label": nice.get(dest) or dest.replace("_", " ").title(),
            "confirm_label": f"Open {nice.get(dest) or dest}",
            "auto_execute": True,
        }

    if tool_name == "create_task":
        title = (args.get("title") or "").strip()
        if not title:
            return {"action_type": "create_task", "status": "needs_clarification", "hint": "What should the task be?"}
        return {
            "action_type": "create_task",
            "status": "ready",
            "title": title,
            "due_date": safe_parse_datetime_phrase(args.get("due_date_phrase") or ""),
            "priority": (args.get("priority") or "normal").lower() if (args.get("priority") or "normal").lower() in {"low", "normal", "high"} else "normal",
            "confirm_label": "Add to tasks",
            "low_risk": True,
            "auto_execute": False,
        }

    if tool_name == "create_appointment":
        title = (args.get("title") or "").strip() or "Appointment"
        start_iso = safe_parse_datetime_phrase(args.get("start_phrase") or "")
        if not start_iso:
            return {"action_type": "create_appointment", "status": "needs_clarification", "hint": "When should it be?"}
        customer = None
        if args.get("customer_query"):
            customer = await _lookup_customer(tenant_id, args["customer_query"])
        return {
            "action_type": "create_appointment",
            "status": "ready",
            "title": title,
            "start_at": start_iso,
            "duration_minutes": int(args.get("duration_minutes") or 60),
            "customer": {"id": customer.get("id"), "name": customer.get("name")} if customer else None,
            "confirm_label": "Add to calendar",
            "low_risk": True,
            "auto_execute": False,
        }

    if tool_name == "set_reminder":
        text = (args.get("text") or "").strip()
        when_iso = safe_parse_datetime_phrase(args.get("when_phrase") or "")
        if not text or not when_iso:
            return {"action_type": "set_reminder", "status": "needs_clarification", "hint": "Tell me what to remind you about and when."}
        return {
            "action_type": "set_reminder",
            "status": "ready",
            "text": text,
            "remind_at": when_iso,
            "confirm_label": "Set reminder",
            "low_risk": True,
            "auto_execute": False,
        }

    if tool_name == "send_quote_followup_bulk":
        max_count = min(int(args.get("max_count") or 10), 25)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
        stale = await db.quotes.find(
            {
                "tenant_id": tenant_id,
                "status": {"$in": ["sent", "pending", "draft"]},
                "created_at": {"$lt": cutoff},
            },
            {"_id": 0, "id": 1, "customer_id": 1, "customer_name": 1, "total": 1, "quote_number": 1},
        ).sort("created_at", 1).limit(max_count).to_list(max_count)
        if not stale:
            return {"action_type": "send_quote_followup_bulk", "status": "needs_clarification", "hint": "Nothing stale to follow up on — your quotes are fresh."}
        return {
            "action_type": "send_quote_followup_bulk",
            "status": "ready",
            "count": len(stale),
            "previews": [
                {
                    "quote_id": q["id"],
                    "customer_id": q.get("customer_id"),
                    "customer_name": q.get("customer_name"),
                    "quote_number": q.get("quote_number"),
                    "total": q.get("total"),
                }
                for q in stale
            ],
            "confirm_label": f"Send {len(stale)} follow-up emails",
            "low_risk": False,
            "auto_execute": False,
        }

    if tool_name == "query_shop_metric":
        return await execute_metric_query(args.get("metric"), tenant_id)

    return {"action_type": "unknown", "status": "error", "hint": "Tool not implemented"}


async def execute_metric_query(metric: str, tenant_id: str) -> Dict[str, Any]:
    """Compute one of the supported metrics and return a friendly answer."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    week_start = (now - timedelta(days=7)).isoformat()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    async def _sum_invoices(match: dict) -> float:
        rows = await db.invoices.find(match, {"_id": 0, "grand_total": 1, "total": 1}).to_list(None)
        return float(sum((d.get("grand_total") or d.get("total") or 0) for d in rows))

    if metric == "revenue_today":
        total = await _sum_invoices({"tenant_id": tenant_id, "status": "paid", "updated_at": {"$gte": today_start}})
        return _metric_response(metric, total, f"${total:,.2f}", f"Today's paid revenue is ${total:,.2f}.")
    if metric == "revenue_week":
        total = await _sum_invoices({"tenant_id": tenant_id, "status": "paid", "updated_at": {"$gte": week_start}})
        return _metric_response(metric, total, f"${total:,.2f}", f"Past 7 days: ${total:,.2f} in paid revenue.")
    if metric == "revenue_month":
        total = await _sum_invoices({"tenant_id": tenant_id, "status": "paid", "updated_at": {"$gte": month_start}})
        return _metric_response(metric, total, f"${total:,.2f}", f"Month-to-date paid revenue: ${total:,.2f}.")
    if metric == "open_orders":
        count = await db.jobs.count_documents({"tenant_id": tenant_id, "status": {"$in": ["pending", "in_progress", "production"]}})
        return _metric_response(metric, count, str(count), f"You have {count} open orders.")
    if metric == "open_invoices_total":
        rows = await db.invoices.find(
            {"tenant_id": tenant_id, "status": {"$in": ["sent", "partial", "overdue"]}},
            {"_id": 0, "grand_total": 1, "total": 1, "amount_paid": 1},
        ).to_list(None)
        total = sum(max((d.get("grand_total") or d.get("total") or 0) - (d.get("amount_paid") or 0), 0) for d in rows)
        return _metric_response(metric, total, f"${total:,.2f}", f"Outstanding invoice balance: ${total:,.2f}.")
    if metric == "overdue_invoices_count":
        count = await db.invoices.count_documents({"tenant_id": tenant_id, "status": "overdue"})
        return _metric_response(metric, count, str(count), f"You have {count} overdue invoices.")
    if metric == "customers_total":
        count = await db.customers.count_documents({"tenant_id": tenant_id})
        return _metric_response(metric, count, str(count), f"You have {count} customers in your CRM.")
    if metric == "customers_new_30d":
        cutoff = (now - timedelta(days=30)).isoformat()
        count = await db.customers.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": cutoff}})
        return _metric_response(metric, count, str(count), f"{count} new customers in the last 30 days.")
    if metric == "stale_quotes_count":
        cutoff = (now - timedelta(days=4)).isoformat()
        count = await db.quotes.count_documents(
            {"tenant_id": tenant_id, "status": {"$in": ["sent", "pending", "draft"]}, "created_at": {"$lt": cutoff}}
        )
        return _metric_response(metric, count, str(count), f"{count} quotes are stale (>4 days, not yet accepted).")
    if metric == "top_customer_30d":
        cutoff = (now - timedelta(days=30)).isoformat()
        pipe = [
            {"$match": {"tenant_id": tenant_id, "status": "paid", "updated_at": {"$gte": cutoff}}},
            {"$group": {"_id": "$customer_id", "name": {"$last": "$customer_name"}, "total": {"$sum": {"$ifNull": ["$grand_total", "$total"]}}}},
            {"$sort": {"total": -1}}, {"$limit": 1},
        ]
        top = await db.invoices.aggregate(pipe).to_list(1)
        if not top:
            return _metric_response(metric, 0, "—", "No paid invoices in the last 30 days.")
        t = top[0]
        return _metric_response(metric, t.get("total"), f"{t.get('name') or 'Unknown'} — ${t.get('total', 0):,.2f}",
                                f"Your top customer in the last 30 days is **{t.get('name') or 'Unknown'}** with ${t.get('total', 0):,.2f}.")

    return {"action_type": "metric", "status": "error", "hint": "Unknown metric"}


def _metric_response(metric: str, value: Any, value_label: str, answer: str) -> Dict[str, Any]:
    return {
        "action_type": "metric",
        "status": "ready",
        "metric": metric,
        "value": value,
        "value_label": value_label,
        "answer": answer,
        "auto_execute": True,
    }


# ────────── Commit endpoints ──────────

@router.post("/commit-task")
async def commit_task(
    payload: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user),
):
    title = (payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title is required")
    now = datetime.now(timezone.utc).isoformat()
    task = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "title": title,
        "description": payload.get("description"),
        "priority": payload.get("priority") or "normal",
        "status": "open",
        "is_complete": False,
        "due_date": payload.get("due_date"),
        "created_at": now,
        "updated_at": now,
        "created_by_ai": True,
    }
    await db.tasks.insert_one(task)
    task.pop("_id", None)
    return {"success": True, "task": task}


@router.post("/commit-appointment")
async def commit_appointment(
    payload: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user),
):
    title = (payload.get("title") or "").strip() or "Appointment"
    start_at = payload.get("start_at")
    if not start_at:
        raise HTTPException(status_code=400, detail="Appointment start time is required")
    duration = int(payload.get("duration_minutes") or 60)
    try:
        end_at = (datetime.fromisoformat(start_at) + timedelta(minutes=duration)).isoformat()
    except Exception:
        end_at = start_at
    now = datetime.now(timezone.utc).isoformat()
    customer = payload.get("customer") or {}
    appt = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "title": title,
        "customer_id": customer.get("id"),
        "customer_name": customer.get("name"),
        "start_at": start_at,
        "end_at": end_at,
        "duration_minutes": duration,
        "status": "confirmed",
        "created_at": now,
        "updated_at": now,
        "created_by_ai": True,
    }
    await db.appointments.insert_one(appt)
    appt.pop("_id", None)
    return {"success": True, "appointment": appt}


@router.post("/commit-reminder")
async def commit_reminder(
    payload: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Persist a one-shot reminder. Surfaces in the Dashboard nudges widget
    when ``remind_at`` is in the past (the scheduler / nudge endpoint will
    pick it up). Stored in ``assistant_reminders`` so it doesn't pollute
    the task list."""
    text = (payload.get("text") or "").strip()
    remind_at = payload.get("remind_at")
    if not text or not remind_at:
        raise HTTPException(status_code=400, detail="Reminder text and time are required")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "text": text,
        "remind_at": remind_at,
        "status": "pending",
        "created_at": now,
        "updated_at": now,
        "created_by_ai": True,
    }
    await db.assistant_reminders.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "reminder": doc}


@router.post("/bulk-followup-quotes")
async def commit_bulk_quote_followups(
    payload: Dict[str, Any],
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Send follow-up emails to a batch of stale quotes. Reuses the existing
    assistant draft-email + send-email helpers."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from services.email_service import email_service

    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI not configured")

    previews = payload.get("previews") or []
    if not previews:
        return {"success": True, "sent": 0, "results": []}

    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0, "company_name": 1}) or {}
    company = tenant.get("company_name") or "your sign shop"

    sent_results = []
    for p in previews[:25]:
        cust = await db.customers.find_one(
            {"id": p.get("customer_id"), "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1, "email": 1},
        )
        if not cust or not cust.get("email"):
            sent_results.append({"quote_id": p.get("quote_id"), "status": "skipped", "reason": "no email"})
            continue

        prompt = (
            f"Write a 2-3 sentence friendly quote follow-up for {cust.get('name')} "
            f"on quote #{p.get('quote_number') or p.get('quote_id', '')[:8]} totalling "
            f"${(p.get('total') or 0):.2f}. Keep professional, no fake name. "
            "Return JSON: {\"subject\":..., \"body\":...} only."
        )
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"bulk_followup_{uuid.uuid4()}",
                system_message="Strict JSON only.",
            ).with_model("openai", "gpt-4o-mini")
            raw = await chat.send_message(UserMessage(text=prompt))
            text = raw if isinstance(raw, str) else (getattr(raw, "text", None) or str(raw))
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
            parsed = json.loads(text)
            subject = (parsed.get("subject") or "Following up on your quote").strip()
            body = (parsed.get("body") or "").strip()
        except Exception as exc:
            logger.warning("draft for %s failed: %s", p.get("quote_id"), exc)
            subject = "Following up on your quote"
            body = (
                f"Hi {cust.get('name')}, just checking in on quote "
                f"#{p.get('quote_number') or ''} we sent over. Happy to answer any questions."
            )

        html = f"<div style='font-family:Arial,sans-serif;max-width:600px;color:#0F172A;'><p>Hi {cust.get('name')},</p><p>{body.replace(chr(10), '<br/>')}</p><hr style='border:none;border-top:1px solid #E2E8F0;margin:18px 0;'/><p style='color:#94A3B8;font-size:12px;'>Sent by {company}</p></div>"
        res = await email_service.send_email(
            to_email=cust["email"],
            subject=subject,
            html_content=html,
            plain_content=body,
            tenant_id=current_user.tenant_id,
        )
        sent_results.append({
            "quote_id": p.get("quote_id"),
            "to": cust["email"],
            "status": "sent" if res.get("success") else "failed",
            "reason": res.get("error") if not res.get("success") else None,
        })

    successful = sum(1 for r in sent_results if r["status"] == "sent")
    return {"success": True, "sent": successful, "results": sent_results}
