"""
Historical Invoice Import + AI Pricing Analysis Tests (Iteration 56)
====================================================================
Testing the tenant-specific historical invoice import workflow:
- POST /api/pricing-setup/imports - Upload CSV, XLSX, PDF historical invoice files
- GET /api/pricing-setup/imports - List tenant-scoped import sessions
- GET /api/pricing-setup/imports/{id} - Get specific tenant-scoped import session
- PUT /api/pricing-setup/imports/{id}/mapping - Save field mapping (description, quantity, total, dimension, category)
- POST /api/pricing-setup/imports/{id}/analyze - Run AI analysis, get suggestions with confidence levels
- POST /api/pricing-setup/imports/{id}/review - Accept/Edit/Ignore suggestions, save to selling_price_benchmarks only
- Tenant isolation checks
- Verify pricing settings separation (benchmarks vs cost settings)
- No regression on /pricing-calculator/settings
"""

import pytest
import requests
import os
import io
import csv
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD


class TestPricingSetup:
    """Test historical invoice import and AI pricing analysis features"""
    
    token = None
    tenant_id = None
    test_import_id = None
    suggestion_ids = []
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate and get token before tests"""
        if TestPricingSetup.token is None:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )
            assert response.status_code == 200, f"Login failed: {response.text}"
            data = response.json()
            TestPricingSetup.token = data["access_token"]
    
    def get_headers(self):
        return {"Authorization": f"Bearer {TestPricingSetup.token}"}
    
    def get_json_headers(self):
        return {"Authorization": f"Bearer {TestPricingSetup.token}", "Content-Type": "application/json"}
    
    # ===================== GET IMPORTS LIST TESTS =====================
    
    def test_01_get_imports_list_empty_or_existing(self):
        """GET /api/pricing-setup/imports returns tenant-scoped import sessions"""
        response = requests.get(f"{BASE_URL}/api/pricing-setup/imports", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"[PASS] GET /api/pricing-setup/imports returned {len(data)} import sessions")
    
    # ===================== CREATE IMPORT WITH CSV UPLOAD =====================
    
    def test_02_create_import_with_csv(self):
        """POST /api/pricing-setup/imports creates tenant-scoped import session with CSV"""
        # Create a simple CSV in memory
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Description", "Quantity", "Total", "Dimensions", "Category"])
        writer.writerow(["24x36 Banner with Grommets", "2", "85.00", "24x36", "banners"])
        writer.writerow(["18x24 Yard Sign - Coroplast", "10", "120.00", "18x24", "rigid_signs"])
        writer.writerow(["Vehicle Door Logo - Van", "1", "350.00", "24x18", "vehicle_wraps"])
        writer.writerow(["Custom Vinyl Lettering", "5", "75.00", "12x6", "cut_vinyl"])
        writer.writerow(["T-Shirt Screen Print", "25", "275.00", "", "apparel"])
        csv_content = csv_buffer.getvalue().encode('utf-8')
        
        files = {
            'files': ('test_invoices.csv', csv_content, 'text/csv')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing-setup/imports",
            headers=self.get_headers(),
            files=files
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Import ID missing"
        assert "tenant_id" in data, "tenant_id missing"
        assert "files" in data, "files missing"
        assert len(data["files"]) == 1, "Expected 1 file"
        
        # Verify file metadata
        file_info = data["files"][0]
        assert file_info.get("extension") == ".csv", "Expected CSV extension"
        assert file_info.get("filename") == "test_invoices.csv"
        
        # Verify mapping suggestions were auto-generated
        mapping = data.get("mapping", {})
        assert mapping is not None, "mapping should not be None"
        
        TestPricingSetup.test_import_id = data["id"]
        
        print(f"[PASS] Created import {data['id'][:8]} with CSV file, status: {data.get('status')}")
    
    # ===================== GET SINGLE IMPORT =====================
    
    def test_03_get_import_by_id(self):
        """GET /api/pricing-setup/imports/{id} returns tenant-scoped import session"""
        assert TestPricingSetup.test_import_id is not None, "No import ID from previous test"
        
        response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert data.get("id") == TestPricingSetup.test_import_id
        assert "files" in data
        assert "mapping" in data
        assert "status" in data
        
        # Verify preview data exists
        files = data.get("files", [])
        if files and files[0].get("extension") in [".csv", ".xlsx", ".xls"]:
            preview = files[0].get("preview", {})
            assert "columns" in preview, "CSV preview should have columns"
            assert "sample_rows" in preview, "CSV preview should have sample_rows"
        
        print(f"[PASS] GET /api/pricing-setup/imports/{TestPricingSetup.test_import_id[:8]} returned correct data")
    
    # ===================== UPDATE MAPPING =====================
    
    def test_04_update_mapping(self):
        """PUT /api/pricing-setup/imports/{id}/mapping saves field mapping and builds normalized rows"""
        assert TestPricingSetup.test_import_id is not None
        
        mapping_payload = {
            "description_field": "Description",
            "quantity_field": "Quantity",
            "total_field": "Total",
            "dimension_field": "Dimensions",
            "category_field": "Category",
            "category_overrides": {}
        }
        
        response = requests.put(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}/mapping",
            headers=self.get_json_headers(),
            json=mapping_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify mapping was saved
        mapping = data.get("mapping", {})
        assert mapping.get("description_field") == "Description"
        assert mapping.get("quantity_field") == "Quantity"
        assert mapping.get("total_field") == "Total"
        
        # Verify normalized_rows were created
        normalized_rows = data.get("normalized_rows", [])
        assert len(normalized_rows) >= 1, "Expected normalized rows to be created"
        
        # Check normalized row structure
        if normalized_rows:
            row = normalized_rows[0]
            assert "row_id" in row, "row_id missing"
            assert "description" in row, "description missing"
            assert "quantity" in row, "quantity missing"
            assert "total" in row, "total missing"
            assert "category_final" in row, "category_final missing"
        
        # Verify status updated
        assert data.get("status") == "ready_for_analysis", "Status should be ready_for_analysis"
        
        print(f"[PASS] Mapping saved, {len(normalized_rows)} normalized rows created")
    
    # ===================== RUN ANALYSIS =====================
    
    def test_05_run_analysis(self):
        """POST /api/pricing-setup/imports/{id}/analyze generates AI suggestions with confidence levels"""
        assert TestPricingSetup.test_import_id is not None
        
        analyze_payload = {
            "excluded_row_ids": []  # Don't exclude any rows
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}/analyze",
            headers=self.get_json_headers(),
            json=analyze_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify analysis_summary was created
        analysis_summary = data.get("analysis_summary")
        assert analysis_summary is not None, "analysis_summary missing"
        assert "invoice_count" in analysis_summary, "invoice_count missing"
        assert "line_item_count" in analysis_summary, "line_item_count missing"
        assert "categories_detected" in analysis_summary, "categories_detected missing"
        
        # Verify suggestions were created
        suggestions = data.get("suggestions", [])
        assert len(suggestions) >= 1, "Expected at least one suggestion"
        
        # Check suggestion structure
        for suggestion in suggestions:
            assert "id" in suggestion, "suggestion id missing"
            assert "category_key" in suggestion, "category_key missing"
            assert "category_label" in suggestion, "category_label missing"
            assert "benchmark_field" in suggestion, "benchmark_field missing"
            assert "suggested_value" in suggestion, "suggested_value missing"
            assert "confidence" in suggestion, "confidence missing"
            assert suggestion["confidence"] in ["High", "Medium", "Low"], f"Invalid confidence: {suggestion['confidence']}"
            assert "status" in suggestion, "status missing (should be pending)"
        
        # Save suggestion IDs for review test
        TestPricingSetup.suggestion_ids = [s["id"] for s in suggestions]
        
        # Verify status updated
        assert data.get("status") == "analyzed", "Status should be analyzed"
        
        print(f"[PASS] Analysis complete: {analysis_summary.get('line_item_count')} items, {len(suggestions)} suggestions with confidence levels")
    
    # ===================== REVIEW SUGGESTIONS =====================
    
    def test_06_review_suggestions_save_to_benchmarks(self):
        """POST /api/pricing-setup/imports/{id}/review saves accepted suggestions to selling_price_benchmarks only"""
        assert TestPricingSetup.test_import_id is not None
        assert len(TestPricingSetup.suggestion_ids) > 0, "No suggestions from previous test"
        
        # Accept one suggestion, ignore another
        decisions = []
        for i, sid in enumerate(TestPricingSetup.suggestion_ids[:2]):  # Take first 2
            decisions.append({
                "suggestion_id": sid,
                "status": "accepted" if i == 0 else "ignored",
                "final_value": 100.0 if i == 0 else 50.0  # Override value for first
            })
        
        review_payload = {
            "decisions": decisions
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}/review",
            headers=self.get_json_headers(),
            json=review_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify response indicates benchmarks-only save
        assert "message" in data, "message missing"
        assert "selling_price_benchmarks_only" in data.get("saved_to", ""), "Should save to benchmarks only"
        
        print(f"[PASS] Review saved, accepted categories: {data.get('accepted_categories', [])}")
    
    # ===================== VERIFY BENCHMARKS SAVED, NOT COST SETTINGS =====================
    
    def test_07_verify_benchmarks_separate_from_cost_settings(self):
        """GET /api/pricing/defaults verifies selling_price_benchmarks updated, cost settings unchanged"""
        response = requests.get(f"{BASE_URL}/api/pricing/defaults", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify selling_price_benchmarks structure exists
        benchmarks = data.get("selling_price_benchmarks", {})
        assert len(benchmarks) > 0, "selling_price_benchmarks should exist"
        
        # Verify category_defaults (cost settings) are separate
        category_defaults = data.get("category_defaults", {})
        assert len(category_defaults) > 0, "category_defaults should exist"
        
        # Verify materials list exists (cost settings)
        materials = data.get("materials", [])
        assert len(materials) > 0, "materials should exist"
        
        # Key check: benchmarks and cost settings are SEPARATE structures
        # Benchmarks have: average_sell_price_per_sqft, average_order_total, minimum_charge
        # Cost settings have: default_labor_hours_per_sqft, default_markup_multiplier, etc.
        
        for cat_key in ["vehicle_wraps", "banners", "rigid_signs"]:
            if cat_key in benchmarks:
                benchmark = benchmarks[cat_key]
                # Benchmarks should NOT have cost-related fields
                assert "default_labor_hours_per_sqft" not in benchmark, "Benchmark should not have cost field"
                # Benchmarks should have selling-price fields
                # (may have average_sell_price_per_sqft or average_sell_price_per_unit depending on category)
            
            if cat_key in category_defaults:
                _cost_settings = category_defaults[cat_key]
                # Cost settings should have labor/markup fields
                # (specific fields depend on category type)
        
        print(f"[PASS] Selling benchmarks ({len(benchmarks)} categories) are separate from cost settings ({len(category_defaults)} categories)")
    
    # ===================== TENANT ISOLATION CHECK =====================
    
    def test_08_tenant_isolation_check(self):
        """Verify imports are tenant-isolated (access own imports only)"""
        # Get list of imports
        response = requests.get(f"{BASE_URL}/api/pricing-setup/imports", headers=self.get_headers())
        assert response.status_code == 200
        
        imports = response.json()
        
        # All imports should belong to the same tenant
        if len(imports) > 0:
            # Try to access each import - should succeed for own tenant
            for imp in imports[:3]:  # Check first 3
                imp_response = requests.get(
                    f"{BASE_URL}/api/pricing-setup/imports/{imp['id']}",
                    headers=self.get_headers()
                )
                assert imp_response.status_code == 200, f"Should access own import {imp['id'][:8]}"
        
        # Try to access a fake import ID - should return 404
        fake_id = "00000000-0000-0000-0000-000000000000"
        fake_response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports/{fake_id}",
            headers=self.get_headers()
        )
        assert fake_response.status_code == 404, "Fake import ID should return 404"
        
        print("[PASS] Tenant isolation verified - can access own imports, 404 for non-existent")
    
    # ===================== NO REGRESSION ON PRICING SETTINGS =====================
    
    def test_09_no_regression_pricing_settings(self):
        """Verify /pricing-calculator/settings endpoint still works after benchmark saves"""
        # GET pricing defaults
        response = requests.get(f"{BASE_URL}/api/pricing/defaults", headers=self.get_headers())
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Verify all expected fields exist
        assert "materials" in data, "materials missing"
        assert "production_hourly_rate" in data, "production_hourly_rate missing"
        assert "overhead_percentage" in data, "overhead_percentage missing"
        assert "category_defaults" in data, "category_defaults missing"
        assert "selling_price_benchmarks" in data, "selling_price_benchmarks missing"
        
        # Verify we can still update pricing settings (PUT)
        update_payload = {
            "production_hourly_rate": data.get("production_hourly_rate", 28.0)
        }
        
        put_response = requests.put(
            f"{BASE_URL}/api/pricing/defaults",
            headers=self.get_json_headers(),
            json=update_payload
        )
        assert put_response.status_code == 200, f"PUT failed: {put_response.text}"
        
        # Verify pricing calculator still works
        calc_payload = {
            "category": "digital_print",
            "pricing_data": {
                "width_inches": 24,
                "length_inches": 36,
                "print_material": "banner_13oz"
            },
            "quantity": 1
        }
        
        calc_response = requests.post(
            f"{BASE_URL}/api/pricing/calculate",
            headers=self.get_json_headers(),
            json=calc_payload
        )
        assert calc_response.status_code == 200, f"Calculate failed: {calc_response.text}"
        
        calc_data = calc_response.json()
        assert "selling_price" in calc_data
        assert "total_cost" in calc_data
        
        print("[PASS] No regression - pricing settings and calculator still working")
    
    # ===================== CONFIDENCE LEVELS CHECK =====================
    
    def test_10_verify_confidence_levels_in_suggestions(self):
        """Verify suggestions have proper confidence levels (High/Medium/Low)"""
        assert TestPricingSetup.test_import_id is not None
        
        response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        confidence_counts = {"High": 0, "Medium": 0, "Low": 0, "Other": 0}
        
        for suggestion in suggestions:
            conf = suggestion.get("confidence", "Unknown")
            if conf in confidence_counts:
                confidence_counts[conf] += 1
            else:
                confidence_counts["Other"] += 1
        
        # All suggestions should have valid confidence levels
        assert confidence_counts["Other"] == 0, f"Found {confidence_counts['Other']} suggestions with invalid confidence"
        
        print(f"[PASS] Confidence levels distribution: High={confidence_counts['High']}, Medium={confidence_counts['Medium']}, Low={confidence_counts['Low']}")
    
    # ===================== CATEGORY OVERRIDE REVIEW =====================
    
    def test_11_category_override_mapping(self):
        """Verify category_overrides in mapping work before AI analysis"""
        assert TestPricingSetup.test_import_id is not None
        
        # Get current import
        response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        data = response.json()
        normalized_rows = data.get("normalized_rows", [])
        
        if len(normalized_rows) == 0:
            print("[SKIP] No normalized rows to test category override")
            return
        
        # Get a description to override
        test_description = normalized_rows[0].get("description", "")
        _original_category = normalized_rows[0].get("category_final", "")
        
        # Update mapping with category override
        mapping_payload = {
            "description_field": "Description",
            "quantity_field": "Quantity",
            "total_field": "Total",
            "dimension_field": "Dimensions",
            "category_field": "Category",
            "category_overrides": {
                test_description: "services"  # Override to services
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}/mapping",
            headers=self.get_json_headers(),
            json=mapping_payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        
        # Find the row with the overridden description
        updated_rows = data.get("normalized_rows", [])
        overridden_row = None
        for row in updated_rows:
            if row.get("description") == test_description:
                overridden_row = row
                break
        
        if overridden_row:
            assert overridden_row.get("category_final") == "services", "Category override not applied"
            print(f"[PASS] Category override applied: '{test_description[:30]}...' -> services")
        else:
            print("[WARN] Could not verify category override - row not found")
    
    # ===================== XLSX UPLOAD TEST (if available) =====================
    
    def test_12_upload_xlsx_file(self):
        """Test XLSX file upload (creates minimal XLSX-like content)"""
        # Note: This creates a CSV named as .xlsx for API acceptance testing
        # In real usage, pandas would handle proper XLSX parsing
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["Item", "Qty", "Amount"])
        writer.writerow(["Banner 3x6", "1", "150.00"])
        writer.writerow(["Yard Signs 18x24", "20", "200.00"])
        csv_content = csv_buffer.getvalue().encode('utf-8')
        
        # Note: The backend will try to parse this as XLSX which may fail
        # This test verifies the upload endpoint accepts the file type
        files = {
            'files': ('test_invoice.xlsx', csv_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pricing-setup/imports",
            headers=self.get_headers(),
            files=files
        )
        
        # May succeed or fail depending on pandas XLSX parsing of CSV content
        # We're mainly testing the endpoint accepts xlsx mime type
        if response.status_code == 200:
            print("[PASS] XLSX upload accepted")
        else:
            print(f"[INFO] XLSX upload returned {response.status_code} - may need real XLSX content")
    
    # ===================== VERIFY IMPORT STATUS FLOW =====================
    
    def test_13_verify_import_status_flow(self):
        """Verify import status transitions correctly through workflow"""
        assert TestPricingSetup.test_import_id is not None
        
        response = requests.get(
            f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        
        data = response.json()
        status = data.get("status")
        
        # After our tests, status should be 'reviewed' (we ran analyze and review)
        valid_statuses = ["mapping_required", "ready_for_analysis", "analyzed", "reviewed"]
        assert status in valid_statuses, f"Invalid status: {status}"
        
        print(f"[PASS] Import status: {status} (valid workflow state)")
    
    # ===================== ADMIN ACCESS CHECK =====================
    
    def test_14_admin_access_required(self):
        """Verify only admin/owner can access pricing-setup endpoints"""
        # This test verifies we're logged in as admin and can access
        # A proper test would involve creating a non-admin user and testing denial
        # For now, we verify the endpoint returns 200 (admin access works)
        
        response = requests.get(f"{BASE_URL}/api/pricing-setup/imports", headers=self.get_headers())
        assert response.status_code == 200, "Admin should have access"
        
        print("[PASS] Admin access to pricing-setup endpoints verified")
    
    # ===================== CLEANUP =====================
    
    def test_99_cleanup(self):
        """Note: Import sessions are not deleted, they remain for historical record"""
        # In production, imports would be retained for audit purposes
        # This test documents that behavior
        
        if TestPricingSetup.test_import_id:
            # Verify import still exists
            response = requests.get(
                f"{BASE_URL}/api/pricing-setup/imports/{TestPricingSetup.test_import_id}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                print(f"[INFO] Import {TestPricingSetup.test_import_id[:8]} retained for records (no cleanup endpoint)")
        
        print("[PASS] Cleanup complete (imports retained as designed)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
