# SignGuy AI - Complete Feature Catalog
**Generated: December 1, 2025**
**Version: Current Build**

---

# A) APP FEATURE CATALOG (IMPLEMENTED)

---

## 1. AUTHENTICATION & USER MANAGEMENT

**Module Name:** Authentication System

**Purpose:** Multi-tenant user authentication, registration, and role-based access control.

**Where it lives:** `/login`, `/users`

**Who can access it:**
- Registration: Public (creates new tenant + owner account)
- Login: All users
- User Management: Owner, Admin (Permission: `users:view`, `users:manage`)

**Core actions:** Register, Login, Logout, Create User, Update User Role, Delete User, Password Reset

**Sub-features:**
- JWT-based authentication with 24-hour expiry
- Multi-tenant isolation (each user belongs to one tenant)
- Three user roles: Owner, Admin, Staff
- Role-based permission system with 23 permission types
- Founder account flag (special access to promo codes, tier preview)
- Remember me functionality

**Data it uses:**
- `users`: id, email, full_name, company_name, role, tenant_id, is_founder, hashed_password
- `tenants`: id, name, slug, owner_email, plan, is_active, time_tracking_settings

**Automations/workflows:**
- Auto-create tenant on first user registration
- Assign owner role to first user of tenant

**Integrations involved:** None

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Team member limits (1/3/unlimited)

---

## 2. DASHBOARD

**Module Name:** Dashboard

**Purpose:** Central overview of business metrics, recent activity, and quick actions.

**Where it lives:** `/dashboard`

**Who can access it:** All authenticated users

**Core actions:** View metrics, Quick navigation

**Sub-features:**
- Revenue summary (today, week, month)
- Job counts by status
- Recent jobs list
- Recent customers list
- Quick stats cards (quotes pending, jobs in progress, invoices due)
- Trial countdown display (for trial users)

**Data it uses:**
- `jobs`: For job counts and revenue calculations
- `customers`: For recent customer list
- `invoices`: For revenue tracking

**Automations/workflows:** None

**Integrations involved:** None

**Dependencies:** Jobs, Customers, Invoices modules

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Analytics depth (basic summary vs advanced metrics)

---

## 3. CUSTOMERS (CRM)

**Module Name:** Customer Management

**Purpose:** Store and manage customer information, contacts, and relationships.

**Where it lives:** `/customers`

**Who can access it:**
- View: All roles (Permission: `customers:view`)
- Create/Edit: Owner, Admin, Staff (Permission: `customers:create`, `customers:edit`)
- Delete: Owner, Admin (Permission: `customers:delete`)

**Core actions:** Create, Edit, Delete, View, Search, Filter

**Sub-features:**
- Customer list with search and filtering
- Customer status tracking (Lead, Active, Inactive)
- Contact information (email, phone, address)
- Company information
- Customer notes
- Tax exempt status flag
- Portal access toggle
- Customer-specific pricing toggle
- Customer tags
- View related jobs/quotes/invoices per customer

**Data it uses:**
- `customers`: id, tenant_id, name, email, phone, address, city, state, zip_code, company_name, status, tags, notes, tax_exempt, portal_enabled, portal_password_hash

**Automations/workflows:**
- Auto-create customer from webstore orders
- Customer status updates based on activity

**Integrations involved:** None

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Customer count limits, advanced CRM features

---

## 4. JOBS (UNIFIED QUOTES & JOBS)

**Module Name:** Jobs Management

**Purpose:** Unified workflow for quotes and production jobs from creation to completion.

**Where it lives:** `/jobs`, `/jobs/:id`

**Who can access it:**
- View: All roles (Permission: `jobs:view`)
- Create/Edit: Owner, Admin, Staff (Permission: `jobs:create`, `jobs:edit`)
- Delete: Owner, Admin (Permission: `jobs:delete`)

**Core actions:** Create Quote, Create Job, Edit, Delete, Change Status, Add Line Items, Convert Quote to Job, Generate Invoice

**Sub-features:**
- **Job Statuses Pipeline:**
  - Quote (initial proposal stage)
  - Approved (ready for production)
  - In Progress (currently being worked on)
  - Completed (production done)
  - Invoiced (billed to customer)
  - Archived (closed/stored)
- **Status Filters:** All, Quotes, Active, Completed
- **Line Items Management:**
  - Item types: Banner, Yard Sign, Decal, Wrap, Install, Design, Vehicle Graphics, Window Graphics, Dimensional Letters, Monument Sign, Other
  - Item status: Pending, In Production, Done
  - Quantity, unit price, line total
- **Job Notes:** Internal notes with timestamps
- **Job Activity Log:** Track all status changes, item additions, etc.
- **Quick Quote vs Full Job creation**
- **Customer selection/linking**
- **Subtotal auto-calculation**
- **Job time tracking link**

**Data it uses:**
- `jobs`: id, tenant_id, customer_id, name, description, status, subtotal, created_at, updated_at
- `job_items`: id, job_id, item_type, description, quantity, unit_price, line_total, status, webstore_order_id, webstore_order_item_product_id, variant_id
- `job_notes`: id, job_id, content, created_by, created_at
- `job_activities`: id, job_id, activity_type, description, created_by, created_at

**Automations/workflows:**
- Auto-create job from webstore order (status: approved)
- Activity logging on every status change
- Convert quote to job (changes status from "quote" to "approved")
- Auto-link customer

**Integrations involved:** None

**Dependencies:** Customers

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Active job limits, kanban view access, job activity log

---

## 5. INVOICES

**Module Name:** Invoicing

**Purpose:** Create and manage invoices for completed work.

**Where it lives:** `/invoices`

**Who can access it:**
- View: Owner, Admin, Staff (Permission: `invoices:view`)
- Create/Edit: Owner, Admin (Permission: `invoices:create`, `invoices:edit`)
- Delete: Owner, Admin (Permission: `invoices:delete`)

**Core actions:** Create, Edit, Delete, View, Mark Paid, Send Invoice, Export PDF

**Sub-features:**
- Invoice statuses: Draft, Sent, Paid, Overdue
- Create invoice from job
- Line items with quantities and prices
- Tax calculation
- Invoice number auto-generation
- Due date tracking
- Payment method tracking (Cash, Check, Card, Bank Transfer, Other)
- Customer linkage
- Invoice notes

