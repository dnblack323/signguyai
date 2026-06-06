"""Phase 6 — Admin progress endpoint + stage stamping tests."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://action-central-35.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
OWNER_EMAIL = "phase5-owner-test@example.com"
OWNER_PASSWORD = "OwnerPass123!"
STORE_ID = "fc0bad7e-9040-477e-93b9-a3f0b1a2df90"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# --- TEST 1: admin-progress GET schema + finance parity with analytics ---
def test_admin_progress_schema(admin_headers):
    r = requests.get(f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress", headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "store" in d
    assert "current_stage" in d
    assert "stages" in d and len(d["stages"]) == 15, f"expected 15 stages got {len(d.get('stages', []))}"
    assert "required_actions" in d and len(d["required_actions"]) == 6, f"expected 6 actions got {len(d.get('required_actions', []))}"
    assert "finance" in d
    assert "formula" in d["finance"]
    assert "payout_history" in d
    assert "privacy_note" in d


def test_admin_progress_finance_matches_analytics(admin_headers):
    p = requests.get(f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress", headers=admin_headers, timeout=30).json()
    a = requests.get(f"{BASE_URL}/api/webstores/v2/{STORE_ID}/analytics", headers=admin_headers, timeout=30).json()
    gross = float(p["finance"]["gross_sales"])
    total_rev = float(a["summary"]["total_revenue"])
    assert abs(gross - total_rev) < 0.01, f"finance drift: progress.gross_sales={gross} vs analytics.total_revenue={total_rev}"


# --- TEST 2: PATCH stamp persistence (production / ready / completed) ---
def _db_doc_snapshot():
    """Read the raw mongo doc to verify stage timestamps that the GET /v2/{id}
    response model strips out (Webstore response_model doesn't declare
    production_started_at / completed_at fields)."""
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    async def m():
        client = AsyncIOMotorClient(os.environ['MONGO_URL'])
        db = client[os.environ['DB_NAME']]
        d = await db.webstores_v2.find_one({"id": STORE_ID}, {"_id": 0})
        client.close()
        return d
    return asyncio.run(m())


def test_admin_stamp_production_set_and_clear(admin_headers):
    # Set
    r = requests.patch(
        f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress",
        headers=admin_headers,
        json={"mark_production_started": True},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    doc = _db_doc_snapshot()
    assert doc and doc.get("production_started_at"), "production_started_at not persisted on doc"

    # Clear
    r2 = requests.patch(
        f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress",
        headers=admin_headers,
        json={"mark_production_started": False},
        timeout=30,
    )
    assert r2.status_code == 200
    doc2 = _db_doc_snapshot()
    assert not doc2.get("production_started_at"), "production_started_at should be unset"


def test_admin_stamp_completed_flips_status(admin_headers):
    pre = _db_doc_snapshot()
    original_status = pre.get("status") if pre else "active"

    r = requests.patch(
        f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress",
        headers=admin_headers,
        json={"mark_completed": True},
        timeout=30,
    )
    assert r.status_code == 200
    doc = _db_doc_snapshot()
    assert doc.get("status") == "completed", f"status not flipped to completed (got {doc.get('status')})"
    assert doc.get("completed_at"), "completed_at not persisted"

    # Note: GET /api/webstores/v2/{id} returns 500 here because
    # WebstoreStatus enum doesn't include 'completed' (see iteration_170 report).

    # Cleanup
    requests.patch(
        f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress",
        headers=admin_headers,
        json={"mark_completed": False},
        timeout=30,
    )
    # Restore status directly in DB (PUT would also 500 due to enum)
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    async def m():
        client = AsyncIOMotorClient(os.environ['MONGO_URL'])
        db = client[os.environ['DB_NAME']]
        await db.webstores_v2.update_one({"id": STORE_ID}, {"$set": {"status": original_status or "active"}})
        client.close()
    asyncio.run(m())


# --- TEST 3: admin-progress 404 / tenant guard ---
def test_admin_progress_404_for_unknown_id(admin_headers):
    r = requests.get(
        f"{BASE_URL}/api/webstores/v2/00000000-0000-0000-0000-000000000000/admin-progress",
        headers=admin_headers,
        timeout=30,
    )
    assert r.status_code == 404


def test_admin_progress_requires_auth():
    r = requests.get(f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress", timeout=30)
    assert r.status_code in (401, 403)


# --- TEST 11: existing flows still work ---
def test_owner_progress_still_works():
    """Phase 5 owner GET still functional (no regression after _build_store_progress_payload refactor)."""
    lr = requests.post(f"{BASE_URL}/api/auth/login", json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD}, timeout=30)
    if lr.status_code != 200:
        pytest.skip("owner login unavailable")
    token = lr.json().get("access_token") or lr.json().get("token")
    h = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/owner-portal/stores/{STORE_ID}/progress", headers=h, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert len(d.get("stages", [])) == 15
    assert len(d.get("required_actions", [])) == 6


def test_webstores_list_for_orders_picker(admin_headers):
    r = requests.get(f"{BASE_URL}/api/webstores/v2", headers=admin_headers, timeout=30)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) > 0


def test_orders_source_filter_webstore(admin_headers):
    r = requests.get(f"{BASE_URL}/api/orders?source=webstore", headers=admin_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    rows = data if isinstance(data, list) else data.get("orders") or data.get("items") or []
    # Every returned order should be source=webstore (if any rows)
    for o in rows[:20]:
        src = (o.get("source") or "").lower()
        # Some orders may not have explicit source but webstore_id implies webstore
        assert src == "webstore" or o.get("webstore_id"), f"non-webstore order leaked: {o.get('id')}"


def test_orders_webstore_id_filter(admin_headers):
    r = requests.get(f"{BASE_URL}/api/orders?webstore_id={STORE_ID}", headers=admin_headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    rows = data if isinstance(data, list) else data.get("orders") or data.get("items") or []
    for o in rows[:20]:
        assert o.get("webstore_id") == STORE_ID, f"order {o.get('id')} webstore_id={o.get('webstore_id')}"
