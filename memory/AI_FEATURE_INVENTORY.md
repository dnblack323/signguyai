# SignGuy AI - Complete AI Feature Inventory

**Last Updated:** December 2025  
**Source Files:** `/app/backend/routes/ai.py`, `/app/backend/services/ai_assistant_actions.py`

---

## 1. AI INFRASTRUCTURE

### Backend Services
| File | Purpose |
|------|---------|
| `/app/backend/routes/ai.py` | Main AI routes (1889 lines) |
| `/app/backend/services/ai_assistant_actions.py` | Structured database actions |

### LLM Integration
| Provider | Model | Usage |
|----------|-------|-------|
| OpenAI | GPT-5.2 | Text generation (via Emergent LLM Key) |
| OpenAI | GPT Image 1 | Image generation (via Emergent LLM Key) |

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/generate` | POST | Text content generation |
| `/api/ai/generate-images` | POST | Image generation |
| `/api/ai/history` | GET | Generation history |
| `/api/ai/generate-product-description` | POST | Webstore product descriptions |
| `/api/ai/assistant` | POST | Business-aware AI assistant |
| `/api/ai/generate-email` | POST | Email composition |
| `/api/ai/assistant/action` | POST | Structured database actions |
| `/api/ai/assistant/action/confirm` | POST | Confirm pending actions |
| `/api/ai/assistant/actions/audit` | GET | Action audit log |
| `/api/ai/assistant/actions/pending` | GET | Pending confirmations |
| `/api/ai/assistant/actions/types` | GET | Available action types |

---

## 2. TEXT GENERATION TOOLS (29 Tools)

### Content Creation
| Tool ID | Name | Description |
|---------|------|-------------|
| `blog_creator` | Blog Creator | SEO-optimized blog articles |
| `completed_job_post` | Completed Job Post | Social media posts for finished work |
| `showcase_post` | Showcase Post | Social media showcase content |
| `social_pack_generator` | Social Pack | Multiple social media post ideas |
| `social_job_post` | Social Job Post | Job completion social content |

### Branding & Design
| Tool ID | Name | Description |
|---------|------|-------------|
| `idea_brainstormer` | Idea Brainstormer | Taglines, logos, names, campaigns |
| `tagline_generator` | Tagline Generator | Business taglines |
| `brand_color_advisor` | Brand Color Advisor | Color palette recommendations |
| `brand_voice_guide` | Brand Voice Guide | Communication guidelines |
| `branding_kit_generator` | Branding Kit | Complete brand system |

### Business Documents
| Tool ID | Name | Description |
|---------|------|-------------|
| `proposal_writer` | Proposal Writer | Project proposals |
| `review_responder` | Review Responder | Customer review responses |
| `email_templates` | Email Templates | Business email templates |
| `document_composer` | Document Composer | Business documents |
| `business_copywriter` | Business Copywriter | Marketing copy |

### Marketing & SEO
| Tool ID | Name | Description |
|---------|------|-------------|
| `seo_content` | SEO Content | Website content optimization |
| `content_calendar` | Content Calendar | Social media planning |
| `campaign_builder` | Campaign Builder | Marketing campaigns |

### Pricing & Business Intelligence
| Tool ID | Name | Description |
|---------|------|-------------|
| `pricing_advisor` | Pricing Advisor | Pricing recommendations |
| `pricing_intelligence` | Pricing Intelligence | Deep pricing analysis |
| `wrap_cost_calculator` | Wrap Cost Calculator | Vehicle wrap pricing |

### Design Analysis
| Tool ID | Name | Description |
|---------|------|-------------|
| `photo_enhancer` | Photo Enhancer | Print readiness analysis |
| `image_vectorizer` | Image Vectorizer | Vectorization guidance |
| `font_identifier` | Font Identifier | Typography identification |

### Regulatory
| Tool ID | Name | Description |
|---------|------|-------------|
| `permit_research` | Permit Research | Sign permit guidance |

### Product Descriptions
| Tool ID | Name | Description |
|---------|------|-------------|
| `product_description` | Product Description | E-commerce product copy |

### Racing & Motorsports (Text)
| Tool ID | Name | Description |
|---------|------|-------------|
| `race_number_designer` | Race Number Designer | Number design briefs |
| `driver_name_plate` | Driver Name Plate | Name plate specifications |
| `race_team_branding` | Race Team Branding | Team branding packages |

---

## 3. IMAGE GENERATION TOOLS (9 Tools)

| Tool ID | Name | Description |
|---------|------|-------------|
| `logo_refresher` | Logo Refresher | Modern logo redesigns |
| `generative_fill` | Generative Fill | Image expansion |
| `text_to_image` | Text to Image | Custom image generation |
| `ai_sign_designer` | AI Sign Designer | Sign mockup generation |
| `ai_banner_designer` | AI Banner Designer | Banner design generation |
| `logo_creator` | Logo Creator | New logo designs |
| `mockup_creator` | Mockup Creator | Product mockups |
| `vehicle_wrap_mockup` | Vehicle Wrap Mockup | Wrap visualization |
| `race_number_designer` | Race Number (Image) | Racing number graphics |

---

## 4. AI BUSINESS ASSISTANT

### Features
- **Business Data Aware**: Reads actual shop data (orders, customers, financials)
- **Contextual Responses**: Answers based on real business metrics
- **Session Management**: Maintains conversation context
- **Role-Based Access**: Respects user permissions

### Data Context Available
| Category | Data Points |
|----------|-------------|
| Orders | Total count, status breakdown, recent orders |
| Customers | Total count, recent customers |
| Invoices | Total, paid/unpaid, revenue totals |
| Employees | Count, recent entries |
| Time Entries | Recent logs |
| Webstores | Store count, products |

---

## 5. AI ASSISTANT STRUCTURED ACTIONS (9 Actions)

| Action | Description | Requires Confirmation |
|--------|-------------|----------------------|
| `create_job` | Create new order | No |
| `update_job_status` | Change order status | **Yes** |
| `create_calendar_event` | Schedule event | No |
| `add_material` | Add inventory item | No |
| `update_material_cost` | Change material cost | **Yes** |
| `create_invoice` | Create invoice | **Yes** |
| `assign_employee` | Assign to order | **Yes** |
| `log_time_entry` | Log work hours | No |
| `categorize_expense` | Categorize expense | No |

### Action Features
- Tenant scoped
- Permission checked
- Audit logged
- Confirmation flow for destructive actions

---

## 6. AI EMAIL COMPOSER

### Features
- Email template generation
- Tone customization
- Multiple template types
- Professional formatting

### Template Types
- Follow-up emails
- Quote emails
- Thank you emails
- Payment reminders
- Custom emails

---

## 7. FEATURE GATING BY PLAN

### AI Tools Access
| Plan | AI Access | Text Gen | Image Gen | Monthly Limit |
|------|-----------|----------|-----------|---------------|
| OS Starter | ✅ | ✅ | ❌ | 25 |
| OS Pro | ✅ | ✅ | ✅ | 100 |
| OS Business | ✅ | ✅ | ✅ | Unlimited |
| WS Launch | ❌ | ❌ | ❌ | 0 |
| WS Growth | ❌ | ❌ | ❌ | 0 |
| WS Scale | ❌ | ❌ | ❌ | 0 |
| AI Basic | ✅ | ✅ | ❌ | 25 |
| AI Pro | ✅ | ✅ | ✅ | 100 |
| AI Max | ✅ | ✅ | ✅ | Unlimited |

### AI Assistant Access
| Plan | Assistant | Queries/Mo | Business Data |
|------|-----------|------------|---------------|
| OS Starter | ✅ | 10 | ❌ |
| OS Pro | ✅ | 50 | Limited |
| OS Business | ✅ | Unlimited | Full |
| AI Basic | ✅ | 10 | ❌ |
| AI Pro | ✅ | 50 | ❌ |
| AI Max | ✅ | Unlimited | ❌ |

### Business-Only Features
| Feature | Required Plan |
|---------|---------------|
| Branding Kit Generator | OS Business / AI Max |
| Campaign Builder | OS Business / AI Max |
| Pricing Intelligence | OS Business / AI Max |
| Content Calendar | OS Business / AI Max |

---

## 8. FRONTEND AI COMPONENTS

| Component | File | Purpose |
|-----------|------|---------|
| AITools | `/pages/AITools.js` | Main AI tools page |
| AIAssistant | `/pages/AIAssistant.js` | Business assistant chat |
| AIEmailComposer | `/components/AIEmailComposer.js` | Email composition |
| DocsAITools | `/pages/docs/DocsAITools.js` | AI documentation |

### Marketing Pages
| Page | Route | Product |
|------|-------|---------|
| AIStudioPage | `/ai-studio` | AI Studio product overview |
| AIBasicPage | `/ai-basic` | AI Basic plan details |
| AIProPage | `/ai-pro` | AI Pro plan details |
| AIMaxPage | `/ai-max` | AI Max plan details |

---

## 9. DATA STORAGE

### Collections
| Collection | Purpose |
|------------|---------|
| `ai_generations` | Text/image generation history |
| `ai_assistant_messages` | Assistant conversation history |
| `ai_action_audit` | Structured action audit log |

### Generation History Schema
```json
{
  "id": "uuid",
  "tenant_id": "string",
  "user_id": "string",
  "tool": "string",
  "input_data": {},
  "output": "string",
  "images": ["url1", "url2"],
  "created_at": "ISO datetime"
}
```

---

## 10. TEST COVERAGE

| Test File | Tests | Description |
|-----------|-------|-------------|
| `test_ai_assistant_actions.py` | 17 | Structured actions |
| `test_ai_assistant_context.py` | - | Context management |
| `test_ai_document_workflow.py` | - | Document workflows |
| `test_ai_image_tools.py` | - | Image generation |
| `test_ai_tools.py` | - | Text generation |
| `test_ai_tools_comprehensive.py` | - | Full tool coverage |
| `test_all_ai_tools.py` | - | Integration tests |
| `test_portal_documents_ai.py` | - | Portal AI features |
| `test_product_description_ai.py` | - | Product descriptions |
| `test_racing_tools.py` | - | Racing/motorsports |
| `test_timeline_ai_image.py` | - | Timeline images |

---

## 11. SUMMARY COUNTS

| Category | Count |
|----------|-------|
| Text Generation Tools | 29 |
| Image Generation Tools | 9 |
| AI Assistant Actions | 9 |
| API Endpoints | 11 |
| Frontend Pages | 5 |
| Test Files | 11 |
| **Total AI Features** | **74** |

---

*Inventory generated December 2025*
