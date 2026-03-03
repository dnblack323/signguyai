"""
Sample Data Service

Creates demo data for new trial accounts to help users understand
how the platform works. Called during registration.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional


async def create_sample_data_for_tenant(db, tenant_id: str, owner_name: str) -> dict:
    """
    Create sample data for a new trial account:
    - 3 sample customers
    - 2 sample jobs (different stages)
    - 1 sample invoice
    - 1 sample webstore (draft mode)
    - 2 sample products
    
    Returns summary of created data.
    """
    now = datetime.now(timezone.utc)
    created_items = {
        "customers": [],
        "jobs": [],
        "invoices": [],
        "webstores": [],
        "products": [],
    }
    
    # ==========================================================================
    # SAMPLE CUSTOMERS
    # ==========================================================================
    
    sample_customers = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "ABC Manufacturing Co.",
            "email": "demo-contact@abcmanufacturing.example",
            "phone": "(555) 123-4567",
            "company": "ABC Manufacturing Co.",
            "address": "123 Industrial Blvd, Suite 100",
            "city": "Springfield",
            "state": "IL",
            "zip": "62701",
            "notes": "[SAMPLE DATA] This is a demo B2B customer for exploring the platform.",
            "is_sample_data": True,
            "portal_enabled": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Sarah Johnson",
            "email": "demo-sarah@example.com",
            "phone": "(555) 234-5678",
            "company": "",
            "address": "456 Oak Street",
            "city": "Riverside",
            "state": "CA",
            "zip": "92501",
            "notes": "[SAMPLE DATA] Demo retail customer - ordered vehicle decals.",
            "is_sample_data": True,
            "portal_enabled": False,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Riverside Youth Soccer League",
            "email": "demo-fundraiser@rysoccer.example",
            "phone": "(555) 345-6789",
            "company": "Riverside Youth Soccer League",
            "address": "789 Sports Complex Dr",
            "city": "Riverside",
            "state": "CA",
            "zip": "92502",
            "notes": "[SAMPLE DATA] Demo fundraiser organization - great candidate for a fundraiser webstore!",
            "is_sample_data": True,
            "portal_enabled": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
    ]
    
    for customer in sample_customers:
        await db.customers.insert_one(customer)
        created_items["customers"].append(customer["name"])
    
    customer_abc_id = sample_customers[0]["id"]
    customer_sarah_id = sample_customers[1]["id"]
    
    # ==========================================================================
    # SAMPLE PRODUCTS (for webstore)
    # ==========================================================================
    
    sample_products = [
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Custom Vinyl Banner",
            "description": "High-quality 13oz vinyl banner with hemmed edges and grommets. Perfect for outdoor advertising.",
            "category": "signs",
            "base_cost": 15.00,
            "retail_price": 45.00,
            "is_active": True,
            "is_sample_data": True,
            "images": [],
            "variants": [
                {"id": str(uuid.uuid4()), "name": "3x6 ft", "price_modifier": 0, "is_available": True},
                {"id": str(uuid.uuid4()), "name": "4x8 ft", "price_modifier": 25, "is_available": True},
            ],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "name": "Team Spirit T-Shirt",
            "description": "Soft cotton t-shirt with custom team logo. Great for sports teams and fundraisers.",
            "category": "apparel",
            "base_cost": 8.00,
            "retail_price": 25.00,
            "is_active": True,
            "is_sample_data": True,
            "images": [],
            "variants": [
                {"id": str(uuid.uuid4()), "name": "S", "price_modifier": 0, "is_available": True},
                {"id": str(uuid.uuid4()), "name": "M", "price_modifier": 0, "is_available": True},
                {"id": str(uuid.uuid4()), "name": "L", "price_modifier": 0, "is_available": True},
                {"id": str(uuid.uuid4()), "name": "XL", "price_modifier": 2, "is_available": True},
            ],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        },
    ]
    
    for product in sample_products:
        await db.products.insert_one(product)
        created_items["products"].append(product["name"])
    
    # ==========================================================================
    # SAMPLE JOBS
    # ==========================================================================
    
    # Job 1: In production (approved stage)
    job1_id = str(uuid.uuid4())
    sample_jobs = [
        {
            "id": job1_id,
            "tenant_id": tenant_id,
            "customer_id": customer_abc_id,
            "customer_name": "ABC Manufacturing Co.",
            "title": "Lobby Signage Package",
            "description": "[SAMPLE] Dimensional letters and directional signs for main lobby renovation.",
            "status": "in_progress",
            "priority": "high",
            "due_date": (now + timedelta(days=7)).isoformat(),
            "total_amount": 2450.00,
            "is_sample_data": True,
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Dimensional Letters - Company Name",
                    "description": "Brushed aluminum letters, 8\" tall",
                    "quantity": 1,
                    "unit_price": 1800.00,
                    "total": 1800.00,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Directional Signs (set of 3)",
                    "description": "Acrylic with aluminum standoffs",
                    "quantity": 3,
                    "unit_price": 150.00,
                    "total": 450.00,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Installation",
                    "description": "Professional installation included",
                    "quantity": 1,
                    "unit_price": 200.00,
                    "total": 200.00,
                },
            ],
            "activities": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "status_change",
                    "description": "Job created",
                    "timestamp": (now - timedelta(days=5)).isoformat(),
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "status_change",
                    "description": "Quote approved by customer",
                    "timestamp": (now - timedelta(days=3)).isoformat(),
                },
                {
                    "id": str(uuid.uuid4()),
                    "type": "status_change",
                    "description": "Production started",
                    "timestamp": (now - timedelta(days=1)).isoformat(),
                },
            ],
            "created_at": (now - timedelta(days=5)).isoformat(),
            "updated_at": now.isoformat(),
        },
        # Job 2: Quote stage
        {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "customer_id": customer_sarah_id,
            "customer_name": "Sarah Johnson",
            "title": "Vehicle Decals",
            "description": "[SAMPLE] Custom vinyl decals for personal vehicle - racing stripes and sponsor logos.",
            "status": "quote",
            "priority": "medium",
            "due_date": (now + timedelta(days=14)).isoformat(),
            "total_amount": 375.00,
            "is_sample_data": True,
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Racing Stripe Kit",
                    "description": "Premium vinyl racing stripes",
                    "quantity": 1,
                    "unit_price": 250.00,
                    "total": 250.00,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Custom Logo Decals (pair)",
                    "description": "12\" sponsor logos",
                    "quantity": 2,
                    "unit_price": 45.00,
                    "total": 90.00,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Number Decal",
                    "description": "18\" race number",
                    "quantity": 1,
                    "unit_price": 35.00,
                    "total": 35.00,
                },
            ],
            "activities": [
                {
                    "id": str(uuid.uuid4()),
                    "type": "status_change",
                    "description": "Quote created",
                    "timestamp": (now - timedelta(days=2)).isoformat(),
                },
            ],
            "created_at": (now - timedelta(days=2)).isoformat(),
            "updated_at": now.isoformat(),
        },
    ]
    
    for job in sample_jobs:
        await db.jobs.insert_one(job)
        created_items["jobs"].append(job["title"])
    
    # ==========================================================================
    # SAMPLE INVOICE
    # ==========================================================================
    
    sample_invoice = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "invoice_number": "INV-DEMO-001",
        "customer_id": customer_abc_id,
        "customer_name": "ABC Manufacturing Co.",
        "customer_email": "demo-contact@abcmanufacturing.example",
        "job_id": job1_id,
        "status": "sent",
        "due_date": (now + timedelta(days=30)).isoformat(),
        "subtotal": 2450.00,
        "tax_rate": 0,
        "tax_amount": 0,
        "total": 2450.00,
        "amount_paid": 0,
        "balance_due": 2450.00,
        "notes": "[SAMPLE INVOICE] This is a demo invoice to show how invoicing works.",
        "is_sample_data": True,
        "items": [
            {
                "id": str(uuid.uuid4()),
                "description": "Lobby Signage Package - 50% Deposit",
                "quantity": 1,
                "unit_price": 1225.00,
                "total": 1225.00,
            },
        ],
        "created_at": (now - timedelta(days=1)).isoformat(),
        "updated_at": now.isoformat(),
    }
    
    await db.invoices.insert_one(sample_invoice)
    created_items["invoices"].append(sample_invoice["invoice_number"])
    
    # ==========================================================================
    # SAMPLE WEBSTORE (Draft mode - not live)
    # ==========================================================================
    
    sample_webstore = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "name": "Demo Fundraiser Store",
        "description": "This is a sample fundraiser store. Customize it for your customers!",
        "store_type": "fundraiser",
        "status": "draft",  # Cannot go live during trial
        "is_public": False,
        "is_sample_data": True,
        "owner_name": "Riverside Youth Soccer League",
        "owner_email": "demo-fundraiser@rysoccer.example",
        "branding": {
            "primary_color": "#22C55E",
            "logo_url": None,
            "banner_url": None,
        },
        "fundraiser_goal": 5000.00,
        "fundraiser_profit_percent": 30,
        "total_sales": 0,
        "total_orders": 0,
        "total_profit": 0,
        "payout_owed": 0,
        "payout_paid": 0,
        "products": [],  # Products added separately
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    await db.webstores_v2.insert_one(sample_webstore)
    created_items["webstores"].append(sample_webstore["name"])
    
    # Add sample products to webstore
    for product in sample_products:
        webstore_product = {
            "id": str(uuid.uuid4()),
            "webstore_id": sample_webstore["id"],
            "product_id": product["id"],
            "is_enabled": True,
            "price_override": None,
            "created_at": now.isoformat(),
        }
        await db.webstore_products.insert_one(webstore_product)
    
    return {
        "success": True,
        "created": created_items,
        "message": "Sample data created successfully! Explore customers, jobs, invoices, and webstores to see how SignGuy AI works.",
    }


async def delete_sample_data_for_tenant(db, tenant_id: str) -> dict:
    """
    Delete all sample data for a tenant (optional cleanup).
    Called when user wants to start fresh or during subscription activation.
    """
    results = {
        "customers_deleted": 0,
        "jobs_deleted": 0,
        "invoices_deleted": 0,
        "webstores_deleted": 0,
        "products_deleted": 0,
    }
    
    # Delete sample customers
    result = await db.customers.delete_many({"tenant_id": tenant_id, "is_sample_data": True})
    results["customers_deleted"] = result.deleted_count
    
    # Delete sample jobs
    result = await db.jobs.delete_many({"tenant_id": tenant_id, "is_sample_data": True})
    results["jobs_deleted"] = result.deleted_count
    
    # Delete sample invoices
    result = await db.invoices.delete_many({"tenant_id": tenant_id, "is_sample_data": True})
    results["invoices_deleted"] = result.deleted_count
    
    # Delete sample webstores
    sample_stores = await db.webstores_v2.find({"tenant_id": tenant_id, "is_sample_data": True}).to_list(100)
    for store in sample_stores:
        await db.webstore_products.delete_many({"webstore_id": store["id"]})
    result = await db.webstores_v2.delete_many({"tenant_id": tenant_id, "is_sample_data": True})
    results["webstores_deleted"] = result.deleted_count
    
    # Delete sample products
    result = await db.products.delete_many({"tenant_id": tenant_id, "is_sample_data": True})
    results["products_deleted"] = result.deleted_count
    
    return results
