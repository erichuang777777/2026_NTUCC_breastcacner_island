"""Pure NumPy checks; Blender's bundled Python works without a Metal device."""
import ast
from collections import Counter
from pathlib import Path
import math
import numpy as np
from v08_face_geometry import read_rest_components, face_masks, fixed_boundary_smooth

SOURCE=Path(__file__).with_name('build_cast_v08_hunyuan.py')
ROOT=SOURCE.resolve().parents[3]


def load_math():
    tree=ast.parse(SOURCE.read_text())
    keep={'lab','srgb_linear','rgb','smooth_labels'}
    selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in keep]
    ns=dict(np=np,Counter=Counter,SMOOTH_ROUNDS=6,ISLAND_MIN=60)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(SOURCE),'exec'),ns)
    # Evaluate only literal configuration, without importing bpy.
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PARAMS' for t in node.targets):
            ns['cfg']=eval(compile(ast.Expression(node.value),str(SOURCE),'eval'),{'HEAD_SCALE':1.12})
    return ns


def main():
    ns=load_math()
    np.testing.assert_allclose(ns['lab'](np.array([[1.,1.,1.],[0.,0.,0.]])),[[100,0,0],[0,0,0]],atol=.02)
    assert ns['smooth_labels'](np.array([0,0,1,0]),[{1},{0,2},{1,3},{2}],rounds=0,island_min=2).tolist()==[0,0,0,0]
    components,eyes=read_rest_components(ROOT/'webgl-prototype/assets/characters/v05/visitor.glb')
    np.testing.assert_allclose(eyes[:,0],[-.086,.086],atol=1e-6)
    counts=Counter(c['category'] for c in components)
    assert counts=={'excluded':12,'eye.L':6,'eye.R':6,'cheek.L':1,'cheek.R':1,'mouth':2,'brow.L':1,'brow.R':1},counts
    selected=[c for c in components if c['category']!='excluded']
    assert sum(len(c['faces']) for c in selected)==6472
    for c in selected:
        assert c['vertices'].shape[1]==3 and c['faces'].max()<len(c['vertices'])
        assert c['minimum'][2]>1.1, 'Finger/foot geometry leaked into face'
    masked=[c for c in selected if c['category'] not in {'mouth','cheek.L','cheek.R'}]
    assert all(c['material']!='lip' for c in masked)
    # Frontal angle, hat/mask exclusions, ears, and under-chin hair cleanup.
    cfg=ns['cfg']
    centers=np.array([[0,-.1,.85],[0,-.1,.85],[0,-.1,.85],[0,-.1,.85],
                      [.13,0,.85],[0,-.05,.78],[0,.1,.85],[0,-.1,.95]])
    normals=np.tile([0,-1,0.],(8,1)); normals[1]=[0,-math.cos(math.radians(76)),math.sin(math.radians(76))]
    names=np.array(['hair','skin','cap','mask','hair','hair','hair','hair'])
    face,ear,clean=face_masks(centers,normals,names,cfg,1.)
    assert face.tolist()==[True,False,False,False,False,True,False,False]
    assert ear[4] and clean[5] and not clean[6] and not clean[7]
    # An interior spike flattens, while shared boundary vertices remain bit-identical.
    vertices=np.array([[0,0,1],[1,0,0],[0,1,0],[-1,0,0],[0,-1,0],[2,0,0]],float)
    faces=[np.array(f) for f in [(0,1,2),(0,2,3),(0,3,4),(0,4,1),(1,5,2),(2,5,3),(3,5,4),(4,5,1)]]
    smoothed,movable,boundary=fixed_boundary_smooth(vertices,faces,np.array([True]*4+[False]*4),30)
    assert movable.tolist()==[0]
    assert abs(smoothed[0,2])<1e-8
    assert np.array_equal(smoothed[boundary],vertices[boundary])
    assert np.array_equal(vertices[0],[0,0,1])
    for script in ['build_cast_v08_hunyuan.py','render_cast_v08.py','v08_face_geometry.py']:
        ast.parse(SOURCE.with_name(script).read_text())
    print('PASS: actual v05 components / rest eyes / mask exclusion / 6472 feature triangles')
    print('PASS: face angle / protected headwear / ears / chin cleanup / fixed smoothing boundary')
    print('PASS: existing color math and all modified script syntax')


if __name__=='__main__': main()
