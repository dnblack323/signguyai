# SignGuy AI - Product Requirements Document

## Original Problem Statement
Full-stack business management app for sign/graphics shops: customer management, quoting, invoicing, job tracking, production workflow, employee time tracking, payroll, webstores with Stripe-powered checkout, and AI-driven business assistance.

## Core Modules
- **CRM / Quotes / Invoices / Jobs** — standard business workflow.
- **Production Workflow** — job tickets, production tasks, drawings, signatures.
- **Employee Portal + Timeclock + Payroll** — punch tracking, shift state, payroll worksheets.
- **Webstores** — per-tenant storefronts, products, Stripe Checkout via Connect, orders → jobs.
- **AI Business Assistant** — Phase 5 (saved commands, routines, modes, bulk action previews).
- **Stripe Connect (platform-owned) + Stripe Connect (tenant onboarding)** — platform billing + tenant payouts.

## Architecture — Stripe Service Layer
As of 2026-04-25, all Stripe business logic is centralised in `backend/services/stripe_service.py`:
- Platform fee schedule, `get_stripe_mode()`, `get_tenant_tier()`
- Connect account checkout-status cache (`get_stripe_account_checkout_status`)
- DB helpers: `find_invoice_document`, `record_stripe_event`, `mark_invoice_paid`
- Webstore finalization: `finalize_webstore_stripe_checkout` (lazy-imports webstore types to avoid circular dep)

`routes/stripe_connect.py` and `routes/webstores.py` are thin consumers of this service.
Invoice Stripe payments (`POST /stripe-connect/invoice/{id}/pay`) are independently usable with no webstore dependency.

## Implemented (CHANGELOG)
- 2026-05-21 — **Customer Portal: Webstores Tab for Assigned Owners (COMPLETE)**:
  - **Backend** (`routes/portal.py`): Added `GET /api/portal/webstores`, `GET /api/portal/webstores/{id}`, `POST /api/portal/webstores/{id}/stripe-onboarding`, `POST /api/portal/webstores/{id}/stripe-refresh`, `POST /api/portal/webstores/{id}/stripe-login-link`. Assignment rule: `webstore.owner_email == customer.email` (case-insensitive) AND `tenant_id` matches. All endpoints enforce assignment server-side via `_portal_load_assigned_webstore` (returns 404 — never leaks existence).
  - **Sanitization** (`_sanitize_webstore_for_portal_owner`): whitelist-only output — strips `tenant_id`, `owner_user_id`, and raw `locked_settings` cost/profit fields. Only safe locked-settings keys (`shipping_fee`, `handling_fee`, `shipping_handling_*`) are exposed read-only.
  - **Dashboard** (`/api/portal/dashboard`): added `stats.assigned_webstores` + top-level `has_webstores`. Counter uses case-insensitive regex so nav-tab visibility never disagrees with the list endpoint.
  - **Stripe Express onboarding**: reuses the exact same `webstore_owners.py` Stripe Express flow (Account.create with transfers+card_payments capabilities, AccountLink, login_link). NO duplicate Stripe code.
  - **Frontend** (`PortalDashboard.js`): `PortalLayout` fetches `/api/portal/webstores` once per mount and conditionally inserts a `Webstores` nav item (data-testid=`portal-nav-webstores`) between Appointments and Profile.
  - **Frontend** (`PortalWebstores.js`): new page at `/customer-portal/webstores`. Per-store card with: store name + type + status badge, public store link + Copy + QR (data-testid=`portal-store-qr`), Stripe onboarding/refresh/dashboard buttons, Event Details (Event Stores), Fundraiser Summary (donations/profit_allocated/total_raised + progress bar gated on `fundraiser_enabled && show_progress_bar && goal > 0`), Questionnaire status block, read-only Financial Summary (with Lock badge), Recent Orders. All financial controls clearly marked read-only.
  - **App.js**: added `<Route path='/customer-portal/webstores' element={<PortalWebstores />} />`.
  - **Tested**: `/app/test_reports/iteration_158.json` → **100% backend (16/16), 100% frontend**. Cross-tenant isolation verified — a portal user from tenant T1 cannot see a webstore in tenant T2 even if the email matches. Sanitization sweep confirmed no `tenant_id` / cost / profit fields leak.

- 2026-05-21 — **Part 4: Event Store Fundraiser Money Logic & Checkout Donations (COMPLETE)**:
  - **Backend** (`routes/stripe_connect.py`): `WebstoreCheckoutRequest` accepts optional `donation_amount`. `create_webstore_checkout` now:
    - Server-side validates donations (rejects if `allow_checkout_donations=false`; requires preset match or `allow_custom_donation=true`).
    - Pulls shipping/handling from `webstore.locked_settings` only — honors `shipping_handling_enabled` bundle, otherwise sums `shipping_fee` + `handling_fee`. Adds a Stripe line item.
    - Server-computes `profit_allocation_amount` from store config (`profit_allocation_type=percentage|fixed_per_item|manual`, `fundraiser_cap_amount`). Never trusts the frontend.
    - Stores `donation_amount`, `profit_allocation_amount`, `shipping_handling_amount`, `fundraiser_enabled` in Stripe metadata + the `payment_transactions` row.
  - **Backend** (`services/stripe_service.py`): `finalize_webstore_stripe_checkout` passes donation/profit-allocation/shipping-handling through to `WebstoreOrderCreate`.
  - **Backend** (`routes/webstores.py`):
    - `WebstoreOrder` model: added `donation_amount`, `profit_allocation_amount`, `shipping_handling_amount`, `grand_total`, `fundraiser_totals_applied` fields.
    - `WebstoreOrderCreate` accepts the same fields (with `ge=0`).
    - New helpers: `_parse_donation_presets`, `_public_locked_settings`, `_compute_shipping_handling_total`, `compute_event_profit_allocation`, `_apply_fundraiser_totals` (idempotent flag-guarded increment).
    - `create_webstore_order` runs server-side recomputation of profit allocation (`min(supplied, server_recomputed)`), persists donation/allocation/grand_total on the order, and rolls fundraiser totals into `total_donations`, `total_profit_allocated`, `total_raised` exactly once via the `fundraiser_totals_applied` flag.
    - Idempotency-replay branch also back-fills fundraiser totals if a prior partial run missed them.
    - Defensive: `base_cost = float(product.get('base_cost') or 0)` and `unit_price = … or 0` so legacy products without `base_cost` no longer 500.
    - Public storefront sanitizer (`sanitize_webstore_for_public`) now exposes `allow_checkout_donations`, `donation_amount_options`, `allow_custom_donation`, plus parsed `donation_presets` and a pre-sanitized `locked_settings` (ONLY shipping/handling — cost/profit/split fields stripped).
  - **Frontend** (`pages/Storefront.js`):
    - Reads `locked_settings.shipping_handling_*` (and `shipping_fee`/`handling_fee`) to compute the server-locked S&H fee — displays it as a line in the order summary.
    - Donation block (`data-testid=checkout-donation-block`) renders when `allow_checkout_donations=true`. Presets from `donation_presets`. Custom amount input when `allow_custom_donation=true`.
    - Fundraiser progress bar (`data-testid=fundraiser-progress-bar`) renders ONLY when `fundraiser_enabled && show_progress_bar && fundraiser_goal_amount > 0`. Uses `total_raised / fundraiser_goal_amount`.
    - Order summary shows shipping/handling row, donation row, and grand total (`= subtotal + S&H + donation`).
    - Submits `donation_amount` to the checkout API.
  - **Tested**: `/app/test_reports/iteration_157.json` → **100% backend (6/6), 100% frontend**. Idempotent fundraiser totals verified end-to-end (second call with same `idempotency_key=stripe:<sid>` does NOT double-count). Public storefront verified to NEVER leak `base_item_cost`, `production_cost`, `store_owner_profit`, `profit_split`, `profit_allocation_percentage`.

