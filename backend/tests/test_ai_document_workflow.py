"""
Test AI Document Workflow Features (Iteration 33)

Tests for:
1. POST /api/documents/generate-pdf - PDF generation from content
2. POST /api/documents/from-ai - Save AI content as document
3. Document Library features
"""

import pytest
import requests
import os
import base64

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test_ai@test.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture
def api_headers(auth_token):
    """Headers with authentication"""
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }


class TestPDFGeneration:
    """Tests for /api/documents/generate-pdf endpoint"""
    
    def test_generate_pdf_basic(self, api_headers):
        """Test basic PDF generation"""
        response = requests.post(
            f"{BASE_URL}/api/documents/generate-pdf",
            headers=api_headers,
            json={
                "content": "Test document content for PDF generation.",
                "title": "Test PDF Document",
                "tool_id": "document_composer"
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "pdf_data" in data, "Missing pdf_data in response"
        assert "filename" in data, "Missing filename in response"
        assert "file_size" in data, "Missing file_size in response"
        
        # Verify PDF data is valid base64
        try:
            pdf_bytes = base64.b64decode(data["pdf_data"])
            assert pdf_bytes[:4] == b'%PDF', "Invalid PDF header"
        except Exception as e:
            pytest.fail(f"Invalid base64 PDF data: {e}")
        
        print(f"✓ PDF generated: {data['filename']} ({data['file_size']} bytes)")
    
    def test_generate_pdf_with_markdown(self, api_headers):
        """Test PDF generation with markdown-style content"""
        content = """# Main Heading

## Section 1: Introduction

This is the introduction paragraph with some text content.

- Bullet point 1
- Bullet point 2
- Bullet point 3

### Subsection 1.1

More detailed content here.

## Section 2: Conclusion

Final thoughts and summary."""
        
        response = requests.post(
            f"{BASE_URL}/api/documents/generate-pdf",
            headers=api_headers,
            json={
                "content": content,
                "title": "Markdown Test Document",
                "tool_id": "document_composer"
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "pdf_data" in data
        assert data["file_size"] > 500, "PDF seems too small for markdown content"
        print(f"✓ Markdown PDF generated: {data['filename']}")
    
    def test_generate_pdf_requires_auth(self):
        """Test PDF generation requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/documents/generate-pdf",
            headers={"Content-Type": "application/json"},
            json={"content": "Test", "title": "Test"}
        )
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Auth required for PDF generation")
    
    def test_generate_pdf_empty_content(self, api_headers):
        """Test PDF generation with empty content"""
        response = requests.post(
            f"{BASE_URL}/api/documents/generate-pdf",
            headers=api_headers,
            json={
                "content": "",
                "title": "Empty Test"
            }
        )
        # Should still succeed (empty content makes valid PDF)
        assert response.status_code == 200, f"Failed: {response.text}"
        print("✓ Empty content handled gracefully")


class TestSaveToLibrary:
    """Tests for /api/documents/from-ai endpoint"""
    
    def test_save_ai_document_basic(self, api_headers):
        """Test saving AI content as document"""
        import time
        unique_name = f"AI Generated Doc - {int(time.time())}"
        
        response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers=api_headers,
            json={
                "content": "This is AI-generated content that should be saved to the document library.",
                "name": unique_name,
                "tool_id": "document_composer",
                "category": "contract",
                "input_data": {"topic": "test"}
            }
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Missing id in response"
        assert data["name"] == unique_name, "Name mismatch"
        assert data["category"] == "contract", "Category mismatch"
        assert "ai-generated" in data.get("tags", []), "Missing ai-generated tag"
        assert data["file_type"] == "text/plain", "Wrong file type"
        
        print(f"✓ AI document saved: {data['id']}")
        return data["id"]
    
    def test_save_ai_document_verify_persistence(self, api_headers):
        """Test that saved AI document is retrievable"""
        import time
        unique_name = f"Persistence Test Doc - {int(time.time())}"
        
        # Create document
        create_response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers=api_headers,
            json={
                "content": "Test persistence content.",
                "name": unique_name,
                "tool_id": "idea_brainstormer",
                "category": "other"
            }
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        doc_id = create_response.json()["id"]
        
        # Verify document exists by fetching it
        get_response = requests.get(
            f"{BASE_URL}/api/documents/{doc_id}",
            headers=api_headers
        )
        
        assert get_response.status_code == 200, f"Get failed: {get_response.text}"
        fetched_doc = get_response.json()
        assert fetched_doc["name"] == unique_name, "Name mismatch on GET"
        print(f"✓ Document persistence verified: {doc_id}")
    
    def test_save_ai_document_requires_auth(self):
        """Test that saving requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers={"Content-Type": "application/json"},
            json={"content": "Test", "name": "Test Doc"}
        )
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Auth required for save to library")
    
    def test_save_ai_document_with_different_categories(self, api_headers):
        """Test saving with various categories"""
        import time
        categories = ["contract", "other", "internal"]
        
        for category in categories:
            response = requests.post(
                f"{BASE_URL}/api/documents/from-ai",
                headers=api_headers,
                json={
                    "content": f"Content for {category} document.",
                    "name": f"Category Test - {category} - {int(time.time())}",
                    "tool_id": "business_copywriter",
                    "category": category
                }
            )
            
            assert response.status_code == 200, f"Failed for {category}: {response.text}"
            assert response.json()["category"] == category
            print(f"✓ Category '{category}' handled correctly")


class TestDocumentDownload:
    """Tests for document download functionality"""
    
    def test_download_ai_generated_document(self, api_headers):
        """Test downloading an AI-generated document"""
        import time
        
        # First create a document
        create_response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers=api_headers,
            json={
                "content": "Downloadable content test.",
                "name": f"Download Test - {int(time.time())}",
                "tool_id": "document_composer"
            }
        )
        
        assert create_response.status_code == 200
        doc_id = create_response.json()["id"]
        
        # Download the document
        download_response = requests.get(
            f"{BASE_URL}/api/documents/{doc_id}/download",
            headers=api_headers
        )
        
        assert download_response.status_code == 200, f"Download failed: {download_response.text}"
        data = download_response.json()
        
        assert "file_data" in data, "Missing file_data"
        assert data["file_type"] == "text/plain"
        
        # Verify content
        content = base64.b64decode(data["file_data"]).decode('utf-8')
        assert "Downloadable content test" in content
        print(f"✓ Document download verified: {doc_id}")


class TestSendToPortal:
    """Tests for sending documents to customer portal"""
    
    def test_send_to_portal_requires_customer(self, api_headers):
        """Test that send-to-portal requires valid customer"""
        import time
        
        # Create a test document
        doc_response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers=api_headers,
            json={
                "content": "Portal test content.",
                "name": f"Portal Test - {int(time.time())}",
                "tool_id": "document_composer"
            }
        )
        
        assert doc_response.status_code == 200
        doc_id = doc_response.json()["id"]
        
        # Try to send without valid customer
        send_response = requests.post(
            f"{BASE_URL}/api/documents/{doc_id}/send-to-portal",
            headers=api_headers,
            json={
                "customer_id": "invalid-customer-id",
                "notify_customer": False
            }
        )
        
        # Should fail with 404 for invalid customer
        assert send_response.status_code == 404, f"Expected 404, got: {send_response.status_code}"
        print("✓ Invalid customer handled correctly")
    
    def test_send_to_portal_with_valid_customer(self, api_headers):
        """Test sending document to valid customer with portal access"""
        import time
        import uuid
        
        # First create a customer with portal enabled
        customer_name = f"Portal Test Customer {int(time.time())}"
        customer_email = f"portal_test_{uuid.uuid4().hex[:8]}@test.com"
        
        customer_response = requests.post(
            f"{BASE_URL}/api/customers",
            headers=api_headers,
            json={
                "name": customer_name,
                "email": customer_email,
                "portal_enabled": True
            }
        )
        
        if customer_response.status_code != 200:
            pytest.skip(f"Could not create test customer: {customer_response.text}")
        
        customer_id = customer_response.json()["id"]
        
        # Create a test document
        doc_response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers=api_headers,
            json={
                "content": "Document for portal sharing.",
                "name": f"Portal Share Test - {int(time.time())}",
                "tool_id": "document_composer"
            }
        )
        
        assert doc_response.status_code == 200
        doc_id = doc_response.json()["id"]
        
        # Send to customer portal
        send_response = requests.post(
            f"{BASE_URL}/api/documents/{doc_id}/send-to-portal",
            headers=api_headers,
            json={
                "customer_id": customer_id,
                "message": "Test document for you!",
                "notify_customer": False
            }
        )
        
        assert send_response.status_code == 200, f"Send failed: {send_response.text}"
        result = send_response.json()
        assert "portal_document_id" in result, "Missing portal_document_id"
        print(f"✓ Document sent to portal: {result['portal_document_id']}")


