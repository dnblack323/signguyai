"""
Admin Portal Routes - Backend API Tests
Tests for the centralized communication hub for company owners:
- Dashboard stats (messages, approvals, documents)
- Conversations CRUD (create, list, get details, send messages)
- Artwork approval queue and send artwork
- Document sharing
- Helper endpoints (customers, jobs for dropdowns)
"""

import pytest
import requests
import uuid
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = LEGACY_ADMIN_EMAIL
TEST_PASSWORD = LEGACY_ADMIN_PASSWORD


class TestAdminPortalAuth:
    """Authentication and setup tests"""

    def test_login_success(self):
        """Test admin login to get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        return data["access_token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Could not authenticate: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestAdminPortalDashboard:
    """Dashboard endpoint tests - GET /api/admin-portal/dashboard"""

    def test_dashboard_returns_stats(self, auth_headers):
        """Test dashboard returns message counts, approval counts, document counts"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "messages" in data
        assert "approvals" in data
        assert "documents" in data
        
        # Verify messages structure
        assert "unread" in data["messages"]
        assert "total_active" in data["messages"]
        
        # Verify approvals structure
        assert "pending" in data["approvals"]
        assert "revision_requested" in data["approvals"]
        assert "recent_approved" in data["approvals"]
        
        # Verify documents structure
        assert "total_shared" in data["documents"]
        assert "unviewed" in data["documents"]
        
        print(f"Dashboard stats: {data}")

    def test_dashboard_requires_auth(self):
        """Test dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin-portal/dashboard")
        assert response.status_code == 401 or response.status_code == 403


class TestAdminPortalConversations:
    """Conversations endpoints tests"""

    def test_get_conversations_empty_or_list(self, auth_headers):
        """GET /api/admin-portal/conversations - Returns all conversations"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/conversations",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get conversations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} conversations")

    def test_get_conversations_with_filter(self, auth_headers):
        """GET /api/admin-portal/conversations with unread_only filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/conversations?unread_only=true",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get unread conversations failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


@pytest.fixture(scope="module")
def test_customer(auth_headers):
    """Get or create a test customer for conversation tests"""
    # First try to get existing customers
    response = requests.get(
        f"{BASE_URL}/api/admin-portal/customers",
        headers=auth_headers
    )
    if response.status_code == 200:
        customers = response.json()
        if customers:
            return customers[0]  # Return first customer
    
    # Create a test customer if none exist
    customer_data = {
        "name": f"TEST_Portal_Customer_{uuid.uuid4().hex[:6]}",
        "email": f"test_portal_{uuid.uuid4().hex[:6]}@example.com",
        "phone": "555-0123",
        "company": "Test Company"
    }
    response = requests.post(
        f"{BASE_URL}/api/customers",
        headers=auth_headers,
        json=customer_data
    )
    if response.status_code in [200, 201]:
        return response.json()
    
    pytest.skip("Could not get or create test customer")


class TestAdminPortalConversationsCRUD:
    """Conversation CRUD tests - requires test customer"""

    def test_create_conversation(self, auth_headers, test_customer):
        """POST /api/admin-portal/conversations - Create new conversation"""
        conversation_data = {
            "customer_id": test_customer["id"],
            "subject": f"TEST Conversation {uuid.uuid4().hex[:6]}",
            "content": "Hello, this is a test message from the admin portal."
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/conversations",
            headers=auth_headers,
            json=conversation_data
        )
        assert response.status_code == 200, f"Create conversation failed: {response.text}"
        data = response.json()
        
        assert "conversation_id" in data
        assert "message_id" in data
        assert data["message"] == "Conversation started"
        
        print(f"Created conversation: {data['conversation_id']}")
        return data["conversation_id"]

    def test_get_conversation_detail(self, auth_headers, test_customer):
        """GET /api/admin-portal/conversations/{id} - Get conversation with messages"""
        # First create a conversation
        conversation_data = {
            "customer_id": test_customer["id"],
            "subject": f"TEST Detail Conv {uuid.uuid4().hex[:6]}",
            "content": "Test message for detail view."
        }
        create_response = requests.post(
            f"{BASE_URL}/api/admin-portal/conversations",
            headers=auth_headers,
            json=conversation_data
        )
        assert create_response.status_code == 200
        conv_id = create_response.json()["conversation_id"]
        
        # Now get the conversation detail
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/conversations/{conv_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get conversation detail failed: {response.text}"
        data = response.json()
        
        assert "conversation" in data
        assert "messages" in data
        assert data["conversation"]["id"] == conv_id
        assert isinstance(data["messages"], list)
        assert len(data["messages"]) >= 1  # At least the initial message
        
        print(f"Conversation has {len(data['messages'])} messages")

    def test_send_message_in_conversation(self, auth_headers, test_customer):
        """POST /api/admin-portal/conversations/{id}/messages - Send message"""
        # First create a conversation
        conversation_data = {
            "customer_id": test_customer["id"],
            "subject": f"TEST Message Send {uuid.uuid4().hex[:6]}",
            "content": "Initial message."
        }
        create_response = requests.post(
            f"{BASE_URL}/api/admin-portal/conversations",
            headers=auth_headers,
            json=conversation_data
        )
        assert create_response.status_code == 200
        conv_id = create_response.json()["conversation_id"]
        
        # Send a follow-up message
        message_content = "This is a follow-up message via the API"
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/conversations/{conv_id}/messages?content={message_content}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Send message failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data["content"] == message_content
        assert data["sender_type"] == "shop"
        
        print(f"Message sent: {data['id']}")

    def test_get_conversation_not_found(self, auth_headers):
        """GET /api/admin-portal/conversations/{id} - Non-existent conversation returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/conversations/non_existent_id_12345",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_conversation_invalid_customer(self, auth_headers):
        """POST /api/admin-portal/conversations - Invalid customer returns 404"""
        conversation_data = {
            "customer_id": "invalid_customer_id_12345",
            "subject": "Test",
            "content": "Test message"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/conversations",
            headers=auth_headers,
            json=conversation_data
        )
        assert response.status_code == 404


