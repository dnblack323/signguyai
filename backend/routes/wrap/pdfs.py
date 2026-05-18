"""
Wrap Command Center — Phase 2F: PDF generators.

Three PDF endpoints, each generates a PDF using reportlab, stores it in the
``wrap_files`` collection via ``files._record_generated_pdf``, and returns the
new file record. The frontend can then download/display the result from the
Photos & Files tab.

- POST /wrap/items/{ticket_id}/pdfs/customer-receipt
- POST /wrap/items/{ticket_id}/pdfs/aftercare
- POST /wrap/items/{ticket_id}/pdfs/final-packet
"""
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from models import UserInDB
from server import db, get_current_active_user

from .core import _load_ticket_or_404, _get_or_create_doc, _serialize, _now
from .files import _record_generated_pdf

pdfs_router = APIRouter(tags=["Wrap Command Center — PDFs"])


# ──────────────── PDF rendering helpers ────────────────
def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        "WrapTitle", parent=base["Title"], fontSize=20, leading=24,
        spaceAfter=12, textColor=colors.HexColor("#1f2937"),
    ))
    base.add(ParagraphStyle(
        "WrapH2", parent=base["Heading2"], fontSize=13, leading=16,
        spaceBefore=10, spaceAfter=6, textColor=colors.HexColor("#4338ca"),
    ))
    base.add(ParagraphStyle(
        "WrapBody", parent=base["BodyText"], fontSize=10, leading=13,
    ))
    base.add(ParagraphStyle(
        "WrapMuted", parent=base["BodyText"], fontSize=9, leading=12,
        textColor=colors.HexColor("#6b7280"),
    ))
    return base


def _kv_table(rows, col_widths=(1.6 * inch, 4.4 * inch)):
    tbl = Table([[k, v] for k, v in rows], colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
        ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#111827")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    return tbl


def _money(n) -> str:
    try:
        return f"${float(n or 0):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


async def _gather_context(tenant_id: str, ticket_id: str) -> dict:
    """Fetches all docs the PDF generators need."""
    ticket = await db.job_tickets.find_one(
        {"id": ticket_id, "tenant_id": tenant_id}, {"_id": 0}
    ) or {}
    wrap_raw = await db.wrap_data.find_one(
        {"tenant_id": tenant_id, "ticket_id": ticket_id}, {"_id": 0}
    ) or {}
    wrap = _serialize(wrap_raw) if wrap_raw else {}
    order = {}
    if ticket.get("order_id"):
        order = await db.orders.find_one(
            {"id": ticket["order_id"], "tenant_id": tenant_id}, {"_id": 0}
        ) or {}
    customer = {}
    if order.get("customer_id"):
        customer = await db.customers.find_one(
            {"id": order["customer_id"], "tenant_id": tenant_id}, {"_id": 0}
        ) or {}
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0}) or {}
    return {
        "ticket": ticket,
        "wrap": wrap,
        "order": order,
        "customer": customer,
        "tenant": tenant,
    }


def _customer_name(customer: dict) -> str:
    if not customer:
        return "Valued Customer"
    return (
        f"{customer.get('first_name') or ''} {customer.get('last_name') or ''}".strip()
        or customer.get("company")
        or "Valued Customer"
    )


def _vehicle_summary(wrap: dict) -> str:
    v = wrap.get("vehicle_info") or {}
    bits = [v.get("year"), v.get("make"), v.get("model"), v.get("color")]
    return " ".join(b for b in bits if b).strip() or "Vehicle"


def _shop_header(story, styles, tenant: dict, title: str):
    business = tenant.get("business_name") or tenant.get("name") or "Sign Shop"
    story.append(Paragraph(business, styles["WrapH2"]))
    story.append(Paragraph(title, styles["WrapTitle"]))
    contact_bits = [
        tenant.get("phone"),
        tenant.get("email"),
        tenant.get("website"),
        tenant.get("address"),
    ]
    contact = " &nbsp;•&nbsp; ".join(b for b in contact_bits if b)
    if contact:
        story.append(Paragraph(contact, styles["WrapMuted"]))
    story.append(Spacer(1, 0.18 * inch))


