"""Isolated tower study grounded in the user's original poster; Blender Z-up."""
from pathlib import Path
import math
import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent.parent / 'export'
OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color, rough=.55, metal=0, emission=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
    return m

cream=material('warm-ivory-plaster',(.82,.69,.51),.8)
stone=material('carved-sandstone',(.64,.47,.31),.8)
trim=material('ivory-cornice',(.94,.81,.61),.65)
rose=material('rose-satin-ribbon',(.63,.20,.32),.36,.12)
roofmat=material('rose-copper-roof',(.55,.19,.28),.4,.3)
gold=material('aged-brass',(.55,.32,.12),.3,.65)
light=material('warm-lantern', (1,.61,.20),.3,0,3)
dark=material('door-recess',(.12,.08,.06),.8)
glass=material('lantern-glass',(.9,.94,1),.12)
glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.95
glass.node_tree.nodes.get('Principled BSDF').inputs['IOR'].default_value=1.45

def finish(o,name,m):
    o.name=name; o.data.materials.append(m); return o

def cylinder(name,r,z,h,m,top=None,vertices=64):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=r if top is None else top,depth=h,location=(0,0,z))
    o=finish(bpy.context.object,name,m)
    b=o.modifiers.new('soft-masonry-edges','BEVEL'); b.width=.018; b.segments=3
    o.modifiers.new('weighted-normals','WEIGHTED_NORMAL')
    return o

def cube(name,xyz,size,m):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz); o=bpy.context.object; o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,name,m); b=o.modifiers.new('soft-edges','BEVEL'); b.width=.015;b.segments=3
    return o

def tube(name,points,r,m,cyclic=False):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=r;c.bevel_resolution=3
    s=c.splines.new('POLY');s.points.add(len(points)-1)
    for p,xyz in zip(s.points,points):p.co=(*xyz,1)
    s.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o

for i,(r,h) in enumerate(((1.12,.12),(1.02,.12),(.92,.14))):
    cylinder('stepped-foundation-'+str(i),r,.06+i*.12,h,stone)
cylinder('tapered-tower-shaft',.84,2.13,3.56,cream,.59)
for z,r,h in ((.43,.86,.18),(.58,.84,.08),(3.82,.66,.10),(3.94,.72,.15),(4.05,.89,.12),(4.15,1.02,.13)):
    cylinder('masonry-cornice',r,z,h,trim)
# Front elevation faces -Y, as in the poster camera.
cube('recessed-entry',(0,-.825,.86),(.43,.07,.86),dark)
cube('glowing-entry-door',(0,-.87,.86),(.32,.025,.72),light)
for x in (-.23,.23):cube('entry-jamb',(x,-.86,.88),(.08,.12,.9),trim)
tube('arched-entry-lintel',[(.23*math.cos(t),-.86,1.33+.19*math.sin(t)) for t in [i*math.pi/32 for i in range(33)]],.045,trim)
cube('door-centre-mullion',(0,-.90,.89),(.025,.025,.76),gold)
for x,z in ((-.49,1.92),(.47,2.65)):
    y=-math.sqrt(max(.01,(.84-(z-.35)/3.56*.25)**2-x*x))
    cube('narrow-window-recess',(x,y-.018,z),(.12,.035,.31),stone)
    cube('window-glass',(x,y-.042,z),(.075,.025,.24),light)

# Ribbon is a surface strip following the shaft, with an opening and crossing.
def ribbon(name,points,width):
    verts=[]
    for i,(x,z) in enumerate(points):
        a=Vector(points[max(0,i-1)]);b=Vector(points[min(len(points)-1,i+1)])
        t=(b-a).normalized();n=Vector((-t.y,t.x))*width/2
        for side in (-1,1):
            xx=x+side*n.x;zz=z+side*n.y;r=.84-(zz-.35)/3.56*.25
            yy=-math.sqrt(max(.04,r*r-xx*xx))-.07
            if name.endswith('right'):yy-=.025
            verts.append((xx,yy,zz))
    faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(points)-1)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);finish(o,name,rose)
    solid=o.modifiers.new('woven-ribbon-thickness','SOLIDIFY');solid.thickness=.035
    bevel=o.modifiers.new('soft-satin-edges','BEVEL');bevel.width=.014;bevel.segments=3
    for p in mesh.polygons:p.use_smooth=True

