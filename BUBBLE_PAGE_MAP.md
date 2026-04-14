# Sign Guy AI - Page/Route Map (Current)

> Last updated: Feb 2026. Reflects all current routes including Unified Productivity, Admin Payroll Worksheet, Signatures/Drawings, Employee Portal, Customer Portal, and public pages.

## NAVIGATION STRUCTURE

### Main Layout
**File:** `/app/frontend/src/components/MainLayout.js`

- Fixed header with TopAppBar + PrimaryNav + ActionToolbar (desktop: 152px)
- Mobile: hamburger drawer
- Logo from tenant settings
- Active route highlighting
- Floating AI Assistant overlay
- Trial countdown / upgrade prompt when applicable

### Navigation Groups (Ribbon-based)
1. **Core**: Dashboard, Customers, Orders, Quotes, Invoices
2. **Operations**: Time Clock, Payroll, Productivity, Financials
3. **Tools**: AI Tools, AI Assistant, Webstores, Products
4. **Admin**: Users, Settings, Approvals, Admin Portal, Documents
5. **Reports**: Profit Margin Analytics

---

## PROTECTED ROUTES (Require Authentication)

### Dashboard
**Route:** `/dashboard` -> Redirects to `/productivity?view=dashboard`
**Note:** The legacy standalone dashboard is now a view inside the Unified Productivity page.

---

### Customers
**Route:** `/customers`
**File:** `Customers.js`
**Purpose:** CRUD for customer records with search, status filter, portal toggle

---

### Orders List
**Route:** `/orders`
**File:** `OrdersPage.js`
**Purpose:** View/manage all shop orders with filter tabs (Active, Completed, Archived)

### New Order Form
**Route:** `/orders/new`
**File:** `NewOrderForm.js`
**Purpose:** Multi-step order creation wizard

### Order Detail
**Route:** `/orders/:id`
**File:** `OrderDetail.js`
**Purpose:** Comprehensive order management: line items (job tickets), notes, activity, financial snapshot, drawings, signatures, file uploads
**Key sub-features:**
- Inline drawing canvas (`DrawingCanvasPad`) for sketches/markups
- Signature capture modal
- File upload with markup overlay
- Job ticket management

### Add Ticket to Order
**Route:** `/orders/:id/add-ticket`
**File:** `AddTicketToOrder.js`

### Job Ticket Detail
**Route:** `/job-tickets/:ticketId`
**File:** `JobTicketDetail.js`
**Purpose:** Individual ticket with production tasks, workflow steps, time tracking

---

### Quotes
**Route:** `/quotes`
**File:** `Quotes.js`
**Purpose:** Quote CRUD with line items, convert to order

---

### Invoices
**Route:** `/invoices`
**File:** `Invoices.js`
**Purpose:** Invoice management with payment tracking, Stripe Connect

---

### Time Clock
**Route:** `/timeclock`
**File:** `TimeClock.js`
**Purpose:** Employee clock in/out with break tracking, daily summary
**Data sources:** `/api/timeclock/*` endpoints

---

### Payroll (Admin Payroll Worksheet)
**Route:** `/payroll`
**File:** `Payroll.js`
**Purpose:** Desktop-first, single-screen Admin Payroll Worksheet

**Key UI Components:**
| Component | File | Description |
|-----------|------|-------------|
| PayrollWorksheetToolbar | `PayrollWorksheetToolbar.js` | Employee selector, date range, cycle presets, export/print |
| PayrollWeekTable | `PayrollWeekTable.js` | 7-day inline editable spreadsheet (Start, Lunch Out, Lunch In, End, Reg Hrs, OT) |
| PayrollAdjustmentsPanel | `PayrollAdjustmentsPanel.js` | Earnings/advance/payment rows with add/remove |
| PayrollLegacyEntriesSection | `PayrollLegacyEntriesSection.js` | Older off-grid manual entries with resolution UI |
| PayrollWorksheetSummary | `PayrollWorksheetSummary.js` | Period totals (shift pay + adjustments + legacy = final) |
| PayrollSignoffStrip | `PayrollSignoffStrip.js` | Review/approve sign-off with lock for non-editors |

**Data Sources:**
- `GET /api/payroll/report` (custom date ranges, compensation snapshots)
- `POST /api/payroll/timeclock-shifts` (create manual shifts)
- `PUT /api/payroll/timeclock-shifts/:id` (inline edit)
- `GET/PUT /api/payroll/signoff` (sign-off strip)
- `GET /api/payroll/legacy-manual-entries` (legacy data)
- `PUT /api/payroll/legacy-manual-entries/:id/resolution` (resolve legacy)
- `GET/POST/PUT/DELETE /api/payroll/transactions` (adjustments)

**Workflow:** All changes are local (tracked by "unsaved changes" badge) until admin clicks Save. Export/Print disabled while unsaved.