# ──────────────── Customer Receipt PDF ────────────────
def _render_customer_receipt(ctx: dict) -> bytes:
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.55 * inch, bottomMargin=0.55 * inch,
    )
    story = []
    tenant = ctx["tenant"]
    customer = ctx["customer"]
    order = ctx["order"]
    wrap = ctx["wrap"]
    snap = wrap.get("pricing_snapshot") or {}
    contract = wrap.get("contract") or {}
    design = wrap.get("design") or {}
    install = wrap.get("install") or {}
    aftercare = wrap.get("aftercare") or {}

    _shop_header(story, styles, tenant, "Customer Wrap Receipt")

    story.append(_kv_table([
        ("Customer", _customer_name(customer)),
        ("Order #", order.get("order_number") or "—"),
        ("Vehicle", _vehicle_summary(wrap)),
        ("Wrap Type", wrap.get("wrap_type") or "Vehicle Wrap"),
        ("Issued", _now()),
    ]))
    story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph("Pricing", styles["WrapH2"]))
    quoted = float(snap.get("quoted_price") or 0)
    deposit = float((order.get("amount_paid") or order.get("deposit_paid") or 0))
    balance = max(quoted - deposit, 0.0)
    story.append(_kv_table([
        ("Quoted Price", _money(quoted)),
        ("Deposit / Paid", _money(deposit)),
        ("Balance Due", _money(balance)),
    ]))
    story.append(Spacer(1, 0.18 * inch))

    story.append(Paragraph("Contract & Approvals", styles["WrapH2"]))
    story.append(_kv_table([
        ("Contract Status", (contract.get("contract_status") or "—").replace("_", " ").title()),
        ("Signed", "Yes" if contract.get("signed_at") else "No"),
        ("Proof Status", (design.get("proof_status") or "—").replace("_", " ").title()),
        ("Terms Summary",
         Paragraph(contract.get("terms_summary") or "Standard terms apply.", styles["WrapMuted"])),
    ]))
    story.append(Spacer(1, 0.14 * inch))

    story.append(Paragraph("Install & Aftercare", styles["WrapH2"]))
    story.append(_kv_table([
        ("Install Status", (install.get("install_status") or "—").replace("_", " ").title()),
        ("Install Date", install.get("install_date") or "—"),
        ("Aftercare Status", (aftercare.get("aftercare_status") or "—").replace("_", " ").title()),
    ]))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        "Thank you for trusting us with your wrap. Please keep this receipt for your records — "
        "your signed contract is on file at our shop.",
        styles["WrapMuted"],
    ))

    doc.build(story)
    return buf.getvalue()


# ──────────────── Aftercare PDF ────────────────
DEFAULT_CARE_BULLETS = [
    "Wait at least 48 hours before washing your wrap for the first time.",
    "Hand-wash with a soft microfiber cloth and a mild automotive soap.",
    "Avoid automatic car washes with stiff brushes — they can lift edges.",
    "Keep pressure washers below 1,800 PSI and hold the nozzle at least 12 inches away.",
    "Do not use wax, polish, or abrasive cleaners on the wrap surface.",
    "Park in shade or under cover when possible — UV exposure shortens wrap life.",
    "If you notice an edge lifting, contact us right away — small fixes are easy.",
]


def _render_aftercare(ctx: dict) -> bytes:
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.55 * inch, bottomMargin=0.55 * inch,
    )
    story = []
    tenant = ctx["tenant"]
    customer = ctx["customer"]
    wrap = ctx["wrap"]
    install = wrap.get("install") or {}
    aftercare = wrap.get("aftercare") or {}
    materials = wrap.get("materials") or []
    material_summary = ", ".join(m.get("name") or m.get("material_type") or "" for m in materials if m).strip(", ") or "Premium wrap vinyl"

    _shop_header(story, styles, tenant, "Wrap Aftercare Guide")

    story.append(_kv_table([
        ("Customer", _customer_name(customer)),
        ("Vehicle", _vehicle_summary(wrap)),
        ("Wrap Type", wrap.get("wrap_type") or "Vehicle Wrap"),
        ("Install Date", install.get("install_date") or "—"),
        ("Material", material_summary),
    ]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Caring For Your Wrap", styles["WrapH2"]))
    for line in DEFAULT_CARE_BULLETS:
        story.append(Paragraph("• " + line, styles["WrapBody"]))

    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("Warranty & Maintenance", styles["WrapH2"]))
    story.append(Paragraph(
        "Your wrap is backed by our shop's standard workmanship guarantee. "
        "Cosmetic defects discovered within 30 days are repaired at no charge. "
        "Material failures are covered per the manufacturer's stated warranty.",
        styles["WrapBody"],
    ))
    if aftercare.get("aftercare_notes"):
        story.append(Spacer(1, 0.08 * inch))
        story.append(Paragraph("Shop Notes For You", styles["WrapH2"]))
        story.append(Paragraph(aftercare["aftercare_notes"], styles["WrapBody"]))

    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph(
        f"Questions? Call {tenant.get('phone') or 'your shop'} or email {tenant.get('email') or 'us'}.",
        styles["WrapMuted"],
    ))

    doc.build(story)
    return buf.getvalue()


