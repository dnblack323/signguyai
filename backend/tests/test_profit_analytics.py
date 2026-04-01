"""
Test Profit & Margin Analytics Dashboard APIs
Tests: dashboard endpoint, filters, preferences, exports, tenant isolation, access control
"""
import pytest
import requests
import os
from backend.tests.test_credentials_helper import ( PRODUCTION_OWNER_EMAIL, PRODUCTION_OWNER_PASSWORD, LEGACY_ADMIN_EMAIL, LEGACY_ADMIN_PASSWORD, DEV_TEST_EMAIL, DEV_TEST_PASSWORD, FALLBACK_TEST_EMAIL, FALLBACK_TEST_PASSWORD, SYNTHETIC_OWNER_EMAIL, SYNTHETIC_OWNER_PASSWORD )

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = LEGACY_ADMIN_EMAIL
ADMIN_PASSWORD = LEGACY_ADMIN_PASSWORD


@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Requests session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    })
    return session


class TestProfitAnalyticsDashboard:
    """Tests for GET /api/profit-analytics/dashboard"""
    
    def test_dashboard_returns_all_required_fields(self, api_client):
        """Dashboard endpoint returns metrics, category_rows, job_rows, customer_rows, trend_rows, low_margin_jobs, preferences"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=30d")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Required fields
        assert "metrics" in data
        assert "category_rows" in data
        assert "job_rows" in data
        assert "customer_rows" in data
        assert "trend_rows" in data
        assert "low_margin_jobs" in data
        assert "preferences" in data
        
        # Metrics structure
        metrics = data["metrics"]
        assert "revenue_this_month" in metrics
        assert "profit_this_month" in metrics
        assert "average_job_value" in metrics
        assert "average_profit_margin" in metrics
    
    def test_dashboard_with_30d_range(self, api_client):
        """Dashboard returns data for 30-day range"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=30d")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("trend_rows"), list)
    
    def test_dashboard_with_90d_range(self, api_client):
        """Dashboard returns data for 90-day range"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=90d")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("trend_rows"), list)
    
    def test_dashboard_with_this_year_range(self, api_client):
        """Dashboard returns data for this year range"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=this_year")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data.get("trend_rows"), list)
    
    def test_dashboard_with_custom_date_range(self, api_client):
        """Dashboard respects custom date range filters"""
        response = api_client.get(
            f"{BASE_URL}/api/profit-analytics/dashboard?range_key=custom&start_date=2026-01-01&end_date=2026-12-31"
        )
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "job_rows" in data
    
    def test_dashboard_with_category_filter(self, api_client):
        """Dashboard filters by category"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=30d&category=banners")
        assert response.status_code == 200
        data = response.json()
        # If there's data, all category_rows should be banners
        for row in data.get("category_rows", []):
            assert row["category"] == "banners"
    
    def test_dashboard_without_auth_fails(self):
        """Dashboard requires authentication"""
        response = requests.get(f"{BASE_URL}/api/profit-analytics/dashboard")
        assert response.status_code == 401


class TestProfitAnalyticsPreferences:
    """Tests for PUT /api/profit-analytics/preferences"""
    
    def test_save_preferences(self, api_client):
        """Preferences save and persist correctly"""
        preferences_payload = {
            "simple_mode": True,
            "widget_order": ["profit_by_category", "revenue_trend", "top_customers", "low_margin_jobs", "average_job_value"],
            "enabled_widgets": {
                "revenue_trend": True,
                "profit_by_category": True,
                "top_customers": True,
                "low_margin_jobs": False,
                "average_job_value": True
            }
        }
        
        response = api_client.put(
            f"{BASE_URL}/api/profit-analytics/preferences",
            json=preferences_payload
        )
        assert response.status_code == 200
        
        saved = response.json()
        assert saved["simple_mode"] == True
        assert "profit_by_category" in saved["widget_order"]
        assert saved["enabled_widgets"]["low_margin_jobs"] == False
    
    def test_preferences_persist_in_dashboard(self, api_client):
        """Preferences are returned in dashboard response"""
        # Save preferences
        api_client.put(
            f"{BASE_URL}/api/profit-analytics/preferences",
            json={"simple_mode": True}
        )
        
        # Get dashboard and verify preferences included
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=30d")
        assert response.status_code == 200
        data = response.json()
        
        preferences = data.get("preferences", {})
        assert preferences.get("simple_mode") == True
    
    def test_preferences_reset_to_defaults(self, api_client):
        """Can reset preferences to default values"""
        default_widgets = ["revenue_trend", "profit_by_category", "top_customers", "low_margin_jobs", "average_job_value"]
        
        response = api_client.put(
            f"{BASE_URL}/api/profit-analytics/preferences",
            json={
                "simple_mode": False,
                "widget_order": default_widgets,
                "enabled_widgets": {w: True for w in default_widgets}
            }
        )
        assert response.status_code == 200
        
        saved = response.json()
        assert saved["simple_mode"] == False


class TestProfitAnalyticsExport:
    """Tests for GET /api/profit-analytics/export"""
    
    def test_csv_export(self, api_client):
        """CSV export returns downloadable file"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/export?format=csv&range_key=30d")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        assert "attachment" in response.headers.get("Content-Disposition", "")
        
        # Verify CSV content has headers
        content = response.text
        assert "job_id" in content or "job_name" in content
    
    def test_xlsx_export(self, api_client):
        """XLSX export returns downloadable file"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/export?format=xlsx&range_key=30d")
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers.get("Content-Type", "")
        assert "attachment" in response.headers.get("Content-Disposition", "")
        
        # Verify non-empty content
        assert len(response.content) > 0
    
    def test_pdf_export(self, api_client):
        """PDF export returns downloadable file"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/export?format=pdf&range_key=30d")
        assert response.status_code == 200
        assert "pdf" in response.headers.get("Content-Type", "")
        assert "attachment" in response.headers.get("Content-Disposition", "")
        
        # Verify PDF header
        assert response.content[:4] == b'%PDF'
    
    def test_export_with_filters(self, api_client):
        """Export respects time range and category filters"""
        response = api_client.get(
            f"{BASE_URL}/api/profit-analytics/export?format=csv&range_key=custom&start_date=2026-01-01&end_date=2026-12-31&category=banners"
        )
        assert response.status_code == 200
    
    def test_invalid_export_format(self, api_client):
        """Invalid export format returns 400"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/export?format=invalid&range_key=30d")
        assert response.status_code == 400


class TestProfitAnalyticsDataIntegrity:
    """Tests for data derivation and calculations"""
    
    def test_job_row_structure(self, api_client):
        """Job rows have correct fields derived from cost_snapshot"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=this_year")
        assert response.status_code == 200
        data = response.json()
        
        for job in data.get("job_rows", []):
            # Required job row fields
            assert "job_id" in job
            assert "job_name" in job
            assert "customer_name" in job
            assert "revenue" in job
            assert "total_cost" in job
            assert "profit" in job
            assert "profit_margin" in job
            assert "underpriced" in job
            assert "benchmark_margin" in job
    
    def test_category_row_structure(self, api_client):
        """Category rows have correct aggregate fields"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=this_year")
        assert response.status_code == 200
        data = response.json()
        
        for category in data.get("category_rows", []):
            assert "category" in category
            assert "category_label" in category
            assert "revenue" in category
            assert "total_cost" in category
            assert "profit" in category
            assert "average_margin" in category
            assert "job_count" in category
    
    def test_customer_row_structure(self, api_client):
        """Customer rows have correct aggregate fields"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=this_year")
        assert response.status_code == 200
        data = response.json()
        
        for customer in data.get("customer_rows", []):
            assert "customer_id" in customer
            assert "customer_name" in customer
            assert "total_revenue" in customer
            assert "total_profit" in customer
            assert "average_margin" in customer
            assert "total_jobs" in customer
    
    def test_underpriced_detection(self, api_client):
        """Low margin jobs are flagged correctly"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=this_year")
        assert response.status_code == 200
        data = response.json()
        
        # low_margin_jobs should contain jobs where underpriced=true or profit_margin < 25
        for job in data.get("low_margin_jobs", []):
            is_underpriced = job.get("underpriced", False)
            margin = job.get("profit_margin", 100)
            assert is_underpriced or margin < 25, f"Job {job['job_name']} should be low margin"


class TestProfitAnalyticsTenantIsolation:
    """Tests for tenant data isolation"""
    
    def test_dashboard_scoped_to_tenant(self, api_client):
        """Dashboard data is scoped to authenticated user's tenant"""
        response = api_client.get(f"{BASE_URL}/api/profit-analytics/dashboard?range_key=30d")
        assert response.status_code == 200
        data = response.json()
        
        # Preferences should include tenant_id
        preferences = data.get("preferences", {})
        assert "tenant_id" in preferences
    
    def test_preferences_scoped_to_tenant(self, api_client):
        """Preferences are tenant-scoped"""
        response = api_client.put(
            f"{BASE_URL}/api/profit-analytics/preferences",
            json={"simple_mode": False}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "tenant_id" in data


class TestNoRegressionOnExistingEndpoints:
    """Verify no regression on related endpoints"""
    
    def test_pricing_defaults_still_works(self, api_client):
        """GET /api/pricing/defaults still returns proper data"""
        response = api_client.get(f"{BASE_URL}/api/pricing/defaults")
        assert response.status_code == 200
        
        data = response.json()
        assert "materials" in data
        assert "category_defaults" in data
        assert "selling_price_benchmarks" in data
        assert len(data["materials"]) > 0
    
    def test_pricing_calculate_still_works(self, api_client):
        """POST /api/pricing/calculate still calculates correctly"""
        response = api_client.post(
            f"{BASE_URL}/api/pricing/calculate",
            json={
                "category": "digital_print",
                "pricing_data": {
                    "width_inches": 24,
                    "length_inches": 36,
                    "print_material": "banner_13oz"
                },
                "quantity": 1
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "selling_price" in data
        assert "profit_margin_percent" in data
        assert data["selling_price"] > 0
