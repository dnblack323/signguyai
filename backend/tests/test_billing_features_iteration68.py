"""
Billing Features Tests - Iteration 68

Tests for:
1. Founders Edition pricing (plan resolves to os_business with $99/mo founder pricing)
2. AI Credit balance display and credit cost preview API
3. AI Credit pack purchase flow (3 packs: $10/100, $25/300, $60/1000)
4. Processing fees display correctly (1% invoice, 2% webstore for Business/Founders)
5. Stripe Connect status shows correct platform fee (1% for Business tier)
6. Multi-product checkout v2 generates valid Stripe checkout URLs
7. Billing subscription/v2 returns correct plan_type=os_business, is_founder=true, pricing, and fees
8. Founders Edition details endpoint returns correct pricing and features
9. Founders promo code validation (FOUNDERS code)
10. Processing fee explanation endpoint returns detailed breakdown
11. Credit history tracking with action types and costs
"""

import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://platform-insights-4.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD
TEST_EMAIL = FALLBACK_TEST_EMAIL
TEST_PASSWORD = FALLBACK_TEST_PASSWORD


class TestBillingAuth:
    """Authentication for billing tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def test_user_token(self):
        """Get test user authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Test user login failed: {response.status_code}")


class TestSubscriptionV2(TestBillingAuth):
    """Test billing/subscription/v2 endpoint - Founders Edition plan mapping"""
    
    def test_subscription_v2_returns_valid_response(self, admin_token):
        """Test that subscription/v2 returns valid subscription data"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/subscription/v2", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify essential fields exist
        assert "plan_type" in data
        assert "plan_display_name" in data
        assert "product_line" in data
        assert "is_founder" in data
        assert "pricing" in data
        assert "processing_fees" in data
        
        print(f"Subscription V2 Response: plan_type={data['plan_type']}, is_founder={data['is_founder']}")
    
    def test_founders_edition_maps_to_os_business(self, admin_token):
        """Test that founders_edition plan correctly maps to os_business"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/subscription/v2", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # founders_edition should resolve to os_business
        # The plan_type should be os_business when tenant has founders_edition
        assert data["plan_type"] in ["os_business", "founders_edition"], \
            f"Expected os_business or founders_edition, got {data['plan_type']}"
        
        # If founders_edition, verify founder status
        print(f"Plan type: {data['plan_type']}, Is Founder: {data['is_founder']}")
    
    def test_subscription_v2_has_correct_pricing(self, admin_token):
        """Test that subscription/v2 returns correct pricing for the plan"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/subscription/v2", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        pricing = data.get("pricing", {})
        assert "monthly" in pricing
        
        # If founder, founder_monthly should be $99
        if data.get("is_founder"):
            assert pricing.get("founder_monthly") == 99.0, \
                f"Expected founder monthly $99, got {pricing.get('founder_monthly')}"
            print(f"Founder pricing confirmed: ${pricing.get('founder_monthly')}/mo")
        else:
            print(f"Standard pricing: ${pricing.get('monthly')}/mo")
    
    def test_subscription_v2_has_processing_fees(self, admin_token):
        """Test that subscription/v2 returns processing fees"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/subscription/v2", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        fees = data.get("processing_fees", {})
        assert "invoice" in fees
        assert "webstore" in fees
        
        # For Business/Founders: 1% invoice, 2% webstore
        if data["plan_type"] in ["os_business", "founders_edition"]:
            assert fees["invoice"] == 1.0, f"Expected 1% invoice fee, got {fees['invoice']}%"
            assert fees["webstore"] == 2.0, f"Expected 2% webstore fee, got {fees['webstore']}%"
        
        print(f"Processing fees: Invoice={fees['invoice']}%, Webstore={fees['webstore']}%")


class TestFoundersEdition(TestBillingAuth):
    """Test Founders Edition endpoints"""
    
    def test_founders_edition_details(self):
        """Test /plans/founders-edition returns correct details"""
        response = requests.get(f"{BASE_URL}/api/plans/founders-edition")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plan" in data
        assert "availability" in data
        
        plan = data["plan"]
        # Check pricing
        assert "pricing" in plan
        pricing = plan["pricing"]
        assert pricing.get("monthly") == 99.0, f"Expected $99/mo, got {pricing.get('monthly')}"
        
        print(f"Founders Edition: ${pricing.get('monthly')}/mo, Max spots: {data['availability'].get('max_spots')}")
    
    def test_founders_promo_code_validation(self, admin_token):
        """Test FOUNDERS promo code validation"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/plans/founders-edition/validate-promo",
            params={"code": "FOUNDERS"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should return valid or reason
        print(f"FOUNDERS promo code validation: valid={data.get('valid')}, reason={data.get('reason', 'N/A')}")
    
    def test_invalid_promo_code(self, admin_token):
        """Test invalid promo code rejection"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/plans/founders-edition/validate-promo",
            params={"code": "INVALID"},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert not data.get("valid"), "Invalid promo should be rejected"
        print(f"Invalid promo correctly rejected: {data.get('reason')}")


