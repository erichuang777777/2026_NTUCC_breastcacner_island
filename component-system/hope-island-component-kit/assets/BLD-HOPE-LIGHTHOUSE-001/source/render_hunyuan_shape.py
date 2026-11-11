from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "lighthouse-hunyuan-shape-v01.glb"
PREVIEW = ROOT / "export" / "lighthouse-hunyuan-shape-v01-preview.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
mins = Vector((min(point.x for point in corners), min(point.y for point in corners), min(point.z for point in corners)))
maxs = Vector((max(point.x for point in corners), max(point.y for point in corners), max(point.z for point in corners)))
center = (mins + maxs) / 2
scale = 6 / (maxs.z - mins.z)
for obj in meshes:
    obj.location = (obj.location - center) * scale
    obj.location.z += 3
    obj.scale *= scale
    obj.select_set(True)

mat = bpy.data.materials.new("inspection-clay")
mat.diffuse_color = (.72, .52, .42, 1)
mat.use_nodes = True
shader = mat.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value = (.72, .52, .42, 1)
shader.inputs["Roughness"].default_value = .62
for obj in meshes:
    obj.data.materials.clear();obj.data.materials.append(mat)

bpy.ops.mesh.primitive_plane_add(size=24, location=(0, 0, -.02))
floor = bpy.context.object
floor_mat = bpy.data.materials.new("floor")
floor_mat.diffuse_color = (.12, .14, .16, 1)
floor.data.materials.append(floor_mat)

bpy.ops.object.light_add(type="AREA", location=(-4, -4, 8))
bpy.context.object.data.energy = 1100
bpy.context.object.data.shape = "DISK"
bpy.context.object.data.size = 5
bpy.ops.object.light_add(type="AREA", location=(4, 1, 5))
bpy.context.object.data.energy = 700
bpy.context.object.data.size = 4

bpy.ops.object.camera_add(location=(7, -10, 5.2))
camera = bpy.context.object
camera.data.lens = 62
camera.rotation_euler = (Vector((0, 0, 3)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("inspection-world")
scene.world.color = (.025, .035, .05)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"preview={PREVIEW}")
