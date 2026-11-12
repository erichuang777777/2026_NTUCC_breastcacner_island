"""v07 two-role sample, derived from build_refined_cast_v06.py.
Run with Blender --background --python /absolute/path/to/this_script.py.
Geometry uses bmesh/data API; only armature edit mode and glTF export use operators.
Rig rest transforms stay unchanged; idle/walk receive relaxed arm offsets.
Authoring coordinates: (right, up, forward); Blender: (x, -forward, up).
"""
from pathlib import Path
import math
import json
import struct
import hashlib
import bpy
import bmesh
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'art-source/characters/export/v07-sample-r2'
ACTIONS = ['idle', 'walk', 'wave', 'read', 'talk', 'nod', 'stretch', 'wish']
ROLES = [('patient-scarf', '#be8790', '#b6a087', '#594237'),
         ('nurse', '#263e64', '#263e64', '#493329')]
parts = []
category = 'body'


def xyz(p):
    return (p[0], -p[2], p[1])


def linear(v):
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4


def mat(name, color, rough=.8):
    c = tuple(linear(int(color[i:i+2], 16) / 255) for i in (1, 3, 5))
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*c, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*c, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = 0
    return m


def register(o, name, material, bone='head', weights=None):
    o.name = name
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth = True
    for v in o.data.vertices:
        for n, value in (weights(v.co.z) if weights else {bone: 1}).items():
            if value > 0:
                vg = o.vertex_groups.get(n) or o.vertex_groups.new(name=n)
                vg.add([v.index], value, 'REPLACE')
    parts.append((o, category))
    return o


def mesh(name, vertices, faces):
    g = bpy.data.meshes.new(name)
    g.from_pydata(vertices, [], faces)
    g.update()
    # All lofts/caps are closed. Recalculate winding rather than rely on ring order.
    bm = bmesh.new()
    bm.from_mesh(g)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(g)
    bm.free()
    o = bpy.data.objects.new(name, g)
    bpy.context.collection.objects.link(o)
    return o


def bake_modifiers(o):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    old = o.data
    new = bpy.data.meshes.new_from_object(o.evaluated_get(dg), depsgraph=dg)
    o.modifiers.clear()
    o.data = new
    bpy.data.meshes.remove(old)


def ell(name, p, s, m, bone='head', segments=16):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=8, radius=1)
    transform = Matrix.Translation(Vector(xyz(p))) @ Matrix.Diagonal((s[0], s[2], s[1], 1))
    bmesh.ops.transform(bm, matrix=transform, verts=list(bm.verts))
    g = bpy.data.meshes.new(name)
    bm.to_mesh(g)
    bm.free()
    o = bpy.data.objects.new(name, g)
    bpy.context.collection.objects.link(o)
    return register(o, name, m, bone)


def curve(name, pts, r, m, bone='head', weights=None):
    # Catmull-Rom tube with six radial sides, no conversion operator/context.
    points = [Vector(xyz(p)) for p in pts]
    samples = []
    for i in range(len(points) - 1):
        a, b, c, d = points[max(0, i-1)], points[i], points[i+1], points[min(len(points)-1, i+2)]
        for j in range(5):
            t = j / 5
            samples.append(.5 * ((2*b) + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t))
    samples.append(points[-1])
    verts, faces = [], []
    for i, p in enumerate(samples):
        tangent = (samples[min(i+1, len(samples)-1)] - samples[max(i-1, 0)]).normalized()
        normal = tangent.cross(Vector((0, 1, 0)))
        if normal.length < .01:
            normal = tangent.cross(Vector((1, 0, 0)))
        normal.normalize()
        other = tangent.cross(normal).normalized()
        for k in range(6):
            angle = k * math.tau / 6
            verts.append(p + r * (math.cos(angle)*normal + math.sin(angle)*other))
    for i in range(len(samples)-1):
        for k in range(6):
            a, b = i*6+k, i*6+(k+1)%6
            faces.append((a, b, b+6, a+6))
    faces += [tuple(reversed(range(6))), tuple((len(samples)-1)*6+k for k in range(6))]
    return register(mesh(name, verts, faces), name, m, bone, weights)


def loft(name, rings, m, bone='hips', weights=None, sides=20):
    vertices, faces = [], []
    for x, y, z, rx, rz in rings:
        for k in range(sides):
            a = k*math.tau/sides
            vertices.append(xyz((x+math.cos(a)*rx, y, z+math.sin(a)*rz)))
    for j in range(len(rings)-1):
        for k in range(sides):
            a, b = j*sides+k, j*sides+(k+1)%sides
            faces.append((a, b, b+sides, a+sides))
    faces += [tuple(reversed(range(sides))), tuple((len(rings)-1)*sides+k for k in range(sides))]
    o = mesh(name, vertices, faces)
    mod = o.modifiers.new('Rounded silhouette', 'SUBSURF')
    mod.levels = mod.render_levels = 1
    bake_modifiers(o)
    return register(o, name, m, bone, weights)