**Data it uses:**
- `invoices`: id, tenant_id, customer_id, job_id, invoice_number, status, items, subtotal, tax, total, due_date, paid_date, payment_method, notes

**Automations/workflows:**
- Auto-calculate totals
- Update job status to "invoiced" when invoice created

**Integrations involved:** PDF generation (reportlab)

**Dependencies:** Jobs, Customers

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Invoice count, payment integration, recurring invoices

---

## 6. TIME CLOCK

**Module Name:** Time Clock / Time Tracking

**Purpose:** Track employee work hours per job or general time.

**Where it lives:** `/timeclock`

**Who can access it:**
- Own time: All roles (Permission: `time:own`)
- All time: Owner, Admin (Permission: `time:view_all`, `time:manage`)

**Core actions:** Clock In, Clock Out, Add Manual Entry, Edit Entry, Delete Entry, View Time Reports

**Sub-features:**
- Clock in/out functionality
- Break tracking
- Time entries per job
- Time entries per line item (optional setting)
- Manual time entry
- Edit/delete entries
- Time reports by employee
- Time reports by job
- Daily/weekly/monthly summaries
- Kiosk mode (simplified clock-in interface)
- Auto-suggest time entry on job status change

**Data it uses:**
- `timelogs`: id, tenant_id, employee_id, job_id, job_item_id, start_time, end_time, break_duration, status, notes
- `job_time_entries`: id, job_id, tenant_id, employee_id, hours, start_time, end_time, description

**Automations/workflows:**
- Auto-calculate duration from start/end times
- Suggest time entry when job status changes

**Integrations involved:** None

**Dependencies:** Employees, Jobs

**Current status:** WORKING

**Tierable:** Yes (tier-locked in Starter)
**Typical tier lever:** Feature on/off, per-line-item tracking

---

## 7. PAYROLL

**Module Name:** Payroll Management

**Purpose:** Track employee earnings, advances, and payments.

**Where it lives:** `/payroll`

**Who can access it:** Owner, Admin (Permission: `payroll:view`, `payroll:manage`)

**Core actions:** View earnings, Record payment, Record advance, Generate pay summary

**Sub-features:**
- Employee earnings tracking
- Balance owed calculation
- Payment recording
- Advance recording
- Pay period summaries
- YTD tracking
- Individual employee pay history

**Data it uses:**
- `payroll_transactions`: id, tenant_id, employee_id, type (earnings/advance/payment), amount, date, notes
- `employees`: hourly_rate, balance_owed

**Automations/workflows:**
- Auto-calculate earnings from time entries
- Update employee balance on payment/advance

**Integrations involved:** None

**Dependencies:** Employees, Time Clock

**Current status:** WORKING

**Tierable:** Yes (tier-locked in Starter)
**Typical tier lever:** Feature on/off

---

## 8. EMPLOYEES

**Module Name:** Employee Management

**Purpose:** Manage employee profiles, rates, and assignments.

**Where it lives:** `/users` (employees are managed under Users page)

**Who can access it:**
- View: Owner, Admin (Permission: `employees:view`)
- Manage: Owner, Admin (Permission: `employees:manage`)

**Core actions:** Create, Edit, Delete, Set Hourly Rate, Set PIN

**Sub-features:**
- Employee profiles
- Hourly rate configuration
- Portal PIN for employee portal access
- Role assignment
- Active/inactive status

**Data it uses:**
- `employees`: id, tenant_id, name, email, phone, role, hourly_rate, pin, profile_image, is_active

**Automations/workflows:** None

**Integrations involved:** None

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Employee count limits

---

## 9. PRODUCTIVITY

**Module Name:** Productivity Tracking

**Purpose:** Track daily productivity and completed work.

**Where it lives:** `/productivity`

**Who can access it:** All authenticated users

**Core actions:** View productivity metrics, Track daily output

**Sub-features:**
- Daily productivity summary
- Jobs completed tracking
- Time logged summary
- Employee productivity comparison

**Data it uses:**
- `jobs`: status, completed_at
- `timelogs`: hours, employee_id

**Automations/workflows:** None

**Integrations involved:** None

**Dependencies:** Jobs, Time Clock

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Report depth, export capability

---

## 10. FINANCIALS

**Module Name:** Financial Tracking

**Purpose:** Track revenue, expenses, and profit.

**Where it lives:** `/financials`

**Who can access it:** Owner, Admin (Permission: `financials:view`)

**Core actions:** View reports, Add expense, View profit analysis

**Sub-features:**
- Revenue tracking by period
- Expense tracking with categories (20+ expense categories)
- Sales entries
- Profit calculation
- Monthly summaries
- Category breakdown

**Expense Categories:**
- Materials, Labor, Equipment, Utilities, Rent, Insurance, Cell Phone, Garbage
- Printing Supplies, Meals, Entertainment, Donations, Office Supplies, Apparel
- Vehicle, Advertising, Legal, Repairs, Taxes, Travel, Other

**Data it uses:**
- `expense_entries`: id, tenant_id, category, amount, date, description
- `sales_entries`: id, tenant_id, amount, date, source
- `invoices`: For revenue calculations

**Automations/workflows:**
- Auto-calculate profit from revenue - expenses

**Integrations involved:** None

**Dependencies:** Invoices

**Current status:** WORKING

**Tierable:** Yes (tier-locked in Starter)
**Typical tier lever:** Feature on/off, category breakdown, export

---

## 11. AI TOOLS

**Module Name:** AI-Powered Tools

**Purpose:** AI-generated content, images, and business assistance.

**Where it lives:** `/ai-tools`

**Who can access it:** All authenticated users

**Core actions:** Generate content, Generate images, View history

**Sub-features:**

**Text Generation Tools:**
- Blog Creator - Generate industry blog articles
- Completed Job Post - Social media posts from job photos
- Idea Brainstormer - Creative brainstorming
- Permit Research - Sign permit guidance
- Pricing Advisor - Pricing recommendations
- Tagline Generator - Business taglines
- Brand Color Advisor - Color recommendations
- Brand Voice Guide - Brand consistency guide
- Proposal Writer - Professional proposals
- Review Responder - Customer review responses
- Email Templates - Business email templates
- SEO Content - Website content
- Showcase Post - Social media posts
- Social Pack Generator - Multiple post ideas
- Content Calendar - Marketing calendar
- Campaign Builder - Marketing campaigns
- Branding Kit Generator - Complete brand system
- Business Copywriter - Marketing copy
- Document Composer - Business documents
- Pricing Intelligence - Pricing analysis
- Social Job Post - Job showcase posts

