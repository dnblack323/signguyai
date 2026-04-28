# Marketing Tools Simple Audit

**Audit Date:** 2026-04-28
**Scope:** 6 Marketing category tools only
**Purpose:** Review for future improvements - no code changes

---

# Tool Name: Blog Article Creator

## 1. What does this tool do?
Generates full blog articles for sign shop websites on industry topics. Can either write about a user-provided topic or suggest topics based on a category.

## 2. Where is it located?
- **Page:** AI Tools > Marketing
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 317-333)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["blog_creator"] (line 63)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Topic Source | `topic_type` | select | Yes | None |
| Your Topic (if you have one) | `topic` | text | No | None |
| Topic Area (for suggestions) | `topic_area` | select | No | None |
| Article Length | `article_length` | select | No | None |
| Writing Tone | `tone` | select | No | None |
| Target Reader | `target_audience` | text | No | None |
| Call to Action | `include_cta` | select | No | None |
| SEO Keywords (optional) | `seo_keywords` | text | No | None |

**Topic Type Options:** i_have_a_topic, suggest_topics_for_me

**Topic Area Options:** vehicle_wraps, business_signage, trade_shows, window_graphics, branding, marketing_tips, industry_trends, how_to_guides, customer_stories

**Article Length Options:** short_500_words, medium_800_words, long_1200_words, comprehensive_1500_plus

**Tone Options:** professional_informative, friendly_conversational, authoritative_expert, casual_engaging

**CTA Options:** contact_for_quote, schedule_consultation, view_portfolio, download_guide, none

## 4. How do the fields affect the AI output?
- **topic_type** - Critical. Determines if AI suggests topics or uses user-provided topic.
- **topic** - The main subject matter for the article.
- **topic_area** - Used when AI suggests topics - narrows the category.
- **article_length** - Directly affects word count and depth.
- **tone** - Affects writing style throughout the article.
- **target_audience** - Influences language complexity and examples used.
- **include_cta** - Determines the call to action at the end.
- **seo_keywords** - Incorporated naturally throughout the article.

## 5. What prompt or instructions does it send to AI?
The prompt instructs the AI to:
- Act as an expert content writer for the sign/graphics industry
- Suggest 5 topics first if user selected "suggest_topics_for_me"
- Create a complete blog article with:
  - SEO-optimized title (under 60 chars)
  - Meta description (150-160 chars)
  - Introduction with hook
  - Main body with H2 headers
  - Conclusion with call to action
  - 2-3 suggested image descriptions

**Strengths:**
- Very comprehensive prompt
- Includes SEO elements
- Industry-specific context
- Includes image suggestions

**Issues:**
- None significant. This is one of the better prompts.

## 6. What does it output?
- SEO-optimized blog title
- Meta description
- Full article with headers
- Call to action
- Image suggestions
- **Format:** Structured long-form text

## 7. Where does the output go?
- Displays on screen in result area
- Saved to `ai_history` collection
- Can be copied manually (no dedicated copy button)
- Persists in history after refresh

## 8. Does it use real app/business/brand data?
- **Business profile:** No (could use company name)
- **Brand voice:** No
- **Customer data:** No
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No copy button
- Doesn't pull company name/brand info from settings
- No "Save to Document Library" option
- No "Publish to Website" workflow (would require CMS integration)
- Missing company-specific context field

## 10. What would you recommend changing?
1. Add "Copy to Clipboard" button
2. Pre-fill company name from tenant settings
3. Add "Save to Document Library" option
4. Add brand voice/guidelines field for consistency
5. Consider adding featured image generation (pair with image AI)

---

# Tool Name: Completed Order Post Creator

## 1. What does this tool do?
Takes an uploaded photo of completed work and generates ready-to-post social media content. This is the image-based version for showcasing finished projects.

## 2. Where is it located?
- **Page:** AI Tools > Marketing
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 335-349)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["completed_job_post"] (line 95)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Upload Completed Order Photo | `image_upload` | image_upload | Yes | None |
| What Did You Create? | `job_type` | select | Yes | None |
| Order Details | `job_details` | textarea | No | None |
| Client Industry (no names) | `client_industry` | text | No | None |
| Posting To | `platforms` | select | No | None |
| Post Style | `post_style` | select | No | None |
| Include Hashtags? | `include_hashtags` | select | No | None |

**Job Type Options:** full_vehicle_wrap, partial_vehicle_wrap, fleet_graphics, storefront_sign, channel_letters, monument_sign, wall_mural, window_graphics, banner, trade_show_display, dimensional_letters, awning, a_frame_sign, yard_signs, interior_signage, other

**Platform Options:** facebook, instagram, linkedin, tiktok, all_platforms

**Post Style Options:** professional_showcase, behind_the_scenes, before_after, educational, casual_fun

