"""Blender 5.2: --background --python build_cast_v08_hunyuan.py -- [role ...]."""
from pathlib import Path
import argparse
import json
import os
import math
import re
import struct
import sys
from collections import Counter, defaultdict

import bpy
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v08_face_geometry import (read_rest_components, component_report, prepare_surface,
                               smooth_face, transplant)

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / 'art-source/characters/v08-hunyuan/raw'
OUT = ROOT / 'art-source/characters/export/v08-hunyuan'
SOURCE_RIG = ROOT / 'webgl-prototype/assets/characters/v05/visitor.glb'
ACTIONS = ('idle', 'walk', 'wave', 'read', 'talk', 'nod', 'stretch', 'wish')
# Keys are WEB role IDs; patient -> visitor and visitor -> scarf intentionally differ.
ROLES = {'visitor': 'patient', 'scarf': 'visitor', 'doctor': 'doctor',
         'nurse': 'nurse', 'surgeon': 'surgeon', 'scrub': 'scrubnurse'}
HEIGHT = 1.57
MAX_TRIANGLES = 24000
TARGET_TRIANGLES = 24000  # Includes transplanted geometry; reserve its exact triangle count.
BYTE_TARGET = 1_500_000
KMEANS_K, KMEANS_SAMPLES, KMEANS_ITERATIONS = 10, 30000, 35
SMOOTH_ROUNDS, ISLAND_MIN = 6, 60
HEAD_SCALE = 1.12
# Off: Hunyuan head proportions differ from the reference, so front projection shifts the hairline.
FRONT_REFERENCE_COLORS = False
ALPHA_THRESHOLD, WHITE_BACKGROUND_THRESHOLD = .5, .965
# All ratios refer to normalized total height, except explicitly named angles.
PARAMS = dict(rotation_degrees=(0, 0, 0), shoulder_z=.685, neck_z=.755,
              hips_z=.39, knee_z=.215, ankle_z=.055, shoulder_width=.135,
              elbow_fraction=.49, wrist_fraction=.85, rest_abduction=15., head_scale=HEAD_SCALE,
              shoulder_blend_radius=.085, face_min_z=.77, face_half_width=.115,
              face_hairline_z=.925, face_hairline_curve=.025, face_angle=75.,
              face_front_y=.015, ear_inner_x=.105, ear_outer_x=.17,
              ear_min_z=.805, ear_max_z=.89, ear_front_y=.035, hair_back_y=.025,
              face_smooth_rounds=45, face_ellipsoid_mix=.4, face_ellipsoid_depth=.065,
              body_smooth_rounds=2, eye_height_fraction=.45, eye_spacing_fraction=.38,
              feature_offset=.0018, reference_bbox=None)
ROLE_PARAMS = {role: dict(masked=role=='scrub',
                         cream_half_width=.055 if role in {'visitor','scarf'} else .095)
               for role in ROLES}
# Semantic anchors in sRGB. Actual colors are extracted from the reference by Lab
# k-means then matched to these anchors. None means automatic; RGB overrides below
# make art direction repeatable without editing algorithm code.
# Initial anchors extracted from all six supplied PNGs, seed 8, K=10.
PALETTES = {'visitor': {'skin': '#fcc09a',
             'hair': '#663a2d',
             'shirt': '#d39288',
             'pants': '#b29783',
             'shoe': '#f4e4d7',
             'sole': '#c0a591',
             'cream': '#f4e4d7',
             'accent': '#d39288',
             'headscarf': '#b27366'},
 'scarf': {'skin': '#fcbf96',
           'hair': '#4d3d34',
           'shirt': '#4b4f5a',
           'pants': '#a48a77',
           'shoe': '#eddbcd',
           'sole': '#ba9f8b',
           'cream': '#eddbcd',
           'accent': '#4b4f5a'},
 'doctor': {'skin': '#fdc79e',
            'hair': '#34251f',
            'shirt': '#50494e',
            'pants': '#50494e',
            'shoe': '#ebdfd6',
            'sole': '#9f908a',
            'cream': '#ebdfd6',
            'accent': '#9f908a'},
 'nurse': {'skin': '#ffc59d',
           'hair': '#563829',
           'shirt': '#303a5a',
           'pants': '#303a5a',
           'shoe': '#f1e4da',
           'sole': '#cebeb3',
           'cream': '#f1e4da',
           'accent': '#cebeb3'},
 'surgeon': {'skin': '#ffc7a1',
             'hair': '#543527',
             'shirt': '#4e7063',
             'pants': '#4e7063',
             'shoe': '#eedfd4',
             'sole': '#b4ab9f',
             'cream': '#eedfd4',
             'accent': '#b4ab9f',
             'cap': '#4e7063'},
 'scrub': {'skin': '#fbc19a',
           'hair': '#2e1d10',
           'shirt': '#3c6961',
           'pants': '#3c6961',
           'shoe': '#ebe3da',
           'sole': '#c5c2b8',
           'cream': '#ebe3da',
           'accent': '#8e8f84',
           'cap': '#3c6961',
           'mask': '#c5c2b8'}}
PALETTE_OVERRIDES = {role: {} for role in ROLES}  # e.g. {'visitor': {'skin': '#f0bd99'}}


def log(step, **values):
    print('V08 ' + step + ' ' + json.dumps(values, ensure_ascii=False), flush=True)


