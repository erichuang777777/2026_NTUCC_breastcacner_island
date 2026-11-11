"""Detach rehabilitation terrain, hydrotherapy and outdoor training landscape."""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = PROJECT / "webgl-prototype/assets/env-taiwan-archipelago-001-macro.glb"
OUTPUT = HERE.parent / "export/rehabilitation-landscape-detached-v01.glb"
WEB_OUTPUT = PROJECT / "webgl-prototype/assets/rehabilitation-landscape-detached-v01.glb"
ORIGIN = (-5.0, -17.0, 0.0)
BRIDGE_OPENINGS = (0.0, math.atan2(9.0, 5.0), math.atan2(9.0, -6.0))


def is_landscape_mesh(obj):
    name = obj.name.lower()
    return obj.type == "MESH" and (
        "rehabilitation-terrain-hi" in name or "rehabilitation-prop-hi" in name
    )


def material(name, color, roughness=0.82):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = roughness
    return mat


def finish(obj, name, mat, root, bevel=0.0):
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = root
    if bevel:
        modifier = obj.modifiers.new("rehabilitation-soft-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


def near_opening(angle, width):
    return any(abs((angle - opening + math.pi) % math.tau - math.pi) < width for opening in BRIDGE_OPENINGS)


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if is_landscape_mesh(obj)]
if not meshes:
    raise RuntimeError("No rehabilitation landscape meshes found in macro world")

world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
translation = Matrix.Translation((-ORIGIN[0], -ORIGIN[1], -ORIGIN[2]))
bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    if obj not in meshes:
        obj.select_set(True)
bpy.ops.object.delete(use_global=False)

root = bpy.data.objects.new("ENV-REHABILITATION-LANDSCAPE-001-DETACHED", None)
bpy.context.collection.objects.link(root)
for obj in meshes:
    obj.parent = None
    obj.matrix_world = translation @ world_matrices[obj]
    obj.parent = root

rock_dark = material("rehabilitation-v01-rock-dark", (0.24, 0.25, 0.24), 0.95)
rock_blue = material("rehabilitation-v01-rock-blue", (0.27, 0.34, 0.35), 0.91)
fence_wood = material("rehabilitation-v01-fence-wood", (0.32, 0.23, 0.16), 0.84)

for index in range(42):
    angle = index / 42 * math.tau + 0.06
    if near_opening(angle, 0.18):
        continue
    radius = 2.80 + 0.12 * math.sin(index * 1.47)
    scale = 0.11 + (index % 5) * 0.015
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(math.cos(angle) * radius, math.sin(angle) * radius, -0.23 + (index % 3) * 0.023))
    rock = bpy.context.object
    rock.scale = (scale * 1.40, scale, scale * 0.78)
    rock.rotation_euler[2] = angle * 0.73
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(rock, f"rehabilitation-v01-shore-rock-{index:02d}", rock_dark if index % 2 else rock_blue, root)

segments = 44
for index in range(segments):
    angle = index / segments * math.tau
    next_angle = (index + 1) / segments * math.tau
    if near_opening(angle, 0.24):
        continue
    radius = 2.58
    x, y = math.cos(angle) * radius, math.sin(angle) * radius
    nx, ny = math.cos(next_angle) * radius, math.sin(next_angle) * radius
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.034, depth=0.46, location=(x, y, 1.25))
    finish(bpy.context.object, f"rehabilitation-v01-fence-post-{index:02d}", fence_wood, root)
    length = math.hypot(nx - x, ny - y)
    heading = math.atan2(ny - y, nx - x)
    for rail_index, height in enumerate((1.18, 1.37)):
        bpy.ops.mesh.primitive_cube_add(location=((x + nx) / 2, (y + ny) / 2, height))
        rail = bpy.context.object
        rail.scale = (length / 2, 0.024, 0.024)
        rail.rotation_euler[2] = heading
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        finish(rail, f"rehabilitation-v01-fence-rail-{index:02d}-{rail_index}", fence_wood, root, bevel=0.010)

bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for obj in root.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root
for target in (OUTPUT, WEB_OUTPUT):
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(target), export_format="GLB", use_selection=True, export_apply=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6, export_image_format="WEBP")

export_meshes = [obj for obj in root.children_recursive if obj.type == "MESH"]
for obj in export_meshes:
    obj.data.calc_loop_triangles()
print(f"Exported {len(export_meshes)} meshes / {sum(len(obj.data.loop_triangles) for obj in export_meshes)} triangles")
