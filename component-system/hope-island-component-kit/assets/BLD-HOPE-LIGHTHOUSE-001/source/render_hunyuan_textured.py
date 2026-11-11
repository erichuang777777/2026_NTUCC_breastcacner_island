from pathlib import Path
import os

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / os.environ.get(
    "LIGHTHOUSE_SOURCE", "lighthouse-hunyuan-textured-v01.glb"
)
PREVIEW = ROOT / "export" / os.environ.get(
    "LIGHTHOUSE_PREVIEW", "lighthouse-hunyuan-textured-v01-preview.png"
)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
mins = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
maxs = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
center = (mins + maxs) / 2
scale = 6 / (maxs.z - mins.z)
for obj in meshes:
    obj.location = (obj.location - center) * scale
    obj.location.z += 3
    obj.scale *= scale

bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, -0.02))
floor = bpy.context.object
floor_mat = bpy.data.materials.new("inspection-floor")
floor_mat.use_nodes = True
floor_shader = floor_mat.node_tree.nodes.get("Principled BSDF")
floor_shader.inputs["Base Color"].default_value = (0.035, 0.055, 0.075, 1)
floor_shader.inputs["Roughness"].default_value = 0.72
floor.data.materials.append(floor_mat)

for location, energy, size, color in (
    ((-4, -5, 8), 1150, 5, (1.0, 0.78, 0.62)),
    ((5, -1, 6), 850, 4, (0.55, 0.72, 1.0)),
    ((0, 4, 4), 500, 3, (1.0, 0.42, 0.58)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector((0, 0, 3)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(7.2, -10.5, 5.0))
camera = bpy.context.object
camera.data.lens = 62
camera.rotation_euler = (Vector((0, 0, 3.05)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("inspection-world")
scene.world.use_nodes = True
world_shader = scene.world.node_tree.nodes.get("Background")
world_shader.inputs["Color"].default_value = (0.012, 0.022, 0.045, 1)
world_shader.inputs["Strength"].default_value = 0.28
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"preview={PREVIEW}")
