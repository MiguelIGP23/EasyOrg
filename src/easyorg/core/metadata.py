from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from os import stat_result


@dataclass(frozen=True)
class FilesystemDates:
    modification_date: datetime
    creation_date: datetime | None


def get_filesystem_dates(file_path: Path) -> FilesystemDates:
    stat_result = file_path.stat()

    return FilesystemDates(
        modification_date=datetime.fromtimestamp(stat_result.st_mtime),
        creation_date=_extract_creation_date(stat_result),
    )


def _extract_creation_date(stat_result: stat_result) -> datetime | None:
    if sys.platform.startswith("win"):
        return datetime.fromtimestamp(stat_result.st_ctime)

    birthtime = getattr(stat_result, "st_birthtime", None)
    if birthtime is None:
        return None

    return datetime.fromtimestamp(birthtime)
