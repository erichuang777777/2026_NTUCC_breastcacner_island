from math import cos, pi, sin
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "imaging-pavilion-blender-v02.glb"
PREVIEW = ROOT / "export" / "imaging-pavilion-blender-v02-preview.png"


def material(name, color, metallic=0.0, roughness=0.45, transmission=0.0, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission
        bsdf.inputs["IOR"].default_value = 1.45
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 1.8
    return mat


def cube(name, location, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("architectural-edge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    obj.data.materials.append(mat)
    return obj


def cylinder(name, location, radius, depth, mat, vertices=64, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def curved_box(name, center, width, depth, height, mat, bevel=0.28):
    return cube(name, center, (width / 2, depth / 2, height / 2), mat, bevel)


def barrel(name, width, depth, spring_z, radius, mat, segments=40):
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
    obj.data.materials.append(mat)
    return obj


def arch_curve(name, center, radius, bevel, mat, start=0.0, end=pi):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = bevel
    curve.bevel_resolution = 3
    spline = curve.splines.new("POLY")
    count = 32
    spline.points.add(count)
    for index, point in enumerate(spline.points):
        angle = start + (end - start) * index / count
        point.co = (center[0] + radius * cos(angle), center[1], center[2] + radius * sin(angle), 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def front_window(name, x, z, width, height, glass, frame):
    cube(name + "-glass", (x, -3.76, z), (width / 2, 0.055, height / 2), glass, 0.025)
    for dx in (-width / 2, 0, width / 2):
        cube(name + "-mullion", (x + dx, -3.84, z), (0.045, 0.055, height / 2 + 0.04), frame, 0.015)
    for dz in (-height / 2, 0, height / 2):
        cube(name + "-rail", (x, -3.84, z + dz), (width / 2 + 0.04, 0.055, 0.04), frame, 0.015)


bpy.ops.wm.read_factory_settings(use_empty=True)

limestone = material("imaging-warm-limestone", (0.72, 0.55, 0.39, 1), roughness=0.58)
trim = material("imaging-carved-stone", (0.91, 0.75, 0.56, 1), roughness=0.46)
base = material("imaging-rusticated-base", (0.38, 0.31, 0.26, 1), roughness=0.76)
roof = material("imaging-weathered-teal-roof", (0.045, 0.28, 0.31, 1), metallic=0.48, roughness=0.31)
roof_rib = material("imaging-roof-ribs", (0.15, 0.38, 0.39, 1), metallic=0.64, roughness=0.26)
frame = material("imaging-dark-window-frame", (0.025, 0.10, 0.11, 1), metallic=0.55, roughness=0.24)
glass = material("imaging-architectural-glass", (0.055, 0.17, 0.20, 0.34), roughness=0.08, transmission=0.76)
warm = material("imaging-warm-interior", (0.50, 0.16, 0.035, 1), roughness=0.30, emission=(1.0, 0.30, 0.075, 1))
blue = material("imaging-emblem-blue", (0.10, 0.30, 0.40, 1), metallic=0.32, roughness=0.30)
green = material("imaging-emblem-leaf", (0.12, 0.38, 0.16, 1), roughness=0.40)

# Foundation and three-part massing from the cinematic key art.
curved_box("imaging-foundation", (0, 0, 0.42), 14.8, 7.9, 0.84, base, 0.20)
curved_box("imaging-left-wing", (-4.25, 0.05, 2.25), 6.2, 7.0, 3.65, limestone, 0.58)
curved_box("imaging-right-wing", (4.25, 0.05, 2.25), 6.2, 7.0, 3.65, limestone, 0.58)
curved_box("imaging-central-hall", (0, 0.18, 3.05), 3.65, 7.45, 5.25, trim, 0.36)

# Continuous stone belts and deep cornices provide readable scale at island view.
for x in (-4.25, 4.25):
    cube("imaging-base-course", (x, -3.58, 1.02), (3.15, 0.17, 0.48), base, 0.06)
    cube("imaging-belt-course", (x, -3.72, 1.62), (3.25, 0.14, 0.10), trim, 0.04)
    cube("imaging-cornice", (x, -3.78, 4.10), (3.30, 0.18, 0.16), trim, 0.05)

# Wing roofs: layered, low curved forms rather than a single melted shell.
for x in (-4.25, 4.25):
    curved_box("imaging-lower-roof", (x, 0.08, 4.38), 6.9, 7.35, 0.52, roof, 0.58)
    curved_box("imaging-upper-roof", (x, 0.38, 4.78), 5.95, 6.38, 0.42, roof, 0.52)
    for seam in range(11):
        seam_x = x - 2.70 + seam * 0.54
        cube("imaging-wing-roof-seam", (seam_x, -2.72, 4.83), (0.025, 0.80, 0.06), roof_rib, 0.012)

# Central MRI-like barrel roof and structural ribs.
barrel("imaging-central-barrel", 3.9, 7.75, 5.55, 1.95, roof)
for y in [(-3.45 + index * 0.49) for index in range(15)]:
    arch_curve("imaging-central-roof-rib", (0, y, 5.55), 1.98, 0.035, roof_rib)

# Warm glass bays on both wings.
for side in (-1, 1):
    for index in range(5):
        x = side * (2.15 + index * 1.02)
        front_window(f"imaging-front-window-{side}-{index}", x, 2.72, 0.86, 1.92, glass, frame)
        cube("imaging-interior-light", (x, -3.53, 2.70), (0.29, 0.05, 0.73), warm, 0.02)

# Deep central entry, double glass doors, stone portal and steps.
cube("imaging-entry-recess", (0, -3.79, 2.50), (1.25, 0.18, 1.48), frame, 0.30)
for x in (-0.60, 0.60):
    cube("imaging-entry-door", (x, -4.00, 2.24), (0.52, 0.06, 1.12), glass, 0.03)
for x in (-1.22, 0, 1.22):
    cube("imaging-entry-mullion", (x, -4.08, 2.50), (0.055, 0.06, 1.42), frame, 0.018)
for x in (-1.48, 1.48):
    cube("imaging-entry-pillar", (x, -4.02, 2.54), (0.18, 0.20, 1.58), trim, 0.05)
arch_curve("imaging-entry-arch", (0, -4.08, 3.40), 1.48, 0.16, trim)
for index, (width, depth, z) in enumerate(((2.15, 0.90, 0.72), (1.88, 0.64, 0.90), (1.62, 0.40, 1.07))):
    cube(f"imaging-entry-step-{index}", (0, -4.05 - depth / 2, z), (width, depth / 2, 0.11), trim, 0.07)

# MRI scanner relief and radiology-wave emblem from the poster.
cylinder("imaging-emblem-disc", (0, -4.02, 4.98), 1.14, 0.13, trim, rotation=(pi / 2, 0, 0))
cylinder("imaging-mri-ring", (0, -4.14, 4.92), 0.51, 0.16, blue, rotation=(pi / 2, 0, 0))
cylinder("imaging-mri-bore", (0, -4.24, 4.92), 0.26, 0.17, frame, rotation=(pi / 2, 0, 0))
cube("imaging-mri-bed", (0, -4.40, 4.48), (0.72, 0.12, 0.13), trim, 0.05)
for radius in (0.43, 0.66, 0.89):
    arch_curve("imaging-signal-wave", (0, -4.16, 5.62), radius, 0.055, blue, start=pi * 0.18, end=pi * 0.82)
for side in (-1, 1):
    for index in range(3):
        leaf = cube("imaging-emblem-leaf", (side * (0.69 + index * 0.16), -4.17, 4.85 + index * 0.30), (0.10, 0.045, 0.26), green, 0.08)
        leaf.rotation_euler.y = side * (0.45 + index * 0.12)

# Exterior wall lanterns and interior lighting.
for x in (-1.85, 1.85):
    cube("imaging-wall-lantern-frame", (x, -4.04, 2.70), (0.10, 0.10, 0.31), frame, 0.03)
    cube("imaging-wall-lantern-glow", (x, -4.15, 2.70), (0.07, 0.06, 0.23), warm, 0.02)
for x in (-5.4, -3.2, 3.2, 5.4):
    bpy.ops.object.light_add(type="POINT", location=(x, -2.8, 3.0))
    light = bpy.context.object
    light.name = "imaging-interior-point-light"
    light.data.energy = 68
    light.data.color = (1.0, 0.38, 0.13)
    light.data.shadow_soft_size = 0.75

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

# Preview-only environment.
floor = cylinder("preview-island", (0, 0, 0.04), 11.5, 0.12, material("preview-ground", (0.08, 0.15, 0.11, 1), roughness=0.8), vertices=96)
for location, energy, size, color in (
    ((-10, -13, 14), 1800, 6, (1.0, 0.57, 0.34)),
    ((10, -3, 12), 1300, 6, (0.35, 0.58, 1.0)),
    ((0, 8, 13), 1100, 5, (0.78, 0.38, 0.42)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    light.rotation_euler = ((0, 0, 0))
    direction = -light.location
    light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(17.5, -22.5, 14.0))
camera = bpy.context.object
camera.data.lens = 53
camera.data.sensor_width = 36
camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = camera
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 820
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("imaging-preview-world")
scene.world.color = (0.018, 0.028, 0.055)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
