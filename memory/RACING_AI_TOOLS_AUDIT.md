# Racing AI Tool Audit Report

**Audit Date:** 2026-04-28
**Audited By:** AI Agent
**Scope:** Racing category tools only (4 tools)
**Status:** Investigation and documentation only - no code changes

---

# Tool Name: Race Number Designer

## 1. Tool Identification

- **User-facing tool name:** Race Number Designer
- **Internal function/component name:** `race_number_designer`
- **Backend route/API endpoint:** `POST /api/ai/generate-images`
- **Frontend file/component:** `/app/frontend/src/pages/AITools.js` (lines 409-425)
- **Backend file/function:** `/app/backend/routes/ai.py` (IMAGE_PROMPTS at line 840, TOOL_PROMPTS at line 623)
- **Standalone or category system:** Part of AI Tools page category system under "Racing & Motorsports"

## 2. Purpose of the Tool

- **What it does:** Generates professional racing number designs with custom fonts, colors, and visual effects
- **Racing-specific problem it solves:** Creates ready-to-use race number graphics that match specific racing series aesthetics
- **Who it is meant for:**
  - Owner/Admin: Yes - for creating number designs for race team clients
  - Designer: Yes - as a starting point for number design concepts
  - Salesperson: Possibly - for quick mockups during consultations
  - Race team/driver: Indirectly - as end recipients of the designs
- **Type of work:** Creates new design concepts (image generation)

## 3. Location in App

- **Access path:** AI Tools > Racing & Motorsports > Race Number Designer
- **Category placement:** Correct - appears under Racing category
- **Name/icon/description match:** Yes - accurately describes the tool's function
- **Clarity:** Clear and intuitive placement

## 4. Required Input Fields

| Field | Internal Name | Type | Frontend Required | Backend Required | Default | Placeholder | Validation |
|-------|---------------|------|-------------------|------------------|---------|-------------|------------|
| Race Number | `race_number` | text | Yes | Yes (in prompt) | None | "e.g., 24, 88, 3" | None |
| Number Style | `number_style` | select | Yes | Yes (in prompt) | None | N/A | Must select option |

**Required Field Issues:**
- No issues found - both required fields are properly validated

## 5. Optional Input Fields

| Field | Internal Name | Type | Purpose | Used by Backend | Should Remain Optional |
|-------|---------------|------|---------|-----------------|----------------------|
| Color Scheme | `color_scheme` | select | Pre-defined color combinations | Yes | Yes |
| Custom Colors | `custom_colors` | text | User-specified hex colors | Yes | Yes |
| Background | `background_type` | select | Background style for number | Yes | Yes |
| Special Effects | `effects` | select | Visual effects like shadows/glow | Yes | Yes |
| Racing Series Style | `racing_series` | select | Series-specific styling | Yes | Yes |

## 6. Racing-Specific Inputs

| Racing Element | Field Exists | Required/Optional | Sent to Backend | Affects Output | Recommendation |
|----------------|--------------|-------------------|-----------------|----------------|----------------|
| Race number | Yes | Required | Yes | Yes - primary element | Keep as-is |
| Racing series | Yes | Optional | Yes | Yes - affects style | Consider making required |
| Car class/division | No | N/A | N/A | N/A | Could add |
| Number panel location | No | N/A | N/A | N/A | Could add for size guidance |

## 7. Uploaded File / Image Inputs

- **Accepts uploads:** No
- **Recommendation:** Could benefit from:
  - Reference image upload for style matching
  - Existing number image for redesign

## 8. Hidden Context Used

| Context Source | Used | How Used |
|----------------|------|----------|
| Tenant/business profile | No | Not referenced |
| Shop settings | No | Not referenced |
| User role | Yes | Permission check |
| Credit balance | Yes | Pre-flight check |

## 9. Prompt / AI Instruction Logic

**Text Prompt (TOOL_PROMPTS):**
```
You are designing a professional racing number for motorsports.

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

Make it look fast, aggressive, and professional - perfect for race day!
```

