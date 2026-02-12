"""
SignGuy AI Routes Module

This module contains API route handlers organized by domain.
Routes are being migrated from server.py to individual modules.

Completed migrations:
- auth.py - Authentication routes (register, login, profile, admin user management)
- customers.py - Customer CRUD routes
- pricing.py - Pricing calculator routes (calculate, templates, materials, defaults)
- quotes.py - Quote CRUD routes (create, update, convert to job)
- jobs.py - Job management routes (CRUD, items, notes, activities, status)
- invoices.py - Invoice routes (CRUD, from-job, payments)

Pending migrations:
- portal.py - Customer portal routes
- webstores.py - Webstore routes
- time_clock.py - Time clock routes
- payroll.py - Payroll routes
- employees.py - Employee management routes
- financials.py - Financial reports/dashboard routes
"""

# Note: These routes are defined but not yet integrated into the main app
# The server.py still handles all routes. These modules serve as 
# the target architecture for the gradual migration.

# from .auth import router as auth_router, users_router, admin_router
# from .customers import router as customers_router
# from .pricing import router as pricing_router
# from .quotes import router as quotes_router
# from .jobs import router as jobs_router, job_items_router, job_notes_router
# from .invoices import router as invoices_router


