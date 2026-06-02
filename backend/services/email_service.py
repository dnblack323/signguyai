"""
Email Service

This module handles sending emails via SendGrid including:
- Document delivery to customers
- Portal notifications
- Welcome emails
- General transactional emails
"""

import os
import re
from typing import Optional, List, Dict
from datetime import datetime, timezone
import uuid

# SendGrid imports
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
    import base64
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

from server import db, logger


def render_template(template_content: str, data: dict) -> str:
    """Render a template by replacing variables with data"""
    result = template_content
    
    # Replace simple variables
    for key, value in data.items():
        result = result.replace("{{" + key + "}}", str(value) if value else "")
    
    # Handle {{#if variable}} blocks
    def replace_if_block(match):
        var_name = match.group(1)
        content = match.group(2)
        if data.get(var_name):
            return content
        return ""
    
    result = re.sub(r'\{\{#if (\w+)\}\}(.*?)\{\{/if\}\}', replace_if_block, result, flags=re.DOTALL)
    
    return result


class EmailService:
    """Email service using SendGrid"""
    
    def __init__(self):
        self.api_key = os.environ.get("SENDGRID_API_KEY")
        self.from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@signguy.ai")
        self.from_name = os.environ.get("SENDGRID_FROM_NAME", "SignGuy AI")
        
    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured"""
        return SENDGRID_AVAILABLE and bool(self.api_key)
    
    async def get_template(self, template_id: str, tenant_id: str) -> dict:
        """Get email template (custom or default)"""
        from routes.email_templates import DEFAULT_TEMPLATES
        
        if template_id not in DEFAULT_TEMPLATES:
            return None
        
        default = DEFAULT_TEMPLATES[template_id]
        
        # Check for custom version
        custom = await db.email_templates.find_one(
            {"tenant_id": tenant_id, "template_id": template_id},
            {"_id": 0}
        )
        
        return {
            "subject": custom.get("subject", default["subject"]) if custom else default["subject"],
            "html_content": custom.get("html_content", default["html_content"]) if custom else default["html_content"]
        }
    
    async def get_tenant_branding(self, tenant_id: str) -> dict:
        """Get tenant branding info for emails"""
        tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
        
        return {
            "company_name": (tenant.get("company_name") or tenant.get("name") or "SignGuy AI") if tenant else "SignGuy AI",
            "logo_url": tenant.get("logo_url", "") if tenant else "",
            "primary_color": tenant.get("primary_color", "#0D9488") if tenant else "#0D9488",
            "secondary_color": tenant.get("secondary_color", "#14B8A6") if tenant else "#14B8A6",
            "portal_url": tenant.get("portal_url", "") if tenant else "",
            "current_year": str(datetime.now().year)
        }
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None,
        attachments: Optional[List[dict]] = None,
        tenant_id: Optional[str] = None
    ) -> dict:
        """
        Send an email via SendGrid
        
        attachments format: [{"filename": "doc.pdf", "content": base64_string, "type": "application/pdf"}]
        """
        if not self.is_configured():
            logger.warning("SendGrid not configured, email not sent")
            return {"success": False, "error": "Email service not configured"}
        
        try:
            message = Mail(
                from_email=(self.from_email, self.from_name),
                to_emails=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_content
            )
            
            # Add attachments if provided
            if attachments:
                for att in attachments:
                    attachment = Attachment(
                        FileContent(att["content"]),
                        FileName(att["filename"]),
                        FileType(att.get("type", "application/octet-stream")),
                        Disposition("attachment")
                    )
                    message.add_attachment(attachment)
            
            sg = SendGridAPIClient(self.api_key)
            response = sg.send(message)

            # Capture SendGrid's message ID so we can correlate later events
            sg_message_id = None
            try:
                if hasattr(response, "headers") and response.headers:
                    # response.headers is a dict-like
                    sg_message_id = (
                        response.headers.get("X-Message-Id")
                        or response.headers.get("x-message-id")
                    )
            except Exception:
                pass

            # Log the email send
            await self._log_email(
                tenant_id=tenant_id,
                to_email=to_email,
                subject=subject,
                status="sent",
                response_code=response.status_code,
                sg_message_id=sg_message_id,
            )

            logger.info(f"Email sent to {to_email}, status: {response.status_code}")
            return {
                "success": True,
                "status_code": response.status_code,
                "sg_message_id": sg_message_id,
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            await self._log_email(
                tenant_id=tenant_id,
                to_email=to_email,
                subject=subject,
                status="failed",
                error=str(e)
            )
            return {"success": False, "error": str(e)}
    
    async def _log_email(
        self,
        tenant_id: Optional[str],
        to_email: str,
        subject: str,
        status: str,
        response_code: Optional[int] = None,
        error: Optional[str] = None,
        sg_message_id: Optional[str] = None,
    ):
        """Log email to database for tracking"""
        log_entry = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "to_email": to_email,
            "subject": subject,
            "status": status,
            "response_code": response_code,
            "error": error,
            "sg_message_id": sg_message_id,
            "delivery_status": status,  # mirrors `status` until events refine it
            "events": [],
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        await db.email_logs.insert_one(log_entry)
    
    async def send_document_to_customer(
        self,
        customer_email: str,
        customer_name: str,
        document_name: str,
        document_content: str,  # HTML or plain text content
        document_attachment: Optional[dict] = None,  # {"filename", "content" (base64), "type"}
        tenant_id: Optional[str] = None,
        company_name: str = "SignGuy AI"
    ) -> dict:
        """Send a document to a customer via email"""
        
        subject = f"Document from {company_name}: {document_name}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0D9488 0%, #14B8A6 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
                .document-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1px solid #e5e7eb; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
                .btn {{ display: inline-block; background: #0D9488; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{company_name}</h1>
                </div>
                <div class="content">
                    <p>Hi {customer_name},</p>
                    <p>Please find the following document for your review:</p>
                    
                    <div class="document-box">
                        <h3>{document_name}</h3>
                        <div style="white-space: pre-wrap;">{document_content}</div>
                    </div>
                    
                    {"<p><strong>Note:</strong> The document is also attached to this email.</p>" if document_attachment else ""}
                    
                    <p>If you have any questions, please don't hesitate to reach out.</p>
                    
                    <p>Best regards,<br>{company_name} Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent by {company_name}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        attachments = [document_attachment] if document_attachment else None
        
        return await self.send_email(
            to_email=customer_email,
            subject=subject,
            html_content=html_content,
            attachments=attachments,
            tenant_id=tenant_id
        )
    
    async def send_portal_notification(
        self,
        customer_email: str,
        customer_name: str,
        notification_type: str,
        notification_title: str,
        notification_message: str,
        portal_link: str,
        tenant_id: Optional[str] = None,
        company_name: str = "SignGuy AI"
    ) -> dict:
        """Send notification email about something in the portal using template"""
        
        # Get template
        template = await self.get_template("portal_notification", tenant_id) if tenant_id else None
        branding = await self.get_tenant_branding(tenant_id) if tenant_id else {}
        
        # Prepare template data
        data = {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "company_name": branding.get("company_name", company_name),
            "logo_url": branding.get("logo_url", ""),
            "primary_color": branding.get("primary_color", "#0D9488"),
            "secondary_color": branding.get("secondary_color", "#14B8A6"),
            "portal_link": portal_link or branding.get("portal_url", ""),
            "notification_title": notification_title,
            "notification_message": notification_message,
            "item_type": notification_type.replace("_", " ").title(),
            "current_year": str(datetime.now().year)
        }
        
        if template:
            subject = render_template(template["subject"], data)
            html_content = render_template(template["html_content"], data)
        else:
            # Fallback to simple email
            subject = f"{notification_title} - {data['company_name']}"
            html_content = f"""
            <h2>{notification_title}</h2>
            <p>Hi {customer_name},</p>
            <p>{notification_message}</p>
            <p><a href="{portal_link}">View in Portal</a></p>
            """
        
        return await self.send_email(
            to_email=customer_email,
            subject=subject,
            html_content=html_content,
            tenant_id=tenant_id
        )
    
    async def send_password_reset_email(
        self,
        to_email: str,
        reset_link: str,
        user_name: Optional[str] = None,
        expires_minutes: int = 60,
    ) -> dict:
        """Send a single-use password reset link to a user."""
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        subject = "Reset your SignGuy AI password"
        html_content = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;
                    padding:24px;color:#111827;">
          <h2 style="color:#0D9488;margin-top:0;">Reset your password</h2>
          <p>{greeting}</p>
          <p>We received a request to reset the password for your SignGuy AI account.
          Click the button below to choose a new password. This link is valid for
          {expires_minutes} minutes and can only be used once.</p>
          <p style="margin:28px 0;">
            <a href="{reset_link}"
               style="background:#0D9488;color:#fff;padding:12px 24px;
                      text-decoration:none;border-radius:6px;font-weight:600;">
              Reset Password
            </a>
          </p>
          <p style="color:#6b7280;font-size:13px;">If the button doesn't work, copy and
          paste this link into your browser:</p>
          <p style="word-break:break-all;font-size:13px;color:#0D9488;">{reset_link}</p>
          <p style="color:#6b7280;font-size:13px;margin-top:32px;">
            If you didn't request a password reset, you can safely ignore this email —
            your password will not be changed.
          </p>
        </div>
        """
        plain_content = (
            f"{greeting}\n\nReset your SignGuy AI password using this link "
            f"(valid {expires_minutes} minutes, single use):\n{reset_link}\n\n"
            "If you didn't request this, ignore this email."
        )
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            plain_content=plain_content,
        )

    async def send_welcome_email(
        self,
        customer_email: str,
        customer_name: str,
        tenant_id: str
    ) -> dict:
        """Send welcome/invitation email to new customer"""
        
        # Get template
        template = await self.get_template("portal_welcome", tenant_id)
        branding = await self.get_tenant_branding(tenant_id)
        
        # Prepare template data
        data = {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "company_name": branding.get("company_name", "SignGuy AI"),
            "logo_url": branding.get("logo_url", ""),
            "primary_color": branding.get("primary_color", "#0D9488"),
            "secondary_color": branding.get("secondary_color", "#14B8A6"),
            "portal_link": branding.get("portal_url", ""),
            "current_year": str(datetime.now().year)
        }
        
        if template:
            subject = render_template(template["subject"], data)
            html_content = render_template(template["html_content"], data)
        else:
            # Fallback
            subject = f"Welcome to {data['company_name']}!"
            html_content = f"""
            <h2>Welcome!</h2>
            <p>Hi {customer_name},</p>
            <p>Welcome to {data['company_name']}. Your customer portal is ready.</p>
            """
        
        return await self.send_email(
            to_email=customer_email,
            subject=subject,
            html_content=html_content,
            tenant_id=tenant_id
        )

    async def send_tenant_reactivated_email(
        self,
        owner_email: str,
        tenant_name: str,
        tenant_id: str,
        note: Optional[str] = None,
        login_url: Optional[str] = None,
    ) -> dict:
        """Send a 'You're back' email to the tenant owner after reactivation."""
        login_link = login_url or f"{os.environ.get('APP_URL', '').rstrip('/')}/login"
        login_link_html = (
            f'<p style="margin:24px 0;"><a href="{login_link}" '
            f'style="background:#10b981;color:#fff;padding:12px 24px;'
            f'text-decoration:none;border-radius:6px;font-weight:600;">'
            f'Sign back in</a></p>'
            if login_link else ""
        )
        note_html = (
            f'<p style="margin:16px 0;color:#374151;"><strong>Note from our team:</strong> '
            f'{note}</p>' if note else ""
        )

        subject = f"Your {tenant_name} account is active again"
        html_content = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;
                    padding:24px;color:#111827;">
          <h2 style="color:#059669;margin-top:0;">Welcome back!</h2>
          <p>Good news — your <strong>{tenant_name}</strong> account has been
          reactivated and full access is restored.</p>
          {note_html}
          <p>You and your team can sign in and pick up exactly where you left off.
          All of your data is intact.</p>
          {login_link_html}
          <p style="color:#6b7280;font-size:13px;margin-top:32px;">
            If you didn't expect this email or believe it was sent in error,
            please reply and let us know.
          </p>
        </div>
        """
        return await self.send_email(
            to_email=owner_email,
            subject=subject,
            html_content=html_content,
            tenant_id=tenant_id,
        )

    async def send_payment_failed_email(
        self,
        owner_email: str,
        tenant_name: str,
        tenant_id: str,
        attempt: int,
        attempts_remaining: int,
        amount: Optional[float] = None,
        currency: str = "USD",
        billing_url: Optional[str] = None,
    ) -> dict:
        """Send a payment-failed reminder email."""
        billing_link = billing_url or f"{os.environ.get('APP_URL', '').rstrip('/')}/billing"
        amount_str = f"{currency.upper()} ${amount:.2f}" if amount else "your invoice"
        urgency = (
            "Your account will be suspended on the next failed attempt."
            if attempts_remaining <= 1
            else f"You have {attempts_remaining} attempt(s) left before suspension."
        )
        subject = f"Action needed: payment failed for {tenant_name}"
        html_content = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;
                    padding:24px;color:#111827;">
          <h2 style="color:#dc2626;margin-top:0;">Payment failed</h2>
          <p>We weren't able to process {amount_str} for your
          <strong>{tenant_name}</strong> account on this attempt (#{attempt}).</p>
          <p style="color:#b91c1c;"><strong>{urgency}</strong></p>
          <p>Please update your payment method to avoid an interruption in service.</p>
          <p style="margin:24px 0;">
            <a href="{billing_link}"
               style="background:#dc2626;color:#fff;padding:12px 24px;
                      text-decoration:none;border-radius:6px;font-weight:600;">
              Update payment method
            </a>
          </p>
          <p style="color:#6b7280;font-size:13px;margin-top:32px;">
            If the payment has already gone through on your end, no action is needed —
            our system will catch up automatically.
          </p>
        </div>
        """
        return await self.send_email(
            to_email=owner_email,
            subject=subject,
            html_content=html_content,
            tenant_id=tenant_id,
        )

    async def send_dunning_suspended_email(
        self,
        owner_email: str,
        tenant_name: str,
        tenant_id: str,
        billing_url: Optional[str] = None,
    ) -> dict:
        """Send a 'Your account has been suspended for non-payment' email."""
        billing_link = billing_url or f"{os.environ.get('APP_URL', '').rstrip('/')}/billing"
        subject = f"Your {tenant_name} account has been suspended"
        html_content = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:0 auto;
                    padding:24px;color:#111827;">
          <h2 style="color:#dc2626;margin-top:0;">Account suspended for non-payment</h2>
          <p>After multiple failed payment attempts, your <strong>{tenant_name}</strong>
          account has been suspended. All of your data is preserved.</p>
          <p>To restore access, please update your payment method. The account will
          be reactivated automatically as soon as a payment succeeds.</p>
          <p style="margin:24px 0;">
            <a href="{billing_link}"
               style="background:#dc2626;color:#fff;padding:12px 24px;
                      text-decoration:none;border-radius:6px;font-weight:600;">
              Update payment method
            </a>
          </p>
          <p style="color:#6b7280;font-size:13px;margin-top:32px;">
            Need help? Reply to this email and our team will get back to you.
          </p>
        </div>
        """
        return await self.send_email(
            to_email=owner_email,
            subject=subject,
            html_content=html_content,
            tenant_id=tenant_id,
        )




# Global email service instance
email_service = EmailService()
