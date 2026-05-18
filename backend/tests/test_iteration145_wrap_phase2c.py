"""Iteration 145 — Wrap Command Center Phase 2C backend tests.

Covers:
- Design block PUT + send-questionnaire + proof versions CRUD
- Contract block PUT + contract/action (5 actions + invalid)
- Approvals PUT with timestamp idempotency + clearing
- Draft-updated-quote-message email draft
- Pipeline state derivation
- Non-wrap guard on all new endpoints
- No mongo _id in response
- Phase 2A/2B regression smoke
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN = {"email": "thesigntistslab@gmail.com", "password": "password123"}
ORDER_ID = "118b7377-687b-4a28-b42b-3c5f31da64c5"
WRAP_TICKET = "aa0387f8-ac70-4935-9bbc-33d03963e916"
NON_WRAP_TICKET = "e19d6501-f80b-432b-b7b7-76e1d4903f3b"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _has_id(o):
    if isinstance(o, dict):
        if "_id" in o:
            return True
        return any(_has_id(v) for v in o.values())
    if isinstance(o, list):
        return any(_has_id(v) for v in o)
    return False


# ── GET base shape
def test_get_returns_phase2c_blocks(H):
    r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H, timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ("design", "contract", "approvals", "pipeline_state"):
        assert k in d, f"missing top-level {k}"
    # Approvals has all keys + _at
    for k in [
        "quote_approved", "contract_signed", "deposit_paid", "proof_approved",
        "inspection_acknowledged", "final_signoff_completed", "aftercare_sent",
    ]:
        assert k in d["approvals"]
        assert f"{k}_at" in d["approvals"]
    assert not _has_id(d), "Mongo _id leaked"


# ── Design PUT subset / exclude_unset
def test_design_subset_persists(H):
    r = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design",
        headers=H,
        json={"design_brief": "Brand-forward modern look"},
        timeout=30,
    )
    assert r.status_code == 200
    assert r.json()["design"]["design_brief"] == "Brand-forward modern look"
    # second update only touches one field
    r2 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design",
        headers=H,
        json={"style_direction": "Aggressive racing stripes"},
        timeout=30,
    )
    d2 = r2.json()["design"]
    assert d2["style_direction"] == "Aggressive racing stripes"
    assert d2["design_brief"] == "Brand-forward modern look"


def test_design_proof_status_approved_flips_approvals(H):
    r = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design",
        headers=H,
        json={"proof_status": "approved"},
        timeout=30,
    )
    assert r.status_code == 200
    d = r.json()
    assert d["design"]["proof_status"] == "approved"
    assert d["approvals"]["proof_approved"] is True
    assert d["approvals"]["proof_approved_at"]
    # reset back so other tests are deterministic
    requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design",
        headers=H, json={"proof_status": "not_started"}, timeout=30,
    )
    requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/approvals",
        headers=H, json={"proof_approved": False}, timeout=30,
    )


def test_send_questionnaire(H):
    r = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design/send-questionnaire",
        headers=H, timeout=30,
    )
    assert r.status_code == 200
    d = r.json()["design"]
    assert d["questionnaire_status"] == "sent"
    assert d["questionnaire_sent_at"]


def test_proof_versions_crud(H):
    r = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design/proofs",
        headers=H, json={"label": "V1", "notes": "first round"}, timeout=30,
    )
    assert r.status_code == 200
    proofs = r.json()["design"]["proof_versions"]
    new_proof = next((p for p in proofs if p.get("label") == "V1" and p.get("notes") == "first round"), None)
    assert new_proof
    pid = new_proof["id"]
    assert new_proof["status"] == "draft"
    assert new_proof["created_at"]
    assert new_proof["approved_at"] is None

    # approve it
    r2 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design/proofs/{pid}",
        headers=H, json={"status": "approved"}, timeout=30,
    )
    assert r2.status_code == 200
    d = r2.json()
    proof = next(p for p in d["design"]["proof_versions"] if p["id"] == pid)
    assert proof["status"] == "approved"
    assert proof["approved_at"]
    assert d["design"]["proof_status"] == "approved"
    assert d["design"]["approved_proof_id"] == pid
    assert d["approvals"]["proof_approved"] is True

    # delete it
    r3 = requests.delete(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design/proofs/{pid}",
        headers=H, timeout=30,
    )
    assert r3.status_code == 200
    assert all(p["id"] != pid for p in r3.json()["design"]["proof_versions"])
    # reset approval flag for determinism
    requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/approvals",
        headers=H, json={"proof_approved": False}, timeout=30,
    )
    requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/design",
        headers=H, json={"proof_status": "not_started"}, timeout=30,
    )


# ── Contract PUT (subset) + action
def test_contract_put_subset(H):
    r = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract",
        headers=H, json={"contract_template": "standard_wrap_v1"}, timeout=30,
    )
    assert r.status_code == 200
    assert r.json()["contract"]["contract_template"] == "standard_wrap_v1"
    r2 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract",
        headers=H, json={"contract_notes": "rush install"}, timeout=30,
    )
    c = r2.json()["contract"]
    assert c["contract_template"] == "standard_wrap_v1"  # unchanged
    assert c["contract_notes"] == "rush install"


def test_contract_generate_draft_seeds_terms_only_if_empty(H):
    # First clear terms_summary to make sure seeding fires
    requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract",
        headers=H, json={"terms_summary": ""}, timeout=30,
    )
    r = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "generate_draft"}, timeout=30,
    )
    assert r.status_code == 200
    c = r.json()["contract"]
    assert c["contract_status"] == "draft"
    seeded_terms = c["terms_summary"]
    assert seeded_terms and "deposit" in seeded_terms.lower()
    # Now set custom terms and re-run generate_draft — must NOT overwrite
    custom = "1. Custom term A\n2. Custom term B"
    requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract",
        headers=H, json={"terms_summary": custom}, timeout=30,
    )
    r2 = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "generate_draft"}, timeout=30,
    )
    assert r2.json()["contract"]["terms_summary"] == custom


def test_contract_actions_progression(H):
    # send
    r = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "send"}, timeout=30,
    )
    c = r.json()["contract"]
    assert c["contract_status"] == "sent"
    ts1 = c["contract_sent_at"]
    assert ts1
    # idempotent
    r2 = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "send"}, timeout=30,
    )
    assert r2.json()["contract"]["contract_sent_at"] == ts1

    # mark_viewed
    r3 = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "mark_viewed"}, timeout=30,
    )
    c3 = r3.json()["contract"]
    assert c3["contract_status"] == "viewed"
    assert c3["contract_viewed_at"]

    # mark_signed
    r4 = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "mark_signed", "signed_by": "Keith Johnson"}, timeout=30,
    )
    d4 = r4.json()
    assert d4["contract"]["contract_status"] == "signed"
    assert d4["contract"]["accepted_terms"] is True
    assert d4["contract"]["signed_by"] == "Keith Johnson"
    assert d4["contract"]["contract_signed_at"]
    assert d4["approvals"]["contract_signed"] is True
    assert d4["approvals"]["contract_signed_at"]

    # store_signed
    url = "https://example.com/signed-contract.pdf"
    r5 = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "store_signed", "signed_contract_url": url}, timeout=30,
    )
    c5 = r5.json()["contract"]
    assert c5["contract_status"] == "stored"
    assert c5["signed_contract_url"] == url


def test_contract_action_invalid_returns_400(H):
    r = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/contract/action",
        headers=H, json={"action": "nuke"}, timeout=30,
    )
    assert r.status_code == 400
    assert "allowed" in r.text.lower() or "Allowed" in r.text


# ── Approvals
def test_approvals_set_clears_and_idempotent(H):
    # Set quote_approved true
    r = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/approvals",
        headers=H, json={"quote_approved": True, "deposit_paid": True}, timeout=30,
    )
    assert r.status_code == 200
    a = r.json()["approvals"]
    assert a["quote_approved"] is True
    assert a["quote_approved_at"]
    assert a["deposit_paid"] is True
    assert a["deposit_paid_at"]
    ts = a["quote_approved_at"]
    # Idempotent: re-set true keeps timestamp
    r2 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/approvals",
        headers=H, json={"quote_approved": True}, timeout=30,
    )
    assert r2.json()["approvals"]["quote_approved_at"] == ts
    # set false clears
    r3 = requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/approvals",
        headers=H, json={"quote_approved": False}, timeout=30,
    )
    a3 = r3.json()["approvals"]
    assert a3["quote_approved"] is False
    assert a3["quote_approved_at"] is None


# ── Draft updated quote
def test_draft_updated_quote(H):
    # ensure a pricing_snapshot exists
    requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/recalculate", headers=H, timeout=30)
    r = requests.post(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/draft-updated-quote-message",
        headers=H, timeout=30,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("to", "subject", "body", "quote_amount", "deposit_amount",
              "balance_amount", "order_number", "vehicle_summary", "wrap_type", "customer_name"):
        assert k in d, f"missing {k}"
    if d["order_number"]:
        assert d["subject"] == f"Updated Wrap Quote for Order #{d['order_number']}"
    # math
    assert round(d["deposit_amount"], 2) == round(d["quote_amount"] / 2.0, 2)
    assert round(d["balance_amount"], 2) == round(d["quote_amount"] - d["deposit_amount"], 2)
    # body content
    body = d["body"]
    assert "Payment link will be connected in a later phase." in body
    # quote amount in body must match the pricing snapshot
    gd = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H, timeout=30).json()
    snap_quoted = float((gd.get("pricing_snapshot") or {}).get("quoted_price") or 0)
    if snap_quoted:
        assert abs(snap_quoted - d["quote_amount"]) < 0.01


# ── Pipeline state derivation
def test_pipeline_state(H):
    # set some flags deterministically
    requests.put(
        f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/approvals", headers=H,
        json={"quote_approved": True, "deposit_paid": True, "final_signoff_completed": False}, timeout=30,
    )
    r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H, timeout=30)
    d = r.json()
    ps = d["pipeline_state"]
    snap = d.get("pricing_snapshot") or {}
    contract_status = (d.get("contract") or {}).get("contract_status")
    assert ps["measurements_complete"] == any(a.get("included") for a in d.get("wrapped_areas") or [])
    assert ps["estimate_complete"] == bool(snap.get("quoted_price"))
    assert ps["quote_sent"] is True
    assert ps["deposit_paid"] is True
    assert ps["contract_signed"] == (contract_status in {"signed", "stored"} or d["approvals"]["contract_signed"])
    assert ps["complete"] is False


# ── Non-wrap guard on every new endpoint
@pytest.mark.parametrize("method,path,body", [
    ("PUT", "/design", {"design_brief": "x"}),
    ("POST", "/design/send-questionnaire", None),
    ("POST", "/design/proofs", {"label": "V1"}),
    ("PUT", "/contract", {"contract_notes": "x"}),
    ("POST", "/contract/action", {"action": "generate_draft"}),
    ("PUT", "/approvals", {"quote_approved": True}),
    ("POST", "/draft-updated-quote-message", None),
])
def test_non_wrap_guard(H, method, path, body):
    url = f"{BASE_URL}/api/wrap/items/{NON_WRAP_TICKET}{path}"
    r = requests.request(method, url, headers=H, json=body, timeout=30)
    assert r.status_code == 400, f"{method} {path} -> {r.status_code}: {r.text}"
    assert "not a wrap" in r.text.lower()


# ── Phase 2A/2B regression smoke
def test_regression_get_items_and_recalc(H):
    r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert "vehicle_info" in d and "wrapped_areas" in d and "materials" in d and "pricing" in d
    r2 = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/recalculate", headers=H, timeout=30)
    assert r2.status_code == 200
    assert "pricing_snapshot" in r2.json()


def test_no_mongo_id_anywhere(H):
    r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H, timeout=30)
    assert not _has_id(r.json())
