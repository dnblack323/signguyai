# SignGuy AI - Product Requirements Document

## Original Problem Statement
Create a comprehensive SaaS product for sign shops called "SignGuy AI" with:
- **Core Business Modules:** Customer Management, Quotes/Jobs, Invoicing, Productivity, Financials, Employee Time/Payroll
- **Customer Portal:** Secure portal for customers to manage profile, view orders, approve artwork, make payments, communicate
- **Webstores Module:** B2B, Fundraiser, and Creator webstores
- **SaaS Billing & Tiers:** 24-hour free trial, 14-day extended trial, Founder pricing (first 100), AI Tools Add-On, standard pricing
- **Employee Portal:** Dedicated portal with tier-gated features
- **Advanced Features:** Pricing calculators, AI tools suite, job status/timeline tracker, AI business assistant
- **Integrations:** Stripe (TEST keys configured), future BNPL, SMS, QuickBooks
- **Theme:** Dark shell + light content surface design system

## Tech Stack
- **Backend:** FastAPI, Pydantic, Motor (MongoDB)
- **Frontend:** React, React Router, Tailwind CSS, Shadcn UI, Axios, React Context API
- **Database:** MongoDB
- **Payments:** Stripe (TEST keys configured)

## Current Architecture
```
/app/
├── backend/
│   ├── models/         # Pydantic models (billing.py, auth.py, jobs.py, etc.)
│   ├── routes/         # API routes (billing.py, auth.py, tiers.py, dashboard.py, etc.)
│   ├── services/       # Business logic (feature_gate.py, tier_config.py)
│   └── server.py       # Main FastAPI app with pricing calculator
├── frontend/
│   ├── src/
│   │   ├── components/ # UI components (TrialLockout.js, MainLayout.js, ui/)
│   │   ├── context/    # React contexts (AuthContext, TierContext, AppContext)
│   │   ├── pages/      # Page components (Dashboard.js, Quotes.js, Jobs.js, Invoices.js)
│   │   └── index.css   # Global theme variables
│   └── tailwind.config.js
└── memory/
    └── PRD.md
```

## Completed Features
- [x] User authentication with JWT
- [x] Multi-tenant architecture with RBAC
- [x] Customer Management module
- [x] Quotes & Jobs module with Convert to Job functionality
- [x] Invoicing module with email capability
- [x] Time Clock & Payroll
- [x] Customer Portal (full-featured)
- [x] Standalone Pricing Calculator with profit/margin calculations
- [x] 24-hour trial lockout system (TEMPORARILY DISABLED for testing)
- [x] Dark shell + light content surface theme overhaul
- [x] Pricing page with 5-tier structure
- [x] Stripe TEST keys configured
- [x] **Dashboard Enhancement (Feb 16, 2026):**
  - Home as top-level direct link in sidebar
  - Personalized greeting with time-based icon
  - Widgets: Today's Schedule, Messages, Pending Approvals, Clocked In
  - 5 dashboard API endpoints
- [x] **Bug Fixes (Feb 16, 2026):**
  - Job status badges with readable text colors
  - Quote preview with white background, dark text
  - Email buttons on Invoice and Quote previews
  - Pricing calculator profit_amount and profit_margin_percent
  - Convert Quote to Job available for all quotes
  - Invoice preview auth header fix
  - Edit Invoice SelectItem empty value bug fix

## Upcoming Tasks (P1)
- [ ] Employee Portal - separate login, tier-gated features (Time Clock, My Pay, My Tasks)
- [ ] Job Time Tracking - log time against specific jobs
- [ ] Job Status Flow & Timeline - visual timeline on job tickets

## Future Tasks (P2/P3)
- [ ] Efficiency Dashboard for employees
- [ ] AI Business Assistant (internal chat)
- [ ] Calendar + Kanban Views
- [ ] Integrations: BNPL (Affirm/Klarna), SMS (Twilio), QuickBooks
- [ ] Custom Domain Support for webstores
- [ ] Re-enable trial lockout once billing complete

## Key API Endpoints

### Dashboard
- `/api/dashboard/stats` - GET dashboard statistics
- `/api/dashboard/pending-approvals` - GET proofs awaiting approval
- `/api/dashboard/unread-messages` - GET unread customer messages
- `/api/dashboard/clocked-in` - GET employees currently clocked in
- `/api/dashboard/todays-schedule` - GET jobs due today

### Pricing Calculator
- `/api/pricing/calculate` - POST calculate pricing with profit/margin

### Billing
- `/api/billing/pricing` - GET available plans
- `/api/billing/trial-status` - GET user's trial status
- `/api/billing/checkout` - POST create Stripe checkout

## Known Issues
- Trial lockout TEMPORARILY DISABLED for development/testing
- Quick Actions navigate to pages (not modals) - by design

## Test Credentials
- Email: testuser123@test.com
- Password: Test123!
- Customer: customer@test.com

## Last Updated
February 16, 2026
