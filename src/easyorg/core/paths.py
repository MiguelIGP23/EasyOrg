from __future__ import annotations

from datetime import date
from pathlib import Path


def build_output_directory_name(parent_directory: Path, run_date: date) -> Path:
    base_name = f"easyOrg_{run_date.isoformat()}"
    candidate = parent_directory / base_name
    suffix = 2

    while candidate.exists():
        candidate = parent_directory / f"{base_name}_{suffix}"
        suffix += 1

    return candidate

