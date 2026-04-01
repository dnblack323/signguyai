import os
import re
from pathlib import Path


def _read_text(path: str) -> str:
    file_path = Path(path)
    return file_path.read_text(encoding="utf-8") if file_path.exists() else ""


_MEMORY_TEXT = _read_text("/app/memory/test_credentials.md") + "\n" + _read_text("/app/memory/PRD.md")


def _match(pattern: str, default: str = "") -> str:
    match = re.search(pattern, _MEMORY_TEXT, re.IGNORECASE)
    return match.group(1) if match else default


PRODUCTION_OWNER_EMAIL = (
    os.environ.get("TEST_PRODUCTION_OWNER_EMAIL")
    or _match(r"Owner Admin:\s*`?([^`\s|]+@[^`\s|]+)`?")
    or _match(r"Admin:\s*([^\s/]+@[^\s/]+)")
)

PRODUCTION_OWNER_PASSWORD = (
    os.environ.get("TEST_PRODUCTION_OWNER_PASSWORD")
    or _match(r"Owner Admin:.*?Password:\s*`([^`]+)`")
    or _match(r"Admin:\s*[^\s/]+\s*/\s*([^\s]+)")
)

LEGACY_ADMIN_EMAIL = os.environ.get("TEST_LEGACY_ADMIN_EMAIL") or _match(r"Admin:\s*([^\s/]+@[^\s/]+)")
LEGACY_ADMIN_PASSWORD = os.environ.get("TEST_LEGACY_ADMIN_PASSWORD") or _match(r"Admin:\s*[^\s/]+\s*/\s*([^\s]+)")

DEV_TEST_EMAIL = os.environ.get("TEST_DEV_EMAIL") or _match(
    r"Dev Test Account.*?Email:\s*([^\s`]+@[^\s`]+)",
    "",
)

DEV_TEST_PASSWORD = os.environ.get("TEST_DEV_PASSWORD") or _match(
    r"Dev Test Account.*?Password:\s*([^\s`]+)",
    "",
)

FALLBACK_TEST_EMAIL = os.environ.get("TEST_FALLBACK_EMAIL") or _match(r"Test:\s*([^\s/]+@[^\s/]+)")
FALLBACK_TEST_PASSWORD = os.environ.get("TEST_FALLBACK_PASSWORD") or _match(r"Test:\s*[^\s/]+\s*/\s*([^\s]+)")
SYNTHETIC_OWNER_EMAIL = os.environ.get("TEST_SYNTHETIC_OWNER_EMAIL", "synthetic-owner@example.com")
SYNTHETIC_OWNER_PASSWORD = os.environ.get("TEST_SYNTHETIC_OWNER_PASSWORD", "synthetic-owner-password")

COMMON_TEST_EMAIL = os.environ.get("TEST_COMMON_EMAIL", "synthetic-test@example.com")
COMMON_TEST_PASSWORD = os.environ.get("TEST_COMMON_PASSWORD", "synthetic-test-password")
DEMO_TEST_EMAIL = os.environ.get("TEST_DEMO_EMAIL", "synthetic-demo@example.com")
DEMO_TEST_PASSWORD = os.environ.get("TEST_DEMO_PASSWORD", "synthetic-demo-password")
PORTAL_TEST_PASSWORD = os.environ.get("TEST_PORTAL_PASSWORD", "synthetic-portal-password")