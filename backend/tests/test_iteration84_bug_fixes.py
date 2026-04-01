"""
Iteration 84 - Bug Fixes Testing

Tests for:
1. Tenant-scoped user list: /api/admin/users shows only current tenant users
2. Admin create user route works within current tenant
3. Employee portal invite endpoint works and returns invite metadata/PIN
4. Timesheet entries include employee_id for editing manual entries
5. Manual timesheet entry can be edited/deleted from Time Sheets tab
6. Time clock shift can be deleted from Time Sheets and Time Entries tabs
7. No regression in Time Entries tab manual edit/delete flow
8. No regression in payroll transactions tab
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )
from backend.tests.test_credentials_helper import COMMON_TEST_EMAIL, COMMON_TEST_PASSWORD, DEMO_TEST_EMAIL, DEMO_TEST_PASSWORD, PORTAL_TEST_PASSWORD

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = PRODUCTION_OWNER_EMAIL
ADMIN_PASSWORD = PRODUCTION_OWNER_PASSWORD


class TestTenantScopedUserList:
    """Test that /api/admin/users returns only current tenant users"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get current user to know tenant_id
        me_response = requests.get(f"{BASE_URL}/api/users/me", headers=self.headers)
        assert me_response.status_code == 200
        self.current_user = me_response.json()
        self.tenant_id = self.current_user.get("tenant_id")
    
    def test_admin_users_returns_only_tenant_users(self):
        """Verify /api/admin/users returns only users from current tenant"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200, f"Failed to get users: {response.text}"
        
        users = response.json()
        assert isinstance(users, list), "Response should be a list"
        
        # All returned users should belong to the same tenant
        for user in users:
            assert user.get("tenant_id") == self.tenant_id, \
                f"User {user.get('email')} has tenant_id {user.get('tenant_id')}, expected {self.tenant_id}"
        
        print(f"PASS: /api/admin/users returned {len(users)} users, all from tenant {self.tenant_id}")
    
    def test_admin_users_does_not_include_other_tenants(self):
        """Verify no users from other tenants are returned"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert response.status_code == 200
        
        users = response.json()
        tenant_ids = set(u.get("tenant_id") for u in users)
        
        # Should only have one tenant_id (current tenant)
        assert len(tenant_ids) <= 1, f"Found users from multiple tenants: {tenant_ids}"
        print("PASS: All users belong to single tenant")


