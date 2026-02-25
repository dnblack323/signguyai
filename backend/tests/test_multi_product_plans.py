"""
Multi-Product Plan API Tests

Tests for the new 9-plan system across 3 product lines:
1. SignGuy AI OS (Shop Management) - Starter/Pro/Business
2. SignGuy Webstores (Commerce-Only) - Launch/Growth/Scale
3. SignGuy AI Studio (AI-Only) - Basic/Pro/Max

Verifies:
- Plan listing endpoints (all, by product line)
- Founder pricing availability (OS only)
- Plan details with UI visibility flags
- Authenticated plan/feature access endpoints
"""

import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


@pytest.fixture(scope="module")
def api_client():
    """Create shared HTTP session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "billing_test@example.com", "password": "TestPass123!"},
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Authentication failed - skipping authenticated tests")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestGetAllPlans:
    """GET /api/plans/all - Returns 3 product lines with 3 plans each"""

    def test_returns_all_product_lines(self, api_client):
        """Should return exactly 3 product lines"""
        response = api_client.get(f"{BASE_URL}/api/plans/all")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3, f"Expected 3 product lines, got {len(data)}"

    def test_product_line_names(self, api_client):
        """Should return correct product line identifiers and display names"""
        response = api_client.get(f"{BASE_URL}/api/plans/all")
        data = response.json()
        
        product_lines = {pl["product_line"]: pl["display_name"] for pl in data}
        assert "os" in product_lines
        assert "webstores" in product_lines
        assert "ai_studio" in product_lines
        
        assert product_lines["os"] == "SignGuy AI OS"
        assert product_lines["webstores"] == "SignGuy Webstores"
        assert product_lines["ai_studio"] == "SignGuy AI Studio"

    def test_each_product_line_has_3_plans(self, api_client):
        """Each product line should have exactly 3 plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/all")
        data = response.json()
        
        for pl in data:
            assert len(pl["plans"]) == 3, f"{pl['product_line']} has {len(pl['plans'])} plans, expected 3"

    def test_total_9_plans(self, api_client):
        """Should return 9 total plans across all product lines"""
        response = api_client.get(f"{BASE_URL}/api/plans/all")
        data = response.json()
        
        total_plans = sum(len(pl["plans"]) for pl in data)
        assert total_plans == 9, f"Expected 9 total plans, got {total_plans}"


class TestOSPlans:
    """GET /api/plans/os - Returns OS plans with founder pricing"""

    def test_returns_3_os_plans(self, api_client):
        """Should return exactly 3 OS plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/os")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_os_plan_types(self, api_client):
        """Should return Starter, Pro, Business plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/os")
        data = response.json()
        
        plan_types = {p["plan_type"] for p in data}
        assert plan_types == {"os_starter", "os_pro", "os_business"}

    def test_all_os_plans_founder_eligible(self, api_client):
        """All OS plans should be founder eligible"""
        response = api_client.get(f"{BASE_URL}/api/plans/os")
        data = response.json()
        
        for plan in data:
            assert plan["founder_eligible"] is True, f"{plan['plan_type']} should be founder eligible"
            assert plan["founder_price_monthly"] is not None, f"{plan['plan_type']} missing founder monthly price"
            assert plan["founder_price_annual"] is not None, f"{plan['plan_type']} missing founder annual price"

    def test_os_pricing_tiers(self, api_client):
        """OS plans should have correct pricing hierarchy"""
        response = api_client.get(f"{BASE_URL}/api/plans/os")
        data = response.json()
        
        prices = {p["plan_type"]: p["price_monthly"] for p in data}
        assert prices["os_starter"] == 39.0
        assert prices["os_pro"] == 79.0
        assert prices["os_business"] == 149.0


