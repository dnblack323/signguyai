# Design Tools Simple Audit

**Audit Date:** 2026-02-15
**Scope:** 10 Design category tools only
**Purpose:** Review for future improvements - no code changes
**Source files reviewed:** `/app/frontend/src/pages/AITools.js`, `/app/backend/routes/ai.py`

---

# Tool Name: Logo Refresher

## 1. What does this tool do?
Lets the user upload an existing logo and asks GPT Image 1 to generate 3 "refreshed" / modernized versions in a chosen style direction.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #1)
- **Frontend:** `/app/frontend/src/pages/AITools.js` (tool definition lines 41–55)
- **Backend prompt:** `IMAGE_PROMPTS["logo_refresher"]` in `/app/backend/routes/ai.py` (lines ~768–775)
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Upload Your Current Logo | `image_upload` | image_upload | Yes | None |
| Business Name | `business_name` | text | Yes | None |
| Style Direction | `style_direction` | select | No | None |
| Elements to Keep | `keep_elements` | textarea | No | None |
| Elements to Change | `change_elements` | textarea | No | None |

**Style Direction options:** modernize_minimal, make_bold_impactful, add_elegance, make_playful, vintage_retro, tech_futuristic, hand_drawn_organic

## 4. How do the fields affect the AI output?
- `business_name` – inserted as the brand name in the prompt.
- `style_direction` – tells the model which aesthetic direction to push.
- `keep_elements` – text description of which marks/shapes to preserve.
- `change_elements` – text description of what should change.
- `image_upload` – Captured in the form, but **not actually sent to the image generator** (see Issues §9).

## 5. What prompt or instructions does it send to AI?
Image-only prompt (text → GPT Image 1):
```
Redesigned modern logo for "{business_name}".
Style direction: {style_direction}.
Elements to preserve: {keep_elements}.
Changes to make: {change_elements}.
Clean, professional, scalable, vector-style, white/transparent background, single logo centered.
```
**Concerns:** generic image-gen wording, no real reference to the uploaded logo, no constraint for sign-shop output (CMYK, vector readiness, single-color test, max colors). Doesn't use the words "job"/"job ticket" – terminology OK.

## 6. What does it output?
- 3 generated logo concept images (PNG, base64 data URLs)
- No design rationale / production notes accompany the images

## 7. Where does the output go?
- Displayed on screen as 3 thumbnails with download buttons
- Saved to `ai_history` collection (`tenant_id`, `user_id`, `tool`, `images`, `credits_used`)
- Cannot be saved to Documents Library, attached to a customer/order, or exported as PDF
- Single "Select" action only flags the index in local state; it doesn't persist anywhere
- Disappears from the visible UI after the user navigates away

## 8. Does it use real app/design/business data?
Only the text the user types. No business profile, customer, order, brand colors, or stored logo is auto-populated. The uploaded reference image is captured client-side but ignored by the image generator.

## 9. Are there any obvious issues?
- **Reference logo is ignored.** `image_upload` is not extracted in `generate_images()` – GPT Image 1 only sees text. The word "redesigned" is misleading because there is no input image.
- **No brand color field** even though logos are color-driven.
- **No vector / single-color readiness note** in output (critical for sign work).
- **No "Save as Brand Asset" / attach to customer-brand profile.**
- **No print-readiness summary** to accompany the image.
- Selected concept can't be reused anywhere (no save-to-library).

## 10. What would you recommend changing?
- Pass the uploaded logo as a vision reference (image-to-image) so the refresh actually starts from the user's logo.
- Add `brand_colors` field.
- Generate an accompanying short design brief (text) explaining what changed and how it scales for signage.
- Add "Save to Brand Library / Customer Brand Profile" action.

---

# Tool Name: Generative Fill / Image Expander

## 1. What does this tool do?
Takes an uploaded image and asks AI to generate 2 expanded / outpainted versions in the chosen direction.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #2)
- **Frontend:** `AITools.js` (lines 57–69)
- **Backend prompt:** `IMAGE_PROMPTS["generative_fill"]` (lines ~777–783)
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Upload Image to Expand | `image_upload` | image_upload | Yes | None |
| Expansion Direction | `expand_direction` | select | No | None |
| Describe What to Generate | `content_description` | textarea | No | None |
| Style Matching | `style_match` | select | No | None |

