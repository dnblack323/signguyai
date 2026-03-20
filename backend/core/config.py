"""
Core configuration and shared utilities for SignGuy AI backend.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import uuid
import re

# ============== LOGGING ==============
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============== DATABASE ==============
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'signguy_ai')

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# ============== AUTH CONFIG ==============
SECRET_KEY = os.environ.get('JWT_SECRET', 'signguy-super-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = None  # Backwards-compatible reference
security = HTTPBearer()

# ============== AUTH HELPER FUNCTIONS ==============
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ============== TENANT HELPER FUNCTIONS ==============
def generate_tenant_slug(name: str) -> str:
    """Generate URL-friendly slug from tenant name"""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return f"{slug}-{uuid.uuid4().hex[:6]}"

def tenant_query(base_query: dict, tenant_id: str) -> dict:
    """Add tenant_id filter to any query"""
    return {**base_query, "tenant_id": tenant_id}

# ============== SHUTDOWN ==============
async def shutdown_db_client():
    client.close()