class TestWebstorePlans:
    """GET /api/plans/webstores - Returns Webstore plans WITHOUT founder pricing"""

    def test_returns_3_webstore_plans(self, api_client):
        """Should return exactly 3 Webstore plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/webstores")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_webstore_plan_types(self, api_client):
        """Should return Launch, Growth, Scale plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/webstores")
        data = response.json()
        
        plan_types = {p["plan_type"] for p in data}
        assert plan_types == {"ws_launch", "ws_growth", "ws_scale"}

    def test_no_founder_pricing(self, api_client):
        """Webstore plans should NOT have founder pricing"""
        response = api_client.get(f"{BASE_URL}/api/plans/webstores")
        data = response.json()
        
        for plan in data:
            assert plan["founder_eligible"] is False, f"{plan['plan_type']} should NOT be founder eligible"
            assert plan["founder_price_monthly"] is None, f"{plan['plan_type']} should NOT have founder monthly price"
            assert plan["founder_price_annual"] is None, f"{plan['plan_type']} should NOT have founder annual price"

    def test_webstore_pricing_tiers(self, api_client):
        """Webstore plans should have correct pricing hierarchy"""
        response = api_client.get(f"{BASE_URL}/api/plans/webstores")
        data = response.json()
        
        prices = {p["plan_type"]: p["price_monthly"] for p in data}
        assert prices["ws_launch"] == 39.0
        assert prices["ws_growth"] == 59.0
        assert prices["ws_scale"] == 99.0


class TestAIStudioPlans:
    """GET /api/plans/ai-studio - Returns AI Studio plans WITHOUT founder pricing"""

    def test_returns_3_ai_studio_plans(self, api_client):
        """Should return exactly 3 AI Studio plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai-studio")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_ai_studio_plan_types(self, api_client):
        """Should return Basic, Pro, Max plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai-studio")
        data = response.json()
        
        plan_types = {p["plan_type"] for p in data}
        assert plan_types == {"ai_basic", "ai_pro", "ai_max"}

    def test_no_founder_pricing(self, api_client):
        """AI Studio plans should NOT have founder pricing"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai-studio")
        data = response.json()
        
        for plan in data:
            assert plan["founder_eligible"] is False, f"{plan['plan_type']} should NOT be founder eligible"
            assert plan["founder_price_monthly"] is None
            assert plan["founder_price_annual"] is None

    def test_ai_studio_pricing_tiers(self, api_client):
        """AI Studio plans should have correct pricing hierarchy"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai-studio")
        data = response.json()
        
        prices = {p["plan_type"]: p["price_monthly"] for p in data}
        assert prices["ai_basic"] == 29.0
        assert prices["ai_pro"] == 59.0
        assert prices["ai_max"] == 99.0


class TestFounderStatus:
    """GET /api/plans/founder-status - Returns founder spot availability"""

    def test_returns_founder_status(self, api_client):
        """Should return founder status with all required fields"""
        response = api_client.get(f"{BASE_URL}/api/plans/founder-status")
        assert response.status_code == 200
        data = response.json()
        
        assert "founder_spots_total" in data
        assert "founder_spots_used" in data
        assert "founder_spots_remaining" in data
        assert "founder_available" in data

    def test_founder_spots_total_is_100(self, api_client):
        """Founder spots total should be 100"""
        response = api_client.get(f"{BASE_URL}/api/plans/founder-status")
        data = response.json()
        assert data["founder_spots_total"] == 100

    def test_founder_spots_math(self, api_client):
        """Remaining = Total - Used"""
        response = api_client.get(f"{BASE_URL}/api/plans/founder-status")
        data = response.json()
        
        expected_remaining = data["founder_spots_total"] - data["founder_spots_used"]
        assert data["founder_spots_remaining"] == expected_remaining

    def test_founder_available_flag(self, api_client):
        """founder_available should be true if spots remaining > 0"""
        response = api_client.get(f"{BASE_URL}/api/plans/founder-status")
        data = response.json()
        
        expected_available = data["founder_spots_remaining"] > 0
        assert data["founder_available"] == expected_available


