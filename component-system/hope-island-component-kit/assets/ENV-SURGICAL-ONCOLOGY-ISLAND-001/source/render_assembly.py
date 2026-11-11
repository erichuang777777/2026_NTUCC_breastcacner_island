from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
MACRO_BLEND = ROOT.parent / "ENV-TAIWAN-ARCHIPELAGO-001" / "source" / "model-macro.blend"
OUTPUT = ROOT / "export" / "surgical-oncology-assembly-preview-v01.png"

bpy.ops.wm.open_mainfile(filepath=str(MACRO_BLEND))
scene = bpy.context.scene

camera = scene.camera
camera.location = (-3.0, -12.6, 8.8)
camera.data.lens = 58
camera.rotation_euler = (Vector((-3.0, 0.55, .85)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(OUTPUT)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"preview={OUTPUT}")