**Direction options:** expand_all_sides, expand_left, expand_right, expand_top, expand_bottom, expand_horizontal, expand_vertical
**Style match options:** match_exactly, enhance_quality, artistic_interpretation

## 4. How do the fields affect the AI output?
All four fields are interpolated into a generic image-gen text prompt. The actual outpaint operation is **not performed** because GPT Image 1 can't see the source image here.

## 5. What prompt or instructions does it send to AI?
```
Expanded image with seamless continuation.
Expansion direction: {expand_direction}.
Content to generate: {content_description}.
Style matching: {style_match}.
... seamlessly blend with the original image ...
```
**Concerns:** Tells the model to "blend with original" but no original is supplied. Effectively becomes a generic text-to-image generator. No "job"/"job ticket" wording – OK.

## 6. What does it output?
- 2 generated images (will not actually be expansions of the uploaded image)
- No notes / explanation

## 7. Where does the output go?
- Shown on screen, downloadable, saved to `ai_history` only
- Cannot be linked to a proof, design file, or order

## 8. Does it use real app/design/business data?
Only typed user input. The uploaded image is captured client-side but ignored server-side.

## 9. Are there any obvious issues?
- **Tool does not actually do generative fill / outpainting.** No image-conditioned model is wired up; result is a fresh image from text.
- Misleading name and field labels for users.
- No DPI/print-target field (critical for sign jobs).
- No save-to-design-library or attach-to-order option.
- No dimensions field – expansions for print need pixel/inch targets.

## 10. What would you recommend changing?
- Either implement true outpainting (model that accepts source image + mask) or rename/repurpose the tool (e.g., "Background Variation Generator").
- Add target dimensions and DPI.
- Allow saving expanded image to a design/proof library.

---

# Tool Name: Text to Image Creator

## 1. What does this tool do?
Generates 3 brand-new images from a text description, with style/aspect/color controls.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #3)
- **Frontend:** `AITools.js` (lines 72–84)
- **Backend prompt:** `IMAGE_PROMPTS["text_to_image"]` (lines ~785–790)
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Describe the Image You Want | `image_prompt` | textarea | Yes | None |
| Image Style | `image_style` | select | No | None |
| Aspect Ratio | `aspect_ratio` | select | No | None |
| Color/Mood | `color_mood` | select | No | None |

**Style options:** photorealistic, illustration, digital_art, sketch, watercolor, minimalist, 3d_render, vintage_photo
**Aspect options:** square_1x1, landscape_16x9, portrait_9x16, wide_banner_3x1, standard_4x3
**Color options:** vibrant_colorful, muted_soft, dark_moody, bright_airy, warm_tones, cool_tones, black_and_white, neon_glow

## 4. How do the fields affect the AI output?
- `image_prompt` – the main subject and scene description.
- `image_style` – visual style.
- `aspect_ratio` – described in text only; **not enforced** at API level (GPT Image 1 returns 1024x1024 by default).
- `color_mood` – appended to the prompt to bias palette.

## 5. What prompt or instructions does it send to AI?
```
{image_prompt}
Style: {image_style}.
Aspect ratio: {aspect_ratio}.
Color mood: {color_mood}.
High quality, professional image suitable for signage and marketing materials.
```
**Concerns:** Aspect ratio is told to the model in text only, not enforced by the API – output may not match. Otherwise prompt is reasonable. No "job"/"job ticket" wording.

## 6. What does it output?
- 3 generated images, no rationale.

## 7. Where does the output go?
- On-screen + download + saved in `ai_history`
- No save-to-design-library, no attach-to-order

## 8. Does it use real app/design/business data?
Only typed input.

## 9. Are there any obvious issues?
- Aspect ratio choice is cosmetic – output dimensions don't actually change.
- No DPI or print-size target.
- Cannot reuse the image elsewhere in the app (no design library).
- "Wide banner 3x1" implies print but there's no print-readiness output.
- No NSFW/brand-safety guardrails noted.

## 10. What would you recommend changing?
- Enforce aspect ratio at the API call (use a model that supports `size`).
- Add "intended use" field (web vs print) and surface print-readiness notes.
- Add Save-to-design-library + attach-to-customer/order.

---

# Tool Name: Photo Enhancer Analyzer

