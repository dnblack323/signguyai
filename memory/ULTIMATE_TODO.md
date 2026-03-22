# SignGuy AI - Ultimate To-Do List
## Master Task Tracker (Staged by Priority)

> **Created:** March 18, 2026  
> **Status:** Active  
> **Current Plan:** Founders Edition Only ($99/mo)

---

# STAGE 1: CRITICAL FIXES & REINSTATEMENTS ✅ COMPLETED (March 20, 2026)
*All items resolved and tested (14/14 backend tests, 100% frontend verification).*

### 1.1 AI Tools Rate Limiter Parameter Fix ✅ DONE
- **Fixed:** All AI endpoints in `ai.py` now use `request: Request, data: PydanticModel` pattern
- **Scope:** generate_ai_content, generate_ai_images, generate_product_description, ai_business_assistant, generate_voice_output, generate_email, execute_assistant_action, confirm_assistant_action, parse_action_intent
- **Tested:** Endpoints accept new parameter pattern, no Pydantic validation errors

### 1.2 AI Credit Cost Audit & Assignment ✅ VERIFIED
- **All 28+ tools** have assigned credit costs (1-3 credits) in `founders_config.py`
- **AICreditConfirmationDialog.js** is wired with preflight check, "don't show again", low balance warning

### 1.3 AI Credit Confirmation Popup Audit ✅ VERIFIED
- **Popup** shows correct cost, has "don't show again" checkbox, warning badges for low balance/high cost
- **Preflight** endpoint `/api/credits/preflight` checks balance and preferences

### 1.4 Promo Code System - Backend ✅ DONE
- **Added:** `POST /api/billing/apply-promo` endpoint (validates, applies discounts, extends trials)
- **Added:** `free_days` discount type to `promo_codes.py`

### 1.5 Promo Code System - Frontend ✅ DONE
- **Added:** Promo code input to `TrialLockout.js` lockout screen
- **Added:** `free_days` (Free Extra Days) option to `PromoCodes.js` discount type selector

### 1.6 Invoice Line Items Fix Verification ✅ VERIFIED
- **Confirmed:** `create_invoice_from_job()` uses `sync_job_items_from_embedded_line_items` which reads both `job.line_items` and `job_items` collection
- **Fallback:** Falls back to `job.subtotal`, then `quote.total`

---

# STAGE 2: LEGAL, DOCUMENTATION & COLOR SCHEME ✅ COMPLETED (March 22, 2026)
*All items resolved and tested (11/11 frontend tests, 100% verification).*

### 2.1 Terms of Service Page ✅ DONE
- **Created:** `frontend/src/pages/TermsOfService.js` with 13 sections
- **Route:** `/terms` added to `App.js`
- **Content:** Agreement, service description, registration, subscription ($99/mo), billing fees (2.2%+$0.20, 2% webstore), AI credits, acceptable use, IP, liability, termination

### 2.2 Privacy Policy Page ✅ DONE
- **Created:** `frontend/src/pages/PrivacyPolicy.js` with 12 sections
- **Route:** `/privacy` added to `App.js`
- **Content:** GDPR-compliant with data collection, AI processing, third-party sharing (Stripe, SendGrid, OpenAI), security, retention, user rights, cookies

### 2.3 Footer Links ✅ DONE
- **Updated:** `PublicNav.js` footer now uses React Router `<Link>` to `/terms` and `/privacy`

### 2.4 Color Scheme Update - Founders Branding ✅ DONE
- **Changed:** amber/gold → violet/purple across all Founders-branded pages
- **Files updated:** BillingManagement.js, PricingPlansV2.js, LandingPage.js, FoundersEditionPricing.js, WhyFounderPage.js, TrialLockout.js, PublicNav.js

### 2.5 Update Documentation Pages
- **Status:** Deferred to next session (docs pages need Founders-only content audit)

### 2.6 Update Feature Catalog
- **Status:** Deferred to next session

### 2.7 Update Landing Page - Founders Focused ✅ DONE
- **Updated:** Color scheme to purple/violet, all Founders branding refreshed

---

# STAGE 3: NAVIGATION & UI OVERHAUL
*Major visual improvements and navigation fixes.*

### 3.1 Main Navigation Bar Redo
- **Files:** `PrimaryNav.js`, `ActionToolbar.js`, `MobileRibbonOverlay.js`
- **Verify:** All 11 primary tabs work correctly
- **Verify:** Sub-navigation per tab is contextual and accurate
- **Add:** Missing links (Documents in AI Tools, Admin Portal in Settings)
- **Fix:** Any broken or misaligned nav items
- **Verify:** Mobile hamburger menu works properly

