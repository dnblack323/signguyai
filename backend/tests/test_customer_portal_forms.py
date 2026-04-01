"""
Test Customer Portal Forms / Questionnaires - Iteration 60

Tests for:
- Portal forms navigation and listing
- Portal form detail with questionnaire
- Portal form submission creating customer_form document
- Admin portal form sending/monitoring
- Portal dashboard enriched widgets
- Portal order detail enriched sections
- Portal proof version history
- Portal invoice PDF download
- No regression on existing portal features
"""

import pytest
import requests
import os
import time
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review request
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD
PORTAL_CUSTOMER_EMAIL = "portal1773603307@example.com"
PORTAL_CUSTOMER_PASSWORD = LEGACY_ADMIN_PASSWORD


class TestPortalAuth:
    """Test portal login works"""
    
    def test_portal_login(self, api_client):
        """Login to customer portal"""
        response = api_client.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": PORTAL_CUSTOMER_EMAIL,
            "password": PORTAL_CUSTOMER_PASSWORD
        })
        print(f"Portal login status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Portal login response keys: {data.keys()}")
            assert "access_token" in data
            assert "customer_id" in data
            return data
        else:
            print(f"Portal login error: {response.text}")
        assert response.status_code == 200


class TestPortalDashboard:
    """Test enriched portal dashboard"""
    
    def test_portal_dashboard_returns_enriched_stats(self, portal_token, api_client):
        """GET /api/portal/dashboard returns pending_forms, recent_documents, awaiting_approval"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        response = api_client.get(f"{BASE_URL}/api/portal/dashboard")
        print(f"Dashboard response status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        print(f"Dashboard response keys: {data.keys()}")
        
        # Verify stats object exists with expected fields
        assert "stats" in data
        stats = data["stats"]
        assert "pending_forms" in stats, "pending_forms missing from stats"
        assert "recent_documents" in stats, "recent_documents (unread docs count) missing from stats"
        print(f"Stats: pending_forms={stats.get('pending_forms')}, recent_documents={stats.get('recent_documents')}")
        
        # Verify new widget data arrays exist
        assert "pending_forms" in data, "pending_forms array missing from dashboard"
        assert "awaiting_approval" in data, "awaiting_approval array missing from dashboard"
        assert "recent_documents" in data, "recent_documents array missing from dashboard"
        
        print(f"Dashboard pending_forms count: {len(data.get('pending_forms', []))}")
        print(f"Dashboard awaiting_approval count: {len(data.get('awaiting_approval', []))}")
        print(f"Dashboard recent_documents count: {len(data.get('recent_documents', []))}")


class TestPortalForms:
    """Test portal forms / questionnaires"""
    
    def test_portal_forms_list(self, portal_token, api_client):
        """GET /api/portal/forms lists form requests for customer"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        response = api_client.get(f"{BASE_URL}/api/portal/forms")
        print(f"Portal forms list status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Portal forms should return a list"
        print(f"Portal forms count: {len(data)}")
        
        if len(data) > 0:
            form = data[0]
            print(f"First form keys: {form.keys()}")
            # Verify expected fields
            assert "id" in form
            assert "questionnaire_name" in form or "questionnaire_id" in form
            assert "status" in form
            print(f"Form: id={form.get('id')[:8]}, status={form.get('status')}, name={form.get('questionnaire_name')}")
        
        return data
    
    def test_portal_forms_filter_by_status(self, portal_token, api_client):
        """GET /api/portal/forms?status=pending filters correctly"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        response = api_client.get(f"{BASE_URL}/api/portal/forms?status=pending")
        print(f"Portal forms (pending) status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        print(f"Pending forms count: {len(data)}")
        
        # All returned should be pending
        for form in data:
            assert form.get("status") in ["pending", "in_progress", "overdue"], f"Got status {form.get('status')}"
    
    def test_portal_form_detail(self, portal_token, api_client):
        """GET /api/portal/forms/{request_id} returns request + questionnaire"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        
        # First get list of forms
        list_response = api_client.get(f"{BASE_URL}/api/portal/forms")
        if list_response.status_code != 200:
            pytest.skip("No forms available to test detail")
        
        forms = list_response.json()
        if len(forms) == 0:
            pytest.skip("No forms available to test detail")
        
        form_id = forms[0]["id"]
        response = api_client.get(f"{BASE_URL}/api/portal/forms/{form_id}")
        print(f"Portal form detail status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        print(f"Form detail keys: {data.keys()}")
        
        # Verify structure
        assert "request" in data, "Form detail should have 'request'"
        assert "questionnaire" in data, "Form detail should have 'questionnaire'"
        
        request = data["request"]
        questionnaire = data["questionnaire"]
        print(f"Request status: {request.get('status')}, opened_at: {request.get('opened_at')}")
        print(f"Questionnaire name: {questionnaire.get('name')}, questions count: {len(questionnaire.get('questions', []))}")
        
        # The form should be marked as opened (in_progress) after viewing
        if request.get("status") in ["pending", "in_progress"]:
            assert request.get("opened_at") is not None, "Form should have opened_at after viewing"


class TestPortalFormSubmission:
    """Test form submission flow"""
    
    def test_portal_form_submit(self, portal_token, api_client):
        """POST /api/portal/forms/{request_id}/submit saves response and creates document"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        
        # Get pending forms
        list_response = api_client.get(f"{BASE_URL}/api/portal/forms?status=pending")
        if list_response.status_code != 200:
            pytest.skip("Could not fetch forms")
        
        forms = list_response.json()
        pending_forms = [f for f in forms if f.get("status") in ["pending", "in_progress"]]
        
        if len(pending_forms) == 0:
            print("No pending forms to submit - checking if any completed forms exist")
            all_forms = api_client.get(f"{BASE_URL}/api/portal/forms").json()
            print(f"Total forms: {len(all_forms)}")
            pytest.skip("No pending forms available to test submission")
        
        form_request = pending_forms[0]
        form_id = form_request["id"]
        
        # Get form detail to see questions
        detail_response = api_client.get(f"{BASE_URL}/api/portal/forms/{form_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        
        questionnaire = detail.get("questionnaire", {})
        questions = questionnaire.get("questions", [])
        
        # Build minimal valid answers
        answers = {}
        for q in questions:
            q_type = q.get("type", "text")
            if q_type in ["heading", "paragraph"]:
                continue
            q_id = q.get("id")
            if q.get("required"):
                if q_type in ["checkbox", "multi_select"]:
                    if q.get("options") and len(q.get("options")) > 0:
                        answers[q_id] = [q.get("options")[0]["value"]]
                    else:
                        answers[q_id] = []
                elif q_type in ["select", "radio"]:
                    if q.get("options") and len(q.get("options")) > 0:
                        answers[q_id] = q.get("options")[0]["value"]
                    else:
                        answers[q_id] = ""
                else:
                    answers[q_id] = "Test answer from automated testing"
            else:
                answers[q_id] = "" if q_type not in ["checkbox", "multi_select"] else []
        
        print(f"Submitting form {form_id} with {len(answers)} answers")
        
        response = api_client.post(f"{BASE_URL}/api/portal/forms/{form_id}/submit", json={
            "answers": answers
        })
        print(f"Form submit status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Submit error: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        print(f"Submit response: {data}")
        
        # Verify response has expected fields
        assert "message" in data, "Response should have thank you message"
        assert "response_id" in data, "Response should have response_id"
        assert "document_id" in data, "Response should create customer_form document"


class TestAdminPortalForms:
    """Test admin portal form sending/monitoring"""
    
    def test_admin_get_form_requests(self, admin_token, api_client):
        """GET /api/admin-portal/forms returns sent requests with customer/job context"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin-portal/forms")
        print(f"Admin forms list status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Admin forms should return a list"
        print(f"Admin forms count: {len(data)}")
        
        if len(data) > 0:
            form = data[0]
            print(f"Form keys: {form.keys()}")
            # Should have customer context
            assert "customer" in form or "customer_id" in form
            print(f"Form: {form.get('questionnaire_name')}, status={form.get('status')}, customer={form.get('customer')}")
    
    def test_admin_send_form_request(self, admin_token, api_client):
        """POST /api/admin-portal/forms/send can send a questionnaire request"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        
        # Get available questionnaires
        q_response = api_client.get(f"{BASE_URL}/api/questionnaires")
        if q_response.status_code != 200:
            pytest.skip("Could not fetch questionnaires")
        
        questionnaires = q_response.json()
        active_questionnaires = [q for q in questionnaires if q.get("status") == "active"]
        
        if len(active_questionnaires) == 0:
            print("No active questionnaires - cannot test send form")
            pytest.skip("No active questionnaires available")
        
        questionnaire_id = active_questionnaires[0]["id"]
        
        # Get portal customer
        c_response = api_client.get(f"{BASE_URL}/api/customers?search={PORTAL_CUSTOMER_EMAIL}")
        if c_response.status_code != 200 or len(c_response.json()) == 0:
            # Try getting customers list directly
            c_response = api_client.get(f"{BASE_URL}/api/admin-portal/customers?portal_enabled_only=true")
            if c_response.status_code != 200 or len(c_response.json()) == 0:
                pytest.skip("Could not find portal customer")
        
        customers = c_response.json()
        customer_id = customers[0]["id"]
        
        response = api_client.post(f"{BASE_URL}/api/admin-portal/forms/send", json={
            "customer_id": customer_id,
            "questionnaire_id": questionnaire_id,
            "instructions": "Test form from automated testing",
            "due_date": "2026-02-01"
        })
        print(f"Admin send form status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Send form error: {response.text}")
        
        # Could be 200 or 201
        assert response.status_code in [200, 201]
        data = response.json()
        print(f"Send form response: {data}")
        assert "id" in data, "Response should have form request id"


class TestPortalOrderDetail:
    """Test enriched portal order detail"""
    
    def test_portal_order_detail_enriched_sections(self, portal_token, api_client):
        """GET /api/portal/orders/{job_id} returns forms/messages/documents/invoice/timeline"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        
        # First get orders list
        orders_response = api_client.get(f"{BASE_URL}/api/portal/orders")
        if orders_response.status_code != 200:
            pytest.skip("Could not fetch orders")
        
        orders = orders_response.json()
        if len(orders) == 0:
            pytest.skip("No orders available to test")
        
        order_id = orders[0]["id"]
        response = api_client.get(f"{BASE_URL}/api/portal/orders/{order_id}")
        print(f"Order detail status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        print(f"Order detail keys: {data.keys()}")
        
        # Verify enriched sections exist
        assert "customer_status_timeline" in data, "Order detail should have customer_status_timeline"
        assert "forms" in data, "Order detail should have forms section"
        assert "conversations" in data or "messages" in data, "Order detail should have conversations/messages"
        assert "documents" in data, "Order detail should have documents section"
        
        timeline = data.get("customer_status_timeline", [])
        print(f"Status timeline steps: {len(timeline)}")
        if len(timeline) > 0:
            print(f"Timeline sample: {timeline[0]}")
        
        print(f"Forms linked: {len(data.get('forms', []))}")
        print(f"Documents linked: {len(data.get('documents', []))}")


class TestPortalProofVersionHistory:
    """Test portal proof version history"""
    
    def test_portal_proof_detail_has_version_history(self, portal_token, api_client):
        """GET /api/portal/proofs/{proof_id} returns version_history"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        
        # Get proofs list
        proofs_response = api_client.get(f"{BASE_URL}/api/portal/proofs")
        if proofs_response.status_code != 200:
            pytest.skip("Could not fetch proofs")
        
        proofs = proofs_response.json()
        if len(proofs) == 0:
            pytest.skip("No proofs available to test")
        
        proof_id = proofs[0]["id"]
        response = api_client.get(f"{BASE_URL}/api/portal/proofs/{proof_id}")
        print(f"Proof detail status: {response.status_code}")
        
        assert response.status_code == 200
        data = response.json()
        print(f"Proof detail keys: {data.keys()}")
        
        # Verify version history exists
        assert "version_history" in data, "Proof detail should have version_history"
        history = data.get("version_history", [])
        print(f"Version history entries: {len(history)}")
        
        if len(history) > 0:
            entry = history[0]
            assert "version" in entry
            assert "status" in entry
            print(f"Version history sample: version={entry.get('version')}, status={entry.get('status')}")


class TestPortalInvoiceDownload:
    """Test portal invoice PDF download"""
    
    def test_portal_invoice_pdf_download(self, portal_token, api_client):
        """GET /api/portal/invoices/{invoice_id}/download returns PDF"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        
        # Get invoices list
        invoices_response = api_client.get(f"{BASE_URL}/api/portal/invoices")
        if invoices_response.status_code != 200:
            pytest.skip("Could not fetch invoices")
        
        invoices = invoices_response.json()
        if len(invoices) == 0:
            pytest.skip("No invoices available to test")
        
        invoice_id = invoices[0]["id"]
        response = api_client.get(f"{BASE_URL}/api/portal/invoices/{invoice_id}/download")
        print(f"Invoice download status: {response.status_code}")
        
        assert response.status_code == 200
        
        # Verify it's a PDF
        content_type = response.headers.get("content-type", "")
        print(f"Content-Type: {content_type}")
        assert "application/pdf" in content_type, "Response should be application/pdf"
        
        # Verify content-disposition for download
        content_disposition = response.headers.get("content-disposition", "")
        print(f"Content-Disposition: {content_disposition}")
        assert "attachment" in content_disposition.lower() or "invoice" in content_disposition.lower()


class TestPortalRegressions:
    """Test no regression on existing portal features"""
    
    def test_portal_messages(self, portal_token, api_client):
        """GET /api/portal/conversations works"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        response = api_client.get(f"{BASE_URL}/api/portal/conversations")
        print(f"Portal conversations status: {response.status_code}")
        assert response.status_code == 200
    
    def test_portal_documents(self, portal_token, api_client):
        """GET /api/portal/documents works"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        response = api_client.get(f"{BASE_URL}/api/portal/documents")
        print(f"Portal documents status: {response.status_code}")
        assert response.status_code == 200
    
    def test_portal_quotes(self, portal_token, api_client):
        """GET /api/portal/quotes works"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        response = api_client.get(f"{BASE_URL}/api/portal/quotes")
        print(f"Portal quotes status: {response.status_code}")
        assert response.status_code == 200
    
    def test_portal_profile(self, portal_token, api_client):
        """GET /api/portal/profile works"""
        api_client.headers.update({"Authorization": f"Bearer {portal_token}"})
        response = api_client.get(f"{BASE_URL}/api/portal/profile")
        print(f"Portal profile status: {response.status_code}")
        assert response.status_code == 200


class TestAdminPortalRegressions:
    """Test admin portal messaging and documents tabs"""
    
    def test_admin_portal_conversations(self, admin_token, api_client):
        """GET /api/admin-portal/conversations works"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin-portal/conversations")
        print(f"Admin conversations status: {response.status_code}")
        assert response.status_code == 200
    
    def test_admin_portal_documents(self, admin_token, api_client):
        """GET /api/admin-portal/documents works"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin-portal/documents")
        print(f"Admin documents status: {response.status_code}")
        assert response.status_code == 200
    
    def test_admin_portal_artwork_queue(self, admin_token, api_client):
        """GET /api/admin-portal/artwork-queue works"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin-portal/artwork-queue")
        print(f"Admin artwork queue status: {response.status_code}")
        assert response.status_code == 200
    
    def test_admin_portal_dashboard(self, admin_token, api_client):
        """GET /api/admin-portal/dashboard works"""
        api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
        response = api_client.get(f"{BASE_URL}/api/admin-portal/dashboard")
        print(f"Admin portal dashboard status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        # Verify forms section in dashboard
        assert "forms" in data, "Admin dashboard should have forms stats"
        print(f"Admin dashboard forms: {data.get('forms')}")


# ============== FIXTURES ==============

@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed - skipping admin tests")


@pytest.fixture
def portal_token(api_client):
    """Get portal customer authentication token"""
    response = api_client.post(f"{BASE_URL}/api/portal/auth/login", json={
        "email": PORTAL_CUSTOMER_EMAIL,
        "password": PORTAL_CUSTOMER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Portal authentication failed - skipping portal tests")
