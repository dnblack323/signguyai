"""
Customer Management Routes

This module contains all routes related to:
- Customer CRUD operations
- Customer search and filtering
- Bulk import from CSV
- Soft delete and restore
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from models import (
    Customer, CustomerCreate, CustomerUpdate, CustomerStatus,
    UserInDB, Permission
)

# Import from server module (will be refactored later)
from server import (
    db, logger,
    get_current_active_user, has_permission
)
from services.soft_delete_service import SoftDeleteService, build_active_filter

router = APIRouter(prefix="/customers", tags=["Customers"])


class CustomerImportItem(BaseModel):
    name: str
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


@router.post("", response_model=Customer)
async def create_customer(
    input: CustomerCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new customer and optionally send welcome email"""
    customer = Customer(**input.model_dump())
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


@router.post("/import", response_model=CustomerImportResponse)
async def import_customers(
    request: CustomerImportRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Bulk import customers from CSV data"""
    created = 0
    updated = 0
    errors = []
    
    for i, item in enumerate(request.customers):
        try:
            # Validate name
            if not item.name or not item.name.strip():
                errors.append(f"Row {i + 1}: Name is required")
                continue
            
            # Check for existing customer with same email (if email provided)
            existing = None
            if item.email and item.email.strip():
                existing = await db.customers.find_one({
                    "email": item.email.strip(),
                    "tenant_id": current_user.tenant_id
                })
            
            # Normalize status
            status = "lead"
            if item.status and item.status.lower() in ["lead", "active", "inactive"]:
                status = item.status.lower()
            
            if existing:
                # Update existing customer
                update_data = {
                    "name": item.name.strip(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                if item.company:
                    update_data["company"] = item.company.strip()
                if item.phone:
                    update_data["phone"] = item.phone.strip()
                if item.notes:
                    update_data["notes"] = item.notes.strip()
                update_data["status"] = status
                
                await db.customers.update_one(
                    {"id": existing["id"]},
                    {"$set": update_data}
                )
                updated += 1
            else:
                # Create new customer
                customer = Customer(
                    name=item.name.strip(),
                    company=item.company.strip() if item.company else None,
                    email=item.email.strip() if item.email else None,
                    phone=item.phone.strip() if item.phone else None,
                    status=status,
                    notes=item.notes.strip() if item.notes else None,
                    tenant_id=current_user.tenant_id
                )
                await db.customers.insert_one(customer.model_dump())
                created += 1
                
        except Exception as e:
            logger.error(f"Error importing customer row {i + 1}: {str(e)}")
            errors.append(f"Row {i + 1}: {str(e)}")
    
    return CustomerImportResponse(created=created, updated=updated, errors=errors)


@router.get("", response_model=List[Customer])
async def get_customers(
    status: Optional[CustomerStatus] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """List all customers with optional filtering. Excludes deleted by default."""
    query = build_active_filter(current_user.tenant_id, include_deleted)
    if status:
        query["status"] = status.value
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
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
        {"id": customer_id, "tenant_id": current_user.tenant_id, "deleted_at": None}, 
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: str, 
    input: CustomerUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a customer"""
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = await db.customers.update_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}, 
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    permanent: bool = False,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Soft delete a customer. Use permanent=true for hard delete (admin only)."""
    soft_delete_service = SoftDeleteService(db)
    
    if permanent:
        # Hard delete - admin only
        success = await soft_delete_service.hard_delete(
            collection_name="customers",
            record_id=customer_id,
            tenant_id=current_user.tenant_id,
            admin_confirmation=True
        )
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer permanently deleted"}
    else:
        # Soft delete
        success = await soft_delete_service.soft_delete(
            collection_name="customers",
            record_id=customer_id,
            deleted_by=current_user.id,
            tenant_id=current_user.tenant_id,
            reason="User requested deletion"
        )
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found or already deleted")
        return {"message": "Customer deleted (can be restored)"}


@router.post("/{customer_id}/restore")
async def restore_customer(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Restore a soft-deleted customer"""
    soft_delete_service = SoftDeleteService(db)
    
    success = await soft_delete_service.restore(
        collection_name="customers",
        record_id=customer_id,
        restored_by=current_user.id,
        tenant_id=current_user.tenant_id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found or not deleted")
    
    # Return the restored customer
    customer = await db.customers.find_one({"id": customer_id}, {"_id": 0})
    return {"message": "Customer restored", "customer": customer}


@router.get("/deleted/list")
async def get_deleted_customers(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get list of soft-deleted customers for admin review"""
    soft_delete_service = SoftDeleteService(db)
    
    deleted = await soft_delete_service.get_deleted_records(
        collection_name="customers",
        tenant_id=current_user.tenant_id,
        limit=100
    )
    
    return {"deleted_customers": deleted, "count": len(deleted)}


@router.get("/{customer_id}/summary")
async def get_customer_summary(
    customer_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a summary of customer activity (quotes, jobs, invoices)"""
    # Verify customer exists and belongs to tenant (exclude deleted)
    customer = await db.customers.find_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id, "deleted_at": None},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get counts (exclude deleted records)
    quote_count = await db.quotes.count_documents({
        "customer_id": customer_id, 
        "tenant_id": current_user.tenant_id,
        "deleted_at": None
    })
    job_count = await db.jobs.count_documents({
        "customer_id": customer_id, 
        "tenant_id": current_user.tenant_id,
        "deleted_at": None
    })
    invoice_count = await db.invoices.count_documents({
        "customer_id": customer_id, 
        "tenant_id": current_user.tenant_id,
        "deleted_at": None
    })
    
    # Get totals (exclude deleted invoices)
    invoices = await db.invoices.find(
        {"customer_id": customer_id, "tenant_id": current_user.tenant_id, "deleted_at": None},
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
