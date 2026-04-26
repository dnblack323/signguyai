"""
Iteration 130 — Prelaunch Checklist Sections 2.6 / 2.7 / 2.8 / 2.9 / 2.10
Tests:
  2.6  Artwork/Files/Drawings (file upload, promote-to-shared, delete, content, drawings CRUD)
  2.7  Webstores remaining (slug uniqueness, storefront SEO/OG)
  2.8  Products CRUD (create, update, delete, apparel-options, field round-trip)
  2.9  Questionnaires (CRUD, public access, submit, required-field enforcement, email validation)
  2.10 Customer Signature Page (requirement, public token, sign, one-time-use, invalid/expired token)
"""

import os
import io
import struct
import zlib
import base64
import uuid
import pytest
import requests
import pymongo

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
EMAIL = "thesigntistslab@gmail.com"
PASSWORD = "password123"

ORDER_ID = "aa583c33-8c17-4c14-96ee-56cce7971754"  # Existing order for file tests

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "signguy_ai")


# ─── helpers ─────────────────────────────────────────────────────────────────

def make_png(width: int, height: int, r=255, g=0, b=0) -> bytes:
    """Create a valid RGB PNG of the given size (no external deps)."""
    def chunk(ctype: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + ctype + data
        return c + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    raw = b""
    for _ in range(height):
        raw += b"\x00" + bytes([r, g, b]) * width
    idat = chunk(b"IDAT", zlib.compress(raw, 0))  # level 0 → minimal compression → larger file
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# 20x20 PNG → ~1288 bytes (>150 for drawing, >1000 for signature)
PNG_20 = make_png(20, 20, r=255, g=0, b=0)
# 1x1 red PNG for quick uploads
PNG_1 = make_png(1, 1, r=255, g=0, b=0)

# Minimal valid JPEG (SOI+APP0+DQT+SOF0+DHT+SOS+EOI pattern)
JPEG_BYTES = bytes([
    0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
    0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
    0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
    0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
    0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
    0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
    0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
    0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
    0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
    0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
    0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
    0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
    0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
    0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
    0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
    0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
    0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
    0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
    0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
    0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
    0x8A, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3, 0xA4,
    0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6, 0xB7,
    0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9, 0xCA,
    0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2, 0xE3,
    0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4, 0xF5,
    0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00,
    0x00, 0x3F, 0x00, 0xFB, 0xDB, 0xFF, 0xD9,
])

PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n" \
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n" \
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n" \
            b"xref\n0 4\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"

SVG_BYTES = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect fill="red" width="10" height="10"/></svg>'

AI_BYTES = b"%!PS-Adobe-3.0 EPSF-3.0\n%%BoundingBox: 0 0 100 100\n%%EndComments\nnewpath 10 10 moveto 90 10 lineto showpage"

PNG_DATA_URL_20 = "data:image/png;base64," + base64.b64encode(PNG_20).decode()


def get_token() -> str:
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
        timeout=15,
    )
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text[:200]}"
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def token():
    return get_token()


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def get_mongo_db():
    client = pymongo.MongoClient(MONGO_URL)
    return client[DB_NAME]


# ─── 2.6 File Upload Tests ────────────────────────────────────────────────────

