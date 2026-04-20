"""
Final Backend Spot-Check for Storage Migration
Testing the 5 specific production-facing flows requested in the review.
"""

import requests
import io
import base64
import os
from datetime import datetime

# Production URL from review request
BASE_URL = "https://dynamic-order-form-2.preview.emergentagent.com"

# Production credentials from review request
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"

def get_auth_token():
    """Get authentication token"""
    print("🔐 Authenticating...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30
    )
    if response.status_code != 200:
        raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    print(f"✅ Authentication successful")
    return token

def test_documents_upload():
    """Test 1: POST /api/documents -> upload still works"""
    print("\n📄 Testing POST /api/documents (document upload)...")
    
    token = get_auth_token()
    
    # Create test document content
    test_content = b"Cloud Storage Smoke Test - Document Upload"
    
    files = {
        "file": ("storage_test.txt", io.BytesIO(test_content), "text/plain")
    }
    data = {
        "name": "Cloud Storage Smoke Test",
        "description": "Final storage migration verification",
        "category": "other",
        "is_template": "false",
        "tags": "storage-test,final-check"
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/api/documents",
        files=files,
        data=data,
        headers=headers,
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Document upload failed: {response.status_code} - {response.text}")
        return None
    
    doc = response.json()
    print(f"✅ Document uploaded successfully: {doc['id']}")
    print(f"   Storage path: {doc.get('storage_path', 'N/A')}")
    print(f"   Storage backend: {doc.get('storage_backend', 'N/A')}")
    
    return doc["id"]

def test_documents_download(doc_id):
    """Test 2: GET /api/documents/{id}/download -> returns file_data for frontend compatibility"""
    print(f"\n📥 Testing GET /api/documents/{doc_id}/download...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/documents/{doc_id}/download",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Document download failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    
    # Verify response structure for frontend compatibility
    required_fields = ["id", "file_data", "file_type", "original_filename"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        print(f"❌ Missing required fields: {missing_fields}")
        return False
    
    # Verify file_data is valid base64
    try:
        decoded = base64.b64decode(data["file_data"])
        if len(decoded) == 0:
            print("❌ Decoded file data is empty")
            return False
    except Exception as e:
        print(f"❌ Invalid base64 file_data: {e}")
        return False
    
    print(f"✅ Document download successful")
    print(f"   File type: {data['file_type']}")
    print(f"   Original filename: {data['original_filename']}")
    print(f"   File data size: {len(decoded)} bytes")
    
    return True

def test_pricing_imports():
    """Test 3: POST /api/pricing-setup/imports -> stores import files successfully"""
    print("\n💰 Testing POST /api/pricing-setup/imports...")
    
    token = get_auth_token()
    
    # Create test CSV content
    csv_content = b"description,quantity,total\nStorage Test Banner,1,100.00\nStorage Test Wrap,1,500.00"
    
    files = {
        "files": ("storage_test_pricing.csv", io.BytesIO(csv_content), "text/csv")
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/api/pricing-setup/imports",
        files=files,
        headers=headers,
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Pricing import failed: {response.status_code} - {response.text}")
        return None
    
    data = response.json()
    
    if not data.get("files") or len(data["files"]) == 0:
        print("❌ No files in import response")
        return None
    
    file_record = data["files"][0]
    
    # Verify object storage fields
    if "storage_path" not in file_record:
        print("❌ Missing storage_path in file record")
        return None
    
    if file_record.get("storage_backend") != "emergent_object_storage":
        print(f"❌ Wrong storage backend: {file_record.get('storage_backend')}")
        return None
    
    print(f"✅ Pricing import successful: {data['id']}")
    print(f"   Storage path: {file_record.get('storage_path')}")
    print(f"   Storage backend: {file_record.get('storage_backend')}")
    
    return data["id"]

def test_migrate_storage():
    """Test 4: POST /api/pricing-setup/imports/migrate-storage -> returns valid migration stats"""
    print("\n🔄 Testing POST /api/pricing-setup/imports/migrate-storage...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    response = requests.post(
        f"{BASE_URL}/api/pricing-setup/imports/migrate-storage",
        headers=headers,
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Storage migration failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    
    # Verify required migration stats fields
    required_fields = ["imports_checked", "imports_updated", "files_migrated", "files_skipped", "storage_backend"]
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        print(f"❌ Missing migration stats fields: {missing_fields}")
        return False
    
    if data.get("storage_backend") != "emergent_object_storage":
        print(f"❌ Wrong storage backend in migration stats: {data.get('storage_backend')}")
        return False
    
    print(f"✅ Storage migration successful")
    print(f"   Imports checked: {data['imports_checked']}")
    print(f"   Imports updated: {data['imports_updated']}")
    print(f"   Files migrated: {data['files_migrated']}")
    print(f"   Files skipped: {data['files_skipped']}")
    
    return True

def test_order_file_upload_and_download():
    """Test 5: POST /api/orders/{id}/upload and GET /api/orders/{id}/files/{file_id}/content -> still work"""
    print("\n📦 Testing order file upload and download...")
    
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # First, create a test order
    print("   Creating test order...")
    order_data = {
        "customer_name": "Storage Test Customer",
        "company_name": "Final Check Co",
        "source": "walk_in",
        "priority": "normal"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/orders",
        json=order_data,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Order creation failed: {response.status_code} - {response.text}")
        return False
    
    order = response.json()
    order_id = order["id"]
    print(f"   ✅ Test order created: {order_id}")
    
    # Upload file to order
    print("   Uploading file to order...")
    test_content = b"Order file storage test content"
    
    files = {
        "file": ("order_storage_test.txt", io.BytesIO(test_content), "text/plain")
    }
    data = {
        "label": "Storage Test File"
    }
    upload_headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/api/orders/{order_id}/upload",
        files=files,
        data=data,
        headers=upload_headers,
        timeout=60
    )
    
    if response.status_code != 200:
        print(f"❌ Order file upload failed: {response.status_code} - {response.text}")
        return False
    
    file_data = response.json()
    file_id = file_data["id"]
    print(f"   ✅ File uploaded: {file_id}")
    
    # Download file content
    print("   Downloading file content...")
    response = requests.get(
        f"{BASE_URL}/api/orders/{order_id}/files/{file_id}/content",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Order file download failed: {response.status_code} - {response.text}")
        return False
    
    # Verify content
    if len(response.content) == 0:
        print("❌ Downloaded content is empty")
        return False
    
    content_type = response.headers.get("content-type", "")
    print(f"   ✅ File download successful")
    print(f"   Content size: {len(response.content)} bytes")
    print(f"   Content type: {content_type}")
    
    # Cleanup: delete the test order
    print("   Cleaning up test order...")
    requests.delete(f"{BASE_URL}/api/orders/{order_id}", headers=headers, timeout=30)
    
    return True

def main():
    """Run all storage migration spot-checks"""
    print("🚀 Starting Final Backend Spot-Check for Storage Migration")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    
    results = {}
    
    try:
        # Test 1: Document upload
        doc_id = test_documents_upload()
        results["documents_upload"] = doc_id is not None
        
        # Test 2: Document download (only if upload succeeded)
        if doc_id:
            results["documents_download"] = test_documents_download(doc_id)
        else:
            results["documents_download"] = False
        
        # Test 3: Pricing imports
        import_id = test_pricing_imports()
        results["pricing_imports"] = import_id is not None
        
        # Test 4: Storage migration
        results["migrate_storage"] = test_migrate_storage()
        
        # Test 5: Order file upload/download
        results["order_files"] = test_order_file_upload_and_download()
        
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        return False
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL SPOT-CHECK RESULTS")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("🎉 ALL STORAGE MIGRATION SPOT-CHECKS PASSED!")
        print("✅ Production storage integration is working correctly")
    else:
        print("⚠️  SOME SPOT-CHECKS FAILED")
        print("❌ Storage migration needs attention")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)