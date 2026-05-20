#!/usr/bin/env python3
"""
Seed document templates into the database
Run this script to add the 4 vehicle wrap templates
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
from uuid import uuid4

# MongoDB connection
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "signguy")

async def seed_templates():
    """Add the 4 document templates to all tenants"""
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all tenants
    tenants = await db.tenants.find({}, {"_id": 0, "tenant_id": 1}).to_list(1000)
    print(f"Found {len(tenants)} tenant(s)")
    
    templates = [
        {
            "name": "Vehicle Wrap Aftercare Instructions",
            "description": "Complete care and maintenance guide for vehicle wraps with {{variables}} for auto-population",
            "category": "warranty",
            "content": """# Vehicle Wrap Care & Maintenance Guide

**Customer:** {{customer_name}}
**Company:** {{customer_company}}
**Installation Date:** {{today_date}}
**Order ID:** {{order_id}}

---

## Congratulations on Your New Vehicle Wrap!

Your vehicle wrap from {{company_name}} is a high-quality product designed to last for years with proper care.

---

## First 7 Days After Installation - CRITICAL PERIOD

⚠️ **DO NOT WASH your vehicle for at least 7 days** after installation.

- Avoid automatic car washes
- Avoid pressure washers  
- Park in shade when possible
- Do not apply wax or protectants

---

## Washing Your Wrapped Vehicle

### Hand Washing (Recommended)
1. Use cool/lukewarm water and pH neutral automotive soap
2. Soft sponge or microfiber cloth only
3. Rinse thoroughly
4. Dry with clean microfiber towel

### Touchless Car Washes
- ✅ Acceptable if pressure below 2000 PSI
- Keep nozzle 12+ inches away
- Angle at 90 degrees (not at seams)

### ❌ Automatic Brush Washes
- NOT RECOMMENDED - can lift edges

---

## What to AVOID

❌ Abrasive products, steel wool, harsh brushes
❌ Waxes & polishes  
❌ Petroleum-based cleaners
❌ Engine degreasers
❌ High pressure at seams
❌ Prolonged sun exposure - park in shade when possible

---

## Spot Cleaning

For bugs, bird droppings, sap, or tar:
1. Soak with warm soapy water for several minutes
2. Gently wipe with soft cloth
3. For stubborn spots: Use isopropyl alcohol
4. Rinse immediately
5. Never scrape or use abrasive tools

---

## Warranty Information

**Coverage:** Manufacturing defects, premature fading, adhesive failure
**Not Covered:** Improper care, accidents, vandalism, natural wear

**Warranty valid only if:**
- Proper aftercare guidelines followed
- No unauthorized modifications
- Regular professional cleaning

---

## Expected Lifespan

With proper care:
- **Cast vinyl:** 5-7 years
- **Calendared vinyl:** 3-5 years

---

## Contact Us

{{company_name}}
Phone: {{company_phone}}
Email: {{company_email}}
Website: {{company_website}}

**Emergency wrap repair:** Call immediately if you notice lifting, bubbling, or damage.

---

**Thank you for choosing {{company_name}}!**

Document created: {{today_date}}

Customer signature: _________________________
Date: _________________________
""",
            "tags": ["aftercare", "vehicle wrap", "warranty", "customer"]
        },
        {
            "name": "Decal & Sticker Aftercare Instructions", 
            "description": "Care guide for decals and vinyl graphics with {{variables}} for auto-population",
            "category": "warranty",
            "content": """# Decal & Vinyl Graphics Care Guide

**Customer:** {{customer_name}}
**Company:** {{customer_company}}  
**Installation Date:** {{today_date}}
**Order ID:** {{order_id}}

---

## First 48 Hours - CRITICAL PERIOD

⚠️ **DO NOT WASH OR WET** for at least 48 hours after installation.

- Allow adhesive to fully bond
- Avoid touching or pressing
- Keep out of rain if possible

---

## Cleaning Your Decals

### Hand Washing (Recommended)
1. **Wait 48 hours** after installation
2. Mild soap and warm water
3. Soft cloth or sponge only - no scrubbing
4. Rinse and pat dry

### Pressure Washing
- ✅ OK after 48 hours if careful
- Keep nozzle 12+ inches away
- Low pressure (under 1200 PSI)
- Spray at 90-degree angle
- ❌ Never spray at edges

---

## What to AVOID

❌ Abrasive materials
❌ Harsh chemicals (bleach, acetone)
❌ Automatic car wash brushes
❌ Waxing over decals
❌ Scraping or picking at edges

---

## Lifespan

**Indoor decals:** 5-7 years
**Outdoor decals:** 3-5 years
**Factors:** Sun, weather, surface, care

---

## Warranty

**Coverage:** Manufacturing defects, premature peeling, color fading
**Not Covered:** Improper application, accidents, harsh cleaning

**Contact:** {{company_name}} | {{company_phone}} | {{company_email}}

---

## Removal

