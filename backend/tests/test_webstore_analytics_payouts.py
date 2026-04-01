"""
Webstore Analytics and Payouts Tests
Tests the NEW analytics and payouts endpoints added to webstores.py:
1. GET /api/webstores/v2/{id}/analytics - Returns summary, sales_by_day, top_products, fundraiser_metrics
2. GET /api/webstores/v2/{id}/payouts - Returns list of recorded payouts
3. POST /api/webstores/v2/{id}/record-payout - Records a payout and updates balances

Prerequisites:
- Admin login credentials
- Complete order flow to generate payout_owed balance
"""

import pytest
import requests
import os
import time
from datetime import datetime
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = LEGACY_ADMIN_EMAIL
TEST_PASSWORD = LEGACY_ADMIN_PASSWORD


class TestWebstoreAnalytics:
    """Tests for GET /api/webstores/v2/{id}/analytics endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in login response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_webstore_with_order(self, auth_headers):
        """Create a webstore, product, and place an order to generate analytics data"""
        timestamp = int(time.time())
        
        # 1. Create webstore (fundraiser type to test fundraiser_metrics)
        webstore_data = {
            "name": f"TEST_Analytics_Store_{timestamp}",
            "store_type": "fundraiser",
            "owner_name": f"TEST_Owner_{timestamp}",
            "owner_email": "test_analytics@example.com",
            "owner_phone": "555-ANAL",
            "description": "Test store for analytics testing",
            "is_public": True,
            "fundraiser_goal": 1000.00,
            "fundraiser_profit_percent": 20
        }
        
        webstore_resp = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers,
            json=webstore_data
        )
        assert webstore_resp.status_code == 200, f"Failed to create webstore: {webstore_resp.text}"
        webstore = webstore_resp.json()
        
        # 2. Create product
        product_data = {
            "name": f"TEST_Analytics_Product_{timestamp}",
            "description": "Test product for analytics testing",
            "category": "signs",
            "base_cost": 10.00,
            "retail_price": 25.00
        }
        
        product_resp = requests.post(
            f"{BASE_URL}/api/products",
            headers=auth_headers,
            json=product_data
        )
        assert product_resp.status_code == 200, f"Failed to create product: {product_resp.text}"
        product = product_resp.json()
        
        # 3. Assign product to webstore
        assign_resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/products",
            headers=auth_headers,
            json={"product_id": product["id"], "is_enabled": True}
        )
        assert assign_resp.status_code == 200, f"Failed to assign product: {assign_resp.text}"
        
        # 4. Place order to generate analytics data
        order_data = {
            "webstore_id": webstore["id"],
            "customer_name": f"TEST_Analytics_Customer_{timestamp}",
            "customer_email": f"test_analytics_{timestamp}@example.com",
            "customer_phone": "555-TEST",
            "items": [
                {"product_id": product["id"], "quantity": 3}
            ],
            "notes": "Order for analytics testing"
        }
        
        order_resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        assert order_resp.status_code == 200, f"Failed to create order: {order_resp.text}"
        order = order_resp.json()
        
        yield {
            "webstore": webstore,
            "product": product,
            "order": order,
            "expected_subtotal": 25.00 * 3,  # 75.00
            "expected_profit": (25.00 - 10.00) * 3,  # 45.00
            "expected_commission": ((25.00 - 10.00) * 3) * 0.20  # 9.00 (20% of profit)
        }
        
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/webstores/v2/{webstore['id']}", headers=auth_headers)
            requests.delete(f"{BASE_URL}/api/products/{product['id']}", headers=auth_headers)
        except Exception:
            pass
    
    # ============== Test 1: Analytics Endpoint Returns 200 ==============
    def test_analytics_endpoint_exists(self, auth_headers, test_webstore_with_order):
        """Test that GET /api/webstores/v2/{id}/analytics returns 200"""
        webstore = test_webstore_with_order["webstore"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Analytics endpoint returned {response.status_code}: {response.text}"
        print("✓ Analytics endpoint returns 200")
    
    # ============== Test 2: Analytics Returns Summary ==============
    def test_analytics_summary(self, auth_headers, test_webstore_with_order):
        """Test that analytics returns correct summary structure"""
        webstore = test_webstore_with_order["webstore"]
        expected_subtotal = test_webstore_with_order["expected_subtotal"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data, "Analytics missing 'summary' field"
        
        summary = data["summary"]
        # Check required fields in summary
        required_fields = ["total_revenue", "total_orders", "pending_orders", "completed_orders", "total_profit", "shop_profit", "avg_order_value"]
        for field in required_fields:
            assert field in summary, f"Summary missing '{field}' field"
        
        # Verify values
        assert summary["total_orders"] >= 1, "Should have at least 1 order"
        assert summary["total_revenue"] >= expected_subtotal, f"Revenue should be at least {expected_subtotal}"
        
        print("✓ Analytics summary structure verified")
        print(f"  - Total Revenue: ${summary['total_revenue']:.2f}")
        print(f"  - Total Orders: {summary['total_orders']}")
        print(f"  - Total Profit: ${summary['total_profit']:.2f}")
    
    # ============== Test 3: Analytics Returns Sales By Day ==============
    def test_analytics_sales_by_day(self, auth_headers, test_webstore_with_order):
        """Test that analytics returns sales_by_day array"""
        webstore = test_webstore_with_order["webstore"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "sales_by_day" in data, "Analytics missing 'sales_by_day' field"
        
        sales_by_day = data["sales_by_day"]
        assert isinstance(sales_by_day, list), "sales_by_day should be a list"
        assert len(sales_by_day) == 14, f"sales_by_day should have 14 days, got {len(sales_by_day)}"
        
        # Check structure of each day
        for day in sales_by_day:
            assert "date" in day, "Day missing 'date' field"
            assert "label" in day, "Day missing 'label' field"
            assert "amount" in day, "Day missing 'amount' field"
        
        # Today should have sales
        today = datetime.now().strftime("%Y-%m-%d")
        today_sales = next((d for d in sales_by_day if d["date"] == today), None)
        if today_sales:
            print(f"✓ Today's sales: ${today_sales['amount']:.2f}")
        
        print("✓ Sales by day structure verified (14 days)")
    
    # ============== Test 4: Analytics Returns Top Products ==============
    def test_analytics_top_products(self, auth_headers, test_webstore_with_order):
        """Test that analytics returns top_products array"""
        webstore = test_webstore_with_order["webstore"]
        product = test_webstore_with_order["product"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "top_products" in data, "Analytics missing 'top_products' field"
        
        top_products = data["top_products"]
        assert isinstance(top_products, list), "top_products should be a list"
        
        if len(top_products) > 0:
            # Check structure
            for p in top_products:
                assert "product_id" in p, "Product missing 'product_id'"
                assert "name" in p, "Product missing 'name'"
                assert "quantity" in p, "Product missing 'quantity'"
                assert "revenue" in p, "Product missing 'revenue'"
            
            # Our test product should be in the list
            product_ids = [p["product_id"] for p in top_products]
            assert product["id"] in product_ids, "Test product should be in top products"
            
            test_product_stats = next((p for p in top_products if p["product_id"] == product["id"]), None)
            print("✓ Top products structure verified")
            print(f"  - {test_product_stats['name']}: {test_product_stats['quantity']} units, ${test_product_stats['revenue']:.2f}")
    
    # ============== Test 5: Analytics Returns Fundraiser Metrics ==============
    def test_analytics_fundraiser_metrics(self, auth_headers, test_webstore_with_order):
        """Test that analytics returns fundraiser_metrics for fundraiser stores"""
        webstore = test_webstore_with_order["webstore"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "fundraiser_metrics" in data, "Analytics missing 'fundraiser_metrics' field"
        
        # Our test store is a fundraiser, so metrics should not be null
        fundraiser_metrics = data["fundraiser_metrics"]
        assert fundraiser_metrics is not None, "Fundraiser metrics should not be null for fundraiser store"
        
        # Check structure
        required_fields = ["goal", "raised", "progress_percent", "profit_percent"]
        for field in required_fields:
            assert field in fundraiser_metrics, f"Fundraiser metrics missing '{field}' field"
        
        assert fundraiser_metrics["goal"] == 1000.00, "Goal should be 1000.00"
        assert fundraiser_metrics["profit_percent"] == 20, "Profit percent should be 20"
        
        print("✓ Fundraiser metrics structure verified")
        print(f"  - Goal: ${fundraiser_metrics['goal']:.2f}")
        print(f"  - Raised: ${fundraiser_metrics['raised']:.2f}")
        print(f"  - Progress: {fundraiser_metrics['progress_percent']:.1f}%")
    
    # ============== Test 6: Analytics Returns Payout Info ==============
    def test_analytics_payout_info(self, auth_headers, test_webstore_with_order):
        """Test that analytics returns payout_info"""
        webstore = test_webstore_with_order["webstore"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "payout_info" in data, "Analytics missing 'payout_info' field"
        
        payout_info = data["payout_info"]
        required_fields = ["total_owed", "total_paid", "pending_payout", "commission_rate"]
        for field in required_fields:
            assert field in payout_info, f"Payout info missing '{field}' field"
        
        print("✓ Payout info structure verified")
        print(f"  - Total Owed: ${payout_info['total_owed']:.2f}")
        print(f"  - Total Paid: ${payout_info['total_paid']:.2f}")


class TestWebstorePayouts:
    """Tests for GET /api/webstores/v2/{id}/payouts endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_webstore(self, auth_headers):
        """Create a test webstore"""
        timestamp = int(time.time())
        webstore_data = {
            "name": f"TEST_Payouts_Store_{timestamp}",
            "store_type": "creator",
            "owner_name": f"TEST_Payouts_Owner_{timestamp}",
            "owner_email": "test_payouts@example.com",
            "is_public": True,
            "creator_commission_type": "percentage",
            "creator_commission_value": 15
        }
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers,
            json=webstore_data
        )
        assert response.status_code == 200, f"Failed to create webstore: {response.text}"
        webstore = response.json()
        
        yield webstore
        
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/webstores/v2/{webstore['id']}", headers=auth_headers)
        except Exception:
            pass
    
    # ============== Test 7: Payouts Endpoint Returns 200 ==============
    def test_payouts_endpoint_exists(self, auth_headers, test_webstore):
        """Test that GET /api/webstores/v2/{id}/payouts returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{test_webstore['id']}/payouts",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Payouts endpoint returned {response.status_code}: {response.text}"
        print("✓ Payouts endpoint returns 200")
    
    # ============== Test 8: Payouts Returns Array ==============
    def test_payouts_returns_array(self, auth_headers, test_webstore):
        """Test that payouts returns an array (empty for new store)"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{test_webstore['id']}/payouts",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        payouts = response.json()
        assert isinstance(payouts, list), "Payouts should return a list"
        print(f"✓ Payouts returns array with {len(payouts)} records")


