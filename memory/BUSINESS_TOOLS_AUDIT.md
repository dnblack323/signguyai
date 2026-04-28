# Business Tools Simple Audit

**Audit Date:** 2026-04-28
**Scope:** 5 Business category tools only
**Purpose:** Review for future improvements - no code changes

---

# Tool Name: Sign Permit Research

## 1. What does this tool do?
Provides guidance on sign permit requirements for any US location. Helps shop owners understand permit rules, fees, size restrictions, and application processes before starting a project.

## 2. Where is it located?
- **Page:** AI Tools > Business
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 104-117)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["permit_research"] (line 168)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| City and State | `city_state` | text | Yes | None |
| Type of Sign | `sign_type` | select | Yes | None |
| Approximate Sign Size | `sign_size` | text | No | None |
| Location Type | `location_type` | select | No | None |
| Illumination | `illumination` | select | No | None |
| Specific Questions | `specific_questions` | textarea | No | None |

**Sign Type Options:** monument_sign, pylon_sign, channel_letters, wall_sign, awning_sign, window_graphics, a_frame_sidewalk, digital_led, banner_temporary, vehicle_wrap

**Location Type Options:** commercial_strip, shopping_center, downtown_historic, industrial, residential_area, highway_visible

**Illumination Options:** non_illuminated, internally_lit, externally_lit, led_digital, neon

## 4. How do the fields affect the AI output?
- **city_state** - Critical. Determines which regulations to reference.
- **sign_type** - Important. Different sign types have very different permit rules.
- **sign_size** - Affects size restriction guidance.
- **location_type** - Affects zoning and placement rules (historic districts have extra rules).
- **illumination** - Affects lighting restrictions, curfews, LED rules.
- **specific_questions** - Lets user ask targeted questions beyond the standard checklist.

## 5. What prompt or instructions does it send to AI?
The prompt asks the AI to act as an expert consultant on US sign permits. It provides a structured 7-section response:
1. General Permit Requirements
2. Size & Placement Regulations
3. Illumination Rules
4. Historic District Considerations
5. Application Process
6. Pro Tips
7. Resources

**Strengths:**
- Comprehensive structure
- Includes important disclaimer about verifying with local authorities
- Practical and actionable

**Issues:**
- None significant. Prompt is well-written and thorough.

## 6. What does it output?
- **Type:** Regulatory guidance / advisory text
- **Format:** Structured text with sections and bullet points
- **Length:** Medium to long (500-1000 words typically)

## 7. Where does the output go?
- Displays on screen in result area
- Saved to `ai_history` collection
- Can be copied manually (no dedicated copy button)
- Persists in history after refresh

## 8. Does it use real app/business data?
- **Customer data:** No
- **Order data:** No
- **Pricing data:** No
- **Business profile:** No
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No copy button for the result
- Could link to order if user is researching for a specific project
- No save-to-project functionality
- No integration with customer location data (could pre-fill city/state from customer record)

## 10. What would you recommend changing?
1. Add "Copy to Clipboard" button
2. Add "Save to Order Notes" option
3. Consider pre-filling city/state from active customer's address
4. Add link to actual municipal website search

---

# Tool Name: AI Business Assistant

## 1. What does this tool do?
A chat-based AI assistant that helps with sign shop operations, pricing questions, customer management, and can now create orders through conversation.

## 2. Where is it located?
- **Page:** AI Tools > Business (links to separate page)
- **Actual Page:** `/ai-assistant`
- **Frontend:** `/app/frontend/src/pages/AIAssistant.js`
- **Backend:** `/app/backend/routes/ai.py` - `/api/ai/assistant` endpoint (line 1791)
- **Note:** This is an external link tool - clicking it goes to a dedicated chat page

## 3. What input fields does it ask for?
This is a chat interface, not a form-based tool.
- **Message input:** Free-text chat message
- **Voice input:** Microphone recording (transcribed to text)

## 4. How do the fields affect the AI output?
- **Message content** - The AI responds contextually to whatever the user asks
- **Conversation history** - Previous messages provide context for follow-up questions
- **Active order draft** - If user is creating an order, extracted fields affect subsequent questions

