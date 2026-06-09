from __future__ import annotations

import re
from pathlib import Path

from .settings import BridgeSettings


HOST_TARGETS = {
    "maya": "blender",
    "blender": "maya",
}


def transfer_path(settings: BridgeSettings, asset_name: str, source_host: str) -> Path:
    target_host = HOST_TARGETS.get(source_host, "dcc")
    clean_name = sanitize_name(asset_name) or "selection"
    return settings.fbx_path.parent / f"{clean_name}__{source_host}_to_{target_host}.fbx"


def sanitize_name(name: str) -> str:
    clean = name.split("|")[-1].split(":")[-1]
    clean = clean.split(".")[0]
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "_", clean).strip("._")
    return clean[:80]

