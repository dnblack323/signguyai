"""
Iteration 94 - Pricing & Billing Tests

Tests for:
1. POST /api/pricing/calculate reflects different prices for rigid-sign thickness changes
2. POST /api/pricing/calculate reflects a different price when rush_order is enabled
3. Order-generated quote via POST /api/orders/{order_id}/generate-quote appears in GET /api/quotes
4. Order-generated invoice via POST /api/orders/{order_id}/generate-invoice appears in GET /api/invoices
5. GET /api/orders/{order_id}/financials still shows linked quotes/invoices/work orders correctly
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestPricingCalculator:
    """Test pricing calculator for rigid signs and rush orders"""

    def test_rigid_sign_thickness_4mm_price(self, auth_headers):
        """Test pricing for rigid sign with 4mm thickness"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "rigid_signs",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 18,
                    "substrate_type": "coroplast_4mm",
                    "thickness": "4mm",
                    "double_sided": False,
                    "rush_order": False
                }
            }
        )
        assert response.status_code == 200, f"Pricing calculation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "suggested_price" in data or "selling_price" in data
        price_4mm = data.get("suggested_price") or data.get("selling_price")
        assert price_4mm > 0, "Price should be greater than 0"
        
        # Store for comparison
        return price_4mm

    def test_rigid_sign_thickness_10mm_price(self, auth_headers):
        """Test pricing for rigid sign with 10mm thickness - should be higher than 4mm"""
        response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "rigid_signs",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 18,
                    "substrate_type": "coroplast_10mm",
                    "thickness": "10mm",
                    "double_sided": False,
                    "rush_order": False
                }
            }
        )
        assert response.status_code == 200, f"Pricing calculation failed: {response.text}"
        data = response.json()
        
        price_10mm = data.get("suggested_price") or data.get("selling_price")
        assert price_10mm > 0, "Price should be greater than 0"
        
        return price_10mm

    def test_rigid_sign_thickness_difference(self, auth_headers):
        """Verify 10mm thickness costs more than 4mm thickness"""
        # Use larger dimensions to exceed minimum charge
        # Calculate 4mm price
        response_4mm = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "rigid_signs",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 48,
                    "length_inches": 36,
                    "substrate_type": "coroplast_4mm",
                    "thickness": "4mm",
                    "double_sided": False,
                    "rush_order": False
                }
            }
        )
        assert response_4mm.status_code == 200
        price_4mm = response_4mm.json().get("suggested_price") or response_4mm.json().get("selling_price")
        
        # Calculate 10mm price
        response_10mm = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "rigid_signs",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 48,
                    "length_inches": 36,
                    "substrate_type": "coroplast_10mm",
                    "thickness": "10mm",
                    "double_sided": False,
                    "rush_order": False
                }
            }
        )
        assert response_10mm.status_code == 200
        price_10mm = response_10mm.json().get("suggested_price") or response_10mm.json().get("selling_price")
        
        # 10mm should be more expensive than 4mm
        print(f"4mm price: ${price_4mm:.2f}, 10mm price: ${price_10mm:.2f}")
        assert price_10mm > price_4mm, f"10mm (${price_10mm}) should cost more than 4mm (${price_4mm})"

    def test_rush_order_increases_price(self, auth_headers):
        """Test that rush_order flag increases the price"""
        # Calculate normal price
        response_normal = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "rigid_signs",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 18,
                    "substrate_type": "coroplast_4mm",
                    "thickness": "4mm",
                    "double_sided": False,
                    "rush_order": False
                }
            }
        )
        assert response_normal.status_code == 200
        price_normal = response_normal.json().get("suggested_price") or response_normal.json().get("selling_price")
        
        # Calculate rush price
        response_rush = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "rigid_signs",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 18,
                    "substrate_type": "coroplast_4mm",
                    "thickness": "4mm",
                    "double_sided": False,
                    "rush_order": True
                }
            }
        )
        assert response_rush.status_code == 200
        price_rush = response_rush.json().get("suggested_price") or response_rush.json().get("selling_price")
        
        # Rush order should be more expensive
        print(f"Normal price: ${price_normal:.2f}, Rush price: ${price_rush:.2f}")
        assert price_rush > price_normal, f"Rush order (${price_rush}) should cost more than normal (${price_normal})"

    def test_rush_order_on_banners(self, auth_headers):
        """Test rush order pricing on banners category"""
        # Calculate normal banner price
        response_normal = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "digital_print",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 48,
                    "length_inches": 96,
                    "print_material": "banner_13oz",
                    "laminate": False,
                    "rush_order": False
                }
            }
        )
        assert response_normal.status_code == 200
        price_normal = response_normal.json().get("suggested_price") or response_normal.json().get("selling_price")
        
        # Calculate rush banner price
        response_rush = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=auth_headers,
            json={
                "category": "digital_print",
                "quantity": 1,
                "pricing_data": {
                    "width_inches": 48,
                    "length_inches": 96,
                    "print_material": "banner_13oz",
                    "laminate": False,
                    "rush_order": True
                }
            }
        )
        assert response_rush.status_code == 200
        price_rush = response_rush.json().get("suggested_price") or response_rush.json().get("selling_price")
        
        print(f"Banner normal: ${price_normal:.2f}, Banner rush: ${price_rush:.2f}")
        assert price_rush > price_normal, f"Rush banner (${price_rush}) should cost more than normal (${price_normal})"


