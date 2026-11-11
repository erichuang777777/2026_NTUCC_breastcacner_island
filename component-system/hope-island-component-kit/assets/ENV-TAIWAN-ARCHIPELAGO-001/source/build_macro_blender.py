from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
BLEND = ROOT / "source" / "model-macro.blend"
GLB = ROOT / "export" / "env-taiwan-archipelago-001-macro.glb"
PREVIEW = ROOT / "export" / "macro-preview-v13-spacious.png"
LIGHTHOUSE_MODEL = ROOT.parent / "BLD-HOPE-LIGHTHOUSE-001" / "export" / "lighthouse-hunyuan-textured-lod0-v02.glb"
NTUCC_MODEL = ROOT.parent / "BLD-NTUCC-001" / "export" / "ntucc-hunyuan-textured-lod0-v02.glb"
PATHOLOGY_MODEL = ROOT.parent / "ENV-PATHOLOGY-ISLAND-001" / "export" / "pathology-island-hunyuan-textured-lod0-v01.glb"
IMAGING_PAVILION_MODEL = ROOT.parent / "ENV-IMAGING-ISLAND-001" / "export" / "imaging-pavilion-hunyuan-textured-lod0-v01.glb"
IMAGING_TERRAIN_MODEL = ROOT.parent / "ENV-IMAGING-ISLAND-001" / "export" / "imaging-island-terrain-hunyuan-textured-lod0-v01.glb"
MEDICAL_ONCOLOGY_CLINIC_MODEL = ROOT.parent / "ENV-MEDICAL-ONCOLOGY-ISLAND-001" / "export" / "medical-oncology-clinic-hunyuan-textured-lod0-v01.glb"
MEDICAL_ONCOLOGY_TERRAIN_MODEL = ROOT.parent / "ENV-MEDICAL-ONCOLOGY-ISLAND-001" / "export" / "medical-oncology-terrain-hunyuan-textured-lod0-v01.glb"
SURGICAL_ONCOLOGY_CENTER_MODEL = ROOT.parent / "ENV-SURGICAL-ONCOLOGY-ISLAND-001" / "export" / "surgical-oncology-center-hunyuan-textured-lod0-v01.glb"
SURGICAL_ONCOLOGY_TERRAIN_MODEL = ROOT.parent / "ENV-SURGICAL-ONCOLOGY-ISLAND-001" / "export" / "surgical-oncology-terrain-hunyuan-textured-lod0-v01.glb"
RECONSTRUCTION_CENTER_MODEL = ROOT.parent / "ENV-RECONSTRUCTION-ISLAND-001" / "export" / "reconstruction-center-hunyuan-textured-lod0-v01.glb"
RECONSTRUCTION_TERRAIN_MODEL = ROOT.parent / "ENV-RECONSTRUCTION-ISLAND-001" / "export" / "reconstruction-terrain-hunyuan-textured-lod0-v02.glb"
RADIATION_ONCOLOGY_CENTER_MODEL = ROOT.parent / "ENV-RADIATION-ONCOLOGY-ISLAND-001" / "export" / "radiation-oncology-center-hunyuan-textured-lod0-v01.glb"
RADIATION_ONCOLOGY_TERRAIN_MODEL = ROOT.parent / "ENV-RADIATION-ONCOLOGY-ISLAND-001" / "export" / "radiation-oncology-terrain-hunyuan-textured-lod0-v01.glb"
CARDIOLOGY_CENTER_MODEL = ROOT.parent / "ENV-CARDIOLOGY-ISLAND-001" / "export" / "cardiology-center-hunyuan-textured-lod0-v01.glb"
CARDIOLOGY_TERRAIN_MODEL = ROOT.parent / "ENV-CARDIOLOGY-ISLAND-001" / "export" / "cardiology-terrain-hunyuan-textured-lod0-v01.glb"
FAMILY_MEDICINE_CENTER_MODEL = ROOT.parent / "ENV-FAMILY-MEDICINE-ISLAND-001" / "export" / "family-medicine-center-web-lod-v01.glb"
FAMILY_MEDICINE_TERRAIN_MODEL = ROOT.parent / "ENV-FAMILY-MEDICINE-ISLAND-001" / "export" / "family-medicine-terrain-web-lod-v01.glb"
REHABILITATION_CENTER_MODEL = ROOT.parent / "ENV-REHABILITATION-ISLAND-001" / "export" / "rehabilitation-center-web-lod-v01.glb"
REHABILITATION_TERRAIN_MODEL = ROOT.parent / "ENV-REHABILITATION-ISLAND-001" / "export" / "rehabilitation-terrain-web-lod-v01.glb"
FERTILITY_CENTER_MODEL = ROOT.parent / "ENV-FERTILITY-PRESERVATION-ISLAND-001" / "export" / "fertility-center-web-lod-v01.glb"
FERTILITY_TERRAIN_MODEL = ROOT.parent / "ENV-FERTILITY-PRESERVATION-ISLAND-001" / "export" / "fertility-terrain-web-lod-v01.glb"

ISLANDS = [
    ("pathology", -5.0, 9.0, (0.55, 0.62, 0.50)),
    ("imaging", 5.0, 9.0, (0.45, 0.58, 0.66)),
    ("medical-oncology", -11.0, 1.0, (0.68, 0.50, 0.51)),
    ("surgical-oncology", 0.0, 1.0, (0.63, 0.55, 0.47)),
    ("reconstruction", 11.0, 1.0, (0.72, 0.48, 0.53)),
    ("radiation-oncology", -11.0, -8.0, (0.43, 0.55, 0.67)),
    ("cardiology", 0.0, -8.0, (0.66, 0.43, 0.44)),
    ("family-medicine", 11.0, -8.0, (0.58, 0.61, 0.49)),
    ("rehabilitation", -5.0, -17.0, (0.43, 0.58, 0.57)),
    ("fertility", 5.0, -17.0, (0.62, 0.54, 0.65)),
]

LINKS = [(0,1),(0,2),(0,3),(1,4),(2,3),(2,5),(3,4),(3,6),(4,7),(5,6),(5,8),(6,7),(6,8),(6,9),(7,9),(8,9)]


def material(name, color, roughness=0.78, emission=None):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        shader.inputs["Emission Color"].default_value = (*emission, 1)
        shader.inputs["Emission Strength"].default_value = 2.5
    return value


