"""
PRICING FOUNDATION FIELD USAGE AUDIT

This script performs a comprehensive audit of every field in the Pricing Foundation
to determine which fields actually affect pricing output and which are just stored data.

GOAL: Identify fields that can be removed, hidden, or marked as informational.

SAFETY: This is a READ-ONLY audit. No fields are removed or modified.
"""

import json
import os
import sys
import re
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "signtist")

# ============================================================================
# FIELD CLASSIFICATION CATEGORIES
# ============================================================================

CLASSIFICATION = {
    "ACTIVELY_USED": "Actively Used - Field directly changes pricing output",
    "USED_INDIRECTLY": "Used Indirectly - Affects multiplier, rule, or default",
    "STORED_DISPLAY": "Stored / Display Only - Saved but doesn't affect price",
    "QUIZ_MAPPED_ONLY": "Quiz-Mapped Only - Receives quiz data but calculator doesn't use it",
    "DEPRECATED": "Deprecated / Legacy - Old field no longer used",
    "UNUSED": "Unused / Safe to Remove - No pricing impact anywhere",
    "NEEDS_REVIEW": "Needs Review - Usage unclear",
}

# ============================================================================
# KNOWN ACTIVELY USED FIELDS (from calculator code review)
# ============================================================================

ACTIVELY_USED_FIELDS = {
    # Top-level labor rates
    "design_hourly_rate",
    "production_hourly_rate",  # Maps to hourly_rate in some contexts
    "install_hourly_rate",
    "hourly_rate",  # General production rate
    
    # Margins and markups
    "target_profit_margin_percent",
    "default_markup_percent",
    "material_markup_percent",
    
    # Minimums
    "minimum_order",
    "deposit_percentage",
    
    # Waste and overhead
    "waste_percentage",
    
    # Category sell rates
    "category_defaults.banners.sell_rate_defaults.base_rate",
    "category_defaults.rigid_signs.sell_rate_defaults.base_rate",
    "category_defaults.rigid_signs.sell_rate_defaults.yard_sign_rate",
    "category_defaults.cut_vinyl.sell_rate_defaults.base_rate",
    "category_defaults.digital_print.sell_rate_defaults.base_rate",
    "category_defaults.digital_print.sell_rate_defaults.laminate_addon_per_sqft",
    "category_defaults.vehicle_graphics.sell_rate_defaults.printed_wrap_per_sqft",
    "category_defaults.vehicle_graphics.sell_rate_defaults.color_change_per_sqft",
    "category_defaults.apparel.default_blank_cost",
    "category_defaults.apparel.default_decoration_cost",
    "category_defaults.services.labor_rate_overrides.design",
    "category_defaults.services.labor_rate_overrides.production",
    "category_defaults.services.labor_rate_overrides.install",
    "category_defaults.promotional.default_markup_multiplier",
    "category_defaults.custom.default_markup_multiplier",
    
    # Materials (cost inputs)
    "materials",  # Array of material configs with cost_per_sqft
    
    # Rush fees
    "rush_fee_percentage",
    "rush_fee_flat",
    
    # Time estimates (affect labor cost)
    "weeding_time_per_sqft",
    "application_time_per_sqft",
    "print_time_per_sqft",
    "laminate_time_per_sqft",
    
    # Travel
    "mileage_rate",
    "minimum_travel_charge",
    
    # Banner components
    "banner_grommet_price_each",
    "banner_hemming_tape_price_per_linear_inch",
}

# Fields that are stored but not used in calculations
STORED_NOT_USED_FIELDS = {
    "category_defaults.banners.default_minimum_sell_price",
    "category_defaults.rigid_signs.default_minimum_sell_price",
    "category_defaults.rigid_signs.quantity_breaks.qty_10_percent",
    "category_defaults.rigid_signs.quantity_breaks.qty_25_percent",
    "category_defaults.cut_vinyl.default_minimum_sell_price",
    "category_defaults.services.minimums.design",
    "category_defaults.services.minimums.install",
    "category_defaults.promotional.minimum_setup_fee",
    "category_defaults.promotional.minimum_charge",
    "minimum_design_charge",
    "minimum_install_charge",
    "minimum_removal_charge",
    "minimum_vinyl_charge",
    "minimum_print_charge",
    "minimum_sign_charge",
    "minimum_service_charge",
    "minimum_wrap_charge",
}

