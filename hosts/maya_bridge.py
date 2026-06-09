from __future__ import annotations

from typing import Any

from bridge_core.host_base import BridgeHost
from bridge_core.manifest import BridgeManifest, MeshRecord
from bridge_core.naming import sanitize_name, transfer_path
from bridge_core.settings import BridgeSettings
from bridge_core.state import apply_latest_for_import, write_latest


try:
    import maya.cmds as cmds
    import maya.mel as mel
except Exception:  # pragma: no cover - only available inside Maya
    cmds = None
    mel = None


class MayaBridgeHost(BridgeHost):
    host_name = "maya"

    def _require_maya(self) -> None:
        if cmds is None or mel is None:
            raise RuntimeError("Maya Python APIs are not available. Run this adapter inside Maya.")

    def export_selected(self, settings: BridgeSettings) -> BridgeManifest:
        self._require_maya()
        settings.ensure_exchange_dir()
        
        selection = cmds.ls(selection=True, long=True) or []
        mesh_transforms = []
        for node in selection:
            if cmds.nodeType(node) == "transform" and self._has_mesh_shape(node):
                mesh_transforms.append(node)
            elif cmds.nodeType(node) == "mesh":
                parent = cmds.listRelatives(node, parent=True, fullPath=True)
                if parent:
                    mesh_transforms.append(parent[0])
                    
        # Maintain order and filter unique transforms
        mesh_transforms = list(dict.fromkeys(mesh_transforms))
        
        if settings.selected_only and not mesh_transforms:
            raise RuntimeError("Select at least one polygon mesh object in Maya before exporting.")
            
        active_name = self._short_name(mesh_transforms[0]) if mesh_transforms else "scene"
        if mesh_transforms:
            settings.fbx_path = transfer_path(settings, active_name, self.host_name)
            
        self._load_fbx_plugin()
        manifest = self.collect_manifest(settings)
        self._configure_fbx_export(settings)
        
        # Delete modeling/normal construction history to clean normal history before export
        for node in mesh_transforms:
            try:
                cmds.bakePartialHistory(node, preDeformers=True)
            except Exception:
                try:
                    cmds.delete(node, ch=True)
                except Exception:
                    pass
        
        fbx_path = settings.fbx_path.as_posix()
        if settings.selected_only:
            # Temporarily re-select only valid mesh transforms to guarantee Maya MEL FBXExport -s has zero errors
            cmds.select(mesh_transforms, replace=True)
            mel.eval(f'FBXExport -f "{fbx_path}" -s')
            # Restore user selection list
            if selection:
                cmds.select(selection, replace=True)
        else:
            mel.eval(f'FBXExport -f "{fbx_path}"')
            
        manifest.write(settings.manifest_path)
        write_latest(settings, self.host_name, active_name)
        return manifest

    def import_fbx(self, settings: BridgeSettings) -> BridgeManifest | None:
        self._require_maya()
        self._load_fbx_plugin()
        apply_latest_for_import(settings, self.host_name)
        if not settings.fbx_path.exists():
            raise FileNotFoundError(settings.fbx_path)
 
        manifest = BridgeManifest.read(settings.manifest_path) if settings.manifest_path.exists() else None
        before = set(cmds.ls(long=True, type="transform") or [])
        before_by_name = {
            sanitize_name(self._short_name(node)): node
            for node in before
            if self._has_mesh_shape(node)
        }
        self._configure_fbx_import(settings)
        self._import_file(settings.fbx_path.as_posix())
        after = set(cmds.ls(long=True, type="transform") or [])
        imported = sorted(after - before)
        
        # Unfreeze custom normals on all newly imported mesh nodes to cure the locked-normals black mesh bug
        # and apply sharp edges from the manifest to restore smooth/hard edge shading
        for node in imported:
            if self._has_mesh_shape(node):
                try:
                    cmds.polyNormalPerVertex(node, unFreezeNormal=True)
                except Exception:
                    pass
                if manifest and settings.preserve_smoothing:
                    try:
                        by_short_name = {self._short_name(record.name): record for record in manifest.meshes}
                        key = self._match_key(node, by_short_name)
                        record = by_short_name.get(key) if key else None
                        if record:
                            self._apply_sharp_edges(node, record.sharp_edges)
                    except Exception:
                        pass
                    
        if settings.update_existing and manifest:
            updated = self._update_existing_meshes(imported, manifest, before_by_name, settings)
            if updated:
                cmds.select(updated, replace=True)
        elif imported:
            cmds.select(imported, replace=True)
 
        if manifest:
            self.apply_manifest(manifest, settings)
        return manifest

    def collect_manifest(self, settings: BridgeSettings) -> BridgeManifest:
        self._require_maya()
        transforms = cmds.ls(selection=settings.selected_only, long=True, type="transform") or []
        mesh_transforms = [node for node in transforms if self._has_mesh_shape(node)]
        records = [self._record_for_transform(node) for node in mesh_transforms]
        self._merge_previous_blender_metadata(records, settings)
        return BridgeManifest(
            source_host=self.host_name,
            source_version=str(cmds.about(version=True)),
            fbx_file=str(settings.fbx_path),
            meshes=records,
        )

    def apply_manifest(self, manifest: BridgeManifest, settings: BridgeSettings) -> None:
        self._require_maya()
        by_short_name = {self._short_name(record.name): record for record in manifest.meshes}
        scale_factor = 100.0 if manifest.source_host == "blender" else 1.0
        for transform in cmds.ls(selection=True, long=True, type="transform") or []:
            short_name = self._short_name(transform)
            record = by_short_name.get(short_name)
            if not record:
                continue
            if settings.sync_transforms and record.matrix_world:
                mat_data = list(record.matrix_world)
                if len(mat_data) == 16:
                    if manifest.source_host == "blender":
                        mat_data = self._blender_to_maya_matrix(mat_data)
                    else:
                        mat_data[12] *= scale_factor
                        mat_data[13] *= scale_factor
                        mat_data[14] *= scale_factor
                cmds.xform(transform, worldSpace=True, matrix=mat_data)
            if settings.sync_transforms and settings.preserve_pivots and record.rotate_pivot:
                scaled_pivot = [val * scale_factor for val in record.rotate_pivot]
                cmds.xform(transform, worldSpace=True, rotatePivot=scaled_pivot)
            if settings.sync_transforms and settings.preserve_pivots and record.scale_pivot:
                scaled_pivot = [val * scale_factor for val in record.scale_pivot]
                cmds.xform(transform, worldSpace=True, scalePivot=scaled_pivot)
            if settings.preserve_custom_properties:
                self._apply_custom_properties(transform, record.custom_properties)
            if settings.preserve_smoothing:
                try:
                    cmds.polyNormalPerVertex(transform, unFreezeNormal=True)
                    self._apply_sharp_edges(transform, record.sharp_edges)
                except Exception:
                    pass

    def _load_fbx_plugin(self) -> None:
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya")

    def _configure_fbx_export(self, settings: BridgeSettings) -> None:
        self._try_mel("FBXResetExport")
        self._try_mel("FBXExportInAscii -v false")
        self._try_mel(f"FBXExportSmoothingGroups -v {str(settings.preserve_smoothing).lower()}")
        self._try_mel("FBXExportHardEdges -v false")
        self._try_mel("FBXExportSplitPerVertexNormals -v false")
        self._try_mel("FBXExportTangents -v true")
        self._try_mel("FBXExportSmoothMesh -v true")
        self._try_mel(f"FBXExportTriangulate -v {str(settings.triangulate).lower()}")
        self._try_mel(f"FBXExportEmbeddedTextures -v {str(settings.embed_textures).lower()}")
        self._try_mel("FBXExportSkins -v true")
        self._try_mel("FBXExportShapes -v true")
        self._try_mel("FBXExportConstraints -v true")
        self._try_mel("FBXExportCameras -v false")
        self._try_mel("FBXExportLights -v false")

    def _configure_fbx_import(self, settings: BridgeSettings) -> None:
        self._try_mel("FBXResetImport")
        self._try_mel("FBXImportMode -v add")
        self._try_mel("FBXImportHardEdges -v true")
        self._try_mel("FBXImportFillTimeline -v false")

    def _try_mel(self, command: str) -> None:
        try:
            cmd_name = command.split()[0] if command else ""
            if cmd_name:
                info = mel.eval(f'whatIs "{cmd_name}"')
                if info != "Unknown":
                    mel.eval(command)
        except Exception:
            pass

    def _has_mesh_shape(self, transform: str) -> bool:
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
        return any(cmds.nodeType(shape) == "mesh" for shape in shapes)

    def _record_for_transform(self, transform: str) -> MeshRecord:
        parent = (cmds.listRelatives(transform, parent=True, fullPath=True) or [None])[0]
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True, type="mesh") or []
        uv_layers = []
        for shape in shapes:
            uv_layers.extend(cmds.polyUVSet(shape, query=True, allUVSets=True) or [])
 
        return MeshRecord(
            name=self._short_name(transform),
            host_name=transform,
            parent=self._short_name(parent) if parent else None,
            matrix_world=list(cmds.xform(transform, query=True, worldSpace=True, matrix=True)),
            rotate_pivot=list(cmds.xform(transform, query=True, worldSpace=True, rotatePivot=True)),
            scale_pivot=list(cmds.xform(transform, query=True, worldSpace=True, scalePivot=True)),
            material_slots=self._materials_for_transform(transform),
            uv_layers=sorted(set(uv_layers)),
            sharp_edges=self._sharp_edges(transform),
            seam_edges=[],
            custom_properties=self._custom_properties(transform),
        )

    def _sharp_edges(self, transform: str) -> list[list[int]]:
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True, type="mesh") or []
        if not shapes:
            return []
        shape = shapes[0]
        
        try:
            # Query smooth/hard properties for all edges (True = smooth, False = hard/sharp)
            edge_states = cmds.polyEdge(shape + ".e[*]", query=True, l=True) or []
        except Exception:
            return []
            
        hard_edges = []
        for index, is_smooth in enumerate(edge_states):
            if not is_smooth:
                try:
                    info = cmds.polyInfo(f"{shape}.e[{index}]", edgeToVertex=True)[0]
                    # Parse EDGE index: v1 v2
                    tokens = info.split()
                    v1 = int(tokens[2])
                    v2 = int(tokens[3])
                    hard_edges.append([v1, v2])
                except Exception:
                    continue
        return hard_edges
 
    def _merge_previous_blender_metadata(self, records: list[MeshRecord], settings: BridgeSettings) -> None:
        previous_records: dict[str, MeshRecord] = {}
        for manifest_path in sorted(settings.fbx_path.parent.glob("*.bridge_manifest.json")):
            try:
                manifest = BridgeManifest.read(manifest_path)
            except Exception:
                continue
            if manifest.source_host != "blender":
                continue
            for record in manifest.meshes:
                previous_records.setdefault(self._short_name(record.name), record)
 
        for record in records:
            previous = previous_records.get(self._short_name(record.name))
            if not previous:
                continue
            if not record.sharp_edges and getattr(previous, "sharp_edges", None):
                record.sharp_edges = previous.sharp_edges
            if getattr(previous, "seam_edges", None):
                record.seam_edges = previous.seam_edges
            if getattr(previous, "vertex_groups", None):
                record.vertex_groups = previous.vertex_groups
            if getattr(previous, "material_slots", None):
                record.material_slots = previous.material_slots

    def _update_existing_meshes(
        self,
        imported: list[str],
        manifest: BridgeManifest,
        before_by_name: dict[str, str],
        settings: BridgeSettings,
    ) -> list[str]:
        records = {sanitize_name(record.name): record for record in manifest.meshes}
        updated = []
        for imported_transform in imported:
            if not self._has_mesh_shape(imported_transform):
                continue
            key = self._match_key(imported_transform, records)
            record = records.get(key) if key else None
            target = before_by_name.get(key) if key else None
            if not record or not target or target == imported_transform:
                if record:
                    imported_transform = self._rename_transform(imported_transform, record.name)
                updated.append(imported_transform)
                continue

            self._replace_mesh_shapes(target, imported_transform)
            # Unfreeze custom normals on target to cure the locked-normals black mesh bug after shape replacement
            if settings.preserve_smoothing and record:
                try:
                    self._apply_sharp_edges(target, record.sharp_edges)
                except Exception:
                    pass
                
            if settings.preserve_custom_properties:
                self._apply_custom_properties(target, record.custom_properties)
            try:
                cmds.delete(imported_transform)
            except Exception:
                pass
            updated.append(target)
        return updated

    def _replace_mesh_shapes(self, target: str, imported_transform: str) -> None:
        target_matrix = cmds.xform(target, query=True, worldSpace=True, matrix=True)
        target_rotate_pivot = cmds.xform(target, query=True, worldSpace=True, rotatePivot=True)
        target_scale_pivot = cmds.xform(target, query=True, worldSpace=True, scalePivot=True)

        old_shapes = cmds.listRelatives(target, shapes=True, fullPath=True, type="mesh") or []
        new_shapes = []
        duplicated_transform = cmds.duplicate(imported_transform, renameChildren=True)[0]
        duplicated_shapes = cmds.listRelatives(duplicated_transform, shapes=True, fullPath=True, type="mesh") or []
        for dup_shape in duplicated_shapes:
            parented = cmds.parent(dup_shape, target, shape=True, relative=True)[0]
            new_shapes.append(parented)
        cmds.delete(duplicated_transform)

        if old_shapes:
            cmds.delete(old_shapes)
        for index, shape in enumerate(new_shapes):
            try:
                cmds.rename(shape, f"{self._short_name(target)}Shape{index + 1 if index else ''}")
            except Exception:
                pass

        cmds.xform(target, worldSpace=True, matrix=target_matrix)
        cmds.xform(target, worldSpace=True, rotatePivot=target_rotate_pivot)
        cmds.xform(target, worldSpace=True, scalePivot=target_scale_pivot)

    def _rename_transform(self, transform: str, desired_name: str) -> str:
        try:
            return cmds.rename(transform, desired_name)
        except Exception:
            return transform

    def _match_key(self, transform: str, records: dict[str, MeshRecord]) -> str | None:
        clean = sanitize_name(self._short_name(transform))
        if clean in records:
            return clean
        for key in records:
            if clean.startswith(key):
                return key
        return next(iter(records)) if len(records) == 1 else None

    def _import_file(self, fbx_path: str) -> None:
        try:
            mel.eval(f'FBXImport -f "{fbx_path}"')
            return
        except Exception:
            pass
        cmds.file(
            fbx_path,
            i=True,
            type="FBX",
            ignoreVersion=True,
            ra=True,
            mergeNamespacesOnClash=False,
            namespace=":",
            options="fbx",
            preserveReferences=True,
        )

    def _materials_for_transform(self, transform: str) -> list[str]:
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True, type="mesh") or []
        shading_groups = set()
        for shape in shapes:
            shading_groups.update(cmds.listConnections(shape, type="shadingEngine") or [])
        materials = []
        for sg in sorted(shading_groups):
            materials.extend(cmds.ls(cmds.listConnections(f"{sg}.surfaceShader") or [], materials=True) or [])
        return sorted(set(materials))

    def _custom_properties(self, transform: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for attr in cmds.listAttr(transform, userDefined=True) or []:
            plug = f"{transform}.{attr}"
            try:
                result[attr] = cmds.getAttr(plug)
            except Exception:
                continue
        return result

    def _apply_custom_properties(self, transform: str, properties: dict[str, Any]) -> None:
        for name, value in properties.items():
            if cmds.attributeQuery(name, node=transform, exists=True):
                continue
            try:
                if isinstance(value, bool):
                    cmds.addAttr(transform, longName=name, attributeType="bool")
                elif isinstance(value, int):
                    cmds.addAttr(transform, longName=name, attributeType="long")
                elif isinstance(value, float):
                    cmds.addAttr(transform, longName=name, attributeType="double")
                else:
                    cmds.addAttr(transform, longName=name, dataType="string")
                if isinstance(value, str):
                    cmds.setAttr(f"{transform}.{name}", value, type="string")
                else:
                    cmds.setAttr(f"{transform}.{name}", value)
            except Exception:
                continue

    def _apply_sharp_edges(self, transform: str, sharp_edges: list[list[int]]) -> None:
        shapes = cmds.listRelatives(transform, shapes=True, fullPath=True, type="mesh") or []
        if not shapes:
            return
        shape = shapes[0]
        
        # Soften all edges first
        try:
            cmds.polySoftEdge(shape, angle=180, constructionHistory=False)
        except Exception:
            return
            
        if not sharp_edges:
            return
            
        # Match vertex index pairs to edge indices
        try:
            edge_infos = cmds.polyInfo(shape + ".e[*]", edgeToVertex=True) or []
        except Exception:
            return
            
        sharp_set = {tuple(sorted(edge)) for edge in sharp_edges if len(edge) == 2}
        edges_to_harden = []
        for info in edge_infos:
            try:
                tokens = info.split()
                edge_idx = int(tokens[1].replace(":", ""))
                v1 = int(tokens[2])
                v2 = int(tokens[3])
                if tuple(sorted((v1, v2))) in sharp_set:
                    edges_to_harden.append(f"{shape}.e[{edge_idx}]")
            except Exception:
                continue
                
        if edges_to_harden:
            try:
                cmds.polySoftEdge(edges_to_harden, angle=0, constructionHistory=False)
            except Exception:
                pass

    def _blender_to_maya_matrix(self, matrix_blender: list[float]) -> list[float]:
        # Reconstruct as a 4x4 list of lists (row-major)
        Mb = [matrix_blender[i:i+4] for i in range(0, 16, 4)]
        
        # Temp = Mb @ C
        Temp = [[0.0]*4 for _ in range(4)]
        for r in range(4):
            Temp[r][0] = Mb[r][0] * 0.01
            Temp[r][1] = Mb[r][2] * 0.01
            Temp[r][2] = -Mb[r][1] * 0.01
            Temp[r][3] = Mb[r][3]
            
        # M_maya_t = C_inv @ Temp
        M_maya_t = [
            [Temp[0][0] * 100.0, Temp[0][1] * 100.0, Temp[0][2] * 100.0, Temp[0][3] * 100.0],
            [Temp[2][0] * 100.0, Temp[2][1] * 100.0, Temp[2][2] * 100.0, Temp[2][3] * 100.0],
            [Temp[1][0] * -100.0, Temp[1][1] * -100.0, Temp[1][2] * -100.0, Temp[1][3] * -100.0],
            [Temp[3][0], Temp[3][1], Temp[3][2], Temp[3][3]]
        ]
        
        # Transpose M_maya_t to get Maya's row-vector layout
        M_maya = []
        for r in range(4):
            for c in range(4):
                M_maya.append(M_maya_t[c][r])
                
        return M_maya

    def _short_name(self, name: str | None) -> str:
        if not name:
            return ""
        return name.split("|")[-1].split(":")[-1]