class TestFileUpload:
    """2.6 - Order file upload, retrieve, promote-to-shared, delete, drawing CRUD"""

    # Shared state across test methods (class-level variables set in tests)
    png_file_id = None
    jpg_file_id = None
    pdf_file_id = None
    svg_file_id = None
    ai_file_id = None

    def test_2_6_A_upload_png(self, auth_headers):
        """Upload PNG file — verify 200, id, filename, content_type, file_size > 0"""
        resp = requests.post(
            f"{BASE_URL}/api/orders/{ORDER_ID}/upload",
            headers=auth_headers,
            files={"file": ("test_artwork.png", io.BytesIO(PNG_1), "image/png")},
            data={"is_shared": "false", "category": "artwork", "label": "Test PNG"},
            timeout=30,
        )
        assert resp.status_code == 200, f"2.6-A PNG upload failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "id" in data, "Missing 'id' in response"
        assert data.get("filename") == "test_artwork.png"
        assert data.get("content_type") == "image/png"
        assert data.get("file_size", 0) > 0
        assert data.get("category") == "artwork"
        TestFileUpload.png_file_id = data["id"]
        print(f"2.6-A PASS — PNG file_id={data['id']}")

    def test_2_6_B_upload_jpg(self, auth_headers):
        """Upload JPG file — verify content_type=image/jpeg"""
        resp = requests.post(
            f"{BASE_URL}/api/orders/{ORDER_ID}/upload",
            headers=auth_headers,
            files={"file": ("logo.jpg", io.BytesIO(JPEG_BYTES), "image/jpeg")},
            data={"is_shared": "false", "category": "logo"},
            timeout=30,
        )
        assert resp.status_code == 200, f"2.6-B JPG upload failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert data.get("content_type") == "image/jpeg", f"Expected image/jpeg, got {data.get('content_type')}"
        assert data.get("file_size", 0) > 0
        TestFileUpload.jpg_file_id = data["id"]
        print(f"2.6-B PASS — JPG file_id={data['id']}")

    def test_2_6_C_upload_pdf(self, auth_headers):
        """Upload PDF — verify content_type=application/pdf"""
        resp = requests.post(
            f"{BASE_URL}/api/orders/{ORDER_ID}/upload",
            headers=auth_headers,
            files={"file": ("spec.pdf", io.BytesIO(PDF_BYTES), "application/pdf")},
            data={"is_shared": "false", "category": "reference"},
            timeout=30,
        )
        assert resp.status_code == 200, f"2.6-C PDF upload failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert data.get("content_type") == "application/pdf"
        assert data.get("file_size", 0) > 0
        TestFileUpload.pdf_file_id = data["id"]
        print(f"2.6-C PASS — PDF file_id={data['id']}")

    def test_2_6_D_upload_svg(self, auth_headers):
        """Upload SVG — verify accepted (image/svg+xml starts with image/ prefix)"""
        resp = requests.post(
            f"{BASE_URL}/api/orders/{ORDER_ID}/upload",
            headers=auth_headers,
            files={"file": ("design.svg", io.BytesIO(SVG_BYTES), "image/svg+xml")},
            data={"is_shared": "false", "category": "artwork"},
            timeout=30,
        )
        # image/svg+xml starts with "image/" prefix → should be accepted
        assert resp.status_code == 200, f"2.6-D SVG upload failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert data.get("content_type") in ("image/svg+xml", "application/octet-stream")
        TestFileUpload.svg_file_id = data["id"]
        print(f"2.6-D PASS — SVG file_id={data['id']}, content_type={data.get('content_type')}")

    def test_2_6_E_upload_ai(self, auth_headers):
        """Upload .ai file with application/octet-stream — verify accepted, no 422/500"""
        resp = requests.post(
            f"{BASE_URL}/api/orders/{ORDER_ID}/upload",
            headers=auth_headers,
            files={"file": ("logo.ai", io.BytesIO(AI_BYTES), "application/octet-stream")},
            data={"is_shared": "false", "category": "artwork"},
            timeout=30,
        )
        assert resp.status_code not in (422, 500), f"2.6-E .ai upload rejected: {resp.status_code} {resp.text[:300]}"
        assert resp.status_code == 200, f"2.6-E .ai upload failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert data.get("file_size", 0) > 0
        TestFileUpload.ai_file_id = data["id"]
        print(f"2.6-E PASS — AI file_id={data['id']}")

    def test_2_6_F_file_content(self, auth_headers):
        """GET file content for the PNG uploaded in 2.6-A → 200, image bytes, Content-Type header"""
        if not TestFileUpload.png_file_id:
            pytest.skip("PNG file_id not set (2.6-A failed)")
        resp = requests.get(
            f"{BASE_URL}/api/orders/{ORDER_ID}/files/{TestFileUpload.png_file_id}/content",
            headers=auth_headers,
            timeout=20,
        )
        assert resp.status_code == 200, f"2.6-F content failed: {resp.status_code} {resp.text[:200]}"
        assert len(resp.content) > 0, "2.6-F: empty content returned"
        assert "image/png" in resp.headers.get("content-type", ""), \
            f"2.6-F: Expected image/png content-type, got {resp.headers.get('content-type')}"
        print(f"2.6-F PASS — content bytes={len(resp.content)}, ct={resp.headers.get('content-type')}")

    def test_2_6_G_file_list(self, auth_headers):
        """GET /files list — should contain the uploaded files from 2.6-A through 2.6-E"""
        resp = requests.get(
            f"{BASE_URL}/api/orders/{ORDER_ID}/files",
            headers=auth_headers,
            timeout=15,
        )
        assert resp.status_code == 200, f"2.6-G list failed: {resp.status_code} {resp.text[:200]}"
        files = resp.json()
        assert isinstance(files, list), "2.6-G: expected list"
        file_ids = {f["id"] for f in files}
        for label, fid in [
            ("PNG", TestFileUpload.png_file_id),
            ("JPG", TestFileUpload.jpg_file_id),
            ("PDF", TestFileUpload.pdf_file_id),
            ("SVG", TestFileUpload.svg_file_id),
            ("AI", TestFileUpload.ai_file_id),
        ]:
            if fid:
                assert fid in file_ids, f"2.6-G: {label} file_id={fid} NOT in file list"
        print(f"2.6-G PASS — {len(files)} files in list, all uploaded files found")

    def test_2_6_H_promote_to_shared(self, auth_headers):
        """Promote file to shared → is_shared=True in file record"""
        if not TestFileUpload.png_file_id:
            pytest.skip("PNG file_id not set")
        resp = requests.post(
            f"{BASE_URL}/api/orders/{ORDER_ID}/files/{TestFileUpload.png_file_id}/promote-to-shared",
            headers=auth_headers,
            timeout=15,
        )
        assert resp.status_code == 200, f"2.6-H promote failed: {resp.status_code} {resp.text[:200]}"
        data = resp.json()
        assert data.get("ok") is True, f"2.6-H: expected ok=True, got {data}"
        # Verify is_shared=True via file list
        list_resp = requests.get(
            f"{BASE_URL}/api/orders/{ORDER_ID}/files",
            headers=auth_headers,
            timeout=15,
        )
        assert list_resp.status_code == 200
        files = list_resp.json()
        promoted = next((f for f in files if f["id"] == TestFileUpload.png_file_id), None)
        assert promoted is not None, "2.6-H: file not found in list after promote"
        assert promoted.get("is_shared") is True, f"2.6-H: is_shared not True, got {promoted.get('is_shared')}"
        print(f"2.6-H PASS — is_shared=True confirmed")

    def test_2_6_I_file_delete(self, auth_headers):
        """DELETE file → 200; subsequent content → 404"""
        if not TestFileUpload.ai_file_id:
            pytest.skip("AI file_id not set")
        del_resp = requests.delete(
            f"{BASE_URL}/api/orders/{ORDER_ID}/files/{TestFileUpload.ai_file_id}",
            headers=auth_headers,
            timeout=15,
        )
        assert del_resp.status_code == 200, f"2.6-I delete failed: {del_resp.status_code} {del_resp.text[:200]}"

        # Subsequent content fetch should 404
        content_resp = requests.get(
            f"{BASE_URL}/api/orders/{ORDER_ID}/files/{TestFileUpload.ai_file_id}/content",
            headers=auth_headers,
            timeout=15,
        )
        assert content_resp.status_code == 404, \
            f"2.6-I: Expected 404 after delete, got {content_resp.status_code}"
        print("2.6-I PASS — delete confirmed, content returns 404")