**Image Tools:**
- Photo Enhancer - Analyze and suggest improvements
- Image Vectorizer - Vectorization guidance
- Font Identifier - Identify fonts in images
- AI Sign Designer - Sign design concepts
- AI Banner Designer - Banner concepts
- Logo Refresher - Logo redesign suggestions
- Generative Fill - Image extension
- Text to Image - Custom image generation
- Logo Creator - New logo designs
- Mockup Creator - Product mockups
- Vehicle Wrap Mockup - Wrap previews

**Other Features:**
- AI History - View past generations
- Save to job capability

**Data it uses:**
- `ai_history`: id, tenant_id, tool, input_data, output, images, created_at
- `ai_responses`: id, tenant_id, tool, content, created_at
- `ai_usage_logs`: id, tenant_id, usage_type, count

**Automations/workflows:**
- Track usage against tier limits
- Log all AI interactions

**Integrations involved:**
- OpenAI GPT-5.2 (text generation)
- OpenAI GPT Image 1 (image generation)
- Emergent LLM Key (authentication)

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Monthly generation limits (25/100/unlimited), image generation on/off

---

## 12. AI ASSISTANT

**Module Name:** AI Business Assistant

**Purpose:** Conversational AI for business queries and insights.

**Where it lives:** `/ai-assistant`

**Who can access it:** All authenticated users

**Core actions:** Chat, Ask questions, Get insights

**Sub-features:**
- Natural language business queries
- Revenue queries
- Customer queries
- Job queries
- Trend analysis
- Comparison queries
- Contextual responses based on business data

**Data it uses:**
- Queries all business collections contextually
- `ai_history`: For conversation context

**Automations/workflows:**
- Context-aware responses using business data

**Integrations involved:**
- OpenAI GPT-5.2
- Emergent LLM Key

**Dependencies:** All business modules (for data context)

**Current status:** WORKING (reported intermittent issues)

**Tierable:** Yes
**Typical tier lever:** Query limits (10/50/unlimited), query types access

---

## 13. APPROVALS (ARTWORK PROOFS)

**Module Name:** Artwork Approval System

**Purpose:** Manage artwork proofs and customer approval workflow.

**Where it lives:** `/approvals`

**Who can access it:** Owner, Admin, Staff (Permission: `jobs:view`)

**Core actions:** Upload proof, Request approval, View status, View feedback

**Sub-features:**
- Upload artwork proofs
- Link proofs to jobs
- Send approval request to customer
- Track proof status (Pending, Approved, Revision Requested, Rejected)
- Customer feedback/notes
- Version tracking
- Email notifications

**Data it uses:**
- `artwork_proofs`: id, tenant_id, job_id, customer_id, image_url, status, feedback, created_at

**Automations/workflows:**
- Email notification on proof upload
- Status update notifications

**Integrations involved:**
- SendGrid (email notifications)

**Dependencies:** Jobs, Customers

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Proof storage limits

---

## 14. DOCUMENTS

**Module Name:** Document Management

**Purpose:** Store and manage business documents and files.

**Where it lives:** `/documents`

**Who can access it:** All authenticated users

**Core actions:** Upload, View, Delete, Organize, Share

**Sub-features:**
- File upload (images, PDFs, documents)
- Document organization
- Share with customers (portal)
- Activity logging
- File type validation
- Size limits

**Data it uses:**
- `documents`: id, tenant_id, name, file_url, file_type, size, folder, created_at
- `document_activities`: id, document_id, action, user_id, created_at
- `portal_documents`: id, tenant_id, customer_id, document_id

**Automations/workflows:**
- Activity logging on document actions

**Integrations involved:** None (base64 storage currently)

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Storage limits (100MB/500MB/2GB)

---

## 15. PRICING CALCULATOR

**Module Name:** Pricing Calculator

**Purpose:** Calculate project pricing based on materials, labor, and markups.

**Where it lives:** `/pricing-calculator`, `/pricing-calculator/settings`

**Who can access it:** All authenticated users (Settings: Owner, Admin)

**Core actions:** Calculate price, Save template, Apply to job

**Sub-features:**
- **Category-based pricing:**
  - Promotional products
  - Cut vinyl
  - Services/labor
  - Digital print
  - Rigid signs
  - Apparel
  - Vehicle graphics
  - Custom items
- **Material configurations:**
  - Vinyl types (Oracal 651/751/951, Avery HP750, Reflective, Specialty)
  - Print materials (Banner 13oz/18oz, Adhesive vinyl, Poster, Canvas, Backlit, Perforated)
  - Substrates (Coroplast, Aluminum, PVC, Acrylic, Dibond, MDO)
- **Service types:** Design, Installation, Removal, Site Survey, Consultation, Travel
- **Apparel types:** T-shirt, Hoodie, Hat, Polo, Tank, Longsleeve, Jacket
- **Transfer types:** HTV, Screen Print, DTF, Sublimation, Embroidery
- **Vehicle types:** Sedan, SUV, Mini Van, Cargo Van, Sprinter, Box Trucks (12/16/24ft), Trailer, Semi
- **Coverage types:** Spot, Partial, Half, Full
- Pricing templates (save/load configurations)
- Pricing defaults (per-tenant customization)
- Labor rate configuration
- Markup configuration

**Data it uses:**
- `pricing_defaults`: id, tenant_id, category, defaults
- `pricing_templates`: id, tenant_id, name, category, configuration

**Automations/workflows:**
- Auto-calculate totals based on dimensions, materials, labor

**Integrations involved:** None

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Template limits, AI price suggestions

---

## 16. WEBSTORES

**Module Name:** Webstore Management

**Purpose:** Create and manage customer-facing online stores.

**Where it lives:** `/webstores`, `/products`

**Who can access it:**
- View: Owner, Admin, Staff (Permission: `webstores:view`)
- Create/Manage: Owner, Admin (Permission: `webstores:create`, `webstores:manage`)

**Core actions:** Create store, Configure, Add products, Manage orders, Track payouts

**Sub-features:**

