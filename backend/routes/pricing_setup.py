from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os
import re
import uuid

import pandas as pd
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from pypdf import PdfReader

from core.auth_deps import get_current_active_user
from models import UserInDB

load_dotenv()

router = APIRouter(prefix="/pricing-setup", tags=["Pricing Setup"])

UPLOAD_ROOT = Path("/app/backend/uploads/historical_invoices")
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

_db = None
_logger = None


def _get_db():
    global _db
    if _db is None:
        from server import db
        _db = db
    return _db


def _get_logger():
    global _logger
    if _logger is None:
        from server import logger
        _logger = logger
    return _logger


class LazyDB:
    def __getattr__(self, name):
        return getattr(_get_db(), name)


db = LazyDB()

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls"}
MAX_PREVIEW_ROWS = 25

CATEGORY_META = {
    "vehicle_wraps": {"label": "Vehicle Wraps", "benchmark_field": "average_sell_price_per_sqft"},
    "banners": {"label": "Banners", "benchmark_field": "average_sell_price_per_sqft"},
    "rigid_signs": {"label": "Rigid Signs", "benchmark_field": "average_sell_price_per_sqft"},
    "cut_vinyl": {"label": "Cut Vinyl", "benchmark_field": "average_sell_price_per_sqft"},
    "apparel": {"label": "Apparel", "benchmark_field": "average_sell_price_per_unit"},
    "services": {"label": "Services", "benchmark_field": "average_sell_price_per_hour"},
    "custom": {"label": "Custom / Miscellaneous", "benchmark_field": "average_sell_price_per_unit"},
}

FIELD_ALIASES = {
    "description_field": ["description", "item", "item description", "line item", "product", "service", "details"],
    "quantity_field": ["quantity", "qty", "units", "hours", "count"],
    "total_field": ["total", "amount", "line total", "price", "extended price", "net amount"],
    "dimension_field": ["dimensions", "dimension", "size", "sqft", "square feet"],
    "category_field": ["category", "type", "item type", "department"],
}


class MappingPayload(BaseModel):
    description_field: Optional[str] = None
    quantity_field: Optional[str] = None
    total_field: Optional[str] = None
    dimension_field: Optional[str] = None
    category_field: Optional[str] = None
    category_overrides: Dict[str, str] = Field(default_factory=dict)


class AnalyzePayload(BaseModel):
    excluded_row_ids: List[str] = Field(default_factory=list)


class SuggestionDecision(BaseModel):
    suggestion_id: str
    status: str
    final_value: Optional[float] = None


class ReviewPayload(BaseModel):
    decisions: List[SuggestionDecision]


def ensure_admin_access(current_user: UserInDB):
    if current_user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can manage historical pricing imports")


def normalize_column_name(column_name: str) -> str:
    return str(column_name).strip().lower().replace("_", " ")


def suggest_mapping(columns: List[str]) -> Dict[str, Optional[str]]:
    normalized = {normalize_column_name(column): column for column in columns}
    suggestions = {}
    for field_name, aliases in FIELD_ALIASES.items():
        suggestions[field_name] = None
        for alias in aliases:
            if alias in normalized:
                suggestions[field_name] = normalized[alias]
                break
    return suggestions


def safe_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^0-9.\-]", "", str(value))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_dimensions(raw_value: str) -> Dict[str, Any]:
    if not raw_value:
        return {"width_inches": None, "height_inches": None, "square_feet": None}
    match = re.search(r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)", raw_value)
    if not match:
        return {"width_inches": None, "height_inches": None, "square_feet": None}
    width_inches = float(match.group(1))
    height_inches = float(match.group(2))
    return {
        "width_inches": width_inches,
        "height_inches": height_inches,
        "square_feet": round((width_inches * height_inches) / 144, 2),
    }


def guess_category(description: str) -> str:
    text = (description or "").lower()
    if any(token in text for token in ["wrap", "vehicle", "van", "truck", "car graphic"]):
        return "vehicle_wraps"
    if any(token in text for token in ["banner", "grommet", "hemmed"]):
        return "banners"
    if any(token in text for token in ["coro", "coroplast", "yard sign", "rigid", "dibond", "acm", "aluminum sign", "pvc sign"]):
        return "rigid_signs"
    if any(token in text for token in ["vinyl", "decal", "lettering", "sticker"]):
        return "cut_vinyl"
    if any(token in text for token in ["shirt", "hoodie", "apparel", "hat", "polo", "garment"]):
        return "apparel"
    if any(token in text for token in ["install", "installation", "design", "survey", "consult", "service", "labor"]):
        return "services"
    return "custom"


