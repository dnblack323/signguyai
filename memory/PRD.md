# Sign Guy AI - Product Requirements Document

## Original Problem Statement
Build a web-based sign-shop operating system called "Sign Guy AI" - a single daily-use platform for sign and design shops replacing spreadsheets, notebooks, emails with a structured system for Customers, Quotes, Jobs, Invoices, Productivity, Financial tracking, Time clock & payroll, AI-assisted tools, and Fundraiser/B2B webstores.

## Architecture & Tech Stack
- **Frontend**: React 19 + Tailwind CSS + Shadcn/UI components
- **Backend**: FastAPI (Python) with async MongoDB motor driver
- **Database**: MongoDB
- **AI Integration**: OpenAI GPT-5.2 via Emergent LLM key
- **Theme**: Dark mode with electric teal (#00E0D0) accent

## User Personas
1. **Sign Shop Owners** - Need overview dashboards, financial tracking, business decisions
2. **Office/Admin Staff** - Manage customers, quotes, invoices, payroll
3. **Production/Install Staff** - Track jobs, time clock, task management

## Core Requirements (Static)
- Customer → Quote → Job → Invoice workflow (strict hierarchy)
- No orphaned records allowed
- Time clock sequence validation
- Payroll balance tracking (Earnings - Advances - Payments)
- AI outputs must be saved to database

## Data Model

### JobItem (Line Items for Jobs)
- **job_id**: Reference to parent Job
- **item_type**: banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other
- **description**: Text description of the item
- **quantity**: Number (default 1)
- **unit_price**: Number (default 0)
- **line_total**: Calculated (qty × unit_price)
- **status**: pending, in_production, done
- **notes**: Optional text/file references

### Workflow Rules
- Converting Quote → Job automatically creates JobItems from Quote line items
- Invoice created from Job pulls JobItems into Invoice line_items array
- Job subtotal auto-recalculates when items are added/edited/deleted
- Job description serves as "overall job notes" - actual work lives in JobItems

## What's Been Implemented (January 2026)

### Phase 1 MVP - COMPLETE
- [x] Dashboard with real-time stats
- [x] Customer Management (CRUD, search, filters, status)
- [x] Quotes Module (line items, totals, convert to job)
- [x] Jobs Module (List view, Kanban board, status changes)
- [x] **Job Line Items** (NEW) - Multiple line items per job with types, pricing, status
- [x] Invoice Management (create from job with line items, mark paid)
- [x] Time Clock (start/end work, breaks, sequence validation, shift summary)
- [x] Payroll (earnings/advances/payments, balance calculation, reports)
- [x] Productivity (tasks, calendar, job kanban)
- [x] Financial Tracking (sales, expenses, tax tracking, summaries)
- [x] AI Tools Suite (6 GPT-5.2 powered tools)
- [x] Webstores (Fundraiser campaigns, B2B custom stores)

### Recent Updates (February 2, 2026)
- [x] **Webstore System v2 - Phase 1 Complete**
  - New data models: Webstore, Product, ProductVariant, WebstoreProduct, WebstoreOrderV2
  - **Master Product Catalog** - Products with variants (size/color), base cost, retail price, profit calculation
  - **Webstore Manager** - Create/list/manage Business, Fundraiser, Creator stores
  - **Product Assignment** - Enable/disable products per store with price overrides
  - **Order System** - Orders link to webstore + sign shop, profit/payout calculation
  - Backend APIs for all CRUD operations, product assignment, orders, payouts

### Recent Updates (January 31, 2026)
- [x] **Dark/Light Mode Toggle** - Full theme switching capability
  - Toggle button in sidebar (bottom, above Collapse)
  - Persists selection to localStorage
  - Light theme based on BUBBLE_DESIGN_SYSTEM_LIGHT.md design specs
  - Sidebar adapts background color per theme
  - All components respect theme variables
- [x] **Invoice Preview Modal** - Click "View Invoice" from any location opens a popup modal with print-preview style invoice instead of navigating to invoice list
  - Available on: Invoices page, Job Details page, Dashboard overdue invoices
  - Features: Print button, line items table, balance due calculation, customer/job info display
- [x] **Daily Sales Entry Enhancement** - Renamed "Add Sale" to "Enter Daily Sales" with payment method tracking
  - Payment methods: Cash, Credit/Debit Card, Check, Other
  - Tracks actual money received at the business daily
  - Shows payment method icons in Sales table and Recent Activity
- [x] Dashboard Recent Activity - Clicking jobs navigates to job details
- [x] Bubble.io migration documentation (13 files) created for evaluation

### Testing Results (January 28, 2026)
- Backend: 95-98% tests passing
- Frontend: 100% functionality verified
- Integration: 100% workflows operational

## API Endpoints Reference
```
/api/customers - Customer CRUD
/api/quotes - Quote CRUD + /convert-to-job
/api/jobs - Job CRUD
/api/jobs/{job_id}/items - Job Items CRUD (POST, GET)
/api/job-items/{item_id} - Job Item Update/Delete (PUT, DELETE)
/api/invoices - Invoice CRUD + /from-job
/api/employees - Employee CRUD
/api/timeclock - Clock actions + /status + /summary
/api/payroll - Transactions + /balance + /report
/api/financials - Sales + Expenses + /summary
/api/tasks - Task CRUD
/api/ai/generate - AI tool generation
/api/webstores/* - Fundraiser and B2B stores
```

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [ ] User Authentication (JWT + optional Google OAuth)
- [ ] Role-based access control (Owner, Admin, Staff)
- [ ] Data export functionality (CSV/PDF)

### P1 - High Priority
- [ ] Artwork Approval System (upload proof, customer approve/reject)
- [ ] Email notifications for overdue invoices
- [ ] Print-ready file generation
- [ ] Mobile-responsive time clock interface

### P2 - Medium Priority
- [ ] Report generation and analytics
- [ ] Bulk operations (multi-select delete, status update)
- [ ] Search across all modules
- [ ] Customer portal for viewing quotes/invoices

### P3 - Low Priority / Future
- [ ] Light mode theme toggle
- [ ] Integrations (QuickBooks, Stripe payments)
- [ ] Advanced scheduling calendar
- [ ] Real-time collaboration features

## Next Tasks
1. Add user authentication
2. Implement artwork approval workflow
3. Add email notifications
4. Create customer-facing portal
