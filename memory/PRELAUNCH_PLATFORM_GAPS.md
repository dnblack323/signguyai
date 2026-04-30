# Pre-Launch Platform Gaps — "Things You Don't Know You Need Until You Need Them"

Originally surfaced after the user added the Impersonate-User admin tool and asked
what other operator/admin tools would be needed for launch.

## ✅ TOP 5 P0 GAPS — ALL COMPLETE (Feb 15, 2026)
The five most critical pre-launch admin tools are now shipped, audited, and end-to-end verified.

---

## P0 — Will hit in week 1 (TOP 5 to ship before launch)

1. **Admin Audit Log** ✅ DONE (Feb 15, 2026)
   - Collection: `admin_audit_log`
   - Helper: `services/admin_audit.py::log_admin_action()`
   - Endpoints: `GET /api/platform-admin/audit-log`, `/audit-log/actions`, `/audit-log/{id}`
   - Page: `/platform-admin/audit-log`
   - Wired into impersonation start/exit/manual-end + checklist updates.
   - Next wiring opportunities: tenant suspend/reactivate, tenant create/delete, plan changes, refunds, credit grants, force-logout, role changes, password resets — wire as those features are added.

2. **Suspend / Reactivate Tenant** ✅ DONE (Feb 15, 2026)
   - Endpoints: `POST /api/platform-admin/tenants/{id}/suspend`, `/reactivate`.
   - Tenant doc: `is_active`, `suspension_reason`, `suspended_at`, `suspended_by`, `suspended_by_email`, `reactivated_at`, `reactivated_by`, `reactivated_by_email`.
   - Login + active session both blocked with HTTP 403 + structured payload `{code: "tenant_suspended", message, reason, suspended_at}`.
   - Self-lockout protection: cannot suspend a tenant that contains a `platform_admin` user.
   - Idempotent.
   - Auto audit log via `log_admin_action`.
   - UI: red "Suspend"/green "Reactivate" buttons + dialogs on tenant detail; red banner on suspended tenant; suspended badge in tenant list.
   - User-side: `/account-suspended` screen shows reason + Contact Support mailto. AuthContext login, fetchUserProfile, and AppContext axios interceptor all detect tenant_suspended and route there.

3. **Failed-Payment / Dunning Workflow** ✅ DONE (Feb 15, 2026)
   - Service: `services/dunning.py` — `record_payment_failure()` and `record_payment_success()`.
   - Tenant doc: `payment_failed_count`, `first_payment_failure_at`, `last_payment_failure_at`, `last_payment_succeeded_at`, `auto_suspended_for_payment`.
   - State machine: failure 1 → email "N attempts left" → failure 2 → email → failure 3 → AUTO-SUSPEND + email → payment success → AUTO-REACTIVATE + welcome-back email → counters reset.
   - Threshold configurable via env `DUNNING_AUTO_SUSPEND_AFTER` (default 3).
   - Self-lockout protection: never auto-suspends a tenant with a platform_admin user.
   - Manual override endpoint: `POST /api/platform-admin/tenants/{id}/mark-paid` for NET-60, wires, cleared chargebacks, etc.
   - Audit log entries: `payment.failed`, `dunning.auto_suspend`, `payment.succeeded`, `dunning.auto_reactivate`, `payment.manual_mark_paid` — all under `action_category="billing"`.
   - UI: "Billing & Dunning" card on tenant detail with failed-attempts counter, timestamps, auto-suspended badge, "Mark as Paid" button + dialog.
   - Wired into existing Stripe webhook handlers `handle_invoice_payment_failed` and `handle_invoice_payment_succeeded`.

4. **Email Deliverability Dashboard + un-mock SendGrid** ✅ DONE (Feb 15, 2026)
   - SendGrid is **already live** (verified by 202 responses on real welcome-back / payment emails).
   - Schema: `email_logs.delivery_status`, `email_logs.sg_message_id`, `email_logs.events[]`. Back-filled 40 historical records.
   - SendGrid Event Webhook: `POST /api/webhook/sendgrid` matches events to `email_logs` and refines `delivery_status`.
   - New endpoints: `GET /api/platform-admin/email-logs` (filterable), `GET /api/platform-admin/email-logs/summary` (aggregate counts).
   - Page: `/platform-admin/email-logs` with summary tiles + filterable table + detail dialog showing every captured event.
   - Per-tenant deliverability tile on tenant detail page (auto-hides when no email history).
   - To finish the deployment side: configure SendGrid → Settings → Mail Settings → Event Webhook → URL = `https://<host>/api/webhook/sendgrid`, then enable the "Bounced", "Spam Reports", "Dropped", "Delivered" toggles.

5. **System-wide Announcement Banner + Maintenance Mode Toggle** ✅ DONE (Feb 15, 2026)
   - Collection `platform_settings` (single `id="global"` doc) holds both states.
   - Public endpoints `GET /api/platform/announcement`, `GET /api/platform/maintenance`. Admin endpoints `PUT /api/platform-admin/announcement`, `PUT /api/platform-admin/maintenance`, `GET /api/platform-admin/settings`.
   - Announcement: message, severity (info/warning/critical), dismissable, optional expires_at. Per-user dismiss is keyed by updated_at so new edits re-show for everyone.
   - Maintenance Mode: ASGI middleware in `server.py` returns HTTP 503 + structured `maintenance_mode` payload on POST/PUT/PATCH/DELETE for non-admin users. Allowlist keeps auth, platform-admin, webhooks, and health checks flowing.
   - Audit log entries: `announcement.set`, `announcement.clear`, `maintenance.enable`, `maintenance.disable` (`action_category="platform"`).
   - UI: `<GlobalBanner>` sticky on every page (re-polls every 60s); new `/platform-admin/site-settings` page; "Site Settings" button on Platform Admin home.

---

## P1 — Will hit in month 1

6. **Tenant data export (GDPR / portability)** — NOT STARTED
7. **Right-to-be-forgotten / hard delete** — NOT STARTED (UI page exists, admin trigger missing)
8. **Feature flags / kill switches per tenant** — NOT STARTED (most relevant: per-AI-tool kill switch)
9. **Login & session activity per user** — NOT STARTED
10. **2FA / MFA for platform-admin and tenant-owner roles** — NOT STARTED
11. **API key / personal access tokens for tenants** — NOT STARTED

---

## P2 — Month 2-3

12. **Onboarding analytics funnel** (drop-off per `OnboardingHub` step)
13. **Usage / quota visibility per tenant** (credits burned, customer counts, plan-fit)
14. **In-app support chat / "Help" beacon** with auto-context packet
15. **"View as customer" mode for the customer portal**
16. **Bulk import safety net / undo last import**
17. **Email/Notification preferences per user** (CAN-SPAM/CASL)
18. **Status page** (even static)

---

## P3 — Nice to have

19. **SSO (Google/Microsoft Workspace)**
20. **Webhook subscriptions for tenants**
21. **Sandbox / test mode for tenants**
22. **Tenant-facing audit log** ("who edited this customer record?")
