"""Rebuild the posterior cranium and mandible; preserve approved central face."""
from pathlib import Path
import bpy,bmesh,math,json
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[5];OUT=ROOT/'webgl-prototype/assets/characters/director-v06';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v05.blend')))
bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
bpy.context.scene.frame_set(1)
rot=Matrix.Rotation(.16,3,'Y')
def author(v):return rot.inverted()@Vector((v.x,v.z,-v.y))
def xyz(p):
 v=rot@Vector(p);return Vector((v.x,-v.z,v.y))
head=bpy.data.objects['portrait_head'];old=head.data;frontFaces=[f for f in old.polygons if f.material_index==0];frontIDs=sorted({i for f in frontFaces for i in f.vertices});remap={i:j for j,i in enumerate(frontIDs)}
verts=[author(old.vertices[i].co) for i in frontIDs];faces=[tuple(remap[i] for i in f.vertices) for f in frontFaces];UV={}
for f in frontFaces:
 for li in f.loop_indices:UV[remap[old.loops[li].vertex_index]]=tuple(old.uv_layers.active.data[li].uv)
frontCount=len(faces);frontVertexCount=len(verts);edges={}
for f in faces:
 for a,b in zip(f,f[1:]+f[:1]):e=tuple(sorted((a,b)));edges[e]=edges.get(e,0)+1
adj={}
for (a,b),n in edges.items():
 if n==1:adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
assert all(len(v)==2 for v in adj.values())
start=max(adj,key=lambda i:verts[i].y);hull=[start];prev=None
while True:
 nxt=next(i for i in adj[hull[-1]] if i!=prev)
 if nxt==start:break
 prev=hull[-1];hull.append(nxt)
assert len(hull)==len(adj)
# Elliptical cranial vault, with lower rings returning upward to the nape.
# Unlike v04/v05, the chin outline is not extruded through the whole rear skull.
cx,cy,rx,ry=.008,1.295,.192,.255
last=hull;n=len(hull)
lengths=[0.]
for a,b in zip(hull,hull[1:]+hull[:1]):lengths.append(lengths[-1]+(Vector(verts[a][:2])-Vector(verts[b][:2])).length)
orientation=-1 if verts[hull[1]].x>verts[start].x else 1
thetas={i:math.pi/2+orientation*2*math.pi*lengths[k]/lengths[-1] for k,i in enumerate(hull)}
for step in range(1,25):
 phi=(math.pi/2)*step/25;cs,sn=math.cos(phi),math.sin(phi);blend=1-math.exp(-phi*8);ring=[]
 for i in hull:
  p=verts[i];theta=thetas[i]
  ex=cx+rx*math.cos(theta);ey=cy+ry*math.sin(theta)
  x=cx+((p.x-cx)*(1-blend)+(ex-cx)*blend)*cs
  y=cy+((p.y-cy)*(1-blend)+(ey-cy)*blend)*cs+.13*sn*cs*(1-math.sin(theta))*.5
  z=(p.z*math.exp(-phi*6)+.025*(1-math.exp(-phi*6)))*cs-.125*sn
  ring.append(len(verts));verts.append(Vector((x,y,z)))
 for k in range(n):faces.append((last[k],last[(k+1)%n],ring[(k+1)%n],ring[k]))
 last=ring
center=len(verts);verts.append(Vector((cx,cy,-.125)))
for k in range(n):faces.append((last[k],last[(k+1)%n],center))
mesh=bpy.data.meshes.new('anatomical-cranium-v06');mesh.from_pydata([xyz(v) for v in verts],[],faces);mesh.update()
mesh.materials.append(old.materials[0]);profile=next(m for m in old.materials if m.name.startswith('continuous-profile'));mesh.materials.append(profile)
uv=mesh.uv_layers.new(name='PortraitUV');colors=mesh.color_attributes.new(name='ProfileColor',type='FLOAT_COLOR',domain='CORNER')
photo=next(i for i in bpy.data.images if i.name.startswith('reference.jpg'));W,H=photo.size;pixels=list(photo.pixels)
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def sample(uv):
 x=max(0,min(W-1,int(uv[0]*W)));y=max(0,min(H-1,int(uv[1]*H)));return Vector([linear(pixels[(y*W+x)*4+k]) for k in range(3)])
skin=Vector([linear(v/255) for v in [211,165,133]]);hair=Vector([linear(v/255) for v in [140,144,133]])
kd=KDTree(n)
for i in hull:kd.insert(verts[i],i)
kd.balance()
def hairline(p):return 1.19+.10*max(0,min(1,(p.z+.12)/.24))
for f in mesh.polygons:
 f.use_smooth=True;f.material_index=0 if f.index<frontCount else 1
 for li in f.loop_indices:
  vi=mesh.loops[li].vertex_index;p=verts[vi]
  if f.index<frontCount:uv.data[li].uv=UV[vi];colors.data[li].color=(1,1,1,1);continue
  _,bi,d=kd.find(p);edge=sample(UV[bi]);h=max(0,min(1,(p.y-hairline(p))/.018));h=h*h*(3-2*h);base=skin.lerp(hair,h)
  if edge.z>edge.x*1.05:edge=base
  c=edge.lerp(base,1-math.exp(-(d/.028)**2));colors.data[li].color=(*c,1);uv.data[li].uv=UV[bi]
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
head.data=mesh;group=head.vertex_groups.get('head') or head.vertex_groups.new(name='head');group.add(list(range(len(mesh.vertices))),1,'REPLACE')
bpy.context.view_layer.update();surface=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
# Refit existing attached hairs onto the new skull without increasing density.
hairObject=bpy.data.objects.get('portrait_hair_strands')
if hairObject:
 for v in hairObject.data.vertices:
  point,normal,_,_=surface.find_nearest(v.co)
  if point is not None:v.co=point+normal*.0007
 hairObject.data.update()
# Preserve the previous auricle placement to avoid widening the approved frontal outline.
# Refit the existing neck into the new underside of the jaw; leave hands/clothing alone.
body=bpy.data.objects['cast_body'];skinIDs={i for f in body.data.polygons if body.data.materials[f.material_index].name=='skin' for i in f.vertices}
for i in skinIDs:
 v=body.data.vertices[i]
 if v.co.z<=.96:continue
 t=max(0,min(1,(v.co.z-.96)/.151));t=t*t*(3-2*t)
 v.co.z+=.105*t;v.co.y-=.04*t
body.data.update()
# Quantitative guard: the approved front vertices and UVs are carried through.
frontError=max((mesh.vertices[j].co-old.vertices[i].co).length for i,j in remap.items());assert frontError<1e-6
bm=bmesh.new();bm.from_mesh(mesh);nonManifold=sum(not e.is_manifold for e in bm.edges);bm.free();assert nonManifold==0
for o in bpy.context.scene.objects:
 if o.type=='MESH':assert not o.data.validate(clean_customdata=False),o.name
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v06.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_def_bones=False,export_leaf_bone=False,export_extras=True)
report={'version':'director-v06','source':'Approved front from v05; rebuilt cranial vault and mandible','frontVertices':frontVertexCount,'frontGeometryMaxError':frontError,'headNonManifoldEdges':nonManifold,'neckRefit':True,'facialAnimation':False,'bytes':(OUT/'director_wu.glb').stat().st_size,'bones':len(rig.data.bones),'actions':[a.name for a in bpy.data.actions],'meshes':[]}
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();report['meshes'].append({'name':o.name,'triangles':len(o.data.loop_triangles)})
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('PORTRAIT_V06',json.dumps(report))
