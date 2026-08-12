from datetime import date

import pytest

from easyorg.core.models import (
    DateSource,
    MediaFile,
    MediaType,
    OperationMode,
    OrganizationMode,
)
from easyorg.core.paths import build_output_directory_name
from easyorg.utils.dates import month_folder_name, week_of_month
from easyorg.utils.sizes import format_size


@pytest.mark.parametrize(
    ("day", "expected_week"),
    [
        (1, 1),
        (7, 1),
        (8, 2),
        (14, 2),
        (15, 3),
        (21, 3),
        (22, 4),
        (28, 4),
        (29, 5),
        (31, 5),
    ],
)
def test_week_of_month(day: int, expected_week: int) -> None:
    assert week_of_month(day) == expected_week


def test_month_folder_name_uses_spanish_names() -> None:
    assert month_folder_name(8) == "08 - Agosto"


def test_format_size_uses_human_units() -> None:
    assert format_size(0) == "0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1024 * 1024) == "1.0 MB"


def test_build_output_directory_name_uses_incremental_suffix(tmp_path) -> None:
    run_date = date(2026, 8, 12)

    assert build_output_directory_name(tmp_path, run_date).name == "easyOrg_2026-08-12"

    (tmp_path / "easyOrg_2026-08-12").mkdir()
    assert build_output_directory_name(tmp_path, run_date).name == "easyOrg_2026-08-12_2"

    (tmp_path / "easyOrg_2026-08-12_2").mkdir()
    assert build_output_directory_name(tmp_path, run_date).name == "easyOrg_2026-08-12_3"


def test_media_file_defaults_to_no_resolved_date() -> None:
    media_file = MediaFile(
        source_path=tmp_path_factory().mktemp("media") / "photo.jpg",
        media_type=MediaType.IMAGE,
        size_bytes=42,
    )

    assert media_file.date_source is DateSource.NONE
    assert media_file.capture_date is None


def test_core_enums_expose_expected_values() -> None:
    assert OperationMode.COPY.value == "copy"
    assert OperationMode.MOVE.value == "move"
    assert OrganizationMode.YEAR_MONTH.value == "year_month"
    assert OrganizationMode.YEAR_MONTH_WEEK.value == "year_month_week"


def tmp_path_factory():
    from tempfile import TemporaryDirectory
    from pathlib import Path

    class _Factory:
        def __init__(self) -> None:
            self._holders: list[TemporaryDirectory[str]] = []

        def mktemp(self, prefix: str) -> Path:
            holder = TemporaryDirectory(prefix=prefix)
            self._holders.append(holder)
            return Path(holder.name)

    return _Factory()
