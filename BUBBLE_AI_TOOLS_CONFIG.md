# Sign Guy AI - AI Tools Configuration

## GLOBAL CONFIGURATION

### LLM Provider
| Setting | Value |
|---------|-------|
| Provider | OpenAI (via Emergent Integrations) |
| Model | `gpt-5.2` |
| API Key Source | Environment variable `EMERGENT_LLM_KEY` |
| Library | `emergentintegrations.llm.chat` |

### Global System Message
```
You are a helpful AI assistant for Sign Guy AI, a sign shop management system.
```

### Default Model Parameters
| Parameter | Value | Notes |
|-----------|-------|-------|
| Model | `gpt-5.2` | Set via `.with_model("openai", "gpt-5.2")` |
| Temperature | Not explicitly set | Uses OpenAI default (1.0) |
| Max Tokens | Not explicitly set | Uses OpenAI default |
| Session ID | New UUID per request | `str(uuid.uuid4())` |

### Cost-Saving / Throttling Logic
- **None implemented** - Each request creates a new LlmChat session
- No rate limiting
- No token counting
- No cost tracking
- No caching of responses
- **Recommendation:** Add rate limiting, response caching, and cost tracking

---

## DATABASE STORAGE

### Collection
`ai_responses`

### Schema (AIResponse)
```python
class AIResponse(BaseModel):
    id: str                          # Auto-generated UUID
    tool: str                        # Tool identifier (e.g., "layout_generator")
    input_data: Dict[str, Any]       # Full input object sent to AI
    output: str                      # Raw AI response text
    order_id: Optional[str] = None     # Link to Job (if provided in input)
    customer_id: Optional[str] = None # Link to Customer (if provided in input)
    created_at: str                  # ISO 8601 timestamp
```

### Record Linking
- **order_id**: Extracted from `request.input_data.get("order_id")` if present
- **customer_id**: Extracted from `request.input_data.get("customer_id")` if present
- Both are optional - user can manually pass them in the input_data object
- Currently NOT automatically linked from context (user must explicitly provide IDs)

### Query Capabilities
```python
GET /api/ai/history
Parameters:
  - tool: Filter by tool type
  - order_id: Filter by linked job
  - customer_id: Filter by linked customer
Limit: 100 most recent records
Sort: created_at DESC
```

---

## AI TOOLS

---

### TOOL 1: Layout Generator

**Tool ID:** `layout_generator`

**Category:** Design

**Purpose:** Create multiple sign layout concepts with professional design guidance including text hierarchy, spacing, color recommendations, and typography.

**Icon:** Layout (lucide-react)

---

**INPUT FIELDS:**

| Field Name | Label | Type | Placeholder | Required |
|------------|-------|------|-------------|----------|
| product_type | Product Type | text | e.g., Banner, Window Sign, Vehicle Wrap | No |
| size | Size | text | e.g., 4ft x 8ft | No |
| text_content | Text Content | textarea | Main text and secondary text | No |
| colors | Colors | text | e.g., Blue, White, Gold | No |
| style | Style Preference | text | e.g., Modern, Classic, Bold | No |

**Input JSON Example:**
```json
{
  "product_type": "Banner",
  "size": "4ft x 8ft",
  "text_content": "GRAND OPENING\nJohnson's Auto Repair\nCall 555-1234",
  "colors": "Blue, White, Gold",
  "style": "Modern",
  "order_id": "optional-job-uuid",
  "customer_id": "optional-customer-uuid"
}
```

---

**SYSTEM PROMPT:**
```
You are a helpful AI assistant for Sign Guy AI, a sign shop management system.
```

**USER PROMPT TEMPLATE (verbatim):**
```
You are a sign design layout expert. Create multiple layout concepts based on the input.
Input: {input}
Provide:
1. 3 different layout concepts with text hierarchy, spacing guidance, and design rationale
2. Color recommendations based on provided colors
3. Font pairing suggestions
4. Key design principles for this type of sign
```

