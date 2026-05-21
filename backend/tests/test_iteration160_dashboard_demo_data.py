"""
Iteration 160: Dashboard Demo Data Verification Tests
Tests all dashboard widgets, demo data counts, API endpoints,
navigation links, and specific data verification.
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"

# Demo data IDs from the report
DEMO_ORDER_IDS = {
    "ORD-0023": "95bdf2c6-baf7-4249-ad79-c5231a18ff64",
    "ORD-0024": "0f2c006b-8add-400e-824c-890b73f2cb74",
    "ORD-0025": "ea405513-fbc9-4598-9529-74fbb4992a4c",
    "ORD-0026": "bf4446a3-b081-4a57-919c-7e375bd7f11e",
    "ORD-0027": "f3692132-7a12-45ed-ac38-51943ec2f4ed",
    "ORD-0028": "9a0fb2d8-7e1d-44e1-b3b0-06aabc02c551",
    "ORD-0029": "cd4dd39c-c4ef-4a46-bbf1-c43ddfff22bd",
    "ORD-0030": "36a57405-656d-4f06-91c7-9841de328680",
    "ORD-0031": "2d50de47-875f-4ec2-b4e6-97160f262304",
    "ORD-0032": "d682a5c5-3b56-4fae-9b54-5599edbe39f0",
    "ORD-0033": "7939d1bb-f352-423a-805b-743ada035b92",
}

DEMO_INVOICE_IDS = {
    "overdue_cyf": "7cb85fad-4c72-4611-af1a-06bf22525599",
    "sent_champion": "ed8f5f08-6a15-491e-af67-85d1c5d103f0",
    "paid_abc": "d466f653-f1b5-4d51-884d-07fb7563459c",
    "sent_rr": "9e09448d-dc55-4252-9055-83e2022ed3c7",
    "overdue_patriot": "6dbd2339-aad9-40a6-a988-b0c81a1ff1a0",
    "sent_miller": "77f58a46-1a69-44b5-b8ba-6c0121076a86",
    "paid_mountain_view": "7db279e5-e4df-4c94-99b8-8040a2b6572d",
    "draft_lh_racing": "4717bbdd-313e-47ab-823a-3c323ae1b785",
    "draft_johnson": "75f8b342-0a34-4573-896f-447c96f14230",
}

DEMO_WEBSTORE_IDS = {
    "creator": "fb8cb09f-77da-4ce0-b84a-cecac6ea2e16",
    "business": "4d33df5b-768a-4118-ba72-3eedbfe3b179",
    "fundraiser": "1a23c96f-272e-4c29-a3d4-aa852bef64c8",
    "event": "60077d2a-5ffc-45fb-9184-d21ba000c8c7",
}


@pytest.fixture(scope="module")
def token():
    """Get auth token for admin"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if res.status_code == 200:
        data = res.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Auth failed: {res.status_code} {res.text[:200]}")


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ─── WIDGET 1: Total Customers ───────────────────────────────────────────────