def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def coords(obj):
    a = np.empty(len(obj.data.vertices)*3, dtype=np.float64)
    obj.data.vertices.foreach_get('co', a)
    return a.reshape(-1, 3)


def srgb_linear(c):
    c = np.asarray(c)
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055)**2.4)


def lab(rgb):
    xyz = srgb_linear(rgb) @ np.array([[.4124564,.2126729,.0193339],
                                      [.3575761,.7151522,.1191920],
                                      [.1804375,.0721750,.9503041]])
    xyz /= [.95047, 1., 1.08883]
    f = np.where(xyz > (6/29)**3, np.cbrt(xyz), xyz/(3*(6/29)**2)+4/29)
    return np.stack((116*f[...,1]-16, 500*(f[...,0]-f[...,1]),
                     200*(f[...,1]-f[...,2])), axis=-1)


def rgb(hex_color):
    return np.array([int(hex_color[i:i+2], 16)/255 for i in (1,3,5)])


def image_array(image):
    w, h = image.size
    a = np.empty(w*h*4, dtype=np.float32)
    image.pixels.foreach_get(a)
    return a.reshape(h,w,4)  # Blender bottom-up pixels, UV origin bottom left.


def reference(role, cfg):
    im = bpy.data.images.load(str(RAW / (ROLES[role]+'-rgba.png')), check_existing=False)
    pixels = image_array(im)
    mask = pixels[:,:,3] > ALPHA_THRESHOLD
    # Some supplied RGBA files still contain an opaque white background.
    if mask.mean() > .98:
        mask &= np.min(pixels[:,:,:3], axis=2) < WHITE_BACKGROUND_THRESHOLD
        log('reference_warning', role=role, message='Opaque background; using white rejection. Inspect silhouette bbox.')
    ys, xs = np.where(mask)
    if len(xs) < 100:
        raise ValueError('Reference has no usable silhouette')
    bbox = cfg['reference_bbox'] or [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)]
    samples = pixels[:,:,:3][mask]
    rng = np.random.default_rng(8)
    if len(samples) > KMEANS_SAMPLES:
        samples = samples[rng.choice(len(samples), KMEANS_SAMPLES, replace=False)]
    values = lab(samples)
    centers = [values[rng.integers(len(values))]]
    for _ in range(KMEANS_K-1):
        d = np.min(np.sum((values[:,None]-centers)**2, axis=2), axis=1)
        centers.append(values[rng.choice(len(values), p=d/d.sum())] if d.sum() else values[0])
    centers = np.array(centers)
    for _ in range(KMEANS_ITERATIONS):
        labels = np.argmin(np.sum((values[:,None]-centers)**2, axis=2), axis=1)
        updated = np.array([values[labels==i].mean(0) if np.any(labels==i) else centers[i]
                            for i in range(KMEANS_K)])
        if np.max(np.abs(updated-centers)) < .02:
            break
        centers = updated
    colors = np.array([samples[labels==i].mean(0) if np.any(labels==i) else samples[0]
                       for i in range(KMEANS_K)])
    palette = {}
    for name, anchor in PALETTES[role].items():
        idx = np.argmin(np.sum((lab(colors)-lab(rgb(anchor)))**2, axis=1))
        color = colors[idx].copy()
        if name == 'skin':
            color = np.clip(color + [.012, .002, -.008], 0, 1)
        palette[name] = rgb(PALETTE_OVERRIDES[role][name]) if name in PALETTE_OVERRIDES[role] else color
    log('palette', role=role, silhouette_bbox=bbox,
        clusters=colors.round(4).tolist(), colors={k:v.round(4).tolist() for k,v in palette.items()})
    return pixels, bbox, palette


def import_body(role, cfg):
    old = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(RAW/(ROLES[role]+'-textured.glb')))
    imported = set(bpy.data.objects)-old
    meshes = [o for o in imported if o.type == 'MESH']
    if not meshes:
        raise ValueError('No mesh in input GLB')
    for o in meshes:
        world = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = world
        active(o)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in imported:
        if o.type != 'MESH':
            bpy.data.objects.remove(o, do_unlink=True)
    active(meshes[0])
    for o in meshes:
        o.select_set(True)
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = 'cast_body'
    obj.data.name = 'cast_body'
    before = coords(obj)
    obj.rotation_euler = [math.radians(v) for v in cfg['rotation_degrees']]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    a = coords(obj)
    a *= HEIGHT / np.ptp(a[:,2])
    a[:,2] -= a[:,2].min()
    feet = a[a[:,2] < .10*HEIGHT]
    center = (feet.min(0)+feet.max(0))/2
    a[:,:2] -= center[:2]
    obj.data.vertices.foreach_set('co', a.ravel())
    obj.data.update()
    log('bbox_orientation', role=role, input_min=before.min(0).tolist(), input_max=before.max(0).tolist(),
        normalized_min=a.min(0).tolist(), normalized_max=a.max(0).tolist(),
        rotation_degrees=cfg['rotation_degrees'], expected_front='-Y', up='+Z', left='-X',
        note='glTF importer maps Y-up to Z-up; front sign is an explicit assumption, inspect rendered face/feet.')
    if np.ptp(a[:,1]) > np.ptp(a[:,2]):
        raise ValueError('Depth exceeds height: adjust rotation_degrees')
    return obj


