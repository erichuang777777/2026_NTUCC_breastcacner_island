"""Blender --background --python /absolute/path/build_prop_kit_v02.py.
Authoring coordinates: web X/Y/Z; xyz maps to Blender X/-Z/Y.
No viewport operators. All modifiers baked through evaluated mesh data.
"""
from pathlib import Path
import json
import math
import hashlib
import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'export' / 'v02'
PALETTE = {
    'cream': '#E9D8B9', 'wood': '#C69365', 'wood-light': '#DBAE7C',
    'iron': '#505655', 'blue': '#668FA8', 'leaf': '#789559',
    'leaf-light': '#A0B66B', 'leaf-dark': '#52744F', 'soil': '#938365',
    'pink': '#DF98A6', 'white': '#FFF4DF', 'yellow': '#F2CE79',
    'paving-pink': '#D9A79B', 'rock': '#A4A69E', 'rock-light': '#BEBCAF',
    'moss': '#A4B875', 'water': '#76C6D8', 'foam': '#F6FFF5', 'lamp-glow': '#FFE5AB',
}
IDS = ['bench', 'lamp', 'flowerbed-round', 'flowerbed-long', 'shrub-cluster',
       'tree-round', 'path-straight', 'path-curve', 'path-plaza',
       'rock-shore-a', 'rock-shore-b', 'foam-ring', 'signpost']
BUDGETS = {i: (300, 1500) for i in IDS}
BUDGETS.update({i: (1500, 4000) for i in ['flowerbed-round', 'flowerbed-long', 'tree-round']})
BUDGETS.update({i: (800, 2500) for i in ['rock-shore-a', 'rock-shore-b']})
SOURCES = {
    'bench': ['webgl-prototype/hope-landscapes.js:22; seat .70/.07/.27, back top .63'],
    'lamp': ['webgl-prototype/taiwan-study.js:69; ground .70, pole top 1.30, shade top 1.45'],
    'flowerbed-round': ['webgl-prototype/hope-landmark-gardens.js:11-17; diameter .74, wall .11, flower top .525'],
    'flowerbed-long': ['Derived module: twice the round bed diameter; no same-shape existing asset'],
    'shrub-cluster': ['Derived from webgl-prototype/hope-environment.js:63; ground cluster radius .20; new three-size shrub silhouette'],
    'tree-round': ['webgl-prototype/hope-environment.js:70-75; round crown .45/.34/.36, scale .70/.82/.94; use .82'],
    'path-straight': ['New module 1.20; webgl-prototype/taiwan-study.js:58 has no path mesh; :63 reserves .72 from route center'],
    'path-curve': ['New 2x2 module, same 1.20 width; inner radius 1.20, outer radius 2.40'],
    'path-plaza': ['New 1.20 square module; same paving pitch and height'],
    'rock-shore-a': ['webgl-prototype/hope-environment.js:60; radii .22/.29/.36, y scale .70; layered reinterpretation'],
    'rock-shore-b': ['Same source as rock-shore-a; new alternate arrangement'],
    'foam-ring': ['New local ring sized to shore rocks; webgl-prototype/hope-environment.js:12 uses island-wide lines, not a prop'],
    'signpost': ['New upright sign; webgl-prototype/hope-landmark-gardens.js:30-33 plaque is 1.50 wide, top 1.4325, ground .70; use .7325 height'],
}
MATS = {}
PARTS = []


def xyz(p):
    return (p[0], -p[2], p[1])


def linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4


def material(key):
    name = 'hope-prop-' + key
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    rgb = tuple(linear(int(PALETTE[key][i:i + 2], 16) / 255) for i in (1, 3, 5))
    alpha = .62 if key == 'water' else 1.0
    m.diffuse_color = (*rgb, alpha)
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Alpha'].default_value = alpha
    bs.inputs['Roughness'].default_value = .65 if key == 'foam' else .72
    bs.inputs['Metallic'].default_value = 0
    bs.inputs['Emission Color'].default_value = (*rgb, 1)
    bs.inputs['Emission Strength'].default_value = .7 if key == 'lamp-glow' else 0
    if key == 'water':
        m.surface_render_method = 'DITHERED'
        m.use_backface_culling = False
    MATS[name] = m
    return m


def bake(o):
    bpy.context.view_layer.update()
    old = o.data
    evaluated = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    data = bpy.data.meshes.new_from_object(evaluated, depsgraph=bpy.context.evaluated_depsgraph_get())
    o.modifiers.clear()
    o.data = data
    if old.users == 0:
        bpy.data.meshes.remove(old)