# Benchmark-only fields (reference pricing, not used in calculations)
BENCHMARK_FIELDS = {
    "selling_price_benchmarks",
    "category_defaults.vehicle_graphics.benchmarks",
    "category_defaults.apparel.shop_pricing_table",
}

# Fields used indirectly (affect rules, defaults, or multipliers)
INDIRECTLY_USED_FIELDS = {
    "ai_estimation_rules",
    "benchmark_rules",
    "global_calc_rules",
    "quantity_breaks",
    "complexity_multiplier_base",
    "complexity_multiplier_max",
    "install_complexity_multiplier_base",
    "install_complexity_multiplier_max",
    "rounding_rule",
}

# ============================================================================
# FIELD EXTRACTION
# ============================================================================

def extract_all_field_paths(obj: Any, prefix: str = "", max_depth: int = 10) -> List[str]:
    """Recursively extract all field paths from a nested dict/object."""
    if max_depth == 0:
        return []
    
    paths = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{prefix}.{key}" if prefix else key
            paths.append(current_path)
            
            if isinstance(value, (dict, list)):
                paths.extend(extract_all_field_paths(value, current_path, max_depth - 1))
    
    elif isinstance(obj, list) and len(obj) > 0:
        # For arrays, we note the array itself and sample first element structure
        if isinstance(obj[0], dict):
            for key in obj[0].keys():
                array_path = f"{prefix}[].{key}"
                paths.append(array_path)
    
    return paths


def get_default_pricing_structure() -> Dict[str, Any]:
    """Get the default Pricing Foundation structure from models."""
    # This mirrors the structure from pricing.py PricingDefaults
    return {
        "tenant_id": "sample",
        "materials": [],
        "hardware_accessories": [],
        "category_defaults": {
            "banners": {
                "sell_rate_defaults": {"base_rate": 0, "large_format_rate": 0},
                "cost_multipliers": {},
                "default_minimum_sell_price": 0,
            },
            "rigid_signs": {
                "sell_rate_defaults": {"base_rate": 0, "yard_sign_rate": 0},
                "quantity_breaks": {"qty_10_percent": 0, "qty_25_percent": 0},
                "default_minimum_sell_price": 0,
            },
            "cut_vinyl": {
                "sell_rate_defaults": {"base_rate": 0},
                "default_minimum_sell_price": 0,
            },
            "digital_print": {
                "sell_rate_defaults": {"base_rate": 0, "laminate_addon_per_sqft": 0},
            },
            "vehicle_graphics": {
                "sell_rate_defaults": {
                    "printed_wrap_per_sqft": 0,
                    "color_change_per_sqft": 0,
                },
                "benchmarks": {
                    "package_door_lettering": 0,
                    "package_spot_graphics": 0,
                    "package_partial_wrap": 0,
                    "package_full_wrap": 0,
                },
            },
            "apparel": {
                "default_blank_cost": 0,
                "default_decoration_cost": 0,
                "shop_pricing_table": {},
            },
            "services": {
                "labor_rate_overrides": {"design": 0, "production": 0, "install": 0},
                "minimums": {"design": 0, "install": 0},
            },
            "promotional": {
                "default_markup_multiplier": 1.0,
                "minimum_setup_fee": 0,
                "minimum_charge": 0,
            },
            "custom": {
                "default_markup_multiplier": 1.0,
            },
        },
        "selling_price_benchmarks": {},
        "design_hourly_rate": 85,
        "production_hourly_rate": 28,
        "install_hourly_rate": 95,
        "hourly_rate": 75,
        "removal_hourly_rate": 65,
        "travel_hourly_rate": 45,
        "admin_hourly_rate": 35,
        "project_handling_hourly_rate": 35,
        "default_markup_percent": 100,
        "material_markup_percent": 50,
        "target_profit_margin_percent": 40,
        "waste_percentage": 10,
        "minimum_order": 50,
        "minimum_design_charge": 75,
        "minimum_install_charge": 150,
        "minimum_removal_charge": 120,
        "minimum_vinyl_charge": 25,
        "minimum_print_charge": 35,
        "minimum_sign_charge": 50,
        "minimum_service_charge": 75,
        "minimum_wrap_charge": 500,
        "banner_grommet_price_each": 1.0,
        "banner_hemming_tape_price_per_linear_inch": 0.03,
        "rush_fee_percentage": 25,
        "rush_fee_flat": 0,
        "setup_fee_default": 20,
        "file_cleanup_fee_default": 15,
        "rounding_rule": "nearest_dollar",
        "deposit_percentage": 50,
        "ai_fallback_behavior": "warn",
        "ai_fallback_warnings_enabled": True,
        "complexity_multiplier_base": 1.0,
        "complexity_multiplier_max": 2.0,
        "install_complexity_multiplier_base": 1.0,
        "install_complexity_multiplier_max": 2.0,
        "setup_fee_vinyl": 15,
        "setup_fee_print": 25,
        "setup_fee_apparel_screen": 35,
        "setup_fee_apparel_dtf": 20,
        "quantity_breaks": {},
        "weeding_time_per_sqft": 5.0,
        "application_time_per_sqft": 3.0,
        "print_time_per_sqft": 1.0,
        "laminate_time_per_sqft": 1.5,
        "mileage_rate": 0.67,
        "minimum_travel_charge": 50,
        "ai_estimation_rules": {},
        "benchmark_rules": {},
        "global_calc_rules": {},
    }


