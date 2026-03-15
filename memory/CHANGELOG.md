# SignGuy AI - Changelog


## March 15, 2026 - Company-Based Pricing Foundation

### New Feature: Pricing & Cost Settings (`/pricing-calculator/settings`)
- Rebuilt pricing settings into a tenant-specific pricing control center
- Added editable material costs, labor rates, overhead settings, category defaults, and selling price benchmarks
- Explicitly separated **Selling Price Benchmarks** from **Actual Cost Settings** to avoid fake-profit math
- Added Settings ribbon access: **Settings → Pricing & Costs**

### Pricing Engine Upgrade
- `GET/PUT /api/pricing/defaults` now reads/writes tenant pricing configuration consistently
- All 8 calculator categories now use company settings for cost math
- Calculator responses now include: `material_cost`, `labor_cost`, `overhead_cost`, `total_cost`, `selling_price`, `profit_amount`, `profit_margin_percent`

### Estimate Storage Upgrade
- Job/quote estimate items can now preserve `pricing_category`, `pricing_data`, and `cost_snapshot`
- Invoice line items created from jobs retain pricing metadata for later analytics/reporting

### Testing
- Manual smoke test passed on preview for login + `/pricing-calculator/settings`
- Backend/API verification passed for defaults + calculator math + job snapshot persistence
- Test report: `/app/test_reports/iteration_54.json`

## March 15, 2026 - Pricing Expansion to Remaining Calculators

### Expanded Calculator Coverage
- Added company-based settings support to **Cut Vinyl**, **Apparel**, **Services**, and **Custom / Miscellaneous** calculators
- Also removed remaining hardcoded pricing paths from **Promotional** calculations so all active calculator categories use tenant settings
- Added new material presets: `apparel_blank`, `apparel_decoration`, `misc_material`
- Expanded category defaults + selling benchmarks to support all calculator categories

### Consistent Cost Snapshot Storage
- Calculator-generated snapshots now include `material_cost`, `labor_cost`, `overhead_cost`, `total_cost`, `selling_price`, `profit`, `profit_margin`, plus compatibility fields
- Job items persist these snapshots consistently across categories for future analytics

### Testing
- Expanded audit completed via `/app/test_reports/iteration_55.json`
- Result: **100% backend + 100% frontend pass** for all 8 calculator categories

## March 15, 2026 - Historical Invoice Import + AI Pricing Analysis

### New Feature: Pricing Setup (`/settings/pricing-setup`)
- Added a tenant-specific workflow for historical invoice uploads inside Company Settings / Pricing Setup
- Supports **PDF, CSV, XLSX, XLS** invoice files
- Added import history, field mapping review, category override review, AI analysis, and benchmark review states

### AI Benchmark Pipeline
- GPT-5.2 now analyzes normalized invoice data to generate selling benchmark suggestions
- Suggestions include confidence levels: **High / Medium / Low**
- Review workflow supports **Accept / Edit / Ignore** before any value is saved
- Accepted suggestions update **selling_price_benchmarks only** and do not change company cost settings

### Testing
- Full feature validation completed via `/app/test_reports/iteration_56.json`
- Result: **100% backend + 100% frontend pass** for historical pricing setup workflow

## March 15, 2026 - Profit & Margin Analytics Dashboard

### New Feature: Profit & Margin Analytics (`/reports/profit-margin`)
- Added tenant-specific reporting dashboard powered by stored `cost_snapshot` data + selling benchmarks
- Includes top metrics, profit by category, job profitability table, customer profitability report, and underpriced job detection
- Added time range filters, category filters, CSV/XLSX/PDF export options, and widget customization
- Added **Simple View** toggle so reporting stays usable without over-complication

### Testing
- Full feature validation completed via `/app/test_reports/iteration_57.json`
- Result: **100% backend + 100% frontend pass** for profit analytics
- Pre-existing note from testing: legacy `/financials` frontend exists but its backend routes are still missing and were not introduced by this phase

## March 15, 2026 - Production Workflow + Job History Integration

### Workflow Settings Upgrade
- Added tenant-specific workflow settings endpoint: `GET/PUT /api/production-timeline/settings`
- Added **Workflow Mode** selector in Settings → Production (`Simple`, `Detailed`, `Custom`)
- Custom templates can now be assigned to a category as the active workflow

### Job History Upgrade
- Added unified job history endpoint: `/api/jobs/{job_id}/history`
- Job Details now includes a **View Timeline** button that opens a scrollable, filterable history panel
- History combines job activities, artwork/proof events, production stage events, linked documents, and invoice/payment events

