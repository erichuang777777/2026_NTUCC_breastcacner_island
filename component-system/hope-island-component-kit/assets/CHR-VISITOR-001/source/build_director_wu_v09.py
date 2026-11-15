"""Add true 3D eyes/brows and vertex-colored skin/lips to accepted v08 form."""
from pathlib import Path
import bpy,bmesh,json,math,random,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[5];OUT=ROOT/'webgl-prototype/assets/characters/director-v09';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v08.blend')))
bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2
head=bpy.data.objects['anatomy_head_and_neck'];eyes=bpy.data.objects['anatomy_eyes'];deps=bpy.context.evaluated_depsgraph_get()
# Freeze evaluated accepted form: no new sculpt in this appearance-only pass.
for o in [head,eyes]:
 baked=bpy.data.meshes.new_from_object(o.evaluated_get(deps),depsgraph=deps);o.modifiers.clear();o.data=baked
 for p in o.data.polygons:p.use_smooth=True
original=[tuple(v.co) for v in head.data.vertices]
def mat(name,color,rough=.6,vertex=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.28
 if vertex:
  vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Color';m.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color'])
 return m
def colors(mesh,fn):
 c=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
 for v in mesh.vertices:c.data[v.index].color=(*fn(v.co),1)
 mesh.color_attributes.active_color=c
skin=mat('warm-skin-and-lips',(1,1,1),.68,True);head.data.materials.clear();head.data.materials.append(skin)
def mix(a,b,t):return tuple(x*(1-t)+y*t for x,y in zip(a,b))
def skin_color(p):
 x,y,z=p;front=max(0,min(1,(-y-.10)/.06));a=abs(x)
 skin=(.43,.255,.163)
 cheek=math.exp(-((a-.100)/.06)**2-((z-1.20)/.05)**2)*front
 skin=mix(skin,(.46,.235,.165),.22*cheek)
 # Blend vermilion along the actual lip plane, with soft taper at corners.
 center=1.118+.003*math.exp(-((a-.054)/.024)**2)
 height=.010*max(.12,1-(a/.065)**2)
 lip=math.exp(-((z-center)/max(.002,height))**4-(a/.061)**8)*front
 skin=mix(skin,(.32,.137,.114),.67*lip)
 lower=math.exp(-((z-1.106)/.007)**4-(a/.050)**6)*front
 skin=mix(skin,(.39,.185,.155),.58*lower)
 # Warm eyelid edge; avoid painting a black eyeliner line on the face.
 lid=math.exp(-((a-.069)/.040)**4-((z-1.273)/.020)**4)*front
 skin=mix(skin,(.35,.204,.151),.10*lid)
 return skin
colors(head.data,skin_color)
sclera=mat('warm-ivory-sclera',(.69,.68,.62),.28);eyes.data.materials.clear();eyes.data.materials.append(sclera)
headBVH=BVHTree.FromPolygons([v.co for v in head.data.vertices],[list(p.vertices) for p in head.data.polygons]);eyeBVH=BVHTree.FromPolygons([v.co for v in eyes.data.vertices],[list(p.vertices) for p in eyes.data.polygons])
def frontpoint(tree,x,z,offset=.0002):
 hit,n,idx,dist=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2)
 assert hit is not None,(x,z)
 return hit+Vector((0,-offset,0))
def object_mesh(name,verts,faces,material):
 m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(material)
 for p in m.polygons:p.use_smooth=True
 return o
irisMat=mat('brown-iris-pupil',(1,1,1),.23,True);ibs=irisMat.node_tree.nodes.get('Principled BSDF');ibs.inputs['Coat Weight'].default_value=.6;ibs.inputs['Coat Roughness'].default_value=.12
added=[]
for side in [-1,1]:
 cx=side*.06758;cz=1.27236;verts=[];cols=[];faces=[];N=96;rings=[0,.0038,.0042,.006,.0085,.0105,.0114]
 for radius in rings:
  for k in range(N):
   theta=2*math.pi*k/N;x=cx+radius*math.cos(theta);z=cz+radius*math.sin(theta);verts.append(frontpoint(eyeBVH,x,z))
   if radius<=.0038:c=(.002,.0015,.0012)
   elif radius>=.0105:c=(.013,.008,.006)
   else:
    grain=.80+.16*math.sin(theta*37)+.09*math.sin(theta*71+radius*900)
    c=(.065*grain,.031*grain,.013*grain)
   cols.append(c)
 for j in range(len(rings)-1):
  for k in range(N):a=j*N+k;b=j*N+(k+1)%N;faces.append((a,b,b+N,a+N))
 # Merge coincident central vertices to avoid zero-area triangles.
 o=object_mesh('feature_iris_'+str(side),verts,faces,irisMat);colors(o.data,lambda p:(1,1,1));c=o.data.color_attributes['Color']
 for i,v in enumerate(cols):c.data[i].color=(*v,1)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();added.append(o)
