"""
SignGuy AI Routes Module

This module contains API route handlers organized by domain.
Routes are being migrated from server.py to individual modules.

Completed migrations:
- auth.py - Authentication routes
- customers.py - Customer CRUD routes
- pricing.py - Pricing calculator routes

Pending migrations:
- jobs.py - Job management routes
- quotes.py - Quote routes
- invoices.py - Invoice routes
- portal.py - Customer portal routes
- webstores.py - Webstore routes
- time_clock.py - Time clock routes
- payroll.py - Payroll routes
"""

# Note: These routes are defined but not yet integrated into the main app
# The server.py still handles all routes. These modules serve as 
# the target architecture for the gradual migration.

# from .auth import router as auth_router, users_router, admin_router
# from .customers import router as customers_router
# from .pricing import router as pricing_router

