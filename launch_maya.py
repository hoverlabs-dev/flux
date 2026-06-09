from __future__ import annotations

from bridge_core.dependencies import ensure_pyqt6
from hosts.maya_bridge import MayaBridgeHost


_WINDOW = None


def show():
    ensure_pyqt6("maya")
    from ui.bridge_window import show_window

    global _WINDOW
    _WINDOW = show_window(MayaBridgeHost())
    return _WINDOW


if __name__ == "__main__":
    show()
