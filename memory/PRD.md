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

## Pricing Tiers (Updated Feb 18, 2026)
- **Starter Shop:** $79/mo founder, $129/mo regular
  - Customer Management, Quotes & Jobs, Basic Invoicing
  - 1 Webstore, 25 AI generations/month, 1 Team member
  - 100MB Storage, Email Support
- **Growth Shop:** $129/mo founder, $229/mo regular (Most Popular)
  - Everything in Starter, plus:
  - 5 Webstores, 100 AI generations/month, 5 Team members
  - 1GB Storage, Time Clock & Payroll, Kanban & Calendar
  - Advanced Analytics, Priority Support
- **Pro Shop:** $199/mo founder, $379/mo regular
  - Everything in Growth, plus:
  - Unlimited Webstores, AI generations, Team members
  - 5GB Storage, B2B Features, BNPL Payments
  - Custom Reports, SMS Notifications, API Access, Dedicated Support
- **AI Tools Add-On:** $49/mo founder, $89/mo later (standalone or with any plan)
- **Extended Trial:** $19.99 for 14 days (credits toward Tier 3)

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
- [x] **Website & Pricing Updates (Feb 18, 2026):**
  - Pricing tiers: Starter $79, Growth $129, Pro $199 (founder)
  - AI Tools Add-On: $49/mo founder
  - Comparison table cleaned up (no alternating colors)
  - Added new features to comparison table
- [x] **Employee Portal Permissions (Feb 18, 2026):**
  - Settings page section for controlling employee access
  - Portal Sections: Tasks, Schedule, Pay Stubs, Time Clock, Edit Profile
  - Sensitive Info: Job Details, Customer Info, Pricing (all OFF by default)
- [x] **Customer CSV Import (Feb 18, 2026):**
  - Import CSV button on Customers page
  - Column mapping interface
  - Download template feature
  - Bulk create/update customers
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
- [ ] Complete Billing System Logic - track first 100 founders, $19.99 credit, AI Tools Add-On
- [ ] Re-enable Trial Lockout System - fix root cause, not just disable
- [x] **Pricing Calculator Major Overhaul (Feb 18, 2026):** FIXED - Industry-standard pricing
  - **Previous Issue:** Prices were WAY TOO HIGH (e.g., $80+ for a 12x12 decal)
  - **Root Cause:** Complexity defaulted to 5 (mid-range) + aggressive labor calculations + automatic setup fees
  - **Changes Made:**
    - Complexity now defaults to 1 (simple) instead of 5
    - Setup fee is now OPTIONAL via checkbox (one-time per order, not per item)
    - Simplified labor calculations to flat rate per sqft
    - Aligned pricing with industry standards ($5-8/sqft for cut vinyl)
    - Example: 12x12 simple decal now costs **$5.00** (was $80+)
    - Example: 4x8 banner now costs **$140** (was ~$270+)
    - Example: 25 t-shirts with HTV now costs **$1,083** (~$43/shirt)
  - Fixed route conflict: `/pricing-calculator` for internal app, `/pricing` for public SaaS pricing
- [x] **Job Time Tracking (Feb 17, 2026):**
  - Start/Stop timer on jobs with task type selection
  - Track time by: design, production, installation, admin
  - Time Log showing all entries with employee, duration, labor cost
  - Summary panel with total hours, labor cost, entry count
  - Delete time entries
  - Real-time running timer display (HH:MM:SS)
  - Prevents duplicate active timers per employee per job
  - API endpoints: /api/jobs/{id}/time/start, stop, summary, active
- [x] **Job Status Timeline (Feb 17, 2026):**
  - Visual status flow diagram: Quoted → Approved → In Production → Installed → Complete
  - Green checkmarks for completed stages, highlighted current stage
  - Status Change History section with old/new status, timestamps
  - Shows time spent in previous status (e.g., "2 min in previous status")
  - Timeline tab in Job Details page
  - Activities logged on status change with old_value and new_value

## Future Tasks (P2/P3)
- [x] **Public Landing Page (Feb 17, 2026):** Marketing website with hero, features, AI tools showcase, comparison table, pricing tiers, FAQ - accessible at /home
- [x] **Marketing Site Integration (Feb 18, 2026):**
  - Added "View Website" link button in dashboard (bottom-right corner)
  - Fixed landing page screenshot display using AI-generated mockup images
  - All 4 screenshot tabs (Dashboard, Jobs, AI Tools, Customers) now working
  - Images hosted on static.prod-images.emergentagent.com
- [x] **Additional AI Tools (Feb 18, 2026):**
  - Logo Refresher - upload logo, get modern style variations (3 images)
  - Generative Fill / Image Expander - expand images with AI (2 images)
  - Text to Image Creator - generate images from prompts (3 images)
  - Idea Brainstormer - taglines, logo concepts, business names
  - Sign Permit Research - permit guidance for any location
  - AI Business Assistant - full chat interface for sign shop questions
  - Blog Article Creator - full blog articles with SEO optimization
  - Completed Job Post Creator - social media content from job photos
  - Vehicle Wrap Mockup Generator - see designs on various vehicle types
  - **Total: 24 AI Tools across 4 categories**
