# SignGuy AI - Product Requirements Document

## Original Problem Statement
Create a comprehensive SaaS product for sign shops called "SignGuy AI" with:
- **Core Business Modules:** Customer Management, Quotes/Jobs, Invoicing, Productivity, Financials, Employee Time/Payroll
- **Customer Portal:** Secure portal for customers to manage profile, view orders, approve artwork, make payments, communicate
- **Webstores Module:** B2B, Fundraiser, and Creator webstores
- **SaaS Billing & Tiers:** 24-hour free trial, 14-day extended trial, Founder pricing (first 100), AI Tools Add-On, standard pricing
- **Employee Portal:** Dedicated portal with tier-gated features
- **Advanced Features:** Pricing calculators, AI tools suite, job status/timeline tracker, AI business assistant
- **Integrations:** Stripe (in progress), future BNPL, SMS, QuickBooks
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
│   └── server.py       # Main FastAPI app
├── frontend/
│   ├── src/
│   │   ├── components/ # UI components (TrialLockout.js, MainLayout.js, ui/)
│   │   ├── context/    # React contexts (AuthContext, TierContext, etc.)
│   │   ├── pages/      # Page components (Dashboard.js, etc.)
│   │   └── index.css   # Global theme variables
│   └── tailwind.config.js
└── memory/
    └── PRD.md
```

## Completed Features
- [x] User authentication with JWT
- [x] Multi-tenant architecture with RBAC
- [x] Customer Management module
- [x] Quotes & Jobs module
- [x] Invoicing module
- [x] Time Clock & Payroll
- [x] Customer Portal (full-featured)
- [x] Standalone Pricing Calculator
- [x] 24-hour trial lockout system (TEMPORARILY DISABLED for testing)
- [x] Dark shell + light content surface theme overhaul
- [x] Pricing page with 5-tier structure (24hr trial, extended trial, 3 tiers, AI add-on)
- [x] Stripe TEST keys configured
- [x] **Dashboard Enhancement (Feb 16, 2026):**
  - Home is now top-level direct link in sidebar
  - Personalized greeting with time-based icon
  - Today's Schedule widget
  - Messages widget
  - Pending Approvals widget
  - Clocked In Employees widget
  - 5 new dashboard API endpoints

## In Progress
- [ ] Billing System Testing - backend routes need production testing

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

### Dashboard (NEW)
- `/api/dashboard/stats` - GET dashboard statistics
- `/api/dashboard/pending-approvals` - GET proofs awaiting approval
- `/api/dashboard/unread-messages` - GET unread customer messages
- `/api/dashboard/clocked-in` - GET employees currently clocked in
- `/api/dashboard/todays-schedule` - GET jobs due today

### Billing
- `/api/billing/pricing` - GET available plans
- `/api/billing/trial-status` - GET user's trial status
- `/api/billing/checkout` - POST create Stripe checkout
- `/api/tiers/my-plan` - GET user's current plan & features

## Known Issues
- Trial lockout TEMPORARILY DISABLED for development/testing
- Billing system backend untested in production

## Test Credentials
- Email: testuser123@test.com
- Password: Test123!

## Last Updated
February 16, 2026
