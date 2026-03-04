"""
Production Timeline Routes

API endpoints for managing production timelines at the line-item level.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from server import db, get_current_active_user, logger
from models import UserInDB
from models.production_timeline import (
    ProductionTimeline, TimelineStageEntry, TimelineStageUpdate,
    WorkflowTemplate, WorkflowStage, TimelineAnalytics,
    DEFAULT_WORKFLOW_TEMPLATES, ProductionCategory
)


router = APIRouter(prefix="/production-timeline", tags=["Production Timeline"])


# ============== WORKFLOW TEMPLATES ==============

@router.get("/templates")
async def get_workflow_templates(
    category: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get all workflow templates for the tenant.
    If no custom templates exist, returns default templates.
    """
    tenant_id = current_user.tenant_id
    query = {"tenant_id": tenant_id}
    
    if category:
        query["category"] = category
    
    # Get custom templates
    custom_templates = await db.workflow_templates.find(
        query, {"_id": 0}
    ).to_list(100)
    
    # If no custom templates, return defaults
    if not custom_templates:
        defaults = []
        for cat, template in DEFAULT_WORKFLOW_TEMPLATES.items():
            if category and cat != category:
                continue
            defaults.append({
                "id": f"default_{cat}",
                "tenant_id": tenant_id,
                "category": cat,
                "name": template["name"],
                "stages": [WorkflowStage(**s).model_dump() for s in template["stages"]],
                "is_default": True
            })
        return defaults
    
    return custom_templates


@router.get("/templates/{template_id}")
async def get_workflow_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get a specific workflow template"""
    # Check for default templates
    if template_id.startswith("default_"):
        category = template_id.replace("default_", "")
        if category in DEFAULT_WORKFLOW_TEMPLATES:
            template = DEFAULT_WORKFLOW_TEMPLATES[category]
            return {
                "id": template_id,
                "tenant_id": current_user.tenant_id,
                "category": category,
                "name": template["name"],
                "stages": [WorkflowStage(**s).model_dump() for s in template["stages"]],
                "is_default": True
            }
    
    # Get custom template
    template = await db.workflow_templates.find_one(
        {"id": template_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.post("/templates")
async def create_workflow_template(
    name: str,
    category: str,
    stages: List[dict],
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Create a custom workflow template"""
    tenant_id = current_user.tenant_id
    
    # Validate stages
    validated_stages = []
    for i, stage in enumerate(stages):
        validated_stages.append(WorkflowStage(
            name=stage.get("name", f"Stage {i+1}"),
            order=stage.get("order", i + 1),
            auto_trigger=stage.get("auto_trigger"),
            is_final=stage.get("is_final", False),
            description=stage.get("description"),
            estimated_duration_minutes=stage.get("estimated_duration_minutes")
        ).model_dump())
    
    template = WorkflowTemplate(
        tenant_id=tenant_id,
        category=category,
        name=name,
        stages=validated_stages,
        is_default=False
    )
    
    await db.workflow_templates.insert_one(template.model_dump())
    logger.info(f"Created workflow template {template.id} for tenant {tenant_id}")
    
    return template.model_dump()