## 1. What does this tool do?
Uploads a photo and returns a written **assessment** (not an enhanced image) covering print readiness, fixes needed, and color profile concerns.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #4)
- **Frontend:** `AITools.js` (lines 132–143)
- **Backend prompt:** `TOOL_PROMPTS["photo_enhancer"]` (lines ~243–252)
- **API:** `POST /api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Upload Image to Analyze | `image_upload` | image_upload | Yes | None |
| Enhancement Goals | `enhancement_notes` | textarea | No | None |
| Intended Use | `output_type` | select | No | None |

**Intended Use options:** print_large_format, print_standard, web_digital, social_media

## 4. How do the fields affect the AI output?
- `image_upload` – sent to GPT-5.2 vision as a `FileContent` attachment, so the model actually sees the image.
- `output_type` – passed into the prompt to tailor scaling/print advice.
- `enhancement_notes` – injected into the prompt verbatim.

## 5. What prompt or instructions does it send to AI?
```
You are an expert photo analyst for a sign shop. Analyze the uploaded image and provide:
1. Print Readiness Assessment ...
2. Enhancement Recommendations ...
3. Color Profile Analysis (CMYK, signage) ...
4. Scaling Recommendations for {output_type}
5. Technical Fixes Needed
Enhancement goals: {enhancement_notes}
```
**Concerns:** Prompt is solid and sign-shop specific. No "job"/"job ticket" wording. Could ask the model for an explicit "approved for production / not approved" verdict.

## 6. What does it output?
- Plain text assessment / proof note style.

## 7. Where does the output go?
- On-screen
- Copy-to-clipboard button
- "Save to Document Library" button (saves as document)
- "Generate PDF" button
- "Send to Customer Portal" button
- Saved in `ai_history`

## 8. Does it use real app/design/business data?
The uploaded photo is genuinely analyzed. No customer/order/material data is pulled in automatically.

## 9. Are there any obvious issues?
- No way to attach the assessment directly to an existing order/proof.
- No structured "approved/needs work" output – the output is pure prose.
- No DPI estimate field – user must describe scale in free text.
- No file-type/size validation in the UI before upload.

## 10. What would you recommend changing?
- Add a structured verdict (Approved / Needs Fixing / Not Usable) at the top of the output.
- Add "Attach to Order/Proof" action so the analysis becomes a proof note.
- Add target output dimensions (W × H × DPI) field.

---

# Tool Name: Vectorization Analyzer

## 1. What does this tool do?
Analyzes an uploaded raster image and returns vectorization complexity, recommended approach, color reduction, and time estimate.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #5)
- **Frontend:** `AITools.js` (lines 145–155)
- **Backend prompt:** `TOOL_PROMPTS["image_vectorizer"]` (lines ~254–262)
- **API:** `POST /api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Upload Image to Analyze | `image_upload` | image_upload | Yes | None |
| Target Color Count | `num_colors` | select | No | None |
| Source Image Type | `image_type` | select | No | None |

**Color count options:** 2_colors, 3_colors, 4_colors, 6_colors, 8_colors, full_color
**Source type options:** crisp_line_art, logo_clean_edges, photo_simple, photo_complex, hand_drawn, blurry_edges

## 4. How do the fields affect the AI output?
- `image_upload` – sent as vision input to GPT-5.2.
- `num_colors` – tells the model the spot-color reduction target.
- `image_type` – sets the model's expectation about the source.

## 5. What prompt or instructions does it send to AI?
```
You are a vectorization expert for a sign shop. Analyze this image and provide:
1. Vectorization Complexity Score 1–10
2. Recommended Approach (for {image_type})
3. Color Analysis & reduction to {num_colors}
4. Problem Areas
5. Production Tips
6. Estimated Time
```
**Concerns:** Solid sign-shop framing. No "job"/"job ticket" wording. Doesn't ask the model to specify cut-vs-print recommendation.

## 6. What does it output?
- Plain text production guidance / shop-floor advice.

## 7. Where does the output go?
- On-screen, copy, save-to-library, PDF, send-to-portal
- `ai_history`

## 8. Does it use real app/design/business data?
Real image analyzed. No materials/cutter capability data is auto-pulled.

