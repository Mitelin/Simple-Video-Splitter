"""Parsing helpers for user-entered split timestamps."""

from __future__ import annotations

import re

TIME_PATTERN = re.compile(r"^(\d{2}):(\d{2}):(\d{2})$")


def parse_time_to_seconds(value: str) -> int:
    """Convert a strict HH:MM:SS string into a positive number of seconds."""

    match = TIME_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError("Split time must use HH:MM:SS format.")

    hours, minutes, seconds = (int(part) for part in match.groups())
    if minutes > 59 or seconds > 59:
        raise ValueError("Minutes and seconds must be between 00 and 59.")

    total_seconds = hours * 3600 + minutes * 60 + seconds
    if total_seconds <= 0:
        raise ValueError("Split time must be greater than 00:00:00.")

    return total_seconds
