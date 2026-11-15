"""Integrate the approved v15 portrait with the v02 island body and actions.
Run with Blender headless, CPU, two threads. Head/face/hair above the neck are unchanged.
"""
from pathlib import Path
import hashlib, json, math
import bpy, bmesh
ROOT = Path(__file__).resolve().parents[5]
ASSETS = ROOT / 'webgl-prototype/assets/characters'
OUT = ASSETS / 'director-v16'
OUT.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ASSETS / 'director-v02/director_wu.glb'))
rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
body = bpy.data.objects['cast_body']
# Remove all old facial parts; keep the tailored coat, hands, legs and authored rig.
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH' and o != body:
        bpy.data.objects.remove(o, do_unlink=True)
head_groups = {g.index for g in body.vertex_groups if g.name in {'head', 'eye.L', 'eye.R'}}
remove = {v.index for v in body.data.vertices if any(g.group in head_groups and g.weight > .5 for g in v.groups)}
# The old neck is an independent skin ellipsoid; replace it with continuous v15 skin.
skin_slots = {i for i, m in enumerate(body.data.materials) if m and m.name.split('.')[0] == 'skin'}
for p in body.data.polygons:
    if p.material_index in skin_slots:
        remove.update(i for i in p.vertices if body.data.vertices[i].co.z > .88)
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index in remove], context='VERTS')
bm.to_mesh(body.data); bm.free(); body.data.update()
existing = set(bpy.context.scene.objects)
bpy.ops.import_scene.gltf(filepath=str(ASSETS / 'director-v15/director_wu.glb'))
portrait = [o for o in bpy.context.scene.objects if o not in existing and o.type == 'MESH']
for o in portrait:
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if o.name == 'anatomy_head_and_neck':
        # Remove study shoulders hidden by the coat, retaining a continuous neck.
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces), dist=.000001,
                              plane_co=(0,0,.975), plane_no=(0,0,1), clear_inner=True)
        for v in bm.verts:
            # Only lower neck narrows into the shirt collar; approved jaw remains unchanged.
            t=max(0,min(1,(1.105-v.co.z)/.105)); t=t*t*(3-2*t)
            radius=math.hypot(v.co.x/.075,v.co.y/.074)
            if radius>1:
                factor=1-t+t/radius
                v.co.x *= factor
                v.co.y *= factor
        bm.to_mesh(o.data); bm.free(); o.data.update()
    spine=o.vertex_groups.new(name='spine'); head=o.vertex_groups.new(name='head')
    for v in o.data.vertices:
        t=max(0,min(1,(v.co.z-1.005)/.10)); t=t*t*(3-2*t)
        if t>0: head.add([v.index],t,'REPLACE')
        if t<1: spine.add([v.index],1-t,'REPLACE')
    o.parent=rig
    mod=o.modifiers.new('Portrait follows shared skeleton','ARMATURE'); mod.object=rig
# Remove imported bone display objects and keep only the actual character.
for o in list(bpy.context.scene.objects):
    if o.type == 'MESH' and o not in [body, *portrait]: bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [rig,body,*portrait]: o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'director_wu.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,
                         export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True)
p=OUT/'director_wu.glb'
(OUT/'manifest.json').write_text(json.dumps({'version':'director-v16','portrait':'director-v15','bodyAndActions':'director-v02',
 'integratedInIsland':True,'faceAndHairUnchanged':True,'oldFaceRemoved':True,'neckTransition':[.975,1.105],
 'sideBackEstimated':True,'bytes':p.stat().st_size,'assetSHA256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n')
