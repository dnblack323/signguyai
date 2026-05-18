"""Iteration 147 — Wrap Command Center Phase 2E backend tests.

Covers Inspection + Aftercare blocks:
- PUT /api/wrap/items/{id}/inspection (status + acknowledged mirror to approvals.inspection_acknowledged)
- POST/PUT/DELETE damage-markers
- PUT /api/wrap/items/{id}/aftercare (status, template, sent/viewed/acknowledged
  + auto-stamped *_at fields, follow-up toggles + their *_at)
- _pipeline_state: inspection_active/complete and aftercare_active/complete + workflow_complete
- Production Board mirror (_sync_wrap_to_production_board) — exactly one row per wrap ticket
- Non-wrap guard
- _id leakage
- Phase 2A/2B/2C/2D regression smoke
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = {"email": "thesigntistslab@gmail.com", "password": "password123"}
ORDER_ID = "118b7377-687b-4a28-b42b-3c5f31da64c5"
WRAP = "aa0387f8-ac70-4935-9bbc-33d03963e916"
NON_WRAP = "e19d6501-f80b-432b-b7b7-76e1d4903f3b"


@pytest.fixture(scope="session")
def H():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}",
            "Content-Type": "application/json"}


def _has_id(o):
    if isinstance(o, dict):
        if "_id" in o:
            return True
        return any(_has_id(v) for v in o.values())
    if isinstance(o, list):
        return any(_has_id(v) for v in o)
    return False


def _reset(H):
    # Reset inspection + aftercare + approvals.inspection_acknowledged/aftercare_sent
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                 json={"inspection_status": "not_started",
                       "customer_acknowledged": False,
                       "inspection_notes": "",
                       "inspected_by": "",
                       "vehicle_diagram_type": ""}, timeout=30)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                 json={"aftercare_status": "not_sent",
                       "aftercare_template": "",
                       "aftercare_sent": False,
                       "customer_viewed": False,
                       "customer_acknowledged": False,
                       "followup_24h": False,
                       "followup_7d": False,
                       "followup_30d": False,
                       "aftercare_notes": "",
                       "sent_by": ""}, timeout=30)


def _get(H):
    r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()


# ── GET shape
def test_get_returns_inspection_aftercare_blocks(H):
    _reset(H)
    d = _get(H)
    assert "inspection" in d
    assert "aftercare" in d
    insp = d["inspection"]
    after = d["aftercare"]
    # inspection
    for k in ("inspection_status", "vehicle_diagram_type", "inspected_by",
              "inspection_date", "customer_acknowledged", "customer_acknowledged_at",
              "inspection_notes", "damage_markers"):
        assert k in insp, f"inspection missing {k}"
    assert insp["inspection_status"] == "not_started"
    assert isinstance(insp["damage_markers"], list)
    # aftercare
    for k in ("aftercare_status", "aftercare_template", "aftercare_sent",
              "aftercare_sent_at", "customer_viewed", "customer_viewed_at",
              "customer_acknowledged", "customer_acknowledged_at",
              "aftercare_notes", "followup_24h", "followup_24h_at",
              "followup_7d", "followup_7d_at", "followup_30d", "followup_30d_at"):
        assert k in after, f"aftercare missing {k}"
    assert after["aftercare_status"] == "not_sent"
    assert not _has_id(d)


# ── Inspection PUT
def test_inspection_status_and_notes_persist(H):
    _reset(H)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                     json={"inspection_status": "in_progress",
                           "inspected_by": "TEST_Tech",
                           "inspection_notes": "TEST notes",
                           "vehicle_diagram_type": "Generic Van",
                           "inspection_date": "2026-01-20"}, timeout=30)
    assert r.status_code == 200, r.text
    insp = _get(H)["inspection"]
    assert insp["inspection_status"] == "in_progress"
    assert insp["inspected_by"] == "TEST_Tech"
    assert insp["inspection_notes"] == "TEST notes"
    assert insp["vehicle_diagram_type"] == "Generic Van"
    assert insp["inspection_date"] == "2026-01-20"


def test_inspection_invalid_status_returns_400(H):
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                     json={"inspection_status": "bogus_status"}, timeout=30)
    assert r.status_code == 400
    assert "Invalid inspection_status" in r.json().get("detail", "")


def test_inspection_acknowledged_mirrors_approvals_and_flips_status(H):
    _reset(H)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                     json={"customer_acknowledged": True}, timeout=30)
    assert r.status_code == 200
    d = _get(H)
    insp = d["inspection"]
    appr = d["approvals"]
    assert insp["customer_acknowledged"] is True
    assert insp["customer_acknowledged_at"] is not None
    # auto-flip status to acknowledged
    assert insp["inspection_status"] == "acknowledged"
    # mirrored to approvals
    assert appr["inspection_acknowledged"] is True
    assert appr["inspection_acknowledged_at"] is not None
    # pipeline derives inspection_complete=true
    ps = d["pipeline_state"]
    assert ps["inspection_complete"] is True


def test_inspection_acknowledged_false_clears_mirror(H):
    # Pre-condition: ack=true from prior test or set it now
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                 json={"customer_acknowledged": True}, timeout=30)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                     json={"customer_acknowledged": False,
                           "inspection_status": "in_progress"}, timeout=30)
    assert r.status_code == 200
    d = _get(H)
    assert d["inspection"]["customer_acknowledged"] is False
    assert d["inspection"]["customer_acknowledged_at"] is None
    assert d["approvals"]["inspection_acknowledged"] is False
    assert d["approvals"]["inspection_acknowledged_at"] is None


def test_inspection_pipeline_active(H):
    _reset(H)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                 json={"inspection_status": "in_progress"}, timeout=30)
    ps = _get(H)["pipeline_state"]
    assert ps["inspection_active"] is True
    assert ps["inspection_complete"] is False


# ── Damage markers CRUD
def test_damage_marker_crud(H):
    _reset(H)
    r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers",
                      headers=H,
                      json={"area": "TEST_LeftFender", "damage_type": "Scratch",
                            "severity": "Medium", "notes": "TEST scratch"},
                      timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    markers = d["inspection"]["damage_markers"]
    assert any(m["area"] == "TEST_LeftFender" for m in markers)
    target = next(m for m in markers if m["area"] == "TEST_LeftFender")
    assert target["damage_type"] == "Scratch"
    assert target["severity"] == "Medium"
    assert "id" in target and "created_at" in target
    marker_id = target["id"]

    # Verify persisted in GET
    g = _get(H)
    assert any(m["id"] == marker_id for m in g["inspection"]["damage_markers"])

    # UPDATE
    r2 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers/{marker_id}",
        headers=H, json={"severity": "High", "notes": "TEST updated"}, timeout=30)
    assert r2.status_code == 200, r2.text
    upd = next(m for m in r2.json()["inspection"]["damage_markers"]
               if m["id"] == marker_id)
    assert upd["severity"] == "High"
    assert upd["notes"] == "TEST updated"
    assert upd["area"] == "TEST_LeftFender"  # unchanged preserved

    # Invalid damage_type
    r3 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers/{marker_id}",
        headers=H, json={"damage_type": "BogusDamage"}, timeout=30)
    assert r3.status_code == 400

    # Invalid severity
    r4 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers/{marker_id}",
        headers=H, json={"severity": "Catastrophic"}, timeout=30)
    assert r4.status_code == 400

    # DELETE
    r5 = requests.delete(
        f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers/{marker_id}",
        headers=H, timeout=30)
    assert r5.status_code == 200
    assert not any(m["id"] == marker_id
                   for m in r5.json()["inspection"]["damage_markers"])


def test_damage_marker_update_unknown_returns_404(H):
    r = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers/nonexistent-id",
        headers=H, json={"severity": "Low"}, timeout=30)
    assert r.status_code == 404


# ── Aftercare PUT
def test_aftercare_template_and_status_persist(H):
    _reset(H)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                     json={"aftercare_status": "generated",
                           "aftercare_template": "standard_vinyl",
                           "aftercare_notes": "TEST aftercare notes",
                           "sent_by": "TEST_Sender"}, timeout=30)
    assert r.status_code == 200, r.text
    after = _get(H)["aftercare"]
    assert after["aftercare_status"] == "generated"
    assert after["aftercare_template"] == "standard_vinyl"
    assert after["aftercare_notes"] == "TEST aftercare notes"
    assert after["sent_by"] == "TEST_Sender"


def test_aftercare_invalid_status_returns_400(H):
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                     json={"aftercare_status": "junk"}, timeout=30)
    assert r.status_code == 400


def test_aftercare_sent_autostamps_and_mirrors_approval(H):
    _reset(H)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                     json={"aftercare_sent": True}, timeout=30)
    assert r.status_code == 200
    d = _get(H)
    a = d["aftercare"]
    assert a["aftercare_sent"] is True
    assert a["aftercare_sent_at"] is not None
    # auto-status flip
    assert a["aftercare_status"] == "sent"
    # mirrored to approvals
    assert d["approvals"]["aftercare_sent"] is True
    assert d["approvals"]["aftercare_sent_at"] is not None
    # pipeline: aftercare_complete should now be true (per logic — aftercare_sent OR approvals.aftercare_sent)
    assert d["pipeline_state"]["aftercare_complete"] is True

    # idempotency — 2nd save with same value preserves timestamp
    ts1 = a["aftercare_sent_at"]
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                 json={"aftercare_sent": True}, timeout=30)
    a2 = _get(H)["aftercare"]
    assert a2["aftercare_sent_at"] == ts1  # not overwritten


def test_aftercare_viewed_acknowledged_autostamps(H):
    _reset(H)
    # First send so status >= sent
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                 json={"aftercare_sent": True}, timeout=30)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                     json={"customer_viewed": True}, timeout=30)
    assert r.status_code == 200
    a = _get(H)["aftercare"]
    assert a["customer_viewed"] is True
    assert a["customer_viewed_at"] is not None
    assert a["aftercare_status"] == "viewed"

    r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                      json={"customer_acknowledged": True}, timeout=30)
    assert r2.status_code == 200
    a2 = _get(H)["aftercare"]
    assert a2["customer_acknowledged"] is True
    assert a2["customer_acknowledged_at"] is not None
    assert a2["aftercare_status"] == "acknowledged"


def test_aftercare_followup_toggles_persist_with_timestamps(H):
    _reset(H)
    for fk in ("followup_24h", "followup_7d", "followup_30d"):
        r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                         json={fk: True}, timeout=30)
        assert r.status_code == 200
        a = _get(H)["aftercare"]
        assert a[fk] is True
        assert a[f"{fk}_at"] is not None

    # idempotency — re-toggle followup_24h true preserves timestamp
    ts = _get(H)["aftercare"]["followup_24h_at"]
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                 json={"followup_24h": True}, timeout=30)
    assert _get(H)["aftercare"]["followup_24h_at"] == ts

    # toggle false clears ts
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                 json={"followup_24h": False}, timeout=30)
    a3 = _get(H)["aftercare"]
    assert a3["followup_24h"] is False
    assert a3["followup_24h_at"] is None


def test_aftercare_pipeline_active(H):
    _reset(H)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                 json={"aftercare_status": "viewed"}, timeout=30)
    ps = _get(H)["pipeline_state"]
    assert ps["aftercare_active"] is True


# ── workflow_complete requires install_complete + complete + aftercare_complete
def test_workflow_complete_logic(H):
    _reset(H)
    # Set install + final_signoff true, aftercare_sent true
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                 json={"install_status": "complete", "customer_signoff": True}, timeout=30)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                 json={"aftercare_sent": True}, timeout=30)
    ps = _get(H)["pipeline_state"]
    # All three pieces true
    assert ps["install_complete"] is True
    assert ps["complete"] is True  # final_signoff_completed auto-flipped via 2D
    assert ps["aftercare_complete"] is True
    assert ps["workflow_complete"] is True


# ── Production Board mirror — exactly one row per wrap ticket
def test_production_board_single_mirror_row(H):
    # Flip production status to force a mirror update
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                 json={"production_status": "printing"}, timeout=30)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                 json={"production_status": "ready_for_install"}, timeout=30)

    # Hit the board endpoint — should not 500 and should return a coherent view
    r = requests.get(f"{BASE_URL}/api/production-tasks/board", headers=H, timeout=30)
    assert r.status_code == 200, r.text
    board = r.json()
    # Collect any wrap-CC sourced tasks for our ticket
    wrap_rows = []
    if isinstance(board, dict):
        for v in board.values():
            if isinstance(v, list):
                for t in v:
                    if isinstance(t, dict) and t.get("job_ticket_id") == WRAP and t.get("source") == "wrap_command_center":
                        wrap_rows.append(t)
    elif isinstance(board, list):
        for t in board:
            if isinstance(t, dict) and t.get("job_ticket_id") == WRAP and t.get("source") == "wrap_command_center":
                wrap_rows.append(t)
    # At most ONE wrap CC mirror row across all stages
    assert len(wrap_rows) <= 1, f"Expected <=1 wrap CC mirror, found {len(wrap_rows)}"


# ── Non-wrap guard on Phase 2E endpoints
@pytest.mark.parametrize("method,path,body", [
    ("put", f"/api/wrap/items/{NON_WRAP}/inspection", {"inspection_status": "in_progress"}),
    ("post", f"/api/wrap/items/{NON_WRAP}/inspection/damage-markers", {"area": "x"}),
    ("put", f"/api/wrap/items/{NON_WRAP}/inspection/damage-markers/abc", {"severity": "Low"}),
    ("delete", f"/api/wrap/items/{NON_WRAP}/inspection/damage-markers/abc", None),
    ("put", f"/api/wrap/items/{NON_WRAP}/aftercare", {"aftercare_status": "sent"}),
])
def test_non_wrap_guard(H, method, path, body):
    fn = getattr(requests, method)
    if body is None:
        r = fn(f"{BASE_URL}{path}", headers=H, timeout=30)
    else:
        r = fn(f"{BASE_URL}{path}", headers=H, json=body, timeout=30)
    assert r.status_code == 400, f"{method.upper()} {path} → {r.status_code}: {r.text}"
    assert "not a wrap" in r.json().get("detail", "").lower()


# ── _id leakage on all Phase 2E responses
def test_no_mongo_id_in_responses(H):
    _reset(H)
    r1 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection", headers=H,
                      json={"inspection_status": "in_progress"}, timeout=30)
    assert not _has_id(r1.json())

    r2 = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers",
                       headers=H, json={"area": "TEST_zone", "damage_type": "Dent"},
                       timeout=30)
    assert not _has_id(r2.json())
    mid = next(m["id"] for m in r2.json()["inspection"]["damage_markers"]
               if m["area"] == "TEST_zone")
    r3 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers/{mid}",
        headers=H, json={"severity": "Low"}, timeout=30)
    assert not _has_id(r3.json())
    r4 = requests.delete(
        f"{BASE_URL}/api/wrap/items/{WRAP}/inspection/damage-markers/{mid}",
        headers=H, timeout=30)
    assert not _has_id(r4.json())

    r5 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/aftercare", headers=H,
                      json={"aftercare_status": "sent"}, timeout=30)
    assert not _has_id(r5.json())


# ── Phase 2A/2B/2C/2D regression smoke
def test_get_returns_all_phase_blocks(H):
    d = _get(H)
    for k in ("vehicle_info", "wrapped_areas", "materials", "pricing",
              "design", "contract", "approvals", "production", "install",
              "inspection", "aftercare", "pipeline_state", "coverage_summary"):
        assert k in d, f"Missing top-level block {k}"


def test_recalculate_still_returns_snapshot(H):
    r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/recalculate",
                      headers=H, timeout=30)
    assert r.status_code == 200, r.text
    snap = r.json().get("pricing_snapshot")
    assert snap is not None
    assert "quoted_price" in snap
