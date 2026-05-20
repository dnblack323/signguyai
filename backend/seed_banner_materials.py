"""
Seed starter Banner Materials for Phase 2A Step 2

Creates 4 starter banner materials if they don't already exist:
1. 13 oz Banner
2. 18 oz Banner  
3. Standard Mesh Banner
4. Standard Fabric Banner

All materials save to Materials Library with:
- category = banner_material
- shop cost per sq ft (editable)
- waste % (editable)
- suggested material charge per sq ft (optional)
- active = true
"""

import os
import sys
from pymongo import MongoClient

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'signguy')

STARTER_BANNER_MATERIALS = [
    {
        'key': '13oz_banner',
        'name': '13 oz Banner',
        'category': 'banner_material',
        'purchase_type': 'roll',
        'shop_cost_per_sqft': 0.45,
        'waste_percent': 10,
        'markup_percent': 40,
        'suggested_material_charge_per_sqft': 8.00,
        'manual_material_charge_per_sqft': 0,
        'is_active': True,
        'brand': '',
        'vendor': '',
        'compatible_categories': ['banners'],
        'notes': 'Standard 13 oz vinyl banner material. Suggested retail: $8/sq ft.',
    },
    {
        'key': '18oz_banner',
        'name': '18 oz Banner',
        'category': 'banner_material',
        'purchase_type': 'roll',
        'shop_cost_per_sqft': 0.75,
        'waste_percent': 10,
        'markup_percent': 35,
        'suggested_material_charge_per_sqft': 10.00,
        'manual_material_charge_per_sqft': 0,
        'is_active': True,
        'brand': '',
        'vendor': '',
        'compatible_categories': ['banners'],
        'notes': 'Heavy-duty 18 oz vinyl banner material. Suggested retail: $10/sq ft.',
    },
    {
        'key': 'mesh_banner',
        'name': 'Standard Mesh Banner',
        'category': 'banner_material',
        'purchase_type': 'roll',
        'shop_cost_per_sqft': 0.90,
        'waste_percent': 10,
        'markup_percent': 30,
        'suggested_material_charge_per_sqft': 11.00,
        'manual_material_charge_per_sqft': 0,
        'is_active': True,
        'brand': '',
        'vendor': '',
        'compatible_categories': ['banners'],
        'notes': 'Mesh banner material for windy conditions. Suggested retail: $11/sq ft.',
    },
    {
        'key': 'fabric_banner',
        'name': 'Standard Fabric Banner',
        'category': 'banner_material',
        'purchase_type': 'roll',
        'shop_cost_per_sqft': 1.20,
        'waste_percent': 10,
        'markup_percent': 25,
        'suggested_material_charge_per_sqft': 12.00,
        'manual_material_charge_per_sqft': 0,
        'is_active': True,
        'brand': '',
        'vendor': '',
        'compatible_categories': ['banners'],
        'notes': 'Fabric banner material for pole banners. Suggested retail: $12/sq ft.',
    },
]

def seed_banner_materials():
    """Seed starter banner materials if they don't exist"""
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get all tenants
    tenants = list(db.users.find({'role': {'$in': ['shop_owner', 'admin']}}, {'tenant_id': 1}))
    unique_tenant_ids = list(set(t.get('tenant_id') for t in tenants if t.get('tenant_id')))
    
    print(f"Found {len(unique_tenant_ids)} tenants")
    
    for tenant_id in unique_tenant_ids:
        print(f"\nProcessing tenant: {tenant_id}")
        
        # Get existing pricing defaults
        pricing_doc = db.pricing_defaults.find_one({'tenant_id': tenant_id})
        
        if not pricing_doc:
            print(f"  No pricing defaults found, skipping...")
            continue
        
        existing_materials = pricing_doc.get('materials', [])
        existing_keys = {m.get('key') for m in existing_materials if m.get('key')}
        
        materials_added = 0
        for material in STARTER_BANNER_MATERIALS:
            if material['key'] in existing_keys:
                print(f"  {material['name']} already exists, skipping...")
            else:
                # Add unique ID
                material['id'] = f"mat-{material['key']}"
                existing_materials.append(material)
                materials_added += 1
                print(f"  ✅ Added {material['name']}")
        
        if materials_added > 0:
            # Update pricing defaults with new materials
            db.pricing_defaults.update_one(
                {'tenant_id': tenant_id},
                {'$set': {'materials': existing_materials}}
            )
            print(f"  Saved {materials_added} new banner materials")
        else:
            print(f"  No new materials to add")
    
    client.close()
    print("\n✅ Banner material seeding complete")

if __name__ == '__main__':
    try:
        seed_banner_materials()
    except Exception as e:
        print(f"❌ Error seeding banner materials: {e}")
        sys.exit(1)