**Image Prompt (IMAGE_PROMPTS):**
```
Professional racing number "{race_number}" design.
Style: {number_style}, {racing_series} series aesthetic.
Colors: {color_scheme}, {custom_colors}.
Background: {background_type}.
Effects: {effects}.
Bold, aggressive racing number suitable for motorsports.
Clean graphic design, high contrast, readable at speed.
Vector-style appearance, sharp edges, professional race graphics.
The number should look fast and powerful.
```

**Issues:**
- None significant - prompts are well-crafted for racing context

## 10. Output Type

- **Primary output:** AI-generated images (PNG, base64)
- **Image count:** 3 design options
- **Format:** Visual images displayed in grid
- **Editable:** No - display only
- **Creates business record:** No

## 11. Output Destination

- Displayed on AI Tools page in results grid
- Saved to `ai_history` collection in database
- Can be downloaded (right-click save)
- Persists after refresh (via history)

## 12. How Each Field Affects the Output

1. **race_number** - Required - Sent - Used in prompt - The actual number rendered
2. **number_style** - Required - Sent - Used in prompt - Determines font/visual style
3. **color_scheme** - Optional - Sent - Used in prompt - Pre-defined color combinations
4. **custom_colors** - Optional - Sent - Used in prompt - Overrides color_scheme if provided
5. **background_type** - Optional - Sent - Used in prompt - Determines background rendering
6. **effects** - Optional - Sent - Used in prompt - Adds visual effects
7. **racing_series** - Optional - Sent - Used in prompt - Applies series-specific styling

**No unused fields detected.**

## 13. Save / Edit / Approval Behavior

- **Edit output:** No
- **Approve output:** No formal approval workflow
- **Confirmation before save:** No - auto-saves to history
- **Copy output:** No copy button
- **Regenerate:** Yes - individual image regeneration supported
- **Compare versions:** No
- **Undo:** No

**Missing:** Copy to clipboard, formal approval workflow

## 14. Role and Permission Behavior

- **Current access:** All authenticated users with AI Tools access
- **Backend check:** Feature gate `ai_tools.image_generation`
- **Customer access:** No - requires authentication
- **Appropriate:** Yes for internal use

## 15. Credit / Cost Behavior

- **Cost:** 3 AI credits (1 per image)
- **Warning shown:** Yes - AICreditConfirmationDialog
- **Balance check:** Yes - pre-flight check
- **Usage logged:** Yes - to ai_history
- **Prevents duplicates:** Yes - button disabled while loading

## 16. Error Handling

- **On failure:** Toast error message shown
- **Input preserved:** Yes
- **Retry available:** Yes
- **Backend logging:** Yes - failed attempts logged
- **Error clarity:** Good - specific error messages

## 17. Tool Quality Review

- **Input quality:** Good - comprehensive racing-specific fields
- **Prompt quality:** Good - well-crafted for motorsports
- **Output usefulness:** Good - generates usable number designs
- **Category placement:** Good - correct category
- **Save/review behavior:** Needs Work - no formal save-to-project
- **Launch readiness:** Ready

## 18. Customer-Facing vs Internal Use

- **Current:** Internal only
- **Wording:** Professional/technical - appropriate for internal
- **Hidden private details:** No pricing exposed
- **Recommendation:** Keep internal - could add customer-facing simplified version

## 19. Real Business Record Behavior

- **Creates usable record:** No - generates images only
- **Saves to order/proof:** No
- **Recommendation:** Add "Save to Order" or "Create Design Brief" button

## 20. Generic Chat vs Real Racing Tool

- **Racing-specific:** Yes
- **Uses racing context:**
  - Race number: Yes
  - Racing series: Yes
  - Speed/visibility: Yes (in prompts)
  - Professional racing aesthetic: Yes
- **Verdict:** Real Racing Tool - well-specialized

## 21. Structured Output Recommendation

- Current: Images only (appropriate)
- Could add: JSON design specifications for production use

## 22. File/Image Support Recommendation

- **Should support:**
  - Reference image upload: Yes - for style matching
  - Previous number design: Yes - for redesign requests
- **Current support:** Insufficient - no uploads

## 23. Duplicate or Overlapping Tools

- **Overlaps with:** None significant
- **Recommendation:** Keep separate - specialized tool

## 24. Recommended Improvements