## 5. What prompt or instructions does it send to AI?
The system prompt instructs the AI to:
- Act as a sign shop business assistant
- Have access to real shop data (customers, revenue, jobs)
- Help with pricing, operations, customer management, sales advice
- Create orders through structured conversation (NEW - added 2026-04-28)

**Order Creation Mode:**
- Detects order intent from messages
- Extracts customer name, product type, quantity, size, material, etc.
- Maintains active_order_draft state
- Only asks for missing fields

**Strengths:**
- Uses real shop data (revenue, job counts, customer info)
- Now supports order creation workflow
- Conversational and contextual

**Issues:**
- None significant after recent improvements

## 6. What does it output?
- **Type:** Conversational responses, business advice, order creation guidance
- **Format:** Chat messages (markdown supported)
- **Also returns:** `active_order_draft` object when creating orders

## 7. Where does the output go?
- Displays in chat interface
- Logged to `ai_assistant_logs` collection
- Active order draft stored in `assistant_sessions` collection
- Chat history maintained in frontend state (clears on new chat)

## 8. Does it use real app/business data?
- **Customer data:** Yes - shows top customers by revenue
- **Order data:** Yes - job counts, average values
- **Pricing data:** Indirectly through shop context
- **Business profile:** Yes - company name
- **Revenue data:** Yes - total, last 30 days, pending
- **Employee data:** Yes - team size
- **Credit balance:** Yes - checked before each message

## 9. Are there any obvious issues?
- Order drafts don't create actual orders yet (need confirmation step)
- Chat history clears when starting new chat
- No export/save chat transcript option

## 10. What would you recommend changing?
1. Add "Create Order" button to finalize order draft
2. Add chat transcript export/save
3. Add suggested follow-up questions
4. Consider showing shop data summary in sidebar

---

# Tool Name: Business Copywriter

## 1. What does this tool do?
Generates professional marketing copy for sign shops - taglines, about pages, service descriptions, emails, ads, social posts, website copy, and brochure text.

## 2. Where is it located?
- **Page:** AI Tools > Business
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 271-282)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["business_copywriter"] (line 504)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Copy Type | `copy_type` | select | No* | None |
| About the Business | `business_info` | textarea | No | None |
| Tone | `tone` | select | No | None |
| Must-Include Points | `key_points` | textarea | No | None |

*No fields are marked required in the frontend definition.

**Copy Type Options:** tagline_slogan, about_us_page, service_description, email_template, ad_copy, social_media_post, website_homepage, brochure_text

**Tone Options:** professional, casual_friendly, urgent_action, authoritative_expert, playful_fun, inspirational

## 4. How do the fields affect the AI output?
- **copy_type** - Determines format and length (taglines = multiple short options, about page = longer narrative)
- **business_info** - Core content to work with - what makes the business unique
- **tone** - Affects voice and word choice throughout
- **key_points** - Must-include items (phone numbers, offers, etc.)

## 5. What prompt or instructions does it send to AI?
The prompt instructs the AI to:
- Act as a professional marketing copywriter for sign shops
- Create polished, professional copy
- Highlight key differentiators
- Include clear calls to action
- Format appropriately for each copy type

**Specific guidance by type:**
- About Us: 200-400 words with company story, values, team
- Taglines: 5-10 options with varying lengths
- Service Descriptions: Feature-benefit focused
- Ad Copy: Attention-grabbing with urgency
- Social Posts: Platform-optimized with hashtags
- Website Copy: SEO-friendly

**Strengths:**
- Good guidance per copy type
- Covers common needs

**Issues:**
- No required fields - user could submit empty form
- Could benefit from customer/industry context

## 6. What does it output?
- **Type:** Marketing copy text
- **Format:** Formatted text, sometimes with multiple options
- **Length:** Varies by copy type (taglines short, about pages long)

## 7. Where does the output go?
- Displays on screen in result area
- Saved to `ai_history`
- Can be copied manually
- Persists in history

