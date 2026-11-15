"""Preserve approved frontal portrait; refine rigid side skull, color transition and ears."""
from pathlib import Path
import bpy,bmesh,math,json,random,hashlib
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'webgl-prototype/assets/characters/director-v05';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v04.blend')))
bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
bpy.context.scene.frame_set(1)
for o in list(bpy.data.objects):
 if o.name=='portrait_hair_strands':bpy.data.objects.remove(o,do_unlink=True)
head=bpy.data.objects['portrait_head'];mesh=head.data
rot=Matrix.Rotation(.16,3,'Y')
def author(v):return rot.inverted()@Vector((v.x,v.z,-v.y))
def xyz(v):
 p=rot@Vector(v);return Vector((p.x,-p.z,p.y))
front={v for f in mesh.polygons if f.material_index==0 for v in f.vertices}
originalFront={i:author(mesh.vertices[i].co) for i in front}
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
# Recess the photo's outer ear/cheek depth into the side skull. Its frontal x/y
# projection and central facial features remain fixed; only profile depth changes.
profileDepthChanges=0
for i in front:
 p=author(mesh.vertices[i].co);x=abs(p.x)
 ear=smooth(.158,.198,x)*smooth(1.14,1.18,p.y)*(1-smooth(1.29,1.33,p.y))
 cheek=smooth(.13,.20,x)*smooth(1.025,1.07,p.y)*(1-smooth(1.18,1.23,p.y))
 target=.16*math.sqrt(max(.04,1-(x/.215)**2));z=p.z*(1-cheek)+target*cheek;z=z*(1-ear)+.045*ear
 if abs(z-p.z)>1e-7:profileDepthChanges+=1;p.z=z;mesh.vertices[i].co=xyz(p)
frontProjectionError=max((Vector(author(mesh.vertices[i].co)[:2])-Vector(p[:2])).length for i,p in originalFront.items())
assert frontProjectionError<1e-6
locked=[tuple(mesh.vertices[i].co) for i in sorted(front)]
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
# Refine only side faces; original front edges are not subdivided.
edges=[e for e in bm.edges if not all(v.index in front for v in e.verts)]
bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
bm.to_mesh(mesh);bm.free();mesh.update()
front={v for f in mesh.polygons if f.material_index==0 for v in f.vertices}
# Lock every approved face vertex, including its perimeter. Relax only the side shell.
links=[set() for v in mesh.vertices]
for e in mesh.edges:
 a,b=e.vertices;links[a].add(b);links[b].add(a)
side=set(range(len(mesh.vertices)))-front
for _ in range(10):
 smooth={i:sum((mesh.vertices[j].co for j in links[i]),Vector())/len(links[i]) for i in side if links[i]}
 for i,p in smooth.items():mesh.vertices[i].co=mesh.vertices[i].co.lerp(p,.32)
# The same original photo colors are carried continuously across the profile seam.
uvs=mesh.uv_layers.active.data;frontUV={}
for f in mesh.polygons:
 if f.material_index==0:
  for li in f.loop_indices:frontUV[mesh.loops[li].vertex_index]=tuple(uvs[li].uv)
boundary={i for f in mesh.polygons if f.material_index!=0 for i in f.vertices if i in front}
kd=KDTree(len(boundary))
for i in boundary:kd.insert(mesh.vertices[i].co,i)
kd.balance()
photo=next(i for i in bpy.data.images if i.name.startswith('reference.jpg'));W,H=photo.size;pixels=list(photo.pixels)
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def sample(uv):
 x=max(0,min(W-2,uv[0]*W-.5));y=max(0,min(H-2,uv[1]*H-.5));ix,iy=int(x),int(y);fx,fy=x-ix,y-iy
 c=[0.,0.,0.]
 for ox,oy,w in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
  for k in range(3):c[k]+=pixels[((iy+oy)*W+ix+ox)*4+k]*w
 return Vector([linear(v) for v in c])
def at(x,y):return sample((x/W,1-y/H))
skin=Vector([linear(v/255) for v in [211,165,133]]);hair=Vector([linear(v/255) for v in [140,144,133]])
def clean_uv(uv):
 x,y=uv[0]*W,(1-uv[1])*H
 if y<800:
  for _ in range(45):
   c=at(x,y)
   if c.z<=c.x*1.05:break
   x+=1 if x<662 else -1;y+=.25
 return (x/W,1-y/H)
