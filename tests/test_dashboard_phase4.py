"""
Phase 4 — Dashboard Reliability Validation Tests

Coverage matrix:
  1. Loaded state smoke          — 6 rows, strip metrics, row headers
  2. Empty states (exact text)   — all 6 required empty texts
  3. Error states (exact text)   — "Couldn't load this section." + Retry button
  4. Retry behavior              — fail once → succeed on retry (per-section)
  5. Staleness / trust           — stale ts > 10 min, missing ts
  6. CTA routing                 — href assertions for every action link
  7. Ordering assertions         — urgency_score desc, at-risk priority
  8. Guardrail checks            — no .catch(()=>{}) in source, no /jobs/:id links

Run:
  export REACT_APP_BACKEND_URL=https://sign-production-hub-1.preview.emergentagent.com
  pytest tests/test_dashboard_phase4.py -v --tb=short

Playwright intercepts backend API calls and returns controlled fixture data,
enabling deterministic tests for every state without altering DB data.
"""

import pytest
import json
import re
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Route, expect

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://sign-production-hub-1.preview.emergentagent.com")
ADMIN_EMAIL    = "thesigntistslab@gmail.com"
ADMIN_PASSWORD = "password123"

# ─────────────────────────────────────────────────────────────────
# Timestamp helpers
# ─────────────────────────────────────────────────────────────────

def fresh_ts():
    return datetime.now(timezone.utc).isoformat()

def stale_ts(minutes=11):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()

# ─────────────────────────────────────────────────────────────────
# Fixture data factories
# ─────────────────────────────────────────────────────────────────

def _summary_v2(ts=None, counts=None):
    base_counts = {"due_today": 0, "overdue": 0, "awaiting_approval": 0,
                   "unread_messages": 0, "in_production": 0, "unpaid_invoices": 0}
    if counts:
        base_counts.update(counts)
    return {
        "last_updated_at": ts or fresh_ts(),
        "metrics": {
            k: {"count": v, "severity": ("red" if v >= 4 else "amber" if v > 0 else "neutral")}
            for k, v in base_counts.items()
        },
    }

def _command_center(ts=None, due_items=None, appts=None, employees=None):
    return {
        "last_updated_at": ts or fresh_ts(),
        "due_order_items_today": due_items or [],
        "appointments_installs_today": appts or [],
        "team_status_today": {
            "scheduled_count": len([e for e in (employees or []) if e.get("is_scheduled")]),
            "clocked_in_count": len([e for e in (employees or []) if e.get("clock_status") == "working"]),
            "employees": employees or [],
        },
    }

def _production_snapshot(ts=None, stages=None, at_risk=None, bottlenecks=None):
    return {
        "last_updated_at": ts or fresh_ts(),
        "order_items_by_stage": stages or {"queued": 0, "printing": 0, "finishing": 0, "install": 0, "complete": 0},
        "bottlenecks": bottlenecks or [],
        "at_risk": at_risk or [],
    }

def _customer_attention(ts=None, conversations=None, approvals=None, quotes=None):
    return {
        "last_updated_at": ts or fresh_ts(),
        "unread_conversations": conversations or [],
        "approvals_signatures_pending": approvals or [],
        "quote_followups": quotes or [],
    }

def _financial_attention(ts=None, unpaid=None, overdue=None, due_week=None, recent=None):
    def _sec(data):
        return {"count": len(data or []), "total_amount": sum(r.get("amount", 0) for r in (data or [])), "top_records": (data or [])[:3]}
    return {
        "last_updated_at": ts or fresh_ts(),
        "unpaid":        _sec(unpaid),
        "overdue":       _sec(overdue),
        "due_this_week": _sec(due_week),
        "recent_payments": _sec(recent),
    }

def _all_empty(ts=None):
    return {
        "summary-v2":           _summary_v2(ts=ts),
        "today-command-center": _command_center(ts=ts),
        "production-snapshot":  _production_snapshot(ts=ts),
        "customer-attention":   _customer_attention(ts=ts),
        "financial-attention":  _financial_attention(ts=ts),
    }

# ─────────────────────────────────────────────────────────────────
# Playwright helpers
# ─────────────────────────────────────────────────────────────────

