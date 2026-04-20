"""
Apparel pricing tests.
Covers:
 - POST /api/pricing/calculate (category=apparel): shop-table + cost-plus methods, tiers,
   brand switch, placement, product switch, add-ons, setup, rush, manual override
 - GET /api/job-tickets/schema/apparel (30+ foundation-driven fields)
 - GET /api/pricing/defaults (apparel block)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:3000").rstrip("/")
API = f"{BASE_URL}/api"

EMAIL = "signguypa@gmail.com"
PASSWORD = "Billnel323"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Login failed {r.status_code}: {r.text[:200]}")
    return r.json().get("access_token") or r.json().get("token")


@pytest.fixture(scope="session")
def headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def base(overrides=None, quantity=24):
    pd = {
        "apparel_product_type": "short_sleeve_tee",
        "apparel_brand_style_key": "blank_ss_gildan_5000",
        "apparel_decoration_method": "htv",
        "apparel_placement_set": "front",
        "apparel_num_colors": 1,
        "apparel_stitch_count": 0,
        "apparel_plus_size_count": 0,
        "apparel_custom_name_number": False,
        "apparel_custom_name_number_count": 0,
        "apparel_specialty_finish": False,
        "apparel_two_tone_hat_finish": False,
        "apparel_leather_patch": False,
        "apparel_bag_and_fold": False,
        "artwork_ready": True,
        "artwork_needed": False,
        "design_complexity": "simple",
        "rush_order": False,
        "apparel_manual_quote_override": 0,
    }
    if overrides:
        pd.update(overrides)
    return {"category": "apparel", "pricing_data": pd, "quantity": quantity}


def calc(headers, overrides=None, quantity=24):
    r = requests.post(f"{API}/pricing/calculate", json=base(overrides, quantity), headers=headers, timeout=30)
    assert r.status_code == 200, f"calc failed {r.status_code}: {r.text[:300]}"
    return r.json()


# ---------------- Breakdown & schema ----------------
class TestApparelBreakdown:
    def test_baseline_breakdown_fields(self, headers):
        data = calc(headers)
        br = data.get("breakdown", data)
        for key in [
            "product_type", "brand_style_key", "decoration_method", "placement_set",
            "quantity_tier", "per_piece_sell", "total_blank_cost",
            "total_decoration_material_cost", "setup_fee",
            "rush_percent_applied", "manual_quote_override",
        ]:
            assert key in br, f"missing {key} in breakdown; got keys={list(br.keys())[:30]}"
        assert br["product_type"] == "short_sleeve_tee"
        assert br["decoration_method"] == "htv"
        assert br["placement_set"] == "front"
        assert br["quantity_tier"] == "5_24"
        assert br.get("baseline_source") == "shop_table:htv"
        assert abs(br["per_piece_sell"] - 10.50) < 0.01
        assert abs(br["total_blank_cost"] - 78.00) < 0.01


# ---------------- Quantity tiers ----------------
@pytest.mark.parametrize("qty,tier", [(1, "1_4"), (24, "5_24"), (50, "50_99"), (100, "100_plus"), (150, "100_plus")])
def test_quantity_tier(headers, qty, tier):
    data = calc(headers, quantity=qty)
    br = data.get("breakdown", data)
    assert br["quantity_tier"] == tier


# ---------------- Brand switch ----------------
class TestBrandSwitch:
    def test_gildan_vs_bella(self, headers):
        g = calc(headers, {"apparel_brand_style_key": "blank_ss_gildan_5000"})["breakdown"]
        b = calc(headers, {"apparel_brand_style_key": "blank_ss_bella_3001"})["breakdown"]
        assert g["per_piece_sell"] != b["per_piece_sell"]
        assert g["total_blank_cost"] != b["total_blank_cost"]
        assert abs(b["per_piece_sell"] - 12.50) < 0.01


# ---------------- Placement ----------------
class TestPlacement:
    def test_front_vs_back_vs_fb(self, headers):
        f = calc(headers, {"apparel_placement_set": "front"})["breakdown"]["per_piece_sell"]
        b = calc(headers, {"apparel_placement_set": "back"})["breakdown"]["per_piece_sell"]
        fb = calc(headers, {"apparel_placement_set": "front_back"})["breakdown"]["per_piece_sell"]
        assert f == 10.50 and b == 12.00 and fb == 15.00

    def test_hat_placements(self, headers):
        d = calc(headers, {
            "apparel_product_type": "hat_premium",
            "apparel_brand_style_key": "blank_hat_premium",
            "apparel_placement_set": "side_back",
        })["breakdown"]
        assert abs(d["per_piece_sell"] - 14.00) < 0.01


# ---------------- Product switch: hoodie & hat ----------------
class TestProductSwitch:
    def test_hoodie(self, headers):
        d = calc(headers, {
            "apparel_product_type": "hoodie",
            "apparel_brand_style_key": "blank_hd_gildan_18500",
        }, quantity=10)["breakdown"]
        assert d["product_type"] == "hoodie"
        assert abs(d["per_piece_sell"] - 21.50) < 0.01
        assert abs(d["total_blank_cost"] - 130.00) < 0.01

    def test_hat_standard(self, headers):
        d = calc(headers, {
            "apparel_product_type": "hat_standard",
            "apparel_brand_style_key": "blank_hat_standard",
        })["breakdown"]
        assert abs(d["per_piece_sell"] - 11.00) < 0.01


# ---------------- Add-ons ----------------
class TestAddOns:
    def test_plus_size(self, headers):
        d = calc(headers, {"apparel_plus_size_count": 5})["breakdown"]
        assert abs(d["plus_size_cost"] - 10.00) < 0.01  # 5 * $2

    def test_custom_names_garment(self, headers):
        d = calc(headers, {"apparel_custom_name_number": True, "apparel_custom_name_number_count": 10})["breakdown"]
        assert abs(d["custom_name_number_cost"] - 40.00) < 0.01  # 10 * $4

    def test_custom_names_hat(self, headers):
        d = calc(headers, {
            "apparel_product_type": "hat_standard",
            "apparel_brand_style_key": "blank_hat_standard",
            "apparel_custom_name_number": True,
            "apparel_custom_name_number_count": 10,
        })["breakdown"]
        assert abs(d["custom_name_number_cost"] - 30.00) < 0.01  # 10 * $3

    def test_specialty_finish_garment(self, headers):
        d = calc(headers, {"apparel_specialty_finish": True})["breakdown"]
        assert abs(d["specialty_cost"] - 48.00) < 0.01  # $2 * 24

    def test_two_tone_hat(self, headers):
        d = calc(headers, {
            "apparel_product_type": "hat_premium",
            "apparel_brand_style_key": "blank_hat_premium",
            "apparel_two_tone_hat_finish": True,
        })["breakdown"]
        assert abs(d["two_tone_cost"] - 36.00) < 0.01  # $1.50 * 24

    def test_leather_patch(self, headers):
        d = calc(headers, {
            "apparel_product_type": "hat_premium",
            "apparel_brand_style_key": "blank_hat_premium",
            "apparel_leather_patch": True,
        })["breakdown"]
        assert abs(d["patch_cost"] - 60.00) < 0.01  # $2.50 * 24

    def test_bag_and_fold(self, headers):
        d = calc(headers, {"apparel_bag_and_fold": True})["breakdown"]
        assert abs(d["bag_fold_cost"] - 24.00) < 0.01  # $1 * 24


# ---------------- Setup ----------------
class TestSetup:
    def test_artwork_needed_complex(self, headers):
        d = calc(headers, {
            "artwork_ready": False,
            "artwork_needed": True,
            "design_complexity": "complex",
        })["breakdown"]
        assert abs(d["setup_fee"] - 25.00) < 0.01


# ---------------- Rush ----------------
class TestRush:
    def test_rush_applied(self, headers):
        base_resp = calc(headers)
        base_sell = base_resp.get("selling_price")
        rush_resp = calc(headers, {"rush_order": True})
        rush_sell = rush_resp.get("selling_price")
        assert rush_resp["breakdown"]["rush_percent_applied"] in (17.5, 0.175)
        assert rush_sell > base_sell


# ---------------- Manual override ----------------
class TestManualOverride:
    def test_override(self, headers):
        resp = calc(headers, {"apparel_manual_quote_override": 500})
        sell = resp.get("selling_price")
        assert abs(sell - 500.00) < 0.5
        assert resp["breakdown"].get("manual_quote_override") == 500


# ---------------- Cost-plus methods ----------------
class TestCostPlusMethods:
    def test_embroidery(self, headers):
        d = calc(headers, {
            "apparel_product_type": "polo",
            "apparel_brand_style_key": "blank_po_gildan_8800",
            "apparel_decoration_method": "embroidery",
            "apparel_stitch_count": 6000,
        })["breakdown"]
        assert d["baseline_source"] == "cost_plus:embroidery"
        assert d["total_decoration_material_cost"] > 0

    def test_dtg(self, headers):
        d = calc(headers, {
            "apparel_product_type": "hoodie",
            "apparel_brand_style_key": "blank_hd_gildan_18500",
            "apparel_decoration_method": "dtg",
        }, quantity=12)["breakdown"]
        assert d["baseline_source"] == "cost_plus:dtg"

    def test_direct_screen_print(self, headers):
        d = calc(headers, {
            "apparel_decoration_method": "direct_screen_print",
            "apparel_num_colors": 3,
        }, quantity=50)["breakdown"]
        assert d["baseline_source"] == "cost_plus:direct_screen_print"


# ---------------- Shop-table methods ----------------
class TestShopTableMethods:
    def test_htv(self, headers):
        d = calc(headers, {"apparel_decoration_method": "htv"})["breakdown"]
        assert d["baseline_source"] == "shop_table:htv"

    def test_screen_print_transfer(self, headers):
        d = calc(headers, {"apparel_decoration_method": "screen_print_transfer"})["breakdown"]
        assert d["baseline_source"] == "shop_table:screen_print_transfer"

    def test_dtf_transfer(self, headers):
        d = calc(headers, {"apparel_decoration_method": "dtf_transfer"})["breakdown"]
        assert d["baseline_source"] == "shop_table:dtf_transfer"


# ---------------- Schema & defaults ----------------
class TestSchemaAndDefaults:
    def test_schema_fields(self, headers):
        r = requests.get(f"{API}/job-tickets/schema/apparel", headers=headers, timeout=20)
        assert r.status_code == 200
        body = r.json()
        fields = body.get("fields", body if isinstance(body, list) else [])
        names = set()
        if isinstance(fields, list):
            for f in fields:
                if isinstance(f, dict):
                    names.add(f.get("name") or f.get("field") or f.get("key"))
                else:
                    names.add(f)
        elif isinstance(fields, dict):
            names = set(fields.keys())
        required = {
            "apparel_product_type", "apparel_brand_style_key", "apparel_placement_set",
            "apparel_decoration_method", "apparel_plus_size_count",
            "apparel_custom_name_number", "apparel_specialty_finish",
            "apparel_two_tone_hat_finish", "apparel_leather_patch",
            "apparel_bag_and_fold", "artwork_ready", "artwork_needed",
            "design_complexity", "rush_order", "apparel_rush_percent",
            "apparel_manual_quote_override",
        }
        missing = required - names
        assert not missing, f"missing schema fields: {missing}"
        assert len(names) >= 30, f"expected >=30 fields, got {len(names)}"

    def test_defaults_apparel_block(self, headers):
        r = requests.get(f"{API}/pricing/defaults", headers=headers, timeout=20)
        assert r.status_code == 200
        body = r.json()
        cat = body.get("category_defaults", body).get("apparel", {})
        assert cat, "no apparel block in defaults"
        for key in [
            "shop_pricing_table", "available_product_types", "available_brand_styles",
            "placement_sets", "available_decoration_methods", "method_config",
            "quantity_tiers",
        ]:
            assert key in cat, f"missing {key} in apparel defaults; keys={list(cat.keys())}"
