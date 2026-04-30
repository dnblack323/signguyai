"""
Backend tests for:
1) Customer Branding Profile endpoints (GET/PUT/POST append)
2) Document Library new categories from AI (POST /documents/from-ai)
3) Marketing AI tools regressions: completed_job_post (merged with post_mode),
   social_pack_generator, content_calendar (new fields)
"""
import os
import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
        except FileNotFoundError:
            pass
    return url.rstrip("/")

BASE_URL = _load_backend_url()
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_headers():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Admin auth failed: {r.status_code} {r.text}")
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def customer_id(auth_headers):
    # Create a throwaway TEST_ customer
    payload = {"name": "TEST_BrandingCustomer", "company": "TEST_BrandCo", "email": "test_brand@example.com"}
    r = requests.post(f"{BASE_URL}/api/customers", json=payload, headers=auth_headers, timeout=20)
    assert r.status_code == 200, r.text
    cid = r.json()["id"]
    yield cid
    # teardown
    requests.delete(f"{BASE_URL}/api/customers/{cid}", headers=auth_headers, timeout=10)


# -------- BRANDING PROFILE --------
class TestBrandingProfile:
    def test_get_empty_branding(self, auth_headers, customer_id):
        r = requests.get(f"{BASE_URL}/api/customers/{customer_id}/branding", headers=auth_headers, timeout=10)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "business_name" in data
        assert data.get("taglines") == []
        assert data.get("logos") == []

    def test_put_branding_replaces_and_stamps(self, auth_headers, customer_id):
        body = {
            "business_name": "Acme Signs",
            "industry": "Signage",
            "target_audience": "Small businesses",
            "brand_colors": ["#FF0000", "#00FF00"],
            "taglines": ["Sign your way"],
            "selected_tagline": "Sign your way",
        }
        r = requests.put(f"{BASE_URL}/api/customers/{customer_id}/branding", json=body, headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["business_name"] == "Acme Signs"
        assert data["updated_at"] is not None
        assert data["updated_by_email"] == ADMIN_EMAIL

        # GET to verify persistence
        r2 = requests.get(f"{BASE_URL}/api/customers/{customer_id}/branding", headers=auth_headers, timeout=10)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["business_name"] == "Acme Signs"
        assert d2["brand_colors"] == ["#FF0000", "#00FF00"]

    def test_append_tagline_and_select(self, auth_headers, customer_id):
        r = requests.post(
            f"{BASE_URL}/api/customers/{customer_id}/branding/append",
            json={"tagline": "Best signs in town", "select_tagline": True},
            headers=auth_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "Best signs in town" in data["taglines"]
        assert data["selected_tagline"] == "Best signs in town"
        # Prior tagline should still exist (append, not replace)
        assert "Sign your way" in data["taglines"]

    def test_append_logo_caps_at_three(self, auth_headers, customer_id):
        # push 4 logos, expect only last 3 retained
        for i in range(4):
            r = requests.post(
                f"{BASE_URL}/api/customers/{customer_id}/branding/append",
                json={"logo": {"image_url": f"data:image/png;base64,AAA{i}", "summary": f"Logo {i}", "source_tool": "logo_creator"}},
                headers=auth_headers, timeout=15,
            )
            assert r.status_code == 200, r.text
        data = r.json()
        assert len(data["logos"]) == 3
        # should be the last 3 (logos 1,2,3)
        summaries = [lg["summary"] for lg in data["logos"]]
        assert summaries == ["Logo 1", "Logo 2", "Logo 3"]

    def test_append_brand_kit_without_trampling(self, auth_headers, customer_id):
        r = requests.post(
            f"{BASE_URL}/api/customers/{customer_id}/branding/append",
            json={
                "brand_kit_text": "Complete brand kit here",
                "brand_colors": ["#0000FF"],
                "font_suggestions": ["Inter", "Roboto"],
            },
            headers=auth_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["brand_kit_text"] == "Complete brand kit here"
        # Existing brand_colors preserved + new one appended
        assert "#FF0000" in data["brand_colors"]
        assert "#0000FF" in data["brand_colors"]
        assert "Inter" in data["font_suggestions"]
        # Business name preserved
        assert data["business_name"] == "Acme Signs"
        # Logos preserved
        assert len(data["logos"]) == 3


# -------- DOCUMENTS FROM AI (new categories) --------
NEW_CATEGORIES = [
    "social_post", "marketing_content", "content_calendar", "campaign_plan",
    "blog_article", "logo_concept", "brand_kit", "tagline",
]


class TestDocumentsFromAICategories:
    @pytest.mark.parametrize("category", NEW_CATEGORIES)
    def test_from_ai_accepts_new_category(self, auth_headers, category):
        r = requests.post(
            f"{BASE_URL}/api/documents/from-ai",
            json={
                "content": f"TEST {category} short content",
                "name": f"TEST_{category}_doc",
                "tool_id": "pytest_tool",
                "category": category,
            },
            headers=auth_headers, timeout=20,
        )
        assert r.status_code == 200, f"{category}: {r.status_code} {r.text}"
        data = r.json()
        assert data["category"] == category, f"expected {category}, got {data.get('category')}"
        # cleanup
        try:
            requests.delete(f"{BASE_URL}/api/documents/{data['id']}", headers=auth_headers, timeout=10)
        except Exception:
            pass


# -------- AI GENERATE MARKETING TOOLS (regression) --------
class TestAIGenerateMarketingTools:
    def test_completed_job_post_text_only_no_500(self, auth_headers):
        """Ensure merged tool doesn't KeyError on new placeholders."""
        r = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "completed_job_post",
                "input_data": {
                    "post_mode": "text_only",
                    "job_type": "Vehicle wrap",
                    "job_description": "Full wrap in matte black for a pickup truck.",
                    "job_details": "Finished in 3 days.",
                    "client_industry": "Landscaping",
                    "platforms": "instagram",
                    "post_style": "professional",
                    "brand_voice": "friendly",
                    "include_hashtags": True,
                },
            },
            headers=auth_headers, timeout=90,
        )
        # Real LLM; must not be 500 KeyError
        assert r.status_code != 500, f"500 error (likely KeyError): {r.text[:500]}"
        assert r.status_code in (200, 201), f"Unexpected status {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert body.get("content") or body.get("result") or body.get("output"), f"No content returned: {body}"

    def test_social_pack_generator_new_fields(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "social_pack_generator",
                "input_data": {
                    "business_name": "Acme Signs",
                    "services_offered": "Vehicle wraps, channel letters, LED signs",
                    "pack_size": "5",
                    "platforms": "instagram, facebook",
                    "brand_voice": "bold and energetic",
                },
            },
            headers=auth_headers, timeout=90,
        )
        assert r.status_code != 500, f"500 error: {r.text[:500]}"
        assert r.status_code in (200, 201), f"Unexpected status {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert body.get("content") or body.get("result") or body.get("output"), f"No content returned: {body}"

    def test_content_calendar_new_fields(self, auth_headers):
        r = requests.post(
            f"{BASE_URL}/api/ai/generate",
            json={
                "tool": "content_calendar",
                "input_data": {
                    "business_name": "Acme Signs",
                    "start_date": "2026-02-01",
                    "post_frequency": "3x per week",
                    "brand_voice": "professional",
                    "target_audience": "SMBs",
                    "months": "1",
                },
            },
            headers=auth_headers, timeout=90,
        )
        assert r.status_code != 500, f"500 error: {r.text[:500]}"
        assert r.status_code in (200, 201), f"Unexpected status {r.status_code}: {r.text[:300]}"
        body = r.json()
        assert body.get("content") or body.get("result") or body.get("output"), f"No content returned: {body}"
