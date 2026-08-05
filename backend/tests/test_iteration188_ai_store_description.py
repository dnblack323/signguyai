"""
Tests for POST /api/ai/generate - store_description_rewrite tool
Also includes regression check for branding_kit_generator tool
"""
import pytest
import requests
import os

# Load from frontend/.env if not in environment
def _get_base_url():
    url = os.environ.get('REACT_APP_BACKEND_URL', '')
    if not url:
        env_path = '/app/frontend/.env'
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        url = line.strip().split('=', 1)[1]
                        break
    return url.rstrip('/')

BASE_URL = _get_base_url()

def get_auth_token():
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "thesigntistslab@gmail.com",
        "password": "password123"
    })
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json().get("token") or resp.json().get("access_token")

@pytest.fixture(scope="module")
def auth_token():
    return get_auth_token()

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

STORE_DESC_PAYLOAD = {
    "tool": "store_description_rewrite",
    "input_data": {
        "store_name": "Riverside Spirit Wear",
        "store_type": "fundraiser",
        "owner_name": "Riverside High School",
        "existing_description": "",
        "products": "T-shirts, Hoodies, Hats"
    }
}

# Test 1: Returns 401 without auth token
def test_store_description_rewrite_no_auth():
    resp = requests.post(f"{BASE_URL}/api/ai/generate", json=STORE_DESC_PAYLOAD)
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}: {resp.text}"
    print("PASS: 401 without auth token")

# Test 2: Returns 200 with valid auth
def test_store_description_rewrite_200(auth_headers):
    resp = requests.post(f"{BASE_URL}/api/ai/generate", json=STORE_DESC_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    print("PASS: 200 with valid auth")

# Test 3: Response contains 'content' key
def test_store_description_rewrite_has_content(auth_headers):
    resp = requests.post(f"{BASE_URL}/api/ai/generate", json=STORE_DESC_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data, f"Missing 'content' key in response: {data}"
    print(f"PASS: response has 'content' key. Preview: {data['content'][:80]}")

# Test 4: Content is at least 80 characters
def test_store_description_rewrite_min_length(auth_headers):
    resp = requests.post(f"{BASE_URL}/api/ai/generate", json=STORE_DESC_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 200
    content = resp.json().get("content", "")
    assert len(content) >= 80, f"Content too short ({len(content)} chars): {content}"
    print(f"PASS: content length={len(content)} chars")

# Test 5: Content is not an error string
def test_store_description_rewrite_not_error(auth_headers):
    resp = requests.post(f"{BASE_URL}/api/ai/generate", json=STORE_DESC_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 200
    content = resp.json().get("content", "").lower()
    assert "unknown tool" not in content, f"Got 'Unknown tool' error in content"
    assert "error" not in content[:30], f"Content starts with error: {content[:80]}"
    print("PASS: content is not an error message")

# Test 6: Regression - branding_kit_generator still works
def test_branding_kit_generator_regression(auth_headers):
    payload = {
        "tool": "branding_kit_generator",
        "input_data": {
            "business_name": "Riverside Spirit Wear",
            "industry": "fundraiser"
        }
    }
    resp = requests.post(f"{BASE_URL}/api/ai/generate", json=payload, headers=auth_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "content" in data, f"Missing content: {data}"
    content = data["content"].lower()
    assert "unknown tool" not in content, "branding_kit_generator returned 'Unknown tool' error"
    print(f"PASS: branding_kit_generator regression OK. Content len={len(data['content'])}")
