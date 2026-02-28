# SIGNGUY AI OS - MASTER PRODUCT SPEC v1.0

**Document Version:** 1.0  
**Last Updated:** December 2025  
**Source of Truth:** Extracted from codebase - `/app/backend/services/plan_configs.py`, `/app/backend/services/tier_config.py`, `/app/backend/models/product_tiers.py`, `/app/backend/services/multi_product_gate.py`

---

## 1. PRODUCT OVERVIEW

SignGuy AI is a three-product ecosystem for sign shops:

| Product Line | Internal Name | Target User | Plans |
|-------------|---------------|-------------|-------|
| **SignGuy AI OS** | `os` | Full shop management | Starter / Pro / Business |
| **SignGuy Webstores** | `webstores` | Commerce-only users | Launch / Growth / Scale |
| **SignGuy AI Studio** | `ai_studio` | AI tools-only users | Basic / Pro / Max |

---

## 2. PRICING MATRIX (From plan_configs.py)

### 2.1 SignGuy AI OS Plans

| Plan | Monthly | Annual | Founder Monthly | Founder Annual | Founder Eligible |
|------|---------|--------|-----------------|----------------|------------------|
| OS Starter | $39 | $390 | $29 | $290 | YES |
| OS Pro | $79 | $790 | $59 | $590 | YES |
| OS Business | $149 | $1,490 | $99 | $990 | YES |

### 2.2 SignGuy Webstores Plans (NO Founder Pricing)

| Plan | Monthly | Annual |
|------|---------|--------|
| WS Launch | $39 | $390 |
| WS Growth | $59 | $590 |
| WS Scale | $99 | $990 |

### 2.3 SignGuy AI Studio Plans (NO Founder Pricing)

| Plan | Monthly | Annual |
|------|---------|--------|
| AI Basic | $29 | $290 |
| AI Pro | $59 | $590 |
| AI Max | $99 | $990 |

---

## 3. PROCESSING FEES (From plan_configs.py)

| Plan | Invoice Fee | Webstore Fee | Stripe Connect | Online Payments |
|------|-------------|--------------|----------------|-----------------|
| **OS Starter** | 0% | 0% | NO | NO |
| **OS Pro** | 1% | 3% | YES | YES |
| **OS Business** | 1% | 2% | YES | YES |
| **WS Launch** | 0% | 3% | YES | NO |
| **WS Growth** | 0% | 2.5% | YES | NO |
| **WS Scale** | 0% | 2% | YES | NO |
| **AI Basic** | 0% | 0% | NO | NO |
| **AI Pro** | 0% | 0% | NO | NO |
| **AI Max** | 0% | 0% | NO | NO |

**Founder Annual Business Discount:** Invoice 0.5%, Webstore 1.5% (per multi_product_gate.py lines 207-221)

---

## 4. UI VISIBILITY FLAGS (From plan_configs.py)

| Plan | show_jobs_ui | show_payroll_ui | show_time_clock_ui | show_financials_ui | show_ai_assistant_ui |
|------|-------------|-----------------|-------------------|-------------------|---------------------|
| **OS Starter** | YES | NO | YES | NO | YES |
| **OS Pro** | YES | YES | YES | YES | YES |
| **OS Business** | YES | YES | YES | YES | YES |
| **WS Launch** | NO | NO | NO | NO | NO |
| **WS Growth** | NO | NO | NO | NO | NO |
| **WS Scale** | NO | NO | NO | NO | NO |
| **AI Basic** | NO | NO | NO | NO | YES |
| **AI Pro** | NO | NO | NO | NO | YES |
| **AI Max** | NO | NO | NO | NO | YES |

---

## 5. FEATURE GATING TABLE

### 5.1 Core Module Features

| Feature | OS Starter | OS Pro | OS Business | WS Launch | WS Growth | WS Scale | AI Basic | AI Pro | AI Max |
|---------|-----------|--------|-------------|-----------|-----------|----------|----------|--------|--------|
| customers | ON | ON | ON | ON | ON | ON | OFF | OFF | OFF |
| jobs | ON | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| invoices | ON | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| online_invoice_payments | OFF | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| dashboard | ON | ON | ON | ON | ON | ON | ON | ON | ON |
| employees | LIMITED (2) | LIMITED (10) | ON (Unlimited) | OFF | OFF | OFF | OFF | OFF | OFF |
| time_clock | ON | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| time_clock_advanced | OFF | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| tasks | ON | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| productivity | ON | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| productivity_advanced | OFF | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| payroll | OFF | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| financials | OFF | ON | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| financials_advanced | OFF | OFF | ON | OFF | OFF | OFF | OFF | OFF | OFF |
| company_settings | ON | ON | ON | ON | ON | ON | ON | ON | ON |
| email_templates | ON | ON | ON | ON | ON | ON | OFF | OFF | OFF |

