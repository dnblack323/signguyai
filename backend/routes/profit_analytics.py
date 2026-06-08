from collections import defaultdict
from datetime import datetime, timezone, timedelta
import uuid
from io import BytesIO
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from core.auth_deps import get_current_active_user
from models import Permission, UserInDB

router = APIRouter(prefix="/profit-analytics", tags=["Profit Analytics"])

_db = None
_has_permission = None


def _get_db():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


def _get_has_permission():
    global _has_permission
    if _has_permission is None:
        from server import has_permission
        _has_permission = has_permission
    return _has_permission


class LazyDB:
    def __getattr__(self, name):
        return getattr(_get_db(), name)


db = LazyDB()

CATEGORY_LABELS = {
    "vehicle_wraps": "Vehicle Wraps",
    "vehicle_graphics": "Vehicle Wraps",
    "banners": "Banners",
    "digital_print": "Digital Prints",
    "rigid_signs": "Rigid Signs",
    "cut_vinyl": "Cut Vinyl",
    "apparel": "Apparel",
    "services": "Services",
    "promotional": "Promotional",
    "custom": "Custom / Miscellaneous",
}

BENCHMARK_FIELDS = {
    "vehicle_wraps": "average_sell_price_per_sqft",
    "vehicle_graphics": "average_sell_price_per_sqft",
    "banners": "average_sell_price_per_sqft",
    "digital_print": "average_sell_price_per_sqft",
    "rigid_signs": "average_sell_price_per_sqft",
    "cut_vinyl": "average_sell_price_per_sqft",
    "apparel": "average_sell_price_per_unit",
    "services": "average_sell_price_per_hour",
    "promotional": "average_sell_price_per_unit",
    "custom": "average_sell_price_per_unit",
}


class ProfitAnalyticsPreferences(BaseModel):
    simple_mode: bool = False
    widget_order: List[str] = Field(default_factory=lambda: [
        "revenue_trend",
        "profit_by_category",
        "top_customers",
        "low_margin_jobs",
        "average_job_value",
    ])
    enabled_widgets: Dict[str, bool] = Field(default_factory=lambda: {
        "revenue_trend": True,
        "profit_by_category": True,
        "top_customers": True,
        "low_margin_jobs": True,
        "average_job_value": True,
    })


def ensure_reporting_access(current_user: UserInDB):
    if current_user.role in ["owner", "admin"]:
        return
    if _get_has_permission()(current_user, Permission.FINANCIALS_VIEW):
        return
    raise HTTPException(status_code=403, detail="You do not have permission to view profit analytics")


