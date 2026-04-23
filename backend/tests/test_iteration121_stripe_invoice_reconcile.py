"""
Test Suite for Iteration 121: Stripe Invoice Reconciliation & Tenant Dashboard

Tests:
1. POST /api/stripe-connect/reconcile-invoices - Invoice status reconciliation
2. GET /api/stripe-connect/tenant-dashboard - Tenant Stripe operations dashboard
3. GET /api/stripe-connect/payment-status/{session_id} - Payment status fallback
4. GET /api/stripe-connect/status - Stripe Connect status check
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestStripeConnectReconciliation:
    """Tests for Stripe Connect invoice reconciliation and tenant dashboard"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
        # Authenticate
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("access_token") or data.get("token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        self.session.close()
    
    def test_auth_login_success(self):
        """Verify authentication works with test credentials"""
        assert self.token is not None, "Authentication failed - no token received"
        print(f"✓ Authentication successful, token received")
    
    def test_stripe_connect_status_endpoint(self):
        """Test GET /api/stripe-connect/status returns valid structure"""
        if not self.token:
            pytest.skip("Authentication required")
        
        response = self.session.get(f"{BASE_URL}/api/stripe-connect/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "connected" in data, "Response missing 'connected' field"
        assert "stripe_mode" in data, "Response missing 'stripe_mode' field"
        assert "platform_fee_percent" in data, "Response missing 'platform_fee_percent' field"
        
        # Verify data types
        assert isinstance(data["connected"], bool), "'connected' should be boolean"
        assert data["stripe_mode"] in ["test", "live"], f"Invalid stripe_mode: {data['stripe_mode']}"
        assert isinstance(data["platform_fee_percent"], (int, float)), "'platform_fee_percent' should be numeric"
        
        print(f"✓ Stripe Connect status: connected={data['connected']}, mode={data['stripe_mode']}")
        
        if data["connected"]:
            # Additional fields when connected
            assert "charges_enabled" in data, "Connected account missing 'charges_enabled'"
            assert "payouts_enabled" in data, "Connected account missing 'payouts_enabled'"
            assert "onboarding_complete" in data, "Connected account missing 'onboarding_complete'"
            print(f"  charges_enabled={data['charges_enabled']}, payouts_enabled={data['payouts_enabled']}")
    
    def test_reconcile_invoices_endpoint(self):
        """Test POST /api/stripe-connect/reconcile-invoices runs successfully"""
        if not self.token:
            pytest.skip("Authentication required")
        
        response = self.session.post(f"{BASE_URL}/api/stripe-connect/reconcile-invoices")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "checked_paid_transactions" in data, "Response missing 'checked_paid_transactions'"
        assert "fixed_invoices" in data, "Response missing 'fixed_invoices'"
        
        # Verify data types
        assert isinstance(data["checked_paid_transactions"], int), "'checked_paid_transactions' should be int"
        assert isinstance(data["fixed_invoices"], int), "'fixed_invoices' should be int"
        
        # Values should be non-negative
        assert data["checked_paid_transactions"] >= 0, "checked_paid_transactions should be >= 0"
        assert data["fixed_invoices"] >= 0, "fixed_invoices should be >= 0"
        
        print(f"✓ Reconcile invoices: checked={data['checked_paid_transactions']}, fixed={data['fixed_invoices']}")
    
    def test_tenant_dashboard_endpoint(self):
        """Test GET /api/stripe-connect/tenant-dashboard returns valid structure"""
        if not self.token:
            pytest.skip("Authentication required")
        
        response = self.session.get(f"{BASE_URL}/api/stripe-connect/tenant-dashboard")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify core response structure
        assert "connected" in data, "Response missing 'connected' field"
        assert "generated_at" in data, "Response missing 'generated_at' field"
        assert "payments_summary" in data, "Response missing 'payments_summary' field"
        assert "recent_payments" in data, "Response missing 'recent_payments' field"
        
        # Verify payments_summary structure
        payments_summary = data["payments_summary"]
        assert "paid_count" in payments_summary, "payments_summary missing 'paid_count'"
        assert "pending_count" in payments_summary, "payments_summary missing 'pending_count'"
        assert "failed_count" in payments_summary, "payments_summary missing 'failed_count'"
        assert "paid_total" in payments_summary, "payments_summary missing 'paid_total'"
        assert "pending_total" in payments_summary, "payments_summary missing 'pending_total'"
        
        print(f"✓ Tenant dashboard: connected={data['connected']}")
        print(f"  payments_summary: paid_count={payments_summary['paid_count']}, paid_total=${payments_summary['paid_total']}")
        
        if data["connected"]:
            # Additional fields when connected
            assert "stripe_account_id" in data, "Connected dashboard missing 'stripe_account_id'"
            assert "connect_status" in data, "Connected dashboard missing 'connect_status'"
            assert "balances" in data, "Connected dashboard missing 'balances'"
            assert "recent_payouts" in data, "Connected dashboard missing 'recent_payouts'"
            assert "recent_disputes" in data, "Connected dashboard missing 'recent_disputes'"
            assert "recent_events" in data, "Connected dashboard missing 'recent_events'"
            assert "recent_failed_payments" in data, "Connected dashboard missing 'recent_failed_payments'"
            
            # Verify balances structure
            balances = data["balances"]
            assert "available_usd" in balances, "balances missing 'available_usd'"
            assert "pending_usd" in balances, "balances missing 'pending_usd'"
            
            print(f"  balances: available=${balances['available_usd']}, pending=${balances['pending_usd']}")
            print(f"  recent_payments count: {len(data['recent_payments'])}")
            print(f"  recent_payouts count: {len(data['recent_payouts'])}")
            print(f"  recent_events count: {len(data['recent_events'])}")
            
            # Verify payouts_summary if present
            if "payouts_summary" in data:
                payouts_summary = data["payouts_summary"]
                assert "count" in payouts_summary, "payouts_summary missing 'count'"
                assert "total" in payouts_summary, "payouts_summary missing 'total'"
                print(f"  payouts_summary: count={payouts_summary['count']}, total=${payouts_summary['total']}")
    
    def test_tenant_dashboard_recent_payments_structure(self):
        """Test that recent_payments in tenant dashboard have correct structure"""
        if not self.token:
            pytest.skip("Authentication required")
        
        response = self.session.get(f"{BASE_URL}/api/stripe-connect/tenant-dashboard")
        
        assert response.status_code == 200
        
        data = response.json()
        recent_payments = data.get("recent_payments", [])
        
        if len(recent_payments) > 0:
            payment = recent_payments[0]
            
            # Verify payment structure
            assert "session_id" in payment, "Payment missing 'session_id'"
            assert "type" in payment, "Payment missing 'type'"
            assert "status" in payment, "Payment missing 'status'"
            assert "amount" in payment, "Payment missing 'amount'"
            assert "currency" in payment, "Payment missing 'currency'"
            assert "created_at" in payment, "Payment missing 'created_at'"
            
            print(f"✓ Recent payment structure verified: {len(recent_payments)} payments")
            print(f"  Sample: session_id={payment['session_id'][:20]}..., status={payment['status']}, amount=${payment['amount']}")
        else:
            print("✓ No recent payments to verify structure (empty list is valid)")
    
    def test_payment_status_endpoint_invalid_session(self):
        """Test GET /api/stripe-connect/payment-status/{session_id} with invalid session"""
        # This endpoint is public (no auth required)
        session = requests.Session()
        
        # Test with a fake session ID - should return 400 from Stripe
        fake_session_id = "cs_test_invalid_session_12345"
        
        response = session.get(f"{BASE_URL}/api/stripe-connect/payment-status/{fake_session_id}")
        
        # Should return 400 because Stripe will reject invalid session
        assert response.status_code == 400, f"Expected 400 for invalid session, got {response.status_code}"
        
        print(f"✓ Payment status correctly rejects invalid session ID")
        session.close()
    
    def test_reconcile_invoices_requires_auth(self):
        """Test that reconcile-invoices endpoint requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/stripe-connect/reconcile-invoices")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print(f"✓ Reconcile invoices correctly requires authentication")
        session.close()
    
    def test_tenant_dashboard_requires_auth(self):
        """Test that tenant-dashboard endpoint requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/stripe-connect/tenant-dashboard")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print(f"✓ Tenant dashboard correctly requires authentication")
        session.close()
    
    def test_stripe_connect_status_requires_auth(self):
        """Test that stripe-connect/status endpoint requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.get(f"{BASE_URL}/api/stripe-connect/status")
        
        # Should return 401 or 403 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print(f"✓ Stripe connect status correctly requires authentication")
        session.close()


class TestInvoicesPageIntegration:
    """Tests for invoice page integration with Stripe reconciliation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        
        # Authenticate
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            self.token = data.get("access_token") or data.get("token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        yield
        
        self.session.close()
    
    def test_invoices_list_endpoint(self):
        """Test GET /api/invoices returns valid list"""
        if not self.token:
            pytest.skip("Authentication required")
        
        response = self.session.get(f"{BASE_URL}/api/invoices")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Invoices response should be a list"
        
        print(f"✓ Invoices list: {len(data)} invoices found")
        
        if len(data) > 0:
            invoice = data[0]
            # Verify invoice structure
            assert "id" in invoice, "Invoice missing 'id'"
            assert "status" in invoice, "Invoice missing 'status'"
            print(f"  Sample invoice: id={invoice['id'][:8]}..., status={invoice['status']}")
    
    def test_reconcile_then_fetch_invoices(self):
        """Test that reconcile followed by fetch invoices works correctly"""
        if not self.token:
            pytest.skip("Authentication required")
        
        # First reconcile
        reconcile_response = self.session.post(f"{BASE_URL}/api/stripe-connect/reconcile-invoices")
        assert reconcile_response.status_code == 200, f"Reconcile failed: {reconcile_response.text}"
        
        reconcile_data = reconcile_response.json()
        print(f"✓ Reconcile completed: checked={reconcile_data['checked_paid_transactions']}, fixed={reconcile_data['fixed_invoices']}")
        
        # Then fetch invoices
        invoices_response = self.session.get(f"{BASE_URL}/api/invoices")
        assert invoices_response.status_code == 200, f"Invoices fetch failed: {invoices_response.text}"
        
        invoices = invoices_response.json()
        print(f"✓ Invoices fetched after reconcile: {len(invoices)} invoices")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