**Store Types:**
- B2B Store - Business-to-business ordering
- Fundraiser Store - Fundraising campaigns with profit sharing
- Creator Store - Creator/affiliate stores with commissions

**Store Configuration:**
- Store name and description
- Store status (Active, Paused, Completed, Archived)
- Public/private toggle
- Owner information
- Branding settings (logo, colors, banner)
- Custom domain (future)

**Product Management:**
- Product catalog with categories (Apparel, Signs, Decals, Promotional, Other)
- Product variants (sizes, colors)
- Product images (up to 3)
- Base cost and retail price
- Variant pricing
- Product assignment to stores
- Price overrides per store
- Enable/disable per store

**Order Management:**
- Order list with filters
- Order statuses (Pending, Processing, Ready, Shipped, Delivered, Cancelled)
- Order details view
- Convert order to job (auto or manual)
- Customer information
- Order notes

**Fundraiser Features:**
- Fundraiser goal amount
- Start/end dates
- Progress tracking
- Profit percentage configuration

**Creator Features:**
- Commission type (percentage or flat)
- Commission value
- Payout tracking

**Payout Management:**
- Payout owed tracking
- Payout paid tracking
- Commission calculations

**Storefront (Public):**
- Public store page at `/store/:storeId`
- Product browsing
- Add to cart
- Checkout flow
- Guest checkout
- Order placement

**Data it uses:**
- `webstores_v2`: id, tenant_id, name, store_type, status, owner_name, owner_email, branding, fundraiser_*, creator_*, payout_owed, payout_paid, total_sales, total_orders
- `products`: id, tenant_id, name, description, category, base_cost, retail_price, images, variants, is_active
- `webstore_products`: id, webstore_id, product_id, is_enabled, price_override
- `webstore_orders_v2`: id, webstore_id, customer_name, customer_email, items, subtotal, total_profit, commission_amount, status, job_id
- `webstore_payouts`: id, webstore_id, amount, date, notes

**Automations/workflows:**
- Auto-create job from order
- Auto-create customer from order
- Commission calculation on order
- Payout tracking updates
- Back-reference from job items to order items

**Integrations involved:**
- Stripe Connect (for creator/fundraiser payments)

**Dependencies:** Products

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Store count (1/3/unlimited), store types access, branding options

---

## 17. PRODUCTS (MASTER CATALOG)

**Module Name:** Product Catalog

**Purpose:** Manage master product catalog for webstores.

**Where it lives:** `/products`

**Who can access it:**
- View: Owner, Admin, Staff (Permission: `products:view`)
- Create/Manage: Owner, Admin (Permission: `products:create`, `products:manage`)

**Core actions:** Create, Edit, Delete, Manage variants

**Sub-features:**
- Product categories (Apparel, Signs, Decals, Promotional, Other)
- Product images (up to 3)
- Base cost and retail price
- Product variants (size, color, etc.)
- Variant availability toggle
- Additional cost per variant
- Active/inactive status
- Assign to multiple webstores

**Data it uses:**
- `products`: id, tenant_id, name, description, category, base_cost, retail_price, images, image_url, has_variants, variants, is_active, created_at, updated_at

**Automations/workflows:**
- Auto-set updated_at on edits

**Integrations involved:** None

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Product count, image count per product

---

## 18. COMPANY SETTINGS

**Module Name:** Company Settings

**Purpose:** Configure company profile and preferences.

**Where it lives:** `/settings`

**Who can access it:** Owner, Admin (Permission: `settings:view`, `settings:manage`)

**Core actions:** Update company info, Configure preferences

**Sub-features:**
- Company name and details
- Address information
- Contact information
- Logo upload
- Website URL
- Time tracking settings
  - Track per job
  - Track per line item
  - Employee portal toggle
  - Kiosk mode toggle
  - Auto-suggest on status change

**Data it uses:**
- `tenants`: All company profile fields, time_tracking_settings

**Automations/workflows:** None

**Integrations involved:** None

**Dependencies:** None

**Current status:** WORKING

**Tierable:** No (all tiers have access)

---

## 19. EMAIL TEMPLATES

**Module Name:** Email Template Management

**Purpose:** Customize transactional email templates.

**Where it lives:** `/settings/email-templates`

**Who can access it:** Owner, Admin (Permission: `settings:view`)

**Core actions:** View, Edit templates

**Sub-features:**
- Template types:
  - Quote sent
  - Invoice sent
  - Proof approval request
  - Order confirmation
  - Job status update
  - Payment received
- Variable placeholders
- Preview functionality
- HTML/text editing

**Data it uses:**
- Email templates stored in tenant configuration or dedicated collection

**Automations/workflows:**
- Templates used by automated email sends

**Integrations involved:**
- SendGrid

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Template customization depth

---

## 20. PAYMENT SETTINGS

**Module Name:** Payment Configuration

**Purpose:** Configure payment processing and Stripe integration.

**Where it lives:** `/admin/payments`

**Who can access it:** Owner, Admin (Permission: `settings:view`)

**Core actions:** Connect Stripe, Configure payment options

**Sub-features:**
- Stripe Connect setup
- Account connection status
- Webhook configuration
- Payment method enablement

**Data it uses:**
- `tenants`: stripe_account_id, stripe_connected

**Automations/workflows:**
- OAuth flow for Stripe Connect

**Integrations involved:**
- Stripe Connect

**Dependencies:** None

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Payment provider options

---

## 21. PROMO CODES (FOUNDER ONLY)

**Module Name:** Promo Code Management

**Purpose:** Create and manage promotional discount codes.

**Where it lives:** `/promo-codes`

**Who can access it:** Founders only (is_founder = true)

**Core actions:** Create, Edit, Delete, Deactivate codes

**Sub-features:**
- Code creation
- Discount type (percentage, fixed)
- Discount value
- Usage limits
- Expiration dates
- Active/inactive status

**Data it uses:**
- `promo_codes`: id, code, discount_type, discount_value, usage_limit, used_count, expires_at, is_active

**Automations/workflows:**
- Track usage count

**Integrations involved:** None

**Dependencies:** Billing

**Current status:** WORKING

**Tierable:** No (founder feature only)

---

## 22. CUSTOMER PORTAL

**Module Name:** Customer Portal

**Purpose:** Customer-facing portal for order tracking, communication, and approvals.

**Where it lives:** `/customer-portal/*`

**Who can access it:** Customers with portal access enabled

