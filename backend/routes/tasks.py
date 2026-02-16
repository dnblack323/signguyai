"""
Tasks Routes

This module contains routes for task management:
- CRUD operations for tasks
- Task filtering by job, status, date
"""

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Get database directly
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/signguy")
DB_NAME = os.environ.get("DB_NAME", "signguy")

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    job_id: Optional[str] = None
    due_date: Optional[str] = None
    is_complete: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    job_id: Optional[str] = None
    due_date: Optional[str] = None
    is_complete: Optional[bool] = None


class Task(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: Optional[str] = None
    job_id: Optional[str] = None
    due_date: Optional[str] = None
    is_complete: bool = False
    created_at: str
    updated_at: str


@router.get("", response_model=List[Task])
async def get_tasks(
    job_id: Optional[str] = None,
    is_complete: Optional[bool] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all tasks for tenant with optional filters"""
    query = {"tenant_id": current_user.tenant_id}
    
    if job_id:
        query["job_id"] = job_id
    if is_complete is not None:
        query["is_complete"] = is_complete
    
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return tasks


@router.post("", response_model=Task)
async def create_task(
    data: TaskCreate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a new task"""
    now = datetime.now(timezone.utc).isoformat()
    
    task = {
        "id": str(uuid.uuid4()),
        "tenant_id": current_user.tenant_id,
        "title": data.title,
        "description": data.description,
        "job_id": data.job_id,
        "due_date": data.due_date,
        "is_complete": data.is_complete,
        "created_at": now,
        "updated_at": now
    }
    
    await db.tasks.insert_one(task)
    task.pop("_id", None)
    return task


@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a single task"""
    task = await db.tasks.find_one(
        {"id": task_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task)
async def update_task(
    task_id: str,
    data: TaskUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a task"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.tasks.update_one(
        {"id": task_id, "tenant_id": current_user.tenant_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a task"""
    result = await db.tasks.delete_one(
        {"id": task_id, "tenant_id": current_user.tenant_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {"message": "Task deleted"}