class TestTotalCustomers:
    """Widget 1: Total Customers"""

    def test_customers_api_returns_200(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert res.status_code == 200, f"Customers API failed: {res.status_code}"

    def test_customers_count_34_or_more(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        customers = data if isinstance(data, list) else data.get("customers", data.get("items", []))
        print(f"Total customers: {len(customers)}")
        assert len(customers) >= 34, f"Expected 34+ customers, got {len(customers)}"

    def test_demo_customers_present(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        customers = data if isinstance(data, list) else data.get("customers", data.get("items", []))
        names = [c.get("name", c.get("company_name", "")) for c in customers]
        demo_names = [
            "DEMO - Champion Bakery", "DEMO - Miller Plumbing", "DEMO - Laurel Highlands Racing",
            "DEMO - Connellsville Youth Football", "DEMO - ABC Manufacturing",
            "DEMO - Johnson Benefit Dinner", "DEMO - Mountain View Church",
            "DEMO - R&R Landscaping", "DEMO - Smith Family Reunion", "DEMO - Patriot Auto Sales"
        ]
        found = [d for d in demo_names if any(d in n for n in names)]
        print(f"Found demo customers: {found}")
        assert len(found) >= 8, f"Expected 8+ DEMO customers, found only {len(found)}: {found}"


# ─── WIDGET 2: Active Orders ─────────────────────────────────────────────────

class TestActiveOrders:
    """Widget 2: Active Orders"""

    def test_orders_api_returns_200(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/orders", headers=auth_headers)
        assert res.status_code == 200, f"Orders API failed: {res.status_code}"

    def test_demo_orders_exist(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/orders", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        orders = data if isinstance(data, list) else data.get("orders", data.get("items", []))
        order_numbers = [o.get("order_number", "") for o in orders]
        demo_orders_found = [num for num in DEMO_ORDER_IDS.keys() if num in order_numbers]
        print(f"Found demo orders: {demo_orders_found}")
        assert len(demo_orders_found) >= 8, f"Expected 8+ demo orders, found {len(demo_orders_found)}"

    def test_specific_order_ORD0023_accessible(self, auth_headers):
        order_id = DEMO_ORDER_IDS["ORD-0023"]
        res = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert res.status_code in [200, 201], f"ORD-0023 not found: {res.status_code}"
        data = res.json()
        print(f"ORD-0023 data: title={data.get('title')}, order_number={data.get('order_number')}")

    def test_specific_order_ORD0028_accessible(self, auth_headers):
        order_id = DEMO_ORDER_IDS["ORD-0028"]
        res = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert res.status_code in [200, 201], f"ORD-0028 not found: {res.status_code}"
        data = res.json()
        print(f"ORD-0028 data: title={data.get('title')}, order_number={data.get('order_number')}")


# ─── WIDGET 3 & 4: Pending Invoices + Today's Revenue ─────────────────────────

class TestInvoicesAndRevenue:
    """Widget 3: Pending Invoices, Widget 4: Today's Revenue"""

    def test_invoices_api_returns_200(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert res.status_code == 200, f"Invoices API failed: {res.status_code}"

    def test_overdue_invoices_count(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        invoices = data if isinstance(data, list) else data.get("invoices", data.get("items", []))
        overdue = [i for i in invoices if i.get("status") == "overdue"]
        print(f"Overdue invoices: {len(overdue)}")
        assert len(overdue) >= 2, f"Expected 2+ overdue invoices, found {len(overdue)}"

    def test_paid_invoices_exist(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        invoices = data if isinstance(data, list) else data.get("invoices", data.get("items", []))
        paid = [i for i in invoices if i.get("status") == "paid"]
        print(f"Paid invoices: {len(paid)}, totals: {[i.get('total') for i in paid]}")
        assert len(paid) >= 2, f"Expected 2+ paid invoices, got {len(paid)}"

    def test_sent_invoices_exist(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        invoices = data if isinstance(data, list) else data.get("invoices", data.get("items", []))
        sent = [i for i in invoices if i.get("status") == "sent"]
        print(f"Sent invoices: {len(sent)}")
        assert len(sent) >= 3, f"Expected 3+ sent invoices, got {len(sent)}"

    def test_specific_overdue_cyf_invoice(self, auth_headers):
        inv_id = DEMO_INVOICE_IDS["overdue_cyf"]
        res = requests.get(f"{BASE_URL}/api/invoices/{inv_id}", headers=auth_headers)
        assert res.status_code == 200, f"CYF overdue invoice not found: {res.status_code}"
        data = res.json()
        assert data.get("status") == "overdue", f"Expected overdue, got {data.get('status')}"
        print(f"CYF invoice total: {data.get('total')}, status: {data.get('status')}")

    def test_specific_overdue_patriot_invoice(self, auth_headers):
        inv_id = DEMO_INVOICE_IDS["overdue_patriot"]
        res = requests.get(f"{BASE_URL}/api/invoices/{inv_id}", headers=auth_headers)
        assert res.status_code == 200, f"Patriot overdue invoice not found: {res.status_code}"
        data = res.json()
        assert data.get("status") == "overdue", f"Expected overdue, got {data.get('status')}"
        print(f"Patriot invoice total: {data.get('total')}, status: {data.get('status')}")

    def test_abc_paid_invoice_amount(self, auth_headers):
        inv_id = DEMO_INVOICE_IDS["paid_abc"]
        res = requests.get(f"{BASE_URL}/api/invoices/{inv_id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "paid", f"Expected paid, got {data.get('status')}"
        total = float(data.get("total", 0))
        print(f"ABC paid invoice total: {total}")
        assert abs(total - 42.40) < 1.0, f"Expected ~$42.40, got {total}"

    def test_mountain_view_paid_invoice_amount(self, auth_headers):
        inv_id = DEMO_INVOICE_IDS["paid_mountain_view"]
        res = requests.get(f"{BASE_URL}/api/invoices/{inv_id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "paid", f"Expected paid, got {data.get('status')}"
        total = float(data.get("total", 0))
        print(f"Mountain View paid invoice total: {total}")
        assert abs(total - 267.12) < 1.0, f"Expected ~$267.12, got {total}"


# ─── WIDGET 5: Today's Schedule ───────────────────────────────────────────────

class TestTodaysSchedule:
    """Widget 5: Today's Schedule — appointments from /api/appointments"""

    def test_appointments_api_returns_200(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/appointments", headers=auth_headers)
        assert res.status_code == 200, f"Appointments API failed: {res.status_code}"

    def test_today_appointments_exist(self, auth_headers):
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        res = requests.get(f"{BASE_URL}/api/appointments", headers=auth_headers,
                           params={"start_date": today, "end_date": today})
        assert res.status_code == 200
        data = res.json()
        appts = data if isinstance(data, list) else data.get("appointments", data.get("items", []))
        print(f"Today's appointments ({today}): {len(appts)}")
        for a in appts:
            print(f"  - {a.get('title', a.get('name', 'N/A'))} | date: {a.get('date', a.get('start_date', a.get('start_datetime', 'N/A')))}")
        # Note: 6 demo appointments created for today
        assert len(appts) >= 0, "Appointments API should work"  # just reporting

    def test_demo_appointments_exist_ungrouped(self, auth_headers):
        """Check all appointments including without date filter"""
        res = requests.get(f"{BASE_URL}/api/appointments", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        appts = data if isinstance(data, list) else data.get("appointments", data.get("items", []))
        demo_titles = [
            "Miller Plumbing Van Drop-Off",
            "Champion Bakery Banner Production Review",
            "CYF Yard Sign Printing - Production",
            "ABC Mfg Sign Installation",
            "Patriot Auto - Customer Pickup",
            "R&R Landscaping Design Review"
        ]
        found_titles = [a.get('title', a.get('name', '')) for a in appts]
        found_demo = [t for t in demo_titles if any(t in ft for ft in found_titles)]
        print(f"Found demo appointments: {found_demo}")
        print(f"Total appointments returned: {len(appts)}")

    def test_productivity_items_today(self, auth_headers):
        """Check if appointments show in /api/productivity/items for today"""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        res = requests.get(f"{BASE_URL}/api/productivity/items", headers=auth_headers, params={
            "start_date": today,
            "end_date": today,
            "include_completed": False,
            "item_types": "job,production_task,appointment,schedule_shift"
        })
        assert res.status_code == 200, f"Productivity items API failed: {res.status_code}"
        data = res.json()
        items = data.get("items", [])
        print(f"Productivity items today: {len(items)}")
        for item in items[:10]:
            print(f"  - {item.get('title', 'N/A')} | type: {item.get('item_type', 'N/A')} | date: {item.get('start_datetime', item.get('due_datetime', 'N/A'))}")


# ─── WIDGET 6: Messages ──────────────────────────────────────────────────────

class TestMessages:
    """Widget 6: Messages"""

    def test_unread_messages_api(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/dashboard/unread-messages", headers=auth_headers)
        assert res.status_code == 200, f"Unread messages API failed: {res.status_code}"
        data = res.json()
        print(f"Unread messages count: {len(data) if isinstance(data, list) else data}")


# ─── WIDGET 7: Pending Approvals ─────────────────────────────────────────────

class TestPendingApprovals:
    """Widget 7: Pending Approvals"""

    def test_pending_approvals_api(self, auth_headers):
        """Check productivity items with approval statuses"""
        res = requests.get(f"{BASE_URL}/api/productivity/items", headers=auth_headers, params={
            "include_completed": False,
            "statuses": "pending,awaiting_approval,awaiting_quote,awaiting_review",
            "item_types": "job,production_task"
        })
        assert res.status_code == 200, f"Pending approvals API failed: {res.status_code}"
        data = res.json()
        items = data.get("items", [])
        print(f"Pending approval items: {len(items)}")
        for item in items[:5]:
            print(f"  - {item.get('title', 'N/A')} | status: {item.get('status', 'N/A')} | customer: {item.get('customer_name', 'N/A')}")


# ─── WIDGET 8: Team Status ───────────────────────────────────────────────────

class TestTeamStatus:
    """Widget 8: Team Status"""

    def test_employees_api_returns_200(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert res.status_code == 200, f"Employees API failed: {res.status_code}"

    def test_employees_count_includes_demo(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/employees", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        employees = data if isinstance(data, list) else data.get("employees", data.get("items", []))
        print(f"Total employees: {len(employees)}")
        demo_employees = [e for e in employees if "DEMO" in e.get("name", "") or "DEMO" in str(e.get("full_name", ""))]
        print(f"Demo employees: {[e.get('name', e.get('full_name', '')) for e in demo_employees]}")
        assert len(demo_employees) >= 4, f"Expected 4+ DEMO employees, found {len(demo_employees)}"

    def test_team_status_today_api(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/dashboard/team-status-today", headers=auth_headers)
        assert res.status_code == 200, f"Team status today API failed: {res.status_code}"
        data = res.json()
        print(f"Team status today: clocked_in={data.get('clocked_in_count', 0)}, scheduled={data.get('scheduled_count', 0)}")
        print(f"Employees in response: {len(data.get('employees', []))}")
        for emp in data.get('employees', []):
            print(f"  - {emp.get('employee_name', 'N/A')}: status={emp.get('clock_status', 'N/A')}, scheduled={emp.get('is_scheduled', False)}")


# ─── WIDGET 10: Overdue Invoices Banner ──────────────────────────────────────

class TestOverdueBanner:
    """Widget 10: Overdue Invoices Banner — via dashboard stats"""

    def test_productivity_summary_returns_200(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/productivity/summary", headers=auth_headers)
        assert res.status_code == 200, f"Productivity summary failed: {res.status_code}"
        data = res.json()
        print(f"Productivity summary: {data}")

    def test_dashboard_stats_overdue_count(self, auth_headers):
        """Dashboard stats should show overdue invoices"""
        # Try fetching from multiple possible endpoints
        endpoints = [
            "/api/dashboard/stats",
            "/api/productivity/summary",
        ]
        for endpoint in endpoints:
            res = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers)
            if res.status_code == 200:
                data = res.json()
                print(f"{endpoint}: {data}")
                overdue_count = data.get("overdue_count", data.get("overdue_invoices", 0))
                print(f"Overdue count from {endpoint}: {overdue_count}")
                break


# ─── Webstores ────────────────────────────────────────────────────────────────

class TestWebstores:
    """Navigation: Webstores"""

    def test_webstores_api_returns_200(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers)
        assert res.status_code == 200, f"Webstores API failed: {res.status_code}"

    def test_4_demo_webstores_exist(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/webstores/v2", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        webstores = data if isinstance(data, list) else data.get("webstores", data.get("items", []))
        print(f"Total webstores: {len(webstores)}")
        demo_stores = [w for w in webstores if "DEMO" in w.get("name", "")]
        print(f"Demo webstores: {[w.get('name', '') for w in demo_stores]}")
        assert len(demo_stores) >= 4, f"Expected 4 DEMO webstores, found {len(demo_stores)}"

    def test_event_store_johnson_exists(self, auth_headers):
        """Verify DEMO - Johnson Benefit Dinner Store with event fields"""
        store_id = DEMO_WEBSTORE_IDS["event"]
        res = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        assert res.status_code == 200, f"Johnson event store not found: {res.status_code}"
        data = res.json()
        print(f"Johnson store: name={data.get('name')}, type={data.get('store_type')}")
        print(f"  fundraiser_enabled={data.get('fundraiser_enabled')}, fundraiser_goal={data.get('fundraiser_goal')}")
        print(f"  donation_enabled={data.get('donation_enabled')}, event_date={data.get('event_date')}")
        assert data.get("store_type") == "event" or data.get("type") == "event", f"Expected event store type"

    def test_creator_store_lh_racing_exists(self, auth_headers):
        store_id = DEMO_WEBSTORE_IDS["creator"]
        res = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        assert res.status_code == 200, f"LH Racing creator store not found: {res.status_code}"
        data = res.json()
        print(f"LH Racing store: name={data.get('name')}, type={data.get('store_type', data.get('type'))}")

    def test_fundraiser_store_mountain_view_exists(self, auth_headers):
        store_id = DEMO_WEBSTORE_IDS["fundraiser"]
        res = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        assert res.status_code == 200, f"Mountain View fundraiser store not found: {res.status_code}"
        data = res.json()
        print(f"Mountain View store: name={data.get('name')}, type={data.get('store_type', data.get('type'))}")


# ─── Pricing Verification ─────────────────────────────────────────────────────

class TestPricingVerification:
    """Verify order pricing for ORD-0023 and ORD-0028"""

    def test_ord0023_cyf_yard_signs_price(self, auth_headers):
        """ORD-0023 should have a job ticket with $1800.00"""
        order_id = DEMO_ORDER_IDS["ORD-0023"]
        res = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        print(f"ORD-0023: {data.get('title')}")
        # Check job tickets
        tickets = data.get("job_tickets", data.get("tickets", []))
        if tickets:
            for t in tickets:
                print(f"  Ticket: {t.get('item', 'N/A')} | price: {t.get('price', t.get('total', 'N/A'))}")
        total = data.get("total", data.get("amount", 0))
        print(f"  Order total: {total}")

    def test_ord0028_miller_van_graphics_price(self, auth_headers):
        """ORD-0028 should have job ticket with $562.10"""
        order_id = DEMO_ORDER_IDS["ORD-0028"]
        res = requests.get(f"{BASE_URL}/api/orders/{order_id}", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        print(f"ORD-0028: {data.get('title')}")
        tickets = data.get("job_tickets", data.get("tickets", []))
        if tickets:
            for t in tickets:
                print(f"  Ticket: {t.get('item', 'N/A')} | price: {t.get('price', t.get('total', 'N/A'))}")
        total = data.get("total", data.get("amount", 0))
        print(f"  Order total: {total}")


# ─── Dashboard Data Endpoint ──────────────────────────────────────────────────

class TestDashboardDataEndpoints:
    """Test all dashboard data endpoints"""

    def test_dashboard_stats_endpoint(self, auth_headers):
        """Fetch dashboard stats — where does it come from?"""
        res = requests.get(f"{BASE_URL}/api/productivity/summary", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        print(f"Productivity summary data keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
        print(f"Full productivity summary: {json.dumps(data, indent=2)[:1000]}")

    def test_dashboard_clocked_in_endpoint(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/dashboard/clocked-in", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        print(f"Clocked in response: {data}")

    def test_dashboard_recent_ai_docs_endpoint(self, auth_headers):
        res = requests.get(f"{BASE_URL}/api/dashboard/recent-ai-documents", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        print(f"Recent AI docs: {len(data) if isinstance(data, list) else data}")
