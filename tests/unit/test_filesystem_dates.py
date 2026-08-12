from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from easyorg.core.metadata import FilesystemDates, get_filesystem_dates


def test_get_filesystem_dates_uses_birthtime_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_stat = SimpleNamespace(
        st_mtime=1_700_000_000,
        st_ctime=1_600_000_000,
        st_birthtime=1_500_000_000,
    )

    monkeypatch.setattr(Path, "stat", lambda self: fake_stat)
    monkeypatch.setattr("easyorg.core.metadata.sys.platform", "linux")

    result = get_filesystem_dates(Path("sample.jpg"))

    assert result == FilesystemDates(
        modification_date=datetime.fromtimestamp(fake_stat.st_mtime),
        creation_date=datetime.fromtimestamp(fake_stat.st_birthtime),
    )


def test_get_filesystem_dates_returns_none_when_birthtime_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_stat = SimpleNamespace(
        st_mtime=1_700_000_000,
        st_ctime=1_600_000_000,
    )

    monkeypatch.setattr(Path, "stat", lambda self: fake_stat)
    monkeypatch.setattr("easyorg.core.metadata.sys.platform", "linux")

    result = get_filesystem_dates(Path("sample.jpg"))

    assert result.creation_date is None
    assert result.modification_date == datetime.fromtimestamp(fake_stat.st_mtime)


def test_get_filesystem_dates_uses_ctime_as_creation_on_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_stat = SimpleNamespace(
        st_mtime=1_700_000_000,
        st_ctime=1_600_000_000,
    )

    monkeypatch.setattr(Path, "stat", lambda self: fake_stat)
    monkeypatch.setattr("easyorg.core.metadata.sys.platform", "win32")

    result = get_filesystem_dates(Path("sample.jpg"))

    assert result.creation_date == datetime.fromtimestamp(fake_stat.st_ctime)
    assert result.modification_date == datetime.fromtimestamp(fake_stat.st_mtime)
