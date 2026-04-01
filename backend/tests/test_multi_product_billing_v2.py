"""
Multi-Product Billing V2 Tests - Phase 3: Stripe Wiring

Tests for:
- POST /api/billing/checkout/v2 - Creates Stripe checkout for all 9 plans
- GET /api/billing/subscription/v2 - Returns subscription with product_line and plan_type

Validates:
- OS plans (os_starter, os_pro, os_business) with founder pricing
- Webstore plans (ws_launch, ws_growth, ws_scale)
- AI Studio plans (ai_basic, ai_pro, ai_max)
- Annual billing only for os_business
- Founder pricing only for OS plans
- Processing fee validation
- UI visibility flags in subscription response

Test user: test@test.com / password
"""

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# All 9 plan types across 3 product lines
OS_PLANS = ["os_starter", "os_pro", "os_business"]
WS_PLANS = ["ws_launch", "ws_growth", "ws_scale"]
AI_PLANS = ["ai_basic", "ai_pro", "ai_max"]
ALL_PLANS = OS_PLANS + WS_PLANS + AI_PLANS


@pytest.fixture(scope="module")
def api_client():
    """Create shared HTTP session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for test@test.com"""
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": FALLBACK_TEST_EMAIL, "password": FALLBACK_TEST_PASSWORD},
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    
    # Fallback to billing_test user
    response = api_client.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "billing_test@example.com", "password": COMMON_TEST_PASSWORD},
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    
    pytest.skip("Authentication failed - no valid test user")


@pytest.fixture(scope="module")
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


# ============================================================================
# CHECKOUT V2 - OS PLANS
# ============================================================================

class TestCheckoutV2OSPlans:
    """POST /api/billing/checkout/v2 - OS Plans (os_starter, os_pro, os_business)"""

    def test_os_starter_checkout(self, authenticated_client):
        """OS Starter checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_starter",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "url" in data, "Missing checkout URL"
        assert data["url"].startswith("https://checkout.stripe.com")
        assert data["plan_type"] == "os_starter"
        assert data["product_line"] == "os"
        assert "session_id" in data

    def test_os_pro_checkout(self, authenticated_client):
        """OS Pro checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_pro",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["url"].startswith("https://checkout.stripe.com")
        assert data["plan_type"] == "os_pro"
        assert data["product_line"] == "os"

    def test_os_business_checkout_monthly(self, authenticated_client):
        """OS Business monthly checkout should work"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_business",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["plan_type"] == "os_business"
        assert data["product_line"] == "os"

    def test_os_business_annual_checkout(self, authenticated_client):
        """OS Business annual checkout should work - ONLY plan with annual billing"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_business",
                "billing_interval": "annual",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["url"].startswith("https://checkout.stripe.com")
        assert data["plan_type"] == "os_business"

    def test_os_starter_founder_pricing(self, authenticated_client):
        """OS Starter with founder pricing should work"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_starter",
                "billing_interval": "monthly",
                "use_founder_pricing": True,
                "origin_url": "https://example.com"
            }
        )
        # Should either work (200) or fail with no spots left (400)
        assert response.status_code in [200, 400], f"Unexpected: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data["is_founder"] is True


# ============================================================================
# CHECKOUT V2 - WEBSTORE PLANS
# ============================================================================

class TestCheckoutV2WebstorePlans:
    """POST /api/billing/checkout/v2 - Webstore Plans (ws_launch, ws_growth, ws_scale)"""

    def test_ws_launch_checkout(self, authenticated_client):
        """WS Launch checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "ws_launch",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["url"].startswith("https://checkout.stripe.com")
        assert data["plan_type"] == "ws_launch"
        assert data["product_line"] == "webstores"

    def test_ws_growth_checkout(self, authenticated_client):
        """WS Growth checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "ws_growth",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["plan_type"] == "ws_growth"
        assert data["product_line"] == "webstores"

    def test_ws_scale_checkout(self, authenticated_client):
        """WS Scale checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "ws_scale",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["plan_type"] == "ws_scale"
        assert data["product_line"] == "webstores"


# ============================================================================
# CHECKOUT V2 - AI STUDIO PLANS
# ============================================================================

