# Launch Readiness Master Checklist — Index
Source: LAUNCH READY MASTER DOC.pdf (uploaded 2026-06-07)

## Checklist Files By Category

| File | Category | Status |
|---|---|---|
| [LAUNCH_CAT1_CORE_WORKFLOW.md](./LAUNCH_CAT1_CORE_WORKFLOW.md) | Category 1: Core Sales And Customer Workflow | In Progress |
| [LAUNCH_CAT2_PRODUCTION.md](./LAUNCH_CAT2_PRODUCTION.md) | Category 2: Production And Work Management | Not Started |
| [LAUNCH_CAT3_PRICING.md](./LAUNCH_CAT3_PRICING.md) | Category 3: Pricing, Products, And Catalog | Not Started |
| [LAUNCH_CAT4_BILLING.md](./LAUNCH_CAT4_BILLING.md) | Category 4: Billing, Payments, And Financial Reporting | Not Started |

---

## Overall Progress Summary

### Category 1: Core Sales And Customer Workflow
- **Section 1 (Dashboard):** ~60% — Fixed: platform_creator permissions, PendingCustomerActionsWidget error+retry, dead code
- **Section 2 (Customers):** ~40% — Fixed: tenant scoping bugs (update readback + create lookup), customer load error+retry, View Quotes filter, webstores error state, lint fixes
- **Section 3 (Quotes):** Not started — Key blockers: Share Link (`/portal/{token}` no route), Email Quote action (success toast / coming soon), `sent_at` regression
- **Sections 4–10:** Not started
- **Category-Wide Blockers:** 10 remaining (signature terminal states, quote share links, approval false-success, etc.)

### Category 2: Production And Work Management
- Not started — Key blockers: Production Board false-success on update fail, proof-approval dependency enforcement, public appointment GET mutations

### Category 3: Pricing, Products, And Catalog
- Not started — Key blockers: promo code tenant safety, promotional double-sided bug, Custom/Other description persistence, `handleAnalyze` response parsing

### Category 4: Billing, Payments, And Financial Reporting
- Not started — Key blockers: invoice endpoint permissions, unscoped invoice mutations, Financials field contract (`net_income` vs `net_profit`), unsigned webhooks, Founder Billing return flow

---

## Fixes Applied To Date (2026-06-07)

### Permission Fix (Affects Cat 1 + Cat 4)
- `backend/models/auth.py`: Added `UserRole.PLATFORM_CREATOR: list(Permission)` to ROLE_PERMISSIONS
- `frontend/src/context/AuthContext.js`: Updated `hasPermission()` to bypass for `platform_creator` and `platform_admin`
- **Result:** Invoices, Financials, and all permission-gated pages now accessible for the admin account

### Category 1, Section 1 — Dashboard
- `PendingCustomerActionsWidget.js`: Converted to `useReducer`, added ERROR state + Retry button
- `Dashboard.js`: Removed orphaned `recentAIDocs` state and dead API fetch

### Category 1, Section 2 — Customers
- `backend/routes/customers.py`: Fixed `create_customer` tenant lookup (`{"tenant_id":...}` → `{"id":...}`)
- `backend/routes/customers.py`: Fixed `update_customer` readback to be tenant-scoped
- `frontend/src/pages/Customers.js`: Added `loadError` state + Retry button; webstores converted to `useReducer` with error state; URL param import dialog uses lazy initializer; `handleViewCustomer` uses `structuredClone`
- `frontend/src/pages/Quotes.js`: Added `?customer_id=` URL param support with customer filter chip + clear button; `loadData` converted to `useReducer`

---

*Last updated: 2026-06-07*