# ============================================================================
# CODE USAGE SEARCH
# ============================================================================

def search_code_for_field(field_name: str, search_dirs: List[str]) -> Dict[str, List[str]]:
    """Search backend and frontend code for field usage."""
    results = {
        "backend": [],
        "frontend": [],
    }
    
    # Normalize field name for search patterns
    # e.g., "category_defaults.banners.sell_rate_defaults.base_rate"
    parts = field_name.split(".")
    search_patterns = [
        field_name,  # Exact path
        parts[-1],   # Last part only (e.g., "base_rate")
        "_".join(parts[-2:]) if len(parts) >= 2 else "",  # Last two parts
    ]
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        
        for root, dirs, files in os.walk(search_dir):
            # Skip node_modules, .git, etc.
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.next']]
            
            for file in files:
                if not (file.endswith('.py') or file.endswith('.js') or file.endswith('.jsx')):
                    continue
                
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        for pattern in search_patterns:
                            if pattern and pattern in content:
                                location = "backend" if "/backend/" in filepath else "frontend"
                                relative_path = filepath.replace("/app/", "")
                                
                                # Check if it's just a comment or actual usage
                                if not re.search(rf'#.*{re.escape(pattern)}', content):
                                    if relative_path not in results[location]:
                                        results[location].append(relative_path)
                                break
                except:
                    pass
    
    return results


# ============================================================================
# FIELD CLASSIFIER
# ============================================================================