- [x] **AI Email Integration (Feb 18, 2026):**
  - AI Email Composer component for contextual email drafting
  - Invoice emails: Send, Reminder, Overdue notices
  - Quote emails: Send, Follow-up
  - Added "AI Draft" button to Invoice Preview Modal
  - Added "AI Draft" button to Quote Preview Modal
  - Backend /api/ai/generate-email endpoint
- [x] **Documentation & Help Center (Feb 18, 2026):**
  - Complete docs site at /docs with sidebar navigation
  - Getting Started guide (5-step walkthrough)
  - Feature docs: Customers, Quotes & Jobs, Invoicing, Pricing Calculator
  - Advanced docs: AI Tools Suite, Time Tracking, Employee Management
  - FAQ section with collapsible questions
  - "Docs" link added to landing page navigation
- [ ] **Mobile Responsiveness (P1):** Owner dashboard mobile optimization
- [ ] **Mobile Responsiveness (P0):** Optimize owner dashboard for mobile - collapsible sidebar, mobile-friendly tables, touch-optimized buttons
- [ ] **RaceWrap AI Tool (P2):** Race Car Number & Sponsor Wrap Designer - custom race car numbers, full/partial wrap concepts, sponsor placement strategies (see ROADMAP.md for full specs)
- [ ] Form & Document Library - questionnaires, inspections, aftercare guides with AI summarization, PDF export
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
- `/api/dashboard/onboarding-status` - GET onboarding checklist status (NEW)

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

## Recent Updates (Feb 20, 2026)

### Annual Billing & Trial Credits
- Added annual billing option (save 2 months - pay for 10 months, get 12)
- Billing interval toggle (Monthly/Annual) on pricing page
- Extended trial $19.99 now creates credit that auto-applies to Tier 3 subscription
- Trial credits tracked in subscription record (`trial_credits_applied`, `trial_credits_used`)
- New endpoint: `GET /api/billing/trial-credits` to check available credits
- Pricing card dynamically shows monthly equivalent when annual is selected
- Added `amount_annual`, `annual_savings` to all pricing plans

### Dynamic Onboarding Checklist
- Added `GET /api/dashboard/onboarding-status` endpoint to dynamically track user setup progress
- Tracks: company info, pricing config, email templates, customers, imported customers, employees, quotes, webstores, documents, AI usage
- Frontend `OnboardingChecklist.js` now fetches status from the dedicated endpoint (single API call vs multiple)
- Shows "X of 10 completed" with real-time progress

### Scroll-to-Top Navigation Fix
- Added `ScrollToTop.js` component that scrolls to top on route changes
- Fixes issue where navigating to pages (especially docs) started users in the middle of content
- Integrated into App.js router

### Completed in Previous Session
- Webstore creation bug fix
- Logo & banner uploads for webstores
- Smart Document Library with send-to-email/portal
- Email Template System (admin-editable)
- "Approvals" module moved to Tools section

## Known Issues
- "Business" badge in bottom-right is PREVIEW TIER SELECTOR (not a bug)

## Test Credentials
- **Admin:** testuser123@test.com / Test123!
- **Customer Portal:** customer@test.com
- **Employee Portal:** john@signshop.com / PIN: 5678

## UI Theme (NON-NEGOTIABLE)
- Dark shell background: `#0B0F17`
- Light content cards: `#FFFFFF` or `#F7F8FA`
- Dark text on cards: `#111827` or `#374151`
- Blue accents ONLY: `#2F8BFB` (hover: `#1E7AF0`)
- Secondary dark surfaces: `#111826`
- This theme has been applied to: Dashboard, LandingPage, FeaturesPage, PricingPagePublic, AboutPage, ContactPage

