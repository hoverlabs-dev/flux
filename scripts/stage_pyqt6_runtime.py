from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WHEELHOUSE = PROJECT_ROOT / "vendor" / "wheels"
RUNTIME_ROOT = PROJECT_ROOT / "vendor" / "python"
PYTHON_TARGETS = ("310", "311")


def main() -> None:
    WHEELHOUSE.mkdir(parents=True, exist_ok=True)
    for py_version in PYTHON_TARGETS:
        _download_wheels(py_version)
        _stage_runtime(py_version)
    print(f"PyQt6 runtimes staged under {RUNTIME_ROOT}")


def _download_wheels(py_version: str) -> None:
    command = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "--only-binary",
        ":all:",
        "--platform",
        "win_amd64",
        "--implementation",
        "cp",
        "--python-version",
        py_version,
        "--dest",
        str(WHEELHOUSE),
        "PyQt6",
    ]
    subprocess.check_call(command)


def _stage_runtime(py_version: str) -> None:
    target = RUNTIME_ROOT / f"py{py_version}"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        str(WHEELHOUSE),
        "--only-binary",
        ":all:",
        "--platform",
        "win_amd64",
        "--implementation",
        "cp",
        "--python-version",
        py_version,
        "--target",
        str(target),
        "PyQt6",
    ]
    subprocess.check_call(command)


if __name__ == "__main__":
    main()
