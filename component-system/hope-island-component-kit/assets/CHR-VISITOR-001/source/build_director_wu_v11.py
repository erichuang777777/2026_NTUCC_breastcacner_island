"""Complete portrait detail study: fitted silver hair, brows and eye surface.
Retains the accepted v10 photographic head and eye geometry unchanged.
"""
from pathlib import Path
import bpy,bmesh,json,math,random,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[5];OUT=ROOT/'webgl-prototype/assets/characters/director-v11';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v10.blend')))
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2
head=bpy.data.objects['anatomy_head_and_neck'];eyes=bpy.data.objects['anatomy_eyes'];original={o.name:[tuple(v.co) for v in o.data.vertices] for o in [head,eyes]}
bvh=BVHTree.FromPolygons([v.co for v in head.data.vertices],[list(p.vertices) for p in head.data.polygons]);ebvh=BVHTree.FromPolygons([v.co for v in eyes.data.vertices],[list(p.vertices) for p in eyes.data.polygons]);origin=Vector((0,.015,1.28))
def material(name,color,rough=.75,vc=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Specular IOR Level'].default_value=.25
 if vc:
  n=m.node_tree.nodes.new('ShaderNodeVertexColor');n.layer_name='Color';m.node_tree.links.new(n.outputs['Color'],bs.inputs['Base Color'])
 return m
def meshobj(name,verts,faces,mat,cols=None):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);mesh.materials.append(mat)
 if cols:
  attr=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
  for i,c in enumerate(cols):attr.data[i].color=(*c,1)
 for p in mesh.polygons:p.use_smooth=True
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();return o
def surface(theta,phi):
 d=Vector((math.sin(phi)*math.sin(theta),-math.sin(phi)*math.cos(theta),math.cos(phi)));hit,n,idx,dist=bvh.ray_cast(origin+d*.8,-d,1.5);assert hit is not None;return hit,n
# Hairline follows the skull, higher at the temples and down to the posterior nape.
N=160;limits=[]
for k in range(N):
 th=2*math.pi*k/N;c=math.cos(th);target=1.310+(.055*c**3 if c>=0 else -.075*c*c)+.003*math.sin(th*13)+.002*math.sin(th*23)
 lo,hi=0,2.1
 for _ in range(18):
  mid=(lo+hi)/2;p,n=surface(th,mid)
  if p.z>target:lo=mid
  else:hi=mid
 limits.append((lo+hi)/2)
def cap(th,t,extra=0):
 u=(th%(2*math.pi))/(2*math.pi)*N;k=int(u)%N;phi=limits[k]*(1-(u%1))+limits[(k+1)%N]*(u%1)
 p,n=surface(th,phi*min(t,1.065));front=max(0,math.cos(th));lift=.007+.009*math.sin(math.pi*min(t,1))+.007*(1-t)+front*.004*math.sin(math.pi*min(t,1))+.0015*math.sin(th*11+t*17)*math.sin(math.pi*min(t,1))
 return p+n*(lift+extra)
verts=[];uv=[];masks=[];faces=[];R=34
for j in range(R+1):
 t=max(.0001,j/R)
 for k in range(N):
  th=2*math.pi*k/N;p=cap(th,t);verts.append(p)
  uv.append(((650+max(-1,min(1,p.x/.20))*245)/1384,1-(180+max(0,min(1,(1.545-p.z)/.18))*150)/1850))
  # Portrait hair only on the front; back and sides use salt-and-pepper material.
  c=math.cos(th);w=max(0,min(1,(c-.15)/.55));w=w*w*(3-2*w);masks.append(w*.18)
for j in range(R):
 for k in range(N):a=j*N+k;b=j*N+(k+1)%N;faces.append((a,b,b+N,a+N))
