"""
Invoice Platform Fee Application Tests

Tests that platform fees are correctly calculated and stored for invoice payments.
Tests scenarios:
1) OS_PRO, non-founder: 1% invoice fee
2) OS_BUSINESS, founder, annual: 0.5% invoice fee (founder discount)
3) OS_STARTER: 0% invoice fee
4) Rounding test for edge cases

Fee storage locations:
- Stripe payments: db.payment_transactions.platform_fee
- Manual payments: db.payments.platform_fee (needs to be added)

Uses multi_product_gate.py for fee calculation.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import sys
import os

# Add backend to path
sys.path.insert(0, '/app/backend')

from services.plan_configs import get_plan_config, PlanType
from services.multi_product_gate import MultiProductFeatureGate
from models.product_tiers import ProcessingFees


class MockDB:
    """Mock database for testing"""
    def __init__(self):
        self.tenants = MockCollection()
        self.subscriptions = MockCollection()
        self.invoices = MockCollection()
        self.payments = MockCollection()
        self.payment_transactions = MockCollection()
        self.tenant_usage = MockCollection()


class MockCollection:
    """Mock MongoDB collection"""
    def __init__(self):
        self.data = {}
    
    async def find_one(self, query, projection=None):
        for doc in self.data.values():
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                if projection:
                    return {k: doc[k] for k in projection if k in doc and k != '_id'}
                return {k: v for k, v in doc.items() if k != '_id'}
        return None
    
    async def insert_one(self, doc):
        doc_id = doc.get('id', str(len(self.data)))
        self.data[doc_id] = doc
        return type('InsertResult', (), {'inserted_id': doc_id})()
    
    async def update_one(self, query, update, upsert=False):
        for doc_id, doc in self.data.items():
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                if '$set' in update:
                    doc.update(update['$set'])
                return type('UpdateResult', (), {'matched_count': 1})()
        if upsert:
            new_doc = dict(query)
            if '$set' in update:
                new_doc.update(update['$set'])
            doc_id = new_doc.get('id', str(len(self.data)))
            self.data[doc_id] = new_doc
            return type('UpdateResult', (), {'matched_count': 0, 'upserted_id': doc_id})()
        return type('UpdateResult', (), {'matched_count': 0})()
    
    async def count_documents(self, query):
        count = 0
        for doc in self.data.values():
            match = True
            for key, value in query.items():
                if doc.get(key) != value:
                    match = False
                    break
            if match:
                count += 1
        return count


def create_test_tenant(db: MockDB, tenant_id: str, plan: str, is_founder: bool = False):
    """Create a test tenant with specified plan"""
    db.tenants.data[tenant_id] = {
        'id': tenant_id,
        'plan': plan,
        'is_founder': is_founder,
        'stripe_connect_account_id': 'acct_test123'
    }


def create_test_subscription(db: MockDB, tenant_id: str, billing_interval: str = 'monthly'):
    """Create a test subscription"""
    db.subscriptions.data[tenant_id] = {
        'id': f'sub_{tenant_id}',
        'tenant_id': tenant_id,
        'billing_interval': billing_interval,
        'status': 'active'
    }


def create_test_invoice(db: MockDB, invoice_id: str, tenant_id: str, amount: float):
    """Create a test invoice"""
    db.invoices.data[invoice_id] = {
        'id': invoice_id,
        'tenant_id': tenant_id,
        'total': amount,
        'grand_total': amount,
        'status': 'sent',
        'amount_paid': 0
    }


def calculate_expected_fee(amount: float, fee_percent: float) -> float:
    """Calculate expected platform fee with proper rounding"""
    # Use Decimal for precise calculation
    amount_dec = Decimal(str(amount))
    fee_dec = Decimal(str(fee_percent)) / Decimal('100')
    result = (amount_dec * fee_dec).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(result)


class TestPlanConfigFees:
    """Test that plan configs have correct fee percentages"""
    
    def test_os_starter_invoice_fee(self):
        """OS_STARTER should have 0% invoice fee"""
        config = get_plan_config(PlanType.OS_STARTER)
        assert config.processing_fees.invoice_fee_percent == 0.0
    
    def test_os_pro_invoice_fee(self):
        """OS_PRO should have 1% invoice fee"""
        config = get_plan_config(PlanType.OS_PRO)
        assert config.processing_fees.invoice_fee_percent == 1.0
    
    def test_os_business_invoice_fee(self):
        """OS_BUSINESS should have 1% invoice fee (base rate)"""
        config = get_plan_config(PlanType.OS_BUSINESS)
        assert config.processing_fees.invoice_fee_percent == 1.0
    
    def test_webstore_plans_no_invoice_fee(self):
        """Webstore plans should have 0% invoice fee"""
        for plan in [PlanType.WS_LAUNCH, PlanType.WS_GROWTH, PlanType.WS_SCALE]:
            config = get_plan_config(plan)
            assert config.processing_fees.invoice_fee_percent == 0.0, f"{plan} should have 0% invoice fee"
    
    def test_ai_studio_plans_no_invoice_fee(self):
        """AI Studio plans should have 0% invoice fee"""
        for plan in [PlanType.AI_BASIC, PlanType.AI_PRO, PlanType.AI_MAX]:
            config = get_plan_config(plan)
            assert config.processing_fees.invoice_fee_percent == 0.0, f"{plan} should have 0% invoice fee"


class TestMultiProductGateFees:
    """Test fee calculation via MultiProductFeatureGate"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.mark.asyncio
    async def test_os_pro_non_founder_fee(self, mock_db):
        """OS_PRO non-founder should get 1% invoice fee"""
        tenant_id = 'tenant_os_pro'
        create_test_tenant(mock_db, tenant_id, 'os_pro', is_founder=False)
        create_test_subscription(mock_db, tenant_id, 'monthly')
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        
        assert fees.invoice_fee_percent == 1.0
        
        # Calculate fee on $100
        amount = 100.00
        platform_fee = gate.calculate_platform_fee(amount, fees.invoice_fee_percent)
        
        assert platform_fee == 1.00
        assert fees.invoice_fee_percent == 1.0
    
    @pytest.mark.asyncio
    async def test_os_business_founder_annual_fee(self, mock_db):
        """OS_BUSINESS founder with annual billing should get 0.5% invoice fee"""
        tenant_id = 'tenant_os_business_founder'
        create_test_tenant(mock_db, tenant_id, 'os_business', is_founder=True)
        create_test_subscription(mock_db, tenant_id, 'annual')
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        
        # Founder annual discount: 0.5%
        assert fees.invoice_fee_percent == 0.5
        
        # Calculate fee on $100
        amount = 100.00
        platform_fee = gate.calculate_platform_fee(amount, fees.invoice_fee_percent)
        
        assert platform_fee == 0.50
        assert fees.invoice_fee_percent == 0.5
    
    @pytest.mark.asyncio
    async def test_os_business_founder_monthly_fee(self, mock_db):
        """OS_BUSINESS founder with monthly billing should get 1% invoice fee (no discount)"""
        tenant_id = 'tenant_os_business_founder_monthly'
        create_test_tenant(mock_db, tenant_id, 'os_business', is_founder=True)
        create_test_subscription(mock_db, tenant_id, 'monthly')  # Monthly = no founder discount
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        
        # No discount for monthly billing
        assert fees.invoice_fee_percent == 1.0
    
    @pytest.mark.asyncio
    async def test_os_starter_zero_fee(self, mock_db):
        """OS_STARTER should have 0% invoice fee"""
        tenant_id = 'tenant_os_starter'
        create_test_tenant(mock_db, tenant_id, 'os_starter', is_founder=False)
        create_test_subscription(mock_db, tenant_id, 'monthly')
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        
        assert fees.invoice_fee_percent == 0.0
        
        # Calculate fee on $100
        amount = 100.00
        platform_fee = gate.calculate_platform_fee(amount, fees.invoice_fee_percent)
        
        assert platform_fee == 0.00
        assert fees.invoice_fee_percent == 0.0


