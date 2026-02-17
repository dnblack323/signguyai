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
- [x] **Bug Fixes Batch 3 (Feb 17, 2026):**
  - User upgraded to Business tier (Payroll/Financials now accessible)
  - Job list rows fully clickable (not just eyeball icon)
  - Pricing calculator shows zeros initially (not blank)
  - Complexity slider now affects all calculator prices (1.0x to 2.0x multiplier)
  - Setup fee charged once per order (not per item)
  - Fixed Payroll report.map error (handles backend response format)
- [x] **AI Tools Suite (Feb 17, 2026):**
  - Created /api/ai/generate endpoint for text generation
  - Created /api/ai/generate-images endpoint for image generation
  - Created /api/ai/history endpoint for generation history
  - Using OpenAI GPT-5.2 for text, GPT Image 1 for images via Emergent LLM key
  - 15 AI tools across 4 categories: Design, Branding, Business, Marketing
  - Tools include: Photo Enhancer, Vectorizer, Font Identifier, Sign/Banner Designer,
    Tagline Generator, Brand Color Advisor, Proposal Writer, Review Responder, etc.
- [x] **AI Pricing Advisor (Feb 17, 2026):**
  - Added AI-powered pricing suggestions in calculator
  - Analyzes current pricing and provides actionable recommendations
  - Suggests quantity tiers, upsells, margin improvements
  - Purple-themed UI with Sparkles icon

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

## Future Features - Detailed Specs

### Smart Quote Builder (P2)
AI-powered quote generation from natural language descriptions.
- Input: "24x36 banner with grommets for outdoor use"
- Output: Full quote with materials, pricing, timeline
- Learns from shop's pricing history and preferences

### Form & Document Library (P2)
Comprehensive document management system for customer communication.

**Document Types:**
1. **Questionnaires** (Customer fills out via portal)
   - Logo Design Brief - colors, style, industry, competitors
   - Vehicle Wrap Questionnaire - vehicle info, design preferences, coverage
   - Sign Project Intake - location, size, materials, installation needs
   
2. **Inspection Checklists** (Staff fills out)
   - Pre-Wrap Vehicle Inspection - dents, rust, paint condition, measurements
   - Installation Checklist - site prep, mounting verification
   
3. **Aftercare Guides** (Auto-send to customer)
   - Vinyl/Wrap Care Instructions - washing, waxing, damage prevention
   - Sign Maintenance Guide - cleaning, inspection schedule
   - Apparel Care Instructions - washing, drying, storage

4. **AI-Generated Documents**
   - Custom documents created via AI Document Creator
   - Save to library for reuse

**Features:**
- 📎 Attach documents to jobs/orders
- 📧 Quick-send to customers via email
- 🌐 Customer portal questionnaire completion
- 🤖 AI summarizes questionnaire responses
- 💾 Save AI-created docs to library
- 🏷️ Template categories by job type
- 📄 **PDF Export** - branded with shop logo & colors
- 🎨 Customizable templates

**Starter Templates (Pre-built):**
- Vehicle Wrap Questionnaire
- Logo Design Brief  
- Sign Project Intake Form
- Pre-Wrap Vehicle Inspection
- Wrap Aftercare Guide
- Vinyl Care Instructions
- Apparel Washing Guide

**Customer Flow Example:**
```
1. Customer orders vehicle wrap
2. Auto-send: Vehicle Wrap Questionnaire (via portal)
3. Customer fills out in portal
4. AI summarizes responses → attached to job
5. Staff completes: Pre-Wrap Inspection Form
6. Job complete
7. Auto-send: Wrap Aftercare Guide (PDF, branded)
```

**Database Schema (Planned):**
- Document: {id, type, name, content, category, is_template, tenant_id}
- DocumentAttachment: {id, document_id, job_id, sent_at, completed_at}
- QuestionnaireResponse: {id, document_id, customer_id, responses, ai_summary}

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

### Employee Portal (NEW)
- `/api/employee-portal/auth/login` - POST employee login with email/PIN
- `/api/employee-portal/profile` - GET employee profile
- `/api/employee-portal/time-clock/status` - GET current clock status
- `/api/employee-portal/time-clock/punch` - POST clock action (start_work, break_start, break_end, end_work)
- `/api/employee-portal/time-clock/history` - GET clock history
- `/api/employee-portal/pay/summary` - GET pay summary (earnings, YTD, balance)
- `/api/employee-portal/tasks` - GET assigned tasks
- `/api/employee-portal/tasks/{id}/complete` - PUT mark task complete

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
- **Admin:** testuser123@test.com / Test123!
- **Customer Portal:** customer@test.com
- **Employee Portal:** john@signshop.com / PIN: 5678

## Last Updated
February 16, 2026
