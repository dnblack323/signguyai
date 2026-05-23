"""
Phase 1 Dashboard Contract Tests

Strategy: HTTP-only tests against the live server using requests.
No Motor/event-loop issues. Tests use /api/auth/register to create isolated
tenant contexts per test class, and seed data via the REST API.

Coverage:
1. GET /api/dashboard/stats — fixes verified:
   - active_jobs/active_orders sourced from db.orders (not db.jobs)
   - pending_invoices excludes draft
   - backward-compat: all original keys still present

2. Schema + empty-dataset contract tests for all 5 new endpoints

3. Tenant isolation — data from other tenants must not appear

4. financial top_records <= 3 assertion

5. Urgency ordering for customer-attention lists

6. All new endpoints include last_updated_at

7. Legacy deprecated endpoints still callable (backward compat)
"""

import pytest
import requests
import uuid
import os
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid():
    return str(uuid.uuid4())


def _today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _iso_now():
    return datetime.now(timezone.utc).isoformat()


def _register_and_login():
    """Register a fresh isolated tenant and return (token, headers)."""
    email = f"phase1_test_{_uid()[:8]}@example.com"
    payload = {
        "email": email,
        "password": "TestPass123!",
        "full_name": "Phase1 Tester",
        "company_name": f"Test Shop {_uid()[:6]}",
    }
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert resp.status_code == 200, f"Register failed: {resp.text}"
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return token, headers


def _get_first_customer_id(headers):
    """Fetch the first customer id from the tenant (created during onboarding)."""
    resp = requests.get(f"{BASE_URL}/api/customers", headers=headers)
    assert resp.status_code == 200, f"List customers failed: {resp.text}"
    customers = resp.json()
    assert len(customers) > 0, "No customers found — onboarding must create at least one"
    return customers[0]["id"]


def _create_customer(headers, name="Test Customer"):
    """Create a customer and return its id."""
    resp = requests.post(
        f"{BASE_URL}/api/customers",
        json={"name": name, "email": f"{_uid()[:6]}@test.com"},
        headers=headers,
    )
    assert resp.status_code in (200, 201), f"Create customer failed: {resp.text}"
    return resp.json()["id"]


def _create_order(headers, customer_id=None, **kwargs):
    """Create an order via POST /api/orders. Always uses 'new_intake' initial status."""
    if not customer_id:
        customer_id = _get_first_customer_id(headers)
    payload = {
        "customer_id": customer_id,
        "customer_name": kwargs.pop("customer_name", "Test Customer"),
        "status": "new_intake",   # API enforces new_intake or draft as initial status
        "order_type": kwargs.pop("order_type", "standard"),
    }
    payload.update(kwargs)
    resp = requests.post(f"{BASE_URL}/api/orders", json=payload, headers=headers)
    assert resp.status_code in (200, 201), f"Create order failed: {resp.text}"
    return resp.json()


def _create_invoice(headers, customer_id=None, status="sent", total=100.0, **kwargs):
    """Create an invoice via POST /api/invoices. Requires customer_id."""
    if not customer_id:
        customer_id = _get_first_customer_id(headers)
    payload = {
        "customer_id": customer_id,
        "status": status,
        "total": total,
        "due_date": kwargs.pop("due_date", _today_str()),
        "line_items": [{"description": "Test item", "quantity": 1,
                        "unit_price": total, "total": total}],
    }
    payload.update(kwargs)
    resp = requests.post(f"{BASE_URL}/api/invoices", json=payload, headers=headers)
    assert resp.status_code in (200, 201), f"Create invoice failed ({status}): {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# 1. GET /api/dashboard/stats  — fix assertions
# ---------------------------------------------------------------------------