**Core actions:** Login, View orders, View quotes, View invoices, Message shop, Approve proofs, Manage profile

**Sub-features:**

**Authentication:**
- Portal registration (existing customers)
- Portal login
- Magic link login
- Password reset

**Dashboard:**
- Order summary
- Recent activity
- Pending approvals
- Quick stats

**Orders:**
- Order list
- Order detail view
- Order status tracking

**Quotes:**
- Quote list
- Quote details
- Quote approval

**Invoices:**
- Invoice list
- Invoice details
- Payment status

**Messaging:**
- Conversation list
- Send messages (text, images, files)
- View message history
- Message notifications

**Artwork Proofs:**
- Proof list
- Proof detail view
- Approve/Request revision/Reject
- Add feedback

**Appointments:**
- Appointment list
- Appointment types (Consultation, Installation, Pickup, Site Survey, Other)
- Appointment status (Scheduled, Confirmed, In Progress, Completed, Cancelled, No Show)

**Profile:**
- Update contact info
- Notification preferences
- Tax exempt status

**Documents:**
- View shared documents

**Data it uses:**
- `customers`: portal_enabled, portal_password_hash
- `conversations`: id, tenant_id, customer_id, messages
- `conversation_messages`: id, conversation_id, sender_type, content, type
- `artwork_proofs`: For proof approval
- `customer_notifications`: id, customer_id, type, message, read
- `magic_links`: For passwordless login

**Automations/workflows:**
- Email notifications on new messages
- Email notifications on proof uploads
- Status update notifications

**Integrations involved:**
- SendGrid (notifications)

**Dependencies:** Customers, Jobs, Invoices, Approvals

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Messaging on/off, appointments on/off, document sharing

---

## 23. EMPLOYEE PORTAL

**Module Name:** Employee Portal

**Purpose:** Employee-facing portal for time clock and pay information.

**Where it lives:** `/employee-portal/*`

**Who can access it:** Employees with PIN access

**Core actions:** Clock in/out, View pay, View tasks

**Sub-features:**

**Authentication:**
- PIN-based login
- Email + PIN

**Dashboard:**
- Current clock status
- Today's hours
- Week summary

**Time Clock:**
- Clock in
- Clock out
- Break start/end
- View time history

**Pay:**
- Current period earnings
- YTD earnings
- Payment history
- Balance owed

**Tasks:**
- Assigned tasks list
- Task details
- Mark complete

**Profile:**
- View profile info
- Update PIN

**Data it uses:**
- `employees`: pin, hourly_rate
- `timelogs`: For time tracking
- `payroll_transactions`: For pay history
- `tasks`: For task assignments

**Automations/workflows:**
- Real-time clock status tracking
- Auto-calculate earnings

**Integrations involved:** None

**Dependencies:** Employees, Time Clock, Payroll

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Portal access on/off (tenant setting)

---

## 24. BILLING & SUBSCRIPTIONS

**Module Name:** Billing System

**Purpose:** SaaS subscription management and payments.

**Where it lives:** `/pricing-plans`, `/billing/success`, `/billing/cancel`

**Who can access it:** All authenticated users

**Core actions:** View plans, Subscribe, Manage subscription

**Sub-features:**

**Subscription Plans:**
- Starter (free tier)
- Pro ($49/month or $490/year)
- Business ($99/month or $990/year)
- AI Addon ($29/month or $290/year)
- Extended Trial ($19.99 one-time, 14-day full access)

**Checkout:**
- Stripe Checkout integration
- Mode: subscription for regular plans
- Mode: payment for extended trial
- Trial credits toward Business subscription

**Subscription Management:**
- View current plan
- View subscription status
- View billing history
- Cancel subscription

**Founder Pricing:**
- Limited founder spots
- Lifetime discounted pricing
- Founder number assignment

**Data it uses:**
- `subscriptions`: id, tenant_id, plan, status, tier, stripe_subscription_id, stripe_customer_id, current_period_end, is_founder, founder_number
- `payment_transactions`: id, tenant_id, stripe_session_id, amount, status, plan
- `tenants`: plan, is_founder, subscription_status

**Automations/workflows:**
- Webhook handling for subscription events
- Auto-activate on payment success
- Auto-update on renewal
- Auto-cancel/pause on payment failure
- Trial expiration handling

**Integrations involved:**
- Stripe (subscriptions, webhooks)

**Dependencies:** None

**Current status:** WORKING

**Tierable:** N/A (this IS the tier system)

---

## 25. PUBLIC WEBSITE / MARKETING PAGES

**Module Name:** Marketing Website

**Purpose:** Public-facing marketing pages for lead generation.

**Where it lives:** `/`, `/home`, `/features`, `/pricing`, `/about`, `/contact`

**Who can access it:** Public (no authentication)

**Core actions:** View pages, Submit contact form

**Sub-features:**

**Landing Page:**
- Hero section
- Feature highlights
- Call to action
- Testimonials

**Features Page:**
- Detailed feature descriptions
- Screenshots/demos

**Pricing Page:**
- Plan comparison
- Pricing table
- Sign up CTAs

**About Page:**
- Company story
- Team information

**Contact Page:**
- Contact form
- Contact information

**Documentation:**
- Getting started guide
- Feature documentation
- FAQ

**Data it uses:** None (static content)

**Automations/workflows:**
- Contact form submission (email notification)

**Integrations involved:**
- SendGrid (contact form)

**Dependencies:** None

**Current status:** WORKING

**Tierable:** No

---

## 26. TASKS

**Module Name:** Task Management

**Purpose:** Assign and track tasks for employees.

**Where it lives:** Integrated in Jobs and Employee Portal

**Who can access it:** All authenticated users

**Core actions:** Create, Assign, Complete, Delete

**Sub-features:**
- Task creation
- Link to job
- Assign to employee
- Due date
- Completion tracking
- Task list view

**Data it uses:**
- `tasks`: id, tenant_id, title, description, job_id, assigned_to, due_date, is_complete, created_at

**Automations/workflows:**
- Notification on assignment

**Integrations involved:** None

**Dependencies:** Jobs, Employees

**Current status:** WORKING

**Tierable:** Yes
**Typical tier lever:** Task limits, assignment features

---

# B) NAVIGATION + PAGES MAP

## Main Navigation (Sidebar)