**Do not attempt removal yourself.** Contact {{company_name}} for professional removal.

---

**Questions?**

{{company_name}}
{{company_phone}}
{{company_email}}

---

Document created: {{today_date}}

Customer signature: _________________________
Date: _________________________
""",
            "tags": ["aftercare", "decals", "warranty", "customer"]
        },
        {
            "name": "Vehicle Wrap Pre-Installation Checklist",
            "description": "Complete pre-prep checklist for vehicle wrap installations with {{variables}}",
            "category": "internal",
            "content": """# Pre-Installation Vehicle Preparation

**Customer:** {{customer_name}}
**Order ID:** {{order_id}}
**Vehicle:** _______________________
**Installation Date:** {{today_date}}
**Inspector:** _______________________

---

## Customer Requirements (Before Drop-Off)

### Vehicle Condition
- [ ] Fuel tank at least 1/4 full
- [ ] Clean exterior (washed)
- [ ] Interior cleaned, personal items removed
- [ ] All keys provided
- [ ] Alarm/immobilizer instructions provided

### Vehicle Disclosure
- [ ] Existing damage documented with photos
- [ ] Previous wraps/graphics disclosed
- [ ] Paint condition documented
- [ ] Body work history disclosed
- [ ] Aftermarket modifications noted

---

## Shop Inspection (Upon Arrival)

### Exterior Inspection
- [ ] Overall cleanliness acceptable
- [ ] No tar, sap, wax, or residue
- [ ] Paint not peeling or flaking
- [ ] Panel fitment normal
- [ ] Trim pieces secure
- [ ] Emblems/badges noted for removal
- [ ] Antenna noted
- [ ] Door handles functional
- [ ] Mirrors secure
- [ ] Lights/lenses intact

### Surface Preparation
- [ ] Clay bar treatment needed?
- [ ] Degreasing required?
- [ ] Alcohol wipe-down (always required)
- [ ] Any polishing needed?
- [ ] Rust treatment needed?

### Disassembly Required
- [ ] Door handles to remove
- [ ] Emblems/badges to remove
- [ ] Trim pieces to remove
- [ ] Mirrors to disassemble
- [ ] Bumpers to remove
- [ ] Lights to mask/remove
- [ ] Gas door to remove

---

## Documentation

### Photos Required (Minimum 12)
- [ ] Front view
- [ ] Rear view
- [ ] Driver side full
- [ ] Passenger side full
- [ ] Hood, Roof, Trunk
- [ ] Close-ups of existing damage (4+)

### Notes
**Existing damage:** _______________________
**Special considerations:** _______________________

---

## Material & Design Verification

- [ ] Vinyl material received and inspected
- [ ] Design files final version confirmed
- [ ] Print quality checked
- [ ] Lamination applied and cured
- [ ] Panel templates printed
- [ ] Special finishes confirmed

---

## Workspace Preparation

- [ ] Bay cleaned (dust-free)
- [ ] Temperature 65-85°F maintained
- [ ] Humidity controlled (below 60%)
- [ ] Adequate lighting
- [ ] Tools ready
- [ ] Vehicle lift available if needed

---

## Customer Communication

- [ ] Timeline confirmed
- [ ] Contact method confirmed
- [ ] Drop-off completed
- [ ] Pickup date/time set
- [ ] Deposit received

---

## Team Assignment

**Lead Installer:** _______________________
**Assistant(s):** _______________________
**Estimated Time:** _______ hours

---

## Pre-Wrap Cleaning Protocol

1. **Wash:** Automotive soap, hand wash, rinse, dry
2. **Prep:** Isopropyl alcohol wipe-down, clay bar if needed
3. **Final:** Surface dry, no dust/debris, ready for vinyl

---

## Sign-Off

**Prepared by:** _______________________
**Date:** {{today_date}}
**Approved by:** _______________________

**Ready for Installation:** ☐ Yes ☐ No

---

{{company_name}}
{{company_phone}} | {{company_email}}
""",
            "tags": ["pre-prep", "checklist", "internal", "vehicle wrap"]
        },
        {
            "name": "Post-Installation Quality Check & Delivery",
            "description": "Post-install inspection and customer delivery checklist with {{variables}}",
            "category": "internal", 
            "content": """# Post-Installation Quality Control & Delivery

**Customer:** {{customer_name}}
**Order ID:** {{order_id}}
**Vehicle:** _______________________
**Completed:** {{today_date}}
**Inspector:** _______________________

---

## Quality Control Inspection

### Overall Wrap Quality
- [ ] No bubbles or air pockets
- [ ] No wrinkles or creases
- [ ] Seams aligned properly
- [ ] Color matching consistent
- [ ] Design alignment correct
- [ ] No overstretch

### Panel-by-Panel Check

**Hood**
- [ ] Smooth, no bubbles
- [ ] Edges tucked properly
- [ ] Design centered
- Notes: _______________________

