"""
Artwork Approvals Routes

This module contains routes for the shop-side artwork approval system:
- Create and manage artwork proofs
- Dashboard stats
- Send proofs to customer portal
- Track approval status
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid
import base64

from server import db, get_current_active_user
from models import UserInDB, ArtworkProof, ProofStatus


router = APIRouter(prefix="/approvals", tags=["Artwork Approvals"])


class ApprovalStats(BaseModel):
    total: int
    pending: int
    approved: int
    revisions: int


class ProofCreate(BaseModel):
    job_id: str
    customer_id: str
    file_url: str
    file_name: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    watermarked_url: Optional[str] = None  # URL with watermark applied


class ProofUpdate(BaseModel):
    description: Optional[str] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    watermarked_url: Optional[str] = None


class ProofResponse(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    job_id: str
    customer_id: str
    customer_name: Optional[str] = None
    job_name: Optional[str] = None
    version: int
    file_url: str
    file_name: str
    thumbnail_url: Optional[str] = None
    watermarked_url: Optional[str] = None
    description: Optional[str] = None
    status: str
    customer_comment: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    created_at: str


async def _get_proof_parent_name(tenant_id: str, parent_id: str):
    job = await db.jobs.find_one({"id": parent_id, "tenant_id": tenant_id}, {"_id": 0, "name": 1})
    if job:
        return job.get("name"), job
    order = await db.orders.find_one({"id": parent_id, "tenant_id": tenant_id}, {"_id": 0, "order_number": 1})
    if order:
        return order.get("order_number") or "Order", order
    return "Unknown", None


@router.get("/stats", response_model=ApprovalStats)
async def get_approval_stats(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get approval statistics for the dashboard"""
    tenant_id = current_user.tenant_id
    
    total = await db.artwork_proofs.count_documents({"tenant_id": tenant_id})
    pending = await db.artwork_proofs.count_documents({"tenant_id": tenant_id, "status": "pending"})
    approved = await db.artwork_proofs.count_documents({"tenant_id": tenant_id, "status": "approved"})
    revisions = await db.artwork_proofs.count_documents({"tenant_id": tenant_id, "status": "revision_requested"})
    
    return ApprovalStats(
        total=total,
        pending=pending,
        approved=approved,
        revisions=revisions
    )


