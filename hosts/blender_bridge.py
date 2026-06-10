from __future__ import annotations

from bridge_core.host_base import BridgeHost
from bridge_core.manifest import BridgeManifest, MeshRecord
from bridge_core.naming import sanitize_name, transfer_path
from bridge_core.settings import BridgeSettings
from bridge_core.state import apply_latest_for_import, write_latest


try:
    import bpy
    from mathutils import Matrix
except Exception:  # pragma: no cover - only available inside Blender
    bpy = None
    Matrix = None


class BlenderBridgeHost(BridgeHost):
    host_name = "blender"

    def _require_blender(self) -> None:
        if bpy is None:
            raise RuntimeError("Blender Python APIs are not available. Run this adapter inside Blender.")

    def export_selected(self, settings: BridgeSettings) -> BridgeManifest:
        self._require_blender()
        settings.ensure_exchange_dir()
        objects = self._mesh_objects(settings.selected_only)
        if settings.selected_only and not objects:
            raise RuntimeError("Select at least one mesh object before exporting.")
        if objects:
            settings.fbx_path = transfer_path(settings, objects[0].name, self.host_name)

        manifest = self.collect_manifest(settings)

        if settings.freeze_transforms:
            duplicates = []
            orig_to_dup = {}
            # Deselect all first
            bpy.ops.object.select_all(action="DESELECT")
            
            for obj in objects:
                # Duplicate the object
                dup = obj.copy()
                dup.data = obj.data.copy()
                bpy.context.scene.collection.objects.link(dup)
                duplicates.append(dup)
                orig_to_dup[obj] = dup
                
                # Make the duplicate active and select it to apply transforms
                bpy.context.view_layer.objects.active = dup
                dup.select_set(True)
                
                # Apply translation, rotation, scale
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                
                # Deselect
                dup.select_set(False)
                
            # Select all duplicates for export
            for dup in duplicates:
                dup.select_set(True)
            if duplicates:
                bpy.context.view_layer.objects.active = duplicates[0]
                
            # Export duplicates
            bpy.ops.export_scene.fbx(
                filepath=str(settings.fbx_path),
                use_selection=True,  # Force selection only for duplicates
                object_types={"MESH", "EMPTY", "ARMATURE"},
                use_custom_props=False,
                bake_space_transform=True,
                apply_unit_scale=settings.apply_unit_scale,
                apply_scale_options="FBX_SCALE_UNITS",
                axis_forward=settings.axis_forward,
                axis_up=settings.axis_up,
                mesh_smooth_type="FACE" if settings.preserve_smoothing else "OFF",
                use_mesh_modifiers=True,
                use_mesh_edges=True,
                use_tspace=True,
                add_leaf_bones=False,
                path_mode="COPY" if settings.embed_textures else "AUTO",
                embed_textures=settings.embed_textures,
            )
            
            # Delete duplicates
            bpy.ops.object.delete()
            
            # Restore selection to original objects
            bpy.ops.object.select_all(action="DESELECT")
            for obj in objects:
                obj.select_set(True)
            if objects:
                bpy.context.view_layer.objects.active = objects[0]
        else:
            bpy.ops.export_scene.fbx(
                filepath=str(settings.fbx_path),
                use_selection=settings.selected_only,
                object_types={"MESH", "EMPTY", "ARMATURE"},
                use_custom_props=False,
                bake_space_transform=True,
                apply_unit_scale=settings.apply_unit_scale,
                apply_scale_options="FBX_SCALE_UNITS",
                axis_forward=settings.axis_forward,
                axis_up=settings.axis_up,
                mesh_smooth_type="FACE" if settings.preserve_smoothing else "OFF",
                use_mesh_modifiers=True,
                use_mesh_edges=True,
                use_tspace=True,
                add_leaf_bones=False,
                path_mode="COPY" if settings.embed_textures else "AUTO",
                embed_textures=settings.embed_textures,
            )
            
        manifest.write(settings.manifest_path)
        write_latest(settings, self.host_name, objects[0].name if objects else "selection")
        return manifest

    def import_fbx(self, settings: BridgeSettings) -> BridgeManifest | None:
        self._require_blender()
        apply_latest_for_import(settings, self.host_name)
        if not settings.fbx_path.exists():
            raise FileNotFoundError(settings.fbx_path)

        manifest = BridgeManifest.read(settings.manifest_path) if settings.manifest_path.exists() else None
        before_objects = set(bpy.context.scene.objects)
        bpy.ops.import_scene.fbx(
            filepath=str(settings.fbx_path),
            use_custom_props=False,  # Custom properties are restored via the manifest sidecar
            use_custom_normals=settings.preserve_smoothing,
            use_image_search=True,
            bake_space_transform=True,
            axis_forward=settings.axis_forward,
            axis_up=settings.axis_up,
        )
        imported = [obj for obj in bpy.context.scene.objects if obj not in before_objects]
        for obj in imported:
            if obj.type == "MESH":
                self._force_material_link_to_data(obj)
        if manifest and settings.preserve_pivots:
            by_short_name = {record.name: record for record in manifest.meshes}
            for obj in imported:
                if obj.type == "MESH":
                    key = self._match_key(obj.name, by_short_name)
                    record = by_short_name.get(key) if key else None
                    if record and record.rotate_pivot:
                        try:
                            if manifest.source_host == "maya":
                                scaled_pivot = [record.rotate_pivot[0] * 0.01, -record.rotate_pivot[2] * 0.01, record.rotate_pivot[1] * 0.01]
                            else:
                                scaled_pivot = record.rotate_pivot
                            self._set_object_pivot(obj, scaled_pivot)
                        except Exception:
                            pass
        if settings.update_existing and manifest:
            self._update_existing_meshes(imported, manifest, before_objects, settings)
        else:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in imported:
                obj.select_set(True)
            if imported:
                bpy.context.view_layer.objects.active = imported[0]

        if manifest:
            self.apply_manifest(manifest, settings)

        if manifest and settings.preserve_pivots:
            try:
                area = next((a for a in bpy.context.screen.areas if a.type == 'VIEW_3D'), None)
                region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                if area and region:
                    override = bpy.context.temp_override(area=area, region=region)
                    with override:
                        bpy.ops.object.transforms_to_deltas(mode='ALL')
                else:
                    bpy.ops.object.transforms_to_deltas(mode='ALL')
            except Exception:
                for obj in bpy.context.selected_objects:
                    if obj.type == "MESH":
                        try:
                            self._apply_transforms_to_deltas_python(obj)
                        except Exception:
                            pass
        return manifest

    def _update_existing_meshes(
        self,
        imported: list,
        manifest: BridgeManifest,
        before_objects: set,
        settings: BridgeSettings,
    ) -> None:
        records = {sanitize_name(record.name): record for record in manifest.meshes}
        existing = {
            sanitize_name(obj.name): obj
            for obj in before_objects
            if obj.type == "MESH"
        }
        updated = []

        for imported_obj in [obj for obj in imported if obj.type == "MESH"]:
            self._force_material_link_to_data(imported_obj)
            key = self._match_key(imported_obj.name, records)
            record = records.get(key) if key else None
            target = existing.get(key) if key else None
            if not record or not target:
                if record:
                    imported_obj.name = record.name
                    imported_obj.data.name = f"{record.name}Shape"
                    self._deduplicate_materials(imported_obj)
                    self._restore_vertex_groups(imported_obj, record.vertex_groups)
                updated.append(imported_obj)
                continue

            self._force_material_link_to_data(target)
            self._reset_delta_transforms(target)
            target.matrix_world = imported_obj.matrix_world
            old_mesh = target.data
            blender_materials = list(target.data.materials)
            target.data = imported_obj.data
            target.data.name = f"{target.name}Shape"
            if settings.preserve_pivots and record.rotate_pivot:
                try:
                    if manifest.source_host == "maya":
                        scaled_pivot = [record.rotate_pivot[0] * 0.01, -record.rotate_pivot[2] * 0.01, record.rotate_pivot[1] * 0.01]
                    else:
                        scaled_pivot = record.rotate_pivot
                    self._set_object_pivot(target, scaled_pivot)
                except Exception:
                    pass
            try:
                self._restore_material_slots(target, blender_materials, record.material_slots)
            except Exception:
                pass
            if settings.preserve_custom_properties:
                for custom_key, value in record.custom_properties.items():
                    try:
                        target[custom_key] = value
                    except TypeError:
                        if custom_key in target and custom_key not in target.bl_rna.properties:
                            try:
                                del target[custom_key]
                            except Exception:
                                pass
                        try:
                            target[custom_key] = value
                        except Exception:
                            pass
                    except Exception:
                        pass
            try:
                self._apply_sharp_edges(target, record.sharp_edges)
            except Exception:
                pass
            try:
                self._apply_seam_edges(target, getattr(record, "seam_edges", []))
            except Exception:
                pass
            try:
                self._restore_vertex_groups(target, record.vertex_groups)
            except Exception:
                pass
            try:
                bpy.data.objects.remove(imported_obj, do_unlink=True)
            except Exception:
                pass
            if old_mesh and old_mesh.users == 0:
                try:
                    bpy.data.meshes.remove(old_mesh)
                except Exception:
                    pass
            try:
                self._purge_unused_duplicate_materials(record.material_slots)
            except Exception:
                pass
            updated.append(target)

        bpy.ops.object.select_all(action="DESELECT")
        for obj in updated:
            obj.select_set(True)
        if updated:
            bpy.context.view_layer.objects.active = updated[0]

    def collect_manifest(self, settings: BridgeSettings) -> BridgeManifest:
        self._require_blender()
        records = [self._record_for_object(obj) for obj in self._mesh_objects(settings.selected_only)]
        return BridgeManifest(
            source_host=self.host_name,
            source_version=bpy.app.version_string,
            fbx_file=str(settings.fbx_path),
            meshes=records,
        )

    def apply_manifest(self, manifest: BridgeManifest, settings: BridgeSettings) -> None:
        self._require_blender()
        by_short_name = {record.name: record for record in manifest.meshes}
        for obj in bpy.context.selected_objects:
            record = by_short_name.get(obj.name.split(".")[0])
            if not record:
                continue
            if settings.sync_transforms and Matrix and record.matrix_world and len(record.matrix_world) == 16:
                try:
                    self._reset_delta_transforms(obj)
                    if manifest.source_host == "maya":
                        M_maya = Matrix([record.matrix_world[i:i+4] for i in range(0, 16, 4)])
                        M_maya_t = M_maya.transposed()
                        C = Matrix([
                            [0.01,  0.0,   0.0,  0.0],
                            [ 0.0,  0.0, -0.01,  0.0],
                            [ 0.0, 0.01,   0.0,  0.0],
                            [ 0.0,  0.0,   0.0,  1.0]
                        ])
                        C_inv = Matrix([
                            [100.0,   0.0,   0.0,  0.0],
                            [  0.0,   0.0, 100.0,  0.0],
                            [  0.0, -100.0,   0.0,  0.0],
                            [  0.0,   0.0,   0.0,  1.0]
                        ])
                        obj.matrix_world = C @ M_maya_t @ C_inv
                    else:
                        mat_data = list(record.matrix_world)
                        obj.matrix_world = Matrix([mat_data[index:index + 4] for index in range(0, 16, 4)])
                except Exception:
                    pass
            if settings.sync_transforms and settings.preserve_pivots and record.rotate_pivot:
                try:
                    if manifest.source_host == "maya":
                        scaled_pivot = [record.rotate_pivot[0] * 0.01, -record.rotate_pivot[2] * 0.01, record.rotate_pivot[1] * 0.01]
                    else:
                        scaled_pivot = record.rotate_pivot
                    self._set_object_pivot(obj, scaled_pivot)
                except Exception:
                    pass
            if settings.preserve_custom_properties:
                for key, value in record.custom_properties.items():
                    try:
                        obj[key] = value
                    except TypeError:
                        if key in obj and key not in obj.bl_rna.properties:
                            try:
                                del obj[key]
                            except Exception:
                                pass
                        try:
                            obj[key] = value
                        except Exception:
                            pass
                    except Exception:
                        pass
            try:
                self._apply_sharp_edges(obj, record.sharp_edges)
            except Exception:
                pass
            try:
                self._apply_seam_edges(obj, getattr(record, "seam_edges", []))
            except Exception:
                pass
            try:
                self._restore_vertex_groups(obj, record.vertex_groups)
            except Exception:
                pass

    def _mesh_objects(self, selected_only: bool) -> list:
        objects = bpy.context.selected_objects if selected_only else bpy.context.scene.objects
        return [obj for obj in objects if obj.type == "MESH"]

    def _record_for_object(self, obj) -> MeshRecord:
        return MeshRecord(
            name=obj.name,
            host_name=obj.name_full,
            parent=obj.parent.name if obj.parent else None,
            matrix_world=[value for row in obj.matrix_world for value in row],
            object_origin=list(obj.location),
            material_slots=[slot.material.name for slot in obj.material_slots if slot.material],
            uv_layers=[layer.name for layer in obj.data.uv_layers],
            sharp_edges=self._sharp_edges(obj),
            seam_edges=self._seam_edges(obj),
            vertex_groups=self._vertex_groups(obj),
            custom_properties={key: obj[key] for key in obj.keys() if self._is_json_safe(obj[key])},
        )

    def _is_json_safe(self, value) -> bool:
        return isinstance(value, (str, int, float, bool, list, tuple, dict, type(None)))

    def _vertex_groups(self, obj) -> list[dict]:
        groups = []
        for group in obj.vertex_groups:
            weights = []
            for vertex in obj.data.vertices:
                try:
                    weight = group.weight(vertex.index)
                except RuntimeError:
                    continue
                weights.append([int(vertex.index), float(weight)])
            groups.append({"name": group.name, "index": int(group.index), "weights": weights})
        return groups

    def _restore_vertex_groups(self, obj, vertex_groups: list[dict]) -> None:
        if obj.type != "MESH":
            return
        obj.vertex_groups.clear()
        vertex_count = len(obj.data.vertices)
        for group_data in vertex_groups or []:
            name = group_data.get("name")
            if not name:
                continue
            group = obj.vertex_groups.new(name=name)
            for vertex_index, weight in group_data.get("weights", []):
                vertex_index = int(vertex_index)
                if 0 <= vertex_index < vertex_count:
                    group.add([vertex_index], float(weight), "REPLACE")

    def _restore_material_slots(self, obj, blender_materials: list, manifest_material_names: list[str]) -> None:
        replacement_slots = []
        imported_materials = list(obj.data.materials)
        slot_count = max(len(imported_materials), len(blender_materials), len(manifest_material_names))
        for index in range(slot_count):
            material = None
            if index < len(blender_materials) and blender_materials[index]:
                material = blender_materials[index]
            if material is None and index < len(imported_materials) and imported_materials[index]:
                material = self._existing_material(imported_materials[index].name)
            if material is None and index < len(manifest_material_names):
                material = self._existing_material(manifest_material_names[index])
            replacement_slots.append(material)

        # Build mapping from imported index to replacement index
        mapping = {}
        for imp_idx, imp_mat in enumerate(imported_materials):
            if not imp_mat:
                mapping[imp_idx] = 0
                continue
            imp_base = sanitize_name(self._base_blender_name(imp_mat.name))
            matched_idx = None
            for rep_idx, rep_mat in enumerate(replacement_slots):
                if rep_mat and sanitize_name(self._base_blender_name(rep_mat.name)) == imp_base:
                    matched_idx = rep_idx
                    break
            if matched_idx is not None:
                mapping[imp_idx] = matched_idx
            else:
                mapping[imp_idx] = imp_idx if imp_idx < len(replacement_slots) else 0

        for slot in obj.material_slots:
            try:
                slot.link = 'DATA'
            except Exception:
                pass

        mesh_mats = obj.data.materials
        while len(mesh_mats) < len(replacement_slots):
            mesh_mats.append(None)
        while len(mesh_mats) > len(replacement_slots):
            mesh_mats.pop(index=len(mesh_mats) - 1)
        for i, material in enumerate(replacement_slots):
            mesh_mats[i] = material

        # Apply the mapping to the polygons
        if hasattr(obj.data, "polygons"):
            for poly in obj.data.polygons:
                poly.material_index = mapping.get(poly.material_index, 0)

    def _deduplicate_materials(self, obj) -> None:
        for index, material in enumerate(list(obj.data.materials)):
            if not material:
                continue
            existing = self._existing_material(material.name)
            if existing and existing != material:
                obj.data.materials[index] = existing

    def _existing_material(self, material_name: str):
        base_name = self._base_blender_name(material_name)
        material = bpy.data.materials.get(base_name)
        if material:
            return material
        clean = sanitize_name(base_name)
        for candidate in bpy.data.materials:
            if sanitize_name(self._base_blender_name(candidate.name)) == clean:
                return candidate
        return None

    def _purge_unused_duplicate_materials(self, protected_names: list[str]) -> None:
        protected = {sanitize_name(self._base_blender_name(name)) for name in protected_names}
        for material in list(bpy.data.materials):
            if material.users != 0:
                continue
            base = sanitize_name(self._base_blender_name(material.name))
            if base in protected or self._is_numbered_duplicate(material.name):
                bpy.data.materials.remove(material)

    def _base_blender_name(self, name: str) -> str:
        if self._is_numbered_duplicate(name):
            return name[:-4]
        return name

    def _is_numbered_duplicate(self, name: str) -> bool:
        return len(name) > 4 and name[-4] == "." and name[-3:].isdigit()

    def _match_key(self, object_name: str, records: dict[str, MeshRecord]) -> str | None:
        clean = sanitize_name(object_name)
        if clean in records:
            return clean
        base = object_name.split(".")[0]
        clean_base = sanitize_name(base)
        if clean_base in records:
            return clean_base
        for key in records:
            if clean.startswith(key):
                return key
        return next(iter(records)) if len(records) == 1 else None

    def _sharp_edges(self, obj) -> list[list[int]]:
        sharp_attribute = obj.data.attributes.get("sharp_edge") if hasattr(obj.data, "attributes") else None
        sharp_edges = []
        for edge in obj.data.edges:
            is_sharp = False
            if hasattr(edge, "use_edge_sharp"):
                is_sharp = bool(edge.use_edge_sharp)
            elif sharp_attribute and edge.index < len(sharp_attribute.data):
                is_sharp = bool(sharp_attribute.data[edge.index].value)
            if is_sharp:
                sharp_edges.append([int(edge.vertices[0]), int(edge.vertices[1])])
        return sharp_edges

    def _apply_sharp_edges(self, obj, sharp_edges: list[list[int]]) -> None:
        if obj.type != "MESH":
            return

        sharp_attribute = None
        if hasattr(obj.data, "attributes"):
            sharp_attribute = obj.data.attributes.get("sharp_edge")
            if sharp_attribute is None:
                try:
                    sharp_attribute = obj.data.attributes.new("sharp_edge", "BOOLEAN", "EDGE")
                except Exception:
                    pass
        edge_keys = {tuple(sorted(edge)) for edge in sharp_edges or [] if len(edge) == 2}
        for edge in obj.data.edges:
            is_sharp = tuple(sorted(edge.vertices)) in edge_keys
            if hasattr(edge, "use_edge_sharp"):
                edge.use_edge_sharp = is_sharp
            if sharp_attribute and edge.index < len(sharp_attribute.data):
                sharp_attribute.data[edge.index].value = is_sharp
        
        # Enable Auto Smooth on older Blender versions (<4.1) or add Smooth by Angle modifier on newer versions (>=4.1)
        if hasattr(obj.data, "use_auto_smooth"):
            try:
                obj.data.use_auto_smooth = True
                obj.data.auto_smooth_angle = 3.14159
            except Exception:
                pass
        else:
            if sharp_edges:
                try:
                    has_mod = any(m.type == 'SMOOTH_BY_ANGLE' for m in obj.modifiers)
                    if not has_mod:
                        mod = obj.modifiers.new(name="Smooth by Angle", type='SMOOTH_BY_ANGLE')
                        mod.angle = 3.14159
                except Exception:
                    pass

        obj.data.update()

    def _seam_edges(self, obj) -> list[list[int]]:
        seam_attribute = obj.data.attributes.get("seam") if hasattr(obj.data, "attributes") else None
        seam_edges = []
        for edge in obj.data.edges:
            is_seam = False
            if hasattr(edge, "use_seam"):
                is_seam = bool(edge.use_seam)
            elif seam_attribute and edge.index < len(seam_attribute.data):
                is_seam = bool(seam_attribute.data[edge.index].value)
            if is_seam:
                seam_edges.append([int(edge.vertices[0]), int(edge.vertices[1])])
        return seam_edges

    def _apply_seam_edges(self, obj, seam_edges: list[list[int]]) -> None:
        if obj.type != "MESH":
            return
        if seam_edges:
            edge_keys = {tuple(sorted(edge)) for edge in seam_edges if len(edge) == 2}
            seam_attribute = None
            if hasattr(obj.data, "attributes"):
                seam_attribute = obj.data.attributes.get("seam")
                if seam_attribute is None:
                    try:
                        seam_attribute = obj.data.attributes.new("seam", "BOOLEAN", "EDGE")
                    except Exception:
                        pass
            for edge in obj.data.edges:
                is_seam = tuple(sorted(edge.vertices)) in edge_keys
                if hasattr(edge, "use_seam"):
                    edge.use_seam = is_seam
                if seam_attribute and edge.index < len(seam_attribute.data):
                    seam_attribute.data[edge.index].value = is_seam
            obj.data.update()
        else:
            self._auto_mark_uv_seams(obj)

    def _auto_mark_uv_seams(self, obj) -> None:
        if obj.type != "MESH" or not obj.data.uv_layers:
            return
        active_uv = obj.data.uv_layers.active
        if not active_uv:
            return
        from collections import defaultdict
        edge_uvs = defaultdict(lambda: defaultdict(list))
        for poly in obj.data.polygons:
            n_loops = len(poly.loop_indices)
            for i in range(n_loops):
                loop_idx = poly.loop_indices[i]
                next_loop_idx = poly.loop_indices[(i + 1) % n_loops]
                loop = obj.data.loops[loop_idx]
                next_loop = obj.data.loops[next_loop_idx]
                edge_idx = loop.edge_index
                v_start = loop.vertex_index
                v_end = next_loop.vertex_index
                uv_start = active_uv.data[loop_idx].uv
                uv_end = active_uv.data[next_loop_idx].uv
                edge_uvs[edge_idx][v_start].append((uv_start[0], uv_start[1]))
                edge_uvs[edge_idx][v_end].append((uv_end[0], uv_end[1]))
        seam_attribute = None
        if hasattr(obj.data, "attributes"):
            seam_attribute = obj.data.attributes.get("seam")
            if seam_attribute is None:
                try:
                    seam_attribute = obj.data.attributes.new("seam", "BOOLEAN", "EDGE")
                except Exception:
                    pass
        for edge in obj.data.edges:
            is_seam = False
            for v_idx in edge.vertices:
                coords = edge_uvs[edge.index].get(v_idx, [])
                if len(coords) > 1:
                    first = coords[0]
                    for c in coords[1:]:
                        if abs(c[0] - first[0]) > 1e-5 or abs(c[1] - first[1]) > 1e-5:
                            is_seam = True
                            break
                if is_seam:
                    break
            if hasattr(edge, "use_seam"):
                edge.use_seam = is_seam
            if seam_attribute and edge.index < len(seam_attribute.data):
                seam_attribute.data[edge.index].value = is_seam
        obj.data.update()

    def _reset_delta_transforms(self, obj) -> None:
        from mathutils import Vector
        obj.delta_location = Vector((0.0, 0.0, 0.0))
        if hasattr(obj, "delta_rotation_euler"):
            obj.delta_rotation_euler = Vector((0.0, 0.0, 0.0))
        if hasattr(obj, "delta_rotation_quaternion"):
            from mathutils import Quaternion
            obj.delta_rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
        if hasattr(obj, "delta_rotation_axis_angle"):
            obj.delta_rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        obj.delta_scale = Vector((1.0, 1.0, 1.0))

    def _apply_transforms_to_deltas_python(self, obj) -> None:
        from mathutils import Vector, Quaternion
        obj.delta_location = obj.location.copy()
        obj.location = Vector((0.0, 0.0, 0.0))
        
        obj.delta_scale = obj.scale.copy()
        obj.scale = Vector((1.0, 1.0, 1.0))
        
        if obj.rotation_mode == 'QUATERNION':
            obj.delta_rotation_quaternion = obj.rotation_quaternion.copy()
            obj.rotation_quaternion = Quaternion((1.0, 0.0, 0.0, 0.0))
        elif obj.rotation_mode == 'AXIS_ANGLE':
            obj.delta_rotation_axis_angle = list(obj.rotation_axis_angle)
            obj.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        else:
            obj.delta_rotation_euler = obj.rotation_euler.copy()
            obj.rotation_euler = Vector((0.0, 0.0, 0.0))

    def _set_object_pivot(self, obj, pivot_world: list[float]) -> None:
        if obj.type != "MESH" or not pivot_world or len(pivot_world) != 3:
            return
        from mathutils import Vector
        P = Vector(pivot_world)
        
        # Reset delta transforms to default first, so that we work with clean matrices/transforms
        self._reset_delta_transforms(obj)

        W = obj.matrix_world.copy()
        W_new = W.copy()
        W_new.translation = P
        
        M = W_new.inverted() @ W
        # If translation difference is extremely small, skip to save computation
        if M.translation.length < 1e-6:
            return
            
        # Store world matrices of children to prevent them from moving
        children_matrices = [(child, child.matrix_world.copy()) for child in obj.children]
        
        for vert in obj.data.vertices:
            vert.co = M @ vert.co
        obj.matrix_world = W_new
        obj.data.update()
        
        # Convert all transforms to deltas to keep transforms in 0,0,0
        try:
            self._apply_transforms_to_deltas_python(obj)
        except Exception:
            obj.delta_location = obj.location.copy()
            obj.location = Vector((0.0, 0.0, 0.0))

        # Restore children matrices
        for child, matrix in children_matrices:
            child.matrix_world = matrix

    def _force_material_link_to_data(self, obj) -> None:
        if not hasattr(obj, "material_slots"):
            return
        mats = [slot.material for slot in obj.material_slots]
        for slot in obj.material_slots:
            try:
                slot.link = 'DATA'
            except Exception:
                pass
        if hasattr(obj, "data") and hasattr(obj.data, "materials"):
            mesh_mats = obj.data.materials
            while len(mesh_mats) < len(mats):
                mesh_mats.append(None)
            while len(mesh_mats) > len(mats):
                mesh_mats.pop(index=len(mesh_mats) - 1)
            for i, mat in enumerate(mats):
                mesh_mats[i] = mat