def rounded(name, p, size, radius, m, bone='spine'):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    transform = Matrix.Translation(Vector(xyz(p))) @ Matrix.Diagonal((size[0], size[2], size[1], 1))
    bmesh.ops.transform(bm, matrix=transform, verts=list(bm.verts))
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=radius, segments=3, affect='EDGES')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    g = bpy.data.meshes.new(name)
    bm.to_mesh(g)
    bm.free()
    o = bpy.data.objects.new(name, g)
    bpy.context.collection.objects.link(o)
    return register(o, name, m, bone)


def joint(upper, lower, y, span=.09):
    def weights(h):
        t = max(0, min(1, (h-y+span/2)/span))
        t = t*t*(3-2*t)
        return {upper: t, lower: 1-t}
    return weights


def merge_parts(rig):
    # Explicit data merge preserves vertex weights and semantic mesh/material names.
    for cat in sorted({c for _, c in parts}):
        objects = [o for o, c in parts if c == cat]
        verts, faces, materials, assignments, weights = [], [], [], [], []
        for o in objects:
            offset = len(verts)
            verts.extend(tuple(v.co) for v in o.data.vertices)
            for v in o.data.vertices:
                weights.append({o.vertex_groups[g.group].name: g.weight for g in v.groups})
            slots = []
            for m in o.data.materials:
                if m not in materials:
                    materials.append(m)
                slots.append(materials.index(m))
            for p in o.data.polygons:
                faces.append(tuple(offset+i for i in p.vertices))
                assignments.append(slots[p.material_index])
        o = mesh('cast_'+cat, verts, faces)
        for m in materials:
            o.data.materials.append(m)
        for p, index in zip(o.data.polygons, assignments):
            p.material_index = index
            p.use_smooth = True
        for i, w in enumerate(weights):
            assert abs(sum(w.values())-1) < 1e-5
            for name, value in w.items():
                assert name in rig.data.bones
                vg = o.vertex_groups.get(name) or o.vertex_groups.new(name=name)
                vg.add([i], value, 'REPLACE')
        o.parent = rig
        mod = o.modifiers.new('Shared smooth skeleton', 'ARMATURE')
        mod.object = rig
        for old in objects:
            data = old.data
            bpy.data.objects.remove(old, do_unlink=True)
            bpy.data.meshes.remove(data)


