# Vehicle Wrap AI Tool - Full Specifications
## Saved for Future Development

---

## 1. CORE ARCHITECTURE RULES (NON-NEGOTIABLE)

**This tool is NOT a generative image toy.**
It must be a vector-based layout engine with AI-assisted placement logic and production-aware export.

### Hard Requirements:

**Canvas must support:**
- True vector rendering
- Layer system
- Locked asset layers
- Grouping
- Precise scaling

**All sponsor logos:**
- Must remain original uploaded assets
- Never be recreated or redrawn by AI
- Never rasterized unless originally raster

**AI is allowed to:**
- Suggest layout
- Create background graphics
- Adjust hierarchy
- Recommend sizing
- Generate shape layers

**AI is NOT allowed to:**
- Rebuild logos
- Guess brand fonts
- Convert logos to text-to-image
- Replace vector artwork

---

## 2. FILE INPUT REQUIREMENTS

### Supported Upload Types:
- SVG
- AI
- EPS
- PDF (vector)
- High-res PNG
- High-res JPG

### Behavior Rules:

**If vector:**
→ Preserve vector format internally.

**If raster:**
→ Keep original resolution.
→ Do not attempt auto-vectorization unless user requests it.

**All uploaded logos become:**
→ Locked Smart Objects
→ Editable scale/position only

---

## 3. VEHICLE TEMPLATE SYSTEM

### System must include:
- Preloaded accurate vehicle templates
- True scale measurements
- Defined printable zones
- Door gap overlays
- Wheel well cutouts
- Window masked areas

### When user selects vehicle:
- Load scaled vector template
- Define total printable area
- Store actual dimensions in inches

**No fake perspective mockups. Use flat production profiles.**

---

## 4. AI LAYOUT ENGINE

### User Inputs:
- Industry
- Brand colors
- Wrap coverage level (Spot graphics / Partial / Full)
- Design style preference
- Uploaded logos
- Optional slogan
- Optional website

### AI Must Generate:
**3–5 Layout Concepts**
- Different hierarchy styles
- Different background directions
- Different logo emphasis

### Maintain:
- Minimum readable text size
- Proper contrast ratios
- Clean visual flow

### Apply design to:
- Driver side
- Passenger side
- Rear
- Hood (if selected)

### AI must respect:
- Safe zones
- Panel edges
- Handle cutouts

---

## 5. SPONSOR & MULTI-LOGO HANDLING

### When multiple logos uploaded:

**System must:**
- Allow sponsor tier assignment:
  - Primary
  - Secondary
  - Supporting

**AI must:**
- Scale primary largest
- Maintain equal spacing
- Avoid overlapping wheel wells
- Keep logos visually balanced

**NO logo distortion. NO stretching. NO color modification.**

---

## 6. PRINT PANELING ENGINE

### User Inputs:
- Printer max width (ex: 54", 60")
- Desired overlap (default 0.5–1")
- Bleed setting (default 0.5")

### System Must:
- Calculate total wrap width
- Divide evenly into panels
- Add:
  - Overlap margins
  - Bleed extension
- Label panels:
  - Panel 1A
  - Panel 1B
  - etc.

### Each panel must:
- Be exportable individually
- Maintain correct scale
- Include alignment marks

**This is geometry, not generative AI.**

---

## 7. RESOLUTION & COLOR CONTROL

### Background graphics must be generated at:
- True production scale OR
- Scalable vector format

### If raster:
- Minimum 150 DPI at full scale
- 300 DPI at half scale minimum

### Color Mode:
- CMYK export option
- ICC profile selection

**No upscaling low-res mockups for print.**

---

## 8. TEXT HANDLING

### System Text Fields:
- Must use selectable fonts
- Convert to outlines before export

### Uploaded Logos:
- Never convert to system font
- Never substitute fonts
- Never regenerate text

---

## 9. EXPORT OPTIONS

### Export Formats Required:
- PDF/X-1a
- High-res TIFF
- Layered PDF
- Individual paneled PDFs

### Export must include:
- Bleed
- Crop marks
- Panel labels
- Scale reference

### Optional:
- Production summary sheet
  - Total sq ft
  - Estimated vinyl usage
  - Estimated laminate usage

---

## 10. PRODUCTION INTELLIGENCE FEATURES

### Add optional AI tools:

**Material Usage Calculator**
- Auto-calc square footage
- Add waste factor %

**Install Complexity Estimator**
- Detect heavy curves
- Suggest labor hours

**Visibility Analyzer**
- Simulate viewing distance

**Contrast Warning System**
- Flag low readability areas

---

## 11. UI STRUCTURE

### Step-by-step workflow:
1. Select Vehicle
2. Upload Logos
3. Choose Coverage Level
4. Select Style
5. Generate Concepts
6. Adjust Layout
7. Confirm Print Settings
8. Export Production Files

**Do NOT overwhelm with too many controls at once.**

---

## 12. MVP VS ADVANCED

### If building in phases:

**MVP:**
- Logo placement AI
- Background generator
- Basic panel splitting
- PDF export

**Advanced:**
- 3D preview
- Traffic simulation
- Install heat map
- Fleet auto-variation

---

## 13. TECHNICAL IMPLEMENTATION NOTES

### Recommended Tech Stack:
- **Canvas Library:** Fabric.js (handles vector/raster, layers, locking, JSON save/load)
- **PDF Generation:** pdf-lib or jsPDF for client-side, reportlab/WeasyPrint for server-side
- **Vector Parsing:** svg-parser, pdf.js for handling uploads
- **Export:** Server-side CMYK conversion with ImageMagick or similar

### Key Principle:
**Separate generative design logic from production export logic.**
- AI assists in layout and background creation only
- Vector integrity preserved at all times
- Export engine operates independently from AI image generation

---

## Vehicle Templates Needed:
- Box Truck
- Sprinter Van
- Pickup Truck (F-150 style)
- Enclosed Trailer
- Semi Truck
- Sprint Car (dirt track)
- Late Model (dirt track)
- NASCAR style stock car

---

*Saved: February 2026*
*Status: Future Development - Build after current features are perfected*