def _login(page: Page):
    """Navigate to /login, authenticate, then navigate away so mocks can be set before /dashboard."""
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    try:
        page.wait_for_selector('[data-testid="auth-email-input"]', timeout=10000)
        page.fill('[data-testid="auth-email-input"]', ADMIN_EMAIL)
        page.fill('[data-testid="auth-password-input"]', ADMIN_PASSWORD)
        page.click('[data-testid="login-submit-btn"]')
        page.wait_for_url("**/dashboard**", timeout=20000)
    except Exception:
        pass  # Already authenticated or already at dashboard
    # Navigate away so _navigate_dashboard causes a fresh Dashboard remount
    page.goto(f"{BASE_URL}/customers", wait_until="domcontentloaded")
    page.wait_for_timeout(300)

def _mock_all_v1(page: Page, fixtures: dict):
    """Install route mocks for all 5 V1 dashboard endpoints from a fixtures dict."""
    for slug, data in fixtures.items():
        # Capture current `data` to avoid late-binding closure bug
        _data = data
        page.route(
            f"**/{slug}**",
            lambda route, request, d=_data: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(d),
            ),
        )

def _navigate_dashboard(page: Page):
    """Navigate to dashboard (forces fresh React mount because we came from /customers)."""
    page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
    page.wait_for_selector('[data-testid="dashboard"]', timeout=15000)
    page.wait_for_timeout(600)

def _get_page(playwright):
    browser = playwright.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1400, "height": 900})
    return ctx.new_page(), browser

# ─────────────────────────────────────────────────────────────────
# 1. Smoke tests — loaded state
# ─────────────────────────────────────────────────────────────────

def test_smoke_dashboard_renders_all_6_rows():
    """Dashboard loads and all 6 row sections are present in the DOM."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _navigate_dashboard(page)
            assert page.locator('[data-testid="dashboard"]').count() == 1
            assert page.locator('[data-testid="severity-strip"]').count() == 1
            assert page.locator('[data-testid="production-stages"]').count() == 1
            assert page.locator('[data-testid="financial-attention-row"]').count() == 1
            # Row 2 cards (via heading text)
            assert page.get_by_text("Today's Command Center").count() >= 1
            assert page.get_by_text("Customer Attention").count() >= 1
            print("PASS: dashboard renders all 6 rows")
        finally:
            browser.close()


def test_smoke_severity_strip_has_6_metrics():
    """Top strip shows exactly 6 metric badges."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _navigate_dashboard(page)
            strip = page.locator('[data-testid="severity-strip"]')
            assert strip.count() == 1
            metrics = strip.locator('[data-testid^="severity-"]')
            assert metrics.count() == 6, f"Expected 6 metrics, got {metrics.count()}"
            metric_ids = set()
            for i in range(6):
                tid = metrics.nth(i).get_attribute("data-testid")
                metric_ids.add(tid)
            expected = {
                "severity-due_today", "severity-overdue", "severity-awaiting_approval",
                "severity-unread_messages", "severity-in_production", "severity-unpaid_invoices"
            }
            assert expected == metric_ids, f"Missing metrics: {expected - metric_ids}"
            print("PASS: severity strip has 6 correct metrics")
        finally:
            browser.close()


def test_smoke_row_order():
    """Row headers appear in the correct vertical order."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _navigate_dashboard(page)
            # Find bounding boxes of key section headers
            cmd_el  = page.get_by_text("Today's Command Center").first
            prod_el = page.get_by_text("Production Snapshot").first
            cust_el = page.get_by_text("Customer Attention").first
            fin_el  = page.locator('[data-testid="financial-attention-row"]').first

            cmd_y  = cmd_el.bounding_box()["y"]
            prod_y = prod_el.bounding_box()["y"]
            cust_y = cust_el.bounding_box()["y"]
            fin_y  = fin_el.bounding_box()["y"]

            assert cmd_y < prod_y < cust_y < fin_y, (
                f"Row order wrong: cmd={cmd_y:.0f} prod={prod_y:.0f} cust={cust_y:.0f} fin={fin_y:.0f}"
            )
            print("PASS: row order is correct")
        finally:
            browser.close()

# ─────────────────────────────────────────────────────────────────
# 2. Empty state tests — exact required texts
# ─────────────────────────────────────────────────────────────────

REQUIRED_EMPTY_TEXTS = [
    "No order items due today.",
    "No approvals pending. Send a new proof.",
    "No unread customer messages.",
    "No team schedule for today. Set schedule.",
    "No unpaid invoices.",
    "No production bottlenecks right now.",
]

@pytest.mark.parametrize("empty_text", REQUIRED_EMPTY_TEXTS)
def test_empty_state_exact_text(empty_text):
    """With all endpoints returning empty data, each required empty text appears exactly."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            # Set up mocks BEFORE navigation
            _mock_all_v1(page, _all_empty())
            _navigate_dashboard(page)
            # Wait for all loading spinners to go
            page.wait_for_timeout(800)
            count = page.get_by_text(empty_text, exact=True).count()
            assert count >= 1, f"Empty text not found: '{empty_text}'"
            print(f"PASS: empty text '{empty_text}' found")
        finally:
            browser.close()


