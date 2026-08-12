from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    pyinstaller = shutil.which("pyinstaller")
    if pyinstaller is None:
        print("PyInstaller no esta instalado en el entorno actual.")
        return 1

    command = [
        pyinstaller,
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "easyOrg",
        "--add-data",
        f"{project_root / 'tools' / 'exiftool'};tools/exiftool",
        str(project_root / "src" / "easyorg" / "gui_main.py"),
    ]
    subprocess.run(command, check=True, cwd=project_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
