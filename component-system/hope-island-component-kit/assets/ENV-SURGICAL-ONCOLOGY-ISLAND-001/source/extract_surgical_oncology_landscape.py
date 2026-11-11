"""Detach and refine the surgical-oncology island landscape.

The surgical centre remains a separate GLB.  Terrain, accessible entry ramps
and garden props are extracted from the legacy macro world, centred on the
island anchor, and augmented with poster-guided planting and perimeter detail.
"""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = PROJECT / "webgl-prototype/assets/env-taiwan-archipelago-001-macro.glb"
OUTPUT = HERE.parent / "export/surgical-oncology-landscape-detached-v01.glb"
WEB_OUTPUT = PROJECT / "webgl-prototype/assets/surgical-oncology-landscape-detached-v01.glb"
ORIGIN = (0.0, 1.0, 0.0)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def is_landscape_mesh(obj):
    name = obj.name.lower()
    return obj.type == "MESH" and any(
        prefix in name
        for prefix in (
            "surgical-oncology-terrain-hi",
            "surgical-access-hi",
            "surgical-prop-hi",
        )
    )


def material(name, color, roughness=0.8, metallic=0.0, emission=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = roughness
        shader.inputs["Metallic"].default_value = metallic
        if emission:
            emission_input = shader.inputs.get("Emission Color") or shader.inputs.get("Emission")
            strength_input = shader.inputs.get("Emission Strength")
            if emission_input:
                emission_input.default_value = (*emission[0], 1.0)
            if strength_input:
                strength_input.default_value = emission[1]
    return mat


def finish(obj, name, mat, root, bevel=0.0):
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = root
    if bevel:
        modifier = obj.modifiers.new("surgical-soft-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


clear_scene()
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if is_landscape_mesh(obj)]
if not meshes:
    raise RuntimeError("No surgical-oncology landscape meshes found in macro world")

world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
translation = Matrix.Translation((-ORIGIN[0], -ORIGIN[1], -ORIGIN[2]))

bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    if obj not in meshes:
        obj.select_set(True)
bpy.ops.object.delete(use_global=False)

root = bpy.data.objects.new("ENV-SURGICAL-ONCOLOGY-LANDSCAPE-001-DETACHED", None)
bpy.context.collection.objects.link(root)
for obj in meshes:
    obj.parent = None
    obj.matrix_world = translation @ world_matrices[obj]
    obj.parent = root

rock_dark = material("surgical-v01-rock-dark", (0.26, 0.23, 0.22), 0.95)
rock_mid = material("surgical-v01-rock-mid", (0.40, 0.34, 0.30), 0.92)
wood = material("surgical-v01-fence-wood", (0.36, 0.20, 0.11), 0.82)
soil = material("surgical-v01-flower-soil", (0.24, 0.16, 0.10), 0.95)
rose = material("surgical-v01-flower-rose", (0.88, 0.34, 0.48), 0.72)
blush = material("surgical-v01-flower-blush", (0.98, 0.68, 0.73), 0.70)
white = material("surgical-v01-flower-white", (0.97, 0.90, 0.80), 0.70)
leaf = material("surgical-v01-flower-leaf", (0.26, 0.44, 0.21), 0.88)

# Embedded shoreline facets, intentionally smaller than the underlying cliff.
for index in range(40):
    angle = index / 40 * math.tau + 0.10
    if any(abs((angle - opening + math.pi) % math.tau - math.pi) < 0.17 for opening in (-math.pi / 2, 0.0, math.pi)):
        continue
    radius = 2.78 + 0.12 * math.sin(index * 1.59)
    scale = 0.115 + (index % 4) * 0.017
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=1.0,
        location=(math.cos(angle) * radius, math.sin(angle) * radius, -0.23 + (index % 3) * 0.025),
    )
    rock = bpy.context.object
    rock.scale = (scale * 1.34, scale, scale * 0.78)
    rock.rotation_euler[2] = angle * 0.76
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(rock, f"surgical-v01-shore-rock-{index:02d}", rock_dark if index % 2 else rock_mid, root)

# The macro-authored garden already contains the central flower roundel.  Keep
# that single layer instead of stacking a second flower mound over it.

# Timber fence segments preserve the three bridge/dock openings.
segments = 42
for index in range(segments):
    angle = index / segments * math.tau
    next_angle = (index + 1) / segments * math.tau
    if any(abs((angle - opening + math.pi) % math.tau - math.pi) < 0.22 for opening in (-math.pi / 2, 0.0, math.pi)):
        continue
    radius = 2.57
    x, y = math.cos(angle) * radius, math.sin(angle) * radius
    nx, ny = math.cos(next_angle) * radius, math.sin(next_angle) * radius
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.034, depth=0.46, location=(x, y, 1.25))
    finish(bpy.context.object, f"surgical-v01-fence-post-{index:02d}", wood, root)
    length = math.hypot(nx - x, ny - y)
    heading = math.atan2(ny - y, nx - x)
    for rail_index, height in enumerate((1.18, 1.37)):
        bpy.ops.mesh.primitive_cube_add(location=((x + nx) / 2, (y + ny) / 2, height))
        rail = bpy.context.object
        rail.scale = (length / 2, 0.024, 0.024)
        rail.rotation_euler[2] = heading
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        finish(rail, f"surgical-v01-fence-rail-{index:02d}-{rail_index}", wood, root, bevel=0.010)

bpy.ops.object.select_all(action="DESELECT")
root.select_set(True)
for obj in root.children_recursive:
    obj.select_set(True)
bpy.context.view_layer.objects.active = root

for target in (OUTPUT, WEB_OUTPUT):
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(target),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_draco_mesh_compression_enable=True,
        export_draco_mesh_compression_level=6,
        export_image_format="WEBP",
    )

export_meshes = [obj for obj in root.children_recursive if obj.type == "MESH"]
for obj in export_meshes:
    obj.data.calc_loop_triangles()
triangles = sum(len(obj.data.loop_triangles) for obj in export_meshes)
print(f"Exported {len(export_meshes)} meshes / {triangles} triangles to {OUTPUT} and {WEB_OUTPUT}")
