from __future__ import annotations

import sys

from bridge_core.dependencies import ensure_pyqt6


def main() -> int:
    ensure_pyqt6("flux")
    from flux.flux_window import main as flux_main

    return flux_main()


if __name__ == "__main__":
    raise SystemExit(main())

