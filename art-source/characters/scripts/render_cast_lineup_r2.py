"""Compare exported v07 r1/r2 GLBs with identical EEVEE/AgX studio lighting.
Blender --background --python /absolute/path/render_cast_lineup.py
Optional: -- --action walk --frame 7 (also supports all other shared actions).
Default: idle frame 1. Includes a 12-unit, 30-degree island scale view.
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
    ('PATIENT / r1', 'art-source/characters/export/v07-sample/patient-scarf.glb', 'scarf'),
    ('PATIENT / r2', 'art-source/characters/export/v07-sample-r2/patient-scarf.glb', 'scarf'),
    ('NURSE / r1', 'art-source/characters/export/v07-sample/nurse.glb', 'bob'),
    ('NURSE / r2', 'art-source/characters/export/v07-sample-r2/nurse.glb', 'bob'),
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--action', choices=ACTIONS, default='idle')
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
    pivots = []
    for i,(title,rel,style) in enumerate(CASES):
        x = (i-1.5)*.94
        pivots.append(import_case(ROOT/rel,style,x,args.action,args.frame))
        # No 3D labels: their shadows previously projected PATIENT onto the scarf.
    OUT.mkdir(parents=True,exist_ok=True)
    suffix = '' if args.action == 'idle' and args.frame == 1 else f'-{args.action}-{args.frame:03d}'
    for view, angle in [('front',0),('three-quarter',math.radians(35))]:
        for pivot in pivots:
            pivot.rotation_euler.z = angle
        scene.render.filepath = str(OUT/f'v07-sample-r2-{view}{suffix}.png')
        bpy.context.view_layer.update()
        bpy.ops.render.render(write_still=True)
        print('RENDER_COMPLETE',scene.render.filepath)

    # Two r2 characters on a simple scale-context island, not a game-scene capture.
    for i, pivot in enumerate(pivots):
        if i in (0,2):
            for child in pivot.children_recursive:
                child.hide_render = True
        else:
            pivot.location.x = -.55 if i == 1 else .55
            pivot.rotation_euler.z = 0
    ground.materials.clear()
    ground.materials.append(material('sea',(.20,.43,.46)))
    floor.location.z = -.20
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=3.3, depth=.18, location=(0,0,-.105))
    island = bpy.context.object
    island.scale.y = .78
    island.data.materials.append(material('sand',(.64,.53,.35)))
    bevel = island.modifiers.new('soft-shore','BEVEL')
    bevel.width, bevel.segments = .10, 3
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=2.95, depth=.025, location=(0,0,-.0185))
    grass = bpy.context.object
    grass.scale.y = .77
    grass.data.materials.append(material('grass',(.32,.43,.24)))
    camera.data.type = 'PERSP'
    camera.data.lens = 48
    target = Vector((0,0,.65))
    camera.location = target + Vector((0,-12*math.cos(math.radians(30)),12*math.sin(math.radians(30))))
    aim(camera,target)
    assert abs((camera.location-target).length-12) < 1e-5
    scene.render.filepath = str(OUT/f'v07-sample-r2-panorama{suffix}.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER_COMPLETE',scene.render.filepath)


if __name__ == '__main__':
    main()
