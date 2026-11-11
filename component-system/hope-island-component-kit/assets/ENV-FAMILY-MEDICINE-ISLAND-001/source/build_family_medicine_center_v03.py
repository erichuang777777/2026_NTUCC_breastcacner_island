from math import atan, cos, pi, sin, sqrt
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "family-medicine-center-blender-v03.glb"
PREVIEW = ROOT / "export" / "family-medicine-center-blender-v03-preview.png"


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

limestone = mat("family-warm-limestone", (.84, .70, .57, 1), roughness=.55)
trim = mat("family-carved-stone", (.97, .83, .69, 1), roughness=.42)
base = mat("family-rusticated-base", (.43, .35, .29, 1), roughness=.74)
sage = mat("family-sage-roof", (.28, .40, .28, 1), metallic=.24, roughness=.39)
sage_light = mat("family-sage-highlight", (.42, .53, .37, 1), metallic=.18, roughness=.38)
copper = mat("family-copper-trim", (.67, .34, .25, 1), metallic=.62, roughness=.27)
brass = mat("family-brass", (.59, .37, .13, 1), metallic=.76, roughness=.24)
frame = mat("family-window-frame", (.035, .07, .065, 1), metallic=.60, roughness=.22)
glass = mat("family-warm-glass", (.24, .36, .33, .28), roughness=.10, transmission=.68, emission=(.20, .10, .045, 1))
dome_glass = mat("family-dome-glass", (.22, .39, .40, .24), roughness=.08, transmission=.74, emission=(.12, .16, .12, 1))
warm = mat("family-warm-interior", (.55, .16, .025, 1), roughness=.30, emission=(1, .30, .07, 1))
green = mat("family-emblem-leaf", (.24, .43, .16, 1), roughness=.40)
rose = mat("family-care-hands", (.73, .35, .30, 1), metallic=.20, roughness=.34)
cream = mat("family-furniture-cream", (.75, .68, .55, 1), roughness=.42)
monitor = mat("family-vitals-monitor", (.03, .08, .08, 1), metallic=.20, roughness=.18, emission=(.05, .42, .25, 1))

# Rounded holistic-care clinic shell.
cyl("family-foundation", (0, 0, .42), 7.62, .84, base, scale=(1, .55, 1))
cyl("family-clinic-body", (0, 0, 2.43), 7.18, 3.92, limestone, scale=(1, .52, 1))
cyl("family-base-course", (0, 0, 1.02), 7.27, .66, base, scale=(1, .525, 1))
cyl("family-lower-roof", (0, .08, 4.54), 7.48, .42, sage, scale=(1, .54, 1))
cyl("family-lower-roof-trim", (0, .08, 4.79), 7.56, .14, trim, scale=(1, .545, 1))

# Flowing raised roof terraces, all independent for material and silhouette control.
for side in (-1, 1):
    sphere(f"family-roof-wing-{side}", (side * 3.34, .25, 5.05), (3.62, 2.48, .30), sage)
    torus(f"family-roof-wing-rim-{side}", (side * 3.28, .08, 5.08), 2.78, .075, trim, scale=(1.20, .78, .22))
    sphere(f"family-roof-terrace-{side}", (side * 2.28, .82, 5.28), (2.72, 2.02, .25), sage_light)
    torus(f"family-terrace-rim-{side}", (side * 2.28, .68, 5.30), 2.10, .060, trim, scale=(1.22, .80, .20))

# Central low glass dome and structural meridians.
sphere("family-glass-dome", (0, .62, 5.52), (2.62, 1.92, .64), dome_glass, segments=64, rings=32)
torus("family-dome-base-ring", (0, .62, 5.30), 2.55, .10, trim, scale=(1, .74, .28))
for index in range(9):
    angle = -pi / 2 + index * pi / 8
    curve(
        f"family-dome-meridian-{index}",
        [(-2.50 * cos(angle), .62 - 1.82 * sin(angle), 5.32), (0, .62, 6.14), (2.50 * cos(angle), .62 + 1.82 * sin(angle), 5.32)],
        .028,
        frame,
    )
for radius, z in ((2.28, 5.50), (1.68, 5.78)):
    torus(f"family-dome-latitude-{radius}", (0, .62, z), radius, .028, frame, scale=(1, .74, .20))

# Side oval skylights reveal herb gardens below.
for side in (-1, 1):
    torus(f"family-side-skylight-rim-{side}", (side * 4.62, .12, 5.10), 1.05, .10, trim, scale=(1.48, .72, .25))
    sphere(f"family-side-skylight-glass-{side}", (side * 4.62, .12, 5.08), (1.48, .72, .12), dome_glass)

