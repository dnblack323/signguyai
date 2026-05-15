"""Regression tests for platform fee math + webstore owner-connect endpoints.

Run:
    cd /app/backend && python -m pytest tests/test_fees_and_owner_connect.py -v
"""

from services.stripe_service import (
    calculate_platform_fee_cents,
    get_platform_fee_config,
    WEBSTORE_SURCHARGE_PERCENT,
)


# ── Platform fee math ─────────────────────────────────────────────────────────

class TestPlatformFeeMath:
    def test_invoice_5_dollar(self):
        # $5.00 → 2.2% + $0.20 = $0.11 + $0.20 = $0.31 (31c)
        assert calculate_platform_fee_cents("founders_edition", 500, is_webstore=False) == 31

    def test_invoice_10_dollar(self):
        # $10.00 → 22c + 20c = 42c
        assert calculate_platform_fee_cents("founders_edition", 1000, is_webstore=False) == 42

    def test_invoice_100_dollar(self):
        # $100.00 → $2.20 + $0.20 = $2.40
        assert calculate_platform_fee_cents("founders_edition", 10000, is_webstore=False) == 240

    def test_webstore_50_dollar(self):
        # $50.00 webstore → 4.2% + $0.20 = $2.10 + $0.20 = $2.30
        assert calculate_platform_fee_cents("founders_edition", 5000, is_webstore=True) == 230

    def test_webstore_500_dollar(self):
        # $500.00 webstore → $21.00 + $0.20 = $21.20
        assert calculate_platform_fee_cents("founders_edition", 50000, is_webstore=True) == 2120

    def test_micro_payment_does_not_overflow(self):
        # 30c invoice → 2.2%*30c = 0.66c → rounds to 1c + 20c = 21c (< 30c, ok)
        fee = calculate_platform_fee_cents("founders_edition", 30, is_webstore=False)
        assert fee == 21

    def test_micro_payment_floor(self):
        # 5c invoice → 2.2%*5 = 0c + 20c = 20c which would exceed; clamp to 4c
        fee = calculate_platform_fee_cents("founders_edition", 5, is_webstore=False)
        assert fee == 4  # amount - 1 cent floor

    def test_unknown_tier_falls_back_to_founders(self):
        # Should use the founders config for unknown tiers (post-launch safety)
        assert calculate_platform_fee_cents("unknown_tier_xyz", 1000, is_webstore=False) == 42

    def test_webstore_surcharge_constant_is_2pct(self):
        assert WEBSTORE_SURCHARGE_PERCENT == 0.020

    def test_all_tiers_use_same_base_for_now(self):
        # All four legacy tiers should resolve to the same base since the
        # phase-launch positions everyone as Founders.
        for tier in ("starter", "pro", "business", "founders_edition"):
            cfg = get_platform_fee_config(tier)
            assert cfg["percent"] == 0.022
            assert cfg["flat_cents"] == 20
