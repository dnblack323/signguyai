"""
Section 1 Prelaunch Checklist Backend Tests

Tests for:
- 1.1B: Backup export size > 50KB
- 1.1C: Backup includes legacy keys (orders, order_items, payroll_transactions, timeclock_shifts)
- 1.3A: Billing subscription returns plan + renewal/trial date field
- 1.6D: Empty customer import returns clear error
- 1.6K-1.6O: Customer search supports various phone formats including + prefixed
- 1.6P: Invalid email row is skipped with error while valid row imports
"""

import pytest
import requests
import os
import json
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


class TestSection1Prelaunch:
    """Section 1 Prelaunch Checklist Tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for owner account"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        if not token:
            pytest.skip("No token in auth response")
        return token
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    # ==================== 1.1 Backup & Restore Tests ====================
    
    def test_1_1B_backup_export_size_exceeds_50kb(self, auth_headers):
        """1.1B: Backup export size now exceeds 50KB"""
        response = requests.get(
            f"{BASE_URL}/api/backup/export",
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200, f"Backup export failed: {response.status_code}"
        
        # Check size
        content_length = len(response.content)
        assert content_length > 50 * 1024, f"Backup size {content_length} bytes is not > 50KB"
        print(f"✅ 1.1B PASS: Backup size = {content_length} bytes (> 50KB)")
    
    def test_1_1C_backup_includes_legacy_keys(self, auth_headers):
        """1.1C: Backup export includes legacy keys orders, order_items, payroll_transactions, timeclock_shifts"""
        response = requests.get(
            f"{BASE_URL}/api/backup/export",
            headers=auth_headers,
            timeout=60
        )
        assert response.status_code == 200, f"Backup export failed: {response.status_code}"
        
        backup_data = response.json()
        collections = backup_data.get("collections", {})
        
        # Required legacy keys
        required_keys = ["orders", "order_items", "payroll_transactions", "timeclock_shifts"]
        missing_keys = [key for key in required_keys if key not in collections]
        
        assert len(missing_keys) == 0, f"Missing legacy keys in backup: {missing_keys}"
        print(f"✅ 1.1C PASS: All legacy keys present: {required_keys}")

    # ==================== 1.3 Billing Tests ====================
    
    def test_1_3A_billing_subscription_returns_plan_and_date(self, auth_headers):
        """1.3A: Billing subscription returns plan + renewal/trial date field"""
        response = requests.get(
            f"{BASE_URL}/api/billing/subscription",
            headers=auth_headers,
            timeout=30
        )
        assert response.status_code == 200, f"Subscription endpoint failed: {response.status_code}"
        
        data = response.json()
        
        # Must have plan field
        plan = data.get("plan")
        assert plan is not None, "Subscription response missing 'plan' field"
        
        # Must have at least one date field (trial_end OR current_period_end)
        trial_end = data.get("trial_end")
        current_period_end = data.get("current_period_end")
        
        has_date = trial_end is not None or current_period_end is not None
        assert has_date, f"Subscription response missing date field. Got: trial_end={trial_end}, current_period_end={current_period_end}"
        
        print(f"✅ 1.3A PASS: plan={plan}, trial_end={trial_end}, current_period_end={current_period_end}")

    # ==================== 1.6 Customer Import Tests ====================
    
    def test_1_6D_empty_customer_import_returns_error(self, auth_headers):
        """1.6D: Empty customer import payload returns clear error"""
        response = requests.post(
            f"{BASE_URL}/api/customers/import",
            headers=auth_headers,
            json={"customers": []},
            timeout=30
        )
        
        # Should return 400 for empty payload
        assert response.status_code == 400, f"Expected 400 for empty import, got {response.status_code}"
        
        data = response.json()
        detail = data.get("detail", "")
        assert "at least one" in detail.lower() or "row" in detail.lower(), f"Error message not clear: {detail}"
        
        print(f"✅ 1.6D PASS: Empty import returns 400 with message: {detail}")

    def test_1_6K_phone_search_parentheses_format(self, auth_headers):
        """1.6K: Customer search supports phone format (415) 555-1234"""
        # First create a test customer with this phone
        test_phone = "(415) 555-1234"
        test_name = f"TEST_PhoneSearch_{uuid.uuid4().hex[:8]}"
        
        # Create customer
        create_resp = requests.post(
            f"{BASE_URL}/api/customers",
            headers=auth_headers,
            json={"name": test_name, "phone": test_phone}
        )
        assert create_resp.status_code == 200, f"Failed to create test customer: {create_resp.text}"
        customer_id = create_resp.json().get("id")
        
        try:
            # Search by phone
            search_resp = requests.get(
                f"{BASE_URL}/api/customers",
                headers=auth_headers,
                params={"search": test_phone}
            )
            assert search_resp.status_code == 200
            results = search_resp.json()
            
            found = any(c.get("id") == customer_id for c in results)
            assert found, f"Customer not found with phone search: {test_phone}"
            print(f"✅ 1.6K PASS: Phone search works for format (415) 555-1234")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)

    def test_1_6L_phone_search_dot_format(self, auth_headers):
        """1.6L: Customer search supports phone format 415.555.1234"""
        test_phone = "415.555.1234"
        test_name = f"TEST_PhoneSearch_{uuid.uuid4().hex[:8]}"
        
        create_resp = requests.post(
            f"{BASE_URL}/api/customers",
            headers=auth_headers,
            json={"name": test_name, "phone": test_phone}
        )
        assert create_resp.status_code == 200, f"Failed to create test customer: {create_resp.text}"
        customer_id = create_resp.json().get("id")
        
        try:
            search_resp = requests.get(
                f"{BASE_URL}/api/customers",
                headers=auth_headers,
                params={"search": test_phone}
            )
            assert search_resp.status_code == 200
            results = search_resp.json()
            
            found = any(c.get("id") == customer_id for c in results)
            assert found, f"Customer not found with phone search: {test_phone}"
            print(f"✅ 1.6L PASS: Phone search works for format 415.555.1234")
        finally:
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)

    def test_1_6M_phone_search_dash_format(self, auth_headers):
        """1.6M: Customer search supports phone format 415-555-1234"""
        test_phone = "415-555-1234"
        test_name = f"TEST_PhoneSearch_{uuid.uuid4().hex[:8]}"
        
        create_resp = requests.post(
            f"{BASE_URL}/api/customers",
            headers=auth_headers,
            json={"name": test_name, "phone": test_phone}
        )
        assert create_resp.status_code == 200, f"Failed to create test customer: {create_resp.text}"
        customer_id = create_resp.json().get("id")
        
        try:
            search_resp = requests.get(
                f"{BASE_URL}/api/customers",
                headers=auth_headers,
                params={"search": test_phone}
            )
            assert search_resp.status_code == 200
            results = search_resp.json()
            
            found = any(c.get("id") == customer_id for c in results)
            assert found, f"Customer not found with phone search: {test_phone}"
            print(f"✅ 1.6M PASS: Phone search works for format 415-555-1234")
        finally:
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)

    def test_1_6N_phone_search_plus_space_format(self, auth_headers):
        """1.6N: Customer search supports phone format +1 415 555 1234"""
        test_phone = "+1 415 555 1234"
        test_name = f"TEST_PhoneSearch_{uuid.uuid4().hex[:8]}"
        
        create_resp = requests.post(
            f"{BASE_URL}/api/customers",
            headers=auth_headers,
            json={"name": test_name, "phone": test_phone}
        )
        assert create_resp.status_code == 200, f"Failed to create test customer: {create_resp.text}"
        customer_id = create_resp.json().get("id")
        
        try:
            search_resp = requests.get(
                f"{BASE_URL}/api/customers",
                headers=auth_headers,
                params={"search": test_phone}
            )
            assert search_resp.status_code == 200
            results = search_resp.json()
            
            found = any(c.get("id") == customer_id for c in results)
            assert found, f"Customer not found with phone search: {test_phone}"
            print(f"✅ 1.6N PASS: Phone search works for format +1 415 555 1234")
        finally:
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)

    def test_1_6O_phone_search_plus_no_space_format(self, auth_headers):
        """1.6O: Customer search supports phone format +14155551234"""
        test_phone = "+14155551234"
        test_name = f"TEST_PhoneSearch_{uuid.uuid4().hex[:8]}"
        
        create_resp = requests.post(
            f"{BASE_URL}/api/customers",
            headers=auth_headers,
            json={"name": test_name, "phone": test_phone}
        )
        assert create_resp.status_code == 200, f"Failed to create test customer: {create_resp.text}"
        customer_id = create_resp.json().get("id")
        
        try:
            search_resp = requests.get(
                f"{BASE_URL}/api/customers",
                headers=auth_headers,
                params={"search": test_phone}
            )
            assert search_resp.status_code == 200
            results = search_resp.json()
            
            found = any(c.get("id") == customer_id for c in results)
            assert found, f"Customer not found with phone search: {test_phone}"
            print(f"✅ 1.6O PASS: Phone search works for format +14155551234")
        finally:
            requests.delete(f"{BASE_URL}/api/customers/{customer_id}", headers=auth_headers)

    def test_1_6P_invalid_email_skipped_valid_imports(self, auth_headers):
        """1.6P: Invalid email row is skipped and error is returned while valid row imports"""
        test_suffix = uuid.uuid4().hex[:8]
        
        # Row 1: Invalid email
        # Row 2: Valid customer
        import_payload = {
            "customers": [
                {"name": f"TEST_InvalidEmail_{test_suffix}", "email": "not-an-email"},
                {"name": f"TEST_ValidCustomer_{test_suffix}", "email": f"valid_{test_suffix}@example.com"}
            ]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/customers/import",
            headers=auth_headers,
            json=import_payload,
            timeout=30
        )
        
        assert response.status_code == 200, f"Import failed: {response.status_code} - {response.text}"
        
        data = response.json()
        created = data.get("created", 0)
        errors = data.get("errors", [])
        
        # Should have created 1 (valid row) and have 1 error (invalid email row)
        assert created == 1, f"Expected 1 created, got {created}"
        assert len(errors) >= 1, f"Expected at least 1 error for invalid email, got {errors}"
        
        # Check error mentions invalid email
        error_text = " ".join(errors).lower()
        assert "email" in error_text or "invalid" in error_text, f"Error should mention email issue: {errors}"
        
        print(f"✅ 1.6P PASS: Invalid email skipped (errors={errors}), valid row imported (created={created})")
        
        # Cleanup - find and delete the valid customer
        search_resp = requests.get(
            f"{BASE_URL}/api/customers",
            headers=auth_headers,
            params={"search": f"TEST_ValidCustomer_{test_suffix}"}
        )
        if search_resp.status_code == 200:
            for customer in search_resp.json():
                if f"TEST_ValidCustomer_{test_suffix}" in customer.get("name", ""):
                    requests.delete(f"{BASE_URL}/api/customers/{customer['id']}", headers=auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
