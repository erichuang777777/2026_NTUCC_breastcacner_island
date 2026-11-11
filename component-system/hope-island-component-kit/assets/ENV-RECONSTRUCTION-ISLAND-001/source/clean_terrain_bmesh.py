from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "reconstruction-terrain-hunyuan-textured-v01.glb"
OUTPUT = ROOT / "export" / "reconstruction-terrain-hunyuan-textured-clean-v02.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(mesh_objects) != 1:
    raise RuntimeError(f"Expected one source mesh, found {len(mesh_objects)}")
obj = mesh_objects[0]
bm = bmesh.new()
bm.from_mesh(obj.data)
bm.verts.ensure_lookup_table()

unvisited = set(bm.verts)
delete_verts = set()
removed = []
while unvisited:
    seed = unvisited.pop()
    component = [seed]
    stack = [seed]
    while stack:
        current = stack.pop()
        for edge in current.link_edges:
            other = edge.other_vert(current)
            if other in unvisited:
                unvisited.remove(other)
                component.append(other)
                stack.append(other)
    world_points = [obj.matrix_world @ vertex.co for vertex in component]
    min_x = min(point.x for point in world_points)
    max_x = max(point.x for point in world_points)
    min_y = min(point.y for point in world_points)
    max_y = max(point.y for point in world_points)
    min_z = min(point.z for point in world_points)
    max_z = max(point.z for point in world_points)
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    extent_z = max_z - min_z
    if center_x > .70 and center_y < -.55 and extent_z < .015:
        delete_verts.update(component)
        removed.append((len(component), round(center_x, 5), round(center_y, 5), round(extent_z, 5)))

bmesh.ops.delete(bm, geom=list(delete_verts), context="VERTS")
bm.to_mesh(obj.data)
bm.free()
obj.data.update()
obj.name = "reconstruction-terrain-clean"
bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLB", export_yup=True)
print(f"removed_components={removed}")
print(f"removed_vertices={len(delete_verts)}")
print(f"output={OUTPUT}")