- 2026-05-20 — **Fundraiser Field Structure Fix (Part 3 fix) (COMPLETE)**:
  - Fixed incorrect `SAFE_MAP` in `apply_questionnaire_answers_to_event_store`: "Fundraiser Name" now maps to `fundraiser_name` (not `event_name`), "Fundraiser Description" → `fundraiser_description`, "Fundraiser Goal Amount" → `fundraiser_goal_amount` (with float coercion). Added 11 more fundraiser mappings with proper type coercion (bool: yes/no→True/False, float: string→float).
  - Added 17 dedicated fundraiser fields to `Webstore`, `WebstoreCreate`, `WebstoreUpdate`: `fundraiser_enabled`, `fundraiser_name`, `fundraiser_description`, `fundraiser_goal_amount` (optional), `show_progress_bar`, `allow_checkout_donations`, `donation_amount_options`, `allow_custom_donation`, `profit_allocation_enabled`, `profit_allocation_type`, `profit_allocation_percentage`, `fixed_amount_per_item`, `fundraiser_cap_amount`, `include_donations_in_progress`, `include_profit_allocation_in_progress`, `show_total_raised_publicly`, `show_supporter_names`. Plus aggregate totals: `total_donations`, `total_profit_allocated`, `manual_adjustments`, `total_raised`.
  - Fixed missing `WebstoreUpdate` class declaration (accidentally removed in prior edit — caused ruff F821 lint error).
  - Updated `WEBSTORE_PUBLIC_FIELDS` to include fundraiser public fields.
  - Frontend (`Webstores.js`): Added `fundraiserEdits` state, `handleSaveFundraiserSettings`, Fundraiser Settings card in Event Store settings tab with all fundraiser fields. Progress bar toggle disables when goal amount is empty.
  - **Tested**: iteration_156.json → **27/27 backend PASS, 100% frontend PASS**.

- 2026-05-20 — **Part 3: Event Store Questionnaire Integration (COMPLETE)**:
  - **Backend** (`models/questionnaires.py`):
    - Added 18 fundraiser questions as Section 4.5 to `event_web_store_setup` template (orders 44-61): fundraiser_enabled, fundraiser_name, fundraiser_description, fundraiser_goal_amount (optional), show_progress_bar, allow_checkout_donations, donation_amount_options, allow_custom_donation, profit_allocation_enabled, profit_allocation_type, profit_allocation_percentage, fixed_amount_per_item, fundraiser_cap_amount, include_donations_in_progress, include_profit_allocation_in_progress, show_total_raised_publicly, show_supporter_names. Template now has 87 questions total.
    - Shifted existing Section 5 (Stripe Connect) orders 44→62 and Section 6 (Final Approval) orders 53→71.
    - Added `webstore_id`, `prefill_answers`, `locked_answer_ids`, `last_sent_at` to `Questionnaire` model.
  - **Backend** (`routes/webstores.py`):
    - `GET /{webstore_id}/questionnaire` — returns questionnaire status (linked/unlinked, status, last_sent_at, response count, latest response).
    - `POST /{webstore_id}/questionnaire/send` — idempotent: creates questionnaire from template (once per webstore), prefills event fields (Event Name, location, dates) and locks tenant financial fields (profit_per_item → locked from `store_owner_profit`), activates questionnaire, sends email via SendGrid. Reusing same questionnaire_id on re-send.
    - `POST /{webstore_id}/questionnaire/apply-answers` — maps safe questionnaire answers to Event Store fields. Never touches `locked_settings`. Returns applied_fields and suggested_changes for admin review.
  - **Frontend** (`context/AppContext.js`): Added `getWebstoreQuestionnaire`, `sendWebstoreQuestionnaire`, `applyWebstoreQuestionnaireAnswers`.
  - **Frontend** (`PublicQuestionnaire.js`): Applies `prefill_answers` on load, renders `locked_answer_ids` questions as read-only with amber Lock + "Set by store provider" badge. Passes `webstore_id` in submission. Locked fields skip required validation.
  - **Frontend** (`Webstores.js`): Questionnaire status card in Event Store settings tab (status, last sent, responses, linked badge). Send dialog with email/message override + amber lock notice. "Resend Questionnaire", "View Form", "Apply Safe Answers" buttons.
  - **Tested**: iteration_155.json → **23/23 backend PASS, 17/17 frontend PASS**.

- 2026-05-20 — **Event Store Foundation + Tenant-Controlled Locked Settings (COMPLETE)**:
  - **Backend** (`routes/webstores.py`):
    - Added `EVENT = "event"` to `WebstoreType` enum (4th type alongside business, fundraiser, creator).
    - Fixed `_normalize_webstore_doc`: added EVENT to the valid type set so event stores are no longer coerced to "business".
    - Added `LockedSettings` Pydantic model (tenant-controlled: base_item_cost, production_cost, retail_price, store_owner_profit, profit_split, setup_fee, shipping_fee, handling_fee, shipping_handling_enabled/fee/label/description).
    - Added event-specific fields to `Webstore`, `WebstoreCreate`, `WebstoreUpdate`: event_name, event_type, event_start_date, event_end_date, event_location, order_deadline, pickup_delivery_date, pickup_delivery_instructions, auto_close_after_deadline, allow_late_orders.
    - Added `locked_settings: LockedSettings` to Webstore model; `Optional[Dict]` in Create/Update.
    - Added `store_slug` field with `_generate_unique_slug()` helper (async uniqueness check per tenant).
    - `WEBSTORE_PUBLIC_FIELDS` updated: event public fields added, locked_settings intentionally excluded (security).
    - `_normalize_webstore_doc` ensures `locked_settings` is always a dict before Pydantic coercion.
  - **Frontend** (`Webstores.js`):
    - Added Event Store as 4th storeType (CalendarDays icon, orange badge).
    - Extended `formData` / `resetForm` with all event + locked_settings fields.
    - Added empty-string→null sanitization for locked_settings in `handleCreateStore` (prevents 500 on creation).
    - Create dialog: Event-specific section (event_name, event_type, start/end dates, location, order_deadline, pickup fields, auto_close/allow_late toggles).
    - Create dialog: Admin-Controlled Financial Settings section (8 fee/cost fields + shipping_handling bundle, "Tenant Only" badge).
    - Detail Settings tab: Event Settings card (edit + save), Admin-Controlled Financial Settings card (edit + save).
    - Added `lockedEdits`, `eventEdits`, `savingLocked`, `savingEvent` state + `handleSaveEventSettings`, `handleSaveLockedSettings` handlers.
  - **Tested**: iteration_154.json → **16/16 backend PASS, 100% frontend PASS**. Bug found and fixed (empty locked_settings empty-string validation error). All existing store types unaffected.
  - **Frontend** (`PricingCalculator.js`): Added `computeBannerCompareMethods()` function using foundationDefaults (material cost_per_sqft, sell_rate_per_sqft, labor_rates, category waste/minutes/minimum), `bannerBreakdownExpanded` state, updated `BANNER_ADDON_DEFAULTS` with `default_labor_minutes` and `rate_source`; added full Compare Methods UI panel at end of banners case block with two-column Price Per SqFt vs Detailed M+L comparison, recommended price (higher of two), Use/Use Recommended buttons (sets overrideEnabled+overridePrice), manual override input with clear button, expandable detailed breakdown showing all formula inputs.
  - Formula: PricePerSqFt = retailRate×sqft+addonFees (max minimum). Detailed = wasteAdjCost×sqft + laborMin/60×prodRate + addonFees (max minimum). Recommended = max of both.
  - **Tested**: iteration_153.json → **20/20 frontend PASS**. Math verified: Small Pole Banner = $60.00/$35.08/$60.00 recommended. Large Pole = $95.00/$39.80/$95.00. All Use/override/breakdown features verified.
