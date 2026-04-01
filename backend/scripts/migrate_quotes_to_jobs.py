"""
Migration Script: Quotes to Jobs

This script migrates existing quotes from the 'quotes' collection to the 'jobs' collection,
preserving the original quote IDs and converting them to jobs with status='quote'.

Run this script once to unify quotes and jobs.

Usage:
    python scripts/migrate_quotes_to_jobs.py
"""

import asyncio
import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Get MongoDB connection from environment
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "signguy_ai")


async def migrate_quotes_to_jobs():
    """Migrate all quotes to jobs collection"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print(f"Connected to database: {DB_NAME}")
    
    # Get all quotes
    quotes = await db.quotes.find({}, {"_id": 0}).to_list(None)
    print(f"Found {len(quotes)} quotes to migrate")
    
    if not quotes:
        print("No quotes to migrate. Exiting.")
        return
    
    migrated = 0
    skipped = 0
    
    for quote in quotes:
        quote_id = quote.get("id")
        
        # Check if this quote has already been converted to a job
        if quote.get("job_id"):
            # Quote was already converted - skip but note for reference
            print(f"  Quote {quote_id[:8]} already converted to job {quote.get('job_id')[:8]} - skipping")
            skipped += 1
            continue
        
        # Check if a job with this ID already exists (from a previous migration attempt)
        existing_job = await db.jobs.find_one({"id": quote_id})
        if existing_job:
            print(f"  Job with ID {quote_id[:8]} already exists - skipping")
            skipped += 1
            continue
        
        # Create job from quote, preserving the original ID
        job = {
            "id": quote_id,  # PRESERVE ORIGINAL ID
            "tenant_id": quote.get("tenant_id"),
            "customer_id": quote.get("customer_id"),
            "name": f"Quote #{quote_id[:8]}",  # Use quote ID as name
            "description": quote.get("notes", ""),
            "notes": quote.get("notes", ""),
            "status": "quote",  # All migrated quotes start as quote status
            "line_items": quote.get("line_items", []),
            "total": quote.get("total", 0),
            "subtotal": quote.get("total", 0),
            "due_date": None,
            "invoice_id": None,
            "is_archived": False,
            "sent_at": quote.get("sent_at"),
            "approved_at": None,
            "quote_id": None,  # This field is for legacy backward compatibility only
            "created_at": quote.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # If quote was approved/declined, adjust status accordingly
        quote_status = quote.get("status", "draft")
        if quote_status == "approved":
            job["status"] = "approved"
            job["approved_at"] = quote.get("updated_at")
        elif quote_status == "declined":
            job["status"] = "archived"
            job["is_archived"] = True
        
        # Insert the job
        await db.jobs.insert_one(job)
        print(f"  Migrated quote {quote_id[:8]} -> job with status '{job['status']}'")
        migrated += 1
    
    print("\nMigration complete!")
    print(f"  Migrated: {migrated}")
    print(f"  Skipped: {skipped}")
    print(f"  Total quotes: {len(quotes)}")
    
    # Optionally, rename or archive the quotes collection
    # Uncomment the following to archive the quotes collection
    # await db.quotes.rename("quotes_archived")
    # print("  Renamed 'quotes' collection to 'quotes_archived'")


if __name__ == "__main__":
    asyncio.run(migrate_quotes_to_jobs())