**Prompt Variable Substitution:**
- `{input}` → Stringified version of entire input_data object
- Additional fields from input_data available via `**request.input_data`

---

**OUTPUT FORMAT:**

Plain text response containing:
1. **3 Layout Concepts** - Each with:
   - Text hierarchy breakdown
   - Spacing guidance (margins, padding)
   - Design rationale
2. **Color Recommendations** - Based on input colors
3. **Font Pairing Suggestions** - Heading and body fonts
4. **Key Design Principles** - For the specific sign type

**Example Output Structure:**
```
## Layout Concept 1: Bold & Centered
[Description of layout with hierarchy]

### Text Hierarchy:
- Primary: "GRAND OPENING" - 48pt, bold, centered
- Secondary: "Johnson's Auto Repair" - 24pt, medium weight
- Tertiary: "Call 555-1234" - 18pt, regular

### Spacing:
- Top margin: 6 inches
- Between elements: 4 inches
...

## Layout Concept 2: ...
## Layout Concept 3: ...

## Color Recommendations
...

## Font Pairings
...

## Design Principles for Banners
...
```

---

### TOOL 2: Print-Ready Checklist

**Tool ID:** `print_checklist`

**Category:** Design

**Purpose:** Review designs for print production readiness and identify potential issues before production.

**Icon:** CheckSquare (lucide-react)

---

**INPUT FIELDS:**

| Field Name | Label | Type | Placeholder | Required |
|------------|-------|------|-------------|----------|
| design_description | Design Description | textarea | Describe the design, dimensions, colors, and any concerns | No |
| print_method | Print Method | text | e.g., Digital, Screen Print, Large Format | No |
| material | Material | text | e.g., Vinyl, Acrylic, Coroplast | No |

**Input JSON Example:**
```json
{
  "design_description": "4x8 vinyl banner, full color print. Red and yellow text on white background. Logo in top left. Multiple photos along bottom.",
  "print_method": "Large Format Digital",
  "material": "13oz Vinyl",
  "order_id": "optional-job-uuid"
}
```

---

**SYSTEM PROMPT:**
```
You are a helpful AI assistant for Sign Guy AI, a sign shop management system.
```

**USER PROMPT TEMPLATE (verbatim):**
```
You are a print production expert. Review this design for print-readiness.
Input: {input}
Check and report on:
1. Bleed margins (recommended 0.125" or 3mm)
2. Color contrast and accessibility
3. Text sizing and hierarchy
4. Image resolution requirements
5. File format recommendations
Provide a checklist with pass/fail status for each item.
```

---

**OUTPUT FORMAT:**

Plain text checklist with pass/fail indicators:

**Example Output Structure:**
```
## PRINT-READY CHECKLIST

### 1. Bleed Margins
Status: ⚠️ REVIEW NEEDED
- Recommended: 0.125" (3mm) bleed on all sides
- For a 4ft x 8ft banner, ensure artwork extends to 48.25" x 96.25"
- Action: Verify bleed area contains no critical content

### 2. Color Contrast and Accessibility
Status: ✅ PASS
- Red on white: High contrast ratio (~7:1)
- Yellow on white: ⚠️ May need darker shade for visibility
- Recommendation: Consider gold (#FFD700) instead of bright yellow

### 3. Text Sizing and Hierarchy
Status: ✅ PASS
- For 4x8 banner viewed at 20ft distance:
  - Primary text: Minimum 6" tall
  - Secondary text: Minimum 3" tall
  - Contact info: Minimum 2" tall

### 4. Image Resolution
Status: ⚠️ REVIEW NEEDED
- Large format requires minimum 100-150 DPI at final size
- For photos at bottom, verify source images are high resolution
- Action: Check all images are at least 150 DPI

### 5. File Format
Status: ℹ️ RECOMMENDATION
- Recommended format: PDF/X-1a or high-res PDF
- Color mode: CMYK
- Include all fonts outlined or embedded

## SUMMARY
- Items Passed: 2
- Items Need Review: 2
- Recommendations: 1
```

