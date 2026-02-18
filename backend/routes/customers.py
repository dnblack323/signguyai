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

from models import (
    Customer, CustomerCreate, CustomerUpdate, CustomerStatus,
    UserInDB, Permission
)

# Import from server module (will be refactored later)
from server import (
    db, logger,
    get_current_active_user, has_permission
)

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
    """Create a new customer"""
    customer = Customer(**input.model_dump())
    customer.tenant_id = current_user.tenant_id
    doc = customer.model_dump()
    await db.customers.insert_one(doc)
    return customer


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
        {"id": customer_id, "tenant_id": current_user.tenant_id}, 
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
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a customer"""
    result = await db.customers.delete_one(
        {"id": customer_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
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
