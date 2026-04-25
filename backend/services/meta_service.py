"""
Meta / Facebook Service

Handles:
- Page access token encryption / decryption (Fernet)
- Meta Graph API calls: OAuth exchange, page listing, webhook subscription
- Webhook signature verification
- Audit logging for all Meta integration events

All external calls use httpx (already installed). DB uses a standalone Motor
client to avoid circular import through server.py.
"""

import os
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet, InvalidToken
from motor.motor_asyncio import AsyncIOMotorClient

# ── Standalone DB connection ──────────────────────────────────────────────────
_MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
_DB_NAME = os.environ.get("DB_NAME", "signguy_ai")
_client = AsyncIOMotorClient(_MONGO_URL)
db = _client[_DB_NAME]
logger = logging.getLogger(__name__)

# ── Meta Graph API constants ──────────────────────────────────────────────────
META_API_BASE = "https://graph.facebook.com/v20.0"
META_APP_ID = os.environ.get("META_APP_ID", "")
META_APP_SECRET = os.environ.get("META_APP_SECRET", "")
META_VERIFY_TOKEN = os.environ.get("META_WEBHOOK_VERIFY_TOKEN", "signguy_meta_webhook_2026")

# Minimum required scopes for Page Messenger integration
REQUIRED_SCOPES = ",".join([
    "pages_manage_metadata",
    "pages_read_engagement",
    "pages_messaging",
    "pages_show_list",
])


# ── Token encryption ──────────────────────────────────────────────────────────
def _get_fernet() -> Fernet:
    key = os.environ.get("META_TOKEN_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("META_TOKEN_ENCRYPTION_KEY is not configured in .env")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(token: str) -> str:
    """Encrypt a Page access token before storing it in the database."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    """Decrypt a stored Page access token. Raises InvalidToken if corrupt."""
    return _get_fernet().decrypt(encrypted.encode()).decode()


# ── OAuth helpers ─────────────────────────────────────────────────────────────
def get_oauth_url(redirect_uri: str, state: str) -> str:
    """Build the Meta Facebook authorization URL to redirect the tenant admin."""
    if not META_APP_ID:
        raise RuntimeError("META_APP_ID is not configured in .env")
    params = {
        "client_id": META_APP_ID,
        "redirect_uri": redirect_uri,
        "scope": REQUIRED_SCOPES,
        "response_type": "code",
        "state": state,
    }
    return f"https://www.facebook.com/v20.0/dialog/oauth?{urlencode(params)}"


async def exchange_code_for_token(code: str, redirect_uri: str) -> Dict[str, Any]:
    """Exchange an OAuth authorization code for a user access token."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{META_API_BASE}/oauth/access_token",
            params={
                "client_id": META_APP_ID,
                "client_secret": META_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def get_user_pages(user_access_token: str) -> List[Dict[str, Any]]:
    """Return the list of Facebook Pages the authenticated user manages."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{META_API_BASE}/me/accounts",
            params={
                "access_token": user_access_token,
                "fields": "id,name,access_token,category,fan_count",
            },
        )
        resp.raise_for_status()
        return resp.json().get("data", [])


async def subscribe_page_to_webhook(page_id: str, page_access_token: str) -> bool:
    """Subscribe a Page to our app webhook so we receive messages events."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{META_API_BASE}/{page_id}/subscribed_apps",
            params={
                "access_token": page_access_token,
                "subscribed_fields": "messages,messaging_postbacks,messaging_optins",
            },
        )
        return resp.json().get("success", False)


async def unsubscribe_page_from_webhook(page_id: str, page_access_token: str) -> bool:
    """Remove our app's webhook subscription from a Page."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.delete(
            f"{META_API_BASE}/{page_id}/subscribed_apps",
            params={"access_token": page_access_token},
        )
        return resp.json().get("success", False)


# ── Webhook signature validation ──────────────────────────────────────────────
def verify_webhook_signature(payload_bytes: bytes, signature_header: str) -> bool:
    """Validate that the webhook payload came from Meta using HMAC-SHA256.

    Meta sends the signature in the X-Hub-Signature-256 header as:
    'sha256=<hex_digest>'
    """
    if not META_APP_SECRET:
        # If secret is not configured, skip validation (dev only)
        return True
    expected = "sha256=" + hmac.new(
        META_APP_SECRET.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


# ── Audit log ─────────────────────────────────────────────────────────────────
async def log_audit_event(
    tenant_id: str,
    event_type: str,
    details: Dict[str, Any],
    user_id: Optional[str] = None,
    page_id: Optional[str] = None,
) -> None:
    """Append an immutable audit record for every Meta integration action."""
    await db.meta_audit_logs.insert_one(
        {
            "tenant_id": tenant_id,
            "event_type": event_type,
            "page_id": page_id,
            "user_id": user_id,
            "details": details,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
