from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "imaging-pavilion-hunyuan-shape-v01.glb"
PREVIEW = ROOT / "export" / "imaging-pavilion-hunyuan-shape-v01-preview.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
mins = Vector(tuple(min(point[index] for point in corners) for index in range(3)))
maxs = Vector(tuple(max(point[index] for point in corners) for index in range(3)))
center = (mins + maxs) / 2
scale = 10 / max(maxs.x - mins.x, maxs.y - mins.y)
for obj in meshes:
    obj.location = (obj.location - center) * scale
    obj.location.z += (maxs.z - mins.z) * scale / 2
    obj.scale *= scale

clay = bpy.data.materials.new("imaging-pavilion-inspection-clay")
clay.use_nodes = True
shader = clay.node_tree.nodes.get("Principled BSDF")
shader.inputs["Base Color"].default_value = (0.54, 0.67, 0.65, 1)
shader.inputs["Roughness"].default_value = 0.55
for obj in meshes:
    obj.data.materials.clear()
    obj.data.materials.append(clay)

bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, -0.02))
floor = bpy.context.object
floor_mat = bpy.data.materials.new("inspection-floor")
floor_mat.diffuse_color = (0.025, 0.035, 0.05, 1)
floor.data.materials.append(floor_mat)

for location, energy, size, color in (
    ((-7, -8, 13), 2200, 7, (1.0, 0.80, 0.66)),
    ((8, 0, 9), 1500, 6, (0.58, 0.78, 1.0)),
    ((0, 7, 7), 950, 5, (1.0, 0.52, 0.58)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector((0, 0, 2.0)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(11.5, -15.8, 8.2))
camera = bpy.context.object
camera.data.lens = 58
camera.rotation_euler = (Vector((0, 0, 2.0)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("inspection-world")
scene.world.color = (0.01, 0.018, 0.035)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"preview={PREVIEW}")
