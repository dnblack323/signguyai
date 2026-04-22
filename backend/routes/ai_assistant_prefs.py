"""
Phase 5 — Business Assistant personalization endpoints.

Lightweight per-user features:
- saved_commands: pin/reuse useful prompts
- routines: 2–4 saved commands run in sequence (micro-automations)
- user preferences: interaction mode (quick | guided | power)
- bulk action: send_overdue_reminders (preview + execute)
- next-step suggestions derived from action type
"""
from __future__ import annotations

from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from models import UserInDB
from models.auth import Permission, user_has_permission
from models.enums import UserRole
from core_runtime import db, get_current_active_user


router = APIRouter(prefix="/ai/assistant", tags=["business-assistant-phase5"])


# ============================================================================
# Models
# ============================================================================
class SavedCommandCreate(BaseModel):
    label: Optional[str] = None
    command: str
    pinned: bool = True


class SavedCommandUpdate(BaseModel):
    label: Optional[str] = None
    command: Optional[str] = None
    pinned: Optional[bool] = None


class RoutineCreate(BaseModel):
    name: str
    commands: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class RoutineUpdate(BaseModel):
    name: Optional[str] = None
    commands: Optional[List[str]] = None
    description: Optional[str] = None


class UserPreferencesUpdate(BaseModel):
    mode: Optional[str] = None  # "quick" | "guided" | "power"


class BulkRemindersSend(BaseModel):
    invoice_ids: Optional[List[str]] = None  # if None, all overdue
    note: Optional[str] = None


# ============================================================================
# Small helpers
# ============================================================================
MODE_VALUES = {"quick", "guided", "power"}

NEXT_STEP_SUGGESTIONS: Dict[str, List[Dict[str, Any]]] = {
    "create_order": [
        {"id": "next-create-invoice", "label": "Create invoice for this order", "kind": "command", "command": "create invoice for this order"},
        {"id": "next-schedule", "label": "Schedule production", "kind": "navigate", "route": "/production-board"},
        {"id": "next-view", "label": "View this order", "kind": "navigate_dynamic", "route_template": "/orders/{order_id}"},
    ],
    "create_invoice": [
        {"id": "next-open-invoice", "label": "Open invoice", "kind": "navigate", "route": "/invoices"},
        {"id": "next-back-to-order", "label": "Back to order", "kind": "navigate_dynamic", "route_template": "/orders/{order_id}"},
    ],
    "create_calendar_event": [
        {"id": "next-open-schedule", "label": "Open Schedule", "kind": "navigate", "route": "/schedule"},
    ],
    "log_time_entry": [
        {"id": "next-open-timesheets", "label": "Open Timesheets", "kind": "navigate", "route": "/timesheets"},
    ],
}


def _build_next_step_suggestions(action_type: str, result: Dict[str, Any]) -> List[Dict[str, Any]]:
    suggestions = []
    for s in NEXT_STEP_SUGGESTIONS.get(action_type, []):
        entry = {"id": s["id"], "label": s["label"]}
        if s.get("kind") == "navigate":
            entry.update({"action": "navigate", "target": s["route"]})
        elif s.get("kind") == "navigate_dynamic":
            # Fill placeholders from result (e.g. order_id)
            try:
                route = s["route_template"].format(**result)
                entry.update({"action": "navigate", "target": route})
            except (KeyError, ValueError):
                continue
        elif s.get("kind") == "command":
            entry.update({"action": "rerun_command", "target": s["command"]})
        suggestions.append(entry)
    return suggestions


# ============================================================================
# Saved commands
# ============================================================================
def _saved_cmds(db):
    return db.assistant_saved_commands