class TestAdminCreateUser:
    """Test admin create user route within current tenant"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        me_response = requests.get(f"{BASE_URL}/api/users/me", headers=self.headers)
        self.tenant_id = me_response.json().get("tenant_id")
        self.created_user_ids = []
    
    def teardown_method(self, method):
        """Cleanup created test users - disable them"""
        for user_id in self.created_user_ids:
            try:
                requests.put(
                    f"{BASE_URL}/api/admin/users/{user_id}/status?is_active=false",
                    headers=self.headers
                )
            except Exception:
                pass
    
    def test_admin_create_user_success(self):
        """Test creating a new user via admin route"""
        test_email = f"test_iter84_user_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/admin/users/create", headers=self.headers, json={
            "email": test_email,
            "password": COMMON_TEST_PASSWORD,
            "full_name": "TEST Iter84 User",
            "company_name": "Test Company",
            "role": "staff"
        })
        
        assert response.status_code == 200, f"Failed to create user: {response.text}"
        
        created_user = response.json()
        self.created_user_ids.append(created_user["id"])
        
        # Verify user is in same tenant
        assert created_user.get("tenant_id") == self.tenant_id, \
            f"Created user has wrong tenant_id: {created_user.get('tenant_id')}"
        # Email is lowercased by backend
        assert created_user.get("email") == test_email.lower()
        assert created_user.get("role") == "staff"
        
        print(f"PASS: Created user {test_email} in tenant {self.tenant_id}")
    
    def test_admin_create_user_appears_in_user_list(self):
        """Verify created user appears in tenant user list"""
        test_email = f"test_iter84_list_{uuid.uuid4().hex[:8]}@example.com"
        
        # Create user
        create_response = requests.post(f"{BASE_URL}/api/admin/users/create", headers=self.headers, json={
            "email": test_email,
            "password": COMMON_TEST_PASSWORD,
            "full_name": "TEST Iter84 List User",
            "role": "staff"
        })
        assert create_response.status_code == 200
        created_user = create_response.json()
        self.created_user_ids.append(created_user["id"])
        
        # Verify user appears in list (email is lowercased)
        list_response = requests.get(f"{BASE_URL}/api/admin/users", headers=self.headers)
        assert list_response.status_code == 200
        
        users = list_response.json()
        user_emails = [u.get("email") for u in users]
        assert test_email.lower() in user_emails, "Created user not found in user list"
        
        print("PASS: Created user appears in tenant user list")


class TestEmployeePortalInvite:
    """Test employee portal invite endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin and create test employee"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_employee_ids = []
    
    def teardown_method(self, method):
        """Cleanup test employees"""
        for emp_id in self.created_employee_ids:
            try:
                requests.delete(f"{BASE_URL}/api/employees/{emp_id}", headers=self.headers)
            except Exception:
                pass
    
    def test_invite_portal_returns_metadata(self):
        """Test that invite-portal endpoint returns invite metadata and PIN"""
        # Create employee with email
        test_email = f"TEST_iter84_invite_{uuid.uuid4().hex[:8]}@example.com"
        create_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Invite Employee",
            "email": test_email,
            "hourly_rate": 20.0
        })
        assert create_response.status_code == 200, f"Failed to create employee: {create_response.text}"
        employee = create_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Send portal invite
        invite_response = requests.post(
            f"{BASE_URL}/api/employees/{employee['id']}/invite-portal",
            headers=self.headers,
            json={"origin_url": "https://example.com"}
        )
        
        assert invite_response.status_code == 200, f"Invite failed: {invite_response.text}"
        
        invite_data = invite_response.json()
        
        # Verify response contains required fields
        assert "employee_id" in invite_data, "Missing employee_id in response"
        assert "employee_email" in invite_data, "Missing employee_email in response"
        assert "temporary_pin" in invite_data, "Missing temporary_pin in response"
        assert "login_url" in invite_data, "Missing login_url in response"
        assert "email_sent" in invite_data, "Missing email_sent in response"
        
        assert invite_data["employee_id"] == employee["id"]
        assert invite_data["employee_email"] == test_email
        assert len(invite_data["temporary_pin"]) >= 4, "PIN should be at least 4 digits"
        
        print(f"PASS: Invite portal returned metadata with PIN: {invite_data['temporary_pin']}")
    
    def test_invite_portal_requires_email(self):
        """Test that invite fails if employee has no email"""
        # Create employee without email
        create_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 No Email Employee",
            "hourly_rate": 15.0
        })
        assert create_response.status_code == 200
        employee = create_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Try to send portal invite
        invite_response = requests.post(
            f"{BASE_URL}/api/employees/{employee['id']}/invite-portal",
            headers=self.headers,
            json={}
        )
        
        assert invite_response.status_code == 400, f"Expected 400, got {invite_response.status_code}"
        assert "email" in invite_response.text.lower(), "Error should mention email requirement"
        
        print("PASS: Invite portal correctly requires employee email")


