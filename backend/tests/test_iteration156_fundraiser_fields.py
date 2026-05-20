"""
Iteration 156 Backend Tests: Fundraiser Field Structure Fix (Part 3)

Tests verify:
1. Event Store creation with dedicated fundraiser fields (fundraiser_name, fundraiser_goal_amount, etc.)
2. fundraiser_name is separate from event_name (NOT overwritten)
3. apply-answers SAFE_MAP correctly maps:
   - 'Fundraiser Name' → fundraiser_name (NOT event_name)
   - 'Fundraiser Description' → fundraiser_description
   - 'Fundraiser Goal Amount ($)' → fundraiser_goal_amount
   - 'Event Name' → event_name (unchanged behavior)
   - 'Event Location' → event_location
4. locked_settings are NOT modified by apply-answers
5. PUT /api/webstores/v2/{id} with fundraiser fields updates correctly
6. Business and Creator stores are unaffected (no fundraiser fields required)
"""

import pytest
import requests
import os
import uuid
import time

# Load env from frontend .env if not already set
_backend_url = os.environ.get("REACT_APP_BACKEND_URL", "")
if not _backend_url:
    try:
        with open("/app/frontend/.env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("REACT_APP_BACKEND_URL="):
                    _backend_url = line.split("=", 1)[1].strip()
                    break
    except Exception:
        pass

BASE_URL = _backend_url.rstrip("/")


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def auth_token():
    """Login with admin credentials and return bearer token."""
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "thesigntistslab@gmail.com",
        "password": "password123",
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json().get("access_token") or resp.json().get("token")
    assert token, "No token in login response"
    return token


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def event_store_with_fundraiser(auth_headers):
    """Create a TEST event store with fundraiser fields; delete it after all tests."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"TEST_Fundraiser_Event_Store_{unique}",
        "store_type": "event",
        "owner_name": "Test Fundraiser Owner",
        "owner_email": "fundraiser@example.com",
        "event_name": "Test Gala 2026",
        "event_location": "Test Venue",
        # Dedicated fundraiser fields
        "fundraiser_name": "Gala Fund",
        "fundraiser_goal_amount": 5000,
        "profit_allocation_type": "percentage",
        "profit_allocation_percentage": 20,
        "fundraiser_enabled": True,
        "fundraiser_description": "Raising funds for the gala",
        "locked_settings": {
            "store_owner_profit": 8.50,
        },
    }
    resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
    assert resp.status_code in (200, 201), f"Failed to create event store: {resp.text}"
    store = resp.json()
    store_id = store["id"]
    yield store
    # Teardown
    requests.delete(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)


@pytest.fixture(scope="module")
def business_store(auth_headers):
    """Create a TEST business store (unaffected by fundraiser changes)."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"TEST_Business_Store_156_{unique}",
        "store_type": "business",
        "owner_name": "Biz Owner",
        "owner_email": "biz@example.com",
    }
    resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
    assert resp.status_code in (200, 201), f"Failed to create business store: {resp.text}"
    store = resp.json()
    yield store
    store_id_b = store["id"]
    requests.delete(f"{BASE_URL}/api/webstores/v2/{store_id_b}", headers=auth_headers)


