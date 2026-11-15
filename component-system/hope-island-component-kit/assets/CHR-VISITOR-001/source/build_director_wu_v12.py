"""Screen-registered likeness correction using measured reference/render landmarks.
Preserves anatomical depth; changes proportions instead of adding generic detail.
"""
from pathlib import Path
import bpy,bmesh,json,math,struct
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[5];OUT=ROOT/'webgl-prototype/assets/characters/director-v12';OUT.mkdir(parents=True,exist_ok=True)
ref=json.loads((ROOT/'art-source/director-wu/face-landmarks.json').read_text());seen=json.loads((ROOT/'art-source/director-wu/v12-render-landmarks.json').read_text());rp=np.array(ref['points'])[:,:2]*ref['size'];sp=np.array(seen['points'])[:,:2]*seen['size'];W,H=seen['size'];ppw=H/.65;ang=-.16;ca,sa=math.cos(ang),math.sin(ang)
scale=np.linalg.norm(sp[33]-sp[263])/np.linalg.norm(rp[33]-rp[263]);shift=(sp[33]+sp[263])/2-scale*(rp[33]+rp[263])/2
ids=list(dict.fromkeys(ref['oval']+[33,133,263,362,159,145,386,374,70,105,107,300,334,336,168,1,4,98,327,2,61,291,0,13,14,17,37,267,84,314,234,454]))
def world(q):return np.column_stack([.018+(q[:,0]-W/2)/ppw,1.26+(H/2-q[:,1])/ppw])
X=world(sp[ids]);Y=world(rp[ids]*scale+shift)-X
# Fix the lower neck and the distant rear/cranium field for a smooth local transition.
locks=np.array([[-.35,.85],[0,.85],[.35,.85],[-.35,1.35],[.35,1.35],[-.30,1.70],[0,1.70],[.30,1.70]])
X=np.vstack([X,locks]);Y=np.vstack([Y,np.zeros((len(locks),2))])
def kernel(d):return d*d*np.log(np.maximum(d,1e-12))
D=np.linalg.norm(X[:,None,:]-X[None,:,:],axis=2);P=np.column_stack([np.ones(len(X)),X]);A=np.block([[kernel(D)+np.eye(len(X))*2e-5,P],[P.T,np.zeros((3,3))]]);coef=np.linalg.solve(A,np.vstack([Y,np.zeros((3,2))]))
def delta(q):
 d=np.linalg.norm(q[:,None,:]-X[None,:,:],axis=2);return kernel(d)@coef[:len(X)]+np.column_stack([np.ones(len(q)),q])@coef[len(X):]
def project(p):return (p.x*ca-p.y*sa,p.z)
def photo(p):
 u,z=project(p);px=W/2+(u-.018)*ppw;py=H/2-(z-1.26)*ppw;return ((px-shift[0])/scale,(py-shift[1])/scale)
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v11.blend')));scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2
# Existing synthetic eyebrows compete with the photographed brow, so remove that overlay.
if bpy.data.objects.get('detail_brow_hairs'):bpy.data.objects.remove(bpy.data.objects['detail_brow_hairs'],do_unlink=True)
changes=[]
for name in ['anatomy_head_and_neck','anatomy_eyes','detail_corneal_highlight']:
 o=bpy.data.objects[name];q=np.array([project(v.co) for v in o.data.vertices]);disp=delta(q);maxmove=0
 for v,d in zip(o.data.vertices,disp):
  x,y,z=v.co;depth=-x*sa-y*ca;weight=smooth(-.015,.11,depth)*smooth(.91,1.00,z) if name=='anatomy_head_and_neck' else 1
  du,dz=d*weight;v.co+=Vector((ca*du,-sa*du,dz));maxmove=max(maxmove,math.hypot(du,dz))
 o.data.update();changes.append({'mesh':name,'maxDisplacement':maxmove})
# Relax the open lip seam toward the reference's closed-mouth expression.
# This monotonic vertical compression preserves the surrounding lip loops.
head=bpy.data.objects['anatomy_head_and_neck']
for v in head.data.vertices:
 px,py=photo(v.co);depth=-v.co.x*sa-v.co.y*ca
 # Reference lip seam rises toward each corner, with slight photo asymmetry.
 t=(px-645)/94;seam=841.8-10*t*t-6*t
 dz=-(py-seam)*scale/ppw
 weight=math.exp(-((px-645)/105)**8-(dz/.022)**4)*smooth(.09,.14,depth)
 v.co.z-=.003*math.tanh(dz/.006)*weight
