"""
Daily Digest Routes

Endpoints for the morning digest email:
- Preview digest content
- Send digest manually
- Manage digest settings (enable, schedule, recipients)
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from pydantic import BaseModel

from server import db, logger, get_current_active_user
from models import UserInDB
from services.email_service import email_service


router = APIRouter(prefix="/digest", tags=["Daily Digest"])


class DigestSettings(BaseModel):
    enabled: bool = False
    schedule_time: str = "07:00"  # HH:MM in 24h format
    recipients: List[str] = []  # list of email addresses


class DigestSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    schedule_time: Optional[str] = None
    recipients: Optional[List[str]] = None


# ==================== HELPERS ====================

async def compile_digest_data(tenant_id: str) -> dict:
    """Compile all digest data for a tenant."""
    today = datetime.now(timezone.utc).date()
    today_str = today.isoformat()
    yesterday = (today - timedelta(days=1))
    yesterday_str = yesterday.isoformat()

    # 1. Employees scheduled today
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

    schedule_map = {}
    for sched in schedules:
        emp_id = sched.get("employee_id")
        shift = sched.get("shifts", {}).get(day_key)
        if shift and (shift.get("start") or shift.get("end")):
            schedule_map[emp_id] = shift

    scheduled_employees = []
    for emp in employees:
        if emp.get("id") in schedule_map:
            shift = schedule_map[emp["id"]]
            scheduled_employees.append({
                "name": emp.get("name", "Unknown"),
                "shift": f"{shift.get('start', '')} - {shift.get('end', '')}"
            })

    # 2. Overdue orders/invoices
    overdue_invoices = await db.invoices.find(
        {"tenant_id": tenant_id, "status": "overdue"},
        {"_id": 0, "id": 1, "customer_name": 1, "total": 1, "due_date": 1}
    ).to_list(50)

    # 3. Jobs scheduled/due today
    jobs_today = await db.jobs.find({
        "tenant_id": tenant_id,
        "due_date": {"$lte": today_str},
        "status": {"$nin": ["complete", "delivered", "cancelled"]}
    }, {"_id": 0, "id": 1, "name": 1, "customer_id": 1, "status": 1, "due_date": 1}).to_list(50)

    jobs_with_customers = []
    for job in jobs_today:
        customer = await db.customers.find_one(
            {"id": job.get("customer_id"), "tenant_id": tenant_id},
            {"_id": 0, "name": 1}
        )
        jobs_with_customers.append({
            "name": job.get("name", "Unknown"),
            "customer_name": customer.get("name", "Unknown") if customer else "Unknown",
            "status": job.get("status", ""),
            "due_date": job.get("due_date", ""),
            "is_overdue": job.get("due_date", "") < today_str
        })

    # 4. Pending approvals
    pending_approvals = await db.artwork_proofs.count_documents(
        {"tenant_id": tenant_id, "status": "pending"}
    )

    # 5. Yesterday's revenue
    yesterday_invoices = await db.invoices.find({
        "tenant_id": tenant_id,
        "status": "paid",
        "paid_date": {"$gte": f"{yesterday_str}T00:00:00", "$lte": f"{yesterday_str}T23:59:59"}
    }, {"_id": 0, "total": 1}).to_list(500)
    yesterday_revenue = sum(inv.get("total", 0) for inv in yesterday_invoices)

    # 6. Unread messages
    unread_count = await db.conversations.count_documents(
        {"tenant_id": tenant_id, "shop_unread_count": {"$gt": 0}}
    )
    low_stock_count = 0
    inventory_items = await db.inventory_items.find(
        {"tenant_id": tenant_id, "is_active": {"$ne": False}, "reorder_point": {"$gt": 0}},
        {"_id": 0, "id": 1, "reorder_point": 1},
    ).to_list(10000)
    if inventory_items:
        from services.inventory_service import item_balances
        balances = await item_balances(db, tenant_id, [item["id"] for item in inventory_items])
        low_stock_count = sum(
            1 for item in inventory_items
            if balances.get(item["id"], {}).get("available", 0) <= float(item.get("reorder_point", 0))
        )
    inventory_shortages = await db.inventory_shortages.count_documents({"tenant_id": tenant_id, "status": "open"})

    # Get tenant info
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0, "company_name": 1})
    company_name = tenant.get("company_name", "Your Shop") if tenant else "Your Shop"

    return {
        "date": today_str,
        "day_name": today.strftime("%A, %B %d, %Y"),
        "company_name": company_name,
        "scheduled_employees": scheduled_employees,
        "scheduled_count": len(scheduled_employees),
        "total_employees": len(employees),
        "overdue_invoices": overdue_invoices,
        "overdue_count": len(overdue_invoices),
        "overdue_total": sum(inv.get("total", 0) for inv in overdue_invoices),
        "jobs_today": jobs_with_customers,
        "jobs_today_count": len(jobs_with_customers),
        "pending_approvals": pending_approvals,
        "yesterday_revenue": yesterday_revenue,
        "unread_messages": unread_count,
        "low_stock_count": low_stock_count,
        "inventory_shortages": inventory_shortages,
    }


def render_digest_html(data: dict) -> str:
    """Render the digest data into a styled HTML email."""
    scheduled_rows = ""
    for emp in data["scheduled_employees"]:
        scheduled_rows += f'<tr><td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{emp["name"]}</td><td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;color:#6b7280;">{emp["shift"]}</td></tr>'

    if not scheduled_rows:
        scheduled_rows = '<tr><td colspan="2" style="padding:12px;color:#9ca3af;text-align:center;">No employees scheduled today</td></tr>'

    jobs_rows = ""
    for job in data["jobs_today"]:
        badge_color = "#EF4444" if job["is_overdue"] else "#F59E0B"
        badge_text = "OVERDUE" if job["is_overdue"] else job["status"].replace("_", " ").upper()
        jobs_rows += f'''<tr>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{job["name"]}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;color:#6b7280;">{job["customer_name"]}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;"><span style="background:{badge_color};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">{badge_text}</span></td>
        </tr>'''

    if not jobs_rows:
        jobs_rows = '<tr><td colspan="3" style="padding:12px;color:#9ca3af;text-align:center;">No jobs due today</td></tr>'

    overdue_rows = ""
    for inv in data["overdue_invoices"][:5]:
        overdue_rows += f'<tr><td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;">{inv.get("customer_name", "Unknown")}</td><td style="padding:8px 12px;border-bottom:1px solid #e5e7eb;color:#EF4444;font-weight:600;">${inv.get("total", 0):,.2f}</td></tr>'

    overdue_section = ""
    if data["overdue_count"] > 0:
        overdue_section = f'''
        <div style="margin-bottom:24px;">
            <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:16px;">
                <h3 style="margin:0 0 12px;color:#991B1B;font-size:15px;">Overdue Invoices ({data["overdue_count"]})</h3>
                <p style="margin:0 0 12px;color:#991B1B;font-size:13px;">Total overdue: <strong>${data["overdue_total"]:,.2f}</strong></p>
                <table style="width:100%;border-collapse:collapse;font-size:13px;">
                    <thead><tr style="background:#FEE2E2;"><th style="padding:8px 12px;text-align:left;">Customer</th><th style="padding:8px 12px;text-align:left;">Amount</th></tr></thead>
                    <tbody>{overdue_rows}</tbody>
                </table>
            </div>
        </div>'''

    return f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<div style="max-width:600px;margin:0 auto;padding:20px;">
    <!-- Header -->
    <div style="background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);padding:24px 28px;border-radius:12px 12px 0 0;">
        <h1 style="margin:0;color:#fff;font-size:22px;">Good Morning!</h1>
        <p style="margin:4px 0 0;color:#94a3b8;font-size:14px;">{data["day_name"]} &mdash; {data["company_name"]}</p>
    </div>

    <!-- Stats Strip -->
    <div style="background:#fff;padding:16px 28px;display:flex;border-bottom:1px solid #e5e7eb;">
        <table style="width:100%;border-collapse:collapse;">
            <tr>
                <td style="text-align:center;padding:8px;">
                    <div style="font-size:24px;font-weight:700;color:#0f172a;">{data["scheduled_count"]}</div>
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Scheduled</div>
                </td>
                <td style="text-align:center;padding:8px;">
                    <div style="font-size:24px;font-weight:700;color:#0f172a;">{data["jobs_today_count"]}</div>
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Jobs Due</div>
                </td>
                <td style="text-align:center;padding:8px;">
                    <div style="font-size:24px;font-weight:700;color:#0f172a;">{data["pending_approvals"]}</div>
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Approvals</div>
                </td>
                <td style="text-align:center;padding:8px;">
                    <div style="font-size:24px;font-weight:700;color:#22c55e;">${data["yesterday_revenue"]:,.2f}</div>
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Yesterday Rev</div>
                </td>
                <td style="text-align:center;padding:8px;">
                    <div style="font-size:24px;font-weight:700;color:#3b82f6;">{data["unread_messages"]}</div>
                    <div style="font-size:11px;color:#6b7280;text-transform:uppercase;">Messages</div>
                </td>
            </tr>
        </table>
    </div>

    <!-- Content -->
    <div style="background:#fff;padding:24px 28px;">

        {overdue_section}

        <!-- Jobs Due Today -->
        <div style="margin-bottom:24px;">
            <h3 style="margin:0 0 12px;color:#0f172a;font-size:15px;">Jobs Due Today ({data["jobs_today_count"]})</h3>
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead><tr style="background:#f8fafc;"><th style="padding:8px 12px;text-align:left;color:#6b7280;">Job</th><th style="padding:8px 12px;text-align:left;color:#6b7280;">Customer</th><th style="padding:8px 12px;text-align:left;color:#6b7280;">Status</th></tr></thead>
                <tbody>{jobs_rows}</tbody>
            </table>
        </div>

        <!-- Team Schedule -->
        <div style="margin-bottom:24px;">
            <h3 style="margin:0 0 12px;color:#0f172a;font-size:15px;">Team Schedule ({data["scheduled_count"]}/{data["total_employees"]} employees)</h3>
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
                <thead><tr style="background:#f8fafc;"><th style="padding:8px 12px;text-align:left;color:#6b7280;">Employee</th><th style="padding:8px 12px;text-align:left;color:#6b7280;">Shift</th></tr></thead>
                <tbody>{scheduled_rows}</tbody>
            </table>
        </div>

    </div>

    <!-- Footer -->
    <div style="background:#f8fafc;padding:16px 28px;border-radius:0 0 12px 12px;border-top:1px solid #e5e7eb;text-align:center;">
        <p style="margin:0;color:#9ca3af;font-size:12px;">Sent by SignGuy AI &bull; Daily Digest</p>
        <p style="margin:4px 0 0;color:#9ca3af;font-size:11px;">Manage digest settings in your app under Settings &gt; Daily Digest</p>
    </div>
</div>
</body>
</html>'''


# ==================== ENDPOINTS ====================

@router.get("/preview")
async def preview_digest(current_user: UserInDB = Depends(get_current_active_user)):
    """Preview the daily digest content without sending."""
    data = await compile_digest_data(current_user.tenant_id)
    return data


@router.post("/send")
async def send_digest_now(
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Manually trigger sending the daily digest email."""
    tenant_id = current_user.tenant_id

    # Get digest settings to find recipients
    settings = await db.digest_settings.find_one(
        {"tenant_id": tenant_id}, {"_id": 0}
    )

    recipients = []
    if settings and settings.get("recipients"):
        recipients = settings["recipients"]
    else:
        # Default: send to the current user
        recipients = [current_user.email]

    # Compile and send
    data = await compile_digest_data(tenant_id)
    html = render_digest_html(data)
    subject = f"Daily Digest — {data['day_name']} | {data['company_name']}"

    results = []
    for email_addr in recipients:
        result = await email_service.send_email(
            to_email=email_addr,
            subject=subject,
            html_content=html,
            tenant_id=tenant_id
        )
        results.append({"email": email_addr, "success": result.get("success", False)})

    # Log the digest send
    await db.digest_logs.insert_one({
        "tenant_id": tenant_id,
        "sent_at": datetime.now(timezone.utc).isoformat(),
        "recipients": recipients,
        "results": results,
        "triggered_by": current_user.email,
        "type": "manual"
    })

    success_count = sum(1 for r in results if r["success"])
    return {
        "message": f"Digest sent to {success_count}/{len(recipients)} recipients",
        "results": results
    }


