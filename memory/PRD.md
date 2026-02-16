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
│   ├── models/         # Pydantic models
│   ├── routes/         # API routes (billing, auth, tiers, dashboard, tasks, etc.)
│   ├── services/       # Business logic
│   └── server.py       # Main FastAPI app with pricing calculator
├── frontend/
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── context/    # React contexts
│   │   ├── pages/      # Page components
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
- [x] 24-hour trial lockout system (TEMPORARILY DISABLED)
- [x] Dark shell + light content surface theme
- [x] Pricing page with 5-tier structure
- [x] Stripe TEST keys configured
- [x] Dashboard Enhancement - Home link, widgets, 5 API endpoints
- [x] **Bug Fixes (Feb 16, 2026):**
  - Job status badges with readable text
  - Quote preview white background, dark text
  - Invoice preview white background, dark text
  - Email buttons on Invoice and Quote previews
  - Pricing calculator profit_amount and profit_margin_percent
  - Convert Quote to Job available for all quotes + icon in actions
  - Invoice preview auth header fix
  - AI Tools link restored (no permission required)
  - Kanban drag-and-drop functionality
  - Task CRUD API created (/api/tasks)
  - Kanban cards clickable to navigate to job
- [x] **Employee Portal (Feb 16, 2026):**
  - Separate login with email/PIN authentication
  - Dashboard with clock in/out, break management
  - Time clock status tracking (hours worked, break time)
  - My Pay page with earnings, YTD, balance owed
  - My Tasks page with assigned tasks
  - Profile page with clock history
  - Bottom navigation and responsive mobile-first design
  - JWT tokens with employee type
  - Backend tests created (/app/backend/tests/test_employee_portal.py)

## Upcoming Tasks (P1)
- [ ] Job Time Tracking - log time against specific jobs
- [ ] Job Status Flow & Timeline - visual timeline on job tickets
- [ ] Complete Billing System Logic - track first 100 founders, $19.99 credit, AI Tools Add-On
- [ ] Re-enable Trial Lockout System - fix root cause, not just disable

## Future Tasks (P2/P3)
- [ ] Efficiency Dashboard for employees
- [ ] AI Business Assistant (internal chat)
- [ ] Calendar + Kanban Views (Calendar view)
- [ ] Integrations: BNPL (Affirm/Klarna), SMS (Twilio), QuickBooks
- [ ] Custom Domain Support for webstores

## Key API Endpoints

### Dashboard
- `/api/dashboard/stats` - GET dashboard statistics
- `/api/dashboard/pending-approvals` - GET proofs awaiting approval
- `/api/dashboard/unread-messages` - GET unread customer messages
- `/api/dashboard/clocked-in` - GET employees currently clocked in
- `/api/dashboard/todays-schedule` - GET jobs due today

### Tasks (NEW)
- `/api/tasks` - GET/POST tasks
- `/api/tasks/{id}` - GET/PUT/DELETE task

### Pricing Calculator
- `/api/pricing/calculate` - POST calculate pricing with profit/margin

### Billing
- `/api/billing/pricing` - GET available plans
- `/api/billing/trial-status` - GET user's trial status
- `/api/billing/checkout` - POST create Stripe checkout

## Known Issues
- Trial lockout TEMPORARILY DISABLED for development/testing
- "Business" badge in bottom-right is PREVIEW TIER SELECTOR (not a bug)

## Test Credentials
- Email: testuser123@test.com
- Password: Test123!
- Customer: customer@test.com

## Last Updated
February 16, 2026