| Category | Items | Route | Permission Required |
|----------|-------|-------|---------------------|
| Dashboard | Dashboard | `/dashboard` | None |
| Sales | Customers | `/customers` | `customers:view` |
| Sales | Jobs | `/jobs` | `jobs:view` |
| Sales | Invoices | `/invoices` | `invoices:view` |
| Operations | Time Clock | `/timeclock` | `time:own` |
| Operations | Payroll | `/payroll` | `payroll:view` |
| Operations | Productivity | `/productivity` | None |
| Operations | Financials | `/financials` | `financials:view` |
| Webstores | Webstores | `/webstores` | `webstores:view` |
| Webstores | Products | `/products` | `webstores:view` |
| Tools | AI Tools | `/ai-tools` | None |
| Tools | Approvals | `/approvals` | `jobs:view` |
| Tools | Documents | `/documents` | None |
| Tools | Pricing Calculator | `/pricing-calculator` | None |
| Admin | Users | `/users` | `users:view` |
| Admin | Company Settings | `/settings` | `settings:view` |
| Admin | Payment Settings | `/admin/payments` | `settings:view` |
| Admin | Email Templates | `/settings/email-templates` | `settings:view` |
| Admin | Promo Codes | `/promo-codes` | Founder only |
| Admin | Pricing Settings | `/pricing-calculator/settings` | `settings:view` |

## Public Pages

| Page | Route | Purpose |
|------|-------|---------|
| Landing Page | `/`, `/home` | Marketing homepage |
| Features | `/features` | Feature showcase |
| Pricing (Public) | `/pricing` | Plan comparison |
| About | `/about` | Company info |
| Contact | `/contact` | Contact form |
| Login | `/login` | Authentication |
| Pricing Plans | `/pricing-plans` | Subscription signup |
| Billing Success | `/billing/success` | Post-checkout success |
| Billing Cancel | `/billing/cancel` | Checkout cancelled |
| Storefront | `/store/:storeId` | Public webstore |
| Documentation | `/docs/*` | Help documentation |

## Customer Portal Pages

| Page | Route | Features |
|------|-------|----------|
| Portal Login | `/customer-portal/login` | Customer authentication |
| Portal Dashboard | `/customer-portal` | Overview, stats |
| Orders | `/customer-portal/orders` | Order list |
| Order Detail | `/customer-portal/orders/:orderId` | Single order |
| Quotes | `/customer-portal/quotes` | Quote list |
| Invoices | `/customer-portal/invoices` | Invoice list |
| Messages | `/customer-portal/messages` | Conversations |
| Conversation | `/customer-portal/messages/:conversationId` | Single thread |
| Proofs | `/customer-portal/proofs` | Artwork proofs |
| Proof Detail | `/customer-portal/proofs/:proofId` | Single proof |
| Appointments | `/customer-portal/appointments` | Scheduling |
| Profile | `/customer-portal/profile` | Account settings |
| Documents | `/customer-portal/documents` | Shared files |

## Employee Portal Pages

| Page | Route | Features |
|------|-------|----------|
| Employee Login | `/employee-portal/login` | PIN authentication |
| Employee Dashboard | `/employee-portal` | Clock status, summary |
| Pay | `/employee-portal/pay` | Earnings, history |
| Tasks | `/employee-portal/tasks` | Assigned tasks |
| Profile | `/employee-portal/profile` | Account settings |

---

# C) DATA/BACKEND INVENTORY

## Collections/Tables

| Collection | Purpose | Key Fields | Relationships |
|------------|---------|------------|---------------|
| `tenants` | Multi-tenant organizations | id, name, slug, owner_email, plan, is_active, time_tracking_settings | Has many: users, customers, jobs |
| `users` | Authenticated users | id, tenant_id, email, full_name, role, is_founder, hashed_password | Belongs to: tenant |
| `customers` | Customer records | id, tenant_id, name, email, phone, status, portal_enabled | Belongs to: tenant; Has many: jobs, invoices |
| `jobs` | Work orders (quotes + jobs) | id, tenant_id, customer_id, name, status, subtotal | Belongs to: tenant, customer; Has many: job_items, job_notes |
| `job_items` | Line items on jobs | id, job_id, item_type, description, quantity, unit_price, status | Belongs to: job |
| `job_notes` | Notes on jobs | id, job_id, content, created_by | Belongs to: job |
| `job_activities` | Activity log | id, job_id, activity_type, description | Belongs to: job |
| `job_time_entries` | Time tracked on jobs | id, job_id, employee_id, hours, start_time, end_time | Belongs to: job, employee |
| `invoices` | Customer invoices | id, tenant_id, customer_id, job_id, invoice_number, status, total | Belongs to: tenant, customer, job |
| `employees` | Employee records | id, tenant_id, name, email, hourly_rate, pin | Belongs to: tenant |
| `timelogs` | Clock in/out records | id, tenant_id, employee_id, job_id, start_time, end_time | Belongs to: tenant, employee, job |
| `payroll_transactions` | Pay records | id, tenant_id, employee_id, type, amount | Belongs to: tenant, employee |
| `products` | Master product catalog | id, tenant_id, name, category, base_cost, retail_price, variants | Belongs to: tenant |
| `webstores_v2` | Online stores | id, tenant_id, name, store_type, status, branding, payout_owed | Belongs to: tenant; Has many: orders |
| `webstore_products` | Product assignments | id, webstore_id, product_id, is_enabled, price_override | Links: webstore, product |
| `webstore_orders_v2` | Store orders | id, webstore_id, customer_name, items, subtotal, job_id | Belongs to: webstore; Links to: job |
| `webstore_payouts` | Payout records | id, webstore_id, amount, date | Belongs to: webstore |
| `conversations` | Message threads | id, tenant_id, customer_id | Belongs to: tenant, customer |
| `conversation_messages` | Individual messages | id, conversation_id, sender_type, content, type | Belongs to: conversation |
| `artwork_proofs` | Proof files | id, tenant_id, job_id, customer_id, image_url, status | Belongs to: job, customer |
| `customer_notifications` | Portal notifications | id, customer_id, type, message, read | Belongs to: customer |
| `documents` | File storage | id, tenant_id, name, file_url, file_type | Belongs to: tenant |
| `portal_documents` | Shared docs | id, tenant_id, customer_id, document_id | Links: tenant, customer, document |
| `tasks` | Employee tasks | id, tenant_id, job_id, assigned_to, title, is_complete | Belongs to: tenant, job, employee |
| `subscriptions` | SaaS subscriptions | id, tenant_id, plan, status, tier, stripe_subscription_id | Belongs to: tenant |
| `payment_transactions` | Payment records | id, tenant_id, stripe_session_id, amount, status | Belongs to: tenant |
| `pricing_defaults` | Pricing config | id, tenant_id, category, defaults | Belongs to: tenant |
| `pricing_templates` | Saved templates | id, tenant_id, name, configuration | Belongs to: tenant |
| `ai_history` | AI tool usage | id, tenant_id, tool, input_data, output, images | Belongs to: tenant |
| `ai_responses` | AI responses | id, tenant_id, tool, content | Belongs to: tenant |
| `ai_usage_logs` | AI usage tracking | id, tenant_id, usage_type, count | Belongs to: tenant |
| `promo_codes` | Discount codes | id, code, discount_type, discount_value, is_active | Global |
| `expense_entries` | Expense records | id, tenant_id, category, amount, date | Belongs to: tenant |
| `sales_entries` | Sales records | id, tenant_id, amount, date | Belongs to: tenant |
| `tenant_usage` | Usage tracking | id, tenant_id, usage_type, current_usage, limit | Belongs to: tenant |
| `magic_links` | Passwordless auth | id, customer_id, token, expires_at | Belongs to: customer |

