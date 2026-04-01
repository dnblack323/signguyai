"""
Test suite for AI Product Description Generator endpoint
Tests the /api/ai/generate-product-description endpoint for webstore products
"""
import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": FALLBACK_TEST_EMAIL,
        "password": FALLBACK_TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping tests")


class TestProductDescriptionGenerator:
    """Test AI Product Description Generator endpoint"""
    
    def test_health_check(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("Health check passed")
    
    def test_generate_product_description_success(self, auth_token):
        """Test successful product description generation with all fields"""
        payload = {
            "product_name": "Custom Yard Sign 18x24",
            "product_category": "Signs",
            "product_features": "Corrugated plastic, weatherproof, double-sided printing, includes H-stake",
            "target_audience": "Real estate agents and small businesses",
            "tone": "professional",
            "price": 29.99
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-product-description",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "description" in data, "Response missing 'description' field"
        assert "headline" in data, "Response missing 'headline' field"
        assert "bullet_points" in data, "Response missing 'bullet_points' field"
        assert "call_to_action" in data, "Response missing 'call_to_action' field"
        assert "id" in data, "Response missing 'id' field (history entry)"
        
        # Verify data types
        assert isinstance(data["description"], str), "Description should be a string"
        assert isinstance(data["bullet_points"], list), "Bullet points should be a list"
        assert isinstance(data["id"], str), "ID should be a string"
        
        # Verify description content
        assert len(data["description"]) > 100, "Description should be substantial (>100 chars)"
        
        print(f"Product description generated successfully - {len(data['description'])} chars")
        print(f"Headline: {data['headline'][:80]}...")
        print(f"Bullet points: {len(data['bullet_points'])} items")
        print(f"CTA: {data['call_to_action'][:60]}...")
    
    def test_generate_description_minimal_fields(self, auth_token):
        """Test generation with minimal required fields"""
        payload = {
            "product_name": "Business Cards 500pc"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-product-description",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "description" in data
        assert len(data["description"]) > 50
        print(f"Minimal fields test passed - {len(data['description'])} chars generated")
    
    def test_generate_description_different_tones(self, auth_token):
        """Test generation with different tone settings"""
        tones = ["professional", "friendly", "enthusiastic", "premium", "technical", "casual"]
        
        for tone in tones:
            payload = {
                "product_name": "Custom T-Shirt",
                "product_category": "Apparel",
                "tone": tone,
                "price": 24.99
            }
            
            response = requests.post(
                f"{BASE_URL}/api/ai/generate-product-description",
                json=payload,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200, f"Tone '{tone}' failed: {response.text}"
            data = response.json()
            assert len(data["description"]) > 50
            print(f"Tone '{tone}' test passed")
    
    def test_generate_description_invalid_tone_defaults(self, auth_token):
        """Test that invalid tone defaults to professional"""
        payload = {
            "product_name": "Test Product",
            "tone": "invalid_tone_xyz"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-product-description",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should not fail - should default to professional
        assert response.status_code == 200, f"Expected 200 (fallback to default tone), got {response.status_code}"
        print("Invalid tone fallback test passed")
    
    def test_generate_description_requires_auth(self):
        """Test that endpoint requires authentication"""
        payload = {
            "product_name": "Test Product"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-product-description",
            json=payload
            # No Authorization header
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthenticated request, got {response.status_code}"
        print("Auth requirement test passed")
    
    def test_generate_description_missing_product_name(self, auth_token):
        """Test that missing product_name returns validation error"""
        payload = {
            "product_category": "Signs",
            "tone": "professional"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-product-description",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422, f"Expected 422 validation error, got {response.status_code}"
        print("Missing product_name validation test passed")
    
    def test_generate_description_all_categories(self, auth_token):
        """Test generation with different product categories"""
        categories = ["Apparel", "Signs", "Decals", "Promotional", "Other"]
        
        for category in categories:
            payload = {
                "product_name": f"Custom {category} Product",
                "product_category": category,
                "price": 19.99
            }
            
            response = requests.post(
                f"{BASE_URL}/api/ai/generate-product-description",
                json=payload,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code == 200, f"Category '{category}' failed: {response.text}"
            print(f"Category '{category}' test passed")
    
    def test_generate_description_saved_to_history(self, auth_token):
        """Test that generation is saved to AI history"""
        # Generate a description
        payload = {
            "product_name": "TEST_HISTORY_Custom Banner",
            "product_category": "Signs"
        }
        
        gen_response = requests.post(
            f"{BASE_URL}/api/ai/generate-product-description",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert gen_response.status_code == 200
        gen_id = gen_response.json().get("id")
        
        # Check history for the entry
        history_response = requests.get(
            f"{BASE_URL}/api/ai/history?tool=product_description&limit=5",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert history_response.status_code == 200
        history = history_response.json()
        
        # Find our entry in history
        found = False
        for entry in history:
            if entry.get("id") == gen_id:
                found = True
                assert entry.get("tool") == "product_description"
                assert "TEST_HISTORY_Custom Banner" in str(entry.get("input_data", {}))
                break
        
        assert found, f"Generated entry {gen_id} not found in history"
        print(f"History test passed - entry {gen_id} saved to AI history")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
