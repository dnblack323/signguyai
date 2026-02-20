"""
Test Suite for AI Business Assistant Context-Awareness Fix
Tests that AI assistant returns shop-specific data instead of generic advice.

Issue Fixed: Line 1062 in ai.py had ${Y} in f-string causing 'name Y is not defined' error.
Fix: Changed ${Y} to $[Y] to escape the curly brace.

Tests verify:
1. AI Assistant endpoint returns shop-specific data
2. Document Composer generates professional documents
3. Business Copywriter generates marketing copy
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token using test_ai@test.com credentials"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "test_ai@test.com", "password": "password123"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with authentication"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestAPIHealth:
    """Verify API is accessible"""
    
    def test_health_check(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✅ API Health check passed")


class TestAIAssistantContextAwareness:
    """Test AI Business Assistant returns shop-specific data"""
    
    def test_ai_assistant_revenue_question(self, auth_headers):
        """AI Assistant should return actual revenue numbers, not generic advice"""
        session_id = f"test_session_{uuid.uuid4()}"
        
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers=auth_headers,
            json={
                "message": "What is my revenue?",
                "session_id": session_id,
                "conversation_history": []
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        
        response_text = data["response"]
        
        # Check that the response contains actual revenue data markers
        # The response should mention specific numbers (even if $0.00)
        assert "$" in response_text, "Response should contain dollar amounts"
        assert any(kw in response_text.lower() for kw in ["revenue", "all-time", "30 days", "pending"]), \
            "Response should mention revenue-related terms"
        
        # Should NOT contain generic phrases indicating lack of data access
        generic_phrases = ["upload your data", "tell me what software", "I don't have access to your"]
        for phrase in generic_phrases:
            assert phrase not in response_text.lower(), f"Response should not contain generic phrase: '{phrase}'"
        
        print(f"✅ AI Assistant returned context-aware response with revenue data")
        print(f"   First 200 chars: {response_text[:200]}...")

    def test_ai_assistant_jobs_question(self, auth_headers):
        """AI Assistant should return actual job statistics"""
        session_id = f"test_session_{uuid.uuid4()}"
        
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers=auth_headers,
            json={
                "message": "How many active jobs do I have?",
                "session_id": session_id
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        response_text = data["response"]
        
        # Should contain job-related specific data
        assert any(kw in response_text.lower() for kw in ["job", "active", "total"]), \
            "Response should mention job-related terms"
        
        print(f"✅ AI Assistant returned context-aware job data")

    def test_ai_assistant_customer_question(self, auth_headers):
        """AI Assistant should return actual customer statistics"""
        session_id = f"test_session_{uuid.uuid4()}"
        
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers=auth_headers,
            json={
                "message": "Tell me about my customers",
                "session_id": session_id
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        response_text = data["response"]
        
        # Should contain customer-related specific data
        assert any(kw in response_text.lower() for kw in ["customer", "total"]), \
            "Response should mention customer-related terms"
        
        print(f"✅ AI Assistant returned context-aware customer data")


class TestDocumentComposer:
    """Test Document Composer generates professional documents"""
    
    def test_document_composer_proposal(self, auth_headers):
        """Document Composer should generate a proposal document"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "document_composer",
                "input_data": {
                    "document_type": "proposal",
                    "custom_document_type": "",
                    "client_name": "TEST_ABC Company",
                    "project_or_invoice_details": "Vehicle wrap for company van",
                    "tone": "formal_professional",
                    "your_company_name": "TEST_SignGuy Pro"
                }
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "content" in data, "Response should contain 'content' field"
        assert "id" in data, "Response should contain 'id' field"
        
        content = data["content"]
        assert len(content) > 500, "Proposal should be substantial content"
        
        # Should contain proposal-related content
        assert any(kw in content.lower() for kw in ["proposal", "scope", "project", "vehicle wrap"]), \
            "Content should contain proposal-related terms"
        
        print(f"✅ Document Composer generated proposal ({len(content)} chars)")

    def test_document_composer_thank_you_letter(self, auth_headers):
        """Document Composer should generate a thank you letter"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "document_composer",
                "input_data": {
                    "document_type": "thank_you_letter",
                    "client_name": "TEST_XYZ Corp",
                    "project_or_invoice_details": "Storefront signage project completed",
                    "tone": "friendly",
                    "your_company_name": "TEST_Signs Plus"
                }
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "content" in data
        content = data["content"]
        assert len(content) > 200, "Thank you letter should have content"
        
        print(f"✅ Document Composer generated thank you letter ({len(content)} chars)")


class TestBusinessCopywriter:
    """Test Business Copywriter generates marketing copy"""
    
    def test_business_copywriter_about_us(self, auth_headers):
        """Business Copywriter should generate About Us page content"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "business_copywriter",
                "input_data": {
                    "copy_type": "about_us_page",
                    "business_info": "TEST_Local sign shop specializing in vehicle wraps",
                    "tone": "professional",
                    "key_points": "20 years experience, family owned"
                }
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "content" in data
        content = data["content"]
        assert len(content) > 200, "About Us content should be substantial"
        
        print(f"✅ Business Copywriter generated About Us page ({len(content)} chars)")

    def test_business_copywriter_tagline(self, auth_headers):
        """Business Copywriter should generate taglines"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "business_copywriter",
                "input_data": {
                    "copy_type": "tagline_slogan",
                    "business_info": "TEST_Professional sign company",
                    "tone": "casual_friendly",
                    "key_points": "Quality craftsmanship"
                }
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "content" in data
        content = data["content"]
        assert len(content) > 50, "Should contain tagline options"
        
        print(f"✅ Business Copywriter generated taglines ({len(content)} chars)")

    def test_business_copywriter_social_post(self, auth_headers):
        """Business Copywriter should generate social media posts"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "business_copywriter",
                "input_data": {
                    "copy_type": "social_media_post",
                    "business_info": "TEST_Sign shop completing a major project",
                    "tone": "playful_fun",
                    "key_points": "New vehicle wrap completed"
                }
            },
            timeout=120
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "content" in data
        content = data["content"]
        
        print(f"✅ Business Copywriter generated social post ({len(content)} chars)")


class TestAuthRequired:
    """Test that AI endpoints require authentication"""
    
    def test_ai_assistant_requires_auth(self):
        """AI Assistant should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            json={"message": "test", "session_id": "test"}
        )
        assert response.status_code == 401, "Should require authentication"
        print("✅ AI Assistant correctly requires authentication")
    
    def test_ai_generate_requires_auth(self):
        """AI Generate endpoint should require authentication"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={"tool": "document_composer", "input_data": {}}
        )
        assert response.status_code == 401, "Should require authentication"
        print("✅ AI Generate correctly requires authentication")
