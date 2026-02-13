"""
Tier System API Tests

Tests for the 3-tier subscription system (Starter/Pro/Business) with feature gating.
Tests cover:
- GET /api/tiers/plans - List all subscription plans (public)
- GET /api/tiers/my-plan - Get current tenant's tier and features (requires auth)
- GET /api/tiers/check/{category}/{feature} - Check feature access
- POST /api/tiers/use/{category}/{feature} - Use a limited feature (increments usage)
- GET /api/tiers/usage - Get all usage for limited features
- GET /api/tiers/upgrade-prompt/{category}/{feature} - Get upgrade prompt for blocked feature
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "tiertest@signguy.com"
TEST_PASSWORD = "Test123!"


class TestTierPlansPublic:
    """Test public tier plans endpoint - no auth required"""
    
    def test_get_plans_returns_all_tiers(self):
        """GET /api/tiers/plans should return all 3 subscription plans"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        
        plans = data["plans"]
        assert len(plans) == 3, f"Expected 3 plans, got {len(plans)}"
        
        # Verify plan IDs
        plan_ids = [p["id"] for p in plans]
        assert "starter" in plan_ids, "Should have starter plan"
        assert "pro" in plan_ids, "Should have pro plan"
        assert "business" in plan_ids, "Should have business plan"
    
    def test_starter_plan_details(self):
        """Verify Starter plan has correct pricing and highlights"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        assert response.status_code == 200
        
        data = response.json()
        starter = next((p for p in data["plans"] if p["id"] == "starter"), None)
        
        assert starter is not None, "Starter plan should exist"
        assert starter["name"] == "Starter", f"Expected 'Starter', got {starter['name']}"
        assert starter["price_monthly"] == 0, f"Starter should be free, got {starter['price_monthly']}"
        assert starter["price_yearly"] == 0, f"Starter yearly should be free"
        assert "highlights" in starter, "Should have highlights"
        assert len(starter["highlights"]) > 0, "Should have at least one highlight"
    
    def test_pro_plan_details(self):
        """Verify Pro plan has correct pricing"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        assert response.status_code == 200
        
        data = response.json()
        pro = next((p for p in data["plans"] if p["id"] == "pro"), None)
        
        assert pro is not None, "Pro plan should exist"
        assert pro["name"] == "Pro"
        assert pro["price_monthly"] == 49, f"Pro monthly should be $49, got {pro['price_monthly']}"
        assert pro["price_yearly"] == 490, f"Pro yearly should be $490, got {pro['price_yearly']}"
    
    def test_business_plan_details(self):
        """Verify Business plan has correct pricing"""
        response = requests.get(f"{BASE_URL}/api/tiers/plans")
        assert response.status_code == 200
        
        data = response.json()
        business = next((p for p in data["plans"] if p["id"] == "business"), None)
        
        assert business is not None, "Business plan should exist"
        assert business["name"] == "Business"
        assert business["price_monthly"] == 149, f"Business monthly should be $149, got {business['price_monthly']}"
        assert business["price_yearly"] == 1490, f"Business yearly should be $1490, got {business['price_yearly']}"


class TestTierAuthentication:
    """Test that authenticated endpoints require valid token"""
    
    def test_my_plan_requires_auth(self):
        """GET /api/tiers/my-plan should require authentication"""
        response = requests.get(f"{BASE_URL}/api/tiers/my-plan")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_check_feature_requires_auth(self):
        """GET /api/tiers/check/{category}/{feature} should require authentication"""
        response = requests.get(f"{BASE_URL}/api/tiers/check/ai_tools/text_tools")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_use_feature_requires_auth(self):
        """POST /api/tiers/use/{category}/{feature} should require authentication"""
        response = requests.post(f"{BASE_URL}/api/tiers/use/ai_tools/monthly_generations")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_usage_requires_auth(self):
        """GET /api/tiers/usage should require authentication"""
        response = requests.get(f"{BASE_URL}/api/tiers/usage")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
    
    def test_upgrade_prompt_requires_auth(self):
        """GET /api/tiers/upgrade-prompt/{category}/{feature} should require authentication"""
        response = requests.get(f"{BASE_URL}/api/tiers/upgrade-prompt/ai_tools/image_generation")
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"


@pytest.fixture(scope="class")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Could not authenticate test user: {response.text}")
    
    return response.json()["access_token"]


