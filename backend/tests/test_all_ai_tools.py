"""
Comprehensive Test Suite for All 15 AI Tools in Sign Guy AI
Tests:
- Design Tools (Vision): Photo Enhancer, Vectorization Analyzer, Font Identifier
- Design Tools (Image Gen): AI Sign Designer, AI Banner Designer, Mockup Creator
- Branding Tools: Logo Creator (Image Gen), Branding Kit Generator (Text)
- Business Tools: Business Copywriter, Document Composer, Pricing Intelligence (All Text)
- Marketing Tools: Social Job Post, Social Media Pack, Content Calendar, Campaign Builder (All Text)
"""
import pytest
import requests
import os
import base64
from pathlib import Path

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test image path
TEST_IMAGE_PATH = "/tmp/test_font_image.png"

def get_test_image_base64():
    """Load test image and convert to base64"""
    if Path(TEST_IMAGE_PATH).exists():
        with open(TEST_IMAGE_PATH, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    # Fallback: minimal valid PNG
    return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mNk+M9QzwAEjDAGNzYAAIoaB/lnvJMAAAAASUVORK5CYII="


class TestHealthAndSetup:
    """Verify API is accessible before running AI tests"""
    
    def test_api_health(self):
        """Verify API is healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        print("✅ API Health check passed")


# ============== DESIGN TOOLS - VISION (Image Analysis) ==============

class TestVisionTools:
    """Test tools that analyze uploaded images using Gemini vision"""
    
    def test_photo_enhancer_with_image(self):
        """Photo Enhancer - Upload image, get vision-based analysis and print recommendations"""
        image_base64 = get_test_image_base64()
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "photo_enhancer",
                "input_data": {
                    "image_upload": image_base64,
                    "enhancement_notes": "Need for large banner print, fix colors",
                    "output_type": "print_large_format"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "photo_enhancer"
        assert "output" in data
        assert len(data["output"]) > 100, "Expected substantial analysis output"
        # Check for expected content in analysis
        output_lower = data["output"].lower()
        assert any(word in output_lower for word in ["quality", "resolution", "print", "enhancement", "image"]), \
            "Output should contain image analysis terms"
        print(f"✅ Photo Enhancer vision analysis passed - Output: {len(data['output'])} chars")
        print(f"   Sample: {data['output'][:200]}...")
    
    def test_vectorization_analyzer_with_image(self):
        """Vectorization Analyzer - Upload image, get vectorization guidance via vision analysis"""
        image_base64 = get_test_image_base64()
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "image_vectorizer",
                "input_data": {
                    "image_upload": image_base64,
                    "num_colors": "4_colors",
                    "image_type": "logo_clean_edges"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "image_vectorizer"
        assert "output" in data
        assert len(data["output"]) > 100, "Expected substantial vectorization guidance"
        output_lower = data["output"].lower()
        assert any(word in output_lower for word in ["vector", "path", "color", "svg", "complexity"]), \
            "Output should contain vectorization terms"
        print(f"✅ Vectorization Analyzer vision analysis passed - Output: {len(data['output'])} chars")
        print(f"   Sample: {data['output'][:200]}...")
    
    def test_font_identifier_with_image(self):
        """Font Identifier - Upload image with text, identify fonts using vision"""
        image_base64 = get_test_image_base64()
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "font_identifier",
                "input_data": {
                    "image_upload": image_base64,
                    "text_sample": "GRAND OPENING"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "font_identifier"
        assert "output" in data
        assert len(data["output"]) > 100, "Expected substantial font analysis"
        output_lower = data["output"].lower()
        assert any(word in output_lower for word in ["font", "typeface", "serif", "sans", "style", "typography"]), \
            "Output should contain font identification terms"
        print(f"✅ Font Identifier vision analysis passed - Output: {len(data['output'])} chars")
        print(f"   Sample: {data['output'][:200]}...")


# ============== DESIGN TOOLS - IMAGE GENERATION ==============

class TestImageGenerationTools:
    """Test tools that generate images using OpenAI image generation"""
    
    def test_ai_sign_designer_generates_images(self):
        """AI Sign Designer - Generate sign design images based on inputs"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "ai_sign_designer",
                "input_data": {
                    "business_name": "Joe's Auto Shop",
                    "business_type": "Automotive Repair",
                    "sign_type": "channel_letters",
                    "size": "4ft x 8ft",
                    "colors": "Red, White, Blue",
                    "additional_text": "Open 7 Days",
                    "style_preference": "modern_clean"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print(f"✅ AI Sign Designer image generation passed - Generated {len(data['images'])} image(s)")
    
    def test_ai_banner_designer_generates_images(self):
        """AI Banner Designer - Generate banner design images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "ai_banner_designer",
                "input_data": {
                    "headline": "GRAND OPENING SALE!",
                    "subtext": "50% OFF Everything - This Weekend Only!",
                    "banner_size": "4x8ft",
                    "event_type": "grand_opening",
                    "brand_colors": "Red, Gold, White",
                    "style": "bold_modern"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print(f"✅ AI Banner Designer image generation passed - Generated {len(data['images'])} image(s)")
    
    def test_mockup_creator_generates_images(self):
        """Mockup Creator - Generate mockup images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "mockup_creator",
                "input_data": {
                    "design_description": "Red channel letters spelling PIZZA on white background with Italian flag colors",
                    "product_type": "storefront_sign",
                    "environment": "urban_street_day"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print(f"✅ Mockup Creator image generation passed - Generated {len(data['images'])} image(s)")


# ============== BRANDING TOOLS ==============

class TestBrandingTools:
    """Test branding tools - Logo Creator (image gen) and Branding Kit (text)"""
    
    def test_logo_creator_generates_images(self):
        """Logo Creator - Generate logo design images"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "logo_creator",
                "input_data": {
                    "business_name": "Mountain View Signs",
                    "tagline": "Quality Signs Since 1995",
                    "industry": "construction_trades",
                    "logo_type": "icon_with_text",
                    "style_preferences": "modern_bold",
                    "color_preferences": "Blue, Green, White",
                    "icon_ideas": "mountain, sign, tools"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0]["url"].startswith("data:image/png;base64,")
        print(f"✅ Logo Creator image generation passed - Generated {len(data['images'])} image(s)")
    
    def test_branding_kit_generator_text(self):
        """Branding Kit Generator - Text-only, generate brand guidelines"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "branding_kit_generator",
                "input_data": {
                    "logo_description": "Modern mountain logo with blue and green colors, clean sans-serif font",
                    "brand_tone": "professional_trustworthy",
                    "target_audience": "Local businesses, contractors, and restaurants looking for quality signage",
                    "competitors": "FastSigns, SignWarehouse"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "branding_kit_generator"
        assert "output" in data
        assert len(data["output"]) > 200, "Expected comprehensive brand guidelines"
        output_lower = data["output"].lower()
        assert any(word in output_lower for word in ["brand", "color", "font", "guideline", "identity"]), \
            "Output should contain branding terms"
        print(f"✅ Branding Kit Generator passed - Output: {len(data['output'])} chars")


# ============== BUSINESS TOOLS (All Text-Only) ==============

class TestBusinessTools:
    """Test business tools - all text-only generation"""
    
    def test_business_copywriter(self):
        """Business Copywriter - Text-only, generate marketing copy"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "business_copywriter",
                "input_data": {
                    "copy_type": "about_us_page",
                    "business_info": "Family-owned sign shop serving the community for 25 years. Specializing in vehicle wraps, storefront signs, and banners.",
                    "tone": "professional",
                    "key_points": "25 years experience, family-owned, free estimates, fast turnaround"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "business_copywriter"
        assert "output" in data
        assert len(data["output"]) > 100
        print(f"✅ Business Copywriter passed - Output: {len(data['output'])} chars")
    
    def test_document_composer(self):
        """Document Composer - Text-only, generate business documents"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "document_composer",
                "input_data": {
                    "document_type": "proposal",
                    "client_name": "ABC Restaurant",
                    "project_or_invoice_details": "New storefront signage including channel letters, window graphics, and menu boards. Estimated cost $5,500.",
                    "tone": "formal_professional",
                    "your_company_name": "Mountain View Signs"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "document_composer"
        assert "output" in data
        assert len(data["output"]) > 200
        print(f"✅ Document Composer passed - Output: {len(data['output'])} chars")
    
    def test_pricing_intelligence(self):
        """Pricing Intelligence - Text-only, analyze pricing"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "pricing_intelligence",
                "input_data": {
                    "service_type": "Vehicle Wrap - Full Wrap",
                    "specifications": "Full wrap on Ford Transit van, 3M vinyl, custom design with logo and contact info",
                    "material_cost": "800",
                    "labor_hours": "16",
                    "current_price": "3500"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "pricing_intelligence"
        assert "output" in data
        assert len(data["output"]) > 100
        output_lower = data["output"].lower()
        assert any(word in output_lower for word in ["price", "margin", "profit", "cost", "market"]), \
            "Output should contain pricing analysis terms"
        print(f"✅ Pricing Intelligence passed - Output: {len(data['output'])} chars")


# ============== MARKETING TOOLS (All Text-Only) ==============

class TestMarketingTools:
    """Test marketing tools - all text-only generation"""
    
    def test_social_job_post_creator(self):
        """Social Job Post Creator - Text-only, create social media posts"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "social_job_post",
                "input_data": {
                    "job_description": "Completed a full vehicle wrap on a food truck with vibrant graphics featuring tacos and Mexican food imagery",
                    "job_type": "vehicle_wrap",
                    "client_industry": "local food truck business",
                    "platforms": "all_platforms"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "social_job_post"
        assert "output" in data
        assert len(data["output"]) > 50
        print(f"✅ Social Job Post Creator passed - Output: {len(data['output'])} chars")
    
    def test_social_media_pack_generator(self):
        """Social Media Pack Generator - Text-only"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "social_pack_generator",
                "input_data": {
                    "services_offered": "Vehicle wraps, storefront signs, banners, window graphics, dimensional letters",
                    "pack_size": "10_posts",
                    "target_audience": "Local businesses, restaurants, contractors",
                    "content_mix": "balanced_mix"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "social_pack_generator"
        assert "output" in data
        assert len(data["output"]) > 200
        print(f"✅ Social Media Pack Generator passed - Output: {len(data['output'])} chars")
    
    def test_content_calendar_creator(self):
        """Content Calendar Creator - Text-only"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "content_calendar",
                "input_data": {
                    "date_range": "1_month",
                    "platforms": "Facebook, Instagram",
                    "goals": "Increase brand awareness and generate 10 new leads per month",
                    "upcoming_events": "Spring sale in 2 weeks, local business expo next month"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "content_calendar"
        assert "output" in data
        assert len(data["output"]) > 200
        print(f"✅ Content Calendar Creator passed - Output: {len(data['output'])} chars")
    
    def test_campaign_builder(self):
        """Campaign Builder - Text-only"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "campaign_builder",
                "input_data": {
                    "campaign_type": "grand_opening",
                    "campaign_goal": "Generate 50 new leads in first month",
                    "target_audience": "Local business owners and restaurants within 10 miles",
                    "budget_range": "1000_to_2500",
                    "duration": "1_month"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["tool"] == "campaign_builder"
        assert "output" in data
        assert len(data["output"]) > 200
        output_lower = data["output"].lower()
        assert any(word in output_lower for word in ["campaign", "marketing", "strategy", "goal", "audience"]), \
            "Output should contain campaign planning terms"
        print(f"✅ Campaign Builder passed - Output: {len(data['output'])} chars")


# ============== ERROR HANDLING ==============

class TestErrorHandling:
    """Test error handling for AI tools"""
    
    def test_unknown_tool_returns_400(self):
        """Unknown tool should return 400 error"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "unknown_tool_xyz",
                "input_data": {"test": "data"}
            },
            timeout=30
        )
        assert response.status_code == 400
        assert "Unknown tool" in response.json().get("detail", "")
        print("✅ Unknown tool error handling passed")
    
    def test_unsupported_image_tool_returns_400(self):
        """Unsupported image generation tool should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            json={
                "tool": "branding_kit_generator",  # This is text-only, not image gen
                "input_data": {},
                "image_count": 1
            },
            timeout=30
        )
        assert response.status_code == 400
        assert "not supported" in response.json().get("detail", "").lower()
        print("✅ Unsupported image tool error handling passed")


# ============== AI HISTORY ==============

class TestAIHistory:
    """Test AI history endpoint"""
    
    def test_ai_history_endpoint(self):
        """AI history should return list of past generations"""
        response = requests.get(f"{BASE_URL}/api/ai/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ AI History endpoint passed - {len(data)} records found")
    
    def test_ai_history_with_tool_filter(self):
        """AI history should filter by tool"""
        response = requests.get(f"{BASE_URL}/api/ai/history?tool=campaign_builder")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item.get("tool") == "campaign_builder"
        print(f"✅ AI History with filter passed - {len(data)} campaign_builder records")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