class TestCheckoutV2AIStudioPlans:
    """POST /api/billing/checkout/v2 - AI Studio Plans (ai_basic, ai_pro, ai_max)"""

    def test_ai_basic_checkout(self, authenticated_client):
        """AI Basic checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "ai_basic",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["url"].startswith("https://checkout.stripe.com")
        assert data["plan_type"] == "ai_basic"
        assert data["product_line"] == "ai_studio"

    def test_ai_pro_checkout(self, authenticated_client):
        """AI Pro checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "ai_pro",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["plan_type"] == "ai_pro"
        assert data["product_line"] == "ai_studio"

    def test_ai_max_checkout(self, authenticated_client):
        """AI Max checkout should return Stripe URL"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "ai_max",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert data["plan_type"] == "ai_max"
        assert data["product_line"] == "ai_studio"


# ============================================================================
# CHECKOUT V2 - VALIDATION
# ============================================================================

class TestCheckoutV2Validation:
    """Validation rules for checkout/v2"""

    def test_annual_only_for_os_business(self, authenticated_client):
        """Annual billing should ONLY work for os_business"""
        # Test with os_starter - should fail
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_starter",
                "billing_interval": "annual",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400, "Should reject annual for os_starter"
        data = response.json()
        assert "annual" in data.get("detail", "").lower() or "business" in data.get("detail", "").lower()

    def test_annual_rejected_for_webstore_plans(self, authenticated_client):
        """Annual billing should be rejected for webstore plans"""
        for plan in ["ws_launch", "ws_growth", "ws_scale"]:
            response = authenticated_client.post(
                f"{BASE_URL}/api/billing/checkout/v2",
                json={
                    "plan_type": plan,
                    "billing_interval": "annual",
                    "use_founder_pricing": False,
                    "origin_url": "https://example.com"
                }
            )
            assert response.status_code == 400, f"Should reject annual for {plan}"

    def test_annual_rejected_for_ai_plans(self, authenticated_client):
        """Annual billing should be rejected for AI Studio plans"""
        for plan in ["ai_basic", "ai_pro", "ai_max"]:
            response = authenticated_client.post(
                f"{BASE_URL}/api/billing/checkout/v2",
                json={
                    "plan_type": plan,
                    "billing_interval": "annual",
                    "use_founder_pricing": False,
                    "origin_url": "https://example.com"
                }
            )
            assert response.status_code == 400, f"Should reject annual for {plan}"

    def test_founder_pricing_only_for_os_plans(self, authenticated_client):
        """Founder pricing should ONLY work for OS plans"""
        # Test with ws_launch - should fail
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "ws_launch",
                "billing_interval": "monthly",
                "use_founder_pricing": True,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400, "Should reject founder pricing for ws_launch"
        data = response.json()
        assert "founder" in data.get("detail", "").lower() or "os" in data.get("detail", "").lower()

    def test_founder_pricing_rejected_for_ai_plans(self, authenticated_client):
        """Founder pricing should be rejected for AI Studio plans"""
        for plan in ["ai_basic", "ai_pro", "ai_max"]:
            response = authenticated_client.post(
                f"{BASE_URL}/api/billing/checkout/v2",
                json={
                    "plan_type": plan,
                    "billing_interval": "monthly",
                    "use_founder_pricing": True,
                    "origin_url": "https://example.com"
                }
            )
            assert response.status_code == 400, f"Should reject founder pricing for {plan}"

    def test_invalid_plan_type_rejected(self, authenticated_client):
        """Invalid plan type should return 400"""
        response = authenticated_client.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "invalid_plan",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400

    def test_unauthenticated_checkout_fails(self, api_client):
        """Checkout without auth should return 401"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_starter",
                "billing_interval": "monthly",
                "use_founder_pricing": False,
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code in [401, 403]


# ============================================================================
# SUBSCRIPTION V2 - RESPONSE STRUCTURE
# ============================================================================