## 9. Are there any obvious issues?
- No "intended end use" field (cut vinyl vs printed vinyl vs embroidery vs CNC) – production guidance would be sharper if known.
- No "attach to order" option – this is a pre-production note that should live on the order.
- No structured color-list output (would be valuable as a swatch list for the production team).

## 10. What would you recommend changing?
- Add `intended_production_method` field (cut vinyl / print + cut / sublimation / CNC / embroidery).
- Output a structured color list (with HEX/CMYK guesses).
- "Attach to Order" button.

---

# Tool Name: Font Identifier

## 1. What does this tool do?
Looks at an image containing text and tries to identify the font and suggest similar alternatives.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #6)
- **Frontend:** `AITools.js` (lines 158–167)
- **Backend prompt:** `TOOL_PROMPTS["font_identifier"]` (lines ~264–275)
- **API:** `POST /api/ai/generate`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Upload Image with Text | `image_upload` | image_upload | Yes | None |
| Text Visible in Image | `text_sample` | text | No | None |

## 4. How do the fields affect the AI output?
- `image_upload` – analyzed by GPT-5.2 vision.
- `text_sample` – improves accuracy when the model can't read the rendering reliably.

## 5. What prompt or instructions does it send to AI?
```
You are a typography expert for a sign shop. Analyze the text in this image:
Text visible: {text_sample}
1. Primary Font Identification (family + weight)
2. Similar Alternatives (3–5, include free)
3. Font Characteristics
4. Sign Shop Recommendations (cut/print well)
5. Licensing Notes
```
**Concerns:** Sign-shop specific, includes licensing reminder – good. No "job"/"job ticket" wording.

## 6. What does it output?
- Plain text with the font guess + alternatives + licensing note.

## 7. Where does the output go?
- On-screen, copy, save-to-library, PDF, send-to-portal
- `ai_history`

## 8. Does it use real app/design/business data?
Real image analyzed. No internal font library is referenced.

## 9. Are there any obvious issues?
- No internal "shop font library" lookup – recommendations may suggest fonts the shop doesn't own.
- LLM-only font identification is unreliable; should ideally use a dedicated WhatTheFont-style API.
- No way to save the matched font as a customer brand-asset.
- No "show the closest font we already own" option.

## 10. What would you recommend changing?
- Add an internal `installed_fonts` list and constrain alternatives to those.
- Save matched font into the customer's brand profile.
- Optionally integrate a real font ID API for accuracy.

---

# Tool Name: AI Sign Designer

## 1. What does this tool do?
Generates 3 visual concept images of a finished sign for a business.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #7)
- **Frontend:** `AITools.js` (lines 170–186)
- **Backend prompt:** `IMAGE_PROMPTS["ai_sign_designer"]` (lines ~792–797). Note: a `TOOL_PROMPTS["ai_sign_designer"]` text prompt also exists at lines ~277–287 but is **never executed** because the tool is registered as `generatesImages: true`.
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Business Name (text on sign) | `business_name` | text | Yes | None |
| Business Type | `business_type` | text | No | None |
| Sign Type | `sign_type` | select | No | None |
| Approximate Size | `size` | text | No | None |
| Brand Colors | `colors` | text | No | None |
| Additional Text | `additional_text` | textarea | No | None |
| Style | `style_preference` | select | No | None |

**Sign Type options:** channel_letters, monument_sign, pylon_sign, wall_sign, lightbox_cabinet, dimensional_letters, awning, blade_sign
**Style options:** modern_clean, classic_traditional, bold_impactful, elegant_upscale, playful_fun, industrial_rugged, rustic_vintage

## 4. How do the fields affect the AI output?
All field values are interpolated into the image prompt; `size` is included as text only and does not control output dimensions.

## 5. What prompt or instructions does it send to AI?
```
Professional photograph of a {sign_type} sign for "{business_name}" business.
Style: {style_preference}, clean professional signage photography.
Colors: {colors}.
Realistic, professionally installed, appropriate for a {business_type}.
Additional elements: {additional_text}.
High quality, daylight lighting.
```
**Concerns:** Prompt is generic for image-gen. No structured design brief. The richer text-style brief in `TOOL_PROMPTS["ai_sign_designer"]` is dead code. No "job"/"job ticket" wording.

## 6. What does it output?
- 3 generated sign concept images, no accompanying brief.

