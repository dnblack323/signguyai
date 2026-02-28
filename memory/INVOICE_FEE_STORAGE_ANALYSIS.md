# Invoice Platform Fee - Storage Analysis & Test Results

**Date:** December 2025  
**Test File:** `/app/backend/tests/test_invoice_platform_fees.py`

---

## BUSINESS RULE (AUTHORITATIVE)

**Platform fees apply ONLY when the platform processes the payment.**

| Payment Type | Platform Fee | Reason |
|--------------|--------------|--------|
| **Stripe Invoice Payment** | Calculated based on plan | Platform processes payment |
| **Manual Payment (cash/check/external)** | **Always $0.00** | No platform processing |
| **Webstore Order** | Calculated based on plan | Platform-mediated |

---

## 1. FEE STORAGE LOCATIONS

### 1.1 Stripe Payments (Online) - FEES APPLY
**Location:** `db.payment_transactions`  
**File:** `/app/backend/routes/stripe_connect.py` line 362-374

```python
payment_record = {
    'id': session.id,
    'tenant_id': tenant_id,
    'type': 'invoice',
    'reference_id': invoice_id,
    'amount': amount,
    'platform_fee': platform_fee_cents / 100,  # ← Calculated fee
    'currency': 'usd',
    'status': 'pending',
    ...
}
await db.payment_transactions.insert_one(payment_record)
```

### 1.2 Manual Payments (Offline) - NO FEES
**Location:** `db.payments`  
**File:** `/app/backend/routes/invoices.py` line 260-280

```python
payment_record = {
    'invoice_id': invoice_id,
    'tenant_id': current_user.tenant_id,
    'amount': amount,
    'platform_fee': 0.00,                                    # ← Always zero
    'platform_fee_percent': 0.0,                             # ← Always zero
    'platform_fee_reason': 'manual_payment_no_platform_processing',
    'payment_method': payment_method or 'manual',
    'payment_type': 'manual',
    'notes': notes,
    'created_at': datetime.now(timezone.utc).isoformat()
}
await db.payments.insert_one(payment_record)
```

**Manual payments intentionally have no platform fee** - the platform does not process manual/cash/check payments, so no fee is earned.

---

## 2. FEE CALCULATION PATH

### Code Path:
1. **Get tenant's plan:** `multi_product_gate.get_tenant_plan(tenant_id)` → `PlanType`
2. **Get fee config:** `multi_product_gate.get_processing_fees(tenant_id)` → `ProcessingFees`
3. **Calculate fee:** `multi_product_gate.calculate_platform_fee(amount, fee_percent)` → `float`

### Fee Source Files:
| File | Function | Purpose |
|------|----------|---------|
| `plan_configs.py` | `get_plan_config()` | Base fee rates per plan |
| `multi_product_gate.py` | `get_processing_fees()` | Fee with founder discounts |
| `multi_product_gate.py` | `calculate_platform_fee()` | Round to 2 decimals |

---

## 3. TEST RESULTS

### All 23 Tests PASSED ✅

```
TestPlanConfigFees::test_os_starter_invoice_fee                    PASSED
TestPlanConfigFees::test_os_pro_invoice_fee                        PASSED
TestPlanConfigFees::test_os_business_invoice_fee                   PASSED
TestPlanConfigFees::test_webstore_plans_no_invoice_fee             PASSED
TestPlanConfigFees::test_ai_studio_plans_no_invoice_fee            PASSED
TestMultiProductGateFees::test_os_pro_non_founder_fee              PASSED
TestMultiProductGateFees::test_os_business_founder_annual_fee      PASSED
TestMultiProductGateFees::test_os_business_founder_monthly_fee     PASSED
TestMultiProductGateFees::test_os_starter_zero_fee                 PASSED
TestFeeRounding::test_rounding_99_99_at_1_percent                  PASSED
TestFeeRounding::test_rounding_100_00_at_1_percent                 PASSED
TestFeeRounding::test_rounding_100_00_at_0_5_percent               PASSED
TestFeeRounding::test_rounding_99_99_at_0_5_percent                PASSED
TestFeeRounding::test_rounding_small_amount                        PASSED
TestFeeRounding::test_gate_calculate_matches_expected              PASSED
TestInvoicePaymentFeeStorage::test_stripe_payment_stores_fee       PASSED
TestInvoicePaymentFeeStorage::test_manual_payment_zero_fee_os_pro  PASSED
TestInvoicePaymentFeeStorage::test_manual_payment_zero_fee_os_business_founder_annual PASSED
TestInvoicePaymentFeeStorage::test_manual_payment_zero_fee_os_starter PASSED
TestFullScenarios::test_scenario_os_pro_non_founder                PASSED
TestFullScenarios::test_scenario_os_business_founder_annual        PASSED
TestFullScenarios::test_scenario_os_starter                        PASSED
TestFullScenarios::test_scenario_rounding_99_99                    PASSED
```

---

## 4. VERIFIED SCENARIOS

### Scenario 1: OS_PRO, non-founder
| Setting | Value |
|---------|-------|
| Plan | `os_pro` |
| is_founder | `false` |
| Invoice Amount | $100.00 |
| **fee_percent** | **1.0%** |
| **platform_fee** | **$1.00** |

### Scenario 2: OS_BUSINESS, founder, annual
| Setting | Value |
|---------|-------|
| Plan | `os_business` |
| is_founder | `true` |
| billing_interval | `annual` |
| Invoice Amount | $100.00 |
| **fee_percent** | **0.5%** (founder discount) |
| **platform_fee** | **$0.50** |

### Scenario 3: OS_STARTER
| Setting | Value |
|---------|-------|
| Plan | `os_starter` |
| Invoice Amount | $100.00 |
| **fee_percent** | **0.0%** |
| **platform_fee** | **$0.00** |

### Scenario 4: Rounding ($99.99 at 1%)
| Setting | Value |
|---------|-------|
| Amount | $99.99 |
| Fee Rate | 1.0% |
| Raw Calculation | 0.9999 |
| **Rounded Result** | **$1.00** |

---

## 5. FEE CONFIGURATION BY PLAN

| Plan | Invoice Fee | Webstore Fee | Founder Discount |
|------|-------------|--------------|------------------|
| OS_STARTER | 0.0% | 0.0% | N/A |
| OS_PRO | 1.0% | 3.0% | N/A |
| OS_BUSINESS | 1.0% | 2.0% | Annual: 0.5%/1.5% |
| WS_LAUNCH | 0.0% | 3.0% | N/A |
| WS_GROWTH | 0.0% | 2.5% | N/A |
| WS_SCALE | 0.0% | 2.0% | N/A |
| AI_BASIC | 0.0% | 0.0% | N/A |
| AI_PRO | 0.0% | 0.0% | N/A |
| AI_MAX | 0.0% | 0.0% | N/A |

---

## 6. ISSUES FOUND

### Issue: Manual Payments Missing Fee Storage

**Current State:** `/app/backend/routes/invoices.py` `record_payment()` does NOT calculate or store platform fees.

**Impact:** Platform revenue tracking incomplete for manual/cash/check payments.

**Severity:** MEDIUM - Affects financial reporting accuracy.

**Fix Required:** Update `record_payment()` to:
1. Get tenant's processing fees via `multi_product_gate`
2. Calculate platform fee
3. Store `platform_fee` and `fee_percent` in payment record

---

*Report generated from automated test suite execution.*
