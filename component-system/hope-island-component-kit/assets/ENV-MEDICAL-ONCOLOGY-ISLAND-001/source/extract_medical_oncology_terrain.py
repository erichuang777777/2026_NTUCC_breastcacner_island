"""Detach the medical-oncology island terrain from the legacy macro world.

The infusion clinic and healing-garden props remain separate GLBs.  This
component contains only the island shell, circulation base, dock and a modest
cinematic shoreline refinement, centred on the medical-oncology world anchor.
"""

from pathlib import Path
import math

import bpy
from mathutils import Matrix


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
SOURCE = PROJECT / "webgl-prototype/assets/env-taiwan-archipelago-001-macro.glb"
OUTPUT = HERE.parent / "export/medical-oncology-terrain-detached-v01.glb"
WEB_OUTPUT = PROJECT / "webgl-prototype/assets/medical-oncology-terrain-detached-v01.glb"
ORIGIN = (-11.0, 1.0, 0.0)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def is_terrain_mesh(obj):
    return obj.type == "MESH" and "medical-oncology-terrain-hi" in obj.name.lower()


def material(name, color, roughness=0.9):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    if shader:
        shader.inputs["Base Color"].default_value = (*color, 1.0)
        shader.inputs["Roughness"].default_value = roughness
    return mat


clear_scene()
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if is_terrain_mesh(obj)]
if not meshes:
    raise RuntimeError("No medical-oncology terrain meshes found in the macro world")

world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
translation = Matrix.Translation((-ORIGIN[0], -ORIGIN[1], -ORIGIN[2]))

bpy.ops.object.select_all(action="DESELECT")
for obj in bpy.context.scene.objects:
    if obj not in meshes:
        obj.select_set(True)
bpy.ops.object.delete(use_global=False)

root = bpy.data.objects.new("ENV-MEDICAL-ONCOLOGY-TERRAIN-001-DETACHED", None)
bpy.context.collection.objects.link(root)
for obj in meshes:
    obj.parent = None
    obj.matrix_world = translation @ world_matrices[obj]
    obj.parent = root

# Small embedded rock facets strengthen the poster silhouette without creating
# the oversized boulder necklace corrected during the imaging-island pass.
rock_dark = material("medonc-terrain-v01-rock-dark", (0.26, 0.23, 0.22), 0.95)
rock_mid = material("medonc-terrain-v01-rock-mid", (0.40, 0.34, 0.30), 0.92)
rock_warm = material("medonc-terrain-v01-rock-warm", (0.52, 0.42, 0.34), 0.89)

for index in range(42):
    angle = index / 42 * math.tau + 0.11
    # Leave broad openings for the three bridge/dock approaches.
    if any(abs((angle - opening + math.pi) % math.tau - math.pi) < 0.16 for opening in (-math.pi / 2, 0.0, math.pi)):
        continue
    radius = 2.79 + 0.12 * math.sin(index * 1.63)
    scale = 0.115 + (index % 4) * 0.018
    bpy.ops.mesh.primitive_ico_sphere_add(
        subdivisions=1,
        radius=1.0,
        location=(math.cos(angle) * radius, math.sin(angle) * radius, -0.24 + (index % 3) * 0.026),
    )
    rock = bpy.context.object
    rock.name = f"medonc-terrain-v01-shore-rock-{index:02d}"
    rock.scale = (scale * 1.34, scale, scale * 0.78)
    rock.rotation_euler[2] = angle * 0.74
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    rock.data.materials.append((rock_dark, rock_mid, rock_warm)[index % 3])
    rock.parent = root

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
