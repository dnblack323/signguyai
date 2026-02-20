"""
Email Templates Routes

This module handles email template management including:
- Default templates for portal notifications and welcome emails
- Admin editing of templates
- Template variables and placeholders
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

from server import db, logger, get_current_active_user
from models import UserInDB


# Default email templates
DEFAULT_TEMPLATES = {
    "portal_notification": {
        "id": "portal_notification",
        "name": "Portal Notification",
        "description": "Sent when a document or item needs customer attention in the portal",
        "subject": "Action Required: {{item_type}} Ready for Review - {{company_name}}",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .logo { max-height: 60px; margin-bottom: 15px; }
        .content { background: white; padding: 40px; border: 1px solid #e5e7eb; }
        .greeting { font-size: 18px; margin-bottom: 20px; }
        .message-box { background: #f9fafb; padding: 25px; border-radius: 8px; margin: 25px 0; border-left: 4px solid {{primary_color}}; }
        .btn { display: inline-block; background: {{primary_color}}; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin-top: 20px; font-weight: bold; }
        .btn:hover { opacity: 0.9; }
        .footer { text-align: center; padding: 25px; color: #6b7280; font-size: 12px; background: #f9fafb; border-radius: 0 0 8px 8px; }
        .divider { height: 1px; background: #e5e7eb; margin: 25px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {{#if logo_url}}
            <img src="{{logo_url}}" alt="{{company_name}}" class="logo" />
            {{/if}}
            <h1 style="margin: 0; font-size: 24px;">{{company_name}}</h1>
        </div>
        <div class="content">
            <p class="greeting">Hi {{customer_name}},</p>
            
            <p>We wanted to let you know that there's something that needs your attention in your customer portal.</p>
            
            <div class="message-box">
                <h3 style="margin-top: 0; color: {{primary_color}};">{{notification_title}}</h3>
                <p style="margin-bottom: 0;">{{notification_message}}</p>
            </div>
            
            <p>Please log in to your customer portal to view and take action:</p>
            
            <p style="text-align: center;">
                <a href="{{portal_link}}" class="btn">View in Portal</a>
            </p>
            
            <div class="divider"></div>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
            
            <p>Best regards,<br><strong>{{company_name}} Team</strong></p>
        </div>
        <div class="footer">
            <p>&copy; {{current_year}} {{company_name}}. All rights reserved.</p>
            <p>This email was sent to {{customer_email}}</p>
        </div>
    </div>
</body>
</html>
""",
        "variables": [
            {"name": "customer_name", "description": "Customer's name"},
            {"name": "customer_email", "description": "Customer's email"},
            {"name": "company_name", "description": "Your company name"},
            {"name": "logo_url", "description": "Your company logo URL"},
            {"name": "primary_color", "description": "Primary brand color"},
            {"name": "secondary_color", "description": "Secondary brand color"},
            {"name": "notification_title", "description": "Title of the notification"},
            {"name": "notification_message", "description": "Notification message"},
            {"name": "portal_link", "description": "Link to the customer portal"},
            {"name": "current_year", "description": "Current year"}
        ]
    },
    "portal_welcome": {
        "id": "portal_welcome",
        "name": "Portal Welcome/Invitation",
        "description": "Sent when a new customer is created to invite them to the portal",
        "subject": "Welcome to {{company_name}} - Your Customer Portal Access",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .logo { max-height: 60px; margin-bottom: 15px; }
        .content { background: white; padding: 40px; border: 1px solid #e5e7eb; }
        .welcome-banner { background: linear-gradient(135deg, {{primary_color}}15 0%, {{secondary_color}}15 100%); padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 25px; }
        .welcome-banner h2 { color: {{primary_color}}; margin: 0; }
        .feature-list { background: #f9fafb; padding: 25px; border-radius: 8px; margin: 25px 0; }
        .feature-item { display: flex; align-items: flex-start; margin-bottom: 15px; }
        .feature-icon { width: 24px; height: 24px; background: {{primary_color}}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 14px; flex-shrink: 0; }
        .credentials-box { background: #fef3c7; border: 1px solid #f59e0b; padding: 20px; border-radius: 8px; margin: 25px 0; }
        .btn { display: inline-block; background: {{primary_color}}; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin-top: 20px; font-weight: bold; }
        .btn:hover { opacity: 0.9; }
        .steps { counter-reset: step; margin: 25px 0; }
        .step { display: flex; align-items: flex-start; margin-bottom: 20px; }
        .step-number { width: 30px; height: 30px; background: {{primary_color}}; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 15px; font-weight: bold; flex-shrink: 0; }
        .footer { text-align: center; padding: 25px; color: #6b7280; font-size: 12px; background: #f9fafb; border-radius: 0 0 8px 8px; }
        .divider { height: 1px; background: #e5e7eb; margin: 25px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {{#if logo_url}}
            <img src="{{logo_url}}" alt="{{company_name}}" class="logo" />
            {{/if}}
            <h1 style="margin: 0; font-size: 24px;">{{company_name}}</h1>
        </div>
        <div class="content">
            <div class="welcome-banner">
                <h2>Welcome to Your Customer Portal!</h2>
            </div>
            
            <p>Hi {{customer_name}},</p>
            
            <p>Thank you for choosing <strong>{{company_name}}</strong>! We're excited to have you as a customer. We've created a secure customer portal just for you where you can manage your account and stay connected with us.</p>
            
            <div class="feature-list">
                <h3 style="margin-top: 0; color: {{primary_color}};">What You Can Do in Your Portal:</h3>
                <div class="feature-item">
                    <div class="feature-icon">✓</div>
                    <div><strong>View Quotes & Invoices</strong> - Access all your quotes and invoices in one place</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">✓</div>
                    <div><strong>Track Job Progress</strong> - See real-time updates on your projects</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">✓</div>
                    <div><strong>Review & Approve Artwork</strong> - Review proofs and approve designs</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">✓</div>
                    <div><strong>Access Documents</strong> - Download contracts, warranties, and more</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">✓</div>
                    <div><strong>Communicate with Us</strong> - Send messages directly to our team</div>
                </div>
            </div>
            
            <h3 style="color: {{primary_color}};">How to Get Started:</h3>
            
            <div class="steps">
                <div class="step">
                    <div class="step-number">1</div>
                    <div>
                        <strong>Click the button below</strong> to access your customer portal
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">2</div>
                    <div>
                        <strong>Log in</strong> using your email address: <strong>{{customer_email}}</strong>
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">3</div>
                    <div>
                        <strong>Set your password</strong> on first login (check for a separate password setup email)
                    </div>
                </div>
                <div class="step">
                    <div class="step-number">4</div>
                    <div>
                        <strong>Explore your dashboard</strong> to see your quotes, jobs, and documents
                    </div>
                </div>
            </div>
            
            <p style="text-align: center;">
                <a href="{{portal_link}}" class="btn">Access Your Portal</a>
            </p>
            
            <div class="divider"></div>
            
            <p><strong>Need help?</strong> If you have any questions about using the portal or your account, please don't hesitate to reach out to us. We're here to help!</p>
            
            <p>Welcome aboard!</p>
            
            <p>Best regards,<br><strong>{{company_name}} Team</strong></p>
        </div>
        <div class="footer">
            <p>&copy; {{current_year}} {{company_name}}. All rights reserved.</p>
            <p>This email was sent to {{customer_email}}</p>
            <p style="margin-top: 10px;">
                <a href="{{portal_link}}" style="color: {{primary_color}};">Customer Portal</a>
            </p>
        </div>
    </div>
</body>
</html>
""",
        "variables": [
            {"name": "customer_name", "description": "Customer's name"},
            {"name": "customer_email", "description": "Customer's email"},
            {"name": "company_name", "description": "Your company name"},
            {"name": "logo_url", "description": "Your company logo URL"},
            {"name": "primary_color", "description": "Primary brand color"},
            {"name": "secondary_color", "description": "Secondary brand color"},
            {"name": "portal_link", "description": "Link to the customer portal"},
            {"name": "current_year", "description": "Current year"}
        ]
    },
    "document_delivery": {
        "id": "document_delivery",
        "name": "Document Delivery",
        "description": "Sent when delivering a document directly via email",
        "subject": "Document from {{company_name}}: {{document_name}}",
        "html_content": """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, {{primary_color}} 0%, {{secondary_color}} 100%); color: white; padding: 30px; text-align: center; border-radius: 8px 8px 0 0; }
        .logo { max-height: 60px; margin-bottom: 15px; }
        .content { background: white; padding: 40px; border: 1px solid #e5e7eb; }
        .document-box { background: #f9fafb; padding: 25px; border-radius: 8px; margin: 25px 0; border: 1px solid #e5e7eb; }
        .document-icon { font-size: 48px; text-align: center; margin-bottom: 15px; }
        .btn { display: inline-block; background: {{primary_color}}; color: white; padding: 14px 28px; text-decoration: none; border-radius: 6px; margin-top: 20px; font-weight: bold; }
        .footer { text-align: center; padding: 25px; color: #6b7280; font-size: 12px; background: #f9fafb; border-radius: 0 0 8px 8px; }
        .divider { height: 1px; background: #e5e7eb; margin: 25px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            {{#if logo_url}}
            <img src="{{logo_url}}" alt="{{company_name}}" class="logo" />
            {{/if}}
            <h1 style="margin: 0; font-size: 24px;">{{company_name}}</h1>
        </div>
        <div class="content">
            <p>Hi {{customer_name}},</p>
            
            <p>Please find the following document for your review:</p>
            
            <div class="document-box">
                <div class="document-icon">📄</div>
                <h3 style="margin: 0 0 10px 0; text-align: center; color: {{primary_color}};">{{document_name}}</h3>
                {{#if custom_message}}
                <p style="text-align: center; color: #666;">{{custom_message}}</p>
                {{/if}}
            </div>
            
            {{#if has_attachment}}
            <p style="text-align: center; background: #ecfdf5; padding: 15px; border-radius: 8px; color: #059669;">
                <strong>📎 The document is attached to this email.</strong>
            </p>
            {{/if}}
            
            <div class="divider"></div>
            
            <p>If you have any questions about this document, please don't hesitate to reach out.</p>
            
            <p>Best regards,<br><strong>{{company_name}} Team</strong></p>
        </div>
        <div class="footer">
            <p>&copy; {{current_year}} {{company_name}}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
""",
        "variables": [
            {"name": "customer_name", "description": "Customer's name"},
            {"name": "company_name", "description": "Your company name"},
            {"name": "logo_url", "description": "Your company logo URL"},
            {"name": "primary_color", "description": "Primary brand color"},
            {"name": "secondary_color", "description": "Secondary brand color"},
            {"name": "document_name", "description": "Name of the document"},
            {"name": "custom_message", "description": "Custom message from sender"},
            {"name": "has_attachment", "description": "Whether document is attached"},
            {"name": "current_year", "description": "Current year"}
        ]
    }
}


class EmailTemplateUpdate(BaseModel):
    subject: Optional[str] = None
    html_content: Optional[str] = None


router = APIRouter(prefix="/email-templates", tags=["Email Templates"])


@router.get("")
async def list_email_templates(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all email templates for the tenant"""
    # Get custom templates from database
    custom_templates = await db.email_templates.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).to_list(20)
    
    custom_dict = {t["template_id"]: t for t in custom_templates}
    
    # Merge with defaults
    result = []
    for template_id, default in DEFAULT_TEMPLATES.items():
        template = {
            "id": template_id,
            "name": default["name"],
            "description": default["description"],
            "subject": custom_dict.get(template_id, {}).get("subject", default["subject"]),
            "html_content": custom_dict.get(template_id, {}).get("html_content", default["html_content"]),
            "variables": default["variables"],
            "is_customized": template_id in custom_dict
        }
        result.append(template)
    
    return result


@router.get("/{template_id}")
async def get_email_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific email template"""
    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    default = DEFAULT_TEMPLATES[template_id]
    
    # Check for custom version
    custom = await db.email_templates.find_one(
        {"tenant_id": current_user.tenant_id, "template_id": template_id},
        {"_id": 0}
    )
    
    return {
        "id": template_id,
        "name": default["name"],
        "description": default["description"],
        "subject": custom.get("subject", default["subject"]) if custom else default["subject"],
        "html_content": custom.get("html_content", default["html_content"]) if custom else default["html_content"],
        "variables": default["variables"],
        "is_customized": custom is not None
    }


@router.put("/{template_id}")
async def update_email_template(
    template_id: str,
    update: EmailTemplateUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update an email template"""
    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["tenant_id"] = current_user.tenant_id
    update_data["template_id"] = template_id
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.id
    
    await db.email_templates.update_one(
        {"tenant_id": current_user.tenant_id, "template_id": template_id},
        {"$set": update_data},
        upsert=True
    )
    
    logger.info(f"Email template {template_id} updated by {current_user.id}")
    
    return await get_email_template(template_id, current_user)


@router.post("/{template_id}/reset")
async def reset_email_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Reset an email template to default"""
    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.email_templates.delete_one(
        {"tenant_id": current_user.tenant_id, "template_id": template_id}
    )
    
    logger.info(f"Email template {template_id} reset to default by {current_user.id}")
    
    return {"message": "Template reset to default"}


@router.post("/{template_id}/preview")
async def preview_email_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a preview of an email template with sample data"""
    template = await get_email_template(template_id, current_user)
    
    # Get tenant info for preview
    tenant = await db.tenants.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    # Sample data for preview
    sample_data = {
        "customer_name": "John Smith",
        "customer_email": "john@example.com",
        "company_name": tenant.get("company_name", "Your Company") if tenant else "Your Company",
        "logo_url": tenant.get("logo_url", "") if tenant else "",
        "primary_color": tenant.get("primary_color", "#0D9488") if tenant else "#0D9488",
        "secondary_color": tenant.get("secondary_color", "#14B8A6") if tenant else "#14B8A6",
        "portal_link": tenant.get("portal_url", "https://portal.example.com") if tenant else "https://portal.example.com",
        "notification_title": "New Document Available",
        "notification_message": "A new proposal has been uploaded for your review.",
        "item_type": "Document",
        "document_name": "Sample Proposal",
        "custom_message": "Please review this proposal at your earliest convenience.",
        "has_attachment": True,
        "current_year": str(datetime.now().year)
    }
    
    # Simple template rendering (replace {{variable}} with values)
    html_preview = template["html_content"]
    subject_preview = template["subject"]
    
    for key, value in sample_data.items():
        html_preview = html_preview.replace("{{" + key + "}}", str(value))
        subject_preview = subject_preview.replace("{{" + key + "}}", str(value))
    
    # Handle conditional blocks (simplified)
    import re
    # Remove {{#if ...}} and {{/if}} but keep content
    html_preview = re.sub(r'\{\{#if \w+\}\}', '', html_preview)
    html_preview = re.sub(r'\{\{/if\}\}', '', html_preview)
    
    return {
        "subject": subject_preview,
        "html_content": html_preview
    }


# Helper function to render template with data
def render_template(template_content: str, data: dict) -> str:
    """Render a template by replacing variables with data"""
    import re
    
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
