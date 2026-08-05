"""Customer-safe serializers for public quote views."""

from typing import Any, Dict


PUBLIC_QUOTE_FIELDS = {
    "id",
    "quote_number",
    "status",
    "total",
    "notes",
    "created_at",
    "expiration_date",
}

PUBLIC_LINE_ITEM_FIELDS = {
    "description",
    "quantity",
    "unit_price",
    "total",
}


def _copy_allowed(source: Dict[str, Any], allowed_fields: set[str]) -> Dict[str, Any]:
    return {field: source[field] for field in allowed_fields if field in source}


def serialize_public_quote(quote: Dict[str, Any]) -> Dict[str, Any]:
    """Return only quote fields safe for unauthenticated customer links.

    The public magic-link response is reachable by anyone with the share token.
    Use an allowlist so internal pricing/cost/margin fields, including future
    fields added to quote documents, do not leak by default.
    """
    public_quote = _copy_allowed(quote, PUBLIC_QUOTE_FIELDS)

    line_items = quote.get("line_items")
    if isinstance(line_items, list):
        public_quote["line_items"] = [
            _copy_allowed(item, PUBLIC_LINE_ITEM_FIELDS)
            for item in line_items
            if isinstance(item, dict)
        ]

    return public_quote
