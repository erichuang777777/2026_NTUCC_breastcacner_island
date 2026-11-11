"""Detach the imaging-island terrain and garden from the legacy macro world.

The diagnostic pavilion stays a separate editable building component.  This
script preserves the authored macro placement, recentres the terrain and
garden on the imaging-island anchor, and adds a restrained diagnostic-arrival
detail layer without touching the cross-island bridge network.
"""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = PROJECT / "webgl-prototype/assets/env-taiwan-archipelago-001-macro.glb"
OUTPUT = HERE.parent / "export/imaging-island-landscape-v01.glb"
WEB_OUTPUT = PROJECT / "webgl-prototype/assets/imaging-island-landscape-v01.glb"
ORIGIN = (5.0, 9.0, 0.0)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def is_landscape_mesh(obj):
    name = obj.name.lower()
    return obj.type == "MESH" and (
        "imaging-terrain-hi" in name or "imaging-prop-hi" in name
    )


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


def finish(obj, name, mat, root, bevel=0.0):
    obj.name = name
    obj.data.materials.append(mat)
    obj.parent = root
    if bevel:
        modifier = obj.modifiers.new("imaging-soft-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


clear_scene()
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if is_landscape_mesh(obj)]
if not meshes:
    raise RuntimeError("No imaging-island landscape meshes found in the macro world")

world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
translation = Matrix.Translation((-ORIGIN[0], -ORIGIN[1], -ORIGIN[2]))

bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    if obj not in meshes:
        obj.select_set(True)
bpy.ops.object.delete(use_global=False)

root = bpy.data.objects.new("ENV-IMAGING-ISLAND-LANDSCAPE-001-DETACHED", None)
bpy.context.collection.objects.link(root)
for obj in meshes:
    obj.parent = None
    obj.matrix_world = translation @ world_matrices[obj]
    obj.parent = root

# Diagnostic arrival language: concentric scanner rings and low illuminated
# markers echo the pavilion's MRI gantry while keeping the walking route clear.
stone_dark = material("imaging-v01-arrival-stone-dark", (0.30, 0.35, 0.35), 0.78)
stone_light = material("imaging-v01-arrival-stone-light", (0.70, 0.67, 0.59), 0.76)
metal = material("imaging-v01-marker-metal", (0.13, 0.19, 0.20), 0.34, 0.58)
glow = material(
    "imaging-v01-marker-glow",
    (0.75, 0.90, 0.88),
    0.20,
    emission=((0.25, 0.78, 0.72), 2.2),
)
rock_dark = material("imaging-v01-shore-rock-dark", (0.26, 0.24, 0.23), 0.94)
rock_mid = material("imaging-v01-shore-rock-mid", (0.40, 0.35, 0.31), 0.91)
rock_warm = material("imaging-v01-shore-rock-warm", (0.52, 0.43, 0.36), 0.88)
soil = material("imaging-v01-flower-soil", (0.24, 0.17, 0.12), 0.96)
leaf_dark = material("imaging-v01-leaf-dark", (0.19, 0.34, 0.17), 0.92)
leaf_light = material("imaging-v01-leaf-light", (0.42, 0.56, 0.27), 0.88)
flower_rose = material("imaging-v01-flower-rose", (0.86, 0.32, 0.46), 0.76)
flower_pale = material("imaging-v01-flower-pale", (0.98, 0.72, 0.76), 0.72)
flower_white = material("imaging-v01-flower-white", (0.96, 0.91, 0.81), 0.70)
fence_wood = material("imaging-v01-fence-wood", (0.38, 0.22, 0.13), 0.82)

# Layered faceted rocks restore the cinematic shoreline silhouette.  Their
# alternating height and radius avoid the uniform scalloped edge of the old
# low-detail island while leaving all bridge landings open.
for index in range(56):
    angle = index / 56 * math.tau + 0.08
    if abs(math.sin(angle)) > 0.92 and math.cos(angle) < 0.15:
        continue
    radius = 2.78 + 0.14 * math.sin(index * 1.71) + 0.06 * math.cos(index * 0.63)
    scale = 0.12 + (index % 5) * 0.016
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=1.0,
        location=(math.cos(angle) * radius, math.sin(angle) * radius, -0.23 + (index % 4) * 0.024),
    )
    rock = bpy.context.object
    rock.scale = (scale * 1.35, scale, scale * (0.76 + (index % 3) * 0.08))
    rock.rotation_euler[2] = angle * 0.82
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(
        rock,
        f"imaging-v01-layered-shore-rock-{index:02d}",
        (rock_dark, rock_mid, rock_warm)[index % 3],
        root,
    )