class TestSubscriptionV2:
    """GET /api/billing/subscription/v2 - Returns current plan info"""

    def test_subscription_v2_response_structure(self, authenticated_client):
        """Should return all required fields"""
        response = authenticated_client.get(f"{BASE_URL}/api/billing/subscription/v2")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Plan identification
        assert "plan_type" in data
        assert "plan_display_name" in data
        assert "product_line" in data
        assert "product_line_display" in data
        
        # Status
        assert "status" in data
        assert "is_founder" in data
        
        # Billing info
        assert "billing_interval" in data

    def test_subscription_v2_pricing_info(self, authenticated_client):
        """Should return pricing information"""
        response = authenticated_client.get(f"{BASE_URL}/api/billing/subscription/v2")
        data = response.json()
        
        assert "pricing" in data
        pricing = data["pricing"]
        assert "monthly" in pricing
        assert "annual" in pricing
        assert "founder_monthly" in pricing
        assert "founder_annual" in pricing

    def test_subscription_v2_processing_fees(self, authenticated_client):
        """Should return processing fee information"""
        response = authenticated_client.get(f"{BASE_URL}/api/billing/subscription/v2")
        data = response.json()
        
        assert "processing_fees" in data
        fees = data["processing_fees"]
        assert "invoice" in fees
        assert "webstore" in fees
        assert "stripe_connect_enabled" in fees
        assert "online_payments_enabled" in fees

    def test_subscription_v2_ui_visibility(self, authenticated_client):
        """Should return UI visibility flags"""
        response = authenticated_client.get(f"{BASE_URL}/api/billing/subscription/v2")
        data = response.json()
        
        assert "ui_visibility" in data
        ui = data["ui_visibility"]
        
        # Check for key UI visibility fields
        assert "show_jobs_ui" in ui or "product_line" in ui

    def test_subscription_v2_upgrade_options(self, authenticated_client):
        """Should return upgrade options based on current plan"""
        response = authenticated_client.get(f"{BASE_URL}/api/billing/subscription/v2")
        data = response.json()
        
        assert "upgrade_options" in data
        assert isinstance(data["upgrade_options"], list)

    def test_subscription_v2_unauthenticated_fails(self, api_client):
        """Subscription without auth should return 401"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/billing/subscription/v2")
        assert response.status_code in [401, 403]


# ============================================================================
# PLANS API - ALL 9 PLANS
# ============================================================================

class TestPlansAPIAll:
    """GET /api/plans/all - Returns all 9 plans grouped by product line"""

    def test_plans_all_returns_9_plans(self, api_client):
        """Should return 9 total plans across 3 product lines"""
        response = api_client.get(f"{BASE_URL}/api/plans/all")
        assert response.status_code == 200
        data = response.json()
        
        total_plans = sum(len(pl["plans"]) for pl in data)
        assert total_plans == 9, f"Expected 9 plans, got {total_plans}"

    def test_plans_os_correct_pricing(self, api_client):
        """OS plans should have correct pricing"""
        response = api_client.get(f"{BASE_URL}/api/plans/os")
        assert response.status_code == 200
        data = response.json()
        
        prices = {p["plan_type"]: p["price_monthly"] for p in data}
        assert prices["os_starter"] == 39.0
        assert prices["os_pro"] == 79.0
        assert prices["os_business"] == 149.0

    def test_plans_webstores(self, api_client):
        """Webstores endpoint should return 3 plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/webstores")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        plan_types = {p["plan_type"] for p in data}
        assert plan_types == {"ws_launch", "ws_growth", "ws_scale"}

    def test_plans_ai_studio(self, api_client):
        """AI Studio endpoint should return 3 plans"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai-studio")
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3
        plan_types = {p["plan_type"] for p in data}
        assert plan_types == {"ai_basic", "ai_pro", "ai_max"}


# ============================================================================
# PLANS API - FOUNDER STATUS
# ============================================================================

class TestFounderStatusAPI:
    """GET /api/plans/founder-status - Returns founder availability"""

    def test_founder_status_response(self, api_client):
        """Should return founder spot availability info"""
        response = api_client.get(f"{BASE_URL}/api/plans/founder-status")
        assert response.status_code == 200
        data = response.json()
        
        assert "founder_spots_total" in data
        assert "founder_spots_used" in data
        assert "founder_spots_remaining" in data
        assert "founder_available" in data
        
        # Total should be 100
        assert data["founder_spots_total"] == 100
        
        # Math check
        assert data["founder_spots_remaining"] == data["founder_spots_total"] - data["founder_spots_used"]


# ============================================================================
# PLANS API - PLAN DETAILS
# ============================================================================

class TestPlanDetailsAPI:
    """GET /api/plans/{plan_type}/details - Returns detailed plan config"""

    def test_os_starter_details(self, api_client):
        """OS Starter details should include all config"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_starter/details")
        assert response.status_code == 200
        data = response.json()
        
        assert data["plan_type"] == "os_starter"
        assert data["product_line"] == "os"
        assert "pricing" in data
        assert "processing_fees" in data
        assert "features" in data
        assert "ui_visibility" in data

    def test_ws_launch_details(self, api_client):
        """WS Launch details should show no jobs UI"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_launch/details")
        assert response.status_code == 200
        data = response.json()
        
        assert data["ui_visibility"]["show_jobs_ui"] is False
        assert data["processing_fees"]["webstore_fee_percent"] == 3.0

    def test_ai_max_details(self, api_client):
        """AI Max details should show AI features but no business data access"""
        response = api_client.get(f"{BASE_URL}/api/plans/ai_max/details")
        assert response.status_code == 200
        data = response.json()
        
        # AI Max should have unlimited AI
        assert data["features"]["ai_tools"]["monthly_generations"]["status"] == "on"
        # But no business data awareness
        assert data["features"]["ai_assistant"]["business_data_aware"]["status"] == "off"


# ============================================================================
# PROCESSING FEES - BY PLAN
# ============================================================================

class TestProcessingFeesCalculation:
    """Verify processing fees are correct per plan and transaction type"""

    def test_os_starter_no_fees(self, api_client):
        """OS Starter: 0% invoice, 0% webstore"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_starter/details")
        data = response.json()
        
        assert data["processing_fees"]["invoice_fee_percent"] == 0.0
        assert data["processing_fees"]["webstore_fee_percent"] == 0.0

    def test_os_pro_fees(self, api_client):
        """OS Pro: 1% invoice, 3% webstore"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_pro/details")
        data = response.json()
        
        assert data["processing_fees"]["invoice_fee_percent"] == 1.0
        assert data["processing_fees"]["webstore_fee_percent"] == 3.0

    def test_os_business_fees(self, api_client):
        """OS Business: 1% invoice, 2% webstore"""
        response = api_client.get(f"{BASE_URL}/api/plans/os_business/details")
        data = response.json()
        
        assert data["processing_fees"]["invoice_fee_percent"] == 1.0
        assert data["processing_fees"]["webstore_fee_percent"] == 2.0

    def test_ws_launch_fees(self, api_client):
        """WS Launch: 0% invoice, 3% webstore"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_launch/details")
        data = response.json()
        
        assert data["processing_fees"]["invoice_fee_percent"] == 0.0
        assert data["processing_fees"]["webstore_fee_percent"] == 3.0

    def test_ws_growth_fees(self, api_client):
        """WS Growth: 0% invoice, 2.5% webstore"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_growth/details")
        data = response.json()
        
        assert data["processing_fees"]["invoice_fee_percent"] == 0.0
        assert data["processing_fees"]["webstore_fee_percent"] == 2.5

    def test_ws_scale_fees(self, api_client):
        """WS Scale: 0% invoice, 2% webstore"""
        response = api_client.get(f"{BASE_URL}/api/plans/ws_scale/details")
        data = response.json()
        
        assert data["processing_fees"]["invoice_fee_percent"] == 0.0
        assert data["processing_fees"]["webstore_fee_percent"] == 2.0

    def test_ai_plans_no_fees(self, api_client):
        """AI plans have no processing fees"""
        for plan in ["ai_basic", "ai_pro", "ai_max"]:
            response = api_client.get(f"{BASE_URL}/api/plans/{plan}/details")
            data = response.json()
            
            assert data["processing_fees"]["invoice_fee_percent"] == 0.0
            assert data["processing_fees"]["webstore_fee_percent"] == 0.0
