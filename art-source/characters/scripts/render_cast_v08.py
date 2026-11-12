"""Render v08/v05 lineup, four pose samples and a 12-unit panorama in Blender."""
from pathlib import Path
import math
import re
import sys
import bpy
from mathutils import Matrix, Vector

# Reuse the existing warm studio's light/material helpers without running its main.
sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_cast_lineup_r2 import material, area, aim
from build_cast_v08_hunyuan import ROOT, OUT as MODELS, ROLES, set_action

OUT = ROOT/'art-source/characters/renders'
STYLES = {'visitor':'scarf','scarf':'short','doctor':'short','nurse':'bob','surgeon':'cap','scrub':'mask'}
RESOLUTION = (2560,1440)
SPACING, BACK_ROW_Y, BACK_ROW_X = 1.05, 1.15, .35
BACKGROUND = (.40,.35,.30,1)
FLOOR = (.64,.58,.50)
POSES = [('idle',1),('walk',1),('walk',8),('wave',None)]


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x,scene.render.resolution_y=RESOLUTION
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.render.fps=24
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.view_settings.exposure=0
    world=bpy.data.worlds.new('Warm studio')
    world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=BACKGROUND
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    scene.world=world
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008))
    bpy.context.object.data.materials.append(material('warm-ivory',FLOOR))
    area('large-warm-key',(-3,-4,5),850,5,(1,.86,.72))
    area('soft-fill',(3,-2,3),550,4,(.81,.89,1))
    area('warm-rim',(1,3,4),850,4,(1,.91,.81))
    camera=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'))
    bpy.context.collection.objects.link(camera)
    scene.camera=camera
    return scene,camera


def snapshot(path,style,action,frame,label):
    old_objects,old_actions=set(bpy.data.objects),set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(path))
    imported=set(bpy.data.objects)-old_objects
    # The glTF importer adds an unlinked bone-display icosphere; it is not part of the asset.
    for o in [o for o in imported if o.name.startswith('Icosphere')]:
        imported.discard(o); bpy.data.objects.remove(o,do_unlink=True)
    actions=set(bpy.data.actions)-old_actions
    clip=next((a for a in actions if re.sub(r'\.\d+$','',a.name).split('|')[-1].lower()==action),None)
    if action is not None and clip is None: raise ValueError(f'{path}: missing action {action}')
    for o in imported:
        if o.type=='ARMATURE':
            o.animation_data_clear()
            for b in o.pose.bones: b.matrix_basis=Matrix.Identity(4)
            set_action(o,clip)
    sample_frame=frame if frame is not None else round(sum(clip.frame_range)/2) if clip else 1
    bpy.context.scene.frame_set(sample_frame)
    bpy.context.view_layer.update()
    pivot=bpy.data.objects.new(label,None)
    bpy.context.collection.objects.link(pivot)
    allowed={'body','cap' if style=='mask' else style}
    if style=='mask': allowed.add('mask')
    deps=bpy.context.evaluated_depsgraph_get()
    count=0
    for o in imported:
        if o.type!='MESH': continue
        ancestor=o
        visible=True
        while ancestor in imported:
            match=re.match(r'^cast_([a-z]+)',ancestor.name)
            if match and match.group(1) not in allowed: visible=False
            ancestor=ancestor.parent
        if not visible: continue
        evaluated=o.evaluated_get(deps)
        mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
        copy=bpy.data.objects.new(label+'-mesh',mesh)
        bpy.context.collection.objects.link(copy)
        copy.matrix_world=o.matrix_world.copy()
        copy.parent=pivot
        count+=1
    for o in imported: bpy.data.objects.remove(o,do_unlink=True)
    for a in actions: bpy.data.actions.remove(a)
    if not count: raise ValueError(f'No visible meshes: {path}')
    print(f'V08_RENDER sample={label} action={action} frame={sample_frame} meshes={count}',flush=True)
    return pivot


def render(scene,name):
    scene.render.filepath=str(OUT/name)
    bpy.ops.render.render(write_still=True)
    print('RENDER_COMPLETE',scene.render.filepath,flush=True)


