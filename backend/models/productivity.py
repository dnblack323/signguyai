"""Unified productivity models."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProductivityItem(BaseModel):
    uid: str
    id: str
    title: str
    type: str
    source_type: str
    source_id: str
    related_order_id: Optional[str] = None
    related_job_id: Optional[str] = None
    related_job_ticket_id: Optional[str] = None
    related_customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    status: str = "open"
    priority: str = "normal"
    start_datetime: Optional[str] = None
    due_datetime: Optional[str] = None
    all_day: bool = True
    is_completed: bool = False
    board_column: str = "open"
    notes: str = ""
    category: str = "general"
    color: str = "slate"
    source_route: Optional[str] = None
    source_reference: Optional[str] = None
    source_label: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class ProductivityResponse(BaseModel):
    items: List[ProductivityItem]
    total: int
    applied_filters: Dict[str, Any] = Field(default_factory=dict)


class ProductivitySummary(BaseModel):
    due_today: int = 0
    overdue: int = 0
    waiting_on_approval: int = 0
    scheduled_this_week: int = 0
    my_assigned: int = 0
    open_items: int = 0
    completed_items: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_board_column: Dict[str, int] = Field(default_factory=dict)
