"""
Assistant Navigation Service (Phase 3 — Business Assistant Context & Navigation)

- Route whitelist so LLM cannot inject arbitrary URLs.
- Route builders for filtered lists (overdue invoices, jobs due tomorrow, etc).
- Related-record resolver (order→customer, invoice→order, etc).
- Customer / order / employee lookup with ambiguity handling.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from datetime import date
import re

from models.auth import Permission

# ----------------------------------------------------------------------------
# Whitelist of navigable destinations.
# Each target -> (route template, required Permission or None, accepts filter kwargs)
# Route template uses Python format-style {placeholders} ({id}, {ticket_id}).
# ----------------------------------------------------------------------------
NAV_TARGETS: Dict[str, Dict[str, Any]] = {
    # Sales
    "orders_list": {"route": "/orders", "perm": Permission.JOBS_VIEW, "filters": {"status", "due_from", "due_to", "customer_id"}},
    "order_detail": {"route": "/orders/{id}", "perm": Permission.JOBS_VIEW, "filters": set()},
    "new_order": {"route": "/orders/new", "perm": Permission.JOBS_CREATE, "filters": {"customer_id", "customer_name"}},
    "job_ticket_detail": {"route": "/job-tickets/{ticket_id}", "perm": Permission.JOBS_VIEW, "filters": set()},
    "customers_list": {"route": "/customers", "perm": Permission.CUSTOMERS_VIEW, "filters": set()},
    "invoices_list": {"route": "/invoices", "perm": Permission.INVOICES_VIEW, "filters": {"status", "customer_id"}},
    "quotes_list": {"route": "/quotes", "perm": Permission.QUOTES_VIEW, "filters": set()},

    # Production
    "production_board": {"route": "/production-board", "perm": Permission.JOBS_VIEW, "filters": set()},
    "approvals": {"route": "/approvals", "perm": Permission.JOBS_VIEW, "filters": {"status"}},

    # Financials
    "financials": {"route": "/financials", "perm": Permission.FINANCIALS_VIEW, "filters": {"period"}},
    "reports_profit_margin": {"route": "/reports/profit-margin", "perm": Permission.FINANCIALS_VIEW, "filters": set()},

    # Team
    "timeclock": {"route": "/timeclock", "perm": Permission.TIME_CLOCK_OWN, "filters": set()},
    "timesheets": {"route": "/timesheets", "perm": Permission.PAYROLL_VIEW, "filters": set()},
    "payroll": {"route": "/payroll", "perm": Permission.PAYROLL_VIEW, "filters": set()},
    "employee_schedule": {"route": "/employee-schedule", "perm": Permission.EMPLOYEES_VIEW, "filters": {"employee_id", "week"}},
    "productivity": {"route": "/productivity", "perm": Permission.EMPLOYEES_VIEW, "filters": set()},

    # Webstores
    "webstores": {"route": "/webstores", "perm": Permission.WEBSTORES_VIEW, "filters": set()},

    # Docs / AI
    "documents": {"route": "/documents", "perm": None, "filters": set()},
    "ai_tools": {"route": "/ai-tools", "perm": None, "filters": set()},
    "ai_assistant": {"route": "/ai-assistant", "perm": None, "filters": set()},

    # Dashboard / Settings
    "dashboard": {"route": "/dashboard", "perm": None, "filters": set()},
    "settings": {"route": "/settings", "perm": Permission.SETTINGS_VIEW, "filters": set()},
    "settings_pricing": {"route": "/settings/pricing-setup", "perm": Permission.SETTINGS_VIEW, "filters": set()},
    "settings_production": {"route": "/settings/production", "perm": Permission.SETTINGS_VIEW, "filters": set()},
}


def build_safe_route(
    target: str,
    *,
    params: Optional[Dict[str, str]] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Validate target + render a real route. Returns None if target is unknown or
    required path params are missing. Filter keys outside the allowed set are dropped.
    """
    spec = NAV_TARGETS.get(target)
    if not spec:
        return None
    template: str = spec["route"]
    params = params or {}
    filters = filters or {}

    # Fill path placeholders.
    placeholders = re.findall(r"\{([a-z_]+)\}", template)
    for p in placeholders:
        value = params.get(p)
        if not value or not re.fullmatch(r"[A-Za-z0-9_\-]+", str(value)):
            return None
        template = template.replace("{" + p + "}", str(value))

    # Filter keys: only allow whitelisted ones.
    allowed = spec.get("filters") or set()
    safe_filters = {}
    for k, v in filters.items():
        if k in allowed and v not in (None, ""):
            if re.fullmatch(r"[A-Za-z0-9_\-:,\.]+", str(v)):
                safe_filters[k] = str(v)
    if safe_filters:
        template = f"{template}?{urlencode(safe_filters)}"
    return template


def get_permission_for_target(target: str) -> Optional[Permission]:
    spec = NAV_TARGETS.get(target)
    return spec.get("perm") if spec else None


# ----------------------------------------------------------------------------
# Helpers: filtered-list resolvers for Phase 2 suggested_actions
# ----------------------------------------------------------------------------

def route_overdue_invoices() -> str:
    return build_safe_route("invoices_list", filters={"status": "overdue"}) or "/invoices"


