"""Public website contact/support submission routes."""

from datetime import datetime, timezone
from typing import Optional
import os
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from server import db, logger
from services.email_service import email_service


router = APIRouter(prefix="/public", tags=["Public Website"])


SMS_DISCLOSURE_VERSION = "signguy_ai_sms_v1"
SMS_DISCLOSURE_TEXT = (
    "By checking this box, you agree to receive SMS/MMS messages from SignGuy AI, "
    "operated by SignTists Lab, about your account, platform access, billing, support, "
    "and service notifications. Message frequency varies. Message and data rates may apply. "
    "Reply STOP to opt out and HELP for help. Consent is not a condition of purchase. "
    "View our Privacy Policy and Terms."
)


class PublicInquiryInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    subject: str = Field(min_length=2, max_length=180)
    message: str = Field(min_length=5, max_length=5000)
    company: Optional[str] = Field(default=None, max_length=160)
    phone: Optional[str] = Field(default=None, max_length=40)
    sms_opt_in: bool = False


async def _save_inquiry(form_type: str, payload: PublicInquiryInput, request: Request):
    now_iso = datetime.now(timezone.utc).isoformat()
    source = "public_contact_form" if form_type == "contact" else "public_support_form"

    if payload.sms_opt_in and not payload.phone:
        raise HTTPException(status_code=400, detail="Phone number is required when SMS consent is enabled")

    doc = {
        "id": str(uuid.uuid4()),
        "form_type": form_type,
        "name": payload.name.strip(),
        "email": payload.email,
        "company": (payload.company or "").strip() or None,
        "subject": payload.subject.strip(),
        "message": payload.message.strip(),
        "phone": (payload.phone or "").strip() or None,
        "sms_opt_in": bool(payload.sms_opt_in),
        "created_at": now_iso,
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", ""),
    }

    if payload.sms_opt_in and payload.phone:
        doc["sms_consent"] = {
            "phone_number": payload.phone.strip(),
            "consented_at": now_iso,
            "source": source,
            "disclosure_version": SMS_DISCLOSURE_VERSION,
            "disclosure_text": SMS_DISCLOSURE_TEXT,
        }

    await db.public_website_inquiries.insert_one(doc)
    logger.info("Public %s inquiry stored: %s", form_type, doc["id"])

    # Notify the platform admin via email (non-blocking — never fail the form submit)
    try:
        admin_email = os.environ.get("SENDGRID_FROM_EMAIL", "")
        if admin_email:
            label = "Contact" if form_type == "contact" else "Support"
            html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:30px 0;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08);">
    <div style="background:#0D9488;padding:24px 32px;">
      <h1 style="color:#fff;margin:0;font-size:20px;">New {label} Form Submission</h1>
    </div>
    <div style="padding:28px 32px;">
      <table style="width:100%;border-collapse:collapse;font-size:14px;color:#333;">
        <tr><td style="padding:6px 0;font-weight:bold;width:120px;">Name</td><td style="padding:6px 0;">{doc['name']}</td></tr>
        <tr><td style="padding:6px 0;font-weight:bold;">Email</td><td style="padding:6px 0;">{doc['email']}</td></tr>
        {'<tr><td style="padding:6px 0;font-weight:bold;">Phone</td><td style="padding:6px 0;">' + doc['phone'] + '</td></tr>' if doc.get('phone') else ''}
        {'<tr><td style="padding:6px 0;font-weight:bold;">Company</td><td style="padding:6px 0;">' + doc['company'] + '</td></tr>' if doc.get('company') else ''}
        <tr><td style="padding:6px 0;font-weight:bold;">Subject</td><td style="padding:6px 0;">{doc['subject']}</td></tr>
      </table>
      <div style="margin-top:16px;padding:16px;background:#f9fafb;border-radius:6px;font-size:14px;color:#333;white-space:pre-wrap;">{doc['message']}</div>
      <p style="margin-top:20px;font-size:12px;color:#888;">Submitted at {doc['created_at']} · IP: {doc.get('ip_address','unknown')}</p>
    </div>
  </div>
</body>
</html>"""
            await email_service.send_email(
                to_email=admin_email,
                subject=f"[SignGuy AI] New {label} Form: {doc['subject']}",
                html_content=html_body,
                plain_content=f"New {label} from {doc['name']} ({doc['email']})\n\nSubject: {doc['subject']}\n\n{doc['message']}",
            )
    except Exception as exc:
        logger.warning("Failed to send admin notification for public inquiry %s: %s", doc["id"], exc)

    return {"success": True, "message": "Thanks — your message has been received."}


@router.post("/contact")
async def submit_public_contact(payload: PublicInquiryInput, request: Request):
    return await _save_inquiry("contact", payload, request)


@router.post("/support")
async def submit_public_support(payload: PublicInquiryInput, request: Request):
    return await _save_inquiry("support", payload, request)
