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
8. Budget Allocation Suggestions"""
}

IMAGE_PROMPTS = {
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
Marketing banner suitable for outdoor or indoor display."""
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
    except KeyError as e:
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
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.ai_history.insert_one(history_entry)
        
        return {"content": result, "id": history_entry["id"]}
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
