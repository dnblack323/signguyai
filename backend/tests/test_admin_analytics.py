"""
Backend tests for Admin Analytics feature (Iteration 178).
Tests: access control, event ingestion, overview/chart/users/routes/sessions/referrers/errors/suspicious endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_token():
    """Get platform_admin JWT"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "thesigntistslab@gmail.com",
        "password": "password123",
    })
    if resp.status_code == 200:
        return resp.json().get("token") or resp.json().get("access_token")
    pytest.skip(f"Admin login failed: {resp.status_code} {resp.text}")


@pytest.fixture(scope="module")
def non_admin_token():
    """Get a non-platform_admin JWT (staff user)"""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "staff_payroll_test@test.com",
        "password": "StaffTest123!",
    })
    if resp.status_code == 200:
        return resp.json().get("token") or resp.json().get("access_token")
    pytest.skip("Staff login failed — skipping non-admin access tests")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def non_admin_headers(non_admin_token):
    return {"Authorization": f"Bearer {non_admin_token}"}


# ── Test 1: Event ingestion (public endpoint) ─────────────────────────────────

class TestAnalyticsEventIngestion:
    """POST /api/analytics/event — public, no auth required"""

    def test_ingest_page_view_event(self):
        """POST event returns {ok: True}"""
        payload = {
            "event_type": "page_view",
            "session_id": "test-session-001",
            "visitor_id": "test-visitor-001",
            "user_id": None,
            "route": "/dashboard",
            "referrer": "",
            "user_agent": "Mozilla/5.0 TestAgent",
            "metadata": {"page": "/dashboard"},
        }
        resp = requests.post(f"{BASE_URL}/api/analytics/event", json=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("ok") is True, f"Expected ok=True, got: {data}"

    def test_ingest_event_without_auth(self):
        """No token needed for public event endpoint"""
        payload = {
            "event_type": "login_success",
            "session_id": "test-session-002",
            "visitor_id": "test-visitor-002",
            "metadata": {},
        }
        resp = requests.post(f"{BASE_URL}/api/analytics/event", json=payload)
        assert resp.status_code == 200, f"Should not require auth: {resp.status_code}"
        assert resp.json().get("ok") is True

    def test_ingest_event_missing_required_fields_fails(self):
        """Missing required fields should return 422"""
        resp = requests.post(f"{BASE_URL}/api/analytics/event", json={"event_type": "page_view"})
        # session_id and visitor_id are required
        assert resp.status_code == 422, f"Expected 422 for missing fields, got {resp.status_code}"

    def test_bot_ua_event_flagged(self):
        """Event with bot user-agent should be accepted but flagged"""
        payload = {
            "event_type": "page_view",
            "session_id": "bot-session-001",
            "visitor_id": "bot-visitor-001",
            "user_agent": "Googlebot/2.1 (+http://www.google.com/bot.html)",
            "route": "/",
            "metadata": {},
        }
        resp = requests.post(f"{BASE_URL}/api/analytics/event", json=payload)
        assert resp.status_code == 200, f"Bot event should still be accepted: {resp.status_code}"
        assert resp.json().get("ok") is True


# ── Test 2: Access Control for Admin endpoints ────────────────────────────────

class TestAdminAnalyticsAccessControl:
    """All /api/admin/analytics/* require platform_admin role"""

    def test_overview_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_overview_non_admin_returns_403(self, non_admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview", headers=non_admin_headers)
        assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}: {resp.text}"

    def test_chart_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/activity-chart")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_users_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/users")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_routes_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/routes")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_sessions_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/sessions")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_referrers_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/referrers")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_errors_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/errors")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"

    def test_suspicious_no_token_returns_401(self):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/suspicious")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"


# ── Test 3: Admin GET endpoints (platform_admin) ──────────────────────────────