def clean_edge(uv):
 x,y=uv[0]*W,(1-uv[1])*H
 c=sample(uv)
 # Extend the hair's interior color, excluding photographed blue backdrop.
 if y<800:
  c=at(x+(662-x)*.065,y+10)
  if c.z>c.x*1.1:c=hair.copy()
 return c
def hairline(p):
 # Sideburns above the ear; lower, curved nape at the rear.
 return 1.165+.118*max(0,min(1,(p.z+.12)/.24))+.015*abs(p.x)/.21
# Remove only blue backdrop contamination at the outer hair UV edge.
for f in mesh.polygons:
 if f.material_index==0:
  for li in f.loop_indices:
   vi=mesh.loops[li].vertex_index
   if ((uvs[li].uv.x*W<430 or uvs[li].uv.x*W>940) and (1-uvs[li].uv.y)*H<800):
    uv=clean_uv(tuple(uvs[li].uv));uvs[li].uv=uv;frontUV[vi]=uv
hairPhoto=mesh.materials[0].copy();hairPhoto.name='profile-silver-photo-detail';mesh.materials.append(hairPhoto);hairMaterialIndex=len(mesh.materials)-1
colors=mesh.color_attributes.new(name='ProfileColor',type='FLOAT_COLOR',domain='CORNER')
mat=bpy.data.materials.new('continuous-profile-colors');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85;bs.inputs['Specular IOR Level'].default_value=.18
vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='ProfileColor';mat.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat);profileMaterial=len(mesh.materials)-1
for f in mesh.polygons:
 if f.material_index==0:
  for li in f.loop_indices:colors.data[li].color=(1,1,1,1)
  continue
 f.material_index=profileMaterial
 for li in f.loop_indices:
  vi=mesh.loops[li].vertex_index;v=mesh.vertices[vi].co;p=author(v);_,bi,d=kd.find(v);edge=clean_edge(frontUV[bi]);blend=1-math.exp(-(d/.025)**2)
  h=max(0,min(1,(p.y-hairline(p))/.018));h=h*h*(3-2*h)
  base=skin.lerp(hair,h);grain=1+.025*math.sin(p.x*1447+p.y*813)*math.sin(p.z*1067)
  c=edge.lerp(base*grain,blend);colors.data[li].color=(*c,1)
mesh.update()
def plain(name,c):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Roughness'].default_value=.86;b.inputs['Specular IOR Level'].default_value=.18;return m
def bind(o):
 o.parent=rig;g=o.vertex_groups.new(name='head');g.add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Rigid head attachment','ARMATURE');mod.object=rig
 for f in o.data.polygons:f.use_smooth=True
# Layered auricles: helix rim, antihelix and recessed concha, closed on the rear.
bpy.context.view_layer.update();earSurface=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
def earx(sign,y,z,lift=0):
 hit,_,_,_=earSurface.ray_cast(xyz((sign*.5,y,z)),xyz((-sign,0,0)))
 return (author(hit).x if hit is not None else sign*.18)+sign*lift