def strip_code_fences(payload_text: str) -> str:
    text = payload_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    return text


def calculate_confidence(sample_count: int, complete_samples: int) -> str:
    if sample_count >= 12 and complete_samples >= 8:
        return "High"
    if sample_count >= 5 and complete_samples >= 3:
        return "Medium"
    return "Low"


def percentile(sorted_values: List[float], percent: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = (len(sorted_values) - 1) * percent
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def flag_outliers(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows_by_category: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        if not row.get("excluded"):
            rows_by_category[row["category_final"]].append(row.get("total", 0))

    category_bounds = {}
    for category_key, totals in rows_by_category.items():
        sorted_totals = sorted(totals)
        q1 = percentile(sorted_totals, 0.25)
        q3 = percentile(sorted_totals, 0.75)
        iqr = q3 - q1
        category_bounds[category_key] = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)

    updated_rows = []
    for row in rows:
        lower, upper = category_bounds.get(row["category_final"], (None, None))
        total = row.get("total", 0)
        row["is_outlier"] = bool(lower is not None and (total < lower or total > upper))
        updated_rows.append(row)
    return updated_rows


def summarize_aggregates(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    included_rows = [row for row in rows if not row.get("excluded")]
    by_category: Dict[str, Dict[str, Any]] = {}
    invoice_totals = defaultdict(float)

    for row in included_rows:
        category_key = row["category_final"]
        category_bucket = by_category.setdefault(category_key, {
            "category_key": category_key,
            "category_label": CATEGORY_META.get(category_key, {}).get("label", category_key),
            "sample_count": 0,
            "rows_with_sqft": 0,
            "rows_with_qty": 0,
            "totals": [],
            "price_per_measure": [],
            "common_quantities": Counter(),
            "common_descriptions": Counter(),
        })
        category_bucket["sample_count"] += 1
        category_bucket["totals"].append(row.get("total", 0))
        category_bucket["common_quantities"][str(row.get("quantity", 1))] += 1
        category_bucket["common_descriptions"][row.get("description", "Unknown")] += 1

        benchmark_field = CATEGORY_META.get(category_key, {}).get("benchmark_field")
        if benchmark_field == "average_sell_price_per_sqft" and row.get("square_feet"):
            category_bucket["rows_with_sqft"] += 1
            category_bucket["price_per_measure"].append(row["total"] / row["square_feet"])
        elif benchmark_field in ["average_sell_price_per_unit", "average_sell_price_per_hour"] and row.get("quantity"):
            category_bucket["rows_with_qty"] += 1
            category_bucket["price_per_measure"].append(row["total"] / max(row["quantity"], 1))

        invoice_totals[row.get("invoice_key") or row["row_id"]] += row.get("total", 0)

    top_categories = []
    suggestions = []
    category_metrics = []

    for category_key, bucket in by_category.items():
        totals = bucket["totals"]
        average_order_total = round(sum(totals) / max(len(totals), 1), 2)
        measure_values = bucket["price_per_measure"]
        benchmark_field = CATEGORY_META.get(category_key, {}).get("benchmark_field")
        confidence = calculate_confidence(bucket["sample_count"], len(measure_values) or bucket["sample_count"])
        top_categories.append({
            "category_key": category_key,
            "category_label": bucket["category_label"],
            "sample_count": bucket["sample_count"],
            "average_order_total": average_order_total,
        })

        category_metrics.append({
            "category_key": category_key,
            "category_label": bucket["category_label"],
            "sample_count": bucket["sample_count"],
            "average_order_total": average_order_total,
            "benchmark_field": benchmark_field,
            "benchmark_value": round(sum(measure_values) / max(len(measure_values), 1), 2) if measure_values else None,
            "common_quantities": bucket["common_quantities"].most_common(5),
            "common_descriptions": bucket["common_descriptions"].most_common(5),
            "confidence": confidence,
        })

        suggestions.append({
            "id": str(uuid.uuid4()),
            "category_key": category_key,
            "category_label": bucket["category_label"],
            "benchmark_field": "average_order_total",
            "benchmark_label": "Average Order Total",
            "suggested_value": average_order_total,
            "confidence": confidence,
            "status": "pending",
        })

        if measure_values:
            suggestions.append({
                "id": str(uuid.uuid4()),
                "category_key": category_key,
                "category_label": bucket["category_label"],
                "benchmark_field": benchmark_field,
                "benchmark_label": benchmark_field.replace("_", " ").title(),
                "suggested_value": round(sum(measure_values) / max(len(measure_values), 1), 2),
                "confidence": confidence,
                "status": "pending",
            })

    return {
        "invoice_count": len(invoice_totals),
        "line_item_count": len(included_rows),
        "top_categories": sorted(top_categories, key=lambda item: item["sample_count"], reverse=True),
        "category_metrics": category_metrics,
        "suggestions": suggestions,
    }


async def ai_analyze_category_metrics(category_metrics: List[Dict[str, Any]], import_id: str) -> Dict[str, Any]:
    if not EMERGENT_LLM_KEY or not category_metrics:
        return {}

    from emergentintegrations.llm.chat import LlmChat, UserMessage

    prompt = f"""
You are analyzing historical sign-shop invoice data for pricing benchmark setup.

Return VALID JSON only in this shape:
{{
  "categories": [
    {{
      "category_key": "banners",
      "summary": "...",
      "pattern_notes": ["..."],
      "confidence_reason": "..."
    }}
  ]
}}

Use this aggregate data:
{json.dumps(category_metrics, indent=2)}
"""

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"historical_invoice_analysis_{import_id}",
        system_message="You are a careful pricing benchmark analyst. Return valid JSON only.",
    ).with_model("openai", "gpt-5.2")

    response = await chat.send_message(UserMessage(text=prompt))
    return json.loads(strip_code_fences(response))


async def ai_extract_pdf_rows(pdf_text: str, import_id: str, file_label: str) -> List[Dict[str, Any]]:
    if not pdf_text.strip() or not EMERGENT_LLM_KEY:
        return []

    from emergentintegrations.llm.chat import LlmChat, UserMessage

    prompt = f"""
Extract invoice line items from this PDF text. Return VALID JSON only in this exact shape:
{{"rows":[{{"description":"","quantity":1,"total":0,"dimension_text":"","invoice_number":"","invoice_date":""}}]}}

Rules:
- Keep only actual sellable line items if possible
- Ignore tax-only, payment-only, and duplicate summary lines where obvious
- If quantity is missing, use 1
- If total is missing, use 0
- If dimensions are embedded in description, copy them into dimension_text

File: {file_label}
Text:
{pdf_text[:18000]}
"""

    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"historical_invoice_pdf_extract_{import_id}_{uuid.uuid4()}",
        system_message="You extract structured line-item data from invoice text. Return valid JSON only.",
    ).with_model("openai", "gpt-5.2")

    response = await chat.send_message(UserMessage(text=prompt))
    parsed = json.loads(strip_code_fences(response))
    return parsed.get("rows", [])