def classify_field(field_path: str, code_usage: Dict[str, List[str]]) -> Tuple[str, str]:
    """
    Classify a field based on known usage patterns and code search.
    
    Returns: (classification, reason)
    """
    # Check against known categories first
    if field_path in ACTIVELY_USED_FIELDS:
        return "ACTIVELY_USED", "Verified in calculator code - directly affects price output"
    
    if field_path in STORED_NOT_USED_FIELDS:
        return "STORED_DISPLAY", "Stored in database but not enforced in calculator"
    
    if field_path in INDIRECTLY_USED_FIELDS:
        return "USED_INDIRECTLY", "Affects calculation rules, multipliers, or AI behavior"
    
    # Check for benchmark fields
    for benchmark_prefix in BENCHMARK_FIELDS:
        if field_path.startswith(benchmark_prefix):
            return "STORED_DISPLAY", "Benchmark/reference pricing - not used in cost-plus calculations"
    
    # Check code usage
    backend_usage = code_usage.get("backend", [])
    frontend_usage = code_usage.get("frontend", [])
    
    # Field used in backend pricing routes
    pricing_files = ["routes/pricing.py", "routes/job_tickets.py", "routes/wrap/"]
    used_in_pricing = any(any(pf in file for pf in pricing_files) for file in backend_usage)
    
    if used_in_pricing:
        return "ACTIVELY_USED", f"Found in pricing logic: {', '.join(backend_usage[:2])}"
    
    # Field only in models or frontend
    if backend_usage and not used_in_pricing:
        return "STORED_DISPLAY", f"Found in models but not calculator: {', '.join(backend_usage[:2])}"
    
    if frontend_usage and not backend_usage:
        # Check if it's quiz mapping
        if any("quiz" in f.lower() for f in frontend_usage):
            return "QUIZ_MAPPED_ONLY", f"Quiz maps to this field but calculator doesn't use it"
        return "STORED_DISPLAY", "Frontend display only"
    
    if not backend_usage and not frontend_usage:
        return "UNUSED", "No usage found in backend or frontend code"
    
    return "NEEDS_REVIEW", "Usage pattern unclear - manual review needed"


# ============================================================================
# MAIN AUDIT
# ============================================================================

