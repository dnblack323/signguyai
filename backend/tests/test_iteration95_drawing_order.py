"""
Iteration 95 - Drawing and Order Entry Tests
Tests for drawing API, new order form, and add ticket to order features
"""
import pytest
import requests
import base64
import os
import struct
import zlib

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ops-command-center-77.preview.emergentagent.com')


class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("email") == "signguypa@gmail.com"


class TestDrawingAPI:
    """Drawing API tests - verifies backend accepts drawings correctly"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_order(self, headers):
        """Create a test order for drawing tests"""
        response = requests.post(f"{BASE_URL}/api/orders", json={
            "customer_name": "TEST_Drawing_Customer",
            "order_source": "phone"
        }, headers=headers)
        assert response.status_code == 200
        order_id = response.json().get("id")
        yield order_id
        # Cleanup
        requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=headers)
    
    def create_test_png(self, width, height):
        """Create a simple PNG with a diagonal line"""
        raw_data = []
        for y in range(height):
            raw_data.append(0)  # Filter byte
            for x in range(width):
                if abs(x - y) < 3:
                    raw_data.extend([0, 0, 0, 255])  # Black pixel
                else:
                    raw_data.extend([255, 255, 255, 255])  # White pixel
        
        raw_bytes = bytes(raw_data)
        compressed = zlib.compress(raw_bytes, 9)
        
        def png_chunk(chunk_type, data):
            chunk = chunk_type + data
            crc = zlib.crc32(chunk) & 0xffffffff
            return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)
        
        png = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
        png += png_chunk(b'IHDR', ihdr_data)
        png += png_chunk(b'IDAT', compressed)
        png += png_chunk(b'IEND', b'')
        
        return png
    
    def test_drawing_api_accepts_small_valid_drawing(self, headers, test_order):
        """Test that backend accepts small but valid drawings (>150 bytes)"""
        # Create a 50x50 PNG (should be ~314 bytes)
        png_data = self.create_test_png(50, 50)
        b64_data = base64.b64encode(png_data).decode()
        
        response = requests.post(f"{BASE_URL}/api/order-drawings/", json={
            "order_id": test_order,
            "drawing_type": "sketch",
            "title": "TEST_Small_Drawing",
            "image_data": f"data:image/png;base64,{b64_data}",
            "status": "saved"
        }, headers=headers)
        
        assert response.status_code == 200, f"Small drawing rejected: {response.text}"
        data = response.json()
        assert data.get("id") is not None
        assert data.get("order_id") == test_order
    
    def test_drawing_api_accepts_medium_drawing(self, headers, test_order):
        """Test that backend accepts medium-sized drawings"""
        # Create a 200x200 PNG
        png_data = self.create_test_png(200, 200)
        b64_data = base64.b64encode(png_data).decode()
        
        response = requests.post(f"{BASE_URL}/api/order-drawings/", json={
            "order_id": test_order,
            "drawing_type": "sketch",
            "title": "TEST_Medium_Drawing",
            "image_data": f"data:image/png;base64,{b64_data}",
            "status": "saved"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("id") is not None
    
    def test_drawing_api_accepts_large_drawing(self, headers, test_order):
        """Test that backend accepts larger drawings"""
        # Create a 400x300 PNG
        png_data = self.create_test_png(400, 300)
        b64_data = base64.b64encode(png_data).decode()
        
        response = requests.post(f"{BASE_URL}/api/order-drawings/", json={
            "order_id": test_order,
            "drawing_type": "sketch",
            "title": "TEST_Large_Drawing",
            "image_data": f"data:image/png;base64,{b64_data}",
            "status": "saved"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("id") is not None
    
    def test_drawing_api_list_drawings(self, headers, test_order):
        """Test listing drawings for an order"""
        response = requests.get(f"{BASE_URL}/api/order-drawings/{test_order}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least the drawings we created
        assert len(data) >= 1


class TestOrderAPI:
    """Order API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_create_order(self, headers):
        """Test creating a new order"""
        response = requests.post(f"{BASE_URL}/api/orders", json={
            "customer_name": "TEST_Order_Customer",
            "order_source": "phone",
            "internal_notes": "Test order for iteration 95"
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("id") is not None
        assert data.get("customer_name") == "TEST_Order_Customer"
        
        # Cleanup
        order_id = data.get("id")
        requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=headers)
    
    def test_get_existing_order(self, headers):
        """Test getting an existing order"""
        # Use the smoke test order
        order_id = "12bb5a34-23bd-4ae0-8802-b839cbbb681c"
        response = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("id") == order_id


class TestJobTicketAPI:
    """Job Ticket API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    @pytest.fixture(scope="class")
    def test_order(self, headers):
        """Create a test order for ticket tests"""
        response = requests.post(f"{BASE_URL}/api/orders", json={
            "customer_name": "TEST_Ticket_Customer",
            "order_source": "phone"
        }, headers=headers)
        assert response.status_code == 200
        order_id = response.json().get("id")
        yield order_id
        # Cleanup
        requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=headers)
    
    def test_create_job_ticket(self, headers, test_order):
        """Test creating a job ticket for an order"""
        response = requests.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": test_order,
            "item_name": "TEST_Banner_3x8",
            "item_category": "banners",
            "quantity": 2,
            "priority": "normal",
            "estimated_price": 150.00
        }, headers=headers)
        
        assert response.status_code in [200, 201], f"Failed to create ticket: {response.text}"
        data = response.json()
        assert data.get("id") is not None
        assert data.get("item_name") == "TEST_Banner_3x8"
        assert data.get("order_id") == test_order
    
    def test_create_detailed_job_ticket(self, headers, test_order):
        """Test creating a detailed job ticket with specs"""
        response = requests.post(f"{BASE_URL}/api/job-tickets", json={
            "order_id": test_order,
            "item_name": "TEST_Detailed_Sign",
            "item_category": "rigid_signs",
            "quantity": 1,
            "priority": "high",
            "estimated_price": 250.00,
            "specs": {
                "width": 48,
                "height": 36,
                "material": "aluminum",
                "thickness": "10mm"
            },
            "special_instructions": "Rush order - needs by Friday"
        }, headers=headers)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("id") is not None
        assert data.get("specs", {}).get("width") == 48


class TestPricingAPI:
    """Pricing API tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "signguypa@gmail.com",
            "password": "Billnel323"
        })
        assert response.status_code == 200
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    def test_pricing_calculator_endpoint(self, headers):
        """Test pricing calculator endpoint"""
        response = requests.post(f"{BASE_URL}/api/pricing/calculate", json={
            "category": "banners",
            "specs": {
                "width": 36,
                "height": 96,
                "material": "13oz_vinyl"
            },
            "quantity": 1
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total" in data or "price" in data or "estimated_price" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
