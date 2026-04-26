"""
Iteration 127 - Bug Fix Tests:
- Bug 2.1F: Tax-exempt toggle in invoice generation
  - Non-exempt customer: tax_amount = subtotal * default_tax_rate/100
  - Tax-exempt customer: tax_amount = 0

- Bug 2.2E: Company settings tax rate field persistence
  - default_tax_rate set via PUT /api/tenant persists correctly
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


def get_auth_token(email=None, password=None):
    """Get auth token for the given credentials"""
    email = email or 'thesigntistslab@gmail.com'
    password = password or 'password123'
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        return None
    return resp.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers():
    """Shared auth headers for all tests"""
    token = get_auth_token()
    if not token:
        pytest.skip("Authentication failed — skipping all tests")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def original_tax_rate(auth_headers):
    """Capture and restore original default_tax_rate"""
    resp = requests.get(f"{BASE_URL}/api/tenant", headers=auth_headers)
    assert resp.status_code == 200
    original = resp.json().get("default_tax_rate", 0.0)
    yield original
    # Restore after module
    requests.put(f"{BASE_URL}/api/tenant", json={"default_tax_rate": original}, headers=auth_headers)


# ============== TENANT TAX RATE TESTS ==============

class TestTenantTaxRate:
    """Test setting and getting default_tax_rate on tenant"""

    def test_set_default_tax_rate_6(self, auth_headers, original_tax_rate):
        """Set default_tax_rate = 6.0 via PUT /api/tenant"""
        resp = requests.put(f"{BASE_URL}/api/tenant", json={"default_tax_rate": 6.0}, headers=auth_headers)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "default_tax_rate" in data, "Response should include default_tax_rate"
        assert float(data["default_tax_rate"]) == 6.0, f"Expected 6.0, got {data['default_tax_rate']}"
        print(f"✓ default_tax_rate set to 6.0. Was: {original_tax_rate}")

    def test_get_tenant_returns_tax_rate(self, auth_headers):
        """GET /api/tenant should return the persisted default_tax_rate"""
        resp = requests.get(f"{BASE_URL}/api/tenant", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert float(data.get("default_tax_rate", -1)) == 6.0, \
            f"Expected persisted rate = 6.0, got {data.get('default_tax_rate')}"
        print(f"✓ Tenant GET returns default_tax_rate = {data['default_tax_rate']}")


# ============== TAX-EXEMPT INVOICE TESTS ==============

class TestInvoiceTaxExemptToggle:
    """
    Test tax-exempt toggle on invoice generation.
    Non-exempt customer: tax applied at default_tax_rate.
    Exempt customer: tax_amount = 0.
    """

    @pytest.fixture(scope="class")
    def setup_tax_rate(self, auth_headers):
        """Ensure tax rate is 6% before these tests"""
        resp = requests.put(f"{BASE_URL}/api/tenant", json={"default_tax_rate": 6.0}, headers=auth_headers)
        assert resp.status_code == 200
        return 6.0

    def _create_customer(self, auth_headers, is_tax_exempt: bool, suffix: str):
        """Helper: create a test customer"""
        uid = str(uuid.uuid4())[:8]
        payload = {
            "name": f"TEST_TaxCustomer_{suffix}_{uid}",
            "email": f"test_tax_{suffix}_{uid}@example.com",
            "is_tax_exempt": is_tax_exempt,
        }
        resp = requests.post(f"{BASE_URL}/api/customers", json=payload, headers=auth_headers)
        assert resp.status_code in (200, 201), f"Create customer failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("id"), "Customer must have an id"
        assert data.get("is_tax_exempt") == is_tax_exempt, \
            f"is_tax_exempt should be {is_tax_exempt}, got {data.get('is_tax_exempt')}"
        print(f"✓ Created customer id={data['id']} is_tax_exempt={is_tax_exempt}")
        return data

    def _create_order(self, auth_headers, customer):
        """Helper: create an order for a customer"""
        payload = {
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "order_source": "phone",
        }
        resp = requests.post(f"{BASE_URL}/api/orders", json=payload, headers=auth_headers)
        assert resp.status_code in (200, 201), f"Create order failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("id"), "Order must have an id"
        print(f"✓ Created order id={data['id']}")
        return data

    def _create_job_ticket(self, auth_headers, order_id, price=100.0):
        """Helper: create a job ticket with given estimated_price"""
        uid = str(uuid.uuid4())[:8]
        payload = {
            "order_id": order_id,
            "item_name": f"TEST_Ticket_{uid}",
            "item_category": "banner",
            "quantity": 1,
            "estimated_price": price,
        }
        resp = requests.post(f"{BASE_URL}/api/job-tickets", json=payload, headers=auth_headers)
        assert resp.status_code in (200, 201), f"Create ticket failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("id"), "Ticket must have an id"
        print(f"✓ Created job ticket id={data['id']} price={price}")
        return data

    def _generate_invoice(self, auth_headers, order_id):
        """Helper: generate invoice from order"""
        resp = requests.post(f"{BASE_URL}/api/orders/{order_id}/generate-invoice", headers=auth_headers)
        assert resp.status_code in (200, 201), f"Generate invoice failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("id"), "Invoice must have an id"
        print(f"✓ Generated invoice id={data['id']} tax_amount={data.get('tax_amount')} grand_total={data.get('grand_total')}")
        return data

    # Non-exempt customer tests
    def test_non_exempt_customer_has_tax_amount(self, auth_headers, setup_tax_rate):
        """Non-exempt customer: invoice should have tax_amount = subtotal * 0.06"""
        customer = self._create_customer(auth_headers, is_tax_exempt=False, suffix="nonexempt")
        order = self._create_order(auth_headers, customer)
        ticket = self._create_job_ticket(auth_headers, order["id"], price=100.0)
        invoice = self._generate_invoice(auth_headers, order["id"])

        tax_amount = float(invoice.get("tax_amount", -1))
        grand_total = float(invoice.get("grand_total", -1))
        total = float(invoice.get("total", -1))
        is_tax_exempt = invoice.get("is_tax_exempt")
        tax_rate = float(invoice.get("tax_rate", -1))

        assert is_tax_exempt == False, f"Invoice is_tax_exempt should be False, got {is_tax_exempt}"
        assert tax_rate == 6.0, f"Invoice tax_rate should be 6.0, got {tax_rate}"
        assert total == 100.0, f"Invoice total (subtotal) should be 100.0, got {total}"
        assert tax_amount == 6.0, f"Non-exempt customer: expected tax_amount=6.0, got {tax_amount}"
        assert grand_total == 106.0, f"Non-exempt customer: expected grand_total=106.0, got {grand_total}"
        print(f"✓ PASS: Non-exempt invoice: tax_amount={tax_amount}, grand_total={grand_total}")

    def test_non_exempt_customer_invoice_tax_rate_field(self, auth_headers, setup_tax_rate):
        """Non-exempt customer: invoice.tax_rate should equal tenant default_tax_rate"""
        customer = self._create_customer(auth_headers, is_tax_exempt=False, suffix="nonexempt2")
        order = self._create_order(auth_headers, customer)
        self._create_job_ticket(auth_headers, order["id"], price=200.0)
        invoice = self._generate_invoice(auth_headers, order["id"])

        assert float(invoice.get("tax_rate", -1)) == 6.0, \
            f"tax_rate field should be 6.0, got {invoice.get('tax_rate')}"
        assert float(invoice.get("tax_amount", -1)) == 12.0, \
            f"tax_amount for $200 at 6% should be 12.0, got {invoice.get('tax_amount')}"
        assert float(invoice.get("grand_total", -1)) == 212.0, \
            f"grand_total for $200 + $12 tax should be 212.0, got {invoice.get('grand_total')}"
        print(f"✓ PASS: Non-exempt $200 invoice: tax_amount={invoice.get('tax_amount')}, grand_total={invoice.get('grand_total')}")

    # Tax-exempt customer tests
    def test_exempt_customer_has_zero_tax(self, auth_headers, setup_tax_rate):
        """Tax-exempt customer: invoice should have tax_amount = 0"""
        customer = self._create_customer(auth_headers, is_tax_exempt=True, suffix="exempt")
        order = self._create_order(auth_headers, customer)
        ticket = self._create_job_ticket(auth_headers, order["id"], price=100.0)
        invoice = self._generate_invoice(auth_headers, order["id"])

        tax_amount = float(invoice.get("tax_amount", -1))
        grand_total = float(invoice.get("grand_total", -1))
        total = float(invoice.get("total", -1))
        is_tax_exempt = invoice.get("is_tax_exempt")
        tax_rate = float(invoice.get("tax_rate", -1))

        assert is_tax_exempt == True, f"Invoice is_tax_exempt should be True, got {is_tax_exempt}"
        assert tax_rate == 0.0, f"Invoice tax_rate for exempt customer should be 0.0, got {tax_rate}"
        assert total == 100.0, f"Invoice total (subtotal) should be 100.0, got {total}"
        assert tax_amount == 0.0, f"Tax-exempt customer: expected tax_amount=0.0, got {tax_amount}"
        assert grand_total == 100.0, f"Tax-exempt customer: expected grand_total=100.0, got {grand_total}"
        print(f"✓ PASS: Exempt invoice: tax_amount={tax_amount}, grand_total={grand_total}")

    def test_exempt_customer_grand_total_equals_subtotal(self, auth_headers, setup_tax_rate):
        """Tax-exempt customer: grand_total must equal subtotal (no tax)"""
        customer = self._create_customer(auth_headers, is_tax_exempt=True, suffix="exempt2")
        order = self._create_order(auth_headers, customer)
        self._create_job_ticket(auth_headers, order["id"], price=250.0)
        invoice = self._generate_invoice(auth_headers, order["id"])

        total = float(invoice.get("total", -1))
        grand_total = float(invoice.get("grand_total", -1))
        tax_amount = float(invoice.get("tax_amount", -1))

        assert tax_amount == 0.0, f"Exempt customer: tax_amount should be 0.0, got {tax_amount}"
        assert grand_total == total, \
            f"grand_total ({grand_total}) should equal total/subtotal ({total}) for exempt customer"
        print(f"✓ PASS: Exempt $250 invoice: grand_total == subtotal = {grand_total}")


# ============== EXISTING ORDER TESTS (from context) ==============

class TestExistingOrderTaxExemptInvoice:
    """Use pre-existing order and customer IDs from agent context for regression"""

    # From agent context:
    NON_EXEMPT_CUSTOMER_ID = "1eaeec1d-6fbb-48fa-aa96-ecc4298bdb8b"
    EXEMPT_CUSTOMER_ID = "1a72666e-1e4f-41ac-bf75-cd8c494cc836"

    def test_get_non_exempt_customer(self, auth_headers):
        """Verify non-exempt customer exists and is_tax_exempt=False"""
        resp = requests.get(f"{BASE_URL}/api/customers/{self.NON_EXEMPT_CUSTOMER_ID}", headers=auth_headers)
        if resp.status_code == 404:
            pytest.skip("Pre-existing non-exempt customer not found — skipped")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_tax_exempt") == False, \
            f"Non-exempt customer should have is_tax_exempt=False, got {data.get('is_tax_exempt')}"
        print(f"✓ Non-exempt customer verified: {data.get('name')} is_tax_exempt={data.get('is_tax_exempt')}")

    def test_get_exempt_customer(self, auth_headers):
        """Verify exempt customer exists and is_tax_exempt=True"""
        resp = requests.get(f"{BASE_URL}/api/customers/{self.EXEMPT_CUSTOMER_ID}", headers=auth_headers)
        if resp.status_code == 404:
            pytest.skip("Pre-existing exempt customer not found — skipped")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_tax_exempt") == True, \
            f"Exempt customer should have is_tax_exempt=True, got {data.get('is_tax_exempt')}"
        print(f"✓ Exempt customer verified: {data.get('name')} is_tax_exempt={data.get('is_tax_exempt')}")


# ============== CLEANUP FIXTURE ==============

@pytest.fixture(scope="module", autouse=True)
def cleanup_test_customers(auth_headers):
    """Track and clean up TEST_ customers created during tests"""
    yield
    # List customers and delete TEST_ prefixed ones created in this run
    resp = requests.get(f"{BASE_URL}/api/customers?limit=200", headers=auth_headers)
    if resp.status_code == 200:
        customers = resp.json() if isinstance(resp.json(), list) else resp.json().get("items", [])
        for c in customers:
            if c.get("name", "").startswith("TEST_TaxCustomer_"):
                requests.delete(f"{BASE_URL}/api/customers/{c['id']}", headers=auth_headers)
    print("✓ Cleanup complete")
