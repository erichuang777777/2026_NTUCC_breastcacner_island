"""Blender --background --python art-source/scripts/assemble_scene.py"""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'art-source'


def read(relative):
    return json.loads((ROOT / relative).read_text())


def convert(p):
    return Vector((p[0], -p[2], p[1]))


def linear(hex_color):
    values = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values)


def sun_light(name, spec):
    data = bpy.data.lights.new(name, 'SUN')
    data.color = linear(spec['color'])
    data.energy = spec['intensity']
    data.angle = math.radians(2)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = convert(spec['position'])
    obj.rotation_euler = (-obj.location).to_track_quat('-Z', 'Y').to_euler()
    return obj


def world_lighting(scene, spec):
    world = bpy.data.worlds.new('capture_world')
    world.use_nodes = True
    scene.world = world
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputWorld')
    sky = nodes.new('ShaderNodeBackground')
    sky.inputs['Strength'].default_value = spec['hemisphere']['intensity']
    tex = nodes.new('ShaderNodeTexCoord')
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(tex.outputs['Normal'], separate.inputs[0])
    ramp = nodes.new('ShaderNodeValToRGB')
    # World normals span -1..1; map to 0..1 for the two hemisphere colors.
    remap = nodes.new('ShaderNodeMapRange')
    remap.inputs['From Min'].default_value = -1
    links.new(separate.outputs['Z'], remap.inputs['Value'])
    links.new(remap.outputs['Result'], ramp.inputs['Fac'])
    ramp.color_ramp.elements[0].color = (*linear(spec['hemisphere']['ground']), 1)
    ramp.color_ramp.elements[1].color = (*linear(spec['hemisphere']['sky']), 1)
    links.new(ramp.outputs['Color'], sky.inputs['Color'])
    background = nodes.new('ShaderNodeBackground')
    background.inputs['Color'].default_value = (*linear(spec['background']), 1)
    ray = nodes.new('ShaderNodeLightPath')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(ray.outputs['Is Camera Ray'], mix.inputs[0])
    links.new(sky.outputs[0], mix.inputs[1])
    links.new(background.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs[0])


shots = read('art-source/captures/shots-capture.json')['shots']
manifest = read('art-source/captures/export-manifest.json')
lighting = read('scene/lighting.json')
assert len(shots) == 4 and all(s['camera']['position'] for s in shots)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ART / 'exports/taiwan-study-scene-v01.glb'))
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.exposure = math.log2(lighting['colorManagement']['target']['exposure'])
scene.view_settings.gamma = 1
bpy.context.view_layer.update()
probe = bpy.data.objects.get('capture_axis_probe')
assert probe is not None, 'Missing coordinate probe'
axis_error = (probe.matrix_world.translation - convert((1, 2, 3))).length
assert axis_error < 1e-5, f'glTF axis conversion mismatch: {axis_error}; do not double rotate meshes'
imported = list(scene.objects)
reports = {'blender': bpy.app.version_string, 'axisProbeError': axis_error, 'shots': []}
for directory in ('renders', 'blend'):
    (ART / directory).mkdir(parents=True, exist_ok=True)

for shot_index, shot in enumerate(shots):
    state = manifest['states'][shot['timeOfDay']]
    spec = lighting['presets'][shot['timeOfDay']]
    for obj in imported:
        source = obj.get('captureSource', obj.name)
        obj.hide_render = not state['objects'].get(source, True)
    for name, value in state['materials'].items():
        mat = bpy.data.materials.get(name)
        if mat and mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    node.inputs['Emission Color'].default_value = (*value['color'], 1)
                    node.inputs['Emission Strength'].default_value = value['strength']
    world_lighting(scene, spec)
    lights = [sun_light('capture_sun', spec['sun']), sun_light('capture_fill', spec['fill'])]
    for entry in state['lights']:
        if entry['intensity'] <= 0:
            continue
        data = bpy.data.lights.new(entry['name'], 'POINT')
        # Three intensity is candela, Blender point energy is total radiant power;
        # 4*pi is only a geometric approximation, not photometric calibration.
        data.energy = entry['intensity'] * 4 * math.pi
        data.color = entry['color']
        obj = bpy.data.objects.new(entry['name'], data)
        scene.collection.objects.link(obj)
        obj.location = convert(entry['position'])
        lights.append(obj)
    data = bpy.data.cameras.new(shot['id'])
    data.sensor_fit = 'VERTICAL'
    data.sensor_height = 24
    data.lens = 24 / (2 * math.tan(math.radians(shot['fov'])/2))
    data.clip_start = shot['camera']['near']
    data.clip_end = shot['camera']['far']
    cam = bpy.data.objects.new(shot['id'], data)
    scene.collection.objects.link(cam)
    cam.location = convert(shot['camera']['position'])
    direction = convert(shot['camera']['target']) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    scene.camera = cam
    bpy.context.view_layer.update()
    errors = {}
    for name, landmark in shot['landmarkPixels'].items():
        ndc = world_to_camera_view(scene, cam, convert(landmark['world']))
        pixel = (ndc.x * 1920, (1-ndc.y) * 1080)
        error = math.dist(pixel, landmark['pixel'])
        assert error < .1, f'{shot["id"]} {name}: projection differs by {error}px'
        errors[name] = {'blenderPixel': pixel, 'errorPixels': error}
    scene.render.filepath = str(ART / 'renders' / (shot['id'] + '.png'))
    bpy.ops.render.render(write_still=True)
    reports['shots'].append({'id': shot['id'], 'projection': errors})
    if shot_index < len(shots)-1:
        for obj in lights:
            bpy.data.objects.remove(obj, do_unlink=True)

# Leave S04's lighting active for the saved assembly; all four cameras are retained.
scene['capture_manifest'] = json.dumps(manifest)
scene['capture_shots'] = json.dumps(shots)
scene['rerender_instruction'] = 'Run assemble_scene.py to restore each shot lighting and emissive state.'
bpy.ops.wm.save_as_mainfile(filepath=str(ART / 'blend/taiwan-study-assembly-v01.blend'))
(ART / 'captures/blender-validation.json').write_text(json.dumps(reports, indent=2))
print('CAPTURE_RENDER_COMPLETE')
