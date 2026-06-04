"""
Core configuration (canonical-source shim).

This module previously held a SECOND copy of the DB connection and JWT
secret, using its own env-var names (``JWT_SECRET`` instead of
``JWT_SECRET_KEY``) and its own DB_NAME default (``"signguy_ai"`` instead
of the strict env from :mod:`core_runtime`).

It now re-exports everything from :mod:`core_runtime` so all importers
share one MongoDB client, one JWT secret, and one set of auth helpers.
"""

import logging
import re
import uuid

from core_runtime import (  # re-export — single source of truth
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    client,
    create_access_token,
    db,
    generate_tenant_slug,
    get_password_hash,
    pwd_context,
    security,
    verify_password,
)

logger = logging.getLogger(__name__)

# Convenience constants — kept for any historical importer that read the
# raw env-var values directly. They mirror what :mod:`core_runtime` did
# at startup.
import os  # noqa: E402

MONGO_URL = os.environ['MONGO_URL']
DB_NAME = os.environ['DB_NAME']


def tenant_query(base_query: dict, tenant_id: str) -> dict:
    """Add tenant_id filter to any query (legacy helper)."""
    return {**base_query, "tenant_id": tenant_id}


async def shutdown_db_client():
    client.close()


__all__ = [
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "SECRET_KEY",
    "MONGO_URL",
    "DB_NAME",
    "client",
    "db",
    "logger",
    "pwd_context",
    "security",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "generate_tenant_slug",
    "tenant_query",
    "shutdown_db_client",
    "re",
    "uuid",
]