## 7. Where does the output go?
- On-screen, download, "Select" (UI-only flag)
- Saved in `ai_history`
- Cannot be saved as a proof, attached to a customer or order, or exported as PDF
- Cannot regenerate variations of one specific concept (regenerate replaces in-place)

## 8. Does it use real app/design/business data?
Only typed input. Nothing is pre-filled from the active business profile, customer brand colors, materials catalog, or pricing foundation.

## 9. Are there any obvious issues?
- Dead `TOOL_PROMPTS["ai_sign_designer"]` text prompt – should either run alongside the image (to give a written brief) or be removed.
- No mounting/installation context (height, viewing distance, illumination, day/night).
- No "save as proof / attach to order" flow.
- No materials / substrate suggestion.
- Brand colors field is plain text, not a real color picker / hex input.
- "Approximate Size" doesn't change the image's actual proportions.

## 10. What would you recommend changing?
- Run the dead text prompt alongside the image gen to produce a paired design brief.
- Add fields for illumination, viewing distance, day/night.
- Replace `colors` text field with a structured color picker pulling from customer brand profile.
- Add "Save as Proof" linked to a customer / order.

---

# Tool Name: AI Banner Designer

## 1. What does this tool do?
Generates 3 banner concept images for promotions, events, or announcements.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #8)
- **Frontend:** `AITools.js` (lines 188–203)
- **Backend prompt:** `IMAGE_PROMPTS["ai_banner_designer"]` (lines ~799–805). A `TOOL_PROMPTS["ai_banner_designer"]` text version also exists at ~289–298 but is **never executed**.
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Main Headline | `headline` | text | Yes | None |
| Supporting Text | `subtext` | textarea | No | None |
| Banner Size | `banner_size` | select | No | None |
| Purpose | `event_type` | select | No | None |
| Colors to Use | `brand_colors` | text | No | None |
| Design Style | `style` | select | No | None |

**Banner Size options:** 2x4ft, 3x6ft, 4x8ft, 3x10ft, 4x12ft, retractable_33x80
**Purpose options:** grand_opening, sale_promotion, event_announcement, sports_team, birthday_celebration, business_promotion, now_hiring, real_estate, political
**Style options:** bold_modern, elegant_classy, fun_colorful, professional_corporate, vintage_retro, minimalist_clean

## 4. How do the fields affect the AI output?
All values are interpolated into the prompt. `banner_size` is included as text only, doesn't change output proportions.

## 5. What prompt or instructions does it send to AI?
```
Professional promotional banner design, {banner_size} format.
Main headline: "{headline}"
Supporting text area for: {subtext}
Style: {style}, {event_type} theme.
Colors: {brand_colors}.
Clean, readable typography, professional print-ready design.
```
**Concerns:** Says "print-ready" but doesn't enforce DPI or actual banner aspect. Dead `TOOL_PROMPTS["ai_banner_designer"]` text prompt. No "job"/"job ticket" wording.

## 6. What does it output?
- 3 banner concept images, no copy notes or layout brief.

## 7. Where does the output go?
- On-screen, download, "Select" (UI-only)
- `ai_history`
- No proof / order linkage

## 8. Does it use real app/design/business data?
Only typed input. No pre-fill from active business profile or customer record.

## 9. Are there any obvious issues?
- Banner size is cosmetic in the prompt only – aspect ratio is not enforced.
- No "place customer's logo on the banner" support (cannot upload a logo).
- Dead text prompt sitting unused.
- No grommet/finishing notes (a real-world production must-have).
- No "Save as proof / attach to order" flow.

## 10. What would you recommend changing?
- Use a model call that respects aspect ratio (e.g., 4:8 for 4x8ft) or pre-define mappings.
- Add optional logo upload + brand color picker.
- Run the text prompt alongside to produce print-spec & finishing notes.
- "Save as proof" + attach to an event/order.

---

# Tool Name: Mockup Creator

## 1. What does this tool do?
Generates 2 realistic mockup photos showing a described sign/wrap inside a chosen environment.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #9)
- **Frontend:** `AITools.js` (lines 205–216)
- **Backend prompt:** `IMAGE_PROMPTS["mockup_creator"]` (lines ~817–821)
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Describe the Design to Show | `design_description` | textarea | Yes | None |
| Product Type | `product_type` | select | No | None |
| Environment Setting | `environment` | select | No | None |