class TestAdminPortalArtwork:
    """Artwork approval queue tests"""

    def test_get_artwork_queue(self, auth_headers):
        """GET /api/admin-portal/artwork-queue - Get all artwork proofs"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/artwork-queue",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get artwork queue failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Artwork queue has {len(data)} proofs")

    def test_get_artwork_queue_with_status_filter(self, auth_headers):
        """GET /api/admin-portal/artwork-queue?status=pending"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/artwork-queue?status=pending",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get pending artwork failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # All returned items should have pending status
        for proof in data:
            assert proof.get("status") == "pending"


@pytest.fixture(scope="module")
def test_job(auth_headers, test_customer):
    """Get or create a test job for artwork tests"""
    # Try to get existing jobs for the customer
    response = requests.get(
        f"{BASE_URL}/api/admin-portal/jobs?customer_id={test_customer['id']}",
        headers=auth_headers
    )
    if response.status_code == 200:
        jobs = response.json()
        if jobs:
            return jobs[0]  # Return first job
    
    # Get all jobs
    response = requests.get(
        f"{BASE_URL}/api/admin-portal/jobs",
        headers=auth_headers
    )
    if response.status_code == 200:
        jobs = response.json()
        if jobs:
            return jobs[0]
    
    # Create a test job if none exist
    job_data = {
        "name": f"TEST_Portal_Job_{uuid.uuid4().hex[:6]}",
        "customer_id": test_customer["id"],
        "description": "Test job for portal testing",
        "status": "in_progress"
    }
    response = requests.post(
        f"{BASE_URL}/api/jobs",
        headers=auth_headers,
        json=job_data
    )
    if response.status_code in [200, 201]:
        return response.json()
    
    return None  # Will skip tests that need a job


class TestAdminPortalArtworkSend:
    """Artwork send tests - requires job"""

    def test_send_artwork_for_approval(self, auth_headers, test_customer, test_job):
        """POST /api/admin-portal/artwork/send - Send artwork for customer approval"""
        if not test_job:
            pytest.skip("No test job available")
        
        artwork_data = {
            "job_id": test_job["id"],
            "customer_id": test_customer["id"],
            "file_url": "https://example.com/test_artwork.png",
            "file_name": f"test_artwork_{uuid.uuid4().hex[:6]}.png",
            "description": "Test artwork for approval"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/artwork/send",
            headers=auth_headers,
            json=artwork_data
        )
        assert response.status_code == 200, f"Send artwork failed: {response.text}"
        data = response.json()
        
        assert "proof_id" in data
        assert "version" in data
        assert data["message"] == "Artwork sent for approval"
        
        print(f"Artwork sent: proof_id={data['proof_id']}, version={data['version']}")

    def test_send_artwork_invalid_customer(self, auth_headers, test_job):
        """POST /api/admin-portal/artwork/send - Invalid customer returns 404"""
        if not test_job:
            pytest.skip("No test job available")
        
        artwork_data = {
            "job_id": test_job["id"],
            "customer_id": "invalid_customer_id",
            "file_url": "https://example.com/test.png",
            "file_name": "test.png"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/artwork/send",
            headers=auth_headers,
            json=artwork_data
        )
        assert response.status_code == 404

    def test_send_artwork_invalid_job(self, auth_headers, test_customer):
        """POST /api/admin-portal/artwork/send - Invalid job returns 404"""
        artwork_data = {
            "job_id": "invalid_job_id",
            "customer_id": test_customer["id"],
            "file_url": "https://example.com/test.png",
            "file_name": "test.png"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/artwork/send",
            headers=auth_headers,
            json=artwork_data
        )
        assert response.status_code == 404


