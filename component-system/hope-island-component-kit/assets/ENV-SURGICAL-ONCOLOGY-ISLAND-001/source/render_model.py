from pathlib import Path
import os
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/"export"/os.environ.get("SURGICAL_SOURCE","surgical-oncology-center-hunyuan-shape-v01.glb")
PREVIEW=ROOT/"export"/os.environ.get("SURGICAL_PREVIEW","surgical-oncology-center-hunyuan-shape-v01-preview.png")
TEXTURED=os.environ.get("SURGICAL_TEXTURED","0")=="1"
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes=[obj for obj in bpy.context.scene.objects if obj.type=="MESH"]
corners=[obj.matrix_world@Vector(corner) for obj in meshes for corner in obj.bound_box]
mins=Vector(tuple(min(point[i] for point in corners) for i in range(3)));maxs=Vector(tuple(max(point[i] for point in corners) for i in range(3)));center=(mins+maxs)/2
scale=9.5/max(maxs.x-mins.x,maxs.y-mins.y)
for obj in meshes:obj.location=(obj.location-center)*scale;obj.location.z+=(maxs.z-mins.z)*scale/2;obj.scale*=scale
if not TEXTURED:
    clay=bpy.data.materials.new("surgical-inspection-clay");clay.use_nodes=True;shader=clay.node_tree.nodes.get("Principled BSDF");shader.inputs["Base Color"].default_value=(.57,.67,.61,1);shader.inputs["Roughness"].default_value=.56
    for obj in meshes:obj.data.materials.clear();obj.data.materials.append(clay)
bpy.ops.mesh.primitive_plane_add(size=30,location=(0,0,-.02));floor=bpy.context.object;floor_mat=bpy.data.materials.new("inspection-floor");floor_mat.diffuse_color=(.025,.045,.06,1);floor.data.materials.append(floor_mat)
for location,energy,size,color in (((-7,-8,13),3000,7,(1,.82,.68)),((8,0,9),1900,6,(.62,.79,1)),((0,7,6),1200,5,(1,.58,.62))):
    bpy.ops.object.light_add(type="AREA",location=location);light=bpy.context.object;light.data.energy=energy;light.data.size=size;light.data.color=color;light.rotation_euler=(Vector((0,0,1.9))-light.location).to_track_quat("-Z","Y").to_euler()
bpy.ops.object.camera_add(location=(11.8,-16.2,8.8));camera=bpy.context.object;camera.data.lens=58;camera.rotation_euler=(Vector((0,0,1.8))-camera.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene;scene.camera=camera;scene.render.engine="BLENDER_EEVEE";scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG";scene.render.filepath=str(PREVIEW);scene.world=bpy.data.worlds.new("inspection-world");scene.world.color=(.04,.08,.12);scene.view_settings.look="AgX - Medium High Contrast"
bpy.ops.render.render(write_still=True);print(f"preview={PREVIEW}")
