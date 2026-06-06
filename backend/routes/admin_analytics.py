"""
Admin Analytics — platform_admin only.

Real data sources (existing collections):
  users, orders, quotes, webstores_v2, admin_audit_log

Forward-collecting data (new, starts empty):
  analytics_events — page views, sessions, frontend errors, bot signals

All GET endpoints require platform_admin role.
POST /api/analytics/event is public but validated.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from models.auth import UserInDB
from core_runtime import db, get_current_user

router = APIRouter(tags=["admin_analytics"])

# ── auth guard ────────────────────────────────────────────────────────────────

def require_platform_admin(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if current_user.role != "platform_admin":
        raise HTTPException(status_code=403, detail="Platform Admin access required")
    return current_user

# ── constants ─────────────────────────────────────────────────────────────────

BOT_UA_SIGNALS = [
    "bot", "crawler", "spider", "scraper", "scan", "slurp",
    "baiduspider", "googlebot", "bingbot", "yandexbot", "duckduckbot",
    "facebookexternalhit", "twitterbot", "python-requests", "go-http",
    "curl/", "wget/", "libwww", "java/", "okhttp", "axios", "node-fetch",
    "nmap", "nikto", "sqlmap", "masscan", "zgrab", "shodan",
]

SUSPICIOUS_PATHS = [
    "/wp-admin", "/phpmyadmin", "/.env", "/xmlrpc.php",
    "/wp-login", "/.git", "/backup", "/admin.php", "/shell",
    "/.well-known/acme", "//etc/passwd", "/cgi-bin", "/wp-content",
]


def is_bot_ua(ua: str) -> bool:
    if not ua:
        return True
    ua_lower = ua.lower()
    return any(s in ua_lower for s in BOT_UA_SIGNALS)


def _date_bounds(range_key: str, custom_start: Optional[str], custom_end: Optional[str]):
    now = datetime.now(timezone.utc)
    if range_key == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now
    elif range_key == "yesterday":
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59)
    elif range_key == "7d":
        start = now - timedelta(days=7)
        end = now
    elif range_key == "14d":
        start = now - timedelta(days=14)
        end = now
    elif range_key == "custom" and custom_start:
        start = datetime.fromisoformat(custom_start.replace("Z", "+00:00"))
        end_raw = custom_end or now.isoformat()
        end = datetime.fromisoformat(end_raw.replace("Z", "+00:00"))
    else:  # default 30d
        start = now - timedelta(days=30)
        end = now
    return start.isoformat(), end.isoformat()


# ── Ingest endpoint (public) ──────────────────────────────────────────────────

class AnalyticsEvent(BaseModel):
    event_type: str
    session_id: str
    visitor_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    route: Optional[str] = None
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[dict] = None


@router.post("/analytics/event")
async def ingest_event(event: AnalyticsEvent, request: Request):
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else None)
    ua = event.user_agent or request.headers.get("user-agent", "")

    doc = {
        "id": str(uuid.uuid4()),
        "event_type": event.event_type[:64],
        "session_id": event.session_id[:64],
        "visitor_id": event.visitor_id[:64],
        "user_id": event.user_id,
        "tenant_id": event.tenant_id,
        "route": (event.route or "")[:256],
        "referrer": (event.referrer or "")[:512],
        "user_agent": ua[:512],
        "ip_address": (ip or "")[:64],
        "is_bot": is_bot_ua(ua),
        "is_suspicious": any(p in (event.route or "") for p in SUSPICIOUS_PATHS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": event.metadata or {},
    }
    await db.analytics_events.insert_one(doc)
    return {"ok": True}


# ── Overview endpoint ─────────────────────────────────────────────────────────

@router.get("/admin/analytics/overview")
async def analytics_overview(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)
    date_filter = {"$gte": start, "$lte": end}

    # ── Business metrics (existing collections, real data) ─────────────────
    new_users     = await db.users.count_documents({"created_at": date_filter})
    new_orders    = await db.orders.count_documents({"date_created": date_filter})
    new_quotes    = await db.quotes.count_documents({"created_at": date_filter})
    new_webstores = await db.webstores_v2.count_documents({"created_at": date_filter})
    audit_actions = await db.admin_audit_log.count_documents({"created_at": date_filter})

    total_users     = await db.users.count_documents({})
    total_orders    = await db.orders.count_documents({})
    total_webstores = await db.webstores_v2.count_documents({})

    # ── Forward-collecting (analytics_events) ─────────────────────────────
    ev_filter = {"timestamp": date_filter}
    total_events   = await db.analytics_events.count_documents(ev_filter)
    session_ids    = await db.analytics_events.distinct("session_id", ev_filter)
    visitor_ids    = await db.analytics_events.distinct("visitor_id", ev_filter)
    total_sessions = len(session_ids)
    total_visitors = len(visitor_ids)

    logged_in_vis = await db.analytics_events.count_documents(
        {**ev_filter, "user_id": {"$ne": None, "$exists": True}}
    )
    anon_vis    = total_events - logged_in_vis
    bot_events  = await db.analytics_events.count_documents({**ev_filter, "is_bot": True})
    error_events = await db.analytics_events.count_documents(
        {**ev_filter, "event_type": {"$in": ["error", "api_error", "frontend_error"]}}
    )
    page_views = await db.analytics_events.count_documents(
        {**ev_filter, "event_type": "page_view"}
    )

    avg_req_session = round(total_events / total_sessions, 1) if total_sessions > 0 else 0

    return {
        "new_users":       new_users,
        "new_orders":      new_orders,
        "new_quotes":      new_quotes,
        "new_webstores":   new_webstores,
        "audit_actions":   audit_actions,
        "total_users":     total_users,
        "total_orders":    total_orders,
        "total_webstores": total_webstores,
        "total_events":        total_events,
        "total_sessions":      total_sessions,
        "total_visitors":      total_visitors,
        "logged_in_visits":    logged_in_vis,
        "anonymous_visits":    anon_vis,
        "bot_events":          bot_events,
        "error_events":        error_events,
        "page_views":          page_views,
        "avg_req_per_session": avg_req_session,
        "range":        range,
        "period_start": start,
        "period_end":   end,
    }


# ── Activity chart (time-series) ──────────────────────────────────────────────

@router.get("/admin/analytics/activity-chart")
async def analytics_activity_chart(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)
    start_dt = datetime.fromisoformat(start)
    end_dt   = datetime.fromisoformat(end)
    days     = max(1, (end_dt - start_dt).days)

    # Cap at 30 buckets for readability
    step = max(1, days // 30)
    buckets = []
    current = start_dt
    while current <= end_dt:
        day_start = current.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        day_end   = current.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        df = {"$gte": day_start, "$lte": day_end}

        orders    = await db.orders.count_documents({"date_created": df})
        quotes    = await db.quotes.count_documents({"created_at": df})
        webstores = await db.webstores_v2.count_documents({"created_at": df})
        users     = await db.users.count_documents({"created_at": df})
        events    = await db.analytics_events.count_documents({"timestamp": df})
        pv        = await db.analytics_events.count_documents({"timestamp": df, "event_type": "page_view"})
        errors    = await db.analytics_events.count_documents(
            {"timestamp": df, "event_type": {"$in": ["error", "api_error", "frontend_error"]}}
        )

        buckets.append({
            "date":       current.strftime("%b %d"),
            "orders":     orders,
            "quotes":     quotes,
            "webstores":  webstores,
            "new_users":  users,
            "events":     events,
            "page_views": pv,
            "errors":     errors,
        })
        current += timedelta(days=step)

    return {"days": buckets}


# ── User activity ─────────────────────────────────────────────────────────────

@router.get("/admin/analytics/users")
async def analytics_users(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    limit: int = 100,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)
    date_filter = {"$gte": start, "$lte": end}

    raw_users = await db.users.find(
        {"role": {"$ne": "platform_admin"}},
        {"_id": 0, "hashed_password": 0},
    ).sort("created_at", -1).limit(limit).to_list(limit)

    result = []
    for u in raw_users:
        uid       = u.get("id", "")
        tenant_id = u.get("tenant_id", "")

        orders_count    = await db.orders.count_documents({"tenant_id": tenant_id, "date_created": date_filter}) if tenant_id else 0
        quotes_count    = await db.quotes.count_documents({"tenant_id": tenant_id, "created_at": date_filter}) if tenant_id else 0
        webstores_count = await db.webstores_v2.count_documents({"tenant_id": tenant_id, "created_at": date_filter}) if tenant_id else 0
        audit_count     = await db.admin_audit_log.count_documents({"actor_user_id": uid, "created_at": date_filter})
        pv_count        = await db.analytics_events.count_documents({"user_id": uid, "event_type": "page_view", "timestamp": date_filter})

        result.append({
            "id":           uid,
            "full_name":    u.get("full_name", ""),
            "email":        u.get("email", ""),
            "role":         u.get("role", ""),
            "company_name": u.get("company_name", ""),
            "tenant_id":    tenant_id,
            "is_active":    u.get("is_active", True),
            "created_at":   u.get("created_at", ""),
            "orders":       orders_count,
            "quotes":       quotes_count,
            "webstores":    webstores_count,
            "admin_actions": audit_count,
            "page_views":   pv_count,
        })

    return {"users": result, "total": len(result)}


# ── Top routes ────────────────────────────────────────────────────────────────

@router.get("/admin/analytics/routes")
async def analytics_routes(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)

    pipeline = [
        {"$match": {"timestamp": {"$gte": start, "$lte": end}, "event_type": "page_view"}},
        {"$group": {
            "_id": "$route",
            "requests":         {"$sum": 1},
            "unique_users":     {"$addToSet": "$user_id"},
            "unique_visitors":  {"$addToSet": "$visitor_id"},
            "last_accessed":    {"$max": "$timestamp"},
        }},
        {"$project": {
            "_id": 0,
            "route":            "$_id",
            "requests":         1,
            "unique_users":     {"$size": "$unique_users"},
            "unique_visitors":  {"$size": "$unique_visitors"},
            "last_accessed":    1,
        }},
        {"$sort": {"requests": -1}},
        {"$limit": 50},
    ]
    routes = await db.analytics_events.aggregate(pipeline).to_list(50)
    return {"routes": routes}


# ── Sessions ──────────────────────────────────────────────────────────────────

@router.get("/admin/analytics/sessions")
async def analytics_sessions(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    limit: int = 100,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)

    pipeline = [
        {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
        {"$group": {
            "_id":        "$session_id",
            "visitor_id": {"$first": "$visitor_id"},
            "user_id":    {"$first": "$user_id"},
            "ip_address": {"$first": "$ip_address"},
            "user_agent": {"$first": "$user_agent"},
            "referrer":   {"$first": "$referrer"},
            "first_seen": {"$min": "$timestamp"},
            "last_seen":  {"$max": "$timestamp"},
            "requests":   {"$sum": 1},
            "is_bot":     {"$first": "$is_bot"},
            "routes":     {"$addToSet": "$route"},
        }},
        {"$project": {
            "_id": 0,
            "session_id":  "$_id",
            "visitor_id":  1,
            "user_id":     1,
            "ip_address":  1,
            "user_agent":  1,
            "referrer":    1,
            "first_seen":  1,
            "last_seen":   1,
            "requests":    1,
            "is_logged_in": {"$cond": [{"$ifNull": ["$user_id", False]}, True, False]},
            "is_bot":      1,
            "route_count": {"$size": "$routes"},
        }},
        {"$sort": {"last_seen": -1}},
        {"$limit": limit},
    ]
    sessions = await db.analytics_events.aggregate(pipeline).to_list(limit)
    return {"sessions": sessions}


# ── Referrers ─────────────────────────────────────────────────────────────────

@router.get("/admin/analytics/referrers")
async def analytics_referrers(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)

    def classify(ref: str) -> str:
        if not ref:
            return "Direct"
        r = ref.lower()
        if "google" in r:
            return "Google"
        if "facebook" in r or "fb.com" in r:
            return "Facebook"
        if "instagram" in r:
            return "Instagram"
        if "twitter" in r or "t.co" in r:
            return "Twitter/X"
        if "linkedin" in r:
            return "LinkedIn"
        if "emergentagent" in r:
            return "Emergent Preview"
        if "localhost" in r or "127.0.0.1" in r:
            return "Internal/Test"
        if "mail" in r or "email" in r or "newsletter" in r:
            return "Email"
        return "Other"

    pipeline = [
        {"$match": {"timestamp": {"$gte": start, "$lte": end}}},
        {"$group": {
            "_id":             "$referrer",
            "requests":        {"$sum": 1},
            "unique_visitors": {"$addToSet": "$visitor_id"},
            "logged_in":       {"$sum": {"$cond": [{"$ifNull": ["$user_id", False]}, 1, 0]}},
        }},
        {"$project": {
            "_id": 0,
            "referrer":        "$_id",
            "requests":        1,
            "unique_visitors": {"$size": "$unique_visitors"},
            "logged_in":       1,
        }},
        {"$sort": {"requests": -1}},
        {"$limit": 200},
    ]
    raw = await db.analytics_events.aggregate(pipeline).to_list(200)

    grouped: dict = {}
    for row in raw:
        src = classify(row.get("referrer") or "")
        if src not in grouped:
            grouped[src] = {"source": src, "requests": 0, "unique_visitors": 0, "logged_in": 0}
        grouped[src]["requests"]        += row["requests"]
        grouped[src]["unique_visitors"] += row["unique_visitors"]
        grouped[src]["logged_in"]       += row["logged_in"]

    total_req = sum(v["requests"] for v in grouped.values()) or 1
    result = []
    for v in sorted(grouped.values(), key=lambda x: -x["requests"]):
        v["pct"] = round(v["requests"] / total_req * 100, 1)
        result.append(v)

    return {"referrers": result}


# ── Errors ────────────────────────────────────────────────────────────────────

@router.get("/admin/analytics/errors")
async def analytics_errors(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    limit: int = 100,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)
    err_types = ["error", "api_error", "frontend_error"]
    base_filter = {
        "timestamp":  {"$gte": start, "$lte": end},
        "event_type": {"$in": err_types},
    }

    pipeline = [
        {"$match": base_filter},
        {"$group": {
            "_id": {
                "event_type": "$event_type",
                "route":      "$route",
                "message":    {"$ifNull": ["$metadata.message", "Unknown"]},
            },
            "count":          {"$sum": 1},
            "last_occurred":  {"$max": "$timestamp"},
            "first_occurred": {"$min": "$timestamp"},
            "users":          {"$addToSet": "$user_id"},
        }},
        {"$project": {
            "_id": 0,
            "event_type":     "$_id.event_type",
            "route":          "$_id.route",
            "message":        "$_id.message",
            "count":          1,
            "last_occurred":  1,
            "first_occurred": 1,
            "affected_users": {"$size": "$users"},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ]
    errors = await db.analytics_events.aggregate(pipeline).to_list(limit)

    total_errors    = await db.analytics_events.count_documents(base_filter)
    frontend_errors = await db.analytics_events.count_documents({**base_filter, "event_type": "frontend_error"})
    api_errors      = await db.analytics_events.count_documents({**base_filter, "event_type": "api_error"})

    return {
        "errors":          errors,
        "total_errors":    total_errors,
        "frontend_errors": frontend_errors,
        "api_errors":      api_errors,
    }


# ── Suspicious / Bot traffic ──────────────────────────────────────────────────

@router.get("/admin/analytics/suspicious")
async def analytics_suspicious(
    range: str = "30d",
    custom_start: Optional[str] = None,
    custom_end: Optional[str] = None,
    _: UserInDB = Depends(require_platform_admin),
):
    start, end = _date_bounds(range, custom_start, custom_end)
    date_filter = {"timestamp": {"$gte": start, "$lte": end}}

    pipeline = [
        {"$match": {**date_filter, "$or": [{"is_bot": True}, {"is_suspicious": True}]}},
        {"$group": {
            "_id":         {"ip": "$ip_address", "ua": "$user_agent"},
            "requests":    {"$sum": 1},
            "session_ids": {"$addToSet": "$session_id"},
            "routes":      {"$addToSet": "$route"},
            "first_seen":  {"$min": "$timestamp"},
            "last_seen":   {"$max": "$timestamp"},
            "is_bot":      {"$first": "$is_bot"},
            "is_suspicious": {"$first": "$is_suspicious"},
        }},
        {"$project": {
            "_id": 0,
            "ip_address":    "$_id.ip",
            "user_agent":    "$_id.ua",
            "requests":      1,
            "session_count": {"$size": "$session_ids"},
            "route_count":   {"$size": "$routes"},
            "first_seen":    1,
            "last_seen":     1,
            "is_bot":        1,
            "is_suspicious": 1,
            "label": {"$cond": [
                "$is_bot",
                "Likely Bot",
                {"$cond": ["$is_suspicious", "Suspicious Path", "Flagged"]},
            ]},
        }},
        {"$sort": {"requests": -1}},
        {"$limit": 50},
    ]
    suspicious = await db.analytics_events.aggregate(pipeline).to_list(50)

    total_bot    = await db.analytics_events.count_documents({**date_filter, "is_bot": True})
    total_susp   = await db.analytics_events.count_documents({**date_filter, "is_suspicious": True})
    total_events = await db.analytics_events.count_documents(date_filter)

    return {
        "suspicious":       suspicious,
        "total_bot":        total_bot,
        "total_suspicious": total_susp,
        "total_events":     total_events,
        "bot_pct": round(total_bot / total_events * 100, 1) if total_events else 0,
    }
