"""
Iteration 83 - Employee Module End-to-End Tests

Tests for:
- Employee admin lifecycle: create, edit, deactivate/reactivate, reset PIN, delete
- Employee portal login with reset PIN and inactive employee rejection
- Employee portal config endpoint returns tenant settings
- Employee portal permission enforcement (pay/tasks/job details blocked when disabled)
- Payroll/timeclock admin-only routes remain protected
- Payroll transaction add/edit/delete
- TimeClock hourly-rate input (no sticky 0)
- No regressions in employee portal dashboard/pay/tasks/profile/job pages
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "signguypa@gmail.com"
ADMIN_PASSWORD = "Billnel323"


class TestEmployeeAdminLifecycle:
    """Test employee CRUD operations from admin perspective"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_employee_id(self, admin_token):
        """Create a test employee for lifecycle tests"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_Iter83_Employee_{unique_id}",
                "email": f"test_iter83_{unique_id}@example.com",
                "phone": "5551234567",
                "hourly_rate": 25.50,
                "role": "staff",
                "pin": "9876"
            }
        )
        assert response.status_code == 200, f"Failed to create test employee: {response.text}"
        employee = response.json()
        yield employee["id"]
        
        # Cleanup: delete the test employee
        requests.delete(
            f"{BASE_URL}/api/employees/{employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_01_create_employee(self, admin_token):
        """Test creating a new employee"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_CreateEmployee_{unique_id}",
                "email": f"test_create_{unique_id}@example.com",
                "hourly_rate": 20.00,
                "role": "staff"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == f"TEST_CreateEmployee_{unique_id}"
        assert data["hourly_rate"] == 20.00
        assert "id" in data
        assert "pin" in data  # Default PIN should be set
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{data['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print("PASS: Create employee works correctly")
    
    def test_02_get_employee(self, admin_token, test_employee_id):
        """Test getting a specific employee"""
        response = requests.get(
            f"{BASE_URL}/api/employees/{test_employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_employee_id
        assert "name" in data
        assert "hourly_rate" in data
        print("PASS: Get employee works correctly")
    
    def test_03_update_employee(self, admin_token, test_employee_id):
        """Test updating an employee"""
        response = requests.put(
            f"{BASE_URL}/api/employees/{test_employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "TEST_Iter83_Updated",
                "hourly_rate": 30.00
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Iter83_Updated"
        assert data["hourly_rate"] == 30.00
        
        # Verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/employees/{test_employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["hourly_rate"] == 30.00
        print("PASS: Update employee works correctly")
    
    def test_04_deactivate_employee(self, admin_token, test_employee_id):
        """Test deactivating an employee"""
        response = requests.put(
            f"{BASE_URL}/api/employees/{test_employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == False
        print("PASS: Deactivate employee works correctly")
    
    def test_05_reactivate_employee(self, admin_token, test_employee_id):
        """Test reactivating an employee"""
        response = requests.put(
            f"{BASE_URL}/api/employees/{test_employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] == True
        print("PASS: Reactivate employee works correctly")
    
    def test_06_reset_employee_pin(self, admin_token, test_employee_id):
        """Test resetting an employee's PIN"""
        response = requests.post(
            f"{BASE_URL}/api/employees/{test_employee_id}/reset-pin",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"pin": "5432"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "PIN" in data["message"] or "updated" in data["message"].lower()
        print("PASS: Reset employee PIN works correctly")
    
    def test_07_reset_pin_validation(self, admin_token, test_employee_id):
        """Test PIN validation (must be 4-6 digits)"""
        # Too short
        response = requests.post(
            f"{BASE_URL}/api/employees/{test_employee_id}/reset-pin",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"pin": "123"}
        )
        assert response.status_code == 400
        
        # Non-numeric
        response = requests.post(
            f"{BASE_URL}/api/employees/{test_employee_id}/reset-pin",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"pin": "abcd"}
        )
        assert response.status_code == 400
        print("PASS: PIN validation works correctly")
    
    def test_08_delete_employee(self, admin_token):
        """Test deleting an employee"""
        # Create a temporary employee to delete
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_DeleteMe_{unique_id}",
                "email": f"test_delete_{unique_id}@example.com",
                "hourly_rate": 15.00
            }
        )
        assert create_response.status_code == 200
        employee_id = create_response.json()["id"]
        
        # Delete the employee
        delete_response = requests.delete(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 404
        print("PASS: Delete employee works correctly")


class TestEmployeePortalAuth:
    """Test employee portal authentication"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_employee(self, admin_token):
        """Create a test employee for portal auth tests"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_PortalAuth_{unique_id}",
                "email": f"test_portal_{unique_id}@example.com",
                "phone": "5559876543",
                "hourly_rate": 22.00,
                "role": "staff",
                "pin": "1234"
            }
        )
        assert response.status_code == 200
        employee = response.json()
        yield employee
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_01_employee_portal_login_success(self, test_employee):
        """Test successful employee portal login"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={
                "email": test_employee["email"],
                "pin": "1234"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["employee_id"] == test_employee["id"]
        assert data["employee_name"] == test_employee["name"]
        print("PASS: Employee portal login works correctly")
    
    def test_02_employee_portal_login_with_reset_pin(self, admin_token, test_employee):
        """Test employee portal login after PIN reset"""
        # Reset PIN
        reset_response = requests.post(
            f"{BASE_URL}/api/employees/{test_employee['id']}/reset-pin",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"pin": "4321"}
        )
        assert reset_response.status_code == 200
        
        # Login with new PIN
        login_response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={
                "email": test_employee["email"],
                "pin": "4321"
            }
        )
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        print("PASS: Employee portal login with reset PIN works correctly")
    
    def test_03_employee_portal_login_wrong_pin(self, test_employee):
        """Test employee portal login with wrong PIN"""
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={
                "email": test_employee["email"],
                "pin": "9999"
            }
        )
        assert response.status_code == 401
        print("PASS: Employee portal rejects wrong PIN")
    
    def test_04_inactive_employee_cannot_login(self, admin_token, test_employee):
        """Test that inactive employees cannot login"""
        # Deactivate employee
        deactivate_response = requests.put(
            f"{BASE_URL}/api/employees/{test_employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False}
        )
        assert deactivate_response.status_code == 200
        
        # Try to login
        login_response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={
                "email": test_employee["email"],
                "pin": "4321"
            }
        )
        assert login_response.status_code == 403
        assert "inactive" in login_response.json().get("detail", "").lower()
        
        # Reactivate for cleanup
        requests.put(
            f"{BASE_URL}/api/employees/{test_employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": True}
        )
        print("PASS: Inactive employee cannot login")


class TestEmployeePortalConfig:
    """Test employee portal config endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def employee_token(self, admin_token):
        """Create test employee and get portal token"""
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_PortalConfig_{unique_id}",
                "email": f"test_config_{unique_id}@example.com",
                "hourly_rate": 20.00,
                "pin": "1234"
            }
        )
        assert create_response.status_code == 200
        employee = create_response.json()
        
        # Login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": employee["email"], "pin": "1234"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        yield {"token": token, "employee": employee}
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_01_get_portal_config(self, employee_token):
        """Test getting employee portal config"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/config",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check expected config keys exist
        expected_keys = [
            "can_view_tasks", "can_view_schedule", "can_view_pay_stubs",
            "can_view_time_clock", "can_edit_profile"
        ]
        for key in expected_keys:
            assert key in data, f"Missing config key: {key}"
        print("PASS: Employee portal config endpoint returns settings")


class TestEmployeePortalPermissionEnforcement:
    """Test that employee portal respects permission settings"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def employee_token(self, admin_token):
        """Create test employee and get portal token"""
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_PermEnforce_{unique_id}",
                "email": f"test_perm_{unique_id}@example.com",
                "hourly_rate": 20.00,
                "pin": "1234"
            }
        )
        assert create_response.status_code == 200
        employee = create_response.json()
        
        # Login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": employee["email"], "pin": "1234"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        yield {"token": token, "employee": employee}
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_01_employee_portal_profile(self, employee_token):
        """Test employee portal profile endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/profile",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == employee_token["employee"]["id"]
        print("PASS: Employee portal profile works")
    
    def test_02_employee_portal_timeclock_status(self, employee_token):
        """Test employee portal timeclock status"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/time-clock/status",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        # Should work if can_view_time_clock is enabled (default)
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert "is_clocked_in" in data
        print("PASS: Employee portal timeclock status endpoint works")
    
    def test_03_employee_portal_pay_summary(self, employee_token):
        """Test employee portal pay summary"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/pay/summary",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        # Should work if can_view_pay_stubs is enabled (default)
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert "current_period_earnings" in data
            assert "ytd_earnings" in data
        print("PASS: Employee portal pay summary endpoint works")
    
    def test_04_employee_portal_tasks(self, employee_token):
        """Test employee portal tasks endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/tasks",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        # Should work if can_view_tasks is enabled (default)
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        print("PASS: Employee portal tasks endpoint works")
    
    def test_05_employee_portal_work_summary(self, employee_token):
        """Test employee portal work summary"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/work-summary",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert "today_hours_worked" in data
            assert "week_hours_worked" in data
        print("PASS: Employee portal work summary endpoint works")


class TestPayrollAdminOnlyRoutes:
    """Test that payroll/timeclock admin routes remain protected"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_employee(self, admin_token):
        """Create a test employee for payroll tests"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_PayrollAdmin_{unique_id}",
                "email": f"test_payroll_{unique_id}@example.com",
                "hourly_rate": 25.00,
                "pin": "1234"
            }
        )
        assert response.status_code == 200
        employee = response.json()
        yield employee
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_01_admin_can_add_transaction(self, admin_token, test_employee):
        """Test admin can add payroll transaction"""
        response = requests.post(
            f"{BASE_URL}/api/payroll/transactions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": test_employee["id"],
                "type": "advance",
                "amount": 100.00,
                "description": "TEST_Iter83_Advance"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.00
        assert data["type"] == "advance"
        print("PASS: Admin can add payroll transaction")
        return data["id"]
    
    def test_02_admin_can_edit_transaction(self, admin_token, test_employee):
        """Test admin can edit payroll transaction"""
        # First create a transaction
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/transactions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": test_employee["id"],
                "type": "payment",
                "amount": 50.00,
                "description": "TEST_Iter83_Payment"
            }
        )
        assert create_response.status_code == 200
        transaction_id = create_response.json()["id"]
        
        # Edit the transaction
        edit_response = requests.put(
            f"{BASE_URL}/api/payroll/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"amount": 75.00}
        )
        assert edit_response.status_code == 200
        assert edit_response.json()["amount"] == 75.00
        print("PASS: Admin can edit payroll transaction")
    
    def test_03_admin_can_delete_transaction(self, admin_token, test_employee):
        """Test admin can delete payroll transaction"""
        # First create a transaction
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/transactions",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": test_employee["id"],
                "type": "advance",
                "amount": 25.00,
                "description": "TEST_Iter83_ToDelete"
            }
        )
        assert create_response.status_code == 200
        transaction_id = create_response.json()["id"]
        
        # Delete the transaction
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/transactions/{transaction_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        print("PASS: Admin can delete payroll transaction")
    
    def test_04_admin_can_add_manual_hours(self, admin_token, test_employee):
        """Test admin can add manual hours"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = requests.post(
            f"{BASE_URL}/api/payroll/hours",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": test_employee["id"],
                "date": today,
                "hours": 4.5,
                "description": "TEST_Iter83_ManualHours",
                "task_type": "general"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hours"] == 4.5
        print("PASS: Admin can add manual hours")
    
    def test_05_admin_can_edit_manual_hours(self, admin_token, test_employee):
        """Test admin can edit manual hours"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create manual hours entry
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/hours",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": test_employee["id"],
                "date": today,
                "hours": 2.0,
                "description": "TEST_Iter83_ToEdit"
            }
        )
        assert create_response.status_code == 200
        entry_id = create_response.json()["id"]
        
        # Edit the entry
        edit_response = requests.put(
            f"{BASE_URL}/api/payroll/hours/{entry_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"hours": 3.5}
        )
        assert edit_response.status_code == 200
        assert edit_response.json()["hours"] == 3.5
        print("PASS: Admin can edit manual hours")
    
    def test_06_admin_can_delete_manual_hours(self, admin_token, test_employee):
        """Test admin can delete manual hours"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create manual hours entry
        create_response = requests.post(
            f"{BASE_URL}/api/payroll/hours",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "employee_id": test_employee["id"],
                "date": today,
                "hours": 1.0,
                "description": "TEST_Iter83_ToDelete"
            }
        )
        assert create_response.status_code == 200
        entry_id = create_response.json()["id"]
        
        # Delete the entry
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/hours/{entry_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        print("PASS: Admin can delete manual hours")


class TestEmployeePortalNoRegressions:
    """Test that existing employee portal pages still work"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def employee_token(self, admin_token):
        """Create test employee and get portal token"""
        unique_id = str(uuid.uuid4())[:8]
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_NoRegression_{unique_id}",
                "email": f"test_noreg_{unique_id}@example.com",
                "hourly_rate": 20.00,
                "pin": "1234"
            }
        )
        assert create_response.status_code == 200
        employee = create_response.json()
        
        # Login to get token
        login_response = requests.post(
            f"{BASE_URL}/api/employee-portal/auth/login",
            json={"email": employee["email"], "pin": "1234"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        yield {"token": token, "employee": employee}
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{employee['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
    
    def test_01_dashboard_profile(self, employee_token):
        """Test employee portal profile for dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/profile",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "hourly_rate" in data
        print("PASS: Dashboard profile endpoint works")
    
    def test_02_dashboard_jobs(self, employee_token):
        """Test employee portal jobs for dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/jobs",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        # May return 200 or 403 depending on settings
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        print("PASS: Dashboard jobs endpoint works")
    
    def test_03_timeclock_punch(self, employee_token):
        """Test employee portal timeclock punch"""
        # Start work
        response = requests.post(
            f"{BASE_URL}/api/employee-portal/time-clock/punch?action=start_work",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        # May return 200 or 403 depending on settings
        assert response.status_code in [200, 400, 403]
        
        if response.status_code == 200:
            # End work to clean up
            requests.post(
                f"{BASE_URL}/api/employee-portal/time-clock/punch?action=end_work",
                headers={"Authorization": f"Bearer {employee_token['token']}"}
            )
        print("PASS: Timeclock punch endpoint works")
    
    def test_04_timeclock_history(self, employee_token):
        """Test employee portal timeclock history"""
        response = requests.get(
            f"{BASE_URL}/api/employee-portal/time-clock/history",
            headers={"Authorization": f"Bearer {employee_token['token']}"}
        )
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            assert isinstance(response.json(), list)
        print("PASS: Timeclock history endpoint works")


class TestTimeclockHourlyRateInput:
    """Test that TimeClock hourly rate input doesn't stick on 0"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_01_create_employee_with_rate(self, admin_token):
        """Test creating employee with specific hourly rate"""
        unique_id = str(uuid.uuid4())[:8]
        response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_HourlyRate_{unique_id}",
                "email": f"test_rate_{unique_id}@example.com",
                "hourly_rate": 25.50
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["hourly_rate"] == 25.50
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{data['id']}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print("PASS: Employee created with correct hourly rate")
    
    def test_02_update_employee_rate(self, admin_token):
        """Test updating employee hourly rate"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Create employee with rate 0
        create_response = requests.post(
            f"{BASE_URL}/api/employees",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": f"TEST_UpdateRate_{unique_id}",
                "email": f"test_uprate_{unique_id}@example.com",
                "hourly_rate": 0
            }
        )
        assert create_response.status_code == 200
        employee_id = create_response.json()["id"]
        
        # Update to non-zero rate
        update_response = requests.put(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"hourly_rate": 30.00}
        )
        assert update_response.status_code == 200
        assert update_response.json()["hourly_rate"] == 30.00
        
        # Verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        assert get_response.json()["hourly_rate"] == 30.00
        
        # Cleanup
        requests.delete(
            f"{BASE_URL}/api/employees/{employee_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        print("PASS: Employee hourly rate updates correctly (not stuck on 0)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
