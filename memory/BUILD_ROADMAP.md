# SignGuy AI - Complete Build Roadmap & Feature Tracker

> **Last Updated:** March 18, 2026  
> **Version:** 4.0  
> **Status:** Active Development - Feature-Rich SaaS Platform

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Platform Stats](#platform-stats)
3. [Completed Features by Phase](#completed-features)
4. [SaaS Readiness Scorecard](#saas-readiness)
5. [Current Status & Active Tasks](#current-status)
6. [Upcoming Features](#upcoming-features)
7. [Future / Backlog](#future-backlog)
8. [Technical Architecture](#technical-architecture)

---

## Project Overview

**SignGuy AI** is a comprehensive multi-tenant SaaS operating system for sign shops, print shops, and custom graphics businesses. It replaces spreadsheets, notebooks, and disconnected tools with a unified platform.

**Target Market:** Sign shops, print shops, and custom graphics businesses  
**Business Model:** SaaS subscription with tiered pricing (3 product lines, 9 plans + Founders Edition)  
**Tech Stack:** React 18 + FastAPI + MongoDB + OpenAI (GPT-5.2, Whisper, TTS, GPT Image 1)

---

## Platform Stats (as of March 18, 2026)

| Metric | Count |
|--------|-------|
| Frontend Pages | 87 |
| Frontend Components | 81 |
| Frontend Routes | 98 |
| Backend Route Files | 33 |
| Backend API Endpoints | 289 |
| Backend Services | 11 |
| Backend Models | 12 |
| MongoDB Collections | 58 |
| AI Tools | 28+ |
| Frontend Lines of Code | 50,414 |
| Backend Lines of Code | 29,169 |
| **Total Lines of Code** | **~80,000** |

---

## Completed Features by Phase

### Phase 1: Core Infrastructure (Jan 2026)
| Feature | Status |
|---------|--------|
| FastAPI Backend + React Frontend + MongoDB | DONE |
| Hot Reload Development (Frontend & Backend) | DONE |
| JWT Authentication (24hr expiry, 30-day remember me) | DONE |
| Protected Routes + Redirect to Login | DONE |
| User Registration, Login, Logout, Profile | DONE |
| Password Recovery ("Forgot Password?" for owners) | DONE |
| Improved Login Error Handling | DONE |

### Phase 2: Customer Management (Jan 2026)
| Feature | Status |
|---------|--------|
| Customer CRUD with search, filter, pagination | DONE |
| Customer status tracking (Lead, Active, Inactive) | DONE |
| Contact info, notes, tags, tax exempt flag | DONE |
| CSV Import with column mapping + template download | DONE |
| Customer-specific pricing toggle | DONE |
| Portal access toggle + invite with temporary PIN | DONE |
| Inline customer creation from Job/Quote forms | DONE |
| Phone number auto-formatting | DONE |
| Name OR Company validation enforcement | DONE |

### Phase 3: Unified Jobs & Quotes (Jan 2026)
| Feature | Status |
|---------|--------|
| Unified jobs/quotes system (quote is a job in "quote" stage) | DONE |
| Status pipeline: quote -> approved -> in_progress -> completed -> invoiced -> archived | DONE |
| Line items (11 types: Banner, Yard Sign, Decal, Wrap, etc.) | DONE |
| Item status tracking (Pending, In Production, Done) | DONE |
| Job notes with timestamps + activity log | DONE |
| Convert quote to job (one-click approve) | DONE |
| Job time tracking (start/stop timer per job) | DONE |
| Job Status Timeline (visual flow + time-in-status) | DONE |
| Unified Job History feed | DONE |
| Customer Portal tab on job detail | DONE |
| Whole-job + stage-level employee assignment | DONE |
| Kanban board with drag-and-drop | DONE |

### Phase 4: Invoicing (Jan 2026)
| Feature | Status |
|---------|--------|
| Invoice CRUD with statuses (Draft, Sent, Paid, Overdue) | DONE |
| Create invoice from job (auto-populate items) | DONE |
| Tax calculation and auto-total | DONE |
| Invoice number auto-generation + due date tracking | DONE |
| PDF export (reportlab) | DONE |
| Email send with AI-drafted email option | DONE |
| Invoice preview modal | DONE |
| Stripe Connect "Pay Link" button | DONE |

### Phase 5: Time Clock & Payroll (Jan 2026)
| Feature | Status |
|---------|--------|
| Clock in/out with sequence validation | DONE |
| Break start/end tracking | DONE |
| Time entries per job with task type selection | DONE |
| Manual time entry + edit/delete | DONE |
| Real-time running timer display (HH:MM:SS) | DONE |
| Time reports by employee and by job | DONE |
| Kiosk mode (simplified clock-in interface) | DONE |
| Auto-suggest time entry on job status change | DONE |
| Admin Payroll - Overview Tab (pay period summary) | DONE |
| Admin Payroll - Time Sheets Tab (consolidated view) | DONE |
| Admin Payroll - Manual Hours Tab (CRUD) | DONE |
| Admin Payroll - Transactions Tab (earnings, advances, payments) | DONE |
| Overtime calculation (1.5x over 40hrs/week) | DONE |

### Phase 6: Productivity & Financial Tracking (Jan 2026)
| Feature | Status |
|---------|--------|
| Task management (create, assign, track, link to jobs) | DONE |
| Productivity dashboard | DONE |
| Revenue tracking by period | DONE |
| Expense tracking (21 categories) | DONE |
| Profit calculation + monthly summaries | DONE |

### Phase 7: AI Tools Suite (Feb 2026)
| Feature | Status |
|---------|--------|
| Design Tools (11): Photo Enhancer, Vectorizer, Font ID, Sign Designer, Banner Designer, Logo Refresher, Generative Fill, Text-to-Image, Logo Creator, Mockup Creator, Vehicle Wrap Mockup | DONE |
| Business Tools (6): Tagline Generator, Brand Color Advisor, Brand Voice Guide, Proposal Writer, Review Responder, Pricing Intelligence | DONE |
| Marketing Tools (6): Blog Creator, Job Post Creator, Showcase Post, Social Pack, Content Calendar, Campaign Builder | DONE |
| Racing Tools (4): Race Number Designer, Driver Name Plate, Wrap Cost Calculator, Race Team Branding Kit | DONE |
| Additional: Email Templates, SEO Content, Business Copywriter, Document Composer, AI Product Description Generator, Branding Kit Generator | DONE |
| AI History + Save to Job + Download PDF + Send to Customer | DONE |
| Credit system integration (1-3 credits per action) | DONE |
| Pre-run credit confirmation popup with per-user preference | DONE |

### Phase 8: AI Business Assistant (Feb 2026)
| Feature | Status |
|---------|--------|
| Natural language business queries with shop data context | DONE |
| Context: customer/job/revenue/invoice/employee stats | DONE |
| Conversation chat interface with sessions | DONE |
| Voice Input - Whisper STT (AI Assistant page) | DONE |
| Voice Output - OpenAI TTS (AI Assistant page) | DONE |

### Phase 9: Floating AI Assistant (Mar 2026)
| Feature | Status |
|---------|--------|
| Persistent bottom-right chat widget on all pages | DONE |
| Quick action buttons (Create job, Schedule, Invoice, Lookup) | DONE |
| Action execution from chat (create jobs, lookup customers) | DONE |
| Confirmation dialogs for create/destructive actions | DONE |
| Voice Input - Whisper STT | DONE |
| Voice Output - OpenAI TTS ("Read aloud") | DONE |
| Session-based conversations with unique IDs | DONE |

### Phase 10: Webstores & Commerce (Feb 2026)
| Feature | Status |
|---------|--------|
| 3 Store Types: B2B, Fundraiser, Creator | DONE |
| Store management (name, type, status, branding) | DONE |
| Product catalog (5 categories, images, variants, AI descriptions) | DONE |
| Public storefront with cart + checkout | DONE |
| Stripe Connect integration for payments | DONE |
| Order management with auto-create job + customer | DONE |
| QR code generation for store URLs | DONE |
| Fundraiser features (goals, progress, profit %) | DONE |
| Creator features (commission, payout tracking) | DONE |
| Analytics dashboard (KPIs, sales trends, top products) | DONE |
| Payouts tab | DONE |

### Phase 11: Role-Based Access Control (Feb 2026)
| Feature | Status |
|---------|--------|
| 3 User Roles: Owner, Admin, Staff | DONE |
| 23+ permission types | DONE |
| Backend permission checks (require_permission decorator) | DONE |
| Frontend permission context (hasPermission helper) | DONE |
| Navigation filtering by permission | DONE |
| Protected pages with Access Denied component | DONE |
| Role badges (color-coded) | DONE |
| User management page (list, search, role change) | DONE |

### Phase 12: Multi-Tenancy (Feb 2026)
| Feature | Status |
|---------|--------|
| Tenant model with settings | DONE |
| Tenant ID on all models | DONE |
| Tenant-scoped queries on all API routes | DONE |
| Auto-tenant creation on first registration | DONE |
| Security audit: 28 tests, 100% pass rate, cross-tenant blocked | DONE |

### Phase 13: Artwork Approvals (Feb 2026)
| Feature | Status |
|---------|--------|
| Upload artwork with client-side watermarking | DONE |
| Approval workflow (Pending, Approved, Revision, Rejected) | DONE |
| Version tracking + customer feedback | DONE |
| Customer Portal integration | DONE |

### Phase 14: Document Library & Forms (Feb 2026)
| Feature | Status |
|---------|--------|
| File upload with drag-and-drop (12 categories) | DONE |
| Template system (reusable documents) | DONE |
| 3 send methods: Email PDF, Customer Portal, As Form | DONE |
| Questionnaires with multiple question types | DONE |
| Pre-built templates (Vehicle Wrap, Logo Brief, etc.) | DONE |
| Public shareable link for form completion | DONE |
| AI summary of questionnaire responses | DONE |

### Phase 15: Company-Based Pricing System (Mar 2026)
| Feature | Status |
|---------|--------|
| 8 category-based pricing calculators | DONE |
| Tenant-specific cost & markup settings | DONE |
| Material configurations (vinyl, print, substrates) | DONE |
| Complexity slider (1.0x - 2.0x multiplier) | DONE |
| Pricing templates (save/load) | DONE |
| Historical Invoice Import + AI Pricing Benchmark Analysis | DONE |
| AI Pricing Advisor integration | DONE |

### Phase 16: Profit & Margin Analytics (Mar 2026)
| Feature | Status |
|---------|--------|
| Profit dashboard by job, category, and customer | DONE |
| Cost snapshot data on jobs | DONE |

### Phase 17: Production Workflow & Timeline (Mar 2026)
| Feature | Status |
|---------|--------|
| Configurable production stages (Simple, Detailed, Custom) | DONE |
| Visual timeline with status flow + checkmarks | DONE |
| Time-in-status tracking | DONE |
| Category-to-template assignment | DONE |
| Unified timeline/history via Job Details | DONE |

### Phase 18: Employee Portal (Mar 2026)
| Feature | Status |
|---------|--------|
| PIN-based login | DONE |
| Dashboard (clock status, work summary, assigned jobs) | DONE |
| Job detail with stage start/pause/complete actions | DONE |
| Pay history (earnings, YTD, balance) | DONE |
| Task management | DONE |
| Profile (image upload, clock history) | DONE |
| Configurable permissions per tenant | DONE |

### Phase 19: Customer Portal (Mar 2026)
| Feature | Status |
|---------|--------|
| Email/password login + temporary invite PIN | DONE |
| Dashboard (active jobs, approvals, messages, docs, forms, invoices) | DONE |
| Orders + Quotes (list + detail views) | DONE |
| Invoices (list, PDF download, Pay Now via Stripe) | DONE |
| Documents (view shared docs, "New" badge) | DONE |
| Messages (conversations with file attachments) | DONE |
| Proofs (artwork approval/revision + version history) | DONE |
| Forms (receive and complete questionnaires) | DONE |
| Appointments (5 types, 6 statuses) | DONE |
| Profile (contact info, notification preferences) | DONE |

### Phase 20: Billing & AI Credits (Mar 2026)
| Feature | Status |
|---------|--------|
| Multi-Product Plans: SignGuy OS (3), Webstores (3), AI Studio (3) | DONE |
| Founders Edition ($99/mo, 150 credits, lifetime lock) | DONE |
| Stripe Checkout (subscription + one-time) | DONE |
| 14 Stripe Price IDs configured | DONE |
| Webhook handling (subscription lifecycle) | DONE |
| AI Credit System (150/mo for Founders) | DONE |
| Credit packs via Stripe ($10/100, $25/300, $60/1000) | DONE |
| Pre-run credit confirmation + cost preview | DONE |
| Usage ledger + admin summary | DONE |
| Low credits warning + purchase modal | DONE |

### Phase 21: Onboarding System (Mar 2026)
| Feature | Status |
|---------|--------|
| 3 Tiers: Quick Start, Standard Setup, Full Optimization | DONE |
| Checklist + guided walkthrough | DONE |
| Resume/Finish Later with session persistence | DONE |
| Step-level analytics | DONE |
| Dashboard onboarding card with progress | DONE |

### Phase 22: Navigation & UI Structure (Feb-Mar 2026)
| Feature | Status |
|---------|--------|
| Office-Style Ribbon Navigation (3 rows) | DONE |
| 11 primary tabs with contextual sub-navigation | DONE |
| Mobile hamburger menu with overlay | DONE |
| Customizable Quick Toolbar (18 shortcuts, up to 10 active) | DONE |
| Floating AI Assistant widget | DONE |

### Phase 23: Community & Documentation (Feb 2026)
| Feature | Status |
|---------|--------|
| Community Hub (bug reports, feature requests, Q&A, upvotes) | DONE |
| Documentation site (15+ pages with mobile sidebar) | DONE |
| Contact Support email link | DONE |

### Phase 24: Marketing Website (Feb 2026)
| Feature | Status |
|---------|--------|
| Landing Page (hero, features, AI showcase, pricing, FAQ) | DONE |
| Features page | DONE |
| About, Contact pages | DONE |
| Founders Edition Pricing page | DONE |
| Multi-Product Pricing (tabbed, 3 product lines) | DONE |
| 9 Plan Detail Pages | DONE |
| 3 Product Line Overview Pages (OS, Webstores, AI Studio) | DONE |
| Why Founder page | DONE |

### Phase 25: Data Management (Feb 2026)
| Feature | Status |
|---------|--------|
| Tenant data export as JSON | DONE |
| Restore with preview summary + confirmation | DONE |
| Weekly backup reminder banner | DONE |

### Phase 26: Email & Notifications (Feb 2026)
| Feature | Status |
|---------|--------|
| SendGrid integration for transactional email | DONE |
| Email templates (6 types with variable placeholders) | DONE |
| AI Email Composer (contextual drafting) | DONE |
| Customer portal notifications | DONE |

### Phase 27: Promo Codes (Feb 2026)
| Feature | Status |
|---------|--------|
| Code creation (%, $, free trial discounts) | DONE |
| Usage limits, expiration dates, tracking | DONE |
| Founder-only access | DONE |

---

## SaaS Readiness Scorecard

### Category Breakdown

#### 1. Core Product Features (100% Complete)
| Item | Status | Weight |
|------|--------|--------|
| CRM / Customer Management | DONE | 5% |
| Jobs / Quotes / Pipeline | DONE | 5% |
| Invoicing / Payments | DONE | 5% |
| Time Clock / Payroll | DONE | 5% |
| AI Tools (28+ tools) | DONE | 5% |
| Webstores / E-Commerce | DONE | 5% |
| Document Library / Forms | DONE | 3% |
| Pricing Calculator | DONE | 3% |
| **Subtotal** | **36/36** | **36%** |

#### 2. Multi-Tenancy & Security (90% Complete)
| Item | Status | Weight |
|------|--------|--------|
| Multi-tenant data isolation | DONE | 5% |
| JWT Authentication | DONE | 3% |
| Role-Based Access Control (3 roles, 23+ perms) | DONE | 3% |
| Security audit (28 tests, 100% pass) | DONE | 3% |
| Password recovery / reset | DONE | 1% |
| Rate limiting | NOT DONE | 2% |
| Input sanitization / XSS prevention | PARTIAL | 1% |
| **Subtotal** | **16/18** | **16%** |

#### 3. Billing & Monetization (95% Complete)
| Item | Status | Weight |
|------|--------|--------|
| Stripe subscriptions (9 plans, 3 product lines) | DONE | 4% |
| Stripe Connect (webstore payments) | DONE | 2% |
| Stripe webhooks (lifecycle events) | DONE | 2% |
| AI credit billing system | DONE | 2% |
| Credit pack purchases | DONE | 1% |
| Founders Edition pricing | DONE | 1% |
| Failed payment / dunning handling | NOT DONE | 1% |
| **Subtotal** | **12/13** | **12%** |

#### 4. User Portals (100% Complete)
| Item | Status | Weight |
|------|--------|--------|
| Customer Portal (10 pages, full feature set) | DONE | 5% |
| Employee Portal (6 pages, PIN auth) | DONE | 3% |
| Admin Portal / Communications Hub | DONE | 2% |
| **Subtotal** | **10/10** | **10%** |

#### 5. Onboarding & User Experience (85% Complete)
| Item | Status | Weight |
|------|--------|--------|
| Tiered onboarding (3 tiers, guided walkthrough) | DONE | 3% |
| In-app documentation (15+ pages) | DONE | 2% |
| Community Hub (support, feedback) | DONE | 2% |
| Marketing website (landing, features, pricing) | DONE | 2% |
| UI Overhaul (Dark Shell / Light Workspace) | NOT DONE | 2% |
| Mobile responsiveness optimization | PARTIAL | 1% |
| **Subtotal** | **10/12** | **10%** |

#### 6. Integrations (90% Complete)
| Item | Status | Weight |
|------|--------|--------|
| OpenAI GPT-5.2 (text generation) | DONE | 2% |
| OpenAI GPT Image 1 (image generation) | DONE | 1% |
| OpenAI Whisper (speech-to-text) | DONE | 1% |
| OpenAI TTS (text-to-speech) | DONE | 1% |
| Stripe (subscriptions + Connect) | DONE | 2% |
| SendGrid (transactional email) | DONE | 1% |
| PDF Generation (reportlab) | DONE | 1% |
| QuickBooks / Accounting integration | NOT DONE | 1% |
| **Subtotal** | **9/10** | **9%** |

#### 7. Operations & Compliance (50% Complete)
| Item | Status | Weight |
|------|--------|--------|
| Data backup & restore | DONE | 2% |
| Email templates (6 types) | DONE | 1% |
| Terms of Service / Privacy Policy pages | NOT DONE | 1% |
| Cookie consent banner | NOT DONE | 1% |
| GDPR compliance tools (data export/deletion) | NOT DONE | 1% |
| Uptime / status page | NOT DONE | 1% |
| Error boundary / graceful error handling | NOT DONE | 1% |
| **Subtotal** | **3/7** | **3%** |

---

### OVERALL SAAS READINESS

```
Core Product Features:     ████████████████████ 36/36  (100%)
Multi-Tenancy & Security:  ████████████████░░░░ 16/18  ( 90%)
Billing & Monetization:    ███████████████████░ 12/13  ( 95%)
User Portals:              ████████████████████ 10/10  (100%)
Onboarding & UX:           █████████████████░░░ 10/12  ( 85%)
Integrations:              ██████████████████░░  9/10  ( 90%)
Operations & Compliance:   ██████░░░░░░░░░░░░░░  3/7   ( 50%)

TOTAL:                     ████████████████░░░░ 96/106 
```

### SAAS READINESS: 90.5%

**Breakdown:**
- **96 of 106 weighted items complete**
- **10 remaining items** needed for full production SaaS:
  1. Rate limiting (P1)
  2. Failed payment / dunning handling (P2)
  3. UI Overhaul - Dark Shell / Light Workspace (P1)
  4. Mobile responsiveness optimization (P2)
  5. QuickBooks / accounting integration (P3)
  6. Terms of Service / Privacy Policy pages (P1)
  7. Cookie consent banner (P2)
  8. GDPR compliance tools (P2)
  9. Uptime / status page (P3)
  10. Error boundary / graceful error handling (P2)

---

## Current Status

### What's Working
| Area | Status | Endpoints |
|------|--------|-----------|
| Authentication & RBAC | WORKING | 12+ |
| Customer CRM | WORKING | 15+ |
| Jobs & Quotes | WORKING | 25+ |
| Invoicing | WORKING | 15+ |
| Time Clock & Payroll | WORKING | 20+ |
| AI Tools (28+ tools) | WORKING | 30+ |
| AI Assistants (page + floating, with voice) | WORKING | 10+ |
| Webstores | WORKING | 25+ |
| Customer Portal | WORKING | 30+ |
| Employee Portal | WORKING | 15+ |
| Pricing System | WORKING | 15+ |
| Production Workflow | WORKING | 10+ |
| Billing & Credits | WORKING | 20+ |
| Community & Docs | WORKING | 10+ |
| Backup & Restore | WORKING | 5+ |
| Marketing Website | WORKING | N/A |
| Onboarding | WORKING | 8+ |

### Known Issues
| Issue | Priority | Status |
|-------|----------|--------|
| Production login CORS 400 preflight | P0 | BLOCKED - Platform issue, not app code |
| Legacy `/financials` routes gap | P2 | Low priority |

---

## Active Tasks

| Task | Priority | Status |
|------|----------|--------|
| "Dark Shell / Light Workspace" UI Overhaul | P1 | NOT STARTED |
| Add "New Job" button in customer info popup | P1 | NOT STARTED |
| Finalize ribbon navigation cleanup | P1 | NOT STARTED |

---

## Upcoming Features (P1-P2)

| Feature | Priority | Blocked? |
|---------|----------|----------|
| UI Overhaul (Dark Shell / Light Workspace) | P1 | No |
| "New Job" button in customer popup | P1 | No |
| Terms of Service / Privacy Policy pages | P1 | No |
| Rate limiting on API endpoints | P1 | No |
| Founders Edition Stripe Price IDs | P2 | Yes - awaiting user |
| Failed payment / dunning handling | P2 | No |
| Cookie consent banner | P2 | No |
| Error boundary implementation | P2 | No |
| GDPR data export/deletion tools | P2 | No |
| Mobile responsiveness pass | P2 | No |

---

## Future / Backlog (P3)

| Feature | Description |
|---------|-------------|
| Full Optimization onboarding tier | Workflow automation rules, advanced analytics |
| Learning Calculator | Calculator that improves pricing over time |
| Archive Legacy Pricing | Remove old pricing pages/routes |
| Vehicle Wrap AI Tool (Full Spec) | Complete wrap design & estimation |
| Master Product List | Centralized catalog across tenants |
| Custom Domain Support | Custom URLs for webstores |
| SMS Notifications (Twilio) | Text alerts for customers |
| QuickBooks Integration | Sync invoices, payments |
| BNPL (Affirm/Klarna) | Buy now pay later |
| Zapier Integration | Connect to 1000+ apps |
| Scheduled Reports | Auto-generated email reports |
| Advanced Analytics | Trend analysis, forecasting |
| Uptime / Status Page | Public service status |
| SEO Optimization | Meta tags, Open Graph, sitemap |
| Analytics / Telemetry | Usage tracking, funnel analysis |
| i18n / Localization | Multi-language support |

---

## Technical Architecture

### Stack Summary
```
Frontend (50,414 LOC):
  React 18, React Router v6, Tailwind CSS, Shadcn UI
  Axios, Context API, Lucide React icons
  Fonts: Barlow Condensed + Manrope
  87 pages, 81 components, 98 routes

Backend (29,169 LOC):
  FastAPI, Motor (Async MongoDB), Pydantic, PyJWT
  emergentintegrations (AI), reportlab (PDF)
  pdfplumber, openpyxl, xlrd (doc parsing)
  33 route files, 289 endpoints, 11 services, 12 models

Database:
  MongoDB - 58 collections
  Full multi-tenant isolation (verified)

Integrations:
  OpenAI GPT-5.2 (text) via Emergent LLM Key
  OpenAI GPT Image 1 (images) via Emergent LLM Key
  OpenAI Whisper STT via user OPENAI_API_KEY
  OpenAI TTS via user OPENAI_API_KEY
  Stripe (subscriptions, Connect, webhooks)
  SendGrid (transactional email)
```

### Key Directories
```
/app/
  backend/
    routes/    (33 files) - API endpoint handlers
    models/    (12 files) - Pydantic data models
    services/  (11 files) - Business logic layer
    server.py  (1193 lines) - App setup, middleware, router mounting
  frontend/
    src/pages/       (87 files) - Page components
    src/components/  (81 files) - Reusable UI + ribbon nav
    src/context/     - AuthContext, state management
    src/hooks/       - Custom React hooks
    App.js           - Route definitions and layout
  memory/            - Project documentation
  docs/              - User-facing help docs
  FEATURE_CATALOG.md - Complete feature inventory
```

---

*This document is maintained as the master build tracker for SignGuy AI.*  
*Last session: March 18, 2026*