**Front Bumper**
- [ ] Curves handled properly
- [ ] No lifting
- [ ] Fog lights clean
- Notes: _______________________

**Doors (All)**
- [ ] Handle areas wrapped
- [ ] Window trim clean
- [ ] Panel gaps uniform
- Notes: _______________________

**Roof**
- [ ] Smooth finish
- [ ] Edges finished properly
- [ ] Antenna addressed
- Notes: _______________________

**Mirrors, Fenders, Trunk/Tailgate**
- [ ] All wrapped smoothly
- [ ] Edges sealed
- Notes: _______________________

---

## Edge Work & Finishing

- [ ] All edges sealed, no exposed adhesive
- [ ] Post-heating completed
- [ ] Excess vinyl trimmed cleanly
- [ ] Door jambs finished
- [ ] Gas door finished
- [ ] Panel gaps wrapped appropriately

---

## Reinstallation Check

- [ ] Door handles reinstalled and functional
- [ ] Emblems reinstalled
- [ ] Mirrors secure and functional
- [ ] Trim pieces reinstalled
- [ ] Lights/lenses clean
- [ ] Antenna reinstalled
- [ ] License plates remounted

---

## Functionality Tests

- [ ] All doors open/close smoothly
- [ ] Hood/trunk latches work
- [ ] Gas door opens easily
- [ ] Windows roll up/down
- [ ] Mirrors adjust fully
- [ ] Sensors functional
- [ ] Wipers operate (no contact)

---

## Final Cleaning

- [ ] Exterior washed
- [ ] Wrap surface wiped clean
- [ ] Glass cleaned
- [ ] Interior vacuumed
- [ ] No adhesive residue
- [ ] Wheel wells cleaned

---

## Documentation

### Photos (Minimum 15)
- [ ] Front/rear 3/4 views
- [ ] Full side views
- [ ] Hood, roof, trunk
- [ ] Close-ups of design elements (8+)
- [ ] Before/after comparison ready

---

## Warranty & Care Package

- [ ] Aftercare instructions printed
- [ ] Warranty card filled out
- [ ] Care kit provided
- [ ] Business cards included
- [ ] Touch-up kit (if applicable)

---

## Customer Delivery

### Vehicle Ready
- [ ] Keys ready
- [ ] Personal items returned
- [ ] Fuel level maintained
- [ ] Interior clean

### Walk-Through
- [ ] Show entire vehicle
- [ ] Explain care instructions
- [ ] Demonstrate cleaning
- [ ] Address concerns
- [ ] Review warranty
- [ ] Provide contact info
- [ ] Request review/photos

---

## Customer Acceptance

**Walk-Through Date:** {{today_date}}

- [ ] Customer inspected vehicle
- [ ] Customer satisfied
- [ ] Care instructions received
- [ ] Acceptance form signed

**Issues noted:** _______________________
**Resolution:** _______________________

---

## Financial

- [ ] Final payment received: $_______
- [ ] Invoice finalized
- [ ] Receipt provided

---

## Follow-Up

- [ ] One-week follow-up scheduled
- [ ] Review request sent
- [ ] Social media posted (with permission)

---

## Final Sign-Off

**Installation by:** _______________________
**QC by:** _______________________
**Customer:** _______________________
**Date:** {{today_date}}

**Vehicle Released:** ☐ Yes
**Customer Satisfied:** ☐ Yes ☐ No

---

{{company_name}}
{{company_phone}} | {{company_email}}
""",
            "tags": ["post-install", "checklist", "quality control", "internal"]
        }
    ]
    
    added_count = 0
    for tenant in tenants:
        tenant_id = tenant["tenant_id"]
        
        for template_data in templates:
            # Check if template already exists
            existing = await db.documents.find_one({
                "tenant_id": tenant_id,
                "name": template_data["name"],
                "is_template": True
            })
            
            if existing:
                print(f"  ⏭️  Template '{template_data['name']}' already exists for tenant {tenant_id}")
                continue
            
            # Create document template
            doc = {
                "id": str(uuid4()),
                "tenant_id": tenant_id,
                "name": template_data["name"],
                "description": template_data["description"],
                "category": template_data["category"],
                "file_type": "text/markdown",
                "file_size": len(template_data["content"].encode('utf-8')),
                "file_data": template_data["content"],  # Store content directly
                "original_filename": f"{template_data['name'].lower().replace(' ', '_')}.md",
                "is_template": True,
                "tags": template_data["tags"],
                "linked_jobs": [],
                "linked_customers": [],
                "uploaded_by": "system",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.documents.insert_one(doc)
            added_count += 1
            print(f"  ✅ Added '{template_data['name']}' for tenant {tenant_id}")
    
    print(f"\n✅ Successfully added {added_count} template(s) to database")
    client.close()

if __name__ == "__main__":
    print("="*60)
    print("Document Templates Seeder")
    print("="*60)
    asyncio.run(seed_templates())
    print("="*60)