async def save_upload_file(import_dir: Path, upload_file: UploadFile) -> Dict[str, Any]:
    extension = Path(upload_file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {upload_file.filename}")

    file_id = str(uuid.uuid4())
    file_path = import_dir / f"{file_id}{extension}"
    contents = await upload_file.read()
    file_path.write_bytes(contents)
    return {
        "id": file_id,
        "filename": upload_file.filename,
        "extension": extension,
        "stored_path": str(file_path),
        "size_bytes": len(contents),
        "content_type": upload_file.content_type,
    }


def parse_structured_preview(file_record: Dict[str, Any]) -> Dict[str, Any]:
    file_path = file_record["stored_path"]
    extension = file_record["extension"]
    if extension == ".csv":
        dataframe = pd.read_csv(file_path)
    else:
        dataframe = pd.read_excel(file_path)

    dataframe = dataframe.fillna("")
    columns = [str(column) for column in dataframe.columns]
    sample_rows = dataframe.head(5).to_dict(orient="records")
    return {
        "row_count": int(len(dataframe.index)),
        "columns": columns,
        "sample_rows": sample_rows,
        "mapping_suggestions": suggest_mapping(columns),
    }


def extract_pdf_preview(file_record: Dict[str, Any]) -> Dict[str, Any]:
    reader = PdfReader(file_record["stored_path"])
    text_chunks = []
    for page in reader.pages[:8]:
        text_chunks.append(page.extract_text() or "")
    preview_text = "\n".join(text_chunks).strip()
    return {
        "page_count": len(reader.pages),
        "text_preview": preview_text[:5000],
    }


def normalize_structured_rows(file_record: Dict[str, Any], mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
    dataframe = pd.read_csv(file_record["stored_path"]).fillna("") if file_record["extension"] == ".csv" else pd.read_excel(file_record["stored_path"]).fillna("")

    rows = []
    for _, row in dataframe.iterrows():
        description = str(row.get(mapping.get("description_field") or "", "")).strip()
        if not description:
            continue
        quantity = safe_float(row.get(mapping.get("quantity_field") or "", 1)) or 1
        total = safe_float(row.get(mapping.get("total_field") or "", 0))
        dimension_text = str(row.get(mapping.get("dimension_field") or "", "")).strip() or description
        parsed_dimensions = parse_dimensions(dimension_text)
        category_hint = str(row.get(mapping.get("category_field") or "", "")).strip().lower()

        rows.append({
            "row_id": str(uuid.uuid4()),
            "file_id": file_record["id"],
            "file_name": file_record["filename"],
            "invoice_key": f"{file_record['id']}-{len(rows) + 1}",
            "description": description,
            "quantity": quantity,
            "total": total,
            "dimension_text": dimension_text,
            **parsed_dimensions,
            "category_hint": category_hint,
            "category_final": guess_category(category_hint or description),
            "excluded": False,
            "is_outlier": False,
        })
    return rows


async def build_normalized_rows(import_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    normalized_rows: List[Dict[str, Any]] = []
    mapping = import_doc.get("mapping", {})
    category_overrides = mapping.get("category_overrides", {})

    for file_record in import_doc.get("files", []):
        extension = file_record["extension"]
        if extension in [".csv", ".xlsx", ".xls"]:
            normalized_rows.extend(normalize_structured_rows(file_record, mapping))
        elif extension == ".pdf":
            reader = PdfReader(file_record["stored_path"])
            full_text = "\n".join((page.extract_text() or "") for page in reader.pages[:20])
            ai_rows = await ai_extract_pdf_rows(full_text, import_doc["id"], file_record["filename"])
            for extracted in ai_rows:
                dimension_text = extracted.get("dimension_text") or extracted.get("description") or ""
                normalized_rows.append({
                    "row_id": str(uuid.uuid4()),
                    "file_id": file_record["id"],
                    "file_name": file_record["filename"],
                    "invoice_key": extracted.get("invoice_number") or f"{file_record['id']}-{len(normalized_rows) + 1}",
                    "description": extracted.get("description", "").strip(),
                    "quantity": safe_float(extracted.get("quantity", 1)) or 1,
                    "total": safe_float(extracted.get("total", 0)),
                    "dimension_text": dimension_text,
                    **parse_dimensions(dimension_text),
                    "category_hint": "",
                    "category_final": guess_category(extracted.get("description", "")),
                    "excluded": False,
                    "is_outlier": False,
                })

    for row in normalized_rows:
        override_key = row.get("description", "")
        if override_key in category_overrides:
            row["category_final"] = category_overrides[override_key]

    return flag_outliers(normalized_rows)


async def get_import_or_404(import_id: str, tenant_id: str) -> Dict[str, Any]:
    record = await db.pricing_imports.find_one({"id": import_id, "tenant_id": tenant_id}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="Historical invoice import not found")
    return record


@router.get("/imports")
async def list_imports(current_user: UserInDB = Depends(get_current_active_user)):
    ensure_admin_access(current_user)
    imports = await db.pricing_imports.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(25)
    return imports


@router.post("/imports")
async def create_import(
    files: List[UploadFile] = File(...),
    current_user: UserInDB = Depends(get_current_active_user),
):
    ensure_admin_access(current_user)

    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    import_id = str(uuid.uuid4())
    import_dir = UPLOAD_ROOT / current_user.tenant_id / import_id
    import_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    mapping_preview_columns = set()
    structured_file_present = False

    for upload_file in files:
        file_record = await save_upload_file(import_dir, upload_file)
        if file_record["extension"] in [".csv", ".xlsx", ".xls"]:
            file_record["preview"] = parse_structured_preview(file_record)
            mapping_preview_columns.update(file_record["preview"]["columns"])
            structured_file_present = True
        else:
            file_record["preview"] = extract_pdf_preview(file_record)
        saved_files.append(file_record)

    default_mapping = suggest_mapping(sorted(mapping_preview_columns)) if structured_file_present else {}

    import_doc = {
        "id": import_id,
        "tenant_id": current_user.tenant_id,
        "created_by": current_user.id,
        "status": "mapping_required" if structured_file_present else "ready_for_analysis",
        "files": saved_files,
        "mapping": {**default_mapping, "category_overrides": {}},
        "normalized_rows": [],
        "analysis_summary": None,
        "suggestions": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.pricing_imports.insert_one(import_doc)
    return await get_import_or_404(import_id, current_user.tenant_id)


@router.get("/imports/{import_id}")
async def get_import(import_id: str, current_user: UserInDB = Depends(get_current_active_user)):
    ensure_admin_access(current_user)
    return await get_import_or_404(import_id, current_user.tenant_id)


@router.put("/imports/{import_id}/mapping")
async def update_mapping(
    import_id: str,
    payload: MappingPayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ensure_admin_access(current_user)
    import_doc = await get_import_or_404(import_id, current_user.tenant_id)
    mapping = payload.model_dump()
    normalized_rows = await build_normalized_rows({**import_doc, "mapping": mapping})

    await db.pricing_imports.update_one(
        {"id": import_id, "tenant_id": current_user.tenant_id},
        {"$set": {
            "mapping": mapping,
            "normalized_rows": normalized_rows,
            "status": "ready_for_analysis",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return await get_import_or_404(import_id, current_user.tenant_id)


@router.post("/imports/{import_id}/analyze")
async def analyze_import(
    import_id: str,
    payload: AnalyzePayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ensure_admin_access(current_user)
    import_doc = await get_import_or_404(import_id, current_user.tenant_id)

    normalized_rows = import_doc.get("normalized_rows") or await build_normalized_rows(import_doc)
    excluded_ids = set(payload.excluded_row_ids)
    for row in normalized_rows:
        row["excluded"] = row["row_id"] in excluded_ids

    summary = summarize_aggregates(normalized_rows)
    ai_notes = await ai_analyze_category_metrics(summary["category_metrics"], import_id)
    notes_by_category = {item["category_key"]: item for item in ai_notes.get("categories", [])} if ai_notes else {}

    suggestions = []
    for suggestion in summary["suggestions"]:
        category_notes = notes_by_category.get(suggestion["category_key"], {})
        suggestions.append({
            **suggestion,
            "summary": category_notes.get("summary", ""),
            "pattern_notes": category_notes.get("pattern_notes", []),
            "confidence_reason": category_notes.get("confidence_reason", "Confidence is based on sample size and data completeness."),
            "final_value": suggestion["suggested_value"],
        })

    analysis_summary = {
        **summary,
        "categories_detected": [item["category_key"] for item in summary["top_categories"]],
        "outlier_rows": [row for row in normalized_rows if row.get("is_outlier")],
    }

    await db.pricing_imports.update_one(
        {"id": import_id, "tenant_id": current_user.tenant_id},
        {"$set": {
            "normalized_rows": normalized_rows,
            "analysis_summary": analysis_summary,
            "suggestions": suggestions,
            "status": "analyzed",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )
    return await get_import_or_404(import_id, current_user.tenant_id)


@router.post("/imports/{import_id}/review")
async def review_suggestions(
    import_id: str,
    payload: ReviewPayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ensure_admin_access(current_user)
    import_doc = await get_import_or_404(import_id, current_user.tenant_id)

    decision_map = {decision.suggestion_id: decision for decision in payload.decisions}
    updated_suggestions = []
    accepted_updates: Dict[str, Dict[str, Any]] = defaultdict(dict)

    for suggestion in import_doc.get("suggestions", []):
        decision = decision_map.get(suggestion["id"])
        if decision:
            suggestion["status"] = decision.status
            if decision.final_value is not None:
                suggestion["final_value"] = decision.final_value
        updated_suggestions.append(suggestion)

        if suggestion.get("status") in ["accepted", "edited"]:
            accepted_updates[suggestion["category_key"]][suggestion["benchmark_field"]] = suggestion.get("final_value", suggestion.get("suggested_value"))

    pricing_config = await db.pricing_configuration.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0}) or {
        "tenant_id": current_user.tenant_id,
        "selling_price_benchmarks": {},
    }
    selling_benchmarks = pricing_config.get("selling_price_benchmarks", {})

    for category_key, values in accepted_updates.items():
        category_bucket = {**selling_benchmarks.get(category_key, {}), **values}
        category_bucket.setdefault("label", CATEGORY_META.get(category_key, {}).get("label", category_key))
        selling_benchmarks[category_key] = category_bucket

    await db.pricing_configuration.update_one(
        {"tenant_id": current_user.tenant_id},
        {"$set": {
            "selling_price_benchmarks": selling_benchmarks,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
        upsert=True,
    )

    await db.pricing_imports.update_one(
        {"id": import_id, "tenant_id": current_user.tenant_id},
        {"$set": {
            "suggestions": updated_suggestions,
            "status": "reviewed",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }}
    )

    return {
        "message": "Historical invoice suggestions reviewed",
        "accepted_categories": list(accepted_updates.keys()),
        "saved_to": "selling_price_benchmarks_only",
    }