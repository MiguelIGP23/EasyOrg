from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    spec_path = project_root / "easyOrg.spec"
    if spec_path.exists():
        spec_path.unlink()

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
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