### Testing
- Full feature validation completed via `/app/test_reports/iteration_58.json`
- Result: **100% backend + 100% frontend pass** for the production workflow + timeline scope

## March 15, 2026 - Employee Portal + Production Tracking Integration

### Employee Portal Upgrade
- Added assigned jobs list and work summary metrics to the employee dashboard
- Added employee job detail page with production stage controls (`Start`, `Pause`, `Complete`)
- Employee stage actions update production timeline status and duration data

### Admin Assignment Upgrade
- Added Job Details assignment UI for assigning employees to whole jobs
- Added stage-level employee assignment inside the production timeline editor
- Backend now returns `assigned_employee_details` in job detail payloads

### Testing
- Full feature validation completed via `/app/test_reports/iteration_59.json`
- Result: **100% backend + 100% frontend pass** for the employee portal + production tracking scope


## March 14, 2026 - Admin Payroll Enhancement + Document Library Update

### Major Enhancement: Admin Payroll Page (`/payroll`)
- Complete rewrite of payroll page with 4-tab layout
- **Overview Tab**: Pay period summary table with per-employee gross pay, overtime, advances, payments, net owed
- **Time Sheets Tab**: Consolidated view combining job timer entries + manual hours with employee/date filters
- **Manual Hours Tab**: Add, edit, delete manual hours entries for employees
  - Supports per-job allocation (optional job assignment)
  - Task type categorization (general, design, production, installation, admin)
  - Automatic gross pay calculation (hours × hourly rate)
- **Transactions Tab**: Existing earnings/advances/payments ledger
- **Overtime Calculation**: Automatic 1.5x overtime for hours over 40/week (or 80/biweekly)
- **Pay Period Selector**: Weekly or Bi-Weekly period types
- **Summary Cards**: Total Hours, Regular Hours, Overtime Hours, Gross Pay, Net Owed
- New backend endpoints: POST/PUT/DELETE `/api/payroll/hours`, GET `/api/payroll/timesheet`, GET `/api/payroll/pay-period`
- New MongoDB collection: `payroll_hours` for manual hour entries

### Enhancement: Document Library Send Methods
- Updated send dialog with 3 methods: **Email PDF** (no response needed), **Portal** (view only), **As Form** (interactive questionnaire)
- Each method has clear description explaining what the customer receives
- "As Form" method redirects to questionnaire creator for interactive customer forms
- Clear labeling: "No response needed" for PDF/Portal, "Customer fills it out" for Form

### Testing
- All backend APIs: 100% pass rate
- All frontend UI elements: 100% pass rate
- Test file: `/app/backend/tests/test_payroll_enhancement.py`

## March 14, 2026 - Community Hub + Backup System + Pricing Transparency

### New Feature: Community Hub (`/community`)
- Searchable message board for bug reports, feature requests, questions, and feedback
- Category system: Bug Report, Feature Request, Question, Feedback
- Upvote system for prioritizing posts
- Owner can reply with "Official" badge, pin posts, change status (Open/In Progress/Resolved/Closed)
- Owner replies auto-mark posts as "Answered"
- Direct "Contact Support" email link to app owner
- Search across titles, descriptions, and replies
- Filter by category and status
- Added to main navigation bar
- Backend: `/api/community/posts`, `/api/community/stats` + CRUD endpoints
- Frontend: `CommunityHub.js` with list and detail views

### New Feature: Tenant Data Backup & Restore (`/settings/backup`)
- Owner-only backup/restore system
- Download all tenant data as JSON (images excluded, ~31KB vs 20MB)
- Restore with preview summary and confirmation ("This will replace all existing data")
- Weekly backup reminder banner (dismissable per session)
- Link from Company Settings > Data Management
- Backend: `/api/backup/export`, `/api/backup/status`, `/api/backup/preview-restore`, `/api/backup/restore`

### Enhancement: Webstore Product Image Upload
- Added image upload UI (up to 3 images per product) to Create Product form
- Product list shows image thumbnails

### Enhancement: Landing Page Pricing Transparency (8 Sections)
- Founder Launch Offer banner, How AI Credits Work block, Billing & Payments section
- AI Usage Transparency notice with example UI, Fair Usage Protection notice
- 4 new FAQ questions on both FoundersEditionPricing.js and LandingPage.js

### Bug Fix: Login Network Error (P0)
- Tenant response optimization: 2.95MB → 497 bytes (base64 logo separated to `/api/tenant/logo`)
- Production routing issue identified: `quote-to-invoice-3.emergent.host` → "Deployment not found" (Emergent support contacted)
