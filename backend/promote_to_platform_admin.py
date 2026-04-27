"""
Platform Admin Setup Script

This script promotes an existing user to platform_admin role.
Usage: python promote_to_platform_admin.py <email>
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent))

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

async def promote_user_to_platform_admin(email: str):
    """Promote a user to platform_admin role"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Find user
        user = await db.users.find_one({"email": email.lower()}, {"_id": 0})
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
        
        # Update user role to platform_admin
        result = await db.users.update_one(
            {"email": email.lower()},
            {"$set": {"role": "platform_admin"}}
        )
        
        if result.modified_count > 0:
            print(f"✅ Successfully promoted {email} to platform_admin")
            print(f"   User ID: {user['id']}")
            print(f"   Name: {user.get('full_name', 'N/A')}")
            print(f"   Previous Role: {user.get('role', 'N/A')}")
            print(f"   New Role: platform_admin")
            return True
        else:
            print(f"⚠️  No changes made. User might already be platform_admin.")
            print(f"   Current Role: {user.get('role', 'N/A')}")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        client.close()

async def list_platform_admins():
    """List all platform admins"""
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        admins = await db.users.find(
            {"role": "platform_admin"},
            {"_id": 0, "id": 1, "email": 1, "full_name": 1}
        ).to_list(100)
        
        if admins:
            print("\n📋 Current Platform Admins:")
            for admin in admins:
                print(f"   - {admin.get('full_name', 'N/A')} ({admin['email']})")
        else:
            print("\n📋 No platform admins found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python promote_to_platform_admin.py <email>")
        print("   Or: python promote_to_platform_admin.py --list")
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        asyncio.run(list_platform_admins())
    else:
        email = sys.argv[1]
        success = asyncio.run(promote_user_to_platform_admin(email))
        asyncio.run(list_platform_admins())
        sys.exit(0 if success else 1)
