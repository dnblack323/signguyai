"""Iteration 146 — Wrap Command Center Phase 2D backend tests.

Covers Production + Install blocks: PUT /production, production task CRUD +
load-defaults, PUT /install (including customer_signoff auto-flip to
approvals.final_signoff_completed), install checklist partial merge, install
issue log CRUD, pipeline_state production_complete / install_active /
install_complete, non-wrap guard, _id leakage, and Phase 2A/B/C regression smoke.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = {"email": "thesigntistslab@gmail.com", "password": "password123"}
ORDER_ID = "118b7377-687b-4a28-b42b-3c5f31da64c5"
WRAP = "aa0387f8-ac70-4935-9bbc-33d03963e916"
NON_WRAP = "e19d6501-f80b-432b-b7b7-76e1d4903f3b"

PRODUCTION_CHECKLIST = [
    "files_ready", "materials_pulled", "printed", "laminated", "outgassed",
    "trimmed", "panels_labeled", "install_kit_ready", "prep_complete", "ready_for_install",
]
INSTALL_CHECKLIST = [
    "vehicle_received", "vehicle_inspected", "surface_cleaned",
    "old_graphics_removed", "panels_staged", "install_started",
    "install_completed", "post_heated", "final_inspection_complete",
    "customer_walkthrough_complete",
]


@pytest.fixture(scope="session")
def H():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    tok = r.json()["access_token"]
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def _has_id(o):
    if isinstance(o, dict):
        if "_id" in o:
            return True
        return any(_has_id(v) for v in o.values())
    if isinstance(o, list):
        return any(_has_id(v) for v in o)
    return False


def _reset_state(H):
    # neutral state for repeatable tests
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                 json={"install_status": "not_scheduled", "customer_signoff": False}, timeout=30)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/approvals", headers=H,
                 json={"final_signoff_completed": False}, timeout=30)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                 json={"production_status": "not_started"}, timeout=30)


# ── GET shape (production + install blocks)
def test_get_returns_production_install_blocks(H):
    r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "production" in d and "install" in d
    for k in PRODUCTION_CHECKLIST:
        assert k in d["production"], f"missing prod.{k}"
        assert f"{k}_at" in d["production"], f"missing prod.{k}_at"
    for must in ("production_status", "assigned_to", "production_notes", "tasks"):
        assert must in d["production"]
    assert "checklist" in d["install"]
    for k in INSTALL_CHECKLIST:
        assert k in d["install"]["checklist"]
    assert "issues" in d["install"]
    assert not _has_id(d), "Mongo _id leaked in GET"
    ps = d["pipeline_state"]
    for k in ("production_complete", "install_active", "install_complete", "complete"):
        assert k in ps


# ── PUT /production subset
def test_production_subset_sets_timestamps_and_preserves(H):
    _reset_state(H)
    # First persist a baseline value to verify preservation later
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                 json={"production_notes": "phase2d notes baseline"}, timeout=30)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                     json={"production_status": "printing", "assigned_to": "Sam Q.",
                           "printed": True, "files_ready": True}, timeout=30)
    assert r.status_code == 200
    p = r.json()["production"]
    assert p["production_status"] == "printing"
    assert p["assigned_to"] == "Sam Q."
    assert p["printed"] is True and p["printed_at"]
    assert p["files_ready"] is True and p["files_ready_at"]
    assert p["production_notes"] == "phase2d notes baseline"  # preserved


def test_production_checklist_off_clears_and_idempotent(H):
    # Turn ON files_ready, capture ts, re-PUT true, ts must be unchanged
    r1 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                      json={"files_ready": True}, timeout=30)
    ts1 = r1.json()["production"]["files_ready_at"]
    assert ts1
    r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                      json={"files_ready": True}, timeout=30)
    assert r2.json()["production"]["files_ready_at"] == ts1
    # Toggle OFF clears
    r3 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                      json={"files_ready": False}, timeout=30)
    p3 = r3.json()["production"]
    assert p3["files_ready"] is False
    assert p3["files_ready_at"] is None
    # Toggle ON again — new ts
    r4 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                      json={"files_ready": True}, timeout=30)
    assert r4.json()["production"]["files_ready_at"]


def test_production_invalid_status_returns_400(H):
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                     json={"production_status": "nuke"}, timeout=30)
    assert r.status_code == 400


# ── Tasks
def test_tasks_load_defaults_idempotent(H):
    # Clear all tasks first by deleting them individually
    g = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30).json()
    for t in g["production"]["tasks"]:
        requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks/{t['id']}",
                        headers=H, timeout=30)
    r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks/load-defaults",
                      headers=H, timeout=30)
    assert r.status_code == 200
    tasks = r.json()["production"]["tasks"]
    assert len(tasks) == 10
    names = [t["task_name"] for t in tasks]
    assert "Print wrap panels" in names
    assert "Stage for install" in names
    # 2nd call must be no-op
    r2 = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks/load-defaults",
                       headers=H, timeout=30)
    assert len(r2.json()["production"]["tasks"]) == 10


def test_task_add_update_delete(H):
    r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks", headers=H,
                      json={"task_name": "Trim driver door", "assigned_to": "Sam",
                            "estimated_minutes": 30}, timeout=30)
    assert r.status_code == 200
    tasks = r.json()["production"]["tasks"]
    new = next(t for t in tasks if t["task_name"] == "Trim driver door")
    assert new["status"] == "not_started"
    assert new["completed_at"] is None
    tid = new["id"]

    # Update to complete -> completed_at set
    r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks/{tid}",
                      headers=H, json={"status": "complete", "actual_minutes": 25}, timeout=30)
    upd = next(t for t in r2.json()["production"]["tasks"] if t["id"] == tid)
    assert upd["status"] == "complete"
    assert upd["completed_at"]
    assert upd["actual_minutes"] == 25

    # Back to in_progress -> completed_at cleared
    r3 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks/{tid}",
                      headers=H, json={"status": "in_progress"}, timeout=30)
    upd2 = next(t for t in r3.json()["production"]["tasks"] if t["id"] == tid)
    assert upd2["status"] == "in_progress"
    assert upd2["completed_at"] is None

    # Invalid status -> 400
    r4 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks/{tid}",
                      headers=H, json={"status": "nuke"}, timeout=30)
    assert r4.status_code == 400

    # Delete
    r5 = requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP}/production/tasks/{tid}",
                         headers=H, timeout=30)
    assert r5.status_code == 200
    assert all(t["id"] != tid for t in r5.json()["production"]["tasks"])


# ── Install PUT
def test_install_subset_and_preserves(H):
    _reset_state(H)
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                 json={"install_notes": "be careful with chrome trim"}, timeout=30)
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                     json={"install_status": "scheduled", "install_date": "2026-05-25",
                           "install_start_time": "09:00", "installer_name": "Jake",
                           "hours_estimated": 8, "install_location": "Bay 2",
                           "bay_needed": True}, timeout=30)
    assert r.status_code == 200, r.text
    i = r.json()["install"]
    assert i["install_status"] == "scheduled"
    assert i["install_date"] == "2026-05-25"
    assert i["install_start_time"] == "09:00"
    assert i["installer_name"] == "Jake"
    assert i["hours_estimated"] == 8
    assert i["install_location"] == "Bay 2"
    assert i["bay_needed"] is True
    assert i.get("install_notes") == "be careful with chrome trim"


def test_install_customer_signoff_idempotent_and_clear(H):
    _reset_state(H)
    r1 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                      json={"customer_signoff": True}, timeout=30)
    i1 = r1.json()["install"]
    assert i1["customer_signoff"] is True
    ts = i1["customer_signoff_at"]
    assert ts
    r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                      json={"customer_signoff": True}, timeout=30)
    assert r2.json()["install"]["customer_signoff_at"] == ts
    r3 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                      json={"customer_signoff": False}, timeout=30)
    i3 = r3.json()["install"]
    assert i3["customer_signoff"] is False
    assert i3["customer_signoff_at"] is None


def test_final_signoff_autoflip(H):
    _reset_state(H)
    # complete alone — should NOT autoflip
    r1 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                      json={"install_status": "complete"}, timeout=30)
    assert r1.status_code == 200
    assert r1.json()["approvals"]["final_signoff_completed"] is False

    # signoff alone (back to scheduled) — should NOT autoflip
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                 json={"install_status": "scheduled"}, timeout=30)
    r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                      json={"customer_signoff": True}, timeout=30)
    assert r2.json()["approvals"]["final_signoff_completed"] is False

    # Now flip status -> complete (signoff already true) — SHOULD autoflip
    r3 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                      json={"install_status": "complete"}, timeout=30)
    d3 = r3.json()
    assert d3["install"]["install_status"] == "complete"
    assert d3["approvals"]["final_signoff_completed"] is True
    assert d3["approvals"]["final_signoff_completed_at"]


def test_install_checklist_partial_merge(H):
    # set one key true
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                 json={"checklist": {"surface_cleaned": True}}, timeout=30)
    # set another key, surface_cleaned must remain
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                     json={"checklist": {"vehicle_received": True}}, timeout=30)
    cl = r.json()["install"]["checklist"]
    assert cl["surface_cleaned"] is True
    assert cl["vehicle_received"] is True
    # unknown key -> 400
    r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                      json={"checklist": {"bogus_key": True}}, timeout=30)
    assert r2.status_code == 400


def test_install_invalid_status_returns_400(H):
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                     json={"install_status": "nuke"}, timeout=30)
    assert r.status_code == 400


# ── Issues
def test_issues_crud_and_idempotent_resolved_at(H):
    r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/install/issues", headers=H,
                      json={"issue_type": "Misprint", "area": "driver door",
                            "description": "color shift"}, timeout=30)
    assert r.status_code == 200
    issues = r.json()["install"]["issues"]
    new = issues[-1]
    assert new["issue_type"] == "Misprint"
    assert new["resolved"] is False
    assert new["resolved_at"] is None
    assert new["created_at"]
    iid = new["id"]

    # Resolve
    r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install/issues/{iid}", headers=H,
                      json={"resolved": True, "resolution_notes": "reprinted panel"}, timeout=30)
    upd = next(i for i in r2.json()["install"]["issues"] if i["id"] == iid)
    assert upd["resolved"] is True
    assert upd["resolved_at"]
    ts = upd["resolved_at"]
    # Idempotent
    r3 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install/issues/{iid}", headers=H,
                      json={"resolved": True}, timeout=30)
    upd2 = next(i for i in r3.json()["install"]["issues"] if i["id"] == iid)
    assert upd2["resolved_at"] == ts
    # Re-open
    r4 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install/issues/{iid}", headers=H,
                      json={"resolved": False}, timeout=30)
    upd3 = next(i for i in r4.json()["install"]["issues"] if i["id"] == iid)
    assert upd3["resolved"] is False
    assert upd3["resolved_at"] is None
    # Delete
    r5 = requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP}/install/issues/{iid}",
                         headers=H, timeout=30)
    assert r5.status_code == 200
    assert all(i["id"] != iid for i in r5.json()["install"]["issues"])


def test_issue_invalid_type_returns_400(H):
    r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/install/issues", headers=H,
                      json={"issue_type": "Aliens", "description": "x"}, timeout=30)
    assert r.status_code == 400


# ── Pipeline state derivation
def test_pipeline_state_production_install(H):
    _reset_state(H)
    # production=complete -> production_complete True
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                     json={"production_status": "complete"}, timeout=30)
    g = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30).json()
    assert g["pipeline_state"]["production_complete"] is True

    # install=scheduled -> install_active True, install_complete False
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                 json={"install_status": "scheduled"}, timeout=30)
    g2 = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30).json()
    assert g2["pipeline_state"]["install_active"] is True
    assert g2["pipeline_state"]["install_complete"] is False

    # install=complete -> install_complete True
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/install", headers=H,
                 json={"install_status": "complete"}, timeout=30)
    g3 = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30).json()
    assert g3["pipeline_state"]["install_complete"] is True

    # ready_for_install also counts as production_complete
    requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                 json={"production_status": "ready_for_install"}, timeout=30)
    g4 = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30).json()
    assert g4["pipeline_state"]["production_complete"] is True


# ── Non-wrap guard on all new endpoints
@pytest.mark.parametrize("method,path,body", [
    ("PUT", "/production", {"production_status": "printing"}),
    ("POST", "/production/tasks", {"task_name": "x"}),
    ("POST", "/production/tasks/load-defaults", None),
    ("PUT", "/production/tasks/some-id", {"status": "complete"}),
    ("DELETE", "/production/tasks/some-id", None),
    ("PUT", "/install", {"install_status": "scheduled"}),
    ("POST", "/install/issues", {"issue_type": "Other"}),
    ("PUT", "/install/issues/some-id", {"resolved": True}),
    ("DELETE", "/install/issues/some-id", None),
])
def test_non_wrap_guard(H, method, path, body):
    url = f"{BASE_URL}/api/wrap/items/{NON_WRAP}{path}"
    r = requests.request(method, url, headers=H, json=body, timeout=30)
    assert r.status_code == 400, f"{method} {path} -> {r.status_code}"
    assert "not a wrap" in r.text.lower()


# ── No mongo _id anywhere
def test_no_mongo_id_anywhere(H):
    g = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30).json()
    assert not _has_id(g)
    # Also confirm on a PUT response
    r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP}/production", headers=H,
                     json={"production_status": "printing"}, timeout=30)
    assert not _has_id(r.json())


# ── Regressions: Phase 2A/2B/2C
def test_regression_phase2abc(H):
    g = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP}", headers=H, timeout=30).json()
    for k in ("vehicle_info", "wrapped_areas", "materials", "pricing",
              "design", "contract", "approvals"):
        assert k in g
    r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP}/recalculate", headers=H, timeout=30)
    assert r.status_code == 200
    assert "pricing_snapshot" in r.json()
