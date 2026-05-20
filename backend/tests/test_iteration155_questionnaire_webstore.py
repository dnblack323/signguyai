"""
Iteration 155 Backend Tests: Event Store Questionnaire Integration (Part 3)
Tests:
- GET /{webstore_id}/questionnaire endpoint (status check)
- POST /{webstore_id}/questionnaire/send (create + email)
- POST /{webstore_id}/questionnaire/apply-answers
- 87 questions in event_web_store_setup template
- Fundraiser section exists (Section 4.5)
- Prefill/locked answer behavior
- Idempotency of send endpoint
- Non-event stores unaffected
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

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
def event_store(auth_headers):
    """Create a TEST event store for this test module; delete it after."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"TEST_Questionnaire_Event_Store_{unique}",
        "store_type": "event",
        "owner_name": "Test Owner",
        "owner_email": "test@example.com",
        "event_name": "Test Gala 2026",
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
    """Create a TEST business store to verify it is unaffected by questionnaire endpoints."""
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": f"TEST_Business_Store_{unique}",
        "store_type": "business",
        "owner_name": "Biz Test Owner",
        "owner_email": "biztest@example.com",
    }
    resp = requests.post(f"{BASE_URL}/api/webstores/v2", json=payload, headers=auth_headers)
    assert resp.status_code in (200, 201), f"Failed to create business store: {resp.text}"
    store = resp.json()
    store_id = store["id"]
    yield store
    requests.delete(f"{BASE_URL}/api/webstores/v2/{store_id}", headers=auth_headers)


# ── Template Verification ──────────────────────────────────────────────────────

class TestQuestionnaireTemplate:
    """Verify the event_web_store_setup template has 87 questions & fundraiser section."""

    def test_template_has_87_questions(self):
        """event_web_store_setup template should have exactly 87 questions."""
        import sys
        sys.path.insert(0, "/app/backend")
        from models.questionnaires import QUESTIONNAIRE_TEMPLATES
        template = QUESTIONNAIRE_TEMPLATES.get("event_web_store_setup")
        assert template is not None, "event_web_store_setup template not found"
        q_count = len(template["questions"])
        assert q_count == 87, f"Expected 87 questions, got {q_count}"
        print(f"Template has {q_count} questions — PASS")

    def test_fundraiser_section_heading_exists(self):
        """Fundraiser Settings heading should exist at order 44."""
        import sys
        sys.path.insert(0, "/app/backend")
        from models.questionnaires import QUESTIONNAIRE_TEMPLATES
        template = QUESTIONNAIRE_TEMPLATES["event_web_store_setup"]
        headings = [q["label"] for q in template["questions"] if q["type"] == "heading"]
        assert "Fundraiser Settings" in headings, f"Fundraiser Settings heading not found. Headings: {headings}"
        print("Fundraiser Settings heading found — PASS")

    def test_fundraiser_questions_present(self):
        """Key fundraiser questions must exist in the template."""
        import sys
        sys.path.insert(0, "/app/backend")
        from models.questionnaires import QUESTIONNAIRE_TEMPLATES
        template = QUESTIONNAIRE_TEMPLATES["event_web_store_setup"]
        labels = {q["label"] for q in template["questions"]}
        required_labels = [
            "Fundraiser Name",
            "Fundraiser Description",
            "Fundraiser Goal Amount ($)",
            "Should a fundraiser progress bar be shown on the store?",
            "Should customers be able to add a donation at checkout?",
            "Should a portion of each product sale be allocated to the fundraiser?",
        ]
        for lbl in required_labels:
            assert lbl in labels, f"Missing fundraiser question: '{lbl}'"
        print(f"All {len(required_labels)} required fundraiser questions found — PASS")

    def test_fundraiser_goal_amount_is_optional(self):
        """Fundraiser Goal Amount should NOT be required and description should mention 'Optional'."""
        import sys
        sys.path.insert(0, "/app/backend")
        from models.questionnaires import QUESTIONNAIRE_TEMPLATES
        template = QUESTIONNAIRE_TEMPLATES["event_web_store_setup"]
        goal_q = next(
            (q for q in template["questions"] if q["label"] == "Fundraiser Goal Amount ($)"),
            None
        )
        assert goal_q is not None, "Fundraiser Goal Amount ($) question not found"
        assert not goal_q.get("required", False), "Fundraiser Goal Amount should NOT be required"
        desc = goal_q.get("description", "")
        assert "Optional" in desc or "optional" in desc, (
            f"Fundraiser Goal Amount description should mention 'Optional'. Got: {desc!r}"
        )
        print("Fundraiser Goal Amount: not required + description mentions Optional — PASS")

    def test_section_5_stripe_connect_shifted(self):
        """Stripe Connect section heading should be at order 62 (shifted by 18)."""
        import sys
        sys.path.insert(0, "/app/backend")
        from models.questionnaires import QUESTIONNAIRE_TEMPLATES
        template = QUESTIONNAIRE_TEMPLATES["event_web_store_setup"]
        stripe_heading = next(
            (q for q in template["questions"]
             if q["type"] == "heading" and "Stripe" in q["label"]),
            None
        )
        assert stripe_heading is not None, "Stripe Connect heading not found"
        assert stripe_heading["order"] == 62, (
            f"Stripe Connect heading should be at order 62, got {stripe_heading['order']}"
        )
        print(f"Stripe Connect heading at order {stripe_heading['order']} — PASS")

    def test_section_6_final_approval_shifted(self):
        """Final Approval section heading should be at order 71."""
        import sys
        sys.path.insert(0, "/app/backend")
        from models.questionnaires import QUESTIONNAIRE_TEMPLATES
        template = QUESTIONNAIRE_TEMPLATES["event_web_store_setup"]
        final_heading = next(
            (q for q in template["questions"]
             if q["type"] == "heading" and "Final" in q["label"]),
            None
        )
        assert final_heading is not None, "Final Approval heading not found"
        assert final_heading["order"] == 71, (
            f"Final Approval heading should be at order 71, got {final_heading['order']}"
        )
        print(f"Final Approval heading at order {final_heading['order']} — PASS")


