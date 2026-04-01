## Employee/Auth Testing Notes

- Verify owner/admin login still works via `/api/auth/login`
- Verify employee portal login works via `/api/employee-portal/auth/login`
- Verify disabled employee accounts cannot log in
- Verify employee portal section access respects tenant `employee_portal_settings`
- Verify admin-only employee lifecycle actions (deactivate/delete/reset PIN) remain blocked for non-admin users
- Verify payroll/timeclock admin mutations remain admin-only
- Verify auth token storage now prefers `sessionStorage` by default and only uses `localStorage` for remembered admin login persistence