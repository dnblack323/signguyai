# Wrap Command Center — QA & Manual Smoke-Test Reference

**Audience**: QA testers running a manual smoke pass before/after a deploy.
**Scope**: Phase 2A → 2F of the Wrap Command Center, plus the customer-portal
extension, the Dashboard widget, and the shop notification emails.
**Last updated**: 2026-05-18 (post launch-polish hardening pass).

---

## 0. How to log in

| Role | Email | Password | Lands on |
|------|-------|----------|----------|
| Admin / internal staff | `thesigntistslab@gmail.com` | `password123` | `/dashboard` |
| Customer portal | `taxtest_non@example.com` | `portal123` | `/customer-portal/dashboard` |

Live wrap fixture used by every example below:
- **Order**: `118b7377-687b-4a28-b42b-3c5f31da64c5` (ORD-0018)
- **Wrap item / job ticket**: `aa0387f8-ac70-4935-9bbc-33d03963e916`

---

## 1. Entry: OrderDetail → Wrap Command Center

| Item | Value |
|------|-------|
| Page | `/orders/{orderId}` |
| Action | Click the **Wrap Workflow** badge / "Open Wrap Command Center" button on a wrap-category line item. |
| Expected | Navigates to `/orders/{orderId}/items/{itemId}/wrap-command-center`. |
| Key testids | `order-item-wrap-trigger-{itemId}` |
| Must NOT happen | A non-wrap item must NOT show the trigger. |

---

## 2. Wrap Command Center route

| Item | Value |
|------|-------|
| Page | `/orders/{orderId}/items/{itemId}/wrap-command-center` |
| Expected | Page renders sticky header + tab nav + the active tab body. |
| Key testids | `wrap-command-center-page`, `wrap-command-header`, `wrap-tab-nav`, `wrap-cc-tab-content` |
| Must NOT happen | No separate standalone wrap dashboard. Reachable only from an OrderDetail wrap trigger. |

---

## 3. Wrap CC tab buttons (12 tabs)

All emit `data-testid="wrap-tab-{id}"` (from `WrapTabNavigation.js`).

| Tab id | Label | testid |
|--------|-------|--------|
| `overview`     | Overview                  | `wrap-tab-overview` |
| `vehicle`      | Vehicle Info              | `wrap-tab-vehicle` |
| `measurements` | Measurements & Coverage   | `wrap-tab-measurements` |
| `pricing`      | Pricing & Materials       | `wrap-tab-pricing` |
| `design`       | Design & Mockups          | `wrap-tab-design` |
| `contract`     | Contract & Approvals      | `wrap-tab-contract` |
| `inspection`   | Inspection                | `wrap-tab-inspection` |
| `production`   | Production                | `wrap-tab-production` |
| `install`      | Install                   | `wrap-tab-install` |
| `photos`       | Photos & Files            | `wrap-tab-photos` |
| `aftercare`    | Aftercare                 | `wrap-tab-aftercare` |
| `ai`           | AI Assistant              | `wrap-tab-ai` |

**Selector note for automation**: use the `data-testid` selectors above to avoid colliding with the top-nav text content (e.g. the global "Production Board" link in Orders nav).

---

## 4. Respond row (Wrap CC header)

| Item | Value |
|------|-------|
| Page | Wrap CC header — always visible |
| Action | Click each of the three buttons. |
| Expected | Each opens the existing internal page in the same tab. |
| Key testids | `wrap-header-respond-row`, `wrap-respond-open-order` → `/orders/{orderId}`, `wrap-respond-open-conversation` → `/admin-portal`, `wrap-respond-open-customer` → `/customers` |
| Must NOT happen | No new conversation/message system, no template picker. |

---

## 5. Photos & Files tab — uploads & PDFs

