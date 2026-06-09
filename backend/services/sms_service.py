"""
SMS Service — Twilio-powered transactional SMS.

Usage:
    sms = SMSService()
    await sms.send(to="+15551234567", body="Your quote is ready!")
"""

import os
import logging
from typing import Optional

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")


def _format_phone(phone: str) -> Optional[str]:
    """Normalize to E.164. Returns None if unparseable."""
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if len(digits) > 7:
        return f"+{digits}"
    return None


class SMSService:
    def __init__(self):
        if not ACCOUNT_SID or not AUTH_TOKEN:
            logger.warning("Twilio credentials not configured — SMS disabled")
            self._client = None
        else:
            self._client = Client(ACCOUNT_SID, AUTH_TOKEN)

    async def send(self, to: str, body: str) -> dict:
        """Send an SMS. Returns {"success": bool, "sid": str, "error": str}."""
        if not self._client:
            return {"success": False, "error": "SMS not configured"}

        to_e164 = _format_phone(to)
        if not to_e164:
            return {"success": False, "error": f"Invalid phone number: {to}"}

        if not FROM_NUMBER:
            return {"success": False, "error": "TWILIO_FROM_NUMBER not set"}

        try:
            message = self._client.messages.create(
                to=to_e164,
                from_=FROM_NUMBER,
                body=body,
            )
            logger.info("SMS sent sid=%s to=%s", message.sid, to_e164)
            return {"success": True, "sid": message.sid}
        except TwilioRestException as e:
            logger.error("Twilio SMS error: %s", e)
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error("SMS unexpected error: %s", e)
            return {"success": False, "error": str(e)}

    # ── Convenience helpers ───────────────────────────────────────────────────

    async def send_quote_notification(self, to: str, customer_name: str,
                                       quote_number: str, total: float,
                                       share_url: Optional[str] = None) -> dict:
        name = customer_name.split()[0] if customer_name else "there"
        body = (
            f"Hi {name}, your quote #{quote_number} is ready — ${total:,.2f}. "
        )
        if share_url:
            body += f"View it here: {share_url}"
        else:
            body += "Reply to this number or contact us with any questions."
        return await self.send(to, body)

    async def send_invoice_notification(self, to: str, customer_name: str,
                                         invoice_number: str, total: float,
                                         due_date: Optional[str] = None) -> dict:
        name = customer_name.split()[0] if customer_name else "there"
        body = f"Hi {name}, invoice #{invoice_number} for ${total:,.2f} has been sent."
        if due_date:
            body += f" Due: {due_date}."
        body += " Contact us with any questions."
        return await self.send(to, body)

    async def send_appointment_reminder(self, to: str, customer_name: str,
                                         scheduled_time: str,
                                         business_name: str = "us") -> dict:
        name = customer_name.split()[0] if customer_name else "there"
        body = (
            f"Hi {name}, reminder: you have an appointment with {business_name} "
            f"on {scheduled_time}. Reply STOP to opt out."
        )
        return await self.send(to, body)
