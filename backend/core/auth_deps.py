"""
Core Authentication Dependencies (canonical-source shim).

Historically this module duplicated the JWT secret, DB connection, and
auth helpers found in :mod:`core_runtime`. Two divergences crept in:

* DB_NAME defaulted to ``"signage_erp"`` here, ``"signguy_ai"`` in
  :mod:`core.config`, and was strict in :mod:`core_runtime`. Token
  validation could read users from a different database depending on
  which symbol a route imported.
* JWT secret was sourced from ``JWT_SECRET_KEY`` here and in
  :mod:`core_runtime` but from ``JWT_SECRET`` in :mod:`core.config`.

This shim re-exports the canonical names so every route module shares the
same DB client, secret, algorithm, and auth dependency chain regardless
of which import path it uses.
"""

from core_runtime import (  # re-export — single source of truth
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    client as _client,
    db as _db,
    get_current_active_user,
    get_current_user,
    pwd_context,
    security,
)

__all__ = [
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "SECRET_KEY",
    "_client",
    "_db",
    "get_current_active_user",
    "get_current_user",
    "pwd_context",
    "security",
]