**Hashtag Options:** yes_full_set, yes_minimal, no

## 4. How do the fields affect the AI output?
- **image_upload** - Critical. The AI analyzes the photo to describe the work.
- **job_type** - Helps AI understand what's in the image and use correct terminology.
- **job_details** - Adds context the AI can't see in the image (challenges, materials, etc.).
- **client_industry** - Used for context without revealing client names.
- **platforms** - Affects caption length and format (Instagram vs LinkedIn style).
- **post_style** - Changes the tone and approach of the post.
- **include_hashtags** - Controls whether hashtags are included and how many.

## 5. What prompt or instructions does it send to AI?
The prompt instructs the AI to:
- Act as a social media expert for sign shops
- Analyze the uploaded image
- Create:
  1. Primary post caption with hook, description, CTA
  2. Alternative caption (shorter/different angle)
  3. Hashtag set (industry, local, trending, branded)
  4. Posting tips (optimal time, story ideas, engagement prompts)

**Strengths:**
- Multiple caption versions
- Platform-specific guidance
- Confidentiality reminder
- Includes posting strategy tips

**Issues:**
- Prompt says "analyze the uploaded image" but unclear if image is actually sent to vision AI

## 6. What does it output?
- Primary social media caption
- Alternative caption
- Hashtag set
- Posting tips
- **Format:** Structured text for social posting

## 7. Where does the output go?
- Displays on screen
- Saved to `ai_history`
- Can be copied manually
- Image stored in upload system

## 8. Does it use real app/business/brand data?
- **Business profile:** No
- **Uploaded image:** Yes - key input
- **Order data:** No (could link to actual order)
- **Only uses:** Uploaded image + typed info

## 9. Are there any obvious issues?
- No copy button for each section
- Unclear if AI actually analyzes the image or just uses metadata
- No direct "Post to Facebook/Instagram" integration
- No link to actual order record
- No before/after image pair support

## 10. What would you recommend changing?
1. Verify image is actually sent to vision AI (not just stored)
2. Add "Copy Caption" and "Copy Hashtags" buttons
3. Add "Link to Order" option to pull order details automatically
4. Add before/after image pair upload
5. Consider social media posting integration (Buffer, Later, etc.)

---

# Tool Name: Social Media Job Post Creator

## 1. What does this tool do?
Creates social media posts about completed sign projects based on text description (no image upload). A simpler, text-only version of the Completed Order Post Creator.

## 2. Where is it located?
- **Page:** AI Tools > Marketing
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 352-364)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["social_job_post"] (line 579)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Describe the Completed Job | `job_description` | textarea | No* | None |
| Order Type | `job_type` | select | No | None |
| Client Industry (no names) | `client_industry` | text | No | None |
| Target Platforms | `platforms` | select | No | None |

*No fields marked required.

**Job Type Options:** vehicle_wrap, storefront_sign, monument_sign, interior_signage, banner, window_graphics, fleet_graphics, dimensional_letters

**Platform Options:** facebook, instagram, linkedin, all_platforms

## 4. How do the fields affect the AI output?
- **job_description** - Main content for the post.
- **job_type** - Helps with terminology and hashtag selection.
- **client_industry** - Context without revealing names.
- **platforms** - Affects format and style.

## 5. What prompt or instructions does it send to AI?
The prompt is simpler than completed_job_post:
- Create engaging caption
- Relevant hashtags (10-15)
- Call to action
- Keep client confidentiality

**Issues:**
- Very basic prompt compared to completed_job_post
- No post style option
- No alternative captions
- No posting tips
- Essentially a stripped-down duplicate of completed_job_post

## 6. What does it output?
- Social media caption
- Hashtags
- Call to action
- **Format:** Short text for social posting

## 7. Where does the output go?
- Displays on screen
- Saved to `ai_history`
- Can be copied manually

## 8. Does it use real app/business/brand data?
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- **Duplicate functionality** with Completed Order Post Creator
- No required fields
- Less comprehensive than the image-based version
- No copy button
- Missing post_style and include_hashtags options

## 10. What would you recommend changing?
1. **Consider removing** - this overlaps heavily with Completed Order Post Creator
2. OR differentiate it clearly (e.g., "Quick Post Creator" for fast posts without images)
3. Add required fields if keeping
4. Match features from completed_job_post (post_style, hashtag options)
5. Add copy button

---

# Tool Name: Social Media Pack Generator

## 1. What does this tool do?
Generates a batch of social media content ideas (5-30 posts) for planning ahead. Creates multiple post concepts at once rather than one at a time.

