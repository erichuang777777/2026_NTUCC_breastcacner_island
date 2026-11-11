from pathlib import Path

import bpy
import bmesh


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "chr-visitor-hunyuan-textured-v02.glb"
TARGETS = (
    (80_000, ROOT / "export" / "chr-visitor-hunyuan-textured-lod0-v02.glb"),
    (35_000, ROOT / "export" / "chr-visitor-hunyuan-textured-lod1-v02.glb"),
    (12_000, ROOT / "export" / "chr-visitor-hunyuan-textured-lod2-v02.glb"),
)


def triangle_count(objects):
    return sum(len(obj.data.polygons) for obj in objects if obj.type == "MESH")


for target, output in TARGETS:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    source_triangles = triangle_count(meshes)
    ratio = min(1.0, target / source_triangles)

    for obj in meshes:
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        modifier = obj.modifiers.new(name=f"character-web-lod-{target}", type="DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = ratio
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj.data.validate(clean_customdata=True)
        edit_mesh = bmesh.new()
        edit_mesh.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(edit_mesh, faces=edit_mesh.faces)
        edit_mesh.to_mesh(obj.data)
        edit_mesh.free()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        obj.data.update()

    bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLB",
        export_apply=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
    )
    print(
        f"output={output} source_triangles={source_triangles} "
        f"triangles={triangle_count(meshes)} ratio={ratio:.6f}"
    )
