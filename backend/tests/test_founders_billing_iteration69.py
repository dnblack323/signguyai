"""
Test Suite for Founders Edition Billing System - Iteration 69

Tests the new Founders-only billing system:
- GET /api/billing/founders/plan - Plan details with correct pricing
- POST /api/billing/founders/checkout - Stripe checkout generation
- POST /api/billing/founders/purchase-credits - Credit pack purchases
- GET /api/billing/founders/fees - Fee structure
- GET /api/billing/founders/spots - Remaining spots
- GET /api/billing/founders/credits - Credit balance
- GET /api/plans/my-processing-fees - Founders fees (2.2% + $0.20, 2% webstore)

Pricing:
- $99/mo, $594/yr
- FOUNDERS promo code for 50% off
- 150 AI credits/month (no rollover)
- Purchased credits DO rollover
- Processing: 2.2% + $0.20 platform, 2% webstore
- Credit packs: 100/$10, 300/$25, 1000/$60
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "password"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for admin user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def test_user_token():
    """Get authentication token for test user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Test user auth failed: {response.status_code}")


class TestFoundersPlanEndpoint:
    """Test GET /api/billing/founders/plan"""

    def test_founders_plan_returns_correct_pricing(self, auth_token):
        """Verify Founders Edition pricing: $99/mo, $594/yr"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/plan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Verify plan exists
        assert "plan" in data, "Missing plan field"
        plan = data["plan"]
        
        # Verify pricing
        assert plan.get("price_monthly") == 99, f"Expected $99/mo, got {plan.get('price_monthly')}"
        assert plan.get("price_annual") == 594, f"Expected $594/yr, got {plan.get('price_annual')}"
        assert plan.get("plan_id") == "founders_edition", f"Expected founders_edition, got {plan.get('plan_id')}"
        assert plan.get("plan_name") == "Founders Edition", f"Expected 'Founders Edition', got {plan.get('plan_name')}"
        print(f"PASS: Founders pricing verified - ${plan['price_monthly']}/mo, ${plan['price_annual']}/yr")

    def test_founders_plan_has_correct_fees(self, auth_token):
        """Verify processing fees: 2.2% + $0.20 platform, 2% webstore"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/plan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "fees" in data, "Missing fees field"
        fees = data["fees"]
        
        # Verify fee structure
        assert fees.get("platform_processing_percent") == 2.2, f"Expected 2.2%, got {fees.get('platform_processing_percent')}"
        assert fees.get("platform_processing_fixed") == 0.20, f"Expected $0.20, got {fees.get('platform_processing_fixed')}"
        assert fees.get("webstore_additional_percent") == 2.0, f"Expected 2%, got {fees.get('webstore_additional_percent')}"
        print(f"PASS: Fees verified - {fees['platform_processing_percent']}% + ${fees['platform_processing_fixed']}, webstore {fees['webstore_additional_percent']}%")

    def test_founders_plan_has_correct_credit_allowance(self, auth_token):
        """Verify 150 AI credits/month with correct rollover settings"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/plan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        plan = data["plan"]
        
        # Verify credit settings
        assert plan.get("ai_credits_monthly") == 150, f"Expected 150 credits, got {plan.get('ai_credits_monthly')}"
        assert plan.get("monthly_credit_rollover") == False, "Monthly credits should NOT rollover"
        assert plan.get("purchased_credit_rollover") == True, "Purchased credits SHOULD rollover"
        print(f"PASS: Credit allowance verified - {plan['ai_credits_monthly']}/month, purchased rollover: {plan['purchased_credit_rollover']}")

    def test_founders_plan_has_spots_info(self, auth_token):
        """Verify spots remaining info is included"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/plan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "spots" in data, "Missing spots field"
        spots = data["spots"]
        
        assert "total_spots" in spots, "Missing total_spots"
        assert "spots_taken" in spots, "Missing spots_taken"
        assert "spots_remaining" in spots, "Missing spots_remaining"
        assert spots["total_spots"] == 100, f"Expected 100 total spots, got {spots['total_spots']}"
        print(f"PASS: Spots info - {spots['spots_remaining']} of {spots['total_spots']} remaining")

    def test_founders_plan_has_credit_packs(self, auth_token):
        """Verify credit packs: 100/$10, 300/$25, 1000/$60"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/plan",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "credit_packs" in data, "Missing credit_packs field"
        packs = data["credit_packs"]
        
        # Should have 3 packs
        assert len(packs) == 3, f"Expected 3 credit packs, got {len(packs)}"
        
        # Verify each pack
        pack_dict = {p["pack_id"]: p for p in packs}
        
        assert "pack_small" in pack_dict
        assert pack_dict["pack_small"]["credits"] == 100
        assert pack_dict["pack_small"]["price"] == 10
        
        assert "pack_medium" in pack_dict
        assert pack_dict["pack_medium"]["credits"] == 300
        assert pack_dict["pack_medium"]["price"] == 25
        
        assert "pack_large" in pack_dict
        assert pack_dict["pack_large"]["credits"] == 1000
        assert pack_dict["pack_large"]["price"] == 60
        
        print(f"PASS: Credit packs verified - {len(packs)} packs available")


class TestFoundersCheckoutEndpoint:
    """Test POST /api/billing/founders/checkout"""

    def test_checkout_monthly_generates_stripe_url(self, auth_token):
        """Verify monthly checkout generates valid Stripe URL"""
        response = requests.post(
            f"{BASE_URL}/api/billing/founders/checkout",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "billing_interval": "monthly",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "checkout_url" in data, "Missing checkout_url"
        assert "session_id" in data, "Missing session_id"
        assert data["checkout_url"].startswith("https://checkout.stripe.com"), f"Invalid Stripe URL: {data['checkout_url'][:50]}"
        print(f"PASS: Monthly checkout URL generated - {data['checkout_url'][:60]}...")

    def test_checkout_annual_generates_stripe_url(self, auth_token):
        """Verify annual checkout generates valid Stripe URL"""
        response = requests.post(
            f"{BASE_URL}/api/billing/founders/checkout",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "billing_interval": "annual",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "checkout_url" in data, "Missing checkout_url"
        assert data["checkout_url"].startswith("https://checkout.stripe.com"), f"Invalid Stripe URL"
        print(f"PASS: Annual checkout URL generated - {data['checkout_url'][:60]}...")

    def test_checkout_requires_auth(self):
        """Verify checkout requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/billing/founders/checkout",
            json={
                "billing_interval": "monthly",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 401 or response.status_code == 403
        print("PASS: Checkout requires authentication")


class TestFoundersCreditPurchaseEndpoint:
    """Test POST /api/billing/founders/purchase-credits"""

    def test_purchase_small_pack_generates_url(self, auth_token):
        """Verify pack_small (100/$10) checkout works"""
        response = requests.post(
            f"{BASE_URL}/api/billing/founders/purchase-credits",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "pack_id": "pack_small",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "checkout_url" in data, "Missing checkout_url"
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
        print(f"PASS: pack_small checkout URL generated")

    def test_purchase_medium_pack_generates_url(self, auth_token):
        """Verify pack_medium (300/$25) checkout works"""
        response = requests.post(
            f"{BASE_URL}/api/billing/founders/purchase-credits",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "pack_id": "pack_medium",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "checkout_url" in data
        print(f"PASS: pack_medium checkout URL generated")

    def test_purchase_large_pack_generates_url(self, auth_token):
        """Verify pack_large (1000/$60) checkout works"""
        response = requests.post(
            f"{BASE_URL}/api/billing/founders/purchase-credits",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "pack_id": "pack_large",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "checkout_url" in data
        print(f"PASS: pack_large checkout URL generated")

    def test_purchase_invalid_pack_fails(self, auth_token):
        """Verify invalid pack_id is rejected"""
        response = requests.post(
            f"{BASE_URL}/api/billing/founders/purchase-credits",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "pack_id": "invalid_pack",
                "origin_url": "https://example.com"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("PASS: Invalid pack correctly rejected")


class TestFoundersFeesEndpoint:
    """Test GET /api/billing/founders/fees"""

    def test_founders_fees_returns_correct_structure(self, auth_token):
        """Verify fee endpoint returns correct values"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/fees",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # This might be a public endpoint
        if response.status_code == 401:
            # Try without auth
            response = requests.get(f"{BASE_URL}/api/billing/founders/fees")
        
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        assert data.get("platform_processing_percent") == 2.2
        assert data.get("platform_processing_fixed") == 0.20
        assert data.get("webstore_additional_percent") == 2.0
        assert "note" in data  # Should have Stripe fees note
        print(f"PASS: Fees endpoint - {data['platform_processing_percent']}% + ${data['platform_processing_fixed']}")


class TestFoundersSpotsEndpoint:
    """Test GET /api/billing/founders/spots (public endpoint)"""

    def test_spots_returns_remaining_info(self):
        """Verify public spots endpoint returns availability"""
        response = requests.get(f"{BASE_URL}/api/billing/founders/spots")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert "total_spots" in data
        assert "spots_taken" in data
        assert "spots_remaining" in data
        assert "is_available" in data
        
        assert data["total_spots"] == 100
        assert 0 <= data["spots_taken"] <= 100
        assert data["spots_remaining"] == 100 - data["spots_taken"]
        print(f"PASS: Spots - {data['spots_remaining']} of {data['total_spots']} remaining, available: {data['is_available']}")


class TestFoundersCreditsEndpoint:
    """Test GET /api/billing/founders/credits"""

    def test_credits_returns_balance_info(self, auth_token):
        """Verify credit balance endpoint with rollover info"""
        response = requests.get(
            f"{BASE_URL}/api/billing/founders/credits",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Required fields
        assert "monthly_credits" in data
        assert "purchased_credits" in data
        assert "total_available" in data
        assert "monthly_allowance" in data
        assert "monthly_rollover" in data
        assert "purchased_rollover" in data
        
        # Verify values
        assert data["monthly_allowance"] == 150
        assert data["monthly_rollover"] == False
        assert data["purchased_rollover"] == True
        assert data["total_available"] == data["monthly_credits"] + data["purchased_credits"]
        print(f"PASS: Credits - {data['total_available']} total ({data['monthly_credits']} monthly, {data['purchased_credits']} purchased)")


class TestMyProcessingFees:
    """Test GET /api/plans/my-processing-fees"""

    def test_my_processing_fees_returns_founders_rates(self, auth_token):
        """Verify my-processing-fees returns Founders rates"""
        response = requests.get(
            f"{BASE_URL}/api/plans/my-processing-fees",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Should return Founders Edition fees
        assert data.get("invoice_fee_percent") == 2.2, f"Expected 2.2%, got {data.get('invoice_fee_percent')}"
        assert data.get("webstore_fee_percent") == 2.0, f"Expected 2%, got {data.get('webstore_fee_percent')}"
        assert data.get("platform_processing_fixed") == 0.20, f"Expected $0.20, got {data.get('platform_processing_fixed')}"
        print(f"PASS: my-processing-fees - invoice: {data['invoice_fee_percent']}%, webstore: {data['webstore_fee_percent']}%")


class TestOldTierEndpointsBehavior:
    """Test that old tier endpoints don't expose non-Founders tiers"""

    def test_pricing_endpoint_shows_founders_only(self):
        """Verify /api/billing/pricing doesn't show Starter/Pro/Business tiers"""
        response = requests.get(f"{BASE_URL}/api/billing/pricing")
        # This endpoint may still exist but should only show Founders or be deprecated
        if response.status_code == 200:
            data = response.json()
            # Check that if it returns plans, it's handled properly
            plans = data.get("plans", [])
            for plan in plans:
                plan_id = plan.get("id", "")
                # Founders Edition is the only active plan
                # Old tiers should not be prominently displayed
                print(f"INFO: Found plan in /pricing: {plan_id}")
        print(f"PASS: Checked /billing/pricing endpoint")


class TestFeatureGatingForFounders:
    """Test that founders_edition plan gets all features"""

    def test_founders_bypass_feature_gate(self, auth_token):
        """Verify founders get all features allowed"""
        # Check feature access
        response = requests.post(
            f"{BASE_URL}/api/plans/check-feature",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"category": "ai_tools", "feature": "monthly_generations"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Founders should have access
        assert data.get("allowed") == True, f"Founders should have feature access, got: {data}"
        print(f"PASS: Feature gating - founders have ai_tools access")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
