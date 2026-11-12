"""v05 rest-mesh extraction and v08 face geometry; NumPy analysis needs no Blender."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import math
import struct
import numpy as np

FEATURE_MATERIALS = {'eye-white', 'iris', 'ink', 'blush', 'lip'}


def read_rest_components(path):
    data = Path(path).read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    gltf = json.loads(data[20:20+size])
    blob = data[28+size:]
    def accessor(index):
        a = gltf['accessors'][index]
        assert not a.get('sparse'), 'Sparse accessors require explicit decoding'
        v = gltf['bufferViews'][a['bufferView']]
        dtype = np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        width = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        return np.ndarray((a['count'],width), dtype, blob,
            v.get('byteOffset',0)+a.get('byteOffset',0),
            strides=(v.get('byteStride',dtype.itemsize*width),dtype.itemsize)).copy()
    node = next(n for n in gltf['nodes'] if n.get('name')=='cast_body')
    # This source bakes geometry into mesh coordinates; never silently apply a posed mesh.
    ancestors = [node]
    child = gltf['nodes'].index(node)
    while True:
        parents = [n for n in gltf['nodes'] if child in n.get('children',[])]
        if not parents: break
        ancestors += parents
        child = gltf['nodes'].index(parents[0])
    for n in ancestors:
        assert np.allclose(n.get('translation',[0,0,0]),0)
        assert np.allclose(n.get('rotation',[0,0,0,1]),[0,0,0,1])
        assert np.allclose(n.get('scale',[1,1,1]),1)
        assert np.allclose(n.get('matrix',np.eye(4).ravel()),np.eye(4).ravel())
    result = []
    for primitive in gltf['meshes'][node['mesh']]['primitives']:
        material = gltf['materials'][primitive['material']]
        name = material['name']
        if name not in FEATURE_MATERIALS | {'hair','shoe'}: continue
        assert primitive.get('mode',4)==4
        vertices = accessor(primitive['attributes']['POSITION']).astype(float)
        vertices = vertices[:,[0,2,1]] * [1,-1,1]  # glTF Y-up -> Blender Z-up.
        faces = accessor(primitive['indices']).reshape(-1,3)
        # Weld UV / normal seams for connectivity, without changing source geometry.
        _, welded = np.unique(np.round(vertices,6), axis=0, return_inverse=True)
        parent = np.arange(welded.max()+1)
        def root(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]]
                i=parent[i]
            return i
        for face in welded[faces]:
            r=root(face[0])
            for v in face[1:]: parent[root(v)]=r
        groups=defaultdict(list)
        for i,face in enumerate(faces): groups[root(welded[face[0]])].append(i)
        for indices in groups.values():
            selected=faces[indices]
            ids, inverse=np.unique(selected,return_inverse=True)
            a=vertices[ids]
            result.append(dict(material=name, vertices=a, faces=inverse.reshape(-1,3),
                center=(a.min(0)+a.max(0))/2, minimum=a.min(0), maximum=a.max(0),
                color=material.get('pbrMetallicRoughness',{}).get('baseColorFactor',[1,1,1,1])))
    whites=sorted([c for c in result if c['material']=='eye-white'],key=lambda c:c['center'][0])
    assert len(whites)==2
    eye_z=np.mean([c['center'][2] for c in whites])
    separation=whites[1]['center'][0]-whites[0]['center'][0]
    for i,c in enumerate(result):
        x,y,z=c['center']; name=c['material']
        side='L' if x<0 else 'R'
        near_eye=(abs(abs(x)-separation/2)<separation*.40 and abs(z-eye_z)<separation*.44 and y<-.10)
        if name in {'eye-white','iris'} or (name in {'ink','hair','shoe'} and near_eye):
            category='eye.'+side
        elif name in {'ink','hair'} and eye_z+separation*.44<z<eye_z+separation*.75 and abs(x)<separation:
            category='brow.'+side
        elif name=='lip' or (name=='blush' and abs(x)<separation*.25 and eye_z-separation<z<eye_z):
            category='mouth'
        elif name=='blush' and eye_z-separation*.55<z<eye_z and separation*.55<abs(x)<separation*1.12 and y<-.10:
            category='cheek.'+side
        else: category='excluded'  # ear interiors, finger creases, shoes, and head hair.
        c.update(id=i,category=category)
    assert sum(c['category'].startswith('brow.') for c in result)==2
    assert sum(c['material']=='lip' and c['category']=='mouth' for c in result)==1
    return result, np.array([c['center'] for c in whites])


def component_report(components):
    return [dict(id=c['id'],material=c['material'],category=c['category'],
                 triangles=len(c['faces']),minimum=c['minimum'].tolist(),maximum=c['maximum'].tolist())
            for c in components]


def face_masks(centers, normals, names, cfg, height):
    x,y,z=(centers/height).T
    half=cfg['face_half_width']
    top=cfg['face_hairline_z']-cfg['face_hairline_curve']*(x/half)**2
    front=(normals[:,1]<-math.cos(math.radians(cfg['face_angle']))) & (y<cfg['face_front_y'])
    face=(z>cfg['face_min_z']) & (z<top) & (abs(x)<half) & front
    # Hat/scarf geometry and mask color blocks remain protected even under the cutoff.
    protected=np.isin(names,['cap','headscarf','mask','hair_main'])
    face &= ~protected
    ear=(abs(x)>cfg['ear_inner_x']) & (abs(x)<cfg['ear_outer_x']) & (z>cfg['ear_min_z']) & (z<cfg['ear_max_z']) & (y<cfg['ear_front_y']) & ~protected
    neck_chin=(z>cfg['neck_z']) & (z<cfg['face_min_z']+.035) & (abs(x)<half) & (y<cfg['face_front_y']) & ~protected
    invalid_hair=(names=='hair') & (z>cfg['neck_z']) & (z<top) & (y<cfg['hair_back_y'])
    return face, ear, neck_chin | invalid_hair


def fixed_boundary_smooth(vertices, faces, selected, rounds=40, factor=.55):
    vertices=vertices.copy()
    adjacency=[set() for _ in vertices]
    inside=np.zeros(len(vertices),bool); outside=np.zeros(len(vertices),bool)
    edge_counts=defaultdict(int)
    for i,face in enumerate(faces):
        (inside if selected[i] else outside)[face]=True
        for a,b in zip(face,np.roll(face,-1)):
            adjacency[a].add(b); adjacency[b].add(a)
            edge_counts[tuple(sorted((a,b)))]+=1
    for edge,count in edge_counts.items():
        if count != 2: outside[list(edge)]=True
    movable=np.flatnonzero(inside & ~outside)
    # Every vertex touching an unselected polygon is an immutable boundary.
    if not len(movable): raise ValueError('Face selection has no interior vertices')
    row=[]; col=[]
    for i in movable:
        row.extend([i]*len(adjacency[i])); col.extend(adjacency[i])
    row=np.array(row); col=np.array(col)
    degree=np.bincount(row,minlength=len(vertices))
    for _ in range(rounds):
        mean=np.zeros_like(vertices)
        np.add.at(mean,row,vertices[col])
        mean[movable]/=degree[movable,None]
        vertices[movable] += factor*(mean[movable]-vertices[movable])
    return vertices, movable, inside & outside


def prepare_surface(obj, cfg, height):
    import bpy
    import bmesh
    # glTF hard normals / UV seams otherwise leave disconnected flat triangles.
    for uv in list(obj.data.uv_layers): obj.data.uv_layers.remove(uv)
    if obj.data.has_custom_normals:
        bpy.context.view_layer.objects.active=obj
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    bm=bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    group=obj.vertex_groups.new(name='_body_smooth')
    ids=[v.index for v in obj.data.vertices if v.co.z<(cfg['neck_z']-.025)*height]
    group.add(ids,1.,'REPLACE')
    mod=obj.modifiers.new('Body volume preserving smoothing','CORRECTIVE_SMOOTH')
    mod.factor=.35; mod.iterations=cfg['body_smooth_rounds']; mod.smooth_type='LENGTH_WEIGHTED'
    mod.use_pin_boundary=True; mod.vertex_group=group.name
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.vertex_groups.remove(obj.vertex_groups['_body_smooth'])


def small_islands(mesh,names,max_faces=80):
    parent=list(range(len(names)))
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
        return i
    owner=defaultdict(list)
    for p in mesh.polygons:
        for e in p.edge_keys: owner[e].append(p.index)
    for faces in owner.values():
        for a,b in zip(faces,faces[1:]):
            if names[a]==names[b]: parent[find(a)]=find(b)
    roots=[find(i) for i in range(len(names))]
    sizes=Counter(roots)
    return np.array([sizes[r]<=max_faces for r in roots])


def main_hair_mask(mesh,names,min_faces=300):
    hair=np.flatnonzero(names=='hair')
    parent={int(i):int(i) for i in hair}
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]]; i=parent[i]
        return i
    owner=defaultdict(list)
    for i in hair:
        for e in mesh.polygons[int(i)].edge_keys: owner[e].append(int(i))
    for faces in owner.values():
        for a,b in zip(faces,faces[1:]): parent[find(a)]=find(b)
    sizes=Counter(find(int(i)) for i in hair)
    mask=np.zeros(len(names),bool)
    for i in hair:
        if sizes[find(int(i))]>=min_faces: mask[i]=True
    return mask


def smooth_face(obj,cfg,height):
    mesh=obj.data
    centers=np.array([p.center[:] for p in mesh.polygons])
    normals=np.array([p.normal[:] for p in mesh.polygons])
    names=np.array([mesh.materials[p.material_index].name for p in mesh.polygons])
    # Bangs belong to the main hair mass; only small detached hair islands on the face are color noise.
    names[main_hair_mask(mesh,names)]='hair_main'
    face,ear,cleanup=face_masks(centers,normals,names,cfg,height)
    # The geometric box overlaps bangs and hairlines; keep only skin plus small enclosed noise islands.
    small=small_islands(mesh,names,max_faces=80)
    keep=(names=='skin')|(small&~np.isin(names,['cap','headscarf','mask','hair_main']))
    geo_face=face.copy()
    face&=keep; cleanup&=keep|(names=='hair')&small
    assert face.sum()>50, 'Too few face polygons; inspect region parameters'
    skin=next(i for i,m in enumerate(mesh.materials) if m.name=='skin')
    for p in mesh.polygons:
        if face[p.index] or ear[p.index] or cleanup[p.index]: p.material_index=skin
    original=np.array([v.co[:] for v in mesh.vertices])
    faces=[np.array(p.vertices) for p in mesh.polygons]
    smoothed,movable,boundary=fixed_boundary_smooth(original,faces,face,cfg['face_smooth_rounds'])
    # Flatten residual nasal relief toward an ellipse while keeping the seam fixed.
    t=np.clip((smoothed[movable,2]/height-cfg['face_min_z'])/(cfg['face_hairline_z']-cfg['face_min_z']),0,1)
    x=smoothed[movable,0]/(cfg['face_half_width']*height)
    weight=cfg['face_ellipsoid_mix']*np.sin(np.pi*t)**2*np.maximum(0,1-x*x)
    zcenter=(cfg['face_min_z']+cfg['face_hairline_z'])*height/2
    rz=(cfg['face_hairline_z']-cfg['face_min_z'])*height*.65
    ellipse=np.sqrt(np.maximum(.02,1-(smoothed[movable,0]/(cfg['face_half_width']*height*1.18))**2-((smoothed[movable,2]-zcenter)/rz)**2))
    depth=cfg['face_ellipsoid_depth']*height
    center_y=float(np.median(smoothed[movable,1]+depth*ellipse))
    smoothed[movable,1]=(1-weight)*smoothed[movable,1]+weight*(center_y-depth*ellipse)
    assert np.array_equal(smoothed[boundary],original[boundary])
    mesh.vertices.foreach_set('co',smoothed.ravel()); mesh.update()
    attr=mesh.attributes.get('v08_face_region') or mesh.attributes.new('v08_face_region','INT','FACE')
    attr.data.foreach_set('value',np.where(face,1,np.where(ear,2,np.where(cleanup,3,np.where(geo_face,4,0)))).astype(np.int32))
    group=obj.vertex_groups.get('_face_region') or obj.vertex_groups.new(name='_face_region')
    group.add(np.unique(np.concatenate([faces[i] for i in np.flatnonzero(face)])).tolist(),1.,'REPLACE')
    assert all(mesh.materials[p.material_index].name=='skin' for p in mesh.polygons
               if face[p.index] or ear[p.index] or cleanup[p.index])
    return dict(face_polygons=int(face.sum()),ear_polygons=int(ear.sum()),cleanup_polygons=int(cleanup.sum()),
                movable_vertices=len(movable),fixed_boundary_vertices=int(boundary.sum()))


def transplant(obj,rig,source,components,source_eyes,cfg,height,palette):
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    mesh=obj.data
    face_attr=mesh.attributes['v08_face_region']
    # Project onto the full geometric face (value 4 = face geometry kept in its original color).
    polygons=[tuple(p.vertices) for p in mesh.polygons if face_attr.data[p.index].value in (1,4)]
    tree=BVHTree.FromPolygons([v.co for v in mesh.vertices],polygons)
    # Place features from this character's actual face region, not fixed height ratios.
    region=np.array([p.center[:] for p in mesh.polygons if face_attr.data[p.index].value in (1,4)])
    zlo,zhi=np.percentile(region[:,2],[3,97])
    eye_z=zlo+(zhi-zlo)*cfg['eye_height_fraction']
    band=region[np.abs(region[:,2]-eye_z)<.02*height]
    face_width=float(np.percentile(band[:,0],97)-np.percentile(band[:,0],3)) if len(band)>10 else 2*cfg['face_half_width']*height
    separation=face_width*cfg['eye_spacing_fraction']
    scale=separation/(source_eyes[1,0]-source_eyes[0,0])
    midpoint=source_eyes.mean(0)
    target=np.array([0.,0.,eye_z])
    selected=[c for c in components if c['category']!='excluded' and not (cfg['masked'] and c['category'] in {'mouth','cheek.L','cheek.R'})]
    groups=defaultdict(list)
    for c in selected:
        a=(c['vertices']-midpoint)*scale+target
        groups[c['category']].append((c,a))
    objects=[]; eye_centers={}; report=[]
    for category,parts in groups.items():
        # Rigid project shrinkwrap along -Y: one translation for the whole assembly.
        # Vertexwise shrinkwrap would flatten the eye volumes and destroy iris layering.
        def project(points):
            shifts=[]
            for x,y,z in points:
                hit,normal,index,distance=tree.ray_cast(Vector((float(x),1.,float(z))),Vector((0,-1,0)),3.)
                if hit is not None: shifts.append(hit.y-cfg['feature_offset']-y)
            return shifts
        points=np.concatenate([a for _,a in parts])
        shifts=project(points)
        # Brows may sit above a low hairline or cap edge; lower them toward the eyes until they land on skin.
        drop=0.
        while category.startswith('brow.') and len(shifts)/len(points)<.9 and drop<.03*height:
            drop+=.002*height
            for _,a in parts: a[:,2]-=.002*height
            points=np.concatenate([a for _,a in parts]); shifts=project(points)
        coverage=len(shifts)/len(points)
        # Blush discs extend past the face seam onto the cheeks; a rigid shift only needs some hits.
        minimum=.2 if category.startswith('cheek.') else .6 if category=='mouth' else .5 if category.startswith('brow.') else .75
        if coverage<minimum: raise ValueError(f'{category}: face projection coverage {coverage:.1%}; adjust face/eye parameters')
        shift=float(min(shifts))
        if category.startswith('eye.'):
            side=category[-1]; src=source_eyes[0 if side=='L' else 1]
            eye_centers[category]=(src-midpoint)*scale+target+[0,shift,0]
        for c,a in parts:
            a[:,1]+=shift
            name='brow' if category.startswith('brow.') else 'ink' if c['material']=='hair' else 'eye-white' if c['material']=='shoe' else c['material']
            mat=bpy.data.materials.get(name)
            if mat is None:
                mat=bpy.data.materials.new(name); mat.use_nodes=True
                color=palette['hair'] if name=='brow' else None
                if color is not None:
                    color=np.where(color<=.04045,color/12.92,((color+.055)/1.055)**2.4)
                    rgba=(*color,1.)
                else: rgba=c['color']
                mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgba
                mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.4 if name in {'iris','eye-white'} else .7
            partmesh=bpy.data.meshes.new('v05-'+category)
            partmesh.from_pydata(a.tolist(),[],c['faces'].tolist()); partmesh.materials.append(mat)
            part=bpy.data.objects.new('v05-'+category,partmesh); bpy.context.collection.objects.link(part)
            for p in partmesh.polygons: p.use_smooth=True
            group=part.vertex_groups.new(name=category if category.startswith('eye.') else 'head')
            group.add(list(range(len(a))),1.,'REPLACE')
            objects.append(part)
        report.append(dict(part=category,projection_coverage=coverage,translation_y=shift,offset=cfg['feature_offset']))
    # Face geometry hidden under the transplanted features becomes skin (dark eye sockets from the texture).
    feature_points=np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in objects])
    lo,hi=feature_points.min(0),feature_points.max(0); pad=(hi-lo)*.12
    skin_index=next(i for i,m in enumerate(mesh.materials) if m.name=='skin')
    for p in mesh.polygons:
        if face_attr.data[p.index].value==4:
            cx,_,cz=p.center
            if lo[0]-pad[0]<cx<hi[0]+pad[0] and lo[2]-pad[2]<cz<hi[2]+pad[2]: p.material_index=skin_index
    bpy.ops.object.select_all(action='DESELECT'); rig.select_set(True); bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    for name,center in eye_centers.items():
        b=rig.data.edit_bones.new(name)
        src=source.data.bones[name]
        b.head=Vector(center); b.tail=b.head+(src.tail_local-src.head_local).normalized()*.025
        b.align_roll(src.matrix_local.to_3x3().col[2]); b.parent=rig.data.edit_bones['head']
        b.use_deform=True
    bpy.ops.object.mode_set(mode='OBJECT')
    for name in eye_centers:
        assert rig.data.bones[name].matrix_local.to_3x3().col[1].dot(source.data.bones[name].matrix_local.to_3x3().col[1]) > .9999
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
    for part in objects: part.select_set(True)
    bpy.context.view_layer.objects.active=obj; bpy.ops.object.join()
    for name in eye_centers:
        index=obj.vertex_groups[name].index
        weighted=[v for v in obj.data.vertices if any(g.group==index for g in v.groups)]
        assert weighted and all(len(v.groups)==1 and abs(v.groups[0].weight-1.)<1e-6 for v in weighted)
    # Do not export diagnostic UVs or unweighted analysis groups.
    group=obj.vertex_groups.get('_face_region')
    if group: obj.vertex_groups.remove(group)
    return report