@pytest.fixture(scope="class")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestMyPlan:
    """Test GET /api/tiers/my-plan endpoint"""
    
    def test_get_my_plan_success(self, auth_headers):
        """Should return current tenant's tier and features"""
        response = requests.get(f"{BASE_URL}/api/tiers/my-plan", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "tier" in data, "Response should contain 'tier'"
        assert "tier_display_name" in data, "Response should contain 'tier_display_name'"
        assert "features" in data, "Response should contain 'features'"
        
        # Verify tier is valid
        assert data["tier"] in ["starter", "pro", "business"], f"Invalid tier: {data['tier']}"
    
    def test_my_plan_has_feature_categories(self, auth_headers):
        """Should return all feature categories"""
        response = requests.get(f"{BASE_URL}/api/tiers/my-plan", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        features = data["features"]
        
        # Check key categories exist
        expected_categories = [
            "customer_portal", "webstores", "ai_tools", "team", 
            "core_modules", "analytics", "pricing"
        ]
        
        for category in expected_categories:
            assert category in features, f"Missing category: {category}"


class TestFeatureCheckON:
    """Test feature check for ON status features (allowed=true)"""
    
    def test_check_on_feature_ai_text_tools(self, auth_headers):
        """ai_tools.text_tools should be ON for starter tier"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/ai_tools/text_tools",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["allowed"] == True, f"text_tools should be allowed, got {data}"
        assert data["status"] == "on", f"Status should be 'on', got {data['status']}"
        assert data["feature"] == "ai_tools.text_tools"
    
    def test_check_on_feature_customer_portal(self, auth_headers):
        """customer_portal.portal_access should be ON"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/customer_portal/portal_access",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] == True
        assert data["status"] == "on"
    
    def test_check_on_feature_core_modules_jobs(self, auth_headers):
        """core_modules.jobs should be ON for all tiers"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/core_modules/jobs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] == True
        assert data["status"] == "on"


class TestFeatureCheckOFF:
    """Test feature check for OFF status features (allowed=false with upgrade message)"""
    
    def test_check_off_feature_image_generation(self, auth_headers):
        """ai_tools.image_generation should be OFF for starter tier"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/ai_tools/image_generation",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["allowed"] == False, f"image_generation should NOT be allowed for starter, got {data}"
        assert data["status"] == "off", f"Status should be 'off', got {data['status']}"
        assert "message" in data, "Should have upgrade message"
        assert "upgrade" in data["message"].lower(), f"Message should mention upgrade: {data['message']}"
    
    def test_check_off_feature_kanban(self, auth_headers):
        """core_modules.kanban should be OFF for starter tier"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/core_modules/kanban",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] == False
        assert data["status"] == "off"
    
    def test_check_off_feature_time_clock(self, auth_headers):
        """core_modules.time_clock should be OFF for starter tier"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/core_modules/time_clock",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] == False
        assert data["status"] == "off"


