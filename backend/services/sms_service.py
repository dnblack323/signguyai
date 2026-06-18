"""
SMS Service

Handles sending SMS messages via Twilio including:
- Appointment reminders
- Order notifications
- Portal access notifications
- General transactional SMS
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("twilio package not installed. SMS features disabled.")


class SMSService:
    """SMS service using Twilio"""

    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = os.environ.get("TWILIO_PHONE_NUMBER")

    def is_configured(self) -> bool:
        return TWILIO_AVAILABLE and bool(self.account_sid) and bool(self.auth_token) and bool(self.from_number)

    def _get_client(self) -> Optional["TwilioClient"]:
        if not self.is_configured():
            return None
        return TwilioClient(self.account_sid, self.auth_token)

    async def send_sms(self, to: str, body: str) -> dict:
        """
        Send an SMS message.

        Args:
            to: Recipient phone number in E.164 format (+1XXXXXXXXXX)
            body: SMS message body (max 160 chars recommended)

        Returns:
            dict with keys: success (bool), sid (str), error (str)
        """
        if not self.is_configured():
            logger.warning("SMS service not configured — skipping send to %s", to)
            return {"success": False, "error": "SMS service not configured"}

        # Normalize to E.164
        to_normalized = self._normalize_phone(to)
        if not to_normalized:
            return {"success": False, "error": f"Invalid phone number: {to}"}

        try:
            client = self._get_client()
            message = client.messages.create(
                body=body,
                from_=self.from_number,
                to=to_normalized,
            )
            logger.info("SMS sent to %s, SID: %s", to_normalized, message.sid)
            return {"success": True, "sid": message.sid}
        except Exception as e:
            logger.error("Twilio SMS error sending to %s: %s", to_normalized, str(e))
            return {"success": False, "error": str(e)}

    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Ensure phone is in E.164 format. Returns None if invalid."""
        if not phone:
            return None
        digits = "".join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
        elif phone.startswith("+") and len(digits) >= 10:
            return phone
        return None

    # --- Convenience methods ---

    async def send_appointment_reminder(self, to: str, customer_name: str, date: str, time: str, business_name: str) -> dict:
        body = (
            f"Hi {customer_name}! Reminder: You have an appointment at {business_name} "
            f"on {date} at {time}. Reply STOP to opt out."
        )
        return await self.send_sms(to, body)

    async def send_order_notification(self, to: str, customer_name: str, order_id: str, status: str, business_name: str) -> dict:
        body = (
            f"Hi {customer_name}! Your order #{order_id} from {business_name} "
            f"is now {status}. Reply STOP to opt out."
        )
        return await self.send_sms(to, body)

    async def send_portal_access(self, to: str, customer_name: str, portal_url: str, business_name: str) -> dict:
        body = (
            f"Hi {customer_name}! {business_name} has shared a portal link with you: "
            f"{portal_url}"
        )
        return await self.send_sms(to, body)

    async def send_webstore_order_confirmation(self, to: str, customer_name: str, order_id: str, store_name: str) -> dict:
        body = (
            f"Hi {customer_name}! Your order #{order_id} at {store_name} has been received. "
            f"We'll notify you when it's ready. Reply STOP to opt out."
        )
        return await self.send_sms(to, body)

    async def send_custom(self, to: str, body: str) -> dict:
        return await self.send_sms(to, body)
