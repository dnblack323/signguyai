# Complete Feature Reference - Last Two Weeks

**Created:** March 11, 2026
**Purpose:** Know what features should exist if you rollback, and what to add back

---

# WEEK 1: Feb 28 - March 8 (Previous Week)

## Major Features Added

### 1. Admin Portal (`/admin-portal`)
**Files:**
- `backend/routes/admin_portal.py` - NEW (715 lines)
- `frontend/src/pages/AdminPortal.js` - NEW (866 lines)
- `backend/tests/test_admin_portal.py` - NEW

**Features:**
- View/respond to customer messages
- Artwork approval workflow
- Customer communication hub

---

### 2. Credits System
**Files:**
- `backend/models/credits.py` - NEW
- `backend/routes/credits.py` - NEW (459 lines)
- `backend/services/credit_service.py` - NEW (176 lines)
- `frontend/src/components/credits/CreditBalance.js` - NEW

**Features:**
- AI credit tracking and deduction
- Credit balance display
- Usage tracking

---

### 3. Production Timeline
**Files:**
- `backend/models/production_timeline.py` - NEW
- `backend/routes/production_timeline.py` - NEW (619 lines)
- `frontend/src/components/ProductionTimeline.js` - NEW
- `frontend/src/pages/settings/ProductionSettings.js` - NEW (676 lines)

**Features:**
- Job production tracking
- Timeline visualization
- Production settings

---

### 4. Founders Edition System
**Files:**
- `backend/services/founders_config.py` - NEW (496 lines)
- `frontend/src/pages/FoundersEditionPricing.js` - NEW (477 lines)
- `frontend/src/pages/WhyFounderPage.js` - NEW (590 lines)
- `frontend/src/components/founders/CreditMeter.js` - NEW
- `frontend/src/components/founders/FoundersBadge.js` - NEW

**Features:**
- Founders edition pricing display
- Credit meter widget
- Founder badge display

---

### 5. Dev Panel
**Files:**
- `frontend/src/components/DevPanel.js` - NEW (283 lines)
- `backend/routes/dev.py` - NEW (287 lines)

**Features:**
- Developer tools panel
- Debug utilities

---

### 6. Floating Assistant
**Files:**
- `frontend/src/components/FloatingAssistant.js` - NEW (533 lines)

**Features:**
- AI assistant overlay
- Quick help access

---

### 7. Sample Data Service
**Files:**
- `backend/services/sample_data.py` - NEW (401 lines)

**Features:**
- Generate sample data for new accounts
- Demo data creation

---

### 8. Webstore Enhancements
**Files:**
- `backend/routes/webstores.py` - Updated (244+ lines added)
- `frontend/src/pages/Webstores.js` - Major update
- `backend/tests/test_webstore_analytics_payouts.py` - NEW
- `backend/tests/test_webstore_order_flow.py` - NEW

**Features:**
- Analytics and payouts
- Order flow improvements
- Enhanced webstore management

---

### 9. Jobs Page Enhancements
**Files:**
- `frontend/src/pages/Jobs.js` - Major update (800+ lines changed)

**Features:**
- Bulk actions
- Search functionality
- Enhanced UI

---

### 10. Landing Page Update
**Files:**
- `frontend/src/pages/LandingPage.js` - Major update (500+ lines added)
- `frontend/src/pages/FeaturesPage.js` - Updated
- `frontend/public/screenshots/` - NEW images

**Features:**
- New pricing display
- Feature screenshots
- Updated copy

---

### 11. 48-Hour Free Trial
**Files:**
- `backend/tests/test_48hr_free_trial.py` - NEW (284 lines)
- `frontend/src/components/TrialLockout.js` - Updated

**Features:**
- Trial period tracking
- Lockout screen

---

### 12. Invoice Line Items Fix
**Files:**
- `backend/routes/invoices.py` - Updated (91 lines changed)
- `backend/tests/test_invoice_from_job_line_items.py` - NEW

**Features:**
- Line items properly copied from job to invoice

---

### 13. Shell Card Component
**Files:**
- `frontend/src/components/ui/shell-card.jsx` - NEW (110 lines)

**Features:**
- Consistent card styling

---

### 14. Plans/Tiers Route
**Files:**
- `backend/routes/plans.py` - NEW (84 lines)

**Features:**
- Subscription plan management

---

### 15. Quick Add Customer to Jobs
**Files:**
- `frontend/src/pages/Customers.js` - Updated (80 lines changed)

**Features:**
- Quick add job from customer modal

---

## Config Changes (Week 1)

### Stripe Config
**File:** `backend/config/stripe_config.py`
- Founders Edition price IDs
- Credit pack pricing
- Promo code configuration

### Auth Updates
**File:** `backend/routes/auth.py`
- Rate limiting added
- Trial period logic

### Billing Updates
**File:** `backend/routes/billing.py`
- Founders checkout routes
- Credit purchase routes

---

# WEEK 2: March 9-11 (Current Week)

## See: /app/CHANGES_TO_REINSTATE.md

Quick summary:
1. **bcrypt==4.0.1** - CRITICAL for login
2. **AI routes fix** - CRITICAL for AI tools
3. **Soft delete system** - Data safety
4. **Materials & Inventory** - New feature
5. **Pricing Calculator integration** - Enhancement
6. **Promo code "Free Days" type** - New feature
7. **Navigation links** - Documents, Admin Portal
8. **CORS configuration** - Updated

---

# ROLLBACK GUIDE

## If you rollback to Feb 28 (5b3c327):
You will LOSE everything above. This is before all the major features.

## If you rollback to March 4 (38b8b2a):
You will HAVE:
- Admin Portal
- Credits System
- Production Timeline
- Founders Edition
- Dev Panel
- Webstore enhancements
- Jobs enhancements
- Landing page updates

You will LOSE:
- This week's changes (soft delete, materials, etc.)
- Need to add bcrypt==4.0.1 fix

## If you rollback to March 7 (8d6afe7):
You will HAVE:
- Everything from March 4
- Additional fixes

You will LOSE:
- This week's changes
- Need to add bcrypt==4.0.1 fix

## If you rollback to March 8 (89f7f3d):
You will HAVE:
- All Week 1 features

You will LOSE:
- Only this week's changes
- Need to add bcrypt==4.0.1 fix

---

# CRITICAL: After ANY Rollback

You MUST change `backend/requirements.txt`:

FROM:
```
bcrypt==4.1.3
```

TO:
```
bcrypt==4.0.1
```

This fixes the login issue. Without this change, NO ONE can log in.

---

# Files to Check After Rollback

Run these commands to verify key features exist:

```bash
# Check Admin Portal exists
ls backend/routes/admin_portal.py
ls frontend/src/pages/AdminPortal.js

# Check Credits system exists
ls backend/routes/credits.py
ls backend/services/credit_service.py

# Check Production Timeline exists
ls backend/routes/production_timeline.py

# Check Founders config exists
ls backend/services/founders_config.py

# Check bcrypt version
grep bcrypt backend/requirements.txt
```

---

# Recommended Rollback Point

**March 8, 2026 - Commit 89f7f3d**

This has all the major features from previous week, just missing this week's additions. After rollback:
1. Fix bcrypt to 4.0.1
2. Deploy
3. Test login
4. Then add back this week's features one by one

---

# Support

If deployment still shows "Deployment not found" after rollback:
- Discord: https://discord.gg/VzKfwCXC4A
- Email: support@emergent.sh

Include your Job ID (click "i" button in top-right of chat)
