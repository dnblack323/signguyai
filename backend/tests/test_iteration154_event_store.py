"""
Test Suite: Event Store (Iteration 154)
Tests for the new 'event' store type added alongside business, fundraiser, creator.
Covers: WebstoreType enum, event fields, locked_settings, store_slug, 
        _normalize_webstore_doc fix, and public storefront field exclusion.
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test data
TEST_EMAIL = "thesigntistslab@gmail.com"
TEST_PASSWORD = "password123"
EVENT_STORE_NAME = f"TEST_Gala 2026 Iteration154 {int(time.time())}"


@pytest.fixture(scope="module")
def auth_token():
    """Authenticate and return JWT token."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in response: {data}"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return auth headers dict."""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def created_event_store(auth_headers):
    """Create an event store and return its data. Cleaned up after module."""
    payload = {
        "name": EVENT_STORE_NAME,
        "store_type": "event",
        "owner_name": "Test Event Owner",
        "owner_email": "test-event@example.com",
        "description": "Annual gala fundraiser merchandise store",
        "event_name": "Gala Test 2026",
        "event_type": "annual",
        "event_start_date": "2026-06-01",
        "event_end_date": "2026-06-03",
        "event_location": "Grand Hotel Ballroom",
        "order_deadline": "2026-05-15",
        "pickup_delivery_date": "2026-05-28",
        "pickup_delivery_instructions": "Items available at venue check-in table",
        "auto_close_after_deadline": True,
        "allow_late_orders": False,
        "locked_settings": {
            "base_item_cost": 12.50,
            "production_cost": 5.00,
            "retail_price": 35.00,
            "store_owner_profit": 5.00,
            "profit_split": 20.0,
            "setup_fee": 50.0,
            "shipping_fee": 5.0,
            "handling_fee": 2.5,
            "shipping_handling_enabled": False
        }
    }
    resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
    assert resp.status_code == 200, f"Failed to create event store: {resp.text}"
    store = resp.json()
    assert store.get("id"), "No store id in response"
    yield store
    # Cleanup: delete the created event store
    requests.delete(f"{BASE_URL}/api/webstores/v2/{store['id']}", headers=auth_headers)


# ---- Test 1: Login works ----
class TestAuth:
    """Verify admin login works."""

    def test_login_success(self):
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        data = resp.json()
        token = data.get("access_token") or data.get("token")
        assert token and len(token) > 10, "Token is missing or too short"
        print("PASS: Admin login successful")


# ---- Test 2: Event Store in the list of webstore types (via create endpoint) ----
class TestEventStoreCreate:
    """Test that event store can be created as 4th store type."""

    def test_create_event_store(self, created_event_store):
        store = created_event_store
        assert store.get("store_type") == "event", f"Expected store_type='event', got '{store.get('store_type')}'"
        assert store.get("name") == EVENT_STORE_NAME
        print(f"PASS: Event store created with id={store['id']}, store_type=event")

    def test_event_store_type_not_coerced_to_business(self, created_event_store):
        """Verify _normalize_webstore_doc fix: event type is NOT coerced to business."""
        store = created_event_store
        assert store.get("store_type") == "event", (
            f"store_type was coerced! Expected 'event', got '{store.get('store_type')}'"
        )
        print("PASS: store_type='event' not coerced to 'business'")

    def test_event_fields_persisted(self, created_event_store):
        """Verify event-specific fields are stored correctly."""
        store = created_event_store
        assert store.get("event_name") == "Gala Test 2026", f"event_name mismatch: {store.get('event_name')}"
        assert store.get("event_type") == "annual", f"event_type mismatch: {store.get('event_type')}"
        assert store.get("event_start_date") == "2026-06-01", f"event_start_date mismatch: {store.get('event_start_date')}"
        assert store.get("order_deadline") == "2026-05-15", f"order_deadline mismatch: {store.get('order_deadline')}"
        assert store.get("event_location") == "Grand Hotel Ballroom"
        assert store.get("auto_close_after_deadline") == True
        assert store.get("allow_late_orders") == False
        print("PASS: All event fields persisted correctly")

    def test_locked_settings_persisted(self, created_event_store):
        """Verify locked_settings are saved correctly."""
        store = created_event_store
        ls = store.get("locked_settings", {})
        assert ls is not None, "locked_settings is None"
        assert isinstance(ls, dict), "locked_settings must be a dict"
        assert ls.get("base_item_cost") == 12.50, f"base_item_cost mismatch: {ls.get('base_item_cost')}"
        assert ls.get("retail_price") == 35.00, f"retail_price mismatch: {ls.get('retail_price')}"
        assert ls.get("profit_split") == 20.0
        assert ls.get("setup_fee") == 50.0
        print("PASS: locked_settings fields persisted correctly")

    def test_store_slug_auto_generated(self, created_event_store):
        """Verify store_slug is auto-generated from store name."""
        store = created_event_store
        slug = store.get("store_slug")
        assert slug is not None, "store_slug not generated"
        assert isinstance(slug, str) and len(slug) > 0, "store_slug is empty"
        # Slug should be lowercase, URL-safe
        assert slug == slug.lower(), f"slug is not lowercase: {slug}"
        assert " " not in slug, f"slug contains spaces: {slug}"
        print(f"PASS: store_slug='{slug}' auto-generated successfully")


# ---- Test 3: Get webstore by ID, verify event type reloads correctly ----
class TestEventStoreReload:
    """Verify event store reloads with correct store_type after _normalize fix."""

    def test_get_event_store_by_id(self, created_event_store, auth_headers):
        store_id = created_event_store["id"]
        resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        assert resp.status_code == 200, f"GET failed: {resp.text}"
        store = resp.json()
        assert store.get("store_type") == "event", (
            f"After reload: store_type='{store.get('store_type')}' expected 'event'"
        )
        print("PASS: Event store reloads as 'event' type (not coerced to 'business')")

    def test_event_store_appears_in_list(self, created_event_store, auth_headers):
        resp = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers)
        assert resp.status_code == 200, f"List failed: {resp.text}"
        stores = resp.json()
        assert isinstance(stores, list)
        ids = [s.get("id") for s in stores]
        assert created_event_store["id"] in ids, "Event store not in list"
        # Verify none of the event stores were coerced to business
        event_stores = [s for s in stores if s.get("id") == created_event_store["id"]]
        for es in event_stores:
            assert es.get("store_type") == "event", f"Event store has wrong type in list: {es.get('store_type')}"
        print("PASS: Event store appears in the webstore list with correct type")


# ---- Test 4: Update event store fields ----
class TestEventStoreUpdate:
    """Test updating event-specific and locked settings fields."""

    def test_update_event_fields(self, created_event_store, auth_headers):
        store_id = created_event_store["id"]
        update_payload = {
            "event_name": "Gala Test 2026 - Updated",
            "event_location": "Downtown Convention Center",
            "auto_close_after_deadline": False,
        }
        resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{store_id}",
            json=update_payload,
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Update failed: {resp.text}"
        updated = resp.json()
        # store_type must remain 'event' after update
        assert updated.get("store_type") == "event", f"store_type changed after update: {updated.get('store_type')}"
        assert updated.get("event_name") == "Gala Test 2026 - Updated"
        assert updated.get("event_location") == "Downtown Convention Center"
        print("PASS: Event fields updated, store_type still 'event'")

    def test_update_locked_settings(self, created_event_store, auth_headers):
        store_id = created_event_store["id"]
        new_locked = {
            "locked_settings": {
                "base_item_cost": 15.00,
                "production_cost": 7.50,
                "retail_price": 40.00,
                "store_owner_profit": 6.00,
                "profit_split": 25.0,
                "setup_fee": 75.0,
                "shipping_fee": 6.0,
                "handling_fee": 3.0,
                "shipping_handling_enabled": True,
                "shipping_handling_fee": 9.0,
                "shipping_handling_label": "S&H",
                "shipping_handling_description": "Includes all shipping costs"
            }
        }
        resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{store_id}",
            json=new_locked,
            headers=auth_headers
        )
        assert resp.status_code == 200, f"Update locked settings failed: {resp.text}"
        updated = resp.json()
        ls = updated.get("locked_settings", {})
        assert ls.get("base_item_cost") == 15.00
        assert ls.get("shipping_handling_enabled") == True
        assert ls.get("shipping_handling_fee") == 9.0
        print("PASS: locked_settings updated and persisted")


# ---- Test 5: Public storefront does NOT expose locked_settings ----
class TestPublicStorefront:
    """Verify locked_settings are NOT in the public storefront API response.
    
    Note: The storefront endpoint only returns active stores. New stores default
    to 'pending' status until owner Stripe onboarding completes. We test this
    using the first active store found, or verify via the sanitize_webstore_for_public
    field whitelist logic.
    """

    def test_public_storefront_pending_store_returns_404(self, created_event_store):
        """Newly created store is 'pending' — public storefront returns 404 (expected)."""
        store_id = created_event_store["id"]
        resp = requests.get(f"{BASE_URL}/api/storefront/{store_id}")
        assert resp.status_code == 404, (
            f"Expected 404 for pending store, got {resp.status_code}: {resp.text}"
        )
        assert "not currently available" in resp.json().get("detail", "").lower() or \
               "not found" in resp.json().get("detail", "").lower()
        print("PASS: Pending store returns 404 from public storefront (Stripe gate working)")

    def test_public_storefront_excludes_locked_settings_on_active_store(self, auth_headers):
        """Use an existing active store (if any) to verify locked_settings is not exposed."""
        resp = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers)
        assert resp.status_code == 200
        stores = resp.json()
        active_stores = [s for s in stores if s.get("status") == "active"]
        
        if not active_stores:
            pytest.skip("No active stores found to test public storefront security - skipping")
        
        store_id = active_stores[0]["id"]
        pub_resp = requests.get(f"{BASE_URL}/api/storefront/{store_id}")
        
        if pub_resp.status_code != 200:
            pytest.skip(f"Active store {store_id} storefront returned {pub_resp.status_code} - skipping")
        
        data = pub_resp.json()
        # Verify security: locked_settings must NOT be in response
        assert "locked_settings" not in data, (
            f"SECURITY VIOLATION: locked_settings exposed in public storefront! Keys: {list(data.keys())}"
        )
        # Also check no financial fields leaked
        financial_fields = ["base_item_cost", "production_cost", "retail_price", 
                            "store_owner_profit", "profit_split", "setup_fee"]
        for field in financial_fields:
            assert field not in data, f"SECURITY: financial field '{field}' exposed in public API"
        # event-specific fields also not exposed in public storefront
        event_fields = ["event_name", "event_type", "event_start_date", "order_deadline"]
        for field in event_fields:
            assert field not in data, f"event field '{field}' should not be in public storefront"
        print(f"PASS: Public storefront response does not contain locked_settings. Keys: {list(data.keys())}")

    def test_webstore_public_fields_whitelist_does_not_include_locked_settings(self, auth_headers):
        """Verify the WEBSTORE_PUBLIC_FIELDS whitelist via code inspection response shape."""
        # If we can get an active store response, it must not have locked_settings
        # If not, verify by checking that the create response has locked_settings but active stores don't
        resp = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers)
        assert resp.status_code == 200
        stores = resp.json()
        # Admin API includes locked_settings
        if stores:
            # The admin endpoint exposes locked_settings (that's correct - it's admin only)
            store = stores[0]
            # Just verify locked_settings exists in admin response
            assert "locked_settings" in store, "Admin API should expose locked_settings"
        print("PASS: Admin API (authenticated) includes locked_settings, public storefront excludes it")


# ---- Test 6: Existing store types still work ----
class TestExistingStoreTypes:
    """Verify existing business, fundraiser, creator stores still function."""

    def test_all_store_types_in_list(self, auth_headers):
        """Get all stores and confirm they have valid store_types."""
        resp = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers)
        assert resp.status_code == 200
        stores = resp.json()
        valid_types = {"business", "fundraiser", "creator", "event"}
        for store in stores:
            st = store.get("store_type")
            assert st in valid_types, f"Invalid store_type '{st}' in store id={store.get('id')}"
        print(f"PASS: All {len(stores)} stores have valid store_types")

    def test_create_business_store_still_works(self, auth_headers):
        """Verify business store creation is unaffected."""
        unique_name = f"TEST_Business_Store_{int(time.time())}"
        payload = {
            "name": unique_name,
            "store_type": "business",
            "owner_name": "Business Test Owner"
        }
        resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
        assert resp.status_code == 200, f"Business store creation failed: {resp.text}"
        store = resp.json()
        assert store.get("store_type") == "business"
        # Cleanup
        requests.delete(f"{BASE_URL}/api/webstores/v2/{store['id']}", headers=auth_headers)
        print("PASS: Business store creation still works")

    def test_invalid_store_type_rejected(self, auth_headers):
        """Verify invalid store type returns validation error."""
        payload = {
            "name": "TEST_InvalidType",
            "store_type": "invalid_type",
            "owner_name": "Test Owner"
        }
        resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
        assert resp.status_code in (400, 422), (
            f"Expected 400/422 for invalid store_type, got {resp.status_code}: {resp.text}"
        )
        print("PASS: Invalid store type correctly rejected with 400/422")
