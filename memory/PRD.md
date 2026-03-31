# SignGuy AI - Product Requirements Document

> **Last Updated:** March 31, 2026
> **Version:** 6.1

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

### Session: March 31, 2026 (Signature & Drawing System)
- **Signature System (DONE):**
  - Added tenant-level `signature_settings` feature toggle in Company Settings
  - Signature UI now hides completely when disabled on tested surfaces
  - New structured `/api/signatures/*` flow with:
    - per-record signature requirements
    - email signature request links
    - public review + sign page (`/customer-sign/:token`)
    - internal signature capture modal
  - Signatures store context: parent record, order/job context, type, signer info, signed timestamp, version reference, and image
  - Order Detail now exposes signatures for:
    - Order authorization
    - Change approval
    - Pickup / delivery / install confirmation
    - Quote / invoice / work order cards
  - Added proof signature controls in Approvals preview and document signature controls in Document Library details
  - Parent order signature history view added
- **Drawing / Sketch / Markup System (DONE):**
  - Upgraded drawing pad with undo, pen size selector, color picker, and improved touch support
  - Added autosave draft behavior for persisted order/item/image drawings
  - Extended drawing storage to structured contexts:
    - order-level
    - job-ticket/item-level
    - uploaded-image markup
  - Order Detail Drawings tab now supports combined filtered views: All / Order / Item / Image
  - Job Ticket Detail now has item-level drawings tab with enable/reveal behavior and image markup actions
  - Added secure image content endpoint for markup-on-uploaded-image flow
- **Testing:**
  - Self-tested: signature capture, email request creation, public signing flow, order/item drawings, image markup API paths
  - Screenshot smoke test passed for signature UI on Order Detail
  - Testing agent iteration_78 passed (backend 22/22, frontend 100%; skipped cases only due missing seed data)

### Session: March 31, 2026 (Order Workflow Hardening & Verification)
- **Order Workflow Verification Pass (DONE):**
  - Verified full order flow: order creation → job tickets → quote/invoice/work order generation → production start
  - Added ticket-level workflow shortcuts from Order Detail + Job Ticket Detail:
    - Assign employee
    - Add to employee schedule
    - Create productivity task
- **Live Estimate + Saved Price Sync (DONE):**
  - New Order and Add Ticket forms now auto-sync live pricing into `estimated_price`
  - Banner, apparel, and vehicle-wrap tickets now save calculator-backed pricing snapshots during ticket creation
  - Quotes and invoices now use active pricing snapshot values when available
- **Category / Pricing Reliability Fixes (DONE):**
  - Dynamic category schema now pulls pricing config and material options from tenant pricing settings with fallback catalog merge
  - Vehicle Wrap category now correctly maps to `vehicle_wraps` settings defaults
  - Vehicle coverage values (`25/50/75/custom`) now normalize correctly for pricing engine
  - Added `pickup` vehicle support to pricing enums/calculator
  - Apparel size breakdown now drives ticket quantity automatically
- **Document Visibility Fix (DONE):**
  - Generated work orders now appear in the Order Detail Financial tab alongside quotes and invoices
- **Testing:**
  - Self-tested backend pricing + workflow APIs with live tenant auth
  - Screenshot smoke test passed on `/orders/new`
  - Testing agent iteration_77 passed: backend 23 passed / 1 skipped, frontend 100%

### Session: March 30, 2026 (Dashboard Team Status & Navigation)
- **Dashboard Team Status Widget (DONE):**
  - Replaced basic ClockedInWidget with enhanced TeamStatusWidget
  - New backend endpoint: GET /api/dashboard/team-status-today
  - Combines employee schedule data with real-time clock-in status
  - Shows "Scheduled Today" section with clock status badges (Clocked In / Not In / On Break / Finished)
  - Shows "Clocked In (Unscheduled)" section for walk-ins
  - Empty state with "Set Up Schedule" button linking to /payroll?tab=schedule
  - Count badges: "X in" and "X scheduled" in header
- **Employee Schedule Navigation Link (DONE):**
  - Added "Employee Schedule" to Team sub-nav in PrimaryNav.js
  - Added "Employee Schedule" to Team children in MobileNav.js
  - Links to /payroll?tab=schedule which pre-selects the Schedule tab
  - Payroll.js now reads ?tab query parameter to initialize active tab