### 5.2 Customer Portal Features

| Feature | OS Starter | OS Pro | OS Business | WS * | AI * |
|---------|-----------|--------|-------------|------|------|
| portal_access | OFF | ON | ON | OFF | OFF |
| messaging | OFF | ON | ON | OFF | OFF |
| artwork_approvals | OFF | ON | ON | OFF | OFF |
| documents | OFF | ON | ON | OFF | OFF |
| document_storage_mb | OFF | LIMITED (500MB) | LIMITED (2GB) | OFF | OFF |

### 5.3 Webstore Features

| Feature | OS Starter | OS Pro | OS Business | WS Launch | WS Growth | WS Scale | AI * |
|---------|-----------|--------|-------------|-----------|-----------|----------|------|
| webstore_access | OFF | ON | ON | ON | ON | ON | OFF |
| num_stores | OFF | LIMITED (3) | ON (Unlimited) | LIMITED (1) | LIMITED (5) | ON (Unlimited) | OFF |
| store_type_b2b | OFF | ON | ON | ON | ON | ON | OFF |
| store_type_fundraiser | OFF | ON | ON | ON | ON | ON | OFF |
| store_type_creator | OFF | OFF | ON | OFF | ON | ON | OFF |
| stripe_connect | OFF | ON | ON | ON | ON | ON | OFF |
| order_to_job_automation | OFF | ON | ON | OFF | OFF | OFF | OFF |
| commission_tracking | OFF | OFF | ON | ON | ON | ON | OFF |
| payout_tracking | OFF | OFF | ON | OFF | OFF | ON | OFF |
| advanced_branding | OFF | OFF | ON | OFF | ON | ON | OFF |
| price_overrides | OFF | OFF | ON | OFF | ON | ON | OFF |
| bulk_order_tools | OFF | OFF | ON | OFF | OFF | ON | OFF |
| store_analytics | OFF | ON | ON | ON | ON | ON | OFF |
| store_analytics_advanced | OFF | OFF | ON | OFF | OFF | ON | OFF |
| fundraiser_goals | OFF | ON | ON | ON | ON | ON | OFF |

### 5.4 AI Tools Features

| Feature | OS Starter | OS Pro | OS Business | WS * | AI Basic | AI Pro | AI Max |
|---------|-----------|--------|-------------|------|----------|--------|--------|
| ai_access | ON | ON | ON | OFF | ON | ON | ON |
| text_generation | ON | ON | ON | OFF | ON | ON | ON |
| image_generation | OFF | ON | ON | OFF | OFF | ON | ON |
| monthly_generations | LIMITED (25) | LIMITED (100) | ON (Unlimited) | OFF | LIMITED (25) | LIMITED (100) | ON (Unlimited) |
| branding_kit_generator | OFF | OFF | ON | OFF | OFF | OFF | ON |
| campaign_builder | OFF | OFF | ON | OFF | OFF | OFF | ON |
| pricing_intelligence | OFF | OFF | ON | OFF | OFF | OFF | ON |
| content_calendar | OFF | OFF | ON | OFF | OFF | OFF | ON |

### 5.5 AI Assistant Features

| Feature | OS Starter | OS Pro | OS Business | WS * | AI Basic | AI Pro | AI Max |
|---------|-----------|--------|-------------|------|----------|--------|--------|
| assistant_access | ON | ON | ON | OFF | ON | ON | ON |
| monthly_queries | LIMITED (10) | LIMITED (50) | ON (Unlimited) | OFF | LIMITED (10) | LIMITED (50) | ON (Unlimited) |
| business_data_aware | OFF | OFF | ON | OFF | OFF | OFF | OFF |
| business_data_limited | OFF | ON | ON | OFF | OFF | OFF | OFF |

### 5.6 CRM Features

| Feature | OS Starter | OS Pro | OS Business | WS * | AI * |
|---------|-----------|--------|-------------|------|------|
| customer_specific_pricing | OFF | OFF | ON | OFF | OFF |
| advanced_tagging | OFF | OFF | ON | OFF | OFF |
| portal_document_sharing | OFF | OFF | ON | OFF | OFF |

---

## 6. FOUNDER PROGRAM RULES (From models/product_tiers.py)

| Rule | Value | Source |
|------|-------|--------|
| Total Founder Spots | 100 | `FOUNDER_SPOTS_TOTAL = 100` |
| Founder Eligible Products | OS Plans ONLY | `founder_eligible=True` only on OS Starter/Pro/Business |
| Webstore Founder Pricing | NOT AVAILABLE | All WS plans have `founder_monthly=None` |
| AI Studio Founder Pricing | NOT AVAILABLE | All AI plans have `founder_monthly=None` |

