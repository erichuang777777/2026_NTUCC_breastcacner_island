"""Continuous photo-calibrated scalp material and a surface-following short groom.
Single-photo likeness study; rear appearance is estimated, not reconstructed.
"""
from pathlib import Path
import bpy,bmesh,json,math,struct,random
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[5]
OUT=ROOT/'webgl-prototype/assets/characters/director-v13';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v12.blend')))
originalHeadNormals=[f.normal.copy() for f in bpy.data.objects['anatomy_head_and_neck'].data.polygons]
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.margin=12
fit=json.loads((ROOT/'webgl-prototype/assets/characters/director-v12/manifest.json').read_text());scale=fit['fitScale'];shift=np.array(fit['fitShift']);ppw=602/.65;ca,sa=math.cos(-.16),math.sin(-.16)
ref=json.loads((ROOT/'art-source/director-wu/face-landmarks.json').read_text());rw,rh=ref['size']
def photo(p):
 u=p.x*ca-p.y*sa;return ((236+(u-.018)*ppw-shift[0])/scale,(301-(p.z-1.26)*ppw-shift[1])/scale)
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
poly=[(670,126),(780,145),(870,190),(945,265),(984,345),(995,435),(975,520),(945,575),(898,550),(865,473),(831,427),(780,402),(720,382),(660,372),(610,380),(555,385),(505,400),(458,435),(420,512),(402,584),(365,541),(338,454),(343,362),(374,278),(433,223),(500,182),(585,147)]
def hair_bounds(x):
 x=max(351,min(974,x));ys=[]
 for i,(ax,ay) in enumerate(poly):
  bx,by=poly[i-1]
  if min(ax,bx)<=x<max(ax,bx):ys.append(ay+(by-ay)*(x-ax)/(bx-ax))
 return x,min(ys)+9,max(ys)-9
def hair_sample(p):
 x,y=photo(p);x,top,bot=hair_bounds(x)
 # Compress the sampled range smoothly at the rear instead of clamping whole rows.
 depth=-p.x*sa-p.y*ca;back=1-smooth(-.03,.09,depth)
 rearY=top+(bot-top)*(.25+.5*max(0,min(1,(1.58-p.z)/.37)))
 y=y*(1-back)+rearY*back
 return x,max(top,min(bot,y))
source=bpy.data.images.load(str(ROOT/'webgl-prototype/assets/character-study/reference.jpg'),check_existing=True)
# Photo pixels are sampled into 3D material/vertex color, never changed.
pixels=np.array(source.pixels[:],dtype=np.float32).reshape(rh,rw,4)
def hair_rgb(p):
 x,y=hair_sample(p);return pixels[rh-1-int(y),int(x),:3]
for name in ['detail_swept_silver_strands','detail_temporal_wisps']:
 if bpy.data.objects.get(name):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
cap=bpy.data.objects['detail_hair_foundation'];mesh=cap.data
# Keep the full 3D scalp while reducing the extra crown above the reference silhouette.
for v in mesh.vertices:
 if v.co.z>1.49:v.co.z+=.007*smooth(1.49,1.58,v.co.z)

# Reparameterize the existing scalp surface toward the photo hairline; do not
# collapse the lower rows into a flat shelf at the fringe.
original=[v.co.copy() for v in mesh.vertices]
for k in range(160):
 limit=1.0
 for j in range(1,35):
  p=original[j*160+k];x,y=photo(p);_,_,bot=hair_bounds(x)
  if y>bot:
   prev=original[(j-1)*160+k];_,py=photo(prev);f=max(0,min(1,(bot-py)/max(1e-6,y-py)));limit=(j-1+f)/34;break
 end=original[34*160+k];front=smooth(.01,.12,-end.x*sa-end.y*ca);limit=1-(1-limit)*front
 for j in range(35):
  t=min(33.999,j*limit);r=int(t);mesh.vertices[j*160+k].co=original[r*160+k].lerp(original[(r+1)*160+k],t-r)
mesh.update()
# Reuse the scalp's coherent UV grid for a seamless transition around the head.
coverage=mesh.color_attributes.new(name='V13FrontalHair',type='FLOAT_COLOR',domain='POINT')
for v in mesh.vertices:
 depth=-v.co.x*sa-v.co.y*ca;w=smooth(.025,.145,depth);coverage.data[v.index].color=(w,w,w,1)
backuv=mesh.uv_layers.new(name='BackHairReference')
for f in mesh.polygons:
 for li in f.loop_indices:
  vi=mesh.loops[li].vertex_index;j,k=divmod(vi,160);a=k*2*math.pi/160;x=520+160*(.5+.5*math.sin(a))+80*j/34;y=180+120*j/34;backuv.data[li].uv=(x/rw,1-y/rh)
