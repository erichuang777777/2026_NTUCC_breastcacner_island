from math import atan, cos, pi, sin, sqrt
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parent.parent
EXPORT=ROOT/"export"/"reconstruction-center-blender-v03.glb"
PREVIEW=ROOT/"export"/"reconstruction-center-blender-v03-preview.png"

def mat(name,color,metallic=0,roughness=.45,transmission=0,emission=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get("Principled BSDF");b.inputs["Base Color"].default_value=color;b.inputs["Metallic"].default_value=metallic;b.inputs["Roughness"].default_value=roughness
    if transmission:b.inputs["Transmission Weight"].default_value=transmission;b.inputs["IOR"].default_value=1.45
    if emission:b.inputs["Emission Color"].default_value=emission;b.inputs["Emission Strength"].default_value=1.8
    return m

def cube(name,loc,scale,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:mod=o.modifiers.new("architectural-edge","BEVEL");mod.width=bevel;mod.segments=2
    o.data.materials.append(m);return o

def cyl(name,loc,radius,depth,m,scale=(1,1,1),vertices=96,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rotation);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o

def sphere(name,loc,scale,m,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,location=loc,rotation=rotation);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);return o

def arc(name,center,radius,thickness,m,start=0,end=pi):
    c=bpy.data.curves.new(name+"Curve","CURVE");c.dimensions="3D";c.bevel_depth=thickness;c.bevel_resolution=3;s=c.splines.new("POLY");count=32;s.points.add(count)
    for i,p in enumerate(s.points):a=start+(end-start)*i/count;p.co=(center[0]+radius*cos(a),center[1],center[2]+radius*sin(a),1)
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o

def ribbon_curve(name,points,thickness,m):
    c=bpy.data.curves.new(name+"Curve","CURVE");c.dimensions="3D";c.bevel_depth=thickness;c.bevel_resolution=4;s=c.splines.new("BEZIER");s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points):p.co=co;p.handle_left_type="AUTO";p.handle_right_type="AUTO"
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o

def window(name,x,y,z,width,height,glass,frame,rotation_z=0.0):
    panel=cube(name+"-glass",(x,y,z),(width/2,.055,height/2),glass,.025);panel.rotation_euler.z=rotation_z
    for dx in (-width/2,0,width/2):
        mullion=cube(name+"-mullion",(x+dx*cos(rotation_z),y+dx*sin(rotation_z),z),(.04,.05,height/2+.05),frame,.012);mullion.rotation_euler.z=rotation_z
    for dz in (-height/2,0,height/2):
        rail=cube(name+"-rail",(x,y,z+dz),(width/2+.04,.05,.04),frame,.012);rail.rotation_euler.z=rotation_z

bpy.ops.wm.read_factory_settings(use_empty=True)
stone=mat("reconstruction-warm-limestone",(.78,.61,.47,1),roughness=.58);trim=mat("reconstruction-carved-stone",(.94,.80,.64,1),roughness=.46);base=mat("reconstruction-rusticated-base",(.44,.35,.29,1),roughness=.76);pink=mat("reconstruction-petal-copper",(.62,.22,.27,1),metallic=.42,roughness=.35);pink_light=mat("reconstruction-petal-highlight",(.83,.38,.43,1),metallic=.32,roughness=.32);sage=mat("reconstruction-sage-trim",(.30,.40,.27,1),metallic=.32,roughness=.36);frame=mat("reconstruction-dark-frame",(.035,.085,.08,1),metallic=.54,roughness=.24);glass=mat("reconstruction-warm-glass",(.08,.17,.16,.34),roughness=.08,transmission=.76);warm=mat("reconstruction-warm-interior",(.52,.15,.025,1),roughness=.3,emission=(1,.27,.055,1));rose=mat("reconstruction-ribbon-rose",(.62,.22,.28,1),metallic=.18,roughness=.34);green=mat("reconstruction-emblem-leaf",(.18,.38,.12,1),roughness=.42);brass=mat("reconstruction-brass",(.55,.34,.13,1),metallic=.75,roughness=.26);cream=mat("reconstruction-display-ceramic",(.82,.62,.53,1),roughness=.38)

# Rounded consultation center.
cyl("reconstruction-foundation",(0,0,.42),7.5,.84,base,scale=(1,.54,1));cyl("reconstruction-center-body",(0,0,2.42),7.1,3.92,stone,scale=(1,.51,1));cube("reconstruction-central-hall",(0,.12,3.02),(2.22,3.50,2.55),trim,.48);cyl("reconstruction-base-course",(0,0,1.05),7.18,.72,base,scale=(1,.515,1));cyl("reconstruction-roof-deck",(0,.08,4.55),7.38,.42,pink,scale=(1,.52,1));cyl("reconstruction-roof-trim",(0,.10,4.82),7.46,.16,sage,scale=(1,.525,1))

# Five low, overlapping petal roofs unfold visibly to both sides of the central facade.
petal_layout=((-4.15,.42,-.28),(-2.25,1.02,-.10),(0,1.42,0),(2.25,1.02,.10),(4.15,.42,.28))
for index,(x,y,angle) in enumerate(petal_layout):
    petal=sphere(f"reconstruction-petal-{index}",(x,y,5.25),(2.30,.78,.28),pink_light,rotation=(0,.11,angle));petal.rotation_euler.z=angle
    rim=sphere(f"reconstruction-petal-rim-{index}",(x,y,5.30),(2.35,.82,.055),brass,rotation=(0,.11,angle));rim.rotation_euler.z=angle