# ─── 2.6 Drawing Tests ────────────────────────────────────────────────────────

class TestDrawings:
    """2.6-J through 2.6-M — Order Drawing CRUD"""

    drawing_id = None

    def test_2_6_J_drawing_create(self, auth_headers):
        """Create drawing with base64 data URL → 200/201, drawing_id returned"""
        resp = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=auth_headers,
            json={
                "order_id": ORDER_ID,
                "image_data": PNG_DATA_URL_20,
                "title": "Test Sketch",
                "drawing_type": "sketch",
                "parent_type": "order",
            },
            timeout=30,
        )
        assert resp.status_code in (200, 201), f"2.6-J create failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "id" in data, f"2.6-J: missing id in {data}"
        assert data.get("title") in ("Test Sketch", "sketch", "Sketch"), f"2.6-J: title mismatch: {data.get('title')}"
        TestDrawings.drawing_id = data["id"]
        print(f"2.6-J PASS — drawing_id={data['id']}, title={data.get('title')}")

    def test_2_6_K_drawing_retrieve(self, auth_headers):
        """GET /order-drawings/{order_id} → list contains the created drawing"""
        resp = requests.get(
            f"{BASE_URL}/api/order-drawings/{ORDER_ID}",
            headers=auth_headers,
            timeout=15,
        )
        assert resp.status_code == 200, f"2.6-K list failed: {resp.status_code} {resp.text[:200]}"
        drawings = resp.json()
        assert isinstance(drawings, list), "2.6-K: expected list"
        if TestDrawings.drawing_id:
            ids = [d["id"] for d in drawings]
            assert TestDrawings.drawing_id in ids, \
                f"2.6-K: drawing_id={TestDrawings.drawing_id} not in list: {ids}"
        print(f"2.6-K PASS — {len(drawings)} drawings in list")

    def test_2_6_L_drawing_file(self, auth_headers):
        """GET /order-drawings/file/{drawing_id} → 200, image bytes"""
        if not TestDrawings.drawing_id:
            pytest.skip("Drawing ID not set (2.6-J failed)")
        resp = requests.get(
            f"{BASE_URL}/api/order-drawings/file/{TestDrawings.drawing_id}",
            # No auth required for file endpoint (public)
            timeout=20,
        )
        assert resp.status_code == 200, f"2.6-L file failed: {resp.status_code} {resp.text[:200]}"
        assert len(resp.content) > 0, "2.6-L: empty content returned"
        print(f"2.6-L PASS — drawing file bytes={len(resp.content)}")

    def test_2_6_M_drawing_delete(self, auth_headers):
        """DELETE drawing → 200; subsequent file → 404"""
        if not TestDrawings.drawing_id:
            pytest.skip("Drawing ID not set (2.6-J failed)")
        del_resp = requests.delete(
            f"{BASE_URL}/api/order-drawings/{TestDrawings.drawing_id}",
            headers=auth_headers,
            timeout=15,
        )
        assert del_resp.status_code == 200, f"2.6-M delete failed: {del_resp.status_code} {del_resp.text[:200]}"

        # After soft-delete, file endpoint should 404
        file_resp = requests.get(
            f"{BASE_URL}/api/order-drawings/file/{TestDrawings.drawing_id}",
            timeout=15,
        )
        assert file_resp.status_code == 404, \
            f"2.6-M: Expected 404 after delete, got {file_resp.status_code}"
        print("2.6-M PASS — soft delete, file returns 404")


# ─── 2.7 Webstores (slug uniqueness + storefront) ────────────────────────────

