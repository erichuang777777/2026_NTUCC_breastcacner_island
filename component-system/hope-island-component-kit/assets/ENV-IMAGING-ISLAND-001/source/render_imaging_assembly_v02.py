"""Render the detached imaging-island landscape and pavilion as one assembly."""

from pathlib import Path
import math

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LANDSCAPE = ROOT / "export/imaging-island-landscape-v01.glb"
PAVILION = ROOT / "export/imaging-pavilion-blender-v03.glb"
OUTPUT = ROOT / "export/imaging-island-assembly-v02-preview.png"


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.import_scene.gltf(filepath=str(LANDSCAPE))
landscape_objects = list(bpy.context.selected_objects)
landscape_root = bpy.data.objects.new("ENV-IMAGING-LANDSCAPE-PREVIEW", None)
bpy.context.collection.objects.link(landscape_root)
for obj in landscape_objects:
    if obj.parent is None:
        obj.parent = landscape_root

bpy.ops.import_scene.gltf(filepath=str(PAVILION))
pavilion_objects = list(bpy.context.selected_objects)
pavilion_root = bpy.data.objects.new("BLD-IMAGING-PAVILION-PREVIEW", None)
bpy.context.collection.objects.link(pavilion_root)
pavilion_root.scale = (0.25, 0.25, 0.25)
pavilion_root.location = (0.0, 0.0, 0.94)
for obj in pavilion_objects:
    if obj.parent is None:
        obj.parent = pavilion_root

# A dark teal sea plane provides the same contrast as the continuous web world.
sea_mat = bpy.data.materials.new("preview-sea")
sea_mat.diffuse_color = (0.035, 0.17, 0.20, 1.0)
sea_mat.use_nodes = True
sea_shader = sea_mat.node_tree.nodes.get("Principled BSDF")
sea_shader.inputs["Base Color"].default_value = (0.035, 0.17, 0.20, 1.0)
sea_shader.inputs["Roughness"].default_value = 0.24
sea_shader.inputs["Metallic"].default_value = 0.10
bpy.ops.mesh.primitive_plane_add(size=40, location=(0.0, 0.0, -1.08))
bpy.context.object.data.materials.append(sea_mat)

world = bpy.context.scene.world or bpy.data.worlds.new("Preview World")
bpy.context.scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.035, 0.075, 0.10, 1.0)
background.inputs["Strength"].default_value = 0.32

bpy.ops.object.light_add(type="SUN", location=(-6.0, -8.0, 12.0))
sun = bpy.context.object
sun.data.energy = 2.2
sun.data.color = (1.0, 0.62, 0.40)
sun.rotation_euler = (math.radians(34), math.radians(-18), math.radians(-32))

bpy.ops.object.light_add(type="AREA", location=(1.5, -4.0, 8.0))
key = bpy.context.object
key.data.energy = 1250
key.data.shape = "DISK"
key.data.size = 6.0
key.data.color = (1.0, 0.66, 0.46)
look_at(key, (0.0, 0.0, 1.0))

bpy.ops.object.light_add(type="AREA", location=(-6.0, 3.0, 5.0))
fill = bpy.context.object
fill.data.energy = 850
fill.data.size = 5.0
fill.data.color = (0.36, 0.64, 1.0)
look_at(fill, (0.0, 0.0, 1.1))

bpy.ops.object.camera_add(location=(8.6, -10.4, 7.8))
camera = bpy.context.object
camera.data.lens = 57
look_at(camera, (0.0, 0.0, 1.0))
bpy.context.scene.camera = camera

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUTPUT)
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.resolution_percentage = 100

bpy.ops.render.render(write_still=True)
print(f"Rendered {OUTPUT}")
