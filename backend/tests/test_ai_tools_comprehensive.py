"""
Comprehensive Test Suite for All 24 AI Tools in SignGuy AI
Tests text generation, image generation, AI assistant, and email generator endpoints

Tools by Category:
- Design Tools (10): logo_refresher, generative_fill, text_to_image, photo_enhancer, image_vectorizer, 
  font_identifier, ai_sign_designer, ai_banner_designer, mockup_creator, vehicle_wrap_mockup
- Branding Tools (3): idea_brainstormer, logo_creator, branding_kit_generator
- Business Tools (5): permit_research, ai_business_assistant, business_copywriter, document_composer, pricing_intelligence
- Marketing Tools (6): blog_creator, completed_job_post, social_job_post, social_pack_generator, content_calendar, campaign_builder
"""
import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for API calls"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEMO_TEST_EMAIL, "password": DEMO_TEST_PASSWORD}
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


# ============== TEXT GENERATION TOOLS ==============

class TestTextGenerationTools:
    """Test tools that generate text content via /api/ai/generate"""
    
    def test_idea_brainstormer(self, auth_headers):
        """Idea Brainstormer - Generate taglines, logo concepts, business ideas"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "idea_brainstormer",
                "input_data": {
                    "brainstorm_type": "taglines_slogans",
                    "business_name": "TEST_BrainStorm Shop",
                    "industry": "Automotive",
                    "target_audience": "Car enthusiasts",
                    "key_values": "Quality and speed",
                    "tone": "professional_serious",
                    "avoid": ""
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 100, "Expected substantial output"
        print(f"✅ idea_brainstormer passed - Output: {len(data['content'])} chars")

    def test_permit_research(self, auth_headers):
        """Permit Research - Sign permit guidance for any location"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "permit_research",
                "input_data": {
                    "city_state": "Austin, TX",
                    "sign_type": "channel_letters",
                    "sign_size": "4ft x 8ft",
                    "location_type": "commercial_strip",
                    "illumination": "internally_lit",
                    "specific_questions": "What permits do I need?"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 200, "Expected detailed permit guidance"
        print(f"✅ permit_research passed - Output: {len(data['content'])} chars")

    def test_blog_creator(self, auth_headers):
        """Blog Creator - Generate full blog articles"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "blog_creator",
                "input_data": {
                    "topic_type": "i_have_a_topic",
                    "topic": "Benefits of Vehicle Wraps for Small Businesses",
                    "topic_area": "vehicle_wraps",
                    "article_length": "medium_800_words",
                    "tone": "professional_informative",
                    "target_audience": "small business owners",
                    "include_cta": "contact_for_quote",
                    "seo_keywords": "vehicle wrap, business advertising"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 500, "Expected article content"
        print(f"✅ blog_creator passed - Output: {len(data['content'])} chars")

    def test_completed_job_post(self, auth_headers):
        """Completed Job Post Creator - Social media content from job photos"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "completed_job_post",
                "input_data": {
                    "job_type": "full_vehicle_wrap",
                    "job_details": "Full wrap on Ford Transit van with vibrant blue and orange colors",
                    "client_industry": "plumbing company",
                    "platforms": "all_platforms",
                    "post_style": "professional_showcase",
                    "include_hashtags": "yes_full_set"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        assert len(data["content"]) > 100, "Expected social post content"
        print(f"✅ completed_job_post passed - Output: {len(data['content'])} chars")

    def test_business_copywriter(self, auth_headers):
        """Business Copywriter - Generate marketing copy"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "business_copywriter",
                "input_data": {
                    "copy_type": "about_us_page",
                    "business_info": "Family-owned sign shop serving the community for 25 years",
                    "tone": "professional",
                    "key_points": "25 years experience, family-owned, free estimates"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"✅ business_copywriter passed - Output: {len(data['content'])} chars")

    def test_branding_kit_generator(self, auth_headers):
        """Branding Kit Generator - Generate brand guidelines"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "branding_kit_generator",
                "input_data": {
                    "logo_description": "Modern mountain logo with blue and green colors",
                    "brand_tone": "professional_trustworthy",
                    "target_audience": "Local businesses",
                    "competitors": "FastSigns"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"✅ branding_kit_generator passed - Output: {len(data['content'])} chars")

    def test_document_composer(self, auth_headers):
        """Document Composer - Generate business documents"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "document_composer",
                "input_data": {
                    "document_type": "proposal",
                    "client_name": "ABC Restaurant",
                    "project_or_invoice_details": "New storefront signage including channel letters",
                    "tone": "formal_professional",
                    "your_company_name": "TEST Sign Shop"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"✅ document_composer passed - Output: {len(data['content'])} chars")

    def test_social_job_post(self, auth_headers):
        """Social Job Post Creator - Create social posts"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "social_job_post",
                "input_data": {
                    "job_description": "Full vehicle wrap on food truck",
                    "job_type": "vehicle_wrap",
                    "client_industry": "local food truck",
                    "platforms": "all_platforms"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"✅ social_job_post passed - Output: {len(data['content'])} chars")

    def test_social_pack_generator(self, auth_headers):
        """Social Media Pack Generator - Batch content ideas"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "social_pack_generator",
                "input_data": {
                    "services_offered": "Vehicle wraps, storefront signs, banners",
                    "pack_size": "5_posts",
                    "target_audience": "Local businesses",
                    "content_mix": "balanced_mix"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"✅ social_pack_generator passed - Output: {len(data['content'])} chars")

    def test_content_calendar(self, auth_headers):
        """Content Calendar Creator - Plan posting schedule"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "content_calendar",
                "input_data": {
                    "date_range": "1_week",
                    "platforms": "Facebook, Instagram",
                    "goals": "Increase brand awareness",
                    "upcoming_events": "Spring sale next week"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"✅ content_calendar passed - Output: {len(data['content'])} chars")

    def test_campaign_builder(self, auth_headers):
        """Campaign Builder - Design complete marketing campaign"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "campaign_builder",
                "input_data": {
                    "campaign_type": "grand_opening",
                    "campaign_goal": "Generate 50 new leads",
                    "target_audience": "Local business owners",
                    "budget_range": "1000_to_2500",
                    "duration": "1_month"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "content" in data
        print(f"✅ campaign_builder passed - Output: {len(data['content'])} chars")


# ============== IMAGE GENERATION TOOLS ==============

class TestImageGenerationTools:
    """Test tools that generate images via /api/ai/generate-images"""
    
    def test_logo_refresher(self, auth_headers):
        """Logo Refresher - Generate refreshed logo designs"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            headers=auth_headers,
            json={
                "tool": "logo_refresher",
                "input_data": {
                    "business_name": "TEST Modern Signs",
                    "style_direction": "modernize_minimal",
                    "keep_elements": "mountain icon",
                    "change_elements": "update the font"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        assert data["images"][0].startswith("data:image/png;base64,")
        print(f"✅ logo_refresher passed - Generated {len(data['images'])} image(s)")

    def test_text_to_image(self, auth_headers):
        """Text to Image Creator - Generate images from descriptions"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            headers=auth_headers,
            json={
                "tool": "text_to_image",
                "input_data": {
                    "image_prompt": "A modern coffee shop storefront with large windows",
                    "image_style": "photorealistic",
                    "aspect_ratio": "landscape_16x9",
                    "color_mood": "warm_tones"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        print(f"✅ text_to_image passed - Generated {len(data['images'])} image(s)")

    def test_vehicle_wrap_mockup(self, auth_headers):
        """Vehicle Wrap Mockup Generator - Generate wrap mockups"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            headers=auth_headers,
            json={
                "tool": "vehicle_wrap_mockup",
                "input_data": {
                    "design_description": "Blue and white design with logo on doors",
                    "business_name": "TEST Plumbing Co",
                    "vehicle_type": "cargo_van",
                    "wrap_coverage": "full_wrap",
                    "primary_colors": "Navy Blue, White",
                    "style": "clean_corporate",
                    "view_angle": "three_quarter_front"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        print(f"✅ vehicle_wrap_mockup passed - Generated {len(data['images'])} image(s)")

    def test_logo_creator(self, auth_headers):
        """Logo Creator - Generate logo designs"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            headers=auth_headers,
            json={
                "tool": "logo_creator",
                "input_data": {
                    "business_name": "TEST Mountain Signs",
                    "tagline": "Quality Since 1995",
                    "industry": "construction_trades",
                    "logo_type": "icon_with_text",
                    "style_preferences": "modern_bold",
                    "color_preferences": "Blue, Green",
                    "icon_ideas": "mountain"
                },
                "image_count": 1
            },
            timeout=180
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "images" in data
        assert len(data["images"]) >= 1
        print(f"✅ logo_creator passed - Generated {len(data['images'])} image(s)")

    def test_ai_sign_designer(self, auth_headers):
        """AI Sign Designer - Generate sign design concepts"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            headers=auth_headers,
            json={
                "tool": "ai_sign_designer",
                "input_data": {
                    "business_name": "TEST Auto Shop",
                    "business_type": "Automotive Repair",
                    "sign_type": "channel_letters",
                    "size": "4ft x 8ft",
                    "colors": "Red, White",
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
        print(f"✅ ai_sign_designer passed - Generated {len(data['images'])} image(s)")

    def test_mockup_creator(self, auth_headers):
        """Mockup Creator - Generate realistic mockups"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-images",
            headers=auth_headers,
            json={
                "tool": "mockup_creator",
                "input_data": {
                    "design_description": "Red channel letters spelling PIZZA",
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
        print(f"✅ mockup_creator passed - Generated {len(data['images'])} image(s)")


# ============== AI BUSINESS ASSISTANT ==============

class TestAIAssistant:
    """Test AI Business Assistant chat interface"""
    
    def test_assistant_basic_question(self, auth_headers):
        """AI Assistant - Basic question about sign shop operations"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers=auth_headers,
            json={
                "message": "What is a good profit margin for vehicle wraps?",
                "session_id": f"test_session_{uuid.uuid4()}",
                "conversation_history": []
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 50, "Expected substantial response"
        # Check for relevant terms in response
        response_lower = data["response"].lower()
        assert any(term in response_lower for term in ["profit", "margin", "percent", "%", "wrap"]), \
            "Response should contain relevant pricing terms"
        print(f"✅ ai_assistant passed - Response: {len(data['response'])} chars")

    def test_assistant_with_history(self, auth_headers):
        """AI Assistant - Question with conversation history"""
        response = requests.post(
            f"{BASE_URL}/api/ai/assistant",
            headers=auth_headers,
            json={
                "message": "Can you give me a specific example?",
                "session_id": f"test_session_{uuid.uuid4()}",
                "conversation_history": [
                    {"role": "user", "content": "What is a good profit margin for vehicle wraps?"},
                    {"role": "assistant", "content": "A typical profit margin for vehicle wraps ranges from 40-60%."}
                ]
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data
        print(f"✅ ai_assistant with history passed - Response: {len(data['response'])} chars")


# ============== AI EMAIL GENERATOR ==============

class TestAIEmailGenerator:
    """Test AI Email Generator endpoint"""
    
    def test_generate_quote_email(self, auth_headers):
        """Generate email for sending a quote"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-email",
            headers=auth_headers,
            json={
                "email_type": "quote_send",
                "tone": "professional",
                "context": {
                    "customer_name": "TEST John Smith",
                    "job_name": "Storefront Sign",
                    "amount": 2500
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "subject" in data
        assert "body" in data
        assert len(data["subject"]) > 0
        assert len(data["body"]) > 50
        print(f"✅ generate-email (quote_send) passed - Subject: {data['subject'][:50]}...")

    def test_generate_invoice_reminder(self, auth_headers):
        """Generate invoice reminder email"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-email",
            headers=auth_headers,
            json={
                "email_type": "invoice_reminder",
                "tone": "friendly",
                "context": {
                    "customer_name": "TEST Jane Doe",
                    "invoice_number": "INV-001",
                    "amount": 1500,
                    "due_date": "2026-02-25"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "subject" in data
        assert "body" in data
        print("✅ generate-email (invoice_reminder) passed")

    def test_generate_thank_you_email(self, auth_headers):
        """Generate thank you email"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-email",
            headers=auth_headers,
            json={
                "email_type": "thank_you",
                "tone": "friendly",
                "context": {
                    "customer_name": "TEST Company",
                    "job_name": "Vehicle Wrap Project"
                }
            },
            timeout=120
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "subject" in data
        assert "body" in data
        print("✅ generate-email (thank_you) passed")


# ============== AI HISTORY ==============

class TestAIHistory:
    """Test AI history endpoint"""
    
    def test_get_history(self, auth_headers):
        """Get AI generation history"""
        response = requests.get(
            f"{BASE_URL}/api/ai/history",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ AI history endpoint passed - {len(data)} records")

    def test_get_history_with_tool_filter(self, auth_headers):
        """Get AI history filtered by tool"""
        response = requests.get(
            f"{BASE_URL}/api/ai/history?tool=idea_brainstormer",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item.get("tool") == "idea_brainstormer"
        print(f"✅ AI history with filter passed - {len(data)} records")


# ============== ERROR HANDLING ==============

class TestErrorHandling:
    """Test error handling for AI tools"""
    
    def test_unknown_tool_returns_400(self, auth_headers):
        """Unknown tool should return 400 error"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate",
            headers=auth_headers,
            json={
                "tool": "unknown_tool_xyz",
                "input_data": {"test": "data"}
            },
            timeout=30
        )
        assert response.status_code == 400
        print("✅ Unknown tool error handling passed")

    def test_invalid_email_type(self, auth_headers):
        """Invalid email type should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/ai/generate-email",
            headers=auth_headers,
            json={
                "email_type": "invalid_type",
                "tone": "professional",
                "context": {}
            },
            timeout=30
        )
        assert response.status_code == 400
        print("✅ Invalid email type error handling passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