---

## 7. LEGACY TIER MAPPING (From plan_configs.py lines 917-930)

| Legacy Tier Name | Maps To |
|------------------|---------|
| `starter` | OS_STARTER |
| `pro` | OS_PRO |
| `business` | OS_BUSINESS |
| `tier_1` | OS_STARTER |
| `tier_2` | OS_PRO |
| `tier_3` | OS_BUSINESS |

---

## 8. USAGE TRACKING (From multi_product_gate.py)

Features tracked for LIMITED status:
- `ai_tools.monthly_generations`
- `ai_assistant.monthly_queries`
- `core.employees`
- `webstores.num_stores`
- `customer_portal.document_storage_mb`

Monthly reset features:
- `ai_tools.monthly_generations`
- `ai_assistant.monthly_queries`

---

## 9. MISSING OR AMBIGUOUS DEFINITIONS

### 9.1 Pricing Discrepancies
- **PRD.md (lines 14-29)** shows different pricing than **plan_configs.py**:
  - PRD: Starter $79/$129, Growth $129/$229, Pro $199/$379
  - Code: OS Starter $39/$29, OS Pro $79/$59, OS Business $149/$99
  - **AMBIGUITY:** Two different pricing structures exist. Code is the source of truth.

### 9.2 Undefined Features (Present in tier_config.py but NOT in plan_configs.py)
The legacy `tier_config.py` has these feature categories that are NOT in the new multi-product `plan_configs.py`:
- `webstore_payments` (cash_check, stripe, paypal, affirm, klarna, store_credit)
- `b2b` (b2b_access, volume_discounts, net_terms, budget_limits, purchase_orders, approval_workflows)
- `creator_affiliate` (creator_access, commission_tracking, affiliate_links, payout_management)
- `analytics` (basic_summary, category_breakdown, profit_analysis, customer_insights, trend_analysis, export_reports, custom_reports, scheduled_reports, cash_flow_projections)
- `communications` (email_notifications, sms, abandoned_cart, marketing_emails)
- `integrations` (paypal, affirm, klarna, twilio, quickbooks, google_analytics, facebook_pixel, zapier, mailchimp)
- `data` (storage_mb, data_export, retention_years, backup)

**AMBIGUITY:** Two tier configuration systems exist. Need clarification on which is authoritative.

### 9.3 Missing Definitions
1. **Trial System:** Trial rules mentioned in PRD but no corresponding plan config
2. **Extended Trial:** $19.99 for 14 days mentioned in PRD but no enforcement logic found
3. **AI Tools Add-On:** $49/mo mentioned in PRD but no standalone add-on plan in code
4. **Employee Portal Feature Gating:** Settings for employee portal access exist but not in plan_configs.py
5. **Promo Codes:** PromoCodes.js page exists but no tier-based promo code rules defined

### 9.4 Conflicting Sources
| Item | tier_config.py Value | plan_configs.py Value |
|------|---------------------|----------------------|
| Starter team_members | LIMITED (1) | LIMITED (2) |
| Pro team_members | LIMITED (5) | LIMITED (10) |
| Starter price_monthly | $0 | $39 |
| Pro price_monthly | $49 | $79 |
| Business price_monthly | $149 | $149 |

**RECOMMENDATION:** Confirm which configuration file is authoritative and deprecate the other.

---

## 10. ENFORCEMENT LOGIC LOCATIONS

| Gate Type | File | Function |
|-----------|------|----------|
| Feature Access Check | `multi_product_gate.py` | `check_feature()` |
| Feature Requirement (403) | `multi_product_gate.py` | `require_feature()` |
| UI Visibility | `multi_product_gate.py` | `get_ui_visibility()` |
| Processing Fees | `multi_product_gate.py` | `get_processing_fees()` |
| Usage Increment | `multi_product_gate.py` | `_increment_usage()` |
| Monthly Reset | `multi_product_gate.py` | `reset_monthly_usage()` |
| Plan Changes | `multi_product_gate.py` | `set_tenant_plan()` |

---

## 11. STRIPE INTEGRATION

- Stripe TEST keys configured (per PRD)
- Stripe Connect enabled for: OS Pro, OS Business, WS Launch, WS Growth, WS Scale
- Online invoice payments enabled for: OS Pro, OS Business only

---

## DOCUMENT CHANGELOG

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2025 | Initial extraction from codebase |

---

*This document is auto-generated from codebase analysis. Do not modify without updating source files.*