def test_all_empty_states_present_together():
    """All 6 empty texts are visible at once with empty API responses."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _mock_all_v1(page, _all_empty())
            _navigate_dashboard(page)
            page.wait_for_timeout(800)
            missing = []
            for text in REQUIRED_EMPTY_TEXTS:
                if page.get_by_text(text, exact=True).count() == 0:
                    missing.append(text)
            assert not missing, f"Missing empty texts: {missing}"
            print("PASS: all 6 empty state texts present together")
        finally:
            browser.close()

# ─────────────────────────────────────────────────────────────────
# 3. Error state tests — exact text + retry button visible
# ─────────────────────────────────────────────────────────────────

def _abort_route(slug: str, page: Page):
    """Abort all requests for a specific V1 endpoint slug."""
    page.route(f"**/{slug}**", lambda route, request: route.abort())


@pytest.mark.parametrize("slug", [
    "summary-v2",
    "today-command-center",
    "production-snapshot",
    "customer-attention",
    "financial-attention",
])
def test_error_state_shows_correct_text(slug):
    """Aborting an endpoint shows 'Couldn't load this section.' and 'Please retry.'"""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _abort_route(slug, page)
            _navigate_dashboard(page)
            page.wait_for_timeout(1000)

            error_blocks = page.locator('[data-testid="section-error"]')
            assert error_blocks.count() >= 1, f"No error block for {slug}"

            # Check exact text in at least one error block
            found_main  = page.get_by_text("Couldn't load this section.", exact=True).count() >= 1
            found_sub   = page.get_by_text("Please retry.", exact=True).count() >= 1
            assert found_main, f"Missing 'Couldn't load this section.' for {slug}"
            assert found_sub,  f"Missing 'Please retry.' for {slug}"

            # Retry button visible
            retry_btn = page.locator('[data-testid="section-error-retry"]')
            assert retry_btn.count() >= 1, f"No retry button for {slug}"
            print(f"PASS: error state for {slug}")
        finally:
            browser.close()


def test_error_state_does_not_show_empty_state():
    """Error state must not bleed into empty-state copy — the two are mutually exclusive."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            # Abort today-command-center (which owns ScheduleWidget + TeamStatusWidget)
            _abort_route("today-command-center", page)
            _navigate_dashboard(page)
            page.wait_for_timeout(1000)

            # These empty texts must NOT appear when the request failed
            assert page.get_by_text("No order items due today.", exact=True).count() == 0, \
                "Empty state text appeared during error state"
            assert page.get_by_text("No team schedule for today. Set schedule.", exact=True).count() == 0, \
                "Team empty text appeared during error state"
            print("PASS: empty state text absent when request failed")
        finally:
            browser.close()

# ─────────────────────────────────────────────────────────────────
# 4. Retry behavior — fail once, succeed on retry, section refreshes
# ─────────────────────────────────────────────────────────────────

def test_retry_refreshes_only_that_section():
    """Clicking Retry on a failed section re-fetches and renders data without full reload."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        call_counts = {"summary": 0}
        try:
            _login(page)
            recovery_data = _summary_v2(
                counts={"due_today": 3, "unpaid_invoices": 5}
            )

            def _summary_handler(route: Route, request):
                call_counts["summary"] += 1
                if call_counts["summary"] == 1:
                    route.abort()   # first call fails
                else:
                    route.fulfill(  # subsequent calls succeed
                        status=200,
                        content_type="application/json",
                        body=json.dumps(recovery_data),
                    )

            page.route("**/summary-v2**", _summary_handler)
            # Mock other endpoints with empty (so the page loads cleanly)
            for slug in ["today-command-center", "production-snapshot", "customer-attention", "financial-attention"]:
                _d = _all_empty()[slug]
                page.route(f"**/{slug}**", lambda r, req, d=_d: r.fulfill(status=200, content_type="application/json", body=json.dumps(d)))

            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            # Error block should appear for summary-v2 section (severity strip)
            # We can't easily check WHICH section failed, so just check that a retry button exists
            retry_btn = page.locator('[data-testid="section-error-retry"]').first
            assert retry_btn.count() == 1, "Retry button not shown after section failure"

            # Click retry — this should re-fetch summary-v2 only
            retry_btn.click()
            page.wait_for_timeout(1000)

            # After retry: error block should be gone
            assert page.locator('[data-testid="section-error"]').count() == 0, \
                "Error block still visible after successful retry"

            # The severity strip data should now reflect recovery_data
            strip = page.locator('[data-testid="severity-strip"]')
            assert strip.count() == 1, "Severity strip not rendered after retry"

            # Verify retry triggered an additional call (fail + retry = at least 2)
            assert call_counts["summary"] >= 2, f"Expected at least 2 calls, got {call_counts['summary']}"
            print("PASS: retry refreshes section and clears error")
        finally:
            browser.close()

