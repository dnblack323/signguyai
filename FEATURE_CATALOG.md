# SignGuy AI - Complete Feature Catalog
**Updated: March 14, 2026**
**Version: Current Build**

---

# A) APP FEATURE CATALOG (IMPLEMENTED)

---

## 1. AUTHENTICATION & USER MANAGEMENT

**Where it lives:** `/login`, `/users`

**Who can access it:** Public (registration/login), Owner/Admin (user management)

**Core actions:** Register, Login, Logout, Create User, Update User Role, Delete User

**Sub-features:**
- JWT-based authentication with 24-hour expiry
- Multi-tenant isolation (each user belongs to one tenant)
- Three user roles: Owner, Admin, Staff
- Role-based permission system with 23 permission types
- Founder account flag (special access to promo codes, tier preview)
- Auto-create tenant on first user registration
- Assign owner role to first user of tenant

**Data:** `users`, `tenants`

**Status:** WORKING

---

## 2. DASHBOARD

**Where it lives:** `/dashboard`

**Who can access it:** All authenticated users

**Sub-features:**
- Greeting with user name and Founding Shop badge
- 4 stat cards: Total Customers, Active Jobs, Pending Invoices, Today's Revenue
- Today's Schedule with job status badges
- Pending Approvals widget (linked to artwork proofs)
- Messages inbox (customer conversations)
- Clocked In employees widget
- Quick Actions: New Customer, New Quote, New Job, Time Clock
- Recent AI Documents widget (last 5, with create link)
- Dynamic Onboarding Checklist (10-step, real-time progress)

**Integrations:** Dashboard API endpoints (`/api/dashboard/stats`, `/api/dashboard/pending-approvals`, `/api/dashboard/unread-messages`, `/api/dashboard/clocked-in`, `/api/dashboard/todays-schedule`, `/api/dashboard/onboarding-status`, `/api/dashboard/recent-ai-documents`)

**Status:** WORKING

---

## 3. CUSTOMERS (CRM)

**Where it lives:** `/customers`

**Who can access it:** Permission-based (`customers:view`, `customers:create`, `customers:edit`, `customers:delete`)

**Sub-features:**
- Customer list with search and filtering
- Customer status tracking (Lead, Active, Inactive)
- Contact info (email, phone, address, company)
- Customer notes and tags
- Tax exempt status flag
- Portal access toggle (enables Customer Portal login)
- Customer-specific pricing toggle
- CSV Import with column mapping and template download
- Bulk create/update customers
- View related jobs/quotes/invoices per customer
- Card view on mobile (responsive)

**Data:** `customers` collection

**Status:** WORKING

---

## 4. JOBS (UNIFIED QUOTES & JOBS)

**Where it lives:** `/jobs`, `/jobs/:id`

**Who can access it:** Permission-based (`jobs:view`, `jobs:create`, `jobs:edit`, `jobs:delete`)

**Architecture:** A quote is a job in the "quote" stage. Single `jobs` collection, status-based filtering.

**Status Pipeline:**
```
quote -> approved -> in_progress -> completed -> invoiced -> archived
```

**Sub-features:**
- Quick filter badges for each status
- Create New dropdown: "New Quote (Pipeline)" / "New Job (Ready for production)"
- Line items: Banner, Yard Sign, Decal, Wrap, Install, Design, Vehicle Graphics, Window Graphics, Dimensional Letters, Monument Sign, Other
- Item status: Pending, In Production, Done
- Job notes with timestamps
- Job activity log (all status changes, item additions)
- Convert quote to job (approve button on quote rows)
- Job time tracking (start/stop timer per job with task types)
- Job Status Timeline (visual flow diagram with checkmarks, status history, time-in-status)
- Fully clickable job list rows

**Data:** `jobs`, `job_items`, `job_notes`, `job_activities`, `job_time_entries`

**Status:** WORKING

---

## 5. INVOICES

**Where it lives:** `/invoices`

**Who can access it:** Permission-based (`invoices:view`, `invoices:create`, `invoices:edit`, `invoices:delete`)

**Sub-features:**
- Invoice statuses: Draft, Sent, Paid, Overdue
- Create invoice from job
- Line items with quantities and prices
- Tax calculation and auto-total
- Invoice number auto-generation
- Due date tracking
- Payment method tracking (Cash, Check, Card, Bank Transfer, Other)
- PDF export (reportlab)
- Email send with AI-drafted email option
- Invoice preview modal (white background, dark text)
- Stripe Connect "Pay Link" button for online payments

**Data:** `invoices`

**Status:** WORKING

---

## 6. TIME CLOCK

**Where it lives:** `/timeclock`

**Who can access it:** Permission-based (`time:own`, `time:view_all`, `time:manage`)

**Sub-features:**
- Clock in/out functionality with sequence validation
- Break start/end tracking
- Time entries per job with task type selection (design, production, installation, admin)
- Manual time entry and edit/delete
- Real-time running timer display (HH:MM:SS)
- Time reports by employee and by job
- Daily/weekly/monthly summaries
- Prevents duplicate active timers per employee per job
- Kiosk mode (simplified clock-in interface)
- Auto-suggest time entry on job status change (configurable)

**Data:** `timelogs`, `job_time_entries`

**API Endpoints:** `/api/jobs/{id}/time/start`, `/api/jobs/{id}/time/stop`, `/api/jobs/{id}/time/summary`, `/api/jobs/{id}/time/active`, `/api/jobs/time/my-active`

**Status:** WORKING

---