@router.get("/saved-commands")
async def list_saved_commands(
    current_user: UserInDB = Depends(get_current_active_user),
):
    items = await db.assistant_saved_commands.find(
        {"tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"_id": 0},
    ).sort("pinned", -1).sort("updated_at", -1).to_list(100)
    return {"items": items, "count": len(items)}


@router.post("/saved-commands")
async def create_saved_command(
    data: SavedCommandCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    cmd = (data.command or "").strip()
    if not cmd:
        raise HTTPException(status_code=400, detail="command is required")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "label": (data.label or cmd)[:80],
        "command": cmd,
        "pinned": data.pinned,
        "run_count": 0,
        "last_run_at": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.assistant_saved_commands.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/saved-commands/{cmd_id}")
async def update_saved_command(
    cmd_id: str,
    data: SavedCommandUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    update = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if not update:
        raise HTTPException(status_code=400, detail="nothing to update")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.assistant_saved_commands.update_one(
        {"id": cmd_id, "tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"$set": update},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Saved command not found")
    return {"ok": True}


@router.delete("/saved-commands/{cmd_id}")
async def delete_saved_command(
    cmd_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    result = await db.assistant_saved_commands.delete_one(
        {"id": cmd_id, "tenant_id": current_user.tenant_id, "user_id": current_user.id},
    )
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Saved command not found")
    return {"ok": True}


@router.post("/saved-commands/{cmd_id}/record-run")
async def record_saved_command_run(
    cmd_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Increment run_count when user reruns a saved command — feeds habit learning."""
    now = datetime.now(timezone.utc).isoformat()
    await db.assistant_saved_commands.update_one(
        {"id": cmd_id, "tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"$inc": {"run_count": 1}, "$set": {"last_run_at": now}},
    )
    return {"ok": True}


# ============================================================================
# Routines (micro-automations)
# ============================================================================
@router.get("/routines")
async def list_routines(
    current_user: UserInDB = Depends(get_current_active_user),
):
    items = await db.assistant_routines.find(
        {"tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"_id": 0},
    ).sort("updated_at", -1).to_list(50)
    return {"items": items, "count": len(items)}


@router.post("/routines")
async def create_routine(
    data: RoutineCreate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    commands = [c.strip() for c in (data.commands or []) if c.strip()]
    if not (1 <= len(commands) <= 8):
        raise HTTPException(status_code=400, detail="A routine must contain 1–8 commands")
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "user_id": current_user.id,
        "name": data.name.strip()[:80],
        "description": (data.description or "")[:200],
        "commands": commands,
        "run_count": 0,
        "last_run_at": None,
        "created_at": now,
        "updated_at": now,
    }
    await db.assistant_routines.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/routines/{routine_id}")
async def update_routine(
    routine_id: str,
    data: RoutineUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    update = {k: v for k, v in data.model_dump(exclude_none=True).items()}
    if "commands" in update:
        cleaned = [c.strip() for c in update["commands"] if c and c.strip()]
        if not (1 <= len(cleaned) <= 8):
            raise HTTPException(status_code=400, detail="A routine must contain 1–8 commands")
        update["commands"] = cleaned
    if "name" in update:
        update["name"] = update["name"].strip()[:80]
    if not update:
        raise HTTPException(status_code=400, detail="nothing to update")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.assistant_routines.update_one(
        {"id": routine_id, "tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"$set": update},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Routine not found")
    return {"ok": True}


@router.delete("/routines/{routine_id}")
async def delete_routine(
    routine_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    result = await db.assistant_routines.delete_one(
        {"id": routine_id, "tenant_id": current_user.tenant_id, "user_id": current_user.id},
    )
    if not result.deleted_count:
        raise HTTPException(status_code=404, detail="Routine not found")
    return {"ok": True}


@router.post("/routines/{routine_id}/record-run")
async def record_routine_run(
    routine_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Client confirms a routine run — bump counters so suggestions can use it."""
    now = datetime.now(timezone.utc).isoformat()
    result = await db.assistant_routines.update_one(
        {"id": routine_id, "tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"$inc": {"run_count": 1}, "$set": {"last_run_at": now}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Routine not found")
    return {"ok": True}


# ============================================================================
# User preferences (mode)
# ============================================================================
@router.get("/preferences")
async def get_preferences(current_user: UserInDB = Depends(get_current_active_user)):
    doc = await db.assistant_user_prefs.find_one(
        {"tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"_id": 0},
    )
    return doc or {"mode": "guided", "tenant_id": current_user.tenant_id, "user_id": current_user.id}


@router.put("/preferences")
async def update_preferences(
    data: UserPreferencesUpdate,
    current_user: UserInDB = Depends(get_current_active_user),
):
    update = {}
    if data.mode is not None:
        if data.mode not in MODE_VALUES:
            raise HTTPException(status_code=400, detail=f"mode must be one of {sorted(MODE_VALUES)}")
        update["mode"] = data.mode
    if not update:
        raise HTTPException(status_code=400, detail="nothing to update")
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.assistant_user_prefs.update_one(
        {"tenant_id": current_user.tenant_id, "user_id": current_user.id},
        {"$set": update, "$setOnInsert": {
            "id": str(uuid.uuid4()),
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "created_at": update["updated_at"],
        }},
        upsert=True,
    )
    return {"ok": True, **update}


# ============================================================================
# Habit / suggested next steps (based on action just taken)
# ============================================================================
class NextStepRequest(BaseModel):
    action_type: str
    result: Dict[str, Any] = Field(default_factory=dict)


@router.post("/next-step-suggestions")
async def next_step_suggestions(
    data: NextStepRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Returns a lightweight, rule-based list of next actions a user might want
    to take after completing an assistant action. Intentionally NOT an ML model —
    just hand-curated habit rules that respect what the user already does.
    """
    suggestions = _build_next_step_suggestions(data.action_type, data.result or {})
    return {"suggestions": suggestions}


# ============================================================================
# Smart defaults — last customer used in an AI-created order
# ============================================================================
@router.get("/smart-defaults/last-order-customer")
async def last_order_customer(current_user: UserInDB = Depends(get_current_active_user)):
    """Return the most recent customer this user created an order for via AI.
    Client uses this to offer: 'Use Acme Corp again?'"""
    doc = await db.ai_action_audit.find_one(
        {
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "action_type": "create_order",
            "status": "executed",
        },
        {"_id": 0, "parameters": 1, "result": 1, "created_at": 1},
        sort=[("created_at", -1)],
    )
    if not doc:
        return {"customer_name": None, "customer_id": None, "last_used_at": None}
    params = doc.get("parameters") or {}
    result = doc.get("result") or {}
    return {
        "customer_name": params.get("customer_name") or result.get("customer_name"),
        "customer_id": result.get("customer_id") or params.get("customer_id"),
        "last_used_at": doc.get("created_at"),
    }


# ============================================================================
# Bulk action: overdue-invoice reminders
# ============================================================================
@router.get("/bulk/overdue-reminders/preview")
async def overdue_reminders_preview(current_user: UserInDB = Depends(get_current_active_user)):
    """Preview which invoices would receive a reminder."""
    if not user_has_permission(current_user.role, Permission.INVOICES_VIEW):
        raise HTTPException(status_code=403, detail="Missing INVOICES_VIEW permission")
    from services.assistant_queries import query_overdue_invoices
    result = await query_overdue_invoices(db, current_user.tenant_id)
    rows = result.get("rows") or []
    affected = [
        {
            "invoice_id": r.get("invoice_id"),
            "invoice_number": r.get("invoice_number"),
            "customer_name": r.get("customer_name"),
            "balance_due": r.get("balance_due"),
            "days_overdue": r.get("days_overdue"),
        }
        for r in rows
    ]
    return {
        "count": len(affected),
        "total_overdue": result.get("metrics", []),
        "sample": affected[:10],
        "all_ids": [a["invoice_id"] for a in affected if a.get("invoice_id")],
    }


@router.post("/bulk/overdue-reminders/send")
async def overdue_reminders_send(
    data: BulkRemindersSend,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Send a reminder audit-log entry per invoice. Real email delivery is
    delegated to the Invoices reminders module if/when wired — this endpoint
    keeps the action visible and auditable.
    """
    if current_user.role not in (UserRole.OWNER, UserRole.ADMIN) and not user_has_permission(current_user.role, Permission.INVOICES_EDIT):
        raise HTTPException(status_code=403, detail="You don't have permission to send invoice reminders")
    from services.assistant_queries import query_overdue_invoices

    target_ids = data.invoice_ids
    if not target_ids:
        preview = await query_overdue_invoices(db, current_user.tenant_id)
        target_ids = [r.get("invoice_id") for r in (preview.get("rows") or []) if r.get("invoice_id")]

    if not target_ids:
        return {"sent": 0, "skipped": 0, "message": "No overdue invoices to remind."}

    now = datetime.now(timezone.utc).isoformat()
    audit_entries = []
    for inv_id in target_ids[:100]:  # safety cap
        audit_entries.append({
            "id": str(uuid.uuid4()),
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "action_type": "bulk_send_overdue_reminder",
            "parameters": {"invoice_id": inv_id, "note": data.note or ""},
            "result": {"queued": True},
            "status": "executed",
            "source": "ai_assistant",
            "created_at": now,
        })
    if audit_entries:
        await db.ai_action_audit.insert_many(audit_entries)

    # Mark each invoice so downstream reminder systems can pick up.
    await db.invoices.update_many(
        {"id": {"$in": target_ids[:100]}, "tenant_id": current_user.tenant_id},
        {"$set": {"reminder_queued_at": now, "reminder_queued_by": current_user.id}},
    )

    return {
        "sent": len(audit_entries),
        "skipped": max(0, len(target_ids) - 100),
        "message": f"Queued {len(audit_entries)} reminders. Invoice reminder delivery will pick them up.",
    }
