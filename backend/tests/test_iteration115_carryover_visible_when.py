"""
Iteration 115 - Carryover Override + Rigid/Cut Vinyl visible_when rules + Timeclock regression.

Review request coverage:
1. PUT /api/employees/{id} accepts carryover_override (float / 0 / null clears).
2. GET /api/payroll/timesheet returns carryover_balance reflecting override.
3. GET /api/job-tickets/schema/rigid_signs visible_when rules:
   install_complexity, hardware_type, drill_prep_required, double_sided_art,
   protective_finish_type, design_complexity.
4. GET /api/job-tickets/schema/cut_vinyl visible_when rules: install_complexity, design_complexity.
5. carryover_override round-trips on GET /api/employees/{id}.
6. POST /api/payroll/timeclock-shifts regression with ISO clock_in/clock_out.

Credentials: signguypa@gmail.com / Billnel323 (owner).
Target employee: 18eed187-1a90-4bf8-b233-dc47b44c9579
"""
import os
import uuid
from datetime import datetime, timezone

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://job-tracker-pro-32.preview.emergentagent.com").rstrip("/")
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"
EMPLOYEE_ID = "18eed187-1a90-4bf8-b233-dc47b44c9579"


# -------- Fixtures --------

@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def auth_token(api_client):
    resp = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30,
    )
    if resp.status_code != 200:
        pytest.skip(f"Login failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        pytest.skip(f"No token in login response: {data}")
    return token


@pytest.fixture(scope="module")
def auth_client(api_client, auth_token):
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


@pytest.fixture(scope="module", autouse=True)
def cleanup_carryover(auth_client):
    """Ensure carryover_override is cleared (null) after tests so prod state is restored."""
    yield
    try:
        auth_client.put(
            f"{BASE_URL}/api/employees/{EMPLOYEE_ID}",
            json={"carryover_override": None},
            timeout=30,
        )
    except Exception:
        pass


# -------- Helpers --------

def _get_timesheet_carryover(auth_client, employee_id=EMPLOYEE_ID):
    resp = auth_client.get(
        f"{BASE_URL}/api/payroll/timesheet",
        params={
            "start_date": "2026-01-05",
            "end_date": "2026-01-11",
            "employee_id": employee_id,
        },
        timeout=30,
    )
    assert resp.status_code == 200, f"timesheet failed: {resp.status_code} {resp.text[:300]}"
    data = resp.json()
    emps = data.get("employees", [])
    assert emps, f"no employees in timesheet: {data}"
    return emps[0]["carryover_balance"]


# -------- TEST: Carryover override --------

class TestCarryoverOverride:
    def test_set_carryover_override_to_500(self, auth_client):
        resp = auth_client.put(
            f"{BASE_URL}/api/employees/{EMPLOYEE_ID}",
            json={"carryover_override": 500.0},
            timeout=30,
        )
        assert resp.status_code == 200, f"PUT failed: {resp.status_code} {resp.text[:300]}"
        body = resp.json()
        assert body.get("carryover_override") == 500.0, f"Response missing override: {body}"

        # Round-trip GET
        g = auth_client.get(f"{BASE_URL}/api/employees/{EMPLOYEE_ID}", timeout=30)
        assert g.status_code == 200
        assert g.json().get("carryover_override") == 500.0

        # Timesheet reflects
        carry = _get_timesheet_carryover(auth_client)
        assert carry == 500.0, f"expected 500.0, got {carry}"

    def test_set_carryover_override_to_zero(self, auth_client):
        resp = auth_client.put(
            f"{BASE_URL}/api/employees/{EMPLOYEE_ID}",
            json={"carryover_override": 0},
            timeout=30,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("carryover_override") in (0, 0.0), f"got {body.get('carryover_override')}"

        # GET
        g = auth_client.get(f"{BASE_URL}/api/employees/{EMPLOYEE_ID}", timeout=30)
        assert g.status_code == 200
        assert g.json().get("carryover_override") in (0, 0.0)

        # Timesheet
        carry = _get_timesheet_carryover(auth_client)
        assert carry == 0.0, f"expected 0.0, got {carry}"

    def test_clear_carryover_override_with_null(self, auth_client):
        # First set an override
        auth_client.put(
            f"{BASE_URL}/api/employees/{EMPLOYEE_ID}",
            json={"carryover_override": 1234.56},
            timeout=30,
        )
        # Now clear
        resp = auth_client.put(
            f"{BASE_URL}/api/employees/{EMPLOYEE_ID}",
            json={"carryover_override": None},
            timeout=30,
        )
        assert resp.status_code == 200, f"PUT null failed: {resp.status_code} {resp.text[:300]}"
        body = resp.json()
        assert body.get("carryover_override") in (None, ), f"override not cleared: {body.get('carryover_override')}"

        # Verify GET shows no/null override
        g = auth_client.get(f"{BASE_URL}/api/employees/{EMPLOYEE_ID}", timeout=30)
        assert g.status_code == 200
        assert g.json().get("carryover_override") in (None, )


# -------- TEST: Rigid Signs schema visible_when --------

class TestRigidSignsVisibleWhen:
    @pytest.fixture(scope="class")
    def schema(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/job-tickets/schema/rigid_signs", timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        return r.json()

    @staticmethod
    def _rules_map(schema):
        fields = schema.get("fields") or schema.get("schema") or schema
        if isinstance(fields, dict) and "fields" in fields:
            fields = fields["fields"]
        out = {}
        for f in fields:
            if not isinstance(f, dict):
                continue
            key = f.get("key")
            if key and "visible_when" in f:
                out[key] = f["visible_when"]
        return out

    def test_install_complexity_depends_install_required(self, schema):
        rules = self._rules_map(schema)
        assert "install_complexity" in rules, f"install_complexity not in rules: {list(rules)}"
        assert rules["install_complexity"] == {"install_required": True}

    def test_hardware_type_depends_hardware_included(self, schema):
        rules = self._rules_map(schema)
        assert rules.get("hardware_type") == {"hardware_included": True}

    def test_drill_prep_depends_hardware_included(self, schema):
        rules = self._rules_map(schema)
        assert rules.get("drill_prep_required") == {"hardware_included": True}

    def test_double_sided_art_depends_sidedness_double(self, schema):
        rules = self._rules_map(schema)
        assert rules.get("double_sided_art") == {"sidedness": "double"}

    def test_protective_finish_type_depends_protective_finish(self, schema):
        rules = self._rules_map(schema)
        assert rules.get("protective_finish_type") == {"protective_finish": True}

    def test_design_complexity_depends_artwork_needed(self, schema):
        rules = self._rules_map(schema)
        assert rules.get("design_complexity") == {"artwork_needed": True}


# -------- TEST: Cut Vinyl schema visible_when --------

class TestCutVinylVisibleWhen:
    @pytest.fixture(scope="class")
    def schema(self, auth_client):
        r = auth_client.get(f"{BASE_URL}/api/job-tickets/schema/cut_vinyl", timeout=30)
        assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
        return r.json()

    def test_install_complexity_rule(self, schema):
        rules = TestRigidSignsVisibleWhen._rules_map(schema)
        assert rules.get("install_complexity") == {"install_required": True}

    def test_design_complexity_rule(self, schema):
        rules = TestRigidSignsVisibleWhen._rules_map(schema)
        assert rules.get("design_complexity") == {"artwork_needed": True}


# -------- TEST: Timeclock regression --------

class TestTimeclockShiftRegression:
    def test_create_timeclock_shift_with_iso(self, auth_client):
        # New York 10pm UTC equivalent - test ISO strings with TZ
        date_str = "2026-01-06"
        clock_in_iso = "2026-01-07T03:00:00+00:00"   # 10pm EST
        clock_out_iso = "2026-01-07T07:00:00+00:00"  # 2am EST
        payload = {
            "employee_id": EMPLOYEE_ID,
            "date": date_str,
            "clock_in": clock_in_iso,
            "clock_out": clock_out_iso,
            "break_minutes": 0,
            "notes": f"TEST_iter115_{uuid.uuid4().hex[:8]}",
        }
        resp = auth_client.post(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            json=payload,
            timeout=30,
        )
        assert resp.status_code in (200, 201), f"{resp.status_code} {resp.text[:300]}"
        shift = resp.json()
        assert shift.get("clock_in") == clock_in_iso
        assert shift.get("clock_out") == clock_out_iso
        assert shift.get("employee_id") == EMPLOYEE_ID
        assert shift.get("status") == "finished"
        assert "id" in shift
        # Metrics should be calculated (4 hours = 240 min)
        assert shift.get("work_minutes") == 240.0, f"expected 240 work_minutes, got {shift.get('work_minutes')}"
        assert shift.get("net_minutes") == 240.0
        assert shift.get("net_hours") == 4.0

        # Cleanup: delete the test shift
        shift_id = shift["id"]
        try:
            auth_client.delete(
                f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}",
                timeout=30,
            )
        except Exception:
            pass
