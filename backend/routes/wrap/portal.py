"""
Wrap Command Center — Phase 2F: customer-facing summary (authenticated, internal).

Returns the safe payload that the existing Customer Portal consumes to render
the "Vehicle Wrap Project" section. NO public token endpoint, NO separate
portal page — this is the canonical data contract for the existing portal.

The actual customer-portal route extensions live in routes/portal.py.
"""
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends

from models import UserInDB
from server import db, get_current_active_user

from .core import _load_ticket_or_404, _now, _serialize

portal_router = APIRouter(tags=["Wrap Command Center — Customer Summary"])


DEFAULT_CARE_INSTRUCTIONS = [
    "Wait at least 48 hours before washing your wrap for the first time.",
    "Hand-wash with a soft microfiber cloth and a mild automotive soap.",
    "Avoid automatic car washes with stiff brushes — they can lift edges.",
    "Keep pressure washers below 1,800 PSI and hold the nozzle at least 12 inches away.",
    "Do not use wax, polish, or abrasive cleaners on the wrap surface.",
    "Park in shade or under cover when possible — UV exposure shortens wrap life.",
    "If you notice an edge lifting, contact us right away — small fixes are easy.",
]


def _safe_vehicle(v: dict) -> dict:
    if not v:
        return {}
    return {
        "year": v.get("year") or "",
        "make": v.get("make") or "",
        "model": v.get("model") or "",
        "color": v.get("color") or "",
        "trim": v.get("trim") or "",
        "vehicle_type": v.get("vehicle_type") or "",
    }


def _safe_install(i: dict) -> dict:
    if not i:
        return {}
    return {
        "install_date": i.get("install_date"),
        "completed_at": i.get("completed_at"),
        "installer": i.get("installer_name") or i.get("lead_installer") or "",
        "install_status": i.get("install_status") or "",
    }


def _safe_aftercare(a: dict) -> dict:
    if not a:
        return {}
    return {
        "aftercare_status": a.get("aftercare_status") or "",
        "aftercare_sent": bool(a.get("aftercare_sent")),
        "aftercare_sent_at": a.get("aftercare_sent_at"),
        "customer_viewed": bool(a.get("customer_viewed")),
        "customer_viewed_at": a.get("customer_viewed_at"),
        "customer_acknowledged": bool(a.get("customer_acknowledged")),
        "customer_acknowledged_at": a.get("customer_acknowledged_at"),
        "followup_24h": bool(a.get("followup_24h")),
        "followup_7d": bool(a.get("followup_7d")),
        "followup_30d": bool(a.get("followup_30d")),
    }


def _safe_design(d: dict) -> dict:
    if not d:
        return {}
    return {
        "questionnaire_status": d.get("questionnaire_status") or "",
        "proof_status": d.get("proof_status") or "",
        "current_proof_version": d.get("current_proof_version"),
    }


def _safe_contract(c: dict) -> dict:
    if not c:
        return {}
    return {
        "contract_status": c.get("contract_status") or "",
        "signed_at": c.get("signed_at"),
        "signed_by": c.get("signed_by"),
        "terms_summary": c.get("terms_summary") or "",
        "accepted_terms": bool(c.get("accepted_terms")),
    }


def _safe_inspection(i: dict, expose: bool) -> dict:
    """Only return inspection block when explicitly customer-visible.

    If expose is False, return a minimal stub so the frontend can hide the card.
    """
    if not i or not expose:
        return {"customer_visible": False}
    return {
        "customer_visible": True,
        "inspection_status": i.get("inspection_status") or "",
        "inspection_date": i.get("inspection_date"),
        "customer_acknowledged": bool(i.get("customer_acknowledged")),
        "customer_acknowledged_at": i.get("customer_acknowledged_at"),
        # NO internal notes, NO damage notes, only customer-visible markers if any
        "damage_marker_count": len(i.get("damage_markers") or []),
    }


