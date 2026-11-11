"""Photo-guided revision of the existing editable NTUCC model, not a measured BIM."""
from pathlib import Path
from math import sin, cos, pi, atan2
import bpy
from mathutils import Vector

SOURCE=Path(__file__).resolve()
exec(SOURCE.with_name('build_ntucc_v03.py').read_text().split('bpy.ops.wm.read_factory_settings')[0])
ROOT=SOURCE.parent.parent
OUTPUT=ROOT/'export/ntucc-blender-v07.glb'
bpy.ops.wm.read_factory_settings(use_empty=True)

glass=mat('ntucc-v06-blue-grey-glass',(.14,.24,.28,1),.28,.30)
glass_alt=mat('ntucc-v06-glass-variation',(.19,.30,.32,1),.25,.32)
charcoal=mat('ntucc-v06-charcoal-panels',(.11,.14,.17,1),.12,.55)
spandrel=mat('ntucc-v06-grey-floor-spandrels',(.29,.32,.34,1),.12,.58)
aluminum=mat('ntucc-v06-silver-fins',(.59,.64,.64,1),.45,.36)
sandstone=mat('ntucc-v06-sandstone',(.72,.56,.38,1),0,.78)
window_frame=mat('ntucc-v06-wing-window-frames',(.63,.65,.62,1),.12,.65)
concrete=mat('ntucc-v06-roof-concrete',(.56,.57,.53,1),0,.88)
canopy_glass=mat('ntucc-v06-canopy-glass',(.33,.47,.47,1),.15,.4)
roof_metal=mat('ntucc-v06-roof-metal',(.26,.31,.32,1),.35,.55)
pipe=mat('ntucc-v06-green-service-pipes',(.12,.43,.22,1),.2,.5)
sign=mat('ntucc-v06-sign',(.17,.23,.25,1),.15,.5)
rose=mat('ntucc-v06-identity-mark',(.65,.22,.29,1),0,.55)
paving=mat('ntucc-v06-plaza-light',(.69,.69,.63,1),0,.9)
inlay=mat('ntucc-v06-plaza-dark',(.37,.42,.43,1),0,.85)

def ellipse(name,rx,ry,z,depth,material,cy=1.1):
    ob=cylinder(name,(0,cy,z),1,depth,material,96)
    ob.scale.x=rx;ob.scale.y=ry
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return ob

def ring(name,rx,ry,z,h,thickness,material,cy=1.1):
    vertices=[];faces=[];n=96
    for zz in (z-h/2,z+h/2):
        for inset in (0,thickness):
            for i in range(n):
                a=i*2*pi/n;vertices.append(((rx-inset)*cos(a),cy+(ry-inset)*sin(a),zz))
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,2*n+j,2*n+i),(n+j,n+i,3*n+i,3*n+j),(2*n+i,2*n+j,3*n+j,3*n+i),(j,i,n+i,n+j)])
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.data.materials.append(material);return ob

# Continuous curved tower and layered horizontal spandrels seen in the aerial references.
ellipse('v06-main-curved-tower',9.25,3.45,9.1,17.5,glass)
for floor in range(15):
    z=1.05+floor*1.10
    ring(f'v06-floor-spandrel-{floor:02}',9.31,3.51,z,.40,.08,spandrel)
    ring(f'v06-floor-sill-{floor:02}',9.34,3.54,z+.22,.045,.09,aluminum)
for i in range(72):
    a=i*2*pi/72;x,y=9.33*cos(a),1.1+3.53*sin(a)
    beam(f'v06-curtain-mullion-{i:02}',(x,y,.65),(x,y,17.65),.026,aluminum)
    if pi*1.10<a<pi*1.90 and i%2==0:
        beam(f'v06-front-vertical-fin-{i:02}',(x,y-.06,2.0),(x,y-.06,16.75),.054,aluminum)
for side in (-1,1):
    cube(f'v06-service-core-{side}',(side*8.35,1.4,9.15),(.85,2.85,8.85),charcoal,.09)
    for floor in range(14):
        cube(f'v06-core-window-{side}-{floor}',(side*8.35,-1.50,1.2+floor*1.12),(.52,.035,.16),glass_alt,.012)