@router.get("", response_model=List[ProofResponse])
async def get_approvals(
    status: Optional[str] = None,
    customer_id: Optional[str] = None,
    job_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all artwork proofs with optional filters"""
    query = {"tenant_id": current_user.tenant_id}
    
    if status:
        query["status"] = status
    if customer_id:
        query["customer_id"] = customer_id
    if job_id:
        query["job_id"] = job_id
    
    proofs = await db.artwork_proofs.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with customer and job names
    enriched = []
    for proof in proofs:
        customer = await db.customers.find_one(
            {"id": proof.get("customer_id"), "tenant_id": current_user.tenant_id},
            {"_id": 0, "name": 1}
        )
        job_name, _parent = await _get_proof_parent_name(current_user.tenant_id, proof.get("job_id"))
        
        proof["customer_name"] = customer.get("name") if customer else "Unknown"
        proof["job_name"] = job_name
        enriched.append(proof)
    
    return enriched


@router.get("/{proof_id}", response_model=ProofResponse)
async def get_approval(
    proof_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific artwork proof"""
    proof = await db.artwork_proofs.find_one(
        {"id": proof_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    # Enrich with names
    customer = await db.customers.find_one(
        {"id": proof.get("customer_id"), "tenant_id": current_user.tenant_id},
        {"_id": 0, "name": 1}
    )
    job_name, _parent = await _get_proof_parent_name(current_user.tenant_id, proof.get("job_id"))
    
    proof["customer_name"] = customer.get("name") if customer else "Unknown"
    proof["job_name"] = job_name
    
    return proof


@router.post("", response_model=ProofResponse)
async def create_approval(
    input: ProofCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new artwork proof and send to customer portal"""
    tenant_id = current_user.tenant_id
    
    # Verify customer belongs to tenant
    customer = await db.customers.find_one(
        {"id": input.customer_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify job belongs to tenant
    job = await db.jobs.find_one({"id": input.job_id, "tenant_id": tenant_id}, {"_id": 0})
    order = None
    if not job:
        order = await db.orders.find_one({"id": input.job_id, "tenant_id": tenant_id}, {"_id": 0})
    if not job and not order:
        raise HTTPException(status_code=404, detail="Job or order not found")
    
    # Get latest version for this job
    latest = await db.artwork_proofs.find_one(
        {"job_id": input.job_id, "tenant_id": tenant_id},
        {"_id": 0},
        sort=[("version", -1)]
    )
    version = (latest["version"] + 1) if latest else 1
    
    proof = ArtworkProof(
        tenant_id=tenant_id,
        job_id=input.job_id,
        customer_id=input.customer_id,
        version=version,
        file_url=input.watermarked_url or input.file_url,  # Use watermarked if provided
        file_name=input.file_name,
        thumbnail_url=input.thumbnail_url,
        description=input.description,
        status=ProofStatus.PENDING
    )
    
    await db.artwork_proofs.insert_one(proof.model_dump())
    
    # Create notification for customer
    notification = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "customer_id": input.customer_id,
        "notification_type": "proof_ready",
        "title": "New Artwork Ready for Review",
        "message": f"A new proof (Version {version}) is ready for your review for job: {(job or order or {}).get('name') or (order or {}).get('order_number') or 'Unknown'}",
        "link": f"/customer-portal/proofs/{proof.id}",
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.customer_notifications.insert_one(notification)
    
    # Return enriched response
    result = proof.model_dump()
    result["customer_name"] = customer.get("name")
    result["job_name"] = (job or order or {}).get("name") or (order or {}).get("order_number") or "Unknown"
    
    return result


@router.put("/{proof_id}", response_model=ProofResponse)
async def update_approval(
    proof_id: str,
    input: ProofUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update an artwork proof"""
    proof = await db.artwork_proofs.find_one(
        {"id": proof_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    update_data = {k: v for k, v in input.model_dump().items() if v is not None}
    
    if update_data:
        await db.artwork_proofs.update_one(
            {"id": proof_id, "tenant_id": current_user.tenant_id},
            {"$set": update_data}
        )
    
    updated = await db.artwork_proofs.find_one(
        {"id": proof_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    # Enrich with names
    customer = await db.customers.find_one(
        {"id": updated.get("customer_id"), "tenant_id": current_user.tenant_id},
        {"_id": 0, "name": 1}
    )
    job_name, _parent = await _get_proof_parent_name(current_user.tenant_id, updated.get("job_id"))
    
    updated["customer_name"] = customer.get("name") if customer else "Unknown"
    updated["job_name"] = job_name
    
    return updated


@router.delete("/{proof_id}")
async def delete_approval(
    proof_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete an artwork proof"""
    result = await db.artwork_proofs.delete_one(
        {"id": proof_id, "tenant_id": current_user.tenant_id}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    return {"message": "Proof deleted"}


@router.post("/{proof_id}/resend")
async def resend_approval_notification(
    proof_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Resend notification to customer about this proof"""
    proof = await db.artwork_proofs.find_one(
        {"id": proof_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    
    job_name, _parent = await _get_proof_parent_name(current_user.tenant_id, proof.get("job_id"))
    
    # Create new notification
    notification = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "customer_id": proof["customer_id"],
        "notification_type": "proof_reminder",
        "title": "Reminder: Artwork Awaiting Your Review",
        "message": f"Please review proof (Version {proof['version']}) for job: {job_name}",
        "link": f"/customer-portal/proofs/{proof_id}",
        "is_read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.customer_notifications.insert_one(notification)
    
    return {"message": "Notification sent"}


@router.get("/customers/list")
async def get_customers_for_approval(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get list of customers for the approval dropdown"""
    customers = await db.customers.find(
        {"tenant_id": current_user.tenant_id},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    ).sort("name", 1).to_list(500)
    return customers


@router.get("/jobs/list")
async def get_jobs_for_approval(
    customer_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get list of active jobs for the approval dropdown"""
    query = {
        "tenant_id": current_user.tenant_id,
        "status": {"$nin": ["complete", "delivered", "cancelled", "archived"]}
    }
    if customer_id:
        query["customer_id"] = customer_id
    
    jobs = await db.jobs.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "customer_id": 1}
    ).sort("created_at", -1).to_list(500)
    return jobs
