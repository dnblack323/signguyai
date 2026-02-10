"""
Customer Portal API Tests
Tests for portal login, registration, dashboard, orders, quotes, invoices, 
messages, proofs, appointments, and profile management.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
TEST_PORTAL_CUSTOMER = {
    "email": "johndoe@example.com",
    "password": "portal123",
    "name": "John Doe"
}

TEST_SHOP_USER = {
    "email": "testowner@example.com",
    "password": "test123"
}


class TestPortalAuth:
    """Portal Authentication Tests"""
    
    def test_portal_login_success(self):
        """Test successful portal login with existing customer"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        print(f"Portal login response: {response.status_code} - {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "customer_id" in data
        assert "customer_name" in data
        assert data["customer_name"] == TEST_PORTAL_CUSTOMER["name"]
        print(f"✅ Portal login successful for {data['customer_name']}")
    
    def test_portal_login_invalid_password(self):
        """Test portal login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✅ Portal login correctly rejects invalid password")
    
    def test_portal_login_nonexistent_email(self):
        """Test portal login with non-existent email"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "anypassword"
        })
        assert response.status_code == 401
        print("✅ Portal login correctly rejects non-existent email")
    
    def test_portal_register_already_registered(self):
        """Test registration for already registered customer"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/register", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": "newpassword123"
        })
        # Should fail because already registered
        assert response.status_code == 400
        print("✅ Portal registration correctly rejects already registered customer")


class TestPortalProfile:
    """Portal Profile Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_profile(self, portal_token):
        """Test getting customer profile"""
        response = requests.get(
            f"{BASE_URL}/api/portal/profile",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "email" in data
        assert data["email"] == TEST_PORTAL_CUSTOMER["email"]
        # Should not contain password hash
        assert "portal_password_hash" not in data
        print(f"✅ Profile retrieved: {data['name']}")
    
    def test_update_profile(self, portal_token):
        """Test updating customer profile"""
        response = requests.put(
            f"{BASE_URL}/api/portal/profile",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={
                "phone": "(555) 123-4567"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "(555) 123-4567"
        print("✅ Profile updated successfully")
    
    def test_update_tax_exempt_status(self, portal_token):
        """Test updating tax exempt status"""
        response = requests.put(
            f"{BASE_URL}/api/portal/profile",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={
                "is_tax_exempt": True,
                "tax_exempt_document_url": "https://example.com/tax-cert.pdf"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_tax_exempt"] == True
        print("✅ Tax exempt status updated")
    
    def test_profile_without_auth(self):
        """Test profile access without authentication"""
        response = requests.get(f"{BASE_URL}/api/portal/profile")
        assert response.status_code == 401
        print("✅ Profile correctly requires authentication")


class TestPortalDashboard:
    """Portal Dashboard Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_dashboard(self, portal_token):
        """Test getting dashboard data"""
        response = requests.get(
            f"{BASE_URL}/api/portal/dashboard",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check stats structure
        assert "stats" in data
        stats = data["stats"]
        assert "total_quotes" in stats
        assert "active_jobs" in stats
        assert "pending_invoices" in stats
        assert "pending_proofs" in stats
        assert "unread_messages" in stats
        assert "unread_notifications" in stats
        
        # Check other dashboard data
        assert "upcoming_appointments" in data
        assert "recent_jobs" in data
        assert "recent_invoices" in data
        
        print(f"✅ Dashboard data retrieved - Stats: {stats}")


class TestPortalOrders:
    """Portal Orders (Jobs) Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_orders(self, portal_token):
        """Test getting customer orders"""
        response = requests.get(
            f"{BASE_URL}/api/portal/orders",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Orders retrieved: {len(data)} orders")
    
    def test_get_orders_with_status_filter(self, portal_token):
        """Test getting orders with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/portal/orders?status=in_production",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        print("✅ Orders with status filter works")


class TestPortalQuotes:
    """Portal Quotes Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_quotes(self, portal_token):
        """Test getting customer quotes"""
        response = requests.get(
            f"{BASE_URL}/api/portal/quotes",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Quotes retrieved: {len(data)} quotes")
    
    def test_get_quotes_with_status_filter(self, portal_token):
        """Test getting quotes with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/portal/quotes?status=sent",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        print("✅ Quotes with status filter works")


class TestPortalInvoices:
    """Portal Invoices Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_invoices(self, portal_token):
        """Test getting customer invoices"""
        response = requests.get(
            f"{BASE_URL}/api/portal/invoices",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Invoices retrieved: {len(data)} invoices")
    
    def test_get_invoices_with_status_filter(self, portal_token):
        """Test getting invoices with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/portal/invoices?status=sent",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        print("✅ Invoices with status filter works")


class TestPortalMessages:
    """Portal Messaging Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_conversations(self, portal_token):
        """Test getting customer conversations"""
        response = requests.get(
            f"{BASE_URL}/api/portal/conversations",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Conversations retrieved: {len(data)} conversations")
    
    def test_create_conversation(self, portal_token):
        """Test creating a new conversation"""
        response = requests.post(
            f"{BASE_URL}/api/portal/conversations",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={
                "subject": "Test Question",
                "message": "This is a test message from the portal."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["subject"] == "Test Question"
        print(f"✅ Conversation created: {data['id']}")
        return data["id"]
    
    def test_get_conversation_messages(self, portal_token):
        """Test getting messages in a conversation"""
        # First create a conversation
        create_response = requests.post(
            f"{BASE_URL}/api/portal/conversations",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={
                "subject": "Test for Messages",
                "message": "Initial message"
            }
        )
        if create_response.status_code != 200:
            pytest.skip("Could not create conversation")
        
        conv_id = create_response.json()["id"]
        
        # Get messages
        response = requests.get(
            f"{BASE_URL}/api/portal/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "conversation" in data
        assert "messages" in data
        assert len(data["messages"]) >= 1
        print(f"✅ Messages retrieved: {len(data['messages'])} messages")
    
    def test_send_message(self, portal_token):
        """Test sending a message in a conversation"""
        # First create a conversation
        create_response = requests.post(
            f"{BASE_URL}/api/portal/conversations",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={
                "subject": "Test for Sending",
                "message": "Initial message"
            }
        )
        if create_response.status_code != 200:
            pytest.skip("Could not create conversation")
        
        conv_id = create_response.json()["id"]
        
        # Send a message
        response = requests.post(
            f"{BASE_URL}/api/portal/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={
                "content": "This is a follow-up message"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "This is a follow-up message"
        print("✅ Message sent successfully")


class TestPortalProofs:
    """Portal Artwork Proofs Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_proofs(self, portal_token):
        """Test getting customer proofs"""
        response = requests.get(
            f"{BASE_URL}/api/portal/proofs",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Proofs retrieved: {len(data)} proofs")
    
    def test_get_proofs_with_status_filter(self, portal_token):
        """Test getting proofs with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/portal/proofs?status=pending",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        print("✅ Proofs with status filter works")


class TestPortalAppointments:
    """Portal Appointments Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_appointments(self, portal_token):
        """Test getting customer appointments"""
        response = requests.get(
            f"{BASE_URL}/api/portal/appointments",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Appointments retrieved: {len(data)} appointments")
    
    def test_get_upcoming_appointments(self, portal_token):
        """Test getting upcoming appointments only"""
        response = requests.get(
            f"{BASE_URL}/api/portal/appointments?upcoming_only=true",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        print("✅ Upcoming appointments filter works")


class TestPortalNotifications:
    """Portal Notifications Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_notifications(self, portal_token):
        """Test getting customer notifications"""
        response = requests.get(
            f"{BASE_URL}/api/portal/notifications",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ Notifications retrieved: {len(data)} notifications")
    
    def test_get_unread_notifications(self, portal_token):
        """Test getting unread notifications only"""
        response = requests.get(
            f"{BASE_URL}/api/portal/notifications?unread_only=true",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        print("✅ Unread notifications filter works")
    
    def test_mark_all_read(self, portal_token):
        """Test marking all notifications as read"""
        response = requests.put(
            f"{BASE_URL}/api/portal/notifications/read-all",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        print("✅ Mark all notifications read works")


class TestPortalPasswordChange:
    """Portal Password Change Tests"""
    
    @pytest.fixture
    def portal_token(self):
        """Get portal auth token"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": TEST_PORTAL_CUSTOMER["email"],
            "password": TEST_PORTAL_CUSTOMER["password"]
        })
        if response.status_code != 200:
            pytest.skip(f"Portal login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_change_password_wrong_current(self, portal_token):
        """Test password change with wrong current password"""
        response = requests.put(
            f"{BASE_URL}/api/portal/change-password",
            headers={"Authorization": f"Bearer {portal_token}"},
            params={
                "current_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )
        assert response.status_code == 400
        print("✅ Password change correctly rejects wrong current password")
    
    def test_change_password_too_short(self, portal_token):
        """Test password change with too short new password"""
        response = requests.put(
            f"{BASE_URL}/api/portal/change-password",
            headers={"Authorization": f"Bearer {portal_token}"},
            params={
                "current_password": TEST_PORTAL_CUSTOMER["password"],
                "new_password": "short"
            }
        )
        assert response.status_code == 400
        print("✅ Password change correctly rejects short password")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
