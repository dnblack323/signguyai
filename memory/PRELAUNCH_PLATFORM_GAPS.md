# Pre-Launch Platform Gaps — "Things You Don't Know You Need Until You Need Them"

Originally surfaced after the user added the Impersonate-User admin tool and asked
what other operator/admin tools would be needed for launch.

Each P0 item is being implemented one at a time on user request.

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

3. **Failed-Payment / Dunning Workflow** — NOT STARTED
   - State machine: declined → grace_period → restricted → suspended → cancelled.
   - Stripe webhook hooks for `invoice.payment_failed`, `invoice.payment_succeeded`.
   - Admin override "manually mark paid".
   - Email notifications at each transition.

4. **Email Deliverability Dashboard + Un-mock SendGrid** — PARTIAL
   - SendGrid is currently mocked. Real delivery is the precondition.
   - Need: bounces / spam complaints / last-sent timestamp per tenant, surfaced on Platform Admin tenant detail.
   - Re-use existing `email_logs` collection.

5. **System-wide Announcement Banner + Maintenance Mode Toggle** — NOT STARTED
   - Single global banner ("We deploy at 11pm ET", outage notices) controllable by Platform Admin.
   - Maintenance/read-only mode flag that returns 503 from mutation endpoints with friendly message.

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
