"""
Dashboard Routes

This module contains routes for the main dashboard:
- Dashboard stats (customers, jobs, invoices, revenue)
- Pending approvals (proofs awaiting customer approval)
- Unread messages
- Clocked-in employees
- Today's schedule (jobs due today)
"""

from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel

from server import db, get_current_active_user
from models import UserInDB


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardStats(BaseModel):
    total_customers: int = 0
    active_jobs: int = 0
    pending_invoices: int = 0
    today_revenue: float = 0
    overdue_count: int = 0
    overdue_total: float = 0


class PendingApproval(BaseModel):
    id: str
    job_id: str
    job_name: str
    customer_name: str
    created_at: str
    status: str


class UnreadMessage(BaseModel):
    conversation_id: str
    customer_id: str
    customer_name: str
    last_message: str
    last_message_at: str
    unread_count: int


class ClockedInEmployee(BaseModel):
    employee_id: str
    employee_name: str
    clocked_in_at: str
    status: str  # working, on_break


class ScheduleItem(BaseModel):
    id: str
    name: str
    customer_name: str
    due_date: str
    status: str
    priority: str = "normal"


class OnboardingStatus(BaseModel):
    """Status of onboarding checklist items"""
    has_company_info: bool = False
    has_pricing_config: bool = False
    has_email_templates: bool = False
    has_customers: bool = False
    has_imported_customers: bool = False
    has_employees: bool = False
    has_quotes: bool = False
    has_webstores: bool = False
    has_documents: bool = False
    has_used_ai: bool = False


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: UserInDB = Depends(get_current_active_user)):
    """Get main dashboard statistics"""
    tenant_id = current_user.tenant_id
    
    # Count customers
    total_customers = await db.customers.count_documents({"tenant_id": tenant_id})
    
    # Count active jobs (not complete/delivered/cancelled)
    active_jobs = await db.jobs.count_documents({
        "tenant_id": tenant_id,
        "status": {"$nin": ["complete", "delivered", "cancelled"]}
    })
    
    # Count pending invoices (sent but not paid)
    pending_invoices = await db.invoices.count_documents({
        "tenant_id": tenant_id,
        "status": {"$in": ["sent", "draft"]}
    })
    
    # Calculate today's revenue (paid invoices today)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_invoices = await db.invoices.find({
        "tenant_id": tenant_id,
        "status": "paid",
        "paid_date": {"$gte": today_start.isoformat()}
    }, {"_id": 0, "total": 1}).to_list(1000)
    today_revenue = sum(inv.get("total", 0) for inv in today_invoices)
    
    # Count overdue invoices
    overdue_invoices = await db.invoices.find({
        "tenant_id": tenant_id,
        "status": "overdue"
    }, {"_id": 0, "total": 1}).to_list(1000)
    overdue_count = len(overdue_invoices)
    overdue_total = sum(inv.get("total", 0) for inv in overdue_invoices)
    
    return DashboardStats(
        total_customers=total_customers,
        active_jobs=active_jobs,
        pending_invoices=pending_invoices,
        today_revenue=today_revenue,
        overdue_count=overdue_count,
        overdue_total=overdue_total
    )


@router.get("/pending-approvals", response_model=List[PendingApproval])
async def get_pending_approvals(current_user: UserInDB = Depends(get_current_active_user)):
    """Get proofs awaiting customer approval"""
    tenant_id = current_user.tenant_id
    
    # Find proofs with pending status
    pending_proofs = await db.artwork_proofs.find({
        "tenant_id": tenant_id,
        "status": "pending"
    }, {"_id": 0}).sort("created_at", -1).to_list(20)
    
    approvals = []
    for proof in pending_proofs:
        # Get job info (tenant-filtered for extra safety)
        job = await db.jobs.find_one(
            {"id": proof.get("job_id"), "tenant_id": tenant_id}, 
            {"_id": 0, "name": 1, "customer_id": 1}
        )
        if not job:
            continue
            
        # Get customer name (tenant-filtered for extra safety)
        customer = await db.customers.find_one(
            {"id": job.get("customer_id"), "tenant_id": tenant_id}, 
            {"_id": 0, "name": 1}
        )
        customer_name = customer.get("name", "Unknown") if customer else "Unknown"
        
        approvals.append(PendingApproval(
            id=proof.get("id", ""),
            job_id=proof.get("job_id", ""),
            job_name=job.get("name", "Unknown Job"),
            customer_name=customer_name,
            created_at=proof.get("created_at", ""),
            status=proof.get("status", "pending")
        ))
    
    return approvals


