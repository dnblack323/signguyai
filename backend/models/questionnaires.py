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
            
            # Section 5: Stripe Connect Payment Setup
            {"type": "heading", "label": "Stripe Connect Payment Setup", "order": 44},
            {"type": "paragraph", "label": "To allow payments from this web store to go directly to your bank account, we use Stripe Connect. You will receive a secure setup link where you can enter your business, identity, tax, and banking information directly through Stripe.\n\nWe do not collect or store your full bank account information through this form. Stripe may require verification before payouts can begin.\n\nThe store may accept payments before payouts are fully available, but funds cannot be sent to your bank account until Stripe Connect setup is completed and approved.", "order": 45},
            {"type": "select", "label": "Who should receive the payments from this web store?", "options": [
                {"value": "individual", "label": "Individual"},
                {"value": "business", "label": "Business"},
                {"value": "organization", "label": "Organization"},
                {"value": "school", "label": "School / team / group"},
                {"value": "other", "label": "Other"}
            ], "order": 46},
            {"type": "text", "label": "Legal name or business name for payment account", "order": 47},
            {"type": "email", "label": "Email address to use for Stripe setup", "order": 48},
            {"type": "phone", "label": "Phone number for Stripe setup", "order": 49},
            {"type": "select", "label": "Do you already have a Stripe account?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"},
                {"value": "not_sure", "label": "Not sure"}
            ], "order": 50},
            {"type": "select", "label": "Who will complete the Stripe Connect setup?", "options": [
                {"value": "me", "label": "Me"},
                {"value": "business_owner", "label": "Business owner"},
                {"value": "treasurer", "label": "Treasurer"},
                {"value": "event_organizer", "label": "Event organizer"},
                {"value": "other", "label": "Other"}
            ], "order": 51},
            {"type": "email", "label": "Best email to receive the Stripe Connect setup link", "order": 52},
            
            # Section 6: Final Approval and Signature
            {"type": "heading", "label": "Final Approval and Signature", "order": 53},
            {"type": "text", "label": "Who should review the store before it goes live?", "order": 54},
            {"type": "select", "label": "Do you want to approve product names, pricing, images, and descriptions before launch?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ], "order": 55},
            {"type": "select", "label": "Do you want a store preview link before launch?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no", "label": "No"}
            ], "order": 56},
            
            # Final Store Setup Agreement
            {"type": "paragraph", "label": "Final Store Setup Agreement", "description": "Please read and acknowledge the following statements before signing.", "order": 57},
            {"type": "checkbox", "label": "I understand the store will be built based on the information, artwork, pricing, product details, fulfillment details, and payment information provided.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 58},
            {"type": "checkbox", "label": "I understand missing or incorrect information may delay the store launch.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 59},
            {"type": "checkbox", "label": "I understand the store will not launch until product details, pricing, artwork, fulfillment settings, and payment setup are approved.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 60},
            {"type": "checkbox", "label": "I understand changes after launch may affect orders, pricing, production timelines, customer experience, and reporting.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 61},
            {"type": "checkbox", "label": "I understand Stripe Connect setup must be completed before payouts can be sent to your bank account, and Stripe may require identity, business, tax, and banking information before payouts can begin.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 62},
            {"type": "checkbox", "label": "I understand payment processing fees and any agreed platform/store fees may be deducted from online transactions, and payouts are sent according to Stripe's payout schedule.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 63},
            {"type": "checkbox", "label": "I understand customer-provided artwork, logos, images, names, and sponsor files must be approved for use by the customer or organization submitting this form.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 64},
            {"type": "checkbox", "label": "I understand production timelines depend on final store approval, payment setup, artwork readiness, order volume, product availability, fulfillment method, and whether submitted artwork is usable for print.", "required": True, "options": [
                {"value": "agree", "label": "I understand"}
            ], "order": 65},
            
            # Signature Fields
            {"type": "text", "label": "Customer Name", "required": True, "order": 66},
            {"type": "signature", "label": "Customer Signature", "required": True, "order": 67},
            {"type": "date", "label": "Date", "required": True, "order": 68}
        ]
    }
}
