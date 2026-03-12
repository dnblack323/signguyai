# SignGuy AI - Changelog

## March 12, 2026 - CORS Login Bug Fix (P0 CRITICAL)

### Bug Fix: Login "Network Error" - CORS Preflight 400
- **Root Cause:** `allow_credentials=True` combined with `allow_origins=["*"]` in FastAPI's CORSMiddleware violated the CORS spec. Browsers reject `Access-Control-Allow-Origin: *` when `Access-Control-Allow-Credentials: true` is present.
- **Fix:** Changed `allow_credentials=False` in `backend/server.py` CORSMiddleware config. This works because the app uses Bearer token auth (Authorization header), NOT cookies.
- **Impact:** This was a P0 critical bug that prevented ALL users from logging in. Recurring issue across 4+ forks.
- **Testing:** 16/16 backend tests passed, frontend login flow verified with no CORS errors in browser console.
- **Files Changed:** `backend/server.py` (line ~1062-1069)

### Previous Session Completed Features (Reference)
- Admin Communications Hub (backend + frontend)
- Floating AI Assistant chat widget
- Line-Item Production Timeline tracking system
- Webstore module fixes (creation bug, analytics, payouts)
- Company logo upload fixes (URL, color inversion, size)
- Dark mode text visibility fixes across all pages