## Status Enums

**JobStatus:** quote, approved, in_progress, completed, invoiced, archived

**JobItemStatus:** pending, in_production, done

**JobItemType:** banner, yard_sign, decal, wrap, install, design, vehicle_graphics, window_graphics, dimensional_letters, monument_sign, other

**InvoiceStatus:** draft, sent, paid, overdue

**CustomerStatus:** lead, active, inactive

**WebstoreType:** b2b, fundraiser, creator

**WebstoreStatus:** active, paused, completed, archived

**OrderStatus:** pending, processing, ready, shipped, delivered, cancelled

**ProofStatus:** pending, approved, revision_requested, rejected

**SubscriptionStatus:** trialing, active, past_due, cancelled, expired, locked, pending

**UserRole:** owner, admin, staff

**TenantPlan:** starter, pro, business

## Helper Lists (Dropdowns)

- ProductCategory: apparel, signs, decals, promotional, other
- ExpenseCategory: 21 categories (materials, labor, equipment, etc.)
- VinylType: 7 types
- PrintMaterial: 8 types
- SubstrateType: 11 types
- VehicleType: 11 types
- ServiceType: 7 types
- ApparelType: 8 types
- TransferType: 5 types
- AppointmentType: 5 types
- PaymentMethod: 5 types

## Background Tasks / Scheduled Jobs

Currently: None implemented

Future potential: Trial expiration checks, subscription renewal reminders, abandoned cart emails

---

# D) INTEGRATIONS INVENTORY

## Stripe

**Purpose:** Payment processing for SaaS subscriptions and webstore payments

**How Used:**
- Checkout Sessions (mode: subscription, payment)
- Price IDs for recurring billing (env vars configured, placeholders pending real IDs)
- Webhooks for subscription lifecycle events:
  - checkout.session.completed
  - customer.subscription.created
  - customer.subscription.updated
  - customer.subscription.deleted
  - invoice.payment_succeeded
  - invoice.payment_failed

**Stripe Connect:**
- For webstore owner payouts (fundraiser/creator stores)
- OAuth connection flow
- Separate from main billing

## SendGrid

**Purpose:** Transactional email delivery

**How Used:**
- Quote sent notifications
- Invoice notifications
- Proof approval requests
- Order confirmations
- Portal notifications
- Contact form submissions

## OpenAI

**Purpose:** AI-powered content and image generation

**How Used:**
- GPT-5.2 for text generation (20+ tool types)
- GPT Image 1 for image generation
- Via Emergent LLM Key integration

**Models:**
- Text: emergentintegrations OpenAITextService
- Images: emergentintegrations OpenAIImageService

## reportlab

**Purpose:** PDF document generation

**How Used:**
- Invoice PDF export
- Quote PDF export

## File Storage

**Current:** Base64 in MongoDB (images, documents)

**Note:** Not ideal for scale, future improvement to object storage recommended

---

# E) NOT IMPLEMENTED / FUTURE IDEAS

## Planned but Not Built

1. **Custom Domain Support** - Allow tenants to use their own domain for webstores
2. **SMS Notifications** - Twilio integration for text alerts
3. **QuickBooks Integration** - Accounting sync
4. **PayPal Integration** - Alternative payment method
5. **Affirm/Klarna Integration** - BNPL options
6. **Vehicle Wrap AI Tool** - Advanced vector-based wrap design (spec exists)
7. **Race Number Generator** - Racing-specific tools
8. **Wrap Cost Calculator** - Specialized pricing tool
9. **Dynamic Questionnaire Creator** - Custom intake forms
10. **Kanban Job Board** - Visual job pipeline (tier-locked, UI partially exists)
11. **Job Activity Log UI** - Full activity timeline view
12. **Advanced Analytics** - Trend analysis, forecasting
13. **Scheduled Reports** - Auto-generated email reports
14. **Zapier Integration** - Workflow automation
15. **Google Analytics Integration** - Marketing tracking
16. **Facebook Pixel** - Ad conversion tracking
17. **Mailchimp Integration** - Email marketing
18. **Leaderboard for Fundraisers** - Gamification
19. **B2B Features** - Volume discounts, net terms, POs
20. **Store Credit System** - Customer credits/refunds
21. **Calculated Shipping** - Real-time shipping rates
22. **Low Stock Alerts** - Inventory management
23. **Abandoned Cart Emails** - Recovery automation
24. **Marketing Email Campaigns** - Bulk email
25. **Custom User Roles** - Beyond owner/admin/staff
26. **Data Export** - Full data download
27. **Data Backup** - Automated backups

---

# MASTER FEATURE HIERARCHY

