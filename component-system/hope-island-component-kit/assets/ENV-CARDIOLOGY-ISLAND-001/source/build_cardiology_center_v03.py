from math import atan, cos, pi, sin, sqrt
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "cardiology-center-blender-v03.glb"
PREVIEW = ROOT / "export" / "cardiology-center-blender-v03-preview.png"


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
    data.bevel_resolution = 4
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


def front_window(name, x, y, z, width, height, glass, frame, rotation_z=0.0):
    panel = cube(name + "-glass", (x, y, z), (width / 2, .055, height / 2), glass, .02)
    panel.rotation_euler.z = rotation_z
    for dx in (-width / 2, 0, width / 2):
        mullion = cube(name + "-mullion", (x + dx * cos(rotation_z), y + dx * sin(rotation_z), z), (.035, .05, height / 2 + .04), frame, .01)
        mullion.rotation_euler.z = rotation_z
    for dz in (-height / 2, height / 2):
        rail = cube(name + "-rail", (x, y, z + dz), (width / 2 + .04, .05, .035), frame, .01)
        rail.rotation_euler.z = rotation_z


bpy.ops.wm.read_factory_settings(use_empty=True)

limestone = mat("cardiology-warm-limestone", (.84, .69, .56, 1), roughness=.55)
trim = mat("cardiology-carved-stone", (.97, .82, .68, 1), roughness=.42)
base = mat("cardiology-rusticated-base", (.43, .35, .29, 1), roughness=.74)
burgundy = mat("cardiology-burgundy-roof", (.48, .085, .14, 1), metallic=.34, roughness=.35)
rose_metal = mat("cardiology-rose-trim", (.67, .27, .30, 1), metallic=.48, roughness=.28)
brass = mat("cardiology-brass", (.59, .37, .13, 1), metallic=.76, roughness=.24)
frame = mat("cardiology-window-frame", (.035, .07, .065, 1), metallic=.60, roughness=.22)
glass = mat("cardiology-warm-glass", (.24, .36, .33, .28), roughness=.10, transmission=.68, emission=(.20, .10, .045, 1))
warm = mat("cardiology-warm-interior", (.55, .16, .025, 1), roughness=.30, emission=(1, .30, .07, 1))
green = mat("cardiology-emblem-leaf", (.20, .40, .15, 1), roughness=.40)
machine = mat("cardiology-ultrasound-ceramic", (.78, .80, .75, 1), metallic=.10, roughness=.30)
screen = mat("cardiology-ultrasound-screen", (.04, .08, .09, 1), metallic=.20, roughness=.18, emission=(.08, .34, .42, 1))
bed = mat("cardiology-exam-bed", (.37, .53, .55, 1), roughness=.38)

# Symmetrical clinic shell and curved glazed wings.
cyl("cardiology-foundation", (0, 0, .42), 7.62, .84, base, scale=(1, .55, 1))
cyl("cardiology-clinic-body", (0, 0, 2.43), 7.18, 3.92, limestone, scale=(1, .52, 1))
cyl("cardiology-base-course", (0, 0, 1.02), 7.27, .66, base, scale=(1, .525, 1))
cyl("cardiology-roof-deck", (0, .08, 4.55), 7.46, .42, burgundy, scale=(1, .54, 1))
cyl("cardiology-roof-trim", (0, .08, 4.80), 7.54, .14, trim, scale=(1, .545, 1))

# Two low, wide roof lobes and a pronounced central notch create the poster heart silhouette.
for side in (-1, 1):
    sphere(f"cardiology-roof-lobe-{side}", (side * 2.78, .42, 5.18), (4.05, 2.55, .40), burgundy, rotation=(0, side * .025, side * .10))
    for index in range(6):
        rib = curve(
            f"cardiology-roof-rib-{side}-{index}",
            [(side * (.58 + index * .55), -2.02, 5.20), (side * (1.10 + index * .52), .15, 5.56), (side * (1.72 + index * .48), 2.20, 5.19)],
            .028,
            rose_metal,
        )
curve("cardiology-roof-center-notch", [(-.95, -.25, 5.32), (0, .52, 4.98), (.95, -.25, 5.32)], .10, trim)

# Heart-topped monumental central facade.
cube("cardiology-central-facade", (0, -3.70, 3.47), (2.10, .30, 2.54), trim, .34)
torus("cardiology-facade-arch", (0, -4.04, 4.66), 2.10, .18, trim, rotation=(pi / 2, 0, 0))

