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
- **Payments:** Stripe (LIVE keys currently - need TEST keys)

## Current Architecture
```
/app/
├── backend/
│   ├── models/         # Pydantic models (billing.py, auth.py, jobs.py, etc.)
│   ├── routes/         # API routes (billing.py, auth.py, tiers.py, etc.)
│   ├── services/       # Business logic (feature_gate.py, tier_config.py)
│   └── server.py       # Main FastAPI app
├── frontend/
│   ├── src/
│   │   ├── components/ # UI components (TrialLockout.js, layout/, ui/)
│   │   ├── context/    # React contexts (AuthContext, TierContext, etc.)
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
- [x] Quotes & Jobs module
- [x] Invoicing module
- [x] Time Clock & Payroll
- [x] Customer Portal (full-featured)
- [x] Standalone Pricing Calculator
- [x] 24-hour trial lockout system (TEMPORARILY DISABLED)
- [x] Dark shell + light content surface theme overhaul
- [x] Backend billing models/routes (needs testing)

## In Progress
- [ ] Billing System Refactor - backend updated but untested, frontend PricingPage.js needs complete rewrite

## Upcoming Tasks (P1)
- [ ] Dashboard Enhancement - Home link, widgets for greeting, schedule, approvals, messages
- [ ] Employee Portal - separate login, tier-gated features (Time Clock, My Pay, My Tasks)
- [ ] Job Time Tracking - log time against specific jobs
- [ ] Job Status Flow & Timeline - visual timeline on job tickets

## Future Tasks (P2/P3)
- [ ] Efficiency Dashboard for employees
- [ ] AI Business Assistant (internal chat)
- [ ] Calendar + Kanban Views
- [ ] Integrations: BNPL (Affirm/Klarna), SMS (Twilio), QuickBooks
- [ ] Custom Domain Support for webstores

## Key API Endpoints
- `/api/billing/pricing` - GET available plans
- `/api/billing/trial-status` - GET user's trial status
- `/api/billing/checkout` - POST create Stripe checkout
- `/api/tiers/my-plan` - GET user's current plan & features

## Known Issues
- Trial lockout TEMPORARILY DISABLED for development
- LIVE Stripe keys in use (should switch to TEST)
- PricingPage.js outdated for new 5-tier structure

## Last Updated
February 16, 2026
