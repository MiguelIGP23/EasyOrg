from __future__ import annotations

from pathlib import Path

from easyorg.gui.app import run_gui


def main() -> None:
    run_gui(project_root=Path(__file__).resolve().parents[2])


if __name__ == "__main__":
    main()
