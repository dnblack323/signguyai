"""
Webstore Owner Connect — Stripe Express onboarding & owner portal.

Two flows are supported, both initiated by the tenant from the Webstore detail
page:

1. **Quick Connect** (no portal account, no password):
   - Tenant clicks "Send Quick Connect Link" → we email a one-time tokenized
     URL to the owner's email.
   - Owner clicks the link → lands on a public branded page → "Connect Stripe"
     button creates a Stripe Express account + Account Link → Stripe-hosted
     onboarding → returns to our success page → we save the account id +
     status flags on the webstore.
   - No password, no login, no SignGuy account.

2. **Owner Portal** (full account, can see commissions, login anytime):
   - Tenant clicks "Create Owner Portal" → we email a portal-invite link.
   - Owner clicks → creates a SignGuy account scoped to ``role='webstore_owner'``
     with no tenant_id link → still gets pointed at the same Stripe Express
     onboarding flow as above.
   - After Stripe onboarding, owner can log in to ``/owner-portal`` to see
     their commission history, payouts, and click "Stripe Dashboard" to manage
     payouts.

Money flow on order completion:
- ``checkout.session.completed`` (already handled in stripe_connect.py) finalizes
  the order, which puts ``commission_amount`` into ``webstore.payout_owed``.
- For webstores with ``owner_stripe_account_id`` set + ``owner_stripe_charges_enabled``,
  we additionally fire ``stripe.Transfer.create(amount=commission, destination=owner_acct)``
  from the tenant's connected account to the owner's connected account.
- Idempotent via ``transfer_group = f"order_{order_id}"`` + an `owner_transfer_id`
  field on the webstore_order doc so we never double-pay.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
import os
import secrets
import logging

import stripe
from motor.motor_asyncio import AsyncIOMotorClient

from models import UserInDB
from core.auth_deps import get_current_active_user
from services.email_service import email_service

logger = logging.getLogger(__name__)

mongo_client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
db = mongo_client[os.environ.get("DB_NAME", "signguy")]

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY") or os.environ.get("STRIPE_API_KEY")

# Tenant-facing actions
router = APIRouter(prefix="/webstore-owners", tags=["Webstore Owner Connect"])

# Public (token-bound) actions used by the owner onboarding magic-link landing page
public_router = APIRouter(prefix="/owner-onboard", tags=["Webstore Owner Onboard (Public)"])


# ── Models ────────────────────────────────────────────────────────────────────

class OwnerInviteRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    public_url: Optional[str] = None  # frontend origin
    message: Optional[str] = None


class OwnerInviteResponse(BaseModel):
    success: bool
    invite_url: str
    expires_at: str
    message: str


class OwnerOnboardContext(BaseModel):
    webstore_id: str
    webstore_name: str
    tenant_company_name: str
    owner_name: str
    owner_email: EmailStr
    stripe_account_id: Optional[str] = None
    charges_enabled: bool = False
    payouts_enabled: bool = False
    details_submitted: bool = False
    portal_invite: bool = False


class StartStripeRequest(BaseModel):
    return_url: str
    refresh_url: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_token() -> str:
    return secrets.token_urlsafe(32)


def _public_origin(supplied: Optional[str]) -> str:
    return (supplied or os.environ.get("META_PUBLIC_URL", "") or "").rstrip("/")


async def _fetch_webstore(webstore_id: str, tenant_id: str) -> dict:
    ws = await db.webstores_v2.find_one(
        {"id": webstore_id, "tenant_id": tenant_id}, {"_id": 0}
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Webstore not found")
    return ws


async def _resolve_invite(token: str) -> dict:
    """Look up an unexpired, unused owner onboarding token."""
    invite = await db.webstore_owner_invites.find_one({"token": token}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    if invite.get("status") == "expired":
        raise HTTPException(status_code=410, detail="This invitation has expired")
    try:
        exp = datetime.fromisoformat(invite["expires_at"])
    except Exception:
        exp = datetime.now(timezone.utc)
    if datetime.now(timezone.utc) > exp:
        await db.webstore_owner_invites.update_one(
            {"token": token}, {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=410, detail="This invitation has expired")
    return invite


async def _sync_stripe_status(webstore_id: str, account_id: str) -> dict:
    """Refresh the cached charges/payouts/details flags from Stripe."""
    try:
        acct = stripe.Account.retrieve(account_id)
    except stripe.error.StripeError as exc:
        logger.warning("Failed to retrieve owner account %s: %s", account_id, exc)
        return {}
    flags = {
        "owner_stripe_account_id": account_id,
        "owner_stripe_charges_enabled": bool(acct.charges_enabled),
        "owner_stripe_payouts_enabled": bool(acct.payouts_enabled),
        "owner_stripe_details_submitted": bool(acct.details_submitted),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.webstores_v2.update_one({"id": webstore_id}, {"$set": flags})
    return flags


# ── Tenant-facing endpoints ───────────────────────────────────────────────────

async def _send_invite(
    webstore: dict,
    payload: OwnerInviteRequest,
    *,
    portal_invite: bool,
    current_user: UserInDB,
) -> OwnerInviteResponse:
    token = _new_token()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=72)
    owner_name = (payload.name or webstore.get("owner_name") or "there").strip()

    await db.webstore_owner_invites.insert_one({
        "token": token,
        "webstore_id": webstore["id"],
        "tenant_id": current_user.tenant_id,
        "owner_email": payload.email,
        "owner_name": owner_name,
        "portal_invite": portal_invite,
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "invited_by": current_user.id,
    })

    # Also persist the owner email on the webstore if missing so the storefront UI can show it
    if not webstore.get("owner_email"):
        await db.webstores_v2.update_one(
            {"id": webstore["id"]},
            {"$set": {"owner_email": payload.email, "updated_at": now.isoformat()}},
        )

    origin = _public_origin(payload.public_url)
    path = "owner-portal-signup" if portal_invite else "webstore-owner/onboard"
    link = f"{origin}/{path}/{token}" if origin else f"/{path}/{token}"

    tenant = await db.tenants.find_one({"tenant_id": current_user.tenant_id}, {"_id": 0})
    company_name = (tenant or {}).get("company_name") or "SignGuy AI"

    intro = payload.message or (
        f"{company_name} has set up a webstore for you on SignGuy AI. "
        "To receive your sales directly to your bank account, please connect your Stripe account."
    )
    if portal_invite:
        cta = "Create Your Owner Portal"
        sub = (
            "After creating your portal, you'll be able to log in anytime to see your sales, "
            "commission earnings, and payouts."
        )
    else:
        cta = "Connect Stripe (Quick Setup)"
        sub = "Takes about 5 minutes. You'll be paid directly to your bank — no login required."

    subject = f"Connect your Stripe account for {webstore.get('name')}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; color: #0F172A;">
      <h2 style="color: #0F172A; margin-bottom: 4px;">Welcome, {owner_name}!</h2>
      <p style="color: #475569; margin-top: 0;">From {company_name}</p>
      <p>{intro}</p>
      <p style="color: #475569;">{sub}</p>
      <p style="margin: 28px 0;">
        <a href="{link}"
           style="background:#2F8BFB;color:#ffffff;padding:12px 24px;border-radius:8px;
                  text-decoration:none;display:inline-block;font-weight:600;">
          {cta}
        </a>
      </p>
      <p style="color:#475569;font-size:13px;">
        This link expires in 72 hours. If the button doesn't work, copy &amp; paste into your browser:<br/>
        <a href="{link}" style="color:#2F8BFB;">{link}</a>
      </p>
      <hr style="border:none;border-top:1px solid #E2E8F0;margin:24px 0;"/>
      <p style="color:#94A3B8;font-size:12px;">Sent by {company_name} via SignGuy AI</p>
    </div>
    """
    plain = (
        f"Welcome, {owner_name}!\n\n"
        f"{intro}\n\n"
        f"{sub}\n\n"
        f"Open this link to continue: {link}\n\n"
        f"(Link expires in 72 hours.)\n\n"
        f"— {company_name}"
    )

    result = await email_service.send_email(
        to_email=payload.email,
        subject=subject,
        html_content=html,
        plain_content=plain,
        tenant_id=current_user.tenant_id,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error") or "Failed to send invite email (check SendGrid).",
        )

    return OwnerInviteResponse(
        success=True,
        invite_url=link,
        expires_at=expires_at.isoformat(),
        message=f"Connect link sent to {payload.email}.",
    )


