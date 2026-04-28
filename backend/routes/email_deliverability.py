"""
SendGrid Event Webhook + Platform Admin Email Deliverability endpoints.

SendGrid Event Webhook payload format:
    [
      {
        "email": "user@example.com",
        "event": "delivered" | "bounce" | "deferred" | "dropped"
                 | "spamreport" | "open" | "click" | "unsubscribe" | "processed",
        "sg_message_id": "filterdrecv-...",
        "timestamp": 1234567890,
        "reason": "...",     # for bounce/dropped/deferred
        ...
      },
      ...
    ]

We update the matching `email_logs` document (matched by sg_message_id prefix)
with a refined `delivery_status`, append the event to `events[]`, and bump
`bounce_count` / `complaint_count` on the tenant for at-a-glance deliverability.
"""

from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request

from server import db, logger
from core_runtime import UserInDB
from routes.platform_admin import require_platform_admin


router = APIRouter(prefix="/platform-admin", tags=["Platform Admin - Email"])
sendgrid_webhook_router = APIRouter(tags=["SendGrid Webhook"])


# Map raw SendGrid event names to a normalized "delivery_status" we surface in the UI
TERMINAL_GOOD = {"delivered"}
TERMINAL_BAD = {"bounce", "dropped", "spamreport", "blocked"}
SOFT_FAIL = {"deferred"}
INFO = {"processed", "open", "click", "unsubscribe", "group_unsubscribe", "group_resubscribe"}


def _normalize_status(event_name: str, current_status: Optional[str]) -> str:
    """Decide what `delivery_status` should become for this event."""
    if event_name in TERMINAL_BAD:
        return event_name  # "bounce" | "dropped" | "spamreport" | "blocked"
    if event_name in TERMINAL_GOOD:
        return "delivered"
    if event_name in SOFT_FAIL:
        # Don't overwrite a terminal status with a soft-fail
        if current_status in TERMINAL_BAD or current_status == "delivered":
            return current_status or "deferred"
        return "deferred"
    # info events leave status unchanged
    return current_status or "sent"


@sendgrid_webhook_router.post("/webhook/sendgrid")
async def sendgrid_event_webhook(request: Request):
    """
    Public webhook endpoint for SendGrid Event Webhook callbacks.

    Configure in SendGrid: Settings → Mail Settings → Event Webhook → URL =
    https://<your-host>/api/webhook/sendgrid
    """
    try:
        events = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    if not isinstance(events, list):
        raise HTTPException(status_code=400, detail="Expected JSON array of events")

    processed = 0
    matched = 0
    for ev in events:
        try:
            sg_message_id = (ev.get("sg_message_id") or "").split(".")[0] or None
            event_name = (ev.get("event") or "").strip().lower()
            email = ev.get("email")
            if not event_name:
                continue

            event_doc = {
                "event": event_name,
                "email": email,
                "sg_message_id": sg_message_id,
                "reason": ev.get("reason"),
                "type": ev.get("type"),
                "status": ev.get("status"),
                "url": ev.get("url"),
                "timestamp": ev.get("timestamp"),
                "received_at": datetime.now(timezone.utc).isoformat(),
            }
            # Insert into events collection (mutates event_doc by adding _id)
            await db.email_events.insert_one(dict(event_doc))
            processed += 1

            if not sg_message_id:
                continue

            # Find matching email_log (sg_message_id stored exactly as we received it)
            log = await db.email_logs.find_one(
                {"sg_message_id": {"$regex": f"^{sg_message_id}"}},
                {"_id": 0, "id": 1, "delivery_status": 1, "tenant_id": 1},
            )
            if not log:
                continue
            matched += 1

            new_status = _normalize_status(event_name, log.get("delivery_status"))
            await db.email_logs.update_one(
                {"id": log["id"]},
                {
                    "$set": {"delivery_status": new_status},
                    "$push": {"events": event_doc},
                },
            )

            # Increment counters on the tenant for at-a-glance deliverability
            if log.get("tenant_id"):
                if event_name == "bounce":
                    await db.tenants.update_one(
                        {"id": log["tenant_id"]},
                        {"$inc": {"email_bounce_count": 1},
                         "$set": {"email_last_bounce_at": event_doc["received_at"]}},
                    )
                elif event_name == "spamreport":
                    await db.tenants.update_one(
                        {"id": log["tenant_id"]},
                        {"$inc": {"email_spam_count": 1},
                         "$set": {"email_last_spam_at": event_doc["received_at"]}},
                    )
                elif event_name == "delivered":
                    await db.tenants.update_one(
                        {"id": log["tenant_id"]},
                        {"$set": {"email_last_delivered_at": event_doc["received_at"]}},
                    )
        except Exception as e:
            logger.error(f"sendgrid_event_webhook: failed to process event: {e}")

    logger.info(f"SendGrid webhook processed {processed} events ({matched} matched)")
    return {"status": "ok", "processed": processed, "matched": matched}


@router.get("/email-logs/summary")
async def email_logs_summary(
    tenant_id: Optional[str] = None,
    since: Optional[str] = None,
    current_user: UserInDB = Depends(require_platform_admin),
):
    """
    High-level deliverability counts. Useful for the dashboard tile.
    Optionally filter by tenant_id and/or `since` (ISO datetime).
    """
    match: dict = {}
    if tenant_id:
        match["tenant_id"] = tenant_id
    if since:
        match["sent_at"] = {"$gte": since}

    pipeline = [
        {"$match": match} if match else {"$match": {}},
        {
            "$group": {
                "_id": "$delivery_status",
                "count": {"$sum": 1},
            }
        },
    ]
    rows = await db.email_logs.aggregate(pipeline).to_list(50)
    counts = {r["_id"]: r["count"] for r in rows if r["_id"]}
    total = sum(counts.values())
    bounced = counts.get("bounce", 0) + counts.get("dropped", 0) + counts.get("blocked", 0)
    complaints = counts.get("spamreport", 0)
    delivered = counts.get("delivered", 0)
    pending = counts.get("sent", 0) + counts.get("deferred", 0)
    failed = counts.get("failed", 0)

    return {
        "total": total,
        "delivered": delivered,
        "pending": pending,
        "bounced": bounced,
        "complaints": complaints,
        "failed": failed,
        "by_status": counts,
    }


@router.get("/email-logs")
async def list_email_logs(
    tenant_id: Optional[str] = None,
    delivery_status: Optional[str] = None,
    to_email: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 200,
    current_user: UserInDB = Depends(require_platform_admin),
):
    """
    Paginated email log list with filters.

    Filters: tenant_id, delivery_status (sent / delivered / bounce / dropped /
    spamreport / deferred / blocked / failed), to_email (substring), since/until.
    """
    limit = max(1, min(limit, 500))
    query: dict = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    if delivery_status:
        query["delivery_status"] = delivery_status
    if to_email:
        query["to_email"] = {"$regex": to_email, "$options": "i"}
    if since or until:
        sent_filter: dict = {}
        if since:
            sent_filter["$gte"] = since
        if until:
            sent_filter["$lte"] = until
        query["sent_at"] = sent_filter

    entries = await db.email_logs.find(
        query, {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(limit)

    return {
        "total_returned": len(entries),
        "limit": limit,
        "entries": entries,
    }
