from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .naming import HOST_TARGETS
from .settings import BridgeSettings


@dataclass
class TransferState:
    source_host: str
    target_host: str
    asset_name: str
    fbx_file: str
    manifest_file: str


def state_path(settings: BridgeSettings) -> Path:
    return settings.fbx_path.parent / "latest_transfer.json"


def write_latest(settings: BridgeSettings, source_host: str, asset_name: str) -> None:
    state = TransferState(
        source_host=source_host,
        target_host=HOST_TARGETS.get(source_host, "dcc"),
        asset_name=asset_name,
        fbx_file=str(settings.fbx_path),
        manifest_file=str(settings.manifest_path),
    )
    path = state_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2, sort_keys=True), encoding="utf-8")


def apply_latest_for_import(settings: BridgeSettings, target_host: str) -> None:
    path = state_path(settings)
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("target_host") != target_host:
        return
    fbx_file = Path(data.get("fbx_file", ""))
    if fbx_file.exists():
        settings.fbx_path = fbx_file