## 7. ADMIN PAYROLL

**Where it lives:** `/payroll`

**Who can access it:** Owner, Admin (Permission: `payroll:view`, `payroll:manage`)

**Sub-features (4-Tab Layout):**

**Overview Tab:**
- Pay Period Summary table (per-employee: rate, hours, overtime, gross pay, advances, payments, net owed)
- Weekly or Bi-Weekly period selector
- Summary cards: Total Hours, Regular Hours, Overtime Hours, Gross Pay, Net Owed

**Time Sheets Tab:**
- Consolidated view combining job timer entries + manual hours
- Employee filter and date range filters
- Per-entry breakdown showing source (Timer vs Manual), job name, task type, hours, pay

**Manual Hours Tab:**
- Add/Edit/Delete manual hours entries
- Per-job allocation (optional job assignment)
- Task type categorization (general, design, production, installation, admin)
- Automatic gross pay calculation (hours x hourly rate)

**Transactions Tab:**
- Earnings, Advances, Payments ledger
- Employee filter
- Add Transaction dialog (type, amount, date, description)
- Balance formula: Earnings - Advances - Payments

**Overtime Calculation:**
- Automatic 1.5x overtime for hours over 40/week (or 80/biweekly)

**Data:** `payroll_transactions`, `payroll_hours`, `employees`, `job_time_entries`

**API Endpoints:** `/api/payroll/hours` (CRUD), `/api/payroll/timesheet`, `/api/payroll/pay-period`, `/api/payroll/transactions`, `/api/payroll/balance/{id}`, `/api/payroll/report`

**Status:** WORKING

---

## 8. EMPLOYEES

**Where it lives:** `/users` (employees managed under Users page)

**Who can access it:** Owner, Admin (Permission: `employees:view`, `employees:manage`)

**Sub-features:**
- Employee profiles with name, email, phone
- Hourly rate configuration
- Portal PIN for employee portal access (4-6 digit)
- Role assignment and active/inactive status
- Profile image upload
- Employee Portal permissions configuration (Tasks, Schedule, Pay Stubs, Time Clock, Edit Profile)
- Sensitive info toggles (Job Details, Customer Info, Pricing - all OFF by default)

**Data:** `employees`

**Status:** WORKING

---

## 9. PRODUCTIVITY

**Where it lives:** `/productivity`

**Sub-features:**
- Daily productivity summary
- Jobs completed tracking
- Time logged summary
- Employee productivity comparison

**Status:** WORKING

---

## 10. FINANCIALS

**Where it lives:** `/financials`

**Who can access it:** Owner, Admin (Permission: `financials:view`)

**Sub-features:**
- Revenue tracking by period
- Expense tracking with 21 categories (Materials, Labor, Equipment, Utilities, Rent, Insurance, Cell Phone, Garbage, Printing Supplies, Meals, Entertainment, Donations, Office Supplies, Apparel, Vehicle, Advertising, Legal, Repairs, Taxes, Travel, Other)
- Sales entries
- Profit calculation
- Monthly summaries
- Category breakdown

**Data:** `expense_entries`, `sales_entries`, `invoices`

**Status:** WORKING

---

## 11. AI TOOLS SUITE

**Where it lives:** `/ai-tools`

**Who can access it:** All authenticated users (credit-gated)

**Categories & Tools (28+ Total):**

**Design & Visual (Image Generation):**
- Photo Enhancer - Analyze and suggest improvements
- Image Vectorizer - Vectorization guidance
- Font Identifier - Identify fonts in images
- AI Sign Designer - Sign design concepts (3 images)
- AI Banner Designer - Banner concepts (3 images)
- Logo Refresher - Logo redesign suggestions (3 images)
- Generative Fill / Image Expander - Expand images with AI (2 images)
- Text to Image Creator - Custom image generation (3 images)
- Logo Creator - New logo designs
- Mockup Creator - Product mockups
- Vehicle Wrap Mockup Generator - Wrap previews on vehicles

**Business & Writing (Text Generation):**
- Tagline Generator
- Brand Color Advisor
- Brand Voice Guide
- Proposal Writer
- Review Responder
- Email Templates
- SEO Content
- Business Copywriter - Marketing copy
- Document Composer - Business documents
- Pricing Intelligence - Pricing analysis
- AI Product Description Generator (auto-fills product descriptions)

**Marketing & Social:**
- Blog Article Creator - Full articles with SEO
- Completed Job Post Creator - Social media from job photos
- Showcase Post
- Social Pack Generator - Multiple post ideas
- Content Calendar - Marketing calendar
- Campaign Builder - Marketing campaigns
- Branding Kit Generator - Complete brand system

**Racing & Motorsports:**
- Race Number Designer (3 images)
- Driver Name Plate Generator (2 images)
- Vehicle Wrap Cost Calculator (text)
- Race Team Branding Kit (3 images)

**AI Tool Features:**
- AI History (view past generations)
- Save to job capability
- Download PDF button
- Save to Document Library button
- Send to Customer button (with customer selection)
- Credit system integration (1-3 credits per action)

**Integrations:** OpenAI GPT-5.2 (text), GPT Image 1 (images), Emergent LLM Key

**Data:** `ai_history`, `ai_responses`, `ai_usage_logs`

**Status:** WORKING

---

## 12. AI BUSINESS ASSISTANT

**Where it lives:** `/ai-assistant`

