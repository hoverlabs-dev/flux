from __future__ import annotations

from abc import ABC, abstractmethod

from .manifest import BridgeManifest
from .settings import BridgeSettings


class BridgeHost(ABC):
    host_name: str

    @abstractmethod
    def export_selected(self, settings: BridgeSettings) -> BridgeManifest:
        raise NotImplementedError

    @abstractmethod
    def import_fbx(self, settings: BridgeSettings) -> BridgeManifest | None:
        raise NotImplementedError

    @abstractmethod
    def collect_manifest(self, settings: BridgeSettings) -> BridgeManifest:
        raise NotImplementedError

    @abstractmethod
    def apply_manifest(self, manifest: BridgeManifest, settings: BridgeSettings) -> None:
        raise NotImplementedError