def cube(name, size, location, mat, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = tuple(v / 2 for v in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("soft-edges", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def cone(name, radius1, radius2, depth, location, mat, vertices=12):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def sphere(name, radius, location, mat, scale=(1,1,1), subdivisions=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    return obj


def irregular_layer(name, x, y, radius_bottom, radius_top, depth, z, mat, phase=0.0, vertices=24):
    coords = []
    for level, radius in ((-depth / 2, radius_bottom), (depth / 2, radius_top)):
        for index in range(vertices):
            angle = index / vertices * math.tau
            wobble = 1 + .07 * math.sin(angle * 3 + phase) + .035 * math.sin(angle * 7 + phase * 1.7)
            coords.append((x + math.cos(angle) * radius * wobble, y + math.sin(angle) * radius * wobble, z + level))
    faces = [tuple(range(vertices - 1, -1, -1)), tuple(range(vertices, vertices * 2))]
    for index in range(vertices):
        next_index = (index + 1) % vertices
        faces.append((index, next_index, vertices + next_index, vertices + index))
    mesh = bpy.data.meshes.new(name + "-mesh")
    mesh.from_pydata(coords, [], faces);mesh.update()
    obj = bpy.data.objects.new(name, mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(mat)
    bevel = obj.modifiers.new("weathered-edges", "BEVEL");bevel.width = min(depth * .12, .16);bevel.segments = 2
    return obj


def tree(prefix, x, y, z, blossom=False, scale=1.0):
    trunk = material("trunk", (0.34,0.22,0.14))
    leaf = material("blossom" if blossom else "leaf", (0.83,0.48,0.55) if blossom else (0.34,0.48,0.29))
    cone(prefix+"-trunk", .12*scale, .16*scale, 1.0*scale, (x,y,z+.5*scale), trunk, 8)
    for i,(dx,dy,dz) in enumerate(((0,0,1.2),(.32,0,1.15),(-.28,.08,1.1))):
        sphere(f"{prefix}-crown-{i}", .52*scale, (x+dx*scale,y+dy*scale,z+dz*scale), leaf, (1,1,.85))


def island_base(prefix, x, y, scale=1.0):
    rock = material("layered-rock", (0.37,0.33,0.31))
    rock2 = material("warm-rock", (0.48,0.41,0.36))
    grass = material("sage-grass", (0.43,0.53,0.36))
    sand = material("shore", (0.66,0.58,0.47))
    phase = (sum(ord(char) for char in prefix) % 31) / 31 * math.tau
    irregular_layer(prefix+"-cliff", x, y, 3.25*scale, 2.82*scale, 1.55*scale, -.5*scale, rock, phase)
    irregular_layer(prefix+"-rock-layer", x, y, 2.98*scale, 2.82*scale, .35*scale, .34*scale, rock2, phase+.2)
    irregular_layer(prefix+"-shore", x, y, 2.88*scale, 2.75*scale, .22*scale, .62*scale, sand, phase+.3)
    irregular_layer(prefix+"-grass", x, y, 2.75*scale, 2.62*scale, .24*scale, .84*scale, grass, phase+.45)
    for i in range(9):
        angle = i/9*math.tau + phase
        radius = (3.02 + .13*math.sin(i*2.3))*scale
        sphere(f"{prefix}-coast-rock-{i}", (.28+(i%3)*.07)*scale, (x+math.cos(angle)*radius,y+math.sin(angle)*radius,-.45*scale), rock2, (1,.72,.65), 1)
    rail=material("island-rail",(.34,.30,.26))
    bpy.ops.mesh.primitive_torus_add(major_radius=2.43*scale,minor_radius=.035*scale,major_segments=48,minor_segments=6,location=(x,y,1.25*scale))
    railing=bpy.context.object;railing.name=prefix+"-perimeter-rail";railing.data.materials.append(rail)
    for index in range(16):
        angle=index/16*math.tau+phase
        cone(f"{prefix}-rail-post-{index}",.025*scale,.035*scale,.48*scale,(x+math.cos(angle)*2.43*scale,y+math.sin(angle)*2.43*scale,1.13*scale),rail,6)


def pavilion(prefix, x, y, accent, scale=1.0):
    ivory = material("warm-ivory", (0.84,0.78,0.68))
    glass = material("mist-glass", (0.22,0.38,0.42), .18, (1.0,.46,.16))
    accent_mat = material(prefix+"-accent", accent)
    body = cone(prefix+"-building", 1.5*scale, 1.5*scale, 1.25*scale, (x,y,1.55*scale), ivory, 32)
    body.scale[1] = .68
    for side in (-1,1):
        wing = cone(f"{prefix}-wing-{side}", .78*scale, .78*scale, 1.02*scale, (x+side*1.25*scale,y+.08*scale,1.45*scale), ivory, 24)
        wing.scale[1] = .72
        wing_window = cube(f"{prefix}-wing-window-{side}", (.82*scale,.06*scale,.55*scale), (x+side*1.25*scale,y-.51*scale,1.48*scale), glass, .05)
        wing_window.rotation_euler[2] = side*.08
    window = cube(prefix+"-window", (2.15*scale,.06*scale,.72*scale), (x,y-.72*scale,1.55*scale), glass, .08)
    door = cube(prefix+"-door", (.58*scale,.1*scale,.88*scale), (x,y-.79*scale,1.37*scale), accent_mat, .08)
    canopy = cube(prefix+"-canopy", (1.25*scale,.75*scale,.15*scale), (x,y-1.05*scale,2.02*scale), ivory, .12)
    roof = sphere(prefix+"-roof", 1.0*scale, (x,y,2.15*scale), accent_mat, (1.62,.82,.28), 2)
    for side in (-1,1):
        sphere(f"{prefix}-wing-roof-{side}", .68*scale, (x+side*1.25*scale,y+.08*scale,1.98*scale), accent_mat, (1.15,.82,.25), 2)
    cone(prefix+"-emblem", .43*scale, .43*scale, .12*scale, (x,y-.82*scale,2.45*scale), accent_mat, 32).rotation_euler[0] = math.pi/2
    path = material("stone-path", (0.70,0.63,0.54))
    cube(prefix+"-entry-path", (1.05*scale,2.15*scale,.12*scale), (x,y-1.73*scale,.98*scale), path, .12)
    plaza = cone(prefix+"-entry-plaza", 1.35*scale,1.35*scale,.1*scale,(x,y-2.05*scale,.99*scale),path,32)
    tree(prefix+"-tree-a",x-2.0*scale,y+.72*scale,.92*scale,False,.7*scale)
    tree(prefix+"-tree-b",x+1.95*scale,y+.62*scale,.92*scale,True,.67*scale)
    for tree_index,(tx,ty,blossom) in enumerate(((-1.65,1.65,True),(1.55,1.72,False),(-2.05,-.15,False),(2.05,-.08,True))):
        tree(f"{prefix}-grove-{tree_index}",x+tx*scale,y+ty*scale,.92*scale,blossom,.42*scale)
    flower = material("garden-rose", (.78,.35,.45))
    for flower_index in range(8):
        angle=flower_index/8*math.tau
        sphere(f"{prefix}-garden-{flower_index}",.11*scale,(x+math.cos(angle)*1.65*scale,y-1.95*scale+math.sin(angle)*.52*scale,1.13*scale),flower,(1,.8,.65),1)
    lamp_glow = material("path-lamp-glow", (.95,.68,.32), .25, (1.0,.42,.12))
    dark = material("path-lamp-post", (.22,.25,.24))
    for lamp_index, lamp_x in enumerate((-1.25,1.25)):
        cone(f"{prefix}-lamp-post-{lamp_index}", .035*scale, .045*scale, .72*scale, (x+lamp_x*scale,y-1.45*scale,1.35*scale), dark, 8)
        sphere(f"{prefix}-lamp-{lamp_index}", .11*scale, (x+lamp_x*scale,y-1.45*scale,1.76*scale), lamp_glow, subdivisions=2)
    unit_landmark(prefix,x,y,accent_mat,scale)


def unit_landmark(prefix,x,y,accent_mat,scale):
    dark=material("unit-symbol-dark",(.20,.28,.29));white=material("unit-symbol-ivory",(.9,.84,.73))
    z=2.48*scale;front_y=y-.86*scale
    def torus(name,major=.28,minor=.065):
        bpy.ops.mesh.primitive_torus_add(major_radius=major*scale,minor_radius=minor*scale,major_segments=24,minor_segments=8,location=(x,front_y-.03,z))
        obj=bpy.context.object;obj.name=name;obj.rotation_euler[0]=math.pi/2;obj.data.materials.append(dark);return obj
    if prefix=="pathology":
        cube(prefix+"-microscope-base",(.55*scale,.08*scale,.1*scale), (x,front_y-.03,z-.22*scale),dark,.04)
        arm=cone(prefix+"-microscope-arm",.06*scale,.08*scale,.48*scale,(x-.08*scale,front_y-.05,z),dark,12);arm.rotation_euler[1]=-.42
        lens=cone(prefix+"-microscope-lens",.07*scale,.09*scale,.28*scale,(x+.09*scale,front_y-.06,z+.1*scale),accent_mat,12);lens.rotation_euler[1]=-.55
    elif prefix=="imaging":
        torus(prefix+"-mri-ring",.3,.085);cube(prefix+"-mri-bed",(.62*scale,.1*scale,.08*scale),(x,front_y-.04,z-.31*scale),white,.03)
    elif prefix=="medical-oncology":
        capsule=cube(prefix+"-capsule",(.62*scale,.1*scale,.2*scale),(x,front_y-.04,z),accent_mat,.1);capsule.rotation_euler[1]=-.45
    elif prefix=="surgical-oncology":
        cube(prefix+"-cross-v",(.16*scale,.09*scale,.65*scale),(x,front_y-.04,z),accent_mat,.04);cube(prefix+"-cross-h",(.58*scale,.09*scale,.16*scale),(x,front_y-.05,z),accent_mat,.04)
    elif prefix=="reconstruction":
        ribbon=torus(prefix+"-ribbon",.25,.055);ribbon.scale[0]=.72;ribbon.rotation_euler[2]=-.35
        cube(prefix+"-ribbon-tail",(.1*scale,.08*scale,.42*scale),(x+.12*scale,front_y-.04,z-.27*scale),accent_mat,.03).rotation_euler[1]=-.35
    elif prefix=="radiation-oncology":
        torus(prefix+"-target-outer",.31,.045);torus(prefix+"-target-inner",.16,.04);sphere(prefix+"-target-core",.07*scale,(x,front_y-.08,z),accent_mat,subdivisions=2)
    elif prefix=="cardiology":
        sphere(prefix+"-heart-left",.2*scale,(x-.13*scale,front_y-.05,z+.08*scale),accent_mat,(1,.55,1),2);sphere(prefix+"-heart-right",.2*scale,(x+.13*scale,front_y-.05,z+.08*scale),accent_mat,(1,.55,1),2)
        tip=cone(prefix+"-heart-tip",.3*scale,.03*scale,.42*scale,(x,front_y-.05,z-.12*scale),accent_mat,16);tip.rotation_euler[0]=math.pi
    elif prefix=="family-medicine":
        cube(prefix+"-family-house",(.58*scale,.08*scale,.42*scale),(x,front_y-.04,z-.05*scale),white,.05);roof=cube(prefix+"-family-roof",(.5*scale,.09*scale,.12*scale),(x,front_y-.04,z+.25*scale),accent_mat,.03);roof.rotation_euler[1]=math.radians(45)
    elif prefix=="rehabilitation":
        sphere(prefix+"-rehab-head",.1*scale,(x,front_y-.05,z+.27*scale),accent_mat,subdivisions=2);body=cube(prefix+"-rehab-body",(.09*scale,.08*scale,.35*scale),(x,front_y-.05,z+.02*scale),dark,.03);body.rotation_euler[1]=-.35
        for side in (-1,1):cube(f"{prefix}-rehab-limb-{side}",(.34*scale,.07*scale,.08*scale),(x+side*.12*scale,front_y-.05,z-.18*scale),accent_mat,.03).rotation_euler[1]=side*.55
    elif prefix=="fertility":
        sphere(prefix+"-ovum",.25*scale,(x,front_y-.05,z),accent_mat,subdivisions=2)
        for index in range(5):
            angle=index/5*math.tau;sphere(f"{prefix}-cell-{index}",.055*scale,(x+math.cos(angle)*.38*scale,front_y-.05,z+math.sin(angle)*.38*scale),white,subdivisions=1)


def bridge(prefix, a, b):
    ax,ay=a; bx,by=b; dx=bx-ax;dy=by-ay; length=math.hypot(dx,dy); angle=math.atan2(dy,dx)
    wood = material("bridge-stone", (0.58,0.47,0.38))
    clear_length=max(.6,length-4.7)
    rail=material("bridge-rail",(.28,.25,.22))
    for segment in range(5):
        t=(segment+.5)/5
        height=.98+math.sin(t*math.pi)*.24
        deck=cube(f"{prefix}-deck-{segment}",(clear_length/5+.06,.82,.16),(ax+dx*(.5+(t-.5)*clear_length/length),ay+dy*(.5+(t-.5)*clear_length/length),height),wood,.08)
        deck.rotation_euler[2]=angle
        center_x=ax+dx*(.5+(t-.5)*clear_length/length);center_y=ay+dy*(.5+(t-.5)*clear_length/length)
        side_x=math.sin(angle)*.46;side_y=-math.cos(angle)*.46
        for side in (-1,1):
            post=cone(f"{prefix}-post-{segment}-{side}",.025,.035,.5,(center_x+side*side_x,center_y+side*side_y,height+.23),rail,6)
            rail_piece=cube(f"{prefix}-rail-{segment}-{side}",(clear_length/5+.04,.045,.07),(center_x+side*side_x,center_y+side*side_y,height+.45),rail,.02);rail_piece.rotation_euler[2]=angle


def hospital(x,y):
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(NTUCC_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=7.4/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-NTUCC-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.92-mins.z*scale)
    for obj in imported:
        obj.name="ntucc-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def hospital_landscape(x,y):
    """臺大癌醫獨立院區景觀層：入口廣場、接送環道、療癒花園、候車亭與步道照明。"""
    before=set(bpy.context.scene.objects)
    ivory=material("ntucc-campus-ivory",(.82,.75,.66),.72)
    stone=material("ntucc-campus-stone",(.62,.58,.53),.82)
    paving=material("ntucc-campus-paving",(.76,.68,.60),.72)
    road=material("ntucc-campus-road",(.22,.25,.26),.66)
    wood=material("ntucc-campus-wood",(.35,.23,.16),.58)
    metal=material("ntucc-campus-metal",(.18,.23,.24),.38)
    glass=material("ntucc-campus-glass",(.32,.55,.62),.16)
    sage=material("ntucc-campus-sage",(.38,.50,.31),.78)
    rose=material("ntucc-campus-rose",(.79,.40,.49),.66)
    white=material("ntucc-campus-white",(.94,.88,.78),.72)
    glow=material("ntucc-campus-glow",(1.0,.72,.36),.20,(1.0,.42,.12))

    # 建築前方大尺度橢圓廣場與車道；保持和建築本體分離。
    campus_pad=cone("ntucc-campus-terrace",4.05,4.05,.16,(x,y-.18,.94),stone,48);campus_pad.scale.y=.76
    entry_plaza=cone("ntucc-entry-plaza",2.25,2.25,.10,(x,y-2.18,1.05),paving,48);entry_plaza.scale.y=.68
    roundabout=cone("ntucc-dropoff-road",1.78,1.78,.055,(x,y-2.68,1.115),road,48);roundabout.scale.y=.60
    garden=cone("ntucc-healing-garden",.98,.98,.075,(x,y-2.68,1.155),sage,40);garden.scale.y=.62
    fountain=cone("ntucc-garden-fountain",.36,.42,.20,(x,y-2.68,1.27),ivory,32)
    sphere("ntucc-garden-water",.28,(x,y-2.68,1.39),glass,(1,1,.18),2)

    # 入口兩側候車亭與玻璃資訊牆。
    for side in (-1,1):
        sx=x+side*2.30;sy=y-1.92
        cube(f"ntucc-transit-platform-{side}",(1.55,.88,.11),(sx,sy,1.04),paving,.05)
        for ox in (-.58,.58):
            cube(f"ntucc-transit-post-{side}-{ox}",(.08,.08,1.04),(sx+ox,sy,1.57),metal,.02)
        roof=cube(f"ntucc-transit-roof-{side}",(1.72,1.02,.13),(sx,sy,2.10),glass,.08);roof.rotation_euler[1]=side*.06
        cube(f"ntucc-info-wall-{side}",(1.10,.06,.58),(sx,sy+.30,1.50),glass,.035)

    # 花園長椅、燈具與抽象院區導引碑。
    for bench_index,(bx,by,rotation) in enumerate(((-1.36,-3.18,-.12),(1.36,-3.18,.12),(-2.82,-.76,-.05),(2.82,-.76,.05))):
        parts=[cube(f"ntucc-bench-seat-{bench_index}",(1.04,.35,.10),(x+bx,y+by,1.20),wood,.025),cube(f"ntucc-bench-back-{bench_index}",(1.04,.09,.42),(x+bx,y+by+.16,1.44),wood,.025)]
        for leg in (-.37,.37):parts.append(cube(f"ntucc-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.03),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation
    cube("ntucc-wayfinding-monument",(.62,.30,1.45),(x-3.12,y-1.64,1.78),ivory,.08)
    cube("ntucc-wayfinding-inset",(.46,.035,.90),(x-3.12,y-1.81,1.82),rose,.035)

    for lamp_index,(lx,ly) in enumerate(((-3.20,-2.75),(-2.25,-3.55),(-.90,-3.68),(.90,-3.68),(2.25,-3.55),(3.20,-2.75),(-3.38,.25),(3.38,.25))):
        cone(f"ntucc-lamp-post-{lamp_index}",.038,.048,.88,(x+lx,y+ly,1.53),metal,10)
        sphere(f"ntucc-lamp-{lamp_index}",.12,(x+lx,y+ly,2.02),glow,subdivisions=2)

    # 大小喬木形成醫院後側與兩翼景觀，不遮擋主入口。
    for tree_index,(tx,ty,blossom,scale) in enumerate(((-3.32,1.25,False,.72),(3.32,1.20,False,.72),(-3.55,-.45,True,.64),(3.55,-.42,True,.64),(-2.48,2.18,False,.58),(2.50,2.18,True,.58))):
        tree(f"ntucc-campus-tree-{tree_index}",x+tx,y+ty,.96,blossom,scale)
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-2.68,.88,.50),(-2.55,-2.55,.62,.28),(2.55,-2.55,.62,.28))):
        for flower_index in range(18):
            angle=flower_index/18*math.tau+bed_index*.35;radius=.64 if flower_index%2 else .90
            sphere(f"ntucc-flower-{bed_index}-{flower_index}",.085,(x+cx+math.cos(angle)*rx*radius,y+cy+math.sin(angle)*ry*radius,1.23),rose if flower_index%3 else white,(1,.86,.72),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("ENV-NTUCC-CAMPUS-LANDSCAPE-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        if obj.parent is None:obj.parent=root


def pathology_island(x,y):
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(PATHOLOGY_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-PATHOLOGY-ISLAND-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,-1.0-mins.z*scale)
    for obj in imported:
        obj.name="pathology-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def imaging_pavilion(x,y):
    """匯入獨立的影像檢查館；島體與庭園維持各自可替換的組裝層。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(IMAGING_PAVILION_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.75/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-IMAGING-PAVILION-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="imaging-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def imaging_terrain(x,y):
    """匯入獨立島體；與檢查館共享中心與正面方向，但不共用網格。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(IMAGING_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-IMAGING-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,-1.0-mins.z*scale)
    for obj in imported:
        obj.name="imaging-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def imaging_garden_props(x,y):
    """影像檢查島第三層：展示棚、植栽、座椅與路燈，保持為可獨立替換物件。"""
    before=set(bpy.context.scene.objects)
    wood=material("imaging-props-walnut",(.31,.19,.12),.62)
    dark=material("imaging-props-metal",(.12,.15,.15),.42)
    stone=material("imaging-props-stone",(.72,.63,.53),.78)
    roof_mat=material("imaging-props-roof",(.28,.48,.49),.44)
    glow=material("imaging-props-lantern-glow",(1.0,.66,.28),.24,(1.0,.38,.10))
    rose=material("imaging-props-rose",(.78,.34,.43),.68)
    white=material("imaging-props-white-flower",(.92,.84,.74),.72)
    leaf=material("imaging-props-leaf",(.27,.43,.24),.76)

    # 左側衛教展示棚：四柱、銅綠屋頂與三面檢查圖板。
    sx,sy=x-1.78,y-.28
    cube("imaging-prop-shelter-platform",(1.46,.92,.13),(sx,sy,1.02),stone,.06)
    for side_x in (-.58,.58):
        for side_y in (-.34,.34):
            cube(f"imaging-prop-shelter-post-{side_x}-{side_y}",(.10,.10,1.06),(sx+side_x,sy+side_y,1.56),wood,.025)
    shelter_roof=cube("imaging-prop-shelter-roof",(1.58,1.02,.13),(sx,sy,2.14),roof_mat,.10)
    shelter_roof.rotation_euler[1]=math.radians(-4)
    panel=cube("imaging-prop-education-board",(1.12,.08,.48),(sx,sy+.30,1.48),dark,.035)
    for index in range(3):
        cube(f"imaging-prop-board-inset-{index}",(.28,.025,.32),(sx-.36+index*.36,sy+.345,1.48),stone,.025)

    # 兩張長椅：座面與靠背分件，避免融合成塊。
    for bench_index,(bx,by,rotation) in enumerate(((-1.28,-1.72,-.12),(1.36,-1.62,.12))):
        parts=[]
        parts.append(cube(f"imaging-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025))
        back=cube(f"imaging-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025);parts.append(back)
        for leg in (-.36,.36):parts.append(cube(f"imaging-prop-bench-leg-{bench_index}-{leg}",(.08,.26,.36),(x+bx+leg,y+by,1.00),dark,.018))
        for part in parts:part.rotation_euler[2]=rotation

    # 暖光路燈沿中央動線排列。
    for lamp_index,(lx,ly) in enumerate(((-.82,-1.12),(.78,-1.10),(-1.98,-1.12),(1.98,-1.04),(-2.22,.72),(2.20,.65))):
        cone(f"imaging-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),dark,10)
        cube(f"imaging-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"imaging-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),dark,8)

    # 兩側樹叢與櫻花樹使用分離樹幹、樹冠；不併入島體碰撞。
    tree("imaging-prop-tree-back-left",x-1.65,y+1.72,.96,False,.62)
    tree("imaging-prop-tree-back-right",x+1.65,y+1.66,.96,False,.60)
    tree("imaging-prop-cherry-left",x-2.18,y+.72,.96,True,.58)
    tree("imaging-prop-cherry-right",x+2.18,y+.52,.96,True,.58)

    # 中央與兩側花圃，花朵均為獨立小簇。
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-1.54,.78,.34),(-1.82,-1.26,.54,.25),(1.82,-1.18,.54,.25))):
        for flower_index in range(14):
            angle=flower_index/14*math.tau + bed_index*.4
            radius=.62 if flower_index%2 else .88
            px=x+cx+math.cos(angle)*rx*radius;py=y+cy+math.sin(angle)*ry*radius
            sphere(f"imaging-prop-flower-{bed_index}-{flower_index}",.085,(px,py,1.10),rose if flower_index%3 else white,(1,.88,.72),1)
        for shrub_index in range(7):
            angle=shrub_index/7*math.tau
            sphere(f"imaging-prop-shrub-{bed_index}-{shrub_index}",.16,(x+cx+math.cos(angle)*rx*.52,y+cy+math.sin(angle)*ry*.52,1.08),leaf,(1.15,.9,.65),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-IMAGING-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="imaging-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def medical_oncology_clinic(x,y):
    """匯入獨立輸液治療館；島體與庭園將維持不同組裝層。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(MEDICAL_ONCOLOGY_CLINIC_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.75/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-MEDICAL-ONCOLOGY-CLINIC-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="medical-oncology-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def medical_oncology_terrain(x,y):
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(MEDICAL_ONCOLOGY_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-MEDICAL-ONCOLOGY-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,-1.0-mins.z*scale)
    for obj in imported:
        obj.name="medical-oncology-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def surgical_oncology_center(x,y):
    """外科腫瘤島建築主體；坡道、庭園與島體維持可獨立替換的組裝層。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(SURGICAL_ONCOLOGY_CENTER_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.60/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-SURGICAL-ONCOLOGY-CENTER-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.42-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="surgical-oncology-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def surgical_oncology_terrain(x,y):
    """匯入外科島獨立岩岸、步道、碼頭與橋接基座。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(SURGICAL_ONCOLOGY_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-SURGICAL-ONCOLOGY-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    # Hunyuan GLB 含內部縮放節點；以最高可行走面對齊建築基座，避免整座建築懸浮。
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-maxs.z*scale)
    for obj in imported:
        obj.name="surgical-oncology-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def surgical_oncology_accessibility(x,y):
    """以乾淨的 Blender 幾何重建雙側入口坡道與扶手，覆蓋生成模型的融合瑕疵。"""
    before=set(bpy.context.scene.objects)
    ramp_mat=material("surgical-ramp-stone",(.76,.66,.56),.72)
    rail_mat=material("surgical-ramp-rail",(.67,.70,.66),.30)
    segments=12
    for side in (-1,1):
        points=[]
        for index in range(segments+1):
            t=index/segments
            # 入口向左右外展後回到前方廣場，形成海報中的對稱弧形無障礙坡道。
            px=x+side*(.56+1.05*t-.18*t*t)
            py=y-.56-.50*t-.32*t*t
            pz=1.10-.14*t
            points.append((px,py,pz))
        for index,(start,end) in enumerate(zip(points,points[1:])):
            dx=end[0]-start[0];dy=end[1]-start[1];length=math.hypot(dx,dy)
            tile=cube(f"surgical-ramp-deck-{side}-{index}",(length+.025,.54,.10),((start[0]+end[0])/2,(start[1]+end[1])/2,(start[2]+end[2])/2),ramp_mat,.025)
            tile.rotation_euler[2]=math.atan2(dy,dx)
            if index%2==0:
                tangent=Vector((dx,dy,0)).normalized();normal=Vector((-tangent.y,tangent.x,0))*side
                post_x=(start[0]+end[0])/2+normal.x*.29;post_y=(start[1]+end[1])/2+normal.y*.29
                cube(f"surgical-ramp-post-{side}-{index}",(.045,.045,.58),(post_x,post_y,(start[2]+end[2])/2+.31),rail_mat,.012)
        # 連續扶手以短節段跟隨坡道曲線，避免 AI 生成的黏合護欄。
        rail_points=[]
        for px,py,pz in points:
            rail_points.append((px+side*.29,py,pz+.57))
        for index,(start,end) in enumerate(zip(rail_points,rail_points[1:])):
            dx=end[0]-start[0];dy=end[1]-start[1];length=math.hypot(dx,dy)
            rail=cube(f"surgical-ramp-handrail-{side}-{index}",(length+.035,.045,.045),((start[0]+end[0])/2,(start[1]+end[1])/2,(start[2]+end[2])/2),rail_mat,.018)
            rail.rotation_euler[2]=math.atan2(dy,dx)
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-SURGICAL-ONCOLOGY-ACCESSIBILITY-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="surgical-access-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def reconstruction_center(x,y):
    """匯入獨立花瓣屋頂乳房重建中心。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(RECONSTRUCTION_CENTER_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.60/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-RECONSTRUCTION-CENTER-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.40-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="reconstruction-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def reconstruction_terrain(x,y):
    """匯入已清除游離薄片的重建島岩岸、步道、碼頭與橋接基座。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(RECONSTRUCTION_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-RECONSTRUCTION-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-maxs.z*scale)
    for obj in imported:
        obj.name="reconstruction-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def radiation_oncology_center(x,y):
    """匯入獨立圓形放射治療中心，保留玻璃側翼、入口與無障礙坡道。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(RADIATION_ONCOLOGY_CENTER_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.72/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-RADIATION-ONCOLOGY-CENTER-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.42-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="radiation-oncology-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def radiation_oncology_terrain(x,y):
    """匯入放射腫瘤島岩岸、圓形基座、步道、碼頭與聯島接口。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(RADIATION_ONCOLOGY_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-RADIATION-ONCOLOGY-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-maxs.z*scale)
    for obj in imported:
        obj.name="radiation-oncology-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def cardiology_center(x,y):
    """匯入獨立雙翼心形心臟評估中心。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(CARDIOLOGY_CENTER_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.82/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-CARDIOLOGY-CENTER-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.42-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="cardiology-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def cardiology_terrain(x,y):
    """匯入心臟科島岩岸、橢圓基座、無障礙步道、碼頭與聯島接口。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(CARDIOLOGY_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-CARDIOLOGY-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-maxs.z*scale)
    for obj in imported:
        obj.name="cardiology-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def family_medicine_center(x,y):
    """匯入獨立環形家庭醫學與癌症存活照護中心。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(FAMILY_MEDICINE_CENTER_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.86/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-FAMILY-MEDICINE-CENTER-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.46-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="family-medicine-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def family_medicine_terrain(x,y):
    """匯入家庭醫學島岩岸、診所平台、藥草園基座、步道與碼頭。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(FAMILY_MEDICINE_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-FAMILY-MEDICINE-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-maxs.z*scale)
    for obj in imported:
        obj.name="family-medicine-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def rehabilitation_center(x,y):
    """匯入獨立三翼復健與動作恢復中心。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(REHABILITATION_CENTER_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.92/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-REHABILITATION-CENTER-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.48-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="rehabilitation-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def rehabilitation_terrain(x,y):
    """匯入復健島岩岸、水療池、觸覺步道、運動平台與聯島接口。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(REHABILITATION_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-REHABILITATION-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-maxs.z*scale)
    for obj in imported:
        obj.name="rehabilitation-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def fertility_center(x,y):
    """匯入獨立花瓣形生育保存與生殖諮詢中心。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(FERTILITY_CENTER_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=3.98/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("BLD-FERTILITY-PRESERVATION-CENTER-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.48-(mins.y+maxs.y)*.5*scale,.94-mins.z*scale)
    for obj in imported:
        obj.name="fertility-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def fertility_terrain(x,y):
    """匯入生育保存島岩岸、多瓣中心平台、花園基座、步道與碼頭。"""
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(FERTILITY_TERRAIN_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=6.25/max(maxs.x-mins.x,maxs.y-mins.y)
    root=bpy.data.objects.new("ENV-FERTILITY-PRESERVATION-TERRAIN-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y-(mins.y+maxs.y)*.5*scale,.94-maxs.z*scale)
    for obj in imported:
        obj.name="fertility-terrain-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def medical_oncology_garden_props(x,y):
    """腫瘤內科島第三層：輸液衛教棚、座椅、暖光燈、植栽與花圃。"""
    before=set(bpy.context.scene.objects)
    wood=material("medonc-props-walnut",(.31,.19,.12),.64)
    dark=material("medonc-props-metal",(.13,.15,.15),.42)
    stone=material("medonc-props-stone",(.75,.65,.54),.78)
    roof_mat=material("medonc-props-roof",(.40,.52,.42),.46)
    glow=material("medonc-props-lantern-glow",(1.0,.67,.30),.24,(1.0,.40,.11))
    rose=material("medonc-props-rose",(.80,.35,.45),.68)
    white=material("medonc-props-white-flower",(.94,.86,.76),.72)
    leaf=material("medonc-props-leaf",(.30,.45,.25),.76)

    sx,sy=x-1.78,y-.30
    cube("medonc-prop-shelter-platform",(1.46,.92,.13),(sx,sy,1.02),stone,.06)
    for side_x in (-.58,.58):
        for side_y in (-.34,.34):cube(f"medonc-prop-shelter-post-{side_x}-{side_y}",(.10,.10,1.06),(sx+side_x,sy+side_y,1.56),wood,.025)
    cube("medonc-prop-shelter-roof",(1.58,1.02,.13),(sx,sy,2.14),roof_mat,.10)
    cube("medonc-prop-education-board",(1.12,.08,.48),(sx,sy+.30,1.48),dark,.035)
    for index in range(3):
        cube(f"medonc-prop-board-inset-{index}",(.28,.025,.32),(sx-.36+index*.36,sy+.345,1.48),stone,.025)
        # 每一格以輸液袋外形標記，不使用文字貼圖。
        cube(f"medonc-prop-iv-bag-{index}",(.10,.02,.15),(sx-.36+index*.36,sy+.365,1.50),rose,.025)

    for bench_index,(bx,by,rotation) in enumerate(((-1.28,-1.72,-.12),(1.36,-1.62,.12))):
        parts=[cube(f"medonc-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"medonc-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.36,.36):parts.append(cube(f"medonc-prop-bench-leg-{bench_index}-{leg}",(.08,.26,.36),(x+bx+leg,y+by,1.00),dark,.018))
        for part in parts:part.rotation_euler[2]=rotation

    for lamp_index,(lx,ly) in enumerate(((-.82,-1.12),(.78,-1.10),(-1.98,-1.12),(1.98,-1.04),(-2.22,.72),(2.20,.65))):
        cone(f"medonc-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),dark,10)
        cube(f"medonc-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"medonc-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),dark,8)

    tree("medonc-prop-tree-back-left",x-1.65,y+1.72,.96,False,.62)
    tree("medonc-prop-tree-back-right",x+1.65,y+1.66,.96,False,.60)
    tree("medonc-prop-cherry-left",x-2.18,y+.72,.96,True,.58)
    tree("medonc-prop-cherry-right",x+2.18,y+.52,.96,True,.58)
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-1.54,.78,.34),(-1.82,-1.26,.54,.25),(1.82,-1.18,.54,.25))):
        for flower_index in range(14):
            angle=flower_index/14*math.tau+bed_index*.4;radius=.62 if flower_index%2 else .88
            sphere(f"medonc-prop-flower-{bed_index}-{flower_index}",.085,(x+cx+math.cos(angle)*rx*radius,y+cy+math.sin(angle)*ry*radius,1.10),rose if flower_index%3 else white,(1,.88,.72),1)
        for shrub_index in range(7):
            angle=shrub_index/7*math.tau
            sphere(f"medonc-prop-shrub-{bed_index}-{shrub_index}",.16,(x+cx+math.cos(angle)*rx*.52,y+cy+math.sin(angle)*ry*.52,1.08),leaf,(1.15,.9,.65),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-MEDICAL-ONCOLOGY-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="medonc-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def surgical_oncology_garden_props(x,y):
    """外科島獨立庭園層：衛教棚、座椅、步道燈、櫻花樹與花圃。"""
    before=set(bpy.context.scene.objects)
    wood=material("surgical-props-walnut",(.34,.20,.12),.62)
    metal=material("surgical-props-metal",(.18,.20,.19),.38)
    stone=material("surgical-props-stone",(.72,.63,.53),.76)
    roof_mat=material("surgical-props-roof",(.38,.49,.41),.44)
    glow=material("surgical-props-lantern-glow",(1.0,.68,.31),.22,(1.0,.39,.10))
    rose=material("surgical-props-rose",(.82,.38,.48),.66)
    white=material("surgical-props-white-flower",(.96,.88,.78),.70)
    leaf=material("surgical-props-leaf",(.30,.46,.25),.74)

    # 海報左側的三格術前衛教棚，與治療中心保持可獨立替換。
    sx,sy=x-1.83,y-.06
    cube("surgical-prop-shelter-platform",(1.48,.88,.13),(sx,sy,1.02),stone,.06)
    for side_x in (-.59,.59):
        for side_y in (-.32,.32):cube(f"surgical-prop-shelter-post-{side_x}-{side_y}",(.10,.10,1.02),(sx+side_x,sy+side_y,1.54),wood,.025)
    cube("surgical-prop-shelter-roof",(1.62,1.02,.14),(sx,sy,2.10),roof_mat,.10)
    cube("surgical-prop-education-board",(1.14,.07,.48),(sx,sy+.30,1.47),metal,.035)
    for index in range(3):
        px=sx-.37+index*.37
        cube(f"surgical-prop-board-panel-{index}",(.29,.025,.33),(px,sy+.345,1.47),stone,.025)
        # 清單、生命徵象與安全盾牌的抽象圖示，不使用不可讀的生成文字。
        icon=rose if index!=1 else roof_mat
        sphere(f"surgical-prop-board-icon-{index}",.075,(px,sy+.37,1.48),icon,(1,.42,1),1)

    for bench_index,(bx,by,rotation) in enumerate(((-1.20,-1.62,-.13),(1.25,-1.60,.13))):
        parts=[cube(f"surgical-prop-bench-seat-{bench_index}",(1.00,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"surgical-prop-bench-back-{bench_index}",(1.00,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.35,.35):parts.append(cube(f"surgical-prop-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.00),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation

    for lamp_index,(lx,ly) in enumerate(((-.78,-1.08),(.76,-1.08),(-1.94,-1.02),(1.94,-1.02),(-2.22,.72),(2.20,.68))):
        cone(f"surgical-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),metal,10)
        cube(f"surgical-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"surgical-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),metal,8)

    tree("surgical-prop-tree-back-left",x-1.62,y+1.70,.96,False,.62)
    tree("surgical-prop-tree-back-right",x+1.62,y+1.66,.96,False,.60)
    tree("surgical-prop-cherry-left",x-2.16,y+.74,.96,True,.58)
    tree("surgical-prop-cherry-right",x+2.16,y+.58,.96,True,.58)
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-1.46,.76,.32),(-1.74,-1.20,.52,.24),(1.74,-1.18,.52,.24))):
        for flower_index in range(14):
            angle=flower_index/14*math.tau+bed_index*.4;radius=.62 if flower_index%2 else .88
            sphere(f"surgical-prop-flower-{bed_index}-{flower_index}",.085,(x+cx+math.cos(angle)*rx*radius,y+cy+math.sin(angle)*ry*radius,1.10),rose if flower_index%3 else white,(1,.88,.72),1)
        for shrub_index in range(7):
            angle=shrub_index/7*math.tau
            sphere(f"surgical-prop-shrub-{bed_index}-{shrub_index}",.16,(x+cx+math.cos(angle)*rx*.52,y+cy+math.sin(angle)*ry*.52,1.08),leaf,(1.15,.9,.65),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-SURGICAL-ONCOLOGY-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="surgical-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def reconstruction_garden_props(x,y):
    """乳房重建島庭園層：重建衛教棚、座椅、暖光燈、櫻花樹與花圃。"""
    before=set(bpy.context.scene.objects)
    wood=material("reconstruction-props-walnut",(.34,.20,.13),.62)
    metal=material("reconstruction-props-metal",(.28,.25,.24),.36)
    stone=material("reconstruction-props-stone",(.78,.68,.58),.74)
    roof_mat=material("reconstruction-props-roof",(.55,.59,.48),.44)
    glow=material("reconstruction-props-lantern-glow",(1.0,.68,.31),.22,(1.0,.39,.10))
    rose=material("reconstruction-props-rose",(.84,.43,.52),.64)
    blush=material("reconstruction-props-blush",(.91,.64,.65),.66)
    white=material("reconstruction-props-white-flower",(.96,.88,.78),.70)
    leaf=material("reconstruction-props-leaf",(.31,.47,.26),.74)

    # 海報左側的三格重建衛教展示棚。
    sx,sy=x-1.86,y-.06
    cube("reconstruction-prop-shelter-platform",(1.50,.90,.13),(sx,sy,1.02),stone,.06)
    for side_x in (-.60,.60):
        for side_y in (-.33,.33):cube(f"reconstruction-prop-shelter-post-{side_x}-{side_y}",(.10,.10,1.04),(sx+side_x,sy+side_y,1.55),wood,.025)
    cube("reconstruction-prop-shelter-roof",(1.64,1.04,.14),(sx,sy,2.12),roof_mat,.10)
    cube("reconstruction-prop-education-board",(1.16,.07,.49),(sx,sy+.31,1.48),metal,.035)
    for index in range(3):
        px=sx-.38+index*.38
        cube(f"reconstruction-prop-board-panel-{index}",(.30,.025,.34),(px,sy+.355,1.48),stone,.025)
        # 使用葉片、曲線與對稱外形作抽象重建選項，不生成不可讀文字。
        sphere(f"reconstruction-prop-board-icon-{index}",.078,(px,sy+.38,1.49),rose if index!=1 else blush,(1,.48,1),1)

    for bench_index,(bx,by,rotation) in enumerate(((-1.28,-1.64,-.12),(1.34,-1.60,.12))):
        parts=[cube(f"reconstruction-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"reconstruction-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.36,.36):parts.append(cube(f"reconstruction-prop-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.00),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation

    for lamp_index,(lx,ly) in enumerate(((-.80,-1.08),(.78,-1.08),(-1.98,-1.02),(1.98,-1.02),(-2.24,.72),(2.22,.68))):
        cone(f"reconstruction-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),metal,10)
        cube(f"reconstruction-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"reconstruction-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),metal,8)

    tree("reconstruction-prop-tree-back-left",x-1.62,y+1.72,.96,False,.62)
    tree("reconstruction-prop-tree-back-right",x+1.62,y+1.68,.96,False,.60)
    tree("reconstruction-prop-cherry-left",x-2.17,y+.74,.96,True,.58)
    tree("reconstruction-prop-cherry-right",x+2.17,y+.58,.96,True,.58)
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-1.46,.78,.33),(-1.76,-1.20,.53,.24),(1.76,-1.18,.53,.24))):
        for flower_index in range(16):
            angle=flower_index/16*math.tau+bed_index*.4;radius=.62 if flower_index%2 else .88
            flower_mat=(rose,blush,white)[flower_index%3]
            sphere(f"reconstruction-prop-flower-{bed_index}-{flower_index}",.085,(x+cx+math.cos(angle)*rx*radius,y+cy+math.sin(angle)*ry*radius,1.10),flower_mat,(1,.88,.72),1)
        for shrub_index in range(7):
            angle=shrub_index/7*math.tau
            sphere(f"reconstruction-prop-shrub-{bed_index}-{shrub_index}",.16,(x+cx+math.cos(angle)*rx*.52,y+cy+math.sin(angle)*ry*.52,1.08),leaf,(1.15,.9,.65),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-RECONSTRUCTION-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="reconstruction-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def radiation_oncology_garden_props(x,y):
    """放射腫瘤島獨立層：標靶衛教亭、座椅、暖光燈、花圃與遮蔭樹。"""
    before=set(bpy.context.scene.objects)
    wood=material("radiation-props-walnut",(.32,.20,.13),.62)
    metal=material("radiation-props-metal",(.24,.28,.26),.34)
    stone=material("radiation-props-stone",(.79,.69,.58),.74)
    sage=material("radiation-props-sage",(.42,.54,.37),.44)
    glow=material("radiation-props-lantern-glow",(1.0,.69,.31),.22,(1.0,.40,.10))
    red=material("radiation-props-target-red",(.72,.17,.18),.52)
    cream=material("radiation-props-target-cream",(.93,.81,.68),.68)
    gold=material("radiation-props-gold",(.72,.51,.22),.38)
    flower=material("radiation-props-flower",(.83,.46,.48),.66)
    white=material("radiation-props-white-flower",(.96,.89,.78),.70)
    leaf=material("radiation-props-leaf",(.30,.47,.25),.74)

    sx,sy=x-1.84,y-.02
    cube("radiation-prop-shelter-platform",(1.52,.92,.13),(sx,sy,1.02),stone,.06)
    for side_x in (-.60,.60):
        for side_y in (-.34,.34):cube(f"radiation-prop-shelter-post-{side_x}-{side_y}",(.10,.10,1.04),(sx+side_x,sy+side_y,1.55),wood,.025)
    cube("radiation-prop-shelter-roof",(1.66,1.06,.14),(sx,sy,2.12),sage,.10)
    cube("radiation-prop-education-board",(1.16,.07,.50),(sx,sy+.31,1.49),metal,.035)
    for index in range(3):
        px=sx-.38+index*.38
        cube(f"radiation-prop-board-panel-{index}",(.30,.025,.35),(px,sy+.355,1.49),cream,.025)
        for ring,(radius,ring_mat) in enumerate(((.090,red),(.060,cream),(.030,red))):
            target=cone(f"radiation-prop-target-{index}-{ring}",radius,radius,.018,(px,sy+.381,1.49),ring_mat,24)
            target.rotation_euler[0]=math.radians(90)

    for bench_index,(bx,by,rotation) in enumerate(((-1.22,-1.62,-.13),(1.28,-1.58,.13))):
        parts=[cube(f"radiation-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"radiation-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.36,.36):parts.append(cube(f"radiation-prop-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.00),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation

    for lamp_index,(lx,ly) in enumerate(((-.80,-1.08),(.78,-1.08),(-1.98,-1.02),(1.98,-1.02),(-2.24,.72),(2.22,.68))):
        cone(f"radiation-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),metal,10)
        cube(f"radiation-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"radiation-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),gold,8)

    tree("radiation-prop-tree-back-left",x-1.64,y+1.72,.96,False,.62)
    tree("radiation-prop-tree-back-right",x+1.64,y+1.68,.96,False,.60)
    tree("radiation-prop-cherry-left",x-2.18,y+.72,.96,True,.58)
    tree("radiation-prop-cherry-right",x+2.18,y+.56,.96,True,.58)
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-1.45,.78,.33),(-1.76,-1.18,.53,.24),(1.76,-1.16,.53,.24))):
        for flower_index in range(16):
            angle=flower_index/16*math.tau+bed_index*.4;radius=.62 if flower_index%2 else .88
            sphere(f"radiation-prop-flower-{bed_index}-{flower_index}",.085,(x+cx+math.cos(angle)*rx*radius,y+cy+math.sin(angle)*ry*radius,1.10),flower if flower_index%3 else white,(1,.88,.72),1)
        for shrub_index in range(7):
            angle=shrub_index/7*math.tau
            sphere(f"radiation-prop-shrub-{bed_index}-{shrub_index}",.16,(x+cx+math.cos(angle)*rx*.52,y+cy+math.sin(angle)*ry*.52,1.08),leaf,(1.15,.9,.65),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-RADIATION-ONCOLOGY-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="radiation-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def cardiology_garden_props(x,y):
    """心臟科島獨立層：血壓與心臟健康衛教亭、休憩設施、花圃與樹木。"""
    before=set(bpy.context.scene.objects)
    wood=material("cardiology-props-walnut",(.33,.20,.13),.62)
    metal=material("cardiology-props-metal",(.20,.23,.23),.36)
    stone=material("cardiology-props-stone",(.80,.69,.58),.74)
    burgundy=material("cardiology-props-burgundy",(.48,.16,.20),.44)
    glow=material("cardiology-props-lantern-glow",(1.0,.69,.31),.22,(1.0,.40,.10))
    rose=material("cardiology-props-rose",(.78,.34,.42),.62)
    cream=material("cardiology-props-cream",(.94,.84,.72),.70)
    leaf=material("cardiology-props-leaf",(.30,.47,.25),.74)

    sx,sy=x-1.84,y-.02
    cube("cardiology-prop-shelter-platform",(1.52,.92,.13),(sx,sy,1.02),stone,.06)
    for side_x in (-.60,.60):
        for side_y in (-.34,.34):cube(f"cardiology-prop-shelter-post-{side_x}-{side_y}",(.10,.10,1.04),(sx+side_x,sy+side_y,1.55),wood,.025)
    cube("cardiology-prop-shelter-roof",(1.66,1.06,.14),(sx,sy,2.12),burgundy,.10)
    cube("cardiology-prop-education-board",(1.16,.07,.50),(sx,sy+.31,1.49),metal,.035)
    for index in range(3):
        px=sx-.38+index*.38
        cube(f"cardiology-prop-board-panel-{index}",(.30,.025,.35),(px,sy+.355,1.49),cream,.025)
        # 心跳點與連線形成可讀的心電圖抽象圖示。
        for beat,(offset,height) in enumerate(((-.09,0),(-.045,.06),(0,-.08),(.045,.10),(.09,0))):
            sphere(f"cardiology-prop-ecg-{index}-{beat}",.025,(px+offset,sy+.382,1.49+height),rose,(1,.45,1),1)

    for bench_index,(bx,by,rotation) in enumerate(((-1.22,-1.62,-.13),(1.28,-1.58,.13))):
        parts=[cube(f"cardiology-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"cardiology-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.36,.36):parts.append(cube(f"cardiology-prop-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.00),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation

    for lamp_index,(lx,ly) in enumerate(((-.80,-1.08),(.78,-1.08),(-1.98,-1.02),(1.98,-1.02),(-2.24,.72),(2.22,.68))):
        cone(f"cardiology-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),metal,10)
        cube(f"cardiology-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"cardiology-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),burgundy,8)

    tree("cardiology-prop-tree-back-left",x-1.64,y+1.72,.96,False,.62)
    tree("cardiology-prop-tree-back-right",x+1.64,y+1.68,.96,False,.60)
    tree("cardiology-prop-cherry-left",x-2.18,y+.72,.96,True,.58)
    tree("cardiology-prop-cherry-right",x+2.18,y+.56,.96,True,.58)
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-1.45,.78,.33),(-1.76,-1.18,.53,.24),(1.76,-1.16,.53,.24))):
        for flower_index in range(16):
            angle=flower_index/16*math.tau+bed_index*.4;radius=.62 if flower_index%2 else .88
            sphere(f"cardiology-prop-flower-{bed_index}-{flower_index}",.085,(x+cx+math.cos(angle)*rx*radius,y+cy+math.sin(angle)*ry*radius,1.10),rose if flower_index%3 else cream,(1,.88,.72),1)
        for shrub_index in range(7):
            angle=shrub_index/7*math.tau
            sphere(f"cardiology-prop-shrub-{bed_index}-{shrub_index}",.16,(x+cx+math.cos(angle)*rx*.52,y+cy+math.sin(angle)*ry*.52,1.08),leaf,(1.15,.9,.65),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-CARDIOLOGY-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="cardiology-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def family_medicine_garden_props(x,y):
    """家庭醫學島獨立層：預防保健衛教亭、藥草園、果樹、座椅與暖光步道。"""
    before=set(bpy.context.scene.objects)
    wood=material("family-props-walnut",(.34,.22,.13),.62)
    metal=material("family-props-metal",(.22,.25,.23),.38)
    stone=material("family-props-stone",(.82,.73,.60),.76)
    sage=material("family-props-sage",(.40,.51,.34),.48)
    terracotta=material("family-props-terracotta",(.64,.34,.22),.62)
    glow=material("family-props-lantern-glow",(1.0,.70,.33),.22,(1.0,.42,.11))
    cream=material("family-props-cream",(.95,.87,.72),.72)
    herb=material("family-props-herb",(.25,.48,.22),.74)
    blossom=material("family-props-blossom",(.86,.60,.51),.68)

    # 左側衛教亭與四格抽象健康主題面板。
    sx,sy=x-1.88,y-.02
    cube("family-prop-shelter-platform",(1.54,.94,.13),(sx,sy,1.02),stone,.06)
    for side_x in (-.61,.61):
        for side_y in (-.35,.35):cube(f"family-prop-shelter-post-{side_x}-{side_y}",(.10,.10,1.05),(sx+side_x,sy+side_y,1.56),wood,.025)
    cube("family-prop-shelter-roof",(1.70,1.08,.14),(sx,sy,2.13),sage,.11)
    cube("family-prop-education-board",(1.20,.07,.51),(sx,sy+.32,1.50),metal,.035)
    for index in range(4):
        px=sx-.42+index*.28
        cube(f"family-prop-health-panel-{index}",(.22,.025,.34),(px,sy+.365,1.50),cream,.025)
        sphere(f"family-prop-health-symbol-{index}",.065,(px,sy+.39,1.50),terracotta,(1,.38,1),1)

    # 中央圓形藥草園與前側長形菜圃均維持可繞行淨寬。
    for bed_index,(cx,cy,rx,ry,count) in enumerate(((0,-.92,.68,.43,18),(1.50,-1.34,.62,.25,14))):
        for plant_index in range(count):
            angle=plant_index/count*math.tau+bed_index*.27
            radius=.48 if plant_index%3 else .78
            px=x+cx+math.cos(angle)*rx*radius;py=y+cy+math.sin(angle)*ry*radius
            sphere(f"family-prop-herb-{bed_index}-{plant_index}",.095,(px,py,1.10),herb if plant_index%4 else blossom,(.85,.70,1.15),1)

    for bench_index,(bx,by,rotation) in enumerate(((-1.15,-1.64,-.12),(1.02,-1.72,.12))):
        parts=[cube(f"family-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"family-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.36,.36):parts.append(cube(f"family-prop-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.00),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation

    for lamp_index,(lx,ly) in enumerate(((-.72,-1.18),(.62,-1.20),(-2.12,-1.00),(2.08,-.96),(-2.30,.84),(2.25,.78))):
        cone(f"family-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),metal,10)
        cube(f"family-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"family-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),sage,8)

    tree("family-prop-orchard-left",x-1.70,y+1.70,.96,False,.63)
    tree("family-prop-orchard-right",x+1.72,y+1.66,.96,False,.61)
    tree("family-prop-blossom-left",x-2.25,y+.72,.96,True,.56)
    tree("family-prop-blossom-right",x+2.24,y+.62,.96,True,.56)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-FAMILY-MEDICINE-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="family-medicine-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def rehabilitation_therapy_props(x,y):
    """復健島獨立層：戶外步態廊道、運動器材、水療水面、座椅與暖光植栽。"""
    before=set(bpy.context.scene.objects)
    wood=material("rehab-props-walnut",(.34,.22,.13),.62)
    metal=material("rehab-props-metal",(.22,.28,.28),.34)
    stone=material("rehab-props-stone",(.82,.73,.61),.76)
    teal=material("rehab-props-teal",(.30,.58,.56),.44)
    water=material("rehab-props-water",(.20,.62,.68),.18)
    glow=material("rehab-props-lantern-glow",(1.0,.70,.33),.22,(1.0,.42,.11))
    leaf=material("rehab-props-leaf",(.29,.48,.28),.72)
    flower=material("rehab-props-flower",(.84,.48,.57),.68)

    # 左側弧形步態訓練廊道，以多組柱、扶手及分段屋頂形成可走動的訓練路徑。
    for index in range(7):
        angle=math.radians(150-index*14)
        px=x-1.12+math.cos(angle)*1.18;py=y-.10+math.sin(angle)*.92
        cone(f"rehab-prop-colonnade-post-{index}",.055,.065,1.18,(px,py,1.55),stone,10)
        cube(f"rehab-prop-colonnade-roof-{index}",(.62,.48,.11),(px,py,2.18),teal,.08).rotation_euler[2]=angle-math.pi/2
        for side in (-1,1):
            cone(f"rehab-prop-parallel-bar-{index}-{side}",.025,.025,.72,(px+side*.22,py,1.34),metal,8)

    # 水療池透明水面維持低於池緣，避免角色碰撞。
    water_surface=cone("rehab-prop-hydrotherapy-water",.64,.64,.045,(x-1.25,y-.78,1.005),water,32)
    water_surface.scale.y=.70

    # 右側戶外復健平台：平衡墊、低階踏箱、阻力球與器材架。
    ex,ey=x+1.55,y-.32
    cube("rehab-prop-exercise-platform",(1.50,.94,.10),(ex,ey,1.03),stone,.05)
    for index,(ox,oy) in enumerate(((-.42,-.18),(0,-.18),(.42,-.18))):
        cube(f"rehab-prop-step-box-{index}",(.28,.28,.10+index*.04),(ex+ox,ey+oy,1.12+index*.02),teal,.035)
    for index,(ox,color_mat) in enumerate(((-.34,flower),(.02,teal),(.38,leaf))):
        sphere(f"rehab-prop-therapy-ball-{index}",.14,(ex+ox,ey+.23,1.19),color_mat,(1,1,1),2)
    cube("rehab-prop-equipment-rack",(1.12,.10,.62),(ex,ey+.38,1.39),metal,.035)

    for bench_index,(bx,by,rotation) in enumerate(((-1.14,-1.70,-.13),(1.10,-1.72,.13))):
        parts=[cube(f"rehab-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"rehab-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.36,.36):parts.append(cube(f"rehab-prop-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.00),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation
    for lamp_index,(lx,ly) in enumerate(((-.72,-1.18),(.65,-1.20),(-2.18,-.92),(2.12,-.88),(-2.30,.86),(2.28,.78))):
        cone(f"rehab-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),metal,10)
        cube(f"rehab-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"rehab-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),teal,8)
    tree("rehab-prop-tree-back-left",x-1.76,y+1.72,.96,False,.62)
    tree("rehab-prop-tree-back-right",x+1.78,y+1.68,.96,False,.61)
    tree("rehab-prop-blossom-left",x-2.25,y+.72,.96,True,.56)
    tree("rehab-prop-blossom-right",x+2.25,y+.62,.96,True,.56)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-REHABILITATION-THERAPY-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="rehabilitation-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def fertility_garden_props(x,y):
    """生育保存島獨立層：私人諮詢亭、植物溫室、希望種子雕塑、座椅與花園。"""
    before=set(bpy.context.scene.objects)
    wood=material("fertility-props-walnut",(.35,.22,.14),.62)
    metal=material("fertility-props-copper",(.58,.30,.32),.34)
    stone=material("fertility-props-stone",(.86,.76,.66),.76)
    mauve=material("fertility-props-mauve",(.57,.38,.57),.46)
    glass=material("fertility-props-glass",(.62,.82,.82),.16)
    glow=material("fertility-props-lantern-glow",(1.0,.70,.34),.22,(1.0,.42,.11))
    lavender=material("fertility-props-lavender",(.63,.43,.68),.68)
    white=material("fertility-props-white",(.96,.89,.79),.72)
    leaf=material("fertility-props-leaf",(.30,.47,.27),.74)

    # 左側私人諮詢亭。
    px,py=x-1.72,y-.40
    cone("fertility-prop-counselling-platform",.78,.78,.12,(px,py,1.02),stone,28)
    for index in range(8):
        angle=index/8*math.tau
        cone(f"fertility-prop-pavilion-post-{index}",.045,.055,1.12,(px+math.cos(angle)*.62,py+math.sin(angle)*.50,1.58),wood,8)
    cone("fertility-prop-pavilion-roof",.92,.15,.28,(px,py,2.22),mauve,24)
    cube("fertility-prop-private-table",(.42,.42,.46),(px,py,1.23),wood,.12)
    for side in (-1,1):cube(f"fertility-prop-private-chair-{side}",(.34,.36,.50),(px+side*.42,py,1.24),mauve,.09)

    # 右側玻璃植物溫室，使用銅色框架與透明穹頂切片。
    gx,gy=x+1.60,y-.38
    cone("fertility-prop-greenhouse-base",.82,.82,.10,(gx,gy,1.02),stone,28)
    for index in range(10):
        angle=index/10*math.tau
        cone(f"fertility-prop-greenhouse-frame-{index}",.025,.030,.92,(gx+math.cos(angle)*.68,gy+math.sin(angle)*.48,1.50),metal,8)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(gx,gy,1.54));dome=bpy.context.object;dome.name="fertility-prop-greenhouse-glass";dome.scale=(.78,.60,.55);dome.data.materials.append(glass)
    for index in range(12):
        angle=index/12*math.tau
        sphere(f"fertility-prop-greenhouse-plant-{index}",.10,(gx+math.cos(angle)*.48,gy+math.sin(angle)*.34,1.15),leaf,(.8,.8,1.4),1)

    # 中央種子與保護意象雕塑。
    sx,sy=x,y-.92
    cone("fertility-prop-seed-plinth",.58,.64,.20,(sx,sy,1.08),stone,28)
    seed=cone("fertility-prop-hope-seed",.26,.03,.82,(sx,sy,1.58),metal,28);seed.scale.y=.62
    for side in (-1,1):
        hand=cone(f"fertility-prop-protective-hand-{side}",.08,.18,.66,(sx+side*.28,sy,1.48),mauve,16);hand.rotation_euler[1]=side*math.radians(28)

    for bench_index,(bx,by,rotation) in enumerate(((-.92,-1.78,-.12),(1.02,-1.74,.12))):
        parts=[cube(f"fertility-prop-bench-seat-{bench_index}",(1.02,.34,.10),(x+bx,y+by,1.17),wood,.025),cube(f"fertility-prop-bench-back-{bench_index}",(1.02,.09,.42),(x+bx,y+by+.16,1.42),wood,.025)]
        for leg in (-.36,.36):parts.append(cube(f"fertility-prop-bench-leg-{bench_index}-{leg}",(.08,.25,.36),(x+bx+leg,y+by,1.00),metal,.018))
        for part in parts:part.rotation_euler[2]=rotation
    for lamp_index,(lx,ly) in enumerate(((-.68,-1.20),(.68,-1.18),(-2.12,-.92),(2.14,-.90),(-2.28,.78),(2.28,.76))):
        cone(f"fertility-prop-lamp-post-{lamp_index}",.035,.045,.78,(x+lx,y+ly,1.40),metal,10)
        cube(f"fertility-prop-lamp-head-{lamp_index}",(.24,.24,.28),(x+lx,y+ly,1.84),glow,.045)
        cone(f"fertility-prop-lamp-cap-{lamp_index}",.20,.04,.14,(x+lx,y+ly,2.05),mauve,8)
    tree("fertility-prop-blossom-left",x-2.20,y+1.30,.96,True,.63)
    tree("fertility-prop-blossom-right",x+2.20,y+1.30,.96,True,.63)
    for bed_index,(cx,cy,rx,ry) in enumerate(((0,-1.30,.80,.34),(-1.72,.20,.50,.28),(1.72,.18,.50,.28))):
        for flower_index in range(18):
            angle=flower_index/18*math.tau+bed_index*.3;radius=.60 if flower_index%2 else .88
            sphere(f"fertility-prop-flower-{bed_index}-{flower_index}",.08,(x+cx+math.cos(angle)*rx*radius,y+cy+math.sin(angle)*ry*radius,1.10),lavender if flower_index%3 else white,(1,.85,.70),1)

    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    root=bpy.data.objects.new("BLD-FERTILITY-PRESERVATION-GARDEN-PROPS-001",None);bpy.context.collection.objects.link(root)
    for obj in imported:
        obj.name="fertility-prop-hi-"+obj.name
        if obj.parent is None:obj.parent=root


def lighthouse(x,y):
    glow=material("lantern-glow",(.95,.70,.31),.25,(1.0,.45,.12))
    path=material("lighthouse-path",(.72,.62,.50));wood=material("pier-wood",(.42,.28,.18))
    rail=material("lighthouse-rail",(.24,.20,.18),.48)
    cottage_wall=material("lighthouse-cottage-wall",(.88,.76,.61),.72)
    cottage_roof=material("lighthouse-cottage-roof",(.55,.27,.24),.52)
    cottage_glass=material("lighthouse-cottage-glass",(.92,.66,.34),.18,(.78,.30,.08))
    rock=material("lighthouse-terrace-rock",(.43,.40,.38),.86)
    grass=material("lighthouse-terrace-grass",(.40,.50,.27),.82)
    before_landscape=set(bpy.context.scene.objects)
    island_base("lighthouse-core",x,y,.9)
    # 權威美術圖的雙層岩台，而非單一圓盤。
    cone("lighthouse-lower-terrace",3.05,2.72,.58,(x,y-.28,.35),rock,40)
    cone("lighthouse-lower-lawn",2.78,2.56,.18,(x,y-.28,.73),grass,40)
    cone("lighthouse-upper-terrace",2.22,1.96,.62,(x,y+.15,.88),rock,40)
    cone("lighthouse-upper-lawn",2.02,1.82,.16,(x,y+.15,1.24),grass,40)
    cone("lighthouse-plaza",1.58,1.58,.12,(x,y+.16,1.35),path,40)
    for step in range(5):
        cube(f"lighthouse-step-{step}",(1.26+step*.14,.40,.13),(x,y-1.60-step*.32,1.25-step*.10),path,.06)
    before=set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(LIGHTHOUSE_MODEL))
    imported=[obj for obj in bpy.context.scene.objects if obj not in before]
    meshes=[obj for obj in imported if obj.type == "MESH"]
    corners=[obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    mins=Vector(tuple(min(point[index] for point in corners) for index in range(3)))
    maxs=Vector(tuple(max(point[index] for point in corners) for index in range(3)))
    scale=5.25/(maxs.z-mins.z)
    root=bpy.data.objects.new("BLD-HOPE-LIGHTHOUSE-001",None);bpy.context.collection.objects.link(root)
    root.scale=(scale,scale,scale)
    root.location=(x-(mins.x+maxs.x)*.5*scale,y+.16-(mins.y+maxs.y)*.5*scale,1.39-mins.z*scale)
    for obj in imported:
        obj.name="lighthouse-hi-"+obj.name
        if obj.parent is None:obj.parent=root
    # 上層環狀欄杆，保留中央階梯入口。
    for index in range(18):
        angle=index/18*math.tau
        if -2.02 < angle-math.tau < -1.10 or -2.02 < angle < -1.10:continue
        px=x+math.cos(angle)*1.82;py=y+.15+math.sin(angle)*1.66
        cone(f"lighthouse-upper-rail-post-{index}",.035,.045,.52,(px,py,1.58),rail,8)
        next_angle=(index+1)/18*math.tau
        nx=x+math.cos(next_angle)*1.82;ny=y+.15+math.sin(next_angle)*1.66
        length=math.hypot(nx-px,ny-py);bar=cube(f"lighthouse-upper-rail-{index}",(length,.045,.06),((px+nx)/2,(py+ny)/2,1.82),rail,.02);bar.rotation_euler[2]=math.atan2(ny-py,nx-px)

    # 雙側暖光照護小屋；各自維持牆、屋頂、門窗分件。
    for side in (-1,1):
        hx=x+side*1.92;hy=y-.74
        cube(f"lighthouse-cottage-wall-{side}",(1.10,.82,.78),(hx,hy,1.10),cottage_wall,.10)
        roof_piece=cube(f"lighthouse-cottage-roof-{side}",(1.28,1.00,.18),(hx,hy,1.58),cottage_roof,.07);roof_piece.rotation_euler[1]=side*.08
        cube(f"lighthouse-cottage-door-{side}",(.25,.04,.48),(hx-side*.28,hy-.43,1.03),wood,.025)
        cube(f"lighthouse-cottage-window-{side}",(.33,.035,.28),(hx+side*.26,hy-.435,1.18),cottage_glass,.035)

    tree("lighthouse-tree-a",x+1.38,y+.96,1.24,True,.58);tree("lighthouse-tree-b",x+2.20,y-.12,.76,False,.52)
    tree("lighthouse-tree-c",x-1.72,y+.72,.76,False,.50);tree("lighthouse-tree-d",x-2.26,y-.30,.76,True,.54)
    flower=material("lighthouse-garden",(.82,.38,.48))
    for index in range(14):
        angle=index/14*math.tau
        sphere(f"lighthouse-flower-{index}",.11,(x+math.cos(angle)*2.35,y-.28+math.sin(angle)*2.05,.88),flower,(1,.8,.6),1)
    post=material("lighthouse-lamp-post",(.20,.24,.24))
    for index in range(6):
        angle=index/6*math.tau+.25
        lx=x+math.cos(angle)*2.50;ly=y-.28+math.sin(angle)*2.18
        cone(f"lighthouse-lamp-post-{index}",.035,.045,.72,(lx,ly,1.12),post,8)
        sphere(f"lighthouse-lamp-{index}",.11,(lx,ly,1.54),glow,subdivisions=2)

    # 兩張面海長椅。
    for bench_index,(bx,by,rotation) in enumerate(((-1.18,-2.05,-.10),(1.20,-2.02,.10))):
        parts=[cube(f"lighthouse-bench-seat-{bench_index}",(1.00,.34,.10),(x+bx,y+by,.96),wood,.025),cube(f"lighthouse-bench-back-{bench_index}",(1.00,.09,.42),(x+bx,y+by+.16,1.20),wood,.025)]
        for leg in (-.35,.35):parts.append(cube(f"lighthouse-bench-leg-{bench_index}-{leg}",(.08,.25,.34),(x+bx+leg,y+by,.79),rail,.018))
        for part in parts:part.rotation_euler[2]=rotation

    # 中央碼頭之外再加入右側短碼頭，對應海報的雙側靠岸關係。
    for index in range(6):
        cube(f"lighthouse-pier-{index}",(.72,.75,.14),(x,y-3.35-index*.62,.62-index*.015),wood,.04)
    for side in (-1,1):
        for index in range(4):cone(f"pier-post-{side}-{index}",.045,.055,.8,(x+side*.36,y-3.3-index*.9,.2),wood,8)
    for index in range(4):
        cube(f"lighthouse-side-pier-{index}",(.70,.68,.14),(x+3.10+index*.58,y-.72,.55),wood,.04)
        for side in (-1,1):cone(f"lighthouse-side-pier-post-{index}-{side}",.045,.055,.76,(x+3.10+index*.58,y-.72+side*.33,.18),wood,8)

    landscape=[obj for obj in bpy.context.scene.objects if obj not in before_landscape and obj is not root and obj.parent is None]
    landscape_root=bpy.data.objects.new("ENV-HOPE-LIGHTHOUSE-LANDSCAPE-001",None);bpy.context.collection.objects.link(landscape_root)
    for obj in landscape:
        if obj.parent is None:obj.parent=landscape_root


def look_at(obj, target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
scene.name="ENV-TAIWAN-ARCHIPELAGO-001-MACRO"
scene.unit_settings.system='METRIC'

# 網頁使用可延伸至視野外的動態 shader 海洋。宏觀 GLB 不再烘焙 52×36
# 的實體海面方盒，避免 glTF 匯出合併節點後無法單獨隱藏而形成矩形展示板。

for name,x,y,accent in ISLANDS:
    if name=="pathology":
        pathology_island(x,y)
    elif name=="imaging":
        imaging_terrain(x,y)
        imaging_pavilion(x,y)
        imaging_garden_props(x,y)
    elif name=="medical-oncology":
        medical_oncology_terrain(x,y)
        medical_oncology_clinic(x,y)
        medical_oncology_garden_props(x,y)
    elif name=="surgical-oncology":
        surgical_oncology_terrain(x,y)
        surgical_oncology_center(x,y)
        surgical_oncology_accessibility(x,y)
        surgical_oncology_garden_props(x,y)
    elif name=="reconstruction":
        reconstruction_terrain(x,y)
        reconstruction_center(x,y)
        reconstruction_garden_props(x,y)
    elif name=="radiation-oncology":
        radiation_oncology_terrain(x,y)
        radiation_oncology_center(x,y)
        radiation_oncology_garden_props(x,y)
    elif name=="cardiology":
        cardiology_terrain(x,y)
        cardiology_center(x,y)
        cardiology_garden_props(x,y)
    elif name=="family-medicine":
        family_medicine_terrain(x,y)
        family_medicine_center(x,y)
        family_medicine_garden_props(x,y)
    elif name=="rehabilitation":
        rehabilitation_terrain(x,y)
        rehabilitation_center(x,y)
        rehabilitation_therapy_props(x,y)
    elif name=="fertility":
        fertility_terrain(x,y)
        fertility_center(x,y)
        fertility_garden_props(x,y)
    else:
        island_base(name,x,y,.92)
        pavilion(name,x,y,accent,.9)
for index,(a,b) in enumerate(LINKS): bridge(f"bridge-{index}",ISLANDS[a][1:3],ISLANDS[b][1:3])

island_base("ntu-core",-15.0,10.0,1.35)
hospital(-15.0,10.0)
hospital_landscape(-15.0,10.0)
bridge("bridge-ntucc-pathology",(-15.0,10.0),ISLANDS[0][1:3])
lighthouse(14.0,-17.0)
bridge("bridge-fertility-lighthouse",ISLANDS[9][1:3],(14.0,-17.0))

scene.world=bpy.data.worlds.new("Hope Island World")
scene.world.color=(.04,.07,.10)
bpy.ops.object.light_add(type='AREA',location=(-8,-10,24));bpy.context.object.data.energy=1900;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=14
bpy.ops.object.light_add(type='SUN',location=(-12,-12,18));bpy.context.object.data.energy=2.0;bpy.context.object.rotation_euler=(math.radians(28),0,math.radians(-35))

bpy.ops.object.camera_add(location=(38,-58,48));camera=bpy.context.object;camera.data.lens=52;look_at(camera,(0,-4.0,.5));scene.camera=camera
scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(PREVIEW)
scene.render.film_transparent=False
scene.view_settings.look='AgX - Medium High Contrast'
scene["component_id"]="ENV-TAIWAN-ARCHIPELAGO-001"
scene["care_islands"]=10
scene["public_cores"]="NTUCC,Hope Lighthouse"

BLEND.parent.mkdir(parents=True,exist_ok=True);GLB.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
bpy.ops.export_scene.gltf(
    filepath=str(GLB),
    export_format='GLB',
    export_apply=True,
    export_yup=True,
    export_materials='EXPORT',
    export_image_format='WEBP',
    export_image_quality=76,
    export_image_add_webp=False,
    export_image_webp_fallback=False,
    export_draco_mesh_compression_enable=True,
    export_draco_mesh_compression_level=7,
    export_draco_position_quantization=14,
    export_draco_normal_quantization=10,
    export_draco_texcoord_quantization=12,
)
bpy.ops.render.render(write_still=True)
print(f"BLEND={BLEND}\nGLB={GLB}\nPREVIEW={PREVIEW}")
