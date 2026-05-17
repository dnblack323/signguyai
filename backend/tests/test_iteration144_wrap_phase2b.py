"""Iteration 144 — Wrap Command Center Phase 2B backend tests.

Covers: vehicle-sync into JobTicket.specs, materials CRUD, pricing save,
formulas (material_labor_markup, per_sqft, manual), recalculate (no overwrite),
apply-price-to-order (mirror to ticket + order_total recompute),
non-wrap guard, auth, mongo _id leakage. Phase-2A regression spot checks.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
ORDER_ID = "118b7377-687b-4a28-b42b-3c5f31da64c5"
WRAP_TICKET = "aa0387f8-ac70-4935-9bbc-33d03963e916"
NON_WRAP_TICKET = "e19d6501-f80b-432b-b7b7-76e1d4903f3b"


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
    })
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="module")
def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ─── helpers ───
def _no_mongo_id(obj, path="root"):
    """Recursive _id leak check."""
    if isinstance(obj, dict):
        assert "_id" not in obj, f"_id leaked at {path}: {list(obj.keys())}"
        for k, v in obj.items():
            _no_mongo_id(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_mongo_id(v, f"{path}[{i}]")


def _reset_state(H):
    """Drop areas, materials, reset pricing config for deterministic run."""
    d = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H).json()
    for a in d.get("wrapped_areas") or []:
        requests.delete(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{a['id']}", headers=H
        )
    for m in d.get("materials") or []:
        requests.delete(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/materials/{m['id']}", headers=H
        )


# ─── auth gating ───
class TestAuthGating:
    def test_no_token_blocked_get(self):
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}")
        assert r.status_code in (401, 403)

    def test_no_token_blocked_pricing(self):
        r = requests.put(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/pricing", json={})
        assert r.status_code in (401, 403)

    def test_no_token_blocked_materials(self):
        r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/materials", json={})
        assert r.status_code in (401, 403)

    def test_no_token_blocked_apply(self):
        r = requests.post(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/apply-price-to-order")
        assert r.status_code in (401, 403)


# ─── non-wrap guard on new endpoints ───
class TestNonWrapGuard:
    def test_materials_blocked(self, H):
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{NON_WRAP_TICKET}/materials", headers=H, json={}
        )
        assert r.status_code == 400 and "not a wrap" in r.text.lower()

    def test_pricing_blocked(self, H):
        r = requests.put(
            f"{BASE_URL}/api/wrap/items/{NON_WRAP_TICKET}/pricing", headers=H, json={}
        )
        assert r.status_code == 400 and "not a wrap" in r.text.lower()

    def test_recalc_blocked(self, H):
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{NON_WRAP_TICKET}/recalculate", headers=H
        )
        assert r.status_code == 400

    def test_apply_blocked(self, H):
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{NON_WRAP_TICKET}/apply-price-to-order",
            headers=H,
        )
        assert r.status_code == 400


# ─── vehicle sync into JobTicket.specs ───
class TestVehicleSync:
    def test_vehicle_mirrors_to_ticket_specs(self, H):
        payload = {
            "year": "2023", "make": "Mercedes", "model": "Sprinter",
            "trim": "Cargo", "body_type": "High Roof", "vehicle_color": "Silver",
        }
        r = requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/vehicle", headers=H, json=payload
        )
        assert r.status_code == 200
        body = r.json()
        _no_mongo_id(body, "vehicle_response")
        assert body["vehicle_info"]["make"] == "Mercedes"

        t = requests.get(
            f"{BASE_URL}/api/job-tickets/{WRAP_TICKET}", headers=H
        ).json()
        specs = t.get("specs") or {}
        assert specs.get("vehicle_year") == "2023"
        assert specs.get("vehicle_make") == "Mercedes"
        assert specs.get("vehicle_model") == "Sprinter"
        assert specs.get("vehicle_trim") == "Cargo"
        assert specs.get("vehicle_body_type") == "High Roof"
        assert specs.get("vehicle_color") == "Silver"


# ─── Materials CRUD ───
class TestMaterials:
    def test_create_computes_total(self, H):
        _reset_state(H)
        payload = {
            "material_name": "Printed Wrap", "brand": "3M IJ180Cv3",
            "material_type": "printed_wrap_vinyl", "sqft_used": 140,
            "cost_per_sqft": 1.85, "supplier": "Grimco", "in_stock": True,
        }
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/materials", headers=H, json=payload
        )
        assert r.status_code == 200
        body = r.json()
        _no_mongo_id(body, "materials_post")
        mats = body["materials"]
        assert len(mats) == 1
        assert mats[0]["total_material_cost"] == 259.0
        pytest.shared_material_id = mats[0]["id"]

    def test_update_recomputes_total(self, H):
        mid = pytest.shared_material_id
        r = requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/materials/{mid}",
            headers=H, json={"sqft_used": 100, "cost_per_sqft": 2.5},
        )
        assert r.status_code == 200
        m = [x for x in r.json()["materials"] if x["id"] == mid][0]
        assert m["total_material_cost"] == 250.0

    def test_delete(self, H):
        mid = pytest.shared_material_id
        r = requests.delete(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/materials/{mid}", headers=H
        )
        assert r.status_code == 200
        ids = [m["id"] for m in r.json()["materials"]]
        assert mid not in ids


# ─── Formulas: build deterministic coverage + materials, then save pricing ───
class TestPricingFormulas:
    @pytest.fixture(autouse=True, scope="class")
    def seed(self, H):
        _reset_state(H)
        # 3 included areas: 60 + 60 + 30 = 150 raw? Spec says 180 raw / 207 billable.
        # 207 / 1.15 = 180 raw, 180 = 60+90+30. Use units in ft so raw = w*h.
        # Areas with 15% waste -> billable = raw * 1.15.
        # 60 + 90 + 30 = 180 raw -> 207 billable.
        for w, h, name in [(10, 6, "A"), (15, 6, "B"), (10, 3, "C")]:
            requests.post(
                f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas", headers=H,
                json={"area_name": name, "width": w, "height": h, "unit": "ft",
                      "waste_percent": 15, "included": True},
            )
        # 2 materials summing to $392: 100*1.5 + 121*2 = 150 + 242 = 392
        m1 = requests.post(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/materials", headers=H,
            json={"material_name": "M1", "sqft_used": 100, "cost_per_sqft": 1.5},
        ).json()
        m2 = requests.post(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/materials", headers=H,
            json={"material_name": "M2", "sqft_used": 121, "cost_per_sqft": 2.0},
        ).json()
        assert sum(x["total_material_cost"] for x in m2["materials"]) == 392.0
        yield

    def test_coverage_seeded(self, H):
        d = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H).json()
        cs = d["coverage_summary"]
        assert cs["total_raw_sqft"] == 180.0
        assert cs["total_billable_sqft"] == 207.0
        assert cs["included_count"] == 3

    def test_material_labor_markup(self, H):
        payload = {
            "pricing_method": "material_labor_markup",
            "price_per_sqft": 0, "design_hours": 2, "production_hours": 4,
            "install_hours": 6, "labor_rate": 75, "removal_fee": 50,
            "prep_fee": 40, "rush_fee": 0, "travel_fee": 25,
            "setup_design_fee": 150, "misc_cost": 10, "laminate_cost": 0,
            "ink_consumables_cost": 35, "markup_percent": 30,
            "manual_quoted_price": None,
        }
        r = requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/pricing", headers=H, json=payload
        )
        assert r.status_code == 200
        snap = r.json()["pricing_snapshot"]
        _no_mongo_id(snap, "snap")
        assert snap["total_labor_cost"] == 900.0
        assert snap["material_total"] == 427.0
        assert snap["base_cost"] == 1452.0
        assert snap["markup_amount"] == 435.6
        assert snap["suggested_price"] == 2037.6
        assert snap["quoted_price"] == 2037.6
        assert snap["estimated_profit"] == 585.6
        assert abs(snap["estimated_margin_percent"] - 28.74) < 0.05

    def test_per_sqft(self, H):
        payload = {
            "pricing_method": "per_sqft", "price_per_sqft": 15,
            "design_hours": 0, "production_hours": 0, "install_hours": 0,
            "labor_rate": 75, "removal_fee": 50, "prep_fee": 40,
            "rush_fee": 0, "travel_fee": 25, "setup_design_fee": 150,
            "misc_cost": 10, "laminate_cost": 0, "ink_consumables_cost": 0,
            "markup_percent": 0, "manual_quoted_price": None,
        }
        r = requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/pricing", headers=H, json=payload
        )
        snap = r.json()["pricing_snapshot"]
        # 207*15 + 150+25+40+50+10 = 3105+275 = 3380
        assert snap["per_sqft_price"] == 3380.0
        assert snap["quoted_price"] == 3380.0

    def test_manual_override(self, H):
        payload = {
            "pricing_method": "manual", "price_per_sqft": 15,
            "design_hours": 2, "production_hours": 4, "install_hours": 6,
            "labor_rate": 75, "removal_fee": 50, "prep_fee": 40,
            "rush_fee": 0, "travel_fee": 25, "setup_design_fee": 150,
            "misc_cost": 10, "laminate_cost": 0, "ink_consumables_cost": 35,
            "markup_percent": 30, "manual_quoted_price": 2500,
        }
        r = requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/pricing", headers=H, json=payload
        )
        snap = r.json()["pricing_snapshot"]
        assert snap["quoted_price"] == 2500.0
        # base_cost = 427+900+50+40+25+10 = 1452
        assert snap["base_cost"] == 1452.0
        assert snap["estimated_profit"] == round(2500 - 1452, 2)

    def test_recalculate_does_not_overwrite_config(self, H):
        # Save MLM config first
        requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/pricing", headers=H,
            json={
                "pricing_method": "material_labor_markup",
                "design_hours": 2, "production_hours": 4, "install_hours": 6,
                "labor_rate": 75, "removal_fee": 50, "prep_fee": 40,
                "rush_fee": 0, "travel_fee": 25, "setup_design_fee": 150,
                "misc_cost": 10, "laminate_cost": 0, "ink_consumables_cost": 35,
                "markup_percent": 30, "manual_quoted_price": None,
            },
        )
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/recalculate", headers=H
        )
        assert r.status_code == 200
        body = r.json()
        _no_mongo_id(body, "recalc")
        # Config unchanged
        assert body["pricing"]["markup_percent"] == 30
        assert body["pricing"]["design_hours"] == 2
        assert body["pricing_snapshot"]["quoted_price"] == 2037.6

    def test_coverage_exclude_drops_billable(self, H):
        d = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H).json()
        # Exclude area B (15x6 = 90 raw, 103.5 billable)
        target = [a for a in d["wrapped_areas"] if a["area_name"] == "B"][0]
        requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{target['id']}",
            headers=H, json={"included": False},
        )
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/recalculate", headers=H
        )
        snap = r.json()["pricing_snapshot"]
        cs = r.json()["coverage_summary"]
        assert cs["total_billable_sqft"] == 103.5  # 207 - 103.5
        # billable dropped, so per_sqft_price would drop if method=per_sqft
        # Snapshot is MLM here so unaffected by sqft. Just verify total_billable shrinks.
        assert snap["total_billable_sqft"] == 103.5
        # restore
        requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{target['id']}",
            headers=H, json={"included": True},
        )


# ─── apply-price-to-order ───
class TestApplyToOrder:
    def test_apply_writes_estimated_price_and_recomputes_total(self, H):
        # Re-save MLM=$2037.60 to make assertion deterministic
        requests.put(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/pricing", headers=H,
            json={
                "pricing_method": "material_labor_markup",
                "design_hours": 2, "production_hours": 4, "install_hours": 6,
                "labor_rate": 75, "removal_fee": 50, "prep_fee": 40,
                "rush_fee": 0, "travel_fee": 25, "setup_design_fee": 150,
                "misc_cost": 10, "laminate_cost": 0, "ink_consumables_cost": 35,
                "markup_percent": 30, "manual_quoted_price": None,
            },
        )
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/apply-price-to-order", headers=H
        )
        assert r.status_code == 200
        body = r.json()
        _no_mongo_id(body, "apply")
        assert body["applied_to_ticket"]["ticket_id"] == WRAP_TICKET
        assert body["applied_to_ticket"]["estimated_price"] == 2037.6

        t = requests.get(
            f"{BASE_URL}/api/job-tickets/{WRAP_TICKET}", headers=H
        ).json()
        assert t["estimated_price"] == 2037.6
        ps = t.get("pricing_snapshot") or {}
        assert ps.get("pricing_mode") == "wrap"
        assert ps.get("active_price") == 2037.6
        assert ps.get("source") == "wrap_command_center"

        o = requests.get(f"{BASE_URL}/api/orders/{ORDER_ID}", headers=H).json()
        # banner $250 + acrylic $50 + wrap $2037.60 = $2337.60
        assert abs(o["order_total"] - 2337.60) < 0.05, f"order_total={o['order_total']}"


# ─── Phase 2A regression: still passes ───
class TestPhase2ARegression:
    def test_get_items_works(self, H):
        r = requests.get(f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}", headers=H)
        assert r.status_code == 200
        _no_mongo_id(r.json(), "get")

    def test_area_math_unchanged(self, H):
        # add a 144x72 in area @ 10% -> raw 72, billable 79.2
        r = requests.post(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas", headers=H,
            json={"area_name": "RegA", "width": 144, "height": 72,
                  "unit": "in", "waste_percent": 10},
        )
        new_areas = r.json()["wrapped_areas"]
        added = [a for a in new_areas if a["area_name"] == "RegA"][0]
        assert added["raw_sqft"] == 72.0
        assert added["billable_sqft"] == 79.2
        requests.delete(
            f"{BASE_URL}/api/wrap/items/{WRAP_TICKET}/areas/{added['id']}", headers=H
        )
