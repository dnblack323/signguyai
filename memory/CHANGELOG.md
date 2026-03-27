# SignGuy AI - Changelog

## March 27, 2026
- Updated all documentation (Feature Catalog, Build Roadmap, Docs pages) to reflect Order/Job Ticket system
- Removed all references to old "Jobs" module from docs and navigation
- Updated DocsQuotesJobs → DocsOrdersTickets (Orders & Job Tickets documentation)
- Updated DocsEmployees with schedule feature documentation
- Updated GettingStarted guide with order workflow
- Updated DocsOverview with 4-layer architecture description

## March 26, 2026
- Fixed: Sales and expense recording (created /api/financials/sales and /api/financials/expenses endpoints)
- Fixed: Schedule dialog not opening (removed conditional wrapper)
- Fixed: Owner permissions (hasPermission now grants all permissions to owner role)
- Fixed: Contact Support now emails donnell@signguy-ai.com
- Navigation: Financials moved to top-level, Reports = shortcuts page
- Theme: Applied light theme to PricingSetup, CompanySettings, PaymentSettings
- Workflow Templates: Removed duplicate QC toggle, kept only Required
- New Order Form: Added ticket buttons near Save, fixed zero placeholder, better error handling
- Square footage: Default changed to inches (18x24 = 3 sqft, not 432)
- LivePricingPreview: Added all finishing options, fixed apparel trigger
- Production Board: Shows ticket name first, task name secondary

## March 25, 2026
- Fixed: Setup fee markup bug — $25 fee was causing $67 increase, now adds exactly $25 (flat, not marked up)
- Fixed across ALL 6 calculator functions
- Added: Generate Work Order on order detail
- Added: Apparel quantity discounts (5-25% based on qty tiers)
- Improved: Stripe Connect error messaging

## March 24, 2026
- Built: File upload system for orders (upload, list, delete)
- Built: Live pricing preview on new order form (calls pricing API in real-time)
- Built: Employee schedule system (weekly grid, shift dialog, save to DB)
- Built: Materials & Pricing admin page (global rates, material CRUD)
- Added: Files tab on Order Detail page
- Added: Order action buttons (Generate Quote/Invoice/Work Order, Email, Status, Portal)
- Created: 30 database indexes for production performance

## March 23, 2026
- Built: Full Banner category schema (24 fields, 7 subtypes)
- Built: Full Apparel category schema (27 fields, 8 subtypes, size grid, print locations with per-location details)
- Built: Rigid Signs, Cut Vinyl, Digital Print, Vehicle Wrap schemas (22-30 fields each)
- All material options now from centralized catalog (not hardcoded)
- Calculator wiring: all dynamic fields map to pricing engine
- Quick Entry / Detailed Entry modes for job tickets
- Legacy Jobs removed from navigation, redirects to Orders
- Dashboard quick actions updated (New Job → New Order)
- Dark shell / light content theme applied globally (20+ pages)
- Container widened to 1600px

## March 22, 2026
- Built: Complete 4-layer Order system backend (Orders, Job Tickets, Production Tasks, Workflow Templates)
- Built: Frontend pages (OrdersPage, OrderDetail, NewOrderForm, JobTicketDetail, ProductionBoard, WorkflowTemplateManager)
- 6 default workflow templates, activity logging, status roll-up
- Terms of Service and Privacy Policy pages
- Color scheme: amber/gold → violet/purple across all Founders-branded pages
- Founder grace period (14 days read-only after subscription lapse)
- Multiple production bug fixes (login, promo codes, onboarding, mobile nav)

## March 20, 2026
- Stage 1 Critical Fixes: AI rate limiter, promo code system, invoice line items
- Deployment fix: requirements.txt cleaned from 137 → 24 packages
- SendGrid email configured
- Production setup endpoint and page (/setup)