| Item | Value |
|------|-------|
| Page | Wrap CC → **Photos & Files** tab |
| Upload action | Pick category → pick file → toggle Customer-visible / Marketing-allowed → file uploads. |
| Expected | File appears in the category list with Open / Toggle-CV / Delete actions; image files thumbnail; counts on category tiles update. |
| Key testids | `photos-files-tab`, `files-select-category`, `files-upload-input`, `files-upload-notes`, `files-upload-toggle-customer_visible`, `files-upload-toggle-marketing_allowed`, `files-grid`, `files-card-{file_id}`, `files-download-{file_id}`, `files-toggle-cv-{file_id}`, `files-delete-{file_id}`, `files-cat-tile-{slug}` |
| PDF generators (in same tab) | `files-gen-receipt-btn` (Customer Receipt → Signed Documents, customer_visible=true), `files-gen-aftercare-btn` (Aftercare → Aftercare Documents, customer_visible=true), `files-gen-packet-btn` (Final Packet → Final Packets, **internal-only**) |
| Expected after PDF generation | The generated PDF appears in the matching category list as a downloadable wrap_file. |
| Must NOT happen | Final Packet must NOT be customer_visible. File size limit 25MB. |

---

## 6. Visual inspection diagram

| Item | Value |
|------|-------|
| Page | Wrap CC → **Inspection** tab |
| Action | Pick a Vehicle Diagram Type → click `insp-diagram-arm-btn` → click on the SVG canvas → fill marker form → save. |
| Expected | A numbered circle appears on the diagram at the click position. Clicking the circle highlights the matching list row, and clicking a list row highlights the circle. |
| Key testids | `insp-diagram-svg`, `insp-diagram-arm-btn`, `insp-diagram-canvas`, `insp-diagram-marker-{id}`, `insp-marker-row-{id}`, `insp-marker-add-form`, `insp-marker-add-pos`, `insp-toggle-customer_visible`, `insp-toggle-customer_acknowledged` |
| Persistence | Saved markers carry `x_percent`, `y_percent`, `marker_label`. After refresh, markers re-render at their stored positions. |
| Customer-visible toggle | Without this, the customer portal inspection card is hidden. |

---

## 7. Customer Portal — Vehicle Wrap Project card

| Item | Value |
|------|-------|
| Page | `/customer-portal/orders/{orderId}` (existing Customer Portal — NOT a separate wrap portal) |
| Visibility | Card appears ONLY when the order contains at least one wrap-category item. |
| Key testids | `portal-wrap-project-{ticket_id}`, `portal-wrap-quote-card`, `portal-wrap-proof-card`, `portal-wrap-contract-card`, `portal-wrap-inspection-card`, `portal-wrap-aftercare-card`, `portal-wrap-receipts-card`, `portal-wrap-after-photos-card`, `portal-wrap-file-{file_id}`, `portal-wrap-file-open-{file_id}` |
| Customer-safe content only | Vehicle, wrap type, install date, quoted price (NO profit/margin/cost), customer-visible files, customer-visible inspection summary (count only — never the damage notes). |
| Must NOT happen | NO public unauthenticated `/customer/wrap-care/:token` route. NO internal-only files. NO profit/margin/cost. NO damage notes. NO internal install/inspection notes. |

---

## 8. Customer Portal — Wrap actions

All 6 buttons hit existing portal JWT-authenticated endpoints under `/api/portal/orders/{job_id}/wrap/{ticket_id}/*`.

| Button | testid | Endpoint | Idempotent? |
|--------|--------|----------|-------------|
| Approve Quote | `portal-wrap-approve-quote-btn` | `POST .../approve-quote` | ✅ Yes |
| Approve Artwork | `portal-wrap-approve-proof-btn` | `POST .../approve-proof` | ✅ Yes |
| Request Revision (notes form) | `portal-wrap-request-revision-btn` + `portal-wrap-revision-notes` + `portal-wrap-revision-submit` | `POST .../request-revision` | ❌ Fires every time (unique notes) |
| Sign / Acknowledge Contract | `portal-wrap-acknowledge-contract-btn` + `portal-wrap-contract-signedby` + `portal-wrap-contract-submit` | `POST .../acknowledge-contract` | ✅ Yes |
| Acknowledge Inspection | `portal-wrap-acknowledge-inspection-btn` (only renders when `inspection.customer_visible=true`) | `POST .../acknowledge-inspection` | ✅ Yes |
| Acknowledge Aftercare | `portal-wrap-acknowledge-aftercare-btn` | `POST .../acknowledge-aftercare` | ✅ Yes |