earMats=[plain('auricle-skin',skin),plain('auricle-inner',skin*.92),plain('auricle-rim',skin*1.04)]
for sign in [-1,1]:
 vs=[];fs=[];N=48
 for radius,bulge in [(1,0),(.90,.005),(.75,.009),(.55,.002),(.30,0)]:
  for k in range(N):
   a=2*math.pi*k/N;y=1.235+.052*radius*math.cos(a);z=.032+.027*radius*math.sin(a)*(.87+.13*math.cos(a))+.010*math.cos(a);x=earx(sign,y,z,bulge-.001)
   vs.append(xyz((x,y,z)))
 for j in range(4):
  for k in range(N):fs.append((j*N+k,j*N+(k+1)%N,(j+1)*N+(k+1)%N,(j+1)*N+k))
 vs.append(xyz((earx(sign,1.235,.032,.001),1.235,.032)));center=len(vs)-1
 for k in range(N):fs.append((4*N+k,4*N+(k+1)%N,center))
 fs.append(tuple(reversed(range(N))))
 me=bpy.data.meshes.new('auricle');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('portrait_ear_'+('right' if sign>0 else 'left'),me);bpy.context.collection.objects.link(o)
 for m in earMats:me.materials.append(m)
 for f in me.polygons:f.material_index=2 if f.index<2*N else (1 if f.index>=3*N else 0)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();bind(o)

 # Antihelix folds and tragus break the simple oval into an anatomical auricle.
 for branch,shape in enumerate([[(1.207,.026),(1.217,.023),(1.232,.025),(1.245,.031),(1.263,.032)],[(1.242,.029),(1.252,.018),(1.268,.016)]]):
  curve=bpy.data.curves.new('antihelix','CURVE');curve.dimensions='3D';curve.bevel_depth=.0018;curve.bevel_resolution=1
  sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(shape)-1)
  for v,(y,z) in zip(sp.bezier_points,shape):v.co=xyz((earx(sign,y,z,.006),y,z));v.handle_left_type='AUTO';v.handle_right_type='AUTO'
  fold=bpy.data.objects.new('portrait_ear_fold',curve);bpy.context.collection.objects.link(fold);fold.data.materials.append(earMats[0]);bpy.ops.object.select_all(action='DESELECT');fold.select_set(True);bpy.context.view_layer.objects.active=fold;bpy.ops.object.convert(target='MESH');bind(fold)

# Short silver strands conform to the side/rear shell instead of a floating cap.
bpy.context.view_layer.update();bvh=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get());rng=random.Random(20261113)
strandMats=[plain('silver-fiber-'+str(i),hair*f) for i,f in enumerate([.45,.8,1.1,1.5,1.9])]
hairVerts=[];hairFaces=[];hairMaterial=[]
for k in range(7200):
 theta=rng.uniform(0,2*math.pi);phi=rng.uniform(.05,1.86);pts=[];normals=[]
 for j in range(7):
  a=theta+.12*j/6;q=phi+.12*j/6;candidate=xyz((.20*math.sin(q)*math.cos(a),1.30+.245*math.cos(q),-.02+.18*math.sin(q)*math.sin(a)))
  pos,normal,face,d=bvh.find_nearest(candidate)
  if pos is None:break
  local=author(pos)
  if local.y<hairline(local)+.006 or mesh.polygons[face].material_index==0:break
  pts.append(pos+normal*.0007);normals.append(normal)
 if len(pts)<4:continue
 start=len(hairVerts);width=rng.uniform(.00035,.00075)
 for j,pos in enumerate(pts):
  tangent=pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)];across=normals[j].cross(tangent).normalized()*width*(1-.7*j/(len(pts)-1));hairVerts.extend([pos-across,pos+across])
 for j in range(len(pts)-1):hairFaces.append((start+j*2,start+j*2+1,start+j*2+3,start+j*2+2));hairMaterial.append(k%len(strandMats))
me=bpy.data.meshes.new('silver-hair-ribbons');me.from_pydata(hairVerts,[],hairFaces);me.update();o=bpy.data.objects.new('portrait_hair_strands',me);bpy.context.collection.objects.link(o)
for m in strandMats:me.materials.append(m)
for f,i in zip(me.polygons,hairMaterial):f.material_index=i
bind(o)
assert set(locked).issubset({tuple(mesh.vertices[i].co) for i in front}),'Approved front geometry changed'
bm=bmesh.new();bm.from_mesh(mesh);manifold=sum(not e.is_manifold for e in bm.edges);bm.free();assert manifold==0
for o in bpy.context.scene.objects:
 if o.type=='MESH':assert not o.data.validate(clean_customdata=False),o.name
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v05.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,export_def_bones=False,export_leaf_bone=False,export_extras=True)
report={'version':'director-v05','frontLockedVertices':len(front),'frontProjectionMaxError':frontProjectionError,'outerProfileDepthAdjustedVertices':profileDepthChanges,'centralFacialFeaturesUnchanged':True,'source':'Approved v04 front; estimated profile and posterior','facialAnimation':False,'headNonManifoldEdges':manifold,'bones':len(rig.data.bones),'actions':[a.name for a in bpy.data.actions],'bytes':(OUT/'director_wu.glb').stat().st_size,'meshes':[]}
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.data.calc_loop_triangles();report['meshes'].append({'name':o.name,'triangles':len(o.data.loop_triangles)})
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('PORTRAIT_V05',json.dumps(report))
