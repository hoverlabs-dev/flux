# Portal - Maya Blender Asset Bridge (FBX)

A standalone PyQt6 launchpad for moving selected mesh assets between Maya 2024 and Blender 4.5 using FBX while preserving the data artists care about: UVs, normals/smoothing, materials, transforms, pivots, hierarchy, sharp edges, and custom properties where the host APIs expose them.

The main app is:

```text
Portal - Maya Blender Asset Bridge (FBX)
```

Launch it with:

```powershell
.\Launch Portal.bat
```

or:

```powershell
python run_portal.py
```

## Portal Workflow

1. Open Portal from the shared tool folder.
2. Set the Maya 2024 executable, Blender 4.5 executable, and exchange folder.
3. Click **Launch Maya** and/or **Launch Blender** from Portal.
4. Select a mesh in the DCC.
5. Use Portal buttons:
   - **Maya: Export Selection**
   - **Maya: Import Latest**
   - **Blender: Export Selection**
   - **Blender: Import Latest**

Portal launches each DCC with a tiny local command server, then sends export/import commands to that DCC. This keeps the main UI outside Maya and Blender. Maya uses Portal's own socket server on port `7821`, avoiding Maya's built-in `commandPort`.

By default Portal uses an asset-update workflow:

- **Update existing mesh by name** is enabled. If `Cube` already exists, importing `Cube` updates that object's mesh data instead of creating `Cube.001` or `Cube1`.
- **Sync transforms and pivots** is disabled. The destination object's translate/rotate/scale/pivot stays stable while geometry, UVs, normals, materials, smoothing, hard edges, and tracked metadata update.
- Enable transform sync only when the scene explicitly needs source-DCC transforms stamped onto the destination object.

Blender is treated as the source of truth for look-development data:

- Existing Blender material slots and shader datablocks are preserved when a Maya-edited mesh comes back.
- FBX-created duplicate materials such as `mymaterial.001` are remapped back to the existing Blender material when names match.
- Blender vertex groups are stored in the sidecar manifest and restored after the mesh is updated.
- Maya is expected to be used mainly for modeling and UV edits. Avoid changing material/shader ownership in Maya for assets whose look is maintained in Blender.

The tool is built as:

- `portal`: standalone launchpad UI and process controls.
- `portal_dcc`: small Maya/Blender command server bootstraps.
- `bridge_core`: host-independent transfer settings, manifest sidecar, paths, and logging.
- `hosts/maya_bridge.py`: Maya exporter/importer adapter.
- `hosts/blender_bridge.py`: Blender exporter/importer adapter.
- `ui/bridge_window.py`: legacy embedded PyQt6 interface.
- `launch_maya.py` and `launch_blender.py`: one-button launchers for each DCC.

## What It Does

- Exports selected mesh transforms/objects from Maya or Blender to FBX.
- Imports the last exported bridge FBX into the other app.
- Writes a JSON manifest next to the FBX with extra metadata that FBX commonly loses or host importers interpret differently.
- Reapplies supported metadata after import, including object transforms, custom properties, Maya rotate/scale pivots, and Blender object origin approximation.
- Carries Blender marked-sharp edges through Maya in the manifest and reapplies them when the asset returns to Blender.

## Requirements

- Maya 2024 with FBX plugin enabled.
- Blender 4.5.
- Windows 64-bit workstations using the shared project folder.

PyQt6 is vendored inside this project under:

```text
vendor/python/py310
vendor/python/py311
```

The launchers add the matching folder to `sys.path` automatically. Artists do not need to install PyQt6 on each machine.

If the shared dependency folder ever needs to be rebuilt, run this once from the project folder on an internet-connected TD/admin machine:

```powershell
python scripts/stage_pyqt6_runtime.py
```

## Legacy Embedded Launch

### Maya

Run this in Maya Script Editor as Python:

```python
import sys
sys.path.insert(0, r"D:\Local_P4\TA_Storage\Jaisurya\Maya Blender workflow")
import launch_maya
launch_maya.show()
```

To install a shelf button, run this once in Maya Script Editor as Python:

```python
import sys
sys.path.insert(0, r"D:\Local_P4\TA_Storage\Jaisurya\Maya Blender workflow")
import install_maya
install_maya.install_shelf_button()
```

You can also drag `install_maya.py` directly into the Maya viewport. It creates/selects a custom shelf tab named **FBX Bridge** and adds the launcher button there.

### Blender

Run this in Blender Python console or Text Editor:

```python
import sys
sys.path.insert(0, r"D:\Local_P4\TA_Storage\Jaisurya\Maya Blender workflow")
import launch_blender
launch_blender.show()
```

To install a Blender sidebar button, install `blender_addon.py` from Blender Preferences > Add-ons > Install, then enable **Maya Blender FBX Bridge**. The button appears in 3D View > Sidebar > FBX Bridge.

Blender copies single-file add-ons into its add-ons folder, so the add-on has a **Bridge Project Folder** preference. Set it to the shared server project folder if needed:

```text
D:\Local_P4\TA_Storage\Jaisurya\Maya Blender workflow
```

When moved to the server, replace this path with the final UNC/share path, for example:

```text
\\server\tools\Maya Blender workflow
```

## Default Bridge Folder

Exports are written to:

```text
<project>/exchange/<asset>__maya_to_blender.fbx
<project>/exchange/<asset>__blender_to_maya.fbx
<project>/exchange/<asset>__*.bridge_manifest.json
<project>/exchange/latest_transfer.json
```

The import button reads `latest_transfer.json`, so Maya automatically picks the latest Blender-to-Maya FBX and Blender automatically picks the latest Maya-to-Blender FBX. Re-exporting the same asset overwrites its deterministic exchange file instead of creating a new numbered file.

## Notes on Data Preservation

FBX is good for mesh exchange but not perfectly identical across DCCs. This bridge therefore uses:

- Conservative FBX options.
- Explicit normal/tangent/UV/material export settings.
- Maya FBX plugin MEL options for smoothing groups, tangents, constraints, pivots, and units.
- Blender FBX operator settings for custom normals, leaf bones off, axes, object selection, and custom properties.
- A manifest sidecar for pivots, transforms, hierarchy names, object IDs, and custom properties.
- Blender marked-sharp edge data stored in the manifest because Maya/FBX do not preserve Blender's editor flag directly.
- Blender vertex groups stored in the manifest by vertex index/weight so they can survive a Maya modeling/UV pass when topology remains compatible.

For production, validate with representative client assets before rolling out studio-wide. The included smoke test checks the pure Python core; full DCC round-trip validation must run inside Maya and Blender.

## Smoke Test

```powershell
python scripts/smoke_test.py
```
