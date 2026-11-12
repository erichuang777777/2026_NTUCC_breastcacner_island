"""Pure-Python preflight; no Blender import or execution, no output artifacts."""
import ast
import math
from pathlib import Path
from collections import Counter

SCRIPTS=Path(__file__).resolve().parent


def main():
    for file in SCRIPTS.glob('*.py'):
        ast.parse(file.read_text(),filename=str(file))
    source=ast.parse((SCRIPTS/'build_prop_kit_v01.py').read_text())
    source.body=[node for node in source.body if not (
        isinstance(node,ast.Import) and any(n.name in ('bpy','bmesh') for n in node.names)
        or isinstance(node,ast.ImportFrom) and node.module=='mathutils')]
    namespace={'__name__':'static_check','__file__':str(SCRIPTS/'build_prop_kit_v01.py')}
    exec(compile(source,'build_prop_kit_v01.py','exec'),namespace)
    captured=[]

    def capture(name,vertices,faces,tone,bevel=0,smooth=False):
        assert tone in namespace['PALETTE']
        assert vertices and faces
        assert all(math.isfinite(x) for p in vertices for x in p)
        edges=Counter()
        for f in faces:
            assert len(set(f))==len(f) and len(f)>=3
            assert all(0<=v<len(vertices) for v in f)
            for i,a in enumerate(f):edges[tuple(sorted((a,f[(i+1)%len(f)])))]+=1
        assert all(count<=2 for count in edges.values()),name
        if name!='foam-ribbon':assert all(count==2 for count in edges.values()),name
        if not smooth and name!='foam-ribbon':assert bevel>0,name
        captured.append((name,vertices,faces,bevel))
    namespace['mesh']=capture
    assert len(set(namespace['IDS']))==13
    for asset in namespace['IDS']:
        captured.clear();namespace['build_parts'](asset)
        points=[p for _,vertices,_,_ in captured for p in vertices]
        dimensions=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(3)]
        raw_tris=sum(len(face)-2 for _,_,faces,_ in captured for face in faces)
        print(asset, 'raw_triangles=',raw_tris,'raw_dimensions=',[round(x,4) for x in dimensions])
        assert asset in namespace['SOURCES']
        assert dimensions[0]>0 and dimensions[2]>0
    ports=namespace['PATH_PORTS']
    for asset,items in ports.items():
        for port in items:
            assert sum(x*x for x in port['outward'])==1
            assert port['position'][1]==0
    # A straight instance at (.6, 0, -1.8) meets the first curve port exactly.
    a=ports['path-straight'][1]['position']
    translated=[a[0]+.6,a[1],a[2]-1.8]
    assert all(abs(x-y)<1e-9 for x,y in zip(translated,ports['path-curve'][0]['position']))
    print('STATIC_PREFLIGHT_OK; modifier baking, glTF export and rendering still require Blender.')


if __name__=='__main__':main()