---

### TOOL 3: Brand Kit Generator

**Tool ID:** `brand_kit`

**Category:** Branding

**Purpose:** Create complete brand identity elements including color palettes, typography, taglines, and brand guidelines for sign shop clients.

**Icon:** Palette (lucide-react)

---

**INPUT FIELDS:**

| Field Name | Label | Type | Placeholder | Required |
|------------|-------|------|-------------|----------|
| business_name | Business Name | text | Client's business name | No |
| industry | Industry | text | e.g., Restaurant, Retail, Construction | No |
| target_audience | Target Audience | text | Who are their customers? | No |
| brand_values | Brand Values/Personality | textarea | e.g., Professional, Fun, Eco-friendly, Premium | No |
| existing_colors | Existing Colors (if any) | text | Any colors they already use | No |

**Input JSON Example:**
```json
{
  "business_name": "Green Valley Landscaping",
  "industry": "Landscaping / Outdoor Services",
  "target_audience": "Homeowners ages 35-65, mid to high income, suburban areas",
  "brand_values": "Eco-friendly, Professional, Trustworthy, Family-owned",
  "existing_colors": "Green",
  "customer_id": "optional-customer-uuid"
}
```

---

**SYSTEM PROMPT:**
```
You are a helpful AI assistant for Sign Guy AI, a sign shop management system.
```

**USER PROMPT TEMPLATE (verbatim):**
```
You are a branding expert. Create a brand kit based on this input.
Input: {input}
Generate:
1. Color palette (primary, secondary, accent colors with hex codes)
2. Font pairings (heading and body fonts)
3. 5 tagline options
4. Brand voice guidelines
5. Logo usage recommendations
```

---

**OUTPUT FORMAT:**

Plain text brand kit document:

**Example Output Structure:**
```
# BRAND KIT: Green Valley Landscaping

## 1. COLOR PALETTE

### Primary Colors
- Forest Green: #228B22
  - Use for: Headers, primary buttons, logo
- Earth Brown: #8B4513
  - Use for: Accents, secondary elements

### Secondary Colors
- Sky Blue: #87CEEB
  - Use for: Backgrounds, highlights
- Cream: #FFFDD0
  - Use for: Light backgrounds, cards

### Accent Color
- Sunset Orange: #FF6B35
  - Use for: CTAs, attention-grabbing elements

## 2. FONT PAIRINGS

### Heading Font
- **Montserrat Bold**
  - Clean, professional, highly legible at large sizes
  - Perfect for signage and headers

### Body Font
- **Open Sans Regular**
  - Friendly, readable, pairs well with Montserrat
  - Use for descriptions, small text

## 3. TAGLINE OPTIONS

1. "Growing Your Outdoor Dreams"
2. "Where Nature Meets Nurture"
3. "Your Landscape, Our Passion"
4. "Rooted in Excellence"
5. "Cultivating Beautiful Spaces"

## 4. BRAND VOICE GUIDELINES

- **Tone:** Warm, professional, knowledgeable
- **Language:** Accessible, avoid jargon
- **Key phrases:** "sustainable," "family values," "trusted partner"
- **Avoid:** Overly technical terms, aggressive sales language

## 5. LOGO USAGE RECOMMENDATIONS

- Minimum size: 1" width for print
- Clear space: Equal to height of "G" in logo
- Backgrounds: Use on white, cream, or very light colors
- Never: Stretch, rotate, or modify colors
```

---

### TOOL 4: Document Creator

**Tool ID:** `document_creator`

**Category:** Business

**Purpose:** Generate professional business documents including proposals, scope of work documents, installation notes, and project briefs.

**Icon:** FileText (lucide-react)

---

**INPUT FIELDS:**

