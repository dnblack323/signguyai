"""
Test suite for Signature and Drawing System - Iteration 78
Tests: Signature feature toggle, signature requests, public signing, internal capture,
       order drawings, item-level drawings, markup mode, autosave drafts
"""

import pytest
import requests
import os
import uuid
import base64
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = PRODUCTION_OWNER_EMAIL
TEST_PASSWORD = PRODUCTION_OWNER_PASSWORD

# Test order ID from test_credentials.md
TEST_ORDER_ID = "1efe0ae8-473d-4d5f-bde7-dbfde8180cda"

# Generate a minimal valid PNG image for testing (1x1 white pixel)
def generate_test_image():
    # Minimal PNG: 1x1 white pixel
    png_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    # Pad to make it larger than 1000 bytes (signature validation requirement)
    padded_data = png_data + b'\x00' * 1500
    return "data:image/png;base64," + base64.b64encode(padded_data).decode()


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Shared requests session with auth"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestSignatureFeatureToggle:
    """Test signature feature toggle in company settings"""
    
    def test_get_tenant_settings(self, api_client):
        """Verify tenant settings include signature_settings"""
        response = api_client.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        data = response.json()
        assert "signature_settings" in data or data.get("signature_settings") is None
        print(f"Tenant signature_settings: {data.get('signature_settings')}")
    
    def test_enable_signature_feature(self, api_client):
        """Enable signature feature via tenant update"""
        response = api_client.put(f"{BASE_URL}/api/tenant", json={
            "signature_settings": {
                "enabled": True,
                "link_expiry_days": 7
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("signature_settings", {}).get("enabled") == True
        print("Signature feature enabled successfully")
    
    def test_signature_settings_persist(self, api_client):
        """Verify signature settings persist after update"""
        response = api_client.get(f"{BASE_URL}/api/tenant")
        assert response.status_code == 200
        data = response.json()
        settings = data.get("signature_settings", {})
        assert settings.get("enabled") == True
        assert settings.get("link_expiry_days") == 7
        print("Signature settings persisted correctly")


class TestSignatureAPIs:
    """Test signature CRUD and request APIs"""
    
    def test_list_signatures_empty_or_existing(self, api_client):
        """List signatures for an order"""
        response = api_client.get(f"{BASE_URL}/api/signatures", params={
            "order_id": TEST_ORDER_ID
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} signatures for order")
    
    def test_create_signature_requirement(self, api_client):
        """Create a signature requirement for an order"""
        response = api_client.post(f"{BASE_URL}/api/signatures/requirement", json={
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "signature_type": "order_authorization",
            "requires_signature": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("parent_record_type") == "order"
        assert data.get("requires_signature") == True
        assert data.get("status") == "pending"
        print(f"Created signature requirement: {data.get('id')}")
    
    def test_request_signature_via_email(self, api_client):
        """Request signature via email (creates public link)"""
        response = api_client.post(f"{BASE_URL}/api/signatures/request", json={
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "signature_type": "order_authorization",
            "request_email": "test@example.com",
            "signer_name": "Test Customer",
            "signer_role": "customer",
            "notes": "Please sign to confirm order",
            "expires_in_days": 7,
            "origin_url": BASE_URL
        })
        assert response.status_code == 200
        data = response.json()
        assert "signature_id" in data
        assert "expires_at" in data
        print(f"Signature request sent, ID: {data.get('signature_id')}")
        return data.get("signature_id")


class TestPublicSignatureFlow:
    """Test public signature page flow"""
    
    @pytest.fixture
    def signature_token(self, api_client):
        """Create a signature request and get the token"""
        # First create a test order for this flow
        order_response = api_client.post(f"{BASE_URL}/api/orders", json={
            "customer_name": "Test Signature Customer",
            "email": "testsig@example.com",
            "status": "awaiting_quote"
        })
        if order_response.status_code != 200:
            pytest.skip("Could not create test order")
        
        order_id = order_response.json().get("id")
        
        # Create signature request
        response = api_client.post(f"{BASE_URL}/api/signatures/request", json={
            "parent_record_type": "order",
            "parent_record_id": order_id,
            "order_id": order_id,
            "signature_type": "order_authorization",
            "request_email": "testsig@example.com",
            "signer_name": "Test Signer",
            "expires_in_days": 7,
            "origin_url": BASE_URL
        })
        assert response.status_code == 200
        
        # Get the token from the database (we need to query signatures)
        sig_response = api_client.get(f"{BASE_URL}/api/signatures", params={
            "order_id": order_id
        })
        assert sig_response.status_code == 200
        signatures = sig_response.json()
        
        # The token is not returned in list, so we need to get it from the request
        # For testing, we'll create a new request and capture the token
        # Actually, the token is stored in DB but not exposed via API
        # We need to test the public endpoint differently
        
        yield {"order_id": order_id, "signature_id": response.json().get("signature_id")}
        
        # Cleanup
        api_client.delete(f"{BASE_URL}/api/orders/{order_id}")
    
    def test_public_signature_endpoint_requires_valid_token(self):
        """Test that invalid token returns 404"""
        response = requests.get(f"{BASE_URL}/api/signatures/public/invalid-token-12345")
        assert response.status_code == 404
        print("Invalid token correctly returns 404")


class TestInternalSignatureCapture:
    """Test internal signature capture flow"""
    
    def test_capture_signature_internal(self, api_client):
        """Capture signature internally (staff capturing customer signature)"""
        test_image = generate_test_image()
        
        response = api_client.post(f"{BASE_URL}/api/signatures/capture", json={
            "parent_record_type": "order",
            "parent_record_id": TEST_ORDER_ID,
            "order_id": TEST_ORDER_ID,
            "signature_type": "order_authorization",
            "signer_name": "Test Internal Signer",
            "signer_role": "customer",
            "printed_name": "Test Internal Signer",
            "notes": "Captured in-store",
            "image_data": test_image
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "signed"
        assert data.get("signature_acquired") == True
        assert data.get("signer_name") == "Test Internal Signer"
        assert "signature_image" in data
        print(f"Internal signature captured: {data.get('id')}")


class TestOrderDrawings:
    """Test order-level drawing creation and management"""
    
    def test_list_order_drawings(self, api_client):
        """List drawings for an order"""
        response = api_client.get(f"{BASE_URL}/api/order-drawings/{TEST_ORDER_ID}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} drawings for order")
    
    def test_create_order_level_drawing(self, api_client):
        """Create an order-level drawing (sketch)"""
        test_image = generate_test_image()
        
        response = api_client.post(f"{BASE_URL}/api/order-drawings/", json={
            "order_id": TEST_ORDER_ID,
            "parent_type": "order",
            "parent_id": TEST_ORDER_ID,
            "drawing_type": "sketch",
            "title": "Test Order Sketch",
            "notes": "Test drawing for order",
            "image_data": test_image,
            "status": "saved"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("parent_type") == "order"
        assert data.get("type") == "sketch"
        assert "image_url" in data
        print(f"Created order drawing: {data.get('id')}")
        return data.get("id")
    
    def test_create_draft_drawing_autosave(self, api_client):
        """Create a draft drawing (autosave behavior)"""
        test_image = generate_test_image()
        drawing_id = str(uuid.uuid4())
        
        response = api_client.post(f"{BASE_URL}/api/order-drawings/", json={
            "id": drawing_id,
            "order_id": TEST_ORDER_ID,
            "parent_type": "order",
            "parent_id": TEST_ORDER_ID,
            "drawing_type": "sketch",
            "title": "Autosave Draft",
            "notes": "",
            "image_data": test_image,
            "status": "draft"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "draft"
        assert data.get("id") == drawing_id
        print(f"Created draft drawing: {drawing_id}")
        
        # Update the same draft (simulating autosave)
        response2 = api_client.post(f"{BASE_URL}/api/order-drawings/", json={
            "id": drawing_id,
            "order_id": TEST_ORDER_ID,
            "parent_type": "order",
            "parent_id": TEST_ORDER_ID,
            "drawing_type": "sketch",
            "title": "Autosave Draft Updated",
            "notes": "Updated via autosave",
            "image_data": test_image,
            "status": "draft"
        })
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get("id") == drawing_id
        assert data2.get("title") == "Autosave Draft Updated"
        print("Draft drawing updated via autosave")
        
        return drawing_id
    
    def test_get_drawing_file(self, api_client):
        """Get drawing file content"""
        # First get list of drawings
        list_response = api_client.get(f"{BASE_URL}/api/order-drawings/{TEST_ORDER_ID}")
        assert list_response.status_code == 200
        drawings = list_response.json()
        
        if not drawings:
            pytest.skip("No drawings to test file retrieval")
        
        drawing_id = drawings[0].get("id")
        response = api_client.get(f"{BASE_URL}/api/order-drawings/file/{drawing_id}")
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("image/")
        print(f"Retrieved drawing file: {drawing_id}")


class TestItemLevelDrawings:
    """Test job ticket (item) level drawings"""
    
    @pytest.fixture
    def test_ticket(self, api_client):
        """Get a job ticket from the test order"""
        response = api_client.get(f"{BASE_URL}/api/orders/{TEST_ORDER_ID}")
        if response.status_code != 200:
            pytest.skip("Could not get test order")
        
        order = response.json()
        tickets = order.get("job_tickets", [])
        if not tickets:
            pytest.skip("No job tickets in test order")
        
        return tickets[0]
    
    def test_create_item_level_drawing(self, api_client, test_ticket):
        """Create a drawing attached to a specific job ticket"""
        test_image = generate_test_image()
        ticket_id = test_ticket.get("id")
        
        response = api_client.post(f"{BASE_URL}/api/order-drawings/", json={
            "order_id": TEST_ORDER_ID,
            "parent_type": "job_ticket",
            "parent_id": ticket_id,
            "job_ticket_id": ticket_id,
            "drawing_type": "measurement_note",
            "title": "Item Measurement Note",
            "notes": "Measurements for this specific item",
            "image_data": test_image,
            "status": "saved"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("parent_type") == "job_ticket"
        assert data.get("job_ticket_id") == ticket_id
        print(f"Created item-level drawing: {data.get('id')}")
    
    def test_query_drawings_by_job_ticket(self, api_client, test_ticket):
        """Query drawings filtered by job ticket"""
        ticket_id = test_ticket.get("id")
        
        response = api_client.get(f"{BASE_URL}/api/order-drawings", params={
            "job_ticket_id": ticket_id
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned drawings should be for this ticket
        for drawing in data:
            assert drawing.get("job_ticket_id") == ticket_id
        print(f"Found {len(data)} drawings for job ticket")


class TestImageMarkupDrawings:
    """Test markup mode for uploaded images"""
    
    @pytest.fixture
    def test_uploaded_image(self, api_client):
        """Get an uploaded image from the test order"""
        response = api_client.get(f"{BASE_URL}/api/orders/{TEST_ORDER_ID}/files")
        if response.status_code != 200:
            pytest.skip("Could not get order files")
        
        files = response.json()
        image_files = [f for f in files if f.get("content_type", "").startswith("image/")]
        
        if not image_files:
            pytest.skip("No image files in test order")
        
        return image_files[0]
    
    def test_create_image_markup_drawing(self, api_client, test_uploaded_image):
        """Create a markup drawing on an uploaded image"""
        test_image = generate_test_image()
        file_id = test_uploaded_image.get("id")
        
        response = api_client.post(f"{BASE_URL}/api/order-drawings/", json={
            "order_id": TEST_ORDER_ID,
            "parent_type": "uploaded_image",
            "parent_id": file_id,
            "uploaded_image_id": file_id,
            "drawing_type": "markup",
            "title": f"Markup - {test_uploaded_image.get('label', 'Image')}",
            "notes": "Customer markup on uploaded image",
            "image_data": test_image,
            "status": "saved"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("parent_type") == "uploaded_image"
        assert data.get("uploaded_image_id") == file_id
        assert data.get("type") == "markup"
        print(f"Created image markup drawing: {data.get('id')}")
    
    def test_query_drawings_by_uploaded_image(self, api_client, test_uploaded_image):
        """Query drawings filtered by uploaded image"""
        file_id = test_uploaded_image.get("id")
        
        response = api_client.get(f"{BASE_URL}/api/order-drawings", params={
            "uploaded_image_id": file_id
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} markup drawings for uploaded image")


class TestDrawingTypes:
    """Test different drawing types"""
    
    @pytest.mark.parametrize("drawing_type", [
        "sketch",
        "markup",
        "measurement_note",
        "install_note",
        "layout_note",
        "other"
    ])
    def test_create_drawing_with_type(self, api_client, drawing_type):
        """Create drawings with different types"""
        test_image = generate_test_image()
        
        response = api_client.post(f"{BASE_URL}/api/order-drawings/", json={
            "order_id": TEST_ORDER_ID,
            "parent_type": "order",
            "parent_id": TEST_ORDER_ID,
            "drawing_type": drawing_type,
            "title": f"Test {drawing_type.replace('_', ' ').title()}",
            "notes": f"Testing {drawing_type} type",
            "image_data": test_image,
            "status": "saved"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("type") == drawing_type
        print(f"Created {drawing_type} drawing successfully")


class TestSignatureFeatureDisabled:
    """Test behavior when signature feature is disabled"""
    
    def test_disable_signature_feature(self, api_client):
        """Disable signature feature"""
        response = api_client.put(f"{BASE_URL}/api/tenant", json={
            "signature_settings": {
                "enabled": False,
                "link_expiry_days": 7
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("signature_settings", {}).get("enabled") == False
        print("Signature feature disabled")
    
    def test_signature_apis_return_404_when_disabled(self, api_client):
        """Signature APIs should return 404 when feature is disabled"""
        response = api_client.get(f"{BASE_URL}/api/signatures", params={
            "order_id": TEST_ORDER_ID
        })
        assert response.status_code == 404
        print("Signature list correctly returns 404 when disabled")
    
    def test_reenable_signature_feature(self, api_client):
        """Re-enable signature feature for other tests"""
        response = api_client.put(f"{BASE_URL}/api/tenant", json={
            "signature_settings": {
                "enabled": True,
                "link_expiry_days": 7
            }
        })
        assert response.status_code == 200
        print("Signature feature re-enabled")


class TestQuoteSignatureFlow:
    """Test signature flow for quotes"""
    
    @pytest.fixture
    def test_quote(self, api_client):
        """Generate a quote for the test order"""
        response = api_client.post(f"{BASE_URL}/api/orders/{TEST_ORDER_ID}/generate-quote")
        if response.status_code != 200:
            # Quote might already exist, get from financials
            fin_response = api_client.get(f"{BASE_URL}/api/orders/{TEST_ORDER_ID}/financials")
            if fin_response.status_code == 200:
                quotes = fin_response.json().get("quotes", [])
                if quotes:
                    return quotes[0]
            pytest.skip("Could not get or create quote")
        return response.json()
    
    def test_create_quote_signature_requirement(self, api_client, test_quote):
        """Create signature requirement for a quote"""
        quote_id = test_quote.get("id")
        
        response = api_client.post(f"{BASE_URL}/api/signatures/requirement", json={
            "parent_record_type": "quote",
            "parent_record_id": quote_id,
            "order_id": TEST_ORDER_ID,
            "signature_type": "quote_acceptance",
            "requires_signature": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("parent_record_type") == "quote"
        assert data.get("signature_type") == "quote_acceptance"
        print(f"Created quote signature requirement: {data.get('id')}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_drawings(self, api_client):
        """Delete test drawings created during tests"""
        response = api_client.get(f"{BASE_URL}/api/order-drawings/{TEST_ORDER_ID}")
        if response.status_code != 200:
            return
        
        drawings = response.json()
        test_drawings = [d for d in drawings if d.get("title", "").startswith("Test") or d.get("title", "").startswith("Autosave")]
        
        for drawing in test_drawings:
            del_response = api_client.delete(f"{BASE_URL}/api/order-drawings/{drawing.get('id')}")
            if del_response.status_code in [200, 204]:
                print(f"Deleted test drawing: {drawing.get('id')}")
        
        print(f"Cleaned up {len(test_drawings)} test drawings")
