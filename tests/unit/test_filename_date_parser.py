from datetime import datetime
from pathlib import Path

import pytest

from easyorg.core.filename_date_parser import parse_date_from_filename


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("IMG_20230417_153025.jpg", datetime(2023, 4, 17, 15, 30, 25)),
        ("VID_20210821_121300.mp4", datetime(2021, 8, 21, 12, 13, 0)),
        ("20200514_182223.jpg", datetime(2020, 5, 14, 18, 22, 23)),
        ("Screenshot_20240322-194355.png", datetime(2024, 3, 22, 19, 43, 55)),
        ("2024-01-31_photo.jpg", datetime(2024, 1, 31, 0, 0, 0)),
        ("2024-03-18_12-42-31.jpg", datetime(2024, 3, 18, 12, 42, 31)),
    ],
)
def test_parse_date_from_filename_accepts_unambiguous_patterns(
    filename: str,
    expected: datetime,
) -> None:
    assert parse_date_from_filename(Path(filename)) == expected


@pytest.mark.parametrize(
    "filename",
    [
        "foto_12_04_08.jpg",
        "IMG_20231340.jpg",
        "foto_final.jpg",
        "123456.jpg",
        "IMG_20230230_120000.jpg",
        "random_2024-99-01.png",
    ],
)
def test_parse_date_from_filename_rejects_ambiguous_or_invalid_patterns(filename: str) -> None:
    assert parse_date_from_filename(Path(filename)) is None
