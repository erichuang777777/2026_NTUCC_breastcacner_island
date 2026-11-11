from math import atan2, cos, pi, sin
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "export" / "ntucc-blender-v05.glb"
PREVIEW = ROOT / "export" / "ntucc-blender-v05-preview.png"
FONT = Path("/Users/eric777/Library/Fonts/NotoSansCJKtc-Medium.otf")


def mat(name, color, metallic=0.0, roughness=0.45, emission=None):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        shader.inputs["Emission Color"].default_value = emission
        shader.inputs["Emission Strength"].default_value = 1.5
    return material


def cube(name, loc, scale, material, bevel=0.0, rotation_z=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.rotation_euler.z = rotation_z
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("edge-softening", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
    return obj


def cylinder(name, loc, radius, depth, material, vertices=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def beam(name, start, end, radius, material):
    a, b = Vector(start), Vector(end)
    direction = b - a
    obj = cube(name, (a + b) / 2, (radius, radius, direction.length / 2), material, radius * 0.3)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def text_mesh(name, body, loc, size, material, rotation=(pi / 2, 0, 0), extrude=0.035):
    bpy.ops.object.text_add(location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = extrude
    obj.data.bevel_depth = 0.012
    obj.data.bevel_resolution = 2
    if FONT.exists():
        obj.data.font = bpy.data.fonts.load(str(FONT))
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return obj


bpy.ops.wm.read_factory_settings(use_empty=True)

glass = mat("ntucc-curtain-glass", (0.018, 0.080, 0.095, 1), metallic=0.40, roughness=0.18)
glass_lit = mat("ntucc-warm-interior", (0.18, 0.075, 0.025, 1), roughness=0.25, emission=(1.0, 0.30, 0.07, 1))
charcoal = mat("ntucc-charcoal-frame", (0.018, 0.026, 0.032, 1), metallic=0.52, roughness=0.28)
aluminum = mat("ntucc-silver-mullion", (0.40, 0.47, 0.50, 1), metallic=0.76, roughness=0.24)
sandstone = mat("ntucc-sandstone", (0.68, 0.47, 0.28, 1), roughness=0.63)
concrete = mat("ntucc-roof-concrete", (0.35, 0.36, 0.35, 1), roughness=0.82)
canopy_glass = mat("ntucc-canopy-glass", (0.11, 0.26, 0.27, 1), metallic=0.18, roughness=0.16)
roof_metal = mat("ntucc-roof-metal", (0.14, 0.17, 0.18, 1), metallic=0.65, roughness=0.34)
sign_metal = mat("ntucc-sign-brushed-metal", (0.72, 0.78, 0.76, 1), metallic=0.82, roughness=0.20)
sign_rose = mat("ntucc-sign-rose", (0.66, 0.16, 0.24, 1), metallic=0.18, roughness=0.38)
paver_dark = mat("ntucc-plaza-inlay", (0.22, 0.25, 0.26, 1), roughness=0.76)
pipe_green = mat("ntucc-roof-service-pipe", (0.18, 0.46, 0.28, 1), metallic=0.32, roughness=0.42)

# Main curved tower, assembled from tangent façade bays so each bay remains editable.
radius = 14.0
angles = [(-32 + i * 8) * pi / 180 for i in range(9)]
for bay_index, angle in enumerate(angles):
    x = radius * sin(angle)
    y = 2.8 - radius * (1 - cos(angle))
    rotation = -angle
    cube(f"tower-bay-{bay_index:02d}", (x, y, 7.25), (1.12, 1.22, 6.75), glass, 0.08, rotation)
    # Dark vertical piers and silver horizontal floor bands.
    for side in (-1, 1):
        dx, dy = side * 1.08, -1.25
        offset_x = dx * cos(rotation) - dy * sin(rotation)
        offset_y = dx * sin(rotation) + dy * cos(rotation)
        cube(f"tower-pier-{bay_index:02d}-{side}", (x + offset_x, y + offset_y, 7.25), (0.07, 0.09, 6.78), charcoal, 0.02, rotation)
    for floor in range(1, 12):
        z = 1.15 + floor * 1.05
        cube(f"tower-floor-band-{bay_index:02d}-{floor:02d}", (x, y - 1.29, z), (1.10, 0.055, 0.055), aluminum, 0.015, rotation)
    # Sparse warm windows keep night state readable without making every floor identical.
    for floor in range(2, 11, 3):
        z = 1.55 + floor * 1.05
        cube(f"tower-warm-window-{bay_index:02d}-{floor:02d}", (x, y - 1.31, z), (0.72, 0.025, 0.20), glass_lit, 0.01, rotation)

# Tower side cores and roof crown.
for side in (-1, 1):
    cube(f"tower-side-core-{side}", (side * 9.25, 1.65, 7.15), (1.05, 2.65, 6.65), charcoal, 0.16, side * 0.10)
cube("tower-roof-deck", (0, 2.2, 14.05), (9.25, 2.7, 0.24), concrete, 0.18)
cube("tower-roof-crown-front", (0, -0.25, 14.72), (9.45, 0.18, 0.72), charcoal, 0.09)
cube("tower-roof-crown-rear", (0, 4.60, 14.72), (9.45, 0.18, 0.72), charcoal, 0.09)
for unit in range(8):
    cube(f"tower-hvac-{unit:02d}", (-5.25 + unit * 1.50, 2.55, 14.55), (0.46, 0.70, 0.44), roof_metal, 0.08)
    cylinder(f"tower-hvac-fan-{unit:02d}", (-5.25 + unit * 1.50, 2.55, 15.03), 0.24, 0.10, charcoal, 32)

# Sandstone clinical wings.
for side in (-1, 1):
    wing_x = side * 10.65
    cube(f"clinical-wing-{side}", (wing_x, -0.15, 4.75), (3.30, 4.20, 4.45), sandstone, 0.16)
    cube(f"clinical-wing-roof-{side}", (wing_x, -0.15, 9.30), (3.15, 4.05, 0.16), concrete, 0.08)
    for floor in range(7):
        z = 1.45 + floor * 1.04
        for col in range(5):
            x = wing_x + side * (-2.10 + col * 1.05)
            cube(f"wing-window-{side}-{floor:02d}-{col:02d}", (x, -4.38, z), (0.36, 0.055, 0.28), glass, 0.035)
    for unit in range(4):
        cube(f"wing-hvac-{side}-{unit}", (wing_x - 1.65 + unit * 1.10, -0.3, 9.63), (0.34, 0.48, 0.34), roof_metal, 0.05)

# Main entrance and circular glass lobby.
cube("main-entry-recess", (0, -5.12, 1.45), (2.15, 0.18, 1.20), glass_lit, 0.08)
cube("main-entry-canopy", (0, -5.75, 2.65), (2.80, 1.00, 0.14), aluminum, 0.10)
# Individual sliding-door leaves, mullions and canopy ribs remain readable in
# close film shots instead of collapsing into a single glowing rectangle.
for panel in range(6):
    x = -1.75 + panel * 0.70
    cube(f"main-entry-glass-door-{panel:02d}", (x, -5.33, 1.22), (0.30, 0.035, 0.88), canopy_glass, 0.025)
    cube(f"main-entry-door-mullion-{panel:02d}", (x - 0.35, -5.38, 1.22), (0.025, 0.025, 0.94), aluminum, 0.008)
for rib in range(7):
    cube(f"main-entry-canopy-rib-{rib:02d}", (-2.40 + rib * 0.80, -5.78, 2.82), (0.035, 0.92, 0.045), aluminum, 0.012)
cylinder("round-glass-lobby", (3.15, -5.05, 1.55), 1.32, 2.75, canopy_glass, 64)
cylinder("round-lobby-roof", (3.15, -5.05, 3.00), 1.42, 0.14, aluminum, 64)
for i in range(12):
    a = i / 12 * 2 * pi
    beam("round-lobby-rib", (3.15, -5.05, 3.08), (3.15 + cos(a) * 1.30, -5.05 + sin(a) * 1.30, 3.08), 0.025, aluminum)

# Curved public arrival canopy: segmented arc gives a crisp, inspectable replacement
# for the melted Hunyuan foreground element.
arc_radius = 14.5
arc_angles = [(-36 + i * 6) * pi / 180 for i in range(13)]
for index, angle in enumerate(arc_angles[:-1]):
    next_angle = arc_angles[index + 1]
    p1 = Vector((arc_radius * sin(angle), -8.1 + arc_radius * (1 - cos(angle)), 2.15))
    p2 = Vector((arc_radius * sin(next_angle), -8.1 + arc_radius * (1 - cos(next_angle)), 2.15))
    mid = (p1 + p2) / 2
    length = (p2 - p1).length
    segment = cube(f"arrival-canopy-{index:02d}", mid, (length / 2 + 0.06, 1.10, 0.12), canopy_glass, 0.07)
    segment.rotation_euler.z = atan2(p2.y - p1.y, p2.x - p1.x)
    for endpoint in (p1,):
        cube(f"arrival-column-{index:02d}", (endpoint.x, endpoint.y, 1.02), (0.08, 0.08, 1.02), aluminum, 0.025)

# Ground plane/plaza belongs to the building candidate so its entrance reads correctly.
cube("entrance-plaza", (0, -5.3, 0.18), (14.0, 4.2, 0.18), concrete, 0.12)
for stripe in range(13):
    cube(f"entrance-plaza-inlay-{stripe:02d}", (-12.0 + stripe * 2.0, -6.05, 0.375), (0.055, 2.85, 0.018), paver_dark, 0.012)

# Bilingual hospital identity is real geometry, not a floating HTML label.
text_mesh("ntucc-sign-zh", "臺大癌醫中心", (-8.45, -4.56, 8.30), 0.62, sign_metal)
text_mesh("ntucc-sign-en", "NTU CANCER CENTER", (-8.42, -4.57, 7.62), 0.27, sign_metal)
text_mesh("ntucc-sign-mark", "✚", (-12.25, -4.58, 8.00), 0.72, sign_rose)

# Roof service detail based on the aerial reference: equipment screen, chiller
# bank and green service pipes make the crown credible at oblique camera angles.
cube("tower-roof-equipment-screen", (0.0, 3.55, 14.82), (5.90, 0.08, 0.56), charcoal, 0.03)
for unit in range(6):
    x = -4.25 + unit * 1.70
    cube(f"tower-roof-chiller-{unit:02d}", (x, 3.15, 14.70), (0.58, 0.72, 0.38), roof_metal, 0.06)
    cylinder(f"tower-roof-chiller-fan-{unit:02d}", (x, 3.15, 15.13), 0.27, 0.08, charcoal, 24)
beam("tower-roof-service-pipe-a", (-5.2, 1.55, 14.50), (5.2, 1.55, 14.50), 0.11, pipe_green)
beam("tower-roof-service-pipe-b", (-5.2, 1.95, 14.50), (5.2, 1.95, 14.50), 0.08, pipe_green)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(OUTPUT), export_format="GLB", export_apply=True)

# Inspection render.
floor = cube("preview-floor", (0, 0, -0.12), (26, 22, 0.10), mat("preview-floor-mat", (0.02, 0.035, 0.045, 1), roughness=0.72))
for loc, energy, size, color in (
    ((-18, -18, 24), 2800, 10, (1.0, 0.66, 0.42)),
    ((18, -4, 18), 2300, 9, (0.32, 0.58, 1.0)),
    ((0, 16, 20), 1800, 8, (0.82, 0.36, 0.46)),
):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector((0, 0, 6.0)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(35, -49, 31))
camera = bpy.context.object
camera.data.lens = 66
camera.rotation_euler = (Vector((0, 0, 6.4)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("ntucc-night")
scene.world.color = (0.004, 0.010, 0.025)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"output={OUTPUT}")
print(f"preview={PREVIEW}")
