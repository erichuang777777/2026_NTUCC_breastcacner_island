"""Static geometry preflight; estimates are NOT Blender-measured triangle counts."""
import ast
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'scripts'/'build_prop_kit_v02.py'


def main():
    tree=ast.parse(SOURCE.read_text())
    tree.body=[n for n in tree.body if not (
        isinstance(n,ast.Import) and any(x.name in ('bpy','bmesh') for x in n.names)
        or isinstance(n,ast.ImportFrom) and n.module=='mathutils')]
    ns={'__name__':'preflight','__file__':str(SOURCE)}
    exec(compile(tree,str(SOURCE),'exec'),ns)
    records=[]
    def capture(name,vertices,faces,tone,bevel=0,smooth=False):
        assert tone in ns['PALETTE']
        assert vertices and faces and all(math.isfinite(v) for p in vertices for v in p)
        edges=defaultdict(list)
        for face in faces:
            assert len(face)>=3 and len(set(face))==len(face)
            assert all(0<=i<len(vertices) for i in face)
            # Newell normal supports curved paver polygons with collinear vertices.
            normal=[0.,0.,0.]
            for i,a in enumerate(face):
                b=face[(i+1)%len(face)];p=vertices[a];q=vertices[b]
                normal[0]+=(p[1]-q[1])*(p[2]+q[2])
                normal[1]+=(p[2]-q[2])*(p[0]+q[0])
                normal[2]+=(p[0]-q[0])*(p[1]+q[1])
                edges[tuple(sorted((a,b)))].append(normal)
            length=math.sqrt(sum(x*x for x in normal));assert length>1e-12,name
            normal[:]=[x/length for x in normal]
        assert all(len(v)==2 for v in edges.values()),name
        raw=sum(len(f)-2 for f in faces)
        selected=[]
        if bevel:
            for edge,(a,b) in edges.items():
                # Face winding is recalculated in Blender; use unsigned angle here.
                dot=abs(sum(x*y for x,y in zip(a,b)))
                if math.acos(min(1,dot))>.35:selected.append(edge)
        degree=Counter(v for edge in selected for v in edge)
        estimate=raw+4*len(selected)+sum(6*(d-2) for d in degree.values() if d>2)
        records.append({'name':name,'vertices':vertices,'raw':raw,'estimate':estimate})
    ns['mesh']=capture
    output=[]
    for asset in ns['IDS']:
        records.clear();ns['build_parts'](asset)
        estimate=sum(r['estimate'] for r in records)
        raw=sum(r['raw'] for r in records)
        points=[p for r in records for p in r['vertices']]
        dimensions=[round(max(p[i] for p in points)-min(p[i] for p in points),6) for i in range(3)]
        limit=ns['BUDGETS'][asset][1]
        assert estimate<=limit,(asset,estimate,limit)
        assert all(v>0 for v in dimensions),asset
        if asset.startswith('path-'):
            assert ns['PATH_PORTS'][asset]
        if asset=='lamp':
            assert sum(r['name']=='lantern-corner' for r in records)==4
        if asset=='tree-round':
            assert sum(r['name']=='soft-canopy' for r in records)==7
        if asset.startswith('rock-') or asset=='foam-ring':
            assert any(r['name']=='translucent-water-plinth' for r in records)
        output.append({'id':asset,'raw_triangles':raw,'estimated_baked_triangles':estimate,
                       'budget_max':limit,'raw_dimensions':dimensions})
    result={'status':'static-only; Blender execution required',
            'triangle_method':'raw polygon tessellation plus analytic 2-segment bevel estimate; not measured',
            'assets':output}
    dest=ROOT/'export'/'v02'/'preflight.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    print('STATIC_PREFLIGHT_OK')


if __name__=='__main__':main()