def adjacency(mesh):
    edges = defaultdict(list)
    neighbors = [set() for _ in mesh.polygons]
    for p in mesh.polygons:
        for edge in p.edge_keys:
            edges[tuple(sorted(edge))].append(p.index)
    for faces in edges.values():
        for i in faces:
            neighbors[i].update(j for j in faces if j != i)
    return neighbors, edges


def smooth_labels(labels, neighbors, rounds=SMOOTH_ROUNDS, island_min=ISLAND_MIN):
    labels = labels.copy()
    for _ in range(rounds):
        new = labels.copy()
        for i, ns in enumerate(neighbors):
            counts = Counter(labels[j] for j in ns)
            if counts:
                winner, count = counts.most_common(1)[0]
                if count > len(ns)/2:
                    new[i] = winner
        labels = new
    seen, components = set(), []
    for i in range(len(labels)):
        if i in seen:
            continue
        stack, part = [i], []
        seen.add(i)
        while stack:
            j = stack.pop()
            part.append(j)
            for n in neighbors[j]:
                if n not in seen and labels[n] == labels[i]:
                    seen.add(n)
                    stack.append(n)
        components.append(part)
    owner = np.empty(len(labels), dtype=int)
    for i, part in enumerate(components):
        owner[part] = i
    for part in sorted(components, key=len):
        if len(part) >= island_min:
            continue
        border = {owner[n] for f in part for n in neighbors[f] if owner[n] != owner[f]}
        larger = [n for n in border if len(components[n]) > len(part)]
        if larger:
            target = max(larger, key=lambda n: len(components[n]))
            labels[part] = labels[components[target][0]]
    return labels


def sample_colors(obj):
    mesh = obj.data
    if not mesh.uv_layers.active:
        raise ValueError('Input GLB must contain UVs')
    uv = mesh.uv_layers.active.data
    textures = {}
    for slot, mat in enumerate(mesh.materials):
        bs = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if mat and mat.use_nodes else None
        if not bs or not bs.inputs['Base Color'].is_linked:
            raise ValueError(f'Material {slot} has no linked baseColor texture')
        node = bs.inputs['Base Color'].links[0].from_node
        if node.type != 'TEX_IMAGE' or not node.image:
            raise ValueError('Expected direct baseColor image texture from glTF')
        textures[slot] = image_array(node.image)
    mesh.calc_loop_triangles()
    sums, counts = np.zeros((len(mesh.polygons),3)), np.zeros(len(mesh.polygons))
    bary = np.array([[1/3]*3, [.6,.2,.2], [.2,.6,.2], [.2,.2,.6], [.45,.45,.1], [.1,.45,.45], [.45,.1,.45]])
    for tri in mesh.loop_triangles:
        tex = textures[mesh.polygons[tri.polygon_index].material_index]
        samples = bary @ np.array([uv[i].uv[:] for i in tri.loops])
        xy = np.floor((samples % 1) * [tex.shape[1],tex.shape[0]]).astype(int)
        color = tex[xy[:,1],xy[:,0],:3].mean(0)
        weight = max(tri.area, 1e-12)
        sums[tri.polygon_index] += color*weight
        counts[tri.polygon_index] += weight
    return sums / counts[:,None]


def material(name, color, roughness=.8):
    existing = bpy.data.materials.get(name)
    if existing: existing.name = '_input_'+name
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*srgb_linear(color),1)
    bs.inputs['Roughness'].default_value = roughness
    return mat


def front_reference_colors(obj, colors, pixels, bbox, cfg):
    # Hunyuan's texture smears the hairline; the T-pose reference shows it sharply from the front.
    centers = np.array([p.center[:] for p in obj.data.polygons])
    normals = np.array([p.normal[:] for p in obj.data.polygons])
    xs = centers[:,0]
    x0, y0, x1, y1 = bbox
    px = np.round(x0 + (xs-xs.min())/(xs.max()-xs.min())*(x1-x0-1)).astype(int)
    py = np.round(y0 + centers[:,2]/HEIGHT*(y1-y0-1)).astype(int)
    h, w = pixels.shape[:2]
    px, py = np.clip(px,0,w-1), np.clip(py,0,h-1)
    sample = pixels[py,px]
    use = (centers[:,2] > cfg['neck_z']*HEIGHT) & (normals[:,1] < -.35) & (sample[:,3] > .5)
    colors[use] = sample[use,:3]
    log('front_reference_colors', polygons=int(use.sum()))