**Sub-features:**
- Natural language business queries
- Context-aware responses using actual shop data:
  - Customer stats (total, new in 30 days)
  - Job stats (total, active, completed, average value)
  - Revenue (all-time, last 30 days, pending invoices)
  - Quote conversion rate
  - Top job categories by revenue
  - Top customers by spend
  - Employee count & webstore stats
- Conversation chat interface

**Integrations:** OpenAI GPT-5.2, Emergent LLM Key

**Status:** WORKING

---

## 13. AI PRICING ADVISOR

**Where it lives:** Integrated in Pricing Calculator

**Sub-features:**
- AI-powered pricing suggestions
- Analyzes current pricing and provides actionable recommendations
- Suggests quantity tiers, upsells, margin improvements

**Status:** WORKING

---

## 14. AI EMAIL COMPOSER

**Where it lives:** Integrated in Invoice/Quote preview modals

**Sub-features:**
- AI Email Composer component for contextual email drafting
- Invoice emails: Send, Reminder, Overdue notices
- Quote emails: Send, Follow-up
- "AI Draft" button on Invoice and Quote Preview Modals

**API:** `/api/ai/generate-email`

**Status:** WORKING

---

## 15. APPROVALS (ARTWORK PROOFS)

**Where it lives:** `/approvals`

**Sub-features:**
- Dashboard with stats cards (Total Proofs, Awaiting Approval, Approved, Needs Revisions)
- Upload artwork file (PNG, JPG) with client-side watermarking
  - Diagonal company name pattern
  - Bottom disclaimer: "PROOF ONLY - Artwork remains property of [Company]..."
- Link proofs to customers and jobs
- Track proof status (Pending, Approved, Revision Requested, Rejected)
- Version tracking and customer feedback
- Resend notifications
- Customer Portal integration (proofs sent to portal)

**Data:** `artwork_proofs`

**Status:** WORKING

---

## 16. DOCUMENT LIBRARY

**Where it lives:** `/documents`

**Sub-features:**
- File upload (images, PDFs, documents) with drag-and-drop
- 12 document categories: Contract, Invoice Template, Work Order, Artwork, Proof, Permit, Insurance, Warranty, Quote Template, Customer Form, Internal, Other
- Template system (mark documents as reusable templates)
- Search and category filtering
- Document stats dashboard
- View document details (preview, metadata)
- **3 Send Methods:**
  - **Email PDF** - Send as attachment (no response needed)
  - **Customer Portal** - Add to portal for viewing (no response needed)
  - **As Form** - Send as interactive questionnaire (customer fills out and submits)
- AI-generated documents: Save from AI Tools to library
- Tags system
- Activity logging

**Data:** `documents`, `document_activities`, `portal_documents`

**Status:** WORKING

---

## 17. QUESTIONNAIRES & FORMS

**Where it lives:** `/questionnaires`, `/questionnaire/:id` (public)

**Sub-features:**
- Create custom questionnaires with multiple question types
- Pre-built templates (Vehicle Wrap, Logo Design Brief, Sign Project Intake, etc.)
- Public shareable link for customer completion
- Customer portal integration
- Response tracking
- AI summary of questionnaire responses

**Data:** `questionnaires`, `questionnaire_responses`

**Status:** WORKING

---

## 18. PRICING CALCULATOR

**Where it lives:** `/pricing-calculator`, `/pricing-calculator/settings`

**Sub-features:**
- **8 Category-based pricing:**
  - Promotional products, Cut vinyl, Services/labor, Digital print, Rigid signs, Apparel, Vehicle graphics, Custom items
- **Material configurations:**
  - Vinyl types: Oracal 651/751/951, Avery HP750, Reflective, Specialty
  - Print materials: Banner 13oz/18oz, Adhesive vinyl, Poster, Canvas, Backlit, Perforated
  - Substrates: Coroplast, Aluminum, PVC, Acrylic, Dibond, MDO
- Service types: Design, Installation, Removal, Site Survey, Consultation, Travel
- Apparel: T-shirt, Hoodie, Hat, Polo, Tank, Longsleeve, Jacket
- Transfer: HTV, Screen Print, DTF, Sublimation, Embroidery
- Vehicle: 18+ vehicle types with coverage options
- Complexity slider (1.0x to 2.0x multiplier)
- Optional setup fee (one-time per order)
- Industry-standard pricing (aligned with market rates)
- Pricing templates (save/load configurations)
- Per-tenant default customization
- AI Pricing Advisor integration

**Data:** `pricing_defaults`, `pricing_templates`

**Status:** WORKING

---

## 19. WEBSTORES

**Where it lives:** `/webstores`, `/products`, `/store/:storeId` (public)

**Sub-features:**

**Store Types:** B2B, Fundraiser, Creator

**Store Management:**
- Store creation with name, type, description, owner info
- Store status: Active, Paused, Completed, Archived
- Branding: Logo upload, banner upload, primary color picker
- Public/private toggle
- QR code generation for store URLs
- Unified "Settings & Branding" tab

**Product Management:**
- Master product catalog with 5 categories (Apparel, Signs, Decals, Promotional, Other)
- Product images (up to 3) with upload UI
- Base cost and retail price
- Variants (size, color, tier) with pricing modifiers
- Apparel tier variants: Economy (+$0), Standard (+$5), Premium (+$12)
- Quick-add buttons for apparel/decal size variants
- AI Product Description Generator
- Create product directly from store's Products tab
- Enable/disable products per store with price overrides

**Order Management:**
- Order list with filters and statuses (Pending, Processing, Ready, Shipped, Delivered, Cancelled)
- Auto-create job from order (status: approved)
- Auto-create customer if doesn't exist
- Order linked to job via job_id

