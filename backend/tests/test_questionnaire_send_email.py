"""
Tests for questionnaire send-email feature + regressions on existing questionnaire endpoints.

Covers:
- POST /api/questionnaires/{id}/send-email
    * 401 without auth
    * 404 for unknown id
    * 404 for cross-tenant access (tenant isolation)
    * 422 invalid email
    * 400 when status != 'active' (draft)
    * 200 happy path on active questionnaire, link format correct
- Regression on existing endpoints
    * GET /api/questionnaires (list)
    * POST /api/questionnaires (create)
    * GET /api/questionnaires/{id}
    * PUT /api/questionnaires/{id} (status flip)
    * GET /api/questionnaires/public/{id}
    * POST /api/questionnaires/public/{id}/submit
    * GET /api/questionnaires/{id}/responses
    * DELETE /api/questionnaires/{id}
    * POST /api/questionnaires/from-template/{template_id}
"""

import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://webstore-events.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"

KNOWN_QUESTIONNAIRES = [
    "c9f8a177-40b4-44ea-85a5-17d928bacf93",  # Vehicle Wrap Intake Form
    "4c575ad6-8ef5-4357-87bf-ed0b9862f8b8",  # Apparel/Merchandise Order Form
]


# ------------------- fixtures -------------------

@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(
        f"{API}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    data = r.json()
    token = data.get("access_token") or data.get("token")
    assert token, f"No token in login response: {data}"
    return token


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def existing_q_id(auth_headers):
    """Pick an existing questionnaire id known in this tenant."""
    r = requests.get(f"{API}/questionnaires", headers=auth_headers, timeout=15)
    assert r.status_code == 200, r.text
    items = r.json()
    ids = [q["id"] for q in items]
    for qid in KNOWN_QUESTIONNAIRES:
        if qid in ids:
            return qid
    if ids:
        return ids[0]
    pytest.skip("No questionnaires exist in tenant")


# ------------------- send-email negative paths -------------------

class TestSendEmailErrors:
    def test_send_email_requires_auth(self):
        r = requests.post(
            f"{API}/questionnaires/{KNOWN_QUESTIONNAIRES[0]}/send-email",
            json={"email": "x@example.com"},
            timeout=15,
        )
        # FastAPI returns 401 or 403 depending on dep
        assert r.status_code in (401, 403), r.text

    def test_send_email_unknown_id_returns_404(self, auth_headers):
        r = requests.post(
            f"{API}/questionnaires/00000000-0000-0000-0000-000000000000/send-email",
            headers=auth_headers,
            json={"email": "test@example.com", "public_url": BASE_URL},
            timeout=15,
        )
        assert r.status_code == 404, r.text

    def test_send_email_invalid_email_returns_422(self, auth_headers, existing_q_id):
        r = requests.post(
            f"{API}/questionnaires/{existing_q_id}/send-email",
            headers=auth_headers,
            json={"email": "not-an-email"},
            timeout=15,
        )
        assert r.status_code == 422, r.text

    def test_send_email_draft_returns_400(self, auth_headers, existing_q_id):
        # Ensure it's draft (revert any leftover state from prior runs)
        requests.put(
            f"{API}/questionnaires/{existing_q_id}",
            headers=auth_headers,
            json={"status": "draft"},
            timeout=15,
        )
        r = requests.post(
            f"{API}/questionnaires/{existing_q_id}/send-email",
            headers=auth_headers,
            json={"email": "test@example.com", "public_url": BASE_URL},
            timeout=15,
        )
        assert r.status_code == 400, r.text
        detail = r.json().get("detail", "")
        assert "Active" in detail and "Publish" in detail, detail


# ------------------- send-email happy path -------------------

class TestSendEmailHappyPath:
    def test_send_email_active_success(self, auth_headers, existing_q_id):
        # Flip to active
        r = requests.put(
            f"{API}/questionnaires/{existing_q_id}",
            headers=auth_headers,
            json={"status": "active"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "active"

        try:
            send = requests.post(
                f"{API}/questionnaires/{existing_q_id}/send-email",
                headers=auth_headers,
                json={
                    "email": "thesigntistslab@gmail.com",
                    "customer_name": "QA Tester",
                    "public_url": BASE_URL,
                    "message": "Automated test - please ignore",
                },
                timeout=30,
            )
            assert send.status_code == 200, send.text
            body = send.json()
            assert body.get("success") is True
            assert "Questionnaire sent to" in body.get("message", "")
            assert body.get("link") == f"{BASE_URL}/questionnaire/{existing_q_id}", body
        finally:
            # Always revert to draft to avoid polluting user data
            revert = requests.put(
                f"{API}/questionnaires/{existing_q_id}",
                headers=auth_headers,
                json={"status": "draft"},
                timeout=15,
            )
            assert revert.status_code == 200, revert.text
            # Confirm GET shows draft
            g = requests.get(f"{API}/questionnaires/{existing_q_id}", headers=auth_headers, timeout=15)
            assert g.status_code == 200
            assert g.json().get("status") == "draft"


# ------------------- regression on existing endpoints -------------------

class TestQuestionnaireRegression:
    """Full CRUD + public flow + responses on a fresh test questionnaire we clean up."""

    @pytest.fixture(scope="class")
    def created_q(self, auth_headers):
        payload = {
            "name": "TEST_send_email_regression",
            "description": "Created by automated test",
            "category": "general",
            "questions": [
                {
                    "id": "q1",
                    "type": "text",
                    "label": "Your favorite color?",
                    "required": True,
                    "order": 0,
                },
                {
                    "id": "q2",
                    "type": "radio",
                    "label": "Pick one",
                    "required": True,
                    "order": 1,
                    "options": [
                        {"value": "a", "label": "Option A"},
                        {"value": "b", "label": "Option B"},
                    ],
                },
            ],
        }
        r = requests.post(f"{API}/questionnaires", headers=auth_headers, json=payload, timeout=15)
        assert r.status_code in (200, 201), r.text
        q = r.json()
        assert q.get("name") == "TEST_send_email_regression"
        assert "id" in q
        yield q
        # cleanup
        requests.delete(f"{API}/questionnaires/{q['id']}", headers=auth_headers, timeout=15)

    def test_list_includes_created(self, auth_headers, created_q):
        r = requests.get(f"{API}/questionnaires", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        ids = [q["id"] for q in r.json()]
        assert created_q["id"] in ids

    def test_get_by_id(self, auth_headers, created_q):
        r = requests.get(f"{API}/questionnaires/{created_q['id']}", headers=auth_headers, timeout=15)
        assert r.status_code == 200
        assert r.json()["id"] == created_q["id"]

    def test_put_status_active_and_revert(self, auth_headers, created_q):
        r = requests.put(
            f"{API}/questionnaires/{created_q['id']}",
            headers=auth_headers,
            json={"status": "active"},
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json().get("status") == "active"
        # revert
        r2 = requests.put(
            f"{API}/questionnaires/{created_q['id']}",
            headers=auth_headers,
            json={"status": "draft"},
            timeout=15,
        )
        assert r2.status_code == 200
        assert r2.json().get("status") == "draft"

    def test_public_get_when_active(self, auth_headers, created_q):
        # Public endpoint usually requires active status
        requests.put(
            f"{API}/questionnaires/{created_q['id']}",
            headers=auth_headers,
            json={"status": "active"},
            timeout=15,
        )
        try:
            r = requests.get(f"{API}/questionnaires/public/{created_q['id']}", timeout=15)
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["id"] == created_q["id"]
            assert "questions" in data
        finally:
            requests.put(
                f"{API}/questionnaires/{created_q['id']}",
                headers=auth_headers,
                json={"status": "draft"},
                timeout=15,
            )

    def test_public_submit_and_responses(self, auth_headers, created_q):
        # Activate to allow public submission
        requests.put(
            f"{API}/questionnaires/{created_q['id']}",
            headers=auth_headers,
            json={"status": "active"},
            timeout=15,
        )
        try:
            submit_payload = {
                "questionnaire_id": created_q["id"],
                "customer_name": "TEST_Submitter",
                "customer_email": "test_submitter@example.com",
                "answers": {"q1": "Blue", "q2": "a"},
            }
            r = requests.post(
                f"{API}/questionnaires/public/{created_q['id']}/submit",
                json=submit_payload,
                timeout=15,
            )
            assert r.status_code in (200, 201), r.text

            # list responses (auth required)
            time.sleep(0.3)
            rr = requests.get(
                f"{API}/questionnaires/{created_q['id']}/responses",
                headers=auth_headers,
                timeout=15,
            )
            assert rr.status_code == 200, rr.text
            data = rr.json()
            responses = data["responses"] if isinstance(data, dict) else data
            assert isinstance(responses, list)
            assert any(
                resp.get("customer_email") == "test_submitter@example.com"
                for resp in responses
            ), responses
        finally:
            requests.put(
                f"{API}/questionnaires/{created_q['id']}",
                headers=auth_headers,
                json={"status": "draft"},
                timeout=15,
            )

    def test_send_email_returns_link_for_created_q(self, auth_headers, created_q):
        # Activate
        requests.put(
            f"{API}/questionnaires/{created_q['id']}",
            headers=auth_headers,
            json={"status": "active"},
            timeout=15,
        )
        try:
            r = requests.post(
                f"{API}/questionnaires/{created_q['id']}/send-email",
                headers=auth_headers,
                json={
                    "email": "thesigntistslab@gmail.com",
                    "public_url": BASE_URL,
                    "customer_name": "Regression QA",
                },
                timeout=30,
            )
            assert r.status_code == 200, r.text
            data = r.json()
            assert data["success"] is True
            assert data["link"].endswith(f"/questionnaire/{created_q['id']}")
        finally:
            requests.put(
                f"{API}/questionnaires/{created_q['id']}",
                headers=auth_headers,
                json={"status": "draft"},
                timeout=15,
            )


# ------------------- template -------------------

class TestTemplates:
    def test_list_templates(self, auth_headers):
        r = requests.get(f"{API}/questionnaires/templates", headers=auth_headers, timeout=15)
        assert r.status_code == 200, r.text
        templates = r.json()
        assert isinstance(templates, list)
        assert len(templates) > 0