**Product Type options:** storefront_sign, vehicle_wrap_car, vehicle_wrap_truck, vehicle_wrap_van, window_graphics, monument_sign, wall_sign_interior, banner_outdoor, yard_sign, trade_show_booth
**Environment options:** urban_street_day, suburban_plaza, parking_lot, highway_view, indoor_office, indoor_retail, night_illuminated

## 4. How do the fields affect the AI output?
All three are merged into the image prompt. The design is described in text only – the model imagines it.

## 5. What prompt or instructions does it send to AI?
```
Realistic mockup photograph showing {product_type} in a {environment} setting.
The design shows: {design_description}.
Professional product photography, realistic lighting, natural environment integration.
... like an actual installed sign or vehicle wrap ...
```
**Concerns:** Cannot upload an actual artwork file to insert into the mockup, so it remains a "what if" image. No "job"/"job ticket" wording.

## 6. What does it output?
- 2 mockup images.

## 7. Where does the output go?
- On-screen, download, `ai_history`
- No save-as-proof, no link to customer/order

## 8. Does it use real app/design/business data?
None. Pure text input.

## 9. Are there any obvious issues?
- **No artwork upload** – defeats the main use of a mockup tool (showing the customer's actual design).
- No customer/order picker – mockups are normally tied to a specific opportunity.
- Cannot save the mockup to a proof or send it via the customer portal.
- Limited environment list compared to typical mockup needs (e.g., trade show floor, highway billboard, restaurant interior at night).

## 10. What would you recommend changing?
- Add an artwork upload that the model uses as a reference (image-to-image).
- Add "Save as proof / attach to order / send via portal".
- Expand environments and add lighting controls (golden hour, overcast, night-illuminated, store-closed).

---

# Tool Name: Vehicle Wrap Mockup Generator

## 1. What does this tool do?
Generates 2 mockup photos showing a described vehicle wrap on a chosen vehicle type / view angle.

## 2. Where is it located?
- **Page:** AI Tools > Design (card #10)
- **Frontend:** `AITools.js` (lines 219–235)
- **Backend prompt:** `IMAGE_PROMPTS["vehicle_wrap_mockup"]` (lines ~823–837)
- **API:** `POST /api/ai/generate-images`

## 3. What input fields does it ask for?

| Field Label | Internal Name | Type | Required | Default |
|---|---|---|---|---|
| Describe Your Wrap Design | `design_description` | textarea | Yes | None |
| Business Name on Wrap | `business_name` | text | Yes | None |
| Vehicle Type | `vehicle_type` | select | Yes | None |
| Wrap Coverage | `wrap_coverage` | select | No | None |
| Primary Colors | `primary_colors` | text | No | None |
| Design Style | `style` | select | No | None |
| View Angle | `view_angle` | select | No | None |

**Vehicle options:** sedan_car, suv_crossover, pickup_truck, box_truck, cargo_van, sprinter_van, semi_truck, trailer, bus, sports_car
**Coverage options:** full_wrap, partial_wrap_sides, partial_wrap_rear, spot_graphics_logo_only, half_wrap_lower
**Style options:** clean_corporate, bold_aggressive, elegant_luxury, fun_playful, industrial_rugged, tech_modern, classic_traditional
**View options:** three_quarter_front, side_view, three_quarter_rear, front_view

## 4. How do the fields affect the AI output?
All inputs are interpolated into the image prompt. Design is described in text only.

## 5. What prompt or instructions does it send to AI?
```
Realistic vehicle wrap mockup photograph.
Vehicle: {vehicle_type}, coverage: {wrap_coverage}, business "{business_name}".
Design: {design_description}, colors {primary_colors}, style {style}, view {view_angle}.
Photorealistic, professional installation, realistic reflections following body lines.
```
**Concerns:** Most thorough of the design prompts. Still text-only – cannot place a real artwork file. No "job"/"job ticket" wording.

## 6. What does it output?
- 2 vehicle wrap mockup images.

## 7. Where does the output go?
- On-screen, download, `ai_history`
- Cannot be saved as a proof or attached to a wrap-quote/order

## 8. Does it use real app/design/business data?
None auto-pulled. Pure typed input.

## 9. Are there any obvious issues?
- No upload of the actual wrap design file.
- No customer-pricing tie-in (vehicle type maps directly to the Vehicle Wrap Calculator – missed opportunity).
- No "save as proof / attach to wrap order" action.
- No square-foot / coverage-area info passed alongside (would dovetail with pricing tool).
- Only 4 view angles – top-down / drone view missing.

## 10. What would you recommend changing?
- Add artwork upload (image-to-image) so the customer's real wrap is shown.
- Add "Send to Vehicle Wrap Calculator" / "Save as proof on order" actions.
- Pass vehicle dimensions through so coverage-area pricing follows along.
- Optional per-side previews (driver / passenger / rear / hood).

---

# Quick Summary

## Tools that seem good as-is
- **Photo Enhancer Analyzer** – strong vision-enabled prompt, clear sign-shop framing, save/PDF/portal flows already exist.
- **Vectorization Analyzer** – solid prompt, sign-shop specific, save flows present.
- **Font Identifier** – simple, well-scoped, save flows present (only weakness is LLM accuracy for font ID).

## Tools that need small cleanup
- **Text to Image Creator** – enforce aspect ratio, add intended-use field, add save-to-library.
- **AI Sign Designer** – kill or activate the dead text prompt; add lighting/viewing-distance fields; add save-as-proof.
- **AI Banner Designer** – kill or activate the dead text prompt; honor banner aspect ratio; add finishing/grommet info; add save-as-proof.

## Tools that may need bigger changes
- **Logo Refresher** – currently doesn't actually use the uploaded logo (image_upload ignored in image-gen path); needs true image-to-image.
- **Generative Fill / Image Expander** – name implies outpainting; in reality it's text-to-image. Either implement true outpainting or rename and refocus.
- **Mockup Creator** – needs real artwork upload to be useful; no order/proof flow.
- **Vehicle Wrap Mockup Generator** – same: needs artwork upload + tie-in to wrap calculator + save-as-proof.

---

# Suggested Design Tool Structure

A useful regrouping for the 10 design tools:

1. **Design Intake (Asset Analysis)**
   - Photo Enhancer Analyzer
   - Vectorization Analyzer
   - Font Identifier

2. **Concept Generation (Layout & Ideas)**
   - AI Sign Designer
   - AI Banner Designer
   - Text to Image Creator

3. **Brand Asset Tools**
   - Logo Refresher (after fixing image-to-image)

4. **Mockups & Visualization**
   - Mockup Creator
   - Vehicle Wrap Mockup Generator
   - Generative Fill / Image Expander (rename → "Background / Scene Variation")

(Categories the tools currently lack but would benefit from later: **Proofing & Revisions**, **Production Notes**, **Customer Communication**.)

---

# Memory Document Request

This file **is** the memory document:
- Path: `/app/memory/DESIGN_TOOLS_AUDIT.md`
- Title: **Design Tools Audit Results**
- Use: Reference when deciding which Design tool fields, prompts, outputs, or workflows to change.

Companion audit documents (already in `/app/memory/`):
- `RACING_AI_TOOLS_AUDIT.md`
- `BUSINESS_TOOLS_AUDIT.md`
- `MARKETING_TOOLS_AUDIT.md`

Remaining category to audit on user request: **Branding** (4 tools).

---

## Cross-Cutting Findings (apply to most Design tools)

1. **Output orphaning:** image-generating design tools save to `ai_history` only. They cannot be turned into a proof, attached to a customer/order, or exported as PDF. The non-image analyzers already have the full Save/PDF/Portal flow.
2. **Image-input fields ignored:** for `logo_refresher` and `generative_fill`, the uploaded image is never sent to the image generator. Users will assume it's used.
3. **Dead text prompts:** `ai_sign_designer` and `ai_banner_designer` have full TOOL_PROMPTS that never run because their tools are flagged `generatesImages: true`. Either run them in parallel for a written brief or delete them.
4. **No business-context auto-fill:** none of the design tools pre-populate business name, brand colors, customer, or product/material data. Everything is typed by hand.
5. **Aspect ratio / size fields are text-only:** they appear in the prompt but don't actually change output dimensions.
6. **Terminology:** Design prompts do **not** use the words "job" or "job ticket" – they're already aligned with "order"-friendly language.