# ── Questionnaire Status Endpoint ──────────────────────────────────────────────

class TestGetQuestionnaireStatus:
    """GET /{webstore_id}/questionnaire tests."""

    def test_get_questionnaire_status_before_send(self, auth_headers, event_store):
        """Before sending, questionnaire should return linked=false."""
        store_id = event_store["id"]
        resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["linked"] == False, f"Expected linked=false, got {data}"
        assert data["questionnaire"] is None
        print("GET questionnaire status before send: linked=false — PASS")

    def test_get_questionnaire_not_found_for_invalid_store(self, auth_headers):
        """Should return 404 for a non-existent store."""
        resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/nonexistent-store-id/questionnaire",
            headers=auth_headers,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("GET questionnaire for non-existent store: 404 — PASS")

    def test_business_store_questionnaire_unaffected(self, auth_headers, business_store):
        """Business store questionnaire endpoint should return linked=false (not error)."""
        store_id = business_store["id"]
        resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["linked"] == False, f"Business store should have linked=false, got {data}"
        print("Business store questionnaire: linked=false (unaffected) — PASS")


# ── Send Questionnaire Endpoint ────────────────────────────────────────────────

class TestSendQuestionnaire:
    """POST /{webstore_id}/questionnaire/send tests."""

    @pytest.fixture(scope="class")
    def send_result(self, auth_headers, event_store):
        """Send questionnaire once for this test class."""
        store_id = event_store["id"]
        origin = BASE_URL
        resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/send",
            json={"email": "test@example.com", "public_url": origin},
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Send questionnaire failed: {resp.text}"
        return resp.json()

    def test_send_returns_questionnaire_id(self, send_result):
        """Send response must include questionnaire_id."""
        assert "questionnaire_id" in send_result, f"No questionnaire_id in: {send_result}"
        assert send_result["questionnaire_id"], "questionnaire_id is empty"
        print(f"questionnaire_id: {send_result['questionnaire_id']} — PASS")

    def test_send_returns_link(self, send_result):
        """Send response must include a questionnaire link."""
        assert "link" in send_result, f"No link in: {send_result}"
        assert "/questionnaire/" in send_result["link"], (
            f"Link should contain /questionnaire/, got: {send_result['link']}"
        )
        print(f"Link: {send_result['link']} — PASS")

    def test_status_linked_true_after_send(self, auth_headers, event_store, send_result):
        """GET /questionnaire should return linked=true after sending."""
        store_id = event_store["id"]
        resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["linked"] == True, f"Expected linked=true after send, got {data}"
        assert data["questionnaire"] is not None
        print("GET questionnaire after send: linked=true — PASS")

    def test_questionnaire_has_87_questions(self, auth_headers, event_store):
        """The linked questionnaire should have 87 questions."""
        store_id = event_store["id"]
        # Get questionnaire status to get id
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        # Fetch full questionnaire via public endpoint
        public_resp = requests.get(
            f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}",
        )
        assert public_resp.status_code == 200, f"Failed to fetch questionnaire: {public_resp.text}"
        q_data = public_resp.json()
        q_count = len(q_data.get("questions", []))
        assert q_count == 87, f"Expected 87 questions, got {q_count}"
        print(f"Public questionnaire has {q_count} questions — PASS")

    def test_questionnaire_has_prefill_answers(self, auth_headers, event_store):
        """Questionnaire should have prefill_answers with event_name."""
        store_id = event_store["id"]
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        # Fetch full questionnaire via public endpoint
        public_resp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        assert public_resp.status_code == 200
        q_data = public_resp.json()
        prefills = q_data.get("prefill_answers") or {}
        assert len(prefills) > 0, "Expected at least 1 prefill answer"
        print(f"prefill_answers count: {len(prefills)} — PASS")

    def test_questionnaire_has_locked_answer_ids(self, auth_headers, event_store):
        """Questionnaire should have locked_answer_ids for profit field."""
        store_id = event_store["id"]
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        # Fetch full questionnaire via public endpoint
        public_resp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        assert public_resp.status_code == 200
        q_data = public_resp.json()
        locked_ids = q_data.get("locked_answer_ids") or []
        assert len(locked_ids) >= 1, f"Expected at least 1 locked_answer_id, got {locked_ids}"
        print(f"locked_answer_ids count: {len(locked_ids)} — PASS")

    def test_event_name_prefilled(self, auth_headers, event_store):
        """Event Name question should be prefilled with the store's event_name."""
        store_id = event_store["id"]
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        public_resp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        assert public_resp.status_code == 200
        q_data = public_resp.json()
        
        # Find "Event Name" question
        event_name_q = next(
            (q for q in q_data["questions"] if q["label"] == "Event Name"),
            None
        )
        assert event_name_q is not None, "Event Name question not found"
        prefills = q_data.get("prefill_answers") or {}
        prefill_val = prefills.get(event_name_q["id"])
        assert prefill_val == "Test Gala 2026", (
            f"Expected 'Test Gala 2026' prefill for Event Name, got {prefill_val!r}"
        )
        print(f"Event Name prefilled with '{prefill_val}' — PASS")

    def test_profit_field_is_locked(self, auth_headers, event_store):
        """'If adding profit...' question should be in locked_answer_ids."""
        store_id = event_store["id"]
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        public_resp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        assert public_resp.status_code == 200
        q_data = public_resp.json()
        
        profit_q = next(
            (q for q in q_data["questions"]
             if "profit" in q["label"].lower() and "adding" in q["label"].lower()),
            None
        )
        assert profit_q is not None, "Profit per item question not found"
        locked_ids = set(q_data.get("locked_answer_ids") or [])
        assert profit_q["id"] in locked_ids, (
            f"Profit field {profit_q['id']} not in locked_answer_ids: {locked_ids}"
        )
        # Also verify it is prefilled with the correct value
        prefills = q_data.get("prefill_answers") or {}
        prefill_val = prefills.get(profit_q["id"])
        assert prefill_val and "8.50" in str(prefill_val), (
            f"Expected profit prefill to contain '8.50', got {prefill_val!r}"
        )
        print(f"Profit field locked and prefilled with '{prefill_val}' — PASS")

    def test_idempotency_second_send(self, auth_headers, event_store, send_result):
        """Sending questionnaire again should reuse the same questionnaire_id."""
        store_id = event_store["id"]
        first_questionnaire_id = send_result["questionnaire_id"]
        
        # Send again
        resp2 = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/send",
            json={"email": "test@example.com", "public_url": BASE_URL},
            headers=auth_headers,
        )
        assert resp2.status_code == 200, f"Second send failed: {resp2.text}"
        second_id = resp2.json()["questionnaire_id"]
        assert second_id == first_questionnaire_id, (
            f"Idempotency failure: first={first_questionnaire_id}, second={second_id}"
        )
        print(f"Idempotency verified: same questionnaire_id {second_id} — PASS")


