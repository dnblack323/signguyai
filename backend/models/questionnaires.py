"""
Questionnaire Models for Dynamic Form Builder

Allows sign shops to create custom intake forms for different job types
like vehicle wraps, signs, apparel, etc.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
import uuid


class QuestionType(str, Enum):
    """Types of questions that can be added to a questionnaire"""
    TEXT = "text"                    # Single line text input
    TEXTAREA = "textarea"            # Multi-line text input
    NUMBER = "number"                # Numeric input
    EMAIL = "email"                  # Email input with validation
    PHONE = "phone"                  # Phone number input
    SELECT = "select"                # Dropdown/single select
    MULTI_SELECT = "multi_select"    # Multiple selection
    RADIO = "radio"                  # Radio buttons (single choice)
    CHECKBOX = "checkbox"            # Checkboxes (multiple choice)
    DATE = "date"                    # Date picker
    FILE_UPLOAD = "file_upload"      # File/image upload
    SIGNATURE = "signature"          # Signature capture
    HEADING = "heading"              # Section heading (non-input)
    PARAGRAPH = "paragraph"          # Descriptive text (non-input)


class QuestionOption(BaseModel):
    """Option for select/radio/checkbox questions"""
    value: str
    label: str
    description: Optional[str] = None


class QuestionConditional(BaseModel):
    """Conditional logic for showing/hiding questions"""
    depends_on: str  # Question ID this depends on
    operator: str = "equals"  # equals, not_equals, contains, greater_than, less_than
    value: Any  # Value to compare against


class Question(BaseModel):
    """Individual question in a questionnaire"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: QuestionType
    label: str
    description: Optional[str] = None
    placeholder: Optional[str] = None
    required: bool = False
    options: Optional[List[QuestionOption]] = None  # For select/radio/checkbox
    validation: Optional[Dict[str, Any]] = None  # min, max, pattern, etc.
    conditional: Optional[QuestionConditional] = None  # Show/hide based on other answers
    order: int = 0
    # For file uploads
    accept_file_types: Optional[List[str]] = None  # e.g., ["image/*", ".pdf"]
    max_file_size_mb: Optional[int] = 10


class QuestionnaireCategory(str, Enum):
    """Categories for organizing questionnaires"""
    VEHICLE_WRAP = "vehicle_wrap"
    SIGNAGE = "signage"
    APPAREL = "apparel"
    PRINT = "print"
    CUSTOM = "custom"
    GENERAL = "general"


class QuestionnaireStatus(str, Enum):
    """Status of a questionnaire"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class QuestionnaireCreate(BaseModel):
    """Request model for creating a questionnaire"""
    name: str
    description: Optional[str] = None
    category: QuestionnaireCategory = QuestionnaireCategory.GENERAL
    questions: List[Question] = []
    is_default: bool = False  # If true, auto-attach to new jobs of this category
    thank_you_message: Optional[str] = "Thank you for completing this questionnaire!"


class QuestionnaireUpdate(BaseModel):
    """Request model for updating a questionnaire"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[QuestionnaireCategory] = None
    questions: Optional[List[Question]] = None
    status: Optional[QuestionnaireStatus] = None
    is_default: Optional[bool] = None
    thank_you_message: Optional[str] = None


class Questionnaire(BaseModel):
    """Full questionnaire model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    description: Optional[str] = None
    category: QuestionnaireCategory = QuestionnaireCategory.GENERAL
    questions: List[Question] = []
    status: QuestionnaireStatus = QuestionnaireStatus.DRAFT
    is_default: bool = False
    thank_you_message: str = "Thank you for completing this questionnaire!"
    response_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_by: Optional[str] = None


class QuestionnaireResponseCreate(BaseModel):
    """Request model for submitting questionnaire responses"""
    questionnaire_id: str
    answers: Dict[str, Any]  # question_id -> answer value
    job_id: Optional[str] = None  # Link to a job if applicable
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None


class QuestionnaireResponse(BaseModel):
    """Stored questionnaire response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    questionnaire_id: str
    questionnaire_name: str
    answers: Dict[str, Any]
    job_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    submitted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ip_address: Optional[str] = None