class TestWebstores:
    """2.7-A Slug/name uniqueness, 2.7-F SEO/OG storefront response"""

    webstore_id_1 = None
    webstore_id_2 = None

    def test_2_7_A_slug_name_uniqueness(self, auth_headers):
        """POST /api/webstores/v2 twice with same name — document if uniqueness enforced"""
        payload = {
            "name": f"TEST_DUP_STORE_{uuid.uuid4().hex[:8]}",
            "store_type": "business",
            "owner_name": "Test Owner",
            "owner_email": "test@example.com",
            "owner_phone": "555-1234",
            "is_public": False,
        }
        resp1 = requests.post(f"{BASE_URL}/api/webstores/v2", headers=auth_headers, json=payload, timeout=15)
        assert resp1.status_code == 200, f"2.7-A first create failed: {resp1.status_code} {resp1.text[:200]}"
        TestWebstores.webstore_id_1 = resp1.json().get("id")

        resp2 = requests.post(f"{BASE_URL}/api/webstores/v2", headers=auth_headers, json=payload, timeout=15)
        # Document actual behavior — uniqueness may or may not be enforced
        if resp2.status_code == 200:
            TestWebstores.webstore_id_2 = resp2.json().get("id")
            print(f"2.7-A INFO — Name uniqueness NOT enforced (both creates succeed): id1={TestWebstores.webstore_id_1}, id2={TestWebstores.webstore_id_2}")
        elif resp2.status_code in (400, 409, 422):
            print(f"2.7-A INFO — Name uniqueness IS enforced: second create returned {resp2.status_code}")
        else:
            print(f"2.7-A WARNING — Unexpected status on duplicate: {resp2.status_code} {resp2.text[:200]}")
        # Either behavior is valid to document
        print("2.7-A PASS — behavior documented above")

    def test_2_7_F_storefront_seo_og(self, auth_headers):
        """GET /api/storefront/{webstore_id} → inspect for seo_title/og_image/meta fields"""
        # Use an existing active webstore
        list_resp = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers, timeout=15)
        assert list_resp.status_code == 200, f"2.7-F list failed: {list_resp.status_code}"

        webstores = list_resp.json()
        active = next((w for w in webstores if w.get("status") == "active" and w.get("is_public", False)), None)
        if not active:
            # Find any active (is_public might default True)
            active = next((w for w in webstores if w.get("status") == "active"), None)
        if not active:
            pytest.skip("No active webstore found for storefront test")

        webstore_id = active["id"]
        resp = requests.get(f"{BASE_URL}/api/storefront/{webstore_id}", timeout=15)
        assert resp.status_code == 200, f"2.7-F storefront failed: {resp.status_code} {resp.text[:200]}"

        # Check content-type
        ct = resp.headers.get("content-type", "")
        if "text/html" in ct:
            # HTML response — check for <title> and <meta> tags
            html = resp.text
            has_title = "<title>" in html
            has_meta_desc = 'name="description"' in html or 'property="og:' in html
            print(f"2.7-F INFO — HTML response: has_title={has_title}, has_og_meta={has_meta_desc}")
        else:
            # JSON response — check for seo fields
            data = resp.json()
            seo_fields = ["seo_title", "seo_description", "og_image", "meta_description"]
            present = [f for f in seo_fields if f in data]
            missing = [f for f in seo_fields if f not in data]
            print(f"2.7-F INFO — JSON response fields: present={present}, missing={missing}")
            print(f"2.7-F INFO — Actual fields: {list(data.keys())}")
            assert "id" in data, "2.7-F: webstore id not in storefront response"
            assert "name" in data, "2.7-F: webstore name not in storefront response"
        print(f"2.7-F PASS — storefront endpoint returns 200")


# ─── 2.8 Products CRUD ───────────────────────────────────────────────────────

class TestProducts:
    """2.7-B/C/D/E/G — Product CRUD + apparel-options + field round-trip"""

    product_id = None

    def test_2_7_B_product_create(self, auth_headers):
        """POST /api/products — create product, verify product_id returned"""
        payload = {
            "name": "TEST_Banner_2.8",
            "description": "Test banner product",
            "category": "signs",         # ProductCategory enum: apparel/signs/decals/promotional/other
            "base_cost": 25.00,          # NOTE: Product model uses 'base_cost' + 'retail_price', NOT 'base_price'
            "retail_price": 45.00,
            "has_variants": False,
        }
        resp = requests.post(f"{BASE_URL}/api/products", headers=auth_headers, json=payload, timeout=15)
        assert resp.status_code in (200, 201), f"2.7-B create failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "id" in data, f"2.7-B: missing id in {data}"
        assert data.get("name") == "TEST_Banner_2.8"
        assert data.get("retail_price") == 45.00
        TestProducts.product_id = data["id"]
        print(f"2.7-B PASS — product_id={data['id']}, retail_price={data.get('retail_price')}")

    def test_2_7_C_product_edit(self, auth_headers):
        """PUT /api/products/{id} — update name + price"""
        if not TestProducts.product_id:
            pytest.skip("product_id not set (2.7-B failed)")
        resp = requests.put(
            f"{BASE_URL}/api/products/{TestProducts.product_id}",
            headers=auth_headers,
            json={"name": "Updated Banner 2.8", "retail_price": 50.00},
            timeout=15,
        )
        assert resp.status_code == 200, f"2.7-C update failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert data.get("name") == "Updated Banner 2.8", f"2.7-C: name not updated: {data.get('name')}"
        assert data.get("retail_price") == 50.00, f"2.7-C: price not updated: {data.get('retail_price')}"
        print(f"2.7-C PASS — name={data.get('name')}, retail_price={data.get('retail_price')}")

    def test_2_7_D_product_delete(self, auth_headers):
        """DELETE /api/products/{id} → 200; subsequent GET → 404"""
        if not TestProducts.product_id:
            pytest.skip("product_id not set (2.7-B failed)")
        del_resp = requests.delete(
            f"{BASE_URL}/api/products/{TestProducts.product_id}",
            headers=auth_headers,
            timeout=15,
        )
        assert del_resp.status_code == 200, f"2.7-D delete failed: {del_resp.status_code} {del_resp.text[:200]}"

        # Subsequent GET should 404
        get_resp = requests.get(
            f"{BASE_URL}/api/products/{TestProducts.product_id}",
            headers=auth_headers,
            timeout=15,
        )
        assert get_resp.status_code == 404, \
            f"2.7-D: Expected 404 after delete, got {get_resp.status_code}"
        TestProducts.product_id = None  # Cleanup marker
        print("2.7-D PASS — product deleted, GET returns 404")

    def test_2_7_E_apparel_options(self, auth_headers):
        """GET /api/products/defaults/apparel-options → non-empty array with tier/color options"""
        resp = requests.get(
            f"{BASE_URL}/api/products/defaults/apparel-options",
            headers=auth_headers,
            timeout=15,
        )
        assert resp.status_code == 200, f"2.7-E apparel-options failed: {resp.status_code} {resp.text[:200]}"
        data = resp.json()
        assert "tiers" in data, f"2.7-E: missing 'tiers' key in {list(data.keys())}"
        assert "apparel_sizes" in data, f"2.7-E: missing 'apparel_sizes' key"
        tiers = data.get("tiers", {})
        assert len(tiers) > 0, "2.7-E: tiers is empty"
        sizes = data.get("apparel_sizes", [])
        assert len(sizes) > 0, "2.7-E: apparel_sizes is empty"
        print(f"2.7-E PASS — tiers={list(tiers.keys())}, sizes={sizes[:4]}")

    def test_2_7_G_product_field_round_trip(self, auth_headers):
        """POST product with extra fields (size_options, color_options, is_featured, in_stock) → document behavior"""
        payload = {
            "name": "TEST_RoundTrip_2.8",
            "description": "Round-trip field test",
            "category": "apparel",
            "base_cost": 10.00,
            "retail_price": 25.00,
            "has_variants": False,
            # NOTE: Product model uses extra='ignore' — these fields will be silently dropped
            "size_options": ["S", "M", "L"],
            "color_options": ["Red", "Blue"],
            "is_featured": True,
            "in_stock": True,
        }
        resp = requests.post(f"{BASE_URL}/api/products", headers=auth_headers, json=payload, timeout=15)
        assert resp.status_code in (200, 201), f"2.7-G create failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        product_id = data["id"]

        # GET the product back and check which fields are preserved
        get_resp = requests.get(f"{BASE_URL}/api/products/{product_id}", headers=auth_headers, timeout=15)
        assert get_resp.status_code == 200, f"2.7-G GET failed: {get_resp.status_code}"
        got = get_resp.json()

        # Required fields must be present
        assert got.get("name") == "TEST_RoundTrip_2.8"
        assert got.get("retail_price") == 25.00
        assert got.get("description") == "Round-trip field test"

        # Document extra fields behavior
        extra_present = [f for f in ["size_options", "color_options", "is_featured", "in_stock"] if f in got]
        extra_missing = [f for f in ["size_options", "color_options", "is_featured", "in_stock"] if f not in got]
        print(f"2.7-G INFO — extra fields present in GET: {extra_present}, missing (stripped by model): {extra_missing}")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/products/{product_id}", headers=auth_headers, timeout=15)
        print(f"2.7-G PASS — base fields round-trip correctly; extra fields stripped by Product model (extra='ignore')")


