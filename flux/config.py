from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


import sys
from bridge_core.settings import PROJECT_ROOT, DEFAULT_EXCHANGE_DIR

CONFIG_PATH = (
    Path(sys.executable).parent.resolve() / "flux_config.json"
    if getattr(sys, "frozen", False)
    else PROJECT_ROOT / "flux_config.json"
)
OLD_MAYA_COMMAND_PORT = 7721
MAYA_SOCKET_PORT = 7821


@dataclass(slots=True)
class FluxConfig:
    maya_exe: str = r"C:\Program Files\Autodesk\Maya2024\bin\maya.exe"
    blender_exe: str = r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
    exchange_dir: str = str(DEFAULT_EXCHANGE_DIR)
    maya_port: int = MAYA_SOCKET_PORT
    blender_port: int = 7722

    @classmethod
    def load(cls) -> "FluxConfig":
        if not CONFIG_PATH.exists():
            return cls()
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if data.get("maya_port") == OLD_MAYA_COMMAND_PORT:
            data["maya_port"] = MAYA_SOCKET_PORT
            
        exchange_dir = data.get("exchange_dir", "")
        if exchange_dir and "{PROJECT_ROOT}" in exchange_dir:
            rel = exchange_dir.replace("{PROJECT_ROOT}/", "").replace("{PROJECT_ROOT}", "")
            data["exchange_dir"] = str((PROJECT_ROOT / rel).resolve())
            
        defaults = asdict(cls())
        defaults.update({key: value for key, value in data.items() if key in defaults})
        return cls(**defaults)

    def save(self) -> None:
        data = asdict(self)
        try:
            exchange_path = Path(self.exchange_dir).resolve()
            proj_root_resolved = PROJECT_ROOT.resolve()
            if proj_root_resolved in exchange_path.parents or proj_root_resolved == exchange_path:
                rel = exchange_path.relative_to(proj_root_resolved)
                data["exchange_dir"] = f"{{PROJECT_ROOT}}/{rel.as_posix()}"
        except Exception:
            pass
        CONFIG_PATH.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
