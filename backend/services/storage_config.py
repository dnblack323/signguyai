"""Shared object storage configuration and initialization helpers.

This module exists to prevent circular imports between the FastAPI app setup
and the object storage service implementation.
"""

import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "signguy-ai"

logger = logging.getLogger(__name__)

_storage_key = None


def init_storage():
    """Initialize storage once and return the reusable storage key."""
    global _storage_key
    if _storage_key:
        return _storage_key

    response = requests.post(
        f"{STORAGE_URL}/init",
        json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")},
        timeout=30,
    )
    response.raise_for_status()
    _storage_key = response.json()["storage_key"]
    logger.info("Object storage initialized successfully")
    return _storage_key


def get_storage_key():
    """Return an initialized storage key."""
    return init_storage()