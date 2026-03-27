# SignGuy AI - Ultimate To-Do List
## Master Task Tracker (Staged by Priority)

> **Created:** March 18, 2026
> **Last Updated:** March 27, 2026
> **Status:** Active
> **Current Plan:** Founders Edition Only ($99/mo)

---

# STAGE 1: CRITICAL FIXES & REINSTATEMENTS ✅ COMPLETED (March 20, 2026)

### 1.1 AI Tools Rate Limiter Parameter Fix ✅ DONE
### 1.2 AI Credit Cost Audit & Assignment ✅ VERIFIED
### 1.3 AI Credit Confirmation Popup Audit ✅ VERIFIED
### 1.4 Promo Code System - Backend ✅ DONE
### 1.5 Promo Code System - Frontend ✅ DONE
### 1.6 Invoice Line Items Fix Verification ✅ VERIFIED

---

# STAGE 2: LEGAL, DOCUMENTATION & COLOR SCHEME ✅ COMPLETED (March 22, 2026)

### 2.1 Terms of Service Page ✅ DONE
### 2.2 Privacy Policy Page ✅ DONE
### 2.3 Footer Links ✅ DONE
### 2.4 Color Scheme (amber → violet/purple) ✅ DONE
### 2.5 Update Documentation Pages ✅ DONE (March 27)
- All docs updated to reflect Orders/Job Tickets system
- DocsQuotesJobs → DocsOrdersTickets
- DocsEmployees updated with schedule feature
- GettingStarted updated with order workflow
### 2.6 Update Feature Catalog ✅ DONE (March 27)
- FEATURE_ROADMAP.md completely rewritten for v6.0
- BUILD_ROADMAP.md rewritten with all completed features
- All "Jobs" references replaced with "Orders" across 30+ files
### 2.7 Landing Page - Founders Focused ✅ DONE

---

# STAGE 3: NAVIGATION & UI OVERHAUL ✅ COMPLETED (March 23-27, 2026)

### 3.1 Main Navigation Bar ✅ DONE
- Legacy "Jobs" tab removed entirely
- "Orders" tab with sub-nav: All Orders, Production Board, Approvals
- "Financials" added as top-level nav (was hidden under Reports)
- "Reports" is now a shortcuts page
- Contact Support → emails donnell@signguy-ai.com
- Mobile nav rebuilt with all pages and expandable sub-menus

### 3.2 Dark Shell / Light Content UI ✅ DONE (March 27)
- Applied to ALL 30+ pages globally
- Dark shell background, white content cards
- Multiple cards per page with visible dark gaps
- Container max-width 1600px
- Fixed all light-on-light text issues
- Inline styles converted to Tailwind classes
- Button text colors corrected (white text on colored buttons)

### 3.3 All AI Tools Verification ✅ DONE (March 22)
- 11/11 image tools tested and passing
- 10+ text tools tested and passing
- AI Business Assistant verified
- Email Generator verified
- Credit deduction verified

---

# STAGE 4: SEARCH, UX & ORDER SYSTEM ✅ COMPLETED (March 22-27, 2026)

### 4.1 Orders Page Search ✅ DONE
### 4.2 Invoices Page Search ✅ DONE
### 4.3 Webstores Page Search ✅ DONE
### 4.4 Quick Add Order from Customer ✅ DONE
### 4.5 4-Layer Order System ✅ DONE
- Order → Job Tickets → Quotes/Invoices → Production Tasks
- Full CRUD backend + frontend for all 4 layers
- 6 category dynamic field schemas (Banner 24, Rigid Signs 22, Cut Vinyl 23, Digital Print 24, Vehicle Wrap 30, Apparel 27 fields)
- Quick Entry / Detailed Entry modes
- Live pricing panel connected to settings-driven calculator
- Production Board (by department, status)
- Workflow Template Manager (admin)
- File upload on orders
- Order actions: Generate Quote/Invoice/Work Order, Email, Status change, Portal
- Customer type-ahead search on new order form
- Duplicate ticket action
- Apparel quantity discounts (5-25%)
- Setup fee fix (flat, not marked up)