@router.get("/settings")
async def get_digest_settings(current_user: UserInDB = Depends(get_current_active_user)):
    """Get digest settings for the current tenant."""
    settings = await db.digest_settings.find_one(
        {"tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not settings:
        return {"enabled": False, "schedule_time": "07:00", "recipients": []}
    return {
        "enabled": settings.get("enabled", False),
        "schedule_time": settings.get("schedule_time", "07:00"),
        "recipients": settings.get("recipients", []),
    }


@router.put("/settings")
async def update_digest_settings(
    input: DigestSettingsUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update digest settings for the current tenant."""
    tenant_id = current_user.tenant_id
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    existing = await db.digest_settings.find_one({"tenant_id": tenant_id})
    if existing:
        await db.digest_settings.update_one(
            {"tenant_id": tenant_id}, {"$set": update_data}
        )
    else:
        update_data["tenant_id"] = tenant_id
        update_data.setdefault("enabled", False)
        update_data.setdefault("schedule_time", "07:00")
        update_data.setdefault("recipients", [])
        await db.digest_settings.insert_one(update_data)

    settings = await db.digest_settings.find_one(
        {"tenant_id": tenant_id}, {"_id": 0}
    )
    return {
        "enabled": settings.get("enabled", False),
        "schedule_time": settings.get("schedule_time", "07:00"),
        "recipients": settings.get("recipients", []),
    }


@router.get("/history")
async def get_digest_history(
    limit: int = 10,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get history of sent digests."""
    logs = await db.digest_logs.find(
        {"tenant_id": current_user.tenant_id}, {"_id": 0}
    ).sort("sent_at", -1).to_list(limit)
    return logs
