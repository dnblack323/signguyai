"""
Iteration 169 — Phase 5 Owner Portal Progress + Financial Transparency
and Phase 4 follow-up Customer/Webstores enhancement.
"""
import os
import re
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://sign-production-hub-1.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
OWNER_EMAIL = "phase5-owner-test@example.com"
OWNER_PASSWORD = "OwnerPass123!"
TEST_WEBSTORE_ID = "fc0bad7e-9040-477e-93b9-a3f0b1a2df90"

PRIVACY_BANNED = ["base_cost", "production_cost", "supplier_cost", "internal_notes", "staff_comments", "markup"]


def _login(email, password):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD)


@pytest.fixture(scope="module")
def owner_token():
    return _login(OWNER_EMAIL, OWNER_PASSWORD)


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# --------- TEST 1 — Customer/Webstores enhancement ---------
class TestCustomerWebstores:
    def test_customer_webstores_endpoint(self, admin_token):
        # find a customer with webstore_owner tag
        r = requests.get(f"{BASE_URL}/api/customers", headers=_auth(admin_token), timeout=30)
        assert r.status_code == 200, r.text
        customers = r.json()
        if isinstance(customers, dict):
            customers = customers.get("customers", customers.get("items", []))
        target = None
        for c in customers:
            tags = c.get("tags") or []
            if "webstore_owner" in tags:
                target = c
                break
        if target is None:
            # fallback to id hint
            for c in customers:
                if str(c.get("id", "")).startswith("a296ce20-1568-4296-855e-cca8e60b21f0"):
                    target = c
                    break
        assert target, "No customer with webstore_owner tag found"
        cid = target["id"]
        r2 = requests.get(f"{BASE_URL}/api/customers/{cid}/webstores", headers=_auth(admin_token), timeout=30)
        assert r2.status_code == 200, r2.text
        body = r2.json()
        for k in ("customer_id", "tags", "as_owner", "as_buyer"):
            assert k in body, f"Missing key {k} in response: {list(body.keys())}"
        assert "webstore_owner" in body["tags"]
        assert isinstance(body["as_owner"], list)
        assert isinstance(body["as_buyer"], list)
        if body["as_owner"]:
            row = body["as_owner"][0]
            for k in ("id", "name", "store_type", "status", "order_count", "gross_sales", "payout_owed", "payout_paid"):
                assert k in row, f"as_owner row missing {k}: {row}"
        # privacy guard
        raw = json.dumps(body).lower()
        for banned in PRIVACY_BANNED + ["margin"]:
            assert banned not in raw, f"Privacy-banned field '{banned}' appears in customer webstores response"


