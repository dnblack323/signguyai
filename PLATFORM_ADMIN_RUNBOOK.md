# SignGuy AI — Platform Admin Runbook

> Your day-to-day playbook for running the platform side of SignGuy AI.
> This is the "what do I click, when, and why?" guide for everything in
> `/platform-admin`. Read top to bottom on launch day, then keep it as a
> reference.

**Last updated:** April 30, 2026
**Audience:** You — the platform owner / `platform_admin` role.
**Login:** `thesigntistslab@gmail.com` / `password123`

---

## Table of contents

1. [How to get to the Platform Admin area](#1-how-to-get-to-the-platform-admin-area)
2. [The Platform Admin home page](#2-the-platform-admin-home-page)
3. [Tenant Detail page (your per-tenant cockpit)](#3-tenant-detail-page-your-per-tenant-cockpit)
4. [Suspend / Reactivate a tenant](#4-suspend--reactivate-a-tenant)
5. [Failed-payment dunning (auto) + manual "Mark as Paid"](#5-faile dpayment-dunning-auto--manual-mark-as-paid)
6. [Set a per-tenant dunning threshold](#6-set-a-per-tenant-dunning-threshold)
7. [Impersonate a tenant user](#7-impersonate-a-tenant-user)
8. [Onboarding checklist (per tenant)](#8-onboarding-checklist-per-tenant)
9. [Broadcast Email (NEW — mass email to tenant owners)](#9-broadcast-email-new--mass-email-to-tenant-owners)
10. [Site Settings: Announcement Banner + Maintenance Mode](#10-site-settings-announcement-banner--maintenance-mode)
11. [Email Deliverability Dashboard](#11-email-deliverability-dashboard)
12. [Admin Audit Log](#12-admin-audit-log)
13. [Launch-day runbook (do these in order)](#13-launch-day-runbook-do-these-in-order)
14. [Common scenarios cheat-sheet](#14-common-scenarios-cheat-sheet)
15. [Setup work that still needs to happen outside the app](#15-setup-work-that-still-needs-to-happen-outside-the-app)

---

## 1. How to get to the Platform Admin area

1. Log in to the app as `thesigntistslab@gmail.com`.
2. In the top nav, click **Platform Admin**. You land on `/platform-admin`.

If you don't see the Platform Admin link, you're not logged in as a `platform_admin`. Log out and back in with the right account.

---

## 2. The Platform Admin home page

**URL:** `/platform-admin`

This is the master view. You'll see:

- **Top-right action buttons:**
  - **Broadcast Email** — send a one-off email to tenant owners (see §9)
  - **Site Settings** — announcement banner + maintenance mode (see §10)
  - **Email Deliverability** — outgoing-email dashboard (see §11)
  - **View Audit Log** — read-only history of every privileged action (see §12)
- **Stats cards** — total tenants, total users, etc.
- **Tenant list** — every tenant on your platform. Search by name or owner email. Each row shows plan, user count, and status (Active / Suspended).

**What you do here:** Click any tenant row to drill into that tenant's detail page (§3), or use a top-right button to do a platform-wide action.

---

## 3. Tenant Detail page (your per-tenant cockpit)

**URL:** `/platform-admin/tenants/{id}` (click any tenant from the list)

A single page with everything you can do **to or about one specific tenant**:

- **Header** — tenant name, owner email, plan, "Suspended" red banner (if applicable).
- **Profile card** — when joined, last activity, founder badge, etc.
- **Billing & Dunning card** — failure count, last failure / success timestamps, threshold, "Mark as Paid" button, "Set Threshold" button. Auto-hides if there's nothing to show.
- **Email Deliverability mini-tile** — counts for sent / delivered / bounced for this tenant only. Click through to the full dashboard filtered to this tenant.
- **Onboarding checklist card** — % complete + the items themselves, with manual "mark complete" toggle for each.
- **Users list** — every user inside the tenant, with **Impersonate** button next to each.
- **Action buttons (top-right of header):** Suspend / Reactivate.

---

## 4. Suspend / Reactivate a tenant

### Suspend

1. Open the tenant on Tenant Detail.
2. Click the red **Suspend Tenant** button (top-right).
3. A dialog asks for a **reason** — type one sentence (e.g., "Non-payment after dunning").
4. Click **Suspend**.

What happens:
- The tenant is frozen. Existing logged-in browser tabs die on the next API call.
- Login is blocked with a friendly `/account-suspended` page that shows the reason and your contact email.
- You **cannot suspend yourself** — the system refuses to suspend a tenant that contains a `platform_admin` user.
- An audit row is written automatically (action: `tenant.suspend`).

### Reactivate

1. On the same tenant page, click the green **Reactivate Tenant** button (only visible if currently suspended).
2. Optional: type a note (it gets included in the "Welcome back" email).
3. Make sure the **"Send the owner a 'Welcome back' email"** checkbox is on (default) — leave on unless you don't want to email them.
4. Click **Reactivate**.

What happens:
- Tenant is unfrozen, existing tokens work again.
- Owner receives a "Welcome back" HTML email if you left the checkbox on.
- Audit row written (`tenant.reactivate`).

### When to use it

| Reason | Action |
|---|---|
| Refund dispute / chargeback | Suspend until resolved |
| ToS violation | Suspend |
| Non-payment that auto-dunning escalated to suspended | Already auto-handled, but you can also manually re-suspend if they re-fail |
| Customer asked to cancel | Suspend (then later, fully delete out-of-band) |
| Resolved | Reactivate |

---

## 5. Failed-payment dunning (auto) + manual "Mark as Paid"

You don't have to do anything for normal dunning — it's automatic via Stripe webhooks.

### What runs automatically

| Event | What happens |
|---|---|
| Stripe `invoice.payment_failed` (1st time) | Email tenant: "you have 2 attempts left" |
| 2nd failure | Email tenant: "you have 1 attempt left" |
| 3rd failure | Tenant **auto-suspended**, email "account suspended" (unless founder — see grace period) |
| Founder hits threshold | 24-hour grace window starts (audit row `dunning.grace_started`). Suspension only if next failure arrives **after** the window expires. |
| Stripe `invoice.payment_succeeded` | Failure counter reset. If tenant was auto-suspended for non-payment, **auto-reactivated**. |

### When to use "Mark as Paid" manually

Open Tenant Detail → "Billing & Dunning" card → **Mark as Paid** button.

Use this when:
- A tenant pays you by **wire transfer**, **check**, or **cash**.
- You issue a **NET-60 invoice** outside Stripe.
- A **chargeback was reversed** in your favor and you cleared it manually.

What it does:
- Resets the failure counter to zero.
- Auto-reactivates the tenant if they were auto-suspended.
- Writes an audit row (`payment.manual_mark_paid`).

---

## 6. Set a per-tenant dunning threshold

The default is "3 strikes and auto-suspend." For a specific tenant you can override.

**How:** Tenant Detail → "Billing & Dunning" card → **Set Threshold** button → enter a number → Save.

When to override:
- **Higher (e.g., 5):** anchor customer, founder, large account you don't want auto-suspended easily.
- **Lower (e.g., 2):** chronically late tenant where you want to escalate faster.
- **Clear it:** removes the override, returns to global default.

Audit row: `dunning.threshold_set`.

---

## 7. Impersonate a tenant user

The single most useful support tool you have.

**How:**
1. Open Tenant Detail.
2. Find the user in the Users list.
3. Click **Impersonate** next to their row.
4. You're now logged in as them, with a banner across the top reminding you you're impersonating.
5. Click **Exit Impersonation** in the banner when done.

What's happening behind the scenes:
- You get an impersonation token. The app behaves exactly as that user sees it.
- Every action you take is logged in their tenant context **but** with your real identity recorded in the audit log.
- The session is also tracked in `impersonation_logs` (visible to you).

When to use it:
- Tenant says "the button doesn't work" — see exactly what they see.
- Investigating a data issue without asking them for screenshots.
- Reproducing a bug they reported.

Important: **do not change data on their behalf without their consent.** Audit log will show you did it.

---

## 8. Onboarding checklist (per tenant)

Every brand-new tenant gets a default checklist (company info, logo, first customer, etc.).

**Where:** Tenant Detail → "Onboarding Checklist" card.

**What you do:**
- Glance at the % complete to see how engaged a new tenant is.
- Click any item's checkbox to mark it complete on their behalf.
- Use **Impersonate** (§7) if they're stuck and you want to do the setup with them.

When to use:
- First 7 days after a new tenant signs up.
- Before reaching out to a tenant who hasn't used the product in a week.

---

## 9. Broadcast Email (NEW — mass email to tenant owners)

This is the feature you asked for. It sends a one-off email to one or more tenant owners.

**URL:** `/platform-admin/broadcast-email`. Reach it from the **Broadcast Email** button on the Platform Admin home page.

### How to send a broadcast

1. **Subject** — type a short, clear subject line.
2. **Body** — type plain text. Blank lines start new paragraphs; single newlines become line breaks. The system wraps it in HTML automatically.
3. **Audience** — pick one:
   - **All tenant owners** — every tenant with an owner email
   - **Only active tenants** — skips suspended
   - **Only suspended tenants** — useful for "we'd like to win you back" messages
   - **Only founders** — your inner circle
4. The page shows **how many tenants will receive it** in real time.
5. **Always send a test first.**
   - The "Test recipient" field is pre-filled with your own email.
   - Click **Send test to {your email}** — you'll get one preview email.
   - Read it. Check formatting, links, tone. Fix typos. Send another test.
6. When the test looks right, click **Send to N tenants**.
7. A confirm dialog summarizes subject, audience, recipient count.
8. Click **Yes, send now**.
9. The result panel appears with sent count, failed count, and the first 25 failures (if any).

### What gets logged

- **Single audit row** per broadcast (action: `broadcast_email.send`) with subject, audience, recipient count, sent count, failed count.
- Each individual email also lands in the **Email Deliverability Dashboard** (§11) with its SendGrid `sg_message_id`, so you can track who opened, who bounced, etc.

### Things to know

- **Cost:** uses your existing SendGrid plan. Each email is one SendGrid send.
- **Speed:** sends are sequential. A 1000-tenant blast takes ~1–2 minutes. Don't close the tab mid-send.
- **No undo:** once you click "Yes, send now" the emails go out. The audit log has a record but you can't unsend.
- **Dedupe:** if one human owns multiple tenants, they only get one email.
- **Personalization:** ✅ supported. Use `{{owner_first_name}}`, `{{tenant_name}}`, `{{owner_email}}` in either subject or body. Each recipient gets their own values rendered in. Unknown placeholders are left as-is so typos are visible at preview time. All values are HTML-escaped for safety.
- **Rate limits (per-admin):** 10 full broadcasts per hour, 30 test sends per hour. Returns HTTP 429 over the cap — wait an hour or use a different admin account.
- **Body / subject size limits:** subject ≤ 200 chars, body ≤ 50 KB. Beyond that the request is rejected with 422. (For larger emails, use linked CDN images, not embedded.)
- **SendGrid required:** if `SENDGRID_API_KEY` is missing the endpoint returns 503 instead of silently "succeeding" with 0 emails sent.

### When to use it

| Situation | Audience |
|---|---|
| Announcing a new feature | All owners (or active only) |
| Pricing change | Active only |
| Outage post-mortem | Active only |
| "We'd love to have you back" recovery message | Suspended only |
| Founder's-circle update | Founders only |

---

## 10. Site Settings: Announcement Banner + Maintenance Mode

**URL:** `/platform-admin/site-settings`

Two cards on one page. Both audit-logged.

### Announcement Banner (top card)

A message that appears at the top of every page in the app, **including the login page**, so logged-out visitors see it too.

**How:**
1. Type a message.
2. Pick severity: **info** (blue), **warning** (amber), **critical** (red).
3. Optional: set an **expires-at** time. The banner auto-vanishes after that.
4. Optional: toggle **dismissable** — if on, each user can close the banner once and it stays closed for them.
5. Click **Publish**.

Live users see the new banner within 60 seconds (no refresh needed).

To **clear** it: click the **Clear** button on the same card.

When to use:
- Scheduled maintenance announcement.
- Pricing change effective in 7 days.
- New feature available now.
- Outage update ("we know — fixing it").
- Holiday hours.

### Maintenance Mode (bottom card)

Hard stop on all writes for everyone except platform admins.

**How:**
1. Type a user-facing message ("scheduled maintenance, back at 3pm EST").
2. Click **Enable**.
3. Do your work — DB migration, key rotation, deploy, etc.
4. Click **Disable** when done.

What it does:
- Every POST/PUT/PATCH/DELETE on `/api/*` returns HTTP 503 with your message — **except** for platform admins, who keep working.
- GETs (reads) still work — the app doesn't go totally dark; users can still see their data.
- Stripe webhook (`/api/webhook/stripe`) and SendGrid webhook (`/api/webhook/sendgrid`) **always pass through**, so payments and email events still flow.

When to use:
- Database migration touching payment data.
- Stripe key rotation.
- Deploy that touches money.
- Emergency stop because something's burning.

When **not** to use:
- Routine deploys (the app hot-reloads — no maintenance window needed).
- Cosmetic frontend tweaks.

---

## 11. Email Deliverability Dashboard

**URL:** `/platform-admin/email-logs`

What it shows:
- **Summary tiles:** total / delivered / pending / bounced / complaints / failed
- **Filter bar:** tenant, recipient email, status, date range
- **Table:** every outgoing email — subject, recipient, tenant, current status, SendGrid message ID
- **Detail dialog (click a row):** all SendGrid events captured for that one email — every "delivered", "open", "click", "bounce", with reasons

When to use:
- Tenant says "my customer never got the invoice" — open the page, search the customer's email, see exactly what SendGrid reported.
- Spotting tenants whose customers are bouncing a lot (they may have a bad list).
- Verifying a broadcast email (§9) actually delivered.

**Setup needed before this works fully:**
Until you point SendGrid's Event Webhook at `https://<your-app>/api/webhook/sendgrid`, the dashboard only shows "sent" — never "delivered" or "bounced". See [§15](#15-setup-work-that-still-needs-to-happen-outside-the-app).

---

## 12. Admin Audit Log

**URL:** `/platform-admin/audit-log`

Read-only history of every privileged action ever taken. Includes:

| Action | When written |
|---|---|
| `tenant.suspend` / `tenant.reactivate` | You suspend/reactivate a tenant |
| `dunning.auto_suspend` / `dunning.auto_reactivate` | Stripe webhook auto-suspend/reactivate |
| `dunning.grace_started` | Founder grace window starts |
| `dunning.threshold_set` | You change a per-tenant threshold |
| `payment.failed` / `payment.succeeded` / `payment.manual_mark_paid` | Stripe webhook or your manual override |
| `impersonation.start` / `impersonation.exit` | Impersonate / Exit |
| `announcement.set` / `announcement.clear` | Banner publish / clear |
| `maintenance.enable` / `maintenance.disable` | Maintenance toggle |
| `broadcast_email.send` | Mass email blast |
| `onboarding.checklist.update` | Manual checklist tick |

What you do:
- Open it when you need to prove what happened.
- Filter by actor (your email), action, target, tenant, date range.
- Click any row for the full detail (IP, user agent, metadata, target, status).

---

## 13. Launch-day runbook (do these in order)

A clean checklist for the morning you turn the platform on for real customers.

| Step | Action | Where |
|---|---|---|
| 1 | Verify `thesigntistslab@gmail.com` can log in | `/login` |
| 2 | Confirm Platform Admin link visible | top nav |
| 3 | Open Audit Log — make sure it loads (no schema issues) | `/platform-admin/audit-log` |
| 4 | Open Site Settings — set a launch-day announcement: severity=info, dismissable=on, message="Welcome to SignGuy AI! We're live." | `/platform-admin/site-settings` |
| 5 | Send a **broadcast test** to yourself with the launch announcement | `/platform-admin/broadcast-email` |
| 6 | Verify the test arrived (check inbox + spam) | your email |
| 7 | Send the **real broadcast** to all owners | `/platform-admin/broadcast-email` |
| 8 | Open Email Deliverability — confirm broadcast emails landed with status=sent | `/platform-admin/email-logs` |
| 9 | Confirm SendGrid event webhook is wired (statuses move from "sent" → "delivered") | `/platform-admin/email-logs` (check 5 min after step 7) |
| 10 | Spot-check an audit row for `broadcast_email.send` | `/platform-admin/audit-log?action=broadcast_email.send` |
| 11 | Test maintenance mode (enable, do nothing, disable) — confirm the 503 lands and you stay logged in | `/platform-admin/site-settings` |
| 12 | Verify Stripe webhook is in live mode (not test mode) | Stripe dashboard |
| 13 | Verify your "from" email's SPF / DKIM / DMARC are passing | mail-tester.com |
| 14 | Stay near a computer for 24 hours | yourself |

---

## 14. Common scenarios cheat-sheet

| If a tenant... | You... |
|---|---|
| Says "I can't log in" | Check Tenant Detail for `Suspended` banner. If yes, find out why before reactivating. |
| Says "I never got the email" | Email Deliverability → search their email → show them the SendGrid trail. |
| Says "this button doesn't work" | Impersonate them and see for yourself. |
| Has 3 failed Stripe payments | Already auto-handled. Check audit log for `dunning.auto_suspend`. |
| Pays you by check | Tenant Detail → Mark as Paid. |
| Is a founder you want to cut slack | Tenant Detail → Set Threshold → 5. |
| You want to message everyone | Broadcast Email. |
| You want to message everyone *for free, in-app* | Site Settings → Announcement. |
| You're about to deploy something risky | Maintenance Mode on, deploy, off. |
| Some legal thing happens | Audit Log filtered by tenant_id. |
| Someone asks "who suspended us?" | Audit Log → action=`tenant.suspend`, target_id=their_id. |

---

## 15. Setup work that still needs to happen outside the app

These can't be done by code — they're external dashboard tasks.

| # | Task | Where | Why it matters |
|---|---|---|---|
| 1 | Point **SendGrid Event Webhook** at `https://<your-app>/api/webhook/sendgrid` | SendGrid dashboard → Settings → Mail Settings → Event Webhook | Until you do this, Email Deliverability only knows "sent" — never delivered/bounced/spam. |
| 2 | Set **SPF, DKIM, DMARC** records for your sender domain | DNS provider (e.g., Cloudflare) | Without these, your emails go straight to spam for many recipients. Already on your personal pre-launch checklist. |
| 3 | Switch Stripe to **live mode** | Stripe dashboard | Test mode key in `.env` won't accept real payments. |
| 4 | Register your **Stripe webhook** in live mode | Stripe dashboard → Webhooks | Pointed at `https://<your-app>/api/webhook/stripe`. Without this, dunning won't fire on real payments. |
| 5 | Decide where **Vehicle Wrap Cost Calculator** lives | (product decision) | Currently hidden from Racing; backend code preserved. Either delete or relocate to Pricing/Quotes/Business. |
| 6 | Decide CSV-import error policy | (product decision) | Currently all-or-nothing rollback on any row failure. May want skip-and-report instead. |

---

## Appendix A — API endpoints (for your reference if you ever script against them)

All require `Authorization: Bearer <admin-token>`.

```
# Tenants
GET    /api/platform-admin/tenants
GET    /api/platform-admin/tenants/{id}
POST   /api/platform-admin/tenants/{id}/suspend       body: {reason}
POST   /api/platform-admin/tenants/{id}/reactivate    body: {note?, notify_owner?}
POST   /api/platform-admin/tenants/{id}/mark-paid
PUT    /api/platform-admin/tenants/{id}/dunning-threshold  body: {threshold|null}

# Impersonation
POST   /api/platform-admin/impersonate              body: {target_user_id}
POST   /api/platform-admin/exit-impersonation
GET    /api/platform-admin/impersonation-logs
POST   /api/platform-admin/impersonation-logs/{id}/end

# Onboarding
GET    /api/platform-admin/tenants/{id}/checklist
PATCH  /api/platform-admin/tenants/{id}/checklist/{item_id}
GET    /api/platform-admin/tenants/{id}/checklist/progress

# Site settings
GET    /api/platform/announcement      (public)
GET    /api/platform/maintenance       (public)
PUT    /api/platform-admin/announcement
PUT    /api/platform-admin/maintenance
GET    /api/platform-admin/settings

# Broadcast email (NEW)
GET    /api/platform-admin/broadcast-email/audience-counts
POST   /api/platform-admin/broadcast-email
       body: {subject, html_body, target?, tenant_ids?, test_to?}

# Audit log
GET    /api/platform-admin/audit-log
GET    /api/platform-admin/audit-log/actions
GET    /api/platform-admin/audit-log/{id}

# Email deliverability
GET    /api/platform-admin/email-logs
GET    /api/platform-admin/email-logs/summary

# Webhooks (no auth — verified by signature / source)
POST   /api/webhook/stripe
POST   /api/webhook/sendgrid
```

---

## Appendix B — What is *not* yet built (in case you ask)

These do **not** exist yet. Each is a future feature, not a hidden tool:

- Mass email to **end customers** of all tenants (this runbook only covers tenant *owners*).
- Bulk suspend / reactivate (one-at-a-time only).
- Tenant-to-tenant broadcast / chat.
- In-app surveys.
- Per-recipient personalization in Broadcast Email (e.g., `{{tenant_name}}` in body).
- Confirm/Reject quick-action buttons inside Appointment notification emails.
- Internal Notes + User invite flow on Tenant Detail (Phase 2).

If you want any of these, ask and I'll scope them.

---

**End of runbook.** Bookmark `/platform-admin` and you've got the whole platform in one click.
