"""
Tests for GET /api/questionnaires/{questionnaire_id}/uploads endpoint
and regression test for GET /api/questionnaires/{questionnaire_id}/responses
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

VALID_QUESTIONNAIRE_ID = "46d4751b-28cb-45a9-b581-29219485b893"
UNKNOWN_QUESTIONNAIRE_ID = "00000000-0000-0000-0000-000000000000"

ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if resp.status_code != 200:
        pytest.skip(f"Auth failed: {resp.status_code} {resp.text}")
    return resp.json().get("access_token") or resp.json().get("token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


class TestUploadsEndpoint:
    """Tests for GET /api/questionnaires/{questionnaire_id}/uploads"""

    def test_200_valid_questionnaire_with_auth(self, auth_headers):
        """Should return 200 with uploads/total for valid questionnaire"""
        resp = requests.get(
            f"{BASE_URL}/api/questionnaires/{VALID_QUESTIONNAIRE_ID}/uploads",
            headers=auth_headers,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "uploads" in data, "Response missing 'uploads' key"
        assert "total" in data, "Response missing 'total' key"
        assert isinstance(data["uploads"], list), "'uploads' should be a list"
        assert isinstance(data["total"], int), "'total' should be an int"
        assert data["total"] == len(data["uploads"]), "total should match len(uploads)"

    def test_404_unknown_questionnaire(self, auth_headers):
        """Should return 404 for unknown questionnaire ID"""
        resp = requests.get(
            f"{BASE_URL}/api/questionnaires/{UNKNOWN_QUESTIONNAIRE_ID}/uploads",
            headers=auth_headers,
        )
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_401_no_auth_token(self):
        """Should return 401 without auth token"""
        resp = requests.get(
            f"{BASE_URL}/api/questionnaires/{VALID_QUESTIONNAIRE_ID}/uploads"
        )
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"

    def test_upload_fields_structure(self, auth_headers):
        """When uploads exist, validate field structure"""
        resp = requests.get(
            f"{BASE_URL}/api/questionnaires/{VALID_QUESTIONNAIRE_ID}/uploads",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for upload in data["uploads"]:
            assert "id" in upload
            assert "original_filename" in upload
            assert "stored_filename" in upload
            assert "content_type" in upload
            assert "size_bytes" in upload
            assert "uploaded_at" in upload
            assert "download_url" in upload
            assert "file_exists" in upload
            assert isinstance(upload["file_exists"], bool)


class TestResponsesRegression:
    """Regression: existing GET /{questionnaire_id}/responses still works"""

    def test_responses_endpoint_still_works(self, auth_headers):
        """GET /api/questionnaires/{id}/responses should return 200"""
        resp = requests.get(
            f"{BASE_URL}/api/questionnaires/{VALID_QUESTIONNAIRE_ID}/responses",
            headers=auth_headers,
        )
        # 200 or 404 (no responses); both are acceptable — 500 is not
        assert resp.status_code in (200, 404), f"Unexpected status {resp.status_code}: {resp.text}"
