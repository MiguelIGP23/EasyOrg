from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


_COMPACT_DATETIME_PATTERNS = (
    re.compile(r"(?<!\d)(\d{8})[_-](\d{6})(?!\d)"),
    re.compile(r"(?<!\d)(\d{8})-(\d{6})(?!\d)"),
)

_SEPARATED_DATETIME_PATTERN = re.compile(
    r"(?<!\d)(\d{4})-(\d{2})-(\d{2})[_-](\d{2})-(\d{2})-(\d{2})(?!\d)"
)

_DATE_ONLY_PATTERN = re.compile(r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)")


def parse_date_from_filename(file_path: Path) -> datetime | None:
    stem = file_path.stem

    separated_match = _SEPARATED_DATETIME_PATTERN.search(stem)
    if separated_match:
        return _build_datetime(*separated_match.groups())

    for pattern in _COMPACT_DATETIME_PATTERNS:
        match = pattern.search(stem)
        if match:
            compact_date, compact_time = match.groups()
            return _build_datetime(
                compact_date[0:4],
                compact_date[4:6],
                compact_date[6:8],
                compact_time[0:2],
                compact_time[2:4],
                compact_time[4:6],
            )

    date_only_match = _DATE_ONLY_PATTERN.search(stem)
    if date_only_match:
        year, month, day = date_only_match.groups()
        return _build_datetime(year, month, day, "00", "00", "00")

    return None


def _build_datetime(
    year: str,
    month: str,
    day: str,
    hour: str,
    minute: str,
    second: str,
) -> datetime | None:
    try:
        return datetime(
            year=int(year),
            month=int(month),
            day=int(day),
            hour=int(hour),
            minute=int(minute),
            second=int(second),
        )
    except ValueError:
        return None