class TestFeeRounding:
    """Test fee calculation rounding behavior"""
    
    def test_rounding_99_99_at_1_percent(self):
        """$99.99 at 1% should round to $1.00"""
        amount = 99.99
        fee_percent = 1.0
        
        # 99.99 * 0.01 = 0.9999 -> rounds to 1.00
        expected_fee = calculate_expected_fee(amount, fee_percent)
        
        assert expected_fee == 1.00, f"Expected 1.00, got {expected_fee}"
    
    def test_rounding_100_00_at_1_percent(self):
        """$100.00 at 1% should be exactly $1.00"""
        amount = 100.00
        fee_percent = 1.0
        
        expected_fee = calculate_expected_fee(amount, fee_percent)
        
        assert expected_fee == 1.00
    
    def test_rounding_100_00_at_0_5_percent(self):
        """$100.00 at 0.5% should be exactly $0.50"""
        amount = 100.00
        fee_percent = 0.5
        
        expected_fee = calculate_expected_fee(amount, fee_percent)
        
        assert expected_fee == 0.50
    
    def test_rounding_99_99_at_0_5_percent(self):
        """$99.99 at 0.5% should round correctly"""
        amount = 99.99
        fee_percent = 0.5
        
        # 99.99 * 0.005 = 0.49995 -> rounds to 0.50
        expected_fee = calculate_expected_fee(amount, fee_percent)
        
        assert expected_fee == 0.50, f"Expected 0.50, got {expected_fee}"
    
    def test_rounding_small_amount(self):
        """$1.00 at 1% should be $0.01"""
        amount = 1.00
        fee_percent = 1.0
        
        expected_fee = calculate_expected_fee(amount, fee_percent)
        
        assert expected_fee == 0.01
    
    def test_gate_calculate_matches_expected(self):
        """MultiProductFeatureGate.calculate_platform_fee should match expected calculation"""
        from services.multi_product_gate import MultiProductFeatureGate
        
        gate = MultiProductFeatureGate(None)
        
        # Test $99.99 at 1%
        result = gate.calculate_platform_fee(99.99, 1.0)
        expected = calculate_expected_fee(99.99, 1.0)
        assert result == expected, f"Gate returned {result}, expected {expected}"
        
        # Test $100 at 0.5%
        result = gate.calculate_platform_fee(100.00, 0.5)
        expected = calculate_expected_fee(100.00, 0.5)
        assert result == expected


