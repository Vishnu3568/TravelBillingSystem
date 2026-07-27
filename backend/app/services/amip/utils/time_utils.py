"""
AMIP Timestamp & Duration Utilities.
Provides ISO timestamp formatting and millisecond duration calculations.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional


def current_utc_timestamp() -> str:
    """Returns the current UTC timestamp formatted as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def current_datetime_utc() -> datetime:
    """Returns the current datetime in UTC timezone."""
    return datetime.now(timezone.utc)


def parse_iso_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Parses an ISO 8601 timestamp string into a UTC datetime object."""
    if not timestamp_str:
        return None
    try:
        dt = datetime.fromisoformat(timestamp_str)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def calculate_duration_ms(start_time_iso: str, end_time_iso: Optional[str] = None) -> float:
    """
    Calculates duration in milliseconds between two ISO timestamp strings.
    If end_time_iso is None, calculates duration up to the current time.
    """
    start_dt = parse_iso_timestamp(start_time_iso)
    if not start_dt:
        return 0.0

    if end_time_iso:
        end_dt = parse_iso_timestamp(end_time_iso)
    else:
        end_dt = current_datetime_utc()

    if not end_dt:
        return 0.0

    delta = end_dt - start_dt
    return max(0.0, delta.total_seconds() * 1000.0)