**Expected for every action**: button transitions to a green badge (e.g. "Approved", "Signed", "Acknowledged", "Received") on success. `wrap_data` updates persist after a page reload. Cross-tenant attempts return 404. Non-wrap items return 400.

---

## 9. Dashboard — Pending Customer Actions widget

| Item | Value |
|------|-------|
| Page | `/dashboard` (admin/internal staff only) |
| Position | Right column, between "Quick Actions" and "Recent AI Documents". |
| Key testids | `pending-customer-actions-widget`, `pending-actions-loading`, `pending-actions-empty`, `pending-actions-list`, `pending-actions-row-{ticket_id}`, `pending-actions-badge-{ticket_id}-{code}`, `pending-actions-open-order-{ticket_id}` → `/orders/{order_id}`, `pending-actions-open-wrap-{ticket_id}` → `/orders/{order_id}/items/{ticket_id}/wrap-command-center`, `pending-actions-open-admin-{ticket_id}` → `/admin-portal` |
| Action codes shown | `proof_pending`, `revision_requested`, `contract_pending`, `quote_pending`, `inspection_pending`, `aftercare_pending` |
| API | `GET /api/wrap/pending-customer-actions` (authenticated). |
| Must NOT happen | NO write actions. NO templates. NO AI dispatch. Read-only + links to existing pages. |

---

## 10. Shop notification emails

Triggered by `services/wrap_notifications.send_wrap_portal_action_notification`. Dispatched from each customer-portal action endpoint AFTER the wrap_data update succeeds. Failure NEVER blocks the customer action.

| Action key | Subject | Idempotent? |
|------------|---------|-------------|
| `proof_approved`           | `Wrap Proof Approved — Order #{order_number}` | ✅ Yes |
| `revision_requested`       | `Wrap Revision Requested — Order #{order_number}` | ❌ No |
| `contract_signed`          | `Wrap Contract Signed — Order #{order_number}` | ✅ Yes |
| `quote_approved`           | `Wrap Quote Approved — Order #{order_number}` | ✅ Yes |
| `inspection_acknowledged`  | `Wrap Inspection Acknowledged — Order #{order_number}` | ✅ Yes |
| `aftercare_acknowledged`   | `Wrap Aftercare Acknowledged — Order #{order_number}` | ✅ Yes |

**Email body**: shop name, customer name + email, order #, item name, wrap type, vehicle, timestamp, action-specific extra rows. Body **MUST NOT** contain profit, margin, material cost, labor cost, internal/damage/install notes.

**Email deep-link buttons**: Open Order → `/orders/{order_id}`, Open Wrap Command Center → `/orders/{order_id}/items/{ticket_id}/wrap-command-center`, Respond in Admin Portal → `/admin-portal`. All href values are HTML-escaped (hardening pass).

**Recipient resolution**: `tenant.notification_email > business_email > email > owner_email`. No recipient → log + skip.

---

## 11. AI placeholder cards (6 approved groups — all disabled)

All render via `WrapAIHelperCard` with `disabled={true}` (default). Greyed style, "Coming soon" chip, buttons carry the `disabled` HTML attribute, click is gated.