class TestDocumentLibraryIntegration:
    """Tests for document library list and retrieval"""
    
    def test_list_documents_includes_ai_generated(self, api_headers):
        """Test that AI-generated documents appear in library list"""
        import time
        
        # Create an AI document
        unique_name = f"Library List Test - {int(time.time())}"
        create_response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers=api_headers,
            json={
                "content": "Test content for library listing.",
                "name": unique_name,
                "tool_id": "document_composer"
            }
        )
        
        assert create_response.status_code == 200
        doc_id = create_response.json()["id"]
        
        # List documents
        list_response = requests.get(
            f"{BASE_URL}/api/documents",
            headers=api_headers
        )
        
        assert list_response.status_code == 200, f"List failed: {list_response.text}"
        documents = list_response.json()
        
        # Find our document
        found = any(d["id"] == doc_id for d in documents)
        assert found, f"Document {doc_id} not found in library list"
        print(f"✓ AI document found in library: {doc_id}")
    
    def test_get_document_with_include_data(self, api_headers):
        """Test retrieving document with file data"""
        import time
        
        # Create a document
        create_response = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            headers=api_headers,
            json={
                "content": "Content to retrieve.",
                "name": f"Retrieve Test - {int(time.time())}",
                "tool_id": "document_composer"
            }
        )
        
        assert create_response.status_code == 200
        doc_id = create_response.json()["id"]
        
        # Get with include_data=true
        get_response = requests.get(
            f"{BASE_URL}/api/documents/{doc_id}?include_data=true",
            headers=api_headers
        )
        
        assert get_response.status_code == 200, f"Get failed: {get_response.text}"
        data = get_response.json()
        assert "file_data" in data, "file_data not included when requested"
        print(f"✓ Document retrieved with file data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
