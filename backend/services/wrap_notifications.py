"""
Wrap Command Center — Phase 2F follow-up: shop email notifications when a
customer takes a portal action.

Reuses the existing SendGrid-backed ``services.email_service.EmailService``.
This module is a thin presentation layer that builds the subject/body for each
of the 6 wrap portal actions and dispatches via ``EmailService.send_email``.

Design rules:
- NEVER block the customer action — wrap the dispatch in try/except and log.
- Resolve shop recipient with a tenant-field priority list.
- Strip internal data (profit/margin/cost/internal notes) — only safe fields are
  included in the email body.
- The caller is responsible for de-duplication; only invoke this helper when
  the wrap_data action actually transitions to a new state.
"""
import html as _html
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from server import db, logger
from services.email_service import EmailService


def _resolve_shop_email(tenant: dict) -> Optional[str]:
    """Pick the best shop recipient in priority order."""
    if not tenant:
        return None
    for key in ("notification_email", "business_email", "email", "owner_email"):
        val = (tenant.get(key) or "").strip()
        if val and "@" in val:
            return val
    return None


def _shop_name(tenant: dict) -> str:
    return (
        (tenant or {}).get("business_name")
        or (tenant or {}).get("company_name")
        or (tenant or {}).get("name")
        or "Your Sign Shop"
    )


def _customer_display(customer: dict) -> str:
    if not customer:
        return "A customer"
    name = (customer.get("name") or "").strip()
    if name:
        return name
    full = " ".join(
        b for b in [customer.get("first_name"), customer.get("last_name")] if b
    ).strip()
    return full or customer.get("email") or "A customer"


def _vehicle_summary(wrap_doc: dict) -> str:
    v = (wrap_doc or {}).get("vehicle_info") or {}
    bits = [v.get("year"), v.get("make"), v.get("model"), v.get("color")]
    return " ".join(b for b in bits if b).strip() or "Vehicle"


ACTION_META = {
    "proof_approved": {
        "subject_label": "Wrap Proof Approved",
        "headline": "Customer approved the wrap proof",
        "color": "#10b981",
    },
    "revision_requested": {
        "subject_label": "Wrap Revision Requested",
        "headline": "Customer requested an artwork revision",
        "color": "#f59e0b",
    },
    "contract_signed": {
        "subject_label": "Wrap Contract Signed",
        "headline": "Customer signed the wrap contract",
        "color": "#4338ca",
    },
    "quote_approved": {
        "subject_label": "Wrap Quote Approved",
        "headline": "Customer approved the wrap quote",
        "color": "#0ea5e9",
    },
    "inspection_acknowledged": {
        "subject_label": "Wrap Inspection Acknowledged",
        "headline": "Customer acknowledged the pre-install inspection",
        "color": "#7c3aed",
    },
    "aftercare_acknowledged": {
        "subject_label": "Wrap Aftercare Acknowledged",
        "headline": "Customer acknowledged the aftercare instructions",
        "color": "#0d9488",
    },
}


def _render_html(
    *,
    shop_name: str,
    headline: str,
    color: str,
    customer_name: str,
    customer_email: str,
    order_number: str,
    vehicle_summary: str,
    wrap_type: str,
    item_name: str,
    timestamp: str,
    extra_rows: Optional[list] = None,
    order_link: Optional[str] = None,
    portal_link: Optional[str] = None,
    admin_messages_link: Optional[str] = None,
) -> str:
    """Build a simple inline-styled HTML email body."""
    rows_html = "".join(
        f'<tr><td style="color:#6b7280;padding:4px 8px;font-size:13px">{k}</td>'
        f'<td style="color:#111827;padding:4px 8px;font-size:13px;font-weight:500">{v}</td></tr>'
        for k, v in [
            ("Customer", customer_name),
            ("Email", customer_email or "—"),
            ("Order #", order_number or "—"),
            ("Item", item_name or "—"),
            ("Wrap Type", wrap_type or "—"),
            ("Vehicle", vehicle_summary or "—"),
            ("Time", timestamp),
        ]
        + (extra_rows or [])
    )

    def _btn(href, label, primary=False):
        if not href:
            return ""
        bg = color if primary else "#ffffff"
        fg = "#ffffff" if primary else color
        border = color
        safe_href = _html.escape(str(href), quote=True)
        return (
            f'<a href="{safe_href}" style="display:inline-block;background:{bg};color:{fg};'
            f'border:1px solid {border};padding:9px 14px;border-radius:6px;'
            f'text-decoration:none;font-size:12px;font-weight:600;margin-right:6px;margin-top:6px">'
            f'{label}</a>'
        )

    buttons_html = ""
    if order_link or portal_link or admin_messages_link:
        buttons_html = (
            '<div style="margin:20px 0 0 0">'
            + _btn(order_link, "Open Order", primary=True)
            + _btn(portal_link, "Open Wrap Command Center")
            + _btn(admin_messages_link, "Respond in Admin Portal")
            + '</div>'
        )

    return f"""
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f8fafc;padding:24px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden">
    <div style="background:{color};color:#fff;padding:14px 20px;font-size:14px;font-weight:600;letter-spacing:0.02em">
      {shop_name}
    </div>
    <div style="padding:20px">
      <h2 style="margin:0 0 4px 0;color:#111827;font-size:18px">{headline}</h2>
      <p style="margin:0 0 16px 0;color:#6b7280;font-size:13px">Triggered from the Customer Portal.</p>
      <table style="border-collapse:collapse;width:100%">{rows_html}</table>
      {buttons_html}
    </div>
    <div style="padding:12px 20px;background:#f9fafb;color:#9ca3af;font-size:11px;border-top:1px solid #f1f5f9">
      You are receiving this email because customer-portal notifications are enabled for {shop_name}.
    </div>
  </div>
</div>
""".strip()