**Fundraiser Features:** Goal amount, start/end dates, progress tracking, profit percentage
**Creator Features:** Commission type (% or flat), payout tracking

**Public Storefront:**
- Product browsing with image carousel
- Variant selection dropdown
- Add to cart and checkout flow
- Stripe Connect integration for real payments
- Fallback to pending status if Stripe not connected

**Data:** `webstores_v2`, `products`, `webstore_products`, `webstore_orders_v2`, `webstore_payouts`

**Status:** WORKING (requires Stripe Connect for payments)

---

## 20. COMPANY SETTINGS

**Where it lives:** `/settings`

**Sub-features:**
- Company name, address, contact info
- Logo upload
- Website URL
- Time tracking settings (per job, per line item, employee portal, kiosk mode, auto-suggest)
- Data Management section (link to Backup)

**Status:** WORKING

---

## 21. EMAIL TEMPLATES

**Where it lives:** `/settings/email-templates`

**Sub-features:**
- Template types: Quote sent, Invoice sent, Proof approval, Order confirmation, Job status update, Payment received
- Variable placeholders
- Preview and HTML/text editing

**Status:** WORKING

---

## 22. PAYMENT SETTINGS (STRIPE CONNECT)

**Where it lives:** `/admin/payments`

**Sub-features:**
- Stripe Connect setup with OAuth flow
- Account connection status
- Platform fees by tier: Starter 3%, Growth 2%, Pro 1%
- Invoice "Pay Link" button (creates Stripe checkout)
- Webstore checkout processing
- Payment history

**API:** `/api/stripe-connect/status`, `/api/stripe-connect/create-account`, `/api/stripe-connect/invoice/{id}/pay`, `/api/stripe-connect/webstore/{id}/checkout`

**Status:** WORKING

---

## 23. PROMO CODES

**Where it lives:** `/promo-codes`

**Who can access it:** Founder accounts only

**Sub-features:**
- Code creation with discount type (%, $, free trial)
- Usage limits and expiration dates
- Track usage count
- Active/inactive status

**Data:** `promo_codes`, `promo_code_usage`

**Status:** WORKING

---

## 24. CUSTOMER PORTAL

**Where it lives:** `/customer-portal/*`

**Who can access it:** Customers with portal access enabled

**Pages & Features:**

| Page | Route | Features |
|------|-------|----------|
| Login | `/customer-portal/login` | Email/password, magic link |
| Dashboard | `/customer-portal` | Overview, stats, pending approvals |
| Orders | `/customer-portal/orders` | Order list and detail view |
| Quotes | `/customer-portal/quotes` | Quote list |
| Invoices | `/customer-portal/invoices` | Invoice list and payment status |
| Documents | `/customer-portal/documents` | View shared documents with "New" badge |
| Messages | `/customer-portal/messages` | Conversations with file attachments |
| Proofs | `/customer-portal/proofs` | Artwork proof approval/revision |
| Appointments | `/customer-portal/appointments` | Scheduling (5 types, 6 statuses) |
| Profile | `/customer-portal/profile` | Contact info, notification preferences |

**Data:** `customers`, `conversations`, `conversation_messages`, `artwork_proofs`, `customer_notifications`, `portal_documents`, `magic_links`

**Status:** WORKING

---

## 25. EMPLOYEE PORTAL

**Where it lives:** `/employee-portal/*`

**Who can access it:** Employees with PIN access

**Pages & Features:**

| Page | Route | Features |
|------|-------|----------|
| Login | `/employee-portal/login` | Email + PIN authentication |
| Dashboard | `/employee-portal` | Clock status, today's hours, week summary |
| Pay | `/employee-portal/pay` | Earnings, YTD, payment history, balance |
| Tasks | `/employee-portal/tasks` | Assigned tasks, mark complete |
| Profile | `/employee-portal/profile` | Profile image upload, clock history, PIN |

**Configurable permissions per tenant:** Tasks, Schedule, Pay Stubs, Time Clock, Edit Profile, Job Details, Customer Info, Pricing

**Status:** WORKING

---

## 26. BILLING & SUBSCRIPTIONS

**Where it lives:** `/billing`, `/pricing-plans`, `/pricing`

**Multi-Product Structure (3 Product Lines, 9 Plans):**

**SignGuy AI OS (Shop Management):**
| Plan | Monthly | Founder | Invoice Fee | Webstore Fee |
|------|---------|---------|-------------|--------------|
| Starter | $39 | $29 | 0% | 0% |
| Pro | $79 | $59 | 1% | 3% |
| Business | $149 | $99 | 1% | 2% |

**SignGuy Webstores (Commerce-Only):**
| Plan | Monthly | Webstore Fee |
|------|---------|--------------|
| Launch | $39 | 3% |
| Growth | $59 | 2.5% |
| Scale | $99 | 2% |

**SignGuy AI Studio (AI-Only):**
| Plan | Monthly |
|------|---------|
| Basic | $29 |
| Pro | $59 |
| Max | $99 |

**Founders Edition:** $99/mo, all features, 150 AI credits/month, limited to 100 customers, lifetime lock

**Features:**
- Stripe Checkout (subscription + one-time)
- 14 Stripe Price IDs configured
- Annual billing for OS Business plan
- Webhook handling for subscription lifecycle
- Trial system with $19.99 extended trial (credits toward Business)
- Billing Management page with plan info, fees, upgrade options
- Product line preview mode (view app as different customer types)

