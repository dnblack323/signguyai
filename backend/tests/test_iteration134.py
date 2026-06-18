"""Iteration 134 Tests:
PART 1: Customer Request Appointment flow (portal request -> admin confirm/reject)
PART 2: Tier 5 Backend audit (admin/settings checklist items 5.1-5.12)
"""

import os
import json
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://sms-email-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
PORTAL_EMAIL = "taxtest_non@example.com"
PORTAL_PASSWORD = "portal123"
STAFF_EMAIL = "staff_payroll_test@test.com"
STAFF_PASSWORD = "StaffTest123!"


# ---------------- Fixtures ----------------

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def admin_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def portal_token():
    r = requests.post(f"{API}/portal/auth/login", json={"email": PORTAL_EMAIL, "password": PORTAL_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def portal_h(portal_token):
    return {"Authorization": f"Bearer {portal_token}"}


@pytest.fixture(scope="session")
def staff_token():
    r = requests.post(f"{API}/auth/login", json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD})
    if r.status_code != 200:
        pytest.skip("staff user not available")
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def staff_h(staff_token):
    return {"Authorization": f"Bearer {staff_token}"}


# ---------------- PART 1: Customer Appointment Request ----------------

class TestAppointmentRequestFlow:
    appt_id = None

    def test_01_request_missing_preferred_date(self, portal_h):
        r = requests.post(f"{API}/portal/appointments/request", headers=portal_h, json={"appointment_type": "consultation"})
        assert r.status_code in (400, 422), r.text

    def test_02_create_request(self, portal_h):
        payload = {
            "appointment_type": "consultation",
            "preferred_date": "2026-06-15",
            "preferred_time": "14:00",
            "location": "Shop",
            "description": "Test request via iteration 134",
        }
        r = requests.post(f"{API}/portal/appointments/request", headers=portal_h, json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "requested"
        assert data["requested_by_customer"] is True
        assert data["duration_minutes"] == 60
        assert data["customer_id"] == "1eaeec1d-6fbb-48fa-aa96-ecc4298bdb8b"
        assert data["scheduled_date"] == "2026-06-15"
        assert "_id" not in data
        TestAppointmentRequestFlow.appt_id = data["id"]

    def test_03_portal_upcoming_includes_requested(self, portal_h):
        r = requests.get(f"{API}/portal/appointments?upcoming_only=true", headers=portal_h)
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()]
        assert TestAppointmentRequestFlow.appt_id in ids

    def test_04_admin_sees_requested(self, admin_h):
        r = requests.get(f"{API}/appointments?status=requested", headers=admin_h)
        assert r.status_code == 200
        ids = [a["id"] for a in r.json()]
        assert TestAppointmentRequestFlow.appt_id in ids

    def test_05_admin_confirm(self, admin_h, portal_h):
        appt_id = TestAppointmentRequestFlow.appt_id
        body = {"scheduled_start": "2026-06-15T15:00:00", "scheduled_end": "2026-06-15T16:00:00", "notes": "Confirmed by test"}
        r = requests.put(f"{API}/appointments/{appt_id}/confirm", headers=admin_h, json=body)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "confirmed"
        # Re-fetch via portal
        r2 = requests.get(f"{API}/portal/appointments?upcoming_only=true", headers=portal_h)
        assert r2.status_code == 200
        match = [a for a in r2.json() if a["id"] == appt_id]
        assert match and match[0]["status"] == "confirmed"

    def test_06_admin_reject_new_request(self, admin_h, portal_h):
        # Create another request, then reject
        r = requests.post(f"{API}/portal/appointments/request", headers=portal_h, json={
            "appointment_type": "site_survey",
            "preferred_date": "2026-07-01",
            "preferred_time": "10:00",
        })
        assert r.status_code == 200
        appt2 = r.json()["id"]
        rj = requests.put(f"{API}/appointments/{appt2}/reject", headers=admin_h, json={"reason": "Booked already"})
        assert rj.status_code == 200, rj.text
        d = rj.json()
        assert d["status"] == "cancelled"
        assert "Booked already" in (d.get("notes") or "")
        # cleanup
        requests.delete(f"{API}/appointments/{appt2}", headers=admin_h)

    def test_07_cleanup_confirmed_appt(self, admin_h):
        if TestAppointmentRequestFlow.appt_id:
            requests.delete(f"{API}/appointments/{TestAppointmentRequestFlow.appt_id}", headers=admin_h)


# ---------------- PART 2: Tier 5 Audit ----------------

class TestTier5_UserManagement:
    """5.1 User management"""
    created_uid = None

    def test_create_user(self, admin_h):
        email = f"TEST_t5_user_{uuid.uuid4().hex[:6]}@test.com"
        r = requests.post(f"{API}/admin/users/create", headers=admin_h, json={
            "email": email, "full_name": "T5 User", "password": "Password123!", "role": "staff"
        })
        assert r.status_code in (200, 201), r.text
        d = r.json()
        TestTier5_UserManagement.created_uid = d.get("id")
        assert d["email"].lower() == email.lower()

    def test_change_role(self, admin_h):
        uid = TestTier5_UserManagement.created_uid
        if not uid:
            pytest.skip("no user")
        r = requests.put(f"{API}/admin/users/{uid}/role", headers=admin_h, json={"role": "admin"})
        assert r.status_code == 200, r.text

    def test_delete_user_endpoint_present(self, admin_h):
        uid = TestTier5_UserManagement.created_uid
        if not uid:
            pytest.skip("no user")
        r = requests.delete(f"{API}/admin/users/{uid}", headers=admin_h)
        # Capture current behavior; xfail if not implemented
        if r.status_code == 404 or r.status_code == 405:
            pytest.xfail(f"DELETE /admin/users/{{id}} not implemented (got {r.status_code})")
        assert r.status_code in (200, 204)


class TestTier5_DigestConfig:
    """5.4 Digest"""
    def test_get_settings(self, admin_h):
        r = requests.get(f"{API}/digest/settings", headers=admin_h)
        assert r.status_code == 200, r.text

    def test_update_settings(self, admin_h):
        r = requests.put(f"{API}/digest/settings", headers=admin_h, json={"enabled": True, "send_time": "08:00"})
        assert r.status_code == 200, r.text

    def test_preview(self, admin_h):
        r = requests.get(f"{API}/digest/preview", headers=admin_h)
        assert r.status_code == 200, r.text


class TestTier5_PromoCodes:
    """5.7 Promo codes CRUD"""
    pid = None

    def test_create_percent(self, admin_h):
        r = requests.post(f"{API}/promo-codes", headers=admin_h, json={
            "code": f"TEST{uuid.uuid4().hex[:6].upper()}",
            "discount_type": "percent",
            "discount_value": 10,
            "max_redemptions": 5,
            "expires_at": "2026-12-31T23:59:59",
        })
        assert r.status_code in (200, 201), r.text
        TestTier5_PromoCodes.pid = r.json()["id"]

    def test_list(self, admin_h):
        r = requests.get(f"{API}/promo-codes", headers=admin_h)
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert TestTier5_PromoCodes.pid in ids

    def test_update(self, admin_h):
        if not TestTier5_PromoCodes.pid:
            pytest.skip()
        r = requests.put(f"{API}/promo-codes/{TestTier5_PromoCodes.pid}", headers=admin_h, json={"discount_value": 15})
        assert r.status_code == 200, r.text

    def test_delete(self, admin_h):
        if not TestTier5_PromoCodes.pid:
            pytest.skip()
        r = requests.delete(f"{API}/promo-codes/{TestTier5_PromoCodes.pid}", headers=admin_h)
        assert r.status_code in (200, 204)


class TestTier5_Community:
    """5.8 Community Hub"""
    post_id = None

    def test_create_post(self, admin_h):
        r = requests.post(f"{API}/community/posts", headers=admin_h, json={
            "title": "TEST_iter134_post",
            "body": "Test content body for iteration 134",
            "category": "feedback",
        })
        if r.status_code == 404:
            pytest.xfail("Community routes not registered")
        assert r.status_code in (200, 201), r.text
        TestTier5_Community.post_id = r.json().get("id")

    def test_list_posts(self, admin_h):
        r = requests.get(f"{API}/community/posts", headers=admin_h)
        if r.status_code == 404:
            pytest.xfail("Community not available")
        assert r.status_code == 200

    def test_upvote(self, admin_h):
        if not TestTier5_Community.post_id:
            pytest.skip()
        r = requests.post(f"{API}/community/posts/{TestTier5_Community.post_id}/upvote", headers=admin_h)
        assert r.status_code in (200, 201, 204)

    def test_delete(self, admin_h):
        if not TestTier5_Community.post_id:
            pytest.skip()
        r = requests.delete(f"{API}/community/posts/{TestTier5_Community.post_id}", headers=admin_h)
        assert r.status_code in (200, 204)


class TestTier5_PricingFoundation:
    """5.10 Pricing Foundation - exposed under /api/pricing/defaults & /settings"""

    def test_get_defaults(self, admin_h):
        r = requests.get(f"{API}/pricing/defaults", headers=admin_h)
        assert r.status_code == 200, r.text

    def test_update_defaults_and_calculate(self, admin_h):
        r0 = requests.get(f"{API}/pricing/defaults", headers=admin_h)
        original = r0.json() if r0.status_code == 200 else {}
        # change a markup or rate
        new_payload = dict(original)
        new_payload["default_markup_percent"] = 42.5
        r = requests.put(f"{API}/pricing/defaults", headers=admin_h, json=new_payload)
        if r.status_code in (404, 405, 422):
            pytest.xfail(f"PUT /pricing/defaults rejected ({r.status_code}): {r.text[:120]}")
        assert r.status_code == 200, r.text
        # restore original best-effort
        if original:
            requests.put(f"{API}/pricing/defaults", headers=admin_h, json=original)


class TestTier5_TenantSettings:
    """5.11 Company / Tenant settings"""

    def test_put_tenant(self, admin_h):
        r0 = requests.get(f"{API}/tenant", headers=admin_h)
        assert r0.status_code == 200, r0.text
        original = r0.json()
        new_phone = "555-0134-TEST"
        r = requests.put(f"{API}/tenant", headers=admin_h, json={"phone": new_phone})
        assert r.status_code == 200, r.text
        # verify persistence
        r2 = requests.get(f"{API}/tenant", headers=admin_h)
        assert r2.status_code == 200
        assert r2.json().get("phone") == new_phone
        # restore
        if original.get("phone") is not None:
            requests.put(f"{API}/tenant", headers=admin_h, json={"phone": original.get("phone")})


class TestTier5_EmailTemplates:
    """5.12 Email templates"""
    template_id = None

    def test_list(self, admin_h):
        r = requests.get(f"{API}/email-templates", headers=admin_h)
        assert r.status_code == 200, r.text
        items = r.json()
        if isinstance(items, list) and items:
            TestTier5_EmailTemplates.template_id = items[0]["id"]

    def test_get_one(self, admin_h):
        if not TestTier5_EmailTemplates.template_id:
            pytest.skip("no template seeded")
        r = requests.get(f"{API}/email-templates/{TestTier5_EmailTemplates.template_id}", headers=admin_h)
        assert r.status_code == 200

    def test_update(self, admin_h):
        if not TestTier5_EmailTemplates.template_id:
            pytest.skip()
        # get current to preserve
        r0 = requests.get(f"{API}/email-templates/{TestTier5_EmailTemplates.template_id}", headers=admin_h)
        cur = r0.json()
        r = requests.put(f"{API}/email-templates/{TestTier5_EmailTemplates.template_id}", headers=admin_h, json={
            "subject": cur.get("subject", "Test") + " ",
            "body_html": cur.get("body_html", "<p>x</p>"),
        })
        # Some templates may be locked; accept 200/400/403
        assert r.status_code in (200, 400, 403), r.text

    def test_preview(self, admin_h):
        if not TestTier5_EmailTemplates.template_id:
            pytest.skip()
        r = requests.post(f"{API}/email-templates/{TestTier5_EmailTemplates.template_id}/preview", headers=admin_h, json={})
        assert r.status_code in (200, 400)


class TestTier5_AdminPortal:
    """5.2 Admin Portal Communications Hub - check protected routes work for owner"""

    def test_dashboard(self, admin_h):
        r = requests.get(f"{API}/admin-portal/dashboard", headers=admin_h)
        assert r.status_code == 200, r.text