## 2. Where is it located?
- **Page:** AI Tools > Marketing
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 366-378)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["social_pack_generator"] (line 420)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Services You Offer | `services_offered` | textarea | No | None |
| Number of Posts | `pack_size` | select | No | None |
| Target Audience | `target_audience` | text | No | None |
| Content Focus | `content_mix` | select | No | None |

**Pack Size Options:** 5_posts, 10_posts, 15_posts, 30_posts

**Content Mix Options:** mostly_promotional, mostly_educational, behind_the_scenes, balanced_mix

## 4. How do the fields affect the AI output?
- **services_offered** - Determines what services to feature in posts.
- **pack_size** - Controls how many post ideas are generated.
- **target_audience** - Influences content angle and messaging.
- **content_mix** - Affects the balance of post types.

## 5. What prompt or instructions does it send to AI?
The prompt requests for each post:
- Post type (educational, promotional, behind-scenes, etc.)
- Caption/copy
- Visual suggestion
- Best platform for this content
- Hashtag suggestions

**Strengths:**
- Batch generation saves time
- Includes visual suggestions
- Platform recommendations per post

**Issues:**
- No platform filter (generates for all, user may only want Instagram)
- Missing tone/brand voice option

## 6. What does it output?
- Multiple post ideas (5-30)
- Each with: type, caption, visual suggestion, platform, hashtags
- **Format:** Structured list of post concepts

## 7. Where does the output go?
- Displays on screen
- Saved to `ai_history`
- Can be copied manually
- No export to spreadsheet/calendar

## 8. Does it use real app/business/brand data?
- **Business profile:** No
- **Order data:** No (could pull recent completed orders)
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No required fields
- No export to CSV/spreadsheet
- No platform filter
- No copy button
- No link to Content Calendar tool
- Doesn't pull services from tenant settings

## 10. What would you recommend changing?
1. Add required fields (at least services_offered)
2. Add "Export to CSV" or "Copy All" button
3. Add platform filter option
4. Add tone/brand voice option
5. Pre-fill services from tenant settings
6. Add "Send to Content Calendar" integration

---

# Tool Name: Content Calendar Creator

## 1. What does this tool do?
Creates a structured posting schedule for 1 week to 1 month, with content themes and specific post ideas for each day.

## 2. Where is it located?
- **Page:** AI Tools > Marketing
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 380-391)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["content_calendar"] (line 433)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Time Period | `date_range` | select | No | None |
| Platforms | `platforms` | text | No | None |
| Marketing Goals | `goals` | textarea | No | None |
| Upcoming Events/Promotions | `upcoming_events` | textarea | No | None |

**Date Range Options:** 1_week, 2_weeks, 1_month

## 4. How do the fields affect the AI output?
- **date_range** - Determines calendar length and number of posts.
- **platforms** - Affects which platforms are included in the schedule.
- **goals** - Influences content direction and strategy.
- **upcoming_events** - Special dates are worked into the calendar.

## 5. What prompt or instructions does it send to AI?
The prompt requests:
- Posting schedule by day
- Content themes for each day
- Specific post ideas
- Important dates to leverage
- Content mix balance

**Strengths:**
- Structured calendar format
- Incorporates events/promotions
- Goal-oriented

