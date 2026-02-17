"""
Job Time Tracking Routes

This module contains routes for tracking time spent on jobs by employees.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from server import db, get_current_active_user
from models import UserInDB
from models.jobs import JobTimeEntry, JobTimeEntryCreate, JobTimeEntryUpdate, JobTimeSummary

router = APIRouter(prefix="/jobs", tags=["Job Time Tracking"])


# ============== HELPER FUNCTIONS ==============

async def get_employee_by_id(employee_id: str, tenant_id: str):
    """Get employee data"""
    employee = await db.employees.find_one(
        {"id": employee_id, "tenant_id": tenant_id},
        {"_id": 0}
    )
    return employee


async def calculate_entry_duration(entry: dict) -> dict:
    """Calculate duration and labor cost for a time entry"""
    if entry.get('end_time'):
        start = datetime.fromisoformat(entry['start_time'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(entry['end_time'].replace('Z', '+00:00'))
        duration = (end - start).total_seconds() / 60  # in minutes
        entry['duration_minutes'] = round(duration, 2)
        entry['is_active'] = False
        
        # Calculate labor cost
        hourly_rate = entry.get('hourly_rate', 0)
        entry['labor_cost'] = round((duration / 60) * hourly_rate, 2)
    else:
        # Still active - calculate running duration
        start = datetime.fromisoformat(entry['start_time'].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        duration = (now - start).total_seconds() / 60
        entry['duration_minutes'] = round(duration, 2)
        entry['is_active'] = True
        entry['labor_cost'] = 0  # Not calculated until stopped
    
    return entry


# ============== ROUTES ==============

@router.post("/{job_id}/time/start", response_model=JobTimeEntry)
async def start_job_timer(
    job_id: str,
    entry_data: JobTimeEntryCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Start tracking time on a job"""
    # Verify job exists
    job = await db.jobs.find_one({"id": job_id, "tenant_id": current_user.tenant_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user is owner or get employee info
    employee_id = current_user.id
    employee_name = current_user.full_name
    hourly_rate = 0
    
    # Check if there's an employee record
    employee = await db.employees.find_one(
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if employee:
        employee_id = employee.get('id', current_user.id)
        employee_name = employee.get('name', current_user.full_name)
        hourly_rate = employee.get('hourly_rate', 0)
    
    # Check for existing active timer on this job
    active_entry = await db.job_time_entries.find_one({
        "job_id": job_id,
        "employee_id": employee_id,
        "is_active": True,
        "tenant_id": current_user.tenant_id
    })
    if active_entry:
        raise HTTPException(
            status_code=400, 
            detail="You already have an active timer on this job. Stop it first."
        )
    
    # Create new time entry
    entry = JobTimeEntry(
        job_id=job_id,
        employee_id=employee_id,
        employee_name=employee_name,
        tenant_id=current_user.tenant_id,
        description=entry_data.description,
        task_type=entry_data.task_type or "production",
        hourly_rate=hourly_rate,
        is_active=True
    )
    
    await db.job_time_entries.insert_one(entry.model_dump())
    
    return entry


@router.post("/{job_id}/time/stop", response_model=JobTimeEntry)
async def stop_job_timer(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Stop the active timer on a job"""
    # Get employee ID
    employee_id = current_user.id
    employee = await db.employees.find_one(
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if employee:
        employee_id = employee.get('id', current_user.id)
    
    # Find active entry
    active_entry = await db.job_time_entries.find_one({
        "job_id": job_id,
        "employee_id": employee_id,
        "is_active": True,
        "tenant_id": current_user.tenant_id
    })
    
    if not active_entry:
        raise HTTPException(status_code=404, detail="No active timer found on this job")
    
    # Update with end time
    end_time = datetime.now(timezone.utc).isoformat()
    
    await db.job_time_entries.update_one(
        {"id": active_entry['id']},
        {"$set": {"end_time": end_time, "is_active": False}}
    )
    
    # Get updated entry and calculate duration
    updated = await db.job_time_entries.find_one({"id": active_entry['id']}, {"_id": 0})
    updated = await calculate_entry_duration(updated)
    
    # Update the calculated fields
    await db.job_time_entries.update_one(
        {"id": active_entry['id']},
        {"$set": {
            "duration_minutes": updated['duration_minutes'],
            "labor_cost": updated['labor_cost'],
            "is_active": False
        }}
    )
    
    return JobTimeEntry(**updated)


@router.get("/{job_id}/time", response_model=List[JobTimeEntry])
async def get_job_time_entries(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all time entries for a job"""
    entries = await db.job_time_entries.find(
        {"job_id": job_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).sort("start_time", -1).to_list(1000)
    
    # Calculate durations for active entries
    for i, entry in enumerate(entries):
        entries[i] = await calculate_entry_duration(entry)
    
    return entries


@router.get("/{job_id}/time/summary", response_model=JobTimeSummary)
async def get_job_time_summary(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get summary of time spent on a job"""
    entries = await db.job_time_entries.find(
        {"job_id": job_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).to_list(1000)
    
    total_minutes = 0
    total_labor_cost = 0
    by_employee = {}
    by_task_type = {}
    
    for entry in entries:
        entry = await calculate_entry_duration(entry)
        minutes = entry.get('duration_minutes', 0)
        cost = entry.get('labor_cost', 0)
        
        total_minutes += minutes
        total_labor_cost += cost
        
        # Group by employee
        emp_name = entry.get('employee_name', 'Unknown')
        emp_id = entry.get('employee_id')
        if emp_id not in by_employee:
            by_employee[emp_id] = {
                "name": emp_name,
                "minutes": 0,
                "hours": 0,
                "labor_cost": 0,
                "entries": 0
            }
        by_employee[emp_id]['minutes'] += minutes
        by_employee[emp_id]['hours'] = round(by_employee[emp_id]['minutes'] / 60, 2)
        by_employee[emp_id]['labor_cost'] += cost
        by_employee[emp_id]['entries'] += 1
        
        # Group by task type
        task_type = entry.get('task_type', 'other')
        if task_type not in by_task_type:
            by_task_type[task_type] = {
                "minutes": 0,
                "hours": 0,
                "labor_cost": 0,
                "entries": 0
            }
        by_task_type[task_type]['minutes'] += minutes
        by_task_type[task_type]['hours'] = round(by_task_type[task_type]['minutes'] / 60, 2)
        by_task_type[task_type]['labor_cost'] += cost
        by_task_type[task_type]['entries'] += 1
    
    return JobTimeSummary(
        job_id=job_id,
        total_minutes=round(total_minutes, 2),
        total_hours=round(total_minutes / 60, 2),
        total_labor_cost=round(total_labor_cost, 2),
        entries_count=len(entries),
        by_employee=by_employee,
        by_task_type=by_task_type
    )


@router.get("/{job_id}/time/active")
async def get_active_timer(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Check if user has an active timer on this job"""
    employee_id = current_user.id
    employee = await db.employees.find_one(
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if employee:
        employee_id = employee.get('id', current_user.id)
    
    active_entry = await db.job_time_entries.find_one({
        "job_id": job_id,
        "employee_id": employee_id,
        "is_active": True,
        "tenant_id": current_user.tenant_id
    }, {"_id": 0})
    
    if active_entry:
        active_entry = await calculate_entry_duration(active_entry)
        return {"has_active_timer": True, "entry": active_entry}
    
    return {"has_active_timer": False, "entry": None}


@router.delete("/{job_id}/time/{entry_id}")
async def delete_time_entry(
    job_id: str,
    entry_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a time entry (admin only or own entry)"""
    entry = await db.job_time_entries.find_one({
        "id": entry_id,
        "job_id": job_id,
        "tenant_id": current_user.tenant_id
    })
    
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    # Check permission - must be owner or the employee who created it
    employee_id = current_user.id
    employee = await db.employees.find_one(
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if employee:
        employee_id = employee.get('id', current_user.id)
    
    if entry['employee_id'] != employee_id and current_user.role != 'owner':
        raise HTTPException(status_code=403, detail="You can only delete your own time entries")
    
    await db.job_time_entries.delete_one({"id": entry_id})
    
    return {"message": "Time entry deleted"}


@router.put("/{job_id}/time/{entry_id}", response_model=JobTimeEntry)
async def update_time_entry(
    job_id: str,
    entry_id: str,
    update_data: JobTimeEntryUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a time entry"""
    entry = await db.job_time_entries.find_one({
        "id": entry_id,
        "job_id": job_id,
        "tenant_id": current_user.tenant_id
    })
    
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await db.job_time_entries.update_one(
            {"id": entry_id},
            {"$set": update_dict}
        )
    
    # Get updated entry
    updated = await db.job_time_entries.find_one({"id": entry_id}, {"_id": 0})
    updated = await calculate_entry_duration(updated)
    
    # Update calculated fields if end_time was set
    if update_data.end_time:
        await db.job_time_entries.update_one(
            {"id": entry_id},
            {"$set": {
                "duration_minutes": updated['duration_minutes'],
                "labor_cost": updated['labor_cost'],
                "is_active": False
            }}
        )
    
    return JobTimeEntry(**updated)


# ============== MY ACTIVE TIMERS ==============

@router.get("/time/my-active", response_model=List[dict])
async def get_my_active_timers(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all active timers for current user across all jobs"""
    employee_id = current_user.id
    employee = await db.employees.find_one(
        {"user_id": current_user.id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if employee:
        employee_id = employee.get('id', current_user.id)
    
    active_entries = await db.job_time_entries.find({
        "employee_id": employee_id,
        "is_active": True,
        "tenant_id": current_user.tenant_id
    }, {"_id": 0}).to_list(100)
    
    # Enhance with job info and calculate durations
    result = []
    for entry in active_entries:
        entry = await calculate_entry_duration(entry)
        job = await db.jobs.find_one({"id": entry['job_id']}, {"_id": 0, "name": 1, "id": 1})
        if job:
            entry['job_name'] = job.get('name', 'Unknown Job')
        result.append(entry)
    
    return result