def parse_date(date_value: Optional[str]) -> Optional[datetime]:
    if not date_value:
        return None
    try:
        return datetime.fromisoformat(date_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def resolve_date_range(range_key: str, start_date: Optional[str], end_date: Optional[str]) -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    if range_key == "30d":
        return now - timedelta(days=30), now
    if range_key == "90d":
        return now - timedelta(days=90), now
    if range_key == "this_year":
        return datetime(now.year, 1, 1, tzinfo=timezone.utc), now
    if range_key == "custom" and start_date and end_date:
        start = parse_date(start_date) or now - timedelta(days=30)
        end = parse_date(end_date) or now
        return start, end
    return now - timedelta(days=30), now


def snapshot_metric(snapshot: Dict[str, Any], *keys: str) -> float:
    for key in keys:
        if key in snapshot and snapshot[key] is not None:
            return float(snapshot[key])
    return 0.0


def get_measurement(item: Dict[str, Any], category_key: str) -> float:
    pricing_data = item.get("pricing_data") or {}
    snapshot = item.get("cost_snapshot") or {}
    breakdown = snapshot.get("breakdown") or {}
    if BENCHMARK_FIELDS.get(category_key) == "average_sell_price_per_sqft":
        if pricing_data.get("square_footage"):
            return float(pricing_data.get("square_footage"))
        if pricing_data.get("width_inches") and pricing_data.get("length_inches"):
            return round((float(pricing_data["width_inches"]) * float(pricing_data["length_inches"])) / 144, 2)
        return float(breakdown.get("square_feet") or 0)
    if BENCHMARK_FIELDS.get(category_key) == "average_sell_price_per_hour":
        return float(pricing_data.get("estimated_hours") or 0) or float(item.get("quantity") or 0)
    return float(item.get("quantity") or 0)


def estimate_benchmark_margin(item: Dict[str, Any], benchmarks: Dict[str, Any]) -> Optional[float]:
    category_key = item.get("category")
    benchmark_entry = benchmarks.get(category_key) or {}
    benchmark_field = BENCHMARK_FIELDS.get(category_key)
    benchmark_value = benchmark_entry.get(benchmark_field)
    if not benchmark_value:
        return None

    measure = get_measurement(item, category_key)
    if not measure:
        return None

    benchmark_revenue = float(benchmark_value) * measure
    total_cost = float(item.get("total_cost") or 0)
    if benchmark_revenue <= 0:
        return None
    return round(((benchmark_revenue - total_cost) / benchmark_revenue) * 100, 1)


async def load_dashboard_rows(tenant_id: str, start_dt: datetime, end_dt: datetime, category_filter: Optional[str]) -> List[Dict[str, Any]]:
    jobs = await db.jobs.find(
        {"tenant_id": tenant_id, "created_at": {"$gte": start_dt.isoformat(), "$lte": end_dt.isoformat()}},
        {"_id": 0}
    ).to_list(1000)
    customers = await db.customers.find({"tenant_id": tenant_id}, {"_id": 0, "id": 1, "name": 1}).to_list(1000)
    customers_by_id = {customer["id"]: customer.get("name", "Unknown") for customer in customers}

    job_ids = [job["id"] for job in jobs]
    job_items = await db.job_items.find({"job_id": {"$in": job_ids}}, {"_id": 0}).to_list(5000) if job_ids else []
    items_by_job = defaultdict(list)
    for item in job_items:
        items_by_job[item["job_id"]].append(item)

    pricing_config = await db.pricing_configuration.find_one({"tenant_id": tenant_id}, {"_id": 0}) or {}
    benchmarks = pricing_config.get("selling_price_benchmarks", {})

    rows = []
    for job in jobs:
      items = items_by_job.get(job["id"]) or job.get("line_items", [])
      for item in items:
        snapshot = item.get("cost_snapshot") or {}
        if not snapshot:
            continue

        category_key = item.get("pricing_category") or item.get("category") or "custom"
        canonical_category = category_key if category_key in CATEGORY_LABELS else "custom"
        if category_filter and canonical_category != category_filter:
            continue

        revenue = snapshot_metric(snapshot, "selling_price") or float(item.get("line_total") or item.get("total") or 0)
        total_cost = snapshot_metric(snapshot, "total_cost") or (
            snapshot_metric(snapshot, "material_cost") + snapshot_metric(snapshot, "labor_cost") + snapshot_metric(snapshot, "overhead_cost")
        )
        profit = snapshot_metric(snapshot, "profit", "profit_amount") or round(revenue - total_cost, 2)
        margin = snapshot_metric(snapshot, "profit_margin", "profit_margin_percent") or (round((profit / revenue) * 100, 1) if revenue else 0)

        row = {
            "job_id": job["id"],
            "job_name": job.get("name", "Untitled Job"),
            "customer_id": job.get("customer_id"),
            "customer_name": customers_by_id.get(job.get("customer_id"), "Unknown"),
            "category": canonical_category,
            "category_label": CATEGORY_LABELS.get(canonical_category, canonical_category.title()),
            "created_at": job.get("created_at"),
            "revenue": round(revenue, 2),
            "total_cost": round(total_cost, 2),
            "profit": round(profit, 2),
            "profit_margin": round(margin, 1),
        }
        benchmark_margin = estimate_benchmark_margin({**item, **row}, benchmarks)
        row["benchmark_margin"] = benchmark_margin
        row["underpriced"] = bool(benchmark_margin is not None and row["profit_margin"] < (benchmark_margin - 10))
        rows.append(row)

    return rows


def build_dashboard_payload(rows: List[Dict[str, Any]], range_key: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
    total_revenue = round(sum(row["revenue"] for row in rows), 2)
    total_profit = round(sum(row["profit"] for row in rows), 2)
    avg_job_value = round(total_revenue / max(len({row['job_id'] for row in rows}), 1), 2) if rows else 0
    avg_profit_margin = round((total_profit / total_revenue) * 100, 1) if total_revenue else 0

    grouped_by_category: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"revenue": 0.0, "total_cost": 0.0, "profit": 0.0, "jobs": 0})
    grouped_by_job: Dict[str, Dict[str, Any]] = {}
    grouped_by_customer: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"customer_name": "Unknown", "total_revenue": 0.0, "total_profit": 0.0, "jobs": set()})
    trend = defaultdict(lambda: {"revenue": 0.0, "profit": 0.0})

    for row in rows:
        category_bucket = grouped_by_category[row["category"]]
        category_bucket["revenue"] += row["revenue"]
        category_bucket["total_cost"] += row["total_cost"]
        category_bucket["profit"] += row["profit"]
        category_bucket["jobs"] += 1

        job_bucket = grouped_by_job.setdefault(row["job_id"], {
            "job_id": row["job_id"],
            "job_name": row["job_name"],
            "customer_name": row["customer_name"],
            "created_at": row["created_at"],
            "revenue": 0.0,
            "total_cost": 0.0,
            "profit": 0.0,
            "categories": defaultdict(float),
            "underpriced": False,
            "benchmark_margin": None,
        })
        job_bucket["revenue"] += row["revenue"]
        job_bucket["total_cost"] += row["total_cost"]
        job_bucket["profit"] += row["profit"]
        job_bucket["categories"][row["category_label"]] += row["revenue"]
        job_bucket["underpriced"] = job_bucket["underpriced"] or row["underpriced"]
        if row["benchmark_margin"] is not None:
            current_benchmark = job_bucket["benchmark_margin"] or row["benchmark_margin"]
            job_bucket["benchmark_margin"] = min(current_benchmark, row["benchmark_margin"])

        customer_bucket = grouped_by_customer[row["customer_id"]]
        customer_bucket["customer_name"] = row["customer_name"]
        customer_bucket["total_revenue"] += row["revenue"]
        customer_bucket["total_profit"] += row["profit"]
        customer_bucket["jobs"].add(row["job_id"])

        created_dt = parse_date(row["created_at"]) or datetime.now(timezone.utc)
        trend_key = created_dt.strftime("%Y-%m-%d") if range_key in ["30d", "90d"] else created_dt.strftime("%Y-%m")
        trend[trend_key]["revenue"] += row["revenue"]
        trend[trend_key]["profit"] += row["profit"]

    category_rows = []
    for category_key, bucket in grouped_by_category.items():
        revenue = round(bucket["revenue"], 2)
        profit = round(bucket["profit"], 2)
        category_rows.append({
            "category": category_key,
            "category_label": CATEGORY_LABELS.get(category_key, category_key.title()),
            "revenue": revenue,
            "total_cost": round(bucket["total_cost"], 2),
            "profit": profit,
            "average_margin": round((profit / revenue) * 100, 1) if revenue else 0,
            "job_count": bucket["jobs"],
        })

    job_rows = []
    for job in grouped_by_job.values():
        revenue = round(job["revenue"], 2)
        profit = round(job["profit"], 2)
        dominant_category = max(job["categories"].items(), key=lambda item: item[1])[0] if job["categories"] else "Mixed"
        job_rows.append({
            "job_id": job["job_id"],
            "job_name": job["job_name"],
            "customer_name": job["customer_name"],
            "category": dominant_category,
            "revenue": revenue,
            "total_cost": round(job["total_cost"], 2),
            "profit": profit,
            "profit_margin": round((profit / revenue) * 100, 1) if revenue else 0,
            "underpriced": job["underpriced"],
            "benchmark_margin": job["benchmark_margin"],
            "created_at": job["created_at"],
        })

    customer_rows = []
    for customer_id, bucket in grouped_by_customer.items():
        revenue = round(bucket["total_revenue"], 2)
        profit = round(bucket["total_profit"], 2)
        customer_rows.append({
            "customer_id": customer_id,
            "customer_name": bucket["customer_name"],
            "total_revenue": revenue,
            "total_profit": profit,
            "average_margin": round((profit / revenue) * 100, 1) if revenue else 0,
            "total_jobs": len(bucket["jobs"]),
        })

    low_margin_jobs = [job for job in job_rows if job["underpriced"] or job["profit_margin"] < 25]

    return {
        "metrics": {
            "revenue_this_month": total_revenue,
            "profit_this_month": total_profit,
            "average_job_value": avg_job_value,
            "average_profit_margin": avg_profit_margin,
        },
        "category_rows": sorted(category_rows, key=lambda item: item["profit"], reverse=True),
        "job_rows": sorted(job_rows, key=lambda item: item["profit"], reverse=True),
        "customer_rows": sorted(customer_rows, key=lambda item: item["total_profit"], reverse=True),
        "low_margin_jobs": sorted(low_margin_jobs, key=lambda item: item["profit_margin"]),
        "trend_rows": [{"period": key, **value} for key, value in sorted(trend.items())],
        "preferences": preferences,
    }


