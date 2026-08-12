import subprocess
import sys
from pathlib import Path
import os


def test_import_package() -> None:
    import easyorg

    assert easyorg.__version__ == "1.0.0"


def test_module_entrypoint_outputs_name() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "easyorg", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "easyOrg 1.0.0"
