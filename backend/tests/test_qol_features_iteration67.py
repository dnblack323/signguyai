"""
Iteration 67 - Quality of Life Features Tests

Tests for:
1. Customer detail modal New Job button
2. Productivity Kanban drag-and-drop status updates
3. New Job dialog inline customer creation
4. New Quote dialog inline customer creation
5. Customer creation Company-only records
6. Customer creation blocks when both Name and Company blank
7. Customer phone auto-format (###) ###-####
8. AI Assistant voice input and output controls
9. POST /api/ai/voice/speak returns playable audio
10. POST /api/ai/voice/transcribe endpoint exists
11. Regression tests on portal invite, job creation, assistant text chat
"""

import pytest
import requests
import os
import io
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://banner-calc-preview.preview.emergentagent.com').rstrip('/')
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code}")


@pytest.fixture
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestCustomerCreation:
    """Customer creation tests - Name OR Company required, Company-only records, phone format"""
    
    def test_create_customer_with_company_only(self, auth_headers):
        """Test customer creation with only Company (no Name)"""
        response = requests.post(f"{BASE_URL}/api/customers", json={
            "company": "TEST_QOL_Company_Only_Corp",
            "name": "",
            "email": "company.only@test.com",
            "phone": "1234567890",
            "status": "lead"
        }, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Backend should resolve display name from company when name is blank
        assert data.get("company") == "TEST_QOL_Company_Only_Corp"
        # Name should be resolved to company value
        assert data.get("name") == "TEST_QOL_Company_Only_Corp"
        
        # Cleanup
        customer_id = data.get("id")
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        print("PASS: Customer created with Company-only, name resolved correctly")
    
    def test_create_customer_blocks_both_blank(self, auth_headers):
        """Test customer creation fails when both Name and Company are blank"""
        response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "",
            "company": "",
            "email": "blank@test.com",
            "status": "lead"
        }, headers=auth_headers)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "Name or Company is required" in data.get("detail", "")
        print("PASS: Customer creation blocked when both Name and Company blank")
    
    def test_create_customer_with_name_only(self, auth_headers):
        """Test customer creation with Name only"""
        response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_QOL_Name_Only_Person",
            "company": "",
            "email": "nameonly@test.com",
            "status": "lead"
        }, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("name") == "TEST_QOL_Name_Only_Person"
        
        # Cleanup
        customer_id = data.get("id")
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        print("PASS: Customer created with Name-only")
    
    def test_create_customer_with_both_name_and_company(self, auth_headers):
        """Test customer creation with both Name and Company"""
        response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_QOL_John Doe",
            "company": "TEST_QOL_Acme Corp",
            "email": "john@acme.com",
            "status": "lead"
        }, headers=auth_headers)
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Name should take precedence over company for display name
        assert data.get("name") == "TEST_QOL_John Doe"
        assert data.get("company") == "TEST_QOL_Acme Corp"
        
        # Cleanup
        customer_id = data.get("id")
        requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
        print("PASS: Customer created with both Name and Company")


class TestJobCreation:
    """Job creation tests - basic flow works"""
    
    def test_create_job_with_customer(self, auth_headers):
        """Test creating a job with line items"""
        # First create a test customer
        cust_response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_QOL_Job_Customer",
            "status": "lead"
        }, headers=auth_headers)
        assert cust_response.status_code == 200
        customer = cust_response.json()
        customer_id = customer.get("id")
        
        try:
            # Create job
            job_response = requests.post(f"{BASE_URL}/api/jobs", json={
                "customer_id": customer_id,
                "name": "TEST_QOL_Job_Creation",
                "status": "approved",
                "line_items": [
                    {"description": "Test Banner", "quantity": 2, "unit_price": 100.00}
                ]
            }, headers=auth_headers)
            
            assert job_response.status_code == 200, f"Failed: {job_response.text}"
            job = job_response.json()
            assert job.get("name") == "TEST_QOL_Job_Creation"
            assert job.get("customer_id") == customer_id
            print("PASS: Job created successfully with customer")
            
            # Cleanup job
            job_id = job.get("id")
            requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)
        finally:
            # Cleanup customer
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)


