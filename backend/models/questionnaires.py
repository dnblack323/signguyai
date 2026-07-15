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
    depends_on: Optional[str] = None       # Question ID (set at runtime from depends_on_label)
    depends_on_label: Optional[str] = None  # Question label (resolved to ID on load)
    operator: str = "equals"  # equals, not_equals, contains, not_contains, greater_than, less_than
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
    # Contact-field markers — used by the public form to auto-wire customer name/email
    is_contact_name: Optional[bool] = None
    is_contact_email: Optional[bool] = None


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
        "description": "Tell us everything we need to set up your event store — products, artwork, pricing, fulfillment, and payment.",
        "category": "web_stores",
        "intro_text": "Complete this form so we can build your store correctly and without delays. Upload any logos, artwork, event flyers, or sponsor files. The more detail you give us, the faster and better we can get your store ready.",
        "questions": [
            # ── Section 1: Contact ──────────────────────────────────────────
            {"type": "heading", "label": "Contact and Event Details", "order": 0},
            {"type": "text",  "label": "Your Name",              "required": True, "order": 1, "is_contact_name": True},
            {"type": "text",  "label": "Organization or Business Name",            "order": 2},
            {"type": "phone", "label": "Phone Number",           "required": True, "order": 3},
            {"type": "email", "label": "Your Email",             "required": True, "order": 4, "is_contact_email": True},
            {"type": "select","label": "Best way to reach you", "options": [
                {"value": "call",  "label": "Call"},
                {"value": "text",  "label": "Text"},
                {"value": "email", "label": "Email"},
            ], "order": 5},
            {"type": "text",  "label": "Main decision-maker (if different from you)", "order": 6},

            {"type": "text",  "label": "Event Name",    "required": True, "order": 7},
            {"type": "date",  "label": "Event Date",                       "order": 8},
            {"type": "text",  "label": "Event Location",                   "order": 9},
            {"type": "textarea", "label": "Briefly describe the event",    "order": 10},
            {"type": "select","label": "Is this a one-time or recurring event?", "options": [
                {"value": "one_time",  "label": "One-time event"},
                {"value": "annual",    "label": "Annual event"},
                {"value": "seasonal",  "label": "Seasonal"},
                {"value": "recurring", "label": "Recurring"},
                {"value": "not_sure",  "label": "Not sure"},
            ], "order": 11},

            # ── Section 2: Store Setup ──────────────────────────────────────
            {"type": "heading", "label": "Store Setup and Branding", "order": 12},
            {"type": "text",  "label": "What should the store be called?", "required": True, "order": 13},
            {"type": "date",  "label": "When should the store open?",                        "order": 14},
            {"type": "date",  "label": "When should the store close?",                       "order": 15},
            {"type": "select","label": "Should the store be public or private?", "required": True, "options": [
                {"value": "public",  "label": "Public — anyone with the link can shop"},
                {"value": "private", "label": "Private — link only, not listed publicly"},
            ], "order": 16},
            {"type": "textarea", "label": "Store welcome message or event description",
             "description": "This appears at the top of your store. Keep it short and welcoming.", "order": 17},
            {"type": "text",  "label": "Brand colors to use",   "placeholder": "e.g., Navy #003366, Gold #FFD700",  "order": 18},
            {"type": "text",  "label": "Colors to avoid",                                    "order": 19},
            {"type": "file_upload", "label": "Upload logo, event flyer, or reference artwork",
             "description": "Accepted: JPG, PNG, PDF, SVG, AI, EPS, ZIP. Max 25MB.",
             "accept_file_types": ["image/*", ".pdf", ".ai", ".eps", ".svg", ".zip"],
             "max_file_size_mb": 25, "order": 20},

            # ── Section 3: Products ─────────────────────────────────────────
            {"type": "heading", "label": "Products", "order": 21},
            {"type": "checkbox", "label": "What products do you want in the store?", "required": True, "options": [
                {"value": "tshirts",     "label": "T-shirts"},
                {"value": "hoodies",     "label": "Hoodies"},
                {"value": "crewnecks",   "label": "Crewnecks"},
                {"value": "long_sleeve", "label": "Long sleeve shirts"},
                {"value": "hats",        "label": "Hats"},
                {"value": "yard_signs",  "label": "Yard signs"},
                {"value": "banners",     "label": "Banners"},
                {"value": "decals",      "label": "Decals / stickers"},
                {"value": "posters",     "label": "Posters"},
                {"value": "tumblers",    "label": "Tumblers / cups"},
                {"value": "bags",        "label": "Bags"},
                {"value": "other",       "label": "Other"},
            ], "order": 22},
            {"type": "textarea", "label": "Describe what you want on each product",
             "description": "For each item you selected, tell us what should go on it — design, placement, colors, images, text, sizes, etc. Be as specific as you like.",
             "placeholder": "T-shirts: front center logo in navy, back says 'Event 2025' in gold...\nHats: front patch with event logo, no back print...",
             "order": 23},
            {"type": "text",  "label": "Preferred apparel colors", "placeholder": "e.g., Black, Navy, Maroon", "order": 24},

            # ── Section 4: Design ───────────────────────────────────────────
            {"type": "heading", "label": "Artwork and Design", "order": 25},
            {"type": "select","label": "Do you already have finished artwork?", "required": True, "options": [
                {"value": "yes",         "label": "Yes — I will upload it"},
                {"value": "no",          "label": "No — I need a design created"},
                {"value": "partial",     "label": "Partial — I have some pieces but need help"},
            ], "order": 26},
            {"type": "file_upload", "label": "Upload your artwork files",
             "description": "Accepted: JPG, PNG, PDF, SVG, AI, EPS, ZIP. Max 25MB.",
             "accept_file_types": ["image/*", ".pdf", ".ai", ".eps", ".svg", ".zip"],
             "max_file_size_mb": 25, "order": 27,
             "conditional": {"depends_on_label": "Do you already have finished artwork?", "operator": "not_equals", "value": "no"}},

            {"type": "checkbox", "label": "What should be included on the design?", "options": [
                {"value": "event_name",     "label": "Event name"},
                {"value": "event_date",     "label": "Event date"},
                {"value": "event_location", "label": "Event location"},
                {"value": "sponsor_logos",  "label": "Sponsor logos"},
                {"value": "team_names",     "label": "Team names"},
                {"value": "memorial_name",  "label": "Memorial / honoree name"},
                {"value": "year",           "label": "Year"},
                {"value": "other_text",     "label": "Other custom text"},
            ], "order": 28,
             "conditional": {"depends_on_label": "Do you already have finished artwork?", "operator": "not_equals", "value": "yes"}},

            # Sponsor questions — only show if sponsor_logos is checked
            {"type": "file_upload", "label": "Upload sponsor logos",
             "description": "Accepted: JPG, PNG, PDF, SVG, AI, EPS, ZIP. Max 25MB.",
             "accept_file_types": ["image/*", ".pdf", ".ai", ".eps", ".svg", ".zip"],
             "max_file_size_mb": 25, "order": 29,
             "conditional": {"depends_on_label": "What should be included on the design?", "operator": "contains", "value": "sponsor_logos"}},
            {"type": "select","label": "Should sponsor logos be arranged by size or tier?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"},
            ], "order": 30,
             "conditional": {"depends_on_label": "What should be included on the design?", "operator": "contains", "value": "sponsor_logos"}},
            {"type": "textarea","label": "List sponsor priority or tier order",
             "description": "List them in order, e.g., Title Sponsor first, then Gold, Silver, etc.",
             "order": 31,
             "conditional": {"depends_on_label": "Should sponsor logos be arranged by size or tier?", "operator": "equals", "value": "yes"}},

            {"type": "select","label": "Do you need help creating the design?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"},
            ], "order": 32,
             "conditional": {"depends_on_label": "Do you already have finished artwork?", "operator": "not_equals", "value": "yes"}},

            {"type": "checkbox","label": "Design style preferences", "options": [
                {"value": "clean_simple",   "label": "Clean and simple"},
                {"value": "bold_loud",      "label": "Bold and loud"},
                {"value": "vintage",        "label": "Vintage"},
                {"value": "sporty",         "label": "Sporty"},
                {"value": "fun",            "label": "Fun / playful"},
                {"value": "elegant",        "label": "Elegant / formal"},
                {"value": "memorial",       "label": "Memorial / meaningful"},
                {"value": "racing",         "label": "Racing / motorsports"},
                {"value": "school_spirit",  "label": "School spirit"},
                {"value": "corporate",      "label": "Corporate / professional"},
            ], "order": 33},

            {"type": "select","label": "Do products need personalization?",
             "description": "e.g., name, number, team, role, date, custom text on each item", "options": [
                {"value": "yes",   "label": "Yes"},
                {"value": "no",    "label": "No"},
                {"value": "maybe", "label": "Maybe / some items"},
            ], "order": 34},
            {"type": "textarea","label": "Describe what customers should be able to personalize",
             "description": "e.g., name on back, jersey number, team name, custom message",
             "order": 35,
             "conditional": {"depends_on_label": "Do products need personalization?", "operator": "not_equals", "value": "no"}},

            # ── Section 5: Pricing & Fulfillment ───────────────────────────
            {"type": "heading","label": "Pricing and Fulfillment", "order": 36},
            {"type": "textarea","label": "Any specific pricing requirements or profit per item?",
             "description": "e.g., Add $5 profit to each shirt. Leave blank and we'll suggest pricing.", "order": 37},
            {"type": "text",  "label": "Who should receive the final order report or sales summary?", "order": 38},
            {"type": "select","label": "How should customers receive their orders?", "required": True, "options": [
                {"value": "individual_shipping", "label": "Individual shipping to each customer"},
                {"value": "pickup_event",        "label": "Pickup at the event"},
                {"value": "pickup_org",          "label": "Pickup at your location"},
                {"value": "pickup_shop",         "label": "Pickup at our shop"},
                {"value": "bulk_delivery",       "label": "Bulk delivery to organizer"},
                {"value": "not_sure",            "label": "Not sure yet"},
            ], "order": 39},
            {"type": "textarea","label": "Pickup location address or details",
             "order": 40,
             "conditional": {"depends_on_label": "How should customers receive their orders?", "operator": "contains", "value": "pickup"}},
            {"type": "textarea","label": "Pickup date and time instructions",
             "order": 41,
             "conditional": {"depends_on_label": "How should customers receive their orders?", "operator": "contains", "value": "pickup"}},
            {"type": "select","label": "Should orders be individually bagged and labeled by customer name?", "options": [
                {"value": "yes",      "label": "Yes"},
                {"value": "no",       "label": "No"},
                {"value": "not_sure", "label": "Not sure"},
            ], "order": 42},
            {"type": "select","label": "Should customers receive order confirmation emails?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"},
            ], "order": 43},

            # ── Section 6: Fundraiser (conditional) ────────────────────────
            {"type": "heading","label": "Fundraiser Settings", "order": 44},
            {"type": "select","label": "Is this store also raising funds for a cause?", "options": [
                {"value": "yes",   "label": "Yes"},
                {"value": "no",    "label": "No"},
                {"value": "maybe", "label": "Maybe / not sure"},
            ], "order": 45},

            {"type": "text","label": "Fundraiser name",
             "description": "e.g., Gala Fund, Team Spirit Fund",
             "order": 46,
             "conditional": {"depends_on_label": "Is this store also raising funds for a cause?", "operator": "equals", "value": "yes"}},
            {"type": "textarea","label": "What will the funds be used for?",
             "order": 47,
             "conditional": {"depends_on_label": "Is this store also raising funds for a cause?", "operator": "equals", "value": "yes"}},
            {"type": "number","label": "Fundraiser goal amount ($)",
             "description": "Optional — leave blank if no specific goal.",
             "order": 48,
             "conditional": {"depends_on_label": "Is this store also raising funds for a cause?", "operator": "equals", "value": "yes"}},
            {"type": "select","label": "Show a fundraiser progress bar on the store?", "options": [
                {"value": "yes",      "label": "Yes, show progress toward the goal"},
                {"value": "no",       "label": "No"},
            ], "order": 49,
             "conditional": {"depends_on_label": "Is this store also raising funds for a cause?", "operator": "equals", "value": "yes"}},
            {"type": "select","label": "Allow customers to add a donation at checkout?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"},
            ], "order": 50,
             "conditional": {"depends_on_label": "Is this store also raising funds for a cause?", "operator": "equals", "value": "yes"}},
            {"type": "text","label": "Donation amounts to offer at checkout",
             "description": "e.g., $5, $10, $25 — leave blank to allow any amount",
             "order": 51,
             "conditional": {"depends_on_label": "Allow customers to add a donation at checkout?", "operator": "equals", "value": "yes"}},
            {"type": "select","label": "Should a portion of each product sale go to the fundraiser?", "options": [
                {"value": "yes",      "label": "Yes"},
                {"value": "no",       "label": "No"},
                {"value": "not_sure", "label": "Not sure"},
            ], "order": 52,
             "conditional": {"depends_on_label": "Is this store also raising funds for a cause?", "operator": "equals", "value": "yes"}},
            {"type": "select","label": "How should the fundraiser portion be calculated?", "options": [
                {"value": "percentage",     "label": "Percentage of each sale"},
                {"value": "fixed_per_item", "label": "Fixed dollar amount per item"},
                {"value": "manual",         "label": "Manual — we decide after the store closes"},
            ], "order": 53,
             "conditional": {"depends_on_label": "Should a portion of each product sale go to the fundraiser?", "operator": "equals", "value": "yes"}},
            {"type": "number","label": "Fundraiser percentage (%)",
             "description": "e.g., 20 for 20% of each sale",
             "order": 54,
             "conditional": {"depends_on_label": "How should the fundraiser portion be calculated?", "operator": "equals", "value": "percentage"}},
            {"type": "number","label": "Fixed amount per item ($)",
             "description": "e.g., 5 for $5 per item sold",
             "order": 55,
             "conditional": {"depends_on_label": "How should the fundraiser portion be calculated?", "operator": "equals", "value": "fixed_per_item"}},

            # ── Section 7: Payment Setup ────────────────────────────────────
            {"type": "heading","label": "Payment Setup", "order": 56},
            {"type": "paragraph","label": "Payments are processed through Stripe. After you submit this form, you will receive a separate secure Stripe email to complete your payment account setup. Please check your spam folder — it sometimes ends up there. You do not need to complete Stripe setup now.", "order": 57},
            {"type": "select","label": "Who should receive payments from this store?", "options": [
                {"value": "individual",   "label": "Individual"},
                {"value": "business",     "label": "Business"},
                {"value": "organization", "label": "Organization / nonprofit"},
                {"value": "school",       "label": "School / team / group"},
                {"value": "other",        "label": "Other"},
            ], "order": 58},
            {"type": "text","label": "Legal name or business name for payment account", "order": 59},
            {"type": "select","label": "Do you already have a Stripe account?", "options": [
                {"value": "yes",      "label": "Yes"},
                {"value": "no",       "label": "No"},
                {"value": "not_sure", "label": "Not sure"},
            ], "order": 60},

            # ── Section 8: Pre-launch Approval ─────────────────────────────
            {"type": "heading","label": "Pre-Launch Approval", "order": 61},
            {"type": "paragraph","label": "Before your store goes live, we will send you a Pre-Launch Packet with product mockups, pricing, store description, and setup details for your review and approval. Nothing goes live without your sign-off.", "order": 62},
            {"type": "select","label": "Do you want to review and approve products and mockups before launch?", "required": True, "options": [
                {"value": "yes", "label": "Yes — send me the pre-launch packet first"},
                {"value": "no",  "label": "No — I trust your judgment, just launch it"},
            ], "order": 63},
            {"type": "text","label": "Who should review and approve the store before launch?",
             "description": "Name and email if different from your contact info above.", "order": 64},
            {"type": "select","label": "Do you want a private preview link to see the store before launch?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"},
            ], "order": 65},
            {"type": "textarea","label": "Anything else we should know?",
             "description": "Special requirements, hard deadlines, budget limits, important contacts, etc.", "order": 66},

            # ── Section 9: Agreement ────────────────────────────────────────
            {"type": "heading","label": "Agreement", "order": 67},
            {"type": "checkbox","label": "I understand the store will be built from the information I provided, and missing details may delay the launch.", "required": True, "options": [{"value": "agree", "label": "I understand"}], "order": 68},
            {"type": "checkbox","label": "I understand the store will not go live until products, pricing, artwork, fulfillment, and payment setup are fully approved.", "required": True, "options": [{"value": "agree", "label": "I understand"}], "order": 69},
            {"type": "checkbox","label": "I understand payment processing fees and any agreed platform fees may be deducted from transactions, and payouts follow Stripe's schedule.", "required": True, "options": [{"value": "agree", "label": "I understand"}], "order": 70},
            {"type": "checkbox","label": "I confirm I have the rights to use all artwork, logos, names, and images uploaded in this form.", "required": True, "options": [{"value": "agree", "label": "I confirm"}], "order": 71},
            {"type": "signature","label": "Type your full name as your electronic signature", "required": True, "order": 72},
            {"type": "date",     "label": "Today's Date",                                   "required": True, "order": 73},
        ],
    },
    "fundraiser_web_store_setup": {
        "name": "Fundraiser Web Store Setup Questionnaire",
        "description": "Intake form for setting up a fundraiser web store (campaigns, profit-share, donation goals).",
        "category": "web_stores",
        "questions": [
            # Section 1 — Contact & Cause
            {"type": "heading", "label": "Contact and Cause", "order": 0},
            {"type": "text",     "label": "Your Name",                    "required": True,  "order": 1, "is_contact_name": True},
            {"type": "text",     "label": "Organization / Cause Name",    "required": True,  "order": 2},
            {"type": "phone",    "label": "Phone Number",                  "required": True,  "order": 3},
            {"type": "email",    "label": "Your Email",                    "required": True,  "order": 4, "is_contact_email": True},
            {"type": "text",     "label": "Main decision-maker (if different from above)",   "order": 5},

            # Section 2 — Fundraiser Goals
            {"type": "heading",  "label": "Fundraiser Goals",                                "order": 6},
            {"type": "text",     "label": "Fundraiser Name",               "required": True, "order": 7},
            {"type": "textarea", "label": "What is the money being raised for?",             "order": 8},
            {"type": "number",   "label": "Fundraiser Goal Amount ($)",                      "order": 9},
            {"type": "date",     "label": "Fundraiser Start Date",                           "order": 10},
            {"type": "date",     "label": "Fundraiser End Date",                             "order": 11},
            {"type": "select",   "label": "Show a progress bar publicly?", "options": [
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
            {"type": "select",   "label": "How should profit be allocated?", "options": [
                {"value": "percentage",     "label": "Percentage of each sale"},
                {"value": "fixed_per_item", "label": "Fixed dollar amount per item"},
                {"value": "manual",         "label": "We'll decide after the store closes"}
            ], "order": 16},
            {"type": "number",   "label": "Profit percentage (%)",
             "description": "e.g., 20 for 20% of each sale.",
             "conditional": {"depends_on_label": "profit_allocation_type", "operator": "equals", "value": "percentage"},
             "order": 17},
            {"type": "number",   "label": "Fixed profit amount per item ($)",
             "description": "e.g., 5 for $5 per item sold.",
             "conditional": {"depends_on_label": "profit_allocation_type", "operator": "equals", "value": "fixed_per_item"},
             "order": 18},
            {"type": "select",   "label": "Allow customers to add a donation at checkout?", "options": [
                {"value": "yes", "label": "Yes"},
                {"value": "no",  "label": "No"}
            ], "order": 19},
            {"type": "text",     "label": "Suggested donation amounts",
             "description": "e.g., $5, $10, $25 — leave blank to allow any amount.",   "order": 20},

            # Section 4 — Branding
            {"type": "heading",  "label": "Branding",                                  "order": 21},
            {"type": "file_upload", "label": "Upload your logo / artwork",
             "accept_file_types": ["image/*", ".pdf", ".svg", ".ai", ".eps", ".zip"],
             "max_file_size_mb": 25,                                                    "order": 22},
            {"type": "text",     "label": "Brand colors (e.g., Navy blue and gold)",   "order": 23},
            {"type": "textarea", "label": "Welcome message for your storefront",
             "description": "Shown at the top of your store. Keep it short and friendly.", "order": 24},

            # Section 5 — Payout Setup
            {"type": "heading",  "label": "Payout Setup",                              "order": 25},
            {"type": "paragraph","label": "Funds are paid out directly to your bank via Stripe. We will email you a secure setup link — no banking info is collected here.", "order": 26},
            {"type": "text",     "label": "Legal name or organization name for payouts", "required": True, "order": 27},
            {"type": "select",   "label": "Do you already have a Stripe account?", "options": [
                {"value": "yes",       "label": "Yes"},
                {"value": "no",        "label": "No"},
                {"value": "not_sure",  "label": "Not sure"}
            ], "order": 28},

            # Section 6 — Final Approval
            {"type": "heading",   "label": "Final Approval",                           "order": 29},
            {"type": "checkbox",  "label": "I understand the store will be built from the information provided, and that missing details may delay the launch.", "required": True, "options": [
                {"value": "agree", "label": "I understand and agree"}
            ], "order": 30},
            {"type": "signature", "label": "Type your full name as your electronic signature", "required": True, "order": 31},
            {"type": "date",      "label": "Today's Date",  "required": True,          "order": 32},
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