@pytest.fixture(scope="module")
def creator_store(auth_headers):
    """Create a TEST creator store (unaffected by fundraiser changes)."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"TEST_Creator_Store_156_{unique}",
        "store_type": "creator",
        "owner_name": "Creator Owner",
        "owner_email": "creator@example.com",
        "creator_commission_type": "percentage",
        "creator_commission_value": 15,
    }
    resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
    assert resp.status_code in (200, 201), f"Failed to create creator store: {resp.text}"
    store = resp.json()
    yield store
    requests.delete(f"{BASE_URL}/api/webstores/v2/{store['id']}", headers=auth_headers)


# ── Tests: Event Store Fundraiser Fields on Create ─────────────────────────────

class TestEventStoreFundraiserFieldsCreate:
    """Verify fundraiser fields are stored correctly on Event Store creation."""

    def test_event_store_created_with_fundraiser_name(self, event_store_with_fundraiser):
        """fundraiser_name should be 'Gala Fund'."""
        store = event_store_with_fundraiser
        assert store.get("fundraiser_name") == "Gala Fund", (
            f"Expected fundraiser_name='Gala Fund', got '{store.get('fundraiser_name')}'"
        )
        print(f"✓ fundraiser_name = {store.get('fundraiser_name')}")

    def test_event_name_is_separate_from_fundraiser_name(self, event_store_with_fundraiser):
        """event_name and fundraiser_name are separate, independent fields."""
        store = event_store_with_fundraiser
        assert store.get("event_name") == "Test Gala 2026", (
            f"event_name should be 'Test Gala 2026', got '{store.get('event_name')}'"
        )
        assert store.get("fundraiser_name") == "Gala Fund", (
            f"fundraiser_name should be 'Gala Fund', got '{store.get('fundraiser_name')}'"
        )
        assert store.get("event_name") != store.get("fundraiser_name"), (
            "event_name and fundraiser_name must be distinct!"
        )
        print(f"✓ event_name='{store.get('event_name')}' != fundraiser_name='{store.get('fundraiser_name')}'")

    def test_fundraiser_goal_amount_saved(self, event_store_with_fundraiser):
        """fundraiser_goal_amount should be 5000."""
        store = event_store_with_fundraiser
        assert store.get("fundraiser_goal_amount") == 5000.0, (
            f"Expected 5000, got {store.get('fundraiser_goal_amount')}"
        )
        print(f"✓ fundraiser_goal_amount = {store.get('fundraiser_goal_amount')}")

    def test_profit_allocation_type_saved(self, event_store_with_fundraiser):
        """profit_allocation_type should be 'percentage'."""
        store = event_store_with_fundraiser
        assert store.get("profit_allocation_type") == "percentage", (
            f"Expected 'percentage', got '{store.get('profit_allocation_type')}'"
        )
        print(f"✓ profit_allocation_type = {store.get('profit_allocation_type')}")

    def test_profit_allocation_percentage_saved(self, event_store_with_fundraiser):
        """profit_allocation_percentage should be 20."""
        store = event_store_with_fundraiser
        assert store.get("profit_allocation_percentage") == 20.0, (
            f"Expected 20.0, got {store.get('profit_allocation_percentage')}"
        )
        print(f"✓ profit_allocation_percentage = {store.get('profit_allocation_percentage')}")

    def test_fundraiser_enabled_saved(self, event_store_with_fundraiser):
        """fundraiser_enabled should be True."""
        store = event_store_with_fundraiser
        assert store.get("fundraiser_enabled") is True, (
            f"Expected True, got {store.get('fundraiser_enabled')}"
        )
        print(f"✓ fundraiser_enabled = {store.get('fundraiser_enabled')}")

    def test_locked_settings_preserved_on_create(self, event_store_with_fundraiser):
        """locked_settings.store_owner_profit should be 8.50."""
        store = event_store_with_fundraiser
        ls = store.get("locked_settings", {})
        assert ls.get("store_owner_profit") == 8.50, (
            f"locked_settings.store_owner_profit expected 8.50, got {ls.get('store_owner_profit')}"
        )
        print(f"✓ locked_settings.store_owner_profit = {ls.get('store_owner_profit')}")

    def test_get_store_by_id_fundraiser_fields_persisted(self, auth_headers, event_store_with_fundraiser):
        """GET the store and confirm fundraiser fields persisted in DB."""
        store_id = event_store_with_fundraiser["id"]
        resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        assert resp.status_code == 200, f"GET failed: {resp.text}"
        data = resp.json()
        assert data.get("fundraiser_name") == "Gala Fund"
        assert data.get("fundraiser_goal_amount") == 5000.0
        assert data.get("event_name") == "Test Gala 2026"
        assert data.get("fundraiser_name") != data.get("event_name")
        print("✓ GET confirms fundraiser fields persisted and separate from event_name")


# ── Tests: PUT Update with Fundraiser Fields ──────────────────────────────────

class TestEventStoreFundraiserFieldsUpdate:
    """Verify PUT /api/webstores/v2/{id} correctly updates fundraiser fields."""

    def test_put_update_fundraiser_name(self, auth_headers, event_store_with_fundraiser):
        """Update fundraiser_name via PUT and verify persistence."""
        store_id = event_store_with_fundraiser["id"]
        resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{store_id}",
            json={"fundraiser_name": "Youth Scholarship Fund"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"PUT failed: {resp.text}"
        updated = resp.json()
        assert updated.get("fundraiser_name") == "Youth Scholarship Fund", (
            f"Expected 'Youth Scholarship Fund', got '{updated.get('fundraiser_name')}'"
        )
        # Verify event_name is NOT changed
        assert updated.get("event_name") == "Test Gala 2026", (
            f"event_name should remain unchanged, got '{updated.get('event_name')}'"
        )
        print(f"✓ PUT updated fundraiser_name without touching event_name")

    def test_put_update_fundraiser_goal_amount(self, auth_headers, event_store_with_fundraiser):
        """Update fundraiser_goal_amount via PUT."""
        store_id = event_store_with_fundraiser["id"]
        resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{store_id}",
            json={"fundraiser_goal_amount": 7500.0},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"PUT failed: {resp.text}"
        updated = resp.json()
        assert updated.get("fundraiser_goal_amount") == 7500.0, (
            f"Expected 7500.0, got {updated.get('fundraiser_goal_amount')}"
        )
        print(f"✓ PUT updated fundraiser_goal_amount to 7500.0")

    def test_put_update_multiple_fundraiser_fields(self, auth_headers, event_store_with_fundraiser):
        """Update multiple fundraiser fields at once."""
        store_id = event_store_with_fundraiser["id"]
        resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{store_id}",
            json={
                "fundraiser_name": "Gala Fund",  # restore
                "fundraiser_goal_amount": 5000.0,  # restore
                "show_progress_bar": True,
                "allow_checkout_donations": True,
                "donation_amount_options": "$5, $10, $25",
                "profit_allocation_enabled": True,
                "profit_allocation_type": "percentage",
                "profit_allocation_percentage": 20.0,
                "show_total_raised_publicly": True,
                "show_supporter_names": "yes_with_permission",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"PUT failed: {resp.text}"
        data = resp.json()
        assert data.get("fundraiser_name") == "Gala Fund"
        assert data.get("show_progress_bar") is True
        assert data.get("allow_checkout_donations") is True
        assert data.get("show_total_raised_publicly") is True
        print(f"✓ Multiple fundraiser fields updated correctly")

    def test_put_update_does_not_change_locked_settings(self, auth_headers, event_store_with_fundraiser):
        """Updating fundraiser fields should not affect locked_settings."""
        store_id = event_store_with_fundraiser["id"]
        resp = requests.put(
            f"{BASE_URL}/api/webstores/v2/{store_id}",
            json={"fundraiser_name": "Updated Fund"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        ls = data.get("locked_settings", {})
        assert ls.get("store_owner_profit") == 8.50, (
            f"locked_settings.store_owner_profit should remain 8.50, got {ls.get('store_owner_profit')}"
        )
        # Restore
        requests.put(
            f"{BASE_URL}/api/webstores/v2/{store_id}",
            json={"fundraiser_name": "Gala Fund"},
            headers=auth_headers,
        )
        print(f"✓ locked_settings unchanged after fundraiser field update")


# ── Tests: Questionnaire Apply-Answers SAFE_MAP ──────────────────────────────

class TestApplyAnswersSafeMap:
    """
    Verify apply-answers SAFE_MAP maps questionnaire fields to correct store fields:
    - 'Fundraiser Name' → fundraiser_name (NOT event_name)
    - 'Fundraiser Description' → fundraiser_description
    - 'Fundraiser Goal Amount ($)' → fundraiser_goal_amount
    - 'Event Name' → event_name
    - 'Event Location' → event_location
    """

    @pytest.fixture(scope="class")
    def fresh_event_store(self, auth_headers):
        """Create a dedicated event store for apply-answers testing."""
        unique = str(uuid.uuid4())[:8]
        payload = {
            "name": f"TEST_ApplyAnswers_Store_{unique}",
            "store_type": "event",
            "owner_name": "Apply Answers Owner",
            "owner_email": "apply@example.com",
            "event_name": "Original Event Name",
            "locked_settings": {"store_owner_profit": 10.00},
        }
        resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
        assert resp.status_code in (200, 201), f"Failed to create store: {resp.text}"
        store = resp.json()
        yield store
        requests.delete(f"{BASE_URL}/api/webstores/v2/{store['id']}", headers=auth_headers)

    @pytest.fixture(scope="class")
    def linked_questionnaire(self, auth_headers, fresh_event_store):
        """Send questionnaire and return the questionnaire data."""
        store_id = fresh_event_store["id"]
        resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/send",
            json={"email": "apply@example.com", "message": "Test"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Send questionnaire failed: {resp.text}"
        data = resp.json()
        questionnaire_id = data.get("questionnaire_id")
        assert questionnaire_id, "No questionnaire_id in response"
        # Get the public questionnaire
        qresp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        assert qresp.status_code == 200, f"Failed to get public questionnaire: {qresp.text}"
        q_data = qresp.json()
        return q_data

    @pytest.fixture(scope="class")
    def submitted_response(self, auth_headers, fresh_event_store, linked_questionnaire):
        """
        Submit the questionnaire with all required fields PLUS fundraiser-specific answers.
        Build answers map from question labels.
        """
        q_id = linked_questionnaire["id"]
        questions = linked_questionnaire.get("questions", [])

        # Build label → id map
        label_to_id = {q["label"]: q["id"] for q in questions}

        # Get all required question IDs + options
        def get_options_for(label):
            for q in questions:
                if q["label"] == label:
                    return [o["value"] for o in (q.get("options") or [])]
            return []

        answers = {}

        # === Required fields ===
        # order 1: Customer Name (text)
        if "Customer Name" in label_to_id:
            # There are TWO "Customer Name" questions (order 1 and order 84)
            # Build list of IDs
            cname_ids = [q["id"] for q in questions if q["label"] == "Customer Name"]
            for cid in cname_ids:
                answers[cid] = "Test Customer"

        # Phone Number (required)
        if "Phone Number" in label_to_id:
            answers[label_to_id["Phone Number"]] = "555-555-5555"

        # Email Address (required)
        if "Email Address" in label_to_id:
            answers[label_to_id["Email Address"]] = "apply@example.com"

        # Event Name (required, order 7) — CRITICAL: should map to event_name
        if "Event Name" in label_to_id:
            answers[label_to_id["Event Name"]] = "Spring Gala 2026"

        # What should the store be called? (required)
        if "What should the store be called?" in label_to_id:
            answers[label_to_id["What should the store be called?"]] = "Apply Test Store"

        # Do you want the store to be public or private? (required, select)
        store_visibility_label = "Do you want the store to be public or private?"
        if store_visibility_label in label_to_id:
            opts = get_options_for(store_visibility_label)
            answers[label_to_id[store_visibility_label]] = opts[0] if opts else "public"

        # Products checkbox (required)
        products_label = "What products do you want in the store? Check all that apply."
        if products_label in label_to_id:
            opts = get_options_for(products_label)
            answers[label_to_id[products_label]] = [opts[0]] if opts else ["shirts"]

        # Orders 76-83: 8 agreement checkboxes
        checkbox_labels = [
            "I understand the store will be built based on the information, artwork, pricing, product details, fulfillment details, and payment information provided.",
            "I understand missing or incorrect information may delay the store launch.",
            "I understand the store will not launch until product details, pricing, artwork, fulfillment settings, and payment setup are approved.",
            "I understand changes after launch may affect orders, pricing, production timelines, customer experience, and reporting.",
            "I understand Stripe Connect setup must be completed before payouts can be sent to your bank account, and Stripe may require identity, business, tax, and banking information before payouts can begin.",
            "I understand payment processing fees and any agreed platform/store fees may be deducted from online transactions, and payouts are sent according to Stripe's payout schedule.",
            "I understand customer-provided artwork, logos, images, names, and sponsor files must be approved for use by the customer or organization submitting this form.",
            "I understand production timelines depend on final store approval, payment setup, artwork readiness, order volume, product availability, fulfillment method, and whether submitted artwork is usable for print.",
        ]
        for lbl in checkbox_labels:
            if lbl in label_to_id:
                opts = get_options_for(lbl)
                answers[label_to_id[lbl]] = [opts[0]] if opts else ["agree"]

        # Customer Signature (required, type=signature)
        if "Customer Signature" in label_to_id:
            answers[label_to_id["Customer Signature"]] = "Test Signature"

        # Date (required, type=date)
        if "Date" in label_to_id:
            answers[label_to_id["Date"]] = "2026-02-01"

        # === Fundraiser-specific answers (key test data) ===
        if "Event Location" in label_to_id:
            answers[label_to_id["Event Location"]] = "Grand Ballroom"

        if "Fundraiser Name" in label_to_id:
            answers[label_to_id["Fundraiser Name"]] = "Youth Scholarship Fund"

        if "Fundraiser Description" in label_to_id:
            answers[label_to_id["Fundraiser Description"]] = "Raising funds for student scholarships"

        if "Fundraiser Goal Amount ($)" in label_to_id:
            answers[label_to_id["Fundraiser Goal Amount ($)"]] = "10000"

        # Submit
        submit_resp = requests.post(
            f"{BASE_URL}/api/questionnaires/public/{q_id}/submit",
            json={
                "questionnaire_id": q_id,
                "answers": answers,
                "customer_name": "Test Customer",
                "customer_email": "apply@example.com",
            },
        )
        assert submit_resp.status_code == 200, f"Questionnaire submit failed: {submit_resp.text}"
        return submit_resp.json()

    def test_questionnaire_submitted_successfully(self, submitted_response):
        """Questionnaire submission should succeed with 200."""
        assert "response_id" in submitted_response, (
            f"No response_id in submit response: {submitted_response}"
        )
        print(f"✓ Questionnaire submitted, response_id={submitted_response.get('response_id')}")

    def test_apply_answers_returns_200(self, auth_headers, fresh_event_store, submitted_response):
        """apply-answers should return 200 and applied_fields."""
        store_id = fresh_event_store["id"]
        resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"apply-answers failed: {resp.text}"
        data = resp.json()
        assert "applied_fields" in data, f"No applied_fields in response: {data}"
        print(f"✓ apply-answers returned 200, applied_fields={list(data['applied_fields'].keys())}")
        # Store result for downstream tests
        return data

    def test_event_name_mapped_correctly(self, auth_headers, fresh_event_store, submitted_response):
        """After apply-answers, event_name should have questionnaire's 'Event Name' answer."""
        store_id = fresh_event_store["id"]
        # Apply answers
        resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        applied = resp.json().get("applied_fields", {})

        # Verify event_name
        if "event_name" in applied:
            assert applied["event_name"] == "Spring Gala 2026", (
                f"event_name should be 'Spring Gala 2026', got '{applied.get('event_name')}'"
            )
        # Verify via GET
        get_resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        store_data = get_resp.json()
        assert store_data.get("event_name") == "Spring Gala 2026", (
            f"Store event_name should be 'Spring Gala 2026', got '{store_data.get('event_name')}'"
        )
        print(f"✓ event_name correctly mapped to 'Spring Gala 2026'")

    def test_fundraiser_name_mapped_to_fundraiser_name_not_event_name(
        self, auth_headers, fresh_event_store, submitted_response
    ):
        """
        CRITICAL: After apply-answers:
        - fundraiser_name should have 'Youth Scholarship Fund' (from 'Fundraiser Name' question)
        - event_name should NOT be 'Youth Scholarship Fund'
        """
        store_id = fresh_event_store["id"]
        # Apply answers (idempotent, safe to call again)
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        get_resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        store_data = get_resp.json()

        # fundraiser_name must be set from 'Fundraiser Name' question
        assert store_data.get("fundraiser_name") == "Youth Scholarship Fund", (
            f"fundraiser_name should be 'Youth Scholarship Fund', got '{store_data.get('fundraiser_name')}'"
        )
        # event_name must NOT be 'Youth Scholarship Fund' (should be 'Spring Gala 2026')
        assert store_data.get("event_name") != "Youth Scholarship Fund", (
            f"event_name should NOT be 'Youth Scholarship Fund' — Fundraiser Name was incorrectly mapped to event_name!"
        )
        assert store_data.get("event_name") == "Spring Gala 2026", (
            f"event_name should be 'Spring Gala 2026', got '{store_data.get('event_name')}'"
        )
        print(
            f"✓ fundraiser_name='{store_data.get('fundraiser_name')}' correctly separate from "
            f"event_name='{store_data.get('event_name')}'"
        )

    def test_fundraiser_description_mapped_correctly(
        self, auth_headers, fresh_event_store, submitted_response
    ):
        """fundraiser_description should come from 'Fundraiser Description' question."""
        store_id = fresh_event_store["id"]
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        get_resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        store_data = get_resp.json()
        assert store_data.get("fundraiser_description") == "Raising funds for student scholarships", (
            f"fundraiser_description expected 'Raising funds for student scholarships', "
            f"got '{store_data.get('fundraiser_description')}'"
        )
        print(f"✓ fundraiser_description correctly mapped")

    def test_fundraiser_goal_amount_mapped_correctly(
        self, auth_headers, fresh_event_store, submitted_response
    ):
        """fundraiser_goal_amount should come from 'Fundraiser Goal Amount ($)' question as float."""
        store_id = fresh_event_store["id"]
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        get_resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        store_data = get_resp.json()
        assert store_data.get("fundraiser_goal_amount") == 10000.0, (
            f"fundraiser_goal_amount expected 10000.0, got {store_data.get('fundraiser_goal_amount')}"
        )
        print(f"✓ fundraiser_goal_amount correctly mapped to 10000.0 (float coercion)")

    def test_event_location_mapped_correctly(
        self, auth_headers, fresh_event_store, submitted_response
    ):
        """event_location should come from 'Event Location' question."""
        store_id = fresh_event_store["id"]
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        get_resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        store_data = get_resp.json()
        assert store_data.get("event_location") == "Grand Ballroom", (
            f"event_location expected 'Grand Ballroom', got '{store_data.get('event_location')}'"
        )
        print(f"✓ event_location correctly mapped to 'Grand Ballroom'")

    def test_locked_settings_not_modified_by_apply_answers(
        self, auth_headers, fresh_event_store, submitted_response
    ):
        """locked_settings.store_owner_profit must remain unchanged after apply-answers."""
        store_id = fresh_event_store["id"]
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        get_resp = requests.get(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)
        store_data = get_resp.json()
        ls = store_data.get("locked_settings", {})
        assert ls.get("store_owner_profit") == 10.00, (
            f"locked_settings.store_owner_profit should be 10.00 (unchanged), got {ls.get('store_owner_profit')}"
        )
        print(f"✓ locked_settings.store_owner_profit unchanged after apply-answers")

    def test_apply_answers_response_has_applied_fields(
        self, auth_headers, fresh_event_store, submitted_response
    ):
        """apply-answers response should include applied_fields with expected keys."""
        store_id = fresh_event_store["id"]
        resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        applied = data.get("applied_fields", {})

        # Check key fields are present
        important_fields = ["event_name", "fundraiser_name", "fundraiser_description",
                            "fundraiser_goal_amount", "event_location"]
        for field in important_fields:
            assert field in applied, f"Expected '{field}' in applied_fields, got: {list(applied.keys())}"
        print(f"✓ apply-answers response contains all expected fundraiser fields: {list(applied.keys())}")


