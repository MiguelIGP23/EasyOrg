from __future__ import annotations

from pathlib import Path

from easyorg.gui.main_window import EasyOrgMainWindow


def run_gui(project_root: Path) -> None:
    window = EasyOrgMainWindow(project_root=project_root)
    window.run()
