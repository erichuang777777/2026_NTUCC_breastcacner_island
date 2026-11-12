"""Render exported GLBs, not source geometry; run build_prop_kit_v02.py first."""
from pathlib import Path
import json
import math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
EXPORT=ROOT/'export'/'v02'
OUTPUT=ROOT/'renders'/'prop-sheet-v02.png'


def point_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()


def solid(name,color):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=.78
    return m


def text_object(body,location,size,mat,camera):
    data=bpy.data.curves.new('sheet-label','FONT')
    data.body=body;data.size=size;data.align_x='CENTER';data.align_y='CENTER'
    obj=bpy.data.objects.new('sheet-label',data);bpy.context.scene.collection.objects.link(obj)
    obj.location=location;obj.rotation_euler=camera.rotation_euler
    data.materials.append(mat)
    return obj


def main():
    manifest=json.loads((EXPORT/'manifest.json').read_text())
    assets=manifest['assets']
    assert len(assets)==13, 'Incomplete kit: rebuild before rendering'
    for entry in assets:
        assert (EXPORT/entry['file']).is_file(),entry['file']
    for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=2560;scene.render.resolution_y=1440
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Punchy'
    scene.view_settings.exposure=.65
    scene.render.filepath=str(OUTPUT)
    world=bpy.data.worlds.new('warm-studio');scene.world=world;world.use_nodes=True
    world.node_tree.nodes['Background'].inputs['Color'].default_value=(.78,.73,.63,1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
    cam_data=bpy.data.cameras.new('sheet-camera')
    camera=bpy.data.objects.new('sheet-camera',cam_data);scene.collection.objects.link(camera)
    camera.location=(8,-12,13);point_at(camera,(0,0,0))
    cam_data.type='ORTHO';cam_data.ortho_scale=12.4;cam_data.lens=50
    scene.camera=camera
    rotation=camera.rotation_euler.to_matrix()
    right=rotation@Vector((1,0,0));up=rotation@Vector((0,1,0))
    view=rotation@Vector((0,0,1))

    def ground_at(screen_x,screen_y):
        # Intersect a screen-space orthographic ray with the ground.
        p=right*screen_x+up*screen_y
        return p-view*(p.z/view.z)

    ground_mat=solid('sheet-sand',(.88,.82,.72))
    data=bpy.data.meshes.new('sheet-ground')
    data.from_pydata([(-200,-200,-.008),(200,-200,-.008),(200,200,-.008),(-200,200,-.008)],[],[(0,1,2,3)])
    ground=bpy.data.objects.new('sheet-ground',data);scene.collection.objects.link(ground)
    data.materials.append(ground_mat)
    ink=solid('sheet-ink',(.035,.065,.07))
    subtle=solid('sheet-muted',(.09,.12,.11))
    text_object('HOPE ISLAND / PROP KIT 02',right*0+up*2.97+view*2,.23,ink,camera)
    text_object('SOFT CLAY  /  13 MODULAR ASSETS  /  Y-UP GLB',up*2.61+view*2,.095,subtle,camera)
    # Fixed presentation scales keep the small modules legible; labels disclose them.
    positions=[(-4.5,1.35),(-2.25,1.35),(0,1.35),(2.25,1.35),(4.5,1.35),
               (-3.6,-.35),(-1.2,-.35),(1.2,-.35),(3.6,-.35),
               (-3.6,-2.08),(-1.2,-2.08),(1.2,-2.08),(3.6,-2.08)]
    scales={'bench':1.8,'lamp':1.7,'flowerbed-round':1.7,'flowerbed-long':1.25,
            'shrub-cluster':1.8,'tree-round':1.1,'path-straight':1.15,'path-curve':.65,
            'path-plaza':1.15,'rock-shore-a':1.5,'rock-shore-b':1.5,'foam-ring':1.15,'signpost':1.7}
    for entry,(sx,sy) in zip(assets,positions):
        before=set(bpy.data.objects)
        result=bpy.ops.import_scene.gltf(filepath=str(EXPORT/entry['file']))
        assert 'FINISHED' in result,entry['id']
        imported=set(bpy.data.objects)-before
        parent=bpy.data.objects.new('display-'+entry['id'],None);scene.collection.objects.link(parent)
        for obj in imported:
            if obj.parent not in imported:obj.parent=parent
        s=scales[entry['id']];parent.scale=(s,s,s)
        # Shift baseline down by the projected half-height to center the silhouette.
        height=entry['dimensions'][1]*s
        parent.location=ground_at(sx,sy-height*up.z*.5)
        text_object(entry['id'],right*sx+up*(sy-.69)+view*3,.105,ink,camera)
        text_object(f"{entry['triangles']:,} tris  /  display {s:g}x",
                    right*sx+up*(sy-.84)+view*3,.075,subtle,camera)
    sun_data=bpy.data.lights.new('warm-sun','SUN');sun_data.energy=2.3
    sun_data.color=(1.0,.96,.87);sun_data.angle=math.radians(18)
    sun=bpy.data.objects.new('warm-sun',sun_data);scene.collection.objects.link(sun)
    sun.location=(-4,-6,10);point_at(sun,(0,0,0))
    fill_data=bpy.data.lights.new('large-softbox','AREA');fill_data.energy=550;fill_data.shape='DISK';fill_data.size=9
    fill=bpy.data.objects.new('large-softbox',fill_data);scene.collection.objects.link(fill)
    fill.location=(2,-3,9);point_at(fill,(0,0,0))
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.render.render(write_still=True)
    assert OUTPUT.is_file(),'PNG output missing'
    print('PROP_SHEET_COMPLETE',str(OUTPUT),flush=True)


if __name__=='__main__':
    main()
