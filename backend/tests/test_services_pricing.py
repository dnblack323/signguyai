"""
Services pricing category tests (category='services').
Covers:
 - POST /api/pricing/calculate: service types, billing units, labor roles,
   complexity multipliers, travel, trip charge, equipment, subcontract,
   permit, minimums (+override/off), rush, manual override, multi-worker,
   sell_method variants, unknown-service fallback warnings.
 - GET /api/job-tickets/schema/services (Foundation-driven fields)
 - GET /api/pricing/defaults (services category_defaults block)
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


def _base(overrides=None, quantity=1):
    pd = {
        "service_type": "general_labor",
        "services_billing_unit": "hour",
        "services_labor_role": "production",
        "services_complexity": "medium",
        "estimated_hours": 1.0,
        "num_workers": 1,
        "services_minimum_applies": True,
        "services_travel_required": False,
        "services_travel_miles": 0,
        "services_trip_charge_applies": False,
        "services_trip_count": 1,
        "services_equipment_required": False,
        "services_equipment_days": 0,
        "services_equipment_hours": 0,
        "services_subcontracted": False,
        "services_subcontract_cost": 0,
        "services_subcontract_markup_applies": True,
        "services_permit_external_fee": 0,
        "services_manual_quote_override": 0,
        "services_minimum_override": 0,
        "services_flat_fee": None,
        "services_unit_rate_override": None,
        "rush_order": False,
    }
    if overrides:
        pd.update(overrides)
    return {"category": "services", "pricing_data": pd, "quantity": quantity}


def calc(headers, overrides=None, quantity=1):
    r = requests.post(f"{API}/pricing/calculate", json=_base(overrides, quantity), headers=headers, timeout=30)
    assert r.status_code == 200, f"calc failed {r.status_code}: {r.text[:300]}"
    return r.json()


def br(resp):
    return resp.get("breakdown", resp)


# -------------- Breakdown fields --------------
class TestBreakdownFields:
    def test_full_breakdown_keys(self, headers):
        d = br(calc(headers))
        required = [
            "service_type", "billing_unit", "labor_role", "complexity",
            "complexity_multiplier", "labor_cost", "labor_sell_baseline",
            "cost_plus_labor_sell", "travel_cost", "travel_sell",
            "equipment_cost", "equipment_sell", "subcontract_cost",
            "subcontract_sell", "permit_cost", "permit_sell",
            "effective_min", "minimum_applied", "sell_method",
        ]
        for k in required:
            assert k in d, f"missing {k}; keys={list(d.keys())}"


# -------------- Service type / billing unit --------------
class TestServiceTypeSwitch:
    def test_general_labor_to_installation(self, headers):
        r1 = br(calc(headers, {"service_type": "general_labor"}))
        r2 = br(calc(headers, {"service_type": "installation", "services_labor_role": None}))
        assert r1["service_type"] == "general_labor"
        assert r2["service_type"] == "installation"
        assert r2["labor_role"] == "installer"
        # installation minimum is 125
        assert r2["effective_min"] == 125.0
        # general_labor minimum 25
        assert r1["effective_min"] == 25.0

    def test_billing_unit_flat_uses_default_flat_fee(self, headers):
        d = br(calc(headers, {
            "service_type": "site_survey",
            "services_billing_unit": "flat",
            "services_labor_role": None,
        }))
        assert d["billing_unit"] == "flat"
        # site_survey default_flat_fee=125 (from defaults)
        assert d.get("flat_fee") == 125.0

    def test_billing_mile_applies_travel(self, headers):
        d = br(calc(headers, {
            "service_type": "delivery",
            "services_billing_unit": "mile",
            "services_labor_role": None,
            "services_travel_required": True,
            "services_travel_miles": 40,
            "estimated_hours": 0,
        }))
        assert d["billing_unit"] == "mile"
        # travel rates: cost 0.65, sell 1.25 per mile; but when billing=mile, travel fields may be
        # rolled into cost_plus. Make sure suggested_price > 0.
        resp = calc(headers, {
            "service_type": "delivery",
            "services_billing_unit": "mile",
            "services_labor_role": None,
            "services_travel_required": True,
            "services_travel_miles": 40,
            "estimated_hours": 0,
        })
        assert resp.get("suggested_price", 0) > 0

    def test_billing_trip_multiplies_trip_count(self, headers):
        d1 = br(calc(headers, {
            "service_type": "delivery", "services_billing_unit": "trip",
            "services_labor_role": None, "services_trip_count": 1,
            "estimated_hours": 0.5,
        }))
        d2 = br(calc(headers, {
            "service_type": "delivery", "services_billing_unit": "trip",
            "services_labor_role": None, "services_trip_count": 2,
            "estimated_hours": 0.5,
        }))
        # trip 2 baseline sell should be higher than trip 1
        assert d2["labor_sell_baseline"] > d1["labor_sell_baseline"]

    def test_billing_day_applies_daily(self, headers):
        resp = calc(headers, {
            "service_type": "equipment_rental",
            "services_billing_unit": "day",
            "services_equipment_required": True,
            "services_equipment_type": "scissor_lift",
            "services_equipment_days": 2,
            "services_labor_role": None,
            "estimated_hours": 0,
        })
        d = br(resp)
        assert d["billing_unit"] == "day"
        # scissor_lift 2 days: cost=$450, sell=$650
        assert abs(d["equipment_cost"] - 450.0) < 0.5
        assert abs(d["equipment_sell"] - 650.0) < 0.5


# -------------- Labor role + complexity --------------
class TestLaborAndComplexity:
    def test_labor_role_updates_rates(self, headers):
        d_prod = br(calc(headers, {"services_labor_role": "production"}))
        d_inst = br(calc(headers, {"services_labor_role": "installer"}))
        d_lead = br(calc(headers, {"services_labor_role": "lead_installer"}))
        assert d_lead["labor_cost_rate"] > d_inst["labor_cost_rate"] > d_prod["labor_cost_rate"]
        assert d_lead["labor_sell_rate"] > d_prod["labor_sell_rate"]

    def test_complexity_multipliers(self, headers):
        easy = br(calc(headers, {"services_complexity": "easy"}))
        med = br(calc(headers, {"services_complexity": "medium"}))
        diff = br(calc(headers, {"services_complexity": "difficult"}))
        ext = br(calc(headers, {"services_complexity": "extreme"}))
        assert easy["complexity_multiplier"] == 1.0
        assert med["complexity_multiplier"] == 1.25
        assert diff["complexity_multiplier"] == 1.5
        assert ext["complexity_multiplier"] == 2.0
        # labor_cost scales with multiplier
        assert ext["labor_cost"] > diff["labor_cost"] > med["labor_cost"] > easy["labor_cost"]


# -------------- Travel + trips --------------
class TestTravelTrips:
    def test_travel_cost_and_sell_per_mile(self, headers):
        d = br(calc(headers, {
            "service_type": "installation",
            "services_labor_role": None,
            "estimated_hours": 3,
            "services_travel_required": True,
            "services_travel_miles": 25,
            "services_trip_charge_applies": True,
            "services_trip_count": 1,
        }))
        # 25mi * $0.65 = $16.25 cost; $1.25 sell + $45 trip = $76.25 sell
        assert abs(d["travel_cost"] - 16.25) < 0.5
        assert abs(d["travel_sell"] - 76.25) < 0.5

    def test_trip_charge_only(self, headers):
        d0 = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 2, "services_travel_required": False,
            "services_trip_charge_applies": False,
        }))
        d1 = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 2, "services_travel_required": True,
            "services_trip_charge_applies": True, "services_trip_count": 2,
        }))
        assert d1["travel_sell"] > d0["travel_sell"]


# -------------- Equipment --------------
class TestEquipment:
    def test_equipment_days_scissor_lift(self, headers):
        d = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 4, "services_equipment_required": True,
            "services_equipment_type": "scissor_lift", "services_equipment_days": 2,
        }))
        assert abs(d["equipment_cost"] - 450.0) < 0.5
        assert abs(d["equipment_sell"] - 650.0) < 0.5

    def test_equipment_boom_lift_1_day(self, headers):
        d = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 4, "services_equipment_required": True,
            "services_equipment_type": "boom_lift", "services_equipment_days": 1,
        }))
        assert abs(d["equipment_cost"] - 325.0) < 0.5
        assert abs(d["equipment_sell"] - 475.0) < 0.5

    def test_equipment_hours_path(self, headers):
        d = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 4, "services_equipment_required": True,
            "services_equipment_type": "scissor_lift", "services_equipment_days": 0,
            "services_equipment_hours": 4,
        }))
        # scissor_lift 4h: cost 4*35=140, sell 4*55=220
        assert abs(d["equipment_cost"] - 140.0) < 1.0
        assert abs(d["equipment_sell"] - 220.0) < 1.0


# -------------- Subcontract + permit --------------
class TestSubcontractPermit:
    def test_subcontract_with_markup(self, headers):
        resp = calc(headers, {
            "service_type": "subcontracted", "services_labor_role": None,
            "services_billing_unit": "flat",
            "services_subcontracted": True, "services_subcontract_cost": 500,
            "services_subcontract_markup_applies": True,
            "estimated_hours": 0,
        })
        d = br(resp)
        assert d["subcontracted"] is True
        assert d["subcontract_cost"] == 500.0
        # 500 * 1.20 = 600
        assert abs(d["subcontract_sell"] - 600.0) < 0.5
        assert d["sell_method"] == "pass_through_plus_markup"

    def test_subcontract_no_markup(self, headers):
        d = br(calc(headers, {
            "service_type": "subcontracted", "services_labor_role": None,
            "services_billing_unit": "flat",
            "services_subcontracted": True, "services_subcontract_cost": 500,
            "services_subcontract_markup_applies": False,
            "estimated_hours": 0,
        }))
        assert abs(d["subcontract_sell"] - 500.0) < 0.5

    def test_permit_pass_through(self, headers):
        d = br(calc(headers, {
            "service_type": "permit_handling", "services_labor_role": None,
            "services_billing_unit": "flat",
            "services_permit_external_fee": 300,
            "estimated_hours": 0,
        }))
        assert d["permit_cost"] == 300.0
        assert d["permit_sell"] == 300.0


# -------------- Minimum floor --------------
class TestMinimums:
    def test_minimum_applies_install(self, headers):
        # 0.5hr install → under $125 min, should floor at 125 suggested price
        resp = calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 0.5, "services_minimum_applies": True,
        })
        assert resp["suggested_price"] >= 125.0
        assert br(resp)["effective_min"] == 125.0

    def test_minimum_override(self, headers):
        d = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 0.5, "services_minimum_applies": True,
            "services_minimum_override": 200,
        }))
        assert d["effective_min"] == 200.0

    def test_minimum_off(self, headers):
        resp = calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 0.5, "services_minimum_applies": False,
        })
        # No 125 floor
        assert resp["suggested_price"] < 125.0
        assert br(resp)["minimum_applied"] is False


# -------------- Rush + manual override --------------
class TestRushAndOverride:
    def test_rush_25_percent(self, headers):
        base_r = calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 2, "rush_order": False,
        })
        rush_r = calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 2, "rush_order": True,
        })
        # $237.50 base × 1.25 = $296.88
        assert abs(rush_r["suggested_price"] - 296.88) < 0.5
        assert rush_r["suggested_price"] > base_r["suggested_price"]

    def test_manual_override(self, headers):
        resp = calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 2,
            "services_manual_quote_override": 500,
        })
        assert abs(resp["suggested_price"] - 500.0) < 0.5

    def test_unit_rate_override(self, headers):
        d1 = br(calc(headers, {
            "service_type": "specialty_custom", "services_labor_role": "specialty_technician",
            "estimated_hours": 3,
        }))
        d2 = br(calc(headers, {
            "service_type": "specialty_custom", "services_labor_role": "specialty_technician",
            "estimated_hours": 3, "services_unit_rate_override": 150,
        }))
        assert d2["unit_rate"] == 150.0
        assert d2["labor_sell_baseline"] > d1["labor_sell_baseline"]


# -------------- Fallback + multi-worker + sell methods --------------
class TestEdgeCases:
    def test_unknown_service_fallback(self, headers):
        # 'travel' is valid in ServiceType enum but not in the 19-type pricing library → fallback
        d = br(calc(headers, {"service_type": "travel"}))
        warns = d.get("warnings") or []
        assert any("fallback" in str(w).lower() or "not found" in str(w).lower() for w in warns), f"warnings={warns}"
        # Falls back to general_labor
        assert d["service_type"] == "general_labor"

    def test_multi_worker(self, headers):
        d1 = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 3, "num_workers": 1,
        }))
        d2 = br(calc(headers, {
            "service_type": "installation", "services_labor_role": None,
            "estimated_hours": 3, "num_workers": 2,
        }))
        # 2 workers should double labor_cost and baseline
        assert abs(d2["labor_cost"] - d1["labor_cost"] * 2) < 1.0
        assert abs(d2["labor_sell_baseline"] - d1["labor_sell_baseline"] * 2) < 1.0

    def test_sell_method_cost_plus_equipment_rental(self, headers):
        d = br(calc(headers, {
            "service_type": "equipment_rental", "services_labor_role": None,
            "services_billing_unit": "day",
            "services_equipment_required": True, "services_equipment_type": "scissor_lift",
            "services_equipment_days": 2, "estimated_hours": 0,
        }))
        assert d["sell_method"] == "cost_plus"

    def test_sell_method_pass_through_subcontracted(self, headers):
        d = br(calc(headers, {
            "service_type": "subcontracted", "services_labor_role": None,
            "services_billing_unit": "flat",
            "services_subcontracted": True, "services_subcontract_cost": 500,
        }))
        assert d["sell_method"] == "pass_through_plus_markup"

    def test_sell_method_max_of_both_default(self, headers):
        d = br(calc(headers, {"service_type": "installation", "services_labor_role": None}))
        assert d["sell_method"] == "max_of_both"


# -------------- Schema + defaults --------------
class TestSchemaAndDefaults:
    def test_schema_services(self, headers):
        r = requests.get(f"{API}/job-tickets/schema/services", headers=headers, timeout=30)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        fields = data.get("fields") or data.get("schema") or data
        # Must contain services_* keys
        if isinstance(fields, list):
            keys = [f.get("key") or f.get("name") for f in fields]
        elif isinstance(fields, dict):
            keys = list(fields.keys())
        else:
            keys = []
        svc_keys = [k for k in keys if k and "service" in k.lower()]
        assert len(svc_keys) >= 10, f"expected many services_* schema fields, got {svc_keys}"

    def test_pricing_defaults_services_block(self, headers):
        r = requests.get(f"{API}/pricing/defaults", headers=headers, timeout=30)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        cd = data.get("category_defaults") or data.get("categoryDefaults") or {}
        svc = cd.get("services") if isinstance(cd, dict) else None
        assert svc, f"services block missing; keys={list(cd.keys()) if isinstance(cd, dict) else type(cd)}"
        for key in ["available_service_types", "available_billing_units", "labor_roles",
                    "complexity_multipliers", "travel_cost_per_mile", "travel_sell_rate_per_mile",
                    "equipment_library", "subcontract_markup_percent", "rush_percent", "default_sell_method"]:
            assert key in svc, f"missing {key} in services defaults"
        # 19 service types
        assert len(svc["available_service_types"]) == 19
        # 9 billing units
        assert len(svc["available_billing_units"]) == 9
        # 9 labor roles
        assert len(svc["labor_roles"]) == 9
        # travel rates
        assert svc["travel_cost_per_mile"] == 0.65
        assert svc["travel_sell_rate_per_mile"] == 1.25
