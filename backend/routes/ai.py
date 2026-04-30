"""
AI Tools Routes

This module contains routes for AI-powered tools:
- Text content generation (GPT-5.2)
- Image generation (GPT Image 1)
- AI history
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Request, UploadFile, File
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import asyncio
import logging
import uuid
import os
import base64
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

from server import db, get_current_active_user
from models import UserInDB
from services.credit_service import preview_credit_usage, deduct_credits_after_success, log_failed_ai_usage

router = APIRouter(prefix="/ai", tags=["AI Tools"])

# Get API key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')


# ============== MODELS ==============

class AIGenerateRequest(BaseModel):
    tool: str
    input_data: Dict[str, Any]


class AIGenerateImageRequest(BaseModel):
    tool: str
    input_data: Dict[str, Any]
    image_count: int = 3


class AIHistoryEntry(BaseModel):
    id: str
    tool: str
    input_data: Dict[str, Any]
    output: Optional[str] = None
    images: Optional[List[str]] = None
    created_at: str
    tenant_id: str


# ============== TOOL PROMPTS ==============

TOOL_PROMPTS = {
    # NEW TOOLS - Blog Creator
    "blog_creator": """You are an expert content writer specializing in the sign and graphics industry. Create a comprehensive blog article based on:

**Topic Source:** {topic_type}
**Specific Topic:** {topic}
**Topic Area (for suggestions):** {topic_area}
**Target Length:** {article_length}
**Writing Tone:** {tone}
**Target Reader:** {target_audience}
**Call to Action:** {include_cta}
**SEO Keywords:** {seo_keywords}

If the user selected "suggest_topics_for_me", first provide 5 topic suggestions for the topic area, then write about the most compelling one.

Create a complete blog article including:

1. **SEO-Optimized Title** - Engaging, keyword-rich title (under 60 characters)
2. **Meta Description** - 150-160 character summary for search engines
3. **Introduction** - Hook the reader, introduce the topic
4. **Main Body** - Well-structured with H2 headers, practical information, examples
5. **Conclusion** - Summary and call to action
6. **Suggested Image Descriptions** - 2-3 image ideas for the post

The article should:
- Be written for the sign/graphics industry context
- Include practical, actionable information
- Use the specified tone throughout
- Naturally incorporate SEO keywords if provided
- End with the specified call to action

Format the article with clear headers and easy-to-scan structure.""",

    # NEW TOOLS - Completed Order Post Creator
    # Merged 2026-04: now supports both image-based and text-only modes (was a
    # duplicate of social_job_post). post_mode = "with_image" | "text_only".
    "completed_job_post": """You are a social media expert for sign shops. Create engaging social media content for a completed order.

**Post Mode:** {post_mode}
**Job Type:** {job_type}
**Order / Project Description:** {job_description}
**Order Details:** {job_details}
**Client Industry:** {client_industry}
**Platform:** {platforms}
**Post Style:** {post_style}
**Brand Voice:** {brand_voice}
**Include Hashtags:** {include_hashtags}

If post_mode is "with_image", an image of the completed work has been attached — analyze it and reference visible details (colors, materials, surface, environment) in the caption.
If post_mode is "text_only", base the post entirely on the description above.

Produce:

1. **Primary Post Caption** (length tuned to the chosen platform):
   - Hook in the first line
   - Describe the work and what makes it stand out
   - Match the requested post style and brand voice
   - Single clear call to action

2. **Alternative Caption** — same content, shorter or different angle.

3. **Hashtag Set** (only if requested):
   - Industry hashtags
   - Local / service-area placeholder hashtags
   - 1–2 trending relevant hashtags
   - Suggested branded hashtag

4. **Posting Tips**:
   - Best time to post for this content
   - Story / Reel idea
   - Engagement prompt to add in first comment

Keep client confidentiality — describe the industry, never the client name.
Avoid generic AI fluff. Match the brand voice exactly.""",

    # Original NEW TOOLS
    "idea_brainstormer": """You are a creative brainstorming expert for sign shops and their clients. Generate creative ideas based on:

**Request Type:** {brainstorm_type}
**Business/Brand:** {business_name}
**Industry:** {industry}
**Target Audience:** {target_audience}
**Key Values/USP:** {key_values}
**Desired Tone:** {tone}
**Competitors:** {competitors}
**Differentiation / What makes this brand different:** {differentiation}
**Things to Avoid:** {avoid}

Use competitors and differentiation to make the ideas distinctive — avoid sounding like the listed competitors and lean into what makes this brand different.

Based on the request type, provide:

**For Taglines/Slogans:**
- Generate 15 unique taglines ranging from clever to straightforward
- Include a mix of: punny/wordplay, emotional appeal, benefit-focused, and action-oriented
- Note which ones work best on signage (short, readable)

**For Logo Concepts:**
- Describe 8-10 unique logo concept ideas with specific visual elements
- Include icon/symbol suggestions, typography styles, and color recommendations
- Note which concepts would work well at various sizes

**For Business Names:**
- Generate 15 creative business name options
- Include domain availability suggestions (.com alternatives)
- Mix of: descriptive, abstract, invented words, and combinations

**For Campaign Ideas:**
- Provide 5 detailed campaign concepts with themes, taglines, and visual directions

**For Product Names:**
- Generate 12 product name options with explanations

**For Event Themes:**
- Provide 8 creative event theme ideas with visual direction

Format with clear headers, bullet points, and brief explanations for each idea.""",

    "permit_research": """You are an expert consultant on sign permits and regulations in the United States. Provide helpful guidance on:

**Location:** {city_state}
**Sign Type:** {sign_type}
**Sign Size:** {sign_size}
**Location Type:** {location_type}
**Illumination:** {illumination}
**Specific Questions:** {specific_questions}

Provide comprehensive guidance including:

1. **General Permit Requirements**
   - Whether permits are typically required for this sign type in this area
   - Typical permit fees range (if known for this municipality)
   - Common application requirements (site plans, drawings, etc.)

2. **Size & Placement Regulations**
   - Typical size restrictions for this sign type and zoning
   - Setback requirements from property lines and roads
   - Height restrictions
   - Coverage/density limitations

3. **Illumination Rules**
   - Regulations specific to the illumination type requested
   - Brightness restrictions, timing curfews
   - Digital/LED sign regulations if applicable

4. **Historic District Considerations** (if applicable)
   - Additional review processes
   - Design restrictions
   - Material requirements

5. **Application Process**
   - Typical steps to apply
   - Review timeline expectations
   - Who to contact (planning dept, building dept, etc.)

6. **Pro Tips**
   - Common reasons permits get denied
   - Tips for faster approval
   - Variance process if needed

7. **Resources**
   - Suggest searching for "[City] sign ordinance" or "[City] municipal code signs"
   - Note that regulations change - recommend verifying with local authorities

**IMPORTANT DISCLAIMER:** Note that this is general guidance only. Regulations vary significantly and change frequently. Always verify current requirements directly with the local planning or building department before proceeding.

