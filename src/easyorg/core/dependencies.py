from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from easyorg.utils.platform import is_linux, is_windows


class DependencyResolutionError(RuntimeError):
    """Raised when a required dependency cannot be resolved safely."""


@dataclass(frozen=True)
class ExifToolResolution:
    executable_path: Path | None
    source: str
    requires_confirmation: bool = False
    install_command: tuple[str, ...] | None = None
    message: str = ""


class ExifToolResolver:
    def __init__(
        self,
        project_root: Path,
        which: Callable[[str], str | None] = shutil.which,
        run_command: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._project_root = project_root
        self._which = which
        self._run_command = run_command

    def resolve(self) -> ExifToolResolution:
        portable = self._portable_executable()
        if portable is not None:
            return ExifToolResolution(
                executable_path=portable,
                source="portable",
                message="ExifTool portable encontrado.",
            )

        path_candidate = self._which("exiftool")
        if path_candidate:
            return ExifToolResolution(
                executable_path=Path(path_candidate),
                source="path",
                message="ExifTool encontrado en PATH.",
            )

        if is_linux():
            return ExifToolResolution(
                executable_path=None,
                source="apt",
                requires_confirmation=True,
                install_command=("sudo", "apt", "install", "-y", "libimage-exiftool-perl"),
                message="ExifTool no esta disponible. Se requiere confirmacion para instalarlo con apt.",
            )

        raise DependencyResolutionError(
            "ExifTool no esta disponible. Proporcione un binario portable o instalelo manualmente."
        )

    def install_with_confirmation(self, consent_granted: bool) -> ExifToolResolution:
        resolution = self.resolve()
        if not resolution.requires_confirmation:
            return resolution

        if not consent_granted:
            raise DependencyResolutionError("La instalacion de ExifTool requiere consentimiento explicito.")

        if resolution.install_command is None:
            raise DependencyResolutionError("No hay comando de instalacion disponible para esta plataforma.")

        self._run_command(
            resolution.install_command,
            check=True,
            capture_output=True,
            text=True,
        )

        return self.resolve()

    def _portable_executable(self) -> Path | None:
        candidates = []
        runtime_roots = [self._project_root]
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            runtime_roots.insert(0, Path(meipass))

        for runtime_root in runtime_roots:
            tools_root = runtime_root / "tools" / "exiftool"
            if is_windows():
                candidates.extend(
                    [
                        tools_root / "exiftool.exe",
                        tools_root / "exiftool(-k).exe",
                        tools_root / "windows" / "exiftool.exe",
                    ]
                )
            else:
                candidates.extend(
                    [
                        tools_root / "exiftool",
                        tools_root / "bin" / "exiftool",
                        tools_root / "linux" / "exiftool",
                    ]
                )

        for candidate in candidates:
            if candidate.is_file():
                return candidate

        return None
