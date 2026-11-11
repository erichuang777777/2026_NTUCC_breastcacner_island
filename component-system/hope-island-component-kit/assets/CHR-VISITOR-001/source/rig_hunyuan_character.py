from pathlib import Path
from math import radians

import bpy


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "chr-visitor-hunyuan-meshopt-lod0-v03.glb"
OUTPUT = ROOT / "export" / "chr-visitor-hunyuan-rigged-lod0-v03.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
mesh = next(obj for obj in bpy.context.scene.objects if obj.type == "MESH")

bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
armature = bpy.context.object
armature.name = "CHR_VISITOR_RIG"
armature.data.name = "CHR_VISITOR_ARMATURE"
armature.show_in_front = True
armature.data.edit_bones.remove(armature.data.edit_bones[0])


def add_bone(name, head, tail, parent=None, deform=True):
    bone = armature.data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.use_deform = deform
    if parent:
        bone.parent = armature.data.edit_bones[parent]
        bone.use_connect = False
    return bone


add_bone("root", (0, 0, -0.98), (0, 0, -0.12), deform=False)
add_bone("hips", (0, 0, -0.18), (0, 0, 0.04), "root")
add_bone("spine", (0, 0, 0.04), (0, 0, 0.28), "hips")
add_bone("chest", (0, 0, 0.28), (0, 0, 0.47), "spine")
add_bone("neck", (0, 0, 0.47), (0, 0, 0.57), "chest")
add_bone("head", (0, 0, 0.57), (0, 0, 0.91), "neck")

for side, sign in (("L", 1), ("R", -1)):
    add_bone(f"upper_arm.{side}", (0.18 * sign, 0, 0.40), (0.40 * sign, 0, 0.18), "chest")
    add_bone(f"lower_arm.{side}", (0.40 * sign, 0, 0.18), (0.52 * sign, 0, -0.05), f"upper_arm.{side}")
    add_bone(f"hand.{side}", (0.52 * sign, 0, -0.05), (0.55 * sign, 0, -0.19), f"lower_arm.{side}")
    add_bone(f"upper_leg.{side}", (0.13 * sign, 0, -0.12), (0.14 * sign, 0, -0.52), "hips")
    add_bone(f"lower_leg.{side}", (0.14 * sign, 0, -0.52), (0.14 * sign, 0, -0.87), f"upper_leg.{side}")
    add_bone(f"foot.{side}", (0.14 * sign, 0, -0.87), (0.14 * sign, -0.18, -0.96), f"lower_leg.{side}")

bpy.ops.object.mode_set(mode="OBJECT")
mesh.parent = armature
armature_modifier = mesh.modifiers.new(name="CHR_VISITOR_ARMATURE", type="ARMATURE")
armature_modifier.object = armature

for group in list(mesh.vertex_groups):
    mesh.vertex_groups.remove(group)
groups = {
    bone.name: mesh.vertex_groups.new(name=bone.name)
    for bone in armature.data.bones
    if bone.use_deform
}

for vertex in mesh.data.vertices:
    x, y, z = vertex.co
    absolute_x = abs(x)
    if z > 0.53:
        bone_name = "head"
    elif z > 0.45:
        bone_name = "neck"
    elif absolute_x > 0.21 and z > -0.24:
        side = "L" if x >= 0 else "R"
        if absolute_x > 0.49:
            bone_name = f"hand.{side}"
        elif absolute_x > 0.37:
            bone_name = f"lower_arm.{side}"
        else:
            bone_name = f"upper_arm.{side}"
    elif z < -0.11:
        side = "L" if x >= 0 else "R"
        if z < -0.84:
            bone_name = f"foot.{side}" if y < -0.035 or z < -0.91 else f"lower_leg.{side}"
        elif z < -0.51:
            bone_name = f"lower_leg.{side}"
        else:
            bone_name = f"upper_leg.{side}"
    elif z > 0.27:
        bone_name = "chest"
    elif z > 0.04:
        bone_name = "spine"
    else:
        bone_name = "hips"
    groups[bone_name].add([vertex.index], 1.0, "REPLACE")


