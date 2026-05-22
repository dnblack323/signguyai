"""
Generate a high-level day-by-day changelog PDF for Jan 27 - Feb 15, 2026.
Synthesized from:
- /app/memory/CHANGELOG.md (dated entries Feb 12 + Feb 15)
- /app/memory/PRD.md (dated entries)
- git history (file-add signal per day for Jan 27 - Feb 11, which has no PRD entries)
"""

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, PageBreak
)

OUT_PATH = "/app/memory/CHANGELOG_JAN27_FEB15_2026.pdf"

# --- Content (high-level only, no tiny file refs) ---
DAYS = [
    {
        "date": "Mon, Jan 27, 2026",
        "title": "Project kickoff",
        "items": [
            "SignGuy AI repository created — initial empty commit.",
            "Decision: full-stack SaaS for sign/graphics shops (CRM, quotes, invoicing, jobs, payroll, webstores, AI tools).",
        ],
    },
    {
        "date": "Tue, Jan 28, 2026",
        "title": "Application scaffold + first admin pages",
        "items": [
            "FastAPI backend + React (CRA) + Shadcn UI baseline wired up.",
            "First admin pages stood up: Dashboard, Customers, Quotes, Invoices, Jobs, Productivity, Financials, Payroll, TimeClock, Webstores, AI Tools.",
            "Top-level MainLayout (sidebar + topbar) shipped.",
        ],
    },
    {
        "date": "Wed–Thu, Jan 29–30, 2026",
        "title": "Polish + iteration on day-1 pages",
        "items": [
            "No new top-level pages — UI/UX iteration only.",
        ],
    },
    {
        "date": "Sat, Jan 31, 2026",
        "title": "Invoice preview",
        "items": [
            "Invoice Preview Modal added so invoices can be reviewed before send/download.",
        ],
    },
    {
        "date": "Sun, Feb 1, 2026",
        "title": "Theme toggle",
        "items": [
            "Light/Dark theme toggle component added.",
        ],
    },
    {
        "date": "Mon, Feb 2, 2026",
        "title": "Product catalog",
        "items": [
            "Products page added (catalog of items used by quotes/invoices/webstores).",
        ],
    },
    {
        "date": "Tue–Wed, Feb 3–4, 2026",
        "title": "Iteration",
        "items": [
            "Stability + visual polish; no new modules.",
        ],
    },
    {
        "date": "Thu, Feb 5, 2026",
        "title": "Public Storefront",
        "items": [
            "Public-facing Storefront page launched — customers can browse a tenant's webstore without logging in.",
        ],
    },
    {
        "date": "Fri, Feb 6, 2026",
        "title": "Iteration",
        "items": [
            "Refinements to storefront + admin pages.",
        ],
    },
    {
        "date": "Sat, Feb 7, 2026",
        "title": "Auth + Customer Portal v1",
        "items": [
            "Real Login page shipped.",
            "Customer Portal v1 launched (customers can see their own data).",
            "User Management admin page added.",
        ],
    },
    {
        "date": "Sun–Mon, Feb 8–9, 2026",
        "title": "Iteration",
        "items": [
            "Auth/portal polish, no new modules.",
        ],
    },
    {
        "date": "Tue, Feb 10, 2026",
        "title": "Pricing engine + full Customer Portal",
        "items": [
            "Pricing Calculator + Pricing Settings + Pricing landing page shipped.",
            "Company Settings page added (logo, branding, tax, payroll, etc.).",
            "Webstore Detail Dashboard added for admins to manage stores.",
            "Customer Portal expanded to a full suite: Portal Dashboard, Portal Login, Portal Messages, Portal Orders, Portal Pages, Portal Profile, Portal Proofs.",
        ],
    },
    {
        "date": "Wed, Feb 11, 2026",
        "title": "Iteration",
        "items": [
            "Stabilization + bug-fixing across the pricing + portal work; no new modules.",
        ],
    },
    {
        "date": "Thu, Feb 12, 2026",
        "title": "Major refactor + AI Assistant phases 2/3/4 + Webstore Owner Stripe Connect",
        "items": [
            "Backend modularized — server.py split into models/, routes/, services/ packages "
            "(auth, customers, jobs, invoices, quotes, employees, pricing, portal, webstores).",
            "Questionnaire 'Send via Email' endpoint + branded HTML email shipped. Fixed Public Questionnaire dark-bg contrast.",
            "New 'Events' webstore product category added (alongside business/fundraiser/creator).",
            "Platform fee schedule corrected: $5 invoice now charges the right 31¢ instead of undercharging 11¢. "
            "Webstore checkout includes the +2% webstore surcharge.",
            "Founders-only feature flag — all paid features unlocked for founder tenants while in launch phase.",
            "Webstore Owner Stripe Connect (Phase A/B/C): owner invite (quick + full portal), Stripe Express onboarding, "
            "activation gate (store can't go live until owner's Stripe is connected), auto-transfer of owner commission on order completion.",
            "Webstore Owner Portal launched: owners see their stores, sales, transfer history, and a Stripe Express dashboard link.",
            "AI Assistant Pass 2 — proactive Dashboard 'Nudges' widget (stale quotes, overdue invoices, upcoming appointments), "
            "inline Draft Email modal with GPT-4o-mini, SendGrid send, rolling long-term memory.",
            "AI Assistant Pass 3 — real tool calling: navigate(), create_task(), create_appointment(), query_shop_metric(). "
            "Asking 'how much did I make today' or 'open the schedule' now triggers a real action instead of a chat reply.",
            "AI Assistant Pass 4 — set_reminder + send_quote_followup_bulk tools. Tool-calling system extracted into its own module so new tools are 1-line adds.",
            "AI Assistant 'kill generic mode' + Personality picker (Ops Partner / Wise Mentor / Cheerful Helper / No-BS Direct) + quick-action intent pills.",
            "Pricing Foundation 'Show Math (Behind the Scenes)' debug panel — see exactly how each price was calculated, with a Raw JSON copy.",
        ],
    },
    {
        "date": "Fri, Feb 13, 2026",
        "title": "Billing + Tier system",
        "items": [
            "Multi-tier subscription system shipped: Starter / Pro / Business / Founders Edition.",
            "Pricing Page (public) launched.",
            "Billing Success / Billing Cancel return pages for Stripe Checkout.",
            "Trial Lockout + Upgrade Modal so over-quota features prompt an upgrade instead of failing silently.",
            "Backend tier_config + feature_gate services — single source of truth for what each plan can do.",
        ],
    },
    {
        "date": "Sat, Feb 14, 2026",
        "title": "Iteration",
        "items": [
            "Billing flow stabilization. No new modules.",
        ],
    },
    {
        "date": "Sun, Feb 15, 2026",
        "title": "Top-5 Pre-launch Platform Gaps — ALL CLOSED",
        "items": [
            "#1 Admin Audit Log — every privileged Platform Admin action (impersonation, suspend, etc.) is now captured with actor, target, IP, and metadata. New /platform-admin/audit-log page.",
            "#2 Suspend / Reactivate Tenant — instant kill switch with reason, self-lockout protection, structured 403 response on suspended logins, and an /account-suspended page. Optional 'Welcome back' email on reactivation.",
            "#3 Failed-Payment / Dunning Workflow — auto-suspend after 3 consecutive Stripe failures, auto-reactivate on success, Founder 24h grace period, per-tenant threshold override, manual 'Mark as Paid' for NET-60 customers. Every transition writes a billing audit row.",
            "#4 Email Deliverability Dashboard — SendGrid Event Webhook live; every email's delivery_status (delivered / deferred / bounce / dropped / spam) is now visible to Platform Admin with full event timeline per message.",
            "#5 System-wide Announcement Banner + Maintenance Mode — Platform Admin can broadcast a banner (info/warning/critical, optional auto-expire) and toggle maintenance mode, which blocks all non-admin writes with a structured 503 while keeping reads open.",
            "Result: pre-launch platform-readiness checklist is fully cleared.",
        ],
    },
]


