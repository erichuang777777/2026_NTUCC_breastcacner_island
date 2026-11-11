from math import cos, pi, sin
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "export" / "surgical-oncology-center-blender-v02.glb"
PREVIEW = ROOT / "export" / "surgical-oncology-center-blender-v02-preview.png"


def material(name, color, metallic=0.0, roughness=.45, transmission=0.0, emission=None):
    value=bpy.data.materials.new(name);value.use_nodes=True;bsdf=value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=color;bsdf.inputs["Metallic"].default_value=metallic;bsdf.inputs["Roughness"].default_value=roughness
    if transmission:bsdf.inputs["Transmission Weight"].default_value=transmission;bsdf.inputs["IOR"].default_value=1.45
    if emission:bsdf.inputs["Emission Color"].default_value=emission;bsdf.inputs["Emission Strength"].default_value=1.8
    return value


def cube(name,loc,scale,mat,bevel=0):
    bpy.ops.mesh.primitive_cube_add(location=loc);obj=bpy.context.object;obj.name=name;obj.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:mod=obj.modifiers.new("architectural-edge","BEVEL");mod.width=bevel;mod.segments=2
    obj.data.materials.append(mat);return obj


def cylinder(name,loc,radius,depth,mat,scale=(1,1,1),vertices=96,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rotation);obj=bpy.context.object;obj.name=name;obj.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);obj.data.materials.append(mat);return obj


def barrel(name,width,depth,spring_z,radius,mat,segments=40):
    verts=[];faces=[]
    for y in (-depth/2,depth/2):
        for index in range(segments+1):
            angle=pi*index/segments;verts.append((width*cos(angle)/2,y,spring_z+radius*sin(angle)))
    row=segments+1
    for index in range(segments):faces.append((index,index+1,row+index+1,row+index))
    faces.extend([tuple(range(row-1,-1,-1)),tuple(range(row,row*2)),(0,row,row*2-1,row-1)])
    mesh=bpy.data.meshes.new(name+"Mesh");mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat);return obj


def arc(name,center,radius,thickness,mat,start=0,end=pi):
    curve=bpy.data.curves.new(name+"Curve","CURVE");curve.dimensions="3D";curve.bevel_depth=thickness;curve.bevel_resolution=3;spline=curve.splines.new("POLY");count=32;spline.points.add(count)
    for index,point in enumerate(spline.points):
        angle=start+(end-start)*index/count;point.co=(center[0]+radius*cos(angle),center[1],center[2]+radius*sin(angle),1)
    obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat);return obj


def window(name,x,z,width,height,glass,frame,y=-3.73):
    cube(name+"-glass",(x,y,z),(width/2,.055,height/2),glass,.025)
    for dx in (-width/2,0,width/2):cube(name+"-mullion",(x+dx,y-.07,z),(.04,.05,height/2+.05),frame,.012)
    for dz in (-height/2,0,height/2):cube(name+"-rail",(x,y-.07,z+dz),(width/2+.04,.05,.04),frame,.012)


bpy.ops.wm.read_factory_settings(use_empty=True)
stone=material("surgical-warm-limestone",(.76,.58,.43,1),roughness=.58);trim=material("surgical-carved-stone",(.92,.77,.60,1),roughness=.46);base=material("surgical-rusticated-base",(.43,.34,.27,1),roughness=.76)
copper=material("surgical-aged-copper",(.40,.15,.105,1),metallic=.58,roughness=.32);patina=material("surgical-patinated-copper",(.08,.31,.25,1),metallic=.52,roughness=.34);frame=material("surgical-dark-frame",(.028,.085,.085,1),metallic=.55,roughness=.24)
glass=material("surgical-warm-glass",(.07,.17,.16,.34),roughness=.08,transmission=.76);warm=material("surgical-warm-interior",(.52,.15,.025,1),roughness=.3,emission=(1,.27,.055,1));rose=material("surgical-emblem-rose",(.48,.11,.09,1),metallic=.18,roughness=.34);green=material("surgical-emblem-leaf",(.18,.38,.12,1),roughness=.42);steel=material("surgical-steel",(.36,.40,.42,1),metallic=.82,roughness=.24);blue=material("surgical-table-blue",(.18,.43,.50,1),roughness=.42)

# Main surgical pavilion.
cylinder("surgical-foundation",(0,0,.42),7.5,.84,base,scale=(1,.54,1));cylinder("surgical-center-body",(0,0,2.42),7.1,3.92,stone,scale=(1,.51,1));cube("surgical-central-hall",(0,.12,3.15),(1.90,3.70,2.72),trim,.38)
cylinder("surgical-base-course",(0,0,1.05),7.18,.72,base,scale=(1,.515,1));cylinder("surgical-copper-tier",(0,.05,4.48),7.42,.54,copper,scale=(1,.525,1));cylinder("surgical-patina-deck",(0,.10,4.76),6.85,.22,patina,scale=(1,.50,1));cylinder("surgical-upper-tier",(0,.38,5.02),6.08,.42,copper,scale=(1,.44,1));cylinder("surgical-upper-deck",(0,.42,5.26),5.56,.18,patina,scale=(1,.41,1))
barrel("surgical-central-barrel",4.08,7.60,5.43,2.04,patina)
for y in [(-3.35+i*.48) for i in range(15)]:arc("surgical-barrel-rib",(0,y,5.43),2.07,.035,copper)

