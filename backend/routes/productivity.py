"""Unified productivity endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from server import db, get_current_active_user
from models import UserInDB
from services.productivity_query import build_productivity_summary, get_unified_productivity_items, update_productivity_source

router = APIRouter(prefix="/productivity", tags=["Productivity"])


class ProductivityUpdatePayload(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_user_id: Optional[str] = None
    start_datetime: Optional[str] = None
    due_datetime: Optional[str] = None
    is_completed: Optional[bool] = None
    notes: Optional[str] = None
    schedule_day_key: Optional[str] = None


@router.get("/items")
async def get_productivity_items(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    item_types: Optional[str] = None,
    statuses: Optional[str] = None,
    priorities: Optional[str] = None,
    assigned_user_ids: Optional[str] = None,
    customer_ids: Optional[str] = None,
    source_types: Optional[str] = None,
    search: Optional[str] = None,
    include_completed: bool = False,
    current_user: UserInDB = Depends(get_current_active_user),
):
    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "item_types": item_types,
        "statuses": statuses,
        "priorities": priorities,
        "assigned_user_ids": assigned_user_ids,
        "customer_ids": customer_ids,
        "source_types": source_types,
        "search": search,
        "include_completed": include_completed,
    }
    items = await get_unified_productivity_items(db, current_user.tenant_id, filters)
    return {"items": [item.model_dump() for item in items], "total": len(items), "applied_filters": filters}


@router.get("/summary")
async def get_productivity_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    item_types: Optional[str] = None,
    statuses: Optional[str] = None,
    priorities: Optional[str] = None,
    assigned_user_ids: Optional[str] = None,
    customer_ids: Optional[str] = None,
    source_types: Optional[str] = None,
    search: Optional[str] = None,
    include_completed: bool = True,
    current_user: UserInDB = Depends(get_current_active_user),
):
    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "item_types": item_types,
        "statuses": statuses,
        "priorities": priorities,
        "assigned_user_ids": assigned_user_ids,
        "customer_ids": customer_ids,
        "source_types": source_types,
        "search": search,
        "include_completed": include_completed,
    }
    items = await get_unified_productivity_items(db, current_user.tenant_id, filters)
    return build_productivity_summary(items, current_user.id).model_dump()


@router.get("/calendar-range")
async def get_calendar_range(
    anchor_date: Optional[str] = None,
    view: str = Query("month", pattern="^(month|week|day)$"),
    item_types: Optional[str] = None,
    statuses: Optional[str] = None,
    priorities: Optional[str] = None,
    assigned_user_ids: Optional[str] = None,
    include_completed: bool = False,
    current_user: UserInDB = Depends(get_current_active_user),
):
    today = datetime.now(timezone.utc).date()
    base_date = datetime.fromisoformat(anchor_date).date() if anchor_date else today

    if view == "day":
        start_date = base_date.isoformat()
        end_date = base_date.isoformat()
    elif view == "week":
        week_start = base_date - timedelta(days=base_date.weekday())
        start_date = week_start.isoformat()
        end_date = (week_start + timedelta(days=6)).isoformat()
    else:
        month_start = base_date.replace(day=1)
        grid_start = month_start - timedelta(days=month_start.weekday())
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        grid_end = month_end + timedelta(days=(6 - month_end.weekday()))
        start_date = grid_start.isoformat()
        end_date = grid_end.isoformat()

    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "item_types": item_types,
        "statuses": statuses,
        "priorities": priorities,
        "assigned_user_ids": assigned_user_ids,
        "include_completed": include_completed,
    }
    items = await get_unified_productivity_items(db, current_user.tenant_id, filters)
    return {
        "view": view,
        "anchor_date": base_date.isoformat(),
        "range": {"start_date": start_date, "end_date": end_date},
        "items": [item.model_dump() for item in items],
        "summary": build_productivity_summary(items, current_user.id).model_dump(),
    }


@router.get("/board")
async def get_productivity_board(
    statuses: Optional[str] = None,
    item_types: Optional[str] = None,
    assigned_user_ids: Optional[str] = None,
    include_completed: bool = False,
    current_user: UserInDB = Depends(get_current_active_user),
):
    filters = {
        "statuses": statuses,
        "item_types": item_types,
        "assigned_user_ids": assigned_user_ids,
        "include_completed": include_completed,
    }
    items = await get_unified_productivity_items(db, current_user.tenant_id, filters)
    groups = {}
    for item in items:
        groups.setdefault(item.board_column, []).append(item.model_dump())
    return {"groups": groups, "total": len(items)}


@router.patch("/items/{item_uid}")
async def patch_productivity_item(
    item_uid: str,
    payload: ProductivityUpdatePayload,
    current_user: UserInDB = Depends(get_current_active_user),
):
    await update_productivity_source(db, current_user.tenant_id, item_uid, {k: v for k, v in payload.model_dump().items() if v is not None})
    items = await get_unified_productivity_items(db, current_user.tenant_id, {"include_completed": True})
    updated = next((item for item in items if item.uid == item_uid), None)
    return updated.model_dump() if updated else {"message": "Updated"}