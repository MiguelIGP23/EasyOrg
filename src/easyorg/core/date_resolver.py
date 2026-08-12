from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from easyorg.core.filename_date_parser import parse_date_from_filename
from easyorg.core.metadata import FilesystemDates, MetadataRecord
from easyorg.core.models import DateSource


PRIMARY_METADATA_FIELDS = (
    "DateTimeOriginal",
)

SECONDARY_METADATA_FIELDS = (
    "CreateDate",
    "MediaCreateDate",
    "TrackCreateDate",
)


@dataclass(frozen=True)
class ResolvedDate:
    value: datetime | None
    source: DateSource


def resolve_media_date(
    file_path: Path,
    metadata_record: MetadataRecord | None,
    filesystem_dates: FilesystemDates,
) -> ResolvedDate:
    if metadata_record is not None:
        primary = _extract_metadata_date(metadata_record, PRIMARY_METADATA_FIELDS)
        if primary is not None:
            return ResolvedDate(primary, DateSource.METADATA_PRIMARY)

        secondary = _extract_metadata_date(metadata_record, SECONDARY_METADATA_FIELDS)
        if secondary is not None:
            return ResolvedDate(secondary, DateSource.METADATA_SECONDARY)

    filename_date = parse_date_from_filename(file_path)
    if filename_date is not None:
        return ResolvedDate(filename_date, DateSource.FILENAME)

    if filesystem_dates.modification_date is not None:
        return ResolvedDate(filesystem_dates.modification_date, DateSource.FILESYSTEM_MODIFICATION)

    if filesystem_dates.creation_date is not None:
        return ResolvedDate(filesystem_dates.creation_date, DateSource.FILESYSTEM_CREATION)

    return ResolvedDate(None, DateSource.NONE)


def _extract_metadata_date(metadata_record: MetadataRecord, fields: tuple[str, ...]) -> datetime | None:
    for field in fields:
        raw_value = metadata_record.fields.get(field)
        if not raw_value:
            continue

        parsed = _parse_exif_datetime(raw_value)
        if parsed is not None:
            return parsed

    return None


def _parse_exif_datetime(raw_value: str) -> datetime | None:
    try:
        normalized = raw_value.replace("T", " ").replace("Z", "")
        if "." in normalized:
            normalized = normalized.split(".", 1)[0]
        return datetime.strptime(normalized, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
