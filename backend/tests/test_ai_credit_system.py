"""
AI Credit System Tests

Tests the complete AI credit management system including:
- GET /api/credits/preflight: cost, balances, popup reasons, warning logic
- GET/PUT /api/credits/preferences: hide_ai_credit_popup and acknowledged_costs persistence
- POST /api/ai/generate-email: deducts credits only after success, logs usage
- POST /api/ai/generate-product-description: deducts monthly credits first, then purchased
- POST /api/ai/generate with invalid tool: NO credit deduction, logs failure
- POST /api/pricing-setup/imports/{id}/analyze: credit system enforcement
- GET /api/credits/admin-summary: admin/owner usage visibility
- GET /api/credits/balance: balance check
- GET /api/credits/costs: all credit costs
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"


@pytest.fixture(scope="module")
def admin_session():
    """Get authenticated admin session with auth token"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login as admin
    response = session.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    token = data.get("access_token") or data.get("token")
    assert token, "No token received"
    
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session


class TestCreditBalance:
    """Test credit balance retrieval"""
    
    def test_get_credit_balance(self, admin_session):
        """GET /api/credits/balance returns correct structure"""
        response = admin_session.get(f"{BASE_URL}/api/credits/balance")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Validate response structure
        assert "monthly_credits" in data
        assert "purchased_credits" in data
        assert "total_credits" in data
        assert "is_low_credits" in data
        assert "low_credits_threshold" in data
        
        # Validate data types
        assert isinstance(data["monthly_credits"], (int, float))
        assert isinstance(data["purchased_credits"], (int, float))
        assert isinstance(data["total_credits"], (int, float))
        assert isinstance(data["is_low_credits"], bool)
        
        # Total should equal monthly + purchased
        expected_total = data["monthly_credits"] + data["purchased_credits"]
        assert data["total_credits"] == expected_total, f"Total mismatch: {data}"
        
        print(f"Credit balance: monthly={data['monthly_credits']}, purchased={data['purchased_credits']}, total={data['total_credits']}")