| Field Name | Label | Type | Options/Placeholder | Required |
|------------|-------|------|---------------------|----------|
| document_type | Document Type | select | proposal, scope_of_work, installation_notes, project_brief | No |
| project_name | Project Name | text | Name of the project | No |
| client_name | Client Name | text | Client's name or company | No |
| project_details | Project Details | textarea | Describe the project, deliverables, timeline, etc. | No |
| special_requirements | Special Requirements | textarea | Any special terms, conditions, or notes | No |

**Input JSON Example:**
```json
{
  "document_type": "proposal",
  "project_name": "Storefront Signage Package",
  "client_name": "Downtown Coffee Co.",
  "project_details": "Channel letter sign for storefront, 24\" tall letters, internally illuminated. Window vinyl for hours and logo. A-frame sidewalk sign.",
  "special_requirements": "Must match existing brand colors. Installation requires after-hours work. Landlord approval needed.",
  "order_id": "optional-job-uuid",
  "customer_id": "optional-customer-uuid"
}
```

---

**SYSTEM PROMPT:**
```
You are a helpful AI assistant for Sign Guy AI, a sign shop management system.
```

**USER PROMPT TEMPLATE (verbatim):**
```
You are a business document specialist for sign shops.
Input: {input}
Create a professional {document_type} document including all relevant sections.
```

**Note:** `{document_type}` is pulled from input_data via `**request.input_data`

---

**OUTPUT FORMAT:**

Varies by document_type:

**Proposal Output Structure:**
```
# PROPOSAL

## Client: Downtown Coffee Co.
## Project: Storefront Signage Package
## Date: [Current Date]
## Proposal #: [Auto-generated]

---

## EXECUTIVE SUMMARY
[Brief overview of the project and value proposition]

## SCOPE OF WORK

### Item 1: Channel Letter Sign
- Description: Illuminated channel letters, 24" tall
- Materials: Aluminum returns, acrylic faces, LED illumination
- Specifications: [Details]

### Item 2: Window Vinyl
[Details]

### Item 3: A-Frame Sign
[Details]

## TIMELINE
- Design approval: [X] business days
- Production: [X] business days
- Installation: [Date/timeframe]

## INVESTMENT
[Pricing table or summary]

## TERMS & CONDITIONS
- Payment terms
- Warranty information
- Approval process

## SPECIAL NOTES
- After-hours installation required
- Landlord approval documentation needed

## ACCEPTANCE
[Signature lines]
```

**Scope of Work Output Structure:**
```
# SCOPE OF WORK

## Project: [Name]
## Client: [Name]

## 1. PROJECT OVERVIEW
## 2. DELIVERABLES
## 3. SPECIFICATIONS
## 4. TIMELINE & MILESTONES
## 5. CLIENT RESPONSIBILITIES
## 6. EXCLUSIONS
## 7. CHANGE ORDER PROCESS
```

**Installation Notes Output Structure:**
```
# INSTALLATION NOTES

## Project: [Name]
## Location: [Address]
## Date: [Scheduled Date]

## PRE-INSTALLATION CHECKLIST
## EQUIPMENT NEEDED
## INSTALLATION STEPS
## SAFETY REQUIREMENTS
## POST-INSTALLATION
## SIGN-OFF
```

**Project Brief Output Structure:**
```
# PROJECT BRIEF

## Client: [Name]
## Project: [Name]

## BACKGROUND
## OBJECTIVES
## TARGET AUDIENCE
## KEY MESSAGES
## DELIVERABLES
## CONSTRAINTS
## SUCCESS METRICS
```

---

### TOOL 5: Overdue Payment Assistant

**Tool ID:** `overdue_assistant`

**Category:** Business

**Purpose:** Draft professional collection reminder messages for overdue invoices with appropriate tone based on days overdue.

**Icon:** AlertCircle (lucide-react)

---

**INPUT FIELDS:**

| Field Name | Label | Type | Placeholder | Required |
|------------|-------|------|-------------|----------|
| client_name | Client Name | text | Client's name | No |
| invoice_amount | Invoice Amount | text | e.g., $1,500.00 | No |
| days_overdue | Days Overdue | text | e.g., 15 | No |
| invoice_details | Invoice Details | textarea | What was the invoice for? | No |
| previous_attempts | Previous Contact Attempts | textarea | Have you already reached out? | No |