# Central arch and care emblem.
cube("family-central-facade", (0, -3.70, 3.47), (2.10, .30, 2.54), trim, .34)
torus("family-facade-arch", (0, -4.04, 4.66), 2.10, .18, trim, rotation=(pi / 2, 0, 0))
curve("family-emblem-halo", [(-1.10, -4.45, 5.18), (-.72, -4.45, 5.82), (0, -4.45, 6.05), (.72, -4.45, 5.82), (1.10, -4.45, 5.18)], .07, copper)
curve("family-care-hand-left", [(-1.25, -4.50, 4.70), (-.84, -4.50, 4.42), (-.35, -4.50, 4.62), (-.16, -4.50, 5.02)], .12, rose)
curve("family-care-hand-right", [(1.25, -4.50, 4.70), (.84, -4.50, 4.42), (.35, -4.50, 4.62), (.16, -4.50, 5.02)], .12, rose)
for side in (-1, 1):
    palm = sphere(f"family-care-palm-{side}", (side * .62, -4.53, 4.72), (.52, .07, .22), rose, segments=32, rings=16)
    palm.rotation_euler.y = -side * .24
    for finger in range(4):
        start_x = side * (.42 + finger * .12)
        curve(
            f"family-care-finger-{side}-{finger}",
            [(start_x, -4.58, 4.82), (side * (.28 + finger * .10), -4.58, 5.02 + finger * .055)],
            .045,
            rose,
        )
curve("family-leaf-stem", [(0, -4.58, 4.80), (0, -4.58, 5.78)], .055, green)
for side, x, z, rot in ((0, 0, 5.65, 0), (-1, -.38, 5.42, -.55), (1, .38, 5.42, .55)):
    leaf = sphere(f"family-emblem-leaf-{side}", (x, -4.57, z), (.27, .06, .48), green, segments=24, rings=12)
    leaf.rotation_euler.y = rot

# Curved glazing and warm consultation rooms.
for side in (-1, 1):
    for index in range(5):
        x = side * (2.46 + index * .92)
        ellipse = max(.08, 1 - (x / 7.18) ** 2)
        y = -3.72 * sqrt(ellipse)
        slope = 3.72 * x / (7.18 * 7.18 * sqrt(ellipse))
        tangent = atan(slope)
        front_window(f"family-window-{side}-{index}", x, y - .10, 2.66, .78, 2.04, glass, frame, tangent)
        cube(f"family-interior-glow-{side}-{index}", (x, y + .10, 2.65), (.25, .05, .76), warm, .02)

cube("family-entry-recess", (0, -4.05, 2.42), (1.30, .20, 1.35), frame, .28)
for x in (-.62, .62):
    cube("family-entry-door", (x, -4.27, 2.22), (.54, .06, 1.10), glass, .025)
for x in (-1.25, 0, 1.25):
    cube("family-entry-mullion", (x, -4.34, 2.46), (.055, .055, 1.38), frame, .015)
for x in (-1.58, 1.58):
    cube("family-entry-pillar", (x, -4.19, 2.60), (.17, .22, 1.55), trim, .05)
    cube("family-wall-lantern", (x, -4.43, 2.72), (.11, .10, .31), frame, .03)
    cube("family-lantern-glow", (x, -4.55, 2.72), (.07, .06, .23), warm, .02)
for index, (width, depth, z) in enumerate(((2.28, .98, .70), (1.98, .70, .88), (1.70, .43, 1.06))):
    cube(f"family-step-{index}", (0, -4.20 - depth / 2, z), (width, depth / 2, .11), trim, .07)

# Paired accessible ramps and handrails.
for side in (-1, 1):
    ramp = cube(f"family-accessible-ramp-{side}", (side * 3.40, -4.78, .78), (1.92, .62, .10), trim, .06)
    ramp.rotation_euler.y = -side * .13
    for rail_x in (side * 1.58, side * 5.20):
        for index in range(5):
            cube(f"family-ramp-post-{side}", (rail_x, -5.28 + index * .32, 1.18), (.025, .025, .40), brass, .008)
        cube(f"family-ramp-rail-{side}", (rail_x, -4.64, 1.52), (.025, .84, .025), brass, .008)

# Shared-decision round table, chairs, exam bed and vital-sign monitor.
cyl("family-decision-table", (3.30, -3.18, 1.95), .68, .12, cream)
cyl("family-table-pedestal", (3.30, -3.18, 1.56), .20, .70, copper)
for index in range(3):
    angle = index * 2 * pi / 3
    x, y = 3.30 + cos(angle) * 1.08, -3.18 + sin(angle) * .58
    cube(f"family-chair-seat-{index}", (x, y, 1.72), (.28, .28, .08), cream, .08)
    cube(f"family-chair-back-{index}", (x, y + .18, 2.02), (.28, .08, .32), cream, .08)
cube("family-exam-bed", (5.10, -3.08, 2.02), (.92, .32, .13), cream, .12)
cube("family-vitals-cart", (5.72, -3.16, 1.72), (.34, .28, .45), trim, .08)
cube("family-vitals-monitor", (5.70, -3.44, 2.45), (.40, .07, .30), monitor, .05, rotation=(-.10, 0, 0))

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

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
scene.world = bpy.data.worlds.new("family-preview-world")
scene.world.color = (.018, .028, .055)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
