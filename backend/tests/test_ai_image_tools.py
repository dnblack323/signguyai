"""
Test AI Image Generation Tools
Tests for Photo Enhancer, Image Vectorizer, Font Identifier, AI Banner Designer, Logo Creator
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAIImageGeneration:
    """Test AI image generation endpoints"""
    
    def test_health_check(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passed")
    
    def test_logo_creator_image_generation(self):
        """Test logo creator generates images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "logo_creator",
                "input_data": {
                    "business_name": "Test Logo",
                    "industry": "technology",
                    "style_preferences": "modern",
                    "color_preferences": "blue and white"
                },
                "image_count": 1
            },
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print("✅ Logo Creator image generation passed")
    
    def test_ai_banner_designer_image_generation(self):
        """Test AI Banner Designer generates images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "ai_banner_designer",
                "input_data": {
                    "headline": "GRAND OPENING",
                    "subtext": "Join us for our grand opening celebration!",
                    "banner_size": "4x8ft",
                    "event_type": "grand_opening",
                    "brand_colors": "red, white, blue",
                    "style": "bold_modern"
                },
                "image_count": 1
            },
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print("✅ AI Banner Designer image generation passed")
    
    def test_ai_sign_designer_image_generation(self):
        """Test AI Sign Designer generates images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "ai_sign_designer",
                "input_data": {
                    "business_name": "Joe's Auto Shop",
                    "business_type": "Automotive",
                    "sign_type": "channel_letters",
                    "size": "4ft x 8ft",
                    "colors": "Red, White",
                    "style_preference": "modern_clean"
                },
                "image_count": 1
            },
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print("✅ AI Sign Designer image generation passed")
    
    def test_photo_enhancer_image_generation(self):
        """Test Photo Enhancer generates images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "photo_enhancer",
                "input_data": {
                    "image_description": "A low quality photo of a storefront sign",
                    "enhancement_notes": "increase brightness, sharpen text",
                    "output_type": "print_large_format"
                },
                "image_count": 1
            },
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print("✅ Photo Enhancer image generation passed")
    
    def test_image_vectorizer_image_generation(self):
        """Test Image Vectorizer generates images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "image_vectorizer",
                "input_data": {
                    "image_description": "A simple logo with text",
                    "num_colors": "4_colors",
                    "image_type": "crisp_line_art"
                },
                "image_count": 1
            },
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print("✅ Image Vectorizer image generation passed")
    
    def test_unsupported_tool_returns_error(self):
        """Test that unsupported tools return 400 error"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "unsupported_tool",
                "input_data": {},
                "image_count": 1
            },
            timeout=30
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not supported" in data["detail"].lower()
        print("✅ Unsupported tool error handling passed")


class TestFontIdentifier:
    """Test Font Identifier text generation (not image)"""
    
    def test_font_identifier_text_generation(self):
        """Test Font Identifier generates text analysis"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "font_identifier",
                "input_data": {
                    "image_upload": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                    "text_sample": "GRAND OPENING"
                }
            },
            timeout=120
        )
        assert response.status_code == 200
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        print("✅ Font Identifier text generation passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