loop=[(.22*math.sin(t),2.77+.43*math.cos(t)) for t in [(-math.pi*.78)+i*(math.pi*1.56)/80 for i in range(81)]]
ribbon('awareness-ribbon-loop',loop,.145)
for sign,name in ((-1,'left'),(1,'right')):
    ribbon('awareness-ribbon-tail-'+name,[(sign*(-.15+.82*t),2.49-.89*t+.08*math.sin(t*math.pi)) for t in [i/45 for i in range(46)]],.17)

# Balcony has separate posts and two continuous brass guard rails.
for z in (4.24,4.51):tube('balcony-rail',[(.96*math.cos(i*math.tau/96),.96*math.sin(i*math.tau/96),z) for i in range(96)],.024,gold,True)
for i in range(20):
    a=i*math.tau/20;tube('balcony-baluster',[(.96*math.cos(a),.96*math.sin(a),4.18),(.96*math.cos(a),.96*math.sin(a),4.53)],.021,gold)
cylinder('lantern-sill',.69,4.36,.12,trim)
cylinder('lantern-light-core',.20,4.82,.70,light)
for i in range(12):
    a=i*math.tau/12; b=(i+1)*math.tau/12
    tube('lantern-mullion',[(.62*math.cos(a),.62*math.sin(a),4.40),(.62*math.cos(a),.62*math.sin(a),5.27)],.022,gold)
    mesh=bpy.data.meshes.new('glass-pane');mesh.from_pydata([(.615*math.cos(t),.615*math.sin(t),z) for t,z in ((a,4.42),(b,4.42),(b,5.25),(a,5.25))],[],[(0,1,2,3)]);mesh.update()
    o=bpy.data.objects.new('lantern-glass-pane',mesh);bpy.context.collection.objects.link(o);finish(o,'lantern-glass-pane',glass)
for z in (4.83,5.28):cylinder('lantern-ring',.66,z,.04,gold)
cylinder('roof-eaves',.79,5.31,.08,roofmat)
# Curved roof profile revolved into twelve visible copper panels.
profile=[(.76,5.35),(.68,5.43),(.54,5.60),(.38,5.76),(.16,5.86),(.055,5.89)]
verts=[(r*math.cos(i*math.tau/48),r*math.sin(i*math.tau/48),z) for r,z in profile for i in range(48)]
faces=[(j*48+i,j*48+(i+1)%48,(j+1)*48+(i+1)%48,(j+1)*48+i) for j in range(len(profile)-1) for i in range(48)]
mesh=bpy.data.meshes.new('domed-roof');mesh.from_pydata(verts,[],faces);mesh.update()
o=bpy.data.objects.new('rose-domed-roof',mesh);bpy.context.collection.objects.link(o);finish(o,'rose-domed-roof',roofmat)
for p in mesh.polygons:p.use_smooth=True
for i in range(12):
    a=i*math.tau/12;tube('roof-standing-seam',[(r*math.cos(a),r*math.sin(a),z+.012) for r,z in profile],.012,rose)
cylinder('finial-base',.13,5.94,.17,rose,.07)
tube('finial-spire',[(0,0,5.95),(0,0,6.21)],.018,gold)

# Export only the tower, before presentation floor/lights/camera are added.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(OUT/'poster-lighthouse-tower-v01.glb'),export_format='GLB',use_selection=True,export_apply=True)
assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])>35
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'poster-lighthouse-tower-v01.blend'))
floor=material('studio-floor',(.055,.085,.10),.85)
cylinder('presentation-floor',200,-.08,.1,floor)
world=bpy.context.scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.21,.27,1);world.node_tree.nodes['Background'].inputs[1].default_value=.4
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for xyz,power,col,size in (((-4,-6,8),1100,(1,.77,.52),5),((4,1,7),1400,(.58,.74,1),4),((1,-4,4),180,(1,.88,.7),3)):
    bpy.ops.object.light_add(type='AREA',location=xyz);o=bpy.context.object;o.data.energy=power;o.data.color=col;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,3))
bpy.ops.object.camera_add(location=(1.8,-12,6));cam=bpy.context.object;aim(cam,(0,0,3));cam.data.type='ORTHO';cam.data.ortho_scale=7.3
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=32
s.render.resolution_x=900;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.view_settings.look='AgX - Medium High Contrast';s.render.filepath=str(OUT/'poster-lighthouse-tower-v01.png')
bpy.ops.render.render(write_still=True)
