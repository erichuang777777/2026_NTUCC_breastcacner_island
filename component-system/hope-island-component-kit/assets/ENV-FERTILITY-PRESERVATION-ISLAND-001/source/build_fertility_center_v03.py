from math import atan2, cos, pi, sin
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "fertility-center-blender-v03.glb"
PREVIEW = ROOT / "export" / "fertility-center-blender-v03-preview.png"


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


bpy.ops.wm.read_factory_settings(use_empty=True)

limestone = mat("fertility-warm-limestone", (.84, .70, .58, 1), roughness=.54)
trim = mat("fertility-carved-stone", (.97, .83, .70, 1), roughness=.42)
base = mat("fertility-rusticated-base", (.43, .35, .29, 1), roughness=.74)
mauve = mat("fertility-mauve-copper", (.48, .22, .49, 1), metallic=.50, roughness=.29)
mauve_light = mat("fertility-mauve-highlight", (.66, .36, .64, 1), metallic=.42, roughness=.28)
copper = mat("fertility-rose-copper", (.66, .34, .27, 1), metallic=.70, roughness=.24)
frame = mat("fertility-window-frame", (.035, .07, .065, 1), metallic=.60, roughness=.22)
glass = mat("fertility-warm-glass", (.23, .35, .34, .27), roughness=.09, transmission=.70, emission=(.18, .10, .045, 1))
warm = mat("fertility-warm-interior", (.55, .16, .025, 1), roughness=.30, emission=(1, .30, .07, 1))
seed = mat("fertility-hope-seed", (.80, .45, .34, 1), metallic=.55, roughness=.28)
hand = mat("fertility-protective-hand", (.74, .38, .34, 1), metallic=.28, roughness=.33)
lab = mat("fertility-lab-ceramic", (.82, .84, .80, 1), metallic=.10, roughness=.31)
steel = mat("fertility-cryogenic-steel", (.48, .55, .57, 1), metallic=.80, roughness=.18)
screen = mat("fertility-lab-screen", (.03, .07, .09, 1), metallic=.18, roughness=.16, emission=(.08, .34, .48, 1))
lavender = mat("fertility-consultation-chair", (.53, .37, .55, 1), roughness=.40)

# Rounded fertility centre shell.
cyl("fertility-foundation", (0, 0, .42), 7.72, .84, base, scale=(1.06, .56, 1))
cyl("fertility-center-body", (0, 0, 2.44), 7.26, 3.95, limestone, scale=(1.05, .53, 1))
cyl("fertility-base-course", (0, 0, 1.02), 7.35, .66, base, scale=(1.06, .535, 1))

# Five low horizontal rose-copper shells, matching the poster's layered pavilion roof.
roof_layout = (
    (-4.25, -.15, 4.58, 3.45, 1.62, -.10),
    (-2.25, 1.05, 5.14, 3.40, 1.58, -.04),
    (0, 1.48, 5.58, 3.62, 1.72, 0),
    (2.35, 1.04, 5.14, 3.40, 1.58, .04),
    (4.35, -.12, 4.58, 3.45, 1.62, .10),
)
for index, (x, y, z, sx, sy, angle) in enumerate(roof_layout):
    petal = sphere(f"fertility-roof-shell-{index}", (x, y, z), (sx, sy, .38), mauve_light, rotation=(0, .07, angle))
    petal.rotation_euler.z = angle
    rim = sphere(f"fertility-roof-rim-{index}", (x, y, z + .11), (sx + .05, sy + .05, .055), copper, rotation=(0, .07, angle))
    rim.rotation_euler.z = angle
    for rib_index in range(-2, 3):
        rib_x = x + rib_index * sx * .30
        curve(f"fertility-roof-rib-{index}-{rib_index}", [(rib_x, y - sy * .80, z), (rib_x, y, z + .43), (rib_x, y + sy * .80, z)], .026, copper)

# Central monumental facade and seed-protection emblem.
cube("fertility-central-facade", (0, -3.70, 3.50), (2.12, .32, 2.55), trim, .28)
curve("fertility-central-arch", [(-2.08, -4.04, 4.72), (0, -4.08, 5.92), (2.08, -4.04, 4.72)], .17, trim)
sphere("fertility-emblem-seed", (0, -4.10, 5.34), (.30, .07, .52), seed, rotation=(0, .18, 0), segments=32, rings=16)
for side in (-1, 1):
    palm = sphere(f"fertility-emblem-palm-{side}", (side * .55, -4.11, 4.88), (.42, .07, .18), hand, segments=32, rings=16)
    palm.rotation_euler.y = -side * .36
    curve(f"fertility-emblem-arm-{side}", [(side * 1.02, -4.10, 4.52), (side * .68, -4.10, 4.72), (side * .34, -4.10, 5.04)], .09, hand)
    for finger in range(3):
        curve(f"fertility-emblem-finger-{side}-{finger}", [(side * (.32 + finger * .11), -4.18, 4.98), (side * (.20 + finger * .07), -4.18, 5.24 + finger * .05)], .038, hand)

