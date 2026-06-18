from __future__ import annotations

import tempfile
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from bridge_core.manifest import BridgeManifest, MeshRecord
from bridge_core.settings import BridgeSettings


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fbx_path = Path(tmp) / "asset.fbx"
        settings = BridgeSettings(fbx_path=fbx_path)
        manifest = BridgeManifest(
            source_host="test",
            source_version="1.0",
            fbx_file=str(settings.fbx_path),
            meshes=[
                MeshRecord(
                    name="Cube",
                    host_name="|Cube",
                    matrix_world=[1.0 if index in (0, 5, 10, 15) else 0.0 for index in range(16)],
                    uv_layers=["map1"],
                    sharp_edges=[[0, 1], [2, 3]],
                    vertex_groups=[{"name": "Pin", "index": 0, "weights": [[0, 1.0], [2, 0.5]]}],
                    custom_properties={"asset_id": "hero_prop"},
                )
            ],
        )
        manifest.write(settings.manifest_path)
        loaded = BridgeManifest.read(settings.manifest_path)
        assert loaded.source_host == "test"
        assert loaded.meshes[0].name == "Cube"
        assert loaded.meshes[0].uv_layers == ["map1"]
        assert loaded.meshes[0].sharp_edges == [[0, 1], [2, 3]]
        assert loaded.meshes[0].vertex_groups[0]["name"] == "Pin"
        assert loaded.meshes[0].custom_properties["asset_id"] == "hero_prop"
        
    print("Smoke test passed")


if __name__ == "__main__":
    main()