async def send_wrap_portal_action_notification(
    *,
    tenant_id: str,
    ticket_id: str,
    action_key: str,
    extra: Optional[Dict[str, Any]] = None,
) -> dict:
    """Fire-and-log shop notification. NEVER raises — always returns a status
    dict. Caller can ignore the return value.

    action_key: one of ACTION_META keys.
    extra: per-action extra rows (e.g. {"Revision notes": "..."}).
    """
    extra = extra or {}
    meta = ACTION_META.get(action_key)
    if not meta:
        logger.warning(f"wrap-notify: unknown action_key={action_key}")
        return {"sent": False, "reason": "unknown_action"}

    try:
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0}) or {}
        shop_email = _resolve_shop_email(tenant)
        if not shop_email:
            logger.info(f"wrap-notify: no shop email on tenant {tenant_id} — skipping {action_key}")
            return {"sent": False, "reason": "no_shop_email"}

        ticket = await db.job_tickets.find_one(
            {"id": ticket_id, "tenant_id": tenant_id}, {"_id": 0}
        ) or {}
        order = {}
        if ticket.get("order_id"):
            order = await db.orders.find_one(
                {"id": ticket["order_id"], "tenant_id": tenant_id},
                {"_id": 0, "order_number": 1, "customer_id": 1, "id": 1},
            ) or {}
        customer = {}
        if order.get("customer_id"):
            customer = await db.customers.find_one(
                {"id": order["customer_id"], "tenant_id": tenant_id},
                {"_id": 0, "first_name": 1, "last_name": 1, "name": 1, "email": 1, "company": 1},
            ) or {}
        wrap_doc = await db.wrap_data.find_one(
            {"tenant_id": tenant_id, "ticket_id": ticket_id},
            {"_id": 0, "vehicle_info": 1, "wrap_type": 1},
        ) or {}

        order_number = order.get("order_number") or "—"
        customer_name = _customer_display(customer)
        customer_email = customer.get("email") or ""
        shop_name = _shop_name(tenant)
        item_name = ticket.get("item_name") or ticket.get("description") or "Wrap Item"
        wrap_type = wrap_doc.get("wrap_type") or ticket.get("item_category") or "Vehicle Wrap"
        vehicle = _vehicle_summary(wrap_doc)
        ts = datetime.now(timezone.utc).isoformat()

        portal_link = None
        order_link = None
        admin_messages_link = None
        # Best-effort deep links if a frontend URL is configured. We accept any
        # of: tenant.app_url, tenant.portal_url, env FRONTEND_URL, env
        # REACT_APP_BACKEND_URL (single-domain SPA setup).
        import os as _os
        app_url = (
            tenant.get("app_url")
            or tenant.get("portal_url")
            or _os.environ.get("FRONTEND_URL")
            or _os.environ.get("REACT_APP_BACKEND_URL")
            or ""
        ).rstrip("/")
        if app_url:
            if order.get("id"):
                order_link = f"{app_url}/orders/{order['id']}"
                portal_link = f"{app_url}/orders/{order['id']}/items/{ticket_id}/wrap-command-center"
            admin_messages_link = f"{app_url}/admin-portal"

        extra_rows = [(k, v) for k, v in extra.items()]
        subject = f"{meta['subject_label']} — Order #{order_number}"
        html = _render_html(
            shop_name=shop_name,
            headline=meta["headline"],
            color=meta["color"],
            customer_name=customer_name,
            customer_email=customer_email,
            order_number=order_number,
            vehicle_summary=vehicle,
            wrap_type=wrap_type,
            item_name=item_name,
            timestamp=ts,
            extra_rows=extra_rows,
            order_link=order_link,
            portal_link=portal_link,
            admin_messages_link=admin_messages_link,
        )

        result = await EmailService().send_email(
            to_email=shop_email,
            subject=subject,
            html_content=html,
            tenant_id=tenant_id,
        )
        if not result.get("success"):
            logger.warning(f"wrap-notify: send_email failed for {action_key}: {result}")
            return {"sent": False, "reason": "send_failed", "detail": result.get("error")}
        return {"sent": True, "to": shop_email}
    except Exception as exc:  # noqa: BLE001 — never propagate
        logger.warning(f"wrap-notify: dispatch failed for {action_key}: {exc}")
        return {"sent": False, "reason": "exception", "detail": str(exc)}