def route_orders_due_between(start: date, end: date) -> str:
    return (
        build_safe_route("orders_list", filters={"due_from": start.isoformat(), "due_to": end.isoformat()})
        or "/orders"
    )


def route_pending_approvals() -> str:
    return build_safe_route("approvals", filters={"status": "pending"}) or "/approvals"


# ----------------------------------------------------------------------------
# Related-record navigation
# ----------------------------------------------------------------------------

async def resolve_related_record(
    db, tenant_id: str, source_type: str, source_id: str, target_type: str
) -> Optional[Dict[str, Any]]:
    """Follow a relationship from one record to another.

    Supported pairs:
      order -> customer, order -> invoice, order -> documents
      invoice -> order, invoice -> customer
      job_ticket -> order
      customer -> invoices (filtered list), customer -> orders (filtered list)
      employee -> time_entries (payroll page)
    """
    if not source_type or not source_id or not target_type:
        return None

    if source_type == "order" and target_type == "customer":
        order = await db.orders.find_one({"id": source_id, "tenant_id": tenant_id}, {"_id": 0, "customer_id": 1, "customer_name": 1})
        if order and order.get("customer_id"):
            return {
                "target_type": "customer",
                "record_id": order["customer_id"],
                "label": f"Customer: {order.get('customer_name') or ''}".strip(),
                "route": build_safe_route("customers_list"),
            }

    if source_type == "order" and target_type == "invoice":
        inv = await db.invoices.find_one({"order_id": source_id, "tenant_id": tenant_id}, {"_id": 0, "id": 1, "invoice_number": 1})
        if inv:
            return {
                "target_type": "invoice",
                "record_id": inv["id"],
                "label": f"Invoice {inv.get('invoice_number')}",
                "route": build_safe_route("invoices_list"),
            }

    if source_type == "invoice" and target_type == "order":
        inv = await db.invoices.find_one({"id": source_id, "tenant_id": tenant_id}, {"_id": 0, "order_id": 1})
        if inv and inv.get("order_id"):
            return {
                "target_type": "order",
                "record_id": inv["order_id"],
                "label": f"Order ({inv['order_id']})",
                "route": build_safe_route("order_detail", params={"id": inv["order_id"]}),
            }

    if source_type == "invoice" and target_type == "customer":
        inv = await db.invoices.find_one({"id": source_id, "tenant_id": tenant_id}, {"_id": 0, "customer_id": 1, "customer_name": 1})
        if inv and inv.get("customer_id"):
            return {
                "target_type": "customer",
                "record_id": inv["customer_id"],
                "label": f"Customer: {inv.get('customer_name') or ''}".strip(),
                "route": build_safe_route("customers_list"),
            }

    if source_type == "job_ticket" and target_type == "order":
        t = await db.job_tickets.find_one({"id": source_id, "tenant_id": tenant_id}, {"_id": 0, "order_id": 1})
        if t and t.get("order_id"):
            return {
                "target_type": "order",
                "record_id": t["order_id"],
                "label": f"Order ({t['order_id']})",
                "route": build_safe_route("order_detail", params={"id": t["order_id"]}),
            }

    if source_type == "customer" and target_type == "invoices":
        return {
            "target_type": "invoices_list",
            "record_id": None,
            "label": "Customer's invoices",
            "route": build_safe_route("invoices_list", filters={"customer_id": source_id}),
        }

    if source_type == "customer" and target_type == "orders":
        return {
            "target_type": "orders_list",
            "record_id": None,
            "label": "Customer's orders",
            "route": build_safe_route("orders_list", filters={"customer_id": source_id}),
        }

    if source_type == "employee" and target_type == "time_entries":
        return {
            "target_type": "timesheets",
            "record_id": None,
            "label": "Time entries",
            "route": build_safe_route("timesheets"),  # timesheets page; filtering by employee handled in-page
        }

    return None


# ----------------------------------------------------------------------------
# Lookup / ambiguity
# ----------------------------------------------------------------------------

async def lookup_customers_by_name(db, tenant_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    rx = {"$regex": re.escape(q), "$options": "i"}
    results = await db.customers.find(
        {"tenant_id": tenant_id, "$or": [{"name": rx}, {"company": rx}]},
        {"_id": 0, "id": 1, "name": 1, "company": 1},
    ).limit(limit).to_list(limit)
    return results


async def lookup_order_by_number(db, tenant_id: str, order_number: str) -> Optional[Dict[str, Any]]:
    if not order_number:
        return None
    on = order_number.strip().upper()
    order = await db.orders.find_one(
        {"tenant_id": tenant_id, "order_number": {"$regex": f"^{re.escape(on)}$", "$options": "i"}},
        {"_id": 0, "id": 1, "order_number": 1, "customer_name": 1},
    )
    return order


async def lookup_employees_by_name(db, tenant_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    q = (query or "").strip()
    if not q:
        return []
    rx = {"$regex": re.escape(q), "$options": "i"}
    return await db.employees.find(
        {"tenant_id": tenant_id, "$or": [{"name": rx}, {"first_name": rx}, {"last_name": rx}]},
        {"_id": 0, "id": 1, "name": 1, "first_name": 1, "last_name": 1},
    ).limit(limit).to_list(limit)
