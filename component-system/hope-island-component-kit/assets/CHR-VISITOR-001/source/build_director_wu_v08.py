"""Anatomical clay study from CC0 MakeHuman topology, not photo extrusion.
Static head/neck blockout. No likeness-final or facial-rig claim.
"""
from pathlib import Path
import bpy,bmesh,json,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[5];SRC=ROOT/'art-source/director-wu/anatomy-base';OUT=ROOT/'webgl-prototype/assets/characters/director-v08';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=2

def read_obj(path):
 vertices=[];faces=[];groups=[];g='';uvs=[];faceUV=[]
 for line in path.read_text().splitlines():
  a=line.split()
  if not a:continue
  if a[0]=='v':vertices.append(Vector(tuple(map(float,a[1:4]))))
  elif a[0]=='vt':uvs.append(tuple(map(float,a[1:3])))
  elif a[0]=='g':g=' '.join(a[1:])
  elif a[0]=='f':
   faces.append(tuple(int(v.split('/')[0])-1 for v in a[1:]));faceUV.append(tuple(int(v.split('/')[1])-1 if '/' in v and v.split('/')[1] else -1 for v in a[1:]));groups.append(g)
 return vertices,faces,groups,uvs,faceUV
base,faces,groups,uvs,faceUV=read_obj(SRC/'base.obj');posed=[v.copy() for v in base]
for line in (SRC/'asian-male-old.target').read_text().splitlines():
 a=line.split()
 if len(a)==4 and a[0].isdigit():posed[int(a[0])]+=Vector(tuple(map(float,a[1:])))