async def run_audit(tenant_id: Optional[str] = None):
    """Run comprehensive Pricing Foundation field usage audit."""
    
    print("\n" + "="*80)
    print("PRICING FOUNDATION FIELD USAGE AUDIT")
    print("="*80)
    print(f"\nStarting audit at: {datetime.now().isoformat()}")
    print("SAFETY: This is a READ-ONLY audit. No fields will be removed.\n")
    
    # Get default structure
    print("Loading Pricing Foundation schema...")
    default_structure = get_default_pricing_structure()
    
    # Extract all field paths
    print("Extracting all field paths...")
    all_paths = extract_all_field_paths(default_structure)
    all_paths = sorted(set(all_paths))  # Deduplicate and sort
    
    print(f"✓ Found {len(all_paths)} unique field paths\n")
    
    # Search code for each field
    print("Searching codebase for field usage (this may take a moment)...")
    search_dirs = ["/app/backend", "/app/frontend/src"]
    
    field_audit = []
    
    for i, field_path in enumerate(all_paths, 1):
        if i % 20 == 0:
            print(f"  Processed {i}/{len(all_paths)} fields...")
        
        code_usage = search_code_for_field(field_path, search_dirs)
        classification, reason = classify_field(field_path, code_usage)
        
        field_audit.append({
            "field_path": field_path,
            "classification": classification,
            "reason": reason,
            "backend_files": code_usage.get("backend", [])[:5],  # Limit to first 5
            "frontend_files": code_usage.get("frontend", [])[:5],
        })
    
    print(f"✓ Completed field usage analysis\n")
    
    # Generate statistics
    stats = defaultdict(int)
    for item in field_audit:
        stats[item["classification"]] += 1
    
    print("="*80)
    print("AUDIT SUMMARY STATISTICS")
    print("="*80 + "\n")
    print(f"Total fields audited:                 {len(all_paths)}")
    print(f"  • Actively Used:                    {stats['ACTIVELY_USED']}")
    print(f"  • Used Indirectly:                  {stats['USED_INDIRECTLY']}")
    print(f"  • Stored / Display Only:            {stats['STORED_DISPLAY']}")
    print(f"  • Quiz-Mapped Only:                 {stats['QUIZ_MAPPED_ONLY']}")
    print(f"  • Deprecated / Legacy:              {stats['DEPRECATED']}")
    print(f"  • Unused / Safe to Remove:          {stats['UNUSED']}")
    print(f"  • Needs Review:                     {stats['NEEDS_REVIEW']}")
    print()
    
    # Generate detailed report
    print("="*80)
    print("DETAILED FIELD AUDIT REPORT")
    print("="*80 + "\n")
    
    # Group by classification
    for classification in ["ACTIVELY_USED", "USED_INDIRECTLY", "STORED_DISPLAY", 
                          "QUIZ_MAPPED_ONLY", "UNUSED", "NEEDS_REVIEW"]:
        items = [item for item in field_audit if item["classification"] == classification]
        if not items:
            continue
        
        print(f"\n{'='*80}")
        print(f"{classification}: {CLASSIFICATION[classification]}")
        print(f"{'='*80}\n")
        print(f"Count: {len(items)}\n")
        
        for item in items:
            print(f"Field: {item['field_path']}")
            print(f"Reason: {item['reason']}")
            if item['backend_files']:
                print(f"Backend: {', '.join(item['backend_files'][:3])}")
            if item['frontend_files']:
                print(f"Frontend: {', '.join(item['frontend_files'][:3])}")
            print()
    
    # Save report
    report_path = "/app/PRICING_FOUNDATION_FIELD_USAGE_AUDIT.md"
    json_path = "/app/pricing_foundation_field_usage_audit.json"
    
    # Generate markdown report
    with open(report_path, "w") as f:
        f.write("# Pricing Foundation Field Usage Audit Report\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}  \n")
        f.write(f"**Total Fields Audited:** {len(all_paths)}  \n\n")
        
        f.write("---\n\n")
        f.write("## Summary Statistics\n\n")
        f.write("| Classification | Count | Percentage |\n")
        f.write("|----------------|-------|------------|\n")
        for classification in ["ACTIVELY_USED", "USED_INDIRECTLY", "STORED_DISPLAY", 
                              "QUIZ_MAPPED_ONLY", "UNUSED", "NEEDS_REVIEW"]:
            count = stats[classification]
            pct = (count / len(all_paths) * 100) if len(all_paths) > 0 else 0
            f.write(f"| {classification} | {count} | {pct:.1f}% |\n")
        
        f.write("\n---\n\n")
        
        # Detailed tables by classification
        for classification in ["ACTIVELY_USED", "USED_INDIRECTLY", "STORED_DISPLAY", 
                              "QUIZ_MAPPED_ONLY", "UNUSED", "NEEDS_REVIEW"]:
            items = [item for item in field_audit if item["classification"] == classification]
            if not items:
                continue
            
            f.write(f"\n## {classification}\n\n")
            f.write(f"**Definition:** {CLASSIFICATION[classification]}  \n")
            f.write(f"**Count:** {len(items)}  \n\n")
            
            f.write("| Field Path | Reason | Code Usage |\n")
            f.write("|------------|--------|------------|\n")
            for item in items:
                backend = f"Backend: {len(item['backend_files'])} files" if item['backend_files'] else ""
                frontend = f"Frontend: {len(item['frontend_files'])} files" if item['frontend_files'] else ""
                usage = ", ".join(filter(None, [backend, frontend])) or "None found"
                f.write(f"| `{item['field_path']}` | {item['reason']} | {usage} |\n")
            
            f.write("\n")
    
    # Save JSON
    with open(json_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_fields": len(all_paths),
            "statistics": dict(stats),
            "fields": field_audit,
        }, f, indent=2)
    
    print("="*80)
    print("REPORTS GENERATED")
    print("="*80 + "\n")
    print(f"📄 Markdown report: {report_path}")
    print(f"📄 JSON report: {json_path}\n")
    
    print("="*80)
    print("SAFETY CONFIRMATION")
    print("="*80 + "\n")
    print("✅ DRY RUN ONLY - No fields were removed or modified")
    print("✅ No Pricing Foundation values were changed")
    print("✅ No database updates performed\n")
    
    print("="*80)
    print("AUDIT COMPLETE")
    print("="*80 + "\n")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_audit())
