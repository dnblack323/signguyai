"""
Questionnaires Feature Tests - Dynamic Form Builder
Tests all CRUD operations for questionnaires, templates, and public submission endpoints.
"""

import pytest
import requests
import os
import uuid
from backend.tests.test_credentials_helper import FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, TEST_CUSTOMER_EMAIL

# API URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = FALLBACK_TEST_EMAIL
TEST_PASSWORD = FALLBACK_TEST_PASSWORD


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for test user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Return headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def created_questionnaire_ids():
    """Track created questionnaires for cleanup"""
    return []


class TestHealthCheck:
    """Basic health check to verify API is accessible"""

    def test_api_accessible(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        # Accept 200 or 404 (health endpoint may not exist)
        assert response.status_code in [200, 404], f"API not accessible: {response.status_code}"
        print(f"API accessible at {BASE_URL}")


class TestTemplatesEndpoint:
    """Test GET /api/questionnaires/templates - Pre-built templates"""

    def test_get_templates_requires_auth(self):
        """Templates endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/questionnaires/templates")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Templates endpoint correctly requires auth")

    def test_get_templates_returns_three_templates(self, auth_headers):
        """Should return 3 pre-built templates: Vehicle Wrap, Sign Request, Apparel Order"""
        response = requests.get(
            f"{BASE_URL}/api/questionnaires/templates",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get templates: {response.status_code}"
        
        templates = response.json()
        assert isinstance(templates, list), "Templates should be a list"
        assert len(templates) == 3, f"Expected 3 templates, got {len(templates)}"
        
        # Verify template structure
        template_ids = [t["id"] for t in templates]
        assert "vehicle_wrap_intake" in template_ids, "Missing vehicle_wrap_intake template"
        assert "sign_request" in template_ids, "Missing sign_request template"
        assert "apparel_order" in template_ids, "Missing apparel_order template"
        
        # Verify each template has required fields
        for template in templates:
            assert "id" in template, "Template missing id"
            assert "name" in template, "Template missing name"
            assert "description" in template, "Template missing description"
            assert "category" in template, "Template missing category"
            assert "question_count" in template, "Template missing question_count"
            assert template["question_count"] > 0, f"Template {template['id']} has no questions"
        
        print(f"Templates returned: {[t['name'] for t in templates]}")

    def test_vehicle_wrap_template_has_14_questions(self, auth_headers):
        """Vehicle Wrap template should have 14 questions"""
        response = requests.get(
            f"{BASE_URL}/api/questionnaires/templates",
            headers=auth_headers
        )
        templates = response.json()
        vehicle_wrap = next((t for t in templates if t["id"] == "vehicle_wrap_intake"), None)
        assert vehicle_wrap is not None, "Vehicle wrap template not found"
        assert vehicle_wrap["question_count"] == 14, f"Expected 14 questions, got {vehicle_wrap['question_count']}"
        print(f"Vehicle Wrap template has {vehicle_wrap['question_count']} questions")

    def test_sign_request_template_has_9_questions(self, auth_headers):
        """Sign Request template should have 9 questions"""
        response = requests.get(
            f"{BASE_URL}/api/questionnaires/templates",
            headers=auth_headers
        )
        templates = response.json()
        sign_request = next((t for t in templates if t["id"] == "sign_request"), None)
        assert sign_request is not None, "Sign request template not found"
        assert sign_request["question_count"] == 9, f"Expected 9 questions, got {sign_request['question_count']}"
        print(f"Sign Request template has {sign_request['question_count']} questions")

    def test_apparel_order_template_has_9_questions(self, auth_headers):
        """Apparel Order template should have 9 questions"""
        response = requests.get(
            f"{BASE_URL}/api/questionnaires/templates",
            headers=auth_headers
        )
        templates = response.json()
        apparel = next((t for t in templates if t["id"] == "apparel_order"), None)
        assert apparel is not None, "Apparel order template not found"
        assert apparel["question_count"] == 9, f"Expected 9 questions, got {apparel['question_count']}"
        print(f"Apparel Order template has {apparel['question_count']} questions")


class TestCreateFromTemplate:
    """Test POST /api/questionnaires/from-template/{id}"""

    def test_create_from_vehicle_wrap_template(self, auth_headers, created_questionnaire_ids):
        """Create questionnaire from vehicle wrap template"""
        response = requests.post(
            f"{BASE_URL}/api/questionnaires/from-template/vehicle_wrap_intake",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to create from template: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "id" in data, "Response missing id"
        assert data["name"] == "Vehicle Wrap Intake Form", f"Wrong name: {data['name']}"
        assert data["category"] == "vehicle_wrap", f"Wrong category: {data['category']}"
        assert data["status"] == "draft", f"New questionnaire should be draft, got {data['status']}"
        assert len(data.get("questions", [])) == 14, f"Expected 14 questions, got {len(data.get('questions', []))}"
        
        created_questionnaire_ids.append(data["id"])
        print(f"Created questionnaire from vehicle_wrap template: {data['id']}")

    def test_create_from_sign_request_template(self, auth_headers, created_questionnaire_ids):
        """Create questionnaire from sign request template"""
        response = requests.post(
            f"{BASE_URL}/api/questionnaires/from-template/sign_request",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["name"] == "Sign Request Form", f"Wrong name: {data['name']}"
        assert data["category"] == "signage", f"Wrong category: {data['category']}"
        assert len(data.get("questions", [])) == 9, f"Expected 9 questions, got {len(data.get('questions', []))}"
        
        created_questionnaire_ids.append(data["id"])
        print(f"Created questionnaire from sign_request template: {data['id']}")

    def test_create_from_nonexistent_template_returns_404(self, auth_headers):
        """Creating from non-existent template returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/questionnaires/from-template/nonexistent_template",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Non-existent template correctly returns 404")