### 3.2 Dark Shell / Light Workspace UI Overhaul
- **Concept:** Dark page background + light/dark content cards (not one mega-card per page)
- **Start with:** Jobs page
- **Apply to:** Dashboard, Customers, Invoices, Quotes, and all main pages
- **Pattern:** Multiple smaller cards per section instead of single page-wide card

### 3.3 All AI Tools Verification
- **Check:** Every tool in all 5 categories (Design, Business, Marketing, Racing, Branding) loads and executes
- **Verify:** Tool inputs render correctly
- **Verify:** AI response is displayed properly
- **Verify:** Save to Job, Download PDF, Send to Customer actions work
- **Verify:** Credit deduction on each tool

---

# STAGE 4: SEARCH, BULK ACTIONS & UX IMPROVEMENTS
*Productivity features for daily use.*

### 4.1 Jobs Page Search
- **Add:** `searchQuery` state and search input in filters card
- **Filter by:** customer name, job title/description, job number, status

### 4.2 Invoices Page Search
- **Add:** Search by customer, job reference, invoice number, notes

### 4.3 Webstores Page Search
- **Add:** Search by store name, owner, description

### 4.4 Jobs Page Bulk Actions
- **Add:** Checkbox selection per job row
- **Add:** Select All / Deselect All
- **Add:** Floating bulk action bar: Complete, Archive, Delete, Assign Employee
- **Add:** Keyboard shortcuts (A=Select All, C=Complete, R=Archive, Del=Delete, Esc=Clear)

### 4.5 Quick Add Job Button in Customer Modal
- **File:** `Customers.js` customer detail dialog
- **Add:** "Quick Add Job" and "Quick Add Quote" buttons
- **Navigate to:** `/jobs?new=true&customer_id={id}&type=job`

### 4.6 Settings Page Pricing Link
- **Add:** Card in `CompanySettings.js` linking to pricing settings and materials

---

# STAGE 5: MATERIALS & INVENTORY SYSTEM
*New feature - Materials management for pricing calculator.*

### 5.1 Materials Settings Page
- **Create:** `frontend/src/pages/MaterialsSettings.js`
- **Features:** CRUD for custom materials
- **Categories:** vinyl, print_media, laminate, substrate, hardware, supplies
- **Fields:** cost per unit, markup %, auto-calculated sell price
- **Special:** "Load Sign Shop Defaults" button (32 default materials)

### 5.2 Materials Backend Endpoints
- **File:** `backend/routes/pricing.py`
- **Endpoints:**
  - `GET /api/pricing/materials/catalog` - List tenant materials
  - `POST /api/pricing/materials` - Create material
  - `PUT /api/pricing/materials/{id}` - Update material
  - `DELETE /api/pricing/materials/{id}` - Delete material
  - `POST /api/pricing/materials/seed-defaults` - Seed 32 default materials

### 5.3 Pricing Calculator Integration
- **File:** `PricingCalculator.js`
- **Replace:** Hardcoded VINYL_TYPES, PRINT_MATERIALS, SUBSTRATE_TYPES with custom materials
- **Fallback:** Use defaults if no custom materials configured

### 5.4 App.js Route
- **Add:** `/pricing-calculator/materials` route to `MaterialsSettings`

---

# STAGE 6: INFRASTRUCTURE & CODE QUALITY
*Backend hardening and developer experience.*

### 6.1 Database Indexes
- **Create:** `backend/migrations/create_core_indexes.py`
- **Collections:** users, tenants, jobs, customers, invoices, quotes, employees, ai_history, payment_transactions, time_entries, conversations
- **Run:** `python migrations/create_core_indexes.py`

### 6.2 Rate Limiting
- **Install:** `slowapi`
- **Apply to:** AI endpoints, auth endpoints (login, register), public endpoints
- **Config:** Configurable per-route limits

### 6.3 Tier Config Deprecation
- **Reference:** `/app/memory/TIER_CONFIG_DEPRECATION_PLAN.md`
- **Action:** Remove `tier_config.py` usage, replace with `founders_plan.py` config
- **Update:** `feature_gate.py`, `routes/tiers.py` to use new config
- **Archive:** Old tier system files

### 6.4 Code Cleanup
- **Remove:** `console.log` statements from frontend (Pricing.js, Webstores.js, etc.)
- **Replace:** `print()` with `logger.error/info()` in backend (ai.py, billing.py)
- **Add:** `import logging` and `logger = logging.getLogger(__name__)` where needed

### 6.5 CORS Configuration
- **Update:** `server.py` CORS to use environment-based origins instead of `allow_origins=["*"]`
- **Add:** `CORS_ORIGINS` to `.env`

### 6.6 Error Boundaries
- **Create:** React Error Boundary component
- **Wrap:** Main app routes to prevent white-screen crashes
- **Add:** Fallback UI with retry option