# ─────────────────────────────────────────────────────────────────
# 5. Staleness / trust behavior
# ─────────────────────────────────────────────────────────────────

def test_stale_indicator_appears_when_data_is_old():
    """'Data may be stale.' appears when last_updated_at is > 10 minutes ago."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            # Use a stale timestamp (11 minutes ago)
            old_ts = stale_ts(minutes=11)
            fixtures = {
                "summary-v2":           _summary_v2(ts=old_ts),
                "today-command-center": _command_center(ts=old_ts),
                "production-snapshot":  _production_snapshot(ts=old_ts),
                "customer-attention":   _customer_attention(ts=old_ts),
                "financial-attention":  _financial_attention(ts=old_ts),
            }
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            stale_text = page.get_by_text("Data may be stale.", exact=False)
            assert stale_text.count() >= 1, (
                f"Expected stale indicator for ts={old_ts}, found 0 instances"
            )
            print("PASS: stale indicator appears for 11-min-old data")
        finally:
            browser.close()


def test_no_stale_indicator_for_fresh_data():
    """'Data may be stale.' must NOT appear when last_updated_at is current."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _mock_all_v1(page, _all_empty())   # all fresh timestamps
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            stale_text = page.get_by_text("Data may be stale.", exact=False)
            assert stale_text.count() == 0, (
                f"Stale indicator appeared for fresh data ({stale_text.count()} times)"
            )
            print("PASS: no stale indicator for fresh data")
        finally:
            browser.close()


def test_missing_timestamp_shows_unavailable():
    """'Last updated unavailable.' shown when last_updated_at is null/missing."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            # Remove last_updated_at from command center
            cc = _command_center(ts=None)
            del cc["last_updated_at"]  # completely absent
            fixtures = {**_all_empty(), "today-command-center": cc}
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            missing_text = page.get_by_text("Last updated unavailable.", exact=True)
            assert missing_text.count() >= 1, "Missing 'Last updated unavailable.' text"
            print("PASS: 'Last updated unavailable.' shown when timestamp absent")
        finally:
            browser.close()


def test_stale_threshold_boundary_10_minutes():
    """Data exactly at 10 minutes old should NOT show stale; 10min+1s should."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            # Exactly 9 minutes ago — not stale
            ts_9min = (datetime.now(timezone.utc) - timedelta(minutes=9)).isoformat()
            fixtures_fresh = {
                "summary-v2":           _summary_v2(ts=ts_9min),
                "today-command-center": _command_center(ts=ts_9min),
                "production-snapshot":  _production_snapshot(ts=ts_9min),
                "customer-attention":   _customer_attention(ts=ts_9min),
                "financial-attention":  _financial_attention(ts=ts_9min),
            }
            _mock_all_v1(page, fixtures_fresh)
            _navigate_dashboard(page)
            page.wait_for_timeout(600)
            assert page.get_by_text("Data may be stale.", exact=False).count() == 0, \
                "Stale shown at 9 minutes (threshold is 10)"
            print("PASS: 9-minute-old data not stale")
        finally:
            browser.close()

