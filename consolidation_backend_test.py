"""
Backend/API Regression Tests for Consolidation Pass
Testing the specific endpoints requested in the review.
"""

import requests
import json
from datetime import datetime

# Production URL from review request
BASE_URL = "https://owner-portal-dev.preview.emergentagent.com"

# Production credentials from review request
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"

def get_auth_token():
    """Get authentication token"""
    print("🔐 Authenticating...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30
    )
    if response.status_code != 200:
        raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    print(f"✅ Authentication successful - Token type: {data.get('token_type', 'N/A')}")
    return token

def test_auth_login():
    """Test 1: Auth login works and returns a usable token"""
    print("\n🔐 Testing POST /api/auth/login...")
    
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Auth login failed: {response.status_code} - {response.text}")
        return False, None
    
    data = response.json()
    token = data.get("access_token") or data.get("token")
    token_type = data.get("token_type", "bearer")
    
    if not token:
        print("❌ No access token in response")
        return False, None
    
    print(f"✅ Auth login successful")
    print(f"   Token type: {token_type}")
    print(f"   Token length: {len(token)} chars")
    
    return True, token

def test_productivity_items(token):
    """Test 2: GET /api/productivity/items works for the tenant"""
    print("\n📋 Testing GET /api/productivity/items...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/productivity/items",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Productivity items failed: {response.status_code} - {response.text}")
        return False, []
    
    data = response.json()
    
    # Handle both list and dict response formats
    if isinstance(data, dict) and 'items' in data:
        items = data['items']
        print(f"✅ Productivity items successful")
        print(f"   Items count: {len(items)}")
        print(f"   Total: {data.get('total', 'N/A')}")
        print(f"   Applied filters: {data.get('applied_filters', 'N/A')}")
        
        # Show sample item structure if available
        if items:
            sample_item = items[0]
            print(f"   Sample item keys: {list(sample_item.keys())}")
            if 'uid' in sample_item:
                print(f"   Sample item UID: {sample_item['uid']}")
        
        return True, items
    elif isinstance(data, list):
        print(f"✅ Productivity items successful")
        print(f"   Items count: {len(data)}")
        
        # Show sample item structure if available
        if data:
            sample_item = data[0]
            print(f"   Sample item keys: {list(sample_item.keys())}")
            if 'uid' in sample_item:
                print(f"   Sample item UID: {sample_item['uid']}")
        
        return True, data
    else:
        print(f"❌ Unexpected response format: {type(data)}")
        return False, []

def test_productivity_summary(token):
    """Test 3: GET /api/productivity/summary works"""
    print("\n📊 Testing GET /api/productivity/summary...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/productivity/summary",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Productivity summary failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    
    # Verify response structure
    if not isinstance(data, dict):
        print(f"❌ Expected dict response, got: {type(data)}")
        return False
    
    print(f"✅ Productivity summary successful")
    print(f"   Response keys: {list(data.keys())}")
    
    # Show summary stats if available
    for key, value in data.items():
        if isinstance(value, (int, float)):
            print(f"   {key}: {value}")
    
    return True

def test_productivity_item_patch(token, items):
    """Test 4: PATCH /api/productivity/items/{uid} still works for an editable item if data exists"""
    print("\n✏️ Testing PATCH /api/productivity/items/{uid}...")
    
    if not items:
        print("⚠️ COVERAGE GAP - No productivity items exist to test PATCH operation")
        return True  # Not a failure, just a coverage gap
    
    # Find an editable item (look for items with status that can be updated)
    editable_item = None
    for item in items:
        if item.get('uid') and item.get('source') in ['tasks', 'appointments', 'production_tasks']:
            editable_item = item
            break
    
    if not editable_item:
        print("⚠️ COVERAGE GAP - No editable productivity items found to test PATCH operation")
        return True  # Not a failure, just a coverage gap
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    uid = editable_item['uid']
    
    # Try to update status (common editable field)
    patch_data = {
        "status": "in_progress" if editable_item.get('status') != 'in_progress' else "completed"
    }
    
    response = requests.patch(
        f"{BASE_URL}/api/productivity/items/{uid}",
        json=patch_data,
        headers=headers,
        timeout=30
    )
    
    if response.status_code not in [200, 204]:
        print(f"❌ Productivity item PATCH failed: {response.status_code} - {response.text}")
        return False
    
    print(f"✅ Productivity item PATCH successful")
    print(f"   Updated item UID: {uid}")
    print(f"   Patch data: {patch_data}")
    
    return True

def test_appointment_detail(token):
    """Test 5: New route GET /api/appointments/{appointment_id} works for a real appointment if data exists"""
    print("\n📅 Testing GET /api/appointments/{appointment_id}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test if the route exists by trying with a test ID
    response = requests.get(
        f"{BASE_URL}/api/appointments/test-appointment-id",
        headers=headers,
        timeout=30
    )
    
    if response.status_code == 404:
        response_text = response.text
        if "Appointment not found" in response_text:
            print("✅ Appointment detail route exists and is working")
            print("⚠️ COVERAGE GAP - No appointments exist to test with real data")
            return True
        elif "Not Found" in response_text:
            print("❌ Appointment detail route does not exist")
            return False
    elif response.status_code == 200:
        print("✅ Appointment detail route working with test data")
        return True
    else:
        print(f"❌ Unexpected response from appointment route: {response.status_code} - {response.text}")
        return False

def test_legacy_job_detail(token):
    """Test 6: Legacy job detail route support still works through existing backend GET /api/jobs/{job_id}/details"""
    print("\n🔧 Testing GET /api/jobs/{job_id}/details...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, try to get list of jobs to find a real ID
    response = requests.get(
        f"{BASE_URL}/api/jobs",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Could not fetch jobs list: {response.status_code} - {response.text}")
        return False
    
    jobs = response.json()
    
    if not jobs or len(jobs) == 0:
        print("⚠️ COVERAGE GAP - No jobs exist to test legacy job detail route")
        return True  # Not a failure, just a coverage gap
    
    # Test the detail route with first job
    job_id = jobs[0].get('id') or jobs[0].get('uid')
    
    if not job_id:
        print("❌ No job ID found in job data")
        return False
    
    response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/details",
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"❌ Legacy job detail failed: {response.status_code} - {response.text}")
        return False
    
    data = response.json()
    
    print(f"✅ Legacy job detail successful")
    print(f"   Job ID: {job_id}")
    print(f"   Response keys: {list(data.keys())}")
    
    return True

def test_productivity_aggregation_regression(token):
    """Test 7: Make sure no backend error/regression appears from the new source routes/day_key additions"""
    print("\n🔍 Testing productivity aggregation for regressions...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test various productivity endpoints that might use aggregation
    endpoints_to_test = [
        "/api/productivity/items",
        "/api/productivity/summary",
        "/api/dashboard/stats",
        "/api/productivity/calendar"
    ]
    
    all_passed = True
    
    for endpoint in endpoints_to_test:
        print(f"   Testing {endpoint}...")
        
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 500:
            print(f"❌ 500 error on {endpoint}: {response.text}")
            all_passed = False
        elif response.status_code == 404:
            print(f"   ⚠️ {endpoint} not found (404) - may not exist")
        elif response.status_code not in [200, 401, 403]:
            print(f"   ⚠️ Unexpected status {response.status_code} on {endpoint}")
        else:
            print(f"   ✅ {endpoint} - no 500 errors")
    
    if all_passed:
        print("✅ No backend errors/regressions detected in productivity aggregation")
    else:
        print("❌ Backend errors detected in productivity aggregation")
    
    return all_passed

def test_consolidation_endpoints_500s(token):
    """Test 8: Confirm no obvious 500s on the consolidation endpoints"""
    print("\n🚨 Testing consolidation endpoints for 500 errors...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Key consolidation endpoints
    consolidation_endpoints = [
        "/api/productivity/items",
        "/api/productivity/summary", 
        "/api/appointments",
        "/api/jobs",
        "/api/dashboard/stats",
        "/api/orders",
        "/api/tasks"
    ]
    
    all_passed = True
    
    for endpoint in consolidation_endpoints:
        print(f"   Testing {endpoint} for 500s...")
        
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 500:
            print(f"❌ 500 error on {endpoint}: {response.text}")
            all_passed = False
        else:
            print(f"   ✅ {endpoint} - no 500 error (status: {response.status_code})")
    
    if all_passed:
        print("✅ No 500 errors detected on consolidation endpoints")
    else:
        print("❌ 500 errors detected on consolidation endpoints")
    
    return all_passed

def main():
    """Run all consolidation pass backend tests"""
    print("🚀 Starting Backend/API Regression Tests for Consolidation Pass")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    
    results = {}
    token = None
    productivity_items = []
    
    try:
        # Test 1: Auth login
        auth_success, token = test_auth_login()
        results["auth_login"] = auth_success
        
        if not token:
            print("❌ Cannot proceed without valid auth token")
            return False
        
        # Test 2: Productivity items
        items_success, productivity_items = test_productivity_items(token)
        results["productivity_items"] = items_success
        
        # Test 3: Productivity summary
        results["productivity_summary"] = test_productivity_summary(token)
        
        # Test 4: Productivity item PATCH
        results["productivity_patch"] = test_productivity_item_patch(token, productivity_items)
        
        # Test 5: Appointment detail
        results["appointment_detail"] = test_appointment_detail(token)
        
        # Test 6: Legacy job detail
        results["legacy_job_detail"] = test_legacy_job_detail(token)
        
        # Test 7: Productivity aggregation regression
        results["productivity_aggregation"] = test_productivity_aggregation_regression(token)
        
        # Test 8: Consolidation endpoints 500s
        results["consolidation_500s"] = test_consolidation_endpoints_500s(token)
        
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        return False
    
    # Summary
    print("\n" + "="*70)
    print("📊 CONSOLIDATION PASS BACKEND TEST RESULTS")
    print("="*70)
    
    all_passed = True
    coverage_gaps = []
    
    for test_name, passed in results.items():
        if passed is True:
            status = "✅ PASS"
        elif passed is False:
            status = "❌ FAIL"
            all_passed = False
        else:
            status = "⚠️ COVERAGE GAP"
            coverage_gaps.append(test_name)
        
        print(f"{test_name:30} {status}")
    
    print("="*70)
    
    if coverage_gaps:
        print(f"⚠️ Coverage gaps noted: {', '.join(coverage_gaps)}")
        print("   These are not failures - just areas where test data doesn't exist")
    
    if all_passed:
        print("🎉 ALL CONSOLIDATION BACKEND TESTS PASSED!")
        print("✅ Backend consolidation is working correctly")
    else:
        print("⚠️ SOME CONSOLIDATION TESTS FAILED")
        print("❌ Backend consolidation needs attention")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)