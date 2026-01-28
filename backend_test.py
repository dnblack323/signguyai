#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, date, timedelta

class SignGuyAPITester:
    def __init__(self, base_url="https://signtists-lab.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {}  # Store created entities for cleanup and reference
        self.job_line_items_results = []  # Store job line items test results

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.text else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n" + "="*50)
        print("TESTING HEALTH & BASIC ENDPOINTS")
        print("="*50)
        
        self.run_test("Root endpoint", "GET", "", 200)
        self.run_test("Health check", "GET", "health", 200)

    def test_customers_crud(self):
        """Test customer CRUD operations"""
        print("\n" + "="*50)
        print("TESTING CUSTOMERS CRUD")
        print("="*50)
        
        # Create customer
        customer_data = {
            "name": "Test Customer",
            "company": "Test Company Inc",
            "email": "test@example.com",
            "phone": "555-0123",
            "status": "active",
            "notes": "Test customer for API testing"
        }
        success, customer = self.run_test("Create customer", "POST", "customers", 200, customer_data)
        if success and customer:
            self.test_data['customer_id'] = customer['id']
            
            # Get all customers
            self.run_test("Get all customers", "GET", "customers", 200)
            
            # Get specific customer
            self.run_test("Get customer by ID", "GET", f"customers/{customer['id']}", 200)
            
            # Update customer
            update_data = {"status": "inactive", "notes": "Updated notes"}
            self.run_test("Update customer", "PUT", f"customers/{customer['id']}", 200, update_data)
            
            # Search customers
            self.run_test("Search customers", "GET", "customers", 200, params={"search": "Test"})
            
            return True
        return False

    def test_quotes_crud(self):
        """Test quotes CRUD operations"""
        print("\n" + "="*50)
        print("TESTING QUOTES CRUD")
        print("="*50)
        
        if 'customer_id' not in self.test_data:
            print("❌ Skipping quotes test - no customer available")
            return False
            
        # Create quote
        quote_data = {
            "customer_id": self.test_data['customer_id'],
            "line_items": [
                {"description": "Banner 4x8", "quantity": 1, "unit_price": 150.00},
                {"description": "Installation", "quantity": 1, "unit_price": 75.00}
            ],
            "notes": "Test quote",
            "status": "draft"
        }
        success, quote = self.run_test("Create quote", "POST", "quotes", 200, quote_data)
        if success and quote:
            self.test_data['quote_id'] = quote['id']
            
            # Get all quotes
            self.run_test("Get all quotes", "GET", "quotes", 200)
            
            # Get specific quote
            self.run_test("Get quote by ID", "GET", f"quotes/{quote['id']}", 200)
            
            # Update quote status
            update_data = {"status": "approved"}
            self.run_test("Update quote", "PUT", f"quotes/{quote['id']}", 200, update_data)
            
            # Convert quote to job
            success, job = self.run_test("Convert quote to job", "POST", f"quotes/{quote['id']}/convert-to-job", 200)
            if success and job:
                self.test_data['job_id'] = job['id']
            
            return True
        return False

    def test_jobs_crud(self):
        """Test jobs CRUD operations"""
        print("\n" + "="*50)
        print("TESTING JOBS CRUD")
        print("="*50)
        
        if 'customer_id' not in self.test_data:
            print("❌ Skipping jobs test - no customer available")
            return False
            
        # Create job
        job_data = {
            "customer_id": self.test_data['customer_id'],
            "name": "Test Sign Installation",
            "description": "Install banner at storefront",
            "status": "approved",
            "due_date": (date.today() + timedelta(days=7)).isoformat()
        }
        success, job = self.run_test("Create job", "POST", "jobs", 200, job_data)
        if success and job:
            if 'job_id' not in self.test_data:
                self.test_data['job_id'] = job['id']
            
            # Get all jobs
            self.run_test("Get all jobs", "GET", "jobs", 200)
            
            # Get specific job
            self.run_test("Get job by ID", "GET", f"jobs/{job['id']}", 200)
            
            # Update job status
            update_data = {"status": "in_production"}
            self.run_test("Update job", "PUT", f"jobs/{job['id']}", 200, update_data)
            
            return True
        return False

    def test_invoices_crud(self):
        """Test invoices CRUD operations"""
        print("\n" + "="*50)
        print("TESTING INVOICES CRUD")
        print("="*50)
        
        if 'customer_id' not in self.test_data:
            print("❌ Skipping invoices test - no customer available")
            return False
            
        # Create invoice
        invoice_data = {
            "customer_id": self.test_data['customer_id'],
            "job_id": self.test_data.get('job_id'),
            "total": 225.00,
            "status": "draft",
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
            "notes": "Test invoice"
        }
        success, invoice = self.run_test("Create invoice", "POST", "invoices", 200, invoice_data)
        if success and invoice:
            self.test_data['invoice_id'] = invoice['id']
            
            # Get all invoices
            self.run_test("Get all invoices", "GET", "invoices", 200)
            
            # Get specific invoice
            self.run_test("Get invoice by ID", "GET", f"invoices/{invoice['id']}", 200)
            
            # Update invoice status
            update_data = {"status": "paid"}
            self.run_test("Update invoice", "PUT", f"invoices/{invoice['id']}", 200, update_data)
            
            # Create invoice from job
            if 'job_id' in self.test_data:
                self.run_test("Create invoice from job", "POST", f"invoices/from-job/{self.test_data['job_id']}", 200)
            
            return True
        return False

    def test_employees_and_timeclock(self):
        """Test employee and time clock operations"""
        print("\n" + "="*50)
        print("TESTING EMPLOYEES & TIME CLOCK")
        print("="*50)
        
        # Create employee
        employee_data = {
            "name": "Test Employee",
            "hourly_rate": 20.00,
            "is_active": True
        }
        success, employee = self.run_test("Create employee", "POST", "employees", 200, employee_data)
        if success and employee:
            self.test_data['employee_id'] = employee['id']
            
            # Get all employees
            self.run_test("Get all employees", "GET", "employees", 200)
            
            # Get specific employee
            self.run_test("Get employee by ID", "GET", f"employees/{employee['id']}", 200)
            
            # Test time clock sequence
            employee_id = employee['id']
            
            # Start work
            self.run_test("Clock in - start work", "POST", "timeclock", 200, 
                         {"employee_id": employee_id, "action": "start_work"})
            
            # Get clock status
            self.run_test("Get clock status", "GET", f"timeclock/{employee_id}/status", 200)
            
            # Start break
            self.run_test("Clock - start break", "POST", "timeclock", 200, 
                         {"employee_id": employee_id, "action": "break_start"})
            
            # End break
            self.run_test("Clock - end break", "POST", "timeclock", 200, 
                         {"employee_id": employee_id, "action": "break_end"})
            
            # End work
            self.run_test("Clock out - end work", "POST", "timeclock", 200, 
                         {"employee_id": employee_id, "action": "end_work"})
            
            # Get today's logs
            self.run_test("Get today's logs", "GET", f"timeclock/{employee_id}/today", 200)
            
            # Get shift summary
            self.run_test("Get shift summary", "GET", f"timeclock/{employee_id}/summary", 200)
            
            return True
        return False

    def test_payroll(self):
        """Test payroll operations"""
        print("\n" + "="*50)
        print("TESTING PAYROLL")
        print("="*50)
        
        if 'employee_id' not in self.test_data:
            print("❌ Skipping payroll test - no employee available")
            return False
            
        employee_id = self.test_data['employee_id']
        
        # Create earnings transaction
        earnings_data = {
            "employee_id": employee_id,
            "type": "earnings",
            "amount": 160.00,
            "description": "8 hours @ $20/hr",
            "date": date.today().isoformat()
        }
        self.run_test("Create earnings transaction", "POST", "payroll/transactions", 200, earnings_data)
        
        # Create advance transaction
        advance_data = {
            "employee_id": employee_id,
            "type": "advance",
            "amount": 50.00,
            "description": "Cash advance",
            "date": date.today().isoformat()
        }
        self.run_test("Create advance transaction", "POST", "payroll/transactions", 200, advance_data)
        
        # Get payroll balance
        self.run_test("Get payroll balance", "GET", f"payroll/balance/{employee_id}", 200)
        
        # Get payroll transactions
        self.run_test("Get payroll transactions", "GET", "payroll/transactions", 200)
        
        # Get payroll report
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        self.run_test("Get payroll report", "GET", "payroll/report", 200, 
                     params={"start_date": start_date, "end_date": end_date})
        
        return True

    def test_financials(self):
        """Test financial operations"""
        print("\n" + "="*50)
        print("TESTING FINANCIALS")
        print("="*50)
        
        # Create sales entry
        sales_data = {
            "date": date.today().isoformat(),
            "amount": 500.00,
            "tax_amount": 40.00,
            "description": "Sign installation payment"
        }
        self.run_test("Create sales entry", "POST", "financials/sales", 200, sales_data)
        
        # Create expense entry
        expense_data = {
            "date": date.today().isoformat(),
            "amount": 150.00,
            "category": "materials",
            "description": "Vinyl and hardware"
        }
        self.run_test("Create expense entry", "POST", "financials/expenses", 200, expense_data)
        
        # Get sales entries
        self.run_test("Get sales entries", "GET", "financials/sales", 200)
        
        # Get expense entries
        self.run_test("Get expense entries", "GET", "financials/expenses", 200)
        
        # Get financial summary
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        self.run_test("Get financial summary", "GET", "financials/summary", 200, 
                     params={"start_date": start_date, "end_date": end_date})
        
        return True

    def test_tasks(self):
        """Test task operations"""
        print("\n" + "="*50)
        print("TESTING TASKS")
        print("="*50)
        
        # Create task
        task_data = {
            "title": "Design banner layout",
            "description": "Create 3 layout options for client review",
            "job_id": self.test_data.get('job_id'),
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
            "is_complete": False
        }
        success, task = self.run_test("Create task", "POST", "tasks", 200, task_data)
        if success and task:
            self.test_data['task_id'] = task['id']
            
            # Get all tasks
            self.run_test("Get all tasks", "GET", "tasks", 200)
            
            # Update task
            update_data = {"is_complete": True}
            self.run_test("Update task", "PUT", f"tasks/{task['id']}", 200, update_data)
            
            return True
        return False

    def test_ai_tools(self):
        """Test AI tools functionality"""
        print("\n" + "="*50)
        print("TESTING AI TOOLS")
        print("="*50)
        
        # Test layout generator
        ai_request = {
            "tool": "layout_generator",
            "input_data": {
                "product_type": "Banner",
                "size": "4ft x 8ft",
                "text_content": "GRAND OPENING - 50% OFF",
                "colors": "Red, White, Blue",
                "style": "Bold and Eye-catching"
            }
        }
        success, response = self.run_test("AI Layout Generator", "POST", "ai/generate", 200, ai_request)
        if success:
            # Get AI history
            self.run_test("Get AI history", "GET", "ai/history", 200, params={"tool": "layout_generator"})
            return True
        return False

    def test_webstores(self):
        """Test webstore operations"""
        print("\n" + "="*50)
        print("TESTING WEBSTORES")
        print("="*50)
        
        # Create fundraiser campaign
        fundraiser_data = {
            "name": "School Band Fundraiser",
            "goal": 5000.00,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
            "organizer": "Lincoln High School",
            "products": ["T-Shirts", "Banners", "Stickers"]
        }
        success, fundraiser = self.run_test("Create fundraiser", "POST", "webstores/fundraiser", 200, fundraiser_data)
        if success and fundraiser:
            self.test_data['fundraiser_id'] = fundraiser['id']
            
            # Get fundraisers
            self.run_test("Get fundraisers", "GET", "webstores/fundraiser", 200)
            
            # Get specific fundraiser
            self.run_test("Get fundraiser by ID", "GET", f"webstores/fundraiser/{fundraiser['id']}", 200)
        
        # Create B2B store
        b2b_data = {
            "company_name": "ABC Corporation",
            "contact_email": "orders@abc.com",
            "login_password": "secure123",
            "allowed_products": ["Business Cards", "Letterhead", "Banners"],
            "discount_percent": 15.0
        }
        success, b2b_store = self.run_test("Create B2B store", "POST", "webstores/b2b", 200, b2b_data)
        if success and b2b_store:
            self.test_data['b2b_store_id'] = b2b_store['id']
            
            # Get B2B stores
            self.run_test("Get B2B stores", "GET", "webstores/b2b", 200)
            
            # Test B2B login
            self.run_test("B2B store login", "POST", f"webstores/b2b/{b2b_store['id']}/login", 200, 
                         params={"password": "secure123"})
        
        # Create webstore order
        if 'fundraiser_id' in self.test_data:
            order_data = {
                "store_type": "fundraiser",
                "store_id": self.test_data['fundraiser_id'],
                "items": [{"product": "T-Shirt", "quantity": 10, "price": 15.00}],
                "total": 150.00
            }
            self.run_test("Create webstore order", "POST", "webstores/orders", 200, order_data)
            
            # Get webstore orders
            self.run_test("Get webstore orders", "GET", "webstores/orders", 200)
        
        return True

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n" + "="*50)
        print("TESTING DASHBOARD STATS")
        print("="*50)
        
        self.run_test("Get dashboard stats", "GET", "dashboard/stats", 200)
        return True

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n" + "="*50)
        print("CLEANING UP TEST DATA")
        print("="*50)
        
        # Delete in reverse order of dependencies
        if 'task_id' in self.test_data:
            self.run_test("Delete task", "DELETE", f"tasks/{self.test_data['task_id']}", 200)
        
        if 'job_id' in self.test_data:
            self.run_test("Delete job", "DELETE", f"jobs/{self.test_data['job_id']}", 200)
        
        if 'customer_id' in self.test_data:
            self.run_test("Delete customer", "DELETE", f"customers/{self.test_data['customer_id']}", 200)

def main():
    print("🚀 Starting Sign Guy AI API Tests")
    print("=" * 60)
    
    tester = SignGuyAPITester()
    
    # Run all tests
    try:
        tester.test_health_check()
        tester.test_customers_crud()
        tester.test_quotes_crud()
        tester.test_jobs_crud()
        tester.test_invoices_crud()
        tester.test_employees_and_timeclock()
        tester.test_payroll()
        tester.test_financials()
        tester.test_tasks()
        tester.test_ai_tools()
        tester.test_webstores()
        tester.test_dashboard_stats()
        
        # Cleanup
        tester.cleanup_test_data()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
    
    # Print results
    print("\n" + "="*60)
    print("📊 TEST RESULTS")
    print("="*60)
    print(f"Tests run: {tester.tests_run}")
    print(f"Tests passed: {tester.tests_passed}")
    print(f"Tests failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%" if tester.tests_run > 0 else "0%")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())