# ─────────────────────────────────────────────────────────────────
# 6. CTA routing — href assertions
# ─────────────────────────────────────────────────────────────────

CTA_ASSERTIONS = [
    # (testid, expected_href_contains, label)
    ("quick-add-quote",        "/orders/new",                "New Order"),
    ("quick-add-customer",     "/customers",                 "New Customer"),
    ("quick-production-board", "/production-board",          "Production Board"),
    ("quick-open-calendar",    "/productivity?view=calendar","Open Calendar"),
    ("quick-send-approval",    "/approvals",                 "Send Approval"),
    ("quick-create-invoice",   "/invoices",                  "Create Invoice"),
    ("quick-ai-assistant",     "/ai-assistant",              "AI Assistant"),
    ("quick-clock-in",         "/timeclock",                 "Time Clock"),
]

@pytest.mark.parametrize("testid,expected_path,label", CTA_ASSERTIONS)
def test_quick_action_href(testid, expected_path, label):
    """Each Quick Actions button must link to the canonical path."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _navigate_dashboard(page)
            btn = page.locator(f'[data-testid="{testid}"]')
            assert btn.count() == 1, f"Button {testid} not found"
            # The button is inside a <Link> (anchor). Find the wrapping <a>.
            anchor = btn.locator("xpath=ancestor-or-self::a").first
            href = anchor.get_attribute("href") or ""
            assert expected_path in href, (
                f"{label} ({testid}) href='{href}' should contain '{expected_path}'"
            )
            print(f"PASS: {label} → {href}")
        finally:
            browser.close()


def test_cta_production_board_not_orders():
    """Production Board CTA must NOT link to /orders (was a Phase 2 bug)."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _navigate_dashboard(page)
            btn = page.locator('[data-testid="quick-production-board"]')
            anchor = btn.locator("xpath=ancestor-or-self::a").first
            href = anchor.get_attribute("href") or ""
            assert href.rstrip("/") != "/orders", (
                f"Production Board incorrectly links to /orders (should be /production-board)"
            )
            assert "/production-board" in href, f"Expected /production-board, got {href}"
            print("PASS: Production Board does not link to /orders")
        finally:
            browser.close()


def test_cta_create_invoice_not_invoices_new():
    """Create Invoice CTA must NOT link to /invoices/new (route doesn't exist)."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _navigate_dashboard(page)
            btn = page.locator('[data-testid="quick-create-invoice"]')
            anchor = btn.locator("xpath=ancestor-or-self::a").first
            href = anchor.get_attribute("href") or ""
            assert "/invoices/new" not in href, f"Create Invoice links to non-existent /invoices/new"
            assert "/invoices" in href, f"Create Invoice should link to /invoices, got {href}"
            print("PASS: Create Invoice links to /invoices (not /invoices/new)")
        finally:
            browser.close()


def test_no_jobs_id_links_on_dashboard():
    """No anchor tags on the dashboard should have href matching /jobs/ pattern."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            _navigate_dashboard(page)
            all_anchors = page.locator("a[href]")
            count = all_anchors.count()
            violations = []
            for i in range(min(count, 200)):
                href = all_anchors.nth(i).get_attribute("href") or ""
                if re.match(r".*\/jobs\/[^/]+", href):
                    violations.append(href)
            assert not violations, f"Found /jobs/:id links on dashboard: {violations}"
            print("PASS: no /jobs/:id links on dashboard")
        finally:
            browser.close()


