"""
Production Timeline Models

Models for tracking production workflow stages at the line-item level.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import uuid


class ProductionCategory(str, Enum):
    """Categories of production items with different workflows"""
    VEHICLE_WRAP = "vehicle_wrap"
    PRINTED_SIGNS = "printed_signs"
    CUT_VINYL = "cut_vinyl"
    BANNERS = "banners"
    APPAREL = "apparel"
    CUSTOM = "custom"


# Default workflow templates by category
DEFAULT_WORKFLOW_TEMPLATES = {
    ProductionCategory.VEHICLE_WRAP.value: {
        "name": "Vehicle Wrap",
        "stages": [
            {"name": "Job Created", "order": 1, "auto_trigger": "job_created"},
            {"name": "Artwork Uploaded", "order": 2, "auto_trigger": "artwork_uploaded"},
            {"name": "Design Revisions", "order": 3},
            {"name": "Sent for Approval", "order": 4, "auto_trigger": "sent_for_approval"},
            {"name": "Customer Approved", "order": 5, "auto_trigger": "customer_approved"},
            {"name": "Production Scheduled", "order": 6},
            {"name": "Print Panels", "order": 7},
            {"name": "Laminate", "order": 8},
            {"name": "Prep Vehicle", "order": 9},
            {"name": "Install Wrap", "order": 10},
            {"name": "Final Inspection", "order": 11},
            {"name": "Completed", "order": 12, "is_final": True}
        ]
    },
    ProductionCategory.PRINTED_SIGNS.value: {
        "name": "Printed Signs",
        "stages": [
            {"name": "Job Created", "order": 1, "auto_trigger": "job_created"},
            {"name": "Artwork Uploaded", "order": 2, "auto_trigger": "artwork_uploaded"},
            {"name": "Design Adjustments", "order": 3},
            {"name": "Sent for Approval", "order": 4, "auto_trigger": "sent_for_approval"},
            {"name": "Customer Approved", "order": 5, "auto_trigger": "customer_approved"},
            {"name": "Print", "order": 6},
            {"name": "Laminate", "order": 7},
            {"name": "Trim / Mount", "order": 8},
            {"name": "Quality Check", "order": 9},
            {"name": "Completed", "order": 10, "is_final": True}
        ]
    },
    ProductionCategory.CUT_VINYL.value: {
        "name": "Cut Vinyl / Decals",
        "stages": [
            {"name": "Job Created", "order": 1, "auto_trigger": "job_created"},
            {"name": "Artwork Uploaded", "order": 2, "auto_trigger": "artwork_uploaded"},
            {"name": "Sent for Approval", "order": 3, "auto_trigger": "sent_for_approval"},
            {"name": "Customer Approved", "order": 4, "auto_trigger": "customer_approved"},
            {"name": "Cut Vinyl", "order": 5},
            {"name": "Weed", "order": 6},
            {"name": "Mask", "order": 7},
            {"name": "Quality Check", "order": 8},
            {"name": "Completed", "order": 9, "is_final": True}
        ]
    },
    ProductionCategory.BANNERS.value: {
        "name": "Banners",
        "stages": [
            {"name": "Job Created", "order": 1, "auto_trigger": "job_created"},
            {"name": "Artwork Uploaded", "order": 2, "auto_trigger": "artwork_uploaded"},
            {"name": "Sent for Approval", "order": 3, "auto_trigger": "sent_for_approval"},
            {"name": "Customer Approved", "order": 4, "auto_trigger": "customer_approved"},
            {"name": "Print", "order": 5},
            {"name": "Trim", "order": 6},
            {"name": "Grommets", "order": 7},
            {"name": "Completed", "order": 8, "is_final": True}
        ]
    },
    ProductionCategory.APPAREL.value: {
        "name": "Apparel",
        "stages": [
            {"name": "Job Created", "order": 1, "auto_trigger": "job_created"},
            {"name": "Artwork Uploaded", "order": 2, "auto_trigger": "artwork_uploaded"},
            {"name": "Sent for Approval", "order": 3, "auto_trigger": "sent_for_approval"},
            {"name": "Customer Approved", "order": 4, "auto_trigger": "customer_approved"},
            {"name": "Order Transfers", "order": 5},
            {"name": "Press Apparel", "order": 6},
            {"name": "Quality Check", "order": 7},
            {"name": "Completed", "order": 8, "is_final": True}
        ]
    }
}

SIMPLE_WORKFLOW_TEMPLATES = {
    ProductionCategory.VEHICLE_WRAP.value: {
        "name": "Vehicle Wrap - Simple",
        "stages": [
            {"name": "Design", "order": 1},
            {"name": "Production", "order": 2},
            {"name": "Installation / Completion", "order": 3, "is_final": True},
        ],
    },
    ProductionCategory.PRINTED_SIGNS.value: {
        "name": "Printed Signs - Simple",
        "stages": [
            {"name": "Design", "order": 1},
            {"name": "Production", "order": 2},
            {"name": "Installation / Completion", "order": 3, "is_final": True},
        ],
    },
    ProductionCategory.CUT_VINYL.value: {
        "name": "Cut Vinyl - Simple",
        "stages": [
            {"name": "Design", "order": 1},
            {"name": "Production", "order": 2},
            {"name": "Installation / Completion", "order": 3, "is_final": True},
        ],
    },
    ProductionCategory.BANNERS.value: {
        "name": "Banners - Simple",
        "stages": [
            {"name": "Design", "order": 1},
            {"name": "Production", "order": 2},
            {"name": "Installation / Completion", "order": 3, "is_final": True},
        ],
    },
    ProductionCategory.APPAREL.value: {
        "name": "Apparel - Simple",
        "stages": [
            {"name": "Design", "order": 1},
            {"name": "Production", "order": 2},
            {"name": "Installation / Completion", "order": 3, "is_final": True},
        ],
    },
    ProductionCategory.CUSTOM.value: {
        "name": "Custom - Simple",
        "stages": [
            {"name": "Design", "order": 1},
            {"name": "Production", "order": 2},
            {"name": "Installation / Completion", "order": 3, "is_final": True},
        ],
    },
}


class WorkflowStage(BaseModel):
    """Definition of a single workflow stage"""
    name: str
    order: int
    auto_trigger: Optional[str] = None  # Event that auto-advances to this stage
    is_final: bool = False
    description: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None


class WorkflowTemplate(BaseModel):
    """A workflow template that can be customized per tenant"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    category: str  # ProductionCategory value
    name: str
    stages: List[WorkflowStage]
    is_default: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TimelineStageEntry(BaseModel):
    """A single stage entry in a line item's production timeline"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage_name: str
    stage_order: int
    status: str = "pending"  # pending, in_progress, completed, skipped
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_minutes: Optional[int] = None
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    notes: Optional[str] = None
    # Manual override fields
    manual_start_override: Optional[str] = None
    manual_end_override: Optional[str] = None
    manually_adjusted: bool = False


class ProductionTimeline(BaseModel):
    """Production timeline for a single line item"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    job_id: str
    line_item_id: str
    workflow_template_id: Optional[str] = None
    category: str
    enabled: bool = True
    current_stage_order: int = 1
    stages: List[TimelineStageEntry] = []
    total_duration_minutes: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TimelineStageUpdate(BaseModel):
    """Request to update a timeline stage"""
    status: Optional[str] = None  # in_progress, completed, skipped
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    notes: Optional[str] = None
    manual_start_override: Optional[str] = None
    manual_end_override: Optional[str] = None


class TimelineAnalytics(BaseModel):
    """Analytics data for production timelines"""
    total_timelines: int = 0
    completed_timelines: int = 0
    average_completion_time_minutes: Optional[float] = None
    stage_averages: Dict[str, float] = {}  # stage_name: avg_minutes
    bottlenecks: List[Dict[str, Any]] = []  # [{stage_name, avg_time, is_bottleneck}]
    category_breakdown: Dict[str, int] = {}  # category: count