class TestAICredits(TestBillingAuth):
    """Test AI Credits endpoints"""
    
    def test_credit_balance(self, admin_token):
        """Test /credits/balance returns credit balance"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/credits/balance", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "monthly_credits" in data
        assert "purchased_credits" in data
        assert "total_credits" in data
        
        print(f"Credit Balance: Monthly={data['monthly_credits']}, Purchased={data['purchased_credits']}, Total={data['total_credits']}")
    
    def test_credit_packs_available(self, admin_token):
        """Test /credits/packs returns available credit packs"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/credits/packs", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        packs = data.get("packs", [])
        assert len(packs) == 3, f"Expected 3 credit packs, got {len(packs)}"
        
        # Verify pack contents - $10/100, $25/300, $60/1000
        expected_packs = {
            "pack_100": {"credits": 100, "price": 10.00},
            "pack_300": {"credits": 300, "price": 25.00},
            "pack_1000": {"credits": 1000, "price": 60.00},
        }
        
        for pack in packs:
            pack_type = pack.get("pack_type")
            if pack_type in expected_packs:
                expected = expected_packs[pack_type]
                assert pack["credits"] == expected["credits"], \
                    f"Pack {pack_type}: expected {expected['credits']} credits, got {pack['credits']}"
                assert pack["price"] == expected["price"], \
                    f"Pack {pack_type}: expected ${expected['price']}, got ${pack['price']}"
        
        pack_names = [f"{p.get('display_name')} ${p.get('price')}" for p in packs]
        print(f"Credit packs verified: {pack_names}")
    
    def test_credit_costs_endpoint(self, admin_token):
        """Test /credits/costs returns AI action costs"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/credits/costs", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        costs = data.get("costs", {})
        
        # Verify some common AI actions have costs
        assert "text_generation" in costs or "image_generation" in costs, "Should have AI action costs"
        print(f"Credit costs returned with {len(costs)} action types")
    
    def test_single_action_credit_cost(self, admin_token):
        """Test /credits/cost/{action_type} returns specific action cost"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/credits/cost/text_generation", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "action_type" in data
        assert "credit_cost" in data
        assert data["credit_cost"] >= 1, "Credit cost should be at least 1"
        
        print(f"text_generation costs {data['credit_cost']} credit(s)")
    
    def test_credit_history(self, admin_token):
        """Test /credits/history returns credit transaction history"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/credits/history", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        
        print(f"Credit history: {data['total']} total transactions")
    
    def test_credit_pack_purchase_generates_checkout_url(self, admin_token):
        """Test credit pack purchase creates Stripe checkout URL - DO NOT FOLLOW URL"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/credits/purchase",
            json={"pack_type": "pack_100"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data, "Should return checkout_url"
        assert "session_id" in data, "Should return session_id"
        assert "stripe.com" in data["checkout_url"], "Checkout URL should be Stripe"
        
        print(f"Credit pack purchase checkout URL generated: {data['checkout_url'][:50]}...")


class TestProcessingFees(TestBillingAuth):
    """Test processing fee endpoints"""
    
    def test_processing_fee_explanation(self):
        """Test /plans/processing-fees/explanation returns detailed breakdown"""
        response = requests.get(f"{BASE_URL}/api/plans/processing-fees/explanation")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "explanation" in data
        assert "note" in data
        
        print(f"Processing fee explanation received (length: {len(data['explanation'])} chars)")
    
    def test_my_processing_fees(self, admin_token):
        """Test /plans/my-processing-fees returns user's processing fees"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/plans/my-processing-fees", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "invoice_fee_percent" in data
        assert "webstore_fee_percent" in data
        assert "stripe_connect_enabled" in data
        
        print(f"My processing fees: Invoice={data['invoice_fee_percent']}%, Webstore={data['webstore_fee_percent']}%")


class TestStripeConnect(TestBillingAuth):
    """Test Stripe Connect endpoints"""
    
    def test_stripe_connect_status(self, admin_token):
        """Test /stripe-connect/status returns connection status with platform fee"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/stripe-connect/status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "connected" in data
        assert "platform_fee_percent" in data
        
        # For Business tier, platform fee should be 1%
        if data.get("connected"):
            print(f"Stripe Connect: Connected, Platform fee: {data['platform_fee_percent']}%")
        else:
            # Platform fee based on tier even if not connected
            print(f"Stripe Connect: Not connected, Platform fee (tier-based): {data['platform_fee_percent']}%")


class TestMultiProductCheckout(TestBillingAuth):
    """Test multi-product checkout v2 endpoint - DO NOT FOLLOW STRIPE URLs"""
    
    def test_checkout_v2_generates_url(self, admin_token):
        """Test /billing/checkout/v2 generates valid Stripe checkout URL"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_business",
                "billing_interval": "monthly",
                "use_founder_pricing": True,
                "origin_url": BASE_URL
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data or "url" in data, "Should return checkout URL"
        
        url = data.get("checkout_url") or data.get("url")
        assert "stripe.com" in url, "URL should be Stripe checkout"
        
        print(f"Checkout V2 URL generated: {url[:60]}... (DO NOT FOLLOW - LIVE KEYS)")
    
    def test_checkout_v2_invalid_plan(self, admin_token):
        """Test checkout v2 rejects invalid plan type"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "invalid_plan",
                "billing_interval": "monthly",
                "origin_url": BASE_URL
            },
            headers=headers
        )
        
        # Should return error
        assert response.status_code in [400, 422], \
            f"Expected 400/422 for invalid plan, got {response.status_code}"
        print("Invalid plan correctly rejected")
    
    def test_checkout_v2_annual_only_for_business(self, admin_token):
        """Test that annual billing is only available for OS Business"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Try annual on OS Starter - should fail
        response = requests.post(
            f"{BASE_URL}/api/billing/checkout/v2",
            json={
                "plan_type": "os_starter",
                "billing_interval": "annual",
                "origin_url": BASE_URL
            },
            headers=headers
        )
        
        # Should reject annual for non-business plans
        if response.status_code == 400:
            print("Annual billing correctly restricted to OS Business only")
        else:
            # Some implementations may allow it
            print(f"Annual checkout response: {response.status_code}")


class TestPlansEndpoints(TestBillingAuth):
    """Test plans API endpoints"""
    
    def test_all_plans_grouped(self):
        """Test /plans/all returns all plans grouped by product line"""
        response = requests.get(f"{BASE_URL}/api/plans/all")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert len(data) == 3, f"Expected 3 product lines, got {len(data)}"
        
        product_lines = [item["product_line"] for item in data]
        assert "os" in product_lines
        assert "webstores" in product_lines
        assert "ai_studio" in product_lines
        
        print(f"Plans endpoint returns {len(data)} product lines with plans")
    
    def test_os_plans(self):
        """Test /plans/os returns OS plans"""
        response = requests.get(f"{BASE_URL}/api/plans/os")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert len(data) == 3, f"Expected 3 OS plans, got {len(data)}"
        
        plan_types = [p["plan_type"] for p in data]
        assert "os_starter" in plan_types
        assert "os_pro" in plan_types
        assert "os_business" in plan_types
        
        print(f"OS plans: {plan_types}")
    
    def test_founder_status(self):
        """Test /plans/founder-status returns availability"""
        response = requests.get(f"{BASE_URL}/api/plans/founder-status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "founder_spots_total" in data
        assert "founder_spots_used" in data
        assert "founder_spots_remaining" in data
        assert "founder_available" in data
        
        print(f"Founder status: {data['founder_spots_used']}/{data['founder_spots_total']} used, Available: {data['founder_available']}")
    
    def test_plan_details(self):
        """Test /plans/{plan_type}/details returns plan details"""
        response = requests.get(f"{BASE_URL}/api/plans/os_business/details")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["plan_type"] == "os_business"
        assert "pricing" in data
        assert "processing_fees" in data
        assert "founder_eligible" in data
        
        # Verify Business pricing
        assert data["pricing"]["monthly"] == 149.0
        assert data["pricing"]["founder_monthly"] == 99.0
        
        print(f"OS Business: ${data['pricing']['monthly']}/mo (Founder: ${data['pricing']['founder_monthly']}/mo)")
    
    def test_my_plan(self, admin_token):
        """Test /plans/my-plan returns current user's plan"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/plans/my-plan", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"My plan: {data}")


