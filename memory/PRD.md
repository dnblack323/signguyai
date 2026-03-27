# SignGuy AI - Product Requirements Document

> **Last Updated:** March 27, 2026
> **Version:** 6.0

---

## Original Problem Statement
Build a comprehensive multi-tenant SaaS operating system for sign shops, print shops, and custom graphics businesses. Replace spreadsheets, notebooks, and disconnected tools with a unified platform.

## Core Requirements
- Full-stack React + FastAPI + MongoDB application
- Multi-tenant isolation with role-based access control
- AI-powered tools for design, business, and marketing
- Stripe billing integration
- Customer and Employee portals

---

## What's Been Implemented

### Session: March 27, 2026 (Bug Fixes & UI Improvements)
- **Task List Display Bug (FIXED):**
  - Updated AppContext.js to use local state updates instead of refetching
  - `createTask`, `updateTask`, `deleteTask` now immediately update local state
  - Tasks appear instantly in the UI after creation
- **Job Ticket Customer Data Bug (FIXED):**
  - Created new `AddTicketToOrder.js` page for adding tickets to existing orders
  - Updated App.js routing to use dedicated component instead of reusing NewOrderForm
  - Order summary card shows customer info while adding tickets
- **Orders List Icons (DONE):**
  - Added View icon (blue eye) for quick view
  - Added dropdown menu with View Details, Add Ticket, Delete Order options
  - Added bulk actions toolbar with checkboxes for multi-select
  - Bulk status change and bulk delete functionality
- **Users List Icons (DONE):**
  - Added View icon (blue eye) for quick user info
  - Consolidated Role/Reset/Enable actions into dropdown menu
- **Financials Page Color Fix (DONE):**
  - Fixed page header to use white text on dark background
  - Updated summary cards to use -600 color variants for better visibility on white
  - Fixed expense breakdown and recent activity text colors
  - Changed table cell text to text-gray-900 for readability
- **Documentation Theme Fixes (DONE):**
  - DocsEmployees.js - Fixed text colors for dark theme
  - DocsQuotesJobs.js - Fixed text colors for dark theme with cyan accents
  - Updated bg-gray-50 to bg-gray-800/50 for proper dark theme cards
- **Documentation Content Updates (DONE):**
  - Created new DocsDocumentLibrary.js page with full guide
  - Enhanced DocsProductivity.js with Task List, Calendar, and Kanban details
  - Enhanced DocsCustomerPortal.js with Portal Invite Flow, Proofs, Forms sections
  - Enhanced DocsWebstores.js with creating stores, products, checkout details
  - Enhanced DocsAITools.js with tool descriptions and credit system explanation
  - Added Document Library to DocsLayout sidebar navigation
  - Added Document Library to DocsOverview primary links

### Session: March 22-27, 2026 (Previous Sessions)
- **NEW 4-Layer Workflow System (DONE - Backend):**
  - Layer 1: Orders (master record with auto-numbering ORD-XXXX)
  - Layer 2: Job Tickets (production detail per item, category-based)
  - Layer 3: Quotes generated from job tickets (financial layer)
  - Layer 4: Production Tasks (auto-generated from category workflow templates)
  - 6 Default Workflow Templates: Rigid Signs (11), Banners (12), Cut Vinyl (8), Vehicle Wrap (14), Apparel (11), Promo/Misc (5)
  - Status roll-up: tasks→tickets→orders with partial completion logic
  - Activity logging for all status changes
  - Production board grouped by department/status
  - Admin workflow template CRUD
- **Testing:** 21/21 backend tests passed (iteration_72)
- **New Files:** models/orders.py, services/workflow_engine.py, routes/orders.py, routes/job_tickets.py, routes/production_tasks.py, routes/workflow_templates.py
- **New Collections:** orders, job_tickets, production_tasks, workflow_templates, order_quotes, order_activities

### Session: March 22, 2026 (Stage 2 + Fixes)
- **Stage 2 Legal & Color Scheme (DONE):**
  - Terms of Service page (`/terms`) — 13 sections covering agreement, billing, AI credits, GDPR
  - Privacy Policy page (`/privacy`) — 12 sections GDPR-compliant with third-party sharing disclosure
  - Footer links updated from `<a href="#">` to React Router `<Link>` components
  - Color scheme changed from amber/gold → violet/purple across 7 files (Landing, Pricing, Billing, Founders, WhyFounder, TrialLockout, PublicNav)
- **Testing:** 11/11 frontend tests passed (iteration_71)
- **Deployment Fix:** Cleaned requirements.txt from 137 → 24 packages, removed server_backup.py