@router.get("/unread-messages", response_model=List[UnreadMessage])
async def get_unread_messages(current_user: UserInDB = Depends(get_current_active_user)):
    """Get conversations with unread messages from customers"""
    tenant_id = current_user.tenant_id
    
    # Find conversations with unread messages (messages from customer not read by shop)
    conversations = await db.conversations.find({
        "tenant_id": tenant_id,
        "shop_unread_count": {"$gt": 0}
    }, {"_id": 0}).sort("last_message_at", -1).to_list(10)
    
    messages = []
    for conv in conversations:
        # Get customer name (tenant-filtered for extra safety)
        customer = await db.customers.find_one(
            {"id": conv.get("customer_id"), "tenant_id": tenant_id}, 
            {"_id": 0, "name": 1}
        )
        customer_name = customer.get("name", "Unknown") if customer else "Unknown"
        
        messages.append(UnreadMessage(
            conversation_id=conv.get("id", ""),
            customer_id=conv.get("customer_id", ""),
            customer_name=customer_name,
            last_message=conv.get("last_message", "")[:100],  # Truncate
            last_message_at=conv.get("last_message_at", ""),
            unread_count=conv.get("shop_unread_count", 0)
        ))
    
    return messages


@router.get("/clocked-in", response_model=List[ClockedInEmployee])
async def get_clocked_in_employees(current_user: UserInDB = Depends(get_current_active_user)):
    """Get employees currently clocked in"""
    today = datetime.now(timezone.utc).date().isoformat()
    tenant_id = current_user.tenant_id
    
    # Get all employees FOR THIS TENANT ONLY
    employees = await db.employees.find({
        "is_active": True,
        "tenant_id": tenant_id
    }, {"_id": 0}).to_list(100)
    
    clocked_in = []
    for emp in employees:
        # Get today's logs for this employee
        logs = await db.timelogs.find({
            "employee_id": emp.get("id"),
            "timestamp": {"$regex": f"^{today}"}
        }, {"_id": 0}).sort("timestamp", -1).to_list(1)
        
        if logs:
            last_log = logs[0]
            action = last_log.get("action")
            
            # If last action is start_work or break_end, they're working
            # If last action is break_start, they're on break
            if action in ["start_work", "break_end"]:
                # Find when they clocked in
                start_log = await db.timelogs.find_one({
                    "employee_id": emp.get("id"),
                    "timestamp": {"$regex": f"^{today}"},
                    "action": "start_work"
                }, {"_id": 0}, sort=[("timestamp", 1)])
                
                clocked_in.append(ClockedInEmployee(
                    employee_id=emp.get("id", ""),
                    employee_name=emp.get("name", "Unknown"),
                    clocked_in_at=start_log.get("timestamp", "") if start_log else "",
                    status="working"
                ))
            elif action == "break_start":
                start_log = await db.timelogs.find_one({
                    "employee_id": emp.get("id"),
                    "timestamp": {"$regex": f"^{today}"},
                    "action": "start_work"
                }, {"_id": 0}, sort=[("timestamp", 1)])
                
                clocked_in.append(ClockedInEmployee(
                    employee_id=emp.get("id", ""),
                    employee_name=emp.get("name", "Unknown"),
                    clocked_in_at=start_log.get("timestamp", "") if start_log else "",
                    status="on_break"
                ))
    
    return clocked_in


@router.get("/todays-schedule", response_model=List[ScheduleItem])
async def get_todays_schedule(current_user: UserInDB = Depends(get_current_active_user)):
    """Get jobs due today or overdue"""
    tenant_id = current_user.tenant_id
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Find jobs due today or before (and not complete)
    jobs = await db.jobs.find({
        "tenant_id": tenant_id,
        "due_date": {"$lte": today},
        "status": {"$nin": ["complete", "delivered", "cancelled"]}
    }, {"_id": 0}).sort("due_date", 1).to_list(20)
    
    schedule = []
    for job in jobs:
        # Get customer name (tenant-filtered for extra safety)
        customer = await db.customers.find_one(
            {"id": job.get("customer_id"), "tenant_id": tenant_id}, 
            {"_id": 0, "name": 1}
        )
        customer_name = customer.get("name", "Unknown") if customer else "Unknown"
        
        # Determine priority based on due date
        due_date = job.get("due_date", "")
        priority = "normal"
        if due_date < today:
            priority = "overdue"
        elif due_date == today:
            priority = "urgent"
        
        schedule.append(ScheduleItem(
            id=job.get("id", ""),
            name=job.get("name", "Unknown Job"),
            customer_name=customer_name,
            due_date=due_date,
            status=job.get("status", ""),
            priority=priority
        ))
    
    return schedule