def build():
    doc = SimpleDocTemplate(
        OUT_PATH,
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="SignGuy AI — Build Log: Jan 27 – Feb 15, 2026",
        author="SignGuy AI",
    )

    styles = getSampleStyleSheet()
    PRIMARY = HexColor("#6D28D9")  # violet-700
    INK = HexColor("#0F172A")
    SUB = HexColor("#475569")

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=INK,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=SUB,
        spaceAfter=18,
    )
    day_style = ParagraphStyle(
        "Day",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13.5,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=2,
    )
    day_title_style = ParagraphStyle(
        "DayTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        textColor=INK,
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=INK,
        spaceAfter=2,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        textColor=SUB,
        spaceBefore=22,
    )

    flow = []
    flow.append(Paragraph("SignGuy AI — Build Log", title_style))
    flow.append(Paragraph("January 27 → February 15, 2026 &nbsp; · &nbsp; high-level daily summary", subtitle_style))

    for d in DAYS:
        flow.append(Paragraph(d["date"], day_style))
        flow.append(Paragraph(d["title"], day_title_style))
        bullets = [
            ListItem(Paragraph(item, bullet_style), leftIndent=10)
            for item in d["items"]
        ]
        flow.append(
            ListFlowable(
                bullets,
                bulletType="bullet",
                start="•",
                bulletColor=PRIMARY,
                leftIndent=14,
                bulletFontSize=10,
                spaceAfter=2,
            )
        )

    flow.append(Spacer(1, 0.15 * inch))
    flow.append(
        Paragraph(
            "Notes: Jan 27 – Feb 11 entries are reconstructed from git file-add history "
            "(commit messages were auto-generated UUIDs). Feb 12 + Feb 15 entries are drawn directly "
            "from the dated CHANGELOG / PRD entries. Tiny per-file changes intentionally omitted — "
            "only material features, modules, and platform milestones are listed.",
            footer_style,
        )
    )

    doc.build(flow)
    print(f"OK: wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
