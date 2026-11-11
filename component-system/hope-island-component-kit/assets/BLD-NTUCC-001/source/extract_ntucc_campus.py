"""Detach and refine the NTU Cancer Center campus landscape.

The hospital building remains a separate editable GLB.  This script extracts
the campus plaza layer from the legacy macro world, centres it on the NTUCC
anchor, and adds the concentric arrival-plaza pattern visible in aerial photos.
"""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = PROJECT / "webgl-prototype/assets/env-taiwan-archipelago-001-macro.glb"
OUTPUT = HERE.parent / "export/ntucc-campus-landscape-v01.glb"
WEB_OUTPUT = PROJECT / "webgl-prototype/assets/ntucc-campus-landscape-v01.glb"
ORIGIN = (-15.0, 10.0, 0.0)

PREFIXES = (
    "ntucc-campus-",
    "ntucc-entry-",
    "ntucc-dropoff-",
    "ntucc-healing-",
    "ntucc-garden-",
    "ntucc-transit-",
    "ntucc-info-",
    "ntucc-bench-",
    "ntucc-wayfinding-",
    "ntucc-lamp-",
    "ntucc-flower-",
)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def is_campus_mesh(obj):
    return obj.type == "MESH" and obj.name.lower().startswith(PREFIXES)


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
        modifier = obj.modifiers.new("campus-soft-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return obj


clear_scene()
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if is_campus_mesh(obj)]
if not meshes:
    raise RuntimeError("No NTUCC campus meshes found in the macro world")

world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
translation = Matrix.Translation((-ORIGIN[0], -ORIGIN[1], -ORIGIN[2]))

bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    if obj not in meshes:
        obj.select_set(True)
bpy.ops.object.delete(use_global=False)

root = bpy.data.objects.new("ENV-NTUCC-CAMPUS-LANDSCAPE-001-DETACHED", None)
bpy.context.collection.objects.link(root)
for obj in meshes:
    obj.parent = None
    obj.matrix_world = translation @ world_matrices[obj]
    obj.parent = root

plaza_dark = material("ntucc-v01-plaza-dark", (0.25, 0.27, 0.27), 0.82)
plaza_light = material("ntucc-v01-plaza-light", (0.70, 0.67, 0.62), 0.78)
road_marking = material("ntucc-v01-road-marking", (0.94, 0.90, 0.78), 0.64)
metal = material("ntucc-v01-bollard-metal", (0.18, 0.22, 0.23), 0.38, 0.52)
glow = material("ntucc-v01-bollard-glow", (1.0, 0.72, 0.34), 0.22, emission=((1.0, 0.38, 0.08), 2.0))

# The aerial reference has a fingerprint-like concentric arrival plaza.
for index in range(9):
    radius = 0.48 + index * 0.205
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,
        minor_radius=0.028,
        major_segments=72,
        minor_segments=8,
        location=(0.0, -2.18, 1.175 + index * 0.001),
    )
    ring = bpy.context.object
    ring.scale.y = 0.66
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(ring, f"ntucc-v01-arrival-ring-{index:02d}", plaza_dark if index % 2 else plaza_light, root)

# Elliptical lane markings make the drop-off route legible from the film camera.
for index in range(20):
    angle = index / 20 * math.tau
    x = math.cos(angle) * 1.72
    y = -2.68 + math.sin(angle) * 1.04
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 1.158), rotation=(0.0, 0.0, angle + math.pi / 2))
    dash = bpy.context.object
    dash.scale = (0.15, 0.027, 0.012)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(dash, f"ntucc-v01-dropoff-dash-{index:02d}", road_marking, root, bevel=0.012)

# Low illuminated bollards define a safe pedestrian edge without blocking it.
for index, (x, y) in enumerate(((-1.72, -1.52), (1.72, -1.52), (-2.24, -2.44), (2.24, -2.44), (-1.84, -3.38), (1.84, -3.38))):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.055, depth=0.38, location=(x, y, 1.30))
    finish(bpy.context.object, f"ntucc-v01-bollard-{index}", metal, root)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.075, location=(x, y, 1.51))
    finish(bpy.context.object, f"ntucc-v01-bollard-light-{index}", glow, root)

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

print(f"Exported {len(root.children_recursive)} NTUCC campus objects to {OUTPUT} and {WEB_OUTPUT}")
