"""
Test Webstores Phase 2 Features:
- Webstore analytics endpoint
- Dashboard KPIs (Revenue, Orders, Profit, Avg Order Value)
- Sales trend data
- Top products
- Order status breakdown
- Fundraiser progress metrics
- Payouts management
"""
import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = SYNTHETIC_OWNER_EMAIL
OWNER_PASSWORD = SYNTHETIC_OWNER_PASSWORD


class TestWebstoresPhase2:
    """Test Webstores Phase 2 Analytics and Dashboard Features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as owner
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_api_health(self):
        """Test API health endpoint"""
        response = self.session.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"
        print("✅ API health check passed")
    
    def test_get_webstores_list(self):
        """Test getting list of webstores"""
        response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        assert response.status_code == 200
        stores = response.json()
        assert isinstance(stores, list)
        print(f"✅ Got {len(stores)} webstores")
        return stores
    
    def test_webstore_analytics_endpoint(self):
        """Test the analytics endpoint for a webstore"""
        # First get list of stores
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        assert stores_response.status_code == 200
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        # Test analytics for first store
        store = stores[0]
        store_id = store.get("id")
        
        analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
        assert analytics_response.status_code == 200
        analytics = analytics_response.json()
        
        # Verify analytics structure
        assert "store_id" in analytics
        assert "store_name" in analytics
        assert "store_type" in analytics
        assert "summary" in analytics
        assert "payout_info" in analytics
        assert "sales_by_day" in analytics
        assert "top_products" in analytics
        
        print(f"✅ Analytics endpoint working for store: {store.get('name')}")
        return analytics
    
    def test_analytics_summary_kpis(self):
        """Test that analytics summary contains all required KPIs"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        store_id = stores[0].get("id")
        analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
        analytics = analytics_response.json()
        
        summary = analytics.get("summary", {})
        
        # Verify all KPI fields exist
        assert "total_orders" in summary, "Missing total_orders in summary"
        assert "completed_orders" in summary, "Missing completed_orders in summary"
        assert "pending_orders" in summary, "Missing pending_orders in summary"
        assert "processing_orders" in summary, "Missing processing_orders in summary"
        assert "total_revenue" in summary, "Missing total_revenue in summary"
        assert "total_profit" in summary, "Missing total_profit in summary"
        assert "shop_profit" in summary, "Missing shop_profit in summary"
        assert "avg_order_value" in summary, "Missing avg_order_value in summary"
        
        print(f"✅ KPIs verified - Revenue: ${summary.get('total_revenue', 0):.2f}, Orders: {summary.get('total_orders', 0)}")
    
    def test_analytics_payout_info(self):
        """Test that payout info is correctly returned"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        store_id = stores[0].get("id")
        analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
        analytics = analytics_response.json()
        
        payout_info = analytics.get("payout_info", {})
        
        assert "total_earned" in payout_info, "Missing total_earned in payout_info"
        assert "total_paid_out" in payout_info, "Missing total_paid_out in payout_info"
        assert "balance_owed" in payout_info, "Missing balance_owed in payout_info"
        
        print(f"✅ Payout info verified - Earned: ${payout_info.get('total_earned', 0):.2f}, Owed: ${payout_info.get('balance_owed', 0):.2f}")
    
    def test_analytics_sales_by_day(self):
        """Test that sales by day data is returned"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        store_id = stores[0].get("id")
        analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
        analytics = analytics_response.json()
        
        sales_by_day = analytics.get("sales_by_day", [])
        assert isinstance(sales_by_day, list), "sales_by_day should be a list"
        
        # If there are sales, verify structure
        if len(sales_by_day) > 0:
            first_day = sales_by_day[0]
            assert "date" in first_day, "Missing date in sales_by_day item"
            assert "amount" in first_day, "Missing amount in sales_by_day item"
        
        print(f"✅ Sales by day data verified - {len(sales_by_day)} days of data")
    
    def test_analytics_top_products(self):
        """Test that top products data is returned"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        store_id = stores[0].get("id")
        analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
        analytics = analytics_response.json()
        
        top_products = analytics.get("top_products", [])
        assert isinstance(top_products, list), "top_products should be a list"
        
        # If there are products, verify structure
        if len(top_products) > 0:
            first_product = top_products[0]
            assert "product_id" in first_product, "Missing product_id in top_products item"
            assert "name" in first_product, "Missing name in top_products item"
            assert "quantity" in first_product, "Missing quantity in top_products item"
            assert "revenue" in first_product, "Missing revenue in top_products item"
        
        print(f"✅ Top products data verified - {len(top_products)} products")
    
    def test_fundraiser_store_analytics(self):
        """Test analytics for fundraiser stores include fundraiser metrics"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        # Find a fundraiser store
        fundraiser_stores = [s for s in stores if s.get("store_type") == "fundraiser"]
        
        if len(fundraiser_stores) == 0:
            pytest.skip("No fundraiser stores available for testing")
        
        store = fundraiser_stores[0]
        store_id = store.get("id")
        
        analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
        assert analytics_response.status_code == 200
        analytics = analytics_response.json()
        
        # Fundraiser stores should have fundraiser_metrics
        fundraiser_metrics = analytics.get("fundraiser_metrics")
        assert fundraiser_metrics is not None, "Fundraiser store should have fundraiser_metrics"
        
        assert "goal" in fundraiser_metrics, "Missing goal in fundraiser_metrics"
        assert "raised" in fundraiser_metrics, "Missing raised in fundraiser_metrics"
        assert "progress_percent" in fundraiser_metrics, "Missing progress_percent in fundraiser_metrics"
        assert "profit_percent" in fundraiser_metrics, "Missing profit_percent in fundraiser_metrics"
        
        print(f"✅ Fundraiser metrics verified - Goal: ${fundraiser_metrics.get('goal', 0):.2f}, Progress: {fundraiser_metrics.get('progress_percent', 0):.1f}%")
    
    def test_get_webstore_orders(self):
        """Test getting orders for a webstore"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        store_id = stores[0].get("id")
        
        # Get orders filtered by webstore
        orders_response = self.session.get(f"{BASE_URL}/api/webstores/v2/orders", params={"webstore_id": store_id})
        assert orders_response.status_code == 200
        orders = orders_response.json()
        assert isinstance(orders, list)
        
        print(f"✅ Got {len(orders)} orders for store")
        return orders
    
    def test_get_webstore_payouts(self):
        """Test getting payouts for a webstore"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        store_id = stores[0].get("id")
        
        payouts_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/payouts")
        assert payouts_response.status_code == 200
        payouts = payouts_response.json()
        assert isinstance(payouts, list)
        
        print(f"✅ Got {len(payouts)} payouts for store")
        return payouts
    
    def test_analytics_for_store_with_orders(self):
        """Test analytics for Lincoln High School store which has orders"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        # Find Lincoln High School store
        lincoln_stores = [s for s in stores if "Lincoln" in s.get("name", "")]
        
        if len(lincoln_stores) == 0:
            pytest.skip("Lincoln High School store not found")
        
        store = lincoln_stores[0]
        store_id = store.get("id")
        
        analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
        assert analytics_response.status_code == 200
        analytics = analytics_response.json()
        
        summary = analytics.get("summary", {})
        
        # Lincoln High School should have orders
        print(f"✅ Lincoln High School analytics - Orders: {summary.get('total_orders', 0)}, Revenue: ${summary.get('total_revenue', 0):.2f}")
        
        return analytics
    
    def test_webstore_detail_endpoint(self):
        """Test getting individual webstore details"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        if len(stores) == 0:
            pytest.skip("No webstores available for testing")
        
        store_id = stores[0].get("id")
        
        detail_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}")
        assert detail_response.status_code == 200
        store = detail_response.json()
        
        assert "id" in store
        assert "name" in store
        assert "store_type" in store
        assert "owner_name" in store
        
        print(f"✅ Store detail endpoint working - {store.get('name')}")
    
    def test_analytics_invalid_store_id(self):
        """Test analytics endpoint with invalid store ID returns 404"""
        response = self.session.get(f"{BASE_URL}/api/webstores/v2/invalid-store-id/analytics")
        assert response.status_code == 404
        print("✅ Invalid store ID returns 404 as expected")
    
    def test_all_webstores_have_analytics(self):
        """Test that all webstores can return analytics"""
        stores_response = self.session.get(f"{BASE_URL}/api/webstores/v2")
        stores = stores_response.json()
        
        for store in stores:
            store_id = store.get("id")
            analytics_response = self.session.get(f"{BASE_URL}/api/webstores/v2/{store_id}/analytics")
            assert analytics_response.status_code == 200, f"Analytics failed for store {store.get('name')}"
        
        print(f"✅ All {len(stores)} webstores return valid analytics")


