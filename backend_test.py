#!/usr/bin/env python3
"""
Backend API Testing for Payroll Export Feature
Tests authentication and payroll endpoints for regression and new functionality.
"""

import requests
import json
from datetime import datetime, timedelta
import sys

# Configuration
BASE_URL = "https://workforce-hub-389.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Test credentials from review request
TEST_EMAIL = "signguypa@gmail.com"
TEST_PASSWORD = "Billnel323"

class PayrollAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data
        })
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def test_auth_login(self):
        """Test POST /api/auth/login"""
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.auth_token = data["access_token"]
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    self.log_result(
                        "POST /api/auth/login", 
                        True, 
                        f"Successfully authenticated. Token type: {data.get('token_type', 'bearer')}"
                    )
                    return True
                else:
                    self.log_result(
                        "POST /api/auth/login", 
                        False, 
                        "No access_token in response", 
                        data
                    )
            else:
                self.log_result(
                    "POST /api/auth/login", 
                    False, 
                    f"HTTP {response.status_code}", 
                    response.text
                )
        except Exception as e:
            self.log_result("POST /api/auth/login", False, f"Exception: {str(e)}")
        return False

    def test_payroll_report(self):
        """Test GET /api/payroll/report with various parameters"""
        if not self.auth_token:
            self.log_result("GET /api/payroll/report", False, "No auth token available")
            return

        # Test cases for payroll report
        test_cases = [
            {
                "name": "Custom date range",
                "params": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "period_type": "custom"
                }
            },
            {
                "name": "Weekly period",
                "params": {
                    "period_type": "weekly"
                }
            },
            {
                "name": "Biweekly period", 
                "params": {
                    "period_type": "biweekly"
                }
            },
            {
                "name": "With employee filter",
                "params": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "employee_id": "test-employee-id",
                    "period_type": "custom"
                }
            }
        ]

        for test_case in test_cases:
            try:
                response = self.session.get(
                    f"{API_BASE}/payroll/report",
                    params=test_case["params"]
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Validate response structure
                    required_fields = ["period_type", "start_date", "end_date", "employee_count", "employees", "totals"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_result(
                            f"GET /api/payroll/report ({test_case['name']})",
                            True,
                            f"Employee count: {data['employee_count']}, Period: {data['start_date']} to {data['end_date']}"
                        )
                    else:
                        self.log_result(
                            f"GET /api/payroll/report ({test_case['name']})",
                            False,
                            f"Missing fields: {missing_fields}",
                            data
                        )
                else:
                    self.log_result(
                        f"GET /api/payroll/report ({test_case['name']})",
                        False,
                        f"HTTP {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result(
                    f"GET /api/payroll/report ({test_case['name']})",
                    False,
                    f"Exception: {str(e)}"
                )

    def test_existing_payroll_endpoints(self):
        """Test existing payroll endpoints for regression"""
        if not self.auth_token:
            self.log_result("Existing payroll endpoints", False, "No auth token available")
            return

        # Define endpoints to test
        endpoints = [
            {
                "method": "GET",
                "path": "/payroll/timesheet",
                "params": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                "required_fields": ["start_date", "end_date", "employees", "totals"]
            },
            {
                "method": "GET", 
                "path": "/payroll/pay-period",
                "params": {
                    "period_type": "weekly"
                },
                "required_fields": ["period_type", "period_start", "period_end", "employees", "totals"]
            },
            {
                "method": "GET",
                "path": "/payroll/transactions",
                "params": {},
                "required_fields": None  # Returns array
            },
            {
                "method": "GET",
                "path": "/payroll/hours", 
                "params": {},
                "required_fields": None  # Returns array
            },
            {
                "method": "GET",
                "path": "/payroll/timeclock-shifts",
                "params": {},
                "required_fields": None  # Returns array
            },
            {
                "method": "GET",
                "path": "/payroll/schedule",
                "params": {},
                "required_fields": ["week_start", "schedules"]
            }
        ]

        for endpoint in endpoints:
            try:
                url = f"{API_BASE}{endpoint['path']}"
                response = self.session.get(url, params=endpoint['params'])
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Validate structure if required fields specified
                    if endpoint['required_fields']:
                        missing_fields = [field for field in endpoint['required_fields'] if field not in data]
                        if not missing_fields:
                            self.log_result(
                                f"GET {endpoint['path']}",
                                True,
                                "Response structure valid"
                            )
                        else:
                            self.log_result(
                                f"GET {endpoint['path']}",
                                False,
                                f"Missing fields: {missing_fields}",
                                data
                            )
                    else:
                        # For array responses, just check it's a list
                        if isinstance(data, list):
                            self.log_result(
                                f"GET {endpoint['path']}",
                                True,
                                f"Returned {len(data)} items"
                            )
                        else:
                            self.log_result(
                                f"GET {endpoint['path']}",
                                False,
                                "Expected array response",
                                data
                            )
                else:
                    self.log_result(
                        f"GET {endpoint['path']}",
                        False,
                        f"HTTP {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result(
                    f"GET {endpoint['path']}",
                    False,
                    f"Exception: {str(e)}"
                )

    def test_auth_protection(self):
        """Test that payroll endpoints require authentication"""
        # Create session without auth token
        unauth_session = requests.Session()
        
        test_endpoints = [
            "/payroll/report",
            "/payroll/timesheet?start_date=2024-01-01&end_date=2024-01-31",
            "/payroll/transactions"
        ]
        
        for endpoint in test_endpoints:
            try:
                response = unauth_session.get(f"{API_BASE}{endpoint}")
                
                if response.status_code == 401:
                    self.log_result(
                        f"Auth protection {endpoint}",
                        True,
                        "Correctly rejected unauthenticated request"
                    )
                else:
                    self.log_result(
                        f"Auth protection {endpoint}",
                        False,
                        f"Expected 401, got {response.status_code}",
                        response.text
                    )
            except Exception as e:
                self.log_result(
                    f"Auth protection {endpoint}",
                    False,
                    f"Exception: {str(e)}"
                )

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting Payroll Export Backend API Tests")
        print("=" * 60)
        print()
        
        # Test authentication first
        if self.test_auth_login():
            # Test new payroll report endpoint
            self.test_payroll_report()
            
            # Test existing endpoints for regression
            self.test_existing_payroll_endpoints()
        
        # Test auth protection (doesn't need login)
        self.test_auth_protection()
        
        # Print summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print()
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result["success"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("✅ ALL TESTS PASSED!")
        
        print()
        return len(failed_tests) == 0

if __name__ == "__main__":
    tester = PayrollAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)