# Glass consultation lounge and operating theatre.
for side in (-1,1):
    for index in range(5):
        x=side*(2.20+index*.98);window(f"surgical-window-{side}-{index}",x,2.72,.82,1.96,glass,frame);cube("surgical-interior-glow",(x,-3.50,2.72),(.27,.05,.74),warm,.02)
cube("surgical-operating-table",(4.15,-3.18,2.15),(1.10,.40,.15),blue,.12);cube("surgical-table-base",(4.15,-3.06,1.78),(.23,.23,.32),steel,.05)
cylinder("surgical-lamp-head",(4.15,-3.08,3.05),.36,.10,steel,vertices=48,rotation=(pi/2,0,0));cube("surgical-lamp-arm",(4.15,-2.95,3.48),(.05,.05,.48),steel,.02)
for index in range(6):
    angle=2*pi*index/6;cylinder("surgical-lamp-light",(4.15+cos(angle)*.20,-3.15,3.05+sin(angle)*.20),.045,.04,warm,vertices=24,rotation=(pi/2,0,0))

# Portal, steps and symmetric accessible ramps.
cube("surgical-entry-recess",(0,-3.83,2.54),(1.28,.18,1.48),frame,.30)
for x in (-.61,.61):cube("surgical-entry-door",(x,-4.04,2.28),(.53,.06,1.12),glass,.03)
for x in (-1.23,0,1.23):cube("surgical-entry-mullion",(x,-4.11,2.54),(.055,.06,1.42),frame,.018)
for x in (-1.50,1.50):cube("surgical-entry-pillar",(x,-4.06,2.60),(.18,.20,1.60),trim,.05)
arc("surgical-entry-arch",(0,-4.12,3.44),1.50,.16,trim)
for index,(width,depth,z) in enumerate(((2.20,.94,.72),(1.92,.66,.90),(1.65,.42,1.08))):cube(f"surgical-entry-step-{index}",(0,-4.08-depth/2,z),(width,depth/2,.11),trim,.08)
for side in (-1,1):
    ramp=cube("surgical-accessible-ramp",(side*2.75,-4.60,.78),(1.28,.56,.10),trim,.06);ramp.rotation_euler.y=side*.13
    for rail_x in (side*1.58,side*3.92):
        for index in range(4):cube("surgical-ramp-post",(rail_x,-4.95+index*.32,1.18),(.025,.025,.40),steel,.01)
        cube("surgical-ramp-rail",(rail_x,-4.45,1.52),(.025,.72,.025),steel,.01)

# Shield, scalpel and laurel emblem.
cylinder("surgical-emblem-disc",(0,-4.05,5.02),1.22,.13,trim,rotation=(pi/2,0,0))
shield=curve_arc=None
for radius,zoff in ((.72,0),(.54,-.04)):arc("surgical-shield",(0,-4.22,5.08+zoff),radius,.075 if radius>.6 else .045,rose,start=pi*.12,end=pi*.88)
knife=cube("surgical-scalpel",(.10,-4.33,5.15),(.72,.055,.105),rose,.05);knife.rotation_euler.y=-.58
cube("surgical-scalpel-handle",(.48,-4.34,5.43),(.32,.06,.13),rose,.05)
for side in (-1,1):
    for index in range(3):
        leaf=cube("surgical-laurel-leaf",(side*(.70+index*.18),-4.23,4.70+index*.28),(.10,.045,.27),green,.08);leaf.rotation_euler.y=side*(.45+index*.12)
for x in (-1.88,1.88):cube("surgical-wall-lantern",(x,-4.08,2.76),(.10,.10,.31),frame,.03);cube("surgical-wall-lantern-glow",(x,-4.19,2.76),(.07,.06,.23),warm,.02)

bpy.ops.object.select_all(action="SELECT");bpy.ops.export_scene.gltf(filepath=str(EXPORT),export_format="GLB",export_apply=True)
cylinder("preview-ground",(0,0,.02),11.5,.10,material("preview-ground-material",(.06,.13,.10,1),roughness=.8))
for location,energy,size,color in (((-10,-13,14),1800,6,(1,.55,.32)),((10,-3,12),1300,6,(.34,.58,1)),((0,8,13),1100,5,(.78,.36,.40))):
    bpy.ops.object.light_add(type="AREA",location=location);light=bpy.context.object;light.data.energy=energy;light.data.shape="DISK";light.data.size=size;light.data.color=color;light.rotation_euler=(-light.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add(location=(17.5,-22.5,14));camera=bpy.context.object;camera.data.lens=53;camera.rotation_euler=(-camera.location).to_track_quat("-Z","Y").to_euler();bpy.context.scene.camera=camera
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=1280;scene.render.resolution_y=820;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.render.filepath=str(PREVIEW);scene.world=bpy.data.worlds.new("surgical-preview-world");scene.world.color=(.018,.028,.055);scene.view_settings.look="AgX - Medium High Contrast";bpy.ops.render.render(write_still=True)