# --------- TEST 2,3,4,5 — Owner progress endpoint ---------
class TestOwnerProgress:
    @pytest.fixture(scope="class")
    def progress(self, owner_token):
        r = requests.get(
            f"{BASE_URL}/api/owner-portal/stores/{TEST_WEBSTORE_ID}/progress",
            headers=_auth(owner_token),
            timeout=30,
        )
        assert r.status_code == 200, r.text
        return r.json()

    def test_structure(self, progress):
        for k in ("store", "current_stage", "stages", "next_blocker", "required_actions", "finance", "payout_history", "privacy_note", "as_of"):
            assert k in progress, f"Missing top-level key {k}"
        store = progress["store"]
        for k in ("id", "name", "store_type", "status"):
            assert k in store
        cs = progress["current_stage"]
        for k in ("key", "label", "index", "total"):
            assert k in cs
        assert cs["total"] == 15
        stages = progress["stages"]
        assert isinstance(stages, list) and len(stages) == 15
        for s in stages:
            assert "key" in s and "label" in s and "status" in s
            assert s["status"] in ("done", "active", "todo")
        ra = progress["required_actions"]
        assert isinstance(ra, list) and len(ra) == 6
        keys_present = {a["key"] for a in ra}
        for k in ("complete_questionnaire", "upload_artwork", "review_preview", "approve_store", "confirm_fulfillment", "stripe_onboarding"):
            assert k in keys_present, f"Missing required action {k}"
        for a in ra:
            for k in ("key", "label", "status", "reason", "cta_url"):
                assert k in a, f"Required action missing {k}: {a}"
        fin = progress["finance"]
        for k in ("gross_sales", "total_orders", "donations_collected", "profit_allocation", "fundraiser_total_raised", "payout_owed", "payout_paid", "net_pending_payout", "formula"):
            assert k in fin, f"finance missing {k}"
        assert isinstance(progress["payout_history"], list)
        assert isinstance(progress["privacy_note"], str)

    def test_privacy_guard(self, progress):
        # Convert with privacy_note temporarily removed to allow 'margin' in note
        clone = dict(progress)
        privacy_note = clone.pop("privacy_note", "")
        raw = json.dumps(clone).lower()
        for banned in PRIVACY_BANNED:
            assert banned not in raw, f"Banned substring '{banned}' found in owner progress payload"
        # 'margin' allowed only inside privacy_note
        assert "margin" not in raw, "'margin' should not appear outside privacy_note"

    def test_lifecycle_staging(self, progress):
        cs_key = progress["current_stage"]["key"]
        assert cs_key in ("questionnaire_submitted", "waiting_artwork", "store_being_built"), f"Unexpected current_stage.key={cs_key}"
        by_key = {s["key"]: s for s in progress["stages"]}
        assert "setup_received" in by_key, "setup_received stage missing"
        assert by_key["setup_received"]["status"] == "done", f"setup_received expected done, got {by_key['setup_received']['status']}"
        assert "orders_coming_in" in by_key, "orders_coming_in stage missing"

    def test_required_actions_wired(self, progress):
        ra = {a["key"]: a for a in progress["required_actions"]}
        assert ra["complete_questionnaire"]["status"] == "todo"
        assert ra["upload_artwork"]["status"] == "todo"
        assert ra["review_preview"]["status"] == "done"
        assert ra["approve_store"]["status"] == "done"
        assert ra["confirm_fulfillment"]["status"] == "todo"
        assert ra["stripe_onboarding"]["status"] == "todo"
        for k, a in ra.items():
            assert isinstance(a.get("reason"), str) and len(a["reason"]) > 0, f"{k} has empty reason"


# --------- TEST 6 — 403 for non-owner ---------
def test_admin_blocked_from_owner_progress(admin_token):
    r = requests.get(
        f"{BASE_URL}/api/owner-portal/stores/{TEST_WEBSTORE_ID}/progress",
        headers=_auth(admin_token),
        timeout=30,
    )
    assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"


# --------- TEST 7 — 404 for non-owned ---------
def test_owner_404_for_unknown_store(owner_token):
    r = requests.get(
        f"{BASE_URL}/api/owner-portal/stores/00000000-0000-0000-0000-000000000000/progress",
        headers=_auth(owner_token),
        timeout=30,
    )
    assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"


# --------- TEST 9 — Cross-check finance ---------
def test_finance_matches_admin_analytics(admin_token, owner_token):
    r = requests.get(
        f"{BASE_URL}/api/owner-portal/stores/{TEST_WEBSTORE_ID}/progress",
        headers=_auth(owner_token),
        timeout=30,
    )
    assert r.status_code == 200
    progress_gross = r.json()["finance"]["gross_sales"]

    a = requests.get(
        f"{BASE_URL}/api/webstores/v2/{TEST_WEBSTORE_ID}/analytics",
        headers=_auth(admin_token),
        timeout=30,
    )
    assert a.status_code == 200, a.text
    analytics = a.json()
    summary = analytics.get("summary", {})
    total_sales = (
        summary.get("total_sales")
        or summary.get("total_revenue")
        or analytics.get("total_sales")
        or analytics.get("gross_sales")
    )
    assert total_sales is not None, f"No total_sales/total_revenue in analytics: {analytics}"
    # Compare gross from progress vs analytics revenue — they should match (same source-of-truth)
    assert float(progress_gross) == float(total_sales), (
        f"FINANCE DRIFT: progress gross={progress_gross} vs analytics total_revenue={total_sales} "
        f"(progress orders={r.json()['finance']['total_orders']}, analytics orders={summary.get('total_orders')})"
    )