# ─── 2.9 Questionnaires ──────────────────────────────────────────────────────

class TestQuestionnaires:
    """2.9-A through 2.9-G — Questionnaire CRUD, public submit, validation"""

    questionnaire_id = None
    q_text_id = None
    q_textarea_id = None
    q_email_id = None
    q_phone_id = None
    q_select_id = None
    q_checkbox_id = None
    q_required_text_id = None
    response_id = None

    def test_2_9_A_create_questionnaire(self, auth_headers):
        """POST /api/questionnaires — with multiple field types, verify id + fields array"""
        # Valid QuestionType values from enum: text, textarea, number, email, phone,
        # select, multi_select, radio, checkbox, date, file_upload, signature, heading, paragraph
        # NOTE: 'short_text','long_text','multiple_choice','dropdown' are NOT valid enum values
        questions = [
            {
                "type": "text",
                "label": "Company Name",
                "required": True,
                "order": 0,
            },
            {
                "type": "textarea",
                "label": "Project Description",
                "required": False,
                "order": 1,
            },
            {
                "type": "select",
                "label": "Sign Type",
                "required": False,
                "options": [
                    {"value": "banner", "label": "Banner"},
                    {"value": "vinyl", "label": "Vinyl"},
                ],
                "order": 2,
            },
            {
                "type": "checkbox",
                "label": "Services Needed",
                "required": False,
                "options": [
                    {"value": "design", "label": "Design"},
                    {"value": "install", "label": "Installation"},
                ],
                "order": 3,
            },
            {
                "type": "email",
                "label": "Contact Email",
                "required": False,
                "order": 4,
            },
            {
                "type": "phone",
                "label": "Phone Number",
                "required": False,
                "order": 5,
            },
            {
                "type": "radio",
                "label": "Turnaround Time",
                "required": False,
                "options": [
                    {"value": "rush", "label": "Rush (1-2 days)"},
                    {"value": "standard", "label": "Standard (5-7 days)"},
                ],
                "order": 6,
            },
        ]
        resp = requests.post(
            f"{BASE_URL}/api/questionnaires",
            headers=auth_headers,
            json={
                "name": "TEST_Pre-Production Intake",
                "description": "Test questionnaire for iteration 130",
                "category": "signage",
                "questions": questions,
            },
            timeout=15,
        )
        assert resp.status_code in (200, 201), f"2.9-A create failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "id" in data, f"2.9-A: missing id"
        assert data.get("name") == "TEST_Pre-Production Intake"
        q_list = data.get("questions", [])
        assert len(q_list) == len(questions), f"2.9-A: expected {len(questions)} questions, got {len(q_list)}"

        TestQuestionnaires.questionnaire_id = data["id"]
        # Store question IDs for later tests
        for q in q_list:
            if q.get("type") == "text" and "Company" in q.get("label", ""):
                TestQuestionnaires.q_text_id = q["id"]
                TestQuestionnaires.q_required_text_id = q["id"]
            elif q.get("type") == "textarea":
                TestQuestionnaires.q_textarea_id = q["id"]
            elif q.get("type") == "email":
                TestQuestionnaires.q_email_id = q["id"]
            elif q.get("type") == "phone":
                TestQuestionnaires.q_phone_id = q["id"]
            elif q.get("type") == "select":
                TestQuestionnaires.q_select_id = q["id"]
            elif q.get("type") == "checkbox":
                TestQuestionnaires.q_checkbox_id = q["id"]

        print(f"2.9-A PASS — questionnaire_id={data['id']}, {len(q_list)} fields preserved")

    def test_2_9_B_get_questionnaire(self, auth_headers):
        """GET /api/questionnaires/{id} → fields round-trip correctly"""
        if not TestQuestionnaires.questionnaire_id:
            pytest.skip("questionnaire_id not set (2.9-A failed)")
        resp = requests.get(
            f"{BASE_URL}/api/questionnaires/{TestQuestionnaires.questionnaire_id}",
            headers=auth_headers,
            timeout=15,
        )
        assert resp.status_code == 200, f"2.9-B GET failed: {resp.status_code} {resp.text[:200]}"
        data = resp.json()
        assert data.get("id") == TestQuestionnaires.questionnaire_id
        assert data.get("name") == "TEST_Pre-Production Intake"
        q_list = data.get("questions", [])
        assert len(q_list) >= 7, f"2.9-B: expected >=7 questions, got {len(q_list)}"
        # Verify field types round-trip
        types_found = {q["type"] for q in q_list}
        for expected_type in ["text", "textarea", "select", "checkbox", "email", "phone", "radio"]:
            assert expected_type in types_found, f"2.9-B: type '{expected_type}' missing from round-trip"
        print(f"2.9-B PASS — fields round-trip: {sorted(types_found)}")

    def test_2_9_C_activate_and_public_access(self, auth_headers):
        """Activate questionnaire, then GET /api/questionnaires/public/{id} without auth → 200"""
        if not TestQuestionnaires.questionnaire_id:
            pytest.skip("questionnaire_id not set (2.9-A failed)")

        # First activate the questionnaire (public endpoint requires status=active)
        update_resp = requests.put(
            f"{BASE_URL}/api/questionnaires/{TestQuestionnaires.questionnaire_id}",
            headers=auth_headers,
            json={"status": "active"},
            timeout=15,
        )
        assert update_resp.status_code == 200, f"2.9-C activate failed: {update_resp.status_code} {update_resp.text[:200]}"

        # Now test public access WITHOUT auth header
        public_resp = requests.get(
            f"{BASE_URL}/api/questionnaires/public/{TestQuestionnaires.questionnaire_id}",
            # No Authorization header — purely public
            timeout=15,
        )
        assert public_resp.status_code == 200, \
            f"2.9-C public access failed: {public_resp.status_code} {public_resp.text[:200]}"
        data = public_resp.json()
        assert data.get("name") == "TEST_Pre-Production Intake"
        # Sensitive fields should be excluded
        assert "tenant_id" not in data, "2.9-C: tenant_id exposed in public response"
        assert "created_by" not in data, "2.9-C: created_by exposed in public response"
        print(f"2.9-C PASS — public access works, sensitive fields excluded")

    def test_2_9_D_submit_questionnaire(self):
        """POST /api/questionnaires/public/{id}/submit with valid answers → 200, response_id"""
        if not TestQuestionnaires.questionnaire_id:
            pytest.skip("questionnaire_id not set (2.9-A failed)")

        answers = {}
        if TestQuestionnaires.q_text_id:
            answers[TestQuestionnaires.q_text_id] = "Test Company Inc"
        if TestQuestionnaires.q_textarea_id:
            answers[TestQuestionnaires.q_textarea_id] = "Looking for banner signs"
        if TestQuestionnaires.q_email_id:
            answers[TestQuestionnaires.q_email_id] = "customer@testcompany.com"
        if TestQuestionnaires.q_phone_id:
            answers[TestQuestionnaires.q_phone_id] = "555-867-5309"
        if TestQuestionnaires.q_select_id:
            answers[TestQuestionnaires.q_select_id] = "banner"
        if TestQuestionnaires.q_checkbox_id:
            answers[TestQuestionnaires.q_checkbox_id] = ["design", "install"]

        resp = requests.post(
            f"{BASE_URL}/api/questionnaires/public/{TestQuestionnaires.questionnaire_id}/submit",
            # No auth — public endpoint
            json={
                "questionnaire_id": TestQuestionnaires.questionnaire_id,
                "answers": answers,
                "customer_name": "Test Customer",
                "customer_email": "customer@testcompany.com",
            },
            timeout=15,
        )
        assert resp.status_code == 200, f"2.9-D submit failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "response_id" in data, f"2.9-D: missing response_id in {data}"
        TestQuestionnaires.response_id = data["response_id"]
        print(f"2.9-D PASS — response_id={data['response_id']}")

    def test_2_9_E_submission_in_dashboard(self, auth_headers):
        """GET /api/questionnaires/{id}/responses → submitted response appears"""
        if not TestQuestionnaires.questionnaire_id or not TestQuestionnaires.response_id:
            pytest.skip("questionnaire_id or response_id not set")
        resp = requests.get(
            f"{BASE_URL}/api/questionnaires/{TestQuestionnaires.questionnaire_id}/responses",
            headers=auth_headers,
            timeout=15,
        )
        assert resp.status_code == 200, f"2.9-E responses failed: {resp.status_code} {resp.text[:200]}"
        data = resp.json()
        assert "responses" in data, f"2.9-E: missing 'responses' key in {data}"
        responses = data["responses"]
        response_ids = [r["id"] for r in responses]
        assert TestQuestionnaires.response_id in response_ids, \
            f"2.9-E: response_id={TestQuestionnaires.response_id} not in responses: {response_ids[:5]}"
        # Check the response has answers
        target = next(r for r in responses if r["id"] == TestQuestionnaires.response_id)
        assert "answers" in target, "2.9-E: answers missing from response"
        print(f"2.9-E PASS — response found, answers={list(target.get('answers', {}).values())[:3]}")

    def test_2_9_F_required_field_enforcement(self):
        """Submit with required field missing → 422 or 400 (not 200)"""
        if not TestQuestionnaires.questionnaire_id:
            pytest.skip("questionnaire_id not set (2.9-A failed)")
        # Submit with empty answers — required 'Company Name' (text) field is missing
        resp = requests.post(
            f"{BASE_URL}/api/questionnaires/public/{TestQuestionnaires.questionnaire_id}/submit",
            json={
                "questionnaire_id": TestQuestionnaires.questionnaire_id,
                "answers": {},  # Missing required 'Company Name' field
                "customer_name": "Test",
            },
            timeout=15,
        )
        assert resp.status_code in (400, 422), \
            f"2.9-F: Expected 400/422 for missing required field, got {resp.status_code} {resp.text[:200]}"
        print(f"2.9-F PASS — required field enforcement returns {resp.status_code}")

    def test_2_9_G_email_validation(self):
        """Submit with invalid email in email field — document actual behavior"""
        if not TestQuestionnaires.questionnaire_id:
            pytest.skip("questionnaire_id not set (2.9-A failed)")

        answers = {}
        # Fulfill required field first
        if TestQuestionnaires.q_required_text_id:
            answers[TestQuestionnaires.q_required_text_id] = "Company Name"
        if TestQuestionnaires.q_email_id:
            answers[TestQuestionnaires.q_email_id] = "not-an-email"

        resp = requests.post(
            f"{BASE_URL}/api/questionnaires/public/{TestQuestionnaires.questionnaire_id}/submit",
            json={
                "questionnaire_id": TestQuestionnaires.questionnaire_id,
                "answers": answers,
                "customer_name": "Test",
            },
            timeout=15,
        )
        # NOTE: The submit endpoint does NOT validate answer field content/format,
        # only checks if required fields are present. Email format validation is not implemented.
        if resp.status_code in (400, 422):
            print(f"2.9-G PASS — email validation enforced: {resp.status_code}")
        elif resp.status_code == 200:
            print(f"2.9-G INFO — email validation NOT enforced (submit accepted with invalid email). "
                  "The questionnaire submit endpoint stores answers as Dict[str,Any] without format validation.")
            # This is not a hard fail — document for main agent
        else:
            print(f"2.9-G WARN — unexpected status: {resp.status_code} {resp.text[:200]}")
        # Test passes (documents behavior either way)
        assert resp.status_code in (200, 400, 422), f"Unexpected status: {resp.status_code}"