class TestWebstoreRecordPayout:
    """Tests for POST /api/webstores/v2/{id}/record-payout endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_webstore_with_balance(self, auth_headers):
        """Create webstore with order to have payout_owed balance"""
        timestamp = int(time.time())
        
        # 1. Create webstore
        webstore_data = {
            "name": f"TEST_RecordPayout_Store_{timestamp}",
            "store_type": "creator",
            "owner_name": f"TEST_RecordPayout_Owner_{timestamp}",
            "owner_email": "test_recordpayout@example.com",
            "is_public": True,
            "creator_commission_type": "percentage",
            "creator_commission_value": 25
        }
        
        webstore_resp = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers,
            json=webstore_data
        )
        assert webstore_resp.status_code == 200, f"Failed to create webstore: {webstore_resp.text}"
        webstore = webstore_resp.json()
        
        # 2. Create product
        product_data = {
            "name": f"TEST_RecordPayout_Product_{timestamp}",
            "description": "Test product",
            "category": "signs",
            "base_cost": 20.00,
            "retail_price": 50.00
        }
        
        product_resp = requests.post(
            f"{BASE_URL}/api/products",
            headers=auth_headers,
            json=product_data
        )
        assert product_resp.status_code == 200
        product = product_resp.json()
        
        # 3. Assign product to webstore
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/products",
            headers=auth_headers,
            json={"product_id": product["id"], "is_enabled": True}
        )
        
        # 4. Place order to generate payout_owed
        # Profit = (50-20) * 2 = 60, Commission = 60 * 0.25 = 15
        order_data = {
            "webstore_id": webstore["id"],
            "customer_name": f"TEST_RecordPayout_Customer_{timestamp}",
            "customer_email": f"test_recordpayout_{timestamp}@example.com",
            "items": [{"product_id": product["id"], "quantity": 2}],
            "notes": "Order for record-payout testing"
        }
        
        order_resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/orders",
            json=order_data,
            headers={"Content-Type": "application/json"}
        )
        assert order_resp.status_code == 200, f"Failed to create order: {order_resp.text}"
        order = order_resp.json()
        
        # Verify webstore now has payout_owed
        updated_webstore_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}",
            headers=auth_headers
        )
        updated_webstore = updated_webstore_resp.json()
        
        yield {
            "webstore": updated_webstore,
            "product": product,
            "order": order,
            "expected_commission": 15.00  # (50-20) * 2 * 0.25
        }
        
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/webstores/v2/{webstore['id']}", headers=auth_headers)
            requests.delete(f"{BASE_URL}/api/products/{product['id']}", headers=auth_headers)
        except Exception:
            pass
    
    # ============== Test 9: Record Payout Success ==============
    def test_record_payout_success(self, auth_headers, test_webstore_with_balance):
        """Test that POST /api/webstores/v2/{id}/record-payout works"""
        webstore = test_webstore_with_balance["webstore"]
        payout_owed = webstore.get("payout_owed", 0)
        
        # Record a partial payout
        payout_amount = min(5.00, payout_owed) if payout_owed > 0 else 0
        
        if payout_amount == 0:
            pytest.skip("No payout_owed to test with")
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/record-payout",
            headers=auth_headers,
            params={"amount": payout_amount, "notes": "Test payout recording"}
        )
        assert response.status_code == 200, f"Record payout failed: {response.text}"
        
        result = response.json()
        assert "message" in result, "Response missing 'message'"
        assert "payout_id" in result, "Response missing 'payout_id'"
        assert "new_balance_owed" in result, "Response missing 'new_balance_owed'"
        assert "total_paid" in result, "Response missing 'total_paid'"
        
        # Verify balance was updated
        expected_balance = payout_owed - payout_amount
        assert abs(result["new_balance_owed"] - expected_balance) < 0.01, f"Balance mismatch: expected {expected_balance}, got {result['new_balance_owed']}"
        
        print("✓ Payout recorded successfully")
        print(f"  - Amount: ${payout_amount:.2f}")
        print(f"  - New Balance: ${result['new_balance_owed']:.2f}")
        print(f"  - Total Paid: ${result['total_paid']:.2f}")
    
    # ============== Test 10: Record Payout Validation - Zero Amount ==============
    def test_record_payout_zero_amount(self, auth_headers, test_webstore_with_balance):
        """Test that record-payout rejects zero amount"""
        webstore = test_webstore_with_balance["webstore"]
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/record-payout",
            headers=auth_headers,
            params={"amount": 0, "notes": "Should fail"}
        )
        assert response.status_code == 400, f"Expected 400 for zero amount, got {response.status_code}"
        print("✓ Zero amount correctly rejected with 400")
    
    # ============== Test 11: Record Payout Validation - Negative Amount ==============
    def test_record_payout_negative_amount(self, auth_headers, test_webstore_with_balance):
        """Test that record-payout rejects negative amount"""
        webstore = test_webstore_with_balance["webstore"]
        
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/record-payout",
            headers=auth_headers,
            params={"amount": -10.00, "notes": "Should fail"}
        )
        assert response.status_code == 400, f"Expected 400 for negative amount, got {response.status_code}"
        print("✓ Negative amount correctly rejected with 400")
    
    # ============== Test 12: Record Payout Validation - Exceeds Owed ==============
    def test_record_payout_exceeds_owed(self, auth_headers, test_webstore_with_balance):
        """Test that record-payout rejects amount exceeding owed"""
        webstore = test_webstore_with_balance["webstore"]
        
        # Get current balance
        webstore_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}",
            headers=auth_headers
        )
        current_webstore = webstore_resp.json()
        current_owed = current_webstore.get("payout_owed", 0)
        
        # Try to record more than owed
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/record-payout",
            headers=auth_headers,
            params={"amount": current_owed + 1000.00, "notes": "Should fail"}
        )
        assert response.status_code == 400, f"Expected 400 for amount exceeding owed, got {response.status_code}"
        print("✓ Amount exceeding owed correctly rejected with 400")
    
    # ============== Test 13: Payout Appears in Payouts List ==============
    def test_payout_appears_in_list(self, auth_headers, test_webstore_with_balance):
        """Test that recorded payout appears in payouts list"""
        webstore = test_webstore_with_balance["webstore"]
        
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{webstore['id']}/payouts",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        payouts = response.json()
        assert len(payouts) >= 1, "Should have at least one payout recorded"
        
        # Check structure of payout record
        payout = payouts[0]
        required_fields = ["id", "webstore_id", "amount", "created_at"]
        for field in required_fields:
            assert field in payout, f"Payout missing '{field}' field"
        
        assert payout["webstore_id"] == webstore["id"]
        
        print("✓ Payout appears in payouts list")
        print(f"  - Payout ID: {payout['id'][:8]}...")
        print(f"  - Amount: ${payout['amount']:.2f}")


class TestAnalyticsEdgeCases:
    """Edge case tests for analytics endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return {
            "Authorization": f"Bearer {response.json()['access_token']}",
            "Content-Type": "application/json"
        }
    
    # ============== Test 14: Analytics 404 for Invalid Webstore ==============
    def test_analytics_invalid_webstore(self, auth_headers):
        """Test analytics returns 404 for non-existent webstore"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/non-existent-id-12345/analytics",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Analytics returns 404 for invalid webstore")
    
    # ============== Test 15: Payouts 404 for Invalid Webstore ==============
    def test_payouts_invalid_webstore(self, auth_headers):
        """Test payouts returns 404 for non-existent webstore"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/non-existent-id-12345/payouts",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Payouts returns 404 for invalid webstore")
    
    # ============== Test 16: Record Payout 404 for Invalid Webstore ==============
    def test_record_payout_invalid_webstore(self, auth_headers):
        """Test record-payout returns 404 for non-existent webstore"""
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/non-existent-id-12345/record-payout",
            headers=auth_headers,
            params={"amount": 10.00}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Record-payout returns 404 for invalid webstore")
    
    # ============== Test 17: Analytics Requires Auth ==============
    def test_analytics_requires_auth(self):
        """Test analytics requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/some-id/analytics"
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Analytics requires authentication")
    
    # ============== Test 18: Payouts Requires Auth ==============
    def test_payouts_requires_auth(self):
        """Test payouts requires authentication"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/some-id/payouts"
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Payouts requires authentication")
    
    # ============== Test 19: Record Payout Requires Auth ==============
    def test_record_payout_requires_auth(self):
        """Test record-payout requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/webstores/v2/some-id/record-payout",
            params={"amount": 10.00}
        )
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Record-payout requires authentication")


class TestBusinessWebstoreAnalytics:
    """Test analytics for business type webstore (no commission)"""
    
    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Login and get auth headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        return {
            "Authorization": f"Bearer {response.json()['access_token']}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def business_webstore_with_order(self, auth_headers):
        """Create business webstore with order"""
        timestamp = int(time.time())
        
        # Create business webstore
        webstore_data = {
            "name": f"TEST_Business_Analytics_{timestamp}",
            "store_type": "business",
            "owner_name": f"TEST_Business_Owner_{timestamp}",
            "is_public": True
        }
        
        webstore_resp = requests.post(
            f"{BASE_URL}/api/webstores/v2",
            headers=auth_headers,
            json=webstore_data
        )
        assert webstore_resp.status_code == 200
        webstore = webstore_resp.json()
        
        # Create product
        product_data = {
            "name": f"TEST_Business_Product_{timestamp}",
            "category": "signs",
            "base_cost": 10.00,
            "retail_price": 30.00
        }
        product_resp = requests.post(f"{BASE_URL}/api/products", headers=auth_headers, json=product_data)
        product = product_resp.json()
        
        # Assign product
        requests.post(f"{BASE_URL}/api/webstores/v2/{webstore['id']}/products", headers=auth_headers, json={"product_id": product["id"], "is_enabled": True})
        
        # Place order
        order_data = {
            "webstore_id": webstore["id"],
            "customer_name": f"TEST_Business_Customer_{timestamp}",
            "customer_email": f"test_business_{timestamp}@example.com",
            "items": [{"product_id": product["id"], "quantity": 1}]
        }
        requests.post(f"{BASE_URL}/api/webstores/v2/orders", json=order_data, headers={"Content-Type": "application/json"})
        
        yield webstore
        
        # Cleanup
        try:
            requests.delete(f"{BASE_URL}/api/webstores/v2/{webstore['id']}", headers=auth_headers)
            requests.delete(f"{BASE_URL}/api/products/{product['id']}", headers=auth_headers)
        except Exception:
            pass
    
    # ============== Test 20: Business Store Has No Fundraiser Metrics ==============
    def test_business_store_no_fundraiser_metrics(self, auth_headers, business_webstore_with_order):
        """Test that business store analytics has null fundraiser_metrics"""
        response = requests.get(
            f"{BASE_URL}/api/webstores/v2/{business_webstore_with_order['id']}/analytics",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["fundraiser_metrics"] is None, "Business store should have null fundraiser_metrics"
        print("✓ Business store correctly has null fundraiser_metrics")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