## 8. Does it use real app/business data?
- **Customer data:** No
- **Order data:** No
- **Business profile:** No (could use company name, services)
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No required fields - should require at least copy_type
- No copy button
- Doesn't pull business name/info from tenant settings
- No save-to-document-library option

## 10. What would you recommend changing?
1. Make `copy_type` required
2. Add "Copy to Clipboard" button
3. Pre-fill business info from tenant settings
4. Add "Save to Document Library" option
5. Add platform-specific options for social media (Instagram vs Facebook vs LinkedIn)

---

# Tool Name: Document Composer

## 1. What does this tool do?
Generates professional business documents including proposals, scope of work, payment reminder letters, thank you letters, project briefs, and installation instructions.

## 2. Where is it located?
- **Page:** AI Tools > Business
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 285-298)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["document_composer"] (line 524)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Document Type | `document_type` | select | No* | None |
| Custom Document Description | `custom_document_type` | text | No | None |
| Client/Company Name | `client_name` | text | No | None |
| Project/Invoice Details | `project_or_invoice_details` | textarea | No | None |
| Document Tone | `tone` | select | No | None |
| Your Company Name | `your_company_name` | text | No | None |

*No fields are marked required.

**Document Type Options:** proposal, scope_of_work, late_payment_reminder, final_payment_notice, collections_letter, thank_you_letter, project_brief, installation_instructions, warranty_info, other_custom

**Tone Options:** formal_professional, firm_but_polite, friendly, urgent

## 4. How do the fields affect the AI output?
- **document_type** - Critical. Completely changes document structure and content.
- **custom_document_type** - Used when "other_custom" selected
- **client_name** - Used in salutation and throughout document
- **project_or_invoice_details** - Core content - what project or what's owed
- **tone** - Affects formality and urgency
- **your_company_name** - Used in signature/letterhead

## 5. What prompt or instructions does it send to AI?
The prompt instructs the AI to:
- Act as a professional document writer for sign shops
- Create complete, ready-to-use documents
- Use appropriate business formatting
- Maintain consistent tone

**Type-specific guidance:**
- Proposals: Include scope, timeline, pricing summary, terms
- Payment Letters: Include invoice reference, amount, due date, payment options
- Thank You Letters: Express gratitude, mention project, invite future business
- Scope of Work: Detail deliverables, timeline, responsibilities, exclusions

**Strengths:**
- Good variety of document types
- Practical sign shop documents

**Issues:**
- No required fields
- Doesn't integrate with actual invoices/orders for payment letters
- No PDF export

## 6. What does it output?
- **Type:** Formal business document text
- **Format:** Structured text with letterhead-style formatting
- **Length:** Medium to long depending on document type

## 7. Where does the output go?
- Displays on screen
- Saved to `ai_history`
- Can be copied manually
- No PDF generation
- No save to Document Library

## 8. Does it use real app/business data?
- **Customer data:** No (could pull client names from customers)
- **Order data:** No (could pull invoice amounts for payment letters)
- **Business profile:** No (could pull company name)
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No required fields
- No copy button
- Doesn't integrate with real invoices (payment letters could pull invoice data)
- Doesn't pull company name from settings
- No PDF export
- No save to Document Library

## 10. What would you recommend changing?
1. Make `document_type` required
2. Add "Copy to Clipboard" button
3. Add "Export as PDF" option
4. Pre-fill company name from tenant settings
5. For payment letters: Add invoice selector to pull real invoice data
6. Add "Save to Document Library" option
7. Add "Send to Customer" option for appropriate document types

---

# Tool Name: Pricing Intelligence Assistant

## 1. What does this tool do?
Analyzes pricing for sign shop services and provides profit margin recommendations, market comparison, and pricing strategy advice.

## 2. Where is it located?
- **Page:** AI Tools > Business
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 301-313)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["pricing_intelligence"] (line 544)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Service/Product Type | `service_type` | text | No* | None |
| Specifications | `specifications` | textarea | No | None |
| Material Cost ($) | `material_cost` | text | No | None |
| Estimated Labor Hours | `labor_hours` | text | No | None |
| Current/Proposed Price ($) | `current_price` | text | No | None |

*No fields are marked required.

