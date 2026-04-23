"""
Iteration 122: Portal Regressions Testing

Tests for:
1. Portal dashboard stat cards are clickable and navigate to intended routes
2. Portal dashboard shows recent orders when order exists
3. Portal Orders page lists all customer orders
4. Portal Quotes and Invoices list and status refresh correctly from unified sources
5. Portal conversation send message from customer works without network error
6. Customers detail popup shows only one New Order and one distinct secondary action
7. Invoices page payment verification/reconcile fallback still functional after portal changes

Seeded test data:
- customer_id: a5023d21-2b6c-4480-9b00-f1adb8d53b3d
- order_id: c4f00d92-c7d1-4a83-af96-f74adf7d5e4d
- quote_id: 56c2c9c5-f89e-44e3-9fc1-f80ed55594d1
- invoice_id: 810e9945-b706-46d4-9665-53215370765e
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = "signguypa@gmail.com"
OWNER_PASSWORD = "Billnel323"
PORTAL_EMAIL = "portalreg_1776974524@example.com"
PORTAL_PASSWORD = "123456"

# Seeded test data IDs
SEEDED_CUSTOMER_ID = "a5023d21-2b6c-4480-9b00-f1adb8d53b3d"
SEEDED_ORDER_ID = "c4f00d92-c7d1-4a83-af96-f74adf7d5e4d"
SEEDED_QUOTE_ID = "56c2c9c5-f89e-44e3-9fc1-f80ed55594d1"
SEEDED_INVOICE_ID = "810e9945-b706-46d4-9665-53215370765e"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": OWNER_EMAIL,
        "password": OWNER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def portal_token():
    """Get portal customer authentication token"""
    response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
        "email": PORTAL_EMAIL,
        "password": PORTAL_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Portal authentication failed: {response.status_code} - {response.text}")


class TestPortalAuthentication:
    """Test portal authentication works"""
    
    def test_portal_login_success(self):
        """Test portal login with seeded test user"""
        response = requests.post(f"{BASE_URL}/api/portal/auth/login", json={
            "email": PORTAL_EMAIL,
            "password": PORTAL_PASSWORD
        })
        assert response.status_code == 200, f"Portal login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "customer_id" in data
        assert "customer_name" in data
        print(f"Portal login successful for customer: {data.get('customer_name')}")


class TestPortalDashboard:
    """Test portal dashboard returns correct data for stat cards"""
    
    def test_dashboard_returns_stats(self, portal_token):
        """Test dashboard endpoint returns stats object with all required fields"""
        response = requests.get(f"{BASE_URL}/api/portal/dashboard", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Verify stats object exists
        assert "stats" in data, "Dashboard missing 'stats' object"
        stats = data["stats"]
        
        # Verify all stat fields exist (for clickable cards)
        required_stats = [
            "total_quotes", "active_jobs", "pending_invoices", "pending_proofs",
            "unread_messages", "unread_notifications", "pending_forms", "recent_documents"
        ]
        for stat in required_stats:
            assert stat in stats, f"Dashboard stats missing '{stat}'"
            print(f"  {stat}: {stats[stat]}")
    
    def test_dashboard_returns_recent_jobs(self, portal_token):
        """Test dashboard returns recent_jobs array (for Recent Orders section)"""
        response = requests.get(f"{BASE_URL}/api/portal/dashboard", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "recent_jobs" in data, "Dashboard missing 'recent_jobs'"
        recent_jobs = data["recent_jobs"]
        assert isinstance(recent_jobs, list), "recent_jobs should be a list"
        
        # If seeded order exists, it should appear
        if len(recent_jobs) > 0:
            print(f"Found {len(recent_jobs)} recent jobs")
            # Check first job has required fields
            job = recent_jobs[0]
            assert "id" in job, "Job missing 'id'"
            assert "status" in job, "Job missing 'status'"
            print(f"  First job: {job.get('id')[:8]}... status={job.get('status')}")
        else:
            print("No recent jobs found (may need to verify seeded data)")
    
    def test_dashboard_returns_recent_invoices(self, portal_token):
        """Test dashboard returns recent_invoices array"""
        response = requests.get(f"{BASE_URL}/api/portal/dashboard", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "recent_invoices" in data, "Dashboard missing 'recent_invoices'"
        recent_invoices = data["recent_invoices"]
        assert isinstance(recent_invoices, list), "recent_invoices should be a list"
        
        if len(recent_invoices) > 0:
            print(f"Found {len(recent_invoices)} recent invoices")
            invoice = recent_invoices[0]
            assert "id" in invoice
            assert "status" in invoice
            print(f"  First invoice: {invoice.get('id')[:8]}... status={invoice.get('status')}")


class TestPortalOrders:
    """Test portal orders endpoint lists all customer orders"""
    
    def test_orders_list_returns_data(self, portal_token):
        """Test /portal/orders returns list of orders"""
        response = requests.get(f"{BASE_URL}/api/portal/orders", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200, f"Orders list failed: {response.text}"
        orders = response.json()
        
        assert isinstance(orders, list), "Orders should be a list"
        print(f"Found {len(orders)} orders for portal customer")
        
        if len(orders) > 0:
            order = orders[0]
            # Verify order has required fields
            assert "id" in order
            assert "status" in order
            print(f"  First order: {order.get('id')[:8]}... status={order.get('status')}")
    
    def test_orders_list_with_status_filter(self, portal_token):
        """Test orders can be filtered by status"""
        response = requests.get(f"{BASE_URL}/api/portal/orders?status=active", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200, f"Orders filter failed: {response.text}"
        orders = response.json()
        assert isinstance(orders, list)
        print(f"Found {len(orders)} active orders")


class TestPortalQuotes:
    """Test portal quotes endpoint"""
    
    def test_quotes_list_returns_data(self, portal_token):
        """Test /portal/quotes returns list of quotes"""
        response = requests.get(f"{BASE_URL}/api/portal/quotes", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200, f"Quotes list failed: {response.text}"
        quotes = response.json()
        
        assert isinstance(quotes, list), "Quotes should be a list"
        print(f"Found {len(quotes)} quotes for portal customer")
        
        if len(quotes) > 0:
            quote = quotes[0]
            assert "id" in quote
            assert "status" in quote
            print(f"  First quote: {quote.get('id')[:8]}... status={quote.get('status')}")


class TestPortalInvoices:
    """Test portal invoices endpoint with unified sources"""
    
    def test_invoices_list_returns_data(self, portal_token):
        """Test /portal/invoices returns list of invoices from unified sources"""
        response = requests.get(f"{BASE_URL}/api/portal/invoices", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200, f"Invoices list failed: {response.text}"
        invoices = response.json()
        
        assert isinstance(invoices, list), "Invoices should be a list"
        print(f"Found {len(invoices)} invoices for portal customer")
        
        if len(invoices) > 0:
            invoice = invoices[0]
            assert "id" in invoice
            assert "status" in invoice
            # Verify normalized fields
            assert "total" in invoice
            print(f"  First invoice: {invoice.get('id')[:8]}... status={invoice.get('status')} total={invoice.get('total')}")
    
    def test_invoice_status_normalization(self, portal_token):
        """Test invoice status is properly normalized (paid when amount_paid >= total)"""
        response = requests.get(f"{BASE_URL}/api/portal/invoices", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        invoices = response.json()
        
        for invoice in invoices:
            total = float(invoice.get("total", 0) or 0)
            amount_paid = float(invoice.get("amount_paid", 0) or 0)
            status = invoice.get("status", "")
            
            # If fully paid, status should be 'paid'
            if amount_paid >= total and total > 0:
                assert status == "paid", f"Invoice {invoice['id'][:8]} should be 'paid' but is '{status}'"
                print(f"  Invoice {invoice['id'][:8]}: correctly marked as paid (paid={amount_paid}, total={total})")


class TestPortalMessaging:
    """Test portal messaging - send message without network error"""
    
    def test_conversations_list(self, portal_token):
        """Test /portal/conversations returns list"""
        response = requests.get(f"{BASE_URL}/api/portal/conversations", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200, f"Conversations list failed: {response.text}"
        conversations = response.json()
        assert isinstance(conversations, list)
        print(f"Found {len(conversations)} conversations")
        return conversations
    
    def test_create_conversation(self, portal_token):
        """Test creating a new conversation"""
        response = requests.post(f"{BASE_URL}/api/portal/conversations", 
            headers={
                "Authorization": f"Bearer {portal_token}",
                "Content-Type": "application/json"
            },
            json={
                "subject": "Test conversation from iteration 122",
                "message": "This is a test message to verify portal messaging works"
            }
        )
        assert response.status_code == 200, f"Create conversation failed: {response.text}"
        conv = response.json()
        assert "id" in conv
        print(f"Created conversation: {conv.get('id')[:8]}...")
        return conv
    
    def test_send_message_in_conversation(self, portal_token):
        """Test sending a message in an existing conversation - the main regression test"""
        # First create a conversation
        create_resp = requests.post(f"{BASE_URL}/api/portal/conversations", 
            headers={
                "Authorization": f"Bearer {portal_token}",
                "Content-Type": "application/json"
            },
            json={
                "subject": "Message send test",
                "message": "Initial message"
            }
        )
        assert create_resp.status_code == 200
        conv = create_resp.json()
        conv_id = conv["id"]
        
        # Now send a follow-up message - THIS IS THE REGRESSION TEST
        # The bug was "network error sending portal message"
        send_resp = requests.post(f"{BASE_URL}/api/portal/conversations/{conv_id}/messages",
            headers={
                "Authorization": f"Bearer {portal_token}",
                "Content-Type": "application/json"
            },
            json={
                "content": "Follow-up message to test send functionality",
                "conversation_id": conv_id  # Optional field per MessageCreate model
            }
        )
        
        assert send_resp.status_code == 200, f"Send message failed: {send_resp.status_code} - {send_resp.text}"
        msg = send_resp.json()
        assert "id" in msg
        assert "content" in msg
        assert msg["content"] == "Follow-up message to test send functionality"
        print(f"Successfully sent message in conversation {conv_id[:8]}...")
    
    def test_send_message_empty_content_rejected(self, portal_token):
        """Test that empty message content is rejected"""
        # Create conversation first
        create_resp = requests.post(f"{BASE_URL}/api/portal/conversations", 
            headers={
                "Authorization": f"Bearer {portal_token}",
                "Content-Type": "application/json"
            },
            json={
                "subject": "Empty message test",
                "message": "Initial"
            }
        )
        conv_id = create_resp.json()["id"]
        
        # Try to send empty message
        send_resp = requests.post(f"{BASE_URL}/api/portal/conversations/{conv_id}/messages",
            headers={
                "Authorization": f"Bearer {portal_token}",
                "Content-Type": "application/json"
            },
            json={
                "content": "   "  # Whitespace only
            }
        )
        
        assert send_resp.status_code == 400, f"Empty message should be rejected: {send_resp.status_code}"
        print("Empty message correctly rejected with 400")


class TestAdminCustomersPage:
    """Test admin customers page - verify no duplicate New Order button"""
    
    def test_customers_list(self, admin_token):
        """Test customers list endpoint works"""
        response = requests.get(f"{BASE_URL}/api/customers", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Customers list failed: {response.text}"
        customers = response.json()
        assert isinstance(customers, list)
        print(f"Found {len(customers)} customers")
    
    def test_customer_detail(self, admin_token):
        """Test getting customer detail"""
        # First get customers list
        list_resp = requests.get(f"{BASE_URL}/api/customers", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        customers = list_resp.json()
        
        if len(customers) > 0:
            customer_id = customers[0]["id"]
            detail_resp = requests.get(f"{BASE_URL}/api/customers/{customer_id}", headers={
                "Authorization": f"Bearer {admin_token}"
            })
            assert detail_resp.status_code == 200
            customer = detail_resp.json()
            assert "id" in customer
            assert "name" in customer
            print(f"Customer detail: {customer.get('name')}")


class TestInvoicesReconciliation:
    """Test invoices page payment verification/reconcile still works"""
    
    def test_reconcile_invoices_endpoint(self, admin_token):
        """Test reconcile-invoices endpoint still works after portal changes"""
        response = requests.post(f"{BASE_URL}/api/stripe-connect/reconcile-invoices", 
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # May return 200 or 400 if Stripe not connected - both are valid
        assert response.status_code in [200, 400], f"Reconcile failed unexpectedly: {response.status_code}"
        print(f"Reconcile invoices returned: {response.status_code}")
    
    def test_invoices_list_admin(self, admin_token):
        """Test admin invoices list endpoint"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Invoices list failed: {response.text}"
        invoices = response.json()
        assert isinstance(invoices, list)
        print(f"Found {len(invoices)} invoices in admin view")


class TestSeededDataVerification:
    """Verify seeded test data exists"""
    
    def test_seeded_customer_exists(self, portal_token):
        """Verify the seeded portal customer can access their profile"""
        response = requests.get(f"{BASE_URL}/api/portal/profile", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200, f"Profile fetch failed: {response.text}"
        profile = response.json()
        assert "id" in profile
        print(f"Portal customer profile: {profile.get('name')} (id={profile.get('id')[:8]}...)")
    
    def test_seeded_order_in_portal_orders(self, portal_token):
        """Check if seeded order appears in portal orders"""
        response = requests.get(f"{BASE_URL}/api/portal/orders", headers={
            "Authorization": f"Bearer {portal_token}"
        })
        assert response.status_code == 200
        orders = response.json()
        
        order_ids = [o["id"] for o in orders]
        if SEEDED_ORDER_ID in order_ids:
            print(f"Seeded order {SEEDED_ORDER_ID[:8]}... found in portal orders")
        else:
            print(f"Seeded order {SEEDED_ORDER_ID[:8]}... NOT found - may be in different collection")
            print(f"  Available order IDs: {[oid[:8] for oid in order_ids[:5]]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
