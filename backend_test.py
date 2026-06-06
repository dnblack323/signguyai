#!/usr/bin/env python3
"""
Backend Testing for Payroll Updates - Regression Testing
Testing the payroll mark-paid-in-full functionality and related endpoints
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "https://action-central-35.preview.emergentagent.com/api"
LOGIN_EMAIL = "signguypa@gmail.com"
LOGIN_PASSWORD = "Billnel323"

class PayrollTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate and get bearer token"""
        print("🔐 Authenticating...")
        try:
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": LOGIN_EMAIL,
                    "password": LOGIN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.auth_token}"
                    })
                    self.log_result("Authentication", True, f"Token length: {len(self.auth_token)}")
                    return True
                else:
                    self.log_result("Authentication", False, "No access_token in response")
                    return False
            else:
                self.log_result("Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_mark_paid_in_full_validation(self):
        """Test /api/payroll/mark-paid-in-full validation"""
        print("\n🧪 Testing mark-paid-in-full validation...")
        
        # Test 1: period_end < period_start should fail
        try:
            response = self.session.post(
                f"{BASE_URL}/payroll/mark-paid-in-full",
                json={
                    "employee_id": "test-employee-123",
                    "period_start": "2026-04-20",
                    "period_end": "2026-04-15",  # Before start date
                    "paid_amount": 100.0
                }
            )
            
            if response.status_code == 400:
                self.log_result("Mark Paid - Invalid Period Validation", True, 
                               "Correctly rejected period_end < period_start")
            else:
                self.log_result("Mark Paid - Invalid Period Validation", False, 
                               f"Expected 400, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Mark Paid - Invalid Period Validation", False, f"Exception: {str(e)}")
        
        # Test 2: Zero amount should fail
        try:
            response = self.session.post(
                f"{BASE_URL}/payroll/mark-paid-in-full",
                json={
                    "employee_id": "test-employee-123",
                    "period_start": "2026-04-15",
                    "period_end": "2026-04-20",
                    "paid_amount": 0.0  # Zero amount
                }
            )
            
            if response.status_code == 422:  # Pydantic validation error
                self.log_result("Mark Paid - Zero Amount Validation", True, 
                               "Correctly rejected zero amount")
            else:
                self.log_result("Mark Paid - Zero Amount Validation", False, 
                               f"Expected 422, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Mark Paid - Zero Amount Validation", False, f"Exception: {str(e)}")
    
    def test_timeclock_shifts_update(self):
        """Test /api/payroll/timeclock-shifts/{id} update with null lunch fields"""
        print("\n🧪 Testing timeclock shifts update...")
        
        # First, get existing shifts to find a valid ID
        try:
            response = self.session.get(f"{BASE_URL}/payroll/timeclock-shifts")
            
            if response.status_code == 200:
                shifts = response.json()
                if shifts and len(shifts) > 0:
                    shift_id = shifts[0].get("id")
                    if shift_id:
                        # Test updating with null lunch fields and break_minutes
                        update_response = self.session.put(
                            f"{BASE_URL}/payroll/timeclock-shifts/{shift_id}",
                            json={
                                "lunch_start": None,
                                "lunch_end": None,
                                "break_minutes": 15.0
                            }
                        )
                        
                        if update_response.status_code == 200:
                            self.log_result("Timeclock Shift Update - Null Lunch Fields", True,
                                           "Successfully updated with null lunch fields")
                        else:
                            self.log_result("Timeclock Shift Update - Null Lunch Fields", False,
                                           f"Update failed: {update_response.status_code}")
                    else:
                        self.log_result("Timeclock Shift Update - Null Lunch Fields", False,
                                       "No shift ID found in response")
                else:
                    self.log_result("Timeclock Shift Update - Null Lunch Fields", False,
                                   "No shifts found to test update")
            else:
                self.log_result("Timeclock Shift Update - Null Lunch Fields", False,
                               f"Failed to get shifts: {response.status_code}")
                
        except Exception as e:
            self.log_result("Timeclock Shift Update - Null Lunch Fields", False, f"Exception: {str(e)}")
    
    def test_payroll_endpoints_basic(self):
        """Test basic payroll endpoints are accessible"""
        print("\n🧪 Testing basic payroll endpoints...")
        
        endpoints = [
            ("/payroll/report", "Payroll Report"),
            ("/payroll/timesheet", "Payroll Timesheet"),
            ("/payroll/pay-period", "Pay Period Summary"),
            ("/payroll/transactions", "Payroll Transactions"),
            ("/payroll/hours", "Manual Hours"),
            ("/payroll/timeclock-shifts", "Timeclock Shifts"),
            ("/payroll/schedule", "Employee Schedule")
        ]
        
        for endpoint, name in endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 200:
                    self.log_result(f"{name} Endpoint", True, "Accessible and returns 200")
                else:
                    self.log_result(f"{name} Endpoint", False, 
                                   f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"{name} Endpoint", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend Payroll Testing...")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with tests.")
            return False
        
        # Run tests
        self.test_payroll_endpoints_basic()
        self.test_mark_paid_in_full_validation()
        self.test_timeclock_shifts_update()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if "✅" in result["status"])
        total = len(self.test_results)
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
        
        print(f"\n📈 Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. See details above.")
            return False

if __name__ == "__main__":
    tester = PayrollTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)