## 4. How do the fields affect the AI output?
- **service_type** - Determines which industry benchmarks to reference
- **specifications** - Affects complexity and pricing range
- **material_cost** - Used to calculate margin percentage
- **labor_hours** - Used to estimate labor cost
- **current_price** - Compared against calculated costs to show margin

## 5. What prompt or instructions does it send to AI?
The prompt requests a comprehensive pricing analysis with 5 sections:
1. Market Analysis (industry averages, regional factors, competitor range)
2. Cost Breakdown (material %, labor analysis, overhead suggestions)
3. Profit Margin Assessment (current margin, targets 40-60%, recommendations)
4. Pricing Strategy (volume pricing, upsells, premium positioning)
5. Recommendations (adjustments, value-adds, risks)

**Strengths:**
- Comprehensive analysis structure
- Industry-specific margin targets (40-60%)
- Practical recommendations

**Issues:**
- Doesn't integrate with Pricing Foundation settings
- Doesn't pull shop hourly rate from settings
- Analysis is AI estimate, not based on real shop data

## 6. What does it output?
- **Type:** Pricing analysis and recommendations
- **Format:** Structured text with sections
- **Length:** Medium to long

## 7. Where does the output go?
- Displays on screen
- Saved to `ai_history`
- Can be copied manually
- No save to order/quote

## 8. Does it use real app/business data?
- **Customer data:** No
- **Order data:** No
- **Pricing Foundation:** No (should integrate)
- **Shop hourly rate:** No (user must type it)
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No required fields
- Doesn't integrate with Pricing Foundation
- Doesn't know shop's actual hourly rate
- No copy button
- No way to apply pricing to an order

## 10. What would you recommend changing?
1. Make `service_type` required
2. Add "Copy to Clipboard" button
3. Pull hourly rate from tenant settings
4. Integrate with Pricing Foundation (show actual shop rates)
5. Add "Create Quote" option to generate quote from analysis
6. Consider overlap with Vehicle Wrap Cost Calculator - potentially merge or differentiate

---

# Quick Summary

## Tools That Seem Good As-Is
- **Sign Permit Research** - Well-structured, comprehensive, practical
- **AI Business Assistant** - Full-featured chat with order creation

## Tools That Need Small Cleanup
- **Business Copywriter** - Missing required fields, no copy button
- **Document Composer** - Missing required fields, no copy button, no PDF

## Tools That May Need Bigger Changes
- **Pricing Intelligence Assistant** - Should integrate with actual shop pricing data and Pricing Foundation

---

# Suggested Business Tool Structure

## Business Planning & Pricing
- Pricing Intelligence Assistant
- (Consider merging with Vehicle Wrap Cost Calculator from Racing)

## Customer Documents
- Document Composer (proposals, payment letters, thank you notes)

## Marketing Copy
- Business Copywriter (taglines, about pages, ads, social)

## Research & Compliance
- Sign Permit Research

## AI Chat
- AI Business Assistant (flagship conversational tool)

---

# Issues Summary Table

| Tool | Missing Required Fields | No Copy Button | No Real Data Integration | No Save Option |
|------|------------------------|----------------|-------------------------|----------------|
| Sign Permit Research | No | Yes | Yes | Yes |
| AI Business Assistant | N/A (chat) | N/A | No - uses real data | Partial |
| Business Copywriter | Yes | Yes | Yes | Yes |
| Document Composer | Yes | Yes | Yes | Yes |
| Pricing Intelligence | Yes | Yes | Yes | Yes |

---

# Priority Improvements

## Quick Wins (Low Effort)
1. Add required field validation to copywriter, document composer, pricing tools
2. Add copy-to-clipboard buttons to all text output tools

## Medium Effort
3. Pre-fill company name from tenant settings in document composer and copywriter
4. Add PDF export to document composer

## Higher Effort
5. Integrate Pricing Intelligence with Pricing Foundation settings
6. Add invoice selector to Document Composer for payment letters
7. Add "Create Quote" flow from Pricing Intelligence output
8. Add "Save to Document Library" across tools

---

**End of Business Tools Simple Audit**
