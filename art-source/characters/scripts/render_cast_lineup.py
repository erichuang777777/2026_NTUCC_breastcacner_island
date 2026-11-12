"""Compare exported v05/v07 GLBs with identical EEVEE/AgX studio lighting.
Blender --background --python /absolute/path/render_cast_lineup.py
Optional: -- --action walk --frame 7 (also supports all other shared actions).
The default is the neutral rest pose, to isolate geometry from animation.
"""
from pathlib import Path
import argparse
import math
import re
import sys
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'art-source/characters/renders'
CASES = [
    ('PATIENT / v05', 'webgl-prototype/assets/characters/v05/visitor.glb', 'scarf'),
    ('PATIENT / v07', 'art-source/characters/export/v07-sample/patient-scarf.glb', 'scarf'),
    ('NURSE / v05', 'webgl-prototype/assets/characters/v05/nurse.glb', 'bob'),
    ('NURSE / v07', 'art-source/characters/export/v07-sample/nurse.glb', 'bob'),
]
ACTIONS = ['idle','walk','wave','read','talk','nod','stretch','wish']


def material(name, color, roughness=.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = roughness
    return m


def aim(o, point):
    o.rotation_euler = (Vector(point)-o.location).to_track_quat('-Z','Y').to_euler()


def area(name, location, power, size, color, target=(0,0,.85)):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy, d.shape, d.size, d.color = power, 'DISK', size, color
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    o.location = location
    aim(o, target)


def import_case(path, head_style, x, action, frame):
    old_objects, old_actions = set(bpy.data.objects), set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported = set(bpy.data.objects)-old_objects
    actions = set(bpy.data.actions)-old_actions
    pivot = bpy.data.objects.new(path.stem+'-display', None)
    bpy.context.collection.objects.link(pivot)
    for o in imported:
        if o.parent not in imported:
            o.parent = pivot
        if o.type == 'ARMATURE':
            o.animation_data_clear()
            for b in o.pose.bones:
                b.matrix_basis = Matrix.Identity(4)
            if action:
                clip = next((a for a in actions if re.sub(r'\.\d+$','',a.name).split('|')[-1].lower() == action), None)
                if clip is None:
                    raise RuntimeError(f'{path.name}: missing {action}; found {[a.name for a in actions]}')
                o.animation_data_create()
                o.animation_data.action = clip
                if hasattr(clip, 'slots') and clip.slots:
                    o.animation_data.action_slot = clip.slots[0]
        # glTF multi-material objects may have cast_* child primitives.
        ancestor = o
        visible = True
        while ancestor in imported:
            match = re.match(r'^cast_([a-z]+)', ancestor.name)
            if match and match.group(1) not in {'body', head_style}:
                visible = False
            ancestor = ancestor.parent
        o.hide_render = not visible
        o.hide_set(not visible)
    pivot.location.x = x
    bpy.context.scene.frame_set(frame)
    return pivot


def label(text, x, m):
    c = bpy.data.curves.new('comparison-label', 'FONT')
    c.body, c.align_x, c.size, c.extrude = text, 'CENTER', .065, 0
    o = bpy.data.objects.new('comparison-label', c)
    bpy.context.collection.objects.link(o)
    o.location = (x,-.30,1.74)
    o.rotation_euler = (math.pi/2,0,0)
    c.materials.append(m)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=ACTIONS)
    parser.add_argument('--frame', type=int, default=1)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    for _, rel, _ in CASES:
        if not (ROOT/rel).is_file():
            raise FileNotFoundError(f'{ROOT/rel}: run build_cast_v07_sample.py first')
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 2400, 1350
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = False
    scene.render.fps = 24
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    world = bpy.data.worlds.new('Warm studio')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.40,.35,.30,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    scene.world = world
    ground = bpy.data.meshes.new('studio-floor')
    ground.from_pydata([(-100,-100,-.006),(100,-100,-.006),(100,100,-.006),(-100,100,-.006)],[],[(0,1,2,3)])
    floor = bpy.data.objects.new('studio-floor',ground)
    bpy.context.collection.objects.link(floor)
    ground.materials.append(material('warm-ivory',(.64,.58,.50)))
    area('large-warm-key',(-3,-4,5),650,4,(1,.86,.72))
    area('soft-fill',(3,-2,3),400,3,(.81,.89,1))
    area('warm-rim',(1,3,4),700,3,(1,.91,.81))
    camera = bpy.data.objects.new('LineupCamera',bpy.data.cameras.new('LineupCamera'))
    bpy.context.collection.objects.link(camera)
    camera.location = (0,-7,2.35)
    aim(camera,(0,0,.76))
    camera.data.type, camera.data.ortho_scale = 'ORTHO', 4.25
    camera.data.lens = 65
    scene.camera = camera
    text_mat = material('label-ink',(.095,.12,.12))
    pivots = []
    for i,(title,rel,style) in enumerate(CASES):
        x = (i-1.5)*.94
        pivots.append(import_case(ROOT/rel,style,x,args.action,args.frame))
        label(title,x,text_mat)
    OUT.mkdir(parents=True,exist_ok=True)
    suffix = f'-{args.action}-{args.frame:03d}' if args.action else ''
    for view, angle in [('front',0),('three-quarter',math.radians(35))]:
        for pivot in pivots:
            pivot.rotation_euler.z = angle
        scene.render.filepath = str(OUT/f'v05-v07-sample-{view}{suffix}.png')
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        print('RENDER_COMPLETE',scene.render.filepath)


if __name__ == '__main__':
    main()