# A surface-fitted soft brow foundation prevents fine hairs becoming isolated dots.
browBaseMat=mat('soft-brow-foundation',(1,1,1),.78,True)
for side in [-1,1]:
 verts=[];faces=[];cols=[];N=56;rows=9
 for j in range(N):
  t=j/(N-1);x=side*(.027+.095*t)
  arch=1.318+.012*math.sin(math.pi*t)-.007*t
  width=.0075*(max(.015,math.sin(math.pi*t))**.55)
  for k in range(rows):
   q=2*k/(rows-1)-1;z=arch+q*width;v=frontpoint(headBVH,x,z,.00018);verts.append(v)
   density=.66*(max(0,1-q*q)**1.4)*(math.sin(math.pi*t)**.35)
   cols.append(mix(skin_color(v),(.068,.049,.036),density))
 for j in range(N-1):
  for k in range(rows-1):a=j*rows+k;faces.append((a,a+1,a+1+rows,a+rows))
 o=object_mesh('feature_brow_base_'+str(side),verts,faces,browBaseMat);colors(o.data,lambda p:(1,1,1))
 for i,c in enumerate(cols):o.data.color_attributes['Color'].data[i].color=(*c,1)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();added.append(o)
browMat=mat('salt-pepper-brow' ,(1,1,1),.85,True)
rng=random.Random(23220322)
for side in [-1,1]:
 verts=[];faces=[];cols=[]
 for h in range(240):
  t=(h+rng.random())/240;x0=.028+.092*t
  arch=1.318+.012*math.sin(math.pi*t)-.007*t
  thickness=.0065*(math.sin(math.pi*t)**.5)
  z0=arch+rng.uniform(-1,1)*thickness
  length=rng.uniform(.003,.007);width=rng.uniform(.00023,.00036)*(1-.4*t)
  gray=rng.random()<.28;c=(.13,.12,.105) if gray else (.035,.027,.021)
  start=len(verts)
  for j in range(5):
   u=j/4;x=side*(x0+length*u*(.4+.6*t));z=z0+length*.65*math.sin(u*math.pi*.65)
   center=frontpoint(headBVH,x,z,.00038)
   for k in range(4):
    th=2*math.pi*k/4;v=center+Vector((math.cos(th)*width*(1-.88*u),-math.sin(th)*width*(1-.88*u),0));verts.append(v);cols.append(c)
  for j in range(4):
   for k in range(4):a=start+j*4+k;b=start+j*4+(k+1)%4;faces.append((a,b,b+4,a+4))
 o=object_mesh('feature_brow_'+str(side),verts,faces,browMat);colors(o.data,lambda p:(1,1,1));c=o.data.color_attributes['Color']
 for i,v in enumerate(cols):c.data[i].color=(*v,1)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();added.append(o)
assert original==[tuple(v.co) for v in head.data.vertices]
report={'version':'director-v09','stage':'facial-appearance-study','base':'director-v08','acceptedHeadGeometryUnchanged':True,'photoProjection':False,'facialRig':False,'bodyAnimation':False,'features':['3D fitted sclera','surface-fitted brown iris and pupils','individual gray-brown eyebrow strands','vertex-colored skin and lips'],'meshes':[]}
for o in [head,eyes]+added:
 assert not o.data.validate(clean_customdata=False),o.name
 assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
 o.data.calc_loop_triangles();report['meshes'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles)})
head['stage']='Facial appearance study; likeness not final';head['base_version']='director-v08'
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v09.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True)
report['bytes']=(OUT/'director_wu.glb').stat().st_size;(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('FEATURE_STUDY',json.dumps(report))