class TestPlanDetails:
    """GET /api/plans/{plan_type}/details - Returns detailed plan info"""

    def test_ws_launch_ui_visibility(self, api_client):
        """ws_launch should have show_jobs_ui=false"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_launch/details")
        assert response.status_code == 200
        data = response.json()
        
        assert data["ui_visibility"]["show_jobs_ui"] is False
        assert data["ui_visibility"]["show_payroll_ui"] is False
        assert data["ui_visibility"]["show_time_clock_ui"] is False
        assert data["ui_visibility"]["show_financials_ui"] is False
        assert data["ui_visibility"]["show_ai_assistant_ui"] is False

    def test_ai_max_ui_visibility(self, api_client):
        """ai_max should have business_data_aware=false but show_ai_assistant_ui=true"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai_max/details")
        assert response.status_code == 200
        data = response.json()
        
        # AI assistant UI should be ON
        assert data["ui_visibility"]["show_ai_assistant_ui"] is True
        
        # But business data access should be OFF
        assert data["features"]["ai_assistant"]["business_data_aware"]["status"] == "off"
        assert data["features"]["ai_assistant"]["business_data_limited"]["status"] == "off"
        
        # Jobs/payroll should be OFF for AI-only plan
        assert data["ui_visibility"]["show_jobs_ui"] is False
        assert data["ui_visibility"]["show_payroll_ui"] is False

    def test_os_business_all_features_on(self, api_client):
        """os_business should have maximum features enabled"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_business/details")
        assert response.status_code == 200
        data = response.json()
        
        # All UI visibility should be ON
        assert data["ui_visibility"]["show_jobs_ui"] is True
        assert data["ui_visibility"]["show_payroll_ui"] is True
        assert data["ui_visibility"]["show_time_clock_ui"] is True
        assert data["ui_visibility"]["show_financials_ui"] is True
        assert data["ui_visibility"]["show_ai_assistant_ui"] is True
        
        # Business data aware should be ON for Business tier
        assert data["features"]["ai_assistant"]["business_data_aware"]["status"] == "on"

    def test_invalid_plan_type_returns_404(self, api_client):
        """Invalid plan type should return 404"""
        response = api_client.get(f"{BASE_URL}/api/plans/invalid_plan/details")
        assert response.status_code == 404

    def test_plan_details_include_features(self, api_client):
        """Plan details should include all feature categories"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_pro/details")
        data = response.json()
        
        assert "features" in data
        assert "core" in data["features"]
        assert "customer_portal" in data["features"]
        assert "webstores" in data["features"]
        assert "ai_tools" in data["features"]
        assert "ai_assistant" in data["features"]
        assert "crm" in data["features"]

    def test_plan_details_include_processing_fees(self, api_client):
        """Plan details should include processing fee info"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_pro/details")
        data = response.json()
        
        assert "processing_fees" in data
        assert "invoice_fee_percent" in data["processing_fees"]
        assert "webstore_fee_percent" in data["processing_fees"]
        assert "stripe_connect_enabled" in data["processing_fees"]


class TestAuthenticatedEndpoints:
    """Authenticated plan endpoints"""

    def test_my_plan_returns_current_plan(self, authenticated_client):
        """GET /api/plans/my-plan should return user's current plan"""
        response = authenticated_client.get(f"{BASE_URL}/api/plans/my-plan")
        assert response.status_code == 200
        data = response.json()
        
        assert "plan_type" in data
        assert "product_line" in data
        assert "display_name" in data
        assert "is_founder" in data
        assert "pricing" in data
        assert "ui_visibility" in data

    def test_my_ui_visibility_returns_flags(self, authenticated_client):
        """GET /api/plans/my-ui-visibility should return UI flags"""
        response = authenticated_client.get(f"{BASE_URL}/api/plans/my-ui-visibility")
        assert response.status_code == 200
        data = response.json()
        
        assert "show_jobs_ui" in data
        assert "show_payroll_ui" in data
        assert "show_time_clock_ui" in data
        assert "show_financials_ui" in data
        assert "show_ai_assistant_ui" in data
        assert "product_line" in data
        assert "plan_type" in data

    def test_check_feature_allowed(self, authenticated_client):
        """POST /api/plans/check-feature should return feature access status"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/plans/check-feature?category=ai_tools&feature=text_generation"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "allowed" in data
        assert "feature" in data
        assert "status" in data
        assert data["feature"] == "ai_tools.text_generation"

    def test_check_feature_not_allowed(self, authenticated_client):
        """Check feature that is OFF for current plan"""
        # For os_starter, advanced features should be off
        response = authenticated_client.post(
            f"{BASE_URL}/api/plans/check-feature?category=ai_tools&feature=branding_kit_generator"
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["allowed"] is False
        assert data["status"] == "off"

    def test_unauthenticated_my_plan_fails(self, api_client):
        """GET /api/plans/my-plan without auth should fail"""
        # Create new session without auth
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/plans/my-plan")
        assert response.status_code == 401


class TestWebstoreUIVisibility:
    """Verify Webstore plans hide shop management UI"""

    def test_ws_launch_hides_jobs_ui(self, api_client):
        """ws_launch should hide jobs UI"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_launch/details")
        data = response.json()
        assert data["ui_visibility"]["show_jobs_ui"] is False

    def test_ws_growth_hides_jobs_ui(self, api_client):
        """ws_growth should hide jobs UI"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_growth/details")
        data = response.json()
        assert data["ui_visibility"]["show_jobs_ui"] is False

    def test_ws_scale_hides_jobs_ui(self, api_client):
        """ws_scale should hide jobs UI"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_scale/details")
        data = response.json()
        assert data["ui_visibility"]["show_jobs_ui"] is False

    def test_webstore_plans_have_webstore_access(self, api_client):
        """All webstore plans should have webstore_access=on"""
        for plan_type in ["ws_launch", "ws_growth", "ws_scale"]:
            response = api_client.get(f"{BASE_URL}/api/plans/{plan_type}/details")
            data = response.json()
            assert data["features"]["webstores"]["webstore_access"]["status"] == "on"


