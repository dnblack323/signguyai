"""
Core Database Indexes Migration

Run this script to create all necessary indexes for optimal performance.
Usage: python migrations/create_core_indexes.py
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

async def create_indexes():
    """Create all necessary database indexes"""
    client = AsyncIOMotorClient(os.environ['MONGO_URL'])
    db = client[os.environ['DB_NAME']]
    
    print("Creating core database indexes...")
    
    # Users collection
    try:
        await db.users.create_index([("email", 1)], unique=True, name="idx_users_email_unique")
        await db.users.create_index([("tenant_id", 1)], name="idx_users_tenant")
        print("✓ Users indexes created")
    except Exception as e:
        print(f"⚠ Users indexes: {e}")
    
    # Tenants collection
    try:
        await db.tenants.create_index([("id", 1)], unique=True, name="idx_tenants_id_unique")
        await db.tenants.create_index([("slug", 1)], unique=True, sparse=True, name="idx_tenants_slug_unique")
        print("✓ Tenants indexes created")
    except Exception as e:
        print(f"⚠ Tenants indexes: {e}")
    
    # Jobs collection
    try:
        await db.jobs.create_index([("tenant_id", 1), ("status", 1)], name="idx_jobs_tenant_status")
        await db.jobs.create_index([("tenant_id", 1), ("customer_id", 1)], name="idx_jobs_tenant_customer")
        await db.jobs.create_index([("tenant_id", 1), ("created_at", -1)], name="idx_jobs_tenant_created")
        await db.jobs.create_index([("id", 1)], unique=True, name="idx_jobs_id_unique")
        print("✓ Jobs indexes created")
    except Exception as e:
        print(f"⚠ Jobs indexes: {e}")
    
    # Customers collection  
    try:
        await db.customers.create_index([("tenant_id", 1)], name="idx_customers_tenant")
        await db.customers.create_index([("tenant_id", 1), ("created_at", -1)], name="idx_customers_tenant_created")
        await db.customers.create_index([("id", 1)], unique=True, name="idx_customers_id_unique")
        print("✓ Customers indexes created")
    except Exception as e:
        print(f"⚠ Customers indexes: {e}")
    
    # Invoices collection
    try:
        await db.invoices.create_index([("tenant_id", 1), ("status", 1)], name="idx_invoices_tenant_status")
        await db.invoices.create_index([("tenant_id", 1), ("customer_id", 1)], name="idx_invoices_tenant_customer")
        await db.invoices.create_index([("tenant_id", 1), ("created_at", -1)], name="idx_invoices_tenant_created")
        await db.invoices.create_index([("job_id", 1)], name="idx_invoices_job")
        await db.invoices.create_index([("id", 1)], unique=True, name="idx_invoices_id_unique")
        print("✓ Invoices indexes created")
    except Exception as e:
        print(f"⚠ Invoices indexes: {e}")
    
    # Quotes collection
    try:
        await db.quotes.create_index([("tenant_id", 1), ("status", 1)], name="idx_quotes_tenant_status")
        await db.quotes.create_index([("tenant_id", 1), ("customer_id", 1)], name="idx_quotes_tenant_customer")
        await db.quotes.create_index([("id", 1)], unique=True, name="idx_quotes_id_unique")
        print("✓ Quotes indexes created")
    except Exception as e:
        print(f"⚠ Quotes indexes: {e}")
    
    # Employees collection
    try:
        await db.employees.create_index([("tenant_id", 1)], name="idx_employees_tenant")
        await db.employees.create_index([("id", 1)], unique=True, name="idx_employees_id_unique")
        print("✓ Employees indexes created")
    except Exception as e:
        print(f"⚠ Employees indexes: {e}")
    
    # AI History collection
    try:
        await db.ai_history.create_index([("tenant_id", 1), ("created_at", -1)], name="idx_ai_history_tenant_created")
        await db.ai_history.create_index([("user_id", 1)], name="idx_ai_history_user")
        print("✓ AI History indexes created")
    except Exception as e:
        print(f"⚠ AI History indexes: {e}")
    
    # Payment Transactions collection
    try:
        await db.payment_transactions.create_index([("tenant_id", 1)], name="idx_payment_transactions_tenant")
        await db.payment_transactions.create_index([("stripe_session_id", 1)], name="idx_payment_transactions_session")
        print("✓ Payment Transactions indexes created")
    except Exception as e:
        print(f"⚠ Payment Transactions indexes: {e}")
    
    # Time entries collection
    try:
        await db.time_entries.create_index([("tenant_id", 1), ("employee_id", 1)], name="idx_time_entries_tenant_employee")
        await db.time_entries.create_index([("tenant_id", 1), ("date", -1)], name="idx_time_entries_tenant_date")
        print("✓ Time Entries indexes created")
    except Exception as e:
        print(f"⚠ Time Entries indexes: {e}")
    
    # Conversations collection (customer portal)
    try:
        await db.conversations.create_index([("tenant_id", 1), ("customer_id", 1)], name="idx_conversations_tenant_customer")
        await db.conversations.create_index([("tenant_id", 1), ("updated_at", -1)], name="idx_conversations_tenant_updated")
        print("✓ Conversations indexes created")
    except Exception as e:
        print(f"⚠ Conversations indexes: {e}")
    
    print("\n✅ Core indexes migration completed!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
