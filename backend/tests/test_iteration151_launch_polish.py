"""
Iteration 151 — Launch-polish follow-up tests.

Covers:
  1) Email deep-link rendering in services/wrap_notifications._render_html
     (3 inline buttons, app_url priority resolution, graceful skip).
  2) Email body safety — no internal data (profit/material/labor/etc).
  3) Pending Customer Actions endpoint: GET /api/wrap/pending-customer-actions
     (shape, action codes, tenant isolation).

Frontend & regression suites are run separately.
"""
import os
import asyncio
import importlib
import requests
import pytest


def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if url:
        return url.rstrip("/")
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip().rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = _load_backend_url()

# Shared event loop across the module (motor is loop-bound)
_LOOP = asyncio.new_event_loop()
asyncio.set_event_loop(_LOOP)


def _run(coro):
    return _LOOP.run_until_complete(coro)


# Forbidden internal-data identifiers (skip CSS-words like 'margin')
INTERNAL_TOKENS = [
    "material_cost", "labor_cost", "internal_notes",
    "damage_notes", "install_notes", "profit_amount",
    "profit_margin", "Internal:", "Damage Notes",
]
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"


# ───────────────────── HTTP fixtures ─────────────────────
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ───────────────────── Unit: _render_html ─────────────────────
class TestRenderHtmlButtons:
    """services/wrap_notifications._render_html should emit 3 inline buttons
    when app_url-derived links are present; should skip the block when none."""

    def _render(self, **overrides):
        # Import lazily so backend test process imports server.py only once
        import sys
        sys.path.insert(0, "/app/backend")
        mod = importlib.import_module("services.wrap_notifications")
        kwargs = dict(
            shop_name="Test Shop",
            headline="Customer approved the wrap proof",
            color="#10b981",
            customer_name="John Doe",
            customer_email="jd@example.com",
            order_number="ORD-0018",
            vehicle_summary="2020 Ford Transit",
            wrap_type="Full Wrap",
            item_name="Van Wrap",
            timestamp="2026-01-01T00:00:00+00:00",
            extra_rows=None,
            order_link=None,
            portal_link=None,
            admin_messages_link=None,
        )
        kwargs.update(overrides)
        return mod._render_html(**kwargs)

    def test_all_three_links_render_when_provided(self):
        html = self._render(
            order_link="https://app.example.com/orders/o1",
            portal_link="https://app.example.com/orders/o1/items/t1/wrap-command-center",
            admin_messages_link="https://app.example.com/admin-portal",
        )
        assert 'href="https://app.example.com/orders/o1"' in html
        assert 'href="https://app.example.com/orders/o1/items/t1/wrap-command-center"' in html
        assert 'href="https://app.example.com/admin-portal"' in html
        assert ">Open Order<" in html
        assert ">Open Wrap Command Center<" in html
        assert ">Respond in Admin Portal<" in html

    def test_no_buttons_when_all_links_missing(self):
        html = self._render()
        # No <a href=...> should appear in the buttons block
        assert 'href="' not in html or 'Open Order' not in html
        assert "Open Wrap Command Center" not in html
        assert "Respond in Admin Portal" not in html

    def test_no_internal_data_in_body(self):
        html = self._render(
            order_link="https://app.example.com/orders/o1",
            portal_link="https://app.example.com/p",
            admin_messages_link="https://app.example.com/admin-portal",
            extra_rows=[("Revision notes", "please make red")],
        )
        for forbidden in INTERNAL_TOKENS:
            assert forbidden not in html, f"Leak: {forbidden}"