# Broad consultation and embryology glazing follows the elliptical facade.
for side in (-1, 1):
    for index in range(7):
        theta = (1.67 + index * .17) if side < 0 else (.28 + index * .17)
        x = 7.62 * cos(theta)
        y = -4.02 * sin(theta)
        angle = atan2(-4.02 * cos(theta), -7.62 * sin(theta))
        curved_window(f"fertility-window-{side}-{index}", x, y, 2.55, .74, 2.25, angle, glass, frame)

cube("fertility-entry-recess", (0, -4.08, 2.38), (1.32, .20, 1.40), frame, .27)
for x in (-.64, .64):
    cube("fertility-entry-door", (x, -4.30, 2.20), (.55, .06, 1.12), glass, .025)
for x in (-1.26, 0, 1.26):
    cube("fertility-entry-mullion", (x, -4.37, 2.46), (.055, .055, 1.42), frame, .015)
for x in (-1.62, 1.62):
    cube("fertility-entry-pillar", (x, -4.21, 2.60), (.17, .22, 1.58), trim, .05)
    cube("fertility-wall-lantern", (x, -4.45, 2.72), (.11, .10, .31), frame, .03)
    cube("fertility-lantern-glow", (x, -4.57, 2.72), (.07, .06, .23), warm, .02)
for index, (width, depth, z) in enumerate(((2.30, .98, .70), (2.00, .70, .88), (1.72, .43, 1.06))):
    cube(f"fertility-step-{index}", (0, -4.23 - depth / 2, z), (width, depth / 2, .11), trim, .07)

# Paired accessible ramps and rose-copper rails.
for side in (-1, 1):
    ramp = cube(f"fertility-accessible-ramp-{side}", (side * 3.48, -4.82, .78), (1.98, .62, .10), trim, .06)
    ramp.rotation_euler.y = -side * .13
    for rail_x in (side * 1.62, side * 5.35):
        for index in range(5):
            cube(f"fertility-ramp-post-{side}", (rail_x, -5.32 + index * .32, 1.18), (.025, .025, .40), copper, .008)
        cube(f"fertility-ramp-rail-{side}", (rail_x, -4.68, 1.52), (.025, .84, .025), copper, .008)

# Private consultation furniture in the left bay.
cyl("fertility-consultation-table", (-4.15, -3.22, 1.90), .58, .12, trim)
cyl("fertility-table-pedestal", (-4.15, -3.22, 1.52), .18, .68, copper)
for side in (-1, 1):
    cube(f"fertility-consultation-chair-{side}", (-4.15 + side * .82, -3.18, 1.72), (.28, .28, .08), lavender, .08)
    cube(f"fertility-chair-back-{side}", (-4.15 + side * .82, -3.00, 2.02), (.28, .08, .32), lavender, .08)

# Embryology workbench, microscopes and screens.
cube("fertility-lab-bench", (3.42, -3.20, 1.74), (1.85, .34, .44), lab, .08)
for index in range(3):
    x = 2.35 + index * 1.05
    cyl(f"fertility-microscope-base-{index}", (x, -3.52, 2.22), .18, .08, frame, vertices=32)
    cube(f"fertility-microscope-arm-{index}", (x, -3.46, 2.52), (.07, .07, .30), lab, .04, rotation=(0, .24, 0))
    cyl(f"fertility-microscope-lens-{index}", (x + .10, -3.50, 2.77), .09, .20, frame, vertices=24, rotation=(pi / 2, 0, 0))
    cube(f"fertility-lab-screen-{index}", (x + .34, -3.48, 2.45), (.24, .06, .18), screen, .04)

# Four independent cryogenic storage tanks in the far-right bay.
for index in range(4):
    x = 5.25 + index * .48
    cyl(f"fertility-cryotank-{index}", (x, -3.12, 2.08), .20, 1.42, steel, vertices=40)
    cyl(f"fertility-cryotank-lid-{index}", (x, -3.12, 2.82), .23, .12, steel, vertices=40)
    cube(f"fertility-cryotank-handle-{index}", (x, -3.12, 2.98), (.10, .05, .08), frame, .03)

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
scene.world = bpy.data.worlds.new("fertility-preview-world")
scene.world.color = (.018, .028, .055)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