| Tab | AI card title | testid |
|-----|---------------|--------|
| Vehicle Info             | **Vehicle AI**                          | `wrap-ai-helper-card-vehicle-ai-helper` |
| Pricing & Materials      | **Quote Builder AI**                    | `wrap-ai-helper-card-pricing-ai-helper` |
| Design & Mockups         | **Design Direction & Mockup AI**        | `wrap-ai-helper-card-design-ai-helper` |
| Contract & Approvals     | **Contract Draft AI**                   | `wrap-ai-helper-card-contract-ai-helper` |
| Inspection               | **Inspection Summary & Report AI**      | `wrap-ai-helper-card-insp-ai-helper` |
| AI Assistant             | **Workflow Completion Summary AI**      | `wrap-ai-helper-card-ai-assistant-helper` |

(The exact testid slug is derived from the `testId` prop — use a partial match in automation: `wrap-ai-helper-card-*`.)

**Tabs with NO AI helper card** (must not render): Overview, Measurements & Coverage, Production, Install, Photos & Files, Aftercare.

**Must NOT happen**: no AI API call when clicking an AI button. No real LLM dispatch in this phase.

---

## 12. Final manual checklist

Walk top-to-bottom for a release-readiness pass:

- [ ] Wrap item on an order opens the Wrap Command Center route.
- [ ] Vehicle Info tab saves and reloads correctly.
- [ ] Measurements & Coverage areas add/edit/delete; total billable sqft recalculates.
- [ ] Pricing & Materials → "Apply to Order" updates the parent order's total without disturbing payments.
- [ ] Design / Proof: approve, request revision, send proof all work and timestamps stick.
- [ ] Contract: send, acknowledge, signed_at all persist; approvals mirror flips.
- [ ] Inspection: visual diagram click-to-add works, markers persist with x/y%, customer-visible toggle gates portal exposure.
- [ ] Photos & Files: upload across categories, toggle customer-visible / marketing-allowed, delete, image thumbnail loads.
- [ ] PDFs: Customer Receipt + Aftercare appear as customer-visible wrap_files; Final Packet is internal-only.
- [ ] Customer Portal → opens the wrap order → "Vehicle Wrap Project" card shows ONLY customer-safe data + customer-visible files.
- [ ] Customer portal actions: approve quote / approve proof / request revision / sign contract / acknowledge inspection (when shared) / acknowledge aftercare all succeed and update both the portal card and the Wrap CC backend state.
- [ ] Each customer action triggers a shop notification email (when SendGrid is configured) with the 3 deep-link buttons. Repeat actions on already-completed states do NOT spam duplicate emails.
- [ ] Dashboard `Pending Customer Actions` widget lists the stalled wrap tickets and the Open Order / Wrap CC / Admin Portal links open the right pages.
- [ ] AI helper buttons (6 approved groups) remain disabled with "Coming soon" chip. No AI request is fired.
- [ ] A non-wrap order item is completely unaffected: no Vehicle Wrap Project card in the portal, no wrap badge, no /wrap/items endpoints reachable for that ticket id.

---

## Quick API smoke (curl)

```bash
API=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
TOKEN=$(curl -s -X POST "$API/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"thesigntistslab@gmail.com","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 1. Pending Customer Actions
curl -s "$API/api/wrap/pending-customer-actions" -H "Authorization: Bearer $TOKEN"

# 2. Customer-facing summary preview
curl -s "$API/api/wrap/items/aa0387f8-ac70-4935-9bbc-33d03963e916/customer-facing-summary" \
  -H "Authorization: Bearer $TOKEN"

# 3. Customer portal login
PTOKEN=$(curl -s -X POST "$API/api/portal/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"taxtest_non@example.com","password":"portal123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 4. Order detail must include wrap_items[]
curl -s "$API/api/portal/orders/118b7377-687b-4a28-b42b-3c5f31da64c5" \
  -H "Authorization: Bearer $PTOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print('wrap_items count:', len(d.get('wrap_items',[])))"
```

---

## Automated regression command

```bash
cd /app/backend && python3 -m pytest \
  tests/test_iteration148_wrap_phase2f.py \
  tests/test_iteration150_wrap_notifications.py \
  tests/test_iteration151_launch_polish.py -q
# Expected: 66 passed
```
