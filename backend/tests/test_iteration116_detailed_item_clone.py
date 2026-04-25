"""
Iteration 116 regression: Detailed Order Item Entry flow
 - POST /api/job-tickets/{id}/clone (3 modes: duplicate, variation, copy_to_category)
 - carry_over flags (artwork / quantity / due_date / production_notes)
 - Cross-category remap (rigid_signs -> banners drops rigid-specific specs)
 - GET /api/job-tickets/schema/{category} visible_when rules
 - PUT/GET /api/orders/{id} shared_* context fields
 - POST /api/orders/{id}/upload + GET /api/orders/{id}/files (is_shared flag)
"""
import os
import io
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://prelaunch-checklist.preview.emergentagent.com").rstrip("/")
EMAIL = "signguypa@gmail.com"
PASSWORD = "Billnel323"


@pytest.fixture(scope="session")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def client(auth_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def test_order(client):
    # Create fresh order
    payload = {
        "customer_name": "TEST_iter116_Customer",
        "name": f"TEST_iter116_Order_{uuid.uuid4().hex[:6]}",
        "contact_name": "Tester",
        "email": "testeriter116@example.com",
    }
    r = client.post(f"{BASE_URL}/api/orders", json=payload, timeout=30)
    assert r.status_code in (200, 201), f"Order create failed: {r.status_code} {r.text}"
    order = r.json()
    yield order
    # cleanup — archive/delete
    try:
        client.delete(f"{BASE_URL}/api/orders/{order['id']}", timeout=15)
    except Exception:
        pass


@pytest.fixture(scope="session")
def rigid_source_ticket(client, test_order):
    """Create a rigid_signs ticket with rich spec data for clone testing."""
    payload = {
        "order_id": test_order["id"],
        "item_name": "TEST_iter116_SourceSign",
        "item_category": "rigid_signs",
        "quantity": 5,
        "due_date": "2026-02-15",
        "special_instructions": "Handle with care",
        "production_notes": "Use UV print",
        "install_notes": "Install on north wall",
        "description": "Source rigid sign",
        "specs": {
            "width": "36",
            "height": "24",
            "unit_of_measure": "in",
            "substrate_material_key": "acm_3mm_white",
            "print_method": "uv_flatbed",
            "double_sided": "double",
            "double_sided_art": "mirror",
            "hardware_included": True,
            "hardware_type": "standoffs",
            "artwork_ready": True,
            "rush_order": False,
            "production_notes": "Use UV print",
            "install_notes": "Install on north wall",
            "install_required": True,
            "install_complexity": "basic",
        },
        "linked_order_file_ids": [],
        "item_artwork_file_ids": [],
    }
    r = client.post(f"{BASE_URL}/api/job-tickets", json=payload, timeout=30)
    assert r.status_code in (200, 201), f"Ticket create failed: {r.status_code} {r.text}"
    return r.json()


# ===== CLONE ENDPOINT =====
class TestCloneEndpoint:
    def test_clone_duplicate_mode(self, client, rigid_source_ticket):
        body = {"mode": "duplicate", "carry_over": {"artwork": True, "production_notes": True, "quantity": True, "due_date": True}}
        r = client.post(f"{BASE_URL}/api/job-tickets/{rigid_source_ticket['id']}/clone", json=body, timeout=30)
        assert r.status_code == 200, f"clone(duplicate) failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["id"] != rigid_source_ticket["id"]
        assert data["clone_mode"] == "duplicate"
        assert data["source_item_id"] == rigid_source_ticket["id"]
        assert data["item_category"] == "rigid_signs"
        assert data["item_name"].startswith("Copy of ")
        assert "ticket_number" in data and data["ticket_number"]
        # carry_over quantity=true → keep 5
        assert data["quantity"] == 5
        # carry_over due_date=true → kept
        assert data["due_date"] is not None
        # production_notes carried
        assert data["production_notes"] == "Use UV print"
        assert data["install_notes"] == "Install on north wall"
        # converted_from_category should be None for non-copy modes
        assert data.get("converted_from_category") in (None, "")

    def test_clone_variation_mode(self, client, rigid_source_ticket):
        body = {"mode": "variation", "carry_over": {"artwork": True, "production_notes": True, "quantity": False, "due_date": False}}
        r = client.post(f"{BASE_URL}/api/job-tickets/{rigid_source_ticket['id']}/clone", json=body, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["clone_mode"] == "variation"
        assert data["item_name"].startswith("Variant \u2014 ") or data["item_name"].startswith("Variant - ")
        # quantity=false → reset to 1
        assert data["quantity"] == 1
        # due_date=false → None
        assert data["due_date"] in (None, "")
        # entry_mode should be 'detailed' for variation
        assert data.get("entry_mode") == "detailed"

    def test_clone_copy_to_category_drops_specifics(self, client, rigid_source_ticket):
        body = {
            "mode": "copy_to_category",
            "target_category": "banners",
            "carry_over": {"artwork": True, "production_notes": True, "design_setup": True, "rush_setting": True},
        }
        r = client.post(f"{BASE_URL}/api/job-tickets/{rigid_source_ticket['id']}/clone", json=body, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["clone_mode"] == "copy_to_category"
        assert data["item_category"] == "banners"
        assert data["converted_from_category"] == "rigid_signs"
        assert data["item_name"].startswith("Converted \u2014 ") or data["item_name"].startswith("Converted - ")
        specs = data.get("specs") or {}
        # Rigid-specific fields dropped
        assert "hardware_included" not in specs
        assert "hardware_type" not in specs
        assert "double_sided_art" not in specs
        assert "substrate_material_key" not in specs
        # Universal fields kept via design_setup + rush_setting
        assert specs.get("artwork_ready") is True
        assert specs.get("rush_order") is False
        # width/height/unit_of_measure remapped
        assert specs.get("width") == "36"
        assert specs.get("height") == "24"
        assert specs.get("unit_of_measure") == "in"
        # double_sided carried (on remap allow-list)
        assert specs.get("double_sided") == "double"

    def test_clone_carry_over_artwork_false_resets_linked_files(self, client, rigid_source_ticket):
        body = {"mode": "duplicate", "carry_over": {"artwork": False, "quantity": False}}
        r = client.post(f"{BASE_URL}/api/job-tickets/{rigid_source_ticket['id']}/clone", json=body, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["linked_order_file_ids"] == []
        assert data["item_artwork_file_ids"] == []
        assert data["quantity"] == 1

    def test_clone_nonexistent_returns_404(self, client):
        r = client.post(f"{BASE_URL}/api/job-tickets/nonexistent-id-xyz/clone", json={"mode": "duplicate"}, timeout=30)
        assert r.status_code == 404


# ===== VISIBLE_WHEN schema rules =====
class TestSchemaVisibleWhen:
    @pytest.mark.parametrize("category,expected", [
        ("rigid_signs", {
            "install_complexity": {"install_required": True},
            "hardware_type": {"hardware_included": True},
            "drill_prep_required": {"hardware_included": True},
            "double_sided_art": {"sidedness": "double"},
            "protective_finish_type": {"protective_finish": True},
            "design_complexity": {"artwork_needed": True},
        }),
        ("cut_vinyl", {
            "install_complexity": {"install_required": True},
            "design_complexity": {"artwork_needed": True},
        }),
        ("banners", {
            "install_complexity": {"install_required": True},
            "design_complexity": {"artwork_needed": True},
        }),
        ("vehicle_wrap", {
            "install_difficulty_level": {"install_required": True},
            "wrap_laminate_type_key": {"wrap_laminate_required": True},
        }),
        ("services", {
            "services_flat_fee": {"services_billing_unit": "flat"},
            "services_travel_miles": {"services_travel_required": True},
        }),
    ])
    def test_schema_visible_when(self, client, category, expected):
        r = client.get(f"{BASE_URL}/api/job-tickets/schema/{category}", timeout=30)
        assert r.status_code == 200, f"{category}: {r.status_code} {r.text}"
        schema = r.json()
        # Collect fields list
        fields = schema.get("fields") if isinstance(schema, dict) else schema
        assert isinstance(fields, list)
        by_key = {f.get("key"): f for f in fields if isinstance(f, dict)}
        for key, rule in expected.items():
            assert key in by_key, f"Field {key} missing from {category} schema"
            assert by_key[key].get("visible_when") == rule, (
                f"{category}.{key} visible_when mismatch: got {by_key[key].get('visible_when')}, expected {rule}"
            )

    def test_apparel_size_visible_when(self, client):
        r = client.get(f"{BASE_URL}/api/job-tickets/schema/apparel", timeout=30)
        assert r.status_code == 200
        fields = r.json().get("fields") or []
        by_key = {f.get("key"): f for f in fields}
        # size_m should be hidden when apparel_product_type is hat
        assert by_key.get("size_m", {}).get("visible_when") == {
            "apparel_product_type": {"not_in": ["hat_standard", "hat_premium", "visor"]}
        }
        # apparel_stitch_count visible when decoration=embroidery
        assert by_key.get("apparel_stitch_count", {}).get("visible_when") == {
            "apparel_decoration_method": "embroidery"
        }


# ===== Shared order-level context =====
class TestSharedContext:
    def test_put_get_shared_fields(self, client, test_order):
        update = {
            "order_title": "TEST_iter116 shared title",
            "shared_production_notes": "global production note",
            "shared_color_brand_notes": "Pantone 185C, red",
            "shared_install_notes": "Install at rear entrance",
            "shared_design_notes": "Logo centered",
            "shared_artwork_default_mode": "inherit",
        }
        r = client.put(f"{BASE_URL}/api/orders/{test_order['id']}", json=update, timeout=30)
        assert r.status_code == 200, r.text
        body = r.json()
        for k, v in update.items():
            assert body.get(k) == v, f"PUT response field {k}: got {body.get(k)}, expected {v}"
        # GET round-trip
        g = client.get(f"{BASE_URL}/api/orders/{test_order['id']}", timeout=30)
        assert g.status_code == 200
        gbody = g.json()
        for k, v in update.items():
            assert gbody.get(k) == v, f"GET round-trip field {k}: got {gbody.get(k)}, expected {v}"


# ===== Order files shared flag =====
class TestOrderFilesShared:
    def test_upload_and_list_with_is_shared(self, client, test_order, auth_token):
        # multipart upload
        url = f"{BASE_URL}/api/orders/{test_order['id']}/upload"
        files = {"file": ("TEST_iter116.txt", io.BytesIO(b"hello iter116"), "text/plain")}
        data = {"category": "artwork", "tags": "logo,approved", "is_shared": "true"}
        headers = {"Authorization": f"Bearer {auth_token}"}
        r = requests.post(url, files=files, data=data, headers=headers, timeout=60)
        assert r.status_code in (200, 201), f"upload: {r.status_code} {r.text}"
        uploaded = r.json()
        assert uploaded.get("is_shared") is True
        assert uploaded.get("category") == "artwork"
        assert "logo" in (uploaded.get("tags") or [])

        # list files
        lr = client.get(f"{BASE_URL}/api/orders/{test_order['id']}/files", timeout=30)
        assert lr.status_code == 200
        file_list = lr.json()
        assert isinstance(file_list, list)
        match = next((f for f in file_list if f.get("id") == uploaded["id"]), None)
        assert match is not None, "Uploaded file not returned in list"
        assert match.get("is_shared") is True
        assert match.get("category") == "artwork"
