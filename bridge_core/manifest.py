from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1


@dataclass(slots=True)
class MeshRecord:
    name: str
    host_name: str
    parent: str | None = None
    matrix_world: list[float] = field(default_factory=list)
    rotate_pivot: list[float] | None = None
    scale_pivot: list[float] | None = None
    object_origin: list[float] | None = None
    material_slots: list[str] = field(default_factory=list)
    uv_layers: list[str] = field(default_factory=list)
    sharp_edges: list[list[int]] = field(default_factory=list)
    seam_edges: list[list[int]] = field(default_factory=list)
    vertex_groups: list[dict[str, Any]] = field(default_factory=list)
    custom_properties: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BridgeManifest:
    source_host: str
    source_version: str
    fbx_file: str
    meshes: list[MeshRecord] = field(default_factory=list)
    unit_scale: float = 0.01
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BridgeManifest":
        meshes = [MeshRecord(**mesh) for mesh in data.get("meshes", [])]
        return cls(
            source_host=data["source_host"],
            source_version=data.get("source_version", "unknown"),
            fbx_file=data["fbx_file"],
            meshes=meshes,
            unit_scale=float(data.get("unit_scale", 0.01)),
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
        )

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "BridgeManifest":
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))
