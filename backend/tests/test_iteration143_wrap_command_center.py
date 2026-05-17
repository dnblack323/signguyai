"""Iteration 143 — Wrap Command Center Phase 2A backend CRUD tests.

Covers /api/wrap/items/{ticket_id} endpoints:
- GET (auto-create + shape)
- Non-wrap 400, nonexistent 404, no-auth 401/403
- PUT vehicle (persistence)
- POST/PUT/DELETE areas (math + coverage summary)
- _id stripping
"""
import os
import pytest
import requests

def _read_frontend_env():
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _read_frontend_env() or "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASS = "password123"
WRAP_TICKET = "aa0387f8-ac70-4935-9bbc-33d03963e916"
NON_WRAP_TICKET = "e19d6501-f80b-432b-b7b7-76e1d4903f3b"
ORDER_ID = "118b7377-687b-4a28-b42b-3c5f31da64c5"


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code != 200:
        return None
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def admin_token():
    tok = _login(ADMIN_EMAIL, ADMIN_PASS)
    if not tok:
        pytest.skip("Admin login failed")
    return tok


@pytest.fixture(scope="module")
def hdr(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module", autouse=True)
def reset_wrap_data(hdr):
    """Best-effort cleanup: delete any existing areas before suite so math is deterministic."""
    try:
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        if r.status_code == 200:
            for a in r.json().get("wrapped_areas", []):
                requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{a['id']}", headers=hdr, timeout=30)
    except Exception:
        pass
    yield
    # post cleanup
    try:
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        if r.status_code == 200:
            for a in r.json().get("wrapped_areas", []):
                requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{a['id']}", headers=hdr, timeout=30)
    except Exception:
        pass


def _assert_no_mongo_id(obj, path="root"):
    if isinstance(obj, dict):
        assert "_id" not in obj, f"_id found at {path}"
        for k, v in obj.items():
            _assert_no_mongo_id(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_no_mongo_id(v, f"{path}[{i}]")


# ───── GET / shape ─────
class TestGetWrap:
    def test_get_wrap_auto_creates_and_shape(self, hdr):
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("id", "tenant_id", "ticket_id", "order_id", "vehicle_info", "wrapped_areas", "coverage_summary"):
            assert k in d, f"missing key {k}"
        assert d["ticket_id"] == WRAP_TICKET
        # 17 vehicle_info fields
        vi = d["vehicle_info"]
        expected_vi_keys = {
            "year", "make", "model", "trim", "body_type", "roof_height", "wheelbase",
            "vehicle_color", "license_plate", "vin", "existing_graphics", "existing_wrap",
            "paint_condition", "body_condition", "vehicle_notes", "template_type",
            "customer_photo_placeholders",
        }
        assert expected_vi_keys.issubset(set(vi.keys()))
        cs = d["coverage_summary"]
        for k in ("total_raw_sqft", "total_billable_sqft", "average_waste_percent", "included_count", "excluded_count"):
            assert k in cs
        _assert_no_mongo_id(d)

    def test_get_returns_same_id_on_second_call(self, hdr):
        r1 = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        r2 = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json()["id"] == r2.json()["id"]

    def test_get_non_wrap_returns_400(self, hdr):
        r = requests.get(f"{BASE_URL}/api/wrap/items/{NON_WRAP_TICKET}", headers=hdr, timeout=30)
        assert r.status_code == 400
        assert "not a wrap category" in r.json().get("detail", "").lower()

    def test_get_nonexistent_returns_404(self, hdr):
        r = requests.get(f"{BASE_URL}/api/wrap/items/does-not-exist-xyz", headers=hdr, timeout=30)
        assert r.status_code == 404

    def test_get_without_auth(self):
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", timeout=30)
        assert r.status_code in (401, 403)


# ───── Vehicle Info PUT ─────
class TestVehicleInfo:
    def test_update_vehicle(self, hdr):
        payload = {
            "year": "2024", "make": "Chevy", "model": "Express",
            "body_type": "Cargo Van", "vehicle_color": "Black",
            "existing_graphics": True, "vehicle_notes": "Test",
        }
        r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/vehicle", json=payload, headers=hdr, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        vi = d["vehicle_info"]
        assert vi["year"] == "2024"
        assert vi["make"] == "Chevy"
        assert vi["model"] == "Express"
        assert vi["body_type"] == "Cargo Van"
        assert vi["vehicle_color"] == "Black"
        assert vi["existing_graphics"] is True
        assert vi["vehicle_notes"] == "Test"
        _assert_no_mongo_id(d)
        # persistence
        r2 = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        assert r2.json()["vehicle_info"]["make"] == "Chevy"


# ───── Areas CRUD + math ─────
class TestAreasMath:
    def test_post_area_in_unit_math(self, hdr):
        payload = {
            "area_name": "Test Side", "width": 120, "height": 72, "unit": "in",
            "waste_percent": 15, "material": "3M IJ180Cv3", "complexity": "medium", "included": True,
        }
        r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas", json=payload, headers=hdr, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        areas = d["wrapped_areas"]
        assert len(areas) >= 1
        new_area = next(a for a in areas if a["area_name"] == "Test Side")
        assert new_area["raw_sqft"] == 60
        assert new_area["billable_sqft"] == 69
        _assert_no_mongo_id(d)

    def test_post_area_ft_unit_math(self, hdr):
        payload = {"area_name": "FT Area", "width": 10, "height": 5, "unit": "ft", "waste_percent": 0, "included": True}
        r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas", json=payload, headers=hdr, timeout=30)
        assert r.status_code == 200
        new_area = next(a for a in r.json()["wrapped_areas"] if a["area_name"] == "FT Area")
        assert new_area["raw_sqft"] == 50
        assert new_area["billable_sqft"] == 50
        # cleanup
        requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{new_area['id']}", headers=hdr, timeout=30)

    def test_post_area_missing_dims(self, hdr):
        payload = {"area_name": "No Dims", "included": True}
        r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas", json=payload, headers=hdr, timeout=30)
        assert r.status_code == 200
        new_area = next(a for a in r.json()["wrapped_areas"] if a["area_name"] == "No Dims")
        assert new_area["raw_sqft"] is None
        assert new_area["billable_sqft"] is None
        # cleanup
        requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{new_area['id']}", headers=hdr, timeout=30)

    def test_put_area_recomputes(self, hdr):
        # ensure clean state - find or create
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        target = next((a for a in r.json()["wrapped_areas"] if a["area_name"] == "Test Side"), None)
        assert target is not None, "expected Test Side from prior test"
        upd = {"width": 144, "waste_percent": 10}
        r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{target['id']}", json=upd, headers=hdr, timeout=30)
        assert r2.status_code == 200, r2.text
        a = next(x for x in r2.json()["wrapped_areas"] if x["id"] == target["id"])
        # 144*72/144 = 72 raw; 72*1.10 = 79.2 billable
        assert a["raw_sqft"] == 72.0
        assert a["billable_sqft"] == 79.2

    def test_put_area_included_false_excludes(self, hdr):
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        target = next((a for a in r.json()["wrapped_areas"] if a["area_name"] == "Test Side"), None)
        assert target is not None
        before_included = r.json()["coverage_summary"]["included_count"]
        r2 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{target['id']}", json={"included": False}, headers=hdr, timeout=30)
        assert r2.status_code == 200
        cs = r2.json()["coverage_summary"]
        assert cs["excluded_count"] >= 1
        assert cs["included_count"] == before_included - 1
        # revert for further tests
        requests.put(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{target['id']}", json={"included": True, "width": 120, "waste_percent": 15}, headers=hdr, timeout=30)

    def test_coverage_summary_math(self, hdr):
        # Reset all areas first
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        for a in r.json()["wrapped_areas"]:
            requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{a['id']}", headers=hdr, timeout=30)
        # Area 1: 120x72in, 15% waste -> raw 60, billable 69
        requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas", json={
            "area_name": "A1", "width": 120, "height": 72, "unit": "in", "waste_percent": 15, "included": True
        }, headers=hdr, timeout=30)
        # Area 2: 60x72in, 20% waste -> raw 30, billable 36
        r2 = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas", json={
            "area_name": "A2", "width": 60, "height": 72, "unit": "in", "waste_percent": 20, "included": True
        }, headers=hdr, timeout=30)
        cs = r2.json()["coverage_summary"]
        assert cs["total_raw_sqft"] == 90.0
        assert cs["total_billable_sqft"] == 105.0
        assert cs["included_count"] == 2
        assert cs["excluded_count"] == 0
        assert abs(cs["average_waste_percent"] - 17.5) < 0.01

        # exclude A2
        a2 = next(x for x in r2.json()["wrapped_areas"] if x["area_name"] == "A2")
        r3 = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{a2['id']}", json={"included": False}, headers=hdr, timeout=30)
        cs3 = r3.json()["coverage_summary"]
        assert cs3["total_raw_sqft"] == 60.0
        assert cs3["total_billable_sqft"] == 69.0
        assert cs3["included_count"] == 1
        assert cs3["excluded_count"] == 1

    def test_delete_area(self, hdr):
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=hdr, timeout=30)
        target = r.json()["wrapped_areas"][0]
        r2 = requests.delete(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{target['id']}", headers=hdr, timeout=30)
        assert r2.status_code == 200
        ids = [a["id"] for a in r2.json()["wrapped_areas"]]
        assert target["id"] not in ids
        _assert_no_mongo_id(r2.json())


# ───── Tenant isolation ─────
class TestTenantIsolation:
    def test_other_tenant_isolation(self):
        # signguypa is same tenant per credentials file (signguy_ai), so we cannot
        # do a true cross-tenant test. Document and skip.
        pytest.skip("No second-tenant account available; signguypa is same tenant per /app/memory/test_credentials.md")
