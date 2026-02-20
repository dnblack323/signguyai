"""
Email Service

This module handles sending emails via SendGrid including:
- Document delivery to customers
- Portal notifications
- General transactional emails
"""

import os
from typing import Optional, List
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


class EmailService:
    """Email service using SendGrid"""
    
    def __init__(self):
        self.api_key = os.environ.get("SENDGRID_API_KEY")
        self.from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@signguy.ai")
        self.from_name = os.environ.get("SENDGRID_FROM_NAME", "SignGuy AI")
        
    def is_configured(self) -> bool:
        """Check if SendGrid is properly configured"""
        return SENDGRID_AVAILABLE and bool(self.api_key)
    
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
        """Send notification email about something in the portal"""
        
        subject_map = {
            "document_ready": f"New Document Available - {company_name}",
            "proof_ready": f"Artwork Proof Ready for Review - {company_name}",
            "invoice_ready": f"New Invoice Available - {company_name}",
            "quote_ready": f"New Quote Available - {company_name}",
            "message": f"New Message - {company_name}",
            "job_update": f"Job Update - {company_name}",
        }
        
        subject = subject_map.get(notification_type, f"Notification from {company_name}")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0D9488 0%, #14B8A6 100%); color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                .content {{ background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; }}
                .notification-box {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0D9488; }}
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
                    
                    <div class="notification-box">
                        <h3>{notification_title}</h3>
                        <p>{notification_message}</p>
                    </div>
                    
                    <p>Please log in to your customer portal to view and take action:</p>
                    
                    <p style="text-align: center;">
                        <a href="{portal_link}" class="btn">View in Portal</a>
                    </p>
                    
                    <p>If you have any questions, please don't hesitate to reach out.</p>
                    
                    <p>Best regards,<br>{company_name} Team</p>
                </div>
                <div class="footer">
                    <p>This email was sent by {company_name}</p>
                    <p>If you did not expect this email, please contact us.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return await self.send_email(
            to_email=customer_email,
            subject=subject,
            html_content=html_content,
            tenant_id=tenant_id
        )


# Global email service instance
email_service = EmailService()
