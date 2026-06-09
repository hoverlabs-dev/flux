from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WHEELHOUSE = PROJECT_ROOT / "vendor" / "wheels"


def main() -> None:
    print("This script only downloads wheels. For shared deployment, use scripts/stage_pyqt6_runtime.py.")
    WHEELHOUSE.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--only-binary",
        ":all:",
        "--dest",
        str(WHEELHOUSE),
        "PyQt6",
    ]
    subprocess.check_call(command)
    print(f"PyQt6 wheels downloaded to {WHEELHOUSE}")


if __name__ == "__main__":
    main()
