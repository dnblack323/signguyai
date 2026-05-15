# SignGuy AI - Changelog

## February 12, 2026 — AI Assistant: kill "generic mode" + personality picker + quick-action intents

### Backend (`/app/backend/routes/ai.py`)
- **Killed "generic mode" disclaimer.** Founders (every tenant during the launch phase) get `has_business_data_access = True` unconditionally. The fallback prompt (when business data isn't wired) no longer says "I don't have access to your account screens" — it says nothing of the sort and still injects the real app nav.
- **System prompt rewritten from rigid rules → tone-driven.** Dropped the 80-line "CRITICAL RULES FOR ORDER CREATION", "Bad Response Examples (NEVER DO THESE)", "Question Order" script. The LLM now handles flow naturally; the draft state is still tracked but exposed as context, not enforced as rules.
- **Removed the brittle regex `detected_question` post-processor** (which forced the "Got it!" / "Perfect, X." pattern by hard-keying on phrases like "how many", "what size", etc.).
- **Always-on app awareness.** Every system prompt now embeds `APP_NAV_REFERENCE` listing all top-level tabs by their real names (Dashboard / Orders / Billing / Customers / Webstores / Documents / Team / AI Tools / Financials / Productivity / Reports / Community / Settings) so the assistant references YOUR app, not a hypothetical app.
- **4 personality presets** (`PERSONALITY_PRESETS`): `ops_partner` (default) / `wise_mentor` / `cheerful_helper` / `no_bs_direct`. Loaded from `tenant.assistant_personality`.
- **Quick action intent detection.** New `_detect_quick_action()` runs after every LLM reply. Matches simple verbs ("email <name>", "send invoice to <name>", "message <name>") + does a real customer lookup. Returns `proposed_action: { action_type, status: ready|needs_clarification, customer: {id,name,email}, confirm_label, low_risk }` alongside the chat response.
- **New endpoints:**
  - `GET /api/ai/assistant/personality` → `{ selected, skip_confirm, options[] }`
  - `PUT /api/ai/assistant/personality` → `{ personality?, skip_confirm? }` (whitelisted to known action types)
- **Tenant model**: added `assistant_personality: Optional[str]` and `assistant_skip_confirm: Optional[List[str]]` to `TenantUpdate` in `/app/backend/models/auth.py`.

### Frontend
- **`AIAssistant.js` chat UI** renders new `ProposedActionPill` below assistant replies when backend returns `proposed_action`. Two states: "ready" (purple pill with customer + Open button → routes to /customers/{id} or /billing/invoices/new) or "needs_clarification" (amber hint box).
- **`pages/settings/AssistantSettings.js`** (NEW) at `/settings/assistant` — 4 personality option cards with active highlight + "Auto-open email drafts" toggle. Routes wired in `App.js`. Added to Settings primary + mobile nav as "AI Assistant" with Sparkles icon.

### Verified
- `curl /api/ai/assistant` with "where do I add a vehicle wrap questionnaire" returns "**Documents** is where questionnaires live. Go to **Documents** → **Questionnaires** → **New Questionnaire**" — NOT the old "I'm in generic mode" answer.
- Switching to `no_bs_direct` and re-asking same question returns pure bullet-pointed steps with zero pleasantries.
- "email Donald Black" returns `proposed_action: { status: "needs_clarification", hint: "I couldn't find a customer matching..." }` instead of crashing.
- 43/43 backend regression tests still green (`tests/test_fees_and_owner_connect.py`, `tests/test_iteration140_owner_connect_endpoints.py`, `tests/test_questionnaire_send_email.py`).
- Settings page screenshot-verified live.

### Out of scope for this pass (next iteration)
- True real-time tool-calling (assistant actually CLICKS buttons for you via API)
- Voice quality / latency improvements
- "What I know about your shop" rolling memory summary (long-term memory)
- Multi-step workflows ("create order → invoice → schedule install")



## February 12, 2026 — "Show Math (Behind the Scenes)" debug panel on Pricing Foundation → Review

- Added `ShowMathPanel` to the Review tab in `/app/frontend/src/pages/PricingFoundation.js`. Renders 4 sub-tabs after every Run Test:
  1. **Calculation Flow** — numbered, human-readable trail (Dimensions → Area → Billable area → Waste-adjusted → Material cost → Production/Design/Install hours × rate → Labor subtotal → Overhead → Multipliers → Suggested → Final). Pulls labor rates from `labor_rates.production/design/installation.hourly_rate` with fallbacks.
  2. **All Variables** — raw `result.breakdown` dict as a 2-col table with smart number formatting.
  3. **Source Map** — for each known breakdown key, shows which Pricing Foundation tab/setting it comes from (e.g. `color_multiplier ↳ Cut Vinyl tab → color_multipliers`, `production_hours ↳ Category tab → production_labor_hours_per_sqft × area × multipliers`). Also displays effective Shop Defaults labor rates + overhead method + selected material at top.
  4. **Raw JSON** — full `result` payload with one-click Copy.
- Backend already returned `breakdown: Dict[str, Any]` on every calculator (no backend change needed). Verified working with Digital Print test 24"×24" qty 1 → flow shows 12 steps, $88.50 suggested.
- `Copy` icon imported from lucide-react for the Raw JSON copy button.
- All elements carry `data-testid` (`show-math-panel`, `show-math-toggle`, `show-math-tab-flow|breakdown|sources|raw`, `show-math-copy-raw`).



## February 12, 2026 — Fee fix + Founders-only flag + Webstore Owner Stripe Connect (Phase A/B/C)

### Phase A — Fee structure aligned to landing page
- `PLATFORM_FEES` reshaped from `tier→percent` to `tier→{percent, flat_cents}` in `/app/backend/services/stripe_service.py`. All four tiers default to `{0.022, 20}`. Added `WEBSTORE_SURCHARGE_PERCENT = 0.020`.
- New helper `calculate_platform_fee_cents(tier, amount_cents, is_webstore)` does the rounded math (round-half-up to avoid float drift; micro-payment floor never produces a fee ≥ amount).
- Wired into 3 checkout call sites in `/app/backend/routes/stripe_connect.py`: invoice pay, invoice send-payment-link, webstore checkout (only the webstore site uses `is_webstore=True`).
- New public endpoint `GET /api/stripe-connect/fee-preview?amount=X&is_webstore=Y` returns `{platform_fee_cents, platform_fee_label, stripe_estimated_cents, tenant_receives_cents}` for UI use.
- **Result:** $5 invoice → 31¢ platform fee (was 11¢, undercharging by $0.20). Webstore $500 → $21.20 (was $11.00).

### Phase B — Founders-only feature flag
- `REACT_APP_SHOW_FOUNDERS_ONLY=true` added to `/app/frontend/.env`.
- `TierContext.js` `checkFeature()` + `requireFeature()` short-circuit to "allowed" when flag on; reported tier becomes `founders_edition`.
- `MainLayout.js` preview-mode panel hides Starter/Pro/Business/Webstores-only/AI-Studio-only options (only "Founders Edition (Full)" shows).
- `/pricing-legacy` route now redirects to `/pricing-plans` (which is already Founders-only).
- UpgradeModal will never open while flag is on (no upstream calls produce `upgradeModal.open=true`).

### Phase C — Webstore Owner Stripe Connect (2 flows)
**Backend (new `/app/backend/routes/webstore_owners.py`):**
- Webstore model adds: `owner_stripe_account_id`, `owner_stripe_charges_enabled`, `owner_stripe_payouts_enabled`, `owner_stripe_details_submitted`, `owner_user_id`, `owner_portal_enabled`. Default webstore status changed to `PENDING`.
- `UserRole.WEBSTORE_OWNER = "webstore_owner"` added to `/app/backend/models/enums.py` with empty permission set in `ROLE_PERMISSIONS`.
- Tenant routes (auth): `POST /api/webstore-owners/{id}/invite/quick`, `POST /api/webstore-owners/{id}/invite/portal`, `GET /api/webstore-owners/{id}/owner-status`. SendGrid email with branded HTML + magic link (72h expiry, one-time use).
- Public routes (token): `GET /api/owner-onboard/{token}`, `POST /api/owner-onboard/{token}/start-stripe` (creates Express account + AccountLink), `GET /api/owner-onboard/{token}/refresh`, `POST /api/owner-onboard/{token}/login-link`.
- Portal routes: `POST /api/owner-portal/signup` (creates `webstore_owner` user), `GET /api/owner-portal/me`, `GET /api/owner-portal/stores/{id}/transfers`, `POST /api/owner-portal/stores/{id}/stripe-login-link`.
- **Activation gate** added in `update_webstore()`: cannot set `status='active'` unless `owner_stripe_account_id` set + `owner_stripe_charges_enabled=true`. Returns 400 with clear message otherwise.
- **Auto-transfer on order completion**: new `_maybe_auto_transfer_owner_commission()` helper inside `routes/webstores.py` `_apply_order_status_transition()`. When an order flips to COMPLETED and the owner has a connected Stripe account, fires `stripe.Transfer.create(amount, destination, idempotency_key=order_<id>_owner_commission)`. Updates `webstore.payout_owed -=, payout_paid +=`. Order doc gets `owner_transfer_id`, `owner_transfer_amount`, `owner_transfer_at`. Falls back to manual payout if owner not connected.

**Frontend:**
- `WebstoreOwnerConnectCard.js` (admin) embedded in the Webstore detail dashboard. Two buttons: "Send Quick Connect Link" and "Create Owner Portal". Live status badge + last-link copy.
- `WebstoreOwnerOnboard.js` (public) at `/webstore-owner/onboard/:token` — branded landing → Connect Stripe button → Stripe Express hosted onboarding → return + auto-poll for status → Stripe Express dashboard link.
- `OwnerPortalSignup.js` (public) at `/owner-portal-signup/:token` — collects password → creates `webstore_owner` user → redirects to same Stripe onboarding flow.
- `OwnerPortal.js` at `/owner-portal` — login + dashboard listing stores, sales/orders/paid/pending stats, transfer history table, Stripe Express dashboard launcher.

**Tests:**
- `/app/backend/tests/test_fees_and_owner_connect.py` — 10 fee-math tests (all pass)
- `/app/backend/tests/test_iteration140_owner_connect_endpoints.py` — 21 endpoint tests covering fee-preview, invites (quick + portal + cross-tenant 404), public onboard (valid + unknown + expired + login-link gate), portal signup (short-pw + quick-rejected + JWT + me + admin-cannot-use), transfers endpoint, stripe-login-link gate, AND activation-gate (cannot activate without connected, succeeds after seeding flags). **21/21 pass.**



## February 12, 2026 — New "Events" webstore product category

- **Backend:** Added `EVENTS = "events"` to `ProductCategory` enum in `/app/backend/routes/webstores.py` and mapped it to `JobItemType.OTHER` in `map_category_to_item_type` so order-from-product flow still works.
- **Frontend:** Added `Events` (CalendarDays icon, pink badge) to `categoryOptions` in `/app/frontend/src/pages/Products.js` (Products admin) and `/app/frontend/src/pages/Webstores.js` (webstore product picker). Added 🎫 emoji to ItemPickerDialog category icons.
- **Verified:** created product with `category: "events"` → 200, filter `GET /api/products?category=events` → returns the item, delete → 200.



## February 12, 2026 — Questionnaire bugs fixed (Send via Email + dark-bg contrast)

- **`POST /api/questionnaires/{id}/send-email` — new endpoint.** Accepts `{email, customer_name?, public_url?, message?}`. Verifies tenant ownership (404 cross-tenant), requires `status == "active"` (400 with explicit "Publish it first" message), validates email via Pydantic `EmailStr` (422 on bad format), uses `EmailService.send_email` (SendGrid) with a branded HTML + plain-text body and a tracked "Open Questionnaire" CTA button. Returns `{success, message, link}` on 200. Tenant company name pulled from `tenants.company_name`.
- **Frontend `handleSendEmail` rewired.** `/app/frontend/src/pages/Questionnaires.js` now calls the new endpoint with `{email, public_url: window.location.origin}` instead of the broken `/documents/send-email` call (which expected a `customer_id` and a `Document`, never a Questionnaire — explaining why it suddenly failed in prod). Added `data-testid` on the email input + submit button for automation.
- **PublicQuestionnaire dark-bg contrast.** Replaced all default `<Label>` (hardcoded `text-[#0F172A]`) and `text-muted-foreground` (resolves to `#475569`) instances on `/app/frontend/src/pages/PublicQuestionnaire.js` with explicit `text-slate-200` (labels), `text-slate-300` (paragraph questions / option labels), `text-slate-400` (descriptions, file-upload helper text, CardDescription) so customers can actually read the form on the `#0B0F17` background. Empty-state and Thank-You screens updated too.
- **Tested:** 12/12 backend pytest pass (`/app/backend/tests/test_questionnaire_send_email.py`). PublicQuestionnaire contrast verified via Playwright screenshot — all labels light-on-dark.



## April 30, 2026 — Assistant Memory Fix (options A + B)

- **Option A — Persistent conversation per user.** New MongoDB collection `assistant_conversations` storing up to 60 messages per (tenant_id, user_id). Two new endpoints: `GET /api/ai/assistant/history` and `DELETE /api/ai/assistant/history`. The existing `POST /api/ai/assistant` now (1) loads saved history, (2) merges with any client-sent history (de-duped by role+content tail), (3) uses it for the prompt, (4) persists the user-turn + assistant-turn after every successful reply.
- **Option B — Bigger context window.** Frontend slice bumped from last 10 → last 30 messages on send. Backend prompt context bumped from last 6 → last 20 messages. Works together with option A — even if the client sends nothing, the server has the full persisted history.
- **UI:** Both the full-page `/ai-assistant` and the floating assistant now hydrate saved history on mount. Floating assistant gained a trash-icon "New Chat" button (top-right of its header, confirm dialog) that calls DELETE and resets local state. Full-page `/ai-assistant` "New Chat" button now also calls DELETE server-side so memory clears everywhere.
- **Verified end-to-end:** clear → empty → "my favorite color is blue" → clear frontend → ask "what color?" → assistant correctly recalls "blue" (screenshot captured).
- Files: `/app/backend/routes/ai.py`, `/app/frontend/src/components/FloatingAssistant.js`, `/app/frontend/src/pages/AIAssistant.js`.


## April 30, 2026 — Broadcast Email personalization + critical platform-admin hardening

### Personalization (per-recipient placeholders)
- `{{owner_first_name}}`, `{{tenant_name}}`, `{{owner_email}}` placeholders now render per recipient in both subject and body. First name derived from `users.full_name` if present, else email local-part. Test mode previews using the admin's own tenant data.
- New helper `_render_broadcast_template()` performs the substitution.
- UI: a blue help card in the Body section lists the available placeholders.

### Critical security/correctness hardening (from troubleshoot agent review)
1. **Body size cap.** `BroadcastEmailRequest.html_body` capped at 50 KB, subject at 200 chars, `tenant_ids` list at 1000. Bodies over the cap return 422 (verified).
2. **HTML-escape placeholder values.** All substituted values now go through `html.escape(..., quote=True)` so a tenant whose name contains `<script>...</script>` cannot inject JS into the rendered email. Verified.
3. **Hourly rate limit per admin.** New `_enforce_broadcast_rate_limit()` queries the audit log for past-hour `broadcast_email.send` rows by this actor. Caps: 10 full broadcasts/hour, 30 test sends/hour. Returns 429 over cap. Verified — fires at attempt 28 (counting earlier smoke tests already on record).
4. **Fail-closed if SendGrid not configured.** Endpoint now calls `email_service.is_configured()` first and returns 503 instead of silently reporting "0 sent."
5. **`founders_only` filter fix.** Was querying `tenants.is_founder` which is never persisted (it's per-user, computed by `_enrich_with_founder_flag`). Now queries `users.distinct("tenant_id", {"is_founder": True})` and filters tenants by those IDs. Both `/broadcast-email` and `/broadcast-email/audience-counts` updated.
6. **Loud audit-log failures.** `services/admin_audit.log_admin_action()` previously swallowed exceptions silently. Now logs `AUDIT_LOG_WRITE_FAILED action=… actor=… target=… err=…` at error level with stack trace, so an ops engineer notices a missing audit trail rather than an attacker silently exploiting the gap. The "logging never breaks the caller" contract is preserved.

### Open follow-ups (post-launch hardening — not blocking)
- Impersonation token revocation (active-tokens collection + check on every request).
- `is_platform_owner` check in dunning auto-suspend for the edge case of a tenant with zero users.
- Frontend impersonation-token expiry check (every 60s).
- Maintenance-mode allowlist test coverage (developer footgun guard).
- Audit-log row even on idempotent suspend attempts.


## April 30, 2026 — NEW: Broadcast Email to Tenant Owners + Platform Admin Runbook

### Broadcast Email (the missing "mass email" feature)
- New endpoint: `POST /api/platform-admin/broadcast-email` with audience filters (`all_owners` | `active_only` | `suspended_only` | `founders_only`) plus a per-tenant override (`tenant_ids`) and a `test_to` mode that sends to a single address only (no audience resolution).
- Companion endpoint: `GET /api/platform-admin/broadcast-email/audience-counts` — live recipient counts so the UI can show "Send to N tenants" before commit.
- Sends via existing SendGrid email service. Sequential delivery, dedupes by email so multi-tenant owners only get one email. Returns `{matched_recipients, sent_count, failed_count, failed[]}`. Single audit row per blast (`broadcast_email.send`) with summary metadata.
- New page `/platform-admin/broadcast-email` — Subject + plain-text Body (auto-wrapped to HTML paragraphs), Audience picker with live count, Test-recipient field (pre-filled with admin's email), "Send test" + "Send to N tenants" buttons, confirm dialog, result panel showing sent/failed.
- Wired button on Platform Admin home (`PlatformAdmin.js` top-right action row) and route registration in `App.js`.
- Smoke-tested end-to-end: audience-counts returns 6 owners; test send returns `sent_count=1`; empty subject correctly returns 400; audit row written with `broadcast_email.send`.

### Platform Admin Runbook
- Created `/app/PLATFORM_ADMIN_RUNBOOK.md` — a plain-English walkthrough of every platform-admin feature (Tenant List, Tenant Detail, Suspend/Reactivate, Dunning + Mark as Paid, Threshold override, Impersonate, Onboarding Checklist, Broadcast Email, Site Settings, Email Deliverability, Audit Log) with step-by-step instructions, when-to-use guidance, common scenarios cheat-sheet, launch-day checklist, "setup work outside the app" list, and an API reference appendix.


## April 30, 2026 — Racing Tools Cleanup (audit-driven)

- **Hidden** `Vehicle Wrap Cost Calculator` from the Racing category (frontend `hidden: true`; backend prompt + logic preserved for future relocation to Pricing / Quotes / Business). It's a general pricing tool, not racing-specific.
- **Kept the 3 actually-racing tools:** Race Number Designer, Driver Name Plate Generator, Race Team Branding Kit.
- **Softened wording** on all three so users don't expect vector / production-ready / cut-ready output:
  - Race Number Designer — "AI-rendered raster concept images… final cut/print artwork may need vectorization or cleanup".
  - Driver Name Plate Generator — "AI raster concept images… not production-cut artwork".
  - Race Team Branding Kit — "AI raster brand-kit concepts plus a written racing branding brief… final vector artwork must be produced separately".
- **Race Team Branding Kit now also emits a written branding brief** alongside images (existing TOOL_PROMPTS["race_team_branding"] already covered Brand Identity / Number Design / Race Car Layout / Merchandise / Production Files Needed). Wired by adding `race_team_branding` to the paired-text-brief tuple in `POST /api/ai/generate-images`. Frontend "Design Brief" panel title now also fires for this tool. No extra credit cost; brief failure does not block images.
- Racing category badge updated to (3); top-of-page total recalculated to 24 via the existing `visibleTools` filter.
- Smoke-tested: Racing tab renders exactly the 3 expected tools; lints clean.


## April 30, 2026 — Design Tools Cleanup (audit-driven)

- **Hidden** two misleading Design tools (frontend-only `hidden: true` flag — kept in array so existing AI history rows still resolve):
  - `Logo Refresher` — uploaded logo wasn't actually sent to the image model.
  - `Generative Fill / Image Expander` — uploaded image wasn't actually sent to the image model.
- **Renamed** `Text to Image Creator` → **`AI Image Concept Creator`** with a concept-only description ("…for design inspiration, marketing visuals, or rough creative direction. Not print-ready production artwork.").
- **Softened wording** on remaining Design tools so users understand outputs are AI concepts, not finished/print-ready artwork or true mockups using customer artwork:
  - Photo Enhancer Analyzer — added verdict language (Approved / Needs Fixing / Not Usable).
  - AI Sign Designer & AI Banner Designer — descriptions now mention "AI sign concept images **with a short written design brief**" + "starting point — final production artwork may need cleanup".
  - Mockup Creator & Vehicle Wrap Mockup Generator — descriptions now state the AI illustrates the description and **does not place the customer's actual artwork**.
- **Wired the unused text prompts** for `ai_sign_designer` and `ai_banner_designer`:
  - Both prompts rewritten as a concise design brief (Direction, Colors & Layout, Readability, Production, Customer-Facing Summary).
  - `POST /api/ai/generate-images` now also calls `generate_text_content()` for these two tools and returns `design_brief` alongside `images` (saved to `ai_history.output`; brief failure does not block image return; no extra credit charge).
  - Frontend renders the brief in the existing "Design Notes" panel, retitled "Design Brief" for these two tools.
- **Visible-tools filter:** added `visibleTools` (`!t.hidden`) — the Design Tools count badge, "All Tools" badge, page header copy, and tool cards all use the filtered list now. Default `selectedTool` skips hidden tools.
- **Tested:** smoke screenshot — Design tab shows exactly 8 tools (no Logo Refresher, no Generative Fill); AI Image Concept Creator selected by default with concept-only copy.


## April 30, 2026 — Customer Branding Profile UI + Marketing Tools Cleanup

### Customer Branding Profile (UI integration shipped)
- Wired existing `CustomerBrandingTab` into the customer detail drawer in `pages/Customers.js` as a 5th "Branding" tab (`grid-cols-5`).
- Tab supports view/edit of full profile (business_name, industry, audience, brand personality, voice notes, competitors, USP, things to avoid, brand colors, taglines, logos, brand_kit_text), with per-item delete for taglines and saved logos.
- 3 CTAs in tab navigate to `/ai-tools?tool={branding_kit_generator|logo_creator|idea_brainstormer}&customer={id}`.
- AITools deep-link: when `?customer={id}` present, the page auto-fetches the branding profile, sets the picker, and pre-fills the form. `CustomerBrandingPicker` now also syncs internally when its `value` prop changes externally.
- Backend models/routes (`GET/PUT/POST /api/customers/{id}/branding{,/append}`) verified end-to-end via curl + pytest.

### Marketing Tools Cleanup (Message 574)
- **Merged** `Completed Order Post Creator` (image-based) and `Social Media Job Post Creator` (text-only) into a single tool with a `post_mode` selector (`with_image` | `text_only`). Image upload and "describe the order" text fields are now conditionally required/visible. Old `social_job_post` tool definition removed from frontend; backend prompt kept as alias for legacy AI history.
- Added a small `requiredWhen` / `showWhen` engine in `AITools.js` so any field can be conditionally required and conditionally hidden.
- Added `date` field type and used it for the new Content Calendar `start_date` picker.
- **Improved `Social Media Pack Generator`**: required `services_offered` + `pack_size`, added `platforms` filter and `brand_voice` selector. Stricter prompt asks for numbered posts with explicit Post Type / Caption / Visual / Best Platform / Hashtags lines, plus a "Quick Reuse Tips" footer.
- **Improved `Content Calendar Creator`**: required `start_date` + `date_range` + `post_frequency`, added `brand_voice`. New prompt produces a `YYYY-MM-DD (Day) | Theme | Platform | Idea | CTA` table tied to the actual start date, plus Theme Summary, Production Checklist, and Optional Boosts.
- **Document Library auto-tagging**: Added 8 new categories (`marketing_content`, `social_post`, `content_calendar`, `campaign_plan`, `blog_article`, `logo_concept`, `brand_kit`, `tagline`) to `DocumentCategory` enum. The `handleSaveToLibrary` mapper now routes every AI tool to the right bucket. `/documents/categories/list` updated so UI filters expose the new buckets.
- **Tested:** testing_agent_v3_fork iteration 138 — backend 16/16 passing, frontend 5/5 smoke checks passing.


## February 15, 2026 (Item #5 — final P0 prelaunch gap)

### Item #5 — System-wide Announcement Banner + Maintenance Mode (NEW)
- New collection `platform_settings` with a single `id="global"` document holding both pieces of state.
- New backend module `routes/platform_settings.py` exposing:
  - **Public reads** (no auth required, so the banner renders on `/login` too): `GET /api/platform/announcement`, `GET /api/platform/maintenance`.
  - **Admin writes** (Platform Admin only): `PUT /api/platform-admin/announcement`, `PUT /api/platform-admin/maintenance`, `GET /api/platform-admin/settings`.
- **Announcement Banner:**
  - Configurable `message`, `severity` (info / warning / critical), `dismissable` flag, optional `expires_at`.
  - Auto-expires when `expires_at` is in the past.
  - Per-user "dismiss" persisted in localStorage keyed by the banner's `updated_at` so a new edit re-shows for everyone.
- **Maintenance Mode:**
  - `enabled` toggle + custom user-facing message.
  - **New ASGI middleware in `server.py`** blocks every mutation method (POST/PUT/PATCH/DELETE) on `/api/*` for non-admin users with HTTP 503 + structured `{code: "maintenance_mode", message}` payload.
  - Allowlist (always passes through): `/api/auth/`, `/api/users/me`, `/api/platform/`, `/api/platform-admin/`, `/api/webhook/` (Stripe + SendGrid), `/api/health`. Reads stay open.
- **Audit log:** every change writes a `platform`-category row — `announcement.set`, `announcement.clear`, `maintenance.enable`, `maintenance.disable`.
- **Frontend:**
  - New `<GlobalBanner>` component mounted at the top of every page (sticky). Polls public read endpoints every 60 seconds so changes propagate to live users without a refresh.
  - New page `/platform-admin/site-settings` with two cards: Announcement (message, severity, expires_at, dismissable, Publish/Update/Clear) and Maintenance Mode (message + Enable/Disable buttons).
  - "Site Settings" button on Platform Admin home, alongside Email Deliverability and Audit Log.
- **End-to-end verified:**
  - Set / read / clear announcement via API.
  - Maintenance enable → user reads stay 200 → user write returns 503 with structured payload → admin write succeeds → SendGrid webhook still 200 → maintenance disable → user write 200 again.
  - All four admin actions captured in the audit log.

### THIS COMPLETES THE TOP-5 PRELAUNCH PLATFORM GAP CHECKLIST.

## February 15, 2026 (Items #3+ refinements + Item #4)

### Dunning Refinements
- **Founder 24-hour grace period.** When a tenant flagged `is_founder` (or with any user where `users.is_founder=True`) hits the failure threshold, the system starts a 24-hour grace window (`grace_period_until` on the tenant doc) and writes a new audit row `dunning.grace_started`. The next failure that arrives **after** the grace expires triggers the actual auto-suspend; payment success during the window clears it. Hours configurable via env `DUNNING_FOUNDER_GRACE_HOURS` (default 24).
- **Per-tenant failure threshold override.** Tenant doc gains `dunning_failure_threshold` (positive int, or null = use global default). New endpoint `PUT /api/platform-admin/tenants/{id}/dunning-threshold` lets a Platform Admin set or clear it. Audit action: `dunning.threshold_set`.
- **`is_founder` surfaced on TenantDetail.** Computed on the fly from any user's `is_founder=True` and exposed via a small `_enrich_with_founder_flag` helper used on every tenant-mutation endpoint.
- **Stripe webhook E2E test.** New `backend/tests/test_dunning_webhook_e2e.py` posts synthetic `invoice.payment_failed` and `invoice.payment_succeeded` events to the live `/api/webhook/stripe` and asserts: (1) auto-suspend at 3 failures, (2) auto-reactivate on success, (3) founder grace window starts instead of immediate suspend, (4) per-tenant threshold of 5 holds until attempt 5. **All 4 phases pass.**
- **UI:** dunning card now shows the active threshold ("Threshold: 3 (default)" or "Threshold: 5"), a purple "Founder · 24h grace applies" badge when applicable, and an amber grace-window banner showing the suspension hold timestamp. New "Set Threshold" button + dialog.

### Item #4 — Email Deliverability Dashboard (NEW)
- Confirmed **SendGrid is already live** (multiple 202 responses observed in production logs).
- New `email_logs` schema additions: `delivery_status`, `sg_message_id`, `events[]`. Existing 40 records back-filled with `delivery_status: "sent"`.
- New SendGrid Event Webhook handler at `POST /api/webhook/sendgrid` — accepts the standard SendGrid array payload. Matches events to `email_logs` by `sg_message_id` prefix, refines `delivery_status` (delivered / deferred / bounce / dropped / spamreport / blocked), appends the event to the log's `events[]`, and bumps `email_bounce_count` / `email_spam_count` on the tenant.
- New endpoints (Platform Admin):
  - `GET /api/platform-admin/email-logs` — filterable by tenant_id, delivery_status, to_email, since, until.
  - `GET /api/platform-admin/email-logs/summary` — aggregate counts (total / delivered / pending / bounced / complaints / failed).
- New page `/platform-admin/email-logs` with summary tiles, filter bar (recipient, status, tenant), table, and detail dialog (subject, sg_message_id, every captured SendGrid event with its reason).
- New "Email Deliverability (this tenant)" mini-tile on `PlatformAdminTenantDetail.js` — auto-hides when there are zero emails.
- "Email Deliverability" button on the Platform Admin home page.
- **Verified end-to-end:** sent a real email (got `sg_message_id`), POSTed a synthetic bounce event to `/api/webhook/sendgrid`, watched `delivery_status` flip from `sent` → `bounce`, the event saved to the log's events array, summary updated to show `bounced: 1`, `email_bounce_count` incremented on the tenant.

## February 15, 2026 (later — Item #3)
- **Failed-Payment / Dunning Workflow (NEW)** — top-5 prelaunch platform gap #3
  - New service `services/dunning.py` with `record_payment_failure()` and `record_payment_success()` — single source of truth for dunning state.
  - Tenant doc gains: `payment_failed_count`, `first_payment_failure_at`, `last_payment_failure_at`, `last_payment_succeeded_at`, `auto_suspended_for_payment`.
  - **Auto-suspend at 3 consecutive failures** (configurable via env `DUNNING_AUTO_SUSPEND_AFTER`). Self-lockout protection: never auto-suspends a tenant that contains a `platform_admin` user.
  - **Auto-reactivate on payment success** if the tenant was previously auto-suspended for payment (`auto_suspended_for_payment=true`). Manual suspensions are NOT auto-reactivated.
  - **Email orchestration:**
    - Failure 1 / 2 → `send_payment_failed_email` ("you have N attempts left").
    - Failure 3 → `send_dunning_suspended_email` ("account suspended").
    - Auto-reactivate → existing `send_tenant_reactivated_email`.
  - **Webhook wiring:** `multi_product_billing.handle_invoice_payment_failed` and `handle_invoice_payment_succeeded` now call into the dunning service.
  - **Manual override:** new `POST /api/platform-admin/tenants/{id}/mark-paid` for NET-60 invoices, wires, manually cleared chargebacks, etc. Resets counters + auto-reactivates if needed.
  - **Audit log integration:** every transition writes a row under `action_category="billing"`: `payment.failed`, `dunning.auto_suspend`, `payment.succeeded`, `dunning.auto_reactivate`, `payment.manual_mark_paid`.
  - **UI:** `PlatformAdminTenantDetail.js` now shows a "Billing & Dunning" card (failed-attempts counter, last failure/success timestamps, "Auto-suspended for non-payment" badge, "Mark as Paid" button + confirmation dialog). Card auto-hides if there's nothing to show (zero failures and no payment history).
  - `TenantDetail` Pydantic now exposes all five dunning fields.
  - **Verified end-to-end:** simulated 3 consecutive failures via `services.dunning` → tenant auto-suspended after #3 → payment success auto-reactivated → manual mark-paid via real HTTP also auto-reactivated → 9 distinct billing audit rows captured.

## February 15, 2026 (later — Email toggle)
- **"Welcome back" email toggle on Reactivation** — Suggestion from Item #2 finish-tool note.
  - New `EmailService.send_tenant_reactivated_email()` (renders an HTML "Welcome back" message with optional "note from our team").
  - `POST /api/platform-admin/tenants/{id}/reactivate` now accepts `notify_owner: bool` (default true) and returns `email_status` so the UI can confirm.
  - Reactivate dialog has a checkbox "Send the owner a 'Welcome back' email" (default ON).
  - Verified via curl: notify_owner=true returns `email_status.success=true, status_code=202` (real SendGrid send); notify_owner=false returns `email_status: null`.

## February 15, 2026 (Item #2)
- **Suspend / Reactivate Tenant (NEW)** — top-5 prelaunch platform gap #2

  - New endpoints: `POST /api/platform-admin/tenants/{id}/suspend` (body: `reason`), `POST /api/platform-admin/tenants/{id}/reactivate` (body: `note?`).
  - Tenant doc gains: `is_active`, `suspension_reason`, `suspended_at`, `suspended_by`, `suspended_by_email`, `reactivated_at`, `reactivated_by`, `reactivated_by_email`.
  - **Self-lockout protection:** cannot suspend a tenant that contains a `platform_admin` user.
  - **Idempotent:** re-suspend returns `already_suspended: true`; re-reactivate returns `already_active: true`.
  - **Login enforcement:** suspended tenants' users get HTTP 403 with structured detail `{code: "tenant_suspended", message, reason, suspended_at}` on login attempt.
  - **Active session enforcement:** every protected endpoint runs through `get_current_active_user`, which checks tenant `is_active` and rejects with the same 403 — existing sessions are killed on the next API call. Platform admins are exempt.
  - **Auto audit log:** suspend / reactivate actions write `tenant.suspend` / `tenant.reactivate` rows automatically via `log_admin_action`.
  - Frontend: `TenantListItem` and `TenantDetail` response models surface `is_active`, `suspension_reason`, `suspended_at`, `suspended_by_email`. `PlatformAdmin.js` shows red "Suspended" badge + reason inline. `PlatformAdminTenantDetail.js` shows red banner + "Suspend Tenant" / "Reactivate Tenant" buttons with reason / note dialogs.
  - **Account-suspended UX:** new `/account-suspended` page shows the user the reason + suspended_at + a "Contact Support" mailto. New `lib/suspensionGuard.js` helper saves the suspension info to sessionStorage and hard-redirects. AuthContext login + fetchUserProfile + AppContext axios response interceptor all detect 403/`tenant_suspended` and route the user to `/account-suspended`.
  - Verified end-to-end: created brand-new tenant → confirmed `/api/users/me` works → suspended → existing token blocked with 403 + structured payload → fresh login also blocked with same payload → reactivated → existing token works again. Audit trail captured 6 events.

## February 15, 2026
- **Admin Audit Log (NEW)** — top-5 prelaunch platform gap #1
  - New collection `admin_audit_log` capturing every privileged Platform Admin action with actor, target, tenant, IP, user-agent, summary, structured metadata, status, timestamp.
  - New service `services/admin_audit.py::log_admin_action()` (failure-tolerant — never blocks the calling action).
  - Wired into existing privileged endpoints: impersonation start, impersonation exit, manual end of impersonation log, and onboarding-checklist updates.
  - New endpoints: `GET /api/platform-admin/audit-log` (filterable by action, category, actor_email, target_id, tenant_id, since/until; paginated), `GET /api/platform-admin/audit-log/actions` (distinct actions/categories), `GET /api/platform-admin/audit-log/{id}` (single entry).
  - New page `/platform-admin/audit-log` with filter bar, table, and detail dialog. Reachable from "View Audit Log" button on the Platform Admin home page.
  - Verified end-to-end: impersonation start writes audit row with action `impersonation.start`, captured IP `34.170.12.145`, actor `thesigntistslab@gmail.com`, target user, tenant, metadata `{impersonation_log_id, target_role}`.

## April 28, 2026
- AI Tool Audits complete (read-only): Racing, Business, Marketing, Design, Branding categories documented in `/app/memory/*_TOOLS_AUDIT.md`.

## April 26, 2026 (Tier 6 sweep)
- **Customer Appointment Request → Owner Email Notification (NEW)**
  - When a customer submits an appointment request via portal, tenant owner now receives an HTML email immediately (verified by `email_logs` rows with status='sent', response_code=202).
  - Try/except wrapper means SendGrid failure does NOT block appointment creation.
- **Admin PDF Endpoints (NEW)**
  - `GET /api/quotes/{id}/pdf` — admin can download quote PDF (no portal login required).
  - `GET /api/invoices/{id}/pdf` — admin can download invoice PDF with PAID/UNPAID status badge.
- **Tier 6 Backend Audit (20/20 PASS)** — AI assistant multi-turn, email composer, voice transcribe, image-gen route, SendGrid wiring, customer portal invoice PDF all verified.
- **Backlog tracked (NOT_IMPLEMENTED, deferred):** `GET /api/ai/tools` list, `POST /api/ai/extract-invoice`, server-side clear-chat, payroll PDF, work-ticket PDF.
- **Trackers updated:** PRELAUNCH_CHECKLIST.md Tier 6 sections + Section 17 added to user personal checklist (31 items: AI UI, mail-client rendering, PDF visual quality, SPF/DKIM/DMARC).

## April 26, 2026 (later)
- **Customer Request Appointment Feature (NEW) + Tier 5 Backend Sweep**
- New: `POST /api/portal/appointments/request` — customer-initiated appointment requests with `status="requested"`. Notification row auto-created for shop staff.
- New: `PUT /api/appointments/{id}/confirm` — admin confirms request, supports time/employee override. Flips status to `confirmed`.
- New: `PUT /api/appointments/{id}/reject` — admin rejects, sets status to `cancelled` and appends reason to notes.
- New UI: Portal Appointments page now has "Request Appointment" button + dialog (type / date / time / location / notes). New "Pending Confirmation" amber badge for `requested` status. Toast feedback on submit.
- New: `DELETE /api/admin/users/{id}` with three guardrails (self / staff-perm / last-owner-of-tenant).
- Bug fix: `routes/auth.py` had broken references to `Permission.USERS_EDIT` (enum doesn't exist). Fixed to `USERS_MANAGE` — would have caused `AttributeError` on first call to admin reset-password / status routes.
- Tier 5 backend audit: 28/29 PASS via testing agent (iteration_134). Sections 5.1, 5.4, 5.7, 5.8, 5.10, 5.11, 5.12 verified working. Manual UI/Stripe/email items migrated to Section 16 of personal checklist.
- Trackers updated: PRELAUNCH_CHECKLIST.md, OPEN_ITEMS_TRACKER.md, POSTFIX_RETEST_RESULTS.md, SECTION1_USER_PERSONAL_CHECKLIST.md (Section 16 added with 25 items).

## April 26, 2026
- **Prelaunch Tier 1–4 Final Mop-Up Complete (iteration_132 follow-up)**
- Security fix: Added `_require_payroll_view_access()` guard to all GET payroll endpoints (`/report`, `/balance`, `/transactions`, `/hours`, `/signoff`, `/timesheet`, `/pay-period`, `/timeclock-shifts`, `/legacy-manual-entries`, `/schedule`) — staff role now correctly receives `403`.
- New endpoint: `GET /api/customers/export` — CSV export of customers (name, email, phone, company, status, notes, created_at).
- New endpoint: `POST /api/workflow-templates/{id}/apply` — applies a template to an order, creates production tasks per stage for each ticket; supports `replace_existing=true`.
- New endpoint: `POST /api/workflow-templates/{id}/duplicate` — copies a template into a tenant-owned "(Copy)" version.
- New endpoint: `GET /api/portal/appointments` — customer portal list of scheduled appointments.
- New endpoint: `GET /api/employee-portal/dashboard` — alias of `/work-summary` (matches frontend spec).
- Enhanced: `GET /api/payroll/report` now accepts `format=csv` query param, returns streaming CSV.
- Updated trackers: `PRELAUNCH_CHECKLIST.md`, `PRELAUNCH_OPEN_ITEMS_TRACKER.md`, `PRELAUNCH_POSTFIX_RETEST_RESULTS.md`, `PRELAUNCH_SECTION1_USER_PERSONAL_CHECKLIST.md` (Section 15 added).

## March 27, 2026
- Updated all documentation (Feature Catalog, Build Roadmap, Docs pages) to reflect Order/Job Ticket system
- Removed all references to old "Jobs" module from docs and navigation
- Updated DocsQuotesJobs → DocsOrdersTickets (Orders & Job Tickets documentation)
- Updated DocsEmployees with schedule feature documentation
- Updated GettingStarted guide with order workflow
- Updated DocsOverview with 4-layer architecture description

## March 26, 2026
- Fixed: Sales and expense recording (created /api/financials/sales and /api/financials/expenses endpoints)
- Fixed: Schedule dialog not opening (removed conditional wrapper)
- Fixed: Owner permissions (hasPermission now grants all permissions to owner role)
- Fixed: Contact Support now emails donnell@signguy-ai.com
- Navigation: Financials moved to top-level, Reports = shortcuts page
- Theme: Applied light theme to PricingSetup, CompanySettings, PaymentSettings
- Workflow Templates: Removed duplicate QC toggle, kept only Required
- New Order Form: Added ticket buttons near Save, fixed zero placeholder, better error handling
- Square footage: Default changed to inches (18x24 = 3 sqft, not 432)
- LivePricingPreview: Added all finishing options, fixed apparel trigger
- Production Board: Shows ticket name first, task name secondary

## March 25, 2026
- Fixed: Setup fee markup bug — $25 fee was causing $67 increase, now adds exactly $25 (flat, not marked up)
- Fixed across ALL 6 calculator functions
- Added: Generate Work Order on order detail
- Added: Apparel quantity discounts (5-25% based on qty tiers)
- Improved: Stripe Connect error messaging

## March 24, 2026
- Built: File upload system for orders (upload, list, delete)
- Built: Live pricing preview on new order form (calls pricing API in real-time)
- Built: Employee schedule system (weekly grid, shift dialog, save to DB)
- Built: Materials & Pricing admin page (global rates, material CRUD)
- Added: Files tab on Order Detail page
- Added: Order action buttons (Generate Quote/Invoice/Work Order, Email, Status, Portal)
- Created: 30 database indexes for production performance

## March 23, 2026
- Built: Full Banner category schema (24 fields, 7 subtypes)
- Built: Full Apparel category schema (27 fields, 8 subtypes, size grid, print locations with per-location details)
- Built: Rigid Signs, Cut Vinyl, Digital Print, Vehicle Wrap schemas (22-30 fields each)
- All material options now from centralized catalog (not hardcoded)
- Calculator wiring: all dynamic fields map to pricing engine
- Quick Entry / Detailed Entry modes for job tickets
- Legacy Jobs removed from navigation, redirects to Orders
- Dashboard quick actions updated (New Job → New Order)
- Dark shell / light content theme applied globally (20+ pages)
- Container widened to 1600px

## March 22, 2026
- Built: Complete 4-layer Order system backend (Orders, Job Tickets, Production Tasks, Workflow Templates)
- Built: Frontend pages (OrdersPage, OrderDetail, NewOrderForm, JobTicketDetail, ProductionBoard, WorkflowTemplateManager)
- 6 default workflow templates, activity logging, status roll-up
- Terms of Service and Privacy Policy pages
- Color scheme: amber/gold → violet/purple across all Founders-branded pages
- Founder grace period (14 days read-only after subscription lapse)
- Multiple production bug fixes (login, promo codes, onboarding, mobile nav)

## March 20, 2026
- Stage 1 Critical Fixes: AI rate limiter, promo code system, invoice line items
- Deployment fix: requirements.txt cleaned from 137 → 24 packages
- SendGrid email configured
- Production setup endpoint and page (/setup)
