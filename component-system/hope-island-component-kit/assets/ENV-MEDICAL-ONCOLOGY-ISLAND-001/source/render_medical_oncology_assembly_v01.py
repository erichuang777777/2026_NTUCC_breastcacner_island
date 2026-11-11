"""Render the web-equivalent three-layer medical-oncology island assembly."""

from pathlib import Path
import math

import bpy
from mathutils import Vector


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TERRAIN = ROOT / "export/medical-oncology-terrain-detached-v01.glb"
LANDSCAPE = ROOT / "export/medical-oncology-landscape-blender-v03.glb"
CLINIC = ROOT / "export/medical-oncology-clinic-blender-v04.glb"
OUTPUT = ROOT / "export/medical-oncology-assembly-v01-preview.png"


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def import_layer(path, name, scale=1.0, height=0.0):
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = list(bpy.context.selected_objects)
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.scale = (scale, scale, scale)
    root.location = (0.0, 0.0, height)
    for obj in imported:
        if obj.parent is None:
            obj.parent = root
    return root


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

import_layer(TERRAIN, "ENV-MEDONC-TERRAIN-PREVIEW")
import_layer(LANDSCAPE, "ENV-MEDONC-LANDSCAPE-PREVIEW", 0.25, 0.80)
import_layer(CLINIC, "BLD-MEDONC-CLINIC-PREVIEW", 0.245, 0.94)

sea_mat = bpy.data.materials.new("preview-sea")
sea_mat.use_nodes = True
sea_shader = sea_mat.node_tree.nodes.get("Principled BSDF")
sea_shader.inputs["Base Color"].default_value = (0.03, 0.16, 0.19, 1.0)
sea_shader.inputs["Roughness"].default_value = 0.23
sea_shader.inputs["Metallic"].default_value = 0.12
bpy.ops.mesh.primitive_plane_add(size=40, location=(0.0, 0.0, -1.08))
bpy.context.object.data.materials.append(sea_mat)

world = bpy.context.scene.world or bpy.data.worlds.new("Preview World")
bpy.context.scene.world = world
world.use_nodes = True
background = world.node_tree.nodes.get("Background")
background.inputs["Color"].default_value = (0.03, 0.065, 0.095, 1.0)
background.inputs["Strength"].default_value = 0.30

bpy.ops.object.light_add(type="SUN", location=(-7.0, -8.0, 12.0))
sun = bpy.context.object
sun.data.energy = 2.25
sun.data.color = (1.0, 0.60, 0.38)
sun.rotation_euler = (math.radians(32), math.radians(-16), math.radians(-34))

bpy.ops.object.light_add(type="AREA", location=(2.0, -4.0, 8.5))
key = bpy.context.object
key.data.energy = 1300
key.data.shape = "DISK"
key.data.size = 6.0
key.data.color = (1.0, 0.65, 0.44)
look_at(key, (0.0, 0.0, 1.0))

bpy.ops.object.light_add(type="AREA", location=(-6.0, 3.0, 5.5))
fill = bpy.context.object
fill.data.energy = 800
fill.data.size = 5.0
fill.data.color = (0.34, 0.60, 1.0)
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
scene.view_settings.look = "AgX - Medium High Contrast"

bpy.ops.render.render(write_still=True)
print(f"Rendered {OUTPUT}")
