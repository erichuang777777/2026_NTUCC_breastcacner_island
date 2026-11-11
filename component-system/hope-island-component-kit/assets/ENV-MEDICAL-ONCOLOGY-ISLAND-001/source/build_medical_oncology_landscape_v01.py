from math import atan2, cos, hypot, pi, sin
from pathlib import Path
import random

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "medical-oncology-landscape-blender-v03.glb"
PREVIEW = ROOT / "export" / "medical-oncology-landscape-blender-v03-preview.png"
BUILDING = ROOT / "export" / "medical-oncology-clinic-blender-v04.glb"
random.seed(20261106)


def material(name, color, metallic=0.0, roughness=0.5, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 3.0
    return mat


def cube(name, location, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("soft-edge", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return obj


def cylinder(name, location, radius, depth, mat, vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def sphere(name, location, scale, mat, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def tree(prefix, x, y, height, blossom=False):
    trunk = cylinder(prefix + "-trunk", (x, y, height * .28), .22, height * .56, bark, 16)
    trunk.rotation_euler.z = random.uniform(-.08, .08)
    crowns = [
        (0, 0, .72, 1.00), (-.55, .05, .68, .68), (.52, .12, .70, .72),
        (-.18, -.45, .78, .65), (.24, .42, .76, .62),
    ]
    palette = (petal_pink, petal_light, petal_deep) if blossom else (leaf, leaf_light, leaf_dark)
    for index, (dx, dy, zf, size) in enumerate(crowns):
        sphere(
            f"{prefix}-crown-{index:02d}",
            (x + dx * height * .22, y + dy * height * .22, zf * height),
            (size * height * .24, size * height * .21, size * height * .19),
            palette[index % len(palette)],
            2,
        )


def flower_bed(prefix, x, y, rx, ry, color_cycle):
    sphere(prefix + "-soil", (x, y, .18), (rx, ry, .18), soil, 2)
    count = max(30, int(rx * ry * 13.0))
    for index in range(count):
        angle = random.random() * 2 * pi
        radius = random.random() ** .5
        fx = x + rx * .84 * radius * __import__("math").cos(angle)
        fy = y + ry * .84 * radius * __import__("math").sin(angle)
        stem_h = random.uniform(.18, .34)
        cylinder(f"{prefix}-stem-{index:03d}", (fx, fy, .26 + stem_h / 2), .025, stem_h, flower_leaf, 8)
        sphere(f"{prefix}-flower-{index:03d}", (fx, fy, .28 + stem_h), (.12, .12, .09), color_cycle[index % len(color_cycle)], 1)


def lamp(prefix, x, y):
    cylinder(prefix + "-post", (x, y, .78), .075, 1.45, bronze, 16)
    cube(prefix + "-lantern", (x, y, 1.55), (.20, .20, .27), lamp_glass, .06)
    cube(prefix + "-cap", (x, y, 1.86), (.27, .27, .06), bronze, .04)


def bench(prefix, x, y, rotation=0.0):
    seat = cube(prefix + "-seat", (x, y, .48), (1.02, .28, .10), wood, .08)
    back = cube(prefix + "-back", (x, y + .24, .86), (1.02, .08, .36), wood, .06)
    for dx in (-.78, .78):
        cylinder(prefix + "-leg", (x + dx, y, .25), .055, .42, bronze, 12)
    seat.rotation_euler.z = rotation
    back.rotation_euler.z = rotation


bpy.ops.wm.read_factory_settings(use_empty=True)

stone = material("infusion-garden-warm-stone", (.83, .67, .51, 1), roughness=.64)
stone_light = material("infusion-garden-pale-inlay", (.96, .83, .69, 1), roughness=.55)
grass = material("medical-oncology-island-grass", (.22, .43, .16, 1), roughness=.86)
cliff = material("medical-oncology-island-cliff", (.43, .34, .31, 1), roughness=.94)
soil = material("garden-soil", (.17, .07, .035, 1), roughness=.92)
bark = material("tree-bark", (.23, .105, .045, 1), roughness=.88)
leaf = material("garden-leaf", (.16, .38, .13, 1), roughness=.72)
leaf_light = material("garden-leaf-light", (.36, .55, .18, 1), roughness=.70)
leaf_dark = material("garden-leaf-dark", (.075, .24, .10, 1), roughness=.74)
petal_pink = material("cherry-petal-pink", (1.0, .49, .62, 1), roughness=.72)
petal_light = material("cherry-petal-light", (1.0, .75, .79, 1), roughness=.70)
petal_deep = material("cherry-petal-deep", (.86, .27, .43, 1), roughness=.72)
flower_white = material("flower-white", (1.0, .92, .79, 1), roughness=.68)
flower_rose = material("flower-rose", (.95, .26, .40, 1), roughness=.68)
flower_blush = material("flower-blush", (1.0, .54, .62, 1), roughness=.68)
flower_leaf = material("flower-stem", (.12, .34, .10, 1), roughness=.75)
wood = material("warm-bench-wood", (.48, .20, .075, 1), roughness=.58)
bronze = material("garden-bronze", (.20, .12, .07, 1), metallic=.72, roughness=.31)
lamp_glass = material("lamp-warm-glass", (1.0, .45, .12, 1), roughness=.22, emission=(1.0, .22, .045, 1))
roof = material("pavilion-sage-roof", (.24, .36, .28, 1), metallic=.22, roughness=.40)
display = material("infusion-wellness-display", (.87, .68, .68, 1), roughness=.38, emission=(.22, .04, .06, 1))
fence_wood = material("infusion-garden-fence-wood", (.34, .16, .065, 1), roughness=.78)
boat_hull = material("infusion-garden-boat-hull", (.72, .52, .32, 1), roughness=.62)
boat_trim = material("infusion-garden-boat-trim", (.93, .80, .60, 1), roughness=.48)
sail_mat = material("infusion-garden-sail", (.96, .83, .64, 1), roughness=.56)

# v02 只輸出可貼合舊島面的景觀元件；岩岸與草地殼不能在舊宏觀島殼仍存在時重疊。

# 中央入口步道與圓形節點，刻意保留兩側可行走空間。
cube("entry-promenade", (0, -7.8, .12), (1.55, 4.0, .12), stone, .16)
cylinder("garden-roundel", (0, -8.0, .15), 2.15, .14, stone_light, 64)
cylinder("garden-roundel-center", (0, -8.0, .24), .92, .20, leaf, 64)

# 左側輸液照護與療癒展示亭，對應電影海報的獨立景觀元件。
for x in (-6.7, -3.5):
    cylinder("pavilion-post", (x, -6.2, 1.55), .12, 3.0, stone_light, 20)
cube("pavilion-beam", (-5.1, -6.2, 3.05), (1.82, .18, .16), stone_light, .08)
cube("pavilion-roof", (-5.1, -6.2, 3.42), (2.12, 1.32, .22), roof, .36)
for index, x in enumerate((-5.95, -5.10, -4.25)):
    panel = cube(f"infusion-wellness-panel-{index}", (x, -6.18, 1.65), (.34, .06, .62), display, .08)
    panel.rotation_euler.x = -.18

# 海報主要植栽：兩株櫻花、後排常綠樹、環形花圃。
for args in (
    ("cherry-left", -5.6, -2.8, 4.4, True),
    ("cherry-right", 5.8, -3.0, 4.5, True),
    ("evergreen-left", -6.8, 2.2, 4.0, False),
    ("evergreen-center", 0.0, 3.0, 4.6, False),
    ("evergreen-right", 6.8, 2.1, 4.0, False),
    ("evergreen-rear-left", -3.9, 4.2, 3.8, False),
    ("evergreen-rear-right", 4.0, 4.1, 3.9, False),
):
    tree(*args)

flower_bed("roundel-bed", 0, -8.0, .82, .82, (flower_rose, flower_blush, flower_white))
flower_bed("left-front-bed", -4.6, -9.4, 2.4, .78, (flower_white, flower_rose, flower_blush))
flower_bed("right-front-bed", 4.7, -9.2, 2.3, .82, (flower_rose, flower_blush, flower_white))
flower_bed("left-side-bed", -7.0, -.4, .72, 2.1, (flower_blush, flower_white))
flower_bed("right-side-bed", 7.0, -.4, .72, 2.1, (flower_rose, flower_white))
flower_bed("left-mid-bed", -4.1, -4.1, 1.72, .72, (flower_white, flower_blush, flower_rose))
flower_bed("right-mid-bed", 4.2, -4.0, 1.78, .74, (flower_rose, flower_blush, flower_white))
flower_bed("rear-left-bed", -4.8, 1.7, 1.52, .62, (flower_blush, flower_white))
flower_bed("rear-right-bed", 4.8, 1.6, 1.52, .62, (flower_white, flower_rose))

for index, (x, y) in enumerate(((-2.3, -6.1), (2.3, -6.1), (-2.4, -10.2), (2.4, -10.2), (-6.9, -8.6), (6.9, -8.6))):
    lamp(f"garden-lamp-{index:02d}", x, y)

bench("bench-left", -5.0, -8.0, .12)
bench("bench-right", 5.0, -8.0, -.12)

# 電影海報的外圈木欄杆：保留前方碼頭與左右橋梁三個入口。
fence_segments = []
for index in range(64):
    angle = index / 64 * 2 * pi
    if any(abs((angle - opening + pi) % (2 * pi) - pi) < .23 for opening in (-pi / 2, 0, pi)):
        continue
    next_angle = angle + 2 * pi / 64
    if any(abs((next_angle - opening + pi) % (2 * pi) - pi) < .23 for opening in (-pi / 2, 0, pi)):
        continue
    fence_segments.append((angle, next_angle))

placed_posts = set()
for index, (angle, next_angle) in enumerate(fence_segments):
    radius = 10.35
    x, y = cos(angle) * radius, sin(angle) * radius - 2.25
    nx, ny = cos(next_angle) * radius, sin(next_angle) * radius - 2.25
    key = (round(x, 2), round(y, 2))
    if key not in placed_posts:
        cylinder(f"perimeter-fence-post-{index:02d}", (x, y, .72), .095, 1.35, fence_wood, 12)
        placed_posts.add(key)
    length = hypot(nx - x, ny - y)
    heading = atan2(ny - y, nx - x)
    for rail_index, height in enumerate((.58, 1.02)):
        rail = cube(f"perimeter-fence-rail-{index:02d}-{rail_index}", ((x + nx) / 2, (y + ny) / 2, height), (length / 2, .055, .055), fence_wood, .025)
        rail.rotation_euler.z = heading

# 前方碼頭小船與桅杆作為電影構圖的低視覺重心；保持在碰撞區域外。
boat_parts = []
boat_parts.append(cube("dock-boat-hull", (-2.35, -12.0, .36), (1.65, .55, .34), boat_hull, .30))
boat_parts.append(cube("dock-boat-inner", (-2.35, -12.0, .68), (1.28, .36, .10), boat_trim, .12))
cylinder("dock-boat-mast", (-2.35, -12.0, 2.0), .055, 2.75, bronze, 12)
sail = cube("dock-boat-sail", (-1.82, -12.0, 2.05), (.48, .045, .82), sail_mat, .04)
sail.rotation_euler.y = -.30

for index, (x, y) in enumerate(((-8.2, -4.8), (8.2, -4.8), (-8.0, 1.0), (8.0, 1.0))):
    lamp(f"perimeter-lamp-{index:02d}", x, y)

# 先只匯出景觀元件，確保建築與庭園可獨立替換。
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(filepath=str(EXPORT), export_format="GLB", export_apply=True)

# 預覽階段才載入 v04 建築，證明建築與景觀是可獨立替換的元件。
bpy.ops.import_scene.gltf(filepath=str(BUILDING))
cube("preview-floor", (0, 0, -.14), (12, 12, .12), material("preview-ground", (.035, .075, .055, 1), roughness=.86), .25)
for location, energy, size, color in (
    ((-12, -14, 18), 2100, 7, (1.0, .67, .43)),
    ((12, -3, 13), 1500, 6, (.38, .64, 1.0)),
    ((0, 9, 16), 1200, 6, (.92, .38, .45)),
):
    bpy.ops.object.light_add(type="AREA", location=location)
    light = bpy.context.object
    light.data.energy = energy
    light.data.size = size
    light.data.color = color
    light.rotation_euler = (Vector((0, -2.5, 2.3)) - light.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(17.8, -26.5, 17.0))
camera = bpy.context.object
camera.data.lens = 56
camera.rotation_euler = (Vector((0, -3.2, 2.5)) - camera.location).to_track_quat("-Z", "Y").to_euler()
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(PREVIEW)
scene.world = bpy.data.worlds.new("cinematic-dusk")
scene.world.color = (.012, .022, .040)
scene.view_settings.look = "AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True)
print(f"export={EXPORT}")
print(f"preview={PREVIEW}")