1. Add "Save to Order" functionality
2. Add reference image upload option
3. Make racing_series required for better results
4. Add number placement/size selector (door, roof, quarter)
5. Add export as vector (SVG) option
6. Add copy design brief to clipboard

---

# Tool Name: Driver Name Plate Generator

## 1. Tool Identification

- **User-facing tool name:** Driver Name Plate Generator
- **Internal function/component name:** `driver_name_plate`
- **Backend route/API endpoint:** `POST /api/ai/generate-images`
- **Frontend file/component:** `/app/frontend/src/pages/AITools.js` (lines 427-445)
- **Backend file/function:** `/app/backend/routes/ai.py` (IMAGE_PROMPTS at line 850, TOOL_PROMPTS at line 643)
- **Standalone or category system:** Part of AI Tools page category system under "Racing & Motorsports"

## 2. Purpose of the Tool

- **What it does:** Creates professional driver name plates and roof strips for race cars
- **Racing-specific problem it solves:** Generates standardized driver identification graphics for various placements on race vehicles
- **Who it is meant for:**
  - Owner/Admin: Yes - for creating name plates for clients
  - Designer: Yes - as design concepts
  - Race team/driver: Indirectly - as end users
- **Type of work:** Creates new design concepts (image generation)

## 3. Location in App

- **Access path:** AI Tools > Racing & Motorsports > Driver Name Plate Generator
- **Category placement:** Correct
- **Name/icon/description match:** Yes - accurately describes function
- **Clarity:** Clear placement

## 4. Required Input Fields

| Field | Internal Name | Type | Frontend Required | Backend Required | Default | Placeholder |
|-------|---------------|------|-------------------|------------------|---------|-------------|
| Driver Name | `driver_name` | text | Yes | Yes | None | "e.g., John Smith" |
| Plate Type | `plate_type` | select | Yes | Yes | None | N/A |

**Plate Type Options:**
- door_name_strip
- roof_strip
- windshield_banner
- quarter_panel_name
- hero_card_style

## 5. Optional Input Fields

| Field | Internal Name | Type | Purpose | Used by Backend |
|-------|---------------|------|---------|-----------------|
| Include Race Number? | `include_number` | select | Toggle number inclusion | Yes |
| Race Number | `race_number` | text | The number to include | Yes |
| Hometown | `hometown` | text | Driver's hometown | Yes |
| Sponsor Text | `sponsor_text` | text | Sponsor mention | Yes |
| Font Style | `font_style` | select | Typography style | Yes |
| Color Scheme | `color_scheme` | select | Color combination | Yes |
| Custom Team Colors | `custom_colors` | text | Custom hex colors | Yes |

## 6. Racing-Specific Inputs

| Racing Element | Field Exists | Required/Optional | Affects Output |
|----------------|--------------|-------------------|----------------|
| Driver name | Yes | Required | Yes - primary element |
| Race number | Yes | Optional | Yes - if included |
| Hometown | Yes | Optional | Yes - adds locality |
| Sponsor | Yes | Optional | Yes - adds sponsor line |
| Plate type | Yes | Required | Yes - determines layout |

**Missing racing elements:**
- Car number location (door vs roof style)
- Series-specific formatting rules

## 7. Uploaded File / Image Inputs

- **Accepts uploads:** No
- **Recommendation:** Could benefit from:
  - Team logo upload
  - Sponsor logo upload

## 8. Hidden Context Used

- Tenant/business profile: No
- User role: Yes (permission check)
- Credit balance: Yes (pre-flight)

## 9. Prompt / AI Instruction Logic

**Text Prompt (TOOL_PROMPTS):**
```
You are creating a professional driver name plate/strip for motorsports.

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

Keep it professional, readable, and race-ready!
```

**Image Prompt (IMAGE_PROMPTS):**
```
Professional motorsports driver name plate design.
Driver name: "{driver_name}"
Plate type: {plate_type}.
Number included: {include_number}, #{race_number}.
Hometown: {hometown}.
Sponsor: {sponsor_text}.
Font style: {font_style}.
Colors: {color_scheme}, {custom_colors}.
Clean racing typography, professional driver identification.
Readable name plate suitable for race car door or roof strip.
High contrast, bold text, racing aesthetic.
```

