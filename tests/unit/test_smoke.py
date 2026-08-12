import subprocess
import sys
from pathlib import Path
import os


def test_import_package() -> None:
    import easyorg

    assert easyorg.__version__ == "0.1.0"


def test_module_entrypoint_outputs_name() -> None:
    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[2] / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"

    result = subprocess.run(
        [sys.executable, "-m", "easyorg", "--version"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "easyOrg 0.1.0"