class TestFeatureCheckLIMITED:
    """Test feature check for LIMITED status features (tracks usage and shows remaining)"""
    
    def test_check_limited_feature_monthly_generations(self, auth_headers):
        """ai_tools.monthly_generations should be LIMITED with limit=25 for starter"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/ai_tools/monthly_generations",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["allowed"] == True, f"Should be allowed if under limit, got {data}"
        assert data["status"] == "limited", f"Status should be 'limited', got {data['status']}"
        assert "limit" in data, "Should have limit field"
        assert data["limit"] == 25, f"Starter limit should be 25, got {data['limit']}"
        assert "current_usage" in data, "Should have current_usage field"
        assert "remaining" in data, "Should have remaining field"
    
    def test_check_limited_feature_num_stores(self, auth_headers):
        """webstores.num_stores should be LIMITED with limit=1 for starter"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/webstores/num_stores",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "limited"
        assert data["limit"] == 1, f"Starter should have 1 store limit, got {data['limit']}"
    
    def test_check_limited_feature_team_members(self, auth_headers):
        """team.team_members should be LIMITED with limit=1 for starter"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/team/team_members",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "limited"
        assert data["limit"] == 1


class TestUseFeature:
    """Test POST /api/tiers/use/{category}/{feature} - usage increment"""
    
    def test_use_limited_feature_increments_usage(self, auth_headers):
        """Using a limited feature should increment the usage counter"""
        # First check current usage
        check_response = requests.get(
            f"{BASE_URL}/api/tiers/check/ai_tools/monthly_generations",
            headers=auth_headers
        )
        assert check_response.status_code == 200
        initial_usage = check_response.json().get("current_usage", 0)
        
        # Use the feature
        use_response = requests.post(
            f"{BASE_URL}/api/tiers/use/ai_tools/monthly_generations",
            headers=auth_headers
        )
        
        assert use_response.status_code == 200, f"Expected 200, got {use_response.status_code}: {use_response.text}"
        
        data = use_response.json()
        assert data["success"] == True, f"Should succeed, got {data}"
        assert "remaining" in data, "Should return remaining count"
        assert "limit" in data, "Should return limit"
        
        # Verify usage incremented
        verify_response = requests.get(
            f"{BASE_URL}/api/tiers/check/ai_tools/monthly_generations",
            headers=auth_headers
        )
        assert verify_response.status_code == 200
        new_usage = verify_response.json()["current_usage"]
        assert new_usage == initial_usage + 1, f"Usage should increment from {initial_usage} to {initial_usage + 1}, got {new_usage}"
    
    def test_use_on_feature_succeeds(self, auth_headers):
        """Using an ON feature should succeed (no usage tracking)"""
        response = requests.post(
            f"{BASE_URL}/api/tiers/use/ai_tools/text_tools",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] == True
    
    def test_use_off_feature_fails(self, auth_headers):
        """Using an OFF feature should return 403"""
        response = requests.post(
            f"{BASE_URL}/api/tiers/use/ai_tools/image_generation",
            headers=auth_headers
        )
        
        assert response.status_code == 403, f"Expected 403 for OFF feature, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "detail" in data, "Should have error detail"
        detail = data["detail"]
        assert detail.get("error") == "feature_limit_reached" or "not available" in str(detail.get("message", "")).lower()


class TestUsageTracking:
    """Test GET /api/tiers/usage endpoint"""
    
    def test_get_usage_returns_list(self, auth_headers):
        """Should return usage data for all limited features"""
        response = requests.get(f"{BASE_URL}/api/tiers/usage", headers=auth_headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "usage" in data, "Response should contain 'usage' key"
        assert isinstance(data["usage"], list), "Usage should be a list"
    
    def test_usage_record_structure(self, auth_headers):
        """Each usage record should have required fields"""
        # First use a feature to ensure there's usage data
        requests.post(
            f"{BASE_URL}/api/tiers/use/ai_tools/monthly_generations",
            headers=auth_headers
        )
        
        response = requests.get(f"{BASE_URL}/api/tiers/usage", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        if len(data["usage"]) > 0:
            record = data["usage"][0]
            assert "feature" in record, "Should have feature name"
            assert "current" in record, "Should have current usage"
            assert "limit" in record, "Should have limit"
            assert "remaining" in record, "Should have remaining"
            assert "percentage" in record, "Should have percentage"


class TestUpgradePrompt:
    """Test GET /api/tiers/upgrade-prompt/{category}/{feature} endpoint"""
    
    def test_upgrade_prompt_for_off_feature(self, auth_headers):
        """Should return upgrade info for blocked feature"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/upgrade-prompt/ai_tools/image_generation",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "current_tier" in data, "Should have current_tier"
        assert "unlock_tier" in data, "Should have unlock_tier"
        assert "unlock_tier_name" in data, "Should have unlock_tier_name"
        assert "unlock_price_monthly" in data, "Should have unlock_price_monthly"
        assert "message" in data, "Should have upgrade message"
        assert "cta_text" in data, "Should have CTA text"
    
    def test_upgrade_prompt_shows_correct_tier(self, auth_headers):
        """Should show Pro tier for image_generation (unlocked at Pro)"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/upgrade-prompt/ai_tools/image_generation",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # image_generation is unlocked at Pro tier
        assert data["unlock_tier"] == "pro", f"image_generation unlocks at Pro, got {data['unlock_tier']}"
        assert data["unlock_price_monthly"] == 49, f"Pro is $49/month, got {data['unlock_price_monthly']}"
    
    def test_upgrade_prompt_for_business_only_feature(self, auth_headers):
        """Should show Business tier for B2B features"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/upgrade-prompt/b2b/b2b_access",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # b2b_access is only available at Business tier
        assert data["unlock_tier"] == "business", f"b2b_access unlocks at Business, got {data['unlock_tier']}"
        assert data["unlock_price_monthly"] == 149


class TestInvalidFeatures:
    """Test handling of invalid category/feature combinations"""
    
    def test_check_invalid_category(self, auth_headers):
        """Should handle invalid category gracefully"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/invalid_category/some_feature",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        # Invalid category should return OFF status
        assert data["allowed"] == False
        assert data["status"] == "off"
    
    def test_check_invalid_feature(self, auth_headers):
        """Should handle invalid feature gracefully"""
        response = requests.get(
            f"{BASE_URL}/api/tiers/check/ai_tools/invalid_feature",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["allowed"] == False
        assert data["status"] == "off"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
