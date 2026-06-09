bl_info = {
    "name": "Maya Blender FBX Bridge",
    "author": "TA Storage",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "3D View > Sidebar > FBX Bridge",
    "description": "Launch the PyQt6 FBX bridge for Maya and Blender transfers.",
    "category": "Import-Export",
}

import sys
from pathlib import Path

import bpy


DEFAULT_PROJECT_ROOT = r"D:\Local_P4\TA_Storage\Jaisurya\Maya Blender workflow"


def _addon_preferences(context):
    addon = context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


def _project_root(context) -> Path:
    preferences = _addon_preferences(context)
    configured_path = preferences.project_root if preferences else DEFAULT_PROJECT_ROOT
    root = Path(configured_path).expanduser()
    if (root / "launch_blender.py").exists():
        return root

    local_root = Path(__file__).resolve().parent
    if (local_root / "launch_blender.py").exists():
        return local_root

    raise FileNotFoundError(
        "Could not find launch_blender.py. Set the Bridge Project Folder in this add-on's preferences."
    )


class MBFBXBRIDGE_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    project_root: bpy.props.StringProperty(
        name="Bridge Project Folder",
        subtype="DIR_PATH",
        default=DEFAULT_PROJECT_ROOT,
        description="Folder containing launch_blender.py, bridge_core, hosts, and ui",
    )

    def draw(self, context):
        self.layout.prop(self, "project_root")


class MBFBXBRIDGE_OT_show(bpy.types.Operator):
    bl_idname = "mb_fbx_bridge.show"
    bl_label = "Open FBX Bridge"

    def execute(self, context):
        try:
            root = str(_project_root(context))
            if root not in sys.path:
                sys.path.insert(0, root)
            import launch_blender

            launch_blender.show()
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class MBFBXBRIDGE_PT_panel(bpy.types.Panel):
    bl_label = "FBX Bridge"
    bl_idname = "MBFBXBRIDGE_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "FBX Bridge"

    def draw(self, context):
        preferences = _addon_preferences(context)
        if preferences:
            self.layout.prop(preferences, "project_root", text="")
        self.layout.operator(MBFBXBRIDGE_OT_show.bl_idname)


CLASSES = (MBFBXBRIDGE_preferences, MBFBXBRIDGE_OT_show, MBFBXBRIDGE_PT_panel)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
