from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


import sys

UNIT_TO_METERS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
}

def get_project_root() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS).resolve()
    return Path(__file__).resolve().parents[1]

PROJECT_ROOT = get_project_root()

def get_default_exchange_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.resolve() / "exchange"
    return PROJECT_ROOT / "exchange"

DEFAULT_EXCHANGE_DIR = get_default_exchange_dir()
DEFAULT_FBX_PATH = DEFAULT_EXCHANGE_DIR / "bridge_transfer.fbx"


@dataclass(slots=True)
class BridgeSettings:
    """Transfer settings shared by Maya and Blender host adapters."""

    fbx_path: Path = DEFAULT_FBX_PATH
    selected_only: bool = True
    preserve_pivots: bool = True
    preserve_custom_properties: bool = True
    preserve_materials: bool = True
    preserve_smoothing: bool = True
    triangulate: bool = False
    embed_textures: bool = False
    apply_unit_scale: bool = True
    update_existing: bool = True
    sync_transforms: bool = False
    axis_forward: str = "-Z"
    axis_up: str = "Y"
    freeze_transforms: bool = True

    @property
    def manifest_path(self) -> Path:
        return self.fbx_path.with_suffix(".bridge_manifest.json")

    def ensure_exchange_dir(self) -> None:
        self.fbx_path.parent.mkdir(parents=True, exist_ok=True)