### Session: March 20, 2026
- **Stage 1 Critical Fixes (ALL DONE):**
  - AI Rate Limiter Fix: All 9 AI endpoints in `ai.py` now use `request: Request, data: PydanticModel` pattern
  - Promo Code Backend: Added `POST /api/billing/apply-promo` endpoint with full validation
  - Promo Code `free_days` type: Backend and frontend support added
  - TrialLockout promo input: Users on lockout screen can now enter promo codes
  - AI Credit Audit: Verified all 28+ tools have credit costs assigned (1-3 credits)
  - AI Credit Confirmation Popup: Verified preflight, "don't show again", low balance warnings
  - Invoice Line Items: Verified fallback chain (job_items → line_items → subtotal → quote.total)
- **Testing:** 14/14 backend tests passed, 100% frontend verification (iteration_70)

### Session: March 18, 2026
- **Founders Edition Only Billing:** Simplified entire billing system from multi-tier (9 plans, 3 product lines) to Founders-only ($99/mo, $594/yr). All other tiers archived.
- **Founders Plan Config:** Created `/app/backend/config/founders_plan.py` as single source of truth
- **New Billing Endpoints:** `/api/billing/founders/*` (plan, checkout, purchase-credits, credits, fees, spots)
- **Processing Fees Fixed:** 2.2% + $0.20 platform, 2% webstore additional
- **Credit Rollover Logic:** Monthly (150) don't roll over, purchased DO roll over
- **Stripe Founders Price IDs:** Added STRIPE_PRICE_FOUNDERS_MONTHLY, ANNUAL, CREDITS_100/300/1000, COUPON
- **Route Redirects:** All old tier pages (/starter, /pro, /business, /platform, /ai-studio) redirect to /pricing-plans
- **Feature Gate Bypass:** Founders get all features enabled regardless of plan config
- **Voice I/O on Floating Assistant:** Added mic button + "Read aloud" to the persistent chat widget
- **Voice Transcription Bug Fix:** Fixed 500 error on /api/ai/voice/transcribe (file handling)
- **Password Recovery:** Added "Forgot Password?" flow for owner accounts
- **Login Error Handling:** Improved to show "Invalid email or password" instead of generic "Network error"
- **bcrypt Fix:** Replaced passlib with direct bcrypt + pinned bcrypt==4.0.1
- **Feature Catalog Updated:** Added voice features, floating assistant, password recovery

### Previous Sessions (Jan-Mar 2026)
- CRM, Orders/Job Tickets, Invoicing, Time Clock, Payroll
- 28+ AI Tools, AI Business Assistant
- Webstores (3 types), Stripe Connect
- Customer Portal, Employee Portal
- Multi-tenant isolation (28 security tests, 100% pass)
- Pricing Calculator (8 categories), Production Workflow
- AI Credit System, Tiered Onboarding
- Community Hub, Documentation Site
- Marketing Website, Promo Codes
- Office-Style Ribbon Navigation

---

## Active Plan: Founders Edition Only

| Field | Value |
|-------|-------|
| Plan Name | Founders Edition |
| Monthly Price | $99 |
| Annual Price | $594 |
| Founder Limit | 100 spots |
| AI Credits | 150/month (no rollover) |
| Purchased Credits | Roll over while active |
| Processing Fee | 2.2% + $0.20 |
| Webstore Fee | 2% additional |
| Promo Code | FOUNDERS (50% off) |
| Features | All included |

---

## Prioritized Backlog

### P0 - Critical
- ~~AI Tools rate limiter parameter fix~~ DONE
- ~~Promo code apply-promo endpoint~~ DONE
- ~~free_days promo type~~ DONE

### P1 - High Priority (from user notes)
- Update documentation pages to Founders-only model
- Update Feature Catalog (remove tier references)
- "New Job" button in customer info popup
- UI Overhaul ("Dark Shell / Light Workspace")

### P2 - Medium Priority (from user notes)
- Reinstate: Materials & Inventory system
- Reinstate: Bulk actions on Orders page
- Reinstate: Search on Orders/Invoices/Webstores pages
- Reinstate: Database indexes migration
- Reinstate: Code cleanup (console.log removal, print→logger)
- Reinstate: Navigation updates (ActionToolbar, Settings links)

### P3 - Future/Backlog
- Rate limiting (slowapi)
- Cookie consent banner
- Error boundary implementation
- GDPR data export/deletion tools
- Mobile responsiveness pass
- Learning Calculator
- Vehicle Wrap AI Tool (Full Spec)
- Master Product List
- Custom Domain Support for webstores
- SMS Notifications (Twilio)
- QuickBooks Integration

---

## Architecture

```
Tech Stack: React 18 + FastAPI + MongoDB + OpenAI + Stripe
Frontend: 87 pages, 81 components, 98 routes, 50,414 LOC
Backend: 33 route files, 289 endpoints, 29,169 LOC
Database: 58 MongoDB collections
Total: ~80,000 lines of code
```

---

## Credentials
- Admin: thesigntistslab@gmail.com / password123
- Test: test@test.com / password