heart_points = [
    (0, -4.44, 4.35), (-1.15, -4.44, 5.16), (-1.00, -4.44, 5.88), (-.42, -4.44, 6.08),
    (0, -4.44, 5.60), (.42, -4.44, 6.08), (1.00, -4.44, 5.88), (1.15, -4.44, 5.16),
]
curve("cardiology-heart-emblem", heart_points, .14, rose_metal, cyclic=True)
ecg_points = [(-.82, -4.61, 5.25), (-.34, -4.61, 5.25), (-.18, -4.61, 5.62), (.06, -4.61, 4.82), (.32, -4.61, 5.48), (.48, -4.61, 5.25), (.84, -4.61, 5.25)]
curve("cardiology-ecg-emblem", ecg_points, .065, rose_metal)
for side in (-1, 1):
    curve(f"cardiology-emblem-branch-{side}", [(side * .48, -4.48, 4.48), (side * 1.05, -4.48, 4.30), (side * 1.56, -4.48, 4.52)], .05, green)
    for index in range(3):
        leaf = sphere(f"cardiology-emblem-leaf-{side}-{index}", (side * (.84 + index * .34), -4.49, 4.54 + index * .20), (.23, .06, .39), green, segments=24, rings=12)
        leaf.rotation_euler.y = side * (.42 + index * .10)

# Warm curved glazing; right bay reveals the ultrasound examination room.
for side in (-1, 1):
    for index in range(5):
        x = side * (2.46 + index * .92)
        ellipse = max(.08, 1 - (x / 7.18) ** 2)
        y = -3.72 * sqrt(ellipse)
        slope = 3.72 * x / (7.18 * 7.18 * sqrt(ellipse))
        tangent = atan(slope)
        front_window(f"cardiology-window-{side}-{index}", x, y - .10, 2.66, .78, 2.04, glass, frame, tangent)
        cube(f"cardiology-interior-glow-{side}-{index}", (x, y + .10, 2.65), (.25, .05, .76), warm, .02)

cube("cardiology-entry-recess", (0, -4.05, 2.42), (1.30, .20, 1.35), frame, .28)
for x in (-.62, .62):
    cube("cardiology-entry-door", (x, -4.27, 2.22), (.54, .06, 1.10), glass, .025)
for x in (-1.25, 0, 1.25):
    cube("cardiology-entry-mullion", (x, -4.34, 2.46), (.055, .055, 1.38), frame, .015)
for x in (-1.58, 1.58):
    cube("cardiology-entry-pillar", (x, -4.19, 2.60), (.17, .22, 1.55), trim, .05)
    cube("cardiology-wall-lantern", (x, -4.43, 2.72), (.11, .10, .31), frame, .03)
    cube("cardiology-lantern-glow", (x, -4.55, 2.72), (.07, .06, .23), warm, .02)
for index, (width, depth, z) in enumerate(((2.28, .98, .70), (1.98, .70, .88), (1.70, .43, 1.06))):
    cube(f"cardiology-step-{index}", (0, -4.20 - depth / 2, z), (width, depth / 2, .11), trim, .07)

# Paired curved-looking accessible ramps, with separate handrails and posts.
for side in (-1, 1):
    ramp = cube(f"cardiology-accessible-ramp-{side}", (side * 3.40, -4.78, .78), (1.92, .62, .10), trim, .06)
    ramp.rotation_euler.y = -side * .13
    for rail_x in (side * 1.58, side * 5.20):
        for index in range(5):
            cube(f"cardiology-ramp-post-{side}", (rail_x, -5.28 + index * .32, 1.18), (.025, .025, .40), brass, .008)
        cube(f"cardiology-ramp-rail-{side}", (rail_x, -4.64, 1.52), (.025, .84, .025), brass, .008)

# Independent ultrasound equipment and examination furniture.
cube("cardiology-exam-bed", (3.25, -3.30, 2.04), (1.12, .34, .13), bed, .12)
cube("cardiology-bed-pedestal", (3.30, -3.05, 1.66), (.34, .28, .34), machine, .08)
cube("cardiology-ultrasound-cart", (4.78, -3.10, 1.85), (.48, .35, .52), machine, .09)
cube("cardiology-ultrasound-screen", (4.72, -3.42, 2.70), (.48, .08, .36), screen, .06, rotation=(-.12, 0, 0))
cube("cardiology-ultrasound-console", (4.40, -3.40, 2.18), (.48, .30, .10), machine, .06, rotation=(-.20, 0, 0))
for x in (4.48, 5.08):
    cyl("cardiology-cart-wheel", (x, -3.18, 1.30), .11, .08, frame, vertices=24, rotation=(pi / 2, 0, 0))
curve("cardiology-probe-cable", [(4.48, -3.46, 2.18), (4.22, -3.48, 1.86), (3.92, -3.46, 2.05)], .025, frame)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

# Cinematic verification render; preview ground is added only after export.
cyl("preview-ground", (0, 0, .02), 11.7, .10, mat("preview-ground-material", (.055, .105, .09, 1), roughness=.82))
for location, energy, size, color in (((-10, -13, 14), 1850, 6, (1, .58, .34)), ((11, -3, 12), 1350, 6, (.38, .58, 1)), ((0, 8, 13), 1100, 5, (.76, .40, .38))):
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
scene.world = bpy.data.worlds.new("cardiology-preview-world")
scene.world.color = (.018, .028, .055)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