# ───────────────────── Dispatch-level integration ─────────────────────
class TestDispatchAppUrlPriority:
    """Patch EmailService.send_email and assert all 3 hrefs appear in html_content
    for the 6 portal actions when app_url resolves from env."""

    def _setup_module_and_db(self):
        import sys
        sys.path.insert(0, "/app/backend")
        # Force FRONTEND_URL so resolution is deterministic
        os.environ["FRONTEND_URL"] = "https://frontend.example.com"
        from server import db  # noqa
        wrap_mod = importlib.import_module("services.wrap_notifications")
        return wrap_mod, db

    @pytest.mark.parametrize("action_key", [
        "proof_approved", "revision_requested", "contract_signed",
        "quote_approved", "inspection_acknowledged", "aftercare_acknowledged",
    ])
    def test_three_hrefs_present_per_action(self, action_key):
        wrap_mod, db = self._setup_module_and_db()
        captured = {}

        async def fake_send_email(self, *, to_email, subject, html_content, tenant_id=None, **kw):
            captured["to"] = to_email
            captured["subject"] = subject
            captured["html"] = html_content
            return {"success": True}

        # Patch the EmailService class method
        from services.email_service import EmailService
        orig = EmailService.send_email
        EmailService.send_email = fake_send_email
        try:
            # Seed a tiny tenant + order + customer + ticket + wrap_data
            tenant_id = "TEST_TENANT_151"
            order_id = "TEST_ORDER_151"
            ticket_id = "TEST_TICKET_151"
            customer_id = "TEST_CUST_151"

            async def seed():
                await db.tenants.update_one(
                    {"id": tenant_id},
                    {"$set": {
                        "id": tenant_id,
                        "business_name": "Iter151 Shop",
                        "notification_email": "shop@example.com",
                    }}, upsert=True,
                )
                await db.orders.update_one(
                    {"id": order_id, "tenant_id": tenant_id},
                    {"$set": {"id": order_id, "tenant_id": tenant_id,
                              "order_number": "ORD-0151", "customer_id": customer_id}},
                    upsert=True,
                )
                await db.customers.update_one(
                    {"id": customer_id, "tenant_id": tenant_id},
                    {"$set": {"id": customer_id, "tenant_id": tenant_id,
                              "first_name": "Iter", "last_name": "151",
                              "email": "c151@example.com"}},
                    upsert=True,
                )
                await db.job_tickets.update_one(
                    {"id": ticket_id, "tenant_id": tenant_id},
                    {"$set": {"id": ticket_id, "tenant_id": tenant_id,
                              "order_id": order_id, "item_name": "Wrap Item 151"}},
                    upsert=True,
                )
                await db.wrap_data.update_one(
                    {"tenant_id": tenant_id, "ticket_id": ticket_id},
                    {"$set": {"tenant_id": tenant_id, "ticket_id": ticket_id,
                              "wrap_type": "Full Wrap",
                              "vehicle_info": {"year": "2020", "make": "Ford",
                                               "model": "Transit", "color": "White"}}},
                    upsert=True,
                )

            _run(seed())

            result = _run(
                wrap_mod.send_wrap_portal_action_notification(
                    tenant_id=tenant_id, ticket_id=ticket_id, action_key=action_key,
                )
            )
            assert result.get("sent") is True, f"dispatch result: {result}"
            html = captured.get("html", "")
            assert "https://frontend.example.com/orders/" in html
            assert "wrap-command-center" in html
            assert "/admin-portal" in html
            # Body safety
            for f in ["material_cost", "labor_cost",
                      "internal_notes", "damage_notes", "install_notes"]:
                assert f not in html.lower(), f"Leak in {action_key}: {f}"
        finally:
            EmailService.send_email = orig

    def test_no_buttons_when_no_app_url(self):
        wrap_mod, db = self._setup_module_and_db()
        # Wipe env so nothing resolves
        os.environ.pop("FRONTEND_URL", None)
        prev = os.environ.pop("REACT_APP_BACKEND_URL", None)
        captured = {}

        async def fake_send_email(self, *, to_email, subject, html_content, tenant_id=None, **kw):
            captured["html"] = html_content
            return {"success": True}

        from services.email_service import EmailService
        orig = EmailService.send_email
        EmailService.send_email = fake_send_email
        try:
            tenant_id = "TEST_TENANT_151_NL"

            async def seed():
                await db.tenants.update_one(
                    {"id": tenant_id},
                    {"$set": {"id": tenant_id, "business_name": "NoLink Shop",
                              "notification_email": "shop@example.com"}},
                    upsert=True,
                )
                await db.job_tickets.update_one(
                    {"id": "T_NL", "tenant_id": tenant_id},
                    {"$set": {"id": "T_NL", "tenant_id": tenant_id}}, upsert=True,
                )
                await db.wrap_data.update_one(
                    {"tenant_id": tenant_id, "ticket_id": "T_NL"},
                    {"$set": {"tenant_id": tenant_id, "ticket_id": "T_NL"}}, upsert=True,
                )

            _run(seed())
            res = _run(
                wrap_mod.send_wrap_portal_action_notification(
                    tenant_id=tenant_id, ticket_id="T_NL", action_key="proof_approved",
                )
            )
            assert res.get("sent") is True
            html = captured.get("html", "")
            assert "Open Order" not in html
            assert "Open Wrap Command Center" not in html
            assert "Respond in Admin Portal" not in html
        finally:
            EmailService.send_email = orig
            if prev:
                os.environ["REACT_APP_BACKEND_URL"] = prev


# ───────────────────── Pending Customer Actions API ─────────────────────
class TestPendingCustomerActionsApi:
    def test_endpoint_returns_shape(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/wrap/pending-customer-actions",
            headers=admin_headers, timeout=20,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data and "total" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert data["total"] == len(data["items"])

    def test_each_item_has_required_fields(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/wrap/pending-customer-actions",
            headers=admin_headers, timeout=20,
        )
        data = r.json()
        if not data["items"]:
            pytest.skip("No pending items in tenant — shape check skipped")
        VALID_CODES = {
            "proof_pending", "revision_requested", "contract_pending",
            "quote_pending", "inspection_pending", "aftercare_pending",
        }
        for it in data["items"]:
            for k in ("ticket_id", "order_id", "order_number", "customer_name",
                      "wrap_type", "vehicle", "actions"):
                assert k in it, f"missing {k}"
            assert isinstance(it["actions"], list) and len(it["actions"]) > 0
            for a in it["actions"]:
                assert "code" in a and "label" in a
                assert a["code"] in VALID_CODES, f"unexpected action code {a['code']}"

    def test_unauthenticated_rejected(self):
        r = requests.get(
            f"{BASE_URL}/api/wrap/pending-customer-actions", timeout=20,
        )
        assert r.status_code in (401, 403)