# ─── 2.10 Signatures ─────────────────────────────────────────────────────────

class TestSignatures:
    """2.10-A through 2.10-G — Signature requirement, public sign, one-time-use, invalid/expired token"""

    signature_id = None
    request_token = None
    expired_token = None
    expired_sig_id = None

    def test_2_10_A_create_signature_requirement(self, auth_headers):
        """POST /api/signatures/requirement → 200, id returned; verify signature feature is enabled"""
        payload = {
            "parent_record_type": "order",
            "parent_record_id": ORDER_ID,
            "order_id": ORDER_ID,
            "document_version": "v1",
            "requires_signature": True,
        }
        resp = requests.post(
            f"{BASE_URL}/api/signatures/requirement",
            headers=auth_headers,
            json=payload,
            timeout=15,
        )
        if resp.status_code == 404 and "disabled" in resp.text:
            pytest.skip("Signature feature is disabled for this tenant — enable via tenant settings")
        assert resp.status_code == 200, f"2.10-A requirement failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "id" in data, f"2.10-A: missing id in response"
        assert data.get("status") == "pending"
        assert data.get("requires_signature") is True
        # NOTE: request_token is intentionally NOT returned in the response (stripped by code)
        # The token must be retrieved from MongoDB for public testing
        assert "request_token" not in data, "2.10-A: INFO — request_token correctly NOT exposed in response"
        TestSignatures.signature_id = data["id"]
        print(f"2.10-A PASS — signature_id={data['id']}, status={data.get('status')}")

    def test_2_10_B_get_request_token_from_db(self):
        """Get request_token from MongoDB (API does not expose it) — used for 2.10-C/D/E"""
        if not TestSignatures.signature_id:
            pytest.skip("signature_id not set (2.10-A failed)")
        db = get_mongo_db()
        sig = db.signatures.find_one({"id": TestSignatures.signature_id}, {"_id": 0, "request_token": 1})
        assert sig is not None, f"2.10-B: signature {TestSignatures.signature_id} not found in MongoDB"
        assert sig.get("request_token"), f"2.10-B: request_token is empty/missing in MongoDB"
        TestSignatures.request_token = sig["request_token"]
        print(f"2.10-B PASS — token retrieved from DB (API does NOT expose token in any endpoint response — design note)")
        print(f"  Token: {TestSignatures.request_token[:20]}... [truncated]")

    def test_2_10_C_public_token_loads(self):
        """GET /api/signatures/public/{token} (no auth) → 200 with signature details"""
        if not TestSignatures.request_token:
            pytest.skip("request_token not set (2.10-B failed)")
        resp = requests.get(
            f"{BASE_URL}/api/signatures/public/{TestSignatures.request_token}",
            # No Authorization header — public endpoint
            timeout=15,
        )
        assert resp.status_code == 200, \
            f"2.10-C public load failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "id" in data, "2.10-C: missing id"
        assert "status" in data, "2.10-C: missing status"
        assert "signature_type" in data, "2.10-C: missing signature_type"
        assert data.get("status") == "pending", f"2.10-C: expected pending, got {data.get('status')}"
        # Sensitive fields not exposed
        assert "request_token" not in data, "2.10-C: request_token should not be exposed"
        print(f"2.10-C PASS — public token loads, status=pending, fields={list(data.keys())}")

    def test_2_10_D_customer_signs(self):
        """POST /api/signatures/public/{token}/sign → 200, status changes to 'signed'"""
        if not TestSignatures.request_token:
            pytest.skip("request_token not set")
        # Use 20x20 PNG (1288 bytes > 1000 byte minimum requirement for signature)
        sig_image_data = PNG_DATA_URL_20

        resp = requests.post(
            f"{BASE_URL}/api/signatures/public/{TestSignatures.request_token}/sign",
            json={
                "signer_name": "Test Customer",
                "signer_role": "customer",
                "image_data": sig_image_data,
                "notes": "Iteration 130 test signature",
            },
            timeout=30,
        )
        assert resp.status_code == 200, f"2.10-D sign failed: {resp.status_code} {resp.text[:300]}"
        data = resp.json()
        assert "signed_at" in data, f"2.10-D: missing signed_at in response"
        # Verify status changed in DB
        db = get_mongo_db()
        sig = db.signatures.find_one({"id": TestSignatures.signature_id}, {"_id": 0, "status": 1, "signature_acquired": 1})
        assert sig["status"] == "signed", f"2.10-D: expected status='signed', got '{sig['status']}'"
        assert sig["signature_acquired"] is True, "2.10-D: signature_acquired should be True"
        print(f"2.10-D PASS — signed_at={data.get('signed_at')}, DB status=signed")

    def test_2_10_E_token_one_time_use(self):
        """POST sign again with same token → 400 (already signed)"""
        if not TestSignatures.request_token:
            pytest.skip("request_token not set")
        resp = requests.post(
            f"{BASE_URL}/api/signatures/public/{TestSignatures.request_token}/sign",
            json={
                "signer_name": "Repeat Customer",
                "image_data": PNG_DATA_URL_20,
            },
            timeout=15,
        )
        assert resp.status_code in (400, 409, 410), \
            f"2.10-E: Expected 400/409/410 for re-sign, got {resp.status_code} {resp.text[:200]}"
        print(f"2.10-E PASS — re-sign correctly rejected with {resp.status_code}")

    def test_2_10_F_invalid_token(self):
        """GET /api/signatures/public/fake-invalid-token-12345 → 404 or 400, no 500"""
        resp = requests.get(
            f"{BASE_URL}/api/signatures/public/fake-invalid-token-12345",
            timeout=15,
        )
        assert resp.status_code != 500, f"2.10-F: Got 500 (stack trace exposure risk): {resp.text[:200]}"
        assert resp.status_code in (400, 404), \
            f"2.10-F: Expected 400/404 for invalid token, got {resp.status_code} {resp.text[:200]}"
        print(f"2.10-F PASS — invalid token returns {resp.status_code} (no 500)")

    def test_2_10_G_expired_token(self):
        """Insert expired signature → GET public returns 410 with 'expired' message"""
        # Create a signature record with past expires_at directly in MongoDB
        expired_token = str(uuid.uuid4())
        expired_sig_id = str(uuid.uuid4())
        TestSignatures.expired_token = expired_token
        TestSignatures.expired_sig_id = expired_sig_id

        from datetime import datetime, timezone, timedelta
        db_conn = get_mongo_db()

        expired_sig = {
            "id": expired_sig_id,
            "tenant_id": "d9c5507b-879c-4bec-9736-1dc841334719",  # The test tenant
            "parent_record_type": "order",
            "parent_record_id": ORDER_ID,
            "order_id": ORDER_ID,
            "signature_type": "order_authorization",
            "status": "pending",
            "requires_signature": True,
            "signature_acquired": False,
            "request_token": expired_token,
            "expires_at": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),  # 30 days in the past
            "review_snapshot": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        db_conn.signatures.insert_one(expired_sig)

        resp = requests.get(
            f"{BASE_URL}/api/signatures/public/{expired_token}",
            timeout=15,
        )
        assert resp.status_code in (400, 410), \
            f"2.10-G: Expected 410 for expired token, got {resp.status_code} {resp.text[:200]}"
        # Check error message mentions "expired"
        resp_text = resp.text.lower()
        assert "expir" in resp_text, f"2.10-G: Response should mention 'expired': {resp.text[:200]}"

        # Cleanup
        db_conn.signatures.delete_one({"id": expired_sig_id})
        print(f"2.10-G PASS — expired token returns {resp.status_code} with 'expired' message")


