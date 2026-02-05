"""
Test suite for AI Tools API endpoints
Tests all 15 AI tools for sign shops
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# List of all 15 AI tools
ALL_TOOLS = [
    # Design Tools (6)
    'photo_enhancer',
    'image_vectorizer', 
    'font_identifier',
    'ai_sign_designer',
    'ai_banner_designer',
    'mockup_creator',
    # Branding Tools (2)
    'logo_creator',
    'branding_kit_generator',
    # Business Tools (3)
    'business_copywriter',
    'document_composer',
    'pricing_intelligence',
    # Marketing Tools (4)
    'social_job_post',
    'social_pack_generator',
    'content_calendar',
    'campaign_builder'
]

class TestAIToolsEndpoint:
    """Test AI generation endpoint with various tools"""
    
    def test_health_check(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✅ Health check passed")
    
    def test_ai_generate_photo_enhancer(self):
        """Test Photo Enhancer tool - Design category"""
        payload = {
            "tool": "photo_enhancer",
            "input_data": {
                "image_url": "https://example.com/test-image.jpg",
                "enhancement_notes": "Increase brightness, sharpen edges",
                "output_type": "print_optimized"
            }
        }
        response = requests.post(f"{BASE_URL}/api/ai/generate", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "tool" in data
        assert data["tool"] == "photo_enhancer"
        assert "output" in data
        assert len(data["output"]) > 0
        assert "input_data" in data
        assert "created_at" in data
        print(f"✅ Photo Enhancer test passed - Output length: {len(data['output'])} chars")
    
    def test_ai_generate_ai_sign_designer(self):
        """Test AI Sign Designer tool - Design category"""
        payload = {
            "tool": "ai_sign_designer",
            "input_data": {
                "business_type": "Restaurant",
                "sign_type": "channel_letters",
                "size": "4ft x 8ft",
                "colors": "Navy Blue #1E3A5F, Gold #D4AF37",
                "text_content": "BELLA ITALIA\nAuthentic Italian Cuisine\n555-123-4567",
                "style_preference": "elegant"
            }
        }
        response = requests.post(f"{BASE_URL}/api/ai/generate", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["tool"] == "ai_sign_designer"
        assert "output" in data
        assert len(data["output"]) > 100  # Should have substantial output
        print(f"✅ AI Sign Designer test passed - Output length: {len(data['output'])} chars")
    
    def test_ai_generate_campaign_builder(self):
        """Test Campaign Builder tool - Marketing category"""
        payload = {
            "tool": "campaign_builder",
            "input_data": {
                "campaign_type": "grand_opening",
                "campaign_goal": "Generate 50 new leads in first month",
                "target_audience": "Local business owners and restaurants within 10 miles",
                "budget_range": "1000_to_2500",
                "duration": "1_month",
                "channels": "Social media, Email, Local ads, Signage"
            }
        }
        response = requests.post(f"{BASE_URL}/api/ai/generate", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["tool"] == "campaign_builder"
        assert "output" in data
        assert len(data["output"]) > 100
        print(f"✅ Campaign Builder test passed - Output length: {len(data['output'])} chars")
    
    def test_ai_generate_unknown_tool(self):
        """Test that unknown tool returns 400 error"""
        payload = {
            "tool": "unknown_tool_xyz",
            "input_data": {"test": "data"}
        }
        response = requests.post(f"{BASE_URL}/api/ai/generate", json=payload)
        assert response.status_code == 400
        assert "Unknown tool" in response.json().get("detail", "")
        print("✅ Unknown tool error handling test passed")
    
    def test_ai_generate_missing_tool(self):
        """Test that missing tool field returns validation error"""
        payload = {
            "input_data": {"test": "data"}
        }
        response = requests.post(f"{BASE_URL}/api/ai/generate", json=payload)
        assert response.status_code == 422  # Validation error
        print("✅ Missing tool validation test passed")
    
    def test_ai_history_endpoint(self):
        """Test AI history endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ AI History endpoint test passed - {len(data)} records found")
    
    def test_ai_history_with_tool_filter(self):
        """Test AI history endpoint with tool filter"""
        response = requests.get(f"{BASE_URL}/api/ai/history?tool=photo_enhancer")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned items should be for photo_enhancer tool
        for item in data:
            assert item.get("tool") == "photo_enhancer"
        print(f"✅ AI History with filter test passed - {len(data)} photo_enhancer records")


class TestAllToolsValidation:
    """Validate all 15 tools are recognized by the backend"""
    
    @pytest.mark.parametrize("tool_name", ALL_TOOLS)
    def test_tool_is_recognized(self, tool_name):
        """Test that each tool is recognized (doesn't return 'Unknown tool' error)"""
        payload = {
            "tool": tool_name,
            "input_data": {"test_field": "test_value"}
        }
        response = requests.post(f"{BASE_URL}/api/ai/generate", json=payload)
        
        # Should not return 400 with "Unknown tool" error
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            assert "Unknown tool" not in detail, f"Tool '{tool_name}' is not recognized by backend"
        
        # 200 means successful generation, 500 might be API key issue but tool is recognized
        assert response.status_code in [200, 500], f"Unexpected status {response.status_code} for tool {tool_name}"
        print(f"✅ Tool '{tool_name}' is recognized by backend")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