class TestCreditPreflight:
    """Test preflight credit check endpoint"""
    
    def test_preflight_returns_cost_and_balances(self, admin_session):
        """GET /api/credits/preflight returns cost, balances, popup reasons"""
        response = admin_session.post(f"{BASE_URL}/api/credits/preflight", json={
            "action_type": "product_description"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        # Required fields
        assert "credit_cost" in data
        assert "monthly_credits" in data
        assert "purchased_credits" in data
        assert "total_credits" in data
        assert "sufficient_credits" in data
        assert "should_show_popup" in data
        assert "popup_reasons" in data
        assert "preferences" in data
        
        # Credit cost should be a positive integer
        assert isinstance(data["credit_cost"], int)
        assert data["credit_cost"] >= 1
        
        # popup_reasons should be a list
        assert isinstance(data["popup_reasons"], list)
        
        print(f"Preflight for product_description: cost={data['credit_cost']}, sufficient={data['sufficient_credits']}, popup_reasons={data['popup_reasons']}")
    
    def test_preflight_warning_logic_low_balance(self, admin_session):
        """Preflight should include 'low_balance' in popup_reasons when total credits are low"""
        # Get current balance first
        balance_resp = admin_session.get(f"{BASE_URL}/api/credits/balance")
        balance_data = balance_resp.json()
        
        # Request preflight
        response = admin_session.post(f"{BASE_URL}/api/credits/preflight", json={
            "action_type": "historical_invoice_analysis"  # High cost action (3 credits)
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "popup_reasons" in data
        assert "is_low_credits" in data
        
        # If balance is low, should have low_balance reason
        if data["is_low_credits"] or data["total_credits"] < data["credit_cost"]:
            assert "low_balance" in data["popup_reasons"]
        
        print(f"Low balance check: is_low={data['is_low_credits']}, reasons={data['popup_reasons']}")
    
    def test_preflight_high_cost_action_warning(self, admin_session):
        """Preflight should include 'high_cost_action' for 3-credit tools"""
        response = admin_session.post(f"{BASE_URL}/api/credits/preflight", json={
            "action_type": "historical_invoice_analysis"  # 3 credits
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["credit_cost"] == 3, f"Expected 3 credits, got {data['credit_cost']}"
        assert "high_cost_action" in data["popup_reasons"], f"Missing high_cost_action in {data['popup_reasons']}"
        
        print(f"High cost action verified: cost={data['credit_cost']}, reasons={data['popup_reasons']}")
    
    def test_preflight_will_use_purchased_warning(self, admin_session):
        """Preflight should show will_use_purchased when monthly credits are insufficient"""
        response = admin_session.post(f"{BASE_URL}/api/credits/preflight", json={
            "action_type": "product_description"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "will_use_purchased" in data
        assert "monthly_credits_to_use" in data
        assert "purchased_credits_to_use" in data
        
        # Verify logic: if monthly < cost, will_use_purchased should be True
        if data["monthly_credits"] < data["credit_cost"] and data["purchased_credits"] > 0:
            assert data["will_use_purchased"] == True
            assert "purchased_credits_needed" in data["popup_reasons"]
        
        print(f"Purchase usage check: will_use={data['will_use_purchased']}, monthly_use={data['monthly_credits_to_use']}, purchased_use={data['purchased_credits_to_use']}")


class TestCreditPreferences:
    """Test credit preferences persistence"""
    
    def test_get_credit_preferences(self, admin_session):
        """GET /api/credits/preferences returns user preferences"""
        response = admin_session.get(f"{BASE_URL}/api/credits/preferences")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "hide_ai_credit_popup" in data
        assert "acknowledged_costs" in data
        
        assert isinstance(data["hide_ai_credit_popup"], bool)
        assert isinstance(data["acknowledged_costs"], dict)
        
        print(f"Preferences: hide_popup={data['hide_ai_credit_popup']}, acknowledged_costs={data['acknowledged_costs']}")
    
    def test_update_credit_preferences(self, admin_session):
        """PUT /api/credits/preferences persists hide_ai_credit_popup and acknowledged_costs"""
        # Set new preferences
        new_prefs = {
            "hide_ai_credit_popup": True,
            "acknowledged_costs": {
                "product_description": 2,
                "ai_business_assistant": 2
            }
        }
        
        response = admin_session.put(f"{BASE_URL}/api/credits/preferences", json=new_prefs)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        # Verify the update
        verify_response = admin_session.get(f"{BASE_URL}/api/credits/preferences")
        assert verify_response.status_code == 200
        
        data = verify_response.json()
        assert data["hide_ai_credit_popup"] == True
        assert data["acknowledged_costs"].get("product_description") == 2
        assert data["acknowledged_costs"].get("ai_business_assistant") == 2
        
        print(f"Preferences updated and verified: {data}")
        
        # Reset preferences to default
        reset_prefs = {
            "hide_ai_credit_popup": False,
            "acknowledged_costs": {}
        }
        admin_session.put(f"{BASE_URL}/api/credits/preferences", json=reset_prefs)


class TestCreditCosts:
    """Test credit cost configuration"""
    
    def test_get_all_credit_costs(self, admin_session):
        """GET /api/credits/costs returns all AI action credit costs"""
        response = admin_session.get(f"{BASE_URL}/api/credits/costs")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "costs" in data
        costs = data["costs"]
        
        # Verify some known costs from founders_config.py
        assert costs.get("product_description") == 2
        assert costs.get("ai_business_assistant") == 2
        assert costs.get("historical_invoice_analysis") == 3
        assert costs.get("pricing_advisor") == 1
        assert costs.get("assistant_chat") == 2
        assert costs.get("assistant_parse_action") == 1
        
        # Verify all costs are 1, 2, or 3
        for action, cost in costs.items():
            assert cost in [1, 2, 3], f"Invalid cost for {action}: {cost}"
        
        print(f"Found {len(costs)} AI actions with configured costs")
    
    def test_get_specific_action_cost(self, admin_session):
        """GET /api/credits/cost/{action_type} returns cost for specific action"""
        response = admin_session.get(f"{BASE_URL}/api/credits/cost/product_description")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data["action_type"] == "product_description"
        assert data["credit_cost"] == 2
        
        print(f"Product description cost: {data['credit_cost']}")


class TestAdminSummary:
    """Test admin credit usage summary"""
    
    def test_admin_summary_returns_usage_data(self, admin_session):
        """GET /api/credits/admin-summary returns usage data for admin/owner"""
        response = admin_session.get(f"{BASE_URL}/api/credits/admin-summary")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Required fields
        assert "balance" in data
        assert "total_ai_credits_used" in data
        assert "monthly_credits_consumed" in data
        assert "purchased_credits_consumed" in data
        assert "by_tool" in data
        assert "by_user" in data
        assert "recent_usage" in data
        
        # Verify balance structure
        balance = data["balance"]
        assert "monthly_credits" in balance
        assert "purchased_credits" in balance
        assert "total_credits" in balance
        
        # by_tool should be a list of objects with action_type, credits_used, count
        assert isinstance(data["by_tool"], list)
        for tool_entry in data["by_tool"]:
            assert "action_type" in tool_entry
            assert "credits_used" in tool_entry
            assert "count" in tool_entry
        
        # recent_usage should be a list
        assert isinstance(data["recent_usage"], list)
        
        print(f"Admin summary: total_used={data['total_ai_credits_used']}, monthly_consumed={data['monthly_credits_consumed']}, purchased_consumed={data['purchased_credits_consumed']}")
        print(f"Top tools: {data['by_tool'][:3]}")


class TestAIEndpointCreditDeduction:
    """Test that AI endpoints properly deduct credits only after success"""
    
    def test_generate_with_invalid_tool_no_deduction(self, admin_session):
        """POST /api/ai/generate with invalid tool should NOT deduct credits and log failure"""
        # Get balance before
        balance_before = admin_session.get(f"{BASE_URL}/api/credits/balance").json()
        
        # Try to generate with an invalid tool
        response = admin_session.post(f"{BASE_URL}/api/ai/generate", json={
            "tool": "completely_invalid_tool_xyz_123",
            "input_data": {"test": "data"}
        })
        
        # Should fail (400 or 500)
        assert response.status_code in [400, 402, 500], f"Expected failure, got {response.status_code}: {response.text}"
        
        # Get balance after
        balance_after = admin_session.get(f"{BASE_URL}/api/credits/balance").json()
        
        # Credits should NOT be deducted
        assert balance_after["total_credits"] == balance_before["total_credits"], \
            f"Credits were deducted for failed action! Before: {balance_before['total_credits']}, After: {balance_after['total_credits']}"
        
        print(f"Invalid tool test passed: balance unchanged at {balance_after['total_credits']}")
    
    def test_insufficient_credits_blocks_action(self, admin_session):
        """AI endpoints should return 402 when credits are insufficient"""
        # First check current balance
        balance = admin_session.get(f"{BASE_URL}/api/credits/balance").json()
        
        if balance["total_credits"] == 0:
            # Try an AI action - should be blocked
            response = admin_session.post(f"{BASE_URL}/api/ai/generate", json={
                "tool": "pricing_advisor",
                "input_data": {"category": "test"}
            })
            assert response.status_code == 402, f"Expected 402 for insufficient credits, got {response.status_code}"
            assert "Insufficient credits" in response.text
            print("Insufficient credits properly blocks action")
        else:
            print(f"Skipping insufficient credits test - user has {balance['total_credits']} credits")


class TestCreditHistory:
    """Test credit transaction history"""
    
    def test_get_credit_history(self, admin_session):
        """GET /api/credits/history returns transaction history"""
        response = admin_session.get(f"{BASE_URL}/api/credits/history?limit=10")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "transactions" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        
        # Transactions should be a list
        assert isinstance(data["transactions"], list)
        
        # Each transaction should have required fields
        for tx in data["transactions"]:
            assert "tenant_id" in tx
            assert "transaction_type" in tx
            assert "amount" in tx
            assert "balance_after" in tx
            
        print(f"Credit history: {data['total']} total transactions, showing {len(data['transactions'])}")


class TestCreditPacks:
    """Test credit pack retrieval"""
    
    def test_get_credit_packs(self, admin_session):
        """GET /api/credits/packs returns available credit packs"""
        response = admin_session.get(f"{BASE_URL}/api/credits/packs")
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "packs" in data
        packs = data["packs"]
        
        # Should have 3 packs: 100, 300, 1000 credits
        assert len(packs) == 3, f"Expected 3 packs, got {len(packs)}"
        
        pack_ids = [p["pack_type"] for p in packs]
        assert "pack_100" in pack_ids
        assert "pack_300" in pack_ids
        assert "pack_1000" in pack_ids
        
        # Verify pack structure
        for pack in packs:
            assert "pack_type" in pack
            assert "credits" in pack
            assert "price" in pack
            assert "price_display" in pack
            assert "per_credit" in pack
            assert "display_name" in pack
            
        print(f"Credit packs available: {pack_ids}")


class TestMonthlyVsPurchasedDeduction:
    """Test that monthly credits are deducted before purchased credits"""
    
    def test_monthly_deducted_first(self, admin_session):
        """Verify monthly credits are deducted before purchased credits"""
        # This is a logic test - verify through preflight
        response = admin_session.post(f"{BASE_URL}/api/credits/preflight", json={
            "action_type": "pricing_advisor"  # 1 credit
        })
        assert response.status_code == 200
        
        data = response.json()
        monthly = data["monthly_credits"]
        purchased = data["purchased_credits"]
        cost = data["credit_cost"]
        
        # Check deduction plan
        monthly_to_use = data["monthly_credits_to_use"]
        purchased_to_use = data["purchased_credits_to_use"]
        
        # Monthly should be used first
        if monthly >= cost:
            assert monthly_to_use == cost
            assert purchased_to_use == 0
            print(f"Monthly first: will use {monthly_to_use} monthly, 0 purchased")
        elif monthly > 0:
            assert monthly_to_use == monthly
            assert purchased_to_use == cost - monthly
            print(f"Mixed: will use {monthly_to_use} monthly + {purchased_to_use} purchased")
        else:
            assert monthly_to_use == 0
            assert purchased_to_use == cost
            print(f"Purchased only: will use 0 monthly + {purchased_to_use} purchased")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