def color_blocks(obj, palette, cfg, pixels=None, bbox=None):
    colors = sample_colors(obj)
    if pixels is not None: front_reference_colors(obj, colors, pixels, bbox, cfg)
    names = list(palette)
    distances = np.sum((lab(colors)[:,None,:]-lab(np.array(list(palette.values())))[None,:,:])**2, axis=2)
    # Color alone cannot distinguish identical scrub shirt/pants or white sole/badge.
    centers = np.array([p.center[:] for p in obj.data.polygons])
    z = centers[:,2]/HEIGHT
    for name, i in zip(names, range(len(names))):
        allowed = np.ones(len(z), dtype=bool)
        if name == 'pants': allowed = (z < cfg['hips_z']+.07) & (z > .08)
        elif name == 'shirt': allowed = (z > cfg['hips_z']-.03) & (z < cfg['neck_z'])
        elif name in {'hair','headscarf','cap'}: allowed = z > cfg['neck_z']
        elif name == 'sole': allowed = z < .035
        elif name == 'shoe': allowed = centers[:,2] < .12
        elif name == 'cream':
            allowed = ((z > cfg['hips_z']-.03) & (z < cfg['neck_z']-.035)
                       & (np.abs(centers[:,0]) < cfg['cream_half_width']*HEIGHT) & (centers[:,1] < 0))
        elif name == 'accent': allowed = z < cfg['neck_z']
        elif name == 'skin':
            face = ((centers[:,0]/(.115*HEIGHT))**2 + ((z-.855)/.085)**2 < 1) & (centers[:,1] < 0)
            ears = (np.abs(centers[:,0]) < .14*HEIGHT) & (z > .815) & (z < .88) & (centers[:,1] < .025*HEIGHT)
            allowed = (z < cfg['face_min_z']) | face | ears
        elif name == 'mask': allowed = (z > cfg['face_min_z']) & (z < .865) & (centers[:,1] < 0)
        distances[~allowed,i] = 1e8
    labels = np.argmin(distances, axis=1)
    neighbors, _ = adjacency(obj.data)
    labels = smooth_labels(labels, neighbors)
    invalid = distances[np.arange(len(labels)), labels] >= 1e8
    labels[invalid] = np.argmin(distances[invalid], axis=1)
    obj.data.materials.clear()
    for name, color in palette.items():
        obj.data.materials.append(material(name, color, .55 if name=='skin' else .6 if name in {'shoe','sole'} else .8))
    for p, value in zip(obj.data.polygons, labels):
        p.material_index = int(value)
        p.use_smooth = True
    log('color_blocks', faces={name:int(np.sum(labels==i)) for i,name in enumerate(names)})


def triangles(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def decimate(obj, budget=TARGET_TRIANGLES):
    before = triangles(obj)
    _, edges = adjacency(obj.data)
    protected = set()
    for edge, faces in edges.items():
        if len(faces)!=2 or len({obj.data.polygons[i].material_index for i in faces})>1:
            protected.update(edge)
    group = obj.vertex_groups.new(name='_decimate_interior')
    interior = [v.index for v in obj.data.vertices if v.index not in protected]
    if interior: group.add(interior, 1., 'REPLACE')
    active(obj)
    for attempt in range(3):
        current = triangles(obj)
        if current <= budget: break
        mod = obj.modifiers.new('Preserve face and color borders', 'DECIMATE')
        mod.decimate_type = 'COLLAPSE'
        mod.ratio = max(.05, budget/current*.96)
        mod.use_collapse_triangulate = True
        mod.vertex_group = '_decimate_interior'
        mod.vertex_group_factor = 1000.
        bpy.ops.object.modifier_apply(modifier=mod.name)
    stale = obj.vertex_groups.get('_decimate_interior')
    if stale: obj.vertex_groups.remove(stale)
    if triangles(obj)>budget:
        raise RuntimeError(f'Decimation exceeded reserved body budget {budget}; inspect topology')
    log('decimate', before=before, after=triangles(obj), protected_vertices=len(protected),
        note='Collapse uses strong border/face weighting, not a hard boundary lock; inspect seams.')


def enlarge_head(obj, cfg):
    a = coords(obj)
    neck = cfg['neck_z']*HEIGHT
    t = np.clip((a[:,2]-neck)/(.055*HEIGHT),0,1)
    blend = t*t*(3-2*t)
    pivot = np.array([0.,0.,neck])
    a = pivot+(a-pivot)*(1+(cfg['head_scale']-1)*blend[:,None])
    # Shorten only the body; retain the full requested head enlargement and total height.
    excess = a[:,2].max()-HEIGHT
    a[:,2] -= excess*np.minimum(a[:,2]/neck,1)
    obj.data.vertices.foreach_set('co',a.ravel())
    obj.data.update()
    for key in ('face_min_z','face_hairline_z','ear_min_z','ear_max_z'):
        z = cfg[key]*HEIGHT
        t = np.clip((z-neck)/(.055*HEIGHT),0,1)
        cfg[key] = (neck+(z-neck)*(1+(cfg['head_scale']-1)*t*t*(3-2*t))-excess*min(z/neck,1))/HEIGHT
    for key in ('face_half_width','ear_inner_x','ear_outer_x','face_hairline_curve'):
        cfg[key] *= cfg['head_scale']
    for key in ('shoulder_z','neck_z','hips_z','knee_z','ankle_z'):
        cfg[key] *= (neck-excess)/neck
    log('head_scale', scale=cfg['head_scale'], height=float(np.ptp(a[:,2])), body_shortening=float(excess))


def smooth_normals(obj):
    active(obj)
    # Imported custom normals describe the old triangulation and must be discarded.
    if obj.data.has_custom_normals:
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
    for p in obj.data.polygons: p.use_smooth = True
    # Smooth color boundaries; only real folds in the same material may be sharp.
    _, edges = adjacency(obj.data)
    region = obj.data.attributes.get('v08_face_region')
    sharp_count = 0
    for edge in obj.data.edges:
        faces = edges.get(tuple(sorted(edge.vertices)), [])
        sharp = False
        if len(faces) == 2:
            left, right = [obj.data.polygons[i] for i in faces]
            in_face = region and any(region.data[i].value == 1 for i in faces)
            sharp = (not in_face and left.material_index == right.material_index
                     and left.normal.angle(right.normal, 0.) > math.radians(40))
        edge.use_edge_sharp = bool(sharp)
        sharp_count += bool(sharp)
    # Ordinary interpolated normals avoid area-weighting every low-poly triangle.
    obj.data.update()
    assert all(p.use_smooth for p in obj.data.polygons)
    log('normals', smooth_faces=len(obj.data.polygons), genuine_sharp_edges=sharp_count)


def blend_shoulders(obj, rig, cfg):
    radius = cfg['shoulder_blend_radius']*HEIGHT
    spine = obj.vertex_groups.get('spine')
    for side, sign in [('L',-1),('R',1)]:
        name = 'upper_arm.'+side
        shoulder = rig.data.bones[name].head_local
        group = obj.vertex_groups.get(name)
        for v in obj.data.vertices:
            distance = (v.co-shoulder).length
            if distance >= radius: continue
            influence = (1-distance/radius)**2
            t = min(1.,max(0.,.5+(v.co.x-shoulder.x)*sign/(2*radius)))
            t = t*t*(3-2*t)
            weights = {g.group:g.weight for g in v.groups}
            total = weights.get(spine.index,0)+weights.get(group.index,0)
            if total < .1: continue
            arm = weights.get(group.index,0)*(1-influence)+total*t*influence
            group.add([v.index],arm,'REPLACE')
            spine.add([v.index],total-arm,'REPLACE')


def load_actions():
    before, old_actions = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE_RIG))
    objects = set(bpy.data.objects)-before
    rig = next(o for o in objects if o.type=='ARMATURE')
    actions = {}
    for a in set(bpy.data.actions)-old_actions:
        key = re.sub(r'\.\d+$','',a.name).split('|')[-1].lower()
        if key in ACTIONS:
            actions[key] = a
            a.name = 'source_'+key
    if set(actions)!=set(ACTIONS): raise ValueError(f'Missing v05 clips: {set(ACTIONS)-set(actions)}')
    rig.animation_data_clear()
    return rig, actions, objects


