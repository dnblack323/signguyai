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

## What's Been Implemented (December 2025)

### Phase 1 MVP - COMPLETE
- [x] Dashboard with real-time stats
- [x] Customer Management (CRUD, search, filters, status)
- [x] Quotes Module (line items, totals, convert to job)
- [x] Jobs Module (List view, Kanban board, status changes)
- [x] Invoice Management (create from job, mark paid, status filters)
- [x] Time Clock (start/end work, breaks, sequence validation, shift summary)
- [x] Payroll (earnings/advances/payments, balance calculation, reports)
- [x] Productivity (tasks, calendar, job kanban)
- [x] Financial Tracking (sales, expenses, tax tracking, summaries)
- [x] AI Tools Suite (Layout Generator, Print Checklist, Brand Kit, Document Creator, Overdue Assistant, Design Intake)
- [x] Webstores (Fundraiser campaigns, B2B custom stores)

### Testing Results
- Backend: 98.3% tests passing (57/58)
- Frontend: 95% functionality verified
- All core workflows operational

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

## API Endpoints Reference
```
/api/customers - Customer CRUD
/api/quotes - Quote CRUD + /convert-to-job
/api/jobs - Job CRUD
/api/invoices - Invoice CRUD + /from-job
/api/employees - Employee CRUD
/api/timeclock - Clock actions + /status + /summary
/api/payroll - Transactions + /balance + /report
/api/financials - Sales + Expenses + /summary
/api/tasks - Task CRUD
/api/ai/generate - AI tool generation
/api/webstores/fundraiser - Fundraiser campaigns
/api/webstores/b2b - B2B stores
/api/webstores/orders - Webstore orders
```

## Next Tasks
1. Add user authentication
2. Implement artwork approval workflow
3. Add email notifications
4. Create customer-facing portal
