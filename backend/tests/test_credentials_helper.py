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

DEV_TEST_EMAIL = os.environ.get("TEST_DEV_EMAIL") or _match(
    r"Dev Test Account.*?Email:\s*([^\s`]+@[^\s`]+)",
    "testuser@example.com",
)

DEV_TEST_PASSWORD = os.environ.get("TEST_DEV_PASSWORD") or _match(
    r"Dev Test Account.*?Password:\s*([^\s`]+)",
    "TestPassword123!",
)

FALLBACK_TEST_EMAIL = os.environ.get("TEST_FALLBACK_EMAIL", "test@test.com")
FALLBACK_TEST_PASSWORD = os.environ.get("TEST_FALLBACK_PASSWORD", "password")
SYNTHETIC_OWNER_EMAIL = os.environ.get("TEST_SYNTHETIC_OWNER_EMAIL", "testowner@example.com")
SYNTHETIC_OWNER_PASSWORD = os.environ.get("TEST_SYNTHETIC_OWNER_PASSWORD", "owner123")