# ── Tests: Business/Creator Stores Unaffected ─────────────────────────────────

class TestNonEventStoresUnaffected:
    """Verify Business and Creator stores can be created/updated without fundraiser fields."""

    def test_business_store_created_without_fundraiser_fields(self, business_store):
        """Business store should not require any fundraiser fields."""
        assert business_store.get("store_type") == "business"
        assert business_store.get("id") is not None
        print(f"✓ Business store created without fundraiser fields, id={business_store['id']}")

    def test_creator_store_created_without_fundraiser_fields(self, creator_store):
        """Creator store should not require any fundraiser fields."""
        assert creator_store.get("store_type") == "creator"
        assert creator_store.get("id") is not None
        print(f"✓ Creator store created without fundraiser fields, id={creator_store['id']}")

    def test_business_store_fundraiser_fields_are_defaults(self, auth_headers, business_store):
        """Business store should have default (falsy) fundraiser fields."""
        resp = requests.get(f"{BASE_URL}/api/webstores/v2/{business_store['id']}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # All these should be falsy/default for a business store
        assert data.get("fundraiser_enabled", False) is False
        assert data.get("fundraiser_name") is None or data.get("fundraiser_name") == ""
        assert data.get("fundraiser_goal_amount") is None or data.get("fundraiser_goal_amount") == 0
        print(f"✓ Business store has default/empty fundraiser fields")

    def test_business_store_questionnaire_endpoint_returns_404(self, auth_headers, business_store):
        """Non-event store should return 404/400 for questionnaire endpoints."""
        store_id = business_store["id"]
        resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        # Should either return linked=False or 404
        if resp.status_code == 200:
            data = resp.json()
            # linked should be False for non-event stores
            assert data.get("linked") is False, (
                f"Business store should not be linked to a questionnaire, got: {data}"
            )
            print(f"✓ Business store questionnaire endpoint returns linked=False")
        else:
            assert resp.status_code in (400, 404), (
                f"Expected 400/404 for business store questionnaire, got {resp.status_code}"
            )
            print(f"✓ Business store questionnaire endpoint returns {resp.status_code}")


# ── Tests: Apply-Answers When No Response Exists ─────────────────────────────

class TestApplyAnswersEdgeCases:
    """Test edge cases for apply-answers endpoint."""

    def test_apply_answers_no_questionnaire_returns_404(self, auth_headers):
        """apply-answers on store without questionnaire should return 404."""
        unique = str(uuid.uuid4())[:8]
        # Create event store without sending questionnaire
        payload = {
            "name": f"TEST_NoQ_Store_{unique}",
            "store_type": "event",
            "owner_name": "No Q Owner",
            "owner_email": "noq@example.com",
        }
        resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
        assert resp.status_code in (200, 201)
        store_id = resp.json()["id"]

        apply_resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        assert apply_resp.status_code == 404, (
            f"Expected 404 for store without questionnaire, got {apply_resp.status_code}: {apply_resp.text}"
        )
        print(f"✓ apply-answers returns 404 when no questionnaire is linked")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)

    def test_fundraiser_name_in_safe_map(self):
        """SAFE_MAP in backend code should map 'Fundraiser Name' → 'fundraiser_name'."""
        import sys
        sys.path.insert(0, "/app/backend")
        # Check the actual SAFE_MAP by reading the source
        with open("/app/backend/routes/webstores.py", "r") as f:
            content = f.read()
        assert '"Fundraiser Name":' in content, "SAFE_MAP should contain 'Fundraiser Name'"
        assert '"fundraiser_name"' in content, "SAFE_MAP should map to 'fundraiser_name'"
        # Make sure fundraiser_name is NOT mapping to event_name
        # Find the line with "Fundraiser Name" key
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if '"Fundraiser Name":' in line:
                # Check it maps to fundraiser_name, not event_name
                assert "fundraiser_name" in line or "fundraiser_name" in lines[i+1], (
                    f"'Fundraiser Name' should map to fundraiser_name, found: {line}"
                )
                assert "event_name" not in line, (
                    f"'Fundraiser Name' should NOT map to event_name! Found: {line}"
                )
                print(f"✓ SAFE_MAP: 'Fundraiser Name' → fundraiser_name (not event_name): {line.strip()}")
                break