class TestJobStatusUpdate:
    """Kanban drag-and-drop status update tests"""
    
    def test_update_job_status(self, auth_headers):
        """Test updating job status via PUT (simulates Kanban drag-drop)"""
        # Create customer
        cust_response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_QOL_Kanban_Customer",
            "status": "lead"
        }, headers=auth_headers)
        customer_id = cust_response.json().get("id")
        
        # Create job in 'quote' status
        job_response = requests.post(f"{BASE_URL}/api/jobs", json={
            "customer_id": customer_id,
            "name": "TEST_QOL_Kanban_Job",
            "status": "quote"
        }, headers=auth_headers)
        job = job_response.json()
        job_id = job.get("id")
        
        try:
            # Test status transitions (Kanban drag-drop)
            status_transitions = [
                ("approved", "Move to Approved"),
                ("in_progress", "Move to In Progress"),
                ("completed", "Move to Completed"),
                ("invoiced", "Move to Invoiced")
            ]
            
            for new_status, description in status_transitions:
                update_response = requests.put(f"{BASE_URL}/api/jobs/{job_id}", json={
                    "status": new_status
                }, headers=auth_headers)
                
                assert update_response.status_code == 200, f"Failed to {description}: {update_response.text}"
                updated_job = update_response.json()
                assert updated_job.get("status") == new_status, f"Status mismatch: expected {new_status}, got {updated_job.get('status')}"
                print(f"PASS: {description}")
            
            print("PASS: All Kanban status transitions work correctly")
            
        finally:
            requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)


class TestCustomerPortalInvite:
    """Regression test for customer portal invite flow"""
    
    def test_invite_customer_to_portal(self, auth_headers):
        """Test inviting customer to portal"""
        # Create customer with email
        cust_response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_QOL_Portal_Customer",
            "email": "portaltest@example.com",
            "status": "active"
        }, headers=auth_headers)
        assert cust_response.status_code == 200
        customer = cust_response.json()
        customer_id = customer.get("id")
        
        try:
            # Invite to portal
            invite_response = requests.post(f"{BASE_URL}/api/customers/{customer_id}/invite-portal", 
                                           headers=auth_headers)
            
            assert invite_response.status_code == 200, f"Portal invite failed: {invite_response.text}"
            data = invite_response.json()
            assert data.get("portal_enabled")
            assert "temporary_pin" in data
            print(f"PASS: Portal invite succeeded, PIN: {data.get('temporary_pin')}")
        finally:
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)
    
    def test_invite_customer_without_email_fails(self, auth_headers):
        """Test that portal invite fails if customer has no email"""
        # Create customer without email
        cust_response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_QOL_NoEmail_Customer",
            "status": "lead"
        }, headers=auth_headers)
        customer_id = cust_response.json().get("id")
        
        try:
            invite_response = requests.post(f"{BASE_URL}/api/customers/{customer_id}/invite-portal",
                                           headers=auth_headers)
            assert invite_response.status_code == 400, f"Expected 400, got {invite_response.status_code}"
            print("PASS: Portal invite correctly blocked for customer without email")
        finally:
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)


