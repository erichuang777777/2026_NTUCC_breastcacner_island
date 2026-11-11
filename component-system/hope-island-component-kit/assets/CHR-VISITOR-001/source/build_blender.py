from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
BLEND_PATH = ROOT / "source" / "model.blend"
GLB_PATH = ROOT / "export" / "chr-visitor-001.glb"
PREVIEW_PATH = ROOT / "export" / "preview-v02.png"


def material(name, color):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = 0.82
    return value


def sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons: polygon.use_smooth = True
    return obj


def cylinder(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons: polygon.use_smooth = True
    bevel = obj.modifiers.new("soft-edges", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 2
    return obj


def cone(name, location, radius_top, radius_bottom, depth, mat):
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=radius_bottom, radius2=radius_top, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons: polygon.use_smooth = True
    bevel = obj.modifiers.new("soft-edges", "BEVEL")
    bevel.width = 0.035
    bevel.segments = 2
    return obj


def cube(name, location, scale, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("soft-edges", "BEVEL")
    bevel.width = 0.035
    bevel.segments = 2
    return obj


def torus(name, location, major_radius, minor_radius, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius, minor_radius=minor_radius,
        major_segments=28, minor_segments=8, location=location, rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons: polygon.use_smooth = True
    return obj


def parent_to_bone(obj, armature, bone_name):
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone_name
    obj.matrix_world = world


def add_bone(edit_bones, name, head, tail, parent=None):
    bone = edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.parent = parent
    return bone


def make_action(armature, name, frames, rotations):
    action = bpy.data.actions.new(name)
    armature.animation_data_create()
    armature.animation_data.action = action
    for frame in frames:
        for bone_name, axis_values in rotations(frame).items():
            bone = armature.pose.bones[bone_name]
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = axis_values
            bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone_name)
    action.frame_range = (frames[0], frames[-1])
    track = armature.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, frames[0], action)
    armature.animation_data.action = None
    return action


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "CHR-VISITOR-001"
scene.unit_settings.system = "METRIC"
scene.render.fps = 24

skin = material("skin", (0.906, 0.718, 0.588))
scarf = material("rose-headscarf", (0.698, 0.443, 0.459))
rose = material("rose-cardigan", (0.722, 0.463, 0.502))
cream = material("cream-shirt", (0.910, 0.882, 0.824))
blue = material("mist-blue-pants", (0.365, 0.482, 0.557))
white = material("warm-white-shoes", (0.930, 0.914, 0.875))
bag = material("cream-backpack", (0.835, 0.804, 0.737))
ribbon = material("hope-ribbon", (0.824, 0.412, 0.494))
eye = material("eye", (0.20, 0.17, 0.16))
brow = material("brow", (0.25, 0.18, 0.15))
eye_white = material("eye-white", (0.96, 0.94, 0.89))
eye_glint = material("eye-glint", (1.0, 0.98, 0.94))
blush = material("blush", (0.88, 0.48, 0.48))
mouth = material("mouth", (0.55, 0.20, 0.20))
sole = material("shoe-sole", (0.72, 0.69, 0.64))

bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
armature = bpy.context.object
armature.name = "CHR-VISITOR-001-rig"
edit = armature.data.edit_bones
edit.remove(edit[0])
root = add_bone(edit, "root", (0, 0, 0), (0, 0, 0.35))
spine = add_bone(edit, "spine", (0, 0, 0.65), (0, 0, 1.45), root)
head_bone = add_bone(edit, "head", (0, 0, 1.45), (0, 0, 2.35), spine)
left_arm = add_bone(edit, "arm.L", (-0.43, 0, 1.42), (-0.43, 0, 0.72), spine)
right_arm = add_bone(edit, "arm.R", (0.43, 0, 1.42), (0.43, 0, 0.72), spine)
left_leg = add_bone(edit, "leg.L", (-0.2, 0, 0.72), (-0.2, 0, 0.05), root)
right_leg = add_bone(edit, "leg.R", (0.2, 0, 0.72), (0.2, 0, 0.05), root)
bpy.ops.object.mode_set(mode="OBJECT")

parts = [
    (cone("cream-shirt", (0, 0, 1.10), 0.34, 0.45, 0.82, cream), "spine"),
    (cube("cardigan-left", (-0.25, 0.36, 1.12), (0.18, 0.07, 0.43), rose), "spine"),
    (cube("cardigan-right", (0.25, 0.36, 1.12), (0.18, 0.07, 0.43), rose), "spine"),
    (cube("cardigan-lapel-left", (-0.16, 0.46, 1.34), (0.10, 0.035, 0.25), rose, (0, 0, -0.22)), "spine"),
    (cube("cardigan-lapel-right", (0.16, 0.46, 1.34), (0.10, 0.035, 0.25), rose, (0, 0, 0.22)), "spine"),
    (cube("cardigan-pocket-left", (-0.27, 0.45, 0.96), (0.12, 0.035, 0.10), rose), "spine"),
    (cube("cardigan-pocket-right", (0.27, 0.45, 0.96), (0.12, 0.035, 0.10), rose), "spine"),
    (cube("shirt-rib-center", (0, 0.455, 1.16), (0.018, 0.012, 0.30), bag), "spine"),
    (cube("backpack", (0, -0.40, 1.17), (0.35, 0.12, 0.40), bag), "spine"),
    (cube("backpack-flap", (0, -0.54, 1.36), (0.33, 0.035, 0.13), bag), "spine"),
    (cube("backpack-pocket", (0, -0.54, 1.08), (0.22, 0.035, 0.13), bag), "spine"),
    (torus("backpack-strap-left", (-0.28, 0, 1.18), 0.28, 0.035, bag, (math.pi / 2, 0, 0)), "spine"),
    (torus("backpack-strap-right", (0.28, 0, 1.18), 0.28, 0.035, bag, (math.pi / 2, 0, 0)), "spine"),
    (sphere("hope-ribbon-pin", (0.28, 0.46, 1.32), (0.07, 0.035, 0.10), ribbon), "spine"),
    (sphere("head", (0, 0, 1.98), (0.56, 0.53, 0.59), skin), "head"),
    (sphere("ear-left", (-0.57, 0.02, 1.99), (0.11, 0.075, 0.15), skin), "head"),
    (sphere("ear-right", (0.57, 0.02, 1.99), (0.11, 0.075, 0.15), skin), "head"),
    (sphere("headscarf-cap", (0, -0.10, 2.12), (0.63, 0.51, 0.50), scarf), "head"),
    (torus("headscarf-fold-1", (0, 0.02, 2.12), 0.51, 0.035, scarf, (math.pi / 2, 0.20, 0.18)), "head"),
    (torus("headscarf-fold-2", (0, 0.00, 2.18), 0.49, 0.032, scarf, (math.pi / 2, -0.16, -0.12)), "head"),
    (torus("headscarf-fold-3", (0, -0.02, 2.23), 0.43, 0.025, scarf, (math.pi / 2, 0.08, -0.22)), "head"),
    (sphere("headscarf-knot", (0, -0.55, 1.88), (0.20, 0.15, 0.17), scarf), "head"),
    (sphere("headscarf-tail-left", (-0.16, -0.58, 1.66), (0.14, 0.08, 0.28), scarf), "head"),
    (sphere("headscarf-tail-right", (0.14, -0.58, 1.64), (0.13, 0.08, 0.26), scarf), "head"),
    (sphere("eye-white-left", (-0.19, 0.525, 2.04), (0.115, 0.028, 0.12), eye_white), "head"),
    (sphere("eye-white-right", (0.19, 0.525, 2.04), (0.115, 0.028, 0.12), eye_white), "head"),
    (sphere("pupil-left", (-0.19, 0.555, 2.04), (0.070, 0.024, 0.080), eye), "head"),
    (sphere("pupil-right", (0.19, 0.555, 2.04), (0.070, 0.024, 0.080), eye), "head"),
    (sphere("eye-glint-left", (-0.165, 0.578, 2.075), (0.018, 0.010, 0.020), eye_glint), "head"),
    (sphere("eye-glint-right", (0.215, 0.578, 2.075), (0.018, 0.010, 0.020), eye_glint), "head"),
    (cube("brow-left", (-0.19, 0.55, 2.17), (0.085, 0.012, 0.014), brow, (0, 0, -0.08)), "head"),
    (cube("brow-right", (0.19, 0.55, 2.17), (0.085, 0.012, 0.014), brow, (0, 0, 0.08)), "head"),
    (sphere("nose", (0, 0.56, 1.96), (0.045, 0.035, 0.055), skin), "head"),
    (sphere("smile-left", (-0.055, 0.557, 1.875), (0.045, 0.015, 0.018), mouth), "head"),
    (sphere("smile-right", (0.055, 0.557, 1.875), (0.045, 0.015, 0.018), mouth), "head"),
    (sphere("blush-left", (-0.36, 0.515, 1.92), (0.085, 0.015, 0.045), blush), "head"),
    (sphere("blush-right", (0.36, 0.515, 1.92), (0.085, 0.015, 0.045), blush), "head"),
    (cylinder("cardigan-sleeve-left", (-0.47, 0, 1.06), 0.13, 0.70, rose), "arm.L"),
    (cylinder("cardigan-sleeve-right", (0.47, 0, 1.06), 0.13, 0.70, rose), "arm.R"),
    (torus("sleeve-cuff-left", (-0.47, 0, 0.76), 0.13, 0.025, rose), "arm.L"),
    (torus("sleeve-cuff-right", (0.47, 0, 0.76), 0.13, 0.025, rose), "arm.R"),
    (sphere("hand-left", (-0.47, 0, 0.69), (0.13, 0.13, 0.13), skin), "arm.L"),
    (sphere("hand-right", (0.47, 0, 0.69), (0.13, 0.13, 0.13), skin), "arm.R"),
    (sphere("thumb-left", (-0.38, 0.08, 0.69), (0.045, 0.055, 0.075), skin), "arm.L"),
    (sphere("thumb-right", (0.38, 0.08, 0.69), (0.045, 0.055, 0.075), skin), "arm.R"),
    (cylinder("pants-left", (-0.20, 0, 0.39), 0.16, 0.66, blue), "leg.L"),
    (cylinder("pants-right", (0.20, 0, 0.39), 0.16, 0.66, blue), "leg.R"),
    (torus("pants-cuff-left", (-0.20, 0, 0.16), 0.155, 0.025, blue), "leg.L"),
    (torus("pants-cuff-right", (0.20, 0, 0.16), 0.155, 0.025, blue), "leg.R"),
    (sphere("shoe-left", (-0.20, 0.09, 0.07), (0.19, 0.29, 0.14), white), "leg.L"),
    (sphere("shoe-right", (0.20, 0.09, 0.07), (0.19, 0.29, 0.14), white), "leg.R"),
    (cube("shoe-sole-left", (-0.20, 0.10, 0.005), (0.19, 0.29, 0.025), sole), "leg.L"),
    (cube("shoe-sole-right", (0.20, 0.10, 0.005), (0.19, 0.29, 0.025), sole), "leg.R"),
    (cube("shoe-panel-left", (-0.20, 0.285, 0.105), (0.13, 0.10, 0.035), bag, (math.radians(-12), 0, 0)), "leg.L"),
    (cube("shoe-panel-right", (0.20, 0.285, 0.105), (0.13, 0.10, 0.035), bag, (math.radians(-12), 0, 0)), "leg.R"),
]
for obj, bone_name in parts:
    parent_to_bone(obj, armature, bone_name)

make_action(armature, "idle", [1, 24, 48], lambda frame: {
    "spine": (math.radians(1.5 if frame == 24 else 0), 0, 0),
    "head": (math.radians(-1 if frame == 24 else 0), 0, 0),
})
make_action(armature, "walk", [1, 7, 13, 19, 25], lambda frame: {
    "arm.L": (math.radians({1: 24, 7: 0, 13: -24, 19: 0, 25: 24}[frame]), 0, 0),
    "arm.R": (math.radians({1: -24, 7: 0, 13: 24, 19: 0, 25: -24}[frame]), 0, 0),
    "leg.L": (math.radians({1: -24, 7: 0, 13: 24, 19: 0, 25: -24}[frame]), 0, 0),
    "leg.R": (math.radians({1: 24, 7: 0, 13: -24, 19: 0, 25: 24}[frame]), 0, 0),
})

scene["component_id"] = "CHR-VISITOR-001"
scene["collider"] = "capsule radius 0.48 m"
BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
bpy.ops.export_scene.gltf(
    filepath=str(GLB_PATH), export_format="GLB", export_apply=True, export_yup=True,
    export_animations=True, export_animation_mode="ACTIONS", export_materials="EXPORT",
)

# 角色審查預覽：正面三分之四角度、柔和攝影棚光，不納入 GLB。
armature.animation_data_clear()
for pose_bone in armature.pose.bones:
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = (0, 0, 0)
scene.frame_set(1)
ground_mat = material("preview-ground", (0.93, 0.93, 0.91))
bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.03));ground=bpy.context.object;ground.data.materials.append(ground_mat)
bpy.ops.object.light_add(type="AREA", location=(3.8, 4.5, 6.0));key=bpy.context.object;key.data.energy=820;key.data.shape="DISK";key.data.size=4.0
bpy.ops.object.light_add(type="AREA", location=(-3.5, 2.0, 3.2));fill=bpy.context.object;fill.data.energy=460;fill.data.size=3.0
bpy.ops.object.light_add(type="AREA", location=(0, -3.5, 4.8));rim=bpy.context.object;rim.data.energy=620;rim.data.size=2.5
bpy.ops.object.camera_add(location=(3.8, 6.8, 3.05));camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,1.2))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=58;scene.camera=camera
scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=900;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG";scene.render.filepath=str(PREVIEW_PATH);scene.render.film_transparent=False
scene.world=bpy.data.worlds.new("Character Preview World");scene.world.color=(0.82,0.85,0.88)
scene.view_settings.look="AgX - Medium High Contrast";bpy.ops.render.render(write_still=True)
print(f"BLEND={BLEND_PATH}")
print(f"GLB={GLB_PATH}")
print(f"PREVIEW={PREVIEW_PATH}")