base=material('silver-hair-base',(.24,.245,.22));capobj=meshobj('detail_hair_foundation',verts,faces,base)
# Bake actual frontal hair detail from the supplied photo onto the fitted curved shell.
mesh=capobj.data;photoUV=mesh.uv_layers.new(name='PhotoHair');groom=mesh.uv_layers.new(name='GroomUV');atlas=mesh.uv_layers.new(name='HairAtlas');mask=mesh.color_attributes.new(name='HairPhotoCoverage',type='FLOAT_COLOR',domain='POINT')
for i,w in enumerate(masks):mask.data[i].color=(w,w,w,1)
for p in mesh.polygons:
 for li in p.loop_indices:
  i=mesh.loops[li].vertex_index;photoUV.data[li].uv=uv[i];t=(i//N)/R;th=(i%N)/N*2*math.pi;groom.data[li].uv=((i%N)/N+.06*(1-t)*max(0,math.cos(th)),t)
n=base.node_tree.nodes;l=base.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs['Surface']);tx=n.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(ROOT/'webgl-prototype/assets/character-study/reference.jpg'),check_existing=True);tx.extension='EXTEND';uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='PhotoHair';l.new(uvnode.outputs[0],tx.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');vc=n.new('ShaderNodeVertexColor');vc.layer_name='HairPhotoCoverage';l.new(vc.outputs['Color'],mix.inputs[0]);mix.inputs[1].default_value=(.24,.245,.22,1)
# Fine directional root-to-tip texture supplies hair fibers instead of a flat gray shell.
guv=n.new('ShaderNodeUVMap');guv.uv_map='GroomUV';scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(1100,9,1);l.new(guv.outputs[0],scale.inputs[0]);noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=2;l.new(scale.outputs[0],noise.inputs['Vector']);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.20;ramp.color_ramp.elements[0].color=(.07,.075,.065,1);ramp.color_ramp.elements[1].position=.80;ramp.color_ramp.elements[1].color=(.43,.44,.40,1);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs['Color'],mix.inputs[1]);l.new(tx.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],em.inputs['Color']);img=bpy.data.images.new('portrait-hair-atlas',width=2048,height=2048,alpha=False);dest=n.new('ShaderNodeTexImage');dest.image=img;n.active=dest
bpy.ops.object.select_all(action='DESELECT');capobj.select_set(True);bpy.context.view_layer.objects.active=capobj;mesh.uv_layers.active=atlas;atlas.active_render=True;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008);bpy.ops.object.mode_set(mode='OBJECT');mesh.uv_layers.active=mesh.uv_layers['HairAtlas'];mesh.uv_layers['HairAtlas'].active_render=True
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.margin=12;bpy.ops.object.bake(type='EMIT');img.filepath_raw=str(OUT/'hair-atlas.png');img.file_format='PNG';img.save();img.pack()
n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.77;bs.inputs['Specular IOR Level'].default_value=.18;tx=n.new('ShaderNodeTexImage');tx.image=img;uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='HairAtlas';l.new(uvnode.outputs[0],tx.inputs['Vector']);l.new(tx.outputs['Color'],bs.inputs['Base Color']);l.new(bs.outputs[0],out.inputs[0]);mesh.color_attributes.remove(mesh.color_attributes['HairPhotoCoverage'])
# Feather the foundation into individual hairs instead of leaving a solid cap edge.
edgecolor=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT')
for i in range(len(mesh.vertices)):
 t=(i//N)/R;fade=max(0,min(1,(1-t)/.10));fade=fade*fade*(3-2*fade);edgecolor.data[i].color=(1,1,1,fade)
vc=n.new('ShaderNodeVertexColor');vc.layer_name='Color';l.new(vc.outputs['Alpha'],bs.inputs['Alpha']);mult=n.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;l.new(tx.outputs['Color'],mult.inputs[1]);l.new(vc.outputs['Color'],mult.inputs[2]);l.new(mult.outputs[0],bs.inputs['Base Color']);mesh.color_attributes.active_color=edgecolor;mesh.color_attributes.render_color_index=list(mesh.color_attributes).index(edgecolor);base.surface_render_method='BLENDED'

# Tapered strand geometry breaks up the silhouette and lays across the side part.
rng=random.Random(112233);verts=[];faces=[];cols=[];hairmat=material('individual-grey-hair',(1,1,1),.74,True);palette=[(.19,.20,.18),(.31,.32,.29),(.46,.47,.42),(.12,.13,.115),(.40,.41,.37)]
def strand(points,width,color):
 start=len(verts)
 for j,p in enumerate(points):
  tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized();n=tangent.cross(Vector((0,1,0)))
  if n.length<.01:n=tangent.cross(Vector((1,0,0)))
  n.normalize();b=tangent.cross(n).normalized();r=width*(.8+.2*math.sin(math.pi*j/(len(points)-1)))*(1-.85*(j/(len(points)-1))**3)
  for k in range(3):verts.append(p+r*(math.cos(k*2*math.pi/3)*n+math.sin(k*2*math.pi/3)*b));cols.append(color)
 for j in range(len(points)-1):
  for k in range(3):a=start+j*3+k;b=start+j*3+(k+1)%3;faces.append((a,b,b+3,a+3))
for h in range(2600):
 th=rng.uniform(-math.pi,math.pi);t0=rng.uniform(.08,.90);end=min(1.035,t0+rng.uniform(.09,.20));sweep=-.32*max(0,math.cos(th))+.07*math.sin(th)
 points=[]
 for j in range(8):
  u=j/7;tt=t0+(end-t0)*u;theta=th+sweep*u+.02*math.sin(u*math.pi+h);points.append(cap(theta,tt,.0006+.002*math.sin(math.pi*u)))
 strand(points,rng.uniform(.00020,.00034),palette[rng.randrange(len(palette))])
# Dense short flyaways break up the tapered hairline around the full scalp.
for h in range(1000):
 th=rng.uniform(-math.pi,math.pi);start=rng.uniform(.90,.98);end=rng.uniform(1.015,1.055)
 points=[cap(th-.035*max(0,math.cos(th))*j/5,start+(end-start)*j/5,.0005) for j in range(6)]
 strand(points,rng.uniform(.00020,.00034),palette[h%len(palette)])
strands=meshobj('detail_swept_silver_strands',verts,faces,hairmat,cols)
# Short wisps at the temporal hairline, staying clear of the ear rims.
verts=[];faces=[];cols=[]
for side in [-1,1]:
 for h in range(100):
  th=side*rng.uniform(.80,1.05);t0=rng.uniform(.86,.98);points=[cap(th+.035*side*j/5,t0+.12*j/5,.001) for j in range(6)];strand(points,.00032,palette[h%4])
sideburns=meshobj('detail_temporal_wisps',verts,faces,hairmat,cols)
# Eyebrow micro-strands sit on the photo-aligned brow, preserving its photographed shape.
def facepoint(tree,x,z,offset):
 p,n,idx,d=tree.ray_cast(Vector((x,-1,z)),Vector((0,1,0)),2);assert p is not None;return p+Vector((0,-offset,0))
verts=[];faces=[];cols=[];browmat=material('fine-grey-brow',(1,1,1),.83,True)
for side in [-1,1]:
 for h in range(45):
  t=(h+rng.random())/45;x=.030+.087*t;z=1.318+.009*math.sin(math.pi*t)-.005*t+rng.uniform(-.003,.003)
  points=[facepoint(bvh,side*(x+.003*j/3),z+.002*math.sin(j/3*2),.00025) for j in range(4)];strand(points,.00011,(.09,.08,.065) if h%4==0 else (.025,.019,.014))
brows=meshobj('detail_brow_hairs',verts,faces,browmat,cols)
# A thin transparent corneal highlight follows each existing spherical eye.
cornea=material('corneal-wet-highlight',(1,1,1),.10);bs=cornea.node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.11;bs.inputs['Coat Weight'].default_value=.9;bs.inputs['Coat Roughness'].default_value=.07;cornea.surface_render_method='BLENDED'
verts=[];faces=[]
for side in [-1,1]:
 start=len(verts);Neye=48;rings=6
 for j in range(rings):
  r=.013*j/(rings-1)
  for k in range(Neye):
   th=2*math.pi*k/Neye;x=side*.06758+r*math.cos(th);z=1.27236+r*math.sin(th);verts.append(facepoint(ebvh,x,z,.00012+.00045*(1-(r/.013)**2)))
 for j in range(rings-1):
  for k in range(Neye):a=start+j*Neye+k;b=start+j*Neye+(k+1)%Neye;faces.append((a,b,b+Neye,a+Neye))
lens=meshobj('detail_corneal_highlight',verts,faces,cornea);bm=bmesh.new();bm.from_mesh(lens.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bm.to_mesh(lens.data);bm.free()
assert all(original[o.name]==[tuple(v.co) for v in o.data.vertices] for o in [head,eyes])
report={'version':'director-v11','base':'director-v10','approvedHeadAndEyesUnchanged':True,'photoHairReference':True,'hairStrands':3800,'browStrands':90,'facialAnimation':False,'meshes':[]}
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  assert not o.data.validate(clean_customdata=False),o.name;o.data.calc_loop_triangles();report['meshes'].append({'name':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles)})
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v11.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True)
# Blender exports alpha-only vertex color as COLOR_1; glTF renderers use COLOR_0.
# Promote the authored fade to the primary color channel for portable hair edges.
import struct
path=OUT/'director_wu.glb';raw=path.read_bytes();json_length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+json_length])
for item in doc['meshes']:
 if item['name']=='detail_hair_foundation':
  for primitive in item['primitives']:
   attrs=primitive['attributes']
   if 'COLOR_1' in attrs:attrs['COLOR_0']=attrs.pop('COLOR_1')
encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);tail=raw[20+json_length:];path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(encoded)+len(tail))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+tail)

report['hairAlphaPrimaryColor']=True;report['bytes']=(OUT/'director_wu.glb').stat().st_size;(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('PORTRAIT_DETAILS',json.dumps(report))