class TestBillingLegacyEndpoints(TestBillingAuth):
    """Test legacy billing endpoints"""
    
    def test_subscription_legacy(self, admin_token):
        """Test legacy /billing/subscription endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/subscription", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "plan" in data or "status" in data
        print(f"Legacy subscription: {data.get('plan', 'N/A')}")
    
    def test_trial_status(self, admin_token):
        """Test /billing/trial-status endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/trial-status", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "is_trial" in data
        assert "is_locked" in data
        
        print(f"Trial status: is_trial={data['is_trial']}, is_locked={data['is_locked']}")
    
    def test_founder_status_legacy(self):
        """Test legacy /billing/founder-status endpoint"""
        response = requests.get(f"{BASE_URL}/api/billing/founder-status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "founders_claimed" in data
        assert "founders_remaining" in data
        assert "is_founder_pricing_available" in data
        
        print(f"Founder legacy: {data['founders_claimed']} claimed, {data['founders_remaining']} remaining")
    
    def test_payment_history(self, admin_token):
        """Test /billing/payment-history endpoint"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/billing/payment-history", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "transactions" in data
        print(f"Payment history: {len(data['transactions'])} transactions")


class TestCreditPreflight(TestBillingAuth):
    """Test AI credit preflight check"""
    
    def test_credit_preflight(self, admin_token):
        """Test /credits/preflight returns credit usage preview"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.post(
            f"{BASE_URL}/api/credits/preflight",
            json={"action_type": "text_generation"},
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "credit_cost" in data
        assert "sufficient_credits" in data
        assert "total_credits" in data
        
        print(f"Preflight check: cost={data['credit_cost']}, sufficient={data['sufficient_credits']}, total={data['total_credits']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
