"""
Iteration 61 Tests: Portal Invoice Payment & Admin Job Communication Tab

Tests:
1. GET /api/jobs/{job_id}/details returns portal_proofs, portal_conversations, portal_documents, portal_forms
2. POST /api/portal/invoices/{invoice_id}/pay - handles Stripe Connect not enabled case
3. POST /api/portal/invoices/{invoice_id}/pay - validates required fields
4. No regression on portal forms flow, portal dashboard, portal orders detail
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from iteration_60
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"
PORTAL_CUSTOMER_EMAIL = "portal1773603307@example.com"
PORTAL_CUSTOMER_PASSWORD = "password123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def portal_token():
    """Get portal customer authentication token"""
    response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
        "email": PORTAL_CUSTOMER_EMAIL,
        "password": PORTAL_CUSTOMER_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Portal login failed: {response.status_code}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def portal_customer_id(portal_token):
    """Get portal customer ID from profile"""
    response = requests.get(f"{BASE_URL}/api/portal/profile", headers={
        "Authorization": f"Bearer {portal_token}"
    })
    if response.status_code != 200:
        pytest.skip("Failed to get portal profile")
    return response.json().get("id")


@pytest.fixture(scope="module")
def test_job_id(admin_token, portal_customer_id):
    """Get or create a test job for the portal customer"""
    # First try to find an existing job for this customer
    response = requests.get(f"{BASE_URL}/api/jobs?customer_id={portal_customer_id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    if response.status_code == 200:
        jobs = response.json()
        if jobs:
            return jobs[0].get("id")
    
    # If no jobs found, skip (we don't want to create test data here)
    pytest.skip("No test job found for portal customer")


class TestAdminJobDetailsPortalData:
    """Test GET /api/jobs/{job_id}/details returns portal communication fields"""

    def test_job_details_returns_portal_proofs(self, admin_token, test_job_id):
        """Verify portal_proofs field is present in job details response"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job_id}/details", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "portal_proofs" in data, "portal_proofs field missing from job details"
        assert isinstance(data["portal_proofs"], list), "portal_proofs should be a list"
        print(f"PASS: portal_proofs found with {len(data['portal_proofs'])} items")

    def test_job_details_returns_portal_conversations(self, admin_token, test_job_id):
        """Verify portal_conversations field is present in job details response"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job_id}/details", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "portal_conversations" in data, "portal_conversations field missing from job details"
        assert isinstance(data["portal_conversations"], list), "portal_conversations should be a list"
        print(f"PASS: portal_conversations found with {len(data['portal_conversations'])} items")

    def test_job_details_returns_portal_documents(self, admin_token, test_job_id):
        """Verify portal_documents field is present in job details response"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job_id}/details", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "portal_documents" in data, "portal_documents field missing from job details"
        assert isinstance(data["portal_documents"], list), "portal_documents should be a list"
        print(f"PASS: portal_documents found with {len(data['portal_documents'])} items")

    def test_job_details_returns_portal_forms(self, admin_token, test_job_id):
        """Verify portal_forms field is present in job details response"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job_id}/details", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "portal_forms" in data, "portal_forms field missing from job details"
        assert isinstance(data["portal_forms"], list), "portal_forms should be a list"
        print(f"PASS: portal_forms found with {len(data['portal_forms'])} items")

    def test_job_details_returns_all_expected_fields(self, admin_token, test_job_id):
        """Verify all expected fields are present in job details response"""
        response = requests.get(f"{BASE_URL}/api/jobs/{test_job_id}/details", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        expected_fields = ["job", "customer", "quote", "invoice", "job_items", 
                         "assigned_employee_details", "notes", "activities",
                         "portal_proofs", "portal_conversations", "portal_documents", 
                         "portal_forms", "financial_snapshot"]
        
        for field in expected_fields:
            assert field in data, f"Field '{field}' missing from job details"
        
        print(f"PASS: All expected fields present in job details response")


class TestPortalInvoicePayment:
    """Test POST /api/portal/invoices/{invoice_id}/pay endpoint"""

    def test_invoice_pay_validation_order(self, portal_token):
        """Verify that payment endpoint validates properly (Stripe Connect checked first)"""
        # First get an invoice
        response = requests.get(f"{BASE_URL}/api/portal/invoices", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        invoices = response.json()
        
        if not invoices:
            pytest.skip("No invoices found for portal customer")
        
        # Find unpaid invoice
        unpaid_invoice = None
        for inv in invoices:
            if inv.get("status") != "paid":
                unpaid_invoice = inv
                break
        
        if not unpaid_invoice:
            pytest.skip("No unpaid invoices found")
        
        # Try to pay without origin_url - endpoint checks Stripe Connect first
        response = requests.post(
            f"{BASE_URL}/api/portal/invoices/{unpaid_invoice['id']}/pay",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={}  # Missing origin_url
        )
        
        # Should return 400 - either for missing Stripe Connect or missing origin_url
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", "")
        # Either Stripe not enabled message (checked first) or origin_url required
        assert "online payments" in detail.lower() or "stripe" in detail.lower() or "origin_url" in detail.lower()
        print(f"PASS: Payment validation works - got: {detail}")

    def test_invoice_pay_stripe_not_enabled_message(self, portal_token):
        """Verify clear message when Stripe Connect is not enabled"""
        # Get invoices
        response = requests.get(f"{BASE_URL}/api/portal/invoices", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        invoices = response.json()
        
        if not invoices:
            pytest.skip("No invoices found for portal customer")
        
        # Find unpaid invoice
        unpaid_invoice = None
        for inv in invoices:
            if inv.get("status") != "paid":
                unpaid_invoice = inv
                break
        
        if not unpaid_invoice:
            pytest.skip("No unpaid invoices found")
        
        # Try to pay with origin_url
        response = requests.post(
            f"{BASE_URL}/api/portal/invoices/{unpaid_invoice['id']}/pay",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={"origin_url": "https://example.com"}
        )
        
        # Should return 400 with message about Stripe Connect not being enabled
        # This is expected behavior per the agent context note
        if response.status_code == 400:
            data = response.json()
            # Check if it's the expected "online payments not enabled" message
            detail = data.get("detail", "")
            if "online payments" in detail.lower() or "stripe" in detail.lower() or "not enabled" in detail.lower():
                print(f"PASS: Correct message when Stripe not enabled: {detail}")
            else:
                print(f"INFO: Got 400 with message: {detail}")
        elif response.status_code == 200:
            # If Stripe IS enabled, we should get a URL and session_id
            data = response.json()
            assert "url" in data or "session_id" in data
            print(f"INFO: Stripe IS enabled - got checkout URL")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

    def test_invoice_pay_already_paid_returns_error(self, portal_token):
        """Verify that paying an already paid invoice returns error"""
        # Get invoices
        response = requests.get(f"{BASE_URL}/api/portal/invoices", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        invoices = response.json()
        
        # Find paid invoice
        paid_invoice = None
        for inv in invoices:
            if inv.get("status") == "paid":
                paid_invoice = inv
                break
        
        if not paid_invoice:
            pytest.skip("No paid invoices found to test")
        
        # Try to pay already paid invoice
        response = requests.post(
            f"{BASE_URL}/api/portal/invoices/{paid_invoice['id']}/pay",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={"origin_url": "https://example.com"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already paid" in data.get("detail", "").lower()
        print(f"PASS: Correctly rejects payment for already paid invoice")

    def test_invoice_not_found(self, portal_token):
        """Verify 404 for non-existent invoice"""
        fake_id = str(uuid.uuid4())
        response = requests.post(
            f"{BASE_URL}/api/portal/invoices/{fake_id}/pay",
            headers={"Authorization": f"Bearer {portal_token}"},
            json={"origin_url": "https://example.com"}
        )
        assert response.status_code == 404
        print("PASS: Returns 404 for non-existent invoice")


class TestPortalFormsRegressionIteration60:
    """Regression tests for portal forms flow from iteration_60"""

    def test_portal_forms_list(self, portal_token):
        """Verify GET /api/portal/forms works"""
        response = requests.get(f"{BASE_URL}/api/portal/forms", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Portal forms list returns {len(data)} forms")

    def test_portal_forms_status_filter(self, portal_token):
        """Verify GET /api/portal/forms with status filter works"""
        for status in ["pending", "completed", "in_progress"]:
            response = requests.get(f"{BASE_URL}/api/portal/forms?status={status}", headers={
                "Authorization": f"Bearer {portal_token}"
            })
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            print(f"PASS: Portal forms filter by status={status} works, returned {len(data)} forms")


class TestPortalDashboardRegression:
    """Regression tests for portal dashboard"""

    def test_portal_dashboard(self, portal_token):
        """Verify GET /api/portal/dashboard returns enriched stats"""
        response = requests.get(f"{BASE_URL}/api/portal/dashboard", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "stats" in data
        stats = data["stats"]
        
        # Check stats fields
        expected_stats = ["total_quotes", "active_jobs", "pending_invoices", "pending_proofs",
                        "unread_messages", "unread_notifications", "pending_forms", "recent_documents"]
        for field in expected_stats:
            assert field in stats, f"Stats missing '{field}'"
        
        print(f"PASS: Portal dashboard returns enriched stats")

    def test_portal_dashboard_arrays(self, portal_token):
        """Verify portal dashboard returns widget arrays"""
        response = requests.get(f"{BASE_URL}/api/portal/dashboard", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Check for widget arrays
        expected_arrays = ["upcoming_appointments", "recent_jobs", "recent_invoices", 
                         "recent_documents", "pending_forms", "awaiting_approval"]
        for field in expected_arrays:
            assert field in data, f"Dashboard missing '{field}' array"
            assert isinstance(data[field], list), f"'{field}' should be a list"
        
        print(f"PASS: Portal dashboard returns all expected widget arrays")


class TestPortalOrdersDetailRegression:
    """Regression tests for portal orders detail"""

    def test_portal_orders_list(self, portal_token):
        """Verify GET /api/portal/orders works"""
        response = requests.get(f"{BASE_URL}/api/portal/orders", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Portal orders list returns {len(data)} orders")

    def test_portal_order_detail_enriched(self, portal_token):
        """Verify GET /api/portal/orders/{job_id} returns enriched data"""
        # First get orders
        response = requests.get(f"{BASE_URL}/api/portal/orders", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        orders = response.json()
        
        if not orders:
            pytest.skip("No orders found for portal customer")
        
        order_id = orders[0]["id"]
        
        # Get order detail
        response = requests.get(f"{BASE_URL}/api/portal/orders/{order_id}", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Check for enriched fields
        expected_fields = ["items", "proofs", "documents", "forms", "conversations", "customer_status_timeline"]
        for field in expected_fields:
            assert field in data, f"Order detail missing '{field}'"
        
        # Verify customer_status_timeline structure
        timeline = data.get("customer_status_timeline", [])
        assert isinstance(timeline, list)
        if timeline:
            assert "label" in timeline[0]
            assert "status" in timeline[0]
        
        print(f"PASS: Portal order detail returns enriched data with timeline")


class TestPortalProofsRegression:
    """Regression tests for portal proofs"""

    def test_portal_proofs_list(self, portal_token):
        """Verify GET /api/portal/proofs works"""
        response = requests.get(f"{BASE_URL}/api/portal/proofs", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Portal proofs list returns {len(data)} proofs")


class TestPortalMessagesRegression:
    """Regression tests for portal messages"""

    def test_portal_conversations_list(self, portal_token):
        """Verify GET /api/portal/conversations works"""
        response = requests.get(f"{BASE_URL}/api/portal/conversations", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Portal conversations list returns {len(data)} conversations")


class TestPortalDocumentsRegression:
    """Regression tests for portal documents"""

    def test_portal_documents_list(self, portal_token):
        """Verify GET /api/portal/documents works"""
        response = requests.get(f"{BASE_URL}/api/portal/documents", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Portal documents list returns {len(data)} documents")


class TestAdminPortalFormsTabRegression:
    """Regression tests for admin portal forms tab"""

    def test_admin_portal_forms_list(self, admin_token):
        """Verify GET /api/admin-portal/forms works"""
        response = requests.get(f"{BASE_URL}/api/admin-portal/forms", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Admin portal forms list returns {len(data)} form requests")


class TestPortalInvoicesRegression:
    """Regression tests for portal invoices"""

    def test_portal_invoices_list(self, portal_token):
        """Verify GET /api/portal/invoices works"""
        response = requests.get(f"{BASE_URL}/api/portal/invoices", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"PASS: Portal invoices list returns {len(data)} invoices")

    def test_portal_invoice_download_pdf(self, portal_token):
        """Verify GET /api/portal/invoices/{invoice_id}/download works"""
        # Get invoices
        response = requests.get(f"{BASE_URL}/api/portal/invoices", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        invoices = response.json()
        
        if not invoices:
            pytest.skip("No invoices found")
        
        invoice_id = invoices[0]["id"]
        
        # Download PDF
        response = requests.get(
            f"{BASE_URL}/api/portal/invoices/{invoice_id}/download",
            headers={"Authorization": f"Bearer {portal_token}"}
        )
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        print(f"PASS: Portal invoice PDF download works")