class TestAdminPortalDocuments:
    """Document sharing tests"""

    def test_get_shared_documents(self, auth_headers):
        """GET /api/admin-portal/documents - Get all shared documents"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/documents",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get documents failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Shared documents: {len(data)}")

    def test_get_documents_with_customer_filter(self, auth_headers, test_customer):
        """GET /api/admin-portal/documents?customer_id={id}"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/documents?customer_id={test_customer['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get customer documents failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)


@pytest.fixture(scope="module")
def test_document(auth_headers):
    """Get or create a test document for sharing tests"""
    # Get existing documents
    response = requests.get(
        f"{BASE_URL}/api/documents",
        headers=auth_headers
    )
    if response.status_code == 200:
        docs = response.json()
        if docs:
            return docs[0]
    
    # Create a test document
    doc_data = {
        "name": f"TEST_Portal_Doc_{uuid.uuid4().hex[:6]}",
        "file_url": "https://example.com/test_doc.pdf",
        "file_type": "pdf",
        "category": "test"
    }
    response = requests.post(
        f"{BASE_URL}/api/documents",
        headers=auth_headers,
        json=doc_data
    )
    if response.status_code in [200, 201]:
        return response.json()
    
    return None


class TestAdminPortalDocumentShare:
    """Document share tests"""

    def test_share_document_with_customer(self, auth_headers, test_customer, test_document):
        """POST /api/admin-portal/documents/share - Share document with customer"""
        if not test_document:
            pytest.skip("No test document available")
        
        share_data = {
            "customer_id": test_customer["id"],
            "document_id": test_document["id"],
            "message": "Please review this document",
            "requires_acknowledgment": False
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/documents/share",
            headers=auth_headers,
            json=share_data
        )
        assert response.status_code == 200, f"Share document failed: {response.text}"
        data = response.json()
        
        assert "portal_document_id" in data
        assert data["message"] == "Document shared"
        
        print(f"Document shared: {data['portal_document_id']}")

    def test_share_document_invalid_customer(self, auth_headers, test_document):
        """POST /api/admin-portal/documents/share - Invalid customer returns 404"""
        if not test_document:
            pytest.skip("No test document available")
        
        share_data = {
            "customer_id": "invalid_customer_id",
            "document_id": test_document["id"]
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/documents/share",
            headers=auth_headers,
            json=share_data
        )
        assert response.status_code == 404

    def test_share_document_invalid_document(self, auth_headers, test_customer):
        """POST /api/admin-portal/documents/share - Invalid document returns 404"""
        share_data = {
            "customer_id": test_customer["id"],
            "document_id": "invalid_document_id"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin-portal/documents/share",
            headers=auth_headers,
            json=share_data
        )
        assert response.status_code == 404


class TestAdminPortalHelperEndpoints:
    """Helper endpoints for dropdowns"""

    def test_get_customers_for_portal(self, auth_headers):
        """GET /api/admin-portal/customers - Get customers list for dropdowns"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/customers",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get customers failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        # Check structure if customers exist
        if data:
            customer = data[0]
            assert "id" in customer
            assert "name" in customer
        print(f"Portal customers: {len(data)}")

    def test_get_customers_with_search(self, auth_headers):
        """GET /api/admin-portal/customers?search=test"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/customers?search=test",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_jobs_for_portal(self, auth_headers):
        """GET /api/admin-portal/jobs - Get jobs list for dropdowns"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/jobs",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Get jobs failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Portal jobs: {len(data)}")

    def test_get_jobs_with_customer_filter(self, auth_headers, test_customer):
        """GET /api/admin-portal/jobs?customer_id={id}"""
        response = requests.get(
            f"{BASE_URL}/api/admin-portal/jobs?customer_id={test_customer['id']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