head.data.update()
# The reference hairstyle is wider and higher than the close-cut cap in v11.
for o in bpy.context.scene.objects:
 if o.type=='MESH' and ('hair_foundation' in o.name or 'silver_strands' in o.name or 'temporal_wisps' in o.name):
  for v in o.data.vertices:
   x,y,z=v.co;u=x*ca-y*sa;depth=-x*sa-y*ca
   u=(u-.005)*1.16+.005;z=1.27+(z-1.27)*1.22
   v.co=(ca*u-sa*depth,-sa*u-ca*depth,z)
  o.data.update()
# Hair silhouette traced on the reference: source image remains unchanged.
poly=[(670,126),(780,145),(870,190),(945,265),(984,345),(995,435),(975,520),(945,575),(898,550),(865,473),(831,427),(780,402),(720,382),(660,372),(610,380),(555,385),(505,400),(458,435),(420,512),(402,584),(365,541),(338,454),(343,362),(374,278),(433,223),(500,182),(585,147)]
def inside(x,y):
 yes=False
 for i,(ax,ay) in enumerate(poly):
  bx,by=poly[i-1]
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:yes=not yes
 return yes
def edge_distance(x,y):
 ds=[]
 for i,(ax,ay) in enumerate(poly):
  bx,by=poly[i-1];vx,vy=bx-ax,by-ay;t=max(0,min(1,((x-ax)*vx+(y-ay)*vy)/(vx*vx+vy*vy)));ds.append(math.hypot(x-ax-t*vx,y-ay-t*vy))
 return min(ds)
# Remove frontal micro-strands outside the actual reference hairstyle silhouette.
for name in ['detail_swept_silver_strands','detail_temporal_wisps']:
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);remove=[]
 for v in bm.verts:
  depth=-v.co.x*sa-v.co.y*ca;px,py=photo(v.co)
  if depth>.055 or (depth>.015 and not inside(px,py)):remove.append(v)
 bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free()
 # Reduce bright repeated strokes; the photographed hair carries the frontal pattern.
 attr=o.data.color_attributes.get('Color')
 if attr:
  for c in attr.data:c.color=(c.color[0]*.7,c.color[1]*.7,c.color[2]*.7,c.color[3])
o=bpy.data.objects['detail_hair_foundation'];mesh=o.data;photoUV=mesh.uv_layers.get('PhotoHair');atlas=mesh.uv_layers.get('HairAtlas');mask=mesh.color_attributes.new(name='ReferenceHairWeight',type='FLOAT_COLOR',domain='POINT');edge=mesh.color_attributes.get('Color')
for v in mesh.vertices:
 px,py=photo(v.co);depth=-v.co.x*sa-v.co.y*ca;weight=smooth(-.02,.12,depth);distance=edge_distance(px,py);coverage=smooth(0,12,distance) if inside(px,py) else 0
 mask.data[v.index].color=(weight*coverage,)*3+(1,)
 if edge:
  alpha=edge.data[v.index].color[3];edge.data[v.index].color=(1,1,1,alpha*(1-weight+weight*coverage))
for face in mesh.polygons:
 for li in face.loop_indices:
  px,py=photo(mesh.vertices[mesh.loops[li].vertex_index].co);photoUV.data[li].uv=(px/ref['size'][0],1-py/ref['size'][1])
