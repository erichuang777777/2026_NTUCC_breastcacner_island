"""Detach the family-medicine island terrain and holistic-care garden."""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = PROJECT / "webgl-prototype/assets/env-taiwan-archipelago-001-macro.glb"
OUTPUT = HERE.parent / "export/family-medicine-landscape-detached-v01.glb"
WEB_OUTPUT = PROJECT / "webgl-prototype/assets/family-medicine-landscape-detached-v01.glb"
ORIGIN = (11.0, -8.0, 0.0)


def is_landscape_mesh(obj):
    name = obj.name.lower()
    return obj.type == "MESH" and (
        "family-medicine-terrain-hi" in name or "family-medicine-prop-hi" in name
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
        modifier = obj.modifiers.new("family-medicine-soft-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if is_landscape_mesh(obj)]
if not meshes:
    raise RuntimeError("No family-medicine landscape meshes found in macro world")

world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
translation = Matrix.Translation((-ORIGIN[0], -ORIGIN[1], -ORIGIN[2]))
bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    if obj not in meshes:
        obj.select_set(True)
bpy.ops.object.delete(use_global=False)

root = bpy.data.objects.new("ENV-FAMILY-MEDICINE-LANDSCAPE-001-DETACHED", None)
bpy.context.collection.objects.link(root)
for obj in meshes:
    obj.parent = None
    obj.matrix_world = translation @ world_matrices[obj]
    obj.parent = root

rock_dark = material("family-medicine-v01-rock-dark", (0.25, 0.24, 0.20), 0.95)
rock_moss = material("family-medicine-v01-rock-moss", (0.34, 0.34, 0.22), 0.92)
fence_wood = material("family-medicine-v01-fence-wood", (0.34, 0.23, 0.14), 0.84)

for index in range(40):
    angle = index / 40 * math.tau + 0.08
    if any(abs((angle - opening + math.pi) % math.tau - math.pi) < 0.17 for opening in (-math.pi / 2, math.pi / 2, math.pi)):
        continue
    radius = 2.78 + 0.12 * math.sin(index * 1.53)
    scale = 0.11 + (index % 5) * 0.015
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0, location=(math.cos(angle) * radius, math.sin(angle) * radius, -0.23 + (index % 3) * 0.023))
    rock = bpy.context.object
    rock.scale = (scale * 1.38, scale, scale * 0.80)
    rock.rotation_euler[2] = angle * 0.71
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(rock, f"family-medicine-v01-shore-rock-{index:02d}", rock_dark if index % 2 else rock_moss, root)

segments = 42
for index in range(segments):
    angle = index / segments * math.tau
    next_angle = (index + 1) / segments * math.tau
    if any(abs((angle - opening + math.pi) % math.tau - math.pi) < 0.22 for opening in (-math.pi / 2, math.pi / 2, math.pi)):
        continue
    radius = 2.57
    x, y = math.cos(angle) * radius, math.sin(angle) * radius
    nx, ny = math.cos(next_angle) * radius, math.sin(next_angle) * radius
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.034, depth=0.46, location=(x, y, 1.25))
    finish(bpy.context.object, f"family-medicine-v01-fence-post-{index:02d}", fence_wood, root)
    length = math.hypot(nx - x, ny - y)
    heading = math.atan2(ny - y, nx - x)
    for rail_index, height in enumerate((1.18, 1.37)):
        bpy.ops.mesh.primitive_cube_add(location=((x + nx) / 2, (y + ny) / 2, height))
        rail = bpy.context.object
        rail.scale = (length / 2, 0.024, 0.024)
        rail.rotation_euler[2] = heading
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        finish(rail, f"family-medicine-v01-fence-rail-{index:02d}-{rail_index}", fence_wood, root, bevel=0.010)

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