- 2026-05-20 — **Phase 2A Step 2B — Banner Calculator Integration (COMPLETE)**:
  - **Backend** (`routes/pricing.py`): Auto-injects 4 starter banner materials (13 oz, 18 oz, Standard Mesh, Standard Fabric) into `pricing_configuration` when banner settings are first saved and no banner materials exist yet. Prevents duplicates by checking existing `banner_material` category count.
  - **Frontend** (`PricingCalculator.js`): Added `BANNER_TEMPLATES` + `BANNER_ADDON_DEFAULTS` constants; updated `getBannerMaterialOptions()` fallback to use correct starter keys; added `applyBannerTemplate()` function; added Quick Templates section (Small Pole Banner 18×36in, Large Pole Banner 24×48in); added Product Type text field; added Add-ons section (8 add-ons: Hems, Grommets, Brackets, Other Hardware, Pole Pockets, Design, Setup Fee, Install) with editable fees; add-ons total included in Final Price; templates auto-inject Pole Pockets add-on.
  - **Tested**: iteration_152.json → **15/15 frontend PASS**. All banner features verified: material dropdown from DB, both templates fill correct dimensions and material, add-ons auto/manual, add-ons affect final price, non-banner calculators unaffected, Banner Wizard accessible.
- 2026-05-18 — **Wrap Command Center — Tiny Hardening Pass**:
  - **Item 1**: `_render_html` in `services/wrap_notifications.py` now `html.escape(..., quote=True)`s every href before rendering. Verified by injecting a `"><script>` payload — output safely contains `&quot;&gt;&lt;script&gt;`.
  - **Item 2**: Already done — `WrapTabNavigation.js` line 18 already emits `data-testid={`wrap-tab-${t.id}`}` for every Wrap CC tab button. Previous iter151 "collision" was a top-level nav text-content matcher, not a missing testid.
  - **Tested**: `pytest tests/test_iteration148_*.py tests/test_iteration150_*.py tests/test_iteration151_*.py` → **66/66 PASS (11.69s)**. No regressions.