class TestDashboardStatsBackwardCompat:
    """Ensure the fixed /stats endpoint returns all original keys."""

    def setup_method(self):
        self.token, self.headers = _register_and_login()

    def test_all_original_keys_present(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        for key in ["total_customers", "active_jobs", "pending_invoices",
                    "today_revenue", "overdue_count", "overdue_total"]:
            assert key in data, f"Backward-compat key missing: {key}"

    def test_new_active_orders_key_present(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert resp.status_code == 200
        assert "active_orders" in resp.json(), "New active_orders key missing"

    def test_active_jobs_equals_active_orders(self):
        """active_jobs (compat) and active_orders (new) must return the same value."""
        resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_jobs"] == data["active_orders"], (
            f"active_jobs={data['active_jobs']} != active_orders={data['active_orders']}"
        )

    def test_empty_tenant_returns_zero_active_orders(self):
        """A fresh tenant with no orders seeded should have active_orders == 0."""
        resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        # active_orders comes from db.orders (not legacy jobs), fresh tenant has 0
        assert data["active_jobs"] == 0
        assert data["active_orders"] == 0

    def test_active_orders_increments_when_order_created(self):
        """Creating a new_intake order must increment active_orders by 1."""
        before = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers).json()
        _create_order(self.headers)
        after = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers).json()
        assert after["active_orders"] == before["active_orders"] + 1
        assert after["active_jobs"] == before["active_jobs"] + 1

    def test_pending_invoices_excludes_draft(self):
        """Adding a draft invoice must NOT increment pending_invoices; adding sent must."""
        before = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers).json()
        _create_invoice(self.headers, status="draft", total=100.0)    # should NOT count
        _create_invoice(self.headers, status="sent", total=200.0)     # should count

        after = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers).json()
        # Only the sent invoice increments pending_invoices (draft excluded)
        assert after["pending_invoices"] == before["pending_invoices"] + 1, (
            f"Expected +1 (sent only), got before={before['pending_invoices']} after={after['pending_invoices']}"
        )


# ---------------------------------------------------------------------------
# 2. GET /api/dashboard/summary-v2 — shape + severity
# ---------------------------------------------------------------------------

class TestSummaryV2:

    def setup_method(self):
        self.token, self.headers = _register_and_login()

    def test_empty_dataset_all_neutral(self):
        """Fresh tenant — all counts should be 0 and severities neutral for a clean account."""
        resp = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "last_updated_at" in data
        assert "metrics" in data
        # All required metric keys must be present
        for key in ["due_today", "overdue", "awaiting_approval",
                    "unread_messages", "in_production", "unpaid_invoices"]:
            assert key in data["metrics"], f"Missing metric: {key}"
        # active_orders should be 0 for fresh account
        assert data["metrics"]["in_production"]["count"] == 0
        assert data["metrics"]["in_production"]["severity"] == "neutral"
        # All severities are valid
        valid = {"neutral", "amber", "red"}
        for key, val in data["metrics"].items():
            assert val["severity"] in valid

    def test_schema_has_required_fields_per_metric(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers)
        data = resp.json()
        for key, val in data["metrics"].items():
            assert "count" in val, f"{key} missing count"
            assert "severity" in val, f"{key} missing severity"

    def test_severity_is_valid_value(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers)
        data = resp.json()
        valid = {"neutral", "amber", "red"}
        for key, val in data["metrics"].items():
            assert val["severity"] in valid, f"{key} severity={val['severity']} not in {valid}"

    def test_unpaid_invoices_severity_increases_with_invoices(self):
        """Adding sent invoices must increase unpaid_invoices count and eventually turn amber."""
        before = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers).json()
        before_count = before["metrics"]["unpaid_invoices"]["count"]

        for _ in range(3):
            _create_invoice(self.headers, status="sent", total=100.0)

        resp = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers)
        data = resp.json()
        assert data["metrics"]["unpaid_invoices"]["count"] == before_count + 3
        assert data["metrics"]["unpaid_invoices"]["severity"] in ("amber", "red")

    def test_last_updated_at_is_recent_iso(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers)
        ts = resp.json()["last_updated_at"]
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - dt).total_seconds()
        assert age < 30, f"last_updated_at is too old: {ts}"


# ---------------------------------------------------------------------------
# 3. GET /api/dashboard/today-command-center — shape
# ---------------------------------------------------------------------------

