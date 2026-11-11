from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
BLEND_PATH = ROOT / "source" / "model.blend"
GLB_PATH = ROOT / "export" / "env-pathology-island-001.glb"


def material(name, color):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1.0)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = 0.88
    shader.inputs["Metallic"].default_value = 0.0
    return value


def cylinder(name, radius, depth, location, mat, radius_top=None):
    bpy.ops.mesh.primitive_cone_add(
        vertices=6,
        radius1=radius,
        radius2=radius if radius_top is None else radius_top,
        depth=depth,
        location=location,
        rotation=(0.0, 0.0, 0.5235987756),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def cube(name, scale, location, mat):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("soft-edges", "BEVEL")
    bevel.width = 0.04
    bevel.segments = 2
    return obj


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "ENV-PATHOLOGY-ISLAND-001"
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

rock = material("rock", (0.561, 0.522, 0.490))
shore = material("grass-lower", (0.725, 0.773, 0.651))
grass = material("grass", (0.604, 0.647, 0.561))
path = material("path", (0.910, 0.788, 0.741))
gate = material("gate", (0.333, 0.420, 0.376))

cylinder("island-rock-base", 13.1, 2.55, (0, 0, -1.03), rock, 12.1)
cylinder("island-shore-rim", 12.45, 0.52, (0, 0, 0.47), shore, 12.35)
cylinder("island-grass-top", 12.04, 0.34, (0, 0, 0.88), grass, 11.72)
cube("north-care-path", (2.4, 3.0, 0.18), (0, 11.15, 1.13), path)
cube("north-gate-left", (0.22, 0.22, 2.25), (-1.12, 11.65, 2.15), gate)
cube("north-gate-right", (0.22, 0.22, 2.25), (1.12, 11.65, 2.15), gate)
cube("north-gate-header", (2.46, 0.22, 0.22), (0, 11.65, 3.2), gate)

scene["component_id"] = "ENV-PATHOLOGY-ISLAND-001"
scene["visitor_spawn"] = "3.0,8.2,1.13"
scene["pathology_cottage_anchor"] = "2.4,-3.4,1.27"
scene["north_connection"] = "0.0,11.7,1.12"

BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
GLB_PATH.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
bpy.ops.export_scene.gltf(
    filepath=str(GLB_PATH),
    export_format="GLB",
    export_apply=True,
    export_yup=True,
    export_materials="EXPORT",
)
print(f"BLEND={BLEND_PATH}")
print(f"GLB={GLB_PATH}")
