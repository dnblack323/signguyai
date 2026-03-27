# SignGuy AI - Complete Feature Catalog v6.0

> **Last Updated:** March 27, 2026

---

## CORE SYSTEM: Orders & Job Tickets

### Order Management
- Create orders with customer info, due dates, source tracking
- Auto-generated order numbers (ORD-0001, ORD-0002...)
- Customer type-ahead search (filters by name, company, email, phone)
- Order status tracking: New Intake → Awaiting Review → Approved → In Production → Ready for Pickup → Completed
- Payment status: Unpaid, Deposit Paid, Partially Paid, Paid
- File upload on orders (artwork, drawings, photos, notes)
- Internal and customer notes
- Pickup/delivery method selection
- Order total auto-calculated from ticket prices

### Job Tickets (Production Detail)
- **Quick Entry mode**: Item name, category, qty, price, description, toggles — for fast intake
- **Detailed Entry mode**: Full category-specific dynamic form with settings-driven options and live pricing
- Ticket numbering: ORD-0001-T1, ORD-0001-T2...
- 8 categories: Banners, Rigid Signs, Cut Vinyl, Digital Print, Vehicle Wrap, Apparel, Promo/Misc, Custom
- Subtypes per category (7-12 each, e.g. Mesh Banner, Pole Banner, Retractable Banner)
- Category-specific fields: 20-30 fields per category covering specs, finishing, materials, production
- Design/proof/artwork status tracking
- Priority levels: Normal, High, Urgent, Rush
- Production workflow toggle (auto-generates tasks when enabled)
- Pricing snapshot storage (calculator vs manual, breakdown preserved)
- Duplicate ticket action
- Edit specs inline

### Dynamic Category Fields
| Category | Fields | Subtypes | Key Specs |
|----------|--------|----------|-----------|
| Banners | 24 | 7 | Width, Height, Material (12 options), Hems, Grommets, Pole Pockets, Wind Slits, Reinforced Corners |
| Rigid Signs | 22 | 7 | Substrate (11 options), Thickness, Lamination, Drill Holes, Stakes, Mounting Hardware |
| Cut Vinyl | 23 | 8 | Vinyl Type (6 options), Colors, Layered/Single, Weed, Mask, Inside/Outside Mount |
| Digital Print | 24 | 12 | Media Type (10 options), Roll/Sheet, Print Quality, Lamination, Mounting, Contour Cut |
| Vehicle Wrap | 30 | 10 | Vehicle Type, Coverage Level, Areas (checkboxes), Vinyl, Paneling, Install Difficulty |
| Apparel | 27 | 8 | Garment Type (9 options), Brand/Style, Size Breakdown (XS-5XL), Decoration Method (6 options), Print Locations (12 checkboxes with per-location details) |

### Financial Documents
- Generate Quote from job tickets
- Generate Invoice from job tickets
- Generate Work Order (production document with full specs)
- Email Quote/Invoice to customer
- Financial tab on order shows all linked documents

### Production System
- Category-based workflow templates (6 defaults: Rigid Signs 11 stages, Banners 12, Cut Vinyl 8, Vehicle Wrap 14, Apparel 11, Promo 5)
- Auto-generate production tasks when workflow enabled
- Status per task: Not Started, In Progress, Paused, On Hold, Complete, Rework
- Task controls: Start, Complete, Pause on each task
- Status roll-up: tasks → tickets → orders (partial completion tracked)
- Production Board: view by department or status
- Activity logging on all status changes
- Workflow Template Manager (admin): edit stage names, departments, order, required toggle

---

## PRICING & CALCULATOR

### Live Pricing
- Real-time price estimates while filling in job ticket forms
- Calculator mode (from settings) or Manual mode (override)
- Pricing breakdown: Material, Labor, Setup, Overhead, Markup, Sell Price
- Setup fee added flat (not marked up)
- Pricing snapshot saved on ticket (preserves breakdown + source)

### Materials & Pricing Admin
- Global rates: Production labor ($/hr), Design rate, Install rate, Default markup, Overhead %, Target margin, Minimum order
- Materials catalog: Print materials (12), Vinyl (6), Substrates (11), Apparel (9), Decoration methods (6)
- Inline editing of material names and costs
- Add/remove materials
- All calculator values flow from settings — zero hardcoding

### Apparel Quantity Discounts
- 12+: 5% off | 24+: 10% | 48+: 15% | 72+: 20% | 144+: 25%
- Configurable in settings

---

## CUSTOMERS

- Full CRUD with search
- Contact info, company, status, notes
- Customer portal (view invoices, make payments, submit forms)
- New Order button from customer detail (pre-fills info)
- Related orders/invoices/quotes per customer

---

## BILLING & PAYMENTS

- Invoice CRUD with line items
- Stripe payment processing
- Stripe Connect for tenant payment acceptance
- Founders Edition plan: $99/mo or $594/year
- Promo codes: FOUNDERS (50% off), PAPPYBILL (19 free days)
- Processing fees: 2.2% + $0.20 platform, 2% webstore

---

## AI TOOLS (41 Total)

### Image Generation (11 tools)
Logo Creator, Logo Refresher, AI Sign Designer, AI Banner Designer, Mockup Creator, Vehicle Wrap Mockup, Text to Image, Race Number Designer, Driver Name Plate, Race Team Branding, Generative Fill

### Text Generation (30 tools)
Tagline Generator, Social Media Post, Business Copywriter, Review Responder, Blog Creator, Proposal Writer, Campaign Builder, Pricing Intelligence, Brand Color Advisor, Wrap Cost Calculator, Email Generator (6 types), Product Description, and more

### AI Business Assistant
- Chat with GPT-5.2 about business data
- Voice input (Whisper STT) and output (TTS)
- Multi-turn conversation with session management
- Structured database actions (create job, update status, etc.)

### AI Credits
- 150 monthly credits (don't roll over)
- Purchasable packs: 100 ($10), 300 ($25), 1000 ($60) — never expire
- Credit cost per tool: 1-3 credits
- Confirmation popup with "don't show again" option

---

## TEAM & PAYROLL

### Employee Management
- Add/edit/remove employees
- Role assignment (Owner, Admin, Staff)
- User management with search

### Time Tracking
- Clock in/out with break tracking
- Job timer integration
- Manual hour entry and editing
- Timesheet view with edit capability per entry

### Employee Schedule (NEW)
- Weekly grid view (Mon-Sun) for all employees
- Click cell to set shift (start time, end time, notes)
- Clear shift option
- Visual indicators for assigned shifts

### Payroll
- Hourly rate management
- Regular/overtime calculation
- Transaction tracking (earnings, advances, payments)
- Pay period summary

---

## FINANCIALS

- Daily sales entry (amount, payment method, description)
- Daily expense entry (amount, category, description)
- Financial summary (total sales, expenses, net profit)
- Top-level navigation item

---

## WEBSTORES

- Create/manage webstores
- Product management with variants
- Fundraiser campaigns
- Customer-facing storefront
- Order processing

---

## DOCUMENTS

- Document library with upload
- Categories and tagging
- Send via email
- Questionnaire builder

---

## REPORTS

- Profit & Margin Analytics
- Productivity tracking
- Sales Analytics
- Webstore Analytics

---

## PLATFORM

- Multi-tenant architecture
- JWT authentication with bcrypt
- Founder grace period (14 days read-only)
- Platform owner account (never expires)
- Production setup page (/setup)
- Dark shell / light content UI theme
- Mobile-responsive navigation
- Terms of Service & Privacy Policy
- SendGrid email integration
- File upload system
- 30 database indexes for performance
