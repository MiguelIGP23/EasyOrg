from pathlib import Path
import subprocess

import pytest

from easyorg.core.dependencies import (
    DependencyResolutionError,
    ExifToolResolution,
    ExifToolResolver,
)


def test_resolve_prefers_portable_exiftool_on_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    portable = tmp_path / "tools" / "exiftool" / "exiftool.exe"
    portable.parent.mkdir(parents=True)
    portable.write_bytes(b"binary")

    monkeypatch.setattr("easyorg.core.dependencies.is_windows", lambda: True)
    monkeypatch.setattr("easyorg.core.dependencies.is_linux", lambda: False)

    resolver = ExifToolResolver(project_root=tmp_path, which=lambda name: r"C:\ExifTool\exiftool.exe")

    resolution = resolver.resolve()

    assert resolution == ExifToolResolution(
        executable_path=portable,
        source="portable",
        requires_confirmation=False,
        install_command=None,
        message="ExifTool portable encontrado.",
    )


def test_resolve_uses_path_when_portable_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("easyorg.core.dependencies.is_windows", lambda: False)
    monkeypatch.setattr("easyorg.core.dependencies.is_linux", lambda: True)

    resolver = ExifToolResolver(project_root=tmp_path, which=lambda name: "/usr/bin/exiftool")

    resolution = resolver.resolve()

    assert resolution.executable_path == Path("/usr/bin/exiftool")
    assert resolution.source == "path"


def test_resolve_returns_assisted_installation_on_linux_when_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("easyorg.core.dependencies.is_windows", lambda: False)
    monkeypatch.setattr("easyorg.core.dependencies.is_linux", lambda: True)

    resolver = ExifToolResolver(project_root=tmp_path, which=lambda name: None)

    resolution = resolver.resolve()

    assert resolution.executable_path is None
    assert resolution.source == "apt"
    assert resolution.requires_confirmation is True
    assert resolution.install_command == ("sudo", "apt", "install", "-y", "libimage-exiftool-perl")


def test_resolve_raises_when_missing_on_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("easyorg.core.dependencies.is_windows", lambda: True)
    monkeypatch.setattr("easyorg.core.dependencies.is_linux", lambda: False)

    resolver = ExifToolResolver(project_root=tmp_path, which=lambda name: None)

    with pytest.raises(DependencyResolutionError, match="instalelo manualmente"):
        resolver.resolve()


def test_install_with_confirmation_runs_command_and_rechecks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("easyorg.core.dependencies.is_windows", lambda: False)
    monkeypatch.setattr("easyorg.core.dependencies.is_linux", lambda: True)

    installed = {"value": False}

    def fake_which(name: str) -> str | None:
        if installed["value"]:
            return "/usr/bin/exiftool"
        return None

    def fake_run(*args, **kwargs) -> subprocess.CompletedProcess[str]:
        installed["value"] = True
        return subprocess.CompletedProcess(
            args=kwargs.get("args", args[0] if args else ()),
            returncode=0,
            stdout="installed",
            stderr="",
        )

    resolver = ExifToolResolver(
        project_root=tmp_path,
        which=fake_which,
        run_command=fake_run,
    )

    resolution = resolver.install_with_confirmation(consent_granted=True)

    assert resolution.executable_path == Path("/usr/bin/exiftool")
    assert resolution.source == "path"


def test_install_with_confirmation_rejects_missing_consent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("easyorg.core.dependencies.is_windows", lambda: False)
    monkeypatch.setattr("easyorg.core.dependencies.is_linux", lambda: True)

    resolver = ExifToolResolver(project_root=tmp_path, which=lambda name: None)

    with pytest.raises(DependencyResolutionError, match="consentimiento explicito"):
        resolver.install_with_confirmation(consent_granted=False)
