from datetime import datetime
from pathlib import Path

from easyorg.core.date_resolver import ResolvedDate, resolve_media_date
from easyorg.core.metadata import FilesystemDates, MetadataRecord
from easyorg.core.models import DateSource


def _filesystem_dates() -> FilesystemDates:
    return FilesystemDates(
        modification_date=datetime(2020, 1, 2, 3, 4, 5),
        creation_date=datetime(2019, 1, 2, 3, 4, 5),
    )


def test_resolve_media_date_prefers_primary_metadata() -> None:
    metadata = MetadataRecord(
        source_path=Path("photo.jpg"),
        fields={"DateTimeOriginal": "2023:04:17 15:30:25", "CreateDate": "2023:04:17 15:31:00"},
        error=None,
    )

    resolved = resolve_media_date(Path("IMG_20220101_101010.jpg"), metadata, _filesystem_dates())

    assert resolved == ResolvedDate(datetime(2023, 4, 17, 15, 30, 25), DateSource.METADATA_PRIMARY)


def test_resolve_media_date_falls_back_to_secondary_metadata() -> None:
    metadata = MetadataRecord(
        source_path=Path("video.mp4"),
        fields={"MediaCreateDate": "2021:08:21 12:13:00"},
        error=None,
    )

    resolved = resolve_media_date(Path("video.mp4"), metadata, _filesystem_dates())

    assert resolved == ResolvedDate(datetime(2021, 8, 21, 12, 13, 0), DateSource.METADATA_SECONDARY)


def test_resolve_media_date_falls_back_to_filename() -> None:
    metadata = MetadataRecord(source_path=Path("IMG_20230417_153025.jpg"), fields={}, error="missing")

    resolved = resolve_media_date(Path("IMG_20230417_153025.jpg"), metadata, _filesystem_dates())

    assert resolved == ResolvedDate(datetime(2023, 4, 17, 15, 30, 25), DateSource.FILENAME)


def test_resolve_media_date_falls_back_to_modification_date() -> None:
    metadata = MetadataRecord(source_path=Path("photo.jpg"), fields={}, error="missing")

    resolved = resolve_media_date(Path("photo.jpg"), metadata, _filesystem_dates())

    assert resolved == ResolvedDate(datetime(2020, 1, 2, 3, 4, 5), DateSource.FILESYSTEM_MODIFICATION)


def test_resolve_media_date_falls_back_to_creation_date_when_modification_unavailable() -> None:
    metadata = MetadataRecord(source_path=Path("photo.jpg"), fields={}, error="missing")
    filesystem_dates = FilesystemDates(
        modification_date=None,  # type: ignore[arg-type]
        creation_date=datetime(2019, 1, 2, 3, 4, 5),
    )

    resolved = resolve_media_date(Path("photo.jpg"), metadata, filesystem_dates)

    assert resolved == ResolvedDate(datetime(2019, 1, 2, 3, 4, 5), DateSource.FILESYSTEM_CREATION)


def test_resolve_media_date_returns_none_when_every_source_is_missing() -> None:
    metadata = MetadataRecord(source_path=Path("photo.jpg"), fields={}, error="missing")
    filesystem_dates = FilesystemDates(
        modification_date=None,  # type: ignore[arg-type]
        creation_date=None,
    )

    resolved = resolve_media_date(Path("photo.jpg"), metadata, filesystem_dates)

    assert resolved == ResolvedDate(None, DateSource.NONE)
