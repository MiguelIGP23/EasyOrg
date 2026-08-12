from pathlib import Path

import pytest

from easyorg.core.dependencies import ExifToolResolver


def test_resolver_checks_pyinstaller_runtime_root_for_windows_portable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meipass = tmp_path / "bundle"
    portable = meipass / "tools" / "exiftool" / "windows" / "exiftool.exe"
    portable.parent.mkdir(parents=True)
    portable.write_bytes(b"binary")

    monkeypatch.setattr("easyorg.core.dependencies.is_windows", lambda: True)
    monkeypatch.setattr("easyorg.core.dependencies.is_linux", lambda: False)
    monkeypatch.setattr("easyorg.core.dependencies.sys._MEIPASS", str(meipass), raising=False)

    resolver = ExifToolResolver(project_root=tmp_path, which=lambda name: None)

    assert resolver.resolve().executable_path == portable
