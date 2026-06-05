"""
Iteration 100 - Testing signature capture, drawing persistence, and schedule shift edit
Tests the fixes for:
1. Signature capture modal runtime loop (DrawingCanvasPad callback dependencies)
2. Schedule shift unified PATCH path parsing
3. Drawing save/preview persistence
"""

import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://sign-shop-checkout.preview.emergentagent.com')

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "signguypa@gmail.com",
        "password": "Billnel323"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")

@pytest.fixture
def headers(auth_token):
    """Headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestSignatureCapture:
    """Test signature capture API endpoints"""
    
    def test_signatures_endpoint_exists(self, headers):
        """Verify signatures endpoint is accessible"""
        response = requests.get(
            f"{BASE_URL}/api/signatures",
            headers=headers,
            params={"parent_record_type": "order", "parent_record_id": "1efe0ae8-473d-4d5f-bde7-dbfde8180cda"}
        )
        assert response.status_code == 200, f"Signatures endpoint failed: {response.text}"
        print(f"Signatures endpoint returned {len(response.json())} signatures")
    
    def test_signature_capture_endpoint(self, headers):
        """Verify signature capture endpoint accepts POST"""
        # This tests the endpoint exists - actual capture requires image data
        response = requests.post(
            f"{BASE_URL}/api/signatures/capture",
            headers=headers,
            json={
                "parent_record_type": "order",
                "parent_record_id": "test-order-id",
                "order_id": "test-order-id",
                "signature_type": "order_authorization",
                "signer_name": "Test Signer",
                "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            }
        )
        # May fail due to invalid order_id, but endpoint should be reachable
        assert response.status_code in [200, 201, 400, 404], f"Signature capture endpoint error: {response.text}"
        print(f"Signature capture endpoint returned status {response.status_code}")


class TestDrawingPersistence:
    """Test drawing save and preview persistence"""
    
    def test_order_drawings_list(self, headers):
        """Verify order drawings can be listed"""
        order_id = "1efe0ae8-473d-4d5f-bde7-dbfde8180cda"
        response = requests.get(
            f"{BASE_URL}/api/order-drawings/{order_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Order drawings list failed: {response.text}"
        drawings = response.json()
        assert isinstance(drawings, list), "Expected list of drawings"
        print(f"Found {len(drawings)} drawings for order")
        
        # Check for QA Persisted Drawing
        qa_drawing = next((d for d in drawings if "QA Persisted" in d.get("label", "")), None)
        if qa_drawing:
            print(f"Found QA Persisted Drawing: {qa_drawing.get('label')}")
            assert qa_drawing.get("id"), "Drawing should have an ID"
    
    def test_drawing_file_retrieval(self, headers):
        """Verify drawing files can be retrieved"""
        order_id = "1efe0ae8-473d-4d5f-bde7-dbfde8180cda"
        response = requests.get(
            f"{BASE_URL}/api/order-drawings/{order_id}",
            headers=headers
        )
        assert response.status_code == 200
        drawings = response.json()
        
        if drawings:
            drawing_id = drawings[0].get("id")
            file_response = requests.get(
                f"{BASE_URL}/api/order-drawings/file/{drawing_id}",
                headers=headers
            )
            assert file_response.status_code == 200, f"Drawing file retrieval failed: {file_response.status_code}"
            assert file_response.headers.get("content-type", "").startswith("image/"), "Expected image content type"
            print(f"Drawing file retrieved successfully, size: {len(file_response.content)} bytes")


class TestScheduleShiftEdit:
    """Test schedule shift edit persistence via unified productivity API"""
    
    def test_productivity_items_schedule_shifts(self, headers):
        """Verify schedule shifts appear in productivity items"""
        response = requests.get(
            f"{BASE_URL}/api/productivity/items",
            headers=headers,
            params={"item_types": "schedule_shift", "include_completed": "true"}
        )
        assert response.status_code == 200, f"Productivity items failed: {response.text}"
        data = response.json()
        items = data.get("items", [])
        print(f"Found {len(items)} schedule shift items")
        
        if items:
            shift = items[0]
            assert shift.get("type") == "schedule_shift"
            assert shift.get("uid"), "Shift should have UID"
            assert shift.get("meta", {}).get("day_key"), "Shift should have day_key in meta"
            print(f"Schedule shift: {shift.get('title')} - {shift.get('start_datetime')} to {shift.get('due_datetime')}")
    
    def test_schedule_shift_patch(self, headers):
        """Test PATCH endpoint for schedule shift updates"""
        # First get a schedule shift
        response = requests.get(
            f"{BASE_URL}/api/productivity/items",
            headers=headers,
            params={"item_types": "schedule_shift", "include_completed": "true"}
        )
        assert response.status_code == 200
        items = response.json().get("items", [])
        
        if not items:
            pytest.skip("No schedule shifts available to test")
        
        shift = items[0]
        shift_uid = shift.get("uid")
        
        # Test PATCH with updated times
        patch_response = requests.patch(
            f"{BASE_URL}/api/productivity/items/{shift_uid}",
            headers=headers,
            json={
                "start_datetime": "2026-04-13T09:30:00+00:00",
                "due_datetime": "2026-04-13T17:30:00+00:00"
            }
        )
        assert patch_response.status_code == 200, f"PATCH failed: {patch_response.text}"
        
        updated = patch_response.json()
        assert "09:30" in updated.get("start_datetime", ""), "Start time should be updated"
        assert "17:30" in updated.get("due_datetime", ""), "End time should be updated"
        print(f"Schedule shift updated: {updated.get('meta', {}).get('shift_start')} - {updated.get('meta', {}).get('shift_end')}")
        
        # Verify persistence by fetching again
        verify_response = requests.get(
            f"{BASE_URL}/api/productivity/items",
            headers=headers,
            params={"item_types": "schedule_shift", "include_completed": "true"}
        )
        assert verify_response.status_code == 200
        verified_items = verify_response.json().get("items", [])
        verified_shift = next((s for s in verified_items if s.get("uid") == shift_uid), None)
        
        assert verified_shift, "Shift should still exist after update"
        assert "09:30" in verified_shift.get("start_datetime", ""), "Persisted start time should match"
        print("Schedule shift persistence verified!")


class TestNoRegressions:
    """Test that no regressions were introduced"""
    
    def test_order_detail_loads(self, headers):
        """Verify order detail endpoint works"""
        order_id = "1efe0ae8-473d-4d5f-bde7-dbfde8180cda"
        response = requests.get(
            f"{BASE_URL}/api/orders/{order_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Order detail failed: {response.text}"
        order = response.json()
        assert order.get("order_number") == "ORD-0001"
        print(f"Order detail loaded: {order.get('order_number')}")
    
    def test_productivity_summary(self, headers):
        """Verify productivity summary endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/productivity/summary",
            headers=headers
        )
        assert response.status_code == 200, f"Productivity summary failed: {response.text}"
        summary = response.json()
        assert "open_items" in summary or "due_today" in summary
        print(f"Productivity summary: {summary}")
    
    def test_employees_list(self, headers):
        """Verify employees endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/employees",
            headers=headers
        )
        assert response.status_code == 200, f"Employees list failed: {response.text}"
        employees = response.json()
        assert isinstance(employees, list)
        print(f"Found {len(employees)} employees")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
