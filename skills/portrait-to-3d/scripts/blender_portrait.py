"""Run inside Blender: inspect, bounded local edits, or selected-mesh GLB export."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector


def write_report(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


def fresh(path):
    if path.exists():
        raise ValueError(f'拒絕覆寫既有檔案：{path}')
    path.parent.mkdir(parents=True, exist_ok=True)


def inspect_object(o):
    mesh = o.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    r = {'name': o.name, 'vertices': len(mesh.vertices),
         'triangles': sum(len(f.vertices)-2 for f in mesh.polygons),
         'boundaryEdges': sum(e.is_boundary for e in bm.edges),
         'nonManifoldEdges': sum(not e.is_manifold for e in bm.edges),
         'degenerateFaces': sum(f.calc_area() <= 1e-12 for f in bm.faces),
         'finite': all(math.isfinite(c) for v in mesh.vertices for c in v.co),
         'scale': list(o.scale), 'shapeKeys': bool(mesh.shape_keys),
         'modifiers': [m.type for m in o.modifiers],
         'vertexGroups': [g.name for g in o.vertex_groups],
         'uvLayers': [u.name for u in mesh.uv_layers]}
    bm.free()
    return r


def edit(a):
    cfg = json.loads(a.config.read_text())
    o = bpy.data.objects.get(cfg['object'])
    if o is None or o.type != 'MESH':
        raise ValueError('指定的 mesh 不存在')
    if o.data.shape_keys or o.modifiers:
        raise ValueError('此輔助工具不直接修改含形狀鍵或 modifier 的模型；請先另存已確認的基準副本')
    if o.data.users != 1:
        raise ValueError('mesh 由多個物件共用，請先建立獨立副本')
    mesh = o.data
    original = [v.co.copy() for v in mesh.vertices]
    mode = cfg['mode']
    limit = float(cfg['max_displacement'])
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError('max_displacement 必須為正有限值，單位為物件局部座標')
    weights = [1.0] * len(original)
    if cfg.get('vertex_group'):
        group = o.vertex_groups.get(cfg['vertex_group'])
        if group is None:
            raise ValueError('找不到頂點群組')
        for i in range(len(weights)):
            try:
                weights[i] = group.weight(i)
            except RuntimeError:
                weights[i] = 0
    if mode == 'handles':
        handles = cfg['handles']
        if not handles:
            raise ValueError('handles 不可空白')
        parsed = []
        for h in handles:
            center, delta, radius = Vector(h['center']), Vector(h['delta']), float(h['radius'])
            if len(center) != 3 or len(delta) != 3 or not all(math.isfinite(v) for v in [*center, *delta, radius]) or radius <= 0:
                raise ValueError('handle center/delta 需為有限 xyz，radius 必須大於零')
            parsed.append((center, delta, radius))
        for i, v in enumerate(mesh.vertices):
            change = Vector()
            for center, delta, radius in parsed:
                t = max(0.0, 1-(original[i]-center).length/radius)
                change += delta * (t*t*(3-2*t))
            change *= weights[i]
            if change.length > limit:
                change = change.normalized()*limit
            v.co = original[i]+change
    elif mode == 'relax':
        if not cfg.get('vertex_group'):
            raise ValueError('relax 必須限定 vertex_group，避免整顆頭被平滑')
        iterations, strength = int(cfg.get('iterations', 8)), float(cfg.get('strength', .3))
        if not 1 <= iterations <= 200 or not 0 < strength <= 1:
            raise ValueError('iterations 需為 1–200，strength 需大於 0 且不超過 1')
        neighbors = [set() for _ in original]
        for edge in mesh.edges:
            x, y = edge.vertices
            neighbors[x].add(y)
            neighbors[y].add(x)
        for _ in range(iterations):
            current = [v.co.copy() for v in mesh.vertices]
            for i, v in enumerate(mesh.vertices):
                if not weights[i] or not neighbors[i]:
                    continue
                average = sum((current[j] for j in neighbors[i]), Vector())/len(neighbors[i])
                change = current[i].lerp(average, strength*weights[i])-original[i]
                if change.length > limit:
                    change = change.normalized()*limit
                v.co = original[i]+change
    else:
        raise ValueError('mode 僅支援 handles 或 relax')
    mesh.update()
    distances = [(v.co-original[i]).length for i, v in enumerate(mesh.vertices)]
    report = {'operation': mode, 'units': 'object-local model units',
              'changedVertices': sum(d > 1e-8 for d in distances),
              'maxDisplacement': max(distances, default=0),
              'config': cfg, 'mesh': inspect_object(o),
              'sourceSHA256': hashlib.sha256(a.blend.read_bytes()).hexdigest()}
    if not report['mesh']['finite']:
        raise ValueError('變形產生非有限值')
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()))
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['inspect', 'edit', 'export'])
    p.add_argument('--blend', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--config', type=Path)
    p.add_argument('--out', type=Path)
    p.add_argument('--objects', nargs='+')
    p.add_argument('--threads', type=int, default=2)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if not a.blend.is_file() or a.threads < 1:
        p.error('找不到 blend 或 threads 無效')
    fresh(a.report)
    if a.action != 'inspect':
        if a.out is None:
            p.error('需要 --out')
        fresh(a.out)
        expected = '.blend' if a.action == 'edit' else '.glb'
        if a.out.suffix.lower() != expected:
            p.error(f'輸出副檔名必須為 {expected}')
    if a.action == 'edit' and (a.config is None or not a.config.is_file()):
        p.error('edit 需要 --config')
    bpy.ops.wm.open_mainfile(filepath=str(a.blend.resolve()))
    scene = bpy.context.scene
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = a.threads
    if hasattr(scene, 'cycles'):
        scene.cycles.device = 'CPU'
    if a.action == 'inspect':
        report = {'blenderVersion': bpy.app.version_string,
                  'meshes': [inspect_object(o) for o in scene.objects if o.type == 'MESH']}
    elif a.action == 'edit':
        report = edit(a)
    else:
        if not a.objects:
            p.error('export 需 --objects 明確限定匯出物件')
        objects = [scene.objects.get(name) for name in a.objects]
        if any(o is None or o.type != 'MESH' for o in objects):
            raise ValueError('匯出清單含不存在或非 mesh 物件；骨架動畫需另用專案匯出流程')
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:
            o.hide_set(False)
            o.hide_viewport = False
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(a.out.resolve()), export_format='GLB',
                                  use_selection=True, export_animations=False,
                                  export_tangents=True, export_extras=False)
        if not a.out.is_file():
            raise ValueError('GLB 未產生')
        report = {'objects': a.objects, 'bytes': a.out.stat().st_size,
                  'assetSHA256': hashlib.sha256(a.out.read_bytes()).hexdigest(),
                  'visualReview': 'not-run', 'animationExported': False}
    write_report(a.report, report)


if __name__ == '__main__':
    main()