**Quality:** Good - comprehensive racing context

## 10. Output Type

- **Primary output:** AI-generated images (2 design options)
- **Format:** Visual images
- **Editable:** No
- **Creates record:** Saves to ai_history only

## 11. Output Destination

- Displayed on AI Tools page
- Saved to ai_history
- Persists after refresh

## 12. How Each Field Affects the Output

1. **driver_name** - Required - Primary text element
2. **plate_type** - Required - Determines layout (door strip vs roof vs windshield)
3. **include_number** - Optional - Controls number visibility
4. **race_number** - Optional - Number displayed if included
5. **hometown** - Optional - Secondary text element
6. **sponsor_text** - Optional - Adds sponsor line
7. **font_style** - Optional - Typography style
8. **color_scheme/custom_colors** - Optional - Color application

## 13. Save / Edit / Approval Behavior

- **Edit:** No
- **Approve:** No
- **Regenerate:** Yes
- **Copy:** No

## 14. Role and Permission Behavior

- **Access:** Authenticated users with AI Tools access
- **Appropriate:** Yes for internal

## 15. Credit / Cost Behavior

- **Cost:** 2 credits (2 images)
- **Warning:** Yes
- **Logged:** Yes

## 16. Error Handling

- **On failure:** Toast error
- **Input preserved:** Yes
- **Retry:** Yes

## 17. Tool Quality Review

- **Input quality:** Good
- **Prompt quality:** Good
- **Output usefulness:** Good
- **Category placement:** Good
- **Save/review:** Needs Work
- **Launch readiness:** Ready

## 18. Customer-Facing vs Internal Use

- **Current:** Internal
- **Recommendation:** Keep internal

## 19. Real Business Record Behavior

- **Creates record:** No - images only
- **Recommendation:** Add "Save to Order" option

## 20. Generic Chat vs Real Racing Tool

- **Racing-specific:** Yes
- **Uses:** driver name, race number, plate types, racing typography
- **Verdict:** Real Racing Tool

## 21. Structured Output Recommendation

- Current: Images appropriate
- Could add: Size specifications export

## 22. File/Image Support Recommendation

- **Should support:** Team logo, sponsor logo uploads
- **Current:** Insufficient

## 23. Duplicate or Overlapping Tools

- Minor overlap with Race Team Branding (hero card style)
- **Recommendation:** Keep separate - specialized function

## 24. Recommended Improvements

1. Add team/sponsor logo upload
2. Add specific dimension presets by series
3. Add "Save to Order" functionality
4. Add export with print specifications

---

# Tool Name: Vehicle Wrap Cost Calculator

## 1. Tool Identification

- **User-facing tool name:** Vehicle Wrap Cost Calculator
- **Internal function/component name:** `wrap_cost_calculator`
- **Backend route/API endpoint:** `POST /api/ai/generate` (text generation)
- **Frontend file/component:** `/app/frontend/src/pages/AITools.js` (lines 447-465)
- **Backend file/function:** `/app/backend/routes/ai.py` (TOOL_PROMPTS at line 665)
- **Standalone or category system:** Part of AI Tools page under "Racing & Motorsports"

## 2. Purpose of the Tool

- **What it does:** Calculates accurate pricing for vehicle wraps based on vehicle type, materials, complexity, and shop rates
- **Racing-specific problem it solves:** Provides pricing estimates for race car wraps specifically, with race vehicle types included
- **Who it is meant for:**
  - Owner/Admin: Yes - for quoting wrap jobs
  - Salesperson: Yes - for quick estimates
  - Manager: Yes - for pricing decisions
- **Type of work:** Calculates/generates pricing breakdown (text output)

## 3. Location in App

- **Access path:** AI Tools > Racing & Motorsports > Vehicle Wrap Cost Calculator
- **Category placement:** Questionable - this is a general business tool with racing vehicle options, not exclusively racing
- **Name/icon/description match:** Yes - accurate description
- **Clarity:** Could be confusing under Racing only - also useful for general wraps

## 4. Required Input Fields