**Input JSON Example:**
```json
{
  "client_name": "ABC Construction",
  "invoice_amount": "$2,450.00",
  "days_overdue": "30",
  "invoice_details": "Channel letter sign installation at 123 Main St, completed October 15",
  "previous_attempts": "Sent invoice on Oct 20, reminder email on Nov 5, no response",
  "customer_id": "optional-customer-uuid"
}
```

---

**SYSTEM PROMPT:**
```
You are a helpful AI assistant for Sign Guy AI, a sign shop management system.
```

**USER PROMPT TEMPLATE (verbatim):**
```
You are a collections specialist for sign shops. Analyze this overdue invoice.
Input: {input}
Provide:
1. A professional reminder message (email format)
2. Suggested follow-up actions
3. Timeline recommendations
```

---

**OUTPUT FORMAT:**

Plain text with email and recommendations:

**Example Output Structure:**
```
## PROFESSIONAL REMINDER MESSAGE

Subject: Invoice #[INV-XXXX] - Payment 30 Days Past Due - ABC Construction

---

Dear ABC Construction Team,

I hope this message finds you well. I'm reaching out regarding invoice #[INV-XXXX] in the amount of $2,450.00 for the channel letter sign installation at 123 Main St, which was completed on October 15.

This invoice is now 30 days past the original due date, and we have not yet received payment or communication regarding any issues.

**Invoice Details:**
- Amount Due: $2,450.00
- Original Due Date: [Date]
- Days Overdue: 30

We value our business relationship and want to resolve this matter promptly. If there are any concerns about the work performed or questions about the invoice, please don't hesitate to reach out.

**Payment Options:**
- Check: [Mailing address]
- Credit Card: Call [phone] or pay online at [URL]
- Bank Transfer: Contact us for details

Please remit payment within the next 7 business days or contact us to discuss alternative arrangements.

Thank you for your prompt attention to this matter.

Best regards,
[Your Name]
Sign Guy AI
[Phone] | [Email]

---

## SUGGESTED FOLLOW-UP ACTIONS

1. **Immediate (Day 1-3)**
   - Send this email
   - Log attempt in customer notes
   - Set reminder for follow-up

2. **If No Response (Day 7)**
   - Phone call to accounts payable
   - Request to speak with decision maker

3. **Escalation (Day 14)**
   - Send formal demand letter via certified mail
   - Consider payment plan offer

4. **Final Steps (Day 30+)**
   - Final notice with collection warning
   - Consult with collections agency or attorney

## TIMELINE RECOMMENDATIONS

| Day | Action |
|-----|--------|
| 0 | Send this email |
| 3 | Follow-up phone call |
| 7 | Second email if no response |
| 14 | Certified mail / formal demand |
| 21 | Payment plan offer |
| 30 | Collection escalation decision |

## NOTES
- Previous contact attempts: 2 (email only)
- Recommendation: Switch to phone contact
- Tone: Firm but professional given 30-day status
```

---

### TOOL 6: Design Intake Chat

**Tool ID:** `design_intake`

**Category:** Customer

**Purpose:** Extract structured project requirements from unstructured customer conversations, creating a formatted job ticket.

**Icon:** MessageSquare (lucide-react)

---

**INPUT FIELDS:**

| Field Name | Label | Type | Placeholder | Required |
|------------|-------|------|-------------|----------|
| conversation | Customer Conversation | textarea | Paste or describe the conversation with the customer about their sign needs | No |
| additional_context | Additional Context | textarea | Any other relevant information | No |