def reset_pose():
    for pose_bone in armature.pose.bones:
        pose_bone.rotation_mode = "XYZ"
        pose_bone.rotation_euler = (0, 0, 0)
        pose_bone.location = (0, 0, 0)
        pose_bone.scale = (1, 1, 1)


def key_pose(frame, rotations=None, locations=None):
    rotations = rotations or {}
    locations = locations or {}
    bpy.context.scene.frame_set(frame)
    reset_pose()
    for name, values in rotations.items():
        armature.pose.bones[name].rotation_euler = tuple(radians(value) for value in values)
    for name, values in locations.items():
        armature.pose.bones[name].location = values
    for pose_bone in armature.pose.bones:
        pose_bone.keyframe_insert("rotation_euler", frame=frame)
        pose_bone.keyframe_insert("location", frame=frame)


armature.animation_data_create()
idle = bpy.data.actions.new("idle")
idle.use_frame_range = True
idle.frame_start = 1
idle.frame_end = 60
armature.animation_data.action = idle
key_pose(1)
key_pose(30, rotations={"chest": (0, 0, 1.5), "head": (0, 0, -1)}, locations={"hips": (0, 0, 0.012)})
key_pose(60)

walk = bpy.data.actions.new("walk")
walk.use_frame_range = True
walk.frame_start = 1
walk.frame_end = 24
armature.animation_data.action = walk
key_pose(1, rotations={"upper_leg.L": (18, 0, 0), "upper_leg.R": (-18, 0, 0), "lower_leg.L": (8, 0, 0), "lower_leg.R": (28, 0, 0), "upper_arm.L": (-14, 0, 0), "upper_arm.R": (14, 0, 0)}, locations={"hips": (0, 0, 0.015)})
key_pose(7, rotations={"upper_leg.L": (0, 0, 0), "upper_leg.R": (0, 0, 0), "lower_leg.L": (18, 0, 0), "lower_leg.R": (18, 0, 0)}, locations={"hips": (0, 0, -0.01)})
key_pose(13, rotations={"upper_leg.L": (-18, 0, 0), "upper_leg.R": (18, 0, 0), "lower_leg.L": (28, 0, 0), "lower_leg.R": (8, 0, 0), "upper_arm.L": (14, 0, 0), "upper_arm.R": (-14, 0, 0)}, locations={"hips": (0, 0, 0.015)})
key_pose(19, rotations={"upper_leg.L": (0, 0, 0), "upper_leg.R": (0, 0, 0), "lower_leg.L": (18, 0, 0), "lower_leg.R": (18, 0, 0)}, locations={"hips": (0, 0, -0.01)})
key_pose(24, rotations={"upper_leg.L": (18, 0, 0), "upper_leg.R": (-18, 0, 0), "lower_leg.L": (8, 0, 0), "lower_leg.R": (28, 0, 0), "upper_arm.L": (-14, 0, 0), "upper_arm.R": (14, 0, 0)}, locations={"hips": (0, 0, 0.015)})

armature.animation_data.action = idle
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 60
bpy.context.scene.frame_set(1)

bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
armature.select_set(True)
bpy.context.view_layer.objects.active = armature
bpy.ops.export_scene.gltf(
    filepath=str(OUTPUT),
    export_format="GLB",
    use_selection=True,
    export_apply=False,
    export_texcoords=True,
    export_normals=True,
    export_materials="EXPORT",
    export_image_format="AUTO",
    export_animations=True,
    export_animation_mode="ACTIONS",
    export_skins=True,
    export_def_bones=True,
    export_leaf_bone=False,
)
print(f"output={OUTPUT}")
print(f"bones={len(armature.data.bones)} actions={[action.name for action in bpy.data.actions]}")
