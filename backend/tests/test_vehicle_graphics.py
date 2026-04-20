"""
Vehicle Graphics / Wraps pricing tests.
Covers:
 - POST /api/pricing/calculate (category=vehicle_graphics) breakdown fields
 - Vehicle type, coverage type, custom coverage, materials, laminate, window perf,
   design complexity, surface prep, removal, install, install difficulty, seam complexity,
   second installer, rush, quantity
 - GET /api/job-tickets/schema/vehicle_wrap
 - GET /api/pricing/defaults (vehicle_wraps block)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000").rstrip("/")
API = f"{BASE_URL}/api"

EMAIL = "signguypa@gmail.com"
PASSWORD = "Billnel323"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Login failed {r.status_code}: {r.text[:200]}")
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="session")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def baseline_payload():
    # SUV, full coverage, premium cast w/ gloss laminate - a common baseline
    return {
        "category": "vehicle_graphics",
        "pricing_data": {
            "vehicle_type": "car_suv",
            "coverage_type": "full",
            "wrap_material_key": "wrap_premium_cast",
            "wrap_laminate_required": True,
            "wrap_laminate_type_key": "wrap_laminate_gloss",
            "window_perf_included": False,
            "artwork_ready": False,
            "design_complexity": "medium",
            "surface_prep_level": "none",
            "removal_scope": "none",
            "install_required": True,
            "install_difficulty_level": "medium",
            "seam_complexity": "basic",
            "second_installer_required": False,
            "rush_order": False,
            "quantity": 1,
        },
    }


def calc(headers, overrides=None, quantity=1):
    payload = baseline_payload()
    payload["quantity"] = quantity
    if overrides:
        # allow overrides to set root quantity too
        if "quantity" in overrides:
            payload["quantity"] = overrides.pop("quantity")
        payload["pricing_data"].update(overrides)
    r = requests.post(f"{API}/pricing/calculate", json=payload, headers=headers, timeout=30)
    assert r.status_code == 200, f"{r.status_code}: {r.text[:300]}"
    return r.json()


# ---------- Schema + defaults ----------

def test_defaults_has_vehicle_wraps(headers):
    r = requests.get(f"{API}/pricing/defaults", headers=headers, timeout=30)
    assert r.status_code == 200
    data = r.json()
    # defaults can be nested under category_defaults or direct
    vw = (
        data.get("vehicle_wraps")
        or data.get("category_defaults", {}).get("vehicle_wraps")
        or data.get("defaults", {}).get("vehicle_wraps")
    )
    assert vw is not None, f"vehicle_wraps block missing. Keys={list(data.keys())[:10]}"
    expected = [
        "install_hours_by_vehicle_coverage",
        "package_pricing_by_vehicle_coverage",
        "install_difficulty_multipliers",
        "seam_complexity_multipliers",
        "surface_prep_hours",
        "removal_hours",
        "window_perf_sell_rate_rear_per_sqft",
    ]
    missing = [k for k in expected if k not in vw]
    assert not missing, f"Missing defaults keys: {missing}"


def test_schema_vehicle_wrap(headers):
    r = requests.get(f"{API}/job-tickets/schema/vehicle_wrap", headers=headers, timeout=30)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    fields = data.get("fields") or data.get("schema") or data
    if isinstance(fields, dict):
        field_names = list(fields.keys())
    else:
        field_names = [f.get("name") or f.get("key") for f in fields]
    required_keys = [
        "wrap_material_key",
        "wrap_laminate_required",
        "window_perf_included",
        "surface_prep_level",
        "removal_scope",
        "install_difficulty_level",
        "seam_complexity",
        "second_installer_required",
    ]
    missing = [k for k in required_keys if k not in field_names]
    assert not missing, f"Missing schema fields: {missing}. Got {field_names[:40]}"
    assert len(field_names) >= 20, f"Expected 20+ fields, got {len(field_names)}"


# ---------- Calculation tests ----------

REQUIRED_FIELDS = [
    "vinyl_material_cost",
    "laminate_material_cost",
    "window_perf_sell",
    "install_labor_cost",
    "helper_cost",
    "package_price_total",
    "cost_plus_price",
]


def _get_breakdown(res):
    return res.get("breakdown") or res.get("details") or res


def test_baseline_has_all_fields(headers):
    res = calc(headers)
    bd = _get_breakdown(res)
    missing = [f for f in REQUIRED_FIELDS if f not in bd]
    assert not missing, f"Missing breakdown fields: {missing}. Keys: {list(bd.keys())[:20]}"
    assert bd["vinyl_material_cost"] > 0
    assert bd["install_labor_cost"] > 0


def test_vehicle_type_change(headers):
    suv = _get_breakdown(calc(headers, {"vehicle_type": "car_sedan"}))
    box = _get_breakdown(calc(headers, {"vehicle_type": "box_truck_24ft"}))
    assert box["install_hours"] > suv["install_hours"]
    assert box["package_price_total"] > suv["package_price_total"]


def test_coverage_spot_vs_full(headers):
    spot = _get_breakdown(calc(headers, {"coverage_type": "spot"}))
    full = _get_breakdown(calc(headers, {"coverage_type": "full"}))
    assert full["install_hours"] > spot["install_hours"]
    assert full["package_price_total"] > spot["package_price_total"]


def test_custom_coverage(headers):
    bd = _get_breakdown(calc(headers, {"coverage_type": "custom", "custom_coverage_percent": 65}))
    full = _get_breakdown(calc(headers, {"coverage_type": "full"}))
    spot = _get_breakdown(calc(headers, {"coverage_type": "spot"}))
    # custom 65% should be between spot and full
    assert spot["install_hours"] < bd["install_hours"] < full["install_hours"]


def test_material_calendared_vs_cast(headers):
    cal = _get_breakdown(calc(headers, {"wrap_material_key": "wrap_standard_calendared"}))
    cast = _get_breakdown(calc(headers, {"wrap_material_key": "wrap_cast_film"}))
    assert cast["vinyl_material_cost"] > cal["vinyl_material_cost"]


def test_laminate_toggle(headers):
    on = _get_breakdown(calc(headers, {"wrap_laminate_required": True}))
    off = _get_breakdown(calc(headers, {"wrap_laminate_required": False}))
    assert on["laminate_material_cost"] > 0
    assert off["laminate_material_cost"] == 0


def test_laminate_type_gloss_vs_satin(headers):
    gloss = _get_breakdown(calc(headers, {"wrap_laminate_type_key": "wrap_laminate_gloss"}))
    satin = _get_breakdown(calc(headers, {"wrap_laminate_type_key": "wrap_laminate_satin"}))
    assert gloss["laminate_material_cost"] != satin["laminate_material_cost"]


def test_window_perf_rear(headers):
    bd = _get_breakdown(calc(headers, {"window_perf_included": True, "window_perf_scope": "rear"}))
    assert bd["window_perf_sell"] > 300  # ~$324


def test_window_perf_side(headers):
    bd = _get_breakdown(calc(headers, {"window_perf_included": True, "window_perf_scope": "side"}))
    assert 250 < bd["window_perf_sell"] < 320  # ~$280


def test_design_complexity(headers):
    simple = _get_breakdown(calc(headers, {"design_complexity": "simple"}))
    extreme = _get_breakdown(calc(headers, {"design_complexity": "extreme"}))
    assert extreme["design_hours"] > simple["design_hours"]


def test_surface_prep(headers):
    none = _get_breakdown(calc(headers, {"surface_prep_level": "none"}))
    heavy = _get_breakdown(calc(headers, {"surface_prep_level": "heavy"}))
    assert heavy["surface_prep_hours"] > none["surface_prep_hours"]


def test_removal_scope(headers):
    none = _get_breakdown(calc(headers, {"removal_scope": "none"}))
    full = _get_breakdown(calc(headers, {"removal_scope": "full"}))
    assert full["removal_hours"] > 0
    assert none["removal_hours"] == 0


def test_install_off(headers):
    bd = _get_breakdown(calc(headers, {"install_required": False}))
    assert bd["install_labor_cost"] == 0


def test_install_difficulty(headers):
    easy = _get_breakdown(calc(headers, {"install_difficulty_level": "easy"}))
    extreme = _get_breakdown(calc(headers, {"install_difficulty_level": "extreme"}))
    assert extreme["install_hours"] > easy["install_hours"]


def test_seam_complexity(headers):
    basic = _get_breakdown(calc(headers, {"seam_complexity": "basic"}))
    advanced = _get_breakdown(calc(headers, {"seam_complexity": "advanced"}))
    assert advanced["install_hours"] > basic["install_hours"]


def test_second_installer(headers):
    off = _get_breakdown(calc(headers, {"second_installer_required": False}))
    on = _get_breakdown(calc(headers, {"second_installer_required": True}))
    assert off["helper_cost"] == 0
    assert on["helper_cost"] > 0
    # helper_cost ~= install_hours * 35
    assert abs(on["helper_cost"] - on["install_hours"] * 35) < 1.0


def test_rush_order(headers):
    normal = calc(headers, {"rush_order": False})
    rush = calc(headers, {"rush_order": True})
    n = normal.get("suggested_price") or normal.get("selling_price")
    r = rush.get("suggested_price") or rush.get("selling_price")
    assert r > n * 1.15, f"Rush should increase price notably: normal={n} rush={r}"


def test_quantity_scaling(headers):
    q1 = calc(headers, {"quantity": 1})
    q3 = calc(headers, {"quantity": 3})
    m1 = q1.get("material_cost") or q1.get("total_material_cost")
    m3 = q3.get("material_cost") or q3.get("total_material_cost")
    assert m3 > m1 * 2.5, f"Material should scale with qty: q1={m1} q3={m3}"