sphere("reconstruction-central-bud",(0,1.25,5.54),(2.18,1.42,.62),pink)

# Curved glazing and warm consultation/display rooms.
for side in (-1,1):
    for index in range(5):
        x=side*(2.20+index*.98);ellipse=max(.08,1-(x/7.10)**2);y=-3.62*sqrt(ellipse);slope=3.62*x/(7.10*7.10*sqrt(ellipse));tangent=atan(slope)
        window(f"reconstruction-window-{side}-{index}",x,y-.10,2.76,.82,2.08,glass,frame,tangent);cube("reconstruction-interior-glow",(x,y+.10,2.72),(.27,.05,.74),warm,.02)
for x in (3.65,4.55):
    sphere("reconstruction-display-form",(x,-3.18,2.28),(.28,.20,.48),cream);cube("reconstruction-display-plinth",(x,-3.18,1.80),(.34,.22,.08),brass,.04)

# Entrance and right-side accessible ramp.
cube("reconstruction-entry-recess",(0,-3.83,2.54),(1.28,.18,1.48),frame,.30)
for x in (-.61,.61):cube("reconstruction-entry-door",(x,-4.04,2.28),(.53,.06,1.12),glass,.03)
for x in (-1.23,0,1.23):cube("reconstruction-entry-mullion",(x,-4.11,2.54),(.055,.06,1.42),frame,.018)
for x in (-1.50,1.50):cube("reconstruction-entry-pillar",(x,-4.06,2.60),(.18,.20,1.60),trim,.05)
arc("reconstruction-entry-arch",(0,-4.12,3.44),1.50,.16,trim)
for index,(width,depth,z) in enumerate(((2.20,.94,.72),(1.92,.66,.90),(1.65,.42,1.08))):cube(f"reconstruction-step-{index}",(0,-4.08-depth/2,z),(width,depth/2,.11),trim,.08)
ramp=cube("reconstruction-accessible-ramp",(3.15,-4.58,.79),(1.70,.60,.10),trim,.06);ramp.rotation_euler.y=.13
for rail_x in (1.52,4.78):
    for index in range(5):cube("reconstruction-ramp-post",(rail_x,-5.10+index*.31,1.18),(.025,.025,.40),brass,.01)
    cube("reconstruction-ramp-rail",(rail_x,-4.48,1.52),(.025,.80,.025),brass,.01)

# Reconstruction ribbon, botanical support and scar-repair motif.
cyl("reconstruction-emblem-disc",(0,-4.05,5.05),1.24,.13,trim,rotation=(pi/2,0,0))
ribbon_curve("reconstruction-awareness-ribbon",[(0,-4.24,5.92),(-.35,-4.24,5.55),(.18,-4.24,5.05),(.42,-4.24,4.66),(-.12,-4.24,4.38)],.095,rose)
for side in (-1,1):
    for index in range(3):
        leaf=cube("reconstruction-emblem-leaf",(side*(.66+index*.18),-4.23,4.64+index*.28),(.11,.045,.28),green,.08);leaf.rotation_euler.y=side*(.45+index*.12)
for z in (4.48,4.70,4.92,5.14):cube("reconstruction-repair-stitch",(0,-4.35,z),(.055,.04,.055),rose,.02)
for x in (-1.88,1.88):cube("reconstruction-wall-lantern",(x,-4.08,2.76),(.10,.10,.31),frame,.03);cube("reconstruction-wall-lantern-glow",(x,-4.19,2.76),(.07,.06,.23),warm,.02)

bpy.ops.object.select_all(action="SELECT");bpy.ops.export_scene.gltf(filepath=str(EXPORT),export_format="GLB",export_apply=True)
cyl("preview-ground",(0,0,.02),11.5,.10,mat("preview-ground-material",(.06,.13,.10,1),roughness=.8))
for location,energy,size,color in (((-10,-13,14),1800,6,(1,.55,.32)),((10,-3,12),1300,6,(.34,.58,1)),((0,8,13),1100,5,(.78,.36,.40))):
    bpy.ops.object.light_add(type="AREA",location=location);l=bpy.context.object;l.data.energy=energy;l.data.shape="DISK";l.data.size=size;l.data.color=color;l.rotation_euler=(-l.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add(location=(17.5,-22.5,14));camera=bpy.context.object;camera.data.lens=53;camera.rotation_euler=(-camera.location).to_track_quat("-Z","Y").to_euler();bpy.context.scene.camera=camera
s=bpy.context.scene;s.render.engine="BLENDER_EEVEE";s.render.resolution_x=1280;s.render.resolution_y=820;s.render.resolution_percentage=100;s.render.image_settings.file_format="PNG";s.render.filepath=str(PREVIEW);s.world=bpy.data.worlds.new("reconstruction-preview-world");s.world.color=(.018,.028,.055);s.view_settings.look="AgX - Medium High Contrast";bpy.ops.render.render(write_still=True)
