# Test Credentials

## Production Admin Account (USER'S PRIMARY — USE THIS)
- Email: thesigntistslab@gmail.com
- Password: password123
- Role: owner / platform_admin
- Tenant: The Signtists Lab (Founders Edition)
- Database: signguy_ai
- NOTE: This is the user's actual working admin account. Always use this for testing/instructions.

## Secondary Account (User's Father — DO NOT use unless explicitly instructed)
- Email: signguypa@gmail.com
- Password: Billnel323
- Tenant: The Signtists Lab (same tenant, signguy_ai database)

## Test Order for Drawing Pad
- Order ID: 1efe0ae8-473d-4d5f-bde7-dbfde8180cda
- Order Number: ORD-0001
- Customer: Test Customer

## Dev Test Account (test_database — NOT production)
- Email: testuser@example.com
- Password: TestPassword123!
- Note: This account is in test_database, NOT the production signguy_ai database

## Employee Portal Test Accounts
- Email: preview-payroll@example.com / PIN: 1234 (QA Test Employee - Iteration 104, employee_id=saas-launch-hub)
- Email: DNBLACK323@GMAIL.COM / Password: 1234 (Note: DNBLACK323 not in employees collection; use preview-payroll for portal)

## Customer Portal Test Account
- Email: taxtest_non@example.com / Password: portal123 (dklayb@gmail.com does NOT exist in production DB)
- Customer ID: 1eaeec1d-6fbb-48fa-aa96-ecc4298bdb8b (Tax Test Customer Non-Exempt)

## Meta/Facebook Integration — Tenant Isolation Test Account
- Email: tenant_b_isolation_test@example.com
- Password: IsolationTest@2026!
- Role: Tenant B isolation tester (created in iteration 126)
- Note: Used for multi-tenant isolation verification only

## Meta/Facebook — Seeded Test Data
- Test Page ID: TEST_PAGE_12345
- Linked Tenant: d9c5507b-879c-4bec-9736-1dc841334719 (signguypa@gmail.com)

## Staff Role User (for Payroll RBAC negative tests)
- Email: staff_payroll_test@test.com
- Password: StaffTest123!
- Role: staff (limited)
- Tenant: d9c5507b-879c-4bec-9736-1dc841334719 (Signtists Lab)
- Used for: verifying GET `/api/payroll/*` returns 403 for staff (security fix 2026-04-26)