class TestAIStudioUIVisibility:
    """Verify AI Studio plans have correct AI access but no business data"""

    def test_ai_basic_has_ai_access(self, api_client):
        """ai_basic should have AI access but limited"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai_basic/details")
        data = response.json()
        
        assert data["features"]["ai_tools"]["ai_access"]["status"] == "on"
        assert data["features"]["ai_tools"]["text_generation"]["status"] == "on"
        assert data["features"]["ai_tools"]["image_generation"]["status"] == "off"

    def test_ai_pro_has_image_generation(self, api_client):
        """ai_pro should have image generation"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai_pro/details")
        data = response.json()
        
        assert data["features"]["ai_tools"]["image_generation"]["status"] == "on"

    def test_ai_max_no_business_data_aware(self, api_client):
        """ai_max should NOT have business_data_aware"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai_max/details")
        data = response.json()
        
        assert data["features"]["ai_assistant"]["business_data_aware"]["status"] == "off"
        assert data["features"]["ai_assistant"]["business_data_limited"]["status"] == "off"

    def test_ai_studio_plans_no_webstore_access(self, api_client):
        """AI Studio plans should NOT have webstore access"""
        for plan_type in ["ai_basic", "ai_pro", "ai_max"]:
            response = api_client.get(f"{BASE_URL}/api/plans/{plan_type}/details")
            data = response.json()
            assert data["features"]["webstores"]["webstore_access"]["status"] == "off"


class TestProcessingFees:
    """Verify processing fees differ by plan"""

    def test_os_starter_no_webstore_fee(self, api_client):
        """os_starter has no webstore fee (no webstore access)"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_starter/details")
        data = response.json()
        
        assert data["processing_fees"]["webstore_fee_percent"] == 0.0
        assert data["processing_fees"]["stripe_connect_enabled"] is False

    def test_os_pro_has_processing_fees(self, api_client):
        """os_pro has processing fees for webstores"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_pro/details")
        data = response.json()
        
        assert data["processing_fees"]["webstore_fee_percent"] == 3.0
        assert data["processing_fees"]["invoice_fee_percent"] == 1.0
        assert data["processing_fees"]["stripe_connect_enabled"] is True

    def test_os_business_lower_fees(self, api_client):
        """os_business has lower fees than os_pro"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_business/details")
        data = response.json()
        
        assert data["processing_fees"]["webstore_fee_percent"] == 2.0
        assert data["processing_fees"]["invoice_fee_percent"] == 1.0

    def test_ws_launch_webstore_fee(self, api_client):
        """ws_launch has webstore processing fee"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_launch/details")
        data = response.json()
        
        assert data["processing_fees"]["webstore_fee_percent"] == 3.0
        assert data["processing_fees"]["stripe_connect_enabled"] is True

    def test_ai_plans_no_fees(self, api_client):
        """AI Studio plans have no processing fees"""
        for plan_type in ["ai_basic", "ai_pro", "ai_max"]:
            response = api_client.get(f"{BASE_URL}/api/plans/{plan_type}/details")
            data = response.json()
            
            assert data["processing_fees"]["webstore_fee_percent"] == 0.0
            assert data["processing_fees"]["invoice_fee_percent"] == 0.0
            assert data["processing_fees"]["stripe_connect_enabled"] is False
