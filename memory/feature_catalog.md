# SignGuy AI - Feature Catalog

Last updated: February 2026

## Core Operating System
- Multi-tenant sign shop SaaS
- Role-based access control (Owner / Admin / Staff)
- Founders Edition plan model
- Customer portal
- Employee portal
- Terminology: Orders & Order Items (standardized across all user-facing UI)

## Orders & Order Items
- 4-layer workflow:
  - Orders (master container)
  - Order Items (individual production items, internally "job tickets")
  - Quotes / Invoices / Work Orders (financial documents from order items)
  - Production Tasks (department-level workflow stages)
- Dynamic category schemas (banners, rigid signs, cut vinyl, digital print, vehicle wrap, apparel, etc.)
- Live estimate / pricing integration
- Draft orders
- Order files and artwork attachments
- Workflow shortcuts from order/order item views (assign, schedule, create task)
- **Quick Camera Upload & Markup:**
  - "Photo" dropdown on Order Detail (Take Photo / Choose from Gallery)
  - Per-item "Quick Photo" in Order Item dropdown menus
  - "Quick Photo" and "Choose Photo" buttons on Order Item Detail
  - Auto-upload + immediate Drawing Modal opening
  - Original photo in Files tab, markup in Drawings tab
  - Mobile-first camera access via `capture="environment"`

## Signatures, Drawings & Markup
- Feature-toggle controlled signature system
- Internal signature capture
- Customer review-and-sign links
- Record-specific signatures for order / quote / proof / invoice / work order / change / pickup-install contexts
- Order-level drawing storage
- Item-level drawing storage
- Uploaded image markup mode
- **4 annotation tools:** Draw (freehand), Arrow, Circle, Text
- Color picker with swatch preview, pen size selector
- Undo, Clear, autosave drafts

## Productivity
- Unified productivity data layer
- Productivity Dashboard (redirected from `/dashboard`)
- Calendar: Month / Week / Day views
- Kanban Board with drag/drop persistence
- Task List with inline edits
- Cross-view sync from shared records
- Employee schedule integration
- Production task integration

## Admin Payroll Worksheet
- Desktop-first single-screen spreadsheet replacing legacy payroll UI
- Inline editable 7-day table (Start, Lunch Out, Lunch In, End, Reg Hours, OT)
- Adjustments panel (earnings/advance/payment rows)
- Legacy manual entry resolution UI (keep/exclude/convert)
- Review & sign-off strip with read-only lock
- Company-level payroll settings (weekly/biweekly, pay week start day)
- Unsaved changes badge, CSV export, printable report

## Time Clock / Employee Management
- Employee directory and lifecycle actions
- Time clock punches with normalized saved shifts
- Historical timeclock backfill from raw logs
- Payroll rollups from: time clock shifts, manual hours, order timer entries, transactions
- Admin editing of: manual hours, saved shifts, transactions
- Employee portal invites with PIN
- Employee portal permission gating from tenant settings

## Billing / Finance
- Founders Edition billing
- Stripe integration
- Processing fee support
- Invoice generation from order items
- Promo codes
- Financial reporting: Sales, Expenses, Profit Margin Analytics

## AI Tools
- GPT-based text generation tools (layout, checklist, brand kit, document, overdue, design intake)
- Completed Order Post Creator (with image upload)
- Social Media Order Post Creator
- GPT image generation tools
- AI Business Assistant (conversational with actions)
- Racing Number Designer
- Voice / transcription helpers
- AI credit accounting and balance checks

## Documentation / Public-Facing
- Public features page
- Public pricing pages (Founders Edition, multi-product plans)
- In-app docs: Getting Started, Orders & Order Items, Invoicing, Pricing Calculator, AI Tools, Time Tracking, Employees, Webstores, Customer Portal, Financials, Productivity, Document Library, FAQ
- BUBBLE documentation files (Database Schema, Page Map, Workflows, Dependency Map)