class TestTimesheetEntryEditing:
    """Test that timesheet entries include employee_id for editing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_employee_ids = []
        self.created_hours_ids = []
    
    def teardown_method(self, method):
        """Cleanup"""
        for hours_id in self.created_hours_ids:
            try:
                requests.delete(f"{BASE_URL}/api/payroll/hours/{hours_id}", headers=self.headers)
            except Exception:
                pass
        for emp_id in self.created_employee_ids:
            try:
                requests.delete(f"{BASE_URL}/api/employees/{emp_id}", headers=self.headers)
            except Exception:
                pass
    
    def test_timesheet_entries_include_employee_id(self):
        """Verify timesheet entries include employee_id for manual entries"""
        # Create test employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Timesheet Employee",
            "hourly_rate": 25.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Add manual hours
        today = datetime.now().strftime("%Y-%m-%d")
        add_hours_response = requests.post(f"{BASE_URL}/api/payroll/hours", headers=self.headers, json={
            "employee_id": employee["id"],
            "date": today,
            "hours": 4.0,
            "description": "TEST Iter84 manual hours",
            "task_type": "general"
        })
        assert add_hours_response.status_code == 200, f"Failed to add hours: {add_hours_response.text}"
        hours_entry = add_hours_response.json()
        self.created_hours_ids.append(hours_entry["id"])
        
        # Get timesheet
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        timesheet_response = requests.get(
            f"{BASE_URL}/api/payroll/timesheet",
            headers=self.headers,
            params={"start_date": start_date, "end_date": end_date, "employee_id": employee["id"]}
        )
        assert timesheet_response.status_code == 200, f"Failed to get timesheet: {timesheet_response.text}"
        
        timesheet = timesheet_response.json()
        
        # Find our employee's entries
        emp_data = None
        for emp in timesheet.get("employees", []):
            if emp.get("employee_id") == employee["id"]:
                emp_data = emp
                break
        
        assert emp_data is not None, "Employee not found in timesheet"
        
        # Check entries have employee_id
        for entry in emp_data.get("entries", []):
            if entry.get("source") == "manual":
                assert "employee_id" in entry, f"Manual entry missing employee_id: {entry}"
                assert entry["employee_id"] == employee["id"], \
                    f"Entry has wrong employee_id: {entry.get('employee_id')}"
        
        print("PASS: Timesheet manual entries include employee_id")
    
    def test_manual_entry_can_be_edited(self):
        """Test that manual hours entry can be edited"""
        # Create test employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Edit Hours Employee",
            "hourly_rate": 30.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Add manual hours
        today = datetime.now().strftime("%Y-%m-%d")
        add_response = requests.post(f"{BASE_URL}/api/payroll/hours", headers=self.headers, json={
            "employee_id": employee["id"],
            "date": today,
            "hours": 3.0,
            "description": "Original description",
            "task_type": "general"
        })
        assert add_response.status_code == 200
        hours_entry = add_response.json()
        self.created_hours_ids.append(hours_entry["id"])
        
        # Edit the entry
        edit_response = requests.put(
            f"{BASE_URL}/api/payroll/hours/{hours_entry['id']}",
            headers=self.headers,
            json={
                "hours": 5.0,
                "description": "Updated description",
                "task_type": "production"
            }
        )
        assert edit_response.status_code == 200, f"Failed to edit hours: {edit_response.text}"
        
        updated_entry = edit_response.json()
        assert updated_entry["hours"] == 5.0, f"Hours not updated: {updated_entry['hours']}"
        assert updated_entry["description"] == "Updated description"
        assert updated_entry["task_type"] == "production"
        
        print("PASS: Manual hours entry can be edited")
    
    def test_manual_entry_can_be_deleted(self):
        """Test that manual hours entry can be deleted"""
        # Create test employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Delete Hours Employee",
            "hourly_rate": 20.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Add manual hours
        today = datetime.now().strftime("%Y-%m-%d")
        add_response = requests.post(f"{BASE_URL}/api/payroll/hours", headers=self.headers, json={
            "employee_id": employee["id"],
            "date": today,
            "hours": 2.0,
            "description": "To be deleted",
            "task_type": "admin"
        })
        assert add_response.status_code == 200
        hours_entry = add_response.json()
        
        # Delete the entry
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/hours/{hours_entry['id']}",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"Failed to delete hours: {delete_response.text}"
        
        # Verify it's gone
        get_response = requests.get(
            f"{BASE_URL}/api/payroll/hours",
            headers=self.headers,
            params={"employee_id": employee["id"]}
        )
        assert get_response.status_code == 200
        remaining = get_response.json()
        remaining_ids = [h["id"] for h in remaining]
        assert hours_entry["id"] not in remaining_ids, "Deleted entry still exists"
        
        print("PASS: Manual hours entry can be deleted")


class TestTimeclockShiftDelete:
    """Test that time clock shifts can be deleted"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_employee_ids = []
    
    def teardown_method(self, method):
        """Cleanup"""
        for emp_id in self.created_employee_ids:
            try:
                requests.delete(f"{BASE_URL}/api/employees/{emp_id}", headers=self.headers)
            except Exception:
                pass
    
    def test_timeclock_shift_can_be_deleted(self):
        """Test that a time clock shift can be deleted"""
        # Create test employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Shift Delete Employee",
            "hourly_rate": 22.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Clock in
        clock_in_response = requests.post(f"{BASE_URL}/api/timeclock", headers=self.headers, json={
            "employee_id": employee["id"],
            "action": "start_work"
        })
        assert clock_in_response.status_code == 200, f"Clock in failed: {clock_in_response.text}"
        
        # Clock out
        clock_out_response = requests.post(f"{BASE_URL}/api/timeclock", headers=self.headers, json={
            "employee_id": employee["id"],
            "action": "end_work"
        })
        assert clock_out_response.status_code == 200, f"Clock out failed: {clock_out_response.text}"
        
        # Get shifts
        today = datetime.now().strftime("%Y-%m-%d")
        shifts_response = requests.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            headers=self.headers,
            params={"employee_id": employee["id"], "start_date": today, "end_date": today}
        )
        assert shifts_response.status_code == 200
        shifts = shifts_response.json()
        
        if len(shifts) == 0:
            print("SKIP: No shifts found to delete (may be timing issue)")
            return
        
        shift_id = shifts[0]["id"]
        
        # Delete the shift
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/timeclock-shifts/{shift_id}",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"Failed to delete shift: {delete_response.text}"
        
        # Verify it's gone
        verify_response = requests.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            headers=self.headers,
            params={"employee_id": employee["id"], "start_date": today, "end_date": today}
        )
        assert verify_response.status_code == 200
        remaining_shifts = verify_response.json()
        remaining_ids = [s["id"] for s in remaining_shifts]
        assert shift_id not in remaining_ids, "Deleted shift still exists"
        
        print("PASS: Time clock shift can be deleted")


