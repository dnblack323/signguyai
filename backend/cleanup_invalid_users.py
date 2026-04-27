"""
Clean up invalid user data

This script fixes users with invalid roles or email addresses.
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

async def cleanup_invalid_users():
    """Find and fix users with invalid data"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Valid roles
        valid_roles = ['owner', 'admin', 'staff', 'platform_admin']
        
        # Find users with invalid roles
        all_users = await db.users.find({}, {"_id": 0}).to_list(10000)
        
        invalid_role_users = []
        invalid_email_users = []
        
        for user in all_users:
            role = user.get('role', '')
            email = user.get('email', '')
            
            # Check role
            if role not in valid_roles:
                invalid_role_users.append(user)
            
            # Check email (basic check for invalid domains)
            if '@' in email and any(domain in email for domain in ['.local', '.test', '.invalid']):
                invalid_email_users.append(user)
        
        print(f"\n📊 Found:")
        print(f"   - {len(invalid_role_users)} users with invalid roles")
        print(f"   - {len(invalid_email_users)} users with invalid email domains")
        
        if invalid_role_users:
            print(f"\n❌ Users with invalid roles:")
            for user in invalid_role_users:
                print(f"   - {user.get('email')} (role: {user.get('role')})")
        
        if invalid_email_users:
            print(f"\n❌ Users with invalid email domains:")
            for user in invalid_email_users:
                print(f"   - {user.get('email')}")
        
        # Ask for confirmation to fix
        if invalid_role_users or invalid_email_users:
            print(f"\n⚠️  Options:")
            print("   1. Delete invalid users")
            print("   2. Fix invalid roles (set to 'staff')")
            print("   3. Exit without changes")
            
            choice = input("\nEnter choice (1/2/3): ").strip()
            
            if choice == "1":
                # Delete invalid users
                for user in invalid_role_users + invalid_email_users:
                    await db.users.delete_one({"id": user['id']})
                    print(f"✓ Deleted: {user.get('email')}")
                print(f"\n✅ Deleted {len(invalid_role_users) + len(invalid_email_users)} users")
                
            elif choice == "2":
                # Fix invalid roles
                for user in invalid_role_users:
                    await db.users.update_one(
                        {"id": user['id']},
                        {"$set": {"role": "staff"}}
                    )
                    print(f"✓ Fixed role for: {user.get('email')} -> staff")
                print(f"\n✅ Fixed {len(invalid_role_users)} users")
                
            else:
                print("\n❌ No changes made")
        else:
            print("\n✅ No invalid users found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_invalid_users())
