from datetime import datetime, timezone

import pytz

local_tz = pytz.timezone("Europe/London")


def localize(dt: datetime) -> datetime:
    """Convert a naive datetime to local timezone."""
    if dt.tzinfo is None:
        return local_tz.localize(dt)
    return dt.astimezone(local_tz)


def to_utc(value: datetime) -> datetime:
    # Convert to UTC and drop tzinfo for storage
    if value.tzinfo is None:
        raise ValueError("Datetime must be timezone-aware.")
        # value = local_tz.localize(value)
    return value.astimezone(timezone.utc)


def to_utc_naive(value: datetime) -> datetime:
    return to_utc(value).replace(tzinfo=None)