def mesh(name, vertices, faces, tone, bevel=0, smooth=False):
    data = bpy.data.meshes.new(name)
    data.from_pydata([xyz(p) for p in vertices], [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    o = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(o)
    data.materials.append(material(tone))
    for p in data.polygons:
        p.use_smooth = smooth
    if bevel:
        for polygon in data.polygons:
            polygon.use_smooth = True
        mod = o.modifiers.new('Soft clay edges - baked', 'BEVEL')
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = 'ANGLE'
        mod.angle_limit = .35
        bake(o)
        normal = o.modifiers.new('Weighted corner normals - baked', 'WEIGHTED_NORMAL')
        normal.keep_sharp = True
        normal.weight = 50
        bake(o)
    PARTS.append(o)
    return o


def box(name, p, size, tone, bevel=.01):
    vertices = [(p[0] + a * size[0] / 2, p[1] + b * size[1] / 2,
                 p[2] + c * size[2] / 2) for a, b, c in
                [(-1,-1,-1), (1,-1,-1), (1,-1,1), (-1,-1,1),
                 (-1,1,-1), (1,1,-1), (1,1,1), (-1,1,1)]]
    return mesh(name, vertices, [(0,3,2,1),(4,5,6,7),(0,1,5,4),
                                (1,2,6,5),(2,3,7,6),(3,0,4,7)], tone,
                min(bevel, min(size) * .4))


def ell(name, p, scale, tone, n=12, rings=7):
    vertices = [(p[0], p[1] + scale[1], p[2])]
    for j in range(1, rings):
        t = math.pi * j / rings
        for k in range(n):
            a = math.tau * k / n
            vertices.append((p[0] + scale[0] * math.sin(t) * math.cos(a),
                             p[1] + scale[1] * math.cos(t),
                             p[2] + scale[2] * math.sin(t) * math.sin(a)))
    bottom = len(vertices)
    vertices.append((p[0], p[1] - scale[1], p[2]))
    faces = []
    for k in range(n):
        faces.append((0, 1+k, 1+(k+1)%n))
        for j in range(rings-2):
            a = 1+j*n+k; b = 1+j*n+(k+1)%n
            faces.append((a, a+n, b+n, b))
        a = 1+(rings-2)*n
        faces.append((bottom, a+(k+1)%n, a+k))
    return mesh(name, vertices, faces, tone, smooth=True)


def post(name, p, radius, height, tone, n=10, top=None, bevel=.006):
    top = radius if top is None else top
    vertices = [(p[0]+r*math.cos(k*math.tau/n), p[1]+h,
                 p[2]+r*math.sin(k*math.tau/n))
                for r,h in [(radius,-height/2),(top,height/2)] for k in range(n)]
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces += [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
    return mesh(name, vertices, faces, tone, bevel, smooth=True)


def leaf(x, y, z, size, angle, tone='leaf'):
    # Closed pointed blade: four elliptical cross-sections and two tapered tips.
    n = 6
    vertices = [(x, y, z)]
    for t, width in [(.23,.65),(.50,1),(.77,.62)]:
        for k in range(n):
            a = math.tau*k/n
            side = math.cos(a)*size*.25*width
            depth = math.sin(a)*size*.10*width + size*.25*t*t
            vertices.append((x+side*math.cos(angle)+depth*math.sin(angle),
                             y+size*t,z-side*math.sin(angle)+depth*math.cos(angle)))
    vertices.append((x+size*.25*math.sin(angle),y+size,z+size*.25*math.cos(angle)))
    faces = [(0,1+(k+1)%n,1+k) for k in range(n)]
    for j in range(2):
        for k in range(n):
            a=1+j*n+k;b=1+j*n+(k+1)%n
            faces.append((a,b,b+n,a+n))
    faces += [(19,13+k,13+(k+1)%n) for k in range(n)]
    return mesh('pointed-leaf',vertices,faces,tone,smooth=True)


def flower(x, y, z, tone, r=.075):
    # Front-tilted flower face keeps all five petals readable in an isometric view.
    for k in range(5):
        a=math.tau*k/5
        ell('petal',(x+math.cos(a)*r*.70,y+math.sin(a)*r*.35,z+math.sin(a)*r*.60),
            (r*.51,r*.25,r*.48),tone,n=8,rings=3)
    ell('pollen',(x,y+r*.18,z+.008),(r*.29,r*.22,r*.29),'yellow',n=8,rings=3)


def bench():
    for z in [-.09, 0, .09]:
        box('seat-slat',(0,.30,z),(.70,.07,.084),'wood-light',.012)
    for y in [.405,.555]:
        box('back-slat',(0,y,-.1125),(.70,.15,.045),'wood',.014)
    for x in [-.2875,.2875]:
        for z in [-.09,.09]:
            box('cast-iron-leg',(x,.14,z),(.045,.28,.045),'iron',.012)
        box('cast-iron-arm',(x,.405,0),(.055,.055,.27),'iron',.018)
        box('arm-support',(x,.34,.09),(.045,.14,.045),'iron',.012)


def lamp():
    post('cream-pedestal',(0,.045,0),.075,.09,'cream',12,top=.068,bevel=.012)
    post('dark-round-pole',(0,.34,0),.027,.51,'iron',12,top=.022,bevel=.004)
    box('lantern-lower-frame',(0,.567,0),(.164,.028,.164),'yellow',.006)
    box('four-sided-glowing-glass',(0,.633,0),(.126,.108,.126),'lamp-glow',.008)
    for x in [-.067,.067]:
        for z in [-.067,.067]:
            box('lantern-corner',(x,.633,z),(.013,.114,.013),'cream',.003)
    box('lantern-upper-frame',(0,.697,0),(.164,.023,.164),'yellow',.006)
    mesh('pointed-lantern-roof',[(-.082,.709,-.082),(.082,.709,-.082),
         (.082,.709,.082),(-.082,.709,.082),(0,.75,0)],
         [(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'cream',.004)


def bed(long=False):
    if long:
        # Individual chamfered limestone blocks enclose a planted interior.
        for z in [-.327,.327]:
            for j in range(5):
                box('wall-block',((j-2)*.292,.055,z),(.289,.11,.086),'cream',.012)
        for x in [-.696,.696]:
            for z in [-.16,.16]:
                box('wall-block',(x,.055,z),(.086,.11,.231),'cream',.012)
        box('soil',(0,.07,0),(1.32,.07,.58),'soil',.009)
        points=[(-.52+.26*j,z) for j in range(5) for z in [-.14,.14]]
    else:
        for j in range(12):
            a0=math.tau*(j+.025)/12;a1=math.tau*(j+.975)/12
            outline=[(r*math.cos(a),r*math.sin(a)) for r,a in
                     [(.29,a0),(.37,a0),(.37,a1),(.29,a1)]]
            vertices=[(x,y,z) for y in [0,.11] for x,z in outline]
            mesh('wall-block',vertices,[(0,3,2,1),(4,5,6,7),(0,1,5,4),
                 (1,2,6,5),(2,3,7,6),(3,0,4,7)],'cream',.009)
        post('soil',(0,.065,0),.30,.075,'soil',20,bevel=0)
        points=[(0,0)]+[(math.cos(j*math.tau/6)*.19,math.sin(j*math.tau/6)*.19) for j in range(6)]
    for j,(x,z) in enumerate(points):
        ell('dense-foliage',(x,.17,z),(.15,.115,.14),['leaf','leaf-light','leaf-dark'][j%3],n=8,rings=3 if long else 4)
        leaf(x+.045,.16,z-.02,.20+(j%3)*.035,j*2.4,['leaf','leaf-dark'][j%2])
    blooms=points[:8] if long else points+[(.10,.08),(-.10,-.08)]
    for j,(x,z) in enumerate(blooms):
        h=.30+(j%3)*.07
        post('flower-stem',(x,(h+.16)/2,z),.007,h-.16,'leaf-dark',5,bevel=0)
        flower(x,h,z,['pink','white','pink'][j%3],.078 if j%2 else .085)


def shrub():
    for j,(x,z,r) in enumerate([(-.21,0,.16),(0,-.02,.23),(.23,.03,.15),
            (-.12,.17,.12),(.12,.17,.13),(0,-.18,.13),(-.28,.13,.095),
            (.27,.16,.09),(-.18,-.14,.12),(.18,-.15,.115)]):
        ell('leaf-cloud',(x,r*.83,z),(r,r*.83,r*.85),
            ['leaf','leaf-light','leaf-dark'][j%3],n=8,rings=5)
    for j in range(6):
        a=j*math.tau/6
        leaf(.26*math.cos(a),.07,.18*math.sin(a),.23,a,'leaf-dark' if j%2 else 'leaf')
    for x,y,z in [(-.17,.24,.13),(.15,.19,.20),(.04,.35,.03)]:
        flower(x,y,z,'pink' if x<0 else 'white',.064)


def tree():
    # Curved taper, with a flared root collar rather than a straight cylinder.
    n=12
    levels=[(0,0,.15),(.06,-.012,.105),(.24,-.04,.065),(.48,-.01,.055),(.77,.035,.045)]
    vertices=[(cx+r*math.cos(k*math.tau/n),y,r*math.sin(k*math.tau/n))
              for y,cx,r in levels for k in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range(4*n,5*n))]
    faces += [(j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k)
              for j in range(4) for k in range(n)]
    mesh('curved-flared-trunk',vertices,faces,'wood',smooth=True)
    post('grass-disc',(0,.024,0),.27,.048,'leaf-light',32,bevel=.008)
    for j,(x,y,z,r) in enumerate([(0,1.02,-.04,.255),(-.235,.85,0,.245),(.23,.88,.01,.245),
          (-.13,1.08,.05,.22),(.16,1.06,.05,.205),(-.10,.87,.22,.205),(.15,.86,.20,.18)]):
        ell('soft-canopy',(x,y,z),(r,r*.94,r),['leaf','leaf-light','leaf'][j%3],n=16,rings=10)
    for j in range(6):
        a=j*2.4
        leaf(math.cos(a)*.16,.04,math.sin(a)*.16,.12,a,'leaf')
    flower(-.16,.08,.15,'white',.044)
    flower(.15,.09,.13,'pink',.045)


PATH_WIDTH = 1.2
PATH_HEIGHT = .06
PATH_PORTS = {
    'path-straight': [{'position':[0,0,-.6],'outward':[0,0,-1]}, {'position':[0,0,.6],'outward':[0,0,1]}],
    'path-plaza': [{'position':p,'outward':n} for p,n in
                   [([0,0,-.6],[0,0,-1]),([0,0,.6],[0,0,1]),([-.6,0,0],[-1,0,0]),([.6,0,0],[1,0,0])]],
    'path-curve': [{'position':[.6,0,-1.2],'outward':[0,0,-1]}, {'position':[-1.2,0,.6],'outward':[-1,0,0]}],
}


def path(kind):
    if kind != 'curve':
        for row in range(3):
            for col in range(3):
                # No end cap on straight; all edge tiles on plaza are cream.
                cream = col != 1 or (kind == 'plaza' and row != 1)
                box('paver',((col-1)*.4,.03,(row-1)*.4),(.4,.06,.4),
                    'cream' if cream else 'paving-pink',.009)
    else:
        for row in range(3):
            for col in range(3):
                inner = 1.2+col*.4
                outer = inner+.4
                a0 = row*math.pi/6; a1 = (row+1)*math.pi/6
                angles = [a0, (a0+a1)/2, a1]
                outline = [(r*math.cos(a)-1.2,r*math.sin(a)-1.2)
                           for r,aa in [(inner,angles),(outer,list(reversed(angles)))] for a in aa]
                vertices = [(x,y,z) for y in [0,.06] for x,z in outline]
                n=len(outline)
                faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
                faces += [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
                mesh('curved-paver',vertices,faces,'paving-pink' if col==1 else 'cream',.009)


def rock_piece(x,z,r,h,phase):
    n=10
    vertices=[]
    # Narrow, offset strata preserve vertical cliff grooves without faceted balls.
    profile=[(0,.88),(.19,.98),(.23,.93),(.48,1),(.52,.94),(.78,.96),(1,.78)]
    for level,(height,scale) in enumerate(profile):
        for k in range(n):
            a=k*math.tau/n
            wobble=1+.075*math.sin(k*2.3+phase)
            vertices.append((x+math.cos(a)*r*scale*wobble+.012*math.sin(level+phase),
                             h*height,z+math.sin(a)*r*scale*wobble))
    faces=[tuple(reversed(range(n))),tuple(range(6*n,7*n))]
    faces += [(j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k)
              for j in range(6) for k in range(n)]
    mesh('stratified-cliff',vertices,faces,'rock' if phase<2 else 'rock-light',smooth=True)
    # A single closed moss blanket follows the top and drops unevenly over the rim.
    vertices=[(x,h+.018,z)]
    for row in range(3):
        for k in range(20):
            a=k*math.tau/20
            rr=r*(.61 if row==0 else .81)*(1+.055*math.sin(a*7+phase))
            yy=h+.014 if row==0 else h-.008 if row==1 else h-.035-.075*(.5+.5*math.sin(a*7+phase))**3
            vertices.append((x+rr*math.cos(a),yy,z+rr*math.sin(a)))
    faces=[(0,1+k,1+(k+1)%20) for k in range(20)]
    faces += [(1+j*20+k,1+j*20+(k+1)%20,1+(j+1)*20+(k+1)%20,1+(j+1)*20+k)
              for j in range(2) for k in range(20)]
    faces.append(tuple(reversed(range(41,61))))
    mesh('draped-moss',vertices,faces,'moss',smooth=True)
    if phase<2:
        flower(x,h+.04,z,'white',.035)
        for j in range(2):leaf(x+r*.35,h-.01,z+j*.035,.09,j+phase,'leaf')


def shore(variant):
    placements=[(-.22,-.08,.24,.36),(.16,-.09,.28,.51),(.04,.24,.19,.24)]
    if variant:
        placements=[(-.22,-.02,.25,.49),(.16,-.09,.27,.45),(.23,.22,.18,.27)]
    for j,(x,z,r,h) in enumerate(placements):rock_piece(x,z,r,h,j+variant*.3)
    foam(small=True)


def foam(small=False):
    # Closed translucent water slab and solid, scalloped foam tubes.
    n=64
    radius=.65 if small else .71
    vertices=[]
    for y in [0,.022]:
        for k in range(n):
            a=k*math.tau/n;r=radius+.025*math.sin(a*7)+.018*math.cos(a*11)
            vertices.append((math.cos(a)*r,y,math.sin(a)*r*.81))
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
    mesh('translucent-water-plinth',vertices,faces,'water',smooth=True)
    for layer in range(1 if small else 2):
        vertices=[]
        segments=64 if small else 72
        for k in range(segments):
            a=k*math.tau/segments
            radius2=radius-.025-layer*.10+.021*math.sin(a*7)+.016*math.cos(a*11)
            for j in range(4):
                b=j*math.tau/4
                width=(.014 if small else .018)*(1+.25*math.sin(a*13))
                r=radius2+width*math.cos(b)
                vertices.append((math.cos(a)*r,.036+.007*math.sin(a*9)+width*.65*math.sin(b),math.sin(a)*r*.81))
        faces=[(4*k+j,4*((k+1)%segments)+j,4*((k+1)%segments)+(j+1)%4,4*k+(j+1)%4)
               for k in range(segments) for j in range(4)]
        mesh('scalloped-foam-crest',vertices,faces,'foam',smooth=True)


def signpost():
    post('sign-foot',(-.18,.045,0),.10,.09,'cream',8)
    box('blue-post',(-.18,.38875,0),(.055,.6875,.055),'blue',.014)
    box('sign-face',(0,.55,0),(.47,.20,.05),'cream',.035)
    # Raised blue arrow faces web +Z; no texture or lettering dependency.
    box('arrow-shaft',(0,.55,.03),(.18,.025,.012),'blue',.005)
    vertices=[(.08,.59,.025),(.08,.51,.025),(.14,.55,.025),
              (.08,.59,.045),(.08,.51,.045),(.14,.55,.045)]
    mesh('arrow-tip',vertices,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],'blue',.004)
    post('post-cap',(-.18,.7125,0),.046,.04,'cream',8)


def build_parts(asset_id):
    PARTS.clear()
    if asset_id=='bench': bench()
    elif asset_id=='lamp': lamp()
    elif asset_id.startswith('flowerbed-'): bed(asset_id.endswith('long'))
    elif asset_id=='shrub-cluster': shrub()
    elif asset_id=='tree-round': tree()
    elif asset_id.startswith('path-'): path(asset_id[5:])
    elif asset_id.startswith('rock-shore-'): shore(asset_id.endswith('b'))
    elif asset_id=='foam-ring': foam()
    elif asset_id=='signpost': signpost()
    else: raise ValueError(asset_id)
    return list(PARTS)


def combine(asset_id, parts):
    vertices=[];faces=[];indices=[];smooth=[];materials=[];normals=[]
    for o in parts:
        normals.extend([tuple(n.vector) for n in o.data.corner_normals])
        offset=len(vertices)
        vertices.extend([tuple(o.matrix_world@v.co) for v in o.data.vertices])
        for p in o.data.polygons:
            m=o.data.materials[p.material_index]
            if m not in materials: materials.append(m)
            faces.append(tuple(offset+i for i in p.vertices))
            indices.append(materials.index(m));smooth.append(p.use_smooth)
    data=bpy.data.meshes.new(asset_id)
    data.from_pydata(vertices,[],faces);data.update()
    for m in materials:data.materials.append(m)
    for p,idx,s in zip(data.polygons,indices,smooth):p.material_index=idx;p.use_smooth=s
    data.normals_split_custom_set(normals)
    for o in parts:
        old=o.data;bpy.data.objects.remove(o,do_unlink=True)
        if old.users==0:bpy.data.meshes.remove(old)
    o=bpy.data.objects.new(asset_id,data);bpy.context.scene.collection.objects.link(o)
    # Curved outer corners shrink slightly under bevel: restore the module footprint.
    if asset_id.startswith('path-'):
        extent = 2.4 if asset_id == 'path-curve' else 1.2
        for axis in (0, 1):
            low = min(v.co[axis] for v in data.vertices)
            high = max(v.co[axis] for v in data.vertices)
            for v in data.vertices:
                v.co[axis] = (v.co[axis] - (low + high) / 2) * extent / (high - low)
    # Center actual bounds on X/Z and put minimum Y on ground.
    lo=[min(v.co[i] for v in data.vertices) for i in range(3)]
    hi=[max(v.co[i] for v in data.vertices) for i in range(3)]
    shift=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]))
    if asset_id.startswith('path-'):
        assert abs(shift.x)<1e-5 and abs(shift.y)<1e-5
    for v in data.vertices:v.co-=shift
    data.update()
    return o


def triangle_count(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)


def validate(o, asset_id):
    count=triangle_count(o)
    low,high=BUDGETS[asset_id]
    assert low<=count<=high, f'{asset_id}: {count} triangles, expected {low}..{high}'
    assert not o.modifiers, f'{asset_id}: unbaked modifiers'
    coords=[(v.co.x,v.co.z,-v.co.y) for v in o.data.vertices]
    lo=[min(p[i] for p in coords) for i in range(3)]
    hi=[max(p[i] for p in coords) for i in range(3)]
    assert abs(lo[1])<1e-6
    assert abs(lo[0]+hi[0])<1e-6 and abs(lo[2]+hi[2])<1e-6
    assert all(math.isfinite(v) for p in coords for v in p)
    return count,[round(hi[i]-lo[i],6) for i in range(3)]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=1
    MATS.clear()
    assets=[]
    for asset_id in IDS:
        o=combine(asset_id,build_parts(asset_id))
        triangles,dimensions=validate(o,asset_id)
        for obj in bpy.data.objects:
            if obj and obj.name in bpy.context.view_layer.objects:obj.select_set(False)
        o.select_set(True);bpy.context.view_layer.objects.active=o
        destination=OUT/(asset_id+'.glb')
        result=bpy.ops.export_scene.gltf(filepath=str(destination),export_format='GLB',
            use_selection=True,export_yup=True,export_animations=False,export_cameras=False,
            export_lights=False,export_extras=True)
        assert 'FINISHED' in result and destination.is_file(), f'Export failed: {asset_id}'
        entry={'id':asset_id,'triangles':triangles,'dimensions':dimensions,
               'materials':[m.name for m in o.data.materials], 'file_size_bytes':destination.stat().st_size,
               'file':destination.name,'dimension_sources':SOURCES[asset_id],
               'sha256':hashlib.sha256(destination.read_bytes()).hexdigest()}
        if asset_id in PATH_PORTS:entry['ports']=PATH_PORTS[asset_id]
        assets.append(entry)
        print('PROP_EXPORTED',json.dumps(entry),flush=True)
        old=o.data;bpy.data.objects.remove(o,do_unlink=True);bpy.data.meshes.remove(old)
    (OUT/'palette.json').write_text(json.dumps({'color_space':'sRGB hex; converted to linear BSDF',
        'material_prefix':'hope-prop-','roughness':.72,'metallic':0,'colors':PALETTE},indent=2)+'\n')
    (OUT/'manifest.json').write_text(json.dumps({'version':'v02','blender':bpy.app.version_string,
        'units':'scene units (~meters)','dimension_axes':['X width','Y height','Z depth'],
        'origin':'bottom bounds center','front':'+Z','authoring_to_blender':'(x,y,z) -> (x,-z,y)',
        'blender_to_gltf':'(x,y,z) -> (x,z,-y)','path_module':1.2,'path_top':.06,
        'lamp_emission_material':'hope-prop-lamp-glow','foam_alpha':1.0,'water_alpha':.62,'assets':assets},indent=2)+'\n')
    print('PROP_KIT_COMPLETE',flush=True)


if __name__=='__main__':
    main()