# Pre-built questionnaire templates
QUESTIONNAIRE_TEMPLATES = {
    "vehicle_wrap_intake": {
        "name": "Vehicle Wrap Intake Form",
        "description": "Gather all necessary information for a vehicle wrap project",
        "category": "vehicle_wrap",
        "questions": [
            {
                "type": "heading",
                "label": "Vehicle Information",
                "order": 0
            },
            {
                "type": "select",
                "label": "Vehicle Type",
                "required": True,
                "options": [
                    {"value": "car_sedan", "label": "Car - Sedan"},
                    {"value": "car_suv", "label": "Car - SUV/Crossover"},
                    {"value": "truck_pickup", "label": "Truck - Pickup"},
                    {"value": "truck_box", "label": "Truck - Box/Cargo"},
                    {"value": "van_cargo", "label": "Van - Cargo"},
                    {"value": "van_sprinter", "label": "Van - Sprinter Style"},
                    {"value": "trailer", "label": "Trailer"},
                    {"value": "boat", "label": "Boat"},
                    {"value": "other", "label": "Other"}
                ],
                "order": 1
            },
            {
                "type": "text",
                "label": "Year, Make & Model",
                "placeholder": "e.g., 2023 Ford F-150 XLT",
                "required": True,
                "order": 2
            },
            {
                "type": "text",
                "label": "Vehicle Color",
                "placeholder": "Current vehicle color",
                "required": True,
                "order": 3
            },
            {
                "type": "heading",
                "label": "Wrap Details",
                "order": 4
            },
            {
                "type": "select",
                "label": "Wrap Coverage",
                "required": True,
                "options": [
                    {"value": "full", "label": "Full Wrap (100%)"},
                    {"value": "partial_75", "label": "Partial Wrap (75%)"},
                    {"value": "partial_50", "label": "Partial Wrap (50%)"},
                    {"value": "partial_25", "label": "Accent/Partial (25% or less)"},
                    {"value": "color_change", "label": "Color Change Only"},
                    {"value": "decals", "label": "Decals/Lettering Only"}
                ],
                "order": 5
            },
            {
                "type": "multi_select",
                "label": "Areas to Wrap",
                "options": [
                    {"value": "hood", "label": "Hood"},
                    {"value": "roof", "label": "Roof"},
                    {"value": "doors", "label": "Doors"},
                    {"value": "fenders", "label": "Fenders"},
                    {"value": "bumpers", "label": "Bumpers"},
                    {"value": "tailgate", "label": "Tailgate/Rear"},
                    {"value": "mirrors", "label": "Mirrors"},
                    {"value": "all", "label": "Entire Vehicle"}
                ],
                "order": 6
            },
            {
                "type": "radio",
                "label": "Do you have artwork/design ready?",
                "required": True,
                "options": [
                    {"value": "yes_files", "label": "Yes, I have print-ready files"},
                    {"value": "yes_concept", "label": "Yes, I have a concept/rough design"},
                    {"value": "no_need_design", "label": "No, I need design services"},
                    {"value": "color_change_only", "label": "No design needed (color change only)"}
                ],
                "order": 7
            },
            {
                "type": "file_upload",
                "label": "Upload Artwork or Reference Images",
                "description": "Upload any logos, designs, or reference images",
                "accept_file_types": ["image/*", ".pdf", ".ai", ".eps"],
                "max_file_size_mb": 25,
                "order": 8
            },
            {
                "type": "textarea",
                "label": "Design Notes or Special Requests",
                "placeholder": "Describe your vision, colors, placement preferences, etc.",
                "order": 9
            },
            {
                "type": "heading",
                "label": "Timeline & Budget",
                "order": 10
            },
            {
                "type": "date",
                "label": "When do you need this completed?",
                "required": True,
                "order": 11
            },
            {
                "type": "select",
                "label": "Budget Range",
                "options": [
                    {"value": "under_1000", "label": "Under $1,000"},
                    {"value": "1000_2500", "label": "$1,000 - $2,500"},
                    {"value": "2500_5000", "label": "$2,500 - $5,000"},
                    {"value": "5000_plus", "label": "$5,000+"},
                    {"value": "not_sure", "label": "Not sure / Need quote"}
                ],
                "order": 12
            },
            {
                "type": "textarea",
                "label": "Anything else we should know?",
                "placeholder": "Any other details, questions, or concerns",
                "order": 13
            }
        ]
    },
    "sign_request": {
        "name": "Sign Request Form",
        "description": "Intake form for sign projects",
        "category": "signage",
        "questions": [
            {
                "type": "heading",
                "label": "Sign Details",
                "order": 0
            },
            {
                "type": "select",
                "label": "Sign Type",
                "required": True,
                "options": [
                    {"value": "banner", "label": "Banner"},
                    {"value": "yard_sign", "label": "Yard/Lawn Sign"},
                    {"value": "window", "label": "Window Graphics"},
                    {"value": "wall", "label": "Wall Sign/Graphics"},
                    {"value": "monument", "label": "Monument Sign"},
                    {"value": "channel_letter", "label": "Channel Letters"},
                    {"value": "illuminated", "label": "Illuminated/LED Sign"},
                    {"value": "acrylic", "label": "Acrylic Sign"},
                    {"value": "metal", "label": "Metal Sign"},
                    {"value": "a_frame", "label": "A-Frame/Sandwich Board"},
                    {"value": "other", "label": "Other"}
                ],
                "order": 1
            },
            {
                "type": "text",
                "label": "Desired Size (Width x Height)",
                "placeholder": "e.g., 4ft x 3ft, 24\" x 36\"",
                "required": True,
                "order": 2
            },
            {
                "type": "number",
                "label": "Quantity Needed",
                "required": True,
                "validation": {"min": 1},
                "order": 3
            },
            {
                "type": "radio",
                "label": "Indoor or Outdoor Use?",
                "required": True,
                "options": [
                    {"value": "indoor", "label": "Indoor Only"},
                    {"value": "outdoor", "label": "Outdoor"},
                    {"value": "both", "label": "Both Indoor & Outdoor"}
                ],
                "order": 4
            },
            {
                "type": "textarea",
                "label": "What text/message should be on the sign?",
                "placeholder": "Enter the exact text you want displayed",
                "required": True,
                "order": 5
            },
            {
                "type": "file_upload",
                "label": "Upload Logo or Design Files",
                "accept_file_types": ["image/*", ".pdf", ".ai", ".eps"],
                "order": 6
            },
            {
                "type": "text",
                "label": "Brand Colors (if applicable)",
                "placeholder": "e.g., Blue #003366, Red #CC0000",
                "order": 7
            },
            {
                "type": "date",
                "label": "When do you need this?",
                "required": True,
                "order": 8
            }
        ]
    },
    "apparel_order": {
        "name": "Apparel/Merchandise Order Form",
        "description": "Intake form for custom apparel and merchandise",
        "category": "apparel",
        "questions": [
            {
                "type": "heading",
                "label": "Order Details",
                "order": 0
            },
            {
                "type": "multi_select",
                "label": "What items do you need?",
                "required": True,
                "options": [
                    {"value": "tshirt", "label": "T-Shirts"},
                    {"value": "hoodie", "label": "Hoodies/Sweatshirts"},
                    {"value": "polo", "label": "Polo Shirts"},
                    {"value": "jacket", "label": "Jackets"},
                    {"value": "hat", "label": "Hats/Caps"},
                    {"value": "bag", "label": "Bags/Totes"},
                    {"value": "other", "label": "Other"}
                ],
                "order": 1
            },
            {
                "type": "number",
                "label": "Approximate Total Quantity",
                "required": True,
                "validation": {"min": 1},
                "order": 2
            },
            {
                "type": "select",
                "label": "Decoration Method Preference",
                "options": [
                    {"value": "screen_print", "label": "Screen Printing"},
                    {"value": "dtg", "label": "Direct-to-Garment (DTG)"},
                    {"value": "embroidery", "label": "Embroidery"},
                    {"value": "heat_transfer", "label": "Heat Transfer/Vinyl"},
                    {"value": "not_sure", "label": "Not Sure - Recommend for me"}
                ],
                "order": 3
            },
            {
                "type": "file_upload",
                "label": "Upload Artwork/Logo",
                "accept_file_types": ["image/*", ".pdf", ".ai", ".eps"],
                "required": True,
                "order": 4
            },
            {
                "type": "multi_select",
                "label": "Print/Design Locations",
                "options": [
                    {"value": "front_left", "label": "Front Left Chest"},
                    {"value": "front_center", "label": "Front Center"},
                    {"value": "front_full", "label": "Full Front"},
                    {"value": "back_upper", "label": "Back Upper"},
                    {"value": "back_full", "label": "Full Back"},
                    {"value": "sleeve_left", "label": "Left Sleeve"},
                    {"value": "sleeve_right", "label": "Right Sleeve"}
                ],
                "order": 5
            },
            {
                "type": "textarea",
                "label": "Size Breakdown (if known)",
                "placeholder": "e.g., 5 Small, 10 Medium, 15 Large, 5 XL",
                "order": 6
            },
            {
                "type": "date",
                "label": "Event/Deadline Date",
                "order": 7
            },
            {
                "type": "textarea",
                "label": "Additional Notes",
                "order": 8
            }
        ]
    }
}