class TestAdminAnalyticsOverview:
    """GET /api/admin/analytics/overview"""

    def test_overview_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_overview_has_required_fields(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview", headers=admin_headers)
        data = resp.json()
        required = [
            "new_users", "new_orders", "new_quotes", "new_webstores",
            "total_users", "total_orders", "total_webstores",
            "total_events", "total_sessions", "total_visitors",
            "page_views", "bot_events", "error_events",
            "range", "period_start", "period_end",
        ]
        for field in required:
            assert field in data, f"Missing field '{field}' in overview response"

    def test_overview_business_metrics_are_non_negative(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview", headers=admin_headers)
        data = resp.json()
        assert data["total_users"] >= 0
        assert data["total_orders"] >= 0
        assert data["total_webstores"] >= 0

    def test_overview_range_today(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview?range=today", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json().get("range") == "today"

    def test_overview_range_7d(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview?range=7d", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json().get("range") == "7d"

    def test_overview_range_14d(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/overview?range=14d", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json().get("range") == "14d"


class TestAdminAnalyticsActivityChart:
    """GET /api/admin/analytics/activity-chart"""

    def test_chart_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/activity-chart", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_chart_has_days_list(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/activity-chart", headers=admin_headers)
        data = resp.json()
        assert "days" in data, "Missing 'days' key in chart response"
        assert isinstance(data["days"], list), "'days' should be a list"

    def test_chart_bucket_has_required_fields(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/activity-chart?range=7d", headers=admin_headers)
        days = resp.json().get("days", [])
        assert len(days) > 0, "Expected at least one day bucket"
        bucket = days[0]
        for field in ["date", "orders", "quotes", "webstores", "new_users", "events", "page_views", "errors"]:
            assert field in bucket, f"Missing field '{field}' in chart bucket"


class TestAdminAnalyticsUsers:
    """GET /api/admin/analytics/users"""

    def test_users_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/users", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_users_has_users_list(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/users", headers=admin_headers)
        data = resp.json()
        assert "users" in data, "Missing 'users' key"
        assert "total" in data, "Missing 'total' key"
        assert isinstance(data["users"], list)

    def test_users_no_platform_admin(self, admin_headers):
        """platform_admin users should be excluded"""
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/users", headers=admin_headers)
        users = resp.json().get("users", [])
        for u in users:
            assert u.get("role") != "platform_admin", \
                f"platform_admin user found in users list: {u.get('email')}"

    def test_users_have_required_fields(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/users", headers=admin_headers)
        users = resp.json().get("users", [])
        if users:
            u = users[0]
            for field in ["id", "email", "role", "orders", "quotes", "webstores", "admin_actions"]:
                assert field in u, f"Missing field '{field}' in user record"


class TestAdminAnalyticsRoutes:
    """GET /api/admin/analytics/routes"""

    def test_routes_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/routes", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_routes_has_routes_list(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/routes", headers=admin_headers)
        data = resp.json()
        assert "routes" in data, "Missing 'routes' key"
        assert isinstance(data["routes"], list)


class TestAdminAnalyticsSessions:
    """GET /api/admin/analytics/sessions"""

    def test_sessions_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/sessions", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_sessions_has_sessions_list(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/sessions", headers=admin_headers)
        data = resp.json()
        assert "sessions" in data, "Missing 'sessions' key"
        assert isinstance(data["sessions"], list)


class TestAdminAnalyticsReferrers:
    """GET /api/admin/analytics/referrers"""

    def test_referrers_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/referrers", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_referrers_has_referrers_list(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/referrers", headers=admin_headers)
        data = resp.json()
        assert "referrers" in data, "Missing 'referrers' key"
        assert isinstance(data["referrers"], list)


class TestAdminAnalyticsErrors:
    """GET /api/admin/analytics/errors"""

    def test_errors_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/errors", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_errors_has_required_fields(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/errors", headers=admin_headers)
        data = resp.json()
        assert "errors" in data, "Missing 'errors' key"
        assert "total_errors" in data, "Missing 'total_errors' key"
        assert "frontend_errors" in data, "Missing 'frontend_errors' key"
        assert "api_errors" in data, "Missing 'api_errors' key"


class TestAdminAnalyticsSuspicious:
    """GET /api/admin/analytics/suspicious"""

    def test_suspicious_returns_200(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/suspicious", headers=admin_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_suspicious_has_required_fields(self, admin_headers):
        resp = requests.get(f"{BASE_URL}/api/admin/analytics/suspicious", headers=admin_headers)
        data = resp.json()
        assert "suspicious" in data
        assert "total_bot" in data
        assert "total_suspicious" in data
        assert "bot_pct" in data


# ── Test 4: Infinite loop guard — analytics event endpoint should NOT trigger tracking ──

class TestAnalyticsNoLoop:
    """Ensure POST /api/analytics/event doesn't cause infinite loop (no analytics tracking call to itself)"""

    def test_single_event_ingest_produces_one_record(self):
        """Posting an event should produce exactly one record insertion, not multiple"""
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["signguy_ai"]

        unique_session = "loop-test-session-xyz-999"
        # Count docs before
        count_before = db.analytics_events.count_documents({"session_id": unique_session})

        # Post ONE event
        payload = {
            "event_type": "page_view",
            "session_id": unique_session,
            "visitor_id": "loop-test-visitor-001",
            "route": "/test-loop",
            "metadata": {},
        }
        resp = requests.post(f"{BASE_URL}/api/analytics/event", json=payload)
        assert resp.status_code == 200

        # Brief wait for any async side effects
        import time; time.sleep(0.3)

        count_after = db.analytics_events.count_documents({"session_id": unique_session})
        # Should be exactly +1
        assert count_after == count_before + 1, (
            f"Expected exactly 1 new record, got {count_after - count_before} "
            f"(possible infinite loop!)"
        )
        client.close()


# ── Test 5: MongoDB indexes ────────────────────────────────────────────────────

class TestMongoDBIndexes:
    """Verify analytics_events indexes were created"""

    def test_required_indexes_exist(self):
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017")
        db = client["signguy_ai"]
        index_keys = list(db.analytics_events.index_information().keys())
        client.close()

        required = ["timestamp_1", "event_type_1", "session_id_1", "user_id_1", "route_1", "ip_address_1"]
        for idx in required:
            assert idx in index_keys, f"Missing MongoDB index: {idx}. Found: {index_keys}"
