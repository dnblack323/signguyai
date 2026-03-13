# SignGuy AI - Changelog

## March 13, 2026 - Login Network Error Fix (P0 CRITICAL) - Two Root Causes

### Fix 1: CORS Preflight 400 Error
- **Root Cause:** `allow_credentials=True` combined with `allow_origins=["*"]` in CORSMiddleware violated CORS spec
- **Fix:** Changed to `allow_credentials=False` — app uses Bearer token auth, not cookies
- **File:** `backend/server.py` (CORS middleware config)

### Fix 2: 3MB Tenant Response Causing Timeouts (Account-Specific)
- **Root Cause:** The admin account's tenant document contained a 2.95MB base64-encoded logo in `logo_url`. The `/api/tenant` endpoint returned the entire document on every page load (via TopAppBar), causing timeouts on production (Cloudflare/proxy limits)
- **Fix:** 
  - Excluded `logo_url` from `/api/tenant` GET response, added `has_logo` boolean flag
  - Created dedicated `/api/tenant/logo` GET endpoint for logo data
  - Updated `TopAppBar.js` to fetch logo separately and asynchronously
  - Updated `CompanySettings.js` to use dedicated logo endpoint
- **Impact:** `/api/tenant` response reduced from 2.95MB to 497 bytes
- **Files:** `backend/server.py`, `frontend/src/components/ribbon/TopAppBar.js`, `frontend/src/pages/CompanySettings.js`

### Previous Session Completed Features (Reference)
- Admin Communications Hub, Floating AI Assistant, Line-Item Production Timeline
- Webstore fixes, Company logo upload fixes, Dark mode text visibility fixes
