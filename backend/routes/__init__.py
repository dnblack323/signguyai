"""
SignGuy AI Routes Module

This module contains API route handlers organized by domain.
All routes have been migrated from server.py to individual modules.

Completed migrations (100%):
- auth.py - Authentication routes (register, login, profile, admin user management)
- customers.py - Customer CRUD routes
- pricing.py - Pricing calculator routes (calculate, templates, materials, defaults)
- quotes.py - Quote CRUD routes (create, update, convert to job)
- jobs.py - Job management routes (CRUD, items, notes, activities, status)
- invoices.py - Invoice routes (CRUD, from-job, payments)
- portal.py - Customer portal routes (auth, profile, orders, messaging, proofs)
- employees.py - Employee, time clock, payroll routes
- webstores.py - Products catalog, webstores (B2B/Fundraiser/Creator), orders

Pending:
- financials.py - Financial reports/dashboard routes (optional, low priority)
"""

# Note: These routes are defined but not yet integrated into the main app
# The server.py still handles all routes. These modules serve as 
# the target architecture for the gradual migration.

# Uncomment these imports when ready to wire up:
# from .auth import router as auth_router, users_router, admin_router
# from .customers import router as customers_router
# from .pricing import router as pricing_router
# from .quotes import router as quotes_router
# from .jobs import router as jobs_router, job_items_router, job_notes_router
# from .invoices import router as invoices_router
# from .portal import router as portal_router
# from .employees import employees_router, timeclock_router, payroll_router
# from .webstores import products_router, webstores_router


