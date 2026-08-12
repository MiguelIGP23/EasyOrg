from __future__ import annotations

import shutil
import stat
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    dist_root = project_root / "dist" / "easyOrg-linux"
    if dist_root.exists():
        shutil.rmtree(dist_root)

    app_root = dist_root / "app"
    app_root.mkdir(parents=True)
    shutil.copytree(project_root / "src", app_root / "src")
    if (project_root / "tools" / "exiftool").exists():
        shutil.copytree(project_root / "tools" / "exiftool", app_root / "tools" / "exiftool")
    shutil.copy2(project_root / "README.md", dist_root / "README.md")
    shutil.copy2(project_root / "pyproject.toml", dist_root / "pyproject.toml")

    launcher = dist_root / "run-easyorg.sh"
    launcher.write_text(
        "#!/usr/bin/env sh\n"
        "SCRIPT_DIR=$(CDPATH= cd -- \"$(dirname -- \"$0\")\" && pwd)\n"
        "PYTHONPATH=\"$SCRIPT_DIR/app/src\" exec python3 -m easyorg \"$@\"\n",
        encoding="utf-8",
    )
    launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
