"""Extract the Hope Lighthouse island from the legacy macro world.

The source macro remains the authoritative spatial layout.  This script turns
the lighthouse tower and its landscape into an origin-centred component so it
can be refined and replaced without rebuilding the whole archipelago.
"""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = PROJECT / "webgl-prototype/assets/env-taiwan-archipelago-001-macro.glb"
OUTPUT = HERE.parent / "export/hope-lighthouse-island-v02.glb"
WEB_OUTPUT = PROJECT / "webgl-prototype/assets/hope-lighthouse-island-v02.glb"
ORIGIN = (14.0, -17.0, 0.0)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def is_lighthouse_mesh(obj):
    name = obj.name.lower()
    return obj.type == "MESH" and (
        name.startswith("lighthouse-") or "lighthouse-hi" in name
    )


clear_scene()
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

meshes = [obj for obj in bpy.context.scene.objects if is_lighthouse_mesh(obj)]
if not meshes:
    raise RuntimeError("No lighthouse meshes found in the macro world")

world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
translation = Matrix.Translation((-ORIGIN[0], -ORIGIN[1], -ORIGIN[2]))

# Remove everything outside the component, keeping the imported mesh datablocks.
bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    if obj not in meshes:
        obj.select_set(True)
bpy.ops.object.delete(use_global=False)

root = bpy.data.objects.new("BLD-HOPE-LIGHTHOUSE-ISLAND-001", None)
bpy.context.collection.objects.link(root)

for obj in meshes:
    obj.parent = None
    obj.matrix_world = translation @ world_matrices[obj]
    obj.parent = root
    obj.select_set(True)

root.select_set(True)
bpy.context.view_layer.objects.active = root


def material(name, color, roughness=0.72, metallic=0.0, emission=None):
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


