"""
SMS Routes

Provides endpoints for:
- Sending test SMS (platform admin only)
- Checking SMS service status
- Sending transactional SMS messages
"""

import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from routes.auth import get_current_user
from services.sms_service import SMSService

router = APIRouter(prefix="/sms", tags=["SMS"])


class TestSMSRequest(BaseModel):
    to: str
    message: Optional[str] = "This is a test SMS from SignGuy AI. Your Twilio integration is working!"


class SendSMSRequest(BaseModel):
    to: str
    body: str


@router.get("/status")
async def sms_status(current_user: dict = Depends(get_current_user)):
    """Check if SMS service is configured and available"""
    svc = SMSService()
    return {
        "configured": svc.is_configured(),
        "from_number": os.environ.get("TWILIO_PHONE_NUMBER", ""),
        "account_sid_prefix": os.environ.get("TWILIO_ACCOUNT_SID", "")[:8] + "..." if os.environ.get("TWILIO_ACCOUNT_SID") else "",
    }


@router.post("/test")
async def send_test_sms(payload: TestSMSRequest, current_user: dict = Depends(get_current_user)):
    """Send a test SMS — platform_admin / platform_creator only"""
    role = getattr(current_user, "role", "")
    if role not in ("platform_creator", "platform_admin"):
        raise HTTPException(status_code=403, detail="Platform admin access required")

    svc = SMSService()
    if not svc.is_configured():
        raise HTTPException(status_code=503, detail="SMS service not configured. Check TWILIO_* env vars.")

    result = await svc.send_sms(to=payload.to, body=payload.message)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send SMS"))

    return {"success": True, "sid": result.get("sid"), "to": payload.to}


@router.post("/send")
async def send_sms(payload: SendSMSRequest, current_user: dict = Depends(get_current_user)):
    """Send a transactional SMS message"""
    svc = SMSService()
    if not svc.is_configured():
        raise HTTPException(status_code=503, detail="SMS service not configured.")

    result = await svc.send_sms(to=payload.to, body=payload.body)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send SMS"))

    return {"success": True, "sid": result.get("sid")}
