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
        tenant = await db.tenants.find_one({"tenant_id": tenant_id}, {"_id": 0})
        
        return {
            "company_name": tenant.get("company_name", "SignGuy AI") if tenant else "SignGuy AI",
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
            
            # Log the email send
            await self._log_email(
                tenant_id=tenant_id,
                to_email=to_email,
                subject=subject,
                status="sent",
                response_code=response.status_code
            )
            
            logger.info(f"Email sent to {to_email}, status: {response.status_code}")
            return {"success": True, "status_code": response.status_code}
            
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
        error: Optional[str] = None
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


# Global email service instance
email_service = EmailService()
