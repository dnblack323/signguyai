"""
Wrap Command Center package.

Phase 2F refactor — wrap.py was split into a routes/wrap/ package. The original
behemoth lives on (for now) in ``core.py`` and exposes the canonical ``router``
plus all shared helpers. New Phase 2F functionality lives in dedicated sibling
modules:

- ``files``  — Photos & Files uploads (wrap_files collection)
- ``portal`` — Customer-facing summary endpoint (consumed by the existing
              Customer Portal in routes/portal.py — NOT a separate portal)
- ``pdfs``   — Customer Receipt / Aftercare / Final Packet PDF generators

All authenticated routers are mounted on the same ``/wrap`` prefix via
``router.include_router`` so existing endpoint paths are preserved exactly.

NOTE: There is intentionally NO public unauthenticated wrap-care portal.
Customer-facing wrap content is exposed through the existing Customer Portal
routes (see routes/portal.py) which use the standard portal JWT auth.
"""
from .core import router  # canonical /wrap router (Phase 1-2E endpoints)
from .files import files_router
from .portal import portal_router
from .pdfs import pdfs_router

# Mount sub-routers under the same /wrap prefix.
router.include_router(files_router)
router.include_router(portal_router)
router.include_router(pdfs_router)

__all__ = ["router"]
