# Remaining Code Issues / Hardening Backlog

Last updated: April 1, 2026

## High Priority Remaining

### 1. Backend AI route complexity reduction
- `backend/routes/ai.py`
  - `generate_text_content()` is still a large multi-branch function
  - `ai_business_assistant()` is still the largest remaining active backend complexity hotspot
- Goal:
  - split prompt construction, gating, context formatting, and response handling into smaller helpers
  - preserve current behavior and credit/gate enforcement

### 2. Broader non-sensitive storage cleanup
- Token-sensitive storage has been hardened and moved to shared helpers.
- Remaining browser storage usage is mostly non-auth/session metadata and UI preferences such as:
  - preview product line
  - onboarding dismissal state
  - quick toolbar shortcut preferences
- Goal:
  - decide which values should remain persisted, which should move to session-only storage, and which should be centralized into helper utilities for consistency

### 3. Legacy/backend consistency audit
- `backend/main.py` is now lint-clean, but older compatibility/migration files still exist.
- Goal:
  - audit older non-primary runtime files and compatibility shims for consistency with current `server.py` architecture

## Medium Priority Remaining

### 4. Wider React cleanup outside priority pages
- The highest-risk hook dependency pages were fixed.
- A broader consistency pass can still be done for:
  - additional dependency arrays
  - lower-risk list keys in static/marketing screens
  - older page-level state patterns

### 5. Additional component decomposition
- `DynamicCategoryFields` and `DrawingCanvasPad` were reduced.
- More large files can still be split for maintainability, but no active runtime issue is currently known there.

## Low Priority / Optional

### 6. Test suite standardization beyond secrets cleanup
- Hardcoded credential literals were removed from the targeted test sweep.
- Further improvement opportunity:
  - shared fixtures
  - common test client/auth helpers
  - reduced duplicated setup logic across historical test files

## Not Currently Considered Active Bugs
- The circular import reported in code review is fixed
- Targeted mutable default issue is fixed
- Priority hook dependency issues are fixed in the reviewed files
- High-risk auth token localStorage usage is fixed
- Tenant user leakage in user management is fixed
- Timeclock/payroll connection issues are fixed
- Employee portal invite and permission gating are fixed