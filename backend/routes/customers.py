"""
Customer Management Routes

This module contains all routes related to:
- Customer CRUD operations
- Customer search and filtering
- Bulk import from CSV
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import random
import re

from models import (
    Customer, CustomerCreate, CustomerUpdate, CustomerStatus,
    UserInDB, Permission
)

# Import from server module (will be refactored later)
from server import (
    db, logger,
    get_current_active_user, has_permission
)
from server import get_password_hash

router = APIRouter(prefix="/customers", tags=["Customers"])

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class CustomerImportItem(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = "lead"
    notes: Optional[str] = None


class CustomerImportRequest(BaseModel):
    customers: List[CustomerImportItem]


class CustomerImportResponse(BaseModel):
    created: int
    updated: int
    errors: List[str]


class PortalInviteResponse(BaseModel):
    message: str
    portal_enabled: bool
    temporary_pin: str


@router.post("", response_model=Customer)
async def create_customer(
    input: CustomerCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new customer and optionally send welcome email"""
    payload = input.model_dump()
    name_val = (payload.get("name") or "").strip()
    company_val = (payload.get("company") or "").strip()
    if not name_val and not company_val:
        raise HTTPException(status_code=400, detail="Name or Company is required")
    # Auto-generate display_name: prefer company, fallback to name (no spaces, CamelCase)
    if not payload.get("display_name"):
        raw = company_val or name_val
        payload["display_name"] = raw.replace(" ", "")
    payload["name"] = name_val or company_val

    customer = Customer(**payload)
    customer.tenant_id = current_user.tenant_id
    doc = customer.model_dump()
    await db.customers.insert_one(doc)
    
    # Check tenant settings for auto-welcome email
    tenant = await db.tenants.find_one(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    # Send welcome email if enabled and customer has email
    if tenant and tenant.get("auto_welcome_email", True) and customer.email:
        try:
            from services.email_service import email_service
            await email_service.send_welcome_email(
                customer_email=customer.email,
                customer_name=customer.name or customer.contact_name or "Valued Customer",
                tenant_id=current_user.tenant_id
            )
            logger.info(f"Welcome email sent to new customer {customer.email}")
        except Exception as e:
            # Don't fail customer creation if email fails
            logger.error(f"Failed to send welcome email: {str(e)}")
    
    return customer


@router.get("/export")
async def export_customers(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Export all customers to CSV (name, email, phone, company, status)."""
    import csv
    from io import StringIO
    from fastapi.responses import StreamingResponse

    customers = await db.customers.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10000)

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["name", "email", "phone", "company", "status", "notes", "created_at"])
    for c in customers:
        writer.writerow([
            c.get("name") or "",
            c.get("email") or "",
            c.get("phone") or "",
            c.get("company") or "",
            c.get("status") or "",
            c.get("notes") or "",
            c.get("created_at") or "",
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=customers_export.csv"}
    )


@router.post("/import", response_model=CustomerImportResponse)
async def import_customers(
    request: CustomerImportRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Bulk import customers from CSV data"""
    if not request.customers:
        raise HTTPException(status_code=400, detail="CSV file must include at least one customer row")

    created = 0
    updated = 0
    errors = []
    inserted_customer_ids = []
    updated_snapshots = []
    
    try:
        for i, item in enumerate(request.customers):
            # Validate name
            resolved_name = (item.name or '').strip() or (item.company or '').strip()
            if not resolved_name:
                errors.append(f"Row {i + 1}: Name or Company is required")
                continue

            normalized_email = item.email.strip() if item.email else None
            if normalized_email and not EMAIL_REGEX.match(normalized_email):
                errors.append(f"Row {i + 1}: Invalid email format")
                continue
            
            # Check for existing customer with same email (if email provided)
            existing = None
            if normalized_email:
                existing = await db.customers.find_one({
                    "email": normalized_email,
                    "tenant_id": current_user.tenant_id
                }, {"_id": 0})
            
            # Normalize status
            status = "lead"
            if item.status and item.status.lower() in ["lead", "active", "inactive"]:
                status = item.status.lower()
            
            if existing:
                # Update existing customer
                update_data = {
                    "name": resolved_name,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                if item.company:
                    update_data["company"] = item.company.strip()
                if item.phone:
                    update_data["phone"] = item.phone.strip()
                if item.notes:
                    update_data["notes"] = item.notes.strip()
                update_data["status"] = status

                updated_snapshots.append({
                    "id": existing["id"],
                    "document": existing,
                })
                
                await db.customers.update_one(
                    {"id": existing["id"], "tenant_id": current_user.tenant_id},
                    {"$set": update_data}
                )
                updated += 1
            else:
                # Create new customer
                customer = Customer(
                    name=resolved_name,
                    company=item.company.strip() if item.company else None,
                    email=normalized_email,
                    phone=item.phone.strip() if item.phone else None,
                    status=status,
                    notes=item.notes.strip() if item.notes else None,
                    tenant_id=current_user.tenant_id
                )
                await db.customers.insert_one(customer.model_dump())
                inserted_customer_ids.append(customer.id)
                created += 1

    except Exception as e:
        logger.error(f"Import failed mid-way. Rolling back customer import: {str(e)}")

        if inserted_customer_ids:
            await db.customers.delete_many({
                "tenant_id": current_user.tenant_id,
                "id": {"$in": inserted_customer_ids},
            })

        for snapshot in reversed(updated_snapshots):
            original = dict(snapshot["document"])
            original.pop("_id", None)
            await db.customers.replace_one(
                {"id": snapshot["id"], "tenant_id": current_user.tenant_id},
                original,
                upsert=True,
            )

        return CustomerImportResponse(
            created=0,
            updated=0,
            errors=[f"Import failed and was rolled back: {str(e)}"],
        )
    
    return CustomerImportResponse(created=created, updated=updated, errors=errors)


@router.get("", response_model=List[Customer])
async def get_customers(
    status: Optional[CustomerStatus] = None,
    search: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all customers with optional filtering"""
    query = {"tenant_id": current_user.tenant_id}
    if status:
        query["status"] = status.value
    if search:
        escaped_search = re.escape(search)
        query["$or"] = [
            {"name": {"$regex": escaped_search, "$options": "i"}},
            {"company": {"$regex": escaped_search, "$options": "i"}},
            {"email": {"$regex": escaped_search, "$options": "i"}},
            {"phone": {"$regex": escaped_search, "$options": "i"}},
        ]
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    return customers


@router.get("/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific customer by ID"""
    customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}, 
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/{customer_id}/invite-portal", response_model=PortalInviteResponse)
async def invite_customer_to_portal(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    customer = await db.customers.find_one({"id": customer_id, "tenant_id": current_user.tenant_id}, {"_id": 0})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if not customer.get("email"):
        raise HTTPException(status_code=400, detail="Customer needs an email address before portal access can be invited")

    temporary_pin = f"{random.randint(100000, 999999)}"
    hashed = get_password_hash(temporary_pin)
    now = datetime.now(timezone.utc).isoformat()
    await db.customers.update_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id},
        {"$set": {
            "portal_enabled": True,
            "portal_password_hash": hashed,
            "portal_invited_at": now,
            "updated_at": now,
        }}
    )

    tenant = await db.tenants.find_one({"id": current_user.tenant_id}, {"_id": 0})
    portal_link = f"{tenant.get('portal_url') or ''}/customer-portal/login" if tenant else "/customer-portal/login"

    try:
        from services.email_service import email_service
        html = f"""
        <h2>Your Customer Portal is Ready</h2>
        <p>Hi {customer.get('name')},</p>
        <p>You have been invited to access your SignGuy AI customer portal.</p>
        <p><strong>Portal Login:</strong> {customer.get('email')}</p>
        <p><strong>Temporary PIN:</strong> {temporary_pin}</p>
        <p>Please sign in and change your password after your first login.</p>
        <p><a href=\"{portal_link}\">Open Customer Portal</a></p>
        """
        await email_service.send_email(
            to_email=customer.get("email"),
            subject="Your Customer Portal Invitation",
            html_content=html,
            tenant_id=current_user.tenant_id,
        )
    except Exception as exc:
        logger.error(f"Failed to send portal invitation email: {exc}")

    return PortalInviteResponse(
        message="Portal invitation created",
        portal_enabled=True,
        temporary_pin=temporary_pin,
    )


@router.put("/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: str, 
    input: CustomerUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a customer"""
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    existing_customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not existing_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    resolved_name = (update_data.get("name") if "name" in update_data else existing_customer.get("name") or '').strip() or (
        update_data.get("company") if "company" in update_data else existing_customer.get("company") or ''
    ).strip()
    if not resolved_name:
        raise HTTPException(status_code=400, detail="Name or Company is required")
    update_data["name"] = resolved_name
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.customers.update_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a customer"""
    delete_result = await db.customers.delete_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}
    )
    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted"}


@router.get("/{customer_id}/summary")
async def get_customer_summary(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a summary of customer activity (quotes, jobs, invoices)"""
    # Verify customer exists and belongs to tenant
    customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get counts
    quote_count = await db.quotes.count_documents({
        "customer_id": customer_id, 
        "tenant_id": current_user.tenant_id
    })
    job_count = await db.jobs.count_documents({
        "customer_id": customer_id, 
        "tenant_id": current_user.tenant_id
    })
    invoice_count = await db.invoices.count_documents({
        "customer_id": customer_id, 
        "tenant_id": current_user.tenant_id
    })
    
    # Get totals
    invoices = await db.invoices.find(
        {"customer_id": customer_id, "tenant_id": current_user.tenant_id},
        {"_id": 0, "grand_total": 1, "amount_paid": 1, "status": 1}
    ).to_list(1000)
    
    total_invoiced = sum(inv.get("grand_total", 0) for inv in invoices)
    total_paid = sum(inv.get("amount_paid", 0) for inv in invoices)
    total_outstanding = total_invoiced - total_paid
    
    return {
        "customer": customer,
        "quotes_count": quote_count,
        "jobs_count": job_count,
        "invoices_count": invoice_count,
        "total_invoiced": round(total_invoiced, 2),
        "total_paid": round(total_paid, 2),
        "total_outstanding": round(total_outstanding, 2)
    }