| Field | Internal Name | Type | Frontend Required | Backend Required | Placeholder |
|-------|---------------|------|-------------------|------------------|-------------|
| Vehicle Type | `vehicle_type` | select | Yes | Yes | N/A |
| Wrap Coverage | `wrap_coverage` | select | Yes | Yes | N/A |
| Wrap Material Type | `wrap_type` | select | Yes | Yes | N/A |

**Vehicle Type Options (Racing-specific):**
- race_car_stock
- race_car_late_model
- race_car_modified
- sprint_car

**Vehicle Type Options (General):**
- sedan_compact, sedan_full
- suv_crossover, suv_full_size
- pickup_truck
- van_cargo, van_sprinter
- box_truck
- semi_truck_cab, semi_trailer
- motorcycle
- atv_utv
- boat
- trailer

## 5. Optional Input Fields

| Field | Internal Name | Type | Purpose | Used by Backend |
|-------|---------------|------|---------|-----------------|
| Design Complexity | `design_complexity` | select | Affects labor estimate | Yes |
| Design Services Needed? | `includes_design` | select | Adds design costs | Yes |
| Installation Difficulty | `installation_difficulty` | select | Affects labor hours | Yes |
| Old Wrap Removal? | `removal_needed` | select | Adds removal cost | Yes |
| Turnaround Time | `turnaround` | select | Rush fees | Yes |
| Your Shop Hourly Rate | `your_hourly_rate` | text | Shop-specific pricing | Yes |
| Material Markup % | `material_markup` | text | Profit margin | Yes |

## 6. Racing-Specific Inputs

| Racing Element | Field Exists | Notes |
|----------------|--------------|-------|
| Race car types | Yes | Includes: race_car_stock, race_car_late_model, race_car_modified, sprint_car |
| Sponsor layout complexity | Indirectly | Via design_complexity |
| Decal kit option | Yes | In wrap_coverage |

**Issue:** Tool is more general-purpose than racing-specific. Contains racing vehicle types but the pricing logic is universal.

## 7. Uploaded File / Image Inputs

- **Accepts uploads:** No
- **Recommendation:** Could add:
  - Reference image for complexity assessment
  - Design file for size calculation

## 8. Hidden Context Used

- Shop settings: No - uses manual input for hourly rate
- Pricing Foundation: No - could integrate
- **Issue:** Could pull default hourly rate from tenant settings

## 9. Prompt / AI Instruction Logic

**Text Prompt (TOOL_PROMPTS):**
```
You are a vehicle wrap pricing expert. Calculate accurate pricing for this wrap job.

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

Format as a professional quote the shop owner can reference or adapt.
```

**Quality:** Excellent - detailed pricing structure

## 10. Output Type

- **Primary output:** Formatted text pricing breakdown
- **Format:** Structured text with categories
- **Editable:** No
- **Creates record:** Saves to ai_history

## 11. Output Destination

- Displayed as text result
- Saved to ai_history
- Can be copied manually
- No direct export to quote/invoice

## 12. How Each Field Affects the Output

1. **vehicle_type** - Required - Determines square footage base
2. **wrap_coverage** - Required - Percentage of material/labor
3. **wrap_type** - Required - Material cost per sq ft
4. **design_complexity** - Optional - Design hours and complexity fee
5. **includes_design** - Optional - Adds design labor
6. **installation_difficulty** - Optional - Labor hour multiplier
7. **removal_needed** - Optional - Removal labor hours
8. **turnaround** - Optional - Rush fee percentage
9. **your_hourly_rate** - Optional - Base labor calculation
10. **material_markup** - Optional - Profit margin

## 13. Save / Edit / Approval Behavior

- **Edit:** No
- **Copy:** No dedicated button
- **Save to Quote:** No
- **Regenerate:** Yes

**Missing:** "Create Quote from This" functionality

## 14. Role and Permission Behavior

- **Access:** Authenticated users
- **Issue:** Exposes shop hourly rate in output - appropriate for internal only

## 15. Credit / Cost Behavior

- **Cost:** 1 credit (text generation)
- **Warning:** Yes
- **Logged:** Yes

## 16. Error Handling

- Standard toast errors
- Input preserved on failure

## 17. Tool Quality Review

