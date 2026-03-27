# SignGuy AI - Complete Build Roadmap & Feature Tracker

> **Last Updated:** March 27, 2026
> **Version:** 6.0
> **Status:** Active Development — Order System Complete

---

## Project Overview

**SignGuy AI** is a multi-tenant SaaS operating system for sign shops, print shops, and custom graphics businesses.

**Business Model:** Founders Edition ($99/mo or $594/year)
**Tech Stack:** React 18 + FastAPI + MongoDB + OpenAI (GPT-5.2, Whisper, TTS, GPT Image 1)

---

## Platform Stats (v6.0)

| Metric | Count |
|--------|-------|
| Backend Routes | 40+ |
| Frontend Pages | 45+ |
| API Endpoints | 200+ |
| AI Tools | 41 (11 image, 30 text) |
| MongoDB Collections | 60+ |
| Database Indexes | 30 |

---

## SaaS Readiness: 95%

| Area | Status |
|------|--------|
| Multi-tenant auth | Done |
| Order management | Done |
| Job ticket system | Done |
| Production workflow | Done |
| Pricing calculator | Done |
| Live pricing | Done |
| Invoice/Quote generation | Done |
| Payment processing (Stripe) | Done |
| AI tools (28+ tools) | Done |
| Customer portal | Done |
| Webstores | Done |
| Employee management | Done |
| Time tracking | Done |
| Employee scheduling | Done |
| Payroll | Done |
| Financials (sales/expenses) | Done |
| Email (SendGrid) | Done |
| File uploads | Done |
| Promo codes | Done |
| Mobile navigation | Done |
| Dark shell / light content UI | Done |
| Legal pages (Terms/Privacy) | Done |
| Production setup page | Done |

---

## Core System Architecture

### 4-Layer Order System (NEW — replaces old Jobs module)
```
Layer 1: ORDER (master container)
  → Layer 2: JOB TICKETS (production detail per item)
    → Layer 3: QUOTES / INVOICES (financial documents)
    → Layer 4: PRODUCTION TASKS (department-level tracking)
```

### Key Features
- **Dynamic category forms**: Banner, Rigid Sign, Cut Vinyl, Digital Print, Vehicle Wrap, Apparel — each with 20-30 fields specific to that category
- **Quick Entry / Detailed Entry**: Fast manual intake OR full category-specific form with settings-driven calculator
- **Live pricing**: Real-time price estimates as you fill in the form
- **Production workflow**: Category-based templates auto-generate tasks (6 default templates, customizable)
- **Status roll-up**: Task progress → Ticket progress → Order progress
- **Pricing from Settings**: All materials, labor rates, markups come from centralized pricing settings — no hardcoded values

---

## Completed Features

### Phase 1: Foundation (Done)
- Multi-tenant auth (JWT + bcrypt)
- Customer CRUD
- Invoice system
- Quote system
- Stripe payments
- Employee management

### Phase 2: AI & Webstores (Done)
- 41 AI tools (text + image generation)
- AI Business Assistant (chat)
- Voice input/output (Whisper + TTS)
- Webstore builder
- Product management
- Customer portal

### Phase 3: Founders Edition (Done)
- Single-plan pricing ($99/mo)
- Promo code system (FOUNDERS, PAPPYBILL)
- AI credit system (150/month + purchasable packs)
- Founder grace period (14 days read-only after lapse)
- Platform owner account (never expires)

### Phase 4: Order System (Done — March 2026)
- 4-layer Order → Job Ticket → Quote/Invoice → Production Task
- 6 category dynamic field schemas (Banner, Rigid Signs, Cut Vinyl, Digital Print, Vehicle Wrap, Apparel)
- Subtypes per category (7-12 each)
- Live pricing panel connected to settings-driven calculator
- Quick Entry and Detailed Entry modes
- Production Board (by department, status)
- Workflow Template Manager (admin)
- File upload on orders (artwork, drawings, notes)
- Order actions: Generate Quote, Generate Invoice, Generate Work Order, Email, Status change
- Customer type-ahead search
- Materials & Pricing admin page
- Apparel quantity discounts (5-25% based on qty)
- Setup fee fix (added flat, not marked up)

### Phase 5: Polish & Fixes (Done — March 2026)
- Dark shell / light content theme across all pages
- Mobile navigation rebuilt (all pages, expandable sub-menus)
- Square footage calculation fix
- Employee schedule (weekly grid with shift editing)
- Financials endpoints (daily sales + expenses)
- Navigation restructured (Financials top-level, Reports = shortcuts)
- Database indexes (30 created)
- Legal pages (Terms of Service, Privacy Policy)
- Contact Support → donnell@signguy-ai.com
- Owner permissions fix (all permissions granted)

---

## Remaining / Backlog

### P1 — Should Do Soon
- Questionnaire send to portal/email
- Webstore duplicate logo/color cleanup
- Task list display bug
- Subtype-specific conditional field hiding
- Stripe Connect enrollment (platform level)

### P2 — Nice to Have
- Drag/drop on production board
- Calendar view for install jobs
- Error boundaries
- Cookie consent banner

### P3 — Future
- Vehicle Wrap AI Tool
- QuickBooks integration
- SMS notifications
- Custom domains for webstores
- Employee GPS time tracking
- Learning pricing calculator

---

## Technical Architecture

```
Frontend: React 18 + Tailwind + Shadcn/UI + Craco
Backend: FastAPI + Motor (async MongoDB)
Database: MongoDB (local dev) / MongoDB Atlas (production)
AI: OpenAI GPT-5.2 + GPT Image 1 + Whisper + TTS (via Emergent LLM Key)
Email: SendGrid
Payments: Stripe (direct + Connect)
Auth: JWT + bcrypt
Deployment: Emergent Platform (Kubernetes)
```
