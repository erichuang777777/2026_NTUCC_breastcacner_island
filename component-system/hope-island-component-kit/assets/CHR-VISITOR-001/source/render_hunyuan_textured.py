from pathlib import Path
import os

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / os.environ.get(
    "CHARACTER_SOURCE", "chr-visitor-hunyuan-textured-v02.glb"
)
PREVIEW = ROOT / "export" / os.environ.get(
    "CHARACTER_PREVIEW", "chr-visitor-hunyuan-textured-v02-preview.png"
)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
action_name = os.environ.get("CHARACTER_ACTION")
if armatures and action_name and action_name in bpy.data.actions:
    armatures[0].animation_data_create()
    armatures[0].animation_data.action = bpy.data.actions[action_name]
scene_frame = int(os.environ.get("CHARACTER_FRAME", "1"))
bpy.context.scene.frame_set(scene_frame)

meshes = [
    obj
    for obj in bpy.context.scene.objects
    if obj.type == "MESH" and len(obj.data.materials) > 0
]
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
mins = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
maxs = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
center = (mins + maxs) / 2
scale = 5.65 / (maxs.z - mins.z)
for obj in meshes:
    obj.location = (obj.location - center) * scale
    obj.location.z += 2.825
    obj.scale *= scale

bpy.ops.mesh.primitive_plane_add(size=18, location=(0, 0, -0.02))
floor = bpy.context.object
floor_material = bpy.data.materials.new("inspection-floor")
floor_material.use_nodes = True
floor_shader = floor_material.node_tree.nodes.get("Principled BSDF")
floor_shader.inputs["Base Color"].default_value = (0.035, 0.045, 0.065, 1)
floor_shader.inputs["Roughness"].default_value = 0.76
floor.data.materials.append(floor_material)

for location, energy, size, color in (
    ((-4, -5, 8), 1000, 5, (1.0, 0.84, 0.72)),
    ((4, -2, 5), 600, 4, (0.66, 0.78, 1.0)),
    ((0, 4, 6), 450, 3, (1.0, 0.7, 0.74)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector((0, 0, 2.9)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(0, -11.7, 2.95))
camera = bpy.context.object
camera.data.lens = 67
camera.rotation_euler = (Vector((0, 0, 2.8)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("inspection-world")
scene.world.use_nodes = True
world_shader = scene.world.node_tree.nodes.get("Background")
world_shader.inputs["Color"].default_value = (0.012, 0.018, 0.032, 1)
world_shader.inputs["Strength"].default_value = 0.32
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"preview={PREVIEW}")
