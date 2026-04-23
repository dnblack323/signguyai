# Tier 2 — Section 2.1 Results (Customers CRUD)

Run timestamp: `2026-04-23T06:44:39Z`  
Environment: `REACT_APP_BACKEND_URL` (production preview URL)

---

- ✅ **2.1A** Create customer manually appears in list
  - Evidence: `POST /api/customers` then `GET /api/customers?search=<name>` returned created customer

- ✅ **2.1B** Search by name, email, phone works independently
  - Evidence: each search path returned the created customer ID

- ✅ **2.1C** Edit persists after refresh
  - Evidence: `PUT /api/customers/{id}` updated email/note; `GET /api/customers/{id}` reflected persisted values

- ✅ **2.1D** Delete customer keeps historical order identity
  - Evidence: after `DELETE /api/customers/{id}`, related order `GET /api/orders/{order_id}` still returned original `customer_name`

- ✅ **2.1E** Customer detail data paths valid (orders/jobs, invoices, totals, portal invite status)
  - Evidence: `GET /api/jobs?customer_id=...`, `GET /api/invoices?customer_id=...`, `GET /api/customers/{id}/summary`, and invite toggled `portal_enabled=true`

- ❌ **2.1F** Tax-exempt toggle to invoice tax-zero behavior
  - Evidence: generated invoice tax for both non-exempt and exempt test paths was `0`
  - Outcome: tested flow does not currently show customer-dependent tax behavior

- ⛔ **2.1G** Portal invite email arrival + customer login completion
  - Blocked reason: requires mailbox access and end-user portal login verification

---

Artifacts:
- Raw JSON: `/app/memory/TIER2_SECTION_2_1_RESULTS.json`