---

### Productivity (Unified)
**Route:** `/productivity`
**File:** `Productivity.js`
**Purpose:** Unified productivity layer aggregating tasks, orders, job tickets, schedule shifts, appointments into four views

**Views (controlled by `?view=` param):**
| View | Component | Description |
|------|-----------|-------------|
| dashboard | `ProductivityDashboardView.js` | Summary cards, due today, overdue, assigned to me |
| list | `ProductivityTaskListView.js` | Filterable task list with inline completion |
| calendar | `ProductivityCalendarView.js` | Calendar with daily task breakdown |
| kanban | `ProductivityKanbanView.js` | Drag-and-drop board (Open/In Progress/Blocked/Done) |

**Data Sources:**
- `GET /api/productivity/items` (unified aggregation)
- `GET /api/productivity/summary` (counts/stats)
- `PATCH /api/productivity/items/:uid` (update from any view)

**Filters bar:** `ProductivityFiltersBar.js` - Type, status, priority, assigned user, customer, date range

---

### Financials
**Route:** `/financials`
**File:** `Financials.js`
**Purpose:** Sales entries, expense tracking, date-range summaries

### Profit Margin Analytics
**Route:** `/reports/profit-margin`
**File:** `ProfitMarginAnalytics.js`

---

### AI Tools
**Route:** `/ai-tools`
**File:** `AITools.js`
**Purpose:** 6 AI assistants (layout generator, print checklist, brand kit, document creator, overdue assistant, design intake)

### AI Assistant
**Route:** `/ai-assistant`
**File:** `AIAssistant.js`
**Purpose:** Conversational AI business assistant with action capabilities

---

### Webstores
**Route:** `/webstores`
**File:** `Webstores.js`
**Purpose:** Manage fundraiser campaigns, B2B stores, creator stores, orders

### Products
**Route:** `/products`
**File:** `Products.js`
**Purpose:** Product catalog management

---

### Production Board
**Route:** `/production-board`
**File:** `ProductionBoard.js`
**Purpose:** Visual production tracking board

---

### User Management
**Route:** `/users`
**File:** `UserManagement.js`
**Purpose:** Manage staff accounts, roles, permissions

### Company Settings
**Route:** `/settings`
**File:** `CompanySettings.js`
**Purpose:** Company profile, branding, and configuration panels:
- Business details (name, address, logo)
- **Payroll Settings** (weekly/biweekly cycle, pay week start day)
- Time tracking settings
- Employee portal toggle
- Signature settings

### Sub-settings Pages
| Route | File | Purpose |
|-------|------|---------|
| `/settings/pricing-setup` | `PricingSetup.js` | Historical invoice import, pricing foundation |
| `/settings/email-templates` | `EmailTemplates.js` | Custom email templates |
| `/settings/production` | `ProductionSettings.js` | Workflow templates, production config |
| `/settings/backup` | `BackupRestore.js` | Data backup/restore |
| `/settings/digest` | `DigestSettings.js` | Daily digest email preferences |

---

### Other Protected Routes
| Route | File | Purpose |
|-------|------|---------|
| `/approvals` | `Approvals.js` | Proof/quote approval queue |
| `/admin-portal` | `AdminPortal.js` | Communications hub |
| `/documents` | `Documents.js` | Document library |
| `/community` | `CommunityHub.js` | Community features |
| `/onboarding` | `OnboardingHub.js` | Guided onboarding |
| `/pricing-calculator` | `Pricing.js` | Live pricing calculator |
| `/pricing-calculator/settings` | `PricingSettings.js` | Pricing config |
| `/billing` | `BillingManagement.js` | Subscription billing |
| `/questionnaires` | `Questionnaires.js` | Dynamic form builder |
| `/admin/payments` | `PaymentSettings.js` | Stripe Connect settings |
| `/promo-codes` | `PromoCodes.js` | Discount code management |
| `/materials` | `MaterialsAdmin.js` | Materials pricing admin |

---

## PUBLIC ROUTES (No Authentication)

### Marketing / Landing
| Route | File | Purpose |
|-------|------|---------|
| `/` | `LandingPage.js` | Main landing page |
| `/features` | `FeaturesPage.js` | Feature showcase |
| `/pricing` | `FoundersEditionPricing.js` | Pricing page |
| `/founders` | `FoundersEditionPricing.js` | Founders Edition |
| `/why-founder` | `WhyFounderPage.js` | Founders value prop |
| `/about` | `AboutPage.js` | About page |
| `/contact` | `ContactPage.js` | Contact form |
| `/terms` | `TermsOfService.js` | Legal |
| `/privacy` | `PrivacyPolicy.js` | Legal |
| `/pricing-plans` | `PricingPlansV2.js` | Multi-product pricing |

