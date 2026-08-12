from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from os import stat_result


@dataclass(frozen=True)
class FilesystemDates:
    modification_date: datetime
    creation_date: datetime | None


@dataclass(frozen=True)
class MetadataRecord:
    source_path: Path
    fields: dict[str, str]
    error: str | None = None


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


class ExifToolMetadataReader:
    PHOTO_FIELDS = (
        "DateTimeOriginal",
        "CreateDate",
    )
    VIDEO_FIELDS = (
        "DateTimeOriginal",
        "MediaCreateDate",
        "TrackCreateDate",
        "CreateDate",
    )

    def __init__(
        self,
        exiftool_path: Path,
        run_command: callable = subprocess.run,
    ) -> None:
        self._exiftool_path = exiftool_path
        self._run_command = run_command

    def read_batch(self, file_paths: list[Path]) -> dict[Path, MetadataRecord]:
        if not file_paths:
            return {}

        command = [
            str(self._exiftool_path),
            "-j",
            "-n",
            "-DateTimeOriginal",
            "-CreateDate",
            "-MediaCreateDate",
            "-TrackCreateDate",
            *[str(path) for path in file_paths],
        ]
        completed = self._run_command(
            command,
            check=True,
            capture_output=True,
            text=True,
        )

        payload = json.loads(completed.stdout)
        records_by_path: dict[Path, MetadataRecord] = {}

        for item in payload:
            source_path = Path(item.get("SourceFile", ""))
            if not source_path:
                continue

            error = item.get("Error")
            fields = {
                key: value
                for key, value in item.items()
                if key not in {"SourceFile", "Error"} and isinstance(value, str)
            }
            records_by_path[source_path] = MetadataRecord(
                source_path=source_path,
                fields=fields,
                error=error if isinstance(error, str) else None,
            )

        for path in file_paths:
            records_by_path.setdefault(
                path,
                MetadataRecord(
                    source_path=path,
                    fields={},
                    error="No metadata returned by ExifTool.",
                ),
            )

        return records_by_path
