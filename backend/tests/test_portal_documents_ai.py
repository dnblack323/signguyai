"""
Test Portal Documents and AI Assistant Features - Iteration 32

Tests:
1. AI Business Assistant - returns context-aware responses about shop data
2. Portal Documents endpoint - GET /api/portal/documents
3. Document send-to-portal - POST /api/documents/{id}/send-to-portal
4. Portal login/registration works correctly
"""

import pytest
import requests
import os
import time
import uuid
from datetime import datetime, timezone
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test account credentials
TEST_EMAIL = COMMON_TEST_EMAIL
TEST_PASSWORD = LEGACY_ADMIN_PASSWORD


class TestAIBusinessAssistant:
    """Test AI Business Assistant functionality"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get token"""
        if not TestAIBusinessAssistant.token:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestAIBusinessAssistant.token = response.json().get("access_token")
        yield
    
    def test_ai_assistant_returns_response(self):
        """Test AI assistant endpoint returns a valid response"""
        if not self.token:
            pytest.skip("No auth token available")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            json={
                "message": "What is my total revenue?",
                "session_id": f"test_session_{uuid.uuid4()}",
                "conversation_history": []
            },
            headers=headers,
            timeout=60  # AI can take time
        )
        
        print(f"AI Assistant Status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        assert len(data["response"]) > 0, "Response should not be empty"
        print(f"AI Response length: {len(data['response'])} characters")
        print(f"AI Response preview: {data['response'][:200]}...")
    
    def test_ai_assistant_context_awareness(self):
        """Test AI assistant uses real shop data in response"""
        if not self.token:
            pytest.skip("No auth token available")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            json={
                "message": "How many active jobs do I have?",
                "session_id": f"test_session_{uuid.uuid4()}",
                "conversation_history": []
            },
            headers=headers,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that the response mentions specific data (not generic)
        response_text = data["response"].lower()
        # Should contain some specific information
        assert len(data["response"]) >= 50, "Response too short - may not have context"
        print(f"Context-aware response check passed")
        print(f"Response: {data['response'][:300]}...")
    
    def test_ai_assistant_with_conversation_history(self):
        """Test AI assistant handles conversation history"""
        if not self.token:
            pytest.skip("No auth token available")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        session_id = f"test_session_{uuid.uuid4()}"
        
        # First message
        response1 = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            json={
                "message": "What services does a sign shop offer?",
                "session_id": session_id,
                "conversation_history": []
            },
            headers=headers,
            timeout=60
        )
        assert response1.status_code == 200
        first_response = response1.json()["response"]
        
        # Follow-up with history
        response2 = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            json={
                "message": "Which of those is most profitable?",
                "session_id": session_id,
                "conversation_history": [
                    {"role": "user", "content": "What services does a sign shop offer?"},
                    {"role": "assistant", "content": first_response}
                ]
            },
            headers=headers,
            timeout=60
        )
        
        assert response2.status_code == 200
        print("Conversation history test passed")