# Bake the registered photo into the existing non-overlapping atlas.
m=bpy.data.materials.new('registered-reference-hair');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');emit=n.new('ShaderNodeEmission');l.new(emit.outputs[0],out.inputs[0]);tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'webgl-prototype/assets/character-study/reference.jpg'),check_existing=True);tex.extension='EXTEND';uv=n.new('ShaderNodeUVMap');uv.uv_map='PhotoHair';l.new(uv.outputs[0],tex.inputs[0]);mix=n.new('ShaderNodeMixRGB');vc=n.new('ShaderNodeVertexColor');vc.layer_name='ReferenceHairWeight';l.new(vc.outputs['Color'],mix.inputs[0]);mix.inputs[1].default_value=(.18,.19,.165,1);back=n.new('ShaderNodeTexImage');back.image=bpy.data.images.load(str(ROOT/'webgl-prototype/assets/characters/director-v11/hair-atlas.png'),check_existing=True);buv=n.new('ShaderNodeUVMap');buv.uv_map='HairAtlas';l.new(buv.outputs[0],back.inputs[0]);l.new(back.outputs['Color'],mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],emit.inputs[0]);img=bpy.data.images.new('v12-reference-hair',width=2048,height=2048,alpha=False);dest=n.new('ShaderNodeTexImage');dest.image=img;n.active=dest;mesh.materials.clear();mesh.materials.append(m);mesh.uv_layers.active=atlas;atlas.active_render=True
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.margin=12;bpy.ops.object.bake(type='EMIT');img.filepath_raw=str(OUT/'hair-atlas.png');img.file_format='PNG';img.save();img.pack()
n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.8;bs.inputs['Specular IOR Level'].default_value=.15;uv=n.new('ShaderNodeUVMap');uv.uv_map='HairAtlas';tx=n.new('ShaderNodeTexImage');tx.image=img;l.new(uv.outputs[0],tx.inputs['Vector']);l.new(tx.outputs[0],bs.inputs['Base Color']);vc=n.new('ShaderNodeVertexColor');vc.layer_name='Color';l.new(vc.outputs['Alpha'],bs.inputs['Alpha']);l.new(bs.outputs[0],out.inputs[0]);m.surface_render_method='BLENDED';mesh.color_attributes.remove(mask)
# Reproject the registered face after the proportion edit, extending the real
# forehead material up to the hairline instead of retaining v10's bald color band.
sourceimg=bpy.data.images.load(str(ROOT/'webgl-prototype/assets/character-study/reference.jpg'),check_existing=True)
for obj in [bpy.data.objects['anatomy_head_and_neck'],bpy.data.objects['anatomy_eyes']]:
 mesh=obj.data;iseye=obj.name=='anatomy_eyes';uvlayer=mesh.uv_layers['PhotoRegistration'];atlas=mesh.uv_layers['BakedAtlas']
 coverage=mesh.color_attributes.new(name='PhotoCoverageV12',type='FLOAT_COLOR',domain='POINT')
 for v in mesh.vertices:
  px,py=photo(v.co);depth=-v.co.x*sa-v.co.y*ca
  amount=1 if iseye else smooth(.025,.125,depth)*smooth(350,405,px)*(1-smooth(920,995,px))*smooth(330,385,py)*(1-smooth(980,1050,py))
  coverage.data[v.index].color=(amount,amount,amount,1)
 for face in mesh.polygons:
  for li in face.loop_indices:
   px,py=photo(mesh.vertices[mesh.loops[li].vertex_index].co);uvlayer.data[li].uv=(px/ref['size'][0],1-py/ref['size'][1])
 mat=bpy.data.materials.new('registered-likeness-'+obj.name);mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs[0]);tx=n.new('ShaderNodeTexImage');tx.image=sourceimg;tx.extension='EXTEND';uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='PhotoRegistration';l.new(uvnode.outputs[0],tx.inputs[0]);gain=n.new('ShaderNodeMixRGB');gain.blend_type='MULTIPLY';gain.inputs[0].default_value=1;gain.inputs[2].default_value=(.75,.75,.75,1);l.new(tx.outputs[0],gain.inputs[1]);mix=n.new('ShaderNodeMixRGB');vc=n.new('ShaderNodeVertexColor');vc.layer_name='PhotoCoverageV12';l.new(vc.outputs[0],mix.inputs[0]);mix.inputs[1].default_value=(.43,.255,.163,1);l.new(gain.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],em.inputs[0]);img=bpy.data.images.new('v12-eye' if iseye else 'v12-face',width=1024 if iseye else 4096,height=1024 if iseye else 4096,alpha=False);dest=n.new('ShaderNodeTexImage');dest.image=img;n.active=dest;mesh.materials.clear();mesh.materials.append(mat);mesh.uv_layers.active=atlas;atlas.active_render=True
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.bake(type='EMIT');img.filepath_raw=str(OUT/('eyes-atlas.png' if iseye else 'face-atlas.png'));img.file_format='PNG';img.save();img.pack()
 n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.33 if iseye else .78;bs.inputs['Specular IOR Level'].default_value=.3 if iseye else .12;uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='BakedAtlas';tx=n.new('ShaderNodeTexImage');tx.image=img;l.new(uvnode.outputs[0],tx.inputs[0]);l.new(tx.outputs[0],bs.inputs['Base Color']);l.new(bs.outputs[0],out.inputs[0]);mesh.color_attributes.remove(coverage)

# Validate fitted geometry before export.
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  assert not o.data.validate(clean_customdata=False),o.name
  assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v12.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
path=OUT/'director_wu.glb';raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary=raw[20+length:]
for item in doc['meshes']:
 if item['name']=='detail_hair_foundation':
  for primitive in item['primitives']:
   attrs=primitive['attributes']
   if 'COLOR_1' in attrs:attrs['COLOR_0']=attrs.pop('COLOR_1')
encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+binary)
report={'version':'director-v12','method':'measured render/reference landmark proportion fitting, preserving anatomical depth','landmarkControls':len(ids),'fitScale':float(scale),'fitShift':shift.tolist(),'changes':changes,'hairReferenceRegistered':True,'bytes':path.stat().st_size,'singlePhotoSideBackEstimated':True};(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('LIKENESS_FIT',json.dumps(report))