# ──────────────── Endpoints ────────────────
@pdfs_router.post("/items/{ticket_id}/pdfs/customer-receipt")
async def generate_customer_receipt(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    ctx = await _gather_context(current_user.tenant_id, ticket_id)
    pdf_bytes = _render_customer_receipt(ctx)
    filename = f"Wrap_Receipt_{ctx['order'].get('order_number') or ticket_id[:6]}.pdf"
    record = await _record_generated_pdf(
        tenant_id=current_user.tenant_id,
        ticket_id=ticket_id,
        order_id=ticket.get("order_id", ""),
        pdf_bytes=pdf_bytes,
        filename=filename,
        category="Signed Documents",
        uploaded_by=getattr(current_user, "email", "") or current_user.id,
        notes="Customer wrap receipt — auto-generated",
        customer_visible=True,
    )
    return record


@pdfs_router.post("/items/{ticket_id}/pdfs/aftercare")
async def generate_aftercare_pdf(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    ctx = await _gather_context(current_user.tenant_id, ticket_id)
    pdf_bytes = _render_aftercare(ctx)
    filename = f"Wrap_Aftercare_{ctx['order'].get('order_number') or ticket_id[:6]}.pdf"
    record = await _record_generated_pdf(
        tenant_id=current_user.tenant_id,
        ticket_id=ticket_id,
        order_id=ticket.get("order_id", ""),
        pdf_bytes=pdf_bytes,
        filename=filename,
        category="Aftercare Documents",
        uploaded_by=getattr(current_user, "email", "") or current_user.id,
        notes="Aftercare guide — auto-generated",
        customer_visible=True,
    )
    return record


@pdfs_router.post("/items/{ticket_id}/pdfs/final-packet")
async def generate_final_packet_pdf(
    ticket_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    ticket = await _load_ticket_or_404(ticket_id, current_user.tenant_id)
    await _get_or_create_doc(current_user.tenant_id, ticket)
    ctx = await _gather_context(current_user.tenant_id, ticket_id)
    # _render_final_packet is async due to db.count_documents await — handle inline:
    pdf_bytes = await _render_final_packet_async(ctx)
    filename = f"Wrap_Final_Packet_{ctx['order'].get('order_number') or ticket_id[:6]}.pdf"
    record = await _record_generated_pdf(
        tenant_id=current_user.tenant_id,
        ticket_id=ticket_id,
        order_id=ticket.get("order_id", ""),
        pdf_bytes=pdf_bytes,
        filename=filename,
        category="Final Packets",
        uploaded_by=getattr(current_user, "email", "") or current_user.id,
        notes="Final wrap packet — internal",
        customer_visible=False,
    )
    return record


async def _render_final_packet_async(ctx: dict) -> bytes:
    """Async wrapper that performs the one Mongo count before delegating to the sync builder."""
    tenant_id = ctx["tenant"].get("id")
    ticket_id = ctx["ticket"].get("id")
    file_count = 0
    if tenant_id and ticket_id:
        file_count = await db.wrap_files.count_documents(
            {"tenant_id": tenant_id, "ticket_id": ticket_id}
        )
    return _render_final_packet_sync(ctx, file_count)


def _render_final_packet_sync(ctx: dict, file_count: int) -> bytes:
    """Sync render — same content as _render_final_packet but with pre-fetched file_count."""
    styles = _styles()
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )
    story = []
    tenant = ctx["tenant"]
    customer = ctx["customer"]
    order = ctx["order"]
    wrap = ctx["wrap"]

    _shop_header(story, styles, tenant, "Final Wrap Packet (Internal)")

    story.append(_kv_table([
        ("Customer", _customer_name(customer)),
        ("Order #", order.get("order_number") or "—"),
        ("Vehicle", _vehicle_summary(wrap)),
        ("Wrap Type", wrap.get("wrap_type") or "Vehicle Wrap"),
        ("Packet Created", _now()),
    ]))
    story.append(Spacer(1, 0.15 * inch))

    cov = wrap.get("coverage_summary") or {}
    areas = wrap.get("wrapped_areas") or []
    story.append(Paragraph("Measurements", styles["WrapH2"]))
    story.append(_kv_table([
        ("Total Raw Sq Ft", f"{cov.get('total_raw_sqft', 0):.2f}"),
        ("Total Billable Sq Ft", f"{cov.get('total_billable_sqft', 0):.2f}"),
        ("Included Areas", str(cov.get("included_count", 0))),
        ("Total Areas", str(len(areas))),
    ]))

    snap = wrap.get("pricing_snapshot") or {}
    story.append(Paragraph("Pricing", styles["WrapH2"]))
    story.append(_kv_table([
        ("Method", (snap.get("pricing_method") or "—").replace("_", " ").title()),
        ("Quoted Price", _money(snap.get("quoted_price"))),
        ("Estimated Profit", _money(snap.get("estimated_profit"))),
        ("Margin %", f"{snap.get('estimated_margin_percent', 0):.1f}%"),
    ]))

    design = wrap.get("design") or {}
    contract = wrap.get("contract") or {}
    approvals = wrap.get("approvals") or {}
    story.append(Paragraph("Design, Contract & Approvals", styles["WrapH2"]))
    story.append(_kv_table([
        ("Questionnaire", (design.get("questionnaire_status") or "—").title()),
        ("Proof Status", (design.get("proof_status") or "—").title()),
        ("Contract Status", (contract.get("contract_status") or "—").title()),
        ("Contract Signed", "Yes" if approvals.get("contract_signed") else "No"),
        ("Deposit Paid", "Yes" if approvals.get("deposit_paid") else "No"),
        ("Proof Approved", "Yes" if approvals.get("proof_approved") else "No"),
        ("Final Signoff", "Yes" if approvals.get("final_signoff_completed") else "No"),
    ]))

    story.append(PageBreak())

    insp = wrap.get("inspection") or {}
    story.append(Paragraph("Pre-Install Inspection", styles["WrapH2"]))
    story.append(_kv_table([
        ("Status", (insp.get("inspection_status") or "—").replace("_", " ").title()),
        ("Inspected By", insp.get("inspected_by") or "—"),
        ("Inspection Date", insp.get("inspection_date") or "—"),
        ("Customer Acknowledged", "Yes" if insp.get("customer_acknowledged") else "No"),
    ]))
    markers = insp.get("damage_markers") or []
    if markers:
        story.append(Paragraph(f"Damage Markers ({len(markers)})", styles["WrapH2"]))
        marker_rows = [["#", "Area", "Type", "Severity", "Notes"]]
        for i, m in enumerate(markers, 1):
            marker_rows.append([
                str(i),
                (m.get("area") or "—")[:40],
                m.get("damage_type") or "—",
                m.get("severity") or "—",
                (m.get("notes") or "")[:60],
            ])
        mt = Table(marker_rows, colWidths=(0.3 * inch, 1.7 * inch, 1.5 * inch, 0.9 * inch, 2.6 * inch))
        mt.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "Helvetica", 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#3730a3")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(mt)

    prod = wrap.get("production") or {}
    story.append(Paragraph("Production", styles["WrapH2"]))
    story.append(_kv_table([
        ("Status", (prod.get("production_status") or "—").replace("_", " ").title()),
        ("Tasks", str(len(prod.get("tasks") or []))),
    ]))

    install = wrap.get("install") or {}
    story.append(Paragraph("Install", styles["WrapH2"]))
    story.append(_kv_table([
        ("Status", (install.get("install_status") or "—").replace("_", " ").title()),
        ("Install Date", install.get("install_date") or "—"),
        ("Customer Signoff", "Yes" if install.get("customer_signoff") else "No"),
    ]))
    issues = install.get("issues") or []
    if issues:
        story.append(Paragraph(f"Install Issues ({len(issues)})", styles["WrapH2"]))
        issue_rows = [["#", "Type", "Severity", "Resolved", "Notes"]]
        for i, iss in enumerate(issues, 1):
            issue_rows.append([
                str(i),
                iss.get("issue_type") or "—",
                iss.get("severity") or "—",
                "Yes" if iss.get("resolved") else "No",
                (iss.get("notes") or "")[:60],
            ])
        it = Table(issue_rows, colWidths=(0.3 * inch, 1.8 * inch, 0.9 * inch, 0.8 * inch, 3.2 * inch))
        it.setStyle(TableStyle([
            ("FONT", (0, 0), (-1, -1), "Helvetica", 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#92400e")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(it)

    aftercare = wrap.get("aftercare") or {}
    story.append(Paragraph("Aftercare", styles["WrapH2"]))
    story.append(_kv_table([
        ("Status", (aftercare.get("aftercare_status") or "—").replace("_", " ").title()),
        ("Sent", "Yes" if aftercare.get("aftercare_sent") else "No"),
        ("Customer Viewed", "Yes" if aftercare.get("customer_viewed") else "No"),
        ("Followup 24h", "Yes" if aftercare.get("followup_24h") else "No"),
        ("Followup 7d", "Yes" if aftercare.get("followup_7d") else "No"),
        ("Followup 30d", "Yes" if aftercare.get("followup_30d") else "No"),
    ]))

    story.append(Paragraph("Files Summary", styles["WrapH2"]))
    story.append(Paragraph(f"Total wrap files attached: {file_count}", styles["WrapBody"]))

    doc.build(story)
    return buf.getvalue()
