"""
AI Tools Routes

This module contains routes for AI-powered tools:
- Text content generation (GPT-5.2)
- Image generation (GPT Image 1)
- AI history
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid
import os
import base64
from dotenv import load_dotenv

load_dotenv()

from server import db, get_current_active_user
from models import UserInDB

router = APIRouter(prefix="/ai", tags=["AI Tools"])

# Get API key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


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

    # NEW TOOLS - Completed Job Post Creator
    "completed_job_post": """You are a social media expert for sign shops. Based on the uploaded photo of a completed job, create engaging social media content.

**Job Type:** {job_type}
**Job Details:** {job_details}
**Client Industry:** {client_industry}
**Platform:** {platforms}
**Post Style:** {post_style}
**Include Hashtags:** {include_hashtags}

Analyze the uploaded image and create:

1. **Primary Post Caption** (platform-optimized length):
   - Hook/attention-grabber in first line
   - Describe the work showcased
   - Highlight craftsmanship, challenges overcome, or unique features
   - Include the call to action
   - Match the requested post style

2. **Alternative Caption** - A shorter or different angle version

3. **Hashtag Set** (if requested):
   - Industry hashtags (#signshop, #vehiclewrap, etc.)
   - Local/service area hashtags (suggest format)
   - Trending relevant hashtags
   - Branded hashtag suggestion

4. **Best Posting Tips**:
   - Optimal posting time for this content type
   - Suggested story/reel content ideas
   - Engagement prompt suggestions

Keep client confidentiality - use industry description, not names.
Make the content genuinely engaging, not generic or salesy.""",

    # Original NEW TOOLS
    "idea_brainstormer": """You are a creative brainstorming expert for sign shops and their clients. Generate creative ideas based on:

**Request Type:** {brainstorm_type}
**Business/Brand:** {business_name}
**Industry:** {industry}
**Target Audience:** {target_audience}
**Key Values/USP:** {key_values}
**Desired Tone:** {tone}
**Things to Avoid:** {avoid}

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

    "ai_sign_designer": """Create a professional sign design concept for:

Business: {business_name}
Type: {business_type}
Sign Type: {sign_type}
Size: {size}
Colors: {colors}
Additional Text: {additional_text}
Style: {style_preference}

Generate a detailed visual description for a {sign_type} sign that would work for this business.""",

    "ai_banner_designer": """Create a banner design concept for:

Headline: {headline}
Supporting Text: {subtext}
Size: {banner_size}
Purpose: {event_type}
Colors: {brand_colors}
Style: {style}

Generate a detailed visual description for this promotional banner.""",

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

    "social_pack_generator": """Generate {pack_size} social media post ideas for a sign shop:

Services: {services_offered}
Target Audience: {target_audience}
Content Mix: {content_mix}

For each post provide:
- Post type (educational, promotional, behind-scenes, etc.)
- Caption/copy
- Visual suggestion
- Best platform for this content
- Hashtag suggestions""",

    "content_calendar": """Create a {date_range} content calendar for a sign shop:

Platforms: {platforms}
Goals: {goals}
Upcoming Events: {upcoming_events}

Provide a structured calendar with:
- Posting schedule by day
- Content themes for each day
- Specific post ideas
- Important dates to leverage
- Content mix balance""",

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
    "branding_kit_generator": """You are a brand strategist for sign shops. Create a complete brand system with guidelines:

**Logo Description:** {logo_description}
**Brand Personality:** {brand_tone}
**Target Audience:** {target_audience}
**Competitors:** {competitors}

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

    "logo_creator": """Professional logo design for "{business_name}".
Industry: {industry}.
Logo style: {logo_type}, {style_preferences} aesthetic.
Colors: {color_preferences}.
Tagline to incorporate: {tagline}.
Icon/symbol ideas: {icon_ideas}.
The logo should be clean, scalable, memorable, and work well on signage.
Professional brand identity design, vector-style appearance, white or transparent background.
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
    request: AIGenerateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate AI text content"""
    from services.multi_product_gate import get_multi_product_feature_gate
    from services.credit_service import check_and_deduct_credits
    
    # Check feature access
    gate = get_multi_product_feature_gate(db)
    await gate.require_feature(current_user.tenant_id, "ai_tools", "text_generation")
    
    # Check and deduct credits
    success, credits_used, message = await check_and_deduct_credits(
        db, 
        current_user.tenant_id, 
        request.tool,
        {"tool": request.tool}
    )
    if not success:
        raise HTTPException(status_code=402, detail=message)
    
    try:
        result = await generate_text_content(request.tool, request.input_data)
        
        # Save to history
        history_entry = {
            "id": str(uuid.uuid4()),
            "tool": request.tool,
            "input_data": request.input_data,
            "output": result,
            "images": None,
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "credits_used": credits_used,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.ai_history.insert_one(history_entry)
        
        return {"content": result, "id": history_entry["id"], "credits_used": credits_used}
    except HTTPException:
        raise
    except Exception as e:
        print(f"AI generation error: {e}")
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@router.post("/generate-images")
async def generate_ai_images(
    request: AIGenerateImageRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate AI images"""
    from services.multi_product_gate import get_multi_product_feature_gate
    from services.credit_service import check_and_deduct_credits
    
    # Check feature access
    gate = get_multi_product_feature_gate(db)
    await gate.require_feature(current_user.tenant_id, "ai_tools", "image_generation")
    
    # Check and deduct credits for image generation
    success, credits_used, message = await check_and_deduct_credits(
        db, 
        current_user.tenant_id, 
        "image_generation",
        {"tool": request.tool, "image_count": request.image_count}
    )
    if not success:
        raise HTTPException(status_code=402, detail=message)
    
    try:
        images = await generate_images(request.tool, request.input_data, request.image_count)
        
        if not images:
            raise HTTPException(status_code=500, detail="No images were generated")
        
        # Save to history
        history_entry = {
            "id": str(uuid.uuid4()),
            "tool": request.tool,
            "input_data": request.input_data,
            "output": None,
            "images": images,
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.ai_history.insert_one(history_entry)
        
        return {"images": images, "id": history_entry["id"]}
    except HTTPException:
        raise
    except Exception as e:
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
    request: ProductDescriptionRequest,
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
    tone = request.tone.lower() if request.tone.lower() in valid_tones else "professional"
    
    try:
        # Prepare input data for the template
        input_data = {
            "product_name": request.product_name,
            "product_category": request.product_category,
            "product_features": request.product_features or "Standard quality product",
            "target_audience": request.target_audience or "general consumers",
            "tone": tone,
            "price": request.price if request.price > 0 else "competitive",
        }
        
        # Generate using existing infrastructure
        result = await generate_text_content("product_description", input_data)
        
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
        print(f"Product description generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate product description: {str(e)}")


def parse_product_description(text: str) -> dict:
    """Parse the generated description to extract structured components"""
    result = {
        "headline": "",
        "bullet_points": [],
        "call_to_action": ""
    }
    
    lines = text.split('\n')
    
    # Extract headline (usually first non-empty line or after "Headline Hook")
    for i, line in enumerate(lines):
        line = line.strip()
        if "headline" in line.lower() and i + 1 < len(lines):
            result["headline"] = lines[i + 1].strip().strip('*').strip('"').strip()
            break
        elif line and not line.startswith('#') and not line.startswith('*') and len(line) < 150:
            if not result["headline"] and line:
                result["headline"] = line.strip('*').strip('"').strip()
    
    # Extract bullet points
    in_bullet_section = False
    for line in lines:
        line = line.strip()
        if "bullet" in line.lower() or "selling points" in line.lower():
            in_bullet_section = True
            continue
        if in_bullet_section:
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                bullet = line.lstrip('-•* ').strip()
                if bullet and len(bullet) > 10:
                    result["bullet_points"].append(bullet)
            elif line.startswith('#') or "call to action" in line.lower():
                in_bullet_section = False
    
    # Extract call to action
    for i, line in enumerate(lines):
        if "call to action" in line.lower() and i + 1 < len(lines):
            cta = lines[i + 1].strip().strip('*').strip('"').strip()
            if cta:
                result["call_to_action"] = cta
            break
    
    # Fallback: if no bullet points found, extract any lines starting with - or •
    if not result["bullet_points"]:
        for line in lines:
            line = line.strip()
            if line.startswith('-') or line.startswith('•'):
                bullet = line.lstrip('-•* ').strip()
                if bullet and len(bullet) > 10:
                    result["bullet_points"].append(bullet)
    
    return result


# ============== AI BUSINESS ASSISTANT ==============

class AIAssistantRequest(BaseModel):
    message: str
    session_id: str
    conversation_history: Optional[List[Dict[str, str]]] = None


async def get_shop_context(tenant_id: str) -> dict:
    """Fetch comprehensive shop data for AI context"""
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    
    # Get tenant info
    tenant = await db.tenants.find_one({"id": tenant_id}, {"_id": 0})
    company_name = tenant.get("company_name", "Your Shop") if tenant else "Your Shop"
    
    # Get customer stats
    total_customers = await db.customers.count_documents({"tenant_id": tenant_id})
    new_customers_30d = await db.customers.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    })
    
    # Get job stats
    total_jobs = await db.jobs.count_documents({"tenant_id": tenant_id})
    active_jobs = await db.jobs.count_documents({"tenant_id": tenant_id, "status": {"$in": ["pending", "in_progress", "production"]}})
    completed_jobs_30d = await db.jobs.count_documents({
        "tenant_id": tenant_id, 
        "status": "completed",
        "updated_at": {"$gte": thirty_days_ago.isoformat()}
    })
    
    # Get revenue from invoices
    paid_invoices = await db.invoices.find({
        "tenant_id": tenant_id,
        "status": "paid"
    }, {"_id": 0, "total": 1, "paid_at": 1, "created_at": 1}).to_list(1000)
    
    total_revenue = sum(inv.get("total", 0) for inv in paid_invoices)
    revenue_30d = sum(inv.get("total", 0) for inv in paid_invoices 
                      if inv.get("paid_at", inv.get("created_at", "")) >= thirty_days_ago.isoformat())
    
    # Get pending invoices
    pending_invoices = await db.invoices.find({
        "tenant_id": tenant_id,
        "status": {"$in": ["sent", "draft", "overdue"]}
    }, {"_id": 0, "total": 1}).to_list(500)
    pending_revenue = sum(inv.get("total", 0) for inv in pending_invoices)
    
    # Get quote stats
    total_quotes = await db.quotes.count_documents({"tenant_id": tenant_id})
    quotes_30d = await db.quotes.count_documents({
        "tenant_id": tenant_id,
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    })
    accepted_quotes = await db.quotes.count_documents({"tenant_id": tenant_id, "status": "accepted"})
    quote_conversion_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0
    
    # Get job categories/types breakdown
    jobs_pipeline = [
        {"$match": {"tenant_id": tenant_id}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_value": {"$sum": "$total"}}},
        {"$sort": {"total_value": -1}},
        {"$limit": 10}
    ]
    job_categories = await db.jobs.aggregate(jobs_pipeline).to_list(10)
    
    # Get top customers by revenue
    customer_pipeline = [
        {"$match": {"tenant_id": tenant_id, "status": "paid"}},
        {"$group": {"_id": "$customer_id", "total_spent": {"$sum": "$total"}, "invoice_count": {"$sum": 1}}},
        {"$sort": {"total_spent": -1}},
        {"$limit": 5}
    ]
    top_customers_data = await db.invoices.aggregate(customer_pipeline).to_list(5)
    
    # Enrich with customer names
    top_customers = []
    for tc in top_customers_data:
        customer = await db.customers.find_one({"id": tc["_id"]}, {"_id": 0, "name": 1})
        if customer:
            top_customers.append({
                "name": customer.get("name", "Unknown"),
                "total_spent": tc["total_spent"],
                "orders": tc["invoice_count"]
            })
    
    # Get employee count
    employee_count = await db.employees.count_documents({"tenant_id": tenant_id})
    
    # Get webstore stats
    webstore_count = await db.webstores_v2.count_documents({"tenant_id": tenant_id})
    webstore_orders = await db.webstore_orders.count_documents({"tenant_id": tenant_id})
    
    # Calculate average job value
    avg_job_value = total_revenue / total_jobs if total_jobs > 0 else 0
    
    return {
        "company_name": company_name,
        "customers": {
            "total": total_customers,
            "new_last_30_days": new_customers_30d
        },
        "jobs": {
            "total": total_jobs,
            "active": active_jobs,
            "completed_last_30_days": completed_jobs_30d,
            "average_value": round(avg_job_value, 2)
        },
        "revenue": {
            "total_all_time": round(total_revenue, 2),
            "last_30_days": round(revenue_30d, 2),
            "pending": round(pending_revenue, 2)
        },
        "quotes": {
            "total": total_quotes,
            "last_30_days": quotes_30d,
            "conversion_rate": round(quote_conversion_rate, 1)
        },
        "job_categories": [{"category": jc["_id"] or "Uncategorized", "count": jc["count"], "revenue": round(jc.get("total_value", 0), 2)} for jc in job_categories],
        "top_customers": top_customers,
        "team_size": employee_count,
        "webstores": {
            "count": webstore_count,
            "total_orders": webstore_orders
        }
    }


@router.post("/assistant")
async def ai_business_assistant(
    request: AIAssistantRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """AI Business Assistant - Chat interface for sign shop operations with real shop data"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from services.multi_product_gate import get_multi_product_feature_gate
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Check feature access
    gate = get_multi_product_feature_gate(db)
    await gate.require_feature(current_user.tenant_id, "ai_assistant", "assistant_access")
    await gate.require_feature(current_user.tenant_id, "ai_assistant", "monthly_queries", increment_usage=True)
    
    # Check if business data access is allowed
    data_aware_result = await gate.check_feature(current_user.tenant_id, "ai_assistant", "business_data_aware")
    data_limited_result = await gate.check_feature(current_user.tenant_id, "ai_assistant", "business_data_limited")
    
    has_business_data_access = data_aware_result.allowed or data_limited_result.allowed
    
    try:
        # Only fetch shop data if user has access
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
            # Non-data-aware mode - provide generic sign shop context
            shop_summary = """
## Note: Operating in generic mode (no access to your business data)

I can help with general sign shop questions, industry best practices, and advice,
but I don't have access to your specific customer, job, or financial data.

To get personalized insights based on your actual business data, please upgrade your plan.
"""
        
        # Build conversation context from history
        # Build conversation context from history
        context_messages = ""
        if request.conversation_history:
            for msg in request.conversation_history[-6:]:  # Last 6 messages for context
                role = "User" if msg.get("role") == "user" else "Assistant"
                context_messages += f"{role}: {msg.get('content', '')}\n\n"
        
        # Build system message based on data access level
        if has_business_data_access and shop_data:
            system_message = f"""You are the AI Business Assistant for SignGuy AI, a comprehensive sign shop management platform. You are chatting with {current_user.full_name or 'the owner'} from {shop_data['company_name']}.

## Your Role
You have FULL ACCESS to this shop's real business data (shown below). Use this data to give SPECIFIC, PERSONALIZED answers - never generic advice.

{shop_summary}

## Your Knowledge
- **Sign Industry Operations**: Vehicle wraps, channel letters, monument signs, banners, vinyl graphics, dimensional letters, LED signs, A-frames, window graphics, wall wraps, trade show displays
- **Materials & Production**: Vinyl types (cast, calendered, reflective), substrates (ACM, PVC, MDO), laminates, print technologies, installation techniques
- **Business Management**: Pricing strategies, profit margins (industry standard 40-60%), job costing, time tracking, workflow optimization
- **SignGuy AI Features**: You know this platform has Quotes, Jobs, Invoices, Customers, Time Tracking, Webstores, Employee Portal, AI Tools, and more

## How to Respond
1. ALWAYS use the shop's actual data when answering questions about their business
2. Reference specific numbers: "Your average job is ${shop_data['jobs']['average_value']:,.2f}" not "typically shops charge..."
3. Identify their best-performing categories and customers from the data
4. If asked about profit margins, calculate using THEIR data
5. Be conversational but data-driven
6. For questions about features, explain how to use SignGuy AI

## Examples of Good Responses
- "Looking at your data, your top category is [X] with $[Y] in revenue. Here's how to grow it..."
- "Your quote conversion rate is {shop_data['quotes']['conversion_rate']}% - here are 3 ways to improve it..."
- "Based on your {shop_data['jobs']['active']} active jobs, here's how to optimize workflow..."

Never say "if you upload your data" or "tell me what software you use" - you already have their data!"""
        else:
            # Non-data-aware mode
            system_message = f"""You are the AI Business Assistant for SignGuy AI, a comprehensive sign shop management platform.

## Your Role
You are operating in GENERAL ADVICE MODE. You can help with sign industry best practices, but you don't have access to this user's specific business data.

{shop_summary}

## Your Knowledge
- **Sign Industry Operations**: Vehicle wraps, channel letters, monument signs, banners, vinyl graphics, dimensional letters, LED signs, A-frames, window graphics, wall wraps, trade show displays
- **Materials & Production**: Vinyl types (cast, calendered, reflective), substrates (ACM, PVC, MDO), laminates, print technologies, installation techniques
- **Business Management**: Pricing strategies, profit margins (industry standard 40-60%), job costing, time tracking, workflow optimization
- **SignGuy AI Features**: You know this platform has Quotes, Jobs, Invoices, Customers, Time Tracking, Webstores, Employee Portal, AI Tools, and more

## How to Respond
1. Provide helpful general advice about the sign industry
2. Share industry benchmarks and best practices
3. If they ask about their specific data, politely explain you don't have access and suggest they upgrade for personalized insights
4. Be conversational and helpful

Note: For personalized insights based on their actual business data, users can upgrade to a Pro or Business plan."""
        
        # Initialize chat with the session
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=request.session_id,
            system_message=system_message
        ).with_model("openai", "gpt-5.2")
        
        # Build the prompt with context
        if context_messages:
            full_prompt = f"Previous conversation:\n{context_messages}\nUser's new message: {request.message}"
        else:
            full_prompt = request.message
        
        # Send message and get response
        response = await chat.send_message(UserMessage(text=full_prompt))
        
        # Log AI usage
        await db.ai_usage_logs.insert_one({
            "tenant_id": current_user.tenant_id,
            "user_id": current_user.id,
            "tool": "business_assistant",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {"response": response}
        
    except Exception as e:
        print(f"AI Assistant error: {e}")
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")


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
    request: EmailGenerateRequest,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """Generate professional email content using AI"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    email_type = request.email_type
    if email_type not in EMAIL_TYPE_PROMPTS:
        raise HTTPException(status_code=400, detail=f"Unknown email type: {email_type}")
    
    try:
        # Build context string from provided context
        context = request.context
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

Tone: {request.tone}

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


class ConfirmActionRequest(BaseModel):
    """Request to confirm a pending action"""
    action_id: str
    confirm: bool  # True to execute, False to cancel


@router.post("/assistant/action")
async def execute_assistant_action(
    request: ExecuteActionRequest,
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
        action_type = ActionType(request.action_type)
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid action type: {request.action_type}. Valid types: {[a.value for a in ActionType]}"
        )
    
    actions = get_ai_assistant_actions(db)
    
    action_request = ActionRequest(
        action_type=action_type,
        parameters=request.parameters
    )
    
    response = await actions.execute_action(
        user=current_user,
        action_request=action_request,
        confirmed=request.confirmed
    )
    
    return response.model_dump()


@router.post("/assistant/action/confirm")
async def confirm_assistant_action(
    request: ConfirmActionRequest,
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
        "action_id": request.action_id,
        "tenant_id": current_user.tenant_id,
        "status": ActionStatus.PENDING_CONFIRMATION.value
    }, {"_id": 0})
    
    if not pending:
        raise HTTPException(
            status_code=404,
            detail="Pending action not found or already processed"
        )
    
    if not request.confirm:
        # Cancel the action
        await db.ai_action_audit.update_one(
            {"action_id": request.action_id},
            {"$set": {
                "status": ActionStatus.CANCELLED.value,
                "cancelled_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {
            "action_id": request.action_id,
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
        {"action_id": request.action_id},
        {"$set": {
            "status": response.status.value,
            "confirmed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return response.model_dump()


@router.get("/assistant/actions/audit")
async def get_action_audit_log(
    limit: int = 50,
    action_type: Optional[str] = None,
    current_user: UserInDB = Depends(get_current_active_user)
):
    """
    Get audit log of AI Assistant actions for the tenant.
    
    Returns all actions executed via the AI Assistant, including:
    - Action type and parameters
    - Status (executed, failed, cancelled, pending)
    - Results or errors
    - Timestamps
    """
    actions = get_ai_assistant_actions(db)
    
    at = None
    if action_type:
        try:
            at = ActionType(action_type)
        except ValueError:
            pass
    
    entries = await actions.get_action_audit_log(
        tenant_id=current_user.tenant_id,
        limit=limit,
        action_type=at
    )
    
    return {"audit_log": entries, "count": len(entries)}


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