## Recent Fixes (Feb 19, 2026)
- **Trial Lockout Re-enabled:** Users with expired trials will now see the lockout screen
- **Dashboard Badge Fix:** Status badges in "Today's Schedule" now have high-contrast colors (solid backgrounds with white/black text)
- **Theme Consistency:** Applied blue accent color (#2F8BFB) across all marketing pages (was using teal #00D4FF)
- **Background Colors:** Standardized dark backgrounds to #0B0F17 and secondary surfaces to #111826
- **Logo Updates:** Updated to new brand logos:
  - Slant logo on sign-in page

## Security Audit - Tenant Isolation (Feb 19, 2026) - COMPLETE ✅
Comprehensive security audit completed to ensure complete data isolation between tenants.

### Vulnerabilities Fixed:
1. **tasks.py** - ALL routes now require authentication and filter by tenant_id (was completely unprotected!)
2. **jobs.py** - job_items standalone routes now require auth and verify parent job belongs to tenant
3. **employees.py** - Employee update now returns tenant-filtered result
4. **invoices.py** - Invoice update now returns tenant-filtered result
5. **dashboard.py** - All related object lookups (customer, job) now include tenant_id filter
6. **webstores.py** - create-job-from-order now verifies webstore ownership
7. **webstores.py** - Product update route now properly filters by tenant_id

### Test Coverage:
- **28 security tests** across 11 API domains
- All APIs verified: Customers, Employees, Jobs, Tasks, Job Items, Quotes, Invoices, Webstores, Products, Dashboard, Payroll
- Cross-tenant access tested for: LIST, GET, UPDATE, DELETE operations
- Authentication required tests for all endpoints

### Result:
- **100% pass rate** (28/28 tests)
- No data leaks possible between tenants
- Test file: `/app/backend/tests/test_tenant_isolation_security.py`

## Artwork Approvals Module (Feb 20, 2026) - COMPLETE ✅
Full artwork proof approval system for managing customer artwork reviews.

### Features:
1. **Dashboard with Stats Cards:**
   - Total Proofs count
   - Awaiting Approval count (yellow)
   - Approved count (green)
   - Needs Revisions count (orange)
   - Clickable cards filter the main list

2. **Approval Request Creation:**
   - Select customer from dropdown
   - Select job (filtered by customer)
   - Upload artwork file (PNG, JPG)
   - Add notes for customer
   - Client-side watermarking with:
     - Diagonal company name pattern
     - Bottom disclaimer: "PROOF ONLY - Artwork remains property of [Company] until final payment is received"

3. **Approval Management:**
   - View proof preview
   - Track version numbers
   - See customer feedback
   - Resend notifications
   - Delete proofs

4. **Customer Portal Integration:**
   - Proofs sent to customer portal
   - Notifications created automatically
   - Customer can approve/request revisions

### API Endpoints:
- `GET /api/approvals/stats` - Dashboard statistics
- `GET /api/approvals` - List proofs (filterable by status)
- `POST /api/approvals` - Create new proof
- `GET /api/approvals/{id}` - Get single proof
- `DELETE /api/approvals/{id}` - Delete proof
- `POST /api/approvals/{id}/resend` - Resend notification
- `GET /api/approvals/customers/list` - Customers for dropdown
- `GET /api/approvals/jobs/list` - Jobs for dropdown

### Test Results:
- Backend: 27/27 tests passed
- Frontend: 14/14 tests passed

## Webstores Module (Feb 19, 2026) - FULLY TESTED
Complete webstore system for B2B, Fundraiser, and Creator stores.

### Features Implemented:
1. **Product Catalog:**
   - Products support up to 3 images (UI allows adding/removing images)
   - Apparel tier variants: Economy (+$0), Standard (+$5), Premium (+$12)
   - Quick-add buttons for apparel/decal size variants
   - Categories: Apparel, Signs, Decals, Promotional, Other
   - Variants with size, color, tier, and custom price modifiers

2. **Webstore Management:**
   - Create Business, Fundraiser, or Creator webstores
   - Custom branding (logo, primary color)
   - Add products from catalog to webstores
   - Track sales, profit, orders per store
   - Orders tab shows customer info and linked job IDs

3. **Public Storefront:**
   - Accessible at `/store/{webstore_id}` without login
   - Shows store name, description, products
   - Image carousel for multi-image products
   - Variant selection dropdown (size/color/tier)
   - Add to cart and checkout flow

4. **Order to Job Pipeline:**
   - Orders auto-create jobs with status "Approved"
   - Job named "Webstore Order - {Customer Name}"
   - Customer auto-created if doesn't exist
   - Job items created from order line items
   - Order linked to job via job_id field

### API Endpoints:
- `POST /api/products` - Create product with images and variants
- `GET /api/products/defaults/apparel-options` - Get tier/size defaults
- `GET /api/storefront/{id}` - Public store info (no auth)
- `GET /api/storefront/{id}/products` - Public products (no auth)
- `POST /api/webstores/v2/orders` - Create order (auto-creates job)
- `GET /api/webstores/v2/orders` - List orders (tenant-filtered)

### Test Results:
- Backend: 16/16 tests passed
- Frontend: All UI flows verified
- E2E: Full order flow tested (storefront → order → job)
  - Long logo ("The Sign Guy AI") in marketing headers
  - Square logo in app sidebar and Employee Portal
- **Promo Codes System:** Admin feature to create discount codes for friends/beta testers
  - Create codes with % off, $ off, or free extended trial
  - Track usage, set limits and expiration dates
  - Located in Admin > Promo Codes
- **Employee Portal Branding:** Replaced hardhat icon with SignGuy AI square logo
- **Employee Profile Images:** Employees can now upload their own profile photos via the Profile page

## Last Updated
February 19, 2026
