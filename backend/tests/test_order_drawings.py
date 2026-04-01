"""
Order Drawings API Tests
Tests for canvas-based drawing feature (signatures, sketches, markups)
attached to orders with Emergent Object Storage integration.
"""

import pytest
import requests
import os
import base64
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = PRODUCTION_OWNER_EMAIL
TEST_PASSWORD = PRODUCTION_OWNER_PASSWORD

# Test order ID (existing order ORD-0001)
TEST_ORDER_ID = "1efe0ae8-473d-4d5f-bde7-dbfde8180cda"

# Existing drawing ID from previous test
EXISTING_DRAWING_ID = "e2c99373-696b-4787-85f8-e2ac732a6b43"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing."""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access_token in response"
    return data["access_token"]


@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


def create_valid_png_base64():
    """Create a valid PNG image with actual drawing content (not blank).
    Must be > 1000 bytes after base64 decode to pass backend validation.
    """
    import struct
    import zlib
    
    def create_png(width, height):
        """Create a PNG with a visible pattern (not blank)."""
        def png_chunk(chunk_type, data):
            chunk_len = struct.pack('>I', len(data))
            chunk_crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
            return chunk_len + chunk_type + data + chunk_crc
        
        # PNG signature
        signature = b'\x89PNG\r\n\x1a\n'
        
        # IHDR chunk (RGB, 8-bit)
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr = png_chunk(b'IHDR', ihdr_data)
        
        # IDAT chunk (image data with pattern)
        raw_data = b''
        for y in range(height):
            raw_data += b'\x00'  # filter byte (none)
            for x in range(width):
                # Create a checkerboard + diagonal pattern
                if (x + y) % 10 < 5 or abs(x - y) < 3:
                    raw_data += b'\x00\x00\x00'  # black
                else:
                    raw_data += b'\xff\xff\xff'  # white
        
        # Use minimal compression to ensure larger file size
        compressed = zlib.compress(raw_data, 1)
        idat = png_chunk(b'IDAT', compressed)
        
        # IEND chunk
        iend = png_chunk(b'IEND', b'')
        
        return signature + ihdr + idat + iend
    
    # Create a 200x200 PNG with pattern (will be well > 1000 bytes)
    png_bytes = create_png(200, 200)
    print(f"Generated PNG size: {len(png_bytes)} bytes")
    return f"data:image/png;base64,{base64.b64encode(png_bytes).decode()}"


def create_blank_png_base64():
    """Create a blank/minimal PNG that should be rejected."""
    # Very small PNG (will be < 1000 bytes after decode)
    tiny_png = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
        b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return f"data:image/png;base64,{base64.b64encode(tiny_png).decode()}"


class TestOrderDrawingsListEndpoint:
    """Tests for GET /api/order-drawings/{order_id}"""
    
    def test_list_drawings_success(self, headers):
        """Test listing drawings for an order returns 200."""
        response = requests.get(
            f"{BASE_URL}/api/order-drawings/{TEST_ORDER_ID}",
            headers=headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} drawings for order {TEST_ORDER_ID}")
        
        # Verify structure if drawings exist
        if len(data) > 0:
            drawing = data[0]
            assert "id" in drawing, "Drawing should have id"
            assert "order_id" in drawing, "Drawing should have order_id"
            assert "type" in drawing, "Drawing should have type"
            assert "label" in drawing, "Drawing should have label"
            assert "image_url" in drawing, "Drawing should have image_url"
            assert "created_at" in drawing, "Drawing should have created_at"
            assert "created_by" in drawing, "Drawing should have created_by"
    
    def test_list_drawings_nonexistent_order(self, headers):
        """Test listing drawings for non-existent order returns empty list."""
        response = requests.get(
            f"{BASE_URL}/api/order-drawings/nonexistent-order-id",
            headers=headers
        )
        # Should return 200 with empty list (not 404)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 0, "Should return empty list for non-existent order"
    
    def test_list_drawings_unauthorized(self):
        """Test listing drawings without auth returns 401."""
        response = requests.get(
            f"{BASE_URL}/api/order-drawings/{TEST_ORDER_ID}"
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestOrderDrawingsCreateEndpoint:
    """Tests for POST /api/order-drawings/"""
    
    def test_create_drawing_success(self, headers):
        """Test creating a drawing with valid image data."""
        image_data = create_valid_png_base64()
        
        payload = {
            "order_id": TEST_ORDER_ID,
            "type": "sketch",
            "label": "TEST_Pytest Drawing",
            "notes": "Created by pytest",
            "image_data": image_data
        }
        
        response = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Response should have id"
        assert data["order_id"] == TEST_ORDER_ID, "order_id should match"
        assert data["type"] == "sketch", "type should match"
        assert data["label"] == "TEST_Pytest Drawing", "label should match"
        assert data["notes"] == "Created by pytest", "notes should match"
        assert "image_url" in data, "Should have image_url"
        assert "storage_path" in data, "Should have storage_path"
        assert "created_at" in data, "Should have created_at"
        assert "created_by" in data, "Should have created_by"
        assert not data["is_deleted"], "is_deleted should be False"
        
        print(f"Created drawing with ID: {data['id']}")
        
        # Store for cleanup
        TestOrderDrawingsCreateEndpoint.created_drawing_id = data["id"]
        
        # Verify drawing appears in list
        list_response = requests.get(
            f"{BASE_URL}/api/order-drawings/{TEST_ORDER_ID}",
            headers=headers
        )
        assert list_response.status_code == 200
        drawings = list_response.json()
        drawing_ids = [d["id"] for d in drawings]
        assert data["id"] in drawing_ids, "Created drawing should appear in list"
    
    def test_create_drawing_blank_rejected(self, headers):
        """Test that blank/minimal drawings are rejected."""
        image_data = create_blank_png_base64()
        
        payload = {
            "order_id": TEST_ORDER_ID,
            "type": "signature",
            "label": "Blank Test",
            "image_data": image_data
        }
        
        response = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 400, f"Expected 400 for blank drawing, got {response.status_code}"
        data = response.json()
        assert "blank" in data.get("detail", "").lower(), "Error should mention blank drawing"
    
    def test_create_drawing_invalid_type(self, headers):
        """Test that invalid drawing type is rejected."""
        image_data = create_valid_png_base64()
        
        payload = {
            "order_id": TEST_ORDER_ID,
            "type": "invalid_type",
            "label": "Invalid Type Test",
            "image_data": image_data
        }
        
        response = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
    
    def test_create_drawing_invalid_image_data(self, headers):
        """Test that invalid base64 image data is rejected."""
        payload = {
            "order_id": TEST_ORDER_ID,
            "type": "sketch",
            "label": "Invalid Image Test",
            "image_data": "not-valid-base64-data!!!"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid image, got {response.status_code}"
    
    def test_create_drawing_nonexistent_order(self, headers):
        """Test creating drawing for non-existent order returns 404."""
        image_data = create_valid_png_base64()
        
        payload = {
            "order_id": "nonexistent-order-id-12345",
            "type": "sketch",
            "label": "Test",
            "image_data": image_data
        }
        
        response = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=headers,
            json=payload
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_create_drawing_all_types(self, headers):
        """Test creating drawings with all valid types."""
        image_data = create_valid_png_base64()
        
        for drawing_type in ["signature", "sketch", "markup"]:
            payload = {
                "order_id": TEST_ORDER_ID,
                "type": drawing_type,
                "label": f"TEST_{drawing_type.capitalize()} Type Test",
                "image_data": image_data
            }
            
            response = requests.post(
                f"{BASE_URL}/api/order-drawings/",
                headers=headers,
                json=payload
            )
            
            assert response.status_code == 200, f"Failed to create {drawing_type}: {response.text}"
            data = response.json()
            assert data["type"] == drawing_type
            print(f"Created {drawing_type} drawing: {data['id']}")


class TestOrderDrawingsFileEndpoint:
    """Tests for GET /api/order-drawings/file/{drawing_id}"""
    
    def test_get_drawing_file_success(self, headers):
        """Test retrieving drawing file returns PNG."""
        # Use existing drawing or create one
        drawing_id = getattr(TestOrderDrawingsCreateEndpoint, 'created_drawing_id', EXISTING_DRAWING_ID)
        
        response = requests.get(
            f"{BASE_URL}/api/order-drawings/file/{drawing_id}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert response.headers.get("Content-Type") == "image/png", "Content-Type should be image/png"
        assert len(response.content) > 0, "Response should have content"
        
        # Verify PNG signature
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n', "Content should be valid PNG"
    
    def test_get_drawing_file_nonexistent(self, headers):
        """Test retrieving non-existent drawing file returns 404."""
        response = requests.get(
            f"{BASE_URL}/api/order-drawings/file/nonexistent-drawing-id",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestOrderDrawingsDeleteEndpoint:
    """Tests for DELETE /api/order-drawings/{drawing_id}"""
    
    def test_delete_drawing_admin_success(self, headers):
        """Test admin can delete a drawing (soft delete)."""
        # First create a drawing to delete
        image_data = create_valid_png_base64()
        
        create_response = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=headers,
            json={
                "order_id": TEST_ORDER_ID,
                "type": "sketch",
                "label": "TEST_To Be Deleted",
                "image_data": image_data
            }
        )
        
        assert create_response.status_code == 200, f"Failed to create drawing: {create_response.text}"
        drawing_id = create_response.json()["id"]
        
        # Now delete it
        delete_response = requests.delete(
            f"{BASE_URL}/api/order-drawings/{drawing_id}",
            headers=headers
        )
        
        assert delete_response.status_code == 200, f"Expected 200, got {delete_response.status_code}: {delete_response.text}"
        data = delete_response.json()
        assert "message" in data, "Response should have message"
        
        # Verify drawing no longer appears in list
        list_response = requests.get(
            f"{BASE_URL}/api/order-drawings/{TEST_ORDER_ID}",
            headers=headers
        )
        drawings = list_response.json()
        drawing_ids = [d["id"] for d in drawings]
        assert drawing_id not in drawing_ids, "Deleted drawing should not appear in list"
        
        # Verify file endpoint returns 404 for deleted drawing
        file_response = requests.get(
            f"{BASE_URL}/api/order-drawings/file/{drawing_id}",
            headers=headers
        )
        assert file_response.status_code == 404, "Deleted drawing file should return 404"
    
    def test_delete_drawing_nonexistent(self, headers):
        """Test deleting non-existent drawing returns 404."""
        response = requests.delete(
            f"{BASE_URL}/api/order-drawings/nonexistent-id",
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestOrderDrawingsUpdateEndpoint:
    """Tests for PUT /api/order-drawings/{drawing_id}"""
    
    def test_update_drawing_label(self, headers):
        """Test updating drawing label."""
        # First create a drawing
        image_data = create_valid_png_base64()
        
        create_response = requests.post(
            f"{BASE_URL}/api/order-drawings/",
            headers=headers,
            json={
                "order_id": TEST_ORDER_ID,
                "type": "sketch",
                "label": "TEST_Original Label",
                "image_data": image_data
            }
        )
        
        assert create_response.status_code == 200
        drawing_id = create_response.json()["id"]
        
        # Update label
        update_response = requests.put(
            f"{BASE_URL}/api/order-drawings/{drawing_id}",
            headers=headers,
            json={"label": "TEST_Updated Label"}
        )
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}"
        data = update_response.json()
        assert data["label"] == "TEST_Updated Label", "Label should be updated"
    
    def test_update_drawing_notes(self, headers):
        """Test updating drawing notes."""
        # Use existing drawing
        drawing_id = getattr(TestOrderDrawingsCreateEndpoint, 'created_drawing_id', EXISTING_DRAWING_ID)
        
        update_response = requests.put(
            f"{BASE_URL}/api/order-drawings/{drawing_id}",
            headers=headers,
            json={"notes": "Updated notes from pytest"}
        )
        
        # May return 404 if drawing was deleted, which is acceptable
        if update_response.status_code == 200:
            data = update_response.json()
            assert data["notes"] == "Updated notes from pytest"
        else:
            assert update_response.status_code == 404, f"Expected 200 or 404, got {update_response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
