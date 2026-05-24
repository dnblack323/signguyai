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
    WEB_STORES = "web_stores"
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
    # Event Store linkage
    webstore_id: Optional[str] = None
    # Prefilled answer values keyed by question ID (auto-filled in public form)
    prefill_answers: Optional[Dict[str, Any]] = None
    # Question IDs that are locked (read-only, shown as "Set by store provider")
    locked_answer_ids: Optional[List[str]] = None
    # ISO timestamp of last email send
    last_sent_at: Optional[str] = None


class QuestionnaireResponseCreate(BaseModel):
    """Request model for submitting questionnaire responses"""
    questionnaire_id: str
    answers: Dict[str, Any]  # question_id -> answer value
    job_id: Optional[str] = None  # Link to a job if applicable
    customer_id: Optional[str] = None
    webstore_id: Optional[str] = None  # Link to a webstore if applicable
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
    webstore_id: Optional[str] = None
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
    },
    "event_web_store_setup": {
        "name": "Event Web Store Setup Questionnaire",
        "description": "Comprehensive intake form for setting up an event-based web store for apparel, signs, decals, merchandise, or other event-related products",
        "category": "web_stores",
        "intro_text": "Thank you for choosing us to set up your event web store. Please complete this form as accurately as possible so we can build your store correctly and avoid delays.\n\nYour answers will help us determine what products should be offered, what artwork or design work is needed, when the store should open and close, how customers should receive their orders, who should receive payments, whether Stripe Connect setup is required, and who needs to approve the store before launch.\n\nPlease upload any logos, event artwork, flyers, sponsor logos, product ideas, or design examples that may help with the store setup.",
        "questions": [
            # Section 1: Contact and Event Details
            {"type": "heading", "label": "Contact and Event Details", "order": 0},
            {"type": "text", "label": "Customer Name", "required": True, "order": 1},
            {"type": "text", "label": "Organization / Business Name", "order": 2},
            {"type": "phone", "label": "Phone Number", "required": True, "order": 3},
            {"type": "email", "label": "Email Address", "required": True, "order": 4},
            {"type": "select", "label": "Best way to contact you", "options": [
                {"value": "call", "label": "Call"},
                {"value": "text", "label": "Text"},
                {"value": "email", "label": "Email"}
            ], "order": 5},
            {"type": "text", "label": "Who is the main decision-maker for this store?", "order": 6},
            {"type": "text", "label": "Event Name", "required": True, "order": 7},
            {"type": "date", "label": "Event Date", "order": 8},
            {"type": "text", "label": "Event Location", "order": 9},
            {"type": "textarea", "label": "Briefly describe the event", "order": 10},
            {"type": "select", "label": "Is this a one-time event or recurring event?", "options": [
                {"value": "one_time", "label": "One-time event"},
                {"value": "annual", "label": "Annual event"},
                {"value": "seasonal", "label": "Seasonal event"},
                {"value": "recurring", "label": "Recurring event"},
                {"value": "not_sure", "label": "Not sure"}
            ], "order": 11},
            {"type": "date", "label": "When do you want the store to launch?", "order": 12},
            {"type": "date", "label": "When should the store close?", "order": 13},
            
            # Section 2: Store Setup and Branding
            {"type": "heading", "label": "Store Setup and Branding", "order": 14},
            {"type": "text", "label": "What should the store be called?", "required": True, "order": 15},
            {"type": "select", "label": "Do you want the store to be public or private?", "required": True, "options": [
                {"value": "public", "label": "Public"},
                {"value": "private", "label": "Private link only"}
            ], "order": 16},
            {"type": "file_upload", "label": "Upload your logo, event flyer, artwork, or graphics", 
             "description": "Accept images, PDF, AI, EPS, SVG, PNG, JPG, JPEG, ZIP",
             "accept_file_types": ["image/*", ".pdf", ".ai", ".eps", ".svg", ".zip"],
             "max_file_size_mb": 25, "order": 17},
            {"type": "text", "label": "Colors to use", "placeholder": "e.g., Blue #003366, Red #CC0000", "order": 18},
            {"type": "text", "label": "Colors to avoid", "order": 19},
            {"type": "textarea", "label": "Store welcome message / event description", "order": 20},
            
            # Section 3: Products and Design
            {"type": "heading", "label": "Products and Design", "order": 21},
            {"type": "checkbox", "label": "What products do you want in the store? Check all that apply.", "required": True, "options": [
                {"value": "tshirts", "label": "T-shirts"},
                {"value": "hoodies", "label": "Hoodies"},
                {"value": "crewnecks", "label": "Crewnecks"},
                {"value": "long_sleeve", "label": "Long sleeve shirts"},
                {"value": "hats", "label": "Hats"},
                {"value": "yard_signs", "label": "Yard signs"},
                {"value": "banners", "label": "Banners"},
                {"value": "decals", "label": "Decals / stickers"},
                {"value": "posters", "label": "Posters"},
                {"value": "tumblers", "label": "Tumblers / cups"},
                {"value": "bags", "label": "Bags"},
                {"value": "other", "label": "Other"}
            ], "order": 22},
            {"type": "select", "label": "How many designs do you want available?", "options": [
                {"value": "1", "label": "1 design"},
                {"value": "2_3", "label": "2–3 designs"},
                {"value": "4_5", "label": "4–5 designs"},
                {"value": "5_plus", "label": "More than 5"},
                {"value": "not_sure", "label": "Not sure"}
            ], "order": 23},
            {"type": "select", "label": "Do products need personalization?", 
             "description": "Example: name, number, team, role, date, custom text", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"},
                {"value": "maybe", "label": "Maybe"}
            ], "order": 24},
            {"type": "textarea", "label": "If yes, describe what customers should be able to customize", "order": 25},
            {"type": "text", "label": "Preferred shirt / apparel colors", "order": 26},
            {"type": "select", "label": "Do you want product recommendations based on the event type?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ], "order": 27},
            {"type": "select", "label": "Do you already have finished artwork?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"},
                {"value": "need_design", "label": "I need the design created"}
            ], "order": 28},
            {"type": "file_upload", "label": "Upload artwork files", 
             "accept_file_types": ["image/*", ".pdf", ".ai", ".eps", ".svg", ".zip"],
             "max_file_size_mb": 25, "order": 29},
            {"type": "select", "label": "Do you need help creating the event design?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ], "order": 30},
            {"type": "checkbox", "label": "What should be included on the design? Check all that apply.", "options": [
                {"value": "event_name", "label": "Event name"},
                {"value": "event_date", "label": "Event date"},
                {"value": "event_location", "label": "Event location"},
                {"value": "sponsor_logos", "label": "Sponsor logos"},
                {"value": "team_names", "label": "Team names"},
                {"value": "memorial_name", "label": "Memorial name"},
                {"value": "year", "label": "Year"},
                {"value": "other_text", "label": "Other custom text"}
            ], "order": 31},
            {"type": "file_upload", "label": "Upload sponsor logos if needed",
             "accept_file_types": ["image/*", ".pdf", ".ai", ".eps", ".svg", ".zip"],
             "max_file_size_mb": 25, "order": 32},
            {"type": "select", "label": "Should sponsor logos be arranged by size or importance?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"},
                {"value": "na", "label": "Not applicable"}
            ], "order": 33},
            {"type": "textarea", "label": "If yes, list sponsor priority order", "order": 34},
            {"type": "checkbox", "label": "Any design style preferences? Check all that apply.", "options": [
                {"value": "clean_simple", "label": "Clean and simple"},
                {"value": "bold_loud", "label": "Bold and loud"},
                {"value": "vintage", "label": "Vintage"},
                {"value": "sporty", "label": "Sporty"},
                {"value": "fun", "label": "Fun"},
                {"value": "elegant", "label": "Elegant"},
                {"value": "memorial", "label": "Memorial / meaningful"},
                {"value": "racing", "label": "Racing style"},
                {"value": "school_spirit", "label": "School spirit"},
                {"value": "corporate", "label": "Corporate / professional"},
                {"value": "other", "label": "Other"}
            ], "order": 35},
            
            # Section 4: Pricing and Fulfillment
            {"type": "heading", "label": "Pricing and Fulfillment", "order": 36},
            {"type": "text", "label": "If adding profit, how much should be added per item?", 
             "description": "Example: $5 per shirt, $10 per hoodie", "order": 37},
            {"type": "text", "label": "Who should receive the final order or sales report?", "order": 38},
            {"type": "select", "label": "How should customers receive their orders?", "options": [
                {"value": "individual_shipping", "label": "Individual shipping"},
                {"value": "pickup_event", "label": "Pickup at event"},
                {"value": "pickup_org", "label": "Pickup at your organization / business"},
                {"value": "pickup_shop", "label": "Pickup at SignGuy / shop location"},
                {"value": "bulk_delivery", "label": "Bulk delivery to organizer"},
                {"value": "not_sure", "label": "Not sure"}
            ], "order": 39},
            {"type": "textarea", "label": "If pickup is available, what pickup location should be shown?", "order": 40},
            {"type": "textarea", "label": "Pickup date / time instructions", "order": 41},
            {"type": "select", "label": "Should orders be individually bagged and labeled by customer name?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"},
                {"value": "not_sure", "label": "Not sure"}
            ], "order": 42},
            {"type": "select", "label": "Should customers receive order confirmation emails?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ], "order": 43},
            
            # Section 4.5: Fundraiser Settings
            {"type": "heading", "label": "Fundraiser Settings", "order": 44},
            {"type": "select", "label": "Is this store raising funds for a cause or organization?",
             "options": [
                 {"value": "yes", "label": "Yes"},
                 {"value": "no", "label": "No"},
                 {"value": "maybe", "label": "Maybe / Not sure"}
             ], "order": 45},
            {"type": "text", "label": "Fundraiser Name",
             "description": "e.g., Gala Fund, Team Spirit Fund", "order": 46},
            {"type": "textarea", "label": "Fundraiser Description",
             "description": "What will the funds be used for?", "order": 47},
            {"type": "number", "label": "Fundraiser Goal Amount ($)",
             "description": "Optional. Leave blank if you do not have a specific goal. "
                            "Donations and profit allocation can still be accepted without a set goal.",
             "order": 48},
            {"type": "select", "label": "Should a fundraiser progress bar be shown on the store?",
             "description": "Only applies when a fundraiser goal amount is set.",
             "options": [
                 {"value": "yes", "label": "Yes, show progress toward the goal"},
                 {"value": "no", "label": "No, do not show a progress bar"},
                 {"value": "not_sure", "label": "Not sure"}
             ], "order": 49},
            {"type": "select", "label": "Should customers be able to add a donation at checkout?",
             "options": [
                 {"value": "yes", "label": "Yes"},
                 {"value": "no", "label": "No"},
                 {"value": "not_sure", "label": "Not sure"}
             ], "order": 50},
            {"type": "text", "label": "Donation amount options to offer at checkout",
             "description": "e.g., $5, $10, $25, $50 — leave blank to allow any amount",
             "order": 51},
            {"type": "select", "label": "Should customers be able to enter a custom donation amount?",
             "options": [
                 {"value": "yes", "label": "Yes"},
                 {"value": "no", "label": "No"}
             ], "order": 52},
            {"type": "select",
             "label": "Should a portion of each product sale be allocated to the fundraiser?",
             "description": "Example: $5 from each shirt sold goes to the cause.",
             "options": [
                 {"value": "yes", "label": "Yes"},
                 {"value": "no", "label": "No"},
                 {"value": "not_sure", "label": "Not sure"}
             ], "order": 53},
            {"type": "select", "label": "Profit allocation type",
             "description": "How should the fundraiser portion be calculated?",
             "options": [
                 {"value": "percentage", "label": "Percentage of each sale"},
                 {"value": "fixed_per_item", "label": "Fixed dollar amount per item"},
                 {"value": "manual", "label": "Manual — we decide after the store closes"},
                 {"value": "na", "label": "Not applicable"}
             ], "order": 54},
            {"type": "number", "label": "Profit allocation percentage (%)",
             "description": "Only if percentage allocation is selected above.", "order": 55},
            {"type": "number", "label": "Fixed profit allocation amount per item ($)",
             "description": "Only if fixed amount per item is selected above.", "order": 56},
            {"type": "number", "label": "Maximum fundraiser cap amount ($)",
             "description": "Optional. Stop allocating to fundraiser once this amount is reached.",
             "order": 57},
            {"type": "select", "label": "Include checkout donations in fundraiser progress total?",
             "options": [
                 {"value": "yes", "label": "Yes"},
                 {"value": "no", "label": "No"}
             ], "order": 58},
            {"type": "select",
             "label": "Include product sale profit allocation in fundraiser progress total?",
             "options": [
                 {"value": "yes", "label": "Yes"},
                 {"value": "no", "label": "No"}
             ], "order": 59},
            {"type": "select", "label": "Show total amount raised publicly on the store?",
             "options": [
                 {"value": "yes", "label": "Yes"},
                 {"value": "no", "label": "No"}
             ], "order": 60},
            {"type": "select", "label": "Show supporter names on the store?",
             "options": [
                 {"value": "yes_with_permission", "label": "Yes, if customer consents"},
                 {"value": "yes_all", "label": "Yes, show all supporters"},
                 {"value": "no", "label": "No, keep supporters anonymous"}
             ], "order": 61},

            # Section 5: Stripe Connect Payment Setup
            {"type": "heading", "label": "Stripe Connect Payment Setup", "order": 62},
            {"type": "paragraph", "label": "To allow payments from this web store to go directly to your bank account, we use Stripe Connect. You will receive a secure setup link where you can enter your business, identity, tax, and banking information directly through Stripe.\n\nWe do not collect or store your full bank account information through this form. Stripe may require verification before payouts can begin.\n\nThe store may accept payments before payouts are fully available, but funds cannot be sent to your bank account until Stripe Connect setup is completed and approved.", "order": 63},
            {"type": "select", "label": "Who should receive the payments from this web store?", "options": [
                {"value": "individual", "label": "Individual"},
                {"value": "business", "label": "Business"},
                {"value": "organization", "label": "Organization"},
                {"value": "school", "label": "School / team / group"},
                {"value": "other", "label": "Other"}
            ], "order": 64},
            {"type": "text", "label": "Legal name or business name for payment account", "order": 65},
            {"type": "email", "label": "Email address to use for Stripe setup", "order": 66},
            {"type": "phone", "label": "Phone number for Stripe setup", "order": 67},
            {"type": "select", "label": "Do you already have a Stripe account?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"},
                {"value": "not_sure", "label": "Not sure"}
            ], "order": 68},
            {"type": "select", "label": "Who will complete the Stripe Connect setup?", "options": [
                {"value": "me", "label": "Me"},
                {"value": "business_owner", "label": "Business owner"},
                {"value": "treasurer", "label": "Treasurer"},
                {"value": "event_organizer", "label": "Event organizer"},
                {"value": "other", "label": "Other"}
            ], "order": 69},
            {"type": "email", "label": "Best email to receive the Stripe Connect setup link", "order": 70},

            # Section 6: Final Approval and Signature
            {"type": "heading", "label": "Final Approval and Signature", "order": 71},
            {"type": "text", "label": "Who should review the store before it goes live?", "order": 72},
            {"type": "select", "label": "Do you want to approve product names, pricing, images, and descriptions before launch?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ], "order": 73},
            {"type": "select", "label": "Do you want a store preview link before launch?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ], "order": 74},

            # Final Store Setup Agreement
            {"type": "paragraph", "label": "Final Store Setup Agreement", "description": "Please read and acknowledge the following statements before signing.", "order": 75},
            {"type": "checkbox", "label": "I understand the store will be built based on the information, artwork, pricing, product details, fulfillment details, and payment information provided.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 76},
            {"type": "checkbox", "label": "I understand missing or incorrect information may delay the store launch.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 77},
            {"type": "checkbox", "label": "I understand the store will not launch until product details, pricing, artwork, fulfillment settings, and payment setup are approved.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 78},
            {"type": "checkbox", "label": "I understand changes after launch may affect orders, pricing, production timelines, customer experience, and reporting.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 79},
            {"type": "checkbox", "label": "I understand Stripe Connect setup must be completed before payouts can be sent to your bank account, and Stripe may require identity, business, tax, and banking information before payouts can begin.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 80},
            {"type": "checkbox", "label": "I understand payment processing fees and any agreed platform/store fees may be deducted from online transactions, and payouts are sent according to Stripe's payout schedule.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 81},
            {"type": "checkbox", "label": "I understand customer-provided artwork, logos, images, names, and sponsor files must be approved for use by the customer or organization submitting this form.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 82},
            {"type": "checkbox", "label": "I understand production timelines depend on final store approval, payment setup, artwork readiness, order volume, product availability, fulfillment method, and whether submitted artwork is usable for print.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 83},

            # Signature Fields
            {"type": "text", "label": "Customer Name", "required": True, "order": 84},
            {"type": "signature", "label": "Customer Signature", "required": True, "order": 85},
            {"type": "date", "label": "Date", "required": True, "order": 86}
        ]
    },

    # ────────────────────────────────────────────────────────────────────────
    # Phase 4 — additional store-type templates. Each follows the same
    # heading→fields pattern as the event template so the existing
    # questionnaire engine (prefill, locked, send-email) keeps working.
    # ────────────────────────────────────────────────────────────────────────

    "fundraiser_web_store_setup": {
        "name": "Fundraiser Web Store Setup Questionnaire",
        "description": "Intake form for setting up a fundraiser web store (campaigns, profit-share, donation goals).",
        "category": "web_stores",
        "questions": [
            # Section 1 — Contact & Cause
            {"type": "heading", "label": "Contact and Cause", "order": 0},
            {"type": "text",     "label": "Customer Name",                "required": True, "order": 1},
            {"type": "text",     "label": "Organization / Cause Name",                   "order": 2},
            {"type": "phone",    "label": "Phone Number",                 "required": True, "order": 3},
            {"type": "email",    "label": "Email Address",                "required": True, "order": 4},
            {"type": "text",     "label": "Main decision-maker for this fundraiser",     "order": 5},

            # Section 2 — Fundraiser Goals
            {"type": "heading",  "label": "Fundraiser Goals",                            "order": 6},
            {"type": "text",     "label": "Fundraiser Name", "required": True, "order": 7},
            {"type": "textarea", "label": "What is the money being raised for?",         "order": 8},
            {"type": "number",   "label": "Fundraiser Goal Amount ($)",                  "order": 9},
            {"type": "date",     "label": "Fundraiser Start Date",                       "order": 10},
            {"type": "date",     "label": "Fundraiser End Date",                         "order": 11},
            {"type": "select",   "label": "Should a progress bar be shown publicly?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"}
            ], "order": 12},
            {"type": "select",   "label": "Show total amount raised publicly?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"}
            ], "order": 13},

            # Section 3 — Products & Profit Share
            {"type": "heading",  "label": "Products and Profit Share", "order": 14},
            {"type": "checkbox", "label": "Which products do you want to sell?", "required": True, "options": [
                {"value": "tshirts",   "label": "T-shirts"},
                {"value": "hoodies",   "label": "Hoodies"},
                {"value": "yard_signs","label": "Yard signs"},
                {"value": "banners",   "label": "Banners"},
                {"value": "decals",    "label": "Decals / stickers"},
                {"value": "bags",      "label": "Bags"},
                {"value": "other",     "label": "Other"}
            ], "order": 15},
            {"type": "select",   "label": "Profit allocation type", "options": [
                {"value": "percentage",     "label": "Percentage of each sale"},
                {"value": "fixed_per_item", "label": "Fixed dollar amount per item"},
                {"value": "manual",         "label": "Manual — decide after the store closes"}
            ], "order": 16},
            {"type": "number",   "label": "Profit allocation percentage (%)",          "order": 17},
            {"type": "number",   "label": "Fixed profit allocation amount per item ($)","order": 18},
            {"type": "select",   "label": "Allow checkout donations?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"}
            ], "order": 19},
            {"type": "text",     "label": "Suggested donation amounts at checkout",
             "description": "e.g., $5, $10, $25 — leave blank to allow any amount.",   "order": 20},

            # Section 4 — Branding
            {"type": "heading",  "label": "Branding",                                  "order": 21},
            {"type": "file_upload", "label": "Upload your logo / artwork",
             "accept_file_types": ["image/*", ".pdf", ".svg", ".ai", ".eps", ".zip"],
             "max_file_size_mb": 25,                                                    "order": 22},
            {"type": "text",     "label": "Brand colors",                              "order": 23},
            {"type": "textarea", "label": "Storefront welcome message",                "order": 24},

            # Section 5 — Stripe Connect
            {"type": "heading",  "label": "Stripe Connect Payment Setup",              "order": 25},
            {"type": "paragraph","label": "Payments will be processed via Stripe Connect so funds can be paid out directly to the fundraiser bank account. We will email a secure setup link.", "order": 26},
            {"type": "text",     "label": "Legal name or business name for payouts",   "order": 27},
            {"type": "email",    "label": "Best email to receive the Stripe Connect setup link", "order": 28},
            {"type": "select",   "label": "Do you already have a Stripe account?", "options": [
                {"value": "yes",       "label": "Yes"},
                {"value": "no",        "label": "No"},
                {"value": "not_sure",  "label": "Not sure"}
            ], "order": 29},

            # Section 6 — Final approval & signature
            {"type": "heading",   "label": "Final Approval and Signature",             "order": 30},
            {"type": "checkbox",  "label": "I understand the store will be built from the info provided and that missing details may delay launch.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 31},
            {"type": "text",      "label": "Customer Name",  "required": True,         "order": 32},
            {"type": "signature", "label": "Customer Signature", "required": True,     "order": 33},
            {"type": "date",      "label": "Date",           "required": True,         "order": 34},
        ],
    },

    "team_school_web_store_setup": {
        "name": "Team / School Web Store Setup Questionnaire",
        "description": "Intake form for team, school, or organisation merch stores (uniforms, spirit wear, recurring rosters).",
        "category": "web_stores",
        "questions": [
            # Section 1 — Contact & Organisation
            {"type": "heading", "label": "Contact and Organisation",                   "order": 0},
            {"type": "text",     "label": "Customer Name",                "required": True, "order": 1},
            {"type": "text",     "label": "Team / School / Organisation Name",
             "required": True, "order": 2},
            {"type": "phone",    "label": "Phone Number",                 "required": True, "order": 3},
            {"type": "email",    "label": "Email Address",                "required": True, "order": 4},
            {"type": "text",     "label": "Main contact / coach / advisor role",       "order": 5},

            # Section 2 — Season / Program
            {"type": "heading",  "label": "Season and Program",                        "order": 6},
            {"type": "text",     "label": "Sport / Program Name", "required": True,    "order": 7},
            {"type": "select",   "label": "Store type", "options": [
                {"value": "one_season", "label": "One-season store"},
                {"value": "year_round", "label": "Year-round store"},
                {"value": "tournament", "label": "Tournament / event store"}
            ], "order": 8},
            {"type": "date",     "label": "Store Open Date",                           "order": 9},
            {"type": "date",     "label": "Store Close Date",                          "order": 10},
            {"type": "textarea", "label": "Roster details (sizes, names, numbers)",
             "description": "Optional — you can also upload a roster file below.",    "order": 11},
            {"type": "file_upload", "label": "Upload roster file (CSV / PDF)",
             "accept_file_types": [".csv", ".pdf", ".xlsx", ".xls"],
             "max_file_size_mb": 10,                                                   "order": 12},

            # Section 3 — Products & Personalisation
            {"type": "heading",  "label": "Products and Personalisation",              "order": 13},
            {"type": "checkbox", "label": "Which products do you want available?", "required": True, "options": [
                {"value": "tshirts",     "label": "T-shirts"},
                {"value": "hoodies",     "label": "Hoodies"},
                {"value": "jerseys",     "label": "Jerseys"},
                {"value": "warmups",     "label": "Warm-up gear"},
                {"value": "hats",        "label": "Hats"},
                {"value": "polos",       "label": "Polos / coach shirts"},
                {"value": "spirit_wear", "label": "Spirit wear (parents, family)"},
                {"value": "bags",        "label": "Bags / backpacks"},
                {"value": "other",       "label": "Other"}
            ], "order": 14},
            {"type": "select",   "label": "Allow names on items?", "options": [
                {"value": "yes",     "label": "Yes"},
                {"value": "no",      "label": "No"},
                {"value": "roster",  "label": "Only from roster list"}
            ], "order": 15},
            {"type": "select",   "label": "Allow numbers on items?", "options": [
                {"value": "yes",     "label": "Yes"},
                {"value": "no",      "label": "No"},
                {"value": "roster",  "label": "Only from roster list"}
            ], "order": 16},
            {"type": "textarea", "label": "Personalisation rules / restrictions",      "order": 17},

            # Section 4 — Branding
            {"type": "heading",  "label": "Branding",                                  "order": 18},
            {"type": "file_upload", "label": "Upload logo, mascot, or design files",
             "accept_file_types": ["image/*", ".pdf", ".svg", ".ai", ".eps", ".zip"],
             "max_file_size_mb": 25,                                                   "order": 19},
            {"type": "text",     "label": "Primary team / school colors",              "order": 20},
            {"type": "textarea", "label": "Spirit slogan, hashtag, or extra text",     "order": 21},

            # Section 5 — Fulfillment
            {"type": "heading",  "label": "Fulfillment",                               "order": 22},
            {"type": "select",   "label": "How should orders be delivered?", "options": [
                {"value": "individual_shipping", "label": "Individual shipping to each customer"},
                {"value": "bulk_to_coach",       "label": "Bulk to coach / organiser"},
                {"value": "pickup_school",       "label": "Pickup at school / facility"},
                {"value": "pickup_shop",         "label": "Pickup at our shop"}
            ], "order": 23},
            {"type": "select",   "label": "Bag and label each order by athlete?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"}
            ], "order": 24},

            # Section 6 — Stripe Connect
            {"type": "heading",  "label": "Stripe Connect Payment Setup",              "order": 25},
            {"type": "paragraph","label": "Online payments are processed via Stripe Connect, paying out directly to your team / school / booster bank account.", "order": 26},
            {"type": "text",     "label": "Legal name / organisation for payouts",     "order": 27},
            {"type": "email",    "label": "Best email to receive the Stripe Connect setup link", "order": 28},

            # Section 7 — Final approval
            {"type": "heading",   "label": "Final Approval and Signature",             "order": 29},
            {"type": "checkbox",  "label": "I have authority to set up this store on behalf of the team / school / organisation.", "required": True, "options": [
                {"value": "agree", "label": "I confirm"}
            ], "order": 30},
            {"type": "text",      "label": "Customer Name",  "required": True,         "order": 31},
            {"type": "signature", "label": "Customer Signature", "required": True,     "order": 32},
            {"type": "date",      "label": "Date",           "required": True,         "order": 33},
        ],
    },

    "business_web_store_setup": {
        "name": "Business / Company Web Store Setup Questionnaire",
        "description": "Intake form for B2B / company / employee branded merch stores.",
        "category": "web_stores",
        "questions": [
            # Section 1 — Contact & Company
            {"type": "heading", "label": "Contact and Company",                        "order": 0},
            {"type": "text",     "label": "Customer Name",                "required": True, "order": 1},
            {"type": "text",     "label": "Company / Business Name",      "required": True, "order": 2},
            {"type": "phone",    "label": "Phone Number",                 "required": True, "order": 3},
            {"type": "email",    "label": "Email Address",                "required": True, "order": 4},
            {"type": "text",     "label": "Job title / role of main contact",          "order": 5},
            {"type": "text",     "label": "Approximate number of employees / customers", "order": 6},

            # Section 2 — Store Purpose
            {"type": "heading",  "label": "Store Purpose",                             "order": 7},
            {"type": "checkbox", "label": "What is this store mainly for?", "options": [
                {"value": "employee_apparel", "label": "Employee apparel / uniforms"},
                {"value": "customer_swag",    "label": "Customer-facing swag / merch"},
                {"value": "promo_events",     "label": "Tradeshow / promo events"},
                {"value": "client_gifts",     "label": "Client gifts"},
                {"value": "internal_only",    "label": "Internal-only / private store"}
            ], "order": 8},
            {"type": "select",   "label": "Should the store be public or private?", "required": True, "options": [
                {"value": "public",  "label": "Public — anyone with the link"},
                {"value": "private", "label": "Private — only invited users"}
            ], "order": 9},
            {"type": "select",   "label": "How often will products change?", "options": [
                {"value": "static",   "label": "Static catalog — rarely changes"},
                {"value": "seasonal", "label": "Updated each season"},
                {"value": "rotating", "label": "Frequently rotating"}
            ], "order": 10},

            # Section 3 — Products
            {"type": "heading",  "label": "Products",                                  "order": 11},
            {"type": "checkbox", "label": "Which product types do you need?", "required": True, "options": [
                {"value": "tshirts",    "label": "T-shirts"},
                {"value": "polos",      "label": "Polos / button-downs"},
                {"value": "hoodies",    "label": "Hoodies / outerwear"},
                {"value": "uniforms",   "label": "Branded uniforms"},
                {"value": "hats",       "label": "Hats"},
                {"value": "drinkware",  "label": "Drinkware / tumblers"},
                {"value": "bags",       "label": "Bags / backpacks"},
                {"value": "tech",       "label": "Tech accessories"},
                {"value": "signs",      "label": "Signs / banners"},
                {"value": "other",      "label": "Other"}
            ], "order": 12},
            {"type": "textarea", "label": "Any size, color, or stock requirements?",   "order": 13},
            {"type": "select",   "label": "Do you want to allow custom embroidery / names per order?", "options": [
                {"value": "yes",   "label": "Yes"},
                {"value": "no",    "label": "No"}
            ], "order": 14},

            # Section 4 — Branding
            {"type": "heading",  "label": "Branding",                                  "order": 15},
            {"type": "file_upload", "label": "Upload logo, brand guidelines, mockups",
             "accept_file_types": ["image/*", ".pdf", ".svg", ".ai", ".eps", ".zip"],
             "max_file_size_mb": 25,                                                   "order": 16},
            {"type": "text",     "label": "Brand colors",                              "order": 17},
            {"type": "text",     "label": "Approved fonts (if any)",                   "order": 18},
            {"type": "textarea", "label": "Storefront welcome message",                "order": 19},

            # Section 5 — Fulfillment & Billing
            {"type": "heading",  "label": "Fulfillment and Billing",                   "order": 20},
            {"type": "select",   "label": "Who pays for items in this store?", "options": [
                {"value": "employees",        "label": "Employees pay themselves"},
                {"value": "company",          "label": "Company pays everything"},
                {"value": "company_subsidy",  "label": "Company subsidises part of the price"},
                {"value": "department_codes", "label": "Department / cost code billing"}
            ], "order": 21},
            {"type": "select",   "label": "How should items be delivered?", "options": [
                {"value": "individual_shipping", "label": "Ship to each employee individually"},
                {"value": "bulk_to_hr",          "label": "Bulk shipment to HR / office"},
                {"value": "pickup_office",       "label": "Pickup at office"},
                {"value": "pickup_shop",         "label": "Pickup at our shop"}
            ], "order": 22},
            {"type": "textarea", "label": "Special billing or PO requirements",        "order": 23},

            # Section 6 — Stripe Connect
            {"type": "heading",  "label": "Stripe Connect Payment Setup",              "order": 24},
            {"type": "paragraph","label": "Stripe Connect handles online payments and pays out directly to the bank account you choose.", "order": 25},
            {"type": "text",     "label": "Legal business name for payouts",           "order": 26},
            {"type": "email",    "label": "Best email to receive the Stripe Connect setup link", "order": 27},

            # Section 7 — Final approval
            {"type": "heading",   "label": "Final Approval and Signature",             "order": 28},
            {"type": "checkbox",  "label": "I am authorised to set up this store for the company.", "required": True, "options": [
                {"value": "agree", "label": "I confirm"}
            ], "order": 29},
            {"type": "text",      "label": "Customer Name",  "required": True,         "order": 30},
            {"type": "signature", "label": "Customer Signature", "required": True,     "order": 31},
            {"type": "date",      "label": "Date",           "required": True,         "order": 32},
        ],
    },
}