def _safe_pricing(snapshot: Optional[dict]) -> dict:
    if not snapshot:
        return {}
    # Show ONLY the customer-facing total. No profit, margin, materials, labor.
    return {
        "quoted_price": snapshot.get("quoted_price"),
        "computed_at": snapshot.get("computed_at"),
    }


async def build_customer_facing_summary(
    tenant_id: str, ticket_id: str, ticket: Optional[dict] = None
) -> dict:
    """Canonical builder used by both the internal endpoint AND the
    Customer Portal route extensions in routes/portal.py.
    """
    if ticket is None:
        ticket = await db.job_tickets.find_one(
            {"id": ticket_id, "tenant_id": tenant_id}, {"_id": 0}
        ) or {}

    wrap_raw = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    )
    wrap = _serialize(wrap_raw) if wrap_raw else {}

    inspection_raw = wrap.get("inspection") or {}
    # Inspection report is shown to the customer only if explicitly opted in.
    inspection_customer_visible = bool(inspection_raw.get("customer_visible"))

    # Customer-visible files only
    files_cursor = db.wrap_files.find(
        {
            "tenant_id": tenant_id,
            "ticket_id": ticket_id,
            "customer_visible": True,
        },
        {
            "_id": 0,
            "id": 1,
            "category": 1,
            "filename": 1,
            "content_type": 1,
            "uploaded_at": 1,
            "notes": 1,
            "size": 1,
        },
    ).sort("uploaded_at", -1)
    files = await files_cursor.to_list(200)

    snap = wrap.get("pricing_snapshot") or {}

    return {
        "ticket_id": ticket_id,
        "order_id": ticket.get("order_id", ""),
        "wrap_type": wrap.get("wrap_type") or ticket.get("item_category") or "Vehicle Wrap",
        "vehicle": _safe_vehicle(wrap.get("vehicle_info")),
        "design": _safe_design(wrap.get("design")),
        "contract": _safe_contract(wrap.get("contract")),
        "inspection": _safe_inspection(inspection_raw, inspection_customer_visible),
        "install": _safe_install(wrap.get("install")),
        "aftercare": _safe_aftercare(wrap.get("aftercare")),
        "pricing": _safe_pricing(snap),
        "approvals": {
            "quote_approved": bool((wrap.get("approvals") or {}).get("quote_approved")),
            "contract_signed": bool((wrap.get("approvals") or {}).get("contract_signed")),
            "proof_approved": bool((wrap.get("approvals") or {}).get("proof_approved")),
            "deposit_paid": bool((wrap.get("approvals") or {}).get("deposit_paid")),
            "inspection_acknowledged": bool((wrap.get("approvals") or {}).get("inspection_acknowledged")),
            "final_signoff_completed": bool((wrap.get("approvals") or {}).get("final_signoff_completed")),
            "aftercare_sent": bool((wrap.get("approvals") or {}).get("aftercare_sent")),
        },
        "pipeline_state": wrap.get("pipeline_state") or {},
        "files": files,
        "files_count": len(files),
        "care_instructions": DEFAULT_CARE_INSTRUCTIONS,
        "generated_at": _now(),
    }


