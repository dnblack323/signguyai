# Branding Tools Simple Audit

**Audit Date:** 2026-02-15
**Scope:** 3 Branding category tools only
**Purpose:** Review for future improvements - no code changes
**Source files reviewed:** `/app/frontend/src/pages/AITools.js`, `/app/backend/routes/ai.py`

---

# Tool Name: Idea Brainstormer

## 1. What does this tool do?
Brainstorms taglines/slogans, logo concepts, business names, campaign ideas, product names, or event themes for a brand. Pure text output – no images.

## 2. Where is it located?
- **Page:** AI Tools > Branding (card #1)
- **Frontend:** `/app/frontend/src/pages/AITools.js` (tool definition lines 87–101)
- **Backend prompt:** `TOOL_PROMPTS["idea_brainstormer"]` in `/app/backend/routes/ai.py` (lines ~130–166)
- **API:** `POST /api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| What Do You Need? | `brainstorm_type` | select | Yes | None |
| Business/Brand Name | `business_name` | text | No | None |
| Industry | `industry` | text | No | None |
| Target Audience | `target_audience` | textarea | No | None |
| Key Values/USP | `key_values` | textarea | No | None |
| Desired Tone | `tone` | select | No | None |
| Things to Avoid | `avoid` | text | No | None |

**brainstorm_type options:** taglines_slogans, logo_concepts, business_names, campaign_ideas, product_names, event_themes
**tone options:** professional_serious, friendly_approachable, fun_playful, luxurious_premium, bold_edgy, warm_caring, innovative_tech

## 4. How do the fields affect the AI output?
- `brainstorm_type` – **most important.** Controls which of the 6 output formats the model returns (taglines vs logo concepts vs names, etc.).
- `business_name` – inserted as the brand context.
- `industry` – frames the suggestions to the right vertical.
- `target_audience` – shapes language and emotional appeal.
- `key_values` – feeds into differentiation/USP-based ideas.
- `tone` – sets voice across all suggestions.
- `avoid` – excluded words/themes/styles.

## 5. What prompt or instructions does it send to AI?
A single prompt that asks the model to return a different output structure depending on `brainstorm_type`. For example:
```
You are a creative brainstorming expert for sign shops and their clients.
Request Type: {brainstorm_type}
Business/Brand: {business_name}
Industry: {industry}
Target Audience: {target_audience}
Key Values/USP: {key_values}
Desired Tone: {tone}
Things to Avoid: {avoid}

For Taglines/Slogans: 15 unique taglines (mix of pun, emotional, benefit, action) ...
For Logo Concepts: 8–10 concept ideas with icon/typography/color ...
For Business Names: 15 names + .com alternatives ...
For Campaign Ideas: 5 campaigns ...
For Product Names: 12 names ...
For Event Themes: 8 themes ...
```
**Concerns:**
- Prompt forces the model to "render the right section" based on `brainstorm_type`. The model usually does this, but there is no enforcement / structured output schema – occasional drift to other sections.
- "Sign shops and their clients" framing is fine for the app's domain.
- No "job"/"job ticket" wording – terminology OK.
- Missing fields the prompt references but the UI doesn't strongly highlight: `key_values` is interpolated as **Key Values/USP** but the UI label is just "Key Values/USP" – aligned.
- No competitor/differentiation field (would sharpen names + taglines).
- No language/locale field (everything assumed English).

## 6. What does it output?
- Plain text. The output type depends on `brainstorm_type`:
  - Taglines / Slogans (list)
  - Logo concept descriptions (list, no images)
  - Business name list (with .com hints)
  - Campaign idea descriptions
  - Product name list
  - Event theme list

## 7. Where does the output go?
- Displayed on screen
- "Copy to Clipboard" button
- "Save to Document Library" button (saves as a document record)
- "Generate PDF" button
- "Send to Customer Portal" dialog (with notify option)
- Saved to `ai_history` collection

## 8. Does it use real app/brand/business data?
Only the text typed into the form. No auto-pull from:
- Active business profile
- Brand assets / brand profile records
- Customer record (customer ID is never linked)
- Existing logos/colors
- Website/social URLs

The credit balance is checked through `AICreditGuard`, but no other app data is referenced.

## 9. Are there any obvious issues?
- **Output is unstructured.** All 6 brainstorm_type results return free-form text – there's no JSON / list structure that could be saved as discrete brand assets (e.g., a "tagline candidate" record).
- **Logo Concepts mode produces text descriptions only**, no actual logo images. Users will likely expect images here (see Logo Creator instead).
- **Business name mode hints at .com availability** but does not actually check domains – purely model speculation.
- **No competitor/differentiation field**, even though the underlying prompt would benefit from it (only Branding Kit Generator has competitors).
- **No "Save as Brand Idea / Tagline Candidate" structured save** – the only save path is "save as document" which loses the list semantics.
- **No customer / brand profile linkage** – a brainstorm session for "Customer X" is not connected to that customer.
- **No language selector** (English-only assumed).
- No upload field – cannot reference an existing logo/brand to align the suggestions.

## 10. What would you recommend changing?
- Add a `competitors` and `differentiation` field (mirror Branding Kit Generator).
- Output structured lists where appropriate (taglines as JSON array → save individually as candidates).
- Add an optional **Customer** picker so the brainstorm session is attached to that customer's brand profile.
- Add a "Save selected ideas to Brand Library" action (per-item save).
- Domain check: either remove the .com claim or actually integrate a domain availability API.

---

# Tool Name: Logo Creator

## 1. What does this tool do?
Generates 3 logo concept images for a business using GPT Image 1.

## 2. Where is it located?
- **Page:** AI Tools > Branding (card #2)
- **Frontend:** `/app/frontend/src/pages/AITools.js` (tool definition lines 238–254)
- **Backend prompt:** `IMAGE_PROMPTS["logo_creator"]` in `/app/backend/routes/ai.py` (lines ~807–815)
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Business Name | `business_name` | text | Yes | None |
| Tagline (Optional) | `tagline` | text | No | None |
| Industry | `industry` | select | No | None |
| Logo Style Preference | `logo_type` | select | No | None |
| Design Style | `style_preferences` | select | No | None |
| Color Preferences | `color_preferences` | text | No | None |
| Icon/Symbol Ideas (Optional) | `icon_ideas` | text | No | None |

**industry options:** construction_trades, restaurant_food, retail_shop, automotive, healthcare_medical, legal_financial, technology, real_estate, fitness_sports, beauty_salon, education, nonprofit
**logo_type options:** wordmark_text_only, lettermark_initials, icon_with_text, icon_symbol_only, emblem_badge_style
**style_preferences options:** minimalist_clean, vintage_classic, modern_bold, playful_fun, corporate_professional, artistic_creative, luxurious_elegant

## 4. How do the fields affect the AI output?
All seven fields are interpolated into the image-gen text prompt:
- `business_name` – the actual text rendered in the logo.
- `tagline` – told to "incorporate" but image-gen text rendering of long phrases is unreliable.
- `industry` – steers iconography.
- `logo_type` – tells the model which logo composition to use.
- `style_preferences` – aesthetic direction.
- `color_preferences` – plain text color brief.
- `icon_ideas` – seed visuals.

## 5. What prompt or instructions does it send to AI?
```
Professional logo design for "{business_name}".
Industry: {industry}.
Logo style: {logo_type}, {style_preferences} aesthetic.
Colors: {color_preferences}.
Tagline to incorporate: {tagline}.
Icon/symbol ideas: {icon_ideas}.
The logo should be clean, scalable, memorable, and work well on signage.
Professional brand identity design, vector-style appearance, white or transparent background.
High quality logo suitable for business cards, signs, and digital use.
```
**Concerns:**
- Generic image-gen scaffolding. No constraint that the result should be a single mark with **legible text**, single-color test, or be reproducible at small sizes – which are critical for signage.
- The prompt asks for "vector-style appearance" but GPT Image 1 returns a raster PNG; the result is not actually vector. Users may assume otherwise.
- No "primary / secondary / monochrome" variant generation (a real logo needs all three).
- No "job"/"job ticket" wording – terminology OK.

## 6. What does it output?
- 3 logo concept images (PNG, base64 data URLs)
- No accompanying brand brief or rationale
- No structured color/font recommendations attached

## 7. Where does the output go?
- Displayed as 3 thumbnails with download buttons
- Saved to `ai_history` collection
- "Select" button only flags the index in local state; **no persistence**
- **Cannot** save to a Brand Library, attach to a customer brand profile, save as a document, or export to PDF

## 8. Does it use real app/brand/business data?
Only the text typed into the form. The active business profile, customer record, or any existing brand assets are not pre-filled or linked. No upload of an existing logo to evolve from.

## 9. Are there any obvious issues?
- **Output is orphaned.** Generated logos die in `ai_history` – no "Save as Brand Asset / attach to Customer" flow.
- **No upload of existing logo** for evolution / refresh (Logo Refresher in Design covers that, partially).
- **Claims vector** but returns raster only.
- **Single composition variant.** No primary/secondary/monochrome version generated for signage use.
- **Color field is plain text**, not a structured color picker / brand-profile link.
- **No "include tagline?" toggle** – tagline is always inserted, often poorly rendered by image-gen.
- **No customer picker** – generated logos have no place to live beyond history.
- **No paired text brief** – branding decisions (why this logo / how to use it) aren't generated.

## 10. What would you recommend changing?
- Add a "Save as Brand Asset → Customer / Brand Profile" action.
- Pair image generation with a short text brief (rationale + suggested colors/fonts/usage).
- Generate primary + monochrome + reverse-on-dark variants of the chosen concept.
- Replace the free-text color field with a structured color picker.
- Optional logo upload for evolution (image-to-image when supported).
- Set expectations: explain raster vs vector, add a "Send to vectorization tool" CTA.

---

# Tool Name: Branding Kit Generator

## 1. What does this tool do?
Generates a complete written brand system: mission, color palette (with hex), typography pairing, voice/tone, visual guidelines, and application examples.

## 2. Where is it located?
- **Page:** AI Tools > Branding (card #3)
- **Frontend:** `/app/frontend/src/pages/AITools.js` (tool definition lines 256–268)
- **Backend prompt:** `TOOL_PROMPTS["branding_kit_generator"]` in `/app/backend/routes/ai.py` (lines ~465–502)
- **API:** `POST /api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Describe Your Logo | `logo_description` | textarea | No | None |
| Brand Personality | `brand_tone` | select | No | None |
| Target Audience | `target_audience` | textarea | No | None |
| Competitors (Optional) | `competitors` | text | No | None |

**brand_tone options:** professional_trustworthy, friendly_approachable, luxurious_premium, playful_energetic, innovative_modern, traditional_established

## 4. How do the fields affect the AI output?
- `logo_description` – feeds the visual baseline that color/typography recommendations are built around.
- `brand_tone` – sets personality across the kit (mission, voice, visual choices).
- `target_audience` – shapes voice/tone and messaging samples.
- `competitors` – informs differentiation suggestions (USP framing).

## 5. What prompt or instructions does it send to AI?
```
You are a brand strategist for sign shops. Create a complete brand system with guidelines:

Logo Description: {logo_description}
Brand Personality: {brand_tone}
Target Audience: {target_audience}
Competitors: {competitors}

1. Brand Overview (mission, personality, USP)
2. Color Palette (primary + secondary with hex codes + usage)
3. Typography (primary headline + secondary body + pairing rules)
4. Voice & Tone (style + words to use/avoid + sample messaging)
5. Visual Guidelines (logo usage rules, spacing, sign applications)
6. Application Examples (business card, sign design principles, social media)
```
**Concerns:**
- Strong, well-structured prompt – clearly the most "brand-strategist-like" of the three.
- **No `business_name` or `industry` field collected** – the prompt has all the structure but lacks core identity inputs. The model has to infer these from `logo_description`, which is unreliable.
- **No required field at all** – user can submit an essentially empty form and still get a generic kit.
- **No upload of an existing logo image** – the kit is built from a text description of the logo only, so colors/typography recommendations can't be matched against a real mark.
- **No website/social URL input** for tone-mining.
- No "job"/"job ticket" wording – terminology OK.

## 6. What does it output?
- A long-form text brand kit (mission, color palette with hex, typography, voice/tone, visual rules, application examples).
- Output is plain Markdown-ish text – not structured JSON. Hex codes are inline strings, fonts are inline names; nothing machine-readable.

## 7. Where does the output go?
- Displayed on screen
- "Copy to Clipboard" button
- "Save to Document Library" button
- "Generate PDF" button
- "Send to Customer Portal" dialog
- Saved in `ai_history` collection

## 8. Does it use real app/brand/business data?
Only typed input. No business profile, customer brand profile, uploaded logo, or website URL is auto-pulled. No structured brand-asset record is created from the output.

## 9. Are there any obvious issues?
- **Missing `business_name` field** – the most important brand identifier is not asked for.
- **Missing `industry` field** – brand strategy advice should be industry-anchored.
- **No required fields** – form can be submitted blank.
- **No logo upload** – kit is built from a description; can't sample existing colors/typography.
- **Output is unstructured** – hex codes and font names live inside prose. They can't be saved as actual brand-asset records (no Color records, no Typography records, no Voice rules record).
- **No customer linkage** – a kit generated for "Customer X" is not tied to that customer's brand profile.
- **No iteration / regenerate-section action** – user must regenerate the entire kit to refine just the color palette or just the voice.
- **No website / social bio output** despite being a common deliverable in a brand kit.

## 10. What would you recommend changing?
- Add `business_name` (required) and `industry` (required) fields.
- Add optional logo upload + brand color preferences (structured picker).
- Output structured JSON alongside prose so colors/fonts/voice rules can be saved as discrete brand-asset records.
- Add a customer picker → "Save as this customer's Brand Kit" linked to a brand profile entity.
- Per-section regenerate buttons (regenerate just the color palette, just the voice, etc.).
- Optional fields: website URL, existing tagline, social handles (for tone-mining).

---

# Quick Summary

## Tools that seem good as-is
- *(none qualify outright – all 3 have meaningful gaps)*

## Tools that need small cleanup
- **Idea Brainstormer** – prompt and structure are reasonable; mostly needs a competitor/differentiation field, structured output for taglines/names, and the ability to attach the brainstorm session to a customer.

## Tools that may need bigger changes
- **Logo Creator** – output is orphaned (no save-as-brand-asset / attach-to-customer flow); claims "vector" but returns raster; no monochrome / reverse variants; no paired written brief.
- **Branding Kit Generator** – missing `business_name` and `industry` fields, no required inputs, no logo upload, output is prose only (hex codes/fonts not structured), no customer/brand-profile linkage, no per-section regenerate.

---

# Suggested Branding Tool Structure

A clean grouping for the 3 current Branding tools, plus where they'd ideally sit:

1. **Brand Strategy**
   - Branding Kit Generator (mission, voice, color palette, typography, application rules)

2. **Logo & Visual Identity**
   - Logo Creator (concept images)
   - *(Logo Refresher already lives in Design – arguably belongs here too)*

3. **Brand Voice & Messaging**
   - Idea Brainstormer (taglines, names, campaign ideas)

4. **Customer Brand Profiles** *(does not exist yet – recommended)*
   - Persistent per-customer brand record that captures saved logos, color palette, typography, voice rules, and tagline candidates from all of the above tools. Today, every output dies in `ai_history` with no link to a brand profile.

---

# Memory Document Request

This file **is** the memory document:
- Path: `/app/memory/BRANDING_TOOLS_AUDIT.md`
- Title: **Branding Tools Audit Results**
- Use: Reference when deciding which Branding tool fields, prompts, outputs, or workflows to change.

Companion audit documents (already in `/app/memory/`):
- `RACING_AI_TOOLS_AUDIT.md`
- `BUSINESS_TOOLS_AUDIT.md`
- `MARKETING_TOOLS_AUDIT.md`
- `DESIGN_TOOLS_AUDIT.md`

With this file, the per-category audit set on the AI Tools page is now **complete** (Racing, Business, Marketing, Design, Branding).

---

## Cross-Cutting Findings (apply to most/all Branding tools)

1. **Output orphaning.** All 3 tools save only to `ai_history`. None of them write into a structured customer Brand Profile or Brand Library. Generated logos, color palettes, taglines, and brand kits cannot be reused programmatically anywhere else in the app.
2. **No customer linkage.** None of the 3 tools take a Customer ID, so a brand artifact generated for "Customer X" lives nowhere in that customer's record.
3. **No structured output.** Hex codes, font names, and tagline lists are buried inside prose. They aren't machine-readable, so downstream features (e.g., auto-fill colors on AI Sign Designer, auto-fill tagline on banners) can't consume them.
4. **Missing core branding inputs in some tools.** Branding Kit Generator does not collect business name or industry. Idea Brainstormer does not collect competitors/differentiation. Logo Creator does not allow uploading an existing mark.
5. **Vector vs raster confusion.** Logo Creator and Logo Refresher both imply vector output; both actually return raster. A "Send to Vectorization Analyzer" handoff would resolve user expectations.
6. **Terminology:** Branding prompts do **not** use "job" or "job ticket" – already aligned with order-friendly language.
7. **There is also a `tagline_generator` prompt in `TOOL_PROMPTS` (line ~301) that is not exposed by any frontend tool** – it is dead code today. It could be wired to the Idea Brainstormer's `taglines_slogans` mode for a tighter, dedicated prompt, or removed.