# Independent x/y/z dimensions preserve a real cranial volume and integral ears.
def convert(p):return Vector((p.x*.24,-(p.z-.35)*.205,1.03+(p.y-5.54)*.22))
def material(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.82;bs.inputs['Specular IOR Level'].default_value=.2;return m
clay=material('neutral-clay',(.42,.34,.27));eyeClay=material('eye-clay',(.58,.52,.43))
bodyFaces=[f for f,g in zip(faces,groups) if g=='body'];used=sorted({i for f in bodyFaces for i in f});remap={i:j for j,i in enumerate(used)}
mesh=bpy.data.meshes.new('MakeHuman-head-neck-quads');mesh.from_pydata([convert(posed[i]) for i in used],[],[tuple(remap[i] for i in f) for f in bodyFaces]);mesh.update()
head=bpy.data.objects.new('anatomy_head_and_neck',mesh);bpy.context.collection.objects.link(head);mesh.materials.append(clay)
# Cut below the neck into the upper shoulder mass and cap only the bottom opening.
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,.83),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
cut=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-.83)<1e-4 for v in e.verts)]
if cut:bmesh.ops.holes_fill(bm,edges=cut,sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
for f in mesh.polygons:f.use_smooth=True
# Shape keys retain an untouched stage for later, localized likeness adjustments.
head.shape_key_add(name='Anatomical base');study=head.shape_key_add(name='Reference proportion study')
# Broad, low-frequency sculpt based on visible frontal proportions only.
# Keep the original anatomical base available; do not project photograph depth.
for point in study.data:
 x,y,z=point.co
 front=max(0,min(1,(-y-.035)/.10))
 mouth=math.exp(-((z-1.115)/.035)**2-(x/.085)**4)*front
 jaw=math.exp(-((z-1.075)/.065)**2)*front
 cheek=math.exp(-((z-1.18)/.065)**2-((abs(x)-.105)/.06)**2)*front
 nose=math.exp(-((z-1.185)/.035)**2-(x/.045)**4)*front
 point.co.x=x*(1+.18*mouth+.07*jaw+.035*cheek+.09*nose)
 point.co.y=y-.009*cheek
 if z>1.30:point.co.z=1.30+(z-1.30)*.96
study.value=1.0
sub=head.modifiers.new('Review surface','SUBSURF');sub.levels=1;sub.render_levels=1
# Fit the supplied eyeball mesh through the official barycentric proxy mapping.
eyeV,eyeF,eyeG,_,_=read_obj(SRC/'high-poly.obj');mapping=[];started=False;scale=Vector((1,1,1))
for line in (SRC/'high-poly.mhclo').read_text().splitlines():
 a=line.split()
 if not a:continue
 if a[0] in ['x_scale','y_scale','z_scale']:
  axis={'x_scale':0,'y_scale':1,'z_scale':2}[a[0]];v1,v2=int(a[1]),int(a[2]);scale[axis]=abs(posed[v1][axis]-posed[v2][axis])/float(a[3])
 elif a[0]=='verts':started=True
 elif started and len(a)==9 and a[0].isdigit():mapping.append(a)
 elif started and not a[0].startswith('#') and not a[0].isdigit():break
assert len(mapping)==len(eyeV),(len(mapping),len(eyeV))
fit=[]
for row in mapping:
 indices=list(map(int,row[:3]));weights=list(map(float,row[3:6]));offset=Vector(tuple(map(float,row[6:9])));p=sum((posed[i]*w for i,w in zip(indices,weights)),Vector())+Vector(tuple(offset[k]*scale[k] for k in range(3)));fit.append(convert(p))
em=bpy.data.meshes.new('Fitted-eye-geometry');em.from_pydata(fit,[],eyeF);em.update();eyes=bpy.data.objects.new('anatomy_eyes',em);bpy.context.collection.objects.link(eyes);em.materials.append(eyeClay)
for f in em.polygons:f.use_smooth=True
# Local feature refinement keeps the source loops and rear skull intact.
def feature_warp(p):
 x,y,z=p; a=abs(x)
 front=max(0,min(1,(-y-.09)/.07))
 def gauss(cx,cz,sx,sz):return math.exp(-((a-cx)/sx)**2-((z-cz)/sz)**2)*front
 corner=gauss(.054,1.115,.024,.025)
 lips=gauss(0,1.118,.055,.018)
 cheek=gauss(.103,1.192,.050,.055)
 lower_cheek=gauss(.100,1.115,.052,.055)
 nose=gauss(.030,1.177,.027,.029)
 tip=gauss(0,1.185,.025,.028)
 lid=gauss(.068,1.270,.038,.029)
 brow=gauss(.026,1.309,.028,.025)
 xx=x*(1+.045*nose+.025*lower_cheek)
 yy=y-.006*cheek-.003*lower_cheek+.0025*tip+.002*brow
 zz=z+.0030*corner-.0014*math.tanh((z-1.118)/.0035)*lips
 zz+=.10*(z-1.270)*lid
 return Vector((xx,yy,zz))
# A separate relative shape key makes this pass reversible in Blender.
detail=head.shape_key_add(name='Gentle expression and facial volume',from_mix=True)
detail.relative_key=study
for point in detail.data:point.co=feature_warp(point.co)
# Relax only the depth of hollow cheek/fold areas, not eyelid or lip edges.
neighbors=[set() for _ in mesh.vertices]
for edge in mesh.edges:
 a,b=edge.vertices;neighbors[a].add(b);neighbors[b].add(a)
for _ in range(8):
 old=[p.co.copy() for p in detail.data]
 for i,point in enumerate(detail.data):
  x,y,z=old[i];front=max(0,min(1,(-y-.08)/.065))
  weight=(.38*math.exp(-((abs(x)-.100)/.043)**2-((z-1.145)/.065)**2)+.35*math.exp(-(x/.095)**2-((z-1.059)/.035)**2))*front
  # Protect the folded lip seam and mouth corners from depth relaxation.
  gate=min(1,max(0,(abs(x)-.075)/.025,(abs(z-1.117)-.035)/.03))
  weight*=gate*gate*(3-2*gate)
  if neighbors[i]:point.co.y=y+weight*(sum(old[j].y for j in neighbors[i])/len(neighbors[i])-y)
detail.value=1
for v in em.vertices:v.co=feature_warp(v.co)
report_changes={'eyelids':'relaxed lid opening, same fitted eyeball transform','nose':'rounder wings and reduced tip projection','mouth':'raised corners and reduced lip gap','cheeks':'fuller midface with local depth-only fold relaxation','preserved':'rear skull, ears, neck and facial loop topology'}

# Simple integrated bust base; the cut is below all facial deformation loops.
head['source_license']='CC0-1.0';head['stage']='Anatomical clay blockout; likeness not final';head['source_commit']=json.loads((SRC/'sources.json').read_text())['commit']
report={'version':'director-v08','stage':'facial-proportion-study','photoProjection':False,'source':'MakeHuman CC0 base mesh and adult target','sourceCommit':head['source_commit'],'proportionStudy':'broader mouth, fuller cheeks and jaw, slightly lower crown; frontal estimate only','featureRefinement':report_changes,'facialRig':False,'bodyAnimation':False,'meshes':[]}
for o in [head,eyes]:
 assert not o.data.validate(clean_customdata=False),o.name
 o.data.calc_loop_triangles();report['meshes'].append({'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons),'quadFaces':sum(len(f.vertices)==4 for f in o.data.polygons),'trianglesBeforeSubdivision':len(o.data.loop_triangles)})
bm=bmesh.new();bm.from_mesh(mesh);report['boundaryEdges']=sum(e.is_boundary for e in bm.edges);report['nonManifoldJunctions']=sum(len(e.link_faces)>2 for e in bm.edges);report['looseVertices']=sum(not v.link_faces for v in bm.verts);bm.free();assert report['nonManifoldJunctions']==0 and report['looseVertices']==0
bpy.ops.object.select_all(action='SELECT');bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('director-wu-v08.blend')))
bpy.ops.export_scene.gltf(filepath=str(OUT/'director_wu.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True)
report['bytes']=(OUT/'director_wu.glb').stat().st_size;(OUT/'manifest.json').write_text(json.dumps(report,indent=2));print('ANATOMY_STUDY',json.dumps(report))