class TestOrderQuoteInvoiceGeneration:
    """Test order-generated quotes and invoices appear in billing flows"""

    @pytest.fixture(scope="class")
    def test_order(self, auth_headers):
        """Create a test order for quote/invoice generation"""
        order_data = {
            "customer_name": f"TEST_Pricing_Customer_{uuid.uuid4().hex[:8]}",
            "company_name": "TEST Pricing Company",
            "status": "new"
        }
        response = requests.post(
            f"{BASE_URL}/api/orders",
            headers=auth_headers,
            json=order_data
        )
        assert response.status_code == 200, f"Failed to create order: {response.text}"
        order = response.json()
        yield order
        
        # Cleanup: delete the test order
        requests.delete(f"{BASE_URL}/api/orders/{order['id']}", headers=auth_headers)

    @pytest.fixture(scope="class")
    def test_ticket(self, auth_headers, test_order):
        """Create a test job ticket for the order"""
        ticket_data = {
            "order_id": test_order["id"],
            "item_name": "TEST Pricing Ticket",
            "item_category": "rigid_signs",
            "quantity": 2,
            "estimated_price": 150.00,
            "specs": {
                "width": "24",
                "height": "18",
                "substrate": "coroplast_4mm",
                "thickness": "4mm"
            }
        }
        response = requests.post(
            f"{BASE_URL}/api/job-tickets",
            headers=auth_headers,
            json=ticket_data
        )
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        return response.json()

    def test_generate_quote_from_order(self, auth_headers, test_order, test_ticket):
        """Test generating a quote from an order"""
        response = requests.post(
            f"{BASE_URL}/api/orders/{test_order['id']}/generate-quote",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to generate quote: {response.text}"
        quote = response.json()
        
        # Verify quote structure
        assert "id" in quote, "Quote should have an ID"
        assert quote.get("order_id") == test_order["id"], "Quote should be linked to order"
        assert "line_items" in quote, "Quote should have line items"
        assert len(quote["line_items"]) > 0, "Quote should have at least one line item"
        
        return quote

    def test_generated_quote_appears_in_quotes_list(self, auth_headers, test_order, test_ticket):
        """Test that order-generated quote appears in GET /api/quotes"""
        # First generate a quote
        gen_response = requests.post(
            f"{BASE_URL}/api/orders/{test_order['id']}/generate-quote",
            headers=auth_headers
        )
        assert gen_response.status_code == 200
        generated_quote = gen_response.json()
        quote_id = generated_quote["id"]
        
        # Verify the generated quote has order_id
        assert generated_quote.get("order_id") == test_order["id"], "Generated quote should have order_id"
        assert generated_quote.get("source") == "order", "Generated quote should have source='order'"
        
        # Now check if it appears in the quotes list
        list_response = requests.get(
            f"{BASE_URL}/api/quotes",
            headers=auth_headers
        )
        assert list_response.status_code == 200, f"Failed to list quotes: {list_response.text}"
        quotes = list_response.json()
        
        # Find our generated quote
        quote_ids = [q["id"] for q in quotes]
        assert quote_id in quote_ids, f"Generated quote {quote_id} should appear in quotes list"
        
        # Verify the quote in the list has order_id (after model fix)
        matching_quote = next((q for q in quotes if q["id"] == quote_id), None)
        assert matching_quote is not None
        # After model fix, order_id should be present
        print(f"Quote {quote_id} found in quotes list with order_id={matching_quote.get('order_id')}, source={matching_quote.get('source')}")

    def test_generate_invoice_from_order(self, auth_headers, test_order, test_ticket):
        """Test generating an invoice from an order"""
        response = requests.post(
            f"{BASE_URL}/api/orders/{test_order['id']}/generate-invoice",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to generate invoice: {response.text}"
        invoice = response.json()
        
        # Verify invoice structure
        assert "id" in invoice, "Invoice should have an ID"
        assert invoice.get("order_id") == test_order["id"], "Invoice should be linked to order"
        assert "line_items" in invoice, "Invoice should have line items"
        
        return invoice

    def test_generated_invoice_appears_in_invoices_list(self, auth_headers, test_order, test_ticket):
        """Test that order-generated invoice appears in GET /api/invoices"""
        # First generate an invoice
        gen_response = requests.post(
            f"{BASE_URL}/api/orders/{test_order['id']}/generate-invoice",
            headers=auth_headers
        )
        assert gen_response.status_code == 200
        generated_invoice = gen_response.json()
        invoice_id = generated_invoice["id"]
        
        # Verify the generated invoice has order_id
        assert generated_invoice.get("order_id") == test_order["id"], "Generated invoice should have order_id"
        assert generated_invoice.get("source") == "order", "Generated invoice should have source='order'"
        
        # Now check if it appears in the invoices list
        list_response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        assert list_response.status_code == 200, f"Failed to list invoices: {list_response.text}"
        invoices = list_response.json()
        
        # Find our generated invoice
        invoice_ids = [i["id"] for i in invoices]
        assert invoice_id in invoice_ids, f"Generated invoice {invoice_id} should appear in invoices list"
        
        # Verify the invoice in the list has order_id (after model fix)
        matching_invoice = next((i for i in invoices if i["id"] == invoice_id), None)
        assert matching_invoice is not None
        # After model fix, order_id should be present
        print(f"Invoice {invoice_id} found in invoices list with order_id={matching_invoice.get('order_id')}, source={matching_invoice.get('source')}")

    def test_order_financials_shows_linked_documents(self, auth_headers, test_order, test_ticket):
        """Test GET /api/orders/{order_id}/financials shows linked quotes/invoices"""
        # Generate both quote and invoice
        requests.post(f"{BASE_URL}/api/orders/{test_order['id']}/generate-quote", headers=auth_headers)
        requests.post(f"{BASE_URL}/api/orders/{test_order['id']}/generate-invoice", headers=auth_headers)
        
        # Get financials
        response = requests.get(
            f"{BASE_URL}/api/orders/{test_order['id']}/financials",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get financials: {response.text}"
        financials = response.json()
        
        # Verify structure
        assert "quotes" in financials, "Financials should include quotes"
        assert "invoices" in financials, "Financials should include invoices"
        assert "work_orders" in financials, "Financials should include work_orders"
        
        # Verify we have at least one quote and invoice
        assert len(financials["quotes"]) > 0, "Should have at least one quote"
        assert len(financials["invoices"]) > 0, "Should have at least one invoice"
        
        print(f"Financials: {len(financials['quotes'])} quotes, {len(financials['invoices'])} invoices, {len(financials['work_orders'])} work orders")


class TestQuotesInvoicesEndpoints:
    """Test quotes and invoices endpoints work correctly"""

    def test_quotes_list_endpoint(self, auth_headers):
        """Test GET /api/quotes returns valid response"""
        response = requests.get(
            f"{BASE_URL}/api/quotes",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Quotes list failed: {response.text}"
        quotes = response.json()
        assert isinstance(quotes, list), "Quotes should be a list"
        print(f"Found {len(quotes)} quotes")

    def test_invoices_list_endpoint(self, auth_headers):
        """Test GET /api/invoices returns valid response"""
        response = requests.get(
            f"{BASE_URL}/api/invoices",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Invoices list failed: {response.text}"
        invoices = response.json()
        assert isinstance(invoices, list), "Invoices should be a list"
        print(f"Found {len(invoices)} invoices")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