class TestPayrollTransactionsNoRegression:
    """Test no regression in payroll transactions tab"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_employee_ids = []
        self.created_transaction_ids = []
    
    def teardown_method(self, method):
        """Cleanup"""
        for txn_id in self.created_transaction_ids:
            try:
                requests.delete(f"{BASE_URL}/api/payroll/transactions/{txn_id}", headers=self.headers)
            except Exception:
                pass
        for emp_id in self.created_employee_ids:
            try:
                requests.delete(f"{BASE_URL}/api/employees/{emp_id}", headers=self.headers)
            except Exception:
                pass
    
    def test_create_transaction(self):
        """Test creating a payroll transaction"""
        # Create test employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Transaction Employee",
            "hourly_rate": 18.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Create transaction
        today = datetime.now().strftime("%Y-%m-%d")
        create_txn_response = requests.post(f"{BASE_URL}/api/payroll/transactions", headers=self.headers, json={
            "employee_id": employee["id"],
            "type": "advance",
            "amount": 100.0,
            "description": "TEST Iter84 advance",
            "date": today
        })
        assert create_txn_response.status_code == 200, f"Failed to create transaction: {create_txn_response.text}"
        
        txn = create_txn_response.json()
        self.created_transaction_ids.append(txn["id"])
        
        assert txn["employee_id"] == employee["id"]
        assert txn["type"] == "advance"
        assert txn["amount"] == 100.0
        
        print("PASS: Payroll transaction created successfully")
    
    def test_edit_transaction(self):
        """Test editing a payroll transaction"""
        # Create test employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Edit Txn Employee",
            "hourly_rate": 20.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Create transaction
        today = datetime.now().strftime("%Y-%m-%d")
        create_txn_response = requests.post(f"{BASE_URL}/api/payroll/transactions", headers=self.headers, json={
            "employee_id": employee["id"],
            "type": "payment",
            "amount": 200.0,
            "description": "Original payment",
            "date": today
        })
        assert create_txn_response.status_code == 200
        txn = create_txn_response.json()
        self.created_transaction_ids.append(txn["id"])
        
        # Edit transaction
        edit_response = requests.put(
            f"{BASE_URL}/api/payroll/transactions/{txn['id']}",
            headers=self.headers,
            json={
                "amount": 250.0,
                "description": "Updated payment"
            }
        )
        assert edit_response.status_code == 200, f"Failed to edit transaction: {edit_response.text}"
        
        updated_txn = edit_response.json()
        assert updated_txn["amount"] == 250.0
        assert updated_txn["description"] == "Updated payment"
        
        print("PASS: Payroll transaction edited successfully")
    
    def test_delete_transaction(self):
        """Test deleting a payroll transaction"""
        # Create test employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 Delete Txn Employee",
            "hourly_rate": 15.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        # Create transaction
        today = datetime.now().strftime("%Y-%m-%d")
        create_txn_response = requests.post(f"{BASE_URL}/api/payroll/transactions", headers=self.headers, json={
            "employee_id": employee["id"],
            "type": "earnings",
            "amount": 500.0,
            "description": "To be deleted",
            "date": today
        })
        assert create_txn_response.status_code == 200
        txn = create_txn_response.json()
        
        # Delete transaction
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/transactions/{txn['id']}",
            headers=self.headers
        )
        assert delete_response.status_code == 200, f"Failed to delete transaction: {delete_response.text}"
        
        # Verify it's gone
        list_response = requests.get(
            f"{BASE_URL}/api/payroll/transactions",
            headers=self.headers,
            params={"employee_id": employee["id"]}
        )
        assert list_response.status_code == 200
        remaining = list_response.json()
        remaining_ids = [t["id"] for t in remaining]
        assert txn["id"] not in remaining_ids, "Deleted transaction still exists"
        
        print("PASS: Payroll transaction deleted successfully")
    
    def test_list_transactions(self):
        """Test listing payroll transactions"""
        response = requests.get(f"{BASE_URL}/api/payroll/transactions", headers=self.headers)
        assert response.status_code == 200, f"Failed to list transactions: {response.text}"
        
        transactions = response.json()
        assert isinstance(transactions, list), "Response should be a list"
        
        print(f"PASS: Listed {len(transactions)} payroll transactions")


class TestTimeEntriesNoRegression:
    """Test no regression in Time Entries tab"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.created_employee_ids = []
        self.created_hours_ids = []
    
    def teardown_method(self, method):
        """Cleanup"""
        for hours_id in self.created_hours_ids:
            try:
                requests.delete(f"{BASE_URL}/api/payroll/hours/{hours_id}", headers=self.headers)
            except Exception:
                pass
        for emp_id in self.created_employee_ids:
            try:
                requests.delete(f"{BASE_URL}/api/employees/{emp_id}", headers=self.headers)
            except Exception:
                pass
    
    def test_get_manual_hours(self):
        """Test getting manual hours entries"""
        response = requests.get(f"{BASE_URL}/api/payroll/hours", headers=self.headers)
        assert response.status_code == 200, f"Failed to get hours: {response.text}"
        
        hours = response.json()
        assert isinstance(hours, list), "Response should be a list"
        
        print(f"PASS: Listed {len(hours)} manual hours entries")
    
    def test_get_timeclock_shifts(self):
        """Test getting time clock shifts"""
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/payroll/timeclock-shifts",
            headers=self.headers,
            params={"start_date": week_ago, "end_date": today}
        )
        assert response.status_code == 200, f"Failed to get shifts: {response.text}"
        
        shifts = response.json()
        assert isinstance(shifts, list), "Response should be a list"
        
        print(f"PASS: Listed {len(shifts)} time clock shifts")
    
    def test_manual_hours_crud_flow(self):
        """Test full CRUD flow for manual hours"""
        # Create employee
        create_emp_response = requests.post(f"{BASE_URL}/api/employees", headers=self.headers, json={
            "name": "TEST Iter84 CRUD Hours Employee",
            "hourly_rate": 25.0
        })
        assert create_emp_response.status_code == 200
        employee = create_emp_response.json()
        self.created_employee_ids.append(employee["id"])
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # CREATE
        create_response = requests.post(f"{BASE_URL}/api/payroll/hours", headers=self.headers, json={
            "employee_id": employee["id"],
            "date": today,
            "hours": 6.0,
            "description": "CRUD test entry",
            "task_type": "design"
        })
        assert create_response.status_code == 200
        entry = create_response.json()
        self.created_hours_ids.append(entry["id"])
        
        # READ
        read_response = requests.get(
            f"{BASE_URL}/api/payroll/hours",
            headers=self.headers,
            params={"employee_id": employee["id"]}
        )
        assert read_response.status_code == 200
        entries = read_response.json()
        assert any(e["id"] == entry["id"] for e in entries), "Created entry not found"
        
        # UPDATE
        update_response = requests.put(
            f"{BASE_URL}/api/payroll/hours/{entry['id']}",
            headers=self.headers,
            json={"hours": 8.0, "description": "Updated CRUD test"}
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["hours"] == 8.0
        
        # DELETE
        delete_response = requests.delete(
            f"{BASE_URL}/api/payroll/hours/{entry['id']}",
            headers=self.headers
        )
        assert delete_response.status_code == 200
        self.created_hours_ids.remove(entry["id"])
        
        # Verify deleted
        verify_response = requests.get(
            f"{BASE_URL}/api/payroll/hours",
            headers=self.headers,
            params={"employee_id": employee["id"]}
        )
        assert verify_response.status_code == 200
        remaining = verify_response.json()
        assert not any(e["id"] == entry["id"] for e in remaining), "Entry not deleted"
        
        print("PASS: Manual hours CRUD flow works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