- **Input quality:** Good - comprehensive options
- **Prompt quality:** Excellent - detailed pricing structure
- **Output usefulness:** Good - practical pricing reference
- **Category placement:** Needs Work - should also appear in Business category
- **Save/review:** Needs Work - no quote integration
- **Launch readiness:** Ready (with category note)

## 18. Customer-Facing vs Internal Use

- **Current:** Internal (shows shop hourly rate)
- **Recommendation:** Keep internal - pricing tool

## 19. Real Business Record Behavior

- **Creates record:** No - text output only
- **Saves to quote:** No
- **Recommendation:** Add "Create Quote" or "Copy to Quote" button

## 20. Generic Chat vs Real Racing Tool

- **Racing-specific:** Partially - includes race car types
- **Verdict:** Hybrid Tool - useful for racing and general wraps
- **Recommendation:** Consider dual placement or separate racing-specific version

## 21. Structured Output Recommendation

- Current: Formatted text
- Should be: Structured JSON for quote integration
- Fields: material_cost, labor_cost, total, line_items[]

## 22. File/Image Support Recommendation

- Could add: Vehicle photo for size estimation
- Current: Not needed for basic function

## 23. Duplicate or Overlapping Tools

- **Overlaps with:** Pricing Calculator (general)
- **Recommendation:** Merge into general pricing tool with vehicle wrap preset, OR create racing-specific variant

## 24. Recommended Improvements

1. **Critical:** Add "Create Quote" button to generate actual quote record
2. Move to Business category or dual-list
3. Pull default hourly rate from tenant settings
4. Output structured JSON for integration
5. Add vehicle photo upload for complexity assessment
6. Add racing-specific presets (race car package pricing)

---

# Tool Name: Race Team Branding Kit

## 1. Tool Identification

- **User-facing tool name:** Race Team Branding Kit
- **Internal function/component name:** `race_team_branding`
- **Backend route/API endpoint:** `POST /api/ai/generate-images`
- **Frontend file/component:** `/app/frontend/src/pages/AITools.js` (lines 467-483)
- **Backend file/function:** `/app/backend/routes/ai.py` (IMAGE_PROMPTS at line 862, TOOL_PROMPTS at line 714)
- **Standalone or category system:** Part of AI Tools page under "Racing & Motorsports"

## 2. Purpose of the Tool

- **What it does:** Generates complete branding packages for race teams including logos, numbers, and sponsor layouts
- **Racing-specific problem it solves:** Creates comprehensive team identity concepts for motorsports
- **Who it is meant for:**
  - Owner/Admin: Yes - for creating team branding packages
  - Designer: Yes - as comprehensive concept starting point
  - Race team/driver: Indirectly - as clients
- **Type of work:** Creates comprehensive design concepts (image generation with text brief)

## 3. Location in App

- **Access path:** AI Tools > Racing & Motorsports > Race Team Branding Kit
- **Category placement:** Correct
- **Name/icon/description match:** Yes
- **Clarity:** Clear - flagship racing tool

## 4. Required Input Fields

| Field | Internal Name | Type | Frontend Required | Backend Required | Placeholder |
|-------|---------------|------|-------------------|------------------|-------------|
| Team Name | `team_name` | text | Yes | Yes | "e.g., Thunder Racing, Smith Motorsports" |
| Racing Series | `racing_series` | select | Yes | Yes | N/A |

**Racing Series Options:**
- nascar_regional
- dirt_track_late_model
- dirt_track_modified
- sprint_car
- drag_racing
- road_racing
- rally
- motocross
- karting
- other

## 5. Optional Input Fields

| Field | Internal Name | Type | Purpose | Used by Backend |
|-------|---------------|------|---------|-----------------|
| Primary Car Number | `primary_number` | text | Team's race number | Yes |
| Team Colors | `team_colors` | text | Color palette | Yes |
| Style Preference | `style_preference` | select | Design direction | Yes |
| Include Elements | `include_elements` | select | What to generate | Yes |
| Sponsor Placeholder Locations | `sponsor_placeholders` | select | Sponsor zones | Yes |

**Style Preference Options:**
- aggressive_bold
- classic_traditional
- modern_clean
- retro_vintage
- tech_futuristic

**Include Elements Options:**
- logo_number_only
- logo_number_pattern
- full_wrap_concept
- hero_card_template