def finish_object(obj, name, mat, parent=root, bevel=0.0):
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = parent
    if bevel:
        modifier = obj.modifiers.new("cinematic-soft-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


def cube(name, location, scale, mat, bevel=0.0, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_object(obj, name, mat, bevel=bevel)


def cylinder(name, location, radius, depth, mat, vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    return finish_object(bpy.context.object, name, mat)


def ico(name, location, scale, mat, subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1.0, location=location)
    obj = bpy.context.object
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_object(obj, name, mat)


# Poster-guided cinematic detail layer.  These are deliberately separate and
# named so future passes can replace rocks, planting, cottages or lamps alone.
rock_dark = material("lighthouse-v02-rock-dark", (0.30, 0.27, 0.28), 0.94)
rock_mid = material("lighthouse-v02-rock-mid", (0.43, 0.38, 0.37), 0.90)
rock_warm = material("lighthouse-v02-rock-warm", (0.55, 0.45, 0.40), 0.88)
path_stone = material("lighthouse-v02-path-stone", (0.73, 0.62, 0.51), 0.82)
trunk_mat = material("lighthouse-v02-tree-trunk", (0.33, 0.20, 0.14), 0.92)
leaf_green = material("lighthouse-v02-leaf-green", (0.30, 0.42, 0.22), 0.90)
leaf_pink = material("lighthouse-v02-cherry-blossom", (0.90, 0.52, 0.62), 0.78)
leaf_pale = material("lighthouse-v02-cherry-pale", (0.97, 0.72, 0.77), 0.74)
flower_white = material("lighthouse-v02-flower-white", (0.96, 0.90, 0.80), 0.72)
flower_rose = material("lighthouse-v02-flower-rose", (0.86, 0.34, 0.48), 0.72)
flower_gold = material("lighthouse-v02-flower-gold", (0.95, 0.68, 0.24), 0.70)
metal_dark = material("lighthouse-v02-dark-metal", (0.18, 0.20, 0.19), 0.42, 0.48)
roof_mat = material("lighthouse-v02-roof-tile", (0.45, 0.16, 0.15), 0.70)
window_mat = material(
    "lighthouse-v02-window-glow",
    (0.88, 0.52, 0.20),
    0.28,
    emission=((1.0, 0.34, 0.08), 1.8),
)
lamp_glow = material(
    "lighthouse-v02-lamp-glow",
    (1.0, 0.72, 0.34),
    0.20,
    emission=((1.0, 0.32, 0.05), 2.4),
)

# Irregular faceted shoreline gives the island the stepped cinematic silhouette
# visible in the authoritative poster.
for index in range(30):
    angle = index / 30 * math.tau + 0.13
    radius = 3.15 + 0.28 * math.sin(index * 1.83)
    scale = 0.24 + (index % 5) * 0.045
    rock = ico(
        f"lighthouse-v02-shore-rock-{index:02d}",
        (math.cos(angle) * radius, math.sin(angle) * radius - 0.10, 0.08 + (index % 3) * 0.035),
        (scale * 1.25, scale, scale * 0.82),
        (rock_dark, rock_mid, rock_warm)[index % 3],
    )
    rock.rotation_euler[2] = angle * 0.73

# A readable winding stone route joins the lower garden to the lighthouse stair.
for index in range(34):
    t = index / 33
    angle = -2.46 + t * 4.22
    radius = 2.48 - 0.58 * t
    stone = cube(
        f"lighthouse-v02-garden-path-{index:02d}",
        (math.cos(angle) * radius, math.sin(angle) * radius - 0.20, 0.91 + 0.30 * t),
        (0.18, 0.13, 0.035),
        path_stone,
        bevel=0.045,
        rotation=(0.0, 0.0, angle + math.pi / 2),
    )
    stone.scale.x *= 0.86 + (index % 3) * 0.08

# Dense flower beds frame the path without blocking the avatar route.
for index in range(54):
    angle = index / 54 * math.tau + 0.31
    radius = 2.10 + (index % 3) * 0.20
    flower_mat = (flower_white, flower_rose, flower_gold)[index % 3]
    ico(
        f"lighthouse-v02-flower-cluster-{index:02d}",
        (math.cos(angle) * radius, math.sin(angle) * radius - 0.04, 1.03 + (index % 4) * 0.025),
        (0.105, 0.105, 0.075),
        flower_mat,
        subdivisions=1,
    )

# Three cherry trees reproduce the poster's foreground pink canopy rhythm.
for tree_index, (x, y, size) in enumerate(((-2.16, -0.82, 0.72), (2.28, -0.56, 0.64), (-1.76, 1.40, 0.55))):
    cylinder(f"lighthouse-v02-cherry-trunk-{tree_index}", (x, y, 1.34), 0.10 * size, 1.10 * size, trunk_mat, 12)
    for crown_index in range(6):
        crown_angle = crown_index / 6 * math.tau
        crown_mat = leaf_pale if crown_index % 2 else leaf_pink
        ico(
            f"lighthouse-v02-cherry-crown-{tree_index}-{crown_index}",
            (
                x + math.cos(crown_angle) * 0.30 * size,
                y + math.sin(crown_angle) * 0.25 * size,
                1.82 * size + 0.48 + (crown_index % 2) * 0.12,
            ),
            (0.42 * size, 0.37 * size, 0.31 * size),
            crown_mat,
            subdivisions=2,
        )
    ico(f"lighthouse-v02-cherry-core-{tree_index}", (x, y, 1.86 * size + 0.50), (0.45 * size,) * 3, leaf_green, subdivisions=2)

# Cottage silhouettes gain tile ridges, chimneys and warm window mullions.
for side in (-1, 1):
    x = side * 1.92
    y = -0.74
    cube(f"lighthouse-v02-cottage-roof-ridge-{side}", (x, y, 1.70), (0.64, 0.055, 0.055), roof_mat, bevel=0.025)
    cube(f"lighthouse-v02-cottage-chimney-{side}", (x + side * 0.34, y + 0.12, 1.77), (0.09, 0.09, 0.29), rock_warm, bevel=0.018)
    for mullion in (-0.09, 0.09):
        cube(f"lighthouse-v02-window-mullion-{side}-{mullion}", (x + side * 0.26 + mullion, y - 0.445, 1.18), (0.018, 0.018, 0.14), window_mat, bevel=0.006)

# Warm garden lights support both dusk and hope-star night states.
for index, (x, y) in enumerate(((-1.62, -2.10), (1.52, -2.06), (-2.12, 0.54), (2.18, 0.42))):
    cylinder(f"lighthouse-v02-garden-lamp-post-{index}", (x, y, 1.24), 0.035, 0.72, metal_dark, 10)
    ico(f"lighthouse-v02-garden-lamp-glow-{index}", (x, y, 1.62), (0.12, 0.12, 0.15), lamp_glow, subdivisions=2)

# Re-select the complete component because primitive creation changes selection.
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

for obj in meshes:
    obj.data.calc_loop_triangles()
triangles = sum(len(obj.data.loop_triangles) for obj in meshes)
print(
    f"Exported {len(meshes)} meshes / {triangles} triangles to {OUTPUT} and {WEB_OUTPUT}"
)
