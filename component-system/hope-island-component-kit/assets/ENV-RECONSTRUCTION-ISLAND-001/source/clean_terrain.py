from pathlib import Path
import os

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "reconstruction-terrain-hunyuan-textured-v01.glb"
OUTPUT = ROOT / "export" / "reconstruction-terrain-hunyuan-textured-clean-v01.glb"
CLEAN = os.environ.get("RECONSTRUCTION_CLEAN", "0") == "1"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
for mesh in list(meshes):
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    mesh.select_set(False)

parts = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
largest_faces = max(len(obj.data.polygons) for obj in parts)
removed = []
for index, obj in enumerate(sorted(parts, key=lambda item: len(item.data.polygons), reverse=True)):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    mins = Vector(tuple(min(point[axis] for point in corners) for axis in range(3)))
    maxs = Vector(tuple(max(point[axis] for point in corners) for axis in range(3)))
    extents = maxs - mins
    faces = len(obj.data.polygons)
    slender = min(extents.x, extents.y) < max(extents.x, extents.y) * .12
    tiny = faces < largest_faces * .012
    long_sliver = slender and tiny and max(extents.x, extents.y) > .35
    center = (mins + maxs) / 2
    low_candidate = center.z < -.18 and max(extents.x, extents.y) > .20 and faces < 8000
    front_right_candidate = center.x > .55 and center.y < -.55 and max(extents.x, extents.y) > .08
    detached_front_right_artifact = center.x > .70 and center.y < -.55 and extents.z < .015
    if index < 12 or long_sliver or low_candidate or front_right_candidate:
        print(f"part={index} name={obj.name} faces={faces} center={tuple(round(value, 5) for value in center)} extents={tuple(round(value, 5) for value in extents)} long_sliver={long_sliver} low_candidate={low_candidate} front_right={front_right_candidate}")
    if CLEAN and detached_front_right_artifact:
        removed.append(obj.name)
        bpy.data.objects.remove(obj, do_unlink=True)

if CLEAN:
    remaining = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in remaining:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = max(remaining, key=lambda item: len(item.data.polygons))
    bpy.ops.object.join()
    bpy.context.object.name = "reconstruction-terrain-clean"
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLB", export_yup=True)
    print(f"removed={removed}")
    print(f"output={OUTPUT}")
