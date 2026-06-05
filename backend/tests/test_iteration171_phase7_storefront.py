"""
Phase 7 Backend Tests — Public Storefront Polish + Webstores Audit Trail
Tests: status-aware storefront, admin preview, products gate bypass, webstore_stage_events
Store under test: fc0bad7e-9040-477e-93b9-a3f0b1a2df90 (Preview Storefront QA)
"""
import pytest
import requests
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://sign-shop-checkout.preview.emergentagent.com").rstrip("/")
STORE_ID = "fc0bad7e-9040-477e-93b9-a3f0b1a2df90"
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "signguy_ai"


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token."""
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "thesigntistslab@gmail.com", "password": "password123"},
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    token = resp.json().get("access_token")
    assert token, "No access_token in login response"
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_stage_events(webstore_id=STORE_ID):
    """Read stage events directly from MongoDB for this webstore."""
    async def _fetch():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        docs = await db.webstore_stage_events.find(
            {"webstore_id": webstore_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        client.close()
        return docs

    return asyncio.get_event_loop().run_until_complete(_fetch())


# ─── Tests: GET /api/storefront/{id} — Status page payload ──────────────────

class TestStorefrontStatusPage:
    """Test that non-active stores return _status_page:true with limited payload."""

    def test_pending_store_returns_status_page(self):
        """Non-active store (pending) → _status_page:true in response."""
        resp = requests.get(f"{BASE_URL}/api/storefront/{STORE_ID}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("_status_page") is True, f"Expected _status_page:true, got: {data}"
        assert data.get("status") == "pending"

    def test_status_page_has_limited_fields(self):
        """Status page response must expose only safe public fields."""
        resp = requests.get(f"{BASE_URL}/api/storefront/{STORE_ID}")
        data = resp.json()
        # Required safe fields
        assert "id" in data
        assert "name" in data
        assert "status" in data
        assert "branding" in data
        # Must NOT expose internal fields
        assert "tenant_id" not in data
        assert "payout_owed" not in data
        assert "total_profit" not in data

    def test_status_page_branding_present(self):
        """Status page must return branding object with primary_color."""
        resp = requests.get(f"{BASE_URL}/api/storefront/{STORE_ID}")
        data = resp.json()
        branding = data.get("branding", {})
        assert isinstance(branding, dict)
        assert "primary_color" in branding

    def test_disabled_store_returns_status_page(self, admin_headers):
        """Change store to disabled → still returns _status_page:true."""
        # Set to disabled
        put_resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "disabled"},
        )
        assert put_resp.status_code == 200, f"PUT failed: {put_resp.text}"
        assert put_resp.json().get("status") == "disabled"

        # Verify status page for disabled store
        resp = requests.get(f"{BASE_URL}/api/storefront/{STORE_ID}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("_status_page") is True
        assert data.get("status") == "disabled"

        # Restore to pending
        restore = requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "pending"},
        )
        assert restore.status_code == 200
        assert restore.json().get("status") == "pending"


# ─── Tests: GET /api/storefront/{id}/preview ─────────────────────────────────

class TestStorefrontPreview:
    """Admin preview endpoint tests."""

    def test_preview_without_auth_401(self):
        """Preview endpoint requires auth — returns 401 without token."""
        resp = requests.get(f"{BASE_URL}/api/storefront/{STORE_ID}/preview")
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_preview_with_admin_auth_200(self, admin_headers):
        """Preview endpoint with admin JWT → 200 + is_admin_preview:true."""
        resp = requests.get(
            f"{BASE_URL}/api/storefront/{STORE_ID}/preview",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get("is_admin_preview") is True, f"Expected is_admin_preview:true, got: {data}"

    def test_preview_response_has_store_fields(self, admin_headers):
        """Preview returns full sanitized store payload (name, status, branding, checkout)."""
        resp = requests.get(
            f"{BASE_URL}/api/storefront/{STORE_ID}/preview",
            headers=admin_headers,
        )
        data = resp.json()
        assert "name" in data
        assert "status" in data
        assert "branding" in data
        assert "checkout_enabled" in data
        assert "checkout_status" in data

    def test_preview_response_hides_internal_fields(self, admin_headers):
        """Preview endpoint must not expose tenant_id / payout data."""
        resp = requests.get(
            f"{BASE_URL}/api/storefront/{STORE_ID}/preview",
            headers=admin_headers,
        )
        data = resp.json()
        assert "tenant_id" not in data
        assert "payout_owed" not in data
        assert "total_profit" not in data

    def test_preview_logs_admin_preview_accessed_event(self, admin_headers):
        """Calling preview logs admin_preview_accessed in webstore_stage_events."""
        events_before = get_stage_events()
        preview_count_before = sum(
            1 for e in events_before if e.get("event_type") == "admin_preview_accessed"
        )

        requests.get(
            f"{BASE_URL}/api/storefront/{STORE_ID}/preview",
            headers=admin_headers,
        )

        events_after = get_stage_events()
        preview_count_after = sum(
            1 for e in events_after if e.get("event_type") == "admin_preview_accessed"
        )
        assert preview_count_after > preview_count_before, (
            "Expected a new admin_preview_accessed event after calling preview endpoint"
        )


# ─── Tests: GET /api/storefront/{id}/products ─────────────────────────────────

class TestStorefrontProducts:
    """Products endpoint tests — status gate + admin_preview bypass."""

    def test_products_pending_store_404(self):
        """Products endpoint returns 404 when store is pending (not active)."""
        resp = requests.get(f"{BASE_URL}/api/storefront/{STORE_ID}/products")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_products_admin_preview_bypasses_gate(self):
        """?admin_preview=true bypasses active-status gate and returns products."""
        resp = requests.get(
            f"{BASE_URL}/api/storefront/{STORE_ID}/products?admin_preview=true"
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert isinstance(data, list), "Expected a list of products"

    def test_products_admin_preview_returns_valid_structure(self):
        """Products returned via admin_preview=true have proper structure."""
        resp = requests.get(
            f"{BASE_URL}/api/storefront/{STORE_ID}/products?admin_preview=true"
        )
        data = resp.json()
        if data:  # Only if there are products
            first = data[0]
            assert "product_id" in first or "id" in first, "Product must have id/product_id"
            assert "product" in first, "Product must have nested product object"
            assert "effective_price" in first, "Product must have effective_price"

    def test_products_disabled_store_404(self, admin_headers):
        """Products endpoint returns 404 when store is disabled."""
        # Temporarily disable
        requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "disabled"},
        )
        resp = requests.get(f"{BASE_URL}/api/storefront/{STORE_ID}/products")
        assert resp.status_code == 404

        # Restore
        requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "pending"},
        )


# ─── Tests: webstore_stage_events audit trail ─────────────────────────────────

class TestStageEvents:
    """webstore_stage_events collection receives audit events on key operations."""

    def test_status_changed_event_on_put(self, admin_headers):
        """PUT /api/webstores/v2/{id} with status change → logs status_changed event."""
        events_before = get_stage_events()
        sc_count_before = sum(
            1 for e in events_before if e.get("event_type") == "status_changed"
        )

        # Change status pending → disabled
        resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "disabled"},
        )
        assert resp.status_code == 200

        events_after = get_stage_events()
        sc_count_after = sum(
            1 for e in events_after if e.get("event_type") == "status_changed"
        )
        assert sc_count_after > sc_count_before, "Expected new status_changed event"

        # Restore
        requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "pending"},
        )

    def test_status_changed_event_has_required_fields(self, admin_headers):
        """status_changed event must have webstore_id, actor_email, event_type."""
        events = get_stage_events()
        sc_events = [e for e in events if e.get("event_type") == "status_changed"]
        assert sc_events, "No status_changed events found"
        ev = sc_events[0]
        assert ev.get("webstore_id") == STORE_ID
        assert ev.get("event_type") == "status_changed"
        assert ev.get("actor_email"), "actor_email must be set"
        assert ev.get("actor_id"), "actor_id must be set"
        assert ev.get("created_at"), "created_at must be set"

    def test_stage_stamped_event_on_patch_admin_progress(self, admin_headers):
        """PATCH /api/webstores/v2/{id}/admin-progress → logs stage_stamped event."""
        events_before = get_stage_events()
        ss_count_before = sum(
            1 for e in events_before if e.get("event_type") == "stage_stamped"
        )

        # Apply a stamp
        resp = requests.patch(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}/admin-progress",
            headers=admin_headers,
            json={"mark_preview_ready": True},
        )
        assert resp.status_code == 200

        events_after = get_stage_events()
        ss_count_after = sum(
            1 for e in events_after if e.get("event_type") == "stage_stamped"
        )
        assert ss_count_after > ss_count_before, "Expected new stage_stamped event"

    def test_stage_stamped_event_has_stamps_applied(self, admin_headers):
        """stage_stamped event must include stamps_applied list."""
        events = get_stage_events()
        ss_events = [e for e in events if e.get("event_type") == "stage_stamped"]
        assert ss_events, "No stage_stamped events found"
        ev = ss_events[0]
        assert ev.get("stamps_applied"), "stamps_applied must be set and non-empty"
        assert isinstance(ev.get("stamps_applied"), list)

    def test_admin_preview_accessed_event_present(self):
        """webstore_stage_events has admin_preview_accessed records."""
        events = get_stage_events()
        ap_events = [e for e in events if e.get("event_type") == "admin_preview_accessed"]
        assert ap_events, "Expected at least one admin_preview_accessed event"
        ev = ap_events[0]
        assert ev.get("actor_email") == "thesigntistslab@gmail.com"

    def test_stage_events_collection_total_not_zero(self):
        """webstore_stage_events collection has at least one record for this webstore."""
        events = get_stage_events()
        assert len(events) > 0, "webstore_stage_events must have at least one event"


# ─── Tests: Webstore V2 GET after status changes ──────────────────────────────

class TestWebstoreV2AfterStatusChange:
    """GET /api/webstores/v2/{id} should work for all status values."""

    def test_get_webstore_with_pending_status(self, admin_headers):
        """GET webstore detail works when status=pending."""
        resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"500 or error: {resp.text}"
        data = resp.json()
        assert data.get("status") in ("pending", "disabled", "active", "completed", "closed")

    def test_get_webstore_with_completed_status_no_500(self, admin_headers):
        """GET webstore/v2/{id} must NOT return 500 after status set to completed."""
        # Set to completed
        put_resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "completed"},
        )
        assert put_resp.status_code == 200, f"PUT to completed failed: {put_resp.text}"

        # GET should not 500
        get_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
        )
        assert get_resp.status_code == 200, f"GET returned {get_resp.status_code}: {get_resp.text}"
        assert get_resp.json().get("status") == "completed"

        # Restore
        requests.put(
            f"{BASE_URL}/api/webstores/v2/{STORE_ID}",
            headers=admin_headers,
            json={"status": "pending"},
        )
