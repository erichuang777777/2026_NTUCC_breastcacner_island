from math import cos, pi, sin
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "imaging-pavilion-blender-v03.glb"
PREVIEW = ROOT / "export" / "imaging-pavilion-blender-v03-preview.png"


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
        bsdf.inputs["Emission Strength"].default_value = 2.0
    return mat


def add_micro_surface(mat, scale, strength, detail=4.0, roughness_variation=0.16):
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    texcoord = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = 0.68
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = strength
    bump.inputs["Distance"].default_value = 0.08
    remap = nodes.new("ShaderNodeMapRange")
    remap.inputs["To Min"].default_value = max(0.0, bsdf.inputs["Roughness"].default_value - roughness_variation)
    remap.inputs["To Max"].default_value = min(1.0, bsdf.inputs["Roughness"].default_value + roughness_variation)
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(noise.outputs["Fac"], remap.inputs["Value"])
    links.new(remap.outputs["Result"], bsdf.inputs["Roughness"])
    return mat


def cube(name, location, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("edge-softening", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    obj.data.materials.append(mat)
    return obj


def cylinder(name, location, radius, depth, mat, vertices=96, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def tapered_roof(name, center, bottom_size, top_size, height, mat):
    bx, by = bottom_size[0] / 2, bottom_size[1] / 2
    tx, ty = top_size[0] / 2, top_size[1] / 2
    z0 = center[2] - height / 2
    z1 = center[2] + height / 2
    verts = [
        (center[0] - bx, center[1] - by, z0), (center[0] + bx, center[1] - by, z0),
        (center[0] + bx, center[1] + by, z0), (center[0] - bx, center[1] + by, z0),
        (center[0] - tx, center[1] - ty, z1), (center[0] + tx, center[1] - ty, z1),
        (center[0] + tx, center[1] + ty, z1), (center[0] - tx, center[1] + ty, z1),
    ]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("roof-edge-softening", "BEVEL")
    bevel.width = 0.08
    bevel.segments = 3
    return obj


def beam_between(name, start, end, radius, mat):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    midpoint = (start_v + end_v) / 2
    obj = cube(name, midpoint, (radius, radius, direction.length / 2), mat, radius * 0.35)
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def barrel(name, center, width, depth, spring_z, radius, mat, segments=48):
    """Closed half-cylinder roof, axis along Y."""
    verts = []
    faces = []
    for y in (-depth / 2, depth / 2):
        for i in range(segments + 1):
            angle = pi * i / segments
            verts.append((center[0] + width * cos(angle) / 2, center[1] + y, spring_z + radius * sin(angle)))
    row = segments + 1
    for i in range(segments):
        faces.append((i, i + 1, row + i + 1, row + i))
    faces.append(tuple(range(row - 1, -1, -1)))
    faces.append(tuple(range(row, row * 2)))
    faces.append((0, row, row * 2 - 1, row - 1))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("roof-edge-softening", "BEVEL")
    bevel.width = 0.055
    bevel.segments = 2
    return obj


def arch_trim(name, center, radius, thickness, depth, mat):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = thickness
    curve.bevel_resolution = 4
    spline = curve.splines.new("POLY")
    spline.points.add(32)
    for i, point in enumerate(spline.points):
        angle = pi * i / 32
        point.co = (center[0] + radius * cos(angle), center[1], center[2] + radius * sin(angle), 1)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def window_panel(name, x, y, z, width, height, glass, frame, rotation_z=0):
    panel = cube(name + "-glass", (x, y, z), (width / 2, 0.045, height / 2), glass, 0.025)
    panel.rotation_euler.z = rotation_z
    for dx in (-width / 2, width / 2):
        mullion = cube(name + "-vertical", (x + dx * cos(rotation_z), y + dx * sin(rotation_z), z), (0.045, 0.07, height / 2 + 0.06), frame, 0.018)
        mullion.rotation_euler.z = rotation_z
    for dz in (-height / 2, 0, height / 2):
        rail = cube(name + "-rail", (x, y, z + dz), (width / 2 + 0.04, 0.07, 0.045), frame, 0.018)
        rail.rotation_euler.z = rotation_z
    return panel


def roof_seams(prefix, x_min, x_max, y, z, count, height, mat):
    for i in range(count + 1):
        x = x_min + (x_max - x_min) * i / count
        cube(f"{prefix}-seam-{i:02d}", (x, y, z), (0.025, 0.07, height), mat, 0.012)


bpy.ops.wm.read_factory_settings(use_empty=True)

stone = material("warm-limestone", (0.82, 0.68, 0.52, 1), roughness=0.50)
stone_light = material("carved-limestone", (0.96, 0.84, 0.68, 1), roughness=0.42)
base_stone = material("rusticated-stone", (0.58, 0.45, 0.37, 1), roughness=0.66)
roof = material("imaging-blue-standing-seam-roof", (0.22, 0.40, 0.47, 1), metallic=0.36, roughness=0.34)
roof_trim = material("champagne-metal-trim", (0.61, 0.43, 0.24, 1), metallic=0.62, roughness=0.28)
frame = material("soft-bronze-window-frame", (0.18, 0.22, 0.20, 1), metallic=0.50, roughness=0.25)
glass = material("bright-architectural-glass", (0.22, 0.48, 0.58, 0.28), roughness=0.05, transmission=0.86)
warm = material("interior-warmth", (0.70, 0.27, 0.06, 1), roughness=0.30, emission=(1.0, 0.42, 0.11, 1))
red = material("imaging-blue-enamel", (0.18, 0.43, 0.60, 1), metallic=0.24, roughness=0.30)
green = material("leaf-green", (0.07, 0.28, 0.10, 1), roughness=0.52)
equipment = material("diagnostic-equipment", (0.72, 0.79, 0.81, 1), metallic=0.34, roughness=0.28)
screen = material("diagnostic-screen", (0.06, 0.21, 0.28, 1), metallic=0.10, roughness=0.16, emission=(0.08, 0.45, 0.72, 1))

add_micro_surface(stone, 9.0, 0.24, detail=5.0, roughness_variation=0.12)
add_micro_surface(stone_light, 13.0, 0.16, detail=5.0, roughness_variation=0.10)
add_micro_surface(base_stone, 6.5, 0.34, detail=6.0, roughness_variation=0.15)
add_micro_surface(roof, 22.0, 0.12, detail=3.0, roughness_variation=0.13)

# 海報主量體：低矮、寬闊、左右雙翼大圓角，中央入口略高。
cube("foundation", (0, 0, 0.30), (7.65, 4.05, 0.30), base_stone, 0.28)
cube("left-wing", (-4.05, 0.15, 2.20), (3.45, 3.55, 1.86), stone, 0.92)
cube("right-wing", (4.05, 0.15, 2.20), (3.45, 3.55, 1.86), stone, 0.92)
cube("central-tower", (0, 0.05, 2.82), (1.62, 3.62, 2.38), stone_light, 0.62)

# Rusticated lower band and cornices.
for x in (-4.05, 4.05):
    cube("wing-rusticated-base", (x, -3.52, 0.88), (3.34, 0.16, 0.36), base_stone, 0.12)
    cube("wing-belt-course", (x, -3.66, 1.38), (3.48, 0.13, 0.10), stone_light, 0.06)
    cube("wing-cornice", (x, -3.66, 4.08), (3.56, 0.16, 0.13), stone_light, 0.08)

# 單層緩坡屋頂取代舊版三層階梯屋頂，輪廓接近海報的現代弧形量體。
for x in (-4.05, 4.05):
    tapered_roof("wing-sage-canopy", (x, 0.10, 4.34), (7.12, 7.42), (6.54, 6.82), 0.50, roof)
    cube("wing-roof-trim", (x, -3.68, 4.18), (3.60, 0.13, 0.10), roof_trim, 0.06)
    for seam_index in range(15):
        seam_x = x - 3.18 + 6.36 * seam_index / 14
        beam_between("wing-standing-seam", (seam_x, -3.56, 4.12), (seam_x, -3.26, 4.58), 0.022, roof_trim)

# 中央冠部與入口牆連成一體；大圓角薄頂取代懸浮筒狀屋頂。
cube("central-rounded-crown", (0, 0.05, 5.34), (1.76, 3.70, 0.24), roof, 0.42)
for x in (-1.50, -0.75, 0, 0.75, 1.50):
    cube("central-crown-seam", (x, -3.66, 5.34), (0.025, 0.08, 0.27), roof_trim, 0.015)

# 前方玻璃幕牆沿橢圓弧排列，讓左右翼形成海報可辨識的弧形玻璃立面。
for side in (-1, 1):
    for index in range(7):
        local = index / 6
        x = side * (1.88 + local * 4.90)
        y = -3.72 + 0.82 * local * local
        tangent = side * 0.34 * local
        window_panel(f"front-window-{side}-{index}", x, y - 0.05, 2.60, 0.70, 2.18, glass, frame, tangent)
        cube("interior-glow", (x, y + 0.12, 2.60), (0.27, 0.05, 0.84), warm, 0.03)

# Side window walls.
for side in (-1, 1):
    for index in range(5):
        y = -2.35 + index * 1.15
        panel = window_panel(f"side-window-{side}-{index}", side * 7.38, y, 2.60, 0.82, 2.18, glass, frame, pi / 2)

# Entrance portal, glass doors and arch surround.
cube("entry-recess", (0, -4.02, 2.75), (1.02, 0.13, 1.65), frame, 0.36)
cube("left-entry-door", (-0.48, -4.18, 2.30), (0.43, 0.07, 1.20), glass, 0.03)
cube("right-entry-door", (0.48, -4.18, 2.30), (0.43, 0.07, 1.20), glass, 0.03)
for x in (-0.98, 0, 0.98):
    cube("entry-mullion", (x, -4.28, 2.56), (0.055, 0.07, 1.55), frame, 0.018)
cube("entry-transom", (0, -4.28, 3.14), (1.02, 0.07, 0.055), frame, 0.018)
for x in (-1.18, 1.18):
    cube("portal-pillar", (x, -4.24, 2.75), (0.16, 0.18, 1.72), stone_light, 0.04)
arch_trim("portal-arch", (0, -4.25, 3.56), 1.18, 0.14, 0.1, stone_light)

# Three broad entry steps.
for index, (depth, width, z) in enumerate(((0.85, 1.72, 0.68), (0.60, 1.50, 0.85), (0.38, 1.28, 1.02))):
    cube(f"entry-step-{index}", (0, -4.15 - depth / 2, z), (width, depth / 2, 0.11), stone_light, 0.08)

# Stone panel joints across facade.
for side in (-1, 1):
    for x_idx in range(6):
        x = side * (1.85 + x_idx * 0.96)
        cube("stone-vertical-joint", (x, -4.005, 3.86), (0.018, 0.012, 0.48), base_stone)
    for z in (3.45, 4.25):
        cube("stone-horizontal-joint", (side * 4.55, -4.005, z), (2.76, 0.012, 0.018), base_stone)

# 影像醫學專屬標誌：掃描環、檢查床與三道訊號波紋。
cylinder("emblem-medallion", (0, -4.16, 5.18), 0.76, 0.11, stone_light, rotation=(pi / 2, 0, 0))
cylinder("scanner-gantry", (0, -4.26, 5.17), 0.40, 0.13, red, vertices=64, rotation=(pi / 2, 0, 0))
cylinder("scanner-bore", (0, -4.34, 5.17), 0.22, 0.15, frame, vertices=64, rotation=(pi / 2, 0, 0))
cube("scanner-table", (-0.12, -4.40, 4.86), (0.48, 0.10, 0.09), equipment, 0.05)
for index, radius in enumerate((0.34, 0.52, 0.70)):
    arch_trim(f"imaging-signal-{index}", (0, -4.32, 5.58), radius, 0.045, 0.06, red)
for side in (-1, 1):
    leaf = cube("emblem-leaf", (side * 0.48, -4.26, 5.08), (0.10, 0.045, 0.28), green, 0.09)
    leaf.rotation_euler.y = side * 0.65

# 右側窗前的診斷床與螢幕，讓遠景仍可辨識醫療用途。
bed = cube("diagnostic-bed", (4.55, -4.08, 2.10), (0.92, 0.16, 0.16), equipment, 0.12)
bed.rotation_euler.z = -0.08
cube("diagnostic-bed-pedestal", (4.55, -4.00, 1.62), (0.28, 0.16, 0.38), equipment, 0.08)
monitor = cube("diagnostic-monitor", (5.80, -4.06, 2.64), (0.42, 0.08, 0.32), screen, 0.06)
monitor.rotation_euler.z = 0.06
cube("diagnostic-monitor-arm", (5.50, -4.00, 2.20), (0.06, 0.06, 0.48), equipment, 0.03)

# Warm ceiling lights visible through glazing.
for x in (-5.7, -3.8, 3.8, 5.7):
    bpy.ops.object.light_add(type="POINT", location=(x, -2.9, 3.2))
    light = bpy.context.object
    light.data.energy = 75
    light.data.color = (1.0, 0.34, 0.11)
    light.data.shadow_soft_size = 0.8

# Export clean asset before preview-only stage and lighting are added.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

# Movie-poster inspection render.
floor = cube("preview-floor", (0, 0, -0.08), (15, 15, 0.08), material("preview-floor-mat", (0.018, 0.028, 0.038, 1), roughness=0.7))
for location, energy, size, color in (
    ((-10, -12, 15), 1900, 7, (1.0, 0.64, 0.42)),
    ((10, -2, 11), 1500, 6, (0.35, 0.62, 1.0)),
    ((0, 8, 13), 1300, 5, (0.85, 0.35, 0.44)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector((0, 0, 3.1)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(17.5, -25.0, 13.0))
camera = bpy.context.object
camera.data.lens = 62
camera.rotation_euler = (Vector((0, 0, 3.3)) - camera.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("night-world")
scene.world.color = (0.006, 0.012, 0.028)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"export={EXPORT}")
print(f"preview={PREVIEW}")
