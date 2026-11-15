"""Register the supplied photograph onto the accepted anatomical mesh via UVs.
Only material/UV coordinates change; head and eye geometry are preserved.
"""
from pathlib import Path
import bpy,json,math,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[5];OUT=ROOT/'webgl-prototype/assets/characters/director-v10';OUT.mkdir(parents=True,exist_ok=True)
source=ROOT/'webgl-prototype/assets/character-study/reference.jpg';landmarks=json.loads((ROOT/'art-source/director-wu/face-landmarks.json').read_text());W,H=landmarks['size']
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('director-wu-v09.blend')))
for o in list(bpy.data.objects):
 if o.name.startswith('feature_'):bpy.data.objects.remove(o,do_unlink=True)
head=bpy.data.objects['anatomy_head_and_neck'];eyes=bpy.data.objects['anatomy_eyes'];original={o.name:[tuple(v.co) for v in o.data.vertices] for o in [head,eyes]}
# Anatomical locations on v08/v09 paired with 2D landmarks of the supplied photo.
# These controls adjust UVs only, never substitute photographic depth for anatomy.
anchors=[(0,1.385,10),(0,1.033,152),(0,1.185,1),(0,1.270,168),(-.039,1.177,98),(.039,1.177,327),(-.103,1.272,33),(-.038,1.268,133),(.103,1.272,263),(.038,1.268,362),(-.070,1.283,159),(-.068,1.262,145),(.070,1.283,386),(.068,1.262,374),(-.060,1.117,61),(.060,1.117,291),(0,1.120,13),(0,1.116,14),(0,1.130,0),(0,1.098,17),(-.121,1.317,70),(-.079,1.326,105),(-.031,1.318,107),(.121,1.317,300),(.079,1.326,334),(.031,1.318,336),(-.165,1.218,234),(.165,1.218,454),(-.132,1.080,172),(.132,1.080,397),(-.161,1.272,127),(.161,1.272,356)]
X=np.array([[x,z] for x,z,i in anchors]);Y=np.array([[landmarks['points'][i][0],1-landmarks['points'][i][1]] for x,z,i in anchors])
# Thin-plate spline with affine tail; a small regularizer avoids near-coincident lip controls.
def kernel(d):return d*d*np.log(np.maximum(d,1e-12))
D=np.linalg.norm(X[:,None,:]-X[None,:,:],axis=2);P=np.column_stack([np.ones(len(X)),X]);A=np.block([[kernel(D)+np.eye(len(X))*1e-8,P],[P.T,np.zeros((3,3))]]);coef=np.linalg.solve(A,np.vstack([Y,np.zeros((3,2))]))
def uvfield(points):
 q=np.array([[p.x,p.z] for p in points]);d=np.linalg.norm(q[:,None,:]-X[None,:,:],axis=2);return kernel(d)@coef[:len(X)]+np.column_stack([np.ones(len(q)),q])@coef[len(X):]
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
photo=bpy.data.images.load(str(source),check_existing=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.bake.margin=12
records=[]
for obj in [head,eyes]:
 mesh=obj.data;iseye=obj==eyes;field=uvfield([v.co for v in mesh.vertices]);projection=mesh.uv_layers.new(name='PhotoRegistration');atlas=mesh.uv_layers.new(name='BakedAtlas')
 mask=mesh.color_attributes.new(name='PhotoCoverage',type='FLOAT_COLOR',domain='POINT')
 for v in mesh.vertices:
  x,y,z=v.co
  amount=1.0 if iseye else smooth(-.08,-.145,y)*(1-smooth(.147,.180,abs(x)))*smooth(1.025,1.065,z)*(1-smooth(1.350-.15*abs(x),1.370-.15*abs(x),z))
  mask.data[v.index].color=(amount,amount,amount,1)
 for poly in mesh.polygons:
  # Cylindrical UV seam behind the head; never through the facial features.
  us=[]
  for li in poly.loop_indices:
   v=mesh.vertices[mesh.loops[li].vertex_index];projection.data[li].uv=field[v.index]
   x,y,z=v.co
   if iseye:
    cx=.0696 if x>0 else -.0696;theta=math.atan2(x-cx,-(y+.162));u=(.25 if x<0 else .75)+theta/(4*math.pi);vv=(z-1.235)/.080
   else:u=.5+math.atan2(x,-(y-.015))/(2*math.pi);vv=(z-.83)/.70
   us.append([li,u,vv])
  if max(q[1] for q in us)-min(q[1] for q in us)>(.4 if iseye else .5):
   # Only head wraps; eye atlas uses separate hemispheres and front is continuous.
   if not iseye:
    for q in us:
     if q[1]<.5:q[1]+=1
  for li,u,v in us:atlas.data[li].uv=(u,v)
 mat=bpy.data.materials.new('photo-projection-work-'+obj.name);mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');l.new(em.outputs[0],out.inputs['Surface'])
 uv=n.new('ShaderNodeUVMap');uv.uv_map='PhotoRegistration';tex=n.new('ShaderNodeTexImage');tex.image=photo;tex.extension='EXTEND';l.new(uv.outputs[0],tex.inputs['Vector'])
 vc=n.new('ShaderNodeVertexColor');vc.layer_name='PhotoCoverage';scale=n.new('ShaderNodeMixRGB');scale.blend_type='MULTIPLY';scale.inputs[0].default_value=1;scale.inputs[2].default_value=(.75,.75,.75,1);l.new(tex.outputs['Color'],scale.inputs[1])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';l.new(vc.outputs['Color'],mix.inputs[0]);mix.inputs[1].default_value=(.43,.255,.163,1) if not iseye else (.65,.64,.60,1);l.new(scale.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],em.inputs['Color'])
 size=4096 if not iseye else 1024;img=bpy.data.images.new('registered-face' if not iseye else 'registered-eyes',width=size,height=size,alpha=False);dest=n.new('ShaderNodeTexImage');dest.image=img;n.active=dest
 mesh.materials.clear();mesh.materials.append(mat);mesh.uv_layers.active=atlas;atlas.active_render=True
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 # Pack non-overlapping islands, including the folded eyelids, nostrils and inner lips.
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.008,area_weight=.3,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
 mesh.uv_layers.active=mesh.uv_layers['BakedAtlas'];mesh.uv_layers['BakedAtlas'].active_render=True
 bpy.ops.object.bake(type='EMIT')
 img.filepath_raw=str(OUT/('face-atlas.png' if not iseye else 'eyes-atlas.png'));img.file_format='PNG';img.save();img.pack()
 # Export a standard GLTF PBR material with the baked photograph atlas.
 n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=.78 if not iseye else .33;bs.inputs['Specular IOR Level'].default_value=.12 if not iseye else .3;l.new(bs.outputs['BSDF'],out.inputs['Surface']);uv=n.new('ShaderNodeUVMap');uv.uv_map='BakedAtlas';tex=n.new('ShaderNodeTexImage');tex.image=img;l.new(uv.outputs[0],tex.inputs['Vector']);l.new(tex.outputs['Color'],bs.inputs['Base Color'])
 # Old vertex colors must not multiply the new photographic skin in GLTF.
 for attr in list(mesh.color_attributes):mesh.color_attributes.remove(attr)
 records.append({'mesh':obj.name,'atlasSize':size,'vertices':len(mesh.vertices),'geometryUnchanged':original[obj.name]==[tuple(v.co) for v in mesh.vertices]})
 assert records[-1]['geometryUnchanged']
head['stage']='Registered photographic facial material on accepted v08 geometry';head['photo_source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v10.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True)
report={'version':'director-v10','baseGeometry':'director-v08 via v09','method':'landmark-registered photo UV material, baked to PBR atlases','geometryUnchanged':True,'photoSourceSha256':head['photo_source_sha256'],'photoSource':'user supplied reference.jpg','landmarkControls':len(anchors),'syntheticBrowsAndIrisesRemoved':True,'meshes':records,'bytes':(OUT/'director_wu.glb').stat().st_size,'limitations':['single front photo','side/back use blended base skin','no hair or animation']};(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('PHOTO_MATERIAL',json.dumps(report))