### Auth
| Route | File |
|-------|------|
| `/login` | `Login.js` |
| `/register` | Redirects to `/login?register=true` |

### Documentation
| Route | File |
|-------|------|
| `/docs` | `DocsLayout.js` (outlet) |
| `/docs/getting-started` | `GettingStarted.js` |
| `/docs/customers` | `DocsCustomers.js` |
| `/docs/quotes-jobs` | `DocsQuotesJobs.js` |
| `/docs/invoicing` | `DocsInvoicing.js` |
| `/docs/pricing-calculator` | `DocsPricingCalculator.js` |
| `/docs/ai-tools` | `DocsAITools.js` |
| `/docs/time-tracking` | `DocsTimeTracking.js` |
| `/docs/employees` | `DocsEmployees.js` |
| `/docs/webstores` | `DocsWebstores.js` |
| `/docs/customer-portal` | `DocsCustomerPortal.js` |
| `/docs/financials` | `DocsFinancials.js` |
| `/docs/productivity` | `DocsProductivity.js` |
| `/docs/document-library` | `DocsDocumentLibrary.js` |
| `/docs/faq` | `DocsFAQ.js` |

### Public Storefronts & Forms
| Route | File | Purpose |
|-------|------|---------|
| `/store/:storeId` | `Storefront.js` | Public webstore |
| `/questionnaire/:questionnaireId` | `PublicQuestionnaire.js` | Public form |
| `/customer-sign/:token` | `PublicSignaturePage.js` | Email signature capture |

---

## CUSTOMER PORTAL (Separate Auth)

| Route | File | Purpose |
|-------|------|---------|
| `/customer-portal/login` | `PortalLogin.js` | Customer login |
| `/customer-portal` | `PortalDashboard.js` | Dashboard |
| `/customer-portal/orders` | `PortalOrders.js` | View orders |
| `/customer-portal/orders/:orderId` | (detail) | Order detail |
| `/customer-portal/forms` | `PortalForms.js` | Fill forms |
| `/customer-portal/documents` | `PortalDocuments.js` | View documents |
| `/customer-portal/messages` | `PortalMessages.js` | Messaging |
| `/customer-portal/proofs` | `PortalProofs.js` | Proof approval |
| `/customer-portal/appointments` | (list) | Appointments |
| `/customer-portal/profile` | `PortalProfile.js` | Profile settings |

---

## EMPLOYEE PORTAL (Separate Auth)

| Route | File | Purpose |
|-------|------|---------|
| `/employee-portal/login` | `EmployeePortalLogin.js` | PIN-based login |
| `/employee-portal` | `EmployeePortalDashboard.js` | Dashboard, clock in/out |
| `/employee-portal/jobs/:jobId` | `EmployeePortalJob.js` | Job details |
| `/employee-portal/pay` | `EmployeePortalPay.js` | Pay stubs |
| `/employee-portal/tasks` | `EmployeePortalTasks.js` | Assigned tasks |
| `/employee-portal/profile` | `EmployeePortalProfile.js` | Profile |

---

## KEY SHARED COMPONENTS

| Component | Path | Used In |
|-----------|------|---------|
| DrawingCanvasPad | `components/DrawingCanvasPad.js` | Order Detail (sketches, markups, signatures) |
| SignatureCaptureModal | `components/SignatureCaptureModal.js` | Order Detail, Quotes, Invoices |
| SignatureSection | `components/SignatureSection.js` | Order Detail |
| LivePricingPanel | `components/LivePricingPanel.js` | Order Detail, Quotes |
| PricingCalculator | `components/PricingCalculator.js` | Pricing page |
| FloatingAssistant | `components/FloatingAssistant.js` | All authenticated pages |
| ProductionTimeline | `components/ProductionTimeline.js` | Order Detail |
| OrderCommandBar | `components/orders/OrderCommandBar.js` | Order Detail |
| Ribbon (TopAppBar, PrimaryNav, ActionToolbar, MobileNav) | `components/ribbon/*` | MainLayout |

### Utility Functions
**File:** `/app/frontend/src/lib/utils.js`
- `cn()` - className merger
- `formatCurrency()`, `formatDate()`, `formatDateTime()`, `formatTime()`
- `getStatusColor()`, `getInitials()`

**File:** `/app/frontend/src/lib/payrollWorksheet.js`
- `buildWorksheetRows()`, `buildAdjustmentRows()`, `summarizeWorksheet()`
- `getCurrentCycleRange()`, `getPresetDateRange()`, `getDateRangeDates()`
- `calculateBreakMinutes()`, `hasShiftContent()`, `hasAdjustmentContent()`
- `inferTransactionType()`, `getSignedAdjustmentTotal()`, `toIsoDateTime()`

**File:** `/app/frontend/src/lib/payrollExport.js`
- `buildPayrollCsv()`, `buildPayrollPrintHtml()`, `downloadTextFile()`
