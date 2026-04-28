"""Shared runtime/auth dependencies for backend modules.

This module prevents route modules from importing `server.py` directly for core
objects like `db`, `logger`, and auth helpers.
"""

from datetime import datetime, timedelta, timezone
import logging
import os
from pathlib import Path
from typing import Optional

import bcrypt
import jwt
import secrets
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient

from models import Permission, ROLE_PERMISSIONS, TokenData, UserInDB

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
security = HTTPBearer(auto_error=False)
pwd_context = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserInDB:
    credentials_exception = HTTPException(
        status_code=401,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    if credentials is None:
        raise credentials_exception
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get('sub')
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
        
        # Extract impersonation metadata if present
        impersonation_metadata = None
        if payload.get('impersonating'):
            impersonation_metadata = {
                'is_impersonating': True,
                'impersonation_log_id': payload.get('impersonation_log_id'),
                'platform_admin_id': payload.get('platform_admin_id'),
                'platform_admin_email': payload.get('platform_admin_email'),
            }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token has expired')
    except jwt.PyJWTError:
        raise credentials_exception

    user = await db.users.find_one({'id': token_data.user_id}, {'_id': 0})
    if user is None:
        raise credentials_exception
    
    user_obj = UserInDB(**user)
    
    # Attach impersonation metadata to user object for frontend consumption
    if impersonation_metadata:
        user_obj.__dict__['impersonation'] = impersonation_metadata
    
    return user_obj


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail='Inactive user')

    # Block users whose tenant is suspended (skip platform admins).
    if (
        current_user.tenant_id
        and getattr(current_user, "role", None)
        and getattr(current_user.role, "value", current_user.role) != "platform_admin"
    ):
        tenant = await db.tenants.find_one(
            {"id": current_user.tenant_id},
            {"_id": 0, "is_active": 1, "suspension_reason": 1, "suspended_at": 1},
        )
        if tenant and tenant.get("is_active") is False:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "tenant_suspended",
                    "message": "This account is suspended. Please contact support.",
                    "reason": tenant.get("suspension_reason"),
                    "suspended_at": tenant.get("suspended_at"),
                },
            )
    return current_user


def has_permission(user: UserInDB, permission: Permission) -> bool:
    # Platform admins and owners have all permissions
    if user.role.value in ('owner', 'platform_admin'):
        return True
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions


def generate_tenant_slug(name: str) -> str:
    import re
    import uuid

    base = re.sub(r'[^a-zA-Z0-9\s-]', '', name.lower())
    base = re.sub(r'[-\s]+', '-', base).strip('-')
    return f"{base}-{str(uuid.uuid4())[:8]}"