**Data:** `subscriptions`, `payment_transactions`, `user_credits`, `credit_transactions`

**Status:** WORKING

---

## 27. AI CREDIT SYSTEM

**Where it lives:** Header bar (CreditBalance component), `/billing`

**Monthly Allowance:** 150 credits (Founders Edition), reset on billing cycle

**Credit Costs:**
- 1 credit: text generation, email reply, product description, simple assistant queries
- 2 credits: blog creator, SEO content, proposals, pricing advisor
- 3 credits: image generation, mockups, vehicle wrap mockups, branding kit

**Credit Packs (via Stripe):**
- 100 credits: $10 ($0.10/credit)
- 300 credits: $25 ($0.083/credit) - 17% savings
- 1000 credits: $60 ($0.06/credit) - 40% savings

**Features:**
- Credit balance display in header with coin icon
- Low credits warning at < 10 credits
- Purchase modal with pack options
- Monthly credits consumed first, then purchased

**API:** `/api/credits/balance`, `/api/credits/use`, `/api/credits/packs`, `/api/credits/purchase`, `/api/credits/history`, `/api/credits/costs`

**Status:** WORKING

---

## 28. COMMUNITY HUB

**Where it lives:** `/community`

**Sub-features:**
- Message board for bug reports, feature requests, questions, feedback
- Category system: Bug Report, Feature Request, Question, Feedback
- Upvote system for prioritizing posts
- Owner replies with "Official" badge
- Pin posts, change status (Open, In Progress, Resolved, Closed)
- Owner replies auto-mark posts as "Answered"
- Search across titles, descriptions, and replies
- Filter by category and status
- Direct "Contact Support" email link

**Data:** `community_posts`, `community_replies`

**API:** `/api/community/posts` (CRUD), `/api/community/stats`, `/api/community/replies/{post_id}`

**Status:** WORKING

---

## 29. TENANT DATA BACKUP & RESTORE

**Where it lives:** `/settings/backup`

**Who can access it:** Owner only

**Sub-features:**
- Download all tenant data as JSON (images excluded for size)
- Restore with preview summary and confirmation dialog
- Weekly backup reminder banner (dismissable per session)
- Collections backed up: users, employees, customers, jobs, job_items, invoices, products, webstores_v2, tasks, documents, questionnaires, and more

**API:** `/api/backup/export`, `/api/backup/status`, `/api/backup/preview-restore`, `/api/backup/restore`

**Status:** WORKING

---

## 30. ADMIN PORTAL (COMMUNICATIONS HUB)

**Where it lives:** `/admin-portal`

**Sub-features:**
- Centralized customer communication management
- View all conversations across customers
- Reply to customer messages
- Message status tracking

**Status:** WORKING

---

## 31. TASKS

**Where it lives:** Integrated in Jobs and Employee Portal

**Sub-features:**
- Task creation linked to jobs
- Assign to employee
- Due date tracking
- Completion tracking
- Kanban cards clickable to navigate to job

**Data:** `tasks`

**API:** `/api/tasks` (CRUD)

**Status:** WORKING

---

## 32. PRODUCTION TIMELINE

**Where it lives:** Job Detail page (Timeline tab)

**Sub-features:**
- Visual status flow: Quote -> Approved -> In Progress -> Completed -> Invoiced
- Green checkmarks for completed stages
- Highlighted current stage
- Status change history with timestamps
- Time spent in each previous status

**Status:** WORKING

---

## 33. CUSTOMIZABLE QUICK TOOLBAR

**Where it lives:** Integrated in MainLayout (desktop only)

**Sub-features:**
- Horizontal quick-access toolbar at top
- 18 available shortcuts (Dashboard, Customers, Quotes, Jobs, Invoices, Time Clock, Payroll, Productivity, Financials, AI Tools, AI Assistant, Webstores, Products, Documents, Approvals, Calculator, Users, Settings)
- Customizable: click gear icon to select up to 10 shortcuts
- Size options: Small, Medium, Large icons
- Persistent preferences in localStorage

**Status:** WORKING (currently hidden by ribbon navigation)

---

## 34. OFFICE-STYLE RIBBON NAVIGATION

**Where it lives:** App-wide (MainLayout)

**Sub-features:**
- **Top App Bar (Row 1):** Logo (home link), Search, AI Credits balance, Notifications, Help (docs), Profile dropdown (Account, Settings, Sign Out)
- **Primary Nav (Row 2):** 11 tabs - Dashboard, Jobs, Billing, Customers, Webstores, Documents, Team, AI Tools, Reports, Community, Settings
- **Action Toolbar (Row 3):** Context-sensitive sub-navigation per active tab + quick action buttons
- **Tab Sub-Items:**
  - Jobs: All Jobs, Quotes, Approvals, Production
  - Billing: Invoices, Payments, Pricing, Billing
  - Customers: All Customers, Admin Portal
  - Webstores: Stores, Products, Promo Codes
  - Documents: Document Library, Questionnaires
  - Team: Payroll, Time Clock, Users
  - AI Tools: AI Tools, AI Assistant
  - Reports: Financials, Productivity
  - Community: Community Hub, Documentation, Contact Support
  - Settings: Company, Email Templates, Production, Backup, Users
- **Mobile:** Hamburger menu with overlay navigation
- Route-to-tab mapping for automatic tab highlighting

**Files:** `/app/frontend/src/components/ribbon/` (TopAppBar.js, PrimaryNav.js, ActionToolbar.js, Ribbon.js, RibbonToolbar.js, DropdownMenu.js, MobileRibbonOverlay.js, MobileNav.js)

