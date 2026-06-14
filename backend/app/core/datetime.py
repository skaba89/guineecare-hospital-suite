"""Shared UTC timestamp helper.

SQLAlchemy ``default=`` and ``onupdate=`` expect a *callable* that returns
a ``datetime``.  Using the deprecated ``datetime.utcnow`` produces
``DeprecationWarning`` in Python 3.12+.  This module provides a
drop-in replacement that returns a timezone-aware UTC datetime.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)