Be helpful, thorough, and practical. If you're not sure about specific regulations for this location, say so and provide general guidance instead.""",

    # Pricing Advisor Tool
    "pricing_advisor": """You are an expert pricing advisor for a sign shop. Analyze this pricing and provide smart recommendations.

**Current Pricing:**
- Category: {category}
- Quantity: {quantity}
- Current Price: ${current_price:.2f}
- Production Cost: ${production_cost:.2f}
- Profit Margin: {profit_margin}%
- Complexity: {complexity}/10

**Breakdown:**
{breakdown}

Provide 4-5 concise, actionable recommendations:

1. **Pricing Assessment**: Is this price competitive for a sign shop? Too high/low?
2. **Quantity Optimization**: Would different quantities unlock better pricing tiers?
3. **Margin Analysis**: Is the margin healthy for this type of work? Industry target is 40-60%.
4. **Upsell Opportunities**: What add-ons could increase the order value?
5. **Quick Win**: One immediate adjustment that could improve profitability.

Keep each point to 1-2 sentences. Be practical and sign-shop specific. Include specific dollar amounts where relevant.""",

    # Design Tools
    "photo_enhancer": """You are an expert photo analyst for a sign shop. Analyze the uploaded image and provide:
1. **Print Readiness Assessment**: Resolution quality, color depth, potential issues for large format printing
2. **Enhancement Recommendations**: Specific adjustments needed (brightness, contrast, saturation, sharpening)
3. **Color Profile Analysis**: CMYK conversion concerns, color accuracy for signage
4. **Scaling Recommendations**: How well it will scale for the intended use ({output_type})
5. **Technical Fixes Needed**: Any artifacts, noise, or quality issues to address

Enhancement goals from user: {enhancement_notes}

Be specific and actionable in your recommendations.""",

    "image_vectorizer": """You are a vectorization expert for a sign shop. Analyze this image and provide:
1. **Vectorization Complexity Score**: 1-10 scale with explanation
2. **Recommended Approach**: Best vectorization method for this image type ({image_type})
3. **Color Analysis**: Number of colors detected, recommended color reduction to {num_colors}
4. **Problem Areas**: Parts that will be difficult to vectorize (gradients, fine details, textures)
5. **Production Tips**: Specific advice for cutting/printing this as a vector
6. **Estimated Time**: How long manual cleanup might take

Provide practical, shop-floor advice.""",

    "font_identifier": """You are a typography expert for a sign shop. Analyze the text in this image:

Text visible: {text_sample}

Provide:
1. **Primary Font Identification**: Your best guess at the font family and weight
2. **Similar Alternatives**: 3-5 similar fonts that could substitute (include free options)
3. **Font Characteristics**: Serif/sans-serif, weight, style, x-height analysis
4. **Sign Shop Recommendations**: Best fonts for similar looks that cut/print well
5. **Licensing Notes**: Any concerns about font licensing for commercial sign work

Be specific about font names and where to find them.""",

    "ai_sign_designer": """You are a senior sign designer. Produce a concise design brief (NOT a marketing essay) for this sign concept:

Business: {business_name}
Type: {business_type}
Sign Type: {sign_type}
Size: {size}
Colors: {colors}
Additional Text: {additional_text}
Style: {style_preference}

Format the brief with these exact sections (use markdown headers):

### Design Direction
2–3 sentences describing the look and feel.

### Colors & Layout
- Specific color recommendations (with hex if you can infer them) and where each color goes.
- Recommended layout / hierarchy (headline, sub-text, logo, etc.).

### Readability Notes
- Minimum letter height for the stated size and viewing distance.
- Font weight / contrast advice.
- Any text that should be cut or shortened.

### Production Considerations
- Recommended fabrication method for this sign type.
- Material / finish suggestions.
- Lighting or mounting notes if relevant.

### Customer-Facing Summary
A single short paragraph (2–3 sentences) the shop can paste into an email or proposal to describe the concept to the customer.

Keep the entire brief under ~250 words. Plain language, no fluff.""",

    "ai_banner_designer": """You are a senior banner designer. Produce a concise design brief (NOT a marketing essay) for this banner concept:

Headline: {headline}
Supporting Text: {subtext}
Size: {banner_size}
Purpose: {event_type}
Colors: {brand_colors}
Style: {style}

Format the brief with these exact sections (use markdown headers):

### Design Direction
2–3 sentences describing the look and feel.

### Colors & Layout
- Specific color recommendations and where each color goes.
- Recommended hierarchy: headline / sub-text / CTA / logo.

### Readability Notes
- Minimum letter height for the stated banner size and a typical viewing distance.
- Font weight / contrast advice.
- Any text that should be cut or shortened.

### Production Considerations
- Recommended material (13oz vinyl, mesh, blockout, etc.) for the stated purpose.
- Hemming / grommet / pole-pocket guidance.
- Indoor vs outdoor / weather notes if relevant.

### Customer-Facing Summary
A single short paragraph (2–3 sentences) the shop can paste into an email or proposal to describe the concept to the customer.

Keep the entire brief under ~250 words. Plain language, no fluff.""",

    # Branding Tools
    "tagline_generator": """Generate 10 unique, memorable taglines for a sign shop client:

Business Name: {business_name}
Industry: {industry}
Values/USP: {key_values}
Target Audience: {target_audience}
Tone: {tone}

Provide taglines that are:
- Concise (under 8 words preferred)
- Memorable and catchy
- Relevant to the industry
- Easy to read on signage

Format as a numbered list with brief explanations for each.""",

    "brand_color_advisor": """As a brand color expert, recommend colors for:

Business: {business_name}
Industry: {industry}
Personality: {brand_personality}
Existing Colors: {existing_colors}

Provide:
1. **Primary Color Recommendation**: Hex code + psychology explanation
2. **Secondary Colors**: 2-3 complementary colors with hex codes
3. **Accent Color**: For CTAs and highlights
4. **Color Combinations**: How to use them together on signage
5. **What to Avoid**: Colors that don't work for this brand
6. **Sign-Specific Tips**: How these colors will look on different sign types""",

    "brand_voice_guide": """Create a brand voice guide for:

Business: {business_name}
Industry: {industry}
Target Audience: {target_audience}
Personality Traits: {personality_traits}
Competitors: {competitors}

Provide:
1. **Voice Characteristics**: 3-5 defining traits
2. **Tone Guidelines**: How to sound in different contexts
3. **Word Choice**: Words to use vs. avoid
4. **Sample Messages**: Examples for signs, social media, customer communication
5. **Sign Copy Guidelines**: Specific advice for signage text""",

    # Business Tools
    "proposal_writer": """Write a professional sign project proposal:

Client: {client_name}
Project: {project_description}
Services: {services_included}
Timeline: {timeline}
Special Requirements: {special_requirements}

Create a compelling, professional proposal that:
- Opens with understanding their needs
- Details the scope of work
- Highlights your expertise
- Addresses timeline and process
- Ends with a clear call to action

Keep it concise but comprehensive.""",

    "review_responder": """Write a professional response to this customer review:

Review Text: {review_text}
Rating: {star_rating} stars
Customer Name: {customer_name}
Response Tone: {response_tone}

Guidelines:
- Thank them for feedback
- Address specific points mentioned
- Be professional and genuine
- If negative, offer resolution without being defensive
- Keep it concise (2-3 paragraphs max)""",

    "email_templates": """Create {num_templates} professional email templates for a sign shop:

Template Type: {template_type}
Business Name: {business_name}
Tone: {tone}

For each template provide:
- Subject line options (2-3)
- Email body with [PLACEHOLDER] tags for customization
- Best practices note for that template type""",

    "seo_content": """Write SEO-optimized content for a sign shop website:

Page Type: {page_type}
Primary Keyword: {primary_keyword}
Secondary Keywords: {secondary_keywords}
Location: {service_area}
Services: {services}
Word Count Target: {word_count}

Include:
- SEO-optimized title and meta description
- H1 and H2 headers with keywords
- Natural keyword integration
- Local SEO elements
- Call to action""",

    # Marketing Tools
    "showcase_post": """Create a social media post showcasing a completed sign project:

Project Description: {job_description}
Job Type: {job_type}
Client Industry: {client_industry} (don't mention specific names)
Target Platform: {platforms}

Create:
- Engaging caption that showcases the work
- Relevant hashtags (10-15)
- Call to action
- Keep client confidentiality (no names unless approved)""",

    "social_pack_generator": """You are a social media strategist for a sign / graphics shop. Generate {pack_size} social media post ideas the user can drop straight into a posting calendar.

**Services Offered:** {services_offered}
**Target Platforms:** {platforms}
**Target Audience:** {target_audience}
**Brand Voice / Tone:** {brand_voice}
**Content Mix:** {content_mix}

Strict requirements:
- Honor the chosen content mix balance.
- If a single platform is specified, tailor format / length / hashtag count to that platform.
- Number every post (1, 2, 3, …).

For each post, provide on its own labeled lines:
- **Post Type:** educational / promotional / behind-the-scenes / testimonial / engagement / etc.
- **Caption:** 2–4 sentences in the requested brand voice.
- **Visual Suggestion:** a short, concrete image idea (not vague filler).
- **Best Platform:** which platform it suits best, and why in <10 words.
- **Hashtags:** 5–10 hashtags relevant to the post.

End the output with a "Quick Reuse Tips" section (3 bullets) on how to repurpose these across formats (Reel, carousel, story).""",

    "content_calendar": """You are a content planner for a sign / graphics shop. Create a structured content calendar.

**Start Date:** {start_date}
**Duration:** {date_range}
**Posting Frequency:** {post_frequency}
**Platforms:** {platforms}
**Marketing Goals:** {goals}
**Upcoming Events / Promotions:** {upcoming_events}
**Brand Voice / Tone:** {brand_voice}

Strict requirements:
- Calculate exact post dates from the start date and posting frequency.
- Format every entry as a row: `YYYY-MM-DD (Day) | Theme | Platform(s) | Post Idea | CTA`.
- Honor the duration: a 1_week plan = 7 days, 2_weeks = 14 days, 1_month = ~30 days.
- Weave in the listed upcoming events / promotions on or just before their dates.
- Vary content types (educational, promo, behind-the-scenes, customer story, engagement) so no two consecutive posts are the same type.
- Match the brand voice on every post idea.

After the day-by-day table, add:
1. **Theme Summary** — the running themes used across the period.
2. **Production Checklist** — concrete photos / graphics / videos the user needs to capture or create to execute the calendar.
3. **Optional Boosts** — 2–3 paid promotion ideas tied to the most important dates.""",

    "campaign_builder": """Design a complete marketing campaign:

Campaign Type: {campaign_type}
Goal: {campaign_goal}
Target Audience: {target_audience}
Budget: {budget_range}
Duration: {duration}

Provide:
1. Campaign Overview & Objectives
2. Target Audience Profile
3. Key Messages & Offers
4. Channel Strategy (which platforms, why)
5. Content Plan (what to create)
6. Timeline & Milestones
7. Success Metrics to Track
8. Budget Allocation Suggestions""",

    # Frontend-matching tool aliases
    "branding_kit_generator": """You are a brand strategist for sign shops. Create a complete brand system with guidelines.

**Business / Brand Name:** {business_name}
**Industry:** {industry}
**Existing Tagline:** {existing_tagline}
**Website / Social Link:** {website}
**Brand Color Preferences:** {brand_color_preferences}
**Logo Description:** {logo_description}
**Brand Personality:** {brand_tone}
**Target Audience:** {target_audience}
**Competitors:** {competitors}

Use the business name and industry as the anchor for every recommendation.
If brand colors were provided, build the palette around them; otherwise propose a fitting palette.
If an existing tagline was provided, respect it (don't replace it unless asked).

Create comprehensive branding guidelines including:

1. **Brand Overview**
   - Mission statement suggestion
   - Brand personality traits
   - Unique value proposition

2. **Color Palette**
   - Primary color with hex code and usage guidelines
   - Secondary colors with hex codes
   - When to use each color

3. **Typography**
   - Primary font recommendation for headlines
   - Secondary font for body text
   - Font pairing guidelines

4. **Voice & Tone**
   - Communication style guidelines
   - Words to use/avoid
   - Sample messaging

5. **Visual Guidelines**
   - Logo usage rules
   - Spacing and sizing
   - Sign application guidelines

6. **Application Examples**
   - Business card layout
   - Sign design principles
   - Social media profile guidelines""",

    "business_copywriter": """You are a professional marketing copywriter for sign shops. Generate compelling copy:

**Copy Type:** {copy_type}
**Business Info:** {business_info}
**Tone:** {tone}
**Must-Include Points:** {key_points}

Create polished, professional copy that:
- Captures the brand voice
- Highlights key differentiators
- Includes clear calls to action
- Is appropriate for the specified format

For About Us pages: 200-400 words with company story, values, and team highlights.
For Taglines: 5-10 options with varying lengths.
For Service Descriptions: Feature-benefit focused with clear value props.
For Ad Copy: Attention-grabbing with urgency elements.
For Social Posts: Platform-optimized with hashtag suggestions.
For Website Copy: SEO-friendly with natural keyword integration.""",

    "document_composer": """You are a professional document writer for sign shop businesses. Create a well-formatted business document:

**Document Type:** {document_type}
**Custom Type (if other):** {custom_document_type}
**Client/Company Name:** {client_name}
**Project/Invoice Details:** {project_or_invoice_details}
**Tone:** {tone}
**Your Company Name:** {your_company_name}

Create a complete, professional document that:
- Uses appropriate business formatting
- Maintains consistent tone throughout
- Includes all necessary sections
- Is ready to send/use

For Proposals: Include scope, timeline, pricing summary, terms.
For Payment Letters: Include invoice reference, amount, due date, payment options.
For Thank You Letters: Express genuine gratitude, mention specific project, invite future business.
For Scope of Work: Detail deliverables, timeline, responsibilities, exclusions.""",

    "pricing_intelligence": """You are a pricing analyst for sign shops. Analyze this pricing scenario:

**Service/Product:** {service_type}
**Specifications:** {specifications}
**Material Cost:** ${material_cost}
**Labor Hours:** {labor_hours}
**Current/Proposed Price:** ${current_price}

Provide comprehensive pricing analysis:

1. **Market Analysis**
   - How this price compares to industry averages
   - Regional pricing considerations
   - Competitor pricing range

2. **Cost Breakdown**
   - Material cost percentage
   - Labor cost analysis
   - Overhead allocation suggestions

3. **Profit Margin Assessment**
   - Current margin calculation
   - Industry-standard margin targets (40-60%)
   - Recommendations for adjustment

4. **Pricing Strategy**
   - Volume pricing suggestions
   - Upsell opportunities
   - Premium positioning options

5. **Recommendations**
   - Specific pricing adjustments
   - Value-add opportunities
   - Risk factors to consider""",

    "social_job_post": """Create a social media post showcasing a completed sign project:

**Project Description:** {job_description}
**Job Type:** {job_type}
**Client Industry:** {client_industry} (don't mention specific names)
**Target Platform:** {platforms}

Create:
- Engaging caption that showcases the work
- Relevant hashtags (10-15)
- Call to action
- Keep client confidentiality (no names unless approved)""",

    # Product Description Generator for Webstores
    "product_description": """You are an expert e-commerce copywriter specializing in signs, graphics, and custom products. Generate a compelling product description for an online store.

**Product Name:** {product_name}
**Product Category:** {product_category}
**Key Features/Details:** {product_features}
**Target Audience:** {target_audience}
**Tone:** {tone}
**Price Point:** ${price} (use for positioning, don't mention directly)

Generate a product description that includes:

1. **Headline Hook** (1 sentence that grabs attention)

2. **Main Description** (2-3 paragraphs covering):
   - What the product is and its primary benefit
   - Key features and what makes it special
   - Ideal use cases or who it's perfect for
   - Quality/craftsmanship highlights

3. **Bullet Points** (5-7 key selling points)
   - Focus on benefits, not just features
   - Include emotional triggers
   - Mention any customization options

4. **Call to Action** (encouraging but not pushy)

Write in a {tone} tone. Make it persuasive, scannable, and optimized for online shopping.
Do NOT mention the price directly - let the value speak for itself.""",

    # Racing & Motorsports Tool Prompts
    "race_number_designer": """You are designing a professional racing number for motorsports.

**Race Number:** {race_number}
**Number Style:** {number_style}
**Color Scheme:** {color_scheme}
**Custom Colors:** {custom_colors}
**Background Type:** {background_type}
**Special Effects:** {effects}
**Racing Series:** {racing_series}

Create a detailed design brief describing:
1. The exact visual style of the number (font characteristics, weight, angles)
2. Color application and gradients
3. Shadow, stroke, or effect specifications
4. How it fits the racing series style
5. Production notes for vinyl cutting or printing
6. Size recommendations for different placements (door, roof, quarter panel)

Make it look fast, aggressive, and professional - perfect for race day!""",

    "driver_name_plate": """You are creating a professional driver name plate/strip for motorsports.

**Driver Name:** {driver_name}
**Plate Type:** {plate_type}
**Include Number:** {include_number}
**Race Number:** {race_number}
**Hometown:** {hometown}
**Sponsor Text:** {sponsor_text}
**Font Style:** {font_style}
**Color Scheme:** {color_scheme}
**Custom Colors:** {custom_colors}

Design specifications needed:
1. Layout and composition for the plate type
2. Typography hierarchy (name prominence, secondary info)
3. Color blocking and contrast
4. Size dimensions for standard racing applications
5. Material recommendations (vinyl, printed decal)
6. Tips for visibility at speed

Keep it professional, readable, and race-ready!""",

    "wrap_cost_calculator": """You are a vehicle wrap pricing expert. Calculate accurate pricing for this wrap job.

**VEHICLE INFORMATION:**
- Vehicle Type: {vehicle_type}
- Wrap Coverage: {wrap_coverage}
- Material Type: {wrap_type}

**JOB SPECIFICATIONS:**
- Design Complexity: {design_complexity}
- Design Services Needed: {includes_design}
- Installation Difficulty: {installation_difficulty}
- Old Wrap Removal: {removal_needed}
- Turnaround Time: {turnaround}

**PRICING INPUTS:**
- Shop Hourly Rate: ${your_hourly_rate}/hour
- Material Markup: {material_markup}%

Please provide a detailed cost breakdown:

1. **Material Costs**
   - Square footage estimate for vehicle type
   - Material cost per sq ft by type
   - Total material with markup

2. **Labor Costs**
   - Design hours (if applicable)
   - Print/production hours
   - Installation hours
   - Removal hours (if applicable)
   - Total labor cost

3. **Additional Fees**
   - Rush fees (if applicable)
   - Complexity surcharge (if applicable)

4. **Final Quote**
   - Subtotal
   - Recommended retail price
   - Suggested profit margin
   - Price range (low/mid/high)

5. **Notes**
   - What's included
   - Warranty recommendations
   - Timeline expectations

Format as a professional quote the shop owner can reference or adapt.""",

    "race_team_branding": """You are a motorsports branding expert creating a race team brand kit.

**Team Information:**
- Team Name: {team_name}
- Racing Series: {racing_series}
- Primary Number: {primary_number}
- Team Colors: {team_colors}
- Style Preference: {style_preference}
- Include Elements: {include_elements}
- Sponsor Placeholders: {sponsor_placeholders}

Create a comprehensive branding brief:

1. **Brand Identity**
   - Logo concept description
   - Typography recommendations
   - Color palette with hex codes
   - Brand personality and voice

2. **Number Design**
   - Style that matches team brand
   - Color application
   - Effect recommendations

3. **Race Car Layout**
   - Primary placement zones
   - Sponsor placement recommendations
   - Color blocking strategy

4. **Merchandise Potential**
   - T-shirt design concepts
   - Hat/cap ideas
   - Hero card layout

5. **Production Files Needed**
   - Vector logo requirements
   - Number kit specifications
   - Template sizes

Make it memorable, professional, and ready to stand out on race day!"""
}

# Product Description Styles/Tones
PRODUCT_DESCRIPTION_TONES = [
    "professional",      # Business-focused, authoritative
    "friendly",          # Approachable, conversational
    "enthusiastic",      # Energetic, exciting
    "premium",           # Luxury, high-end feel
    "technical",         # Detail-oriented, specification-focused
    "casual",            # Relaxed, everyday language
]

IMAGE_PROMPTS = {
    # NEW IMAGE TOOLS
    "logo_refresher": """Redesigned modern logo for "{business_name}".
Style direction: {style_direction}.
Elements to preserve: {keep_elements}.
Changes to make: {change_elements}.
The logo should be clean, professional, scalable, and work well on signage.
Modern logo design, vector-style appearance, clean white or transparent background.
High quality brand identity design suitable for business cards, signs, and digital use.
Single logo centered in frame, professional presentation.""",

    "generative_fill": """Expanded image with seamless continuation.
Expansion direction: {expand_direction}.
Content to generate: {content_description}.
Style matching: {style_match}.
The expanded areas should seamlessly blend with the original image.
Photorealistic continuation, matching lighting, colors, and style perfectly.
Professional quality image expansion, natural and believable result.""",

    "text_to_image": """{image_prompt}
Style: {image_style}.
Aspect ratio: {aspect_ratio}.
Color mood: {color_mood}.
High quality, professional image suitable for signage and marketing materials.
Sharp details, clean composition, visually appealing.""",

    "ai_sign_designer": """Professional photograph of a {sign_type} sign for "{business_name}" business.
Style: {style_preference}, clean professional signage photography.
Colors: {colors}.
The sign should look realistic, professionally installed, and appropriate for a {business_type}.
Additional elements: {additional_text}.
High quality, commercial photography style, daylight lighting.""",

    "ai_banner_designer": """Professional promotional banner design, {banner_size} format.
Main headline: "{headline}"
Supporting text area for: {subtext}
Style: {style}, {event_type} theme.
Colors: {brand_colors}.
Clean, readable typography, professional print-ready design.
Marketing banner suitable for outdoor or indoor display.""",

    "logo_creator": """AI-generated logo concept image for "{business_name}".
Industry: {industry}.
Logo style: {logo_type}, {style_preferences} aesthetic.
Colors: {color_preferences}.
Tagline to incorporate: {tagline}.
Icon/symbol ideas: {icon_ideas}.
The logo should be clean, memorable, and work well on signage.
Render as a flat, high-contrast logo concept on a white or transparent background — this is a raster concept image, not a final vector artwork file.
High quality logo suitable for business cards, signs, and digital use.""",

    "mockup_creator": """Realistic mockup photograph showing {product_type} in a {environment} setting.
The design shows: {design_description}.
Professional product photography, realistic lighting, natural environment integration.
The mockup should look like an actual installed sign or vehicle wrap in the real world.
High quality commercial photography style, sharp details, professional presentation.""",

    "vehicle_wrap_mockup": """Realistic vehicle wrap mockup photograph.
Vehicle type: {vehicle_type}.
Wrap coverage: {wrap_coverage}.
Business name: "{business_name}".
Design description: {design_description}.
Primary colors: {primary_colors}.
Design style: {style}.
View angle: {view_angle}.

Show a {vehicle_type} with a professional {wrap_coverage} vehicle wrap.
The wrap features {design_description} in {primary_colors} colors with a {style} aesthetic.
The vehicle should be shown from a {view_angle} angle.
Photorealistic mockup, professional vehicle wrap photography, clean background or simple environment.
The wrap should look professionally installed, with realistic reflections and contours following the vehicle body.
High quality commercial photography style suitable for client presentations.""",

    # Racing & Motorsports Image Prompts
    "race_number_designer": """Professional racing number "{race_number}" design.
Style: {number_style}, {racing_series} series aesthetic.
Colors: {color_scheme}, {custom_colors}.
Background: {background_type}.
Effects: {effects}.
Bold, aggressive racing number suitable for motorsports.
Clean graphic design, high contrast, readable at speed.
Vector-style appearance, sharp edges, professional race graphics.
The number should look fast and powerful.""",

    "driver_name_plate": """Professional motorsports driver name plate design.
Driver name: "{driver_name}"
Plate type: {plate_type}.
Number included: {include_number}, #{race_number}.
Hometown: {hometown}.
Sponsor: {sponsor_text}.
Font style: {font_style}.
Colors: {color_scheme}, {custom_colors}.
Clean racing typography, professional driver identification.
Readable name plate suitable for race car door or roof strip.
High contrast, bold text, racing aesthetic.""",

    "race_team_branding": """Professional race team branding design for "{team_name}".
Racing series: {racing_series}.
Team number: #{primary_number}.
Colors: {team_colors}.
Style: {style_preference}.
Elements: {include_elements}.
Sponsor areas: {sponsor_placeholders}.
Bold motorsports branding, aggressive racing aesthetic.
Professional race team identity, logo and number design.
Clean vector style, suitable for car graphics, merchandise, and marketing."""
}


