"""
Iteration 148 — Wrap Command Center Phase 2F end-to-end tests.

Scope:
- Refactor regression: package mount preserves all paths and response shapes.
- Visual diagram markers: x_percent, y_percent, marker_label round-trip.
- Inspection customer_visible flag.
- Photos & Files CRUD (admin auth).
- Three PDF generators (Customer Receipt / Aftercare / Final Packet) -> wrap_files.
- Customer Portal extension: wrap_items attached to GET /api/portal/orders/{id}.
- Six portal action endpoints + portal file content download (portal JWT auth).
- Negative: no public unauth wrap-care endpoint.
"""

import io
import os
import asyncio
import pytest
import requests
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
ORDER_ID = "118b7377-687b-4a28-b42b-3c5f31da64c5"
TICKET_ID = "aa0387f8-ac70-4935-9bbc-33d03963e916"
PORTAL_EMAIL = "taxtest_non@example.com"
PORTAL_PASSWORD = "portal123"
PORTAL_CUSTOMER_ID = "1eaeec1d-6fbb-48fa-aa96-ecc4298bdb8b"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "thesigntistslab@gmail.com", "password": "password123"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def admin(admin_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {admin_token}"})
    return s


@pytest.fixture(scope="module")
def portal_token():
    r = requests.post(
        f"{BASE_URL}/api/portal/auth/login",
        json={"email": PORTAL_EMAIL, "password": PORTAL_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def portal(portal_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {portal_token}"})
    return s


@pytest.fixture(scope="module")
def order_customer_swap():
    """Swap order's customer_id to the portal customer for the test session,
    restore at teardown."""
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = client[os.environ["DB_NAME"]]

    async def _get_orig():
        o = await db.orders.find_one({"id": ORDER_ID}, {"_id": 0, "customer_id": 1, "customer_email": 1, "customer_name": 1})
        return o

    async def _set(cust_id, email, name):
        await db.orders.update_one(
            {"id": ORDER_ID},
            {"$set": {"customer_id": cust_id, "customer_email": email, "customer_name": name}},
        )

    loop = asyncio.new_event_loop()
    orig = loop.run_until_complete(_get_orig())
    loop.run_until_complete(_set(PORTAL_CUSTOMER_ID, PORTAL_EMAIL, "Tax Test Customer Non-Exempt"))
    yield
    loop.run_until_complete(
        _set(orig["customer_id"], orig.get("customer_email"), orig.get("customer_name"))
    )
    loop.close()
    client.close()


# ---------------------------------------------------------------------------
# Refactor regression
# ---------------------------------------------------------------------------
class TestRefactor:
    def test_get_wrap_item_returns_all_blocks(self, admin):
        r = admin.get(f"{BASE_URL}/api/wrap/items/{TICKET_ID}")
        assert r.status_code == 200, r.text
        d = r.json()
        for k in [
            "vehicle_info",
            "wrapped_areas",
            "materials",
            "pricing",
            "design",
            "contract",
            "approvals",
            "production",
            "install",
            "inspection",
            "aftercare",
            "pipeline_state",
            "coverage_summary",
        ]:
            assert k in d, f"missing block: {k}"
        # ensure no top-level mongo _id leaked
        assert "_id" not in d

    def test_recalculate_still_works(self, admin):
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/recalculate", json={})
        assert r.status_code == 200, r.text
        assert "pricing_snapshot" in r.json()

    def test_customer_facing_summary_internal(self, admin):
        r = admin.get(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/customer-facing-summary")
        assert r.status_code == 200
        body = r.json()
        # No profit/margin leak
        s = str(body).lower()
        assert "profit" not in s
        assert "margin" not in s
        assert "material_cost" not in s


# ---------------------------------------------------------------------------
# Visual diagram markers (x_percent / y_percent / marker_label)
# ---------------------------------------------------------------------------
class TestDiagramMarkers:
    def test_create_marker_with_position(self, admin):
        payload = {
            "area": "Hood",
            "damage_type": "Scratch",
            "severity": "Low",
            "x_percent": 42.5,
            "y_percent": 60.25,
            "marker_label": "M-TEST-148",
            "notes": "TEST_iter148 visual",
        }
        r = admin.post(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/inspection/damage-markers",
            json=payload,
        )
        assert r.status_code == 200, r.text
        markers = r.json().get("inspection", {}).get("damage_markers", [])
        found = next((m for m in markers if m.get("marker_label") == "M-TEST-148"), None)
        assert found is not None, "marker not persisted"
        assert abs(found["x_percent"] - 42.5) < 0.01
        assert abs(found["y_percent"] - 60.25) < 0.01
        pytest.marker_id = found["id"]

    def test_update_marker_position(self, admin):
        mid = pytest.marker_id
        r = admin.put(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/inspection/damage-markers/{mid}",
            json={"x_percent": 11.1, "y_percent": 22.2, "marker_label": "M-TEST-148-UPD"},
        )
        assert r.status_code == 200, r.text
        markers = r.json().get("inspection", {}).get("damage_markers", [])
        found = next((m for m in markers if m["id"] == mid), None)
        assert found
        assert abs(found["x_percent"] - 11.1) < 0.01
        assert abs(found["y_percent"] - 22.2) < 0.01
        assert found["marker_label"] == "M-TEST-148-UPD"

    def test_cleanup_marker(self, admin):
        mid = pytest.marker_id
        r = admin.delete(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/inspection/damage-markers/{mid}"
        )
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Inspection customer_visible
# ---------------------------------------------------------------------------
class TestInspectionCustomerVisible:
    def test_default_or_set_false(self, admin):
        r = admin.put(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/inspection",
            json={"customer_visible": False},
        )
        assert r.status_code == 200
        assert r.json()["inspection"]["customer_visible"] is False

    def test_set_true_round_trip(self, admin):
        r = admin.put(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/inspection",
            json={"customer_visible": True},
        )
        assert r.status_code == 200
        assert r.json()["inspection"]["customer_visible"] is True


# ---------------------------------------------------------------------------
# Photos & Files CRUD
# ---------------------------------------------------------------------------
class TestWrapFiles:
    uploaded_id = None

    def test_list_files_initial(self, admin):
        r = admin.get(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files")
        assert r.status_code == 200
        body = r.json()
        assert {"files", "categories", "counts_by_category", "total"} <= set(body)
        assert len(body["categories"]) == 14

    def test_upload_invalid_category(self, admin):
        files = {"file": ("t.txt", b"hi", "text/plain")}
        data = {"category": "BogusCategory"}
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files", files=files, data=data)
        assert r.status_code == 400

    def test_upload_too_large(self, admin):
        big = b"x" * (26 * 1024 * 1024)
        files = {"file": ("big.bin", big, "application/octet-stream")}
        data = {"category": "Customer Uploads"}
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files", files=files, data=data)
        assert r.status_code == 400

    def test_upload_unsupported_mime(self, admin):
        files = {"file": ("bad.xyz", b"x", "application/x-evil")}
        data = {"category": "Customer Uploads"}
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files", files=files, data=data)
        assert r.status_code == 400

    def test_upload_ok(self, admin):
        files = {"file": ("TEST_iter148.png", b"\x89PNG\r\n\x1a\nFAKE", "image/png")}
        data = {
            "category": "Vehicle Photos",
            "notes": "TEST_iter148",
            "customer_visible": "true",
            "marketing_allowed": "false",
        }
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files", files=files, data=data)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["category"] == "Vehicle Photos"
        assert d["customer_visible"] is True
        TestWrapFiles.uploaded_id = d["id"]

    def test_get_file_content(self, admin):
        fid = TestWrapFiles.uploaded_id
        r = admin.get(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files/{fid}/content")
        assert r.status_code == 200
        assert len(r.content) > 0

    def test_update_file(self, admin):
        fid = TestWrapFiles.uploaded_id
        r = admin.put(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files/{fid}",
            json={"customer_visible": False, "category": "Inspection Photos"},
        )
        assert r.status_code == 200
        d = r.json()
        assert d["customer_visible"] is False
        assert d["category"] == "Inspection Photos"

    def test_delete_file(self, admin):
        fid = TestWrapFiles.uploaded_id
        r = admin.delete(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files/{fid}")
        assert r.status_code == 200

    def test_wrong_tenant_404(self):
        # use no auth -> 401 first; emulate wrong tenant via fake bearer
        r = requests.get(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files",
            headers={"Authorization": "Bearer invalid.invalid.invalid"},
            timeout=15,
        )
        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# PDF generators
# ---------------------------------------------------------------------------
class TestPDFGenerators:
    receipt_id = None
    aftercare_id = None
    packet_id = None

    def test_customer_receipt(self, admin):
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/pdfs/customer-receipt", json={})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["category"] == "Signed Documents"
        assert d["customer_visible"] is True
        assert d["content_type"] == "application/pdf"
        TestPDFGenerators.receipt_id = d["id"]

    def test_aftercare(self, admin):
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/pdfs/aftercare", json={})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["category"] == "Aftercare Documents"
        assert d["customer_visible"] is True
        TestPDFGenerators.aftercare_id = d["id"]

    def test_final_packet(self, admin):
        r = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/pdfs/final-packet", json={})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["category"] == "Final Packets"
        assert d["customer_visible"] is False
        TestPDFGenerators.packet_id = d["id"]

    def test_download_pdf(self, admin):
        fid = TestPDFGenerators.receipt_id
        r = admin.get(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files/{fid}/content")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("application/pdf")
        assert r.content[:4] == b"%PDF"
        assert len(r.content) > 200


# ---------------------------------------------------------------------------
# Portal extension: wrap_items in /api/portal/orders/{id}
# ---------------------------------------------------------------------------
class TestPortalOrderWrapItems:
    def test_get_order_with_wrap_items(self, portal, order_customer_swap):
        r = portal.get(f"{BASE_URL}/api/portal/orders/{ORDER_ID}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "wrap_items" in d, "wrap_items missing for wrap order"
        items = d["wrap_items"]
        assert len(items) >= 1
        wi = items[0]
        for k in [
            "ticket_id",
            "order_id",
            "wrap_type",
            "vehicle",
            "design",
            "contract",
            "inspection",
            "install",
            "aftercare",
            "pricing",
            "approvals",
            "pipeline_state",
            "files",
            "care_instructions",
        ]:
            assert k in wi, f"wrap_items[0] missing key: {k}"
        # No internal leakage
        flat = str(wi).lower()
        assert "profit" not in flat
        assert "margin" not in flat
        assert "material_cost" not in flat
        assert "labor_cost" not in flat
        assert "internal_notes" not in flat
        # Inspection.customer_visible flag respected
        ins = wi["inspection"]
        assert "customer_visible" in ins
        # damage notes never exposed
        assert "damage_notes" not in ins
        assert "inspection_notes" not in ins


# ---------------------------------------------------------------------------
# Portal actions
# ---------------------------------------------------------------------------
class TestPortalActions:
    def test_approve_quote(self, portal, order_customer_swap):
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/approve-quote",
            json={},
        )
        assert r.status_code == 200, r.text

    def test_approve_proof(self, portal, order_customer_swap):
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/approve-proof",
            json={},
        )
        assert r.status_code == 200, r.text

    def test_request_revision(self, portal, order_customer_swap):
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/request-revision",
            json={"notes": "TEST_iter148 please adjust"},
        )
        assert r.status_code == 200, r.text

    def test_acknowledge_contract(self, portal, order_customer_swap):
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/acknowledge-contract",
            json={"signed_by": "TEST_iter148", "accepted_terms": True},
        )
        assert r.status_code == 200, r.text

    def test_acknowledge_inspection_blocked_when_not_visible(self, admin, portal, order_customer_swap):
        # Force inspection.customer_visible=false
        admin.put(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/inspection",
            json={"customer_visible": False},
        )
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/acknowledge-inspection",
            json={},
        )
        assert r.status_code == 400, r.text

    def test_acknowledge_inspection_ok_when_visible(self, admin, portal, order_customer_swap):
        admin.put(
            f"{BASE_URL}/api/wrap/items/{TICKET_ID}/inspection",
            json={"customer_visible": True},
        )
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/acknowledge-inspection",
            json={},
        )
        assert r.status_code == 200, r.text

    def test_acknowledge_aftercare(self, portal, order_customer_swap):
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/acknowledge-aftercare",
            json={},
        )
        assert r.status_code == 200, r.text

    def test_cross_tenant_404(self, portal):
        r = portal.post(
            f"{BASE_URL}/api/portal/orders/bogus-order-id/wrap/bogus-ticket/approve-proof",
            json={},
        )
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Portal file download (customer_visible only)
# ---------------------------------------------------------------------------
class TestPortalFileDownload:
    def test_portal_download_customer_visible(self, admin, portal, order_customer_swap):
        # upload a CV file as admin
        files = {"file": ("portal_test.png", b"\x89PNG\r\n\x1a\nFAKE", "image/png")}
        data = {"category": "Proofs", "customer_visible": "true"}
        u = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files", files=files, data=data)
        assert u.status_code == 200, u.text
        fid = u.json()["id"]
        try:
            r = portal.get(
                f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/files/{fid}/content"
            )
            assert r.status_code == 200, r.text
            assert len(r.content) > 0
        finally:
            admin.delete(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files/{fid}")

    def test_portal_download_blocked_internal_file(self, admin, portal, order_customer_swap):
        files = {"file": ("internal.png", b"\x89PNG\r\n\x1a\nFAKE", "image/png")}
        data = {"category": "Final Packets", "customer_visible": "false"}
        u = admin.post(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files", files=files, data=data)
        assert u.status_code == 200
        fid = u.json()["id"]
        try:
            r = portal.get(
                f"{BASE_URL}/api/portal/orders/{ORDER_ID}/wrap/{TICKET_ID}/files/{fid}/content"
            )
            assert r.status_code == 404
        finally:
            admin.delete(f"{BASE_URL}/api/wrap/items/{TICKET_ID}/files/{fid}")


# ---------------------------------------------------------------------------
# Negative: no public wrap-care portal
# ---------------------------------------------------------------------------
class TestNoPublicWrapCare:
    def test_no_public_wrap_care_get(self):
        r = requests.get(f"{BASE_URL}/api/public/wrap-care/anything", timeout=15)
        assert r.status_code == 404

    def test_no_public_wrap_care_token(self):
        r = requests.get(f"{BASE_URL}/api/public/wrap-care/aa0387f8-ac70-4935-9bbc-33d03963e916", timeout=15)
        assert r.status_code == 404