@router.post("/{webstore_id}/invite/quick", response_model=OwnerInviteResponse)
async def invite_owner_quick(
    webstore_id: str,
    payload: OwnerInviteRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Send a no-login magic Connect Stripe link to the webstore owner."""
    webstore = await _fetch_webstore(webstore_id, current_user.tenant_id)
    return await _send_invite(webstore, payload, portal_invite=False, current_user=current_user)


@router.post("/{webstore_id}/invite/portal", response_model=OwnerInviteResponse)
async def invite_owner_portal(
    webstore_id: str,
    payload: OwnerInviteRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Send a portal-signup link so the owner can create a SignGuy account
    AND connect Stripe."""
    webstore = await _fetch_webstore(webstore_id, current_user.tenant_id)
    return await _send_invite(webstore, payload, portal_invite=True, current_user=current_user)


@router.get("/{webstore_id}/owner-status")
async def get_owner_status(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Tenant: see whether the owner has finished Stripe onboarding."""
    ws = await _fetch_webstore(webstore_id, current_user.tenant_id)
    return {
        "owner_email": ws.get("owner_email"),
        "owner_name": ws.get("owner_name"),
        "owner_stripe_account_id": ws.get("owner_stripe_account_id"),
        "charges_enabled": bool(ws.get("owner_stripe_charges_enabled")),
        "payouts_enabled": bool(ws.get("owner_stripe_payouts_enabled")),
        "details_submitted": bool(ws.get("owner_stripe_details_submitted")),
        "portal_enabled": bool(ws.get("owner_portal_enabled")),
        "ready_to_activate": bool(
            ws.get("owner_stripe_account_id") and ws.get("owner_stripe_charges_enabled")
        ),
    }


# ── Public (token-bound) endpoints ────────────────────────────────────────────

@public_router.get("/{token}", response_model=OwnerOnboardContext)
async def get_onboard_context(token: str):
    """Public: validate token and return webstore + owner context for the
    branded landing page."""
    invite = await _resolve_invite(token)
    ws = await db.webstores_v2.find_one({"id": invite["webstore_id"]}, {"_id": 0})
    if not ws:
        raise HTTPException(status_code=404, detail="Webstore not found")
    tenant = await db.tenants.find_one({"tenant_id": ws.get("tenant_id")}, {"_id": 0})
    company = (tenant or {}).get("company_name") or "Your Sign Shop"

    return OwnerOnboardContext(
        webstore_id=ws["id"],
        webstore_name=ws["name"],
        tenant_company_name=company,
        owner_name=invite.get("owner_name") or ws.get("owner_name") or "",
        owner_email=invite["owner_email"],
        stripe_account_id=ws.get("owner_stripe_account_id"),
        charges_enabled=bool(ws.get("owner_stripe_charges_enabled")),
        payouts_enabled=bool(ws.get("owner_stripe_payouts_enabled")),
        details_submitted=bool(ws.get("owner_stripe_details_submitted")),
        portal_invite=bool(invite.get("portal_invite")),
    )


@public_router.post("/{token}/start-stripe")
async def start_stripe_onboarding(token: str, body: StartStripeRequest):
    """Public: create (or reuse) the Stripe Express account for this owner
    and return an AccountLink URL for them to complete onboarding."""
    invite = await _resolve_invite(token)
    ws = await db.webstores_v2.find_one({"id": invite["webstore_id"]}, {"_id": 0})
    if not ws:
        raise HTTPException(status_code=404, detail="Webstore not found")

    account_id = ws.get("owner_stripe_account_id")
    try:
        if not account_id:
            account = stripe.Account.create(
                type="express",
                email=invite["owner_email"],
                capabilities={
                    "transfers": {"requested": True},
                    "card_payments": {"requested": True},
                },
                metadata={
                    "signguy_webstore_id": ws["id"],
                    "signguy_tenant_id": ws.get("tenant_id") or "",
                    "signguy_invite_token": token,
                },
            )
            account_id = account.id
            await db.webstores_v2.update_one(
                {"id": ws["id"]},
                {"$set": {
                    "owner_stripe_account_id": account_id,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }},
            )

        link = stripe.AccountLink.create(
            account=account_id,
            return_url=body.return_url,
            refresh_url=body.refresh_url,
            type="account_onboarding",
        )
        return {"url": link.url, "account_id": account_id}
    except stripe.error.StripeError as exc:
        logger.exception("Stripe onboarding failed for invite %s", token)
        raise HTTPException(status_code=502, detail=str(exc))


@public_router.get("/{token}/refresh")
async def refresh_status(token: str):
    """Public: poll Stripe for latest charges/payouts/details_submitted flags
    after the owner returns from the hosted onboarding."""
    invite = await _resolve_invite(token)
    ws = await db.webstores_v2.find_one({"id": invite["webstore_id"]}, {"_id": 0})
    if not ws:
        raise HTTPException(status_code=404, detail="Webstore not found")
    if not ws.get("owner_stripe_account_id"):
        return {"ready": False, "charges_enabled": False, "payouts_enabled": False}

    flags = await _sync_stripe_status(ws["id"], ws["owner_stripe_account_id"])
    ready = flags.get("owner_stripe_charges_enabled", False)

    # If fully onboarded, mark the invite consumed
    if ready and invite.get("status") == "pending":
        await db.webstore_owner_invites.update_one(
            {"token": token}, {"$set": {"status": "consumed", "consumed_at": datetime.now(timezone.utc).isoformat()}}
        )
    return {
        "ready": ready,
        "charges_enabled": flags.get("owner_stripe_charges_enabled", False),
        "payouts_enabled": flags.get("owner_stripe_payouts_enabled", False),
        "details_submitted": flags.get("owner_stripe_details_submitted", False),
    }


@public_router.post("/{token}/login-link")
async def owner_login_link(token: str):
    """Public: generate a one-time Stripe Express dashboard login link for the
    owner so they can manage payouts/bank info via Stripe directly."""
    invite = await _resolve_invite(token)
    ws = await db.webstores_v2.find_one({"id": invite["webstore_id"]}, {"_id": 0})
    if not ws or not ws.get("owner_stripe_account_id"):
        raise HTTPException(status_code=400, detail="Owner has not completed Stripe onboarding yet")
    try:
        link = stripe.Account.create_login_link(ws["owner_stripe_account_id"])
        return {"url": link.url}
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


# ── Owner Portal — signup + scoped dashboard ──────────────────────────────────
#
# Tenants who picked "Create Owner Portal" instead of "Quick Connect" invite
# the owner to a flow that ALSO creates a SignGuy login (role='webstore_owner').
# The owner can later log in to /owner-portal to see commissions + payouts.

portal_router = APIRouter(prefix="/owner-portal", tags=["Webstore Owner Portal"])


class PortalSignupRequest(BaseModel):
    token: str
    password: str
    full_name: Optional[str] = None


class PortalSignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    webstore_id: str


@portal_router.post("/signup", response_model=PortalSignupResponse)
async def portal_signup(req: PortalSignupRequest):
    """Public: create a webstore_owner SignGuy account from a portal-type
    invite token. Returns a JWT scoped to that owner."""
    from server import get_password_hash, create_access_token

    invite = await _resolve_invite(req.token)
    if not invite.get("portal_invite"):
        raise HTTPException(status_code=400, detail="This invite is for quick connect, not a portal account.")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    email = invite["owner_email"].lower()
    # Reuse existing owner account if one exists; else create
    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing and existing.get("role") not in (None, "webstore_owner"):
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists with a different role. Log in instead.",
        )

    now = datetime.now(timezone.utc).isoformat()
    if existing:
        user_id = existing["id"]
        # update password + ensure role
        await db.users.update_one(
            {"id": user_id},
            {"$set": {
                "hashed_password": get_password_hash(req.password),
                "role": "webstore_owner",
                "full_name": req.full_name or existing.get("full_name") or invite.get("owner_name") or "",
                "is_active": True,
                "updated_at": now,
            }},
        )
    else:
        user_id = str(__import__("uuid").uuid4())
        await db.users.insert_one({
            "id": user_id,
            "email": email,
            "full_name": req.full_name or invite.get("owner_name") or "",
            "hashed_password": get_password_hash(req.password),
            "role": "webstore_owner",
            "tenant_id": None,  # webstore owners are not tenant-scoped
            "is_active": True,
            "is_founder": False,
            "created_at": now,
            "updated_at": now,
        })

    # Link the webstore to this owner user
    await db.webstores_v2.update_one(
        {"id": invite["webstore_id"]},
        {"$set": {
            "owner_user_id": user_id,
            "owner_portal_enabled": True,
            "updated_at": now,
        }},
    )

    token = create_access_token({"sub": user_id, "email": email, "role": "webstore_owner"})
    return PortalSignupResponse(
        access_token=token,
        user_id=user_id,
        webstore_id=invite["webstore_id"],
    )


async def _require_owner_user(current_user: UserInDB) -> dict:
    if getattr(current_user, "role", None) != "webstore_owner":
        raise HTTPException(status_code=403, detail="Owner portal access only")
    return {"id": current_user.id, "email": current_user.email}


@portal_router.get("/me")
async def portal_me(current_user: UserInDB = Depends(get_current_active_user)):
    """Owner: list my linked stores + commission summary + Stripe state."""
    await _require_owner_user(current_user)

    stores = await db.webstores_v2.find(
        {"owner_user_id": current_user.id},
        {
            "_id": 0,
            "id": 1, "name": 1, "store_type": 1, "status": 1,
            "owner_stripe_account_id": 1,
            "owner_stripe_charges_enabled": 1,
            "owner_stripe_payouts_enabled": 1,
            "owner_stripe_details_submitted": 1,
            "payout_owed": 1, "payout_paid": 1,
            "total_sales": 1, "total_orders": 1,
        },
    ).to_list(50)

    return {
        "owner": {"id": current_user.id, "email": current_user.email, "full_name": getattr(current_user, "full_name", None)},
        "stores": stores,
    }


@portal_router.get("/stores/{webstore_id}/transfers")
async def portal_store_transfers(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Owner: list recent commission Transfers credited to me for this store."""
    await _require_owner_user(current_user)
    ws = await db.webstores_v2.find_one(
        {"id": webstore_id, "owner_user_id": current_user.id},
        {"_id": 0, "owner_stripe_account_id": 1, "name": 1},
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Store not found")

    # Pull recent orders with owner_transfer_id set
    orders = await db.webstore_orders_v2.find(
        {"webstore_id": webstore_id, "owner_transfer_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "id": 1, "order_number": 1, "owner_transfer_id": 1,
         "owner_transfer_amount": 1, "owner_transfer_at": 1, "status": 1,
         "total_amount": 1, "created_at": 1, "customer_name": 1},
    ).sort("owner_transfer_at", -1).to_list(100)

    return {"store_name": ws.get("name"), "transfers": orders}


@portal_router.post("/stores/{webstore_id}/stripe-login-link")
async def portal_stripe_login(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Owner: open the Stripe Express dashboard for the connected store."""
    await _require_owner_user(current_user)
    ws = await db.webstores_v2.find_one(
        {"id": webstore_id, "owner_user_id": current_user.id},
        {"_id": 0, "owner_stripe_account_id": 1},
    )
    if not ws or not ws.get("owner_stripe_account_id"):
        raise HTTPException(status_code=400, detail="Stripe account not connected for this store")
    try:
        link = stripe.Account.create_login_link(ws["owner_stripe_account_id"])
        return {"url": link.url}
    except stripe.error.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
