# SignGuy AI - Product Requirements Document

## Original Problem Statement
Build a web-based sign-shop operating system called "SignGuy AI" - a single daily-use platform for sign and design shops replacing spreadsheets, notebooks, emails with a structured system for Customers, Quotes, Jobs, Invoices, Productivity, Financial tracking, Time clock & payroll, AI-assisted tools, and Fundraiser/B2B webstores.

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

### JobItem (Line Items for Jobs) - ENHANCED WITH PRICING CALCULATOR
- **job_id**: Reference to parent Job
- **item_type**: banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other
- **description**: Text description of the item
- **quantity**: Number (default 1)
- **unit_price**: Number (default 0)
- **line_total**: Calculated (qty × unit_price)
- **status**: pending, in_production, done
- **notes**: Optional text/file references
- **pricing_category**: promotional, cut_vinyl, services, digital_print, rigid_signs, apparel, vehicle_graphics, custom
- **pricing_data**: Category-specific fields (dimensions, materials, complexity, etc.)
- **pricing_calculation**: Calculated breakdown (material cost, labor cost, suggested price, margin)
- **production_cost**: For margin tracking

### Webstore Branding Model (NEW)
- **logo_url**: URL to customer's logo image
- **primary_color**: Hex color code for accent color (#0D9488 default)
- **banner_url**: Optional banner image URL

### Workflow Rules
- Converting Quote → Job automatically creates JobItems from Quote line items
- Invoice created from Job pulls JobItems into Invoice line_items array
- Job subtotal auto-recalculates when items are added/edited/deleted
- Job description serves as "overall job notes" - actual work lives in JobItems

## What's Been Implemented

### Phase 1 MVP - COMPLETE
- [x] Dashboard with real-time stats
- [x] Customer Management (CRUD, search, filters, status)
- [x] Quotes Module (line items, totals, convert to job)
- [x] Jobs Module (List view, Kanban board, status changes)
- [x] **Job Line Items** - Multiple line items per job with types, pricing, status
- [x] Invoice Management (create from job with line items, mark paid)
- [x] Time Clock (start/end work, breaks, sequence validation, shift summary)
- [x] Payroll (earnings/advances/payments, balance calculation, reports)
- [x] Productivity (tasks, calendar, job kanban)
- [x] Financial Tracking (sales, expenses, tax tracking, summaries)
- [x] AI Tools Suite (15 GPT-5.2 powered tools - NEW)
  - Design Tools: Photo Enhancer, Image Vectorizer, Font Identifier, AI Sign Designer, AI Banner Designer, Mockup Creator
  - Branding Tools: Logo Creator, Branding Kit Generator
  - Business Tools: Business Copywriter, Document Composer, Pricing Intelligence Assistant
  - Marketing Tools: Social Media Job Post Creator, Social Media Pack Generator, Content Calendar Creator, Campaign Builder
- [x] Webstores (Fundraiser campaigns, B2B custom stores)

### Recent Updates (February 10, 2026) - COMPLETED
- [x] **Pricing Calculator System** ✅ COMPLETE
  - **8 Pricing Categories**: Promotional Items, Cut Vinyl, Services, Digital Print, Rigid Signs, Apparel, Vehicle Graphics, Custom/Other
  - **Category-Specific Calculators**: Each category has its own form fields and pricing logic
  - **Real-Time Calculations**: Auto-calculates as user inputs data
  - **Pricing Breakdown**: Shows material cost, labor cost, setup fees, production cost, suggested price
  - **Profit Margin Display**: Shows markup %, profit margin %, and profit amount
  - **Complexity Multiplier**: 1-10 scale that affects pricing
  - **Quantity Breaks**: Automatic discounts at quantity thresholds
  - **Manual Override**: Users can override calculated price while tracking true cost
  - **Configurable Defaults**: Hourly rates, markups, minimums stored per-tenant in Company Settings
  - **Material Presets**: Built-in vinyl types, substrates, print materials, apparel blanks with costs
  - **Standalone Tool**: Available at /pricing for quick price checks
  - **Tier Preview Toggle**: Admin can preview different subscription tiers (Starter/Pro/Business)
  - **Save as Template**: Save any calculation as a reusable template
  - **Templates Browser**: Load, favorite, and delete saved templates
  - **Pricing Settings Page**: Configure default labor rates, markups, minimums, complexity multipliers, quantity breaks, and setup fees at /pricing/settings
  - **Jobs Integration**: "Use Calculator" button in Job Details line items section opens calculator modal, calculated items auto-populate the add item form
  - **Quotes Integration**: "Calculate" button in New Quote form opens calculator modal, adds items directly to quote line items

- [x] **Full Customer Portal** ✅ COMPLETE
  - **Portal Authentication:** Separate JWT-based auth (type='portal') for customers
  - **Registration:** Customers register using their email on file with the shop
  - **Login Page:** Secure login at `/customer-portal/login` with Sign In/Register tabs
  - **Dashboard:** Stats cards (Active Jobs, Quotes, Pending Invoices, Proofs Awaiting, New Messages, Notifications), Recent Orders, Recent Invoices, Upcoming Appointments
  - **Orders Page:** View all orders with status filters, order detail view with line items
  - **Quotes Page:** View all quotes with status filters
  - **Invoices Page:** View invoices with balance due display
  - **Messages:** Two-way communication with shop via conversations, create new messages, message history
  - **Artwork Approvals:** View proofs, approve/reject/request revisions with comments
  - **Appointments:** View upcoming and past appointments
  - **Profile Management:** Update name, phone, profile image URL
  - **Tax Exempt Status:** Enable tax exempt, link to certificate document
  - **Notification Preferences:** Toggle email notifications for messages, orders, approvals, payments
  - **Security:** Change portal password
  - **Shop-Side Management:** Enable/disable customer portal access, view conversations, upload artwork proofs, create appointments

### Recent Updates (February 10, 2026) - COMPLETED
- [x] **Webstores Phase 2: Enhanced Store Dashboard** ✅ COMPLETE
  - **Store Analytics Dashboard:** Total revenue, orders, profit, avg order value KPIs
  - **Sales Trend Chart:** Visual bar chart showing sales over last 14 days
  - **Top Products:** Ranked list of best-selling products with revenue
  - **Order Status Breakdown:** Visual cards showing pending/processing/completed/total
  - **Fundraiser Progress:** Progress bar toward goal, days remaining, profit split visualization
  - **Orders Management Tab:** Full order list with customer details, status, date
  - **Payouts Tab:** Balance tracking, record new payouts, payout history
  - **Email Notifications:** SendGrid integration for new order notifications (when configured)
  - **Long Logo Integration:** SignGuy long logo in expanded sidebar header

### Recent Updates (February 10, 2026) - COMPLETED
- [x] **Sprint 7: Multi-Tenancy (SaaS Foundation)** ✅ COMPLETE
  - **Tenant Model:** Added `Tenant` entity with fields: id, name, slug, owner_email, phone, address, city, state, zip_code, country, website, logo_url, plan, is_active, created_at, updated_at
  - **Data Isolation:** All data models (Customer, Quote, Job, Invoice, Employee, Product, Webstore, etc.) now have `tenant_id` field
  - **Tenant-Scoped Queries:** All API routes filter data by current user's tenant_id
  - **Auto-Assignment:** New records automatically get assigned the current user's tenant_id
  - **Tenant Management API:**
    - `GET /api/tenant/current` - Returns tenant info for authenticated user
    - `PUT /api/tenant/settings` - Updates tenant settings (name, phone, address, etc.)
  - **Company Settings Page:** New UI for viewing and editing company information
  - **First User = Owner + Tenant:** First registered user creates a new tenant and becomes owner
  - **Data Migration:** All existing records migrated to default tenant

### Recent Updates (February 10, 2026) - COMPLETED
- [x] **Sprint 6: Role-Based Access Control (RBAC)** ✅ COMPLETE
  - **Three User Roles:** Owner (full access, 39 permissions), Admin (operational access, 30 permissions), Staff (limited access, 7 permissions)
  - **Backend Implementation:**
    - Permission enum with 39 granular permissions
    - ROLE_PERMISSIONS matrix mapping roles to permissions
    - `has_permission` and `require_permission` dependency helpers
    - All admin endpoints (`/api/admin/users/*`) check permissions
    - First registered user automatically becomes Owner
  - **Frontend Implementation:**
    - AuthContext provides `hasPermission`, `hasAnyPermission`, `isOwner`, `isAdminOrOwner` helpers
    - Navigation filtering - Staff doesn't see Admin category
    - Protected pages (Financials, Invoices, Payroll, UserManagement) show "Access Denied" for unauthorized users
    - Role badges with color coding: Owner (amber/crown), Admin (blue), Staff (gray)
  - **Permission Matrix:**
    - Owner: All 39 permissions including users:manage_roles
    - Admin: 30 permissions (view-only for payroll/financials, no role management)
    - Staff: 7 permissions (view customers/quotes/jobs, own timeclock, AI tools)
  - **100% test coverage** - 26 backend tests, all frontend features verified

### Recent Updates (February 8, 2026) - COMPLETED
- [x] **Complete UI Redesign - Unified Blended Theme** ✅ COMPLETE
  - Implemented dark shell (#2E2E2E) with light content panels (#F5F7FA, #FFFFFF)
  - Brand color: Primary Blue (#2F8BFB) for buttons, highlights, active states
  - Removed all Light/Dark/Contrast mode toggles - single unified theme
  - Proper text contrast: #1A1A1A on light, #F2F2F2 on dark
  - Panel border color: #D7DCE2

- [x] **Hover-Expanding Navigation** ✅ COMPLETE
  - Compact collapsed state (56px width, icons only)
  - Expands on hover (260px width) with category labels
  - Nested flyout submenus on category hover
  - Smooth 150-250ms hover delay to prevent flicker
  - Active page highlighting with #2F8BFB background
  - User info and Sign Out at bottom

- [x] **Component Updates**
  - New Login page with blended theme styling
  - Dashboard with themed stat cards and panels
  - Theme-consistent buttons, badges, tabs, tables
  - Reusable theme components at `/app/frontend/src/components/ui/theme-components.jsx`

- [x] **AI Tools Suite - All 15 Tools Verified** ✅ COMPLETE
  - **Vision Analysis Tools (Gemini 2.5 Flash):**
    - Photo Enhancer Analyzer - Analyzes images for print-readiness
    - Vectorization Analyzer - Provides vectorization guidance
    - Font Identifier - Identifies fonts from uploaded images
  - **Image Generation Tools (OpenAI gpt-image-1):**
    - AI Sign Designer, AI Banner Designer, Mockup Creator, Logo Creator
  - **Text Generation Tools (GPT-5.2):**
    - Branding Kit Generator, Business Copywriter, Document Composer
    - Pricing Intelligence, Social Job Post, Social Media Pack Generator
    - Content Calendar Creator, Campaign Builder
  - Test suite created at `/app/backend/tests/test_all_ai_tools.py`

### Recent Updates (February 7, 2026) - COMPLETED
- [x] **User Authentication System** ✅ COMPLETE
  - JWT-based authentication with 24-hour token expiry
  - Backend endpoints: `/api/auth/register`, `/api/auth/login`, `/api/users/me`
  - Password hashing with bcrypt
  - Protected routes redirect to login when not authenticated
  - User profile display in sidebar (name & company)
  - Logout functionality clears token and redirects to login
  - Public storefront (`/store/:storeId`) remains accessible without auth
  - 100% backend tests passing (22/22)
  - Test suite created at `/app/backend/tests/test_auth.py`

- [x] **Remember Me Feature** ✅ COMPLETE
  - Checkbox on login form
  - Extended token expiry: 30 days when checked (vs 24 hours default)

- [x] **Admin Password Reset** ✅ COMPLETE
  - User Management page (`/users`) with search functionality
  - Admin can reset any user's password
  - Admin can enable/disable user accounts
  - Cannot modify own account status (safety)

- [x] **Magic Links for Customer Portal** ✅ COMPLETE
  - Generate shareable links for quotes, jobs, invoices
  - Links expire after 7 days (configurable)
  - Customer portal page (`/portal/:token`) - no login required
  - "Share Link" button in quote preview modal
  - Copy link functionality with visual feedback

### Recent Updates (February 7, 2026) - COMPLETED
- [x] **AI Tools Image Generation FIXED** ✨
  - Logo Creator, Banner Designer, Sign Designer, Mockup Creator, Photo Enhancer, Image Vectorizer now generate ACTUAL IMAGES
  - Uses OpenAI gpt-image-1 via Emergent LLM key
  - Returns 2-3 design options per request with base64 images
  - **Design Notes shown alongside images** so users understand the design rationale

- [x] **Photo Enhancer Updated**
  - Now has image upload field (not text URL)
  - Generates 2 enhanced image options

- [x] **Image Vectorizer Updated**
  - Now has image upload field
  - Added "Number of Colors" dropdown (2, 3, 4, 6, 8, full color)
  - Added "Source Image Type" dropdown (crisp line art, blurry edges, hand drawn, etc.)

- [x] **Font Identifier Fixed**
  - Has image upload field
  - Removed unnecessary "what will you use font for" field
  - Just needs image + optional text sample

- [x] **NEW: Contrast Theme** ✨
  - Third theme option: Dark background with light content cards
  - Teal/green sidebar and page background
  - White/light cards for content areas
  - Better text readability with dark text on light backgrounds
  - Theme cycles: Dark → Light → Contrast → Dark

- [x] **Job Scheduling Fixed**
  - Task title auto-fills with job name (editable)
  - Added time input alongside date

- [x] **Number Input UX Fixed**
  - Fields show empty with placeholder when value is 0

### Recent Updates (February 5, 2026) - COMPLETED
- [x] **AI Tools Suite Revamp** ✨
  - Replaced old 6 tools with comprehensive 15-tool suite
  - **Design Tools (6):** Photo Enhancer, Image Vectorizer, Font Identifier, AI Sign Designer, AI Banner Designer, Mockup Creator
  - **Branding Tools (2):** Logo Creator, Branding Kit Generator
  - **Business Tools (3):** Business Copywriter, Document Composer, Pricing Intelligence Assistant
  - **Marketing Tools (4):** Social Media Job Post Creator, Social Media Pack Generator, Content Calendar Creator, Campaign Builder
  - Category filtering for easy tool discovery
  - History feature to view previous generations
  - Copy/Export functionality for results

- [x] **Public Storefronts with Custom Branding** ✨
  - Logo URL field for each webstore (customer's company logo)
  - Accent color picker for customizing storefront appearance
  - Live preview of color selection in admin UI
  - Settings tab in store detail dialog for editing branding
  - Copy Link & Open Store buttons in store manager
  - Public storefront displays custom logo and uses accent color
  - Fully functional shopping cart and checkout flow
  - Order creation with profit/payout calculations

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
- [x] **Invoice Preview Modal** - Click "View Invoice" opens popup modal
- [x] **Daily Sales Entry Enhancement** - Payment method tracking
- [x] Dashboard Recent Activity - Clicking jobs navigates to job details

### Testing Results (February 5, 2026)
- Backend: 100% tests passing
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
/api/products - Master product catalog CRUD
/api/webstores/v2 - Webstore CRUD with branding
/api/webstores/v2/{id}/products - Product assignment
/api/webstores/v2/orders - Order management
/store/{storeId} - Public storefront URL
/api/auth/register - User registration (returns JWT)
/api/auth/login - User login (returns JWT)
/api/users/me - Get/Update current user profile (protected)

# Customer Portal API
/api/portal/auth/register - Customer portal registration
/api/portal/auth/login - Customer portal login
/api/portal/dashboard - Portal dashboard data
/api/portal/profile - Get/Update customer profile
/api/portal/change-password - Change portal password
/api/portal/orders - Customer's orders (jobs)
/api/portal/quotes - Customer's quotes
/api/portal/invoices - Customer's invoices
/api/portal/conversations - Customer's messaging conversations
/api/portal/proofs - Customer's artwork proofs
/api/portal/proofs/{id}/respond - Approve/reject/request revision on proof
/api/portal/appointments - Customer's appointments
/api/portal/notifications - Customer's notifications
/api/portal/magic/{token} - Magic link access (public)

# Shop-Side Portal Management
/api/customers/{id}/enable-portal - Enable portal access for customer
/api/shop/conversations - View all customer conversations
/api/shop/proofs - Manage artwork proofs
/api/shop/appointments - Manage appointments
```

## Prioritized Backlog

### P0 - Critical (Next Sprint)
- [ ] Sprint 8: Smart Pricing Engine (real-time profit margin calculators)
- [x] User Authentication (JWT) ✅ COMPLETED Feb 7, 2026
- [x] Role-based access control (Owner, Admin, Staff) ✅ COMPLETED Feb 10, 2026
- [x] Multi-Tenancy (SaaS Foundation) ✅ COMPLETED Feb 10, 2026
- [x] Webstores Phase 2: Enhanced Store Dashboard ✅ COMPLETED Feb 10, 2026
- [x] Full Customer Portal ✅ COMPLETED Feb 10, 2026

### P1 - High Priority
- [ ] Buy Now, Pay Later (BNPL) Integration - Affirm & Klarna
- [ ] Sprint 9: Artwork Approval System (upload proof, customer approve/reject) - PARTIALLY DONE via Customer Portal
- [ ] Sprint 10: Stripe Subscription & Billing
- [ ] Email notifications configuration (SendGrid API key setup)
- [ ] Print-ready file generation
- [ ] Mobile-responsive time clock interface
- [ ] Productivity Module enhancements (Kanban, Calendar)

### P2 - Medium Priority
- [ ] Webstores Phase 2: External Dashboard for fundraiser organizers
- [ ] Financial Tracking summary views and reports (Cash vs Credit vs Check breakdown)
- [ ] Report generation and analytics
- [ ] Bulk operations (multi-select delete, status update)
- [ ] Search across all modules
- [x] Customer portal for viewing quotes/invoices ✅ COMPLETED Feb 10, 2026
- [ ] Data export functionality (CSV/PDF)

### P3 - Low Priority / Future
- [ ] Integrations (QuickBooks, Stripe payments)
- [ ] Advanced scheduling calendar
- [ ] Real-time collaboration features
- [ ] Google OAuth integration (optional addition to existing JWT auth)

## Next Tasks
1. **Continue Backend Refactoring**: Migrate route handlers from server.py to /routes modules
2. Implement full SaaS Tier System (backend logic and feature gating) - awaiting user's tier configuration
3. Integrate Buy Now, Pay Later (BNPL) - Affirm & Klarna for customer payments
4. Webstores Phase 2: External Dashboard for fundraiser organizers
5. Sprint 10: Stripe Subscription & Billing

## Architecture Notes
The backend has been substantially refactored into a modular structure:

### Completed Modules:
- `/app/backend/core/` - Configuration, database, auth utilities (79 lines)
- `/app/backend/models/` - All Pydantic models and enums (1,099 lines - COMPLETE)
  - `enums.py` - 25+ enums (252 lines)
  - `auth.py` - User, Tenant, Permission, Token models (199 lines)
  - `customer.py` - Customer, Portal, Conversation, Proof models (169 lines)
  - `jobs.py` - Quote, Job, JobItem, Invoice models (175 lines)
  - `pricing.py` - PricingDefaults, PricingCalculation, Template models (254 lines)
- `/app/backend/routes/` - API route handlers (1,712 lines - 70% COMPLETE)
  - `auth.py` - Authentication, user profile, admin management (266 lines)
  - `customers.py` - Customer CRUD operations (154 lines)
  - `quotes.py` - Quote CRUD, convert to job (229 lines)
  - `jobs.py` - Job CRUD, items, notes, activities, status (488 lines)
  - `invoices.py` - Invoice CRUD, from-job, payments (281 lines)
  - `pricing.py` - Calculator, templates, materials catalog (259 lines)

### Pending Migrations:
- Customer Portal routes (~400 lines)
- Webstore routes (~600 lines)
- Time Clock/Payroll routes (~300 lines)
- Employee routes (~100 lines)
- Financial/Dashboard routes (~200 lines)

### Current Status:
- `server.py`: 6,349 lines (still serves all requests)
- Modular code: 2,890 lines (ready for integration)
- Routes are duplicated between server.py and /routes modules
- Final step: Update server.py to import and use modular routes