**Status:** WORKING

---

## 35. MARKETING WEBSITE

**Where it lives:** `/`, `/home`, `/features`, `/pricing`, `/about`, `/contact`, `/docs`

**Pages:**

| Page | Route | Purpose |
|------|-------|---------|
| Landing Page | `/`, `/home` | Hero, features, AI tools showcase, pricing, FAQ |
| Features | `/features` | Detailed feature descriptions |
| Founders Edition Pricing | `/pricing`, `/founders` | Current pricing with credit details, billing rules, FAQ |
| Legacy Pricing | `/pricing-legacy` | Old pricing page |
| Why Founder | `/why-founder` | Founder benefits page |
| About | `/about` | Company story |
| Contact | `/contact` | Contact form |
| Platform Overview | `/platform` | SignGuy AI OS overview |
| Webstores Overview | `/webstores-overview` | SignGuy Webstores overview |
| AI Studio Overview | `/ai-studio` | SignGuy AI Studio overview |
| Plan Detail Pages | `/starter`, `/pro`, `/business` | OS plan details |
| Webstore Plan Pages | `/webstore-launch`, `/webstore-growth`, `/webstore-scale` | Webstore plan details |
| AI Studio Plan Pages | `/ai-basic`, `/ai-pro`, `/ai-max` | AI Studio plan details |
| Multi-Product Pricing | `/pricing-plans` | Tabbed pricing for all 3 product lines |

**Pricing Page Content (8 Sections):**
- Founder Launch Offer banner
- How AI Credits Work block
- Billing & Payments section
- AI Usage Transparency with example UI
- Fair Usage Protection notice
- FAQ questions

**Status:** WORKING

---

## 36. DOCUMENTATION & HELP CENTER

**Where it lives:** `/docs/*`

**Pages:**
- Overview, Getting Started (5-step walkthrough)
- Feature docs: Customers, Quotes & Jobs, Invoicing, Pricing Calculator
- Advanced docs: AI Tools Suite, Time Tracking, Employee Management
- Webstores, Customer Portal, Financials, Productivity
- FAQ section with collapsible questions
- Mobile hamburger menu with slide-out sidebar

**Status:** WORKING

---

## 37. SECURITY & TENANT ISOLATION

**Completed audit results:**
- 28 security tests across 11 API domains, 100% pass rate
- All APIs verified: Customers, Employees, Jobs, Tasks, Job Items, Quotes, Invoices, Webstores, Products, Dashboard, Payroll
- Cross-tenant access blocked for LIST, GET, UPDATE, DELETE operations
- Authentication required on all endpoints

**Status:** VERIFIED

---

# B) NAVIGATION MAP

## Ribbon Navigation (Primary)

| Tab | Sub-Items | Routes |
|-----|-----------|--------|
| Dashboard | - | `/dashboard` |
| Jobs | All Jobs, Quotes, Approvals, Production | `/jobs`, `/jobs?filter=quotes`, `/approvals`, `/settings/production` |
| Billing | Invoices, Payments, Pricing, Billing | `/invoices`, `/admin/payments`, `/pricing-calculator`, `/billing` |
| Customers | All Customers, Admin Portal | `/customers`, `/admin-portal` |
| Webstores | Stores, Products, Promo Codes | `/webstores`, `/products`, `/promo-codes` |
| Documents | Document Library, Questionnaires | `/documents`, `/questionnaires` |
| Team | Payroll, Time Clock, Users | `/payroll`, `/timeclock`, `/users` |
| AI Tools | AI Tools, AI Assistant | `/ai-tools`, `/ai-assistant` |
| Reports | Financials, Productivity | `/financials`, `/productivity` |
| Community | Community Hub, Documentation, Contact Support | `/community`, `/docs` |
| Settings | Company, Email Templates, Production, Backup, Users | `/settings`, `/settings/email-templates`, `/settings/production`, `/settings/backup`, `/users` |

## Portal Pages

| Portal | Pages |
|--------|-------|
| Customer Portal | Login, Dashboard, Orders, Quotes, Invoices, Documents, Messages, Proofs, Appointments, Profile |
| Employee Portal | Login, Dashboard, Pay, Tasks, Profile |

## Public Pages

Landing, Features, Pricing, About, Contact, Docs, Storefronts, Questionnaires, Plan Details (12 routes)

---

# C) DATA/BACKEND INVENTORY

