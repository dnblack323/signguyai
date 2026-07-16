"""
Iteration 186 backend tests:
1. POST /api/webstores/v2/{webstore_id}/questionnaire/send - idempotent resend for store with linked questionnaire
2. POST /api/stripe-connect/create-account - returns Stripe Connect URL
3. GET /api/stripe-connect/status - returns current Stripe status
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
WEBSTORE_ID = "fc0bad7e-9040-477e-93b9-a3f0b1a2df90"
ADMIN_EMAIL = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json().get("access_token") or resp.json().get("token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# --- Questionnaire send/resend ---

def test_questionnaire_send_with_email(auth_headers):
    """POST send questionnaire with an email body - should return email_sent: true, success: true"""
    payload = {"email": "test-resend@example.com"}
    resp = requests.post(
        f"{BASE_URL}/api/webstores/v2/{WEBSTORE_ID}/questionnaire/send",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("success") is True, f"success not True: {data}"
    assert data.get("email_sent") is True, f"email_sent not True: {data}"
    print(f"PASS questionnaire send: {data}")


def test_questionnaire_send_idempotent_resend(auth_headers):
    """Second call to send should also succeed (idempotent resend)"""
    payload = {"email": "test-resend2@example.com"}
    resp = requests.post(
        f"{BASE_URL}/api/webstores/v2/{WEBSTORE_ID}/questionnaire/send",
        json=payload,
        headers=auth_headers
    )
    assert resp.status_code == 200, f"Expected 200 on resend, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("success") is True, f"success not True on resend: {data}"
    print(f"PASS idempotent resend: {data}")


# --- Stripe Connect ---

def test_stripe_connect_status(auth_headers):
    """GET /api/stripe-connect/status returns 200 with status info"""
    resp = requests.get(f"{BASE_URL}/api/stripe-connect/status", headers=auth_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    # Expect some status-related fields
    assert "charges_enabled" in data or "status" in data or "connected" in data or "stripe_account_id" in data, \
        f"Unexpected response shape: {data}"
    print(f"PASS stripe connect status: {data}")


def test_stripe_connect_create_account(auth_headers):
    """POST /api/stripe-connect/create-account returns a Stripe onboarding URL"""
    payload = {
        "return_url": "https://sms-consent-demo.preview.emergentagent.com/settings?stripe_return=true",
        "refresh_url": "https://sms-consent-demo.preview.emergentagent.com/settings?stripe_refresh=true"
    }
    resp = requests.post(f"{BASE_URL}/api/stripe-connect/create-account", json=payload, headers=auth_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    url = data.get("url") or data.get("onboarding_url") or data.get("account_link_url")
    assert url, f"No URL in response: {data}"
    assert "stripe.com" in url, f"URL doesn't look like Stripe: {url}"
    print(f"PASS stripe create-account URL: {url[:80]}...")