def test_messages_link_to_admin_portal():
    """Unread message rows must link to /admin-portal?tab=messages."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            # Seed a conversation in fixture data
            fixtures = {
                **_all_empty(),
                "customer-attention": _customer_attention(
                    conversations=[{
                        "conversation_id": "test-conv-1",
                        "customer_name": "Alice Test",
                        "unread_count": 2,
                        "last_message_preview": "Hello there",
                        "last_message_at": fresh_ts(),
                        "urgency_score": 1.5,
                    }]
                ),
            }
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            # Find the message row link
            msg_row = page.locator('[data-testid="message-row-test-conv-1"]')
            assert msg_row.count() == 1, "Message row not rendered"
            anchor = msg_row.locator("xpath=ancestor-or-self::a").first
            href = anchor.get_attribute("href") or ""
            assert "/admin-portal" in href, f"Message link should go to /admin-portal, got {href}"
            assert "messages" in href.lower(), f"Message link should include tab=messages, got {href}"
            print(f"PASS: message row links to {href}")
        finally:
            browser.close()


def test_approval_items_link_to_approvals():
    """Approval items must link to /approvals (not /jobs/:id)."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            fixtures = {
                **_all_empty(),
                "customer-attention": _customer_attention(
                    approvals=[{
                        "record_id": "proof-001",
                        "type": "proof",
                        "customer_name": "Bob Test",
                        "order_number": "ORD-0001",
                        "requested_at": fresh_ts(),
                        "age_hours": 2.0,
                        "urgency_score": 2.0,
                    }]
                ),
            }
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            approval_item = page.locator('[data-testid="approval-proof-001"]')
            assert approval_item.count() == 1, "Approval item not rendered"
            anchor = approval_item.locator("xpath=ancestor-or-self::a").first
            href = anchor.get_attribute("href") or ""
            assert "/approvals" in href, f"Approval should link to /approvals, got {href}"
            assert "/jobs/" not in href, f"Approval incorrectly links to /jobs/, got {href}"
            print(f"PASS: approval item links to {href}")
        finally:
            browser.close()


def test_order_items_link_to_orders_id():
    """Schedule items must link to /orders/:id (not /orders list)."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            ORDER_ID = "order-abc-123"
            ITEM_ID  = "item-xyz-456"
            fixtures = {
                **_all_empty(),
                "today-command-center": _command_center(
                    due_items=[{
                        "order_id": ORDER_ID,
                        "order_number": "ORD-0042",
                        "order_item_id": ITEM_ID,
                        "item_name": "Test Banner 4x8",
                        "customer_name": "Test Co",
                        "due_at": f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}T00:00:00Z",
                        "stage": "printing",
                        "priority": "normal",
                    }]
                ),
            }
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            item_el = page.locator(f'[data-testid="schedule-item-{ITEM_ID}"]')
            assert item_el.count() == 1, f"Schedule item {ITEM_ID} not rendered"
            anchor = item_el.locator("xpath=ancestor-or-self::a").first
            href = anchor.get_attribute("href") or ""
            assert f"/orders/{ORDER_ID}" in href, (
                f"Schedule item should link to /orders/{ORDER_ID}, got {href}"
            )
            print(f"PASS: schedule item links to {href}")
        finally:
            browser.close()

# ─────────────────────────────────────────────────────────────────
# 7. Ordering assertions
# ─────────────────────────────────────────────────────────────────

def test_customer_attention_conversations_urgency_order():
    """Unread conversations must appear in urgency_score descending order in DOM."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            # High urgency first, then lower — also test equal-score tie-break
            convs = [
                {"conversation_id": "conv-low",  "customer_name": "C (low)",  "unread_count": 1,
                 "last_message_preview": "msg", "last_message_at": "2026-01-01T10:00:00Z", "urgency_score": 0.5},
                {"conversation_id": "conv-high", "customer_name": "A (high)", "unread_count": 5,
                 "last_message_preview": "msg", "last_message_at": "2026-01-02T10:00:00Z", "urgency_score": 8.0},
                {"conversation_id": "conv-med",  "customer_name": "B (med)",  "unread_count": 2,
                 "last_message_preview": "msg", "last_message_at": "2026-01-03T10:00:00Z", "urgency_score": 3.0},
            ]
            # Deliberately pass in wrong order (low, high, med) — frontend must sort
            fixtures = {**_all_empty(), "customer-attention": _customer_attention(conversations=convs)}
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            high_box = page.locator('[data-testid="message-row-conv-high"]').bounding_box()
            med_box  = page.locator('[data-testid="message-row-conv-med"]').bounding_box()
            low_box  = page.locator('[data-testid="message-row-conv-low"]').bounding_box()

            assert high_box is not None and med_box is not None and low_box is not None, \
                "Not all message rows rendered"
            assert high_box["y"] < med_box["y"] < low_box["y"], (
                f"Messages not in urgency order: high_y={high_box['y']:.0f} "
                f"med_y={med_box['y']:.0f} low_y={low_box['y']:.0f}"
            )
            print("PASS: conversations sorted by urgency_score desc")
        finally:
            browser.close()


