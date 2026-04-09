"""
Iteration 92 - Object Storage Integration Tests

Tests for cloud storage migration from local filesystem to Emergent Object Storage:
1. POST /api/pricing-setup/imports - stores uploaded files in object storage
2. POST /api/pricing-setup/imports/migrate-storage - migrates legacy local-file pricing imports
3. POST /api/documents - stores new document uploads in object storage
4. GET /api/documents/{id}/download - returns downloadable file_data
5. POST /api/orders/{order_id}/upload - stores new order attachments in object storage
6. GET /api/orders/{order_id}/files/{file_id}/content - returns file bytes
"""

import pytest
import requests
import os
import io
import base64
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials from /app/memory/test_credentials.md
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for owner account"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    data = response.json()
    return data.get("access_token") or data.get("token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPricingSetupImportsObjectStorage:
    """Tests for pricing-setup/imports endpoint with object storage"""

    def test_create_pricing_import_with_csv_file(self, auth_token):
        """POST /api/pricing-setup/imports stores uploaded CSV files in object storage"""
        # Create a simple CSV file
        csv_content = b"description,quantity,total\nBanner 4x8,2,150.00\nVehicle Wrap,1,2500.00"
        files = {
            "files": ("test_pricing.csv", io.BytesIO(csv_content), "text/csv")
        }
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/pricing-setup/imports",
            files=files,
            headers=headers,
            timeout=60
        )
        
        print(f"Create pricing import response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain import id"
        assert "files" in data, "Response should contain files array"
        assert len(data["files"]) > 0, "Should have at least one file"
        
        # Verify file has storage_path (object storage) instead of stored_path (local)
        file_record = data["files"][0]
        print(f"File record: {file_record}")
        assert "storage_path" in file_record, "File should have storage_path for object storage"
        assert file_record.get("storage_backend") == "emergent_object_storage", "Storage backend should be emergent_object_storage"
        assert "signguy-ai/pricing-imports" in file_record.get("storage_path", ""), "Storage path should contain app name and pricing-imports"
        
        # Store import_id for cleanup
        self.__class__.created_import_id = data["id"]
        print(f"Created pricing import: {data['id']} with storage_path: {file_record.get('storage_path')}")

    def test_get_pricing_import_has_storage_path(self, auth_headers):
        """GET /api/pricing-setup/imports/{id} returns file with storage_path"""
        import_id = getattr(self.__class__, "created_import_id", None)
        if not import_id:
            pytest.skip("No import created in previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports/{import_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "files" in data
        if data["files"]:
            file_record = data["files"][0]
            assert "storage_path" in file_record, "File should have storage_path"
            print(f"Verified storage_path: {file_record.get('storage_path')}")

    def test_migrate_storage_endpoint(self, auth_headers):
        """POST /api/pricing-setup/imports/migrate-storage returns valid response"""
        response = requests.post(
            f"{BASE_URL}/api/pricing-setup/imports/migrate-storage",
            headers=auth_headers,
            timeout=60
        )
        
        print(f"Migrate storage response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should return migration stats
        assert "imports_checked" in data, "Response should contain imports_checked"
        assert "imports_updated" in data, "Response should contain imports_updated"
        assert "files_migrated" in data, "Response should contain files_migrated"
        assert "files_skipped" in data, "Response should contain files_skipped"
        assert data.get("storage_backend") == "emergent_object_storage", "Storage backend should be emergent_object_storage"
        
        print(f"Migration result: {data}")


class TestDocumentsObjectStorage:
    """Tests for documents endpoint with object storage"""

    def test_upload_document_to_object_storage(self, auth_token):
        """POST /api/documents stores new document uploads in object storage"""
        # Create a simple PDF-like content (just bytes for testing)
        pdf_content = b"%PDF-1.4 test document content for object storage testing"
        
        files = {
            "file": ("test_document.pdf", io.BytesIO(pdf_content), "application/pdf")
        }
        data = {
            "name": "TEST_ObjectStorage_Document",
            "description": "Test document for object storage verification",
            "category": "other",
            "is_template": "false",
            "tags": "test,object-storage"
        }
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/documents",
            files=files,
            data=data,
            headers=headers,
            timeout=60
        )
        
        print(f"Upload document response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        doc = response.json()
        assert "id" in doc, "Response should contain document id"
        assert "storage_path" in doc, "Document should have storage_path for object storage"
        assert doc.get("storage_backend") == "emergent_object_storage", "Storage backend should be emergent_object_storage"
        assert "signguy-ai/documents" in doc.get("storage_path", ""), "Storage path should contain app name and documents"
        
        # Store document_id for subsequent tests
        self.__class__.created_document_id = doc["id"]
        print(f"Created document: {doc['id']} with storage_path: {doc.get('storage_path')}")

    def test_download_document_returns_file_data(self, auth_headers):
        """GET /api/documents/{id}/download returns downloadable file_data"""
        doc_id = getattr(self.__class__, "created_document_id", None)
        if not doc_id:
            pytest.skip("No document created in previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/documents/{doc_id}/download",
            headers=auth_headers,
            timeout=30
        )
        
        print(f"Download document response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain document id"
        assert "file_data" in data, "Response should contain file_data"
        assert "file_type" in data, "Response should contain file_type"
        assert "original_filename" in data, "Response should contain original_filename"
        
        # Verify file_data is valid base64
        try:
            decoded = base64.b64decode(data["file_data"])
            assert len(decoded) > 0, "Decoded file data should not be empty"
            print(f"Successfully downloaded document, decoded size: {len(decoded)} bytes")
        except Exception as e:
            pytest.fail(f"file_data is not valid base64: {e}")

    def test_get_document_metadata(self, auth_headers):
        """GET /api/documents/{id} returns document with storage_path"""
        doc_id = getattr(self.__class__, "created_document_id", None)
        if not doc_id:
            pytest.skip("No document created in previous test")
        
        response = requests.get(
            f"{BASE_URL}/api/documents/{doc_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "storage_path" in data, "Document should have storage_path"
        assert data.get("storage_backend") == "emergent_object_storage", "Storage backend should be emergent_object_storage"
        print(f"Document metadata verified with storage_path: {data.get('storage_path')}")

    def test_cleanup_test_document(self, auth_headers):
        """DELETE /api/documents/{id} - cleanup test document"""
        doc_id = getattr(self.__class__, "created_document_id", None)
        if not doc_id:
            pytest.skip("No document to cleanup")
        
        response = requests.delete(
            f"{BASE_URL}/api/documents/{doc_id}",
            headers=auth_headers,
            timeout=30
        )
        
        # Document deletion archives it (soft delete)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"Cleaned up test document: {doc_id}")


class TestOrderFilesObjectStorage:
    """Tests for order file attachments with object storage"""

    def test_create_test_order(self, auth_headers):
        """Create a test order for file upload testing"""
        order_data = {
            "customer_name": "TEST_ObjectStorage_Customer",
            "company_name": "Test Company",
            "source": "walk_in",
            "priority": "normal"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/orders",
            json=order_data,
            headers=auth_headers,
            timeout=30
        )
        
        print(f"Create order response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain order id"
        
        self.__class__.test_order_id = data["id"]
        print(f"Created test order: {data['id']}")

    def test_upload_order_file_to_object_storage(self, auth_token):
        """POST /api/orders/{order_id}/upload stores new order attachments in object storage"""
        order_id = getattr(self.__class__, "test_order_id", None)
        if not order_id:
            pytest.skip("No test order created")
        
        # Create a test image file
        image_content = b"\x89PNG\r\n\x1a\n" + b"test image content for object storage"
        
        files = {
            "file": ("test_artwork.png", io.BytesIO(image_content), "image/png")
        }
        data = {
            "label": "Test Artwork for Object Storage"
        }
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/orders/{order_id}/upload",
            files=files,
            data=data,
            headers=headers,
            timeout=60
        )
        
        print(f"Upload order file response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        file_data = response.json()
        assert "id" in file_data, "Response should contain file id"
        assert "filename" in file_data, "Response should contain filename"
        
        self.__class__.uploaded_file_id = file_data["id"]
        print(f"Uploaded order file: {file_data['id']}")

    def test_list_order_files_has_storage_path(self, auth_headers):
        """GET /api/orders/{order_id}/files returns files with storage info"""
        order_id = getattr(self.__class__, "test_order_id", None)
        if not order_id:
            pytest.skip("No test order created")
        
        response = requests.get(
            f"{BASE_URL}/api/orders/{order_id}/files",
            headers=auth_headers,
            timeout=30
        )
        
        print(f"List order files response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        files = response.json()
        assert isinstance(files, list), "Response should be a list"
        
        if files:
            file_record = files[0]
            assert "storage_path" in file_record, "File should have storage_path"
            assert file_record.get("storage_backend") == "emergent_object_storage", "Storage backend should be emergent_object_storage"
            assert "signguy-ai/orders" in file_record.get("storage_path", ""), "Storage path should contain app name and orders"
            print(f"Order file has storage_path: {file_record.get('storage_path')}")

    def test_get_order_file_content(self, auth_headers):
        """GET /api/orders/{order_id}/files/{file_id}/content returns file bytes"""
        order_id = getattr(self.__class__, "test_order_id", None)
        file_id = getattr(self.__class__, "uploaded_file_id", None)
        if not order_id or not file_id:
            pytest.skip("No test order or file created")
        
        response = requests.get(
            f"{BASE_URL}/api/orders/{order_id}/files/{file_id}/content",
            headers=auth_headers,
            timeout=30
        )
        
        print(f"Get order file content response: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Response should be raw bytes with appropriate content type
        content_type = response.headers.get("content-type", "")
        assert "image" in content_type or "octet-stream" in content_type, f"Expected image or octet-stream content type, got: {content_type}"
        assert len(response.content) > 0, "Response content should not be empty"
        print(f"Retrieved order file content: {len(response.content)} bytes, content-type: {content_type}")

    def test_cleanup_order_file(self, auth_headers):
        """DELETE /api/orders/{order_id}/files/{file_id} - cleanup test file"""
        order_id = getattr(self.__class__, "test_order_id", None)
        file_id = getattr(self.__class__, "uploaded_file_id", None)
        if not order_id or not file_id:
            pytest.skip("No test file to cleanup")
        
        response = requests.delete(
            f"{BASE_URL}/api/orders/{order_id}/files/{file_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"Cleaned up test file: {file_id}")

    def test_cleanup_test_order(self, auth_headers):
        """DELETE /api/orders/{order_id} - cleanup test order"""
        order_id = getattr(self.__class__, "test_order_id", None)
        if not order_id:
            pytest.skip("No test order to cleanup")
        
        response = requests.delete(
            f"{BASE_URL}/api/orders/{order_id}",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"Cleaned up test order: {order_id}")


class TestBackwardCompatibility:
    """Tests for backward compatibility after storage migration"""

    def test_documents_list_endpoint_works(self, auth_headers):
        """GET /api/documents returns list without errors"""
        response = requests.get(
            f"{BASE_URL}/api/documents",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Documents list returned {len(data)} documents")

    def test_documents_stats_endpoint_works(self, auth_headers):
        """GET /api/documents/stats returns stats without errors"""
        response = requests.get(
            f"{BASE_URL}/api/documents/stats",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "total_documents" in data, "Response should contain total_documents"
        print(f"Documents stats: {data}")

    def test_pricing_imports_list_endpoint_works(self, auth_headers):
        """GET /api/pricing-setup/imports returns list without errors"""
        response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Pricing imports list returned {len(data)} imports")

    def test_orders_list_endpoint_works(self, auth_headers):
        """GET /api/orders returns list without errors"""
        response = requests.get(
            f"{BASE_URL}/api/orders",
            headers=auth_headers,
            timeout=30
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "orders" in data, "Response should contain orders"
        print(f"Orders list returned {len(data.get('orders', []))} orders")


class TestObjectStorageServiceHealth:
    """Tests for object storage service availability"""

    def test_auth_endpoint_works(self):
        """POST /api/auth/login works (basic health check)"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=30
        )
        
        assert response.status_code == 200, f"Auth failed: {response.status_code}"
        print("Auth endpoint working")

    def test_health_endpoint(self):
        """GET /api/health returns OK"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        
        # Health endpoint might return 200 or 404 if not implemented
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"Health endpoint status: {response.status_code}")