def glb_info(path):
    b = path.read_bytes()
    assert b[:4] == b'glTF'
    length = struct.unpack_from('<I', b, 12)[0]
    g = json.loads(b[20:20+length])
    triangles = sum(g['accessors'][p['indices']]['count']//3 for m in g['meshes'] for p in m['primitives'])
    return g, triangles


def build_role(role, shirt_hex, pants_hex, hair_hex):
    global parts, category
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for data in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.materials):
        for item in list(data):
            data.remove(item)
    parts, category = [], 'body'
    patient = role == 'patient-scarf'
    skin = mat('skin', '#efbfa0' if patient else '#f2c4a5', .43)
    skin.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value = .15
    blush = mat('blush', '#dda39a', .5)
    outfit, pants, hair = mat('shirt', shirt_hex), mat('pants', pants_hex), mat('hair', hair_hex, .55)
    hair_light = mat('hair-highlight', '#705344', .55)
    cream, white = mat('cream', '#f6eedc'), mat('shoe', '#f8f1e3', .62)
    sole, ink = mat('sole', '#c6b69c', .67), mat('ink', '#382922', .45)
    iris, eye_white = mat('iris', '#704733', .35), mat('eye-white', '#fff9f0', .3)
    rose, metal = mat('ribbon', '#db8d9e'), mat('metal', '#adb7b7', .35)
    scarf = mat('headscarf', '#bc7c87')
    plastic = mat('badge', '#f8f4e9', .35)
    button = mat('button', '#e2c1b3', .35)
    # Face is a shaped jaw/cheek/temple surface, not a shared scaled sphere.
    if patient:
        profile = [(1.048,.055,.068),(1.075,.113,.118),(1.13,.177,.158),
                   (1.20,.218,.189),(1.29,.222,.194),(1.38,.203,.180),
                   (1.46,.146,.135),(1.49,.052,.050)]
    else:
        profile = [(1.072,.045,.060),(1.097,.093,.102),(1.15,.157,.148),
                   (1.22,.194,.179),(1.30,.202,.185),(1.39,.183,.169),
                   (1.46,.128,.122),(1.49,.043,.045)]
    face = loft('sculpted-face', [(0,y,.009,rx,rz) for y,rx,rz in profile], skin, 'head', sides=28)
    # Continuous cheek/forehead volume; eye sockets are recessed in this same mesh.
    for v in face.data.vertices:
        x, z, forward = v.co.x, v.co.z, -v.co.y
        front = max(0, min(1, forward / .12))
        cheek = math.exp(-((abs(x)-.115)/.067)**2-((z-1.205)/.062)**2)
        brow = math.exp(-(x/.16)**2-((z-1.38)/.065)**2)
        socket = math.exp(-((abs(x)-.086)/.040)**2-((z-1.28)/.043)**2)
        v.co.y -= front*(.026*cheek+.016*brow-.009*socket)
        v.co.x *= 1+.045*math.exp(-((z-1.16)/.075)**2)
    loft('visible-neck', [(0,.945,0,.079,.074),(0,.97,0,.080,.075),
                          (0,1.048,0,.077,.072),(0,1.065,0,.086,.078)], skin, 'spine')
    # Lower neckline exposes the neck. Narrow waist, soft hips and sloped shoulders.
    waist = .142 if patient else .126
    shoulder = .176 if patient else .190
    depth = .113 if patient else .102
    torso = [(0,.562,0,.150,depth),(0,.579,0,.178 if patient else .165,depth+.01),
             (0,.64,0,.175 if patient else .16,depth+.005),(0,.75,0,waist,depth-.01),
             (0,.85,0,.160,depth),(0,.92,0,shoulder,depth),
             (0,.950,0,.154 if patient else .172,.096),(0,.981,0,.098,.070),(0,.988,0,.074,.062)]
    loft('tailored-torso', torso, outfit, 'spine')
    ell('hips',(0,.565,0),(.158 if patient else .143,.089,.105),pants,'hips')
    if patient:
        loft('cream-inset',[(0,.586,.105,.063,.014),(0,.61,.117,.069,.017),
              (0,.78,.103,.063,.017),(0,.90,.108,.067,.019),(0,.963,.073,.064,.016)],cream,'spine')
        curve('round-inner-neck',[(-.060,.966,.088),(-.043,.939,.112),(0,.932,.121),(.043,.939,.112),(.060,.966,.088)],.007,cream,'spine')
    for sign, side in [(-1,'L'), (1,'R')]:
        earx = .218 if patient else .198
        ell('ear-'+side,(sign*earx,1.242,.002),(.034,.052,.030),skin)
        ell('ear-inner-'+side,(sign*(earx+.007),1.242,.027),(.015,.028,.007),blush)
        x = sign*.086
        eyey = 1.278 if patient else 1.285
        eyef = .173 if patient else .166
        es = .92 if patient else 1.0
        ell('eye-white-'+side,(x,eyey,eyef),(.046*es,.052*es,.019),eye_white,'eye.'+side,20)
        ell('iris-'+side,(x,eyey,eyef+.017),(.027*es,.035*es,.009),iris,'eye.'+side,20)
        ell('pupil-'+side,(x,eyey,eyef+.024),(.016,.024,.005),ink,'eye.'+side)
        ell('glint-'+side,(x-.009,eyey+.015,eyef+.029),(.008,.010,.003),white,'eye.'+side,12)
        ell('small-glint-'+side,(x+.009,eyey-.015,eyef+.029),(.003,.004,.002),white,'eye.'+side,12)
        curve('upper-eyelid-'+side,[(x-.042*es,eyey+.005,eyef+.012),(x,eyey+.048*es,eyef+.014),(x+.042*es,eyey+.005,eyef+.012)],.005,ink,'eye.'+side)
        curve('lid-fold-'+side,[(x-.043*es,eyey+.019,eyef),(x,eyey+.058*es,eyef-.003),(x+.043*es,eyey+.019,eyef)],.003,skin,'eye.'+side)
        curve('lower-lid-'+side,[(x-.038,eyey-.012,eyef+.008),(x,eyey-.047*es,eyef+.013),(x+.038,eyey-.012,eyef+.008)],.003,skin,'eye.'+side)
        for k in range(2):
            curve('lash-'+side+str(k),[(x+sign*(.032+k*.007),eyey+.025-k*.009,eyef+.015),(x+sign*(.046+k*.006),eyey+.035-k*.010,eyef+.014)],.0028,ink,'eye.'+side)
        curve('brow-'+side,[(x-.032,1.354,.171),(x,1.363,.177),(x+.032,1.352,.171)],.0065 if patient else .0055,hair)
        ell('cheek-'+side,(sign*(.147 if patient else .135),1.212,.155),(.030,.017,.003),blush)
        x = sign*.092
        legw = joint('thigh.'+side,'shin.'+side,.32)
        loft('trousers-'+side,[(x,.108,0,.055,.061),(x,.124,0,.061,.066),
             (x,.25,-.002,.061,.068),(x,.33,-.005,.066,.073),
             (x,.46,0,.074,.085),(x,.58,0,.080,.089)],pants,weights=legw)
        loft('trouser-turnup-'+side,[(x,.11,0,.060,.066),(x,.116,0,.066,.072),
             (x,.148,0,.066,.072),(x,.154,0,.061,.068)],pants,'shin.'+side)
        curve('trouser-seam-'+side,[(x+sign*.060,.16,.012),(x+sign*.063,.31,.012),(x+sign*.074,.51,.012)],.0018,pants,weights=legw)
        # Two separately modelled rounded sole layers, underside exactly at zero.
        for name, rings, material in [
            ('outsole',[(.0,.064,.108),(.004,.075,.120),(.018,.076,.122),(.024,.070,.116)],sole),
            ('midsole',[(.019,.070,.114),(.024,.075,.121),(.039,.074,.120),(.045,.066,.111)],white)]:
            loft(name+'-'+side,[(x,y,.041,rx,rz) for y,rx,rz in rings],material,'foot.'+side,sides=16)
        ell('shoe-upper-'+side,(x,.073,.041),(.073,.049,.119),white,'foot.'+side)
        ell('shoe-tongue-'+side,(x,.106,.012),(.045,.016,.051),cream,'foot.'+side)
        for k in range(3):
            curve('lace-'+side+str(k),[(x-.027,.116-k*.006,.024+k*.020),(x,.120-k*.006,.024+k*.020),(x+.027,.116-k*.006,.024+k*.020)],.0028,cream,'foot.'+side)
        # Preserve rig axes; idle/walk author the relaxed arm rotation.
        # Elbow bend is keyed in idle/walk; mitten depth keeps palms inward.
        def arm_x(y):
            return sign*.213
        def arm_z(y):
            return 0
        armw = joint('upper_arm.'+side,'forearm.'+side,.745,.13)
        if patient:
            heights = [(.555,.042,.047),(.575,.047,.050),(.69,.049,.054),(.75,.052,.057),(.88,.060,.064),(.937,.057,.059),(.969,.031,.035)]
        else:
            heights = [(.805,.055,.058),(.82,.061,.062),(.91,.067,.066),(.95,.065,.063),(.982,.035,.038)]
        loft('sleeve-'+side,[(arm_x(y),y,arm_z(y),rx,rz) for y,rx,rz in heights],outfit,weights=armw)
        cuff_y = .575 if patient else .823
        cuff_r = .050 if patient else .064
        loft('folded-cuff-'+side,[(arm_x(y),y,arm_z(y),r,r*1.06) for y,r in [(cuff_y-.018,cuff_r-.003),(cuff_y-.013,cuff_r+.003),(cuff_y+.018,cuff_r+.003),(cuff_y+.023,cuff_r-.003)]],outfit,'forearm.'+side if patient else 'upper_arm.'+side)
        if not patient:
            loft('bare-arm-'+side,[(arm_x(y),y,arm_z(y),rx,rz) for y,rx,rz in [(.51,.032,.034),(.54,.034,.037),(.65,.041,.042),(.74,.046,.045),(.82,.049,.048),(.85,.048,.048)]],skin,weights=armw)
        else:
            loft('wrist-'+side,[(arm_x(y),y,arm_z(y),.033,.034) for y in [.51,.53,.57]],skin,'hand.'+side)
        hx, hz = arm_x(.50), arm_z(.50)
        loft('mitten-'+side,[(hx,.432,hz+.008,.022,.022),(hx,.445,hz+.009,.037,.027),
             (hx,.485,hz,.040,.029),(hx,.515,hz-.003,.032,.026),(hx,.53,hz-.004,.027,.025)],skin,'hand.'+side,sides=16)
        ell('thumb-base-'+side,(hx-sign*.028,.493,hz+.015),(.023,.029,.023),skin,'hand.'+side)
        ell('thumb-tip-'+side,(hx-sign*.043,.477,hz+.025),(.017,.026,.018),skin,'hand.'+side)
        for k in range(2):
            curve('mitten-crease-'+side+str(k),[(hx-.012+k*.018,.444,hz+.029),(hx-.012+k*.018,.455,hz+.030)],.0012,blush,'hand.'+side)
    ell('nose',(0,1.234,.198 if patient else .190),(.025 if patient else .021,.028,.027),skin)
    curve('smile',[(-.043,1.169,.168),(0,1.156,.179),(.043,1.169,.168)],.0035,mat('lip','#b9766b',.5))
    ell('lower-lip',(0,1.15,.173),(.023,.005,.006),blush)
    if patient:
        for s in [-1,1]:
            curve('cardigan-placket',[(s*.073,.588,.119),(s*.071,.69,.126),(s*.065,.82,.119),(s*.072,.921,.126),(s*.067,.975,.079)],.010,outfit,'spine')
            rounded('patch-pocket',(s*.118,.67,.109),(.079,.089,.022),.010,outfit)
            curve('pocket-welt',[(s*.118-.033,.707,.123),(s*.118,.708,.127),(s*.118+.033,.707,.123)],.0045,outfit,'spine')
        for h in [.615,.69,.765,.84]:
            ell('cardigan-button',(.074,h,.139),(.006,.006,.004),button,'spine',12)
        rounded('backpack',(0,.765,-.166),(.267,.306,.102),.040,cream)
        rounded('backpack-front',(0,.71,-.226),(.207,.132,.037),.017,cream)
        rounded('backpack-flap',(0,.847,-.225),(.253,.122,.035),.018,cream)
        for s in [-1,1]:
            curve('backpack-strap',[(s*.132,.635,-.16),(s*.151,.77,.091),(s*.155,.923,.094),(s*.117,.991,-.012),(s*.114,.895,-.203)],.012,cream,'spine')
            rounded('bag-buckle',(s*.066,.778,-.249),(.025,.036,.010),.004,button)
        curve('bag-handle',[(-.042,.916,-.172),(-.036,.966,-.171),(.036,.966,-.171),(.042,.916,-.172)],.009,cream,'spine')
        curve('hope-ribbon',[(-.119,.864,.132),(-.090,.905,.136),(-.101,.922,.132),(-.115,.904,.135),(-.079,.864,.136)],.0045,rose,'spine')
    else:
        # Inset V and two broad rounded fabric bands read as a collar, not piping.
        loft('v-neck-inset',[(0,.922,.105,.012,.009),(0,.947,.094,.030,.012),(0,.98,.066,.061,.013)],skin,'spine')
        for s in [-1,1]:
            curve('v-neck-band',[(s*.065,.981,.078),(s*.046,.952,.111),(0,.917,.125)],.012,outfit,'spine')
            rounded('uniform-pocket',(s*.103,.658,.101),(.085,.084,.020),.009,outfit)
            curve('pocket-top',[(s*.103-.035,.693,.115),(s*.103,.694,.117),(s*.103+.035,.693,.115)],.0035,outfit,'spine')
        curve('uniform-placket',[(.006,.912,.122),(.006,.862,.119),(.006,.827,.116)],.005,outfit,'spine')
        rounded('id-card',(.099,.842,.126),(.061,.074,.012),.006,plastic)
        rounded('id-clip',(.099,.889,.125),(.017,.025,.011),.003,metal)
        ell('id-portrait',(.084,.850,.135),(.009,.012,.002),skin,'spine',12)
        for h in [.846,.833]:
            curve('id-label',[(.099,h,.134),(.120,h,.134)],.0018,outfit,'spine')
        ell('nurse-watch',(-.10,.87,.12),(.017,.022,.006),metal,'spine')
        ell('watch-face',(-.10,.87,.127),(.013,.017,.003),plastic,'spine')
    category='scarf'
    ell('scarf-back',(0,1.315,-.064),(.233,.237,.177),scarf,segments=24)
    ell('scarf-crown',(0,1.392,-.030),(.235,.178,.191),scarf,segments=24)
    for k in range(3):
        curve('diagonal-wrap', [(-.224,1.26+k*.033,.034),(-.183,1.353+k*.034,.122),(-.075,1.439+k*.025,.164),(.089,1.468+k*.022,.141),(.220,1.357+k*.028,.027)], .008-k*.001, scarf)
    ell('scarf-knot',(-.184,1.192,-.151),(.054,.055,.045),scarf)
    for sign in [-1,1]:
        loft('scarf-tail', [(-.18+sign*.022,.975,-.157,.013,.010),(-.18+sign*.035,1.015,-.151,.031,.015),(-.18+sign*.031,1.12,-.151,.036,.020),(-.18,1.20,-.15,.021,.021)],scarf,'head',sides=16)
    curve('tail-fold',[(-.198,.999,-.132),(-.211,1.087,-.126),(-.19,1.16,-.125)],.003,scarf)
    category='short'
    ell('hair-cap',(0,1.365,-.049),(.236,.199,.175),hair)
    for k in range(10):
        x=-.18+k*.04;ell('swept-lock',(x,1.418+math.sin(k*.7)*.028,.110),(.074,.078,.085),hair)
        curve('hair-ridge',[(x-.03,1.392,.178),(x+.015,1.446,.166),(x+.03,1.478,.121)],.0035,hair)
    for s in [-1,1]:ell('sideburn',(s*.21,1.292,-.005),(.029,.080,.061),hair)
    category='bob'
    ell('bob-cap',(0,1.365,-.048),(.220,.205,.179),hair,segments=24)
    for s in [-1,1]:
        ell('bob-side',(s*.186,1.245,-.060),(.052,.142,.107),hair)
    # Overlapping curved locks break the cap silhouette; ends curl toward the jaw.
    for j in range(3):
        d = j*.028
        curve('parted-fringe-'+str(j),[(.047+d*.4,1.511-d*.25,.065),
              (-.025-d,1.486-d*.35,.133),(-.115-d*.55,1.416-d*.45,.151),
              (-.183-d*.14,1.319-d*.35,.079)],.019-j*.0015,hair if j%2 else hair_light)
    for side in [-1,1]:
        for j in range(2):
            curve('inward-lock',[(side*(.14+j*.019),1.46-j*.014,.035-j*.025),
                  (side*(.209+j*.006),1.32,.021-j*.025),
                  (side*(.211+j*.005),1.18,-.006-j*.025),
                  (side*.173,1.135,-.018-j*.025)],.016,hair if j%2 else hair_light)
    curve('part-line',[(.058,1.522,.049),(.079,1.505,.103),(.125,1.459,.131)],.004,ink)
    category='ponytail'
    ell('tied-hair-cap',(0,1.355,-.056),(.240,.204,.184),hair)
    ell('ponytail',(0,1.14,-.238),(.066,.205,.059),hair)
    ell('hair-tie',(0,1.315,-.227),(.048,.025,.025),ink)
    for sign in [-1,1]:
        curve('side-fringe',[(sign*.05,1.49,.07),(sign*.18,1.39,.15),(sign*.222,1.21,.04)],.019,hair)
        curve('loose-side-lock',[(sign*.21,1.33,.055),(sign*.235,1.19,.025),(sign*.214,1.09,.015)],.006,hair)
    category='cap'
    ell('surgical-cap',(0,1.397,-.033),(.241,.170,.205),outfit)
    curve('cap-edge',[(-.232,1.33,.02),(-.15,1.35,.160),(0,1.36,.184),(.15,1.35,.160),(.232,1.33,.02)],.009,cream)
    ell('cap-knot',(0,1.272,-.230),(.047,.03,.025),outfit)
    category='mask'
    ell('mask',(0,1.170,.188),(.125,.068,.031),mat('mask','#b5d6cc'))
    for h in [1.148,1.169,1.190]:curve('mask-pleat',[(-.093,h,.210),(0,h-.004,.222),(.093,h,.210)],.0025,cream)
    for s in [-1,1]:curve('mask-loop',[(s*.113,1.20,.203),(s*.239,1.245,.025),(s*.115,1.135,.194)],.003,cream)
    # Enlarge head geometry around the fixed crown: top 1.57, jaw lower,
    # shorter exposed neck. Rest bones and eye bones remain byte-for-byte positioned.
    for obj, cat in parts:
        if cat != 'body' or all(g.name == 'head' or g.name.startswith('eye.') for g in obj.vertex_groups):
            for v in obj.data.vertices:
                v.co.x *= 1.09
                v.co.y *= 1.09
                v.co.z = 1.57 + (v.co.z-1.57)*1.09
    # Subdivision rounds the sole upward; retain exact ground contact globally.
    lowest = min(v.co.z for obj, _ in parts for v in obj.data.vertices)
    for obj, _ in parts:
        if obj.name.startswith('outsole-'):
            for v in obj.data.vertices:
                v.co.z -= lowest
    # Shared 18-bone armature. Join by semantic part to share materials and keep headwear editable.
    bpy.ops.object.select_all(action='DESELECT');bpy.ops.object.armature_add(enter_editmode=True)
    rig=bpy.context.object;rig.name='HopeCastRig';eb=rig.data.edit_bones;eb.remove(eb[0])
    def bone(name,h,t,parent=None):
        b=eb.new(name);b.head=xyz(h);b.tail=xyz(t)
        if parent:b.parent=eb[parent]
    bone('root',(0,0,0),(0,.12,0));bone('hips',(0,.55,0),(0,.70,0),'root');bone('spine',(0,.70,0),(0,1.0,0),'hips');bone('head',(0,1.0,0),(0,1.47,0),'spine')
    for s,side in [(-1,'L'),(1,'R')]:
        bone('thigh.'+side,(s*.092,.55,0),(s*.092,.32,0),'hips');bone('shin.'+side,(s*.092,.32,0),(s*.092,.09,0),'thigh.'+side);bone('foot.'+side,(s*.092,.09,0),(s*.092,.09,.12),'shin.'+side)
        bone('upper_arm.'+side,(s*.213,.96,0),(s*.213,.745,0),'spine');bone('forearm.'+side,(s*.213,.745,0),(s*.213,.53,0),'upper_arm.'+side);bone('hand.'+side,(s*.213,.53,0),(s*.213,.45,0),'forearm.'+side)
        bone('eye.'+side,(s*.086,1.267,.184),(s*.086,1.32,.184),'head')
    bpy.ops.object.mode_set(mode='OBJECT')
    merge_parts(rig)
    # Eight compatible actions, authored at 24 fps; idle/walk use relaxed arms.
    bpy.context.scene.render.fps=24;rig.animation_data_create()
    animated=['hips','spine','head']+[n+'.'+s for s in ['L','R'] for n in ['thigh','shin','foot','upper_arm','forearm']]
    for action_name,length in [('idle',72),('walk',24),('wave',60),('read',72),('talk',96),('nod',48),('stretch',96),('wish',96)]:
        a=bpy.data.actions.new(action_name);a.use_frame_range=True;a.frame_start=1;a.frame_end=length+1;rig.animation_data.action=a
        for f in range(1,length+2,3):
            t=(f-1)/length*math.tau
            for n in animated:
                b=rig.pose.bones[n];b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
            if action_name=='walk':
                rig.pose.bones['hips'].location.y=.008*(1-math.cos(t*2));rig.pose.bones['spine'].rotation_euler.y=.025*math.sin(t)
                for s,phase in [('L',0),('R',math.pi)]:
                    stride=math.sin(t+phase)
                    rig.pose.bones['thigh.'+s].rotation_euler.x=-.34*stride
                    rig.pose.bones['shin.'+s].rotation_euler.x=.53*max(0,-stride)
                    rig.pose.bones['foot.'+s].rotation_euler.x=-.14*max(0,stride)
                    rig.pose.bones['upper_arm.'+s].rotation_euler.x=.25*stride
                    rig.pose.bones['forearm.'+s].rotation_euler.x=-.10-.06*max(0,stride)
            else:
                rig.pose.bones['spine'].rotation_euler.x=.012*math.sin(t)
                rig.pose.bones['head'].rotation_euler.z=.018*math.sin(t)
                for s in ['L','R']:rig.pose.bones['forearm.'+s].rotation_euler.x=-.08
                if action_name=='wave':
                    ease=math.sin(math.pi*(f-1)/length)**.5
                    rig.pose.bones['upper_arm.R'].rotation_euler.z=-1.6*ease
                    rig.pose.bones['forearm.R'].rotation_euler.z=(-.4+.22*math.sin(t*3))*ease
                if action_name=='read':
                    rig.pose.bones['head'].rotation_euler.x=.15
                    for s in ['L','R']:rig.pose.bones['forearm.'+s].rotation_euler.x=-.72
                if action_name=='talk':
                    rig.pose.bones['head'].rotation_euler.x=.04*math.sin(t*2)
                    rig.pose.bones['upper_arm.R'].rotation_euler.x=-.22-.10*math.sin(t)
                    rig.pose.bones['forearm.R'].rotation_euler.x=-.7-.16*math.sin(t*2)
                if action_name=='nod':
                    rig.pose.bones['head'].rotation_euler.x=.12+.10*math.sin(t*2)
                if action_name=='stretch':
                    rig.pose.bones['head'].rotation_euler.z=.08*math.sin(t)
                    for side,sign in [('L',1),('R',-1)]:
                        rig.pose.bones['upper_arm.'+side].rotation_euler.z=sign*(.3+.2*math.sin(t))
                        rig.pose.bones['forearm.'+side].rotation_euler.x=-.25
                if action_name=='wish':
                    rig.pose.bones['head'].rotation_euler.x=-.18
                    for side in ['L','R']:rig.pose.bones['forearm.'+side].rotation_euler.x=-1.15
            if action_name in {'idle','walk'}:
                for side, sign in [('L',1),('R',-1)]:
                    rig.pose.bones['upper_arm.'+side].rotation_euler.z = sign*math.radians(10)
                    rig.pose.bones['forearm.'+side].rotation_euler.x = -math.radians(15)
            for n in animated:
                b=rig.pose.bones[n];b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('location',frame=f)
        a.use_fake_user=True
    walk_clearance = []
    rig.animation_data.action = bpy.data.actions['walk']
    body = bpy.data.objects['cast_body']
    hand_groups = {g.index for g in body.vertex_groups if g.name.startswith('hand.')}
    hand_indices = [v.index for v in body.data.vertices if any(g.group in hand_groups and g.weight > .5 for g in v.groups)]
    for frame in range(1,26):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
        clearance = min(abs(evaluated.data.vertices[i].co.x)-.185 for i in hand_indices)
        assert clearance > .008, f'Walk hand enters torso lateral envelope at frame {frame}: {clearance}'
        walk_clearance.append(clearance)
    rig.animation_data.action=None
    for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    triangles = 0
    by_part = {}
    for o in meshes:
        o.data.calc_loop_triangles()
        by_part[o.name] = len(o.data.loop_triangles)
        triangles += by_part[o.name]
    first_round = json.loads((ROOT/'art-source/characters/export/v07-sample/manifest.json').read_text())
    prior = next(r for r in first_round['roles'] if r['role'] == role)
    for old in prior['bones']:
        current = rig.data.bones[old['name']]
        assert (current.head_local-Vector(old['head_blender'])).length < 1e-6
        assert (current.tail_local-Vector(old['tail_blender'])).length < 1e-6
        assert (current.parent.name if current.parent else None) == old['parent']
    assert len(rig.data.bones) == 18
    assert sorted(a.name for a in bpy.data.actions) == sorted(ACTIONS)
    assert triangles <= 38000, f'{role}: {triangles} exceeds 38,000 triangles'
    coords = [v.co for o in meshes for v in o.data.vertices]
    assert abs(min(v.z for v in coords)) < .002, 'Soles must sit at the origin'
    assert abs(max(v.z for v in coords)-1.57) < .002, 'Total rest height must remain 1.57'
    baseline = ROOT / 'webgl-prototype/assets/characters/v05' / ('visitor.glb' if patient else 'nurse.glb')
    _, old_triangles = glb_info(baseline)
    assert triangles <= old_triangles*1.3
    for o in bpy.context.scene.objects:
        o.select_set(o.type in {'MESH','ARMATURE'})
    bpy.context.view_layer.objects.active = rig
    target = OUT / (role+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB', use_selection=True,
        export_animations=True, export_animation_mode='ACTIONS', export_skins=True,
        export_def_bones=False, export_leaf_bone=False)
    gltf, exported_triangles = glb_info(target)
    assert exported_triangles == triangles
    assert {a['name'].lower().split('|')[-1] for a in gltf.get('animations', [])} == set(ACTIONS)
    assert len(gltf['skins']) >= 1 and all(len(s['joints']) == 18 for s in gltf['skins'])
    return {'role':role, 'runtime_replacement':'visitor.glb' if patient else 'nurse.glb',
        'default_part':'scarf' if patient else 'bob', 'triangles':triangles,
        'triangles_by_part':by_part, 'visible_triangles':by_part['cast_body']+by_part['cast_scarf' if patient else 'cast_bob'],
        'baseline_total_triangles':old_triangles, 'baseline_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),
        'bytes':target.stat().st_size, 'actions':ACTIONS,
        'walk_min_hand_clearance':min(walk_clearance),
        'rest_bounds_y':[min(v.z for v in coords),max(v.z for v in coords)],
        'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,
                  'head_blender':list(b.head_local),'tail_blender':list(b.tail_local)} for b in rig.data.bones]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    metrics = [build_role(*role) for role in ROLES]
    (OUT/'manifest.json').write_text(json.dumps({'version':'v07-sample-r2',
        'authoring':'v06-derived data API geometry; unchanged v05/v06 rest rig; relaxed idle/walk arms',
        'bone_position_changes':[], 'arm_geometry':'idle/walk: upper arm abduction 10 degrees, elbow flexion 15 degrees',
        'triangle_limit':38000, 'roles':metrics,
        'runtime_notes':['patient-scarf.glb replaces visitor.glb; nurse.glb replaces nurse.glb',
            'cast_body/scarf/short/bob/ponytail/cap/mask retained; default active headwear is selected by the web app',
            'Existing appearance overrides still recolor shirt/pants/hair/headscarf; current visitor pants override is blue',
            'Skin: warm base color, roughness 0.43; Blender SSS 0.15, glTF uses base-color/roughness fallback'],
        'pending_validation':['Warm studio front and three-quarter review','Visual review of all eight animations; walk hand lateral clearance asserted at every frame','WebGL swap, blink and recolor checks']},ensure_ascii=False,indent=2),encoding='utf-8')
    print('CAST_COMPLETE', json.dumps(metrics))


if __name__ == '__main__':
    main()
