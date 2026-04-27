# Prelaunch Open Items Tracker — Failures & Cannot-Fully-Test Items

This is the **single running unresolved-items file**.

Use categories:
- ❌ Failed and still open
- ⛔ Cannot fully test without user/external actions

Last updated: 2026-04-27 (post Tier 7 sweep — Signatures & Drawings)

---

## ✅ Recently Resolved

| Item | Fix | Date |
|------|-----|------|
| **T7-DELETE-DRAWING** | Added `platform_admin` to allowed roles in DELETE `/api/order-drawings/{id}` | 2026-04-27 |
| **T7-UPDATE-DRAWING** | Added label→title mirror sync in PUT `/api/order-drawings/{id}` | 2026-04-27 |
| **T7-SIGNATURE-IP** | Added `client_ip` capture to signature capture and public sign routes | 2026-04-27 |
| **2.1F** Tax-exempt toggle | Added `default_tax_rate` to tenant model + CompanySettings UI; invoice generation now checks `is_tax_exempt` flag per customer | 2026-04-26 |
| **2.2E** Assets-panel upload/thumbnail | Rewrote `OrderAssetsPanel.js` — drag-and-drop zone + `AssetThumbnail` component shows real image blobs | 2026-04-26 |
| **T1-ISO-E** Payroll READ security bug | Added `_require_payroll_view_access()` to all GET payroll routes — staff now `403` | 2026-04-26 |
| **T1-CSV** Customer CSV export | Added `GET /api/customers/export` (name, email, phone, company, status, notes, created_at) | 2026-04-26 |
| **T3-WF-A** Workflow template apply | Added `POST /api/workflow-templates/{id}/apply` + `/duplicate` — generates production tasks per stage | 2026-04-26 |
| **T4-PORTAL-C** Portal appointments | Added `GET /api/portal/appointments` for customer portal | 2026-04-26 |
| **T4-PAYROLL-A** Payroll CSV export | Added `format=csv` query param to `GET /api/payroll/report` | 2026-04-26 |
| **T4-EMP-PORTAL-A** Employee dashboard alias | Added `GET /api/employee-portal/dashboard` (alias of `/work-summary`) | 2026-04-26 |
| **5.1 Customer Request Appointment** (NEW FEATURE) | `POST /api/portal/appointments/request` + admin `PUT /confirm` & `/reject` + portal UI dialog with "Pending Confirmation" badge | 2026-04-26 |
| **5.1 DELETE user endpoint** | Added `DELETE /api/admin/users/{id}` with self / staff-perm / last-owner guards | 2026-04-26 |
| **Auth permission bug** | Fixed `Permission.USERS_EDIT` → `USERS_MANAGE` in `routes/auth.py` (status + reset-password) | 2026-04-26 |
| **Customer request appointment email** | Tenant owner receives HTML email on portal appointment request (`email_logs` confirms `status='sent'`) | 2026-04-26 |
| **Admin Quote PDF** (NEW) | `GET /api/quotes/{id}/pdf` returns valid PDF with company/customer/line-items/totals/terms | 2026-04-26 |
| **Admin Invoice PDF** (NEW) | `GET /api/invoices/{id}/pdf` returns valid PDF with PAID/UNPAID badge, totals, watermark | 2026-04-26 |
| **Tier 6 sweep** | AI assistant, email composer, voice, image-gen, SendGrid all PASS (iteration_135, 20/20) | 2026-04-26 |
| **Tier 7 sweep** | Signatures & Drawings backend sweep: 22/24 tests pass (iteration_136) | 2026-04-27 |
| **Tier 8 sweep** | Docs & Marketing frontend sweep: 17/17 tests pass (iteration_137). All 24 public pages verified. Docs updated with Signatures/Drawings, Appointments, Financials content. | 2026-04-27 |

---

## ❌ Failed and still open

### Tier 1

#### 1.4 Stripe Connect
- **1.4B** Connect status not fully enabled (`charges_enabled=false`, `payouts_enabled=false`, `onboarding_complete=false`)
  - Next: complete Stripe Connect onboarding and re-check status endpoint

#### 1.6 CSV Import
- **1.6Q** Mid-batch validation failure still leaves partial inserts by design (runtime exceptions rollback; row-validation remains partial-skip)
  - Next: product decision required (strict atomic import vs row-level partial import)

---

## ⛔ Cannot fully test without user/external actions

### Tier 1 (personal verification / inbox / clean-tenant / Stripe dashboard)
- **1.1D, 1.1E, 1.1F, 1.1G, 1.1H, 1.1L** (restore on clean tenant + live backup action)
- **1.2A, 1.2B, 1.2E, 1.2F, 1.2H, 1.2I, 1.2J, 1.2K, 1.2L, 1.2M, 1.2N**
- **1.3B, 1.3C, 1.3D, 1.3E, 1.3F, 1.3G, 1.3H, 1.3I**
- **1.4A, 1.4C, 1.4D, 1.4E, 1.4F, 1.4G, 1.4H**
- **1.5B, 1.5D, 1.5E, 1.5G, 1.5H**
- **1.6R**

### Tier 2 (external/email/mobile/manual dependency)
- **2.1G** (portal invite email + end-user login)
- **2.5C, 2.5I, 2.5J, 2.5K, 2.5L, 2.5M**
- **2.7N, 2.7R**
- **2.9L**
- **2.10E**

---

## Source references
- `/app/memory/PRELAUNCH_CHECKLIST.md`
- `/app/memory/PRELAUNCH_PRETEST_RESULTS.md`
- `/app/memory/PRELAUNCH_POSTFIX_RETEST_RESULTS.md`