ellipse('v06-roof-deck',9.25,3.45,18.0,.18,concrete)
ring('v06-continuous-curved-roof-crown',9.38,3.60,18.55,1.05,.20,charcoal)
for i in range(10):
    x=-5.9+i*1.30
    cube(f'v06-roof-chiller-bank-{i}',(x,1.4,18.72),(.59,.82,.60),roof_metal,.035)
    cylinder(f'v06-chiller-fan-{i}',(x,1.4,19.36),.42,.08,charcoal,24)
    for rib in range(6):cube(f'v06-chiller-grille-{i}-{rib}',(x-.46+rib*.18,.56,18.72),(.025,.025,.49),aluminum)
for y in (-.05,.28):beam('v06-green-service-header',(-6.5,y,18.26),(6.5,y,18.26),.10,pipe)
for i in range(5):beam('v06-service-branch',(-5+i*2.5,0,18.26),(-5+i*2.5,1.0,18.26),.07,pipe)

# Staggered sandstone wings, window recesses on both front and exposed outer faces.
for side in (-1,1):
    cx=side*10.5;cy=-1.15 if side<0 else -2.40;height=8.6 if side<0 else 9.2;wx=3.20;wy=4.8 if side<0 else 5.35
    cube(f'v06-clinical-wing-{side}',(cx,cy,height/2+.25),(wx,wy,height/2),sandstone,.08)
    cube(f'v06-wing-roof-{side}',(cx,cy,height+.27),(wx-.14,wy-.14,.10),concrete,.025)
    for yy in (cy-wy+.08,cy+wy-.08):cube('v06-wing-parapet',(cx,yy,height+.55),(wx,.08,.34),sandstone,.025)
    for xx in (cx-wx+.08,cx+wx-.08):cube('v06-wing-parapet',(xx,cy,height+.55),(.08,wy,.34),sandstone,.025)
    for floor in range(7):
        z=1.10+floor*1.03
        for col in range(5):
            x=cx-2.35+col*1.17
            cube(f'v06-wing-recess-front-{side}-{floor}-{col}',(x,cy-wy-.025,z),(.43,.035,.39),window_frame,.016)
            cube(f'v06-wing-glass-front-{side}-{floor}-{col}',(x,cy-wy-.065,z),(.34,.02,.31),glass if col%2 else glass_alt,.008)
            cube('v06-wing-window-divider',(x,cy-wy-.091,z),(.018,.016,.31),aluminum)
        for col in range(8):
            y=cy-wy+.72+col*(wy*2-1.44)/7
            cube(f'v06-wing-recess-side-{side}-{floor}-{col}',(cx+side*(wx+.025),y,z),(.035,.40,.39),window_frame,.014)
            cube(f'v06-wing-glass-side-{side}-{floor}-{col}',(cx+side*(wx+.065),y,z),(.02,.31,.31),glass,.008)
    for i in range(6):
        x=cx-1.9+(i%3)*1.9;y=cy-1.1+(i//3)*2.1
        cube('v06-wing-cooling-unit',(x,y,height+.65),(.48,.60,.35),roof_metal,.025)
        cylinder('v06-wing-cooling-fan',(x,y,height+1.03),.28,.06,charcoal,20)

# Recessed entry, sliding doors, radial lobby and long segmented arrival canopy.
cube('v06-main-entry-recess',(0,-3.0,1.6),(3.1,.25,1.4),charcoal,.035)
for i in range(8):
    x=-2.55+i*.73
    cube('v06-main-entry-door',(x,-3.29,1.45),(.32,.035,1.15),canopy_glass,.014)
    cube('v06-entry-mullion',(x-.36,-3.34,1.45),(.023,.025,1.18),aluminum)
cube('v06-main-entry-roof',(0,-4.5,3.0),(3.5,1.65,.12),aluminum,.035)
for i in range(10):cube('v06-entry-roof-rib',(-3.15+i*.7,-4.5,3.14),(.025,1.65,.025),roof_metal)
cylinder('v06-round-glass-lobby',(3.1,-4.9,1.45),1.20,2.65,canopy_glass,48)
cylinder('v06-round-lobby-roof',(3.1,-4.9,2.84),1.28,.12,aluminum,48)
for i in range(16):
    a=i*pi/8;x=3.1+1.21*cos(a);y=-4.9+1.21*sin(a);beam('v06-lobby-mullion',(x,y,.2),(x,y,2.80),.022,aluminum)
for i in range(22):
    a=(-38+i*76/22)*pi/180;b=(-38+(i+1)*76/22)*pi/180
    p=Vector((15*sin(a),-11.2+15*(1-cos(a)),2.45));q=Vector((15*sin(b),-11.2+15*(1-cos(b)),2.45));mid=(p+q)/2;length=(q-p).length;angle=atan2(q.y-p.y,q.x-p.x)
    cube('v06-arrival-canopy-frame',mid,(length/2+.025,1.0,.10),aluminum,.025,angle)
    cube('v06-arrival-canopy-skylight',(mid.x,mid.y,mid.z+.11),(length/2-.035,.56,.025),canopy_glass,.01,angle)
    if i%2==0:cube('v06-arrival-canopy-column',(p.x,p.y,1.2),(.055,.055,1.2),aluminum,.012)
cube('v06-entry-plaza',(0,-7.0,.10),(14.1,5.6,.10),paving,.06)
for i in range(20):cube('v06-paving-joint',(-13.5+i*1.4,-7,.205),(.018,5.3,.008),inlay)
for i in range(7):
    bpy.ops.mesh.primitive_torus_add(major_segments=72,minor_segments=4,location=(6.2,-9.5,.22),major_radius=.35+i*.18,minor_radius=.025)
    ob=bpy.context.object;ob.name='v06-concentric-arrival-paving';ob.scale.y=.75;ob.data.materials.append(inlay)
text_mesh('v06-hospital-sign-zh','臺大癌醫中心',(-10.5,-6.02,8.0),.58,sign)
text_mesh('v06-hospital-sign-en','NTU CANCER CENTER',(-10.5,-6.03,7.43),.23,sign)
text_mesh('v06-hospital-identity','✚',(-13.0,-6.04,7.8),.65,rose)

# Front low-rise podium and stepped side volumes visible in ntucc-ref-3.jpg.
# This is photo-guided massing, not a surveyed reconstruction of additional campus towers.
for side in (-1,1):
    for step in range(3):
        x=side*(7.5+step*2.2);height=3.7-step*.55
        cube(f'v07-terraced-clinic-{side}-{step}',(x,-8.0,height/2+.25),(1.05,1.1,height/2),sandstone,.065)
        cube(f'v07-terrace-cap-{side}-{step}',(x,-8.0,height+.3),(1.08,1.14,.10),aluminum,.025)
        for level in range(2):
            for window in range(3):
                cube(f'v07-wing-glass-{side}-{step}-{level}-{window}',(x-.65+window*.65,-9.12,1+level*1.15),(.25,.035,.35),glass,.01)
        for post in range(5):cube('v07-roof-garden-railing',(x-.95+post*.475,-9.0,height+.55),(.018,.018,.22),aluminum)
        beam('v07-roof-garden-handrail',(x-1,-9,height+.77),(x+1,-9,height+.77),.025,aluminum)
for i in range(16):
    x=-5.8+i*.77;y=-7.5+.012*x*x
    cube('v07-curved-clinical-podium',(x,y,1.6),(.40,.65,1.4),sandstone,.035)
    cube('v07-wing-glass-podium',(x,y-.67,1.5),(.27,.035,.80),glass,.01)
    cube('v07-podium-roof-edge',(x,y,3.08),(.41,.72,.10),aluminum,.02)
text_mesh('v07-campus-arrival-sign','NTU CANCER CENTER',(0,-8.2,2.65),.32,sign)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'export/ntucc-blender-v07.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUTPUT),export_format='GLB',export_apply=True)

print('EXPORTED',OUTPUT)
