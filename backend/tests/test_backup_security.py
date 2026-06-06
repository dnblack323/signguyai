"""
Unit tests for backup security helpers (Part 2 code review remediation).

Covers the enum-safe owner check used to gate /backup export/restore.
"""

from enum import Enum
from routes.backup import _is_owner


class _Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    PLATFORM_ADMIN = "platform_admin"


class _User:
    def __init__(self, role):
        self.role = role


def test_is_owner_with_str_enum():
    assert _is_owner(_User(_Role.OWNER))
    assert not _is_owner(_User(_Role.ADMIN))
    assert not _is_owner(_User(_Role.PLATFORM_ADMIN))


def test_is_owner_with_plain_string():
    assert _is_owner(_User("owner"))
    assert not _is_owner(_User("admin"))
    assert not _is_owner(_User("webstore_owner"))


def test_is_owner_with_missing_role():
    assert not _is_owner(_User(None))

    class _NoRole:
        pass

    assert not _is_owner(_NoRole())