## MongoDB Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `tenants` | Multi-tenant orgs | id, name, slug, owner_email, plan, is_active, time_tracking_settings |
| `users` | Authenticated users | id, tenant_id, email, full_name, role, is_founder, hashed_password |
| `customers` | Customer records | id, tenant_id, name, email, phone, status, portal_enabled |
| `jobs` | Work orders (quotes + jobs) | id, tenant_id, customer_id, name, status, subtotal |
| `job_items` | Line items on jobs | id, job_id, item_type, quantity, unit_price, status |
| `job_notes` | Notes on jobs | id, job_id, content, created_by |
| `job_activities` | Activity log | id, job_id, activity_type, description |
| `job_time_entries` | Time tracked on jobs | id, job_id, employee_id, start_time, end_time, duration_minutes, labor_cost |
| `invoices` | Customer invoices | id, tenant_id, customer_id, job_id, invoice_number, status, total |
| `employees` | Employee records | id, tenant_id, name, email, hourly_rate, pin, profile_image |
| `timelogs` | Clock in/out records | id, employee_id, action, timestamp |
| `payroll_transactions` | Pay records | id, employee_id, type (earnings/advance/payment), amount, date |
| `payroll_hours` | Manual hours entries | id, tenant_id, employee_id, date, hours, job_id, task_type, gross_pay |
| `products` | Product catalog | id, tenant_id, name, category, base_cost, retail_price, images, variants |
| `webstores_v2` | Online stores | id, tenant_id, name, store_type, status, branding |
| `webstore_products` | Product assignments | id, webstore_id, product_id, is_enabled, price_override |
| `webstore_orders_v2` | Store orders | id, webstore_id, customer_name, items, subtotal, job_id |
| `webstore_payouts` | Payout records | id, webstore_id, amount, date |
| `conversations` | Message threads | id, tenant_id, customer_id |
| `conversation_messages` | Individual messages | id, conversation_id, sender_type, content, type |
| `artwork_proofs` | Proof files | id, tenant_id, job_id, customer_id, image_url, status |
| `customer_notifications` | Portal notifications | id, customer_id, type, message, read |
| `documents` | File storage | id, tenant_id, name, file_url, file_type, category |
| `portal_documents` | Shared docs | id, tenant_id, customer_id, document_id |
| `document_activities` | Doc activity log | id, document_id, action, user_id |
| `tasks` | Employee tasks | id, tenant_id, job_id, assigned_to, title, is_complete |
| `questionnaires` | Form templates | id, tenant_id, title, questions, is_default |
| `questionnaire_responses` | Form submissions | id, questionnaire_id, customer_id, responses |
| `subscriptions` | SaaS subscriptions | id, tenant_id, plan, status, stripe_subscription_id |
| `payment_transactions` | Payment records | id, tenant_id, stripe_session_id, amount, status |
| `user_credits` | AI credit balances | id, tenant_id, monthly_credits, purchased_credits |
| `credit_transactions` | Credit audit log | id, tenant_id, type, amount, description |
| `promo_codes` | Discount codes | id, code, discount_type, discount_value, is_active |
| `promo_code_usage` | Code usage tracking | id, tenant_id, promo_code_id |
| `community_posts` | Forum posts | id, tenant_id, user_id, title, content, category, status, upvotes |
| `community_replies` | Forum replies | id, post_id, tenant_id, user_id, content, is_official |
| `pricing_defaults` | Pricing config | id, tenant_id, category, defaults |
| `pricing_templates` | Saved templates | id, tenant_id, name, configuration |
| `ai_history` | AI tool usage | id, tenant_id, tool, input_data, output, images |
| `ai_responses` | AI responses | id, tenant_id, tool, content |
| `ai_usage_logs` | AI usage tracking | id, tenant_id, usage_type, count |
| `expense_entries` | Expense records | id, tenant_id, category, amount, date |
| `sales_entries` | Sales records | id, tenant_id, amount, date |
| `magic_links` | Passwordless auth | id, customer_id, token, expires_at |

## Status Enums

- **JobStatus:** quote, approved, in_progress, completed, invoiced, archived
- **JobItemStatus:** pending, in_production, done
- **InvoiceStatus:** draft, sent, paid, overdue
- **CustomerStatus:** lead, active, inactive
- **WebstoreType:** b2b, fundraiser, creator
- **WebstoreStatus:** active, paused, completed, archived
- **OrderStatus:** pending, processing, ready, shipped, delivered, cancelled
- **ProofStatus:** pending, approved, revision_requested, rejected
- **UserRole:** owner, admin, staff
- **TenantPlan:** starter, pro, business
- **PayrollTransactionType:** earnings, advance, payment
- **CommunityPostCategory:** bug_report, feature_request, question, feedback
- **CommunityPostStatus:** open, in_progress, resolved, closed

---

# D) INTEGRATIONS INVENTORY

## Stripe
- SaaS subscriptions (14 Price IDs for 9 plans)
- Stripe Connect for webstore payments (platform fees by tier)
- Webhooks: checkout.session.completed, subscription lifecycle, invoice events
- Credit pack purchases

## OpenAI (via Emergent LLM Key)
- GPT-5.2 for text generation (28+ AI tools)
- GPT Image 1 for image generation
- Via `emergentintegrations` library

## SendGrid
- Transactional emails (quotes, invoices, proofs, orders, portal notifications)
- Contact form submissions

## reportlab
- PDF generation (invoices, quotes, AI documents)

## qrcode.react
- QR code generation for webstore URLs

---

# E) NOT YET IMPLEMENTED / FUTURE

1. Custom Domain Support for webstores
2. SMS Notifications (Twilio)
3. QuickBooks Integration
4. BNPL (Affirm/Klarna)
5. Vehicle Wrap AI Tool (full spec beyond current calculator)
6. Master Product List (centralized across tenants)
7. Kanban Job Board (visual pipeline)
8. Calendar View for jobs/appointments
9. Scheduled Reports (auto-generated email reports)
10. Advanced Analytics (trend analysis, forecasting)
11. Zapier Integration
12. Calculated Shipping rates
13. Low Stock Alerts (inventory)
14. Abandoned Cart Emails
15. Marketing Email Campaigns (bulk)
16. Custom User Roles (beyond owner/admin/staff)
17. Efficiency Dashboard for employees
18. RaceWrap AI Tool (P2)
19. Mobile responsiveness optimization (P1)

---

# F) MASTER FEATURE HIERARCHY