### 4.6 Materials & Pricing Admin ✅ DONE
- Global rates: labor, design, install, markup, overhead, margin, minimum
- Materials catalog with inline editing
- Add/remove materials by category
- All calculator values from settings

### 4.7 Employee Schedule ✅ DONE
- Weekly grid (Mon-Sun) for all employees
- Click cell to set shift time/notes
- Save/clear per cell
- Schedule tab on Payroll page

### 4.8 Financials Endpoints ✅ DONE
- POST/GET /api/financials/sales
- POST/GET /api/financials/expenses
- GET /api/financials/summary

### 4.9 Database Indexes ✅ DONE
- 30 indexes created across all major collections

---

# STAGE 5: REMAINING FIXES & POLISH

### 5.1 Stripe Connect Enrollment
- **Status:** BLOCKED — platform Stripe account needs Connect enabled at dashboard.stripe.com/connect
- **Impact:** Dad's account and all tenants can't accept portal payments until this is done
- **Action:** User must visit https://dashboard.stripe.com/connect and complete enrollment

### 5.2 Orders Page Bulk Actions
- **Status:** Not started
- Checkbox selection, bulk complete/archive/delete

### 5.3 Task List Display Bug
- **Status:** Investigating — API works correctly, may be frontend re-render timing
- Tasks create successfully but may not appear in Productivity list view immediately

### 5.4 Subtype Conditional Field Logic
- **Status:** Schemas serve subtypes but form doesn't yet hide/show fields based on subtype selection
- Example: Mesh Banner should default mesh material, Retractable should hide grommets

### 5.5 Live Pricing Accuracy
- **Status:** Partially done — pricing panel shows estimates but some finishing options may not fully affect the calculation for all categories

---

# STAGE 6: INFRASTRUCTURE & CODE QUALITY

### 6.1 Rate Limiting
- Install slowapi, apply to AI + auth + public endpoints

### 6.2 CORS Configuration
- Use environment-based origins instead of allow_origins=["*"]

### 6.3 Error Boundaries
- React Error Boundary component, wrap main routes

### 6.4 Code Cleanup
- Remove console.log, replace print() with logger in backend

### 6.5 Tier Config Deprecation
- Remove old tier_config.py usage, fully migrate to founders_plan.py

---

# STAGE 7: FUTURE FEATURES (BACKLOG)

### 7.1 Vehicle Wrap AI Tool
### 7.2 QuickBooks Integration
### 7.3 SMS Notifications (Twilio)
### 7.4 Cookie Consent Banner
### 7.5 GDPR Data Tools (export, deletion)
### 7.6 Custom Domain Support for Webstores
### 7.7 Learning Pricing Calculator
### 7.8 Advanced Analytics & Reporting
### 7.9 AI Job Estimator / Smart Scheduling
### 7.10 Inventory & Purchasing System
### 7.11 Calendar Integrations (Google, Outlook)
### 7.12 Webstore Advanced Features (discounts, bundles, shipping)
### 7.13 Drag/Drop Production Board
### 7.14 Calendar View for Install Jobs
### 7.15 Scheduled Reports (auto weekly/monthly email)

---

# COMPLETION SUMMARY

| Stage | Items | Status | Completion |
|-------|-------|--------|------------|
| **Stage 1** | 6 | Critical Fixes | ✅ 100% |
| **Stage 2** | 7 | Legal, Docs, Color | ✅ 100% |
| **Stage 3** | 3 | Navigation & UI | ✅ 100% |
| **Stage 4** | 9 | Orders, Search, UX | ✅ 100% |
| **Stage 5** | 5 | Remaining Fixes | 🟡 20% |
| **Stage 6** | 5 | Infrastructure | ⬜ 0% |
| **Stage 7** | 15 | Future Backlog | ⬜ 0% |

**Overall: 25 of 50 tasks complete (50%) — all critical and high-priority work done**

---

*Last updated: March 27, 2026*