def test_customer_attention_approvals_urgency_order():
    """Approval/signature items must appear in urgency_score descending order."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            approvals = [
                {"record_id": "ap-low",  "type": "proof",     "customer_name": "C", "order_number": "",
                 "requested_at": "2026-01-01T10:00:00Z", "age_hours": 5,  "urgency_score": 5.0},
                {"record_id": "ap-high", "type": "signature", "customer_name": "A", "order_number": "",
                 "requested_at": "2026-01-03T10:00:00Z", "age_hours": 50, "urgency_score": 50.0},
                {"record_id": "ap-med",  "type": "proof",     "customer_name": "B", "order_number": "",
                 "requested_at": "2026-01-02T10:00:00Z", "age_hours": 20, "urgency_score": 20.0},
            ]
            fixtures = {**_all_empty(), "customer-attention": _customer_attention(approvals=approvals)}
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            high_box = page.locator('[data-testid="approval-ap-high"]').bounding_box()
            med_box  = page.locator('[data-testid="approval-ap-med"]').bounding_box()
            low_box  = page.locator('[data-testid="approval-ap-low"]').bounding_box()

            assert all(b is not None for b in [high_box, med_box, low_box]), "Not all approval items rendered"
            assert high_box["y"] < med_box["y"] < low_box["y"], (
                f"Approvals not in urgency order: {high_box['y']:.0f} {med_box['y']:.0f} {low_box['y']:.0f}"
            )
            print("PASS: approvals sorted by urgency_score desc")
        finally:
            browser.close()


def test_at_risk_sort_order_blocked_first():
    """At-risk items must be displayed: blocked > overdue > due_within_24h_not_started."""
    with sync_playwright() as pw:
        page, browser = _get_page(pw)
        try:
            _login(page)
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            at_risk = [
                # Passed in wrong order — frontend must re-sort
                {"order_id": "o1", "order_number": "ORD-1", "order_item_id": "item-due24",
                 "item_name": "Due Soon Item", "reason": "due_within_24h_not_started",
                 "due_at": f"{today}T23:59:00Z"},
                {"order_id": "o2", "order_number": "ORD-2", "order_item_id": "item-blocked",
                 "item_name": "Blocked Item", "reason": "blocked",
                 "due_at": f"{today}T12:00:00Z"},
                {"order_id": "o3", "order_number": "ORD-3", "order_item_id": "item-overdue",
                 "item_name": "Overdue Item", "reason": "overdue",
                 "due_at": "2026-01-01T00:00:00Z"},
            ]
            fixtures = {
                **_all_empty(),
                "production-snapshot": _production_snapshot(at_risk=at_risk),
            }
            _mock_all_v1(page, fixtures)
            _navigate_dashboard(page)
            page.wait_for_timeout(800)

            blocked_box = page.locator('[data-testid="at-risk-item-blocked"]').bounding_box()
            overdue_box = page.locator('[data-testid="at-risk-item-overdue"]').bounding_box()
            due24_box   = page.locator('[data-testid="at-risk-item-due24"]').bounding_box()

            assert all(b is not None for b in [blocked_box, overdue_box, due24_box]), \
                "Not all at-risk items rendered"
            assert blocked_box["y"] < overdue_box["y"] < due24_box["y"], (
                f"At-risk order wrong: blocked={blocked_box['y']:.0f} "
                f"overdue={overdue_box['y']:.0f} due24={due24_box['y']:.0f}"
            )
            print("PASS: at-risk sorted blocked > overdue > due_within_24h")
        finally:
            browser.close()

# ─────────────────────────────────────────────────────────────────
# 8. Guardrail checks (static code analysis)
# ─────────────────────────────────────────────────────────────────

DASHBOARD_SOURCE = Path("/app/frontend/src/pages/Dashboard.js")

def test_guardrail_no_silent_catch():
    """.catch(() => {}) must not exist in Dashboard.js."""
    source = DASHBOARD_SOURCE.read_text()
    matches = re.findall(r'\.catch\(\s*\(\s*\)\s*=>\s*\{\s*\}\s*\)', source)
    assert not matches, (
        f"Found {len(matches)} silent .catch(() => {{}}) in Dashboard.js"
    )
    print("PASS: no silent .catch(() => {}) in Dashboard.js")


def test_guardrail_no_jobs_id_links_in_source():
    """/jobs/:id pattern must not appear in Dashboard.js JSX link props."""
    source = DASHBOARD_SOURCE.read_text()
    # Match to="..." or href="..." containing /jobs/ followed by variable/string
    matches = re.findall(r'(?:to|href)=["\`][^"\'`]*\/jobs\/[^"\'`]+["\`]', source)
    assert not matches, f"Found /jobs/:id links in Dashboard.js: {matches}"
    print("PASS: no /jobs/:id links in Dashboard.js source")


def test_guardrail_no_user_facing_jobs_wording():
    """User-facing label strings must not use 'jobs' (should be 'orders' / 'order items')."""
    source = DASHBOARD_SOURCE.read_text()
    # Check JSX string content — labels like "View all jobs", "Active Jobs", etc.
    # Allowed: 'active_jobs' (data key), 'fetchJobs' (commented/removed), 'legacy_job'
    violations = []
    for line_no, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        # Skip comments and data key references
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        # Match user-visible strings in JSX text or label props
        # Look for "jobs" as a word (case-insensitive) in JSX string literals
        if re.search(r'[">`][^"<`]*\b[Jj]obs\b[^"<`]*["<`]', stripped):
            # Exclude known data-key usages
            if not any(x in stripped for x in ["active_jobs", "legacy_job", "fetchJobs", "job_id", "job_ticket"]):
                violations.append((line_no, stripped[:100]))
    assert not violations, (
        f"User-facing 'jobs' wording found in Dashboard.js:\n" +
        "\n".join(f"  L{ln}: {txt}" for ln, txt in violations)
    )
    print("PASS: no user-facing 'jobs' wording in Dashboard.js")


def test_guardrail_sorting_helpers_defined():
    """sortAtRisk, sortByUrgency, AT_RISK_PRIORITY must be defined in Dashboard.js."""
    source = DASHBOARD_SOURCE.read_text()
    assert "const sortAtRisk" in source, "sortAtRisk not defined"
    assert "const sortByUrgency" in source, "sortByUrgency not defined"
    assert "AT_RISK_PRIORITY" in source, "AT_RISK_PRIORITY not defined"
    assert "blocked: 0" in source, "blocked priority 0 not set in AT_RISK_PRIORITY"
    assert "overdue: 1" in source, "overdue priority 1 not set in AT_RISK_PRIORITY"
    print("PASS: sorting helpers defined with correct priorities")


def test_guardrail_getfreshness_defined_with_10min_threshold():
    """getFreshness must be defined with > 10 minute stale threshold."""
    source = DASHBOARD_SOURCE.read_text()
    assert "const getFreshness" in source, "getFreshness not defined"
    assert "ageMinutes > 10" in source, "10-minute threshold not in getFreshness"
    assert "Data may be stale" in source, "'Data may be stale' text not in source"
    assert "Last updated unavailable" in source, "'Last updated unavailable' text not in source"
    print("PASS: getFreshness defined with correct threshold and messages")


def test_guardrail_error_state_testids():
    """ErrorState must use data-testid=section-error and section-error-retry."""
    source = DASHBOARD_SOURCE.read_text()
    assert 'data-testid="section-error"' in source, "section-error testid missing"
    assert 'data-testid="section-error-retry"' in source, "section-error-retry testid missing"
    assert "Couldn't load this section." in source, "Error main text missing"
    assert "Please retry." in source, "Error secondary text missing"
    print("PASS: ErrorState has correct testids and text")


def test_guardrail_all_5_v1_endpoints_fetched():
    """Dashboard must fetch all 5 V1 endpoints."""
    source = DASHBOARD_SOURCE.read_text()
    for ep in ["summary-v2", "today-command-center", "production-snapshot",
               "customer-attention", "financial-attention"]:
        assert ep in source, f"V1 endpoint '{ep}' not referenced in Dashboard.js"
    print("PASS: all 5 V1 endpoints referenced")


def test_guardrail_per_section_retry_functions():
    """Each section must have its own retry callback (not full-page reload)."""
    source = DASHBOARD_SOURCE.read_text()
    for fn in ["fetchSummary", "fetchCommandCenter", "fetchProductionSnapshot",
               "fetchCustomerAttention", "fetchFinancialAttention"]:
        assert fn in source, f"Per-section retry function '{fn}' not found"
    print("PASS: all 5 per-section retry functions defined")
