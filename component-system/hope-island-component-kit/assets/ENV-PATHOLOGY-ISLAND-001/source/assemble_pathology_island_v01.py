from pathlib import Path
from math import pi

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
TERRAIN = ROOT / "export" / "env-pathology-island-001.glb"
BUILDING = ROOT / "export" / "pathology-center-blender-v05.glb"
OUTPUT = ROOT / "export" / "pathology-island-assembled-v01.glb"
PREVIEW = ROOT / "export" / "pathology-island-assembled-v01-preview.png"


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(TERRAIN))
terrain_objects = set(bpy.context.scene.objects)

bpy.ops.import_scene.gltf(filepath=str(BUILDING))
building_objects = [obj for obj in bpy.context.scene.objects if obj not in terrain_objects]


def mat(name, color, metallic=0.0, roughness=0.5):
    material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def cube(name, location, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("edge-softening", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj

# Fit the detailed building onto the existing 24 m island while retaining a
# clear visitor route from the north connection to the entrance.
scale = 0.66
for obj in building_objects:
    obj.scale *= scale
    scaled = obj.location * scale
    obj.location = Vector((-scaled.x, -scaled.y, scaled.z)) + Vector((0.0, -2.15, 1.05))
    obj.rotation_euler.z += pi
    obj["component_id"] = "BLD-PATHOLOGY-CENTER-001"

for obj in terrain_objects:
    obj["component_id"] = "ENV-PATHOLOGY-TERRAIN-001"

# Direct clinic route from the north bridge gate to the front entrance.
path_mat = mat("pathology-route-stone", (0.42, 0.31, 0.24, 1), roughness=0.68)
soil_mat = mat("pathology-planter-soil", (0.10, 0.045, 0.022, 1), roughness=0.90)
edge_mat = mat("pathology-route-edge", (0.72, 0.57, 0.42, 1), roughness=0.60)
path = cube("walkable-pathology-entry-route", (0.0, 6.05, 1.16), (1.22, 5.45, 0.10), path_mat, 0.10)
path["component_id"] = "NAV-PATHOLOGY-ENTRY-001"
path["walkable"] = True
for side in (-1, 1):
    curb = cube("pathology-route-curb", (side * 1.34, 6.05, 1.20), (0.10, 5.45, 0.12), edge_mat, 0.05)
    curb["component_id"] = "COL-PATHOLOGY-ROUTE-EDGE-001"
    planter = cube("pathology-route-planter", (side * 2.18, 6.05, 1.12), (0.70, 4.95, 0.06), soil_mat, 0.12)
    planter["component_id"] = "ENV-PATHOLOGY-PLANTER-001"

# Export only the assembled navigable scene; cinematic lights are preview-only.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLB", export_apply=True)

# Water plane and atmosphere are intentionally outside the deliverable GLB.
bpy.ops.mesh.primitive_plane_add(size=70, location=(0, 0, -2.22))
water = bpy.context.object
water.name = "preview-ocean"
water.data.materials.append(mat("preview-ocean-mat", (0.006, 0.045, 0.075, 1), metallic=0.3, roughness=0.16))

for location, energy, size, color in (
    ((-14, -17, 22), 2600, 10, (1.0, 0.58, 0.34)),
    ((16, -2, 15), 2100, 9, (0.23, 0.48, 1.0)),
    ((0, 14, 18), 1700, 8, (0.82, 0.30, 0.48)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector((0, -1.0, 2.6)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(21.5, 26.0, 18.5))
camera = bpy.context.object
camera.data.lens = 60
camera.rotation_euler = (Vector((0, -0.8, 1.7)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("hope-night")
scene.world.color = (0.004, 0.009, 0.026)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)

print(f"building_objects={len(building_objects)}")
print(f"terrain_objects={len(terrain_objects)}")
print(f"output={OUTPUT}")
print(f"preview={PREVIEW}")