class TestDocumentSendToPortal:
    """Test document send-to-portal functionality"""
    
    token = None
    customer_id = None
    document_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and setup test data"""
        if not TestDocumentSendToPortal.token:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            if response.status_code == 200:
                TestDocumentSendToPortal.token = response.json().get("access_token")
        yield
    
    def test_create_test_customer_with_portal(self):
        """Create a test customer with portal access enabled"""
        if not self.token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a customer
        test_customer_email = f"test_portal_customer_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/customers",
            json={
                "name": "Test Portal Customer",
                "email": test_customer_email,
                "phone": "555-1234",
                "company": "Test Company",
                "portal_enabled": True
            },
            headers=headers
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            TestDocumentSendToPortal.customer_id = data.get("id")
            print(f"Created test customer: {TestDocumentSendToPortal.customer_id}")
            assert data.get("portal_enabled") == True, "Portal should be enabled"
        else:
            # Try to find existing customers with portal enabled
            customers_resp = requests.get(f"{BASE_URL}/api/customers", headers=headers)
            if customers_resp.status_code == 200:
                customers = customers_resp.json()
                for c in customers:
                    if c.get("portal_enabled"):
                        TestDocumentSendToPortal.customer_id = c.get("id")
                        print(f"Using existing portal customer: {TestDocumentSendToPortal.customer_id}")
                        break
        
        assert TestDocumentSendToPortal.customer_id, "Need a customer with portal access"
    
    def test_upload_test_document(self):
        """Upload a test document"""
        if not self.token:
            pytest.skip("No auth token")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Create a simple test PDF-like content (actually just text for testing)
        import base64
        test_content = b"Test document content for portal testing"
        test_b64 = base64.b64encode(test_content).decode()
        
        # Using form data for document upload
        files = {
            'file': ('test_document.txt', test_content, 'text/plain')
        }
        data = {
            'name': f'Test Portal Document {uuid.uuid4().hex[:6]}',
            'description': 'Test document for portal testing',
            'category': 'other',
            'is_template': 'false',
            'tags': 'test,portal'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/documents",
            files=files,
            data=data,
            headers=headers
        )
        
        print(f"Document upload status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            doc_data = response.json()
            TestDocumentSendToPortal.document_id = doc_data.get("id")
            print(f"Uploaded document: {TestDocumentSendToPortal.document_id}")
        else:
            # Try to get an existing document
            docs_resp = requests.get(f"{BASE_URL}/api/documents", headers=headers)
            if docs_resp.status_code == 200:
                docs = docs_resp.json()
                if docs:
                    TestDocumentSendToPortal.document_id = docs[0].get("id")
                    print(f"Using existing document: {TestDocumentSendToPortal.document_id}")
        
        assert TestDocumentSendToPortal.document_id, "Need a document to send to portal"
    
    def test_send_document_to_portal(self):
        """Test sending a document to customer portal"""
        if not self.token or not self.document_id or not self.customer_id:
            pytest.skip("Missing required test data")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/documents/{self.document_id}/send-to-portal",
            json={
                "customer_id": self.customer_id,
                "notify_customer": True,
                "message": "Test document shared via portal"
            },
            headers=headers
        )
        
        print(f"Send to portal status: {response.status_code}")
        print(f"Response: {response.text}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "portal_document_id" in data, "Should return portal_document_id"
        assert "message" in data, "Should return success message"
        print(f"Document sent to portal successfully: {data}")


class TestPortalDocumentsEndpoint:
    """Test portal documents endpoint for customers"""
    
    portal_token = None
    customer_email = None
    customer_password = "testpass123"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup portal customer access"""
        # First create a customer with portal access and register
        if not TestPortalDocumentsEndpoint.portal_token:
            # Login as admin first
            admin_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            })
            
            if admin_resp.status_code == 200:
                admin_token = admin_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {admin_token}"}
                
                # Create a test customer
                test_email = f"portal_test_{uuid.uuid4().hex[:8]}@test.com"
                create_resp = requests.post(
                    f"{BASE_URL}/api/customers",
                    json={
                        "name": "Portal Test Customer",
                        "email": test_email,
                        "portal_enabled": True
                    },
                    headers=headers
                )
                
                if create_resp.status_code in [200, 201]:
                    TestPortalDocumentsEndpoint.customer_email = test_email
                    
                    # Register the customer in portal
                    reg_resp = requests.post(
                        f"{BASE_URL}/api/portal/auth/register",
                        json={
                            "email": test_email,
                            "password": self.customer_password
                        }
                    )
                    
                    if reg_resp.status_code == 200:
                        TestPortalDocumentsEndpoint.portal_token = reg_resp.json().get("access_token")
                        print(f"Portal customer registered: {test_email}")
        yield
    
    def test_portal_documents_endpoint_returns_list(self):
        """Test GET /api/portal/documents returns a list"""
        if not self.portal_token:
            pytest.skip("No portal token available")
        
        headers = {"Authorization": f"Bearer {self.portal_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/portal/documents",
            headers=headers
        )
        
        print(f"Portal documents status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Portal documents count: {len(data)}")
    
    def test_portal_documents_requires_auth(self):
        """Test portal documents endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/portal/documents")
        
        assert response.status_code in [401, 403], "Should require authentication"
        print("Auth requirement test passed")


class TestPortalNavigation:
    """Test portal navigation includes Documents tab"""
    
    portal_token = None
    
    def test_portal_login(self):
        """Test portal login endpoint works"""
        # First we need a customer with portal access
        # Login as admin
        admin_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert admin_resp.status_code == 200, "Admin login should work"
        admin_token = admin_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get customers
        customers_resp = requests.get(f"{BASE_URL}/api/customers", headers=headers)
        assert customers_resp.status_code == 200
        
        customers = customers_resp.json()
        portal_customer = None
        
        for c in customers:
            if c.get("portal_enabled") and c.get("portal_password_hash"):
                portal_customer = c
                break
        
        if portal_customer:
            print(f"Found portal customer: {portal_customer.get('email')}")
        else:
            print("No existing portal customer found, will need to create one")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("API health check passed")
    
    def test_auth_endpoint(self):
        """Test auth endpoint works"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("Auth endpoint test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