def estimate_bones(obj, cfg):
    a = coords(obj)
    h = HEIGHT
    shoulder = cfg['shoulder_z']*h
    # Estimate arm centerline from the outer T-pose cross-section.
    arm = a[(np.abs(a[:,0])>cfg['shoulder_width']*h*1.4)&(np.abs(a[:,2]-shoulder)<.09*h)]
    arm_y = float(np.median(arm[:,1])) if len(arm) else 0.
    if len(arm): shoulder = float(np.median(arm[:,2]))
    joints = {'root': ((0,0,0),(0,0,cfg['hips_z']*h),None),
              'hips': ((0,0,cfg['hips_z']*h),(0,0,(cfg['hips_z']+.07)*h),'root'),
              'spine': ((0,0,(cfg['hips_z']+.08)*h),(0,0,cfg['neck_z']*h),'hips'),
              'head': ((0,0,cfg['neck_z']*h),(0,0,.97*h),'spine')}
    for side, sign in [('L',-1),('R',1)]:
        leg = a[(a[:,0]*sign>0)&(np.abs(a[:,2]-cfg['knee_z']*h)<.025*h)]
        lx = float(np.median(leg[:,0])) if len(leg) else sign*.09*h
        ly = float(np.median(leg[:,1])) if len(leg) else 0.
        sh = np.array([sign*cfg['shoulder_width']*h,arm_y,shoulder])
        endx = float(a[a[:,0]*sign>0,0].max() if sign>0 else a[a[:,0]*sign>0,0].min())
        tip = np.array([endx,arm_y,shoulder])
        elbow = sh+(tip-sh)*cfg['elbow_fraction']
        wrist = sh+(tip-sh)*cfg['wrist_fraction']
        joints.update({f'upper_arm.{side}':(sh,elbow,'spine'),
                       f'forearm.{side}':(elbow,wrist,f'upper_arm.{side}'),
                       f'hand.{side}':(wrist,tip,f'forearm.{side}'),
                       f'thigh.{side}':((lx,ly,cfg['hips_z']*h),(lx,ly,cfg['knee_z']*h),'hips'),
                       f'shin.{side}':((lx,ly,cfg['knee_z']*h),(lx,ly,cfg['ankle_z']*h),f'thigh.{side}'),
                       f'foot.{side}':((lx,ly,cfg['ankle_z']*h),(lx,ly-.12*h,cfg['ankle_z']*h),f'shin.{side}')})
    return joints


def fallback_weights(obj, rig):
    obj.vertex_groups.clear()
    a = coords(obj)
    names = [b.name for b in rig.data.bones if b.use_deform]
    distances = []
    for name in names:
        b = rig.data.bones[name]
        start, end = np.array(b.head_local),np.array(b.tail_local)
        d = end-start
        t = np.clip((a-start)@d/(d@d),0,1)
        distances.append(np.linalg.norm(a-(start+t[:,None]*d),axis=1))
    distances = np.array(distances).T
    nearest = np.argsort(distances,axis=1)[:,:4]
    weights = 1/np.maximum(np.take_along_axis(distances,nearest,axis=1),.012)**4
    weights /= weights.sum(axis=1,keepdims=True)
    groups = [obj.vertex_groups.new(name=n) for n in names]
    for v, inds, ws in zip(obj.data.vertices,nearest,weights):
        for idx, w in zip(inds,ws): groups[idx].add([v.index],float(w),'REPLACE')