# ============== HELPER FUNCTIONS ==============

async def generate_text_content(tool: str, input_data: Dict[str, Any]) -> str:
    """Generate text content using GPT-5.2"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContent
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Get the prompt template
    prompt_template = TOOL_PROMPTS.get(tool)
    if not prompt_template:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {tool}")

    # Tool-specific required-field validation
    if tool == "branding_kit_generator":
        if not (input_data.get("business_name") or "").strip():
            raise HTTPException(status_code=400, detail="Business / Brand Name is required")
        if not (input_data.get("industry") or "").strip():
            raise HTTPException(status_code=400, detail="Industry is required")
    
    # Handle special formatting for pricing_advisor tool
    if tool == "pricing_advisor":
        breakdown = input_data.get('breakdown', {})
        if isinstance(breakdown, dict):
            breakdown_str = "\n".join([f"- {k}: {v}" for k, v in breakdown.items()])
        else:
            breakdown_str = str(breakdown)
        input_data['breakdown'] = breakdown_str
    
    # Format the prompt with input data (excluding image_upload)
    prompt_data = {k: v if v is not None else '' for k, v in input_data.items() if k != 'image_upload'}
    try:
        prompt = prompt_template.format(**prompt_data)
    except KeyError:
        prompt = prompt_template
        for key, value in prompt_data.items():
            prompt = prompt.replace(f"{{{key}}}", str(value if value is not None else ''))
    
    # Initialize chat
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"ai_tool_{tool}_{uuid.uuid4()}",
        system_message="You are a professional assistant for a sign shop. Provide helpful, practical, and actionable advice. Format your responses clearly with headers and bullet points where appropriate."
    ).with_model("openai", "gpt-5.2")
    
    # Handle image analysis if present
    file_contents = None
    image_upload = input_data.get('image_upload')
    if image_upload and isinstance(image_upload, str):
        # Check if it's a base64 data URL
        if image_upload.startswith('data:'):
            # Extract content type and base64 data
            # Format: data:image/png;base64,XXXXXX
            try:
                header, base64_data = image_upload.split(',', 1)
                content_type = header.split(':')[1].split(';')[0]  # e.g., "image/png"
                file_contents = [FileContent(content_type=content_type, file_content_base64=base64_data)]
                prompt = f"Please analyze this uploaded image.\n\n{prompt}"
            except Exception as e:
                print(f"Error parsing image upload: {e}")
    
    # Create message with or without image
    if file_contents:
        user_message = UserMessage(text=prompt, file_contents=file_contents)
    else:
        user_message = UserMessage(text=prompt)
    
    # Send message and get response
    response = await chat.send_message(user_message)
    return response


async def generate_images(tool: str, input_data: Dict[str, Any], count: int = 3) -> List[str]:
    """Generate images using GPT Image 1"""
    from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Get the image prompt template
    prompt_template = IMAGE_PROMPTS.get(tool)
    if not prompt_template:
        raise HTTPException(status_code=400, detail=f"Tool {tool} does not support image generation")
    
    # Format the prompt
    try:
        prompt = prompt_template.format(**{k: v or '' for k, v in input_data.items()})
    except KeyError:
        prompt = prompt_template
        for key, value in input_data.items():
            prompt = prompt.replace(f"{{{key}}}", str(value or ''))
    
    # Initialize image generator
    image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
    
    # Generate images
    images_base64 = []
    for i in range(count):
        try:
            images = await image_gen.generate_images(
                prompt=prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            if images and len(images) > 0:
                image_base64 = base64.b64encode(images[0]).decode('utf-8')
                images_base64.append(f"data:image/png;base64,{image_base64}")
        except Exception as e:
            print(f"Error generating image {i+1}: {e}")
            continue
    
    return images_base64


# ============== ROUTES ==============

@router.post("/generate")
async def generate_ai_content(
    request: Request,
    data: AIGenerateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate AI text content"""
    from services.multi_product_gate import get_multi_product_feature_gate
    # Check feature access
    gate = get_multi_product_feature_gate(db)
    await gate.require_feature(current_user.tenant_id, "ai_tools", "text_generation")

    preview = await preview_credit_usage(db, current_user.tenant_id, data.tool)
    if not preview["sufficient_credits"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")
    
    try:
        result = await generate_text_content(data.tool, data.input_data)
        credit_result = await deduct_credits_after_success(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type=data.tool,
            module="AI Tools",
            feature_name=data.tool,
            metadata={"tool": data.tool, **(data.input_data or {})},
        )
        
        # Save to history
        history_entry = {
            "id": str(uuid.uuid4()),
            "tool": data.tool,
            "input_data": data.input_data,
            "output": result,
            "images": None,
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "credits_used": credit_result["credit_cost"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.ai_history.insert_one(history_entry)
        
        return {"content": result, "id": history_entry["id"], "credits_used": credit_result["credit_cost"]}
    except HTTPException:
        raise
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type=data.tool,
            module="AI Tools",
            feature_name=data.tool,
            metadata={"tool": data.tool},
        )
        print(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/generate-images")
async def generate_ai_images(
    request: Request,
    data: AIGenerateImageRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate AI images"""
    from services.multi_product_gate import get_multi_product_feature_gate
    # Check feature access
    gate = get_multi_product_feature_gate(db)
    await gate.require_feature(current_user.tenant_id, "ai_tools", "image_generation")

    preview = await preview_credit_usage(db, current_user.tenant_id, data.tool)
    if not preview["sufficient_credits"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")
    
    try:
        images = await generate_images(data.tool, data.input_data, data.image_count)
        
        if not images:
            raise HTTPException(status_code=500, detail="No images were generated")

        # For design tools that have a paired text prompt, also generate a short
        # design brief alongside the images (no extra credit charge — bundled).
        design_brief = None
        if data.tool in ("ai_sign_designer", "ai_banner_designer", "race_team_branding"):
            try:
                design_brief = await generate_text_content(data.tool, data.input_data)
            except Exception as brief_err:
                # Don't fail the whole image generation if the brief errors —
                # the user still gets the images.
                print(f"Design brief generation failed for {data.tool}: {brief_err}")

        credit_result = await deduct_credits_after_success(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type=data.tool,
            module="AI Tools",
            feature_name=data.tool,
            metadata={"tool": data.tool, "image_count": data.image_count, **(data.input_data or {})},
        )
        
        # Save to history
        history_entry = {
            "id": str(uuid.uuid4()),
            "tool": data.tool,
            "input_data": data.input_data,
            "output": design_brief,
            "images": images,
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "credits_used": credit_result["credit_cost"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.ai_history.insert_one(history_entry)
        
        return {
            "images": images,
            "design_brief": design_brief,
            "id": history_entry["id"],
            "credits_used": credit_result["credit_cost"],
        }
    except HTTPException:
        raise
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type=data.tool,
            module="AI Tools",
            feature_name=data.tool,
            metadata={"tool": data.tool, "image_count": data.image_count},
        )
        print(f"AI image generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.get("/history")
async def get_ai_history(
    tool: Optional[str] = None,
    limit: int = 20,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Get AI generation history"""
    query = {"tenant_id": current_user.tenant_id}
    if tool:
        query["tool"] = tool
    
    history = await db.ai_history.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return history


# ============== PRODUCT DESCRIPTION GENERATOR ==============

class ProductDescriptionRequest(BaseModel):
    """Request model for generating product descriptions"""
    product_name: str
    product_category: str = "Other"
    product_features: str = ""  # Key features, materials, dimensions, etc.
    target_audience: str = "general consumers"
    tone: str = "professional"  # professional, friendly, enthusiastic, premium, technical, casual
    price: float = 0.0


class ProductDescriptionResponse(BaseModel):
    """Response model for product descriptions"""
    description: str
    headline: str
    bullet_points: List[str]
    call_to_action: str


@router.post("/generate-product-description")
async def generate_product_description(
    request: Request,
    data: ProductDescriptionRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Generate an AI-powered product description for webstore products.
    
    This endpoint creates compelling, e-commerce optimized product descriptions
    including headlines, bullet points, and calls to action.
    """
    from services.multi_product_gate import get_multi_product_feature_gate
    
    # Check feature access
    gate = get_multi_product_feature_gate(db)
    await gate.require_feature(current_user.tenant_id, "ai_tools", "text_generation")
    await gate.require_feature(current_user.tenant_id, "ai_tools", "monthly_generations", increment_usage=True)
    
    # Validate tone
    valid_tones = ["professional", "friendly", "enthusiastic", "premium", "technical", "casual"]
    tone = data.tone.lower() if data.tone.lower() in valid_tones else "professional"
    
    try:
        # Prepare input data for the template
        input_data = {
            "product_name": data.product_name,
            "product_category": data.product_category,
            "product_features": data.product_features or "Standard quality product",
            "target_audience": data.target_audience or "general consumers",
            "tone": tone,
            "price": data.price if data.price > 0 else "competitive",
        }
        
        preview = await preview_credit_usage(db, current_user.tenant_id, "product_description")
        if not preview["sufficient_credits"]:
            raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

        # Generate using existing infrastructure
        result = await generate_text_content("product_description", input_data)
        credit_result = await deduct_credits_after_success(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="product_description",
            module="Products",
            feature_name="product_description",
            metadata=input_data,
        )
        
        # Parse the response to extract structured data
        parsed = parse_product_description(result)
        
        # Save to history
        history_entry = {
            "id": str(uuid.uuid4()),
            "tool": "product_description",
            "input_data": input_data,
            "output": result,
            "images": None,
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "credits_used": credit_result["credit_cost"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.ai_history.insert_one(history_entry)
        
        return {
            "description": result,
            "headline": parsed.get("headline", ""),
            "bullet_points": parsed.get("bullet_points", []),
            "call_to_action": parsed.get("call_to_action", ""),
            "id": history_entry["id"]
        }
    except HTTPException:
        raise
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="product_description",
            module="Products",
            feature_name="product_description",
            metadata={"product_name": data.product_name},
        )
        print(f"Product description generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate product description: {str(e)}")


def _clean_markdown_line(value: str) -> str:
    return value.strip().strip('*').strip('"').strip()


def _extract_headline(lines: list[str]) -> str:
    fallback = ""
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if "headline" in line.lower() and index + 1 < len(lines):
            return _clean_markdown_line(lines[index + 1])
        if line and not line.startswith('#') and not line.startswith('*') and len(line) < 150 and not fallback:
            fallback = _clean_markdown_line(line)
    return fallback


def _extract_bullets(lines: list[str]) -> list[str]:
    bullets = []
    in_bullet_section = False
    for raw_line in lines:
        line = raw_line.strip()
        if "bullet" in line.lower() or "selling points" in line.lower():
            in_bullet_section = True
            continue
        if in_bullet_section and (line.startswith('#') or "call to action" in line.lower()):
            in_bullet_section = False
        if not in_bullet_section and not (line.startswith('-') or line.startswith('•')):
            continue
        if line.startswith('-') or line.startswith('•') or line.startswith('*'):
            bullet = line.lstrip('-•* ').strip()
            if bullet and len(bullet) > 10:
                bullets.append(bullet)
    return bullets


def _extract_call_to_action(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if "call to action" in line.lower() and index + 1 < len(lines):
            cta = _clean_markdown_line(lines[index + 1])
            if cta:
                return cta
    return ""


def parse_product_description(text: str) -> dict:
    """Parse the generated description to extract structured components"""
    lines = text.split('\n')
    bullets = _extract_bullets(lines)
    return {
        "headline": _extract_headline(lines),
        "bullet_points": bullets,
        "call_to_action": _extract_call_to_action(lines),
    }


# ============== AI BUSINESS ASSISTANT ==============

class AIAssistantRequest(BaseModel):
    message: str
    session_id: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    context: Optional[Dict[str, Any]] = None  # Phase 3: current page / record context


class VoiceSpeakRequest(BaseModel):
    text: str
    voice: str = "alloy"
    speed: float = 1.0


# ============== ORDER DRAFT MANAGEMENT ==============

import re

# Intent detection patterns
ORDER_INTENT_PATTERNS = [
    r'\b(make|create|start|new|add|open)\b.*\b(order|quote|job)\b',
    r'\border\b.*\bfor\b',
    r'\bquote\b.*\bfor\b',
    r'\bjob\b.*\bfor\b',
    r'\bneed\b.*\b(sign|banner|wrap|vinyl|lettering|decal|graphic)\b',
    r'\bwant\b.*\b(sign|banner|wrap|vinyl|lettering|decal|graphic)\b',
]

# Field extraction patterns
QUANTITY_PATTERNS = [
    r'^(\d+)$',  # Just a number as standalone response
    r'(\d+)\s*(sign|banner|piece|unit|item|set|pair|each|qty|quantity)',
    r'(qty|quantity|need|want|order)\s*[:\s]*(\d+)',
    r'(\d+)\s*of\s*them',
]

SIZE_PATTERNS = [
    r'(\d+)\s*(?:x|by|×)\s*(\d+)',  # 18x24, 18 by 24
    r"(\d+)['\"]?\s*(?:x|by|×)\s*(\d+)['\"]?",  # 18"x24"
    r'(\d+)\s*(?:inch|in|ft|foot|feet)',
]

MATERIAL_KEYWORDS = [
    'coroplast', 'aluminum', 'aluminium', 'acm', 'dibond', 'pvc', 'foam', 'foamcore',
    'acrylic', 'wood', 'mdo', 'plywood', 'sintra', 'styrene', 'metal', 'steel',
    'magnetic', 'vinyl', 'banner', 'mesh', 'canvas', 'fabric', 'polyester',
]

PRODUCT_KEYWORDS = [
    'sign', 'signs', 'banner', 'banners', 'yard sign', 'yard signs', 'step sign', 'step signs',
    'a-frame', 'a frame', 'sandwich board', 'channel letter', 'channel letters',
    'vehicle wrap', 'car wrap', 'truck wrap', 'van wrap', 'wrap', 'wraps',
    'decal', 'decals', 'sticker', 'stickers', 'vinyl', 'lettering', 'window graphic',
    'wall graphic', 'floor graphic', 'poster', 'posters', 'real estate sign',
    'political sign', 'campaign sign', 'election sign', 'monument sign',
]

SIDES_KEYWORDS = {
    'single': ['single', 'single-sided', 'single sided', 'one side', '1 side', 'one-sided'],
    'double': ['double', 'double-sided', 'double sided', 'both sides', '2 side', 'two-sided', 'two sides'],
}


def detect_order_intent(message: str) -> bool:
    """Detect if user wants to create an order/quote/job"""
    message_lower = message.lower()
    for pattern in ORDER_INTENT_PATTERNS:
        if re.search(pattern, message_lower):
            return True
    return False


def extract_customer_name(message: str) -> Optional[str]:
    """Extract customer name from message"""
    # Pattern: "for [Name]" or "customer [Name]" or "[Name]'s order"
    patterns = [
        r'\bfor\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "for Donald Black"
        r'\bcustomer\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "customer Donald Black"
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s\s+(?:order|quote|job)",  # "Donald Black's order"
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            name = match.group(1).strip()
            # Filter out common false positives
            if name.lower() not in ['the', 'a', 'an', 'some', 'my', 'this', 'that']:
                return name
    return None


def extract_product_type(message: str) -> Optional[str]:
    """Extract product/item type from message, preferring longer/more specific matches"""
    message_lower = message.lower()
    # Sort by length descending to match longer phrases first (e.g., "step signs" before "signs")
    sorted_products = sorted(PRODUCT_KEYWORDS, key=len, reverse=True)
    for product in sorted_products:
        if product in message_lower:
            return product
    return None


def extract_quantity(message: str, last_question: Optional[str] = None) -> Optional[int]:
    """Extract quantity from message"""
    message_lower = message.lower().strip()
    
    # If last question was about quantity, a standalone number is likely the answer
    if last_question and 'how many' in last_question.lower():
        match = re.match(r'^(\d+)$', message_lower)
        if match:
            return int(match.group(1))
    
    for pattern in QUANTITY_PATTERNS:
        match = re.search(pattern, message_lower)
        if match:
            # Get the first numeric group
            for group in match.groups():
                if group and group.isdigit():
                    return int(group)
    return None


def extract_size(message: str) -> Optional[str]:
    """Extract size dimensions from message"""
    for pattern in SIZE_PATTERNS:
        match = re.search(pattern, message.lower())
        if match:
            groups = match.groups()
            if len(groups) >= 2:
                return f"{groups[0]}x{groups[1]}"
            return match.group(0)
    return None


def extract_material(message: str) -> Optional[str]:
    """Extract material from message"""
    message_lower = message.lower()
    for material in MATERIAL_KEYWORDS:
        if material in message_lower:
            return material
    return None


def extract_sides(message: str) -> Optional[str]:
    """Extract single/double sided from message"""
    message_lower = message.lower()
    for side_type, keywords in SIDES_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                return side_type
    return None


def get_next_missing_field(draft: dict) -> Optional[str]:
    """Determine the next field to ask about"""
    order_items = draft.get('order_items', [])
    if not order_items:
        return 'product_type'
    
    item = order_items[0]  # Focus on first item for now
    
    # Priority order for questions
    if item.get('quantity') is None:
        return 'quantity'
    if item.get('size') is None:
        return 'size'
    if item.get('material') is None:
        return 'material'
    if item.get('sides') is None:
        return 'sides'
    if item.get('design_notes') is None:
        return 'design_notes'
    if item.get('due_date') is None:
        return 'due_date'
    if item.get('delivery_method') is None:
        return 'delivery_method'
    
    return None  # All fields captured


def format_draft_for_prompt(draft: dict) -> str:
    """Format the active order draft for inclusion in the LLM prompt"""
    if not draft or draft.get('intent') != 'create_order':
        return ""
    
    lines = ["## Active Order Draft:"]
    
    if draft.get('customer_name'):
        lines.append(f"- Customer: {draft['customer_name']}")
        if draft.get('customer_id'):
            lines.append(f"  (Customer ID found: {draft['customer_id']})")
    
    order_items = draft.get('order_items', [])
    if order_items:
        item = order_items[0]
        lines.append(f"- Product Type: {item.get('product_type') or 'Not specified'}")
        if item.get('quantity'):
            lines.append(f"- Quantity: {item['quantity']}")
        if item.get('size'):
            lines.append(f"- Size: {item['size']}")
        if item.get('material'):
            lines.append(f"- Material: {item['material']}")
        if item.get('sides'):
            lines.append(f"- Sides: {item['sides']}")
        if item.get('design_notes'):
            lines.append(f"- Design Notes: {item['design_notes']}")
        if item.get('due_date'):
            lines.append(f"- Due Date: {item['due_date']}")
        if item.get('delivery_method'):
            lines.append(f"- Delivery: {item['delivery_method']}")
    
    missing = get_next_missing_field(draft)
    if missing:
        lines.append(f"\n**Next field needed: {missing}**")
    else:
        lines.append("\n**All required fields captured. Ready to confirm and create order.**")
    
    if draft.get('last_question_asked'):
        lines.append(f"\nLast question asked: \"{draft['last_question_asked']}\"")
    
    return "\n".join(lines)


async def get_or_create_assistant_session(tenant_id: str, session_id: str) -> dict:
    """Get or create an assistant session with order draft"""
    session = await db.assistant_sessions.find_one(
        {"tenant_id": tenant_id, "session_id": session_id},
        {"_id": 0}
    )
    if not session:
        session = {
            "tenant_id": tenant_id,
            "session_id": session_id,
            "active_order_draft": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.assistant_sessions.insert_one(session)
    return session


async def update_assistant_session(tenant_id: str, session_id: str, draft: dict, last_question: str = None):
    """Update the assistant session with new draft state"""
    update_data = {
        "active_order_draft": draft,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if last_question:
        if draft:
            draft['last_question_asked'] = last_question
    
    await db.assistant_sessions.update_one(
        {"tenant_id": tenant_id, "session_id": session_id},
        {"$set": update_data},
        upsert=True
    )


async def lookup_customer_by_name(tenant_id: str, customer_name: str) -> Optional[dict]:
    """Look up customer by name (case-insensitive partial match)"""
    if not customer_name:
        return None
    
    # Try exact match first
    customer = await db.customers.find_one(
        {"tenant_id": tenant_id, "name": {"$regex": f"^{re.escape(customer_name)}$", "$options": "i"}},
        {"_id": 0, "id": 1, "name": 1, "company": 1, "email": 1}
    )
    if customer:
        return customer
    
    # Try partial match
    customers = await db.customers.find(
        {"tenant_id": tenant_id, "name": {"$regex": re.escape(customer_name), "$options": "i"}},
        {"_id": 0, "id": 1, "name": 1, "company": 1, "email": 1}
    ).limit(5).to_list(5)
    
    if len(customers) == 1:
        return customers[0]
    
    return None  # No match or multiple matches


def process_user_message_for_draft(message: str, existing_draft: Optional[dict], last_question: Optional[str] = None) -> dict:
    """Process user message and update/create order draft"""
    
    # Initialize or get existing draft
    if existing_draft and existing_draft.get('intent') == 'create_order':
        draft = existing_draft.copy()
    else:
        draft = {
            "intent": None,
            "customer_name": None,
            "customer_id": None,
            "order_items": [],
            "last_question_asked": last_question,
        }
    
    # Check for order intent
    if detect_order_intent(message) or draft.get('intent') == 'create_order':
        draft['intent'] = 'create_order'
    
    # Extract customer name
    customer_name = extract_customer_name(message)
    if customer_name and not draft.get('customer_name'):
        draft['customer_name'] = customer_name
    
    # Extract product type
    product_type = extract_product_type(message)
    
    # Initialize order item if needed
    if not draft.get('order_items'):
        draft['order_items'] = [{
            'product_type': None,
            'quantity': None,
            'size': None,
            'material': None,
            'sides': None,
            'design_notes': None,
            'due_date': None,
            'delivery_method': None,
        }]
    
    item = draft['order_items'][0]
    
    # Update product type
    if product_type and not item.get('product_type'):
        item['product_type'] = product_type
    
    # Extract and update quantity
    quantity = extract_quantity(message, last_question)
    if quantity and not item.get('quantity'):
        item['quantity'] = quantity
    
    # Extract and update size
    size = extract_size(message)
    if size and not item.get('size'):
        item['size'] = size
    
    # Extract and update material
    material = extract_material(message)
    if material and not item.get('material'):
        item['material'] = material
    
    # Extract and update sides
    sides = extract_sides(message)
    if sides and not item.get('sides'):
        item['sides'] = sides
    
    return draft


async def _get_job_category_breakdown(tenant_id: str) -> list:
    pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_value": {"$sum": "$total"}}},
        {"$sort": {"total_value": -1}},
        {"$limit": 10},
    ]
    job_categories = await db.jobs.aggregate(pipeline).to_list(10)
    return [{"category": item["_id"] or "Uncategorized", "count": item["count"], "revenue": round(item.get("total_value", 0), 2)} for item in job_categories]


async def _get_top_customers(tenant_id: str) -> list:
    pipeline = [
        {"$match": {"tenant_id": tenant_id, "status": "paid"}},
        {"$group": {"_id": "$customer_id", "total_spent": {"$sum": "$total"}, "invoice_count": {"$sum": 1}}},
        {"$sort": {"total_spent": -1}},
        {"$limit": 5},
    ]
    top_customers_data = await db.invoices.aggregate(pipeline).to_list(5)
    top_customers = []
    for customer_total in top_customers_data:
        customer = await db.customers.find_one({"id": customer_total["_id"]}, {"_id": 0, "name": 1})
        if customer:
            top_customers.append({
                "name": customer.get("name", "Unknown"),
                "total_spent": customer_total["total_spent"],
                "orders": customer_total["invoice_count"],
            })
    return top_customers


async def get_shop_context(tenant_id: str) -> dict:
    """Fetch comprehensive shop data for AI context"""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    thirty_days_iso = thirty_days_ago.isoformat()

    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    company_name = tenant.get("company_name", "Your Shop") if tenant else "Your Shop"

    total_customers = await db.customers.count_documents({"tenant_id": tenant_id})
    new_customers_30d = await db.customers.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": thirty_days_iso}})

    total_jobs = await db.jobs.count_documents({"tenant_id": tenant_id})
    active_jobs = await db.jobs.count_documents({"tenant_id": tenant_id, "status": {"$in": ["pending", "in_progress", "production"]}})
    completed_jobs_30d = await db.jobs.count_documents({"tenant_id": tenant_id, "status": "completed", "updated_at": {"$gte": thirty_days_iso}})

    paid_invoices = await db.invoices.find({"tenant_id": tenant_id, "status": "paid"}, {"_id": 0, "total": 1, "paid_at": 1, "created_at": 1}).to_list(1000)
    total_revenue = sum(invoice.get("total", 0) for invoice in paid_invoices)
    revenue_30d = sum(invoice.get("total", 0) for invoice in paid_invoices if invoice.get("paid_at", invoice.get("created_at", "")) >= thirty_days_iso)

    pending_invoices = await db.invoices.find({"tenant_id": tenant_id, "status": {"$in": ["sent", "draft", "overdue"]}}, {"_id": 0, "total": 1}).to_list(500)
    pending_revenue = sum(invoice.get("total", 0) for invoice in pending_invoices)

    total_quotes = await db.quotes.count_documents({"tenant_id": tenant_id})
    quotes_30d = await db.quotes.count_documents({"tenant_id": tenant_id, "created_at": {"$gte": thirty_days_iso}})
    accepted_quotes = await db.quotes.count_documents({"tenant_id": tenant_id, "status": "accepted"})
    quote_conversion_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0

    job_categories, top_customers = await asyncio.gather(
        _get_job_category_breakdown(tenant_id),
        _get_top_customers(tenant_id),
    )

    employee_count = await db.employees.count_documents({"tenant_id": tenant_id})
    webstore_count = await db.webstores_v2.count_documents({"tenant_id": tenant_id})
    webstore_orders = await db.webstore_orders.count_documents({"tenant_id": tenant_id})
    avg_job_value = total_revenue / total_jobs if total_jobs > 0 else 0

    return {
        "company_name": company_name,
        "customers": {"total": total_customers, "new_last_30_days": new_customers_30d},
        "jobs": {"total": total_jobs, "active": active_jobs, "completed_last_30_days": completed_jobs_30d, "average_value": round(avg_job_value, 2)},
        "revenue": {"total_all_time": round(total_revenue, 2), "last_30_days": round(revenue_30d, 2), "pending": round(pending_revenue, 2)},
        "quotes": {"total": total_quotes, "last_30_days": quotes_30d, "conversion_rate": round(quote_conversion_rate, 1)},
        "job_categories": job_categories,
        "top_customers": top_customers,
        "team_size": employee_count,
        "webstores": {"count": webstore_count, "total_orders": webstore_orders},
    }


@router.post("/assistant")
async def ai_business_assistant(
    request: Request,
    data: AIAssistantRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """AI Business Assistant - Chat interface for sign shop operations with real shop data and order creation"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from services.multi_product_gate import get_multi_product_feature_gate
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    preview = await preview_credit_usage(db, current_user.tenant_id, "ai_business_assistant")
    if not preview["sufficient_credits"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

    # Check feature access
    gate = get_multi_product_feature_gate(db)
    await gate.require_feature(current_user.tenant_id, "ai_assistant", "assistant_access")
    await gate.require_feature(current_user.tenant_id, "ai_assistant", "monthly_queries", increment_usage=True)
    
    # Check if business data access is allowed
    data_aware_result = await gate.check_feature(current_user.tenant_id, "ai_assistant", "business_data_aware")
    data_limited_result = await gate.check_feature(current_user.tenant_id, "ai_assistant", "business_data_limited")
    
    has_business_data_access = data_aware_result.allowed or data_limited_result.allowed
    
    try:
        def normalize_llm_response(value):
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                return value.get("text") or value.get("content") or str(value)
            if hasattr(value, 'text') and getattr(value, 'text'):
                return value.text
            if hasattr(value, 'content') and getattr(value, 'content'):
                return value.content
            return str(value)

        # ========== ORDER DRAFT MANAGEMENT ==========
        # Get or create assistant session
        session = await get_or_create_assistant_session(current_user.tenant_id, data.session_id)
        existing_draft = session.get('active_order_draft')
        last_question = existing_draft.get('last_question_asked') if existing_draft else None
        
        # Process user message to extract/update order draft
        updated_draft = process_user_message_for_draft(data.message, existing_draft, last_question)
        
        # Look up customer if we have a name but no ID yet
        if updated_draft.get('customer_name') and not updated_draft.get('customer_id'):
            customer = await lookup_customer_by_name(current_user.tenant_id, updated_draft['customer_name'])
            if customer:
                updated_draft['customer_id'] = customer.get('id')
                updated_draft['customer_match'] = customer
        
        # Format draft for inclusion in prompt
        draft_context = format_draft_for_prompt(updated_draft) if updated_draft.get('intent') == 'create_order' else ""
        
        # ========== SHOP DATA CONTEXT ==========
        shop_data = None
        shop_summary = ""
        
        if has_business_data_access:
            shop_data = await get_shop_context(current_user.tenant_id)
            
            # Format shop data for the prompt
            shop_summary = f"""
## Current Shop Data for {shop_data['company_name']}:

### Customers & Sales
- Total Customers: {shop_data['customers']['total']}
- New Customers (30 days): {shop_data['customers']['new_last_30_days']}
- Quote Conversion Rate: {shop_data['quotes']['conversion_rate']}%

### Jobs
- Total Jobs: {shop_data['jobs']['total']}
- Active Jobs: {shop_data['jobs']['active']}
- Completed (30 days): {shop_data['jobs']['completed_last_30_days']}
- Average Job Value: ${shop_data['jobs']['average_value']:,.2f}

### Revenue
- All-Time Revenue: ${shop_data['revenue']['total_all_time']:,.2f}
- Last 30 Days: ${shop_data['revenue']['last_30_days']:,.2f}
- Pending Invoices: ${shop_data['revenue']['pending']:,.2f}

### Top Job Categories by Revenue:
{chr(10).join([f"- {cat['category']}: {cat['count']} jobs, ${cat['revenue']:,.2f}" for cat in shop_data['job_categories'][:5]]) if shop_data['job_categories'] else '- No job data yet'}

### Top Customers:
{chr(10).join([f"- {c['name']}: ${c['total_spent']:,.2f} ({c['orders']} orders)" for c in shop_data['top_customers']]) if shop_data['top_customers'] else '- No customer revenue data yet'}

### Team & Operations
- Employees: {shop_data['team_size']}
- Webstores: {shop_data['webstores']['count']}
- Webstore Orders: {shop_data['webstores']['total_orders']}
"""
        else:
            shop_summary = """
## Note: Operating in generic mode (no access to your business data)

I can help with general sign shop questions, industry best practices, and advice,
but I don't have access to your specific customer, job, or financial data.
"""
        
        # Build conversation context from history
        context_messages = ""
        if data.conversation_history:
            for msg in data.conversation_history[-6:]:  # Last 6 messages for context
                role = "User" if msg.get("role") == "user" else "Assistant"
                context_messages += f"{role}: {msg.get('content', '')}\n\n"
        
        # ========== BUILD SYSTEM MESSAGE ==========
        # Add order creation instructions if there's an active draft
        order_creation_instructions = ""
        if updated_draft.get('intent') == 'create_order':
            order_creation_instructions = f"""

## ACTIVE ORDER CREATION MODE

You are currently helping create an order. Here is the current order draft:

{draft_context}

### CRITICAL RULES FOR ORDER CREATION:
1. **NEVER ask for information already in the draft above.** The user already provided it.
2. **Ask for ONLY the next missing field.** Do not dump a list of questions.
3. **When the user gives a short answer like "10" or "18x24", interpret it based on what you just asked.**
4. **Always acknowledge what you captured before asking the next question.**

### Question Order (skip any already captured):
1. Quantity - "How many [product] do they need?"
2. Size - "What size?" (common: 18x24, 24x36, 4x8 feet)
3. Material - "What material?" (coroplast, aluminum, PVC, etc.)
4. Sides - "Single-sided or double-sided?"
5. Design - "Any design notes or do they have artwork?"
6. Due date - "When do they need it by?"
7. Delivery - "Pickup, delivery, or install?"

### Good Response Examples:
- User: "Make an order for Donald Black for step signs"
  You: "Got it! Starting an order for Donald Black with step signs. How many step signs do they need?"

- User: "10"
  You: "Perfect, 10 step signs. What size - 18x24 is standard, or something different?"

- User: "18 by 24 coroplast"
  You: "Great - 10 step signs, 18x24 coroplast. Single-sided or double-sided?"

### Bad Response Examples (NEVER DO THESE):
- Asking "Who is this order for?" when customer_name is already set
- Asking "What product/item?" when product_type is already set
- Asking multiple questions at once
- Ignoring a short answer like "10" and asking "What do you mean?"
"""
        
        company_name = shop_data['company_name'] if shop_data else 'Your Shop'
        
        system_message = f"""You are the AI Business Assistant for SignGuy AI, a comprehensive sign shop management platform. You are chatting with {current_user.full_name or 'the owner'} from {company_name}.

## Your Role
You are a smart, helpful assistant that can:
1. Answer questions about running a sign shop
2. Help CREATE ORDERS by collecting information step-by-step
3. Provide business insights based on shop data
{order_creation_instructions}

{shop_summary}

## Your Knowledge
- **Sign Industry**: Vehicle wraps, channel letters, monument signs, banners, yard signs, step signs, vinyl graphics, A-frames, window graphics, real estate signs, political signs
- **Materials**: Coroplast, aluminum, ACM/Dibond, PVC/Sintra, foam board, acrylic, MDO, vinyl
- **Production**: Print technologies, lamination, cutting, installation techniques
- **Business**: Pricing (40-60% margins typical), job costing, time tracking

## Response Style
- Be conversational and helpful, not robotic
- Keep responses concise - don't over-explain
- If creating an order, stay focused on collecting the needed info
- Acknowledge what you heard before asking the next question"""
        
        # Initialize chat with the session
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=data.session_id,
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        # Build the prompt with context
        if context_messages:
            full_prompt = f"Previous conversation:\n{context_messages}\nUser's new message: {data.message}"
        else:
            full_prompt = data.message
        
        # Send message and get response
        response = await chat.send_message(UserMessage(text=full_prompt))
        assistant_text = normalize_llm_response(response)
        
        # Extract the question asked from the response (for tracking)
        response_lower = assistant_text.lower()
        detected_question = None
        if 'how many' in response_lower:
            detected_question = 'How many?'
        elif 'what size' in response_lower:
            detected_question = 'What size?'
        elif 'what material' in response_lower:
            detected_question = 'What material?'
        elif 'single-sided' in response_lower or 'double-sided' in response_lower:
            detected_question = 'Single or double sided?'
        elif 'design' in response_lower or 'artwork' in response_lower:
            detected_question = 'Design/artwork notes?'
        elif 'when do they need' in response_lower or 'due date' in response_lower:
            detected_question = 'Due date?'
        elif 'pickup' in response_lower or 'delivery' in response_lower or 'install' in response_lower:
            detected_question = 'Pickup/delivery/install?'
        
        # Save updated draft to session
        if updated_draft.get('intent') == 'create_order':
            await update_assistant_session(
                current_user.tenant_id, 
                data.session_id, 
                updated_draft, 
                detected_question
            )
        
        await deduct_credits_after_success(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="ai_business_assistant",
            module="AI Assistant",
            feature_name="ai_business_assistant",
            metadata={"session_id": data.session_id, "message": data.message[:200]},
        )
        
        # Log assistant conversation
        await db.ai_assistant_logs.insert_one({
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "tool": "business_assistant",
            "has_order_draft": updated_draft.get('intent') == 'create_order',
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Include draft in response for frontend display
        response_data = {"response": assistant_text}
        if updated_draft.get('intent') == 'create_order':
            response_data["active_order_draft"] = updated_draft
        
        return response_data
        
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="ai_business_assistant",
            module="AI Assistant",
            feature_name="ai_business_assistant",
            metadata={"session_id": data.session_id},
        )
        print(f"AI Assistant error: {e}")
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")


@router.post("/voice/transcribe")
async def transcribe_voice_input(
    audio: UploadFile = File(...),
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Transcribe assistant voice input using OpenAI Whisper."""
    voice_api_key = OPENAI_API_KEY or EMERGENT_LLM_KEY
    if not voice_api_key:
        raise HTTPException(status_code=500, detail="Voice input is not configured")

    preview = await preview_credit_usage(db, current_user.tenant_id, "voice_transcription", 1)
    if not preview["sufficient_credits"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

    try:
        from emergentintegrations.llm.openai.speech_to_text import OpenAISpeechToText
        import tempfile

        # Save uploaded file to a temp file with proper extension
        ext = (audio.filename or "audio.webm").rsplit(".", 1)[-1] or "webm"
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            stt = OpenAISpeechToText(api_key=voice_api_key)
            # Open as file object with proper name for the library
            with open(tmp_path, "rb") as audio_file:
                transcription = await stt.transcribe(audio_file, model="whisper-1", response_format="json", language="en")
            # Extract text from response - handle dict, object with .text, or string
            if isinstance(transcription, dict):
                text = transcription.get("text", "")
            elif hasattr(transcription, 'text'):
                text = transcription.text
            elif hasattr(transcription, 'model_dump'):
                text = transcription.model_dump().get('text', '')
            else:
                text = str(transcription)
        finally:
            os.unlink(tmp_path)

        await deduct_credits_after_success(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="voice_transcription",
            module="AI Assistant Voice",
            feature_name="voice_transcription",
            metadata={"filename": audio.filename, "content_type": audio.content_type},
            credits_required=1,
        )

        return {"text": text or ""}
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="voice_transcription",
            module="AI Assistant Voice",
            feature_name="voice_transcription",
            metadata={"filename": audio.filename},
        )
        raise HTTPException(status_code=500, detail=f"Voice transcription failed: {str(e)}")


@router.post("/voice/speak")
async def generate_voice_output(
    request: Request,
    data: VoiceSpeakRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate assistant voice output using OpenAI TTS."""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Voice output is not configured")
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    preview = await preview_credit_usage(db, current_user.tenant_id, "voice_tts", 1)
    if not preview["sufficient_credits"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

    try:
        from emergentintegrations.llm.openai.text_to_speech import OpenAITextToSpeech

        tts = OpenAITextToSpeech(api_key=OPENAI_API_KEY)
        audio_base64 = await tts.generate_speech_base64(
            text=data.text[:4000],
            model="tts-1",
            voice=data.voice,
            speed=data.speed,
            response_format="mp3"
        )

        await deduct_credits_after_success(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="voice_tts",
            module="AI Assistant Voice",
            feature_name="voice_tts",
            metadata={"voice": data.voice, "speed": data.speed, "text_length": len(data.text)},
            credits_required=1,
        )

        return {"audio_base64": audio_base64, "mime_type": "audio/mp3"}
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="voice_tts",
            module="AI Assistant Voice",
            feature_name="voice_tts",
            metadata={"voice": data.voice},
        )
        raise HTTPException(status_code=500, detail=f"Voice output failed: {str(e)}")


# ============== AI EMAIL GENERATOR ==============

class EmailGenerateRequest(BaseModel):
    email_type: str  # invoice_send, quote_send, approval_request, etc.
    tone: str = "professional"  # professional, friendly, formal, urgent
    context: Dict[str, Any] = {}


EMAIL_TYPE_PROMPTS = {
    "invoice_send": "Write an email to send an invoice to a customer. Be clear about the amount due and payment terms.",
    "invoice_reminder": "Write a polite payment reminder email. Be friendly but clear that payment is expected.",
    "invoice_overdue": "Write a firm but professional overdue payment notice. Emphasize the importance of settling the balance.",
    "quote_send": "Write an email to send a quote/estimate to a potential customer. Highlight value and encourage them to proceed.",
    "quote_followup": "Write a follow-up email about a quote that hasn't been responded to. Be helpful, not pushy.",
    "approval_request": "Write an email requesting customer approval for artwork, design proof, or project details. Be clear about what needs approval.",
    "job_update": "Write an email updating the customer on their job progress. Be informative and reassuring.",
    "job_complete": "Write an email notifying the customer their job is complete and ready. Include next steps for pickup or installation.",
    "thank_you": "Write a thank you email after completing a job. Express gratitude and encourage future business/referrals.",
}


@router.post("/generate-email")
async def generate_email(
    request: Request,
    data: EmailGenerateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate professional email content using AI"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    email_type = data.email_type
    if email_type not in EMAIL_TYPE_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Unknown email type: {email_type}")
    
    preview = await preview_credit_usage(db, current_user.tenant_id, email_type)
    if not preview["sufficient_credits"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

    try:
        # Build context string from provided context
        context = data.context
        context_parts = []
        
        if context.get("customer_name"):
            context_parts.append(f"Customer Name: {context['customer_name']}")
        if context.get("customer_email"):
            context_parts.append(f"Customer Email: {context['customer_email']}")
        if context.get("invoice_number"):
            context_parts.append(f"Invoice Number: {context['invoice_number']}")
        if context.get("quote_number"):
            context_parts.append(f"Quote Number: {context['quote_number']}")
        if context.get("job_name"):
            context_parts.append(f"Job/Project Name: {context['job_name']}")
        if context.get("amount"):
            context_parts.append(f"Amount: ${context['amount']}")
        if context.get("due_date"):
            context_parts.append(f"Due Date: {context['due_date']}")
        if context.get("company_name"):
            context_parts.append(f"Our Company: {context['company_name']}")
        if context.get("additional_notes"):
            context_parts.append(f"Additional Notes: {context['additional_notes']}")
        
        context_str = "\n".join(context_parts) if context_parts else "No specific context provided"
        
        system_message = """You are an expert email writer for a sign shop business. Write professional, clear, and effective business emails.

Your emails should:
- Be appropriately toned based on the request (professional, friendly, formal, or urgent)
- Be concise but complete
- Include a clear subject line
- Have proper greeting and sign-off
- Sound human and genuine, not robotic
- Be appropriate for a sign shop/graphics business context

Return your response in this exact format:
SUBJECT: [Your subject line here]
---
[Your email body here]"""
        
        prompt = f"""{EMAIL_TYPE_PROMPTS[email_type]}

Tone: {data.tone}

Context:
{context_str}

Write a complete email with subject line and body. Sign off as "SignGuy AI Team" or similar."""
        
        # Initialize chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"email_gen_{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        # Generate email
        response = await chat.send_message(UserMessage(text=prompt))
        await deduct_credits_after_success(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type=email_type,
            module="AI Email Composer",
            feature_name=email_type,
            metadata=context,
        )
        
        # Parse the response to extract subject and body
        subject = ""
        body = response
        
        if "SUBJECT:" in response and "---" in response:
            parts = response.split("---", 1)
            subject_part = parts[0].strip()
            if subject_part.startswith("SUBJECT:"):
                subject = subject_part.replace("SUBJECT:", "").strip()
            body = parts[1].strip() if len(parts) > 1 else response
        elif "Subject:" in response:
            lines = response.split("\n")
            for i, line in enumerate(lines):
                if line.lower().startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                    body = "\n".join(lines[i+1:]).strip()
                    break
        
        return {
            "subject": subject or "Message from SignGuy AI",
            "body": body
        }
        
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type=email_type,
            module="AI Email Composer",
            feature_name=email_type,
            metadata=data.context,
        )
        print(f"Email generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Email generation error: {str(e)}")



# ============== AI ASSISTANT STRUCTURED ACTIONS ==============

from services.ai_assistant_actions import (
    AIAssistantActions, ActionType, ActionStatus, ActionRequest, ActionResponse,
    get_ai_assistant_actions
)


class ExecuteActionRequest(BaseModel):
    """Request to execute a structured action via AI Assistant"""
    action_type: str  # ActionType enum value
    parameters: Dict[str, Any]
    confirmed: bool = False  # Set to True to skip confirmation
    source: str = "text"  # "text" | "voice" — voice writes always require confirmation


class ConfirmActionRequest(BaseModel):
    """Request to confirm a pending action"""
    action_id: str
    confirm: bool  # True to execute, False to cancel


@router.post("/assistant/action")
async def execute_assistant_action(
    request: Request,
    data: ExecuteActionRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Execute a structured database action via AI Assistant.
    
    All actions are:
    - Tenant scoped (automatically)
    - Permission checked
    - Audit logged
    - Require confirmation for destructive changes (unless confirmed=True)
    
    Supported actions:
    - create_order
    - create_job
    - update_job_status
    - create_calendar_event
    - add_material
    - update_material_cost
    - create_invoice
    - assign_employee
    - log_time_entry
    - categorize_expense
    """
    try:
        action_type = ActionType(data.action_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid action type: {data.action_type}. Valid types: {[a.value for a in ActionType]}"
        )
    
    actions = get_ai_assistant_actions(db)
    
    action_request = ActionRequest(
        action_type=action_type,
        parameters=data.parameters,
        source=data.source,
    )
    
    response = await actions.execute_action(
        user=current_user,
        action_request=action_request,
        confirmed=data.confirmed
    )
    
    return response.model_dump()


@router.post("/assistant/action/confirm")
async def confirm_assistant_action(
    request: Request,
    data: ConfirmActionRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Confirm or cancel a pending action.
    
    After an action returns status=pending_confirmation, use this endpoint
    to either execute (confirm=True) or cancel (confirm=False) the action.
    """
    actions = get_ai_assistant_actions(db)
    
    # Get the pending action from audit log
    pending = await db.ai_action_audit.find_one({
        "action_id": data.action_id,
        "tenant_id": current_user.tenant_id,
        "status": ActionStatus.PENDING_CONFIRMATION.value
    }, {"_id": 0})
    
    if not pending:
        raise HTTPException(
            status_code=404,
            detail="Pending action not found or already processed"
        )
    
    if not data.confirm:
        # Cancel the action
        await db.ai_action_audit.update_one(
            {"action_id": data.action_id},
            {"$set": {
                "status": ActionStatus.CANCELLED.value,
                "cancelled_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {
            "action_id": data.action_id,
            "status": ActionStatus.CANCELLED.value,
            "message": "Action cancelled"
        }
    
    # Execute the confirmed action
    try:
        action_type = ActionType(pending["action_type"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid action type in pending action")
    
    action_request = ActionRequest(
        action_type=action_type,
        parameters=pending["parameters"]
    )
    
    response = await actions.execute_action(
        user=current_user,
        action_request=action_request,
        confirmed=True  # Now confirmed
    )
    
    # Update the original audit entry
    await db.ai_action_audit.update_one(
        {"action_id": data.action_id},
        {"$set": {
            "status": response.status.value,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return response.model_dump()


@router.get("/assistant/actions/audit")
async def get_action_audit_log(
    limit: int = 100,
    action_type: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Admin-only audit log of AI Assistant actions for the tenant.

    Phase 4: adds filters (status, user_id, date range) and returns user names
    for readable admin UI. OWNER/ADMIN only — surface visibility is a trust feature.
    """
    from models.enums import UserRole
    if current_user.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required to view AI audit log")

    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id}
    if action_type:
        query["action_type"] = action_type
    if status:
        query["status"] = status
    if user_id:
        query["user_id"] = user_id
    if start_date or end_date:
        rng: Dict[str, str] = {}
        if start_date:
            rng["$gte"] = start_date
        if end_date:
            rng["$lte"] = end_date + "T23:59:59Z"
        query["created_at"] = rng

    cursor = db.ai_action_audit.find(query, {"_id": 0}).sort("created_at", -1).limit(max(1, min(limit, 500)))
    entries = await cursor.to_list(max(1, min(limit, 500)))

    # Attach human-readable user name (best-effort — tenant-scoped).
    user_ids = list({e.get("user_id") for e in entries if e.get("user_id")})
    user_map: Dict[str, str] = {}
    if user_ids:
        users = await db.users.find(
            {"id": {"$in": user_ids}, "tenant_id": current_user.tenant_id},
            {"_id": 0, "id": 1, "email": 1, "first_name": 1, "last_name": 1},
        ).to_list(500)
        for u in users:
            full = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("email") or u["id"]
            user_map[u["id"]] = full

    for e in entries:
        e["user_name"] = user_map.get(e.get("user_id"), e.get("user_id", "—"))

    # Quick counts for the filter bar.
    totals = {
        "total": len(entries),
        "executed": sum(1 for e in entries if e.get("status") == "executed"),
        "failed": sum(1 for e in entries if e.get("status") == "failed"),
        "cancelled": sum(1 for e in entries if e.get("status") == "cancelled"),
        "pending": sum(1 for e in entries if e.get("status") == "pending_confirmation"),
    }
    return {"audit_log": entries, "count": len(entries), "totals": totals}


@router.get("/assistant/actions/audit/{audit_id}")
async def get_action_audit_detail(
    audit_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Full detail of a single audit entry (admin-only)."""
    from models.enums import UserRole
    if current_user.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")
    entry = await db.ai_action_audit.find_one(
        {"id": audit_id, "tenant_id": current_user.tenant_id}, {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Audit entry not found")

    if entry.get("user_id"):
        u = await db.users.find_one(
            {"id": entry["user_id"], "tenant_id": current_user.tenant_id},
            {"_id": 0, "email": 1, "first_name": 1, "last_name": 1},
        )
        if u:
            entry["user_name"] = f"{u.get('first_name', '')} {u.get('last_name', '')}".strip() or u.get("email")
    return entry


@router.get("/assistant/actions/pending")
async def get_pending_actions(
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get actions that are pending confirmation.
    
    Returns actions that require user confirmation before execution.
    Use /assistant/action/confirm to confirm or cancel.
    """
    actions = get_ai_assistant_actions(db)
    pending = await actions.get_pending_confirmations(current_user.tenant_id)
    
    return {"pending_actions": pending, "count": len(pending)}


@router.get("/assistant/actions/types")
async def get_available_action_types():
    """
    Get list of available action types and their descriptions.
    """
    return {
        "action_types": [
            {
                "type": ActionType.CREATE_ORDER.value,
                "description": "Create a new order",
                "requires_confirmation": False,
                "parameters": ["customer_name", "company_name", "description", "requested_due_date", "pickup_delivery_method"]
            },
            {
                "type": ActionType.CREATE_JOB.value,
                "description": "Create a new job",
                "requires_confirmation": False,
                "parameters": ["name", "customer_id", "customer_name", "category", "description", "due_date", "priority", "total"]
            },
            {
                "type": ActionType.UPDATE_JOB_STATUS.value,
                "description": "Update job status (pending, in_progress, production, completed, on_hold, cancelled)",
                "requires_confirmation": True,
                "parameters": ["job_id", "status"]
            },
            {
                "type": ActionType.CREATE_CALENDAR_EVENT.value,
                "description": "Create a calendar event",
                "requires_confirmation": False,
                "parameters": ["title", "description", "start_time", "end_time", "all_day", "event_type", "location", "job_id"]
            },
            {
                "type": ActionType.ADD_MATERIAL.value,
                "description": "Add material to inventory",
                "requires_confirmation": False,
                "parameters": ["name", "category", "sku", "unit", "cost", "price", "quantity", "supplier"]
            },
            {
                "type": ActionType.UPDATE_MATERIAL_COST.value,
                "description": "Update material cost (affects future quotes/jobs)",
                "requires_confirmation": True,
                "parameters": ["material_id", "cost"]
            },
            {
                "type": ActionType.CREATE_INVOICE.value,
                "description": "Create a new invoice",
                "requires_confirmation": True,
                "parameters": ["customer_id", "customer_name", "job_id", "line_items", "tax_rate", "due_date", "notes"]
            },
            {
                "type": ActionType.ASSIGN_EMPLOYEE.value,
                "description": "Assign employee to a job",
                "requires_confirmation": True,
                "parameters": ["job_id", "employee_id"]
            },
            {
                "type": ActionType.LOG_TIME_ENTRY.value,
                "description": "Log time entry for an employee",
                "requires_confirmation": False,
                "parameters": ["employee_id", "employee_name", "job_id", "job_name", "date", "hours", "description", "billable"]
            },
            {
                "type": ActionType.CATEGORIZE_EXPENSE.value,
                "description": "Categorize or re-categorize an expense",
                "requires_confirmation": False,
                "parameters": ["expense_id", "category"]
            }
        ]
    }


class ParseActionRequest(BaseModel):
    """Request to parse natural language into structured action"""
    message: str
    action_type: str  # Hint about what type of action this might be


@router.post("/assistant/parse-action")
async def parse_action_intent(
    request: Request,
    data: ParseActionRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Parse natural language message into structured action parameters.
    
    Uses AI to extract action parameters from user's message.
    Returns parsed parameters or indicates that more info is needed.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json
    import re
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    preview = await preview_credit_usage(db, current_user.tenant_id, "assistant_parse_action")
    if not preview["sufficient_credits"]:
        raise HTTPException(status_code=402, detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.")

    # Get context data for better parsing
    tenant_id = current_user.tenant_id
    
    # Get recent customers for matching
    recent_customers = await db.customers.find(
        {"tenant_id": tenant_id},
        {"_id": 0, "id": 1, "name": 1, "company": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    customer_names = [f"{c['name']} ({c.get('company', '')})" for c in recent_customers]
    
    # Get active jobs for matching
    active_jobs = await db.jobs.find(
        {"tenant_id": tenant_id, "status": {"$nin": ["completed", "cancelled"]}},
        {"_id": 0, "id": 1, "name": 1, "customer_id": 1}
    ).sort("created_at", -1).limit(20).to_list(20)
    job_names = [j['name'] for j in active_jobs]
    
    # Build parsing prompt based on action type
    if data.action_type == "auto":
        system_prompt = f"""You classify a sign-shop operator's message into ONE intent. Two families:

WRITE intents (modify data):
- chat — general question or advice (no DB write needed)
- create_order — user wants to start a new order/job ticket (includes "create a job", "new order")
- create_calendar_event — user wants to schedule an appointment / meeting / install / consultation
- create_invoice — user wants to generate an invoice from an existing order
- log_time_entry — user wants to log hours/time
- update_job_status — user wants to mark a job or order as complete/in progress/etc.

QUERY intents (read live data — return current shop info):
- overdue_invoices — "who owes me money", "show overdue invoices"
- ar_by_customer — "which customers owe the most", "balances by customer"
- jobs_due — "what's due today/tomorrow/this week/Friday"
- artwork_pending — "what's waiting on artwork/proof/approval"
- employee_hours — "who worked the most this week", "how many hours did John work last week"
- production_load — "production load tomorrow", "how busy are we Friday"
- jobs_in_production — "what's in production right now"
- revenue — "how much did we make this week", "revenue last month" (set filters.comparison='prior' if comparing periods)
- revenue_by_source — "webstore vs invoice revenue", "what came through Stripe"
- top_categories — "top-selling categories this month", "order mix this quarter"

Known customers: {', '.join(customer_names[:10]) if customer_names else 'None yet'}

Return JSON:
{{"intent": "<intent>", "parameters": {{...write fields...}}, "filters": {{"date_phrase": "today|tomorrow|yesterday|this week|last week|next week|this month|last month|this quarter|<weekday>|next <weekday>|YYYY-MM-DD", "employee_name": null, "customer_name": null, "comparison": "prior" | null}}, "needs_more_info": false, "question": null}}

Rules:
- For QUERY intents, fill `filters` (leave `parameters` as {{}}).
- For WRITE intents, fill `parameters` (leave `filters` as {{}}).
- If a required field is missing or a date is ambiguous, set needs_more_info=true and question="<concise follow-up>".
- WRITE parameter hints:
  - create_order: customer_name, company_name, description, requested_due_date (YYYY-MM-DD), pickup_delivery_method (pickup/delivery/install/ship/undecided).
  - create_calendar_event: title, date (YYYY-MM-DD), time (HH:MM), duration_minutes, location, event_type (appointment/meeting/installation/consultation/other), customer_name.
  - create_invoice: order_id (if user named a specific order), order_number, customer_name, notes.
  - log_time_entry: hours, job_name, task, date (YYYY-MM-DD), billable.
  - update_job_status: job_name or order_number, status (pending/in_progress/production/completed/on_hold/cancelled).

Respond ONLY with valid JSON, nothing else."""

    elif data.action_type == "create_order":
        system_prompt = f"""You are a parsing assistant. Extract order details from the user's message.

Known customers: {', '.join(customer_names[:10]) if customer_names else 'None yet'}

Return a JSON object with these fields:
- customer_name: Customer name (required)
- company_name: Company name if mentioned
- description: Order note or item summary if mentioned
- requested_due_date: Date in YYYY-MM-DD format if mentioned
- pickup_delivery_method: one of 'pickup', 'delivery', 'install' if determinable

If you cannot determine the customer name, return:
{{"needs_more_info": true, "question": "Who is the order for?"}}

Respond ONLY with valid JSON, nothing else."""

    elif data.action_type == "create_job":
        system_prompt = f"""You are a parsing assistant. Extract job details from the user's message.

Known customers: {', '.join(customer_names[:10]) if customer_names else 'None yet'}

Return a JSON object with these fields:
- name: Job name/title (required)
- customer_name: Customer name if mentioned
- description: Job description if mentioned
- category: One of 'vehicle_wrap', 'sign', 'banner', 'decal', 'other' if determinable
- due_date: Date in YYYY-MM-DD format if mentioned
- priority: 'low', 'normal', 'high', 'urgent' if mentioned

If you cannot determine enough info to create a job, return:
{{"needs_more_info": true, "question": "Your question to get missing info"}}

Respond ONLY with valid JSON, nothing else."""

    elif data.action_type == "create_calendar_event":
        system_prompt = """You are a parsing assistant. Extract appointment/event details from the user's message.

Return a JSON object with these fields:
- title: Event title (required)
- date: Date in YYYY-MM-DD format (required)
- time: Time in HH:MM format if mentioned
- duration_minutes: Duration if mentioned
- location: Location if mentioned
- event_type: 'appointment', 'meeting', 'installation', 'consultation', 'other'
- description: Additional details

If you cannot determine the required fields, return:
{{"needs_more_info": true, "question": "Your question to get missing info"}}

Respond ONLY with valid JSON, nothing else."""

    elif data.action_type == "log_time_entry":
        system_prompt = f"""You are a parsing assistant. Extract time entry details from the user's message.

Known jobs: {', '.join(job_names[:10]) if job_names else 'None active'}

Return a JSON object with these fields:
- hours: Number of hours (required)
- job_name: Job name if mentioned
- task: Task description
- date: Date in YYYY-MM-DD format (defaults to today)
- billable: true/false

If you cannot determine the hours, return:
{{"needs_more_info": true, "question": "Your question to get missing info"}}

Respond ONLY with valid JSON, nothing else."""

    else:
        # Generic parsing
        system_prompt = """You are a parsing assistant. Extract relevant parameters from the user's message.

Return a JSON object with any relevant fields you can extract.
If you need more information, return:
{"needs_more_info": true, "question": "Your question to get missing info"}

Respond ONLY with valid JSON, nothing else."""

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"parse_action_{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        response = await chat.send_message(UserMessage(text=data.message))
        
        # Try to parse as JSON
        try:
            # Clean up response - sometimes AI adds markdown
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = re.sub(r'^```(?:json)?\n?', '', clean_response)
                clean_response = re.sub(r'\n?```$', '', clean_response)
            
            parsed = json.loads(clean_response)
            
            # If we got parameters, try to match customer/job IDs
            if not parsed.get("needs_more_info"):
                if data.action_type in {"create_job", "create_order"} and parsed.get("customer_name"):
                    # Try to match customer
                    for c in recent_customers:
                        if parsed["customer_name"].lower() in c["name"].lower():
                            parsed["customer_id"] = c["id"]
                            break
                
                if data.action_type == "log_time_entry" and parsed.get("job_name"):
                    # Try to match job
                    for j in active_jobs:
                        if parsed["job_name"].lower() in j["name"].lower():
                            parsed["job_id"] = j["id"]
                            break
            
            await deduct_credits_after_success(
                db,
                tenant_id=current_user.tenant_id,
                user_id=current_user.id,
                action_type="assistant_parse_action",
                module="Floating Assistant",
                feature_name=data.action_type,
                metadata={"requested_action_type": data.action_type},
            )
            return {"parameters": parsed} if not parsed.get("needs_more_info") else parsed
            
        except json.JSONDecodeError:
            # If AI didn't return valid JSON, ask for more info
            return {
                "needs_more_info": True,
                "question": response if len(response) < 200 else "Could you provide more details?"
            }
            
    except Exception as e:
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="assistant_parse_action",
            module="Floating Assistant",
            feature_name=data.action_type,
            metadata={"requested_action_type": data.action_type},
        )
        print(f"Parse action error: {e}")
        return {
            "needs_more_info": True,
            "question": "I couldn't understand that. Could you rephrase?"
        }


# ============== SERVICES AI PREFILL ==============

# --- Per-key validators for AI-returned values (M-2: tamper defense) -------
# Each validator returns the COERCED value if acceptable, or raises ValueError.
# We run the validator on every value the LLM proposes; anything that fails
# is silently dropped so it never reaches the calculator.
def _v_float_range(lo: float, hi: float):
    def _check(value):
        num = float(value)
        if not (lo <= num <= hi):
            raise ValueError(f"out of range [{lo}, {hi}]")
        return num
    return _check


def _v_int_range(lo: int, hi: int):
    def _check(value):
        num = int(value)
        if not (lo <= num <= hi):
            raise ValueError(f"out of range [{lo}, {hi}]")
        return num
    return _check


def _v_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    raise ValueError("not a boolean")


def _v_enum(choices):
    normalized = {c.lower() for c in choices}
    def _check(value):
        if not isinstance(value, str):
            raise ValueError("not a string")
        if value.lower() not in normalized:
            raise ValueError(f"not in {sorted(choices)}")
        return value.lower()
    return _check


def _build_services_prefill_validators(services_cfg: Dict[str, Any]):
    """Build validators using the live Pricing Foundation enums."""
    service_types = [s["key"] for s in (services_cfg.get("available_service_types") or [])]
    billing_units = list(services_cfg.get("available_billing_units") or [
        "hour", "flat", "piece", "sqft", "linear_foot", "mile", "trip", "day", "custom",
    ])
    labor_roles = list((services_cfg.get("labor_roles") or {}).keys())
    complexity_keys = list((services_cfg.get("complexity_multipliers") or {}).keys()) or [
        "easy", "medium", "difficult", "extreme",
    ]
    equipment_keys = [e["key"] for e in (services_cfg.get("equipment_library") or [])]
    return {
        "service_type": _v_enum(service_types) if service_types else (lambda v: str(v)[:64]),
        "services_billing_unit": _v_enum(billing_units),
        "services_labor_role": _v_enum(labor_roles) if labor_roles else (lambda v: str(v)[:64]),
        "services_complexity": _v_enum(complexity_keys),
        "services_equipment_type": _v_enum(equipment_keys) if equipment_keys else (lambda v: str(v)[:64]),
        "estimated_hours": _v_float_range(0, 500),
        "quantity": _v_float_range(0, 100000),
        "services_flat_fee": _v_float_range(0, 100000),
        "services_unit_rate_override": _v_float_range(0, 100000),
        "services_travel_miles": _v_float_range(0, 10000),
        "services_trip_count": _v_int_range(0, 500),
        "services_equipment_days": _v_float_range(0, 365),
        "services_subcontract_cost": _v_float_range(0, 1000000),
        "services_permit_external_fee": _v_float_range(0, 100000),
        "services_minimum_applies": _v_bool,
        "services_travel_required": _v_bool,
        "services_trip_charge_applies": _v_bool,
        "services_equipment_required": _v_bool,
        "services_subcontracted": _v_bool,
        "services_subcontract_markup_applies": _v_bool,
        "rush_order": _v_bool,
    }


def _sign_prefill_fields(tenant_id: str, user_id: str, keys: List[str]) -> str:
    """HMAC-sign the set of AI-prefilled keys so the calculator can verify
    provenance was not forged by a malicious client (M-1)."""
    import hmac as _hmac
    import hashlib as _hashlib
    secret = os.environ.get("JWT_SECRET_KEY", "")
    payload = f"{tenant_id}|{user_id}|{','.join(sorted(keys))}"
    return _hmac.new(secret.encode(), payload.encode(), _hashlib.sha256).hexdigest()


def verify_prefill_signature(tenant_id: str, user_id: str, keys: List[str], signature: Optional[str]) -> bool:
    """Return True iff the signature matches the claimed keys for this user."""
    if not signature or not keys:
        return False
    import hmac as _hmac
    expected = _sign_prefill_fields(tenant_id, user_id, keys)
    return _hmac.compare_digest(expected, signature)


class ServicesPrefillRequest(BaseModel):
    description: str = Field(..., min_length=3, max_length=2000)
    existing_inputs: Dict[str, Any] = Field(default_factory=dict)


@router.post("/services-prefill")
async def services_ai_prefill(
    request: ServicesPrefillRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """AI-prefill missing Services order-item fields from a free-text description.

    Rules:
    - Only fills fields the user hasn't already set (`existing_inputs`).
    - Never overwrites user-entered values.
    - Returns per-field list so the calculator can tag provenance.
    - Validates every proposed value against per-key type/range rules.
    - Signs the field list with HMAC so provenance cannot be forged.
    """
    from server import get_pricing_defaults
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json as _json

    defaults = await get_pricing_defaults(current_user.tenant_id)
    services_cfg = (defaults.get("category_defaults") or {}).get("services", {}) or {}
    service_types = services_cfg.get("available_service_types", []) or []
    labor_roles = services_cfg.get("labor_roles", {}) or {}
    billing_units = services_cfg.get("available_billing_units", []) or []
    complexity_keys = list((services_cfg.get("complexity_multipliers") or {}).keys()) or [
        "easy", "medium", "difficult", "extreme",
    ]
    equipment_library = services_cfg.get("equipment_library", []) or []
    validators = _build_services_prefill_validators(services_cfg)

    # Keys the AI is allowed to propose (and only if not already present in existing_inputs)
    fillable_keys = list(validators.keys())
    already_set = {k for k, v in request.existing_inputs.items() if v not in (None, "", [])}
    missing_keys = [k for k in fillable_keys if k not in already_set]

    # Credit preview (cheap text call)
    preview = await preview_credit_usage(db, current_user.tenant_id, "ai_services_prefill")
    if not preview.get("sufficient_credits", True):
        raise HTTPException(status_code=402, detail="Insufficient AI credits for services prefill")

    system_prompt = (
        "You are a pricing assistant for a sign & graphics shop. Given a short "
        "description of a Services job, propose sensible default values ONLY for "
        "the listed missing fields. Do not invent fields that aren't in the list. "
        "Use only these enums:\n"
        f"- service_type keys: {[s['key'] for s in service_types]}\n"
        f"- services_billing_unit values: {billing_units}\n"
        f"- services_labor_role keys: {list(labor_roles.keys())}\n"
        f"- services_complexity values: {complexity_keys}\n"
        f"- services_equipment_type keys: {[e['key'] for e in equipment_library]}\n"
        "Numeric fields should be numbers. Booleans should be true/false. "
        "Respond with a single JSON object containing ONLY the fields you are proposing values for. "
        "No prose, no markdown, no code fences."
    )

    user_text = (
        f"Description:\n{request.description}\n\n"
        f"User has already set:\n{_json.dumps(request.existing_inputs, default=str)}\n\n"
        f"Propose values ONLY for these missing fields:\n{missing_keys}"
    )

    # M-3: stable per-user session id so conversation memory (if any) can be
    # reused across prefill calls. Still a lightweight single-turn interaction.
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"services_prefill_{current_user.id}",
        system_message=system_prompt,
    ).with_model("openai", "gpt-5.2")

    try:
        raw = await chat.send_message(UserMessage(text=user_text))
    except Exception as exc:
        # M-4: log full traceback server-side, return a generic user-safe
        # message. Never include `exc` in the response body — SDK error
        # strings have been known to echo bearer tokens.
        logger.exception("Services prefill LLM call failed")
        await log_failed_ai_usage(
            db,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            action_type="ai_services_prefill",
            module="Services Pricing",
            feature_name="ai_services_prefill",
            metadata={"error": str(exc)[:500]},
        )
        raise HTTPException(status_code=500, detail="AI prefill is temporarily unavailable. Please try again in a moment.")

    # Extract JSON payload (strip accidental code fences / prose around it)
    cleaned = (raw or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[-1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return {
            "prefilled": {},
            "ai_prefilled_fields": [],
            "ai_prefill_signature": None,
            "reasoning": cleaned[:400],
            "missing_keys": missing_keys,
        }
    try:
        proposed = _json.loads(cleaned[first:last + 1])
    except Exception:
        return {
            "prefilled": {},
            "ai_prefilled_fields": [],
            "ai_prefill_signature": None,
            "reasoning": cleaned[:400],
            "missing_keys": missing_keys,
        }

    if not isinstance(proposed, dict):
        return {
            "prefilled": {},
            "ai_prefilled_fields": [],
            "ai_prefill_signature": None,
            "reasoning": "AI returned non-object payload",
            "missing_keys": missing_keys,
        }

    # M-2: Filter + validate every proposed value against its per-key schema.
    # Never overwrite user-entered. Silently drop anything that fails validation.
    filtered: Dict[str, Any] = {}
    validation_errors: List[str] = []
    for key, value in proposed.items():
        if key not in fillable_keys:
            continue
        if key in already_set:
            continue
        validator = validators.get(key)
        if validator is None:
            continue
        try:
            filtered[key] = validator(value)
        except (ValueError, TypeError) as exc:
            validation_errors.append(f"{key}: {exc}")

    if validation_errors:
        logger.warning(
            "Services prefill dropped %d invalid fields for tenant %s: %s",
            len(validation_errors), current_user.tenant_id, validation_errors[:5],
        )

    await deduct_credits_after_success(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action_type="ai_services_prefill",
        module="Services Pricing",
        feature_name="ai_services_prefill",
        metadata={"description_len": len(request.description), "fields_filled": len(filtered)},
    )

    filled_keys = list(filtered.keys())
    signature = _sign_prefill_fields(current_user.tenant_id, current_user.id, filled_keys) if filled_keys else None

    return {
        "prefilled": filtered,
        "ai_prefilled_fields": filled_keys,
        "ai_prefill_signature": signature,
        "missing_keys": missing_keys,
        "reasoning": None,
    }



# ============================================================================
# Phase 2 — Business Assistant Live Queries
# ============================================================================
from services.assistant_queries import (  # noqa: E402
    run_query as _run_assistant_query,
    parse_date_phrase as _parse_date_phrase,
    QUERY_PERMISSIONS,
)
from models.auth import user_has_permission  # noqa: E402

SUPPORTED_QUERY_TYPES = set(QUERY_PERMISSIONS.keys())


class AssistantQueryRequest(BaseModel):
    """Live-query request. Either provide a `query_type` + `filters`, OR a
    natural-language `message` that the LLM should classify into one of the
    supported intents."""
    message: Optional[str] = None
    query_type: Optional[str] = None
    filters: Dict[str, Any] = {}


async def _classify_query_intent(message: str, tenant_id: str) -> Dict[str, Any]:
    """LLM-classify a natural-language question into one of the supported
    query types, extracting basic filters. Returns a dict shaped:

    {"query_type": "...", "filters": {...}, "needs_more_info": bool, "question": "..."}

    If the message is not a live-data question we mark query_type='chat'.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json as _json
    import re as _re

    system_prompt = (
        "You classify sign-shop operator questions into a live-data query intent. "
        "Supported intents: overdue_invoices, ar_by_customer, jobs_due, "
        "artwork_pending, employee_hours, production_load, jobs_in_production, "
        "revenue, revenue_by_source, top_categories, chat.\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        "  \"query_type\": \"<one of above>\",\n"
        "  \"filters\": {\"date_phrase\": \"today|tomorrow|yesterday|this week|last week|next week|this month|last month|this quarter|next friday|<weekday>|YYYY-MM-DD\", \"employee_id\": null, \"customer_id\": null, \"comparison\": \"prior\" | null},\n"
        "  \"needs_more_info\": false,\n"
        "  \"question\": null\n"
        "}\n\n"
        "Rules:\n"
        "- If the question is unrelated to live business data (general advice, pricing how-tos, etc.) use query_type=chat.\n"
        "- For revenue/comparison questions (‘this week vs last week’), set filters.comparison='prior'.\n"
        "- For employee-specific hours, set employee_id=null and keep the name in filters.employee_name so the server can resolve it.\n"
        "- If a date is required but missing/ambiguous, set needs_more_info=true and provide a concise question.\n"
    )
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"query_classify_{uuid.uuid4()}", system_message=system_prompt)
        chat.with_model("openai", "gpt-4o-mini")
        resp = await chat.send_message(UserMessage(text=message))
        raw = resp.strip()
        m = _re.search(r"\{.*\}", raw, _re.DOTALL)
        payload = _json.loads(m.group(0)) if m else _json.loads(raw)
    except Exception as exc:
        logger.warning("query classifier failed for tenant %s: %s", tenant_id, exc)
        payload = {"query_type": "chat", "filters": {}, "needs_more_info": False, "question": None}
    payload["filters"] = payload.get("filters") or {}
    return payload


@router.post("/assistant/query")
async def assistant_query(
    data: AssistantQueryRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Run a typed live-data query for the Business Assistant.

    Usage modes:
      1) {"query_type": "overdue_invoices"} — direct typed query (no LLM cost).
      2) {"message": "what jobs are due tomorrow?"} — LLM classifies, server runs.
    """
    # Mode 1: direct typed query
    if data.query_type and data.query_type in SUPPORTED_QUERY_TYPES:
        perm = QUERY_PERMISSIONS.get(data.query_type)
        if perm and not user_has_permission(current_user.role, perm):
            raise HTTPException(
                status_code=403,
                detail=f"Your role ({current_user.role.value}) cannot run '{data.query_type}'. Missing permission: {perm.value}.",
            )
        return await _run_assistant_query(db, current_user.tenant_id, data.query_type, data.filters or {})

    # Mode 2: natural-language — classify first (costs a credit), then run.
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=400, detail="Either `query_type` or `message` is required")

    preview = await preview_credit_usage(db, current_user.tenant_id, "assistant_query_classify")
    if not preview["sufficient_credits"]:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits to classify query. Need {preview['credit_cost']}, have {preview['total_credits']}.",
        )

    classified = await _classify_query_intent(data.message, current_user.tenant_id)

    await deduct_credits_after_success(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action_type="assistant_query_classify",
        module="Business Assistant",
        feature_name="assistant_query_classify",
        metadata={"intent": classified.get("query_type")},
    )

    query_type = classified.get("query_type") or "chat"

    if query_type == "chat":
        return {
            "query_type": "chat",
            "summary": "That looks like a general question rather than a live-data query. I'll answer it conversationally instead.",
            "metrics": [],
            "rows": [],
            "suggested_actions": [],
            "needs_more_info": False,
            "classified": classified,
        }

    if classified.get("needs_more_info"):
        return {
            "query_type": query_type,
            "summary": classified.get("question") or "Can you clarify which date range you mean?",
            "metrics": [],
            "rows": [],
            "suggested_actions": [],
            "needs_more_info": True,
            "classified": classified,
        }

    if query_type not in SUPPORTED_QUERY_TYPES:
        return {
            "query_type": query_type,
            "summary": f"I don't have a live-data query for '{query_type}' yet.",
            "metrics": [],
            "rows": [],
            "suggested_actions": [],
            "needs_more_info": False,
            "classified": classified,
        }

    # Permission check.
    perm = QUERY_PERMISSIONS.get(query_type)
    if perm and not user_has_permission(current_user.role, perm):
        return {
            "query_type": query_type,
            "summary": f"Your role ({current_user.role.value}) cannot view this data. Missing permission: {perm.value}.",
            "metrics": [],
            "rows": [],
            "suggested_actions": [],
            "needs_more_info": False,
            "classified": classified,
        }

    # Resolve employee_name → employee_id if the classifier provided only a name.
    filters = dict(classified.get("filters") or {})
    emp_name = filters.pop("employee_name", None)
    if emp_name and not filters.get("employee_id"):
        emp = await db.employees.find_one(
            {"tenant_id": current_user.tenant_id,
             "$or": [
                 {"name": {"$regex": f"^{emp_name}$", "$options": "i"}},
                 {"first_name": {"$regex": f"^{emp_name}$", "$options": "i"}},
             ]},
            {"_id": 0, "id": 1},
        )
        if emp:
            filters["employee_id"] = emp["id"]

    result = await _run_assistant_query(db, current_user.tenant_id, query_type, filters)
    result["classified"] = classified
    return result

# ============================================================================
# Phase 3 — Business Assistant Navigation & Context
# ============================================================================
from services.assistant_navigation import (  # noqa: E402
    NAV_TARGETS,
    build_safe_route,
    get_permission_for_target,
    resolve_related_record,
    lookup_customers_by_name,
    lookup_order_by_number,
    lookup_employees_by_name,
)
from models.auth import Permission as _NavPermission  # noqa: E402
Permission = _NavPermission  # alias for this module scope


class AssistantPageContext(BaseModel):
    page: Optional[str] = None
    route: Optional[str] = None
    record_type: Optional[str] = None
    record_id: Optional[str] = None
    record_label: Optional[str] = None


class AssistantResolveRequest(BaseModel):
    message: str
    context: Optional[AssistantPageContext] = None


async def _classify_navigation_intent(message: str, context: Optional[AssistantPageContext]) -> Dict[str, Any]:
    """LLM classifier — navigation + related-record intents only."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import json as _json
    import re as _re

    nav_keys = ", ".join(sorted(NAV_TARGETS.keys()))
    ctx_summary = "None"
    if context and (context.page or context.record_type):
        ctx_summary = (
            f"page={context.page or '?'} route={context.route or '?'} "
            f"record_type={context.record_type or '?'} record_id={context.record_id or '?'} "
            f"record_label={context.record_label or '?'}"
        )

    system_prompt = (
        "Classify a user's request into a navigation intent for a sign-shop app.\n"
        f"Current page context: {ctx_summary}\n\n"
        "KINDS: navigate | related_record | lookup | none\n"
        f"Allowed navigate targets: {nav_keys}\n"
        "Filters: status, due_from, due_to, customer_id, employee_id, period.\n"
        "related_record source_type in {order, invoice, job_ticket, customer, employee}. "
        "target_type in {customer, order, invoice, documents, invoices, orders, time_entries}.\n\n"
        "Rules:\n"
        "- 'this/that/current/here' → use current record_type from context.\n"
        "- 'open this order' w/ order context → navigate, order_detail, use_current_record=true.\n"
        "- 'create an order' or 'new order for this customer' w/ customer context → navigate, new_order, use_current_record=true. "
        "(This is NAVIGATION to a prefilled create form; NOT a write intent.)\n"
        "- 'show related customer' w/ order context → related_record, source_type=order, target_type=customer.\n"
        "- 'show this order's invoice' w/ order context → related_record, source_type=order, target_type=invoice.\n"
        "- If user says 'open invoices', 'show invoices' → navigate, invoices_list.\n"
        "- If user says 'open unpaid invoices' or 'overdue invoices' → navigate, invoices_list, filters.status=overdue.\n"
        "- 'reschedule this' w/ order context → navigate, production_board (selection is up to user once there).\n"
        "- If user says 'open <ORD-xxxx>' or 'show order <ORD-xxxx>' (matches pattern ORD-\\d+) → kind=lookup, lookup_type=order, lookup_query=<the ORD-xxxx value>.\n"
        "- If user says 'open <person or company name>' without a clear page keyword → kind=lookup. "
        "Default lookup_type=customer unless the phrase is clearly about time/schedule (then lookup_type=employee).\n"
        "- Aliases: 'revenue report' / 'financials' / 'financial dashboard' → navigate, financials. "
        "'smart document library' / 'documents' / 'document library' → navigate, documents. "
        "'team' / 'employees' / 'workforce' → navigate, employee_schedule. "
        "'production schedule' / 'production board' / 'production' → navigate, production_board. "
        "'approvals' / 'proof approvals' / 'artwork approvals' → navigate, approvals. "
        "'webstores' / 'webstore orders' → navigate, webstores. "
        "'time clock' / 'timeclock' → navigate, timeclock. "
        "'payroll' / 'pay period' → navigate, payroll. "
        "'dashboard' / 'home' → navigate, dashboard.\n\n"
        "Return ONLY JSON:\n"
        "{\"kind\":\"navigate|related_record|lookup|none\",\n"
        " \"target\":null, \"filters\":{}, \"use_current_record\":false,\n"
        " \"source_type\":null,\"target_type\":null,\n"
        " \"lookup_type\":null,\"lookup_query\":null,\n"
        " \"needs_more_info\":false,\"question\":null}"
    )
    try:
        chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=f"nav_classify_{uuid.uuid4()}", system_message=system_prompt)
        chat.with_model("openai", "gpt-4o-mini")
        resp = await chat.send_message(UserMessage(text=message))
        raw = resp.strip()
        m = _re.search(r"\{.*\}", raw, _re.DOTALL)
        payload = _json.loads(m.group(0)) if m else _json.loads(raw)
    except Exception as exc:
        logger.warning("nav classifier failed: %s", exc)
        payload = {"kind": "none", "needs_more_info": False}
    return payload


def _label_for_target(target: str, filters: Dict[str, Any], params: Dict[str, str]) -> str:
    if target == "invoices_list":
        if filters.get("status") == "overdue":
            return "Open Overdue Invoices"
        return "Open Invoices"
    if target == "orders_list":
        if filters.get("due_from") or filters.get("due_to"):
            return "View Orders (due filter)"
        if filters.get("status") == "overdue":
            return "View Overdue Orders"
        return "Open Orders"
    if target == "order_detail":
        return f"Open Order {params.get('id', '')}".strip()
    if target == "job_ticket_detail":
        return f"Open Ticket {params.get('ticket_id', '')}".strip()
    if target == "new_order":
        if filters.get("customer_name"):
            return f"New Order for {filters['customer_name']}"
        return "New Order"
    if target == "customers_list":
        return "Open Customers"
    if target == "production_board":
        return "Open Production Board"
    if target == "approvals":
        return "Open Approvals"
    if target == "financials":
        return "Open Financials"
    if target == "payroll":
        return "Open Payroll"
    if target == "timesheets":
        return "Open Timesheets"
    if target == "timeclock":
        return "Open Time Clock"
    if target == "employee_schedule":
        return "Open Employee Schedule"
    if target == "webstores":
        return "Open Webstores"
    if target == "documents":
        return "Open Smart Document Library"
    if target == "dashboard":
        return "Open Dashboard"
    return f"Open {target.replace('_', ' ').title()}"


@router.post("/assistant/resolve")
async def assistant_resolve(
    data: AssistantResolveRequest,
    current_user: UserInDB = Depends(get_current_active_user),
):
    """Resolve a user message into safe navigation actions."""
    preview = await preview_credit_usage(db, current_user.tenant_id, "assistant_nav_classify")
    if not preview["sufficient_credits"]:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need {preview['credit_cost']}, have {preview['total_credits']}.",
        )

    classified = await _classify_navigation_intent(data.message, data.context)

    await deduct_credits_after_success(
        db,
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action_type="assistant_nav_classify",
        module="Business Assistant",
        feature_name="assistant_nav_classify",
        metadata={"kind": classified.get("kind")},
    )

    kind = (classified.get("kind") or "none").lower()
    actions: List[Dict[str, Any]] = []
    clarification: Optional[str] = None

    if kind == "navigate":
        target = classified.get("target")
        filters = classified.get("filters") or {}
        params: Dict[str, str] = {}
        if classified.get("use_current_record") and data.context:
            ctx = data.context
            if target == "order_detail" and ctx.record_type == "order" and ctx.record_id:
                params["id"] = ctx.record_id
            elif target == "job_ticket_detail" and ctx.record_type == "job_ticket" and ctx.record_id:
                params["ticket_id"] = ctx.record_id
            elif target == "new_order" and ctx.record_type == "customer" and ctx.record_id:
                filters = {**filters, "customer_id": ctx.record_id}
                if ctx.record_label:
                    filters["customer_name"] = ctx.record_label
        perm = get_permission_for_target(target) if target else None
        if perm and not user_has_permission(current_user.role, perm):
            return {
                "actions": [],
                "classified": classified,
                "message": f"Your role ({current_user.role.value}) can't open that page. Missing: {perm.value}.",
            }
        route = build_safe_route(target, params=params, filters=filters) if target else None
        if route:
            actions.append({
                "kind": "navigate",
                "target": target,
                "label": _label_for_target(target, filters, params),
                "route": route,
                "reason": "direct_navigation",
            })
        else:
            clarification = f"I couldn't build a valid route for '{target or 'unknown'}'."

    elif kind == "related_record":
        source_type = classified.get("source_type")
        target_type = classified.get("target_type")
        if not source_type and data.context and data.context.record_type:
            source_type = data.context.record_type
        source_id = data.context.record_id if data.context else None
        if not source_type or not source_id or not target_type:
            clarification = (
                "I need to know which record to follow from. "
                "Open the record first and ask again."
            )
        else:
            related = await resolve_related_record(db, current_user.tenant_id, source_type, source_id, target_type)
            if related and related.get("route"):
                dest_perm_map = {
                    "customer": Permission.CUSTOMERS_VIEW,
                    "order": Permission.JOBS_VIEW,
                    "invoice": Permission.INVOICES_VIEW,
                    "invoices_list": Permission.INVOICES_VIEW,
                    "orders_list": Permission.JOBS_VIEW,
                    "timesheets": Permission.PAYROLL_VIEW,
                }
                perm = dest_perm_map.get(related.get("target_type"))
                if perm and not user_has_permission(current_user.role, perm):
                    return {
                        "actions": [],
                        "classified": classified,
                        "message": f"Your role ({current_user.role.value}) can't view this related record.",
                    }
                actions.append({
                    "kind": "navigate",
                    "label": f"Open {related['label']}",
                    "route": related["route"],
                    "record_id": related.get("record_id"),
                    "record_type": related.get("target_type"),
                    "reason": "related_record",
                })
            else:
                clarification = f"I couldn't find a related {target_type} for this {source_type}."

    elif kind == "lookup":
        lookup_type = classified.get("lookup_type")
        q = (classified.get("lookup_query") or "").strip()
        if lookup_type == "order":
            order = await lookup_order_by_number(db, current_user.tenant_id, q)
            if order:
                route = build_safe_route("order_detail", params={"id": order["id"]})
                actions.append({
                    "kind": "navigate",
                    "label": f"Open {order['order_number']}",
                    "route": route,
                    "record_id": order["id"],
                    "record_type": "order",
                    "reason": "lookup_order",
                })
            else:
                clarification = f"I couldn't find an order matching '{q}'."
        elif lookup_type == "customer":
            candidates = await lookup_customers_by_name(db, current_user.tenant_id, q, limit=5)
            if len(candidates) == 1:
                c = candidates[0]
                actions.append({
                    "kind": "navigate",
                    "label": f"Open customer {c.get('name') or c.get('company')}",
                    "route": "/customers",
                    "record_id": c["id"],
                    "record_type": "customer",
                    "reason": "lookup_customer",
                })
            elif len(candidates) > 1:
                clarification = f"I found {len(candidates)} customers matching '{q}'. Which one?"
                for c in candidates:
                    actions.append({
                        "kind": "clarify",
                        "label": f"{c.get('name')}{' — ' + c['company'] if c.get('company') else ''}",
                        "route": "/customers",
                        "record_id": c["id"],
                        "record_type": "customer",
                        "reason": "ambiguous_customer",
                    })
            else:
                clarification = f"I couldn't find a customer matching '{q}'."
        elif lookup_type == "employee":
            candidates = await lookup_employees_by_name(db, current_user.tenant_id, q, limit=5)
            if len(candidates) == 1:
                e = candidates[0]
                actions.append({
                    "kind": "navigate",
                    "label": f"Open employee schedule: {e.get('name') or e.get('first_name')}",
                    "route": build_safe_route("employee_schedule", filters={"employee_id": e["id"]}),
                    "record_id": e["id"],
                    "record_type": "employee",
                    "reason": "lookup_employee",
                })
            elif len(candidates) > 1:
                clarification = f"I found {len(candidates)} employees matching '{q}'. Which one?"
                for e in candidates:
                    full = e.get("name") or f"{e.get('first_name', '')} {e.get('last_name', '')}".strip()
                    actions.append({
                        "kind": "clarify",
                        "label": full or e["id"],
                        "route": build_safe_route("employee_schedule", filters={"employee_id": e["id"]}),
                        "record_id": e["id"],
                        "record_type": "employee",
                        "reason": "ambiguous_employee",
                    })
            else:
                clarification = f"I couldn't find an employee matching '{q}'."

    if not actions and not clarification:
        clarification = (
            "That doesn't look like a navigation request. "
            "Try: 'open overdue invoices', 'take me to production', 'show this customer'."
        )

    return {
        "actions": actions,
        "message": clarification,
        "classified": classified,
    }