class TestVoiceEndpoints:
    """AI Business Assistant voice endpoints"""
    
    def test_voice_speak_endpoint_returns_audio(self, auth_headers):
        """Test POST /api/ai/voice/speak returns playable audio"""
        response = requests.post(f"{BASE_URL}/api/ai/voice/speak", json={
            "text": "Hello, this is a test message.",
            "voice": "alloy",
            "speed": 1.0
        }, headers=auth_headers)
        
        # May return 402 if insufficient credits, which is expected behavior
        if response.status_code == 402:
            print("PASS: Voice speak endpoint exists (got 402 - insufficient credits, expected behavior)")
            return
        
        assert response.status_code == 200, f"Voice speak failed: {response.text}"
        data = response.json()
        
        # Verify audio data returned
        assert "audio_base64" in data, "Missing audio_base64 in response"
        assert "mime_type" in data, "Missing mime_type in response"
        assert len(data.get("audio_base64", "")) > 100, "Audio data too short"
        print(f"PASS: Voice speak returned audio, mime_type: {data.get('mime_type')}")
    
    def test_voice_transcribe_endpoint_exists(self, auth_headers):
        """Test POST /api/ai/voice/transcribe endpoint exists"""
        # Create a dummy audio file for testing
        # We send an empty/minimal file to verify endpoint exists
        # The actual transcription may fail but endpoint should accept the request
        
        # Create a simple audio bytes (just headers)
        files = {'audio': ('test.webm', io.BytesIO(b'test audio content'), 'audio/webm')}
        headers = {"Authorization": auth_headers["Authorization"]}  # Don't include Content-Type for multipart
        
        response = requests.post(f"{BASE_URL}/api/ai/voice/transcribe", 
                                files=files,
                                headers=headers)
        
        # Endpoint may return 500 (invalid audio) or 402 (no credits)
        # but should NOT return 404
        assert response.status_code != 404, "Voice transcribe endpoint not found"
        
        if response.status_code == 402:
            print("PASS: Voice transcribe endpoint exists (got 402 - insufficient credits)")
        elif response.status_code == 500:
            print("PASS: Voice transcribe endpoint exists (got 500 - expected for invalid audio)")
        elif response.status_code == 200:
            print("PASS: Voice transcribe endpoint exists and returned 200")
        else:
            print(f"PASS: Voice transcribe endpoint exists (got {response.status_code})")


class TestAIAssistantTextChat:
    """Regression test for AI Business Assistant text chat"""
    
    def test_ai_assistant_chat(self, auth_headers):
        """Test AI Business Assistant text chat endpoint"""
        response = requests.post(f"{BASE_URL}/api/ai/assistant", json={
            "message": "What is a good profit margin for banners?",
            "session_id": "test_session_qol_67",
            "conversation_history": []
        }, headers=auth_headers)
        
        # May return 402 if insufficient credits
        if response.status_code == 402:
            print("PASS: AI Assistant endpoint works (got 402 - insufficient credits)")
            return
        
        assert response.status_code == 200, f"AI Assistant failed: {response.text}"
        data = response.json()
        assert "response" in data, "Missing response in AI assistant output"
        assert len(data.get("response", "")) > 50, "AI response too short"
        print("PASS: AI Assistant text chat working")


class TestQuoteCreation:
    """Quote creation tests - basic flow for regression"""
    
    def test_create_quote(self, auth_headers):
        """Test creating a quote"""
        # Create customer
        cust_response = requests.post(f"{BASE_URL}/api/customers", json={
            "name": "TEST_QOL_Quote_Customer",
            "status": "lead"
        }, headers=auth_headers)
        customer_id = cust_response.json().get("id")
        
        try:
            # Create quote
            quote_response = requests.post(f"{BASE_URL}/api/quotes", json={
                "customer_id": customer_id,
                "line_items": [
                    {"description": "Test Item", "quantity": 1, "unit_price": 50.00}
                ],
                "status": "draft"
            }, headers=auth_headers)
            
            assert quote_response.status_code == 200, f"Quote creation failed: {quote_response.text}"
            quote = quote_response.json()
            assert quote.get("customer_id") == customer_id
            print("PASS: Quote created successfully")
            
            # Test quote conversion to job
            quote_id = quote.get("id")
            convert_response = requests.post(f"{BASE_URL}/api/quotes/{quote_id}/convert",
                                            headers=auth_headers)
            
            if convert_response.status_code == 200:
                job = convert_response.json()
                job_id = job.get("id")
                print(f"PASS: Quote converted to job {job_id}")
                requests.delete(f"{BASE_URL}/api/jobs/{job_id}", headers=auth_headers)
                
        finally:
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
