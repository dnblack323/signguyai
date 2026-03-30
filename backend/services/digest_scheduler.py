"""
Digest Scheduler Service

Background scheduler that checks every minute whether any tenant's
daily digest email is due, and sends it automatically.
"""

import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from server import db, logger
from services.email_service import email_service


scheduler = AsyncIOScheduler()


async def check_and_send_digests():
    """Check all tenants' digest settings and send if it's time."""
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")

    try:
        # Find all enabled digests that match the current time
        settings_cursor = db.digest_settings.find(
            {"enabled": True, "schedule_time": current_time},
            {"_id": 0}
        )
        settings_list = await settings_cursor.to_list(500)

        for settings in settings_list:
            tenant_id = settings.get("tenant_id")
            recipients = settings.get("recipients", [])

            if not recipients:
                continue

            # Check if we already sent today for this tenant
            today_str = now.date().isoformat()
            already_sent = await db.digest_logs.find_one({
                "tenant_id": tenant_id,
                "sent_at": {"$regex": f"^{today_str}"},
                "type": "scheduled"
            })
            if already_sent:
                continue

            # Import here to avoid circular imports
            from routes.digest import compile_digest_data, render_digest_html

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

            # Log the scheduled send
            await db.digest_logs.insert_one({
                "tenant_id": tenant_id,
                "sent_at": now.isoformat(),
                "recipients": recipients,
                "results": results,
                "triggered_by": "scheduler",
                "type": "scheduled"
            })

            success_count = sum(1 for r in results if r["success"])
            logger.info(f"Scheduled digest for tenant {tenant_id}: sent to {success_count}/{len(recipients)}")

    except Exception as e:
        logger.error(f"Digest scheduler error: {e}")


def start_digest_scheduler():
    """Start the background scheduler."""
    scheduler.add_job(
        check_and_send_digests,
        "interval",
        minutes=1,
        id="digest_checker",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Digest scheduler started — checking every minute")


def stop_digest_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Digest scheduler stopped")
