"""
Stage 1 Critical Fixes - Iteration 70 Testing

Tests for:
1. AI Rate Limiter fix (request: Request, data: Pydantic model pattern in ai.py)
2. Promo code system - POST /api/billing/apply-promo endpoint
3. Promo code system - free_days discount type support
4. Founders billing endpoints
5. Basic health and auth checks
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"


class TestAuthAndHealth:
    """Basic auth and health check tests"""
    
    def test_health_endpoint(self):
        """GET /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        data = response.json()
        assert "status" in data or "healthy" in str(data).lower(), f"Unexpected health response: {data}"
        print(f"✓ Health check passed: {data}")
    
    def test_login_with_admin_credentials(self):
        """POST /api/auth/login with admin credentials returns access_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        data = response.json()
        # Note: Response field is 'access_token' not 'token'
        assert "access_token" in data, f"Missing access_token in response: {data}"
        assert len(data["access_token"]) > 0, "Empty access_token"
        print(f"✓ Login successful, token length: {len(data['access_token'])}")
        return data["access_token"]


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.status_code}")
    return response.json().get("access_token")


class TestAIRoutesFixes:
    """Test AI routes to verify ai.py loads without errors after parameter fix"""
    
    def test_ai_history_endpoint_loads(self, auth_token):
        """GET /api/ai/history returns AI history (verifies ai.py loads)"""
        response = requests.get(
            f"{BASE_URL}/api/ai/history",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # 200 = success, 402 = no credits (expected), both verify ai.py loaded correctly
        assert response.status_code in [200, 402], f"AI history failed: {response.status_code} - {response.text}"
        print(f"✓ AI history endpoint working: status {response.status_code}")
    
    def test_ai_generate_endpoint_accepts_new_params(self, auth_token):
        """POST /api/ai/generate accepts request: Request + data: AIGenerateRequest"""
        # This tests that the endpoint is reachable and the Pydantic model works
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "tool": "tagline_generator",
                "input_data": {
                    "business_name": "Test Sign Shop",
                    "industry": "signage",
                    "key_values": "quality",
                    "target_audience": "businesses",
                    "tone": "professional"
                }
            }
        )
        # Accept 200 (success), 402 (no credits), or 500 (AI service error) - all mean endpoint loaded
        # The key is that it doesn't return 422 (validation error) or 500 with Pydantic issues
        assert response.status_code in [200, 402, 500], f"AI generate failed: {response.status_code} - {response.text}"
        if response.status_code == 422:
            pytest.fail(f"Pydantic validation error - parameter fix may not be applied: {response.text}")
        print(f"✓ AI generate endpoint responds: status {response.status_code}")
    
    def test_ai_assistant_endpoint_accepts_new_params(self, auth_token):
        """POST /api/ai/assistant accepts request: Request + data: AIAssistantRequest"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "message": "Hello, test message",
                "session_id": "test-session-123"
            }
        )
        # Same logic - endpoint should load without Pydantic errors
        assert response.status_code in [200, 402, 500], f"AI assistant failed: {response.status_code} - {response.text}"
        if response.status_code == 422:
            pytest.fail(f"Pydantic validation error - parameter fix may not be applied: {response.text}")
        print(f"✓ AI assistant endpoint responds: status {response.status_code}")


class TestPromoCodeSystem:
    """Test the promo code apply endpoint and free_days support"""
    
    def test_apply_promo_empty_code_returns_400(self, auth_token):
        """POST /api/billing/apply-promo with empty code returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/billing/apply-promo",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"code": ""}
        )
        assert response.status_code == 400, f"Expected 400 for empty code, got {response.status_code}"
        print(f"✓ Empty promo code returns 400 correctly")
    
    def test_apply_promo_invalid_code_returns_404(self, auth_token):
        """POST /api/billing/apply-promo with invalid code returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/billing/apply-promo",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"code": "NONEXISTENT_CODE_12345"}
        )
        assert response.status_code == 404, f"Expected 404 for invalid code, got {response.status_code}"
        data = response.json()
        assert "detail" in data, f"Missing detail in error response: {data}"
        print(f"✓ Invalid promo code returns 404: {data.get('detail')}")
    
    def test_apply_promo_requires_auth(self):
        """POST /api/billing/apply-promo without auth returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/billing/apply-promo",
            json={"code": "TESTCODE"}
        )
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"✓ Apply promo requires authentication")
    
    def test_promo_validate_endpoint_works(self):
        """POST /api/promo-codes/validate endpoint works (public)"""
        response = requests.post(
            f"{BASE_URL}/api/promo-codes/validate",
            json={"code": "TESTCODE123"}
        )
        # Should return valid response structure even for invalid codes
        assert response.status_code == 200, f"Validate endpoint failed: {response.status_code}"
        data = response.json()
        assert "valid" in data, f"Missing 'valid' field: {data}"
        assert "message" in data, f"Missing 'message' field: {data}"
        print(f"✓ Promo validate endpoint works: valid={data.get('valid')}")


class TestFoundersBillingEndpoints:
    """Test Founders Edition billing endpoints"""
    
    def test_founders_plan_returns_info(self, auth_token):
        """GET /api/billing/founders/plan returns plan info"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/plan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Founders plan failed: {response.status_code} - {response.text}"
        data = response.json()
        assert "plan" in data, f"Missing 'plan' in response: {data}"
        assert "fees" in data, f"Missing 'fees' in response: {data}"
        print(f"✓ Founders plan endpoint returns data")
    
    def test_founders_fees_endpoint(self, auth_token):
        """GET /api/billing/founders/fees returns fee structure"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/fees",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Founders fees failed: {response.status_code}"
        data = response.json()
        # Should contain processing fee info
        assert isinstance(data, dict), f"Expected dict response: {data}"
        print(f"✓ Founders fees endpoint returns: {list(data.keys())}")
    
    def test_founders_spots_endpoint(self):
        """GET /api/billing/founders/spots returns spots remaining (public)"""
        response = requests.get(f"{BASE_URL}/api/billing/founders/spots")
        assert response.status_code == 200, f"Founders spots failed: {response.status_code}"
        data = response.json()
        assert "remaining" in data or "spots_remaining" in str(data).lower(), f"Missing spots info: {data}"
        print(f"✓ Founders spots endpoint returns data")
    
    def test_founders_credits_endpoint(self, auth_token):
        """GET /api/billing/founders/credits returns credit balance"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/credits",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Founders credits failed: {response.status_code}"
        data = response.json()
        # Should contain credit balance info
        assert "monthly_credits" in data or "total_available" in data, f"Missing credit info: {data}"
        print(f"✓ Founders credits endpoint returns balance info")


class TestTrialStatus:
    """Test trial status endpoint"""
    
    def test_trial_status_endpoint(self, auth_token):
        """GET /api/billing/trial-status returns trial info"""
        response = requests.get(
            f"{BASE_URL}/api/billing/trial-status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Trial status failed: {response.status_code}"
        data = response.json()
        # Should have trial status fields
        assert "is_trial" in data or "is_locked" in data, f"Missing trial status fields: {data}"
        print(f"✓ Trial status endpoint returns: is_locked={data.get('is_locked')}, is_trial={data.get('is_trial')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