**Issues:**
- No actual date selection (can't pick specific start date)
- Text output, not visual calendar
- Missing posting frequency option

## 6. What does it output?
- Day-by-day posting schedule
- Themes and post ideas
- Important dates
- **Format:** Structured text calendar

## 7. Where does the output go?
- Displays on screen
- Saved to `ai_history`
- Can be copied manually
- No export to actual calendar format

## 8. Does it use real app/business/brand data?
- **Business profile:** No
- **Appointment data:** No (could integrate)
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No required fields
- No actual start date picker
- No export to iCal/Google Calendar
- No export to spreadsheet
- No copy button
- Doesn't integrate with Social Pack Generator

## 10. What would you recommend changing?
1. Add start date picker
2. Add "Export to CSV" option
3. Add "Export to Google Calendar" option
4. Add posting frequency option (1x/day, 3x/week, etc.)
5. Add integration with Social Pack Generator outputs
6. Add required fields

---

# Tool Name: Campaign Builder

## 1. What does this tool do?
Designs complete marketing campaigns with strategy, messaging, channel selection, timeline, and budget allocation for specific business goals.

## 2. Where is it located?
- **Page:** AI Tools > Marketing
- **Frontend:** `/app/frontend/src/pages/AITools.js` (lines 393-407)
- **Backend:** `/app/backend/routes/ai.py` - TOOL_PROMPTS["campaign_builder"] (line 446)
- **API:** POST `/api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|-------------|---------------|------|----------|---------|
| Campaign Type | `campaign_type` | select | No | None |
| Primary Goal | `campaign_goal` | text | No | None |
| Target Audience | `target_audience` | textarea | No | None |
| Budget Range | `budget_range` | select | No | None |
| Campaign Duration | `duration` | select | No | None |

**Campaign Type Options:** grand_opening, seasonal_sale, new_service_launch, referral_program, holiday_promotion

**Budget Range Options:** under_500, 500_to_1000, 1000_to_2500, 2500_plus

**Duration Options:** 1_week, 2_weeks, 1_month

## 4. How do the fields affect the AI output?
- **campaign_type** - Determines overall campaign framework and tactics.
- **campaign_goal** - Specific objective to optimize for.
- **target_audience** - Influences messaging and channel selection.
- **budget_range** - Affects channel recommendations and scope.
- **duration** - Impacts timeline and milestones.

## 5. What prompt or instructions does it send to AI?
The prompt requests a complete campaign plan with 8 sections:
1. Campaign Overview & Objectives
2. Target Audience Profile
3. Key Messages & Offers
4. Channel Strategy (which platforms, why)
5. Content Plan (what to create)
6. Timeline & Milestones
7. Success Metrics to Track
8. Budget Allocation Suggestions

**Strengths:**
- Very comprehensive structure
- Includes budget allocation
- Success metrics included
- Practical and actionable

**Issues:**
- None significant. This is a strong prompt.

## 6. What does it output?
- Complete marketing campaign plan
- Strategy, messaging, channels, timeline
- Budget recommendations
- Success metrics
- **Format:** Comprehensive structured document

## 7. Where does the output go?
- Displays on screen
- Saved to `ai_history`
- Can be copied manually
- No export to project document

## 8. Does it use real app/business/brand data?
- **Business profile:** No (could use for branding)
- **Customer data:** No (could use for audience insights)
- **Only uses:** Text typed by user

## 9. Are there any obvious issues?
- No required fields
- No copy button
- No "Save as Campaign" option
- No export to PDF
- Doesn't integrate with Content Calendar
- Campaign types are limited

## 10. What would you recommend changing?
1. Add required fields (at least campaign_type and campaign_goal)
2. Add "Copy to Clipboard" button
3. Add "Export as PDF" option
4. Add more campaign types (awareness, lead gen, retention, etc.)
5. Add "Create Content Calendar from This" integration
6. Consider linking to actual campaign tracking

---

# Quick Summary

## Tools That Seem Good As-Is
- **Blog Article Creator** - Comprehensive, well-structured, good prompt
- **Campaign Builder** - Strong strategic framework, practical output

## Tools That Need Small Cleanup
- **Completed Order Post Creator** - Good but needs copy buttons, verify image analysis
- **Social Media Pack Generator** - Good concept, needs export and required fields
- **Content Calendar Creator** - Good concept, needs date picker and export

## Tools That May Need Bigger Changes
- **Social Media Job Post Creator** - Overlaps with Completed Order Post Creator, consider removing or differentiating

---

# Suggested Marketing Tool Structure

## Social Media Content
- Completed Order Post Creator (image-based)
- Social Media Pack Generator (batch ideas)
- Social Media Job Post Creator (consider merging into above)

## Content Planning
- Content Calendar Creator
- Campaign Builder

## Website & SEO
- Blog Article Creator

---

# Duplicate/Overlap Analysis

| Tool 1 | Tool 2 | Overlap | Recommendation |
|--------|--------|---------|----------------|
| Completed Order Post Creator | Social Media Job Post Creator | High | Merge or remove simpler one |
| Social Media Pack Generator | Content Calendar Creator | Partial | Consider integration |

---

# Issues Summary Table

| Tool | No Required Fields | No Copy Button | No Real Data | No Export | Duplicate Risk |
|------|-------------------|----------------|--------------|-----------|----------------|
| Blog Article Creator | Partial (1 required) | Yes | Yes | Yes | No |
| Completed Order Post Creator | Partial (2 required) | Yes | Partial | Yes | No |
| Social Media Job Post Creator | Yes | Yes | Yes | Yes | HIGH |
| Social Media Pack Generator | Yes | Yes | Yes | Yes | No |
| Content Calendar Creator | Yes | Yes | Yes | Yes | No |
| Campaign Builder | Yes | Yes | Yes | Yes | No |

---

# Priority Improvements

## Quick Wins (Low Effort)
1. Add required field validation to all tools
2. Add copy-to-clipboard buttons to all tools
3. Remove or differentiate Social Media Job Post Creator

## Medium Effort
4. Add export options (CSV, PDF) to calendar and pack generator
5. Verify image analysis works in Completed Order Post Creator
6. Add date picker to Content Calendar Creator

## Higher Effort
7. Integrate Social Pack Generator with Content Calendar
8. Add social media posting integration (Buffer/Later)
9. Pre-fill brand/company info from tenant settings

---

**End of Marketing Tools Simple Audit**
