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
        try:
            shutil.rmtree(target)
        except Exception as e:
            print(f"Warning: Failed to clean some files under {target} (they may be locked/in use): {e}")
    target.mkdir(parents=True, exist_ok=True)

    import zipfile

    wheels_to_extract = []

    # 1. PyQt6-Qt6
    qt6_wheels = [w for w in WHEELHOUSE.glob("*.whl") if w.name.lower().startswith("pyqt6_qt6")]
    if qt6_wheels:
        wheels_to_extract.append(qt6_wheels[0])

    # 2. PyQt6-sip for this python version
    sip_prefix = "pyqt6_sip"
    sip_tag = f"cp{py_version}-cp{py_version}"
    sip_wheels = [w for w in WHEELHOUSE.glob("*.whl") if w.name.lower().startswith(sip_prefix) and sip_tag in w.name.lower()]
    if sip_wheels:
        wheels_to_extract.append(sip_wheels[0])

    # 3. PyQt6
    pyqt_wheels = [w for w in WHEELHOUSE.glob("*.whl") if w.name.lower().startswith("pyqt6-")]
    if pyqt_wheels:
        wheels_to_extract.append(pyqt_wheels[0])

    if len(wheels_to_extract) < 3:
        raise RuntimeError(
            f"Could not find all required wheels (PyQt6, PyQt6_sip for {py_version}, PyQt6_Qt6) in {WHEELHOUSE}"
        )

    for wheel_path in wheels_to_extract:
        print(f"Extracting {wheel_path.name} to {target}...")
        with zipfile.ZipFile(wheel_path) as z:
            for member in z.infolist():
                try:
                    z.extract(member, target)
                except PermissionError:
                    # Ignore locked files that already exist
                    pass
                except Exception as e:
                    print(f"Failed to extract {member.filename}: {e}")



if __name__ == "__main__":
    main()