def lineup():
    scene,camera=setup()
    pivots=[]
    for i,role in enumerate(ROLES):
        x=(i-2.5)*SPACING
        front=snapshot(MODELS/(role+'.glb'),STYLES[role],'idle',1,'v08-'+role)
        front.location=(x,0,0)
        back=snapshot(ROOT/'webgl-prototype/assets/characters/v05'/(role+'.glb'),STYLES[role],'idle',1,'v05-'+role)
        back.location=(x+BACK_ROW_X,BACK_ROW_Y,0)
        pivots.extend([front,back])
    camera.data.type='ORTHO'
    camera.data.ortho_scale=7.4
    camera.location=(0,-9,5.4)
    aim(camera,(.15,.5,.85))
    render(scene,'v08-lineup-front.png')
    for p in pivots: p.rotation_euler.z=math.radians(35)
    render(scene,'v08-lineup-three-quarter.png')
    # Panorama includes only the six v08 subjects, with actual 12-unit camera distance.
    for i,p in enumerate(pivots):
        p.rotation_euler.z=0
        if i%2:
            for child in p.children_recursive: child.hide_render=True
    camera.data.type='PERSP'
    camera.data.lens=42
    target=Vector((0,0,.70))
    camera.location=target+Vector((0,-12*math.cos(math.radians(30)),12*math.sin(math.radians(30))))
    aim(camera,target)
    assert abs((camera.location-target).length-12)<1e-5
    render(scene,'v08-panorama.png')


def pose_check():
    scene,camera=setup()
    # Eight independent evaluated snapshots: changing the scene frame cannot
    # accidentally turn every sample into the last requested animation frame.
    for row,role in enumerate(('visitor','nurse')):
        for col,(action,frame) in enumerate(POSES):
            pivot=snapshot(MODELS/(role+'.glb'),STYLES[role],action,frame,f'{role}-{action}-{frame}')
            pivot.location=((col-1.5)*1.65,0,(1-row)*2.0)
    camera.data.type='ORTHO'
    camera.data.ortho_scale=8.0
    camera.location=(0,-10,1.8)
    aim(camera,(0,0,1.8))
    render(scene,'v08-pose-check.png')


def label(text,x,z,size=.055):
    curve=bpy.data.curves.new('label','FONT'); curve.body=text
    curve.align_x='CENTER'; curve.size=size
    obj=bpy.data.objects.new(text,curve); bpy.context.collection.objects.link(obj)
    obj.location=(x,-.65,z); obj.rotation_euler=(math.pi/2,0,0)
    obj.data.materials.append(material('label-ivory',(.95,.9,.8)))


def face_check(region=False):
    scene,camera=setup()
    scene.render.resolution_x,scene.render.resolution_y=(3000,1300) if region else (4800,1150)
    versions=('v08',) if region else ('v08','v05')
    for row,angle in enumerate((0,35)):
        for i,role in enumerate(ROLES):
            for j,version in enumerate(versions):
                path=(MODELS/'regions'/(role+'.glb') if region else MODELS/(role+'.glb')) if version=='v08' else ROOT/'webgl-prototype/assets/characters/v05'/(role+'.glb')
                x=((i*len(versions)+j)-(6*len(versions)-1)/2)*.60
                z=(1-row)*.78
                pivot=snapshot(path,STYLES[role],None,1,f'{version}-{role}-{angle}')
                pivot.location=(x,0,z); pivot.rotation_euler.z=math.radians(angle)
                label(f'{version} {role} / {angle}',x,1.04+z,.038 if region else .045)
    camera.data.type='ORTHO'
    camera.data.ortho_scale=3.9 if region else 7.4
    camera.location=(0,-8,1.74)
    aim(camera,(0,0,1.74))
    if region: label('ORANGE face | BLUE ears | PURPLE chin / hair cleanup',0,2.48,.055)
    render(scene,'v08-face-region.png' if region else 'v08-face-check.png')


def main():
    files=[MODELS/'regions'/(r+'.glb') for r in ROLES]+[MODELS/(r+'.glb') for r in ROLES]+[ROOT/'webgl-prototype/assets/characters/v05'/(r+'.glb') for r in ROLES]
    missing=[str(p) for p in files if not p.is_file()]
    if missing: raise FileNotFoundError('Missing models:\n'+'\n'.join(missing))
    OUT.mkdir(parents=True,exist_ok=True)
    lineup()
    pose_check()
    face_check()
    face_check(region=True)


if __name__=='__main__': main()