# ─── Cleanup ─────────────────────────────────────────────────────────────────

class TestCleanup:
    """Cleanup test data created during testing"""

    def test_cleanup_questionnaire(self, auth_headers):
        """Delete the test questionnaire"""
        qid = TestQuestionnaires.questionnaire_id
        if not qid:
            print("Cleanup: no questionnaire to delete")
            return
        resp = requests.delete(f"{BASE_URL}/api/questionnaires/{qid}", headers=auth_headers, timeout=15)
        print(f"Cleanup: questionnaire {qid} delete → {resp.status_code}")

    def test_cleanup_webstore_duplicates(self, auth_headers):
        """Delete the test webstores created in 2.7-A"""
        for wsid in [TestWebstores.webstore_id_1, TestWebstores.webstore_id_2]:
            if wsid:
                resp = requests.delete(f"{BASE_URL}/api/webstores/v2/{wsid}", headers=auth_headers, timeout=15)
                print(f"Cleanup: webstore {wsid} delete → {resp.status_code}")

    def test_cleanup_remaining_files(self, auth_headers):
        """Delete any remaining test files from orders"""
        for label, fid in [
            ("PNG", TestFileUpload.png_file_id),
            ("JPG", TestFileUpload.jpg_file_id),
            ("PDF", TestFileUpload.pdf_file_id),
            ("SVG", TestFileUpload.svg_file_id),
        ]:
            if fid:
                resp = requests.delete(
                    f"{BASE_URL}/api/orders/{ORDER_ID}/files/{fid}",
                    headers=auth_headers,
                    timeout=15,
                )
                print(f"Cleanup: {label} file {fid} → {resp.status_code}")
