from __future__ import annotations

from bridge_core.dependencies import ensure_pyqt6
from hosts.blender_bridge import BlenderBridgeHost


_WINDOW = None


def show():
    ensure_pyqt6("blender")
    from ui.bridge_window import show_window

    global _WINDOW
    _WINDOW = show_window(BlenderBridgeHost())
    return _WINDOW


if __name__ == "__main__":
    show()
