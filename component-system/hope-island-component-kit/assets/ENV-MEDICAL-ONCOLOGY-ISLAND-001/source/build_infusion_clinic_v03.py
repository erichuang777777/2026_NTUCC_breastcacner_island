from math import atan, cos, pi, sin, sqrt
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "medical-oncology-clinic-blender-v03.glb"
PREVIEW = ROOT / "export" / "medical-oncology-clinic-blender-v03-preview.png"


def mat(name, color, metallic=0.0, roughness=0.45, transmission=0.0, emission=None):
    value = bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["IOR"].default_value = 1.45
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 1.8
    return value


def cube(name, loc, scale, material, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("architectural-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    obj.data.materials.append(material)
    return obj


def cylinder(name, loc, radius, depth, material, scale=(1, 1, 1), vertices=96, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def barrel(name, width, depth, spring_z, radius, material, segments=40):
    verts, faces = [], []
    for y in (-depth / 2, depth / 2):
        for index in range(segments + 1):
            angle = pi * index / segments
            verts.append((width * cos(angle) / 2, y, spring_z + radius * sin(angle)))
    row = segments + 1
    for index in range(segments):
        faces.append((index, index + 1, row + index + 1, row + index))
    faces.extend([tuple(range(row - 1, -1, -1)), tuple(range(row, row * 2)), (0, row, row * 2 - 1, row - 1)])
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def curve_arc(name, center, radius, thickness, material, start=0.0, end=pi):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = thickness
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    count = 32
    spline.points.add(count)
    for index, point in enumerate(spline.points):
        angle = start + (end - start) * index / count
        point.co = (center[0] + radius * cos(angle), center[1], center[2] + radius * sin(angle), 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def window_bay(name, x, y, z, width, height, glass, frame, rotation_z=0.0):
    panel = cube(name + "-glass", (x, y, z), (width / 2, .055, height / 2), glass, .025)
    panel.rotation_euler.z = rotation_z
    for dx in (-width / 2, 0, width / 2):
        mullion = cube(name + "-mullion", (x + dx * cos(rotation_z), y + dx * sin(rotation_z), z), (.04, .05, height / 2 + .05), frame, .012)
        mullion.rotation_euler.z = rotation_z
    for dz in (-height / 2, 0, height / 2):
        rail = cube(name + "-rail", (x, y, z + dz), (width / 2 + .04, .05, .04), frame, .012)
        rail.rotation_euler.z = rotation_z


bpy.ops.wm.read_factory_settings(use_empty=True)

stone = mat("infusion-warm-limestone", (.76, .58, .43, 1), roughness=.58)
trim = mat("infusion-carved-stone", (.92, .77, .60, 1), roughness=.46)
base = mat("infusion-rusticated-base", (.43, .34, .27, 1), roughness=.76)
roof = mat("infusion-aged-copper-roof", (.40, .15, .105, 1), metallic=.58, roughness=.32)
roof_green = mat("infusion-patinated-copper", (.08, .31, .25, 1), metallic=.52, roughness=.34)
frame = mat("infusion-dark-window-frame", (.028, .085, .085, 1), metallic=.55, roughness=.24)
glass = mat("infusion-warm-glass", (.07, .17, .16, .34), roughness=.08, transmission=.76)
warm = mat("infusion-warm-interior", (.52, .15, .025, 1), roughness=.3, emission=(1, .27, .055, 1))
rose = mat("infusion-emblem-rose", (.48, .11, .09, 1), metallic=.18, roughness=.34)
leaf = mat("infusion-emblem-leaf", (.18, .38, .12, 1), roughness=.42)
cream = mat("infusion-chair-cream", (.72, .55, .39, 1), roughness=.62)

# Elliptical clinic massing with a central ceremonial hall.
cylinder("infusion-foundation", (0, 0, .42), 7.5, .84, base, scale=(1, .54, 1))
cylinder("infusion-clinic-body", (0, 0, 2.42), 7.1, 3.92, stone, scale=(1, .51, 1))
cube("infusion-central-hall", (0, .12, 2.95), (1.90, 3.45, 2.42), trim, .48)

# Rusticated lower base and stepped copper/patina roofs.
cylinder("infusion-base-course", (0, 0, 1.05), 7.18, .72, base, scale=(1, .515, 1))
cylinder("infusion-lower-roof", (0, .05, 4.48), 7.42, .54, roof, scale=(1, .525, 1))
cylinder("infusion-lower-roof-deck", (0, .10, 4.76), 6.85, .22, roof_green, scale=(1, .50, 1))
barrel("infusion-central-barrel", 4.02, 4.20, 5.18, 1.22, roof_green)

# Front glass infusion lounges with visible chairs and IV stands.
for side in (-1, 1):
    for index in range(5):
        x = side * (2.20 + index * .98)
        ellipse = max(.08, 1 - (x / 7.10) ** 2)
        y = -3.62 * sqrt(ellipse)
        slope = 3.62 * x / (7.10 * 7.10 * sqrt(ellipse))
        tangent = atan(slope)
        window_bay(f"infusion-window-{side}-{index}", x, y - .06, 2.72, .82, 1.96, glass, frame, tangent)
        cube("infusion-interior-glow", (x, y + .10, 2.72), (.27, .05, .74), warm, .02)
    for chair_index, x in enumerate((side * 3.2, side * 5.0)):
        ellipse = max(.08, 1 - (x / 7.10) ** 2)
        chair_y = -3.62 * sqrt(ellipse) + .36
        cube("infusion-recliner-seat", (x, chair_y, 2.05), (.38, .42, .18), cream, .10)
        back = cube("infusion-recliner-back", (x, chair_y + .16, 2.55), (.38, .13, .55), cream, .10)
        back.rotation_euler.x = -.18
        cube("infusion-iv-pole", (x + side * .52, chair_y, 2.62), (.025, .025, .72), frame, .01)
        cube("infusion-iv-bag", (x + side * .52, chair_y, 3.13), (.11, .035, .18), glass, .03)

# Entry portal and three curved-looking broad steps.
cube("infusion-entry-recess", (0, -3.83, 2.54), (1.28, .18, 1.48), frame, .30)
for x in (-.61, .61):
    cube("infusion-entry-door", (x, -4.04, 2.28), (.53, .06, 1.12), glass, .03)
for x in (-1.23, 0, 1.23):
    cube("infusion-entry-mullion", (x, -4.11, 2.54), (.055, .06, 1.42), frame, .018)
for x in (-1.50, 1.50):
    cube("infusion-entry-pillar", (x, -4.06, 2.60), (.18, .20, 1.60), trim, .05)
curve_arc("infusion-entry-arch", (0, -4.12, 3.44), 1.50, .16, trim)
for index, (width, depth, z) in enumerate(((2.20, .94, .72), (1.92, .66, .90), (1.65, .42, 1.08))):
    cube(f"infusion-entry-step-{index}", (0, -4.08 - depth / 2, z), (width, depth / 2, .11), trim, .08)

# Infusion-bag and botanical emblem from the cinematic poster.
cylinder("infusion-emblem-disc", (0, -4.05, 5.02), 1.20, .13, trim, rotation=(pi / 2, 0, 0))
cube("infusion-bag-body", (0, -4.20, 5.12), (.50, .08, .64), rose, .15)
curve_arc("infusion-bag-handle", (0, -4.20, 5.73), .28, .08, rose)
cube("infusion-bag-neck", (0, -4.20, 4.46), (.12, .08, .18), rose, .04)
cylinder("infusion-drop", (0, -4.31, 5.05), .15, .12, trim, vertices=48, rotation=(pi / 2, 0, 0))
for side in (-1, 1):
    for index in range(3):
        emblem_leaf = cube("infusion-leaf", (side * (.68 + index * .17), -4.22, 4.72 + index * .28), (.10, .045, .27), leaf, .08)
        emblem_leaf.rotation_euler.y = side * (.45 + index * .12)

for x in (-1.88, 1.88):
    cube("infusion-wall-lantern", (x, -4.08, 2.76), (.10, .10, .31), frame, .03)
    cube("infusion-wall-lantern-glow", (x, -4.19, 2.76), (.07, .06, .23), warm, .02)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

# Preview stage.
cylinder("preview-ground", (0, 0, .02), 11.5, .10, mat("preview-ground-material", (.06, .13, .10, 1), roughness=.8))
for location, energy, size, color in (((-10, -13, 14), 1800, 6, (1, .55, .32)), ((10, -3, 12), 1300, 6, (.34, .58, 1)), ((0, 8, 13), 1100, 5, (.78, .36, .40))):
    bpy.ops.object.light_add(type="AREA", location=location)
    light_obj = bpy.context.object
    light_obj.data.energy = energy
    light_obj.data.shape = "DISK"
    light_obj.data.size = size
    light_obj.data.color = color
    light_obj.rotation_euler = (-light_obj.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.camera_add(location=(17.5, -22.5, 14))
camera = bpy.context.object
camera.data.lens = 53
camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = camera
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 820
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("infusion-preview-world")
scene.world.color = (.018, .028, .055)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