@router.put("/templates/{template_id}")
async def update_workflow_template(
    template_id: str,
    name: Optional[str] = None,
    stages: Optional[List[dict]] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a custom workflow template"""
    tenant_id = current_user.tenant_id
    
    # Can't edit default templates directly - create a copy
    if template_id.startswith("default_"):
        raise HTTPException(
            status_code=400, 
            detail="Cannot edit default templates. Create a custom template instead."
        )
    
    template = await db.workflow_templates.find_one(
        {"id": template_id, "tenant_id": tenant_id}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if name:
        update_data["name"] = name
    
    if stages:
        validated_stages = []
        for i, stage in enumerate(stages):
            validated_stages.append(WorkflowStage(
                name=stage.get("name", f"Stage {i+1}"),
                order=stage.get("order", i + 1),
                auto_trigger=stage.get("auto_trigger"),
                is_final=stage.get("is_final", False),
                description=stage.get("description"),
                estimated_duration_minutes=stage.get("estimated_duration_minutes")
            ).model_dump())
        update_data["stages"] = validated_stages
    
    await db.workflow_templates.update_one(
        {"id": template_id},
        {"$set": update_data}
    )
    
    return {"message": "Template updated"}


@router.delete("/templates/{template_id}")
async def delete_workflow_template(
    template_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Delete a custom workflow template"""
    if template_id.startswith("default_"):
        raise HTTPException(status_code=400, detail="Cannot delete default templates")
    
    result = await db.workflow_templates.delete_one(
        {"id": template_id, "tenant_id": current_user.tenant_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"message": "Template deleted"}


# ============== PRODUCTION TIMELINES ==============

@router.get("/job/{job_id}")
async def get_job_timelines(
    job_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get all production timelines for a job"""
    timelines = await db.production_timelines.find(
        {"job_id": job_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    ).to_list(100)
    
    return timelines


@router.get("/line-item/{line_item_id}")
async def get_line_item_timeline(
    line_item_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get production timeline for a specific line item"""
    timeline = await db.production_timelines.find_one(
        {"line_item_id": line_item_id, "tenant_id": current_user.tenant_id},
        {"_id": 0}
    )
    
    if not timeline:
        return None
    
    return timeline


@router.post("/enable")
async def enable_timeline_for_line_item(
    job_id: str,
    line_item_id: str,
    category: str,
    template_id: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Enable production timeline tracking for a line item.
    Creates the timeline with stages based on the selected template/category.
    """
    tenant_id = current_user.tenant_id
    
    # Check if timeline already exists
    existing = await db.production_timelines.find_one(
        {"line_item_id": line_item_id, "tenant_id": tenant_id}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Timeline already exists for this line item")
    
    # Get template stages
    stages_data = []
    if template_id and not template_id.startswith("default_"):
        # Custom template
        template = await db.workflow_templates.find_one(
            {"id": template_id, "tenant_id": tenant_id},
            {"_id": 0}
        )
        if template:
            stages_data = template.get("stages", [])
    
    if not stages_data:
        # Use default template for category
        if category in DEFAULT_WORKFLOW_TEMPLATES:
            stages_data = DEFAULT_WORKFLOW_TEMPLATES[category]["stages"]
        else:
            # Fallback to printed_signs if category not found
            stages_data = DEFAULT_WORKFLOW_TEMPLATES[ProductionCategory.PRINTED_SIGNS.value]["stages"]
    
    # Create timeline stages
    stages = []
    now = datetime.now(timezone.utc).isoformat()
    for stage_data in stages_data:
        stage = TimelineStageEntry(
            stage_name=stage_data.get("name", stage_data.get("stage_name", "Unknown")),
            stage_order=stage_data.get("order", stage_data.get("stage_order", len(stages) + 1)),
            status="pending"
        )
        # Auto-start first stage
        if stage.stage_order == 1:
            stage.status = "completed"
            stage.started_at = now
            stage.completed_at = now
        stages.append(stage.model_dump())
    
    # Create timeline
    timeline = ProductionTimeline(
        tenant_id=tenant_id,
        job_id=job_id,
        line_item_id=line_item_id,
        workflow_template_id=template_id,
        category=category,
        enabled=True,
        current_stage_order=2 if len(stages) > 1 else 1,  # Move past "Job Created"
        stages=stages,
        started_at=now
    )
    
    await db.production_timelines.insert_one(timeline.model_dump())
    
    # Update line item to mark timeline as enabled
    await db.job_items.update_one(
        {"id": line_item_id},
        {"$set": {"timeline_enabled": True, "timeline_id": timeline.id}}
    )
    
    logger.info(f"Enabled production timeline {timeline.id} for line item {line_item_id}")
    
    return timeline.model_dump()


@router.delete("/line-item/{line_item_id}")
async def disable_timeline_for_line_item(
    line_item_id: str,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Disable (delete) production timeline for a line item"""
    tenant_id = current_user.tenant_id
    
    result = await db.production_timelines.delete_one(
        {"line_item_id": line_item_id, "tenant_id": tenant_id}
    )
    
    # Update line item
    await db.job_items.update_one(
        {"id": line_item_id},
        {"$set": {"timeline_enabled": False}, "$unset": {"timeline_id": ""}}
    )
    
    return {"message": "Timeline disabled", "deleted": result.deleted_count > 0}


@router.post("/{timeline_id}/advance")
async def advance_timeline_stage(
    timeline_id: str,
    notes: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Advance timeline to the next stage"""
    tenant_id = current_user.tenant_id
    
    timeline = await db.production_timelines.find_one(
        {"id": timeline_id, "tenant_id": tenant_id}
    )
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    stages = timeline.get("stages", [])
    current_order = timeline.get("current_stage_order", 1)
    now = datetime.now(timezone.utc).isoformat()
    
    # Find and complete current stage
    for stage in stages:
        if stage["stage_order"] == current_order:
            if stage["status"] == "pending":
                stage["status"] = "in_progress"
                stage["started_at"] = now
            stage["status"] = "completed"
            stage["completed_at"] = now
            if stage.get("started_at"):
                # Calculate duration
                start = datetime.fromisoformat(stage["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(now.replace("Z", "+00:00"))
                stage["duration_minutes"] = int((end - start).total_seconds() / 60)
            if notes:
                stage["notes"] = notes
            stage["assigned_user_id"] = current_user.id
            stage["assigned_user_name"] = current_user.full_name or current_user.email
            break
    
    # Find and start next stage
    next_order = current_order + 1
    is_completed = True
    for stage in stages:
        if stage["stage_order"] == next_order:
            stage["status"] = "in_progress"
            stage["started_at"] = now
            is_completed = False
            break
    
    # Update timeline
    update_data = {
        "stages": stages,
        "current_stage_order": next_order,
        "updated_at": now
    }
    
    if is_completed or next_order > len(stages):
        update_data["completed_at"] = now
        # Calculate total duration
        if timeline.get("started_at"):
            start = datetime.fromisoformat(timeline["started_at"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(now.replace("Z", "+00:00"))
            update_data["total_duration_minutes"] = int((end - start).total_seconds() / 60)
    
    await db.production_timelines.update_one(
        {"id": timeline_id},
        {"$set": update_data}
    )
    
    return {"message": "Stage advanced", "new_stage_order": next_order, "is_completed": is_completed}


@router.put("/{timeline_id}/stage/{stage_order}")
async def update_timeline_stage(
    timeline_id: str,
    stage_order: int,
    update: TimelineStageUpdate,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Update a specific stage in the timeline (including manual time overrides)"""
    tenant_id = current_user.tenant_id
    
    timeline = await db.production_timelines.find_one(
        {"id": timeline_id, "tenant_id": tenant_id}
    )
    if not timeline:
        raise HTTPException(status_code=404, detail="Timeline not found")
    
    stages = timeline.get("stages", [])
    now = datetime.now(timezone.utc).isoformat()
    
    # Find and update stage
    updated = False
    for stage in stages:
        if stage["stage_order"] == stage_order:
            if update.status:
                stage["status"] = update.status
                if update.status == "in_progress" and not stage.get("started_at"):
                    stage["started_at"] = now
                elif update.status == "completed" and not stage.get("completed_at"):
                    stage["completed_at"] = now
            
            if update.assigned_user_id:
                stage["assigned_user_id"] = update.assigned_user_id
            if update.assigned_user_name:
                stage["assigned_user_name"] = update.assigned_user_name
            if update.notes is not None:
                stage["notes"] = update.notes
            
            # Handle manual time overrides
            if update.manual_start_override:
                stage["manual_start_override"] = update.manual_start_override
                stage["started_at"] = update.manual_start_override
                stage["manually_adjusted"] = True
            if update.manual_end_override:
                stage["manual_end_override"] = update.manual_end_override
                stage["completed_at"] = update.manual_end_override
                stage["manually_adjusted"] = True
            
            # Recalculate duration if both times exist
            start_time = stage.get("started_at")
            end_time = stage.get("completed_at")
            if start_time and end_time:
                try:
                    start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                    stage["duration_minutes"] = int((end - start).total_seconds() / 60)
                except:
                    pass
            
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail="Stage not found")
    
    # Determine current stage
    current_order = 1
    for stage in stages:
        if stage["status"] == "in_progress":
            current_order = stage["stage_order"]
            break
        elif stage["status"] == "completed":
            current_order = stage["stage_order"] + 1
    
    await db.production_timelines.update_one(
        {"id": timeline_id},
        {"$set": {
            "stages": stages,
            "current_stage_order": current_order,
            "updated_at": now
        }}
    )
    
    return {"message": "Stage updated"}


# ============== ANALYTICS ==============

@router.get("/analytics")
async def get_production_analytics(
    category: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=365),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get production timeline analytics.
    Returns averages, bottlenecks, and trends.
    """
    tenant_id = current_user.tenant_id
    
    # Calculate date range
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    query = {
        "tenant_id": tenant_id,
        "created_at": {"$gte": cutoff}
    }
    if category:
        query["category"] = category
    
    timelines = await db.production_timelines.find(
        query, {"_id": 0}
    ).to_list(1000)
    
    if not timelines:
        return TimelineAnalytics().model_dump()
    
    # Calculate metrics
    total = len(timelines)
    completed = len([t for t in timelines if t.get("completed_at")])
    
    # Average completion time (for completed timelines)
    completion_times = [t["total_duration_minutes"] for t in timelines if t.get("total_duration_minutes")]
    avg_completion = sum(completion_times) / len(completion_times) if completion_times else None
    
    # Stage averages
    stage_durations = {}
    for timeline in timelines:
        for stage in timeline.get("stages", []):
            name = stage.get("stage_name")
            duration = stage.get("duration_minutes")
            if name and duration:
                if name not in stage_durations:
                    stage_durations[name] = []
                stage_durations[name].append(duration)
    
    stage_averages = {}
    for name, durations in stage_durations.items():
        stage_averages[name] = sum(durations) / len(durations)
    
    # Identify bottlenecks (stages with highest average time)
    bottlenecks = []
    if stage_averages:
        sorted_stages = sorted(stage_averages.items(), key=lambda x: x[1], reverse=True)
        avg_stage_time = sum(stage_averages.values()) / len(stage_averages)
        
        for name, avg_time in sorted_stages[:5]:
            bottlenecks.append({
                "stage_name": name,
                "avg_minutes": round(avg_time, 1),
                "is_bottleneck": avg_time > avg_stage_time * 1.5  # 50% above average
            })
    
    # Category breakdown
    category_breakdown = {}
    for timeline in timelines:
        cat = timeline.get("category", "unknown")
        category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
    
    return {
        "total_timelines": total,
        "completed_timelines": completed,
        "average_completion_time_minutes": round(avg_completion, 1) if avg_completion else None,
        "stage_averages": {k: round(v, 1) for k, v in stage_averages.items()},
        "bottlenecks": bottlenecks,
        "category_breakdown": category_breakdown
    }


@router.get("/analytics/stage-report")
async def get_stage_time_report(
    days: int = Query(default=30, ge=1, le=365),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get detailed stage time report.
    Shows min, max, average for each stage.
    """
    tenant_id = current_user.tenant_id
    
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    timelines = await db.production_timelines.find(
        {"tenant_id": tenant_id, "created_at": {"$gte": cutoff}},
        {"_id": 0, "stages": 1}
    ).to_list(1000)
    
    stage_data = {}
    for timeline in timelines:
        for stage in timeline.get("stages", []):
            name = stage.get("stage_name")
            duration = stage.get("duration_minutes")
            if name and duration is not None:
                if name not in stage_data:
                    stage_data[name] = []
                stage_data[name].append(duration)
    
    report = []
    for name, durations in stage_data.items():
        report.append({
            "stage_name": name,
            "count": len(durations),
            "min_minutes": min(durations),
            "max_minutes": max(durations),
            "avg_minutes": round(sum(durations) / len(durations), 1),
            "total_minutes": sum(durations)
        })
    
    # Sort by average time descending
    report.sort(key=lambda x: x["avg_minutes"], reverse=True)
    
    return report
