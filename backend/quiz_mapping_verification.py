"""
ONE-TIME PRICING QUIZ MAPPING VERIFICATION TEST

This script performs a DRY RUN verification of the pricing quiz → Pricing Foundation mapping logic.
It generates sample quiz answers, runs the mapping conversion, and produces a detailed report
showing what each question would contribute to the Pricing Foundation.

SAFETY: This is a READ-ONLY test. No actual pricing settings are modified.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "signtist")

# ============================================================================
# QUIZ QUESTION DEFINITIONS (mirrored from PricingSetupQuiz.js SECTIONS)
# ============================================================================

QUIZ_SECTIONS = [
    {
        "key": "shop_basics",
        "title": "Shop Basics",
        "questions": [
            {"key": "design_hourly_rate", "label": "Design hourly rate", "unit": "$/hr", "default": 85},
            {"key": "production_hourly_rate", "label": "Production hourly rate", "unit": "$/hr", "default": 28},
            {"key": "install_hourly_rate", "label": "Install hourly rate", "unit": "$/hr", "default": 95},
            {"key": "target_profit_margin_percent", "label": "Target profit margin", "unit": "%", "default": 40},
            {"key": "minimum_order", "label": "Minimum order amount", "unit": "$", "default": 50},
            {"key": "deposit_required", "label": "Deposit required?", "type": "bool", "default": True},
            {"key": "deposit_percentage", "label": "Deposit %", "unit": "%", "default": 50},
        ],
    },
    {
        "key": "banners",
        "title": "Banners",
        "questions": [
            {"key": "banner_2x4", "label": "2ft × 4ft banner price", "unit": "$", "default": 65, "sqft": 8},
            {"key": "banner_3x6", "label": "3ft × 6ft banner price", "unit": "$", "default": 145, "sqft": 18},
            {"key": "banner_4x8", "label": "4ft × 8ft banner price", "unit": "$", "default": 260, "sqft": 32},
            {"key": "banner_finishing_included", "label": "Hems/grommets included?", "type": "bool", "default": True},
        ],
    },
    {
        "key": "yard_signs",
        "title": "Yard Signs / Coroplast",
        "questions": [
            {"key": "yard_qty_1", "label": "Price for 1 yard sign", "unit": "$", "default": 28},
            {"key": "yard_qty_10", "label": "Price for 10 yard signs", "unit": "$", "default": 18},
            {"key": "yard_qty_25", "label": "Price for 25 yard signs", "unit": "$", "default": 14},
            {"key": "yard_qty_50", "label": "Price for 50 yard signs", "unit": "$", "default": 11},
            {"key": "yard_stakes_included", "label": "Stakes included?", "type": "bool", "default": False},
        ],
    },
    {
        "key": "rigid_signs",
        "title": "Rigid Signs",
        "questions": [
            {"key": "rigid_coroplast_4x4", "label": "4ft × 4ft coroplast", "unit": "$", "default": 175, "sqft": 16},
            {"key": "rigid_coroplast_4x8", "label": "4ft × 8ft coroplast", "unit": "$", "default": 320, "sqft": 32},
            {"key": "rigid_acm_4x8", "label": "4ft × 8ft ACM", "unit": "$", "default": 650, "sqft": 32},
            {"key": "rigid_pvc_4x8", "label": "4ft × 8ft PVC", "unit": "$", "default": 550, "sqft": 32},
        ],
    },
    {
        "key": "cut_vinyl",
        "title": "Cut Vinyl",
        "questions": [
            {"key": "cv_12x24_one_color", "label": "12in × 24in one-color", "unit": "$", "default": 22, "sqft": 2},
            {"key": "cv_24x36_one_color", "label": "24in × 36in one-color", "unit": "$", "default": 55, "sqft": 6},
            {"key": "cv_24x36_two_color", "label": "24in × 36in two-color", "unit": "$", "default": 85, "sqft": 6},
            {"key": "cv_minimum_charge", "label": "Minimum vinyl decal charge", "unit": "$", "default": 20},
        ],
    },
    {
        "key": "digital_print",
        "title": "Digital Print",
        "questions": [
            {"key": "dp_24x36_poster", "label": "24in × 36in poster", "unit": "$", "default": 38, "sqft": 6},
            {"key": "dp_24x36_adhesive", "label": "24in × 36in adhesive", "unit": "$", "default": 62, "sqft": 6},
            {"key": "dp_24x36_adhesive_lam", "label": "24in × 36in laminated adhesive", "unit": "$", "default": 88, "sqft": 6},
            {"key": "dp_4x8_panel", "label": "4ft × 8ft printed panel", "unit": "$", "default": 350, "sqft": 32},
        ],
    },
    {
        "key": "vehicle_graphics",
        "title": "Vehicle Graphics",
        "questions": [
            {"key": "vg_door_lettering", "label": "Basic pickup door lettering", "unit": "$", "default": 180},
            {"key": "vg_spot_van", "label": "Spot graphics on a van", "unit": "$", "default": 450},
            {"key": "vg_partial_wrap", "label": "Partial wrap on cargo van", "unit": "$", "default": 1800},
            {"key": "vg_full_wrap", "label": "Full wrap on cargo van", "unit": "$", "default": 3800},
            {"key": "vg_print_sqft_rate", "label": "Printed wrap sell rate", "unit": "$/sqft", "default": 18},
            {"key": "vg_color_change_sqft", "label": "Color-change wrap rate", "unit": "$/sqft", "default": 22},
        ],
    },
    {
        "key": "apparel",
        "title": "Apparel",
        "questions": [
            {"key": "ap_tee_qty_12_one_side", "label": "12 × one-sided tees (each)", "unit": "$", "default": 14},
            {"key": "ap_tee_qty_24_one_side", "label": "24 × one-sided tees (each)", "unit": "$", "default": 11},
            {"key": "ap_tee_qty_12_two_side", "label": "12 × front-and-back tees", "unit": "$", "default": 19},
            {"key": "ap_blank_cost", "label": "Average blank shirt cost", "unit": "$", "default": 4.5},
            {"key": "ap_decoration_cost", "label": "Average transfer cost", "unit": "$", "default": 2.25},
            {"key": "ap_hoodie_each", "label": "Hoodie price (per piece)", "unit": "$", "default": 35},
        ],
    },
    {
        "key": "services",
        "title": "Services",
        "questions": [
            {"key": "svc_design_rate", "label": "Design rate", "unit": "$/hr", "default": 85},
            {"key": "svc_production_rate", "label": "Production rate", "unit": "$/hr", "default": 28},
            {"key": "svc_install_rate", "label": "Install rate", "unit": "$/hr", "default": 95},
            {"key": "svc_min_design", "label": "Minimum design charge", "unit": "$", "default": 45},
            {"key": "svc_min_install", "label": "Minimum install charge", "unit": "$", "default": 125},
        ],
    },
    {
        "key": "promotional_custom",
        "title": "Promotional / Custom",
        "questions": [
            {"key": "pc_vendor_markup_percent", "label": "Markup on outsourced items", "unit": "%", "default": 50},
            {"key": "pc_min_setup_fee", "label": "Minimum setup fee", "unit": "$", "default": 25},
            {"key": "pc_min_order", "label": "Minimum order amount", "unit": "$", "default": 75},
        ],
    },
]

# ============================================================================
# MAPPING RULES (mirrored from PricingSetupQuiz.js buildSuggestions())
# ============================================================================

# Maps quiz answer keys → Pricing Foundation paths
# Format: { "answer_key": { "target_path": [...], "conversion_rule": "..." } }
ANSWER_TO_FOUNDATION_MAP = {
    # Shop Basics
    "design_hourly_rate": {
        "target_path": ["design_hourly_rate"],
        "conversion_rule": "Direct copy (hourly rate)",
    },
    "production_hourly_rate": {
        "target_path": ["production_hourly_rate"],
        "conversion_rule": "Direct copy (hourly rate)",
    },
    "install_hourly_rate": {
        "target_path": ["install_hourly_rate"],
        "conversion_rule": "Direct copy (hourly rate)",
    },
    "target_profit_margin_percent": {
        "target_path": ["target_profit_margin_percent"],
        "conversion_rule": "Direct copy (percentage)",
    },
    "minimum_order": {
        "target_path": ["minimum_order"],
        "conversion_rule": "Direct copy (dollar amount)",
    },
    "deposit_percentage": {
        "target_path": ["deposit_percentage"],
        "conversion_rule": "Direct copy (percentage, only if deposit_required=true)",
    },
    # Banners
    "banner_2x4": {
        "target_path": ["category_defaults", "banners", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 8 sqft → avg with banner_3x6, banner_4x8 → $/sqft",
    },
    "banner_3x6": {
        "target_path": ["category_defaults", "banners", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 18 sqft → avg with banner_2x4, banner_4x8 → $/sqft",
    },
    "banner_4x8": {
        "target_path": ["category_defaults", "banners", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 32 sqft → avg with banner_2x4, banner_3x6 → $/sqft",
    },
    # Yard signs
    "yard_qty_1": {
        "target_path": ["category_defaults", "rigid_signs", "default_minimum_sell_price"],
        "conversion_rule": "Single qty floor → minimum sell price / item",
    },
    "yard_qty_10": {
        "target_path": ["category_defaults", "rigid_signs", "quantity_breaks", "qty_10_percent"],
        "conversion_rule": "(1 - qty_10 / qty_1) × 100 → discount %",
    },
    "yard_qty_25": {
        "target_path": ["category_defaults", "rigid_signs", "sell_rate_defaults", "yard_sign_rate"],
        "conversion_rule": "Price ÷ 3 sqft (18×24in) → $/sqft",
    },
    "yard_qty_50": {
        "target_path": ["category_defaults", "rigid_signs", "sell_rate_defaults", "yard_sign_rate"],
        "conversion_rule": "Price ÷ 3 sqft (fallback if qty_25 missing)",
    },
    # Rigid signs
    "rigid_coroplast_4x4": {
        "target_path": ["category_defaults", "rigid_signs", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 16 sqft → avg with other rigid answers → $/sqft",
    },
    "rigid_coroplast_4x8": {
        "target_path": ["category_defaults", "rigid_signs", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 32 sqft → avg with other rigid answers → $/sqft",
    },
    "rigid_acm_4x8": {
        "target_path": ["category_defaults", "rigid_signs", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 32 sqft → avg with other rigid answers → $/sqft",
    },
    "rigid_pvc_4x8": {
        "target_path": ["category_defaults", "rigid_signs", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 32 sqft → avg with other rigid answers → $/sqft",
    },
    # Cut Vinyl
    "cv_12x24_one_color": {
        "target_path": ["category_defaults", "cut_vinyl", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 2 sqft → avg with other vinyl answers → $/sqft",
    },
    "cv_24x36_one_color": {
        "target_path": ["category_defaults", "cut_vinyl", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 6 sqft → avg with other vinyl answers → $/sqft",
    },
    "cv_24x36_two_color": {
        "target_path": ["category_defaults", "cut_vinyl", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 6 sqft ÷ 2 (two-color) → avg → $/sqft",
    },
    "cv_minimum_charge": {
        "target_path": ["category_defaults", "cut_vinyl", "default_minimum_sell_price"],
        "conversion_rule": "Direct copy (minimum charge)",
    },
    # Digital Print
    "dp_24x36_poster": {
        "target_path": ["category_defaults", "digital_print", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 6 sqft → avg with other print answers → $/sqft",
    },
    "dp_24x36_adhesive": {
        "target_path": ["category_defaults", "digital_print", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 6 sqft → avg with other print answers → $/sqft",
    },
    "dp_24x36_adhesive_lam": {
        "target_path": ["category_defaults", "digital_print", "sell_rate_defaults", "laminate_addon_per_sqft"],
        "conversion_rule": "(lam_price - adhesive_price) ÷ 6 sqft → laminate add-on $/sqft",
    },
    "dp_4x8_panel": {
        "target_path": ["category_defaults", "digital_print", "sell_rate_defaults", "base_rate"],
        "conversion_rule": "Price ÷ 32 sqft → avg with other print answers → $/sqft",
    },
    # Vehicle Graphics
    "vg_print_sqft_rate": {
        "target_path": ["category_defaults", "vehicle_graphics", "sell_rate_defaults", "printed_wrap_per_sqft"],
        "conversion_rule": "Direct copy ($/sqft)",
    },
    "vg_color_change_sqft": {
        "target_path": ["category_defaults", "vehicle_graphics", "sell_rate_defaults", "color_change_per_sqft"],
        "conversion_rule": "Direct copy ($/sqft)",
    },
    "vg_door_lettering": {
        "target_path": ["category_defaults", "vehicle_graphics", "benchmarks", "package_door_lettering"],
        "conversion_rule": "Direct copy (benchmark package price)",
    },
    "vg_spot_van": {
        "target_path": ["category_defaults", "vehicle_graphics", "benchmarks", "package_spot_graphics"],
        "conversion_rule": "Direct copy (benchmark package price)",
    },
    "vg_partial_wrap": {
        "target_path": ["category_defaults", "vehicle_graphics", "benchmarks", "package_partial_wrap"],
        "conversion_rule": "Direct copy (benchmark package price)",
    },
    "vg_full_wrap": {
        "target_path": ["category_defaults", "vehicle_graphics", "benchmarks", "package_full_wrap"],
        "conversion_rule": "Direct copy (benchmark package price)",
    },
    # Apparel
    "ap_tee_qty_12_one_side": {
        "target_path": ["category_defaults", "apparel", "shop_pricing_table", "tee_one_side", "qty_12"],
        "conversion_rule": "Direct copy (tier pricing per piece)",
    },
    "ap_tee_qty_24_one_side": {
        "target_path": ["category_defaults", "apparel", "shop_pricing_table", "tee_one_side", "qty_24"],
        "conversion_rule": "Direct copy (tier pricing per piece)",
    },
    "ap_blank_cost": {
        "target_path": ["category_defaults", "apparel", "default_blank_cost"],
        "conversion_rule": "Direct copy (cost field)",
    },
    "ap_decoration_cost": {
        "target_path": ["category_defaults", "apparel", "default_decoration_cost"],
        "conversion_rule": "Direct copy (cost field)",
    },
    "ap_tee_qty_12_two_side": {
        "target_path": ["category_defaults", "apparel", "shop_pricing_table", "tee_two_side", "qty_12"],
        "conversion_rule": "Direct copy (two-sided tee tier pricing)",
    },
    "ap_hoodie_each": {
        "target_path": ["category_defaults", "apparel", "shop_pricing_table", "hoodie_one_side", "qty_24"],
        "conversion_rule": "Direct copy (hoodie tier pricing)",
    },
    # Services
    "svc_design_rate": {
        "target_path": ["category_defaults", "services", "labor_rate_overrides", "design"],
        "conversion_rule": "Direct copy (hourly rate)",
    },
    "svc_production_rate": {
        "target_path": ["category_defaults", "services", "labor_rate_overrides", "production"],
        "conversion_rule": "Direct copy (hourly rate)",
    },
    "svc_install_rate": {
        "target_path": ["category_defaults", "services", "labor_rate_overrides", "install"],
        "conversion_rule": "Direct copy (hourly rate)",
    },
    "svc_min_design": {
        "target_path": ["category_defaults", "services", "minimums", "design"],
        "conversion_rule": "Direct copy (minimum charge)",
    },
    "svc_min_install": {
        "target_path": ["category_defaults", "services", "minimums", "install"],
        "conversion_rule": "Direct copy (minimum charge)",
    },
    # Promotional / Custom
    "pc_vendor_markup_percent": {
        "target_path": ["category_defaults", "promotional", "default_markup_multiplier"],
        "conversion_rule": "Percent → multiplier: (1 + percent/100)",
    },
    "pc_min_setup_fee": {
        "target_path": ["category_defaults", "promotional", "minimum_setup_fee"],
        "conversion_rule": "Direct copy",
    },
    "pc_min_order": {
        "target_path": ["category_defaults", "promotional", "minimum_charge"],
        "conversion_rule": "Direct copy",
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def generate_sample_answers() -> Dict[str, Any]:
    """Generate reasonable sample quiz answers based on defaults."""
    answers = {}
    for section in QUIZ_SECTIONS:
        for q in section["questions"]:
            key = q["key"]
            if q.get("type") == "bool":
                answers[key] = q["default"]
            else:
                # Add some variance to defaults (±15%)
                import random
                base = q["default"]
                variance = random.uniform(0.85, 1.15)
                answers[key] = round(base * variance, 2)
    return answers


def get_path_value(obj: Dict, path: List[str]) -> Any:
    """Navigate nested dict path and return value."""
    current = obj
    for key in path:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current


def set_path_value(obj: Dict, path: List[str], value: Any) -> Dict:
    """Set value at nested dict path (creates intermediate dicts)."""
    import copy
    result = copy.deepcopy(obj)
    current = result
    for i, key in enumerate(path[:-1]):
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    current[path[-1]] = value
    return result


def apply_conversion_logic(answer_key: str, answer_value: Any, all_answers: Dict) -> Optional[Any]:
    """
    Apply quiz-to-foundation conversion logic for a specific answer.
    
    Returns the calculated/converted value that would be written to Pricing Foundation.
    """
    if answer_value is None:
        return None
    
    # Banners - average sqft rate
    if answer_key in ["banner_2x4", "banner_3x6", "banner_4x8"]:
        b2x4 = all_answers.get("banner_2x4")
        b3x6 = all_answers.get("banner_3x6")
        b4x8 = all_answers.get("banner_4x8")
        rates = []
        if b2x4: rates.append(b2x4 / 8)
        if b3x6: rates.append(b3x6 / 18)
        if b4x8: rates.append(b4x8 / 32)
        return round(sum(rates) / len(rates), 2) if rates else None
    
    # Yard sign sell rate
    if answer_key in ["yard_qty_25", "yard_qty_10", "yard_qty_50"]:
        y25 = all_answers.get("yard_qty_25")
        y10 = all_answers.get("yard_qty_10")
        y50 = all_answers.get("yard_qty_50")
        mid = y25 or y10 or y50
        return round(mid / 3, 2) if mid else None  # 18×24 = 3 sqft
    
    # Yard sign qty discount
    if answer_key == "yard_qty_10":
        y1 = all_answers.get("yard_qty_1")
        y10 = all_answers.get("yard_qty_10")
        if y1 and y10 and y10 < y1:
            return max(0, min(50, round((1 - y10 / y1) * 100)))
        return None
    
    # Rigid signs - average sqft rate
    if answer_key in ["rigid_coroplast_4x4", "rigid_coroplast_4x8", "rigid_acm_4x8", "rigid_pvc_4x8"]:
        rc44 = all_answers.get("rigid_coroplast_4x4")
        rc48 = all_answers.get("rigid_coroplast_4x8")
        ra48 = all_answers.get("rigid_acm_4x8")
        rp48 = all_answers.get("rigid_pvc_4x8")
        rates = []
        if rc44: rates.append(rc44 / 16)
        if rc48: rates.append(rc48 / 32)
        if ra48: rates.append(ra48 / 32)
        if rp48: rates.append(rp48 / 32)
        return round(sum(rates) / len(rates), 2) if rates else None
    
    # Cut vinyl - average sqft rate
    if answer_key in ["cv_12x24_one_color", "cv_24x36_one_color", "cv_24x36_two_color"]:
        cv1 = all_answers.get("cv_12x24_one_color")
        cv2 = all_answers.get("cv_24x36_one_color")
        cv2c = all_answers.get("cv_24x36_two_color")
        rates = []
        if cv1: rates.append(cv1 / 2)  # 12×24 = 2 sqft
        if cv2: rates.append(cv2 / 6)  # 24×36 = 6 sqft
        if cv2c: rates.append(cv2c / 6 / 2)  # two-color = half per layer
        return round(sum(rates) / len(rates), 2) if rates else None
    
    # Digital print - average sqft rate
    if answer_key in ["dp_24x36_poster", "dp_24x36_adhesive", "dp_4x8_panel"]:
        dp_p = all_answers.get("dp_24x36_poster")
        dp_a = all_answers.get("dp_24x36_adhesive")
        dp_pn = all_answers.get("dp_4x8_panel")
        rates = []
        if dp_p: rates.append(dp_p / 6)
        if dp_a: rates.append(dp_a / 6)
        if dp_pn: rates.append(dp_pn / 32)
        return round(sum(rates) / len(rates), 2) if rates else None
    
    # Laminate add-on
    if answer_key == "dp_24x36_adhesive_lam":
        lam = all_answers.get("dp_24x36_adhesive_lam")
        adh = all_answers.get("dp_24x36_adhesive")
        if lam and adh and lam > adh:
            return round((lam - adh) / 6, 2)
        return None
    
    # Promotional markup percent → multiplier
    if answer_key == "pc_vendor_markup_percent":
        return round(1 + answer_value / 100, 2)
    
    # Deposit percentage - only applies if deposit_required is true
    if answer_key == "deposit_percentage":
        if not all_answers.get("deposit_required"):
            return None
        return answer_value
    
    # Default: direct copy
    return answer_value


def check_calculator_usage(path: List[str]) -> str:
    """
    Check if the calculator actually uses this field.
    
    Returns 'used' | 'stored_not_used' | 'benchmark_only' | 'unknown'
    
    Based on manual code review of:
    - /app/backend/models/pricing.py (default values)
    - /app/backend/routes/pricing.py (calculation logic)
    - /app/backend/routes/job_tickets.py (order calculations)
    """
    # Actively used in cost-plus calculations
    ACTIVELY_USED = [
        ["design_hourly_rate"],
        ["production_hourly_rate"],
        ["install_hourly_rate"],
        ["target_profit_margin_percent"],
        ["minimum_order"],
        ["deposit_percentage"],  # Used in deposit calculation
        ["category_defaults", "banners", "sell_rate_defaults", "base_rate"],
        ["category_defaults", "rigid_signs", "sell_rate_defaults", "base_rate"],
        ["category_defaults", "rigid_signs", "sell_rate_defaults", "yard_sign_rate"],
        ["category_defaults", "cut_vinyl", "sell_rate_defaults", "base_rate"],
        ["category_defaults", "digital_print", "sell_rate_defaults", "base_rate"],
        ["category_defaults", "digital_print", "sell_rate_defaults", "laminate_addon_per_sqft"],
        ["category_defaults", "vehicle_graphics", "sell_rate_defaults", "printed_wrap_per_sqft"],
        ["category_defaults", "vehicle_graphics", "sell_rate_defaults", "color_change_per_sqft"],
        ["category_defaults", "apparel", "default_blank_cost"],
        ["category_defaults", "apparel", "default_decoration_cost"],
        ["category_defaults", "services", "labor_rate_overrides", "design"],
        ["category_defaults", "services", "labor_rate_overrides", "production"],
        ["category_defaults", "services", "labor_rate_overrides", "install"],
        ["category_defaults", "promotional", "default_markup_multiplier"],
    ]
    
    # Benchmark pricing (used for comparison, not in cost-plus math)
    BENCHMARK_ONLY = [
        ["category_defaults", "vehicle_graphics", "benchmarks", "package_door_lettering"],
        ["category_defaults", "vehicle_graphics", "benchmarks", "package_spot_graphics"],
        ["category_defaults", "vehicle_graphics", "benchmarks", "package_partial_wrap"],
        ["category_defaults", "vehicle_graphics", "benchmarks", "package_full_wrap"],
        ["category_defaults", "apparel", "shop_pricing_table"],
    ]
    
    # Stored but not currently used in calculations (floor/minimum values)
    STORED_NOT_USED = [
        ["category_defaults", "banners", "default_minimum_sell_price"],
        ["category_defaults", "rigid_signs", "default_minimum_sell_price"],
        ["category_defaults", "rigid_signs", "quantity_breaks", "qty_10_percent"],
        ["category_defaults", "rigid_signs", "quantity_breaks", "qty_25_percent"],
        ["category_defaults", "cut_vinyl", "default_minimum_sell_price"],
        ["category_defaults", "services", "minimums", "design"],
        ["category_defaults", "services", "minimums", "install"],
        ["category_defaults", "promotional", "minimum_setup_fee"],
        ["category_defaults", "promotional", "minimum_charge"],
    ]
    
    # Check exact match for actively used
    if path in ACTIVELY_USED:
        return "used"
    
    # Check exact match for stored but not used
    if path in STORED_NOT_USED:
        return "stored_not_used"
    
    # Check if path starts with benchmark path
    for benchmark_path in BENCHMARK_ONLY:
        if len(path) >= len(benchmark_path) and path[:len(benchmark_path)] == benchmark_path:
            return "benchmark_only"
    
    return "unknown"


# ============================================================================
# MAIN VERIFICATION LOGIC
# ============================================================================


async def run_verification(tenant_id: str):
    """
    Main verification function.
    
    Performs a DRY RUN and generates a comprehensive report.
    """
    print("\n" + "="*80)
    print("PRICING QUIZ MAPPING VERIFICATION TEST (DRY RUN)")
    print("="*80)
    print(f"\nStarting verification at: {datetime.now().isoformat()}")
    print(f"Tenant ID: {tenant_id}")
    print("\nSAFETY: This is a READ-ONLY test. No pricing settings will be changed.\n")
    
    # Connect to database
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Load current Pricing Foundation
    print("Loading current Pricing Foundation settings...")
    pricing_config = await db.pricing_configuration.find_one(
        {"tenant_id": tenant_id},
        {"_id": 0}
    )
    
    if not pricing_config:
        print(f"⚠️  No Pricing Foundation found for tenant {tenant_id}")
        print("Creating minimal default structure for comparison...")
        pricing_config = {
            "tenant_id": tenant_id,
            "design_hourly_rate": 0,
            "production_hourly_rate": 0,
            "install_hourly_rate": 0,
            "target_profit_margin_percent": 0,
            "minimum_order": 0,
            "deposit_percentage": 0,
            "category_defaults": {},
        }
    
    print(f"✓ Loaded Pricing Foundation ({len(pricing_config)} top-level keys)\n")
    
    # Generate sample answers
    print("="*80)
    print("STEP 1: GENERATING SAMPLE QUIZ ANSWERS")
    print("="*80 + "\n")
    
    sample_answers = generate_sample_answers()
    total_questions = sum(len(s["questions"]) for s in QUIZ_SECTIONS)
    print(f"Generated {len(sample_answers)} sample answers from {total_questions} quiz questions:\n")
    
    for section in QUIZ_SECTIONS:
        print(f"  [{section['title']}]")
        for q in section["questions"]:
            key = q["key"]
            value = sample_answers.get(key)
            if q.get("type") == "bool":
                print(f"    • {q['label']}: {value}")
            else:
                unit = q.get("unit", "")
                print(f"    • {q['label']}: {unit}{value}")
        print()
    
    # Run mapping logic
    print("="*80)
    print("STEP 2: RUNNING QUIZ-TO-PRICING MAPPING LOGIC")
    print("="*80 + "\n")
    
    mapping_results = []
    simulated_foundation = dict(pricing_config)  # Copy for simulation
    
    for section in QUIZ_SECTIONS:
        for q in section["questions"]:
            key = q["key"]
            answer_value = sample_answers.get(key)
            
            if key not in ANSWER_TO_FOUNDATION_MAP:
                # Question doesn't map to any foundation field
                mapping_results.append({
                    "question_key": key,
                    "question_text": q["label"],
                    "section": section["title"],
                    "generated_answer": answer_value,
                    "maps_to": "NOT MAPPED",
                    "current_value": None,
                    "simulated_value": None,
                    "difference": None,
                    "conversion_rule": "No mapping defined",
                    "status": "Not Mapped",
                    "calculator_uses": "n/a",
                })
                continue
            
            mapping = ANSWER_TO_FOUNDATION_MAP[key]
            target_path = mapping["target_path"]
            conversion_rule = mapping["conversion_rule"]
            
            # Get current foundation value
            current_value = get_path_value(pricing_config, target_path)
            
            # Apply conversion logic
            simulated_value = apply_conversion_logic(key, answer_value, sample_answers)
            
            # Update simulated foundation
            if simulated_value is not None:
                simulated_foundation = set_path_value(simulated_foundation, target_path, simulated_value)
            
            # Calculate difference
            if current_value is not None and simulated_value is not None:
                try:
                    diff = round(simulated_value - current_value, 2)
                    diff_str = f"+${diff}" if diff >= 0 else f"-${abs(diff)}"
                    if "%" in conversion_rule or "percent" in conversion_rule.lower():
                        diff_str = f"+{diff}%" if diff >= 0 else f"{diff}%"
                except:
                    diff_str = "N/A"
            else:
                diff_str = "N/A"
            
            # Determine status
            if simulated_value is None:
                status = "Invalid Answer"
            elif current_value == simulated_value:
                status = "Same As Current"
            elif current_value is None or current_value == 0:
                status = "Would Apply (No Current)"
            else:
                status = "Would Apply (Would Change)"
            
            # Check if calculator uses this field
            calc_usage = check_calculator_usage(target_path)
            
            mapping_results.append({
                "question_key": key,
                "question_text": q["label"],
                "section": section["title"],
                "generated_answer": answer_value,
                "maps_to": " → ".join(target_path),
                "current_value": current_value,
                "simulated_value": simulated_value,
                "difference": diff_str,
                "conversion_rule": conversion_rule,
                "status": status,
                "calculator_uses": calc_usage,
            })
    
    # Print detailed mapping report
    print("DETAILED QUESTION-BY-QUESTION MAPPING RESULTS:\n")
    print("-" * 140)
    print(f"{'Question':<35} {'Answer':<12} {'Maps To':<40} {'Current':<10} {'Simulated':<10} {'Diff':<12} {'Status':<20}")
    print("-" * 140)
    
    for result in mapping_results:
        q_text = result["question_text"][:34]
        answer = str(result["generated_answer"])[:11] if result["generated_answer"] is not None else "—"
        maps_to = result["maps_to"][:39]
        current = str(result["current_value"])[:9] if result["current_value"] is not None else "—"
        simulated = str(result["simulated_value"])[:9] if result["simulated_value"] is not None else "—"
        diff = (result["difference"] or "N/A")[:11]
        status = result["status"][:19]
        
        print(f"{q_text:<35} {answer:<12} {maps_to:<40} {current:<10} {simulated:<10} {diff:<12} {status:<20}")
    
    print("-" * 140 + "\n")
    
    # Summary statistics
    print("="*80)
    print("STEP 3: MAPPING SUMMARY STATISTICS")
    print("="*80 + "\n")
    
    total_qs = len(mapping_results)
    mapped = len([r for r in mapping_results if r["status"] != "Not Mapped"])
    not_mapped = len([r for r in mapping_results if r["status"] == "Not Mapped"])
    would_apply = len([r for r in mapping_results if "Would Apply" in r["status"]])
    same_as_current = len([r for r in mapping_results if r["status"] == "Same As Current"])
    invalid = len([r for r in mapping_results if r["status"] == "Invalid Answer"])
    
    print(f"Total quiz questions tested:        {total_qs}")
    print(f"Questions mapped successfully:      {mapped}")
    print(f"Questions not mapped:               {not_mapped}")
    print(f"Would apply (would change):         {would_apply}")
    print(f"Same as current value:              {same_as_current}")
    print(f"Invalid/skipped answers:            {invalid}")
    print()
    
    # Calculator usage analysis
    print("="*80)
    print("STEP 4: CALCULATOR FIELD USAGE ANALYSIS")
    print("="*80 + "\n")
    
    used_count = len([r for r in mapping_results if r["calculator_uses"] == "used"])
    benchmark_count = len([r for r in mapping_results if r["calculator_uses"] == "benchmark_only"])
    stored_not_used_count = len([r for r in mapping_results if r["calculator_uses"] == "stored_not_used"])
    unknown_count = len([r for r in mapping_results if r["calculator_uses"] == "unknown"])
    
    print(f"Fields actively used in calculator:           {used_count}")
    print(f"Benchmark-only (comparison pricing):          {benchmark_count}")
    print(f"Stored but not currently used (minimums):     {stored_not_used_count}")
    print(f"Unknown/unverified usage:                     {unknown_count}")
    print()
    
    # List stored but not used fields
    if stored_not_used_count > 0:
        print("📝 Stored but not currently used in calculations:")
        for r in mapping_results:
            if r["calculator_uses"] == "stored_not_used":
                print(f"  • {r['question_text']} → {r['maps_to']}")
        print("  (These are minimum/floor values that could be enforced in future)")
        print()
    
    # Sample calculator before/after
    print("="*80)
    print("STEP 5: SAMPLE CALCULATOR BEFORE/AFTER COMPARISON")
    print("="*80 + "\n")
    
    print("Example 1: 4ft × 8ft banner (32 sqft)")
    current_banner_rate = get_path_value(pricing_config, ["category_defaults", "banners", "sell_rate_defaults", "base_rate"]) or 0
    simulated_banner_rate = get_path_value(simulated_foundation, ["category_defaults", "banners", "sell_rate_defaults", "base_rate"]) or 0
    print(f"  Current calculation:    32 sqft × ${current_banner_rate:.2f}/sqft = ${32 * current_banner_rate:.2f}")
    print(f"  Simulated calculation:  32 sqft × ${simulated_banner_rate:.2f}/sqft = ${32 * simulated_banner_rate:.2f}")
    print(f"  Difference:             ${32 * (simulated_banner_rate - current_banner_rate):.2f}")
    print()
    
    print("Example 2: 4ft × 8ft coroplast sign (32 sqft)")
    current_rigid_rate = get_path_value(pricing_config, ["category_defaults", "rigid_signs", "sell_rate_defaults", "base_rate"]) or 0
    simulated_rigid_rate = get_path_value(simulated_foundation, ["category_defaults", "rigid_signs", "sell_rate_defaults", "base_rate"]) or 0
    print(f"  Current calculation:    32 sqft × ${current_rigid_rate:.2f}/sqft = ${32 * current_rigid_rate:.2f}")
    print(f"  Simulated calculation:  32 sqft × ${simulated_rigid_rate:.2f}/sqft = ${32 * simulated_rigid_rate:.2f}")
    print(f"  Difference:             ${32 * (simulated_rigid_rate - current_rigid_rate):.2f}")
    print()
    
    print("Example 3: 250 sqft vehicle wrap")
    current_wrap_rate = get_path_value(pricing_config, ["category_defaults", "vehicle_graphics", "sell_rate_defaults", "printed_wrap_per_sqft"]) or 0
    simulated_wrap_rate = get_path_value(simulated_foundation, ["category_defaults", "vehicle_graphics", "sell_rate_defaults", "printed_wrap_per_sqft"]) or 0
    print(f"  Current calculation:    250 sqft × ${current_wrap_rate:.2f}/sqft = ${250 * current_wrap_rate:.2f}")
    print(f"  Simulated calculation:  250 sqft × ${simulated_wrap_rate:.2f}/sqft = ${250 * simulated_wrap_rate:.2f}")
    print(f"  Difference:             ${250 * (simulated_wrap_rate - current_wrap_rate):.2f}")
    print()
    
    print("Example 4: 2 hours of design labor")
    current_design_rate = pricing_config.get("design_hourly_rate", 0)
    simulated_design_rate = simulated_foundation.get("design_hourly_rate", 0)
    print(f"  Current calculation:    2 hrs × ${current_design_rate:.2f}/hr = ${2 * current_design_rate:.2f}")
    print(f"  Simulated calculation:  2 hrs × ${simulated_design_rate:.2f}/hr = ${2 * simulated_design_rate:.2f}")
    print(f"  Difference:             ${2 * (simulated_design_rate - current_design_rate):.2f}")
    print()
    
    print("Example 5: 3 hours of install labor")
    current_install_rate = pricing_config.get("install_hourly_rate", 0)
    simulated_install_rate = simulated_foundation.get("install_hourly_rate", 0)
    print(f"  Current calculation:    3 hrs × ${current_install_rate:.2f}/hr = ${3 * current_install_rate:.2f}")
    print(f"  Simulated calculation:  3 hrs × ${simulated_install_rate:.2f}/hr = ${3 * simulated_install_rate:.2f}")
    print(f"  Difference:             ${3 * (simulated_install_rate - current_install_rate):.2f}")
    print()
    
    # Broken/unused mappings
    print("="*80)
    print("STEP 6: BROKEN OR UNUSED MAPPINGS")
    print("="*80 + "\n")
    
    broken_mappings = [r for r in mapping_results if r["status"] == "Invalid Answer"]
    unused_mappings = [r for r in mapping_results if r["status"] == "Not Mapped"]
    
    if broken_mappings:
        print("⚠️  BROKEN MAPPINGS (invalid answers produced):")
        for r in broken_mappings:
            print(f"  • {r['question_text']}: {r['conversion_rule']}")
        print()
    else:
        print("✓ No broken mappings detected.\n")
    
    if unused_mappings:
        print("⚠️  UNMAPPED QUESTIONS (no Pricing Foundation target):")
        for r in unused_mappings:
            print(f"  • {r['question_text']}")
        print()
    else:
        print("✓ All questions have defined mappings.\n")
    
    # Recommended fixes
    print("="*80)
    print("STEP 7: RECOMMENDED FIXES & IMPROVEMENTS")
    print("="*80 + "\n")
    
    recommendations = []
    
    # Check for questions that don't map
    if unused_mappings:
        recommendations.append(f"Add mapping logic for {len(unused_mappings)} unmapped questions")
    
    # Check for zero current values
    zero_current = [r for r in mapping_results if r["current_value"] == 0 and r["status"] != "Not Mapped"]
    if zero_current:
        recommendations.append(f"{len(zero_current)} fields have zero/null current values — quiz would populate these")
    
    # Check for unknown calculator usage
    unknown_usage = [r for r in mapping_results if r["calculator_uses"] == "unknown"]
    if unknown_usage:
        recommendations.append(f"Verify calculator usage for {len(unknown_usage)} fields marked 'unknown'")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print()
    else:
        print("✓ No immediate fixes needed. Quiz mapping appears functional.\n")
    
    # Final confirmation
    print("="*80)
    print("SAFETY CONFIRMATION")
    print("="*80 + "\n")
    print("✓ DRY RUN ONLY. No real pricing settings were changed.")
    print(f"✓ Simulated {len(mapping_results)} mappings without modifying database.")
    print(f"✓ Current Pricing Foundation remains unchanged.\n")
    
    print("="*80)
    print("VERIFICATION COMPLETE")
    print("="*80)
    print(f"\nCompleted at: {datetime.now().isoformat()}\n")
    
    # Save report to file
    report_path = "/app/quiz_mapping_verification_report.json"
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "tenant_id": tenant_id,
        "summary": {
            "total_questions": total_qs,
            "mapped_successfully": mapped,
            "not_mapped": not_mapped,
            "would_apply": would_apply,
            "same_as_current": same_as_current,
            "invalid_answers": invalid,
            "calculator_usage": {
                "used": used_count,
                "benchmark_only": benchmark_count,
                "stored_not_used": stored_not_used_count,
                "unknown": unknown_count,
            },
        },
        "detailed_results": mapping_results,
        "sample_answers": sample_answers,
        "recommendations": recommendations,
    }
    
    with open(report_path, "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"📄 Full report saved to: {report_path}\n")
    
    client.close()


# ============================================================================
# ENTRY POINT
# ============================================================================


if __name__ == "__main__":
    import asyncio
    
    # Get tenant_id from command line or use default test tenant
    if len(sys.argv) > 1:
        tenant_id = sys.argv[1]
    else:
        print("Usage: python quiz_mapping_verification.py <tenant_id>")
        print("\nAttempting to find first tenant in database...")
        
        async def find_first_tenant():
            client = AsyncIOMotorClient(MONGO_URL)
            db = client[DB_NAME]
            tenant = await db.tenants.find_one({}, {"_id": 0, "id": 1})
            client.close()
            return tenant["id"] if tenant else None
        
        tenant_id = asyncio.run(find_first_tenant())
        
        if not tenant_id:
            print("❌ No tenants found in database. Cannot proceed.")
            sys.exit(1)
        
        print(f"✓ Found tenant: {tenant_id}\n")
    
    asyncio.run(run_verification(tenant_id))