@portal_router.get("/items/{ticket_id}/customer-facing-summary")
async def get_customer_facing_summary(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Authenticated, internal-staff view of the exact payload the existing
    Customer Portal will receive. Used by Wrap Command Center to preview what
    the customer sees and as the canonical data contract.
    """
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    return await build_customer_facing_summary(current_user.tenant_id, ticket_id, ticket)


# ─────────── Pending Customer Actions (dashboard widget) ───────────
@portal_router.get("/pending-customer-actions")
async def list_pending_customer_actions(
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Return all wrap tickets in the current tenant that are waiting on a
    customer action. Read-only, no side effects, no message templates.

    Action codes:
      - proof_pending     — customer hasn't approved or rejected the latest proof
      - revision_requested — customer asked for changes, design tab needs work
      - contract_pending  — contract sent but not signed
      - quote_pending     — order/wrap has a quoted price but quote not approved
      - inspection_pending — inspection shared with customer but not acknowledged
      - aftercare_pending — aftercare sent but not acknowledged
    """
    from server import db as _db
    tenant_id = current_user.tenant_id
    # Pull all wrap_data docs for this tenant
    cursor = _db.wrap_data.find(
        {"tenant_id": tenant_id},
        {
            "_id": 0,
            "ticket_id": 1,
            "order_id": 1,
            "vehicle_info": 1,
            "wrap_type": 1,
            "design": 1,
            "contract": 1,
            "approvals": 1,
            "inspection": 1,
            "aftercare": 1,
            "pricing_snapshot": 1,
        },
    )
    wrap_docs = await cursor.to_list(500)
    if not wrap_docs:
        return {"items": [], "total": 0}

    # Batch-load order numbers + customer names
    order_ids = list({d.get("order_id") for d in wrap_docs if d.get("order_id")})
    orders_by_id: dict = {}
    customer_ids = set()
    if order_ids:
        async for o in _db.orders.find(
            {"id": {"$in": order_ids}, "tenant_id": tenant_id},
            {"_id": 0, "id": 1, "order_number": 1, "customer_id": 1},
        ):
            orders_by_id[o["id"]] = o
            if o.get("customer_id"):
                customer_ids.add(o["customer_id"])
    customers_by_id: dict = {}
    if customer_ids:
        async for c in _db.customers.find(
            {"id": {"$in": list(customer_ids)}, "tenant_id": tenant_id},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "name": 1, "company": 1},
        ):
            customers_by_id[c["id"]] = c

    items: list = []
    for wd in wrap_docs:
        design = wd.get("design") or {}
        contract = wd.get("contract") or {}
        approvals = wd.get("approvals") or {}
        inspection = wd.get("inspection") or {}
        aftercare = wd.get("aftercare") or {}
        snap = wd.get("pricing_snapshot") or {}

        actions: list = []
        proof_status = design.get("proof_status") or ""
        if proof_status in {"sent", "viewed"} and not approvals.get("proof_approved"):
            actions.append({"code": "proof_pending", "label": "Proof awaiting approval"})
        if proof_status == "revision_requested":
            actions.append({"code": "revision_requested", "label": "Customer requested a revision"})
        contract_status = contract.get("contract_status") or ""
        if contract_status in {"sent", "viewed"} and not approvals.get("contract_signed"):
            actions.append({"code": "contract_pending", "label": "Contract awaiting signature"})
        if snap.get("quoted_price") and not approvals.get("quote_approved"):
            actions.append({"code": "quote_pending", "label": "Quote awaiting approval"})
        if inspection.get("customer_visible") and not inspection.get("customer_acknowledged"):
            actions.append({"code": "inspection_pending", "label": "Inspection awaiting acknowledgement"})
        if aftercare.get("aftercare_sent") and not aftercare.get("customer_acknowledged"):
            actions.append({"code": "aftercare_pending", "label": "Aftercare awaiting acknowledgement"})

        if not actions:
            continue

        order = orders_by_id.get(wd.get("order_id"), {})
        customer = customers_by_id.get(order.get("customer_id"), {})
        cust_name = (
            f"{customer.get('first_name') or ''} {customer.get('last_name') or ''}".strip()
            or customer.get("name")
            or customer.get("company")
            or "—"
        )
        v = wd.get("vehicle_info") or {}
        vehicle = " ".join(b for b in [v.get("year"), v.get("make"), v.get("model")] if b).strip()

        items.append({
            "ticket_id": wd.get("ticket_id"),
            "order_id": wd.get("order_id"),
            "order_number": order.get("order_number"),
            "customer_name": cust_name,
            "customer_id": order.get("customer_id"),
            "wrap_type": wd.get("wrap_type") or "Vehicle Wrap",
            "vehicle": vehicle,
            "actions": actions,
        })

    # Sort: most-recent first by order_number string (best-effort)
    items.sort(key=lambda i: (i.get("order_number") or ""), reverse=True)
    return {"items": items, "total": len(items)}