# ── Apply Answers Endpoint ─────────────────────────────────────────────────────

class TestApplyQuestionnaireAnswers:
    """POST /{webstore_id}/questionnaire/apply-answers tests."""

    def test_apply_answers_with_no_responses_returns_404(self, auth_headers, event_store):
        """Apply-answers should return 404 when no responses exist."""
        store_id = event_store["id"]
        # Make sure questionnaire is sent first
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/send",
            json={"email": "test@example.com", "public_url": BASE_URL},
            headers=auth_headers,
        )
        resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        # If there are no responses, should return 404
        assert resp.status_code == 404, (
            f"Expected 404 when no responses, got {resp.status_code}: {resp.text}"
        )
        print("apply-answers with no responses: 404 — PASS")

    def test_apply_answers_unlinked_store_returns_404(self, auth_headers, business_store):
        """Apply-answers on a store with no linked questionnaire should return 404."""
        store_id = business_store["id"]
        resp = requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers",
            headers=auth_headers,
        )
        assert resp.status_code == 404, (
            f"Expected 404 for unlinked store, got {resp.status_code}: {resp.text}"
        )
        print("apply-answers for unlinked store: 404 — PASS")


# ── Fundraiser Section in Public Questionnaire ─────────────────────────────────

class TestFundraiserInPublicQuestionnaire:
    """Test fundraiser questions are accessible in the public questionnaire endpoint."""

    def test_public_questionnaire_has_fundraiser_section(self, auth_headers, event_store):
        """Public questionnaire should have Fundraiser Settings heading."""
        store_id = event_store["id"]
        # Ensure questionnaire is created
        requests.post(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/send",
            json={"email": "test@example.com", "public_url": BASE_URL},
            headers=auth_headers,
        )
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        public_resp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        assert public_resp.status_code == 200
        q_data = public_resp.json()
        
        headings = [q["label"] for q in q_data["questions"] if q["type"] == "heading"]
        assert "Fundraiser Settings" in headings, (
            f"Fundraiser Settings heading not found in public questionnaire. Headings: {headings}"
        )
        print("Public questionnaire has Fundraiser Settings heading — PASS")

    def test_public_questionnaire_has_fundraiser_name(self, auth_headers, event_store):
        """Public questionnaire should have Fundraiser Name question."""
        store_id = event_store["id"]
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        public_resp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        q_data = public_resp.json()
        labels = [q["label"] for q in q_data["questions"]]
        assert "Fundraiser Name" in labels, f"Fundraiser Name not found. Labels sample: {labels[:10]}"
        assert "Fundraiser Description" in labels, "Fundraiser Description not found"
        assert "Fundraiser Goal Amount ($)" in labels, "Fundraiser Goal Amount ($) not found"
        print("Public questionnaire has Fundraiser Name, Description, Goal Amount — PASS")

    def test_public_questionnaire_fundraiser_goal_not_required(self, auth_headers, event_store):
        """Fundraiser Goal Amount should not be required in the public questionnaire."""
        store_id = event_store["id"]
        status_resp = requests.get(
            f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire",
            headers=auth_headers,
        )
        questionnaire_id = status_resp.json()["questionnaire"]["id"]
        public_resp = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
        q_data = public_resp.json()
        goal_q = next(
            (q for q in q_data["questions"] if q["label"] == "Fundraiser Goal Amount ($)"),
            None
        )
        assert goal_q is not None, "Fundraiser Goal Amount ($) question not found"
        assert not goal_q.get("required", False), "Fundraiser Goal Amount should NOT be required"
        print("Fundraiser Goal Amount is not required in public questionnaire — PASS")