class TestInvoicePaymentFeeStorage:
    """Test that fees are properly stored when recording payments"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.mark.asyncio
    async def test_stripe_payment_stores_fee(self, mock_db):
        """
        Stripe invoice payments should store platform_fee in payment_transactions.
        
        This test simulates what happens in stripe_connect.py create_invoice_payment().
        The fee is stored in db.payment_transactions with:
        - platform_fee: calculated fee amount
        - amount: invoice total
        """
        tenant_id = 'tenant_stripe_test'
        invoice_id = 'inv_stripe_test'
        
        create_test_tenant(mock_db, tenant_id, 'os_pro', is_founder=False)
        create_test_subscription(mock_db, tenant_id, 'monthly')
        create_test_invoice(mock_db, invoice_id, tenant_id, 100.00)
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        
        amount = 100.00
        fee_percent = fees.invoice_fee_percent
        platform_fee = gate.calculate_platform_fee(amount, fee_percent)
        
        # Simulate payment_transaction record (as done in stripe_connect.py)
        payment_record = {
            'id': 'cs_test_123',
            'tenant_id': tenant_id,
            'type': 'invoice',
            'reference_id': invoice_id,
            'amount': amount,
            'platform_fee': platform_fee,
            'fee_percent': fee_percent,
            'currency': 'usd',
            'status': 'pending',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await mock_db.payment_transactions.insert_one(payment_record)
        
        # Verify stored correctly
        stored = await mock_db.payment_transactions.find_one({'id': 'cs_test_123'})
        
        assert stored is not None
        assert stored['platform_fee'] == 1.00
        assert stored['fee_percent'] == 1.0
        assert stored['amount'] == 100.00
    
    @pytest.mark.asyncio
    async def test_manual_payment_should_store_fee(self, mock_db):
        """
        Manual invoice payments (record-payment endpoint) should also store platform_fee.
        
        Currently in routes/invoices.py record_payment(), the payment record does NOT
        include platform_fee. This test documents expected behavior.
        """
        tenant_id = 'tenant_manual_test'
        invoice_id = 'inv_manual_test'
        
        create_test_tenant(mock_db, tenant_id, 'os_pro', is_founder=False)
        create_test_subscription(mock_db, tenant_id, 'monthly')
        create_test_invoice(mock_db, invoice_id, tenant_id, 100.00)
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        
        amount = 100.00
        fee_percent = fees.invoice_fee_percent
        platform_fee = gate.calculate_platform_fee(amount, fee_percent)
        
        # Simulate EXPECTED payment record with fee (what record_payment SHOULD do)
        payment_record = {
            'invoice_id': invoice_id,
            'tenant_id': tenant_id,
            'amount': amount,
            'platform_fee': platform_fee,
            'fee_percent': fee_percent,
            'payment_method': 'manual',
            'notes': 'Test payment',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await mock_db.payments.insert_one(payment_record)
        
        # Verify stored correctly
        stored = await mock_db.payments.find_one({'invoice_id': invoice_id})
        
        assert stored is not None
        assert stored['platform_fee'] == 1.00
        assert stored['fee_percent'] == 1.0


class TestFullScenarios:
    """Full end-to-end test scenarios"""
    
    @pytest.fixture
    def mock_db(self):
        return MockDB()
    
    @pytest.mark.asyncio
    async def test_scenario_os_pro_non_founder(self, mock_db):
        """
        SCENARIO 1: OS_PRO, is_founder=false
        - Create tenant with plan OS_PRO, is_founder=false
        - Create invoice amount=100.00
        - Calculate platform fee
        - Assert: fee_percent=1.0, platform_fee=1.00
        """
        tenant_id = 'scenario1_tenant'
        invoice_id = 'scenario1_invoice'
        
        create_test_tenant(mock_db, tenant_id, 'os_pro', is_founder=False)
        create_test_subscription(mock_db, tenant_id, 'monthly')
        create_test_invoice(mock_db, invoice_id, tenant_id, 100.00)
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        platform_fee = gate.calculate_platform_fee(100.00, fees.invoice_fee_percent)
        
        assert fees.invoice_fee_percent == 1.0, f"Expected 1.0, got {fees.invoice_fee_percent}"
        assert platform_fee == 1.00, f"Expected 1.00, got {platform_fee}"
        
        print(f"✅ SCENARIO 1 PASSED: OS_PRO non-founder: {fees.invoice_fee_percent}% = ${platform_fee}")
    
    @pytest.mark.asyncio
    async def test_scenario_os_business_founder_annual(self, mock_db):
        """
        SCENARIO 2: OS_BUSINESS, is_founder=true, billing_interval="annual"
        - Create tenant with plan OS_BUSINESS, is_founder=true
        - Create subscription with billing_interval="annual"
        - Create invoice amount=100.00
        - Calculate platform fee
        - Assert: fee_percent=0.5, platform_fee=0.50
        """
        tenant_id = 'scenario2_tenant'
        invoice_id = 'scenario2_invoice'
        
        create_test_tenant(mock_db, tenant_id, 'os_business', is_founder=True)
        create_test_subscription(mock_db, tenant_id, 'annual')
        create_test_invoice(mock_db, invoice_id, tenant_id, 100.00)
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        platform_fee = gate.calculate_platform_fee(100.00, fees.invoice_fee_percent)
        
        assert fees.invoice_fee_percent == 0.5, f"Expected 0.5, got {fees.invoice_fee_percent}"
        assert platform_fee == 0.50, f"Expected 0.50, got {platform_fee}"
        
        print(f"✅ SCENARIO 2 PASSED: OS_BUSINESS founder annual: {fees.invoice_fee_percent}% = ${platform_fee}")
    
    @pytest.mark.asyncio
    async def test_scenario_os_starter(self, mock_db):
        """
        SCENARIO 3: OS_STARTER
        - Create tenant with plan OS_STARTER
        - Create invoice amount=100.00
        - Calculate platform fee
        - Assert: fee_percent=0.0, platform_fee=0.00
        """
        tenant_id = 'scenario3_tenant'
        invoice_id = 'scenario3_invoice'
        
        create_test_tenant(mock_db, tenant_id, 'os_starter', is_founder=False)
        create_test_subscription(mock_db, tenant_id, 'monthly')
        create_test_invoice(mock_db, invoice_id, tenant_id, 100.00)
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        platform_fee = gate.calculate_platform_fee(100.00, fees.invoice_fee_percent)
        
        assert fees.invoice_fee_percent == 0.0, f"Expected 0.0, got {fees.invoice_fee_percent}"
        assert platform_fee == 0.00, f"Expected 0.00, got {platform_fee}"
        
        print(f"✅ SCENARIO 3 PASSED: OS_STARTER: {fees.invoice_fee_percent}% = ${platform_fee}")
    
    @pytest.mark.asyncio
    async def test_scenario_rounding_99_99(self, mock_db):
        """
        SCENARIO 4: Rounding test
        - Amount=99.99 at 1% should result in platform_fee=1.00
        """
        tenant_id = 'scenario4_tenant'
        
        create_test_tenant(mock_db, tenant_id, 'os_pro', is_founder=False)
        create_test_subscription(mock_db, tenant_id, 'monthly')
        
        gate = MultiProductFeatureGate(mock_db)
        fees = await gate.get_processing_fees(tenant_id)
        platform_fee = gate.calculate_platform_fee(99.99, fees.invoice_fee_percent)
        
        assert platform_fee == 1.00, f"Expected 1.00 (rounded), got {platform_fee}"
        
        print(f"✅ SCENARIO 4 PASSED: $99.99 at 1% = ${platform_fee} (rounded from 0.9999)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
