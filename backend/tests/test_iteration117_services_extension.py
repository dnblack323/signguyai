"""
Iteration 117 — Services Pricing Foundation extension validation.

Covers:
- POST /api/ai/services-prefill: realistic prompt, no-overwrite-of-user-set, 422 on short.
- POST /api/pricing/calculate category=services:
    * rush_percent_source = services_category when foundation.default_rush_percent=0
    * rush_percent_source = foundation when foundation.default_rush_percent=17.5
    * breakdown.total_* totals mirror the underlying cost fields
    * field_sources tags ai_estimated / user_entered / shop_default correctly
- Full scenario (installation + travel + lift + rush) yields price>1000, profit>0, margin>30%.
- Minimum charge enforcement (tiny consultation hits per-service minimum $50).

Restores foundation.default_rush_percent to its original value after the rush-source tests.
AI calls are kept to <=3.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

EMAIL = "signguypa@gmail.com"
PASSWORD = "Billnel323"


# ---------- fixtures ----------
@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Login failed {r.status_code}: {r.text[:200]}")
    body = r.json()
    return body.get("access_token") or body.get("token")


@pytest.fixture(scope="session")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def original_rush_pct(headers):
    """Snapshot the tenant's current default_rush_percent so we can restore after the suite."""
    r = requests.get(f"{API}/pricing/defaults", headers=headers, timeout=30)
    assert r.status_code == 200, r.text[:200]
    return r.json().get("default_rush_percent", 0) or 0


def _set_rush_pct(headers, value):
    r = requests.put(
        f"{API}/pricing/defaults",
        json={"default_rush_percent": value},
        headers=headers,
        timeout=30,
    )
    assert r.status_code == 200, f"PUT defaults failed: {r.status_code} {r.text[:200]}"
    return r.json()


@pytest.fixture(scope="session", autouse=True)
def _restore_rush_pct(original_rush_pct, headers):
    yield
    # Teardown: restore the tenant's original default_rush_percent
    _set_rush_pct(headers, original_rush_pct)


def _calc(headers, pd, quantity=1):
    payload = {"category": "services", "pricing_data": pd, "quantity": quantity}
    r = requests.post(f"{API}/pricing/calculate", json=payload, headers=headers, timeout=30)
    assert r.status_code == 200, f"calc failed {r.status_code}: {r.text[:400]}"
    return r.json()


# =========================================================
# AI PREFILL
# =========================================================
class TestAIPrefill:
    def test_short_description_rejected_422(self, headers):
        r = requests.post(
            f"{API}/ai/services-prefill",
            json={"description": "hi", "existing_inputs": {}},
            headers=headers,
            timeout=30,
        )
        assert r.status_code == 422, f"expected 422 for short desc, got {r.status_code} {r.text[:200]}"

    def test_realistic_prompt_returns_expected_fields(self, headers):
        body = {
            "description": "Install 4 aluminum signs 15 miles away, needs a scissor lift",
            "existing_inputs": {},
        }
        r = requests.post(f"{API}/ai/services-prefill", json=body, headers=headers, timeout=120)
        if r.status_code == 402:
            pytest.skip("Insufficient AI credits — non-blocking")
        assert r.status_code == 200, f"AI prefill failed {r.status_code}: {r.text[:400]}"
        data = r.json()
        assert "prefilled" in data
        assert "ai_prefilled_fields" in data
        assert "missing_keys" in data
        pref = data["prefilled"]
        ai_fields = data["ai_prefilled_fields"]
        # service_type must be an installation-related service
        assert pref.get("service_type") == "installation", f"got service_type={pref.get('service_type')}; full={pref}"
        assert pref.get("services_billing_unit") == "hour", f"got billing_unit={pref.get('services_billing_unit')}"
        assert pref.get("services_travel_required") is True, f"travel_required={pref.get('services_travel_required')}"
        assert pref.get("services_equipment_type"), f"equipment_type not set; pref={pref}"
        # ai_prefilled_fields must include at least those keys AI actually returned
        for k in ["service_type", "services_billing_unit", "services_travel_required"]:
            assert k in ai_fields, f"{k} missing from ai_prefilled_fields={ai_fields}"

    def test_never_overwrites_user_set_fields(self, headers):
        body = {
            "description": "Install 4 aluminum signs 15 miles away, needs a scissor lift",
            "existing_inputs": {"service_type": "wrap_install"},
        }
        r = requests.post(f"{API}/ai/services-prefill", json=body, headers=headers, timeout=120)
        if r.status_code == 402:
            pytest.skip("Insufficient AI credits — non-blocking")
        assert r.status_code == 200, f"AI prefill failed {r.status_code}: {r.text[:400]}"
        data = r.json()
        pref = data["prefilled"]
        ai_fields = data["ai_prefilled_fields"]
        assert "service_type" not in pref, f"service_type MUST NOT be overwritten; got {pref.get('service_type')}"
        assert "service_type" not in ai_fields
        assert "service_type" not in data["missing_keys"], "user-set keys should not be in missing_keys"