---

# STAGE 7: FUTURE FEATURES (BACKLOG)
*Long-term roadmap items - not urgent.*

### 7.1 Vehicle Wrap AI Tool (Full Spec)
- **Reference:** `/app/memory/VEHICLE_WRAP_TOOL_SPECS.md`
- **Type:** Vector-based layout engine with AI-assisted placement
- **Features:** Canvas, layer system, sponsor logos, background generation

### 7.2 Master Product List
- **Centralized:** Filterable, searchable product catalog across webstores
- **Sync:** Products shared or cloned between stores

### 7.3 Learning Calculator
- **Concept:** Calculator that compares estimated vs actual production time/material usage
- **Learns:** Improves pricing accuracy over time

### 7.4 Cookie Consent Banner
- **Create:** Consent popup for GDPR compliance
- **Store:** User preference in localStorage

### 7.5 GDPR Data Tools
- **Add:** Data export (download all tenant data as JSON)
- **Add:** Data deletion request workflow
- **Add:** Right to be forgotten implementation

### 7.6 Mobile Responsiveness Pass
- **Audit:** All pages on mobile viewport
- **Fix:** Layout breaks, touch targets, font sizes
- **Priority:** Dashboard, Jobs, Customers, Invoices

### 7.7 QuickBooks Integration
- **Sync:** Customers, invoices, payments, expenses
- **Type:** OAuth-based connection

### 7.8 SMS Notifications (Twilio)
- **For:** Job status updates, appointment reminders, invoice due alerts
- **Config:** Per-tenant enable/disable

### 7.9 Scheduled Reports
- **Auto-generate:** Weekly/monthly revenue, job completion, outstanding invoices
- **Delivery:** Email to owner/admin

### 7.10 Custom Domain Support
- **For:** Webstores (yourshop.com instead of signshop.signguyai.com)

### 7.11 Advanced Pricing Calculators
- **Reference:** `/app/memory/FEATURE_ROADMAP.md` Update 1.1
- **Categories:** Apparel, Banner, Vehicle Wrap, Yard Sign, Decals, Window Graphics, Dimensional Letters, Monument Signs, Design Services, Installation
- **Each with:** Material selection, size, finish, extras, live profit display

### 7.12 Advanced Analytics
- **Revenue by:** Payment method, category, time period comparisons
- **Sales:** Conversion rate, average job value, top customers
- **Production:** Jobs/day, average time, on-time delivery rate

### 7.13 AI Powerhouse Features
- **AI Job Estimator** - Suggest pricing from history
- **Smart Scheduling** - AI job scheduling & workload balancing
- **Predictive Analytics** - Revenue forecasting, seasonal trends
- **Intelligent Recommendations** - Upsells, material alternatives

### 7.14 Inventory & Purchasing
- **Track:** Material stock levels, low stock alerts, reorder points
- **Usage:** Assign materials to jobs, track waste
- **POs:** Vendor database, purchase orders, receiving

### 7.15 Advanced Integrations
- **Calendar:** Google, Outlook, Apple sync
- **Communication:** Twilio SMS, Slack notifications
- **CRM:** HubSpot, Salesforce
- **Automation:** Zapier, webhooks, public API access

### 7.16 Webstore Advanced Features
- **Discount codes,** bulk pricing, minimum orders, product bundles
- **Custom domains,** multiple pages, banner images
- **Marketing:** Abandoned cart recovery, email marketing, SEO
- **Fulfillment:** Shipping calculations, tracking, packing slips

---

# STAGE SUMMARY

| Stage | Items | Focus | Priority |
|-------|-------|-------|----------|
| **Stage 1** | 6 items | Critical Fixes & Reinstatements | DO FIRST |
| **Stage 2** | 7 items | Legal, Docs, Color Scheme | LAUNCH READY |
| **Stage 3** | 3 items | Navigation & UI Overhaul | USER EXPERIENCE |
| **Stage 4** | 6 items | Search, Bulk Actions, UX | PRODUCTIVITY |
| **Stage 5** | 4 items | Materials & Inventory | NEW FEATURE |
| **Stage 6** | 6 items | Infrastructure & Code Quality | HARDENING |
| **Stage 7** | 16+ items | Future Features (Backlog) | LONG-TERM |

**Total: ~48+ tasks across 7 stages**

---

*This is the master to-do list. All items from BUILD_ROADMAP.md, FEATURE_ROADMAP.md, ROADMAP.md, PRD.md, TIER_CONFIG_DEPRECATION_PLAN.md, VEHICLE_WRAP_TOOL_SPECS.md, and user reinstatement notes have been consolidated here.*

*Last updated: March 18, 2026*
