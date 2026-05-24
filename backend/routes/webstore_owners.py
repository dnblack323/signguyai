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

    # Phase 4 — sync the invited owner into Customers with webstore_owner tag.
    # Failure is non-fatal: invite delivery is more important than the side-effect.
    try:
        from routes.webstores import _upsert_webstore_customer
        await _upsert_webstore_customer(
            tenant_id=current_user.tenant_id,
            name=owner_name,
            email=payload.email,
            phone=webstore.get("owner_phone"),
            tag="webstore_owner",
            company=webstore.get("name"),
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Owner customer sync failed for invite %s: %s", webstore.get("id"), exc)

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


# ── Phase 5 — Owner-facing progress + financial transparency ──────────────
#
# Returns a single privacy-safe payload an owner can use to:
#   * see exactly where the store is in its lifecycle
#   * see what they still need to do
#   * understand the split math behind any pending payout
#
# Strict privacy: never returns base_cost / production_cost / margin /
# supplier_cost / internal_notes / staff comments. Only owner-facing
# financial fields are included.

OWNER_FINANCIAL_FIELDS_SAFE = {
    "total_sales",        # owner already sees this
    "total_orders",
    "payout_owed",
    "payout_paid",
    "total_donations_received",
    "total_profit_allocation_received",
    "fundraiser_total_raised",
}


@portal_router.get("/stores/{webstore_id}/progress")
async def portal_store_progress(
    webstore_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Owner-facing lifecycle progress + required actions + finance breakdown."""
    await _require_owner_user(current_user)

    ws = await db.webstores_v2.find_one(
        {"id": webstore_id, "owner_user_id": current_user.id},
        {"_id": 0},
    )
    if not ws:
        raise HTTPException(status_code=404, detail="Store not found")

    now_iso = datetime.now(timezone.utc).isoformat()

    # ── Aggregate financial signals (privacy-safe) ────────────────────────
    # Source-of-truth alignment with /api/webstores/v2/{id}/analytics — we
    # aggregate live from webstore_orders_v2 instead of trusting the cached
    # counters on the webstores_v2 document. Cached fields drift when order
    # state changes (refunds, cancellations) so reading them produced a
    # $20 / 1-order discrepancy in iteration_169 testing.
    _orders_rows = await db.webstore_orders_v2.find(
        {"webstore_id": webstore_id},
        {"_id": 0, "subtotal": 1, "total_profit": 1, "commission_amount": 1,
         "donation_amount": 1, "profit_allocation_amount": 1, "status": 1},
    ).to_list(2000)
    gross_sales = sum(float(o.get("subtotal") or 0) for o in _orders_rows)
    total_orders = len(_orders_rows)
    total_commission = sum(float(o.get("commission_amount") or 0) for o in _orders_rows)
    total_donations_live = sum(float(o.get("donation_amount") or 0) for o in _orders_rows)
    total_allocation_live = sum(float(o.get("profit_allocation_amount") or 0) for o in _orders_rows)

    # Payout numbers are operational (paid by tenant outside the orders
    # collection) so they still come from the webstores_v2 doc, which is the
    # authoritative payout ledger maintained by record_payout().
    payout_owed = float(ws.get("payout_owed") or 0)
    payout_paid = float(ws.get("payout_paid") or 0)
    # If payout_owed wasn't set explicitly, fall back to commission total.
    if payout_owed == 0 and total_commission > 0:
        payout_owed = round(total_commission - payout_paid, 2)
    # Donations / profit-allocation prefer the live sum but fall back to the
    # cached aggregates on the webstores_v2 doc when no order-level field exists.
    total_donations = total_donations_live or float(ws.get("total_donations_received") or 0)
    total_allocation = total_allocation_live or float(ws.get("total_profit_allocation_received") or 0)
    fundraiser_raised = float(ws.get("fundraiser_total_raised") or 0)
    # Net pending is the amount still due to the owner.
    net_pending = round(max(payout_owed, 0), 2)

    # ── Questionnaire + Stripe + content readiness ────────────────────────
    questionnaire = await db.questionnaires.find_one(
        {"webstore_id": webstore_id},
        {"_id": 0, "id": 1, "status": 1, "response_count": 1},
    )
    questionnaire_submitted = bool(
        questionnaire and int(questionnaire.get("response_count") or 0) > 0
    )

    stripe_ready = bool(
        ws.get("owner_stripe_account_id")
        and ws.get("owner_stripe_charges_enabled")
        and ws.get("owner_stripe_payouts_enabled")
    )

    has_logo = bool(((ws.get("branding") or {}).get("logo_url")))
    has_products = bool(ws.get("product_count") or 0)
    if not has_products:
        # Fallback: count assigned products if the cached value is stale.
        try:
            has_products = await db.webstore_products.count_documents(
                {"webstore_id": webstore_id}
            ) > 0
        except Exception:  # pragma: no cover - defensive
            has_products = False

    store_status = (ws.get("status") or "draft").lower()
    storefront_published = store_status in {"active", "live", "approved"}
    store_closed = store_status in {"closed", "completed"}

    # Order signals (re-using the rows already loaded above)
    recent_orders = total_orders
    completed_orders = sum(1 for o in _orders_rows if (o.get("status") or "").lower() == "completed")

    # ── Lifecycle stage computation ───────────────────────────────────────
    # 15 owner-facing stages, in chronological order. We mark each as
    # done/active/todo so the UI can render a progress meter.
    stages = [
        {"key": "setup_received",         "label": "Store setup received"},
        {"key": "questionnaire_submitted","label": "Questionnaire submitted"},
        {"key": "waiting_artwork",        "label": "Waiting on logo / artwork"},
        {"key": "store_being_built",      "label": "Store being built"},
        {"key": "products_being_added",   "label": "Products being added"},
        {"key": "pricing_review",         "label": "Pricing being reviewed"},
        {"key": "preview_ready",          "label": "Storefront preview ready"},
        {"key": "awaiting_owner_approval","label": "Awaiting owner approval"},
        {"key": "store_approved",         "label": "Store approved"},
        {"key": "store_live",             "label": "Store live"},
        {"key": "orders_coming_in",       "label": "Orders coming in"},
        {"key": "store_closed",           "label": "Store closed"},
        {"key": "production_started",     "label": "Production started"},
        {"key": "ready_for_pickup",       "label": "Ready for pickup / distribution"},
        {"key": "completed",              "label": "Completed"},
    ]
    done_flags = {
        "setup_received":          True,  # the store record itself exists
        "questionnaire_submitted": questionnaire_submitted,
        "waiting_artwork":         has_logo,
        "store_being_built":       has_products or storefront_published,
        "products_being_added":    has_products,
        "pricing_review":          has_products,  # admin sets prices alongside products
        "preview_ready":           bool(ws.get("preview_ready_at")) or storefront_published,
        "awaiting_owner_approval": bool(ws.get("owner_approved_at")) or storefront_published,
        "store_approved":          bool(ws.get("owner_approved_at")) or storefront_published,
        "store_live":              storefront_published and not store_closed,
        "orders_coming_in":        recent_orders > 0,
        "store_closed":            store_closed,
        "production_started":      completed_orders > 0 or bool(ws.get("production_started_at")),
        "ready_for_pickup":        bool(ws.get("ready_for_pickup_at")),
        "completed":               store_status == "completed",
    }
    # Walk stages, marking the first not-done stage as the current one.
    current_idx = 0
    for i, s in enumerate(stages):
        if done_flags.get(s["key"]):
            s["status"] = "done"
            current_idx = i + 1
        else:
            break
    for i, s in enumerate(stages):
        if "status" not in s:
            s["status"] = "active" if i == current_idx else "todo"

    if current_idx >= len(stages):
        current_stage = stages[-1]
        next_blocker = None
    else:
        current_stage = stages[current_idx]
        # Human-readable explanation of what's blocking the next stage.
        blocker_map = {
            "questionnaire_submitted": "Submit the setup questionnaire so we can build your store.",
            "waiting_artwork":         "Upload your logo / artwork so we can finalise the storefront.",
            "store_being_built":       "Our team is finishing the storefront. No action needed.",
            "products_being_added":    "Our team is loading your product catalog. No action needed.",
            "pricing_review":          "Our team is reviewing pricing. No action needed.",
            "preview_ready":           "Storefront preview is in progress.",
            "awaiting_owner_approval": "Review the storefront preview and approve to go live.",
            "store_approved":          "Awaiting final approval to publish.",
            "store_live":              "Complete Stripe Connect so payouts can flow.",
            "orders_coming_in":        "Share your store link to start collecting orders.",
            "store_closed":            "Close the store when sales end.",
            "production_started":      "We'll start production once the store closes.",
            "ready_for_pickup":        "Items are being produced. We'll notify you when ready.",
            "completed":               "Pickup / distribution in progress.",
        }
        next_blocker = blocker_map.get(current_stage["key"], None)

    # ── Required owner actions ───────────────────────────────────────────
    required_actions = [
        {
            "key": "complete_questionnaire",
            "label": "Complete the setup questionnaire",
            "status": "done" if questionnaire_submitted else "todo",
            "cta_url": f"/questionnaire/{questionnaire['id']}" if questionnaire else None,
            "reason": (
                "Done — thank you!"
                if questionnaire_submitted
                else "We need a few details about your event / fundraiser / store before we can build it."
            ),
        },
        {
            "key": "upload_artwork",
            "label": "Upload logo / artwork",
            "status": "done" if has_logo else "todo",
            "cta_url": f"/questionnaire/{questionnaire['id']}" if questionnaire else None,
            "reason": (
                "Logo received."
                if has_logo
                else "Upload your logo so we can finalise the storefront design."
            ),
        },
        {
            "key": "review_preview",
            "label": "Review the storefront preview",
            "status": "done" if (bool(ws.get("owner_approved_at")) or storefront_published) else "todo",
            "cta_url": f"/store/{webstore_id}",
            "reason": (
                "Preview approved."
                if (bool(ws.get("owner_approved_at")) or storefront_published)
                else "Open your storefront preview link and let us know if anything needs changes."
            ),
        },
        {
            "key": "approve_store",
            "label": "Approve store to go live",
            "status": "done" if storefront_published else "todo",
            "cta_url": None,
            "reason": (
                "Store is live."
                if storefront_published
                else "Sign off on the preview so we can publish the store."
            ),
        },
        {
            "key": "confirm_fulfillment",
            "label": "Confirm pickup / delivery details",
            "status": "done" if (ws.get("pickup_delivery_date") or ws.get("pickup_delivery_instructions")) else "todo",
            "cta_url": f"/questionnaire/{questionnaire['id']}" if questionnaire else None,
            "reason": (
                "Fulfillment details on file."
                if (ws.get("pickup_delivery_date") or ws.get("pickup_delivery_instructions"))
                else "Tell us how customers should receive their orders."
            ),
        },
        {
            "key": "stripe_onboarding",
            "label": "Complete Stripe Connect onboarding",
            "status": "done" if stripe_ready else "todo",
            "cta_url": None,  # FE swaps in stripe-login-link
            "reason": (
                "Stripe connected — payouts will land in your bank automatically."
                if stripe_ready
                else "Connect Stripe so we can send your sales directly to your bank."
            ),
        },
    ]

    # ── Financial transparency block ─────────────────────────────────────
    finance = {
        "gross_sales":                  round(gross_sales, 2),
        "total_orders":                 total_orders,
        "donations_collected":          round(total_donations, 2),
        "profit_allocation":            round(total_allocation, 2),
        "fundraiser_total_raised":      round(fundraiser_raised, 2),
        "payout_owed":                  round(payout_owed, 2),
        "payout_paid":                  round(payout_paid, 2),
        "net_pending_payout":           net_pending,
        # Plain-English split math explainer — the UI renders this verbatim
        # so owners always see exactly how the pending number was derived.
        "formula": (
            "Pending payout = Total owed to you so far "
            "− Payouts already sent. "
            "If you have a fundraiser, donations and profit allocation are "
            "shown separately so you can see exactly what was raised."
        ),
    }

    # ── Payout history (auth-scoped to this owner's store only) ──────────
    history_rows = await db.webstore_orders_v2.find(
        {"webstore_id": webstore_id, "owner_transfer_id": {"$exists": True, "$ne": None}},
        {"_id": 0, "id": 1, "order_number": 1,
         "owner_transfer_amount": 1, "owner_transfer_at": 1,
         "owner_transfer_id": 1, "customer_name": 1, "status": 1},
    ).sort("owner_transfer_at", -1).to_list(100)
    payout_history = [
        {
            "id": r.get("owner_transfer_id"),
            "date": r.get("owner_transfer_at"),
            "amount": float(r.get("owner_transfer_amount") or 0),
            "order_number": r.get("order_number"),
            "customer_name": r.get("customer_name"),
            "status": r.get("status") or "transferred",
            "reference": r.get("owner_transfer_id"),
        }
        for r in history_rows
    ]

    return {
        "store": {
            "id": ws["id"],
            "name": ws.get("name"),
            "store_type": ws.get("store_type"),
            "status": store_status,
        },
        "current_stage": {
            "key": current_stage["key"],
            "label": current_stage["label"],
            "index": current_idx,
            "total": len(stages),
        },
        "stages": stages,
        "next_blocker": next_blocker,
        "required_actions": required_actions,
        "finance": finance,
        "payout_history": payout_history,
        "as_of": now_iso,
        # Privacy banner consumed by the UI.
        "privacy_note": (
            "This view never shows internal cost, margin, or supplier data. "
            "Only your sales, donations, and payout totals are displayed."
        ),
    }


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