class TestPreviousFeatures:
    """Test that previously implemented features still work"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as owner
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_rbac_owner_permissions(self):
        """Test that owner still has all permissions"""
        response = self.session.get(f"{BASE_URL}/api/users/me/permissions")
        assert response.status_code == 200
        data = response.json()
        assert data.get("role") == "owner"
        assert len(data.get("permissions", [])) >= 30  # Owner should have many permissions
        print(f"✅ Owner has {len(data.get('permissions', []))} permissions")
    
    def test_multi_tenancy_customers(self):
        """Test that customers endpoint still works with multi-tenancy"""
        response = self.session.get(f"{BASE_URL}/api/customers")
        assert response.status_code == 200
        customers = response.json()
        assert isinstance(customers, list)
        print(f"✅ Multi-tenancy working - Got {len(customers)} customers")
    
    def test_jobs_endpoint(self):
        """Test that jobs endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/jobs")
        assert response.status_code == 200
        jobs = response.json()
        assert isinstance(jobs, list)
        print(f"✅ Jobs endpoint working - Got {len(jobs)} jobs")
    
    def test_products_endpoint(self):
        """Test that products endpoint still works"""
        response = self.session.get(f"{BASE_URL}/api/products")
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        print(f"✅ Products endpoint working - Got {len(products)} products")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
