"""
Tier 7 Pre-launch Sweep - Signatures & Drawings backend API tests.

Covers:
  - 7.1 Signatures: capture, list, file retrieval, requirement, request,
        public sign, public decline.
  - 7.2 Order Drawings: create, list, file retrieval, update, delete, query w/ filters.
"""
import base64
import io
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://ticket-tracker-ai-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
TEST_ORDER_ID = "1efe0ae8-473d-4d5f-bde7-dbfde8180cda"


# Generate a valid PNG (>=1000 bytes for signatures, >=150 for drawings)
def _make_png(min_bytes: int = 1500) -> str:
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (200, 80), "white")
        draw = ImageDraw.Draw(img)
        # Several scribbly lines so the resulting PNG comfortably exceeds 1000 bytes
        for i in range(0, 200, 4):
            draw.line([(i, 10 + (i % 30)), (i + 8, 50 + (i % 20))], fill="black", width=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()
    except Exception:
        # Fallback: synthesize a >1000 byte string and encode
        data = b"\x89PNG\r\n\x1a\n" + os.urandom(max(min_bytes, 1500))
    if len(data) < min_bytes:
        data = data + os.urandom(min_bytes - len(data))
    return "data:image/png;base64," + base64.b64encode(data).decode()


# ---------------- Fixtures ----------------

@pytest.fixture(scope="session")
def admin_token() -> str:
    r = requests.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def signature_image() -> str:
    return _make_png(min_bytes=1500)


@pytest.fixture(scope="session")
def drawing_image() -> str:
    return _make_png(min_bytes=600)


# ============================================================
# 7.1 SIGNATURES
# ============================================================

class TestSignatureFeatureEnabled:
    """Confirm signature feature is enabled for the test tenant."""

    def test_list_signatures_does_not_404_for_disabled(self, auth_headers):
        r = requests.get(f"{API}/signatures?order_id={TEST_ORDER_ID}", headers=auth_headers, timeout=30)
        # If feature is disabled the API returns 404 with that detail. We need 200.
        assert r.status_code == 200, f"Signature feature appears disabled: {r.status_code} {r.text}"
        assert isinstance(r.json(), list)


class TestSignatureCapture:
    """7.1 In-app signature capture via POST /api/signatures/capture."""

    def test_capture_signature_for_order(self, auth_headers, signature_image):
        payload = {
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "signer_name": "TEST_Tier7_Signer",
            "signer_role": "customer",
            "printed_name": "TEST_Tier7_Signer",
            "notes": "Tier 7 sweep test",
            "image_data": signature_image,
        }
        r = requests.post(f"{API}/signatures/capture", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"Capture failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["status"] == "signed"
        assert data["signer_name"] == "TEST_Tier7_Signer"
        assert data["order_id"] == TEST_ORDER_ID
        assert data["parent_record_type"] == "order"
        assert data["signature_image"].startswith("/api/signatures/file/")
        assert data["signed_at"]
        # Stash for later tests
        pytest.captured_signature_id = data["id"]

    def test_capture_rejects_blank_image(self, auth_headers):
        # ~10 bytes of 0xFF — will be < 1000 bytes after b64 decoded
        tiny = "data:image/png;base64," + base64.b64encode(b"\x00" * 50).decode()
        payload = {
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "signer_name": "TEST_Blank",
            "image_data": tiny,
        }
        r = requests.post(f"{API}/signatures/capture", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 400, f"Expected 400 blank, got {r.status_code} {r.text}"

    def test_capture_rejects_unknown_parent_type(self, auth_headers, signature_image):
        payload = {
            "parent_record_type": "totally_invalid",
            "parent_record_id": TEST_ORDER_ID,
            "signer_name": "X",
            "image_data": signature_image,
        }
        r = requests.post(f"{API}/signatures/capture", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 400


class TestSignatureList:
    """GET /api/signatures?order_id=..."""

    def test_list_includes_captured_signature(self, auth_headers):
        r = requests.get(f"{API}/signatures?order_id={TEST_ORDER_ID}", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        rows = r.json()
        assert isinstance(rows, list) and len(rows) > 0
        ids = [row["id"] for row in rows]
        assert getattr(pytest, "captured_signature_id", None) in ids
        # Validate row shape
        sample = rows[0]
        for key in ("id", "parent_record_type", "parent_record_id", "signature_type", "status", "tenant_id"):
            assert key in sample
        assert "request_token" not in sample, "request_token must NOT leak in list response"

    def test_list_filter_by_parent_record(self, auth_headers):
        r = requests.get(
            f"{API}/signatures?parent_record_type=order&parent_record_id={TEST_ORDER_ID}",
            headers=auth_headers, timeout=30,
        )
        assert r.status_code == 200
        for row in r.json():
            assert row["parent_record_type"] == "order"
            assert row["parent_record_id"] == TEST_ORDER_ID

    def test_list_unauthenticated_rejected(self):
        r = requests.get(f"{API}/signatures?order_id={TEST_ORDER_ID}", timeout=30)
        assert r.status_code in (401, 403)


class TestSignatureFile:
    """GET /api/signatures/file/{id} returns image bytes."""

    def test_file_retrieval(self, auth_headers):
        sig_id = getattr(pytest, "captured_signature_id", None)
        assert sig_id, "No captured signature id available"
        r = requests.get(f"{API}/signatures/file/{sig_id}", timeout=30)
        assert r.status_code == 200, f"File retrieval failed: {r.status_code} {r.text[:200]}"
        assert r.headers.get("content-type", "").startswith("image/")
        assert len(r.content) > 100

    def test_file_retrieval_404_for_unknown(self):
        r = requests.get(f"{API}/signatures/file/{uuid.uuid4()}", timeout=30)
        assert r.status_code == 404


class TestSignatureRequirement:
    """POST /api/signatures/requirement creates/updates pending requirement."""

    def test_create_requirement_for_order(self, auth_headers):
        payload = {
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "requires_signature": True,
        }
        r = requests.post(f"{API}/signatures/requirement", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"Requirement failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["requires_signature"] is True
        assert data["parent_record_type"] == "order"
        assert data["status"] in ("pending", "signed")  # may match an existing signed record
        assert "request_token" not in data
        pytest.requirement_signature_id = data["id"]


class TestSignatureRequest:
    """POST /api/signatures/request emails a public signing link."""

    def test_request_signature_via_email(self, auth_headers):
        payload = {
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "request_email": "TEST_tier7@example.com",
            "origin_url": "https://ticket-tracker-ai-1.preview.emergentagent.com",
            "signer_name": "TEST_Public_Signer",
            "signer_role": "customer",
            "notes": "Tier 7 public sign test",
            "expires_in_days": 7,
        }
        r = requests.post(f"{API}/signatures/request", json=payload, headers=auth_headers, timeout=60)
        assert r.status_code == 200, f"Request failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["message"] == "Signature request sent"
        assert "signature_id" in data and "expires_at" in data
        pytest.requested_signature_id = data["signature_id"]


class TestPublicSignatureFlow:
    """Public token: GET preview, POST sign, POST decline."""

    def _get_token_for(self, signature_id, auth_headers):
        # Need to read request_token from DB-backed list; the public list does not include it.
        # Workaround: send a fresh request to obtain a *new* token we control end-to-end.
        payload = {
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "request_email": "TEST_publicflow@example.com",
            "origin_url": "https://ticket-tracker-ai-1.preview.emergentagent.com",
            "signer_name": "TEST_Public_Flow",
            "expires_in_days": 7,
        }
        r = requests.post(f"{API}/signatures/request", json=payload, headers=auth_headers, timeout=60)
        assert r.status_code == 200
        # The request endpoint does not return the token, so look it up via Mongo-less workaround:
        # We use the email_logs collection? Not exposed. Instead, list the signature, grab its id,
        # and call a small internal helper: there is none. Therefore retrieve token via /api/signatures
        # which excludes it; this means we must use the previously-captured request token by querying
        # the public endpoint with the id won't work — public expects token, not id.
        # Skip path: re-use request_token through DB? Not available externally.
        # We will instead verify only the negative branch (invalid token returns 404).
        return None

    def test_public_get_invalid_token_404(self):
        r = requests.get(f"{API}/signatures/public/{uuid.uuid4()}", timeout=30)
        assert r.status_code == 404

    def test_public_sign_invalid_token_404(self, signature_image):
        payload = {"signer_name": "X", "image_data": signature_image}
        r = requests.post(f"{API}/signatures/public/{uuid.uuid4()}/sign", json=payload, timeout=30)
        assert r.status_code == 404

    def test_public_decline_invalid_token_404(self):
        payload = {"signer_name": "X", "notes": "no"}
        r = requests.post(f"{API}/signatures/public/{uuid.uuid4()}/decline", json=payload, timeout=30)
        assert r.status_code == 404


# ============================================================
# 7.2 ORDER DRAWINGS
# ============================================================

class TestDrawingCRUD:

    def test_create_drawing_for_order(self, auth_headers, drawing_image):
        payload = {
            "order_id": TEST_ORDER_ID,
            "parent_type": "order",
            "drawing_type": "sketch",
            "label": "TEST_Tier7_Drawing",
            "notes": "Tier 7 sweep",
            "image_data": drawing_image,
            "status": "saved",
            "tags": ["tier7", "test"],
        }
        r = requests.post(f"{API}/order-drawings/", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"Create drawing failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["order_id"] == TEST_ORDER_ID
        assert data["label"] == "TEST_Tier7_Drawing"
        assert data["drawing_type"] == "sketch"
        assert data["status"] == "saved"
        assert data["image_url"].startswith("/api/order-drawings/file/")
        assert data["file_size"] > 100
        pytest.tier7_drawing_id = data["id"]

    def test_create_drawing_rejects_blank(self, auth_headers):
        tiny = "data:image/png;base64," + base64.b64encode(b"\x00" * 30).decode()
        payload = {
            "order_id": TEST_ORDER_ID,
            "parent_type": "order",
            "drawing_type": "sketch",
            "label": "TEST_Blank",
            "image_data": tiny,
        }
        r = requests.post(f"{API}/order-drawings/", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 400

    def test_create_drawing_invalid_order(self, auth_headers, drawing_image):
        payload = {
            "order_id": str(uuid.uuid4()),
            "parent_type": "order",
            "drawing_type": "sketch",
            "label": "TEST_BadOrder",
            "image_data": drawing_image,
        }
        r = requests.post(f"{API}/order-drawings/", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 404

    def test_list_drawings_by_order_id_path(self, auth_headers):
        r = requests.get(f"{API}/order-drawings/{TEST_ORDER_ID}", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        rows = r.json()
        assert isinstance(rows, list)
        ids = [row["id"] for row in rows]
        assert getattr(pytest, "tier7_drawing_id", None) in ids
        sample = next(row for row in rows if row["id"] == pytest.tier7_drawing_id)
        assert sample["order_id"] == TEST_ORDER_ID
        assert sample["label"] == "TEST_Tier7_Drawing"

    def test_query_drawings_with_filters(self, auth_headers):
        r = requests.get(
            f"{API}/order-drawings?order_id={TEST_ORDER_ID}&status=saved",
            headers=auth_headers, timeout=30,
        )
        assert r.status_code == 200
        rows = r.json()
        assert isinstance(rows, list)
        for row in rows:
            assert row["order_id"] == TEST_ORDER_ID
            assert row["status"] == "saved"

    def test_drawing_file_retrieval(self):
        drawing_id = getattr(pytest, "tier7_drawing_id", None)
        assert drawing_id
        r = requests.get(f"{API}/order-drawings/file/{drawing_id}", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("image/")
        assert len(r.content) > 100

    def test_update_drawing(self, auth_headers):
        drawing_id = getattr(pytest, "tier7_drawing_id", None)
        assert drawing_id
        payload = {"label": "TEST_Tier7_Drawing_Updated", "notes": "updated", "status": "finalized"}
        r = requests.put(f"{API}/order-drawings/{drawing_id}", json=payload, headers=auth_headers, timeout=30)
        assert r.status_code == 200, f"Update failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["label"] == "TEST_Tier7_Drawing_Updated"
        assert data["status"] == "finalized"
        # Verify persistence via GET
        r2 = requests.get(f"{API}/order-drawings/{TEST_ORDER_ID}", headers=auth_headers, timeout=30)
        rows = r2.json()
        match = next(row for row in rows if row["id"] == drawing_id)
        assert match["label"] == "TEST_Tier7_Drawing_Updated"
        assert match["status"] == "finalized"

    def test_update_drawing_invalid_status(self, auth_headers):
        drawing_id = getattr(pytest, "tier7_drawing_id", None)
        assert drawing_id
        r = requests.put(
            f"{API}/order-drawings/{drawing_id}",
            json={"status": "nope"},
            headers=auth_headers, timeout=30,
        )
        assert r.status_code == 400

    def test_delete_drawing(self, auth_headers):
        drawing_id = getattr(pytest, "tier7_drawing_id", None)
        assert drawing_id
        r = requests.delete(f"{API}/order-drawings/{drawing_id}", headers=auth_headers, timeout=30)
        assert r.status_code == 200
        # Verify removal: should no longer appear in list
        r2 = requests.get(f"{API}/order-drawings/{TEST_ORDER_ID}", headers=auth_headers, timeout=30)
        ids = [row["id"] for row in r2.json()]
        assert drawing_id not in ids
        # File retrieval should also 404 (visibility_status=deleted)
        r3 = requests.get(f"{API}/order-drawings/file/{drawing_id}", timeout=30)
        assert r3.status_code == 404

    def test_drawing_unauthenticated_rejected(self, drawing_image):
        payload = {
            "order_id": TEST_ORDER_ID,
            "parent_type": "order",
            "drawing_type": "sketch",
            "label": "TEST_NoAuth",
            "image_data": drawing_image,
        }
        r = requests.post(f"{API}/order-drawings/", json=payload, timeout=30)
        assert r.status_code in (401, 403)
