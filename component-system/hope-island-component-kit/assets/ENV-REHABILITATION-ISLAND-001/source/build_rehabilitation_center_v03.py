from math import atan2, cos, pi, sin
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "rehabilitation-center-blender-v03.glb"
PREVIEW = ROOT / "export" / "rehabilitation-center-blender-v03-preview.png"


def mat(name, color, metallic=0, roughness=.45, transmission=0, emission=None):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Alpha"].default_value = color[3]
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if transmission:
        shader.inputs["Transmission Weight"].default_value = transmission
        shader.inputs["IOR"].default_value = 1.45
    if emission:
        shader.inputs["Emission Color"].default_value = emission
        shader.inputs["Emission Strength"].default_value = 1.7
    if color[3] < 1:
        material.surface_render_method = "DITHERED"
        material.use_transparency_overlap = False
    return material


def cube(name, location, scale, material, bevel=0, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("architectural-edge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    obj.data.materials.append(material)
    return obj


def cyl(name, location, radius, depth, material, scale=(1, 1, 1), vertices=72, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def sphere(name, location, scale, material, rotation=(0, 0, 0), segments=40, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def torus(name, location, major_radius, minor_radius, material, rotation=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, major_segments=64, minor_segments=12, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj


def curve(name, points, thickness, material, cyclic=False):
    data = bpy.data.curves.new(name + "Curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = thickness
    data.bevel_resolution = 2
    data.resolution_u = 2
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    spline.use_cyclic_u = cyclic
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def curved_window(name, x, y, z, width, height, angle, glass, frame):
    rotation = (0, 0, angle)
    cube(name + "-glass", (x, y, z), (width / 2, .055, height / 2), glass, .02, rotation)
    nx, ny = -sin(angle), cos(angle)
    tx, ty = cos(angle), sin(angle)
    for offset in (-width / 2, width / 2):
        cube(name + "-mullion", (x + tx * offset + nx * .07, y + ty * offset + ny * .07, z), (.035, .05, height / 2 + .04), frame, .01, rotation)
    for dz in (-height / 2, height / 2):
        cube(name + "-rail", (x + nx * .07, y + ny * .07, z + dz), (width / 2 + .04, .05, .035), frame, .01, rotation)


def barrel_roof(name, center, length, radius, rise, material, ribs_material):
    cx, cy, cz = center
    segments_x, segments_arc = 12, 24
    vertices, faces = [], []
    for ix in range(segments_x + 1):
        x = cx - length / 2 + length * ix / segments_x
        for ia in range(segments_arc + 1):
            theta = pi * ia / segments_arc
            y = cy + radius * cos(theta)
            z = cz + rise * sin(theta)
            vertices.append((x, y, z))
    stride = segments_arc + 1
    for ix in range(segments_x):
        for ia in range(segments_arc):
            a = ix * stride + ia
            faces.append((a, a + stride, a + stride + 1, a + 1))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    solidify = obj.modifiers.new("standing-seam-shell", "SOLIDIFY")
    solidify.thickness = .12
    bevel = obj.modifiers.new("soft-roof-edge", "BEVEL")
    bevel.width = .05
    bevel.segments = 2
    for ix in range(segments_x + 1):
        x = cx - length / 2 + length * ix / segments_x
        points = []
        for ia in range(segments_arc + 1):
            theta = pi * ia / segments_arc
            points.append((x, cy + radius * cos(theta), cz + rise * sin(theta) + .08))
        curve(f"{name}-seam-{ix}", points, .026, ribs_material)
    return obj


bpy.ops.wm.read_factory_settings(use_empty=True)

limestone = mat("rehab-warm-limestone", (.82, .68, .55, 1), roughness=.56)
trim = mat("rehab-carved-stone", (.95, .80, .65, 1), roughness=.43)
base = mat("rehab-rusticated-base", (.42, .35, .29, 1), roughness=.74)
patina = mat("rehab-patina-roof", (.12, .47, .48, 1), metallic=.50, roughness=.31)
patina_dark = mat("rehab-patina-rib", (.06, .28, .31, 1), metallic=.62, roughness=.25)
copper = mat("rehab-copper-trim", (.61, .34, .18, 1), metallic=.72, roughness=.25)
frame = mat("rehab-window-frame", (.035, .07, .065, 1), metallic=.60, roughness=.22)
glass = mat("rehab-warm-glass", (.20, .37, .36, .26), roughness=.09, transmission=.70, emission=(.18, .10, .045, 1))
warm = mat("rehab-warm-interior", (.55, .16, .025, 1), roughness=.30, emission=(1, .30, .07, 1))
green = mat("rehab-emblem-leaf", (.12, .43, .35, 1), roughness=.36)
bronze = mat("rehab-emblem-bronze", (.55, .32, .16, 1), metallic=.58, roughness=.28)
blue = mat("rehab-therapy-upholstery", (.26, .47, .53, 1), roughness=.39)
track = mat("rehab-indoor-track", (.22, .46, .46, 1), roughness=.58)
band_red = mat("rehab-band-red", (.72, .16, .18, 1), roughness=.38)
band_yellow = mat("rehab-band-yellow", (.86, .58, .08, 1), roughness=.38)
band_blue = mat("rehab-band-blue", (.12, .36, .68, 1), roughness=.38)

# Poster-matched composition: central barrel hall, low left therapy wing and a broad glazed gait pavilion.
cyl("rehab-foundation", (0, 0, .42), 7.72, .84, base, scale=(1.05, .56, 1))
cube("rehab-central-hall", (-.45, .18, 3.22), (2.18, 3.32, 2.72), limestone, .28)
cyl("rehab-left-treatment-wing", (-4.42, .35, 2.30), 3.15, 3.55, limestone, scale=(1.06, .72, 1))
cyl("rehab-right-training-wing", (3.55, .15, 2.22), 4.45, 3.50, limestone, scale=(1.10, .76, 1))
cyl("rehab-base-course", (0, 0, 1.02), 7.35, .66, base, scale=(1.08, .54, 1))
barrel_roof("rehab-central-barrel-roof", (-.45, .18, 5.62), 4.70, 3.48, 1.18, patina, patina_dark)
barrel_roof("rehab-left-barrel-roof", (-4.42, .38, 4.22), 4.95, 2.35, .70, patina, patina_dark)
barrel_roof("rehab-training-barrel-roof", (3.55, .18, 4.36), 7.70, 2.78, .82, patina, patina_dark)

# Monumental central facade and smaller copper entry canopy.
cube("rehab-central-facade", (-.45, -3.35, 3.55), (2.18, .28, 2.60), trim, .24)
curve("rehab-central-arch", [(-2.55, -3.68, 4.78), (-.45, -3.72, 6.10), (1.65, -3.68, 4.78)], .16, trim)
barrel_roof("rehab-entry-canopy", (-.45, -3.92, 3.56), 3.48, .78, .32, patina, copper)

# Dynamic movement emblem: human figure with three rising leaves.
sphere("rehab-emblem-head", (-.45, -3.75, 5.48), (.23, .07, .23), bronze, segments=32, rings=16)
curve("rehab-emblem-body", [(-.45, -3.78, 5.18), (-.63, -3.78, 4.78), (-.45, -3.78, 4.40)], .11, bronze)
curve("rehab-emblem-arm-left", [(-.45, -3.78, 5.05), (-1.10, -3.78, 5.22), (-1.52, -3.78, 5.55)], .08, bronze)
curve("rehab-emblem-arm-right", [(-.45, -3.78, 5.05), (.15, -3.78, 5.30), (.58, -3.78, 5.72)], .08, bronze)
curve("rehab-emblem-leg", [(-.45, -3.78, 4.50), (-.05, -3.78, 4.15)], .09, bronze)
for index in range(3):
    leaf = sphere(f"rehab-emblem-leaf-{index}", (.03 + index * .28, -3.80, 4.60 + index * .38), (.18, .06, .46), green, segments=24, rings=12)
    leaf.rotation_euler.y = .52 + index * .12

# Windows follow each elliptical facade instead of floating in a straight line.
for index in range(5):
    theta = .48 + index * .52
    x = -4.42 + 3.30 * cos(theta)
    y = .35 - 2.38 * sin(theta)
    angle = atan2(-2.38 * cos(theta), -3.30 * sin(theta))
    curved_window(f"rehab-left-window-{index}", x, y, 2.48, .72, 2.05, angle, glass, frame)
for index in range(11):
    theta = .34 + index * .245
    x = 3.55 + 4.90 * cos(theta)
    y = .15 - 3.44 * sin(theta)
    angle = atan2(-3.44 * cos(theta), -4.90 * sin(theta))
    curved_window(f"rehab-training-window-{index}", x, y, 2.55, .73, 2.38, angle, glass, frame)

cube("rehab-entry-recess", (-.45, -3.69, 2.35), (1.32, .20, 1.40), frame, .20)
for x in (-1.09, .19):
    cube("rehab-entry-door", (x, -3.91, 2.18), (.55, .06, 1.12), glass, .025)
for x in (-1.71, -.45, .81):
    cube("rehab-entry-mullion", (x, -3.98, 2.44), (.055, .055, 1.42), frame, .015)
for x in (-2.07, 1.17):
    cube("rehab-entry-pillar", (x, -3.85, 2.58), (.17, .22, 1.58), trim, .05)
    cube("rehab-wall-lantern", (x, -4.09, 2.70), (.11, .10, .31), frame, .03)
    cube("rehab-lantern-glow", (x, -4.21, 2.70), (.07, .06, .23), warm, .02)
for index, (width, depth, z) in enumerate(((2.30, .98, .70), (2.00, .70, .88), (1.72, .43, 1.06))):
    cube(f"rehab-step-{index}", (-.45, -3.84 - depth / 2, z), (width, depth / 2, .11), trim, .07)

# Paired accessible ramps and stainless handrails.
for side in (-1, 1):
    ramp = cube(f"rehab-accessible-ramp-{side}", (side * 3.48, -4.80, .78), (1.98, .62, .10), trim, .06)
    ramp.rotation_euler.y = -side * .13
    for rail_x in (side * 1.62, side * 5.35):
        for index in range(5):
            cube(f"rehab-ramp-post-{side}", (rail_x, -5.30 + index * .32, 1.18), (.025, .025, .40), copper, .008)
        cube(f"rehab-ramp-rail-{side}", (rail_x, -4.66, 1.52), (.025, .84, .025), copper, .008)

# Visible clinical rehabilitation equipment behind the right glass.
for index in range(3):
    x = 2.70 + index * 1.25
    cube(f"rehab-treatment-table-{index}", (x, -3.26, 1.92), (.52, .31, .12), blue, .10)
    cube(f"rehab-table-pedestal-{index}", (x, -3.10, 1.55), (.22, .22, .32), trim, .06)
for rail_x in (2.40, 4.20):
    cube("rehab-parallel-bar", (rail_x, -3.18, 2.12), (.035, 1.02, .035), frame, .01)
    for y in (-3.85, -3.20, -2.55):
        cube("rehab-parallel-post", (rail_x, y, 1.72), (.035, .035, .40), frame, .01)
cube("rehab-indoor-track", (4.55, -2.78, 1.30), (2.05, .38, .025), track, .08)
cube("rehab-band-rack", (5.78, -3.06, 2.42), (.12, .10, .88), frame, .04)
for index, material in enumerate((band_red, band_yellow, band_blue, green)):
    curve(f"rehab-resistance-band-{index}", [(5.72 + index * .08, -3.20, 2.80), (5.50 + index * .08, -3.24, 2.18)], .035, material)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

cyl("preview-ground", (0, 0, .02), 12.0, .10, mat("preview-ground-material", (.055, .105, .09, 1), roughness=.82))
for location, energy, size, color in (((-10, -13, 14), 1850, 6, (1, .58, .34)), ((11, -3, 12), 1350, 6, (.38, .58, 1)), ((0, 8, 13), 1100, 5, (.76, .40, .38))):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (-light.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.camera_add(location=(18.5, -23.5, 14.5))
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
scene.world = bpy.data.worlds.new("rehab-preview-world")
scene.world.color = (.018, .028, .055)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
