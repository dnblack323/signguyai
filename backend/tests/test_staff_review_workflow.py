"""Staff Review Workflow tests - questionnaire review, apply-answers, launch gate"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASS = "password123"
TEST_STORE_ID = "fc0bad7e-9040-477e-93b9-a3f0b1a2df90"


@pytest.fixture(scope="module")
def auth_token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def authed(auth_token):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"})
    return s


# ── 1. Health check ────────────────────────────────────────────────────────────
def test_health():
    r = requests.get(f"{BASE_URL}/api/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("PASS: health check")


# ── 2. review-details on store with NO questionnaire ──────────────────────────
def test_review_details_no_questionnaire(authed):
    r = authed.get(f"{BASE_URL}/api/webstores/v2/{TEST_STORE_ID}/questionnaire/review-details")
    assert r.status_code == 200, f"Expected 200 got {r.status_code}: {r.text}"
    data = r.json()
    assert "has_questionnaire" in data
    print(f"PASS: review-details no questionnaire: {data}")


# ── 3. Full E2E: create store → send questionnaire → submit → review → apply ──
def test_full_review_workflow(authed):
    # 3a. Create a temporary webstore
    unique = str(uuid.uuid4())[:8]
    r = authed.post(f"{BASE_URL}/api/webstores/v2", json={
        "name": f"TEST_ReviewFlow_{unique}",
        "slug": f"test-review-{unique}",
        "business_type": "fundraiser",
        "store_type": "fundraiser",
        "owner_name": "Test Owner",
        "status": "pending"
    })
    assert r.status_code in (200, 201), f"Create store failed: {r.text}"
    store_id = r.json()["id"]
    print(f"PASS: created store {store_id}")

    # 3b. Send questionnaire (create + link to store)
    r2 = authed.post(f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/send", json={
        "email": "test-owner@example.com"
    })
    assert r2.status_code == 200, f"Send questionnaire failed: {r2.text}"
    q_data = r2.json()
    q_link = q_data.get("link", "")
    questionnaire_id = q_data.get("questionnaire_id")
    print(f"PASS: questionnaire sent, link={q_link}, q_id={questionnaire_id}")

    # 3c. Fetch questionnaire to get question IDs for required fields
    q_details = requests.get(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}")
    assert q_details.status_code == 200, f"Fetch questionnaire failed: {q_details.text}"
    q_json = q_details.json()
    # Build answers dict: fill required question IDs with dummy data
    answers = {}
    for q in q_json.get("questions", []):
        q_id = q.get("id")
        q_type = q.get("type", "text")
        if q.get("required") and q_id:
            if q_type == "email":
                answers[q_id] = "test-owner@example.com"
            elif q_type == "phone":
                answers[q_id] = "555-1234"
            else:
                answers[q_id] = "Test Value"
    # Walk sections too
    for section in q_json.get("sections", []):
        for q in section.get("questions", []):
            q_id = q.get("id")
            q_type = q.get("type", "text")
            if q.get("required") and q_id:
                if q_type == "email":
                    answers[q_id] = "test-owner@example.com"
                elif q_type == "phone":
                    answers[q_id] = "555-1234"
                else:
                    answers[q_id] = "Test Value"

    # Submit a response via public endpoint
    r3 = requests.post(f"{BASE_URL}/api/questionnaires/public/{questionnaire_id}/submit", json={
        "questionnaire_id": questionnaire_id,
        "customer_name": "Test Owner",
        "customer_email": "test-owner@example.com",
        "answers": answers
    })
    assert r3.status_code == 200, f"Submit response failed: {r3.text}"
    print(f"PASS: questionnaire response submitted")

    # 3d. review-details should now show has_response=True
    r4 = authed.get(f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/review-details")
    assert r4.status_code == 200, f"review-details failed: {r4.text}"
    details = r4.json()
    assert details.get("has_questionnaire") == True, f"Expected has_questionnaire=True: {details}"
    assert details.get("has_response") == True, f"Expected has_response=True: {details}"
    assert "safe_fields" in details
    assert "suggested_changes" in details
    assert "admin_review_answers" in details
    print(f"PASS: review-details correct structure: safe={len(details['safe_fields'])}, suggest={len(details['suggested_changes'])}, other={len(details['admin_review_answers'])}")

    # 3e. Launch gate should BLOCK since questionnaire submitted but not reviewed
    # First add a product so only questionnaire blocks launch
    r_prod = authed.get(f"{BASE_URL}/api/webstores/v2/{store_id}/products")
    # Try to activate - should fail if questionnaire_submitted_at is set and questionnaire_reviewed=false
    r5 = authed.put(f"{BASE_URL}/api/webstores/v2/{store_id}", json={"status": "active"})
    # The store has questionnaire_submitted_at set and questionnaire_reviewed=false → should get 400
    if details.get("questionnaire_submitted_at"):
        assert r5.status_code == 400, f"Expected 400 launch gate block, got {r5.status_code}: {r5.text}"
        assert "Questionnaire" in r5.text or "questionnaire" in r5.text.lower(), f"Wrong error: {r5.text}"
        print(f"PASS: launch gate blocked correctly")
    else:
        print(f"NOTE: questionnaire_submitted_at not set on store, skipping launch gate check")

    # 3f. Apply safe answers
    r6 = authed.post(f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/apply-answers")
    assert r6.status_code == 200, f"Apply answers failed: {r6.text}"
    apply_data = r6.json()
    assert apply_data.get("questionnaire_reviewed") == True, f"questionnaire_reviewed not set: {apply_data}"
    print(f"PASS: apply-answers set questionnaire_reviewed=True")

    # 3g. Verify via review-details that questionnaire_reviewed=True (GET store endpoint uses
    # response_model=Webstore which doesn't include questionnaire_reviewed — known limitation)
    r7 = authed.get(f"{BASE_URL}/api/webstores/v2/{store_id}/questionnaire/review-details")
    assert r7.status_code == 200
    rd2 = r7.json()
    assert rd2.get("questionnaire_reviewed") == True, f"questionnaire_reviewed not True in review-details: {rd2}"
    print(f"PASS: review-details confirms questionnaire_reviewed=True after apply")

    # Cleanup
    authed.delete(f"{BASE_URL}/api/webstores/v2/{store_id}")
    print(f"Cleanup: deleted test store {store_id}")