- 2026-05-18 — **Wrap Command Center — Launch Polish (Phase 2F follow-up #2)**:
  - **Email deep links** — `services/wrap_notifications._render_html` now renders 3 inline buttons in every shop notification: Open Order → `/orders/{order_id}`, Open Wrap Command Center → `/orders/{order_id}/items/{ticket_id}/wrap-command-center`, Respond in Admin Portal → `/admin-portal`. App URL resolves from `tenant.app_url > tenant.portal_url > FRONTEND_URL > REACT_APP_BACKEND_URL`. No app_url available → skips buttons cleanly.
  - **Wrap CC respond row** — new `wrap-header-respond-row` strip in `WrapCommandHeader` with three Link buttons: Open Order, Open Conversation (`/admin-portal`), Open Customer (`/customers`). Pure links to existing routes — NO template picker, NO message-type dropdown, NO new communication system.
  - **Pending Customer Actions Dashboard widget** — new `GET /api/wrap/pending-customer-actions` endpoint returns tenant-scoped list of wrap tickets where action codes apply (proof_pending, revision_requested, contract_pending, quote_pending, inspection_pending, aftercare_pending). New `PendingCustomerActionsWidget` rendered in right column of Dashboard between `QuickActions` and `RecentAIDocumentsWidget`. Read-only; each row links to existing Order, Wrap CC, and Admin Portal pages.
  - **AI placeholder cleanup** — `WrapAIHelperCard` now defaults to `disabled=true`: grey style, buttons get `disabled` attr, "Coming soon" chip in header, no toast on click. Slug-derived testid `wrap-ai-helper-card-{group}` for stable automation. AI helper REMOVED from MeasurementsTab, ProductionTab, InstallTab, AftercareTab, PhotosFilesTab, OverviewTab (right sidebar collapsed to single column on those tabs). Surviving 6 approved groups renamed: Vehicle AI, Quote Builder AI, Design Direction & Mockup AI, Contract Draft AI, Inspection Summary & Report AI, Workflow Completion Summary AI.
  - **Tested**: testing_agent_v3_fork iteration 151 → **13/13 new + 53/53 regression = 66/66 backend pass**, ~95% frontend pass (selector-stability nits already addressed by adding testids to `WrapAIHelperCard`). Zero bugs. New test file `/app/backend/tests/test_iteration151_launch_polish.py`.
- 2026-05-18 — **Wrap Command Center — Shop Email Notifications (Phase 2F follow-up)**:
  - New helper `services/wrap_notifications.py` (`send_wrap_portal_action_notification`) builds + dispatches a SendGrid email via the existing `EmailService` on every customer portal wrap action.
  - **6 actions wired in `routes/portal.py`** with idempotency guards (false→true transition only): `approve-proof` → "Wrap Proof Approved", `acknowledge-contract` → "Wrap Contract Signed", `approve-quote` → "Wrap Quote Approved", `acknowledge-inspection` → "Wrap Inspection Acknowledged", `acknowledge-aftercare` → "Wrap Aftercare Acknowledged". `request-revision` → "Wrap Revision Requested" fires every time (each request has unique notes).
  - **Recipient resolution**: `tenant.notification_email > business_email > email > owner_email`. No email on tenant → log + skip, customer action still 200.
  - **Failure isolation**: dispatch is wrapped in broad try/except + logger.warning. SendGrid not configured / API failure / Mongo error in helper → customer action still returns 200 with the customer-facing summary.
  - **Body safety**: only safe fields render (shop name, customer name+email, order #, item name, wrap type, vehicle, timestamp, action-specific extras). No profit/margin/material cost/labor cost/internal/damage/install notes leak — enforced by construction.
  - **Tested**: testing_agent_v3_fork iteration 150 → 19/19 new tests + 34/34 regression (test_iteration148) = **53/53 backend pass** (5.03s + 6.18s). Frontend untouched. New test file: `/app/backend/tests/test_iteration150_wrap_notifications.py`.
- 2026-05-18 — **Wrap Command Center Phase 2F (Polish + Customer Portal Integration)**:
  - **Backend refactor**: `routes/wrap.py` split into a `routes/wrap/` package — `__init__.py` aggregates `core.py` (all Phase 1-2E logic) + `files.py` + `portal.py` + `pdfs.py` sub-routers under the same `/wrap` prefix. All existing endpoint paths and response shapes preserved.
  - **Visual damage diagram**: New `WrapVehicleDiagram` SVG component (10 generic vehicle outlines). Click-to-arm then click-to-add marker captures `x_percent`/`y_percent` (0-100). New `DamageMarker.x_percent/y_percent/marker_label` fields persist round-trip via existing POST/PUT `inspection/damage-markers`. Selected marker syncs between SVG circle and list row. Severity-color-coded.
  - **Inspection customer-visibility flag**: New `inspection.customer_visible` (bool) gates whether the inspection report is exposed in the customer portal. Frontend `insp-toggle-customer_visible`. Default False.
  - **Real Photos & Files (`wrap_files` collection)**: New CRUD endpoints `GET/POST/PUT/DELETE /wrap/items/{id}/files` + `GET /files/{id}/content`. 14 categories (Customer Uploads, Logo Files, Vehicle Photos, Inspection Photos, Damage Photos, Mockups, Proofs, Print Files, Before/During/After Photos, Signed Documents, Aftercare Documents, Final Packets). Per-file `customer_visible` + `marketing_allowed` flags. 25MB cap, MIME whitelist (images/video/audio + PDF + Office + common design files). Uses existing `services/object_storage`. Full frontend rewrite of `PhotosFilesTab.js` with upload form, category tiles, image previews, toggle/delete actions.
  - **PDF generators (reportlab)**: 3 endpoints — `POST /wrap/items/{id}/pdfs/customer-receipt` (stored as `Signed Documents`, customer_visible=true), `/pdfs/aftercare` (stored as `Aftercare Documents`, customer_visible=true), `/pdfs/final-packet` (stored as `Final Packets`, customer_visible=false / internal-only). Generated PDFs are stored as wrap_files and downloadable via the same content endpoint.
  - **Customer Portal integration (NO separate portal)**: `GET /api/portal/orders/{id}` now attaches a `wrap_items[]` array (one entry per wrap-category ticket) with the safe customer-facing payload from `routes/wrap/portal.py:build_customer_facing_summary()`. Inspection block is only exposed when `inspection.customer_visible=true`. Pricing block only exposes `quoted_price` + `computed_at` (NO profit/margin/material cost/labor cost). Files filtered to `customer_visible=true` only. Internal notes / damage notes never exposed.
  - **6 customer portal action endpoints** (all under existing portal JWT auth via `get_current_portal_customer`, all verify the order belongs to the customer):
    - `POST /portal/orders/{job_id}/wrap/{ticket_id}/approve-proof`
    - `POST .../request-revision` (notes appended to `design.revision_notes` via aggregation-pipeline update — handles legacy string-shape data)
    - `POST .../acknowledge-contract` (signed_by + accepted_terms)
    - `POST .../approve-quote`
    - `POST .../acknowledge-inspection` (returns 400 if `inspection.customer_visible` is False)
    - `POST .../acknowledge-aftercare`
    - `GET .../files/{file_id}/content` (enforces customer_visible=true AND order ownership)
  - **Frontend customer portal**: New `PortalWrapProjectCard` rendered inside the existing `PortalOrderDetail` page when `order.wrap_items` exists. Card shows quote/proof/contract/inspection/aftercare cards with their respective action buttons, terms summary expand, care-instruction expand, and customer-visible file viewers grouped by category.
  - **Negative confirmations**: NO public unauthenticated wrap-care route. NO separate `/customer/wrap-care/:token` page. NO new token system. All wrap customer flows reuse existing portal JWT auth.
  - **Tested**: `testing_agent_v3_fork` iteration 148 → 33/34 backend pass + 100% frontend; iteration 149 retest → 34/34 backend pass after pipeline-update fix to `request-revision`. Phase 2A-2E regression intact.
  - **New test file**: `/app/backend/tests/test_iteration148_wrap_phase2f.py` (34 tests, 7.46s).
- 2026-05-18 — **Wrap Command Center Phase 2E (Inspection + Aftercare + Overview + AI Assistant shell + Production Board light mirror)**: 5 new endpoints in `routes/wrap.py`: `PUT /inspection`, `POST/PUT/DELETE /inspection/damage-markers[/{id}]`, `PUT /aftercare`. `wrap_data.inspection` holds {inspection_status, vehicle_diagram_type, inspected_by, inspection_date, customer_acknowledged + _at, inspection_notes, damage_markers[]} with DAMAGE_TYPES/SEVERITIES validation and 4 INSPECTION_STATUSES. `wrap_data.aftercare` holds {aftercare_status, aftercare_template, sent_by, aftercare_sent + _at, customer_viewed + _at, customer_acknowledged + _at, aftercare_notes, followup_24h/_7d/_30d + each _at} with 7 AFTERCARE_STATUSES. **Mirror & auto-flip rules**: inspection.customer_acknowledged → approvals.inspection_acknowledged + status='acknowledged'; aftercare_sent → approvals.aftercare_sent + status='sent'; viewed → 'viewed'; acknowledged → 'acknowledged'. All `_at` timestamps idempotent (true preserves original ts; false clears). `pipeline_state` extended with inspection_active/complete, aftercare_active/complete, and workflow_complete (install_complete AND complete AND aftercare_complete). **Production Board light mirror**: `_sync_wrap_to_production_board` upserts a SINGLE row keyed by (tenant_id, job_ticket_id, source='wrap_command_center') — never duplicates, maps wrap stages to PB stages. New frontend tabs: `InspectionTab.js`, `AftercareTab.js`, `OverviewTab.js` (reads real wrap_data — quoted/balance/vehicle/coverage/pricing/pipeline chips, no hardcoded values), `AIAssistantTab.js` (rule-based summaryHelpers only, zero LLM dispatch — health status, next-action, profit-risk, 3 ai-comm-* buttons, 9 ai-quicklink-* tabs, all helper buttons are placeholder toasts per spec). Non-wrap guard returns 400 on all 5 Phase 2E endpoints. Verified end-to-end by testing_agent_v3_fork iteration_147 — backend 24/24 PASS (11.6s), frontend 100% PASS, 0 critical/minor issues, 0 action items. New test file: `/app/backend/tests/test_iteration147_wrap_phase2e.py`.
- 2026-05-18 — **Wrap Command Center Phase 2D (Production + Install workflow)**: Extended `routes/wrap.py` with top-level `production` and `install` blocks on `wrap_data`. Eight new endpoints: `PUT /production`, `POST /production/tasks`, `POST /production/tasks/load-defaults` (idempotent), `PUT/DELETE /production/tasks/{id}`, `PUT /install`, `POST/PUT/DELETE /install/issues`. Production has 10 checklist booleans + matching `_at` timestamps with idempotent semantics (true→true preserves; false clears) and 9 production statuses. Default-tasks endpoint seeds 10 canonical wrap tasks only when the task list is empty (verified no-duplicates). Install has 14 schedule fields + 10-item nested `checklist` (partial-merge updates), customer_signoff toggle with idempotent timestamp, and full Install Issue Log CRUD with 12 issue types. **Critical workflow tie-in**: when `install_status='complete'` AND `customer_signoff=true` (both conditions), the backend auto-flips `approvals.final_signoff_completed=true` (timestamp idempotent). `pipeline_state` extended with `production_complete / install_active / install_complete`; WrapStatusBar now lights the Production / Install / Complete chips emerald from real state. New frontend `ProductionTab.js` (status selector + 10-row checklist + Load-Default-Tasks + per-task CRUD with status badges) and `InstallTab.js` (schedule form + 10-row checklist + Customer Signoff card + Issue Log CRUD). Verified end-to-end by testing_agent_v3_fork iteration_146 — backend 25/25 PASS, frontend 100% PASS, 0 critical/minor issues, 0 action items.
- 2026-05-17 — **Wrap Command Center Phase 2C (Design + Contract + Approvals + Quote Draft + Pipeline)**: 10 endpoints; design/contract/approvals/draft-quote/pipeline_state derivation; QuoteDraftModal; status pipeline chips wired. Test report: iteration_145.json — 21/21 backend + 100% frontend PASS.
- 2026-05-17 — **Wrap Command Center Phase 2B (Pricing & Materials + Vehicle Sync)**: Materials CRUD + 3 pricing methods; apply-price-to-order rolls up order_total via workflow_engine.update_order_progress; vehicle sync into job_tickets.specs. Test report: iteration_144.json — 21/21 backend + 100% frontend PASS.
- 2026-05-17 — **Wrap Command Center Phase 2A (Vehicle Info + Measurements persistence)**: Test report iteration_143.json (13/13 backend, 100% frontend).
- 2026-05-17 — **Wrap Command Center Phase 1 (frontend, modular)**: Specialized workspace tied to wrap-category order items. New page `/app/frontend/src/pages/WrapCommandCenterPage.js` and 23 reusable wrap components under `/app/frontend/src/components/wrap/`. Route added: `/orders/:orderId/items/:itemId/wrap-command-center`. `OrderDetail.js` shows a violet "Wrap Workflow" badge + "Open Wrap Command Center" button only for wrap categories (via `isWrapCategory`). Phase 1 buttons are placeholder toasts. Verified by testing agent (iteration_142.json) — 11/11 PASS.
- 2026-05-15 — **AI Assistant Pass 5 (CRM tools + actionable reminders)**: Added `find_customer` and `attach_note_to_customer` to the tool router; new endpoints `POST /api/ai/assistant/commit-note-to-customer` and `POST /api/ai/assistant/dismiss-reminder`. Reminders set via `set_reminder` now surface in the Dashboard Assistant Nudges widget as actionable "Mark done" pills (Bell icon, yellow theme) that flip `assistant_reminders.status` server-side. New ProposedActionPill components for find_customer (sky theme, shows recent invoices/orders) and attach_note (indigo theme). Regression: 10/10 fees/owner_connect tests + 12/12 new pass-5 tests in `test_iteration141_assistant_pass5.py`. Test report: `/app/test_reports/iteration_141.json`.
- 2026-04-30 — Assistant memory fix: persistent conversation per (tenant, user) in MongoDB (`assistant_conversations`), up to 60 messages stored, last 20 used for prompt context (was 6). Client sends last 30 (was 10). Page reloads and navigation no longer wipe the assistant's memory. GET/DELETE `/api/ai/assistant/history` endpoints added. "New Chat" trash button added to floating assistant.
- 2026-04-30 — NEW: Broadcast Email to Tenant Owners platform-admin tool (`POST /api/platform-admin/broadcast-email`) with audience filters, test-mode, audit logging, full UI at `/platform-admin/broadcast-email`. Plus `/app/PLATFORM_ADMIN_RUNBOOK.md` walkthrough document covering every platform-admin feature step-by-step.
- 2026-04-30 — Racing Tools Cleanup: hid `Vehicle Wrap Cost Calculator` from Racing (kept backend for future relocation); softened production wording on remaining 3 racing tools; Race Team Branding Kit now also emits a written branding brief alongside images.
- 2026-04-30 — Design Tools Cleanup: hid `logo_refresher` and `generative_fill` (misleading); renamed `text_to_image` → `AI Image Concept Creator`; softened production wording on remaining tools; AI Sign / Banner Designer now also emit a concise design brief alongside images.
- 2026-04-30 — Customer Branding Profile UI integration + Marketing Tools Cleanup (merged Completed Order Post Creator + Social Media Job Post Creator; improved Social Pack Generator + Content Calendar; 8 new Document Library categories with AI-tool auto-tagging).

### 2026-04-27 — Tier 8 Sweep (Docs & Marketing) + Tier 7 (Signatures & Drawings)

**Tier 8 — Docs & Marketing (17/17 tests pass)**
- All 15 docs pages return HTTP 200 and render content
- All 9 marketing pages load correctly (/, /features, /pricing, /about, /contact, /terms, /privacy)
- **Docs Content Updates:**
  - `DocsQuotesJobs.js` — Added Signatures & Drawings section
  - `DocsCustomerPortal.js` — Added Appointment Requests + Quotes & Invoices sections
  - `DocsFinancials.js` — Expanded to 8 sections (Invoice Management, Stripe Connect, Invoice Aging)
  - `DocsFAQ.js` — Added Billing & Payments category with 3 new questions
- Test report: `/app/test_reports/iteration_137.json`

**Tier 7 — Signatures & Drawings (22/24 backend tests pass)**
- **Bugs Fixed:**
  1. DELETE `/api/order-drawings/{id}` — Added `platform_admin` to allowed roles
  2. PUT `/api/order-drawings/{id}` — Fixed label↔title mirror sync
  3. Signature capture — Added `client_ip` field to both internal and public sign routes
- **RBAC audit:** Fixed 5 additional role-check locations missing `platform_admin`:
  - `employees.py` — payroll access checks
  - `credits.py`, `pricing.py`, `pricing_setup.py` — admin functions
- Test report: `/app/test_reports/iteration_136.json`

### 2026-04-26 (Tier 6 sweep) — Admin PDFs + Appointment Email Notification
- **Customer Request Appointment email notification:** Tenant owner now receives an HTML email immediately when a customer submits an appointment request via portal. Verified end-to-end (real 202 from SendGrid). Wrapped in try/except so SendGrid failure does not block appointment creation.
- **Admin Quote PDF** `GET /api/quotes/{id}/pdf` — implemented; returns valid PDF with company header, customer block, line items, totals, notes, terms.
- **Admin Invoice PDF** `GET /api/invoices/{id}/pdf` — implemented; includes PAID/UNPAID status badge with colour-coded watermark, line items, totals.
- **Tier 6 backend sweep (20/20 PASS)** — sections 6.1 AI Tools, 6.2 Floating Assistant, 6.3 Emails/SendGrid, 6.4 PDFs.
- **Deferred to backlog:** `GET /api/ai/tools` listing endpoint, `POST /api/ai/extract-invoice`, server-side clear-chat (chat history is client-managed by design), payroll PDF, work-ticket PDF.
- **Code review notes for future refactor:** Split `routes/ai.py` (3183 lines) into 4 files. Extract PDF rendering boilerplate to `services/pdf_renderer.py`. Register a unicode TTFont with reportlab if customer names may include CJK/accented characters.
- **Trackers updated:** PRELAUNCH_CHECKLIST.md Tier 6 sections + Section 17 added to user personal checklist (31 items covering AI UI, 10-mail-client render, PDF visual quality, SPF/DKIM/DMARC).

### 2026-04-26 (later) — Customer Request Appointment Feature + Tier 5 Backend Sweep
- **NEW FEATURE:** Customer-initiated appointment requests via portal:
  - `POST /api/portal/appointments/request` (customer) — creates appointment with `status="requested"`, notifies shop
  - `PUT /api/appointments/{id}/confirm` (admin) — confirms request, supports time/employee override
  - `PUT /api/appointments/{id}/reject` (admin) — cancels request with reason
  - Portal UI: "Request Appointment" button + dialog on `/customer-portal/appointments` with type/date/time/location/notes fields and "Pending Confirmation" amber badge
- **Tier 5 backend sweep:** 28/29 PASS. Sections 5.1 (Users), 5.4 (Digest), 5.7 (Promo Codes), 5.8 (Community), 5.10 (Pricing Foundation), 5.11 (Tenant), 5.12 (Email Templates) all verified.
- **Bug fixes uncovered:**
  - Added missing `DELETE /api/admin/users/{id}` with three guardrails (self / permission / last-owner)
  - Fixed broken `Permission.USERS_EDIT` references in `routes/auth.py` (enum doesn't exist) → changed to `USERS_MANAGE` — would have caused AttributeError on first admin reset-password/status call
- Trackers updated: `PRELAUNCH_CHECKLIST.md` Tier 5 sections + Section 16 added to user personal checklist (25 manual UI/Stripe/email verifications).

### 2026-04-26 — Prelaunch Tier 1–4 Final Mop-Up Closeout (iteration_132 follow-up)
Addressed all 4 missing endpoints and 1 security bug discovered in iteration_132:
- **Security:** Added `_require_payroll_view_access()` guard to all GET payroll routes — staff role now correctly returns `403`. Previously, staff could read all payroll data because GET routes had no permission check.
- **CSV Export — Customers:** New `GET /api/customers/export` endpoint streams CSV (name, email, phone, company, status, notes, created_at).
- **CSV Export — Payroll:** Added `format=csv` query param to `GET /api/payroll/report`. Returns streaming CSV with employee-level columns.
- **Workflow Templates:** New `POST /api/workflow-templates/{id}/apply` (creates production tasks per stage for each ticket on an order; supports `replace_existing=true`) and `POST /{id}/duplicate` endpoints.
- **Customer Portal Appointments:** New `GET /api/portal/appointments` returns customer's scheduled appointments with optional `upcoming_only` and `status` filters.
- **Employee Portal Dashboard:** Added `GET /api/employee-portal/dashboard` as alias of `/work-summary` (matches frontend spec which referenced `/dashboard` URL).
- All 6 fixes verified via curl smoke tests with admin/staff/portal/employee tokens.
- Trackers updated: `PRELAUNCH_CHECKLIST.md`, `PRELAUNCH_OPEN_ITEMS_TRACKER.md`, `PRELAUNCH_POSTFIX_RETEST_RESULTS.md`, `PRELAUNCH_SECTION1_USER_PERSONAL_CHECKLIST.md` (Section 15 added with manual UI verifications).

### 2026-04-25 — Public `/data-deletion` static page (Meta App compliance fix)
- Created `/app/frontend/public/data-deletion.html` and `/app/frontend/public/data-deletion/index.html` so the URL is served as raw HTML (Meta crawler does not run JS).
- Wrapped `mailto:` links in `<!--email_off-->...<!--/email_off-->` to disable Cloudflare's Email Address Obfuscation, which was rewriting `support@signguy-ai.com` to `[email&nbsp;protected]` mid-flight.
- Page contents include: title "Data Deletion Instructions - SignGuy AI OS", `support@signguy-ai.com`, last-updated date, request fields, retention notes.
- Existing React route `/data-deletion` (`pages/DataDeletion.js`) remains intact for in-app navigation.
- Verified production: `https://signguy-ai.com/data-deletion` returns HTTP 200 with full content visible to Facebook crawler UA.
- Note: Meta's "name_placeholder should represent a valid URL" error in their UI was a Meta frontend bug; bypassed with hard refresh / incognito.

### 2026-04-25 — Meta OAuth redirect_uri fix (production)
- Fixed `routes/meta_integration.py` `start_oauth` and `oauth/callback` to build `redirect_uri` from new env var `META_PUBLIC_URL` (`https://signguy-ai.com`) instead of `request.base_url` (which returned the internal Kubernetes cluster URL `team-schedule-32.cluster-2.deploy.emergentagent.com`).
- Added `META_PUBLIC_URL=https://signguy-ai.com` to backend `.env`.
- Verified production now sends correct `redirect_uri=https://signguy-ai.com/api/integrations/meta/oauth/callback`, matching the URI whitelisted in Meta App > Facebook Login for Business > Settings.
- OAuth flow now reaches Facebook's authorization page successfully.


**Backend files created:**
- `services/meta_service.py` — Fernet token encryption, Meta Graph API helpers, audit logging
- `services/facebook_ai.py` — Claude Sonnet AI classification + structured order extraction (12 classification labels, 30+ extraction fields)
- `routes/meta_integration.py` — OAuth flow, webhook GET/POST, page connect/disconnect/settings
- `routes/facebook_messages.py` — Message inbox, AI processing, lead/order creation, review actions

**Frontend files created:**
- `pages/MetaIntegration.js` — Settings > Meta/Facebook page with OAuth connect flow, page management, AI settings
- `pages/FacebookLeads.js` — Leads inbox with stats, message list, search/filter, AI review modal

**Features working:**
- Webhook verification (GET challenge/response) ✅
- Multi-tenant webhook ingestion mapped by Page ID ✅
- Idempotency (duplicate message IDs ignored) ✅
- Claude Sonnet AI classification (12 labels) + structured order extraction ✅
- Auto-create draft lead/order when confidence ≥ threshold ✅
- Audit logs for all actions ✅
- Page access tokens encrypted at rest (Fernet) ✅
- 50/50 backend tests pass ✅

**Phase 2 (not built):** Dashboard widgets, auto-reply sending, advanced customer matching, notification system.
- New `POST /api/stripe-connect/invoice/{id}/send-payment-link` endpoint — generates a Stripe Checkout URL for any invoice and optionally emails it directly to the customer.
- Frontend modal on Invoices page: shows amount, read-only URL, Copy (with check animation), Open-in-new-tab, editable email input, and Send button.
- Customer email auto-filled from the customers DB; the customer needs no account to pay (Stripe-hosted checkout page).
- Extracted all Stripe business logic out of `routes/webstores.py` and `routes/stripe_connect.py` into `services/stripe_service.py`.
- `webstores.py`: 2205 → 2034 lines (-171 lines).
- `stripe_connect.py`: 1371 → 1190 lines (-181 lines).
- New `stripe_service.py`: 410 lines, single source of truth.
- All existing endpoints and webhook flows verified working after refactor.
- Both files use standalone Motor clients to avoid circular import through `server.py`.

## Implemented (CHANGELOG)

### 2026-04-24 — Webstore orders now auto-appear in main Orders list
- Added automatic bridge creation from webstore checkout orders into `orders` collection in `backend/routes/webstores.py`.
- New helper flow:
  - `_next_order_number_for_tenant(...)` to generate standard `ORD-####` numbering.
  - `_ensure_main_order_bridge(...)` to insert a main order record with marker fields (`is_webstore_order`, `webstore_order_id`, `webstore_id`, `webstore_name`, `webstore_job_id`).
- `create_webstore_order(...)` now creates/links `main_order_id` immediately after webstore order creation and updates job with `order_id` linkage.
- Updated `frontend/src/pages/OrdersPage.js` to visibly mark these rows with a **Webstore** badge.
- Verified with simulated paid checkout in `signguypa@gmail.com` tenant:
  - webstore order created,
  - corresponding main order created,
  - marker fields present,
  - UI shows `Webstore` badge and row remains clickable.

### 2026-04-24 — Webstore checkout enforced to Stripe-only paid flow
- Hardened backend `POST /api/webstores/v2/orders` (`backend/routes/webstores.py`) to **block unpaid/direct order creation**.
- Route now requires a real Stripe session-backed idempotency key (`stripe:{session_id}`) and validates against `payment_transactions` with matching `reference_id` + `status=paid`.
- This prevents legacy “customer info only” submissions from creating unpaid orders.
- Updated storefront payment return handling (`frontend/src/pages/Storefront.js`) to verify `session_id` via `/api/stripe-connect/payment-status/{session_id}` before showing success.
- Added short polling for payment verification and clearer checkout CTA text (`Continue to Secure Payment` / `Redirecting to Stripe…`).

### 2026-04-24 — Webstore banner visibility compatibility fix
- Fixed storefront banner/logo rendering compatibility for legacy store docs where media URLs may be stored on top-level keys (`banner_url`, `logo_url`, `*_image_data`) instead of nested `branding`.
- Backend: updated `sanitize_webstore_for_public(...)` and `_normalize_webstore_doc(...)` in `backend/routes/webstores.py` to map legacy media fields into `branding.banner_url` / `branding.logo_url`.
- Frontend: updated `frontend/src/pages/Storefront.js` to use robust fallback chain for banner/logo source selection.
- Verified banner asset rendering + no 404 + no layout regressions on desktop/mobile via frontend test agent.

### 2026-04-23 — Webstores create flow: "created but failed to refresh list"
- Fixed `frontend/src/pages/Webstores.js` list-refresh resilience after create:
  - Added `normalizeWebstoreList(...)` to handle variable response shapes safely.
  - Upgraded `loadData(...)` with one-shot retry for webstore fetch failures.
  - Added optional `suppressStoreErrorToast` mode for create flow to avoid false-negative UX.
  - Added optimistic insert of newly created store into local list so it appears immediately even if background refresh is flaky.
- Create flow now shows success and keeps the store visible immediately + after hard refresh.
- Verified with frontend automation using tenant owner credentials: create succeeds, no "failed to refresh list" toast, store count increments instantly, and persists after page reload.

### 2026-04-23 — Features page screenshot lightbox
- Added click-to-enlarge behavior for feature screenshots on `/features` in `frontend/src/pages/FeaturesPage.js`.
- Each screenshot card now shows a "Click to enlarge" hint and opens a full-screen modal with enlarged image + feature title.
- Lightbox supports both close button and click-outside-to-close interactions.
- Verified desktop + mobile behavior via frontend test agent; no layout regressions.

### 2026-04-23 — Default feature screenshots made taller/readable
- Recaptured all `frontend/public/screenshots/feature_*.jpeg` marketing assets at **1920x1200 (16:10)** instead of short wide-strip framing.
- This increases default on-page screenshot height and improves text readability before opening lightbox.
- Re-verified: all feature images load successfully, lightbox still works, and no desktop/mobile overflow regressions.

### 2026-04-23 — Features page screenshot refresh with real data states
- Replaced/recaptured marketing feature screenshots using live preview tenant data for core admin modules (dashboard, customers, orders, pricing, invoices, payroll, payments, reporting, settings, productivity, webstores, AI tools, intake forms).
- Added dedicated portal screenshots with real account states:
  - `feature_customer_portal.jpeg` from active customer portal dashboard (orders/invoices visible)
  - `feature_employee_portal.jpeg` from active employee portal dashboard (clock/pay/tasks visible)
- Updated `frontend/src/pages/FeaturesPage.js` image mapping to use new context-specific assets (`feature_payments`, `feature_payroll`, `feature_customer_portal`, `feature_employee_portal`, `feature_productivity`, `feature_reporting`, `feature_intake_forms`).
- Verified by frontend test agent: all 17 cards render real images (no placeholders), no broken links, removed legacy terms absent, and responsive layout passes desktop/mobile.

### 2026-04-23 — Marketing Features page coverage refresh
- Updated `frontend/src/pages/FeaturesPage.js` content while preserving existing layout and flow (hero, filters, alternating feature cards, CTA).
- Removed outdated pricing bullets (`Channel letter calculator`, `Monument sign calculator`) and aligned pricing coverage to active categories (digital print, cut vinyl, rigid signs, banners, vehicle graphics, apparel, services, promotional, custom).
- Expanded high-level feature coverage with concise, non-overwhelming additions: Stripe billing/connect, intake forms, reporting/productivity analytics, admin/team/onboarding controls.
- Added compact “Coverage Highlights” cards to represent broader platform capability without excessive detail.
- Reused existing screenshots and mapped them across all added/updated cards to avoid placeholder-heavy sections.
- Verified via UI automation: category filters, new cards, removed terms, screenshot presence, desktop/mobile layout integrity all passing.

### 2026-04-23 — Payroll/timeclock stabilization + payroll controls
- Fixed recurring payroll worksheet break-loss behavior by merging same-day shifts in `frontend/src/lib/payrollWorksheet.js` and preserving break deductions even when lunch fields are blank.
- Added lunch field persistence for timeclock break actions in `backend/services/timeclock_service.py` (`lunch_start` on break start, `lunch_end` on break end).
- Fixed payroll shift edit API to accept explicit null lunch values (`exclude_unset=True`) so admins can clear/edit breaks reliably.
- Added `POST /api/payroll/mark-paid-in-full` in `backend/routes/employees.py` to create/update period-scoped payment transactions with official paid amount.
- Added top-toolbar "Paid in Full" amount input + action button in `frontend/src/components/payroll/PayrollWorksheetToolbar.js` and wired flow in `frontend/src/pages/Payroll.js`.
- Added tenant payroll setting `show_payroll_adjustments` (default `false`) in `backend/models/auth.py` and `frontend/src/pages/CompanySettings.js`, with conditional panel rendering in payroll page.
- Verified by testing agent: `/app/test_reports/iteration_123.json` (backend 14/14 pass, frontend checks pass).

### 2026-04-22 — Stripe Connect mode-safety hardening
- Added `_scrub_stale_connect_account()` + `_is_wrong_mode_error()` helpers in `routes/stripe_connect.py`.
- `/stripe-connect/status` auto-scrubs test-mode Connect accounts lingering on a live platform and records audit trail (`stripe_connect_scrubbed_at/_reason/_account_id`).
- `/stripe-connect/create-account` refuses to save test-mode accounts on a live platform (defense in depth).
- `/stripe-connect/refresh-link` returns 409 with friendly copy when account is stale/wrong-mode, instead of a broken onboarding URL.
- `account_mode` detection now distinguishes `livemode=None` (unactivated live) from `livemode=False` (actual test) — fixes false `mode_mismatch` on fresh live accounts.
- Frontend `PaymentSettings.js` auto-refreshes status on 409 so UI recovers cleanly.
- Verified end-to-end: ghost `acct_1TP6Je0f4QWGY8c6` successfully scrubbed; live `acct_1TP6XF1JC1SdQUDo` recognized correctly.

### Earlier this session
- AI Business Assistant Phase 5 frontend integration.
- Webstore backend hardening (W1–W17): cross-tenant leaks, permission gaps, payout inflation, idempotency, Stripe caching, base64 image migration to object storage.
- Prelaunch checklist: 24 items tested and checked off.
- Timeclock display bug: canonical `clock_in` instead of `updated_at`.
- Dashboard clocked-in widget: removed UTC date regex (was dropping cross-midnight workers).
- Payroll print CSS: outline font stack fixed.
- `PayrollTransaction`: tenant_id scoping + Pydantic validation.
- Webstore frontend empty-state/filter-trap fix.
- Stripe Checkout Flow B rewrite — unified order recording into `webstore_orders_v2`, secure webhook handling, 9 bugs fixed.

## Roadmap (P0 → P3)

### 2026-04-26 — Tier 3 + Tier 4 — 52/55 Pass + 3 Features Built

- **Tier 3** (Production Lifecycle): Board, tasks, timeline, workflow templates, approvals (with status transitions), appointments (full CRUD built), productivity feed, profit analytics, invoice aging endpoint added
- **Tier 4** (People & Portals): Employees CRUD, payroll worksheet, TimeClock full lifecycle, customer portal, employee portal all verified
- **Checklist progress: 257 checked / ~800 total items (including sub-items)**

---

- **2.6 Files & Drawings**: PNG/JPG/PDF/SVG/AI upload, content fetch, promote-to-shared, delete, drawing CRUD — all pass
- **2.7 Webstores**: Products CRUD with new `size_options/color_options/is_featured/in_stock`, webstore name uniqueness (409), SEO fields `seo_title/seo_description/og_image` added to model
- **2.8 Products**: Full CRUD verified with all new fields
- **2.9 Questionnaires**: All field types, public submit, required enforcement, email format validation added
- **2.10 Signatures**: Create, public token, sign, one-time-use (409), invalid token (404), expired token (handled)

**Checklist progress: 179 checked / 736 total**

---

- **2.3g Services (14/14 agent-testable PASS)**: All pricing branches verified — hourly installation, flat-fee, consultation minimum, delivery/mile, delivery/trip, subcontracted permit, equipment rental, file cleanup, site survey, wrap install complexity, rush from foundation/fallback/zero. Breakdown spec fields verified.
- **2.3h Promotional (6/6 PASS)**: Magnets, yard signs, stickers baseline + tier discounts + double-sided upcharge + rush all verified.
- **2.3i Custom/Other (3/3 PASS)**: Manual price override, description persistence, no progressive disclosure.
- 5 AI Prefill badge items in 2.3g remain for user verification (require real AI credits).

**3 bugs found and fixed:**
1. `models/enums.py`: Added `GRAPHIC_DESIGN = 'graphic_design'` to `ServiceType` enum (was causing 500 on `graphic_design` service type)
2. `routes/job_tickets.py`: Added `description`, `entry_mode`, `manual_quote_override`, `pricing_snapshot`, `linked_order_file_ids`, `item_artwork_file_ids`, `artwork_use_mode` to `JobTicket()` constructor (these fields were silently dropped on create)
3. `server.py` `calculate_promotional()`: Added double-sided upcharge (1.5× for `different`, 1.2× for `same`)

---

#### 2.1F — Tax-Exempt Toggle
- Added `default_tax_rate: Optional[float]` to `TenantBase` and `TenantUpdate` models (`models/auth.py`)
- Updated `generate_invoice_from_order` (`routes/orders.py`) to fetch tenant's `default_tax_rate` and customer's `is_tax_exempt` flag; applies `tax_rate=0` for exempt customers, full rate for others
- Added "Default Tax Rate (%)" input to `CompanySettings.js` with data-testid `company-tax-rate-input`
- Verified: non-exempt customer ($100 order, 6% rate) → `tax_amount=6.0, grand_total=106.0`; exempt customer → `tax_amount=0.0, grand_total=100.0`

#### 2.2E — Assets Panel Upload / Drag-and-Drop / Thumbnails
- Rewrote `components/orders/OrderAssetsPanel.js` to add:
  - Drag-and-drop zone (`data-testid="asset-drop-zone"`) with visual feedback on hover
  - `AssetThumbnail` component: fetches actual image blob from `/api/orders/{id}/files/{file_id}/content`, displays real thumbnail; falls back to `FileIcon` for non-images
- Verified: file upload works, `asset-row-{id}` appears, `asset-thumbnail-{id}` shows real image

---

### 🟡 IN PROGRESS — Meta Messenger Phase 1 End-to-End Verification
**Status (paused 2026-04-25):**
- ✅ Backend: webhook GET/POST verified, OAuth start/callback fixed, env vars set
- ✅ Production deployment: `signguy-ai.com` serves new code with `META_PUBLIC_URL` fix
- ✅ Meta Dashboard: App Domains, Privacy URL, Terms URL, Data Deletion URL, Webhook Callback URL, Verify Token, Valid OAuth Redirect URI — all configured and verified
- ✅ OAuth flow now reaches Facebook's auth dialog (no more "Can't load URL")
- ❌ **BLOCKED:** "No Pages Found" after OAuth — user has not yet added the four Messenger permissions in Meta App settings (`pages_show_list`, `pages_messaging`, `pages_manage_metadata`, `pages_read_engagement`)
- ⏸️ Pending: revoke previous FB authorization, re-do OAuth, select page, send test DM, verify lead creation, verify tenant isolation

**Next session — resume here:**
1. Confirm user added the 4 Messenger permissions in Meta App Dashboard (Use Cases or App Review > Permissions and Features)
2. Have user revoke prior auth at facebook.com/settings?tab=business_tools
3. Re-run OAuth — pages should appear
4. Test full flow: connect page → webhook subscribed → real DM → AI-extracted draft lead in `/facebook-leads`
5. Verify tenant isolation
6. After verification, prepare Meta App Review submission (subprocessor list already documented in conversation: Emergent Labs, Cloudflare, MongoDB, Anthropic, PostHog)

### P2 — Upcoming
- Easy Artwork sharing to Customer Portal from order details.
- AI receipt analysis for uploaded expense photos.
- Tax-exempt toggle behavior validation/fix (`2.1F`).
- Assets-panel artwork attach + thumbnail path fix (`2.2E`).

### P2 — Meta Messenger Phase 2 (after Phase 1 verified)
- Dashboard widgets, auto-replies, advanced customer matching, notification system, retention settings.

### P2 — Backlog
- Deduplicate payroll compensation snapshot hours (`_get_employee_compensation_snapshot` sums job+manual+clock without dedupe; needs product decision).

### P3 — Future
- Team / Workforce Ribbon rebuild (on hold).
- Optional: UI banner before Connect click reminding tenants to close old Stripe tabs.

## Key Files
- `backend/routes/stripe_connect.py` — Connect onboarding, webhooks, checkout.
- `backend/routes/webstores.py` — webstore CRUD, unified order creation.
- `backend/routes/employees.py` — payroll transactions, snapshots.
- `backend/services/timeclock_service.py` — punch handling, shift state.
- `frontend/src/lib/payrollWorksheet.js` — worksheet row merge + break calculations.
- `frontend/src/pages/Payroll.js` — worksheet save logic + paid-in-full flow.
- `frontend/src/components/payroll/PayrollWorksheetToolbar.js` — top-area payroll actions.
- `frontend/src/pages/CompanySettings.js` — payroll settings toggles.
- `frontend/src/pages/Admin/PaymentSettings.js` — Connect UI.
- `frontend/src/pages/Webstores.js` — admin dashboard.
- `frontend/src/pages/Storefront.js` — public storefront + checkout.

## Integrations
- **Stripe** — Live keys (`sk_live_…`). Platform account activated with Connect.
- **Emergent LLM Key** — OpenAI / Gemini / Claude via `emergentintegrations`.

## Test Credentials
See `/app/memory/test_credentials.md`.