def fill_empty_weights(obj):
    # Shoulder blending plus the 4-influence limit can leave a few vertices with no weight; copy the nearest weighted vertex.
    from mathutils.kdtree import KDTree
    def total(v): return sum(g.weight for g in v.groups)
    empty = [v for v in obj.data.vertices if not v.groups or total(v)<1e-6]
    if not empty: return
    weighted = [v for v in obj.data.vertices if v.groups and total(v)>1e-6]
    tree = KDTree(len(weighted))
    for i,v in enumerate(weighted): tree.insert(v.co,i)
    tree.balance()
    for v in empty:
        for g in list(v.groups): obj.vertex_groups[g.group].remove([v.index])
        src = weighted[tree.find(v.co)[1]]
        s = total(src)
        for g in src.groups: obj.vertex_groups[g.group].add([v.index],g.weight/s,'REPLACE')
    log('weight_fill', vertices=len(empty))


def bind(obj, cfg):
    joints = estimate_bones(obj,cfg)
    arm = bpy.data.armatures.new('HopeCastRig')
    rig = bpy.data.objects.new('HopeCastRig',arm)
    bpy.context.collection.objects.link(rig)
    active(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for name,(head,tail,parent) in joints.items():
        b = arm.edit_bones.new(name)
        b.head,b.tail = Vector(head),Vector(tail)
        if parent: b.parent = arm.edit_bones[parent]
        b.use_deform = name != 'root'
        b.align_roll(Vector((0,-1,0)))
    bpy.ops.object.mode_set(mode='OBJECT')
    active(rig)
    obj.select_set(True)
    method = 'automatic'
    try:
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    except RuntimeError as e:
        log('weight_warning', message=str(e))
        method = 'nearest_segment'
    bone_names = {b.name for b in arm.bones if b.use_deform}
    valid_groups = {g.index for g in obj.vertex_groups if g.name in bone_names}
    missing = sum(not any(g.group in valid_groups and g.weight>1e-6 for g in v.groups) for v in obj.data.vertices)
    if missing or method!='automatic':
        fallback_weights(obj,rig)
        method = 'nearest_segment'
    obj.parent = rig
    mods = [m for m in obj.modifiers if m.type=='ARMATURE']
    mod = mods[0] if mods else obj.modifiers.new('Armature','ARMATURE')
    mod.object = rig
    mod.use_deform_preserve_volume = True
    # Helper groups are not skin weights; drop them before limiting and normalizing.
    for group in [g for g in obj.vertex_groups if g.name.startswith('_')]: obj.vertex_groups.remove(group)
    blend_shoulders(obj,rig,cfg)
    active(obj)
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    fill_empty_weights(obj)
    invalid = [v.index for v in obj.data.vertices if not v.groups or abs(sum(g.weight for g in v.groups)-1)>1e-4]
    if invalid: raise ValueError(f'Invalid normalized skin weights on {len(invalid)} vertices')
    # Rotation is expressed in armature space, then converted to each bone's local basis.
    for side, sign in [('L',-1),('R',1)]:
        b = rig.pose.bones['upper_arm.'+side]
        world_rot = Quaternion(Vector((0,1,0)), sign*math.radians(90-cfg['rest_abduction']))
        rest = b.bone.matrix_local.to_quaternion()
        b.rotation_mode = 'QUATERNION'
        b.rotation_quaternion = rest.inverted() @ world_rot @ rest
    bpy.context.view_layer.update()
    active(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    active(rig)
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    mod = obj.modifiers.new('Armature','ARMATURE')
    mod.object = rig
    log('rig', weights=method, initially_unweighted=missing,
        bones={b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in arm.bones})
    return rig


def set_action(rig, action):
    rig.animation_data_create()
    rig.animation_data.action = action
    if action and action.slots: rig.animation_data.action_slot = action.slots[0]


def retarget(source, source_actions, rig):
    result = {}
    # Bake source local deltas in the new rest basis; blindly copying channels
    # changes the rotation axis when imported bone rolls differ.
    for name in ACTIONS:
        original = source_actions[name]
        set_action(source,original)
        start,end = map(lambda x:int(round(x)),original.frame_range)
        action = bpy.data.actions.new(name)
        action.use_frame_range = True
        action.frame_start,action.frame_end = start,end
        set_action(rig,action)
        previous = {}
        for f in range(start,end+1):
            bpy.context.scene.frame_set(f)
            for b in rig.pose.bones:
                sb = source.pose.bones.get(b.name)
                if sb is None: continue
                src_rest = (source.matrix_world @ sb.bone.matrix_local).to_quaternion()
                dst_rest = (rig.matrix_world @ b.bone.matrix_local).to_quaternion()
                basis = dst_rest.inverted() @ src_rest
                loc,rot,scale = sb.matrix_basis.decompose()
                q = basis @ rot @ basis.inverted()
                if b.name in previous and previous[b.name].dot(q)<0: q.negate()
                previous[b.name] = q.copy()
                b.rotation_mode = 'QUATERNION'
                b.rotation_quaternion = q
                b.location = (basis @ loc)*(b.bone.length/max(sb.bone.length,1e-6))
                b.scale = scale
                for channel in ('location','rotation_quaternion','scale'):
                    b.keyframe_insert(channel,frame=f,group=b.name)
        result[name] = action
        log('action', name=name, frames=[start,end], method='v05 rest-basis delta bake')
    set_action(rig,None)
    for b in rig.pose.bones: b.matrix_basis = Matrix.Identity(4)
    return result


def collision_report(obj, rig, actions):
    # Diagnostic triangle intersections; does not certify absence of enclosed geometry.
    groups = {g.index:g.name for g in obj.vertex_groups}
    dominant = [groups[max(v.groups,key=lambda g:g.weight).group] for v in obj.data.vertices]
    def category(n):
        if n.startswith(('hand.','forearm.')): return 'arm.'+n[-1]
        if n.startswith(('thigh.','shin.','foot.')): return 'leg.'+n[-1]
        return 'torso'
    cats = [category(n) for n in dominant]
    problems = []
    checks = [('rest',None,[1]),('idle',actions['idle'],[1]),
              ('walk',actions['walk'],range(int(actions['walk'].frame_range[0]),int(actions['walk'].frame_range[1])+1))]
    for name, action, frames in checks:
        set_action(rig,action)
        if action is None:
            for b in rig.pose.bones: b.matrix_basis=Matrix.Identity(4)
        for frame in frames:
            bpy.context.scene.frame_set(frame)
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            try:
                mesh.calc_loop_triangles()
                buckets = defaultdict(list)
                for t in mesh.loop_triangles:
                    cs = {cats[i] for i in t.vertices}
                    if len(cs)==1: buckets[cs.pop()].append(tuple(t.vertices))
                trees = {k:BVHTree.FromPolygons([v.co for v in mesh.vertices],faces,all_triangles=True) for k,faces in buckets.items() if faces}
                for left,right in [('arm.L','torso'),('arm.R','torso'),('leg.L','leg.R')]:
                    hits = trees[left].overlap(trees[right]) if left in trees and right in trees else []
                    if hits: problems.append(dict(action=name,frame=frame,pair=[left,right],triangle_pairs=len(hits)))
            finally: evaluated.to_mesh_clear()
    set_action(rig,None)
    for b in rig.pose.bones: b.matrix_basis=Matrix.Identity(4)
    log('collision_diagnostics', intersections=problems, visual_review_required=True)
    return problems


def glb_info(path):
    data = path.read_bytes()
    if data[:4] != b'glTF': raise ValueError('Invalid GLB')
    n = struct.unpack_from('<I',data,12)[0]
    gltf = json.loads(data[20:20+n])
    count = 0
    for m in gltf['meshes']:
        for p in m['primitives']:
            if p.get('mode',4)!=4: raise ValueError('Non-triangle primitive')
            count += gltf['accessors'][p['indices']]['count']//3
    return gltf,count


def export_region(obj,rig,role):
    """Export actual face-selection IDs as colors, independently of glTF face ordering."""
    original=[p.material_index for p in obj.data.polygons]
    count=len(obj.data.materials)
    colors=[(1.,.15,.05),(.15,.75,1.),(.7,.25,1.)]
    for i,color in enumerate(colors): obj.data.materials.append(material('region-'+str(i+1),color))
    attr=obj.data.attributes['v08_face_region']
    for p in obj.data.polygons:
        region=attr.data[p.index].value
        if region: p.material_index=count+region-1
    folder=OUT/'regions'; folder.mkdir(exist_ok=True)
    active(obj); rig.select_set(True)
    try:
        bpy.ops.export_scene.gltf(filepath=str(folder/(role+'.glb')),export_format='GLB',
            use_selection=True,export_normals=True,export_skins=True,export_animations=False)
    finally:
        for p,index in zip(obj.data.polygons,original): p.material_index=index
        while len(obj.data.materials)>count: obj.data.materials.pop(index=len(obj.data.materials)-1)


def build(role):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 24
    cfg = dict(PARAMS,**ROLE_PARAMS[role])
    pixels,bbox,palette = reference(role,cfg)
    obj = import_body(role,cfg)
    color_blocks(obj,palette,cfg,pixels if FRONT_REFERENCE_COLORS else None,bbox)
    components, source_eyes = read_rest_components(SOURCE_RIG)
    (OUT/'v05-components.json').write_text(json.dumps(component_report(components),indent=2)+'\n')
    feature_triangles = sum(len(c['faces']) for c in components if c['category']!='excluded'
                            and not (cfg['masked'] and c['category'] in {'mouth','cheek.L','cheek.R'}))
    prepare_surface(obj,cfg,HEIGHT)
    decimate(obj, budget=MAX_TRIANGLES-feature_triangles-100)
    enlarge_head(obj,cfg)
    face_report = smooth_face(obj,cfg,HEIGHT)
    if os.environ.get('V08_DEBUG_REGION'):
        dbg = obj.copy(); dbg.data = obj.data.copy(); bpy.context.collection.objects.link(dbg)
        red = bpy.data.materials.new('debug_face'); red.use_nodes = True
        red.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (1, 0, 0, 1)
        dbg.data.materials.append(red)
        attr = dbg.data.attributes['v08_face_region']
        for p in dbg.data.polygons:
            if attr.data[p.index].value == 1: p.material_index = len(dbg.data.materials)-1
        bpy.ops.object.select_all(action='DESELECT'); dbg.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(os.environ['V08_DEBUG_REGION'], role+'-region.glb'),
                                  export_format='GLB', use_selection=True)
        raise SystemExit(0)
    source,source_actions,source_objects = load_actions()
    rig = bind(obj,cfg)
    # Automatic body weights must never let the face follow the shoulders.
    head_ids = [v.index for v in obj.data.vertices if v.co.z > cfg['face_min_z']*HEIGHT]
    for group in obj.vertex_groups:
        if group.name != '_face_region': group.remove(head_ids)
    obj.vertex_groups['head'].add(head_ids,1.,'REPLACE')
    features_report = transplant(obj,rig,source,components,source_eyes,cfg,HEIGHT,palette)
    smooth_normals(obj)
    for name in ('eye.L','eye.R'):
        assert rig.data.bones[name].parent.name == 'head'
        assert obj.vertex_groups.get(name) is not None
    actions = retarget(source,source_actions,rig)
    for o in source_objects: bpy.data.objects.remove(o,do_unlink=True)
    for a in source_actions.values(): bpy.data.actions.remove(a)
    collisions = collision_report(obj,rig,actions)
    rig.animation_data_create()
    for name,action in actions.items():
        track = rig.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name,int(action.frame_range[0]),action)
        if hasattr(strip,'action_slot') and action.slots: strip.action_slot=action.slots[0]
        track.mute = True
    active(obj)
    rig.select_set(True)
    target = OUT/(role+'.glb')
    temporary = OUT/(role+'.pending.glb')
    bpy.ops.export_scene.gltf(filepath=str(temporary),export_format='GLB',use_selection=True,
        export_normals=True,export_animations=True,export_animation_mode='ACTIONS',export_skins=True,
        export_def_bones=False,export_leaf_bone=False,export_image_format='AUTO',
        export_force_sampling=True,export_optimize_animation_size=True,
        export_anim_single_armature=True,export_influence_nb=4)
    gltf,count = glb_info(temporary)
    assert all('NORMAL' in p['attributes'] for m in gltf['meshes'] for p in m['primitives']), 'Missing exported normals'
    clips = [a['name'].split('|')[-1].lower() for a in gltf.get('animations',[])]
    if set(clips)!=set(ACTIONS): raise ValueError(f'Exported clips mismatch: {clips}')
    if count>MAX_TRIANGLES: raise ValueError(f'Exported triangle budget exceeded: {count}')
    if len(gltf['meshes'])!=1 or gltf['meshes'][0].get('name')!='cast_body':
        raise ValueError('Expected one mesh named cast_body')
    materials = [m['name'] for m in gltf.get('materials',[])]
    assert 'skin_face' not in materials and not gltf.get('images'), 'Face texture remains'
    assert {'brow','eye-white','iris','ink'} <= set(materials)
    assert {'eye.L','eye.R'} <= {n.get('name') for n in gltf['nodes']}
    temporary.replace(target)
    old_face = OUT/(role+'-face.png')
    if old_face.exists(): old_face.unlink()
    export_region(obj,rig,role)
    report = dict(round=3,face_region=face_report,features=features_report,role=role,prefix=ROLES[role],triangles=count,bytes=target.stat().st_size,
        size_target_met=target.stat().st_size<=BYTE_TARGET,materials=materials,actions=clips,
        parameters=cfg,palette={k:v.tolist() for k,v in palette.items()},
        material_face_counts=dict(Counter(obj.data.materials[p.material_index].name for p in obj.data.polygons)),
        bones={b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'parent':b.parent.name if b.parent else None} for b in rig.data.bones},
        collision_intersections=collisions,visual_validation='pending exported GLB render review')
    (OUT/(role+'-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    log('export', **report)
    if not report['size_target_met']: log('size_warning',role=role,message='Over 1.5 MB target; lower TARGET_TRIANGLES, then rebuild and inspect.')
    return report


def self_check():
    assert np.linalg.norm(lab(np.array([1.,1.,1.]))-[100,0,0]) < .02
    assert np.linalg.norm(lab(np.array([0.,0.,0.]))) < .001
    assert ROLES['visitor']=='patient' and ROLES['scarf']=='visitor'
    ns=[{1},{0,2},{1,3},{2}]
    assert smooth_labels(np.array([0,0,1,0]),ns,rounds=0,island_min=2).tolist()==[0,0,0,0]
    assert set(PALETTES)==set(ROLES)
    log('self_check',status='passed')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('roles',nargs='*',metavar='ROLE')
    parser.add_argument('--self-check',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    self_check()
    if args.self_check: return
    roles=args.roles or list(ROLES)
    if any(r not in ROLES for r in roles): parser.error('角色須為：'+', '.join(ROLES))
    missing=[str(p) for p in [SOURCE_RIG]+[RAW/(ROLES[r]+suffix) for r in roles for suffix in ('-textured.glb','-rgba.png')] if not p.is_file()]
    if missing: raise FileNotFoundError('Missing inputs:\n'+'\n'.join(missing))
    OUT.mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/'manifest.json'
    manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {'version':'v08-hunyuan','roles':{}}
    for role in roles:
        manifest['roles'][role]=build(role)
        temp=OUT/'manifest.pending.json'
        temp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        temp.replace(manifest_path)


if __name__=='__main__': main()
