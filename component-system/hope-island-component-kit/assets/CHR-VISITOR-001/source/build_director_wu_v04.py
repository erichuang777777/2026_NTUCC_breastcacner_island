"""Photo-guided rigid portrait head; existing body skeleton/actions remain editable.
The face has estimated depth, a closed posterior skull, dimensional ears and hair.
Single-photo texture projection is not a scan or an expression-ready facial rig.
"""
from pathlib import Path
import bpy,bmesh,math,json
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'webgl-prototype/assets/characters/director-v04';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v03.blend')))
bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.animation_data.action=None
for bone in rig.pose.bones:bone.rotation_euler=(0,0,0);bone.location=(0,0,0)
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.name!='cast_body':bpy.data.objects.remove(o,do_unlink=True)
body=bpy.data.objects['cast_body'];bm=bmesh.new();bm.from_mesh(body.data);weights=bm.verts.layers.deform.active
indices={g.index for g in body.vertex_groups if g.name=='head' or g.name.startswith('eye')}
remove=[v for v in bm.verts if any(v[weights].get(i,0)>.1 for i in indices)]
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(body.data);bm.free()
photo=bpy.data.images.load(str(ROOT/'webgl-prototype/assets/character-study/reference.jpg'),check_existing=True);photo.pack()
def plain(name,color,rough=.85):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');rgb=[int(color[k:k+2],16)/255 for k in (1,3,5)];rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb];bs.inputs['Base Color'].default_value=(*rgb,1);m.diffuse_color=(*rgb,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.18;return m
def textured(name):
 m=plain(name,'#ffffff');bs=m.node_tree.nodes.get('Principled BSDF');tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=photo;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);return m
skin=plain('portrait-side-skin','#d3a487');faceMat=textured('portrait-photo-skin');hairMat=textured('portrait-photo-hair');backHair=plain('portrait-silver-hair','#777b70')
W,H=photo.size;scale=.000596;originX=662.4;chin=992.06;yaw=.16
rotation=Matrix.Rotation(yaw,3,'Y')
def xyz(p):
 v=rotation@Vector(p);return (v.x,-v.z,v.y)