- **Daily Notification Digest (DONE):**
  - Full backend: /api/digest/* endpoints (preview, send, settings, history)
  - Compiles: scheduled employees, jobs due today, overdue invoices, pending approvals, yesterday's revenue, unread messages
  - Rich HTML email template rendered server-side with inline CSS
  - SendGrid email delivery (configured in .env)
  - APScheduler background scheduler checks every minute for scheduled sends
  - Settings page at /settings/digest with enable toggle, time picker (UTC), and recipient management
  - "Send Digest" quick action button on Dashboard
  - "Daily Digest" link in Settings sub-nav (desktop + mobile)
  - Send history tracking in MongoDB digest_logs collection
- **Order Drawing Pad — Phase 1 (DONE):**
  - New `order_drawings` collection with full CRUD API: `/api/order-drawings/*`
  - Canvas-based drawing: mouse, touch, stylus support with high-DPI rendering
  - PNG upload to Emergent Object Storage (`signguy-ai/orders/{id}/drawings/...`)
  - Blank drawing prevention (< 1000 bytes rejected)
  - "Drawings & Signatures" tab in Order Detail page with thumbnail grid
  - Full-size preview modal with label, type badge, date, creator, notes
  - Admin-only delete (soft-delete)
  - `touch-none` CSS prevents page scroll while drawing on tablet/mobile
  - Drawing types: signature, sketch, markup
  - Object storage service: `/app/backend/services/object_storage.py`

### Session: March 31, 2026 (Bug Fixes & Drawing Phase 2)
- **Unit of Measure Bug Fix (DONE):**
  - Root cause: Schema defaults not applied to specs on category load
  - DynamicCategoryFields now auto-sets defaults from schema fields
  - Case-insensitive unit comparison in sqFootage and LivePricingPreview
  - Banner: Width=2, Height=8, Feet now correctly shows 16.00 sq ft
- **New Order Form Reorder (DONE):**
  - Customer section: search, name, company, phone, email only
  - Order Information: source, due date (moved here), event date, internal notes
  - Job Tickets section
  - Sketches & Notes: new section with "Add Sketch" drawing pad
  - Pickup / Delivery: moved to end with method + delivery notes
  - Attachments / Artwork: moved to end
  - Save as Draft + Save Order buttons
- **Order Drafts Feature (DONE):**
  - "Save as Draft" button creates order with status='draft'
  - Draft status added to OrderStatus enum and OrderCreate model
  - Drafts filter in Orders page status dropdown
  - Draft status badge styling (gray)
- **Material Price Zero Placeholder Fix (DONE):**
  - Changed initial cost_per_unit from 0 to '' (empty string)
  - Clean numeric input without leading zeros
- **Invoice History Preview Colors Fix (DONE):**
  - Changed dark slate backgrounds to white/gray-100
  - All text now dark (gray-900/gray-700) for readability
  - Preview table has alternating row colors
  - Suggestion cards and stat cards on white backgrounds
- **Logo Upload Update Fix (DONE):**
  - File input reset forces re-mount after upload
  - Can now upload and then update logo reliably
- **Category Schema Fetch Reliability (DONE):**
  - Added retry logic (up to 2 retries with 500ms delay) for schema endpoint
- **Drawing Pad on New Order Form (DONE):**
  - DrawingModal supports onLocalSave for pre-order sketches
  - Sketches stored in-memory until order is saved, then uploaded as order_drawings

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
- **Documentation Screenshots (DONE):**
  - Added screenshot to DocsCustomers.js with feature_customers.jpeg
  - Added screenshot to DocsAITools.js with feature_ai_tools.jpeg
  - Added screenshot to DocsWebstores.js with feature_webstores.jpeg
  - Added screenshot to DocsInvoicing.js with feature_invoices.jpeg
  - Added screenshot to DocsPricingCalculator.js with pricing.png
  - Added screenshot to DocsTimeTracking.js with feature_time_clock.jpeg
  - Screenshots use existing /screenshots/ assets with proper captions

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