**Input JSON Example:**
```json
{
  "conversation": "Customer called asking about getting a sign for their new restaurant. They want something that lights up and can be seen from the street. The restaurant is called 'Mama's Kitchen' and they're going for an Italian feel. They mentioned they like red and green colors. The sign would go above the entrance which is about 15 feet wide. They need it done before their grand opening on December 15th. Budget is around $3000-4000.",
  "additional_context": "Referred by Downtown Coffee Co. First-time customer.",
  "customer_id": "optional-customer-uuid"
}
```

---

**SYSTEM PROMPT:**
```
You are a helpful AI assistant for Sign Guy AI, a sign shop management system.
```

**USER PROMPT TEMPLATE (verbatim):**
```
You are a design intake specialist for sign shops. Based on this conversation:
Input: {input}
Extract and structure:
1. Product type
2. Dimensions
3. Text content
4. Color preferences
5. Logo requirements
6. Special requests
7. Deadline
Format as a structured job ticket.
```

---

**OUTPUT FORMAT:**

Structured job ticket:

**Example Output Structure:**
```
# JOB TICKET - Design Intake

## CLIENT INFORMATION
- Customer: [To be created]
- Referral Source: Downtown Coffee Co.
- Contact Status: First-time customer

---

## 1. PRODUCT TYPE
**Primary:** Illuminated Channel Letters
**Alternatives to Consider:**
- Cabinet sign with internal lighting
- Neon-style LED letters

## 2. DIMENSIONS
- **Available Space:** 15 feet wide (entrance width)
- **Recommended Letter Height:** 18-24 inches
- **Estimated Sign Width:** 10-12 feet (to fit "Mama's Kitchen")
- **Note:** Site survey recommended to confirm measurements

## 3. TEXT CONTENT
**Primary Text:** Mama's Kitchen
**Secondary Text:** None specified
**Font Style:** Consider Italian/script style fonts
- Suggestions: Pacifico, Great Vibes, Allura

## 4. COLOR PREFERENCES
**Stated:** Red and Green (Italian theme)
**Recommended Palette:**
- Primary: Italian Red (#CD212A)
- Accent: Italian Green (#008C45)
- Background/Trim: White or cream

## 5. LOGO REQUIREMENTS
**Status:** Not discussed
**Action Needed:** 
- [ ] Ask if they have an existing logo
- [ ] Offer logo design services if needed

## 6. SPECIAL REQUESTS
- Must be illuminated ("lights up")
- Must be visible from street
- Italian aesthetic feel

## 7. DEADLINE
**Hard Deadline:** December 15 (Grand Opening)
**Working Backwards:**
- Installation: Dec 13-14
- Production: Dec 1-12 (12 days)
- Design Approval: Nov 25-30
- Design Presentation: Nov 20-24
- **TODAY:** Begin design concepts

## 8. BUDGET
**Stated Range:** $3,000 - $4,000
**Assessment:** 
- Budget is tight for illuminated channel letters
- May need to discuss:
  - Cabinet sign alternative (more affordable)
  - Scaled-down letter count
  - Payment plan options

---

## RECOMMENDED NEXT STEPS

1. [ ] Create customer record
2. [ ] Schedule site visit for measurements
3. [ ] Request logo files (if available)
4. [ ] Prepare 2-3 design concepts within budget
5. [ ] Send quote with options

## QUESTIONS TO CLARIFY

1. Do you have a logo, or do you need one designed?
2. What are your business hours? (for lighting timer)
3. Is the mounting surface stucco, brick, or other?
4. Do you need permits? (we can help with this)

---

*Generated from customer conversation on [date]*
*Ready for order creation*
```

---

## API ENDPOINTS

### Generate AI Content

**Endpoint:** `POST /api/ai/generate`

**Request Model:**
```python
class AIRequest(BaseModel):
    tool: str                    # Tool ID (e.g., "layout_generator")
    input_data: Dict[str, Any]   # Input fields object
```

**Request Example:**
```json
{
  "tool": "layout_generator",
  "input_data": {
    "product_type": "Banner",
    "size": "4ft x 8ft",
    "text_content": "GRAND OPENING",
    "colors": "Blue, White",
    "style": "Modern",
    "order_id": "abc-123",
    "customer_id": "xyz-789"
  }
}
```

