from __future__ import annotations

from pathlib import Path


def maya_bootstrap_command(project_root: Path, port: int) -> str:
    dcc_src = project_root / "dcc_sources"
    root_path = dcc_src if dcc_src.exists() else project_root
    root_posix = root_path.as_posix()
    return (
        "python("
        f"\"import sys, os; root='{root_posix}'; parent = os.path.dirname(root) if 'dcc_sources' in root else None; sys.path = [p for p in sys.path if (not parent or p.replace(chr(92), '/').rstrip('/') != parent.replace(chr(92), '/').rstrip('/')) and ('Flux.dist' not in p.replace(chr(92), '/') or 'dcc_sources' in p.replace(chr(92), '/')) and ('Programs/Flux' not in p.replace(chr(92), '/') or 'dcc_sources' in p.replace(chr(92), '/'))]; "
        "sys.path.insert(0, root) if root not in sys.path else None; "
        "from flux_dcc import maya_server; "
        f"maya_server.start({port})\""
        ")"
    )


def blender_bootstrap_expr(project_root: Path, port: int) -> str:
    dcc_src = project_root / "dcc_sources"
    root_path = dcc_src if dcc_src.exists() else project_root
    root_posix = root_path.as_posix()
    return (
        "import sys, os; "
        f"root='{root_posix}'; parent = os.path.dirname(root) if 'dcc_sources' in root else None; sys.path = [p for p in sys.path if (not parent or p.replace(chr(92), '/').rstrip('/') != parent.replace(chr(92), '/').rstrip('/')) and ('Flux.dist' not in p.replace(chr(92), '/') or 'dcc_sources' in p.replace(chr(92), '/')) and ('Programs/Flux' not in p.replace(chr(92), '/') or 'dcc_sources' in p.replace(chr(92), '/'))]; "
        "sys.path.insert(0, root) if root not in sys.path else None; "
        "from flux_dcc import blender_server; "
        f"blender_server.start({port})"
    )


def bridge_action_code(
    host: str,
    action: str,
    exchange_dir: Path,
    update_existing: bool = True,
    sync_transforms: bool = False,
    freeze_transforms: bool = True,
) -> str:
    if host not in {"maya", "blender"}:
        raise ValueError(host)
    if action not in {"export", "import"}:
        raise ValueError(action)

    class_name = "MayaBridgeHost" if host == "maya" else "BlenderBridgeHost"
    module_name = "hosts.maya_bridge" if host == "maya" else "hosts.blender_bridge"
    method = "export_selected" if action == "export" else "import_fbx"
    exchange_posix = exchange_dir.as_posix()
    return "\n".join(
        [
            "import sys",
            "if 'bridge_core.settings' in sys.modules: del sys.modules['bridge_core.settings']",
            f"if '{module_name}' in sys.modules: del sys.modules['{module_name}']",
            "from pathlib import Path",
            "from bridge_core.settings import BridgeSettings",
            f"from {module_name} import {class_name}",
            (
                f"settings = BridgeSettings(fbx_path=Path('{exchange_posix}') / 'flux_transfer.fbx', "
                f"update_existing={update_existing}, sync_transforms={sync_transforms}, "
                f"freeze_transforms={freeze_transforms})"
            ),
            f"{class_name}().{method}(settings)",
        ]
    )