```
SignGuy AI
|
+-- Authentication & Access
|   +-- User Registration/Login/Logout
|   +-- Multi-Tenant Isolation
|   +-- Role Management (Owner/Admin/Staff)
|   +-- Permission System (23 permissions)
|   +-- Founder Account Features
|
+-- Dashboard
|   +-- Revenue Summary & Stat Cards
|   +-- Today's Schedule, Messages, Approvals
|   +-- Quick Actions & Onboarding Checklist
|   +-- Recent AI Documents Widget
|
+-- Sales
|   +-- Customers (CRM with CSV import, portal toggle)
|   +-- Jobs (Unified quotes/jobs pipeline)
|   +-- Invoices (PDF, email, Stripe payments)
|
+-- Operations
|   +-- Time Clock (clock in/out, breaks, per-job tracking)
|   +-- Admin Payroll (4 tabs: Overview, Time Sheets, Manual Hours, Transactions)
|   +-- Productivity Tracking
|   +-- Financials (Revenue, Expenses, Profit)
|
+-- Webstores
|   +-- Store Management (B2B, Fundraiser, Creator)
|   +-- Product Catalog (images, variants, AI descriptions)
|   +-- Orders (auto-create jobs)
|   +-- Public Storefront (checkout, Stripe Connect)
|   +-- QR Codes & Promo Codes
|
+-- Tools
|   +-- AI Tools Suite (28+ tools, 4 categories + Racing)
|   +-- AI Business Assistant (context-aware chat)
|   +-- AI Pricing Advisor
|   +-- AI Email Composer
|   +-- Artwork Approvals (watermarking, portal integration)
|   +-- Document Library (send as PDF/Portal/Form)
|   +-- Questionnaires & Forms
|   +-- Pricing Calculator (8 categories, templates)
|
+-- Team
|   +-- Employee Management (profiles, rates, PINs)
|   +-- Task Assignment & Tracking
|
+-- Admin
|   +-- Company Settings
|   +-- Email Templates
|   +-- Payment Settings (Stripe Connect)
|   +-- Production Settings
|   +-- Data Backup & Restore
|   +-- Promo Codes (Founder only)
|
+-- Community
|   +-- Community Hub (bug reports, feature requests, Q&A)
|   +-- Documentation & Help Center
|
+-- Billing
|   +-- Multi-Product Plans (OS, Webstores, AI Studio)
|   +-- Founders Edition ($99/mo, 150 credits)
|   +-- AI Credit System (purchase packs, usage tracking)
|   +-- Stripe Subscriptions & Webhooks
|
+-- Portals
|   +-- Customer Portal (orders, invoices, messages, proofs, docs, appointments)
|   +-- Employee Portal (clock, pay, tasks, profile)
|
+-- Marketing Website
|   +-- Landing Page, Features, Pricing, About, Contact
|   +-- Product Line Overview Pages (OS, Webstores, AI Studio)
|   +-- Plan Detail Pages (9 plans)
|   +-- Documentation Site
|
+-- Navigation
|   +-- Office-Style Ribbon (11 tabs, contextual toolbars)
|   +-- Mobile Hamburger Menu
|   +-- Customizable Quick Toolbar
```

---

# G) FEATURE-TO-TIER READINESS

| Module | Tierable | Typical Tier Lever |
|--------|----------|-------------------|
| Authentication | Yes | Team member limits (1/5/unlimited) |
| Dashboard | Yes | Analytics depth |
| Customers | Yes | Customer count limits |
| Jobs | Yes | Active job limits, kanban, activity log |
| Invoices | Yes | Invoice count, payment integrations |
| Time Clock | Yes | Feature on/off (Starter locked) |
| Payroll | Yes | Feature on/off (Starter locked) |
| Productivity | Yes | Report depth, export |
| Financials | Yes | Feature on/off (Starter locked) |
| Webstores | Yes | Store count (1/5/unlimited), store types |
| Products | Yes | Product count, image limits |
| AI Tools | Yes | Monthly limits (25/100/unlimited), image gen |
| AI Assistant | Yes | Query limits, query complexity |
| Approvals | Yes | Storage limits |
| Documents | Yes | Storage limits (100MB/1GB/5GB) |
| Questionnaires | Yes | Form limits, response tracking |
| Pricing Calculator | Yes | Template limits, AI suggestions |
| Customer Portal | Yes | Messaging, appointments on/off |
| Employee Portal | Yes | Feature on/off (tenant setting) |
| Email Templates | Yes | Customization depth |
| Company Settings | No | All tiers |
| Payment Settings | Yes | Payment provider options |
| Promo Codes | No | Founder only |
| Community Hub | No | All tiers |
| Backup/Restore | Yes | Frequency, auto-backup |
| Credit System | Yes | Monthly allowance (25/100/150) |

---

# H) QUALITY CHECK

| Question | Answer |
|----------|--------|
| Every page listed? | Yes - 50+ pages/routes |
| Every database collection? | Yes - 42+ collections |
| Every role and permission? | Yes - 3 roles, 23 permissions |
| Implemented vs not implemented separated? | Yes - Section E |
| Sub-features for every module? | Yes |
| New features since Dec 2025 included? | Yes - Community Hub, Backup, Payroll Enhancement, Document Library, Credit System, Ribbon Nav, Racing Tools, Questionnaires |
| All AI tools listed? | Yes - 28+ tools across 5 categories |
| All integrations documented? | Yes - Stripe, OpenAI, SendGrid, reportlab, qrcode.react |

---

*Document generated from comprehensive codebase audit. Last updated: March 14, 2026.*