# =========================================================
# Rush source + totals
# =========================================================
class TestRushSourceAndTotals:
    def test_rush_source_services_category_when_foundation_unset(self, headers):
        _set_rush_pct(headers, 0)
        resp = _calc(
            headers,
            {
                "service_type": "installation",
                "services_billing_unit": "hour",
                "services_labor_role": "installer",
                "services_complexity": "medium",
                "estimated_hours": 2,
                "num_workers": 1,
                "services_minimum_applies": True,
                "rush_order": True,
            },
        )
        br = resp["breakdown"]
        assert br["rush_percent_source"] == "services_category", f"source={br.get('rush_percent_source')}"
        assert abs(br["rush_percent_applied"] - 25.0) < 0.01, f"rush_percent_applied={br.get('rush_percent_applied')}"

    def test_rush_source_foundation_when_set(self, headers):
        _set_rush_pct(headers, 17.5)
        resp = _calc(
            headers,
            {
                "service_type": "installation",
                "services_billing_unit": "hour",
                "services_labor_role": "installer",
                "services_complexity": "medium",
                "estimated_hours": 2,
                "num_workers": 1,
                "services_minimum_applies": True,
                "rush_order": True,
            },
        )
        br = resp["breakdown"]
        assert br["rush_percent_source"] == "foundation", f"source={br.get('rush_percent_source')}"
        assert abs(br["rush_percent_applied"] - 17.5) < 0.01, f"rush_percent_applied={br.get('rush_percent_applied')}"
        # reset for subsequent tests
        _set_rush_pct(headers, 0)

    def test_spec_named_totals_present_and_match(self, headers):
        resp = _calc(
            headers,
            {
                "service_type": "installation",
                "services_billing_unit": "hour",
                "services_labor_role": "lead_installer",
                "services_complexity": "medium",
                "estimated_hours": 3,
                "num_workers": 1,
                "services_minimum_applies": True,
                "services_travel_required": True,
                "services_travel_miles": 20,
                "services_trip_charge_applies": True,
                "services_trip_count": 1,
                "services_equipment_required": True,
                "services_equipment_type": "scissor_lift",
                "services_equipment_days": 1,
                "services_subcontracted": False,
                "services_permit_external_fee": 50,
            },
        )
        br = resp["breakdown"]
        for k in [
            "total_labor_cost",
            "total_travel_cost",
            "total_equipment_cost",
            "total_subcontract_cost",
            "total_permit_cost",
            "total_production_cost",
        ]:
            assert k in br, f"missing key {k}; keys={list(br.keys())}"
        assert abs(br["total_labor_cost"] - br["labor_cost"]) < 0.01
        assert abs(br["total_travel_cost"] - br["travel_cost"]) < 0.01
        assert abs(br["total_equipment_cost"] - br["equipment_cost"]) < 0.01
        assert abs(br["total_subcontract_cost"] - br["subcontract_cost"]) < 0.01
        assert abs(br["total_permit_cost"] - br["permit_cost"]) < 0.01
        assert abs(br["total_production_cost"] - br["production_cost_total"]) < 0.01


# =========================================================
# Field provenance
# =========================================================
class TestFieldSources:
    def test_field_sources_tags(self, headers):
        # services_billing_unit explicitly set by user; service_type and services_travel_required
        # tagged as AI-prefilled; services_flat_fee left unset → shop_default.
        pd = {
            "service_type": "installation",
            "services_billing_unit": "hour",  # user
            "services_labor_role": "installer",
            "services_complexity": "medium",
            "estimated_hours": 2,
            "num_workers": 1,
            "services_minimum_applies": True,
            "services_travel_required": True,
            "ai_prefilled_fields": ["service_type", "services_travel_required"],
        }
        resp = _calc(headers, pd)
        br = resp["breakdown"]
        fs = br.get("field_sources") or {}
        assert fs.get("service_type") == "ai_estimated", f"service_type src={fs.get('service_type')}; full={fs}"
        assert fs.get("travel_required") == "ai_estimated", f"travel_required src={fs.get('travel_required')}"
        assert fs.get("billing_unit") == "user_entered", f"billing_unit src={fs.get('billing_unit')}"
        assert fs.get("flat_fee") == "shop_default", f"flat_fee src={fs.get('flat_fee')}"


# =========================================================
# Full realistic scenario
# =========================================================
class TestFullScenario:
    def test_install_with_travel_lift_rush(self, headers):
        _set_rush_pct(headers, 0)  # use services category rush=25%
        resp = _calc(
            headers,
            {
                "service_type": "installation",
                "services_billing_unit": "hour",
                "services_labor_role": "lead_installer",
                "services_complexity": "medium",
                "estimated_hours": 4,
                "num_workers": 1,
                "services_minimum_applies": True,
                "services_travel_required": True,
                "services_travel_miles": 15,
                "services_trip_charge_applies": True,
                "services_trip_count": 1,
                "services_equipment_required": True,
                "services_equipment_type": "scissor_lift",
                "services_equipment_days": 1,
                "rush_order": True,
            },
        )
        assert resp["suggested_price"] > 1000.0, f"suggested_price={resp['suggested_price']}"
        assert resp.get("profit_amount", 0) > 0, f"profit_amount={resp.get('profit_amount')}"
        # Response uses profit_margin_percent (not profit_margin)
        assert resp.get("profit_margin_percent", 0) > 30.0, f"profit_margin_percent={resp.get('profit_margin_percent')}"
        assert resp.get("overhead_cost", 0) > 0, f"overhead_cost={resp.get('overhead_cost')}"


# =========================================================
# Minimum charge enforcement
# =========================================================
class TestMinimumCharge:
    def test_tiny_consultation_hits_minimum(self, headers):
        _set_rush_pct(headers, 0)
        resp = _calc(
            headers,
            {
                "service_type": "consultation",
                "services_billing_unit": "hour",
                "services_labor_role": "production",
                "services_complexity": "easy",
                "estimated_hours": 0.25,
                "num_workers": 1,
                "services_minimum_applies": True,
            },
        )
        br = resp["breakdown"]
        # consultation per-service minimum = $50 per request spec; labor alone would be well under.
        assert br["effective_min"] == 50.0, f"effective_min={br.get('effective_min')}; full_br_keys={list(br.keys())}"
        assert resp["suggested_price"] >= 50.0, f"suggested_price={resp['suggested_price']}"
        assert br["minimum_applied"] is True