def pixel(x,y,z):return ((x-originX)*scale,1.03+(chin-y)*scale,z)
def make(name,verts,faces,material,uv=None,subdivide=0):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([xyz(p) for p in verts],[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 if uv:
  layer=mesh.uv_layers.new(name='PortraitUV')
  for poly in mesh.polygons:
   for loop in poly.loop_indices:layer.data[loop].uv=uv[mesh.loops[loop].vertex_index]
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
 for poly in mesh.polygons:poly.use_smooth=True
 if subdivide:
  mod=o.modifiers.new('Portrait surface refinement','SUBSURF');mod.levels=subdivide;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 group=o.vertex_groups.new(name='head');group.add(list(range(len(o.data.vertices))),1,'REPLACE');o.parent=rig;arm=o.modifiers.new('Portrait head follows skeleton','ARMATURE');arm.object=rig
 o['portrait_geometry']='Estimated depth from reference photograph; rigid head attachment';return o
source=json.loads((ROOT/'art-source/director-wu/portrait-surface-v04.json').read_text())
pts=source['points'];verts=[pixel(x,y,z) for x,y,z in pts];faces=[tuple(f) for f in source['triangles']]
edges={}
for f in faces:
 for i in range(3):e=tuple(sorted((f[i],f[(i+1)%3])));edges[e]=edges.get(e,0)+1
adj={}
for (a,b),n in edges.items():
 if n==1:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
assert all(len(v)==2 for v in adj.values()),'Head outline must be a simple loop'
start=min(adj,key=lambda i:pts[i][1]);hull=[start];prev=None
while True:
 nxt=next(i for i in adj[hull[-1]] if i!=prev)
 if nxt==start:break
 prev=hull[-1];hull.append(nxt)
assert len(hull)==len(adj),'Unexpected hole in portrait surface'
uv=[(x/W,1-y/H) for x,y,z in pts];frontCount=len(faces);last=hull;n=len(hull)
for depth,factor in [(-.015,.98),(-.085,.87),(-.145,.58),(-.18,.13)]:
 ring=[]
 for i in hull:
  x,y,z=verts[i];theta=math.atan2((y-1.28)/.26,x/.21);blend=.75 if depth==-.015 else 1
  rx=x*(1-blend)+.21*math.cos(theta)*blend;ry=(y-1.28)*(1-blend)+.26*math.sin(theta)*blend
  ring.append(len(verts));verts.append((rx*factor,1.28+ry*factor,depth));uv.append((.59,.57))
 for k in range(n):faces.append((last[k],last[(k+1)%n],ring[(k+1)%n],ring[k]))
 last=ring
faces.append(tuple(reversed(last)))
head=make('portrait_head',verts,faces,faceMat,uv,0);head.data.materials.append(skin);head.data.materials.append(backHair)
for f in head.data.polygons:
 if f.index>=frontCount:f.material_index=2 if f.center.z>1.30 else 1
mod=head.modifiers.new('Continuous portrait surface','SUBSURF');mod.levels=1;bpy.context.view_layer.objects.active=head;bpy.ops.object.modifier_apply(modifier=mod.name)
head.vertex_groups['head'].add(list(range(len(head.data.vertices))),1,'REPLACE')
head.data.validate(clean_customdata=False)
def cap(theta,t,lift=0):
 front=max(0,math.sin(theta));boundary=1.25+.13*front
 phi=t*math.acos((boundary-1.30)/.245)
 return ((.194+lift)*math.sin(phi)*math.cos(theta),1.30+(.245+lift)*math.cos(phi),-.015+(.175+lift)*math.sin(phi)*math.sin(theta))
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update();surface=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
# Subtle real strands on the posterior and sides. Photo hair carries frontal detail.
strandMats=[plain('silver-strand-'+str(i),color) for i,color in enumerate(['#7f8379','#a1a297','#686d62'])]
strands=[]
for k in range(100):
 theta=math.pi+.1+k/99*(math.pi-.2)
 curve=bpy.data.curves.new('swept-grey-strand','CURVE');curve.dimensions='3D';curve.bevel_depth=.0007;curve.bevel_resolution=0;curve.resolution_u=2
 sp=curve.splines.new('POLY');sp.points.add(7)
 for j,p in enumerate(sp.points):
  t=.18+j*.11;v=Vector(xyz(cap(theta+.38*(1-t),t)));nearest,normal,_,_=surface.find_nearest(v);p.co=(*(nearest+normal*.0006),1)
 o=bpy.data.objects.new('swept-grey-strand',curve);bpy.context.collection.objects.link(o);o.data.materials.append(strandMats[k%3]);strands.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in strands:o.select_set(True)
bpy.context.view_layer.objects.active=strands[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();o=bpy.context.object;o.name='portrait_hair_strands';o.parent=rig;vg=o.vertex_groups.new(name='head');vg.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Head attachment','ARMATURE');mod.object=rig
# Preserve all original body actions, without adding names to coat or scene labels.
rig.animation_data.action=None
for bone in rig.pose.bones:bone.rotation_euler=(0,0,0);bone.location=(0,0,0)
bpy.context.scene.frame_set(1)
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  if o.name.startswith('portrait_'):o.vertex_groups['head'].add(list(range(len(o.data.vertices))),1,'REPLACE')
  assert not o.data.validate(clean_customdata=False),o.name
bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v04.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_def_bones=False,export_leaf_bone=False,export_extras=True)
report={'version':'director-v04','source':'User supplied photograph + local MediaPipe depth estimate','facialAnimation':False,'bones':len(rig.data.bones),'actions':[a.name for a in bpy.data.actions],'bytes':(OUT/'director_wu.glb').stat().st_size,'meshes':[]}
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  o.data.calc_loop_triangles();report['meshes'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles)})
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('PORTRAIT_V04',json.dumps(report))
