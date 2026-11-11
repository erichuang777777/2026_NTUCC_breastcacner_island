from pathlib import Path

import bpy
import bmesh


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "export" / "imaging-pavilion-hunyuan-shape-v01.glb"
OUTPUT = ROOT / "export" / "imaging-pavilion-hunyuan-shape-clean-v01.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))

removed_faces = 0
for obj in [item for item in bpy.context.scene.objects if item.type == "MESH"]:
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    unseen = set(bm.verts)
    components = []
    while unseen:
        seed = unseen.pop()
        stack = [seed]
        verts = {seed}
        while stack:
            vert = stack.pop()
            for edge in vert.link_edges:
                other = edge.other_vert(vert)
                if other in unseen:
                    unseen.remove(other)
                    verts.add(other)
                    stack.append(other)
        faces = {face for vert in verts for face in vert.link_faces}
        components.append((verts, faces))

    largest_face_count = max((len(faces) for _, faces in components), default=0)
    # 僅移除不到主體 0.03% 的游離碎片；保留窗框、燈具等合法細節。
    tiny = [vert for verts, faces in components if len(faces) < max(8, largest_face_count * 0.0003) for vert in verts]
    removed_faces += sum(len(faces) for _, faces in components if len(faces) < max(8, largest_face_count * 0.0003))
    if tiny:
        bmesh.ops.delete(bm, geom=tiny, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

bpy.ops.export_scene.gltf(
    filepath=str(OUTPUT),
    export_format="GLB",
    export_apply=True,
    export_yup=True,
)
print(f"output={OUTPUT}")
print(f"removed_faces={removed_faces}")