# Three elliptical beds and their dense flower clusters follow the film still:
# a central bed framed by two asymmetrical side beds.
flower_beds = ((0.0, -1.02, 0.82, 0.38), (-1.84, -0.46, 0.62, 0.30), (1.88, -0.34, 0.66, 0.31))
for bed_index, (cx, cy, rx, ry) in enumerate(flower_beds):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=0.12, location=(cx, cy, 1.08))
    bed = bpy.context.object
    bed.scale = (rx, ry, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(bed, f"imaging-v01-cinematic-flower-bed-{bed_index}", soil, root, bevel=0.035)
    for flower_index in range(28):
        angle = flower_index / 28 * math.tau + bed_index * 0.47
        ring = 0.34 + (flower_index % 4) * 0.15
        x = cx + math.cos(angle) * rx * ring
        y = cy + math.sin(angle) * ry * ring
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.085 + (flower_index % 3) * 0.012, location=(x, y, 1.20 + (flower_index % 4) * 0.018))
        finish(
            bpy.context.object,
            f"imaging-v01-cinematic-flower-{bed_index}-{flower_index:02d}",
            (flower_rose, flower_pale, flower_white)[flower_index % 3],
            root,
        )
    for shrub_index in range(9):
        angle = shrub_index / 9 * math.tau
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=1,
            radius=0.14 + (shrub_index % 2) * 0.025,
            location=(cx + math.cos(angle) * rx * 0.62, cy + math.sin(angle) * ry * 0.62, 1.17),
        )
        shrub = bpy.context.object
        shrub.scale.z = 0.74
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        finish(shrub, f"imaging-v01-flower-bed-shrub-{bed_index}-{shrub_index}", leaf_dark if shrub_index % 2 else leaf_light, root)

# Low timber fencing defines the garden perimeter without creating new avatar
# colliders.  Two intentional openings remain at the front and bridge sides.
fence_angles = [(-2.88 + index * 0.18) for index in range(10)] + [(-0.26 + index * 0.18) for index in range(18)]
for index, angle in enumerate(fence_angles):
    radius = 2.64
    x, y = math.cos(angle) * radius, math.sin(angle) * radius
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.035, depth=0.48, location=(x, y, 1.28))
    finish(bpy.context.object, f"imaging-v01-garden-fence-post-{index:02d}", fence_wood, root)
    if index in (9, 27):
        continue
    next_angle = angle + 0.18
    nx, ny = math.cos(next_angle) * radius, math.sin(next_angle) * radius
    length = math.hypot(nx - x, ny - y)
    for rail_height in (1.20, 1.39):
        bpy.ops.mesh.primitive_cube_add(location=((x + nx) * 0.5, (y + ny) * 0.5, rail_height))
        rail = bpy.context.object
        rail.scale = (length * 0.5, 0.025, 0.025)
        rail.rotation_euler[2] = math.atan2(ny - y, nx - x)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        finish(rail, f"imaging-v01-garden-fence-rail-{index:02d}-{rail_height}", fence_wood, root, bevel=0.012)

for index in range(5):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.42 + index * 0.19,
        minor_radius=0.026,
        major_segments=64,
        minor_segments=8,
        location=(0.0, -1.82, 1.125 + index * 0.002),
    )
    ring = bpy.context.object
    ring.scale.y = 0.58
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(
        ring,
        f"imaging-v01-scanner-arrival-ring-{index:02d}",
        stone_light if index % 2 else stone_dark,
        root,
    )

for index, (x, y) in enumerate(((-1.42, -1.62), (1.42, -1.62), (-1.78, -2.20), (1.78, -2.20))):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.045, depth=0.48, location=(x, y, 1.35))
    finish(bpy.context.object, f"imaging-v01-route-marker-{index}", metal, root)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.075, location=(x, y, 1.61))
    finish(bpy.context.object, f"imaging-v01-route-marker-glow-{index}", glow, root)

# Directional inlays point from the bridge landing to the diagnostic entrance.
for index in range(7):
    y = -2.72 + index * 0.25
    bpy.ops.mesh.primitive_cube_add(location=(0.0, y, 1.135))
    inset = bpy.context.object
    inset.scale = (0.12 + index * 0.006, 0.045, 0.012)
    inset.rotation_euler[2] = math.radians(2.5 * math.sin(index))
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(inset, f"imaging-v01-diagnostic-route-inlay-{index:02d}", stone_light, root, bevel=0.018)

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
