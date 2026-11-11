from math import cos, pi, sin
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "radiation-oncology-center-blender-v02.glb"
PREVIEW = ROOT / "export" / "radiation-oncology-center-blender-v02-preview.png"


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


def torus(name, location, major_radius, minor_radius, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius, major_segments=64, minor_segments=12, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def curve(name, points, thickness, material):
    data = bpy.data.curves.new(name + "Curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = thickness
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def front_window(name, x, z, width, height, glass, frame, y=-3.72):
    cube(name + "-glass", (x, y, z), (width / 2, .055, height / 2), glass, .02)
    for dx in (-width / 2, 0, width / 2):
        cube(name + "-mullion", (x + dx, y - .07, z), (.035, .05, height / 2 + .04), frame, .01)
    for dz in (-height / 2, height / 2):
        cube(name + "-rail", (x, y - .07, z + dz), (width / 2 + .04, .05, .035), frame, .01)


bpy.ops.wm.read_factory_settings(use_empty=True)

limestone = mat("radiation-warm-limestone", (.82, .68, .55, 1), roughness=.56)
trim = mat("radiation-pale-carved-stone", (.96, .82, .68, 1), roughness=.42)
base = mat("radiation-rusticated-base", (.42, .35, .29, 1), roughness=.74)
sage = mat("radiation-sage-roof", (.27, .38, .27, 1), metallic=.24, roughness=.40)
sage_dark = mat("radiation-roof-rib", (.16, .25, .18, 1), metallic=.40, roughness=.32)
rose = mat("radiation-target-rose", (.66, .27, .29, 1), metallic=.18, roughness=.35)
brass = mat("radiation-brass", (.58, .35, .12, 1), metallic=.76, roughness=.24)
frame = mat("radiation-window-frame", (.035, .07, .065, 1), metallic=.60, roughness=.22)
glass = mat("radiation-warm-glass", (.24, .38, .35, .28), roughness=.10, transmission=.68, emission=(.20, .10, .045, 1))
warm = mat("radiation-warm-interior", (.55, .16, .025, 1), roughness=.30, emission=(1, .30, .07, 1))
green = mat("radiation-emblem-leaf", (.20, .39, .15, 1), roughness=.40)
machine = mat("radiation-machine-ceramic", (.82, .84, .78, 1), metallic=.10, roughness=.30)
machine_dark = mat("radiation-machine-joint", (.13, .18, .18, 1), metallic=.58, roughness=.25)
bed = mat("radiation-treatment-bed", (.32, .53, .55, 1), roughness=.38)

# Elliptical clinic body, stepped roof and monumental central arch.
cyl("radiation-foundation", (0, 0, .42), 7.55, .84, base, scale=(1, .55, 1))
cyl("radiation-clinic-body", (0, 0, 2.45), 7.12, 3.95, limestone, scale=(1, .52, 1))
cyl("radiation-base-course", (0, 0, 1.02), 7.22, .66, base, scale=(1, .525, 1))
cyl("radiation-lower-roof", (0, .10, 4.56), 7.42, .42, sage, scale=(1, .54, 1))
cyl("radiation-lower-roof-trim", (0, .10, 4.80), 7.50, .14, brass, scale=(1, .545, 1))
cyl("radiation-upper-roof", (0, .24, 5.15), 5.56, .58, sage, scale=(1, .57, 1))
cyl("radiation-upper-roof-trim", (0, .24, 5.47), 5.66, .13, trim, scale=(1, .58, 1))

# Barrel vault assembled from overlapping ribs to preserve the reference silhouette.
for index, y in enumerate((-2.60, -1.95, -1.30, -.65, 0, .65, 1.30, 1.95, 2.60)):
    sphere(f"radiation-barrel-vault-{index}", (0, y, 5.38), (2.62, .43, 1.58), sage)
    if index in (0, 2, 4, 6, 8):
        torus(f"radiation-vault-rib-{index}", (0, y - .03, 5.38), 2.62, .055, sage_dark, rotation=(pi / 2, 0, 0))

cube("radiation-central-facade", (0, -3.68, 3.48), (2.05, .30, 2.52), trim, .34)
torus("radiation-facade-arch", (0, -4.02, 4.66), 2.06, .18, trim, rotation=(pi / 2, 0, 0))

# Curved glazing and visible room lighting.
for side in (-1, 1):
    for index in range(5):
        x = side * (2.42 + index * .92)
        front_window(f"radiation-window-{side}-{index}", x, 2.65, .78, 2.02, glass, frame)
        cube(f"radiation-interior-glow-{side}-{index}", (x, -3.48, 2.64), (.25, .05, .76), warm, .02)

# Recessed entrance, glass doors, lanterns and accessible approach.
cube("radiation-entry-recess", (0, -4.03, 2.42), (1.28, .20, 1.35), frame, .28)
for x in (-.61, .61):
    cube("radiation-entry-door", (x, -4.25, 2.22), (.53, .06, 1.10), glass, .025)
for x in (-1.24, 0, 1.24):
    cube("radiation-entry-mullion", (x, -4.32, 2.46), (.055, .055, 1.38), frame, .015)
for x in (-1.55, 1.55):
    cube("radiation-entry-pillar", (x, -4.18, 2.60), (.17, .22, 1.55), trim, .05)
    cube("radiation-wall-lantern", (x, -4.42, 2.72), (.11, .10, .31), frame, .03)
    cube("radiation-lantern-glow", (x, -4.54, 2.72), (.07, .06, .23), warm, .02)
for index, (width, depth, z) in enumerate(((2.25, .96, .70), (1.96, .68, .88), (1.68, .42, 1.06))):
    cube(f"radiation-step-{index}", (0, -4.18 - depth / 2, z), (width, depth / 2, .11), trim, .07)
ramp = cube("radiation-accessible-ramp", (3.28, -4.76, .78), (1.82, .62, .10), trim, .06)
ramp.rotation_euler.y = .13
for rail_x in (1.55, 5.02):
    for index in range(5):
        cube("radiation-ramp-post", (rail_x, -5.26 + index * .32, 1.18), (.025, .025, .40), brass, .008)
    cube("radiation-ramp-rail", (rail_x, -4.62, 1.52), (.025, .84, .025), brass, .008)

# Target-and-leaf identity mark, built as independent editable pieces.
for index, (radius, material) in enumerate(((1.22, trim), (.94, rose), (.64, trim), (.34, rose))):
    cyl(f"radiation-target-{radius}", (0, -4.38 - index * .075, 5.18), radius, .10, material, vertices=64, rotation=(pi / 2, 0, 0))
for side in (-1, 1):
    curve(f"radiation-emblem-branch-{side}", [(side * .30, -4.49, 4.32), (side * .82, -4.49, 4.12), (side * 1.46, -4.49, 4.26)], .055, green)
    for index in range(3):
        leaf = sphere(f"radiation-emblem-leaf-{side}-{index}", (side * (.66 + index * .38), -4.49, 4.30 + index * .18), (.24, .06, .40), green, rotation=(0, side * (.42 + index * .10), 0), segments=24, rings=12)
        leaf.rotation_euler.y = side * (.42 + index * .10)

# A complete radiotherapy gantry and patient table behind the right glazing.
torus("radiation-gantry-outer", (4.34, -3.00, 2.58), 1.02, .34, machine, rotation=(pi / 2, 0, 0))
torus("radiation-gantry-inner", (4.34, -3.20, 2.58), .68, .08, machine_dark, rotation=(pi / 2, 0, 0))
cube("radiation-gantry-base", (4.34, -3.00, 1.52), (.62, .48, .38), machine, .10)
cube("radiation-patient-table", (3.05, -3.34, 2.05), (1.16, .34, .13), bed, .12)
cube("radiation-table-pedestal", (3.25, -3.08, 1.66), (.34, .28, .34), machine, .08)
cyl("radiation-collimator", (4.34, -3.39, 3.28), .22, .40, machine_dark, rotation=(pi / 2, 0, 0))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

# Cinematic verification render; the ground is intentionally excluded from the GLB.
cyl("preview-ground", (0, 0, .02), 11.5, .10, mat("preview-ground-material", (.055, .105, .09, 1), roughness=.82))
for location, energy, size, color in (((-10, -13, 14), 1800, 6, (1, .58, .34)), ((11, -3, 12), 1300, 6, (.38, .58, 1)), ((0, 8, 13), 1050, 5, (.76, .40, .38))):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (-light.location).to_track_quat("-Z", "Y").to_euler()
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
scene.world = bpy.data.worlds.new("radiation-preview-world")
scene.world.color = (.018, .028, .055)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
