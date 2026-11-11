from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "chr-visitor-hunyuan-shape-v02.glb"
PREVIEW = ROOT / "export" / "chr-visitor-hunyuan-shape-v02-preview.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
mins = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
maxs = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
center = (mins + maxs) / 2
height = maxs.z - mins.z
scale = 5.8 / height
for obj in meshes:
    obj.location = (obj.location - center) * scale
    obj.location.z += 2.9
    obj.scale *= scale

material = bpy.data.materials.new("character-inspection-clay")
material.use_nodes = True
shader = material.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value = (0.70, 0.42, 0.38, 1)
shader.inputs["Roughness"].default_value = 0.68
for obj in meshes:
    obj.data.materials.clear()
    obj.data.materials.append(material)

bpy.ops.mesh.primitive_plane_add(size=18, location=(0, 0, -0.02))
floor = bpy.context.object
floor_material = bpy.data.materials.new("inspection-floor")
floor_material.diffuse_color = (0.075, 0.09, 0.115, 1)
floor.data.materials.append(floor_material)

for location, energy, size in [((-4, -5, 8), 1000, 5), ((4, -1, 5), 650, 4), ((0, 4, 6), 500, 3)]:
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.rotation_euler = (Vector((0, 0, 3)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(0, -10.7, 3.15))
camera = bpy.context.object
camera.data.lens = 68
camera.rotation_euler = (Vector((0, 0, 3.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("inspection-world")
scene.world.color = (0.018, 0.025, 0.04)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"bounds_min={tuple(round(value, 4) for value in mins)}")
print(f"bounds_max={tuple(round(value, 4) for value in maxs)}")
print(f"preview={PREVIEW}")