async def get_preferences(tenant_id: str) -> Dict[str, Any]:
    preferences = await db.profit_analytics_preferences.find_one({"tenant_id": tenant_id}, {"_id": 0})
    return preferences or {"tenant_id": tenant_id, **ProfitAnalyticsPreferences().model_dump()}


class PreferencesPayload(BaseModel):
    simple_mode: bool = False
    widget_order: List[str] = Field(default_factory=list)
    enabled_widgets: Dict[str, bool] = Field(default_factory=dict)


@router.get("/dashboard")
async def get_profit_analytics_dashboard(
    range_key: str = Query("30d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ensure_reporting_access(current_user)
    start_dt, end_dt = resolve_date_range(range_key, start_date, end_date)
    rows = await load_dashboard_rows(current_user.tenant_id, start_dt, end_dt, category)
    preferences = await get_preferences(current_user.tenant_id)
    return build_dashboard_payload(rows, range_key, preferences)


@router.put("/preferences")
async def save_profit_analytics_preferences(
    payload: PreferencesPayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ensure_reporting_access(current_user)
    preferences = {
        "tenant_id": current_user.tenant_id,
        **ProfitAnalyticsPreferences().model_dump(),
        **payload.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.profit_analytics_preferences.update_one(
        {"tenant_id": current_user.tenant_id},
        {"$set": preferences},
        upsert=True,
    )
    return preferences


@router.get("/export")
async def export_profit_analytics(
    format: str = Query("csv"),
    range_key: str = Query("30d"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ensure_reporting_access(current_user)
    start_dt, end_dt = resolve_date_range(range_key, start_date, end_date)
    rows = await load_dashboard_rows(current_user.tenant_id, start_dt, end_dt, category)
    preferences = await get_preferences(current_user.tenant_id)
    payload = build_dashboard_payload(rows, range_key, preferences)

    if format == "csv":
        dataframe = pd.DataFrame(payload["job_rows"])
        output = BytesIO(dataframe.to_csv(index=False).encode("utf-8"))
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=profit_margin_jobs.csv"})

    if format == "xlsx":
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            pd.DataFrame(payload["job_rows"]).to_excel(writer, sheet_name="Jobs", index=False)
            pd.DataFrame(payload["customer_rows"]).to_excel(writer, sheet_name="Customers", index=False)
            pd.DataFrame(payload["category_rows"]).to_excel(writer, sheet_name="Categories", index=False)
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=profit_margin_dashboard.xlsx"})

    if format == "pdf":
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("Profit & Margin Analytics", styles["Title"]), Spacer(1, 12)]
        story.append(Paragraph(f"Revenue: ${payload['metrics']['revenue_this_month']:.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Profit: ${payload['metrics']['profit_this_month']:.2f}", styles["BodyText"]))
        story.append(Paragraph(f"Average Margin: {payload['metrics']['average_profit_margin']:.1f}%", styles["BodyText"]))
        story.append(Spacer(1, 12))
        table_data = [["Job", "Customer", "Revenue", "Cost", "Profit", "Margin"]]
        for row in payload["job_rows"][:20]:
            table_data.append([
                row["job_name"], row["customer_name"], f"${row['revenue']:.2f}", f"${row['total_cost']:.2f}", f"${row['profit']:.2f}", f"{row['profit_margin']:.1f}%"
            ])
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE7F7")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(table)
        doc.build(story)
        output.seek(0)
        return StreamingResponse(output, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=profit_margin_dashboard.pdf"})

    raise HTTPException(status_code=400, detail="Unsupported export format")


# ==================== FINANCIAL ENTRIES (Sales + Expenses) ====================

financials_router = APIRouter(prefix="/financials", tags=["Financials"])


@financials_router.post("/sales")
async def create_sales_entry(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    body = await request.json()
    db = _get_db()
    entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "date": body.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "amount": float(body.get("amount", 0)),
        "tax_amount": float(body.get("tax_amount", 0)),
        "payment_method": body.get("payment_method", "cash"),
        "description": body.get("description", ""),
        "category": body.get("category", "general"),
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.sales_entries.insert_one(entry)
    entry.pop("_id", None)
    return entry


@financials_router.get("/sales")
async def get_sales_entries(start_date: str = None, end_date: str = None, current_user: UserInDB = Depends(get_current_active_user)):
    db = _get_db()
    query = {"tenant_id": current_user.tenant_id}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    entries = await db.sales_entries.find(query, {"_id": 0}).sort("date", -1).to_list(200)
    return entries


@financials_router.post("/expenses")
async def create_expense_entry(request: Request, current_user: UserInDB = Depends(get_current_active_user)):
    body = await request.json()
    db = _get_db()
    entry = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "date": body.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
        "amount": float(body.get("amount", 0)),
        "category": body.get("category", "materials"),
        "description": body.get("description", ""),
        "vendor": body.get("vendor", ""),
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.expense_entries.insert_one(entry)
    entry.pop("_id", None)
    return entry


@financials_router.get("/expenses")
async def get_expense_entries(start_date: str = None, end_date: str = None, current_user: UserInDB = Depends(get_current_active_user)):
    db = _get_db()
    query = {"tenant_id": current_user.tenant_id}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    entries = await db.expense_entries.find(query, {"_id": 0}).sort("date", -1).to_list(200)
    return entries


@financials_router.get("/summary")
async def get_financial_summary(start_date: str = None, end_date: str = None, current_user: UserInDB = Depends(get_current_active_user)):
    db = _get_db()
    query = {"tenant_id": current_user.tenant_id}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date

    sales = await db.sales_entries.find(query, {"_id": 0, "amount": 1, "tax_amount": 1}).to_list(1000)
    expenses = await db.expense_entries.find(query, {"_id": 0, "amount": 1}).to_list(1000)
    total_sales = sum(s.get("amount", 0) for s in sales)
    total_tax = sum(s.get("tax_amount", 0) or 0 for s in sales)
    total_expenses = sum(e.get("amount", 0) for e in expenses)
    net_profit = round(total_sales - total_expenses, 2)

    return {
        "total_sales": round(total_sales, 2),
        "total_tax": round(total_tax, 2),
        "total_expenses": round(total_expenses, 2),
        "net_profit": net_profit,
        "net_income": net_profit,  # frontend alias
        "sales_count": len(sales),
        "expense_count": len(expenses),
    }


@financials_router.get("/invoice-aging")
async def get_invoice_aging(current_user: UserInDB = Depends(get_current_active_user)):
    """Return outstanding invoices bucketed into 0-30, 31-60, 61-90, 90+ day aging groups."""
    db = _get_db()
    today = datetime.now(timezone.utc).date()

    # Fetch all unpaid/partial invoices with a due_date
    invoices = await db.invoices.find(
        {"tenant_id": current_user.tenant_id, "status": {"$in": ["sent", "partial", "overdue"]}},
        {"_id": 0, "id": 1, "customer_name": 1, "grand_total": 1, "amount_paid": 1, "due_date": 1, "status": 1}
    ).to_list(1000)

    buckets = {
        "current": {"label": "0-30 days", "count": 0, "total": 0.0, "invoices": []},
        "31_60":   {"label": "31-60 days", "count": 0, "total": 0.0, "invoices": []},
        "61_90":   {"label": "61-90 days", "count": 0, "total": 0.0, "invoices": []},
        "over_90": {"label": "90+ days", "count": 0, "total": 0.0, "invoices": []},
        "no_due_date": {"label": "No due date", "count": 0, "total": 0.0, "invoices": []},
    }

    for inv in invoices:
        balance = round(float(inv.get("grand_total") or 0) - float(inv.get("amount_paid") or 0), 2)
        if balance <= 0:
            continue
        due_raw = inv.get("due_date")
        item = {"id": inv["id"], "customer": inv.get("customer_name"), "balance": balance, "status": inv.get("status")}
        if not due_raw:
            buckets["no_due_date"]["count"] += 1
            buckets["no_due_date"]["total"] += balance
            buckets["no_due_date"]["invoices"].append(item)
            continue
        try:
            due_date = datetime.fromisoformat(str(due_raw).rstrip("Z").split("T")[0]).date()
            days_past = (today - due_date).days
        except Exception:
            buckets["no_due_date"]["count"] += 1
            buckets["no_due_date"]["total"] += balance
            buckets["no_due_date"]["invoices"].append(item)
            continue

        if days_past <= 30:
            key = "current"
        elif days_past <= 60:
            key = "31_60"
        elif days_past <= 90:
            key = "61_90"
        else:
            key = "over_90"
        buckets[key]["count"] += 1
        buckets[key]["total"] = round(buckets[key]["total"] + balance, 2)
        buckets[key]["invoices"].append(item)

    total_outstanding = round(sum(b["total"] for b in buckets.values()), 2)
    return {"buckets": buckets, "total_outstanding": total_outstanding, "as_of": today.isoformat()}
