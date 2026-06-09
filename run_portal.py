from __future__ import annotations

import sys

from bridge_core.dependencies import ensure_pyqt6


def main() -> int:
    ensure_pyqt6("portal")
    from portal.portal_window import main as portal_main

    return portal_main()


if __name__ == "__main__":
    raise SystemExit(main())