**Sponsor Placeholder Options:**
- none
- hood_only
- hood_and_quarters
- full_car_layout

## 6. Racing-Specific Inputs

| Racing Element | Field Exists | Required/Optional | Affects Output |
|----------------|--------------|-------------------|----------------|
| Team name | Yes | Required | Yes - brand identity |
| Racing series | Yes | Required | Yes - style context |
| Race number | Yes | Optional | Yes - number design |
| Team colors | Yes | Optional | Yes - palette |
| Sponsor zones | Yes | Optional | Yes - layout |

**Missing racing elements:**
- Driver name(s)
- Sponsor names (for placeholder text)
- Car make/model
- Existing branding to preserve

## 7. Uploaded File / Image Inputs

- **Accepts uploads:** No
- **Recommendation:** Should support:
  - Existing team logo
  - Sponsor logos
  - Current car photo
  - Inspiration/reference images

## 8. Hidden Context Used

- Tenant profile: No
- Credit balance: Yes

## 9. Prompt / AI Instruction Logic

**Text Prompt (TOOL_PROMPTS):**
```
You are a motorsports branding expert creating a race team brand kit.

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

Make it memorable, professional, and ready to stand out on race day!
```

**Image Prompt (IMAGE_PROMPTS):**
```
Professional race team branding design for "{team_name}".
Racing series: {racing_series}.
Team number: #{primary_number}.
Colors: {team_colors}.
Style: {style_preference}.
Elements: {include_elements}.
Sponsor areas: {sponsor_placeholders}.
Bold motorsports branding, aggressive racing aesthetic.
Professional race team identity, logo and number design.
Clean vector style, suitable for car graphics, merchandise, and marketing.
```

- Racing-specific: Yes - full motorsports context
- Quality: Excellent

## 10. Output Type

- **Primary output:** AI-generated images (3 design concepts)
- **Secondary:** Text branding brief (via TOOL_PROMPTS, but currently only images generated)
- **Format:** Images displayed in grid
- **Issue:** Text brief prompt exists but tool generates images only

## 11. Output Destination

- Displayed on AI Tools page
- Saved to ai_history
- Persists after refresh

## 12. How Each Field Affects the Output

1. **team_name** - Required - Core brand element
2. **racing_series** - Required - Style and format context
3. **primary_number** - Optional - Number design element
4. **team_colors** - Optional - Color palette
5. **style_preference** - Optional - Design direction
6. **include_elements** - Optional - What's generated (logo only vs full wrap)
7. **sponsor_placeholders** - Optional - Sponsor zone layout

## 13. Save / Edit / Approval Behavior

- **Edit:** No
- **Approve:** No
- **Regenerate:** Yes
- **Save to project:** No

**Missing:** "Create Design Brief" document, "Save to Customer/Order"

## 14. Role and Permission Behavior

- **Access:** Authenticated users with AI Tools
- **Appropriate:** Yes for internal

## 15. Credit / Cost Behavior

- **Cost:** 3 credits (3 images)
- **Warning:** Yes
- **Logged:** Yes

## 16. Error Handling

- Toast errors on failure
- Input preserved
- Retry available

## 17. Tool Quality Review

- **Input quality:** Good - comprehensive racing fields
- **Prompt quality:** Excellent - detailed branding framework
- **Output usefulness:** Good - generates usable concepts
- **Category placement:** Good
- **Save/review:** Needs Work - no document/project save
- **Launch readiness:** Ready

## 18. Customer-Facing vs Internal Use

- **Current:** Internal
- **Recommendation:** Keep internal - professional design tool

## 19. Real Business Record Behavior

- **Creates record:** No - images only
- **Saves to customer/order:** No
- **Recommendation:** Add "Create Branding Brief" document, "Save to Customer Project"

## 20. Generic Chat vs Real Racing Tool

- **Racing-specific:** Yes - fully specialized
- **Uses:**
  - Team name and identity
  - Racing series context
  - Number design
  - Sponsor placement zones
  - Car layout concepts
- **Verdict:** Real Racing Tool - flagship quality

## 21. Structured Output Recommendation

- Current: Images only
- Should add:
  - PDF branding guide export
  - JSON specifications export
  - Saved design brief document