**Response Model:**
```python
class AIResponse(BaseModel):
    id: str                          # UUID of this response
    tool: str                        # Tool that was used
    input_data: Dict[str, Any]       # Echo of input
    output: str                      # AI-generated content
    order_id: Optional[str]            # Linked job (if provided)
    customer_id: Optional[str]       # Linked customer (if provided)
    created_at: str                  # ISO timestamp
```

**Response Example:**
```json
{
  "id": "resp-uuid-here",
  "tool": "layout_generator",
  "input_data": { ... },
  "output": "## Layout Concept 1: Bold & Centered\n...",
  "order_id": "abc-123",
  "customer_id": "xyz-789",
  "created_at": "2024-12-15T10:30:00Z"
}
```

**Error Responses:**
- `400`: Unknown tool ID
- `500`: AI service not configured (missing API key)
- `500`: AI generation failed (API error)

---

### Get AI History

**Endpoint:** `GET /api/ai/history`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| tool | string | Filter by tool ID |
| order_id | string | Filter by linked job |
| customer_id | string | Filter by linked customer |

**Response:** Array of AIResponse objects (max 100, sorted by created_at DESC)

**Example:**
```
GET /api/ai/history?tool=brand_kit&customer_id=xyz-789
```

---

## IMPLEMENTATION DETAILS

### Code Location
**File:** `/app/backend/server.py`
**Lines:** 1403-1511

### Prompt Construction Flow
```python
# 1. Get template for tool
prompt_template = tool_prompts.get(request.tool)

# 2. Substitute variables
prompt = prompt_template.format(
    input=str(request.input_data),  # Full input as string
    **request.input_data             # Individual fields for {field_name}
)

# 3. Create chat instance
chat = LlmChat(
    api_key=api_key,
    session_id=str(uuid.uuid4()),
    system_message="You are a helpful AI assistant for Sign Guy AI..."
).with_model("openai", "gpt-5.2")

# 4. Send message and get response
user_message = UserMessage(text=prompt)
response = await chat.send_message(user_message)
```

### Database Write
```python
ai_response = AIResponse(
    tool=request.tool,
    input_data=request.input_data,
    output=response,
    order_id=request.input_data.get("order_id"),      # Optional link
    customer_id=request.input_data.get("customer_id")  # Optional link
)
doc = ai_response.model_dump()
await db.ai_responses.insert_one(doc)
```

---

## SUMMARY TABLE

| Tool ID | Name | Category | Input Fields | Links To |
|---------|------|----------|--------------|----------|
| layout_generator | Layout Generator | Design | 5 fields | Job, Customer |
| print_checklist | Print-Ready Checklist | Design | 3 fields | Job, Customer |
| brand_kit | Brand Kit Generator | Branding | 5 fields | Job, Customer |
| document_creator | Document Creator | Business | 5 fields | Job, Customer |
| overdue_assistant | Overdue Payment Assistant | Business | 5 fields | Job, Customer |
| design_intake | Design Intake Chat | Customer | 2 fields | Job, Customer |

---

## LIMITATIONS & RECOMMENDATIONS

### Current Limitations
1. **No rate limiting** - Vulnerable to abuse
2. **No token counting** - No cost visibility
3. **No caching** - Duplicate requests re-run
4. **No streaming** - Full response wait
5. **Single model** - No fallback
6. **No context** - Each request is isolated
7. **Manual linking** - Job/Customer IDs must be explicitly provided

### Recommended Improvements
1. Add rate limiting (requests per minute per user)
2. Implement token counting and cost tracking
3. Cache identical requests for 24 hours
4. Add streaming for better UX
5. Add model fallback (if gpt-5.2 fails, try gpt-4)
6. Auto-link to current job/customer from frontend context
7. Add temperature control per tool (lower for documents, higher for creative)
8. Add max_tokens limits per tool
9. Store token usage in AIResponse for billing
