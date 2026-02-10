# SignGuy AI - Complete Build Roadmap & Feature Tracker

> **Last Updated:** February 10, 2026  
> **Version:** 2.2  
> **Status:** Active Development

---

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Completed Features](#completed-features)
3. [Current Sprint](#current-sprint)
4. [Upcoming Features](#upcoming-features)
5. [SaaS Requirements](#saas-requirements)
6. [Technical Architecture](#technical-architecture)
7. [API Reference](#api-reference)
8. [Database Schema](#database-schema)

---

## 🎯 Project Overview

**SignGuy AI** is a comprehensive web-based operating system for sign shops, designed to replace spreadsheets, notebooks, and disconnected tools with a unified platform for:

- Customer Relationship Management
- Quotes & Estimates
- Job/Order Management
- Invoicing & Payments
- Employee Time Tracking & Payroll
- Productivity & Scheduling
- Financial Tracking
- AI-Powered Design Tools
- B2B/Fundraiser Webstores

**Target Market:** Sign shops, print shops, and custom graphics businesses  
**Business Model:** SaaS subscription with tiered pricing

---

## ✅ COMPLETED FEATURES

### Phase 1: Core Infrastructure ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| FastAPI Backend Setup | ✅ Done | Jan 2026 | Python, Motor async MongoDB |
| React Frontend Setup | ✅ Done | Jan 2026 | React 18, Tailwind CSS, Shadcn UI |
| MongoDB Database | ✅ Done | Jan 2026 | All collections configured |
| Basic CRUD Operations | ✅ Done | Jan 2026 | All modules |
| Hot Reload Development | ✅ Done | Jan 2026 | Frontend & Backend |

### Phase 2: Customer Management ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Customer List View | ✅ Done | Jan 2026 | Search, filter, pagination |
| Customer Create/Edit | ✅ Done | Jan 2026 | Full form with validation |
| Customer Status (Active/Lead/Inactive) | ✅ Done | Jan 2026 | Color-coded badges |
| Customer Contact Info | ✅ Done | Jan 2026 | Name, email, phone, address |
| Customer Notes | ✅ Done | Jan 2026 | Free-text notes field |

### Phase 3: Quotes & Estimates ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Quote List View | ✅ Done | Jan 2026 | Filter by status |
| Quote Create/Edit | ✅ Done | Jan 2026 | Line items, totals |
| Quote Line Items | ✅ Done | Jan 2026 | Description, qty, price |
| Quote Status Workflow | ✅ Done | Jan 2026 | Draft → Sent → Approved/Declined |
| Quote to Job Conversion | ✅ Done | Jan 2026 | One-click convert |
| Quote Preview/Print | ✅ Done | Jan 2026 | Professional PDF-style view |
| Quote Email (Mock) | ✅ Done | Jan 2026 | Opens email client |
| **Magic Link Sharing** | ✅ Done | Feb 2026 | Customer portal access |

### Phase 4: Jobs & Orders ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Job List View | ✅ Done | Jan 2026 | Filter, search |
| Job Create/Edit | ✅ Done | Jan 2026 | Full job details |
| Job Items (Line Items) | ✅ Done | Jan 2026 | Per-job items list |
| Job Status Workflow | ✅ Done | Jan 2026 | Quoted → Production → Complete → Delivered |
| Job Detail Page | ✅ Done | Jan 2026 | Dedicated job view |
| Job Due Dates | ✅ Done | Jan 2026 | Date picker, overdue alerts |
| Job Scheduling Dialog | ✅ Done | Feb 2026 | Auto-fill job name, time input |
| Job Cost Tracking | ✅ Done | Jan 2026 | Materials + labor |

### Phase 5: Invoicing ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Invoice List View | ✅ Done | Jan 2026 | Filter by status |
| Invoice Create/Edit | ✅ Done | Jan 2026 | From job or manual |
| Invoice from Job | ✅ Done | Jan 2026 | Auto-populate items |
| Invoice Status Workflow | ✅ Done | Jan 2026 | Draft → Sent → Paid/Overdue |
| Invoice Preview/Print | ✅ Done | Jan 2026 | Professional layout |
| Payment Recording | ✅ Done | Jan 2026 | Track partial payments |
| Overdue Invoice Alerts | ✅ Done | Jan 2026 | Dashboard warning |

### Phase 6: Time Clock & Payroll ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Employee Management | ✅ Done | Jan 2026 | Add/edit employees |
| Clock In/Out | ✅ Done | Jan 2026 | Real-time tracking |
| Time Entry History | ✅ Done | Jan 2026 | View all entries |
| Manual Time Entry | ✅ Done | Jan 2026 | Add missed punches |
| Break Tracking | ✅ Done | Jan 2026 | Paid/unpaid breaks |
| Payroll Period View | ✅ Done | Jan 2026 | Weekly summary |
| Hours Calculation | ✅ Done | Jan 2026 | Auto-calculate totals |
| Overtime Calculation | ✅ Done | Jan 2026 | >40 hrs/week |

### Phase 7: Productivity & Scheduling ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Task List View | ✅ Done | Jan 2026 | All tasks |
| Task Create/Edit | ✅ Done | Jan 2026 | Title, description, due date |
| Task Assignment | ✅ Done | Jan 2026 | Assign to employees |
| Task Status | ✅ Done | Jan 2026 | Todo → In Progress → Done |
| Task Priority | ✅ Done | Jan 2026 | Low/Medium/High |
| Calendar View | ✅ Done | Jan 2026 | Monthly calendar |
| Job-Linked Tasks | ✅ Done | Jan 2026 | Link tasks to jobs |

### Phase 8: Financial Tracking ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Transaction List | ✅ Done | Jan 2026 | All transactions |
| Income Recording | ✅ Done | Jan 2026 | Payment received |
| Expense Recording | ✅ Done | Jan 2026 | Costs, purchases |
| Transaction Categories | ✅ Done | Jan 2026 | Customizable |
| Payment Methods | ✅ Done | Jan 2026 | Cash, Check, Credit, etc. |
| Daily/Weekly/Monthly Views | ✅ Done | Jan 2026 | Filter by period |
| Revenue Summary | ✅ Done | Jan 2026 | Totals by period |

### Phase 9: AI Tools Suite ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| **Design Tools (6)** | | | |
| Photo Enhancer Analyzer | ✅ Done | Feb 2026 | Vision analysis, print recommendations |
| Vectorization Analyzer | ✅ Done | Feb 2026 | Vision analysis, guidance |
| Font Identifier | ✅ Done | Feb 2026 | Vision-based font matching |
| AI Sign Designer | ✅ Done | Feb 2026 | Image generation |
| AI Banner Designer | ✅ Done | Feb 2026 | Image generation |
| Mockup Creator | ✅ Done | Feb 2026 | Image generation |
| **Branding Tools (2)** | | | |
| Logo Creator | ✅ Done | Feb 2026 | Image generation |
| Branding Kit Generator | ✅ Done | Feb 2026 | Text analysis |
| **Business Tools (3)** | | | |
| Business Copywriter | ✅ Done | Feb 2026 | Marketing copy |
| Document Composer | ✅ Done | Feb 2026 | Proposals, contracts |
| Pricing Intelligence | ✅ Done | Feb 2026 | Pricing analysis |
| **Marketing Tools (4)** | | | |
| Social Job Post Creator | ✅ Done | Feb 2026 | Social media content |
| Social Media Pack Generator | ✅ Done | Feb 2026 | Multi-platform |
| Content Calendar Creator | ✅ Done | Feb 2026 | Monthly planning |
| Campaign Builder | ✅ Done | Feb 2026 | Full campaigns |

### Phase 10: Webstores ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Webstore Management | ✅ Done | Feb 2026 | Create/edit stores |
| Store Types | ✅ Done | Feb 2026 | B2B, Fundraiser, Creator |
| Product Catalog | ✅ Done | Feb 2026 | Master product list |
| Product Assignment | ✅ Done | Feb 2026 | Assign to stores |
| **Public Storefront** | ✅ Done | Feb 2026 | Customer-facing shop |
| Custom Branding | ✅ Done | Feb 2026 | Logo, accent color |
| Shopping Cart | ✅ Done | Feb 2026 | Add/remove items |
| Checkout Flow | ✅ Done | Feb 2026 | Customer info, submit |
| Order Management | ✅ Done | Feb 2026 | View/process orders |
| Fundraiser Goals | ✅ Done | Feb 2026 | Track raised amount |

### Phase 11: User Authentication ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| User Registration | ✅ Done | Feb 2026 | Email, password, name |
| User Login | ✅ Done | Feb 2026 | JWT tokens |
| Remember Me | ✅ Done | Feb 2026 | 30-day token |
| Protected Routes | ✅ Done | Feb 2026 | Redirect to login |
| User Profile Display | ✅ Done | Feb 2026 | Sidebar user info |
| Logout | ✅ Done | Feb 2026 | Clear token |
| Admin Password Reset | ✅ Done | Feb 2026 | Admin can reset |
| User Management Page | ✅ Done | Feb 2026 | List, search users |
| Enable/Disable Users | ✅ Done | Feb 2026 | Toggle active status |

### Phase 12: Customer Portal (Magic Links) ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Magic Link Generation | ✅ Done | Feb 2026 | Secure tokens |
| Quote Portal View | ✅ Done | Feb 2026 | Customer sees quote |
| Job Portal View | ✅ Done | Feb 2026 | Customer sees job |
| Invoice Portal View | ✅ Done | Feb 2026 | Customer sees invoice |
| Link Expiration | ✅ Done | Feb 2026 | 7-day default |
| Share Link UI | ✅ Done | Feb 2026 | Button in quote preview |

### Phase 13: UI/UX Design ✓
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| **Unified Blended Theme** | ✅ Done | Feb 2026 | Dark shell + light panels |
| Brand Colors | ✅ Done | Feb 2026 | #2F8BFB primary blue |
| **Hover-Expanding Nav** | ✅ Done | Feb 2026 | Compact → expanded |
| Flyout Submenus | ✅ Done | Feb 2026 | Category → items |
| Responsive Design | ✅ Done | Feb 2026 | Mobile menu |
| Theme Mode Removal | ✅ Done | Feb 2026 | Single unified theme |
| Consistent Typography | ✅ Done | Feb 2026 | Barlow Condensed + Manrope |

### Phase 14: Role-Based Access Control ✅ COMPLETE
| Feature | Status | Date | Notes |
|---------|--------|------|-------|
| Permission Enum (39 permissions) | ✅ Done | Feb 2026 | Granular permissions |
| Three User Roles | ✅ Done | Feb 2026 | Owner, Admin, Staff |
| ROLE_PERMISSIONS Matrix | ✅ Done | Feb 2026 | Role → permissions mapping |
| Backend Permission Checks | ✅ Done | Feb 2026 | require_permission decorator |
| Admin Endpoints Protection | ✅ Done | Feb 2026 | 403 for unauthorized |
| Frontend Permission Context | ✅ Done | Feb 2026 | hasPermission helper |
| Navigation Filtering | ✅ Done | Feb 2026 | Hide nav by permission |
| Protected Pages | ✅ Done | Feb 2026 | Access Denied component |
| Role Badges | ✅ Done | Feb 2026 | Color-coded (amber/blue/gray) |
| User Role Management | ✅ Done | Feb 2026 | Owner can change roles |
| First User = Owner | ✅ Done | Feb 2026 | Auto-assign on first registration |

**Permission Distribution:**
| Role | Total Permissions | Key Access |
|------|------------------|------------|
| Owner | 39 | Full access + manage roles |
| Admin | 30 | Operational access, view-only financials/payroll |
| Staff | 7 | View customers/quotes/jobs, own timeclock, AI tools |

---

## 🔄 CURRENT SPRINT

### Sprint 7: SaaS Foundation - Multi-Tenancy (In Progress)
**Goal:** Isolate data between companies for SaaS deployment

| Task | Priority | Status | Assignee |
|------|----------|--------|----------|
| Tenant Model (Company entity) | P0 | 🔲 Todo | - |
| Tenant ID on All Records | P0 | 🔲 Todo | - |
| Tenant-Scoped Queries | P0 | 🔲 Todo | - |
| Tenant Settings Page | P1 | 🔲 Todo | - |
| Tenant Onboarding Flow | P1 | 🔲 Todo | - |

---

## 📅 UPCOMING FEATURES

### Sprint 8: Smart Pricing Engine
**Timeline:** After Multi-Tenancy
**Goal:** Real-time profit margin calculators

| Feature | Description | Priority |
|---------|-------------|----------|
| Materials Cost Tracking | Track material costs per job | P0 |
| Labor Cost Calculation | Track labor hours × rate | P0 |
| Real-Time Profit Display | Show margin on quotes/jobs | P0 |
| Price Suggestions | AI-powered pricing recommendations | P1 |

### Sprint 9: Artwork Approval System
**Timeline:** After Smart Pricing
**Goal:** Isolate data between companies

| Feature | Description | Priority |
|---------|-------------|----------|
| Design Upload | Upload proofs/mockups | P0 |
| Approval Workflow | Request → Review → Approve/Reject | P0 |
| Customer Comments | Feedback on designs | P1 |
| Revision Tracking | Version history | P1 |
| Email Notifications | Alert customer on new proofs | P2 |

### Sprint 10: Subscription & Billing
**Timeline:** After Artwork Approval
**Goal:** Monetize with Stripe subscriptions

| Feature | Description | Priority |
|---------|-------------|----------|
| Stripe Integration | Payment processing | P0 |
| Subscription Plans | Free, Pro, Enterprise | P0 |
| Plan Feature Gating | Restrict by subscription | P0 |
| Billing Portal | Manage subscription | P1 |
| Usage Tracking | Track AI credits, storage | P1 |
| Invoices | Subscription invoices | P1 |

**Proposed Pricing Tiers:**
| Plan | Price/mo | Users | AI Credits | Webstores | Features |
|------|----------|-------|------------|-----------|----------|
| **Free** | $0 | 1 | 10/mo | 1 | Basic modules |
| **Pro** | $49 | 5 | 100/mo | 5 | All modules |
| **Business** | $99 | 15 | 500/mo | Unlimited | Priority support |
| **Enterprise** | Custom | Unlimited | Unlimited | Unlimited | White-label, API |

### Sprint 11: Customer Portal (Full)
**Timeline:** After Billing
**Goal:** Allow customers to create accounts

| Feature | Description | Priority |
|---------|-------------|----------|
| Customer Registration | Sign up under a company | P1 |
| Customer Login | Separate from admin | P1 |
| Customer Dashboard | View their quotes, jobs, invoices | P1 |
| Artwork Approval | Approve/reject designs | P1 |
| Order History | Past orders from webstores | P2 |
| Profile Management | Update contact info | P2 |

---

## 🐛 KNOWN ISSUES

### P1 - High Priority
| Issue | Description | Status |
|-------|-------------|--------|
| Customer Portal Empty Descriptions | Quote line item descriptions not showing in portal | 🔲 Todo |

### P2 - Medium Priority
| Issue | Description | Status |
|-------|-------------|--------|
| Accessibility Warnings | Minor ARIA/contrast issues from old test reports | 🔲 Todo |

---

| Feature | Description | Priority |
|---------|-------------|----------|
| Proof Upload | Upload design files to job | P0 |
| Approval Request | Send to customer via magic link | P0 |
| Approval UI | Customer approve/reject/comment | P0 |
| Approval History | Track all approvals | P1 |
| Revision Tracking | Version history | P1 |
| Email Notifications | Notify on upload/approval | P2 |

### Sprint 11: Enhanced Reporting
**Timeline:** After Artwork Approval
**Goal:** Business intelligence and analytics

| Feature | Description | Priority |
|---------|-------------|----------|
| Sales Dashboard | Revenue, quotes, conversion | P1 |
| Customer Reports | Top customers, retention | P1 |
| Job Reports | Turnaround time, profitability | P1 |
| Employee Reports | Hours, productivity | P1 |
| Financial Reports | P&L, cash flow | P1 |
| PDF Export | Download reports | P1 |
| CSV Export | Data export | P1 |
| Scheduled Reports | Email weekly/monthly | P2 |

### Sprint 12: Smart Pricing Engine
**Timeline:** After Reporting
**Goal:** Category-specific pricing calculators

| Feature | Description | Priority |
|---------|-------------|----------|
| Apparel Calculator | Qty breaks, colors, locations | P1 |
| Banner Calculator | Size, material, finishing | P1 |
| Sign Calculator | Type, materials, installation | P1 |
| Vehicle Wrap Calculator | Coverage, complexity | P1 |
| Profit Margin Display | Real-time profit calc | P1 |
| Pricing Templates | Save common configurations | P2 |
| Price Book | Master price list | P2 |

### Sprint 13: Email Integration
**Timeline:** After Pricing
**Goal:** Real email sending/receiving

| Feature | Description | Priority |
|---------|-------------|----------|
| SendGrid/Resend Integration | Transactional email | P0 |
| Quote Email | Send quote to customer | P0 |
| Invoice Email | Send invoice to customer | P0 |
| Reminder Emails | Overdue invoice reminders | P1 |
| Approval Request Email | Send proof for approval | P1 |
| Welcome Email | New customer/user | P2 |
| Custom Email Templates | Branded emails | P2 |

### Sprint 14: Mobile Optimization
**Timeline:** After Email
**Goal:** Field-friendly mobile experience

| Feature | Description | Priority |
|---------|-------------|----------|
| Responsive Time Clock | Easy mobile clock in/out | P1 |
| Mobile Job Updates | Update status from field | P1 |
| Photo Capture | Add job photos from phone | P1 |
| GPS Check-in | Location with time entries | P2 |
| Offline Mode | Work without internet | P3 |
| Push Notifications | Mobile alerts | P3 |

### Sprint 15: Integrations
**Timeline:** After Mobile
**Goal:** Connect with other business tools

| Feature | Description | Priority |
|---------|-------------|----------|
| QuickBooks Online | Sync invoices, payments | P1 |
| Google Calendar | Sync tasks, due dates | P2 |
| Zapier | Connect to 1000+ apps | P2 |
| API Access | Public REST API | P2 |
| Webhooks | Event notifications | P2 |
| Stripe Connect | Customer payments | P1 |

---

## 🏢 SAAS REQUIREMENTS CHECKLIST

### Infrastructure
- [ ] Multi-tenant database architecture
- [ ] Tenant isolation middleware
- [ ] Subdomain routing (optional)
- [ ] SSL certificates
- [ ] CDN for assets
- [ ] Backup system
- [ ] Monitoring & alerting

### Security
- [x] JWT authentication
- [ ] Role-based access control
- [ ] Rate limiting
- [ ] Input validation/sanitization
- [ ] SQL injection prevention (MongoDB)
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Data encryption at rest
- [ ] Audit logging

### Billing
- [ ] Stripe subscription integration
- [ ] Plan management
- [ ] Usage metering
- [ ] Upgrade/downgrade flow
- [ ] Failed payment handling
- [ ] Cancellation flow
- [ ] Refund handling

### Compliance
- [ ] Terms of Service
- [ ] Privacy Policy
- [ ] GDPR compliance (if EU)
- [ ] Data export (user request)
- [ ] Data deletion (user request)
- [ ] Cookie consent

### Operations
- [ ] User onboarding flow
- [ ] In-app help/documentation
- [ ] Support ticket system
- [ ] Changelog/release notes
- [ ] Uptime status page
- [ ] Email support

---

## 🏗️ TECHNICAL ARCHITECTURE

### Current Stack
```
Frontend:
├── React 18
├── React Router v6
├── Tailwind CSS
├── Shadcn UI Components
├── Axios (API calls)
└── Context API (State)

Backend:
├── FastAPI (Python)
├── Motor (Async MongoDB)
├── Pydantic (Validation)
├── PyJWT (Authentication)
├── Passlib (Password hashing)
└── emergentintegrations (AI)

Database:
├── MongoDB
├── Collections: customers, quotes, jobs, invoices,
│   employees, time_entries, tasks, transactions,
│   webstores, products, orders, users, magic_links
└── Indexes: id, tenant_id (future)

AI Services:
├── OpenAI GPT-5.2 (Text generation)
├── Gemini 2.5 Flash (Vision analysis)
└── OpenAI gpt-image-1 (Image generation)
```

### Target SaaS Architecture
```
┌─────────────────────────────────────────────────────┐
│                    Load Balancer                      │
└─────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Frontend │    │ Frontend │    │ Frontend │
    │ (CDN)    │    │ (CDN)    │    │ (CDN)    │
    └──────────┘    └──────────┘    └──────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    ┌──────────┐
                    │   API    │
                    │ Gateway  │
                    └──────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Backend  │    │ Backend  │    │ Backend  │
    │ Instance │    │ Instance │    │ Instance │
    └──────────┘    └──────────┘    └──────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
          ┌────────────────────────────────┐
          │         MongoDB Atlas          │
          │    (Sharded, Multi-Region)     │
          └────────────────────────────────┘
```

---

## 📡 API REFERENCE

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | Create new user account |
| `/api/auth/login` | POST | Login, returns JWT |
| `/api/users/me` | GET | Get current user profile |
| `/api/users/me` | PUT | Update user profile |
| `/api/admin/users` | GET | List all users (admin) |
| `/api/admin/users/{id}/reset-password` | POST | Reset user password |
| `/api/admin/users/{id}/status` | PUT | Enable/disable user |

### Magic Links
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/magic-links` | POST | Create magic link |
| `/api/magic-links` | GET | List magic links |
| `/api/magic-links/{id}` | DELETE | Revoke magic link |
| `/api/portal/{token}` | GET | Access via magic link (public) |

### Core Modules
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/customers` | GET/POST | List/create customers |
| `/api/customers/{id}` | GET/PUT/DELETE | Single customer |
| `/api/quotes` | GET/POST | List/create quotes |
| `/api/quotes/{id}` | GET/PUT/DELETE | Single quote |
| `/api/quotes/{id}/convert-to-job` | POST | Convert to job |
| `/api/jobs` | GET/POST | List/create jobs |
| `/api/jobs/{id}` | GET/PUT/DELETE | Single job |
| `/api/invoices` | GET/POST | List/create invoices |
| `/api/invoices/{id}` | GET/PUT/DELETE | Single invoice |

### AI Tools
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/generate` | POST | Text/analysis generation |
| `/api/ai/generate-images` | POST | Image generation |

---

## 📊 DATABASE SCHEMA

### Users Collection
```javascript
{
  id: "uuid",
  email: "user@example.com",
  hashed_password: "...",
  full_name: "John Smith",
  company_name: "Smith Signs",
  is_active: true,
  // Future: tenant_id, role
  created_at: "ISO8601",
  updated_at: "ISO8601"
}
```

### Customers Collection
```javascript
{
  id: "uuid",
  // Future: tenant_id
  name: "Customer Name",
  company: "Company Inc",
  email: "customer@email.com",
  phone: "555-1234",
  address: "123 Main St",
  status: "active|lead|inactive",
  notes: "...",
  created_at: "ISO8601"
}
```

### Magic Links Collection
```javascript
{
  id: "uuid",
  token: "secure_random_token",
  resource_type: "quote|job|invoice",
  resource_id: "uuid",
  customer_email: "optional@email.com",
  expires_at: "ISO8601",
  is_used: false,
  created_at: "ISO8601"
}
```

---

## 📝 DEVELOPMENT NOTES

### Code Conventions
- Use UUID for all IDs (`str(uuid.uuid4())`)
- Exclude `_id` from MongoDB responses
- Use ISO8601 for all dates
- Pydantic models for validation
- React Context for state management
- Lucide React for icons

### Testing
- Backend tests: `/app/backend/tests/`
- Test reports: `/app/test_reports/`
- Run: `pytest -v`

### Environment Variables
```env
# Backend (.env)
MONGO_URL="mongodb://localhost:27017"
DB_NAME="signguy_ai"
EMERGENT_LLM_KEY="sk-emergent-..."
JWT_SECRET_KEY="..."

# Frontend (.env)
REACT_APP_BACKEND_URL="https://..."
```

---

## 📈 PROGRESS TRACKER

### Overall Completion
```
Phase 1-13 (Core App):     ████████████████████ 100%
Phase 14 (RBAC):           ░░░░░░░░░░░░░░░░░░░░   0%
Phase 15 (Multi-Tenant):   ░░░░░░░░░░░░░░░░░░░░   0%
Phase 16 (Billing):        ░░░░░░░░░░░░░░░░░░░░   0%
Phase 17 (Customer Portal):░░░░░░░░░░░░░░░░░░░░   0%
Phase 18+ (Enhancements):  ░░░░░░░░░░░░░░░░░░░░   0%

Total SaaS Ready:          ████████░░░░░░░░░░░░  40%
```

### Feature Count
- **Completed Features:** 85+
- **Remaining for MVP SaaS:** ~25
- **Nice-to-Have Features:** ~40

---

## 🚀 NEXT SESSION CHECKLIST

When you log in next, here's what to work on:

### Priority 1 (Must Do)
- [ ] Apply blended theme to remaining pages (Customers, Jobs, Quotes, etc.)
- [ ] Implement Role-Based Access Control (RBAC)
- [ ] Add User Roles: Owner, Admin, Staff

### Priority 2 (Should Do)
- [ ] Multi-tenant data isolation
- [ ] Company settings page
- [ ] Add magic link sharing to Jobs and Invoices

### Priority 3 (Nice to Have)
- [ ] Stripe subscription integration
- [ ] Full customer portal with accounts
- [ ] Artwork approval system

---

*This document is automatically updated as features are completed.*
*Last session: February 8, 2026*