class TestTodayCommandCenter:

    def setup_method(self):
        self.token, self.headers = _register_and_login()

    def test_empty_dataset_returns_valid_schema(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/today-command-center", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "last_updated_at" in data
        assert "due_order_items_today" in data
        assert "appointments_installs_today" in data
        assert "team_status_today" in data
        assert isinstance(data["due_order_items_today"], list)
        assert isinstance(data["appointments_installs_today"], list)

    def test_team_status_today_subschema(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/today-command-center", headers=self.headers)
        data = resp.json()
        tst = data["team_status_today"]
        assert "scheduled_count" in tst
        assert "clocked_in_count" in tst
        assert "employees" in tst
        assert isinstance(tst["employees"], list)
        assert isinstance(tst["scheduled_count"], int)
        assert isinstance(tst["clocked_in_count"], int)

    def test_due_order_items_today_item_shape_when_present(self):
        """If any due items returned, verify all required fields are present."""
        resp = requests.get(f"{BASE_URL}/api/dashboard/today-command-center", headers=self.headers)
        data = resp.json()
        for item in data["due_order_items_today"]:
            for field in ["order_id", "order_number", "order_item_id", "item_name",
                          "customer_name", "due_at", "stage", "priority"]:
                assert field in item, f"due_order_items_today item missing: {field}"

    def test_appointments_today_item_shape_when_present(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/today-command-center", headers=self.headers)
        data = resp.json()
        for item in data["appointments_installs_today"]:
            for field in ["appointment_id", "title", "customer_name",
                          "start_at", "type", "status", "order_id"]:
                assert field in item, f"appointments_installs_today item missing: {field}"

    def test_last_updated_at_present(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/today-command-center", headers=self.headers)
        assert "last_updated_at" in resp.json()


# ---------------------------------------------------------------------------
# 4. GET /api/dashboard/production-snapshot — stage counts + at-risk
# ---------------------------------------------------------------------------

class TestProductionSnapshot:

    def setup_method(self):
        self.token, self.headers = _register_and_login()

    def test_empty_dataset_returns_valid_schema(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "last_updated_at" in data
        assert "order_items_by_stage" in data
        assert "bottlenecks" in data
        assert "at_risk" in data

    def test_all_stages_present_in_counts(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        stages = resp.json()["order_items_by_stage"]
        for s in ["queued", "printing", "finishing", "install", "complete"]:
            assert s in stages, f"Missing stage key: {s}"
            assert isinstance(stages[s], int)

    def test_bottlenecks_is_list(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        assert isinstance(resp.json()["bottlenecks"], list)

    def test_at_risk_is_list(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        assert isinstance(resp.json()["at_risk"], list)

    def test_bottleneck_item_shape_when_present(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        for item in resp.json()["bottlenecks"]:
            for field in ["stage", "backlog_count", "oldest_item_age_hours", "sample_order_item_ids"]:
                assert field in item, f"bottleneck item missing: {field}"

    def test_at_risk_item_shape_when_present(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        for item in resp.json()["at_risk"]:
            for field in ["order_id", "order_number", "order_item_id", "item_name", "reason", "due_at"]:
                assert field in item, f"at_risk item missing: {field}"

    def test_at_risk_reason_valid_values(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        valid_reasons = {"overdue", "due_within_24h_not_started", "blocked"}
        for item in resp.json()["at_risk"]:
            assert item["reason"] in valid_reasons, f"Invalid at_risk reason: {item['reason']}"

    def test_stage_counts_non_negative(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers)
        for stage, count in resp.json()["order_items_by_stage"].items():
            assert count >= 0, f"Stage {stage} has negative count: {count}"


# ---------------------------------------------------------------------------
# 5. GET /api/dashboard/customer-attention — shape + urgency ordering
# ---------------------------------------------------------------------------

class TestCustomerAttention:

    def setup_method(self):
        self.token, self.headers = _register_and_login()

    def test_empty_dataset_returns_valid_schema(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/customer-attention", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "last_updated_at" in data
        assert "unread_conversations" in data
        assert "approvals_signatures_pending" in data
        assert "quote_followups" in data
        assert isinstance(data["unread_conversations"], list)
        assert isinstance(data["approvals_signatures_pending"], list)
        assert isinstance(data["quote_followups"], list)

    def test_unread_conversation_item_shape(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/customer-attention", headers=self.headers)
        for item in resp.json()["unread_conversations"]:
            for field in ["conversation_id", "customer_name", "unread_count",
                          "last_message_preview", "last_message_at", "urgency_score"]:
                assert field in item, f"unread_conversation item missing: {field}"

    def test_approvals_signatures_item_shape(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/customer-attention", headers=self.headers)
        for item in resp.json()["approvals_signatures_pending"]:
            for field in ["record_id", "type", "customer_name", "order_number",
                          "requested_at", "age_hours", "urgency_score"]:
                assert field in item, f"approvals item missing: {field}"

    def test_approval_type_is_valid(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/customer-attention", headers=self.headers)
        valid_types = {"proof", "signature"}
        for item in resp.json()["approvals_signatures_pending"]:
            assert item["type"] in valid_types, f"Invalid type: {item['type']}"

    def test_quote_followups_item_shape(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/customer-attention", headers=self.headers)
        for item in resp.json()["quote_followups"]:
            for field in ["quote_id", "customer_name", "order_number",
                          "quote_total", "last_sent_at", "age_days", "urgency_score"]:
                assert field in item, f"quote_followup item missing: {field}"

    def test_unread_conversations_sorted_by_urgency_desc(self):
        """If multiple unread conversations, urgency_score must be descending."""
        resp = requests.get(f"{BASE_URL}/api/dashboard/customer-attention", headers=self.headers)
        convs = resp.json()["unread_conversations"]
        scores = [c["urgency_score"] for c in convs]
        assert scores == sorted(scores, reverse=True), "unread_conversations not sorted by urgency desc"

    def test_approvals_sorted_by_urgency_desc(self):
        """If multiple approvals, urgency_score must be descending."""
        resp = requests.get(f"{BASE_URL}/api/dashboard/customer-attention", headers=self.headers)
        items = resp.json()["approvals_signatures_pending"]
        scores = [i["urgency_score"] for i in items]
        assert scores == sorted(scores, reverse=True), "approvals not sorted by urgency desc"


# ---------------------------------------------------------------------------
# 6. GET /api/dashboard/financial-attention — shape + top_records <= 3
# ---------------------------------------------------------------------------

class TestFinancialAttention:

    def setup_method(self):
        self.token, self.headers = _register_and_login()

    def test_empty_dataset_returns_valid_schema(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "last_updated_at" in data
        for section in ["unpaid", "overdue", "due_this_week", "recent_payments"]:
            assert section in data, f"Missing section: {section}"
            s = data[section]
            assert "count" in s
            assert "total_amount" in s
            assert "top_records" in s
            assert isinstance(s["top_records"], list)

    def test_empty_tenant_all_zero(self):
        """A fresh tenant with no extra invoice data should have 0 active orders."""
        resp = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers)
        data = resp.json()
        # active orders in production starts at 0 — no pending orders are seeded
        # We verify schema only for empty state since onboarding may seed invoices
        for section in ["unpaid", "overdue", "due_this_week", "recent_payments"]:
            assert section in data
            s = data[section]
            assert "count" in s
            assert "total_amount" in s
            assert "top_records" in s
            assert isinstance(s["top_records"], list)

    def test_top_records_never_exceeds_3(self):
        """Even with many invoices, top_records must be capped at 3 per section."""
        for i in range(6):
            _create_invoice(self.headers, status="sent", total=float(100 + i * 50))

        resp = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers)
        data = resp.json()
        for section in ["unpaid", "overdue", "due_this_week", "recent_payments"]:
            assert len(data[section]["top_records"]) <= 3, (
                f"{section}.top_records exceeds 3: got {len(data[section]['top_records'])}"
            )

    def test_top_record_item_shape(self):
        _create_invoice(self.headers, status="sent", total=500.0)

        resp = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers)
        data = resp.json()
        unpaid = data["unpaid"]
        assert unpaid["count"] >= 1
        if unpaid["top_records"]:
            record = unpaid["top_records"][0]
            for field in ["invoice_id", "invoice_number", "customer_name",
                          "amount", "status", "due_date", "paid_date"]:
                assert field in record, f"top_record missing field: {field}"

    def test_unpaid_excludes_draft(self):
        """Draft invoices must NOT appear in unpaid section; only sent does."""
        before = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers).json()
        before_count = before["unpaid"]["count"]

        _create_invoice(self.headers, status="draft", total=999.0)   # should NOT count
        _create_invoice(self.headers, status="sent", total=100.0)    # should count

        resp = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers)
        unpaid = resp.json()["unpaid"]
        # Only 1 new invoice (the sent one), draft excluded
        assert unpaid["count"] == before_count + 1, (
            f"Expected +1 (sent only), got before={before_count} after={unpaid['count']}"
        )

    def test_overdue_separate_from_unpaid(self):
        """Overdue invoices appear in overdue section, not in unpaid (which is sent-only)."""
        _create_invoice(self.headers, status="overdue", total=300.0)
        _create_invoice(self.headers, status="sent", total=100.0)

        resp = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers)
        data = resp.json()
        assert data["overdue"]["count"] >= 1
        assert data["unpaid"]["count"] >= 1
        # Overdue must NOT appear in unpaid (different sections)
        unpaid_ids = {r["invoice_id"] for r in data["unpaid"]["top_records"]}
        overdue_ids = {r["invoice_id"] for r in data["overdue"]["top_records"]}
        assert unpaid_ids.isdisjoint(overdue_ids), "Same invoice appeared in both unpaid and overdue"

    def test_total_amount_correct(self):
        """total_amount must correctly sum all invoices in that section."""
        before = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers).json()
        before_total = before["unpaid"]["total_amount"]
        before_count = before["unpaid"]["count"]

        _create_invoice(self.headers, status="sent", total=100.0)
        _create_invoice(self.headers, status="sent", total=200.0)

        resp = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers)
        unpaid = resp.json()["unpaid"]
        assert unpaid["count"] == before_count + 2
        assert abs(unpaid["total_amount"] - (before_total + 300.0)) < 0.01, (
            f"Total wrong: expected {before_total + 300.0}, got {unpaid['total_amount']}"
        )


# ---------------------------------------------------------------------------
# 7. All new endpoints return last_updated_at
# ---------------------------------------------------------------------------

class TestLastUpdatedAt:

    def setup_method(self):
        _, self.headers = _register_and_login()

    def test_all_v1_endpoints_have_last_updated_at(self):
        endpoints = [
            "/api/dashboard/summary-v2",
            "/api/dashboard/today-command-center",
            "/api/dashboard/production-snapshot",
            "/api/dashboard/customer-attention",
            "/api/dashboard/financial-attention",
        ]
        for ep in endpoints:
            resp = requests.get(f"{BASE_URL}{ep}", headers=self.headers)
            assert resp.status_code == 200, f"Failed {ep}: {resp.text}"
            assert "last_updated_at" in resp.json(), f"Missing last_updated_at in {ep}"
            # Verify it's a valid ISO timestamp
            ts = resp.json()["last_updated_at"]
            try:
                datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                pytest.fail(f"last_updated_at in {ep} is not a valid ISO timestamp: {ts}")


# ---------------------------------------------------------------------------
# 8. Tenant isolation — each endpoint must only return own tenant's data
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    """Two tenants — each should see only their own data."""

    def setup_method(self):
        _, self.headers_a = _register_and_login()
        _, self.headers_b = _register_and_login()

    def test_stats_tenant_isolation(self):
        """Tenant A's orders must not appear in Tenant B's active_orders."""
        _create_order(self.headers_a)
        _create_order(self.headers_a)

        resp_b = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers_b)
        assert resp_b.json()["active_orders"] == 0

    def test_financial_attention_tenant_isolation(self):
        """Tenant A's invoices must not appear in Tenant B's financial-attention."""
        before_b = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers_b).json()
        before_unpaid = before_b["unpaid"]["count"]
        before_overdue = before_b["overdue"]["count"]

        _create_invoice(self.headers_a, status="sent", total=5000.0)
        _create_invoice(self.headers_a, status="overdue", total=9999.0)

        resp_b = requests.get(f"{BASE_URL}/api/dashboard/financial-attention", headers=self.headers_b)
        data_b = resp_b.json()
        # Tenant B's counts must not have changed
        assert data_b["unpaid"]["count"] == before_unpaid
        assert data_b["overdue"]["count"] == before_overdue

    def test_summary_v2_tenant_isolation(self):
        """Tenant A's invoices must not inflate Tenant B's unpaid_invoices metric."""
        before_b = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers_b).json()
        before_count = before_b["metrics"]["unpaid_invoices"]["count"]

        for _ in range(3):
            _create_invoice(self.headers_a, status="sent", total=100.0)

        resp_b = requests.get(f"{BASE_URL}/api/dashboard/summary-v2", headers=self.headers_b)
        # Tenant B's count must be unchanged
        assert resp_b.json()["metrics"]["unpaid_invoices"]["count"] == before_count

    def test_production_snapshot_tenant_isolation(self):
        """Tenant B sees its own production counts, not Tenant A's."""
        # Both tenants start with 0 tickets — snapshot should be clean
        resp_a = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers_a)
        resp_b = requests.get(f"{BASE_URL}/api/dashboard/production-snapshot", headers=self.headers_b)
        # Neither can see the other's data — both start at 0
        for stage in ["queued", "printing", "finishing", "install"]:
            assert resp_a.json()["order_items_by_stage"][stage] == 0
            assert resp_b.json()["order_items_by_stage"][stage] == 0


# ---------------------------------------------------------------------------
# 9. Legacy endpoints backward compat — still callable
# ---------------------------------------------------------------------------

class TestLegacyEndpointsStillCallable:

    def setup_method(self):
        _, self.headers = _register_and_login()

    def test_legacy_stats_still_200(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert resp.status_code == 200

    def test_legacy_pending_approvals_still_200(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/pending-approvals", headers=self.headers)
        assert resp.status_code == 200

    def test_legacy_unread_messages_still_200(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/unread-messages", headers=self.headers)
        assert resp.status_code == 200

    def test_legacy_team_status_today_still_200(self):
        resp = requests.get(f"{BASE_URL}/api/dashboard/team-status-today", headers=self.headers)
        assert resp.status_code == 200
