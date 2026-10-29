"""
Response envelope helpers.

All success responses follow the documented contract in docs/API_CONTRACTS.md:

    # Single object
    { "data": { ... }, "meta": { "timestamp": "..." } }

    # List with pagination
    { "data": [ ... ], "meta": { "page": 1, "limit": 20, "total": 150, ... } }

    # Error
    { "error": { "code": "VALIDATION_ERROR", "message": "...", "details": [...] } }
"""
from datetime import datetime, timezone
from typing import Any, Optional


def meta(page: Optional[int] = None, limit: Optional[int] = None,
         total: Optional[int] = None, total_pages: Optional[int] = None) -> dict:
    """Build the standard ``meta`` block."""
    m: dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat()}
    if page is not None:
        m["page"] = page
    if limit is not None:
        m["limit"] = limit
    if total is not None:
        m["total"] = total
    if total_pages is not None:
        m["total_pages"] = total_pages
    return m


def envelope(data: Any, *, page: Optional[int] = None, limit: Optional[int] = None,
             total: Optional[int] = None, total_pages: Optional[int] = None) -> dict:
    """Wrap ``data`` in the standard success envelope."""
    return {"data": data, "meta": meta(page, limit, total, total_pages)}


def error_envelope(message: str, code: str = "INTERNAL_ERROR",
                   details: Optional[list] = None) -> dict:
    """Wrap an error in the standard error envelope."""
    err: dict[str, Any] = {"code": code, "message": message}
    if details:
        err["details"] = details
    return {"error": err}