class TestQuestionnaireCRUD:
    """Test CRUD operations for questionnaires"""

    def test_list_questionnaires(self, auth_headers):
        """GET /api/questionnaires - List all questionnaires"""
        response = requests.get(
            f"{BASE_URL}/api/questionnaires",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to list: {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Listed {len(data)} questionnaires")

    def test_list_questionnaires_requires_auth(self):
        """List questionnaires requires authentication"""
        response = requests.get(f"{BASE_URL}/api/questionnaires")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("List endpoint correctly requires auth")

    def test_create_questionnaire(self, auth_headers, created_questionnaire_ids):
        """POST /api/questionnaires - Create new questionnaire"""
        payload = {
            "name": "TEST_Custom Test Form",
            "description": "A test questionnaire for testing",
            "category": "general",
            "questions": [
                {
                    "type": "text",
                    "label": "What is your name?",
                    "required": True
                },
                {
                    "type": "select",
                    "label": "Preferred contact method",
                    "required": False,
                    "options": [
                        {"value": "email", "label": "Email"},
                        {"value": "phone", "label": "Phone"}
                    ]
                }
            ],
            "thank_you_message": "Thanks for testing!"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/questionnaires",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200, f"Failed to create: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Custom Test Form"
        assert data["category"] == "general"
        assert len(data.get("questions", [])) == 2
        assert data["status"] == "draft"
        
        created_questionnaire_ids.append(data["id"])
        print(f"Created custom questionnaire: {data['id']}")
        return data["id"]

    def test_get_single_questionnaire(self, auth_headers, created_questionnaire_ids):
        """GET /api/questionnaires/{id} - Get specific questionnaire"""
        if not created_questionnaire_ids:
            pytest.skip("No questionnaire to get")
        
        q_id = created_questionnaire_ids[0]
        response = requests.get(
            f"{BASE_URL}/api/questionnaires/{q_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get: {response.status_code}"
        
        data = response.json()
        assert data["id"] == q_id
        print(f"Retrieved questionnaire: {data['name']}")

    def test_update_questionnaire(self, auth_headers, created_questionnaire_ids):
        """PUT /api/questionnaires/{id} - Update questionnaire"""
        if not created_questionnaire_ids:
            pytest.skip("No questionnaire to update")
        
        q_id = created_questionnaire_ids[0]
        update_payload = {
            "name": "TEST_Updated Form Name",
            "description": "Updated description"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/questionnaires/{q_id}",
            headers=auth_headers,
            json=update_payload
        )
        assert response.status_code == 200, f"Failed to update: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Updated Form Name"
        assert data["description"] == "Updated description"
        print(f"Updated questionnaire: {data['id']}")

    def test_update_questionnaire_status_to_active(self, auth_headers, created_questionnaire_ids):
        """Activate a questionnaire by updating status"""
        if not created_questionnaire_ids:
            pytest.skip("No questionnaire to activate")
        
        q_id = created_questionnaire_ids[0]
        response = requests.put(
            f"{BASE_URL}/api/questionnaires/{q_id}",
            headers=auth_headers,
            json={"status": "active"}
        )
        assert response.status_code == 200, f"Failed to activate: {response.status_code}"
        
        data = response.json()
        assert data["status"] == "active", f"Expected active, got {data['status']}"
        print(f"Activated questionnaire: {q_id}")


class TestPublicQuestionnaireEndpoints:
    """Test public endpoints for questionnaire submission"""

    def test_get_public_questionnaire_inactive_returns_404(self, auth_headers, created_questionnaire_ids):
        """Public endpoint returns 404 for inactive questionnaire"""
        # Create a draft questionnaire
        payload = {
            "name": "TEST_Draft Form",
            "category": "general",
            "questions": [{"type": "text", "label": "Test question", "required": True}]
        }
        create_response = requests.post(
            f"{BASE_URL}/api/questionnaires",
            headers=auth_headers,
            json=payload
        )
        assert create_response.status_code == 200
        draft_id = create_response.json()["id"]
        created_questionnaire_ids.append(draft_id)
        
        # Try to access publicly
        public_response = requests.get(f"{BASE_URL}/api/questionnaires/public/{draft_id}")
        assert public_response.status_code == 404, f"Expected 404 for inactive, got {public_response.status_code}"
        print("Draft questionnaire correctly not accessible publicly")

    def test_get_public_questionnaire_active(self, auth_headers, created_questionnaire_ids):
        """Public endpoint returns questionnaire for active forms"""
        if not created_questionnaire_ids:
            pytest.skip("No active questionnaire")
        
        # Use the first one which we activated earlier
        q_id = created_questionnaire_ids[0]
        
        response = requests.get(f"{BASE_URL}/api/questionnaires/public/{q_id}")
        assert response.status_code == 200, f"Failed to get public questionnaire: {response.status_code}"
        
        data = response.json()
        assert "id" in data
        assert "questions" in data
        # Should not include sensitive fields
        assert "tenant_id" not in data, "Public endpoint should not expose tenant_id"
        assert "created_by" not in data, "Public endpoint should not expose created_by"
        print(f"Public questionnaire accessible: {data['name']}")

    def test_submit_public_questionnaire(self, auth_headers, created_questionnaire_ids):
        """POST /api/questionnaires/public/{id}/submit - Submit response"""
        if not created_questionnaire_ids:
            pytest.skip("No questionnaire available")
        
        # Use the active questionnaire
        q_id = created_questionnaire_ids[0]
        
        # First get the questionnaire to see question IDs
        get_response = requests.get(f"{BASE_URL}/api/questionnaires/public/{q_id}")
        if get_response.status_code != 200:
            pytest.skip(f"Questionnaire not accessible publicly: {get_response.status_code}")
        
        questionnaire = get_response.json()
        questions = questionnaire.get("questions", [])
        
        # Build answers for required questions
        answers = {}
        for q in questions:
            if q.get("required") and q.get("type") not in ["heading", "paragraph"]:
                if q.get("type") in ["select", "radio"]:
                    options = q.get("options", [])
                    if options:
                        answers[q["id"]] = options[0]["value"]
                    else:
                        answers[q["id"]] = "test_value"
                elif q.get("type") in ["multi_select", "checkbox"]:
                    options = q.get("options", [])
                    if options:
                        answers[q["id"]] = [options[0]["value"]]
                    else:
                        answers[q["id"]] = ["test_value"]
                else:
                    answers[q["id"]] = "Test answer"
        
        submission_payload = {
            "questionnaire_id": q_id,
            "answers": answers,
            "customer_name": "Test Customer",
            "customer_email": TEST_CUSTOMER_EMAIL
        }
        
        response = requests.post(
            f"{BASE_URL}/api/questionnaires/public/{q_id}/submit",
            json=submission_payload
        )
        assert response.status_code == 200, f"Failed to submit: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should have thank you message"
        assert "response_id" in data, "Response should have response_id"
        print(f"Submitted response successfully: {data['response_id']}")
        return data["response_id"]


class TestResponseManagement:
    """Test response retrieval endpoints"""

    def test_get_questionnaire_responses(self, auth_headers, created_questionnaire_ids):
        """GET /api/questionnaires/{id}/responses - Get all responses"""
        if not created_questionnaire_ids:
            pytest.skip("No questionnaire available")
        
        q_id = created_questionnaire_ids[0]
        response = requests.get(
            f"{BASE_URL}/api/questionnaires/{q_id}/responses",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed to get responses: {response.status_code}"
        
        data = response.json()
        assert "responses" in data, "Response should contain 'responses' field"
        assert "questionnaire_name" in data, "Response should contain questionnaire_name"
        print(f"Retrieved {len(data['responses'])} responses for questionnaire")

    def test_responses_requires_auth(self, created_questionnaire_ids):
        """Responses endpoint requires authentication"""
        if not created_questionnaire_ids:
            pytest.skip("No questionnaire")
        
        q_id = created_questionnaire_ids[0]
        response = requests.get(f"{BASE_URL}/api/questionnaires/{q_id}/responses")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("Responses endpoint correctly requires auth")


class TestDeleteQuestionnaire:
    """Test delete operations - run last"""

    def test_delete_questionnaire(self, auth_headers, created_questionnaire_ids):
        """DELETE /api/questionnaires/{id} - Delete questionnaire"""
        if not created_questionnaire_ids:
            pytest.skip("No questionnaire to delete")
        
        # Delete only TEST_ prefixed questionnaires
        for q_id in list(created_questionnaire_ids):
            # Get questionnaire first to check if it's a test one
            get_response = requests.get(
                f"{BASE_URL}/api/questionnaires/{q_id}",
                headers=auth_headers
            )
            if get_response.status_code == 200:
                q_data = get_response.json()
                if "TEST_" in q_data.get("name", ""):
                    response = requests.delete(
                        f"{BASE_URL}/api/questionnaires/{q_id}",
                        headers=auth_headers
                    )
                    assert response.status_code == 200, f"Failed to delete: {response.status_code}"
                    print(f"Deleted test questionnaire: {q_id}")
                    created_questionnaire_ids.remove(q_id)

    def test_delete_nonexistent_returns_404(self, auth_headers):
        """Deleting non-existent questionnaire returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(
            f"{BASE_URL}/api/questionnaires/{fake_id}",
            headers=auth_headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("Non-existent questionnaire delete correctly returns 404")


class TestQuestionnaireValidation:
    """Test validation and edge cases"""

    def test_create_questionnaire_without_name_fails(self, auth_headers):
        """Creating questionnaire without name should fail"""
        payload = {
            "category": "general",
            "questions": []
        }
        response = requests.post(
            f"{BASE_URL}/api/questionnaires",
            headers=auth_headers,
            json=payload
        )
        # Should return 422 (validation error) or 400
        assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}"
        print("Questionnaire creation correctly validates required name field")

    def test_question_types_supported(self, auth_headers, created_questionnaire_ids):
        """Test all question types are supported"""
        question_types = [
            "text", "textarea", "number", "email", "phone",
            "select", "multi_select", "radio", "checkbox",
            "date", "file_upload", "heading", "paragraph"
        ]
        
        questions = []
        for i, q_type in enumerate(question_types):
            q = {
                "type": q_type,
                "label": f"Test {q_type} question",
                "order": i
            }
            if q_type in ["select", "multi_select", "radio", "checkbox"]:
                q["options"] = [{"value": "opt1", "label": "Option 1"}]
            questions.append(q)
        
        payload = {
            "name": "TEST_All Question Types",
            "category": "general",
            "questions": questions
        }
        
        response = requests.post(
            f"{BASE_URL}/api/questionnaires",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 200, f"Failed to create with all types: {response.status_code} - {response.text}"
        
        data = response.json()
        assert len(data["questions"]) == len(question_types), "Not all question types saved"
        created_questionnaire_ids.append(data["id"])
        
        print(f"All {len(question_types)} question types supported")


# Cleanup fixture to run at the end
@pytest.fixture(scope="module", autouse=True)
def cleanup(auth_headers, created_questionnaire_ids):
    """Cleanup TEST_ prefixed questionnaires after all tests"""
    yield
    # Cleanup runs after all tests
    if auth_headers and created_questionnaire_ids:
        for q_id in created_questionnaire_ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/questionnaires/{q_id}",
                    headers=auth_headers
                )
            except Exception:
                pass