## 22. File/Image Support Recommendation

- **Should support:**
  - Existing logo upload (for refresh/redesign)
  - Sponsor logos (for placement)
  - Current car photo (for reference)
  - Competitor examples
- **Current:** Insufficient - no uploads

## 23. Duplicate or Overlapping Tools

- **Partial overlap with:** Race Number Designer (number component)
- **Recommendation:** Keep separate - this is comprehensive, number tool is specialized

## 24. Recommended Improvements

1. **Critical:** Add file upload for existing logos/references
2. Add text branding brief generation (use existing TOOL_PROMPT)
3. Add "Create Design Brief Document" export
4. Add driver name field
5. Add sponsor name fields (for placeholder text)
6. Add "Save to Customer" functionality
7. Consider generating both images AND text brief together

---

# Missing Racing AI Tools

## Recommended Additions

### 1. Race Car Wrap Layout Planner
- **Purpose:** Generate wrap panel layouts with sponsor zone mapping
- **Required inputs:** Car type, body style, sponsor list with priority
- **Expected output:** Visual panel map + sponsor placement guide
- **Priority:** MVP

### 2. Sponsor Hierarchy Optimizer
- **Purpose:** Recommend sponsor placement based on value tiers
- **Required inputs:** Sponsor list with contract values, car type
- **Expected output:** Recommended placement map
- **Priority:** Future

### 3. Hero Card / Trading Card Generator
- **Purpose:** Generate driver hero cards/trading cards
- **Required inputs:** Driver info, stats, photo, sponsors
- **Expected output:** Hero card design images
- **Priority:** Beta (partially covered by Driver Name Plate hero_card_style)

---

# Recommended Racing Category Structure

## Current Tools (4)
1. Race Number Designer
2. Driver Name Plate Generator
3. Vehicle Wrap Cost Calculator
4. Race Team Branding Kit

## Recommended Groups

### Race Design Concepts
- Race Number Designer
- Driver Name Plate Generator
- Race Team Branding Kit

### Pricing & Business
- Vehicle Wrap Cost Calculator (consider dual-listing in Business category)

### Future Additions
- Race Car Wrap Layout Planner
- Sponsor Hierarchy Optimizer
- Hero Card Generator

---

# Must Fix Before Launch

| Priority | Issue | Tool | Recommendation |
|----------|-------|------|----------------|
| HIGH | Category placement | Vehicle Wrap Cost Calculator | Should be available in Business category too, not just Racing |
| FIXED | Error handling black screen | All image tools | Fixed 2026-04-28 - removed throw statements |

---

# Should Improve Soon

| Priority | Improvement | Tool(s) | Benefit |
|----------|-------------|---------|---------|
| MEDIUM | Add file upload support | Race Team Branding Kit | Allow existing logos/references |
| MEDIUM | Add "Save to Order/Customer" | All Racing tools | Create business records |
| MEDIUM | Add "Create Quote" button | Wrap Cost Calculator | Integration with quote system |
| MEDIUM | Add text branding brief | Race Team Branding Kit | Use existing TOOL_PROMPT |

---

# Future Enhancements

| Enhancement | Tool(s) | Notes |
|-------------|---------|-------|
| Add Race Car Wrap Layout Planner tool | New tool | Panel-by-panel sponsor mapping |
| Add sponsor logo upload | All racing tools | For real sponsor placement |
| Create customer-facing versions | Select tools | Simplified inputs for customers |
| Add PDF export | Race Team Branding Kit | Professional deliverable |
| Integrate with quote system | Wrap Cost Calculator | Output to actual quotes |
| Add series-specific presets | All tools | NASCAR, dirt track, drag racing packages |
| Add hero card specialized tool | New tool | Expand Driver Name Plate concept |

---

# Summary Statistics

| Metric | Count |
|--------|-------|
| Total Racing Tools | 4 |
| Image Generation Tools | 3 |
| Text Generation Tools | 1 |
| Tools Ready for Launch | 4 |
| Tools Needing Category Fix | 1 |
| Tools Missing File Upload | 4 |
| Tools Missing Save-to-Record | 4 |

---

**End of Racing AI Tool Audit Report**