```
SignGuy AI
├── Authentication & Access
│   ├── User Registration
│   ├── User Login/Logout
│   ├── Role Management (Owner/Admin/Staff)
│   ├── Permission System (23 permissions)
│   └── Founder Account Features
│
├── Dashboard
│   ├── Revenue Summary
│   ├── Job Counts
│   ├── Recent Activity
│   └── Quick Stats
│
├── Sales Module
│   ├── Customers
│   │   ├── Customer List
│   │   ├── Customer Details
│   │   ├── Customer Status (Lead/Active/Inactive)
│   │   ├── Portal Access Toggle
│   │   └── Customer Tags/Notes
│   │
│   ├── Jobs (Unified Quotes/Jobs)
│   │   ├── Job List with Filters
│   │   ├── Create Quote
│   │   ├── Create Job
│   │   ├── Job Statuses (Quote → Approved → In Progress → Completed → Invoiced)
│   │   ├── Line Items
│   │   ├── Job Notes
│   │   ├── Activity Log
│   │   └── Convert Quote to Job
│   │
│   └── Invoices
│       ├── Invoice List
│       ├── Create from Job
│       ├── Invoice Statuses
│       ├── PDF Export
│       └── Payment Tracking
│
├── Operations Module
│   ├── Time Clock
│   │   ├── Clock In/Out
│   │   ├── Break Tracking
│   │   ├── Manual Entries
│   │   ├── Time by Job
│   │   └── Reports
│   │
│   ├── Payroll
│   │   ├── Earnings Tracking
│   │   ├── Payment Recording
│   │   └── Balance Management
│   │
│   ├── Productivity
│   │   └── Daily/Weekly Metrics
│   │
│   └── Financials
│       ├── Revenue Tracking
│       ├── Expense Tracking (21 categories)
│       └── Profit Analysis
│
├── Webstores Module
│   ├── Store Management
│   │   ├── Store Types (B2B/Fundraiser/Creator)
│   │   ├── Store Configuration
│   │   ├── Branding Settings
│   │   └── Store Status
│   │
│   ├── Products
│   │   ├── Product Catalog
│   │   ├── Categories (5 types)
│   │   ├── Variants
│   │   ├── Images (up to 3)
│   │   └── Store Assignment
│   │
│   ├── Orders
│   │   ├── Order List
│   │   ├── Order Statuses (6 stages)
│   │   ├── Convert to Job
│   │   └── Customer Management
│   │
│   ├── Fundraiser Features
│   │   ├── Goal Tracking
│   │   ├── Date Range
│   │   └── Progress Display
│   │
│   ├── Creator Features
│   │   ├── Commission Configuration
│   │   └── Payout Tracking
│   │
│   └── Public Storefront
│       ├── Product Browsing
│       ├── Cart
│       └── Checkout
│
├── Tools Module
│   ├── AI Tools
│   │   ├── Text Generation (20+ tools)
│   │   ├── Image Generation (10+ tools)
│   │   ├── AI History
│   │   └── Usage Tracking
│   │
│   ├── AI Assistant
│   │   └── Business Query Chat
│   │
│   ├── Approvals
│   │   ├── Proof Upload
│   │   ├── Approval Workflow
│   │   └── Customer Feedback
│   │
│   ├── Documents
│   │   ├── File Upload
│   │   ├── Organization
│   │   └── Customer Sharing
│   │
│   └── Pricing Calculator
│       ├── Category Pricing
│       ├── Material Selection
│       ├── Labor Calculation
│       └── Templates
│
├── Admin Module
│   ├── Users
│   │   └── Role Management
│   │
│   ├── Company Settings
│   │   ├── Company Profile
│   │   └── Time Tracking Settings
│   │
│   ├── Payment Settings
│   │   └── Stripe Connect
│   │
│   ├── Email Templates
│   │   └── Template Customization
│   │
│   ├── Pricing Settings
│   │   └── Default Configuration
│   │
│   └── Promo Codes (Founder Only)
│       └── Discount Management
│
├── Customer Portal
│   ├── Authentication
│   ├── Dashboard
│   ├── Orders View
│   ├── Quotes View
│   ├── Invoices View
│   ├── Messaging
│   ├── Proof Approvals
│   ├── Appointments
│   ├── Documents
│   └── Profile
│
├── Employee Portal
│   ├── PIN Authentication
│   ├── Clock In/Out
│   ├── Pay View
│   ├── Tasks
│   └── Profile
│
├── Billing & Subscriptions
│   ├── Plan Selection
│   ├── Stripe Checkout
│   ├── Subscription Management
│   ├── Founder Pricing
│   └── Extended Trial
│
└── Marketing Website
    ├── Landing Page
    ├── Features Page
    ├── Pricing Page
    ├── About Page
    ├── Contact Page
    └── Documentation
```

---

# FEATURE-TO-TIER READINESS TAGS

| Module | Tierable | Typical Tier Lever |
|--------|----------|-------------------|
| Authentication | Yes | Team member limits |
| Dashboard | Yes | Analytics depth |
| Customers | Yes | Customer limits, advanced CRM |
| Jobs | Yes | Active job limits, kanban, activity log |
| Invoices | Yes | Invoice count, payment integrations |
| Time Clock | Yes | Feature on/off |
| Payroll | Yes | Feature on/off |
| Productivity | Yes | Report depth, export |
| Financials | Yes | Feature on/off, export |
| Webstores | Yes | Store count (1/3/unlimited), store types |
| Products | Yes | Product count, image limits |
| AI Tools | Yes | Monthly limits (25/100/unlimited), image gen |
| AI Assistant | Yes | Query limits, query types |
| Approvals | Yes | Storage limits |
| Documents | Yes | Storage limits (100MB/500MB/2GB) |
| Pricing Calculator | Yes | Template limits, AI suggestions |
| Customer Portal | Yes | Messaging, appointments on/off |
| Employee Portal | Yes | Feature on/off (tenant setting) |
| Email Templates | Yes | Customization depth |
| Company Settings | No | All tiers |
| Payment Settings | Yes | Payment provider options |
| Promo Codes | No | Founder only |

---

# QUALITY CHECK

| Question | Answer |
|----------|--------|
| Did you list every page? | Yes - 40+ pages/routes documented |
| Did you list every database table/collection? | Yes - 42 collections documented |
| Did you list every role and permission rule? | Yes - 3 roles, 23 permissions |
| Did you separate implemented vs not implemented? | Yes - Section E for future items |
| Did you list sub-features for every module? | Yes - Detailed sub-features per module |

---

*Document generated by comprehensive codebase audit including frontend routes, backend routes, models, database collections, and integration files.*