uv=mesh.uv_layers['PhotoHair'];atlas=mesh.uv_layers['HairAtlas'];edge=mesh.color_attributes['Color']
for v in mesh.vertices:
 row=v.index//160;alpha=1-smooth(31,34,row);edge.data[v.index].color=(1,1,1,alpha)
for face in mesh.polygons:
 for li in face.loop_indices:
  x,y=hair_sample(mesh.vertices[mesh.loops[li].vertex_index].co);uv.data[li].uv=(x/rw,1-y/rh)
mat=bpy.data.materials.new('continuous-silver-hair');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs[0]);tx=n.new('ShaderNodeTexImage');tx.image=source;u=n.new('ShaderNodeUVMap');u.uv_map='PhotoHair';l.new(u.outputs[0],tx.inputs[0]);gain=n.new('ShaderNodeMixRGB');gain.blend_type='MULTIPLY';gain.inputs[0].default_value=1;gain.inputs[2].default_value=(.70,.70,.70,1);l.new(tx.outputs[0],gain.inputs[1]);frontmix=n.new('ShaderNodeMixRGB');weight=n.new('ShaderNodeVertexColor');weight.layer_name='V13FrontalHair';l.new(weight.outputs[0],frontmix.inputs[0]);l.new(gain.outputs[0],frontmix.inputs[2]);backTex=n.new('ShaderNodeTexImage');backTex.image=source;guv=n.new('ShaderNodeUVMap');guv.uv_map='BackHairReference';l.new(guv.outputs[0],backTex.inputs[0]);backGain=n.new('ShaderNodeMixRGB');backGain.blend_type='MULTIPLY';backGain.inputs[0].default_value=1;backGain.inputs[2].default_value=(.70,.70,.70,1);l.new(backTex.outputs[0],backGain.inputs[1]);groomUV=n.new('ShaderNodeUVMap');groomUV.uv_map='GroomUV';stretch=n.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(1500,16,1);l.new(groomUV.outputs[0],stretch.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=2;l.new(stretch.outputs[0],noise.inputs[0]);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.16;ramp.color_ramp.elements[0].color=(.035,.038,.03,1);ramp.color_ramp.elements[1].position=.84;ramp.color_ramp.elements[1].color=(.28,.29,.25,1);l.new(noise.outputs['Fac'],ramp.inputs[0]);detailmix=n.new('ShaderNodeMixRGB');detailmix.inputs[0].default_value=.35;l.new(ramp.outputs[0],detailmix.inputs[1]);l.new(backGain.outputs[0],detailmix.inputs[2]);l.new(detailmix.outputs[0],frontmix.inputs[1]);l.new(frontmix.outputs[0],em.inputs[0]);img=bpy.data.images.new('v13-continuous-hair',width=2048,height=2048,alpha=False);dest=n.new('ShaderNodeTexImage');dest.image=img;n.active=dest;mesh.materials.clear();mesh.materials.append(mat);mesh.uv_layers.active=atlas;atlas.active_render=True
bpy.ops.object.select_all(action='DESELECT');cap.select_set(True);bpy.context.view_layer.objects.active=cap;bpy.ops.object.bake(type='EMIT');img.filepath_raw=str(OUT/'hair-atlas.png');img.file_format='PNG';img.save();img.pack();mesh.color_attributes.remove(coverage)
n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.86;bs.inputs['Specular IOR Level'].default_value=.12;u=n.new('ShaderNodeUVMap');u.uv_map='HairAtlas';tx=n.new('ShaderNodeTexImage');tx.image=img;l.new(u.outputs[0],tx.inputs[0]);l.new(tx.outputs[0],bs.inputs['Base Color']);vc=n.new('ShaderNodeVertexColor');vc.layer_name='Color';l.new(vc.outputs['Alpha'],bs.inputs['Alpha']);l.new(bs.outputs[0],out.inputs[0]);mat.surface_render_method='BLENDED'
# A short groom sampled on the scalp parameterization. No long vertical strings.
N,R=160,34
coords=[v.co.copy() for v in mesh.vertices]
def surf(t,a):
 t=max(.001,min(.999,t));rr=t*R;r=int(rr);aa=(a%(2*math.pi))/(2*math.pi)*N;k=int(aa);f=aa-k;g=rr-r
 p00=coords[r*N+k];p01=coords[r*N+(k+1)%N];p10=coords[(r+1)*N+k];p11=coords[(r+1)*N+(k+1)%N]
 p=p00.lerp(p01,f).lerp(p10.lerp(p11,f),g)
 tangent=(p01-p00);vertical=(p10-p00);normal=tangent.cross(vertical).normalized()
 if normal.dot(p-Vector((0,0,1.36)))<0:normal=-normal
 return p,normal
rng=random.Random(1307);verts=[];faces=[];colors=[]
for strand in range(9500):
 t=rng.uniform(.075,.997);a=rng.uniform(-math.pi,math.pi);length=rng.uniform(.035,.12);sweep=.10+.17*max(0,math.cos(a));width=rng.uniform(.00013,.00032);shade=rng.uniform(.65,1.1)
 # Shorter hairs near the temple, longer gently swept strands at the crown.
 if t>.84:length*=.65
 base=len(verts);steps=5;sidegray=rng.uniform(.045,.30)
 for j in range(steps+1):
  q=j/steps;tt=t+length*(q-.5);aa=a+sweep*(q-.5)*(1-t*.5);p,normal=surf(tt,aa);p+=normal*(.0005+.0024*math.sin(math.pi*q));p2,_=surf(tt+.002,aa+.002);tangent=(p2-p).normalized();side=normal.cross(tangent).normalized();w=width*(.3+.7*math.sin(math.pi*q)**.5)
  front=smooth(.025,.145,-p.x*sa-p.y*ca);bx=int(520+160*(.5+.5*math.sin(aa))+80*max(0,min(1,tt)));by=int(180+120*max(0,min(1,tt)));backColor=pixels[rh-1-by,bx,:3]*.35+np.array([sidegray,sidegray*1.025,sidegray*.90])*.65/.70;c=np.clip((hair_rgb(p)*front+backColor*(1-front))*shade*.70,0,1)
  for sign in [-1,1]:verts.append(p+side*w*sign);colors.append((*c,1))
  if j:ii=base+2*j;faces.extend([(ii-2,ii-1,ii+1),(ii-2,ii+1,ii)])
gm=bpy.data.meshes.new('surface-following-short-groom');gm.from_pydata(verts,[],faces);gm.update();g=bpy.data.objects.new('detail_short_silver_groom',gm);bpy.context.collection.objects.link(g);attr=gm.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i,c in enumerate(colors):attr.data[i].color=c
m=bpy.data.materials.new('sampled-natural-silver-strands');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.84;bs.inputs['Specular IOR Level'].default_value=.12;vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Color';m.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);gm.materials.append(m)
for f in gm.polygons:f.use_smooth=True
# Correct cool photograph-background contamination at the lower cheek/neck.
# Wider and depth-aware fade keeps image texture on the central face only.
head=bpy.data.objects['anatomy_head_and_neck'];mesh=head.data
for v in mesh.vertices:
 x,y,z=v.co;front=smooth(.10,.16,-y);seam=1.109+.012*(abs(x)/.06)**2
 w=math.exp(-(x/.073)**6)*front
 v.co.y+=w*(-.006*math.exp(-((z-seam)/.0065)**2)+.002*math.exp(-((z-seam-.012)/.008)**2))
 # Soften the pointed chin projection without changing its frontal silhouette.
 v.co.y+=.004*math.exp(-(x/.065)**4-((z-1.025)/.032)**2)*front
mesh.update()
assert all(f.normal.dot(originalHeadNormals[f.index])>=0 for f in mesh.polygons)
def face_photo(p):
 x,y=photo(p);ear=smooth(.165,.183,abs(p.x))*smooth(1.12,1.17,p.z)*(1-smooth(1.31,1.35,p.z))*smooth(-.045,.015,-p.y)
 ex=max(935,min(978,955+p.y*250));ey=max(585,min(755,590+(1.31-p.z)*1050))
 return x*(1-ear)+ex*ear,y*(1-ear)+ey*ear,ear
outline=[]
for i in ref['oval']:
 x,y=ref['points'][i][0]*rw,ref['points'][i][1]*rh
 y-=65*(1-smooth(420,530,y));outline.append((x,y))
def face_coverage(x,y):
 inside=False;nearest=1e9
 for i,(ax,ay) in enumerate(outline):
  bx,by=outline[i-1];vx,vy=bx-ax,by-ay;t=max(0,min(1,((x-ax)*vx+(y-ay)*vy)/(vx*vx+vy*vy)));nearest=min(nearest,math.hypot(x-ax-t*vx,y-ay-t*vy))
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:inside=not inside
 return smooth(0,24,nearest) if inside else 0
atlas=mesh.uv_layers['BakedAtlas'];uv=mesh.uv_layers['PhotoRegistration'];coverage=mesh.color_attributes.new(name='V13PhotoCoverage',type='FLOAT_COLOR',domain='POINT');photoGain=mesh.color_attributes.new(name='V13PhotoGain',type='FLOAT_COLOR',domain='POINT')
for v in mesh.vertices:
 x,y,ear=face_photo(v.co);depth=-v.co.x*sa-v.co.y*ca
 amount=smooth(.015,.10,depth)*face_coverage(x,y)
 amount=max(amount,ear*.85);coverage.data[v.index].color=(amount,amount,amount,1)
 # Compensate the photograph's baked lip shadow for additional surface shading.
 seam=1.109+.012*(abs(v.co.x)/.06)**2;lip=math.exp(-(v.co.x/.075)**6-((v.co.z-seam)/.012)**2);boost=.75+1.8*lip*max(0,-v.normal.z)**2;photoGain.data[v.index].color=(boost,boost,boost,1)
for f in mesh.polygons:
 for li in f.loop_indices:
  x,y,_=face_photo(mesh.vertices[mesh.loops[li].vertex_index].co);uv.data[li].uv=(x/rw,1-y/rh)
m=bpy.data.materials.new('warm-continuous-face-and-neck');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs[0]);tx=n.new('ShaderNodeTexImage');tx.image=source;u=n.new('ShaderNodeUVMap');u.uv_map='PhotoRegistration';l.new(u.outputs[0],tx.inputs[0]);gain=n.new('ShaderNodeMixRGB');gain.blend_type='MULTIPLY';gain.inputs[0].default_value=1;gain.inputs[2].default_value=(.75,.75,.75,1);gainColor=n.new('ShaderNodeVertexColor');gainColor.layer_name='V13PhotoGain';l.new(gainColor.outputs[0],gain.inputs[2]);l.new(tx.outputs[0],gain.inputs[1]);mix=n.new('ShaderNodeMixRGB');vc=n.new('ShaderNodeVertexColor');vc.layer_name='V13PhotoCoverage';l.new(vc.outputs[0],mix.inputs[0]);mix.inputs[1].default_value=(.48,.275,.17,1);l.new(gain.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],em.inputs[0]);img=bpy.data.images.new('v13-face',width=4096,height=4096,alpha=False);dest=n.new('ShaderNodeTexImage');dest.image=img;n.active=dest;mesh.materials.clear();mesh.materials.append(m);mesh.uv_layers.active=atlas;atlas.active_render=True
bpy.ops.object.select_all(action='DESELECT');head.select_set(True);bpy.context.view_layer.objects.active=head;bpy.ops.object.bake(type='EMIT');img.filepath_raw=str(OUT/'face-atlas.png');img.file_format='PNG';img.save();img.pack();mesh.color_attributes.remove(coverage);mesh.color_attributes.remove(photoGain)
n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.85;bs.inputs['Specular IOR Level'].default_value=.1;u=n.new('ShaderNodeUVMap');u.uv_map='BakedAtlas';tx=n.new('ShaderNodeTexImage');tx.image=img;l.new(u.outputs[0],tx.inputs[0]);l.new(tx.outputs[0],bs.inputs['Base Color']);l.new(bs.outputs[0],out.inputs[0])
# Portable GLB; preserve the transparent hairline as the primary vertex color.
for o in scene.objects:
 if o.type=='MESH':assert not o.data.validate(clean_customdata=False);assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v13.blend')));bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
p=OUT/'director_wu.glb';raw=p.read_bytes();ln=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+ln]);binary=raw[20+ln:]
for item in doc['meshes']:
 if item['name']=='detail_hair_foundation':
  for prim in item['primitives']:
   attrs=prim['attributes']
   if 'COLOR_1' in attrs:attrs['COLOR_0']=attrs.pop('COLOR_1')
e=json.dumps(doc,separators=(',',':')).encode();e+=b' '*((-len(e))%4);p.write_bytes(struct.pack('<III',0x46546c67,2,20+len(e)+len(binary))+struct.pack('<II',len(e),0x4e4f534a)+e+binary)
(OUT/'manifest.json').write_text(json.dumps({'version':'director-v13','base':'director-v12','groomStrands':9500,'continuousScalpMaterial':True,'faceGeometryUnchanged':False,'localLipAndChinDepthRefinement':True,'sideBackEstimated':True,'reviewStatus':'internal-review','bytes':p.stat().st_size},indent=2));print('V13_DONE',p.stat().st_size)
