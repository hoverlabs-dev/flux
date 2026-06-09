from __future__ import annotations

import importlib
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WHEELHOUSE = PROJECT_ROOT / "vendor" / "wheels"
RUNTIME_ROOT = PROJECT_ROOT / "vendor" / "python"


def ensure_pyqt6(host_name: str) -> None:
    """Make the vendored PyQt6 runtime importable for the current DCC Python."""

    if _can_import_pyqt6():
        return

    runtime_path = _runtime_path()
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))
    if _can_import_pyqt6():
        return

    raise RuntimeError(
        f"PyQt6 is not available for {host_name} Python {sys.version_info.major}.{sys.version_info.minor}. "
        f"Expected vendored runtime folder: {runtime_path}. "
        "Run scripts/stage_pyqt6_runtime.py from the shared project folder."
    )


def _runtime_path() -> Path:
    py_tag = f"py{sys.version_info.major}{sys.version_info.minor}"
    return RUNTIME_ROOT / py_tag


def _can_import_pyqt6() -> bool:
    try:
        importlib.import_module("PyQt6")
        return True
    except Exception:
        return False
